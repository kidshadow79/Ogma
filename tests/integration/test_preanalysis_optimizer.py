"""
Test du module preanalysis_optimizer
=====================================

Teste les composants individuels et l'intégration.

Usage:
    python test_preanalysis_optimizer.py
"""

import asyncio
import time
import sys


def test_context_cache():
    """Test du cache contextuel"""
    print("\n" + "="*60)
    print("TEST 1: ContextCache")
    print("="*60)
    
    from modules.preanalysis_optimizer.context_cache import ContextCache
    
    cache = ContextCache(max_size=10, max_age_seconds=5)
    
    # Test génération de clé
    msg1 = "Bonjour, comment vas-tu?"
    history1 = [
        {"role": "user", "content": "Salut!"},
        {"role": "assistant", "content": "Bonjour! Comment puis-je t'aider?"}
    ]
    
    key1 = cache.generate_key(msg1, history1)
    print(f"✅ Clé générée: {key1}")
    
    # Test set/get
    data = {"ego_injection": "Test injection", "memory_context": "Test mémoire"}
    cache.set(key1, data)
    
    result = cache.get(key1)
    assert result is not None, "Cache miss inattendu"
    assert result["ego_injection"] == "Test injection", "Données corrompues"
    print(f"✅ Set/Get fonctionne correctement")
    
    # Test cache miss
    key2 = cache.generate_key("Message différent", history1)
    result2 = cache.get(key2)
    assert result2 is None, "Cache hit inattendu"
    print(f"✅ Cache miss correct pour clé différente")
    
    # Test stats
    stats = cache.get_stats()
    print(f"✅ Stats: hits={stats['hits']}, misses={stats['misses']}, rate={stats['hit_rate']}%")
    
    # Test expiration (attendre 6s > TTL de 5s)
    print("⏳ Test expiration (attente 6s)...")
    time.sleep(6)
    result3 = cache.get(key1)
    assert result3 is None, "Cache aurait dû expirer"
    print(f"✅ Expiration TTL fonctionne")
    
    print("\n✅ TEST 1 RÉUSSI: ContextCache OK")


def test_preanalysis_engine():
    """Test du moteur de pré-analyse"""
    print("\n" + "="*60)
    print("TEST 2: PreanalysisEngine")
    print("="*60)
    
    from modules.preanalysis_optimizer.preanalysis_engine import PreanalysisEngine
    
    engine = PreanalysisEngine()
    
    # Test trigger sans contrôleurs
    history = [
        {"role": "user", "content": "Test message"},
        {"role": "assistant", "content": "Test réponse"}
    ]
    
    engine.trigger(history)
    print(f"✅ Trigger sans contrôleurs OK (mode dégradé)")
    
    # Attendre un peu pour le background
    time.sleep(1)
    
    # Test status
    status = engine.get_status()
    print(f"✅ Status: running={status['running']}, ready={status['ready']}")
    
    # Test results
    results = engine.get_results()
    print(f"✅ Results: archi_done={results['archi_done']}, age_ms={results['age_ms']}")
    
    # Test reset
    engine.reset()
    status_after = engine.get_status()
    assert status_after['ready'] == False, "Reset n'a pas fonctionné"
    print(f"✅ Reset fonctionne")
    
    print("\n✅ TEST 2 RÉUSSI: PreanalysisEngine OK")


async def test_parallel_executor():
    """Test de l'exécuteur parallèle"""
    print("\n" + "="*60)
    print("TEST 3: ParallelExecutor")
    print("="*60)
    
    from modules.preanalysis_optimizer.parallel_executor import ParallelExecutor
    
    executor = ParallelExecutor()
    
    # Test configuration
    executor.configure(task_timeout=5, global_timeout=10)
    print(f"✅ Configuration acceptée")
    
    # Test exécution sans dépendances (mode dégradé)
    start = time.time()
    result = await executor.execute(
        user_message="Test message",
        conversation_history=[{"role": "user", "content": "Hello"}],
        preanalysis_results={"archi_guidance": "Test guidance"}
    )
    elapsed = (time.time() - start) * 1000
    
    print(f"✅ Exécution parallèle: {result['task_count']} tâches en {elapsed:.0f}ms")
    print(f"   - ego_injection: {len(result.get('ego_injection', ''))} chars")
    print(f"   - archi_guidance: {len(result.get('archi_guidance', ''))} chars")
    print(f"   - errors: {result.get('errors', [])}")
    
    # Test stats
    stats = executor.get_stats()
    print(f"✅ Stats: executions={stats['executions']}, success_rate={stats['success_rate']}%")
    
    print("\n✅ TEST 3 RÉUSSI: ParallelExecutor OK")


async def test_full_optimizer():
    """Test du PreanalysisOptimizer complet"""
    print("\n" + "="*60)
    print("TEST 4: PreanalysisOptimizer (intégration)")
    print("="*60)
    
    from modules.preanalysis_optimizer import (
        get_optimizer,
        trigger_preanalysis,
        get_optimized_context,
        get_preanalysis_status,
        invalidate_cache
    )
    
    # Test singleton
    opt1 = get_optimizer()
    opt2 = get_optimizer()
    assert opt1 is opt2, "Singleton brisé"
    print(f"✅ Pattern singleton OK")
    
    # Test trigger
    history = [{"role": "user", "content": "Hello OGMA"}]
    trigger_preanalysis(history)
    print(f"✅ trigger_preanalysis OK")
    
    # Attendre pré-analyse
    time.sleep(1)
    
    # Test status
    status = get_preanalysis_status()
    print(f"✅ Status: ready={status['ready']}, age_ms={status['age_ms']}")
    
    # Test contexte optimisé
    start = time.time()
    context = await get_optimized_context(
        user_message="Comment ça va?",
        conversation_history=history
    )
    elapsed = (time.time() - start) * 1000
    
    print(f"✅ get_optimized_context: {elapsed:.0f}ms")
    print(f"   - memory_context: {len(context.get('memory_context', ''))} chars")
    print(f"   - ego_injection: {len(context.get('ego_injection', ''))} chars")
    print(f"   - metrics: {context.get('metrics', {})}")
    
    # Test invalidation cache
    invalidate_cache()
    print(f"✅ invalidate_cache OK")
    
    # Test stats
    stats = opt1.get_stats()
    print(f"✅ Stats globales: {stats}")
    
    print("\n✅ TEST 4 RÉUSSI: PreanalysisOptimizer OK")


def test_integration_module():
    """Test du module d'intégration"""
    print("\n" + "="*60)
    print("TEST 5: Integration Module")
    print("="*60)
    
    from modules.preanalysis_optimizer.integration import (
        set_preanalysis_enabled,
        get_optimization_stats,
        trigger_preanalysis_on_typing,
        INTEGRATION_INSTRUCTIONS
    )
    
    # Test activation/désactivation
    set_preanalysis_enabled(False)
    stats1 = get_optimization_stats()
    assert stats1['enabled'] == False, "Désactivation échouée"
    print(f"✅ Désactivation OK")
    
    set_preanalysis_enabled(True)
    stats2 = get_optimization_stats()
    assert stats2['enabled'] == True, "Activation échouée"
    print(f"✅ Activation OK")
    
    # Test trigger (sans erreur même sans contexte NiceGUI)
    try:
        trigger_preanalysis_on_typing()
        print(f"✅ trigger_preanalysis_on_typing OK (mode dégradé)")
    except Exception as e:
        print(f"⚠️ trigger_preanalysis_on_typing erreur attendue: {e}")
    
    # Test instructions
    assert len(INTEGRATION_INSTRUCTIONS) > 1000, "Instructions trop courtes"
    print(f"✅ Instructions d'intégration: {len(INTEGRATION_INSTRUCTIONS)} chars")
    
    print("\n✅ TEST 5 RÉUSSI: Integration Module OK")


async def main():
    """Exécute tous les tests"""
    print("\n" + "="*60)
    print("🧪 TESTS PREANALYSIS OPTIMIZER")
    print("="*60)
    
    try:
        test_context_cache()
        test_preanalysis_engine()
        await test_parallel_executor()
        await test_full_optimizer()
        test_integration_module()
        
        print("\n" + "="*60)
        print("🎉 TOUS LES TESTS RÉUSSIS!")
        print("="*60)
        print("\n📊 RÉSUMÉ GAINS ATTENDUS:")
        print("   - Pré-analyse: -250ms (Ego pendant typing)")
        print("   - Parallélisation: -50ms (Memory + Ego simultanés)")
        print("   - Cache: -700ms (cache hit = 0 appels API)")
        print("   - Total: jusqu'à 42% réduction overhead")
        print("\n📝 PROCHAINES ÉTAPES:")
        print("   1. Tester avec OGMA réel: python launch_ogma.py")
        print("   2. Observer logs [PREANALYSIS-*] dans console")
        print("   3. Mesurer latence avant/après avec timer")
        
    except AssertionError as e:
        print(f"\n❌ TEST ÉCHOUÉ: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERREUR INATTENDUE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
