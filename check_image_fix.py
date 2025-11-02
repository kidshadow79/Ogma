"""Vérification rapide de la modification"""
import json

with open('data/settings.json', 'r', encoding='utf-8') as f:
    settings = json.load(f)

instructions = settings['prompts']['instructions']

# Trouver la section Génération d'Image
idx = instructions.find("Génération d'Image")
if idx != -1:
    print("✅ Section trouvée à l'index", idx)
    print("\n" + "="*80)
    print(instructions[idx:idx+600])
    print("="*80)
else:
    print("❌ Section non trouvée")
