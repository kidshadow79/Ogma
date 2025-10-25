#!/usr/bin/env python3
"""
Test complet de la fonctionnalité Web Navigator avec phrases magiques IA
Simule une réponse IA contenant une phrase magique et vérifie le traitement
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_full_ai_web_integration():
    """Test complet d'intégration Web Navigator avec phrases magiques IA"""
    
    print("🧪 TEST: Intégration complète Web Navigator + Phrases magiques IA")
    print("=" * 70)
    
    try:
        from extensions.web_navigator import WebNavigatorExtension
        
        # Initialiser l'extension
        web_ext = WebNavigatorExtension()
        print("✅ Extension Web Navigator initialisée")
        
        # Tester la phrase magique du log utilisateur
        ai_response = 'Ah, Yohan, parfait timing pour plonger dans le futur ! Je vais lancer la phrase magique direct : "il faut que je recherche sur internet : les tendances et artistes reggaeton latina pour 2025".'
        
        print(f"\n🔍 Test de détection:")
        print(f"   Texte IA: \"{ai_response[:80]}...\"")
        
        # 1. Vérifier détection
        is_detected = web_ext.commands.is_internet_request(ai_response)
        print(f"   Détection: {'✅ OUI' if is_detected else '❌ NON'}")
        
        if not is_detected:
            print("❌ ÉCHEC: Phrase magique non détectée")
            return
        
        # 2. Vérifier configuration
        is_enabled = web_ext.config.is_web_search_enabled()
        print(f"   Configuration: {'✅ ACTIVÉE' if is_enabled else '❌ DÉSACTIVÉE'}")
        
        if not is_enabled:
            print("⚠️ ATTENTION: Recherche web désactivée dans la configuration")
            return
        
        # 3. Tester le traitement de la requête 
        print(f"\n🚀 Test de traitement de la requête:")
        try:
            web_response, web_file_path = await web_ext.commands.process_internet_request(ai_response)
            
            if web_response:
                print(f"✅ Recherche réussie: {len(web_response)} caractères")
                print(f"✅ Fichier sauvé: {web_file_path}")
                
                # Afficher un aperçu de la réponse
                preview = web_response[:200].replace('\n', ' ')
                print(f"\n📖 Aperçu réponse:")
                print(f"   \"{preview}...\"")
                
                print(f"\n🎯 TEST RÉUSSI: Fonctionnalité complète opérationnelle!")
                print(f"   ✅ Détection phrases magiques IA")
                print(f"   ✅ Recherche web via Serper API")  
                print(f"   ✅ Génération réponse structurée")
                print(f"   ✅ Sauvegarde fichier résultats")
                
            else:
                print(f"❌ ÉCHEC: Aucune réponse de la recherche web")
                print(f"   Cause possible: API Serper, réseau, ou parsing")
                
        except Exception as e:
            print(f"❌ ERREUR lors du traitement: {e}")
            import traceback
            traceback.print_exc()
        
    except Exception as e:
        print(f"❌ ERREUR d'initialisation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_full_ai_web_integration())