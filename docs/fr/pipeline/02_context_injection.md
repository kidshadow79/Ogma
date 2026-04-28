# Injection de contexte dans le prompt système

**Sources vérifiées** : `ogma_ng.py` (construction du prompt), `logic_callbacks.py` (`chat_fn`), `injection_deduplicator.py`, `data/persistent_context.txt`, `data/ego_compiled.json`

---

## Problème fondamental

L'IA principale n'a pas de mémoire native. Elle ne sait qui elle est, ni ce qu'elle connaît de l'utilisateur, qu'à partir de ce que lui transmet chaque requête. L'injection de contexte est le mécanisme qui transforme un modèle de langage générique en une IA personnalisée et mémorielle.

OGMA injecte plusieurs couches d'informations dans chaque requête. L'enjeu est d'être à la fois exhaustif (ne pas manquer un souvenir pertinent) et économique (éviter de gaspiller des tokens avec des redondances).

---

## Composition du prompt système

Le prompt système final est une concaténation ordonnée de blocs séparés par des sauts de ligne. L'ordre de priorité est le suivant :

### 1. Ego compilé

Le fichier `data/ego_compiled.json` contient les traits d'identité de l'IA principale, construits au fil des conversations. Ces traits décrivent la personnalité, les valeurs, les préférences de l'IA.

L'ego est injecté en premier pour que les instructions suivantes soient lues dans ce cadre identitaire.

### 2. Instructions système principales

Le texte principal définissant le rôle, les comportements attendus et les règles de fonctionnement de l'IA. Configuré dans `settings.json` → `prompts.instructions`.

### 3. Contexte persistant utilisateur

Contenu du fichier `data/persistent_context.txt`, éditable directement par l'utilisateur. Ce fichier permet d'injecter des informations permanentes : nom de l'utilisateur, contexte de vie, préférences durables. Il survit aux rechargements de l'application.

### 4. Contexte visuel

Si l'agent de perception (webcam) est actif et a détecté des événements depuis la dernière requête, ils sont injectés ici sous forme de liste d'observations.

### 5. Instructions de perception

Si la webcam est active, un bloc d'instructions spécifique est ajouté pour guider l'IA dans l'interprétation des données visuelles.

---

## Contexte mémoire : une injection différente

Les souvenirs récupérés par `get_parallel_context()` ne sont **pas** injectés dans le prompt système. Ils ont été insérés dans l'historique de conversation comme messages système intermédiaires lors de tours précédents.

Ce choix d'architecture évite une duplication massive : si les souvenirs étaient à la fois dans l'historique et dans le system prompt, l'IA les verrait deux fois, ce qui représenterait un gaspillage de 40 à 60% des tokens de contexte selon les mesures effectuées.

---

## Gestion de la fenêtre de contexte

L'historique de conversation est tronqué avant l'appel IA pour rester sous 75% de la longueur de contexte maximale du modèle configuré. Les messages sont retirés depuis les plus anciens. Les contenus multimodaux (images) dans les anciens messages sont ignorés lors du comptage pour éviter les biais.

---

## Résumé de flux

```
ego_compiled.json
    +
instructions système (settings.json)
    +
persistent_context.txt
    +
contexte visuel (optionnel)
    +
instructions perception (si webcam active)
    │
    └── → prompt système final
            +
        historique tronqué (souvenirs déjà injectés)
            +
        message utilisateur actuel
            │
            └── → appel IA principale
```
