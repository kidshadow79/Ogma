# Uploads et gestion de fichiers

**Sources vérifiées** : `files/file_management.py`, `extensions/file_processor.py`

---

## Flux d'upload

L'upload de fichier suit un pipeline en 4 étapes :

1. **Événement NiceGUI** : l'utilisateur sélectionne un fichier via le composant upload. L'événement `upload_event` est émis avec le contenu et le nom du fichier.

2. **Sauvegarde temporaire** : `process_uploaded_file()` sauvegarde le fichier dans `data/uploads/` avec un préfixe `temp_{uuid}_` pour éviter les collisions.

3. **Extraction contenu** : `extensions/file_processor.process_file()` extrait le texte (PDF, DOCX) ou encode l'image en base64.

4. **Activation** : les données extraites sont stockées dans `active_file_data_ref` — un dict mutable partagé. Le fichier est alors "actif" pour la prochaine requête IA.

---

## Formats supportés

| Format | Méthode d'extraction |
|---|---|
| PDF | `pypdf` (fallback `PyPDF2`) — texte page par page |
| DOCX | `python-docx` — texte de tous les paragraphes |
| Images | OpenCV → encodage JPEG base64 |

---

## Fonctions utilitaires UI

`files/file_management.py` contient également des helpers d'affichage :
- `update_header_display()` — rafraîchit l'en-tête avec l'état du fichier actif
- Icônes par type de fichier et troncature de noms longs (via `utils/formatting_utils.py`)

---

## Nettoyage

Les fichiers temporaires dans `data/uploads/` ne sont pas supprimés automatiquement après traitement. Un nettoyage manuel ou via l'interface peut être nécessaire pour libérer de l'espace.
