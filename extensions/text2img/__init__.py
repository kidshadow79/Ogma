"""
Extension Text2Image pour OGMA
===============================
Génération d'images via IA à partir de descriptions textuelles.

Backends supportés:
- Perchance (Stable Diffusion) - Gratuit et illimité
- [Futur] Fal.ai (Flux)
- [Futur] ComfyUI Local

Usage:
    from extensions.text2img import get_text2img_manager, initialize_text2img

    # Initialiser l'extension
    initialize_text2img(settings_manager)

    # Utiliser le manager
    manager = get_text2img_manager()
    image_data = await manager.generate_image("fantasy landscape")
"""

__version__ = "1.0.0"
__author__ = "OGMA Team"

from .text2img_manager import Text2ImageManager

# Singleton instance
_text2img_manager = None
_is_initialized = False

def initialize_text2img(settings_manager):
    """
    Initialise l'extension Text2Image

    Args:
        settings_manager: Instance de SettingsManager d'OGMA

    Returns:
        bool: True si l'initialisation a réussi
    """
    global _text2img_manager, _is_initialized

    try:
        print("[TEXT2IMG] 🎨 Initialisation extension Text2Image v1.0.0")

        # Créer le manager
        _text2img_manager = Text2ImageManager(settings_manager)

        # Initialiser le backend
        success = _text2img_manager.initialize_backend()

        if success:
            _is_initialized = True
            print("[TEXT2IMG] ✅ Extension Text2Image initialisée avec succès")
            return True
        else:
            print("[TEXT2IMG] ❌ Échec initialisation backend")
            return False

    except Exception as e:
        print(f"[TEXT2IMG] ❌ Erreur initialisation: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_text2img_manager():
    """
    Récupère l'instance du manager Text2Image

    Returns:
        Text2ImageManager: L'instance du manager, ou None si non initialisé
    """
    if not _is_initialized:
        print("[TEXT2IMG] ⚠️ Extension non initialisée, appelez initialize_text2img() d'abord")
        return None
    return _text2img_manager

def is_available():
    """
    Vérifie si l'extension est disponible

    Returns:
        bool: True si l'extension est initialisée et prête
    """
    return _is_initialized and _text2img_manager is not None

__all__ = [
    'Text2ImageManager',
    'initialize_text2img',
    'get_text2img_manager',
    'is_available'
]
