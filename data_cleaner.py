#!/usr/bin/env python3
"""
Système de nettoyage complet des données OGMA
Permet de supprimer toutes les données pour créer un profil vierge
"""

import os
import shutil
import json
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import re


class OGMADataCleaner:
    """Système de nettoyage sécurisé des données OGMA"""
    
    def __init__(self, data_root: str = "data"):
        self.data_root = Path(data_root)
        self.backup_dir = None
        self.analysis_results = {}
        
    def analyze_current_data(self) -> Dict:
        """Analyse les données existantes et retourne un rapport détaillé"""
        
        analysis = {
            'memory': {},
            'conversations': {},
            'ego_data': {},
            'settings': {},
            'temp_files': {},
            'total_size': 0,
            'total_files': 0
        }
        
        # Analyse de la mémoire
        memory_dir = self.data_root / "memory"
        if memory_dir.exists():
            analysis['memory'] = self._analyze_memory_data(memory_dir)
        
        # Analyse des conversations
        conv_dir = self.data_root / "conversations"
        if conv_dir.exists():
            analysis['conversations'] = self._analyze_conversations(conv_dir)
        
        # Analyse des données ego
        analysis['ego_data'] = self._analyze_ego_data()
        
        # Analyse des settings
        settings_file = self.data_root / "settings.json"
        if settings_file.exists():
            analysis['settings'] = self._analyze_settings(settings_file)
        
        # Analyse des fichiers temporaires
        analysis['temp_files'] = self._analyze_temp_files()
        
        # Calcul des totaux
        analysis['total_size'] = sum(
            cat.get('total_size', 0) for cat in analysis.values() 
            if isinstance(cat, dict) and 'total_size' in cat
        )
        analysis['total_files'] = sum(
            cat.get('file_count', 0) for cat in analysis.values() 
            if isinstance(cat, dict) and 'file_count' in cat
        )
        
        self.analysis_results = analysis
        return analysis
    
    def _sync_ego_prompt_after_memory_deletion(self, ego_prompt_path: Path):
        """
        Synchronise le ego_prompt.txt après suppression complète des mémoires.
        Supprime tous les IDs vectoriels puisqu'il n'y a plus de base de données.
        """
        try:
            content = ego_prompt_path.read_text(encoding='utf-8')
            
            # Compter les IDs avant nettoyage
            old_ids = re.findall(r'#MEM_EGO_\d+_\d+_\d+', content)
            
            if old_ids:
                # Nettoyer tous les IDs vectoriels (plus de DB = plus d'IDs valides)
                cleaned_content = self._clean_ego_prompt_content(content)
                ego_prompt_path.write_text(cleaned_content, encoding='utf-8')
                print(f"[SYNC] {len(old_ids)} IDs orphelins supprimés de ego_prompt.txt")
            else:
                print("[SYNC] Aucun ID vectoriel trouvé dans ego_prompt.txt")
                
        except Exception as e:
            print(f"[SYNC] Erreur synchronisation ego_prompt: {e}")
    
    def _clean_ego_prompt_content(self, content: str) -> str:
        """
        Nettoie le contenu du ego_prompt.txt en supprimant les IDs vectoriels
        tout en préservant la structure et les commentaires
        """
        lines = content.splitlines()
        cleaned_lines = []
        
        for line in lines:
            # Garder toutes les lignes sauf celles qui contiennent des IDs vectoriels
            if re.match(r'^#MEM_EGO_\d+_\d+_\d+\s*$', line.strip()):
                # Supprimer cette ligne (ID vectoriel)
                continue
            else:
                # Garder cette ligne (structure, commentaires, etc.)
                cleaned_lines.append(line)
        
        # Ajouter une note de nettoyage
        if cleaned_lines and not any('# Profil nettoyé' in line for line in cleaned_lines):
            cleaned_lines.append("")
            cleaned_lines.append(f"# Profil nettoyé le {datetime.now().strftime('%d/%m/%Y à %H:%M')}")
            cleaned_lines.append("# Les références mémorielles seront reconstruites lors de nouveaux apprentissages")
        
        return '\n'.join(cleaned_lines)
    
    def _analyze_memory_data(self, memory_dir: Path) -> Dict:
        """Analyse les données de mémoire"""
        result = {
            'memories_db': None,
            'faiss_index': None,
            'backups': [],
            'reports': [],
            'total_size': 0,
            'file_count': 0,
            'memory_count': 0
        }
        
        # Base de données mémoire
        memories_db = memory_dir / "memories.db"
        if memories_db.exists():
            size = memories_db.stat().st_size
            result['memories_db'] = {
                'path': str(memories_db),
                'size': size,
                'size_mb': round(size / 1024 / 1024, 2)
            }
            result['total_size'] += size
            result['file_count'] += 1
            
            # Compter les souvenirs
            try:
                with sqlite3.connect(memories_db) as conn:
                    cursor = conn.execute("SELECT COUNT(*) FROM memories")
                    result['memory_count'] = cursor.fetchone()[0]
            except Exception as e:
                result['memory_count'] = f"Erreur: {e}"
        
        # Index FAISS
        faiss_index = memory_dir / "faiss.index"
        if faiss_index.exists():
            size = faiss_index.stat().st_size
            result['faiss_index'] = {
                'path': str(faiss_index),
                'size': size,
                'size_mb': round(size / 1024 / 1024, 2)
            }
            result['total_size'] += size
            result['file_count'] += 1
        
        # Fichiers de sauvegarde
        for backup_file in memory_dir.glob("*.bak"):
            size = backup_file.stat().st_size
            result['backups'].append({
                'path': str(backup_file),
                'size': size,
                'size_kb': round(size / 1024, 2)
            })
            result['total_size'] += size
            result['file_count'] += 1
        
        # Rapports de réparation
        for report_file in memory_dir.glob("repair_report_*.json"):
            size = report_file.stat().st_size
            result['reports'].append({
                'path': str(report_file),
                'size': size
            })
            result['total_size'] += size
            result['file_count'] += 1
        
        return result
    
    def _analyze_conversations(self, conv_dir: Path) -> Dict:
        """Analyse les conversations"""
        result = {
            'conversations': [],
            'index_file': None,
            'total_size': 0,
            'file_count': 0,
            'conversation_count': 0
        }
        
        # Fichiers de conversation
        for conv_file in conv_dir.glob("*.json"):
            if conv_file.name == "index.json":
                continue  # Traité séparément
            
            size = conv_file.stat().st_size
            result['conversations'].append({
                'path': str(conv_file),
                'name': conv_file.name,
                'size': size,
                'size_kb': round(size / 1024, 2),
                'modified': datetime.fromtimestamp(conv_file.stat().st_mtime).isoformat()
            })
            result['total_size'] += size
            result['file_count'] += 1
            
            if not conv_file.name.endswith('_backup.json'):
                result['conversation_count'] += 1
        
        # Fichier index
        index_file = conv_dir / "index.json"
        if index_file.exists():
            size = index_file.stat().st_size
            result['index_file'] = {
                'path': str(index_file),
                'size': size
            }
            result['total_size'] += size
            result['file_count'] += 1
        
        return result
    
    def _analyze_ego_data(self) -> Dict:
        """Analyse les données ego"""
        result = {
            'ego_prompt': None,
            'ego_archive': [],
            'persistent_context': None,
            'total_size': 0,
            'file_count': 0
        }
        
        # Ego prompt principal
        ego_prompt = self.data_root / "ego_prompt.txt"
        if ego_prompt.exists():
            size = ego_prompt.stat().st_size
            result['ego_prompt'] = {
                'path': str(ego_prompt),
                'size': size,
                'lines': len(ego_prompt.read_text(encoding='utf-8').splitlines())
            }
            result['total_size'] += size
            result['file_count'] += 1
        
        # Archive ego
        ego_archive_dir = self.data_root / "ego_archive"
        if ego_archive_dir.exists():
            for archive_file in ego_archive_dir.glob("*"):
                size = archive_file.stat().st_size
                result['ego_archive'].append({
                    'path': str(archive_file),
                    'name': archive_file.name,
                    'size': size
                })
                result['total_size'] += size
                result['file_count'] += 1
        
        # Contexte persistant
        persistent_context = self.data_root / "persistent_context.txt"
        if persistent_context.exists():
            size = persistent_context.stat().st_size
            result['persistent_context'] = {
                'path': str(persistent_context),
                'size': size
            }
            result['total_size'] += size
            result['file_count'] += 1
        
        return result
    
    def _analyze_settings(self, settings_file: Path) -> Dict:
        """Analyse le fichier settings"""
        result = {
            'settings_file': None,
            'total_size': 0,
            'file_count': 0,
            'config_sections': []
        }
        
        size = settings_file.stat().st_size
        result['settings_file'] = {
            'path': str(settings_file),
            'size': size,
            'size_kb': round(size / 1024, 2)
        }
        result['total_size'] += size
        result['file_count'] += 1
        
        # Analyser les sections de configuration
        try:
            with open(settings_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                result['config_sections'] = list(config.keys())
        except Exception as e:
            result['config_sections'] = [f"Erreur lecture: {e}"]
        
        return result
    
    def _analyze_temp_files(self) -> Dict:
        """Analyse les fichiers temporaires"""
        result = {
            'temp_files': [],
            'cache_files': [],
            'log_files': [],
            'other_files': [],
            'total_size': 0,
            'file_count': 0
        }
        
        # Patterns de fichiers temporaires
        temp_patterns = ['*.tmp', '*.temp', '*~', '*.bak', '*.old']
        cache_patterns = ['*cache*', '*temp*']
        log_patterns = ['*.log', '*.out']
        
        for pattern in temp_patterns:
            for temp_file in self.data_root.rglob(pattern):
                size = temp_file.stat().st_size
                result['temp_files'].append({
                    'path': str(temp_file),
                    'name': temp_file.name,
                    'size': size
                })
                result['total_size'] += size
                result['file_count'] += 1
        
        # Analyser autres fichiers suspects
        for file in self.data_root.rglob("*"):
            if file.is_file():
                name_lower = file.name.lower()
                if any(pattern in name_lower for pattern in ['cache', 'temp']) and file not in [item['path'] for item in result['temp_files']]:
                    size = file.stat().st_size
                    result['cache_files'].append({
                        'path': str(file),
                        'name': file.name,
                        'size': size
                    })
                    result['total_size'] += size
                    result['file_count'] += 1
        
        return result
    
    def create_backup(self, backup_name: Optional[str] = None) -> Path:
        """Crée une sauvegarde complète avant suppression"""
        if backup_name is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"ogma_backup_{timestamp}"
        
        self.backup_dir = Path(f"backups/{backup_name}")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Copier tout le dossier data
        if self.data_root.exists():
            backup_data_dir = self.backup_dir / "data"
            shutil.copytree(self.data_root, backup_data_dir)
        
        # Créer un rapport de la sauvegarde
        backup_report = {
            'created_at': datetime.now().isoformat(),
            'original_data_analysis': self.analysis_results,
            'backup_location': str(self.backup_dir),
            'files_backed_up': self._count_backup_files(self.backup_dir)
        }
        
        with open(self.backup_dir / "backup_report.json", 'w', encoding='utf-8') as f:
            json.dump(backup_report, f, indent=2, ensure_ascii=False)
        
        return self.backup_dir
    
    def _count_backup_files(self, backup_dir: Path) -> Dict:
        """Compte les fichiers dans la sauvegarde"""
        count: Dict[str, float] = {'total_files': 0, 'total_size': 0}
        
        for file in backup_dir.rglob("*"):
            if file.is_file():
                count['total_files'] += 1
                count['total_size'] += file.stat().st_size
        
        count['total_size_mb'] = round(count['total_size'] / 1024 / 1024, 2)
        return count
    
    def delete_selected_data(self, categories: List[str], confirmation_code: str) -> List[str]:
        """Supprime les catégories de données sélectionnées"""
        
        # Vérification du code de confirmation
        expected_code = "DELETE-ALL-OGMA-DATA"
        if confirmation_code != expected_code:
            raise ValueError(f"Code de confirmation incorrect. Attendu: {expected_code}")
        
        deletion_log = []
        
        try:
            if 'memory' in categories:
                deleted_memory = self._delete_memory_data()
                deletion_log.extend(deleted_memory)
            
            if 'conversations' in categories:
                deleted_conv = self._delete_conversations()
                deletion_log.extend(deleted_conv)
            
            if 'ego_data' in categories:
                deleted_ego = self._delete_ego_data()
                deletion_log.extend(deleted_ego)
            
            if 'temp_files' in categories:
                deleted_temp = self._delete_temp_files()
                deletion_log.extend(deleted_temp)
            
            if 'settings_reset' in categories:
                reset_settings = self._reset_settings()
                deletion_log.extend(reset_settings)
            
        except Exception as e:
            deletion_log.append(f"❌ Erreur lors de la suppression: {e}")
            
        return deletion_log
    
    def _delete_memory_data(self) -> List[str]:
        """Supprime toutes les données de mémoire"""
        log = []
        memory_dir = self.data_root / "memory"
        
        if not memory_dir.exists():
            log.append("ℹ️  Aucun dossier mémoire trouvé")
            return log
        
        try:
            deleted_count = 0
            failed_count = 0

            # Supprimer tous les fichiers dans memory/
            for file in memory_dir.rglob("*"):
                if file.is_file():
                    try:
                        file.unlink()
                        log.append(f"🗑️ Supprimé: {file.name}")
                        deleted_count += 1
                    except Exception as e:
                        log.append(f"❌ Échec suppression {file.name}: {e}")
                        failed_count += 1

            # Supprimer les dossiers vides
            for dir in memory_dir.rglob("*"):
                if dir.is_dir() and not any(dir.iterdir()):
                    try:
                        dir.rmdir()
                        log.append(f"📁 Dossier vide supprimé: {dir.name}")
                    except Exception as e:
                        log.append(f"❌ Échec suppression dossier {dir.name}: {e}")

            # IMPORTANT: Synchroniser ego_prompt.txt après suppression des mémoires
            ego_prompt = self.data_root / "ego_prompt.txt"
            if ego_prompt.exists():
                self._sync_ego_prompt_after_memory_deletion(ego_prompt)
                log.append("🔄 ego_prompt.txt synchronisé (IDs orphelins supprimés)")

            if failed_count == 0:
                log.append(f"✅ Mémoire complètement nettoyée ({deleted_count} fichiers supprimés)")
            else:
                log.append(f"⚠️ Nettoyage partiel: {deleted_count} fichiers supprimés, {failed_count} échecs")

        except Exception as e:
            log.append(f"❌ Erreur suppression mémoire: {e}")
        
        return log
    
    def _delete_conversations(self) -> List[str]:
        """Supprime toutes les conversations"""
        log = []
        conv_dir = self.data_root / "conversations"
        
        if not conv_dir.exists():
            log.append("ℹ️  Aucun dossier conversations trouvé")
            return log
        
        try:
            file_count = 0
            for file in conv_dir.glob("*"):
                if file.is_file():
                    file.unlink()
                    file_count += 1
            
            log.append(f"🗑️ {file_count} fichiers de conversation supprimés")
            log.append("✅ Conversations complètement nettoyées")
            
        except Exception as e:
            log.append(f"❌ Erreur suppression conversations: {e}")
        
        return log
    
    def _delete_ego_data(self) -> List[str]:
        """Supprime les données ego (avec précaution)"""
        log = []
        
        try:
            # Ego prompt principal - LAISSER le système gérer automatiquement
            ego_prompt = self.data_root / "ego_prompt.txt"
            if ego_prompt.exists():
                log.append("✅ ego_prompt.txt préservé (synchronisation automatique après suppression mémoires)")
            
            # Archive ego
            ego_archive_dir = self.data_root / "ego_archive"
            if ego_archive_dir.exists():
                for file in ego_archive_dir.rglob("*"):
                    if file.is_file():
                        file.unlink()
                        log.append(f"🗑️ Supprimé: ego_archive/{file.name}")
            
            # Contexte persistant
            persistent_context = self.data_root / "persistent_context.txt"
            if persistent_context.exists():
                persistent_context.unlink()
                log.append("🗑️ persistent_context.txt supprimé")
            
            log.append("✅ Données ego nettoyées")
            
        except Exception as e:
            log.append(f"❌ Erreur suppression ego: {e}")
        
        return log
    
    def _delete_temp_files(self) -> List[str]:
        """Supprime les fichiers temporaires"""
        log = []
        
        try:
            temp_patterns = ['*.tmp', '*.temp', '*~', '*.bak', '*.old']
            deleted_count = 0
            
            for pattern in temp_patterns:
                for temp_file in self.data_root.rglob(pattern):
                    temp_file.unlink()
                    deleted_count += 1
                    log.append(f"🗑️ Supprimé: {temp_file.name}")
            
            log.append(f"✅ {deleted_count} fichiers temporaires supprimés")
            
        except Exception as e:
            log.append(f"❌ Erreur suppression fichiers temporaires: {e}")
        
        return log
    
    def _reset_settings(self) -> List[str]:
        """Remet les settings à leur état par défaut (optionnel)"""
        log = []
        
        try:
            settings_file = self.data_root / "settings.json"
            if settings_file.exists():
                # Créer une copie de sauvegarde spécifique
                backup_settings = self.data_root / "settings_backup_before_reset.json"
                shutil.copy2(settings_file, backup_settings)
                log.append(f"💾 Sauvegarde settings: {backup_settings.name}")
                
                # Note: Pour l'instant on ne fait que sauvegarder
                # La réinitialisation complète pourrait être ajoutée plus tard
                log.append("ℹ️  Settings sauvegardés (réinitialisation non implémentée)")
            
        except Exception as e:
            log.append(f"❌ Erreur avec settings: {e}")
        
        return log
    
    def verify_clean_state(self) -> Dict:
        """Vérifie que le nettoyage s'est bien passé"""
        verification = {
            'memory_clean': False,
            'conversations_clean': False,
            'ego_clean': False,
            'temp_files_clean': False,
            'issues': []
        }
        
        # Vérifier mémoire
        memory_dir = self.data_root / "memory"
        if not memory_dir.exists() or not any(memory_dir.rglob("*")):
            verification['memory_clean'] = True
        else:
            remaining = list(memory_dir.rglob("*"))
            verification['issues'].append(f"Mémoire: {len(remaining)} fichiers restants")
        
        # Vérifier conversations
        conv_dir = self.data_root / "conversations"
        if not conv_dir.exists() or not any(conv_dir.glob("*")):
            verification['conversations_clean'] = True
        else:
            remaining = list(conv_dir.glob("*"))
            verification['issues'].append(f"Conversations: {len(remaining)} fichiers restants")
        
        # Vérifier ego
        ego_files = [
            self.data_root / "ego_prompt.txt",
            self.data_root / "persistent_context.txt"
        ]
        ego_remaining = [f for f in ego_files if f.exists()]
        if not ego_remaining:
            verification['ego_clean'] = True
        else:
            verification['issues'].append(f"Ego: {len(ego_remaining)} fichiers restants")
        
        # Vérifier fichiers temporaires
        temp_patterns = ['*.tmp', '*.temp', '*~', '*.bak', '*.old']
        temp_remaining = []
        for pattern in temp_patterns:
            temp_remaining.extend(list(self.data_root.rglob(pattern)))
        
        if not temp_remaining:
            verification['temp_files_clean'] = True
        else:
            verification['issues'].append(f"Temporaires: {len(temp_remaining)} fichiers restants")
        
        verification['all_clean'] = all([
            verification['memory_clean'],
            verification['conversations_clean'],
            verification['ego_clean'],
            verification['temp_files_clean']
        ])
        
        return verification


def format_size(size_bytes: int) -> str:
    """Formate une taille en bytes en format lisible"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024**2:
        return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024**3:
        return f"{size_bytes/1024**2:.1f} MB"
    else:
        return f"{size_bytes/1024**3:.1f} GB"


def print_analysis_report(analysis: Dict):
    """Affiche un rapport d'analyse formaté"""
    print("\n" + "="*60)
    print("📊 ANALYSE DES DONNÉES OGMA")
    print("="*60)
    
    # Résumé global
    print(f"\n📈 RÉSUMÉ GLOBAL:")
    print(f"   Total fichiers: {analysis['total_files']}")
    print(f"   Taille totale: {format_size(analysis['total_size'])}")
    
    # Détail par catégorie
    if analysis['memory'].get('file_count', 0) > 0:
        memory = analysis['memory']
        print(f"\n🧠 MÉMOIRE ({memory['file_count']} fichiers, {format_size(memory['total_size'])}):")
        if memory.get('memory_count'):
            print(f"   Souvenirs stockés: {memory['memory_count']}")
        if memory.get('memories_db'):
            print(f"   Base données: {memory['memories_db']['size_mb']} MB")
        if memory.get('faiss_index'):
            print(f"   Index FAISS: {memory['faiss_index']['size_mb']} MB")
        if memory.get('backups'):
            print(f"   Sauvegardes: {len(memory['backups'])} fichiers")
    
    if analysis['conversations'].get('file_count', 0) > 0:
        conv = analysis['conversations']
        print(f"\n💬 CONVERSATIONS ({conv['file_count']} fichiers, {format_size(conv['total_size'])}):")
        print(f"   Conversations: {conv['conversation_count']}")
        print(f"   Fichiers récents: {len([c for c in conv['conversations'] if '2025-09-20' in c['name']])}")
    
    if analysis['ego_data'].get('file_count', 0) > 0:
        ego = analysis['ego_data']
        print(f"\n🎭 DONNÉES EGO ({ego['file_count']} fichiers, {format_size(ego['total_size'])}):")
        if ego.get('ego_prompt'):
            print(f"   Ego prompt: {ego['ego_prompt']['lines']} lignes")
        if ego.get('ego_archive'):
            print(f"   Archive ego: {len(ego['ego_archive'])} fichiers")
    
    if analysis['temp_files'].get('file_count', 0) > 0:
        temp = analysis['temp_files']
        print(f"\n🗑️ FICHIERS TEMPORAIRES ({temp['file_count']} fichiers, {format_size(temp['total_size'])}):")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    # Test du système de nettoyage
    cleaner = OGMADataCleaner()
    
    print("Analyse des données OGMA en cours...")
    analysis = cleaner.analyze_current_data()
    
    print_analysis_report(analysis)
    
    # Exemple d'utilisation (commenté pour sécurité)
    """
    # Créer une sauvegarde
    backup_dir = cleaner.create_backup()
    print(f"\\nSauvegarde créée dans: {backup_dir}")
    
    # Supprimer des données (ATTENTION: DANGEREUX!)
    # deletion_log = cleaner.delete_selected_data(
    #     categories=['memory', 'conversations'], 
    #     confirmation_code="DELETE-ALL-OGMA-DATA"
    # )
    # 
    # for log_entry in deletion_log:
    #     print(log_entry)
    #
    # # Vérifier le nettoyage
    # verification = cleaner.verify_clean_state()
    # print(f"\\nÉtat après nettoyage: {verification}")
    """