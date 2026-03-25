"""
OGMA - Journal de Bord v2.0
Module de gestion de purge et archivage des entrées anciennes

Fonctionnalités :
- Compression d'entrées anciennes via LLM (Archiviste)
- Transfert FAISS pour archivage intelligent avec recherche sémantique
- Purge sélective avec backup automatique
- Restauration d'entrées compressées

Pattern : Singleton avec lazy initialization
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path


class PurgeManager:
    """Gestionnaire de purge et archivage intelligent des entrées Journal"""
    
    def __init__(self, json_manager, memory_manager=None, archiviste_controller=None):
        """
        Initialise le gestionnaire de purge
        
        Args:
            json_manager: Instance JournalJSONManager pour accès données
            memory_manager: Instance MemoryManager pour archivage FAISS (optionnel)
            archiviste_controller: Contrôleur LLM pour compression (optionnel)
        """
        self.json_manager = json_manager
        self.memory_manager = memory_manager
        self.archiviste_controller = archiviste_controller
        
        # Config paths
        self.data_dir = json_manager.data_dir
        self.backup_dir = self.data_dir / "purge_backups"
        self.backup_dir.mkdir(exist_ok=True)
        
        print("[PURGE-MANAGER] Initialisé")
    
    def get_purgeable_entries(self, age_days: int = 90, exclude_active_states: bool = True) -> List[Dict[str, Any]]:
        """
        Récupère les entrées éligibles pour purge selon l'âge
        
        Args:
            age_days: Âge minimum en jours (défaut: 90j)
            exclude_active_states: Exclure entrées avec états actifs non résolus (défaut: True)
        
        Returns:
            Liste d'entrées avec métadonnées {entry_id, date, age_days, has_active_states, size_bytes}
        """
        try:
            print(f"[PURGE-MANAGER] Recherche entrées >{age_days}j")
            
            cutoff_date = datetime.now() - timedelta(days=age_days)
            purgeable = []
            
            # Parcourir toutes les entrées
            for year in self.json_manager.data_dir.iterdir():
                if not year.is_dir() or not year.name.isdigit():
                    continue
                
                for month in year.iterdir():
                    if not month.is_dir() or not month.name.isdigit():
                        continue
                    
                    for day_file in month.glob("*.json"):
                        date_str = day_file.stem  # YYYY-MM-DD
                        
                        try:
                            entry_date = datetime.strptime(date_str, "%Y-%m-%d")
                            
                            # Vérifier âge
                            if entry_date >= cutoff_date:
                                continue
                            
                            # Charger entrée
                            with open(day_file, 'r', encoding='utf-8') as f:
                                entry_data = json.load(f)
                            
                            # Vérifier états actifs
                            active_states = entry_data.get("active_states", [])
                            unresolved_states = [s for s in active_states if not s.get("resolved", False)]
                            has_active_states = len(unresolved_states) > 0
                            
                            # Exclure si états actifs non résolus
                            if exclude_active_states and has_active_states:
                                continue
                            
                            # Calculer métadonnées
                            age = (datetime.now() - entry_date).days
                            size_bytes = day_file.stat().st_size
                            
                            purgeable.append({
                                "entry_id": entry_data.get("entry_id"),
                                "date": date_str,
                                "timestamp": entry_data.get("timestamp"),
                                "age_days": age,
                                "has_active_states": has_active_states,
                                "size_bytes": size_bytes,
                                "compressed": entry_data.get("compressed", False),
                                "archived_to_faiss": entry_data.get("archived_to_faiss", False),
                                "file_path": str(day_file)
                            })
                        
                        except Exception as e:
                            print(f"[PURGE-MANAGER] WARN Erreur lecture {day_file}: {e}")
                            continue
            
            print(f"[PURGE-MANAGER] ✅ Trouvé {len(purgeable)} entrées purgeable")
            return sorted(purgeable, key=lambda x: x["age_days"], reverse=True)
        
        except Exception as e:
            print(f"[PURGE-MANAGER] ERROR get_purgeable_entries: {e}")
            return []
    
    def compress_entry(self, entry_id: int, max_summary_chars: int = 500) -> Tuple[bool, str]:
        """
        Compresse une entrée via résumé LLM tout en conservant métadonnées
        
        Args:
            entry_id: ID de l'entrée à compresser
            max_summary_chars: Taille max du résumé (défaut: 500 chars)
        
        Returns:
            Tuple (success: bool, message: str)
        """
        try:
            if not self.archiviste_controller:
                return False, "Archiviste non disponible - compression impossible"
            
            print(f"[PURGE-MANAGER] 🗜️ Compression entrée #{entry_id}")
            
            # Récupérer entrée complète
            entry_data = self.json_manager.get_entry_by_id(entry_id)
            if not entry_data:
                return False, f"Entrée #{entry_id} introuvable"
            
            # Vérifier si déjà compressée
            if entry_data.get("compressed", False):
                return False, "Entrée déjà compressée"
            
            # Backup avant compression
            backup_success = self._create_backup(entry_data, "pre_compression")
            if not backup_success:
                return False, "Échec backup pré-compression"
            
            # Extraction contenu original
            original_content = entry_data.get("content", "")
            original_size = len(original_content)
            
            # Génération résumé via Archiviste
            summary_prompt = f"""Résume cette entrée de journal en maximum {max_summary_chars} caractères.
Conserve les informations essentielles : événements clés, émotions, décisions importantes.
Sois concis et factuel.

ENTRÉE ORIGINALE :
{original_content}

RÉSUMÉ (max {max_summary_chars} chars) :"""
            
            try:
                # Appel LLM Archiviste
                summary = self.archiviste_controller.send_message(
                    message=summary_prompt,
                    context="",
                    system_prompt="Tu es un archiviste méthodique. Résume les informations de manière dense et précise."
                )
                
                # Validation longueur
                if len(summary) > max_summary_chars * 1.2:  # Tolérance 20%
                    summary = summary[:max_summary_chars] + "..."
                
            except Exception as e:
                print(f"[PURGE-MANAGER] ERROR Compression LLM: {e}")
                return False, f"Erreur génération résumé: {e}"
            
            # Mise à jour entrée avec version compressée
            entry_data["content_original"] = original_content  # Backup original
            entry_data["content"] = summary  # Remplacer par résumé
            entry_data["compressed"] = True
            entry_data["compressed_at"] = datetime.now().isoformat()
            entry_data["compression_ratio"] = round(len(summary) / original_size, 2)
            
            # Sauvegarder entrée modifiée
            save_success = self.json_manager._save_entry_to_file(entry_data)
            if not save_success:
                return False, "Échec sauvegarde entrée compressée"
            
            compression_ratio = entry_data["compression_ratio"]
            print(f"[PURGE-MANAGER] ✅ Compression réussie : {original_size}→{len(summary)} chars (ratio: {compression_ratio})")
            
            return True, f"Compression réussie (ratio: {compression_ratio})"
        
        except Exception as e:
            print(f"[PURGE-MANAGER] ERROR compress_entry: {e}")
            import traceback
            traceback.print_exc()
            return False, f"Erreur compression: {e}"
    
    def transfer_to_faiss(self, entry_id: int) -> Tuple[bool, str]:
        """
        Transfère une entrée vers FAISS pour archivage avec recherche sémantique
        
        Args:
            entry_id: ID de l'entrée à archiver
        
        Returns:
            Tuple (success: bool, message: str)
        """
        try:
            if not self.memory_manager:
                return False, "MemoryManager non disponible - transfert FAISS impossible"
            
            print(f"[PURGE-MANAGER] 📦 Transfert FAISS entrée #{entry_id}")
            
            # Récupérer entrée
            entry_data = self.json_manager.get_entry_by_id(entry_id)
            if not entry_data:
                return False, f"Entrée #{entry_id} introuvable"
            
            # Vérifier si déjà archivée
            if entry_data.get("archived_to_faiss", False):
                return False, "Entrée déjà archivée FAISS"
            
            # Préparer contenu pour embedding
            content = entry_data.get("content", "")
            date = entry_data.get("date", "")
            category = entry_data.get("category", "général")
            
            # Construire texte enrichi pour embedding
            embedding_text = f"[Journal {date}] Catégorie: {category}\n{content}"
            
            # Métadonnées pour FAISS
            metadata = {
                "source": "journal",
                "entry_id": entry_id,
                "date": date,
                "category": category,
                "timestamp": entry_data.get("timestamp", ""),
                "compressed": entry_data.get("compressed", False)
            }
            
            # Injection dans MemoryManager
            try:
                self.memory_manager.add_memory(
                    content=embedding_text,
                    role="journal_archive",
                    metadata=metadata
                )
                
                print(f"[PURGE-MANAGER] ✅ Transfert FAISS réussi")
                
            except Exception as e:
                print(f"[PURGE-MANAGER] ERROR Injection FAISS: {e}")
                return False, f"Erreur injection FAISS: {e}"
            
            # Marquer entrée comme archivée
            entry_data["archived_to_faiss"] = True
            entry_data["archived_at"] = datetime.now().isoformat()
            
            save_success = self.json_manager._save_entry_to_file(entry_data)
            if not save_success:
                return False, "Échec marquage archive FAISS"
            
            return True, "Transfert FAISS réussi"
        
        except Exception as e:
            print(f"[PURGE-MANAGER] ERROR transfer_to_faiss: {e}")
            import traceback
            traceback.print_exc()
            return False, f"Erreur transfert FAISS: {e}"
    
    def purge_old_entries(
        self, 
        age_days: int = 90, 
        mode: str = "compress", 
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """
        Purge les entrées anciennes selon le mode choisi
        
        Args:
            age_days: Âge minimum en jours (défaut: 90j)
            mode: Mode purge - "compress" (compression seule) ou "archive" (compression + FAISS)
            dry_run: Mode simulation sans modification (défaut: True)
        
        Returns:
            Statistiques {total, compressed, archived, failed, errors}
        """
        try:
            print(f"[PURGE-MANAGER] {'🔍 SIMULATION' if dry_run else '🗑️ PURGE'} mode={mode}, age={age_days}j")
            
            # Récupérer entrées purgeable
            purgeable_entries = self.get_purgeable_entries(age_days=age_days)
            
            stats = {
                "total": len(purgeable_entries),
                "compressed": 0,
                "archived": 0,
                "failed": 0,
                "errors": []
            }
            
            if dry_run:
                print(f"[PURGE-MANAGER] MODE SIMULATION - {stats['total']} entrées détectées (aucune modification)")
                return stats
            
            # Traitement des entrées
            for entry_info in purgeable_entries:
                entry_id = entry_info["entry_id"]
                
                try:
                    # Compression
                    if not entry_info["compressed"]:
                        compress_success, compress_msg = self.compress_entry(entry_id)
                        if compress_success:
                            stats["compressed"] += 1
                        else:
                            stats["errors"].append(f"Compression #{entry_id}: {compress_msg}")
                            stats["failed"] += 1
                            continue
                    
                    # Archivage FAISS (si mode "archive")
                    if mode == "archive" and not entry_info["archived_to_faiss"]:
                        archive_success, archive_msg = self.transfer_to_faiss(entry_id)
                        if archive_success:
                            stats["archived"] += 1
                        else:
                            stats["errors"].append(f"Archive #{entry_id}: {archive_msg}")
                            stats["failed"] += 1
                
                except Exception as e:
                    print(f"[PURGE-MANAGER] ERROR Traitement #{entry_id}: {e}")
                    stats["errors"].append(f"#{entry_id}: {str(e)}")
                    stats["failed"] += 1
            
            print(f"[PURGE-MANAGER] ✅ Purge terminée : {stats}")
            return stats
        
        except Exception as e:
            print(f"[PURGE-MANAGER] ERROR purge_old_entries: {e}")
            import traceback
            traceback.print_exc()
            return {"error": str(e)}
    
    def restore_compressed_entry(self, entry_id: int) -> Tuple[bool, str]:
        """
        Restaure une entrée compressée (si original disponible)
        
        Args:
            entry_id: ID de l'entrée à restaurer
        
        Returns:
            Tuple (success: bool, message: str)
        """
        try:
            print(f"[PURGE-MANAGER] 🔄 Restauration entrée #{entry_id}")
            
            # Récupérer entrée
            entry_data = self.json_manager.get_entry_by_id(entry_id)
            if not entry_data:
                return False, f"Entrée #{entry_id} introuvable"
            
            # Vérifier si compressée
            if not entry_data.get("compressed", False):
                return False, "Entrée non compressée"
            
            # Vérifier si original disponible
            original_content = entry_data.get("content_original")
            if not original_content:
                return False, "Contenu original perdu - restauration impossible"
            
            # Backup avant restauration
            backup_success = self._create_backup(entry_data, "pre_restore")
            if not backup_success:
                return False, "Échec backup pré-restauration"
            
            # Restauration
            entry_data["content"] = original_content
            entry_data["compressed"] = False
            entry_data["restored_at"] = datetime.now().isoformat()
            del entry_data["content_original"]  # Supprimer backup original
            
            # Sauvegarder
            save_success = self.json_manager._save_entry_to_file(entry_data)
            if not save_success:
                return False, "Échec sauvegarde entrée restaurée"
            
            print(f"[PURGE-MANAGER] ✅ Restauration réussie")
            return True, "Entrée restaurée avec succès"
        
        except Exception as e:
            print(f"[PURGE-MANAGER] ERROR restore_compressed_entry: {e}")
            import traceback
            traceback.print_exc()
            return False, f"Erreur restauration: {e}"
    
    def _create_backup(self, entry_data: Dict[str, Any], backup_type: str) -> bool:
        """
        Crée un backup de l'entrée avant modification
        
        Args:
            entry_data: Données entrée à sauvegarder
            backup_type: Type backup ("pre_compression", "pre_restore", etc.)
        
        Returns:
            True si backup réussi
        """
        try:
            entry_id = entry_data.get("entry_id")
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"entry_{entry_id}_{backup_type}_{timestamp}.json"
            backup_path = self.backup_dir / backup_filename
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(entry_data, f, ensure_ascii=False, indent=2)
            
            print(f"[PURGE-MANAGER] 💾 Backup créé: {backup_filename}")
            return True
        
        except Exception as e:
            print(f"[PURGE-MANAGER] ERROR Backup: {e}")
            return False


# Singleton instance
_purge_manager_instance: Optional[PurgeManager] = None


def initialize_purge_manager(
    json_manager,
    memory_manager=None,
    archiviste_controller=None
) -> Optional[PurgeManager]:
    """
    Initialise le gestionnaire de purge (pattern singleton)
    
    Args:
        json_manager: Instance JournalJSONManager
        memory_manager: Instance MemoryManager (optionnel)
        archiviste_controller: Contrôleur LLM Archiviste (optionnel)
    
    Returns:
        Instance PurgeManager ou None si erreur
    """
    global _purge_manager_instance
    
    try:
        if _purge_manager_instance is None:
            _purge_manager_instance = PurgeManager(
                json_manager=json_manager,
                memory_manager=memory_manager,
                archiviste_controller=archiviste_controller
            )
            print("[PURGE-MANAGER] ✅ Instance singleton créée")
        
        return _purge_manager_instance
    
    except Exception as e:
        print(f"[PURGE-MANAGER] ERROR Initialisation: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_purge_manager() -> Optional[PurgeManager]:
    """Retourne l'instance singleton PurgeManager"""
    return _purge_manager_instance
