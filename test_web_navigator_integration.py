#!/usr/bin/env python3
"""
Diagnostic de l'extension Web Navigator dans logic_callbacks.py
"""

import sys
from pathlib import Path

# Ajouter le répertoire racine au path
sys.path.insert(0, str(Path(__file__).parent))

def test_web_navigator_integration():
    """Test d'intégration de l'extension Web Navigator"""
    print("🔍 Test d'intégration Web Navigator dans logic_callbacks...")
    
    try:
        # Test 1: Import de logic_callbacks
        print("\n1. Test import logic_callbacks...")
        from logic_callbacks import _init_web_navigator_extension
        print("✅ Import logic_callbacks réussi")
        
        # Test 2: Initialisation de l'extension
        print("\n2. Test initialisation extension...")
        web_nav_ext = _init_web_navigator_extension()
        
        if web_nav_ext is None:
            print("❌ Extension Web Navigator non initialisée (None)")
            return False
        
        print("✅ Extension Web Navigator initialisée")
        print(f"   - Type: {type(web_nav_ext)}")
        print(f"   - Config: {type(web_nav_ext.config)}")
        print(f"   - Commands: {type(web_nav_ext.commands)}")
        print(f"   - Client: {type(web_nav_ext.serper_client)}")
        
        # Test 3: Vérification des méthodes
        print("\n3. Test méthodes extension...")
        
        if not hasattr(web_nav_ext.commands, 'is_internet_request'):
            print("❌ Méthode is_internet_request manquante")
            return False
        
        if not hasattr(web_nav_ext.commands, 'process_internet_request'):
            print("❌ Méthode process_internet_request manquante") 
            return False
        
        print("✅ Méthodes extension présentes")
        
        # Test 4: Test détection phrases magiques
        print("\n4. Test détection phrases magiques...")
        
        test_phrases = [
            "/web premier ministre francais",
            "cherche sur internet intelligence artificielle",
            "actualités sur technologie",
            "/image chat mignon",
            "bonjour comment allez-vous"  # phrase normale
        ]
        
        for phrase in test_phrases:
            try:
                is_web = web_nav_ext.commands.is_internet_request(phrase)
                status = "🌐 WEB" if is_web else "💬 NORMAL"
                print(f"   {status}: '{phrase}'")
            except Exception as e:
                print(f"   ❌ ERREUR: '{phrase}' -> {e}")
                return False
        
        # Test 5: Configuration
        print("\n5. Test configuration...")
        print(f"   - Extension activée: {web_nav_ext.config.is_enabled()}")
        print(f"   - Clé API configurée: {'Oui' if web_nav_ext.config.has_valid_api_key() else 'Non'}")
        print(f"   - Recherche web activée: {web_nav_ext.config.is_web_search_enabled()}")
        
        if not web_nav_ext.config.has_valid_api_key():
            print("⚠️ ATTENTION: Pas de clé API Serper configurée - les recherches échoueront")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("DIAGNOSTIC INTÉGRATION WEB NAVIGATOR")
    print("=" * 70)
    
    success = test_web_navigator_integration()
    
    print("\n" + "=" * 70)
    if success:
        print("✅ DIAGNOSTIC RÉUSSI - Extension Web Navigator intégrée correctement")
        print("\nSi les recherches ne marchent pas:")
        print("1. Vérifiez que vous avez configuré une clé API Serper")
        print("2. Essayez les phrases magiques: '/web REQUÊTE' ou 'cherche sur internet SUJET'")
        print("3. Regardez les logs OGMA pour voir si [WEB-NAV] apparaît")
    else:
        print("❌ DIAGNOSTIC ÉCHOUÉ - Problème d'intégration détecté")
    print("=" * 70)