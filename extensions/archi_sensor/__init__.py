# 🧠 Extension Archi_sensor - Métacognition par IA Archiviste

"""
Extension révolutionnaire de métacognition utilisant l'IA Archiviste
pour une analyse contextuelle émotionnelle sophistiquée.

Architecture:
- Analyse unifiée par IA générative (vs patterns embedding)
- Compréhension narrative et évolution émotionnelle
- Détection nuances (sarcasme, ironie, subtext)
- Économie tokens optimisée (1 appel vs 7+ appels)
- Toggle exclusif avec extension metacognition_sensor
"""

from .core_archi_sensor import ArchiSensorCore
from .unified_analyzer import ArchivisteUnifiedAnalyzer
from .ui_components import ArchiSensorUI
from .config import ArchiSensorConfig

__version__ = "1.0.0"
__author__ = "OGMA Team"

# Points d'entrée publics
def get_archi_analyzer():
    """Retourne l'analyseur Archiviste principal"""
    try:
        return ArchiSensorCore.get_instance().analyzer
    except Exception as e:
        print(f"[ARCHI-SENSOR] Erreur récupération analyseur: {e}")
        return None

def is_available():
    """Vérifie si l'extension est disponible et fonctionnelle"""
    try:
        core = ArchiSensorCore.get_instance()
        return core is not None and core.is_ready()
    except Exception:
        return False

def get_ui_components():
    """Retourne les composants UI pour intégration"""
    try:
        return ArchiSensorUI.get_components()
    except Exception as e:
        print(f"[ARCHI-SENSOR] Erreur récupération UI: {e}")
        return None

# Initialisation automatique
_core_instance = None

def initialize(archiviste_controller, status_queue=None):
    """Initialise l'extension avec les dépendances OGMA"""
    global _core_instance
    try:
        _core_instance = ArchiSensorCore(archiviste_controller, status_queue)
        print("[ARCHI-SENSOR] ✅ Extension initialisée avec succès")
        return True
    except Exception as e:
        print(f"[ARCHI-SENSOR] ❌ Erreur initialisation: {e}")
        return False

def cleanup():
    """Nettoyage et fermeture extension"""
    global _core_instance
    if _core_instance:
        _core_instance.cleanup()
        _core_instance = None
        print("[ARCHI-SENSOR] Extension fermée proprement")