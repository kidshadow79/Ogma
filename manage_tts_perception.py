# manage_tts_perception.py

"""
Gestionnaire de conflit TTS/Perception - Interface de contrôle
"""

import sys
import json
from pathlib import Path
from tts_perception_manager import get_tts_perception_manager, get_manager_status
from quick_fix_tts import disable_tts_system, restore_tts

def show_status():
    """Affiche le statut complet du système"""
    print("📊 === STATUT TTS/PERCEPTION ===")
    print()
    
    # Statut gestionnaire
    status = get_manager_status()
    print("🔧 GESTIONNAIRE:")
    print(f"   Perception active: {'✅' if status.get('perception_active', False) else '❌'}")
    print(f"   TTS temporairement désactivé: {'✅' if status.get('tts_disabled', False) else '❌'}")
    print(f"   Backup TTS disponible: {'✅' if status.get('has_backup', False) else '❌'}")
    
    # Statut config
    settings_path = Path("data/settings.json")
    if settings_path.exists():
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            tts_enabled = settings.get("tts", {}).get("enabled", True)
            tts_engine = settings.get("tts", {}).get("engine", "unknown")
            
            print()
            print("⚙️ CONFIGURATION ACTUELLE:")
            print(f"   TTS activé: {'✅' if tts_enabled else '❌'}")
            print(f"   Moteur TTS: {tts_engine}")
            
            # Backups disponibles
            backup_files = []
            if Path("data/settings.backup").exists():
                backup_files.append("settings.backup (gestionnaire)")
            if Path("data/settings_backup_no_tts.json").exists():
                backup_files.append("settings_backup_no_tts.json (quick_fix)")
                
            if backup_files:
                print(f"   Backups: {', '.join(backup_files)}")
            else:
                print("   Backups: Aucun")
                
        except Exception as e:
            print(f"❌ Erreur lecture config: {e}")
    else:
        print("❌ Configuration non trouvée")

def manual_disable():
    """Désactivation manuelle TTS"""
    print("🚫 Désactivation manuelle TTS...")
    if disable_tts_system():
        print("✅ TTS désactivé manuellement")
    else:
        print("❌ Échec désactivation manuelle")

def manual_restore():
    """Restauration manuelle TTS"""
    print("🔄 Restauration manuelle TTS...")
    
    # Essayer d'abord le gestionnaire
    manager = get_tts_perception_manager()
    if manager.restore_tts_config():
        print("✅ TTS restauré via gestionnaire")
        return
    
    # Sinon utiliser quick_fix
    if restore_tts():
        print("✅ TTS restauré via backup")
    else:
        print("❌ Échec restauration")

def clean_backups():
    """Nettoie les fichiers de backup"""
    print("🧹 Nettoyage backups...")
    
    backup_files = [
        "data/settings.backup",
        "data/settings_backup_no_tts.json"
    ]
    
    cleaned = 0
    for backup_file in backup_files:
        backup_path = Path(backup_file)
        if backup_path.exists():
            backup_path.unlink()
            print(f"   ✅ {backup_file} supprimé")
            cleaned += 1
    
    if cleaned == 0:
        print("   ℹ️ Aucun backup à nettoyer")
    else:
        print(f"✅ {cleaned} backup(s) nettoyé(s)")

def main():
    if len(sys.argv) < 2:
        print("🎛️ === GESTIONNAIRE TTS/PERCEPTION ===")
        print()
        print("COMMANDES:")
        print("  python manage_tts_perception.py status      # Voir statut complet")
        print("  python manage_tts_perception.py disable     # Désactiver TTS manuellement")
        print("  python manage_tts_perception.py restore     # Restaurer TTS manuellement")  
        print("  python manage_tts_perception.py clean       # Nettoyer backups")
        print()
        print("UTILISATION NORMALE:")
        print("- Le gestionnaire se déclenche automatiquement quand Perception démarre/arrête")
        print("- Utilisez les commandes manuelles seulement en cas de problème")
        print()
        print("DIAGNOSTIC CONFLIT:")
        print("✅ TTS désactivé = Perception stable")
        print("❌ TTS activé + Perception = Risque de plantage")
        return
    
    command = sys.argv[1].lower()
    
    if command == "status":
        show_status()
    elif command == "disable":
        manual_disable()
    elif command == "restore":
        manual_restore()
    elif command == "clean":
        clean_backups()
    else:
        print(f"❌ Commande inconnue: {command}")
        print("Utilisez: status, disable, restore, ou clean")

if __name__ == "__main__":
    main()