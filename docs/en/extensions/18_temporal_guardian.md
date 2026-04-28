# Temporal Guardian — The Sense of Time

**Verified source**: `extensions/temporal_guardian/__init__.py`

> French version: [../../fr/extensions/18_temporal_guardian.md](../../fr/extensions/18_temporal_guardian.md)

---

*This page documents the extension as a module. For temporal context documentation in the pipeline, see [perception/04_temporal_context.md](../perception/04_temporal_context.md).*

---

## Concept

The Temporal Guardian gives the Archivist an awareness of **delays between messages**. How much time has passed since the last conversation? Since the last message in this session? This information enriches the Archivist's behavioral analysis.

---

## Measurement / interpretation separation

| Component | Role |
|---|---|
| `TemporalSensor` | Pure measurement of delays (no judgment) |
| `ArchivisteEnricher` | Enriches the Archivist prompt with measurements |
| `TemporalGuardian` | Orchestrator |

The sensor never says "the user seems tired" — it says "37 minutes have passed since the last message". It is the Archivist who interprets.

---

## Usage

```python
from extensions.temporal_guardian import create_temporal_guardian

guardian = create_temporal_guardian()
enriched_archiviste_prompt = guardian.process_user_message(
    user_message, 
    archiviste_base_prompt
)
```
