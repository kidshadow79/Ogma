"""
Module: backend_communication.py
Description: Communication avec backends IA (list models, test connection)
Extrait de: ogma_ng.py (lignes 4489-4540)
Date: 2025-11-02
"""

from typing import List, Optional, Tuple


async def list_models(
    backend_type: str,
    provider: Optional[str],
    api_key: Optional[str],
    api_mgr,
    ollama_mgr,
    gguf_mgr,
    kobold_mgr
) -> Tuple[List[str], Optional[str]]:
    """
    Liste les modèles disponibles pour un backend donné.
    
    Args:
        backend_type: Type backend ('API', 'Ollama', 'GGUF', 'KoboldCpp')
        provider: Provider API si backend_type='API'
        api_key: Clé API si backend_type='API'
        api_mgr: Instance APIManager
        ollama_mgr: Instance OllamaManager
        gguf_mgr: Instance GGUFManager
        kobold_mgr: Instance KoboldManager
        
    Returns:
        tuple[list[str], str|None]: (liste_modèles, erreur_optionnelle)
    """
    try:
        if backend_type == 'API':
            provider_val = provider or 'Aucun'
            if provider_val == 'Aucun':
                return [], "Aucun fournisseur API sélectionné."
            models, api_err = await api_mgr.list_models(api_key, provider_val)
            return models, api_err
            
        elif backend_type == 'Ollama':
            models = await ollama_mgr.list_models()
            return models, None
            
        elif backend_type == 'GGUF':
            models = gguf_mgr.list_models()
            return models, None
            
        elif backend_type == 'KoboldCpp':
            models = await kobold_mgr.list_models()
            return models, None
            
        else:
            return [], f"Type de backend inconnu: {backend_type}"
            
    except Exception as e:
        return [], f"Erreur lors de la récupération des modèles: {str(e)}"


async def test_connection(
    backend_type: str,
    provider: Optional[str],
    api_key: Optional[str],
    service_url: Optional[str],
    api_mgr,
    ollama_mgr,
    gguf_mgr,
    kobold_mgr
) -> Tuple[bool, str]:
    """
    Teste la connexion à un backend IA.
    
    Args:
        backend_type: Type backend ('API', 'Ollama', 'GGUF', 'KoboldCpp')
        provider: Provider API si backend_type='API'
        api_key: Clé API si backend_type='API'
        service_url: URL service pour Ollama/KoboldCpp
        api_mgr: Instance APIManager
        ollama_mgr: Instance OllamaManager
        gguf_mgr: Instance GGUFManager
        kobold_mgr: Instance KoboldManager
        
    Returns:
        tuple[bool, str]: (succès, message_statut)
    """
    try:
        if backend_type == 'API':
            provider_val = provider or 'Aucun'
            if provider_val == 'Aucun':
                return False, "Aucun fournisseur API sélectionné."
            return await api_mgr.test_connection(api_key, provider_val)
            
        elif backend_type == 'Ollama':
            return await ollama_mgr.test_connection(service_url)
            
        elif backend_type == 'GGUF':
            return gguf_mgr.test_connection()
            
        elif backend_type == 'KoboldCpp':
            return await kobold_mgr.test_connection(service_url)
            
        else:
            return False, f"Type de backend inconnu: {backend_type}"
            
    except Exception as e:
        return False, f"Erreur lors du test de connexion: {str(e)}"
