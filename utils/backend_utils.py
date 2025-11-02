"""
Module: backend_utils.py
Description: Utilitaires pour gestion backends IA
Extrait de: ogma_ng.py (ligne 314-319)
Date: 2025-11-02
"""


def map_backend_for_controller(backend: str) -> str:
    """
    Normalise le nom du backend pour compatibilité controllers.
    
    Args:
        backend: Nom du backend (ex: "GGUF", "API", "Ollama")
        
    Returns:
        str: Nom normalisé du backend
        
    Examples:
        >>> map_backend_for_controller("GGUF")
        'gguf'
        >>> map_backend_for_controller("API")
        'api'
    """
    return backend.lower() if backend else "api"
