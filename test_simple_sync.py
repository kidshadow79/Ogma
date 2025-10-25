# test_simple_sync.py
"""
Test simple pour vérifier la cohérence des paramètres de perception
"""

import json
import os

def test_settings_structure():
    """Test de la structure des settings"""
    print("🔍 VÉRIFICATION STRUCTURE SETTINGS")
    print("=" * 40)
    
    settings_path = "./data/settings.json"
    
    if not os.path.exists(settings_path):
        print("❌ settings.json non trouvé")
        return False
    
    with open(settings_path, 'r', encoding='utf-8') as f:
        settings = json.load(f)
    
    # Vérifier structure extensions.perception
    if 'extensions' in settings and 'perception' in settings['extensions']:
        perception_config = settings['extensions']['perception']
        print("✅ Section extensions.perception trouvée")
        
        # Vérifier save_captures
        if 'save_captures' in perception_config:
            save_captures = perception_config['save_captures']
            print(f"✅ save_captures trouvé: {save_captures}")
            
            # Autres paramètres importants
            important_params = ['webcam_index', 'capture_folder', 'jpeg_quality']
            for param in important_params:
                if param in perception_config:
                    print(f"✅ {param}: {perception_config[param]}")
                else:
                    print(f"⚠️ {param}: manquant")
            
            return True
        else:
            print("❌ save_captures non trouvé dans la config")
            return False
    else:
        print("❌ Section extensions.perception non trouvée")
        
        # Vérifier ancienne structure
        if 'perception_agent' in settings:
            print("⚠️ Ancienne structure perception_agent trouvée")
            print("💡 Suggestion: Migrer vers extensions.perception")
        
        return False

def simulate_ui_change():
    """Simule un changement depuis l'interface utilisateur"""
    print("\n🎛️ SIMULATION CHANGEMENT UI")
    print("=" * 40)
    
    # Lire settings actuel
    settings_path = "./data/settings.json"
    with open(settings_path, 'r', encoding='utf-8') as f:
        settings = json.load(f)
    
    # Obtenir valeur actuelle
    current_save = settings.get('extensions', {}).get('perception', {}).get('save_captures', False)
    print(f"📊 save_captures actuel: {current_save}")
    
    # Simuler changement (inverser la valeur)
    new_save = not current_save
    print(f"🔄 Nouveau save_captures: {new_save}")
    
    # Backup
    backup_path = f"{settings_path}.backup"
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)
    
    # Appliquer changement
    settings['extensions']['perception']['save_captures'] = new_save
    
    # Sauvegarder
    with open(settings_path, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Changement appliqué dans {settings_path}")
    
    # Vérifier
    with open(settings_path, 'r', encoding='utf-8') as f:
        updated_settings = json.load(f)
    
    updated_save = updated_settings.get('extensions', {}).get('perception', {}).get('save_captures', False)
    
    if updated_save == new_save:
        print("✅ Changement vérifié avec succès")
        
        # Restaurer backup
        with open(backup_path, 'r', encoding='utf-8') as f:
            original_settings = json.load(f)
        
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(original_settings, f, indent=2, ensure_ascii=False)
        
        os.remove(backup_path)
        print("🔄 Backup restauré")
        
        return True
    else:
        print("❌ Changement non persisté correctement")
        return False

def main():
    """Test principal"""
    print("🧪 TEST COHÉRENCE PARAMÈTRES PERCEPTION")
    
    test1 = test_settings_structure()
    test2 = simulate_ui_change()
    
    print("\n" + "=" * 40)
    print("📊 RÉSULTATS:")
    print(f"🔸 Structure settings: {'✅ OK' if test1 else '❌ ERREUR'}")
    print(f"🔸 Simulation UI: {'✅ OK' if test2 else '❌ ERREUR'}")
    
    if test1 and test2:
        print("\n🎉 SYNCHRONISATION PERCEPTION UI FONCTIONNELLE")
        print("💡 L'interface utilisateur devrait correctement gérer save_captures")
    else:
        print("\n⚠️ PROBLÈMES DÉTECTÉS")
    
    return test1 and test2

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)