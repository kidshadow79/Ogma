# Layout global

**Sources vérifiées** : `ogma_ng.py` (structure principale), `ogma_headers.py`, `ogma_ui_conversations.py`

---

## Structure NiceGUI

OGMA utilise le framework NiceGUI pour son interface web. La page principale est construite dans `ogma_ng.py` avec une organisation en trois zones :

```
┌─────────────────────────────────────────┐
│  HEADER (statuts IA, boutons extensions)│
├──────────┬──────────────────────────────┤
│          │                              │
│ SIDEBAR  │     ZONE CHAT               │
│ (convers)│     (messages + saisie)     │
│          │                              │
└──────────┴──────────────────────────────┘
```

---

## Header

Bande supérieure permanente. Contient les indicateurs de statut des 3 contrôleurs IA (Chat, Archiviste, Embeddings), les boutons des extensions activées (Cognitive Mirror, Dream Engine, etc.) et le sélecteur de langue FR/EN. Le contenu du header peut être enrichi dynamiquement par les extensions via leur méthode `get_ui_components()`.

---

## Sidebar conversations

Panneau latéral gauche listant les conversations. Peut être masqué. Contient les contrôles de création, renommage et suppression de conversation, ainsi qu'un champ de recherche. La sidebar est construite par `ogma_ui_conversations.py`.

---

## Zone chat

Zone principale. Affiche l'historique des messages avec rendu Markdown. Le message en cours de streaming est mis à jour token par token via un widget `ui.markdown` dont le contenu est remplacé. Un spinner JavaScript est injecté dans le DOM pour l'indicateur de génération en cours.

---

## Zone de saisie

Bandeau inférieur contenant le champ `ui.textarea` (croissance automatique), les boutons d'attachement de fichier, les commutateurs de représentation utilisateur/IA, et le bouton d'envoi. La référence globale `_input_field` permet aux autres composants (STT audio) d'y écrire.
