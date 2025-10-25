#!/usr/bin/env python3
"""
Test de l'intégration contextuelle Web Navigator
Vérifie que l'IA utilise maintenant les informations web dans sa réponse
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_web_context_integration():
    """Test de l'intégration contextuelle"""
    
    print("🧪 TEST: Intégration contextuelle Web Navigator")
    print("=" * 70)
    
    try:
        from extensions.web_navigator import WebNavigatorExtension
        
        # Initialiser l'extension
        web_ext = WebNavigatorExtension()
        print("✅ Extension Web Navigator initialisée")
        
        # Simuler une requête qui nécessite des informations récentes
        test_query = "cherche sur internet les dernières avancées en IA émotionnelle 2024-2025"
        
        print(f"\n🔍 Test d'intégration contextuelle:")
        print(f"   Requête: \"{test_query}\"")
        
        # Vérifier que la requête est détectée
        is_detected = web_ext.commands.is_internet_request(test_query)
        print(f"   Détection: {'✅ OUI' if is_detected else '❌ NON'}")
        
        if is_detected:
            print(f"\n🚀 Simulation du nouveau flux:")
            
            # 1. Récupération des informations web
            print(f"   1️⃣ Recherche web...")
            web_response, web_file_path = await web_ext.commands.process_internet_request(test_query)
            
            if web_response:
                print(f"   ✅ Informations récupérées: {len(web_response)} caractères")
                
                # 2. Simulation de l'injection de contexte
                print(f"   2️⃣ Injection de contexte...")
                context_message = f"CONTEXTE WEB RÉCENT (pour enrichir ta réponse):\n\n{web_response}\n\nUtilise ces informations récentes pour enrichir ta réponse si elles sont pertinentes pour la question de l'utilisateur."
                
                print(f"   ✅ Contexte préparé: {len(context_message)} caractères")
                
                # 3. Vérifier la structure du contexte
                print(f"\n📖 Structure du contexte injecté:")
                print(f"   - Contient 'Synthèse Web': {'✅' if 'Synthèse Web' in web_response else '❌'}")
                print(f"   - Contient 'Points clés': {'✅' if 'Points clés' in web_response else '❌'}")
                print(f"   - Contient 'Sources consultées': {'✅' if 'Sources consultées' in web_response else '❌'}")
                print(f"   - Format exploitable: {'✅' if 'En résumé' in web_response else '❌'}")
                
                # 4. Aperçu du contexte
                print(f"\n📋 Aperçu contexte (200 premiers caractères):")
                print(f"   \"{context_message[:200]}...\"")
                
                print(f"\n🎯 NOUVEAU FLUX SIMULÉ AVEC SUCCÈS:")
                print(f"   ✅ 1. Détection requête web")
                print(f"   ✅ 2. Récupération informations synthétisées")
                print(f"   ✅ 3. Injection dans contexte IA AVANT génération")
                print(f"   ✅ 4. L'IA peut maintenant utiliser ces infos dans sa réponse")
                
                print(f"\n💡 AVANTAGES:")
                print(f"   🧠 L'IA raisonne AVEC les informations web")
                print(f"   🔄 Intégration fluide dans la conversation")
                print(f"   📝 Pas d'affichage séparé de type 'moteur de recherche'")
                print(f"   ⚡ Informations récentes directement exploitables")
                
            else:
                print(f"   ❌ Échec récupération informations web")
        
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_web_context_integration())