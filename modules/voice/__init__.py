"""
modules/voice/__init__.py
=========================
Module de conversation vocale pour OGMA

Système de dialogue vocal avec machine à états :
- INACTIVE : Micro off, aucune écoute
- STANDBY : Écoute trigger d'activation uniquement
- LISTENING : Transcription live vers zone de message
- SPEAKING : Luna répond en TTS, écoute trigger interruption

Auteur: Yohan BROCARD
Date: Janvier 2026
"""

from .voice_manager import VoiceManager, VoiceState, initialize_voice_manager, get_voice_manager
from .voice_ui import create_voice_indicator, VoiceIndicator, get_voice_indicator
from .voice_triggers import TriggerDetector

__all__ = [
    'VoiceManager',
    'VoiceState',
    'initialize_voice_manager',
    'get_voice_manager',
    'create_voice_indicator',
    'VoiceIndicator',
    'get_voice_indicator',
    'TriggerDetector',
]
