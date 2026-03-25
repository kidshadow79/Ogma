# TODO: Endpoints API Images - Providers Kie & WaveSpeed

**Date**: 6 février 2026  
**Statut**: ⚠️ ENDPOINTS INCONNUS (404)

---

## 🔴 Problème Identifié

Les endpoints utilisés pour récupérer dynamiquement les modèles retournent **404 Not Found** :

### Kie.ai
- **Endpoint testé**: `https://api.kie.ai/api/v1/models`
- **Erreur**: `404 Not Found` - `"No message available"`
- **Méthodes concernées**:
  - `fetch_live_models()` (text2img)
  - `fetch_live_img2img_models()` (img2img)

### WaveSpeed.ai
- **Endpoint testé**: `https://api.wavespeed.ai/api/v3/text-to-image/models`
- **Erreur**: `404 page not found`
- **Méthodes concernées**:
  - `fetch_live_models()` (text2img)
  - `fetch_live_img2img_models()` (img2img)

---

## ✅ Solution Temporaire Appliquée

Les méthodes `fetch_live_models()` et `fetch_live_img2img_models()` retournent maintenant:
```python
return None, "Endpoint API non disponible (à déterminer)"
```

**Avantages**:
- ✅ Plus d'erreurs 404 dans les logs
- ✅ Les modèles hardcodés continuent de fonctionner
- ✅ L'UI affiche un message clair à l'utilisateur

**Dans l'UI**, les boutons 🔄 affichent:
```
⚠️ Endpoints API /models non disponibles pour [Provider] (retournent 404)
💡 Les modèles hardcodés restent disponibles
```

---

## 🔍 Actions Requises

### 1. Trouver les Bons Endpoints

#### Pour Kie.ai ❌
**Documentation officielle**: https://docs.kie.ai/

**Statut**: ❌ **PAS D'ENDPOINT `/models`**
- Les modèles sont listés sur https://kie.ai/market (page web HTML)
- Pas d'API pour récupérer dynamiquement la liste
- Les modèles doivent être hardcodés dans `ogma_image_config.py`

**Alternative**:
- Utiliser le Playground de chaque modèle pour tester : https://kie.ai/market
- Contacter support Kie si endpoint API nécessaire

#### Pour WaveSpeed.ai ✅
**Documentation officielle**: https://wavespeed.ai/docs/list-models

**Endpoint confirmé**: `GET https://api.wavespeed.ai/api/v3/models`

**Ce que ça retourne**:
- TOUS les modèles (T2I, I2I, T2V, I2V, etc.)
- Format JSON avec `model_id`, `type`, `api_schema`, `base_price`
- Filtrage par type côté client :
  ```python
  t2i_models = [m for m in models if m.get("type") == "text-to-image"]
  i2i_models = [m for m in models if m.get("type") == "image-to-image"]
  ```

---

## 🧪 Comment Tester un Endpoint

### Méthode 1: cURL
```bash
# Kie
curl -H "Authorization: Bearer YOUR_KIE_API_KEY" \
     https://api.kie.ai/ENDPOINT_A_TESTER

# WaveSpeed
curl -H "Authorization: Bearer YOUR_WAVESPEED_API_KEY" \
     https://api.wavespeed.ai/api/v3/ENDPOINT_A_TESTER
```

### Méthode 2: Python (requests)
```python
import requests

# Kie
headers = {"Authorization": "Bearer YOUR_KIE_API_KEY"}
response = requests.get("https://api.kie.ai/ENDPOINT", headers=headers)
print(f"Status: {response.status_code}")
print(response.json())

# WaveSpeed
headers = {"Authorization": "Bearer YOUR_WAVESPEED_API_KEY"}
response = requests.get("https://api.wavespeed.ai/api/v3/ENDPOINT", headers=headers)
print(f"Status: {response.status_code}")
print(response.json())
```

### Méthode 3: Postman
1. Créer une requête GET
2. URL: endpoint à tester
3. Headers: `Authorization: Bearer YOUR_API_KEY`
4. Send

---

## 🔧 Une Fois les Endpoints Trouvés

### 1. Mettre à jour le code backend

**Fichier**: `extensions/text2img/image_backend.py`

**Pour Kie** (lignes ~524 et ~590):
```python
async def fetch_live_models(self) -> Tuple[Optional[List[str]], Optional[str]]:
    # Remplacer:
    # return None, "Endpoint API Kie.ai /models non disponible (à déterminer)"
    
    # Par:
    if not self.is_available:
        return None, "Clé API Kie manquante"
    
    models_endpoint = "https://api.kie.ai/BON_ENDPOINT_ICI"
    headers = {
        "Authorization": f"Bearer {self.api_key}",
        "Content-Type": "application/json"
    }
    
    # ... reste du code de fetch (parser JSON, extraire modèles, etc.)
```

**Pour WaveSpeed** (lignes ~1602 et ~1668):
```python
async def fetch_live_models(self) -> Tuple[Optional[List[str]], Optional[str]]:
    # Remplacer:
    # return None, "Endpoint API WaveSpeed.ai /models non disponible (à déterminer)"
    
    # Par:
    if not self.is_available:
        return None, "Clé API WaveSpeed manquante"
    
    models_endpoint = f"{self.BASE_URL}/BON_ENDPOINT_ICI"
    headers = {
        "Authorization": f"Bearer {self.api_key}",
        "Content-Type": "application/json"
    }
    
    # ... reste du code de fetch (parser JSON, extraire modèles, etc.)
```

### 2. Mettre à jour l'UI

**Fichier**: `ogma_image_config.py`

**Pour Text-to-Image** (ligne ~703):
```python
async def refresh_models_from_api():
    """Récupère les modèles en direct depuis l'API du provider"""
    provider = provider_select.value
    
    # SUPPRIMER ces 4 lignes:
    # ui.notify(f'⚠️ Endpoints API /models non disponibles pour {provider} (retournent 404)', type='warning')
    # ui.notify('💡 Les modèles hardcodés restent disponibles', type='info')
    # return
    # # Code désactivé temporairement...
    
    # GARDER le reste du code (vérification provider, backend, fetch, etc.)
```

**Pour Image-to-Image** (ligne ~937):
```python
async def refresh_img2img_models_from_api():
    """Récupère les modèles img2img en direct depuis l'API du provider"""
    provider = img2img_provider_select.value
    
    # SUPPRIMER ces 4 lignes:
    # ui.notify(f'⚠️ Endpoints API /models non disponibles pour {provider} (retournent 404)', type='warning')
    # ui.notify('💡 Les modèles hardcodés restent disponibles', type='info')
    # return
    # # Code désactivé temporairement...
    
    # GARDER le reste du code (backend, fetch, update dropdown, etc.)
```

### 3. Tester

```bash
# Relancer les tests
python test_live_models_fetch.py
python test_live_img2img_models_fetch.py
```

### 4. Mettre à jour la documentation

**Fichier**: `docs/RECAP_REFRESH_MODELS_API.md`

Mettre à jour la section "Providers supportés" avec les vrais endpoints.

---

## 📌 État Actuel du Code

### Fichiers avec Code Désactivé
1. `extensions/text2img/image_backend.py`
   - `KieImageProvider.fetch_live_models()` - ligne ~524
   - `KieImageProvider.fetch_live_img2img_models()` - ligne ~590
   - `WaveSpeedImageProvider.fetch_live_models()` - ligne ~1602
   - `WaveSpeedImageProvider.fetch_live_img2img_models()` - ligne ~1668

2. `ogma_image_config.py`
   - `refresh_models_from_api()` - ligne ~703
   - `refresh_img2img_models_from_api()` - ligne ~937

### Fichiers Fonctionnels (Architecture OK)
- `ImageGenerationBackend.fetch_live_models()` ✅
- `ImageGenerationBackend.fetch_live_img2img_models()` ✅
- Tests `test_live_models_fetch.py` ✅
- Tests `test_live_img2img_models_fetch.py` ✅
- UI boutons 🔄 ✅

---

## 💡 Alternative: Contacter le Support API

Si les endpoints restent introuvables dans la documentation:

### Kie.ai
- **Support**: Vérifier leur Discord/Github/Support
- **Question**: "Quel est l'endpoint API pour lister les modèles disponibles (text2img et img2img) ?"

### WaveSpeed.ai
- **Support**: Vérifier leur Discord/Github/Support  
- **Question**: "Quel est l'endpoint API pour lister les modèles disponibles (text-to-image et image-to-image) ?"

---

## ✅ Checklist de Réactivation

- [ ] Trouver endpoint Kie text2img
- [ ] Trouver endpoint Kie img2img
- [ ] Trouver endpoint WaveSpeed text2img
- [ ] Trouver endpoint WaveSpeed img2img
- [ ] Tester les endpoints avec clé API réelle
- [ ] Mettre à jour `image_backend.py` (4 méthodes)
- [ ] Mettre à jour `ogma_image_config.py` (2 fonctions)
- [ ] Tester avec `test_live_models_fetch.py`
- [ ] Tester avec `test_live_img2img_models_fetch.py`
- [ ] Tester dans l'UI OGMA (boutons 🔄)
- [ ] Mettre à jour documentation

---

**Note**: En attendant, les modèles hardcodés dans `ogma_image_config.py` (dictionnaires `IMAGE_PROVIDERS`, `IMG2IMG_MODELS_KIE`, `IMG2IMG_MODELS_WAVESPEED`) fonctionnent parfaitement. La fonctionnalité de refresh dynamique est un **bonus** pour éviter de mettre à jour manuellement le code.
