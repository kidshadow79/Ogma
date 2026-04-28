# Conversation Sidebar

**Verified source**: `ogma_ui_conversations.py`

> French version: [../../fr/ui/05_conversation_sidebar.md](../../fr/ui/05_conversation_sidebar.md)

---

## Role

The sidebar is the conversation navigation manager. It lists available conversations, allows creating new ones, renaming them, deleting them, and accessing memorization functions.

---

## Message display

The `_message()` function (in `ogma_ui_conversations.py`) handles rendering a message in the chat area. It uses `parse_thinking_format()` and `parse_introspection_format()` from `utils/message_parsers.py` to detect and display differently:
- The AI's internal reflection blocks
- Cognitive Mirror introspection blocks
- Standard text content

Images in messages are handled specifically: underscores in URLs are escaped to prevent NiceGUI's Markdown interpretation.

---

## Multi-selection

The sidebar supports multi-selection of conversations for batch deletion. Selected identifiers are stored in a global set `_selected_conversations`. Batch deletion asks for confirmation before acting.

---

## Conversation memorization

An option in the sidebar lets the user "memorize" an entire conversation. The Archivist analyzes the full content and extracts information for long-term memory. This operation is distinct from automatic magic phrase memorization — it is triggered manually.

---

## Data exchange with ogma_ng

`ogma_ui_conversations.py` cannot directly import `ogma_ng` at initialization. The `_get_ogma()` function performs a lazy import at use time, after `ogma_ng` is fully loaded.
