# API Text2Image Extension - Documentation Extraite

**Version**: 1.0.0  
**Fichiers analysés**: `__init__.py`, `text2img_manager.py`  
**Date d'extraction**: 1762345842.5030215  

## Vue d'ensemble

Extension de génération d'images via IA à partir de prompts textuels.

**Backends supportés**:
- Pollinations.AI (Stable Diffusion, Flux) - Gratuit et illimité
- Perchance.org (legacy)

**Total API**: 8 (Fonctions: 3, Méthodes: 5)

---

## 1. API Extension (Niveau Module)

Fonctions publiques dans `extensions/text2img/__init__.py`

### `initialize_text2img()`

```python
def initialize_text2img(settings_manager)
```

**Documentation**:
```
Initialise l'extension Text2Image

Args:
    settings_manager: Instance de SettingsManager d'OGMA

Returns:
    bool: True si l'initialisation a réussi
```

---

### `get_text2img_manager()`

```python
def get_text2img_manager()
```

**Documentation**:
```
Récupère l'instance du manager Text2Image

Returns:
    Text2ImageManager: L'instance du manager, ou None si non initialisé
```

---

### `is_available()`

```python
def is_available()
```

**Documentation**:
```
Vérifie si l'extension est disponible

Returns:
    bool: True si l'extension est initialisée et prête
```

---

## 2. API Manager (Text2ImageManager)

Méthodes publiques de la classe `Text2ImageManager`

### `initialize_backend()`

```python
def initialize_backend() -> bool
```

**Documentation**:
```
Initialise le backend de génération (actuellement Perchance HTTP)

Returns:
    bool: True si l'initialisation a réussi
```

---

### `generate_image()`

```python
async def generate_image(prompt) -> tuple[Optional[bytes], Optional[str], Optional[Dict]]
```

**Documentation**:
```
Génère une image à partir d'un prompt

Args:
    prompt: Description de l'image
    **kwargs: Paramètres additionnels (width, height, etc.)

Returns:
    tuple: (image_bytes, error_message, metadata)
        - Si succès: (bytes, None, metadata)
        - Si échec: (None, error_message, None)
```

---

### `save_image()`

```python
def save_image(image_bytes, metadata) -> tuple[Optional[Path], Optional[str]]
```

**Documentation**:
```
Sauvegarde une image générée avec ses métadonnées

Args:
    image_bytes: Données binaires de l'image
    metadata: Métadonnées de génération

Returns:
    tuple: (chemin_fichier, error_message)
        - Si succès: (Path, None)
        - Si échec: (None, error_message)
```

---

### `get_history()`

```python
def get_history(limit) -> List[Dict[str, Any]]
```

**Documentation**:
```
Récupère l'historique des générations

Args:
    limit: Nombre maximum de résultats (None = tous)

Returns:
    List[Dict]: Liste des métadonnées de génération
```

---

### `get_backend_info()`

```python
def get_backend_info() -> Optional[Dict[str, Any]]
```

**Documentation**:
```
Retourne les informations sur le backend actif

Returns:
    dict: Informations du backend, ou None si non disponible
```

---

## 3. Résumé de l'API

### Fonctions Extension (3)
| Fonction | Args | Retour | Async |
|----------|------|--------|-------|
| `initialize_text2img` | 1 | `None` | ❌ |
| `get_text2img_manager` | 0 | `None` | ❌ |
| `is_available` | 0 | `None` | ❌ |

### Méthodes Manager (5)
| Méthode | Args | Retour | Async |
|---------|------|--------|-------|
| `initialize_backend` | 0 | `bool` | ❌ |
| `generate_image` | 1 | `tuple[Optional[bytes], Optional[str], Optional[Dict]]` | ✅ |
| `save_image` | 2 | `tuple[Optional[Path], Optional[str]]` | ❌ |
| `get_history` | 1 | `List[Dict[str, Any]]` | ❌ |
| `get_backend_info` | 0 | `Optional[Dict[str, Any]]` | ❌ |

## 4. Workflow de Génération

```python
# 1. Initialiser l'extension
initialize_text2img(settings_manager)  # -> bool

# 2. Récupérer le manager
manager = get_text2img_manager()  # -> Text2ImageManager | None

# 3. Générer une image
image_bytes, error, metadata = await manager.generate_image("fantasy landscape")

# 4. Sauvegarder (optionnel)
if image_bytes:
    filepath, error = manager.save_image(image_bytes, metadata)

# 5. Consulter l'historique
history = manager.get_history(limit=10)
```

## 5. Patterns de Test

- **Fixtures**: `mock_settings_manager`, `temp_images_dir`, `text2img_manager`
- **Isolation**: tmp_path pour dossier generated_images
- **Async**: AsyncMock pour backend.generate_image()
- **I/O**: Tests end-to-end avec fichiers réels (isolation tmp_path)
- **Cleanup**: autouse fixture pour reset singleton global

