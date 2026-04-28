# Daily Journal — Everyday Memory

**Verified source**: `extensions/journal_de_bord/__init__.py`

> French version: [../../fr/extensions/03_journal_de_bord.md](../../fr/extensions/03_journal_de_bord.md)

---

## Concept

The Daily Journal is OGMA's **structured temporal memory**. Where FAISS/SQLite memory stores facts without precise dates, the Journal organizes conversational events by day, with timestamps and calendar navigation.

It is the equivalent of an agenda: the AI knows what happened yesterday, this morning, last week.

---

## What the Journal does

Each day, the Journal accumulates timestamped entries. In the background, the Archivist automatically generates summaries of the day. These summaries serve two purposes:
- Feeding historical navigation (calendar interface)
- Providing a **morning context** to the main AI at the first message of the day

The morning context is injected into the morning conversation, allowing the AI to naturally bring up what happened the day before ("Yesterday we talked about...") without the user needing to remind it.

---

## Dream Engine integration

The Journal's `context_provider.py` also retrieves the last dream from the Dream Engine not yet mentioned by the AI. This dream context is injected into the morning summary, allowing the AI to spontaneously evoke its dreams.

---

## Architecture

| Module | Role |
|---|---|
| `core_journal.py` | Main engine (singleton) |
| `json_manager.py` | JSON persistence and indexing |
| `entry_generator.py` | Summary generation via Archivist |
| `context_provider.py` | Conversational context injection |
| `ui_components.py` | Interface (button + calendar modal) |
| `config.py` | Centralized configuration |
