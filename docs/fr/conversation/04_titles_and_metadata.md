# Titres et métadonnées des conversations

**Sources vérifiées** : `conversations/conversation_utils.py`, `conversations/conversation_index.py`

---

## Génération automatique du titre

`make_title_from_text()` dans `conversation_utils.py` génère un titre à partir du premier message utilisateur. La logique est purement algorithmique (sans appel IA) :

1. Nettoyage du texte (ponctuation, caractères spéciaux)
2. Sélection des premiers mots significatifs
3. Troncature à 60 caractères maximum (57 + "..." si dépassement)

Ce titre sert d'identifiant lisible dans la liste des conversations. Il n'est pas regénéré automatiquement si l'utilisateur le renomme manuellement.

---

## Métadonnées dans l'index

L'index `data/conversations/index.json` maintient pour chaque conversation :

| Champ | Description |
|---|---|
| `title` | Titre généré ou défini manuellement |
| `created_at` | Horodatage de création |
| `last_modified` | Horodatage de dernière modification |

Ces métadonnées sont légères intentionnellement : l'index doit rester rapide à charger même avec des centaines de conversations.

---

## Renommage

Le renommage met à jour le titre dans deux endroits : le fichier JSON de la conversation et l'entrée dans l'index. Ces deux opérations sont effectuées séquentiellement. En cas d'erreur, l'état peut être partiellement incohérent entre le fichier et l'index — ce cas est géré par les fonctions d'affichage qui lisent le fichier en priorité.

---

## Conversations mémorisées

Une conversation peut être marquée comme "mémorisée" : l'Archiviste l'analyse intégralement et en extrait les informations pertinentes pour la mémoire long terme. Ce marquage est stocké dans les métadonnées de la conversation dans son fichier JSON.
