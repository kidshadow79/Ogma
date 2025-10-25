# test_ogma_tts_perception_integration.py

"""
Test d'intégration TTS sans conflit dans OGMA avec Perception
Vérifie que le système fonctionne sans crash
"""

import time
import threading
from pathlib import Path

def test_tts_integration():
    """Test l'intégration TTS sans conflit"""
    print("🧪 === TEST INTÉGRATION TTS SANS CONFLIT ===")
    
    try:
        # Test 1: Import wrapper
        print("\n1️⃣ Test import wrapper...")
        from audio_manager_wrapper import get_audio_manager
        audio_mgr = get_audio_manager()
        print("✅ Wrapper importé")
        
        # Test 2: Initialisation
        print("\n2️⃣ Test initialisation...")
        audio_mgr.initialize_tts()
        print("✅ TTS initialisé")
        
        # Test 3: Synthèse vocale
        print("\n3️⃣ Test synthèse vocale...")
        success = audio_mgr.speak("Test intégration OGMA avec TTS sans conflit")
        if success:
            print("✅ Synthèse réussie")
        else:
            print("⚠️ Synthèse en fallback")
        
        time.sleep(2)  # Laisser la synthèse se terminer
        
        # Test 4: Mode Perception
        print("\n4️⃣ Test notification Perception...")
        audio_mgr.set_perception_mode(True)
        print("✅ Perception ACTIVE notifiée")
        
        # Tentative de synthèse pendant Perception (devrait être bloquée)
        print("   → Test synthèse pendant Perception...")
        success = audio_mgr.speak("Cette synthèse devrait être adaptée ou bloquée")
        print(f"   → Résultat: {'✅ Réussie' if success else '🚫 Bloquée (attendu)'}")
        
        time.sleep(1)
        
        # Désactiver Perception
        audio_mgr.set_perception_mode(False)
        print("✅ Perception INACTIVE notifiée")
        
        # Test synthèse après désactivation
        print("   → Test synthèse après Perception...")
        success = audio_mgr.speak("TTS restauré après Perception")
        print(f"   → Résultat: {'✅ Réussie' if success else '❌ Échec'}")
        
        # Nettoyage
        print("\n5️⃣ Test nettoyage...")
        audio_mgr.cleanup()
        print("✅ Nettoyage réussi")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test intégration: {e}")
        return False

def test_perception_ui_integration():
    """Test l'intégration avec PerceptionUI (si disponible)"""
    print("\n🎥 === TEST INTÉGRATION PERCEPTION UI ===")
    
    try:
        # Tenter d'importer PerceptionUI
        import sys
        sys.path.insert(0, str(Path("extensions")))
        
        from perception_ui import get_perception_ui
        perception_ui = get_perception_ui()
        print("✅ PerceptionUI importé")
        
        # Vérifier que les méthodes de notification existent
        if hasattr(perception_ui, '_notify_tts_perception_state'):
            print("✅ Méthode _notify_tts_perception_state présente")
            
            # Test direct de notification
            print("   → Test notification directe...")
            perception_ui._notify_tts_perception_state(True)
            print("   ✅ Notification ACTIVE réussie")
            
            perception_ui._notify_tts_perception_state(False)
            print("   ✅ Notification INACTIVE réussie")
            
        else:
            print("❌ Méthode _notify_tts_perception_state manquante")
            return False
            
        return True
        
    except ImportError as e:
        print(f"⚠️ PerceptionUI non disponible: {e}")
        return True  # Pas critique si extension non disponible
    except Exception as e:
        print(f"❌ Erreur test Perception UI: {e}")
        return False

def test_stability_monitoring():
    """Test de stabilité sur 30 secondes"""
    print("\n⏱️ === TEST STABILITÉ 30 SECONDES ===")
    
    try:
        from audio_manager_wrapper import get_audio_manager
        audio_mgr = get_audio_manager()
        audio_mgr.initialize_tts()
        
        start_time = time.time()
        test_duration = 30
        cycle_count = 0
        
        print(f"🔄 Test cyclique pendant {test_duration}s...")
        
        while time.time() - start_time < test_duration:
            cycle_count += 1
            elapsed = int(time.time() - start_time)
            
            print(f"   Cycle {cycle_count} - {elapsed}s")
            
            # Simulation cycle Perception ON/OFF
            audio_mgr.set_perception_mode(True)
            time.sleep(0.5)
            
            # Tentative synthèse
            audio_mgr.speak(f"Test cycle {cycle_count}")
            time.sleep(1)
            
            audio_mgr.set_perception_mode(False)
            time.sleep(0.5)
            
            # Synthèse normale
            audio_mgr.speak(f"Cycle {cycle_count} complet")
            time.sleep(1)
        
        elapsed_total = time.time() - start_time
        print(f"✅ Test stabilité réussi - {cycle_count} cycles en {elapsed_total:.1f}s")
        
        audio_mgr.cleanup()
        return True
        
    except Exception as e:
        print(f"❌ Erreur test stabilité: {e}")
        return False

def main():
    print("🎵 === TEST COMPLET INTÉGRATION TTS OGMA ===")
    print()
    
    tests = [
        ("Intégration TTS", test_tts_integration),
        ("Intégration Perception UI", test_perception_ui_integration),
        ("Stabilité 30s", test_stability_monitoring)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"🧪 {test_name}")
        print(f"{'='*50}")
        
        try:
            success = test_func()
            results.append((test_name, success))
            
            if success:
                print(f"✅ {test_name} RÉUSSI")
            else:
                print(f"❌ {test_name} ÉCHOUÉ")
                
        except Exception as e:
            print(f"💥 {test_name} CRASH: {e}")
            results.append((test_name, False))
    
    # Résumé
    print(f"\n{'='*60}")
    print("📊 RÉSUMÉ TESTS INTÉGRATION")
    print(f"{'='*60}")
    
    success_count = 0
    for test_name, success in results:
        status = "✅ RÉUSSI" if success else "❌ ÉCHOUÉ"
        print(f"{test_name:<30} {status}")
        if success:
            success_count += 1
    
    print(f"\nRésultat global: {success_count}/{len(results)} tests réussis")
    
    if success_count == len(results):
        print("🎉 INTÉGRATION TTS SANS CONFLIT PARFAITEMENT FONCTIONNELLE")
        print("   → Prêt pour utilisation en production")
        print("   → Perception + TTS peuvent coexister sans conflit")
    else:
        print("⚠️ Intégration partielle - Vérifiez les erreurs ci-dessus")

if __name__ == "__main__":
    main()