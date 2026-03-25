"""
PREANALYSIS ENGINE - Moteur de pré-analyse pendant typing
==========================================================

Déclenche des analyses en arrière-plan pendant que l'utilisateur tape,
évitant ainsi l'attente après validation du message.

Analyses pré-déclenchées:
1. Archi Sensor: Analyse métacognitive du contexte (via extension)
2. Ego Catalog: Chargement catalogue traits de personnalité en mémoire

Thread-safety: Utilise asyncio + locks pour éviter conflits.

Usage:
    engine = PreanalysisEngine()
    engine.set_controllers(archiviste_controller)
    
    # Quand user commence à taper
    engine.trigger(conversation_history)
    
    # Après ENTRÉE, récupérer résultats
    results = engine.get_results()
    if results['ready']:
        archi_guidance = results['archi_guidance']
"""

import asyncio
import threading
import time
from typing import Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor

# Executor dédié pour tâches background
_bg_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="preanalysis")

# Cache global pour Ego Catalog (évite rechargements)
_ego_catalog_cache = {
    'catalog': None,
    'timestamp': 0,
    'ttl_seconds': 60  # Refresh toutes les 60s max
}


class PreanalysisEngine:
    """
    Moteur de pré-analyse asynchrone.
    
    Déclenche Archi Sensor + Ego en background quand l'utilisateur tape.
    Les résultats sont stockés et réutilisés après validation du message.
    """
    
    def __init__(self):
        # Résultats pré-analyses
        self._results = {
            'ready': False,
            'archi_guidance': '',
            'archi_done': False,
            'ego_catalog_loaded': False,
            'trigger_timestamp': 0,
            'completion_timestamp': 0
        }
        
        # Lock pour thread-safety
        self._lock = threading.Lock()
        
        # Contrôleurs (injectés via set_controllers)
        self._archiviste_controller = None
        self._ego_selector = None
        
        # État
        self._is_running = False
        self._current_task = None
        self._conversation_hash = None
        
        # Configuration
        self._config = {
            'timeout_ms': 5000,  # Max 5s pour pré-analyses
            'debounce_ms': 300,  # Debounce 300ms avant lancer
            'max_age_ms': 30000  # Invalider si > 30s
        }
        
        print("[PREANALYSIS-ENGINE] 🚀 Moteur initialisé")
    
    def set_controllers(self, archiviste_controller=None, 
                        ego_selector=None):
        """
        Injecte les contrôleurs nécessaires aux pré-analyses.
        
        Args:
            archiviste_controller: Contrôleur Archiviste pour analyses
            ego_selector: Module Ego Selector
        """
        self._archiviste_controller = archiviste_controller
        self._ego_selector = ego_selector
        print("[PREANALYSIS-ENGINE] ✅ Contrôleurs configurés")
    
    def trigger(self, conversation_history: list = None):
        """
        Déclenche la pré-analyse en arrière-plan.
        
        Utilise debouncing pour éviter déclenchements multiples.
        Si une pré-analyse est déjà en cours avec le même contexte, ne relance pas.
        
        Args:
            conversation_history: Historique conversation courant
        """
        # Calcul hash contexte pour détecter changements
        new_hash = self._hash_conversation(conversation_history)
        
        with self._lock:
            # Si même contexte et résultats encore valides, skip
            if (self._conversation_hash == new_hash and 
                self._results['ready'] and 
                self._is_result_fresh()):
                return
            
            # Si analyse en cours avec même hash, skip
            if self._is_running and self._conversation_hash == new_hash:
                return
            
            # Nouveau contexte, marquer pour nouvelle analyse
            self._conversation_hash = new_hash
            self._results['ready'] = False
        
        # Lancer analyse en background
        self._start_background_analysis(conversation_history)
    
    def get_results(self) -> Dict[str, Any]:
        """
        Récupère les résultats de pré-analyse.
        
        Returns:
            dict: {
                'ready': bool,          # True si analyses complètes
                'archi_guidance': str,  # Guidance Archi Sensor
                'archi_done': bool,     # Archi Sensor terminé
                'ego_catalog_loaded': bool,
                'age_ms': int           # Âge des résultats en ms
            }
        """
        with self._lock:
            results = self._results.copy()
            
            # Ajouter âge
            if results['completion_timestamp'] > 0:
                results['age_ms'] = int(
                    (time.time() - results['completion_timestamp']) * 1000
                )
            else:
                results['age_ms'] = -1
            
            # Vérifier fraîcheur
            if results['ready'] and not self._is_result_fresh():
                results['ready'] = False
                results['stale'] = True
            
            return results
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut du moteur.
        
        Returns:
            dict: {'running': bool, 'ready': bool, 'archi_done': bool, ...}
        """
        with self._lock:
            return {
                'running': self._is_running,
                'ready': self._results['ready'],
                'archi_done': self._results['archi_done'],
                'ego_done': self._results['ego_catalog_loaded'],
                'age_ms': (
                    int((time.time() - self._results['completion_timestamp']) * 1000)
                    if self._results['completion_timestamp'] > 0 else -1
                )
            }
    
    def reset(self):
        """Réinitialise le moteur (nouvelle conversation)"""
        with self._lock:
            self._results = {
                'ready': False,
                'archi_guidance': '',
                'archi_done': False,
                'ego_catalog_loaded': False,
                'trigger_timestamp': 0,
                'completion_timestamp': 0
            }
            self._conversation_hash = None
            self._is_running = False
    
    def _start_background_analysis(self, conversation_history: list):
        """Lance l'analyse en thread background"""
        with self._lock:
            if self._is_running:
                return
            self._is_running = True
            self._results['trigger_timestamp'] = time.time()
        
        # Soumettre au thread pool
        _bg_executor.submit(self._run_analysis_sync, conversation_history)
    
    def _run_analysis_sync(self, conversation_history: list):
        """
        Exécute les pré-analyses de manière synchrone dans un thread.
        
        Note: Archi Sensor remplacé par Unified Meta-Analyzer (parallel_executor)
        Seul le préchargement Ego Catalog reste ici.
        """
        try:
            start_time = time.time()
            
            # Préchargement Ego Catalog
            ego_loaded = self._preload_ego_catalog()
            
            with self._lock:
                self._results['ego_catalog_loaded'] = ego_loaded
                self._results['ready'] = True
                self._results['completion_timestamp'] = time.time()
            
            elapsed_ms = (time.time() - start_time) * 1000
            print(f"[PREANALYSIS-ENGINE] ✅ Pré-analyses complètes en {elapsed_ms:.0f}ms")
            
        except Exception as e:
            print(f"[PREANALYSIS-ENGINE] ❌ Erreur pré-analyse: {e}")
            with self._lock:
                self._results['ready'] = False
        finally:
            with self._lock:
                self._is_running = False
    
    def _preload_ego_catalog(self) -> bool:
        """
        Obsolète — l'ancien système ego_selector a été remplacé par
        modules/logic/ego_activation.py (Ego Boolean System, janvier 2026).
        Cette fonction est conservée pour ne pas casser l'interface mais ne fait rien.
        """
        return False
    
    def _find_memory_db_path(self) -> Optional[str]:
        """Trouve le chemin de la base de données mémoire."""
        import os
        
        # Chemins possibles
        possible_paths = [
            'data/memory/memories.db',
            'C:/IA/OGMA/data/memory/memories.db',
            os.path.join(os.getcwd(), 'data', 'memory', 'memories.db')
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def _hash_conversation(self, conversation_history: list) -> str:
        """
        Génère un hash du contexte conversation pour détection changements.
        
        Utilise les 5 derniers messages pour hash rapide.
        """
        import hashlib
        
        if not conversation_history:
            return "empty"
        
        # Prendre les 5 derniers messages
        recent = conversation_history[-5:] if len(conversation_history) > 5 else conversation_history
        
        # Construire string à hasher
        content = "".join([
            f"{msg.get('role', '')}:{msg.get('content', '')[:100]}"
            for msg in recent
        ])
        
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _is_result_fresh(self) -> bool:
        """Vérifie si les résultats sont encore frais (< max_age_ms)"""
        if self._results['completion_timestamp'] == 0:
            return False
        
        age_ms = (time.time() - self._results['completion_timestamp']) * 1000
        return age_ms < self._config['max_age_ms']


def get_cached_ego_catalog() -> list:
    """
    Récupère le catalogue Ego depuis le cache global.
    
    Returns:
        Liste du catalogue ou liste vide si non chargé.
    """
    global _ego_catalog_cache
    if _ego_catalog_cache['catalog'] is not None:
        return _ego_catalog_cache['catalog']
    return []
