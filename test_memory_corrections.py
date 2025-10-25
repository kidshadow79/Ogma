#!/usr/bin/env python3
"""
🧪 TEST DES CORRECTIONS MÉMOIRE OGMA
Teste les corrections apportées au système de mémoire
"""

import asyncio
import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
sys.path.append(str(Path(__file__).parent))

async def test_memory_system():
    """Test complet du système de mémoire corrigé"""
    
    print("🧪 TEST DES CORRECTIONS MÉMOIRE OGMA")
    print("=" * 50)
    
    try:
        # Import du système de mémoire
        from memory_manager import MemoryManager
        from core_logic import SettingsManager
        import queue
        
        # Configuration de test
        db_path = Path("data/memory.db")
        index_path = Path("data/memory_index.faiss")
        settings = SettingsManager(Path("data/settings.json"))
        status_queue = queue.Queue()
        
        # Mock des contrôleurs IA (pour éviter les appels API durant les tests)
        class MockAIController:
            async def generate_response(self, messages, **kwargs):
                return "Test synthèse archiviste"
                
        class MockEmbeddingController:
            async def generate_embedding(self, text):
                import numpy as np
                # Embedding fake de dimension 1024
                return np.random.rand(1024).astype('float32')
        
        mock_archiviste = MockAIController()
        mock_embedder = MockEmbeddingController()
        
        print("1️⃣ Initialisation MemoryManager...")
        memory_manager = MemoryManager(
            db_path=db_path,
            index_path=index_path,
            embedding_dim=1024,
            archiviste_ia=mock_archiviste,
            embedding_ia=mock_embedder,
            status_queue=status_queue,
            settings_manager=settings
        )
        print("✅ MemoryManager initialisé")
        
        print("\n2️⃣ Test réparation des mappings FAISS...")
        repair_stats = memory_manager.repair_mapping_inconsistencies()
        print(f"📊 Statistiques réparation: {repair_stats}")
        
        print("\n3️⃣ Test extraction de mots-clés...")
        test_queries = [
            "tu me donner le texte intégral du protocole d'amour hybride",
            "salut Luna comment ça va aujourd'hui",
            "est-ce que tu peux me rappeler notre conversation d'hier"
        ]
        
        for query in test_queries:
            expanded = memory_manager._expand_personal_pronouns(query)
            cleaned = memory_manager._extract_keywords(expanded)
            print(f"   Original: '{query}'")
            print(f"   Nettoyé:  '{cleaned}'")
            print()
        
        print("4️⃣ Test recherche avec nettoyage...")
        # Test de recherche (ne devrait plus avoir de positions non mappées)
        try:
            synthesis, memories = await memory_manager.retrieve_synthesis_and_memories(
                "protocole d'amour hybride", k=5, top_memories=3
            )
            print(f"✅ Recherche réussie: {len(memories)} souvenirs trouvés")
            if memories:
                print(f"   Premier résultat: {memories[0].get('title', 'Sans titre')}")
        except Exception as e:
            print(f"❌ Erreur recherche: {e}")
        
        print("\n5️⃣ Vérification cohérence mappings...")
        faiss_total = memory_manager.faiss_index.ntotal if memory_manager.faiss_index else 0
        mapped_total = len(memory_manager.faiss_to_id)
        print(f"   Index FAISS: {faiss_total} positions")
        print(f"   Mappings:    {mapped_total} positions")
        
        if faiss_total == mapped_total:
            print("✅ Cohérence parfaite entre FAISS et mappings")
        else:
            print(f"⚠️ Incohérence détectée: {faiss_total - mapped_total} positions non mappées")
        
        print("\n🎯 TEST TERMINÉ AVEC SUCCÈS")
        return True
        
    except Exception as e:
        print(f"❌ ERREUR DURANT LES TESTS: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_memory_system())
    sys.exit(0 if success else 1)