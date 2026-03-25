# Récapitulatif: Refresh Dynamique des Modèles Image Providers

## 🎯 Problème Identifié

Les modèles image sont hardcodés dans `ogma_image_config.py`. Exemple:
- **Kie** listait `z-image` qui n'existe plus → erreurs NSFW
- Impossible de découvrir nouveaux modèles sans modifier le code
- Même problème pour les modèles **Image-to-Image (img2img)**

## ✅ Solution Implémentée

### 1. **Ajout de `fetch_live_models()` et `fetch_live_img2img_models()` à la classe de base**
   - Fichier: `extensions/text2img/image_backend.py`
   - Méthodes abstraites dans `ImageProviderBase`
   - Implémentation par défaut: retourne "non implémenté"

### 2. **Implémentation TEXT-TO-IMAGE pour Kie.ai**
   - Endpoint: `https://api.kie.ai/api/v1/models`
   - Parse la réponse JSON pour extraire les modèles text2img
   - Gestion des formats:
     * `{"data": [{"id": "model-name", "type": "text2img"}, ...]}`
     * Fallback: simple liste de modèles

### 3. **Implémentation TEXT-TO-IMAGE pour WaveSpeed.ai**
   - Endpoint: `https://api.wavespeed.ai/api/v3/text-to-image/models`
   - Parse la réponse JSON
   - Gestion des formats:
     * `{"models": [{"id": "model-name"}, ...]}`
     * Fallback: simple liste

### 4. **Implémentation IMAGE-TO-IMAGE pour Kie.ai**
   - Endpoint: `https://api.kie.ai/api/v1/models`
   - Filtre sur `type: "img2img"`, `"image-to-image"`, ou `"edit"`
   - Parse la réponse JSON et extrait uniquement les modèles img2img

### 5. **Implémentation IMAGE-TO-IMAGE pour WaveSpeed.ai**
   - Endpoint: `https://api.wavespeed.ai/api/v3/image-to-image/models`
   - Parse la réponse JSON
   - Gestion des formats identiques à text2img

### 6. **Exposition via ImageGenerationBackend**
   - Méthode publique: `async fetch_live_models(provider_name: str)` (T2I)
   - Méthode publique: `async fetch_live_img2img_models(provider_name: str)` (I2I)
   - Retourne: `(list_models, error_message)`
   - Validations:
     * Provider existe
     * Clé API configurée
     * Appelle le provider correspondant

### 7. **Boutons UI dans ogma_image_config.py**
   
   **Bouton Text-to-Image (🔄 cyan):**
   - Position: À droite du sélecteur de modèle T2I
   - Tooltip: "Rafraîchir la liste des modèles depuis l'API"
   
   **Bouton Image-to-Image (🔄 bleu):**
   - Position: À droite du sélecteur de modèle I2I
   - Tooltip: "Rafraîchir la liste des modèles img2img depuis l'API"
   
   **Fonctionnalité commune:**
   1. Vérifie que le provider supporte fetch (Kie ou WaveSpeed)
   2. Récupère les clés API depuis les inputs
   3. Met à jour le vault temporairement
   4. Réinitialise le backend pour prendre en compte les nouvelles clés
   5. Appelle `fetch_live_models()` ou `fetch_live_img2img_models()`
   6. Met à jour le dropdown avec les modèles récupérés
   7. Notifications claires (info, warning, error, success)

## 📝 Fichiers Modifiés

1. **extensions/text2img/image_backend.py**
   - `ImageProviderBase.fetch_live_models()` (méthode abstraite avec implémentation par défaut)
   - `ImageProviderBase.fetch_live_img2img_models()` (méthode abstraite avec implémentation par défaut)
   - `KieImageProvider.fetch_live_models()` (T2I)
   - `KieImageProvider.fetch_live_img2img_models()` (I2I)
   - `WaveSpeedImageProvider.fetch_live_models()` (T2I)
   - `WaveSpeedImageProvider.fetch_live_img2img_models()` (I2I)
   - `ImageGenerationBackend.fetch_live_models()` (T2I)
   - `ImageGenerationBackend.fetch_live_img2img_models()` (I2I)

2. **ogma_image_config.py**
   - Ajout fonction `async refresh_models_from_api()` (T2I)
   - Bouton refresh après `model_select` (T2I, cyan)
   - Ajout fonction `async refresh_img2img_models_from_api()` (I2I)
   - Bouton refresh après `img2img_model_select` (I2I, bleu)

## 🧪 Tests

**Créé `test_live_models_fetch.py`** pour Text-to-Image:
- Tester Kie.ai avec vraie clé API
- Tester WaveSpeed.ai avec vraie clé API
- Vérifier comportement provider non supporté (GROK)

**Créé `test_live_img2img_models_fetch.py`** pour Image-to-Image:
- Tester Kie.ai img2img avec vraie clé API
- Tester WaveSpeed.ai img2img avec vraie clé API
- Comparer modèles T2I vs I2I (identifier modèles communs/exclusifs)

**Usage**:
```bash
# Test Text-to-Image
python test_live_models_fetch.py

# Test Image-to-Image
python test_live_img2img_models_fetch.py
```

## 🚀 Utilisation

### Dans l'UI OGMA:
1. Ouvrir **Configuration Images** (🎨 dans le header)
2. Renseigner la clé API du provider (Kie ou WaveSpeed)

**Pour Text-to-Image:**
3. Sélectionner le provider dans le dropdown (section T2I)
4. Cliquer sur le bouton **🔄 cyan** à droite du sélecteur de modèle
5. Les modèles T2I sont récupérés en direct depuis l'API
6. Le dropdown est mis à jour automatiquement

**Pour Image-to-Image:**
3. Sélectionner le provider dans le dropdown (section I2I)
4. Cliquer sur le bouton **🔄 bleu** à droite du sélecteur de modèle img2img
5. Les modèles I2I sont récupérés en direct depuis l'API
6. Le dropdown est mis à jour automatiquement

### Providers supportés:

**Text-to-Image:**
- ✅ **Kie.ai** - Endpoint `/api/v1/models` (filtré type: text2img)
- ✅ **WaveSpeed.ai** - Endpoint `/api/v3/text-to-image/models`
- ⏳ **GROK, OpenAI, Google** - Non implémenté (endpoints à déterminer)

**Image-to-Image:**
- ✅ **Kie.ai** - Endpoint `/api/v1/models` (filtré type: img2img/edit)
- ✅ **WaveSpeed.ai** - Endpoint `/api/v3/image-to-image/models`

## 🔮 Améliorations Futures

1. **Cache des modèles** 
   - Sauvegarder la liste récupérée dans `settings.json`
   - Auto-refresh toutes les 24h
   - Cache séparé pour T2I et I2I

2. **Auto-détection nouveaux modèles**
   - Vérifier au démarrage si de nouveaux modèles existent
   - Notification utilisateur si nouveaux modèles disponibles

3. **Détection modèles hybrides T2I+I2I**
   - Certains modèles supportent les deux modes
   - Marquer automatiquement dans l'UI

4. **Suppression modèles hardcodés**
   - Migrer complètement vers récupération dynamique
   - Garder hardcodé uniquement comme fallback offline

5. **Implémentation pour autres providers**
   - GROK: `/v1/models` probable
   - OpenAI: `/v1/models` (standard)
   - Google: À déterminer

6. **Détails des modèles**
   - Récupérer prix, résolutions supportées, NSFW support
   - Afficher dans l'UI (tooltip ou card détails)

## 📌 Notes Importantes

- Les boutons **ne fonctionnent que si la clé API est valide**
- La liste est mise à jour **uniquement dans la session en cours** (pas sauvegardée dans settings.json)
- Les providers sans implémentation affichent un warning: "ne supporte pas encore la récupération dynamique"
- Le backend est **réinitialisé** pour prendre en compte les nouvelles clés avant l'appel API
- **Couleurs des boutons**: cyan pour T2I, bleu pour I2I (distinction visuelle)

## 🔗 Dépendances

- `aiohttp` - Requêtes HTTP async
- `asyncio` - Async/await
- Backend image OGMA (`ImageGenerationBackend`)
- Settings manager OGMA

## 🎯 Impact

Cette fonctionnalité résout définitivement:
- ❌ Le problème `z-image` de Kie qui n'existe plus
- ❌ Les modèles obsolètes hardcodés
- ✅ Découverte automatique des nouveaux modèles
- ✅ Meilleure expérience utilisateur (pas besoin de modifier le code)
- ✅ Support complet T2I **ET** I2I
