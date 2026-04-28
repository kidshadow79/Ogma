# Interface de perception (UI)

**Sources vérifiées** : `ogma_perception.py`, `extensions/perception_ui.py`

---

## Concept

La perception est la capacité d'OGMA à voir le monde via une webcam. L'interface dédiée (`ogma_perception.py`) est une page NiceGUI distincte qui s'ouvre dans une **fenêtre popup séparée** (580×440 px).

Cette séparation est intentionnelle : le flux vidéo en temps réel et l'interface de chat principale ont des besoins de rafraîchissement très différents. Mettre la webcam dans la fenêtre principale surchargerait l'interface.

---

## Fenêtre popup

La fenêtre popup sauvegarde sa position et sa taille dans le `localStorage` du navigateur. À chaque ouverture, elle restaure sa dernière position. Ce comportement est implémenté en JavaScript injecté au chargement de la page.

---

## Singleton `perception_ui`

L'extension `extensions/perception_ui.py` est un singleton. `ogma_perception.py` récupère l'instance via `get_perception_ui()` pour construire l'interface. Si l'extension n'est pas disponible, la page affiche un message d'erreur.

---

## État dans localStorage

L'état d'activation de la perception (active/inactive) est synchronisé dans le `localStorage` du navigateur. Cela permet à l'interface principale de savoir si la perception est active sans polling.

---

## Contenu de l'interface

Le panneau de perception affiche :
- Le flux webcam en temps réel
- Le statut de l'agent (actif/inactif)
- Les événements détectés récemment
- Les paramètres de capture (résolution, fréquence)
- Les modules d'analyse disponibles (depth, contours)
