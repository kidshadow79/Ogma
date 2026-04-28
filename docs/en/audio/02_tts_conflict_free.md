# Conflict-Free TTS

**Verified sources**: `modules/audio/tts_utils.py` (via shim `tts_conflict_free.py`), `ConflictFreeTTSManager`

> French version: [../../fr/audio/02_tts_conflict_free.md](../../fr/audio/02_tts_conflict_free.md)

---

## Problems addressed

TTS in OGMA runs into several technical conflicts:

- **OpenCV vs pygame**: the perception agent (webcam) uses OpenCV, which conflicts with pygame at the audio handle level on Windows
- **NiceGUI**: the framework runs an asyncio event loop that can conflict with synchronous audio operations
- **Threading**: multiple components may want to speak simultaneously (AI streaming + notification + audio response)
- **Windows temporary files**: audio processes keep `.mp3` files open, preventing immediate deletion

`ConflictFreeTTSManager` solves these problems through a dedicated queue architecture.

---

## Queue architecture

A dedicated worker thread consumes TTS requests from `speech_queue`. The main interface never blocks on audio: it sends a request to the queue and continues. The worker processes requests sequentially.

---

## Sentence-by-sentence streaming

During AI response generation, TTS can begin before the response is complete. The system detects sentence endings (`.`, `!`, `?`) in the token stream and queues each sentence as soon as it is complete via `_sentence_queue`. This reduces perceived latency.

---

## Perception management

A `perception_active` flag suspends TTS when the perception agent is active. Webcam and TTS share audio resources exclusively.

---

## File cleanup

Temporary audio files (`ogma_tts_*.mp3`) are stored in `data/audio_temp/`. At startup, leftovers from a previous session are deleted (crash recovery case). On clean shutdown, `atexit` guarantees complete cleanup.
