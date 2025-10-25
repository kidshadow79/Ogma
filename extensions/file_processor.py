# extensions/file_processor.py

import os
from pathlib import Path
import docx
try:
    import pypdf
except ImportError:
    import PyPDF2 as pypdf
import base64
import mimetypes

def process_file(file_path: Path):
    """
    Analyse un fichier uploadé et retourne un dictionnaire structuré 
    avec son type et son contenu (texte ou data Base64 pour les images).
    """
    if not file_path or not file_path.exists():
        return None
        
    original_name = file_path.name
    extension = file_path.suffix.lower()
    
    result = None
    try:
        # --- Traitement des fichiers texte ---
        if extension == ".txt":
            content = file_path.read_text(encoding='utf-8')
            result = {'type': 'text', 'content': content, 'filename': original_name}
        elif extension == ".md":
            content = file_path.read_text(encoding='utf-8')
            result = {'type': 'text', 'content': content, 'filename': original_name}
        elif extension == ".json":
            content = file_path.read_text(encoding='utf-8')
            result = {'type': 'text', 'content': content, 'filename': original_name}
        elif extension == ".pdf":
            reader = pypdf.PdfReader(file_path)
            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
            result = {'type': 'text', 'content': text, 'filename': original_name}
        elif extension == ".docx":
            doc = docx.Document(file_path)
            text = ""
            for para in doc.paragraphs:
                text += para.text + "\n"
            result = {'type': 'text', 'content': text, 'filename': original_name}
        
        # --- Traitement des fichiers image ---
        elif extension in [".jpg", ".jpeg", ".png", ".webp", ".gif"]:
            # Lecture des bytes de l'image
            with open(file_path, "rb") as image_file:
                image_bytes = image_file.read()
            
            # Encodage en Base64
            base64_data = base64.b64encode(image_bytes).decode('utf-8')
            
            # Détection du type MIME (ex: 'image/jpeg')
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                mime_type = 'application/octet-stream' # Fallback
            
            result = {
                'type': 'image',
                'mime_type': mime_type,
                'data': base64_data,
                'filename': original_name
            }
        
        else:
            unsupported_content = f"[Type de fichier '{extension}' non supporté]"
            result = {'type': 'text', 'content': unsupported_content, 'filename': original_name}
            
    except Exception as e:
        error_content = f"[Erreur lors de la lecture du fichier {original_name}]"
        print(f"ERROR processing file {original_name}: {e}")
        result = {'type': 'text', 'content': error_content, 'filename': original_name}
    finally:
        # Nettoyage du fichier temporaire
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Erreur lors de la suppression du fichier temporaire {file_path}: {e}")
                
    return result