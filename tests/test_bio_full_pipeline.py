"""
Tests pipeline complet biographie (intégration)
================================================

Simule le cycle de vie bout-en-bout sans OGMA live ni Archiviste réel :

  Étape 1 — Volume2 accumule des faits  (volume2_structured.json)
  Étape 2 — BioCompiler génère les groupes thématiques  (bio_compiled.json)
  Étape 3 — get_bio_context_block() lit le volume2 et produit le bloc contexte
  Étape 4 — Le bloc contexte est bien formé pour injection dans le system prompt
  Étape 5 — Idempotence : un second rêve ne duplique rien

Scénarios couverts :
  - Pipeline nominal (2 faits, 2 groupes différents)
  - Ajout d'un fait mid-session (compilation incrémentale)
  - Volume2 supprimé et recréé → reset bio_compiled
  - Bloc contexte vide si volume2 absent
  - Bloc contexte correct après compilation
"""

import json
import pytest
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from extensions.biographie_profil import get_bio_context_block


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def write_volume2(bio_dir: Path, facts: list):
    user_dir = bio_dir / "yohan"
    user_dir.mkdir(parents=True, exist_ok=True)
    data = {"user_name": "Yohan", "facts": facts, "profile_summary": {}, "metadata": {}}
    (user_dir / "volume2_structured.json").write_text(
        json.dumps(data, ensure_ascii=False), encoding="utf-8"
    )


def make_fact(content: str, category: str = "preference") -> dict:
    return {"content": content, "category": category, "date": "2026-04-18"}


def make_archiviste(groups_by_call: list):
    """
    Retourne un mock dont chaque appel successif répond avec
    le groupe correspondant dans groups_by_call.
    """
    call_count = [0]

    async def _side_effect(*args, **kwargs):
        idx = min(call_count[0], len(groups_by_call) - 1)
        call_count[0] += 1
        r = json.dumps({
            "groups": groups_by_call[idx],
            "keywords": ["kw"],
            "description": "test desc",
        })
        return r, None

    return AsyncMock(side_effect=_side_effect)


def make_compiler(bio_dir: Path, user_name: str = "yohan"):
    from scripts.bio_compiler import BioCompiler
    c = BioCompiler(user_name)
    c.user_dir = bio_dir / user_name.lower()
    c.user_dir.mkdir(parents=True, exist_ok=True)
    c.source_file = c.user_dir / "volume2_structured.json"
    c.output_path = c.user_dir / "bio_compiled.json"
    return c


# ──────────────────────────────────────────────────────────────────────────────
# Scénario 1 — Pipeline nominal
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_pipeline_nominal(tmp_path, monkeypatch):
    """
    Deux faits dans volume2 → BioCompiler génère deux groupes →
    get_bio_context_block() retourne un bloc bien formé.
    """
    bio_dir = tmp_path / "data" / "biographies"
    monkeypatch.chdir(tmp_path)

    facts = [
        make_fact("Yohan aime les films de SF", "preference"),
        make_fact("Yohan a une chatte nommée Willow", "relation"),
    ]
    write_volume2(bio_dir, facts)

    compiler = make_compiler(bio_dir)
    compiler.archiviste_controller = type("C", (), {
        "call_chat_api": make_archiviste([["GOUTS"], ["ANIMAUX"]])
    })()

    await compiler.compile()

    # bio_compiled.json créé avec 2 groupes
    compiled = json.loads(compiler.output_path.read_text(encoding="utf-8"))
    assert "GOUTS" in compiled["groups"]
    assert "ANIMAUX" in compiled["groups"]
    assert compiled["metadata"]["last_scanned_index"] == 2

    # get_bio_context_block() lit le volume2 (pas le compiled) → bloc texte correct
    block = get_bio_context_block("yohan")
    assert "[PROFIL YOHAN — faits observés]" in block
    assert "Yohan aime les films de SF" in block
    assert "Yohan a une chatte nommée Willow" in block


# ──────────────────────────────────────────────────────────────────────────────
# Scénario 2 — Ajout d'un fait mid-session (compilation incrémentale)
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_pipeline_incremental(tmp_path, monkeypatch):
    """
    Premier rêve : 1 fait compilé.
    Ajout d'un fait dans volume2.
    Second rêve : seulement le nouveau fait est re-analysé.
    """
    bio_dir = tmp_path / "data" / "biographies"
    monkeypatch.chdir(tmp_path)

    # Première passe
    write_volume2(bio_dir, [make_fact("Fait initial")])
    compiler = make_compiler(bio_dir)
    mock_call = make_archiviste([["GOUTS"], ["PROJETS"]])
    compiler.archiviste_controller = type("C", (), {"call_chat_api": mock_call})()
    await compiler.compile()
    first_call_count = mock_call.call_count

    # Ajout d'un second fait
    write_volume2(bio_dir, [make_fact("Fait initial"), make_fact("Fait ajouté")])
    await compiler.compile()

    # Un seul appel supplémentaire (seulement le nouveau fait)
    assert mock_call.call_count == first_call_count + 1

    compiled = json.loads(compiler.output_path.read_text(encoding="utf-8"))
    assert compiled["metadata"]["last_scanned_index"] == 2


# ──────────────────────────────────────────────────────────────────────────────
# Scénario 3 — Volume2 supprimé et recréé → reset bio_compiled
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_pipeline_reset_after_volume_deleted(tmp_path, monkeypatch):
    """
    Volume2 supprimé et recréé → bio_compiled.json obsolète est réinitialisé.
    L'ancien groupe disparaît, seul le nouveau fait est analysé.
    """
    bio_dir = tmp_path / "data" / "biographies"
    monkeypatch.chdir(tmp_path)

    # Première compilation avec plusieurs faits
    initial_facts = [make_fact(f"Fait {i}") for i in range(5)]
    write_volume2(bio_dir, initial_facts)
    compiler = make_compiler(bio_dir)
    compiler.archiviste_controller = type("C", (), {
        "call_chat_api": make_archiviste([["ANCIEN_GROUPE"]] * 5)
    })()
    await compiler.compile()

    assert "ANCIEN_GROUPE" in json.loads(
        compiler.output_path.read_text(encoding="utf-8")
    )["groups"]

    # Simulation suppression + recréation volume2 (seulement 1 fait)
    write_volume2(bio_dir, [make_fact("Nouveau départ post-reset")])
    mock_new = make_archiviste([["NOUVEAU_GROUPE"]])
    compiler.archiviste_controller = type("C", (), {"call_chat_api": mock_new})()
    await compiler.compile()

    compiled = json.loads(compiler.output_path.read_text(encoding="utf-8"))
    assert "ANCIEN_GROUPE" not in compiled["groups"]
    assert "NOUVEAU_GROUPE" in compiled["groups"]
    assert compiled["metadata"]["last_scanned_index"] == 1


# ──────────────────────────────────────────────────────────────────────────────
# Scénario 4 — Bloc contexte vide si volume2 absent
# ──────────────────────────────────────────────────────────────────────────────

def test_context_block_empty_without_volume2(tmp_path, monkeypatch):
    """Sans volume2_structured.json, le bloc contexte doit être vide"""
    monkeypatch.chdir(tmp_path)
    result = get_bio_context_block("Yohan")
    assert result == ""


# ──────────────────────────────────────────────────────────────────────────────
# Scénario 5 — Idempotence double compilation
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_pipeline_idempotent_second_compile(tmp_path, monkeypatch):
    """
    Deux compilations consécutives sans nouveaux faits :
    - Aucun appel Archiviste supplémentaire
    - Aucun doublon dans les faits du groupe
    """
    bio_dir = tmp_path / "data" / "biographies"
    monkeypatch.chdir(tmp_path)

    write_volume2(bio_dir, [make_fact("Fait unique")])
    compiler = make_compiler(bio_dir)
    mock_call = make_archiviste([["GOUTS"]])
    compiler.archiviste_controller = type("C", (), {"call_chat_api": mock_call})()

    # Deux compilations
    await compiler.compile()
    await compiler.compile()

    # Un seul appel Archiviste (second tour = aucun nouveau fait)
    assert mock_call.call_count == 1

    compiled = json.loads(compiler.output_path.read_text(encoding="utf-8"))
    assert len(compiled["groups"]["GOUTS"]["facts"]) == 1


# ──────────────────────────────────────────────────────────────────────────────
# Scénario 6 — Bloc contexte correct après plusieurs groupes compilés
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_context_block_after_compilation(tmp_path, monkeypatch):
    """
    Le bloc retourné par get_bio_context_block() contient les faits
    dans l'ordre du volume2 (indépendamment des groupes compilés).
    """
    bio_dir = tmp_path / "data" / "biographies"
    monkeypatch.chdir(tmp_path)

    facts = [
        make_fact("Fait A"),
        make_fact("Fait B"),
        make_fact("Fait C"),
    ]
    write_volume2(bio_dir, facts)
    compiler = make_compiler(bio_dir)
    compiler.archiviste_controller = type("C", (), {
        "call_chat_api": make_archiviste([["G1"], ["G2"], ["G3"]])
    })()
    await compiler.compile()

    block = get_bio_context_block("yohan")
    assert block.startswith("[PROFIL YOHAN — faits observés]")
    for fact in facts:
        assert f"- {fact['content']}" in block
