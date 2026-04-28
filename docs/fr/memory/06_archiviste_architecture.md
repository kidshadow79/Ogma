# L'Archiviste — le deuxième cerveau analytique

**Sources vérifiées** : `core_logic.py` (classe `AIController`, flag `_is_archiviste`), `archiviste_memory_optimizer.py`, `archiviste_logger.py`, `ogma_ng.py` (instanciation `_archiviste_controller`)

---

## Pourquoi un deuxième cerveau ?

OGMA repose sur une conviction architecturale : une IA qui doit à la fois être chaleureuse, spontanée et empathique dans le dialogue, ET rigoureuse, précise et exhaustive dans la gestion de la mémoire, ne peut pas bien faire les deux avec le même jeu de paramètres.

L'IA principale est réglée pour la créativité et la fluidité (température 0.7). Elle dialogue, ressent, s'adapte. L'Archiviste est réglé pour la précision et la cohérence (température 0.3). Il analyse, encode, structure.

Ces deux contrôleurs sont des instances distinctes de la même classe `AIController`, mais configurées différemment — et potentiellement sur des backends différents.

---

## Ce que fait l'Archiviste

L'Archiviste intervient à trois moments :

**1. À l'ajout d'un souvenir**
Quand l'IA principale déclenche la phrase magique de mémorisation, le texte brut est envoyé à l'Archiviste. Celui-ci produit un JSON structuré : type du souvenir, titre en style Jeopardy (deux questions dont le texte est la réponse), résumé, scoring d'impact avec la formule multiplicateur, valence, résonances affectives, commentaire analytique. Ce JSON est stocké dans SQLite.

**2. À la recherche contextuelle**
Quand l'IA principale a besoin d'un contexte mémoriel (avant de répondre), l'Archiviste reçoit les souvenirs les plus proches et en génère une synthèse ciblée. Il ne produit pas une liste brute — il résume ce qui est pertinent pour la question en cours.

**3. Dans l'optimiseur mémoire**
`ArchivisteMemoryOptimizer` est une couche supplémentaire qui, avant même de lancer la recherche FAISS, demande à l'Archiviste d'analyser la requête et d'en extraire les concepts clés. Cela produit des embeddings plus concentrés sur le signal utile, et détermine si la recherche doit porter sur les souvenirs personnels, les souvenirs conversationnels, ou les deux.

---

## `ArchivisteMemoryOptimizer` — chercher mieux, pas plus

L'optimizer résout un problème concret : embedder une question longue ("tu te souviens quand je t'avais parlé de mon projet de reconversion, on avait aussi évoqué l'organisation de mon temps") produit un vecteur dilué. La requête contient trop d'idées pour qu'un seul vecteur soit précis sur toutes.

La solution : l'Archiviste lit la question et en extrait 2 à 4 mots-clés essentiels. Ces mots-clés sont embeddés séparément, produisant des vecteurs plus concentrés. Les résultats sont dédupliqués, puis l'Archiviste génère une synthèse unifiée en un seul appel (au lieu de deux appels séparés pour récupération puis synthèse).

---

## Monitoring des tokens — `ArchivisteLogger`

L'Archiviste est identifié par le flag `_is_archiviste = True` sur son contrôleur. Quand ce flag est actif et que `ARCHIVISTE_LOGGING_ENABLED` est à `True`, chaque appel à `call_chat_api()` est enregistré dans `data/archiviste_tokens_debug.jsonl`.

Chaque entrée contient la source de l'appel, les messages envoyés, la réponse reçue, et une estimation du nombre de tokens consommés (calculée par heuristique : 4 caractères ≈ 1 token). Ce journal permet de comprendre précisément ce que l'Archiviste consomme et d'identifier les sources d'appels les plus coûteuses.

---

## Séparation transparente pour l'utilisateur

L'utilisateur ne voit pas l'Archiviste. Il ne lui parle pas, il ne lit pas ses sorties directement. L'Archiviste travaille toujours en arrière-plan, silencieusement. La seule trace visible est la qualité des souvenirs stockés et la pertinence du contexte injecté dans les réponses de l'IA principale.
