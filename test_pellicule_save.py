# test_pellicule_save.py
"""
Test spécifique de la sauvegarde des pellicules motion
Vérifie qu'elles sont toujours sauvées même si save_captures = false
"""

import os
import sys
import cv2
import numpy as np
from datetime import datetime

def create_test_config():
    """Configuration de test avec save_captures = False"""
    return {
        "webcam_index": 0,
        "motion_buffer_size": 3,
        "triage_resolution": [640, 480],
        "save_captures": False,  # ❗ DÉSACTIVÉ mais pellicules doivent être sauvées
        "capture_folder": "./captures",
        "capture_format": "JPEG",
        "jpeg_quality": 85
    }

def create_mock_composite():
    """Crée une image composite simulée"""
    # Image de test 1920x1080 (3x2 layout de 640x360 chacune)
    composite = np.zeros((1080, 1920, 3), dtype=np.uint8)
    
    # Ajouter du contenu visuel
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255), (0, 255, 255)]
    
    for i, color in enumerate(colors):
        row = i // 3
        col = i % 3
        x_start = col * 640
        y_start = row * 360
        
        # Rectangle coloré
        cv2.rectangle(composite, (x_start, y_start), (x_start + 640, y_start + 360), color, -1)
        
        # Texte
        text = f"Frame {i+1}"
        cv2.putText(composite, text, (x_start + 250, y_start + 180), 
                   cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 255), 3)
    
    return composite

def test_pellicule_save():
    """Test principal de sauvegarde pellicule"""
    print("🎬 TEST SAUVEGARDE PELLICULES MOTION")
    print("=" * 50)
    
    try:
        # Import agent
        sys.path.append('./extensions')
        from perception_agent import PerceptionAgent
        
        # Configuration avec save_captures = False
        config = create_test_config()
        print(f"📋 Configuration: save_captures = {config['save_captures']}")
        
        # Créer agent
        agent = PerceptionAgent(config)
        print("✅ Agent créé")
        
        # Compter fichiers avant
        captures_folder = "./captures"
        before_count = 0
        if os.path.exists(captures_folder):
            before_files = [f for f in os.listdir(captures_folder) if f.startswith('pellicule_')]
            before_count = len(before_files)
        
        print(f"📊 Pellicules avant test: {before_count}")
        
        # Créer image composite mock
        composite = create_mock_composite()
        print("🖼️ Image composite créée (1920x1080)")
        
        # TEST 1: Capture simple (ne doit PAS être sauvée)
        result_simple = agent._save_image_if_enabled(composite, "photo_simple")
        print(f"📸 Capture simple: {'sauvée' if result_simple else 'ignorée (normal)'}")
        
        # TEST 2: Pellicule motion (DOIT être sauvée malgré save_captures = False)
        result_pellicule = agent._save_image_if_enabled(composite, "pellicule_motion")
        print(f"🎬 Pellicule motion: {'sauvée' if result_pellicule else 'ERREUR - non sauvée!'}")
        
        # Vérifier fichiers après
        after_count = 0
        pellicule_files = []
        if os.path.exists(captures_folder):
            after_files = [f for f in os.listdir(captures_folder) if f.startswith('pellicule_')]
            after_count = len(after_files)
            pellicule_files = sorted(after_files)[-3:]  # 3 plus récentes
        
        print(f"📊 Pellicules après test: {after_count}")
        
        # Résultats
        pellicules_added = after_count - before_count
        print(f"📈 Nouvelles pellicules: {pellicules_added}")
        
        if pellicules_added >= 1:
            print("✅ SUCCESS: Pellicule motion sauvée malgré save_captures = False")
            if pellicule_files:
                print(f"📁 Fichier créé: {pellicule_files[-1]}")
                
                # Vérifier taille fichier
                filepath = os.path.join(captures_folder, pellicule_files[-1])
                size_kb = os.path.getsize(filepath) / 1024
                print(f"📏 Taille: {size_kb:.1f} KB")
        else:
            print("❌ ÉCHEC: Pellicule motion non sauvée")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Test principal"""
    print("🚀 Démarrage test sauvegarde pellicules...")
    
    success = test_pellicule_save()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 TEST RÉUSSI")
        print("💡 Les pellicules motion seront maintenant toujours sauvées!")
    else:
        print("❌ TEST ÉCHOUÉ")
        print("⚠️ Problème avec la sauvegarde des pellicules")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)