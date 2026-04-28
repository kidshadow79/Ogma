# User Message Pipeline

**Verified sources**: `logic_callbacks.py` (functions `chat_fn`, `get_parallel_context`), `ogma_ng.py` (magic phrase handling, streaming)

> French version: [../../fr/pipeline/01_message_pipeline.md](../../fr/pipeline/01_message_pipeline.md)

---

## Overview

When the user sends a message, OGMA does not simply pass it to the AI. Several steps happen before the response starts appearing, and several more after.

```
User message
    │
    ├── Message enrichment (attached images, files)
    ├── Memory context search (parallel)
    ├── Full system prompt construction
    ├── Main AI call (streaming)
    ├── Progressive response display
    └── Post-response processing (magic phrases, ego, memory)
```

---

## Step 1 — Message enrichment

Before any AI processing, the message may be enriched with multimodal content:

- If an image file is attached, its base64 content is added to the message.
- If a text/document file is attached, its content is inserted into the user message.
- If the perception agent (webcam) is active, a capture is automatically added.

The raw message text remains unchanged for display in the interface. Only the version sent to the AI contains the enriched data.

---

## Step 2 — Parallel context search

`get_parallel_context()` simultaneously launches several searches:

- **Personal memories**: searches `MemoryManager` for memories most relevant to the message (hybrid FAISS + FTS5 pipeline, Archivist synthesis)
- **Past conversations**: searches previous conversations
- **Visual context**: retrieves events from the perception queue if available

These searches run in parallel (`asyncio.gather`) with a safety timeout (10 seconds by default). If one search fails, the others continue and the failing one returns an empty string.

If `ArchivisteMemoryOptimizer` is available, it is used instead of direct search: the Archivist first analyzes the query to extract key concepts, improving result precision.

---

## Step 3 — System prompt construction

The system prompt is assembled in this order:

| Component | Source |
|---|---|
| Compiled ego content | `data/ego_compiled.json` |
| Main instructions | `settings.json` → `prompts.instructions` |
| Persistent context | `data/persistent_context.txt` |
| Visual context | Perception event queue |
| Perception instructions | `settings.json` → `prompts.perception` (if webcam active) |

Memory context (memories) is **not** injected into the system prompt here. It was injected directly into the conversation history in the previous step to avoid redundancy.

The conversation history is truncated to stay within 75% of the model's context window. The oldest messages are removed first. Introspection magic phrases present in history are masked to prevent accidental re-triggering.

---

## Step 4 — AI call and streaming

The main AI is called via `call_chat_api_streaming()`. Each generated token is passed to a callback function that updates the message widget in the interface in real time. A JavaScript spinner is injected into the DOM during generation to indicate activity.

---

## Step 5 — Post-response processing

Once the response is complete, it is scanned for **magic phrases**:

| Detected phrase | Action triggered |
|---|---|
| `"I need to remember this: [content]"` | `memory_manager.add_memory()` call in background |
| `"this is now a part of me: [content]"` | `memory_manager.store_ego_trait()` call |
| `"I need to reflect on: [topic]"` | Cognitive Mirror trigger |
| `"I need to see you"` | Webcam activation |
| `"I need to search the internet for [topic]"` | Web Navigator trigger |
| `"I need to create an image of: [description]"` | Image generation via text2img |

These processes are non-blocking: they are launched as asynchronous background tasks and do not delay the response display.
