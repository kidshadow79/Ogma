# Backend Communication and AI Status

**Verified sources**: `backend/backend_communication.py`, `backend/ia_status.py`

> French version: [../../fr/backend/01_backend_communication.md](../../fr/backend/01_backend_communication.md)

---

## Context

These two modules were extracted from `ogma_ng.py` during a November 2025 refactoring. They group the network diagnostic operations toward AI backends, used from the configuration interface.

---

## `backend_communication.py` — list and test

This module exposes two functions used by the configuration interface to help users choose and verify their backend:

**`list_models(backend_type, ...)`**: queries the selected backend to get the list of available models. For API providers, this makes an authenticated network call. For Ollama, it queries the local server. For GGUF, it lists the `.gguf` files present in the `models/` folder. On error, returns an empty list and an error message, never an exception.

**`test_connection(backend_type, ...)`**: verifies that the connection to the backend is functional. Returns a `(success: bool, message: str)` tuple. This feeds the status indicators visible in the configuration interface.

These functions receive managers as parameters rather than accessing them globally — making them independent of OGMA's initialization state and easier to test.

---

## `ia_status.py` — three-AI dashboard

`check_global_ia_status()` builds a summary of the state of the three AI controllers (main AI, Archivist, Embeddings). For each controller, it reads the corresponding section of `settings.json` (`chat_api`, `reasoning_api`, `embedding_api`) and determines:

- whether a model is configured (`configured: bool`)
- whether the connection is operational (`available: bool`)
- the name of the active model (`model_name: str`)
- the backend type (`backend: str`)

This status is displayed in the interface to give the user an overview of what is working. It is recalculated on demand, not in real time.
