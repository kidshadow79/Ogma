#!/usr/bin/env python3
"""
Test rapide de l'injection des instructions de perception
"""

import json
from pathlib import Path

def test_perception_instructions():
    """Vérifie que les instructions de perception sont présentes dans settings.json"""
    
    print("🔍 Test de présence des instructions de perception...")
    
    # Charger settings.json
    settings_path = Path("data/settings.json")
    if not settings_path.exists():
        print("❌ Fichier data/settings.json non trouvé")
        return False
    
    try:
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        # Vérifier la structure
        if 'prompts' not in settings:
            print("❌ Section 'prompts' non trouvée dans settings")
            return False
            
        if 'perception' not in settings['prompts']:
            print("❌ Instructions 'perception' non trouvées dans prompts")
            return False
        
        perception_instructions = settings['prompts']['perception']
        
        if not perception_instructions or not perception_instructions.strip():
            print("❌ Instructions de perception vides")
            return False
        
        print(f"✅ Instructions de perception trouvées : {len(perception_instructions)} caractères")
        print(f"📋 Aperçu: {perception_instructions[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la lecture des settings: {e}")
        return False

def simulate_injection_logic():
    """Simule la logique d'injection des instructions de perception"""
    
    print("\n🧪 Test de la logique d'injection...")
    
    # Simuler différents scénarios
    scenarios = [
        {"perception_image_data": None, "_active_file_data": None, "expected": False},
        {"perception_image_data": {"type": "image_url"}, "_active_file_data": None, "expected": True},
        {"perception_image_data": None, "_active_file_data": {"type": "image"}, "expected": True},
        {"perception_image_data": {"type": "image_url"}, "_active_file_data": {"type": "image"}, "expected": True},
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        perception_image_data = scenario["perception_image_data"]
        _active_file_data = scenario["_active_file_data"]
        expected = scenario["expected"]
        
        # Logique copiée de ogma_ng.py
        has_image = (perception_image_data is not None or 
                    (_active_file_data and _active_file_data.get('type') == 'image'))
        has_image = bool(has_image)  # Convertir en booléen explicite
        
        result = "✅" if has_image == expected else "❌"
        print(f"  {result} Scénario {i}: has_image={has_image}, attendu={expected}")
        
        if has_image != expected:
            print(f"    Détails: perception_data={perception_image_data}, file_data={_active_file_data}")
            return False
    
    print("✅ Logique d'injection validée")
    return True

if __name__ == "__main__":
    print("🧪 Test des instructions de perception d'OGMA\n")
    
    success = True
    
    success &= test_perception_instructions()
    success &= simulate_injection_logic()
    
    print(f"\n🎯 Résultat global: {'✅ SUCCÈS' if success else '❌ ÉCHEC'}")