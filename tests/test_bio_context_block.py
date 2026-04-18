"""
Tests get_bio_context_block() (extensions/biographie_profil/__init__.py)
=========================================================================

Couvre :
  - Retourne "" si le fichier est absent
  - Retourne "" si facts[] est vide
  - Génère le bon format de bloc ([PROFIL X — faits observés]\n- fait)
  - Respecte la limite max_facts
  - Gère les faits avec content vide (ignorés)
  - Insensible à la casse du nom utilisateur (recherche lower())
  - Ne plante pas si le JSON est corrompu

Tous les tests redirigent le chemin data/biographies via monkeypatch.
"""

import json
import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))


# ──────────────────────────────────────────────────────────────────────────────
# Fixture : volume2_structured.json dans tmp_path
# ──────────────────────────────────────────────────────────────────────────────

def write_volume2(tmp_path: Path, user_name: str, facts: list) -> Path:
    # La fonction cherche data/biographies/{user_name.lower()}/ depuis le cwd
    user_dir = tmp_path / "data" / "biographies" / user_name.lower()
    user_dir.mkdir(parents=True, exist_ok=True)
    p = user_dir / "volume2_structured.json"
    p.write_text(
        json.dumps({"user_name": user_name, "facts": facts}),
        encoding="utf-8",
    )
    return p


def make_fact(content: str, category: str = "preference") -> dict:
    return {"content": content, "category": category, "date": "2026-04-18"}


# ──────────────────────────────────────────────────────────────────────────────
# Import de la fonction à tester
# ──────────────────────────────────────────────────────────────────────────────

from extensions.biographie_profil import get_bio_context_block


# ──────────────────────────────────────────────────────────────────────────────
# Tests cas "retour vide"
# ──────────────────────────────────────────────────────────────────────────────

def test_returns_empty_when_file_absent(tmp_path, monkeypatch):
    """Aucun fichier → chaîne vide"""
    monkeypatch.chdir(tmp_path)
    result = get_bio_context_block("Yohan")
    assert result == ""


def test_returns_empty_when_user_name_empty(tmp_path, monkeypatch):
    """user_name vide ou None → chaîne vide immédiate"""
    monkeypatch.chdir(tmp_path)
    assert get_bio_context_block("") == ""
    assert get_bio_context_block(None) == ""


def test_returns_empty_when_facts_empty(tmp_path, monkeypatch):
    """facts[] vide → chaîne vide"""
    monkeypatch.chdir(tmp_path)
    write_volume2(tmp_path, "Yohan", [])
    result = get_bio_context_block("Yohan")
    assert result == ""


def test_returns_empty_when_all_contents_empty(tmp_path, monkeypatch):
    """Faits sans champ content non vide → chaîne vide"""
    monkeypatch.chdir(tmp_path)
    write_volume2(tmp_path, "Yohan", [{"content": "", "category": "pref"}])
    result = get_bio_context_block("Yohan")
    assert result == ""


# ──────────────────────────────────────────────────────────────────────────────
# Tests format de sortie
# ──────────────────────────────────────────────────────────────────────────────

def test_header_format(tmp_path, monkeypatch):
    """Le header doit être [PROFIL YOHAN — faits observés]"""
    monkeypatch.chdir(tmp_path)
    write_volume2(tmp_path, "Yohan", [make_fact("Yohan aime les films SF")])
    result = get_bio_context_block("Yohan")
    first_line = result.split("\n")[0]
    assert first_line == "[PROFIL YOHAN — faits observés]"


def test_facts_are_bullet_lines(tmp_path, monkeypatch):
    """Chaque fait doit apparaître en ligne '- contenu'"""
    monkeypatch.chdir(tmp_path)
    write_volume2(tmp_path, "Yohan", [
        make_fact("Yohan aime les films SF"),
        make_fact("Yohan a une chatte Willow"),
    ])
    result = get_bio_context_block("Yohan")
    lines = result.split("\n")
    assert lines[1] == "- Yohan aime les films SF"
    assert lines[2] == "- Yohan a une chatte Willow"


def test_total_lines_count(tmp_path, monkeypatch):
    """header + N faits = N+1 lignes"""
    monkeypatch.chdir(tmp_path)
    facts = [make_fact(f"Fait {i}") for i in range(5)]
    write_volume2(tmp_path, "Yohan", facts)
    result = get_bio_context_block("Yohan")
    lines = result.split("\n")
    assert len(lines) == 6  # 1 header + 5 faits


# ──────────────────────────────────────────────────────────────────────────────
# Tests limite max_facts
# ──────────────────────────────────────────────────────────────────────────────

def test_max_facts_limits_output(tmp_path, monkeypatch):
    """max_facts=3 ne retourne que les 3 premiers faits"""
    monkeypatch.chdir(tmp_path)
    facts = [make_fact(f"Fait {i}") for i in range(10)]
    write_volume2(tmp_path, "Yohan", facts)
    result = get_bio_context_block("Yohan", max_facts=3)
    lines = [l for l in result.split("\n") if l.startswith("- ")]
    assert len(lines) == 3
    assert lines[0] == "- Fait 0"
    assert lines[2] == "- Fait 2"


def test_max_facts_default_is_15(tmp_path, monkeypatch):
    """Le défaut max_facts=15 limite à 15 faits"""
    monkeypatch.chdir(tmp_path)
    facts = [make_fact(f"Fait {i}") for i in range(20)]
    write_volume2(tmp_path, "Yohan", facts)
    result = get_bio_context_block("Yohan")  # max_facts par défaut
    lines = [l for l in result.split("\n") if l.startswith("- ")]
    assert len(lines) == 15


# ──────────────────────────────────────────────────────────────────────────────
# Tests robustesse
# ──────────────────────────────────────────────────────────────────────────────

def test_case_insensitive_path(tmp_path, monkeypatch):
    """user_name en majuscules ou minuscules trouve le bon répertoire"""
    monkeypatch.chdir(tmp_path)
    write_volume2(tmp_path, "Yohan", [make_fact("Fait test")])
    # La fonction cherche data/biographies/{user_name.lower()}/
    result = get_bio_context_block("YOHAN")
    assert result != ""
    assert "- Fait test" in result


def test_filters_facts_without_content(tmp_path, monkeypatch):
    """Les faits avec content absent ou vide sont ignorés"""
    monkeypatch.chdir(tmp_path)
    facts = [
        {"category": "pref"},           # content absent
        {"content": "", "category": "pref"},  # content vide
        make_fact("Fait valide"),
    ]
    write_volume2(tmp_path, "Yohan", facts)
    result = get_bio_context_block("Yohan")
    lines = [l for l in result.split("\n") if l.startswith("- ")]
    assert len(lines) == 1
    assert lines[0] == "- Fait valide"


def test_no_crash_on_corrupted_json(tmp_path, monkeypatch):
    """Un JSON corrompu ne plante pas → retourne chaîne vide"""
    monkeypatch.chdir(tmp_path)
    user_dir = tmp_path / "data" / "biographies" / "yohan"
    user_dir.mkdir(parents=True, exist_ok=True)
    (user_dir / "volume2_structured.json").write_text("{corrupted json", encoding="utf-8")
    result = get_bio_context_block("Yohan")
    assert result == ""


def test_no_crash_on_missing_facts_key(tmp_path, monkeypatch):
    """Un JSON sans clé 'facts' ne plante pas → retourne chaîne vide"""
    monkeypatch.chdir(tmp_path)
    user_dir = tmp_path / "data" / "biographies" / "yohan"
    user_dir.mkdir(parents=True, exist_ok=True)
    (user_dir / "volume2_structured.json").write_text(
        json.dumps({"user_name": "Yohan"}), encoding="utf-8"
    )
    result = get_bio_context_block("Yohan")
    assert result == ""
