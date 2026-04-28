# Input Image Processing (Vision)

**Verified sources**: `core_logic.py` (`_compress_vision_image()`, l.84-148), `extensions/file_processor.py`

> French version: [../../fr/images/02_vision_processing.md](../../fr/images/02_vision_processing.md)

---

## Multimodal input format

Images are transmitted to AI APIs in **base64** format embedded in messages, following the multimodal standard (type `image_url` with data URI `data:image/jpeg;base64,...`). This format is compatible with all vision providers (OpenAI, Anthropic, Google, Mistral Pixtral, etc.).

Images come from two sources:
- **User upload**: processed by `extensions/file_processor.py` (see [docs/en/files/01_file_uploads.md](../files/01_file_uploads.md))
- **Webcam capture**: processed by `extensions/perception_agent.py` (see [docs/en/perception/02_perception_agent.md](../perception/02_perception_agent.md))

---

## Compression before sending

`_compress_vision_image()` in `core_logic.py` reduces image size before API sending. This avoids excessive token costs and payload size errors.

**Process**:
1. Decodes the base64 image
2. Converts to RGB if necessary (RGBA, palette → RGB for JPEG)
3. Resizes as thumbnail to a configurable size (`target_size × target_size`)
4. Encodes as JPEG quality 85 with optimization

`target_size` is read from settings. If it is 0, compression is disabled and the image is transmitted as-is.

If PIL is not available, compression is skipped and the original image is transmitted.

---

## Metrics

The function logs the compression ratio obtained: dimensions before/after, size in KB before/after, reduction percentage.

Example: `1920x1080 → 512x288 | 1240KB → 87KB (93% reduced)`

---

## Integration in the pipeline

Encoded images are injected into the `content` array of messages in OpenAI format (`{"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}`). This format is normalized by `core_logic.py` before each API call.
