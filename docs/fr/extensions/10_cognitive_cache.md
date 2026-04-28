# Cognitive Cache — La mémoire de travail de l'IA

**Source vérifiée** : `extensions/cognitive_cache/__init__.py`

---

## Concept

Le Cognitive Cache est la **mémoire de travail** de l'IA principale — un espace de notes temporaires, propre à chaque conversation, que l'IA gère elle-même.

Contrairement à la mémoire FAISS (persistante, long terme), le cache cognitif est lié à une conversation et vit le temps de celle-ci.

---

## Contrôle par l'IA

C'est l'IA principale qui écrit dans ce cache, via des phrases magiques internes :

```
CACHE_ADD:[type]:[contenu]    → Ajoute une note
CACHE_DELETE:[id]             → Supprime une note
CACHE_UPDATE:[id]:[contenu]   → Modifie une note
CACHE_CLEAR                   → Vide le cache
```

Ces phrases sont interceptées dans le post-traitement de la réponse IA, jamais montrées à l'utilisateur.

---

## Persistance

Le cache est persisté par conversation dans `data/cognitive_cache/{conv_id}.json`. Seules 10 conversations sont conservées (élagage automatique à la fermeture).

Ce comportement permet à l'IA de reprendre une conversation avec ses notes de travail intactes, tout en évitant une accumulation indéfinie.
