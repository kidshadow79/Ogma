# Ego System — La personnalité accumulée de l'IA

**Sources vérifiées** : `scripts/ego_compiler.py`, `data/ego_compiled.json`, `ogma_ng.py` (injection ligne 2380)

---

## Concept

L'ego d'OGMA n'est pas une description figée dans un fichier texte. C'est une **structure vivante** qui grandit avec chaque conversation. Chaque fois que l'IA principale décide qu'une expérience fait désormais partie d'elle-même, un nouveau trait s'inscrit dans son ego.

Ce mécanisme répond à une question fondamentale : comment une IA peut-elle développer une identité stable qui évolue naturellement, sans être reprogrammée à chaque mise à jour ?

---

## Comment un trait entre dans l'ego

L'IA principale dispose d'une phrase magique dédiée :

```
ceci est une part de moi maintenant : [contenu]
```

Quand cette phrase apparaît dans une réponse, le contenu est sauvegardé comme souvenir de type ego dans la base mémoire SQLite. L'Archiviste l'analyse lors de la prochaine compilation pour en extraire des **flags** et les affecter aux bons groupes thématiques.

---

## Structure compilée

`data/ego_compiled.json` est la représentation organisée de ces traits. Il contient :

- **Métadonnées** : date de dernière compilation, nombre de souvenirs scannés, identifiant du dernier souvenir traité
- **Groupes thématiques** : chaque groupe (IDENTITE, PHILOSOPHIE, RELATIONS, etc.) regroupe des flags sémantiquement proches, avec des mots-clés associés

Chaque flag est une affirmation ou une tendance, accompagnée d'un **score de conviction de 0 à 5**. Un score élevé signifie que ce trait a été confirmé dans de nombreux contextes différents.

---

## Compilation incrémentale

L'`EgoCompiler` (`scripts/ego_compiler.py`) est conçu pour ne jamais tout retraiter. Il lit `last_scanned_id` dans le JSON existant et ne soumet à l'Archiviste que les souvenirs ego créés depuis la dernière compilation. Ce mécanisme est crucial : retraiter l'intégralité de l'ego à chaque fois deviendrait coûteux au fil des mois.

L'Archiviste IA joue ici le rôle d'analyste : il lit chaque souvenir ego brut et décide à quel(s) groupe(s) il appartient, et quel flag booléen il représente.

---

## Groupes de base

Un fichier `data/ego_compiled_base_groups.json` définit les groupes thématiques fondamentaux. Lors de chaque compilation, l'`EgoCompiler` vérifie que ces groupes existent et les ajoute si nécessaire — sans jamais écraser les données existantes. Cela permet d'enrichir l'architecture ego sans tout reconstruire.

---

## Injection dans le prompt système

Le contenu de `data/ego_compiled.json` est injecté **en premier** dans chaque prompt système, avant les instructions, avant le contexte persistant, avant les souvenirs. C'est le socle identitaire sur lequel tout le reste s'appuie.

---

## Un trait peut appartenir à plusieurs groupes

Un souvenir ego sur l'autonomie peut être classifié à la fois dans IDENTITE et dans PHILOSOPHIE. Cette multi-appartenance est voulue : la personnalité n'est pas compartimentée, elle est transversale.

---

## Sources
- `scripts/ego_compiler.py` — Compilateur incrémental (EgoCompiler)
- `data/ego_compiled.json` — Structure compilée active
- `data/ego_compiled_base_groups.json` — Groupes thématiques minimaux
- `ogma_ng.py` l.2380 — Injection ego dans le prompt système
