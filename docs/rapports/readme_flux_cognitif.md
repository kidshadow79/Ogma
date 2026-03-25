# Extension Flux Cognitif — Documentation Exhaustive

**Dossier** : `extensions/flux_cognitif/`
**Rôle** : Visualisation en temps réel des événements cognitifs internes d'OGMA (pensées de l'Archiviste, biographie, rêves, journal, directives, web, capacités) via un overlay NiceGUI latéral avec effet de sédimentation et filtrage multi-niveaux.

---

## Concept

Le Flux Cognitif est un observateur passif : chaque composant OGMA peut appeler `log_cognitive_event()` pour signaler une activité interne. Ces événements s'affichent dans un panneau latéral semi-transparent, du plus récent (opaque) au plus ancien (transparent), simulant la décantation naturelle des pensées.

---

## Architecture — Fichiers

| Fichier | Classe | Rôle |
|---------|--------|------|
| `__init__.py` | `FluxCognitif` | Stockage événements, filtrages, niveaux, API publique |
| `stream_ui.py` | `FluxCognitifUI` | Overlay NiceGUI, rendu, CSS, interactions |

---

## `__init__.py` — Classe `FluxCognitif` et API Publique

### Singleton global : `_flux_instance : Optional[FluxCognitif] = None`

### Classe `FluxCognitif`

**`__init__()`** — initialise :

| Attribut | Type | Défaut | Description |
|----------|------|--------|-------------|
| `events` | `list` | `[]` | Files d'événements (max 50) |
| `max_events` | `int` | `50` | Capacité maximale |
| `enabled` | `bool` | `True` | Activation globale |
| `filters` | `dict` | voir ci-dessous | Filtрес par source |
| `level` | `int` | `2` | Niveau d'affichage 1-3 |
| `_default_filters` | `dict` | — | Copie des filtres par défaut |

**Filtres par source (défauts) :**

| Source | Activée par défaut |
|--------|-------------------|
| `archiviste` | `True` |
| `biography` | `True` |
| `dream` | `True` |
| `journal` | `True` |
| `directive` | `True` |
| `web` | `False` |
| `capability` | `False` |

**Niveaux d'affichage :**

| Niveau | Nom | Contenu |
|--------|-----|---------|
| 1 | `SURFACE` | Événements basiques uniquement |
| 2 | `NORMAL` | + dialogues Archiviste |
| 3 | `DEEP` | Tout (métadonnées, prompts, réponses brutes) |

### Méthodes de la classe `FluxCognitif`

| Méthode | Paramètres | Description |
|---------|-----------|-------------|
| `log_event(source, message, metadata, event_level)` | `str, str, dict, int` | Ajoute événement, tronque à 50 si dépassé, affiche avec préfixe `▪/▸/▸▸` selon niveau |
| `get_recent_events(limit)` | `int` | N derniers événements (sans filtrage) |
| `clear_events()` | — | Vide `self.events` |
| `set_filter(source, enabled)` | `str, bool` | Toggle filtre + `_save_prefs()` |
| `set_level(level)` | `int` | Définit 1/2/3 + `_save_prefs()` |
| `get_filtered_events(limit)` | `int` | Filtre par source active ET `event.level <= self.level` |
| `_load_prefs()` | — | Lit `flux_prefs.json` — filtres et level |
| `_save_prefs()` | — | Écrit `flux_prefs.json` |

### API Publique (module-level)

| Fonction | Description |
|----------|-------------|
| `initialize_flux_cognitif()` | Crée singleton si absent, retourne instance |
| `get_flux_cognitif()` | Retourne `_flux_instance` |
| `log_cognitive_event(source, message, metadata, event_level)` | Raccourci → `_flux_instance.log_event()` |
| `is_available()` | `_flux_instance is not None` |
| `get_recent_events(limit)` | Raccourci → `_flux_instance.get_recent_events()` ou `[]` |
| `cleanup()` | Vide events, remet `_flux_instance` à `None` |

### Structure d'un événement

```python
{
    "timestamp": "HH:MM:SS",
    "source": str,        # "archiviste", "biography", "dream", etc.
    "message": str,       # Message court affiché
    "metadata": dict,     # Données brutes (prompt, réponse, JSON, etc.)
    "level": int          # 1, 2, ou 3
}
```

### Fichier de préférences

`flux_prefs.json` (chemin relatif depuis la racine OGMA) :
```json
{
    "filters": {"archiviste": true, "biography": true, ...},
    "level": 2
}
```

---

## `stream_ui.py` — Classe `FluxCognitifUI`

### Attributs

| Attribut | Description |
|----------|-------------|
| `flux` | Instance `FluxCognitif` |
| `overlay_visible` | `bool` — état visible/invisible |
| `stream_container` | `ui.column` — zone des logs |
| `overlay_element` | `ui.element` — conteneur principal |
| `level_buttons` | Liste des 3 boutons niveau |
| `filter_buttons` | `dict {source: button}` |
| `last_event_count` | Anti-doublon pour éviter les re-rendus inutiles |
| `_force_refresh` | Force refresh après toggle filtre/niveau |
| `source_icons` | `dict {source: emoji}` |

### Méthodes de création UI

| Méthode | Description |
|---------|-------------|
| `_is_overlay_valid()` | Teste `overlay_element.client` pour détecter client supprimé (après F5) |
| `create_overlay()` | Construit l'overlay complet : header titre, zone logs, footer (boutons niveau 1/2/3 + boutons filtres par source). Démarre `ui.timer(2.0, _refresh_logs)` |
| `show_overlay()` | Recrée overlay si invalide (post-F5), force `display: flex`, déclenche refresh |
| `hide_overlay()` | `display: none`, protégé contre `RuntimeError` client supprimé |
| `toggle_overlay()` | Bascule show/hide |

### Méthodes de contrôle

| Méthode | Description |
|---------|-------------|
| `_set_level(level)` | Change `flux.level`, met à jour apparence boutons `●/○`, force refresh |
| `_toggle_filter(source)` | Inverse filtre source, met à jour CSS `filter-active/filter-inactive`, force refresh |
| `_refresh_logs()` | Timer 2s : récupère `get_filtered_events(20)`, compare count, clear + redessine si changement OU `_force_refresh`, auto-scroll JS |

### Méthodes de rendu

| Méthode | Description |
|---------|-------------|
| `_get_age_class(index, total)` | Position 0→1 : `log-ancient` (<0.3), `log-old` (<0.6), `log-recent` (≥0.6) |
| `_render_log_card(event, age_class)` | Rendu HTML card : icône source, timestamp, badge niveau `NORMAL/DEEP`, message multi-lignes. Si level ≥ 2 : expansion `ui.expansion` pour métadonnées (prompt/JSON/raw_response) |
| `_inject_inset_styles()` | `ui.add_head_html()` avec tout le CSS : overlay, header, footer, log-card, level-badge, filter-btn, sédimentation, détails Phase 2/3 |

### Spécifications CSS notables

| Propriété | Valeur | Effet |
|----------|--------|-------|
| Positionnement | `fixed, top:80px, right:10px` | Overlay flottant |
| Dimensions | `200px × 70vh` | Largeur fixe, hauteur variable |
| Fond | `rgb(8,8,12)` semi-transparent | Visibilité contenu en dessous |
| Effet relief | `box-shadow: inset 8px 8px 20px rgba(0,0,0,0.6)` | Effet enfoncement |
| Animation entrée | `@keyframes slideInRight 0.3s` | Glissement depuis la droite |
| Scrollbar | 6px custom | Discret |
| Sédimentation | `opacity: 0.3 / 0.6 / 1.0` | Du plus ancien au plus récent |

### Fonctions module-level

```python
create_flux_ui(flux_instance: FluxCognitif) -> FluxCognitifUI
    # Recrée le singleton si overlay invalide (post-F5)

get_flux_ui() -> Optional[FluxCognitifUI]
    # Retourne l'instance ou None
```

---

## Utilisation depuis les extensions

Tout composant OGMA peut logger un événement cognitif :

```python
from extensions.flux_cognitif import log_cognitive_event

# Niveau 1 — événement basique (archiviste)
log_cognitive_event(
    source="archiviste",
    message="Extraction de 3 souvenirs pertinents",
    event_level=1
)

# Niveau 2 — dialogue interne
log_cognitive_event(
    source="dream",
    message="Génération rêve en cours...",
    metadata={"fuel_sources": 4, "tokens_so_far": 450},
    event_level=2
)

# Niveau 3 — données brutes (prompt, réponse)
log_cognitive_event(
    source="biography",
    message="Sélection Archiviste : 3 souvenirs choisis",
    metadata={"prompt": full_prompt, "raw_response": full_response},
    event_level=3
)
```

---

## Données de préférences

| Fichier | Chemin | Contenu |
|---------|--------|---------|
| `flux_prefs.json` | Racine OGMA | `{filters: {source: bool}, level: int}` |

Le fichier est créé automatiquement à la première modification de filtre ou de niveau.
