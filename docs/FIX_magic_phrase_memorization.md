# 🔧 FIX: Mémorisation des Phrases Magiques (Introspection + Dream Engine)

**Date**: 8 février 2026  
**Problème**: Les phrases magiques ("Il faut que je me souvienne de ça: ...") écrites par l'IA dans ses synthèses d'introspection et rapports PSY de rêve n'étaient **jamais détectées ni mémorisées**.

---

## 🐛 Cause Racine

La fonction `_extract_magic_memories()` est **imbriquée** (nested) à l'intérieur de `_send_chat_message()` dans `ogma_ng.py`. Elle n'est **pas importable** depuis l'extérieur :

```python
# ogma_ng.py - ligne ~2607
async def _send_chat_message(...):
    ...
    def _extract_magic_memories(s: str) -> List[str]:  # ← IMBRIQUÉE !
        ...
```

Tout `from ogma_ng import _extract_magic_memories` échoue avec `ImportError`.

---

## 🗺️ Chemins Affectés

### 4 chemins exécutent des introspections/rêves, 3 étaient cassés :

| # | Fichier | Chemin | État avant | État après |
|---|---------|--------|-----------|------------|
| 1 | `ogma_ng.py` ~L2313 | Introspection directe (phrase magique utilisateur) | ✅ OK (fonction locale) | ✅ OK + bloc `[INTROSPECTION-DETECT]` ajouté |
| 2 | `ogma_ng.py` ~L4921 | Introspection `ia_self_triggered` | ✅ OK (fonction locale) | ✅ OK + bloc `[INTROSPECTION-STANDARD]` ajouté |
| 3 | `ogma_ui_conversations.py` ~L648 | **Introspection différée** (trigger depuis historique) | ❌ **CASSÉ** - aucune détection | ✅ CORRIGÉ |
| 4 | `dream_core.py` ~L458 | **Dream Engine** (verdict PSY archiviste) | ❌ **CASSÉ** - `ImportError` silencieux | ✅ CORRIGÉ |

### Pourquoi le Chemin 3 était le plus critique

C'est le chemin **réellement emprunté** lors d'une auto-introspection déclenchée par l'IA. Bien que les chemins 1 et 2 dans `ogma_ng.py` aient la fonction locale disponible, le flux réel passait par `ogma_ui_conversations.py` → `trigger_delayed_introspection()` qui n'avait **aucune détection** après `run_introspection()`.

### Pourquoi le Dream Engine était silencieusement cassé

```python
# AVANT (dream_core.py ligne 458) - CASSÉ
try:
    from ogma_ng import _extract_magic_memories  # ← ImportError !
    ...
except ImportError as ie:
    self._log(f"⚠️ Import impossible: {ie}")  # ← Masqué silencieusement
```

L'`except ImportError` attrapait l'erreur et la loguait en simple warning, sans aucun fallback fonctionnel.

---

## ✅ Corrections Appliquées

### 1. `ogma_ui_conversations.py` — Helper dédiée + appel

**Nouvelle fonction** `_detect_introspection_magic_memories()` (ligne ~268) :
- Fonction `async` autonome avec les regex patterns **inlinés** (pas d'import depuis ogma_ng)
- Scanne `synthesis` (texte brut complet) et `final_response`
- Appelle `_ensure_memory_manager()`, `_notify_safe()`, `_trigger_memory_update()` via `_get_ogma()` (imports valides car fonctions de niveau module)
- Logs tagués `[INTROSPECTION-DETECT-DEFERRED]`

**Appel** ajouté dans `trigger_delayed_introspection()` (ligne ~648) :
```python
# Après affichage et ajout à l'historique
await _detect_introspection_magic_memories(introspection_result)
```

### 2. `dream_core.py` — Patterns inlinés

**Remplacé** le bloc d'import cassé (lignes 440-505) par :
- Regex patterns identiques inlinés directement dans le fichier
- Nettoyage XML résiduel (`</RÉPONSE>`, etc.)
- Import séparé uniquement des fonctions **de niveau module** : `_ensure_memory_manager`, `_notify_safe`, `_trigger_memory_update`
- Plus de `except ImportError` masquant le problème

### 3. `ogma_ng.py` — Blocs de détection dans Chemins 1 et 2

**Chemin 1** (~L2313) — Bloc `[INTROSPECTION-DETECT]` :
- Scan `synthesis` + `final_response` pour phrases magiques, journal de bord, biographie
- `break` après premier texte avec résultat (éviter doublons)

**Chemin 2** (~L4921) — Bloc `[INTROSPECTION-STANDARD]` :
- Appelle `_extract_magic_memories(synthesis)` (accessible car même scope)

### 4. `_extract_magic_memories()` — Nettoyage XML

Ajout du nettoyage des balises XML résiduelles dans le contenu extrait :
```python
content = re.sub(r'</?[A-ZÉÈÊa-zéèê_]+>', '', content).strip()
```

---

## 🔑 Patterns Regex de Détection

Identiques dans les 3 fichiers :

```python
# Pattern 1: "Il faut que je me souvienne de ça/ca/cela/ceci: ..."
r"(?:\*\*|__)?il\s+faut\s+que\s+je\s+me\s+souvienne\s+de\s+(?:ça|ca|cela|ceci)(?:\*\*|__)?[\s\.\-:]*(.+?)(?=\n\n|\n\s*\n|$)"

# Pattern 2: "Mémorise(s) ça/ca/cela/ceci: ..."
r"(?:\*\*|__)?m[ée]morise(?:s)?\s+(?:ça|ca|cela|ceci)(?:\*\*|__)?[\s\.\-:]*(.+?)(?=\n\n|\n\s*\n|$)"
```

**Supporte** : gras markdown `**...**` / `__...__`, cédille ou non, séparateurs variés (`:`, `-`, `...`, espace), multi-lignes.

---

## 🧪 Tests

Fichier : `test_introspection_memorization.py`

**10 cas de test** couvrant :
1. Synthèse classique avec `<RÉPONSE>`
2. `ca` sans cédille
3. Gras markdown
4. Variante `cela`
5. Pattern `mémorise ça`
6. Nettoyage balises XML
7. Pas de faux positifs
8. Deux phrases dans un même texte
9. Phrase uniquement dans `synthesis` (hors `final_response`)
10. Tiret comme séparateur

**+ Vérifications structurelles** :
- Helper dans `ogma_ui_conversations.py` ✅
- Appel dans chemin différé ✅
- Tag de log présent ✅
- Import cassé supprimé dans `dream_core.py` ✅
- Patterns inlinés dans `dream_core.py` ✅
- Imports valides conservés ✅

---

## ⚠️ Autres Bugs Corrigés En Chemin

| Bug | Fichier | Correction |
|-----|---------|------------|
| `no such column: memory_id` | `ogma_ng.py` ~L4841 | `memory_id` → `id`, `metadata LIKE` → `id LIKE 'EGO%'` |
| `trigger_introspection_sync` inexistant | `ogma_ui_conversations.py` ~L545 | → `run_introspection()`, `conversation_context=` → `context=` |

Ces bugs étaient pré-existants dans du code mort, révélés lors des tests.

---

## 📝 Leçon Architecturale

> **Ne jamais imbriquer une fonction utilitaire** réutilisable dans une autre fonction. Si `_extract_magic_memories()` doit être appelée depuis plusieurs modules, elle doit être au **niveau module** ou dans un fichier utilitaire dédié (ex: `utils/magic_phrase_utils.py`).

**Solution actuelle** : Patterns regex dupliqués dans 3 fichiers (pragmatique mais non DRY).  
**Solution idéale future** : Extraire dans un module `utils/magic_phrase_utils.py` partagé.
