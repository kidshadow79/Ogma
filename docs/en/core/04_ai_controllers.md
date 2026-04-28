# AI Controllers — Dual-Brain Architecture

**Verified sources**: `core_logic.py` (classes `AIController`, `EmbeddingController`), `modules/ogma_core/controllers.py`

> French version: [../../fr/core/04_ai_controllers.md](../../fr/core/04_ai_controllers.md)

---

## The core principle: two brains, one class

OGMA uses three distinct instances of the `AIController` class, each with a well-defined role:

| Instance | Role | Default temperature |
|---|---|---|
| `_chat_controller` | Main AI — dialogue with the user | 0.7 (creative) |
| `_archiviste_controller` | Archivist — analysis, memory enrichment | 0.3 (precise) |
| `_embedding_controller` | Vector generation for semantic search | — |

These three instances are independent: each can use a different provider, a different model, a different temperature. This allows, for example, having the main AI on a creative online model and the Archivist on a faster local model.

---

## `AIController` — the AI abstraction layer

`AIController` is the central piece. Its role is to **hide backend complexity**: the rest of the application does not need to know whether the response comes from OpenAI, Ollama, or a local GGUF file. It simply calls `call_chat_api()` or `call_chat_api_streaming()`.

Internally, the controller holds references to all available backend managers (`APIManager`, `OllamaManager`, `GGUFManager`, `KoboldManager`). The `get_active_manager()` method returns the manager corresponding to the currently configured backend (`self.backend_type`), or `None` if that backend is unavailable.

### Standard call vs streaming

- `call_chat_api()`: classic call, waits for the complete response before returning it.
- `call_chat_api_streaming()`: call with callback — each generated token is passed to the `callback(chunk)` function as it arrives. Used for real-time display in the interface. Only API and GGUF backends support streaming; others return an explicit error without silent fallback.

### Supported backends

The `backend_type` can take the following values (case-insensitive):

| Value | Backend |
|---|---|
| `API` | Remote providers (OpenAI, Mistral, Anthropic, Google, GROK, OpenRouter) |
| `OLLAMA` | Local Ollama |
| `GGUF` / `GGUF/LLAMA.CPP` | Local GGUF model via llama-cpp-python |
| `KOBOLDCPP` | Local KoboldCpp |
| `AIHORDE` | AIHorde (distributed community compute) |

### The Archivist is distinct

The `_is_archiviste` attribute marks the controller as the Archivist. When this flag is active and logging is enabled (`ARCHIVISTE_LOGGING_ENABLED`), each Archivist AI call is recorded in the token journal (`archiviste_logger`). This allows precise tracking of what the Archivist consumes in tokens per session.

---

## `EmbeddingController` — vectors for memory

`EmbeddingController` is a similar class dedicated to generating embeddings (numeric vectors representing the meaning of a text). These vectors are stored in FAISS and enable semantic search across memories.

It supports the same backends as `AIController`, but with a single method: `create_embedding(text)` which returns a list of floats (or `None` on failure).

---

## Lazy initialization

Controllers are not created when OGMA starts. They are initialized by the `ensure_chat_controller()`, `ensure_archiviste_controller()`, and `ensure_embedding_controller()` functions in `modules/ogma_core/controllers.py`, only on first call. The asynchronous awakening wave triggers these initializations in the appropriate order (see [02_app_orchestration.md](02_app_orchestration.md)).
