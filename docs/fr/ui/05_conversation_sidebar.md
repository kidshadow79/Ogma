# Sidebar des conversations

**Source vérifiée** : `ogma_ui_conversations.py`

---

## Rôle

La sidebar est le gestionnaire de navigation entre les conversations. Elle liste les conversations disponibles, permet d'en créer de nouvelles, de les renommer, de les supprimer, et d'accéder aux fonctions de mémorisation.

---

## Affichage des messages

La fonction `_message()` (dans `ogma_ui_conversations.py`) gère le rendu d'un message dans la zone chat. Elle utilise `parse_thinking_format()` et `parse_introspection_format()` de `utils/message_parsers.py` pour détecter et afficher différemment :
- Les blocs de réflexion interne de l'IA
- Les blocs d'introspection du Cognitive Mirror
- Le contenu textuel standard

Les images dans les messages sont traitées spécifiquement : les underscores dans les URLs sont échappés pour éviter l'interprétation Markdown de NiceGUI.

---

## Sélection multiple

La sidebar supporte la sélection multiple de conversations pour suppression en lot. Les identifiants sélectionnés sont stockés dans un set global `_selected_conversations`. La suppression en lot demande confirmation avant d'agir.

---

## Mémorisation de conversation

Une option dans la sidebar permet de "mémoriser" une conversation entière. L'Archiviste analyse le contenu complet et en extrait des informations pour la mémoire long terme. Cette opération est distincte de la mémorisation automatique des phrases magiques — elle est déclenchée manuellement.

---

## Échange de données avec ogma_ng

`ogma_ui_conversations.py` ne peut pas importer directement `ogma_ng` à l'initialisation. La fonction `_get_ogma()` effectue un import paresseux lors de l'utilisation, après qu'`ogma_ng` est complètement chargé.
