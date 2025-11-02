"""
Module: backend_utils.py
Description: Utilitaires pour gestion backends IA
Extrait de: ogma_ng.py (ligne 314-319)
Date: 2025-11-02
"""


def map_backend_for_controller(backend: str) -> str:
    """
    Normalise le nom du backend pour compatibilité controllers.
    
    CRITIQUE: Retourne UPPERCASE pour compatibilité avec dictionnaires AIController.
    
    Args:
        backend: Nom du backend (ex: "GGUF", "API", "Ollama")
        
    Returns:
        str: Nom normalisé du backend en MAJUSCULES
        
    Examples:
        >>> map_backend_for_controller("GGUF")
        'GGUF'
        >>> map_backend_for_controller("api")
        'API'
        >>> map_backend_for_controller("Ollama")
        'OLLAMA'
    """
    return backend.upper() if backend else "API"
