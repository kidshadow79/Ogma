# Recherche plein texte (FTS5)

**Source vérifiée** : `memory_manager.py` (fonction `_search_fts5`, table `memories_fts`)

---

## Rôle dans la recherche hybride

La recherche plein texte est l'un des deux moteurs du système de recherche hybride de OGMA. Elle complète la recherche vectorielle FAISS en permettant de retrouver des souvenirs dont les mots correspondent exactement à la requête, même quand la similarité sémantique est faible.

Exemple concret : si la requête mentionne un prénom, un lieu spécifique, ou un terme technique exact, FAISS peut ne pas trouver le bon souvenir (les embeddings capturent la sémantique, pas la correspondance lexicale exacte). FTS5 y répond directement.

---

## Table `memories_fts`

Une table virtuelle SQLite FTS5 est créée en miroir de la table principale `memories`. Elle est maintenue automatiquement par SQLite à chaque insertion ou modification.

FTS5 utilise l'algorithme **BM25** pour calculer la pertinence. BM25 tient compte de la fréquence d'un terme dans le document (TF) et de sa rareté dans l'ensemble des documents (IDF), ce qui donne naturellement plus de poids aux termes distinctifs.

---

## Nettoyage de la requête

Avant de soumettre une requête à FTS5, les caractères spéciaux sont supprimés (FTS5 interprète certains symboles comme des opérateurs de recherche et peut lever des erreurs). La requête est normalisée en espaces simples.

---

## Score FTS5

La valeur `rank` retournée par FTS5 est un nombre négatif : plus il est négatif, meilleur est le résultat. Le module le convertit en score positif normalisé entre 0 et 1 via la formule :

$$score = \frac{1}{1 + |rank|}$$

Cette normalisation rend le score FTS5 compatible avec le score FAISS pour la fusion hybride.

---

## Fusion avec FAISS

Le score final d'un souvenir candidat est calculé en combinant les deux moteurs selon la formule vérifiée dans `memory_manager.py` :

$$score_{final} = 0.6 \times score_{FAISS} + 0.4 \times score_{FTS5} + 0.2 \times bonus_{exact}$$

Le bonus de 0.2 est ajouté quand le terme de la requête apparaît tel quel (correspondance exacte) dans le texte du souvenir.

Un souvenir absent de l'un des deux moteurs obtient simplement un score de 0 pour ce moteur — il n'est pas exclu, mais sa priorité diminue.
