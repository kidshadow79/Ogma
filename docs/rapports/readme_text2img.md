# Extension Text2Image (Text-to-Image) — Documentation Exhaustive

**Dossier** : `extensions/text2img/`
**Rôle** : Génération d'images via prompts textuels (text-to-image) et transformation d'images existantes (image-to-image), avec support de 4 providers IA.

---

## Architecture — Fichiers

| Fichier | Classe | Rôle |
|---------|--------|------|
| `__init__.py` | — | API publique + singleton |
| `config.py` | `Text2ImgConfig` | Configuration providers + paramètres |
| `manager.py` | `Text2ImageManager` | Orchestrateur principal |
| `backend_base.py` | `ImageGenerationBackend` | Classe abstraite provider |
| `providers/grok.py` | `GrokImageProvider` | Provider Grok (Aurora) |
| `providers/openai.py` | `OpenAIImageProvider` | Provider OpenAI (DALL-E) |
| `providers/google.py` | `GoogleImageProvider` | Provider Google (Imagen) |
| `providers/kie.py` | `KieImageProvider` | Provider Kie.ai (multi-modèles) |
| `ui_components.py` | `Text2ImgUI` | Interface configuration NiceGUI |
| `phrases_magiques.py` | `PhrasesMagiquesT2I` | Détection phrases déclencheuses |

---

## `config.py` — Classe `Text2ImgConfig`

| Clé | Défaut | Description |
|-----|--------|-------------|
| `extension_enabled` | `True` | Activé par défaut |
| `default_provider` | `"grok"` | Provider par défaut |
| `save_generated_images` | `True` | Sauvegarde locale |
| `save_directory` | `"data/generated_images"` | Répertoire de sauvegarde |
| `default_width` | `1024` | Largeur par défaut |
| `default_height` | `1024` | Hauteur par défaut |
| `default_quality` | `"standard"` | `"standard"` ou `"hd"` |
| `max_images_per_request` | `4` | Maximum images par appel |
| `show_in_chat` | `True` | Affiche image dans chat NiceGUI |
| `kie_api_key` | `""` | Clé API Kie.ai |
| `kie_default_model` | `"z-image"` | Modèle Kie t2i par défaut |
| `kie_default_i2i_model` | `"kie-iclight"` | Modèle Kie i2i par défaut |
| `openai_model` | `"dall-e-3"` | Modèle OpenAI |
| `google_model` | `"imagen-3.0-generate-002"` | Modèle Google |
| `timeout_seconds` | `120` | Timeout génération |

---

## `manager.py` — Classe `Text2ImageManager`

**Rôle** : Sélectionne et appelle le bon provider selon la configuration.

### Nommage sécurisé des fichiers

Les noms de fichiers utilisent **des tirets** (pas des underscores) pour éviter les conflits NiceGUI avec les assets statiques :
```python
# Correct :  "reve-20251201-003.png"
# Incorrect : "reve_20251201_003.png"  (risque conflit NiceGUI)
```

### `async generate_image(prompt, provider=None, options={})` → `ImageResult`

1. `_select_provider(provider)` → instance concrete
2. `_validate_and_clean_prompt(prompt)` → nettoyage (guillemets, longueur max 4000 chars)
3. `provider.generate(prompt, options)` → bytes ou URL
4. `_save_image(result, prompt)` si `save_generated_images`
5. Retourne `ImageResult(path, url, prompt, provider, stats)`

### `async image_to_image(source_image_base64, prompt, provider=None, options={})` → `ImageResult`

- Même pipeline que `generate_image` mais avec `provider.image_to_image(base64, prompt, options)`
- Seulement Kie et OpenAI supportent i2i

### Méthodes utilitaires

| Méthode | Description |
|---------|-------------|
| `get_available_providers()` | Liste providers avec clés API valides |
| `get_available_models(provider)` | Modèles disponibles pour un provider |
| `_safe_filename(prompt, provider)` | Génère nom fichier sans espaces, caractères spéciaux, max 50 chars |
| `_display_in_chat(result)` | Injecte image dans chat NiceGUI via `ui.image()` |
| `get_stats()` | `{total_generated, by_provider, last_generation_time, ...}` |

---

## `backend_base.py` — Classe abstraite `ImageGenerationBackend`

```python
class ImageGenerationBackend(ABC):
    @abstractmethod
    async def generate(self, prompt: str, options: dict) -> GenerationResult: ...
    
    @abstractmethod
    async def image_to_image(self, base64_image: str, prompt: str, options: dict) -> GenerationResult: ...
    
    @abstractmethod
    def is_available(self) -> bool: ...
    
    @abstractmethod
    def get_models(self) -> list[str]: ...
```

---

## `providers/grok.py` — Classe `GrokImageProvider`

**Modèle** : `"aurora"` (via API xAI/Grok)
**i2i** : Non supporté

### `async generate(prompt, options)`

- Endpoint : `https://api.x.ai/v1/images/generations`
- Headers : `Authorization: Bearer {grok_api_key}`
- Body : `{model: "aurora", prompt: prompt, n: 1, response_format: "url"}`
- Retourne URL → télécharge bytes via `httpx.AsyncClient`

---

## `providers/openai.py` — Classe `OpenAIImageProvider`

**Modèle** : `"dall-e-3"` (ou `"dall-e-2"` si configuré)
**i2i** : Supporté via Edits API (DALL-E 2 uniquement)

### `async generate(prompt, options)`

- `openai.AsyncOpenAI(api_key=...)` → `client.images.generate()`
- Options supportées : `size` (`"1024x1024"`, `"1792x1024"`, `"1024x1792"`), `quality` (`"standard"`, `"hd"`), `style` (`"vivid"`, `"natural"`)
- DALL-E 3 : `n=1` toujours (limitation API)

### `async image_to_image(base64_image, prompt, options)`

- Utilise `client.images.edit()` (DALL-E 2 uniquement)
- Encode image en PNG bytes pour l'API
- Options : `size`, masque optionnel

---

## `providers/google.py` — Classe `GoogleImageProvider`

**Modèle** : `"imagen-3.0-generate-002"` (ou `"imagegeneration@006"`)
**i2i** : Supporté

### `async generate(prompt, options)`

- Via `google.generativeai` SDK ou REST API Vertex AI
- Paramètres : `number_of_images` (1-4), `aspect_ratio` (`"1:1"`, `"16:9"`, `"4:3"`), `safety_filter_level`
- Retourne bytes PNG

---

## `providers/kie.py` — Classe `KieImageProvider`

**Provider le plus riche** — 9 modèles t2i + 7 modèles i2i + polling

### Constantes

| Constante | Valeur |
|-----------|--------|
| `BASE_URL` | `"https://api.kie.ai/v1"` |
| `FILE_UPLOAD_URL` | `"https://api.kie.ai/v1/files/upload"` |
| `MAX_POLLS` | `300` (soit ~10 minutes à 2s/poll) |
| `POLL_INTERVAL` | `2.0` secondes |

### 9 modèles Text-to-Image

| Identifiant | Description |
|-------------|-------------|
| `"z-image"` | Défaut polyvalent |
| `"grok-imagine"` | Grok via Kie |
| `"dalle3-turbo"` | DALL-E 3 via Kie |
| `"stable-diffusion-xl"` | SDXL |
| `"stable-diffusion-3"` | SD3 |
| `"flux-1.1-pro"` | Flux Pro |
| `"flux-1-schnell"` | Flux rapide |
| `"ideogram-v2"` | Ideogram |
| `"recraft-v3"` | Recraft |

### 7 modèles Image-to-Image

| Identifiant | Description |
|-------------|-------------|
| `"kie-iclight"` | Défaut, relighting |
| `"kie-background-removal"` | Suppression fond |
| `"kie-upscale"` | Upscaling |
| `"kie-style-transfer"` | Transfert de style |
| `"kie-face-swap"` | Swap facial |
| `"kie-instruct-pix2pix"` | InstructPix2Pix |
| `"kie-controlnet-canny"` | ControlNet Canny |

### Pipeline génération (polling)

```
POST /generate → {job_id}
↓
POLL /jobs/{job_id} (toutes les 2s, max MAX_POLLS)
↓
status: "completed" → result.image_url
↓
Téléchargement bytes
```

### `_upload_image_for_i2i(base64_image)` → `str` (file_id)

- Encode base64 → bytes PNG
- POST sur `FILE_UPLOAD_URL` (multipart/form-data)
- Retourne `file_id` à injecter dans paramètres i2i

### `async generate(prompt, options)` et `async image_to_image(base64_image, prompt, options)`

- Tous deux suivent le même pipeline polling
- `options` supportées t2i : `model`, `width`, `height`, `steps`, `guidance_scale`, `negative_prompt`, `seed`
- `options` supportées i2i : `model`, `strength` (0.0-1.0), `guidance_scale`, `prompt`

---

## `phrases_magiques.py` — Classe `PhrasesMagiquesT2I`

### Patterns de détection

| Catégorie | Exemples de phrases |
|-----------|---------------------|
| `t2i_standard` | `"génère une image"`, `"crée une image"`, `"dessine"`, `"illustre"`, `"peins"`, `"visualise"` |
| `t2i_style` | `"en style"`, `"façon"`, `"comme une photo"`, `"comme un tableau"` |
| `i2i_transform` | `"transforme cette image"`, `"modifie l'image"`, `"retouche"` |
| `i2i_variation` | `"variation de"`, `"une autre version"` |

### Méthodes

| Méthode | Retour | Description |
|---------|--------|-------------|
| `detect_t2i(text)` | `Optional[str]` | Extrait le prompt si phrase t2i détectée |
| `detect_i2i(text)` | `Optional[str]` | Extrait le prompt si phrase i2i détectée |
| `clean_prompt(text)` | `str` | Retire la phrase magique, garde le vrai prompt |

---

## `__init__.py` — API Publique

| Fonction | Description |
|----------|-------------|
| `initialize_text2img(settings_manager)` | Init singleton + providers |
| `is_available()` | `_manager is not None` |
| `is_enabled()` | `config.extension_enabled` |
| `async generate_image(prompt, provider, options)` | Génération principale |
| `async image_to_image(base64_image, prompt, provider, options)` | Transformation image |
| `get_available_providers()` | Liste providers actifs |
| `get_available_models(provider)` | Modèles disponibles |
| `check_magic_phrases(text)` | Détecte si message déclenche génération |
| `get_ui_components()` | Composants header |
| `cleanup()` | — |

---

## Fichiers de données

| Chemin | Description |
|--------|-------------|
| `data/text2img_config.json` | Configuration sauvegardée |
| `data/generated_images/{date}-{NNN}.png` | Images générées (tirets, pas underscores) |
| `data/generated_images/index.json` | Métadonnées toutes images générées |
