# Optimisation mémoire

**Sources vérifiées** : `memory_manager.py` (fonction `clean_conversational_noise`), `archiviste_memory_optimizer.py` (pipeline `get_optimized_context`)

---

## Problème de la dilution sémantique

Quand un utilisateur écrit "tu sais, j'ai l'impression que mon rapport au travail a changé depuis qu'on a parlé de mes projets", l'embedding de cette phrase entière est dominé par les mots courants (impressions, rapport, depuis). Les concepts importants (travail, projets) sont noyés dans le bruit.

Une recherche FAISS sur cet embedding retourne des souvenirs vaguement similaires au registre de la phrase, pas les souvenirs les plus pertinents.

---

## Nettoyage du bruit conversationnel

`clean_conversational_noise()` dans `memory_manager.py` applique un premier filtre purement algorithmique : suppression des stopwords, des formules de politesse, des marqueurs de discours. La requête "tu sais, j'ai l'impression que mon rapport au travail a changé" devient "rapport travail changé".

Ce nettoyage est systématique et ne coûte rien en tokens.

---

## Seuil adaptatif : Python ou IA

Si la requête nettoyée contient **6 mots ou moins**, elle est utilisée directement comme query d'embedding — le nettoyage Python suffit.

Si elle dépasse 6 mots, l'Archiviste est appelé pour filtrer sémantiquement : il sélectionne 4 à 6 mots-clés essentiels parmi ceux présents. Il ne peut rien ajouter, seulement filtrer. Cela évite les hallucinations de concepts absents du message original.

---

## Génération de queries stratégiques

L'Archiviste génère jusqu'à 5 queries stratégiques couvrant différents angles sémantiques :

- La query principale (intention directe)
- Une version avec résolution des pronoms possessifs (`mon`/`ma` → nom de l'utilisateur)
- Des synonymes ou variations
- Un contexte temporel si la requête mentionne une période
- Une reformulation déclarative

Ces 5 queries sont soumises en batch à `search_memories_batch()`.

---

## Mécanisme Smart Stop

La recherche batch s'arrête avant d'avoir utilisé les 5 queries si le taux de redondance entre les résultats dépasse 80% (seuil `stop_threshold`). Quand les nouvelles queries ne ramènent que des souvenirs déjà trouvés par les premières, continuer ne sert à rien.

Les métriques de la recherche indiquent le nombre de queries effectivement utilisées vs planifiées.

---

## Filtrage final par l'Archiviste

Parmi les candidats retenus (7 maximum), l'Archiviste évalue la pertinence contextuelle réelle de chaque souvenir par rapport au message original. Il ne se base pas sur le score vectoriel mais sur la compréhension du lien entre le souvenir et la conversation en cours.

Les 2 souvenirs les mieux classés sont transmis en texte intégral à l'IA principale. Les suivants sont transmis en résumé court.

Seuls les souvenirs retenus par ce filtre final entrent en cooldown dans le déduplicateur — pas les candidats écartés.
