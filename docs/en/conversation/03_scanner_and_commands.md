# Conversation Scanner and Commands

**Verified sources**: `conversation_scanner.py`, `conversations/conversation_commands.py`

> French version: [../../fr/conversation/03_scanner_and_commands.md](../../fr/conversation/03_scanner_and_commands.md)

---

## Conversation scanner

`search_recent_conversations()` in `conversation_scanner.py` is a lightweight keyword search engine across past conversations. It relies on no index or vector database.

### Behavior

- Scans the **N most recent conversations** (20 by default) in reverse chronological order
- Searches keywords case-insensitively in message content
- Returns matches with a **5-message before/after context** around the matched message
- Sorts results by score (number of keywords found in the same conversation)

### Performance

According to the source file documentation: approximately 50 ms for 20 conversations. This scanner works even without summaries and without an index.

### Return format

Each result contains: conversation identifier, date, matched message index, keywords found, a context excerpt, and a score.

---

## Conversational commands

`handle_conversation_commands()` in `conversations/conversation_commands.py` analyzes user text to detect requests to access archived conversations.

### Detected patterns

The following phrasings trigger conversation loading:
- `"go read the conversation [name]"`
- `"read me the conversation [name]"`
- `"load the conversation [name]"`
- `"open the conversation [name]"`
- `"access the conversation [name]"`

### Behavior after detection

When a pattern is detected, the conversation is loaded and injected as attachment context for the current request. The main AI can then answer questions about that conversation. The request is not blocked: it continues to the AI with the loaded context.

If the requested file doesn't exist, an error notification is emitted and processing stops.
