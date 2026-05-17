import os
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    cv2 = None
    CV2_AVAILABLE = False
    print("[DEPTH] opencv-python non disponible - Depth Manager desactive")
import torch
import numpy as np
from PIL import Image, ImageDraw
from pathlib import Path
from transformers import pipeline

class DepthManager:
    def __init__(self, models_dir="c:/IA/OGMA/models"):
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.pipe = None
        self.model_id = "depth-anything/Depth-Anything-V2-Small-hf"
        self.is_ready = False
        
        # Initialisation différée pour ne pas bloquer le démarrage
        print(f"[DEPTH-MANAGER] ⏳ Initialisé (chargement au premier appel)")

    def _ensure_model(self):
        """Charge le modèle si nécessaire"""
        if self.pipe is not None:
            return True
            
        try:
            print(f"[DEPTH-MANAGER] 🚀 Chargement du modèle {self.model_id}...")
            # Utiliser le dossier models pour le cache si possible, sinon cache par défaut HF
            # Note: transformers gère son propre cache, on laisse faire pour l'instant
            self.pipe = pipeline(
                task="depth-estimation", 
                model=self.model_id, 
                device=0 if torch.cuda.is_available() else -1,
            )
            self.is_ready = True
            print(f"[DEPTH-MANAGER] ✅ Modèle chargé avec succès")
            return True
        except Exception as e:
            print(f"[DEPTH-MANAGER] ❌ Erreur chargement modèle: {e}")
            return False

    def process_image(self, cv2_frame):
        """
        Traite une image OpenCV :
        1. Estime la profondeur
        2. Ajoute une grille
        3. Crée un composite (Original + Depth)
        """
        if not self._ensure_model():
            return cv2_frame

        try:
            # Conversion OpenCV (BGR) -> PIL (RGB)
            rgb_frame = cv2.cvtColor(cv2_frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_frame)
            
            # 1. Estimation Profondeur
            depth_result = self.pipe(pil_image)
            depth_map = depth_result["depth"]
            
            # Convertir depth map en heatmap colorée pour meilleure visibilité
            depth_np = np.array(depth_map)
            # Normaliser 0-255
            depth_normalized = cv2.normalize(depth_np, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
            # Appliquer colormap (INFERNO est très lisible pour la profondeur)
            depth_colored = cv2.applyColorMap(depth_normalized, cv2.COLORMAP_INFERNO)
            # Convertir en PIL
            depth_pil = Image.fromarray(cv2.cvtColor(depth_colored, cv2.COLOR_BGR2RGB))
            
            # 2. Création Composite (Side-by-Side)
            w, h = pil_image.size
            composite = Image.new('RGB', (w * 2, h))
            composite.paste(pil_image, (0, 0))
            composite.paste(depth_pil, (w, 0))
            
            # 3. Ajout Grille et Labels
            draw = ImageDraw.Draw(composite)
            
            # Grille 8x8 sur les deux images
            grid_cols = 8
            grid_rows = 8
            step_x = w / grid_cols
            step_y = h / grid_rows
            
            # Dessiner grille sur image gauche (Originale)
            for i in range(1, grid_cols):
                x = i * step_x
                draw.line([(x, 0), (x, h)], fill=(255, 255, 255, 128), width=1)
            for i in range(1, grid_rows):
                y = i * step_y
                draw.line([(0, y), (w, y)], fill=(255, 255, 255, 128), width=1)
                
            # Dessiner grille sur image droite (Depth)
            for i in range(1, grid_cols):
                x = w + (i * step_x)
                draw.line([(x, 0), (x, h)], fill=(255, 255, 255, 128), width=1)
            for i in range(1, grid_rows):
                y = i * step_y
                draw.line([(w, y), (w + w, y)], fill=(255, 255, 255, 128), width=1)
            
            # Coordonnées (A1..H8)
            # On ajoute quelques repères
            draw.text((10, 10), "VUE ORIGINALE (GRILLE 8x8)", fill=(0, 255, 0))
            draw.text((w + 10, 10), "CARTE PROFONDEUR (DEPTH ANYTHING V2)", fill=(255, 128, 0))
            draw.text((w + 10, 30), "Chaud (Jaune) = Proche | Froid (Violet) = Loin", fill=(255, 128, 0))

            # Conversion retour vers OpenCV
            composite_np = np.array(composite)
            return cv2.cvtColor(composite_np, cv2.COLOR_RGB2BGR)

        except Exception as e:
            print(f"[DEPTH-MANAGER] ❌ Erreur processing: {e}")
            import traceback
            traceback.print_exc()
            return cv2_frame
