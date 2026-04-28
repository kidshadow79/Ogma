# Organic Planner — The AI's Agenda

**Verified source**: `extensions/organic_planner/__init__.py`

> French version: [../../fr/extensions/05_organic_planner.md](../../fr/extensions/05_organic_planner.md)

---

## Concept

The Organic Planner is OGMA's planning system. It allows the AI to maintain a list of tasks, appointments, and commitments, and to inject a relevant **briefing** into conversations.

---

## Briefing

The `get_briefing_text()` method produces a structured summary of planned items relevant to the current moment (today's tasks, upcoming deadlines). This briefing is injected into the system context if the extension is active.

---

## Interaction

The main AI can create, modify, and delete items in the planner via natural language. The Archivist can also suggest planner additions during its analyses.

---

## Configuration

The extension's parameters are persisted in `data/organic_planner_settings.json`. This file is the source of truth at runtime (see [CODING_RULES.md](../../CODING_RULES.md) on JSON/Python synchronization).
