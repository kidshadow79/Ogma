# Audio and TTS Configuration

**Verified sources**: `ogma_tts_config.py`, `tts_perception_manager.py`

> French version: [../../fr/audio/03_audio_ui_config.md](../../fr/audio/03_audio_ui_config.md)

---

## TTS configuration interface

`ogma_tts_config.py` exposes a NiceGUI configuration panel for TTS engines. It allows configuring:

- The active engine (System/pyttsx3, Google Cloud, ElevenLabs, Azure, gTTS, Edge TTS)
- Engine-specific parameters (API key, voice, speed, volume)
- An audio test button to validate the configuration

Configuration is persisted in `settings.json` under the `tts` key. It is applied to `AudioManager` via `_apply_tts_config_from_settings()` from `ogma_ng`.

---

## TTS/Perception conflict manager

`TTSPerceptionManager` resolves the conflict between TTS and the perception agent (webcam) at the configuration level. When perception activates:

1. The current TTS configuration is saved in memory
2. TTS is disabled in `settings.json`
3. `AudioManager` is reloaded with the modified configuration

When perception deactivates, the original TTS configuration is restored.

This mechanism complements the `perception_active` flag in `ConflictFreeTTSManager` (which operates at the TTS queue level). Both protections work independently.

---

## Persistent parameters

The TTS configuration in `settings.json` contains: the selected engine, API keys per service, voice identifier, speech rate, and volume. These parameters are reloaded at application startup.
