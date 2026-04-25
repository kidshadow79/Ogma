"""
PREANALYSIS OPTIMIZER - Module d'optimisation latence OGMA
============================================================

Réduit la latence de réponse via :
1. Pré-analyse pendant que l'utilisateur tape (Archi Sensor + Ego Catalog)
2. Cache contextuel intelligent (évite analyses répétitives)
3. Exécution parallèle (Memory + Ego final simultanés)

GAINS ATTENDUS:
- Latence: -250ms (-42% overhead avant IA principale)
- Tokens: -40% sur conversations similaires (cache hits)

Usage:
    from modules.preanalysis_optimizer import (
        get_optimizer,
        trigger_preanalysis,
        get_optimized_context
    )
    
    # Déclencher pré-analyse quand user tape
    trigger_preanalysis(conversation_history)
    
    # Récupérer contexte optimisé après ENTRÉE
    context = await get_optimized_context(user_message, conversation_history)

Auteur: OGMA Team
Date: 7 décembre 2025
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "OGMA Team"

from .preanalysis_engine import PreanalysisEngine
from .context_cache import ContextCache
from .parallel_executor import ParallelExecutor

# Singleton instance
_optimizer_instance = None


def get_optimizer():
    """
    Retourne l'instance singleton de l'optimizer.
    Lazy initialization au premier appel.
    
    Returns:
        PreanalysisOptimizer: Instance configurée
    """
    global _optimizer_instance
    if _optimizer_instance is None:
        _optimizer_instance = PreanalysisOptimizer()
    return _optimizer_instance


def trigger_preanalysis(conversation_history: list = None):
    """
    Déclenche la pré-analyse en arrière-plan.
    Appeler quand l'utilisateur commence à taper.
    
    Args:
        conversation_history: Historique conversation (optionnel, utilise global si None)
    """
    optimizer = get_optimizer()
    optimizer.trigger_preanalysis(conversation_history)


async def get_optimized_context(user_message: str, conversation_history: list, 
                                 memory_manager=None, archiviste_controller=None,
                                 memory_optimizer=None, temporal_guardian=None,
                                 temporal_data=None) -> dict:
    """
    Récupère le contexte optimisé pour Luna.
    Utilise pré-analyses + cache + parallélisation.
    
    Args:
        user_message: Message utilisateur
        conversation_history: Historique conversation
        memory_manager: Gestionnaire mémoire
        archiviste_controller: Contrôleur Archiviste
        memory_optimizer: Optimizer mémoire (Solution A)
        temporal_guardian: Instance Temporal Guardian (optionnel)
        temporal_data: Données temporelles (optionnel)
        
    Returns:
        dict: {
            'memory_context': str,
            'ego_injection': str,
            'archi_guidance': str,
            'capability_suggestion': dict,
            'temporal_instruction': str,  # NOUVEAU
            'metrics': dict
        }
    """
    optimizer = get_optimizer()
    return await optimizer.get_optimized_context(
        user_message, 
        conversation_history,
        memory_manager=memory_manager,
        archiviste_controller=archiviste_controller,
        memory_optimizer=memory_optimizer,
        temporal_guardian=temporal_guardian,
        temporal_data=temporal_data
    )


def get_preanalysis_status() -> dict:
    """
    Retourne le statut de la pré-analyse en cours.
    
    Returns:
        dict: {'ready': bool, 'archi_done': bool, 'ego_done': bool, 'age_ms': int}
    """
    optimizer = get_optimizer()
    return optimizer.get_status()


def invalidate_cache():
    """Force l'invalidation du cache (changement conversation, etc.)"""
    optimizer = get_optimizer()
    optimizer.invalidate_cache()


class PreanalysisOptimizer:
    """
    Orchestrateur principal de l'optimisation latence.
    
    Coordonne:
    - PreanalysisEngine: Pré-analyse pendant typing
    - ContextCache: Cache contextuel intelligent
    - ParallelExecutor: Exécution parallèle après ENTRÉE
    """
    
    def __init__(self):
        self.preanalysis_engine = PreanalysisEngine()
        self.context_cache = ContextCache()
        self.parallel_executor = ParallelExecutor()
        
        # Métriques
        self._stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'preanalysis_used': 0,
            'avg_latency_ms': 0
        }
        
        print("[PREANALYSIS-OPTIMIZER] ✅ Module initialisé")
    
    def trigger_preanalysis(self, conversation_history: list = None):
        """Déclenche pré-analyse en arrière-plan"""
        self.preanalysis_engine.trigger(conversation_history)
    
    async def get_optimized_context(self, user_message: str, conversation_history: list,
                                     memory_manager=None, archiviste_controller=None,
                                     memory_optimizer=None,
                                     memory_titles_found: list = None) -> dict:
        """
        Pipeline complet d'optimisation.
        
        1. Vérifier cache contextuel
        2. Récupérer pré-analyses si prêtes
        3. Paralléliser le reste (Memory, Ego, Capability, Temporal, ArchiSensor)
        4. Assembler et retourner
        """
        import time
        start_time = time.time()
        self._stats['total_requests'] += 1
        
        # ÉTAPE 1: Vérifier cache
        cache_key = self.context_cache.generate_key(user_message, conversation_history)
        cached_result = self.context_cache.get(cache_key)
        
        if cached_result:
            self._stats['cache_hits'] += 1
            latency_ms = (time.time() - start_time) * 1000
            print(f"[PREANALYSIS-OPTIMIZER] 📋 CACHE HIT ({latency_ms:.0f}ms)")
            cached_result['metrics']['from_cache'] = True
            return cached_result
        
        # ÉTAPE 2: Récupérer pré-analyses
        preanalysis_results = self.preanalysis_engine.get_results()
        
        if preanalysis_results.get('ready'):
            self._stats['preanalysis_used'] += 1
            print("[PREANALYSIS-OPTIMIZER] ⚡ Pré-analyses utilisées")
        
        # ÉTAPE 3: Exécution parallèle du reste (5 tâches: Memory, Ego, Capability, Temporal, ArchiSensor)
        parallel_results = await self.parallel_executor.execute(
            user_message=user_message,
            conversation_history=conversation_history,
            preanalysis_results=preanalysis_results,
            memory_manager=memory_manager,
            archiviste_controller=archiviste_controller,
            memory_optimizer=memory_optimizer,
            memory_titles_found=memory_titles_found
        )
        
        # ÉTAPE 4: Assembler résultat final
        # Note: ego_injection peut être None (permet fallback dans ogma_ng.py)
        ego_injection = parallel_results.get('ego_injection')  # Préserver None
        
        result = {
            'memory_context': parallel_results.get('memory_context', ''),
            'memory_details': parallel_results.get('memory_details', []),
            'ego_injection': ego_injection,  # None ou str (pas de conversion '')
            'archi_guidance': preanalysis_results.get('archi_guidance', ''),
            'capability_suggestion': parallel_results.get('capability_suggestion'),
            # Directive Archiviste (conscience critique)
            'archiviste_directive': parallel_results.get('archiviste_directive'),
            # Emotion hologramme (yeux)
            'emotion_hologram': parallel_results.get('emotion_hologram', 'neutre'),
            # NOUVEAU: Métriques Unified Meta-Analyzer (affinity + auto-censure)
            'affinity_level': parallel_results.get('affinity_level', 4),
            'affinity_confidence': parallel_results.get('affinity_confidence', 0.5),
            'auto_censure_level': parallel_results.get('auto_censure_level', 3),
            'auto_censure_confidence': parallel_results.get('auto_censure_confidence', 0.5),
            'metrics': {
                'latency_ms': (time.time() - start_time) * 1000,
                'cache_hit': False,
                'preanalysis_used': preanalysis_results.get('ready', False),
                'parallel_tasks': parallel_results.get('task_count', 0),
                'unified_duration_ms': parallel_results.get('unified_duration_ms', 0)
            }
        }
        
        # Sauvegarder en cache
        self.context_cache.set(cache_key, result)
        
        latency_ms = result['metrics']['latency_ms']
        self._update_avg_latency(latency_ms)
        
        print(f"[PREANALYSIS-OPTIMIZER] ✅ Contexte optimisé en {latency_ms:.0f}ms")
        
        return result
    
    def get_status(self) -> dict:
        """Retourne statut pré-analyse"""
        return self.preanalysis_engine.get_status()
    
    def invalidate_cache(self):
        """Invalide le cache"""
        self.context_cache.invalidate()
    
    def _update_avg_latency(self, latency_ms: float):
        """Met à jour latence moyenne"""
        n = self._stats['total_requests']
        avg = self._stats['avg_latency_ms']
        self._stats['avg_latency_ms'] = (avg * (n - 1) + latency_ms) / n
    
    def get_stats(self) -> dict:
        """Retourne statistiques d'optimisation"""
        return {
            **self._stats,
            'cache_hit_rate': (
                self._stats['cache_hits'] / self._stats['total_requests'] * 100
                if self._stats['total_requests'] > 0 else 0
            ),
            'preanalysis_rate': (
                self._stats['preanalysis_used'] / self._stats['total_requests'] * 100
                if self._stats['total_requests'] > 0 else 0
            )
        }


__all__ = [
    'get_optimizer',
    'trigger_preanalysis', 
    'get_optimized_context',
    'get_preanalysis_status',
    'invalidate_cache',
    'PreanalysisOptimizer',
    'PreanalysisEngine',
    'ContextCache',
    'ParallelExecutor'
]
