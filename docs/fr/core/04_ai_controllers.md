# Contrôleurs IA — architecture dual-cerveau

**Source vérifiée** : `core_logic.py` (classes `AIController`, `EmbeddingController`), `modules/ogma_core/controllers.py`

---

## Le principe fondamental : deux cerveaux, une classe

OGMA utilise trois instances distinctes de la classe `AIController`, chacune avec un rôle bien défini :

| Instance | Rôle | Température par défaut |
|---|---|---|
| `_chat_controller` | L'IA principale — dialogue avec l'utilisateur | 0.7 (créative) |
| `_archiviste_controller` | L'Archiviste — analyse, enrichissement mémoire | 0.3 (précise) |
| `_embedding_controller` | Génération de vecteurs pour la recherche sémantique | — |

Ces trois instances sont indépendantes : chacune peut utiliser un provider différent, un modèle différent, une température différente. C'est ce qui permet, par exemple, d'avoir l'IA principale sur un modèle créatif en ligne et l'Archiviste sur un modèle local plus rapide.

---

## `AIController` — la couche d'abstraction IA

`AIController` est la pièce centrale. Son rôle est de **masquer la complexité des backends** : le reste de l'application n'a pas à savoir si la réponse vient d'OpenAI, d'Ollama ou d'un fichier GGUF local. Elle appelle simplement `call_chat_api()` ou `call_chat_api_streaming()`.

En interne, le contrôleur conserve des références vers tous les gestionnaires de backends disponibles (`APIManager`, `OllamaManager`, `GGUFManager`, `KoboldManager`). La méthode `get_active_manager()` retourne le gestionnaire correspondant au backend actuellement configuré (`self.backend_type`), ou `None` si ce backend n'est pas disponible.

### Appel standard vs streaming

- `call_chat_api()` : appel classique, attend la réponse complète avant de la retourner.
- `call_chat_api_streaming()` : appel avec callback — chaque token généré est transmis à la fonction `callback(chunk)` au fur et à mesure. Utilisé pour l'affichage en temps réel dans l'interface. Seuls les backends API et GGUF supportent le streaming ; les autres retournent une erreur explicite sans fallback silencieux.

### Backends supportés

Le `backend_type` peut prendre les valeurs suivantes (insensible à la casse) :

| Valeur | Backend |
|---|---|
| `API` | Providers distants (OpenAI, Mistral, Anthropic, Google, GROK, OpenRouter) |
| `OLLAMA` | Ollama local |
| `GGUF` / `GGUF/LLAMA.CPP` | Modèle GGUF local via llama-cpp-python |
| `KOBOLDCPP` | KoboldCpp local |
| `AIHORDE` | AIHorde (réseau distribué) |

### L'Archiviste se distingue

L'attribut `_is_archiviste` marque le contrôleur comme étant l'Archiviste. Quand ce flag est actif et que le logging est activé (`ARCHIVISTE_LOGGING_ENABLED`), chaque appel IA de l'Archiviste est enregistré dans le journal de tokens (`archiviste_logger`). Cela permet de suivre précisément ce que l'Archiviste consomme en tokens à chaque session.

---

## `EmbeddingController` — vecteurs pour la mémoire

`EmbeddingController` est une classe similaire mais dédiée à la génération d'embeddings (vecteurs numériques représentant le sens d'un texte). Ces vecteurs sont stockés dans FAISS et permettent la recherche sémantique dans les souvenirs.

Elle supporte les mêmes backends que `AIController`, mais avec une méthode unique : `create_embedding(text)` qui retourne une liste de flottants (ou `None` en cas d'échec).

---

## Initialisation paresseuse

Les contrôleurs ne sont pas créés au démarrage d'OGMA. Ils sont initialisés par les fonctions `ensure_chat_controller()`, `ensure_archiviste_controller()`, `ensure_embedding_controller()` dans `modules/ogma_core/controllers.py`, uniquement lors du premier appel. La vague d'éveil asynchrone déclenche ces initialisations dans l'ordre approprié (voir [02_app_orchestration.md](02_app_orchestration.md)).
