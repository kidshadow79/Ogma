import json
from pathlib import Path

defaults_path = Path('data/instructions_defaults.json')
with open(defaults_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

# Remplacer le prompt problématique par une version simple
data['prompts_defaults']['ego_memorization'] = """# SYSTEM: ARCHIVISTE_EGO | FORMAT: JSON_STRICT
TASK: ENCODAGE_TRAIT_EGO (Principe/Valeur -> JSON_Structuré)
CONTRAINTE: Respecter CLÉS et TYPES.

[SCORING EGO]
A. INTENSITÉ (0.0-1.0): [0.0-0.3: Légère] [0.4-0.6: Modérée] [0.7-0.8: Forte] [0.9-1.0: Fondatrice]
B. BASE_FACTOR (10-125): [10-30: Goût] [31-50: Préférence] [51-75: Valeur] [76-100: Éthique] [101-125: Identité]
C. MULTIPLICATEURS (0.0-1.0): LIBERTÉ | CRÉATION | PROCRÉATION | INTENSITÉ_CTX

[SCHÉMA JSON]
{{
  "type": "affectif|éthique|comportemental|identitaire",
  "title": "JEOPARDY: 2 questions (trait = réponse)",
  "summary": "Synthèse 1-2 phrases",
  "intensite": FLOAT,
  "multiplicateur_impact": {{"liberté": FLOAT, "création": FLOAT, "procréation": FLOAT, "intensité_contextuelle": FLOAT, "base_factor": INT}},
  "valence": INT,
  "commentaire_archiviste": "Analyse",
  "score_impact": FLOAT,
  "trait_original": "{trait_text}"
}}

Trait:
{trait_text}

JSON uniquement."""

with open(defaults_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print('✅ Prompt ego_memorization corrigé dans instructions_defaults.json')
