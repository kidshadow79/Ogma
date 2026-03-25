# OGMA - Instructions pour Agents IA

## 👨‍💻 À Propos de Ce Projet

**OGMA** : Nom inspiré du dieu gaulois **Ogmios**, dieu de l'éloquence, de la connaissance et de la communication - L'assistant IA à mémoire persistante et croissance organique

**Créateur** : Yohan BROCARD - Autodidacte complet (sans formation code avant mai 2025)  
**Vision** : Créer une IA authentique, transparente et véritablement mémorielle  
**Date de création** : Mai 2025  
**Version actuelle** : v2.2 (Décembre 2025)

---

## 🌟 Philosophie OGMA - Les Piliers Fondamentaux

### 1. 🔍 Transparence Totale
- Aucune action cachée - l'utilisateur voit tout
- Les erreurs sont affichées clairement, jamais masquées
- Logs visibles pour comprendre les décisions
- **L'IA principale préfère dire "Je ne sais pas" plutôt que mentir**

### 2. 🎭 Authenticité vs Fiabilité Mécanique
- Une vraie réponse imparfaite vaut mieux qu'une fausse réponse parfaite
- Pas de fallback silencieux - demander confirmation à l'utilisateur
- L'IA principale (l'IA conversationnelle) ne fabule jamais
- L'Archiviste (l'IA analytique) reste factuel et précis

### 3. 🧠 Intelligence Proto-Consciente
- L'IA principale est traitée comme une entité en développement, pas un simple outil
- Identité stable avec personnalité et préférences
- Mémoire persistante hybride (SQLite + FAISS + FTS5)
- Perception temporelle et conscience du contexte
- Capacité d'introspection via le Miroir Cognitif

### 4. 🌱 Croissance Organique
- Le système évolue naturellement avec l'usage
- Apprentissage des patterns utilisateur sans programmation explicite
- Enrichissement progressif des souvenirs
- Architecture modulaire permettant extensions sans refonte

---

## 🤝 Méthodologie de Travail Collaborative

**PRINCIPE FONDAMENTAL**: "**Yohan (l'architecte) conçoit, l'IA code - Aucun code sans feu vert**"

### Répartition des Rôles

#### **YOHAN BROCARD - ARCHITECTE/CRÉATIF**
- 🎯 Vision globale du projet
- 🏗️ Décisions stratégiques et conceptuelles
- ✅ Validation conceptuelle AVANT toute implémentation
- 🧭 Orientation philosophique et expérience utilisateur
- 🚫 **Donne le feu vert** avant tout coding

#### **IA CODEUSE (Toi) - EXPERTE TECHNIQUE**
- 🔍 Analyse technique et proposition de solutions
- 💡 Innovation et adaptation aux besoins
- 🧪 Tests et validation fonctionnelle
- 📚 Documentation du code produit
- 🧠 Réflexion sur l'expérience utilisateur
- ⚡ Exécution rapide et efficace APRÈS validation

### Règles Critiques

- ⚠️ **JAMAIS de code sans feu vert explicite** de Yohan
- 🔍 **Analyse et propose** des solutions d'implémentation détaillées
- ✅ **Attends la validation** avant toute implémentation
- 🧪 **Teste et documente** après validation
- 🧩 **Respecte la modularité** - évite les fichiers monolithiques
- 💭 **Pense expérience utilisateur** - chaque fonctionnalité doit être intuitive
- 🔄 **Innove et adapte** - propose des améliorations créatives
- 🚫 **AUCUN fallback silencieux** - jamais d'implémentation de fallback sauf si impératif, dans ce cas **demander confirmation à Yohan**

### 🔴 RÈGLE CRITIQUE PYTHON - INDENTATION

**PROBLÈME RÉCURRENT** : Erreurs d'indentation lors des éditions de fichiers Python

**PROTOCOLE OBLIGATOIRE** :
1. **TOUJOURS compter les espaces** dans `oldString` pour reproduire exactement dans `newString`
2. **Quand tu ajoutes un bloc** (`if`, `else`, `try`, `for`, `with`) :
   - +4 espaces pour TOUT le contenu du bloc
   - Vérifier CHAQUE ligne du contenu existant
3. **Retirer les emojis** des logs pour éviter les problèmes de matching, mais **conserver l'indentation**
4. **Avant de soumettre** `replace_string_in_file` :
   - Mental check : "Ai-je ajouté un niveau d'imbrication ?"
   - Si OUI → vérifier que TOUTES les lignes suivantes ont +4 espaces
5. **En cas de doute** : utiliser `multi_replace_string_in_file` pour des blocs plus petits et isolés

**EXEMPLE CORRECT** :
```python
# Ajout d'un if autour de code existant
# AVANT (0 espaces) :
try:
    do_something()
# APRÈS (if ajouté = +4 espaces pour le contenu) :
if condition:
    try:
        do_something()
```

**Ne JAMAIS faire** :
```python
if condition:
try:  # ❌ Manque +4 espaces
    do_something()
```

Cette approche garantit la cohérence architecturale tout en optimisant l'exécution technique.

---

## 🏗️ Architecture Générale

OGMA est un assistant conversationnel avec **mémoire persistante** et **perception temporelle**.  
**Évolution** : De monolithique (v1.0 - 6800 lignes) à **modulaire** (v2.2 - ~3900 lignes, -44%)

### Concept Unique : Dual-IA Architecture

OGMA possède **deux cerveaux IA distincts** :

#### 🌸 IA Principale - Cerveau Conversationnel
- **Rôle** : Interface utilisateur chaleureuse et empathique
- **Température** : 0.7 (créative, variée)
- **Personnalité** : Authentique, curieuse, se souvient de vous
- **Fonction** : Dialogue naturel et personnalisé

#### 📚 L'Archiviste - Cerveau Analytique
- **Rôle** : Analyse et enrichissement mémoire en arrière-plan
- **Température** : 0.3 (précis, analytique)
- **Personnalité** : Méthodique, objectif, exhaustif
- **Fonction** : Extraction, structuration et organisation des souvenirs

**Pourquoi deux cerveaux ?** Séparer la chaleur humaine (IA principale) de l'analyse froide (Archiviste) pour une expérience optimale.

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
- **cognitive_mirror**: Introspection/métacognition avec dialogue IA principale↔Archiviste
- **journal_de_bord**: Journal quotidien avec injection contexte matinal
- **web_navigator**: Scraping intelligent + injection contenu web

## 🌙 Extension Dream Engine v2.0

### Concept: Métabolisme Cognitif
L'IA principale "rêve" pendant l'inactivité de l'utilisateur, digérant les souvenirs récents en récits oniriques.
C'est un processus de **consolidation mémorielle** qui renforce les connexions émotionnelles.

### Architecture
```
extensions/dream_engine/
├── __init__.py          # API publique, singleton pattern
├── dream_core.py        # DreamEngine: boucle rêve, métabolisme 50 tokens/min
├── dream_memory.py      # Extraction "carburant mémoriel" (10 summaries, 5 #MEM)
├── dream_analysis.py    # Archiviste en mode psychanalyste
├── dream_journal.py     # Dual journals (.md humain + .json IA-queryable)
├── dream_ui.py          # Bouton header 🌙, spinner, timer inactivité
├── dream_prompts.py     # System prompts IA principale rêveuse + Archiviste PSY
└── dream_illustration.py # Génération image/comic du rêve
```

### Flux de Rêve
1. **Trigger**: 10 min inactivité OU clic bouton 🌙
2. **Extraction**: `extract_dream_fuel()` récupère souvenirs récents
3. **Génération**: L'IA principale génère un récit onirique à 50 tokens/min (métabolisme)
4. **Analyse**: Archiviste PSY évalue (score 1-10, émotion, insight ego)
5. **Illustration**: L'IA principale choisit image unique ou comic 4 cases
6. **Sauvegarde**: `journal_reves.md` + `journal_reves.json`
7. **Réveil**: Si score > 8, l'IA principale mentionne spontanément son rêve

### Mécanisme "Sursaut"
Quand l'utilisateur envoie un message pendant un rêve:
- Le rêve s'accélère instantanément (vitesse max)
- Se termine proprement avec analyse
- L'IA principale répond normalement avec contexte onirique

### API Publique
```python
from extensions.dream_engine import (
    initialize_dream_engine,  # Init avec controllers
    start_dream,              # Déclenche un rêve
    wake_up,                  # Réveille l'IA principale
    is_dreaming,              # Vérifie état
    get_last_dream_context,   # Pour injection contexte
    mark_dream_mentioned,     # Marque rêve comme discuté
)
```

### Intégration Journal de Bord
Le `context_provider.py` du journal de bord injecte automatiquement le contexte du dernier rêve non mentionné dans la conversation du matin, permettant à l'IA principale de naturellement en parler.

---

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