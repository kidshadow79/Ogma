"""
archiviste_decision.py
---------------------
Archiviste décideur intelligent pour OGMA v2.0

Détermine le niveau de recherche mémorielle nécessaire selon la complexité
de la requête utilisateur, optimisant ainsi les performances et coûts API.
"""

import re
from enum import Enum
from typing import Optional, Dict, Any


class MemorySearchLevel(Enum):
    """Niveaux de recherche mémorielle."""
    SKIP = "skip"           # Pas de recherche
    LIGHT = "light"         # Recherche légère (k=1-2)
    STANDARD = "standard"   # Recherche normale (k=3-5)
    DEEP = "deep"          # Recherche approfondie (k=5+)


class ArchivisteDecision:
    """
    Archiviste décideur intelligent.
    
    Analyse la complexité des requêtes utilisateur pour optimiser
    la recherche mémorielle et réduire la latence/coûts.
    """
    
    # Patterns de détection
    SKIP_PATTERNS = {
        'salutations': [
            r'\b(salut|bonjour|bonsoir|hello|hey|hi|coucou)\b',
            r'^(yo|re|plop)$'
        ],
        'acknowledgments': [
            r'\b(ok|okay|oui|non|merci|thanks|d\'accord)\b',
            r'^(👍|👌|🙂|😊|😄|😁|👋)$'
        ],
        'short_responses': [
            r'^.{1,4}$',  # Messages très courts
            r'^[.!?]{1,3}$'  # Ponctuation seule
        ]
    }
    
    LIGHT_PATTERNS = {
        'simple_questions': [
            r'\b(ça va|comment tu vas|quoi de neuf)\b',
            r'^(comment|pourquoi|quand|où) \w{1,10}\?*$',  # Questions courtes
        ],
        'casual_talk': [
            r'\b(sympa|cool|bien|génial|super)\b'
        ]
    }
    
    DEEP_PATTERNS = {
        'temporal_references': [
            r'\b(la dernière fois|avant|précédemment|auparavant)\b',
            r'\b(comment j\'ai|comment on a|quand j\'ai)\b',
            r'\b(souviens-toi|rappelle-toi|tu te rappelles)\b'
        ],
        'specific_references': [
            r'\b(ce dont on a parlé|notre conversation|notre discussion)\b',
            r'\b(le projet|le problème|la solution)\b'
        ],
        'complex_topics': [
            r'\b(architecture|implémentation|algorithme|optimisation)\b',
            r'\b(configuration|paramètres|settings)\b'
        ]
    }
    
    @classmethod
    def analyze_query_complexity(cls, message: str) -> MemorySearchLevel:
        """
        Analyse la complexité d'une requête pour décider du niveau de recherche.
        
        Args:
            message: Le message utilisateur à analyser
            
        Returns:
            MemorySearchLevel: Le niveau de recherche recommandé
        """
        if not message or not message.strip():
            return MemorySearchLevel.SKIP
            
        message_clean = message.lower().strip()
        message_length = len(message_clean)
        
        # 1. SKIP - Pas de recherche nécessaire
        if cls._matches_patterns(message_clean, cls.SKIP_PATTERNS):
            return MemorySearchLevel.SKIP
            
        # 2. DEEP - Recherche approfondie
        if cls._matches_patterns(message_clean, cls.DEEP_PATTERNS):
            return MemorySearchLevel.DEEP
            
        # 3. LIGHT - Recherche légère
        if message_length <= 20 or cls._matches_patterns(message_clean, cls.LIGHT_PATTERNS):
            return MemorySearchLevel.LIGHT
            
        # 4. STANDARD - Par défaut pour messages moyens
        if message_length <= 100:
            return MemorySearchLevel.STANDARD
            
        # 5. DEEP - Messages longs = sujets complexes
        return MemorySearchLevel.DEEP
    
    @classmethod
    def _matches_patterns(cls, text: str, pattern_groups: Dict[str, list]) -> bool:
        """Vérifie si le texte correspond à un des groupes de patterns."""
        for group_name, patterns in pattern_groups.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return True
        return False
    
    @classmethod
    def get_search_params(cls, level: MemorySearchLevel) -> Dict[str, Any]:
        """
        Retourne les paramètres de recherche selon le niveau.
        
        Returns:
            Dict contenant 'k' (nombre de résultats) et 'enabled' (bool)
        """
        params_map = {
            MemorySearchLevel.SKIP: {'k': 0, 'enabled': False},
            MemorySearchLevel.LIGHT: {'k': 2, 'enabled': True},
            MemorySearchLevel.STANDARD: {'k': 3, 'enabled': True}, 
            MemorySearchLevel.DEEP: {'k': 5, 'enabled': True}
        }
        
        return params_map.get(level, {'k': 3, 'enabled': True})
    
    @classmethod
    def get_decision_summary(cls, message: str, level: MemorySearchLevel, params: Dict[str, Any]) -> str:
        """Génère un résumé de la décision pour les logs."""
        action = "SKIP" if not params['enabled'] else f"SEARCH(k={params['k']})"
        length = len(message.strip())
        
        return f"[ARCHIVISTE-DECISION] '{message[:30]}...' ({length}c) -> {level.value.upper()} -> {action}"


# === FONCTIONS UTILITAIRES ===

def decide_memory_search(message: str) -> tuple[MemorySearchLevel, Dict[str, Any]]:
    """
    Interface principale pour la décision de recherche mémorielle.
    
    Args:
        message: Message utilisateur
        
    Returns:
        tuple: (niveau, paramètres_recherche)
    """
    level = ArchivisteDecision.analyze_query_complexity(message)
    params = ArchivisteDecision.get_search_params(level)
    
    # Log de la décision
    summary = ArchivisteDecision.get_decision_summary(message, level, params)
    print(summary)
    
    return level, params


# === TESTS INTÉGRÉS ===

def test_decision_logic():
    """Tests de la logique de décision."""
    test_cases = [
        ("salut", MemorySearchLevel.SKIP),
        ("👍", MemorySearchLevel.SKIP),
        ("ok", MemorySearchLevel.SKIP),
        ("ça va ?", MemorySearchLevel.LIGHT),
        ("comment ça marche ?", MemorySearchLevel.STANDARD),
        ("comment j'ai résolu le problème la dernière fois ?", MemorySearchLevel.DEEP),
        ("explique-moi l'architecture du système avec tous les détails techniques", MemorySearchLevel.DEEP),
    ]
    
    print("TEST Archiviste Decideur:")
    for message, expected in test_cases:
        level, params = decide_memory_search(message)
        status = "OK" if level == expected else "FAIL"
        print(f"  {status} '{message}' -> {level.value} (attendu: {expected.value})")


if __name__ == "__main__":
    test_decision_logic()