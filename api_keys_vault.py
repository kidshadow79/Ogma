"""
API Keys Vault - Gestion des clés API par provider
===================================================
Module modulaire pour stocker et récupérer les clés API de chaque provider.
Évite de devoir re-saisir les clés lors des changements de provider.

Structure dans settings.json:
{
    "api_keys_vault": {
        "OpenAI": "sk-...",
        "Anthropic": "sk-ant-...",
        "Mistral": "...",
        "Google": "...",
        "GROK": "xai-...",
        "AIHorde": "..."
    }
}
"""

import json
from pathlib import Path
from typing import Optional, Dict

# Chemin du fichier settings
SETTINGS_PATH = Path(__file__).parent / "data" / "settings.json"
VAULT_KEY = "api_keys_vault"


def _load_settings() -> dict:
    """Charge le fichier settings.json"""
    try:
        if SETTINGS_PATH.exists():
            with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"[API-VAULT] ⚠️ Erreur lecture settings: {e}")
    return {}


def _save_settings(settings: dict) -> bool:
    """Sauvegarde le fichier settings.json"""
    try:
        with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"[API-VAULT] ⚠️ Erreur sauvegarde settings: {e}")
        return False


def get_vault() -> Dict[str, str]:
    """
    Récupère le vault complet des clés API.
    
    Returns:
        dict: Dictionnaire {provider: api_key}
    """
    settings = _load_settings()
    return settings.get(VAULT_KEY, {})


def get_api_key(provider: str) -> Optional[str]:
    """
    Récupère la clé API pour un provider donné.
    
    Args:
        provider: Nom du provider (OpenAI, Anthropic, Mistral, Google, GROK, AIHorde)
        
    Returns:
        str ou None: La clé API si elle existe
    """
    if not provider or provider == 'Aucun':
        return None
    
    vault = get_vault()
    key = vault.get(provider)
    
    if key:
        print(f"[API-VAULT] 🔑 Clé récupérée pour {provider}")
    
    return key


def save_api_key(provider: str, api_key: str) -> bool:
    """
    Sauvegarde une clé API pour un provider.
    
    Args:
        provider: Nom du provider
        api_key: Clé API à sauvegarder
        
    Returns:
        bool: True si sauvegarde réussie
    """
    if not provider or provider == 'Aucun':
        return False
    
    if not api_key or api_key.strip() == '':
        return False
    
    settings = _load_settings()
    
    # Initialiser le vault si nécessaire
    if VAULT_KEY not in settings:
        settings[VAULT_KEY] = {}
    
    # Sauvegarder la clé
    settings[VAULT_KEY][provider] = api_key.strip()
    
    if _save_settings(settings):
        print(f"[API-VAULT] 💾 Clé sauvegardée pour {provider}")
        return True
    return False


def delete_api_key(provider: str) -> bool:
    """
    Supprime la clé API d'un provider.
    
    Args:
        provider: Nom du provider
        
    Returns:
        bool: True si suppression réussie
    """
    if not provider or provider == 'Aucun':
        return False
    
    settings = _load_settings()
    
    if VAULT_KEY not in settings:
        return False
    
    if provider in settings[VAULT_KEY]:
        del settings[VAULT_KEY][provider]
        if _save_settings(settings):
            print(f"[API-VAULT] 🗑️ Clé supprimée pour {provider}")
            return True
    
    return False


def list_saved_providers() -> list:
    """
    Liste tous les providers ayant une clé sauvegardée.
    
    Returns:
        list: Liste des noms de providers
    """
    vault = get_vault()
    return list(vault.keys())


def has_saved_key(provider: str) -> bool:
    """
    Vérifie si un provider a une clé sauvegardée.
    
    Args:
        provider: Nom du provider
        
    Returns:
        bool: True si une clé existe
    """
    if not provider or provider == 'Aucun':
        return False
    
    vault = get_vault()
    return provider in vault and bool(vault[provider])


def sync_from_current_settings() -> int:
    """
    Synchronise le vault depuis les clés actuellement dans les settings.
    Utile pour migration initiale.
    
    Returns:
        int: Nombre de clés synchronisées
    """
    settings = _load_settings()
    synced = 0
    
    # Sections contenant des clés API
    sections = ['chat_api', 'reasoning_api', 'embedding_api']
    
    for section in sections:
        if section in settings:
            provider = settings[section].get('provider')
            api_key = settings[section].get('api_key')
            
            if provider and provider != 'Aucun' and api_key:
                if save_api_key(provider, api_key):
                    synced += 1
    
    if synced > 0:
        print(f"[API-VAULT] 🔄 {synced} clé(s) synchronisée(s) depuis settings")
    
    return synced


# ============================================================================
# HELPER POUR INTEGRATION UI
# ============================================================================

def get_key_or_current(provider: str, current_key: str) -> str:
    """
    Retourne la clé du vault si disponible, sinon la clé courante.
    Utile pour pré-remplir les champs lors du changement de provider.
    
    Args:
        provider: Provider sélectionné
        current_key: Clé actuellement dans le champ
        
    Returns:
        str: Clé à utiliser (vault prioritaire)
    """
    vault_key = get_api_key(provider)
    if vault_key:
        return vault_key
    return current_key or ''


def mask_key(api_key: str, visible_chars: int = 8) -> str:
    """
    Masque une clé API pour affichage sécurisé.
    
    Args:
        api_key: Clé à masquer
        visible_chars: Nombre de caractères visibles au début
        
    Returns:
        str: Clé masquée (ex: "sk-abc123...****")
    """
    if not api_key or len(api_key) <= visible_chars:
        return api_key or ''
    
    return api_key[:visible_chars] + '...' + '*' * 4
