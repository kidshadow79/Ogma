"""
🧠 CONTEXTUAL RECALL - Extension mémoire conversationnelle intelligente
=======================================================================

Cette extension permet à Luna d'accéder automatiquement à sa mémoire de
conversations passées via les résumés du cache (summaries_cache) dès lors
qu'une question fait référence à une période temporelle.

PHILOSOPHIE:
- Détection contextuelle SANS phrase magique
- Accès transparent aux résumés progressifs existants
- Injection intelligente dans le contexte système

ARCHITECTURE:
- TemporalParser: Détection expressions temporelles ("il y a 2 jours")
- SummaryLoader: Accès optimisé aux résumés en cache
- ContextBuilder: Formatage contexte pour injection
- RecallAgent: Orchestration et API publique

PATTERN D'INTÉGRATION:
```python
from extensions.contextual_recall import initialize_recall, is_available

# Initialisation
recall_extension = initialize_recall(
    summaries_cache_path="data/summaries_cache",
    conversations_path="data/conversations"
)

# Utilisation dans pipeline chat
if recall_extension and is_available():
    context = recall_extension.process_message(user_message)
    if context:
        messages.insert(0, {'role': 'system', 'content': context})
```

DÉPENDANCES:
- conversation_summarizer.py (système résumés existant)
- data/summaries_cache/ (résumés progressifs)
- data/conversations/ (historique JSON optionnel)

Auteur: Yohan BROCARD
Version: 1.0.0
Date: 1 novembre 2025
"""

from pathlib import Path
from typing import Optional
import sys

# Import composants
from .recall_agent import RecallAgent
from .temporal_parser import TemporalParser
from .summary_loader import SummaryLoader
from .context_builder import ContextBuilder

# Version
__version__ = "1.0.0"

# Instance globale (singleton pattern)
_recall_agent: Optional[RecallAgent] = None


def initialize_recall(
    summaries_cache_path: str = "data/summaries_cache",
    conversations_path: str = "data/conversations",
    debug: bool = False
) -> Optional[RecallAgent]:
    """
    Initialise l'extension Contextual Recall.
    
    Args:
        summaries_cache_path: Chemin vers cache résumés
        conversations_path: Chemin vers historique conversations
        debug: Mode debug verbeux
        
    Returns:
        Instance RecallAgent ou None si échec
    """
    global _recall_agent
    
    try:
        print("[CONTEXTUAL-RECALL] 🧠 Initialisation extension...")
        
        # Vérifier existence répertoires
        summaries_path = Path(summaries_cache_path)
        if not summaries_path.exists():
            print(f"[CONTEXTUAL-RECALL] ⚠️ Répertoire summaries_cache introuvable: {summaries_cache_path}")
            return None
            
        # Initialiser composants
        temporal_parser = TemporalParser(debug=debug)
        summary_loader = SummaryLoader(
            cache_dir=summaries_cache_path,
            conversations_dir=conversations_path,
            debug=debug
        )
        context_builder = ContextBuilder(debug=debug)
        
        # Créer agent orchestrateur
        _recall_agent = RecallAgent(
            temporal_parser=temporal_parser,
            summary_loader=summary_loader,
            context_builder=context_builder,
            debug=debug
        )
        
        print(f"[CONTEXTUAL-RECALL] ✅ Extension initialisée ({len(summary_loader.list_cached_summaries())} résumés détectés)")
        return _recall_agent
        
    except Exception as e:
        print(f"[CONTEXTUAL-RECALL] ❌ Erreur initialisation: {e}")
        if debug:
            import traceback
            traceback.print_exc()
        return None


def is_available() -> bool:
    """Vérifie si l'extension est disponible."""
    return _recall_agent is not None


def get_recall_agent() -> Optional[RecallAgent]:
    """Retourne l'instance RecallAgent (singleton)."""
    return _recall_agent


def process_message(user_message: str) -> Optional[str]:
    """
    Traite un message utilisateur et retourne contexte si pertinent.
    
    Args:
        user_message: Message utilisateur brut
        
    Returns:
        Contexte formaté pour injection ou None
    """
    if not _recall_agent:
        return None
    return _recall_agent.process_message(user_message)


def cleanup():
    """Nettoyage propre de l'extension."""
    global _recall_agent
    if _recall_agent:
        print("[CONTEXTUAL-RECALL] 🔄 Nettoyage extension...")
        _recall_agent = None


# API publique standardisée (pattern OGMA)
__all__ = [
    "initialize_recall",
    "is_available", 
    "get_recall_agent",
    "process_message",
    "cleanup",
    "RecallAgent",
    "TemporalParser",
    "SummaryLoader",
    "ContextBuilder"
]
