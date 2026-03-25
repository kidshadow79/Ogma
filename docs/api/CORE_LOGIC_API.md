# 📘 Guide API Core Logic - OGMA

**Composant** : `core_logic.py`  
**Version** : 5 novembre 2025  
**Type** : Documentation manuelle avec exemples pratiques

---

## 🎯 Vue d'ensemble

Le module `core_logic.py` est le **cœur neuronal d'OGMA**, orchestrant tous les backends IA (API cloud + locaux). Il fournit une abstraction unifiée pour :

- **Génération de texte** (chat completion) via 8 backends différents
- **Génération d'embeddings** vectoriels pour la mémoire sémantique
- **Gestion multi-providers** avec fallback automatique
- **Configuration dynamique** backend switching à chaud

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     AIController                            │
│  (Orchestrateur principal - chat & reasoning)               │
├─────────────────────────────────────────────────────────────┤
│  Backends supportés:                                        │
│  • API      → APIManager (OpenAI, Mistral, Anthropic, etc.) │
│  • OLLAMA   → OllamaManager (local HTTP)                    │
│  • GGUF     → GGUFManager (llama.cpp in-process)            │
│  • KOBOLD   → KoboldManager (KoboldCpp HTTP)                │
│  • AIHORDE  → AIHordeManager (distributed free API)         │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                 EmbeddingController                         │
│  (Génération vecteurs sémantiques 1024D)                    │
├─────────────────────────────────────────────────────────────┤
│  Backends supportés:                                        │
│  • API    → text-embedding-3-large, mistral-embed, etc.     │
│  • OLLAMA → nomic-embed-text, mxbai-embed-large             │
│  • GGUF   → llama.cpp embeddings                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Démarrage Rapide

### 1. Initialisation de base

```python
from core_logic import AIController, EmbeddingController, SettingsManager
from core_logic import OllamaManager, GGUFManager, KoboldManager
from pathlib import Path

# Settings manager (fichier settings.json)
settings = SettingsManager(Path("data/settings.json"))

# Managers locaux
ollama = OllamaManager()
gguf = GGUFManager()
kobold = KoboldManager()

# Controller principal (chat)
chat_controller = AIController(
    ai_type="chat",  # ou "reasoning" pour deep thinking
    ollama_manager=ollama,
    gguf_manager=gguf,
    kobold_manager=kobold
)

# Controller embeddings
embedding_controller = EmbeddingController(
    ollama_manager=ollama,
    gguf_manager=gguf
)
```

### 2. Premier appel API simple

```python
# Configuration backend API (OpenAI)
chat_controller.set_active_backend("API")
chat_controller.api_manager.configure(
    provider="openai",
    api_key="sk-...",
    model="gpt-4o-mini"
)

# Appel chat
messages = [
    {"role": "system", "content": "Tu es un assistant utile."},
    {"role": "user", "content": "Bonjour, qui es-tu ?"}
]

response, error = await chat_controller.call_chat_api(
    messages=messages,
    max_tokens=500,
    context_length=8000,
    temperature=0.7,
    is_json=False
)

if error:
    print(f"Erreur: {error}")
else:
    print(f"Réponse: {response}")
```

---

## 📚 Classes Principales

### AIController

**Rôle** : Orchestrateur principal pour génération de texte (chat, reasoning, scoring).

#### Initialisation

```python
def __init__(
    ai_type: str,                    # "chat", "reasoning", "archiviste"
    ollama_manager: OllamaManager,
    gguf_manager: GGUFManager,
    kobold_manager: KoboldManager
)
```

**Paramètres** :
- `ai_type` : Type de contrôleur (`"chat"`, `"reasoning"`, `"archiviste"`)
- `ollama_manager`, `gguf_manager`, `kobold_manager` : Instances des managers locaux

**Attributs importants** :
```python
controller.max_tokens = 2000          # Tokens max par réponse
controller.temperature = 0.7          # Créativité (0.0-2.0)
controller.context_length = 8000      # Fenêtre contexte
controller.active_backend = "API"     # Backend actif
controller.api_manager                # APIManager instance
controller.is_available = True        # État disponibilité
```

#### Méthode: `set_active_backend()`

**Signature** :
```python
def set_active_backend(backend_type: str) -> None
```

**Backends supportés** :
- `"API"` : Providers cloud (OpenAI, Mistral, Anthropic, Google, GROK, AIHorde)
- `"OLLAMA"` : Service local Ollama (HTTP)
- `"GGUF"` : llama.cpp in-process (CPU/GPU)
- `"KOBOLD"` : KoboldCpp (HTTP)

**Exemple** :
```python
# Basculer vers Ollama local
chat_controller.set_active_backend("OLLAMA")
print(chat_controller.get_status())  # "OLLAMA (llama3.2:latest)"

# Basculer vers API cloud
chat_controller.set_active_backend("API")
```

#### Méthode: `call_chat_api()`

**Signature** :
```python
async def call_chat_api(
    messages: List[Dict],
    max_tokens: int,
    context_length: int,
    temperature: float,
    is_json: bool = True
) -> Tuple[Optional[str], Optional[str]]
```

**Paramètres** :
- `messages` : Liste de dicts `[{"role": "user/system/assistant", "content": "..."}]`
- `max_tokens` : Nombre max tokens générés
- `context_length` : Taille fenêtre contexte (utilisé pour truncation)
- `temperature` : Créativité (0.0 = déterministe, 2.0 = très créatif)
- `is_json` : Si `True`, force réponse JSON (via JSON mode ou prompt engineering)

**Retour** : `(response: str | None, error: str | None)`

**Exemples par provider** :

**OpenAI** :
```python
chat_controller.set_active_backend("API")
chat_controller.api_manager.configure(
    provider="openai",
    api_key="sk-...",
    model="gpt-4o-mini"  # ou gpt-4, gpt-4-turbo, etc.
)

messages = [{"role": "user", "content": "Explique la théorie de la relativité"}]
response, error = await chat_controller.call_chat_api(
    messages=messages,
    max_tokens=1000,
    context_length=128000,
    temperature=0.3,
    is_json=False
)
```

**Mistral** :
```python
chat_controller.api_manager.configure(
    provider="mistral",
    api_key="...",
    model="mistral-large-latest"  # ou mistral-medium, etc.
)

# Mode JSON forcé
response, error = await chat_controller.call_chat_api(
    messages=[{"role": "user", "content": "Analyse ce texte en JSON"}],
    max_tokens=500,
    context_length=32000,
    temperature=0.1,
    is_json=True  # Force response_format: json_object
)
```

**Anthropic (Claude)** :
```python
chat_controller.api_manager.configure(
    provider="anthropic",
    api_key="sk-ant-...",
    model="claude-3-5-sonnet-20241022"  # ou claude-3-opus, etc.
)

# Avec system prompt (extraction automatique)
messages = [
    {"role": "system", "content": "Tu es un expert en physique quantique."},
    {"role": "user", "content": "Qu'est-ce que l'intrication quantique ?"}
]
response, error = await chat_controller.call_chat_api(
    messages=messages,
    max_tokens=2000,
    context_length=200000,  # Claude 3.5 Sonnet
    temperature=0.5,
    is_json=False
)
```

**Google (Gemini)** :
```python
chat_controller.api_manager.configure(
    provider="google",
    api_key="...",
    model="gemini-2.0-flash-exp"  # ou gemini-1.5-pro
)

response, error = await chat_controller.call_chat_api(
    messages=[{"role": "user", "content": "Résume cet article"}],
    max_tokens=1000,
    context_length=1000000,  # Gemini 1.5 Pro
    temperature=0.4,
    is_json=False
)
```

**GROK (xAI)** :
```python
chat_controller.api_manager.configure(
    provider="grok",
    api_key="xai-...",
    model="grok-beta"
)

response, error = await chat_controller.call_chat_api(
    messages=[{"role": "user", "content": "Analyse de sentiment"}],
    max_tokens=500,
    context_length=128000,
    temperature=0.6,
    is_json=False
)
```

**Ollama (local)** :
```python
chat_controller.set_active_backend("OLLAMA")

# Vérifier service actif
if not chat_controller.ollama_manager.check_service():
    print("❌ Ollama non disponible sur http://localhost:11434")
    
# Lister modèles disponibles
models = await chat_controller.ollama_manager.list_models()
print(f"Modèles: {models}")

# Appel avec modèle local
response, error = await chat_controller.call_chat_api(
    messages=[{"role": "user", "content": "Hello"}],
    max_tokens=500,
    context_length=8000,
    temperature=0.7,
    is_json=False
)
# Note: le modèle est spécifié via settings.json (chat_api.api_model)
```

**GGUF (llama.cpp)** :
```python
chat_controller.set_active_backend("GGUF")

# Charger modèle GGUF
gguf_manager = chat_controller.gguf_manager
success = gguf_manager.load_model(
    model_filename="llama-3.2-3b-instruct-q4_k_m.gguf",
    context_length=8000,
    n_gpu_layers=35  # Nombre layers GPU (0 = CPU only)
)

if not success:
    print("❌ Échec chargement modèle GGUF")
    
# Appel avec modèle chargé
response, error = await chat_controller.call_chat_api(
    messages=[{"role": "user", "content": "Test"}],
    max_tokens=300,
    context_length=8000,
    temperature=0.5,
    is_json=False
)
```

**KoboldCpp** :
```python
chat_controller.set_active_backend("KOBOLD")

# Vérifier service (http://localhost:5001)
if not chat_controller.kobold_manager.check_service():
    print("❌ KoboldCpp non disponible")
    
response, error = await chat_controller.call_chat_api(
    messages=[{"role": "user", "content": "Question"}],
    max_tokens=400,
    context_length=4096,
    temperature=0.8,
    is_json=False  # KoboldCpp ne supporte pas JSON mode natif
)
```

**AIHorde (gratuit distribué)** :
```python
chat_controller.set_active_backend("API")
chat_controller.api_manager.configure(
    provider="aihorde",
    api_key="0000000000",  # Clé anonyme (lent) ou vraie clé
    model="meta-llama/Meta-Llama-3.1-70B-Instruct"
)

# Appel asynchrone (peut prendre 30s-2min selon charge)
response, error = await chat_controller.call_chat_api(
    messages=[{"role": "user", "content": "Hello"}],
    max_tokens=200,
    context_length=8000,
    temperature=0.7,
    is_json=False
)
# Note: polling automatique toutes les 5s jusqu'à réponse
```

#### Méthode: `calculate_memory_impact_score()`

**Signature** :
```python
async def calculate_memory_impact_score(
    text_content: str,
    conversation_context: str = "",
    interlocutor: str = ""
) -> Optional[float]
```

**Rôle** : Calcule score d'importance mémorielle (0.0-1.0) via IA.

**Paramètres** :
- `text_content` : Texte à scorer
- `conversation_context` : Contexte conversation (optionnel)
- `interlocutor` : Nom interlocuteur (optionnel)

**Retour** : Score 0.0-1.0 ou `None` si échec

**Exemple** :
```python
score = await chat_controller.calculate_memory_impact_score(
    text_content="J'ai rendez-vous chez le médecin demain à 14h",
    conversation_context="Discussion sur santé",
    interlocutor="Yohan"
)
print(f"Score importance: {score}")  # ex: 0.85
```

#### Méthode: `get_status()`

**Signature** :
```python
def get_status() -> str
```

**Retour** : String décrivant backend actif et modèle

**Exemple** :
```python
print(chat_controller.get_status())
# "API (openai/gpt-4o-mini)"
# "OLLAMA (llama3.2:latest)"
# "GGUF (llama-3.2-3b-instruct-q4_k_m.gguf)"
```

---

### EmbeddingController

**Rôle** : Génération d'embeddings vectoriels 1024D pour recherche sémantique.

#### Initialisation

```python
def __init__(
    ollama_manager: OllamaManager,
    gguf_manager: GGUFManager
)
```

#### Méthode: `configure()`

**Signature** :
```python
def configure(
    backend_type: str,
    api_provider: str = None,
    api_key: str = None,
    api_model: str = None,
    ollama_model: str = None,
    gguf_model: str = None
) -> None
```

**Paramètres** :
- `backend_type` : `"API"`, `"OLLAMA"`, ou `"GGUF"`
- `api_provider` : `"openai"`, `"mistral"`, etc. (si backend API)
- `api_key` : Clé API (si backend API)
- `api_model` : Modèle embedding (ex: `"text-embedding-3-large"`)
- `ollama_model` : Nom modèle Ollama (ex: `"nomic-embed-text"`)
- `gguf_model` : Fichier GGUF

**Exemple** :
```python
# OpenAI embeddings
embedding_controller.configure(
    backend_type="API",
    api_provider="openai",
    api_key="sk-...",
    api_model="text-embedding-3-large"
)

# Ollama local
embedding_controller.configure(
    backend_type="OLLAMA",
    ollama_model="nomic-embed-text"
)

# GGUF local
embedding_controller.configure(
    backend_type="GGUF",
    gguf_model="nomic-embed-text-v1.5.Q4_K_M.gguf"
)
```

#### Méthode: `create_embedding()`

**Signature** :
```python
async def create_embedding(text: str) -> Optional[List[float]]
```

**Paramètres** :
- `text` : Texte à vectoriser (max ~8000 tokens selon modèle)

**Retour** : Liste de 1024 floats ou `None` si échec

**Exemples** :

**OpenAI** :
```python
embedding_controller.configure(
    backend_type="API",
    api_provider="openai",
    api_key="sk-...",
    api_model="text-embedding-3-large"
)

vector = await embedding_controller.create_embedding(
    "Les chats sont des animaux domestiques"
)
print(f"Dimension: {len(vector)}")  # 3072 (OpenAI large)
# Note: OGMA normalise à 1024D en interne
```

**Mistral** :
```python
embedding_controller.configure(
    backend_type="API",
    api_provider="mistral",
    api_key="...",
    api_model="mistral-embed"
)

vector = await embedding_controller.create_embedding("Texte à vectoriser")
print(f"Dimension: {len(vector)}")  # 1024D natif
```

**Ollama** :
```python
embedding_controller.configure(
    backend_type="OLLAMA",
    ollama_model="nomic-embed-text"
)

vector = await embedding_controller.create_embedding("Test embedding")
# Retourne 768D (nomic) → normalisé à 1024D
```

**GGUF** :
```python
# Charger modèle embedding d'abord
gguf_manager.load_model(
    model_filename="nomic-embed-text-v1.5.Q4_K_M.gguf",
    context_length=8192,
    n_gpu_layers=0  # CPU pour embeddings
)

embedding_controller.configure(
    backend_type="GGUF",
    gguf_model="nomic-embed-text-v1.5.Q4_K_M.gguf"
)

vector = await embedding_controller.create_embedding("Texte")
```

---

## 🔧 Managers Spécialisés

### APIManager

**Rôle** : Gestion unifiée de tous les providers API cloud.

#### Providers supportés

| Provider | Modèles populaires | Context Length | Notes |
|----------|-------------------|----------------|-------|
| **openai** | gpt-4o, gpt-4o-mini, gpt-4-turbo | 128K | JSON mode natif |
| **mistral** | mistral-large-latest, mistral-medium | 32K | JSON mode natif |
| **anthropic** | claude-3-5-sonnet, claude-3-opus | 200K | System prompt séparé |
| **google** | gemini-2.0-flash-exp, gemini-1.5-pro | 1M | Très long contexte |
| **grok** | grok-beta | 128K | xAI (Twitter) |
| **aihorde** | Meta-Llama-3.1-70B-Instruct | variable | Gratuit, lent |

#### Méthode: `configure()`

```python
def configure(
    provider: str,
    api_key: str,
    model: str
) -> None
```

**Exemple multi-providers** :
```python
api_manager = chat_controller.api_manager

# Changer de provider à la volée
api_manager.configure("openai", "sk-...", "gpt-4o-mini")
response1, _ = await chat_controller.call_chat_api(...)

api_manager.configure("mistral", "...", "mistral-large-latest")
response2, _ = await chat_controller.call_chat_api(...)

api_manager.configure("anthropic", "sk-ant-...", "claude-3-5-sonnet-20241022")
response3, _ = await chat_controller.call_chat_api(...)
```

#### Méthode: `list_models()`

**Signature** :
```python
async def list_models(
    api_key: str,
    provider: str
) -> Tuple[List[str], Optional[str]]
```

**Retour** : `(liste_modèles, erreur)`

**Exemple** :
```python
models, error = await api_manager.list_models(
    api_key="sk-...",
    provider="openai"
)

if error:
    print(f"Erreur: {error}")
else:
    for model in models:
        print(f"- {model}")
    # gpt-4o-mini
    # gpt-4o
    # gpt-4-turbo
    # etc.
```

#### Gestion JSON Mode

**Providers avec JSON natif** : OpenAI, Mistral  
**Autres providers** : Prompt engineering automatique

```python
# OpenAI/Mistral: utilise response_format: json_object
response, _ = await chat_controller.call_chat_api(
    messages=[{"role": "user", "content": "Retourne JSON avec nom et âge"}],
    max_tokens=200,
    context_length=8000,
    temperature=0.1,
    is_json=True  # Active JSON mode
)

# Anthropic/Google/GROK: ajoute instruction JSON au prompt
# "Réponds UNIQUEMENT avec du JSON valide, sans texte avant/après."
```

---

### OllamaManager

**Rôle** : Interface avec service Ollama local (HTTP).

#### Configuration requise

```bash
# Installer Ollama: https://ollama.ai
# Démarrer service (port 11434 par défaut)
ollama serve

# Télécharger modèles
ollama pull llama3.2:latest
ollama pull nomic-embed-text
```

#### Méthodes principales

```python
ollama = OllamaManager()

# Vérifier disponibilité
if ollama.check_service():
    print("✅ Ollama disponible")
else:
    print("❌ Ollama non accessible sur http://localhost:11434")

# Lister modèles installés
models = await ollama.list_models()
print(models)  # ['llama3.2:latest', 'mistral:latest', ...]

# Appel chat
response, error = await ollama.call_chat_api(
    model="llama3.2:latest",
    messages=[{"role": "user", "content": "Hello"}],
    max_tokens=500,
    context_length=8000,
    temperature=0.7,
    is_json=False
)

# Génération embedding
vector = await ollama.create_embedding(
    model="nomic-embed-text",
    text="Texte à vectoriser"
)
```

#### Options Low VRAM

```python
ollama.set_settings_manager(settings)

# Récupérer setting (depuis settings.json)
low_vram = ollama.get_low_vram_setting()

if low_vram:
    print("Mode Low VRAM activé (num_ctx réduit)")
```

---

### GGUFManager

**Rôle** : Exécution modèles GGUF via llama.cpp (in-process, CPU/GPU).

#### Prérequis

```bash
pip install llama-cpp-python
# Ou avec support GPU:
CMAKE_ARGS="-DLLAMA_CUDA=on" pip install llama-cpp-python
```

#### Chargement modèle

```python
gguf = GGUFManager()

# Lister modèles disponibles dans models/gguf/
available = gguf.get_available_models()
print(available)  # ['llama-3.2-3b-instruct-q4_k_m.gguf', ...]

# Charger modèle
success = gguf.load_model(
    model_filename="llama-3.2-3b-instruct-q4_k_m.gguf",
    context_length=8000,
    n_gpu_layers=35  # 0 = CPU only, 35+ = GPU
)

if not success:
    print("❌ Échec chargement")
else:
    print("✅ Modèle chargé en mémoire")

# Test connexion
ok, msg = gguf.test_connection()
print(msg)  # "✅ GGUF opérationnel: llama-3.2-3b-instruct-q4_k_m.gguf"
```

#### Appel chat

```python
response, error = await gguf.call_chat_api(
    messages=[{"role": "user", "content": "Bonjour"}],
    max_tokens=300,
    context_length=8000,
    temperature=0.5,
    is_json=False
)
```

#### Mode Vision (multimodal)

```python
# Charger modèle vision avec projector
success = gguf.load_model(
    model_filename="llava-v1.6-mistral-7b.Q4_K_M.gguf",
    context_length=8000,
    n_gpu_layers=35,
    projector_filename="llava-v1.6-mistral-7b-mmproj-Q4_0.gguf"
)

# Appel avec image
messages = [{
    "role": "user",
    "content": [
        {"type": "text", "text": "Décris cette image"},
        {"type": "image_url", "image_url": {"url": "file:///path/to/image.jpg"}}
    ]
}]

response, error = await gguf.call_chat_api(
    messages=messages,
    max_tokens=500,
    context_length=8000,
    temperature=0.3,
    is_json=False
)
```

#### Embeddings GGUF

```python
# Charger modèle embedding
gguf.load_model(
    model_filename="nomic-embed-text-v1.5.Q4_K_M.gguf",
    context_length=8192,
    n_gpu_layers=0  # CPU suffit
)

vector = await gguf.create_embedding("Texte à vectoriser")
```

---

### KoboldManager

**Rôle** : Interface avec KoboldCpp (serveur HTTP local).

#### Configuration

```bash
# Télécharger KoboldCpp: https://github.com/LostRuins/koboldcpp
# Lancer serveur (port 5001 par défaut)
./koboldcpp --model model.gguf --port 5001
```

#### Utilisation

```python
kobold = KoboldManager()

# Vérifier service
if kobold.check_service():
    print("✅ KoboldCpp disponible sur http://localhost:5001")

# Appel chat
response, error = await kobold.call_chat_api(
    messages=[{"role": "user", "content": "Test"}],
    max_tokens=400,
    context_length=4096,
    temperature=0.8,
    is_json=False  # Pas de JSON mode natif
)
```

---

### AIHordeManager

**Rôle** : Accès gratuit et distribué via API AIHorde.

#### Caractéristiques

- ✅ **Gratuit** (avec clé anonyme ou compte)
- ⚠️ **Lent** (polling, 30s-2min selon charge réseau)
- 🌐 **Distribué** (workers communautaires)

#### Configuration

```python
aihorde = AIHordeManager()

aihorde.configure(
    api_key="0000000000",  # Anonyme (lent) ou vraie clé
    model="meta-llama/Meta-Llama-3.1-70B-Instruct"
)

# Lister modèles disponibles
models, error = await aihorde.list_models()
for model in models:
    print(f"- {model['name']} ({model['count']} workers)")
```

#### Appel avec polling

```python
# Génération avec polling automatique toutes les 5s
response, error = await aihorde.call_chat_api(
    messages=[{"role": "user", "content": "Question"}],
    max_tokens=200,
    context_length=8000,
    temperature=0.7,
    is_json=False
)

# Peut prendre 30s-2min selon charge
```

---

## 🎯 Patterns d'Usage Courants

### Pattern 1: Fallback Multi-Backends

```python
async def ask_with_fallback(question: str) -> str:
    """Essayer API cloud, puis Ollama, puis GGUF."""
    
    messages = [{"role": "user", "content": question}]
    
    # Tentative 1: API cloud (rapide)
    chat_controller.set_active_backend("API")
    if chat_controller.api_manager.api_key:
        response, error = await chat_controller.call_chat_api(
            messages, max_tokens=500, context_length=8000,
            temperature=0.7, is_json=False
        )
        if not error:
            return response
    
    # Tentative 2: Ollama local
    chat_controller.set_active_backend("OLLAMA")
    if chat_controller.ollama_manager.check_service():
        response, error = await chat_controller.call_chat_api(
            messages, max_tokens=500, context_length=8000,
            temperature=0.7, is_json=False
        )
        if not error:
            return response
    
    # Tentative 3: GGUF local
    chat_controller.set_active_backend("GGUF")
    if chat_controller.gguf_manager.model:
        response, error = await chat_controller.call_chat_api(
            messages, max_tokens=500, context_length=8000,
            temperature=0.7, is_json=False
        )
        if not error:
            return response
    
    return "❌ Aucun backend disponible"
```

### Pattern 2: Extraction JSON Robuste

```python
import json

async def extract_json_data(prompt: str) -> dict:
    """Force JSON mode + parsing robuste."""
    
    messages = [{"role": "user", "content": prompt}]
    
    response, error = await chat_controller.call_chat_api(
        messages=messages,
        max_tokens=1000,
        context_length=8000,
        temperature=0.1,  # Bas pour déterminisme
        is_json=True  # Force JSON mode
    )
    
    if error:
        raise Exception(f"API error: {error}")
    
    try:
        # Tentative parsing direct
        return json.loads(response)
    except json.JSONDecodeError:
        # Extraction entre ```json et ```
        import re
        match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        else:
            raise ValueError(f"Réponse non-JSON: {response}")
```

### Pattern 3: Batch Embeddings

```python
async def batch_embeddings(texts: List[str]) -> List[List[float]]:
    """Génération embeddings par batch (parallèle)."""
    
    import asyncio
    
    tasks = [
        embedding_controller.create_embedding(text)
        for text in texts
    ]
    
    # Parallèle avec limite concurrence
    semaphore = asyncio.Semaphore(5)  # Max 5 simultanés
    
    async def bounded_embedding(text):
        async with semaphore:
            return await embedding_controller.create_embedding(text)
    
    vectors = await asyncio.gather(*[
        bounded_embedding(text) for text in texts
    ])
    
    return [v for v in vectors if v is not None]
```

### Pattern 4: Streaming (si supporté)

```python
# Note: streaming non implémenté dans version actuelle
# Pour OpenAI streaming, utiliser directement SDK:

from openai import AsyncOpenAI

client = AsyncOpenAI(api_key="sk-...")

async def stream_response(question: str):
    stream = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": question}],
        stream=True
    )
    
    async for chunk in stream:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="")
```

---

## ⚠️ Gestion d'Erreurs

### Erreurs Courantes

#### 1. Backend non disponible

```python
response, error = await chat_controller.call_chat_api(...)

if error:
    if "Connection refused" in error:
        print("❌ Service local non démarré (Ollama/KoboldCpp)")
    elif "API key" in error:
        print("❌ Clé API invalide ou manquante")
    elif "Rate limit" in error:
        print("❌ Limite requêtes API atteinte")
    elif "timeout" in error:
        print("❌ Timeout (réseau ou modèle trop lent)")
```

#### 2. Modèle GGUF non chargé

```python
if not gguf_manager.model:
    print("❌ Aucun modèle GGUF chargé")
    success = gguf_manager.load_model(...)
    if not success:
        print("❌ Fichier GGUF introuvable ou corrompu")
```

#### 3. JSON parsing échoué

```python
try:
    data = json.loads(response)
except json.JSONDecodeError as e:
    print(f"❌ Réponse non-JSON: {e}")
    # Fallback: prompt engineering + retry
    messages.append({
        "role": "user",
        "content": "Reformule ta réponse en JSON pur, sans markdown"
    })
    response, _ = await chat_controller.call_chat_api(...)
```

### Pattern Retry avec Backoff

```python
import asyncio

async def call_with_retry(messages, max_retries=3):
    """Retry avec backoff exponentiel."""
    
    for attempt in range(max_retries):
        response, error = await chat_controller.call_chat_api(
            messages, max_tokens=500, context_length=8000,
            temperature=0.7, is_json=False
        )
        
        if not error:
            return response
        
        if "rate limit" in error.lower():
            wait_time = 2 ** attempt  # 1s, 2s, 4s
            print(f"Rate limit, attente {wait_time}s...")
            await asyncio.sleep(wait_time)
        else:
            raise Exception(error)
    
    raise Exception("Max retries atteint")
```

---

## 🔐 Sécurité et Best Practices

### 1. Gestion Clés API

```python
import os
from pathlib import Path

# NE JAMAIS hardcoder les clés
# ❌ api_key = "sk-abc123..."

# ✅ Variables d'environnement
api_key = os.getenv("OPENAI_API_KEY")

# ✅ Fichier .env (non versionné)
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

# ✅ SettingsManager (fichier settings.json)
settings = SettingsManager(Path("data/settings.json"))
settings.load_settings()
api_key = settings.settings["chat_api"]["api_key"]
```

### 2. Validation Input

```python
def validate_messages(messages: List[Dict]) -> bool:
    """Valider format messages."""
    
    for msg in messages:
        if "role" not in msg or "content" not in msg:
            return False
        if msg["role"] not in ["system", "user", "assistant"]:
            return False
        if not isinstance(msg["content"], str):
            return False
    return True

# Usage
if not validate_messages(messages):
    raise ValueError("Format messages invalide")
```

### 3. Limits et Quotas

```python
# Limiter tokens pour éviter coûts
MAX_TOKENS = 2000
MAX_CONTEXT = 32000

response, error = await chat_controller.call_chat_api(
    messages=messages[:50],  # Limiter historique
    max_tokens=min(MAX_TOKENS, 2000),
    context_length=MAX_CONTEXT,
    temperature=0.7,
    is_json=False
)
```

### 4. Logging Complet

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def logged_call(messages):
    logger.info(f"Appel API: {len(messages)} messages")
    
    response, error = await chat_controller.call_chat_api(
        messages, max_tokens=500, context_length=8000,
        temperature=0.7, is_json=False
    )
    
    if error:
        logger.error(f"Erreur API: {error}")
    else:
        logger.info(f"Réponse reçue: {len(response)} chars")
    
    return response, error
```

---

## 📊 Performances et Optimisation

### Benchmarks Approximatifs

| Backend | Latence | Throughput | Coût |
|---------|---------|------------|------|
| OpenAI GPT-4o-mini | 1-3s | ~100 tok/s | $$$ |
| Mistral Large | 2-4s | ~80 tok/s | $$ |
| Anthropic Claude | 2-5s | ~60 tok/s | $$$$ |
| Google Gemini Flash | 1-2s | ~120 tok/s | $ |
| Ollama (llama3.2) | 0.5-2s | ~50 tok/s (GPU) | Gratuit |
| GGUF (Q4) | 1-5s | ~20 tok/s (CPU) | Gratuit |
| KoboldCpp | 1-4s | ~30 tok/s | Gratuit |
| AIHorde | 30-120s | Variable | Gratuit |

### Tips Optimisation

#### 1. Choisir bon backend selon usage

```python
# Raisonnement complexe → API cloud (GPT-4, Claude)
# Chat simple → Ollama local
# Offline absolu → GGUF
# Gratuit sans limite → AIHorde (patience requise)
```

#### 2. Réduire tokens context

```python
# Tronquer historique ancien
def truncate_history(messages, max_messages=20):
    if len(messages) <= max_messages:
        return messages
    # Garder system prompt + N derniers messages
    system = [m for m in messages if m["role"] == "system"]
    recent = messages[-max_messages:]
    return system + recent
```

#### 3. Cache embeddings

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
async def cached_embedding(text: str):
    """Cache embeddings fréquents."""
    return await embedding_controller.create_embedding(text)
```

#### 4. GPU Layers GGUF

```python
# Plus de layers GPU = plus rapide (si VRAM suffisante)
# Modèle 7B: ~35 layers
# Modèle 13B: ~40 layers
# Modèle 70B: ~80 layers

gguf.load_model(
    model_filename="model.gguf",
    context_length=8000,
    n_gpu_layers=35  # Ajuster selon VRAM
)

# Vérifier usage VRAM:
# nvidia-smi  (Linux/Windows)
```

---

## 🧪 Tests et Validation

### Test Connexion Backend

```python
async def test_all_backends():
    """Tester tous les backends disponibles."""
    
    results = {}
    
    # Test API
    chat_controller.set_active_backend("API")
    if chat_controller.api_manager.api_key:
        response, error = await chat_controller.call_chat_api(
            [{"role": "user", "content": "ping"}],
            max_tokens=10, context_length=1000,
            temperature=0.1, is_json=False
        )
        results["API"] = "✅" if not error else f"❌ {error}"
    
    # Test Ollama
    chat_controller.set_active_backend("OLLAMA")
    if chat_controller.ollama_manager.check_service():
        response, error = await chat_controller.call_chat_api(
            [{"role": "user", "content": "ping"}],
            max_tokens=10, context_length=1000,
            temperature=0.1, is_json=False
        )
        results["OLLAMA"] = "✅" if not error else f"❌ {error}"
    else:
        results["OLLAMA"] = "❌ Service non disponible"
    
    # Test GGUF
    chat_controller.set_active_backend("GGUF")
    if chat_controller.gguf_manager.model:
        response, error = await chat_controller.call_chat_api(
            [{"role": "user", "content": "ping"}],
            max_tokens=10, context_length=1000,
            temperature=0.1, is_json=False
        )
        results["GGUF"] = "✅" if not error else f"❌ {error}"
    else:
        results["GGUF"] = "❌ Aucun modèle chargé"
    
    # Test KoboldCpp
    chat_controller.set_active_backend("KOBOLD")
    if chat_controller.kobold_manager.check_service():
        results["KOBOLD"] = "✅ Service disponible"
    else:
        results["KOBOLD"] = "❌ Service non disponible"
    
    return results
```

### Test Embedding

```python
async def test_embedding():
    """Tester génération embedding."""
    
    text = "Test embedding vectoriel"
    vector = await embedding_controller.create_embedding(text)
    
    assert vector is not None, "Embedding None"
    assert isinstance(vector, list), "Embedding pas une liste"
    assert len(vector) > 0, "Embedding vide"
    assert all(isinstance(x, float) for x in vector), "Valeurs non-float"
    
    print(f"✅ Embedding OK: {len(vector)} dimensions")
    return vector
```

---

## 📖 Exemples Complets

### Exemple 1: Chatbot Multi-Backend

```python
async def chatbot_session():
    """Session chatbot interactive avec fallback."""
    
    history = []
    
    print("Chatbot OGMA - Tapez 'quit' pour quitter")
    
    while True:
        user_input = input("\nVous: ")
        if user_input.lower() == "quit":
            break
        
        history.append({"role": "user", "content": user_input})
        
        # Tentative API cloud
        chat_controller.set_active_backend("API")
        response, error = await chat_controller.call_chat_api(
            messages=history[-10:],  # 10 derniers messages
            max_tokens=500,
            context_length=8000,
            temperature=0.7,
            is_json=False
        )
        
        if error:
            # Fallback Ollama
            print("⚠️ API error, fallback Ollama...")
            chat_controller.set_active_backend("OLLAMA")
            response, error = await chat_controller.call_chat_api(
                messages=history[-10:],
                max_tokens=500,
                context_length=8000,
                temperature=0.7,
                is_json=False
            )
        
        if error:
            print(f"❌ Erreur: {error}")
            history.pop()  # Retirer dernier message
        else:
            history.append({"role": "assistant", "content": response})
            print(f"\nAssistant: {response}")
```

### Exemple 2: Analyse JSON Structurée

```python
async def analyze_text_json(text: str) -> dict:
    """Analyse texte et retourne JSON structuré."""
    
    prompt = f"""Analyse le texte suivant et retourne un JSON avec:
- sentiment: "positif", "négatif" ou "neutre"
- topics: liste de sujets principaux
- summary: résumé en 1 phrase
- score_confiance: 0.0-1.0

Texte: {text}

Réponds UNIQUEMENT avec du JSON valide."""

    messages = [{"role": "user", "content": prompt}]
    
    response, error = await chat_controller.call_chat_api(
        messages=messages,
        max_tokens=500,
        context_length=8000,
        temperature=0.2,  # Bas pour cohérence
        is_json=True
    )
    
    if error:
        raise Exception(f"Erreur API: {error}")
    
    return json.loads(response)

# Usage
result = await analyze_text_json(
    "J'adore ce nouveau restaurant ! La cuisine est excellente."
)
print(result)
# {
#   "sentiment": "positif",
#   "topics": ["restaurant", "cuisine"],
#   "summary": "Avis très positif sur un restaurant",
#   "score_confiance": 0.95
# }
```

### Exemple 3: Recherche Sémantique

```python
async def semantic_search(query: str, documents: List[str], top_k=3):
    """Recherche sémantique dans documents."""
    
    # Générer embedding query
    query_vector = await embedding_controller.create_embedding(query)
    
    # Générer embeddings documents
    doc_vectors = await asyncio.gather(*[
        embedding_controller.create_embedding(doc)
        for doc in documents
    ])
    
    # Calculer similarité cosine
    import numpy as np
    
    def cosine_similarity(v1, v2):
        return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
    
    similarities = [
        (i, cosine_similarity(query_vector, doc_vec))
        for i, doc_vec in enumerate(doc_vectors)
        if doc_vec is not None
    ]
    
    # Trier et retourner top_k
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    results = [
        {"document": documents[i], "score": score}
        for i, score in similarities[:top_k]
    ]
    
    return results

# Usage
docs = [
    "Les chats sont des félins domestiques",
    "Python est un langage de programmation",
    "Les chiens sont des animaux loyaux"
]

results = await semantic_search("animaux de compagnie", docs, top_k=2)
for r in results:
    print(f"{r['score']:.2f} - {r['document']}")
# 0.87 - Les chats sont des félins domestiques
# 0.82 - Les chiens sont des animaux loyaux
```

---

## 🔗 Ressources

### Documentation Providers

- **OpenAI**: https://platform.openai.com/docs
- **Mistral**: https://docs.mistral.ai
- **Anthropic**: https://docs.anthropic.com
- **Google AI**: https://ai.google.dev/docs
- **Ollama**: https://ollama.ai/docs
- **llama.cpp**: https://github.com/ggerganov/llama.cpp

### Modèles Recommandés

#### Chat (par usage)
- **Qualité max**: Claude 3.5 Sonnet, GPT-4o
- **Bon rapport qualité/prix**: GPT-4o-mini, Mistral Large
- **Local rapide**: llama3.2:3b (Ollama), Qwen2.5:7b
- **Local qualité**: llama3.1:70b, Mixtral:8x7b

#### Embeddings
- **Production**: text-embedding-3-large (OpenAI)
- **Français**: mistral-embed
- **Local**: nomic-embed-text, mxbai-embed-large

### Fichiers GGUF

Télécharger sur **HuggingFace**:
- https://huggingface.co/models?library=gguf

Quantizations recommandées:
- **Q4_K_M**: Bon compromis qualité/taille
- **Q5_K_M**: Meilleure qualité, +20% taille
- **Q8_0**: Quasi-original, x2 taille

---

## 🎓 Conclusion

Le `core_logic.py` d'OGMA offre une **abstraction puissante et unifiée** pour tous les backends IA. Points clés:

✅ **8 backends supportés** (cloud + local)  
✅ **API cohérente** (`call_chat_api`, `create_embedding`)  
✅ **Fallback automatique** possible entre backends  
✅ **JSON mode** natif ou prompt engineering  
✅ **Multi-modal** (GGUF vision)  
✅ **Production-ready** (testé 28/28)

**Usage recommandé**:
1. Développement: Ollama local (rapide, gratuit)
2. Production: API cloud (qualité, scalabilité)
3. Offline: GGUF (autonomie totale)
4. Gratuit public: AIHorde (patience)

**Next steps**: Consulter `docs/testing/RAPPORT_VALIDATION_CORE_LOGIC.md` pour détails validations.

---

**Documentation maintenue par**: Équipe OGMA  
**Dernière mise à jour**: 5 novembre 2025
