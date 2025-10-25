# 🧠 Extension Introspection v2.0 pour OGMA (anciennement Cognitive Mirror)

"""
Extension Introspection v2.0 - Dialogue visible Luna ↔ Archiviste

NOUVEAU PARADIGME:
- Déclenchement à la demande (phrases magiques ou mode always)
- Dialogue visible streaming dans boîte thinking
- Sauvegarde conditionnelle décidée par l'IA
- Sans détection automatique d'inactivité

Architecture v2.0:
- introspection_core.py: Moteur principal simplifié (NOUVEAU)
- introspection_orchestrator.py: Gestion dialogue streaming (NOUVEAU)
- ui_parameters_modal_v2.py: Popup paramètres complet (NOUVEAU)
- config.py: Configuration étendue avec nouveaux paramètres
- memory_integration.py: Sauvegarde conditionnelle IA
- ui_components.py: Interface avec backward compatibility

Usage v2.0:
    from extensions.cognitive_mirror import initialize_introspection

    # Initialisation
    success = initialize_introspection(
        chat_controller=luna_ai,
        archiviste_controller=archiviste_ai,
        memory_manager=memory_mgr
    )

    # Utilisation
    from extensions.cognitive_mirror import get_introspection_core
    core = get_introspection_core()

    # Traiter message utilisateur
    response = await core.process_user_message(user_msg, context)

COMPATIBILITÉ LEGACY:
    Les anciennes fonctions initialize_cognitive_mirror() et get_cognitive_mirror()
    sont maintenues pour compatibilité mais utilisent le nouveau système.
"""

from .config import CognitiveMirrorConfig, get_config

# Import nouveau système v2.0
try:
    from .introspection_core import IntrospectionCore, initialize_introspection_core, get_introspection_core
    V2_AVAILABLE = True
except ImportError:
    V2_AVAILABLE = False
    print("[INTROSPECTION] ⚠️ Système v2.0 non disponible - fallback v1.0")

# Import ancien système (fallback + compatibilité)
try:
    from .core_cognitive_mirror import CognitiveMirrorCore
    LEGACY_AVAILABLE = True
except ImportError:
    LEGACY_AVAILABLE = False

from .ui_components import CognitiveMirrorUI
from .memory_integration import MemoryIntegration

__version__ = "2.0.0"  # Version Introspection
__author__ = "OGMA Team"

# Instance globale (singleton pattern OGMA)
_core_instance = None

# ===== API v2.0 (NOUVEAU) =====

def initialize_introspection(chat_controller, archiviste_controller, memory_manager, ui_container=None):
    """
    Initialise l'extension Introspection v2.0 (NOUVEAU)

    Args:
        chat_controller: Instance AIController (Luna/IA principale)
        archiviste_controller: Instance AIController (Archiviste)
        memory_manager: Instance MemoryManager
        ui_container: Container UI NiceGUI (optionnel)

    Returns:
        bool: True si initialisation réussie
    """
    global _core_instance

    if not V2_AVAILABLE:
        print("[INTROSPECTION] ❌ Système v2.0 non disponible - utiliser fallback v1.0")
        return False

    try:
        print(f"[INTROSPECTION] 🚀 Initialisation extension v{__version__}")

        # Validation dépendances
        if not all([chat_controller, archiviste_controller, memory_manager]):
            raise ValueError("Dépendances OGMA manquantes")

        # Initialisation via fonction modulaire
        success = initialize_introspection_core(
            chat_controller=chat_controller,
            archiviste_controller=archiviste_controller,
            memory_manager=memory_manager,
            ui_container=ui_container
        )

        if success:
            _core_instance = get_introspection_core()
            print(f"[INTROSPECTION] ✅ Extension v2.0 initialisée (état: {'ON' if _core_instance.is_enabled else 'OFF'})")

        return success

    except Exception as e:
        print(f"[INTROSPECTION] ❌ Erreur initialisation: {e}")
        import traceback
        traceback.print_exc()
        return False


def get_introspection() -> 'IntrospectionCore':
    """
    Retourne l'instance singleton IntrospectionCore v2.0

    Returns:
        IntrospectionCore ou None
    """
    if V2_AVAILABLE:
        return get_introspection_core()
    return None


# ===== API LEGACY (Compatibilité v1.0 → v2.0) =====

def initialize_cognitive_mirror(chat_controller, archiviste_controller, memory_manager, ui_container=None):
    """
    Initialise extension (LEGACY - redirige vers v2.0)

    Maintenue pour compatibilité avec code OGMA existant.
    Utilise le nouveau système Introspection v2.0 en arrière-plan.

    Args:
        chat_controller: Instance AIController
        archiviste_controller: Instance AIController
        memory_manager: Instance MemoryManager
        ui_container: Container UI (optionnel)

    Returns:
        bool: True si succès
    """
    print("[COGNITIVE-MIRROR] ⚠️ Fonction legacy appelée - redirection vers Introspection v2.0")
    return initialize_introspection(chat_controller, archiviste_controller, memory_manager, ui_container)

def get_cognitive_mirror():
    """
    Retourne instance core (LEGACY - redirige vers v2.0)

    Returns:
        IntrospectionCore ou None
    """
    return get_introspection()


def is_available() -> bool:
    """Vérifie si extension disponible"""
    return get_introspection_core() is not None


def is_enabled() -> bool:
    """Vérifie si extension activée"""
    core = get_introspection_core()
    return core is not None and core.is_enabled


def toggle_enabled() -> bool:
    """
    Bascule état ON/OFF

    Returns:
        bool: Nouvel état
    """
    if is_available():
        return _core_instance.toggle_enabled()
    return False


def get_ui_components():
    """
    Retourne composants UI pour intégration OGMA

    Returns:
        CognitiveMirrorUI ou None
    """
    if is_available():
        return _core_instance.get_ui_components()
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
    """
    Traite message utilisateur avec introspection si nécessaire

    Args:
        user_message: Message utilisateur
        conversation_context: Contexte conversationnel

    Returns:
        Réponse enrichie ou None
    """
    if is_enabled():
        return await _core_instance.process_user_message(user_message, conversation_context)
    return None


def check_magic_phrases(text: str, source: str = "user"):
    """
    Vérifie phrases magiques dans texte

    Args:
        text: Texte à vérifier
        source: "user" ou "ia"

    Returns:
        Type phrase ("trigger", "stop") ou None
    """
    if is_available():
        return _core_instance.check_magic_phrases(text, source)
    return None


def stop_current_introspection(reason: str = "external"):
    """
    Arrête introspection en cours

    Args:
        reason: Raison arrêt
    """
    if is_available():
        _core_instance.stop_current_introspection(reason)


def cleanup():
    """Nettoyage et fermeture propre"""
    global _core_instance
    if _core_instance:
        print("[INTROSPECTION] 🔄 Fermeture extension")
        _core_instance.cleanup()
        _core_instance = None
        print("[INTROSPECTION] ✅ Extension fermée proprement")


# ===== FONCTIONS LEGACY OBSOLÈTES (Compatibilité) =====

def get_reflection_context():
    """LEGACY - Obsolète en v2.0"""
    return None


def start_inactivity_monitoring():
    """LEGACY - Obsolète en v2.0 (pas de détection auto)"""
    pass


def stop_reflection_session():
    """LEGACY - Redirige vers stop_current_introspection()"""
    stop_current_introspection("legacy_stop")

# Points d'entrée publics pour intégration OGMA
__all__ = [
    # ===== API v2.0 (NOUVEAU) =====
    'initialize_introspection',
    'get_introspection',
    'process_user_message',
    'check_magic_phrases',
    'stop_current_introspection',

    # ===== API LEGACY (Compatibilité) =====
    'initialize_cognitive_mirror',
    'get_cognitive_mirror',
    'get_reflection_context',  # Obsolète
    'start_inactivity_monitoring',  # Obsolète
    'stop_reflection_session',  # Redirigé

    # ===== API COMMUNE =====
    'cleanup',
    'is_available',
    'is_enabled',
    'toggle_enabled',
    'get_ui_components',
    'get_extension_status',

    # Configuration
    'get_config',
    'CognitiveMirrorConfig',

    # Classes
    'IntrospectionCore',  # Si v2.0 disponible
    'CognitiveMirrorUI',
    'MemoryIntegration'
]