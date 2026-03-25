# Audio STT/TTS — Documentation Exhaustive

**Fichier principal** : `audio_manager.py`
**Rôle** : Gestion complète de la reconnaissance vocale (STT) et de la synthèse vocale (TTS) avec support de 8 moteurs TTS et 3 modes STT.

---

## Vue d'ensemble

```
Entrée micro → STT → texte → OGMA → texte → TTS → Audio out
              Whisper API / Local / Vosk
                                         pyttsx3 / SAPI / Google / ElevenLabs /
                                         Azure / gTTS / edge_tts / fish_audio /
                                         cartesia / hume_ai
```

---

## Classe `AudioManager`

**`__init__(settings_manager)`**

| Attribut | Description |
|----------|-------------|
| `tts_engine` | Moteur TTS actif (string) |
| `stt_engine` | Moteur STT actif (string) |
| `_pygame_initialized` | `bool` — pygame mixer initialisé |
| `_pyttsx3_engine` | Instance pyttsx3 (si actif) |
| `_sapi_voice` | Handle COM Windows SAPI (si actif) |
| `_azure_client` | Instance Azure TTS (si actif) |
| `_elevenlabs_client` | Instance ElevenLabs (si actif) |
| `_current_stream` | Stream audio en cours (pour stop) |
| `_is_speaking` | `bool` |
| `_tts_lock` | `threading.Lock()` — évite double lecture |

---

## Moteurs TTS — 8 moteurs

### 1. `system` (pyttsx3 / SAPI Windows)

**Priorité** : Détection automatique OS
- Windows → SAPI 5 (COM via `win32com.client`)
- Linux/Mac → pyttsx3 (espeak backend)

**Paramètres** :
| Clé | Défaut | Description |
|-----|--------|-------------|
| `system_voice` | `""` | Nom voix (ex. `"Microsoft Hortense"`) |
| `system_rate` | `175` | Vitesse (mots/minute) |
| `system_volume` | `1.0` | Volume (0.0-1.0) |

**`speak_system(text)`** :
- SAPI : `voice.Speak(text)` (synchrone, COM thread)
- pyttsx3 : `engine.say(text)` + `engine.runAndWait()`

### 2. `google` (Google Cloud TTS)

**Dépendance** : `google-cloud-texttospeech`

**Paramètres** :
| Clé | Défaut |
|-----|--------|
| `google_tts_language` | `"fr-FR"` |
| `google_tts_voice` | `"fr-FR-Neural2-A"` |
| `google_tts_pitch` | `0.0` |
| `google_tts_speaking_rate` | `1.0` |

**`speak_google(text)`** :
- `texttospeech.TextToSpeechClient()` → `synthesize_speech()`
- Retourne MP3 bytes → joue via pygame

### 3. `elevenlabs` (ElevenLabs)

**Dépendance** : `elevenlabs` SDK

**Paramètres** :
| Clé | Défaut |
|-----|--------|
| `elevenlabs_api_key` | `""` |
| `elevenlabs_voice_id` | `"21m00Tcm4TlvDq8ikWAM"` (Rachel) |
| `elevenlabs_model` | `"eleven_multilingual_v2"` |
| `elevenlabs_stability` | `0.5` |
| `elevenlabs_similarity_boost` | `0.75` |

**`speak_elevenlabs(text)`** :
- `ElevenLabs(api_key=...).text_to_speech.convert()` → audio bytes MP3
- Streaming via generator → pygame play

### 4. `azure` (Microsoft Azure TTS)

**Dépendance** : `azure-cognitiveservices-speech`

**Paramètres** :
| Clé | Défaut |
|-----|--------|
| `azure_tts_key` | `""` |
| `azure_tts_region` | `"westeurope"` |
| `azure_tts_voice` | `"fr-FR-DeniseNeural"` |
| `azure_tts_rate` | `"+0%"` |
| `azure_tts_pitch` | `"+0Hz"` |

**`speak_azure(text)`** :
- SSML generation → `SpeechSynthesizer.speak_ssml_async()`
- Sortie audio directe (pas de fichier intermédiaire)

### 5. `gtts` (Google Text-to-Speech offline/free)

**Dépendance** : `gtts`

**Paramètres** :
| Clé | Défaut |
|-----|--------|
| `gtts_lang` | `"fr"` |
| `gtts_slow` | `False` |
| `gtts_tld` | `"fr"` |

**`speak_gtts(text)`** :
- `gTTS(text=text, lang=lang, slow=slow)` → BytesIO MP3 → pygame

### 6. `edge_tts` (Microsoft Edge TTS — gratuit)

**Dépendance** : `edge-tts`

**Paramètres** :
| Clé | Défaut |
|-----|--------|
| `edge_tts_voice` | `"fr-FR-DeniseNeural"` |
| `edge_tts_rate` | `"+0%"` |
| `edge_tts_volume` | `"+0%"` |
| `edge_tts_pitch` | `"+0Hz"` |

**`async speak_edge_tts(text)`** :
- `edge_tts.Communicate(text, voice)` → MP3 bytes → pygame

### 7. `fish_audio` (Fish Audio)

**Paramètres** :
| Clé | Défaut |
|-----|--------|
| `fish_audio_api_key` | `""` |
| `fish_audio_reference_id` | `""` |
| `fish_audio_speed` | `1.0` |
| `fish_audio_volume` | `1.0` |

**Cache MD5** : Hash texte → fichier `.mp3` en cache (évite regénération si même texte)  
Cache path : `data/uploads/tts_cache/{MD5}.mp3`

**Émotions** : Fish Audio supporte injection de markups émotionnels dans le texte.

### 8. `cartesia` (Cartesia AI)

**Modèle** : `sonic-3`

**Paramètres** :
| Clé | Défaut |
|-----|--------|
| `cartesia_api_key` | `""` |
| `cartesia_voice_id` | `""` |
| `cartesia_speed` | `"normal"` (`"slow"`, `"normal"`, `"fast"`, ou float) |
| `cartesia_emotion` | `[]` | Liste emotions (`"curiosity:high"`, etc.) |

**`speak_cartesia(text)`** :
- `cartesia.Cartesia(api_key=...).tts.bytes()` → PCM/MP3 bytes
- Support émotions via `voice_controls: {speed, emotion}`

### 9. `hume_ai` (Hume AI — Octave TTS)

**Modèles** : `octave-tts-v1` et `octave-tts-v2`

**Paramètres** :
| Clé | Défaut |
|-----|--------|
| `hume_api_key` | `""` |
| `hume_voice_name` | `""` |
| `hume_model` | `"octave-tts-v2"` |

**Description** : TTS expressif haute qualité avec contrôle émotionnel avancé.

---

## Moteurs STT — 3 modes

### Mode 1 : Whisper API (OpenAI)

**`transcribe_audio_file(filepath)`** :
- `openai.Audio.transcriptions.create(model="whisper-1", file=..., language="fr")`
- Supporte : mp3, mp4, mpeg, mpga, m4a, wav, webm

**`transcribe_audio_bytes(audio_bytes, format)`** :
- Wraps en `BytesIO` + faux nom de fichier pour l'API

### Mode 2 : Whisper local (openai-whisper)

**`transcribe_local_whisper(filepath)`** :
- `whisper.load_model("base")` (ou "small", "medium" selon config)
- `model.transcribe(filepath, language="fr")` → `result["text"]`
- GPU si disponible

### Mode 3 : Vosk (offline)

**`transcribe_vosk(audio_bytes)`** :
- `vosk.Model(model_path)` → `KaldiRecognizer`
- Traitement par chunks 4000 bytes
- Retourne texte partiel + final

---

## `stop_speaking()`

**Arrête simultanément TOUS les moteurs actifs** :
```python
def stop_speaking(self):
    self._is_speaking = False
    # Pygame
    if self._pygame_initialized:
        pygame.mixer.stop()
    # pyttsx3
    if self._pyttsx3_engine:
        self._pyttsx3_engine.stop()
    # SAPI
    if self._sapi_voice:
        self._sapi_voice.Skip("Sentence", 1000)  # Skip tout
    # Azure
    if self._azure_client:
        self._azure_client.stop_speaking_async()
    # Streams async (edge_tts, fish_audio, cartesia)
    if self._current_stream:
        self._current_task_cancel = True
```

---

## `clean_text_for_tts(text)` → `str`

Nettoie le texte avant synthèse vocale :
1. **HTML** : retire toutes les balises `<...>`
2. **Markdown** : retire `**`, `*`, `_`, `##`, `###`, backticks, `---`
3. **Émojis** — plages Unicode complètes retirées :
   - `\U0001F000-\U0001FFFF` (émojis principaux)
   - `\U00002600-\U000027FF` (symboles divers)
   - `\U0001F900-\U0001F9FF` (suppléments émojis)
   - `\U00002300-\U000023FF` (symboles techniques)
4. **URLs** : retire `http://...` et `https://...`
5. **Normalisation** : espaces multiples → simple, strip

---

## Intégration dans `ogma_ng.py`

**Flux TTS** :
1. IA génère réponse → `clean_text_for_tts(response)`
2. `audio_manager.speak(cleaned_text)` → route vers moteur configuré
3. Pendant lecture → `_is_speaking = True`
4. Si nouveau message → `stop_speaking()` avant traitement

**Flux STT** :
1. Bouton micro → `start_recording()` → capture audio
2. Relâche → `stop_recording()` → bytes audio
3. `audio_manager.transcribe(audio_bytes)` → texte
4. Texte injecté dans champ message

---

## Fichiers de données

| Chemin | Description |
|--------|-------------|
| `data/settings.json` | Config moteurs TTS/STT (clés API, voix, paramètres) |
| `data/uploads/tts_cache/{MD5}.mp3` | Cache Fish Audio |
| `models/whisper/` | Modèles Whisper local téléchargés |
| `models/vosk/` | Modèles Vosk offline |
