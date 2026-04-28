# Biographies

**Verified sources**: `extensions/biographie_profil/__init__.py`, `extensions/biographie_profil/biography_manager.py`, `data/biographies/`

> French version: [../../fr/identity/04_biographies.md](../../fr/identity/04_biographies.md)

---

## Concept

The Biography Profile extension lets the main AI build and maintain a biographical journal about the user, automatically fed by conversations. It is not a manually administered user profile: it is an accumulated and structured observation of what the user has shared.

---

## Two volumes

### Volume 1 — Filtered memories

A FAISS filter selects memories from the memory database that concern an identified user. These memories serve as raw material for the journal.

### Volume 2 — Narrative journal

The Archivist writes a structured biographical journal in 10 sections:

- General portrait
- Psyche and emotional life
- Intellectual life
- Projects and creations
- Daily life and habits
- Relationships and social circle
- Personal history
- Values and convictions
- Physical presence
- Tastes and preferences

**Strict rule**: the Archivist only writes what is directly supported by an observed fact from memories. Sections with no corresponding fact contain the note "No observed data." Inference and extrapolation are prohibited.

---

## Triggering

The biography is updated via a magic phrase detected in messages. The extension uses `BiographyMagicPhrases` to monitor these triggers.

If the Archivist is available, it intelligently selects the most relevant memories to enrich the journal. Without the Archivist, selection is done by direct FAISS filtering.

---

## Storage

Biographies are saved in `data/biographies/` as structured JSON files. A backup system with rotation is built in, following the same pattern as profiles.
