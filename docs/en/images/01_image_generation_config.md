# Image Generation Configuration

**Verified source**: `ogma_image_config.py`

> French version: [../../fr/images/01_image_generation_config.md](../../fr/images/01_image_generation_config.md)

---

## Supported providers

OGMA supports 5 text-to-image generation providers:

| Provider | Identifier | Characteristics |
|---|---|---|
| GROK (xAI) | `GROK` | grok-2-image-1212, Spicy mode available |
| OpenAI | `OpenAI` | DALL-E 3 and 2, heavily censored |
| Google | `Google` | Imagen 3.0 (standard and fast), moderately censored |
| Kie.ai | `Kie` | Multi-model ($0.004 to $0.10/image), Unfiltered |
| WaveSpeed.ai | `WaveSpeed` | Multi-model ($0.005 to $0.025), Unfiltered/Spicy |

---

## Image-to-Image

Kie.ai and WaveSpeed.ai support **Image-to-Image** mode: an existing image is provided as a base, the AI transforms it according to the text description.

---

## Censorship level

Each provider has an `nsfw` field in its configuration:
- `nsfw: False` — censored (OpenAI, Google)
- `nsfw: True` — less censored or Unfiltered (GROK, Kie, WaveSpeed)

This field is used in the interface to indicate the censorship level to the user.

---

## Configuration interface

`ogma_image_config.py` exposes a NiceGUI provider and model selection panel, with price-per-image indication for usage-billed providers (Kie, WaveSpeed).

The active configuration is persisted in `settings.json`.
