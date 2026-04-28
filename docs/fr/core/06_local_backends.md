# Backends locaux (Ollama, GGUF, KoboldCpp)

**Source vérifiée** : `core_logic.py` (classes `OllamaManager`, `GGUFManager`, `KoboldManager`)

---

## Vue d'ensemble

OGMA peut fonctionner entièrement sans connexion internet grâce à trois backends locaux. Chacun correspond à une façon différente de faire tourner un modèle IA sur la machine de l'utilisateur.

---

## Ollama

Ollama est un serveur local qui télécharge et gère des modèles IA. Il expose une API REST sur `http://localhost:11434` par défaut. `OllamaManager` communique avec ce serveur via HTTP.

Au démarrage, `check_service()` interroge `/api/tags` pour obtenir la liste des modèles disponibles. Si le serveur répond, le manager se marque disponible. Sinon, il se déclare indisponible sans lever d'exception.

Une particularité utile : le manager peut interroger `/api/show` pour découvrir la vraie fenêtre de contexte d'un modèle. Ce résultat est mis en cache pour éviter des requêtes répétées. Cela permet à OGMA de s'adapter automatiquement à la capacité réelle du modèle chargé.

---

## GGUF / llama-cpp-python

Le format GGUF est un format de modèles compressés (quantifiés) qui peuvent s'exécuter localement, en partie sur GPU, en partie sur CPU. OGMA utilise la bibliothèque `llama-cpp-python` pour les charger.

Les fichiers `.gguf` sont placés dans le dossier `models/` à la racine du projet. `GGUFManager` liste les fichiers disponibles et charge le modèle choisi en mémoire au premier appel (ou au démarrage si le mode de pré-chargement est activé).

Le chargement est potentiellement long (plusieurs secondes à plusieurs dizaines de secondes selon la taille du modèle). C'est pourquoi `_async_awakening()` l'exécute dans un thread séparé via `asyncio.to_thread()`.

Le manager contient un garde (`_is_generating`) pour éviter les appels concurrents, car llama-cpp-python n'est pas thread-safe. Si une génération est déjà en cours, un second appel sera bloqué jusqu'à la fin de la première.

Pour les machines avec peu de VRAM, un paramètre `low_vram` est disponible dans les settings (`other_backends.ollama.low_vram`), qui ajuste le comportement de chargement GPU.

---

## KoboldCpp

KoboldCpp est une alternative à llama-cpp-python qui s'exécute comme un serveur local séparé (sur `http://localhost:5001` par défaut). OGMA lui envoie des requêtes HTTP simples.

Par rapport aux autres backends, KoboldCpp présente quelques différences : il ne supporte pas le streaming natif, son format de requête est différent (prompt unique plutôt que liste de messages), et `is_json` est ignoré (il retourne toujours du texte brut). Ces différences sont gérées de façon transparente par le `KoboldManager`.

---

## Disponibilité conditionnelle

`GGUFManager` vérifie si `llama-cpp-python` est installé au chargement du module (`LlamaCPP_AVAILABLE`). Si la bibliothèque est absente, le manager se désactive proprement sans faire planter l'application. Le support Vision GGUF (images en entrée via projecteur multimodal) dépend en plus de `llama-cpp-python[server]` avec handler Llava.
