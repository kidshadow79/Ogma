# Temporal Context

**Verified sources**: `temporal_injector.py`, `extensions/temporal_guardian/__init__.py`, `extensions/temporal_guardian/temporal_sensor.py` (structure verified)

> French version: [../../fr/perception/04_temporal_context.md](../../fr/perception/04_temporal_context.md)

---

## TemporalInjector (disabled)

`temporal_injector.py` is a module that was responsible for injecting a compact timestamp into user messages. Its original design aimed to give the main AI temporal awareness (day, time) consuming only ~4 tokens per message.

This module is **disabled** in the current version. The `temporal_instruction` constant is an empty string and `inject_temporal_awareness()` returns the message unchanged. The note in the code indicates this feature has been delegated to the **Temporal Guardian** extension.

---

## Temporal Guardian extension

The `extensions/temporal_guardian/` extension replaces and extends TemporalInjector. Its architecture separates:

**TemporalSensor**: pure measurement of delays between messages (time elapsed since last exchange). Makes no interpretation.

**ArchivisteEnricher**: receives measurements from the sensor and enriches the Archivist's prompt with temporal data for behavioral analysis. The Archivist then interprets these delays (fatigue, reflection, interruption, availability).

**TemporalGuardian**: orchestrator that connects sensor and enricher.

---

## Philosophy

The sensor/interpreter separation is deliberate: "the sensor measures, the archivist interprets". The Python module never makes judgments about what a delay means — that is the role of the Archivist AI, which has full conversational context.

---

## Usage

```python
from extensions.temporal_guardian import create_temporal_guardian

guardian = create_temporal_guardian(debug=True)
enriched_prompt = guardian.process_user_message(user_message, archiviste_prompt)
```
