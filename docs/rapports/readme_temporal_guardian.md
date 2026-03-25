# Extension Temporal Guardian — Documentation Exhaustive

**Dossier** : `extensions/temporal_guardian/`
**Rôle** : Mesurer les délais entre messages, enrichir le prompt de l'Archiviste avec un contexte temporel précis, et détecter les rythmes conversationnels anormaux (longue inactivité, burst de messages).

---

## Concept

Le Temporal Guardian fonctionne selon un principe de **séparation des responsabilités** strict :

- **`TemporalSensor`** : mesure brute, sans interprétation (timestamps, délais, statistiques)
- **`ArchivisteEnricher`** : interprète les mesures et enrichit le prompt Archiviste
- **`TemporalGuardian`** : orchestrateur qui assemble le tout

---

## Architecture — Fichiers

| Fichier | Classe exportée | Rôle |
|---------|-----------------|------|
| `config.py` | `TemporalGuardianConfig` | Configuration paramétrable |
| `temporal_sensor.py` | `TemporalSensor`, `TemporalMeasurement` | Mesures temporelles pures |
| `archiviste_enricher.py` | `ArchivisteEnricher` | Enrichissement prompt Archiviste |
| `temporal_guardian.py` | `TemporalGuardian` | Orchestrateur + factory |
| `test_extension.py` | — | Suite de tests autonomes |
| `__init__.py` | Ré-exports | Point d'entrée |

---

## `config.py` — Classe `TemporalGuardianConfig`

### Paramètres (avec valeurs par défaut)

| Attribut | Type | Défaut | Description |
|----------|------|--------|-------------|
| `enabled` | `bool` | `True` | Active/désactive l'extension |
| `debug_mode` | `bool` | `False` | Logs verbeux |
| `collect_session_stats` | `bool` | `True` | Collecte statistiques session |
| `max_history_messages` | `int` | `100` | Limite historique messages |
| `enrich_archiviste_prompt` | `bool` | `True` | Injection contexte dans prompt Archiviste |
| `temporal_context_format` | `str` | `"detailed"` | `"simple"` ou `"detailed"` |
| `track_average_delays` | `bool` | `True` | Calcul délai moyen de session |
| `session_timeout_minutes` | `int` | `30` | Minutes d'inactivité = nouvelle session |
| `enrichment_threshold_seconds` | `int` | `30` | Seuil délai (secondes) pour déclencher enrichissement |

### Méthodes

| Méthode | Description |
|---------|-------------|
| `get_prompt_enrichment_template()` | Retourne le template texte avec placeholders `{delay_seconds}`, `{current_time}`, `{message_count}`, `{session_minutes}`, `{average_delay}`. Format "simple" ou "detailed" selon `temporal_context_format`. |
| `to_dict()` | Sérialise tous les attributs |
| `from_dict(config_dict)` (classmethod) | Crée instance depuis dict (setattr pour chaque clé reconnue) |

---

## `temporal_sensor.py` — Dataclass `TemporalMeasurement` et Classe `TemporalSensor`

### Dataclass `TemporalMeasurement`

| Champ | Type | Description |
|-------|------|-------------|
| `message_timestamp` | `datetime` | Horodatage exact du message |
| `delay_since_last` | `Optional[float]` | Secondes depuis dernier message (`None` pour le 1er) |
| `current_time_str` | `str` | Heure formatée `"HH:MM"` |
| `session_duration` | `float` | Secondes depuis début de session |
| `message_count` | `int` | Numéro du message dans la session courante |
| `average_delay` | `Optional[float]` | Délai moyen session (disponible à partir de 3 mesures) |

### Classe `TemporalSensor`

**État interne** : `session_start`, `last_message_time`, `message_delays` (list max 50), `message_count`.

| Méthode | Paramètres | Retour | Description |
|---------|-----------|--------|-------------|
| `__init__(debug=False)` | — | — | Démarre session (`session_start = now`), initialise compteurs |
| `register_message(message_content)` | `str` | `TemporalMeasurement` | Calcule délai vs dernier message, ajoute à l'historique (max 50), calcule moyenne si ≥3 mesures |
| `get_session_stats()` | — | `dict` | `{session_start, session_duration_minutes, total_messages, average_delay, min_delay, max_delay, delays_count}` |
| `reset_session()` | — | — | Remet à zéro tous les compteurs et timestamps |
| `is_new_session_needed(inactivity_minutes)` | `float` | `bool` | `True` si inactivité ≥ seuil depuis `last_message_time` |

---

## `archiviste_enricher.py` — Classe `ArchivisteEnricher`

**`__init__(config, debug=False)`** — stocke config.

| Méthode | Description |
|---------|-------------|
| `enrich_archiviste_prompt(base_prompt, measurement, user_message)` | Route vers format simple ou detailed selon `config.temporal_context_format`, puis injecte via `_inject_temporal_context()` |
| `_format_simple_context(measurement, user_message)` | Format court : `"Délai: 45s (msg #3)"` |
| `_format_detailed_context(measurement, user_message)` | Format complet avec 🕒 heure, ⏱️ délai, 📊 session + messages, 📈 rythme moyen |
| `_inject_temporal_context(base_prompt, temporal_context)` | Concatène `base_prompt + "\n\n" + temporal_context` |
| `should_enrich_this_message(measurement)` | Règle : toujours le 1er message, enrichir si délai > `enrichment_threshold_seconds` (config, défaut 30s), ou tous les 5 messages (`message_count % 5 == 0`) |
| `create_temporal_summary(measurements)` | Analyse liste de mesures — catégorise rapides/normales/lentes, calcule stats, retourne résumé multi-lignes |

---

## `temporal_guardian.py` — Classe `TemporalGuardian`

Orchestrateur composé de `TemporalSensor + ArchivisteEnricher + TemporalGuardianConfig`.

### Attributs

```python
self.config: TemporalGuardianConfig
self.sensor: TemporalSensor
self.enricher: ArchivisteEnricher
self.is_active: bool              # = config.enabled
self.last_measurement: Optional[TemporalMeasurement]
```

### Méthodes publiques

| Méthode | Paramètres | Retour | Description |
|---------|-----------|--------|-------------|
| `process_user_message(user_message, archiviste_prompt)` | `str, str` | `dict` | Pipeline : `sensor.register_message()` → `enricher.enrich_archiviste_prompt()` → retourne `{enriched_archiviste_prompt, temporal_data, temporal_summary}` |
| `analyze_with_archiviste(temporal_data, archiviste_controller)` | `dict, AIController` | `Optional[str]` (async) | Charge instructions temporelles, construit prompt d'analyse, `archiviste_controller.call_chat_api(max_tokens=150)` — retourne instruction directe ou `None` si résultat `"NORMAL"` |
| `_load_archiviste_instructions()` | — | `str` | **Priorité 1** : `settings.json["prompts"]["temporal_guardian"]` — **Fallback 2** : fichier `INSTRUCTIONS_ARCHIVISTE_TEMPOREL.md` — **Fallback 3** : texte hardcodé |
| `reload_instructions()` | — | `bool` | Recharge instructions à chaud sans redémarrage |
| `_get_temporal_summary()` | — | `str` | `"Session active: Xmin \| Y messages \| Rythme moyen: Zs"` |
| `reset_session()` | — | — | `sensor.reset_session()` + `last_measurement = None` |
| `should_reset_session()` | — | `bool` | Délègue à `sensor.is_new_session_needed(config.session_timeout_minutes)` |
| `get_session_stats()` | — | `dict` | Stats sensor + `extension_active` + config dict + `last_measurement` |
| `enable()` / `disable()` | — | — | Bascule `is_active` |
| `update_config(new_config)` | `TemporalGuardianConfig` | — | Remplace config + recrée l'enricher |

### Factory function

```python
create_temporal_guardian(config_dict: dict = None, debug: bool = False) -> TemporalGuardian
```

---

## `test_extension.py` — Suite de tests

Exécutable directement : `python extensions/temporal_guardian/test_extension.py`

| Suite | Ce qui est validé |
|-------|-------------------|
| `test_basic_functionality()` | 1er message (`delay_since_last is None`), message rapide (<5s), message avec délai (>2s) |
| `test_enrichment_formats()` | Format `"simple"` vs `"detailed"` présents dans le prompt enrichi |
| `test_session_management()` | Compteur messages, stats session, reset (message_count retombe à 1) |
| `test_alert_system()` | Délai normal vs délai long (6s) → vérifie `temporal_summary` change avec le rythme |
| `test_configuration()` | Extension désactivée → `temporal_data is None` ; `disable()`/`enable()` dynamiques |
| `run_all_tests()` | Lance toutes les suites, affiche résultat global |

---

## Données retournées par `process_user_message()`

```python
{
    "enriched_archiviste_prompt": str,      # Prompt Archiviste avec contexte temporel injecté
    "temporal_data": Optional[TemporalMeasurement],  # None si extension désactivée
    # Champs accessibles sur l'objet TemporalMeasurement :
    #   .delay_since_last    float|None   Délai en secondes (None pour le 1er message)
    #   .message_count       int          Numéro du message dans la session
    #   .session_duration    float        Durée session en secondes
    #   .average_delay       float|None   Délai moyen session (disponible à partir de 3 mesures)
    #   .current_time_str    str          Heure formatée "HH:MM"
    #   .message_timestamp   datetime     Horodatage exact
    "temporal_summary": str               # Résumé lisible (ex: "Session active: 5min | 3 messages | Rythme moyen: 45s")
}
```

---

## Intégration dans OGMA

Appelé depuis `ogma_ng.py` dans le handler pré-appel Archiviste :

```python
if temporal_guardian and temporal_guardian.is_active:
    result = temporal_guardian.process_user_message(
        user_message=user_input,
        archiviste_prompt=archiviste_system_prompt
    )
    archiviste_system_prompt = result["enriched_archiviste_prompt"]
```

Le Guardian peut aussi demander une analyse approfondie à l'Archiviste (`analyze_with_archiviste()`) pour détecter des patterns anormaux (pause longue après sujet difficile, burst de 10 messages rapides, etc.) et générer une directive contextuelle injectée dans l'IA principale.

---

## Source des instructions Archiviste

Ordre de priorité pour charger les instructions d'analyse :

1. `settings.json` → clé `prompts.temporal_guardian` (configurable sans code)
2. Fichier externe `INSTRUCTIONS_ARCHIVISTE_TEMPOREL.md` (présent dans la racine ou `data/`)
3. Texte par défaut hardcodé dans `_load_archiviste_instructions()`

`reload_instructions()` permet de rechanger les instructions après modification du fichier/settings sans F5.
