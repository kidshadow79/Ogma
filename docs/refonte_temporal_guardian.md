# Refonte Temporal Guardian — Analyse & Plan d'action

**Date :** 31 mars 2026  
**Statut :** En discussion — en attente d'implémentation

---

## 1. Architecture actuelle

### Fichiers

```
extensions/temporal_guardian/
├── temporal_sensor.py         → mesure brute intra-session
├── temporal_guardian.py       → orchestrateur + analyze_with_archiviste()
├── archiviste_enricher.py     → formatage données (INUTILISÉ dans chemin normal)
├── config.py                  → paramètres
└── INSTRUCTIONS_ARCHIVISTE_TEMPOREL.md
modules/preanalysis_optimizer/
└── unified_meta_analyzer.py   → appel Archiviste unifié (JSON 3-en-1)
```

### Chemin normal (PREANALYSIS=True)

```
_send_chat_message()
  → process_user_message()        [APPELÉ 2 FOIS - BUG]
  → get_optimized_context_for_message()
      → UnifiedMetaAnalyzer.analyze()  [1 appel API]
          → JSON { temporal, capability, directive }
  → parallel_temporal_instruction → temporal_final_alert
  → injection en tête des instructions IA principale
```

### Chemin fallback (PREANALYSIS=False)

```
_send_chat_message()
  → process_user_message()
  → analyze_with_archiviste()      [appel API séquentiel direct]
  → temporal_final_alert
```

---

## 2. Problèmes identifiés (7)

| # | Problème | Impact |
|---|---|---|
| 1 | **Double appel `process_user_message()`** | `message_count` incrémenté x2, délais intra-session biaisés |
| 2 | **Pas de filtre Python (seuil 5 min)** | Section temporelle envoyée à chaque message, réponse NORMAL 95% du temps |
| 3 | **Premier message = `delay_since_last=None`** | Analyse inter-sessions impossible — Archiviste reçoit "Premier message de la session" sans contexte utile |
| 4 | **Inter-session delay calculé mais non passé** | `delta_sec` existe dans `ogma_ng.py` (bloc ~ligne 3735) pour contexte mémoriel, jamais communiqué au Temporal Guardian |
| 5 | **`ArchivisteEnricher` inutilisé** | Code mort dans le chemin normal (`archiviste_prompt=""` passé au `UnifiedMetaAnalyzer`) |
| 6 | **`temperature=0.7` dans `analyze_with_archiviste()`** | Trop créatif pour une décision analytique (chemin fallback) |
| 7 | **`reset_session()` jamais appelé** | La session temporelle n'est jamais réinitialisée, même après 30+ min d'inactivité |

---

## 3. Nouvelle architecture proposée (rejetée partiellement)

Proposition initiale : filtre Python complet (seuil 5 min avant d'appeler l'Archiviste), inter-session via `_conv_index`.

### Pourquoi le filtre Python ≠ économie d'appel API

Le `UnifiedMetaAnalyzer` fait **1 seul appel API** pour 3 analyses (temporal + capability + directive).  
Filtrer le temporal n'économise **pas** un round-trip — l'appel a lieu quand même pour capability et directive.  
Gain réel si filtre appliqué : ~60 tokens dans le prompt (la section temporelle), pas un call entier.

---

## 4. Plan d'action recommandé — 3 chirurgies ciblées

### Priorité HAUTE

**TODO 1 — Fix double appel (`ogma_ng.py`)**  
- Supprimer le bloc "TEMPORAL GUARDIAN" (~lignes 3205–3285) qui appelle `process_user_message()` avant le bloc PREANALYSIS
- Ce résultat n'est jamais utilisé quand PREANALYSIS=True (écrasé plus bas)
- Impact : corrige message_count biaisé, supprime appel inutile

**TODO 2 — Inter-session delay (`temporal_sensor.py` + `temporal_guardian.py`)**  
Valeur ajoutée réelle : l'IA principale peut remarquer qu'on revient après 3 jours.

Dans `temporal_sensor.py`, ajouter :
```python
def compute_inter_session_delay(self, conv_index_data: dict) -> Optional[float]:
    """Calcule le délai depuis la dernière conversation (inter-sessions)."""
    if not conv_index_data:
        return None
    sorted_convs = sorted(conv_index_data.values(), key=lambda x: x.get('updated', ''), reverse=True)
    if not sorted_convs:
        return None
    last_updated = sorted_convs[0].get('updated', '')
    if not last_updated:
        return None
    from datetime import datetime
    last_dt = datetime.fromisoformat(last_updated)
    return (datetime.now() - last_dt).total_seconds()
```

Dans `temporal_guardian.py`, `process_user_message()` :
```python
# Ajouter paramètres is_first_message et conv_index_data
def process_user_message(self, user_message, archiviste_prompt="", 
                          is_first_message=False, conv_index_data=None):
    # Si premier message → calculer delta inter-sessions
    if is_first_message and conv_index_data:
        inter_session_delay = self.sensor.compute_inter_session_delay(conv_index_data)
        measurement.inter_session_delay = inter_session_delay  # injecter dans measurement
```

Dans `ogma_ng.py`, passer les nouveaux arguments :
```python
temporal_result = temporal_guardian_instance.process_user_message(
    user_message=text,
    archiviste_prompt="",
    is_first_message=not bool(_current_conversation_id),
    conv_index_data=_conv_index
)
```

### Priorité MOYENNE

**TODO 3 — temperature 0.3 dans `analyze_with_archiviste()` (`temporal_guardian.py`)**  
- Changer `temperature=0.7` → `temperature=0.3`
- Supprimer l'override `context_length=2048` → utiliser `archiviste_controller.context_length`
- Impact : réponses plus déterministes, moins de faux positifs comportementaux

---

## 5. Ce qu'on NE touche PAS (pour l'instant)

- `archiviste_enricher.py` — code non cassé, nettoyage non prioritaire
- `unified_meta_analyzer.py` — prompt inchangé (le filtre Python n'économise pas un appel)
- `INSTRUCTIONS_ARCHIVISTE_TEMPOREL.md` — améliorable mais non bloquant
- `config.py` — aucune modification nécessaire pour les 3 TODOs prioritaires

---

## 6. Résumé coût/bénéfice

| Action | Coût dev | Gain économique | Gain qualitatif |
|---|---|---|---|
| Fix double appel | Faible (suppression de bloc) | Nul (pas d'appel API supprimé) | ✅ Données temporelles correctes |
| Inter-session delay | Moyen (2 fichiers) | Nul (même nb d'appels) | ✅ IA remarque les absences |
| temperature 0.3 | Minime (1 ligne) | Nul | ✅ Moins de faux positifs |
| Filtre Python 5min (TODO 4) | Moyen | ⚠️ Faible (tokens, pas un appel) | — |
| Réécriture instructions .md | Moyen | Nul | ✅ Qualité réponses Archiviste |

---

## 7. En attente

- Proposition alternative de l'utilisateur (à évaluer)
- Feu vert implémentation
