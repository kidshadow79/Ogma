# Modals and Configuration Panels

**Verified sources**: `ogma_modals.py`, `ogma_config_ui.py`

> French version: [../../fr/ui/03_modals.md](../../fr/ui/03_modals.md)

---

## Modal architecture

OGMA uses NiceGUI's dialog system (`ui.dialog()`) for its modal windows. Modals are created on-the-fly at opening time (not pre-instantiated), except in cases where a stable reference is needed.

All modals go through centralized functions in `ogma_modals.py`. Other modules (header, extensions) call these functions via dynamic aliases to avoid circular imports.

---

## Available modals

| Modal | Trigger | Contents |
|---|---|---|
| Model configuration | Header button | Provider, model, parameter selection for each controller |
| Organic Planner | Header button | Calendar events list, add/remove |
| Memories | Admin panel | Display, search, delete memories |
| Conversation editor | Sidebar | Title and summary editing for a conversation |
| File upload | Input button | File drop zone |

---

## Global access pattern

`ogma_modals.py` cannot import directly from `ogma_ng.py` (circular import). It accesses managers via two helpers:

- `_get_settings_manager()` — retrieves `_ensure_settings_manager()` from `sys.modules['ogma_ng']`
- `_get_global_var(var_name)` — generic access to `ogma_ng` global variables

This pattern is identical to `ogma_headers.py`'s.

---

## AI controller configuration

The model configuration panel (`ogma_config_ui.py`) allows independent configuration of the three controllers (Chat, Archivist, Embeddings). For each controller:

- Backend type selection (remote API or local)
- Provider / URL selection
- API key input
- Model selection (list retrieved dynamically via `list_models()`)
- Advanced parameters (temperature, max tokens, context length)
