# Entry Points and Application Lifecycle

**Verified sources**: `launch_ogma.py`, `ogma_ng.py`, `stop_signal.py`

> French version: [../../fr/core/01_entry_points.md](../../fr/core/01_entry_points.md)

---

## Overview

OGMA starts from a single script:

| Script | Usage |
|---|---|
| `launch_ogma.py` | Single entry point — checks the environment, installs missing dependencies, bootstraps data files on first launch. |

This script ultimately calls `run_ogma()` in `ogma_ng.py`.

## `launch_ogma.py` — the full launcher

This script is designed to ensure a smooth first launch on a fresh machine. Before starting the interface, it handles several responsibilities that `start_ogma.py` does not.

### Environment preparation

`launch_ogma.py` configures UTF-8 encoding for the Windows console, loads a `.env` file if `python-dotenv` is installed, and checks that critical dependencies (`nicegui`, `faiss-cpu`, `sqlalchemy`) are present — installing them via `pip` if missing.

### Data bootstrap

On first launch, some configuration files don't exist yet. The script copies them from their default templates:

- `data/settings.example.json` → `data/settings.json`
- `data/persistent_context.default.txt` → `data/persistent_context.txt`
- `data/memory/memories.seed.db` → `data/memory/memories.db` (if the seed exists)

This logic uses an "if target file is absent" condition, so an existing configuration is never overwritten.

### Port selection

By default, the server listens on `0.0.0.0:8080`. These values can be overridden via the `OGMA_HOST` and `OGMA_PORT` environment variables. If the requested port is busy, the script automatically tries the next nine ports (8080 → 8089).

---

---

## What happens in `ogma_ng.py` at startup

### Module loading

When `launch_ogma.py` imports `ogma_ng`, Python executes the module-level code in the file. This is where all OGMA components are imported: AI controllers, memory manager, audio, conversations, extensions. These imports may print messages to the logs — this is intentional and visible, so you can see what is loaded or missing.

Optional extensions are imported defensively (with `try/except`), and availability flags are set. An extension that fails to import does not block startup.

### `run_ogma(host, port)`

This function does three things before starting the web server:

1. **Exposes static folders**: the `static/` folder (CSS, JS, images) and `data/generated_images/` (generated images) are mounted on HTTP routes if these folders exist.
2. **Pre-loads the GGUF model if needed**: if the configuration specifies a `GGUF/llama.cpp` backend, the AI controller is initialized before NiceGUI starts. This avoids blocking the WebSocket while loading a local model that may take several seconds.
3. **Registers cleanup on exit**: via `atexit`, a shutdown routine is registered to release audio, compile the ego, and consolidate the user biography if the process exits cleanly.

The server is then launched with `ui.run()`, with `reload=False` (no hot-reload), `reconnect_timeout=600` (slow or intermittent connections have 10 minutes to reconnect), and a fixed `storage_secret` so NiceGUI sessions persist across restarts.

---

## `main_page()` — the main page

`main_page()` is called by NiceGUI on every connection to `/`. It builds the complete user interface.

Its main role is managing the **user session**: if an active session exists in `app.storage.user`, the user is silently restored. Otherwise, a login box is displayed. This is the mechanism that lets users pick up where they left off after a page reload.

Once the session is established, the page builds the header, sidebar, chat panel, and footer, then launches `_async_awakening()` in the background — the routine that loads memories and prepares the conversation context.

---

## Application shutdown

There are two shutdown paths:

**From the interface**: the close button opens a confirmation dialog. If the user confirms, OGMA runs its shutdown routines (daily journal, ego compilation, cognitive cache pruning) then terminates the process with `os._exit(0)`.

**External interruption**: if the process receives a `Ctrl+C` or is killed cleanly, the `atexit`-registered routine runs. It performs some of the same cleanup operations, but without interface-specific steps (daily journal, for example).

---

## Normal startup flow

```
python launch_ogma.py
  │
  ├── Dependency check (pip install if missing)
  ├── Data file bootstrap (settings.json, etc.)
  ├── Port selection (8080 → 8089)
  │
  └── run_ogma(host, port)
        │
        ├── Mount /static and /generated
        ├── Pre-load GGUF if configured
        ├── Register atexit cleanup
        │
        └── ui.run(...)
              │
              └── Browser connects → main_page()
                    │
                    ├── Session check / restore
                    ├── Interface construction
                    └── _async_awakening() in background
```
