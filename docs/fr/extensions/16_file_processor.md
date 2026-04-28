# File Processor — Traitement des fichiers uploadés

**Sources vérifiées** : `extensions/file_processor.py`, `files/file_management.py`

---

## Rôle

Le File Processor transforme un fichier uploadé en données exploitables par l'IA principale. Il prend en charge l'extraction de texte (documents) et le traitement d'images pour injection dans le contexte multimodal.

---

## Types de fichiers supportés

| Type | Librairie | Résultat |
|---|---|---|
| PDF | `pypdf` (ou `PyPDF2` fallback) | Texte extrait page par page |
| DOCX | `python-docx` | Texte extrait |
| Images (JPG, PNG…) | OpenCV + base64 | Encodage base64 pour multimodal |

---

## Flux d'upload

`files/file_management.py` orchestre le processus :

1. L'événement NiceGUI `upload_event` déclenche `process_uploaded_file()`
2. Le fichier est sauvegardé temporairement dans `data/uploads/`
3. `extensions/file_processor.process_file()` extrait le contenu
4. Le résultat est stocké dans `active_file_data_ref` (dict mutable partagé)
5. L'IA principale reçoit le contenu lors du prochain message

---

## Enrichissement visuel (images)

Pour les images, le File Processor peut mobiliser deux modules optionnels si disponibles :

- **DepthManager** : analyse de profondeur de la scène
- **ContourAnalyzer** : détection des formes et contours

Chacun est un singleton initialisé de façon paresseuse. Si l'un est absent, le traitement continue sans lui.

---

## Stockage temporaire

Les fichiers uploadés transitent par `data/uploads/`. Ils sont préfixés `temp_{uuid}_` pour éviter les collisions entre sessions concurrentes.
