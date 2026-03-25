"""
📚 SUMMARY LOADER - Accès optimisé aux résumés de conversations
================================================================

Gère la lecture et le filtrage des résumés depuis les fichiers JSON
de conversations (nouveau système v2.2+).

FONCTIONNALITÉS:
- Liste tous résumés disponibles depuis conversations JSON
- Filtrage par plage temporelle (via date conversation)
- Chargement contenu résumés
- Scoring pertinence pour priorisation

SOURCES:
- conversations/*.json (résumés intégrés dans structure {messages, summaries})

MIGRATION v2.2:
- Ancien système: summaries_cache/*.txt (SUPPRIMÉ)
- Nouveau système: résumés persistés dans JSON conversations
- API: get_all_summaries_from_conversations() de conversation_summarizer.py
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

# Ajouter le chemin racine pour importer conversation_summarizer
_root_path = Path(__file__).parent.parent.parent
if str(_root_path) not in sys.path:
    sys.path.insert(0, str(_root_path))


class SummaryLoader:
    """
    Chargeur de résumés depuis conversations JSON.
    
    Interface compatible avec l'ancien système pour que RecallAgent
    continue de fonctionner sans modification.
    """
    
    def __init__(
        self, 
        conversations_dir: str = "data/conversations",
        debug: bool = False,
        **kwargs  # Ignore les anciens paramètres (cache_dir, etc.)
    ):
        self.conversations_dir = Path(conversations_dir)
        self.debug = debug
        
        # Cache en mémoire des résumés chargés
        self._cache: Dict[str, Dict] = {}
        self._last_scan: Optional[datetime] = None
        
        # Charger les résumés au démarrage
        self._scan_conversations()
    
    def _scan_conversations(self):
        """Scan les conversations JSON pour extraire les résumés."""
        try:
            from conversation_summarizer import get_all_summaries_from_conversations
            
            all_summaries = get_all_summaries_from_conversations(
                str(self.conversations_dir), 
                max_conversations=100
            )
            
            self._cache.clear()
            count = 0
            
            for conv_data in all_summaries:
                conv_id = conv_data.get('conversation_id', '')
                conv_file = conv_data.get('conversation_file', '')
                modified = conv_data.get('modified', datetime.now())
                
                for idx, summary_range in enumerate(conv_data.get('summaries', [])):
                    # Créer une clé unique pour ce résumé
                    summary_key = f"{conv_id}_range_{idx}"
                    
                    self._cache[summary_key] = {
                        'name': summary_key,
                        'conversation_id': conv_id,
                        'conversation_file': conv_file,
                        'modified': modified,
                        'start': summary_range.get('start', 0),
                        'end': summary_range.get('end', 0),
                        'content': summary_range.get('text', ''),
                        'cache_key': summary_range.get('cache_key', ''),
                        'is_fusion': False,  # Compatibilité ancien système
                        'size': len(summary_range.get('text', ''))
                    }
                    count += 1
            
            self._last_scan = datetime.now()
            
            if self.debug:
                print(f"[SUMMARY-LOADER] 📊 Scan conversations: {count} résumés trouvés dans {len(all_summaries)} conversations")
                
        except ImportError as e:
            if self.debug:
                print(f"[SUMMARY-LOADER] ⚠️ Import conversation_summarizer échoué: {e}")
        except Exception as e:
            if self.debug:
                print(f"[SUMMARY-LOADER] ❌ Erreur scan conversations: {e}")
    
    def list_cached_summaries(self) -> List[Dict]:
        """Liste tous les résumés en cache (triés par date modification)."""
        summaries = list(self._cache.values())
        summaries.sort(key=lambda s: s['modified'], reverse=True)
        return summaries
    
    def filter_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime,
        include_fusion: bool = True  # Ignoré, conservé pour compatibilité
    ) -> List[Dict]:
        """
        Filtre résumés par plage temporelle.
        
        Args:
            start_date: Date début (inclusive)
            end_date: Date fin (inclusive)
            include_fusion: Ignoré (compatibilité ancien système)
            
        Returns:
            Liste résumés dans la plage
        """
        filtered = []
        
        for summary in self._cache.values():
            # Vérifier plage temporelle (via date conversation)
            mod_date = summary['modified']
            
            # Gérer les cas où mod_date n'a pas d'info timezone
            if hasattr(mod_date, 'tzinfo') and mod_date.tzinfo is not None:
                # Convertir en naive datetime pour comparaison
                mod_date = mod_date.replace(tzinfo=None)
            
            if start_date <= mod_date <= end_date:
                filtered.append(summary)
        
        # Trier par date (plus récent d'abord)
        filtered.sort(key=lambda s: s['modified'], reverse=True)
        
        if self.debug:
            print(f"[SUMMARY-LOADER] 🔍 Filtrage {start_date.date()} → {end_date.date()}: {len(filtered)} résumés")
        
        return filtered
    
    def load_summary_content(self, summary_name: str) -> Optional[str]:
        """
        Charge le contenu d'un résumé (déjà en cache).
        
        Args:
            summary_name: Clé du résumé
            
        Returns:
            Contenu texte ou None
        """
        if summary_name not in self._cache:
            return None
        
        return self._cache[summary_name].get('content')
    
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
            content = summary.get('content') or self.load_summary_content(summary.get('name', ''))
            if content:
                results.append((summary, content))
        
        if self.debug:
            print(f"[SUMMARY-LOADER] 📖 Chargement batch: {len(results)}/{len(summary_list)} réussis")
        
        return results
    
    def get_recent_summaries(
        self, 
        max_count: int = 10,
        include_fusion: bool = True  # Ignoré, conservé pour compatibilité
    ) -> List[Dict]:
        """
        Récupère les N résumés les plus récents.
        
        Args:
            max_count: Nombre maximum de résumés
            include_fusion: Ignoré (compatibilité ancien système)
            
        Returns:
            Liste résumés triés par récence
        """
        all_summaries = list(self._cache.values())
        
        # Trier par date modification
        all_summaries.sort(key=lambda s: s['modified'], reverse=True)
        
        return all_summaries[:max_count]
    
    def get_fusion_summaries(self) -> List[Dict]:
        """
        Récupère les résumés fusionnés.
        
        Note: Dans le nouveau système, il n'y a plus de distinction
        fusion/simple. Retourne une liste vide pour compatibilité.
        """
        return []
    
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
            content = summary.get('content', '')
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
        
        # Compter les conversations uniques
        unique_convs = set(s.get('conversation_id', '') for s in self._cache.values())
        
        total_size = sum(s.get('size', 0) for s in self._cache.values())
        
        if self._cache:
            oldest = min(s['modified'] for s in self._cache.values())
            newest = max(s['modified'] for s in self._cache.values())
        else:
            oldest = newest = None
        
        return {
            'total_summaries': total,
            'conversations_with_summaries': len(unique_convs),
            'simple_summaries': total,  # Compatibilité
            'fusion_summaries': 0,       # Compatibilité
            'total_size_bytes': total_size,
            'oldest_date': oldest,
            'newest_date': newest,
            'last_scan': self._last_scan
        }
    
    def refresh_cache(self):
        """Force re-scan des conversations."""
        self._cache.clear()
        self._scan_conversations()
