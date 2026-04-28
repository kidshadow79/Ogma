# Formatting and Parsing Utilities

**Verified sources**: `utils/formatting_utils.py`, `utils/message_parsers.py`, `utils/json_cleaner.py`, `utils/magic_phrase_normalizer.py`, `utils/backend_utils.py`

> French version: [../../fr/utils/01_utils.md](../../fr/utils/01_utils.md)

---

## Overview

The `utils/` folder contains utility functions extracted from `ogma_ng.py` during refactoring. Each module focuses on a single responsibility.

---

## `formatting_utils.py` — Human-readable formatting

`format_size(size_bytes)` converts a size in bytes to a human-readable format ("1.5 MB", "320 KB"). Used for displaying file sizes and memory in the interface.

---

## `message_parsers.py` — AI format parsers

Two parsers for special formats in AI responses:

**`parse_thinking_format(content)`**: some AIs return complex JSON structures with a `thinking` section (internal reflection) and a `text` section (visible response). This parser extracts both and returns a tuple `(thinking_content, main_text)`.

**`parse_introspection_format(content)`**: parses `<introspection>...</introspection>` tags that the main AI uses for introspection dialogues. Content between tags is extracted and displayed in the dedicated box.

---

## `json_cleaner.py` — JSON response cleanup

AI responses containing JSON often include markdown tags (` ```json ``` `), `//` comments, or control characters. `clean_json_response()` cleans the raw response before parsing.

---

## `magic_phrase_normalizer.py` — Multilingual normalization

Translates English magic phrases into canonical French equivalents before any analysis. This allows the user to write in English ("remember that...") while the French detectors continue to work.

The transformation is non-destructive: the magic phrase payload (the content after the command) is preserved as-is.

---

## `backend_utils.py` — Backend normalization

`map_backend_for_controller(backend)` normalizes backend names to UPPERCASE for compatibility with `AIController` internal dictionaries. This normalization is critical — "GGUF" and "gguf" must be treated identically.
