"""
Configuration pour l'extension Temporal Guardian
==============================================

Gère les paramètres de l'extension temporelle.
"""

class TemporalGuardianConfig:
    """Configuration pour l'extension Temporal Guardian."""
    
    def __init__(self):
        # Configuration générale
        self.enabled = True
        self.debug_mode = False
        
        # Configuration capteur temporel
        self.collect_session_stats = True
        self.max_history_messages = 100
        
        # Configuration archiviste
        self.enrich_archiviste_prompt = True
        self.temporal_context_format = "detailed"  # "simple" ou "detailed"
        
        # Métriques
        self.track_average_delays = True
        self.session_timeout_minutes = 30  # Nouvelle session après 30min inactivité
        self.enrichment_threshold_seconds = 30  # Seuil délai pour enrichissement (secondes)
    
    def get_prompt_enrichment_template(self) -> str:
        """Retourne le template pour enrichir le prompt archiviste."""
        if self.temporal_context_format == "simple":
            return """
CONTEXTE TEMPOREL:
- Délai depuis dernier message: {delay_seconds}s
- Heure: {current_time}
"""
        else:  # detailed
            return """
CONTEXTE TEMPOREL DÉTAILLÉ:
- Délai depuis dernier message: {delay_seconds} secondes
- Heure actuelle: {current_time}
- Session active depuis: {session_duration}
- Nombre de messages dans la session: {message_count}
- Délai moyen de l'utilisateur: {average_delay}s
- Variation par rapport à la normale: {delay_variation}
"""
    
    def to_dict(self) -> dict:
        """Exporte la configuration en dictionnaire."""
        return {
            "enabled": self.enabled,
            "debug_mode": self.debug_mode,
            "collect_session_stats": self.collect_session_stats,
            "max_history_messages": self.max_history_messages,
            "enrich_archiviste_prompt": self.enrich_archiviste_prompt,
            "temporal_context_format": self.temporal_context_format,
            "track_average_delays": self.track_average_delays,
            "session_timeout_minutes": self.session_timeout_minutes,
            "enrichment_threshold_seconds": self.enrichment_threshold_seconds
        }
    
    @classmethod
    def from_dict(cls, config_dict: dict) -> 'TemporalGuardianConfig':
        """Crée une configuration depuis un dictionnaire."""
        config = cls()
        for key, value in config_dict.items():
            if hasattr(config, key):
                setattr(config, key, value)
        return config