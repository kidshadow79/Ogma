# Perception (extension) — OGMA's Eyes

**Verified sources**: `extensions/perception_ui.py`, `extensions/perception_agent.py`

> French version: [../../fr/extensions/17_perception.md](../../fr/extensions/17_perception.md)

---

*This page documents the perception extension as a module. For documentation on the dedicated interface and capture agent, see:*
- *[perception/01_perception_ui.md](../perception/01_perception_ui.md)*
- *[perception/02_perception_agent.md](../perception/02_perception_agent.md)*

---

## Singleton pattern

`extensions/perception_ui.py` exposes the extension via the standard singleton pattern:
- `get_perception_ui()` — returns the unique instance
- `get_ui_components()` — returns the header button for integration in `ogma_headers.py`

## Integration in the pipeline

When perception is active, each message sent by the user triggers a webcam capture (`capture_for_chat()`). The captured image is encoded in base64 and attached to the message as multimodal visual context, before being sent to the main AI.

This injection happens in `logic_callbacks.py` via `get_parallel_context()` which calls the perception extension if available.
