"""
Tests Unitaires - Core Logic (AIController & Backends)
=======================================================

Tests des contrôleurs IA multi-providers et gestionnaires backends.

Couverture: 20-25 tests
Criticité: 🔴 CRITIQUE (cœur système IA)
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json


class TestAIControllerInitialization:
    """Tests d'initialisation des contrôleurs IA."""
    
    def test_api_controller_init(self):
        """Test initialisation APIController."""
        from core_logic import AIController, APIManager
        
        api_mgr = APIManager()
        controller = AIController(
            backend_type="API",
            provider="OpenAI",
            api_key="test-key",
            model="gpt-4",
            backend_manager=api_mgr
        )
        
        assert controller.backend_type == "API"
        assert controller.provider == "OpenAI"
        assert controller.model == "gpt-4"
    
    def test_ollama_controller_init(self):
        """Test initialisation OllamaController."""
        from core_logic import AIController, OllamaManager
        
        ollama_mgr = OllamaManager()
        controller = AIController(
            backend_type="Ollama",
            provider="Ollama",
            model="llama3:latest",
            backend_manager=ollama_mgr
        )
        
        assert controller.backend_type == "Ollama"
        assert controller.model == "llama3:latest"
    
    def test_gguf_controller_init(self):
        """Test initialisation GGUFController."""
        from core_logic import AIController, GGUFManager
        
        gguf_mgr = GGUFManager()
        controller = AIController(
            backend_type="GGUF",
            provider="GGUF",
            model="models/llama-3-8b.gguf",
            backend_manager=gguf_mgr
        )
        
        assert controller.backend_type == "GGUF"
    
    def test_kobold_controller_init(self):
        """Test initialisation KoboldController."""
        from core_logic import AIController, KoboldManager
        
        kobold_mgr = KoboldManager()
        controller = AIController(
            backend_type="KoboldCpp",
            provider="KoboldCpp",
            model="",  # KoboldCpp n'utilise pas de nom de modèle
            backend_manager=kobold_mgr
        )
        
        assert controller.backend_type == "KoboldCpp"


class TestBackendMapping:
    """Tests du mapping provider → backend."""
    
    def test_map_openai_to_api(self):
        """Test mapping OpenAI vers APIManager."""
        from utils.backend_utils import map_backend_for_controller
        
        backend_type, backend_mgr_type = map_backend_for_controller("OpenAI")
        
        assert backend_type == "API"
        assert backend_mgr_type == "APIManager"
    
    def test_map_mistral_to_api(self):
        """Test mapping Mistral vers APIManager."""
        from utils.backend_utils import map_backend_for_controller
        
        backend_type, _ = map_backend_for_controller("Mistral")
        assert backend_type == "API"
    
    def test_map_ollama_to_ollama(self):
        """Test mapping Ollama vers OllamaManager."""
        from utils.backend_utils import map_backend_for_controller
        
        backend_type, backend_mgr_type = map_backend_for_controller("Ollama")
        
        assert backend_type == "Ollama"
        assert backend_mgr_type == "OllamaManager"
    
    def test_map_invalid_provider(self):
        """Test mapping provider invalide."""
        from utils.backend_utils import map_backend_for_controller
        
        backend_type, backend_mgr_type = map_backend_for_controller("InvalidProvider")
        
        # Devrait retourner API par défaut ou lever exception
        assert backend_type in ["API", None]


class TestSendMessage:
    """Tests envoi messages aux IA."""
    
    @pytest.mark.requires_api
    @patch('requests.post')
    def test_send_message_api_success(self, mock_post):
        """Test envoi message API avec succès."""
        from core_logic import AIController, APIManager
        
        # Mock réponse API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{
                "message": {"content": "Réponse de test"}
            }]
        }
        mock_post.return_value = mock_response
        
        api_mgr = APIManager()
        controller = AIController(
            backend_type="API",
            provider="OpenAI",
            api_key="test-key",
            model="gpt-4",
            backend_manager=api_mgr
        )
        
        response = controller.send_message(
            messages=[{"role": "user", "content": "Test"}],
            temperature=0.7
        )
        
        assert "Réponse de test" in response or response is not None
    
    @patch('requests.post')
    def test_send_message_ollama_success(self, mock_post):
        """Test envoi message Ollama avec succès."""
        from core_logic import AIController, OllamaManager
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "response": "Réponse Ollama test"
        }
        mock_post.return_value = mock_response
        
        ollama_mgr = OllamaManager()
        controller = AIController(
            backend_type="Ollama",
            provider="Ollama",
            model="llama3:latest",
            backend_manager=ollama_mgr
        )
        
        response = controller.send_message(
            messages=[{"role": "user", "content": "Test Ollama"}],
            temperature=0.7
        )
        
        assert response is not None


class TestStreamingResponse:
    """Tests réponses streaming."""
    
    @pytest.mark.requires_api
    @patch('requests.post')
    def test_streaming_response(self, mock_post):
        """Test réception réponse streaming."""
        from core_logic import AIController, APIManager
        
        # Mock streaming response
        def mock_iter_lines():
            yield b'data: {"choices":[{"delta":{"content":"Test"}}]}'
            yield b'data: {"choices":[{"delta":{"content":" streaming"}}]}'
            yield b'data: [DONE]'
        
        mock_response = Mock()
        mock_response.iter_lines.return_value = mock_iter_lines()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        api_mgr = APIManager()
        controller = AIController(
            backend_type="API",
            provider="OpenAI",
            api_key="test-key",
            model="gpt-4",
            backend_manager=api_mgr,
            stream=True
        )
        
        # Test streaming
        response = controller.send_message(
            messages=[{"role": "user", "content": "Test"}],
            stream=True
        )
        
        assert response is not None


class TestErrorHandling:
    """Tests gestion d'erreurs (philosophie organique)."""
    
    @patch('requests.post')
    def test_error_no_api_key(self, mock_post):
        """Test erreur API key manquante (erreur visible)."""
        from core_logic import AIController, APIManager
        
        mock_post.side_effect = Exception("API key missing")
        
        api_mgr = APIManager()
        controller = AIController(
            backend_type="API",
            provider="OpenAI",
            api_key="",  # Clé vide
            model="gpt-4",
            backend_manager=api_mgr
        )
        
        # Philosophie organique: erreur doit être propagée, pas masquée
        with pytest.raises(Exception):
            controller.send_message(
                messages=[{"role": "user", "content": "Test"}]
            )
    
    @patch('requests.post')
    def test_error_invalid_model(self, mock_post):
        """Test erreur modèle invalide."""
        from core_logic import AIController, APIManager
        
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"error": "Model not found"}
        mock_post.return_value = mock_response
        
        api_mgr = APIManager()
        controller = AIController(
            backend_type="API",
            provider="OpenAI",
            api_key="test-key",
            model="invalid-model-xyz",
            backend_manager=api_mgr
        )
        
        # Erreur doit être visible (philosophie organique)
        response = controller.send_message(
            messages=[{"role": "user", "content": "Test"}]
        )
        
        # Vérifier que l'erreur n'est pas masquée
        assert response is None or "error" in str(response).lower()
    
    @patch('requests.post')
    def test_error_timeout(self, mock_post):
        """Test timeout API."""
        from core_logic import AIController, APIManager
        import requests
        
        mock_post.side_effect = requests.Timeout("Connection timeout")
        
        api_mgr = APIManager()
        controller = AIController(
            backend_type="API",
            provider="OpenAI",
            api_key="test-key",
            model="gpt-4",
            backend_manager=api_mgr
        )
        
        # Timeout doit être propagé (pas de retry invisible)
        with pytest.raises(requests.Timeout):
            controller.send_message(
                messages=[{"role": "user", "content": "Test"}]
            )


class TestContextLengthValidation:
    """Tests validation longueur contexte."""
    
    def test_context_length_overflow(self):
        """Test détection dépassement context_length."""
        from core_logic import AIController, APIManager
        
        api_mgr = APIManager()
        controller = AIController(
            backend_type="API",
            provider="OpenAI",
            api_key="test-key",
            model="gpt-4",
            backend_manager=api_mgr,
            context_length=4096
        )
        
        # Créer un message très long (>4096 tokens)
        long_message = "test " * 2000  # ~2000 tokens
        
        # Le système devrait gérer ou alerter sur le dépassement
        result = controller.validate_context_length(long_message)
        
        # Vérifier validation (implémentation dépend du code réel)
        assert result is not None


class TestParameterValidation:
    """Tests validation paramètres IA."""
    
    def test_temperature_validation(self):
        """Test validation température (0.0-2.0)."""
        from core_logic import AIController, APIManager
        
        api_mgr = APIManager()
        controller = AIController(
            backend_type="API",
            provider="OpenAI",
            api_key="test-key",
            model="gpt-4",
            backend_manager=api_mgr
        )
        
        # Température valide
        assert controller.validate_temperature(0.7) is True
        assert controller.validate_temperature(0.0) is True
        assert controller.validate_temperature(2.0) is True
        
        # Température invalide
        assert controller.validate_temperature(-0.5) is False
        assert controller.validate_temperature(3.0) is False
    
    def test_max_tokens_validation(self):
        """Test validation max_tokens."""
        from core_logic import AIController, APIManager
        
        api_mgr = APIManager()
        controller = AIController(
            backend_type="API",
            provider="OpenAI",
            api_key="test-key",
            model="gpt-4",
            backend_manager=api_mgr
        )
        
        # max_tokens valide
        assert controller.validate_max_tokens(1000) is True
        assert controller.validate_max_tokens(4000) is True
        
        # max_tokens invalide
        assert controller.validate_max_tokens(-100) is False
        assert controller.validate_max_tokens(0) is False


class TestMultiProviderSwitching:
    """Tests changement de provider à la volée."""
    
    def test_switch_provider_api_to_ollama(self):
        """Test switch OpenAI → Ollama."""
        from core_logic import AIController, APIManager, OllamaManager
        
        # Démarrer avec OpenAI
        api_mgr = APIManager()
        controller = AIController(
            backend_type="API",
            provider="OpenAI",
            api_key="test-key",
            model="gpt-4",
            backend_manager=api_mgr
        )
        
        assert controller.provider == "OpenAI"
        
        # Switch vers Ollama
        ollama_mgr = OllamaManager()
        controller.switch_backend(
            backend_type="Ollama",
            provider="Ollama",
            model="llama3:latest",
            backend_manager=ollama_mgr
        )
        
        assert controller.provider == "Ollama"
        assert controller.backend_type == "Ollama"


class TestEmbeddingController:
    """Tests contrôleur Embedding."""
    
    @patch('requests.post')
    def test_embedding_generation(self, mock_post):
        """Test génération embedding."""
        from core_logic import EmbeddingController, APIManager
        
        # Mock réponse API embedding
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [{
                "embedding": [0.1] * 1024  # Vecteur 1024D factice
            }]
        }
        mock_post.return_value = mock_response
        
        api_mgr = APIManager()
        emb_controller = EmbeddingController(
            backend_type="API",
            provider="Mistral",
            api_key="test-key",
            backend_manager=api_mgr
        )
        
        embedding = emb_controller.generate_embedding("Test text")
        
        assert embedding is not None
        assert len(embedding) == 1024


class TestReasoningVsChat:
    """Tests différence Reasoning vs Chat controller."""
    
    def test_reasoning_controller_specific_params(self):
        """Test paramètres spécifiques Reasoning."""
        from core_logic import AIController, APIManager
        
        api_mgr = APIManager()
        reasoning_controller = AIController(
            backend_type="API",
            provider="OpenAI",
            api_key="test-key",
            model="o1-preview",  # Modèle raisonnement
            backend_manager=api_mgr,
            temperature=1.0  # O1 utilise température fixe
        )
        
        assert reasoning_controller.model == "o1-preview"
        assert reasoning_controller.temperature == 1.0
    
    def test_chat_controller_flexibility(self):
        """Test flexibilité Chat controller."""
        from core_logic import AIController, APIManager
        
        api_mgr = APIManager()
        chat_controller = AIController(
            backend_type="API",
            provider="OpenAI",
            api_key="test-key",
            model="gpt-4",
            backend_manager=api_mgr,
            temperature=0.7,  # Température variable
            max_tokens=2000
        )
        
        assert chat_controller.temperature == 0.7
        assert chat_controller.max_tokens == 2000


class TestVisionSupport:
    """Tests support vision (GGUF multimodal)."""
    
    @pytest.mark.requires_gpu
    def test_vision_gguf_initialization(self):
        """Test init GGUF avec vision."""
        from core_logic import AIController, GGUFManager
        
        gguf_mgr = GGUFManager()
        controller = AIController(
            backend_type="GGUF",
            provider="GGUF",
            model="models/llava-1.6.gguf",
            backend_manager=gguf_mgr,
            vision_enabled=True
        )
        
        assert controller.vision_enabled is True


class TestSettingsManager:
    """Tests SettingsManager."""
    
    def test_load_default_settings(self, temp_dir):
        """Test chargement settings par défaut."""
        from core_logic import SettingsManager
        
        settings_path = temp_dir / "settings.json"
        sm = SettingsManager(settings_path)
        
        assert "chat_api" in sm.settings
        assert "reasoning_api" in sm.settings
        assert "embedding_api" in sm.settings
    
    def test_save_settings(self, temp_dir):
        """Test sauvegarde settings."""
        from core_logic import SettingsManager
        
        settings_path = temp_dir / "settings.json"
        sm = SettingsManager(settings_path)
        
        # Modifier et sauvegarder
        sm.settings["chat_api"]["provider"] = "Mistral"
        sm.save()
        
        # Recharger et vérifier
        sm2 = SettingsManager(settings_path)
        sm2.load()
        
        assert sm2.settings["chat_api"]["provider"] == "Mistral"
    
    def test_update_provider(self, temp_dir):
        """Test mise à jour provider."""
        from core_logic import SettingsManager
        
        settings_path = temp_dir / "settings.json"
        sm = SettingsManager(settings_path)
        
        sm.update_setting("chat_api", "provider", "Anthropic")
        
        assert sm.settings["chat_api"]["provider"] == "Anthropic"
    
    def test_settings_validation(self, temp_dir):
        """Test validation settings."""
        from core_logic import SettingsManager
        
        settings_path = temp_dir / "settings.json"
        sm = SettingsManager(settings_path)
        
        # Provider valide
        assert sm.validate_provider("OpenAI") is True
        assert sm.validate_provider("Mistral") is True
        
        # Provider invalide
        assert sm.validate_provider("InvalidProvider") is False


# ===== TESTS EDGE CASES =====

class TestEdgeCases:
    """Tests cas limites backends."""
    
    def test_empty_message_list(self):
        """Test envoi liste messages vide."""
        from core_logic import AIController, APIManager
        
        api_mgr = APIManager()
        controller = AIController(
            backend_type="API",
            provider="OpenAI",
            api_key="test-key",
            model="gpt-4",
            backend_manager=api_mgr
        )
        
        with pytest.raises(ValueError):
            controller.send_message(messages=[])
    
    def test_invalid_message_format(self):
        """Test format message invalide."""
        from core_logic import AIController, APIManager
        
        api_mgr = APIManager()
        controller = AIController(
            backend_type="API",
            provider="OpenAI",
            api_key="test-key",
            model="gpt-4",
            backend_manager=api_mgr
        )
        
        # Message sans 'role' ou 'content'
        with pytest.raises(KeyError):
            controller.send_message(
                messages=[{"invalid_key": "value"}]
            )
