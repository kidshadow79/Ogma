# Organic Planner — L'agenda de l'IA

**Source vérifiée** : `extensions/organic_planner/__init__.py`

---

## Concept

L'Organic Planner est le système de planification d'OGMA. Il permet à l'IA de maintenir une liste de tâches, rendez-vous et engagements, et d'injecter un **briefing** pertinent dans les conversations.

---

## Briefing

La méthode `get_briefing_text()` produit un résumé structuré des éléments planifiés pertinents pour le moment présent (tâches du jour, échéances proches). Ce briefing est injecté dans le contexte système si l'extension est active.

---

## Interaction

L'IA principale peut créer, modifier et supprimer des éléments dans le planner via des phrases naturelles. L'Archiviste peut également suggérer des ajouts au planner lors de ses analyses.

---

## Configuration

Les paramètres de l'extension sont persistés dans `data/organic_planner_settings.json`. Ce fichier est la source de vérité au runtime (voir [CODING_RULES.md](../../CODING_RULES.md) sur la synchronisation JSON/Python).
