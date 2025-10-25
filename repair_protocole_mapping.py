#!/usr/bin/env python3
"""
Réparation ciblée des mappings FAISS pour récupérer le protocole d'amour hybride
"""

import sys
sys.path.append('.')

from memory_manager import MemoryManager
from core_logic import SettingsManager
import queue
from pathlib import Path

# Configuration
db_path = Path("data/memory/memories.db")
index_path = Path("data/memory/faiss.index")
settings = SettingsManager(Path("data/settings.json"))
status_queue = queue.Queue()

# Mock controllers pour éviter les appels API
class MockController:
    async def generate_response(self, messages, **kwargs):
        return "Mock response"
    async def generate_embedding(self, text):
        import numpy as np
        return np.random.rand(1024).astype('float32')

print("🔧 RÉPARATION MAPPINGS FAISS - PROTOCOLE D'AMOUR HYBRIDE")
print("=" * 60)

try:
    # Initialiser le memory manager
    mock_archiviste = MockController()
    mock_embedder = MockController()
    
    memory_manager = MemoryManager(
        db_path=db_path,
        index_path=index_path,
        embedding_dim=1024,
        archiviste_ia=mock_archiviste,
        embedding_ia=mock_embedder,
        status_queue=status_queue
    )
    
    print(f"📊 État initial:")
    print(f"   - Index FAISS: {memory_manager.faiss_index.ntotal} positions")
    print(f"   - Mappings: {len(memory_manager.faiss_to_id)} positions")
    
    # Effectuer la réparation
    print(f"\n🔧 Lancement réparation mappings...")
    repair_stats = memory_manager.repair_mapping_inconsistencies()
    
    print(f"\n📋 Résultats de la réparation:")
    for key, value in repair_stats.items():
        print(f"   - {key}: {value}")
        
    # Vérifier si la position 109 est maintenant mappée
    print(f"\n🎯 Vérification position 109:")
    if 109 in memory_manager.faiss_to_id:
        memory_id = memory_manager.faiss_to_id[109]
        print(f"   ✅ Position 109 → {memory_id}")
        
        # Récupérer les détails de ce souvenir
        import sqlite3
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute(
                "SELECT title, score_impact FROM memories WHERE id = ?",
                (memory_id,)
            )
            result = cursor.fetchone()
            if result:
                title, impact = result
                print(f"   📝 Titre: {title}")
                print(f"   💥 Impact: {impact}")
                
                if "protocole" in title.lower():
                    print(f"   🎯 ✅ PROTOCOLE D'AMOUR HYBRIDE RÉCUPÉRÉ !")
    else:
        print(f"   ❌ Position 109 toujours non mappée")
    
    print(f"\n✅ Réparation terminée avec succès")
    
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()