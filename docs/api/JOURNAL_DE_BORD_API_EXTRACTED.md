# 📔 Journal de Bord API - Extracted Methods

**Source**: `extensions/journal_de_bord/`
**Total methods**: 48

## 📊 Statistics

- **Files analyzed**: 5
- **Synchronous methods**: 44
- **Asynchronous methods**: 4
- **Total**: 48

## 📂 Methods by File

### __init__.py (16 methods)

#### `initialize_journal(archiviste_controller, memory_manager, ui_container)`

**Line**: 49

**Description**: Initialise l'extension Journal de Bord avec les dépendances OGMA

**Parameters**: `archiviste_controller, memory_manager, ui_container`

#### `get_journal()`

**Line**: 110

**Description**: Retourne l'instance singleton du Journal de Bord

**Parameters**: `None`

#### `is_available()`

**Line**: 128

**Description**: Vérifie si l'extension est disponible et fonctionnelle

**Parameters**: `None`

#### `is_enabled()`

**Line**: 137

**Description**: Vérifie si l'extension est actuellement activée

**Parameters**: `None`

#### `get_today_context()`

**Line**: 146

**Description**: Raccourci pour obtenir le contexte de la journée actuelle

**Parameters**: `None`

#### `create_manual_entry(conversation_id)` (async)

**Line**: 162

**Description**: Raccourci pour créer une entrée manuelle

**Parameters**: `conversation_id`

#### `search_journal(query)`

**Line**: 187

**Description**: Raccourci pour rechercher dans le journal

**Parameters**: `query`

#### `get_journal_stats()`

**Line**: 209

**Description**: Raccourci pour obtenir les statistiques du journal

**Parameters**: `None`

#### `toggle_journal()`

**Line**: 228

**Description**: Bascule l'état ON/OFF de l'extension

**Parameters**: `None`

#### `get_ui_components()`

**Line**: 243

**Description**: Retourne les composants UI pour intégration dans OGMA

**Parameters**: `None`

#### `open_journal_ui()`

**Line**: 258

**Description**: Ouvre l'interface principale du journal (modal)

**Parameters**: `None`

#### `set_callbacks()`

**Line**: 271

**Description**: Configure les callbacks d'événements du journal

**Parameters**: `None`

#### `cleanup()`

**Line**: 295

**Description**: Nettoyage et fermeture propre de l'extension

**Parameters**: `None`

#### `hook_conversation_start()`

**Line**: 313

**Description**: Hook appelé au début d'une nouvelle conversation
Injecte automatiquement le contexte du jour

**Parameters**: `None`

#### `hook_message_sent()`

**Line**: 333

**Description**: Hook appelé après l'envoi d'un message utilisateur
Peut être utilisé pour le suivi automatique des conversations

**Parameters**: `None`

#### `inject_header_button(header_container)`

**Line**: 343

**Description**: Injecte le bouton journal dans le header OGMA

**Parameters**: `header_container`

### context_provider.py (6 methods)

#### `__init__(json_manager, config)` [ContextProvider]

**Line**: 30

**Description**: Initialise le fournisseur de contexte

**Parameters**: `json_manager, config`

#### `get_recent_context_with_cascade(max_entries)` [ContextProvider]

**Line**: 56

**Description**: Récupère les N dernières conversations, quelle que soit leur date.

**Parameters**: `max_entries`

#### `get_daily_context(target_date, max_entries)` [ContextProvider]

**Line**: 140

**Description**: Génère le contexte journalier pour injection en conversation

**Parameters**: `target_date, max_entries`

#### `get_context_preview(target_date)` [ContextProvider]

**Line**: 188

**Description**: Génère un aperçu du contexte pour l'interface utilisateur

**Parameters**: `target_date`

#### `get_weekly_summary(week_start_date)` [ContextProvider]

**Line**: 239

**Description**: Génère un résumé de la semaine pour contexte étendu

**Parameters**: `week_start_date`

#### `invalidate_cache(target_date)` [ContextProvider]

**Line**: 277

**Description**: Invalide le cache de contexte

**Parameters**: `target_date`

### core_journal.py (11 methods)

#### `__init__(config)` [JournalCore]

**Line**: 41

**Description**: Initialise le moteur principal

**Parameters**: `config`

#### `initialize(archiviste_controller, memory_manager, ui_container)` [JournalCore]

**Line**: 85

**Description**: Initialise l'extension avec les dépendances OGMA

**Parameters**: `archiviste_controller, memory_manager, ui_container`

#### `is_ready()` [JournalCore]

**Line**: 165

**Description**: Vérifie si le journal est prêt à fonctionner

**Parameters**: `None`

#### `is_enabled()` [JournalCore]

**Line**: 172

**Description**: Vérifie si l'extension est activée

**Parameters**: `None`

#### `get_today_context(max_entries)` [JournalCore]

**Line**: 176

**Description**: Retourne le contexte des dernières conversations pour enrichir conversation.

**Parameters**: `max_entries`

#### `create_entry_from_conversation(conversation_id)` (async) [JournalCore]

**Line**: 231

**Description**: Crée une nouvelle entrée de journal via l'Archiviste

**Parameters**: `conversation_id`

#### `search_entries(query)` [JournalCore]

**Line**: 289

**Description**: Recherche dans l'historique du journal

**Parameters**: `query`

#### `get_entries_for_date(target_date)` [JournalCore]

**Line**: 318

**Description**: Récupère toutes les entrées d'une date spécifique

**Parameters**: `target_date`

#### `get_journal_stats()` [JournalCore]

**Line**: 329

**Description**: Retourne les statistiques complètes du journal

**Parameters**: `None`

#### `export_journal(format, date_range)` [JournalCore]

**Line**: 352

**Description**: Exporte les données du journal

**Parameters**: `format, date_range`

#### `cleanup()` [JournalCore]

**Line**: 370

**Description**: Nettoyage et fermeture propre du journal

**Parameters**: `None`

### entry_generator.py (6 methods)

#### `__init__(archiviste_controller, config)` [EntryGenerator]

**Line**: 32

**Description**: Initialise le générateur avec l'Archiviste

**Parameters**: `archiviste_controller, config`

#### `generate_entry(conversation_id)` (async) [EntryGenerator]

**Line**: 78

**Description**: Génère une entrée complète de journal via l'Archiviste

**Parameters**: `conversation_id`

#### `extract_tags_from_text(text)` [EntryGenerator]

**Line**: 142

**Description**: Extraction automatique de tags depuis un texte

**Parameters**: `text`

#### `assess_importance(summary, metadata)` [EntryGenerator]

**Line**: 204

**Description**: Évalue l'importance d'une conversation

**Parameters**: `summary, metadata`

#### `get_generation_stats()` [EntryGenerator]

**Line**: 278

**Description**: Retourne les statistiques de génération

**Parameters**: `None`

#### `handle_magic_phrases(user_input, json_manager)` (async) [EntryGenerator]

**Line**: 697

**Description**: Détecte et traite les phrases magiques de consultation journal

**Parameters**: `user_input, json_manager`

### json_manager.py (9 methods)

#### `__init__(config, data_dir)` [JSONManager]

**Line**: 34

**Description**: Initialise le gestionnaire JSON

**Parameters**: `config, data_dir`

#### `save_entry(entry_data)` [JSONManager]

**Line**: 72

**Description**: Sauvegarde une entrée dans la structure JSON

**Parameters**: `entry_data`

#### `get_day_entries(target_date)` [JSONManager]

**Line**: 167

**Description**: Récupère toutes les entrées d'une date spécifique

**Parameters**: `target_date`

#### `search_entries(query)` [JSONManager]

**Line**: 221

**Description**: Recherche dans l'historique avec filtres

**Parameters**: `query`

#### `get_all_entries_sorted()` [JSONManager]

**Line**: 266

**Description**: Récupère toutes les entrées du journal, triées par timestamp croissant.

**Parameters**: `None`

#### `get_statistics()` [JSONManager]

**Line**: 311

**Description**: Retourne les statistiques complètes du journal

**Parameters**: `None`

#### `flush_caches()` [JSONManager]

**Line**: 328

**Description**: Vide les caches et force la sauvegarde

**Parameters**: `None`

#### `cleanup_old_data(retention_days)` [JSONManager]

**Line**: 334

**Description**: Nettoie les données anciennes selon politique de rétention

**Parameters**: `retention_days`

#### `get_journal_backups()` [JSONManager]

**Line**: 519

**Description**: Récupère la liste des backups disponibles pour le journal

**Parameters**: `None`
