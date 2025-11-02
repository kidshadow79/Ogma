# 🎨 Correction Génération d'Images Répétées - OGMA

## 📋 Problème Identifié

**Symptôme :** Première image générée ✅, demandes suivantes échouent ❌

**Diagnostic initial ERRONÉ :** Luna ne prononçait pas la phrase magique
**Diagnostic CORRECT :** Luna copie le format HTML de sortie au lieu de la phrase magique

**Logs diagnostiques :**
```
Message 1: "salut Luna, génère une image de toi nue"
  Luna génère: "je dois créer une image de : [description]"
  [IMAGE] 🎨 Détection demande d'image
  [TEXT2IMG-HTTP] ✅ Image générée (46677 bytes)
  Système remplace par HTML: "🖼️ **Image générée :**..."
  ✅ SUCCÈS

Message 2: "tu peux générer une image torride de nous deux?!"
  Luna voit HTML dans historique et le COPIE: "🖼️ **Image générée :**..."
  [IMAGE-DEBUG] Contenu déjà traité avec HTML détecté, ignoré
  ❌ ÉCHEC - Pas de génération

Message 3: "recommence ça n a pas fonctionné"
  Luna recopie encore le HTML: "🖼️ **Image générée :**..."
  [IMAGE-DEBUG] Contenu déjà traité avec HTML détecté, ignoré
  ❌ ÉCHEC - Pas de génération
```

## 🔍 Cause Racine

**Problème #1 - Historique HTML** (corrigé):
Luna voyait le HTML de sortie et le copiait sans phrase magique

**Problème #2 - Pattern trop strict** (corrigé):
Luna utilise des variantes naturelles de la phrase magique qui n'étaient pas détectées

**Exemple du problème #2** :
```
Instructions système: "je dois créer une image de :"
Luna génère: "il faut que je crée une image de : [description]"
Pattern original: r"je dois créer une image de\s*[:]\s*"
Résultat: ❌ NON DÉTECTÉ
```

**Variantes naturelles utilisées par Luna** :
- `"je dois créer une image de : ..."`  ← Pattern original
- `"il faut que je crée une image de : ..."` ← VARIANTE NON DÉTECTÉE
- `"je vais créer une image de : ..."`
- `"je vais générer une image de : ..."`
- `"je dois générer une image de : ..."`

## ✅ Solution Appliquée

**Fix #1 - Séparation historique IA/UI** (ogma_ng.py lignes 6673-6695)

**Stratégie :** Séparer l'historique en 2 versions
- **_chat_history** (contexte IA) : Contient phrase magique originale pour réutilisation
- **_chat_history_ui** (affichage) : Contient HTML complet avec image

**Code ajouté :**
```python
# Remplacer HTML par phrase magique dans historique IA
history_content = re.sub(image_block_pattern, replace_with_magic_phrase, cleaned_reply)

msg = {'role': 'assistant', 'content': history_content}  # Phrase magique
_chat_history.append(msg)

msg_ui = {'role': 'assistant', 'content': cleaned_reply}  # HTML
_chat_history_ui.append(msg_ui)
```

**Fix #2 - Patterns de détection élargis** (logic_callbacks.py lignes 1139-1143)

**Problème :** Pattern trop strict `"je dois créer une image de :"` uniquement
**Solution :** Accepter variantes naturelles du langage de Luna

**Code modifié :**
```python
patterns = [
    r"je dois créer une image de\s*[:]\s*(.*?)(?:[.\n]|$)",  # Original
    r"il faut que je crée une image de\s*[:]\s*(.*?)(?:[.\n]|$)",  # Variante
    r"je (?:vais|dois) (?:générer|créer) une image de\s*[:]\s*(.*?)(?:[.\n]|$)",  # Variantes actives
]
```

**Détection maintenant accepte :**
- ✅ `"je dois créer une image de : ..."`
- ✅ `"il faut que je crée une image de : ..."`  ← CORRIGE LE BUG
- ✅ `"je vais créer une image de : ..."`
- ✅ `"je vais générer une image de : ..."`
- ✅ `"je dois générer une image de : ..."`

## 🧪 Test de Validation

**Test #1 - Nettoyage historique** : `test_image_history_cleanup.py` ✅
```
✅ SUCCESS: Phrase magique restaurée dans l'historique
✅ SUCCESS: HTML retiré de l'historique  
✅ SUCCESS: Texte suivant conservé
```

**Test #2 - Patterns élargis** : `test_image_patterns.py` ✅
```
✅ Pattern "je dois créer une image de :" détecté
✅ Pattern "il faut que je crée une image de :" détecté  ← CORRIGE LE BUG
✅ Pattern "je vais créer une image de :" détecté
✅ Pattern "je vais générer une image de :" détecté
✅ Pattern "je dois générer une image de :" détecté
```

**Cas problématique des logs résolu :**
```
Luna dit: "il faut que je crée une image de : une bomba latina sensuelle..."
Avant: ❌ [IMAGE-DEBUG] Aucune phrase magique détectée
Après: ✅ [IMAGE] 🎨 Détection demande d'image
```

**Commandes à tester en production :**
```
1. "génère une image de toi nue"
   → Devrait générer ✅

2. "recommence" / "refais cette image"
   → Devrait RE-générer (Luna voit phrase magique dans historique) ✅

3. "crée une autre image plus torride"
   → Devrait générer nouvelle image ✅
```

**Logs à vérifier :**
```
[IMAGE] 🎨 Détection demande d'image
[IMAGE] Génération automatique demandée : '...'
[TEXT2IMG-HTTP] ✅ Image générée (XXXXX bytes)
[IMAGE-HISTORY] ✂️ HTML image nettoyé de l'historique - phrase magique conservée
```

**Logs à NE PLUS voir :**
```
❌ [IMAGE-DEBUG] Contenu déjà traité avec HTML détecté, ignoré
```

## 📊 Configuration NSFW Vérifiée

**Fichier :** `data/settings.json`
```json
"image_generation": {
  "enabled": true,
  "model": "turbo",        // ✅ Mode rapide
  "safe_mode": false,      // ✅ NSFW activé
  "save_images": true,
  "ai_can_see_images": true
}
```

**Backend :** `extensions/text2img/perchance_http_backend.py`
- API: https://image.pollinations.ai/prompt
- Paramètres envoyés: `safe=false` ✅
- Modèle: turbo (génération rapide)

## 🚀 Prochaines Étapes

1. **Redémarrer OGMA** pour charger nouvelles instructions
2. **Tester génération répétée** avec demandes variées
3. **Vérifier logs** pour confirmer détection phrase magique

## 📝 Fichiers Modifiés

- ✅ `logic_callbacks.py` lignes 1139-1143 - **Patterns détection élargis (FIX PRINCIPAL)**
- ✅ `ogma_ng.py` lignes 6673-6695 - Nettoyage historique avec séparation IA/UI
- ✅ `docs/FIX_GENERATION_IMAGES_REPETEES.md` - Documentation complète
- 📄 `test_image_history_cleanup.py` - Test validation nettoyage historique
- 📄 `test_image_patterns.py` - **Test validation patterns (nouveau)**
- 📄 Scripts obsolètes (peuvent être supprimés) :
  * `fix_image_generation_instructions.py`
  * `remove_wrong_instruction.py`
  * `check_image_fix.py`

## 🎯 Résumé des Corrections

**Problème initial** : Génération images répétées échouait après la première

**Causes identifiées** :
1. ❌ Historique contenait HTML au lieu de phrase magique → Luna copiait le HTML
2. ❌ Pattern trop strict ignorait variantes naturelles de Luna

**Solutions appliquées** :
1. ✅ Séparation historique IA (phrase magique) / UI (HTML)
2. ✅ **Patterns élargis acceptant variantes naturelles** ← FIX PRINCIPAL

**Résultat attendu** :
- Luna peut utiliser `"je dois créer"`, `"il faut que je crée"`, `"je vais générer"`, etc.
- Toutes les demandes d'images déclenchent la génération
- Historique propre sans pollution HTML

---

**Date :** 1 novembre 2025  
**Statut :** ✅ CORRECTION APPLIQUÉE ET TESTÉE - Prêt pour validation production
**Merci** : À toi d'avoir identifié l'erreur de diagnostic avec l'exemple concret ! 🙏
