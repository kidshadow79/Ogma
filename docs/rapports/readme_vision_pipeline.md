# Pipeline Vision — Documentation Exhaustive

**Fichiers** : `ogma_perception.py`, `extensions/file_processor/`
**Rôle** : Capture vidéo en temps réel (webcam → analyse IA), pipeline traitement d'images (profondeur, contours, vision avancée), et upload de fichiers utilisateur.

---

## Architecture

```
Webcam / Upload fichier
    ↓
PerceptionAgent (capture + analyse live)
    ↓
FileProcessor (traitement images avancé)
      ├── DepthManager      (estimation profondeur Depth-Anything-V2)
      └── ContourAnalyzer   (détection contours Canny/Sobel/Laplacian/Adaptive)
          ↓
Résultats injectés dans contexte IA principale
```

---

## `ogma_perception.py` — Classes

### `PerceptionAgent`

**Rôle** : Capture flux webcam et génère des analyses IA périodiques.

#### Modes de capture

| Mode | Résolution | FPS | Usage |
|------|-----------|-----|-------|
| `"chirurgical"` | 1920×1080 → 720p | 15 | Analyse détaillée, qualité max |
| `"normal"` | 1280×720 | 30 | Temps réel standard |
| `"rapide"` | 640×480 | 30 | Performance sur machines lentes |

#### `create_motion_sequence()` — 20+ layouts

Génère une séquence d'images pour analyse temporelle IA :
- `"grid_2x2"` — 4 frames en grille
- `"grid_3x3"` — 9 frames en grille
- `"horizontal_strip"` — frames en ligne
- `"vertical_strip"` — frames en colonne
- `"focus_center"` — 1 grand centre + 4 coins
- `"timeline"` — avec horodatages
- `"before_after"` — 2 frames comparaison
- ... 13 autres layouts

Résultat : image composite PIL sauvegardée temporairement, encodée base64 pour l'API vision.

#### Initialisation

**`__init__(chat_controller, settings_manager)`**

| Attribut | Description |
|----------|-------------|
| `_cap` | `cv2.VideoCapture` instance |
| `_capture_thread` | Thread daemon de capture |
| `_analysis_interval` | Secondes entre chaque analyse IA |
| `_current_frame` | Frame courante (numpy array) |
| `_is_running` | `bool` |
| `_mode` | Mode capture actif |
| `_frames_buffer` | Deque max 30 frames (pour motion) |

#### Méthodes

| Méthode | Description |
|---------|-------------|
| `start(mode)` | Ouvre capture, démarre thread analyse |
| `stop()` | Libère `cv2.VideoCapture`, stoppe thread |
| `capture_snapshot()` | Capture frame actuelle → bytes JPEG |
| `analyze_current_frame()` | Encode frame → base64 → appel IA vision |
| `create_motion_sequence(layout, n_frames, interval)` | Génère composite multi-frames |
| `get_frame_base64()` | Frame courante encodée base64 PNG |
| `set_analysis_callback(callback)` | Callback appelé à chaque résultat d'analyse |

#### Thread de capture

Boucle :
1. `_cap.read()` → frame
2. `cv2.resize()` selon mode
3. Push dans `_frames_buffer`
4. Si `time.time() - _last_analysis > _analysis_interval` → `analyze_current_frame()`

---

### `PerceptionUI`

**Rôle** : Interface NiceGUI pour la perception (caméras, settings, preview).

#### `detect_available_cameras()` → `list[dict]`

Stratégie multi-backend (Windows) :
1. `cv2.CAP_DSHOW` (Direct Show) — pour webcams natives
2. `cv2.CAP_MSMF` (Media Foundation) — pour OBS Virtual Camera, etc.
3. Indices 0-9 testés pour chaque backend
4. Dédoublonnage par index

Retourne `[{index, name, backend, width, height, fps}]`

#### `_notify_tts_perception_state(active)`

Informe `tts_perception_manager.py` de l'état actif/inactif de la perception.  
Si actif → peut activer/désactiver TTS pendant analyse (éviter feedback audio).

#### Méthodes UI

| Méthode | Description |
|---------|-------------|
| `render_perception_panel(container)` | Panel NiceGUI : sélection caméra, mode, preview |
| `toggle_perception(mode)` | Démarre/arrête `PerceptionAgent` |
| `update_preview()` | Rafraîchit image preview (timer NiceGUI 500ms) |
| `render_analysis_result(text)` | Affiche dernière analyse dans panel |

---

## `extensions/file_processor/`

**Rôle** : Traitement des fichiers uploadés par l'utilisateur — images standards et images avec analyse avancée (profondeur + contours).

### Fichiers

| Fichier | Classe | Rôle |
|---------|--------|------|
| `__init__.py` | — | API publique |
| `file_processor.py` | `FileProcessor` | Orchestrateur upload + processing |
| `depth_manager.py` | `DepthManager` | Estimation profondeur |
| `contour_analyzer.py` | `ContourAnalyzer` | Détection contours |

---

## `depth_manager.py` — Classe `DepthManager`

### Modèle utilisé

**`Depth-Anything-V2-Small-hf`** (Hugging Face)
- Taille : ~25M paramètres (Small)
- Précision équilibrée vitesse/qualité

### `analyze_depth(image_path)` → `ImageData`

1. Charge image PIL
2. `pipeline("depth-estimation", model="depth-anything/Depth-Anything-V2-Small-hf")`
3. Prédit carte de profondeur (grayscale float32)
4. **Visualisation** : applique `cv2.COLORMAP_INFERNO` (chaud = proche, froid = loin)
5. **Grille 8×8** : divise carte en 64 zones, calcule profondeur moyenne par zone
6. Génère description textuelle : `"Zone centrale : très proche (0.12m estimé), bords droits : lointain..."`
7. Sauvegarde image colorisée dans `data/uploads/depth_{filename}.png`
8. Retourne `ImageData(depth_map_path, grid_analysis_text, raw_values)`

---

## `contour_analyzer.py` — Classe `ContourAnalyzer`

### 4 méthodes de détection

| Méthode | Algorithme | Usage |
|---------|-----------|-------|
| `"canny"` | Canny Edge Detection (défaut) | Contours nets, peu de bruit |
| `"sobel"` | Sobel gradient | Contours directionnels |
| `"laplacian"` | Laplacian of Gaussian | Détails fins |
| `"adaptive"` | Adaptive threshold + Canny | Scènes à éclairage variable |

### `analyze_contours(image_path, method)` → `ImageData`

1. Charge image → conversion grayscale
2. Applique algorithme détection
3. `cv2.findContours()` → liste contours
4. Filtre petits contours (aire < 100 px²)
5. Classifie contours : `"dominant"` (> 5000px²), `"moyen"`, `"petit"`
6. Génère image **side-by-side** : original | contours colorés (`cv2.drawContours()`)
7. Génère description : `"{N} contours détectés : {M} dominants, {P} moyens..."`
8. Sauvegarde `data/uploads/contours_{filename}.png`
9. Retourne `ImageData(contours_path, analysis_text, contour_list)`

---

## `file_processor.py` — Classe `FileProcessor`

### Pipeline 3 cas (vision avancée)

Selon ce qui est disponible et demandé par l'utilisateur :

| Cas | Description | Résultat |
|-----|-------------|---------|
| **Cas 1** : Depth + Contour | Les deux analyses | 3 images : original + depth + contours + descriptions |
| **Cas 2** : Depth seul | Seulement profondeur | 2 images : original + depth colorisé |
| **Cas 3** : Contour seul | Seulement contours | 2 images : original + side-by-side |

### Préfixes sauvegardes

Toutes les images générées ont des préfixes distinctifs :
- `depth_` — cartes de profondeur
- `contours_` — analyses de contours
- `combined_` — exports combinés

### `async process_file(filepath, analysis_type, options)` → `ProcessResult`

1. Vérifie type fichier (image: jpg/png/webp/gif/bmp, doc: pdf/txt/...)
2. Si image → détecte si `"advanced_vision"` requis
3. Si `"advanced_vision"` ET modèle disponible → `_process_with_depth_contour(filepath, options)`
4. Sinon → `_process_standard_image(filepath)` → encode base64 direct
5. Si doc texte → extrait contenu texte brut
6. Retourne `ProcessResult(content_type, base64_image, text_content, analysis_images, description)`

### `_process_with_depth_contour(image_path, options)` → `ProcessResult`

```python
results = {}
if options.get("depth", True):
    results["depth"] = await depth_manager.analyze_depth(image_path)
if options.get("contours", True):
    results["contours"] = await contour_analyzer.analyze_contours(image_path, method)
# Combine descriptions
combined_desc = f"Analyse profondeur: {results['depth'].analysis}\n" \
                f"Analyse contours: {results['contours'].analysis}"
# Encode toutes les images en base64 pour l'API vision
images_b64 = [encode_b64(image_path), ...]
return ProcessResult(..., analysis_images=images_b64, description=combined_desc)
```

---

## Intégration dans `ogma_ng.py`

**Upload handler** :
1. Utilisateur uploade fichier via `ui.upload()`
2. `FileProcessor.process_file(temp_path, analysis_type)`
3. Si images → injectées dans `messages` comme `{type: "image_url", data: base64}`
4. `PerceptionAgent` (si actif) → frame insérée automatiquement en contexte toutes les N secondes

**Perception live** :
1. Bouton `👁️` dans header → `PerceptionUI.toggle_perception()`
2. Analyse en background → résultat injecté comme message système discret

---

## Fichiers de données

| Chemin | Description |
|--------|-------------|
| `data/uploads/` | Fichiers uploadés temporaires |
| `data/uploads/depth_*.png` | Cartes de profondeur générées |
| `data/uploads/contours_*.png` | Images analyse contours |
| `models/depth-anything/` | Modèle Depth-Anything-V2 caché |
