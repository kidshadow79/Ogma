# Text2Image — The AI That Generates Images

**Verified source**: `extensions/text2img/__init__.py`

> French version: [../../fr/extensions/07_text2img.md](../../fr/extensions/07_text2img.md)

---

## Concept

The Text2Image extension allows OGMA to generate images from text descriptions. The main AI can thus illustrate its responses or answer a visual creation request.

---

## Providers

Three providers are supported:

| Provider | Model | Characteristics |
|---|---|---|
| GROK (xAI) | grok-2-image-1212 | Spicy mode available (less censored) |
| OpenAI | DALL-E 3/2 | High quality, censored |
| Google | Imagen 3 | Good quality, moderately censored |

The active provider is configurable in settings.

---

## Usage

The extension exposes a singleton manager (`get_text2img_manager()`). The `generate_image(description)` method is asynchronous and returns the generated image data, displayed in the conversation thread.
