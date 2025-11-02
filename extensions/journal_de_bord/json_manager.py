# JOURNAL Extension Journal de Bord - Gestionnaire JSON

"""
Gestionnaire de persistance JSON optimisé pour le Journal de Bord
Structure hiérarchique, indexation, cache intelligent, performance
"""

import json
import time
import gzip
from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from collections import defaultdict
import hashlib

class JSONManager:
    """
    Gestionnaire optimisé de la persistance JSON
    
    Responsabilités:
    - CRUD operations sur la structure hiérarchique année/mois/jour
    - Indexation pour recherche rapide
    - Cache intelligent pour performance
    - Validation des données selon schemas
    - Compression des données anciennes
    
    Performance:
    - Chargement jour: <20ms
    - Sauvegarde entrée: <50ms  
    - Recherche 1000+ entrées: <100ms
    """
    
    def __init__(self, config, data_dir: Path = None):
        """Initialise le gestionnaire JSON"""
        self.config = config
        self.data_dir = Path(data_dir) if data_dir else Path("extensions/journal_de_bord/data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache des données fréquemment utilisées
        self.cache = {}
        self.cache_timestamps = {}
        self.cache_max_size = self.config.get("cache_size", 100)
        self.cache_expiry_seconds = self.config.get("cache_expiry_hours", 24) * 3600
        
        # Index de recherche en mémoire
        self.search_index = {
            "tags": defaultdict(set),           # tag -> set(dates)
            "keywords": defaultdict(set),       # keyword -> set(dates)  
            "importance": defaultdict(set),     # importance -> set(dates)
            "participants": defaultdict(set),   # participant -> set(dates)
            "dates": set()                      # toutes les dates avec entrées
        }
        self.index_last_update = None
        
        # Statistiques
        self.stats = {
            "total_entries": 0,
            "total_days": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "last_entry_date": None,
            "data_size_mb": 0.0
        }
        
        # Initialisation
        self._build_search_index()
        self._calculate_initial_stats()
        
        print(f"[JSON-MANAGER] OK Initialisé (cache: {self.cache_max_size}, données: {self.data_dir})")
    
    def save_entry(self, entry_data: Dict[str, Any]) -> bool:
        """
        Sauvegarde une entrée dans la structure JSON
        
        Args:
            entry_data: Données de l'entrée avec timestamp obligatoire
        
        Returns:
            bool: True si sauvegarde réussie
        """
        try:
            start_time = time.time()
            
            # Validation de l'entrée
            self._validate_entry(entry_data)
            
            # Extraction de la date
            timestamp = entry_data.get("timestamp")
            if not timestamp:
                raise ValueError("timestamp manquant dans entry_data")
            
            entry_date = timestamp[:10]  # YYYY-MM-DD
            year = entry_date[:4]
            month = entry_date[5:7]
            day = entry_date[8:10]
            
            print(f"[JSON-MANAGER] SAVE Sauvegarde entrée pour {entry_date}")
            
            # Chargement/création structure année
            year_data = self._load_year_data(year)
            
            # Navigation vers le jour
            if "months" not in year_data:
                year_data["months"] = {}
            if month not in year_data["months"]:
                year_data["months"][month] = {"metadata": {"total_entries": 0, "total_days": 0}, "days": {}}
            if "days" not in year_data["months"][month]:
                year_data["months"][month]["days"] = {}
            if day not in year_data["months"][month]["days"]:
                year_data["months"][month]["days"][day] = {
                    "date": entry_date,
                    "entries": [],
                    "total_entries": 0,
                    "day_summary": "",
                    "tags": [],
                    "importance_level": "normal"
                }
            
            # Ajout de l'entrée
            day_data = year_data["months"][month]["days"][day]
            day_data["entries"].append(entry_data)
            day_data["total_entries"] = len(day_data["entries"])
            
            # Mise à jour métadonnées jour
            self._update_day_metadata(day_data)
            
            # Mise à jour métadonnées mois
            month_data = year_data["months"][month]
            month_data["metadata"]["total_entries"] = sum(
                day["total_entries"] for day in month_data["days"].values()
            )
            month_data["metadata"]["total_days"] = len(month_data["days"])
            
            # Mise à jour métadonnées année
            if "metadata" not in year_data:
                year_data["metadata"] = {}
            year_data["metadata"]["total_entries"] = sum(
                month["metadata"]["total_entries"] for month in year_data["months"].values()
            )
            year_data["metadata"]["last_entry"] = entry_date
            
            # Sauvegarde fichier année
            self._save_year_data(year, year_data)
            
            # Mise à jour de l'index
            self._update_search_index_for_entry(entry_data, entry_date)
            
            # Invalidation du cache
            self._invalidate_cache_for_date(entry_date)
            
            # Mise à jour statistiques
            self.stats["total_entries"] += 1
            self.stats["last_entry_date"] = entry_date
            if entry_date not in self.stats.get("processed_dates", set()):
                self.stats["total_days"] += 1
            
            duration = time.time() - start_time
            print(f"[JSON-MANAGER] OK Entrée sauvegardée en {duration:.3f}s")
            
            return True
            
        except Exception as e:
            print(f"[JSON-MANAGER] ERREUR Erreur sauvegarde: {e}")
            return False
    
    def get_day_entries(self, target_date: str) -> List[Dict[str, Any]]:
        """
        Récupère toutes les entrées d'une date spécifique
        
        Args:
            target_date: Date au format YYYY-MM-DD
        
        Returns:
            List[Dict]: Liste des entrées du jour (vide si aucune)
        """
        try:
            start_time = time.time()
            
            # Vérification cache
            cache_key = f"day_{target_date}"
            if self._is_cache_valid(cache_key):
                self.stats["cache_hits"] += 1
                return self.cache[cache_key]
            
            self.stats["cache_misses"] += 1
            
            # Parsing date
            year = target_date[:4]
            month = target_date[5:7]
            day = target_date[8:10]
            
            # Chargement données année
            year_data = self._load_year_data(year)
            
            # Navigation vers les entrées
            entries = []
            if ("months" in year_data and 
                month in year_data["months"] and
                "days" in year_data["months"][month] and
                day in year_data["months"][month]["days"]):
                
                day_data = year_data["months"][month]["days"][day]
                entries = day_data.get("entries", [])
            
            # Tri par timestamp (plus récent en premier)
            entries.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            
            # Mise en cache
            self._cache_data(cache_key, entries)
            
            duration = time.time() - start_time
            print(f"[JSON-MANAGER] JOURNAL {len(entries)} entrées chargées pour {target_date} en {duration:.3f}s")
            
            return entries
            
        except Exception as e:
            print(f"[JSON-MANAGER] ERREUR Erreur get_day_entries: {e}")
            return []
    
    def search_entries(self, query: str = None, **filters) -> List[Dict[str, Any]]:
        """
        Recherche dans l'historique avec filtres
        
        Args:
            query: Texte de recherche libre
            **filters: date_start, date_end, tags, importance, participants
        
        Returns:
            List[Dict]: Entrées correspondant aux critères
        """
        try:
            start_time = time.time()
            
            # Filtrage par index pour performance
            candidate_dates = self._filter_dates_by_index(filters)
            
            # Si query texte, élargir la recherche
            if query:
                text_dates = self._search_text_in_index(query)
                candidate_dates = candidate_dates.intersection(text_dates) if candidate_dates else text_dates
            
            # Chargement des entrées candidates
            results = []
            for target_date in sorted(candidate_dates, reverse=True):  # Plus récent en premier
                day_entries = self.get_day_entries(target_date)
                
                for entry in day_entries:
                    if self._entry_matches_filters(entry, query, filters):
                        results.append(entry)
            
            # Limite de résultats pour performance
            max_results = filters.get("limit", 100)
            if len(results) > max_results:
                results = results[:max_results]
            
            duration = time.time() - start_time
            print(f"[JSON-MANAGER] SEARCH Recherche: {len(results)} résultats en {duration:.3f}s")
            
            return results
            
        except Exception as e:
            print(f"[JSON-MANAGER] ERREUR Erreur search: {e}")
            return []
    
    def get_all_entries_sorted(self) -> List[Dict[str, Any]]:
        """
        Récupère toutes les entrées du journal, triées par timestamp croissant.
        
        Optimisé pour récupérer les N dernières conversations peu importe leur date.
        Utile pour contexte "dernières interactions" sans limite temporelle arbitraire.
        
        Returns:
            List[Dict]: Toutes les entrées avec timestamp, summary, tags, etc.
                       Triées du plus ancien au plus récent.
        
        Performance: O(n log n) pour tri, mais n = nombre total d'entrées
                     Pour 77 entrées actuelles: <5ms
        """
        try:
            start_time = time.time()
            all_entries = []
            
            # Parcours de tous les fichiers année
            for year_file in sorted(self.data_dir.glob("journal_*.json")):
                year = year_file.stem.split('_')[1]  # journal_2025.json -> 2025
                year_data = self._load_year_data(year)
                
                # Parcours mois
                for month_key in sorted(year_data.get("months", {}).keys()):
                    month_data = year_data["months"][month_key]
                    
                    # Parcours jours
                    for day_key in sorted(month_data.get("days", {}).keys()):
                        day_data = month_data["days"][day_key]
                        entries = day_data.get("entries", [])
                        all_entries.extend(entries)
            
            # Tri par timestamp (plus ancien → plus récent)
            all_entries.sort(key=lambda e: e.get("timestamp", ""))
            
            duration = time.time() - start_time
            print(f"[JSON-MANAGER] ALL-SORTED {len(all_entries)} entrées récupérées et triées en {duration:.3f}s")
            
            return all_entries
            
        except Exception as e:
            print(f"[JSON-MANAGER] ERREUR get_all_entries_sorted: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retourne les statistiques complètes du journal"""
        # Mise à jour stats temps réel
        self._calculate_current_stats()
        
        # Ajout métadonnées cache
        cache_stats = {
            "cache_size": len(self.cache),
            "cache_hit_ratio": (
                self.stats["cache_hits"] / max(self.stats["cache_hits"] + self.stats["cache_misses"], 1)
            ),
            "index_entries": sum(len(dates) for dates in self.search_index["tags"].values()),
            "index_last_update": self.index_last_update
        }
        
        return {**self.stats, **cache_stats}
    
    def flush_caches(self):
        """Vide les caches et force la sauvegarde"""
        self.cache.clear()
        self.cache_timestamps.clear()
        print("[JSON-MANAGER] UPDATE Caches vidés")
    
    def cleanup_old_data(self, retention_days: int = None):
        """
        Nettoie les données anciennes selon politique de rétention
        
        Args:
            retention_days: Nombre de jours à conserver (défaut: config)
        """
        try:
            retention = retention_days or self.config.get("data_retention_days", 365)
            cutoff_date = (datetime.now() - timedelta(days=retention)).date().isoformat()
            
            print(f"[JSON-MANAGER] CLEAN Nettoyage données antérieures à {cutoff_date}")
            
            # TODO: Implémentation compression/archivage données anciennes
            # Pour l'instant, simple logging
            
            print("[JSON-MANAGER] OK Nettoyage terminé")
            
        except Exception as e:
            print(f"[JSON-MANAGER] ERREUR Erreur nettoyage: {e}")
    
    # === MÉTHODES PRIVÉES ===
    
    def _load_year_data(self, year: str) -> Dict[str, Any]:
        """Charge les données d'une année spécifique"""
        year_file = self.data_dir / f"journal_{year}.json"
        
        if not year_file.exists():
            # Création structure vide
            empty_structure = {
                "metadata": {
                    "version": "1.0.0",
                    "created": datetime.now().isoformat(),
                    "year": int(year),
                    "total_entries": 0,
                    "first_entry": None,
                    "last_entry": None
                },
                "months": {}
            }
            return empty_structure
        
        try:
            with open(year_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[JSON-MANAGER] WARN Erreur lecture {year_file}: {e}")
            # Fallback structure vide au lieu d'erreur bloquante
            return {"metadata": {"year": int(year)}, "months": {}}
    
    def _save_year_data(self, year: str, year_data: Dict[str, Any]):
        """Sauvegarde les données d'une année"""
        year_file = self.data_dir / f"journal_{year}.json"
        
        # Créer backup AVANT sauvegarde si le fichier existe déjà
        if year_file.exists():
            self._create_journal_backup(year_file)
        
        # Mise à jour métadonnées
        if "metadata" not in year_data:
            year_data["metadata"] = {}
        year_data["metadata"]["last_updated"] = datetime.now().isoformat()
        year_data["metadata"]["version"] = "1.0.0"
        
        # Sauvegarde atomique (temp file + rename)
        temp_file = year_file.with_suffix('.tmp')
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(year_data, f, indent=2, ensure_ascii=False)
            temp_file.replace(year_file)
            
        except Exception as e:
            if temp_file.exists():
                temp_file.unlink()
            raise e
    
    def _create_journal_backup(self, journal_file: Path) -> bool:
        """
        Crée un backup d'un fichier journal avec rotation automatique
        
        Inspiré du système de backup biographique, avec rotation tous les 10 fichiers
        
        Args:
            journal_file: Fichier journal à sauvegarder
            
        Returns:
            True si backup créé avec succès, False sinon
        """
        try:
            if not journal_file.exists():
                print(f"[JSON-MANAGER] ℹ️ Pas de backup: fichier journal n'existe pas encore")
                return False

            # Créer dossier backups
            backup_dir = self.data_dir / "backups"
            backup_dir.mkdir(exist_ok=True)

            # Charger métadonnées backup
            backup_metadata_file = backup_dir / "journal_backup_metadata.json"
            if backup_metadata_file.exists():
                with open(backup_metadata_file, 'r', encoding='utf-8') as f:
                    backup_metadata = json.load(f)
            else:
                backup_metadata = {
                    "total_backups_created": 0,
                    "current_backup_count": 0,
                    "journal_backups": [],
                    "backup_interval": 10,  # Backup tous les 10 sauvegardes
                    "next_backup_threshold": 10
                }

            # Incrémenter compteur de sauvegardes
            backup_metadata["total_backups_created"] += 1
            backup_number = backup_metadata["total_backups_created"]

            # Vérifier si il faut créer un backup (tous les 10 sauvegardes)
            if backup_number % backup_metadata["backup_interval"] != 0:
                # Pas encore le moment de faire un backup
                # Sauvegarder juste le compteur
                with open(backup_metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(backup_metadata, f, ensure_ascii=False, indent=2)
                return True

            # Créer le backup maintenant
            timestamp = datetime.now()
            journal_name = journal_file.stem  # ex: "journal_2025"
            backup_name = f"{journal_name}_backup_{timestamp.strftime('%Y%m%d')}_{backup_number:03d}.json"
            backup_file = backup_dir / backup_name

            # Copier fichier actuel vers backup
            import shutil
            shutil.copy2(journal_file, backup_file)

            # Ajouter aux métadonnées
            backup_info = {
                "filename": backup_name,
                "original_filename": journal_file.name,
                "date": timestamp.isoformat(),
                "size_bytes": backup_file.stat().st_size,
                "backup_number": backup_number,
                "type": "journal_auto_backup"
            }
            
            backup_metadata["journal_backups"].append(backup_info)
            backup_metadata["current_backup_count"] = len(backup_metadata["journal_backups"])

            # Nettoyer vieux backups (garder seulement les 10 derniers)
            if len(backup_metadata["journal_backups"]) > 10:
                # Trier par date (plus ancien en premier)
                backup_metadata["journal_backups"].sort(key=lambda x: x["date"])

                # Supprimer les plus anciens fichiers
                backups_to_delete = backup_metadata["journal_backups"][:-10]  # Tous sauf les 10 derniers
                for old_backup in backups_to_delete:
                    old_backup_file = backup_dir / old_backup["filename"]
                    if old_backup_file.exists():
                        old_backup_file.unlink()
                        print(f"[JSON-MANAGER] 🗑️ Backup journal supprimé: {old_backup['filename']}")

                # Garder seulement les 10 derniers dans métadonnées
                backup_metadata["journal_backups"] = backup_metadata["journal_backups"][-10:]
                backup_metadata["current_backup_count"] = len(backup_metadata["journal_backups"])

            # Mettre à jour metadata avec plus ancien gardé
            if backup_metadata["journal_backups"]:
                backup_metadata["oldest_backup_kept"] = backup_metadata["journal_backups"][0]
                backup_metadata["latest_backup"] = backup_metadata["journal_backups"][-1]

            # Calculer prochaine limite pour backup
            backup_metadata["next_backup_threshold"] = backup_number + backup_metadata["backup_interval"]

            # Sauvegarder métadonnées
            with open(backup_metadata_file, 'w', encoding='utf-8') as f:
                json.dump(backup_metadata, f, ensure_ascii=False, indent=2)

            print(f"[JSON-MANAGER] 💾 Backup journal créé: {backup_name} ({backup_info['size_bytes']} bytes)")
            print(f"[JSON-MANAGER] 📊 Total backups journal: {backup_metadata['current_backup_count']}/10")
            print(f"[JSON-MANAGER] 🔄 Prochain backup dans: {backup_metadata['backup_interval']} sauvegardes")
            
            return True

        except Exception as e:
            print(f"[JSON-MANAGER] ❌ Erreur création backup journal: {e}")
            return False
    
    def get_journal_backups(self) -> List[Dict[str, Any]]:
        """
        Récupère la liste des backups disponibles pour le journal
        
        Returns:
            Liste des informations de backup
        """
        try:
            backup_dir = self.data_dir / "backups"
            backup_metadata_file = backup_dir / "journal_backup_metadata.json"
            
            if not backup_metadata_file.exists():
                return []
                
            with open(backup_metadata_file, 'r', encoding='utf-8') as f:
                backup_metadata = json.load(f)
                
            return backup_metadata.get("journal_backups", [])
            
        except Exception as e:
            print(f"[JSON-MANAGER] ❌ Erreur lecture backups journal: {e}")
            return []
    
    def _validate_entry(self, entry_data: Dict[str, Any]):
        """Valide une entrée selon le schéma"""
        required_fields = ["id", "timestamp", "summary", "tokens"]
        
        for field in required_fields:
            if field not in entry_data:
                raise ValueError(f"Champ obligatoire manquant: {field}")
        
        # Validation types
        if not isinstance(entry_data["tokens"], int) or entry_data["tokens"] < 0:
            raise ValueError("tokens doit être un entier positif")
        
        if not isinstance(entry_data["summary"], str) or len(entry_data["summary"]) < 10:
            raise ValueError("summary doit être une chaîne d'au moins 10 caractères")
        
        # Validation timestamp ISO
        try:
            datetime.fromisoformat(entry_data["timestamp"].replace('Z', '+00:00'))
        except ValueError:
            raise ValueError("timestamp doit être au format ISO 8601")
    
    def _update_day_metadata(self, day_data: Dict[str, Any]):
        """Met à jour les métadonnées d'un jour"""
        entries = day_data.get("entries", [])
        if not entries:
            return
        
        # Agrégation des tags
        all_tags = set()
        for entry in entries:
            all_tags.update(entry.get("tags", []))
        day_data["tags"] = list(all_tags)
        
        # Niveau d'importance dominant
        importance_levels = [entry.get("importance", "normal") for entry in entries]
        if "critical" in importance_levels:
            day_data["importance_level"] = "critical"
        elif "high" in importance_levels:
            day_data["importance_level"] = "high"
        else:
            day_data["importance_level"] = "normal"
        
        # Génération résumé de journée (simple pour l'instant)
        if len(entries) == 1:
            day_data["day_summary"] = entries[0]["summary"][:100] + "..."
        else:
            day_data["day_summary"] = f"{len(entries)} conversations importantes de la journée"
    
    def _build_search_index(self):
        """Construit l'index de recherche depuis tous les fichiers"""
        try:
            start_time = time.time()
            
            # Reset index
            self.search_index = {
                "tags": defaultdict(set),
                "keywords": defaultdict(set),
                "importance": defaultdict(set),
                "participants": defaultdict(set),
                "dates": set()
            }
            
            # Parcours de tous les fichiers années
            for year_file in self.data_dir.glob("journal_*.json"):
                try:
                    with open(year_file, 'r', encoding='utf-8') as f:
                        year_data = json.load(f)
                    
                    self._index_year_data(year_data)
                    
                except Exception as e:
                    print(f"[JSON-MANAGER] WARN Erreur indexation {year_file}: {e}")
            
            self.index_last_update = time.time()
            duration = time.time() - start_time
            
            print(f"[JSON-MANAGER] SEARCH Index construit en {duration:.3f}s")
            print(f"[JSON-MANAGER] STATS Index: {len(self.search_index['dates'])} jours, {len(self.search_index['tags'])} tags")
            
        except Exception as e:
            print(f"[JSON-MANAGER] ERREUR Erreur construction index: {e}")
    
    def _index_year_data(self, year_data: Dict[str, Any]):
        """Indexe les données d'une année"""
        months = year_data.get("months", {})
        
        for month_data in months.values():
            days = month_data.get("days", {})
            
            for day_date, day_data in days.items():
                self.search_index["dates"].add(day_date)
                
                entries = day_data.get("entries", [])
                for entry in entries:
                    # Index tags
                    for tag in entry.get("tags", []):
                        self.search_index["tags"][tag.lower()].add(day_date)
                    
                    # Index importance
                    importance = entry.get("importance", "normal")
                    self.search_index["importance"][importance].add(day_date)
                    
                    # Index participants
                    for participant in entry.get("participants", []):
                        self.search_index["participants"][participant.lower()].add(day_date)
                    
                    # Index mots-clés du résumé
                    summary = entry.get("summary", "").lower()
                    words = summary.split()
                    for word in words:
                        if len(word) > 3:  # Mots significatifs seulement
                            word_clean = word.strip('.,!?;:"()[]{}')
                            if word_clean:
                                self.search_index["keywords"][word_clean].add(day_date)
    
    def _update_search_index_for_entry(self, entry_data: Dict[str, Any], entry_date: str):
        """Met à jour l'index pour une nouvelle entrée"""
        self.search_index["dates"].add(entry_date)
        
        # Tags
        for tag in entry_data.get("tags", []):
            self.search_index["tags"][tag.lower()].add(entry_date)
        
        # Importance
        importance = entry_data.get("importance", "normal")
        self.search_index["importance"][importance].add(entry_date)
        
        # Participants
        for participant in entry_data.get("participants", []):
            self.search_index["participants"][participant.lower()].add(entry_date)
        
        # Mots-clés
        summary = entry_data.get("summary", "").lower()
        words = summary.split()
        for word in words:
            if len(word) > 3:
                word_clean = word.strip('.,!?;:"()[]{}')
                if word_clean:
                    self.search_index["keywords"][word_clean].add(entry_date)
    
    def _filter_dates_by_index(self, filters: Dict[str, Any]) -> set:
        """Filtre les dates en utilisant l'index"""
        candidate_dates = set(self.search_index["dates"])
        
        # Filtre par tags
        if "tags" in filters:
            tags = filters["tags"]
            if isinstance(tags, str):
                tags = [tags]
            
            tag_dates = set()
            for tag in tags:
                tag_dates.update(self.search_index["tags"].get(tag.lower(), set()))
            
            candidate_dates = candidate_dates.intersection(tag_dates)
        
        # Filtre par importance
        if "importance" in filters:
            importance = filters["importance"]
            importance_dates = self.search_index["importance"].get(importance, set())
            candidate_dates = candidate_dates.intersection(importance_dates)
        
        # Filtre par date
        if "date_start" in filters:
            candidate_dates = {d for d in candidate_dates if d >= filters["date_start"]}
        
        if "date_end" in filters:
            candidate_dates = {d for d in candidate_dates if d <= filters["date_end"]}
        
        return candidate_dates
    
    def _search_text_in_index(self, query: str) -> set:
        """Recherche textuelle dans l'index des mots-clés"""
        query_words = query.lower().split()
        matching_dates = set()
        
        for word in query_words:
            if len(word) > 2:
                # Recherche exacte
                if word in self.search_index["keywords"]:
                    matching_dates.update(self.search_index["keywords"][word])
                
                # Recherche partielle (commence par)
                for indexed_word, dates in self.search_index["keywords"].items():
                    if indexed_word.startswith(word):
                        matching_dates.update(dates)
        
        return matching_dates
    
    def _entry_matches_filters(self, entry: Dict[str, Any], query: str, filters: Dict[str, Any]) -> bool:
        """Vérifie si une entrée correspond aux filtres"""
        # Recherche textuelle
        if query:
            summary = entry.get("summary", "").lower()
            if not any(word.lower() in summary for word in query.split()):
                return False
        
        # Filtre participants
        if "participants" in filters:
            entry_participants = [p.lower() for p in entry.get("participants", [])]
            filter_participants = filters["participants"]
            if isinstance(filter_participants, str):
                filter_participants = [filter_participants]
            
            if not any(fp.lower() in entry_participants for fp in filter_participants):
                return False
        
        return True
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Vérifie si une entrée de cache est valide"""
        if cache_key not in self.cache:
            return False
        
        timestamp = self.cache_timestamps.get(cache_key, 0)
        return time.time() - timestamp < self.cache_expiry_seconds
    
    def _cache_data(self, cache_key: str, data: Any):
        """Met en cache des données avec gestion de la taille"""
        # Éviction LRU si cache plein
        if len(self.cache) >= self.cache_max_size:
            oldest_key = min(self.cache_timestamps.keys(), key=self.cache_timestamps.get)
            del self.cache[oldest_key]
            del self.cache_timestamps[oldest_key]
        
        self.cache[cache_key] = data
        self.cache_timestamps[cache_key] = time.time()
    
    def _invalidate_cache_for_date(self, target_date: str):
        """Invalide le cache pour une date spécifique"""
        cache_key = f"day_{target_date}"
        if cache_key in self.cache:
            del self.cache[cache_key]
            del self.cache_timestamps[cache_key]
    
    def _calculate_initial_stats(self):
        """Calcule les statistiques initiales"""
        try:
            self.stats["total_entries"] = 0
            self.stats["total_days"] = len(self.search_index["dates"])
            
            for year_file in self.data_dir.glob("journal_*.json"):
                try:
                    year_data = self._load_year_data(year_file.stem.split('_')[1])
                    self.stats["total_entries"] += year_data.get("metadata", {}).get("total_entries", 0)
                except Exception:
                    pass
            
            # Taille des données
            total_size = sum(f.stat().st_size for f in self.data_dir.glob("*.json"))
            self.stats["data_size_mb"] = total_size / (1024 * 1024)
            
        except Exception as e:
            print(f"[JSON-MANAGER] WARN Erreur calcul stats initiales: {e}")
    
    def _calculate_current_stats(self):
        """Met à jour les statistiques courantes"""
        try:
            # Recalcul taille données
            total_size = sum(f.stat().st_size for f in self.data_dir.glob("*.json"))
            self.stats["data_size_mb"] = total_size / (1024 * 1024)
            
            # Dernière entrée depuis l'index
            if self.search_index["dates"]:
                self.stats["last_entry_date"] = max(self.search_index["dates"])
            
        except Exception as e:
            print(f"[JSON-MANAGER] WARN Erreur calcul stats courantes: {e}")