# tts_perception_manager.py

"""
Gestionnaire de conflit TTS/Perception
Désactive automatiquement TTS quand Perception est active
"""

import json
import os
import threading
import time
from pathlib import Path
from datetime import datetime

class TTSPerceptionManager:
    """Gestionnaire du conflit TTS/Perception"""
    
    def __init__(self):
        self.settings_path = Path("data/settings.json")
        self.original_tts_config = None
        self.perception_active = False
        self.tts_disabled_for_perception = False
        self.lock = threading.Lock()
        
    def backup_tts_config(self):
        """Sauvegarde la configuration TTS originale"""
        try:
            if not self.settings_path.exists():
                return False
                
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            # Sauvegarder config TTS originale
            self.original_tts_config = {
                "tts": settings.get("tts", {}),
                "audio": settings.get("audio", {})
            }
            
            print(f"[TTS-MANAGER] 💾 Configuration TTS sauvegardée")
            return True
            
        except Exception as e:
            print(f"[TTS-MANAGER] ❌ Erreur sauvegarde TTS: {e}")
            return False
    
    def disable_tts_for_perception(self):
        """Désactive TTS pour éviter conflit avec Perception"""
        with self.lock:
            if self.tts_disabled_for_perception:
                return True
                
            try:
                # Backup config si pas déjà fait
                if not self.original_tts_config:
                    if not self.backup_tts_config():
                        return False
                
                # Lire config actuelle
                with open(self.settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                # Désactiver TTS
                settings["tts"] = {
                    "enabled": False,
                    "engine": "none",
                    "voice_id": "",
                    "speed": 150,
                    "volume": 0.8,
                    "api_key": ""
                }
                
                settings["audio"] = settings.get("audio", {})
                settings["audio"]["tts_enabled"] = False
                
                # Sauvegarder
                with open(self.settings_path, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, indent=2, ensure_ascii=False)
                
                self.tts_disabled_for_perception = True
                print(f"[TTS-MANAGER] 🚫 TTS désactivé pour Perception")
                return True
                
            except Exception as e:
                print(f"[TTS-MANAGER] ❌ Erreur désactivation TTS: {e}")
                return False
    
    def restore_tts_config(self):
        """Restaure la configuration TTS originale"""
        with self.lock:
            if not self.tts_disabled_for_perception or not self.original_tts_config:
                return True
                
            try:
                # Lire config actuelle
                with open(self.settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                # Restaurer TTS original
                settings["tts"] = self.original_tts_config["tts"]
                settings["audio"] = {**settings.get("audio", {}), **self.original_tts_config["audio"]}
                
                # Sauvegarder
                with open(self.settings_path, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, indent=2, ensure_ascii=False)
                
                self.tts_disabled_for_perception = False
                print(f"[TTS-MANAGER] ✅ Configuration TTS restaurée")
                return True
                
            except Exception as e:
                print(f"[TTS-MANAGER] ❌ Erreur restauration TTS: {e}")
                return False
    
    def on_perception_start(self):
        """Appelé quand Perception démarre"""
        print(f"[TTS-MANAGER] 📷 Perception démarrée - désactivation TTS...")
        self.perception_active = True
        return self.disable_tts_for_perception()
    
    def on_perception_stop(self):
        """Appelé quand Perception s'arrête"""
        print(f"[TTS-MANAGER] 🛑 Perception arrêtée - restauration TTS...")
        self.perception_active = False
        return self.restore_tts_config()
    
    def get_status(self):
        """Retourne l'état du gestionnaire"""
        return {
            "perception_active": self.perception_active,
            "tts_disabled": self.tts_disabled_for_perception,
            "has_backup": self.original_tts_config is not None
        }

# Instance globale
_tts_perception_manager = None

def get_tts_perception_manager():
    """Récupère l'instance globale du gestionnaire"""
    global _tts_perception_manager
    if _tts_perception_manager is None:
        _tts_perception_manager = TTSPerceptionManager()
    return _tts_perception_manager

# API publique
def on_perception_start():
    """Hook: Perception démarre"""
    return get_tts_perception_manager().on_perception_start()

def on_perception_stop():
    """Hook: Perception s'arrête"""
    return get_tts_perception_manager().on_perception_stop()

def get_manager_status():
    """Statut du gestionnaire"""
    return get_tts_perception_manager().get_status()

if __name__ == "__main__":
    # Test du gestionnaire
    import sys
    
    if len(sys.argv) < 2:
        print("🔧 GESTIONNAIRE TTS/PERCEPTION")
        print()
        print("USAGE:")
        print("  python tts_perception_manager.py test      # Test du système")
        print("  python tts_perception_manager.py status    # État actuel")
        print("  python tts_perception_manager.py restore   # Forcer restauration")
        sys.exit(0)
    
    cmd = sys.argv[1].lower()
    manager = get_tts_perception_manager()
    
    if cmd == "test":
        print("🧪 Test du gestionnaire...")
        print("1. Simulation démarrage Perception...")
        if manager.on_perception_start():
            print("✅ TTS désactivé")
        else:
            print("❌ Échec désactivation")
            
        time.sleep(2)
        
        print("2. Simulation arrêt Perception...")
        if manager.on_perception_stop():
            print("✅ TTS restauré")
        else:
            print("❌ Échec restauration")
    
    elif cmd == "status":
        status = manager.get_status()
        print("📊 ÉTAT GESTIONNAIRE:")
        print(f"   Perception active: {'✅' if status['perception_active'] else '❌'}")
        print(f"   TTS désactivé: {'✅' if status['tts_disabled'] else '❌'}")
        print(f"   Backup disponible: {'✅' if status['has_backup'] else '❌'}")
    
    elif cmd == "restore":
        print("🔄 Restauration forcée...")
        if manager.restore_tts_config():
            print("✅ TTS restauré")
        else:
            print("❌ Échec restauration")
    
    else:
        print(f"❌ Commande inconnue: {cmd}")