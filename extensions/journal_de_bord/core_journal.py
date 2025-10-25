# JOURNAL Extension Journal de Bord - Moteur Principal

"""
Moteur principal du Journal de Bord OGMA
Orchestration des composants, singleton pattern, API publique
"""

import time
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from pathlib import Path

from .config import JournalConfig, get_journal_config

class JournalState(Enum):
    """États possibles du journal"""
    UNINITIALIZED = "uninitialized"    # Pas encore initialisé
    INITIALIZING = "initializing"      # En cours d'initialisation  
    READY = "ready"                    # Prêt à fonctionner
    ACTIVE = "active"                  # En cours d'utilisation
    ERROR = "error"                    # Erreur critique
    DISABLED = "disabled"              # Désactivé par utilisateur

class JournalCore:
    """
    Moteur principal du Journal de Bord OGMA
    
    Responsabilités:
    - Orchestration des composants (JSONManager, EntryGenerator, etc.)
    - Interface publique pour l'intégration OGMA
    - Gestion du cycle de vie de l'extension
    - Coordination entre UI et données
    
    Performance:
    - Cold start: <100ms
    - Context retrieval: <20ms  
    - Entry creation: <3s (avec Archiviste)
    """
    
    def __init__(self, config: JournalConfig = None):
        """Initialise le moteur principal"""
        # Configuration
        self.config = config or get_journal_config()
        
        # État du journal
        self.current_state = JournalState.UNINITIALIZED
        self.initialization_time = None
        self.last_activity_time = None
        
        # Composants (initialisés dans initialize())
        self.json_manager = None
        self.entry_generator = None
        self.context_provider = None
        self.ui_components = None
        
        # Dépendances OGMA (injectées dans initialize())
        self.archiviste_controller = None
        self.memory_manager = None
        self.ui_container = None
        
        # Callbacks d'événements
        self.on_entry_created = None
        self.on_context_requested = None
        self.on_state_changed = None
        self.on_error = None
        
        # Cache et performance
        self.entry_cache = {}
        self.context_cache = {}
        self.last_cache_update = None
        
        # Statistiques
        self.stats = {
            "total_entries": 0,
            "entries_today": 0,
            "days_with_entries": 0,
            "last_entry_date": None,
            "total_tokens_generated": 0,
            "avg_entry_generation_time": 0.0
        }
        
        print(f"[JOURNAL-CORE] INIT Instance créée (config: {self.config.EXTENSION_NAME})")
    
    def initialize(self, archiviste_controller, memory_manager=None, ui_container=None) -> bool:
        """
        Initialise l'extension avec les dépendances OGMA
        
        Args:
            archiviste_controller: Instance AIController pour génération résumés
            memory_manager: Instance MemoryManager OGMA (optionnel)
            ui_container: Container UI pour intégration (optionnel)
        
        Returns:
            bool: True si initialisation réussie
        """
        try:
            self._set_state(JournalState.INITIALIZING)
            start_time = time.time()
            
            print("[JOURNAL-CORE] CONFIG Initialisation des dépendances OGMA...")
            
            # Validation des dépendances critiques
            if not archiviste_controller:
                raise ValueError("archiviste_controller est obligatoire pour la génération de résumés")
            
            self.archiviste_controller = archiviste_controller
            self.memory_manager = memory_manager
            self.ui_container = ui_container
            
            # Initialisation des composants (lazy import pour éviter dépendances circulaires)
            print("[JOURNAL-CORE] STATS Initialisation JSONManager...")
            from .json_manager import JSONManager
            self.json_manager = JSONManager(config=self.config)
            
            print("[JOURNAL-CORE] AI Initialisation EntryGenerator...")
            from .entry_generator import EntryGenerator
            self.entry_generator = EntryGenerator(
                archiviste_controller=self.archiviste_controller,
                config=self.config
            )
            
            print("[JOURNAL-CORE] JOURNAL Initialisation ContextProvider...")
            from .context_provider import ContextProvider
            self.context_provider = ContextProvider(
                json_manager=self.json_manager,
                config=self.config
            )
            
            # Initialisation UI si container fourni
            if self.ui_container:
                print("[JOURNAL-CORE] 🎨 Initialisation UIComponents...")
                from .ui_components import JournalUI
                self.ui_components = JournalUI(
                    journal_core=self,
                    ui_container=self.ui_container,
                    config=self.config
                )
            
            # Chargement des statistiques initiales
            self._load_initial_stats()
            
            # Validation de l'état
            validation_errors = self._validate_system_state()
            if validation_errors:
                raise RuntimeError(f"Erreurs de validation: {validation_errors}")
            
            # Finalisation
            self.initialization_time = time.time() - start_time
            self.last_activity_time = time.time()
            self._set_state(JournalState.READY)
            
            print(f"[JOURNAL-CORE] OK Initialisation réussie en {self.initialization_time:.3f}s")
            print(f"[JOURNAL-CORE] STATS Stats: {self.stats['total_entries']} entrées, {self.stats['days_with_entries']} jours")
            
            return True
            
        except Exception as e:
            print(f"[JOURNAL-CORE] ERROR Erreur initialisation: {e}")
            self._set_state(JournalState.ERROR)
            if self.on_error:
                self.on_error("initialization_failed", str(e))
            return False
    
    def is_ready(self) -> bool:
        """Vérifie si le journal est prêt à fonctionner"""
        return (self.current_state in [JournalState.READY, JournalState.ACTIVE] and 
                self.json_manager is not None and 
                self.entry_generator is not None and
                self.context_provider is not None)
    
    def is_enabled(self) -> bool:
        """Vérifie si l'extension est activée"""
        return self.config.is_enabled() and self.current_state != JournalState.DISABLED
    
    def get_today_context(self, max_entries: int = None) -> str:
        """
        Retourne le contexte de la journée actuelle pour enrichir conversation
        
        Args:
            max_entries: Nombre max d'entrées (par défaut: config)
        
        Returns:
            str: Contexte formaté pour injection en début de conversation
        """
        if not self.is_ready():
            print("[JOURNAL-CORE] WARN Journal non prêt pour get_today_context")
            return ""
        
        try:
            self._set_state(JournalState.ACTIVE)
            start_time = time.time()
            
            # Vérification cache
            today = date.today().isoformat()
            cache_key = f"context_{today}_{max_entries}"
            
            if (cache_key in self.context_cache and 
                self.last_cache_update and 
                time.time() - self.last_cache_update < 300):  # Cache 5 minutes
                print("[JOURNAL-CORE] INIT Contexte depuis cache")
                return self.context_cache[cache_key]
            
            # Génération du contexte
            context = self.context_provider.get_daily_context(
                target_date=today,
                max_entries=max_entries or self.config.get("context_max_entries", 3)
            )
            
            # Mise en cache
            self.context_cache[cache_key] = context
            self.last_cache_update = time.time()
            
            # Callback
            if self.on_context_requested:
                self.on_context_requested(today, context)
            
            duration = time.time() - start_time
            print(f"[JOURNAL-CORE] JOURNAL Contexte généré en {duration:.3f}s")
            
            self._set_state(JournalState.READY)
            return context
            
        except Exception as e:
            print(f"[JOURNAL-CORE] ERROR Erreur get_today_context: {e}")
            if self.on_error:
                self.on_error("context_generation_failed", str(e))
            return ""
    
    async def create_entry_from_conversation(self, conversation_id: str = None, **metadata) -> Optional[Dict[str, Any]]:
        """
        Crée une nouvelle entrée de journal via l'Archiviste
        
        Args:
            conversation_id: ID de la conversation à résumer
            **metadata: Métadonnées additionnelles (title, participants, etc.)
        
        Returns:
            Dict: Entrée créée ou None si échec
        """
        if not self.is_ready():
            print("[JOURNAL-CORE] WARN Journal non prêt pour create_entry")
            return None
        
        try:
            self._set_state(JournalState.ACTIVE)
            start_time = time.time()
            
            print(f"[JOURNAL-CORE] 📝 Création entrée (conversation: {conversation_id})")
            
            # Génération du résumé via Archiviste
            entry_data = await self.entry_generator.generate_entry(
                conversation_id=conversation_id,
                metadata=metadata
            )
            
            if not entry_data:
                raise RuntimeError("EntryGenerator retourné None")
            
            # Sauvegarde dans le JSON
            success = self.json_manager.save_entry(entry_data)
            if not success:
                raise RuntimeError("Échec sauvegarde JSONManager")
            
            # Mise à jour des statistiques
            self._update_stats_after_entry(entry_data)
            
            # Invalidation du cache contexte
            self._invalidate_context_cache()
            
            # Callback
            if self.on_entry_created:
                self.on_entry_created(entry_data)
            
            duration = time.time() - start_time
            print(f"[JOURNAL-CORE] OK Entrée créée en {duration:.3f}s (tokens: {entry_data.get('tokens', 0)})")
            
            self._set_state(JournalState.READY)
            return entry_data
            
        except Exception as e:
            print(f"[JOURNAL-CORE] ERROR Erreur create_entry: {e}")
            if self.on_error:
                self.on_error("entry_creation_failed", str(e))
            self._set_state(JournalState.READY)
            return None
    
    def search_entries(self, query: str = None, **filters) -> List[Dict[str, Any]]:
        """
        Recherche dans l'historique du journal
        
        Args:
            query: Texte de recherche libre
            **filters: Filtres (date_start, date_end, tags, importance, etc.)
        
        Returns:
            List[Dict]: Liste des entrées correspondantes
        """
        if not self.is_ready():
            print("[JOURNAL-CORE] WARN Journal non prêt pour search")
            return []
        
        try:
            start_time = time.time()
            
            results = self.json_manager.search_entries(query=query, **filters)
            
            duration = time.time() - start_time
            print(f"[JOURNAL-CORE] SEARCH Recherche terminée: {len(results)} résultats en {duration:.3f}s")
            
            return results
            
        except Exception as e:
            print(f"[JOURNAL-CORE] ERROR Erreur search: {e}")
            return []
    
    def get_entries_for_date(self, target_date: str) -> List[Dict[str, Any]]:
        """Récupère toutes les entrées d'une date spécifique"""
        if not self.is_ready():
            return []
        
        try:
            return self.json_manager.get_day_entries(target_date)
        except Exception as e:
            print(f"[JOURNAL-CORE] ERROR Erreur get_entries_for_date: {e}")
            return []
    
    def get_journal_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques complètes du journal"""
        base_stats = self.stats.copy()
        
        if self.is_ready():
            # Statistiques temps réel
            try:
                runtime_stats = self.json_manager.get_statistics()
                base_stats.update(runtime_stats)
            except Exception as e:
                print(f"[JOURNAL-CORE] WARN Erreur stats temps réel: {e}")
        
        # Ajout métadonnées système
        base_stats.update({
            "system_state": self.current_state.value,
            "initialization_time": self.initialization_time,
            "last_activity": self.last_activity_time,
            "cache_size": len(self.entry_cache),
            "config_version": self.config.VERSION
        })
        
        return base_stats
    
    def export_journal(self, format: str = "json", date_range: tuple = None, **options) -> str:
        """
        Exporte les données du journal
        
        Args:
            format: Format d'export ("json", "markdown", "csv")
            date_range: Tuple (date_start, date_end) ou None pour tout
            **options: Options d'export spécifiques au format
        
        Returns:
            str: Chemin du fichier exporté
        """
        if not self.is_ready():
            raise RuntimeError("Journal non prêt pour export")
        
        # TODO: Implémenter export (Phase 2)
        raise NotImplementedError("Export sera implémenté en Phase 2")
    
    def cleanup(self):
        """Nettoyage et fermeture propre du journal"""
        try:
            print("[JOURNAL-CORE] UPDATE Nettoyage en cours...")
            
            # Sauvegarde finale des caches
            if self.json_manager:
                self.json_manager.flush_caches()
            
            # Nettoyage des composants
            if self.ui_components:
                self.ui_components.cleanup()
            
            # Reset de l'état
            self._set_state(JournalState.UNINITIALIZED)
            
            print("[JOURNAL-CORE] OK Nettoyage terminé")
            
        except Exception as e:
            print(f"[JOURNAL-CORE] WARN Erreur lors du nettoyage: {e}")
    
    # === MÉTHODES PRIVÉES ===
    
    def _set_state(self, new_state: JournalState):
        """Change l'état du journal avec notification"""
        old_state = self.current_state
        self.current_state = new_state
        
        if old_state != new_state:
            print(f"[JOURNAL-CORE] UPDATE État: {old_state.value} -> {new_state.value}")
            if self.on_state_changed:
                self.on_state_changed(old_state.value, new_state.value)
    
    def _load_initial_stats(self):
        """Charge les statistiques initiales du journal"""
        try:
            if self.json_manager:
                self.stats.update(self.json_manager.get_statistics())
                print(f"[JOURNAL-CORE] STATS Stats chargées: {self.stats['total_entries']} entrées")
        except Exception as e:
            print(f"[JOURNAL-CORE] WARN Erreur chargement stats: {e}")
    
    def _update_stats_after_entry(self, entry_data: Dict[str, Any]):
        """Met à jour les statistiques après création d'entrée"""
        self.stats["total_entries"] += 1
        self.stats["total_tokens_generated"] += entry_data.get("tokens", 0)
        
        # Mise à jour statistiques journalières
        entry_date = entry_data.get("timestamp", "")[:10]  # YYYY-MM-DD
        today = date.today().isoformat()
        
        if entry_date == today:
            self.stats["entries_today"] += 1
        
        # Dernière entrée
        self.stats["last_entry_date"] = entry_date
    
    def _invalidate_context_cache(self):
        """Invalide le cache de contexte après modification"""
        self.context_cache.clear()
        self.last_cache_update = None
        print("[JOURNAL-CORE] UPDATE Cache contexte invalidé")
    
    def _validate_system_state(self) -> List[str]:
        """Valide l'état du système après initialisation"""
        errors = []
        
        # Validation configuration
        config_errors = self.config.validate_settings()
        if config_errors:
            errors.extend(f"Config {k}: {v}" for k, v in config_errors.items())
        
        # Validation composants
        if not self.json_manager:
            errors.append("JSONManager non initialisé")
        if not self.entry_generator:
            errors.append("EntryGenerator non initialisé")
        if not self.context_provider:
            errors.append("ContextProvider non initialisé")
        
        # Validation dépendances
        if not self.archiviste_controller:
            errors.append("archiviste_controller manquant")
        
        return errors