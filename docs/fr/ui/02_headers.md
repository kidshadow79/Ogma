# Header et indicateurs de statut

**Source vérifiée** : `ogma_headers.py`

---

## Rôle

Le header est la zone de contrôle permanent de l'interface. Il affiche l'état des systèmes critiques et donne accès aux extensions actives.

---

## Indicateurs de statut IA

Trois indicateurs visuels reflètent l'état des contrôleurs IA :

| Indicateur | Contrôleur surveillé |
|---|---|
| Chat | IA principale (conversationnelle) |
| Archiviste | IA analytique (mémoire/enrichissement) |
| Embeddings | Contrôleur de vectorisation |

Chaque indicateur affiche le backend configuré et passe au rouge en cas d'indisponibilité.

---

## Boutons d'extension

Les extensions s'enregistrent dans le header via leur méthode `get_ui_components()`. Le header reçoit un composant bouton qu'il intègre à sa disposition. Cette intégration est dynamique : un bouton n'apparaît que si l'extension est chargée et disponible.

Exemples de boutons typiques :
- Bouton Cognitive Mirror (introspection)
- Bouton Dream Engine (rêve)
- Bouton Journal de bord
- Bouton Organic Planner

---

## Accès aux globals

`ogma_headers.py` n'a pas accès direct aux variables globales d'`ogma_ng.py`. Il utilise le helper `_get_global_var(var_name)` qui passe par `sys.modules['ogma_ng']` pour lire les variables au moment de l'appel. Ce pattern évite les imports circulaires.

De même, les appels à des fonctions d'`ogma_ng.py` passent par `_get_ogma_ng_function(func_name)`, récupéré dynamiquement depuis `sys.modules`.

---

## Sélecteur de langue

Un bouton dans le header permet de basculer entre FR et EN. Il appelle `set_lang()` depuis `utils/i18n.py` puis force un rechargement de la page via `ui.navigate.reload()` pour que toutes les chaînes de traduction soient mises à jour.
