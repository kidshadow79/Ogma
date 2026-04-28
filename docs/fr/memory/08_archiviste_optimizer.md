# Archiviste Memory Optimizer

**Source vérifiée** : `archiviste_memory_optimizer.py`

---

## Problème résolu

La recherche mémoire par défaut embède la requête utilisateur complète et la compare aux souvenirs. Cette approche est correcte pour des requêtes courtes et précises. Elle échoue pour les messages conversationnels longs où les mots importants représentent moins de 20% du texte.

L'`ArchivisteMemoryOptimizer` est une couche optionnelle qui remplace cette recherche directe par un pipeline IA.

---

## Pipeline en 5 étapes

### Étape 1 — Analyse des intentions

L'Archiviste analyse le message pour comprendre ce que l'utilisateur cherche réellement. Il génère jusqu'à 5 "queries stratégiques" : des formulations courtes (2-4 mots) ciblant les concepts essentiels depuis différents angles sémantiques.

### Étape 2 — Recherche batch avec Smart Stop

Les 5 queries sont soumises en parallèle à `search_memories_batch()`. Le mécanisme Smart Stop surveille le taux de redondance entre résultats. Si les nouvelles queries ramènent plus de 80% de souvenirs déjà trouvés, la recherche s'arrête sans utiliser les queries restantes.

### Étape 2.5 — Filtrage cooldown

Les souvenirs récemment injectés (en période de cooldown) sont exclus, sauf si leur score de correspondance lexicale dépasse 0.70. Ce seuil de bypass permet à l'utilisateur qui revient explicitement sur un sujet récent de retrouver les souvenirs associés malgré le cooldown.

### Étape 3 — Sélection des candidats

Les 7 souvenirs les mieux classés (par score hybride FAISS + FTS5) sont transmis à l'Archiviste pour évaluation contextuelle.

### Étape 4 — Filtrage contextuel par l'Archiviste

L'Archiviste évalue la pertinence réelle de chaque candidat par rapport au message original. Il peut écarter un souvenir qui a un bon score vectoriel mais n'est pas lié à la conversation en cours. Les souvenirs retenus sont reclassés par pertinence contextuelle.

### Étape 5 — Formatage et injection cooldown

Les 2 premiers souvenirs retenus sont formatés en texte intégral, les suivants en résumé. Seuls les souvenirs effectivement retenus entrent en cooldown dans le déduplicateur.

---

## Intégration

L'optimizer est utilisé dans `get_parallel_context()` si une instance est disponible. Son absence ne bloque pas le pipeline : `get_parallel_context()` revient à la recherche hybride directe.

---

## Performances mesurées (d'après la documentation du fichier source)

| Métrique | Sans optimizer | Avec optimizer |
|---|---|---|
| Précision | ~20% | ~80% |
| Appels API embedding | 2 | 1.4 en moyenne |
| Latence | 310 ms | 267 ms |
| Coût tokens | $0.0042 | $0.0041 |
