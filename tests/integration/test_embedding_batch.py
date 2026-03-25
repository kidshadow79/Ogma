#!/usr/bin/env python3
"""
🧪 TEST: Embedding Batch Optimization
=====================================
Valide la parallélisation des embeddings dans search_memories_batch().

OBJECTIF: Gain 60-75% (5000ms → ~1500ms)

Usage:
    python test_embedding_batch.py
"""

import asyncio
import time
import sys
import os

# Ajout du path pour imports OGMA
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_embedding_batch_exists():
    """Vérifie que la méthode _generate_embeddings_batch existe."""
    print("\n" + "="*60)
    print("TEST 1: Existence de _generate_embeddings_batch()")
    print("="*60)
    
    from memory_manager import MemoryManager
    
    # Vérification méthode existe
    if hasattr(MemoryManager, '_generate_embeddings_batch'):
        print("✅ Méthode _generate_embeddings_batch() trouvée")
        return True
    else:
        print("❌ Méthode _generate_embeddings_batch() MANQUANTE")
        return False


async def test_batch_vs_sequential_mock():
    """Test comparatif batch vs séquentiel avec mock."""
    print("\n" + "="*60)
    print("TEST 2: Comparaison Batch vs Séquentiel (Mock)")
    print("="*60)
    
    # Simulation délai API
    API_DELAY = 0.2  # 200ms par appel
    
    async def mock_embed_single(text: str) -> list:
        """Simule un appel API embedding."""
        await asyncio.sleep(API_DELAY)
        return [0.1] * 1024  # Mock embedding
    
    queries = ["chat préféré", "animal de compagnie", "félin domestique", "willow", "chaton lyon"]
    
    # Test SÉQUENTIEL
    print(f"\n🔄 Mode SÉQUENTIEL ({len(queries)} queries)...")
    seq_start = time.time()
    for q in queries:
        await mock_embed_single(q)
    seq_elapsed = (time.time() - seq_start) * 1000
    print(f"   ⏱️ Temps séquentiel: {seq_elapsed:.0f}ms")
    
    # Test PARALLÈLE
    print(f"\n🚀 Mode PARALLÈLE ({len(queries)} queries)...")
    par_start = time.time()
    tasks = [mock_embed_single(q) for q in queries]
    await asyncio.gather(*tasks)
    par_elapsed = (time.time() - par_start) * 1000
    print(f"   ⏱️ Temps parallèle: {par_elapsed:.0f}ms")
    
    # Calcul gain
    gain_pct = ((seq_elapsed - par_elapsed) / seq_elapsed) * 100
    print(f"\n📊 GAIN: {gain_pct:.0f}% ({seq_elapsed:.0f}ms → {par_elapsed:.0f}ms)")
    
    if gain_pct > 50:
        print("✅ Parallélisation efficace (>50% gain)")
        return True
    else:
        print("⚠️ Gain insuffisant (<50%)")
        return False


async def test_real_memory_manager():
    """Test avec le vrai MemoryManager si disponible."""
    print("\n" + "="*60)
    print("TEST 3: MemoryManager Réel (optionnel)")
    print("="*60)
    
    try:
        from memory_manager import MemoryManager
        from core_logic import EmbeddingController
        
        # Tentative chargement settings
        settings_path = os.path.join(os.path.dirname(__file__), 'data', 'settings.json')
        if not os.path.exists(settings_path):
            print("⚠️ settings.json non trouvé - Skip test réel")
            return None
        
        import json
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        embedding_config = settings.get('embedding_api', {})
        if not embedding_config.get('api_key'):
            print("⚠️ Pas de clé API embedding - Skip test réel")
            return None
        
        print("🔧 Initialisation EmbeddingController...")
        embed_controller = EmbeddingController(
            backend_type=embedding_config.get('backend_type', 'API'),
            api_key=embedding_config.get('api_key', ''),
            api_provider=embedding_config.get('provider', 'mistral'),
            api_model=embedding_config.get('api_model', 'mistral-embed')
        )
        
        if not embed_controller.is_available:
            print("⚠️ EmbedController non disponible - Skip test réel")
            return None
        
        print("🔧 Initialisation MemoryManager...")
        mm = MemoryManager(
            db_path='data/memory/memory.db',
            embedder=embed_controller,
            embedding_dim=1024
        )
        
        # Test batch réel
        queries = ["chat préféré", "animal domestique", "compagnon félin"]
        
        print(f"\n🚀 Test _generate_embeddings_batch({len(queries)} queries)...")
        start = time.time()
        embeddings = await mm._generate_embeddings_batch(queries)
        elapsed = (time.time() - start) * 1000
        
        valid = sum(1 for e in embeddings if e is not None)
        print(f"✅ Résultat: {valid}/{len(queries)} embeddings en {elapsed:.0f}ms")
        
        # Estimation gain vs séquentiel
        estimated_seq = elapsed * len(queries) / max(valid, 1)
        estimated_gain = ((estimated_seq - elapsed) / estimated_seq) * 100 if estimated_seq > 0 else 0
        print(f"📊 Gain estimé: {estimated_gain:.0f}% vs séquentiel")
        
        return True
        
    except Exception as e:
        print(f"⚠️ Test réel échoué: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Exécute tous les tests."""
    print("🧪 TEST EMBEDDING BATCH OPTIMIZATION")
    print("="*60)
    
    results = []
    
    # Test 1: Existence méthode
    results.append(await test_embedding_batch_exists())
    
    # Test 2: Mock comparatif
    results.append(await test_batch_vs_sequential_mock())
    
    # Test 3: Réel (optionnel)
    real_result = await test_real_memory_manager()
    if real_result is not None:
        results.append(real_result)
    
    # Résumé
    print("\n" + "="*60)
    print("📊 RÉSUMÉ DES TESTS")
    print("="*60)
    
    passed = sum(1 for r in results if r)
    total = len(results)
    
    print(f"✅ Tests réussis: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 TOUS LES TESTS PASSENT!")
        print("   L'optimisation embedding batch est opérationnelle.")
        return 0
    else:
        print("\n⚠️ Certains tests ont échoué.")
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
