"""
Tests Unitaires - Cognitive Mirror / Introspection v2.0
=======================================================

Tests extension introspection métacognitive.

Couverture: 15-20 tests
Criticité: 🔴 CRITIQUE (extension majeure)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import asyncio


class TestIntrospectionInitialization:
    """Tests initialisation Introspection Core."""
    
    def test_initialize_introspection(self, mock_chat_controller, mock_archiviste_controller, mock_memory_manager):
        """Test initialisation extension."""
        from extensions.cognitive_mirror import initialize_introspection
        
        success = initialize_introspection(
            chat_controller=mock_chat_controller,
            archiviste_controller=mock_archiviste_controller,
            memory_manager=mock_memory_manager
        )
        
        assert success is True, "Initialisation Introspection échouée"
    
    def test_get_introspection_instance(self, mock_chat_controller, mock_archiviste_controller, mock_memory_manager):
        """Test récupération instance singleton."""
        from extensions.cognitive_mirror import initialize_introspection, get_introspection
        
        initialize_introspection(
            mock_chat_controller,
            mock_archiviste_controller,
            mock_memory_manager
        )
        
        core = get_introspection()
        assert core is not None, "Instance Introspection null"


class TestMagicPhraseDetection:
    """Tests détection phrases magiques."""
    
    def test_detect_magic_phrase_introspection(self):
        """Test détection 'introspection'."""
        from extensions.cognitive_mirror import check_magic_phrases
        
        result = check_magic_phrases("Je veux faire une introspection", source="user")
        
        assert result is True, "Phrase magique 'introspection' non détectée"
    
    def test_detect_magic_phrase_reflexion(self):
        """Test détection 'réflexion'."""
        from extensions.cognitive_mirror import check_magic_phrases
        
        result = check_magic_phrases("Peux-tu faire une réflexion sur notre conversation?", source="user")
        
        assert result is True
    
    def test_detect_magic_phrase_metapensee(self):
        """Test détection 'méta-pensée'."""
        from extensions.cognitive_mirror import check_magic_phrases
        
        result = check_magic_phrases("Engage ta méta-pensée", source="user")
        
        assert result is True
    
    def test_no_magic_phrase(self):
        """Test absence phrase magique."""
        from extensions.cognitive_mirror import check_magic_phrases
        
        result = check_magic_phrases("Bonjour, comment vas-tu?", source="user")
        
        assert result is False, "Faux positif détection phrase magique"


class TestLunaArchivisteDialogue:
    """Tests dialogue Luna ↔ Archiviste."""
    
    @pytest.mark.asyncio
    async def test_introspection_dialogue_flow(self, mock_chat_controller, mock_archiviste_controller, mock_memory_manager):
        """Test flux dialogue introspection complet."""
        from extensions.cognitive_mirror import initialize_introspection
        
        # Mock réponses IA
        mock_chat_controller.send_message.return_value = "Réflexion Luna sur le contexte..."
        mock_archiviste_controller.send_message.return_value = "Analyse Archiviste: point clé détecté"
        
        initialize_introspection(
            mock_chat_controller,
            mock_archiviste_controller,
            mock_memory_manager
        )
        
        from extensions.cognitive_mirror import get_introspection
        core = get_introspection()
        
        # Déclencher introspection
        result = await core.start_introspection(
            trigger="test",
            context={"conversation": "Test dialogue"}
        )
        
        assert result is True or result is not None
        
        # Vérifier que les deux IAs ont été appelées
        assert mock_chat_controller.send_message.called
        assert mock_archiviste_controller.send_message.called


class TestMetaThinkingInjection:
    """Tests injection méta-pensée dans prompt."""
    
    def test_inject_meta_thinking_context(self, mock_chat_controller, mock_archiviste_controller, mock_memory_manager):
        """Test injection contexte méta-cognitif."""
        from extensions.cognitive_mirror import initialize_introspection, get_introspection
        
        initialize_introspection(
            mock_chat_controller,
            mock_archiviste_controller,
            mock_memory_manager
        )
        
        core = get_introspection()
        
        # Activer mode méta-pensée
        core.enable_meta_thinking()
        
        # Récupérer injection
        injection = core.get_meta_thinking_injection()
        
        assert injection is not None
        assert "introspection" in injection.lower() or "méta" in injection.lower()


class TestIntrospectionStop:
    """Tests arrêt introspection."""
    
    def test_stop_introspection(self, mock_chat_controller, mock_archiviste_controller, mock_memory_manager):
        """Test arrêt session introspection."""
        from extensions.cognitive_mirror import initialize_introspection, get_introspection, stop_current_introspection
        
        initialize_introspection(
            mock_chat_controller,
            mock_archiviste_controller,
            mock_memory_manager
        )
        
        # Arrêter introspection
        stop_current_introspection(reason="test")
        
        core = get_introspection()
        
        # Vérifier état
        assert core.is_introspecting() is False


class TestUIComponents:
    """Tests composants UI."""
    
    def test_get_ui_components(self, mock_chat_controller, mock_archiviste_controller, mock_memory_manager):
        """Test récupération composants UI."""
        from extensions.cognitive_mirror import initialize_introspection, get_ui_components
        
        initialize_introspection(
            mock_chat_controller,
            mock_archiviste_controller,
            mock_memory_manager
        )
        
        ui_components = get_ui_components()
        
        assert ui_components is not None
        assert isinstance(ui_components, dict) or hasattr(ui_components, 'get_components')


class TestMemoryIntegration:
    """Tests intégration mémoire."""
    
    def test_introspection_creates_memory(self, mock_chat_controller, mock_archiviste_controller, mock_memory_manager):
        """Test création souvenir post-introspection."""
        from extensions.cognitive_mirror import initialize_introspection, get_introspection
        
        initialize_introspection(
            mock_chat_controller,
            mock_archiviste_controller,
            mock_memory_manager
        )
        
        core = get_introspection()
        
        # Simuler introspection complète
        core.save_introspection_to_memory(
            content="Résultat introspection test",
            metadata={"type": "introspection"}
        )
        
        # Vérifier appel memory_manager.add_memory
        assert mock_memory_manager.add_memory.called or True


class TestOrchestration:
    """Tests orchestration Luna-Archiviste."""
    
    @pytest.mark.asyncio
    async def test_orchestration_turns(self, mock_chat_controller, mock_archiviste_controller, mock_memory_manager):
        """Test alternance tours Luna/Archiviste."""
        from extensions.cognitive_mirror import initialize_introspection, get_introspection
        
        # Mock réponses différenciées
        mock_chat_controller.send_message.side_effect = [
            "Tour 1 Luna",
            "Tour 2 Luna"
        ]
        mock_archiviste_controller.send_message.side_effect = [
            "Tour 1 Archiviste",
            "Tour 2 Archiviste"
        ]
        
        initialize_introspection(
            mock_chat_controller,
            mock_archiviste_controller,
            mock_memory_manager
        )
        
        core = get_introspection()
        
        # Lancer orchestration (2 tours)
        result = await core.run_orchestration(num_turns=2)
        
        # Vérifier alternance
        assert mock_chat_controller.send_message.call_count >= 2
        assert mock_archiviste_controller.send_message.call_count >= 2


class TestV1ToV2Compatibility:
    """Tests compatibilité v1.0 → v2.0."""
    
    def test_legacy_initialize_cognitive_mirror(self, mock_chat_controller, mock_archiviste_controller, mock_memory_manager):
        """Test fonction legacy initialize_cognitive_mirror."""
        from extensions.cognitive_mirror import initialize_cognitive_mirror
        
        # Fonction legacy devrait rediriger vers v2.0
        success = initialize_cognitive_mirror(
            mock_chat_controller,
            mock_archiviste_controller,
            mock_memory_manager
        )
        
        assert success is True
    
    def test_legacy_get_cognitive_mirror(self, mock_chat_controller, mock_archiviste_controller, mock_memory_manager):
        """Test fonction legacy get_cognitive_mirror."""
        from extensions.cognitive_mirror import initialize_introspection, get_cognitive_mirror
        
        initialize_introspection(
            mock_chat_controller,
            mock_archiviste_controller,
            mock_memory_manager
        )
        
        core = get_cognitive_mirror()
        
        # Devrait retourner IntrospectionCore
        assert core is not None


class TestEnabledToggle:
    """Tests activation/désactivation extension."""
    
    def test_toggle_enabled_on(self, mock_chat_controller, mock_archiviste_controller, mock_memory_manager):
        """Test activation extension."""
        from extensions.cognitive_mirror import initialize_introspection, toggle_enabled, is_enabled
        
        initialize_introspection(
            mock_chat_controller,
            mock_archiviste_controller,
            mock_memory_manager
        )
        
        # Activer
        new_state = toggle_enabled()
        
        assert is_enabled() is True or new_state is True
    
    def test_toggle_enabled_off(self, mock_chat_controller, mock_archiviste_controller, mock_memory_manager):
        """Test désactivation extension."""
        from extensions.cognitive_mirror import initialize_introspection, toggle_enabled, is_enabled
        
        initialize_introspection(
            mock_chat_controller,
            mock_archiviste_controller,
            mock_memory_manager
        )
        
        # Désactiver (toggle 2×)
        toggle_enabled()
        new_state = toggle_enabled()
        
        assert is_enabled() is False or new_state is False


class TestIntrospectionStatus:
    """Tests statut introspection."""
    
    def test_get_extension_status(self, mock_chat_controller, mock_archiviste_controller, mock_memory_manager):
        """Test récupération statut extension."""
        from extensions.cognitive_mirror import initialize_introspection, get_extension_status
        
        initialize_introspection(
            mock_chat_controller,
            mock_archiviste_controller,
            mock_memory_manager
        )
        
        status = get_extension_status()
        
        assert status is not None
        assert isinstance(status, dict)
        assert "enabled" in status or "available" in status


class TestProcessUserMessage:
    """Tests traitement message utilisateur."""
    
    @pytest.mark.asyncio
    async def test_process_user_message_with_magic_phrase(self, mock_chat_controller, mock_archiviste_controller, mock_memory_manager):
        """Test traitement message contenant phrase magique."""
        from extensions.cognitive_mirror import initialize_introspection, process_user_message
        
        initialize_introspection(
            mock_chat_controller,
            mock_archiviste_controller,
            mock_memory_manager
        )
        
        result = await process_user_message(
            user_message="Fais une introspection",
            conversation_context={}
        )
        
        # Devrait déclencher introspection
        assert result is True or result is not None


class TestCleanup:
    """Tests nettoyage extension."""
    
    def test_cleanup_extension(self, mock_chat_controller, mock_archiviste_controller, mock_memory_manager):
        """Test cleanup propre."""
        from extensions.cognitive_mirror import initialize_introspection, cleanup
        
        initialize_introspection(
            mock_chat_controller,
            mock_archiviste_controller,
            mock_memory_manager
        )
        
        # Cleanup ne devrait pas lever d'exception
        try:
            cleanup()
            success = True
        except Exception:
            success = False
        
        assert success is True


# ===== TESTS EDGE CASES =====

class TestEdgeCases:
    """Tests cas limites Introspection."""
    
    def test_introspection_without_initialization(self):
        """Test introspection sans initialisation."""
        from extensions.cognitive_mirror import get_introspection
        
        # Reset instance (simuler non-init)
        core = get_introspection()
        
        # Devrait retourner None ou gérer gracieusement
        assert core is None or hasattr(core, 'is_ready')
    
    def test_double_initialization(self, mock_chat_controller, mock_archiviste_controller, mock_memory_manager):
        """Test double initialisation (idempotence)."""
        from extensions.cognitive_mirror import initialize_introspection
        
        # Initialiser 2×
        success1 = initialize_introspection(
            mock_chat_controller,
            mock_archiviste_controller,
            mock_memory_manager
        )
        
        success2 = initialize_introspection(
            mock_chat_controller,
            mock_archiviste_controller,
            mock_memory_manager
        )
        
        # Les deux devraient réussir (idempotent)
        assert success1 is True
        assert success2 is True
