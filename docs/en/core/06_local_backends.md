# Local Backends (Ollama, GGUF, KoboldCpp)

**Verified source**: `core_logic.py` (classes `OllamaManager`, `GGUFManager`, `KoboldManager`)

> French version: [../../fr/core/06_local_backends.md](../../fr/core/06_local_backends.md)

---

## Overview

OGMA can run entirely without an internet connection thanks to three local backends. Each corresponds to a different way of running an AI model on the user's machine.

---

## Ollama

Ollama is a local server that downloads and manages AI models. It exposes a REST API on `http://localhost:11434` by default. `OllamaManager` communicates with this server via HTTP.

At startup, `check_service()` queries `/api/tags` to get the list of available models. If the server responds, the manager marks itself available. Otherwise, it declares itself unavailable without raising an exception.

A useful feature: the manager can query `/api/show` to discover the true context window of a model. This result is cached to avoid repeated requests. This allows OGMA to automatically adapt to the actual capacity of the loaded model.

---

## GGUF / llama-cpp-python

The GGUF format is a compressed (quantized) model format that can run locally, partly on GPU, partly on CPU. OGMA uses the `llama-cpp-python` library to load them.

`.gguf` files are placed in the `models/` folder at the project root. `GGUFManager` lists the available files and loads the chosen model into memory on first call (or at startup if pre-loading mode is enabled).

Loading can be slow (several seconds to tens of seconds depending on model size). This is why `_async_awakening()` runs it in a separate thread via `asyncio.to_thread()`.

The manager contains a guard (`_is_generating`) to prevent concurrent calls, since llama-cpp-python is not thread-safe. If a generation is already in progress, a second call will be blocked until the first completes.

For machines with little VRAM, a `low_vram` parameter is available in settings (`other_backends.ollama.low_vram`), which adjusts GPU loading behavior.

---

## KoboldCpp

KoboldCpp is an alternative to llama-cpp-python that runs as a separate local server (on `http://localhost:5001` by default). OGMA sends it simple HTTP requests.

Compared to other backends, KoboldCpp has some differences: it does not support native streaming, its request format is different (single prompt rather than a message list), and `is_json` is ignored (it always returns plain text). These differences are handled transparently by `KoboldManager`.

---

## Conditional availability

`GGUFManager` checks whether `llama-cpp-python` is installed when the module loads (`LlamaCPP_AVAILABLE`). If the library is absent, the manager deactivates cleanly without crashing the application. GGUF Vision support (images as input via multimodal projector) additionally requires `llama-cpp-python[server]` with the Llava handler.
