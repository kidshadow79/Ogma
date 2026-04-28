# Configuration Manager — `SettingsManager`

**Verified sources**: `core_logic.py` (class `SettingsManager`), `data/settings.example.json`

> French version: [../../fr/config/01_settings_manager.md](../../fr/config/01_settings_manager.md)

---

## Role

`SettingsManager` is the single access point for OGMA's configuration. It loads `data/settings.json` at startup and exposes a `settings` dictionary that all components can read. Saves must go through it — never by writing directly to the file.

---

## Loading

At load time, the manager starts from default values (`_default_settings`) and merges them with the JSON file contents. This merge is recursive: keys present in the file overwrite defaults, but keys absent from the file keep their default value. This means a partial `settings.json` (for example after an update that adds new options) stays valid without manual intervention.

If the file is absent, defaults are used and the `_load_failed` flag is set to `True`. If the file exists but contains invalid JSON, saving is **blocked** to protect existing data — better to write nothing than to overwrite with corrupt data.

---

## Save protection

Two guards protect `save_settings()`:

1. **`_load_failed` flag**: if loading failed, any save attempt is refused with an explicit message.
2. **Empty default value detection**: if the settings look like a blank profile (provider = "None", no vault, short instructions), the save is also refused. This avoids overwriting a real configuration with an uninitialized state.

---

## Automatic backups

Before each successful save, the current file is copied to `data/backups/` with a timestamp. Only the four most recent backups are kept; older ones are deleted automatically.

---

## Structure of `settings.json`

Main sections of the configuration file:

| Section | Contents |
|---|---|
| `chat_api` | Main AI controller configuration (provider, key, model, backend) |
| `reasoning_api` | Archivist configuration |
| `embedding_api` | Embedding configuration |
| `image_generation` | Image generation (enabled, dimensions, provider) |
| `audio` | Audio and STT/TTS preferences |
| `voice` | Voice recognition activation and configuration |
| `dream_engine` | Dream Engine settings (enabled, inactivity timeout) |
| `other_backends` | Ollama-specific settings (low_vram, timeout) |
| `prompts` | Main system prompts (instructions, memorization, injection) |
| `perception_agent` | Webcam and perception model configuration |
| `api_keys_vault` | API key vault (encrypted or stored depending on config) |

The `data/settings.example.json` file serves as a documented template for a new deployment.
