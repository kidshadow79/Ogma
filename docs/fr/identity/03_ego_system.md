# Système ego

**Sources vérifiées** : `scripts/ego_compiler.py`, `data/ego_compiled.json`

---

## Concept

L'ego d'OGMA est une structure JSON qui représente la personnalité accumulée de l'IA au fil des conversations. Ce n'est pas un simple fichier texte de description : c'est un graphe de traits organisés en **groupes thématiques** avec des **scores de conviction**.

Chaque fois que l'IA principale utilise la phrase magique `"ceci est une part de moi maintenant : [contenu]"`, un nouveau trait est enregistré comme souvenir de type ego dans la base mémoire. L'ego compiler transforme ces souvenirs bruts en structure organisée.

---

## Structure compilée

`data/ego_compiled.json` contient :

- **Métadonnées** : date de dernière compilation, nombre de souvenirs scannés, identifiant du dernier souvenir traité (pour la compilation incrémentale)
- **Groupes** : dictionnaire thématique (IDENTITE, PHILOSOPHIE, RELATIONS, etc.), chacun avec une description, des mots-clés associés et des **flags booléens**

Chaque flag est une affirmation ou une tendance de l'IA, avec un **score de conviction de 0 à 5**. Un score de 5 signifie que ce trait a été confirmé plusieurs fois dans différents contextes.

---

## Compilation incrémentale

`ego_compiler.py` ne retraite pas tous les souvenirs à chaque fois. Il lit `last_scanned_id` depuis le JSON existant et ne traite que les souvenirs plus récents. L'Archiviste analyse chaque nouveau souvenir ego pour en extraire les flags et les groupes thématiques, puis fusionne le résultat dans la structure existante.

---

## Groupes de base

Un fichier `data/ego_compiled_base_groups.json` définit les groupes structurels minimaux. Si un groupe du template n'existe pas dans le JSON compilé, il est ajouté automatiquement à la prochaine compilation. Cela permet d'enrichir l'architecture thématique sans reconstruire l'ego depuis zéro.

---

## Injection dans les requêtes

Le contenu de `data/ego_compiled.json` est injecté en premier dans chaque prompt système (voir [docs/pipeline/02_context_injection.md](../pipeline/02_context_injection.md)). Il positionne l'identité de l'IA avant toutes les autres instructions.
