"""
OGMA Next Generation V2 - Extension Architecture
=================================================

Toutes les nouvelles fonctionnalités OGMA post-refactoring.

Architecture:
- features/     → Fonctionnalités complètes (isolées)
- shared/       → Code partagé entre features
- templates/    → Templates pour nouvelles features

Philosophie:
- ogma_ng.py est GELÉ (7723 lignes max)
- Toute nouvelle feature → extensions/ogma_ng_v2/features/
- Code modulaire, testable, documenté

Auteur: Tytan
Date: 25 octobre 2025
Version: 2.0.0
"""

__version__ = "2.0.0"
__author__ = "Tytan"

# Feature registry (sera rempli progressivement)
_registered_features = []


def register_v2_features(dependencies=None):
    """
    Hook principal pour enregistrer toutes les features V2.
    
    Appelé depuis ogma_ng.py au démarrage.
    
    Args:
        dependencies (dict, optional): Dépendances OGMA
            - chat_controller: AIController
            - archiviste_controller: AIController  
            - memory_manager: MemoryManager
            - settings_manager: SettingsManager
            - audio_manager: AudioManager
    
    Returns:
        dict: Status d'initialisation {feature_name: bool}
    """
    print("[OGMA-V2] 🚀 Initialisation OGMA V2 Architecture...")
    print(f"[OGMA-V2] Version: {__version__}")
    
    status = {}
    
    # IMPORTANT: Importer et initialiser features ici
    # Exemple:
    # from .features.ma_feature import initialize_feature
    # status['ma_feature'] = initialize_feature(dependencies)
    
    # Pour l'instant, aucune feature (structure vide)
    if not _registered_features:
        print("[OGMA-V2] ℹ️  Aucune feature V2 enregistrée (architecture prête)")
    else:
        print(f"[OGMA-V2] ✅ {len(_registered_features)} feature(s) V2 chargée(s)")
    
    print("[OGMA-V2] ✅ Initialisation terminée")
    return status


def get_registered_features():
    """Retourne liste des features V2 enregistrées."""
    return _registered_features.copy()


def is_feature_available(feature_name):
    """
    Vérifie si une feature V2 est disponible.
    
    Args:
        feature_name (str): Nom de la feature
        
    Returns:
        bool: True si disponible
    """
    return feature_name in _registered_features


# Version info pour debug
def get_version_info():
    """Retourne informations version OGMA V2."""
    return {
        "version": __version__,
        "author": __author__,
        "features_count": len(_registered_features),
        "features": _registered_features
    }
