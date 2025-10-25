#!/usr/bin/env python3
"""
Vérifier l'état actuel de la configuration OGMA
"""

import json

def check_config():
    print("🤖 VÉRIFICATION CONFIGURATION OGMA")
    print("=" * 50)
    
    try:
        with open('data/settings.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        chat_api = config.get('chat_api', {})
        reasoning_api = config.get('reasoning_api', {})
        
        print("📋 IA PRINCIPALE (chat_api):")
        print(f"   Provider: {chat_api.get('provider', 'Non défini')}")
        print(f"   Modèle: {chat_api.get('model', 'Non défini')}")
        print(f"   api_model: {chat_api.get('api_model', 'Non présent')}")
        print(f"   Context: {chat_api.get('context_length', 'Non défini')} tokens")
        print(f"   Max tokens: {chat_api.get('max_tokens', 'Non défini')}")
        print()
        
        print("🧠 ARCHIVISTE (reasoning_api):")
        print(f"   Provider: {reasoning_api.get('provider', 'Non défini')}")
        print(f"   Modèle: {reasoning_api.get('model', 'Non défini')}")
        print(f"   Max tokens: {reasoning_api.get('max_tokens', 'Non défini')}")
        print()
        
        print("🎯 ANALYSE:")
        if chat_api.get('provider') == 'Mistral' and 'pixtral' in str(chat_api.get('model', '')).lower():
            print("   ❌ Config.json montre Mistral/Pixtral")
            print("   ✅ Mais si l'IA dit être GPT-5, alors GPT-5 est réellement actif!")
            print("   💡 La config en mémoire diffère du fichier config.json")
        elif chat_api.get('provider') == 'OpenAI':
            print("   ✅ Config.json confirme OpenAI")
            print("   🎯 Cohérent avec GPT-5 actif")
        else:
            print(f"   ❓ Provider: {chat_api.get('provider')}")
            
    except Exception as e:
        print(f"❌ Erreur lecture config: {e}")

if __name__ == "__main__":
    check_config()