# extensions/perception_ui.py

"""
Interface utilisateur pour l'extension Perception
Connecte le backend PerceptionAgent à l'interface NiceGUI
"""

import asyncio
import threading
import time
import base64
from typing import Optional, Dict, Any
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    cv2 = None
    CV2_AVAILABLE = False
import numpy as np

from .perception_agent import PerceptionAgent

class PerceptionUI:
    """Gestionnaire UI pour l'extension Perception"""

    def __init__(self):
        self.perception_agent: Optional[PerceptionAgent] = None
        self.is_enabled = False
        self.ui_elements = {}
        self.webcam_display = None
        self.status_dot = None
        self.current_config = {
            'webcam_index': 0,
            'capture_resolution': '640x480',
            'use_native_resolution': False,  # Utiliser résolution native de la source (pas de resize)
            'jpeg_quality': 85,
            'display_fps': 15,  # FPS affichage stream
            # Paramètres stream optimisé
            'stream_quality': 75,  # Qualité JPEG stream (70-85% optimal)
            'surgical_mode': False,  # Mode Chirurgical: haute précision captures
            # Paramètres Vision Avancée
            'enable_depth': True,    # Activer Depth Anything V2
            'enable_sam': False,     # Activer SAM 2 (Segment Anything)
            # Paramètres capture
            'capture_delay': 0.0,  # Délai avant capture (simple ou 1ère image chrono)
            'save_captures': False,  # Sauvegarder captures simples
            'capture_folder': './captures',
            'capture_format': 'JPEG',
            # Paramètres chronophotographie
            'motion_capture_enabled': False,
            'motion_frames_after': 6,   # Nombre d'images chronophotographie
            'motion_interval': 0.5,     # Intervalle entre images (secondes)
            'motion_layout': '3x2',     # Grille 3×2 optimale pour 6 images
            'motion_timeline': False,   # Timeline sur les images
            'motion_annotations': False, # Annotations temps sur les images
            # Parametres MODE LIVE (veille sensorielle proactive)
            'live_enabled': False,           # Active la veille sensorielle
            'live_autostart': False,         # Demarrer la veille automatiquement au boot d'OGMA
            'live_cache_size': 15,           # Images dans le cache tournant (@1fps)
            'live_inactivity_delay': 20,     # Secondes d'inactivite avant declenchement possible
            'live_cooldown': 30,             # Secondes minimum entre deux declenchements
            'live_motion_threshold': 500,    # Pixels changes (frame 320x240) pour declencher
            'live_stimuli_only': False,      # Si True: pas d'image a chaque message, seulement via stimulus Live
            'live_triage_prompt': (
                "Tu disposes d'une veille visuelle autonome (Mode Live). Tu viens de recevoir une "
                "chronophotographie (plusieurs images successives) de ce qui se passe devant ta webcam. "
                "Tu es naturellement curieuse et attentive, mais tu n'interviens pas pour n'importe quoi. "
                "Reponds UNIQUEMENT par OUI ou NON : "
                "OUI si la scene contient quelque chose de notable : une action, une expression, "
                "un changement de situation, quelque chose qui t'interpelle vraiment. "
                "NON si c'est un micro-mouvement banal (ajustement de position, legere rotation de tete, "
                "main qui bouge brievement), si la personne est immobile et concentree, ou si la scene "
                "est essentiellement la meme que d'habitude. "
                "Tu interviens quand ca vaut vraiment la peine, pas a chaque petit geste."
            )
        }

        # Instance de veille sensorielle (MODE LIVE)
        self.live_watcher = None

        # Cache du dernier scan de cameras (evite de rouvrir la webcam active)
        self._cached_cameras: Dict[int, str] = {}

        # Charger configuration depuis settings.json
        self.load_config_from_settings()

    def load_config_from_settings(self):
        """Charge la configuration depuis settings.json"""
        try:
            import json
            import os

            # Chemin vers le fichier settings.json
            settings_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'settings.json')

            if os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)

                # 🔧 CORRECTION: Charger depuis extensions.perception (cohérence avec sauvegarde)
                perception_config = settings.get('extensions', {}).get('perception', {})
                
                # FALLBACK: Si pas trouvé, essayer l'ancien emplacement perception_agent  
                if not perception_config:
                    perception_config = settings.get('perception_agent', {})
                    if perception_config:
                        print(f"[PERCEPTION-UI] ⚠️ Configuration trouvée dans perception_agent (ancienne version)")
                
                if perception_config:
                    # Mapper TOUS les paramètres (pas seulement webcam_index et fps_limit)
                    for key, value in perception_config.items():
                        if key in self.current_config:
                            # Gérer triage_resolution spécialement (peut être liste ou string)
                            if key == 'triage_resolution':
                                if isinstance(value, list) and len(value) >= 2:
                                    self.current_config[key] = f"{value[0]}x{value[1]}"
                                elif isinstance(value, str):
                                    self.current_config[key] = value
                            else:
                                self.current_config[key] = value

                    print(f"[PERCEPTION-UI] ✅ Configuration chargée depuis settings.json: {len(perception_config)} paramètres")
                    print(f"[PERCEPTION-UI] 📋 save_captures = {self.current_config.get('save_captures', False)}")
                else:
                    print(f"[PERCEPTION-UI] ℹ️ Pas de config perception dans settings.json, utilisation des défauts")
        except Exception as e:
            print(f"[PERCEPTION-UI] ❌ Erreur chargement config: {e}")

    def get_current_config(self) -> Dict[str, Any]:
        """Retourne la configuration actuelle"""
        return self.current_config.copy()

    def _save_config_to_settings(self):
        """Sauvegarde la configuration dans settings.json"""
        try:
            import json
            import os
            
            # Chemin vers le fichier settings.json
            settings_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'settings.json')
            
            # Charger settings existants
            if os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            else:
                settings = {}
            
            # Mettre à jour la section extensions.perception
            if 'extensions' not in settings:
                settings['extensions'] = {}
            settings['extensions']['perception'] = self.current_config
            
            # Sauvegarder
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            
            print(f"[PERCEPTION-UI] Configuration sauvée dans settings.json")
            
        except Exception as e:
            print(f"[ERREUR] Échec sauvegarde settings.json: {e}")

    def update_config(self, new_config: Dict[str, Any]):
        """Met à jour la configuration"""
        # Memoriser l'index camera AVANT mise a jour pour detecter un vrai changement
        old_webcam_index = self.current_config.get('webcam_index')
        self.current_config.update(new_config)
        print(f"[PERCEPTION-UI] Configuration mise à jour: {new_config}")

        # Sauvegarder dans settings.json
        self._save_config_to_settings()

        # Propager la configuration à l'agent s'il existe
        if self.perception_agent:
            self.perception_agent.update_config(self.current_config)

        # Propager la configuration au LiveWatcher s'il tourne
        if self.live_watcher:
            self.live_watcher.update_config(self.current_config)

        # Redémarrer l'agent UNIQUEMENT si l'index camera a reellement change
        # (avant: 'webcam_index' in new_config etait toujours vrai en sauvegarde globale,
        #  ce qui tuait le Mode Live a chaque clic sur Sauvegarder)
        new_webcam_index = self.current_config.get('webcam_index')
        if self.perception_agent and self.is_enabled and new_webcam_index != old_webcam_index:
            self.restart_perception_agent()

    def start_perception(self):
        """Démarre l'agent de perception"""
        # ✅ GARDE-FOU: Ne pas redémarrer si déjà actif
        if self.perception_agent:
            print("[PERCEPTION-UI] ⚠️ Agent déjà actif - skip redémarrage (protection double-start)")
            return True  # Déjà actif = succès

        try:
            # Créer l'agent avec la configuration actuelle COMPLÈTE
            agent_config = self.current_config.copy()
            # S'assurer que capture_resolution est au bon format (tuple)
            agent_config['triage_resolution'] = self._parse_resolution(
                self.current_config.get('capture_resolution', '640x480')
            )

            self.perception_agent = PerceptionAgent(agent_config)
            self.perception_agent.start()
            self.is_enabled = True

            # 🎵 NOTIFICATION TTS: Perception active
            self._notify_tts_perception_state(True)

            print("[PERCEPTION-UI] ✅ Extension démarrée")
            self.update_status_indicator('active')
            return True

        except Exception as e:
            print(f"[PERCEPTION-UI] ❌ Erreur démarrage: {e}")
            self.update_status_indicator('error')
            return False

    def stop_perception(self):
        """Arrête l'agent de perception"""
        # Arreter d'abord la veille live: elle depend du flux de l'agent
        if self.live_watcher:
            self.stop_live_mode()

        if not self.perception_agent:
            return

        try:
            self.perception_agent.stop()
            self.perception_agent = None
            self.is_enabled = False

            # 🎵 NOTIFICATION TTS: Perception inactive
            self._notify_tts_perception_state(False)

            print("[PERCEPTION-UI] ⏹️ Extension arrêtée")
            self.update_status_indicator('inactive')

        except Exception as e:
            print(f"[PERCEPTION-UI] ❌ Erreur arrêt: {e}")

    def restart_perception_agent(self):
        """Redémarre l'agent avec la nouvelle configuration"""
        if self.is_enabled:
            print("[PERCEPTION-UI] 🔄 Redémarrage agent...")
            # Memoriser si la veille tournait: stop_perception() l'arrete aussi
            was_live = self.is_live_active()
            self.stop_perception()
            time.sleep(0.5)  # Petite pause
            self.start_perception()
            # Restaurer la veille si elle etait active avant le restart
            if was_live:
                print("[PERCEPTION-UI] Restauration du Mode Live apres restart agent")
                self.start_live_mode()

    def request_capture(self):
        """Demande une capture (wrapper pour capture_for_chat)"""
        return self.capture_for_chat()

    def capture_for_chat(self) -> Optional[Dict[str, Any]]:
        """Capture une image pour le chat (mode simple ou séquence mouvement)"""
        if not self.perception_agent:
            print("[PERCEPTION-UI] ⚠️ Agent non démarré")
            return None

        # Vérifier le mode de capture
        if self.current_config.get('motion_capture_enabled', False):
            return self.create_motion_sequence()
        else:
            return self.perception_agent.capture_for_chat()

    def create_motion_sequence(self) -> Optional[Dict[str, Any]]:
        """Crée une chronophotographie selon configuration"""
        if not self.perception_agent or not self.is_enabled:
            print("[MOTION] Agent de perception non disponible")
            return None
            
        try:
            print("[MOTION] 🎬 Création chronophotographie...")
            return self.perception_agent.create_motion_sequence(
                frames_count=self.current_config.get('motion_frames_after', 6),
                interval=self.current_config.get('motion_interval', 0.5),
                capture_delay=self.current_config.get('capture_delay', 0.0),
                layout=self.current_config.get('motion_layout', '3x2'),
                show_timeline=self.current_config.get('motion_timeline', False),
                show_annotations=self.current_config.get('motion_annotations', False)
            )
        except Exception as e:
            print(f"[MOTION] Erreur création séquence: {e}")
            return None

    def start_live_mode(self) -> bool:
        """
        Demarre la veille sensorielle (MODE LIVE).
        Necessite que l'agent webcam tourne: le demarre si besoin.
        """
        # Le mode live a besoin du flux webcam: demarrer la perception si inactive
        if not self.perception_agent:
            print("[LIVE] Agent perception inactif - demarrage automatique pour le mode Live")
            if not self.start_perception():
                print("[LIVE] ERR Impossible de demarrer la perception, mode Live annule")
                return False

        if self.live_watcher and self.live_watcher.running:
            print("[LIVE] Veille deja active - skip")
            return True

        from .perception_agent import LiveWatcher
        self.live_watcher = LiveWatcher(self.perception_agent, self.current_config.copy())
        self.live_watcher.start()
        self.current_config['live_enabled'] = True
        self._save_config_to_settings()
        print("[LIVE] OK Mode Live demarre")
        return True

    def stop_live_mode(self):
        """Arrete la veille sensorielle (MODE LIVE)."""
        if self.live_watcher:
            self.live_watcher.stop()
            self.live_watcher = None
        self.current_config['live_enabled'] = False
        self._save_config_to_settings()
        print("[LIVE] OK Mode Live arrete")

    def is_live_active(self) -> bool:
        """Vrai si la veille sensorielle tourne."""
        return self.live_watcher is not None and self.live_watcher.running

    def get_pending_live_trigger(self):
        """
        Recupere un declenchement live en attente (chronophoto prete pour triage).
        Non bloquant. Retourne le dict image ou None. A appeler par le hook UI (polling).
        """
        if not self.live_watcher:
            return None
        return self.live_watcher.get_pending_trigger()

    def notify_user_message(self):
        """Signale un message utilisateur ENVOYE (reset du timer d'inactivite live)."""
        if self.live_watcher:
            self.live_watcher.notify_user_message()

    def get_live_triage_prompt(self) -> str:
        """Retourne le prompt de triage configurable."""
        return self.current_config.get('live_triage_prompt', '')

    def test_camera(self, camera_index: int = None) -> bool:
        """Teste une caméra spécifique"""
        idx = camera_index if camera_index is not None else self.current_config['webcam_index']

        try:
            cap = cv2.VideoCapture(idx)
            if not cap.isOpened():
                print(f"[PERCEPTION-UI] ❌ Caméra {idx} non accessible")
                return False

            ret, frame = cap.read()
            cap.release()

            if ret:
                print(f"[PERCEPTION-UI] ✅ Caméra {idx} testée avec succès")
                return True
            else:
                print(f"[PERCEPTION-UI] ❌ Caméra {idx} ne peut pas capturer")
                return False

        except Exception as e:
            print(f"[PERCEPTION-UI] ❌ Erreur test caméra {idx}: {e}")
            return False

    def detect_available_cameras(self) -> Dict[int, str]:
        """Détecte les caméras disponibles avec backends multiples"""
        # GARDE-FOU: si l'agent tourne deja, il detient un handle sur la webcam.
        # Rouvrir des VideoCapture (meme sur d'autres index) perturbe le flux MSMF
        # et fait disparaitre la preview. On renvoie donc le dernier scan connu,
        # complete au minimum par la camera active.
        if self.perception_agent:
            active_index = self.current_config.get('webcam_index', 0)
            cameras = dict(self._cached_cameras)
            if active_index not in cameras:
                cameras[active_index] = f"Caméra {active_index}"
            print(f"[PERCEPTION-UI] Agent actif - scan camera ignore (preview protegee), {len(cameras)} en cache")
            return cameras

        available_cameras = {}

        # Tester avec DSHOW (DirectShow - Windows par défaut)
        for i in range(10):
            try:
                cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
                if cap.isOpened():
                    ret, _ = cap.read()
                    if ret:
                        available_cameras[i] = f"Caméra {i}"
                        print(f"[PERCEPTION-UI] ✅ Caméra {i} détectée (DSHOW)")
                cap.release()
            except:
                pass
        
        # Si peu de caméras trouvées, essayer MSMF (Media Foundation)
        # OBS Virtual Camera peut être visible uniquement en MSMF
        if len(available_cameras) < 3:
            print("[PERCEPTION-UI] 🔄 Tentative détection MSMF (OBS Virtual Camera)...")
            for i in range(10):
                if i not in available_cameras:
                    try:
                        cap = cv2.VideoCapture(i, cv2.CAP_MSMF)
                        if cap.isOpened():
                            ret, _ = cap.read()
                            if ret:
                                available_cameras[i] = f"Caméra {i} (MSMF)"
                                print(f"[PERCEPTION-UI] ✅ Caméra {i} détectée (MSMF)")
                        cap.release()
                    except:
                        pass

        print(f"[PERCEPTION-UI] 📹 {len(available_cameras)} caméra(s) détectée(s)")
        # Memoriser le scan pour les prochaines ouvertures avec agent actif
        if available_cameras:
            self._cached_cameras = dict(available_cameras)
        return available_cameras

    def update_status_indicator(self, status: str):
        """Met à jour l'indicateur de statut"""
        if not self.status_dot:
            return

        colors = {
            'inactive': '#dc2626',  # Rouge
            'active': '#22c55e',    # Vert
            'error': '#ef4444',     # Rouge clair
            'warning': '#f59e0b'    # Orange
        }

        color = colors.get(status, '#666666')

        try:
            self.status_dot.style(f'''
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: {color};
                box-shadow: 0 0 4px {color}66;
            ''')
        except Exception as e:
            # ✅ PROTECTION UI: Ne pas propager l'exception si élément détruit
            # Ceci évite la boucle infernale de reconnexion forcée
            print(f"[PERCEPTION-UI] ⚠️ Status update skip (UI détruit/déconnecté): {e}")
            self.status_dot = None  # Nettoyer référence invalide

    def register_ui_elements(self, webcam_display=None, status_dot=None):
        """Enregistre les éléments UI pour les mises à jour"""
        self.webcam_display = webcam_display
        self.status_dot = status_dot

    def _parse_resolution(self, res_str: str) -> tuple:
        """Parse une chaîne de résolution '640x480' en tuple (640, 480)"""
        try:
            parts = res_str.split('x')
            return (int(parts[0]), int(parts[1]))
        except:
            return (640, 480)  # Défaut

    def get_status(self) -> Dict[str, Any]:
        """Retourne le statut actuel de l'extension"""
        return {
            'enabled': self.is_enabled,
            'agent_status': self.perception_agent.status if self.perception_agent else 'inactive',
            'config': self.current_config,
            'webcam_active': self.display_running
        }

    def _notify_tts_perception_state(self, perception_active: bool):
        """Notifie au système TTS l'état de Perception"""
        try:
            # Importer le gestionnaire audio OGMA (wrapper)
            import sys
            import os
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
            
            from audio_manager_wrapper import get_audio_manager
            audio_mgr = get_audio_manager()
            
            if hasattr(audio_mgr, 'set_perception_mode'):
                audio_mgr.set_perception_mode(perception_active)
                state_text = "ACTIVE" if perception_active else "INACTIVE"
                print(f"[PERCEPTION-UI] 🎵 TTS notifié: Perception {state_text}")
            else:
                print("[PERCEPTION-UI] ⚠️ Audio manager sans support perception_mode")
                
        except Exception as e:
            print(f"[PERCEPTION-UI] ❌ Erreur notification TTS: {e}")


# Instance globale pour l'interface Perception
_perception_ui_instance: Optional[PerceptionUI] = None

def get_perception_ui() -> PerceptionUI:
    """Retourne l'instance globale de PerceptionUI"""
    global _perception_ui_instance
    if _perception_ui_instance is None:
        _perception_ui_instance = PerceptionUI()
    return _perception_ui_instance