# Communication backend et statut des IA

**Sources vérifiées** : `backend/backend_communication.py`, `backend/ia_status.py`

---

## Contexte

Ces deux modules sont des extractions de `ogma_ng.py` (refactoring de novembre 2025). Ils regroupent les opérations de diagnostic réseau vers les backends IA, utilisées depuis l'interface de configuration.

---

## `backend_communication.py` — lister et tester

Ce module expose deux fonctions utilisées par l'interface de configuration pour aider l'utilisateur à choisir et vérifier son backend :

**`list_models(backend_type, ...)`** : interroge le backend sélectionné pour obtenir la liste des modèles disponibles. Pour les providers API, cela fait un appel réseau authentifié. Pour Ollama, cela interroge le serveur local. Pour GGUF, cela liste les fichiers `.gguf` présents dans le dossier `models/`. En cas d'erreur, retourne une liste vide et un message d'erreur, jamais d'exception.

**`test_connection(backend_type, ...)`** : vérifie que la connexion au backend est fonctionnelle. Retourne un tuple `(succès: bool, message: str)`. C'est ce qui alimente les indicateurs de statut visibles dans l'interface de configuration.

Ces fonctions reçoivent les managers en paramètre plutôt que de les accéder globalement — ce qui les rend indépendantes de l'état d'initialisation d'OGMA et facilite les tests.

---

## `ia_status.py` — tableau de bord des trois IA

`check_global_ia_status()` construit un résumé de l'état des trois contrôleurs IA (IA principale, Archiviste, Embeddings). Pour chaque contrôleur, il lit la section correspondante de `settings.json` (`chat_api`, `reasoning_api`, `embedding_api`) et détermine :

- si un modèle est configuré (`configured: bool`)
- si la connexion est opérationnelle (`available: bool`)
- le nom du modèle actif (`model_name: str`)
- le type de backend (`backend: str`)

Ce statut est affiché dans l'interface pour donner à l'utilisateur une vue d'ensemble de ce qui fonctionne. Il est recalculé à la demande, pas en temps réel.
