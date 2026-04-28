# Configuration audio et TTS

**Sources vérifiées** : `ogma_tts_config.py`, `tts_perception_manager.py`

---

## Interface de configuration TTS

`ogma_tts_config.py` expose un panneau de configuration NiceGUI pour les moteurs TTS. Il permet de configurer :

- Le moteur actif (System/pyttsx3, Google Cloud, ElevenLabs, Azure, gTTS, Edge TTS)
- Les paramètres spécifiques au moteur sélectionné (clé API, voix, vitesse, volume)
- Un bouton de test audio pour valider la configuration

La configuration est persistée dans `settings.json` sous la clé `tts`. Elle est appliquée à l'`AudioManager` via `_apply_tts_config_from_settings()` d'`ogma_ng`.

---

## Gestionnaire de conflit TTS/Perception

`TTSPerceptionManager` résout le conflit entre le TTS et l'agent de perception (webcam) au niveau de la configuration. Quand la perception s'active :

1. La configuration TTS courante est sauvegardée en mémoire
2. Le TTS est désactivé dans `settings.json`
3. L'`AudioManager` est rechargé avec la configuration modifiée

Quand la perception se désactive, la configuration TTS originale est restaurée.

Ce mécanisme complète le flag `perception_active` du `ConflictFreeTTSManager` (qui opère au niveau de la file TTS). Les deux protections fonctionnent indépendamment.

---

## Paramètres persistants

La configuration TTS dans `settings.json` contient : le moteur sélectionné, les clés API par service, l'identifiant de voix, la vitesse de parole, le volume. Ces paramètres sont rechargés au démarrage de l'application.
