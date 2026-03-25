"""
Script de Migration FTS5 - Phase 2
Crée la table FTS5, les triggers de synchronisation, et peuple l'index initial
"""

import sqlite3
from pathlib import Path
import sys

db_path = Path("data/memory/memories.db")

print("\n" + "="*70)
print("🚀 MIGRATION FTS5 - PHASE 2 : CRÉATION & POPULATION")
print("="*70 + "\n")

try:
    with sqlite3.connect(db_path) as conn:
        
        # ========================================
        # ÉTAPE 1 : CRÉATION TABLE FTS5
        # ========================================
        print("📋 ÉTAPE 1/4 : Création table FTS5...")
        
        # Vérifier si table existe déjà
        cursor = conn.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='memories_fts'
        """)
        
        if cursor.fetchone():
            print("   ⚠️  Table memories_fts existe déjà")
            response = input("   Voulez-vous la supprimer et recréer? (oui/non): ")
            if response.lower() == 'oui':
                conn.execute("DROP TABLE IF EXISTS memories_fts")
                print("   🗑️  Table supprimée")
            else:
                print("   ❌ Migration annulée")
                sys.exit(0)
        
        # Créer table FTS5 avec colonnes optimisées
        conn.execute("""
            CREATE VIRTUAL TABLE memories_fts USING fts5(
                memory_id UNINDEXED,
                title,
                text_original,
                summary,
                lesson,
                tokenize='unicode61',
                prefix='2,3'
            )
        """)
        
        print("   ✅ Table FTS5 créée")
        print("      - Tokenizer: unicode61 (optimisé français)")
        print("      - Préfixes: 2,3 chars (recherche floue)")
        print("      - Colonnes indexées: title, text_original, summary, lesson")
        
        # ========================================
        # ÉTAPE 2 : CRÉATION TRIGGERS
        # ========================================
        print("\n📋 ÉTAPE 2/4 : Création triggers de synchronisation...")
        
        # Trigger INSERT
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS memories_fts_insert 
            AFTER INSERT ON memories
            BEGIN
                INSERT INTO memories_fts(memory_id, title, text_original, summary, lesson)
                VALUES (new.id, new.title, new.text_original, new.summary, new.lesson);
            END
        """)
        print("   ✅ Trigger INSERT créé")
        
        # Trigger UPDATE
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS memories_fts_update
            AFTER UPDATE ON memories
            BEGIN
                UPDATE memories_fts 
                SET title = new.title,
                    text_original = new.text_original,
                    summary = new.summary,
                    lesson = new.lesson
                WHERE memory_id = new.id;
            END
        """)
        print("   ✅ Trigger UPDATE créé")
        
        # Trigger DELETE
        conn.execute("""
            CREATE TRIGGER IF NOT EXISTS memories_fts_delete
            AFTER DELETE ON memories
            BEGIN
                DELETE FROM memories_fts WHERE memory_id = old.id;
            END
        """)
        print("   ✅ Trigger DELETE créé")
        
        # ========================================
        # ÉTAPE 3 : POPULATION INITIALE
        # ========================================
        print("\n📋 ÉTAPE 3/4 : Population index FTS5 avec souvenirs existants...")
        
        cursor = conn.execute("SELECT COUNT(*) FROM memories")
        total_memories = cursor.fetchone()[0]
        
        print(f"   📊 {total_memories} souvenirs à indexer...")
        
        # Insérer tous les souvenirs existants dans FTS5
        conn.execute("""
            INSERT INTO memories_fts(memory_id, title, text_original, summary, lesson)
            SELECT id, title, text_original, summary, lesson
            FROM memories
        """)
        
        cursor = conn.execute("SELECT COUNT(*) FROM memories_fts")
        fts_count = cursor.fetchone()[0]
        
        print(f"   ✅ {fts_count} souvenirs indexés")
        
        # ========================================
        # ÉTAPE 4 : VALIDATION
        # ========================================
        print("\n📋 ÉTAPE 4/4 : Validation de l'index FTS5...")
        
        # Test recherche simple
        test_query = "genèse"
        cursor = conn.execute("""
            SELECT memory_id, rank
            FROM memories_fts
            WHERE memories_fts MATCH ?
            ORDER BY rank
            LIMIT 5
        """, (test_query,))
        
        results = cursor.fetchall()
        print(f"   🔍 Test recherche '{test_query}': {len(results)} résultats")
        
        if results:
            for i, (mem_id, rank) in enumerate(results[:3], 1):
                # Récupérer titre pour affichage
                cursor2 = conn.execute("SELECT title FROM memories WHERE id = ?", (mem_id,))
                title = cursor2.fetchone()[0] or "(sans titre)"
                print(f"      {i}. {title[:50]}... (rank: {rank:.2f})")
        
        # Stats finales
        print("\n" + "="*70)
        print("✅ MIGRATION FTS5 TERMINÉE AVEC SUCCÈS")
        print("="*70)
        print(f"\n📊 STATISTIQUES:")
        print(f"   - Table FTS5:     memories_fts")
        print(f"   - Souvenirs:      {fts_count}/{total_memories}")
        print(f"   - Triggers:       3 (INSERT, UPDATE, DELETE)")
        print(f"   - Tokenizer:      unicode61")
        print(f"   - Préfixes:       2, 3 chars")
        
        conn.commit()
        
        print(f"\n💾 Base de données sauvegardée")
        print(f"📁 Backup disponible: data/memory_backup_fts5_migration_*")
        print("\n🚀 Prêt pour Phase 3 : Intégration hybride FAISS + FTS5")
        
except Exception as e:
    print(f"\n❌ ERREUR MIGRATION: {e}")
    import traceback
    traceback.print_exc()
    print("\n🔙 Base de données intacte (transaction annulée)")
    print("💾 Backup disponible pour restauration si nécessaire")
    sys.exit(1)

print("\n" + "="*70 + "\n")
