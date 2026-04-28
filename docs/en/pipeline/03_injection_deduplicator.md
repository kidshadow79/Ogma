# Injection Deduplication

**Verified source**: `injection_deduplicator.py`

> French version: [../../fr/pipeline/03_injection_deduplicator.md](../../fr/pipeline/03_injection_deduplicator.md)

---

## Problem solved

OGMA injects information into each request through several independent channels: the ego prompt, the Archivist, metacognition extensions. Each can bring the same memories unknowingly. Before this module, the same memory could appear three times in a request, wasting up to 4,500 tokens per message.

`InjectionDeduplicator` is the guardian that tracks what has already been injected and prevents duplicates.

---

## Tracking mechanism

### Tracking by memory identifier

Each memory has an identifier (e.g. `usr-abc123`, `#MEM_EGO_456`). The module maintains a set of identifiers already injected in the current session. When new content is proposed for injection, its identifiers are extracted by regex and compared to this set.

The regex patterns cover several identifier formats: ego identifiers (`#MEM_EGO_*`), user identifiers (`usr-*`), auto-censorship identifiers (`AUTO_CENSURE_*`), and generic formats.

### Tracking by content hash

Additionally, a simplified hash of the beginning of the text (first 15 words) detects identical content without explicit identifiers. This mechanism is deliberately conservative: it uses enough words to avoid false positives on similar but semantically different texts.

### Cooldown system

A memory that has already been injected enters "cooldown": it cannot be re-injected until 3 conversation turns have passed (configurable threshold). This mechanism prevents repetition of recent information without blocking it permanently — a relevant memory naturally returns in later requests.

---

## Public API

| Function | Role |
|---|---|
| `reset_session()` | Resets all trackers (new conversation) |
| `register_injection(source, content, ...)` | Registers content as injected |
| `check_archiviste_injection(memory_id)` | Checks if a memory is already known |
| `register_archiviste_injection(memory_id, content)` | Declares injection of an Archivist memory |
| `register_ego_prompt_injection(content)` | Declares injection of the full ego prompt |
| `increment_message_count()` | Advances the cooldown counter |
| `is_on_cooldown(memory_id)` | Checks a memory's cooldown status |

---

## Limitations

- Semantic deduplication (detecting memories similar in content but with different IDs) is implemented but **disabled by default** (`enable_semantic_dedup = False`). The risk of false positives on important nuances justifies this caution.
- The module is stateful: it maintains its state for the entire duration of a conversation and must be explicitly reset between conversations via `reset_session()`.
