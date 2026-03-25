"""
Test notification "Écriture en cours..." file_writer
Simule workflow OGMA complet avec notifications
"""

from pathlib import Path
import time

print("=" * 70)
print("TEST NOTIFICATIONS FILE WRITER")
print("=" * 70)

# 1. Initialisation
print("\n1️⃣ Initialisation extension...")
from extensions.file_writer import initialize_file_writer, detect_request

file_writer = initialize_file_writer(
    uploads_dir="data/uploads",
    debug=True
)

if not file_writer:
    print("❌ Extension non initialisée")
    exit(1)

print("✅ Extension initialisée")

# 2. Test détection préalable
print("\n2️⃣ Test pré-détection (comme notification frontend)...")

test_messages = [
    ("écris-moi un .md sur les notifications", True),
    ("crée un document markdown de guide", True),
    ("bonjour comment vas-tu?", False),
    ("rédige un fichier .md pour les tests", True)
]

for message, expected in test_messages:
    is_request = detect_request(message)
    status = "✅" if is_request == expected else "❌"
    
    print(f"{status} '{message[:40]}...' → Détecté: {is_request} (attendu: {expected})")
    
    if is_request:
        print(f"   → Notification UI: '✍️ Écriture en cours...'")

# 3. Test workflow complet avec timing
print("\n3️⃣ Test workflow complet (détection → notification → traitement)...")

user_message = "écris-moi un .md sur le système de notifications"
ai_response = """# Système de Notifications OGMA

## Introduction

Le système de notifications permet d'informer l'utilisateur en temps réel des opérations en cours.

## Workflow

1. Pré-détection de la demande
2. Notification "✍️ Écriture en cours..."
3. Extraction contenu markdown
4. Sauvegarde fichier
5. Notification "📁 Fichier sauvegardé"

## Avantages

- Transparence totale
- Feedback immédiat
- Pas d'attente silencieuse

## Conclusion

L'utilisateur sait toujours ce qui se passe.
"""

print(f"\nUser: {user_message}")
print(f"AI Response: {len(ai_response)} chars")
print()

# Étape 1: Pré-détection
print("--- ÉTAPE 1: PRÉ-DÉTECTION ---")
start = time.time()
is_request = detect_request(user_message)
detection_time = (time.time() - start) * 1000

if is_request:
    print(f"✅ Demande détectée ({detection_time:.2f}ms)")
    print("🔔 NOTIFICATION FRONTEND: '✍️ Écriture en cours...'")
else:
    print("⚪ Pas de demande fichier")
    exit(0)

# Étape 2: Traitement complet
print("\n--- ÉTAPE 2: TRAITEMENT COMPLET ---")
start = time.time()
saved_path = file_writer.process_response(user_message, ai_response)
processing_time = (time.time() - start) * 1000

if saved_path:
    print(f"✅ Fichier sauvegardé ({processing_time:.2f}ms)")
    print(f"🔔 NOTIFICATION FRONTEND: '📁 Fichier sauvegardé: {Path(saved_path).name}'")
    print(f"\n📄 Chemin: {saved_path}")
    
    # Vérification
    if Path(saved_path).exists():
        size = Path(saved_path).stat().st_size
        print(f"📊 Taille: {size} bytes")
    else:
        print("❌ ERREUR: Fichier n'existe pas!")
else:
    print("❌ Échec sauvegarde")

# 4. Timing total
print(f"\n⏱️ TIMING TOTAL: {(detection_time + processing_time):.2f}ms")
print(f"   - Détection: {detection_time:.2f}ms")
print(f"   - Traitement: {processing_time:.2f}ms")

print("\n" + "=" * 70)
print("FIN DU TEST")
print("=" * 70)

print("\n💡 UX WORKFLOW:")
print("   1. User envoie: 'écris-moi un .md sur X'")
print("   2. Luna génère réponse")
print("   3. OGMA détecte demande → Notif '✍️ Écriture en cours...'")
print("   4. OGMA traite (extraction + sauvegarde)")
print("   5. OGMA notifie succès → Notif '📁 Fichier sauvegardé: X.md'")
