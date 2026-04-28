# Cognitive Flux — Watching the AI Think

**Verified source**: `extensions/flux_cognitif/__init__.py`

> French version: [../../fr/extensions/12_flux_cognitif.md](../../fr/extensions/12_flux_cognitif.md)

---

## Concept

The Cognitive Flux is a **real-time visualization of OGMA's internal decisions**. A translucent amber overlay continuously displays cognitive events: Archivist injections, memory access, Journal contributions, ongoing dreams, Capability Advisor decisions.

This is total transparency made visible — not a technical developer log, but a screen that shows what the AI is "thinking" while it responds.

---

## Architecture

**StreamCore** (`stream_core.py`) is a singleton that receives cognitive events from OGMA's various components via hooks in `ogma_ng.py`. These events are timestamped and typed (memory, archivist, journal, dream, capability).

**StreamUI** (`stream_ui.py`) is the NiceGUI overlay that displays these events in real time in a readable format.

---

## Event sources

Hooks in `ogma_ng.py` automatically log:
- Memory injections by the Archivist
- Biography accesses
- Daily Journal entries injected
- Capability Advisor decisions
- Dream Engine states

---

## Philosophy

> "Total Transparency — making the AI's thoughts visible"

The Cognitive Flux is the materialization of this fundamental OGMA pillar: the user should never have to guess why the AI said something.
