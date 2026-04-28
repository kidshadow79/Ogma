# Magic Phrase Guard

**Verified source**: `magic_phrase_guard.py`

> French version: [../../fr/pipeline/04_magic_phrase_guard.md](../../fr/pipeline/04_magic_phrase_guard.md)

---

## Problem solved

"Magic phrases" are special expressions in the main AI's responses that trigger automatic actions: create a memory, launch introspection, activate the webcam, generate an image. These triggers work by analyzing message content in real time.

A problem arises when loading a historical conversation: old messages containing these phrases would be analyzed again, triggering actions that had already occurred. `magic_phrase_guard.py` prevents this double-triggering.

---

## Dual protection

The module implements two complementary mechanisms:

### 1. Global temporal flag

When a conversation is loaded, `activate_loading_mode()` raises a global flag. While this flag is active, `should_process_magic_phrase()` returns `False` for all messages, regardless of source. The flag automatically drops after 5 seconds (safety net) or as soon as loading is complete via `deactivate_loading_mode_delayed()` (1.5 second delay by default).

### 2. Message metadata

Each message loaded from history receives the metadata `from_history: True`. This permanent marker enables an additional check, even if the temporal flag has already dropped.

---

## API for extensions

All extensions that process magic phrases must call the same function:

```python
if should_process_magic_phrase(current_message, "EXTENSION_NAME"):
    # Process the magic phrase...
else:
    # Ignore — historical message
```

The function accepts the message dictionary and the extension name (for logs). It centralizes the protection logic and guarantees consistent behavior across all extensions.

---

## Built-in statistics

The module maintains counters: total number of blocked triggers, breakdown by protection mechanism (flag vs metadata), list of extensions protected in the session. This data is accessible for diagnostics but is not exposed in the user interface.
