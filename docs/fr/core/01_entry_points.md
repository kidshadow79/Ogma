# Points d'entrée et cycle de vie applicatif

**Sources vérifiées** : `launch_ogma.py`, `ogma_ng.py`, `stop_signal.py`

---

## Vue d'ensemble

OGMA démarre via un seul script :

| Script | Usage |
|---|---|
| `launch_ogma.py` | Point d'entrée unique — vérifie l'environnement, installe les dépendances manquantes, bootstrap les fichiers de données au premier lancement. |

Ce script aboutit à l'appel de `run_ogma()` dans `ogma_ng.py`.

## `launch_ogma.py` — le lanceur complet

Ce script est conçu pour qu'un premier démarrage sur une machine vierge se passe bien. Avant de lancer l'interface, il prend en charge plusieurs responsabilités que `start_ogma.py` n'a pas.

### Préparation de l'environnement

`launch_ogma.py` configure l'encodage UTF-8 pour la console Windows, charge un fichier `.env` si `python-dotenv` est installé, et vérifie que les dépendances critiques (`nicegui`, `faiss-cpu`, `sqlalchemy`) sont présentes — les installant via `pip` si elles manquent.

### Bootstrap des données

Au premier lancement, certains fichiers de configuration n'existent pas encore. Le script les copie depuis leurs modèles par défaut :

- `data/settings.example.json` → `data/settings.json`
- `data/persistent_context.default.txt` → `data/persistent_context.txt`
- `data/memory/memories.seed.db` → `data/memory/memories.db` (si le seed existe)

Cette logique utilise une condition "si le fichier cible est absent", donc une configuration existante n'est jamais écrasée.

### Sélection du port

Par défaut, le serveur écoute sur `0.0.0.0:8080`. Ces valeurs sont surchargeables via les variables d'environnement `OGMA_HOST` et `OGMA_PORT`. Si le port demandé est occupé, le script tente automatiquement les neuf ports suivants (8080 → 8089).

---

## Ce qui se passe dans `ogma_ng.py` au démarrage

### Chargement du module

Quand `launch_ogma.py` importe `ogma_ng`, Python exécute le niveau module du fichier. C'est là que sont importés tous les composants d'OGMA : contrôleurs IA, gestionnaire mémoire, audio, conversations, extensions. Ces imports peuvent afficher des messages dans les logs — c'est normal et voulu, pour rendre visible ce qui est chargé ou absent.

Les extensions optionnelles sont importées de façon défensive (avec `try/except`), et des flags de disponibilité sont positionnés. Une extension qui échoue à l'import ne bloque pas le démarrage.

### `run_ogma(host, port)`

Cette fonction fait trois choses avant de démarrer le serveur web :

1. **Expose les dossiers statiques** : le dossier `static/` (CSS, JS, images) et `data/generated_images/` (images générées) sont montés sur des routes HTTP si ces dossiers existent.
2. **Pré-charge le modèle GGUF si nécessaire** : si la configuration indique un backend `GGUF/llama.cpp`, le contrôleur IA est initialisé avant que NiceGUI démarre. Cela évite de bloquer le WebSocket pendant le chargement d'un modèle local qui peut prendre plusieurs secondes.
3. **Enregistre un nettoyage à la fermeture** : via `atexit`, une routine de clôture est enregistrée pour libérer l'audio, compiler l'ego et consolider la biographie utilisateur en cas d'arrêt propre du processus.

Le serveur est ensuite lancé avec `ui.run()`, avec `reload=False` (pas de hot-reload), `reconnect_timeout=600` (les connexions lentes ou intermittentes ont 10 minutes pour se reconnecter), et un `storage_secret` fixe pour que les sessions NiceGUI persistent entre relances.

---

## `main_page()` — la page principale

`main_page()` est appelée par NiceGUI à chaque connexion sur `/`. Elle construit l'interface utilisateur complète.

Son rôle principal est de gérer la **session utilisateur** : si une session active existe dans `app.storage.user`, l'utilisateur est restauré silencieusement. Sinon, une boîte de connexion s'affiche. C'est ce mécanisme qui permet de retrouver son contexte après un rechargement de page.

Une fois la session établie, la page construit le header, la sidebar, le panneau de chat et le footer, puis lance `_async_awakening()` en arrière-plan — la routine qui charge les souvenirs et prépare le contexte de la conversation.

---

## Arrêt de l'application

Il existe deux chemins d'arrêt :

**Depuis l'interface** : le bouton de fermeture ouvre une confirmation. Si l'utilisateur valide, OGMA exécute ses routines de clôture (journal de bord, compilation ego, élagage du cache cognitif) puis termine le processus avec `os._exit(0)`.

**Interruption externe** : si le processus reçoit un `Ctrl+C` ou est tué proprement, la routine enregistrée via `atexit` s'exécute. Elle effectue une partie des mêmes opérations de clôture, mais sans les étapes spécifiques à l'interface (journal de bord, par exemple).

---

## `stop_signal.py` — signal d'interruption global

Ce petit module expose un état global (`_stop_requested`) qui permet d'interrompre des opérations longues depuis n'importe quel endroit du code. Les composants qui génèrent du texte en streaming (contrôleurs IA, Archiviste) peuvent appeler `check_stop_and_raise()` à intervalles réguliers pour détecter une demande d'arrêt et lever `StopAsyncIteration`.

Ce mécanisme est utilisé notamment pour interrompre la génération en cours quand l'utilisateur clique sur un bouton d'arrêt dans l'interface.

---

## Flux de démarrage nominal

```
python launch_ogma.py
  │
  ├── Vérification des dépendances (pip install si manquant)
  ├── Bootstrap des fichiers de données (settings.json, etc.)
  ├── Sélection du port (8080 → 8089)
  │
  └── run_ogma(host, port)
        │
        ├── Montage /static et /generated
        ├── Pré-chargement GGUF si configuré
        ├── Enregistrement atexit cleanup
        │
        └── ui.run(...)
              │
              └── Connexion navigateur → main_page()
                    │
                    ├── Vérification / restauration session
                    ├── Construction de l'interface
                    └── _async_awakening() en arrière-plan
```
