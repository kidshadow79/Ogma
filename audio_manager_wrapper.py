"""
SHIM DE COMPATIBILITÉ
---------------------
Ce fichier assure la compatibilité avec l'ancien emplacement.
Le vrai code a été déplacé dans modules.audio.wrapper.
"""

from modules.audio.wrapper import *
from modules.audio.wrapper import get_audio_manager, reload_stt_config, AudioManagerWrapper
