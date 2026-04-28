# TTS sans conflit

**Sources vérifiées** : `modules/audio/tts_utils.py` (via shim `tts_conflict_free.py`), `ConflictFreeTTSManager`

---

## Problèmes adressés

Le TTS dans OGMA se heurte à plusieurs conflits techniques :

- **OpenCV vs pygame** : l'agent de perception (webcam) utilise OpenCV, qui entre en conflit avec pygame au niveau des handles audio sur Windows
- **NiceGUI** : le framework NiceGUI exécute une boucle d'événements asyncio qui peut entrer en conflit avec les opérations audio synchrones
- **Threading** : plusieurs composants peuvent vouloir parler en même temps (streaming IA + notification + réponse audio)
- **Fichiers temporaires Windows** : les processus audio gardent les fichiers `.mp3` ouverts, empêchant leur suppression immédiate

`ConflictFreeTTSManager` résout ces problèmes par une architecture à file d'attente dédiée.

---

## Architecture file d'attente

Un thread worker dédié consomme les requêtes TTS depuis `speech_queue`. L'interface principale ne bloque jamais sur l'audio : elle envoie une requête dans la file et continue. Le worker traite les requêtes séquentiellement.

---

## Streaming par phrases

Pendant la génération de réponse IA, le TTS peut commencer avant que la réponse soit complète. Le système détecte les fins de phrase (`.`, `!`, `?`) dans le stream de tokens et enfile chaque phrase dès qu'elle est complète via `_sentence_queue`. Cela réduit la latence perçue.

---

## Gestion de perception

Un flag `perception_active` suspend le TTS quand l'agent de perception est actif. La webcam et le TTS partagent les ressources audio de manière exclusive.

---

## Nettoyage des fichiers

Les fichiers audio temporaires (`ogma_tts_*.mp3`) sont stockés dans `data/audio_temp/`. Au démarrage, les restes d'une session précédente sont supprimés (cas d'un crash). À la fermeture propre, `atexit` garantit le nettoyage complet.
