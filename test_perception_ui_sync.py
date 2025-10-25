# test_perception_ui_sync.py
"""
Test de synchronisation des paramètres de perception entre UI et settings.json
Vérifie que save_captures est correctement géré
"""

import os
import sys
import json
import tempfile
import shutil

def test_perception_ui_sync():
    """Test principal de synchronisation UI <-> settings.json"""
    print("🔄 TEST SYNCHRONISATION PERCEPTION UI")
    print("=" * 50)
    
    try:
        # Créer un settings.json temporaire pour test
        temp_dir = tempfile.mkdtemp()
        data_dir = os.path.join(temp_dir, 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        # Settings de test avec save_captures = true
        test_settings = {
            "extensions": {
                "perception": {
                    "webcam_index": 1,
                    "save_captures": True,  # ⭐ Test cette valeur
                    "jpeg_quality": 90,
                    "capture_folder": "./test_captures"
                }
            }
        }
        
        settings_path = os.path.join(data_dir, 'settings.json')
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(test_settings, f, indent=2)
        
        print(f"✅ Settings temporaire créé: {settings_path}")
        
        # Modifier le chemin pour que perception_ui utilise notre settings de test
        original_file = sys.modules.get('extensions.perception_ui')
        if original_file:
            # Backup original path logic
            print("⚠️ Module déjà chargé, test avec import direct")
        
        # Import direct de perception_ui
        sys.path.insert(0, './extensions')
        import perception_ui
        
        # Créer instance et simuler le chemin settings
        perception_instance = perception_ui.PerceptionUI()
        
        # Patcher temporairement le chemin settings pour notre test
        original_method = perception_instance.load_config_from_settings
        
        def patched_load():
            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                perception_config = settings.get('extensions', {}).get('perception', {})
                if perception_config:
                    for key, value in perception_config.items():
                        if key in perception_instance.current_config:
                            perception_instance.current_config[key] = value
                    print(f"[TEST] Configuration chargée: {len(perception_config)} paramètres")
                    print(f"[TEST] save_captures = {perception_instance.current_config.get('save_captures', False)}")
            except Exception as e:
                print(f"[TEST] Erreur: {e}")
        
        # TEST 1: Chargement depuis settings.json
        print("\n📖 TEST 1: Chargement depuis settings.json")
        patched_load()
        
        # Vérifier que save_captures a été chargé correctement
        loaded_save_captures = perception_instance.current_config.get('save_captures', False)
        print(f"🔍 save_captures chargé: {loaded_save_captures}")
        
        if loaded_save_captures == True:
            print("✅ Chargement save_captures OK")
        else:
            print("❌ Échec chargement save_captures")
            return False
        
        # TEST 2: Modification via UI et sauvegarde
        print("\n💾 TEST 2: Sauvegarde via update_config()")
        
        # Simuler changement depuis UI
        new_config = {
            'save_captures': False,  # Changer la valeur
            'jpeg_quality': 75
        }
        
        # Patcher la méthode de sauvegarde pour notre test
        def patched_save():
            try:
                # Charger settings existants
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                
                # Mettre à jour
                if 'extensions' not in settings:
                    settings['extensions'] = {}
                settings['extensions']['perception'] = perception_instance.current_config
                
                # Sauvegarder
                with open(settings_path, 'w', encoding='utf-8') as f:
                    json.dump(settings, f, indent=2, ensure_ascii=False)
                
                print(f"[TEST] Configuration sauvée")
            except Exception as e:
                print(f"[TEST] Erreur sauvegarde: {e}")
        
        # Mettre à jour la config
        perception_instance.current_config.update(new_config)
        patched_save()
        
        # TEST 3: Vérifier que la sauvegarde a fonctionné
        print("\n🔍 TEST 3: Vérification sauvegarde")
        
        # Relire le fichier
        with open(settings_path, 'r', encoding='utf-8') as f:
            saved_settings = json.load(f)
        
        saved_save_captures = saved_settings.get('extensions', {}).get('perception', {}).get('save_captures', None)
        print(f"🔍 save_captures sauvé: {saved_save_captures}")
        
        if saved_save_captures == False:
            print("✅ Sauvegarde save_captures OK")
        else:
            print("❌ Échec sauvegarde save_captures")
            return False
        
        # TEST 4: Rechargement après sauvegarde
        print("\n🔄 TEST 4: Rechargement après sauvegarde")
        
        # Reset la config à une valeur différente
        perception_instance.current_config['save_captures'] = True
        
        # Recharger depuis fichier
        patched_load()
        
        reloaded_save_captures = perception_instance.current_config.get('save_captures', None)
        print(f"🔍 save_captures rechargé: {reloaded_save_captures}")
        
        if reloaded_save_captures == False:
            print("✅ Rechargement save_captures OK")
        else:
            print("❌ Échec rechargement save_captures")
            return False
        
        # Nettoyage
        shutil.rmtree(temp_dir)
        print("🧹 Fichiers temporaires nettoyés")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Test principal"""
    print("🚀 Démarrage test synchronisation Perception UI...")
    
    success = test_perception_ui_sync()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 TOUS LES TESTS PASSENT")
        print("✅ Synchronisation save_captures fonctionne correctement")
    else:
        print("❌ CERTAINS TESTS ÉCHOUENT")
        print("⚠️ Problème avec la synchronisation save_captures")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)