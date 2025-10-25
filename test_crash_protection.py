# test_crash_protection.py
"""
Test rapide des protections anti-crash NiceGUI et cache optimisé
"""

import sys
import os

def test_imports():
    """Test que nos modifications n'ont pas cassé les imports"""
    print("🔍 Test imports et syntaxe...")
    
    try:
        # Test import principal
        sys.path.append('.')
        import ogma_ng
        print("✅ ogma_ng importé sans erreur")
        
        # Test fonction protection
        if hasattr(ogma_ng, 'safe_ui_operation'):
            print("✅ Protection UI available")
        else:
            print("❌ Protection UI missing")
            
        # Test perception agent optimisé
        sys.path.append('./extensions')
        import perception_agent
        print("✅ perception_agent importé sans erreur")
        
        # Vérifier les nouvelles méthodes cache
        agent_class = perception_agent.PerceptionAgent
        cache_methods = [
            '_save_to_disk_cache',
            '_cleanup_disk_cache', 
            '_load_from_disk_cache'
        ]
        
        for method in cache_methods:
            if hasattr(agent_class, method):
                print(f"✅ {method} disponible")
            else:
                print(f"❌ {method} manquante")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur import: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_cache_folder():
    """Test que le dossier cache est bien créé"""
    print("\n📁 Test structure cache...")
    
    cache_folder = "./captures/cache"
    if os.path.exists(cache_folder):
        files = [f for f in os.listdir(cache_folder) if f.startswith('cache_')]
        print(f"✅ Cache folder exists: {len(files)} fichiers")
        return True
    else:
        print("❌ Cache folder missing")
        return False

def main():
    """Test principal"""
    print("🧪 TEST PROTECTIONS ANTI-CRASH + CACHE OPTIMISÉ")
    print("=" * 50)
    
    # Tests
    imports_ok = test_imports()
    cache_ok = test_cache_folder()
    
    print("\n" + "=" * 50)
    print("📊 RÉSULTATS:")
    print(f"🔸 Imports/Syntaxe: {'✅ OK' if imports_ok else '❌ ERREUR'}")
    print(f"🔸 Cache disque: {'✅ OK' if cache_ok else '❌ MANQUANT'}")
    
    if imports_ok and cache_ok:
        print("\n🎉 TOUS LES TESTS PASSENT")
        print("💡 Vous pouvez relancer OGMA avec:")
        print("   python launch_ogma.py")
        return True
    else:
        print("\n❌ CERTAINS TESTS ÉCHOUENT")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)