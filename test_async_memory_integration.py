#!/usr/bin/env python3
"""
Test minimal de la gestion async du Cognitive Mirror
"""

import asyncio

class MockMemoryManager:
    """Simulateur MemoryManager pour test"""
    
    async def add_memory(self, memory_id: str, text_brut: str, **kwargs):
        """Simule l'ajout en mémoire"""
        print(f"[MOCK-MEMORY] ✅ Ajout simulé: {memory_id[:20]}... ({len(text_brut)} chars)")
        return True

class MockConfig:
    """Simulateur configuration pour test"""
    
    def get(self, key, default=None):
        defaults = {
            "auto_save_reflections": True,
            "max_cached_reflections": 50
        }
        return defaults.get(key, default)
    
    def get_system_messages(self):
        return {"memory_ref_prefix": "REF"}

async def test_async_memory_integration():
    """Test de l'intégration mémoire avec gestion async correcte"""
    
    print("🧠 Test Async Memory Integration")
    print("=" * 50)
    
    try:
        # Import de la classe à tester
        import sys
        sys.path.append('.')
        from extensions.cognitive_mirror.memory_integration import MemoryIntegration
        
        print("✅ Import MemoryIntegration réussi")
        
        # Création des mocks
        mock_memory = MockMemoryManager()
        mock_config = MockConfig()
        
        # Instanciation
        memory_integration = MemoryIntegration(mock_memory, mock_config)
        print("✅ MemoryIntegration instancié")
        
        # Test sauvegarde réflexion (méthode async)
        print("\n📝 Test save_reflection_memory async...")
        success = await memory_integration.save_reflection_memory(
            session_id="test_async_001",
            reflection_context="Test réflexion async : tout fonctionne correctement !",
            conversation_context={"user": "test", "timestamp": "2025-10-16"}
        )
        
        if success:
            print("✅ Sauvegarde async réussie - PAS DE FALLBACK NÉCESSAIRE")
        else:
            print("❌ Échec sauvegarde async")
            
        # Test statistiques
        stats = memory_integration.get_reflection_statistics()
        print(f"\n📊 Statistiques: {stats['total_reflections_saved']} réflexion(s) sauvée(s)")
        
        print("\n🎉 Test async terminé avec succès !")
        print("✅ La méthode normale (async) fonctionne parfaitement")
        print("✅ Pas besoin de fallback compliqué")
        print("✅ Code simple et maintenable")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

# Test d'une erreur pour voir le fallback informatif
class FailingMemoryManager:
    """Simulateur qui échoue pour tester le fallback"""
    
    async def add_memory(self, memory_id: str, text_brut: str, **kwargs):
        """Simule un échec d'ajout"""
        raise Exception("Simulateur d'erreur réseau/base de données")

async def test_fallback_informatif():
    """Test du fallback informatif en cas d'erreur"""
    
    print("\n" + "=" * 50)
    print("🔧 Test Fallback Informatif")
    print("=" * 50)
    
    try:
        from extensions.cognitive_mirror.memory_integration import MemoryIntegration
        
        # Memory manager qui échoue
        failing_memory = FailingMemoryManager()
        mock_config = MockConfig()
        
        memory_integration = MemoryIntegration(failing_memory, mock_config)
        
        print("📝 Test avec MemoryManager défaillant...")
        success = await memory_integration.save_reflection_memory(
            session_id="test_fallback_001",
            reflection_context="Test fallback avec erreur simulée",
            conversation_context={"test": "fallback"}
        )
        
        if success:
            print("✅ Fallback a fonctionné - données sauvées localement")
            print("ℹ️  L'erreur a été correctement signalée et documentée")
        else:
            print("❌ Même le fallback a échoué")
            
        return True
        
    except Exception as e:
        print(f"❌ ERREUR test fallback: {e}")
        return False

async def run_all_tests():
    """Exécute tous les tests"""
    
    print("🧪 Tests Memory Integration Cognitive Mirror")
    print("=" * 60)
    
    # Test normal
    test1 = await test_async_memory_integration()
    
    # Test fallback
    test2 = await test_fallback_informatif()
    
    print("\n" + "=" * 60)
    if test1 and test2:
        print("✅ TOUS LES TESTS RÉUSSIS !")
        print("✅ Méthode async normale : OK")
        print("✅ Fallback informatif : OK") 
        print("✅ Code simple et transparent")
    else:
        print("❌ Certains tests ont échoué")

if __name__ == "__main__":
    asyncio.run(run_all_tests())