# Conversation Data

**Verified sources**: `data/conversations/` (direct inspection), `conversations/conversation_index.py`

> French version: [../../fr/data/02_conversations_data.md](../../fr/data/02_conversations_data.md)

---

## Conversation file format

Each conversation is a JSON file named `YYYY-MM-DD_HH-MM-SS_xxxx.json` where `xxxx` is a short hexadecimal identifier (4 characters). This naming guarantees chronological order via alphabetical sorting.

---

## index.json — Lightweight directory

`index.json` is the central directory of conversations. It does not contain conversation content, only metadata:

```json
{
  "conversations": {
    "2026-04-04_14-12-08_401c": {
      "id": "2026-04-04_14-12-08_401c",
      "title": "Initial greeting to Yohan",
      "created": "2026-04-04T14:12:08",
      "updated": "2026-04-04T14:12:24",
      "message_count": 2,
      "auto_title": false,
      "smart_title_pending": false
    }
  }
}
```

This file is loaded at startup via `load_conversation_index()`. It is updated at each conversation creation, rename, or deletion.

---

## Index backups

Timestamped index backups are created automatically (`index_backup_YYYYMMDD_HHMMSS.json`). These backups allow recovering the directory state in case of corruption.

---

## Internal conversation format

Each conversation file contains the message history and generated summaries. Format v2.2+: conversation summaries are integrated directly in the JSON file, allowing `contextual_recall` to access them without loading the entire history.
