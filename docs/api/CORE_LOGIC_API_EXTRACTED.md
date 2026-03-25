# Memory Manager - API Extraite Automatiquement

**Source** : `memory_manager.py`  
**Date extraction** : 5 novembre 2025  
**Méthode** : Analyse AST Python

---

## 📋 Table des Matières

- [__init__()](#---init--)
- [calculate_memory_impact_score()](#-calculate-memory-impact-score)
- [set_active_backend()](#-set-active-backend)
- [get_active_manager()](#-get-active-manager)
- [get_status()](#-get-status)
- [call_chat_api()](#-call-chat-api)
- [__init__()](#---init--)
- [configure()](#-configure)
- [list_models()](#-list-models)
- [call_chat_api()](#-call-chat-api)
- [create_embedding()](#-create-embedding)
- [__init__()](#---init--)
- [configure()](#-configure)
- [list_models()](#-list-models)
- [call_chat_api()](#-call-chat-api)
- [create_embedding()](#-create-embedding)
- [__init__()](#---init--)
- [configure()](#-configure)
- [create_embedding()](#-create-embedding)
- [get_status()](#-get-status)
- [__init__()](#---init--)
- [set_settings_manager()](#-set-settings-manager)
- [get_low_vram_setting()](#-get-low-vram-setting)
- [get_available_models()](#-get-available-models)
- [load_model()](#-load-model)
- [call_chat_api()](#-call-chat-api)
- [create_embedding()](#-create-embedding)
- [list_models()](#-list-models)
- [test_connection()](#-test-connection)
- [__init__()](#---init--)
- [process_memorization_request()](#-process-memorization-request)
- [find_relevant_memories()](#-find-relevant-memories)
- [get_context_injection()](#-get-context-injection)
- [get_conversation_context_injection()](#-get-conversation-context-injection)
- [__init__()](#---init--)
- [check_service()](#-check-service)
- [call_chat_api()](#-call-chat-api)
- [__init__()](#---init--)
- [load_memories()](#-load-memories)
- [save_memories()](#-save-memories)
- [add_memory()](#-add-memory)
- [delete_memory()](#-delete-memory)
- [index_existing_memories()](#-index-existing-memories)
- [__init__()](#---init--)
- [set_settings_manager()](#-set-settings-manager)
- [get_low_vram_setting()](#-get-low-vram-setting)
- [check_service()](#-check-service)
- [call_chat_api()](#-call-chat-api)
- [create_embedding()](#-create-embedding)
- [list_models()](#-list-models)
- [__init__()](#---init--)
- [load_settings()](#-load-settings)
- [save_settings()](#-save-settings)

---

## 📚 Signatures Complètes

### `__init__()`

**Ligne** : 1152  
**Classe** : AIController  
**Type** : 🔄 Sync

**Signature** :
```python
def __init__(
    self: Any,
    ai_type: str,
    ollama_manager: OllamaManager,
    gguf_manager: GGUFManager,
    kobold_manager: KoboldManager
) -> Any
```

**Description** :
Non documenté

---

### `calculate_memory_impact_score()`

**Ligne** : 1157  
**Classe** : AIController  
**Type** : ⚡ Async

**Signature** :
```python
async def calculate_memory_impact_score(
    self: Any,
    text_content: str,
    conversation_context: str,
    interlocutor: str
) -> Optional[float]
```

**Description** :
Calcule le score d'impact mémoriel avec l'IA Principale selon la formule exacte de l'Archiviste.

Formule : score = intensité × base_factor × (liberté + création + procréation + intensité_contextuelle)

Returns:
    Optional[float]: Score calculé selon la formule, ou None si échec (pas de fallback)

---

### `set_active_backend()`

**Ligne** : 1328  
**Classe** : AIController  
**Type** : 🔄 Sync

**Signature** :
```python
def set_active_backend(
    self: Any,
    backend_type: str
) -> Any
```

**Description** :
Non documenté

---

### `get_active_manager()`

**Ligne** : 1332  
**Classe** : AIController  
**Type** : 🔄 Sync

**Signature** :
```python
def get_active_manager(
    self: Any
) -> Any
```

**Description** :
Non documenté

---

### `get_status()`

**Ligne** : 1345  
**Classe** : AIController  
**Type** : 🔄 Sync

**Signature** :
```python
def get_status(
    self: Any
) -> str
```

**Description** :
Non documenté

---

### `call_chat_api()`

**Ligne** : 1356  
**Classe** : AIController  
**Type** : ⚡ Async

**Signature** :
```python
async def call_chat_api(
    self: Any,
    messages: List[Dict],
    max_tokens: int,
    context_length: int,
    temperature: float,
    is_json: bool
) -> tuple[Optional[str], Optional[str]]
```

**Description** :
Non documenté

---

### `__init__()`

**Ligne** : 1617  
**Classe** : AIHordeManager  
**Type** : 🔄 Sync

**Signature** :
```python
def __init__(
    self: Any
) -> Any
```

**Description** :
Non documenté

---

### `configure()`

**Ligne** : 1625  
**Classe** : AIHordeManager  
**Type** : 🔄 Sync

**Signature** :
```python
def configure(
    self: Any,
    api_key: str,
    model: str
) -> Any
```

**Description** :
Non documenté

---

### `list_models()`

**Ligne** : 1633  
**Classe** : AIHordeManager  
**Type** : ⚡ Async

**Signature** :
```python
async def list_models(
    self: Any
) -> Tuple[List[str], Optional[str]]
```

**Description** :
Non documenté

---

### `call_chat_api()`

**Ligne** : 1644  
**Classe** : AIHordeManager  
**Type** : ⚡ Async

**Signature** :
```python
async def call_chat_api(
    self: Any,
    messages: List[Dict],
    max_tokens: int,
    context_length: int,
    temperature: float,
    is_json: bool
) -> tuple[Optional[str], Optional[str]]
```

**Description** :
Non documenté

---

### `create_embedding()`

**Ligne** : 1703  
**Classe** : AIHordeManager  
**Type** : ⚡ Async

**Signature** :
```python
async def create_embedding(
    self: Any,
    text: str
) -> Optional[List[float]]
```

**Description** :
Non documenté

---

### `__init__()`

**Ligne** : 510  
**Classe** : APIManager  
**Type** : 🔄 Sync

**Signature** :
```python
def __init__(
    self: Any
) -> Any
```

**Description** :
Non documenté

---

### `configure()`

**Ligne** : 512  
**Classe** : APIManager  
**Type** : 🔄 Sync

**Signature** :
```python
def configure(
    self: Any,
    provider: str,
    api_key: str,
    model: str
) -> Any
```

**Description** :
Non documenté

---

### `list_models()`

**Ligne** : 518  
**Classe** : APIManager  
**Type** : ⚡ Async

**Signature** :
```python
async def list_models(
    self: Any,
    api_key: str,
    provider: str
) -> Tuple[List[str], Optional[str]]
```

**Description** :
Non documenté

---

### `call_chat_api()`

**Ligne** : 687  
**Classe** : APIManager  
**Type** : ⚡ Async

**Signature** :
```python
async def call_chat_api(
    self: Any,
    messages: List[Dict],
    max_tokens: int,
    context_length: int,
    temperature: float,
    is_json: bool
) -> tuple[Optional[str], Optional[str]]
```

**Description** :
Non documenté

---

### `create_embedding()`

**Ligne** : 1008  
**Classe** : APIManager  
**Type** : ⚡ Async

**Signature** :
```python
async def create_embedding(
    self: Any,
    text: str
) -> Optional[List[float]]
```

**Description** :
Non documenté

---

### `__init__()`

**Ligne** : 1366  
**Classe** : EmbeddingController  
**Type** : 🔄 Sync

**Signature** :
```python
def __init__(
    self: Any,
    ollama_manager: OllamaManager,
    gguf_manager: GGUFManager
) -> Any
```

**Description** :
Non documenté

---

### `configure()`

**Ligne** : 1370  
**Classe** : EmbeddingController  
**Type** : 🔄 Sync

**Signature** :
```python
def configure(
    self: Any,
    backend_type: Any,
    api_provider: Any,
    api_key: Any,
    api_model: Any,
    ollama_model: Any,
    gguf_model: Any
) -> Any
```

**Description** :
Non documenté

---

### `create_embedding()`

**Ligne** : 1392  
**Classe** : EmbeddingController  
**Type** : ⚡ Async

**Signature** :
```python
async def create_embedding(
    self: Any,
    text: str
) -> Optional[List[float]]
```

**Description** :
Non documenté

---

### `get_status()`

**Ligne** : 1406  
**Classe** : EmbeddingController  
**Type** : 🔄 Sync

**Signature** :
```python
def get_status(
    self: Any
) -> str
```

**Description** :
Non documenté

---

### `__init__()`

**Ligne** : 257  
**Classe** : GGUFManager  
**Type** : 🔄 Sync

**Signature** :
```python
def __init__(
    self: Any
) -> Any
```

**Description** :
Non documenté

---

### `set_settings_manager()`

**Ligne** : 263  
**Classe** : GGUFManager  
**Type** : 🔄 Sync

**Signature** :
```python
def set_settings_manager(
    self: Any,
    settings_manager: Any
) -> Any
```

**Description** :
Configure le gestionnaire de paramètres pour accéder aux settings.

---

### `get_low_vram_setting()`

**Ligne** : 267  
**Classe** : GGUFManager  
**Type** : 🔄 Sync

**Signature** :
```python
def get_low_vram_setting(
    self: Any
) -> bool
```

**Description** :
Récupère le paramètre low_vram depuis les settings.

---

### `get_available_models()`

**Ligne** : 272  
**Classe** : GGUFManager  
**Type** : 🔄 Sync

**Signature** :
```python
def get_available_models(
    self: Any
) -> List[str]
```

**Description** :
Non documenté

---

### `load_model()`

**Ligne** : 275  
**Classe** : GGUFManager  
**Type** : 🔄 Sync

**Signature** :
```python
def load_model(
    self: Any,
    model_filename: str,
    context_length: int,
    n_gpu_layers: int,
    projector_filename: Optional[str]
) -> bool
```

**Description** :
Non documenté

---

### `call_chat_api()`

**Ligne** : 333  
**Classe** : GGUFManager  
**Type** : ⚡ Async

**Signature** :
```python
async def call_chat_api(
    self: Any,
    messages: List[Dict],
    max_tokens: int,
    context_length: int,
    temperature: float,
    is_json: bool
) -> tuple[Optional[str], Optional[str]]
```

**Description** :
Non documenté

---

### `create_embedding()`

**Ligne** : 399  
**Classe** : GGUFManager  
**Type** : ⚡ Async

**Signature** :
```python
async def create_embedding(
    self: Any,
    text: str
) -> Optional[List[float]]
```

**Description** :
Non documenté

---

### `list_models()`

**Ligne** : 404  
**Classe** : GGUFManager  
**Type** : 🔄 Sync

**Signature** :
```python
def list_models(
    self: Any
) -> List[str]
```

**Description** :
Retourne la liste des modèles GGUF disponibles ou le modèle chargé.

---

### `test_connection()`

**Ligne** : 410  
**Classe** : GGUFManager  
**Type** : 🔄 Sync

**Signature** :
```python
def test_connection(
    self: Any
) -> Tuple[bool, str]
```

**Description** :
Teste si le modèle GGUF est chargé et disponible.

---

### `__init__()`

**Ligne** : 1418  
**Classe** : IntelligentMemoryAI  
**Type** : 🔄 Sync

**Signature** :
```python
def __init__(
    self: Any,
    mem_struct: MemoryStructure,
    memory_controller: AIController,
    embed_controller: EmbeddingController,
    settings_manager: SettingsManager,
    status_queue: Any
) -> Any
```

**Description** :
Non documenté

---

### `process_memorization_request()`

**Ligne** : 1420  
**Classe** : IntelligentMemoryAI  
**Type** : ⚡ Async

**Signature** :
```python
async def process_memorization_request(
    self: Any,
    content: str,
    history: Optional[List[Dict]]
) -> Any
```

**Description** :
Non documenté

---

### `find_relevant_memories()`

**Ligne** : 1472  
**Classe** : IntelligentMemoryAI  
**Type** : ⚡ Async

**Signature** :
```python
async def find_relevant_memories(
    self: Any,
    query_text: str,
    top_k: int
) -> List[Dict[str, Any]]
```

**Description** :
Non documenté

---

### `get_context_injection()`

**Ligne** : 1488  
**Classe** : IntelligentMemoryAI  
**Type** : ⚡ Async

**Signature** :
```python
async def get_context_injection(
    self: Any,
    user_question: str
) -> str
```

**Description** :
Non documenté

---

### `get_conversation_context_injection()`

**Ligne** : 1514  
**Classe** : IntelligentMemoryAI  
**Type** : ⚡ Async

**Signature** :
```python
async def get_conversation_context_injection(
    self: Any,
    user_question: str,
    history: List[Dict]
) -> str
```

**Description** :
Recherche et injecte automatiquement le contexte conversationnel pertinent.

---

### `__init__()`

**Ligne** : 419  
**Classe** : KoboldManager  
**Type** : 🔄 Sync

**Signature** :
```python
def __init__(
    self: Any
) -> Any
```

**Description** :
Non documenté

---

### `check_service()`

**Ligne** : 421  
**Classe** : KoboldManager  
**Type** : 🔄 Sync

**Signature** :
```python
def check_service(
    self: Any
) -> bool
```

**Description** :
Non documenté

---

### `call_chat_api()`

**Ligne** : 434  
**Classe** : KoboldManager  
**Type** : ⚡ Async

**Signature** :
```python
async def call_chat_api(
    self: Any,
    messages: List[Dict],
    max_tokens: int,
    context_length: int,
    temperature: float,
    is_json: bool
) -> tuple[Optional[str], Optional[str]]
```

**Description** :
Non documenté

---

### `__init__()`

**Ligne** : 1030  
**Classe** : MemoryStructure  
**Type** : 🔄 Sync

**Signature** :
```python
def __init__(
    self: Any,
    filepath: Path,
    status_queue: Any
) -> Any
```

**Description** :
Non documenté

---

### `load_memories()`

**Ligne** : 1037  
**Classe** : MemoryStructure  
**Type** : 🔄 Sync

**Signature** :
```python
def load_memories(
    self: Any
) -> Any
```

**Description** :
Non documenté

---

### `save_memories()`

**Ligne** : 1075  
**Classe** : MemoryStructure  
**Type** : 🔄 Sync

**Signature** :
```python
def save_memories(
    self: Any
) -> Any
```

**Description** :
Non documenté

---

### `add_memory()`

**Ligne** : 1115  
**Classe** : MemoryStructure  
**Type** : 🔄 Sync

**Signature** :
```python
def add_memory(
    self: Any,
    res: Dict[str, Any],
    text: str,
    vector: Optional[List[float]]
) -> Any
```

**Description** :
Non documenté

---

### `delete_memory()`

**Ligne** : 1120  
**Classe** : MemoryStructure  
**Type** : 🔄 Sync

**Signature** :
```python
def delete_memory(
    self: Any,
    memory_id: str
) -> str
```

**Description** :
Non documenté

---

### `index_existing_memories()`

**Ligne** : 1131  
**Classe** : MemoryStructure  
**Type** : ⚡ Async

**Signature** :
```python
async def index_existing_memories(
    self: Any,
    embed_manager: 'EmbeddingController',
    settings_manager: 'SettingsManager'
) -> str
```

**Description** :
Non documenté

---

### `__init__()`

**Ligne** : 145  
**Classe** : OllamaManager  
**Type** : 🔄 Sync

**Signature** :
```python
def __init__(
    self: Any
) -> Any
```

**Description** :
Non documenté

---

### `set_settings_manager()`

**Ligne** : 149  
**Classe** : OllamaManager  
**Type** : 🔄 Sync

**Signature** :
```python
def set_settings_manager(
    self: Any,
    settings_manager: Any
) -> Any
```

**Description** :
Configure le gestionnaire de paramètres pour accéder aux settings.

---

### `get_low_vram_setting()`

**Ligne** : 153  
**Classe** : OllamaManager  
**Type** : 🔄 Sync

**Signature** :
```python
def get_low_vram_setting(
    self: Any
) -> bool
```

**Description** :
Récupère le paramètre low_vram depuis les settings.

---

### `check_service()`

**Ligne** : 158  
**Classe** : OllamaManager  
**Type** : 🔄 Sync

**Signature** :
```python
def check_service(
    self: Any
) -> bool
```

**Description** :
Non documenté

---

### `call_chat_api()`

**Ligne** : 172  
**Classe** : OllamaManager  
**Type** : ⚡ Async

**Signature** :
```python
async def call_chat_api(
    self: Any,
    model: str,
    messages: List[Dict],
    max_tokens: int,
    context_length: int,
    temperature: float,
    is_json: bool
) -> tuple[Optional[str], Optional[str]]
```

**Description** :
Non documenté

---

### `create_embedding()`

**Ligne** : 237  
**Classe** : OllamaManager  
**Type** : ⚡ Async

**Signature** :
```python
async def create_embedding(
    self: Any,
    model: str,
    text: str
) -> Optional[List[float]]
```

**Description** :
Non documenté

---

### `list_models()`

**Ligne** : 249  
**Classe** : OllamaManager  
**Type** : ⚡ Async

**Signature** :
```python
async def list_models(
    self: Any
) -> List[str]
```

**Description** :
Retourne la liste des modèles disponibles dans Ollama.

---

### `__init__()`

**Ligne** : 47  
**Classe** : SettingsManager  
**Type** : 🔄 Sync

**Signature** :
```python
def __init__(
    self: Any,
    filepath: Path
) -> Any
```

**Description** :
Non documenté

---

### `load_settings()`

**Ligne** : 119  
**Classe** : SettingsManager  
**Type** : 🔄 Sync

**Signature** :
```python
def load_settings(
    self: Any
) -> Any
```

**Description** :
Non documenté

---

### `save_settings()`

**Ligne** : 134  
**Classe** : SettingsManager  
**Type** : 🔄 Sync

**Signature** :
```python
def save_settings(
    self: Any
) -> Any
```

**Description** :
Non documenté

---


## 📊 Statistiques

- **Total méthodes publiques** : 53
- **Méthodes async** : 20 (⚡)
- **Méthodes sync** : 33 (🔄)
- **Classes** : 10

---

**Note** : Ce document est généré automatiquement. Pour usage détaillé, consulter le code source.
