# Gestionnaire audio

**Sources vérifiées** : `modules/audio/manager.py` (via shim `audio_manager.py`), `audio_manager_wrapper.py`

---

## Architecture

`audio_manager.py` est un shim de compatibilité qui réexporte depuis `modules/audio/manager.py`. Tout le code réel est dans ce module.

`AudioManager` gère à la fois la reconnaissance vocale (STT — Speech to Text) et la synthèse vocale (TTS — Text to Speech).

---

## Moteurs STT disponibles

La reconnaissance vocale supporte plusieurs backends selon les librairies installées :

| Moteur | Type | Dépendance |
|---|---|---|
| OpenAI Whisper | Cloud | Clé API OpenAI |
| Azure Speech | Cloud | Clé API Azure |
| speech_recognition (Google) | Cloud | `speech_recognition` |
| vosk | Local | `vosk` + modèle |

La détection des moteurs disponibles est automatique au démarrage. Si aucun moteur STT n'est installé, les fonctions vocales restent silencieusement désactivées.

---

## Moteurs TTS disponibles

La synthèse vocale supporte de nombreux backends :

| Moteur | Type | Dépendance |
|---|---|---|
| ElevenLabs | Cloud | Clé API |
| OpenAI TTS | Cloud | Clé API |
| Azure Speech | Cloud | Clé Azure |
| Google Cloud TTS | Cloud | `google-cloud-texttospeech` |
| Edge TTS | Semi-local | `edge-tts` |
| gTTS | Local (online) | `gtts` + connexion |
| pyttsx3 | Local | `pyttsx3` |
| SAPI (Windows) | Local | `win32com` |

---

## Nettoyage du texte

Avant tout passage en TTS, `clean_text_for_tts()` supprime :
- Balises HTML
- Emojis et caractères Unicode hors ASCII étendu
- Formatage Markdown (`**`, `*`, `#`, etc.)
- Blocs de code

Ce nettoyage est nécessaire car les moteurs TTS lisent littéralement tout caractère non filtré.
