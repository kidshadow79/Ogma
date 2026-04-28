# Application Orchestration and Lazy Initialization

**Verified sources**: `ogma_ng.py`, `modules/ogma_core/globals.py`, `modules/ogma_core/controllers.py`, `modules/ogma_core/extensions_loader.py`, `modules/ogma_core/__init__.py`

> French version: [../../fr/core/02_app_orchestration.md](../../fr/core/02_app_orchestration.md)

---

## The problem this system solves

OGMA has many heavy components: one or more AI models, a SQLite + FAISS memory database, an audio manager, extensions. Initializing them all at startup would block the interface for several seconds — or even tens of seconds if a local (GGUF) model needs to be loaded into memory.

The solution is **lazy initialization**: no component is created until it is requested. The interface is available immediately. Components initialize in the background, in the order they are needed.

---

## Architecture: three layers

### 1. Global variables — `modules/ogma_core/globals.py`

All references to active components are stored in a single module (`globals.py`). It holds AI controllers, the memory manager, audio, extensions, conversation history, UI widget references, and internal application states.

This file does nothing by itself: it is a state registry. Every variable starts as `None` and is populated as initialization proceeds.

Access to these variables goes through getter/setter functions (e.g. `get_chat_history()`, `set_current_conversation_id()`), making it possible to read and modify global state without directly importing the variables — avoiding circular import issues between modules.

### 2. Initializers — `modules/ogma_core/controllers.py`

This file contains `ensure_*()` functions — one per component. Each function checks whether the component is already initialized; if not, it creates it and stores it in `globals.py`. Subsequent calls simply return the existing component.

```
ensure_settings_manager()      → SettingsManager (reads data/settings.json)
ensure_backends()              → APIManager, OllamaManager, GGUFManager, KoboldManager
ensure_chat_controller()       → AIController (main AI)
ensure_archiviste_controller() → AIController (Archivist)
ensure_embedding_controller()  → EmbeddingController (memory vectors)
ensure_memory_manager()        → MemoryManager (SQLite + FAISS)
ensure_audio_manager()         → STT/TTS manager
ensure_cognitive_mirror()      → Cognitive Mirror extension
ensure_temporal_guardian()     → Temporal Guardian extension
... (one function per major extension)
```

In `ogma_ng.py`, these functions are re-exposed under `_ensure_*()` names (with an underscore), indicating they are internal to the main application.

### 3. Extension loader — `modules/ogma_core/extensions_loader.py`

A separate mechanism handles extension availability. The `_check_extension_available()` function attempts to import each extension and caches the result (available/unavailable). If the import fails, the extension is marked unavailable but the application continues.

This cache avoids retrying a doomed import on every call. The `get_available_extensions()` function returns the list of all extensions that could be imported.

---

## The asynchronous awakening — `_async_awakening()`

This is the initialization sequence that fires just after the interface is visible. It is launched as a background task (`asyncio.create_task`) from `main_page()`, while the user can already see the chat screen.

The awakening proceeds in **successive waves**, each preceded by a status message visible in the interface:

| Wave | What initializes |
|---|---|
| 1 | Settings (`settings.json`) |
| 2 | Main AI controller (via `asyncio.to_thread` if GGUF to avoid blocking) |
| 3 | Archivist controller |
| 4 | SQLite + FAISS memory |
| 5 | Audio and voice |
| 6 | Cognitive extensions: Daily Journal, Biography, Dream Engine, Cognitive Flow, Cognitive Cache, Telegram... |

Potentially slow operations (loading a GGUF model) are executed in a separate thread via `asyncio.to_thread()`, to avoid blocking the NiceGUI event loop.

Each step is wrapped in an independent `try/except`: an extension that crashes during initialization does not interrupt subsequent waves.

---

## Full sequence from browser open

```
Browser connects → main_page()
    │
    ├── Session check (login or restore)
    ├── Interface construction (header, sidebar, chat, footer)
    ├── Display awakening notification
    │
    └── asyncio.create_task(_async_awakening())
          │
          ├── Wave 1: Settings
          ├── Wave 2: Main AI       (separate thread if GGUF)
          ├── Wave 3: Archivist     (separate thread if GGUF)
          ├── Wave 4: FAISS/SQLite memory
          ├── Wave 5: Audio + Voice
          └── Wave 6: Cognitive extensions (Journal, Bio, Dream, Flow, Cache, Telegram...)
                      → each extension: independent try/except
```

---

## Why split into modules?

`ogma_ng.py` has a long history: it was monolithic (over 8,000 lines). The `modules/ogma_core/` folder represents a refactoring phase (December 2025) that extracts the most cross-cutting responsibilities: global state, initializers, extension loading.

`ogma_ng.py` retains `_ensure_*()` functions that are simple redirections to the centralized module's functions — maintaining compatibility with existing code while delegating the real logic to `modules/ogma_core/`.
