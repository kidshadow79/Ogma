# API Controllers OGMA - Documentation Complète

**Date d'extraction**: 2025-11-05  
**Fichier source**: `core_logic.py`  
**Composants**: AIController, EmbeddingController  

---

## Vue d'Ensemble

Les **Controllers OGMA** orchestrent l'intelligence artificielle multi-providers avec:
- **AIController**: Chat conversationnel (Luna, Archiviste)
- **EmbeddingController**: Vectorisation mémoire

### Architecture Multi-Providers

```
┌────────────────────────────────────────┐
│         AIController                   │
├────────────────────────────────────────┤
│  Backend Router (4 backends)           │
│  ├─> API (OpenAI, Anthropic, etc.)    │
│  ├─> Ollama (local models)            │
│  ├─> GGUF/llama.cpp (VRAM optimize)   │
│  └─> KoboldCpp (community models)     │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│      EmbeddingController               │
├────────────────────────────────────────┤
│  Embedding Router (3 backends)         │
│  ├─> API (OpenAI, Mistral, Google)    │
│  ├─> Ollama (local embeddings)        │
│  └─> GGUF (local embeddings)          │
└────────────────────────────────────────┘
```

---

## API Publique - AIController

### 1. `__init__(ai_type, ollama_manager, gguf_manager, kobold_manager)`

**Description**:  
Initialise le contrôleur IA avec type (Chat/Archiviste) et managers backend.

**Paramètres**:
- `ai_type` (str): "Chat" ou "Archiviste"
- `ollama_manager` (OllamaManager): Gestionnaire Ollama
- `gguf_manager` (GGUFManager): Gestionnaire GGUF/llama.cpp
- `kobold_manager` (KoboldManager): Gestionnaire KoboldCpp

**Side Effects**:
- Crée instances APIManager, AIHordeManager
- Initialise backend_type = "API" (défaut)
- Configure paramètres: max_tokens=512, context_length=4096, temperature=0.7

---

### 2. `async calculate_memory_impact_score(text_content, conversation_context, interlocutor) -> Optional[float]`

**Description**:  
Calcule le score d'impact mémoriel avec formule Archiviste.

**Formule**:  
`score = intensite × base_factor × (liberté + création + procréation + intensité_contextuelle)`

**Paramètres**:
- `text_content` (str): Texte à scorer
- `conversation_context` (str): Contexte conversation (optionnel)
- `interlocutor` (str): Nom interlocuteur (optionnel)

**Retour**: `Optional[float]`
- Score calculé (0-400 typiquement)
- `None` si échec (pas de fallback)

**Process**:
1. Construit prompt scoring avec formule
2. Appel IA pour extraire métriques (JSON)
3. Parse réponse (avec nettoyage thinking format)
4. Applique formule mathématique
5. Retourne score ou None

---

### 3. `set_active_backend(backend_type: str)`

**Description**:  
Change le backend actif pour ce contrôleur.

**Paramètres**:
- `backend_type` (str): "API", "Ollama", "GGUF", "KoboldCpp", "AIHorde"

**Side Effect**: Modifie `self.backend_type`

---

### 4. `get_active_manager() -> Optional[Manager]`

**Description**:  
Retourne le manager actif selon backend_type configuré.

**Retour**: 
- `APIManager` si backend="API"
- `OllamaManager` si backend="Ollama"
- `GGUFManager` si backend="GGUF"
- `KoboldManager` si backend="KoboldCpp"
- `AIHordeManager` si backend="AIHorde"
- `None` si backend invalide ou indisponible

---

### 5. `get_status() -> str`

**Description**:  
Retourne statut actuel du contrôleur (pour UI).

**Retour**: 
- `"[OFF] Inactif"` si aucun manager actif
- `"API: {provider}"` si backend=API
- `"Ollama: {model}"` si backend=Ollama
- `"GGUF: {model_name}"` si backend=GGUF
- `"KoboldCpp"` si backend=KoboldCpp
- `"Horde: {model}"` si backend=AIHorde
- `"[UNK] Inconnu"` si type non reconnu

---

### 6. `async call_chat_api(messages, max_tokens, context_length, temperature, is_json=True) -> Tuple[Optional[str], Optional[str]]`

**Description**:  
Appel chat API via le backend actif. Méthode critique orchestrant tous les providers.

**Paramètres**:
- `messages` (List[Dict]): Historique messages format OpenAI
  ```python
  [{"role": "system", "content": "..."}, {"role": "user", "content": "..."}]
  ```
- `max_tokens` (int): Tokens max génération (-1 = auto)
- `context_length` (int): Taille contexte (-1 = auto)
- `temperature` (float): 0.0-2.0 (créativité)
- `is_json` (bool): Force format JSON (défaut True)

**Retour**: `Tuple[Optional[str], Optional[str]]`
- `(response, None)` si succès (response = texte généré)
- `(None, error_message)` si échec

**Process**:
1. Récupère manager actif
2. Route selon backend_type:
   - Ollama: Ajoute `ollama_model` comme 1er paramètre
   - Autres: Appel direct au manager
3. Retourne réponse ou erreur

**Exemple**:
```python
messages = [
    {"role": "system", "content": "Tu es Luna"},
    {"role": "user", "content": "Salut !"}
]
response, error = await controller.call_chat_api(
    messages, max_tokens=512, context_length=4096, temperature=0.7
)
if error:
    print(f"Erreur: {error}")
else:
    print(f"Réponse IA: {response}")
```

---

## API Publique - EmbeddingController

### 1. `__init__(ollama_manager, gguf_manager)`

**Description**:  
Initialise le contrôleur d'embeddings.

**Paramètres**:
- `ollama_manager` (OllamaManager): Gestionnaire Ollama
- `gguf_manager` (GGUFManager): Gestionnaire GGUF/llama.cpp

**Side Effects**:
- Crée instances APIManager, AIHordeManager
- Initialise is_available=False, backend_type="API"
- ollama_model="mistral:latest" (défaut)

---

### 2. `configure(backend_type, api_provider=None, api_key=None, api_model=None, ollama_model=None, gguf_model=None)`

**Description**:  
Configure le backend pour embeddings.

**Paramètres**:
- `backend_type` (str): "API", "Ollama", "GGUF", "AIHorde"
- `api_provider` (str): Provider API (OpenAI, Mistral, Google)
- `api_key` (str): Clé API
- `api_model` (str): Modèle API (ex: "text-embedding-3-small")
- `ollama_model` (str): Modèle Ollama (ex: "mistral:latest")
- `gguf_model` (str): Chemin modèle GGUF

**Side Effect**: 
- Configure manager approprié
- Met à jour `self.is_available`

---

### 3. `async create_embedding(text: str) -> Optional[List[float]]`

**Description**:  
Crée un vecteur d'embedding pour le texte donné.

**Paramètres**:
- `text` (str): Texte à vectoriser

**Retour**: `Optional[List[float]]`
- Liste floats (dimension 384-1536 selon provider)
- `None` si échec ou provider indisponible

**Process**:
1. Vérifie backend configuré et disponible
2. Route selon backend_type:
   - API: `api_manager.create_embedding(text)`
   - Ollama: `ollama_manager.create_embedding(ollama_model, text)`
   - GGUF: `gguf_manager.create_embedding(text)`
   - AIHorde: `horde_manager.create_embedding(text)`
3. Retourne vecteur ou None

**Exemple**:
```python
# Configuration
controller.configure(
    backend_type="API",
    api_provider="OpenAI",
    api_key="sk-...",
    api_model="text-embedding-3-small"
)

# Embedding
vector = await controller.create_embedding("Bonjour OGMA")
if vector:
    print(f"Dimension: {len(vector)}, premiers: {vector[:5]}")
```

---

### 4. `get_status() -> str`

**Description**:  
Retourne statut actuel pour UI.

**Retour**: 
- `"[OFF] Inactif"` si is_available=False
- `"API: {provider}"` si backend=API
- `"Ollama: {model}"` si backend=Ollama
- `"GGUF: {model_name}"` si backend=GGUF
- `"Horde: {model}"` si backend=AIHorde
- `"[UNK] Inconnu"` si type non reconnu

---


## Backends Disponibles

### Backend: API (Cloud Providers)

**Providers support�s**:
- OpenAI (GPT-4, GPT-4 Turbo, GPT-3.5)
- Anthropic (Claude 3.5, Claude 3 Opus/Sonnet)
- Mistral (Large, Medium, Small)
- Google (Gemini Pro)
- GROK (xAI)
- AIHorde (communautaire, gratuit)

### Backend: Ollama (Local Models)

**Requirements**:
- Service Ollama en cours (http://localhost:11434)
- Mod�les t�l�charg�s (llama3, mistral, etc.)

### Backend: GGUF/llama.cpp (VRAM Optimized)

**Requirements**:
- llama-cpp-python install�
- Fichiers GGUF t�l�charg�s

### Backend: KoboldCpp (Community)

**Requirements**:
- KoboldCpp en cours (http://localhost:5001)
- Compatible mod�les GGUF

---

## D�pendances

### Modules Python Requis
- `asyncio`, `json`, `re`, `typing`

### Modules OGMA
- `SettingsManager`, `APIManager`, `OllamaManager`, `GGUFManager`, `KoboldManager`, `AIHordeManager`

---

**Tests pr�vus**: 20 tests (12 AIController + 8 EmbeddingController)  
**Couverture estim�e**: 100%
