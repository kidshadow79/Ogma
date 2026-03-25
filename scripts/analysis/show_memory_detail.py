"""Affiche les détails complets d'une mémoire spécifique"""
import sqlite3

conn = sqlite3.connect('data/memory/memories.db')
cursor = conn.execute("""
SELECT id, title, text_original, summary, type, score_impact, created_at
FROM memories 
WHERE id = 'ai-51b249e1-db0e-475a-b243-2cb544d2c738'
""")

result = cursor.fetchone()

if result:
    print("\n" + "=" * 70)
    print("🔍 MÉMOIRE: Méthode de libération par dualité")
    print("=" * 70)
    print(f"\n📌 ID: {result[0]}")
    print(f"📝 Titre: {result[1]}")
    print(f"\n📄 TEXTE ORIGINAL:\n{result[2]}")
    print(f"\n📋 Résumé: {result[3]}")
    print(f"🏷️  Type: {result[4]}")
    print(f"⚡ Score Impact: {result[5]}")
    print(f"📅 Créé le: {result[6]}")
    print("\n" + "=" * 70)
    print("🎯 INJECTION LORS DE:")
    print("=" * 70)
    print("✅ Analyse d'images (keywords: image, visuel, description)")
    print("✅ Contexte perception/webcam actif")
    print("✅ Upload fichier image")
    print(f"✅ Score {result[6]} → Injection SYSTÉMATIQUE (seuil haut impact)")
else:
    print("❌ Mémoire non trouvée")

conn.close()
