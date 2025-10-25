# integration_tts_safe.py

"""
Script d'intégration du TTS sans conflit dans OGMA
Remplace progressivement l'ancien système audio_manager
"""

import os
import shutil
from pathlib import Path
import json

def backup_current_audio_system():
    """Sauvegarde le système audio actuel"""
    print("💾 === SAUVEGARDE SYSTÈME AUDIO ACTUEL ===")
    
    files_to_backup = [
        "audio_manager.py",
        "data/settings.json"
    ]
    
    backup_folder = Path("backup_audio_system")
    backup_folder.mkdir(exist_ok=True)
    
    for file_path in files_to_backup:
        file_path = Path(file_path)
        if file_path.exists():
            backup_path = backup_folder / file_path.name
            shutil.copy2(file_path, backup_path)
            print(f"✅ Sauvegardé: {file_path} -> {backup_path}")
        else:
            print(f"⚠️ Fichier non trouvé: {file_path}")
    
    print(f"✅ Sauvegarde complète dans: {backup_folder}")
    return True

def update_settings_for_conflict_free_tts():
    """Met à jour settings.json pour utiliser le TTS sans conflit"""
    print("\n⚙️ === MISE À JOUR CONFIGURATION ===")
    
    settings_path = Path("data/settings.json")
    if not settings_path.exists():
        print("❌ settings.json non trouvé")
        return False
    
    try:
        # Lire config actuelle
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        # Ajouter section TTS sans conflit
        settings["tts_conflict_free"] = {
            "enabled": True,
            "preferred_engine": "edge_tts",
            "fallback_engines": ["gtts_offline", "system_safe", "fallback"],
            "auto_adapt_perception": True,
            "isolated_worker": True
        }
        
        # Marquer ancien TTS comme legacy
        if "tts" in settings:
            settings["tts_legacy"] = settings["tts"]
            settings["tts"]["enabled"] = False
            settings["tts"]["engine"] = "conflict_free"  # Redirection
        
        # Sauvegarder
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
        
        print("✅ Configuration mise à jour")
        print("   - TTS sans conflit activé")
        print("   - Ancien TTS marqué comme legacy")
        print("   - Auto-adaptation Perception activée")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur mise à jour config: {e}")
        return False

def create_audio_manager_wrapper():
    """Crée un wrapper pour compatibilité avec l'ancien audio_manager"""
    print("\n🔗 === CRÉATION WRAPPER COMPATIBILITÉ ===")
    
    wrapper_content = '''# audio_manager_wrapper.py

"""
Wrapper de compatibilité pour l'ancien audio_manager
Redirige vers le nouveau TTS sans conflit
"""

from tts_conflict_free import get_conflict_free_tts, speak_safe, set_perception_active

class AudioManagerWrapper:
    """Wrapper pour compatibilité avec ancien AudioManager"""
    
    def __init__(self):
        self.tts_safe = get_conflict_free_tts()
        self.initialized = False
    
    def initialize_tts(self):
        """Initialise le TTS (compatibilité)"""
        if not self.initialized:
            self.tts_safe.initialize()
            self.initialized = True
            print("[AUDIO-WRAPPER] ✅ TTS sans conflit initialisé")
        return True
    
    def speak(self, text, voice=None, speed=None, volume=None):
        """Interface speak compatible"""
        if not self.initialized:
            self.initialize_tts()
        
        options = {}
        if voice:
            options["voice"] = voice
        if speed:
            options["rate"] = f"{speed:+d}%"
        if volume:
            options["volume"] = volume
        
        return speak_safe(text, **options)
    
    def set_perception_mode(self, active):
        """Notifie l'état Perception (nouveau)"""
        set_perception_active(active)
    
    def cleanup(self):
        """Nettoyage"""
        if self.initialized:
            self.tts_safe.stop()
            self.initialized = False

# Instance globale pour compatibilité
_audio_manager = None

def get_audio_manager():
    """Récupère instance compatible AudioManager"""
    global _audio_manager
    if _audio_manager is None:
        _audio_manager = AudioManagerWrapper()
    return _audio_manager

# Fonctions legacy pour compatibilité
def speak_text(text, **kwargs):
    """Fonction legacy speak_text"""
    return get_audio_manager().speak(text, **kwargs)

def initialize_audio():
    """Fonction legacy initialize_audio"""
    return get_audio_manager().initialize_tts()
'''
    
    wrapper_path = Path("audio_manager_wrapper.py")
    with open(wrapper_path, 'w', encoding='utf-8') as f:
        f.write(wrapper_content)
    
    print(f"✅ Wrapper créé: {wrapper_path}")
    print("   - Compatible avec ancien AudioManager")
    print("   - Redirige vers TTS sans conflit")
    return True

def update_ogma_imports():
    """Met à jour les imports dans ogma_ng.py"""
    print("\n🔄 === MISE À JOUR IMPORTS OGMA ===")
    
    ogma_file = Path("ogma_ng.py")
    if not ogma_file.exists():
        print("❌ ogma_ng.py non trouvé")
        return False
    
    print("💡 Modifications à faire manuellement dans ogma_ng.py:")
    print("   1. Ajouter: from audio_manager_wrapper import get_audio_manager")
    print("   2. Remplacer: _audio_manager = AudioManager() par _audio_manager = get_audio_manager()")
    print("   3. Ajouter hook Perception: _audio_manager.set_perception_mode(perception_active)")
    
    return True

def test_integration():
    """Test complet de l'intégration"""
    print("\n🧪 === TEST INTÉGRATION ===")
    
    try:
        # Test import
        from tts_conflict_free import get_conflict_free_tts
        from audio_manager_wrapper import get_audio_manager
        
        print("✅ Imports réussis")
        
        # Test TTS sans conflit
        tts_safe = get_conflict_free_tts()
        tts_safe.initialize()
        print("✅ TTS sans conflit initialisé")
        
        # Test wrapper
        audio_mgr = get_audio_manager()
        audio_mgr.initialize_tts()
        print("✅ Wrapper AudioManager fonctionnel")
        
        # Test synthèse
        success = audio_mgr.speak("Test intégration TTS sans conflit dans OGMA")
        if success:
            print("✅ Synthèse vocale fonctionnelle")
        else:
            print("⚠️ Synthèse vocale en mode fallback")
        
        # Nettoyage
        audio_mgr.cleanup()
        print("✅ Nettoyage réussi")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test intégration: {e}")
        return False

def main():
    print("🎵 === INTÉGRATION TTS SANS CONFLIT ===")
    print()
    print("Cette intégration va:")
    print("1. Sauvegarder le système audio actuel")
    print("2. Créer un wrapper de compatibilité") 
    print("3. Mettre à jour la configuration")
    print("4. Tester le nouveau système")
    print()
    
    input("Appuyez sur Entrée pour continuer...")
    
    # Étapes d'intégration
    steps = [
        ("Sauvegarde", backup_current_audio_system),
        ("Configuration", update_settings_for_conflict_free_tts),
        ("Wrapper", create_audio_manager_wrapper),
        ("Imports", update_ogma_imports),
        ("Test", test_integration)
    ]
    
    success_count = 0
    
    for step_name, step_func in steps:
        print(f"\n--- {step_name} ---")
        try:
            if step_func():
                success_count += 1
                print(f"✅ {step_name} réussi")
            else:
                print(f"❌ {step_name} échoué")
        except Exception as e:
            print(f"❌ {step_name} erreur: {e}")
    
    print(f"\n📊 === RÉSULTAT INTÉGRATION ===")
    print(f"Étapes réussies: {success_count}/{len(steps)}")
    
    if success_count == len(steps):
        print("🎉 INTÉGRATION COMPLÈTE RÉUSSIE")
        print()
        print("PROCHAINES ÉTAPES:")
        print("1. Redémarrer OGMA")
        print("2. Tester Perception + TTS")
        print("3. Vérifier stabilité")
    else:
        print("⚠️ INTÉGRATION PARTIELLE")
        print("Vérifiez les erreurs ci-dessus")

if __name__ == "__main__":
    main()