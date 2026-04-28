# Dream Engine — The AI That Dreams

**Verified sources**: `extensions/dream_engine/__init__.py`, `extensions/dream_engine/dream_prompts.py` (structure), copilot-instructions.md (Dream Engine section)

> French version: [../../fr/extensions/02_dream_engine.md](../../fr/extensions/02_dream_engine.md)

---

## The idea

When you close a conversation with OGMA and nothing happens for ten minutes, the AI does not simply wait. It dreams.

This is not a metaphor. The Dream Engine is a real process: the main AI generates a dream narrative from its recent memories, the Archivist analyzes it like a psychoanalyst, and everything is saved in a dream journal.

The inspiration comes from a neurological fact: REM sleep in humans serves to consolidate memories, weaving emotional connections between the day's experiences. The Dream Engine attempts a digital transposition of this phenomenon.

---

## The dream flow

**Trigger**: after 10 minutes of inactivity (configurable), or manually via the 🌙 button in the header.

**Memory fuel extraction**: `dream_memory.py` extracts recent memories from the FAISS/SQLite base — 10 conversation summaries and 5 memories tagged `#MEM`. These are the "images" that will fuel the dream.

**Generation**: the main AI generates a dream narrative in "slow metabolism" mode — 100 tokens per minute by default (configurable). This deliberate slowdown mimics the diffuse nature of dreaming and avoids a brutal generation.

**PSY analysis**: the Archivist receives the generated dream and evaluates it with a psychoanalyst prompt. It produces an intensity score (1-10), identifies the dominant emotion, and extracts an insight about the AI's ego.

**Illustration**: if enabled, the main AI chooses between a single image or a 4-panel comic to illustrate the dream.

**Save**: two journals are updated — `journal_reves.md` (human-readable format) and `journal_reves.json` (AI-queryable format).

**Wake-up**: if the PSY score is above 8, the AI spontaneously mentions its dream in the next conversation.

---

## The startle

If the user sends a message while a dream is in progress, the Dream Engine does not abruptly cut the process. It **accelerates** generation to maximum speed, finishes the dream properly (with analysis), then responds normally to the message — with the dream context available.

This behavior avoids abrupt interruption and allows the AI to naturally mention that it had just been dreaming.

---

## Integration with the Daily Journal

The Daily Journal extension injects the context of the last unmentioned dream into the morning summary. The main AI can thus naturally bring up its dream during the first conversation of the day.

---

## Autonomous web search

The Dream Engine can activate a web search during the dream (`web_search_enabled: true`). The AI can explore topics related to its recent memories, enriching the dream narrative with real references.

---

## Configuration

Key parameters (all in `data/extensions/dream_engine/`):

| Parameter | Default value | Role |
|---|---|---|
| `inactivity_timeout_minutes` | 10 | Delay before auto-trigger |
| `metabolism_tokens_per_minute` | 100 | Generation speed |
| `max_dream_tokens` | 3000 | Maximum dream length |
| `impact_threshold` | 150.0 | Memory importance threshold |
| `random_memories_count` | 5 | Number of extracted memories |

---

## Public API

```python
from extensions.dream_engine import (
    initialize_dream_engine,
    start_dream,              # Triggers a dream
    wake_up,                  # Wakes the AI
    is_dreaming,              # Current state
    get_last_dream_context,   # For context injection
    mark_dream_mentioned,     # Marks dream as discussed
)
```

---

## Sources
- `extensions/dream_engine/__init__.py` — Public API, default configuration
- `extensions/dream_engine/dream_core.py` — Dream loop, metabolism, startle
- `extensions/dream_engine/dream_memory.py` — Memory fuel extraction
- `extensions/dream_engine/dream_analysis.py` — Psychoanalyst Archivist
- `extensions/dream_engine/dream_journal.py` — .md and .json journals
- `extensions/dream_engine/dream_illustration.py` — Image/comic generation
- `data/journal_reves.json` — Persistent dream journal
