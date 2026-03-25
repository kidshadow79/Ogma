"""
test_hybrid_search.py
---------------------
Test du système hybride FAISS + FTS5 pour la recherche de souvenirs.
Valide que "genèse des 2 phares" trouve maintenant le bon souvenir.
"""

import sqlite3
from pathlib import Path

def test_fts5_direct():
    """Test direct FTS5 sans passer par MemoryManager"""
    print("="*80)
    print("🧪 TEST DIRECT FTS5")
    print("="*80)
    
    db_path = Path("data/memory/memories.db")
    
    if not db_path.exists():
        print(f"❌ Base de données introuvable: {db_path}")
        return
    
    test_queries = [
        "genèse des 2 phares",
        "genèse",
        "phares",
        "deux phares",
        "naissance conscience artificielle",
        "Luna Archiviste",
    ]
    
    with sqlite3.connect(db_path) as conn:
        for query in test_queries:
            print(f"\n📝 Requête: '{query}'")
            print("-" * 60)
            
            try:
                cursor = conn.execute("""
                    SELECT m.id, m.title, m.type, fts.rank
                    FROM memories_fts fts
                    JOIN memories m ON fts.memory_id = m.id
                    WHERE memories_fts MATCH ?
                    ORDER BY rank
                    LIMIT 5
                """, (query,))
                
                results = cursor.fetchall()
                
                if results:
                    print(f"✅ {len(results)} résultats FTS5:")
                    for i, (mem_id, title, mem_type, rank) in enumerate(results, 1):
                        fts5_score = 1.0 / (1.0 + abs(rank))
                        print(f"  {i}. [{mem_type}] {title}")
                        print(f"     ID: {mem_id}, Rank: {rank:.2f}, Score: {fts5_score:.3f}")
                else:
                    print("❌ Aucun résultat FTS5")
                    
            except Exception as e:
                print(f"❌ Erreur FTS5: {e}")


def test_memory_content():
    """Vérifie le contenu exact des souvenirs avec 'genèse' ou 'phares'"""
    print("\n" + "="*80)
    print("🔍 VÉRIFICATION CONTENU SOUVENIRS")
    print("="*80)
    
    db_path = Path("data/memory/memories.db")
    
    with sqlite3.connect(db_path) as conn:
        # Recherche dans title, summary, text_original
        cursor = conn.execute("""
            SELECT id, title, type, summary, text_original
            FROM memories
            WHERE title LIKE '%genèse%' 
               OR title LIKE '%phare%'
               OR summary LIKE '%genèse%'
               OR summary LIKE '%phare%'
               OR text_original LIKE '%genèse%'
               OR text_original LIKE '%phare%'
            LIMIT 10
        """)
        
        results = cursor.fetchall()
        
        if results:
            print(f"\n✅ {len(results)} souvenirs contenant 'genèse' ou 'phare':")
            for i, (mem_id, title, mem_type, summary, text) in enumerate(results, 1):
                print(f"\n{i}. [{mem_type}] {title}")
                print(f"   ID: {mem_id}")
                if summary:
                    print(f"   Summary: {summary[:150]}...")
                if text:
                    print(f"   Text: {text[:150]}...")
        else:
            print("❌ Aucun souvenir trouvé avec 'genèse' ou 'phare'")


def test_fts5_table_content():
    """Vérifie que la table FTS5 est bien peuplée"""
    print("\n" + "="*80)
    print("📊 STATISTIQUES TABLE FTS5")
    print("="*80)
    
    db_path = Path("data/memory/memories.db")
    
    with sqlite3.connect(db_path) as conn:
        # Compter entrées FTS5
        cursor = conn.execute("SELECT COUNT(*) FROM memories_fts")
        fts5_count = cursor.fetchone()[0]
        
        # Compter entrées memories
        cursor = conn.execute("SELECT COUNT(*) FROM memories")
        memories_count = cursor.fetchone()[0]
        
        print(f"📦 Entrées memories: {memories_count}")
        print(f"📦 Entrées memories_fts: {fts5_count}")
        
        if fts5_count == memories_count:
            print("✅ Synchronisation parfaite")
        else:
            print(f"⚠️ Désynchronisation: {memories_count - fts5_count} souvenirs manquants dans FTS5")
        
        # Échantillon FTS5
        print("\n📋 Échantillon FTS5 (5 premiers):")
        cursor = conn.execute("""
            SELECT memory_id, title
            FROM memories_fts
            LIMIT 5
        """)
        
        for mem_id, title in cursor.fetchall():
            print(f"  - {mem_id}: {title}")


if __name__ == "__main__":
    print("\n🚀 TEST SYSTÈME HYBRIDE FAISS + FTS5")
    print("="*80)
    
    test_fts5_table_content()
    test_memory_content()
    test_fts5_direct()
    
    print("\n" + "="*80)
    print("✅ TESTS TERMINÉS")
    print("="*80)
