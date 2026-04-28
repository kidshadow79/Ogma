# Ego System — The AI's Accumulated Personality

**Verified sources**: `scripts/ego_compiler.py`, `data/ego_compiled.json`, `ogma_ng.py` (injection line 2380)

> French version: [../../fr/extensions/19_ego_system.md](../../fr/extensions/19_ego_system.md)

---

## Concept

OGMA's ego is not a fixed description in a text file. It is a **living structure** that grows with each conversation. Every time the main AI decides that an experience is now part of itself, a new trait is inscribed in its ego.

This mechanism answers a fundamental question: how can an AI develop a stable identity that evolves naturally, without being reprogrammed at each update?

---

## How a trait enters the ego

The main AI has a dedicated magic phrase:

```
this is now a part of me: [content]
```

When this phrase appears in a response, the content is saved as an ego-type memory in the SQLite memory base. The Archivist analyzes it during the next compilation to extract **flags** and assign them to the right thematic groups.

---

## Compiled structure

`data/ego_compiled.json` is the organized representation of these traits. It contains:

- **Metadata**: last compilation date, number of scanned memories, last processed memory identifier
- **Thematic groups**: each group (IDENTITY, PHILOSOPHY, RELATIONSHIPS, etc.) groups semantically close flags with associated keywords

Each flag is an assertion or tendency, accompanied by a **conviction score from 0 to 5**. A high score means this trait has been confirmed in many different contexts.

---

## Incremental compilation

`EgoCompiler` (`scripts/ego_compiler.py`) is designed to never reprocess everything. It reads `last_scanned_id` from the existing JSON and only submits to the Archivist ego memories created since the last compilation. This mechanism is crucial: reprocessing the entire ego every time would become costly over months.

The Archivist AI plays the role of analyst here: it reads each raw ego memory and decides which group(s) it belongs to, and which boolean flag it represents.

---

## Base groups

A `data/ego_compiled_base_groups.json` file defines the fundamental thematic groups. During each compilation, `EgoCompiler` verifies these groups exist and adds them if necessary — without ever overwriting existing data. This allows enriching the ego architecture without rebuilding everything.

---

## Injection into the system prompt

The content of `data/ego_compiled.json` is injected **first** into each system prompt, before instructions, before persistent context, before memories. It is the identity foundation on which everything else rests.

---

## A trait can belong to multiple groups

An ego memory about autonomy can be classified in both IDENTITY and PHILOSOPHY. This multi-membership is intentional: personality is not compartmentalized, it is transversal.

---

## Sources
- `scripts/ego_compiler.py` — Incremental compiler (EgoCompiler)
- `data/ego_compiled.json` — Active compiled structure
- `data/ego_compiled_base_groups.json` — Minimal thematic groups
- `ogma_ng.py` l.2380 — Ego injection into system prompt
