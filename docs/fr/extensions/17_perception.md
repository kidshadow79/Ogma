# Perception (extension) — Les yeux d'OGMA

**Source vérifiée** : `extensions/perception_ui.py`, `extensions/perception_agent.py`

---

*Cette page documente l'extension perception en tant que module. Pour la documentation de l'interface dédiée et de l'agent de capture, voir :*
- *[perception/01_perception_ui.md](../perception/01_perception_ui.md)*
- *[perception/02_perception_agent.md](../perception/02_perception_agent.md)*

---

## Pattern singleton

`extensions/perception_ui.py` expose l'extension via le pattern singleton standard :
- `get_perception_ui()` — retourne l'instance unique
- `get_ui_components()` — retourne le bouton header pour intégration dans `ogma_headers.py`

## Intégration dans le pipeline

Quand la perception est active, chaque message envoyé par l'utilisateur déclenche une capture webcam (`capture_for_chat()`). L'image capturée est encodée en base64 et attachée au message comme contexte visuel multimodal, avant d'être envoyée à l'IA principale.

Cette injection se fait dans `logic_callbacks.py` via `get_parallel_context()` qui appelle l'extension perception si disponible.
