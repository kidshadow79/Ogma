"""
🎨 CONTEXT BUILDER - Construction contexte formaté pour injection
==================================================================

Formate les résumés récupérés en contexte lisible pour injection
dans les messages système de Luna.

RESPONSABILITÉS:
- Formatage texte condensé et structuré
- Gestion limites tokens (budget configurable)
- Priorisation résumés par pertinence
- Métadonnées temporelles claires

SORTIE FORMAT:
```
📚 RAPPEL MÉMOIRE CONVERSATIONNELLE

🗓️ Période: [date_start] → [date_end]

🔍 Résumés de conversations pertinentes:

[Résumé 1 - Date]
[Contenu résumé...]

[Résumé 2 - Date]
[Contenu résumé...]

💡 Utilise ces informations pour contextualiser ta réponse.
```
"""

from datetime import datetime
from typing import List, Dict, Tuple, Optional


class ContextBuilder:
    """Constructeur de contexte formaté pour injection."""
    
    def __init__(
        self,
        max_tokens: int = 1000,  # Budget tokens pour contexte
        max_summaries: int = 5,   # Nombre max résumés inclus
        debug: bool = False
    ):
        self.max_tokens = max_tokens
        self.max_summaries = max_summaries
        self.debug = debug
        
        # Approximation: 1 token ≈ 4 caractères
        self.chars_per_token = 4
    
    def build_context(
        self,
        summaries: List[Tuple[Dict, str]],
        date_start: datetime,
        date_end: datetime,
        user_query: str = ""
    ) -> Optional[str]:
        """
        Construit contexte formaté depuis résumés.
        
        Args:
            summaries: Liste (metadata, content)
            date_start: Date début plage
            date_end: Date fin plage
            user_query: Requête utilisateur (pour contexte)
            
        Returns:
            Contexte formaté ou None si vide
        """
        if not summaries:
            if self.debug:
                print("[CONTEXT-BUILDER] ⚠️ Aucun résumé à formater")
            return None
        
        # Limiter nombre de résumés
        summaries = summaries[:self.max_summaries]
        
        # Header avec période
        context_parts = [
            "📚 RAPPEL MÉMOIRE CONVERSATIONNELLE",
            "",
            f"🗓️ Période: {self._format_date_range(date_start, date_end)}",
            ""
        ]
        
        # Optionnel: requête utilisateur
        if user_query:
            context_parts.append(f"💭 Question: \"{user_query}\"")
            context_parts.append("")
        
        context_parts.append("🔍 Résumés de conversations pertinentes:")
        context_parts.append("")
        
        # Budget tokens restant pour résumés
        header_text = "\n".join(context_parts)
        used_chars = len(header_text)
        remaining_chars = (self.max_tokens * self.chars_per_token) - used_chars
        
        # Ajouter résumés avec gestion budget
        summary_count = 0
        for metadata, content in summaries:
            # Formater résumé avec date
            summary_date = metadata['modified'].strftime("%d/%m/%Y %H:%M")
            is_fusion = " [FUSION]" if metadata['is_fusion'] else ""
            
            summary_text = f"[Résumé {summary_count + 1}{is_fusion} - {summary_date}]\n{content}\n"
            
            # Vérifier budget
            if len(summary_text) > remaining_chars:
                if self.debug:
                    print(f"[CONTEXT-BUILDER] ⚠️ Budget atteint après {summary_count} résumés")
                break
            
            context_parts.append(summary_text)
            remaining_chars -= len(summary_text)
            summary_count += 1
        
        # Footer
        context_parts.append("")
        context_parts.append("💡 Utilise ces informations pour contextualiser ta réponse.")
        
        final_context = "\n".join(context_parts)
        
        if self.debug:
            tokens_estimate = len(final_context) // self.chars_per_token
            print(f"[CONTEXT-BUILDER] ✅ Contexte généré: {summary_count} résumés, ~{tokens_estimate} tokens")
        
        return final_context
    
    def build_compact_context(
        self,
        summaries: List[Tuple[Dict, str]],
        date_start: datetime,
        date_end: datetime
    ) -> Optional[str]:
        """
        Version compacte du contexte (style télégraphique).
        
        Args:
            summaries: Liste (metadata, content)
            date_start: Date début plage
            date_end: Date fin plage
            
        Returns:
            Contexte ultra-compact ou None
        """
        if not summaries:
            return None
        
        # Header minimal
        period = self._format_date_range(date_start, date_end)
        context_parts = [f"📚 MÉMOIRE ({period}):"]
        
        # Résumés condensés
        for i, (metadata, content) in enumerate(summaries[:self.max_summaries], 1):
            # Tronquer si trop long
            max_length = 200
            condensed = content[:max_length] + "..." if len(content) > max_length else content
            
            date_str = metadata['modified'].strftime("%d/%m")
            context_parts.append(f"{i}. [{date_str}] {condensed}")
        
        return "\n".join(context_parts)
    
    def _format_date_range(self, start: datetime, end: datetime) -> str:
        """Formate plage de dates de manière lisible."""
        start_str = start.strftime("%d/%m/%Y")
        end_str = end.strftime("%d/%m/%Y")
        
        # Si même jour
        if start.date() == end.date():
            return start_str
        
        # Si même mois
        if start.month == end.month and start.year == end.year:
            return f"{start.day} → {end.day}/{end.month}/{end.year}"
        
        # Sinon plage complète
        return f"{start_str} → {end_str}"
    
    def estimate_tokens(self, text: str) -> int:
        """Estime nombre de tokens d'un texte."""
        return len(text) // self.chars_per_token
    
    def truncate_to_budget(self, text: str, max_tokens: int) -> str:
        """Tronque texte pour respecter budget tokens."""
        max_chars = max_tokens * self.chars_per_token
        
        if len(text) <= max_chars:
            return text
        
        # Tronquer et ajouter ellipse
        return text[:max_chars - 3] + "..."
    
    def format_summary_metadata(self, metadata: Dict) -> str:
        """Formate métadonnées résumé pour affichage."""
        date = metadata['modified'].strftime("%d/%m/%Y %H:%M")
        size_kb = metadata['size'] / 1024
        fusion_flag = "🔄 FUSION" if metadata['is_fusion'] else "📝"
        
        return f"{fusion_flag} {date} ({size_kb:.1f} KB)"
