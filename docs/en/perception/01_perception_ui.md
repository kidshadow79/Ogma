# Perception Interface (UI)

**Verified sources**: `ogma_perception.py`, `extensions/perception_ui.py`

> French version: [../../fr/perception/01_perception_ui.md](../../fr/perception/01_perception_ui.md)

---

## Concept

Perception is OGMA's ability to see the world via a webcam. The dedicated interface (`ogma_perception.py`) is a separate NiceGUI page that opens in a **separate popup window** (580×440 px).

This separation is intentional: the real-time video stream and the main chat interface have very different refresh needs. Embedding the webcam in the main window would overload the interface.

---

## Popup window

The popup window saves its position and size in the browser's `localStorage`. On each opening it restores its last position. This behavior is implemented in JavaScript injected at page load.

---

## `perception_ui` singleton

The `extensions/perception_ui.py` extension is a singleton. `ogma_perception.py` retrieves the instance via `get_perception_ui()` to build the interface. If the extension is not available, the page displays an error message.

---

## State in localStorage

The perception activation state (active/inactive) is synchronized in the browser's `localStorage`. This allows the main interface to know whether perception is active without polling.

---

## Interface contents

The perception panel displays:
- The real-time webcam stream
- Agent status (active/inactive)
- Recently detected events
- Capture parameters (resolution, frame rate)
- Available analysis modules (depth, contours)
