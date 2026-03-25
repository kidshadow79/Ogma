"""
Mise à jour des instructions introspection avec capacité web
"""
import json

# Charger le fichier
filepath = r'c:\IA\OGMA\data\introspection_settings_v2.json'
with open(filepath, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Backup
import shutil
shutil.copy(filepath, filepath + '.backup')
print(f"✅ Backup créé: {filepath}.backup")

# Modifier step2_conscious - Ajouter section web
old_conscious = data['instructions']['step2_conscious']['instruction']

# Trouver la section GESTION DES IMPASSES et modifier
lines = old_conscious.split('\n')
new_lines = []
for i, line in enumerate(lines):
    new_lines.append(line)
    # Après "Si Mémoire échoue", ajouter le web
    if 'Si Mémoire échoue' in line and 'LANCE WEB' not in line:
        indent = len(line) - len(line.lstrip())
        new_lines[-1] = ' ' * indent + '- Si Mémoire échoue -> LANCE WEB: "il faut que je cherche sur internet : [sujet]"'
        # Décaler le suivant
        if i + 1 < len(lines) and 'Si Web échoue' in lines[i + 1]:
            new_lines.append(lines[i + 1])
            continue

# Ajouter section WEB à la fin
if '>>> RECHERCHE WEB ACTIVÉE <<<' not in old_conscious:
    web_section = '''

>>> RECHERCHE WEB ACTIVÉE <<<
SYNTAXE: "il faut que je cherche sur internet : [requête précise]"
EFFET: Recherche réelle exécutée -> Résultats injectés automatiquement.
USAGE: Uniquement si mémoire vide/insuffisante sur le sujet.'''
    new_conscious = '\n'.join(new_lines) + web_section
else:
    new_conscious = old_conscious

data['instructions']['step2_conscious']['instruction'] = new_conscious

# Modifier step2_unconscious - Suggestion web
old_unconscious = data['instructions']['step2_unconscious']['instruction']
if 'LUNA_PEUT_WEB' not in old_unconscious:
    # Ajouter après [ACTION_REQUISE]
    new_unconscious = old_unconscious.replace(
        'Ex: SCAN_WEB sur "Psychologie peur".',
        'Ex: SCAN_WEB sur "Psychologie peur".\n   - Ou suggère: LUNA_PEUT_WEB "[sujet]" si besoin données externes.'
    )
    data['instructions']['step2_unconscious']['instruction'] = new_unconscious

# Sauvegarder
with open(filepath, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print('✅ Instructions mises à jour avec capacité web')
print(f'  step2_conscious: {len(data["instructions"]["step2_conscious"]["instruction"])} chars')
print(f'  step2_unconscious: {len(data["instructions"]["step2_unconscious"]["instruction"])} chars')
print('\n✨ Modifications appliquées:')
print('  - Luna peut lancer: "il faut que je cherche sur internet : [sujet]"')
print('  - Archiviste peut suggérer la recherche web')
print('  - Section RECHERCHE WEB ACTIVÉE ajoutée')
