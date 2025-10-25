"""
Enrichisseur d'Archiviste pour Analyse Temporelle
================================================

Enrichit le prompt de l'archiviste avec le contexte temporel mesuré par le capteur.
L'archiviste reçoit les données et en déduit les patterns comportementaux.

Philosophie: Le capteur mesure, l'archiviste interprète.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from .temporal_sensor import TemporalMeasurement, TemporalSensor
from .config import TemporalGuardianConfig


class ArchivisteEnricher:
    """
    Enrichit le prompt de l'archiviste avec le contexte temporel.
    
    Responsabilités:
    - Formater données temporelles pour l'archiviste
    - Adapter format selon configuration (simple/détaillé)
    - Injecter contexte temporal dans prompt archiviste
    
    L'archiviste recevra les données et déduira lui-même:
    - Patterns de fatigue utilisateur
    - Moments de réflexion vs pause
    - Variations comportementales
    """
    
    def __init__(self, config: TemporalGuardianConfig, debug: bool = False):
        self.config = config
        self.debug = debug
        
        if self.debug:
            print(f"[ArchivisteEnricher] Mode: {config.temporal_context_format}")
    
    def enrich_archiviste_prompt(
        self, 
        base_prompt: str, 
        measurement: TemporalMeasurement,
        user_message: str = ""
    ) -> str:
        """
        Enrichit le prompt de l'archiviste avec le contexte temporel.
        
        Args:
            base_prompt: Prompt archiviste de base
            measurement: Mesures temporelles du capteur
            user_message: Message utilisateur actuel
            
        Returns:
            str: Prompt enrichi avec contexte temporel
        """
        if not self.config.enrich_archiviste_prompt:
            return base_prompt
        
        # Choisir format d'enrichissement
        if self.config.temporal_context_format == "detailed":
            temporal_context = self._format_detailed_context(measurement, user_message)
        else:
            temporal_context = self._format_simple_context(measurement, user_message)
        
        # Injecter dans prompt selon template
        enriched_prompt = self._inject_temporal_context(base_prompt, temporal_context)
        
        if self.debug:
            self._debug_print_enrichment(measurement, temporal_context)
        
        return enriched_prompt
    
    def _format_simple_context(self, measurement: TemporalMeasurement, user_message: str) -> str:
        """Format simple - juste délai et heure."""
        if measurement.delay_since_last is None:
            return f"Session démarrée à {measurement.current_time_str}"
        
        delay_minutes = measurement.delay_since_last / 60
        if delay_minutes < 1:
            delay_str = f"{measurement.delay_since_last:.0f}s"
        else:
            delay_str = f"{delay_minutes:.1f}min"
        
        return f"Délai: {delay_str} (msg #{measurement.message_count})"
    
    def _format_detailed_context(self, measurement: TemporalMeasurement, user_message: str) -> str:
        """Format détaillé - stats complètes."""
        context_parts = []
        
        # Heure et délai principal
        context_parts.append(f"🕒 {measurement.current_time_str}")
        
        if measurement.delay_since_last is not None:
            delay_minutes = measurement.delay_since_last / 60
            if delay_minutes < 1:
                delay_str = f"{measurement.delay_since_last:.0f}s"
            else:
                delay_str = f"{delay_minutes:.1f}min"
            context_parts.append(f"⏱️ Délai: {delay_str}")
        else:
            context_parts.append("🆕 Premier message session")
        
        # Stats session
        session_minutes = measurement.session_duration / 60
        context_parts.append(f"📊 Session: {session_minutes:.0f}min, {measurement.message_count} messages")
        
        # Délai moyen si disponible
        if measurement.average_delay is not None:
            avg_minutes = measurement.average_delay / 60
            if avg_minutes < 1:
                avg_str = f"{measurement.average_delay:.0f}s"
            else:
                avg_str = f"{avg_minutes:.1f}min"
            context_parts.append(f"📈 Rythme moyen: {avg_str}")
        
        return " | ".join(context_parts)
    
    def _inject_temporal_context(self, base_prompt: str, temporal_context: str) -> str:
        """Injecte le contexte temporel dans le prompt de base."""
        # Utiliser template de configuration
        template = self.config.get_prompt_enrichment_template()
        
        # Remplacer placeholders dans template si besoin
        # Pour l'instant, simple injection directe
        enriched_prompt = f"{base_prompt}\n\n{temporal_context}"
        
        return enriched_prompt
    
    def should_enrich_this_message(self, measurement: TemporalMeasurement) -> bool:
        """
        Détermine si ce message nécessite enrichissement temporel.
        
        Critères:
        - Premier message: toujours enrichir
        - Délais significatifs: enrichir si > seuil
        - Messages fréquents: enrichir occasionnellement
        """
        if measurement.delay_since_last is None:
            return True  # Premier message
        
        # Enrichir si délai > seuil configuré (par défaut 30 secondes)
        enrichment_threshold = getattr(self.config, 'enrichment_threshold_seconds', 30)
        if measurement.delay_since_last >= enrichment_threshold:
            return True
        
        # Enrichir périodiquement même pour messages rapides
        if measurement.message_count % 5 == 0:  # Tous les 5 messages
            return True
        
        return False
    
    def create_temporal_summary(self, measurements: list[TemporalMeasurement]) -> str:
        """
        Crée un résumé temporel de session pour analyse archiviste.
        
        Utilisé pour analyser patterns sur plusieurs messages.
        """
        if not measurements:
            return "Aucune donnée temporelle disponible"
        
        delays = [m.delay_since_last for m in measurements if m.delay_since_last is not None]
        
        if not delays:
            return "Session débutante, pas encore de patterns temporels"
        
        # Statistiques basiques
        avg_delay = sum(delays) / len(delays)
        min_delay = min(delays)
        max_delay = max(delays)
        
        # Classer délais
        quick_responses = sum(1 for d in delays if d <= 10)  # ≤ 10s
        normal_responses = sum(1 for d in delays if 10 < d <= 60)  # 10s-1min
        slow_responses = sum(1 for d in delays if d > 60)  # > 1min
        
        summary_parts = [
            f"📊 Analyse temporelle session ({len(delays)} intervalles):",
            f"   • Réponses rapides (≤10s): {quick_responses}",
            f"   • Réponses normales (10s-1min): {normal_responses}",
            f"   • Réponses lentes (>1min): {slow_responses}",
            f"   • Délai moyen: {avg_delay:.1f}s",
            f"   • Variation: {min_delay:.1f}s → {max_delay:.1f}s"
        ]
        
        return "\n".join(summary_parts)
    
    def _debug_print_enrichment(self, measurement: TemporalMeasurement, temporal_context: str):
        """Debug de l'enrichissement."""
        print(f"[ArchivisteEnricher] Contexte injecté: {temporal_context}")
        if measurement.delay_since_last:
            print(f"[ArchivisteEnricher] Délai mesuré: {measurement.delay_since_last:.1f}s")


# Test de l'enrichisseur si exécuté directement
if __name__ == "__main__":
    print("Test de l'ArchivisteEnricher")
    print("=" * 35)
    
    from .config import TemporalGuardianConfig
    from .temporal_sensor import TemporalSensor
    import time
    
    # Configuration test
    config = TemporalGuardianConfig()
    enricher = ArchivisteEnricher(config, debug=True)
    sensor = TemporalSensor(debug=False)
    
    # Prompt archiviste de base
    base_prompt = "Analysez ce message utilisateur et mémorisez les éléments importants."
    
    # Test enrichissement simple
    print("\n1. Test enrichissement simple:")
    measurement1 = sensor.register_message("Bonjour")
    enriched1 = enricher.enrich_archiviste_prompt(base_prompt, measurement1, "Bonjour")
    print("Prompt enrichi:", enriched1)
    
    # Test avec délai
    print("\n2. Test avec délai:")
    time.sleep(2)
    measurement2 = sensor.register_message("Comment ça va ?")
    enriched2 = enricher.enrich_archiviste_prompt(base_prompt, measurement2, "Comment ça va ?")
    print("Prompt enrichi:", enriched2)
    
    # Test format détaillé
    print("\n3. Test format détaillé:")
    config.temporal_context_format = "detailed"
    enricher_detailed = ArchivisteEnricher(config, debug=True)
    time.sleep(3)
    measurement3 = sensor.register_message("Question complexe ici")
    enriched3 = enricher_detailed.enrich_archiviste_prompt(base_prompt, measurement3, "Question complexe ici")
    print("Prompt enrichi détaillé:", enriched3)