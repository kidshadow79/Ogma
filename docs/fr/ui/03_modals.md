# Modales et panneaux de configuration

**Sources vérifiées** : `ogma_modals.py`, `ogma_config_ui.py`

---

## Architecture des modales

OGMA utilise le système de dialogue NiceGUI (`ui.dialog()`) pour ses fenêtres modales. Les modales sont créées à la volée au moment de l'ouverture (pas pré-instanciées), sauf dans les cas où une référence stable est nécessaire.

Toutes les modales passent par des fonctions centralisées dans `ogma_modals.py`. Les autres modules (header, extensions) appellent ces fonctions via des alias dynamiques pour éviter les imports circulaires.

---

## Modales disponibles

| Modale | Déclencheur | Contenu |
|---|---|---|
| Configuration modèles | Bouton header | Sélection provider, modèle, paramètres pour chaque contrôleur |
| Organic Planner | Bouton header | Liste des événements agenda, ajout/suppression |
| Mémoires | Panneau admin | Affichage, recherche, suppression souvenirs |
| Conversation éditée | Sidebar | Édition titre et résumé d'une conversation |
| Upload fichier | Bouton saisie | Zone de dépôt de fichier |

---

## Pattern d'accès aux globals

`ogma_modals.py` ne peut pas importer directement depuis `ogma_ng.py` (import circulaire). Il accède aux gestionnaires via deux helpers :

- `_get_settings_manager()` — récupère `_ensure_settings_manager()` depuis `sys.modules['ogma_ng']`
- `_get_global_var(var_name)` — accès générique aux variables globales d'`ogma_ng`

Ce pattern est identique à celui d'`ogma_headers.py`.

---

## Configuration des contrôleurs IA

Le panneau de configuration des modèles (`ogma_config_ui.py`) permet de configurer indépendamment les trois contrôleurs (Chat, Archiviste, Embeddings). Pour chaque contrôleur :

- Sélection du type de backend (API distante ou local)
- Sélection du provider / URL
- Saisie de la clé API
- Sélection du modèle (liste récupérée dynamiquement via `list_models()`)
- Paramètres avancés (température, tokens max, longueur contexte)
