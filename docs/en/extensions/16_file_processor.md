# File Processor — Uploaded File Processing

**Verified sources**: `extensions/file_processor.py`, `files/file_management.py`

> French version: [../../fr/extensions/16_file_processor.md](../../fr/extensions/16_file_processor.md)

---

## Role

The File Processor transforms an uploaded file into data usable by the main AI. It handles text extraction (documents) and image processing for injection into the multimodal context.

---

## Supported file types

| Type | Library | Result |
|---|---|---|
| PDF | `pypdf` (or `PyPDF2` fallback) | Text extracted page by page |
| DOCX | `python-docx` | Extracted text |
| Images (JPG, PNG...) | OpenCV + base64 | Base64 encoding for multimodal |

---

## Upload flow

`files/file_management.py` orchestrates the process:

1. The NiceGUI `upload_event` triggers `process_uploaded_file()`
2. The file is temporarily saved in `data/uploads/`
3. `extensions/file_processor.process_file()` extracts the content
4. The result is stored in `active_file_data_ref` (shared mutable dict)
5. The main AI receives the content on the next message

---

## Visual enrichment (images)

For images, the File Processor can engage two optional modules if available:

- **DepthManager**: depth analysis of the scene
- **ContourAnalyzer**: shape and contour detection

Each is a lazily initialized singleton. If one is absent, processing continues without it.

---

## Temporary storage

Uploaded files transit through `data/uploads/`. They are prefixed `temp_{uuid}_` to avoid collisions between concurrent sessions.
