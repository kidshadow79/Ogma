"""
PARALLEL EXECUTOR - Exécution parallèle des analyses OGMA
==========================================================

Parallélise les appels API qui étaient séquentiels:
- Memory Optimizer (analyse + extraction)
- Ego Selector (sélection finale)
- Capability Advisor

Utilise asyncio.gather() avec timeout et isolation erreurs.

GAINS:
- -50ms à -100ms (appels simultanés vs séquentiels)
- Robustesse: un échec n'impacte pas les autres

Usage:
    executor = ParallelExecutor()
    
    results = await executor.execute(
        user_message="Bonjour Luna",
        conversation_history=[...],
        preanalysis_results={'archi_guidance': '...'},
        memory_manager=memory_manager,
        archiviste_controller=archiviste
    )
"""

import asyncio
import time
from typing import Dict, Any, Optional, List, Callable
from concurrent.futures import ThreadPoolExecutor

# Import Unified Meta Analyzer (3-en-1)
from modules.preanalysis_optimizer.unified_meta_analyzer import UnifiedMetaAnalyzer

# Thread pool dédié pour fonctions sync
_sync_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="parallel")


class ParallelExecutor:
    """
    Exécute les analyses en parallèle via asyncio.gather().
    
    Gère:
    - Conversion sync → async pour fonctions bloquantes
    - Timeout par tâche
    - Isolation des erreurs (une tâche échouée n'arrête pas les autres)
    - Métriques de performance
    """
    
    def __init__(self):
        # Configuration
        self._config = {
            'task_timeout_seconds': 10,  # Timeout par tâche
            'global_timeout_seconds': 15,  # Timeout global
            'max_concurrent_tasks': 4
        }
        
        # Métriques
        self._stats = {
            'executions': 0,
            'total_tasks': 0,
            'failed_tasks': 0,
            'avg_duration_ms': 0
        }
        
        print("[PARALLEL-EXECUTOR] ⚡ Exécuteur parallèle initialisé")
    
    async def execute(self, user_message: str, conversation_history: list,
                      preanalysis_results: Dict[str, Any] = None,
                      memory_manager=None, archiviste_controller=None,
                      memory_optimizer=None,
                      temporal_guardian=None,
                      temporal_data=None,
                      memory_titles_found: list = None) -> Dict[str, Any]:
        """
        Exécute toutes les analyses en parallèle.
        
        Tâches parallélisées:
        1. Memory Optimizer (si pré-analyses pas ready)
        2. Ego Selector final
        3. Capability Advisor
        4. Temporal Guardian (NOUVEAU - analyse temporelle via Archiviste)
        
        Args:
            user_message: Message utilisateur
            conversation_history: Historique
            preanalysis_results: Résultats pré-analyses (optionnel)
            memory_manager: Gestionnaire mémoire
            archiviste_controller: Contrôleur Archiviste
            memory_optimizer: Optimizer mémoire
            temporal_guardian: Instance Temporal Guardian (optionnel)
            temporal_data: Données temporelles (optionnel)
            
        Returns:
            dict: Résultats combinés de toutes les tâches
        """
        start_time = time.time()
        self._stats['executions'] += 1
        
        preanalysis_results = preanalysis_results or {}
        
        # Préparer les tâches à exécuter
        tasks = []
        task_names = []
        
        # TÂCHE 1: Memory Optimizer
        if memory_optimizer and memory_manager:
            tasks.append(self._run_memory_optimizer(
                user_message, conversation_history, 
                memory_optimizer, memory_manager, archiviste_controller
            ))
            task_names.append('memory')
        
        # TÂCHE 2: UNIFIED META-ANALYZER (remplace Capability + Temporal + ArchiSensor)
        # Fusion 3-en-1 pour économiser tokens et latence
        if archiviste_controller:
            tasks.append(self._run_unified_meta_analyzer(
                user_message, conversation_history, archiviste_controller,
                memory_manager, temporal_guardian, temporal_data,
                memory_titles_found=memory_titles_found
            ))
            task_names.append('unified_meta')
        
        self._stats['total_tasks'] += len(tasks)
        
        # Exécution parallèle avec timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self._config['global_timeout_seconds']
            )
        except asyncio.TimeoutError:
            print(f"[PARALLEL-EXECUTOR] ⏰ Timeout global ({self._config['global_timeout_seconds']}s)")
            results = [None] * len(tasks)
        
        # Assembler les résultats
        combined_result = self._combine_results(results, task_names, preanalysis_results)
        
        # Métriques
        duration_ms = (time.time() - start_time) * 1000
        combined_result['task_count'] = len(tasks)
        combined_result['duration_ms'] = duration_ms
        
        self._update_avg_duration(duration_ms)
        
        success_count = sum(1 for r in results if r is not None and not isinstance(r, Exception))
        print(f"[PARALLEL-EXECUTOR] ✅ {success_count}/{len(tasks)} tâches en {duration_ms:.0f}ms")
        
        return combined_result
    
    async def _run_memory_optimizer(self, user_message: str, conversation_history: list,
                                     memory_optimizer, memory_manager, 
                                     archiviste_controller) -> Dict[str, Any]:
        """
        Exécute Memory Optimizer en async.
        
        Convertit l'appel sync en async via executor.
        """
        try:
            loop = asyncio.get_event_loop()
            
            # Wrapper pour exécution sync
            def sync_call():
                return memory_optimizer.optimize_memory_context(
                    user_message=user_message,
                    conversation_history=conversation_history,
                    memory_manager=memory_manager,
                    archiviste_controller=archiviste_controller
                )
            
            result = await asyncio.wait_for(
                loop.run_in_executor(_sync_executor, sync_call),
                timeout=self._config['task_timeout_seconds']
            )
            
            return {
                'memory_context': result.get('optimized_context', ''),
                'memory_details': result.get('memory_details', []),
                'memory_tokens': result.get('token_count', 0)
            }
            
        except asyncio.TimeoutError:
            print("[PARALLEL-EXECUTOR] ⏰ Memory Optimizer timeout")
            self._stats['failed_tasks'] += 1
            return {'memory_context': '', 'memory_details': [], 'error': 'timeout'}
        except Exception as e:
            print(f"[PARALLEL-EXECUTOR] ❌ Memory Optimizer erreur: {e}")
            self._stats['failed_tasks'] += 1
            return {'memory_context': '', 'memory_details': [], 'error': str(e)}
    
    async def _run_capability_advisor(self, user_message: str, conversation_history: list,
                                       archiviste_controller) -> Dict[str, Any]:
        """
        Exécute Capability Advisor en async.
        """
        try:
            loop = asyncio.get_event_loop()
            
            def sync_call():
                try:
                    from extensions.capability_advisor import suggest_capability
                    
                    return suggest_capability(
                        user_message=user_message,
                        conversation_history=conversation_history,
                        archiviste_controller=archiviste_controller
                    )
                except ImportError:
                    return None
            
            result = await asyncio.wait_for(
                loop.run_in_executor(_sync_executor, sync_call),
                timeout=self._config['task_timeout_seconds']
            )
            
            return {'capability_suggestion': result}
            
        except asyncio.TimeoutError:
            print("[PARALLEL-EXECUTOR] ⏰ Capability Advisor timeout")
            self._stats['failed_tasks'] += 1
            return {'capability_suggestion': None, 'error': 'timeout'}
        except Exception as e:
            print(f"[PARALLEL-EXECUTOR] ❌ Capability Advisor erreur: {e}")
            self._stats['failed_tasks'] += 1
            return {'capability_suggestion': None, 'error': str(e)}
    
    async def _run_temporal_guardian(self, temporal_guardian, temporal_data,
                                      archiviste_controller) -> Dict[str, Any]:
        """
        Exécute l'analyse Temporal Guardian en async.
        
        Appelle analyze_with_archiviste() pour obtenir une instruction temporelle.
        
        Args:
            temporal_guardian: Instance TemporalGuardian
            temporal_data: TemporalMeasurement avec les données temporelles
            archiviste_controller: Contrôleur Archiviste pour l'analyse
            
        Returns:
            dict: {'temporal_instruction': str|None}
        """
        try:
            print("[PARALLEL-EXECUTOR] 🕒 Temporal Guardian: lancement analyse...")
            
            # analyze_with_archiviste est déjà async
            temporal_instruction = await asyncio.wait_for(
                temporal_guardian.analyze_with_archiviste(temporal_data, archiviste_controller),
                timeout=self._config['task_timeout_seconds']
            )
            
            if temporal_instruction:
                print(f"[PARALLEL-EXECUTOR] 🕒 Temporal Guardian: instruction reçue ({len(temporal_instruction)} chars)")
                return {'temporal_instruction': temporal_instruction}
            else:
                print("[PARALLEL-EXECUTOR] 🕒 Temporal Guardian: rythme normal")
                return {'temporal_instruction': None}
                
        except asyncio.TimeoutError:
            print("[PARALLEL-EXECUTOR] ⏰ Temporal Guardian timeout")
            self._stats['failed_tasks'] += 1
            return {'temporal_instruction': None, 'error': 'timeout'}
        except Exception as e:
            print(f"[PARALLEL-EXECUTOR] ❌ Temporal Guardian erreur: {e}")
            import traceback
            traceback.print_exc()
            self._stats['failed_tasks'] += 1
            return {'temporal_instruction': None, 'error': str(e)}
    
    async def _run_unified_meta_analyzer(self, user_message: str, conversation_history: list,
                                          archiviste_controller, memory_manager,
                                          temporal_guardian=None, temporal_data=None,
                                          memory_titles_found: list = None) -> Dict[str, Any]:
        """
        Exécute l'analyseur unifié (3-en-1) : Temporal + ArchiSensor + Capability.
        
        FUSION des 3 appels API en 1 seul pour économiser tokens et latence.
        
        Args:
            user_message: Message utilisateur
            conversation_history: Historique conversation
            archiviste_controller: Contrôleur Archiviste
            memory_manager: Gestionnaire mémoire
            temporal_guardian: Instance TemporalGuardian (optionnel)
            temporal_data: Données temporelles (optionnel)
            memory_titles_found: Titres des souvenirs deja trouves par FAISS (optionnel)
            
        Returns:
            dict: Résultats fusionnés (temporal, affinity, capability)
        """
        try:
            print("[PARALLEL-EXECUTOR] 🔮 Unified Meta-Analyzer: lancement analyse 3-en-1...")
            
            from modules.preanalysis_optimizer.unified_meta_analyzer import get_unified_analyzer
            
            # Obtenir ou créer l'analyseur unifié
            analyzer = get_unified_analyzer(archiviste_controller, memory_manager)
            
            if not analyzer:
                print("[PARALLEL-EXECUTOR] ⚠️ Unified analyzer non disponible")
                return self._get_empty_unified_result()
            
            # Exécuter l'analyse unifiée (avec info souvenirs trouves)
            result = await asyncio.wait_for(
                analyzer.analyze(user_message, conversation_history, temporal_data,
                                 memory_titles_found=memory_titles_found),
                timeout=self._config['task_timeout_seconds']
            )
            
            # Convertir le dataclass en dict pour combine_results
            unified_result = {
                # Temporal
                'temporal_instruction': result.temporal_instruction,
                'temporal_pattern': result.temporal_pattern,
                
                # Capability
                'capability_suggested': result.suggested_capability,
                'capability_confidence': result.capability_confidence,
                'capability_phrase': result.capability_phrase,
                
                # Directive Archiviste
                'archiviste_directive': result.archiviste_directive,
                
                # Meta
                'unified_duration_ms': result.analysis_duration_ms
            }
            
            print(f"[PARALLEL-EXECUTOR] 🔮 Unified Meta-Analyzer: terminé en {result.analysis_duration_ms:.0f}ms")
            return unified_result
            
        except asyncio.TimeoutError:
            print("[PARALLEL-EXECUTOR] ⏰ Unified Meta-Analyzer timeout")
            self._stats['failed_tasks'] += 1
            return self._get_empty_unified_result('timeout')
        except Exception as e:
            print(f"[PARALLEL-EXECUTOR] ❌ Unified Meta-Analyzer erreur: {e}")
            import traceback
            traceback.print_exc()
            self._stats['failed_tasks'] += 1
            return self._get_empty_unified_result(str(e))
    
    def _get_empty_unified_result(self, error: str = None) -> Dict[str, Any]:
        """Résultat vide pour l'analyseur unifié en cas d'erreur"""
        result = {
            'temporal_instruction': None,
            'temporal_pattern': None,
            'capability_suggested': None,
            'capability_confidence': 0.0,
            'capability_phrase': None,
            'archiviste_directive': None,
            'unified_duration_ms': 0
        }
        if error:
            result['error'] = error
        return result
    
    def _combine_results(self, results: List[Any], task_names: List[str],
                          preanalysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Combine les résultats de toutes les tâches.
        
        Priorise pré-analyses si disponibles.
        Note: ego_injection peut être None (permet fallback) ou str (valeur réelle)
        """
        combined = {
            'memory_context': '',
            'memory_details': [],
            'ego_injection': None,  # None par défaut pour permettre fallback
            'capability_suggestion': None,
            'archi_guidance': preanalysis_results.get('archi_guidance', ''),
            'temporal_instruction': None,  # Instruction Temporal Guardian
            'archiviste_directive': None,   # Directive conscience critique
            'unified_duration_ms': 0,
            'errors': []
        }
        
        for i, (result, name) in enumerate(zip(results, task_names)):
            if isinstance(result, Exception):
                combined['errors'].append(f"{name}: {str(result)}")
                continue
            
            if result is None:
                continue
            
            if isinstance(result, dict):
                # Erreur capturée dans le dict
                if 'error' in result:
                    combined['errors'].append(f"{name}: {result['error']}")
                
                # Merger les résultats
                if name == 'memory':
                    combined['memory_context'] = result.get('memory_context', '')
                    combined['memory_details'] = result.get('memory_details', [])
                elif name == 'capability':
                    combined['capability_suggestion'] = result.get('capability_suggestion')
                elif name == 'temporal':
                    # Résultat Temporal Guardian (mode séparé - legacy)
                    combined['temporal_instruction'] = result.get('temporal_instruction')
                elif name == 'unified_meta':
                    # NOUVEAU: Résultat analyseur unifié 3-en-1 (Temporal + Capability + Directive)
                    combined['temporal_instruction'] = result.get('temporal_instruction')
                    combined['archiviste_directive'] = result.get('archiviste_directive')
                    combined['unified_duration_ms'] = result.get('unified_duration_ms', 0)
                    
                    # Convertir suggestion capability en format attendu
                    cap_suggested = result.get('capability_suggested')
                    cap_phrase = result.get('capability_phrase')
                    cap_confidence = result.get('capability_confidence', 0)
                    # Pas de filtre hardcodé ici : ogma_ng.py vérifie les seuils catalog+custom
                    if cap_suggested and cap_confidence > 0.0:
                        # Créer un objet compatible avec le format attendu
                        combined['capability_suggestion'] = {
                            'capability_id': cap_suggested,
                            'confidence': cap_confidence,
                            'magic_phrase': cap_phrase
                        }
        
        return combined
    
    def _update_avg_duration(self, duration_ms: float):
        """Met à jour la durée moyenne."""
        n = self._stats['executions']
        avg = self._stats['avg_duration_ms']
        self._stats['avg_duration_ms'] = (avg * (n - 1) + duration_ms) / n
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques d'exécution."""
        total = self._stats['total_tasks']
        failed = self._stats['failed_tasks']
        success_rate = ((total - failed) / total * 100) if total > 0 else 100
        
        return {
            **self._stats,
            'success_rate': round(success_rate, 1)
        }
    
    def configure(self, task_timeout: int = None, global_timeout: int = None,
                  max_concurrent: int = None):
        """
        Configure les paramètres de l'exécuteur.
        
        Args:
            task_timeout: Timeout par tâche en secondes
            global_timeout: Timeout global en secondes
            max_concurrent: Nombre max de tâches parallèles
        """
        if task_timeout is not None:
            self._config['task_timeout_seconds'] = task_timeout
        if global_timeout is not None:
            self._config['global_timeout_seconds'] = global_timeout
        if max_concurrent is not None:
            self._config['max_concurrent_tasks'] = max_concurrent
        
        print(f"[PARALLEL-EXECUTOR] ⚙️ Config: task={self._config['task_timeout_seconds']}s, "
              f"global={self._config['global_timeout_seconds']}s")


class SmartParallelExecutor(ParallelExecutor):
    """
    Extension avec optimisations intelligentes.
    
    Features additionnelles:
    - Skip tâches si pré-analyses complètes
    - Priorisation basée sur importance
    - Circuit breaker si trop d'échecs
    """
    
    def __init__(self):
        super().__init__()
        self._circuit_breaker = {
            'failures': 0,
            'threshold': 5,
            'reset_time': 0,
            'cooldown_seconds': 60
        }
    
    def _should_skip_task(self, task_name: str, preanalysis_results: Dict) -> bool:
        """Détermine si une tâche peut être skippée grâce aux pré-analyses."""
        return False
    
    def _is_circuit_open(self) -> bool:
        """Vérifie si le circuit breaker est ouvert (trop d'échecs)."""
        if self._circuit_breaker['failures'] >= self._circuit_breaker['threshold']:
            # Vérifier si cooldown terminé
            if time.time() > self._circuit_breaker['reset_time']:
                self._circuit_breaker['failures'] = 0
                return False
            return True
        return False
    
    def _record_failure(self):
        """Enregistre un échec pour le circuit breaker."""
        self._circuit_breaker['failures'] += 1
        if self._circuit_breaker['failures'] >= self._circuit_breaker['threshold']:
            self._circuit_breaker['reset_time'] = (
                time.time() + self._circuit_breaker['cooldown_seconds']
            )
            print("[PARALLEL-EXECUTOR] ⚠️ Circuit breaker ouvert, pause temporaire")
