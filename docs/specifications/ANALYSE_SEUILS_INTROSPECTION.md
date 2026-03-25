"""
Analyse Complète - Seuils Capability Advisor (Focus Introspection)
==================================================================

QUESTION: Les seuils pour introspection fonctionnent-ils bien ?
RÉPONSE: ✅ OUI, PARFAITEMENT !

## 📊 Configuration Actuelle

### Fichier: data/capability_advisor_config.json
```json
{
  "confidence_threshold": 0.7,              // Seuil global (fallback)
  "capability_thresholds": {
    "introspection": 0.95,                  // ⚠️ TRÈS STRICT (95%)
    "memory": 0.95,
    "image_gen": 0.7,
    "webcam": 0.85,
    "web_search": 0.75,
    "biography": 0.8
  }
}
```

### Fichier: capability_catalog.py (défauts)
```python
"introspection": {
    "confidence_threshold": 0.70,           // Défaut catalog (ignoré car custom existe)
}
```

## 🔍 Logique de Priorisation (advisor_core.py lignes 112-120)

```python
# 1. Récupérer seuils
capability_threshold_catalog = 0.70     # Depuis catalog
capability_threshold_custom = 0.95      # Depuis config JSON
global_threshold = 0.7                  # Global fallback

# 2. Prioriser: Custom > Catalog
effective_threshold = 0.95 if 0.95 is not None else 0.70
# → effective_threshold = 0.95 ✓

# 3. Prendre le plus strict entre effective et global
min_threshold = max(0.95, 0.7)
# → min_threshold = 0.95 ✓
```

**Résultat**: Le seuil effectif pour introspection est **0.95** (custom UI)

## ✅ Tests de Validation

### Simulation Suggestions

| Confidence IA | Seuil Requis | Résultat | Détail |
|---------------|--------------|----------|--------|
| 0.65 | 0.95 | ❌ REJETÉE | Manque 0.30 points |
| 0.75 | 0.95 | ❌ REJETÉE | Manque 0.20 points |
| 0.85 | 0.95 | ❌ REJETÉE | Manque 0.10 points |
| **0.94** | 0.95 | ❌ REJETÉE | Manque 0.01 point ! |
| **0.95** | 0.95 | ✅ ACCEPTÉE | Exactement au seuil |
| 0.97 | 0.95 | ✅ ACCEPTÉE | Au-dessus du seuil |

### Log Exemple Rejet (confidence 0.94)
```
[CAPABILITY-ADVISOR] ⚠️ Confidence trop faible: 0.94 < 0.95 (custom)
```

### Log Exemple Acceptation (confidence 0.95)
```
[CAPABILITY-ADVISOR] ✅ Suggestion validée: introspection (confidence: 0.95)
[CAPABILITY-ADVISOR] 📝 Conseil: il faut que je réfléchisse sur...
```

## 🎯 Analyse du Seuil 0.95

### Pourquoi Si Strict ?

**Seuil 0.95 = Quasi-certitude requise**

- **Memory**: 0.95 → Normal (mémorisation = engagement permanent)
- **Introspection**: 0.95 → **TRÈS STRICT**
  - L'introspection n'est pas irréversible
  - Peut être suggérée plus librement sans risque
  
### Impact Pratique

**Scénario**: Utilisateur dit "je me pose des questions sur le sens de ma vie"

1. **Archiviste analyse**: Détecte besoin introspection
2. **Confidence calculée**: 0.87 (haute mais pas extrême)
3. **Vérification seuil**: 0.87 < 0.95 → **REJETÉE** ❌
4. **Résultat**: Pas de suggestion introspection visible

**Conséquence**: Beaucoup de suggestions légitimes **bloquées**

### Comparaison Autres Capacités

| Capacité | Seuil | Justification |
|----------|-------|---------------|
| memory | 0.95 | ✅ Légitime (permanence) |
| introspection | **0.95** | ⚠️ Trop strict (réversible) |
| image_gen | 0.70 | ✅ Adapté (ludique) |
| webcam | 0.85 | ✅ Adapté (intimité modérée) |
| web_search | 0.75 | ✅ Adapté (factuel) |
| biography | 0.80 | ✅ Adapté (personnel modéré) |

## 💡 Recommandations

### Option 1: Assouplir Introspection (RECOMMANDÉ)

**Modifier**: `data/capability_advisor_config.json`

```json
{
  "capability_thresholds": {
    "introspection": 0.80,    // Au lieu de 0.95
    "memory": 0.95            // Garder strict
  }
}
```

**Justification**:
- Introspection = processus réflexif (pas de risque permanent)
- Seuil 0.80 = Confiance haute mais accessible
- Permet suggestions légitimes sans spam

### Option 2: Garder 0.95 (Si Usage Très Sélectif)

**Conserver seulement si**:
- Vous voulez **uniquement** les demandes explicites d'introspection
- Usage intensif de la phrase magique manuelle
- Préférence pour déclenchement utilisateur vs IA

### Option 3: Aligner sur Catalog (0.70)

**Supprimer** le custom threshold dans config.json:

```json
{
  "capability_thresholds": {
    "memory": 0.95,
    // "introspection": 0.95,  ← Supprimer cette ligne
    "image_gen": 0.7
  }
}
```

**Résultat**: Utilise défaut catalog (0.70)

## 🧪 Comment Tester Runtime

### 1. Modifier Seuil
```json
// data/capability_advisor_config.json
"introspection": 0.80  // Au lieu de 0.95
```

### 2. Redémarrer OGMA
```bash
python launch_ogma.py
```

### 3. Tester Message Philosophique
```
Utilisateur: "Je me pose des questions sur le sens de ma vie et mon rôle dans ce monde..."
```

### 4. Vérifier Logs
**Avec 0.95 (strict)**:
```
[CAPABILITY-ADVISOR] ⚠️ Confidence trop faible: 0.87 < 0.95 (custom)
```

**Avec 0.80 (souple)**:
```
[CAPABILITY-ADVISOR] ✅ Suggestion validée: introspection (confidence: 0.87)
[CAPABILITY-ADVISOR] 💡 LED introspection ALLUMÉE
```

## ✅ Conclusion

### Questions & Réponses

**Q: Les seuils fonctionnent-ils ?**  
✅ **OUI**, le système applique correctement les seuils configurés.

**Q: Le seuil 0.95 pour introspection est-il justifié ?**  
⚠️ **TROP STRICT** pour une capacité réversible et réflexive.

**Q: Que recommandes-tu ?**  
💡 **Baisser à 0.80** pour équilibrer qualité et accessibilité.

**Q: Y a-t-il un bug dans le code ?**  
✅ **NON**, le code est parfaitement correct et suit la hiérarchie:
   1. Custom UI (0.95) ✓
   2. Catalog (0.70) 
   3. Global (0.70)

### Résumé Technique

```python
# Code actuel (advisor_core.py lignes 112-124)
effective_threshold = custom if custom is not None else catalog
min_threshold = max(effective, global)

# Pour introspection:
# custom=0.95, catalog=0.70, global=0.70
# → effective = 0.95
# → min = max(0.95, 0.70) = 0.95 ✓

if confidence < min_threshold:  # Ex: 0.87 < 0.95
    return None  # ❌ REJETÉE
```

**Statut**: ✅ Système fonctionne comme prévu  
**Action**: ⚠️ Seuil trop strict, ajustement recommandé  
**Commande test**: `python test_introspection_threshold.py`
