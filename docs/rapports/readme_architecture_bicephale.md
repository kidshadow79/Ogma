# Architecture Bicéphale — Documentation Exhaustive

**Fichier principal** : `core_logic.py`  
**Concept** : OGMA possède deux "cerveaux IA" indépendants + un moteur d'embeddings, tous orchestrés par `AIController`, avec gestion multi-provider (7 APIs cloud + 3 backends locaux).

---

## Vue d'ensemble

```
ogma_ng.py
    ↓
AIController (chat_controller)     ← IA Principale (T=0.7, conversationnel)
AIController (archiviste_controller) ← Archiviste (T=0.3, analytique)
AIController (embedding_controller)  ← Embeddings (spécialisé)
    ↓
APIManager | OllamaManager | GGUFManager | KoboldManager
    ↓
Provider: OpenAI | Anthropic | Mistral | Google | GROK | OpenRouter | AIHorde
```

---

## `SettingsManager`

**Rôle** : Charge/sauvegarde `data/settings.json` avec protection et backup.

### `__init__(settings_path)`

| Attribut | Description |
|----------|-------------|
| `_settings` | `dict` — config en mémoire |
| `_load_failed` | `bool` — si True, interdit toute sauvegarde |
| `_backup_count` | Max 4 backups rotatifs |

### Chargement

**`_load_settings()`** :
1. Ouvre `data/settings.json`
2. Si JSON invalide → load `data/settings.backup_last.json`
3. Si toujours invalide → `_load_failed = True`, retourne defaults
4. `_merge_with_defaults(loaded, defaults)` — merge récursif : valeurs chargées prioritaires

**`_merge_with_defaults(loaded, defaults)`** — merge récursif :
- Clés manquantes dans loaded → ajoutées depuis defaults
- Clés existantes dans loaded → préservées (même si defaults est différent)
- Profondeur : récursif sur sous-dicts

### Sauvegarde

**`save_settings()`** :
1. Si `_load_failed` → interdit (log warning, retourne False)
2. Crée backup rotatif : `settings.backup_{1..4}.json`
3. Écrit JSON formaté (indent=2)

### Méthodes

| Méthode | Description |
|---------|-------------|
| `get(key, default)` | Lecture avec chemin imbriqué supporté (`"chat_api.provider"`) |
| `set(key, value)` | Écriture + `save_settings()` |
| `get_controller_config(controller_name)` | Retourne sous-dict d'un contrôleur |
| `update_controller_config(name, updates)` | Merge partiel + save |
| `get_api_key(provider)` | Extrait clé API depuis config |

---

## `APIManager`

### 7 Providers supportés

| Provider | Clé config | Endpoint base |
|----------|-----------|----------------|
| `openai` | `openai_api_key` | `https://api.openai.com/v1` |
| `anthropic` | `anthropic_api_key` | `https://api.anthropic.com/v1` |
| `mistral` | `mistral_api_key` | `https://api.mistral.ai/v1` |
| `google` | `google_api_key` | `https://generativelanguage.googleapis.com/v1beta` |
| `grok` | `grok_api_key` | `https://api.x.ai/v1` |
| `openrouter` | `openrouter_api_key` | `https://openrouter.ai/api/v1` |
| `aihorde` | `aihorde_api_key` | `https://aihorde.net/api/v2` |

### Streaming SSE

**`async call_chat_api_streaming(messages, config, on_token_callback, stop_signal)`** :
1. Sélectionne provider depuis `config.provider`
2. Prépare headers (Authorization Bearer ou x-api-key selon provider)
3. `httpx.AsyncClient().stream("POST", endpoint)` avec timeout configurable
4. Parse SSE : `data: {...}` → extrait `delta.content` (OpenAI format) ou équivalent
5. Appelle `on_token_callback(token)` pour chaque token
6. Vérifie `stop_signal.is_set()` à chaque chunk → interrompt si True

### Extended Thinking (6 providers)

Providers supportant le mode "thinking" (raisonnement étendu) :
- `anthropic` : `thinking: {type: "enabled", budget_tokens: N}`
- `openai` : modèles `o1`, `o3-mini` (pas de `temperature`)
- `google` : `generationConfig.thinkingConfig`
- `mistral` : via paramètre spécifique modèle
- `grok` : paramètre thinking
- `openrouter` : forward vers modèle sous-jacent

**`_build_request_body(messages, config, thinking_mode)`** :
- Si `thinking_mode` → ajoute paramètres spécifiques provider
- Si OpenAI o1/o3 → retire `temperature`, `system message` (pas supporté)

### Format Anthropic (conversion)

OpenAI format → Anthropic :
- `messages[0].role == "system"` → extrait comme `system` top-level
- `role: "assistant"` → `role: "assistant"`
- `role: "user"` → `role: "user"`
- Images → `content: [{type: "image", source: {type: "base64", ...}}]`

### Format Google (conversion)

- `contents: [{role: "user/model", parts: [{text: ...}]}]`
- System message → `systemInstruction: {parts: [{text: ...}]}`
- Images → `parts: [{inlineData: {mimeType, data}}]`

### AIHorde

- Génération asynchrone avec polling : `POST /generate/async` → `GET /generate/check/{id}` → `GET /generate/status/{id}`
- Pas de streaming (polling)

---

## `AIController`

**Classe centrale** — orchestre le bon backend selon `backend_type`.

### `__init__(config_dict, settings_manager)`

| Attribut | Description |
|----------|-------------|
| `provider` | Nom provider (ex. `"openai"`) |
| `backend_type` | `"API"`, `"OLLAMA"`, `"GGUF"`, `"KOBOLD"` |
| `api_model` | Modèle utilisé |
| `temperature` | Float (0.0-2.0) |
| `max_tokens` | Int |
| `system_prompt` | Injected at call time |
| `_manager` | Instance APIManager/OllamaManager/GGUFManager/KoboldManager |

### `_map_backend_for_controller(provider, backend_type)` → Classe manager

| backend_type | Classe |
|-------------|--------|
| `"API"` | `APIManager` |
| `"OLLAMA"` | `OllamaManager` |
| `"GGUF"` | `GGUFManager` |
| `"KOBOLD"` | `KoboldManager` |

### `async call_streaming(messages, on_token, stop_signal, override_config)`

Route vers `_manager.call_chat_api_streaming()` (API) ou équivalent local.

### `calculate_memory_impact_score(memory_item)` → `float` (0.0-1.0)

**Formule multi-facteurs** :

| Facteur | Poids | Description |
|---------|-------|-------------|
| Importance explicite | 30% | Score attaché au souvenir (0-10) → normalisé |
| Récence | 25% | Exponentielle décroissante selon âge (jours) |
| Fréquence d'accès | 20% | Nombre d'accès normalisé (log scale) |
| Pertinence vectorielle | 25% | Score cosine similarity avec contexte courant |

Résultat utilisé par `IntelligentMemoryAI` pour prioriser les souvenirs à injecter.

### `async get_embedding(text)` → `list[float]`

Pour le contrôleur embedding uniquement :
- Providers API : `POST /embeddings` (OpenAI format)
- Ollama : `POST /api/embeddings` avec modèle embedding
- Format retour : vecteur float normalisé

---

## `OllamaManager`

**Dépendance** : Ollama local (`http://localhost:11434`)

### Options RTX 5070 Ti

Config spéciale haute performance :
```json
{
  "num_gpu": 999,
  "num_thread": 16,
  "numa": false,
  "low_vram": false,
  "f16_kv": true
}
```

### Multimodal

Si message contient base64 image → injecte dans `images: [base64]` du body Ollama (modèles LLaVA, BakLLaVA, etc.)

### Streaming

`POST /api/chat` avec `stream: true` → JSON newline-delimited.

---

## `GGUFManager`

**Dépendance** : `llama-cpp-python`

### `__init__`

- Charge modèle GGUF depuis chemin config
- `LlamaLlavaChatHandler` si modèle multimodal (LLaVA)
- Paramètres : `n_ctx` (context window), `n_gpu_layers` (offload GPU), `verbose`

### Correction alternance Gemma

**Problème** : Certains modèles Gemma requièrent alternance stricte user/assistant.  
**Correction** : `_fix_gemma_alternation(messages)` — si deux messages consécutifs du même rôle → fusionne ou insère message neutre.

### Streaming local

`Llama.__call__()` avec `stream=True` → iterator de tokens.

---

## `KoboldManager`

**Endpoint** : KoboldCpp API (`http://localhost:5001` par défaut)

### `call_chat_api_streaming(messages, config, on_token, stop_signal)`

- `GET /api/v1/info/version` pour vérifier disponibilité
- `POST /api/extra/generate/stream` pour streaming SSE
- Compatible KoboldAI et KoboldCpp

---

## Configuration `data/settings.json` — Structure par contrôleur

```json
{
  "chat_api": {
    "provider": "openai",
    "api_key": "sk-...",
    "api_model": "gpt-4o",
    "backend_type": "API",
    "temperature": 0.7,
    "max_tokens": 2048,
    "top_p": 0.95,
    "extended_thinking": false
  },
  "archiviste_api": {
    "provider": "anthropic",
    "api_key": "sk-ant-...",
    "api_model": "claude-3-5-haiku-20241022",
    "backend_type": "API",
    "temperature": 0.3,
    "max_tokens": 1024
  },
  "embedding_api": {
    "provider": "openai",
    "api_key": "sk-...",
    "api_model": "text-embedding-3-small",
    "backend_type": "API"
  }
}
```

---

## Variables globales dans `ogma_ng.py`

| Variable | Type | Description |
|----------|------|-------------|
| `_chat_controller` | `Optional[AIController]` | IA Principale |
| `_archiviste_controller` | `Optional[AIController]` | Archiviste |
| `_embedding_controller` | `Optional[AIController]` | Embeddings |
| `_settings_manager` | `Optional[SettingsManager]` | Config persistée |

**Accès** toujours via `_ensure_chat_controller()`, `_ensure_archiviste_controller()`, etc. (lazy init pattern).
