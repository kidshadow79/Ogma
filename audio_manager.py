"""
SHIM DE COMPATIBILITÉ
---------------------
Ce fichier assure la compatibilité avec l'ancien emplacement.
Le vrai code a été déplacé dans modules.audio.manager.
"""

from modules.audio.manager import *
# Expose explicitement les classes principales si nécessaire
from modules.audio.manager import AudioManager, clean_text_for_tts
