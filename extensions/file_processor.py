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
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    cv2 = None
    CV2_AVAILABLE = False
    print("[FILE-PROCESSOR] opencv-python non disponible - analyse visuelle desactivee (pip install opencv-python)")
import numpy as np
from datetime import datetime

# Singleton pour DepthManager
_depth_manager_instance = None

def _get_depth_manager():
    global _depth_manager_instance
    if _depth_manager_instance is None:
        try:
            from extensions.depth_manager import DepthManager
            _depth_manager_instance = DepthManager()
        except ImportError:
            print("[FILE-PROCESSOR] ⚠️ Impossible d'importer DepthManager")
            return None
        except Exception as e:
            print(f"[FILE-PROCESSOR] ⚠️ Erreur init DepthManager: {e}")
            return None
    return _depth_manager_instance

# Singleton pour ContourAnalyzer
_contour_analyzer_instance = None

def _get_contour_analyzer():
    global _contour_analyzer_instance
    if _contour_analyzer_instance is None:
        try:
            from extensions.contour_analyzer import get_contour_analyzer
            _contour_analyzer_instance = get_contour_analyzer()
        except ImportError:
            print("[FILE-PROCESSOR] ⚠️ Impossible d'importer ContourAnalyzer")
            return None
        except Exception as e:
            print(f"[FILE-PROCESSOR] ⚠️ Erreur init ContourAnalyzer: {e}")
            return None
    return _contour_analyzer_instance

def _get_settings_manager():
    """Helper pour accéder au settings manager via import dynamique"""
    try:
        import sys
        ogma_ng = sys.modules.get('ogma_ng')
        if ogma_ng and hasattr(ogma_ng, '_ensure_settings_manager'):
            return ogma_ng._ensure_settings_manager()
        return None
    except Exception:
        return None

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
        elif extension == ".py":
            content = file_path.read_text(encoding='utf-8')
            result = {'type': 'text', 'content': content, 'filename': original_name}
        elif extension in [".js", ".ts", ".jsx", ".tsx"]:
            content = file_path.read_text(encoding='utf-8')
            result = {'type': 'text', 'content': content, 'filename': original_name}
        elif extension in [".html", ".css", ".xml", ".yaml", ".yml"]:
            content = file_path.read_text(encoding='utf-8')
            result = {'type': 'text', 'content': content, 'filename': original_name}
        elif extension in [".c", ".cpp", ".h", ".hpp", ".java", ".cs", ".go", ".rs", ".rb", ".php"]:
            content = file_path.read_text(encoding='utf-8')
            result = {'type': 'text', 'content': content, 'filename': original_name}
        elif extension in [".sh", ".bash", ".ps1", ".bat", ".cmd"]:
            content = file_path.read_text(encoding='utf-8')
            result = {'type': 'text', 'content': content, 'filename': original_name}
        elif extension in [".sql", ".csv", ".log", ".ini", ".cfg", ".conf", ".toml"]:
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
            # 📐 DIAGNOSTIC: Log taille image uploadée
            try:
                from PIL import Image as PILImage
                with PILImage.open(file_path) as img:
                    orig_w, orig_h = img.size
                    orig_pixels = orig_w * orig_h
                    print(f"[FILE-PROCESSOR] 📐 Image uploadée: {original_name} → {orig_w}x{orig_h} = {orig_pixels:,} pixels")
                    if orig_pixels < 3686400:  # Minimum Seedream V4.5
                        print(f"[FILE-PROCESSOR] ⚠️ ATTENTION: Image trop petite pour Seedream V4.5 (min 1920x1920)")
            except Exception as diag_err:
                print(f"[FILE-PROCESSOR] ⚠️ Diag taille échoué: {diag_err}")
            
            # Vérifier les options Vision Avancée
            use_depth = False
            use_contour = False
            sm = _get_settings_manager()
            if sm:
                use_depth = sm.settings.get('perception', {}).get('process_uploads_with_depth', False)
                use_contour = sm.settings.get('perception', {}).get('process_uploads_with_contour', False)
            
            processed_image_bytes = None
            
            # Si au moins une option Vision Avancée est activée
            if use_depth or use_contour:
                print(f"[FILE-PROCESSOR] 🖼️ Vision Avancée demandée pour {original_name} (Depth:{use_depth}, Contour:{use_contour})")
                
                # Récupérer les options contour depuis settings
                contour_options = {}
                if sm and use_contour:
                    perception = sm.settings.get('perception', {})
                    contour_options = {
                        'enable_canny': perception.get('contour_canny', True),
                        'enable_sobel': perception.get('contour_sobel', False),
                        'enable_laplacian': perception.get('contour_laplacian', False),
                        'enable_adaptive': perception.get('contour_adaptive', False),
                        'canny_low': perception.get('contour_canny_low', 50),
                        'canny_high': perception.get('contour_canny_high', 150),
                        'line_thickness': perception.get('contour_thickness', 2),
                        'line_color': perception.get('contour_line_color', 'red'),
                        'render_mode': perception.get('contour_render_mode', 'overlay')
                    }
                
                try:
                    # Lire l'image avec OpenCV
                    img_array = np.fromfile(file_path, np.uint8)
                    cv2_img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                    
                    if cv2_img is not None:
                        h, w = cv2_img.shape[:2]
                        
                        # CAS 1: Les deux activés → 3 colonnes (Original | Depth | Contours)
                        if use_depth and use_contour:
                            dm = _get_depth_manager()
                            ca = _get_contour_analyzer()
                            if ca and contour_options:
                                ca.update_options(contour_options)
                            
                            # Image originale avec header
                            legend_height = 60
                            original_with_header = np.zeros((h + legend_height, w, 3), dtype=np.uint8)
                            original_with_header[:] = (40, 40, 40)
                            original_with_header[legend_height:, :] = cv2_img
                            cv2.putText(original_with_header, "ORIGINAL", (10, 20), 
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                            
                            # Depth (image seule avec header)
                            depth_img = original_with_header.copy()
                            if dm:
                                depth_result = dm.process_image(cv2_img)
                                # Le depth_manager retourne déjà un composite, on prend juste la partie droite
                                if depth_result.shape[1] > w:
                                    depth_only = depth_result[:, w:]
                                    depth_img = np.zeros((h + legend_height, w, 3), dtype=np.uint8)
                                    depth_img[:] = (40, 40, 40)
                                    # Redimensionner si nécessaire
                                    if depth_only.shape[0] != h:
                                        depth_only = cv2.resize(depth_only, (w, h))
                                    depth_img[legend_height:, :] = depth_only
                                cv2.putText(depth_img, "DEPTH MAP", (10, 20), 
                                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                            
                            # Contours (image seule avec header)
                            contour_img = original_with_header.copy()
                            if ca:
                                contour_only = ca.process_image_contours_only(cv2_img)
                                contour_img = np.zeros((h + legend_height, w, 3), dtype=np.uint8)
                                contour_img[:] = (40, 40, 40)
                                contour_img[legend_height:, :] = contour_only
                                cv2.putText(contour_img, "ANALYSE CONTOURS", (10, 20), 
                                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                            
                            # Composite 3 colonnes
                            processed_cv2_img = np.hstack((original_with_header, depth_img, contour_img))
                            print(f"[FILE-PROCESSOR] ✅ Vision Avancée 3 colonnes appliquée")
                        
                        # CAS 2: Depth seul → 2 colonnes
                        elif use_depth:
                            dm = _get_depth_manager()
                            if dm:
                                processed_cv2_img = dm.process_image(cv2_img)
                                print(f"[FILE-PROCESSOR] ✅ Depth Map appliquée")
                            else:
                                processed_cv2_img = cv2_img
                        
                        # CAS 3: Contours seul → 2 colonnes
                        elif use_contour:
                            ca = _get_contour_analyzer()
                            if ca:
                                if contour_options:
                                    ca.update_options(contour_options)
                                processed_cv2_img = ca.process_image(cv2_img)
                                print(f"[FILE-PROCESSOR] ✅ Analyse Contours appliquée")
                            else:
                                processed_cv2_img = cv2_img
                        
                        # Encoder en JPEG (en mémoire)
                        success, encoded_img = cv2.imencode('.jpg', processed_cv2_img)
                        if success:
                            processed_image_bytes = encoded_img.tobytes()
                            
                            # SAUVEGARDE AUTOMATIQUE DANS CAPTURES
                            try:
                                captures_dir = Path("captures")
                                captures_dir.mkdir(exist_ok=True)
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                # Nettoyage nom fichier simple
                                safe_name = "".join([c for c in original_name if c.isalnum() or c in ('-','_','.',' ')])
                                # Préfixe selon le type de traitement
                                if use_depth and use_contour:
                                    prefix = "upload_vision_full"
                                elif use_depth:
                                    prefix = "upload_depth"
                                else:
                                    prefix = "upload_contour"
                                save_name = f"{prefix}_{timestamp}_{safe_name}"
                                save_path = captures_dir / save_name
                                
                                # Ecriture du fichier
                                with open(save_path, "wb") as f:
                                    f.write(processed_image_bytes)
                                print(f"[FILE-PROCESSOR] 💾 Image sauvegardée dans {save_path}")
                            except Exception as e:
                                print(f"[FILE-PROCESSOR] ⚠️ Erreur sauvegarde capture: {e}")

                except Exception as e:
                    print(f"[FILE-PROCESSOR] ⚠️ Erreur Vision Avancée: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Si pas de depth ou erreur, lecture standard
            if processed_image_bytes is None:
                # Lecture des bytes de l'image originale
                with open(file_path, "rb") as image_file:
                    image_bytes = image_file.read()
                vision_bytes = None  # Pas de composite vision
            else:
                # ⚠️ CORRECTION BUG I2I: Toujours stocker l'ORIGINAL dans data
                # Le composite vision va dans un champ séparé pour l'affichage uniquement
                with open(file_path, "rb") as image_file:
                    image_bytes = image_file.read()  # ORIGINAL pour I2I
                vision_bytes = processed_image_bytes  # Composite pour vision/affichage

            # Encodage en Base64 - TOUJOURS l'original pour data (utilisé par I2I)
            base64_data = base64.b64encode(image_bytes).decode('utf-8')
            
            # Si vision avancée, encoder aussi le composite pour l'affichage
            base64_vision = None
            if vision_bytes:
                base64_vision = base64.b64encode(vision_bytes).decode('utf-8')
                print(f"[FILE-PROCESSOR] 📐 Original: {len(image_bytes):,} bytes | Vision: {len(vision_bytes):,} bytes")
            
            # Détection du type MIME (ex: 'image/jpeg')
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                mime_type = 'application/octet-stream' # Fallback
            
            result = {
                'type': 'image',
                'mime_type': mime_type,
                'data': base64_data,  # ORIGINAL - utilisé par I2I
                'data_vision': base64_vision,  # Composite vision (ou None) - pour affichage
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