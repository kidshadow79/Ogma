# Persistent Context and System Prompts

**Verified sources**: `data/persistent_context.default.txt`, `data/instructions_defaults.json`, `data/settings.json` (section `prompts`)

> French version: [../../fr/config/02_prompts_and_context.md](../../fr/config/02_prompts_and_context.md)

---

## Two levels of textual configuration

OGMA distinguishes two types of text that guide the main AI's behavior:

- **Persistent context**: a short, free-form text that the user can edit. It is injected into every conversation as a behavioral foundation.
- **System prompts**: structured, more technical instructions that define how the Archivist encodes memories, how the main AI responds, how memory is selected and injected.

---

## The persistent context — `data/persistent_context.txt`

This is the file the user sees and can edit from the interface. It contains fundamental behavioral rules in natural language:

> *"You speak naturally, you never simulate your responses. If you don't know, you say so. When uncertain, use the conditional..."*

This text is injected at the start of each session as part of the main AI's system prompt. If `persistent_context.txt` does not exist on first launch, `launch_ogma.py` creates it from the `persistent_context.default.txt` template.

---

## System prompts — `data/instructions_defaults.json`

This file contains the default prompts for each role in the system. These prompts are written in a compact style called "High-Density Communication" (HDC): dense instructions, structured in named blocks, without long sentences. This is intentional — AI models follow concise, explicit instructions more reliably.

The main prompts:

| Key | Usage |
|---|---|
| `instructions` | Main AI system prompt — identity, absolute rules, list of available magic phrases, ethical rule |
| `memorization` | Archivist prompt to encode a memory as structured JSON with impact scoring |
| `injection` | Archivist prompt to select and format the memory to inject into a conversation |
| `perception` | Prompt for image analysis (webcam, vision) |
| `salutations` | Continuity prompt — how the main AI greets the user based on absence duration |
| `temporal_guardian` | Behavioral adaptation guide based on the user's temporal rhythm |
| `ego_memorization` | Archivist prompt to encode an ego trait as JSON |

---

## Memory scoring

The `memorization` prompt defines a memory impact scoring formula:

$$\text{score} = \text{intensity} \times \text{base\_factor} \times (\text{freedom} + \text{creation} + \text{transmission} + \text{contextual\_intensity})$$

The Archivist evaluates each memory across these dimensions (0.0 to 1.0) and produces structured JSON. This score then determines the priority of the memory during future injections.

---

## Priority rule

Prompts in `settings.json` (section `prompts`) take priority over the defaults in `instructions_defaults.json`. If the user has customized their instructions from the interface, their version is used. The `instructions_defaults.json` file only serves as a safety net if `settings.json` does not contain these keys.

---

## Magic phrases

The `instructions` prompt lists trigger phrases that the main AI can write in its responses to activate system functions (memorization, introspection, image generation, web search...). These phrases are detected by `magic_phrase_guard.py` and the callback system. They are never simulated — if the AI writes them, the system executes them for real.
