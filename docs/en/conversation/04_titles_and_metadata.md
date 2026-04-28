# Conversation Titles and Metadata

**Verified sources**: `conversations/conversation_utils.py`, `conversations/conversation_index.py`

> French version: [../../fr/conversation/04_titles_and_metadata.md](../../fr/conversation/04_titles_and_metadata.md)

---

## Automatic title generation

`make_title_from_text()` in `conversation_utils.py` generates a title from the first user message. The logic is purely algorithmic (no AI call):

1. Text cleanup (punctuation, special characters)
2. Selection of the first meaningful words
3. Truncation to 60 characters maximum (57 + "..." if exceeded)

This title serves as a readable identifier in the conversation list. It is not automatically regenerated if the user renames it manually.

---

## Metadata in the index

The `data/conversations/index.json` index maintains for each conversation:

| Field | Description |
|---|---|
| `title` | Generated or manually set title |
| `created_at` | Creation timestamp |
| `last_modified` | Last modification timestamp |

These metadata are intentionally lightweight: the index must remain fast to load even with hundreds of conversations.

---

## Renaming

Renaming updates the title in two places: the conversation's JSON file and the index entry. These two operations are performed sequentially. On error, the state may be partially inconsistent between the file and the index — this case is handled by display functions that read the file first.

---

## Memorized conversations

A conversation can be marked as "memorized": the Archivist analyzes it entirely and extracts relevant information for long-term memory. This marking is stored in the conversation's metadata in its JSON file.
