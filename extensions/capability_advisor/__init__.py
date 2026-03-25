# 🎯 Extension Capability Advisor
"""
Extension intelligente de suggestion de capacités IA via Archiviste
Pattern: Singleton identique à archi_sensor et ego_selector

Workflow:
1. Archiviste analyse chaque message utilisateur
2. Suggère UNE capacité si contexte pertinent (pas systématique)
3. LED s'allume pour capacité suggérée
4. IA principale reçoit conseil concis
5. LED s'éteint après utilisation effective de la capacité

Capacités gérées (6 total):
- Mémorisation (💾)
- Introspection (🧠)
- Génération Image (🎨)
- Vision Webcam (📷)
- Recherche Web (🌐)
- Consultation Biographie (👤)
"""

from typing import Optional

from .config import CapabilityAdvisorConfig
from .capability_catalog import get_capability, get_all_capabilities, set_config_instance
from .advisor_core import AdvisorCore, CapabilitySuggestion
from .suggestion_engine import SuggestionEngine
from .led_manager import LEDManager
from .ui_components import CapabilityAdvisorUI


# Singleton instance
_capability_advisor_instance: Optional['CapabilityAdvisor'] = None


class CapabilityAdvisor:
    """Gestionnaire principal extension Capability Advisor"""
    
    def __init__(
        self, 
        chat_controller,
        archiviste_controller,
        memory_manager
    ):
        """
        Initialise Capability Advisor
        
        Args:
            chat_controller: Contrôleur IA principale
            archiviste_controller: Contrôleur IA Archiviste
            memory_manager: Gestionnaire mémoire
        """
        self.chat_controller = chat_controller
        self.archiviste_controller = archiviste_controller
        self.memory_manager = memory_manager
        
        # Configuration
        self.config = CapabilityAdvisorConfig()
        
        # Injecter instance config dans capability_catalog pour IDs mémoire dynamiques
        set_config_instance(self.config)
        
        # Composants core
        self.advisor_core = AdvisorCore(archiviste_controller, self.config)
        self.suggestion_engine = SuggestionEngine()
        self.led_manager = LEDManager(led_timeout=self.config.config.get('led_timeout', 30))
        
        # UI Components
        self.ui = CapabilityAdvisorUI(self.led_manager, self.config)
        
        # État suggestion courante
        self.current_suggestion: Optional[CapabilitySuggestion] = None
        
        # Cooldown système: évite suggestions trop fréquentes
        self._message_counter = 0  # Compteur messages utilisateur
        self._last_suggestion_at = -99  # Message où dernière suggestion faite
        self._cooldown_messages = self.config.config.get('cooldown_messages', 3)  # Minimum 3 messages entre suggestions
        
        print(f"[CAPABILITY-ADVISOR] ✅ Instance principale créée")
    
    async def analyze_conversation(
        self, 
        user_message: str, 
        conversation_history: list
    ) -> Optional[CapabilitySuggestion]:
        """
        Analyse conversation et suggère capacité si pertinent
        
        Args:
            user_message: Message utilisateur
            conversation_history: Historique conversation
            
        Returns:
            CapabilitySuggestion | None
        """
        if not self.is_enabled():
            return None
        
        # Incrémenter compteur messages
        self._message_counter += 1
        
        # Détection de demande explicite (bypass cooldown)
        # Si l'utilisateur demande explicitement une capacité, on analyse quand même
        import re
        explicit_request_patterns = [
            # Web search
            r'\b(?:cherche|recherche|regarde|trouve|va voir|dis[- ]?moi)\b.*\b(?:internet|web|google|en ligne)\b',
            r'\b(?:internet|web)\b.*\b(?:cherche|recherche|regarde|trouve)\b',
            # Biographie
            r'\b(?:qui (?:est|suis)|c\'?est qui|parle[- ]?moi de|infos? sur)\b',
            # Image generation
            r'\b(?:génère|crée|fais|dessine)[- ]?(?:moi)?\b.*\b(?:image|photo|dessin|illustration)\b',
            # Webcam
            r'\b(?:regarde|vois|montre)[- ]?moi\b|\b(?:active|allume).*(?:caméra|webcam|vision)\b',
        ]
        
        is_explicit_request = any(re.search(pattern, user_message.lower()) for pattern in explicit_request_patterns)
        
        # Vérifier cooldown: au moins N messages depuis dernière suggestion
        messages_since_last = self._message_counter - self._last_suggestion_at
        if messages_since_last < self._cooldown_messages and not is_explicit_request:
            print(f"[CAPABILITY-ADVISOR] ⏸️ Cooldown actif ({messages_since_last}/{self._cooldown_messages} messages)")
            return None
        
        if is_explicit_request:
            print(f"[CAPABILITY-ADVISOR] 🎯 Demande explicite détectée - bypass cooldown")
        
        # Appel advisor_core pour analyse Archiviste
        suggestion = await self.advisor_core.analyze_conversation(
            user_message, 
            conversation_history
        )
        
        if suggestion:
            # Sauvegarder suggestion courante
            self.current_suggestion = suggestion
            
            # Marquer message de la suggestion
            self._last_suggestion_at = self._message_counter
            print(f"[CAPABILITY-ADVISOR] 🎯 Suggestion faite au message #{self._message_counter}")
            
            # Allumer LED capacité (restera allumée jusqu'au message suivant)
            self.led_manager.activate_led(suggestion.capability_id)
            
            # ⚠️ DÉSACTIVÉ: Extinction uniquement au message suivant
            # self.led_manager.schedule_deactivation(suggestion.capability_id)
        
        return suggestion
    
    def format_suggestion_for_injection(self, suggestion: CapabilitySuggestion) -> str:
        """
        Formate suggestion pour injection system prompt
        
        Args:
            suggestion: Suggestion Archiviste
            
        Returns:
            str: Message formaté injection
        """
        return self.suggestion_engine.format_for_injection(suggestion)
    
    def detect_capability_usage(self, ai_response: str) -> bool:
        """
        [DÉSACTIVÉ] Détection utilisation capacité
        L'extinction se fait uniquement au message utilisateur suivant.
        
        Args:
            ai_response: Réponse IA principale
            
        Returns:
            bool: False (désactivé)
        """
        # ⚠️ DÉSACTIVÉ - Les LEDs s'éteignent uniquement au message suivant
        return False
    
    def is_enabled(self) -> bool:
        """Vérifie si extension est activée"""
        return self.config.is_enabled()
    
    def get_ui_components(self) -> dict:
        """
        Retourne composants UI pour intégration header
        
        Returns:
            dict: {'header_button': callable}
        """
        return {
            'header_button': self.ui.create_header_button(),
            'inject_css': self.ui.inject_css_styles
        }
    
    def cleanup(self):
        """Nettoyage avant fermeture"""
        self.led_manager.cleanup()
        print(f"[CAPABILITY-ADVISOR] 🧹 Cleanup terminé")


def initialize_capability_advisor(
    chat_controller,
    archiviste_controller,
    memory_manager
) -> Optional[CapabilityAdvisor]:
    """
    Initialise extension Capability Advisor (singleton)
    
    Args:
        chat_controller: Contrôleur IA principale
        archiviste_controller: Contrôleur IA Archiviste
        memory_manager: Gestionnaire mémoire
        
    Returns:
        CapabilityAdvisor | None
    """
    global _capability_advisor_instance
    
    if _capability_advisor_instance is None:
        try:
            _capability_advisor_instance = CapabilityAdvisor(
                chat_controller=chat_controller,
                archiviste_controller=archiviste_controller,
                memory_manager=memory_manager
            )
            print(f"[CAPABILITY-ADVISOR] ✅ Extension initialisée avec succès")
        except Exception as e:
            print(f"[CAPABILITY-ADVISOR] ❌ Erreur initialisation: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    return _capability_advisor_instance


def is_available() -> bool:
    """Vérifie disponibilité extension"""
    return _capability_advisor_instance is not None


def get_capability_advisor() -> Optional[CapabilityAdvisor]:
    """Récupère instance singleton"""
    return _capability_advisor_instance


def cleanup():
    """Nettoyage extension"""
    global _capability_advisor_instance
    
    if _capability_advisor_instance:
        _capability_advisor_instance.cleanup()
        _capability_advisor_instance = None
        print(f"[CAPABILITY-ADVISOR] Extension cleanup OK")


# Exposer API publique
__all__ = [
    'CapabilityAdvisor',
    'initialize_capability_advisor',
    'is_available',
    'get_capability_advisor',
    'cleanup'
]
