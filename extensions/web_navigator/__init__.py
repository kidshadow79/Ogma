# Extension Web Navigator pour OGMA avec Serper API
# Recherche internet intelligente

"""
Extension Web Navigator avec Serper - Point d'entrée
===================================================

Permet à OGMA d'accéder à internet via l'API Serper avec phrases magiques naturelles.

Fonctionnalités:
- Recherche web générale avec /web ou "cherche sur internet"
- Actualités avec /news ou "actualités sur"  
- Images avec /image ou "cherche des images de"
- Recherche académique avec /scholar
- Phrases magiques naturelles reconnues automatiquement
- Sauvegarde automatique des images dans data/uploads

Usage:
- /web intelligence artificielle → Recherche web
- "cherche sur internet dernières nouvelles IA" → Détection automatique
- /news actualités technologie → Actualités récentes
- /image robots humanoïdes → Recherche d'images + téléchargement
"""

__version__ = "2.0.0-serper"
__author__ = "OGMA Team"

# Export des composants principaux pour Serper
from .config import WebNavigatorConfig
from .serper_client import SerperClient
from .commands import WebNavigatorCommands
from .extension import WebNavigatorExtension

# Import conditionnel des anciens composants pour compatibilité temporaire
try:
    from .ui_components import WebNavigatorUI
    UI_AVAILABLE = True
except ImportError:
    UI_AVAILABLE = False
    WebNavigatorUI = None

__all__ = [
    'WebNavigatorConfig',
    'SerperClient',
    'WebNavigatorCommands',
    'WebNavigatorExtension'
]

if UI_AVAILABLE:
    __all__.append('WebNavigatorUI')

def get_extension_info():
    """Retourne les informations de l'extension pour le système OGMA"""
    return {
        "name": "Web Navigator (Serper)",
        "version": __version__,
        "description": "Recherche internet intelligente via Serper API avec phrases magiques",
        "author": __author__,
        "commands": ["/web", "/news", "/image", "/search", "/scholar"],
        "magic_phrases": ["cherche sur internet", "recherche sur internet", "actualités sur", "cherche des images"],
        "config_section": "web_navigator",
        "requires_api_key": True,
        "api_provider": "Serper"
    }