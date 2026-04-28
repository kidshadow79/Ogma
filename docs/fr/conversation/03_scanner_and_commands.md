# Scanner et commandes de conversation

**Sources vérifiées** : `conversation_scanner.py`, `conversations/conversation_commands.py`

---

## Scanner de conversations

`search_recent_conversations()` dans `conversation_scanner.py` est un moteur de recherche léger par mots-clés dans les conversations passées. Il ne repose sur aucun index ni base vectorielle.

### Comportement

- Scanne les **N conversations les plus récentes** (20 par défaut) en ordre chronologique inverse
- Cherche les mots-clés en mode case-insensitive dans le contenu des messages
- Retourne les correspondances avec un **contexte de 5 messages avant/après** le message trouvé
- Trie les résultats par score (nombre de mots-clés trouvés dans la même conversation)

### Performances

D'après la documentation du fichier source : environ 50 ms pour 20 conversations. Ce scanner fonctionne même sans résumés et sans index.

### Format de retour

Chaque résultat contient : l'identifiant de conversation, la date, l'index du message correspondant, les mots-clés trouvés, un extrait de contexte, et un score.

---

## Commandes conversationnelles

`handle_conversation_commands()` dans `conversations/conversation_commands.py` analyse le texte utilisateur pour détecter des demandes d'accès aux conversations archivées.

### Patterns détectés

Les formulations suivantes déclenchent le chargement d'une conversation :
- `"va lire la conversation [nom]"`
- `"lis-moi la conversation [nom]"`
- `"charge la conversation [nom]"`
- `"ouvre la conversation [nom]"`
- `"accède à la conversation [nom]"`

### Comportement après détection

Quand un pattern est détecté, la conversation est chargée et injectée comme contexte d'attachement pour la requête courante. L'IA principale peut alors répondre à des questions sur cette conversation. La requête n'est pas bloquée : elle continue vers l'IA avec le contexte chargé.

Si le fichier demandé n'existe pas, une notification d'erreur est émise et le traitement s'arrête.
