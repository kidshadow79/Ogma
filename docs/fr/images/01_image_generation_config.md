# Configuration de la génération d'images

**Source vérifiée** : `ogma_image_config.py`

---

## Providers supportés

OGMA supporte 5 providers de génération d'images text-to-image :

| Provider | Identifiant | Caractéristiques |
|---|---|---|
| GROK (xAI) | `GROK` | grok-2-image-1212, mode Spicy disponible |
| OpenAI | `OpenAI` | DALL-E 3 et 2, très censuré |
| Google | `Google` | Imagen 3.0 (standard et fast), modérément censuré |
| Kie.ai | `Kie` | Multi-modèles ($0.004 à $0.10/image), Unfiltered |
| WaveSpeed.ai | `WaveSpeed` | Multi-modèles ($0.005 à $0.025), Unfiltered/Spicy |

---

## Image-to-Image

Kie.ai et WaveSpeed.ai supportent le mode **Image-to-Image** : une image existante est fournie comme base, l'IA la transforme selon la description textuelle.

---

## Niveau de censure

Chaque provider a un champ `nsfw` dans sa configuration :
- `nsfw: False` — censuré (OpenAI, Google)
- `nsfw: True` — moins censuré ou Unfiltered (GROK, Kie, WaveSpeed)

Ce champ est utilisé dans l'interface pour indiquer le niveau de censure à l'utilisateur.

---

## Interface de configuration

`ogma_image_config.py` expose un panneau NiceGUI de sélection du provider et du modèle, avec indication du prix par image pour les providers facturés à l'usage (Kie, WaveSpeed).

La configuration active est persistée dans `settings.json`.
