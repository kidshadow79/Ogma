# quick_fix_tts.py

"""
Fix rapide - Désactiver TTS complètement pour tester Perception
"""

import json
import os
from pathlib import Path

def disable_tts_system():
    """Désactive complètement le système TTS"""
    settings_path = Path("data/settings.json")
    
    if not settings_path.exists():
        print("❌ Fichier settings.json non trouvé")
        return False
    
    try:
        # Lire config
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        # Backup
        backup_path = settings_path.with_suffix('.backup')
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        print(f"✅ Backup créé: {backup_path}")
        
        # Désactiver TOUT TTS
        tts_config = {
            "enabled": False,
            "engine": "none",
            "voice_id": "",
            "speed": 150,
            "volume": 0.8,
            "api_key": ""
        }
        
        audio_config = {
            "stt_enabled": False,
            "tts_enabled": False,
            "input_device": -1,
            "output_device": -1
        }
        
        settings["tts"] = tts_config
        settings["audio"] = audio_config
        
        # Sauvegarder
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        
        print("✅ TTS complètement désactivé")
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def restore_tts():
    """Restaure TTS depuis backup"""
    settings_path = Path("data/settings.json")
    backup_path = settings_path.with_suffix('.backup')
    
    if not backup_path.exists():
        print("❌ Pas de backup trouvé")
        return False
    
    try:
        with open(backup_path, 'r', encoding='utf-8') as f:
            original = json.load(f)
        
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(original, f, indent=2, ensure_ascii=False)
        
        backup_path.unlink()
        print("✅ TTS restauré")
        return True
        
    except Exception as e:
        print(f"❌ Erreur restauration: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("🚨 FIX RAPIDE TTS")
        print()
        print("USAGE:")
        print("  python quick_fix_tts.py disable   # Désactiver TTS")
        print("  python quick_fix_tts.py restore   # Restaurer TTS")
        print()
        print("TEST:")
        print("1. python quick_fix_tts.py disable")
        print("2. python launch_ogma.py  # Test sans TTS")
        print("3. python quick_fix_tts.py restore")
        sys.exit(0)
    
    cmd = sys.argv[1].lower()
    
    if cmd == "disable":
        print("🚫 Désactivation TTS...")
        if disable_tts_system():
            print("✅ TTS désactivé - testez maintenant OGMA")
        else:
            print("❌ Échec désactivation")
    
    elif cmd == "restore":
        print("🔄 Restauration TTS...")
        if restore_tts():
            print("✅ TTS restauré")
        else:
            print("❌ Échec restauration")
    
    else:
        print(f"❌ Commande inconnue: {cmd}")