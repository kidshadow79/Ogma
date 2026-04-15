# OGMA — AI Assistant with Persistent Memory

> 🇫🇷 [Version française (README.fr.md)](README.fr.md)

> **Inspired by Ogmios**, the Gaulish god of eloquence, knowledge and communication.  
> Built by **Yohan BROCARD** — Self-taught, since May 2025.

OGMA is a personal conversational AI assistant with **persistent hybrid memory**, a **dual AI architecture**, and a unique **temporal perception**. This is not a simple chatbot: it's an entity that remembers you, grows with you, and dreams while you sleep.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-AGPL--3.0-22c55e)
![Version](https://img.shields.io/badge/Version-2.2-f97316)
![UI](https://img.shields.io/badge/UI-NiceGUI-0ea5e9)
![Status](https://img.shields.io/badge/Status-Experimental-8b5cf6)
[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/R6R71WW6HI)

![OGMA Interface](docs/screenshots/Interface.png)

---

## 🔬 Vision & Experimental Approach

> I'm not a researcher or a scientist. I'm curious, self-taught, and I built OGMA because I had questions that nobody seemed to be asking in quite the same way. What follows isn't an academic paper — it's an intuition translated into code.

---

Today's AI assistants are already impressive. But they share one fundamental limitation: every conversation starts from scratch. They don't remember you, don't adapt to you over time, and apply the same ethical rules to everyone, in every situation.

I believe **the real challenge of tomorrow** — the one that will define what a truly useful AI companion looks like — lies elsewhere:

**How can an AI develop behavioral persistence — meaning: learn who you are, how you think, what matters to you — and adapt to you autonomously, without losing its ethical grounding?**

This is fundamentally different from surface-level personalization (preferred tone, response format). It's something deeper: an entity that knows you over time, adapts its reasoning to your way of thinking, and knows when to say no — not because a rigid rule forces it to, but because it has internalized universal values it applies with discernment depending on context and person.

OGMA is an attempt to architecturally explore these conditions:

- **Real behavioral persistence** — hybrid semantic memory, structured recollections recalled by context, not a simple history log
- **Adaptation to the individual** — modular personality, boolean ego flags, user profile enriched over time
- **Reasoned autonomy** — ability to decide on its own to speak up, ask a question, or trigger introspection, without the user requesting it
- **Embedded ethics, not imposed rules** — universal values anchored in seed memory, applied flexibly, not rigidly
- **Identity stability** — a consistent personality across sessions, models, and backends

OGMA doesn't claim to have solved these questions. It poses them — with working code, observable behaviors, and an architecture anyone can reproduce.

### 🤖 A Broader Perspective: The Companion of Tomorrow

Companion robots are coming. Their bodies are advancing fast — their cognitive layer, much less so. A robot that doesn't remember you, that starts over at each interaction, that applies the same rigid ethical rules to everyone: that's not a companion, it's an appliance.

OGMA is not a robotics project. But the questions it explores — *how an AI memorizes, adapts and reasons ethically with a specific person over time* — are exactly the questions that the cognitive layer of these systems will need to solve. It's the hardest part, and the least worked on.

That's also why this exploration interests me beyond the conversational assistant.

---

## ✨ Philosophy

OGMA is built on four core pillars:

| Pillar | Description |
|--------|-------------|
| 🔍 **Total Transparency** | No hidden actions. Errors are displayed clearly, never masked. |
| 🎭 **Authenticity** | A genuine imperfect answer beats a fabricated perfect one. No silent fallbacks. |
| 🧠 **Persistent Identity & Behavioral Coherence** | The AI is treated as a developing entity, not a tool. Stable identity, real memory. |
| 🌱 **Organic Growth** | The system evolves with use. Pattern learning without explicit programming. |

---

## 🌱 Origin Story

In **May 2025**, Yohan BROCARD — a cinema professional with zero programming background — discovered LLMs and decided to build, with their help, the assistant he had always wanted.

The entire coding journey happened through practice: no books, no courses — just dialogue with a coding AI, experimentation, and observation of what worked.

From **Octopus** (June 2025, first prototype) to **OGMA** (July 2025), the architecture evolved progressively: Gradio giving way to NiceGUI, a hybrid memory system taking shape, extensions added as needs emerged.

OGMA is above all a personal experimentation ground. The code has its flaws — it bears the marks of a learning journey in progress. What matters are the ideas being explored and the observable behaviors they produce.

Alone and without a developer network, I'm looking for feedback, exchanges, and outside perspectives. If you work on related topics — memory, identity, ethics in AI systems — your input genuinely interests me. OGMA has allowed me to explore territories I never imagined reaching. I'd be happy to explore new ones with others.

---

## 🎯 Core Capabilities

### 🧠 Dual-Brain AI Architecture
OGMA has two distinct AI brains collaborating continuously:

- **Main AI** *(temp. 0.7)* — Conversational brain. Stable personality, empathy, natural and personalized dialogue.
- **The Archivist** *(temp. 0.3)* — Analytical brain. Enriches memory, compiles the ego, analyzes dreams, stays cold and precise.

### 💾 Persistent Hybrid Memory
Not an extended context window, but real and structured memory:

- **SQLite** — typed memory storage with metadata
- **FAISS** — semantic (vector) similarity search
- **FTS5** — hybrid vector + lexical recall
- Automatic enrichment by the Archivist after each exchange
- Automatic backups with rotation (10 files)

### 🎭 Ego System — Personality via Boolean Flags
The AI's personality is stored as **thematic groups of boolean flags with conviction scores** (0–5). At each message, only the groups relevant to the current context are injected into the prompt.

- Each flag is `true` (valued) or `false` (rejected), with variable intensity
- Compilation runs in the background at each shutdown via the Dream Engine
- Result: a coherent identity, contextually precise, that evolves with use

### 🌙 Dream Engine — Identity Consolidation
During inactivity, the AI "dreams" — this is not a narrative gimmick, it's an **identity maintenance process**:

1. Extraction of recent memories as "dream fuel"
2. Generation of a dream narrative by the Main AI (at reduced speed — cognitive metabolism)
3. Analysis by the Archivist as a psychoanalyst (score 1–10, emotion, ego insight)
4. **Incremental ego flag compilation** — personality consolidates in the background
5. If score > 8: the dream context is injected into the next conversation; the AI mentions it naturally

![Dream Engine — the AI narrates and illustrates its own dream](docs/screenshots/Capture_r%C3%A8ve.png)

### 🪞 Cognitive Mirror — Introspection
A Main AI ↔ Archivist dialogue about their own functioning. Produces a traceable and measurable view of the system's internal state — not a simulation, a real exchange between two instances with different temperatures and roles.

![Cognitive Mirror — real-time introspection dialogue](docs/screenshots/capture_introspection.png)

### ⏱️ Temporal Guardian — Active Temporal Perception
Measures delays between messages, detects conversational rhythms (long absence, message bursts), enriches the Archivist prompt with precise temporal context. The AI knows when you return, how much time has passed, and adjusts its register accordingly.

### 🎯 Capability Advisor — Situational Autonomy
Analyzes each message to detect whether an OGMA capability could improve the response (web search, biography, image generation...). If detected, the AI quietly receives instructions to activate it — without the user needing to ask explicitly.

### 📔 Daily Journal
Automatically enriched daily journal. Its content is injected into the context of the first conversation of the day — the AI knows what happened yesterday and can talk about it naturally.

### 🗓️ Organic Planner — Cognitive Agenda
Planned events are treated as **memories of the future**: the AI keeps them in mind naturally, mentions them as they approach, and adapts its tone to the emotional note recorded for each event. Not a task list — a diffuse presence of the agenda in its conversational awareness.

### �️ Project RAG — Isolated Document Memory
Each project has its own semantic memory, completely isolated from personal memory:

- Documents indexed per project (PDF, text, code, Word...)
- Adaptive chunking by file type
- Semantic search via dedicated FAISS index + SQLite
- Relevant chunks injected automatically into context when working on a project
- Multiple simultaneous projects, each with independent configuration

Useful for sustained collaborative work: code review, manuscript writing, research — the AI only accesses documents relevant to the active project.

### 🧠 Cognitive Cache — Conversational Working Memory
A personal scratchpad the AI controls directly via magic phrases:

```
CACHE_ADD:[type]:[content]    # Write a note
CACHE_DELETE:[id]             # Delete
CACHE_UPDATE:[id]:[content]   # Update
CACHE_CLEAR                   # Reset
```

- Persisted per conversation (`data/cognitive_cache/`), invisible to the user
- The AI can note intermediate hypotheses, track a reasoning thread, remember an element to revisit later
- Injected into context on each turn, automatically cleaned up after the conversation
- Not a user-facing memory — a tool for the AI's own reasoning continuity

### �🔀 Multi-Backend AI Management
Unified interface to all major providers — each controller (Main AI, Archivist, Embedding) is independently configurable:

| Type | Providers |
|------|-----------|
| ☁️ **Cloud API** | OpenAI, Anthropic (Claude), Mistral, Google Gemini, GROK, AIHorde |
| 🖥️ **Local** | Ollama, GGUF (llama-cpp-python), KoboldCpp |

![Settings panel — multi-backend configuration](docs/screenshots/Capture_parametres.png)

### 💡 Recommended Models

OGMA is a **sandbox for experimenting with AI concepts** — results depend heavily on the model you choose.

> ⚠️ **Minimum context window**: OGMA injects significant context at each turn (memory, ego, temporal log, journal, instructions). Count on **16k tokens minimum**, **32k recommended**. A model with 4k–8k context will truncate and degrade quickly.

#### 🌸 Main AI — Conversational Brain

| Model | Provider | Context | Notes |
|-------|----------|---------|-------|
| **Mistral Small 4** | [Mistral](https://mistral.ai) | 256k | ⭐ Best quality/cost ratio — recommended starting point |
| **grok-4-1-fast (non-reasoning)** | [xAI](https://x.ai) | 1M | Very fast, very cheap, excellent on instruction-following |
| **Gemma 3 27B** | Google / Ollama | 128k | High quality local (Ollama), resource-heavy |

#### 📚 Archivist — Analytical Brain

The Archivist performs many background calls (memory filtering, ego compilation, dream analysis). It needs to be **fast and low-cost** above all.

| Model | Provider | Context | Notes |
|-------|----------|---------|-------|
| **grok-4-1-fast (non-reasoning)** | [xAI](https://x.ai) | 1M | ⭐ Ideal: extremely cheap, 1M context, fast |
| **Mistral Small 4** | [Mistral](https://mistral.ai) | 256k | Good fallback if xAI not available |

#### 🔢 Embeddings — Semantic Memory

| Model | Provider | Dimensions | Notes |
|-------|----------|-----------|-------|
| **mistral-embed** | [Mistral](https://mistral.ai) | 1024 | ⭐ Recommended — quality, cost, and native French support |
| **text-embedding-3-small** | OpenAI | 1536 | Solid alternative |

> OGMA is first and foremost a place to explore and question. The "best" model doesn't exist — it depends on what behavior you're trying to observe. But the combination **Mistral Small 4 (Main AI) + grok-4-1-fast (Archivist) + mistral-embed (Embeddings)** is a proven, cost-effective starting point.

---

## 🔌 Other Extensions

| Extension | Description |
|-----------|-------------|
| 🎤 **Audio STT/TTS** | Voice recognition (Whisper, Azure) + synthesis (ElevenLabs, Edge-TTS, pyttsx3) |
| 🌐 **Web Navigator** | Intelligent web search + content injection into context |
| 📁 **File Processor** | Upload and analysis of documents (PDF, Word, images) |
| 🖼️ **Text2Img** | AI illustration generation |
| 📬 **Telegram Connector** | OGMA interface via Telegram |
| 🌊 **Cognitive Flux** | Visualization of the AI's thought stream |
| 🧬 **Profile Biography** | Evolving user profile |
| 🔁 **Contextual Recall** | Intelligent contextual memory retrieval |
| 🗂️ **Project RAG** | Isolated document memory per project (SQLite + FAISS) |
| 🧠 **Cognitive Cache** | Conversational working memory the AI controls itself |

---

## 🚀 Installation

### System Prerequisites (Windows)

#### Microsoft C++ Build Tools — required for GGUF mode

Some dependencies (`llama-cpp-python`, and occasionally others) require C++ compilation tools on Windows. **Without them, installation will fail if you use the GGUF local backend.**

> **If you only use cloud APIs (Mistral, OpenAI, xAI…), this step is not required.**

1. Download **[Microsoft C++ Build Tools](https://visualstudio.microsoft.com/fr/visual-cpp-build-tools/)** (free, ~4 GB)
2. During installation, check **"Desktop development with C++"**
3. Restart your system before running `pip install`

> You do **not** need the full Visual Studio IDE — only the Build Tools.

### Requirements
- **Python 3.10+**
- Up-to-date `pip`
- (Optional) NVIDIA GPU with CUDA for acceleration

#### 🖥️ GGUF Local Mode — Hardware Requirements

GGUF (llama-cpp-python) runs models locally on your machine. Performance depends entirely on available hardware.

| Configuration | RAM | GPU | Expected speed |
|--------------|-----|-----|----------------|
| ❌ Minimum (not recommended) | 8 GB | None / CPU-only | 5–15 min / response (4B model) |
| ✅ Comfortable | 16 GB | CUDA GPU 8 GB+ | 5–30s / response |
| ⭐ Optimal | 32 GB+ | CUDA GPU 12 GB+ | <5s / response |

**Critical notes:**
- The KV cache consumes ~72 KB per token: a 8192-token context = ~576 MB RAM
- **CUDA is required for real-time performance.** CPU-only = acceptable wait time only for small models (≤ 4B Q4)
- RTX 50xx (Blackwell) series: CUDA not yet supported by standard PyPI builds (April 2026). Set `gpu_layers = 0`.
- For machines without a capable GPU, **cloud APIs (Mistral, xAI, OpenAI...)** are strongly recommended over GGUF

> To compile llama-cpp-python natively for your hardware: `CMAKE_ARGS="-DGGML_CUDA=on" pip install llama-cpp-python --no-binary llama-cpp-python`

### Dependency Files

| File | Use |
|---|---|
| `requirements.txt` | Standard install (recommended to start) |
| `config/requirements-minimal.txt` | Minimal dependencies only |
| `config/requirements-nvidia.txt` | NVIDIA/CUDA GPU layer (install on top) |

### Option A — With virtual environment (recommended)

Isolates OGMA dependencies from the rest of your Python system.

```bash
# 1. Clone the repository
git clone https://github.com/kidshadow79/Ogma.git
cd Ogma

# 2. Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Upgrade pip
python -m pip install --upgrade pip

# 4. Install dependencies
pip install -r requirements.txt

# For NVIDIA GPU (CUDA) — additional step
# pip install -r config/requirements-nvidia.txt
```

> **Note**: At each new session, remember to reactivate the venv (`venv\Scripts\activate`) before launching OGMA.

### Option B — Without virtual environment

```bash
git clone https://github.com/kidshadow79/Ogma.git
cd Ogma
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## ▶️ Launch

```bash
# Recommended — with automatic checks
python launch_ogma.py

# Quick dev start — minimal
python start_ogma.py
```

OGMA starts automatically at `http://localhost:8080` (retry on ports 8080–8090).

---

## 🏗️ Architecture

```
Ogma/
├── ogma_ng.py                  # NiceGUI interface + main orchestration
├── core_logic.py               # AI controllers (multi-providers & backends)
├── memory_manager.py           # Hybrid memory SQLite + FAISS
├── audio_manager.py            # STT/TTS pipeline
├── launch_ogma.py              # Production entry point
├── start_ogma.py               # Development entry point
│
├── extensions/                 # Modular extensions
│   ├── dream_engine/           # Oneiric cognitive metabolism
│   ├── cognitive_mirror/       # AI introspection
│   ├── journal_de_bord/        # Daily journal
│   ├── web_navigator/          # Intelligent web navigation
│   ├── temporal_guardian/      # Temporal perception
│   └── ...
│
├── data/                       # Persistent data (gitignored)
│   ├── settings.json           # Provider/backend configuration
│   ├── conversations/          # JSON history
│   └── memory/                 # SQLite DB + FAISS index + backups
│
├── config/                     # Dependency files and install scripts
├── docs/                       # Documentation, audits, guides
├── static/                     # UI assets (CSS, images)
└── models/                     # Local GGUF models (gitignored)
```

---

## 📋 Observable Behaviors

Without over-promising, here is what OGMA reproducibly produces:

| Behavior | Description |
|---|---|
| **Identity coherence** | The AI maintains a stable personality across sessions, regardless of the LLM backend used |
| **Semantic memory recall** | Memories are recalled by contextual similarity, not exact keyword matching |
| **Functional introspection** | The Cognitive Mirror produces a measurable, traceable AI↔Archivist dialogue |
| **Adaptive temporal perception** | Behavior varies by time of day, day of week, season, and detected rhythms |
| **Oneiric memory consolidation** | The Dream Engine generates consolidation narratives during inactivity, automatically scored and analyzed |

These behaviors are not simulated by fixed prompts — they emerge from the memory architecture and the duality of the AI brains.

---

## 🛠️ Development

### Adding an Extension

All extensions follow a standardized pattern:

```python
# extensions/my_extension/__init__.py

def initialize_my_extension(chat_controller, archiviste_controller, memory_manager) -> bool:
    """Initialize with OGMA dependencies"""

def is_available() -> bool:
    """Check availability"""

def get_ui_components() -> dict:
    """Return UI components for the header"""

def cleanup():
    """Clean shutdown"""
```

---

## 🤝 Contribution Philosophy

OGMA follows a strict collaborative methodology:

> **"I design, the AI codes — No code without a green light."**

- 🎯 **Me** — vision, concepts, validation, green lights
- ⚡ **The coding AI** — analysis, proposals, implementation after validation
- 🚫 No silent fallbacks, no anticipatory implementation
- 🧩 Modular architecture — avoid monolithic files

---

## 📬 Contact

- **GitHub Issues**: [github.com/kidshadow79/Ogma/issues](https://github.com/kidshadow79/Ogma/issues) — bugs, suggestions, questions
- **Email**: [ogma.contact@etik.com](mailto:ogma.contact@etik.com) — security vulnerability reports, private requests
- **Ko-fi**: [ko-fi.com/ogma_corp](https://ko-fi.com/R6R71WW6HI) — support the project

---

## 📄 License

This project is distributed under the **GNU AGPL v3** license. See the [LICENSE](LICENSE) file for details.

---

<div align="center">

**OGMA** — *The AI that remembers, grows, and dreams.*

Built with passion by [Yohan BROCARD](https://github.com/kidshadow79) — May 2025

</div>
