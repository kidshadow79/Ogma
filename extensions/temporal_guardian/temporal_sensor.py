"""
Capteur Temporel Simple pour OGMA
================================

Capteur de mesure pure des délais temporels entre messages utilisateur.
Ne fait AUCUNE interprétation - fournit seulement des données brutes.

Philosophie: Un chronomètre intelligent qui mesure sans juger.
"""

import time
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from dataclasses import dataclass


@dataclass
class TemporalMeasurement:
    """Mesure temporelle brute d'un message utilisateur."""
    message_timestamp: datetime
    delay_since_last: Optional[float]  # None pour le premier message
    current_time_str: str  # Format lisible "22:35"
    session_duration: float  # Durée session en secondes
    message_count: int  # Numéro du message dans la session
    average_delay: Optional[float]  # Délai moyen utilisateur (None si <3 messages)


class TemporalSensor:
    """
    Capteur temporel simple - Mesure les délais entre messages utilisateur.
    
    Responsabilités:
    - Mesurer délais entre messages
    - Collecter métadonnées temporelles
    - Calculer statistiques session basiques
    
    NE fait PAS:
    - Interprétation des délais
    - Classification des patterns
    - Analyse comportementale
    """
    
    def __init__(self, debug: bool = False):
        self.debug = debug
        
        # État session
        self.session_start = datetime.now()
        self.last_message_time: Optional[datetime] = None
        self.message_delays: List[float] = []  # Historique délais pour moyenne
        self.message_count = 0
        
        # Configuration
        self.max_delays_history = 50  # Limite mémoire pour calcul moyenne
        
        if self.debug:
            print(f"[TemporalSensor] Session démarrée à {self.session_start.strftime('%H:%M:%S')}")
    
    def register_message(self, message_content: str = "") -> TemporalMeasurement:
        """
        Enregistre un nouveau message utilisateur et retourne les mesures temporelles.
        
        Args:
            message_content: Contenu du message (optionnel, pour debug)
            
        Returns:
            TemporalMeasurement: Données temporelles brutes
        """
        now = datetime.now()
        self.message_count += 1
        
        # Calculer délai depuis dernier message
        delay_since_last = None
        if self.last_message_time is not None:
            delay_since_last = (now - self.last_message_time).total_seconds()
            self.message_delays.append(delay_since_last)
            
            # Limiter historique pour éviter surcharge mémoire
            if len(self.message_delays) > self.max_delays_history:
                self.message_delays = self.message_delays[-self.max_delays_history:]
        
        # Calculer délai moyen (nécessite au moins 3 mesures)
        average_delay = None
        if len(self.message_delays) >= 3:
            average_delay = sum(self.message_delays) / len(self.message_delays)
        
        # Calculer durée session
        session_duration = (now - self.session_start).total_seconds()
        
        # Créer mesure
        measurement = TemporalMeasurement(
            message_timestamp=now,
            delay_since_last=delay_since_last,
            current_time_str=now.strftime("%H:%M"),
            session_duration=session_duration,
            message_count=self.message_count,
            average_delay=average_delay
        )
        
        # Mettre à jour état
        self.last_message_time = now
        
        if self.debug:
            self._debug_print(measurement, message_content)
        
        return measurement
    
    def get_session_stats(self) -> Dict:
        """Retourne statistiques session pour debug/monitoring."""
        now = datetime.now()
        session_duration = (now - self.session_start).total_seconds()
        
        return {
            "session_start": self.session_start.isoformat(),
            "session_duration_minutes": session_duration / 60,
            "total_messages": self.message_count,
            "average_delay": sum(self.message_delays) / len(self.message_delays) if self.message_delays else None,
            "min_delay": min(self.message_delays) if self.message_delays else None,
            "max_delay": max(self.message_delays) if self.message_delays else None,
            "delays_count": len(self.message_delays)
        }
    
    def reset_session(self):
        """Démarre une nouvelle session (reset compteurs)."""
        if self.debug:
            print(f"[TemporalSensor] Nouvelle session démarrée")
        
        self.session_start = datetime.now()
        self.last_message_time = None
        self.message_delays.clear()
        self.message_count = 0
    
    def is_new_session_needed(self, inactivity_minutes: int = 30) -> bool:
        """
        Détermine si une nouvelle session doit être créée basée sur l'inactivité.
        
        Args:
            inactivity_minutes: Seuil d'inactivité en minutes
            
        Returns:
            bool: True si nouvelle session recommandée
        """
        if self.last_message_time is None:
            return False
        
        now = datetime.now()
        inactivity = (now - self.last_message_time).total_seconds() / 60
        return inactivity >= inactivity_minutes
    
    def _debug_print(self, measurement: TemporalMeasurement, message_content: str):
        """Affichage debug des mesures."""
        delay_str = f"{measurement.delay_since_last:.1f}s" if measurement.delay_since_last else "Premier message"
        avg_str = f"(moy: {measurement.average_delay:.1f}s)" if measurement.average_delay else ""
        
        print(f"[TemporalSensor] #{measurement.message_count} | Délai: {delay_str} {avg_str}")
        if message_content and len(message_content) > 0:
            preview = message_content[:50] + "..." if len(message_content) > 50 else message_content
            print(f"[TemporalSensor] Message: {preview}")


# Test du capteur si exécuté directement
if __name__ == "__main__":
    print("Test du TemporalSensor")
    print("=" * 30)
    
    sensor = TemporalSensor(debug=True)
    
    # Simuler quelques messages avec délais
    import time
    
    measurement1 = sensor.register_message("Bonjour Luna")
    print()
    
    time.sleep(2)
    measurement2 = sensor.register_message("Comment ça va ?")
    print()
    
    time.sleep(5)
    measurement3 = sensor.register_message("Tu peux m'aider avec un problème ?")
    print()
    
    # Afficher stats session
    print("\nStatistiques session:")
    stats = sensor.get_session_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")