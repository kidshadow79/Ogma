"""
OGMA CORE UTILS - Fonctions utilitaires générales
==================================================

Fonctions utilitaires partagées dans tout OGMA.
"""

from typing import Any, Optional


def safe_ui_operation(operation_func, *args, **kwargs) -> Any:
    """
    Wrapper sécurisé pour les opérations NiceGUI.
    Évite les crashes par déconnexion client.
    
    Args:
        operation_func: Fonction UI à exécuter
        *args, **kwargs: Arguments de la fonction
        
    Returns:
        Résultat de l'opération ou None si erreur client
    """
    try:
        return operation_func(*args, **kwargs)
    except Exception as e:
        error_msg = str(e).lower()
        if any(keyword in error_msg for keyword in ["deleted", "client", "belongs"]):
            print(f"[UI-PROTECTION] ⚠️ Opération UI annulée (client déconnecté): {type(e).__name__}")
            return None
        else:
            # Erreur non liée à la déconnexion, la propager
            raise e


def notify_safe(message: str, type: str = 'info') -> None:
    """
    Affiche une notification de manière sûre (évite les erreurs si client déconnecté).
    
    Args:
        message: Message à afficher
        type: Type de notification ('info', 'warning', 'error', 'positive')
    """
    try:
        # Import dynamique pour éviter les dépendances circulaires
        from nicegui import ui
        ui.notify(message, type=type)
    except Exception as e:
        error_msg = str(e).lower()
        if any(keyword in error_msg for keyword in ["deleted", "client", "belongs", "no running"]):
            # Client déconnecté ou pas de contexte UI - ignorer silencieusement
            print(f"[NOTIFY-SAFE] ⚠️ Notification ignorée (pas de client): {message[:50]}...")
        else:
            print(f"[NOTIFY-SAFE] ❌ Erreur notification: {e}")


def get_current_time() -> str:
    """
    Retourne l'heure actuelle formatée pour Luna.
    
    Returns:
        Chaîne décrivant l'heure actuelle
    """
    try:
        from temporal_injector import TemporalInjector
        temporal_injector = TemporalInjector()
        return temporal_injector.get_current_time()
    except Exception as e:
        from datetime import datetime
        return datetime.now().strftime("%H:%M")


def format_size(size_bytes: int) -> str:
    """
    Formate une taille en bytes en format lisible.
    
    Args:
        size_bytes: Taille en bytes
        
    Returns:
        Chaîne formatée (ex: "1.5 MB")
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Tronque un texte à une longueur maximale.
    
    Args:
        text: Texte à tronquer
        max_length: Longueur maximale
        suffix: Suffixe à ajouter si tronqué
        
    Returns:
        Texte tronqué
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


print("[OGMA-UTILS] ✅ Fonctions utilitaires chargées")
