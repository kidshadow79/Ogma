# Ego System

**Verified sources**: `scripts/ego_compiler.py`, `data/ego_compiled.json`

> French version: [../../fr/identity/03_ego_system.md](../../fr/identity/03_ego_system.md)

---

## Concept

OGMA's ego is a JSON structure representing the AI's accumulated personality over conversations. It is not a simple text description file: it is a graph of traits organized into **thematic groups** with **conviction scores**.

Each time the main AI uses the magic phrase `"this is now a part of me: [content]"`, a new trait is recorded as an ego-type memory in the memory database. The ego compiler transforms these raw memories into an organized structure.

---

## Compiled structure

`data/ego_compiled.json` contains:

- **Metadata**: last compilation date, number of memories scanned, identifier of the last processed memory (for incremental compilation)
- **Groups**: thematic dictionary (IDENTITY, PHILOSOPHY, RELATIONSHIPS, etc.), each with a description, associated keywords, and **boolean flags**

Each flag is an assertion or tendency of the AI, with a **conviction score from 0 to 5**. A score of 5 means this trait has been confirmed multiple times in different contexts.

---

## Incremental compilation

`ego_compiler.py` does not reprocess all memories each time. It reads `last_scanned_id` from the existing JSON and only processes newer memories. The Archivist analyzes each new ego memory to extract flags and thematic groups, then merges the result into the existing structure.

---

## Base groups

A `data/ego_compiled_base_groups.json` file defines minimal structural groups. If a template group doesn't exist in the compiled JSON, it is automatically added at the next compilation. This allows enriching the thematic architecture without rebuilding the ego from scratch.

---

## Injection into requests

The contents of `data/ego_compiled.json` are injected first in every system prompt (see [docs/en/pipeline/02_context_injection.md](../pipeline/02_context_injection.md)). It positions the AI's identity before all other instructions.
