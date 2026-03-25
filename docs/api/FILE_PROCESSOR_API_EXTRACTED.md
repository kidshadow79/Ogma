# API File Processor Extension - Documentation Extraite

**Version**: 1.0.0  
**Fichier analysé**: `extensions/file_processor.py`  
**Date d'extraction**: 2025-11-05  

## Vue d'ensemble

Module standalone de traitement de fichiers uploadés pour OGMA.

**Formats supportés**:
- **Texte**: TXT, MD, JSON
- **Documents**: PDF, DOCX
- **Images**: JPG, JPEG, PNG, WEBP, GIF

**Total API**: 1 fonction publique

---

## API Publique

### `process_file()`

```python
def process_file(file_path: Path) -> Optional[Dict[str, Any]]
```

**Documentation**:
```
Analyse un fichier uploadé et retourne un dictionnaire structuré 
avec son type et son contenu (texte ou data Base64 pour les images).

Args:
    file_path (Path): Chemin du fichier à traiter

Returns:
    Optional[Dict]: 
        - None si fichier invalide/inexistant
        - Pour fichiers texte:
            {
                'type': 'text',
                'content': str,  # Contenu extrait
                'filename': str
            }
        - Pour images:
            {
                'type': 'image',
                'mime_type': str,  # ex: 'image/jpeg'
                'data': str,      # Base64 encoded
                'filename': str
            }
        - Pour erreurs/non-supportés:
            {
                'type': 'text',
                'content': '[Erreur...]',
                'filename': str
            }

Side Effects:
    - Supprime le fichier temporaire après traitement
```

---

## Workflow de Traitement

```python
# 1. Upload fichier (via UI NiceGUI)
upload_event = await ui.upload(...)

# 2. Sauvegarde temporaire
temp_path = Path(f"data/uploads/{upload_event.name}")
temp_path.write_bytes(upload_event.content.read())

# 3. Traitement
from extensions.file_processor import process_file
file_data = process_file(temp_path)

# 4. Utilisation
if file_data:
    if file_data['type'] == 'text':
        # Injecter contenu dans contexte conversation
        context += f"\n\nContenu de {file_data['filename']}:\n{file_data['content']}"
    elif file_data['type'] == 'image':
        # Envoyer à modèle vision (ex: GPT-4V, LLaVA)
        vision_prompt = f"Analyse cette image {file_data['filename']}"
        # Utiliser file_data['data'] et file_data['mime_type']
```

---

## Patterns de Test

### Fixtures
- `temp_upload_dir(tmp_path)`: Dossier temporaire isolated
- `sample_txt_file()`: Fichier TXT de test
- `sample_pdf_file()`: PDF minimal (via reportlab ou bytes littéraux)
- `sample_docx_file()`: DOCX minimal (via python-docx)
- `sample_image_file()`: PNG minimal (header valide)

### Tests Requis
1. **Fichiers Texte** (3 tests):
   - TXT: lecture encodage UTF-8
   - MD: lecture markdown
   - JSON: lecture JSON

2. **Documents** (2 tests):
   - PDF: extraction multi-pages (pypdf/PyPDF2)
   - DOCX: extraction paragraphes

3. **Images** (1 test):
   - PNG/JPG: encodage Base64 + MIME type

4. **Edge Cases** (4 tests):
   - Fichier inexistant → None
   - Extension non supportée → message erreur
   - Erreur lecture → message erreur
   - Cleanup fichier temporaire

### Assertions Clés
```python
# Succès texte
assert result is not None
assert result['type'] == 'text'
assert 'content' in result
assert result['filename'] == original_name

# Succès image
assert result['type'] == 'image'
assert result['mime_type'] == 'image/png'
assert isinstance(result['data'], str)  # Base64

# Cleanup
assert not file_path.exists()  # Fichier supprimé
```

---

## Dépendances

- `pypdf` ou `PyPDF2` (PDF)
- `python-docx` (DOCX)
- `mimetypes` (standard library)
- `base64` (standard library)
- `pathlib.Path` (standard library)

---

## Résumé de Couverture Attendue

**Total tests**: 10  
**Suites**:
- Fichiers Texte (3): TXT, MD, JSON
- Documents (2): PDF, DOCX
- Images (1): PNG/JPG Base64
- Edge Cases (4): None, unsupported, error, cleanup

**Durée estimée**: <1s (I/O minimal avec petits fichiers)
