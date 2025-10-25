# test_auto_speak_fix.py

"""
Test de la correction auto_speak dans les settings
"""

import json
import os

def check_settings():
    """Vérifier les settings TTS"""
    print("🔍 === DIAGNOSTIC SETTINGS TTS ===")
    
    settings_path = "data/settings.json"
    
    if not os.path.exists(settings_path):
        print("❌ Fichier settings.json introuvable")
        return False
    
    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        print("📋 Configuration TTS actuelle:")
        
        # Section tts principale
        tts_section = settings.get('tts', {})
        print(f"  tts.enabled: {tts_section.get('enabled', False)}")
        print(f"  tts.auto_speak: {tts_section.get('auto_speak', False)}")
        print(f"  tts.engine: {tts_section.get('engine', 'non défini')}")
        
        # Section audio
        audio_section = settings.get('audio', {})
        print(f"  audio.tts_enabled: {audio_section.get('tts_enabled', False)}")
        
        # Section conflict_free
        conflict_free = settings.get('tts_conflict_free', {})
        print(f"  tts_conflict_free.enabled: {conflict_free.get('enabled', False)}")
        
        # Analyser les conflits potentiels
        print("\n🔍 ANALYSE CONFLITS:")
        
        tts_enabled = tts_section.get('enabled', False)
        auto_speak = tts_section.get('auto_speak', False)
        audio_tts = audio_section.get('tts_enabled', False)
        
        if not tts_enabled:
            print("⚠️  tts.enabled=false - TTS principal désactivé")
        
        if not auto_speak:
            print("⚠️  tts.auto_speak=false - Lecture auto désactivée")
        
        if not audio_tts:
            print("⚠️  audio.tts_enabled=false - Audio TTS désactivé")
        
        if tts_enabled and auto_speak:
            print("✅ Configuration TTS correcte pour auto_speak")
            return True
        else:
            print("❌ Configuration TTS incorrecte")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lecture settings: {e}")
        return False

def simulate_ogma_check():
    """Simuler la vérification OGMA"""
    print("\n🖥️ === SIMULATION VÉRIFICATION OGMA ===")
    
    try:
        # Simuler la logique d'OGMA
        from core_logic import ensure_settings_manager
        
        sm = ensure_settings_manager()
        if not sm:
            print("❌ SettingsManager non disponible")
            return False
        
        auto_speak = sm.settings.get('tts', {}).get('auto_speak', False)
        tts_enabled = sm.settings.get('tts', {}).get('enabled', True)
        
        print(f"📊 Valeurs OGMA:")
        print(f"  auto_speak: {auto_speak}")
        print(f"  tts_enabled: {tts_enabled}")
        
        if auto_speak and tts_enabled:
            print("✅ OGMA détectera auto_speak=True")
            return True
        else:
            print("❌ OGMA détectera auto_speak=False")
            print(f"   → Conditions: auto_speak={auto_speak}, tts_enabled={tts_enabled}")
            return False
            
    except Exception as e:
        print(f"⚠️ Erreur simulation OGMA: {e}")
        return False

def main():
    print("🎯 === TEST CORRECTION AUTO_SPEAK ===")
    print("Objectif: Éliminer l'erreur TTS-DEBUG ERROR AUTO")
    print()
    
    # Vérifications
    settings_ok = check_settings()
    ogma_ok = simulate_ogma_check()
    
    print("\n" + "="*50)
    print("📊 RÉSUMÉ DIAGNOSTIC")
    print("="*50)
    
    if settings_ok:
        print("✅ Fichier settings.json configuré correctement")
    else:
        print("❌ Problème dans settings.json")
    
    if ogma_ok:
        print("✅ OGMA détectera auto_speak=True")
    else:
        print("❌ OGMA continuera à voir auto_speak=False")
    
    if settings_ok and ogma_ok:
        print("\n🎉 CORRECTION RÉUSSIE")
        print("   → L'erreur TTS-DEBUG ne devrait plus apparaître")
        print("   → Luna parlera automatiquement")
    else:
        print("\n⚠️ CORRECTION PARTIELLE")
        print("   → Vérifier la configuration TTS dans OGMA")

if __name__ == "__main__":
    main()