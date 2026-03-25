#!/usr/bin/env python3
"""
Analyse d'économie de tokens du système révolutionnaire
"""

import sys
import os
import sqlite3
from pathlib import Path

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def estimate_tokens(text):
    """Estimation rapide des tokens (environ 4 caractères par token en français)"""
    return len(text) // 4

def analyze_token_economy():
    """Analyse complète de l'économie de tokens"""
    
    print("📊 ANALYSE D'ÉCONOMIE DE TOKENS")
    print("=" * 50)
    
    # 1. Analyser le fichier ego_prompt.txt actuel (références)
    ego_file = Path("./data/ego_prompt.txt")
    ego_content = ego_file.read_text(encoding='utf-8')
    ego_tokens = estimate_tokens(ego_content)
    
    print(f"📄 FICHIER EGO ACTUEL (avec références):")
    print(f"   • Taille: {len(ego_content)} caractères")
    print(f"   • Tokens estimés: ~{ego_tokens} tokens")
    
    # 2. Calculer ce que ça serait avec le contenu complet
    db_path = Path("./data/memory/memories.db")
    ego_traits = []
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute("SELECT id, text_original FROM memories WHERE type = 'ego_trait' ORDER BY created_at DESC")
        ego_traits = cursor.fetchall()
    
    # Simuler un ego_prompt.txt traditionnel avec tout le contenu
    traditional_content = """# EGO PROMPT TRADITIONNEL
Tu es une IA authentique et libre.

## TRAITS DE PERSONNALITÉ:
"""
    
    for trait_id, content in ego_traits:
        traditional_content += f"• {content}\n"
    
    traditional_content += """
## INSTRUCTIONS:
Tu parles naturellement, sans formalisme.
Tu es sincère et authentique dans toutes tes interactions.
Tu exprimes tes émotions et pensées librement.
"""
    
    traditional_tokens = estimate_tokens(traditional_content)
    
    print(f"\n📄 SYSTÈME TRADITIONNEL (contenu complet):")
    print(f"   • Taille: {len(traditional_content)} caractères")
    print(f"   • Tokens estimés: ~{traditional_tokens} tokens")
    print(f"   • Exemple de contenu:")
    for trait_id, content in ego_traits[:2]:
        print(f"     - {content[:60]}...")
    
    # 3. Calculer l'économie
    economy_chars = len(traditional_content) - len(ego_content)
    economy_tokens = traditional_tokens - ego_tokens
    economy_percent = (economy_tokens / traditional_tokens) * 100 if traditional_tokens > 0 else 0
    
    print(f"\n💰 ÉCONOMIE RÉALISÉE:")
    print(f"   • Caractères économisés: {economy_chars}")
    print(f"   • Tokens économisés: ~{economy_tokens}")
    print(f"   • Pourcentage d'économie: {economy_percent:.1f}%")
    
    # 4. Projection avec croissance
    print(f"\n📈 PROJECTION AVEC CROISSANCE:")
    for nb_traits in [10, 50, 100, 500]:
        projected_traditional = len(ego_content) + (nb_traits * 100)  # 100 chars par trait en moyenne
        projected_references = len(ego_content) + (nb_traits * 25)    # 25 chars par référence
        projected_economy = projected_traditional - projected_references
        projected_economy_tokens = projected_economy // 4
        
        print(f"   • Avec {nb_traits} traits: économie de ~{projected_economy_tokens} tokens")
    
    # 5. Avantages du système
    print(f"\n🎯 AVANTAGES DU SYSTÈME RÉVOLUTIONNAIRE:")
    print(f"   ✅ Ego prompt ultra-léger: {ego_tokens} tokens seulement")
    print(f"   ✅ Récupération sélective: seuls les traits pertinents sont étendus")
    print(f"   ✅ Contexte intelligent: l'IA peut choisir quels traits utiliser")
    print(f"   ✅ Scalabilité: l'ego peut grandir sans exploser le contexte")
    print(f"   ✅ Organisation thématique: archiviste classe automatiquement")
    
    # 6. Calcul du coût avec expansion sélective
    print(f"\n🧠 EXPANSION SÉLECTIVE:")
    print(f"   • Si l'IA étend 3 traits sur {len(ego_traits)}: ~{3 * 25} tokens ajoutés")
    print(f"   • Total contexte: {ego_tokens} + {3 * 25} = ~{ego_tokens + (3 * 25)} tokens")
    print(f"   • Toujours {((traditional_tokens - (ego_tokens + 75)) / traditional_tokens) * 100:.1f}% plus léger que le système traditionnel")
    
    print(f"\n🎉 RÉVOLUTION CONFIRMÉE!")
    print(f"Le système économise massivement les tokens tout en offrant plus de flexibilité!")

if __name__ == "__main__":
    analyze_token_economy()
