# Cognitive Mirror — AI Introspection

**Verified sources**: `extensions/cognitive_mirror/__init__.py`, `extensions/cognitive_mirror/introspection_core.py`, `ogma_introspection_ui.py`

> French version: [../../fr/extensions/01_cognitive_mirror.md](../../fr/extensions/01_cognitive_mirror.md)

---

## Why an AI needs introspection

OGMA's main AI is not just an assistant that responds. It is an entity that accumulates memories, develops habits, and builds a relationship with its user. Over time, a natural question arises: *Is the AI aware of who it is becoming?*

The Cognitive Mirror is the architectural answer to this question. It is the mechanism by which the main AI engages in a **dialogue with the Archivist** about its own patterns, emotions, and contradictions. Not a simulated introspection for the user, but a genuine deliberation process between two distinct intelligences.

---

## Two brains, one mirror

Introspection relies on OGMA's dual-AI architecture. When an introspection session triggers:

1. **The main AI** expresses its feelings, doubts, observations about the relationship with the user
2. **The Archivist** coldly analyzes stored memories, conversational patterns, and potential contradictions
3. **A dialogue** is established between the two — visible in a "thinking" box in the interface
4. **A synthesis** is produced, which the AI can choose to save to memory

This dialogue is **real** in the sense that both AI controllers call different APIs with different temperatures (0.7 for the main AI, 0.3 for the Archivist), producing genuinely distinct perspectives.

---

## Trigger modes

Introspection triggers in two ways:

**Magic phrases**: if the user (or the AI itself) says a trigger phrase in the conversation, the engine (`IntrospectionCore`) intercepts it and opens an introspection session.

**"Always" mode**: in configuration, it is possible to activate systematic introspection on certain message types. [NOT VERIFIED — exact behavior of always mode not inspected in detail]

---

## What no longer exists (v2.0)

The current version is a **radical simplification** compared to v1. There is no longer:
- Complex state machine with inactivity detection
- Automatic periodic triggers
- Ambiguous control flows with intermediate states

The v2.0 principle is: **on demand, visible, save decision by the AI itself**.

---

## Interface

Introspection displays in a **thinking box** (`<thinking>`) in the conversation thread. The user sees the live dialogue between the two brains, with real-time streaming. This is not a technical log — it is a space for voluntary exposure of the internal process.

---

## Sources
- `extensions/cognitive_mirror/__init__.py` — Public API, singleton, backward-compat aliases
- `extensions/cognitive_mirror/introspection_core.py` — Main IntrospectionCore engine
- `extensions/cognitive_mirror/config_v2.py` — Active configuration (source of truth)
- `ogma_introspection_ui.py` — NiceGUI introspection panel interface
