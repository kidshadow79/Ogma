# 💬 API Conversation Manager - Extraction Complète

**Date**: 2025-11-05
**Modules**: `conversations/`
**Total Méthodes**: 18

---

## 📊 Statistiques Globales

- **Fichiers analysés**: 4
- **Méthodes totales**: 18
- **Méthodes async**: 8
- **Méthodes sync**: 10

---

## 📄 `conversation_utils.py`

**Méthodes**: 2

### Fonctions Module

- `make_conv_id()` - ⚙️ Sync - Ligne 11
- `make_title_from_text()` - ⚙️ Sync - Ligne 30

## 📄 `conversation_index.py`

**Méthodes**: 2

### Fonctions Module

- `load_conversation_index()` - ⚙️ Sync - Ligne 23
- `save_conversation_index()` - ⚙️ Sync - Ligne 46

## 📄 `conversation_commands.py`

**Méthodes**: 1

### Fonctions Module

- `handle_conversation_commands()` - 🔄 Async - Ligne 12

## 📄 `conversation_summarizer.py`

**Méthodes**: 13

### Fonctions Module

- `create_conversation_tool_prompt()` - 🔄 Async - Ligne 388
- `test_summarizer()` - 🔄 Async - Ligne 417

### Classe: `ConversationSummarizer`

- `__init__()` - ⚙️ Sync - Ligne 27
- `set_archiviste()` - ⚙️ Sync - Ligne 34
- `create_summary()` - 🔄 Async - Ligne 147
- `fuse_summaries()` - 🔄 Async - Ligne 184
- `should_summarize()` - ⚙️ Sync - Ligne 211
- `get_summary_range()` - ⚙️ Sync - Ligne 219
- `optimize_conversation_history()` - 🔄 Async - Ligne 225

### Classe: `ConversationArchive`

- `__init__()` - ⚙️ Sync - Ligne 308
- `list_conversations()` - ⚙️ Sync - Ligne 311
- `load_conversation()` - 🔄 Async - Ligne 342
- `search_conversations()` - 🔄 Async - Ligne 356

---

**Généré automatiquement par**: `scripts/extract_conversation_api.py`