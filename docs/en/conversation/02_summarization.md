# Progressive Conversation Summarization

**Verified source**: `conversation_summarizer.py`

> French version: [../../fr/conversation/02_summarization.md](../../fr/conversation/02_summarization.md)

---

## Problem solved

Language models have a limited context window. A long conversation with hundreds of messages cannot be transmitted in full to the AI on every request. Yet erasing old messages breaks continuity.

`ConversationSummarizer` compresses old messages into dense summaries, allowing the AI to maintain historical context without exceeding the context window.

---

## Trigger

Summarization triggers when the number of unsummarized messages exceeds **30**. The Archivist is then called to produce a summary of each block of **10 messages**. After summarization, the **20 most recent messages** are kept verbatim — they are not summarized.

These thresholds are configured in the constructor:
- `summary_interval = 10` — summarized block size
- `summarize_trigger = 30` — trigger threshold
- `min_recent_messages = 20` — recent messages preserved verbatim

---

## Progressive merging

When multiple summary blocks accumulate, the Archivist can merge them into a summary-of-summaries. This prevents the summary list from growing indefinitely. Merging preserves essential information and emotional context per the Archivist's instructions.

---

## Dual persistence

**Session RAM cache**: summaries are kept in memory during the active session via `_session_cache`. Regenerating an already-computed summary is avoided.

**JSON persistence**: summaries are saved in the conversation file under the `summaries` key. On every conversation reload, summaries are restored from the JSON.

---

## Backend usage

The main AI does not receive the complete history on a call. It receives summaries of old messages (compressed) + the 20 most recent messages verbatim. The interface display always shows the full uncompressed history.
