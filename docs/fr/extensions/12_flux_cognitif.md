# Flux Cognitif — Voir penser l'IA

**Source vérifiée** : `extensions/flux_cognitif/__init__.py`

---

## Concept

Le Flux Cognitif est une **visualisation temps réel des décisions internes d'OGMA**. Un overlay ambre translucide affiche en continu les événements cognitifs : injections de l'Archiviste, accès mémoire, contributions du Journal, rêves en cours, décisions du Capability Advisor.

C'est la transparence totale rendue visible — pas un log technique pour développeur, mais un écran qui montre ce que l'IA "pense" pendant qu'elle répond.

---

## Architecture

**StreamCore** (`stream_core.py`) est un singleton qui reçoit les événements cognitifs depuis les différents composants d'OGMA via des hooks dans `ogma_ng.py`. Ces événements sont horodatés et typés (mémoire, archiviste, journal, dream, capability).

**StreamUI** (`stream_ui.py`) est l'overlay NiceGUI qui affiche ces événements en temps réel dans un format lisible.

---

## Sources d'événements

Les hooks dans `ogma_ng.py` logguent automatiquement :
- Les injections de souvenirs par l'Archiviste
- Les accès à la biographie
- Les entrées du Journal de Bord injectées
- Les décisions du Capability Advisor
- Les états du Dream Engine

---

## Philosophie

> "Transparence Totale — rendre visible les pensées de l'IA"

Le Flux Cognitif est la concrétisation de ce pilier fondamental d'OGMA : l'utilisateur ne doit jamais avoir à deviner pourquoi l'IA a dit quelque chose.
