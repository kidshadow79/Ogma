# Hologram Projector — OGMA in 3D

**Verified source**: `extensions/hologram_projector/__init__.py`

> French version: [../../fr/extensions/13_hologram_projector.md](../../fr/extensions/13_hologram_projector.md)

---

## Concept

The Hologram Projector broadcasts an animated visualization of OGMA on a mobile phone positioned at the center of a **Pepper's Ghost pyramid**. This simple optical technique (four transparent plexiglass faces) creates the illusion of a floating hologram.

---

## Technical mechanism

The extension starts a WebSocket server on the `/hologram` route of the main NiceGUI server. The mobile phone opens `http://[LAN_IP]:8080/hologram` and receives the AI's state (animated blob) in real time.

The blob reacts to two states:
- **Emotion** (`update_emotion(name, intensity)`): changes the blob color based on the AI's emotional state
- **Speech** (`update_speaking(bool)`): makes the blob vibrate when OGMA speaks via TTS

---

## Integration

A toggle button in the header enables/disables holographic broadcasting. The extension integrates via the standard `get_ui_components()` pattern.

---

## Public API

```python
initialize_hologram()           # Starts the server
is_available() -> bool
update_emotion(name, intensity) # Blob color
update_speaking(bool)           # Blob vibration
get_ui_components() -> dict     # Header button
cleanup()
```
