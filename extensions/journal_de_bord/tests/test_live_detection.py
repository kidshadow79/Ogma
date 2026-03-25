"""
OGMA - Journal de Bord v2.0
Tests du système de détection d'états EN LIVE

Valide que la détection fonctionne pendant les conversations
"""

import pytest
import asyncio
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, AsyncMock, MagicMock


@pytest.fixture
def temp_journal_dir(tmp_path):
    """Crée un dossier temporaire pour le journal"""
    journal_dir = tmp_path / "journal_test"
    journal_dir.mkdir()
    return journal_dir


@pytest.fixture
def mock_config():
    """Mock configuration Journal"""
    config = Mock()
    config.get = Mock(side_effect=lambda key, default=None: {
        "cache_size": 100,
        "cache_expiry_hours": 24,
        "enable_active_states": True
    }.get(key, default))
    config.get_active_states_settings = Mock(return_value={
        "enabled": True,
        "auto_archive_days": 40,
        "badge_color": "orange"
    })
    return config


@pytest.fixture
def mock_json_manager(temp_journal_dir, mock_config):
    """Mock JSONManager avec méthodes états actifs"""
    from extensions.journal_de_bord.json_manager import JSONManager
    
    manager = JSONManager(mock_config, data_dir=temp_journal_dir)
    
    # Override pour tests
    manager._active_states = {
        "metadata": {
            "version": "2.0.0",
            "last_update": datetime.now().isoformat(),
            "total_states": 0,
            "last_state_id": 0
        },
        "states": []
    }
    
    return manager


@pytest.fixture
def mock_archiviste():
    """Mock Archiviste controller"""
    archiviste = AsyncMock()
    
    # Simule réponses LLM selon contexte
    async def mock_generate(messages, **kwargs):
        content = messages[0]["content"].lower()
        
        # Détection nouveau projet
        if "nouveau projet" in content and "journal v3" in content:
            return '''{
                "new_states": [{
                    "category": "projet",
                    "description": "Développement Journal v3.0",
                    "importance": "high",
                    "reasoning": "Projet clairement commencé avec objectifs définis"
                }],
                "resolved_state_ids": [],
                "updated_states": []
            }'''
        
        # Détection maladie
        if "malade" in content or "grippe" in content:
            return '''{
                "new_states": [{
                    "category": "santé",
                    "description": "Grippe - symptômes depuis 2 jours",
                    "importance": "high",
                    "reasoning": "État santé en cours nécessitant suivi"
                }],
                "resolved_state_ids": [],
                "updated_states": []
            }'''
        
        # Détection résolution
        if "guéri" in content or "terminé" in content or "fini" in content:
            return '''{
                "new_states": [],
                "resolved_state_ids": [1],
                "resolution_note": "Résolu par l'utilisateur",
                "updated_states": []
            }'''
        
        # Pas de changement
        return '''{
            "new_states": [],
            "resolved_state_ids": [],
            "updated_states": []
        }'''
    
    archiviste.generate_completion = AsyncMock(side_effect=mock_generate)
    return archiviste


@pytest.mark.asyncio
class TestLiveStateDetector:
    """Tests du détecteur d'états en temps réel"""
    
    async def test_detection_nouveau_projet(self, mock_json_manager, mock_archiviste):
        """Test détection d'un nouveau projet en cours"""
        from extensions.journal_de_bord.live_state_detector import LiveStateDetector
        
        detector = LiveStateDetector(mock_json_manager, mock_archiviste)
        
        # Simulation message
        user_msg = "Je commence un nouveau projet : développer Journal v3.0 avec IA améliorée"
        ai_msg = "Super ! Comment puis-je t'aider avec ce projet ?"
        
        result = await detector.analyze_message_pair(user_msg, ai_msg)
        
        # Vérifications
        assert len(result["new_states"]) == 1
        new_state_id = result["new_states"][0]
        assert new_state_id is not None
        
        # Vérifier état créé
        states = mock_json_manager.get_active_states()
        assert states["metadata"]["total_states"] == 1
        
        created_state = states["states"][0]
        assert created_state["category"] == "projet"
        assert "Journal v3.0" in created_state["description"]
        assert created_state["importance"] == "high"
    
    async def test_detection_probleme_sante(self, mock_json_manager, mock_archiviste):
        """Test détection problème de santé"""
        from extensions.journal_de_bord.live_state_detector import LiveStateDetector
        
        detector = LiveStateDetector(mock_json_manager, mock_archiviste)
        
        user_msg = "Je suis malade depuis 2 jours, grosse grippe avec fièvre"
        ai_msg = "Je comprends, prends soin de toi. Repos et hydratation."
        
        result = await detector.analyze_message_pair(user_msg, ai_msg)
        
        assert len(result["new_states"]) == 1
        
        states = mock_json_manager.get_active_states()
        created_state = states["states"][0]
        assert created_state["category"] == "santé"
        assert created_state["importance"] == "high"
    
    async def test_detection_resolution(self, mock_json_manager, mock_archiviste):
        """Test détection résolution d'un état existant"""
        from extensions.journal_de_bord.live_state_detector import LiveStateDetector
        
        # Créer état existant
        state_id = mock_json_manager.create_active_state(
            category="santé",
            description="Grippe en cours",
            importance="high"
        )
        
        detector = LiveStateDetector(mock_json_manager, mock_archiviste)
        
        user_msg = "Bonne nouvelle, je suis guéri ! Plus de symptômes."
        ai_msg = "Excellent ! Content que tu ailles mieux."
        
        result = await detector.analyze_message_pair(user_msg, ai_msg)
        
        assert len(result["resolved_states"]) == 1
        assert result["resolved_states"][0] == state_id
        
        # Vérifier résolution
        states = mock_json_manager.get_active_states()
        resolved_state = next(s for s in states["states"] if s["state_id"] == state_id)
        assert resolved_state["resolved"] == True
    
    async def test_pas_de_faux_positifs(self, mock_json_manager, mock_archiviste):
        """Test que les conversations normales ne créent pas d'états"""
        from extensions.journal_de_bord.live_state_detector import LiveStateDetector
        
        detector = LiveStateDetector(mock_json_manager, mock_archiviste)
        
        user_msg = "Quelle est la capitale de la France ?"
        ai_msg = "La capitale de la France est Paris."
        
        result = await detector.analyze_message_pair(user_msg, ai_msg)
        
        assert len(result["new_states"]) == 0
        assert len(result["resolved_states"]) == 0
        assert len(result["updated_states"]) == 0
    
    async def test_pattern_pré_filtrage(self, mock_json_manager, mock_archiviste):
        """Test que le pré-filtrage regex fonctionne"""
        from extensions.journal_de_bord.live_state_detector import LiveStateDetector
        
        detector = LiveStateDetector(mock_json_manager, mock_archiviste)
        
        # Test détection patterns santé
        quick_scan = detector._quick_pattern_scan("Je suis malade avec fièvre")
        assert quick_scan["has_potential"] == True
        assert "santé" in quick_scan["categories"]
        
        # Test détection patterns projet
        quick_scan = detector._quick_pattern_scan("Je démarre un nouveau projet")
        assert quick_scan["has_potential"] == True
        assert "projet" in quick_scan["categories"]
        
        # Test pas de détection
        quick_scan = detector._quick_pattern_scan("Bonjour comment ça va")
        assert quick_scan["has_potential"] == False


@pytest.mark.asyncio
class TestIntegrationLiveDetection:
    """Tests d'intégration complète"""
    
    async def test_workflow_complet_projet(self, mock_json_manager, mock_archiviste):
        """Test workflow complet : création → progression → résolution"""
        from extensions.journal_de_bord.live_state_detector import LiveStateDetector
        
        detector = LiveStateDetector(mock_json_manager, mock_archiviste)
        
        # Étape 1 : Création projet
        result1 = await detector.analyze_message_pair(
            "Je lance un nouveau projet Journal v3.0",
            "Super ! Comment puis-je t'aider ?"
        )
        assert len(result1["new_states"]) == 1
        
        # Étape 2 : Résolution (simulée)
        mock_archiviste.generate_completion = AsyncMock(return_value='''{
            "new_states": [],
            "resolved_state_ids": [1],
            "resolution_note": "Projet terminé avec succès",
            "updated_states": []
        }''')
        
        result2 = await detector.analyze_message_pair(
            "Le projet Journal v3.0 est terminé et déployé !",
            "Félicitations pour cette réalisation !"
        )
        assert len(result2["resolved_states"]) == 1
        
        # Vérifier état final
        states = mock_json_manager.get_active_states()
        project_state = states["states"][0]
        assert project_state["resolved"] == True


def test_quick_run():
    """Test rapide exécutable directement"""
    print("🧪 Tests détection live états actifs")
    print("=" * 70)
    
    # Run avec pytest
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    test_quick_run()
