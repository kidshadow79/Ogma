"""
Configuration pytest globale et fixtures partagées
===================================================

Ce fichier contient les fixtures pytest utilisées par tous les tests.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock
import asyncio


# ===== FIXTURES DIRECTORIES =====

@pytest.fixture
def temp_dir():
    """Crée un répertoire temporaire pour les tests."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def test_data_dir():
    """Retourne le chemin vers les données de test."""
    return Path(__file__).parent / "fixtures"


# ===== FIXTURES MOCK IA CONTROLLERS =====

@pytest.fixture
def mock_chat_controller():
    """Mock du contrôleur Chat IA."""
    controller = Mock()
    controller.send_message = Mock(return_value="Réponse de test Chat IA")
    controller.send_message_async = Mock(return_value=asyncio.Future())
    controller.send_message_async.return_value.set_result("Réponse async test")
    controller.provider = "OpenAI"
    controller.model = "gpt-4"
    controller.is_available = Mock(return_value=True)
    return controller


@pytest.fixture
def mock_archiviste_controller():
    """Mock du contrôleur Archiviste IA."""
    from unittest.mock import AsyncMock
    controller = Mock()
    
    # Mock async send_message - retourne une coroutine
    async def mock_send_async(*args, **kwargs):
        return "Enrichissement Archiviste test"
    
    # Mock async call_chat_api - MÉTHODE CRITIQUE UTILISÉE PAR add_memory
    async def mock_call_chat_api(*args, **kwargs):
        # Retourne un JSON enrichi factice
        import json
        response = json.dumps({
            "titre": "Test enrichi",
            "résumé": "Résumé test automatique",
            "valence": 1,
            "score_impact": 0.7,
            "tags": ["test"]
        })
        return response, None  # (response, error)
    
    # Utiliser AsyncMock pour tracking automatique
    controller.send_message = AsyncMock(side_effect=mock_send_async)
    controller.call_chat_api = AsyncMock(side_effect=mock_call_chat_api)
    controller.provider = "Mistral"
    controller.model = "mistral-large"
    controller.is_available = Mock(return_value=True)
    controller.max_tokens = 4000
    controller.temperature = 0.7
    controller.context_length = 32000
    return controller


@pytest.fixture
def mock_embedding_controller():
    """Mock du contrôleur Embedding."""
    from unittest.mock import AsyncMock
    controller = Mock()
    
    # Mock async create_embedding - MÉTHODE CRITIQUE UTILISÉE PAR add_memory
    async def mock_create_embedding_async(*args, **kwargs):
        import numpy as np
        return np.random.rand(1024).tolist()
    
    # Utiliser AsyncMock pour tracking automatique
    controller.create_embedding = AsyncMock(side_effect=mock_create_embedding_async)
    controller.generate_embedding = AsyncMock(side_effect=mock_create_embedding_async)  # Alias
    controller.embedding_dim = 1024
    controller.provider = "Mistral"
    controller.is_available = Mock(return_value=True)
    return controller


# ===== FIXTURES MEMORY SYSTEM =====

class MemoryManagerTestWrapper:
    """Wrapper pour simplifier l'API MemoryManager dans les tests."""
    
    def __init__(self, real_mm):
        self._mm = real_mm
        self._counter = 0
    
    async def add_memory(self, text=None, text_brut=None, **kwargs):
        """Wrapper simplifié pour add_memory - génère auto memory_id."""
        self._counter += 1
        memory_id = f"test_mem_{self._counter}"
        content = text_brut or text or "Default test content"
        
        # Appel API réelle
        success = await self._mm.add_memory(
            memory_id=memory_id,
            text_brut=content,
            chat_controller=None,
            conversation_context="",
            interlocutor=""
        )
        return memory_id if success else None
    
    async def search_memories(self, query, k=None, limit=None, threshold=0.3, mode=None, filters=None):
        """Wrapper pour search_memories - k→limit automatique, ignore mode/filters."""
        actual_limit = limit or k or 10
        # Note: mode et filters ignorés car API réelle ne les supporte pas
        return await self._mm.search_memories(
            query=query,
            limit=actual_limit,
            threshold=threshold
        )
    
    async def update_memory(self, memory_id, metadata=None, **kwargs):
        """Wrapper pour update_memory - adapte metadata."""
        # Si metadata fourni, extraire title/summary
        if metadata:
            title = metadata.get('title')
            summary = metadata.get('summary')
            return await self._mm.update_memory(
                memory_id=memory_id,
                title=title,
                summary=summary,
                **kwargs
            )
        return await self._mm.update_memory(memory_id=memory_id, **kwargs)
    
    async def delete_memory(self, memory_id):
        """Wrapper pour delete_memory - SYNCHRONE dans l'API réelle."""
        # delete_memory est sync, pas async !
        return self._mm.delete_memory(memory_id)
    
    def get_memory_count(self):
        """Wrapper sync pour get_memory_count."""
        return self._mm.get_memory_count()
    
    def get_all_memories(self):
        """Wrapper pour get_all_memories - fallback si méthode n'existe pas."""
        if hasattr(self._mm, 'get_all_memories'):
            return self._mm.get_all_memories()
        # Fallback: requête SQL directe
        import sqlite3
        with sqlite3.connect(self._mm.db_path) as conn:
            cursor = conn.execute("SELECT * FROM memories")
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def get_memory_by_id(self, memory_id):
        """Récupère un souvenir par ID - wrapper pour tests."""
        if hasattr(self._mm, 'get_memory_by_id'):
            return self._mm.get_memory_by_id(memory_id)
        # Fallback: requête SQL directe
        import sqlite3
        with sqlite3.connect(self._mm.db_path) as conn:
            cursor = conn.execute("SELECT * FROM memories WHERE memory_id = ?", (memory_id,))
            columns = [desc[0] for desc in cursor.description]
            row = cursor.fetchone()
            return dict(zip(columns, row)) if row else None
    
    def cleanup(self):
        """Wrapper pour cleanup."""
        self._mm.cleanup()
    
    # Exposer les attributs du MemoryManager réel
    @property
    def faiss_index(self):
        return self._mm.faiss_index
    
    @property
    def db_path(self):
        return self._mm.db_path
    
    @property
    def next_faiss_pos(self):
        """Attribut pour tests FAISS."""
        return getattr(self._mm, 'next_faiss_pos', 0)
    
    @property
    def id_to_faiss(self):
        """Mapping ID→FAISS pour tests."""
        return getattr(self._mm, 'id_to_faiss', {})
    
    def rebuild_faiss_index(self):
        """Wrapper pour rebuild_faiss_index."""
        if hasattr(self._mm, 'rebuild_faiss_index'):
            return self._mm.rebuild_faiss_index()
        # Fallback: méthode non implémentée
        return False


@pytest.fixture
def mock_memory_manager(temp_dir, mock_archiviste_controller, mock_embedding_controller):
    """Mock du MemoryManager avec base SQLite temporaire."""
    from memory_manager import MemoryManager
    from queue import Queue
    
    db_path = temp_dir / "test_memory.db"
    index_path = temp_dir / "test_faiss.index"
    status_queue = Queue()
    
    # Créer une instance réelle avec dépendances mockées
    mm = MemoryManager(
        db_path=db_path,
        index_path=index_path,
        embedding_dim=1024,
        archiviste_ia=mock_archiviste_controller,
        embedding_ia=mock_embedding_controller,
        status_queue=status_queue
    )
    
    # Wrapper pour simplifier les tests
    wrapper = MemoryManagerTestWrapper(mm)
    
    yield wrapper
    
    # Cleanup
    mm.cleanup()
    if db_path.exists():
        db_path.unlink()
    if index_path.exists():
        index_path.unlink()


# ===== FIXTURES SETTINGS =====

@pytest.fixture
def mock_settings_manager(temp_dir):
    """Mock du SettingsManager avec fichier temporaire."""
    from core_logic import SettingsManager
    
    settings_path = temp_dir / "test_settings.json"
    sm = SettingsManager(settings_path)
    
    # Configuration test par défaut
    sm.settings = {
        "chat_api": {
            "provider": "OpenAI",
            "api_key": "test-key-123",
            "api_model": "gpt-4",
            "backend_type": "API",
            "temperature": 0.7,
            "max_tokens": 4000
        },
        "reasoning_api": {
            "provider": "Mistral",
            "api_key": "test-mistral-key",
            "api_model": "mistral-large",
            "backend_type": "API"
        },
        "embedding_api": {
            "provider": "Mistral",
            "backend_type": "API"
        }
    }
    sm.save()
    
    yield sm
    
    # Cleanup
    if settings_path.exists():
        settings_path.unlink()


# ===== FIXTURES AUDIO =====

@pytest.fixture
def mock_audio_manager():
    """Mock de l'AudioManager."""
    manager = Mock()
    manager.tts_engines = ["system", "google", "elevenlabs"]
    manager.stt_engines = ["whisper", "google"]
    manager.current_tts_engine = "system"
    manager.current_stt_engine = "whisper"
    manager.speak = Mock(return_value=True)
    manager.transcribe = Mock(return_value="Transcription test")
    manager.is_available = Mock(return_value=True)
    return manager


# ===== FIXTURES STATUS QUEUE =====

@pytest.fixture
def status_queue():
    """Queue de statut pour messages UI."""
    from queue import Queue
    return Queue()


# ===== FIXTURES CONVERSATION =====

@pytest.fixture
def sample_conversation():
    """Conversation exemple pour tests."""
    return [
        {"role": "user", "content": "Bonjour OGMA"},
        {"role": "assistant", "content": "Bonjour ! Comment puis-je vous aider ?"},
        {"role": "user", "content": "Parle-moi de la mémoire"},
        {"role": "assistant", "content": "La mémoire est un système hybride..."}
    ]


@pytest.fixture
def sample_memory_data():
    """Données mémoire exemples pour tests."""
    return [
        {
            "text": "Premier souvenir de test",
            "type": "conversation",
            "title": "Test 1",
            "valence": 1,
            "score_impact": 0.8
        },
        {
            "text": "Deuxième souvenir important",
            "type": "reflection",
            "title": "Test 2",
            "valence": 0,
            "score_impact": 0.6
        },
        {
            "text": "Troisième souvenir technique",
            "type": "technical",
            "title": "Test 3",
            "valence": -1,
            "score_impact": 0.4
        }
    ]


# ===== FIXTURES ASYNC =====

@pytest.fixture
def event_loop():
    """Event loop pour tests asynchrones."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ===== MARKERS PYTEST =====

def pytest_configure(config):
    """Configuration des markers pytest personnalisés."""
    config.addinivalue_line(
        "markers", "slow: marque les tests lents (>1s)"
    )
    config.addinivalue_line(
        "markers", "integration: tests d'intégration multi-composants"
    )
    config.addinivalue_line(
        "markers", "e2e: tests end-to-end complets"
    )
    config.addinivalue_line(
        "markers", "requires_api: tests nécessitant API keys valides"
    )
    config.addinivalue_line(
        "markers", "requires_gpu: tests nécessitant GPU"
    )
