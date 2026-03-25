"""
SHIM DE COMPATIBILITÉ
---------------------
Ce fichier assure la compatibilité avec l'ancien emplacement.
Le vrai code a été déplacé dans modules.audio.tts_utils.
"""

from modules.audio.tts_utils import *
from modules.audio.tts_utils import get_conflict_free_tts, speak_safe, set_perception_active
