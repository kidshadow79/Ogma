"""
Project RAG Extension pour OGMA
================================

Extension de gestion documentaire avec RAG isolé par projet.
Upload fichiers → chunking adaptatif → vectorisation FAISS → injection contexte chat.

Architecture:
- project_config.py    : Configuration JSON par projet
- project_manager.py   : Mémoire isolée SQLite + FAISS
- project_chunker.py   : Chunking adaptatif par type de fichier
- project_retriever.py : Recherche sémantique + cache
- project_injector.py  : Injection contexte dans le pipeline chat
- project_ui.py        : Interface NiceGUI overlay

Auteur: Yohan BROCARD
Date: Janvier 2026
"""

from typing import Optional, Dict, Any

try:
    from utils.i18n import t
except Exception:
    def t(key, **kwargs):
        return key

# ========== SINGLETON ==========
_project_rag_instance = None
_initialized = False

# Composants internes
_config = None
_memory = None
_retriever = None
_injector = None
_ui = None
_embedder = None


def initialize_project_rag(embedding_controller=None) -> bool:
    """
    Initialise l'extension Project RAG avec le contrôleur d'embedding.

    Args:
        embedding_controller: Contrôleur embedding OGMA (pour vectoriser les chunks)

    Returns:
        True si initialisé avec succès
    """
    global _initialized, _config, _memory, _retriever, _injector, _ui, _embedder

    if _initialized:
        print("[PROJECT-RAG] Deja initialise")
        return True

    if embedding_controller is None:
        print("[PROJECT-RAG] Erreur: embedding_controller requis")
        return False

    try:
        _embedder = embedding_controller

        # Config projet (mono-projet "default" pour l'instant)
        from .project_config import ProjectConfig
        _config = ProjectConfig("default")

        # Mémoire isolée SQLite + FAISS
        from .project_manager import ProjectMemory
        _memory = ProjectMemory(_config.project_dir)

        # Retriever sémantique avec cache
        from .project_retriever import ProjectRetriever
        _retriever = ProjectRetriever(_memory, _embedder)

        # Injector pour le pipeline chat
        from .project_injector import ProjectInjector
        _injector = ProjectInjector(_config, _retriever)

        _initialized = True
        stats = _memory.get_stats()
        print(f"[PROJECT-RAG] Extension initialisee ({stats['files']} fichiers, {stats['chunks']} chunks)")
        return True

    except Exception as e:
        print(f"[PROJECT-RAG] Erreur initialisation: {e}")
        import traceback
        traceback.print_exc()
        return False


def is_available() -> bool:
    """Vérifie si l'extension est disponible (modules importables)."""
    try:
        from .project_config import ProjectConfig
        from .project_manager import ProjectMemory
        return True
    except ImportError:
        return False


def is_initialized() -> bool:
    """Vérifie si l'extension est initialisée."""
    return _initialized


def is_active() -> bool:
    """Vérifie si un projet est actif (toggle ON)."""
    if not _initialized or _config is None:
        return False
    return _config.active


def get_project_injector() -> Optional[Any]:
    """Retourne l'injector pour le hook dans le pipeline chat."""
    return _injector


def get_project_config() -> Optional[Any]:
    """Retourne la config du projet courant."""
    return _config


def get_project_memory() -> Optional[Any]:
    """Retourne la mémoire du projet courant."""
    return _memory


def show_ui():
    """Affiche l'overlay UI du projet. Initialise le composant UI si nécessaire."""
    global _ui

    if not _initialized:
        print("[PROJECT-RAG] Extension non initialisee, impossible d'afficher l'UI")
        return

    if _ui is None:
        from .project_ui import ProjectUI
        _ui = ProjectUI(_config, _memory, _retriever, _injector, _embedder)

    _ui.show_overlay()


def get_ui_components() -> Dict[str, Any]:
    """
    Retourne les composants UI pour intégration dans le header OGMA.

    Returns:
        Dict avec callback pour le bouton sidebar
    """
    if not _initialized:
        return {}

    return {
        'header_button': {
            'icon': 'folder_open',
            'tooltip': t('pr_header_tooltip'),
            'on_click': show_ui,
        }
    }


def cleanup():
    """Nettoyage propre de l'extension."""
    global _initialized, _config, _memory, _retriever, _injector, _ui, _embedder

    if _retriever:
        _retriever.clear_cache()

    _config = None
    _memory = None
    _retriever = None
    _injector = None
    _ui = None
    _embedder = None
    _initialized = False
    print("[PROJECT-RAG] Extension nettoyee")
