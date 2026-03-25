# 🧠 Extension Introspection v2.0 pour OGMA

"""
Extension Introspection v2.0 - IntrospectionCore

Système direct sans fallback : IntrospectionCore est le seul moteur.
Si un module manque, l'erreur est explicite au démarrage.

Usage:
    from extensions.cognitive_mirror import initialize_introspection
    success = initialize_introspection(chat_controller, archiviste_controller, memory_manager)
"""

# ===== IMPORTS DIRECTS (v2.1 - config_v2 est le système actif) =====
# config_v2 = source de vérité. Aliases pour rétrocompatibilité.

from .introspection_core import IntrospectionCore, initialize_introspection_core, get_introspection_core
from .config_v2 import IntrospectionConfigV2, get_introspection_config

# Aliases rétrocompatibilité (ancien naming)
get_config = get_introspection_config
CognitiveMirrorConfig = IntrospectionConfigV2

# UI
from .ui_components import CognitiveMirrorUI
from .memory_integration import MemoryIntegration

print("[INTROSPECTION] ✅ Système v2.1 chargé (IntrospectionCore + config_v2)")

__version__ = "2.1.0"
__author__ = "OGMA Team"

# Instance globale singleton
_core_instance = None

def initialize_introspection(chat_controller, archiviste_controller, memory_manager, ui_container=None, settings_manager=None):
    """
    Initialise l'extension Introspection v2.0.
    """
    global _core_instance

    success = initialize_introspection_core(
        chat_controller=chat_controller,
        archiviste_controller=archiviste_controller,
        memory_manager=memory_manager,
        ui_container=ui_container,
        settings_manager=settings_manager
    )

    if success:
        _core_instance = get_introspection_core()
        config = get_introspection_config()
        state = "ON" if config.is_enabled() else "OFF"
        print(f"[INTROSPECTION] ✅ Extension v2.0 initialisée (état: {state})")
        return True

    print("[INTROSPECTION] ❌ Échec initialisation v2.0")
    return False


def get_introspection():
    """Retourne l'instance singleton IntrospectionCore."""
    return get_introspection_core()


def is_v21() -> bool:
    """True — v4 utilise le chemin v2.1 (boite thinking + streaming)."""
    return True


# ===== API LEGACY (Compatibilité v1.0 → v2.0) =====

def initialize_cognitive_mirror(chat_controller, archiviste_controller, memory_manager, ui_container=None, settings_manager=None):
    """
    Initialise extension (LEGACY - redirige vers v2.0)

    Maintenue pour compatibilité avec code OGMA existant.
    Utilise le nouveau système Introspection v2.0 en arrière-plan.

    Args:
        chat_controller: Instance AIController
        archiviste_controller: Instance AIController
        memory_manager: Instance MemoryManager
        ui_container: Container UI (optionnel)
        settings_manager: SettingsManager (optionnel)

    Returns:
        bool: True si succès
    """
    print("[COGNITIVE-MIRROR] ⚠️ Fonction legacy appelée - redirection vers Introspection v2.0")
    return initialize_introspection(chat_controller, archiviste_controller, memory_manager, ui_container, settings_manager)

def get_cognitive_mirror():
    """
    Retourne instance core (LEGACY - redirige vers v2.0)

    Returns:
        IntrospectionCore ou None
    """
    return get_introspection()


def is_available() -> bool:
    """Vérifie si extension disponible."""
    return get_introspection_core() is not None


def is_enabled() -> bool:
    """Vérifie si extension activée."""
    core = get_introspection_core()
    # is_enabled est une @property sur IntrospectionCore
    return core is not None and core.is_enabled


def toggle_enabled() -> bool:
    """Bascule état ON/OFF."""
    core = get_introspection_core()
    if core:
        return core.toggle_enableyhud()
    return False


def get_ui_components():
    """Retourne composants UI pour intégration OGMA."""
    core = get_introspection_core()
    if core:
        return core.get_ui_components()
    return None


def get_extension_status():
    """
    Retourne statut détaillé extension

    Returns:
        dict: Statut complet
    """
    if not is_available():
        return {
            "available": False,
            "enabled": False,
            "error": "Extension non initialisée"
        }

    return _core_instance.get_status()


async def process_user_message(user_message: str, conversation_context: dict):
    """Traite message utilisateur avec introspection si nécessaire."""
    if not is_enabled():
        return None
    core = get_introspection_core()
    if core:
        return await core.process_user_message(user_message, conversation_context)
    return None


def check_magic_phrases(text: str, source: str = "user"):
    """Vérifie phrases magiques dans texte."""
    core = get_introspection_core()
    if core:
        return core.check_magic_phrases(text, source)
    return None


def stop_current_introspection(reason: str = "external"):
    """Arrête introspection en cours."""
    core = get_introspection_core()
    if core:
        core.stop_current_introspection(reason)


def cleanup():
    """Nettoyage et fermeture propre."""
    global _core_instance
    if _core_instance:
        print("[INTROSPECTION] Fermeture extension v2.0")
        _core_instance.cleanup()
        _core_instance = None
        print("[INTROSPECTION] ✅ Extension v2.0 fermée")


# ===== FONCTIONS LEGACY COMPATIBILITÉ =====

def get_reflection_context():
    """LEGACY - Obsolète."""
    return None


def start_inactivity_monitoring():
    """LEGACY - Obsolète."""
    pass


def stop_reflection_session():
    """LEGACY - Redirige vers stop_current_introspection()."""
    stop_current_introspection("legacy_stop")


# Points d'entrée publics pour intégration OGMA
__all__ = [
    # API principale v2.0
    'initialize_introspection',
    'get_introspection',
    'process_user_message',
    'check_magic_phrases',
    'stop_current_introspection',
    'is_v21',

    # Aliases compatibilité (legacy nommage)
    'initialize_cognitive_mirror',
    'get_cognitive_mirror',
    'get_reflection_context',
    'start_inactivity_monitoring',
    'stop_reflection_session',

    # API commune
    'cleanup',
    'is_available',
    'is_enabled',
    'toggle_enabled',
    'get_ui_components',
    'get_extension_status',

    # Configuration (v2.0 + alias v2.1)
    'get_introspection_config',
    'get_config',
    'CognitiveMirrorConfig',
    'IntrospectionConfigV2',

    # Classes
    'IntrospectionCore',
    'CognitiveMirrorUI',
    'MemoryIntegration',
]