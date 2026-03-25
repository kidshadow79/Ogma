# 📊 Audio Manager API - Référence Complète

**Généré automatiquement** via extraction AST

---

## 📈 Statistiques

- **Total méthodes publiques** : 38
- **Fonctions module** : 11
- **Méthodes classe** : 27
- **Async** : 17
- **Sync** : 21

---

## 📋 Table des Matières

- [Fonctions Module](#fonctions-module)
- [Classe AudioManager](#classe-audiomanager)

---

## Fonctions Module

### `clean_text_for_tts()`

- **Type** : ⚡ Sync
- **Signature** : `clean_text_for_tts(text)`
- **Ligne** : 84

### `stop_manual_recording()`

- **Type** : ⚡ Sync
- **Signature** : `stop_manual_recording(self)`
- **Ligne** : 367

### `cleanup()`

- **Type** : ⚡ Sync
- **Signature** : `cleanup(self)`
- **Ligne** : 477

### `initialize_tts_sync()`

- **Type** : ⚡ Sync
- **Signature** : `initialize_tts_sync(self)`
- **Ligne** : 611

### `get_available_voices()`

- **Type** : ⚡ Sync
- **Signature** : `get_available_voices(self)`
- **Ligne** : 688

### `set_voice()`

- **Type** : ⚡ Sync
- **Signature** : `set_voice(self, voice_id)`
- **Ligne** : 695

### `stop_speaking()`

- **Type** : ⚡ Sync
- **Signature** : `stop_speaking(self)`
- **Ligne** : 1158

### `set_tts_settings()`

- **Type** : ⚡ Sync
- **Signature** : `set_tts_settings(self, speed, volume, enabled)`
- **Ligne** : 1216

### `configure_tts_engine()`

- **Type** : ⚡ Sync
- **Signature** : `configure_tts_engine(self, engine_type)`
- **Ligne** : 1234

### `get_engine_info()`

- **Type** : ⚡ Sync
- **Signature** : `get_engine_info(self)`
- **Ligne** : 1277

### `test_microphone()`

- **Type** : ⚡ Sync
- **Signature** : `test_microphone()`
- **Ligne** : 1437

## Classe AudioManager

### `AudioManager.__init__()`

- **Type** : ⚡ Sync
- **Signature** : `AudioManager.__init__(self, use_whisper_api, api_key)`
- **Ligne** : 142

### `AudioManager.initialize()`

- **Type** : 🔄 Async
- **Signature** : `AudioManager.initialize(self)`
- **Ligne** : 201

### `AudioManager.start_listening()`

- **Type** : 🔄 Async
- **Signature** : `AudioManager.start_listening(self)`
- **Ligne** : 228

### `AudioManager.stop_listening()`

- **Type** : 🔄 Async
- **Signature** : `AudioManager.stop_listening(self)`
- **Ligne** : 241

### `AudioManager.record_once()`

- **Type** : 🔄 Async
- **Signature** : `AudioManager.record_once(self, timeout)`
- **Ligne** : 246

### `AudioManager.record_manual_control()`

- **Type** : 🔄 Async
- **Signature** : `AudioManager.record_manual_control(self)`
- **Ligne** : 295

### `AudioManager.stop_manual_recording()`

- **Type** : ⚡ Sync
- **Signature** : `AudioManager.stop_manual_recording(self)`
- **Ligne** : 367

### `AudioManager.process_audio_queue()`

- **Type** : 🔄 Async
- **Signature** : `AudioManager.process_audio_queue(self)`
- **Ligne** : 460

### `AudioManager.cleanup()`

- **Type** : ⚡ Sync
- **Signature** : `AudioManager.cleanup(self)`
- **Ligne** : 477

### `AudioManager.transcribe_with_whisper()`

- **Type** : 🔄 Async
- **Signature** : `AudioManager.transcribe_with_whisper(self, audio_data)`
- **Ligne** : 504

### `AudioManager.transcribe_with_api()`

- **Type** : 🔄 Async
- **Signature** : `AudioManager.transcribe_with_api(self, audio_data)`
- **Ligne** : 528

### `AudioManager.initialize_tts()`

- **Type** : 🔄 Async
- **Signature** : `AudioManager.initialize_tts(self)`
- **Ligne** : 534

### `AudioManager.initialize_tts_sync()`

- **Type** : ⚡ Sync
- **Signature** : `AudioManager.initialize_tts_sync(self)`
- **Ligne** : 611

### `AudioManager.get_available_voices()`

- **Type** : ⚡ Sync
- **Signature** : `AudioManager.get_available_voices(self)`
- **Ligne** : 688

### `AudioManager.set_voice()`

- **Type** : ⚡ Sync
- **Signature** : `AudioManager.set_voice(self, voice_id)`
- **Ligne** : 695

### `AudioManager.speak()`

- **Type** : 🔄 Async
- **Signature** : `AudioManager.speak(self, text)`
- **Ligne** : 730

### `AudioManager.speak_system()`

- **Type** : 🔄 Async
- **Signature** : `AudioManager.speak_system(self, text)`
- **Ligne** : 800

### `AudioManager.speak_google_tts()`

- **Type** : 🔄 Async
- **Signature** : `AudioManager.speak_google_tts(self, text, voice_name, api_key)`
- **Ligne** : 911

### `AudioManager.speak_elevenlabs()`

- **Type** : 🔄 Async
- **Signature** : `AudioManager.speak_elevenlabs(self, text, voice_id, api_key)`
- **Ligne** : 1008

### `AudioManager.speak_azure()`

- **Type** : 🔄 Async
- **Signature** : `AudioManager.speak_azure(self, text, voice, api_key, region)`
- **Ligne** : 1097

### `AudioManager.stop_speaking()`

- **Type** : ⚡ Sync
- **Signature** : `AudioManager.stop_speaking(self)`
- **Ligne** : 1158

### `AudioManager.set_tts_settings()`

- **Type** : ⚡ Sync
- **Signature** : `AudioManager.set_tts_settings(self, speed, volume, enabled)`
- **Ligne** : 1216

### `AudioManager.configure_tts_engine()`

- **Type** : ⚡ Sync
- **Signature** : `AudioManager.configure_tts_engine(self, engine_type)`
- **Ligne** : 1234

### `AudioManager.get_engine_info()`

- **Type** : ⚡ Sync
- **Signature** : `AudioManager.get_engine_info(self)`
- **Ligne** : 1277

### `AudioManager.speak_gtts()`

- **Type** : 🔄 Async
- **Signature** : `AudioManager.speak_gtts(self, text, lang)`
- **Ligne** : 1297

### `AudioManager.speak_edge_tts()`

- **Type** : 🔄 Async
- **Signature** : `AudioManager.speak_edge_tts(self, text, voice)`
- **Ligne** : 1351

### `AudioManager.get_edge_tts_voices()`

- **Type** : 🔄 Async
- **Signature** : `AudioManager.get_edge_tts_voices(self, locale_filter)`
- **Ligne** : 1408

---

**Total** : 38 méthodes publiques extraites
