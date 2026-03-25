# Extension File Writer - Guide Utilisateur

## ✅ STATUT : FONCTIONNELLE

L'extension file_writer fonctionne parfaitement. Ce guide explique comment l'utiliser.

---

## 🎯 Déclenchement Automatique

L'extension détecte automatiquement vos demandes de création de fichiers `.md` dans vos messages.

### Phrases magiques détectées :

1. **"écris-moi un .md sur [sujet]"** (confidence: 0.95)
2. **"crée un document markdown sur [sujet]"** (confidence: 0.90)
3. **"rédige un fichier .md pour [sujet]"** (confidence: 0.95)
4. **"génère un .md [titre]"** (confidence: 0.90)
5. **"fais-moi un document .md"** (confidence: 0.85)

### Variantes naturelles acceptées :
- "écris un .md"
- "écris-nous un .md"
- "crée le document markdown"
- "rédige-moi le fichier .md"

---

## 📝 Workflow Complet

1. **Vous demandez** : "écris-moi un .md sur les bonnes pratiques Python"

2. **Luna génère** le contenu markdown dans sa réponse :
   ```markdown
   # Bonnes Pratiques Python
   
   ## Introduction
   Python est un langage élégant...
   ```

3. **Pré-détection** : Extension détecte votre demande (pattern match, confidence >0.7)

4. **Notification début** : "✍️ Écriture en cours..." (feedback immédiat)

5. **Extraction automatique** : Contenu markdown extrait de la réponse IA

6. **Sauvegarde automatique** : Fichier créé dans `data/uploads/`

7. **Notification succès** : "📁 Fichier sauvegardé: bonnes_pratiques_python.md"

---

## 📁 Localisation Fichiers

**Tous les fichiers .md sont sauvegardés dans** :
```
c:\IA\OGMA\data\uploads\
```

### Nommage automatique :
- Titre extrait de votre message (ex: "les bonnes pratiques Python" → `les_bonnes_pratiques_python.md`)
- Collision évitée avec suffixe `_1`, `_2`, etc.
- Horodatage dans les métadonnées

### Fichiers actuels (17/11/2025) :
- `sur_tes_capacités_et_les_phrases_magiques.md` (8549 bytes)
- `les_bonnes_pratiques_python.md` (481 bytes)
- `documentation.md` (41 bytes)
- `les_tests_python.md` (242 bytes)
- `sur_la_genèse_des_2_phares.md` (3158 bytes)

---

## 🔍 Logs Debug (activés)

Avec `debug=True`, vous verrez dans la console :

```
[FILE-WRITER] Vérification demande création fichier...
[DETECTOR] Pattern matched: \b(?:écris|rédige)...
[DETECTOR] Confidence: 0.95
[DETECTOR] Titre extrait: 'les_bonnes_pratiques_python'
[FILE-WRITER] 📝 Demande détectée, traitement en cours...
[FILE-WRITER-AGENT] ✅ Demande fichier détectée
[EXTRACTOR] Contenu markdown brut extrait (458 chars)
[SAVER] ✅ Fichier sauvegardé: data\uploads\les_bonnes_pratiques_python.md
[FILE-WRITER] ✅ Fichier sauvegardé: data\uploads\les_bonnes_pratiques_python.md
```

**Notifications UI** :
1. "✍️ Écriture en cours..." (dès détection, ~0.4ms)
2. "📁 Fichier sauvegardé: les_bonnes_pratiques_python.md" (après sauvegarde, ~7ms)

---

## 📊 Statistiques Extension

Utilisez l'API interne pour consulter les stats :

```python
from extensions.file_writer import get_file_writer

file_writer = get_file_writer()
stats = file_writer.get_statistics()

# Exemple résultat:
{
    'requests_processed': 10,
    'requests_detected': 8,
    'files_saved': 7,
    'extractions_failed': 1,
    'saves_failed': 0,
    'total_bytes': 12548,
    'success_rate': 0.875,  # 87.5% succès
    'extraction_rate': 0.875
}
```

---

## ⚙️ Configuration

### Activer/Désactiver debug :

**Fichier** : `ogma_ng.py` ligne 674

```python
_file_writer_ext = initialize_file_writer(
    uploads_dir="data/uploads",
    debug=True  # True = logs détaillés, False = silencieux
)
```

### Modifier patterns détection :

**Fichier** : `extensions/file_writer/request_detector.py`

Ajoutez vos propres patterns regex dans `DETECTION_PATTERNS`.

---

## 🐛 Troubleshooting

### Problème : Aucun fichier créé

**Causes possibles** :
1. Pattern non détecté → Vérifiez logs `[DETECTOR]`
2. Extraction échouée → Vérifiez logs `[EXTRACTOR]`
3. Sauvegarde échouée → Vérifiez permissions `data/uploads/`

**Solution** : Activez `debug=True` et consultez logs console

### Problème : Notification invisible

**Vérifiez** : ogma_ng.py ligne 4727
```python
_notify_safe(f"📁 Fichier sauvegardé: {Path(saved_path).name}", 'positive')
```

### Problème : Titre mal extrait

**Exemple** : "écris-moi un .md" → titre = `un`

**Solution** : Spécifiez un sujet explicite :
- ❌ "écris-moi un .md"
- ✅ "écris-moi un .md sur Python"

---

## ✨ Exemples Testés

### Test 1 : Demande simple
**Input** : "écris-moi un .md sur les tests Python"

**Output** : `data/uploads/les_tests_python.md` (242 bytes)

### Test 2 : Documentation
**Input** : "crée un document markdown de documentation"

**Output** : `data/uploads/documentation.md` (41 bytes)

### Test 3 : Guide complet
**Input** : "écris-moi un .md sur tes capacités et les phrases magiques"

**Output** : `data/uploads/sur_tes_capacités_et_les_phrases_magiques.md` (8549 bytes)

---

## 📈 Performance

**Tests diagnostic** (17/11/2025) :
- ✅ Détection : 100% (3/3 messages positifs détectés)
- ✅ Extraction : 100% (3/3 contenus extraits)
- ✅ Sauvegarde : 100% (3/3 fichiers créés)
- ⚡ Success rate : 1.0

**Production OGMA** :
- 6 fichiers créés (dont 5 aujourd'hui)
- Total : ~13 KB sauvegardés
- Aucune erreur détectée

---

## 🚀 Utilisation Avancée

### Forcer sauvegarde sans pattern

Modifiez votre demande pour inclure explicitement ".md" :

```
"crée un fichier .md avec le contenu suivant : ..."
```

### Vérifier fichier créé

```bash
# PowerShell
Get-ChildItem data\uploads\*.md | Sort-Object LastWriteTime -Descending | Select-Object -First 5
```

### Extraire contenu spécifique

L'extension détecte automatiquement :
- Blocs markdown délimités (# Titre, ## Section)
- Blocs code markdown (```markdown...```)
- Contenu brut si pas de structure

---

## 📝 Changelog

**17/11/2025 - v1.1** :
- ✅ Notification "✍️ Écriture en cours..." ajoutée (feedback immédiat)
- ✅ API `detect_request()` publique (pré-détection)
- ✅ Timing optimisé : Détection <1ms, Traitement ~7ms

**17/11/2025 - v1.0** :
- ✅ Debug mode activé (ogma_ng.py)
- ✅ Tests complets réussis (standalone + contexte OGMA)
- ✅ Guide utilisateur créé

**02/11/2025** :
- ✅ Extension file_writer implémentée
- ✅ Premier fichier production créé (`sur_la_genèse_des_2_phares.md`)

---

## 💡 Conseils

1. **Soyez explicite** : "écris-moi un .md sur [SUJET]" plutôt que "écris-moi un .md"
2. **Vérifiez notifications** : L'UI affiche "📁 Fichier sauvegardé: ..." après création
3. **Consultez logs** : Mode debug montre chaque étape (détection, extraction, sauvegarde)
4. **Explorez data/uploads/** : Tous vos fichiers y sont stockés

---

**CONCLUSION** : L'extension file_writer est **100% fonctionnelle**. Si problème, vérifiez logs debug et patterns détection.
