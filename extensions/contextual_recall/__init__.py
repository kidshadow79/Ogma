"""
🧠 CONTEXTUAL RECALL - Extension mémoire conversationnelle intelligente
=======================================================================

Cette extension permet à Luna d'accéder automatiquement à sa mémoire de
conversations passées via les résumés intégrés aux fichiers JSON dès lors
qu'une question fait référence à une période temporelle.

PHILOSOPHIE:
- Détection contextuelle SANS phrase magique
- Accès transparent aux résumés persistés dans les conversations JSON
- Injection intelligente dans le contexte système

ARCHITECTURE:
- TemporalParser: Détection expressions temporelles ("il y a 2 jours")
- SummaryLoader: Accès aux résumés depuis conversations JSON (v2.2+)
- ContextBuilder: Formatage contexte pour injection
- RecallAgent: Orchestration et API publique

PATTERN D'INTÉGRATION:
```python
from extensions.contextual_recall import initialize_recall, is_available

# Initialisation (v2.2+ - plus besoin de summaries_cache_path)
recall_extension = initialize_recall(
    conversations_path="data/conversations"
)

# Utilisation dans pipeline chat
if recall_extension and is_available():
    context = recall_extension.process_message(user_message)
    if context:
        messages.insert(0, {'role': 'system', 'content': context})
```

DÉPENDANCES:
- conversation_summarizer.py (API get_all_summaries_from_conversations)
- data/conversations/ (fichiers JSON avec résumés intégrés)

MIGRATION v2.2:
- Ancien: summaries_cache/*.txt (SUPPRIMÉ)
- Nouveau: résumés dans JSON conversations

Auteur: Yohan BROCARD
Version: 2.0.0 (Migration résumés JSON)
Date: 5 février 2026
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
__version__ = "2.0.0"

# Instance globale (singleton pattern)
_recall_agent: Optional[RecallAgent] = None


def initialize_recall(
    conversations_path: str = "data/conversations",
    debug: bool = False,
    **kwargs  # Ignore les anciens paramètres (summaries_cache_path, etc.)
) -> Optional[RecallAgent]:
    """
    Initialise l'extension Contextual Recall.
    
    Args:
        conversations_path: Chemin vers historique conversations JSON
        debug: Mode debug verbeux
        **kwargs: Ignore les anciens paramètres pour rétrocompatibilité
        
    Returns:
        Instance RecallAgent ou None si échec
    """
    global _recall_agent
    
    try:
        print("[CONTEXTUAL-RECALL] 🧠 Initialisation extension v2.0...")
        
        # Vérifier existence répertoire conversations
        conversations_dir = Path(conversations_path)
        if not conversations_dir.exists():
            print(f"[CONTEXTUAL-RECALL] ⚠️ Répertoire conversations introuvable: {conversations_path}")
            return None
            
        # Initialiser composants
        temporal_parser = TemporalParser(debug=debug)
        summary_loader = SummaryLoader(
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
        
        stats = summary_loader.get_statistics()
        print(f"[CONTEXTUAL-RECALL] ✅ Extension initialisée ({stats['total_summaries']} résumés dans {stats['conversations_with_summaries']} conversations)")
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
