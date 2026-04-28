# Telegram Connector — OGMA in Your Pocket

**Verified source**: `extensions/telegram_connector/__init__.py`

> French version: [../../fr/extensions/08_telegram_connector.md](../../fr/extensions/08_telegram_connector.md)

---

## Concept

The Telegram Connector opens a communication channel between OGMA and the Telegram app. The user can converse with the main AI from their phone, send voice messages and images, without opening the web interface.

---

## Supported formats

- **Text**: classic messages, full dialogue
- **Images**: sending images for AI analysis (if vision is enabled)
- **Voice messages**: STT transcription then normal processing

---

## Architecture

The extension starts a Telegram bot that listens for incoming messages. Each message is translated into a standard OGMA request (same pipeline as the web interface), then the response is sent back via Telegram.

OGMA notifications (alerts, Organic Planner reminders) can also be pushed to Telegram via `send_telegram_notification()`.

---

## Public API

```python
from extensions.telegram_connector import (
    initialize_telegram_connector,
    start_telegram_bot,
    stop_telegram_bot,
    is_telegram_running,
    send_telegram_notification,
)
```
