#!/usr/bin/env python3
"""
Test complet d'une recherche web déclenchée par l'IA elle-même
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from extensions.web_navigator import WebNavigatorExtension

async def test_ai_triggered_search():
    """Test complet d'une recherche web déclenchée par l'IA"""
    
    print("🤖 Test de recherche web déclenchée par l'IA")
    print("=" * 50)
    
    # Initialiser l'extension
    ext = WebNavigatorExtension()
    
    # Messages que l'IA pourrait générer
    ai_messages = [
        "il faut que je recherche sur le net les dernières nouvelles sur l'intelligence artificielle",
        "je dois vérifier en ligne la météo de Paris aujourd'hui",
        "il faut que je cherche sur internet des informations sur Python 3.12"
    ]
    
    for i, message in enumerate(ai_messages, 1):
        print(f"\n🧠 Test {i}: Message IA")
        print(f"Message: '{message}'")
        print("-" * 40)
        
        # Vérifier la détection
        is_detected = ext.commands.is_internet_request(message)
        print(f"✓ Détection: {'OUI' if is_detected else 'NON'}")
        
        if is_detected:
            # Extraire l'intention et la requête
            intent, query = ext.commands.extract_search_intent_and_query(message)
            print(f"✓ Type: {intent}")
            print(f"✓ Requête: '{query}'")
            
            # Faire la vraie recherche
            print(f"\n🌐 Exécution de la recherche...")
            
            try:
                result, file_path = await ext.commands.process_internet_request(message)
                
                if result:
                    print(f"✅ Recherche réussie!")
                    print(f"📝 Résultat ({len(result)} caractères):")
                    
                    # Afficher un extrait du résultat
                    lines = result.split('\n')
                    for line in lines[:10]:  # Afficher les 10 premières lignes
                        if line.strip():
                            print(f"   {line}")
                    
                    if len(lines) > 10:
                        print(f"   ... ({len(lines) - 10} lignes supplémentaires)")
                    
                    if file_path:
                        print(f"📁 Fichier sauvegardé: {file_path}")
                        
                else:
                    print("❌ Échec de la recherche")
                    
            except Exception as e:
                print(f"❌ Erreur lors de la recherche: {e}")
        
        print("\n" + "="*50)
        
        # Petite pause entre les tests
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(test_ai_triggered_search())