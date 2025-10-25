"""
Extension Web Navigator - Classe principale
==========================================

Classe unifiée pour l'extension Web Navigator avec Serper API.
"""

from .config import WebNavigatorConfig
from .serper_client import SerperClient
from .commands import WebNavigatorCommands

try:
    from .ui_components import WebNavigatorUI
    UI_AVAILABLE = True
except ImportError:
    UI_AVAILABLE = False
    WebNavigatorUI = None

class WebNavigatorExtension:
    """
    Extension Web Navigator complète pour OGMA
    
    Intègre:
    - Configuration (WebNavigatorConfig)
    - Client API Serper (SerperClient)
    - Gestionnaire de commandes (WebNavigatorCommands)
    - Interface utilisateur (WebNavigatorUI) si disponible
    """
    
    def __init__(self, settings_manager=None):
        """
        Initialise l'extension Web Navigator
        
        Args:
            settings_manager: Gestionnaire des paramètres OGMA (optionnel)
        """
        print(f"[WEB-NAV-EXTENSION] 🚀 Initialisation de l'extension Web Navigator")
        
        # Configuration
        self.config = WebNavigatorConfig(settings_manager)
        print(f"[WEB-NAV-EXTENSION] ✅ Configuration chargée")
        
        # Client Serper API
        self.serper_client = SerperClient(self.config)
        print(f"[WEB-NAV-EXTENSION] ✅ Client Serper initialisé")
        
        # Gestionnaire de commandes
        self.commands = WebNavigatorCommands(self.config, self.serper_client)
        print(f"[WEB-NAV-EXTENSION] ✅ Gestionnaire de commandes initialisé")
        
        # Interface utilisateur (si disponible)
        self.ui = None
        if UI_AVAILABLE:
            try:
                self.ui = WebNavigatorUI(self.config)
                print(f"[WEB-NAV-EXTENSION] ✅ Interface utilisateur initialisée")
            except Exception as e:
                print(f"[WEB-NAV-EXTENSION] ⚠️ Interface utilisateur non disponible: {e}")
        else:
            print(f"[WEB-NAV-EXTENSION] ⚠️ Interface utilisateur non disponible")
        
        print(f"[WEB-NAV-EXTENSION] 🎉 Extension Web Navigator prête!")
    
    def is_enabled(self):
        """Vérifie si l'extension est activée"""
        return self.config.is_enabled()
    
    def is_web_search_enabled(self):
        """Vérifie si la recherche web est activée"""
        return self.config.is_web_search_enabled()
    
    def has_api_key(self):
        """Vérifie si la clé API Serper est configurée"""
        return bool(self.config.get_serper_api_key())
    
    def get_status(self):
        """Retourne le statut de l'extension"""
        return {
            'enabled': self.is_enabled(),
            'web_search_enabled': self.is_web_search_enabled(),
            'api_key_configured': self.has_api_key(),
            'ui_available': UI_AVAILABLE and self.ui is not None
        }
    
    async def process_message(self, message):
        """
        Traite un message pour détecter les requêtes internet
        
        Args:
            message (str): Message à traiter
            
        Returns:
            tuple: (réponse, chemin_fichier) si traité, (None, None) sinon
        """
        if not self.is_enabled():
            return None, None
            
        if self.commands.is_internet_request(message):
            return await self.commands.process_internet_request(message)
        
        return None, None
    
    def get_extension_info(self):
        """Retourne les informations de l'extension"""
        return {
            "name": "Web Navigator (Serper)",
            "version": "2.0.0-serper",
            "description": "Recherche internet intelligente via Serper API avec phrases magiques",
            "author": "OGMA Team",
            "commands": ["/web", "/news", "/image", "/search", "/scholar"],
            "magic_phrases": ["cherche sur internet", "recherche sur internet", "actualités sur", "cherche des images"],
            "config_section": "web_navigator",
            "requires_api_key": True,
            "api_provider": "Serper",
            "status": self.get_status()
        }