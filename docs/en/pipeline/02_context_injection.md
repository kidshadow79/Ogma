# Context Injection into the System Prompt

**Verified sources**: `ogma_ng.py` (prompt construction), `logic_callbacks.py` (`chat_fn`), `injection_deduplicator.py`, `data/persistent_context.txt`, `data/ego_compiled.json`

> French version: [../../fr/pipeline/02_context_injection.md](../../fr/pipeline/02_context_injection.md)

---

## The core problem

The main AI has no native memory. It only knows who it is and what it knows about the user from what each request passes to it. Context injection is the mechanism that transforms a generic language model into a personalized, memory-aware AI.

OGMA injects several layers of information into every request. The challenge is to be both exhaustive (not miss a relevant memory) and economical (avoid wasting tokens on redundancies).

---

## System prompt composition

The final system prompt is an ordered concatenation of blocks separated by line breaks. The priority order is as follows:

### 1. Compiled ego

The `data/ego_compiled.json` file contains the main AI's identity traits, built up through conversations. These traits describe the AI's personality, values, and preferences.

The ego is injected first so that the following instructions are read within this identity framework.

### 2. Main system instructions

The main text defining the role, expected behaviors, and operating rules of the AI. Configured in `settings.json` → `prompts.instructions`.

### 3. User persistent context

Contents of `data/persistent_context.txt`, directly editable by the user. This file allows injecting permanent information: user name, life context, lasting preferences. It survives application restarts.

### 4. Visual context

If the perception agent (webcam) is active and has detected events since the last request, they are injected here as a list of observations.

### 5. Perception instructions

If the webcam is active, a specific instruction block is added to guide the AI in interpreting visual data.

---

## Memory context: a different injection

Memories retrieved by `get_parallel_context()` are **not** injected into the system prompt. They were inserted into the conversation history as intermediate system messages in previous turns.

This architectural choice avoids massive duplication: if memories were in both history and the system prompt, the AI would see them twice, representing a waste of 40 to 60% of context tokens based on measurements.

---

## Context window management

The conversation history is truncated before the AI call to stay under 75% of the configured model's maximum context length. Messages are removed starting from the oldest. Multimodal content (images) in old messages is ignored during counting to avoid bias.

---

## Flow summary

```
ego_compiled.json
    +
system instructions (settings.json)
    +
persistent_context.txt
    +
visual context (optional)
    +
perception instructions (if webcam active)
    │
    └── → final system prompt
            +
        truncated history (memories already injected)
            +
        current user message
            │
            └── → main AI call
```
