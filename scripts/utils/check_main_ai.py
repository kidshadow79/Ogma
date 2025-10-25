#!/usr/bin/env python3
"""
Vérification Configuration IA Principale
=========================================

Vérifie la configuration actuelle de l'IA principale et ses capacités.
"""

import json
from pathlib import Path

def check_main_ai_config():
    """Vérifie la configuration de l'IA principale."""
    
    print("🤖 VÉRIFICATION IA PRINCIPALE")
    print("=" * 35)
    
    # Lire la configuration
    config_path = Path("config.json")
    if not config_path.exists():
        print("❌ config.json introuvable")
        return
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)
    
    chat_config = config.get('chat_api', {})
    
    print(f"\n📋 CONFIGURATION ACTUELLE:")
    print("-" * 30)
    print(f"   Provider: {chat_config.get('provider', 'NON DÉFINI')}")
    print(f"   Model: {chat_config.get('model', 'NON DÉFINI')}")
    print(f"   Max Tokens: {chat_config.get('max_tokens', 'NON DÉFINI')}")
    print(f"   Context Length: {chat_config.get('context_length', 'NON DÉFINI')}")
    print(f"   Temperature: {chat_config.get('temperature', 'NON DÉFINI')}")
    
    # Vérifier si c'est GPT-5
    provider = chat_config.get('provider', '').lower()
    model = chat_config.get('model', '')
    
    print(f"\n🔍 ANALYSE:")
    print("-" * 15)
    
    if provider == 'openai' and 'gpt-5' in model.lower():
        print(f"   ✅ GPT-5 détecté!")
    elif provider == 'openai':
        print(f"   ℹ️ OpenAI détecté mais pas GPT-5: {model}")
    elif provider == 'mistral':
        print(f"   ℹ️ Mistral détecté: {model}")
        print(f"   ⚠️ Ce n'est PAS GPT-5!")
    else:
        print(f"   ℹ️ Provider: {provider}, Model: {model}")
        print(f"   ⚠️ Ce n'est PAS GPT-5!")
    
    return chat_config

def check_auto_detect_capabilities(chat_config):
    """Vérifie les capacités avec auto-detect."""
    
    print(f"\n🔧 AUTO-DETECT CAPACITÉS:")
    print("-" * 30)
    
    try:
        from model_capabilities import auto_detect_capabilities
        
        provider = chat_config.get('provider', '').lower()
        model = chat_config.get('model', '')
        
        if provider and model:
            detected_caps = auto_detect_capabilities(provider, model, 'chat')
            
            print(f"   Provider: {provider}")
            print(f"   Model: {model}")
            print(f"   Context Length Auto-Détecté: {detected_caps['context_length']:,} tokens")
            print(f"   Max Tokens Auto-Détecté: {detected_caps['max_tokens']:,} tokens")
            
            # Comparaison avec config actuelle
            current_context = chat_config.get('context_length', 0)
            current_max = chat_config.get('max_tokens', 0)
            
            print(f"\n   📊 COMPARAISON:")
            print(f"      Context Length:")
            print(f"         Config: {current_context:,}")
            print(f"         Auto-Detect: {detected_caps['context_length']:,}")
            
            if detected_caps['context_length'] > current_context:
                ratio = detected_caps['context_length'] / current_context if current_context > 0 else float('inf')
                print(f"         🚀 Gain possible: +{ratio:.1f}x")
            elif detected_caps['context_length'] == current_context:
                print(f"         ✅ Optimal")
            else:
                print(f"         ⚠️ Config supérieure à auto-detect")
            
            print(f"\n      Max Tokens:")
            print(f"         Config: {current_max:,}")
            print(f"         Auto-Detect: {detected_caps['max_tokens']:,}")
            
        else:
            print(f"   ❌ Impossible d'auto-détecter: provider ou model manquant")
    
    except Exception as e:
        print(f"   ❌ Erreur auto-detect: {e}")

def check_gpt5_availability():
    """Vérifie la disponibilité GPT-5 dans la base de données."""
    
    print(f"\n🔍 VÉRIFICATION GPT-5:")
    print("-" * 25)
    
    try:
        from model_capabilities import MODEL_CAPABILITIES
        
        # Rechercher GPT-5 dans la base
        gpt5_found = False
        
        for provider, models in MODEL_CAPABILITIES.items():
            for model_name, caps in models.items():
                if 'gpt-5' in model_name.lower():
                    gpt5_found = True
                    print(f"   ✅ GPT-5 trouvé dans {provider}:")
                    print(f"      Model: {model_name}")
                    print(f"      Context Length: {caps['context_length']:,} tokens")
                    print(f"      Max Tokens: {caps['max_tokens']:,} tokens")
        
        if not gpt5_found:
            print(f"   ⚠️ GPT-5 non trouvé dans la base de données")
            print(f"   💡 Modèles OpenAI disponibles:")
            
            openai_models = MODEL_CAPABILITIES.get('openai', {})
            for model_name in openai_models.keys():
                print(f"      - {model_name}")
    
    except Exception as e:
        print(f"   ❌ Erreur vérification GPT-5: {e}")

def suggest_gpt5_config():
    """Suggère une configuration GPT-5 si disponible."""
    
    print(f"\n💡 SUGGESTION CONFIGURATION:")
    print("-" * 35)
    
    print(f"   Pour utiliser GPT-5 (si disponible):")
    print(f"   {{")
    print(f"     \"provider\": \"OpenAI\",")
    print(f"     \"model\": \"gpt-5\",")
    print(f"     \"max_tokens\": -1,")
    print(f"     \"context_length\": -1")
    print(f"   }}")
    print(f"\n   Les valeurs -1 activent l'auto-detect pour utiliser")
    print(f"   les vraies capacités de GPT-5 via l'API.")

if __name__ == "__main__":
    print("🧠 OGMA - VÉRIFICATION IA PRINCIPALE")
    print("====================================")
    
    chat_config = check_main_ai_config()
    
    if chat_config:
        check_auto_detect_capabilities(chat_config)
        check_gpt5_availability()
        suggest_gpt5_config()
    
    print(f"\n" + "=" * 50)
    print("✅ VÉRIFICATION TERMINÉE")
    print("=" * 50)