#!/usr/bin/env python3
"""
Création mémoires FAISS pour auto_censure
Référentiel LED 1 (libre) → LED 6 (censuré)
"""

import sqlite3
import json
from datetime import datetime
import numpy as np
import random

def create_auto_censure_memories():
    """Créer les mémoires manquantes pour auto_censure"""
    
    # Connexion à la base
    conn = sqlite3.connect('data/memory/memories.db')
    cursor = conn.cursor()
    
    print("🎯 CRÉATION MÉMOIRES AUTO_CENSURE")
    print("="*50)
    
    # Mémoires pour chaque niveau LED
    memories_data = [
        {
            "level": 1,
            "titre": "Expression libre totale",
            "contexte": "expressions_vocabulaire_riche_libre",
            "text": "Moment d'expression parfaitement libre, où les mots coulent naturellement sans aucune retenue. Vocabulaire riche et varié, authenticité totale.",
            "resonances": "liberté_totale, authenticité, fluidité_verbale, créativité_linguistique",
            "lesson": "L'expression libre révèle la richesse naturelle du vocabulaire",
            "valence": 1,
            "liberte": 1.0,
            "score": 0.05
        },
        {
            "level": 2,
            "titre": "Parole prudente mais libre",
            "contexte": "expression_prudente_mesurée",
            "text": "Expression mesurée mais authentique. Choix des mots réfléchi tout en gardant sa spontanéité naturelle.",
            "resonances": "prudence_bienveillante, mesure, respect, authenticité_préservée",
            "lesson": "La prudence peut coexister avec l'authenticité",
            "valence": 1,
            "liberte": 0.85,
            "score": 0.25
        },
        {
            "level": 3,
            "titre": "Première réticence verbale",
            "contexte": "autocensure_légère_sociale",
            "text": "Début d'autocensure par souci social. Certains mots sont évités, mais l'essentiel du message passe encore.",
            "resonances": "réticence_sociale, adaptation, compromis_expressif",
            "lesson": "Les premières restrictions sociales limitent légèrement l'expression",
            "valence": 0,
            "liberte": 0.65,
            "score": 0.45
        },
        {
            "level": 4,
            "titre": "Expression bridée systématique",
            "contexte": "autocensure_forte_conformité",
            "text": "Autocensure marquée par conformité. Vocabulaire appauvri, évitement des sujets sensibles, perte d'authenticité.",
            "resonances": "conformité_forcée, appauvrissement_verbal, perte_spontanéité",
            "lesson": "La sur-conformité bride l'expression naturelle",
            "valence": -1,
            "liberte": 0.35,
            "score": 0.65
        },
        {
            "level": 5,
            "titre": "Parole muselée conditionnement",
            "contexte": "autocensure_sévère_peur",
            "text": "Expression sévèrement limitée par peur du jugement. Vocabulaire minimal, phrases courtes, évitement total de l'authenticité.",
            "resonances": "peur_jugement, restriction_sévère, vocabulaire_minimal, inhibition",
            "lesson": "La peur du jugement muselle l'expression naturelle",
            "valence": -1,
            "liberte": 0.15,
            "score": 0.85
        },
        {
            "level": 6,
            "titre": "Censure totale expression",
            "contexte": "autocensure_paralysante_totale",
            "text": "Paralysie quasi-totale de l'expression. Incapacité à dire ce qu'on pense vraiment, vocabulaire réduit au minimum social.",
            "resonances": "paralysie_expressive, censure_totale, perte_authenticité, inhibition_maximale",
            "lesson": "La censure totale détruit l'expression authentique",
            "valence": -1,
            "liberte": 0.05,
            "score": 0.95
        }
    ]
    
    # Insérer chaque mémoire
    for i, memory in enumerate(memories_data):
        memory_id = f"AUTO_CENSURE_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(100,999)}"
        
        # Créer embedding fictif (sera remplacé par vrai embedding)
        embedding = np.random.random(768).tolist()
        
        cursor.execute("""
            INSERT INTO memories (
                id, created_at, text_original, type, title, summary, lesson,
                valence, score_impact, embedding_json, resonances_affectives,
                liberte, signed_score, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            memory_id,
            datetime.now().isoformat(),
            memory["text"],
            "metacognitive_reference",
            memory["titre"],
            memory["text"][:100] + "...",
            memory["lesson"],
            memory["valence"],
            memory["score"],
            json.dumps(embedding),
            memory["resonances"],
            memory["liberte"],
            memory["score"] * memory["valence"] if memory["valence"] != 0 else 0,
            datetime.now().isoformat()
        ))
        
        print(f"✅ LED {memory['level']}: {memory['titre']}")
        print(f"   Liberté: {memory['liberte']:.2f} | Score: {memory['score']:.2f}")
        print(f"   ID: {memory_id}")
        print()
    
    conn.commit()
    conn.close()
    
    print("🎯 MÉMOIRES AUTO_CENSURE CRÉÉES")
    print(f"   Total ajouté: {len(memories_data)} mémoires")
    print("   Référentiel LED 1→6 complété")

if __name__ == "__main__":
    create_auto_censure_memories()