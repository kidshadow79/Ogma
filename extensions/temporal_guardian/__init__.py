"""
Extension Temporal Guardian pour OGMA
====================================

Extension dédiée à la gestion temporelle intelligente.
Fournit un capteur temporel simple et enrichit l'archiviste 
avec des données temporelles pour une analyse contextuelle organique.

Architecture:
- temporal_sensor.py: Capteur de délais temporels (mesure pure)
- archiviste_enricher.py: Enrichissement prompt archiviste
- temporal_guardian.py: Orchestrateur principal
- config.py: Configuration extension

Philosophie: Le capteur mesure, l'archiviste interprète.

Usage:
    from extensions.temporal_guardian import create_temporal_guardian
    
    guardian = create_temporal_guardian(debug=True)
    result = guardian.process_user_message(user_message, archiviste_prompt)
"""

from .temporal_sensor import TemporalSensor, TemporalMeasurement
from .archiviste_enricher import ArchivisteEnricher
from .config import TemporalGuardianConfig
from .temporal_guardian import TemporalGuardian, create_temporal_guardian

__version__ = "1.0.0"
__author__ = "OGMA Team"

# Interface publique de l'extension
__all__ = [
    'TemporalGuardian', 
    'create_temporal_guardian',
    'TemporalSensor', 
    'TemporalMeasurement',
    'ArchivisteEnricher', 
    'TemporalGuardianConfig'
]