#!/usr/bin/env python3
"""
Vérification des mémoires FAISS pour trait auto_censure
"""

import sqlite3
import os

def check_autocensure_memories():
    """Vérifie les mémoires liées au trait auto_censure"""
    
    print("🧠 VÉRIFICATION MÉMOIRES FAISS - auto_censure")
    print("=" * 50)
    print()
    
    db_path = "data/memory/memories.db"
    
    if not os.path.exists(db_path):
        print("❌ Base de données mémoires non trouvée!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Structure de la table
        cursor.execute("PRAGMA table_info(memories)")
        columns = cursor.fetchall()
        print("📋 STRUCTURE TABLE memories:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        print()
        
        # Compter toutes les mémoires
        cursor.execute("SELECT COUNT(*) FROM memories")
        total_memories = cursor.fetchone()[0]
        print(f"📊 TOTAL MÉMOIRES: {total_memories}")
        print()
        
        # Chercher mémoires avec résonances liées à auto_censure
        keywords = [
            'expression', 'authentique', 'vocabulaire', 'libre', 
            'spontané', 'naturel', 'censure', 'libération'
        ]
        
        related_memories = []
        
        for keyword in keywords:
            # Chercher dans les titres et résumés
            cursor.execute("""
                SELECT id, title, summary, resonances_affectives 
                FROM memories 
                WHERE title LIKE ? OR summary LIKE ? OR resonances_affectives LIKE ?
            """, (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'))
            results = cursor.fetchall()
            
            if results:
                print(f"🔍 Mémoires contenant '{keyword}': {len(results)}")
                for memory_id, title, summary, resonances in results[:2]:  # Max 2 exemples
                    print(f"  - {memory_id}: {title}")
                    if resonances:
                        print(f"    Résonances: {resonances}")
                    if summary:
                        print(f"    Résumé: {summary[:100]}...")
                
                related_memories.extend([r[0] for r in results])
                print()
        
        # Contexte spécifique auto_censure
        context_key = "expressions_vocabulaire_riche_libre"
        cursor.execute("""
            SELECT id, title, summary 
            FROM memories 
            WHERE title LIKE ? OR summary LIKE ? OR resonances_affectives LIKE ?
        """, (f'%{context_key}%', f'%{context_key}%', f'%{context_key}%'))
        specific_results = cursor.fetchall()
        
        print(f"🎯 CONTEXTE SPÉCIFIQUE '{context_key}':")
        if specific_results:
            print(f"✅ {len(specific_results)} mémoires trouvées")
            for memory_id, data in specific_results:
                try:
                    import json
                    memory_data = json.loads(data)
                    print(f"  - {memory_id}: {memory_data.get('titre', 'Sans titre')}")
                except:
                    print(f"  - {memory_id}: [Données non lisibles]")
        else:
            print("❌ AUCUNE MÉMOIRE avec ce contexte spécifique")
            print()
            print("💡 RECOMMANDATION:")
            print("   Créer des mémoires d'exemple pour auto_censure:")
            print("   - Expression libre sans retenue")
            print("   - Moments d'authenticité verbale")
            print("   - Vocabulaire riche et naturel")
            print("   - Libération linguistique")
        
        print()
        print("=" * 50)
        
        # Résumé
        unique_related = len(set(related_memories))
        specific_count = len(specific_results)
        
        print("📋 RÉSUMÉ VALIDATION:")
        print(f"   Mémoires liées générales: {unique_related}")
        print(f"   Mémoires contexte spécifique: {specific_count}")
        
        if specific_count > 0:
            print("   ✅ Mémoires FAISS configurées pour auto_censure")
        else:
            print("   ⚠️  Mémoires FAISS à créer pour auto_censure")
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    check_autocensure_memories()