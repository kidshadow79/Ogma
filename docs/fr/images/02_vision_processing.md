# Traitement des images en entrée (vision)

**Sources vérifiées** : `core_logic.py` (`_compress_vision_image()`, l.84-148), `extensions/file_processor.py`

---

## Format d'entrée multimodal

Les images sont transmises aux APIs IA au format **base64** embarqué dans les messages, selon le standard multimodal (type `image_url` avec data URI `data:image/jpeg;base64,...`). Ce format est compatible avec tous les providers vision (OpenAI, Anthropic, Google, Mistral Pixtral, etc.).

Les images proviennent de deux sources :
- **Upload utilisateur** : traitées par `extensions/file_processor.py` (voir [docs/files/01_file_uploads.md](../files/01_file_uploads.md))
- **Capture webcam** : traitées par `extensions/perception_agent.py` (voir [docs/perception/02_perception_agent.md](../perception/02_perception_agent.md))

---

## Compression avant envoi

`_compress_vision_image()` dans `core_logic.py` réduit la taille des images avant envoi API. Cela évite des coûts tokens excessifs et des erreurs de taille de payload.

**Processus** :
1. Décode l'image base64
2. Convertit en RGB si nécessaire (RGBA, palette → RGB pour JPEG)
3. Redimensionne en thumbnail à une taille configurable (`target_size × target_size`)
4. Encode en JPEG qualité 85 avec optimisation

La `target_size` est lue depuis les settings. Si elle vaut 0, la compression est désactivée et l'image est transmise telle quelle.

Si PIL n'est pas disponible, la compression est ignorée et l'image originale est transmise.

---

## Métriques

La fonction logue le ratio de compression obtenu : dimensions avant/après, poids en KB avant/après, pourcentage de réduction.

Exemple : `1920x1080 → 512x288 | 1240KB → 87KB (93% réduit)`

---

## Intégration dans le pipeline

Les images encodées sont injectées dans le tableau `content` des messages au format OpenAI (`{"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}`). Ce format est normalisé par `core_logic.py` avant chaque appel API.
