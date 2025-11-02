"""
Retirer l'instruction inutile ajoutée par erreur
"""
import json

# Charger settings.json
with open('data/settings.json', 'r', encoding='utf-8') as f:
    settings = json.load(f)

instructions = settings['prompts']['instructions']

# Texte à retirer
old_instruction = """-   **Génération d'Image :** `je dois créer une image de : [description détaillée de l'image]`
    ⚠️ RÈGLE CRITIQUE : Tu DOIS prononcer cette phrase magique EXACTE à CHAQUE demande d'image (y compris quand on te demande de "recommencer", "refaire", "régénérer"). Sans cette phrase, AUCUNE image ne sera créée - tu ne dois JAMAIS simuler une génération avec du texte HTML.

-   **Introspection Active :**"""

# Texte correct original
new_instruction = """-   **Génération d'Image :** `je dois créer une image de : [description détaillée de l'image]`

-   **Introspection Active :**"""

if old_instruction in instructions:
    instructions = instructions.replace(old_instruction, new_instruction)
    settings['prompts']['instructions'] = instructions
    
    with open('data/settings.json', 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)
    
    print("✅ Instruction erronée retirée avec succès")
else:
    print("⚠️ Instruction non trouvée - peut-être déjà retirée?")
