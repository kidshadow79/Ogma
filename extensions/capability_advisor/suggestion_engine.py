# 🎯 Capability Advisor - Suggestion Engine
"""
Formatage injection system prompt + détection utilisation capacités
"""

import re
from typing import Optional
from .advisor_core import CapabilitySuggestion
from .capability_catalog import get_capability


class SuggestionEngine:
    """Moteur injection suggestions + détection utilisation"""
    
    def __init__(self):
        """Initialise suggestion engine"""
        print(f"[CAPABILITY-ADVISOR] ✅ SuggestionEngine initialisé")
    
    def format_for_injection(self, suggestion: CapabilitySuggestion) -> str:
        """
        Formate suggestion Archiviste pour injection system prompt
        FORMAT CHD - Ordre impératif du Subconscient
        
        Args:
            suggestion: Suggestion capacité Archiviste
            
        Returns:
            str: Ordre formaté (Protocole CHD)
        """
        # Format CHD - Directive technique explicite
        # Note spécifique pour la mémorisation de textes longs
        long_text_note = ""
        if suggestion.capability_id == 'memory':
            long_text_note = """
⚠️ TEXTES LONGS / MULTI-PARAGRAPHES : Encadre OBLIGATOIREMENT le contenu
de guillemets pour garantir la capture intégrale :
il faut que je me souvienne de ça : "[contenu complet ici]"
Sans guillemets, seul le premier paragraphe sera mémorisé."""

        injection = f"""╔═══════════════════════════════════════════════════╗
║  DIRECTIVE TECHNIQUE - PHRASE MAGIQUE REQUISE     ║
╚═══════════════════════════════════════════════════╝

ACTION REQUISE: Inclure TEXTUELLEMENT cette phrase dans ta réponse.
PHRASE EXACTE À ÉCRIRE (copier mot pour mot):

{suggestion.suggestion}

CONTEXTE: {suggestion.reasoning}{long_text_note}

⚠️ IMPORTANT: Cette phrase est un TRIGGER TECHNIQUE détecté par le système.
Si tu ne l'écris pas MOT POUR MOT dans ta réponse, la fonctionnalité
ne sera PAS déclenchée. Reformuler ou paraphraser NE FONCTIONNE PAS.
Le système cherche un pattern regex précis dans ta réponse.
═══════════════════════════════════════════════════"""
        
        print(f"[CAPABILITY-ADVISOR] 📤 Ordre CHD: {suggestion.suggestion[:60]}...")
        return injection
    
    def detect_capability_usage(
        self, 
        ai_response: str, 
        suggested_capability_id: str
    ) -> bool:
        """
        Détecte si IA a utilisé la capacité suggérée dans sa réponse
        
        Args:
            ai_response: Réponse complète de l'IA principale
            suggested_capability_id: ID capacité suggérée
            
        Returns:
            bool: True si capacité utilisée, False sinon
        """
        capability_info = get_capability(suggested_capability_id)
        
        if not capability_info:
            print(f"[CAPABILITY-ADVISOR] ⚠️ Capacité inconnue pour détection: {suggested_capability_id}")
            return False
        
        # Récupérer pattern regex phrase magique
        magic_phrase_pattern = capability_info.get('magic_phrase_pattern')
        
        if not magic_phrase_pattern:
            print(f"[CAPABILITY-ADVISOR] ⚠️ Pas de pattern regex pour {suggested_capability_id}")
            return False
        
        # Recherche phrase magique dans réponse IA
        match = re.search(magic_phrase_pattern, ai_response, re.IGNORECASE)
        
        if match:
            print(f"[CAPABILITY-ADVISOR] ✅ Capacité {suggested_capability_id} UTILISÉE")
            print(f"[CAPABILITY-ADVISOR] 📝 Phrase détectée: {match.group(0)}")
            return True
        
        print(f"[CAPABILITY-ADVISOR] ⚪ Capacité {suggested_capability_id} NON utilisée")
        return False
    
    def extract_capability_from_response(self, ai_response: str) -> Optional[str]:
        """
        Détecte quelle capacité a été utilisée dans réponse IA
        (Utile pour détection automatique sans suggestion préalable)
        
        Args:
            ai_response: Réponse complète de l'IA
            
        Returns:
            str | None: ID capacité détectée ou None
        """
        from .capability_catalog import get_all_capabilities
        
        capabilities = get_all_capabilities()
        
        for cap_id, cap_info in capabilities.items():
            pattern = cap_info.get('magic_phrase_pattern')
            if pattern and re.search(pattern, ai_response, re.IGNORECASE):
                return cap_id
        
        return None
