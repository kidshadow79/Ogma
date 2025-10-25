#!/usr/bin/env python3
"""
Analyse Mémoire Contextuelle Archiviste OGMA
============================================

Détermine la capacité mémoire exacte de l'archiviste et ce qu'il retient.
"""

import json
from pathlib import Path

def analyze_archiviste_memory_configuration():
    """Analyse la configuration mémoire de l'archiviste."""
    
    print("🧠 ANALYSE MÉMOIRE CONTEXTUELLE ARCHIVISTE")
    print("=" * 45)
    
    # 1. Configuration depuis settings.json (si existe)
    config_data = {}
    settings_path = Path("config.json")
    if settings_path.exists():
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            print(f"✅ Configuration chargée depuis {settings_path}")
        except Exception as e:
            print(f"❌ Erreur lecture config: {e}")
    
    # 2. Paramètres de l'archiviste dans reasoning_api
    print(f"\n🔧 CONFIGURATION ARCHIVISTE")
    print("-" * 30)
    
    reasoning_api = config_data.get('reasoning_api', {})
    
    # Paramètres par défaut si non configurés
    context_length = int(reasoning_api.get('context_length', 4096))
    max_tokens = int(reasoning_api.get('max_tokens', 512))
    backend_type = reasoning_api.get('backend_type', 'API')
    temperature = float(reasoning_api.get('temperature', 0.7))
    
    print(f"   Context Length: {context_length:,} tokens")
    print(f"   Max Tokens Output: {max_tokens} tokens")
    print(f"   Backend Type: {backend_type}")
    print(f"   Temperature: {temperature}")
    
    # 3. Calcul de la mémoire disponible pour contexte
    print(f"\n📊 CALCUL MÉMOIRE DISPONIBLE")
    print("-" * 35)
    
    # Estimation des tokens utilisés par le système
    system_prompt_tokens = 200  # Prompt système archiviste
    response_tokens = max_tokens  # Tokens réservés pour la réponse
    safety_margin = 100  # Marge de sécurité
    
    available_for_context = context_length - system_prompt_tokens - response_tokens - safety_margin
    
    print(f"   Total Context Length: {context_length:,} tokens")
    print(f"   - System Prompt: ~{system_prompt_tokens} tokens")
    print(f"   - Response Reserved: {response_tokens} tokens") 
    print(f"   - Safety Margin: {safety_margin} tokens")
    print(f"   = Disponible pour Contexte: {available_for_context:,} tokens")
    
    # 4. Estimation du nombre de souvenirs
    print(f"\n💾 ESTIMATION CAPACITÉ SOUVENIRS")
    print("-" * 40)
    
    # Tokens moyens par souvenir (estimation basée sur la structure)
    tokens_per_memory = 150  # titre + résumé + métadonnées + formatage JSON
    
    max_memories = available_for_context // tokens_per_memory
    
    print(f"   Tokens par souvenir: ~{tokens_per_memory} tokens")
    print(f"   Souvenirs max théorique: {max_memories} souvenirs")
    print(f"   Limité par code à: k=3 ou k=5 (selon contexte)")
    
    # 5. Types de contexte traités
    print(f"\n🔍 TYPES DE CONTEXTE ARCHIVISTE")
    print("-" * 40)
    
    context_types = [
        ("Personal Context", "k=3", "Souvenirs personnels pertinents"),
        ("Conversation Context", "k=5", "Contexte conversations passées"),
        ("Memory Synthesis", "Variable", "Synthèse de souvenirs spécifiques"),
        ("Ego Traits", "Tous", "Organisation des traits de personnalité")
    ]
    
    for context_type, limit, description in context_types:
        print(f"   • {context_type}: {limit}")
        print(f"     └─ {description}")
    
    # 6. Analyse du code pour les limites réelles
    print(f"\n📋 LIMITES DANS LE CODE")
    print("-" * 25)
    
    # Les limites trouvées dans le code
    code_limits = {
        "retrieve_and_synthesize_context (personal)": "k=3",
        "retrieve_and_synthesize_context (conversation)": "k=5", 
        "FAISS search": "Par défaut selon k",
        "Memory full synthesis": "Tous les souvenirs trouvés",
        "Context timeout": "10 secondes max"
    }
    
    for operation, limit in code_limits.items():
        print(f"   • {operation}: {limit}")
    
    return {
        'context_length': context_length,
        'max_tokens': max_tokens,
        'available_for_context': available_for_context,
        'max_memories_theoretical': max_memories,
        'personal_context_limit': 3,
        'conversation_context_limit': 5,
        'backend_type': backend_type
    }

def analyze_conversation_retention():
    """Analyse ce que l'archiviste retient de la conversation en cours."""
    
    print(f"\n💬 RÉTENTION CONVERSATION EN COURS")
    print("=" * 40)
    
    retention_info = [
        ("Conversation Actuelle", "❌ Non retenue directement"),
        ("Message Utilisateur", "✅ Transmis pour recherche"),
        ("Historique Messages", "❌ Pas d'accès direct à l'historique"),
        ("Contexte Conversations Passées", "✅ Via recherche FAISS (k=5)"),
        ("Souvenirs Personnels", "✅ Via recherche FAISS (k=3)"),
        ("Synthèse Précédente", "❌ Pas de mémoire inter-requêtes")
    ]
    
    for element, status in retention_info:
        status_icon = "✅" if "✅" in status else "❌"
        clean_status = status.replace("✅", "").replace("❌", "").strip()
        print(f"   {status_icon} {element}: {clean_status}")
    
    print(f"\n🔑 POINTS CLÉS:")
    print(f"   • L'archiviste ne garde PAS la conversation en cours")
    print(f"   • Il reçoit uniquement le message actuel pour recherche")
    print(f"   • Il accède aux conversations PASSÉES via FAISS")
    print(f"   • Chaque appel est indépendant (pas de mémoire persistante)")

if __name__ == "__main__":
    print("🧠 OGMA - ANALYSE MÉMOIRE ARCHIVISTE")
    print("===================================")
    
    config = analyze_archiviste_memory_configuration()
    analyze_conversation_retention()
    
    print(f"\n" + "=" * 60)
    print("🎯 RÉSUMÉ EXÉCUTIF:")
    print(f"   • Context Length: {config['context_length']:,} tokens")
    print(f"   • Souvenirs personnels: {config['personal_context_limit']} max")
    print(f"   • Contexte conversations: {config['conversation_context_limit']} max")
    print(f"   • Conversation actuelle: NON retenue")
    print(f"   • Mémoire inter-requêtes: NON")
    print("="*60)