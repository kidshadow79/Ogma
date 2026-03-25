# ✅ Configuration Titre Jeopardy Ego - Implémentation Complète

**Date**: 2 février 2026  
**Statut**: ✅ Implémenté et testé

---

## 📋 Résumé

Le prompt de génération de titre Jeopardy pour les traits ego est maintenant **entièrement configurable** comme les autres instructions OGMA.

---

## 🎯 Modifications Effectuées

### 1. **data/instructions_defaults.json**
Ajout de `ego_title_jeopardy` dans la section `prompts_defaults`:
```json
"ego_title_jeopardy": "Génère un titre au format Jeopardy pour ce trait de personnalité ego.\n\nRÈGLE: Le titre doit être 2 QUESTIONS DISTINCTES (avec ?) dont le texte ci-dessous est LA RÉPONSE.\nMaximum 20 mots au total.\n\nTrait ego: {trait_text}\n\nRetourne UNIQUEMENT les 2 questions séparées par un espace, rien d'autre."
```

### 2. **memory_manager.py** (lignes 728-770)
Modifié `store_ego_trait()` pour charger le prompt de manière configurable:

**Ordre de priorité**:
1. ✅ **settings.json** (`settings['prompts']['ego_title_jeopardy']`) - PRIORITAIRE
2. ✅ **instructions_defaults.json** (`prompts_defaults['ego_title_jeopardy']`) - FALLBACK
3. ⚠️ **Hardcodé** (uniquement si les 2 précédents échouent) - DERNIER RECOURS

**Code**:
```python
# Charger le prompt depuis settings.json (priorité)
jeopardy_prompt_template = None
try:
    from ogma_ng import _settings_manager
    if _settings_manager and _settings_manager.settings:
        jeopardy_prompt_template = _settings_manager.settings.get('prompts', {}).get('ego_title_jeopardy')
        if jeopardy_prompt_template:
            print(f"[EGO-TITLE] ✅ Prompt depuis settings.json")
except Exception:
    pass

# Fallback sur instructions_defaults.json
if not jeopardy_prompt_template:
    try:
        import json
        from pathlib import Path
        defaults_path = Path("data/instructions_defaults.json")
        if defaults_path.exists():
            with open(defaults_path, 'r', encoding='utf-8') as f:
                defaults = json.load(f)
                jeopardy_prompt_template = defaults.get('prompts_defaults', {}).get('ego_title_jeopardy')
                if jeopardy_prompt_template:
                    print(f"[EGO-TITLE] 📋 Prompt depuis instructions_defaults.json")
    except Exception as e:
        print(f"[EGO-TITLE] ⚠️ Erreur chargement defaults: {e}")

# Fallback hardcodé si rien trouvé
if not jeopardy_prompt_template:
    jeopardy_prompt_template = """..."""  # prompt hardcodé
    print(f"[EGO-TITLE] ⚠️ Fallback hardcodé utilisé")

# Formater le prompt avec le trait
jeopardy_prompt = jeopardy_prompt_template.format(trait_text=trait_text)
```

### 3. **ogma_modals.py** (après ligne 523)
Ajout de la définition UI pour l'instruction ego_title_jeopardy:

```python
{
    'id': 'ego_title_jeopardy',
    'title': '🎭 Titre Jeopardy Ego',
    'subtitle': 'Génération titre pour traits ego',
    'description': 'Prompt utilisé par l\'Archiviste pour générer un titre Jeopardy lors du stockage de traits ego.',
    'source': 'settings',
    'settings_key': 'ego_title_jeopardy',
    'template': """Génère un titre au format Jeopardy pour ce trait de personnalité ego.

RÈGLE: Le titre doit être 2 QUESTIONS DISTINCTES (avec ?) dont le texte ci-dessous est LA RÉPONSE.
Maximum 20 mots au total.

Trait ego: {trait_text}

Retourne UNIQUEMENT les 2 questions séparées par un espace, rien d'autre."""
}
```

---

## 🧪 Tests Effectués

✅ **Test 1**: `ego_title_jeopardy` présent dans `instructions_defaults.json`  
✅ **Test 2**: Placeholder `{trait_text}` fonctionnel  
✅ **Test 3**: Formatage du prompt avec trait exemple réussi  
✅ **Test 4**: Définition UI trouvée dans `ogma_modals.py`  
✅ **Test 5**: Logique de chargement depuis settings.json présente  
✅ **Test 6**: Fallback sur instructions_defaults.json présent  
✅ **Test 7**: Reset profil inclura `ego_title_jeopardy`

**Résultat**: 🎉 **TOUS LES TESTS PASSÉS**

---

## 🎯 Workflow Utilisateur

### 📝 Modifier le Prompt via Frontend

1. **Ouvrir OGMA** → Cliquer sur **⚙️ Paramètres**
2. Sélectionner **📜 Instructions**
3. Trouver **🎭 Titre Jeopardy Ego**
4. Modifier le texte du prompt
5. Cliquer **💾 Sauvegarder**

→ Le prompt est sauvegardé dans `data/settings.json` (`settings['prompts']['ego_title_jeopardy']`)  
→ Il sera utilisé prioritairement pour tous les futurs traits ego

### 🔄 Reset Profil

Lors d'un reset de profil (via ProfileManager), le système:

1. Charge `instructions_defaults.json`
2. Copie `prompts_defaults` → `settings.json`
3. Inclut automatiquement `ego_title_jeopardy` avec sa valeur par défaut

→ La version par défaut apparaît dans le frontend après reset

---

## 🔍 Architecture Technique

### Ordre de Chargement (Cascade)

```
1️⃣ PRIORITÉ MAXIMALE: settings.json
   ↓ (si absent ou erreur)
2️⃣ FALLBACK: instructions_defaults.json
   ↓ (si absent ou erreur)  
3️⃣ DERNIER RECOURS: Hardcodé dans memory_manager.py
```

### Avantages de Cette Architecture

- ✅ **Configurabilité**: Utilisateur peut personnaliser via UI
- ✅ **Sauvegarde persistante**: Modifications sauvées dans settings.json
- ✅ **Fallback robuste**: Fonctionne même si settings.json corrompu
- ✅ **Reset propre**: Restaure valeur par défaut depuis instructions_defaults.json
- ✅ **Cohérence**: Suit le pattern des autres instructions (salutations, temporal_guardian, etc.)

---

## 📊 Comportement Actuel

### Lors du Stockage d'un Trait Ego

```python
trait = "Je déteste mentir"

# 1. Chargement du prompt (cascade)
prompt_template = load_from_settings()  # Priorité
if not prompt_template:
    prompt_template = load_from_defaults()  # Fallback
if not prompt_template:
    prompt_template = HARDCODED_FALLBACK  # Dernier recours

# 2. Formatage
prompt = prompt_template.format(trait_text=trait)

# 3. Appel Archiviste
response = await archiviste.call_chat_api(prompt, ...)

# 4. Résultat
title = "Que déteste cette IA ? Quel comportement refuse-t-elle ?"
```

### Logs Visibles

```
[EGO-ARCHIVISTE] 📝 Génération titre Jeopardy...
[EGO-TITLE] ✅ Prompt depuis settings.json
```

Ou:
```
[EGO-TITLE] 📋 Prompt depuis instructions_defaults.json
```

Ou (si problème):
```
[EGO-TITLE] ⚠️ Fallback hardcodé utilisé
```

---

## ✨ Conclusion

Le prompt `ego_title_jeopardy` est maintenant **entièrement configurable** et suit le **pattern OGMA standard**:

- ✅ Modifiable via frontend (Paramètres → Instructions)
- ✅ Sauvegarde dans settings.json
- ✅ Restauré depuis instructions_defaults.json lors d'un reset
- ✅ Priorité settings.json > instructions_defaults.json > hardcodé
- ✅ Cohérent avec les autres instructions (salutations, temporal_guardian, etc.)

**Statut**: ✅ **PRODUCTION READY**
