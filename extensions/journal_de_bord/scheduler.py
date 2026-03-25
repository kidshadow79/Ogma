"""
OGMA - Journal de Bord v2.0
Module de planification hebdomadaire (maintenance automatique)

Fonctionnalités :
- Job hebdomadaire pour maintenance automatique
- Auto-résolution états inactifs
- Purge/compression entrées anciennes
- Configuration via journal_settings.json
- Arrêt propre et redémarrage

Pattern : Singleton avec threading.Timer
"""

import threading
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from .auto_resolution import auto_resolve_states, get_auto_resolution_stats
from .purge_manager import get_purge_manager


class MaintenanceScheduler:
    """Planificateur de maintenance hebdomadaire du Journal"""
    
    def __init__(
        self,
        json_manager,
        purge_manager,
        archiviste_controller,
        settings_path: Path
    ):
        """
        Initialise le planificateur
        
        Args:
            json_manager: Instance JournalJSONManager
            purge_manager: Instance PurgeManager
            archiviste_controller: Contrôleur LLM Archiviste
            settings_path: Chemin fichier journal_settings.json
        """
        self.json_manager = json_manager
        self.purge_manager = purge_manager
        self.archiviste_controller = archiviste_controller
        self.settings_path = settings_path
        
        self._timer: Optional[threading.Timer] = None
        self._is_running = False
        
        # Config par défaut
        self.default_config = {
            "auto_purge_enabled": False,
            "purge_age_days": 90,
            "purge_mode": "compress",  # "compress" ou "archive"
            "auto_resolve_enabled": False,
            "resolve_threshold_days": 30,
            "require_llm_validation": True,
            "maintenance_interval_days": 7,
            "last_maintenance": None
        }
        
        # Charger config
        self.config = self._load_config()
        
        print("[SCHEDULER] Initialisé")
    
    def _load_config(self) -> Dict[str, Any]:
        """Charge la configuration depuis journal_settings.json"""
        try:
            if self.settings_path.exists():
                with open(self.settings_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Fusionner avec config par défaut
                    config = self.default_config.copy()
                    config.update(data.get("maintenance", {}))
                    
                    return config
            else:
                print("[SCHEDULER] Config non trouvée, utilisation défauts")
                return self.default_config.copy()
        
        except Exception as e:
            print(f"[SCHEDULER] ERROR Chargement config: {e}")
            return self.default_config.copy()
    
    def _save_config(self) -> bool:
        """Sauvegarde la configuration dans journal_settings.json"""
        try:
            # Charger fichier complet
            if self.settings_path.exists():
                with open(self.settings_path, 'r', encoding='utf-8') as f:
                    full_data = json.load(f)
            else:
                full_data = {}
            
            # Mettre à jour section maintenance
            full_data["maintenance"] = self.config
            
            # Sauvegarder
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(full_data, f, ensure_ascii=False, indent=2)
            
            return True
        
        except Exception as e:
            print(f"[SCHEDULER] ERROR Sauvegarde config: {e}")
            return False
    
    def start(self):
        """Démarre le planificateur hebdomadaire"""
        try:
            if self._is_running:
                print("[SCHEDULER] Déjà actif")
                return
            
            # Vérifier si maintenance activée
            if not (self.config["auto_purge_enabled"] or self.config["auto_resolve_enabled"]):
                print("[SCHEDULER] Maintenance désactivée (auto_purge et auto_resolve à False)")
                return
            
            self._is_running = True
            
            # Calculer intervalle en secondes
            interval_seconds = self.config["maintenance_interval_days"] * 24 * 60 * 60
            
            # Planifier premier job
            self._schedule_next_run(interval_seconds)
            
            print(f"[SCHEDULER] ✅ Démarré (intervalle: {self.config['maintenance_interval_days']}j)")
        
        except Exception as e:
            print(f"[SCHEDULER] ERROR Démarrage: {e}")
            import traceback
            traceback.print_exc()
    
    def stop(self):
        """Arrête proprement le planificateur"""
        try:
            if self._timer:
                self._timer.cancel()
                self._timer = None
            
            self._is_running = False
            print("[SCHEDULER] 🛑 Arrêté")
        
        except Exception as e:
            print(f"[SCHEDULER] ERROR Arrêt: {e}")
    
    def _schedule_next_run(self, interval_seconds: int):
        """Planifie la prochaine exécution"""
        try:
            if not self._is_running:
                return
            
            self._timer = threading.Timer(interval_seconds, self._run_maintenance)
            self._timer.daemon = True  # Thread daemon pour arrêt propre
            self._timer.start()
            
            next_run = datetime.now().timestamp() + interval_seconds
            next_run_dt = datetime.fromtimestamp(next_run)
            
            print(f"[SCHEDULER] Prochaine maintenance: {next_run_dt.strftime('%d/%m/%Y %H:%M')}")
        
        except Exception as e:
            print(f"[SCHEDULER] ERROR Planification: {e}")
    
    def _run_maintenance(self):
        """Exécute la maintenance hebdomadaire"""
        try:
            print("\n" + "="*60)
            print(f"[SCHEDULER] 🧹 MAINTENANCE HEBDOMADAIRE - {datetime.now().strftime('%d/%m/%Y %H:%M')}")
            print("="*60)
            
            stats = {
                "timestamp": datetime.now().isoformat(),
                "auto_resolution": {},
                "purge": {}
            }
            
            # 1. Auto-résolution des états inactifs
            if self.config["auto_resolve_enabled"]:
                print("\n[SCHEDULER] 📋 Auto-résolution états inactifs...")
                
                try:
                    resolve_stats = auto_resolve_states(
                        json_manager=self.json_manager,
                        archiviste_controller=self.archiviste_controller,
                        threshold_days=self.config["resolve_threshold_days"],
                        dry_run=False,
                        require_llm_validation=self.config["require_llm_validation"]
                    )
                    
                    stats["auto_resolution"] = resolve_stats
                    print(f"[SCHEDULER] ✅ Auto-résolution: {resolve_stats}")
                
                except Exception as e:
                    print(f"[SCHEDULER] ERROR Auto-résolution: {e}")
                    stats["auto_resolution"]["error"] = str(e)
            
            # 2. Purge/compression entrées anciennes
            if self.config["auto_purge_enabled"] and self.purge_manager:
                print("\n[SCHEDULER] 🗜️ Purge entrées anciennes...")
                
                try:
                    purge_stats = self.purge_manager.purge_old_entries(
                        age_days=self.config["purge_age_days"],
                        mode=self.config["purge_mode"],
                        dry_run=False
                    )
                    
                    stats["purge"] = purge_stats
                    print(f"[SCHEDULER] ✅ Purge: {purge_stats}")
                
                except Exception as e:
                    print(f"[SCHEDULER] ERROR Purge: {e}")
                    stats["purge"]["error"] = str(e)
            
            # Mettre à jour dernière maintenance
            self.config["last_maintenance"] = datetime.now().isoformat()
            self._save_config()
            
            # Log résumé
            print("\n" + "="*60)
            print(f"[SCHEDULER] 🎉 MAINTENANCE TERMINÉE")
            print(f"[SCHEDULER] Auto-résolution: {stats['auto_resolution'].get('resolved', 0)} états résolus")
            print(f"[SCHEDULER] Purge: {stats['purge'].get('compressed', 0)} compressées, "
                  f"{stats['purge'].get('archived', 0)} archivées")
            print("="*60 + "\n")
            
            # Planifier prochaine exécution
            interval_seconds = self.config["maintenance_interval_days"] * 24 * 60 * 60
            self._schedule_next_run(interval_seconds)
        
        except Exception as e:
            print(f"[SCHEDULER] ERROR Maintenance: {e}")
            import traceback
            traceback.print_exc()
            
            # Réessayer quand même de planifier la prochaine
            try:
                interval_seconds = self.config["maintenance_interval_days"] * 24 * 60 * 60
                self._schedule_next_run(interval_seconds)
            except:
                pass
    
    def run_maintenance_now(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        Exécute la maintenance immédiatement (manuel)
        
        Args:
            dry_run: Mode simulation (défaut: False)
        
        Returns:
            Statistiques de maintenance
        """
        try:
            print(f"[SCHEDULER] {'🔍 SIMULATION' if dry_run else '🧹 MAINTENANCE'} MANUELLE")
            
            stats = {
                "timestamp": datetime.now().isoformat(),
                "dry_run": dry_run,
                "auto_resolution": {},
                "purge": {}
            }
            
            # Auto-résolution
            if self.config["auto_resolve_enabled"]:
                resolve_stats = auto_resolve_states(
                    json_manager=self.json_manager,
                    archiviste_controller=self.archiviste_controller,
                    threshold_days=self.config["resolve_threshold_days"],
                    dry_run=dry_run,
                    require_llm_validation=self.config["require_llm_validation"]
                )
                stats["auto_resolution"] = resolve_stats
            
            # Purge
            if self.config["auto_purge_enabled"] and self.purge_manager:
                purge_stats = self.purge_manager.purge_old_entries(
                    age_days=self.config["purge_age_days"],
                    mode=self.config["purge_mode"],
                    dry_run=dry_run
                )
                stats["purge"] = purge_stats
            
            print(f"[SCHEDULER] ✅ Maintenance manuelle terminée: {stats}")
            return stats
        
        except Exception as e:
            print(f"[SCHEDULER] ERROR Maintenance manuelle: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}
    
    def update_config(self, **kwargs) -> bool:
        """
        Met à jour la configuration
        
        Args:
            **kwargs: Paramètres à mettre à jour (auto_purge_enabled, purge_age_days, etc.)
        
        Returns:
            True si sauvegarde réussie
        """
        try:
            # Mettre à jour uniquement les clés valides
            valid_keys = self.default_config.keys()
            for key, value in kwargs.items():
                if key in valid_keys:
                    self.config[key] = value
                    print(f"[SCHEDULER] Config mise à jour: {key}={value}")
            
            # Sauvegarder
            success = self._save_config()
            
            # Redémarrer si nécessaire
            if self._is_running:
                self.stop()
                self.start()
            
            return success
        
        except Exception as e:
            print(f"[SCHEDULER] ERROR update_config: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Retourne le statut actuel du planificateur"""
        return {
            "is_running": self._is_running,
            "config": self.config,
            "next_maintenance": "Calculé à la prochaine exécution" if self._is_running else "Inactif"
        }


# Singleton instance
_scheduler_instance: Optional[MaintenanceScheduler] = None


def initialize_scheduler(
    json_manager,
    purge_manager,
    archiviste_controller,
    settings_path: Path,
    auto_start: bool = False
) -> Optional[MaintenanceScheduler]:
    """
    Initialise le planificateur de maintenance (pattern singleton)
    
    Args:
        json_manager: Instance JournalJSONManager
        purge_manager: Instance PurgeManager
        archiviste_controller: Contrôleur LLM Archiviste
        settings_path: Chemin journal_settings.json
        auto_start: Démarrer automatiquement (défaut: False)
    
    Returns:
        Instance MaintenanceScheduler ou None si erreur
    """
    global _scheduler_instance
    
    try:
        if _scheduler_instance is None:
            _scheduler_instance = MaintenanceScheduler(
                json_manager=json_manager,
                purge_manager=purge_manager,
                archiviste_controller=archiviste_controller,
                settings_path=settings_path
            )
            
            if auto_start:
                _scheduler_instance.start()
            
            print("[SCHEDULER] ✅ Instance singleton créée")
        
        return _scheduler_instance
    
    except Exception as e:
        print(f"[SCHEDULER] ERROR Initialisation: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_scheduler() -> Optional[MaintenanceScheduler]:
    """Retourne l'instance singleton du planificateur"""
    return _scheduler_instance


def stop_scheduler():
    """Arrête le planificateur global"""
    global _scheduler_instance
    if _scheduler_instance:
        _scheduler_instance.stop()
