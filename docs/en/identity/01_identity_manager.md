# Identity Manager

**Verified sources**: `identity_manager.py`, `data/identities.json`, `data/identities.default.json`

> French version: [../../fr/identity/01_identity_manager.md](../../fr/identity/01_identity_manager.md)

---

## Role

OGMA can operate with different user-AI profiles. `IdentityManager` abstracts names and descriptions to avoid any hard-coding. Instead of fixed references to specific names, all components go through this manager.

---

## Data structure

`data/identities.json` contains a dictionary of profiles and the active profile:

```json
{
  "current_profile": "profile_1",
  "profiles": {
    "profile_1": {
      "user_name": "User",
      "ai_name": "Assistant",
      "ai_description": "...",
      "relationship_type": "collaborative",
      "relationship_context": "..."
    }
  },
  "defaults": { ... }
}
```

The `relationship_context` field supports the `{user_name}` variable, which is substituted at use time.

---

## Bootstrap

If `data/identities.json` doesn't exist at startup, the system looks for `data/identities.default.json` and copies it. If no default file is available either, a minimal configuration is generated and saved. This pattern is identical to `SettingsManager`'s with `settings.example.json`.

---

## Main API

| Function | Role |
|---|---|
| `get_current_user_name()` | Returns the user name of the active profile |
| `get_current_ai_name()` | Returns the AI name of the active profile |
| `get_relationship_context()` | Returns the relational description with `{user_name}` resolved |
| `set_current_profile(id)` | Changes the active profile |
| `create_profile(...)` | Creates a new profile |

---

## Multi-profiles

Multiple profiles can coexist (family, work, test). Switching between profiles is instantaneous. The active profile is persisted in `identities.json` and restored on restart.
