"""
Fix Image Generation Instructions
----------------------------------
Ajoute un rappel explicite dans les instructions système pour que Luna
prononce TOUJOURS la phrase magique lors des demandes d'images répétées.
"""

import json
from pathlib import Path

# Charger settings.json
settings_path = Path("data/settings.json")
with open(settings_path, 'r', encoding='utf-8') as f:
    settings = json.load(f)

# Récupérer les instructions actuelles
instructions = settings['prompts']['instructions']

# Rechercher et remplacer la section génération d'image
old_text = "-   **Génération d'Image :** `je dois créer une image de : [description détaillée de l'image]`\n\n-   **Introspection Active :**"

new_text = """-   **Génération d'Image :** `je dois créer une image de : [description détaillée de l'image]`
    ⚠️ RÈGLE CRITIQUE : Tu DOIS prononcer cette phrase magique EXACTE à CHAQUE demande d'image (y compris quand on te demande de "recommencer", "refaire", "régénérer"). Sans cette phrase, AUCUNE image ne sera créée - tu ne dois JAMAIS simuler une génération avec du texte HTML.

-   **Introspection Active :**"""

if old_text in instructions:
    instructions = instructions.replace(old_text, new_text)
    settings['prompts']['instructions'] = instructions
    
    # Sauvegarder
    with open(settings_path, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)
    
    print("✅ Instructions mises à jour avec succès!")
    print("\n📝 Nouvelle règle ajoutée:")
    print("   Luna doit prononcer 'je dois créer une image de :' à CHAQUE demande")
    print("   (y compris les demandes répétées comme 'recommence', 'refais', etc.)")
else:
    print("❌ Texte à remplacer non trouvé")
    print("\nRecherché:")
    print(repr(old_text))
    print("\nDans les instructions (extrait):")
    # Chercher manuellement
    if "Génération d'Image" in instructions:
        start = instructions.find("Génération d'Image")
        print(repr(instructions[start:start+300]))
    else:
        print("Section 'Génération d'Image' introuvable")
