# Temporal Guardian — La conscience du temps

**Source vérifiée** : `extensions/temporal_guardian/__init__.py`

---

*Cette page documente l'extension en tant que module. Pour la documentation du contexte temporel dans le pipeline, voir [perception/04_temporal_context.md](../perception/04_temporal_context.md).*

---

## Concept

Le Temporal Guardian donne à l'Archiviste une conscience des **délais entre messages**. Combien de temps s'est écoulé depuis la dernière conversation ? Depuis le dernier message de cette session ? Ces informations enrichissent l'analyse comportementale de l'Archiviste.

---

## Séparation mesure / interprétation

| Composant | Rôle |
|---|---|
| `TemporalSensor` | Mesure pure des délais (sans jugement) |
| `ArchivisteEnricher` | Enrichit le prompt Archiviste avec les mesures |
| `TemporalGuardian` | Orchestrateur |

Le capteur ne dit jamais "l'utilisateur semble fatigué" — il dit "37 minutes se sont écoulées depuis le dernier message". C'est l'Archiviste qui interprète.

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
