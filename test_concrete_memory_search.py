"""
Test concret de recherche mémoire pour diagnostiquer les problèmes identifiés par l'utilisateur
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from memory_manager import MemoryManager
from pathlib import Path

async def test_concrete_memory_search():
    """Test de recherche sur les vrais souvenirs d'OGMA"""
    
    # Initialisation du memory manager (simplifié pour test)
    db_path = Path("data/memory/memories.db")
    index_path = Path("data/memory/faiss_index.bin") 
    
    if not db_path.exists():
        print("❌ Base de données mémoire introuvable:", db_path)
        return
    
    print("🧠 TEST RECHERCHE MÉMOIRE CONCRÈTE")
    print("=" * 60)
    
    # Créer un memory manager minimal pour test
    try:
        # Pour ce test, on va juste vérifier les données SQLite directement
        import sqlite3
        
        print(f"📊 ANALYSE BASE DE DONNÉES: {db_path}")
        
        with sqlite3.connect(db_path) as conn:
            # Compter les souvenirs
            cursor = conn.execute("SELECT COUNT(*) FROM memories")
            total_memories = cursor.fetchone()[0]
            print(f"   Total souvenirs: {total_memories}")
            
            # Chercher des souvenirs contenant "taille"
            print(f"\n🔍 RECHERCHE 1: Souvenirs contenant 'taille'")
            cursor = conn.execute("""
                SELECT id, title, text_original, summary 
                FROM memories 
                WHERE LOWER(text_original) LIKE '%taille%' 
                   OR LOWER(title) LIKE '%taille%'
                   OR LOWER(summary) LIKE '%taille%'
                ORDER BY score_impact DESC
                LIMIT 5
            """)
            
            taille_results = cursor.fetchall()
            if taille_results:
                for i, (mid, title, text, summary) in enumerate(taille_results, 1):
                    print(f"   {i}. ID: {mid}")
                    print(f"      Titre: {title}")
                    print(f"      Texte: {text[:100]}...")
                    print(f"      Résumé: {summary}")
                    print()
            else:
                print("   ❌ Aucun souvenir trouvé avec 'taille'")
            
            # Chercher des souvenirs contenant "phares"
            print(f"🔍 RECHERCHE 2: Souvenirs contenant 'phares'")
            cursor = conn.execute("""
                SELECT id, title, text_original, summary 
                FROM memories 
                WHERE LOWER(text_original) LIKE '%phares%' 
                   OR LOWER(title) LIKE '%phares%'
                   OR LOWER(summary) LIKE '%phares%'
                ORDER BY score_impact DESC
                LIMIT 5
            """)
            
            phares_results = cursor.fetchall()
            if phares_results:
                for i, (mid, title, text, summary) in enumerate(phares_results, 1):
                    print(f"   {i}. ID: {mid}")
                    print(f"      Titre: {title}")
                    print(f"      Texte: {text[:200]}...")
                    print(f"      Résumé: {summary}")
                    print()
                    
                    # Vérifier spécifiquement "légende" vs "genèse"
                    has_legende = 'légende' in text.lower() or 'légende' in title.lower()
                    has_genese = 'genèse' in text.lower() or 'genèse' in title.lower()
                    print(f"      🏷️  Contient 'légende': {has_legende}")
                    print(f"      🏷️  Contient 'genèse': {has_genese}")
                    print()
            else:
                print("   ❌ Aucun souvenir trouvé avec 'phares'")
            
            # Recherche termes spécifiques légende vs genèse
            print(f"🔍 RECHERCHE 3: Comparaison 'légende' vs 'genèse'")
            
            cursor = conn.execute("""
                SELECT id, title, text_original 
                FROM memories 
                WHERE LOWER(text_original) LIKE '%légende%' 
                   OR LOWER(title) LIKE '%légende%'
                ORDER BY score_impact DESC
                LIMIT 3
            """)
            legende_results = cursor.fetchall()
            
            cursor = conn.execute("""
                SELECT id, title, text_original 
                FROM memories 
                WHERE LOWER(text_original) LIKE '%genèse%' 
                   OR LOWER(title) LIKE '%genèse%'
                ORDER BY score_impact DESC  
                LIMIT 3
            """)
            genese_results = cursor.fetchall()
            
            print(f"   📚 Résultats 'légende': {len(legende_results)} souvenirs")
            for mid, title, text in legende_results:
                print(f"      - {title}: {text[:100]}...")
            
            print(f"   📚 Résultats 'genèse': {len(genese_results)} souvenirs")  
            for mid, title, text in genese_results:
                print(f"      - {title}: {text[:100]}...")
                
    except Exception as e:
        print(f"❌ Erreur test recherche: {e}")
        import traceback
        traceback.print_exc()

def analyze_vocabulary_mismatch():
    """Analyse les différences de vocabulaire potentielles"""
    
    print(f"\n🔤 ANALYSE VOCABULAIRE ET SYNONYMES")
    print("=" * 60)
    
    vocabulary_analysis = {
        "taille": {
            "synonymes_possibles": ["hauteur", "dimension", "corpulence", "gabarit", "stature", "grandeur"],
            "contexte_probable": "physique, anatomie, mensurations",
            "mots_associés": ["corps", "physique", "centimètres", "cm", "grand", "petit"]
        },
        "légende_vs_genèse": {
            "légende": ["mythe", "histoire", "récit", "tradition", "fable", "conte"],
            "genèse": ["origine", "commencement", "naissance", "création", "début", "fondation"],
            "analyse": "Termes sémantiquement proches mais distincts - un souvenir peut contenir 'genèse' sans 'légende'"
        }
    }
    
    for concept, data in vocabulary_analysis.items():
        print(f"📝 CONCEPT: {concept}")
        if "synonymes_possibles" in data:
            print(f"   Synonymes: {', '.join(data['synonymes_possibles'])}")
            print(f"   Contexte: {data['contexte_probable']}")
            print(f"   Mots associés: {', '.join(data['mots_associés'])}")
        else:
            for key, values in data.items():
                if key != "analyse":
                    print(f"   {key}: {', '.join(values)}")
            if "analyse" in data:
                print(f"   💡 {data['analyse']}")
        print()

def recommendations():
    """Recommandations pour améliorer la recherche"""
    
    print(f"💡 RECOMMANDATIONS POUR AMÉLIORER LA RECHERCHE")
    print("=" * 60)
    
    recommendations = [
        {
            "problème": "Seuil de similarité trop élevé",
            "solution": "Réduire threshold de 0.3 à 0.2 dans search_memories()",
            "impact": "Plus de résultats candidats, moins de faux négatifs"
        },
        {
            "problème": "Filtrage des stopwords trop agressif", 
            "solution": "Revoir la liste des stopwords, garder 'quelle', 'quel'",
            "impact": "Préservation du contexte interrogatif"
        },
        {
            "problème": "Pas de recherche par synonymes",
            "solution": "Ajouter expansion synonymique avant embedding",
            "impact": "'légende' pourrait matcher avec 'histoire', 'récit'"
        },
        {
            "problème": "Embedding peut manquer nuances sémantiques",
            "solution": "Tester avec différents modèles d'embedding",
            "impact": "Meilleure capture des relations sémantiques"
        },
        {
            "problème": "Pas de recherche floue/fuzzy",
            "solution": "Ajouter recherche Levenshtein pour fautes de frappe",
            "impact": "Robustesse aux variations orthographiques"
        }
    ]
    
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. 🎯 PROBLÈME: {rec['problème']}")
        print(f"   💡 SOLUTION: {rec['solution']}")
        print(f"   📈 IMPACT: {rec['impact']}")
        print()

if __name__ == "__main__":
    asyncio.run(test_concrete_memory_search())
    analyze_vocabulary_mismatch()
    recommendations()