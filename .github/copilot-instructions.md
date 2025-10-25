# OGMA - Instructions pour Agents IA

## 🤝 Méthodologie de Travail Collaborative

**PRINCIPE FONDAMENTAL**: "L'Architecte conçoit, l'IA code - Aucun code sans feu vert"

### Répartition des Rôles
- **ARCHITECTE/CRÉATIF (Humain)**: Vision globale, décisions stratégiques, validation conceptuelle avant implémentation
- **IA CODEUSE**: Analyse technique, proposition de solutions, tests et validation fonctionnelle

### Règles Critiques
- ⚠️ **JAMAIS de code sans feu vert explicite** de l'architecte
- 🔍 L'IA **analyse et propose** des solutions d'implémentation  
- ✅ L'architecte **valide et donne le feu vert** avant tout coding
- 🧪 L'IA **teste et documente** après validation

Cette approche garantit la cohérence architecturale tout en optimisant l'exécution technique.

## Architecture Générale

OGMA est un assistant conversationnel avec mémoire persistante et perception temporelle. **Architecture monolithique principale** dans `ogma_ng.py` (~6800 lignes) avec système d'extensions modulaire.

### Composants Core
- **ogma_ng.py**: Interface NiceGUI + orchestration principale 
- **core_logic.py**: Contrôleurs IA multi-providers (API/Ollama/GGUF/KoboldCpp)
- **memory_manager.py**: Système hybride SQLite + FAISS pour mémoire vectorielle
- **audio_manager.py**: STT/TTS avec moteurs multiples (local/cloud)

### Pattern Extension Standard
Toutes les extensions suivent le pattern singleton avec API publique standardisée:

```python
# extensions/[extension_name]/__init__.py
def initialize_[extension](dependencies) -> bool:
    """Initialise avec dépendances OGMA"""
    
def is_available() -> bool:
    """Vérifie disponibilité extension"""
    
def get_ui_components() -> dict:
    """Retourne composants UI pour intégration header"""
    
def cleanup():
    """Nettoyage propre"""
```

## Démarrage et Configuration

**Point d'entrée principal**: `launch_ogma.py` (recommandé) ou `start_ogma.py` (minimal)
- Vérification dépendances automatique
- Configuration environnement (.env support) 
- Retry automatique ports 8080-8090

```bash
python launch_ogma.py  # Production avec vérifications
python start_ogma.py   # Développement rapide
```

### Structure Données Critique
```
data/
├── settings.json        # Configuration APIs/providers/backends
├── conversations/       # Historique JSON avec index.json
├── memory/             # SQLite + index FAISS + backups auto
└── uploads/            # Fichiers temporaires upload
```

## Patterns Architecturaux Essentiels

### 1. Lazy Initialization Pattern
**CRITIQUE**: Tous les managers sont initialisés paresseusement via `_ensure_*()`:

```python
# Exemple pattern utilisé partout
def _ensure_memory_manager() -> Optional[MemoryManager]:
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager(...)
    return _memory_manager
```

### 2. Dual-IA Architecture 
- **Chat Controller**: IA principale conversationnelle
- **Archiviste Controller**: IA d'enrichissement mémoire et synthèse
- **Embedding Controller**: Génération vecteurs pour FAISS

Configuration indépendante par contrôleur (provider, modèle, paramètres).

### 3. Extension Integration Pattern
Extensions s'intègrent via hooks dans `ogma_ng.py`:

```python
# Dans _ensure_[extension]():
from extensions.[name] import initialize_[extension]
extension = initialize_[extension](chat_controller, archiviste_controller, memory_manager)

# Injection UI header:
ui_components = extension.get_ui_components()
header_button = ui_components.get('header_button')
```

## Workflows Développement Critiques

### Tests et Debug
- **Prefix convention**: `test_*.py` pour validation, `debug_*.py` pour diagnostics
- **Commandes essentielles**: 
  ```bash
  python test_memory_system.py          # Test mémoire SQLite+FAISS
  python debug_config.py                # Diagnostic configuration
  python check_cognitive_mirror_integration.py  # Vérification extensions
  ```

### Memory System Workflow
Le système mémoire est **critique** - toute modification nécessite:
1. Backup automatique dans `data/memory/backup/` (rotation 10 fichiers)
2. Test avec `test_memory_system.py` 
3. Réparation si nécessaire: `rebuild_faiss_safe.py`

### Backend Configuration
**Multi-provider support** avec uniformisation dans `_map_backend_for_controller()`:
- **API**: OpenAI, Mistral, Anthropic, Google, GROK, AIHorde  
- **Local**: Ollama, GGUF (llama-cpp-python), KoboldCpp

## Intégrations Spécifiques

### NiceGUI UI Patterns
- **Modals**: Système centralisé dans `ogma_modals.py` avec aliases dynamiques
- **CSS/JS**: Injection via `ui.run_javascript()` pour personnalisation Quasar
- **File Upload**: Pattern standardisé via `extensions/file_processor.py`

### Audio Pipeline
STT/TTS avec détection automatique moteurs disponibles:
- **Cloud**: OpenAI Whisper, ElevenLabs, Azure  
- **Local**: vosk, pyttsx3, gTTS offline

### Extension Examples
- **cognitive_mirror**: Introspection/métacognition avec dialogue Luna↔Archiviste
- **journal_de_bord**: Journal quotidien avec injection contexte matinal
- **web_navigator**: Scraping intelligent + injection contenu web

## Conventions Codage Spécifiques

### Naming Patterns  
- `_private_functions()`: Helpers internes
- `_ensure_component()`: Lazy initializers 
- `*_controller`: Gestionnaires IA
- `*_manager`: Gestionnaires ressources

### Error Handling
Pattern défensif avec fallbacks:
```python
try:
    # Tentative principale
    result = main_operation()
except Exception as e:
    print(f"[COMPONENT] Erreur: {e}")
    # Fallback ou notification safe
    _notify_safe(f"Erreur: {e}", type='warning')
```

### Threading Safety
Système FAISS avec verrous explicites:
```python
with self._faiss_lock:
    # Opérations FAISS thread-safe
```

## Configuration Critique

**Fichier settings.json** structure par contrôleur:
```json
{
  "chat_api": {"provider": "...", "api_key": "...", "backend_type": "API"},
  "reasoning_api": {"provider": "...", "api_model": "..."},
  "embedding_api": {"provider": "...", "backend_type": "API"}
}
```

**Variables globales essentielles** dans `ogma_ng.py`:
- `_chat_controller`, `_archiviste_controller`, `_embedding_controller`
- `_memory_manager`, `_settings_manager`, `_audio_manager`
- `_conversation_history`: État conversation courante

Ne jamais modifier directement - toujours passer par les `_ensure_*()` functions.