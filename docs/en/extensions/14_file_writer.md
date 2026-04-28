# File Writer — Automatic File Saving

**Verified source**: `extensions/file_writer/__init__.py`

> French version: [../../fr/extensions/14_file_writer.md](../../fr/extensions/14_file_writer.md)

---

## Concept

The File Writer detects when the main AI generates content intended to be saved as a Markdown file, and saves it automatically in `data/uploads/`.

---

## Mechanism

The extension analyzes the main AI's responses looking for Markdown blocks containing a document title. If a block is detected and the context suggests a file creation request (summary, report, article, etc.), the content is extracted and saved with the document title as the filename.

A discreet notification informs the user of the file created.

---

## Trigger

Two conditions must be met:
1. The AI response contains a structured Markdown block with a title
2. The user request suggests a file creation ("write a report", "create a document", etc.)

The extension does not save all code or Markdown blocks — only those clearly intended to be files.
