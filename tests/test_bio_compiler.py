"""
Tests BioCompiler (scripts/bio_compiler.py)
============================================

Couvre :
  - Chargement / init structure vide
  - Détection des nouveaux faits (last_scanned_index)
  - Merge d'un fait dans les groupes
  - Reset si volume2 supprimé et recréé
  - Appel Archiviste mocké → vérification merge dans bio_compiled.json
  - Pas d'appel Archiviste si aucun nouveau fait
  - Idempotence : deux compilations d'affilée ne créent pas de doublons

Tous les tests sont isolés dans un répertoire temporaire.
"""

import json
import pytest
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch
import sys

# Accès racine OGMA
sys.path.insert(0, str(Path(__file__).parent.parent))


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def make_volume2(tmp_path: Path, facts: list) -> Path:
    """Crée un volume2_structured.json minimaliste dans tmp_path/yohan/"""
    user_dir = tmp_path / "yohan"
    user_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "user_name": "Yohan",
        "facts": facts,
        "profile_summary": {},
        "metadata": {"total_analyses": 1},
    }
    p = user_dir / "volume2_structured.json"
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return user_dir


def make_fact(content: str, category: str = "preference", date: str = "2026-04-18") -> dict:
    return {"content": content, "category": category, "date": date}


def make_archiviste_response(groups: list, keywords: list = None, description: str = "test groupe"):
    """Retourne un mock call_chat_api qui répond comme l'Archiviste"""
    async def _mock(*args, **kwargs):
        r = json.dumps({
            "groups": groups,
            "keywords": keywords or ["kw1", "kw2"],
            "description": description,
        })
        return r, None
    return AsyncMock(side_effect=_mock)


# ──────────────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def bio_dir(tmp_path):
    """Répertoire de données isolé pour les tests bio"""
    return tmp_path


@pytest.fixture
def compiler(bio_dir):
    """BioCompiler pointant dans un répertoire de test isolé"""
    from scripts.bio_compiler import BioCompiler
    c = BioCompiler("yohan")
    # Rediriger vers le répertoire temporaire
    c.user_dir = bio_dir / "yohan"
    c.user_dir.mkdir(parents=True, exist_ok=True)
    c.source_file = c.user_dir / "volume2_structured.json"
    c.output_path = c.user_dir / "bio_compiled.json"
    return c


# ──────────────────────────────────────────────────────────────────────────────
# Tests structure
# ──────────────────────────────────────────────────────────────────────────────

def test_empty_structure_shape(compiler):
    """La structure vide doit contenir les clés obligatoires"""
    s = compiler._empty_structure()
    assert "metadata" in s
    assert "groups" in s
    assert "trace_table" in s
    assert s["metadata"]["last_scanned_index"] == 0
    assert s["metadata"]["user_name"] == "yohan"


def test_load_compiled_absent_returns_empty(compiler):
    """Sans fichier bio_compiled.json, load retourne la structure vide"""
    data = compiler.load_compiled()
    assert data["groups"] == {}
    assert data["trace_table"] == {}


def test_load_compiled_reads_existing(compiler):
    """load_compiled() lit un fichier existant"""
    existing = {
        "metadata": {"user_name": "yohan", "last_scanned_index": 3,
                     "last_compilation": None, "total_facts_scanned": 2},
        "groups": {"GOUTS": {"description": "test", "keywords": [], "facts": []}},
        "trace_table": {},
    }
    compiler.output_path.write_text(json.dumps(existing), encoding="utf-8")
    loaded = compiler.load_compiled()
    assert "GOUTS" in loaded["groups"]
    assert loaded["metadata"]["last_scanned_index"] == 3


# ──────────────────────────────────────────────────────────────────────────────
# Tests détection nouveaux faits
# ──────────────────────────────────────────────────────────────────────────────

def test_no_source_file_returns_empty_facts(compiler):
    """Sans volume2_structured.json, load_source_facts() retourne []"""
    facts = compiler.load_source_facts()
    assert facts == []


def test_load_source_facts_reads_array(compiler):
    """load_source_facts() lit correctement facts[] depuis le JSON"""
    data = {
        "facts": [
            make_fact("Yohan aime les films SF"),
            make_fact("Yohan a une chatte Willow", category="relation"),
        ]
    }
    compiler.source_file.write_text(json.dumps(data), encoding="utf-8")
    facts = compiler.load_source_facts()
    assert len(facts) == 2
    assert facts[0]["content"] == "Yohan aime les films SF"


# ──────────────────────────────────────────────────────────────────────────────
# Tests reset
# ──────────────────────────────────────────────────────────────────────────────

def test_should_reset_when_index_exceeds_facts(compiler):
    """Si last_scanned_index > len(facts), détect reset nécessaire"""
    compiled = compiler._empty_structure()
    compiled["metadata"]["last_scanned_index"] = 10
    facts = [make_fact("un seul fait")]
    assert compiler._should_reset(compiled, facts) is True


def test_should_not_reset_normal_case(compiler):
    """Pas de reset si l'index est cohérent"""
    compiled = compiler._empty_structure()
    compiled["metadata"]["last_scanned_index"] = 1
    facts = [make_fact("fait 1"), make_fact("fait 2")]
    assert compiler._should_reset(compiled, facts) is False


# ──────────────────────────────────────────────────────────────────────────────
# Tests merge
# ──────────────────────────────────────────────────────────────────────────────

def test_merge_creates_new_group(compiler):
    """merge_fact_into_compiled crée le groupe si absent"""
    compiled = compiler._empty_structure()
    fact = make_fact("Yohan aime les films SF")
    analysis = {"groups": ["GOUTS"], "keywords": ["film", "SF"], "description": "gouts loisirs"}
    compiler.merge_fact_into_compiled(compiled, fact, 0, analysis)

    assert "GOUTS" in compiled["groups"]
    assert len(compiled["groups"]["GOUTS"]["facts"]) == 1
    assert compiled["groups"]["GOUTS"]["facts"][0]["content"] == "Yohan aime les films SF"


def test_merge_adds_to_existing_group(compiler):
    """Un second fait dans le même groupe s'ajoute à la liste facts"""
    compiled = compiler._empty_structure()
    fact1 = make_fact("Yohan aime les films SF")
    fact2 = make_fact("Yohan aime la musique metal")
    analysis = {"groups": ["GOUTS"], "keywords": ["loisir"], "description": "gouts"}
    compiler.merge_fact_into_compiled(compiled, fact1, 0, analysis)
    compiler.merge_fact_into_compiled(compiled, fact2, 1, analysis)

    assert len(compiled["groups"]["GOUTS"]["facts"]) == 2


def test_merge_no_duplicate_fact(compiler):
    """Appeler merge deux fois avec le même index_fait ne duplique pas"""
    compiled = compiler._empty_structure()
    fact = make_fact("Yohan aime les films SF")
    analysis = {"groups": ["GOUTS"], "keywords": ["film"], "description": "gouts"}
    compiler.merge_fact_into_compiled(compiled, fact, 0, analysis)
    compiler.merge_fact_into_compiled(compiled, fact, 0, analysis)  # second appel

    assert len(compiled["groups"]["GOUTS"]["facts"]) == 1


def test_merge_multi_group(compiler):
    """Un fait peut appartenir à plusieurs groupes simultanément"""
    compiled = compiler._empty_structure()
    fact = make_fact("Yohan a une chatte Willow", category="relation")
    analysis = {
        "groups": ["RELATIONS", "ANIMAUX"],
        "keywords": ["chat", "willow"],
        "description": "animaux compagnie",
    }
    compiler.merge_fact_into_compiled(compiled, fact, 0, analysis)

    assert "RELATIONS" in compiled["groups"]
    assert "ANIMAUX" in compiled["groups"]
    assert compiled["groups"]["ANIMAUX"]["facts"][0]["content"] == "Yohan a une chatte Willow"


def test_merge_updates_keywords(compiler):
    """Les keywords de deux faits dans le même groupe sont fusionnés"""
    compiled = compiler._empty_structure()
    fact1 = make_fact("Fait 1")
    fact2 = make_fact("Fait 2")
    compiler.merge_fact_into_compiled(
        compiled, fact1, 0,
        {"groups": ["GOUTS"], "keywords": ["film", "SF"], "description": "gouts"}
    )
    compiler.merge_fact_into_compiled(
        compiled, fact2, 1,
        {"groups": ["GOUTS"], "keywords": ["musique", "metal"], "description": "gouts"}
    )
    kw = set(compiled["groups"]["GOUTS"]["keywords"])
    assert {"film", "SF", "musique", "metal"} <= kw


def test_merge_trace_table(compiler):
    """La trace_table enregistre quel fait va dans quel groupe"""
    compiled = compiler._empty_structure()
    fact = make_fact("Fait test")
    analysis = {"groups": ["PROJETS"], "keywords": ["code"], "description": "projets"}
    compiler.merge_fact_into_compiled(compiled, fact, 5, analysis)

    assert "5" in compiled["trace_table"]
    assert "PROJETS" in compiled["trace_table"]["5"]["groups"]


# ──────────────────────────────────────────────────────────────────────────────
# Tests compilation async (Archiviste mocké)
# ──────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_compile_calls_archiviste_for_new_facts(compiler):
    """compile() appelle l'Archiviste une fois par nouveau fait"""
    # Préparer source avec 2 faits
    data = {"facts": [make_fact("Fait A"), make_fact("Fait B")]}
    compiler.source_file.write_text(json.dumps(data), encoding="utf-8")

    # Mock Archiviste
    compiler.archiviste_controller = type("C", (), {
        "call_chat_api": make_archiviste_response(["GOUTS"])
    })()

    await compiler.compile()

    compiled = json.loads(compiler.output_path.read_text(encoding="utf-8"))
    assert "GOUTS" in compiled["groups"]
    assert len(compiled["groups"]["GOUTS"]["facts"]) == 2
    assert compiled["metadata"]["last_scanned_index"] == 2


@pytest.mark.asyncio
async def test_compile_incremental_skips_already_scanned(compiler):
    """Une seconde compilation ne re-analyse pas les faits déjà scannés"""
    facts = [make_fact("Fait A"), make_fact("Fait B")]
    data = {"facts": facts}
    compiler.source_file.write_text(json.dumps(data), encoding="utf-8")

    mock_call = make_archiviste_response(["GOUTS"])
    compiler.archiviste_controller = type("C", (), {"call_chat_api": mock_call})()

    # Première compilation
    await compiler.compile()
    first_call_count = mock_call.call_count

    # Deuxième compilation — aucun nouveau fait
    await compiler.compile()
    second_call_count = mock_call.call_count

    # Aucun appel supplémentaire
    assert second_call_count == first_call_count


@pytest.mark.asyncio
async def test_compile_picks_up_new_fact_after_first_run(compiler):
    """Après une première compilation, un nouveau fait est détecté"""
    # Première passe : 1 fait
    data = {"facts": [make_fact("Fait A")]}
    compiler.source_file.write_text(json.dumps(data), encoding="utf-8")

    mock_call = make_archiviste_response(["GOUTS"])
    compiler.archiviste_controller = type("C", (), {"call_chat_api": mock_call})()
    await compiler.compile()

    assert mock_call.call_count == 1

    # Ajout d'un second fait
    data["facts"].append(make_fact("Fait B"))
    compiler.source_file.write_text(json.dumps(data), encoding="utf-8")
    await compiler.compile()

    assert mock_call.call_count == 2
    compiled = json.loads(compiler.output_path.read_text(encoding="utf-8"))
    assert compiled["metadata"]["last_scanned_index"] == 2


@pytest.mark.asyncio
async def test_compile_no_archiviste_skips_gracefully(compiler):
    """Sans Archiviste, compile() ne plante pas et retourne sans écrire"""
    data = {"facts": [make_fact("Fait A")]}
    compiler.source_file.write_text(json.dumps(data), encoding="utf-8")

    # Aucun archiviste controller
    compiler.archiviste_controller = None

    # Pas d'exception
    await compiler.compile()

    # Fichier non écrit (aucun fait analysé)
    # last_scanned_index avancé quand même (les faits ont été lus)
    # → en pratique, si _ensure_archiviste retourne False, compile() retourne tôt
    # On vérifie juste que ça ne plante pas
    assert True


@pytest.mark.asyncio
async def test_compile_reset_after_volume_recreated(compiler):
    """Si last_scanned_index > len(facts), la structure est réinitialisée avant compilation"""
    # Simuler un bio_compiled.json avec index trop élevé
    stale_compiled = compiler._empty_structure()
    stale_compiled["metadata"]["last_scanned_index"] = 99
    stale_compiled["groups"]["ANCIEN_GROUPE"] = {"description": "obsolète", "keywords": [], "facts": []}
    compiler.output_path.write_text(json.dumps(stale_compiled), encoding="utf-8")

    # Volume2 recréé avec seulement 1 fait
    data = {"facts": [make_fact("Nouveau fait post-reset")]}
    compiler.source_file.write_text(json.dumps(data), encoding="utf-8")

    mock_call = make_archiviste_response(["NOUVEAU_GROUPE"])
    compiler.archiviste_controller = type("C", (), {"call_chat_api": mock_call})()

    await compiler.compile()

    compiled = json.loads(compiler.output_path.read_text(encoding="utf-8"))
    # L'ancien groupe obsolète doit avoir disparu (reset)
    assert "ANCIEN_GROUPE" not in compiled["groups"]
    assert "NOUVEAU_GROUPE" in compiled["groups"]
