"""
Test extension file_writer en contexte OGMA réel
Simule le workflow exact de _send_chat_message()
"""

import sys
from pathlib import Path

# Initialisation extension
print("=" * 60)
print("TEST FILE WRITER - CONTEXTE OGMA RÉEL")
print("=" * 60)

print("\n1️⃣ Initialisation extension (comme _ensure_file_writer)...")
try:
    from extensions.file_writer import initialize_file_writer
    
    file_writer = initialize_file_writer(
        uploads_dir="data/uploads",
        debug=True  # Logs détaillés
    )
    
    if file_writer:
        print("✅ Extension initialisée")
    else:
        print("❌ Extension retourne None")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Erreur initialisation: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Simulation messages réels
print("\n2️⃣ Test avec messages réalistes...")

test_cases = [
    {
        "user": "écris-moi un .md sur les bonnes pratiques Python",
        "ai": """# Bonnes Pratiques Python

## Introduction

Python est un langage élégant qui encourage un code lisible.

## PEP 8

PEP 8 est le guide de style officiel Python. Voici les points clés:

- Indentation: 4 espaces
- Ligne max: 79 caractères  
- Imports: en haut du fichier
- Nommage: snake_case pour fonctions/variables, PascalCase pour classes

## Tests

Utilisez pytest ou unittest pour vos tests.

## Conclusion

Un code Python propre est un code maintenable.
"""
    },
    {
        "user": "crée un document markdown de documentation",
        "ai": """Voici la documentation:

```markdown
# Documentation Projet

## Installation

```bash
pip install -r requirements.txt
```

## Usage

Lancez le script principal:

```bash
python main.py
```
```

Cette documentation couvre l'essentiel.
"""
    },
    {
        "user": "bonjour comment vas-tu?",
        "ai": "Je vais bien merci! Comment puis-je t'aider?"
    }
]

for i, test in enumerate(test_cases, 1):
    print(f"\n--- Test {i} ---")
    print(f"User: {test['user'][:50]}...")
    print(f"AI Response: {len(test['ai'])} chars")
    
    # Appel exact comme dans ogma_ng.py ligne 4718-4722
    saved_path = file_writer.process_response(
        user_message=test['user'],
        ai_response=test['ai']
    )
    
    if saved_path:
        print(f"✅ Fichier sauvegardé: {saved_path}")
        
        # Vérification fichier existe
        if Path(saved_path).exists():
            size = Path(saved_path).stat().st_size
            print(f"📄 Taille fichier: {size} bytes")
        else:
            print(f"❌ ERREUR: Fichier n'existe pas!")
    else:
        print("⚪ Pas de fichier à sauvegarder")

# Statistiques finales
print("\n3️⃣ Statistiques extension...")
stats = file_writer.get_statistics()
for key, value in stats.items():
    print(f"  {key}: {value}")

print("\n" + "=" * 60)
print("FIN DU TEST")
print("=" * 60)
