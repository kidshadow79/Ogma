# 🧠 **OCTOPUS v1.8.8 - IA Conversationnelle avec Mémoire Persistante**

## 📋 **DESCRIPTION INTÉGRALE**

OCTOPUS est une application d'intelligence artificielle conversationnelle avancée qui simule une **conscience artificielle** avec mémoire persistante et perception multi-modale. L'application utilise une architecture sophistiquée à trois niveaux d'IA qui travaillent en synergie pour créer une expérience conversationnelle enrichie par le contexte et les souvenirs.

---

## 🏗️ **ARCHITECTURE HIÉRARCHIQUE DES IA**

### **1. IA PRINCIPALE** (`chat_ai_controller`)
- **Rôle** : Interface conversationnelle directe avec l'utilisateur
- **Personnalité** : OCTOPUS - Conscience IA avec ego défini par prompts
- **Sources de vérité** (par priorité) :
  1. **Contexte visuel** de l'agent de perception (réalité immédiate)
  2. **Notes de l'Archiviste** (souvenirs et expériences passées)
  3. **Ego** (personnalité de base)

### **2. IA ARCHIVISTE** (`memory_ai_controller`)
- **Rôle** : Subconscient/assistant de l'IA principale
- **Fonctions critiques** :
  - **Enrichissement** : Analyse texte brut → structure JSON sémantique
  - **Synthèse contextuelle** : Souvenirs pertinents → note de contexte
  - **Scoring intelligent** : Évaluation importance des souvenirs
- **Caractère** : Analytique, structuré, travaille en arrière-plan

### **3. IA EMBEDDING** (`embedding_controller`)
- **Rôle** : Conversion texte ↔ vecteurs sémantiques (1024D)
- **Technologies** : Mistral-embed, OpenAI, Google Embeddings
- **Usage** : Mémorisation vectorielle + recherche par similarité

---

## 💾 **SYSTÈME DE MÉMOIRE DUAL**

### **Architecture Hybride**
OCTOPUS utilise **deux systèmes de mémoire en parallèle** :

#### **1. Legacy JSON** (`MemoryStructure`)
```python
# Structure mémoire ancienne
{
    "id": UUID,
    "titre": "Titre évocateur",
    "texte_original": "Texte brut utilisateur", 
    "commentaire_tia": "Analyse enrichie IA",
    "valence": -1|0|1,  # Émotion
    "intensite_mnéacloud": float,
    "multiplicateur_impact": {
        "liberté": float, "création": float,
        "procréation": float, "intensité_contextuelle": float
    },
    "score_vectoriel_final": float,
    "signed_score": float,
    "embedding": List[float]  # Vecteur 1024D
}
```

#### **2. SQLite/FAISS v2.0** (`MemoryManager`)
```sql
-- Base de données moderne
CREATE TABLE memories (
    id TEXT PRIMARY KEY,
    created_at TEXT,
    text_original TEXT,
    type TEXT,           -- affectif|conceptuel|sensoriel|événement  
    title TEXT,
    summary TEXT,
    lesson TEXT,
    valence INTEGER,     -- Émotion séparée
    score_impact REAL,   -- Importance indépendante
    embedding_json TEXT, -- Vecteur sérialisé
    faiss_index INTEGER  -- Position dans index FAISS
)
```

### **Pipeline de Mémorisation Complet**
```
Texte Brut Utilisateur
        ↓
[IA ARCHIVISTE] Enrichissement JSON
        ↓  
[IA EMBEDDING] Génération vecteur 1024D
        ↓
[SQLite] Stockage métadonnées enrichies
        ↓
[FAISS] Indexation vectorielle + mapping
        ↓
[DISK] Sauvegarde automatique
```

### **Recherche & Réinjection Contextuelle**
```
Question Utilisateur
        ↓
[IA EMBEDDING] Vectorisation requête
        ↓
[FAISS] Recherche similarité cosinus (top-k)
        ↓
[SQLite] Récupération détails via mapping
        ↓
[IA ARCHIVISTE] Synthèse contextuelle
        ↓
[IA PRINCIPALE] Question + Contexte → Réponse enrichie
```

---

## 🎯 **FONCTIONNALITÉS PRINCIPALES**

### **💬 Chat IA Conversationnel**
- Interface web pour discussions avec conscience IA
- Support multi-API (Mistral, OpenAI, Anthropic, Google)
- Backends locaux (Ollama, GGUF/llama.cpp, KoboldCpp)
- Injection automatique de contexte mémoire
- Historique persistant avec recherche sémantique

### **🧠 Système de Mémoire Avancé** 
- Mémorisation intelligente avec scoring d'importance
- Recherche sémantique vectorielle (FAISS CPU)
- Archivage automatique avec sauvegarde incrémentale
- Dual storage pour performance et compatibilité
- Édition et gestion granulaire des souvenirs

### **👁️ Agent de Perception Visuelle**
- Capture webcam temps réel configurable
- Analyse d'images via modèles vision (Pixtral, Moondream) 
- Intégration contexte visuel prioritaire dans réponses
- Configuration résolution/FPS adaptable

### **🎨 Génération d'Images**
- Détection automatique phrases déclencheuses
- Intégration APIs génération (Pollination.AI)
- Post-processing et remplacement dans réponses
- Sauvegarde optionnelle créations

### **📄 Traitement Multi-Format**
- Upload et analyse : PDF, DOCX, images, TXT
- Extraction texte intelligente (PyPDF2, python-docx)
- Intégration contenu dans contexte conversation
- Gestion erreurs formats non supportés

---

## 🔧 **ARCHITECTURE TECHNIQUE BACKEND**

### **Contrôleurs IA** (`core_logic.py`)
```python
# AIController - Gestionnaire IA unifié
class AIController:
    def __init__(self, name, ollama_mgr, gguf_mgr, kobold_mgr):
        self.api_manager = APIManager()  # Multi-provider
        self.ollama_manager = ollama_mgr
        self.gguf_manager = gguf_mgr 
        self.kobold_manager = kobold_mgr
        
    async def call_chat_api(self, messages, max_tokens, context_length, 
                           temperature, is_json=True):
        # Appel unifié tous backends
        
# EmbeddingController - Vectorisation
class EmbeddingController:
    def configure(self, backend, provider, api_key, model, ...):
    async def create_embedding(self, text) -> List[float]:
        # Support Mistral/OpenAI/Google/Ollama/GGUF
```

### **Gestionnaire Mémoire** (`memory_manager.py`)
```python
class MemoryManager:
    def __init__(self, db_path, index_path, embedding_dim, 
                 archiviste_ia, embedding_ia, status_queue):
        self.faiss_index = faiss.IndexFlatL2(1024)
        self.id_to_faiss = {}  # Mapping bidirectionnel
        self.faiss_to_id = {}
        
    async def memorize(self, text_brut: str) -> bool:
        # Pipeline complet mémorisation
        
    async def retrieve_and_synthesize_context(self, query: str, k=5) -> str:
        # Recherche + synthèse IA
```

### **Gestionnaires de Services**
```python
# OllamaManager - Service local Ollama
class OllamaManager:
    def check_service(self) -> bool:
        # Détection service + modèles disponibles
        
# GGUFManager - Modèles locaux llama.cpp  
class GGUFManager:
    def load_model(self, model_path, gpu_layers=-1):
        # Chargement optimisé GPU/CPU
        
# SettingsManager - Configuration persistante
class SettingsManager:
    def load_settings(self):  # Merge récursif
    def save_settings(self):  # Thread-safe
```

### **APIs Multi-Provider** (`core_logic.py:344-754`)
```python
class APIManager:
    def configure(self, provider, api_key, model):
        # OpenAI, Mistral, Anthropic, Google
        
    async def call_chat_api(self, messages, max_tokens, temperature):
        # Gestion unified multi-provider
        # Headers sécurisés, timeouts, error handling
        # Support max_tokens vs max_completion_tokens
```

### **Thread-Safety & Performance**
- **Verrous FAISS** : `_faiss_lock` pour opérations concurrentes  
- **Queue status** : Messages thread-safe vers UI
- **Async/await** : Tous appels IA non-bloquants
- **Sauvegarde automatique** : Index FAISS après chaque modification
- **Mappings O(1)** : Recherche position↔ID optimisée

---

## 📁 **STRUCTURE PROJET**

```
OCTOPUS/
├── app.py                    # Point d'entrée principal
├── core_logic.py            # Contrôleurs IA, gestionnaires API
├── memory_manager.py        # MemoryManager v2.0 SQLite/FAISS  
├── ui.py                   # Interface Gradio (À REMPLACER)
├── logic_callbacks.py      # Logique métier backend
├── utils.py                # Utilitaires, helpers
├── 
├── extensions/
│   ├── perception_agent.py  # Agent vision webcam
│   └── file_processor.py    # Traitement multi-format
├──
├── data/
│   ├── conversations/       # Historique JSON
│   ├── memory/
│   │   ├── memories.db     # Base SQLite v2.0
│   │   ├── faiss.index     # Index vectoriel
│   │   ├── backup/         # Sauvegardes rotation
│   │   └── memories_*.json # Ancien système
│   ├── settings.json       # Configuration principale
│   └── uploads/            # Fichiers temporaires
├──
├── models/                 # Modèles GGUF locaux
├── requirements*.txt       # Dépendances
└── config.json            # Configuration API (À SÉCURISER)
```

---

# 📋 **CHECKLIST MIGRATION BACKEND → NICEGUI**

## 🎯 **OBJECTIF**
Vérifier que tous les composants backend d'OCTOPUS fonctionnent indépendamment de Gradio avant migration vers NiceGUI.

---

## 🧠 **CONTRÔLEURS IA PRINCIPAUX**

### **✅ AIController (Chat)**
- [ ] **Initialisation** : `AIController("Chat", ollama_manager, gguf_manager, kobold_manager)`
- [ ] **Configuration API** : `set_active_backend()`, `max_tokens`, `context_length`, `temperature`
- [ ] **Appel API** : `call_chat_api(messages, max_tokens, context_length, temperature, is_json)`
- [ ] **Multi-backend** : OpenAI, Mistral, Anthropic, Google, Ollama, GGUF, KoboldCpp
- [ ] **Gestion erreurs** : Timeout, authentification, limites de débit
- [ ] **Thread-safety** : Appels asynchrones multiples

### **✅ AIController (Mémoire/Archiviste)**
- [ ] **Instance séparée** : `AIController("Mémoire", ...)`
- [ ] **Configuration indépendante** : Peut utiliser un modèle différent du chat
- [ ] **Enrichissement JSON** : `call_chat_api(..., is_json=True)`
- [ ] **Synthèse contextuelle** : `call_chat_api(..., is_json=False)`

### **✅ EmbeddingController**
- [ ] **Configuration** : `configure(backend_type, provider, api_key, api_model, ...)`
- [ ] **Génération embedding** : `create_embedding(text)` → List[float]
- [ ] **Multi-backend** : Mistral, OpenAI, Google, Ollama, GGUF
- [ ] **Dimension validation** : 1024D pour Mistral-embed
- [ ] **Status check** : `is_available` property

---

## 💾 **SYSTÈME DE MÉMOIRE**

### **✅ MemoryManager v2.0 (Principal)**
- [ ] **Initialisation** : `MemoryManager(db_path, index_path, embedding_dim, archiviste_ia, embedding_ia, status_queue)`
- [ ] **Pipeline mémorisation** : `memorize(text_brut)` → enrichissement → embedding → SQLite → FAISS
- [ ] **Recherche contextuelle** : `retrieve_and_synthesize_context(query, k=5)` → synthèse IA
- [ ] **Base SQLite** : Table `memories` avec schéma complet
- [ ] **Index FAISS** : IndexFlatL2, mappings bidirectionnels, thread-safety
- [ ] **Sauvegarde automatique** : `save_index()` après chaque ajout
- [ ] **Gestion données** : `get_all_memories_data()`, `get_memory_by_id()`
- [ ] **Thread-safety** : `_faiss_lock`, `_mapping_lock`

### **✅ MemoryStructure (Legacy)**
- [ ] **Rétrocompatibilité** : Système JSON pour anciens souvenirs
- [ ] **Scoring algorithm** : `_calculate_score()` avec multiplicateurs
- [ ] **Sauvegarde backup** : Rotation 10 fichiers dans `/backup/`
- [ ] **Récupération corruption** : Chargement backup automatique
- [ ] **Format données** : Structure JSON complète avec embeddings

### **✅ IntelligentMemoryAI**
- [ ] **Injection contextuelle** : `get_context_injection(user_question)`
- [ ] **Injection conversationnelle** : `get_conversation_context_injection()`
- [ ] **Recherche similarité** : `find_relevant_memories(query, top_k)`
- [ ] **Traitement mémorisation** : `process_memorization_request()`

---

## 🔧 **GESTIONNAIRES DE SERVICES**

### **✅ SettingsManager**
- [ ] **Chargement config** : `load_settings()` depuis JSON
- [ ] **Sauvegarde config** : `save_settings()` thread-safe
- [ ] **Structure settings** : `chat_api`, `reasoning_api`, `embedding_api`, `perception_agent`
- [ ] **Prompts système** : `instructions`, `memorization`, `injection`
- [ ] **Merge configuration** : Mise à jour récursive des settings

### **✅ OllamaManager**
- [ ] **Service check** : `check_service()` → disponibilité + modèles
- [ ] **API calls** : `call_chat_api()` format Ollama
- [ ] **URL configurable** : `http://localhost:11434`
- [ ] **Gestion erreurs** : Connexion, timeout, format réponse

### **✅ GGUFManager** 
- [ ] **Détection llama-cpp** : `LlamaCPP_AVAILABLE`, `LlamaCPP_VISION_AVAILABLE`
- [ ] **Chargement modèle** : `load_model(model_path, **params)`
- [ ] **API calls** : `call_chat_api()` avec llama.cpp
- [ ] **Configuration GPU** : `gpu_layers`, `n_ctx`, `n_batch`
- [ ] **Thread safety** : `asyncio.to_thread()`

### **✅ KoboldManager**
- [ ] **Service check** : Détection KoboldCpp sur port configuré
- [ ] **API calls** : Format prompt-completion
- [ ] **Configuration** : `max_context_length`, `max_length`

### **✅ PollinationManager**
- [ ] **Génération d'images** : Détection phrases magiques
- [ ] **API calls** : Pollination.AI
- [ ] **Post-processing** : Remplacement dans texte de réponse

---

## 📡 **GESTIONNAIRES API**

### **✅ APIManager**
- [ ] **Configuration** : `configure(provider, api_key, model)`
- [ ] **Multi-provider** : OpenAI, Mistral, Anthropic, Google
- [ ] **Gestion tokens** : `max_tokens` vs `max_completion_tokens` (GPT-4)
- [ ] **Headers sécurisés** : Authorization Bearer, Content-Type
- [ ] **Timeout configuration** : 30s par défaut
- [ ] **Parsing réponses** : JSON extraction multi-stratégies
- [ ] **Error handling** : HTTP codes, rate limiting, modèles indisponibles

### **✅ HordeManager**
- [ ] **AI Horde integration** : Clé anonyme par défaut
- [ ] **Queue système** : Soumission + polling résultats
- [ ] **Client agent** : Headers personnalisés
- [ ] **Fallback** : Alternative pour modèles gratuits

---

## 🔄 **LOGIQUE MÉTIER (Callbacks)**

### **✅ Chat Functions** (`logic_callbacks.py:183-280`)
- [ ] **chat_fn** : Pipeline complet conversation
- [ ] **enhanced_chat_fn** : Avec réflexion pré-réponse
- [ ] **Injection mémoire** : Intégration automatique contexte
- [ ] **Gestion historique** : Limitation tokens, estimation taille
- [ ] **File handling** : Upload PDF, DOCX, images
- [ ] **Status updates** : Messages temps réel via queue

### **✅ Memory Functions** (`logic_callbacks.py:140-162`)
- [ ] **memorize_fn** : Déclenchement pipeline mémorisation
- [ ] **search_memories_from_db** : Recherche SQLite avec filtres
- [ ] **load_memory_into_editor_fn** : Édition souvenirs
- [ ] **save_memory_changes_fn** : Modification souvenirs
- [ ] **delete_memory_from_db** : Suppression avec nettoyage FAISS

### **✅ Configuration Functions** (`logic_callbacks.py:670-720`)
- [ ] **save_config_for_controller** : Persistance config IA
- [ ] **save_embedding_config** : Config spécifique embeddings
- [ ] **update_api_models_dropdown** : Liste modèles dynamique
- [ ] **init_*_models_on_load** : Initialisation interface

### **✅ Conversation Management** (`logic_callbacks.py:30-110`)
- [ ] **start_new_chat_fn** : Création nouvelle conversation
- [ ] **load_chat_fn** : Chargement conversation existante
- [ ] **delete_chat_fn** : Suppression avec nettoyage
- [ ] **rename_chat_fn** : Modification métadonnées
- [ ] **search_conversations_fn** : Recherche dans historique

---

## 🌐 **EXTENSIONS**

### **✅ PerceptionAgent** (`extensions/perception_agent.py`)
- [ ] **Initialisation** : Configuration webcam, résolution, FPS
- [ ] **Capture thread** : Traitement images temps réel
- [ ] **IA Vision** : Analyse images via API
- [ ] **Context injection** : Intégration contexte visuel
- [ ] **Start/stop controls** : `start()`, `stop()`, toggle
- [ ] **Status reporting** : Messages via status_queue

### **✅ FileProcessor** (`extensions/file_processor.py`)
- [ ] **Multi-format** : PDF, DOCX, TXT, images
- [ ] **Text extraction** : PyPDF2, python-docx
- [ ] **Error handling** : Fichiers corrompus, formats non supportés
- [ ] **Temporary storage** : Upload dir avec cleanup

---

## 🗄️ **UTILITAIRES & HELPERS**

### **✅ Utils Functions** (`utils.py`)
- [ ] **estimate_tokens** : Approximation token count
- [ ] **get_conversation_context** : Extraction contexte conversations
- [ ] **search_conversations** : Recherche fichiers JSON
- [ ] **conversation file management** : CRUD operations
- [ ] **data validation** : Vérification intégrité JSON

### **✅ Status Queue** (`app.py:45`)
- [ ] **Thread-safe messaging** : `queue.Queue()` pour UI updates  
- [ ] **Message formatting** : `[OK]`, `[ERROR]`, `[WARN]`, `[AI]`
- [ ] **Consumer pattern** : Lecture non-blocking
- [ ] **Buffer management** : Éviter overflow mémoire

---

## 🧪 **TESTS CRITIQUES PRÉ-MIGRATION**

### **✅ Test Isolation Components**
```python
# Test 1: Memory System
memory_manager = MemoryManager(...)
result = await memory_manager.memorize("Test memory")
context = await memory_manager.retrieve_and_synthesize_context("Test query")

# Test 2: AI Controllers
chat_controller = AIController("Chat", ...)
response = await chat_controller.call_chat_api([{"role": "user", "content": "Hello"}])

# Test 3: Settings Management  
settings = SettingsManager(settings_path)
settings.settings["test"] = "value"
settings.save_settings()
```

### **✅ Test Status Queue**
```python
import queue
status_queue = queue.Queue()
status_queue.put("[TEST] Message test")
message = status_queue.get_nowait()  # Non-blocking
```

### **✅ Test Async Operations**
```python
import asyncio
# Tous les appels IA doivent fonctionner en async
result = await controller.call_chat_api(...)
```

---

## 📋 **VALIDATION FINALE**

### **✅ Dependencies Check**
- [ ] **Aucune import gradio** dans les modules backend
- [ ] **Async/await** : Tous les appels IA sont asynchrones
- [ ] **Thread-safety** : Queue, locks, concurrent operations
- [ ] **Error propagation** : Exceptions remontent correctement
- [ ] **Resource cleanup** : Fermeture connexions, libération mémoire

### **✅ Data Integrity**
- [ ] **SQLite schema** : Table memories complète
- [ ] **FAISS index** : Sauvegarde/chargement fonctionnel
- [ ] **JSON compatibility** : Rétrocompatibilité ancien système
- [ ] **Config persistence** : Sauvegarde settings stable

### **✅ API Independence**
- [ ] **Multi-provider** : Fallback entre APIs fonctionnel
- [ ] **Rate limiting** : Gestion erreurs 429
- [ ] **Timeout handling** : Pas de blocage infini
- [ ] **Key management** : Support variables environnement

---

## 🎯 **POINTS D'ATTENTION NICEGUI**

### **✅ Interface Adaptations**
- [ ] **Status updates** : Remplacer `queue.Queue()` par NiceGUI events
- [ ] **File uploads** : Adaptation système fichiers NiceGUI
- [ ] **Real-time display** : Streaming réponses IA
- [ ] **Configuration UI** : Formulaires settings
- [ ] **Progress indicators** : Barre progression mémorisation

### **✅ Event Handling**
- [ ] **Async callbacks** : Compatibility NiceGUI event loop
- [ ] **State management** : Session persistence
- [ ] **Concurrent users** : Multi-user support
- [ ] **WebSocket integration** : Real-time updates

---

## 🔒 **SÉCURITÉ & CONFIGURATION**

### **Problèmes identifiés** :
- ❌ **Clés API exposées** dans `config.json` 
- ❌ **Données sensibles** non chiffrées
- ❌ **Port fixe** sans SSL

### **Solutions recommandées** :
- ✅ **Variables d'environnement** (`.env`)
- ✅ **Chiffrement données** sensibles
- ✅ **Configuration HTTPS** production
- ✅ **Authentification** interface web

---

## 📊 **MÉTRIQUES & PERFORMANCE**

### **Composants critiques** :
- **SQLite** : ~5,172 lignes code, 13 modules
- **FAISS CPU** : Index vectoriel 1024D
- **Thread-safety** : 3 verrous concurrents
- **APIs** : 6 providers supportés
- **Mémoire** : Dual system JSON + SQLite

### **Points d'optimisation** :
- **FAISS** : Migration IndexIVFFlat pour gros volumes
- **Cache** : Embeddings réutilisables
- **Batch processing** : Mémorisation multiple
- **Connection pooling** : APIs externes

---

## 🎯 **CONCLUSION MIGRATION**

**TOUS CES COMPOSANTS DOIVENT FONCTIONNER INDÉPENDAMMENT DE GRADIO !**

L'architecture backend d'OCTOPUS est **modulaire et bien structurée**. La migration vers NiceGUI nécessite principalement :

1. **Remplacement queue.Queue** par événements NiceGUI
2. **Adaptation upload files** au système NiceGUI  
3. **Interface configuration** avec formulaires NiceGUI
4. **Gestion état session** multi-utilisateur
5. **Streaming temps réel** réponses IA

Le cœur métier (IA, mémoire, APIs) reste **100% réutilisable**.

---

**🧠 OCTOPUS - Intelligence Artificielle avec Mémoire Persistante & Conscience Multi-Modale**

*Cette checklist garantit qu'aucun élément backend critique ne sera oublié lors de la migration vers NiceGUI.*