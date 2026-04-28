# Uploads and File Management

**Verified sources**: `files/file_management.py`, `extensions/file_processor.py`

> French version: [../../fr/files/01_file_uploads.md](../../fr/files/01_file_uploads.md)

---

## Upload flow

File upload follows a 4-step pipeline:

1. **NiceGUI event**: the user selects a file via the upload component. The `upload_event` is emitted with the file content and name.

2. **Temporary save**: `process_uploaded_file()` saves the file in `data/uploads/` with a `temp_{uuid}_` prefix to avoid collisions.

3. **Content extraction**: `extensions/file_processor.process_file()` extracts text (PDF, DOCX) or encodes the image in base64.

4. **Activation**: extracted data is stored in `active_file_data_ref` — a shared mutable dict. The file is then "active" for the next AI request.

---

## Supported formats

| Format | Extraction method |
|---|---|
| PDF | `pypdf` (fallback `PyPDF2`) — text page by page |
| DOCX | `python-docx` — text from all paragraphs |
| Images | OpenCV → JPEG base64 encoding |

---

## UI utility functions

`files/file_management.py` also contains display helpers:
- `update_header_display()` — refreshes the header with the active file state
- Icons by file type and long name truncation (via `utils/formatting_utils.py`)

---

## Cleanup

Temporary files in `data/uploads/` are not automatically deleted after processing. Manual cleanup or via the interface may be needed to free space.
