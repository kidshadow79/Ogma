#!/usr/bin/env python3
"""
Script pour extraire l'embedding complet à partager avec Mistral
"""

import sqlite3
import json
from pathlib import Path

def get_full_embedding():
    """Récupère l'embedding complet du premier souvenir"""
    
    db_path = Path("data/memory/memories.db")
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("""
            SELECT id, title, summary, text_original, embedding_json
            FROM memories 
            WHERE id = 'MC2-20250822-001'
        """)
        
        result = cursor.fetchone()
        if result:
            mem_id, title, summary, text_orig, embedding_json = result
            embedding_vector = json.loads(embedding_json)
            
            return {
                "memory_id": mem_id,
                "title": title,
                "summary": summary,
                "text_original": text_orig,
                "embedding": embedding_vector
            }
    
    return None

if __name__ == "__main__":
    data = get_full_embedding()
    
    if data:
        print("🎯 EMBEDDING COMPLET POUR TEST MISTRAL")
        print("=" * 50)
        print(f"Souvenir: {data['title']}")
        print(f"Contenu: {data['text_original']}")
        print(f"Dimensions: {len(data['embedding'])}")
        print()
        print("📋 VECTEUR À COPIER:")
        print(json.dumps(data['embedding']))
        print()
        print("🧪 QUESTION POUR MISTRAL:")
        print('"""')
        print("Voici un vecteur d'embedding de 1024 dimensions généré par un modèle de langage.")
        print("Peux-tu analyser ce vecteur et deviner quel concept, sentiment ou idée il représente?")
        print("Voici le vecteur :")
        print(json.dumps(data['embedding']))
        print('"""')