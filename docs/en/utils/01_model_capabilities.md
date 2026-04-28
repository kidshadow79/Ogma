# Model Capabilities and Hybrid Detection

**Verified sources**: `model_capabilities.py`, `hybrid_detection.py`

> French version: [../../fr/utils/01_model_capabilities.md](../../fr/utils/01_model_capabilities.md)

---

## Problem

AI APIs do not always reliably expose their real context and token limits. Some providers cap models below their official specifications. If OGMA uses an incorrect limit, it may either truncate contexts unnecessarily or trigger overflow errors.

---

## `model_capabilities.py` — Static database

Repository of known capabilities by provider and model (context length, maximum output tokens). This database covers Mistral, OpenAI, Anthropic, Google, GROK, DeepSeek, Qwen, Cohere, and others.

Values are documented official specifications. When a model is not in the database, conservative per-provider fallbacks are used.

---

## `hybrid_detection.py` — Active detection

`hybrid_detection.py` combines two sources:

1. **Official specifications** (`OFFICIAL_SPECIFICATIONS`) — known values from the repository
2. **API detection** — actively tests the API to detect possible throttling

Detection uses a **global cache** (`_DETECTION_CACHE`) to avoid redundant calls for the same model in a session.

---

## Per-provider fallbacks

When neither the static database nor detection can provide a value, conservative fallbacks are applied:

| Provider | Context fallback | Max tokens fallback |
|---|---|---|
| OpenAI | 128,000 | 8,192 |
| Anthropic | 200,000 | 8,192 |
| Google | 1,048,576 | 8,192 |
| GROK | 131,072 | 16,384 |
| Default | 32,768 | 4,096 |

These values are deliberately conservative to avoid overflow errors.
