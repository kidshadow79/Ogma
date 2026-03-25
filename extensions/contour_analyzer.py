# extensions/contour_analyzer.py
"""
Analyseur de Contours pour OGMA
===============================
Détection et tracé des contours/formes dans les images.
Unfiltered total - aucun filtre, aucune censure.

Méthodes disponibles :
- Canny Edge Detection (contours nets)
- Sobel (gradients directionnels)  
- Laplacian (contours fins)
- Adaptive Threshold (formes contrastées)
- Combined (fusion des méthodes)

Rendu : Tracés rouges épais sur fond noir ou superposés à l'original
"""

import cv2
import numpy as np
from typing import Optional, Dict, Tuple, List
from pathlib import Path


class ContourAnalyzer:
    """
    Analyseur de contours utilisant OpenCV.
    Détecte les formes et contours anatomiques sans aucun filtre.
    Produit des tracés épais rouges pour guider la compréhension IA.
    """
    
    def __init__(self):
        self.is_ready = True
        
        # Options par défaut
        self.options = {
            # Méthodes de détection
            'enable_canny': True,           # Contours Canny (principal)
            'enable_sobel': False,          # Gradients Sobel
            'enable_laplacian': False,      # Contours Laplacian
            'enable_adaptive': False,       # Seuillage adaptatif
            
            # Paramètres Canny
            'canny_low': 50,                # Seuil bas Canny
            'canny_high': 150,              # Seuil haut Canny
            
            # Paramètres Sobel
            'sobel_ksize': 3,               # Taille kernel Sobel (3, 5, 7)
            
            # Paramètres généraux
            'blur_size': 5,                 # Flou gaussien pré-traitement
            'line_thickness': 2,            # Épaisseur des contours
            'line_color': 'red',            # Couleur: 'red', 'white', 'black'
            
            # Mode de rendu
            'render_mode': 'overlay',       # 'overlay', 'black_bg', 'white_bg'
            'overlay_alpha': 0.7,           # Transparence overlay (0-1)
            
            # Post-traitement
            'dilate_iterations': 1,         # Épaississement contours
            'close_gaps': True,             # Fermer les contours ouverts
        }
        
        # Mapping couleurs nom -> BGR
        self.color_map = {
            'red': (0, 0, 255),      # Rouge
            'white': (255, 255, 255), # Blanc
            'black': (0, 0, 0)        # Noir
        }
        
        print("[CONTOUR] ✅ Analyseur de contours initialisé")

    def update_options(self, options: Dict):
        """Met à jour les options de détection"""
        self.options.update(options)
        print(f"[CONTOUR] Options mises à jour: {list(options.keys())}")

    def _preprocess(self, image: np.ndarray) -> np.ndarray:
        """Prétraitement de l'image (conversion gris + flou)"""
        # Conversion en niveaux de gris
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image.copy()
        
        # Flou gaussien pour réduire le bruit
        blur_size = self.options.get('blur_size', 5)
        if blur_size > 0:
            # S'assurer que la taille est impaire
            blur_size = blur_size if blur_size % 2 == 1 else blur_size + 1
            gray = cv2.GaussianBlur(gray, (blur_size, blur_size), 0)
        
        return gray

    def _detect_canny(self, gray: np.ndarray) -> np.ndarray:
        """Détection de contours par Canny Edge Detection"""
        low = self.options.get('canny_low', 50)
        high = self.options.get('canny_high', 150)
        edges = cv2.Canny(gray, low, high)
        return edges

    def _detect_sobel(self, gray: np.ndarray) -> np.ndarray:
        """Détection de contours par Sobel (gradients X + Y)"""
        ksize = self.options.get('sobel_ksize', 3)
        
        # Gradients X et Y
        sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=ksize)
        sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=ksize)
        
        # Magnitude combinée
        magnitude = np.sqrt(sobel_x**2 + sobel_y**2)
        magnitude = np.uint8(np.clip(magnitude, 0, 255))
        
        # Seuillage
        _, edges = cv2.threshold(magnitude, 50, 255, cv2.THRESH_BINARY)
        return edges

    def _detect_laplacian(self, gray: np.ndarray) -> np.ndarray:
        """Détection de contours par Laplacian"""
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        laplacian = np.uint8(np.abs(laplacian))
        
        # Seuillage
        _, edges = cv2.threshold(laplacian, 30, 255, cv2.THRESH_BINARY)
        return edges

    def _detect_adaptive(self, gray: np.ndarray) -> np.ndarray:
        """Détection par seuillage adaptatif"""
        # Seuillage adaptatif
        binary = cv2.adaptiveThreshold(
            gray, 255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 
            11, 2
        )
        
        # Extraction des contours uniquement
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        edges = np.zeros_like(gray)
        cv2.drawContours(edges, contours, -1, 255, 1)
        
        return edges

    def _postprocess_edges(self, edges: np.ndarray) -> np.ndarray:
        """Post-traitement des contours détectés"""
        # Dilatation pour épaissir les contours
        dilate_iter = self.options.get('dilate_iterations', 1)
        if dilate_iter > 0:
            kernel = np.ones((3, 3), np.uint8)
            edges = cv2.dilate(edges, kernel, iterations=dilate_iter)
        
        # Fermeture morphologique pour connecter les contours proches
        if self.options.get('close_gaps', True):
            kernel = np.ones((5, 5), np.uint8)
            edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
        
        return edges

    def _get_line_color_bgr(self) -> Tuple[int, int, int]:
        """Récupère la couleur des lignes en BGR"""
        color_option = self.options.get('line_color', 'red')
        # Si c'est déjà un tuple BGR, le retourner
        if isinstance(color_option, tuple):
            return color_option
        # Sinon, mapper le nom vers BGR
        return self.color_map.get(color_option, (0, 0, 255))  # Rouge par défaut

    def _render_contours(self, original: np.ndarray, edges: np.ndarray) -> np.ndarray:
        """Rendu des contours sur l'image"""
        h, w = original.shape[:2]
        render_mode = self.options.get('render_mode', 'overlay')
        color = self._get_line_color_bgr()
        thickness = self.options.get('line_thickness', 2)
        
        if render_mode == 'black_bg':
            # Contours sur fond noir
            result = np.zeros((h, w, 3), dtype=np.uint8)
        elif render_mode == 'white_bg':
            # Contours sur fond blanc
            result = np.ones((h, w, 3), dtype=np.uint8) * 255
        else:
            # Overlay sur l'original
            result = original.copy()
        
        # Trouver les contours à partir des edges
        contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        
        # Dessiner les contours
        cv2.drawContours(result, contours, -1, color, thickness)
        
        # Si overlay, mélanger avec l'original
        if render_mode == 'overlay':
            alpha = self.options.get('overlay_alpha', 0.7)
            # Créer un masque des contours
            mask = edges > 0
            # Appliquer les contours colorés uniquement où il y a des edges
            contour_layer = np.zeros_like(original)
            cv2.drawContours(contour_layer, contours, -1, color, thickness)
            
            # Mélange pondéré
            result = original.copy()
            result[mask] = cv2.addWeighted(
                original[mask], 1 - alpha,
                contour_layer[mask], alpha,
                0
            )
            # Redessiner les contours en plein pour visibilité
            cv2.drawContours(result, contours, -1, color, thickness)
        
        return result

    def _add_legend(self, image: np.ndarray, methods_used: List[str], contour_count: int) -> np.ndarray:
        """Ajoute une légende explicative en haut de l'image"""
        h, w = image.shape[:2]
        
        # Créer une bande pour la légende
        legend_height = 50
        legend = np.zeros((legend_height, w, 3), dtype=np.uint8)
        legend[:] = (40, 40, 40)  # Fond gris foncé
        
        # Titre
        cv2.putText(legend, "ANALYSE CONTOURS", (10, 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Méthodes utilisées
        methods_text = " | ".join(methods_used) if methods_used else "Aucune"
        cv2.putText(legend, f"Methodes: {methods_text}", (10, 38), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
        
        # Nombre de contours
        cv2.putText(legend, f"Contours: {contour_count}", (w - 150, 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 255), 1)
        
        # Indicateur couleur avec nom
        color = self._get_line_color_bgr()
        color_name = self.options.get('line_color', 'red')
        color_names_fr = {'red': 'Rouge', 'white': 'Blanc', 'black': 'Noir'}
        color_label = color_names_fr.get(color_name, 'Rouge') if isinstance(color_name, str) else 'Custom'
        cv2.rectangle(legend, (w - 150, 28), (w - 130, 42), color, -1)
        # Bordure pour le rectangle si couleur sombre
        cv2.rectangle(legend, (w - 150, 28), (w - 130, 42), (128, 128, 128), 1)
        cv2.putText(legend, color_label, (w - 125, 40), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1)
        
        # Combiner légende + image
        result = np.vstack((legend, image))
        return result

    def process_image(self, cv2_frame: np.ndarray, add_legend: bool = True) -> np.ndarray:
        """
        Traite une image OpenCV :
        1. Détecte les contours selon les méthodes activées
        2. Dessine les tracés rouges épais
        3. Crée un composite (Original | Contours)
        
        Args:
            cv2_frame: Image BGR OpenCV
            add_legend: Ajouter la légende sur l'image augmentée
            
        Returns:
            Image composite BGR (original gauche, contours droite)
        """
        try:
            # Prétraitement
            gray = self._preprocess(cv2_frame)
            
            # Combiner les différentes méthodes de détection
            combined_edges = np.zeros_like(gray)
            methods_used = []
            
            if self.options.get('enable_canny', True):
                canny_edges = self._detect_canny(gray)
                combined_edges = cv2.bitwise_or(combined_edges, canny_edges)
                methods_used.append("Canny")
            
            if self.options.get('enable_sobel', False):
                sobel_edges = self._detect_sobel(gray)
                combined_edges = cv2.bitwise_or(combined_edges, sobel_edges)
                methods_used.append("Sobel")
            
            if self.options.get('enable_laplacian', False):
                laplacian_edges = self._detect_laplacian(gray)
                combined_edges = cv2.bitwise_or(combined_edges, laplacian_edges)
                methods_used.append("Laplacian")
            
            if self.options.get('enable_adaptive', False):
                adaptive_edges = self._detect_adaptive(gray)
                combined_edges = cv2.bitwise_or(combined_edges, adaptive_edges)
                methods_used.append("Adaptive")
            
            # Si aucune méthode activée, utiliser Canny par défaut
            if not methods_used:
                combined_edges = self._detect_canny(gray)
                methods_used.append("Canny (default)")
            
            # Post-traitement
            processed_edges = self._postprocess_edges(combined_edges)
            
            # Compter les contours
            contours, _ = cv2.findContours(processed_edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            contour_count = len(contours)
            
            # Rendu des contours
            contour_image = self._render_contours(cv2_frame, processed_edges)
            
            # Ajouter légende si demandé
            if add_legend:
                contour_image = self._add_legend(contour_image, methods_used, contour_count)
                # Ajuster l'original pour avoir la même hauteur
                legend_height = 50
                original_padded = np.zeros((cv2_frame.shape[0] + legend_height, cv2_frame.shape[1], 3), dtype=np.uint8)
                original_padded[:] = (40, 40, 40)
                original_padded[legend_height:, :] = cv2_frame
                # Label "ORIGINAL"
                cv2.putText(original_padded, "ORIGINAL", (10, 20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                original = original_padded
            else:
                original = cv2_frame
            
            # Créer composite side-by-side
            composite = np.hstack((original, contour_image))
            
            print(f"[CONTOUR] ✅ Analyse: {contour_count} contours détectés ({', '.join(methods_used)})")
            
            return composite
            
        except Exception as e:
            print(f"[CONTOUR] ❌ Erreur traitement: {e}")
            import traceback
            traceback.print_exc()
            return cv2_frame

    def process_image_contours_only(self, cv2_frame: np.ndarray) -> np.ndarray:
        """
        Retourne UNIQUEMENT l'image avec contours (sans l'originale)
        Utile pour le mode 3 colonnes (Original | Depth | Contours)
        """
        try:
            gray = self._preprocess(cv2_frame)
            
            combined_edges = np.zeros_like(gray)
            
            if self.options.get('enable_canny', True):
                combined_edges = cv2.bitwise_or(combined_edges, self._detect_canny(gray))
            if self.options.get('enable_sobel', False):
                combined_edges = cv2.bitwise_or(combined_edges, self._detect_sobel(gray))
            if self.options.get('enable_laplacian', False):
                combined_edges = cv2.bitwise_or(combined_edges, self._detect_laplacian(gray))
            if self.options.get('enable_adaptive', False):
                combined_edges = cv2.bitwise_or(combined_edges, self._detect_adaptive(gray))
            
            if np.sum(combined_edges) == 0:
                combined_edges = self._detect_canny(gray)
            
            processed_edges = self._postprocess_edges(combined_edges)
            contour_image = self._render_contours(cv2_frame, processed_edges)
            
            return contour_image
            
        except Exception as e:
            print(f"[CONTOUR] ❌ Erreur: {e}")
            return cv2_frame

    def cleanup(self):
        """Libère les ressources"""
        print("[CONTOUR] 🧹 Ressources libérées")


# Singleton global
_contour_analyzer = None

def get_contour_analyzer() -> ContourAnalyzer:
    """Retourne l'instance singleton de l'analyseur de contours"""
    global _contour_analyzer
    if _contour_analyzer is None:
        _contour_analyzer = ContourAnalyzer()
    return _contour_analyzer

def is_available() -> bool:
    """Vérifie si l'analyse de contours est disponible (toujours True - OpenCV seulement)"""
    return True
