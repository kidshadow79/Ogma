"""
Diagnostic File Writer - État système OGMA
"""

import json
from pathlib import Path

print("=" * 70)
print("DIAGNOSTIC FILE WRITER - ÉTAT SYSTÈME")
print("=" * 70)

# 1. Vérification structure fichiers
print("\n1️⃣ Structure fichiers extension...")

extension_files = [
    "extensions/file_writer/__init__.py",
    "extensions/file_writer/file_writer_agent.py",
    "extensions/file_writer/request_detector.py",
    "extensions/file_writer/markdown_extractor.py",
    "extensions/file_writer/file_saver.py"
]

for file_path in extension_files:
    p = Path(file_path)
    if p.exists():
        size = p.stat().st_size
        print(f"  ✅ {file_path} ({size} bytes)")
    else:
        print(f"  ❌ {file_path} MANQUANT")

# 2. Vérification répertoire uploads
print("\n2️⃣ Répertoire uploads...")
uploads_dir = Path("data/uploads")

if uploads_dir.exists():
    print(f"  ✅ {uploads_dir} existe")
    
    # Lister fichiers .md récents
    md_files = sorted(uploads_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    
    if md_files:
        print(f"  📁 {len(md_files)} fichiers .md trouvés")
        print("\n  Fichiers récents:")
        for f in md_files[:5]:  # 5 plus récents
            mtime = f.stat().st_mtime
            size = f.stat().st_size
            from datetime import datetime
            date = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            print(f"    - {f.name} ({size} bytes, modifié: {date})")
    else:
        print("  ⚠️ Aucun fichier .md trouvé")
else:
    print(f"  ❌ {uploads_dir} n'existe pas")

# 3. Test import extension
print("\n3️⃣ Test import extension...")
try:
    from extensions.file_writer import initialize_file_writer, is_available
    print("  ✅ Import réussi")
    
    # Test disponibilité
    available = is_available()
    print(f"  is_available(): {available}")
    
except ImportError as e:
    print(f"  ❌ Erreur import: {e}")
except Exception as e:
    print(f"  ❌ Erreur: {e}")

# 4. Test initialisation
print("\n4️⃣ Test initialisation...")
try:
    from extensions.file_writer import initialize_file_writer
    
    file_writer = initialize_file_writer(
        uploads_dir="data/uploads",
        debug=True
    )
    
    if file_writer:
        print("  ✅ Extension initialisée")
        
        # Test statistiques
        stats = file_writer.get_statistics()
        print("\n  Statistiques:")
        for key, value in stats.items():
            print(f"    {key}: {value}")
    else:
        print("  ❌ Extension retourne None")
        
except Exception as e:
    print(f"  ❌ Erreur initialisation: {e}")
    import traceback
    traceback.print_exc()

# 5. Vérification code ogma_ng.py
print("\n5️⃣ Intégration ogma_ng.py...")

with open("ogma_ng.py", "r", encoding="utf-8") as f:
    content = f.read()
    
# Vérifier initialisation globale
if "_file_writer_ext = None" in content:
    print("  ✅ Variable globale déclarée")
else:
    print("  ❌ Variable globale manquante")

# Vérifier fonction _ensure_file_writer
if "def _ensure_file_writer():" in content:
    print("  ✅ Fonction _ensure_file_writer définie")
    
    # Vérifier debug mode
    if 'debug=True' in content:
        print("  ✅ Debug mode activé")
    elif 'debug=False' in content:
        print("  ⚠️ Debug mode désactivé")
else:
    print("  ❌ Fonction _ensure_file_writer manquante")

# Vérifier workflow _send_chat_message
if "file_writer = _ensure_file_writer()" in content:
    print("  ✅ Workflow intégré dans _send_chat_message")
    
    # Compter occurrences
    count = content.count("file_writer = _ensure_file_writer()")
    print(f"  📊 {count} appel(s) trouvé(s)")
else:
    print("  ❌ Workflow non intégré")

# Vérifier notification
if "_notify_safe(f\"📁 Fichier sauvegardé:" in content:
    print("  ✅ Notification utilisateur présente")
else:
    print("  ⚠️ Notification utilisateur manquante")

# 6. Patterns détection
print("\n6️⃣ Patterns détection...")
try:
    from extensions.file_writer.request_detector import RequestDetector
    
    detector = RequestDetector(debug=True)
    
    test_messages = [
        "écris-moi un .md sur Python",
        "crée un document markdown",
        "rédige un fichier .md",
        "bonjour comment vas-tu"
    ]
    
    print("\n  Tests détection:")
    for msg in test_messages:
        is_request, confidence, title = detector.detect(msg)
        status = "✅" if is_request else "⚪"
        print(f"    {status} '{msg}' → {is_request} (confidence: {confidence:.2f})")
        
except Exception as e:
    print(f"  ❌ Erreur test patterns: {e}")

print("\n" + "=" * 70)
print("FIN DIAGNOSTIC")
print("=" * 70)

# Conclusion
print("\n💡 RECOMMANDATIONS:")
print("  1. Vérifier logs console OGMA (debug=True activé)")
print("  2. Tester avec: 'écris-moi un .md sur les tests'")
print("  3. Vérifier notification frontend après création")
print("  4. Consulter data/uploads/ pour fichiers créés")
