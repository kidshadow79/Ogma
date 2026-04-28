# Hologram Projector — OGMA en 3D

**Source vérifiée** : `extensions/hologram_projector/__init__.py`

---

## Concept

Le Hologram Projector diffuse une visualisation animée d'OGMA sur un téléphone mobile positionné au centre d'une **pyramide de Pepper's Ghost**. Cette technique optique simple (quatre faces en plexiglas transparent) crée l'illusion d'un hologramme flottant.

---

## Mécanisme technique

L'extension démarre un serveur WebSocket sur la route `/hologram` du serveur NiceGUI principal. Le téléphone mobile ouvre `http://[IP_LAN]:8080/hologram` et reçoit en temps réel l'état de l'IA (blob animé).

Le blob réagit à deux états :
- **Émotion** (`update_emotion(name, intensity)`) : change la couleur du blob selon l'état émotionnel de l'IA
- **Parole** (`update_speaking(bool)`) : fait vibrer le blob quand OGMA parle via TTS

---

## Intégration

Un bouton toggle dans le header active/désactive la diffusion holographique. L'extension s'intègre via le pattern standard `get_ui_components()`.

---

## API publique

```python
initialize_hologram()           # Démarre le serveur
is_available() -> bool
update_emotion(name, intensity) # Couleur blob
update_speaking(bool)           # Vibration blob
get_ui_components() -> dict     # Bouton header
cleanup()
```
