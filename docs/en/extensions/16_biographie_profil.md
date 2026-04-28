# Biography — Evolving Portrait of the User

**Verified source**: `extensions/biographie_profil/` (see also [docs/en/identity/04_biographies.md](../identity/04_biographies.md))

> French version: [../../fr/extensions/16_biographie_profil.md](../../fr/extensions/16_biographie_profil.md)

---

## Concept

The Biography is a structured and evolving portrait of the user, built automatically from FAISS memories. It answers the question: "If the AI had to describe me to someone who doesn't know me, what would it say?"

---

## Two volumes

**Volume 1 — Factual portrait**: synthesis of memories marked as important in FAISS (high importance score). The Archivist filters and structures these memories into thematic sections (personality, interests, habits, relationships, projects).

**Volume 2 — Narrative journal**: a more personal account, organized into 10 predefined sections. The Archivist maintains this journal over the course of conversations, never inferring what has not been observed. If a section is empty, it stays empty — "No observed data".

---

## Anti-inference golden rule

The biography contains **no deductions**. If the user has not explicitly said they like classical music, this information does not appear. This rule is enforced at the level of the biographer Archivist's prompts.

---

## Usage by the main AI

When the Capability Advisor suggests the "Biography" capability (👤), the main AI can consult the portrait to personalize its response. The biography is also available as background context for deep conversations about the user.

---

*For complete technical documentation on the biography system, see [identity/04_biographies.md](../identity/04_biographies.md).*
