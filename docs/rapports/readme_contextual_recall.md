# Extension Contextual Recall — Documentation Exhaustive

**Dossier** : `extensions/contextual_recall/`
**Version** : 2.0.0
**Rôle** : Détecter les références temporelles dans les messages utilisateur ("il y a 3 jours", "la semaine dernière", "tu te souviens de..."), retrouver les résumés de conversations correspondants, et injecter ce contexte historique dans le prompt de l'IA.

---

## Concept

Lorsque l'utilisateur fait une référence temporelle implicite ou explicite, l'extension :
1. Détecte et parse l'expression temporelle en plage de dates absolues
2. Filtre le cache des résumés de conversations pour cette plage
3. Formate les résumés en bloc de contexte injectable
4. Retourne ce contexte à `ogma_ng.py` pour injection dans le system prompt

---

## Architecture — Fichiers

| Fichier | Classe | Rôle |
|---------|--------|------|
| `__init__.py` | — | API publique singleton |
| `temporal_parser.py` | `TemporalParser`, `TemporalMatch` | Détection + conversion expressions temporelles |
| `summary_loader.py` | `SummaryLoader` | Accès cache résumés conversations |
| `context_builder.py` | `ContextBuilder` | Formatage blocs de contexte |
| `recall_agent.py` | `RecallAgent` | Orchestrateur pipeline |

---

## API Publique (`__init__.py`)

**Singleton global** : `_recall_agent : Optional[RecallAgent] = None`

| Fonction | Paramètres | Description |
|----------|-----------|-------------|
| `initialize_recall(conversations_path, debug, **kwargs)` | `str, bool` | Crée `TemporalParser`, `SummaryLoader`, `ContextBuilder`, `RecallAgent`. `**kwargs` ignorés (rétrocompat v2.1). Retourne `RecallAgent` ou `None`. |
| `is_available()` | — | `True` si singleton non-None |
| `get_recall_agent()` | — | Retourne le singleton |
| `process_message(user_message)` | `str` | Délègue à `_recall_agent.process_message()`, retourne contexte formaté ou `None` |
| `cleanup()` | — | Réinitialise le singleton |

**Fichiers de données lus** : `data/conversations/` (via `SummaryLoader`)

---

## `temporal_parser.py` — Dataclass `TemporalMatch` et Classe `TemporalParser`

### Dataclass `TemporalMatch`

| Champ | Type | Description |
|-------|------|-------------|
| `pattern_type` | `str` | Catégorie du pattern détecté |
| `date_start` | `datetime` | Début de la plage temporal |
| `date_end` | `datetime` | Fin de la plage |
| `confidence` | `float` | Score 0.0–1.0 |
| `original_text` | `str` | Texte orignal qui a matché |
| `is_period` | `bool` | `True` si plage, `False` si date unique |

### Classe `TemporalParser`

**`__init__(debug=False)`** — compile tous les patterns regex.

#### Catégories de patterns (avec confiance)

| Catégorie | Exemples | Confiance |
|-----------|---------|-----------|
| `ia_magic_phrase` | `"il faut que je consulte notre conversation de..."`, `"je dois consulter mes conversations avec [prénom]"` | 0.95 (0.7 fallback) |
| `relative_days` | `"il y a 3 jours"`, `"3 jours avant"` | 0.90 |
| `relative_weeks` | `"il y a 2 semaines"` | 0.85 |
| `relative_months` | `"il y a 1 mois"`, `"le mois dernier"` | 0.75 |
| `absolute_simple` | `"hier"`, `"avant-hier"`, `"aujourd'hui"` | 0.95 |
| `named_periods` | `"la semaine dernière"`, `"cette semaine"`, `"le week-end dernier"` | 0.85–0.90 |
| `memory_triggers` | `"tu te souviens"`, `"qu'est-ce qu'on a dit"`, `"notre conversation sur"` | 0.60 |

**Méthodes publiques :**

| Méthode | Paramètres | Retour | Description |
|---------|-----------|--------|-------------|
| `parse(text)` | `str` | `List[TemporalMatch]` | Scanne toutes catégories, déduplique, trie par confiance décroissante |
| `has_temporal_reference(text)` | `str` | `bool` | `True` si au moins 1 match |
| `get_best_match(text)` | `str` | `Optional[TemporalMatch]` | Premier item après tri par confiance |

**Méthodes privées :**

- `_convert_to_temporal(category, match, now)` — calcule plage selon catégorie, retourne `TemporalMatch`
- `_deduplicate_matches(matches)` — élimine doublons par `(date_start.date, date_end.date, pattern_type)`

**Logique clé — phrase magique IA** :  
`"il faut que je consulte notre conversation de hier"` → sous-parse la sous-expression `"hier"` → confiance 0.95.  
Si sous-parse échoue → fallback 7 derniers jours, confiance 0.7.

---

## `summary_loader.py` — Classe `SummaryLoader`

**Rôle** : Accès au cache mémoire des résumés extraits des fichiers JSON de conversations.

**`__init__(conversations_dir="data/conversations", debug=False, **kwargs)`**

**Structure d'un item du cache :**

```python
{
    'name': str,                # Clé unique "{conv_id}_range_{idx}"
    'conversation_id': str,
    'conversation_file': str,
    'modified': datetime,       # Date de modification du fichier conversation
    'start': int,               # Index message début de la plage résumée
    'end': int,                 # Index message fin
    'content': str,             # Texte du résumé
    'cache_key': str,
    'is_fusion': False,         # Toujours False (compat ancien système)
    'size': int                 # len(content)
}
```

**Méthodes publiques :**

| Méthode | Paramètres | Description |
|---------|-----------|-------------|
| `list_cached_summaries()` | — | Tous résumés triés par date décroissante |
| `filter_by_date_range(start_date, end_date, include_fusion=True)` | `datetime, datetime` | Filtre par `modified ≥ start` et `≤ end` |
| `load_summary_content(summary_name)` | `str` | Retourne `content` depuis cache ou `None` |
| `load_multiple(summary_list)` | `List[Dict]` | Batch load → `List[Tuple[Dict, str]]` (metadata, content) |
| `get_recent_summaries(max_count=10, include_fusion=True)` | `int` | N résumés les plus récents |
| `get_fusion_summaries()` | — | Retourne `[]` (compat ancien système) |
| `search_by_keywords(keywords, max_results=5)` | `List[str], int` | Score = nb keywords présents — retourne `List[Tuple[Dict, str, float]]` |
| `get_statistics()` | — | `{total_summaries, conversations_with_summaries, simple_summaries, fusion_summaries (0), total_size_bytes, oldest_date, newest_date, last_scan}` |
| `refresh_cache()` | — | Vide cache + re-scanne `conversations_dir` |

**Dépendance externe** : `conversation_summarizer.get_all_summaries_from_conversations()` (racine OGMA)

---

## `context_builder.py` — Classe `ContextBuilder`

**Rôle** : Formater les résumés chargés en blocs de contexte injectables dans le system prompt.

**`__init__(max_tokens=1000, max_summaries=5, debug=False)`**
- `chars_per_token = 4` — approximation 1 token ≈ 4 caractères

### Format long — `build_context()`

```
📚 RAPPEL MÉMOIRE CONVERSATIONNELLE (période: JJ/MM – JJ/MM)

[Résumé 1 - DD/MM/YYYY HH:MM (XX.X KB)]
...contenu...

[Résumé 2 - DD/MM/YYYY HH:MM (XX.X KB)]
...contenu...

💡 Utilise ces informations pour rappeler à l'utilisateur ce dont vous avez parlé.
```

### Format compact — `build_compact_context()`

```
📚 MÉMOIRE (période): 1. [dd/mm] contenu tronqué... 2. [dd/mm] ...
```
MAX 200 chars par résumé.

**Méthodes publiques :**

| Méthode | Paramètres | Description |
|---------|-----------|-------------|
| `build_context(summaries, date_start, date_end, user_query)` | `List[Tuple[Dict,str]], datetime, datetime` | Format long avec header et footer. Respecte budget tokens. |
| `build_compact_context(summaries, date_start, date_end)` | — | Format ultra-compact |
| `estimate_tokens(text)` | `str` | `len(text) // 4` |
| `truncate_to_budget(text, max_tokens)` | `str, int` | Tronque à `max_tokens * 4` chars + `"..."` |
| `format_summary_metadata(metadata)` | `Dict` | `"📝 ou 🔄 FUSION dd/mm/YYYY HH:MM (X.X KB)"` |

**Méthode privée :** `_format_date_range(start, end)` — gère même jour, même mois, ou plage complète.

---

## `recall_agent.py` — Classe `RecallAgent`

**Rôle** : Orchestrateur principal — enchaîne détection → filtrage → chargement → construction.

**`__init__(temporal_parser, summary_loader, context_builder, debug=False)`**
- `_stats` : `{queries_processed, temporal_detected, contexts_generated, summaries_loaded}`

### Méthodes publiques

| Méthode | Paramètres | Retour | Description |
|---------|-----------|--------|-------------|
| `process_message(user_message, source="user")` | `str, str` | `Optional[str]` | Pipeline complet : parse → filter → load_multiple → build_context. Retourne contexte ou `None`. Màj stats. |
| `is_temporal_query(user_message)` | `str` | `bool` | Délègue à `temporal_parser.has_temporal_reference()` |
| `get_best_temporal_match(user_message)` | `str` | `Optional[TemporalMatch]` | Délègue à `temporal_parser.get_best_match()` |
| `preview_context(user_message)` | `str` | `dict` | Pipeline sans effet de bord — retourne `{temporal_match, summaries_count, context_length, context_tokens, context_preview}` |
| `get_statistics()` | — | `dict` | Stats internes + `summary_loader.get_statistics()` + `hit_rate` |
| `reset_statistics()` | — | — | Remet tous compteurs à 0 |
| `refresh_cache()` | — | — | Délègue à `summary_loader.refresh_cache()` |
| `search_by_keywords(keywords, max_results=5)` | `List[str], int` | `Optional[str]` | Fallback si pas de pattern temporel |

### `hit_rate` — calcul

```
hit_rate = contexts_generated / queries_processed   (si > 0, sinon 0.0)
```

---

## Flux d'intégration dans OGMA

```python
# Dans ogma_ng.py, avant l'appel IA
if contextual_recall and contextual_recall.is_available():
    recall_context = contextual_recall.process_message(user_message)
    if recall_context:
        system_prompt = recall_context + "\n\n" + system_prompt
```

---

## Exemples de patterns détectés

| Message utilisateur | Type détecté | Confiance |
|--------------------|-------------|-----------|
| `"tu te souviens de ce qu'on a dit hier ?"` | `absolute_simple` | 0.95 |
| `"on en avait parlé il y a 3 jours"` | `relative_days` | 0.90 |
| `"la semaine dernière tu m'as dit que..."` | `named_periods` | 0.85 |
| `"il faut que je consulte notre conversation de lundi"` | `ia_magic_phrase` | 0.95 |
| `"je dois consulter mes conversations avec Yohan"` | `ia_magic_phrase` | 0.95 |
| `"tu te souviens de notre discussion ?"` | `memory_triggers` | 0.60 |
