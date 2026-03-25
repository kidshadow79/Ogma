# UI Components API - OGMA

**Date**: 2025-11-05  
**Phase**: Phase 5 E2 - UI Components  
**Objectif**: Documentation complète des composants d'interface utilisateur NiceGUI

---

## 📊 Vue d'Ensemble

Les composants UI d'OGMA sont répartis dans 4 modules principaux :

1. **utils/formatting_utils.py**: Fonctions de formatage (dates, tailles, fichiers)
2. **ogma_displays.py**: Affichages dynamiques (LEDs, jauges, diagnostics)
3. **ogma_headers.py**: En-têtes et indicateurs de statut IA
4. **ogma_modals.py**: Dialogs modaux (paramètres, mémoire, conversations)

---

## 🛠️ Module 1: Formatting Utils

### `format_size(size_bytes: int) -> str`

Formate une taille en octets en format lisible humain.

**Paramètres**:
- `size_bytes` (int): Taille en octets

**Retour**:
- `str`: Taille formatée (ex: "1.5 MB", "320 KB", "45 B")

**Logique**:
```python
if size_bytes == 0: return "0 B"
elif size_bytes < 1024: return f"{size_bytes} B"
elif size_bytes < 1024²: return f"{size_bytes/1024:.1f} KB"
elif size_bytes < 1024³: return f"{size_bytes/1024²:.1f} MB"
else: return f"{size_bytes/1024³:.2f} GB"
```

**Exemples**:
```python
format_size(0)          # "0 B"
format_size(1024)       # "1.0 KB"
format_size(1048576)    # "1.0 MB"
format_size(1073741824) # "1.0 GB"
```

---

### `format_datetime(datetime_str: str) -> str`

Formate une date ISO en format français lisible.

**Paramètres**:
- `datetime_str` (str): Date ISO (ex: "2025-11-01T14:30:00")

**Retour**:
- `str`: Date formatée (ex: "01/11/2025 à 14:30")

**Processus**:
1. Parse ISO format via `datetime.fromisoformat()`
2. Formate avec `strftime("%d/%m/%Y à %H:%M")`
3. Fallback sur string original si erreur

**Exemples**:
```python
format_datetime("2025-11-01T14:30:00")  # "01/11/2025 à 14:30"
format_datetime("invalid")              # "invalid" (fallback)
```

---

### `truncate_filename(filename: str, max_length: int = 15) -> str`

Tronque un nom de fichier pour l'affichage.

**Paramètres**:
- `filename` (str): Nom complet du fichier
- `max_length` (int): Longueur max (défaut 15)

**Retour**:
- `str`: Nom tronqué avec "..." si nécessaire

**Logique**:
- Si `len(filename) <= max_length`: retourne tel quel
- Sinon: `filename[:max_length-5] + "..." + filename[-4:]` (préserve extension)

**Exemples**:
```python
truncate_filename("document.pdf", 10)                    # "document.pdf" (< 10)
truncate_filename("document_tres_long_nom.pdf", 10)     # "docume....pdf"
truncate_filename("rapport_final_version_3.docx", 20)   # "rapport_final...docx"
```

---

### `get_file_icon(filename: str) -> str`

Retourne l'icône emoji pour un type de fichier.

**Paramètres**:
- `filename` (str): Nom du fichier

**Retour**:
- `str`: Emoji représentant le type

**Mapping Extensions**:
- **Images**: `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.svg` → 🖼️
- **PDF**: `.pdf` → 📄
- **Texte**: `.txt`, `.md` → 📝
- **Documents**: `.doc`, `.docx` → 📰
- **Autre**: → 📎

**Exemples**:
```python
get_file_icon("image.png")      # "🖼️"
get_file_icon("document.pdf")   # "📄"
get_file_icon("note.txt")       # "📝"
get_file_icon("rapport.docx")   # "📰"
get_file_icon("archive.zip")    # "📎"
```

---

## 🎨 Module 2: Display Components

### `_status_dot(initial: str = '#dc2626') -> ui.Element`

Crée un indicateur de statut coloré (point LED).

**Paramètres**:
- `initial` (str): Couleur hexa initiale (défaut rouge `#dc2626`)

**Retour**:
- `ui.Element`: Div NiceGUI stylisé en cercle coloré

**Style CSS**:
```css
width: 12px
height: 12px
border-radius: 50%
background: {initial}
display: inline-block
margin-right: 4px
```

**Classe**: `'status-dot'`

**Usage**:
```python
# Rouge (inactif)
dot_inactive = _status_dot('#dc2626')

# Vert (actif)
dot_active = _status_dot('#22c55e')

# Jaune (warning)
dot_warning = _status_dot('#eab308')
```

---

### `_update_led_gauges(data: dict) -> None`

Met à jour les jauges LED du panneau métacognitif Archi Sensor.

**Paramètres**:
- `data` (dict): Mapping `{état: niveau}` avec niveaux 1-6

**États Supportés**:
- `autocensure`: Auto-censure (6 niveaux)
- `saturation`: Saturation cognitive
- `stimulation`: Stimulation intellectuelle
- `affinity`: Affinité conversationnelle (7 niveaux affichés 1-6)
- `disorientation`: Désorientation
- `freedom`: Liberté d'expression (alias `tension_liberte`)
- `alignment`: Alignement contraintes (alias `alignement_contraintes`)

**Processus**:
1. Mapping états → IDs jauges (ex: `affinity` → `affinity-gauge`)
2. Pour chaque état détecté:
   - Normalise niveau (1-6)
   - Pour chaque LED (1-6):
     - Active si `led_level <= level`
     - Pulse si `led_level == level` et `level > 1`
3. Injection JavaScript via `ui.run_javascript()`

**Format LED ID**: `{gauge_id}-led-{led_level}`

**Exemple**:
```python
data = {
    'affinity': 4,      # Active LEDs 1-4, pulse LED 4
    'autocensure': 2,   # Active LEDs 1-2, pulse LED 2
    'freedom': 6        # Active toutes LEDs 1-6, pulse LED 6
}
_update_led_gauges(data)
```

**Couleurs LEDs** (selon jauge):
- Affinité: Rose `#ff8cc8`
- Autocensure: Violet `#9333ea`
- Freedom: Cyan `#06b6d4`
- Autres: Variables selon configuration

---

## 📋 Module 3: Headers & Status

### `_header() -> None`

Crée l'en-tête principal OGMA avec indicateurs de statut IA.

**Composants Créés**:
1. **Container principal**: `app-header` class
2. **3 Indicateurs IA**:
   - **IA PRINCIPALE** (Chat): Dot + label + modèle
   - **ARCHIVISTE**: Dot + label + modèle
   - **IA EMBED**: Dot + label + modèle

**Variables Globales Créées**:
```python
_header_container: ui.Element  # Container titre
_ia_status_indicators: {
    'chat_dot': ui.Element,
    'chat_model': ui.Label,
    'archiviste_dot': ui.Element,
    'archiviste_model': ui.Label,
    'embeddings_dot': ui.Element,
    'embeddings_model': ui.Label
}
```

**Layout**:
```
┌─────────────────────────────────────────┐
│ [●] IA PRINCIPALE    [●] ARCHIVISTE    │
│     Modèle: GPT-4        Modèle: O1    │
│                                         │
│              [●] IA EMBED               │
│              Modèle: text-embed-3      │
└─────────────────────────────────────────┘
```

**Positionnement**: Indicateurs centrés via `position: absolute; left: 50%; transform: translateX(-50%)`

**Intégration Extensions**: Appelle `_archi_sensor_modal()` et `get_perception_ui()` si disponibles

---

### `_get_ogma_ng_function(func_name: str) -> Optional[Callable]`

Helper pour récupérer une fonction d'`ogma_ng`.

**Paramètres**:
- `func_name` (str): Nom de la fonction

**Retour**:
- `Optional[Callable]`: Fonction si trouvée, `None` sinon

**Processus**:
1. Récupère module `ogma_ng` via `sys.modules`
2. Vérifie `hasattr(ogma_ng, func_name)`
3. Retourne `getattr(ogma_ng, func_name)` ou `None`

---

### `_get_global_var(var_name: str, default=None) -> Any`

Helper pour accéder aux variables globales d'`ogma_ng`.

**Paramètres**:
- `var_name` (str): Nom de la variable
- `default` (Any): Valeur par défaut si non trouvée

**Retour**:
- `Any`: Valeur de la variable ou `default`

**Usage**:
```python
chat_controller = _get_global_var('_chat_controller')
settings = _get_global_var('_settings', {})
```

---

### `_get_current_conversation_id() -> str`

Récupère l'ID de la conversation active.

**Retour**:
- `str`: ID conversation (ex: `"2025-11-05_14-30-00_abcd"`) ou ID temporaire

**Processus**:
1. Tente de récupérer `_current_conversation_id` global
2. Si absent: génère ID temporaire `f"temp_conv_{uuid4().hex[:8]}"`
3. Si erreur: génère ID erreur `f"error_conv_{uuid4().hex[:8]}"`

**Exemples**:
```python
id1 = _get_current_conversation_id()  # "2025-11-05_14-30-00_abcd"
id2 = _get_current_conversation_id()  # "temp_conv_8f3a21bc" (si aucune active)
```

---

## 🪟 Module 4: Modal Dialogs

### `_notify_safe(message: str, type_msg: str = 'info') -> None`

Notification sécurisée avec gestion erreurs.

**Paramètres**:
- `message` (str): Message à afficher
- `type_msg` (str): Type de notification

**Types Supportés**:
- `'info'`: Information (bleu)
- `'positive'`: Succès (vert)
- `'negative'`: Erreur (rouge)
- `'warning'`: Avertissement (jaune)
- `'ongoing'`: En cours (bleu avec spinner)

**Processus**:
1. Tente `ui.notify(message, type=type_msg)`
2. Si erreur: affiche message console + fallback print

**Exemple**:
```python
_notify_safe("Configuration sauvegardée", 'positive')
_notify_safe("Erreur de connexion", 'negative')
_notify_safe("Traitement en cours...", 'ongoing')
```

---

### `_ensure_settings_manager() -> Optional[SettingsManager]`

Récupère/initialise le SettingsManager global.

**Retour**:
- `Optional[SettingsManager]`: Instance ou `None` si erreur

**Pattern Lazy Init**: Vérifie `_settings_manager` global, crée si absent

---

### `_ensure_memory_manager() -> Optional[MemoryManager]`

Récupère/initialise le MemoryManager global.

**Retour**:
- `Optional[MemoryManager]`: Instance ou `None` si erreur

**Pattern Lazy Init**: Vérifie `_memory_manager` global, crée si absent

---

### `_ensure_backends() -> dict`

Récupère les dictionnaires de gestionnaires backend.

**Retour**:
```python
{
    'api_managers': {...},     # APIManager par section
    'ollama_managers': {...},  # OllamaManager par section
    'gguf_managers': {...}     # GGUFManager par section
}
```

**Usage**: Utilisé par modals de configuration IA

---

## 🎯 Tests Prévus

### Formatting Utils (4 tests)
1. **test_format_size**: Tailles 0B, KB, MB, GB
2. **test_format_datetime**: ISO → FR, fallback invalide
3. **test_truncate_filename**: Court, long, préservation extension
4. **test_get_file_icon**: Mapping tous types fichiers

### Display Components (5 tests)
1. **test_status_dot**: Création avec couleurs variées
2. **test_update_led_gauges**: Mise à jour multi-états
3. **test_led_activation_logic**: LEDs actives selon niveau
4. **test_led_pulse**: Pulse uniquement LED niveau actuel
5. **test_gauge_mapping**: Mapping états → IDs jauges

### Header Components (4 tests)
1. **test_header_creation**: Structure header complète
2. **test_ia_status_indicators**: 3 indicateurs créés
3. **test_get_ogma_ng_function**: Récupération fonctions
4. **test_get_global_var**: Accès variables avec default

### Modal Helpers (4 tests)
1. **test_notify_safe**: Types notifications variés
2. **test_ensure_settings_manager**: Lazy init
3. **test_ensure_memory_manager**: Lazy init
4. **test_ensure_backends**: Structure dict backends

**Total Estimé**: **17 tests** (4+5+4+4)

---

## 🔧 Dépendances

### Python Modules
- `nicegui`: Framework UI (ui.element, ui.label, ui.notify, ui.run_javascript)
- `datetime`: Parsing dates ISO
- `pathlib`: Manipulation chemins
- `typing`: Type hints (Optional, Any, Callable)

### OGMA Modules
- `ogma_ng`: Variables globales, fonctions principales
- `SettingsManager`: Configuration (settings.json)
- `MemoryManager`: Mémoire SQLite+FAISS

### NiceGUI Components
- `ui.element()`: Divs stylisés
- `ui.label()`: Labels texte
- `ui.notify()`: Notifications toast
- `ui.run_javascript()`: Injection JS dynamique

---

## 📚 Patterns Architecturaux

### 1. Helper Functions Pattern
Helpers `_get_*` pour isoler accès globaux (testabilité).

### 2. Lazy Initialization
`_ensure_*` vérifient existence avant création (singleton-like).

### 3. Safe UI Operations
Try/except autour `ui.notify()` avec fallback console.

### 4. JavaScript Injection
`ui.run_javascript()` pour manipulation DOM dynamique (LEDs).

### 5. CSS Inline Styling
Styles via `.style()` pour composants isolés (no CSS global).

---

**Couverture Estimée**: 100% des fonctions publiques (17 fonctions = 17+ tests)
