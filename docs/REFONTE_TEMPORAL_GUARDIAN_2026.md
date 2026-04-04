# Refonte Temporal Guardian — Janvier 2026

## Motivation

L'ancien système Temporal Guardian faisait appel à l'Archiviste (API) à chaque message pour analyser les patterns temporels. Résultat concret : environ 95 % des appels retournaient "NORMAL" (aucune directive), avec ~350 tokens gaspillés et une latence inutile.

---

## Ancien système (supprimé)

- `TemporalGuardian.analyze_with_archiviste()` → appel API Archiviste par message
- `UnifiedMetaAnalyzer` incluait une section `"temporal"` dans son prompt JSON et retournait `temporal_instruction` + `temporal_pattern`
- `ParallelExecutor.execute()` passait `temporal_guardian` et `temporal_data` à chaque analyse
- `ogma_ng.py` construisait un bloc "PRIORITÉ ABSOLUE" entouré de cadres ASCII si `temporal_final_alert` non nul
- Inter-session delay calculé manuellement dans `ogma_ng.py` Zone H

---

## Nouveau système

### `extensions/temporal_guardian/temporal_log_builder.py` (NOUVEAU)

- Python pur, zéro appel API
- `register_message_time()` : appelé en début de `_send_chat_message()`, initialise `_session_start` et `_previous_message_time`
- `build_temporal_log(conv_index, is_new_session)` : génère le bloc JSON formaté

Format de sortie :
```
--- CONTEXTE TEMPOREL ---
{
  "maintenant": "lundi 31 mars 2026 à 22h15",
  "debut_session": "...",
  "ecarts": {
    "depuis_debut_session": "45 minutes",
    "depuis_derniere_interaction": "5 minutes 23 secondes",
    "depuis_derniere_session": null
  },
  "type_session": "intra_session"
}
--- FIN CONTEXTE TEMPOREL ---
```

### Flux d'injection (`ogma_ng.py`)

1. **Début de `_send_chat_message()`** : `register_message_time()` enregistre l'heure
2. **Zone G** (injection instructions) : `build_temporal_log()` génère le JSON, fusionné en tête des instructions de base si `temporal_guardian` est défini dans `settings.json → prompts`
3. L'IA principale interprète elle-même le log JSON sans passer par l'Archiviste

### Instruction dans `settings.json → prompts.temporal_guardian`

Redirigée vers l'IA principale (non plus l'Archiviste). Définit 4 patterns de réaction (absence longue, heure tardive, rythme lent, rythme rapide) + règle "Ne cite jamais le log".

---

## Fichiers modifiés

| Fichier | Changement |
|---|---|
| `extensions/temporal_guardian/temporal_log_builder.py` | CRÉÉ |
| `extensions/temporal_guardian/temporal_guardian.py` | Réduit à stubs DEPRECATED (compatibilité imports) |
| `data/settings.json` | `prompts.temporal_guardian` réécrit pour IA principale |
| `modules/preanalysis_optimizer/unified_meta_analyzer.py` | Suppression section temporal (dataclass, prompt, parser, `_format_temporal_section`) |
| `modules/preanalysis_optimizer/parallel_executor.py` | Suppression `_run_temporal_guardian()`, params temporal de `execute()` et `_run_unified_meta_analyzer()` |
| `modules/preanalysis_optimizer/__init__.py` | Suppression params temporal de `get_optimized_context()` |
| `modules/preanalysis_optimizer/integration.py` | Suppression params temporal de `get_optimized_context_for_message()` |
| `ogma_ng.py` | 8 zones nettoyées — voir détail ci-dessous |

### Zones ogma_ng.py nettoyées

- **Zone A** : Suppression `temporal_final_alert = None` + `temporal_context_enriched = None`, ajout `register_message_time()`
- **Zones B/C** : Suppression affichage `temporal_final_alert` dans blocs debug show_injection
- **Zone D** : Suppression bloc séquentiel TEMPORAL GUARDIAN complet (~60 lignes)
- **Zone E** : Suppression `temporal_guardian_instance` + prep `temporal_data_for_parallel` dans PREANALYSIS, retrait params du call `get_optimized_context_for_message()`
- **Zone F** : Suppression `parallel_temporal_instruction` (init + lecture + affectation)
- **Zone G** : Remplacement bloc "PRIORITÉ ABSOLUE ASCII" par injection `temporal_log_builder`
- **Zone H** : Suppression second bloc temporal guardian résiduel + `inter_session_line` + simplification CONTEXTE MÉMORIEL
- **Zone ext.** : Suppression params temporal dans appel external API (ligne ~8756)

---

## Économies

| Métrique | Avant | Après |
|---|---|---|
| Appels API par message | +1 (Archiviste temporal) | 0 |
| Tokens par message (temporal) | ~350 | ~100 (log JSON) |
| Latence | +appel API Archiviste | 0 ms |

---

## `temporal_guardian.py` — statut DEPRECATED

Le fichier est conservé comme stub pour ne pas casser les imports existants. La classe `TemporalGuardian` retourne des valeurs inertes. Aucun code ne l'appelle plus (vérifié par audit).
