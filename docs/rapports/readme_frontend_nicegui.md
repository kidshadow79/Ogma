# Frontend NiceGUI — Documentation Exhaustive

**Fichiers** : `ogma_ng.py`, `ogma_headers.py`, `ogma_modals.py`, `ogma_displays.py`, `ogma_extensions_ui.py`, `ogma_ui_conversations.py`, `ogma_introspection_ui.py`, `ogma_config_ui.py`
**Framework** : [NiceGUI](https://nicegui.io) (Vue.js/Quasar sous le capot, WebSocket-based)

---

## Architecture Frontend

### Découpage modulaire (post-refactoring Nov 2025)

```
ogma_ng.py              ← Orchestrateur principal (7723 lignes max, GELÉ)
├── ogma_headers.py     ← En-tête + indicateurs statut IA
├── ogma_modals.py      ← Toutes les modales/dialogues
├── ogma_displays.py    ← Fonctions affichage + LEDs métacognitives
├── ogma_extensions_ui.py ← Init + inject UI extensions (Journal, Biography)
├── ogma_ui_conversations.py ← Messages, sidebar, conversations (32 fonctions)
├── ogma_introspection_ui.py  ← UI Miroir Cognitif / Introspection
└── ogma_config_ui.py   ← Interfaces de configuration IA
```

**Règle critique** : `ogma_ng.py` est le point d'entrée unique. Tous les modules accèdent aux variables globales via `sys.modules.get('ogma_ng')` pour éviter les imports circulaires.

---

## Point d'entrée — `main_page()`

**Déclenché par** : `@ui.page('/')` → `index()` → `main_page()`

### Flux d'initialisation (séquentiel)

```
main_page()
├── Vérification session → _show_login_popup() si absent
├── _link_styles()              ← CSS via <link> + <style> inline
├── ui.dark_mode()              ← Mode sombre global
├── _header()                   ← Barre de titre + indicateurs
├── Overlay de chargement       ← Spinner "Réveil d'OGMA..."
├── Zone de chat (_conv_area, _chat_inner)
├── _sidebar()                  ← Liste conversations
├── Zone de saisie + boutons
└── asyncio.create_task(_init_app_async())  ← Init async en arrière-plan
```

### Overlay de chargement

Notification flottante bas-droite avec :
- Spinner `ui.spinner('dots')` blanc
- Message évolutif : `"Réveil d'OGMA..."` → `"Prêt !"` (disparaît après init)
- Statuts : `default` (violet-gradient) → `success` (vert) → `error` (rouge)
- Animation CSS : `slideInUp` (entrée) + `fadeOut` (sortie)

---

## `ogma_headers.py` — `_header()`

### Structure HTML

```
.app-header
└── .header-content (flex, width: 100%)
    ├── .header-title-container  ← Conteneur titre (variable globale _header_container)
    ├── Indicateurs IA (LEDs statut — centre)
    └── Boutons extensions (droite)
```

### Indicateurs de statut IA (3 dots colorés)

| Indicateur | Variable | Description |
|------------|----------|-------------|
| Chat dot | `_ia_status_indicators["chat"]` | IA Principale (vert/rouge/orange) |
| Archiviste dot | `_ia_status_indicators["archiviste"]` | Archiviste (vert/rouge/orange) |
| Embedding dot | `_ia_status_indicators["embedding"]` | Embeddings (vert/rouge/orange) |

**`_status_dot(initial='#dc2626')`** — délègue vers `ogma_displays._status_dot()` :
- Crée `div` rond 12px (classe `status-dot cyber-dot`)
- Initial rouge → vert quand contrôleur prêt

### Boutons extensions dans le header

Injectés dynamiquement via `get_ui_components()` de chaque extension :
- `📔` Journal de Bord
- `📖` Biographie Profil
- `🧠` Miroir Cognitif
- `📋` Organic Planner
- `🌙` Dream Engine
- `✈️` Telegram Connector
- `🌐` Web Navigator
- `🖼️` Text2Image
- `👁️` Perception/Vision

### Accès variables globales `ogma_ng`

Pattern utilisé partout dans les modules :
```python
def _get_global_var(var_name, default=None):
    import sys
    ogma_ng = sys.modules.get('ogma_ng')
    if ogma_ng and hasattr(ogma_ng, var_name):
        return getattr(ogma_ng, var_name)
    return default
```

---

## `ogma_displays.py` — Affichage et LEDs

### `_update_led_gauges(data)`

Met à jour les 9 jauges LED du panneau métacognitif (Capability Advisor) via JavaScript :

```python
data = {
    'autocensure': 0,      # LED rouge (0-5)
    'saturation': 0,       # LED orange
    'stimulation': 0,      # LED cyan
    'affinity': 4,         # LED rose
    'disorientation': 0,   # LED jaune
    'freedom': 0,          # LED verte
    'alignment': 0,        # LED bleue
    ...
}
```

**Injection JavaScript** : `ui.run_javascript()` avec sélection DOM `getElementById('{name}-led-{i}')`, toggle classes CSS `led-active` + `pulse`.

### `_status_dot(initial)`

Crée indicateur rond coloré avec classes `status-dot cyber-dot`.

### Effet "Cyber Scan Overlay"

Ligne laser horizontale qui traverse l'écran périodiquement :
- ID : `#cyber-scan-line`
- Animation : `global-scan` (de top:-2px à top:100vh)
- Couleur : `rgba(0,212,245,0.8)` (cyan)
- Activée/désactivée via settings

---

## `ogma_modals.py` — Modales

### Constantes

```python
REMOTE_PROVIDERS = ['OpenAI', 'Mistral', 'Anthropic', 'Google', 'GROK', 'OpenRouter', 'AIHorde']
LOCAL_BACKENDS = ['Ollama', 'GGUF', 'KoboldCpp']
EMBED_SUPPORTED_PROVIDERS = ['OpenAI', 'Mistral', 'Google', 'OpenRouter']
```

### Modales principales

| Fonction | Description |
|----------|-------------|
| `_show_settings_dialog()` | Configuration complète : providers, modèles, clés API, temperature, max_tokens, context_length pour les 3 contrôleurs |
| `_show_organic_planner_dialog()` | Agenda + charge mentale → `organic_planner.get_all_events()` |
| `_show_memory_modal()` | Recherche + affichage mémoires SQLite/FAISS, stats, suppression |
| `_show_ego_modal()` | Visualisation flags ego compilés depuis `data/ego_compiled.json` |
| `_show_conversation_summary_modal()` | Résumé conversation courante |
| `_show_upload_dialog()` | Dialog upload fichier avec options vision avancée |
| `_show_login_popup()` | Popup identité utilisateur (prénom, stocké `app.storage.user`) |
| `_show_profile_modal()` | Gestion profils utilisateur (ProfileManager) |

### Structure modale standard

```python
with ui.dialog().classes('settings-dialog') as dialog, \
     ui.card().classes('settings-card').style('min-width: 500px; max-width: 800px;'):
    with ui.column().classes('w-full gap-4'):
        # Header : icône + titre + bouton close
        with ui.row().classes('w-full items-center justify-between'):
            ui.icon('X', size='24px').style('color: var(--accent-primary);')
            ui.label('Titre modale').classes('text-xl font-bold')
            ui.button(icon='close', on_click=dialog.close).props('flat round')
        ui.separator().style('background: rgba(255,255,255,0.1);')
        # Contenu
dialog.open()
```

---

## `ogma_ui_conversations.py` — Messages et Conversations (32 fonctions)

### Affichage messages

| Fonction | Description |
|----------|-------------|
| `_message(role, content, metadata)` | Crée bulle de message (user/assistant/system) avec formatage Markdown |
| `_create_streaming_message()` | Crée bulle vide pour streaming — retourne containerref |
| `_finalize_streaming_message(container, full_text, metadata)` | Remplace contenu streamed par version finale formatée |
| `_filter_missing_images(content)` | Retire références images manquantes du HTML |

### Format messages

- **User** : bulle droite, couleur accent
- **Assistant** : bulle gauche, fond sombre, Markdown rendu (bold, italic, code, listes)
- **System** : bandeau subtil, italique, fond transparent
- **Streaming** : curseur clignotant pendant génération → remplacé par texte final

### Sidebar conversations

| Fonction | Description |
|----------|-------------|
| `_sidebar()` | Colonne gauche : liste conversations avec titres + dates |
| `_load_conversation_index()` | Charge `data/conversations/index.json` (liste conversations) |
| `_save_conversation_index()` | Sauvegarde index JSON |
| `_new_conversation()` | Crée nouvelle conversation + vide `_chat_inner` |
| `_load_conversation(conv_id)` | Charge historique + `_render_full_history()` |
| `_persist_conversation()` | Sauvegarde conversation courante en JSON |

### Titres intelligents

| Fonction | Description |
|----------|-------------|
| `_maybe_update_conv_title()` | Décide si titre doit être regénéré (après 3 messages) |
| `_schedule_smart_title_generation()` | Lance génération en background (ui.timer oneshot) |
| `_generate_smart_title_async()` | Appelle Archiviste : résumé 5 mots max |
| `_regenerate_title_manual()` | Bouton regénération manuelle dans sidebar |

### Mémorisation conversations

| Fonction | Description |
|----------|-------------|
| `_generate_conversation_summary()` | Archiviste résume conversation complète |
| `_memorize_conversation()` | Sauvegarde résumé dans MemoryManager |
| `_mark_conversation_memorized(conv_id)` | Flag `memorized: true` dans index |
| `_is_conversation_memorized(conv_id)` | Vérifie flag |
| `_count_memorized_conversations()` | Stats |
| `_delete_memorized_conversation(conv_id)` | Supprime du MemoryManager |

### Interface édition messages

| Fonction | Description |
|----------|-------------|
| `_create_edit_interface(message_el, content)` | Inline edit d'un message existant |
| `load_message_for_edit(message_id)` | Charge contenu pour édition |
| `_edit_summary_popup(conv_id)` | Popup édition résumé de conversation |

### Affichage spécialisé

| Fonction | Description |
|----------|-------------|
| `_display_conversation_as_attachment(conv_id)` | Conversation précédente comme pièce jointe |
| `_display_archived_conversation(filepath)` | Conversation archivée (JSON gzip) |
| `_display_search_results(results)` | Résultats recherche web formatés dans chat |
| `_display_conversation_summary(summary)` | Bloc résumé visuel |
| `_display_available_conversations(convs)` | Liste conversations pour sélection |

---

## `ogma_extensions_ui.py` — Initialisation Extensions UI

### `set_globals(settings_manager, memory_manager, chat_controller, archiviste_controller, status_queue)`

Appelé par `ogma_ng.py` après init des managers — injecte les dépendances dans le module.

### `_initialize_biography_extension()`

1. Vérifie `BIOGRAPHY_EXTENSION_AVAILABLE`
2. Appelle `initialize_biography_extension(settings_manager, memory_manager, chat_controller)`
3. `get_biography_ui()` → instance UI
4. Met `_biography_available = True`

### `_initialize_journal_extension()`

1. Vérifie disponibilité
2. Init via `initialize_journal_de_bord()`
3. `_inject_journal_header_button()` → injecte bouton dans header

### Boutons header inline

**`_create_header_journal_button_inline(container)`** → Bouton `📔` dans container donné  
**`_create_header_biography_button_inline(container)`** → Bouton `📖` dans container donné

---

## Configuration NiceGUI `ui.run()`

```python
ui.run(
    title='OGMA - IA Conversationnelle',
    host=host,             # Défaut 0.0.0.0
    port=port,             # Défaut 8080 (retry 8081-8090)
    reload=False,          # Pas de rechargement automatique (prod)
    show=True,             # Ouvre navigateur au démarrage
    dark=True,             # Mode sombre global
    reconnect_timeout=600.0,     # 10 minutes (réponses IA longues)
    storage_secret='ogma-session-secret-v1',  # Session stable
    binding_refresh_interval=0.3,             # 300ms refresh WebSocket
    favicon='🤖'
)
```

### Routes

| Route | Handler | Description |
|-------|---------|-------------|
| `/` | `index()` → `main_page()` | Interface principale |
| `/perception` | `@ui.page('/perception')` | Page dédiée perception webcam |
| `/static/*` | `app.add_static_files()` | Assets CSS/JS/images |
| `/generated/*` | `app.add_static_files()` | Images générées par t2i |

### Hooks WebSocket

```python
@app.on_connect
async def on_client_connect(client): ...    # Log + track_client_activity()

@app.on_disconnect
async def on_client_disconnect(client): ... # Log déconnexion
```

---

## Gestion des erreurs UI

### `safe_ui_operation(operation_func, *args, **kwargs)`

Wrapper global anti-crash NiceGUI :
- Intercepte erreurs liées à "deleted", "client", "belongs" (client déconnecté)
- Log `[UI-PROTECTION]` sans crash
- Propage les vraies erreurs

### `nicegui_error_handler.py`

Module séparé d'initialisation :
- `initialize_nicegui_error_handling()` → configure gestionnaire global
- `track_client_activity(client_id)` → appelé à chaque connexion

---

## Thème CSS

### Variables CSS principales

```css
--accent-primary: #667eea (violet-bleu gradient)
--background-dark: #0d0d1a
--surface-dark: #111827
--border-subtle: rgba(255,255,255,0.1)
```

### Classes utilitaires

| Classe | Description |
|--------|-------------|
| `.app-header` | Barre en-tête fixe, z-index élevé |
| `.settings-dialog` | Modale centrée avec blur backdrop |
| `.settings-card` | Carte modale (fond sombre, border-radius) |
| `.cyber-dot` | Pulsation CSS pour indicateurs statut |
| `.status-dot` | Rond coloré 12px statut IA |
| `.led-active` | LED allumée (Capability Advisor) |
| `pulse` | Animation clignotement LED |

### Injection CSS

- `_link_styles()` → `ui.add_head_html('<link rel="stylesheet" ...>')` + `ui.add_head_html('<style>...')`
- CSS inliné directement dans `ui.element().style(...)` pour composants dynamiques

---

## Variables globales clés dans `ogma_ng.py`

| Variable | Type | Description |
|----------|------|-------------|
| `_conv_area` | NiceGUI element | Zone scroll conversations |
| `_chat_inner` | NiceGUI element | Conteneur interne messages |
| `_header_container` | NiceGUI element | Container titre en-tête |
| `_ia_status_indicators` | `dict` | Refs dots statut Chat/Archiviste/Embedding |
| `_current_conversation_id` | `str` | UUID conversation active |
| `_conversation_history` | `list` | Messages en cours (format OpenAI) |
| `_current_user_name` | `str` | Prénom utilisateur connecté |
| `_user_authenticated` | `bool` | Session validée |
| `_status_queue` | `queue.Queue` | File messages statut async → UI |

---

## Session utilisateur

**Stockage** : `app.storage.user` (NiceGUI session storage, persistant onglet)

**Clé** : `'ogma_user'` → `{name: "Yohan", ..."}`

**Flux** :
1. `main_page()` lit `app.storage.user.get('ogma_user')`
2. Si présent → auto-login silencieux (`_current_user_name = stored_user['name']`)
3. Si absent → `_show_login_popup()` → champ prénom → stocké dans `app.storage.user`

---

## Fichiers statiques

| Dossier | Route | Contenu |
|---------|-------|---------|
| `static/` | `/static/` | CSS custom, fonts, icônes |
| `data/generated_images/` | `/generated/` | Images t2i (évite encodage base64 lourd) |
