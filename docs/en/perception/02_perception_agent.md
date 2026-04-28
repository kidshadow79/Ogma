# Perception Agent (webcam)

**Verified source**: `extensions/perception_agent.py`

> French version: [../../fr/perception/02_perception_agent.md](../../fr/perception/02_perception_agent.md)

---

## Thread architecture

The perception agent runs in a dedicated thread, separate from the main asyncio loop. This isolation is necessary because OpenCV (webcam capture) is synchronous and blocking.

The agent communicates with the rest of OGMA via two thread-safe queues:
- `event_queue`: detected events (movements, presences, changes)
- `visual_queue`: video frames encoded for the interface

---

## Capture for chat

`capture_for_chat()` is called when a message is sent if perception is active. It captures a frame, encodes it in JPEG base64, and returns an object compatible with the API's multimodal format (type `image_url`). This capture is attached to the message sent to the main AI.

---

## Analysis modules

The agent integrates two optional modules depending on available libraries:

**DepthManager**: analyzes the estimated depth of the scene (object distance). Available if dependencies are installed.

**ContourAnalyzer**: detects contours and shapes in the image. Available independently of DepthManager.

If a module is absent, the agent starts without it with a notification.

---

## TTS integration

When perception starts, `on_perception_start()` is called to suspend TTS. When stopping, `on_perception_stop()` restores TTS. If `TTSPerceptionManager` is not available, empty fallback functions take its place so the agent can still start.

---

## States

| State | Description |
|---|---|
| `inactive` | Thread not started |
| `starting` | Initialization in progress |
| `active` | Capture running |
| `stopping` | Shutdown in progress |
