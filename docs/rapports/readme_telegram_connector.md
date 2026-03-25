# Extension Telegram Connector — Documentation Exhaustive

**Dossier** : `extensions/telegram_connector/`
**Rôle** : Connecter OGMA à Telegram — reçoit les messages texte, images et vocaux via un bot Telegram, les traite via les pipelines OGMA (IA Principale, STT, TTS, Text2Image), et renvoie les réponses.

---

## Architecture — Fichiers

| Fichier | Classe | Rôle |
|---------|--------|------|
| `__init__.py` | — | API publique + singleton |
| `config.py` | `TelegramConfig` | 17 paramètres de configuration |
| `bot_handler.py` | `TelegramBotHandler` | Gestionnaire Telegram (python-telegram-bot v20+) |
| `message_bridge.py` | `TelegramMessageBridge` | Traitement messages → OGMA |
| `media_handler.py` | `TelegramMediaHandler` | Traitement médias (images, audio) |
| `ui_components.py` | `TelegramUI` | Interface config NiceGUI |

---

## `config.py` — Classe `TelegramConfig`

**17 paramètres** :

| Clé | Défaut | Description |
|-----|--------|-------------|
| `extension_enabled` | `False` | Désactivé par défaut |
| `bot_token` | `""` | Token bot Telegram |
| `allowed_user_ids` | `[]` | IDs Telegram autorisés |
| `auto_add_first_user` | `True` | Premier user auto-ajouté à la liste |
| `max_message_length` | `4096` | Longueur max message Telegram |
| `typing_indicator` | `True` | Envoie `typing...` pendant traitement |
| `voice_response_enabled` | `False` | Répond en vocal (TTS) |
| `voice_response_provider` | `"gtts"` | Moteur TTS pour vocal |
| `image_detection_enabled` | `True` | Activation détection génératon image |
| `web_search_enabled` | `True` | Activation recherche web |
| `max_history_messages` | `10` | Messages historique injectés |
| `response_timeout` | `120` | Timeout réponse IA (secondes) |
| `reconnect_attempts` | `3` | Tentatives reconnexion bot |
| `reconnect_delay` | `5` | Délai entre reconnexions (secondes) |
| `log_conversations` | `True` | Journaliser dans conversations OGMA |
| `markdown_parse_mode` | `"MarkdownV2"` | Mode parsing Telegram |
| `max_voice_duration` | `300` | Durée max audio entrant (secondes) |

**Fichier** : `data/telegram_config.json`

---

## `bot_handler.py` — Classe `TelegramBotHandler`

**Dépendance** : `python-telegram-bot >= 20.0` (asyncio-native)

### 8 handlers enregistrés

| Handler | Filtre | Méthode |
|---------|--------|---------|
| `/start` | `CommandHandler` | `_handle_start_command()` |
| `/help` | `CommandHandler` | `_handle_help_command()` |
| `/clear` | `CommandHandler` | `_handle_clear_command()` |
| `/status` | `CommandHandler` | `_handle_status_command()` |
| Message texte | `filters.TEXT & ~filters.COMMAND` | `_handle_text_message()` |
| Message image | `filters.PHOTO` | `_handle_photo_message()` |
| Message vocal | `filters.VOICE` | `_handle_voice_message()` |
| Document | `filters.Document.IMAGE` | `_handle_document_message()` |

### Méthodes importantes

| Méthode | Description |
|---------|-------------|
| `async start_bot()` | Initialise `Application`, enregistre handlers, démarre polling |
| `async stop_bot()` | Arrête polling proprement |
| `_is_allowed_user(user_id)` | Vérifie `allowed_user_ids` ; si `auto_add_first_user` et liste vide → ajoute |
| `async _send_response(chat_id, text, keyboard)` | Envoie avec split si > `max_message_length` |
| `async _send_voice_response(chat_id, text)` | TTS → OGG → `bot.send_voice()` |
| `async _send_typing(chat_id)` | `ChatAction.TYPING` via bot.send_chat_action() |

### Commande `/status`

Retourne :
```
🤖 OGMA Telegram Status
✅ Bot actif
🧠 Modèle: {model_name}
💾 Mémoire: {stats}
📅 Uptime: {duration}
```

---

## `message_bridge.py` — Classe `TelegramMessageBridge`

**Rôle** : Traduit les messages Telegram en appels OGMA et renvoie les réponses.

### `async process_text_message(user_id, username, text, context)` → `str`

1. `_check_web_search(text)` → si phrase magique web → `web_navigator.process_search()`
2. `_check_image_generation(text)` → si phrase magique t2i → retourne URL image
3. `_get_conversation_history(user_id)` → injecte `max_history_messages` messages
4. `ogma_ng.process_external_message(text, history, user_profile)` → réponse complète
5. `_update_history(user_id, text, response)` → maj historique Telegram interne
6. Retourne réponse nettoyée (`_clean_for_telegram()`)

### `async process_image_message(user_id, username, image_bytes, caption)` → `str`

1. Encode image en base64
2. Si caption contient phrase magique i2i → `Text2ImageManager.image_to_image(base64_image, prompt)`
3. Sinon → analyse vision : `ogma_ng.process_external_message(caption, history, vision_data=base64_image)`
4. Retourne description/réponse

### `async process_voice_message(user_id, username, voice_bytes, duration)` → `str`

1. Vérifie durée ≤ `max_voice_duration`
2. Audio STT : `audio_manager.transcribe_audio_bytes(voice_bytes, format="ogg")`
3. Traite transcription comme texte via `process_text_message()`
4. Si `voice_response_enabled` → génère réponse vocale TTS (retourne (text, audio_bytes))

### Phrases magiques t2i (5 patterns)

| Pattern | Description |
|---------|-------------|
| `"génère une image de"` | Génération directe |
| `"dessine"` | Synonyme génération |
| `"crée une image"` | Synonyme |
| `"illustre"` | Synonyme itération |
| `"imagine visuellement"` | Synonyme créatif |

### Phrases magiques i2i (4 patterns)

| Pattern | Description |
|---------|-------------|
| `"transforme cette image"` | Image-to-image direct |
| `"modifie cette image"` | Modification |
| `"retouche"` | Retouche ciblée |
| `"variation de"` | Variation stylisée |

### `_clean_for_telegram(text)` — nettoyage MarkdownV2

- Échappe caractères spéciaux : `.`, `!`, `(`, `)`, `-`, `+`, `=`, `|`, `{`, `}`, `#`
- Préserve formatage : `*gras*`, `_italique_`, `` `code` ``
- Tronque à `max_message_length` si dépassement

---

## `media_handler.py` — Classe `TelegramMediaHandler`

**Rôle** : Téléchargement + conversion médias Telegram.

### Méthodes

| Méthode | Description |
|---------|-------------|
| `async download_photo(bot, file_id, max_size_mb)` | Télécharge meilleure qualité photo, vérifie taille ≤ max_size_mb (défaut 10MB) |
| `async download_voice(bot, file_id)` | Télécharge OGG voice message |
| `async convert_ogg_to_wav(ogg_bytes)` | Via ffmpeg subprocess (ou pydub si ffmpeg absent) |
| `_resize_if_needed(image_bytes, max_width)` | Redimensionne via PIL si > max_width (défaut 1920px) |
| `image_bytes_to_base64(image_bytes, mime_type)` | Encode pour API vision |

---

## `ui_components.py` — Classe `TelegramUI`

### Interface NiceGUI

| Composant | Description |
|-----------|-------------|
| Bouton header `✈️` | Indicateur connexion (vert/rouge) |
| Modal config | Token bot, allowed_user_ids, tous les 17 paramètres |
| Section Tests | Bouton "Tester la connexion" → `bot.get_me()` |
| Section Logs | 20 derniers messages Telegram reçus |

### Méthodes

| Méthode | Description |
|---------|-------------|
| `get_ui_components()` | Retourne `{header_button}` |
| `open_config_modal()` | Ouvre modal avec valeurs actuelles |
| `save_config(values)` | Sauvegarde + redémarre bot si actif |
| `test_connection()` | Test via `bot_handler.test_connection()` |

---

## `__init__.py` — API Publique

### Singleton : `_telegram_connector : Optional[TelegramConnector]`

### Fonctions exposées

| Fonction | Description |
|----------|-------------|
| `initialize_telegram_connector(chat_controller, archiviste_controller, memory_manager, audio_manager, settings_manager)` | Init complète |
| `is_available()` | `_telegram_connector is not None` |
| `is_connected()` | Bot en écoute polling |
| `connect()` / `disconnect()` | Démarre/arrête polling |
| `get_ui_components()` | Composants header |
| `get_extension_status()` | Dict complet (connected, users_count, messages_received, ...) |
| `cleanup()` | Stop bot proprement |

---

## Sécurité

- Validation `allowed_user_ids` sur chaque message avant tout traitement
- Pas de stockage du `bot_token` en clair dans logs
- `TelegramConfig` sauvegarde avec masquage token dans logs
- Timeout `response_timeout` pour éviter blocages
- Vérification taille médias avant téléchargement

---

## Fichiers de données

| Chemin | Description |
|--------|-------------|
| `data/telegram_config.json` | Configuration complète |
| `data/telegram_history_{user_id}.json` | Historique par utilisateur (max_history_messages) |
