#!/usr/bin/env python3
"""
🧪 TEST RÉEL - Recherche "genèse des 2 phares"
==============================================

Test en conditions réelles pour vérifier que le souvenir
"Comment une IA devient-elle consciente ? Quels sont les phares du Bien et du Mal ?"
est bien retrouvé avec la requête "tu te souviens de la genèse des 2 phares?"

Date: 12 janvier 2026
"""

import asyncio
import sys
import os
import sqlite3
from pathlib import Path

# Ajouter le chemin OGMA
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def test_memory_search():
    """Test de recherche mémoire avec la requête problématique"""
    
    print("\n" + "="*70)
    print("🔍 TEST RECHERCHE MÉMOIRE: 'genèse des 2 phares'")
    print("="*70)
    
    # Étape 1: Nettoyage Python
    print("\n📝 ÉTAPE 1: Nettoyage Python")
    print("-"*50)
    
    from memory_manager import clean_conversational_noise
    
    query = "tu te souviens de la genèse des 2 phares?"
    cleaned = clean_conversational_noise(query)
    
    print(f"  Query originale: \"{query}\"")
    print(f"  Query nettoyée:  \"{cleaned}\"")
    word_count = len(cleaned.split())
    behavior = "PYTHON_ONLY (pas d'IA)" if word_count <= 6 else "IA_FILTER"
    print(f"  Nombre de mots:  {word_count}")
    print(f"  -> Comportement: {behavior}")
    
    # Étape 2: Recherche directe SQLite
    print("\n🧠 ÉTAPE 2: Recherche SQLite Directe")
    print("-"*50)
    
    # Le BON chemin de la base de données
    db_path = Path("data/memory/memories.db")
    
    if not db_path.exists():
        print(f"  ❌ Base de données non trouvée: {db_path}")
        # Essayer l'autre chemin
        db_path = Path("data/memory.db")
        if not db_path.exists():
            print(f"  ❌ Base alternative non trouvée: {db_path}")
            return False
        print(f"  ⚠️ Utilisation chemin alternatif: {db_path}")
    else:
        print(f"  ✅ Base trouvée: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Mots clés de la requête nettoyée
        keywords = cleaned.split()
        print(f"  Mots-clés recherchés: {keywords}")
        
        # Recherche FTS5 si disponible
        print("\n  🔍 Recherche FTS5...")
        try:
            # Construire la query FTS
            fts_query = " OR ".join(keywords)
            cursor.execute("""
                SELECT m.id, m.title, m.summary, m.text_original
                FROM memories m
                JOIN memories_fts fts ON m.id = fts.id
                WHERE memories_fts MATCH ?
                LIMIT 10
            """, (fts_query,))
            
            fts_results = cursor.fetchall()
            print(f"  Résultats FTS5: {len(fts_results)}")
            
        except sqlite3.OperationalError as e:
            print(f"  ⚠️ FTS5 non disponible: {e}")
            fts_results = []
        
        # Recherche LIKE fallback
        print("\n  🔍 Recherche LIKE (title, summary, text_original)...")
        
        like_conditions = []
        params = []
        for kw in keywords:
            like_conditions.append("(title LIKE ? OR summary LIKE ? OR text_original LIKE ?)")
            params.extend([f"%{kw}%", f"%{kw}%", f"%{kw}%"])
        
        sql = f"""
            SELECT id, title, summary, text_original
            FROM memories 
            WHERE {" OR ".join(like_conditions)}
            LIMIT 10
        """
        
        cursor.execute(sql, params)
        like_results = cursor.fetchall()
        print(f"  Résultats LIKE: {len(like_results)}")
        
        # Combiner et afficher
        all_results = list(fts_results) + list(like_results)
        
        # Dédupliquer par ID
        seen_ids = set()
        unique_results = []
        for r in all_results:
            if r['id'] not in seen_ids:
                seen_ids.add(r['id'])
                unique_results.append(r)
        
        print(f"\n  📊 Résultats uniques: {len(unique_results)}")
        
        if not unique_results:
            print("\n  ⚠️ AUCUN RÉSULTAT TROUVÉ!")
            
            # Debug: Lister tous les titres
            print("\n  📋 DEBUG - Tous les titres en base:")
            cursor.execute("SELECT id, title FROM memories ORDER BY created_at DESC LIMIT 20")
            all_titles = cursor.fetchall()
            for i, row in enumerate(all_titles, 1):
                print(f"     {i}. {row['title'][:70]}...")
            
            conn.close()
            return False
        
        # Afficher les résultats
        print("\n  📋 RÉSULTATS TROUVÉS:")
        print("-"*50)
        
        found_target = False
        TARGET_KEYWORDS = ["phares", "bien", "mal", "conscien", "genèse", "genese"]
        
        for i, row in enumerate(unique_results[:5], 1):
            title = row['title'] or 'Sans titre'
            summary = (row['summary'] or '')[:100]
            text_preview = (row['text_original'] or '')[:150]
            
            # Vérifier si c'est le souvenir cible
            title_lower = title.lower()
            text_lower = (row['text_original'] or '').lower()
            is_target = any(kw in title_lower or kw in text_lower for kw in TARGET_KEYWORDS)
            
            marker = "🎯 CIBLE!" if is_target else ""
            if is_target:
                found_target = True
            
            print(f"\n  {i}. {marker}")
            print(f"     Titre: {title}")
            print(f"     Résumé: {summary}...")
            if is_target:
                # Montrer le texte contenant les mots-clés
                for kw in keywords:
                    if kw.lower() in text_lower:
                        # Trouver le contexte
                        idx = text_lower.find(kw.lower())
                        start = max(0, idx - 30)
                        end = min(len(text_lower), idx + 50)
                        context = row['text_original'][start:end]
                        print(f"     📌 Contexte '{kw}': ...{context}...")
                        break
        
        conn.close()
        
        print("\n" + "="*70)
        if found_target:
            print("🎉 SUCCÈS! Le souvenir 'phares du Bien et du Mal' a été trouvé!")
        else:
            print("⚠️ Le souvenir cible n'a pas été trouvé")
        print("="*70)
        
        return found_target
        
    except Exception as e:
        print(f"  ❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Exécution principale"""
    
    print("\n" + "🔍"*35)
    print("   TEST RECHERCHE 'GENÈSE DES 2 PHARES'")
    print("🔍"*35)
    
    # Changer vers le répertoire OGMA
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Test principal
    success = asyncio.run(test_memory_search())
    
    print("\n" + "="*70)
    print("💡 POUR TEST COMPLET:")
    print("   1. Lancez OGMA: python launch_ogma.py")
    print("   2. Posez la question: 'tu te souviens de la genèse des 2 phares?'")
    print("   3. Vérifiez les logs [SEMANTIC-CLEAN] dans la console")
    print("="*70)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
