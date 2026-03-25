"""
Test manuel extension File Writer pour diagnostiquer le problème
"""

from extensions.file_writer import initialize_file_writer

print("=" * 70)
print("TEST FILE WRITER EXTENSION")
print("=" * 70)

# 1. Initialiser l'extension
print("\n1️⃣ Initialisation extension...")
file_writer = initialize_file_writer(uploads_dir="data/uploads", debug=True)

if not file_writer:
    print("❌ Échec initialisation")
    exit(1)

print("✅ Extension initialisée")

# 2. Test détection demande
print("\n2️⃣ Test détection demandes...")

test_messages = [
    ("écris-moi un .md sur Python", True),
    ("crée un document markdown sur les tests", True),
    ("rédige un fichier .md pour la documentation", True),
    ("bonjour comment vas-tu?", False),
    ("explique-moi Python", False),
]

for message, should_detect in test_messages:
    is_detected = file_writer.is_file_request(message)
    status = "✅" if is_detected == should_detect else "❌"
    print(f"{status} '{message}' → Détecté: {is_detected} (attendu: {should_detect})")

# 3. Test extraction + sauvegarde
print("\n3️⃣ Test extraction et sauvegarde...")

user_message = "écris-moi un .md sur les tests Python"
ai_response = """# Guide des Tests Python

## Introduction

Les tests sont essentiels pour garantir la qualité du code.

## Types de tests

- Tests unitaires
- Tests d'intégration
- Tests end-to-end

## Conclusion

Testez toujours votre code !
"""

print(f"User: {user_message}")
print(f"AI Response: {len(ai_response)} chars")

saved_path = file_writer.process_response(user_message, ai_response)

if saved_path:
    print(f"✅ Fichier sauvegardé: {saved_path}")
    
    # Vérifier contenu
    from pathlib import Path
    if Path(saved_path).exists():
        content = Path(saved_path).read_text(encoding='utf-8')
        print(f"📄 Contenu fichier: {len(content)} chars")
        print(f"Premiers 100 chars: {content[:100]}...")
    else:
        print(f"❌ Fichier non trouvé: {saved_path}")
else:
    print("❌ Aucun fichier sauvegardé")

# 4. Statistiques
print("\n4️⃣ Statistiques extension...")
stats = file_writer.get_statistics()
for key, value in stats.items():
    print(f"  {key}: {value}")

print("\n" + "=" * 70)
print("FIN DU TEST")
print("=" * 70)
