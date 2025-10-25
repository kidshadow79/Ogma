# JOURNAL Extension Journal de Bord - Configuration

"""
Configuration centralisée pour l'extension Journal de Bord
Paramètres utilisateur, constantes système, settings persistants
"""

from typing import Dict, Any
from pathlib import Path
import json

class JournalConfig:
    """Configuration centralisée extension Journal de Bord"""
    
    # Constantes système
    VERSION = "1.0.0"
    EXTENSION_NAME = "journal_de_bord"
    DISPLAY_NAME = "JOURNAL Journal de Bord"
    
    # Paramètres par défaut (optimisés pour éviter refactoring)
    DEFAULT_SETTINGS = {
        # Contexte matinal
        "auto_context_display": True,           # Affichage automatique contexte du jour
        "context_max_entries": 3,               # Nombre max d'entrées dans contexte
        "context_format": "summary",            # Format: "summary", "detailed", "minimal"
        "context_position": "top",              # Position: "top", "sidebar", "modal"
        
        # Génération de résumés
        "summary_min_tokens": 200,              # Tokens minimum par résumé
        "summary_max_tokens": 400,              # Tokens maximum par résumé
        "summary_style": "balanced",            # Style: "formal", "casual", "technical", "balanced"
        "auto_tag_generation": True,            # Génération automatique de tags
        "importance_detection": True,           # Détection automatique d'importance
        
        # Interface utilisateur
        "button_position": "header",            # Position bouton: "header", "sidebar", "floating"
        "modal_size": "large",                  # Taille modal: "small", "medium", "large"
        "calendar_view": "month",               # Vue calendrier: "week", "month", "year"
        "theme_mode": "auto",                   # Thème: "light", "dark", "auto"
        
        # Performance et stockage
        "lazy_loading": True,                   # Chargement à la demande
        "cache_size": 100,                      # Taille cache (entrées)
        "auto_backup": True,                    # Sauvegarde automatique
        "backup_frequency": "daily",            # Fréquence: "hourly", "daily", "weekly"
        "data_retention_days": 365,             # Rétention données (jours)
        "compress_old_data": True,              # Compression données anciennes
        
        # Notifications
        "notification_level": "normal",         # Niveau: "silent", "normal", "verbose"
        "success_notifications": True,          # Notifications de succès
        "error_notifications": True,           # Notifications d'erreur
        
        # Intégration OGMA
        "memory_integration": True,             # Intégration avec MemoryManager
        "conversation_tracking": True,          # Suivi des conversations
        "auto_save_important": True,            # Sauvegarde auto conversations importantes
        
        # Sécurité
        "encrypt_sensitive": False,             # Chiffrement données sensibles
        "backup_encryption": False,             # Chiffrement sauvegardes
        "data_validation": True,                # Validation stricte données
        
        # Extension activée par défaut
        "extension_enabled": True               # Extension activée (opt-out)
    }
    
    # Messages système pour cohérence narrative
    SYSTEM_MESSAGES = {
        "context_header": "JOURNAL Contexte de la journée",
        "no_entries_today": "Aucune entrée pour aujourd'hui. La journée commence !",
        "entry_created": "OK Nouvelle entrée ajoutée au journal",
        "entry_failed": "ERREUR Erreur lors de la création de l'entrée",
        "backup_created": "SAVE Sauvegarde automatique créée",
        "data_loaded": "DATA Journal chargé avec succès",
        "search_no_results": "Aucun résultat trouvé pour cette recherche",
        "invalid_date": "Date invalide sélectionnée"
    }
    
    # Constantes techniques
    TECHNICAL_CONSTANTS = {
        "max_file_size_mb": 50,                # Taille max fichier JSON (MB)
        "max_entries_per_day": 50,             # Nombre max entrées par jour
        "search_index_update_interval": 60,    # Mise à jour index (secondes)
        "backup_retention_days": 30,           # Rétention sauvegardes
        "cache_expiry_hours": 24,              # Expiration cache
        "json_indent": 2,                      # Indentation JSON
        "encoding": "utf-8",                   # Encodage fichiers
        "date_format": "%Y-%m-%d",             # Format date standard
        "datetime_format": "%Y-%m-%dT%H:%M:%SZ" # Format datetime ISO
    }
    
    def __init__(self, settings_file: Path = None):
        """Initialise la configuration avec persistence"""
        if isinstance(settings_file, str):
            settings_file = Path(settings_file)
        self.settings_file = settings_file or Path("data/journal_settings.json")
        self.current_settings = self.DEFAULT_SETTINGS.copy()
        self.load_settings()
    
    def load_settings(self):
        """Charge les settings depuis le fichier de persistence"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    saved_settings = json.load(f)
                    # Merge avec validation des clés
                    for key, value in saved_settings.items():
                        if key in self.DEFAULT_SETTINGS:
                            self.current_settings[key] = value
                print(f"[JOURNAL-CONFIG] OK Settings chargés depuis {self.settings_file}")
        except Exception as e:
            print(f"[JOURNAL-CONFIG] WARN Erreur chargement settings: {e}")
            # Fallback sur les paramètres par défaut (pas d'erreur bloquante)
    
    def save_settings(self):
        """Sauvegarde les settings actuels"""
        try:
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_settings, f, indent=2, ensure_ascii=False)
            print(f"[JOURNAL-CONFIG] OK Settings sauvegardés dans {self.settings_file}")
        except Exception as e:
            print(f"[JOURNAL-CONFIG] ERREUR Erreur sauvegarde settings: {e}")
            raise  # Erreur critique pour la sauvegarde
    
    def get(self, key: str, default=None):
        """Récupère un paramètre de configuration"""
        return self.current_settings.get(key, default)
    
    def get_required(self, key: str):
        """
        Récupère un paramètre OBLIGATOIRE - lève erreur si manquant
        Pattern validé cognitive_mirror: pas de fallbacks masquants
        """
        if key not in self.current_settings:
            raise ValueError(f"[JOURNAL-CONFIG] Paramètre obligatoire manquant: '{key}' - Vérifiez la configuration")
        value = self.current_settings[key]
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValueError(f"[JOURNAL-CONFIG] Paramètre obligatoire vide: '{key}' - Configurez-le dans l'interface")
        return value
    
    def set(self, key: str, value: Any) -> bool:
        """Modifie un paramètre et sauvegarde immédiatement"""
        if key in self.DEFAULT_SETTINGS:
            old_value = self.current_settings.get(key)
            self.current_settings[key] = value
            try:
                self.save_settings()
                print(f"[JOURNAL-CONFIG] OK Paramètre mis à jour: {key} = {value} (était: {old_value})")
                return True
            except Exception as e:
                # Rollback en cas d'erreur de sauvegarde
                self.current_settings[key] = old_value
                print(f"[JOURNAL-CONFIG] ERREUR Rollback paramètre {key}: erreur sauvegarde")
                raise
        else:
            print(f"[JOURNAL-CONFIG] WARN Paramètre inconnu ignoré: {key}")
            return False
    
    def is_enabled(self) -> bool:
        """Vérifie si l'extension est activée"""
        return self.get("extension_enabled", True)
    
    def toggle_enabled(self) -> bool:
        """Bascule l'état ON/OFF de l'extension"""
        current_state = self.is_enabled()
        new_state = not current_state
        self.set("extension_enabled", new_state)
        print(f"[JOURNAL-CONFIG] UPDATE Extension {'ACTIVÉE' if new_state else 'DÉSACTIVÉE'}")
        return new_state
    
    def get_generation_settings(self) -> Dict[str, Any]:
        """Retourne les paramètres de génération de résumés"""
        return {
            "min_tokens": self.get("summary_min_tokens", 200),
            "max_tokens": self.get("summary_max_tokens", 400),
            "style": self.get("summary_style", "balanced"),
            "auto_tags": self.get("auto_tag_generation", True),
            "importance_detection": self.get("importance_detection", True)
        }
    
    def get_ui_settings(self) -> Dict[str, Any]:
        """Retourne les paramètres d'interface utilisateur"""
        return {
            "button_position": self.get("button_position", "header"),
            "modal_size": self.get("modal_size", "large"),
            "calendar_view": self.get("calendar_view", "month"),
            "theme_mode": self.get("theme_mode", "auto")
        }
    
    def get_context_settings(self) -> Dict[str, Any]:
        """Retourne les paramètres de contexte matinal"""
        return {
            "auto_display": self.get("auto_context_display", True),
            "max_entries": self.get("context_max_entries", 3),
            "format": self.get("context_format", "summary"),
            "position": self.get("context_position", "top")
        }
    
    def get_performance_settings(self) -> Dict[str, Any]:
        """Retourne les paramètres de performance"""
        return {
            "lazy_loading": self.get("lazy_loading", True),
            "cache_size": self.get("cache_size", 100),
            "compress_old_data": self.get("compress_old_data", True),
            "retention_days": self.get("data_retention_days", 365)
        }
    
    def validate_settings(self) -> Dict[str, str]:
        """
        Valide la cohérence des paramètres
        Returns: Dict d'erreurs (vide si tout OK)
        """
        errors = {}
        
        # Validation tokens
        min_tokens = self.get("summary_min_tokens", 200)
        max_tokens = self.get("summary_max_tokens", 400)
        if min_tokens >= max_tokens:
            errors["tokens"] = "summary_min_tokens doit être < summary_max_tokens"
        
        # Validation cache
        cache_size = self.get("cache_size", 100)
        if cache_size < 10:
            errors["cache"] = "cache_size doit être >= 10"
        
        # Validation rétention
        retention = self.get("data_retention_days", 365)
        if retention < 7:
            errors["retention"] = "data_retention_days doit être >= 7"
        
        # Validation contexte
        max_entries = self.get("context_max_entries", 3)
        if max_entries < 1 or max_entries > 10:
            errors["context"] = "context_max_entries doit être entre 1 et 10"
        
        return errors
    
    def reset_to_defaults(self):
        """Remet tous les paramètres par défaut"""
        self.current_settings = self.DEFAULT_SETTINGS.copy()
        self.save_settings()
        print("[JOURNAL-CONFIG] UPDATE Paramètres remis aux valeurs par défaut")
    
    def export_settings(self) -> dict:
        """Exporte la configuration actuelle pour sauvegarde"""
        return {
            "version": self.VERSION,
            "exported_at": self.TECHNICAL_CONSTANTS["datetime_format"],
            "settings": self.current_settings.copy()
        }
    
    def import_settings(self, settings_data: dict) -> bool:
        """Importe une configuration depuis une sauvegarde"""
        try:
            if "settings" in settings_data:
                imported_settings = settings_data["settings"]
                # Validation et merge
                for key, value in imported_settings.items():
                    if key in self.DEFAULT_SETTINGS:
                        self.current_settings[key] = value
                
                self.save_settings()
                print("[JOURNAL-CONFIG] OK Settings importés avec succès")
                return True
        except Exception as e:
            print(f"[JOURNAL-CONFIG] ERREUR Erreur import settings: {e}")
            return False

# Instance globale partagée (singleton pattern OGMA)
_config_instance = None

def get_journal_config() -> JournalConfig:
    """Retourne l'instance singleton de configuration"""
    global _config_instance
    if _config_instance is None:
        _config_instance = JournalConfig()
    return _config_instance

def reset_journal_config():
    """Reset l'instance singleton (pour tests principalement)"""
    global _config_instance
    _config_instance = None