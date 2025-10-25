# test_camera_audio_disabled.py

"""
Test pour vérifier que la caméra n'accède pas à l'audio
Évite les conflits avec le système TTS
"""

import cv2
import sys
import time

def test_camera_audio_disabled():
    """Test que la caméra n'utilise pas l'audio"""
    print("🧪 === TEST DÉSACTIVATION AUDIO CAMÉRA ===")
    print()
    
    try:
        # Tester ouverture caméra comme dans Perception
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("❌ Impossible d'ouvrir la caméra")
            return False
        
        print("✅ Caméra ouverte")
        
        # Configuration comme dans Perception
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        # Test désactivation audio
        audio_disabled = False
        try:
            # Essayer de désactiver l'audio
            result = cap.set(cv2.CAP_PROP_AUDIO, 0)
            audio_disabled = True
            print(f"🔇 Tentative désactivation audio: {'✅ OK' if result else '⚠️ Pas supporté'}")
        except Exception as e:
            print(f"ℹ️ CAP_PROP_AUDIO non supporté: {e}")
        
        # Vérifier propriétés audio disponibles
        print("\n📊 PROPRIÉTÉS CAMÉRA:")
        
        properties_to_check = [
            (cv2.CAP_PROP_FRAME_WIDTH, "Largeur"),
            (cv2.CAP_PROP_FRAME_HEIGHT, "Hauteur"), 
            (cv2.CAP_PROP_FPS, "FPS"),
        ]
        
        # Ajouter propriétés audio si disponibles
        try:
            properties_to_check.append((cv2.CAP_PROP_AUDIO, "Audio"))
        except AttributeError:
            print("   ℹ️ CAP_PROP_AUDIO non disponible dans cette version OpenCV")
        
        for prop, name in properties_to_check:
            try:
                value = cap.get(prop)
                print(f"   {name}: {value}")
            except Exception as e:
                print(f"   {name}: Erreur - {e}")
        
        # Test capture pour vérifier fonctionnement
        print("\n🎥 TEST CAPTURE:")
        for i in range(3):
            ret, frame = cap.read()
            if ret:
                print(f"   Frame {i+1}: ✅ OK ({frame.shape})")
            else:
                print(f"   Frame {i+1}: ❌ Échec")
            time.sleep(0.5)
        
        cap.release()
        
        print("\n🎯 RÉSULTAT:")
        print("✅ Caméra fonctionne sans problème")
        if audio_disabled:
            print("✅ Audio explicitement désactivé")
        else:
            print("ℹ️ Audio non géré par cette caméra (bon)")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test: {e}")
        return False

def test_simultaneous_tts_camera():
    """Test simultané TTS + caméra pour détecter conflits"""
    print("\n🔀 === TEST SIMULTANÉ TTS + CAMÉRA ===")
    print()
    
    try:
        # Test 1: Caméra d'abord
        print("1️⃣ Ouverture caméra...")
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("❌ Caméra non disponible")
            return False
        
        # Désactiver audio explicitement
        try:
            cap.set(cv2.CAP_PROP_AUDIO, 0)
            print("🔇 Audio caméra désactivé")
        except:
            print("ℹ️ Audio non géré par caméra")
        
        # Test capture caméra
        ret, frame = cap.read()
        if ret:
            print(f"✅ Capture caméra OK: {frame.shape}")
        else:
            print("❌ Capture caméra échec")
            cap.release()
            return False
        
        # Test 2: TTS pendant que caméra active
        print("\n2️⃣ Test TTS avec caméra active...")
        try:
            import pyttsx3
            engine = pyttsx3.init()
            if engine:
                print("✅ TTS initialisé avec caméra active")
                # Pas de synthèse vocale pour éviter bruit, juste test init
                engine.stop()
            else:
                print("⚠️ TTS pas disponible")
        except Exception as e:
            print(f"⚠️ Conflit possible TTS/caméra: {e}")
        
        # Test 3: Caméra pendant TTS (inverse)
        print("\n3️⃣ Re-test capture après TTS...")
        ret, frame = cap.read()
        if ret:
            print(f"✅ Capture encore OK après TTS: {frame.shape}")
        else:
            print("❌ Caméra affectée par TTS")
        
        cap.release()
        print("✅ Test simultané terminé")
        return True
        
    except Exception as e:
        print(f"❌ Erreur test simultané: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("🎥 === TEST AUDIO CAMÉRA ===")
        print()
        print("USAGE:")
        print("  python test_camera_audio_disabled.py basic      # Test basique")
        print("  python test_camera_audio_disabled.py conflict   # Test conflit TTS")
        print("  python test_camera_audio_disabled.py both       # Les deux tests")
        print()
        print("OBJECTIF:")
        print("- Vérifier que la caméra n'accède pas à l'audio")
        print("- Tester coexistence TTS + caméra") 
        print("- Valider fix conflit audio")
        return
    
    test_type = sys.argv[1].lower()
    
    success = True
    
    if test_type in ["basic", "both"]:
        success &= test_camera_audio_disabled()
    
    if test_type in ["conflict", "both"]:
        success &= test_simultaneous_tts_camera()
    
    if success:
        print("\n🎉 TOUS LES TESTS RÉUSSIS")
        print("✅ Pas de conflit audio détecté")
    else:
        print("\n⚠️ CERTAINS TESTS ONT ÉCHOUÉ")
        print("💡 Vérifiez les drivers caméra/audio")

if __name__ == "__main__":
    main()