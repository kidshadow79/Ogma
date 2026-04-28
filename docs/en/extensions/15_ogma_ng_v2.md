# OGMA NG V2 — Extensible Architecture Post-Refactoring

**Verified source**: `extensions/ogma_ng_v2/__init__.py`

> French version: [../../fr/extensions/15_ogma_ng_v2.md](../../fr/extensions/15_ogma_ng_v2.md)

---

## Concept

`ogma_ng.py` is OGMA's main orchestrator file. With the project's organic growth, this file reached a size limit (`7723 lines max`). Any new feature added directly to `ogma_ng.py` would make the file unmanageable.

The `ogma_ng_v2/` extension is the architectural answer: an isolated space for all new post-refactoring features, without touching the main file.

---

## Structure

```
extensions/ogma_ng_v2/
├── features/     → Complete, isolated features
├── shared/       → Code shared between features
└── templates/    → Templates for new features
```

Each feature in `features/` is an autonomous module that:
1. Imports what it needs from `ogma_ng` via `sys.modules`
2. Does not directly modify `ogma_ng.py`
3. Follows the standard OGMA extension singleton pattern

---

## Golden rule

> "ogma_ng.py is FROZEN. Any new feature → extensions/ogma_ng_v2/features/"

This deliberate constraint guarantees that the orchestrator file remains stable and readable, while new features can be developed, tested, and removed without risk of regression.
