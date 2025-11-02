"""
📚 SUMMARY LOADER - Accès optimisé aux résumés en cache
========================================================

Gère la lecture et le filtrage des résumés depuis summaries_cache/.

FONCTIONNALITÉS:
- Liste tous résumés disponibles (simples + fusion)
- Filtrage par plage temporelle (via timestamps fichiers)
- Chargement contenu résumés
- Scoring pertinence pour priorisation

SOURCES:
1. summaries_cache/*.txt (résumés simples 10 messages)
2. summaries_cache/fusion_*.txt (résumés fusionnés)
3. conversations/*.json (optionnel, métadonnées)
"""

import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import hashlib


class SummaryLoader:
    """Chargeur de résumés depuis cache persistant."""
    
    def __init__(
        self, 
        cache_dir: str = "data/summaries_cache",
        conversations_dir: str = "data/conversations",
        debug: bool = False
    ):
        self.cache_dir = Path(cache_dir)
        self.conversations_dir = Path(conversations_dir)
        self.debug = debug
        
        # Cache en mémoire pour éviter multiples lectures
        self._cache: Dict[str, Dict] = {}
        self._scan_cache()
    
    def _scan_cache(self):
        """Scan initial du répertoire cache."""
        if not self.cache_dir.exists():
            if self.debug:
                print(f"[SUMMARY-LOADER] ⚠️ Cache dir introuvable: {self.cache_dir}")
            return
        
        count_simple = 0
        count_fusion = 0
        
        for file_path in self.cache_dir.glob("*.txt"):
            try:
                stat = file_path.stat()
                is_fusion = file_path.name.startswith("fusion_")
                
                self._cache[file_path.name] = {
                    'path': str(file_path),
                    'name': file_path.name,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime),
                    'is_fusion': is_fusion,
                    'content': None  # Lazy loading
                }
                
                if is_fusion:
                    count_fusion += 1
                else:
                    count_simple += 1
                    
            except OSError as e:
                if self.debug:
                    print(f"[SUMMARY-LOADER] ⚠️ Erreur scan {file_path.name}: {e}")
        
        if self.debug:
            print(f"[SUMMARY-LOADER] 📊 Cache scanné: {count_simple} résumés simples, {count_fusion} fusions")
    
    def list_cached_summaries(self) -> List[Dict]:
        """Liste tous les résumés en cache (triés par date modification)."""
        summaries = list(self._cache.values())
        summaries.sort(key=lambda s: s['modified'], reverse=True)
        return summaries
    
    def filter_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime,
        include_fusion: bool = True
    ) -> List[Dict]:
        """
        Filtre résumés par plage temporelle.
        
        Args:
            start_date: Date début (inclusive)
            end_date: Date fin (inclusive)
            include_fusion: Inclure résumés fusionnés
            
        Returns:
            Liste résumés dans la plage
        """
        filtered = []
        
        for summary in self._cache.values():
            # Filtrer fusion si demandé
            if not include_fusion and summary['is_fusion']:
                continue
            
            # Vérifier plage temporelle (via date modification fichier)
            mod_date = summary['modified']
            if start_date <= mod_date <= end_date:
                filtered.append(summary)
        
        # Trier par date (plus récent d'abord)
        filtered.sort(key=lambda s: s['modified'], reverse=True)
        
        if self.debug:
            print(f"[SUMMARY-LOADER] 🔍 Filtrage {start_date.date()} → {end_date.date()}: {len(filtered)} résumés")
        
        return filtered
    
    def load_summary_content(self, summary_name: str) -> Optional[str]:
        """
        Charge le contenu d'un résumé (avec cache mémoire).
        
        Args:
            summary_name: Nom fichier résumé
            
        Returns:
            Contenu texte ou None
        """
        if summary_name not in self._cache:
            return None
        
        summary = self._cache[summary_name]
        
        # Utiliser cache mémoire si déjà chargé
        if summary['content'] is not None:
            return summary['content']
        
        # Sinon charger depuis disque
        try:
            with open(summary['path'], 'r', encoding='utf-8') as f:
                content = f.read().strip()
                summary['content'] = content
                return content
        except Exception as e:
            if self.debug:
                print(f"[SUMMARY-LOADER] ❌ Erreur lecture {summary_name}: {e}")
            return None
    
    def load_multiple(self, summary_list: List[Dict]) -> List[Tuple[Dict, str]]:
        """
        Charge plusieurs résumés en batch.
        
        Args:
            summary_list: Liste de métadonnées résumés
            
        Returns:
            Liste de tuples (metadata, content)
        """
        results = []
        
        for summary in summary_list:
            content = self.load_summary_content(summary['name'])
            if content:
                results.append((summary, content))
        
        if self.debug:
            print(f"[SUMMARY-LOADER] 📖 Chargement batch: {len(results)}/{len(summary_list)} réussis")
        
        return results
    
    def get_recent_summaries(
        self, 
        max_count: int = 10,
        include_fusion: bool = True
    ) -> List[Dict]:
        """
        Récupère les N résumés les plus récents.
        
        Args:
            max_count: Nombre maximum de résumés
            include_fusion: Inclure résumés fusionnés
            
        Returns:
            Liste résumés triés par récence
        """
        all_summaries = list(self._cache.values())
        
        # Filtrer fusion si demandé
        if not include_fusion:
            all_summaries = [s for s in all_summaries if not s['is_fusion']]
        
        # Trier par date modification
        all_summaries.sort(key=lambda s: s['modified'], reverse=True)
        
        return all_summaries[:max_count]
    
    def get_fusion_summaries(self) -> List[Dict]:
        """Récupère uniquement les résumés fusionnés (méta-analyses)."""
        return [s for s in self._cache.values() if s['is_fusion']]
    
    def search_by_keywords(
        self, 
        keywords: List[str],
        max_results: int = 5
    ) -> List[Tuple[Dict, str, float]]:
        """
        Recherche résumés contenant certains mots-clés.
        
        Args:
            keywords: Liste mots-clés à rechercher
            max_results: Nombre max résultats
            
        Returns:
            Liste (metadata, content, score) triée par pertinence
        """
        results = []
        keywords_lower = [k.lower() for k in keywords]
        
        for summary in self._cache.values():
            content = self.load_summary_content(summary['name'])
            if not content:
                continue
            
            content_lower = content.lower()
            
            # Scorer par nombre de keywords trouvés
            score = sum(1 for kw in keywords_lower if kw in content_lower)
            
            if score > 0:
                results.append((summary, content, score))
        
        # Trier par score décroissant
        results.sort(key=lambda x: x[2], reverse=True)
        
        if self.debug:
            print(f"[SUMMARY-LOADER] 🔎 Recherche keywords: {len(results)} résultats")
        
        return results[:max_results]
    
    def get_statistics(self) -> Dict:
        """Retourne statistiques sur le cache."""
        total = len(self._cache)
        fusion_count = sum(1 for s in self._cache.values() if s['is_fusion'])
        simple_count = total - fusion_count
        
        total_size = sum(s['size'] for s in self._cache.values())
        
        if self._cache:
            oldest = min(s['modified'] for s in self._cache.values())
            newest = max(s['modified'] for s in self._cache.values())
        else:
            oldest = newest = None
        
        return {
            'total_summaries': total,
            'simple_summaries': simple_count,
            'fusion_summaries': fusion_count,
            'total_size_bytes': total_size,
            'oldest_date': oldest,
            'newest_date': newest
        }
    
    def refresh_cache(self):
        """Force re-scan du répertoire cache."""
        self._cache.clear()
        self._scan_cache()
