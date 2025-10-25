#!/usr/bin/env python3
"""
Test du nouveau formatage synthétique pour Web Navigator
Vérifie que les résultats sont maintenant exploitables par l'IA
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_synthetic_formatting():
    """Test du nouveau formatage synthétique"""
    
    print("🧪 TEST: Nouveau formatage synthétique Web Navigator")
    print("=" * 70)
    
    try:
        from extensions.web_navigator import WebNavigatorExtension
        
        # Initialiser l'extension
        web_ext = WebNavigatorExtension()
        print("✅ Extension Web Navigator initialisée")
        
        # Test avec requête similaire à celle de l'utilisateur
        test_query = "avancées ia relations émotionnelles intimes 2024-2025"
        
        print(f"\n🔍 Test formatage synthétique:")
        print(f"   Requête: \"{test_query}\"")
        
        # Tester le traitement complet
        web_response, web_file_path = await web_ext.commands.process_internet_request(
            f"il faut que je cherche sur internet {test_query}"
        )
        
        if web_response:
            print(f"\n✅ Réponse synthétisée générée: {len(web_response)} caractères")
            
            # Analyser le contenu pour vérifier la synthèse
            print(f"\n📖 Aperçu du nouveau format:")
            print("=" * 50)
            
            # Afficher les 800 premiers caractères pour voir la structure
            preview = web_response[:800]
            print(preview)
            
            if len(web_response) > 800:
                print(f"\n... [+{len(web_response)-800} caractères supplémentaires]")
            
            print("\n" + "=" * 50)
            
            # Vérifier les améliorations
            improvements = []
            if "Points clés identifiés" in web_response:
                improvements.append("✅ Synthèse des points clés")
            if "Sources consultées" in web_response:
                improvements.append("✅ Références sources simplifiées")
            if "En résumé" in web_response:
                improvements.append("✅ Conclusion actionnable")
            if "Synthèse Web" in web_response:
                improvements.append("✅ Format exploitable par l'IA")
            
            # Vérifier l'absence de l'ancien format
            old_format_indicators = [
                "🔗 https://",  # Liens directs
                "📄",  # Descriptions brutes
                "[RECHERCHE WEB SERPER]"  # Ancien header
            ]
            
            reduced_noise = []
            for indicator in old_format_indicators:
                count = web_response.count(indicator)
                if count < 3:  # Considérablement réduit
                    reduced_noise.append(f"✅ Réduction du bruit: {indicator}")
            
            print(f"\n🎯 AMÉLIORATIONS DÉTECTÉES:")
            for improvement in improvements:
                print(f"  {improvement}")
            
            print(f"\n🧹 RÉDUCTION DU BRUIT:")
            for noise in reduced_noise:
                print(f"  {noise}")
            
            if len(improvements) >= 3:
                print(f"\n🎉 TEST RÉUSSI: Format synthétique opérationnel!")
                print(f"   ✅ L'IA peut maintenant exploiter directement ces informations")
                print(f"   ✅ Format plus conversationnel et actionnable")
                print(f"   ✅ Réduction significative du bruit informationnel")
            else:
                print(f"\n⚠️ Format partiellement amélioré - besoin d'ajustements")
                
        else:
            print(f"❌ ÉCHEC: Aucune réponse générée")
            
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_synthetic_formatting())