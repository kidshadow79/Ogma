# Agent de perception (webcam)

**Source vérifiée** : `extensions/perception_agent.py`

---

## Architecture thread

L'agent de perception tourne dans un thread dédié, séparé de la boucle asyncio principale. Cette isolation est nécessaire car OpenCV (capture webcam) est synchrone et bloquant.

L'agent communique avec le reste d'OGMA via deux files thread-safe :
- `event_queue` : événements détectés (mouvements, présences, changements)
- `visual_queue` : frames vidéo encodées pour l'interface

---

## Capture pour chat

`capture_for_chat()` est appelée lors de l'envoi d'un message si la perception est active. Elle capture une frame, l'encode en JPEG base64, et retourne un objet compatible avec le format multimodal de l'API (type `image_url`). Cette capture est attachée au message envoyé à l'IA principale.

---

## Modules d'analyse

L'agent intègre deux modules optionnels selon les librairies disponibles :

**DepthManager** : analyse la profondeur estimée de la scène (distance des objets). Disponible si les dépendances sont installées.

**ContourAnalyzer** : détection des contours et formes dans l'image. Disponible indépendamment du DepthManager.

Si un module est absent, l'agent démarre sans lui avec une notification.

---

## Intégration TTS

Au démarrage de la perception, `on_perception_start()` est appelée pour suspendre le TTS. À l'arrêt, `on_perception_stop()` restaure le TTS. Si le `TTSPerceptionManager` n'est pas disponible, des fonctions de fallback vides prennent sa place pour que l'agent démarre quand même.

---

## États

| État | Description |
|---|---|
| `inactive` | Thread non démarré |
| `starting` | Initialisation en cours |
| `active` | Capture en cours |
| `stopping` | Arrêt en cours |
