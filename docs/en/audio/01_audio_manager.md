# Audio Manager

**Verified sources**: `modules/audio/manager.py` (via shim `audio_manager.py`), `audio_manager_wrapper.py`

> French version: [../../fr/audio/01_audio_manager.md](../../fr/audio/01_audio_manager.md)

---

## Architecture

`audio_manager.py` is a compatibility shim that re-exports from `modules/audio/manager.py`. All real code is in that module.

`AudioManager` handles both speech recognition (STT — Speech to Text) and speech synthesis (TTS — Text to Speech).

---

## Available STT engines

Speech recognition supports several backends depending on installed libraries:

| Engine | Type | Dependency |
|---|---|---|
| OpenAI Whisper | Cloud | OpenAI API key |
| Azure Speech | Cloud | Azure API key |
| speech_recognition (Google) | Cloud | `speech_recognition` |
| vosk | Local | `vosk` + model |

Engine detection is automatic at startup. If no STT engine is installed, voice features are silently disabled.

---

## Available TTS engines

Speech synthesis supports many backends:

| Engine | Type | Dependency |
|---|---|---|
| ElevenLabs | Cloud | API key |
| OpenAI TTS | Cloud | API key |
| Azure Speech | Cloud | Azure key |
| Google Cloud TTS | Cloud | `google-cloud-texttospeech` |
| Edge TTS | Semi-local | `edge-tts` |
| gTTS | Local (online) | `gtts` + connection |
| pyttsx3 | Local | `pyttsx3` |
| SAPI (Windows) | Local | `win32com` |

---

## Text cleanup

Before any TTS pass, `clean_text_for_tts()` removes:
- HTML tags
- Emojis and Unicode characters outside extended ASCII
- Markdown formatting (`**`, `*`, `#`, etc.)
- Code blocks

This cleanup is necessary because TTS engines literally read every unfiltered character.
