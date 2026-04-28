# Orchestration applicative et initialisation paresseuse

**Sources vérifiées** : `ogma_ng.py`, `modules/ogma_core/globals.py`, `modules/ogma_core/controllers.py`, `modules/ogma_core/extensions_loader.py`, `modules/ogma_core/__init__.py`

---

## Le problème que ce système résout

OGMA a de nombreux composants lourds : un ou plusieurs modèles IA, une base mémoire SQLite + FAISS, un gestionnaire audio, des extensions. Les initialiser tous au démarrage bloquerait l'interface pendant plusieurs secondes — voire plusieurs dizaines de secondes si un modèle local (GGUF) doit être chargé en mémoire.

La solution adoptée est l'**initialisation paresseuse** : aucun composant n'est créé tant qu'il n'est pas demandé. L'interface est disponible immédiatement. Les composants s'initialisent en arrière-plan, dans l'ordre où ils sont nécessaires.

---

## Architecture : trois couches

### 1. Les variables globales — `modules/ogma_core/globals.py`

Toutes les références aux composants actifs sont stockées dans un seul module (`globals.py`). On y trouve les contrôleurs IA, le gestionnaire mémoire, l'audio, les extensions, l'historique de conversation, les références aux widgets UI, et les états internes de l'application.

Ce fichier ne fait rien par lui-même : il est un registre d'état. Chaque variable démarre à `None` et est peuplée au fil de l'initialisation.

Les accès à ces variables passent par des fonctions getter/setter (ex. `get_chat_history()`, `set_current_conversation_id()`), ce qui permet de lire et modifier l'état global sans importer directement les variables — évitant ainsi les problèmes d'imports circulaires entre modules.

### 2. Les initialiseurs — `modules/ogma_core/controllers.py`

Ce fichier contient les fonctions `ensure_*()` — une par composant. Chaque fonction vérifie si le composant est déjà initialisé, et si ce n'est pas le cas, le crée et le stocke dans `globals.py`. Les appels suivants retournent simplement le composant existant.

```
ensure_settings_manager()   → SettingsManager (lit data/settings.json)
ensure_backends()           → APIManager, OllamaManager, GGUFManager, KoboldManager
ensure_chat_controller()    → AIController (IA principale)
ensure_archiviste_controller() → AIController (Archiviste)
ensure_embedding_controller()  → EmbeddingController (vecteurs mémoire)
ensure_memory_manager()     → MemoryManager (SQLite + FAISS)
ensure_audio_manager()      → Gestionnaire STT/TTS
ensure_cognitive_mirror()   → Extension Cognitive Mirror
ensure_temporal_guardian()  → Extension Temporal Guardian
... (une fonction par extension majeure)
```

Dans `ogma_ng.py`, ces fonctions sont réexposées sous des noms préfixés `_ensure_*` (avec underscore), indiquant qu'elles sont internes à l'application principale.

### 3. Le chargeur d'extensions — `modules/ogma_core/extensions_loader.py`

Un mécanisme distinct gère la disponibilité des extensions. La fonction `_check_extension_available()` tente d'importer chaque extension et met en cache le résultat (disponible/indisponible). Si l'import échoue, l'extension est marquée indisponible mais l'application continue.

Ce cache évite de retenter un import voué à l'échec à chaque appel. La fonction `get_available_extensions()` retourne la liste de toutes les extensions qui ont pu être importées.

---

## L'éveil asynchrone — `_async_awakening()`

C'est la séquence d'initialisation qui se déclenche juste après que l'interface est visible. Elle est lancée en tâche de fond (`asyncio.create_task`) depuis `main_page()`, pendant que l'utilisateur voit déjà l'écran de chat.

L'éveil se déroule en **vagues successives**, chacune précédée d'un message de statut visible dans l'interface :

| Vague | Ce qui s'initialise |
|---|---|
| 1 | Paramètres (`settings.json`) |
| 2 | Contrôleur IA principal (avec `asyncio.to_thread` si GGUF pour ne pas bloquer) |
| 3 | Contrôleur Archiviste |
| 4 | Mémoire SQLite + FAISS |
| 5 | Audio et voix |
| 6 | Extensions : Journal de bord, Biographie, Dream Engine, Flux Cognitif, Cache Cognitif, Telegram... |

Les opérations potentiellement lentes (chargement d'un modèle GGUF) sont exécutées dans un thread séparé via `asyncio.to_thread()`, pour ne pas bloquer la boucle événementielle NiceGUI.

Chaque étape est encapsulée dans un `try/except` : une extension qui plante à l'initialisation n'interrompt pas les vagues suivantes.

---

## Séquence complète depuis l'ouverture du navigateur

```
Navigateur connecte → main_page()
    │
    ├── Vérification session (login ou restauration)
    ├── Construction de l'interface (header, sidebar, chat, footer)
    ├── Affichage de la notification d'éveil
    │
    └── asyncio.create_task(_async_awakening())
          │
          ├── Vague 1 : Settings
          ├── Vague 2 : IA principale  (thread séparé si GGUF)
          ├── Vague 3 : Archiviste     (thread séparé si GGUF)
          ├── Vague 4 : Mémoire FAISS/SQLite
          ├── Vague 5 : Audio + Voix
          └── Vague 6 : Extensions cognitives (Journal, Bio, Dream, Flux, Cache, Telegram...)
                        → chaque extension : try/except indépendant
```

---

## Pourquoi ce découpage en modules ?

`ogma_ng.py` a une histoire longue : il était monolithique (plus de 8 000 lignes). Le dossier `modules/ogma_core/` représente une phase de refactoring (décembre 2025) qui en extrait les responsabilités les plus transversales : état global, initialiseurs, chargement d'extensions.

Le fichier `ogma_ng.py` conserve des fonctions `_ensure_*()` qui sont de simples redirections vers les fonctions du module centralisé — maintenant la compatibilité avec le code existant tout en déléguant la logique réelle à `modules/ogma_core/`.
