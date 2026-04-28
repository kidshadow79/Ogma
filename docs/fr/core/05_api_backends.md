# Backends distants (API)

**Source vérifiée** : `core_logic.py` (classe `APIManager`)

---

## Rôle de l'`APIManager`

L'`APIManager` gère tous les appels vers des providers IA distants. Il connaît les URLs, les formats de requête et les particularités de chaque provider. Il est utilisé par les trois contrôleurs IA (IA principale, Archiviste, embeddings) quand leur `backend_type` est positionné sur `API`.

---

## Providers supportés

Les providers sont définis dans une table de configuration statique (`API_CONFIG`) :

| Provider | Notes |
|---|---|
| OpenAI | Chat + embeddings. Format standard OpenAI. |
| Anthropic | Format `/messages` spécifique, sans endpoint `/models` public. |
| Mistral | Chat + embeddings. Compatible format OpenAI. |
| Google | Endpoint Gemini, format de requête différent. |
| GROK | API xAI, format compatible OpenAI. |
| OpenRouter | Agrégateur multi-modèles, format OpenAI. |
| AIHorde | Réseau de calcul distribué communautaire, format asynchrone spécifique. |

---

## Configuration

La méthode `configure(provider, api_key, model)` active le manager. Si l'un des trois paramètres est absent ou si le provider est `"Aucun"`, le manager se désactive (`is_available = False`). Il n'y a pas de vérification réseau à ce stade — la configuration est purement locale.

---

## Particularités Anthropic et OpenRouter (mode thinking)

Les modèles de raisonnement Anthropic (ex. `claude-3-7-sonnet`) et certains modèles OpenRouter peuvent retourner un bloc `<thinking>` avant leur réponse. L'`APIManager` détecte et extrait ce contenu dans `_last_thinking_content`, que l'interface peut ensuite afficher séparément dans la zone d'introspection. Ce comportement est transparent pour les appelants.

---

## Streaming

`call_chat_api_streaming()` ouvre une connexion HTTP en streaming (Server-Sent Events pour OpenAI/Mistral/GROK/OpenRouter, format spécifique pour Anthropic) et transmet chaque token à la fonction `callback` passée en paramètre. C'est ce mécanisme qui permet l'affichage progressif des réponses dans l'interface.

---

## Gestion des erreurs

Les messages d'erreur retournés par `APIManager` masquent la clé API si elle y apparaît (fonction interne `_redact_error`). Les erreurs réseau, timeouts et réponses HTTP non-200 sont capturés et retournés comme tuples `(None, message_erreur)` — jamais levés comme exceptions vers l'appelant.
