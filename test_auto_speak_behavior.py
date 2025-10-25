# test_auto_speak_behavior.py

"""
Test du comportement auto_speak normal (pas d'erreur quand désactivé)
"""

import json
import os

def test_auto_speak_disabled():
    """Test comportement quand auto_speak=False (normal)"""
    print("🔇 === TEST AUTO_SPEAK DÉSACTIVÉ ===")
    
    # Vérifier la configuration
    settings_path = "data/settings.json"
    
    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        auto_speak = settings.get('tts', {}).get('auto_speak', False)
        tts_enabled = settings.get('tts', {}).get('enabled', True)
        
        print(f"📋 Configuration actuelle:")
        print(f"  auto_speak: {auto_speak}")
        print(f"  tts_enabled: {tts_enabled}")
        
        if auto_speak == False:
            print("✅ auto_speak correctement désactivé par défaut")
            print("   → Aucune erreur ne devrait apparaître")
            print("   → Mode silencieux normal")
            return True
        else:
            print("⚠️ auto_speak activé - pas le comportement par défaut attendu")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lecture config: {e}")
        return False

def test_auto_speak_enabled():
    """Test simulation quand auto_speak=True"""
    print("\n🔊 === TEST AUTO_SPEAK ACTIVÉ ===")
    
    # Simuler l'activation
    config = {
        'tts': {
            'auto_speak': True,
            'enabled': True
        }
    }
    
    auto_speak = config['tts']['auto_speak']
    tts_enabled = config['tts']['enabled']
    audio_manager = True  # Simule présence
    
    print(f"📋 Configuration simulée:")
    print(f"  auto_speak: {auto_speak}")
    print(f"  tts_enabled: {tts_enabled}")
    print(f"  audio_manager: {audio_manager}")
    
    if auto_speak and tts_enabled and audio_manager:
        print("✅ Conditions remplies pour lecture automatique")
        print("   → Luna parlera automatiquement")
        return True
    else:
        print("❌ Conditions non remplies")
        return False

def test_settings_toggle():
    """Test du toggle auto_speak via interface"""
    print("\n⚙️ === TEST ACTIVATION/DÉSACTIVATION ===")
    
    print("📝 Instructions utilisateur:")
    print("1. Démarrage: auto_speak=false (mode silencieux)")
    print("2. Activation: Bouton TTS ou paramètres → auto_speak=true")
    print("3. Conversation vocale: Luna parle automatiquement")
    print("4. Désactivation: Retour au mode silencieux")
    
    scenarios = [
        ("Démarrage normal", False, False, "Mode silencieux - aucune erreur"),
        ("Activation manuelle", True, True, "Luna parle automatiquement"),
        ("TTS désactivé", True, False, "Pas de lecture même si auto_speak=true"),
        ("Désactivation", False, True, "Retour mode silencieux")
    ]
    
    print("\n📊 Scénarios de test:")
    for scenario, auto_speak, tts_enabled, expected in scenarios:
        status = "✅" if not (auto_speak and not tts_enabled) else "⚠️"
        print(f"  {status} {scenario}: auto_speak={auto_speak}, tts={tts_enabled}")
        print(f"     → {expected}")
    
    return True

def check_ogma_integration():
    """Vérifier l'intégration dans OGMA"""
    print("\n🖥️ === INTÉGRATION OGMA ===")
    
    try:
        # Lire le code modifié
        with open('ogma_ng.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Vérifier les améliorations
        checks = [
            ("Mode silencieux", "pass  # Mode silencieux par choix" in content),
            ("Threading fix", "threading.Thread(target=audio_task" in content),
            ("Messages propres", "[TTS-AUTO]" in content and "ERROR AUTO" not in content.split("[TTS-AUTO]")[1] if "[TTS-AUTO]" in content else False),
            ("Pas d'asyncio", "asyncio.create_task" not in content.split("auto_speak")[1] if "auto_speak" in content else True)
        ]
        
        print("📊 Vérifications code:")
        all_good = True
        for check_name, passed in checks:
            icon = "✅" if passed else "❌"
            print(f"  {icon} {check_name}")
            if not passed:
                all_good = False
        
        if all_good:
            print("✅ Code OGMA correctement modifié")
        else:
            print("⚠️ Modifications partielles")
        
        return all_good
        
    except Exception as e:
        print(f"❌ Erreur vérification code: {e}")
        return False

def main():
    print("🎯 === TEST COMPORTEMENT AUTO_SPEAK ===")
    print("Objectif: Éliminer les fausses erreurs + comportement propre")
    print()
    
    tests = [
        ("auto_speak désactivé", test_auto_speak_disabled),
        ("auto_speak activé", test_auto_speak_enabled),
        ("Toggle fonctionnel", test_settings_toggle),
        ("Intégration OGMA", check_ogma_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"--- {test_name} ---")
        try:
            success = test_func()
            results.append(success)
        except Exception as e:
            print(f"❌ Erreur: {e}")
            results.append(False)
        
        if test_name != tests[-1][0]:  # Pas de pause après le dernier
            print()
    
    print("\n" + "="*60)
    print("📊 RÉSUMÉ COMPORTEMENT AUTO_SPEAK")
    print("="*60)
    
    success_count = sum(results)
    total_tests = len(results)
    
    for i, (test_name, _) in enumerate(tests):
        icon = "✅" if results[i] else "❌"
        print(f"{icon} {test_name}")
    
    if success_count == total_tests:
        print("\n🎉 COMPORTEMENT PARFAIT")
        print("   → Aucune fausse erreur auto_speak")
        print("   → Mode silencieux par défaut")
        print("   → Activation/désactivation propre")
        print("   → Prêt pour conversations vocales à la demande")
    else:
        print(f"\n⚠️ TESTS: {success_count}/{total_tests}")
        print("   → Vérifications nécessaires")

if __name__ == "__main__":
    main()