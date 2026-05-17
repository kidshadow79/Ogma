# extensions/perception_agent.py

import threading
import time
import queue
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    cv2 = None
    CV2_AVAILABLE = False
    print("[PERCEPTION] opencv-python non disponible - webcam desactivee (pip install opencv-python)")
import base64
import requests
import json
import traceback
import numpy as np
import collections
import os
import sys
from datetime import datetime
from typing import Optional, Dict, List
from PIL import Image, ImageDraw, ImageFont

# Import Depth Manager
try:
    from extensions.depth_manager import DepthManager
    DEPTH_AVAILABLE = True
    print("[DEPTH] ✅ Depth Manager disponible")
except ImportError as e:
    DEPTH_AVAILABLE = False
    print(f"[DEPTH] ⚠️ Depth Manager non disponible: {e}")

# Import Contour Analyzer
try:
    from extensions.contour_analyzer import get_contour_analyzer, is_available as contour_is_available
    CONTOUR_AVAILABLE = contour_is_available()
    print(f"[CONTOUR] {'✅' if CONTOUR_AVAILABLE else '⚠️'} Contour Analyzer {'disponible' if CONTOUR_AVAILABLE else 'non disponible'}")
except ImportError as e:
    CONTOUR_AVAILABLE = False
    print(f"[CONTOUR] ⚠️ Contour Analyzer non disponible: {e}")

# Import du gestionnaire TTS/Perception
try:
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from tts_perception_manager import on_perception_start, on_perception_stop, get_manager_status
    TTS_MANAGER_AVAILABLE = True
    print("[TTS-MANAGER] ✅ Gestionnaire TTS/Perception disponible")
except ImportError as e:
    TTS_MANAGER_AVAILABLE = False
    print(f"[TTS-MANAGER] ⚠️ Gestionnaire non disponible: {e}")
    
    # Fallback functions
    def on_perception_start():
        return True
    def on_perception_stop():
        return True
    def get_manager_status():
        return {"available": False}

# Import du nouveau TTS sans conflit
try:
    from tts_conflict_free import set_perception_active, get_conflict_free_tts
    TTS_CONFLICT_FREE_AVAILABLE = True
    print("[TTS-SAFE] ✅ TTS sans conflit disponible")
except ImportError as e:
    TTS_CONFLICT_FREE_AVAILABLE = False
    print(f"[TTS-SAFE] ⚠️ TTS sans conflit non disponible: {e}")
    
    # Fallback functions
    def set_perception_active(active: bool):
        pass
    def get_conflict_free_tts():
        return None

class PerceptionAgent:
    """
    Agent de perception SIMPLIFIÉ - Capture à la demande et chronophotographie
    Architecture optimisée: pas de buffer pré-capture, toutes images après clic
    """
    def __init__(self, initial_config: dict):
        self.visual_queue = queue.Queue(maxsize=10)  # ✅ Buffer plus grand pour stream fluide sans stroboscope
        self.event_queue = queue.Queue()
        self.status = "inactive" # inactive, warming_up, active

        self.running = False
        self.thread = None
        self.cap = None
        self.current_frame = None
        self.frame_lock = threading.Lock()

        # Configuration
        self.config = initial_config
        self.webcam_index = initial_config.get("webcam_index", 0)
        self.capture_resolution = tuple(initial_config.get("triage_resolution", [640, 480]))
        
        # Initialiser Depth Manager
        self.depth_manager = DepthManager() if DEPTH_AVAILABLE else None
        
        # Initialiser Contour Analyzer
        self.contour_analyzer = get_contour_analyzer() if CONTOUR_AVAILABLE else None
        
        print("[PERCEPTION-AGENT] ✅ Agent initialisé (architecture simplifiée)")

    def update_config(self, new_config: dict):
        """Met à jour la configuration de l'agent"""
        # Détecter changements importants pour logs
        old_save_captures = self.config.get('save_captures', False)
        new_save_captures = new_config.get('save_captures', old_save_captures)
        
        self.config.update(new_config)
        
        # Mettre à jour capture_resolution si changée (conversion string → tuple)
        if 'capture_resolution' in new_config:
            res_str = new_config['capture_resolution']
            if isinstance(res_str, str) and 'x' in res_str:
                width, height = map(int, res_str.split('x'))
                self.capture_resolution = (width, height)
                print(f"[CONFIG] 📐 Résolution stream mise à jour: {width}x{height}")
        
        # Log spécial pour save_captures car c'est un paramètre critique
        if old_save_captures != new_save_captures:
            print(f"[CONFIG] 🔄 save_captures: {old_save_captures} → {new_save_captures}")
            print(f"[CONFIG] 💾 Captures simples: {'activées' if new_save_captures else 'désactivées'}")
            print(f"[CONFIG] 🎬 Chronophotographies: toujours sauvegardées si configuré")
        
        print(f"[CONFIG] Configuration mise à jour dans PerceptionAgent: {len(new_config)} paramètres")

    def _save_image_if_enabled(self, frame, filename_prefix="capture"):
        """
        Sauvegarde une image localement si save_captures est activé
        EXCEPTION: les pellicules motion sont TOUJOURS sauvées
        """
        try:
            # PELLICULES MOTION: Toujours sauvegarder (priorité utilisateur)
            is_motion_pellicule = filename_prefix.startswith("pellicule_")
            
            # Vérifier si la sauvegarde est activée (sauf pour pellicules motion)
            if not is_motion_pellicule and not self.config.get('save_captures', False):
                return None
            
            # Créer le dossier de captures s'il n'existe pas
            capture_folder = self.config.get('capture_folder', './captures')
            os.makedirs(capture_folder, exist_ok=True)
            
            # Générer nom de fichier avec timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # milliseconds
            format_ext = self.config.get('capture_format', 'JPEG').lower()
            ext = 'jpg' if format_ext == 'jpeg' else format_ext
            filename = f"{filename_prefix}_{timestamp}.{ext}"
            filepath = os.path.join(capture_folder, filename)
            
            # Sauvegarder l'image
            if format_ext == 'jpeg':
                quality = self.config.get('jpeg_quality', 85)
                cv2.imwrite(filepath, frame, [cv2.IMWRITE_JPEG_QUALITY, quality])
            else:
                cv2.imwrite(filepath, frame)
            
            # Log spécial pour pellicules motion
            if is_motion_pellicule:
                print(f"[PELLICULE] 🎬 Chronophotographie sauvée: {filepath}")
            else:
                print(f"[SAVE] Image sauvegardée: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"[ERREUR] Erreur sauvegarde image: {e}")
            return None

    def _resize_keep_aspect(self, frame, target_width=None, target_height=None):
        """
        Redimensionne une image en préservant l'aspect ratio.
        Priorité: target_height si fourni, sinon target_width.
        
        Args:
            frame: Image OpenCV (numpy array)
            target_width: Largeur cible (optionnel)
            target_height: Hauteur cible (optionnel)
        
        Returns:
            Image redimensionnée avec aspect ratio préservé
        """
        h, w = frame.shape[:2]
        
        # Si hauteur cible fournie (mode Chirurgical 720p)
        if target_height is not None:
            aspect_ratio = w / h
            new_h = target_height
            new_w = int(new_h * aspect_ratio)
        # Sinon utiliser largeur cible
        elif target_width is not None:
            aspect_ratio = h / w
            new_w = target_width
            new_h = int(new_w * aspect_ratio)
        else:
            # Aucune cible fournie, retourner frame original
            return frame
        
        return cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

    def _create_split_view(self, left, right):
        """Crée une vue côte à côte"""
        h1, w1 = left.shape[:2]
        h2, w2 = right.shape[:2]
        
        if h1 != h2:
            right = cv2.resize(right, (int(w2 * h1 / h2), h1))
            
        return np.hstack((left, right))

    def _apply_advanced_vision(self, frame):
        """
        Applique les filtres de vision avancée (Depth et/ou Contours)
        - Depth seul: 2 colonnes (Original | Depth)
        - Contours seul: 2 colonnes (Original | Contours)
        - Les deux: 3 colonnes (Original | Depth | Contours)
        """
        enable_depth = self.config.get('enable_depth', False) and self.depth_manager
        enable_contour = self.config.get('enable_contour', False) and self.contour_analyzer
        
        # Cas 1: Aucun filtre
        if not enable_depth and not enable_contour:
            return frame
        
        h, w = frame.shape[:2]
        legend_height = 60
        
        # Cas 2: Les deux activés → 3 colonnes
        if enable_depth and enable_contour:
            # Mettre à jour les options contours depuis la config
            contour_options = {
                'enable_canny': self.config.get('contour_canny', True),
                'enable_sobel': self.config.get('contour_sobel', False),
                'enable_laplacian': self.config.get('contour_laplacian', False),
                'enable_adaptive': self.config.get('contour_adaptive', False),
                'canny_low': self.config.get('contour_canny_low', 50),
                'canny_high': self.config.get('contour_canny_high', 150),
                'line_thickness': self.config.get('contour_thickness', 2),
                'render_mode': self.config.get('contour_render_mode', 'overlay')
            }
            self.contour_analyzer.update_options(contour_options)
            
            # Colonne 1: Original avec header
            original_col = np.zeros((h + legend_height, w, 3), dtype=np.uint8)
            original_col[:] = (40, 40, 40)
            original_col[legend_height:, :] = frame
            cv2.putText(original_col, "ORIGINAL", (10, 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Colonne 2: Depth avec header
            depth_result = self.depth_manager.process_image(frame)
            # Le depth_manager retourne un composite, on prend la partie droite
            if depth_result.shape[1] > w:
                depth_only = depth_result[:, w:]
            else:
                depth_only = depth_result
            # Redimensionner si nécessaire
            if depth_only.shape[0] != h or depth_only.shape[1] != w:
                depth_only = cv2.resize(depth_only, (w, h))
            depth_col = np.zeros((h + legend_height, w, 3), dtype=np.uint8)
            depth_col[:] = (40, 40, 40)
            depth_col[legend_height:, :] = depth_only
            cv2.putText(depth_col, "DEPTH MAP", (10, 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Colonne 3: Contours avec header
            contour_only = self.contour_analyzer.process_image_contours_only(frame)
            contour_col = np.zeros((h + legend_height, w, 3), dtype=np.uint8)
            contour_col[:] = (40, 40, 40)
            contour_col[legend_height:, :] = contour_only
            cv2.putText(contour_col, "ANALYSE CONTOURS", (10, 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            
            return np.hstack((original_col, depth_col, contour_col))
            
        # Cas 3: Depth seul → 2 colonnes
        elif enable_depth:
            return self.depth_manager.process_image(frame)
            
        # Cas 4: Contours seul → 2 colonnes
        elif enable_contour:
            # Mettre à jour les options contours depuis la config
            contour_options = {
                'enable_canny': self.config.get('contour_canny', True),
                'enable_sobel': self.config.get('contour_sobel', False),
                'enable_laplacian': self.config.get('contour_laplacian', False),
                'enable_adaptive': self.config.get('contour_adaptive', False),
                'canny_low': self.config.get('contour_canny_low', 50),
                'canny_high': self.config.get('contour_canny_high', 150),
                'line_thickness': self.config.get('contour_thickness', 2),
                'render_mode': self.config.get('contour_render_mode', 'overlay')
            }
            self.contour_analyzer.update_options(contour_options)
            return self.contour_analyzer.process_image(frame)

    def capture_for_chat(self) -> dict | None:
        """
        Capture une image au moment de l'envoi d'un message de chat.
        Retourne un dictionnaire avec les données de l'image pour intégration dans le message.
        """
        if not self.running or self.current_frame is None:
            return None
            
        with self.frame_lock:
            if self.current_frame is None:
                return None
                
            # Copie du frame actuel
            frame_copy = self.current_frame.copy()
        
        try:
            # Vérifier si on doit utiliser la résolution native
            use_native = self.config.get('use_native_resolution', False)
            
            if use_native:
                # Pas de redimensionnement - garder taille source
                frame_resized = frame_copy
                print(f"[CAPTURE] Mode résolution native activé - image source: {frame_resized.shape[1]}x{frame_resized.shape[0]}")
            else:
                # Redimensionner en préservant aspect ratio
                frame_resized = self._resize_keep_aspect(
                    frame_copy, 
                    target_width=self.capture_resolution[0]
                )

            # Traitement Vision Avancée (Depth / SAM / Fusion)
            frame_processed = self._apply_advanced_vision(frame_resized)
            
            # Sauvegarder l'image si activé
            self._save_image_if_enabled(frame_processed, "photo_simple")
            
            # Encoder en JPEG
            _, buffer = cv2.imencode('.jpg', frame_processed, [cv2.IMWRITE_JPEG_QUALITY, 85])
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            
            h, w = frame_processed.shape[:2]
            print(f"[CAPTURE] Image capturée pour le chat ({w}x{h}, aspect ratio préservé)")
            
            return {
                'type': 'image_url',
                'image_url': {
                    'url': f'data:image/jpeg;base64,{image_base64}'
                }
            }
            
        except Exception as e:
            print(f"[ERREUR] Erreur lors de la capture pour chat: {e}")
            return None

    def create_motion_sequence(self, frames_count=6, interval=0.5, capture_delay=0.0, 
                              layout='3x2', show_timeline=True, show_annotations=True) -> Optional[Dict]:
        """
        Crée une chronophotographie SIMPLIFIÉE - Capture séquentielle après clic
        
        Architecture OPTIMISÉE selon vision architecte:
        - Pas de buffer pré-capture (toutes images APRÈS clic)
        - Intervalle configurable entre chaque image
        - Délai optionnel avant première capture
        
        Args:
            frames_count: Nombre d'images à capturer (défaut: 6)
            interval: Intervalle en secondes entre chaque image (défaut: 0.5s)
            capture_delay: Délai avant première capture en secondes (défaut: 0s)
            layout: Layout d'assemblage ('3x2', '2x3', '1x6', '6x1', '2x2', '1x4', '4x1')
            show_timeline: Afficher la timeline temporelle
            show_annotations: Afficher les annotations de temps
        
        Returns:
            Dict avec l'image composite encodée en base64 pour le chat
        """
        if not self.running:
            print("[MOTION] Impossible de créer séquence: agent inactif")
            return None
            
        try:
            total_duration = (frames_count - 1) * interval + capture_delay
            print(f"[MOTION] 🎬 CHRONOPHOTOGRAPHIE: {frames_count} images @ {interval}s intervalle (durée: {total_duration:.1f}s)")
            
            # Délai initial si configuré
            if capture_delay > 0:
                print(f"[MOTION] ⏱️ Attente {capture_delay}s avant première capture...")
                time.sleep(capture_delay)
            
            all_frames = []
            all_timestamps = []
            
            # Capturer séquence d'images espacées de 'interval' secondes
            for i in range(frames_count):
                # Capturer l'image actuelle
                with self.frame_lock:
                    if self.current_frame is not None:
                        frame_copy = self.current_frame.copy()
                        all_frames.append(frame_copy)
                        all_timestamps.append(time.time())
                        print(f"[MOTION] ✅ Image {i+1}/{frames_count} capturée")
                    else:
                        print(f"[MOTION] ❌ Frame indisponible {i+1}/{frames_count}")
                
                # Attendre intervalle (sauf après dernière image)
                if i < frames_count - 1:
                    time.sleep(interval)
            
            # Post-traitement Vision Avancée (Depth / SAM)
            # On le fait APRÈS la capture pour ne pas perturber le timing de la rafale
            processed_frames = []
            print(f"[MOTION] 🧠 Traitement Vision Avancée sur {len(all_frames)} frames...")
            for idx, frame in enumerate(all_frames):
                try:
                    # Vérifier si on doit utiliser la résolution native
                    use_native = self.config.get('use_native_resolution', False)
                    
                    if use_native:
                        # Pas de redimensionnement - garder taille source
                        frame_resized = frame
                    else:
                        # Resize d'abord (comme dans capture_for_chat)
                        frame_resized = self._resize_keep_aspect(
                            frame, 
                            target_width=self.capture_resolution[0]
                        )
                    # Appliquer filtres
                    processed = self._apply_advanced_vision(frame_resized)
                    processed_frames.append(processed)
                except Exception as e:
                    print(f"[MOTION] ⚠️ Erreur traitement frame {idx}: {e}")
                    processed_frames.append(frame) # Fallback original
            
            # Utiliser les frames traités pour l'assemblage
            all_frames = processed_frames

            if len(all_frames) < 2:
                print("[MOTION] ⚠️ Pas assez d'images capturées, fallback vers capture simple")
                return self.capture_for_chat()
            
            # Créer l'assemblage selon le layout
            composite_image = self._create_film_strip(all_frames, all_timestamps, layout, 
                                                    show_timeline, show_annotations)
            
            if composite_image is None:
                print("[MOTION] ❌ Échec assemblage pellicule")
                return None
            
            # Sauvegarder la pellicule si activé
            self._save_image_if_enabled(composite_image, "pellicule_motion")
            
            # Encoder en base64 avec qualité configurable
            jpeg_quality = self.config.get('jpeg_quality', 85)
            _, buffer = cv2.imencode('.jpg', composite_image, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
            image_base64 = base64.b64encode(buffer).decode('utf-8')
            
            print(f"[MOTION] ✅ Chronophotographie créée: {len(all_frames)} frames assemblées")
            
            return {
                'type': 'image_url',
                'image_url': {
                    'url': f'data:image/jpeg;base64,{image_base64}'
                }
            }
            
        except Exception as e:
            print(f"[MOTION] ❌ Erreur création séquence: {e}")
            traceback.print_exc()
            return None

    def _create_film_strip(self, frames: List[np.ndarray], timestamps: List[float], 
                          layout='2x2', show_timeline=True, show_annotations=True) -> Optional[np.ndarray]:
        """
        Assemble plusieurs frames en une seule image de pellicule
        
        Args:
            frames: Liste des images à assembler
            timestamps: Timestamps correspondants
            layout: '2x2', '1x4', '4x1'
            show_timeline: Ajouter timeline
            show_annotations: Ajouter annotations
        
        Returns:
            Image composite assemblée
        """
        try:
            if not frames:
                return None
            
            # Redimensionner tous les frames à la même taille EXACTE avec padding pour préserver aspect ratio
            target_size = (320, 240)  # Taille individuelle réduite
            resized_frames = []
            
            for frame in frames:
                # Calculer ratio et dimensions pour préserver aspect ratio
                h, w = frame.shape[:2]
                target_w, target_h = target_size
                
                # Calculer le ratio optimal (fit inside)
                ratio = min(target_w / w, target_h / h)
                new_w = int(w * ratio)
                new_h = int(h * ratio)
                
                # Resize avec aspect ratio préservé
                resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
                
                # Créer canvas noir de taille cible
                canvas = np.zeros((target_h, target_w, 3), dtype=np.uint8)
                
                # Centrer l'image redimensionnée
                y_offset = (target_h - new_h) // 2
                x_offset = (target_w - new_w) // 2
                canvas[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
                
                resized_frames.append(canvas)
            
            # Déterminer layout (jusqu'à 4x5 = 20 images)
            if layout == '2x2':
                rows, cols = 2, 2
            elif layout == '3x2':
                rows, cols = 2, 3
            elif layout == '2x3':
                rows, cols = 3, 2
            elif layout == '4x2':
                rows, cols = 2, 4
            elif layout == '2x4':
                rows, cols = 4, 2
            elif layout == '3x3':
                rows, cols = 3, 3
            elif layout == '4x3':
                rows, cols = 3, 4
            elif layout == '3x4':
                rows, cols = 4, 3
            elif layout == '4x4':
                rows, cols = 4, 4
            elif layout == '5x4':
                rows, cols = 4, 5
            elif layout == '4x5':
                rows, cols = 5, 4
            elif layout == '1x4': 
                rows, cols = 1, 4
            elif layout == '4x1':
                rows, cols = 4, 1
            elif layout == '1x6':
                rows, cols = 1, 6
            elif layout == '6x1':
                rows, cols = 6, 1
            elif layout == '1x10':
                rows, cols = 1, 10
            elif layout == '10x1':
                rows, cols = 10, 1
            elif layout == '1x20':
                rows, cols = 1, 20
            elif layout == '20x1':
                rows, cols = 20, 1
            else:
                rows, cols = 2, 3  # Default 3x2 pour 6 images
            
            # Calculer dimensions finales
            strip_width = cols * target_size[0]
            strip_height = rows * target_size[1]
            
            # Ajouter espace pour timeline si demandé
            timeline_height = 40 if show_timeline else 0
            final_height = strip_height + timeline_height
            
            # Créer image composite
            composite = np.zeros((final_height, strip_width, 3), dtype=np.uint8)
            composite.fill(32)  # Fond gris foncé
            
            # Placer les frames
            frame_index = 0
            for row in range(rows):
                for col in range(cols):
                    if frame_index < len(resized_frames):
                        y_start = row * target_size[1]
                        y_end = y_start + target_size[1]
                        x_start = col * target_size[0]
                        x_end = x_start + target_size[0]
                        
                        composite[y_start:y_end, x_start:x_end] = resized_frames[frame_index]
                        
                        # Ajouter annotations si demandé
                        if show_annotations and frame_index < len(timestamps):
                            self._add_frame_annotation(composite, x_start, y_start, 
                                                     frame_index, timestamps, target_size)
                        
                        frame_index += 1
            
            # Ajouter timeline si demandé
            if show_timeline and timestamps:
                self._add_timeline(composite, timestamps, strip_height, strip_width, timeline_height)
            
            return composite
            
        except Exception as e:
            print(f"[MOTION] Erreur assemblage film strip: {e}")
            return None

    def _add_frame_annotation(self, composite: np.ndarray, x_start: int, y_start: int, 
                             frame_index: int, timestamps: List[float], frame_size: tuple):
        """Ajoute annotations sur un frame individuel"""
        try:
            # Calculer le temps relatif par rapport au frame central
            central_time = timestamps[len(timestamps)//2] if timestamps else time.time()
            frame_time = timestamps[frame_index] if frame_index < len(timestamps) else time.time()
            relative_time = frame_time - central_time
            
            # Texte d'annotation
            if relative_time < 0:
                text = f"{relative_time:.1f}s"
            elif relative_time == 0:
                text = "ENVOI"
            else:
                text = f"+{relative_time:.1f}s"
            
            # Ajouter rectangle semi-transparent pour le texte
            overlay = composite.copy()
            cv2.rectangle(overlay, (x_start + 5, y_start + 5), (x_start + 80, y_start + 25), (0, 0, 0), -1)
            cv2.addWeighted(overlay, 0.7, composite, 0.3, 0, composite)
            
            # Ajouter le texte
            cv2.putText(composite, text, (x_start + 8, y_start + 20), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            
        except Exception as e:
            print(f"[MOTION] Erreur annotation frame: {e}")

    def _add_timeline(self, composite: np.ndarray, timestamps: List[float], 
                     strip_height: int, strip_width: int, timeline_height: int):
        """Ajoute une timeline en bas de l'image composite"""
        try:
            if not timestamps:
                return
            
            # Zone timeline
            timeline_y = strip_height
            
            # Fond timeline
            cv2.rectangle(composite, (0, timeline_y), (strip_width, strip_height + timeline_height), 
                         (64, 64, 64), -1)
            
            # Ligne de temps
            timeline_y_center = timeline_y + timeline_height // 2
            cv2.line(composite, (20, timeline_y_center), (strip_width - 20, timeline_y_center), 
                    (128, 128, 128), 2)
            
            # Marqueurs temporels
            central_time = timestamps[len(timestamps)//2] if len(timestamps) > 1 else timestamps[0]
            
            for i, timestamp in enumerate(timestamps):
                relative_time = timestamp - central_time
                
                # Position X proportionnelle
                x_pos = 20 + int((i / (len(timestamps) - 1)) * (strip_width - 40)) if len(timestamps) > 1 else strip_width // 2
                
                # Marqueur
                color = (0, 255, 0) if relative_time == 0 else (255, 255, 255)
                cv2.circle(composite, (x_pos, timeline_y_center), 4, color, -1)
                
                # Label temporel
                if relative_time < 0:
                    label = f"{relative_time:.1f}s"
                elif relative_time == 0:
                    label = "SEND"
                else:
                    label = f"+{relative_time:.1f}s"
                
                cv2.putText(composite, label, (x_pos - 20, timeline_y + timeline_height - 5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)
            
        except Exception as e:
            print(f"[MOTION] Erreur timeline: {e}")

    def _run(self):
        print("[PERCEPTION] Démarrage du thread de l'agent de perception OPTIMISÉ...")
        
        # ✅ SIMPLIFIÉ: Plus de cache disque (architecture séquentielle pure)
        
        # 🛡️ PROTECTION: Vérifier que l'index webcam est valide avant de démarrer
        try:
            test_cap = cv2.VideoCapture(self.webcam_index)
            if not test_cap.isOpened():
                print(f"[ERREUR] Erreur : Impossible d'ouvrir la webcam (index {self.webcam_index}).")
                print(f"[PERCEPTION] 💡 Conseil: Vérifiez le numéro de caméra dans les paramètres")
                test_cap.release()
                self.event_queue.put(f"[ERREUR] Webcam index {self.webcam_index} non accessible.")
                self.status = "error"
                self.event_queue.put("[STATUS] inactive")
                return
            test_cap.release()
        except Exception as e:
            print(f"[ERREUR] Exception lors du test webcam: {e}")
            self.event_queue.put(f"[ERREUR] Test webcam échoué: {e}")
            self.status = "error"
            self.event_queue.put("[STATUS] inactive")
            return
        
        self.cap = cv2.VideoCapture(self.webcam_index)
        if not self.cap.isOpened():
            print(f"[ERREUR] Erreur : Impossible d'ouvrir la webcam (index {self.webcam_index}).")
            self.event_queue.put("[ERREUR] Webcam non détectée.")
            self.status = "error"
            self.event_queue.put("[STATUS] inactive")
            return
        
        # Configuration de la webcam selon mode
        surgical_mode = self.config.get('surgical_mode', False)
        
        if surgical_mode:
            # MODE CHIRURGICAL 🔬: Résolution maximale pour captures précises
            # Tente 1080p, fallback 720p si webcam ne supporte pas
            print("[SURGICAL] 🔬 Configuration résolution haute précision...")
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            # Vérifier résolution effective
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            print(f"[SURGICAL] ✅ Résolution webcam: {actual_width}x{actual_height}")
            
            if actual_width < 1920:
                print(f"[SURGICAL] ℹ️ Webcam limitée à {actual_width}x{actual_height} (1080p non supporté)")
        else:
            # MODE NORMAL: Résolution standard 640x480
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        # CRITIQUE: S'assurer qu'aucun audio n'est capturé (évite conflit TTS)
        try:
            # Vérifier si CAP_PROP_AUDIO existe dans cette version OpenCV
            if hasattr(cv2, 'CAP_PROP_AUDIO'):
                self.cap.set(cv2.CAP_PROP_AUDIO, 0)  # Désactiver audio caméra
                print("[AUDIO-SAFE] 🔇 Audio caméra explicitement désactivé")
            else:
                print("[AUDIO-SAFE] ✅ Audio non géré par OpenCV (parfait pour éviter conflits TTS)")
        except Exception as e:
            print(f"[AUDIO-SAFE] ℹ️ Configuration audio ignorée: {e}")
        
        self.status = "warming_up"
        self.event_queue.put("[STATUS] warming_up")
        print("[INIT] Initialisation de la webcam HYBRIDE (RAM réduite)...")
        
        # Test initial de capture
        ret, frame = self.cap.read()
        if ret:
            with self.frame_lock:
                self.current_frame = frame
            self.status = "active"
            self.event_queue.put("[STATUS] active")
            print("[OK] Webcam HYBRIDE active: Buffer 3 images RAM + Cache disque rotatif.")
        else:
            print("[ERREUR] Impossible de capturer une image de test.")
            self.status = "error"
            self.event_queue.put("[STATUS] inactive")
            return
        
        # Boucle principale de mise à jour continue du frame
        while self.running:
            try:
                ret, frame = self.cap.read()
                if not ret:
                    time.sleep(0.1)
                    continue

                # Mise à jour thread-safe du frame actuel (pour captures IA)
                with self.frame_lock:
                    self.current_frame = frame
                
                # PIPELINE OPTIMISÉ: JPEG encode direct dans backend thread
                # → Évite double traitement (RGB conversion + JPEG frontend)
                # → Résolution adaptative selon mode
                # → Mode Chirurgical: 720p stream pour voir détails + 1080p captures précises
                
                surgical_mode = self.config.get('surgical_mode', False)
                
                if surgical_mode:
                    # MODE CHIRURGICAL 🔬: 
                    # Stream haute résolution (720p) pour voir détails et cadrer précisément
                    # FPS limité (15 max) pour économiser CPU/RAM
                    # Captures en résolution native (1080p) @ 95% qualité
                    display_frame = self._resize_keep_aspect(frame, target_height=720)
                    stream_quality = 80  # Bonne qualité pour voir détails
                else:
                    # MODE NORMAL: Stream à résolution config (640x480 par défaut)
                    target_resolution = self.capture_resolution
                    if frame.shape[1] != target_resolution[0] or frame.shape[0] != target_resolution[1]:
                        display_frame = self._resize_keep_aspect(frame, target_width=target_resolution[0], target_height=target_resolution[1])
                    else:
                        display_frame = frame
                    stream_quality = self.config.get('stream_quality', 75)
                
                # Encode JPEG directement (pas de conversion RGB inutile)
                _, jpeg_buffer = cv2.imencode('.jpg', display_frame, [
                    cv2.IMWRITE_JPEG_QUALITY, stream_quality
                ])
                
                # Base64 encode dans le backend thread (pas dans UI thread)
                jpeg_base64 = base64.b64encode(jpeg_buffer).decode('utf-8')
                
                # ✅ ANTI-STROBOSCOPE: Vider queue si pleine pour garder image la plus récente
                try:
                    self.visual_queue.put_nowait(jpeg_base64)
                except queue.Full:
                    # Queue pleine → vider frame la plus ancienne et insérer nouvelle
                    try:
                        self.visual_queue.get_nowait()  # Supprimer frame ancienne
                        self.visual_queue.put_nowait(jpeg_base64)  # Insérer frame actuelle
                    except:
                        pass  # Échec silencieux, ne pas bloquer la boucle
                
                # Pause configurable basée sur display_fps
                target_fps = self.config.get('display_fps', 15)
                if surgical_mode:
                    target_fps = min(target_fps, 15)  # Mode chirurgical: max 15 FPS (économie CPU)
                sleep_time = 1.0 / target_fps if target_fps > 0 else 0.067
                time.sleep(sleep_time)

            except Exception as e:
                print(f"💥 ERREUR NON GÉRÉE DANS LE THREAD DE PERCEPTION : {e}")
                traceback.print_exc()
                
                # Auto-recovery au lieu d'arrêt brutal
                print("[PERCEPTION] 🔄 Tentative de récupération automatique...")
                time.sleep(2)
                
                # Réinitialiser la webcam en cas d'erreur
                try:
                    if self.cap:
                        self.cap.release()
                        time.sleep(1)
                        self.cap = cv2.VideoCapture(self.webcam_index)
                        if self.cap.isOpened():
                            # S'assurer aucun audio lors reconnexion
                            try:
                                if hasattr(cv2, 'CAP_PROP_AUDIO'):
                                    self.cap.set(cv2.CAP_PROP_AUDIO, 0)
                                    print("[AUDIO-SAFE] 🔇 Audio désactivé lors reconnexion")
                            except Exception:
                                pass  # Audio non supporté = parfait
                            print("[PERCEPTION] ✅ Webcam réinitialisée avec succès")
                        else:
                            print("[PERCEPTION] ❌ Échec réinitialisation webcam")
                            self.running = False
                    else:
                        self.running = False
                except Exception as recovery_error:
                    print(f"[PERCEPTION] ❌ Erreur récupération: {recovery_error}")
                    self.running = False

        if self.cap:
            self.cap.release()
            self.cap = None
        self.status = "inactive"
        self.event_queue.put("[STATUS] inactive")
        print("👁️ Agent de perception arrêté.")

    def start(self):
        if not self.running:
            # Gérer conflit TTS - Double protection
            
            # Méthode 1: Gestionnaire TTS classique (rétrocompatibilité)
            if TTS_MANAGER_AVAILABLE:
                print("[TTS-MANAGER] 🔧 Désactivation TTS classique...")
                if on_perception_start():
                    print("[TTS-MANAGER] ✅ TTS classique désactivé")
                else:
                    print("[TTS-MANAGER] ⚠️ Échec désactivation TTS classique")
            
            # Méthode 2: TTS sans conflit (recommandé)
            if TTS_CONFLICT_FREE_AVAILABLE:
                print("[TTS-SAFE] 🛡️ Activation mode Perception sur TTS sans conflit...")
                set_perception_active(True)
                print("[TTS-SAFE] ✅ TTS adapté pour Perception")
            
            self.running = True
            
            # Démarrer thread principal de capture
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
            
            print("[PERCEPTION] ✅ Thread capture webcam démarré")

    def stop(self):
        if self.running:
            self.running = False
            
            # Arrêter thread principal
            if self.thread:
                self.thread.join()
            
            print("[PERCEPTION] ✅ Thread capture arrêté proprement")
            
            # Restaurer TTS après arrêt - Double restauration
            
            # Méthode 1: Gestionnaire TTS classique
            if TTS_MANAGER_AVAILABLE:
                print("[TTS-MANAGER] 🔧 Restauration TTS classique...")
                if on_perception_stop():
                    print("[TTS-MANAGER] ✅ TTS classique restauré")
                else:
                    print("[TTS-MANAGER] ⚠️ Échec restauration TTS classique")
            
            # Méthode 2: TTS sans conflit
            if TTS_CONFLICT_FREE_AVAILABLE:
                print("[TTS-SAFE] 🔄 Désactivation mode Perception sur TTS sans conflit...")
                set_perception_active(False)
                print("[TTS-SAFE] ✅ TTS restauré pour usage normal")
            
            # IMPORTANT: Libérer la webcam proprement
            if hasattr(self, 'cap') and self.cap is not None:
                try:
                    self.cap.release()
                    self.cap = None
                    print("[PERCEPTION] 📷 Webcam libérée proprement")
                except Exception as e:
                    print(f"[PERCEPTION] ⚠️ Erreur libération webcam: {e}")
                
            print("[PERCEPTION] Threads arrêtés: capture principale + buffer motion")