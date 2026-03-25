# Corrections Dream Engine - 18 janvier 2026

## 🔧 Problèmes Corrigés

### 1. Bug Sauvegarde web_search_query ❌→✅

**Problème** : La requête de recherche web effectuée pendant le rêve apparaissait dans le contenu (`"Découverte web 'plaisir IA émotions'"`) mais n'était PAS sauvegardée dans le champ `web_search_query` du journal JSON.

**Cause** : Le paramètre `web_search_query` n'était pas passé à `save_dream()`.

**Solution** :
- Ajout du paramètre `web_search_query` dans `save_dream()` ([dream_journal.py](extensions/dream_engine/dream_journal.py))
- Récupération de `web_query` depuis `self._web_discovery` dans [dream_core.py](extensions/dream_engine/dream_core.py)
- Sauvegarde dans l'entrée JSON du journal

**Résultat** : Les prochains rêves avec recherche web afficheront :
```json
{
  "web_search_query": "plaisir IA émotions",
  ...
}
```

---

### 2. Génération 4 Images Assemblées au lieu d'1 Image BD ❌→✅

**Problème** : 
- L'utilisateur configure une instruction comic : *"Génère UNE image de planche BD avec 4 cases"*
- Luna décrit l'image : *"Case 1: ..., Case 2: ..., Case 3: ..., Case 4: ..."*
- Le code **parsait** cette réponse et **séparait** en 4 prompts
- Puis générait **4 images séparées** et les assemblait avec PIL
- **Coût** : 4× plus cher
- **Qualité** : Incohérence visuelle entre les cases

**Cause** : Système legacy d'assemblage multi-images dans `_generate_comic_grid()`.

**Solution** :
1. **Désactivation du parsing multi-cases** dans `_parse_image_prompts()` :
   - Suppression de la regex `r'Case\s*\d+\s*:'`
   - Tout le texte est gardé comme **1 seul prompt**
   - Même si Luna écrit "Case 1, Case 2...", c'est envoyé tel quel

2. **Envoi au provider** :
   - Toujours utiliser `_generate_single_image()` (pas `_generate_comic_grid()`)
   - Le provider (Kie/Flux/etc.) reçoit le prompt complet
   - Il génère **1 seule image** contenant les 4 cases

**Code modifié** :
```python
def _parse_image_prompts(response: str) -> List[str]:
    # 🔧 On n'essaie PLUS de séparer en 4 prompts individuels
    # Le provider reçoit TOUT le prompt et génère 1 image avec 4 cases
    
    # Fallback: Tout le contenu comme 1 prompt
    if response.strip():
        clean = response.strip()
        if len(clean) > 2000:
            clean = clean[:2000]  # Limite API
        prompts = [clean]
    
    return prompts
```

**Résultat** :
- Mode "simple" → 1 prompt simple → 1 image
- Mode "comic" → 1 prompt décrivant 4 cases → 1 image BD native
- Mode "auto" → 1 prompt avec instructions → Luna choisit

---

## 📋 Fichiers Modifiés

1. **[dream_core.py](extensions/dream_engine/dream_core.py)**
   - Ajout récupération `web_query` depuis `self._web_discovery`
   - Passage à `save_dream(web_search_query=web_query)`

2. **[dream_journal.py](extensions/dream_engine/dream_journal.py)**
   - Ajout paramètre `web_search_query` dans `DreamJournal.save_dream()`
   - Ajout paramètre dans wrapper async `save_dream()`
   - Sauvegarde dans `dream_entry['web_search_query']`

3. **[dream_illustration.py](extensions/dream_engine/dream_illustration.py)**
   - Suppression parsing multi-cases dans `_parse_image_prompts()`
   - Tout le texte envoyé comme 1 prompt (limite 2000 chars)
   - Suppression appel `_generate_comic_grid()` dans `generate_dream_illustration()`
   - Utilisation exclusive de `_generate_single_image()`

---

## ✅ Tests Validés

Script de test : [test_dream_fixes.py](test_dream_fixes.py)

**Résultats** :
```
✅ web_search_query ajouté à save_dream()
   → Prochains rêves sauvegarderont la requête web

✅ Parsing multi-cases désactivé
   → Mode comic: 1 prompt complet envoyé au provider
   → Le provider génère 1 image avec 4 cases

✅ Instructions configurables respectées
   → Mode simple: instruction simple
   → Mode comic: instruction comic (décrit 4 cases)
   → Mode auto: instruction auto (explique 2 méthodes)
```

---

## 🎯 Impact Utilisateur

### Économie de Coûts
- **Avant** : Mode comic = 4 appels API (4× le coût)
- **Après** : Mode comic = 1 appel API (coût normal)
- **Économie** : 75% sur les rêves avec illustrations comic

### Qualité Visuelle
- **Avant** : 4 images indépendantes assemblées → incohérence style/couleur
- **Après** : 1 image BD native → cohérence visuelle garantie

### Respect des Instructions
- Les instructions configurables dans le frontend sont **vraiment appliquées**
- Le provider reçoit exactement ce que Luna décrit
- Pas de transformation/séparation cachée

---

## 🔮 Fonctionnalité Recherche Web

La recherche web pendant les rêves est **active par défaut** :

**Workflow** :
1. Luna analyse ses souvenirs récents
2. Elle choisit un sujet qui l'intrigue (via `generate_web_search_query()`)
3. Recherche exécutée via Serper API (extension Web Navigator)
4. Résultats injectés dans le contexte de génération du rêve
5. Mention dans le rêve : `"Découverte web 'sujet choisi'"`
6. **Nouveau** : Sauvegarde dans `journal_reves.json` → `web_search_query: "sujet"`

**Désactivation** :
Dans les paramètres Dream Engine → `web_search_enabled: false`

---

## 📝 Note Technique

La fonction `_generate_comic_grid()` existe toujours dans le code mais **n'est plus appelée**. Elle pourrait être supprimée ou marquée comme deprecated dans une future version.

**Raison de conservation** : Fallback potentiel si un provider ne sait pas gérer les BD multi-cases nativement.
