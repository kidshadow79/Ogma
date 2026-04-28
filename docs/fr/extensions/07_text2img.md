# Text2Image — L'IA qui génère des images

**Source vérifiée** : `extensions/text2img/__init__.py`

---

## Concept

L'extension Text2Image permet à OGMA de générer des images à partir de descriptions textuelles. L'IA principale peut ainsi illustrer ses réponses ou répondre à une demande de création visuelle.

---

## Providers

Trois providers sont supportés :

| Provider | Modèle | Caractéristiques |
|---|---|---|
| GROK (xAI) | grok-2-image-1212 | Mode Spicy disponible (moins censuré) |
| OpenAI | DALL-E 3/2 | Haute qualité, censuré |
| Google | Imagen 3 | Bonne qualité, modérément censuré |

Le provider actif est configurable dans les paramètres.

---

## Utilisation

L'extension expose un manager singleton (`get_text2img_manager()`). La méthode `generate_image(description)` est asynchrone et retourne les données de l'image générée, affichée dans le fil de conversation.
