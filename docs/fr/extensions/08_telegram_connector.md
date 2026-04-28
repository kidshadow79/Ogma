# Telegram Connector — OGMA dans votre poche

**Source vérifiée** : `extensions/telegram_connector/__init__.py`

---

## Concept

Le Telegram Connector ouvre un canal de communication entre OGMA et l'application Telegram. L'utilisateur peut converser avec l'IA principale depuis son téléphone, envoyer des messages vocaux et des images, sans ouvrir l'interface web.

---

## Formats supportés

- **Texte** : messages classiques, dialogue complet
- **Images** : envoi d'images pour analyse par l'IA (si vision activée)
- **Messages vocaux** : transcription STT puis traitement normal

---

## Architecture

L'extension démarre un bot Telegram qui écoute les messages entrants. Chaque message est traduit en requête OGMA standard (même pipeline que l'interface web), puis la réponse est renvoyée via Telegram.

Les notifications OGMA (alertes, rappels du Organic Planner) peuvent également être poussées vers Telegram via `send_telegram_notification()`.

---

## API publique

```python
from extensions.telegram_connector import (
    initialize_telegram_connector,
    start_telegram_bot,
    stop_telegram_bot,
    is_telegram_running,
    send_telegram_notification,
)
```
