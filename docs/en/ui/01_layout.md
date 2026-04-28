# Global Layout

**Verified sources**: `ogma_ng.py` (main structure), `ogma_headers.py`, `ogma_ui_conversations.py`

> French version: [../../fr/ui/01_layout.md](../../fr/ui/01_layout.md)

---

## NiceGUI structure

OGMA uses the NiceGUI framework for its web interface. The main page is built in `ogma_ng.py` with a three-zone layout:

```
┌─────────────────────────────────────────┐
│  HEADER (AI status, extension buttons)  │
├──────────┬──────────────────────────────┤
│          │                              │
│ SIDEBAR  │     CHAT AREA               │
│ (convs)  │     (messages + input)      │
│          │                              │
└──────────┴──────────────────────────────┘
```

---

## Header

Permanent top bar. Contains status indicators for the 3 AI controllers (Chat, Archivist, Embeddings), buttons for enabled extensions (Cognitive Mirror, Dream Engine, etc.), and the FR/EN language selector. Header content can be enriched dynamically by extensions via their `get_ui_components()` method.

---

## Conversation sidebar

Left panel listing conversations. Can be hidden. Contains controls for creating, renaming, and deleting conversations, as well as a search field. The sidebar is built by `ogma_ui_conversations.py`.

---

## Chat area

Main zone. Displays message history with Markdown rendering. The currently streaming message is updated token by token via a `ui.markdown` widget whose content is replaced. A JavaScript spinner is injected into the DOM for the generation-in-progress indicator.

---

## Input area

Bottom bar containing the `ui.textarea` field (auto-growing), file attachment buttons, user/AI representation toggles, and the send button. The global reference `_input_field` lets other components (audio STT) write to it.
