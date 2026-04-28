# Profile Manager

**Verified sources**: `profile_manager.py`, `profils_sauvegardes/`

> French version: [../../fr/identity/02_profile_manager.md](../../fr/identity/02_profile_manager.md)

---

## Single-entity concept

OGMA is designed around the principle of a single AI entity per instance. A "profile" represents the complete state of that entity: all its memories, compiled ego, conversations, and settings. `ProfileManager` handles saving, restoring, and deleting this state.

---

## Saving a profile

A save creates a ZIP archive in `profils_sauvegardes/`. It captures:

- The memory SQLite database (`data/memory/`)
- The compiled ego (`data/ego_compiled.json`)
- Conversations (`data/conversations/`)
- Identities and settings (`data/identities.json`, `data/settings.json`)
- Persistent context (`data/persistent_context.txt`)

Compression is enabled by default. Backup rotation limits the folder to a maximum of **10 saves**: the oldest are deleted automatically.

---

## Deleting a profile

Deletion removes memories and personal data while **preserving foundational seeds** (`SEED_*`). These seeds contain knowledge of magic phrases and the AI's fundamental identity — they must not disappear with a specific user's identity.

The list of preserved seeds is defined in the `ProfileManager` constructor.

---

## Restoration

Restoration decompresses an archive and overwrites current files. This operation is irreversible without a prior backup of the current profile. The application must be restarted after restoration to reload AI controllers.

---

## Link with `IdentityManager`

`ProfileManager` operates on raw files. `IdentityManager` manages identity metadata (names, relationships). The two systems are independent but complementary: changing profiles requires updating the active identity accordingly.
