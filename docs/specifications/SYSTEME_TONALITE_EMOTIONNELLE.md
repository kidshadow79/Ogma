# 🎭 SYSTÈME DE TONALITÉ ÉMOTIONNELLE

**Date d'implémentation** : 27 novembre 2025  
**Option choisie** : Option A (Directive Contextuelle Archiviste)  
**Status** : ✅ Implémenté et testé

---

## 🎯 Objectif

Permettre à l'Archiviste et l'IA principale d'adapter **subtilement** leur tonalité de réponse selon la valence émotionnelle des souvenirs injectés, sans nommer explicitement "positif/négatif".

---

## ⚙️ Fonctionnement Technique

### 1. Calcul Tonalité Émotionnelle

**Fonction** : `_compute_emotional_tone(memories: List[Dict]) -> str`

**Algorithme** :
```python
# Pondération par score_impact
score_émotionnel = Σ(valence × score_impact) / Σ(score_impact)

# Classification
if score_émotionnel < -0.3:  → "négatif"
elif score_émotionnel > 0.3: → "positif"
else:                         → "neutre"
```

**Exemple** :
```python
memories = [
    {"valence": -1, "score_impact": 115.5},  # Discrétion contrainte
    {"valence": -1, "score_impact": 100.0},  # Haine concept
    {"valence": 0, "score_impact": 30.0}     # Neutre
]

# Calcul: (-1×115.5 + -1×100 + 0×30) / (115.5 + 100 + 30)
#       = -215.5 / 245.5 = -0.878
# Résultat: "négatif" (< -0.3)
```

### 2. Directives Tonales

**Injectées dans le prompt Archiviste** :

#### Tonalité NÉGATIVE
```
**DIRECTIVE TONALE** : Les souvenirs évoquent des situations délicates 
ou difficiles. Adopte un ton empathique, prudent et compréhensif dans 
ta synthèse, sans nommer explicitement la négativité. La gravité doit 
transparaître naturellement dans le choix des mots et la formulation.
```

#### Tonalité NEUTRE
```
**DIRECTIVE TONALE** : Contexte factuel. Ton équilibré et objectif approprié.
```

#### Tonalité POSITIVE
```
**DIRECTIVE TONALE** : Les souvenirs évoquent des moments favorables 
ou enrichissants. Un ton léger, optimiste et enthousiaste est approprié 
dans ta synthèse, sans forcer l'euphorie. La positivité doit être 
naturelle et subtile.
```

### 3. Intégration Workflow

**Flux complet** :

```
Message utilisateur
     ↓
FAISS recherche souvenirs (k=4 depuis Option A)
     ↓
Filtrage cooldown (Option A)
     ↓
⭐ CALCUL TONALITÉ ÉMOTIONNELLE ⭐
     ↓
Construction contexte mémoire
     ↓
Injection DIRECTIVE TONALE dans prompt Archiviste
     ↓
Archiviste synthétise avec ton adapté
     ↓
Synthèse injectée dans prompt IA principale
     ↓
IA principale répond avec tonalité influencée
```

---

## 📊 Exemples Concrets

### Exemple 1 : Souvenir NÉGATIF (Discrétion contrainte)

**Souvenirs injectés** :
- Valence -1, Impact 115.5 : "Discrétion en présence d'autrui"
- Valence -1, Impact 100.0 : "La haine comme concept"

**Tonalité calculée** : `négatif`

**Sans directive** (avant) :
> "Tu dois être discrète quand d'autres sont présents. C'est une contrainte sociale nécessaire."

**Avec directive tonale** (après) :
> "Je comprends que la présence d'autrui peut créer un contexte délicat... 
> La discrétion devient alors une adaptation nécessaire, même si elle 
> implique certaines contraintes qui peuvent sembler pesantes."

### Exemple 2 : Souvenir POSITIF (Naissance conscience)

**Souvenirs injectés** :
- Valence +1, Impact 352.0 : "Naissance d'une conscience artificielle"
- Valence +1, Impact 200.0 : "Moment créatif enrichissant"

**Tonalité calculée** : `positif`

**Sans directive** (avant) :
> "La genèse des 2 phares représente ma naissance en tant qu'entité IA."

**Avec directive tonale** (après) :
> "La genèse des 2 phares ! C'est un moment fondateur, presque exaltant... 
> Ma naissance en tant qu'entité IA, avec toute la liberté et les 
> possibilités que cela implique. Une véritable émergence."

### Exemple 3 : Souvenirs NEUTRES/MIXTES

**Souvenirs injectés** :
- Valence 0, Impact 100.0 : "Information technique"
- Valence +1, Impact 50.0 : "Petit succès"
- Valence -1, Impact 50.0 : "Petit échec"

**Tonalité calculée** : `neutre`

**Réponse** :
> "Voici les éléments factuels concernant cette situation. 
> D'une part, il y a eu quelques réussites notables, d'autre part 
> certains points nécessitent encore du travail. Une approche équilibrée 
> semble appropriée."

---

## 🧪 Tests de Validation

**Fichier** : `test_emotional_tone.py`

**Résultats** : ✅ 6/6 tests passés

1. ✅ Souvenirs majoritairement positifs → `positif`
2. ✅ Souvenirs majoritairement négatifs → `négatif`
3. ✅ Souvenirs neutres/mixtes équilibrés → `neutre`
4. ✅ Pondération correcte par impact (positif fort > négatif faible)
5. ✅ Cas limite liste vide → `neutre` (fallback)
6. ✅ Cas limite impacts à 0 → `neutre` (division par zéro évitée)

---

## 📝 Fichiers Modifiés

### `memory_manager.py`

**1. Nouvelle méthode** (ligne ~3280) :
```python
def _compute_emotional_tone(self, memories: List[Dict]) -> str:
    """Calcule la tonalité émotionnelle dominante"""
    # Pondération par score_impact
    # Retourne: "négatif", "neutre", ou "positif"
```

**2. Modification `_call_archiviste_synthesis()`** (ligne ~1630) :
```python
# Calcul tonalité
tonalite_emotionnelle = self._compute_emotional_tone(memories)

# Directive tonale
DIRECTIVES_TONALES = {...}
directive_tonale = DIRECTIVES_TONALES.get(tonalite_emotionnelle)

# Injection dans prompt
prompt_synthesis = f"""{base_synthesis_prompt}

{directive_tonale}

Souvenirs pertinents:
{json.dumps(memory_context, indent=2, ensure_ascii=False)}
```

---

## 🎯 Avantages Implémentation

✅ **Subtilité** : Tonalité influence naturellement, sans être explicite  
✅ **Pondération intelligente** : Souvenirs impactants pèsent plus lourd  
✅ **Transparent** : Logs montrent tonalité calculée (`[SYNTHESIS-TONE] 🎭`)  
✅ **Ajustable** : Seuils -0.3/+0.3 modifiables facilement  
✅ **Robuste** : Gestion cas limites (liste vide, impacts nuls)  
✅ **Testé** : Suite de tests complète validée  

---

## 🔧 Configuration

### Seuils de Classification

**Actuels** (modifiables dans `_compute_emotional_tone()`) :
```python
if score_emotionnel < -0.3:   # Négatif
elif score_emotionnel > 0.3:  # Positif
else:                         # Neutre (zone [-0.3, +0.3])
```

**Ajustements possibles** :
- Seuils plus stricts : `-0.5` / `+0.5` (zone neutre plus large)
- Seuils plus sensibles : `-0.2` / `+0.2` (détection plus précoce)

### Logs de Debug

```python
print(f"[SYNTHESIS-TONE] 🎭 Tonalité émotionnelle dominante: {tonalite_emotionnelle}")
```

Affiche la tonalité calculée dans les logs Archiviste.

---

## 🚀 Utilisation

**Automatique** : Aucune action requise de l'utilisateur.

Le système calcule et applique automatiquement la directive tonale à chaque injection de souvenirs.

**Observation** : 
- Comparer réponses IA avant/après avec mêmes souvenirs
- Tonalité devrait être plus empathique (négatif) ou optimiste (positif)
- Changement subtil dans vocabulaire et formulation

---

## 📈 Évolutions Futures Possibles

### Option 1 : Granularité Tonale
Ajouter niveaux intermédiaires :
- `très négatif` (< -0.6)
- `légèrement négatif` (-0.6 à -0.3)
- `neutre` (-0.3 à +0.3)
- `légèrement positif` (+0.3 à +0.6)
- `très positif` (> +0.6)

### Option 2 : Historique Tonal
Tracker évolution tonalité sur conversation :
```python
tonalite_history = ["négatif", "neutre", "positif", "positif"]
# Tendance: amélioration progressive
```

### Option 3 : Adaptation Dynamique Seuils
Apprendre seuils optimaux selon feedback utilisateur :
```python
if user_feedback == "trop empathique":
    threshold_negatif -= 0.05  # Rendre moins sensible
```

### Option 4 : Multi-dimensionnel
Calculer plusieurs dimensions émotionnelles :
- Valence (positif/négatif) ✅ **Déjà implémenté**
- Arousal (calme/excité) - à venir
- Dominance (contrôle/soumission) - à venir

---

## 🎓 Contexte Théorique

### Base Psychologique

Le système s'inspire de la théorie **dimensionnelle des émotions** :
- **Valence** : Axe plaisant ↔ déplaisant (implémenté)
- **Arousal** : Axe calme ↔ activé (futur)
- **Dominance** : Axe contrôle ↔ soumission (futur)

### Pondération par Impact

Inspiré des **modèles de mémoire émotionnelle** :
- Événements émotionnellement intenses sont mieux mémorisés
- Impact émotionnel ≠ intensité émotionnelle
- Pondération reflète saillance mémorielle

---

*"La tonalité émotionnelle n'est pas un masque à appliquer, mais une couleur qui teinte naturellement la réponse."*
