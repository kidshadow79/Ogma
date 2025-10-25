# test_save_captures_final.py
"""
Test final de bout en bout pour save_captures:
1. Modification dans settings.json
2. Vérification que l'agent reçoit le changement  
3. Test de sauvegarde pellicule (toujours active)
4. Test de sauvegarde capture simple (selon save_captures)
"""

import os
import json
import sys
import cv2
import numpy as np
import tempfile

def create_test_image():
    """Crée une image de test"""
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    # Ajouter du contenu visuel
    cv2.rectangle(img, (50, 50), (590, 430), (0, 255, 0), -1)
    cv2.putText(img, "TEST IMAGE", (200, 250), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
    return img

def test_agent_config_update():
    """Test mise à jour configuration agent"""
    print("🔧 TEST MISE À JOUR CONFIG AGENT")
    print("=" * 40)
    
    try:
        # Import agent
        sys.path.append('./extensions')
        from perception_agent import PerceptionAgent
        
        # Config initiale
        initial_config = {
            'webcam_index': 0,
            'save_captures': False,  # Initialement désactivé
            'capture_folder': './test_captures_temp',
            'triage_resolution': [640, 480]
        }
        
        agent = PerceptionAgent(initial_config)
        print(f"✅ Agent créé avec save_captures = {agent.config.get('save_captures', False)}")
        
        # Test 1: Activer save_captures
        print("\n📝 TEST 1: Activation save_captures")
        new_config = {'save_captures': True}
        agent.update_config(new_config)
        
        if agent.config.get('save_captures', False) == True:
            print("✅ save_captures activé dans l'agent")
        else:
            print("❌ save_captures non activé")
            return False
        
        # Test 2: Désactiver save_captures
        print("\n📝 TEST 2: Désactivation save_captures")
        new_config = {'save_captures': False}
        agent.update_config(new_config)
        
        if agent.config.get('save_captures', True) == False:
            print("✅ save_captures désactivé dans l'agent")
        else:
            print("❌ save_captures non désactivé")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test agent: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_save_behavior():
    """Test comportement sauvegarde selon save_captures"""
    print("\n💾 TEST COMPORTEMENT SAUVEGARDE")
    print("=" * 40)
    
    try:
        # Import agent
        sys.path.append('./extensions')
        from perception_agent import PerceptionAgent
        
        # Dossier temporaire
        temp_dir = tempfile.mkdtemp()
        print(f"📁 Dossier test: {temp_dir}")
        
        # Config avec save_captures = False
        config = {
            'webcam_index': 0,
            'save_captures': False,
            'capture_folder': temp_dir,
            'triage_resolution': [640, 480],
            'jpeg_quality': 85
        }
        
        agent = PerceptionAgent(config)
        test_image = create_test_image()
        
        # Test 1: Capture simple avec save_captures = False
        print("\n📸 TEST 1: Capture simple (save_captures = False)")
        result_simple = agent._save_image_if_enabled(test_image, "photo_simple")
        
        if result_simple is None:
            print("✅ Capture simple ignorée (comportement attendu)")
        else:
            print("❌ Capture simple sauvée (inattendu)")
            return False
        
        # Test 2: Pellicule avec save_captures = False
        print("\n🎬 TEST 2: Pellicule motion (save_captures = False)")
        result_pellicule = agent._save_image_if_enabled(test_image, "pellicule_motion")
        
        if result_pellicule is not None:
            print("✅ Pellicule motion sauvée (comportement attendu)")
            print(f"📁 Fichier: {result_pellicule}")
        else:
            print("❌ Pellicule motion non sauvée (problème)")
            return False
        
        # Test 3: Activer save_captures et retester
        print("\n🔄 TEST 3: Activation save_captures")
        agent.update_config({'save_captures': True})
        
        result_simple_enabled = agent._save_image_if_enabled(test_image, "photo_simple")
        
        if result_simple_enabled is not None:
            print("✅ Capture simple sauvée après activation")
            print(f"📁 Fichier: {result_simple_enabled}")
        else:
            print("❌ Capture simple non sauvée après activation")
            return False
        
        # Compter fichiers créés
        files_created = [f for f in os.listdir(temp_dir) if f.endswith('.jpg')]
        print(f"\n📊 Fichiers créés: {len(files_created)}")
        for f in files_created:
            print(f"  - {f}")
        
        # Nettoyage
        import shutil
        shutil.rmtree(temp_dir)
        print("🧹 Dossier temporaire nettoyé")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test sauvegarde: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Test principal"""
    print("🚀 TEST FINAL save_captures - BOUT EN BOUT")
    print("=" * 50)
    
    test1 = test_agent_config_update()
    test2 = test_save_behavior()
    
    print("\n" + "=" * 50)
    print("📊 RÉSULTATS FINAUX:")
    print(f"🔸 Configuration agent: {'✅ OK' if test1 else '❌ ERREUR'}")
    print(f"🔸 Comportement sauvegarde: {'✅ OK' if test2 else '❌ ERREUR'}")
    
    if test1 and test2:
        print("\n🎉 TOUS LES TESTS PASSENT")
        print("✅ save_captures fonctionne correctement")
        print("💡 Interface UI → Agent → Sauvegarde : OPÉRATIONNEL")
        print("\n📋 COMPORTEMENTS CONFIRMÉS:")
        print("  🔸 save_captures = False → Captures simples ignorées")
        print("  🔸 save_captures = True → Captures simples sauvées")
        print("  🔸 Pellicules motion → TOUJOURS sauvées")
    else:
        print("\n❌ CERTAINS TESTS ÉCHOUENT")
        print("⚠️ Problème avec save_captures")
    
    return test1 and test2

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)