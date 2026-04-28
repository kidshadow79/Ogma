# Analyse de profondeur et contours

**Sources vérifiées** : `extensions/perception_agent.py` (imports et utilisation), structure des extensions (`depth_manager.py`, `contour_analyzer.py` référencés)

---

## DepthManager

Le DepthManager estime la profondeur de la scène capturée par la webcam. Il produit une carte de profondeur qui permet à l'IA principale de comprendre la disposition spatiale des éléments : ce qui est proche, ce qui est loin.

Ce module est optionnel : l'agent de perception vérifie sa disponibilité au démarrage et fonctionne sans lui si les dépendances ne sont pas installées.

---

## ContourAnalyzer

Le ContourAnalyzer détecte les formes et contours dans les frames webcam. Il identifie les objets distincts dans la scène et peut fournir une description structurée des éléments visuels présents.

Comme le DepthManager, il est optionnel et vérifié séparément au démarrage.

---

## Intégration dans l'agent

L'agent de perception (`perception_agent.py`) utilise ces deux modules si disponibles pour enrichir les événements qu'il place dans `event_queue`. Les événements peuvent ainsi porter des informations de profondeur et de contour en plus de la détection de base (mouvement, présence).

Ces enrichissements sont transmis à l'IA principale via le contexte visuel injecté dans le prompt (voir [docs/pipeline/02_context_injection.md](../pipeline/02_context_injection.md)).

---

Note : Ces modules n'ont pas été inspectés directement. Comportements décrits d'après les imports et usages dans `perception_agent.py`. [NON VÉRIFIÉ en détail — structure interne des modules non inspectée]
