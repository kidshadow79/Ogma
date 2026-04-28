# Header and Status Indicators

**Verified source**: `ogma_headers.py`

> French version: [../../fr/ui/02_headers.md](../../fr/ui/02_headers.md)

---

## Role

The header is the permanent control area of the interface. It displays the state of critical systems and provides access to active extensions.

---

## AI status indicators

Three visual indicators reflect the state of AI controllers:

| Indicator | Controller monitored |
|---|---|
| Chat | Main AI (conversational) |
| Archivist | Analytical AI (memory/enrichment) |
| Embeddings | Vectorization controller |

Each indicator shows the configured backend and turns red when unavailable.

---

## Extension buttons

Extensions register in the header via their `get_ui_components()` method. The header receives a button component and integrates it into its layout. This integration is dynamic: a button only appears if the extension is loaded and available.

Typical button examples:
- Cognitive Mirror button (introspection)
- Dream Engine button (dreaming)
- Daily Journal button
- Organic Planner button

---

## Global variable access

`ogma_headers.py` does not have direct access to `ogma_ng.py`'s global variables. It uses the `_get_global_var(var_name)` helper, which reads variables from `sys.modules['ogma_ng']` at call time. This pattern avoids circular imports.

Similarly, calls to `ogma_ng.py` functions go through `_get_ogma_ng_function(func_name)`, retrieved dynamically from `sys.modules`.

---

## Language selector

A button in the header switches between FR and EN. It calls `set_lang()` from `utils/i18n.py` then forces a page reload via `ui.navigate.reload()` so that all translation strings are updated.
