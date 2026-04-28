# Données conversations

**Sources vérifiées** : `data/conversations/` (inspection directe), `conversations/conversation_index.py`

---

## Format des fichiers conversation

Chaque conversation est un fichier JSON nommé `YYYY-MM-DD_HH-MM-SS_xxxx.json` où `xxxx` est un identifiant hexadécimal court (4 caractères). Ce nommage garantit l'ordre chronologique par tri alphabétique.

---

## index.json — Répertoire léger

`index.json` est le répertoire central des conversations. Il ne contient pas le contenu des conversations, seulement leurs métadonnées :

```json
{
  "conversations": {
    "2026-04-04_14-12-08_401c": {
      "id": "2026-04-04_14-12-08_401c",
      "title": "Salutation initiale à Yohan",
      "created": "2026-04-04T14:12:08",
      "updated": "2026-04-04T14:12:24",
      "message_count": 2,
      "auto_title": false,
      "smart_title_pending": false
    }
  }
}
```

Ce fichier est chargé au démarrage via `load_conversation_index()`. Il est mis à jour à chaque création, renommage ou suppression de conversation.

---

## Backups d'index

Des backups horodatés de l'index sont créés automatiquement (`index_backup_YYYYMMDD_HHMMSS.json`). Ces backups permettent de récupérer l'état du répertoire en cas de corruption.

---

## Format interne d'une conversation

Chaque fichier de conversation contient l'historique des messages et les résumés générés. Format v2.2+ : les résumés de conversation sont intégrés directement dans le fichier JSON, permettant à `contextual_recall` d'y accéder sans charger l'intégralité de l'historique.
