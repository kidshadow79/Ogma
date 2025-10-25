"""
Configuration de l'extension Web Navigator avec Serper API

Gère tous les paramètres de recherche internet via Serper
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional

class WebNavigatorConfig:
    """Gestionnaire de configuration pour l'extension Web Navigator avec Serper API"""
    
    def __init__(self, settings_manager=None):
        self.settings_manager = settings_manager
        self.config_section = "web_navigator"
        
        # Configuration par défaut optimisée pour Serper
        self.default_config = {
            "enabled": True,
            
            # API Serper
            "serper_api_key": "",
            "serper_base_url": "https://google.serper.dev",
            
            # Fonctionnalités activées
            "web_search_enabled": True,
            "image_search_enabled": True,
            "news_search_enabled": True,
            "scholar_search_enabled": True,
            
            # Paramètres de recherche
            "results_per_query": 10,
            "language": "fr",
            "country": "fr",
            "request_timeout": 30,
            "rate_limit_seconds": 1.0,
            
            # Gestion des images téléchargées
            "save_downloaded_images": True,
            "image_save_directory": "data/uploads",
            "max_image_size_mb": 10.0,
            "supported_image_formats": ["jpg", "jpeg", "png", "gif", "webp"],
            
            # Options avancées
            "extract_snippets": True,
            "include_metadata": True,
            "safe_search": "moderate"
        }
        
        # Charger la config existante
        self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Charge la configuration depuis settings_manager ou crée les défauts"""
        if self.settings_manager and hasattr(self.settings_manager, 'settings'):
            # Récupérer la config existante ou créer les défauts
            current_config = self.settings_manager.settings.get(self.config_section, {})
            
            # Fusionner avec les défauts pour ajouter nouvelles options
            merged_config = self.default_config.copy()
            merged_config.update(current_config)
            
            # Sauvegarder seulement si des changements nécessaires
            if current_config != merged_config:
                self.settings_manager.settings[self.config_section] = merged_config
                self.settings_manager.save_settings()
                print(f"[WEB-NAV-CONFIG] ⚠️ Configuration mise à jour avec nouvelles options")
            
            return merged_config
        else:
            # Fallback : charger directement depuis settings.json
            try:
                import json
                import os
                
                settings_file = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'settings.json')
                if os.path.exists(settings_file):
                    with open(settings_file, 'r', encoding='utf-8') as f:
                        all_settings = json.load(f)
                    
                    current_config = all_settings.get(self.config_section, {})
                    
                    # Fusionner avec les défauts
                    merged_config = self.default_config.copy()
                    merged_config.update(current_config)
                    
                    print(f"[WEB-NAV-CONFIG] ✅ Configuration chargée depuis settings.json")
                    return merged_config
                else:
                    print(f"[WEB-NAV-CONFIG] ⚠️ settings.json non trouvé, utilisation défauts")
                    return self.default_config.copy()
            except Exception as e:
                print(f"[WEB-NAV-CONFIG] ❌ Erreur chargement settings.json: {e}")
                return self.default_config.copy()
    
    def get(self, key: str, default=None):
        """Récupère une valeur de configuration"""
        config = self.load_config()
        return config.get(key, default)
    
    def set(self, key: str, value: Any, auto_save: bool = True) -> bool:
        """Modifie une valeur de configuration"""
        try:
            if self.settings_manager and hasattr(self.settings_manager, 'settings'):
                if self.config_section not in self.settings_manager.settings:
                    self.settings_manager.settings[self.config_section] = self.default_config.copy()
                
                # Vérifier si la valeur a réellement changé
                current_value = self.settings_manager.settings[self.config_section].get(key)
                if current_value != value:
                    self.settings_manager.settings[self.config_section][key] = value
                    if auto_save:
                        self.settings_manager.save_settings()
                        print(f"[WEB-NAV-CONFIG] 💾 {key} modifié: {current_value} → {value}")
                return True
            else:
                print(f"[WEB-NAV-CONFIG] ⚠️ Impossible de sauvegarder {key}={value} (pas de settings_manager)")
                return False
        except Exception as e:
            print(f"[WEB-NAV-CONFIG] ❌ Erreur sauvegarde config: {e}")
            return False
    
    def is_enabled(self) -> bool:
        """Vérifie si l'extension est activée"""
        return self.get("enabled", True)
    
    def is_web_search_enabled(self) -> bool:
        """Vérifie si la recherche web Serper est activée"""
        return self.get("web_search_enabled", True) and self.is_enabled() and self.has_valid_api_key()
    
    def is_image_search_enabled(self) -> bool:
        """Vérifie si la recherche d'images Serper est activée"""
        return self.get("image_search_enabled", True) and self.is_enabled() and self.has_valid_api_key()
    
    def is_news_search_enabled(self) -> bool:
        """Vérifie si la recherche d'actualités Serper est activée"""
        return self.get("news_search_enabled", True) and self.is_enabled() and self.has_valid_api_key()
    
    def has_valid_api_key(self) -> bool:
        """Vérifie si une clé API Serper valide est configurée"""
        api_key = self.get("serper_api_key", "")
        return api_key and len(api_key.strip()) > 10  # Clés Serper font plus de 10 caractères
    
    def get_serper_api_key(self) -> str:
        """Retourne la clé API Serper"""
        return self.get("serper_api_key", "")
    
    def get_image_save_path(self) -> Path:
        """Retourne le chemin de sauvegarde des images"""
        save_dir = self.get("image_save_directory", "data/uploads")
        path = Path(save_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path
    
    def get_serper_base_url(self) -> str:
        """Retourne l'URL de base de l'API Serper"""
        return self.get("serper_base_url", "https://google.serper.dev")
    
    def get_request_timeout(self) -> int:
        """Retourne le timeout des requêtes"""
        return self.get("request_timeout", 30)
    
    def get_rate_limit(self) -> float:
        """Retourne le délai entre requêtes"""
        return self.get("rate_limit_seconds", 1.0)
    
    def get_results_per_query(self) -> int:
        """Retourne le nombre de résultats par requête"""
        return self.get("results_per_query", 10)
    
    def get_language(self) -> str:
        """Retourne la langue pour les recherches"""
        return self.get("language", "fr")
    
    def get_country(self) -> str:
        """Retourne le pays pour les recherches"""
        return self.get("country", "fr")
    
    def get_max_image_size_bytes(self) -> int:
        """Retourne la taille max des images en bytes"""
        mb = self.get("max_image_size_mb", 10.0)
        return int(mb * 1024 * 1024)
    
    def get_supported_image_formats(self) -> List[str]:
        """Retourne les formats d'images supportés"""
        return self.get("supported_image_formats", ["jpg", "jpeg", "png", "gif", "webp"])
    
    def export_config(self) -> Dict[str, Any]:
        """Exporte la configuration actuelle"""
        return self.load_config()
    
    def reset_to_defaults(self) -> bool:
        """Remet la configuration aux valeurs par défaut"""
        try:
            if self.settings_manager:
                self.settings_manager.settings[self.config_section] = self.default_config.copy()
                self.settings_manager.save_settings()
                return True
            return False
        except Exception as e:
            print(f"[WEB-NAV-CONFIG] ❌ Erreur reset config: {e}")
            return False