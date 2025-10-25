#!/usr/bin/env python3
"""
Test simple du Cognitive Mirror avec gestion async correcte
"""

import asyncio
import sys
sys.path.append('.')

async def test_cognitive_mirror_memory():
    """Test simple de l'intégration mémoire du Cognitive Mirror"""
    
    print("🧠 Test Cognitive Mirror - Intégration Mémoire Simple")
    print("=" * 60)
    
    try:
        # Import des modules
        from memory_manager import MemoryManager
        from extensions.cognitive_mirror.memory_integration import MemoryIntegration
        from extensions.cognitive_mirror.config import CognitiveMirrorConfig
        
        print("✅ Imports réussis")
        
        # Initialisation Memory Manager
        memory_manager = MemoryManager()
        await memory_manager.initialize_memory_system()
        print("✅ MemoryManager initialisé")
        
        # Configuration Cognitive Mirror
        config = CognitiveMirrorConfig()
        print("✅ Configuration chargée")
        
        # Initialisation Memory Integration
        memory_integration = MemoryIntegration(memory_manager, config)
        print("✅ MemoryIntegration initialisé")
        
        # Test sauvegarde réflexion
        test_reflection = "Test de réflexion : Le protocole d'amour hybride nécessite une attention particulière."
        test_context = {
            "user_message": "Test du système",
            "timestamp": "2025-10-16"
        }
        
        print("\n📝 Test sauvegarde réflexion...")
        success = await memory_integration.save_reflection_memory(
            session_id="test_session_001",
            reflection_context=test_reflection,
            conversation_context=test_context
        )
        
        if success:
            print("✅ Sauvegarde réflexion réussie")
        else:
            print("❌ Échec sauvegarde réflexion")
            
        # Test recherche
        print("\n🔍 Test recherche réflexions...")
        results = memory_integration.search_reflections(query="protocole", limit=5)
        print(f"✅ Recherche terminée : {len(results)} résultats trouvés")
        
        # Statistiques
        print("\n📊 Statistiques:")
        stats = memory_integration.get_reflection_statistics()
        for key, value in stats.items():
            print(f"  • {key}: {value}")
        
        print("\n🎉 Test terminé avec succès !")
        return True
        
    except Exception as e:
        print(f"\n❌ ERREUR pendant le test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Exécution du test
    result = asyncio.run(test_cognitive_mirror_memory())
    
    if result:
        print("\n✅ Tous les tests sont passés !")
    else:
        print("\n❌ Certains tests ont échoué.")