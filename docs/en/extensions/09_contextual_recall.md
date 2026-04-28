# Contextual Recall — Memory of the Recent Past

**Verified source**: `extensions/contextual_recall/__init__.py`

> French version: [../../fr/extensions/09_contextual_recall.md](../../fr/extensions/09_contextual_recall.md)

---

## Concept

When a user says "as I was telling you two days ago" or "do you remember our conversation from last week?", the AI must be able to access those memories without the user repeating everything.

Contextual Recall solves this problem by automatically detecting temporal references in messages and loading the corresponding conversation summaries.

---

## How it works

**TemporalParser** identifies temporal expressions in the message: "yesterday", "2 days ago", "last week", specific dates, etc.

**SummaryLoader** accesses summaries persisted in conversation JSON files (v2.2+ format) for the identified period.

**ContextBuilder** formats these summaries and injects them into the current conversation's system context.

The user sees none of this process — the AI simply responds with access to the right past.

---

## Philosophy

No magic phrase, no command. Detection is **entirely automatic and transparent**. The module activates only when a temporal reference is detected, avoiding unnecessary injections.
