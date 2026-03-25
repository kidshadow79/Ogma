"""
Module Audio Unifié
===================
Expose les composants audio principaux avec une API propre.
"""

from .manager import AudioManager
from .wrapper import AudioManagerWrapper, get_audio_manager, reload_stt_config
from .tts_utils import get_conflict_free_tts, speak_safe, set_perception_active, play_audio_file
