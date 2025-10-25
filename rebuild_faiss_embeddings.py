#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rebuild_faiss_embeddings.py
---------------------------
Script pour reconstruire l'index FAISS avec les nouveaux embeddings
qui incluent le texte original (pas seulement titre + résumé)
"""

import asyncio
import sys
import os
from pathlib import Path

# Imports OGMA
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from memory_manager import MemoryManager
from core_logic import SettingsManager, OllamaManager, GGUFManager, KoboldManager, AIController, EmbeddingController
from utils import DATA_DIR
import queue


async def rebuild_faiss_embeddings():
    """Reconstruit l'index FAISS avec les nouveaux embeddings complets"""
    
    print("=" * 60)
    print("REBUILD INDEX FAISS - NOUVEAUX EMBEDDINGS")
    print("=" * 60)
    print()
    
    # Initialisation
    print("📋 Initialisation MemoryManager...")
    
    settings_manager = SettingsManager(DATA_DIR / "settings.json")
    s = settings_manager.settings
    
    ollama_manager = OllamaManager()
    gguf_manager = GGUFManager() 
    kobold_manager = KoboldManager()
    
    memory_ai_controller = AIController("Archiviste", ollama_manager, gguf_manager, kobold_manager)
    embedding_controller = EmbeddingController(ollama_manager, gguf_manager)
    
    memory_ai_controller.set_active_backend(s['reasoning_api'].get('backend_type', 'API'))
    memory_ai_controller.max_tokens = 1500
    
    status_queue = queue.Queue()
    
    memory_manager = MemoryManager(
        db_path=DATA_DIR / "memory" / "memories.db",
        index_path=DATA_DIR / "memory" / "faiss_index.bin", 
        embedding_dim=1024,
        archiviste_ia=memory_ai_controller,
        embedding_ia=embedding_controller,
        status_queue=status_queue
    )
    
    print(f"✅ MemoryManager initialisé")
    
    # Rebuild FAISS
    print("\n🔄 Reconstruction index FAISS...")
    stats = memory_manager.rebuild_faiss_index()
    
    print(f"\n📊 STATISTIQUES REBUILD :")
    print(f"   • Souvenirs traités: {stats.get('processed', 0)}")
    print(f"   • Embeddings générés: {stats.get('embeddings_generated', 0)}")
    print(f"   • Erreurs: {stats.get('errors', 0)}")
    print(f"   • Index final: {memory_manager.get_memory_count()} vecteurs")
    
    print("\n🔍 Test post-rebuild...")
    
    # Test recherche après rebuild
    test_queries = ["taille pénis", "pénis", "anatomie intime"]
    
    for query in test_queries:
        print(f"\n🔎 Test '{query}':")
        
        try:
            results = memory_manager.search_memories(
                query=query,
                limit=3,
                threshold=0.2
            )
            
            print(f"   📋 {len(results)} résultats")
            for i, result in enumerate(results):
                impact = result.get('score_impact', 0)
                similarity = result.get('similarity', 0)
                title = result.get('title', 'N/A')
                
                print(f"   {i+1}. Impact:{impact:.1f} | Sim:{similarity:.3f} | {title}")
                
                if impact >= 180:
                    print(f"      🎯 HAUTE PRIORITÉ trouvée!")
                    
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
    
    print("\n✅ Rebuild terminé!")
    print("\n💡 L'IA Principale devrait maintenant trouver les contenus intimes")
    print("   même si les mots-clés ne sont que dans le texte original !")


if __name__ == "__main__":
    asyncio.run(rebuild_faiss_embeddings())