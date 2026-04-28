# Stockage et index des conversations

**Sources vérifiées** : `conversations/conversation_index.py`, `data/conversations/` (structure observée)

---

## Format de stockage

Chaque conversation est stockée dans un fichier JSON dans `data/conversations/`. Le nom du fichier suit le format `YYYY-MM-DD_HH-MM-SS_xxxx.json` où les 4 derniers caractères sont un identifiant court unique.

Un fichier conversation contient :
- `messages` : liste chronologique des échanges `{role, content, timestamp}`
- `summaries` : résumés progressifs générés par le `ConversationSummarizer`
- Métadonnées : titre, date de création, date de dernière modification

---

## Index central

`data/conversations/index.json` est un dictionnaire qui mappe chaque `conv_id` à ses métadonnées légères : titre, date de création, date de dernière modification. Cet index évite de lire tous les fichiers JSON pour lister les conversations dans la sidebar.

Les fonctions `load_conversation_index()` et `save_conversation_index()` dans `conversations/conversation_index.py` gèrent cet index. En cas d'erreur de lecture, la fonction retourne un dictionnaire vide plutôt que de lever une exception.

---

## Opérations disponibles

| Opération | Comportement |
|---|---|
| Créer | Nouveau fichier JSON + entrée dans l'index |
| Charger | Lecture du fichier JSON par `conv_id` |
| Renommer | Mise à jour du titre dans le fichier et dans l'index |
| Supprimer | Suppression du fichier + retrait de l'index |
| Lister | Lecture de l'index uniquement |

---

## Dossier `data/conversations/`

Le dossier est créé automatiquement au premier lancement si absent. Les conversations sont triées par date via le format de nommage chronologique du fichier. Le fichier `index.json` est le seul fichier non-conversation dans ce dossier.
