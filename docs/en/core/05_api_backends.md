# Remote Backends (API)

**Verified source**: `core_logic.py` (class `APIManager`)

> French version: [../../fr/core/05_api_backends.md](../../fr/core/05_api_backends.md)

---

## Role of `APIManager`

`APIManager` handles all calls to remote AI providers. It knows the URLs, request formats, and quirks of each provider. It is used by all three AI controllers (main AI, Archivist, embeddings) when their `backend_type` is set to `API`.

---

## Supported providers

Providers are defined in a static configuration table (`API_CONFIG`):

| Provider | Notes |
|---|---|
| OpenAI | Chat + embeddings. Standard OpenAI format. |
| Anthropic | Specific `/messages` format, no public `/models` endpoint. |
| Mistral | Chat + embeddings. OpenAI-compatible format. |
| Google | Gemini endpoint, different request format. |
| GROK | xAI API, OpenAI-compatible format. |
| OpenRouter | Multi-model aggregator, OpenAI format. |
| AIHorde | Community distributed compute network, specific asynchronous format. |

---

## Configuration

The `configure(provider, api_key, model)` method activates the manager. If any of the three parameters is missing or the provider is `"None"`, the manager deactivates itself (`is_available = False`). There is no network check at this point — the configuration is purely local.

---

## Anthropic and OpenRouter (thinking mode) specifics

Anthropic reasoning models (e.g. `claude-3-7-sonnet`) and some OpenRouter models can return a `<thinking>` block before their response. `APIManager` detects and extracts this content into `_last_thinking_content`, which the interface can then display separately in the introspection area. This behavior is transparent to callers.

---

## Streaming

`call_chat_api_streaming()` opens an HTTP streaming connection (Server-Sent Events for OpenAI/Mistral/GROK/OpenRouter, Anthropic-specific format) and passes each token to the `callback` function provided as a parameter. This is the mechanism that enables progressive response display in the interface.

---

## Error handling

Error messages returned by `APIManager` mask the API key if it appears in them (internal function `_redact_error`). Network errors, timeouts, and non-200 HTTP responses are caught and returned as `(None, error_message)` tuples — never raised as exceptions to the caller.
