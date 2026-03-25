# OGMA Telegram Connector

Extension permettant de communiquer avec OGMA via Telegram depuis n'importe où.

## 🚀 Installation

1. **Installer la dépendance:**
   ```bash
   pip install python-telegram-bot
   ```

2. **Créer un bot Telegram:**
   - Ouvre Telegram et cherche `@BotFather`
   - Envoie `/newbot` et suis les instructions
   - Copie le token fourni (format: `7123456789:AAHxyz...`)

3. **Configurer dans OGMA:**
   - Va dans les paramètres OGMA → Extensions → 📱 Telegram
   - Colle ton token
   - Active l'extension
   - Clique sur "Démarrer le bot"

## 📱 Utilisation

### Première connexion
1. Sur Telegram, cherche ton bot par son username
2. Envoie `/start`
3. Ton ID Telegram sera automatiquement enregistré

### Commandes disponibles
- `/start` - Démarrer la conversation
- `/help` - Afficher l'aide
- `/status` - Voir l'état d'OGMA
- `/clear` - Effacer l'historique de conversation
- `/memory` - Voir les souvenirs récents (à venir)

### Fonctionnalités
| Fonction | Description |
|----------|-------------|
| 💬 Texte | Envoie des messages normaux |
| 📷 Images | Envoie une photo pour analyse (vision) |
| 🎤 Vocaux | Envoie un message vocal (transcrit automatiquement) |
| 🎨 Images | Reçois les images générées par OGMA |
| 🔊 Audio | Reçois des réponses vocales (si TTS activé) |

## ⚙️ Configuration

### Paramètres disponibles

```json
{
  "telegram_connector": {
    "enabled": true,
    "bot_token": "7123456789:AAHxyz...",
    "allowed_user_ids": [123456789],
    "auto_start": false,
    "voice_input_enabled": true,
    "voice_output_enabled": true,
    "image_input_enabled": true,
    "image_output_enabled": true,
    "polling_interval": 1.0,
    "max_message_length": 4000,
    "send_typing_indicator": true
  }
}
```

### Sécurité
- **allowed_user_ids**: Liste des IDs Telegram autorisés
- Si la liste est vide, le premier utilisateur à envoyer `/start` sera ajouté automatiquement
- Les utilisateurs non autorisés recevront un message de rejet

## 🔧 Architecture

```
extensions/telegram_connector/
├── __init__.py          # API publique, fonctions d'initialisation
├── config.py            # Gestion configuration depuis settings.json
├── bot_handler.py       # Bot Telegram avec polling
├── message_bridge.py    # Pont entre Telegram et OGMA core
├── media_handler.py     # Gestion images et audio
├── ui_components.py     # Interface paramètres NiceGUI
└── README.md            # Cette documentation
```

## 🛠️ API Publique

```python
from extensions.telegram_connector import (
    initialize_telegram_connector,  # Initialiser avec les contrôleurs OGMA
    start_telegram_bot,             # Démarrer le bot
    stop_telegram_bot,              # Arrêter le bot
    is_telegram_running,            # Vérifier si actif
    send_telegram_notification,     # Envoyer une notification
    get_telegram_status,            # Statut complet
)

# Exemple: envoyer une notification quand OGMA rêve
await send_telegram_notification("🌙 OGMA a fait un rêve...")
```

## 📝 Notes techniques

- **Mode Polling**: Pas besoin de webhook ni de tunnel (ngrok). Le bot interroge les serveurs Telegram régulièrement.
- **Prérequis**: Le PC avec OGMA doit être allumé et le script actif.
- **Pas de streaming**: Telegram ne supporte pas le streaming mot-à-mot. La réponse est envoyée complète.
- **Limite messages**: 4096 caractères max par message Telegram (découpé automatiquement).

## 🐛 Dépannage

| Problème | Solution |
|----------|----------|
| "python-telegram-bot non installé" | `pip install python-telegram-bot` |
| "Token non configuré" | Va dans Paramètres → Telegram et ajoute ton token |
| "Tu n'es pas autorisé" | Ajoute ton ID dans `allowed_user_ids` |
| Bot ne répond pas | Vérifie que OGMA tourne sur le PC |
