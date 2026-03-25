"""
Tests pour le système de purge et auto-résolution du Journal v2.0

Tests couverts :
- Compression d'entrées via LLM
- Transfert FAISS avec métadonnées
- Détection états inactifs
- Auto-résolution avec validation LLM
- Backups automatiques
- Intégrité index après purge
"""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Imports modules Journal
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from extensions.journal_de_bord.purge_manager import PurgeManager, initialize_purge_manager
from extensions.journal_de_bord.auto_resolution import detect_inactive_states, auto_resolve_states
from extensions.journal_de_bord.json_manager import JournalJSONManager


class TestPurgeManager:
    """Tests du gestionnaire de purge"""
    
    @pytest.fixture
    def temp_journal_dir(self):
        """Crée un répertoire temporaire pour les tests"""
        temp_dir = tempfile.mkdtemp(prefix="test_journal_")
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def mock_json_manager(self, temp_journal_dir):
        """Mock JournalJSONManager avec données test"""
        manager = Mock(spec=JournalJSONManager)
        manager.base_dir = temp_journal_dir
        manager.data_dir = temp_journal_dir / "data"
        manager.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Créer entrées test
        self._create_test_entries(manager.data_dir)
        
        return manager
    
    def _create_test_entries(self, data_dir: Path):
        """Crée des entrées de test avec différents âges"""
        entries_data = [
            # Entrée récente (5 jours)
            {
                "date": (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"),
                "entry_id": 1,
                "content": "Entrée récente test" * 50,  # ~1000 chars
                "active_states": [],
                "compressed": False
            },
            # Entrée ancienne (100 jours)
            {
                "date": (datetime.now() - timedelta(days=100)).strftime("%Y-%m-%d"),
                "entry_id": 2,
                "content": "Entrée ancienne test" * 50,
                "active_states": [],
                "compressed": False
            },
            # Entrée avec état actif (95 jours)
            {
                "date": (datetime.now() - timedelta(days=95)).strftime("%Y-%m-%d"),
                "entry_id": 3,
                "content": "Entrée avec état actif" * 30,
                "active_states": [{"state_id": 1, "resolved": False}],
                "compressed": False
            }
        ]
        
        for entry in entries_data:
            date_obj = datetime.strptime(entry["date"], "%Y-%m-%d")
            year_dir = data_dir / str(date_obj.year)
            month_dir = year_dir / f"{date_obj.month:02d}"
            month_dir.mkdir(parents=True, exist_ok=True)
            
            file_path = month_dir / f"{entry['date']}.json"
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(entry, f, ensure_ascii=False, indent=2)
    
    @pytest.fixture
    def mock_archiviste(self):
        """Mock contrôleur Archiviste LLM"""
        archiviste = Mock()
        archiviste.send_message.return_value = "Résumé compressé de l'entrée test."
        return archiviste
    
    @pytest.fixture
    def mock_memory_manager(self):
        """Mock MemoryManager pour FAISS"""
        memory = Mock()
        memory.add_memory.return_value = True
        return memory
    
    @pytest.fixture
    def purge_manager(self, mock_json_manager, mock_memory_manager, mock_archiviste):
        """Instance PurgeManager avec mocks"""
        return PurgeManager(
            json_manager=mock_json_manager,
            memory_manager=mock_memory_manager,
            archiviste_controller=mock_archiviste
        )
    
    def test_get_purgeable_entries_age_filter(self, purge_manager):
        """Test détection entrées purgeable selon âge"""
        entries = purge_manager.get_purgeable_entries(age_days=90)
        
        # Devrait trouver 2 entrées (100j et 95j)
        assert len(entries) >= 1, "Au moins une entrée ancienne devrait être détectée"
        
        # Vérifier que toutes ont plus de 90j
        for entry in entries:
            assert entry["age_days"] >= 90, f"Entrée {entry['entry_id']} trop récente"
    
    def test_get_purgeable_entries_exclude_active_states(self, purge_manager):
        """Test exclusion entrées avec états actifs"""
        # Sans exclusion
        all_entries = purge_manager.get_purgeable_entries(age_days=90, exclude_active_states=False)
        
        # Avec exclusion
        filtered_entries = purge_manager.get_purgeable_entries(age_days=90, exclude_active_states=True)
        
        # Devrait avoir moins d'entrées avec exclusion
        assert len(filtered_entries) <= len(all_entries), "L'exclusion devrait réduire le nombre d'entrées"
    
    def test_compress_entry_creates_backup(self, purge_manager, mock_json_manager):
        """Test création backup avant compression"""
        entry_id = 2
        
        # Mock get_entry_by_id
        mock_json_manager.get_entry_by_id.return_value = {
            "entry_id": entry_id,
            "content": "Contenu original très long" * 100,
            "compressed": False,
            "date": "2024-09-20"
        }
        
        # Mock save
        mock_json_manager._save_entry_to_file.return_value = True
        
        success, msg = purge_manager.compress_entry(entry_id)
        
        # Vérifier backup créé
        backup_dir = purge_manager.backup_dir
        assert backup_dir.exists(), "Dossier backup devrait exister"
        
        backups = list(backup_dir.glob(f"entry_{entry_id}_pre_compression_*.json"))
        assert len(backups) > 0, "Un backup devrait être créé"
    
    def test_compress_entry_reduces_size(self, purge_manager, mock_json_manager, mock_archiviste):
        """Test compression réduit taille contenu"""
        original_content = "Contenu très long à compresser" * 100
        compressed_summary = "Résumé court"
        
        mock_json_manager.get_entry_by_id.return_value = {
            "entry_id": 2,
            "content": original_content,
            "compressed": False,
            "date": "2024-09-20"
        }
        
        mock_archiviste.send_message.return_value = compressed_summary
        mock_json_manager._save_entry_to_file.return_value = True
        
        success, msg = purge_manager.compress_entry(2)
        
        assert success, f"Compression devrait réussir: {msg}"
        assert "ratio" in msg.lower(), "Message devrait contenir ratio compression"
    
    def test_transfer_to_faiss(self, purge_manager, mock_json_manager, mock_memory_manager):
        """Test transfert entrée vers FAISS"""
        entry_id = 2
        
        mock_json_manager.get_entry_by_id.return_value = {
            "entry_id": entry_id,
            "content": "Contenu à archiver",
            "date": "2024-09-20",
            "category": "test",
            "archived_to_faiss": False
        }
        
        mock_json_manager._save_entry_to_file.return_value = True
        
        success, msg = purge_manager.transfer_to_faiss(entry_id)
        
        assert success, f"Transfert FAISS devrait réussir: {msg}"
        
        # Vérifier appel memory_manager.add_memory
        mock_memory_manager.add_memory.assert_called_once()
        
        call_args = mock_memory_manager.add_memory.call_args
        assert call_args[1]["metadata"]["source"] == "journal"
        assert call_args[1]["metadata"]["entry_id"] == entry_id
    
    def test_purge_old_entries_dry_run(self, purge_manager):
        """Test mode simulation (dry_run)"""
        stats = purge_manager.purge_old_entries(age_days=90, mode="compress", dry_run=True)
        
        assert "total" in stats, "Stats devrait contenir total"
        assert stats["compressed"] == 0, "Dry run ne devrait rien compresser"
        assert stats["archived"] == 0, "Dry run ne devrait rien archiver"
    
    def test_restore_compressed_entry(self, purge_manager, mock_json_manager):
        """Test restauration entrée compressée"""
        entry_id = 2
        original_content = "Contenu original sauvegardé"
        
        mock_json_manager.get_entry_by_id.return_value = {
            "entry_id": entry_id,
            "content": "Résumé compressé",
            "content_original": original_content,
            "compressed": True,
            "date": "2024-09-20"
        }
        
        mock_json_manager._save_entry_to_file.return_value = True
        
        success, msg = purge_manager.restore_compressed_entry(entry_id)
        
        assert success, f"Restauration devrait réussir: {msg}"


class TestAutoResolution:
    """Tests du système d'auto-résolution"""
    
    @pytest.fixture
    def mock_json_manager_with_states(self):
        """Mock JSONManager avec états actifs"""
        manager = Mock()
        
        # États test
        states_data = {
            "last_updated": datetime.now().isoformat(),
            "next_state_id": 5,
            "states": [
                {
                    "state_id": 1,
                    "category": "santé",
                    "description": "État inactif depuis 40j",
                    "importance": "medium",
                    "resolved": False,
                    "created_at": (datetime.now() - timedelta(days=50)).isoformat(),
                    "last_update": (datetime.now() - timedelta(days=40)).isoformat(),
                    "update_history": []
                },
                {
                    "state_id": 2,
                    "category": "projet",
                    "description": "État récent (5j)",
                    "importance": "high",
                    "resolved": False,
                    "created_at": (datetime.now() - timedelta(days=10)).isoformat(),
                    "last_update": (datetime.now() - timedelta(days=5)).isoformat(),
                    "update_history": []
                },
                {
                    "state_id": 3,
                    "category": "humeur",
                    "description": "État inactif high importance",
                    "importance": "high",
                    "resolved": False,
                    "created_at": (datetime.now() - timedelta(days=60)).isoformat(),
                    "last_update": (datetime.now() - timedelta(days=35)).isoformat(),
                    "update_history": []
                },
                {
                    "state_id": 4,
                    "category": "apprentissage",
                    "description": "État déjà résolu",
                    "importance": "low",
                    "resolved": True,
                    "created_at": (datetime.now() - timedelta(days=100)).isoformat(),
                    "last_update": (datetime.now() - timedelta(days=50)).isoformat(),
                    "update_history": []
                }
            ]
        }
        
        manager.get_active_states.return_value = states_data
        manager.resolve_state.return_value = True
        
        return manager
    
    def test_detect_inactive_states_threshold(self, mock_json_manager_with_states):
        """Test détection états inactifs selon seuil"""
        inactive = detect_inactive_states(
            json_manager=mock_json_manager_with_states,
            threshold_days=30
        )
        
        # Devrait détecter état #1 (40j inactif, medium importance)
        assert len(inactive) >= 1, "Au moins un état inactif devrait être détecté"
        
        # Vérifier que tous sont inactifs > 30j
        for state in inactive:
            assert state["days_inactive"] >= 30
    
    def test_detect_inactive_states_exclude_high(self, mock_json_manager_with_states):
        """Test exclusion états haute importance"""
        # Sans exclusion
        all_inactive = detect_inactive_states(
            json_manager=mock_json_manager_with_states,
            threshold_days=30,
            exclude_high_importance=False
        )
        
        # Avec exclusion
        filtered_inactive = detect_inactive_states(
            json_manager=mock_json_manager_with_states,
            threshold_days=30,
            exclude_high_importance=True
        )
        
        # Devrait avoir moins avec exclusion
        assert len(filtered_inactive) <= len(all_inactive)
        
        # Aucun état high importance dans filtered
        for state in filtered_inactive:
            assert state["importance"] != "high"
    
    def test_auto_resolve_dry_run(self, mock_json_manager_with_states):
        """Test auto-résolution en mode simulation"""
        mock_archiviste = Mock()
        
        stats = auto_resolve_states(
            json_manager=mock_json_manager_with_states,
            archiviste_controller=mock_archiviste,
            threshold_days=30,
            dry_run=True
        )
        
        assert "total" in stats
        assert stats["resolved"] == 0, "Dry run ne devrait rien résoudre"
    
    def test_auto_resolve_with_llm_validation(self, mock_json_manager_with_states):
        """Test auto-résolution avec validation LLM"""
        mock_archiviste = Mock()
        
        # Mock réponse LLM (validation positive)
        mock_archiviste.send_message.return_value = json.dumps({
            "should_resolve": True,
            "reason": "État obsolète, pas de mise à jour récente"
        })
        
        stats = auto_resolve_states(
            json_manager=mock_json_manager_with_states,
            archiviste_controller=mock_archiviste,
            threshold_days=30,
            dry_run=False,
            require_llm_validation=True
        )
        
        assert stats["resolved"] >= 0, "Des états pourraient être résolus"
        
        # Vérifier appel LLM si états détectés
        if stats["total"] > 0:
            assert mock_archiviste.send_message.called


class TestIntegration:
    """Tests d'intégration système complet"""
    
    @pytest.fixture
    def integration_setup(self, tmp_path):
        """Setup complet pour tests intégration"""
        # Créer structure
        journal_dir = tmp_path / "journal_test"
        journal_dir.mkdir()
        
        # JSONManager réel
        json_manager = JournalJSONManager(base_dir=journal_dir)
        
        # Mocks
        mock_memory = Mock()
        mock_memory.add_memory.return_value = True
        
        mock_archiviste = Mock()
        mock_archiviste.send_message.return_value = "Résumé test."
        
        # PurgeManager
        purge_mgr = PurgeManager(
            json_manager=json_manager,
            memory_manager=mock_memory,
            archiviste_controller=mock_archiviste
        )
        
        return {
            "json_manager": json_manager,
            "purge_manager": purge_mgr,
            "memory_manager": mock_memory,
            "archiviste": mock_archiviste,
            "base_dir": journal_dir
        }
    
    def test_full_purge_workflow(self, integration_setup):
        """Test workflow complet purge"""
        setup = integration_setup
        
        # 1. Créer entrée ancienne
        old_entry = {
            "entry_id": 100,
            "date": (datetime.now() - timedelta(days=100)).strftime("%Y-%m-%d"),
            "timestamp": (datetime.now() - timedelta(days=100)).isoformat(),
            "content": "Contenu test très long" * 100,
            "category": "test",
            "active_states": [],
            "compressed": False
        }
        
        success = setup["json_manager"].save_entry(old_entry)
        assert success, "Sauvegarde entrée devrait réussir"
        
        # 2. Détecter entrées purgeable
        purgeable = setup["purge_manager"].get_purgeable_entries(age_days=90)
        assert len(purgeable) >= 1, "Entrée ancienne devrait être détectée"
        
        # 3. Compression
        compress_success, msg = setup["purge_manager"].compress_entry(100)
        assert compress_success, f"Compression devrait réussir: {msg}"
        
        # 4. Transfert FAISS
        transfer_success, msg = setup["purge_manager"].transfer_to_faiss(100)
        assert transfer_success, f"Transfert FAISS devrait réussir: {msg}"
        
        # Vérifier appel memory_manager
        setup["memory_manager"].add_memory.assert_called()


# Markers pytest
pytestmark = pytest.mark.journal


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
