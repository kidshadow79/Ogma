#!/usr/bin/env python3
"""
🧪 TEST UNITAIRE — Cache Cognitif OGMA
========================================

Teste les fonctionnalités du cache cognitif :
- Phase 7.1 : add / delete / update / clear + parse + cleanup
- Phase 7.2 : snapshot Dream Engine
- Phase 7.3 : élagage (max 10 conversations)

Usage :
    pytest tests/test_cognitive_cache.py -v
"""

import sys
import os
import json
import shutil
import asyncio
import pytest
from pathlib import Path
from unittest.mock import patch

# Chemin racine du projet
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# Dossier cache temporaire pour les tests (ne jamais toucher data/cognitive_cache en test)
_TEMP_CACHE_DIR = ROOT / "tests" / "fixtures" / "cognitive_cache_test"


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture(autouse=True)
def isolate_cache_dir(tmp_path, monkeypatch):
    """
    Redirige le dossier cache vers un répertoire temporaire isolé.
    Garantit qu'aucun test ne touche data/cognitive_cache réel.
    """
    # Patcher _CACHE_DIR dans les deux modules
    monkeypatch.setattr(
        "extensions.cognitive_cache.cache_manager._CACHE_DIR",
        tmp_path / "cognitive_cache"
    )
    monkeypatch.setattr(
        "extensions.cognitive_cache.cache_cleanup._CACHE_DIR",
        tmp_path / "cognitive_cache"
    )
    (tmp_path / "cognitive_cache").mkdir(parents=True, exist_ok=True)
    yield tmp_path / "cognitive_cache"


@pytest.fixture
def conv_id():
    return "2026-04-04_14-23-11"


# ============================================================
# PHASE 7.1 — CRUD : add / delete / update / clear
# ============================================================

class TestCacheManager:
    """Tests unitaires du cache_manager (CRUD)."""

    def test_load_cache_vide(self, conv_id):
        """Un cache inexistant retourne une structure vide valide."""
        from extensions.cognitive_cache.cache_manager import load_cache
        data = load_cache(conv_id)
        assert data["conv_id"] == conv_id
        assert data["entries"] == []
        assert "created_at" in data

    def test_add_entry_directive(self, conv_id):
        """Ajoute une entrée de type directive."""
        from extensions.cognitive_cache.cache_manager import add_entry, get_active_entries
        entry_id = add_entry(conv_id, "directive", "ne pas rédiger à sa place")
        assert entry_id is not None
        assert entry_id.startswith("cache-")
        entries = get_active_entries(conv_id)
        assert len(entries) == 1
        assert entries[0]["type"] == "directive"
        assert entries[0]["content"] == "ne pas rédiger à sa place"
        assert entries[0]["active"] is True

    def test_add_entry_type_inconnu_force_observation(self, conv_id):
        """Un type inconnu est forcé en 'observation'."""
        from extensions.cognitive_cache.cache_manager import add_entry, get_active_entries
        add_entry(conv_id, "type_inexistant", "contenu test")
        entries = get_active_entries(conv_id)
        assert entries[0]["type"] == "observation"

    def test_add_entry_contenu_vide_ignore(self, conv_id):
        """Un contenu vide est ignoré (retourne None)."""
        from extensions.cognitive_cache.cache_manager import add_entry
        result = add_entry(conv_id, "directive", "   ")
        assert result is None

    def test_delete_entry(self, conv_id):
        """Supprime logiquement une entrée (active=False)."""
        from extensions.cognitive_cache.cache_manager import add_entry, delete_entry, get_active_entries
        eid = add_entry(conv_id, "observation", "pensée secrète")
        assert eid is not None
        ok = delete_entry(conv_id, eid)
        assert ok is True
        entries = get_active_entries(conv_id)
        assert len(entries) == 0  # désactivée, donc absente des actives

    def test_delete_entry_id_inconnu(self, conv_id):
        """Supprimer un ID inexistant retourne False."""
        from extensions.cognitive_cache.cache_manager import delete_entry
        ok = delete_entry(conv_id, "cache-xxxxxxxx")
        assert ok is False

    def test_update_entry(self, conv_id):
        """Modifie le contenu d'une entrée existante."""
        from extensions.cognitive_cache.cache_manager import add_entry, update_entry, get_active_entries
        eid = add_entry(conv_id, "idea_pending", "parler du projet")
        assert eid is not None
        ok = update_entry(conv_id, eid, "parler du projet OGMA")
        assert ok is True
        entries = get_active_entries(conv_id)
        assert entries[0]["content"] == "parler du projet OGMA"

    def test_update_contenu_vide_ignore(self, conv_id):
        """Modifier avec un contenu vide retourne False sans changer l'entrée."""
        from extensions.cognitive_cache.cache_manager import add_entry, update_entry, get_active_entries
        eid = add_entry(conv_id, "directive", "contenu original")
        ok = update_entry(conv_id, eid, "   ")
        assert ok is False
        entries = get_active_entries(conv_id)
        assert entries[0]["content"] == "contenu original"

    def test_clear_cache(self, conv_id):
        """CACHE_CLEAR désactive toutes les entrées."""
        from extensions.cognitive_cache.cache_manager import add_entry, clear_cache, get_active_entries
        add_entry(conv_id, "directive", "entrée 1")
        add_entry(conv_id, "observation", "entrée 2")
        add_entry(conv_id, "context_anchor", "entrée 3")
        assert len(get_active_entries(conv_id)) == 3
        ok = clear_cache(conv_id)
        assert ok is True
        assert len(get_active_entries(conv_id)) == 0

    def test_persistance_json_atomique(self, conv_id, isolate_cache_dir):
        """Les données sont bien persistées dans le fichier JSON."""
        from extensions.cognitive_cache.cache_manager import add_entry, _cache_path
        eid = add_entry(conv_id, "directive", "persistance test")
        path = _cache_path(conv_id)
        assert path.exists()
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert any(e["id"] == eid for e in data["entries"])

    def test_get_summary_for_injection(self, conv_id):
        """Le résumé injecté dans le prompt contient bien les entrées actives."""
        from extensions.cognitive_cache.cache_manager import add_entry, get_summary_for_injection
        add_entry(conv_id, "directive", "ne pas coder à ma place")
        add_entry(conv_id, "observation", "l'utilisateur semble fatigué")
        summary = get_summary_for_injection(conv_id)
        assert "[CACHE COGNITIF ACTIF]" in summary
        assert "ne pas coder à ma place" in summary
        assert "l'utilisateur semble fatigué" in summary

    def test_get_summary_vide_si_aucune_entree(self, conv_id):
        """Un cache vide retourne une chaîne vide pour injection."""
        from extensions.cognitive_cache.cache_manager import get_summary_for_injection
        summary = get_summary_for_injection(conv_id)
        assert summary == ""


# ============================================================
# PHASE 7.1 — PARSER : parse_cache_commands / strip
# ============================================================

class TestCacheParser:
    """Tests du parser regex (cache_parser.py)."""

    def test_has_cache_commands_detecte(self):
        """Détecte la présence d'une commande CACHE_ADD."""
        from extensions.cognitive_cache.cache_parser import has_cache_commands
        assert has_cache_commands("Voici ma réponse.\nCACHE_ADD:directive:ne pas coder") is True

    def test_has_cache_commands_absent(self):
        """Retourne False si aucune commande présente."""
        from extensions.cognitive_cache.cache_parser import has_cache_commands
        assert has_cache_commands("Bonjour, comment puis-je t'aider ?") is False

    def test_parse_cache_add(self):
        """Parse une commande CACHE_ADD correctement."""
        from extensions.cognitive_cache.cache_parser import parse_cache_commands
        text = "Bonne question.\nCACHE_ADD:directive:ne pas écrire à sa place"
        ops = parse_cache_commands(text)
        assert len(ops) == 1
        assert ops[0]["op"] == "add"
        assert ops[0]["type"] == "directive"
        assert "ne pas écrire à sa place" in ops[0]["content"]

    def test_parse_cache_add_insensible_casse(self):
        """CACHE_ADD est insensible à la casse."""
        from extensions.cognitive_cache.cache_parser import parse_cache_commands
        ops = parse_cache_commands("cache_add:observation:test casse")
        assert len(ops) == 1
        assert ops[0]["op"] == "add"

    def test_parse_cache_delete(self):
        """Parse une commande CACHE_DELETE."""
        from extensions.cognitive_cache.cache_parser import parse_cache_commands
        ops = parse_cache_commands("CACHE_DELETE:cache-abcd1234")
        assert len(ops) == 1
        assert ops[0]["op"] == "delete"
        assert ops[0]["id"] == "cache-abcd1234"

    def test_parse_cache_update(self):
        """Parse une commande CACHE_UPDATE."""
        from extensions.cognitive_cache.cache_parser import parse_cache_commands
        ops = parse_cache_commands("CACHE_UPDATE:cache-abcd1234:nouveau contenu mis à jour")
        assert len(ops) == 1
        assert ops[0]["op"] == "update"
        assert ops[0]["id"] == "cache-abcd1234"
        assert "nouveau contenu" in ops[0]["content"]

    def test_parse_cache_clear(self):
        """Parse une commande CACHE_CLEAR."""
        from extensions.cognitive_cache.cache_parser import parse_cache_commands
        ops = parse_cache_commands("Voici ma réponse.\nCACHE_CLEAR")
        # CACHE_CLEAR est prioritaire — il est en premier
        assert any(op["op"] == "clear" for op in ops)

    def test_parse_multiple_commands(self):
        """Parse plusieurs commandes dans un même texte."""
        from extensions.cognitive_cache.cache_parser import parse_cache_commands
        text = (
            "Réponse normale ici.\n"
            "CACHE_ADD:directive:directive importante\n"
            "CACHE_ADD:observation:observation secrète"
        )
        ops = parse_cache_commands(text)
        add_ops = [o for o in ops if o["op"] == "add"]
        assert len(add_ops) == 2

    def test_strip_cache_commands(self):
        """Les commandes sont supprimées du texte affiché à l'utilisateur."""
        from extensions.cognitive_cache.cache_parser import strip_cache_commands
        text = "Voici ma réponse visible.\nCACHE_ADD:directive:ceci est caché"
        cleaned = strip_cache_commands(text)
        assert "CACHE_ADD" not in cleaned
        assert "Voici ma réponse visible." in cleaned

    def test_strip_sans_commandes(self):
        """Un texte sans commandes est retourné intact."""
        from extensions.cognitive_cache.cache_parser import strip_cache_commands
        original = "Texte normal sans commandes."
        assert strip_cache_commands(original) == original


# ============================================================
# PHASE 7.2 — SNAPSHOT Dream Engine
# ============================================================

class TestCacheSnapshot:
    """Tests du snapshot figé pour Dream Engine."""

    def test_snapshot_copie_profonde(self, conv_id):
        """Le snapshot est une copie profonde — modification live n'affecte pas snapshot."""
        from extensions.cognitive_cache.cache_manager import (
            add_entry, get_snapshot, get_active_entries,
            add_entry as add_after_snapshot
        )
        add_entry(conv_id, "directive", "entrée avant snapshot")
        snapshot = get_snapshot(conv_id)

        # Ajouter une entrée APRÈS le snapshot
        add_after_snapshot(conv_id, "observation", "entrée après snapshot")

        # Le snapshot ne doit pas contenir la nouvelle entrée
        snapshot_entries = [e for e in snapshot["entries"] if e.get("active", True)]
        assert len(snapshot_entries) == 1
        assert all("après snapshot" not in e["content"] for e in snapshot_entries)

        # Le cache live doit contenir les deux
        live_entries = get_active_entries(conv_id)
        assert len(live_entries) == 2

    def test_snapshot_contient_timestamp(self, conv_id):
        """Le snapshot contient un champ snapshot_at."""
        from extensions.cognitive_cache.cache_manager import add_entry, get_snapshot
        add_entry(conv_id, "context_anchor", "ancrage test")
        snapshot = get_snapshot(conv_id)
        assert "snapshot_at" in snapshot
        assert snapshot["snapshot_at"] is not None

    def test_snapshot_vide_si_cache_vide(self, conv_id):
        """Un snapshot d'un cache vide retourne des entrées vides."""
        from extensions.cognitive_cache.cache_manager import get_snapshot
        snapshot = get_snapshot(conv_id)
        assert snapshot["entries"] == []

    def test_get_snapshot_summary_formate(self, conv_id):
        """get_snapshot_summary génère le texte pour le prompt de rêve."""
        from extensions.cognitive_cache.cache_manager import add_entry, get_snapshot, get_snapshot_summary
        add_entry(conv_id, "idea_pending", "idée à aborder plus tard")
        snapshot = get_snapshot(conv_id)
        text = get_snapshot_summary(snapshot)
        assert "[PENSÉES EN FOND" in text
        assert "idée à aborder plus tard" in text

    def test_get_snapshot_summary_vide_si_rien(self, conv_id):
        """Un snapshot vide retourne une chaîne vide."""
        from extensions.cognitive_cache.cache_manager import get_snapshot, get_snapshot_summary
        snapshot = get_snapshot(conv_id)
        assert get_snapshot_summary(snapshot) == ""


# ============================================================
# PHASE 7.3 — ÉLAGAGE (max 10 conversations)
# ============================================================

class TestCacheCleanup:
    """Tests de l'élagage du cache."""

    def _create_fake_cache(self, cache_dir: Path, conv_id: str, offset_seconds: int = 0):
        """Crée un fichier cache JSON factice."""
        from datetime import datetime, timedelta
        dt = datetime(2026, 4, 1, 12, 0, 0) + timedelta(seconds=offset_seconds)
        data = {
            "conv_id": conv_id,
            "created_at": dt.isoformat(),
            "updated_at": dt.isoformat(),
            "entries": [{"id": f"cache-{conv_id[:8]}", "type": "directive",
                         "content": f"Test {conv_id}", "active": True}]
        }
        path = cache_dir / f"{conv_id}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
        return path

    def test_cleanup_sous_limite(self, isolate_cache_dir):
        """Moins de 10 fichiers → aucune suppression."""
        from extensions.cognitive_cache.cache_cleanup import cleanup_old_caches
        for i in range(5):
            self._create_fake_cache(isolate_cache_dir, f"conv-{i:04d}", offset_seconds=i * 60)
        stats = cleanup_old_caches(max_conversations=10)
        assert stats["deleted"] == 0
        assert stats["kept"] == 5

    def test_cleanup_au_dessus_limite(self, isolate_cache_dir):
        """12 fichiers avec max=10 → 2 supprimés (les plus anciens)."""
        from extensions.cognitive_cache.cache_cleanup import cleanup_old_caches
        for i in range(12):
            self._create_fake_cache(isolate_cache_dir, f"conv-{i:04d}", offset_seconds=i * 60)
        stats = cleanup_old_caches(max_conversations=10)
        assert stats["deleted"] == 2
        assert stats["kept"] == 10
        assert stats["total"] == 12

    def test_cleanup_conserve_les_plus_recents(self, isolate_cache_dir):
        """Les fichiers les plus récents sont conservés, les plus anciens supprimés."""
        from extensions.cognitive_cache.cache_cleanup import cleanup_old_caches
        for i in range(12):
            self._create_fake_cache(isolate_cache_dir, f"conv-{i:04d}", offset_seconds=i * 3600)
        cleanup_old_caches(max_conversations=10)
        # Les 2 plus anciens (conv-0000, conv-0001) doivent être supprimés
        assert not (isolate_cache_dir / "conv-0000.json").exists()
        assert not (isolate_cache_dir / "conv-0001.json").exists()
        # Les 10 plus récents doivent exister
        for i in range(2, 12):
            assert (isolate_cache_dir / f"conv-{i:04d}.json").exists()

    def test_cleanup_dossier_inexistant(self, isolate_cache_dir):
        """cleanup sur un dossier vide/inexistant ne crash pas."""
        from extensions.cognitive_cache.cache_cleanup import cleanup_old_caches
        # Supprimer le dossier temporaire
        shutil.rmtree(isolate_cache_dir)
        stats = cleanup_old_caches(max_conversations=10)
        assert stats["deleted"] == 0

    @pytest.mark.asyncio
    async def test_cleanup_async(self, isolate_cache_dir):
        """Version async fonctionne correctement."""
        from extensions.cognitive_cache.cache_cleanup import cleanup_old_caches_async
        for i in range(12):
            self._create_fake_cache(isolate_cache_dir, f"conv-{i:04d}", offset_seconds=i * 60)
        stats = await cleanup_old_caches_async(max_conversations=10)
        assert stats["deleted"] == 2

    def test_get_cache_stats(self, isolate_cache_dir):
        """get_cache_stats retourne les bonnes statistiques."""
        from extensions.cognitive_cache.cache_cleanup import get_cache_stats
        for i in range(3):
            self._create_fake_cache(isolate_cache_dir, f"conv-{i:04d}", offset_seconds=i * 60)
        stats = get_cache_stats()
        assert stats["count"] == 3
        assert stats["oldest"] is not None
        assert stats["newest"] is not None


# ============================================================
# PHASE 7.1 — API PUBLIQUE singleton
# ============================================================

class TestCachePublicAPI:
    """Tests de l'API publique du module (singleton)."""

    def test_initialize_et_is_available(self):
        """initialize_cognitive_cache retourne True et is_available devient True."""
        from extensions.cognitive_cache import initialize_cognitive_cache, is_available
        # Reset état du singleton
        import extensions.cognitive_cache as cc
        cc._initialized = False
        cc._current_conv_id = None

        result = initialize_cognitive_cache("2026-04-04_test")
        assert result is True
        assert is_available() is True

    def test_set_current_conv(self):
        """set_current_conv met à jour l'ID de conversation courante."""
        from extensions.cognitive_cache import initialize_cognitive_cache, set_current_conv, get_current_conv_id
        import extensions.cognitive_cache as cc
        cc._initialized = False
        cc._current_conv_id = None

        initialize_cognitive_cache()
        set_current_conv("2026-04-04_nouvelle-conv")
        assert get_current_conv_id() == "2026-04-04_nouvelle-conv"

    def test_apply_cache_operations_sans_init_retourne_vide(self):
        """apply_cache_operations sans initialisation retourne une liste vide."""
        import extensions.cognitive_cache as cc
        cc._initialized = False
        cc._current_conv_id = None

        from extensions.cognitive_cache import apply_cache_operations
        ops = apply_cache_operations("CACHE_ADD:directive:test")
        assert ops == []

    def test_apply_cache_operations_avec_init(self, conv_id):
        """apply_cache_operations applique correctement les commandes."""
        import extensions.cognitive_cache as cc
        cc._initialized = True
        cc._current_conv_id = conv_id

        from extensions.cognitive_cache import apply_cache_operations
        text = "Ma réponse normale.\nCACHE_ADD:observation:observation secrète de test"
        ops = apply_cache_operations(text, conv_id)
        assert len(ops) == 1
        assert ops[0]["op"] == "add"

    def test_get_cache_summary_vide_si_pas_init(self):
        """get_cache_summary retourne '' si non initialisé."""
        import extensions.cognitive_cache as cc
        cc._initialized = False
        cc._current_conv_id = None

        from extensions.cognitive_cache import get_cache_summary
        assert get_cache_summary() == ""

    def test_strip_commands_from_response(self):
        """strip_commands_from_response nettoie la réponse avant affichage."""
        from extensions.cognitive_cache import strip_commands_from_response
        text = "Voici ma réponse.\nCACHE_ADD:directive:hidden"
        cleaned = strip_commands_from_response(text)
        assert "CACHE_ADD" not in cleaned
        assert "Voici ma réponse." in cleaned

    def test_get_continuation_context_vide_si_aucun_fichier(self):
        """get_continuation_context retourne '' si aucun fichier cache."""
        from extensions.cognitive_cache import get_continuation_context
        result = get_continuation_context(max_convs=3)
        # Avec le dossier isolé vide, aucun fichier → chaîne vide
        assert result == ""


# ============================================================
# MAIN — Exécution directe possible
# ============================================================

if __name__ == "__main__":
    import subprocess
    subprocess.run([
        sys.executable, "-m", "pytest",
        __file__, "-v", "--tb=short"
    ])
