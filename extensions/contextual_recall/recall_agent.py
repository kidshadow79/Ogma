"""
🧠 RECALL AGENT - Orchestrateur principal Contextual Recall
============================================================

Coordonne tous les composants de l'extension pour détecter et traiter
les demandes de rappel mémoire conversationnelle.

WORKFLOW:
1. Détection patterns temporels dans requête utilisateur
2. Récupération résumés pertinents via SummaryLoader
3. Construction contexte formaté via ContextBuilder
4. Retour contexte pour injection dans messages système

API PUBLIQUE:
- process_message(user_message) → contexte ou None
- is_temporal_query(user_message) → bool
- get_statistics() → stats cache/utilisation
"""

from typing import Optional, Dict, List
from .temporal_parser import TemporalParser, TemporalMatch
from .summary_loader import SummaryLoader
from .context_builder import ContextBuilder


class RecallAgent:
    """Agent orchestrateur pour rappel contextuel mémoire."""
    
    def __init__(
        self,
        temporal_parser: TemporalParser,
        summary_loader: SummaryLoader,
        context_builder: ContextBuilder,
        debug: bool = False
    ):
        self.temporal_parser = temporal_parser
        self.summary_loader = summary_loader
        self.context_builder = context_builder
        self.debug = debug
        
        # Statistiques utilisation
        self._stats = {
            'queries_processed': 0,
            'temporal_detected': 0,
            'contexts_generated': 0,
            'summaries_loaded': 0
        }
    
    def process_message(self, user_message: str, source: str = "user") -> Optional[str]:
        """
        Traite un message (utilisateur OU IA) et génère contexte si pertinent.
        
        Args:
            user_message: Message brut (utilisateur ou IA)
            source: Source du message ("user" ou "ia")
            
        Returns:
            Contexte formaté pour injection ou None
        """
        self._stats['queries_processed'] += 1
        
        if self.debug:
            prefix = "👤 USER" if source == "user" else "🤖 IA"
            print(f"[RECALL-AGENT] 🔍 {prefix} Traitement: '{user_message[:100]}...'")
        
        # 1. Détection patterns temporels
        temporal_matches = self.temporal_parser.parse(user_message)
        
        if not temporal_matches:
            if self.debug:
                print("[RECALL-AGENT] ℹ️ Aucun pattern temporel détecté")
            return None
        
        self._stats['temporal_detected'] += 1
        
        # 2. Prendre le meilleur match (confidence la plus haute)
        best_match = temporal_matches[0]
        
        if self.debug:
            print(f"[RECALL-AGENT] ✅ Pattern détecté: {best_match.pattern_type} ({best_match.confidence:.2f})")
            print(f"[RECALL-AGENT] 📅 Plage: {best_match.date_start.date()} → {best_match.date_end.date()}")
        
        # 3. Récupérer résumés dans la plage
        summaries = self.summary_loader.filter_by_date_range(
            best_match.date_start,
            best_match.date_end,
            include_fusion=True
        )
        
        if not summaries:
            if self.debug:
                print("[RECALL-AGENT] ⚠️ Aucun résumé trouvé dans la plage")
            return None
        
        # 4. Charger contenu résumés
        loaded_summaries = self.summary_loader.load_multiple(summaries)
        
        if not loaded_summaries:
            if self.debug:
                print("[RECALL-AGENT] ❌ Échec chargement résumés")
            return None
        
        self._stats['summaries_loaded'] += len(loaded_summaries)
        
        # 5. Construire contexte formaté
        context = self.context_builder.build_context(
            loaded_summaries,
            best_match.date_start,
            best_match.date_end,
            user_query=user_message
        )
        
        if context:
            self._stats['contexts_generated'] += 1
            
            if self.debug:
                tokens = self.context_builder.estimate_tokens(context)
                print(f"[RECALL-AGENT] ✅ Contexte généré: {len(loaded_summaries)} résumés, ~{tokens} tokens")
        
        return context
    
    def is_temporal_query(self, user_message: str) -> bool:
        """
        Vérifie rapidement si message contient référence temporelle.
        
        Args:
            user_message: Message utilisateur
            
        Returns:
            True si pattern temporel détecté
        """
        return self.temporal_parser.has_temporal_reference(user_message)
    
    def get_best_temporal_match(self, user_message: str) -> Optional[TemporalMatch]:
        """
        Retourne le meilleur match temporel sans traitement complet.
        
        Args:
            user_message: Message utilisateur
            
        Returns:
            TemporalMatch ou None
        """
        return self.temporal_parser.get_best_match(user_message)
    
    def preview_context(self, user_message: str) -> Optional[Dict]:
        """
        Prévisualise le contexte sans l'injecter (debug/tests).
        
        Args:
            user_message: Message utilisateur
            
        Returns:
            Dict avec métadonnées contexte ou None
        """
        temporal_matches = self.temporal_parser.parse(user_message)
        
        if not temporal_matches:
            return None
        
        best_match = temporal_matches[0]
        
        summaries = self.summary_loader.filter_by_date_range(
            best_match.date_start,
            best_match.date_end,
            include_fusion=True
        )
        
        loaded_summaries = self.summary_loader.load_multiple(summaries)
        
        context = self.context_builder.build_context(
            loaded_summaries,
            best_match.date_start,
            best_match.date_end,
            user_query=user_message
        )
        
        return {
            'temporal_match': {
                'pattern_type': best_match.pattern_type,
                'date_start': best_match.date_start.isoformat(),
                'date_end': best_match.date_end.isoformat(),
                'confidence': best_match.confidence,
                'is_period': best_match.is_period
            },
            'summaries_count': len(loaded_summaries),
            'context_length': len(context) if context else 0,
            'context_tokens': self.context_builder.estimate_tokens(context) if context else 0,
            'context_preview': context[:500] if context else None
        }
    
    def get_statistics(self) -> Dict:
        """
        Retourne statistiques d'utilisation de l'extension.
        
        Returns:
            Dict avec métriques
        """
        cache_stats = self.summary_loader.get_statistics()
        
        return {
            **self._stats,
            'cache_statistics': cache_stats,
            'hit_rate': (
                self._stats['contexts_generated'] / self._stats['queries_processed'] 
                if self._stats['queries_processed'] > 0 else 0.0
            )
        }
    
    def reset_statistics(self):
        """Réinitialise statistiques utilisation."""
        self._stats = {
            'queries_processed': 0,
            'temporal_detected': 0,
            'contexts_generated': 0,
            'summaries_loaded': 0
        }
    
    def refresh_cache(self):
        """Force refresh du cache de résumés."""
        if self.debug:
            print("[RECALL-AGENT] 🔄 Refresh cache résumés...")
        self.summary_loader.refresh_cache()
    
    def search_by_keywords(self, keywords: List[str], max_results: int = 5) -> Optional[str]:
        """
        Recherche résumés par mots-clés (fallback si pas de pattern temporel).
        
        Args:
            keywords: Liste mots-clés
            max_results: Nombre max résultats
            
        Returns:
            Contexte formaté ou None
        """
        results = self.summary_loader.search_by_keywords(keywords, max_results)
        
        if not results:
            return None
        
        # Convertir en format (metadata, content)
        summaries = [(meta, content) for meta, content, score in results]
        
        # Déterminer plage temporelle depuis résultats
        dates = [meta['modified'] for meta, _, _ in results]
        date_start = min(dates)
        date_end = max(dates)
        
        context = self.context_builder.build_context(
            summaries,
            date_start,
            date_end,
            user_query=f"Recherche: {', '.join(keywords)}"
        )
        
        return context
