#!/usr/bin/env python3
"""
Script pour extraire un embedding existant d'OGMA pour test avec IA externe
"""

import sqlite3
import json
from pathlib import Path

def extract_sample_embedding():
    """Extrait un embedding échantillon depuis la base OGMA"""
    
    db_path = Path("data/memory/memories.db")
    
    if not db_path.exists():
        print("❌ Base de données OGMA introuvable!")
        return None
    
    try:
        with sqlite3.connect(db_path) as conn:
            # Récupérer quelques souvenirs avec embeddings
            cursor = conn.execute("""
                SELECT id, title, summary, text_original, embedding_json, valence, score_impact
                FROM memories 
                WHERE embedding_json IS NOT NULL 
                AND embedding_json != ''
                LIMIT 5
            """)
            
            memories = cursor.fetchall()
            
            if not memories:
                print("❌ Aucun embedding trouvé dans la base!")
                return None
            
            print(f"✅ {len(memories)} souvenirs avec embeddings trouvés\n")
            
            for i, (mem_id, title, summary, text_orig, embedding_json, valence, score) in enumerate(memories):
                print(f"--- SOUVENIR {i+1} ---")
                print(f"ID: {mem_id}")
                print(f"Titre: {title or 'N/A'}")
                print(f"Résumé: {(summary or 'N/A')[:100]}...")
                print(f"Texte: {(text_orig or 'N/A')[:100]}...")
                print(f"Valence: {valence}")
                print(f"Score: {score}")
                
                # Parser l'embedding
                try:
                    embedding_vector = json.loads(embedding_json)
                    if isinstance(embedding_vector, list) and len(embedding_vector) > 100:
                        print(f"✅ Embedding valide: {len(embedding_vector)} dimensions")
                        
                        # Afficher les premières valeurs
                        preview = embedding_vector[:10]
                        print(f"Preview (10 premières valeurs): {preview}")
                        
                        # Retourner toutes les infos pour le test
                        return {
                            "memory_id": mem_id,
                            "title": title,
                            "summary": summary,
                            "text_original": text_orig,
                            "embedding": embedding_vector,
                            "valence": valence,
                            "score_impact": score,
                            "embedding_preview": preview,
                            "dimensions": len(embedding_vector)
                        }
                    else:
                        print(f"❌ Embedding invalide: {type(embedding_vector)}")
                        
                except Exception as e:
                    print(f"❌ Erreur parsing embedding: {e}")
                
                print()
            
            return None
            
    except Exception as e:
        print(f"❌ Erreur accès base: {e}")
        return None

if __name__ == "__main__":
    print("🔍 Extraction d'un embedding échantillon depuis OGMA...")
    
    sample = extract_sample_embedding()
    
    if sample:
        print("=" * 60)
        print("🎯 EMBEDDING EXTRAIT POUR TEST MISTRAL:")
        print("=" * 60)
        print(f"Memory ID: {sample['memory_id']}")
        print(f"Titre: {sample['title']}")
        print(f"Contenu: {sample['text_original'][:200]}...")
        print(f"Dimensions: {sample['dimensions']}")
        print()
        print("📋 EMBEDDING COMPLET (à copier pour Mistral):")
        print("-" * 40)
        print(json.dumps(sample['embedding'], indent=2)[:1000] + "...")
        print()
        print("🧪 QUESTION TEST POUR MISTRAL:")
        print("\"Voici un vecteur d'embedding de 768 dimensions représentant un concept/souvenir.")
        print("Peux-tu deviner de quoi il s'agit? Quel sentiment, idée ou concept cela pourrait représenter?\"")
        
    else:
        print("❌ Impossible d'extraire un embedding valide")