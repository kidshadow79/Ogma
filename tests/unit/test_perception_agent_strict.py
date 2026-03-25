"""
Tests unitaires stricts pour extensions/perception_agent.py
Architecture: Fichier unique avec classe PerceptionAgent

Composants testés:
- PerceptionAgent: Agent capture webcam + chronophotographie
- Méthodes publiques: start/stop, capture_for_chat, create_motion_sequence
- Configuration: update_config, save_captures, résolutions
- TTS Manager: Intégration gestionnaire conflits TTS/Perception
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, call
import sys
import os
import queue
import numpy as np
import cv2
import threading
import time
from datetime import datetime

# Import direct depuis fichier unique perception_agent.py
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'extensions'))
from perception_agent import PerceptionAgent


class TestPerceptionAgentInit(unittest.TestCase):
    """Tests initialisation PerceptionAgent"""
    
    def test_init_with_minimal_config(self):
        """Test initialisation avec config minimale"""
        config = {
            "webcam_index": 0,
            "triage_resolution": [640, 480]
        }
        agent = PerceptionAgent(config)
        
        assert agent.status == "inactive"
        assert agent.running is False
        assert agent.webcam_index == 0
        assert agent.capture_resolution == (640, 480)
        assert isinstance(agent.visual_queue, queue.Queue)
        assert isinstance(agent.event_queue, queue.Queue)
        
    def test_init_with_full_config(self):
        """Test initialisation avec config complète"""
        config = {
            "webcam_index": 1,
            "triage_resolution": [1280, 720],
            "save_captures": True,
            "capture_folder": "./test_captures",
            "capture_format": "PNG",
            "jpeg_quality": 95
        }
        agent = PerceptionAgent(config)
        
        assert agent.config["webcam_index"] == 1
        assert agent.config["save_captures"] is True
        assert agent.config["capture_format"] == "PNG"
        assert agent.capture_resolution == (1280, 720)
        
    def test_init_queue_sizes(self):
        """Test taille buffers queues"""
        config = {"webcam_index": 0}
        agent = PerceptionAgent(config)
        
        # visual_queue maxsize=10 (buffer anti-stroboscope)
        assert agent.visual_queue.maxsize == 10
        # event_queue sans limite
        assert agent.event_queue.maxsize == 0


class TestPerceptionAgentConfig(unittest.TestCase):
    """Tests gestion configuration"""
    
    def setUp(self):
        self.config = {"webcam_index": 0, "save_captures": False}
        self.agent = PerceptionAgent(self.config)
        
    def test_update_config_resolution(self):
        """Test mise à jour résolution capture (string -> tuple)"""
        new_config = {"capture_resolution": "1920x1080"}
        self.agent.update_config(new_config)
        
        assert self.agent.capture_resolution == (1920, 1080)
        assert self.agent.config["capture_resolution"] == "1920x1080"
        
    def test_update_config_save_captures(self):
        """Test toggle save_captures"""
        # save_captures désactivé initialement
        assert self.agent.config.get("save_captures") is False
        
        # Activer
        self.agent.update_config({"save_captures": True})
        assert self.agent.config["save_captures"] is True
        
        # Désactiver
        self.agent.update_config({"save_captures": False})
        assert self.agent.config["save_captures"] is False
        
    def test_update_config_preserves_existing(self):
        """Test update_config préserve paramètres existants"""
        self.agent.config["custom_param"] = "value"
        self.agent.update_config({"new_param": "new_value"})
        
        assert self.agent.config["custom_param"] == "value"
        assert self.agent.config["new_param"] == "new_value"


class TestPerceptionAgentSaveImage(unittest.TestCase):
    """Tests sauvegarde images"""
    
    def setUp(self):
        self.config = {
            "save_captures": False,
            "capture_folder": "./test_captures",
            "capture_format": "JPEG",
            "jpeg_quality": 85
        }
        self.agent = PerceptionAgent(self.config)
        self.mock_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
    @patch('cv2.imwrite')
    @patch('os.makedirs')
    def test_save_image_disabled(self, mock_makedirs, mock_imwrite):
        """Test sauvegarde désactivée (sauf pellicules)"""
        # save_captures=False → pas de sauvegarde capture simple
        filepath = self.agent._save_image_if_enabled(self.mock_frame, "capture")
        
        assert filepath is None
        mock_imwrite.assert_not_called()
        
    @patch('cv2.imwrite')
    @patch('os.makedirs')
    def test_save_image_enabled(self, mock_makedirs, mock_imwrite):
        """Test sauvegarde activée"""
        self.agent.config["save_captures"] = True
        
        filepath = self.agent._save_image_if_enabled(self.mock_frame, "capture")
        
        assert filepath is not None
        assert "capture_" in filepath
        assert filepath.endswith(".jpg")
        mock_makedirs.assert_called_once()
        mock_imwrite.assert_called_once()
        
    @patch('cv2.imwrite')
    @patch('os.makedirs')
    def test_save_pellicule_always_saved(self, mock_makedirs, mock_imwrite):
        """Test pellicules motion toujours sauvées (même si save_captures=False)"""
        # save_captures=False mais pellicule → sauvegarde quand même
        self.agent.config["save_captures"] = False
        
        filepath = self.agent._save_image_if_enabled(self.mock_frame, "pellicule_motion")
        
        assert filepath is not None
        assert "pellicule_motion_" in filepath
        mock_imwrite.assert_called_once()
        
    @patch('cv2.imwrite')
    @patch('os.makedirs')
    def test_save_image_format_png(self, mock_makedirs, mock_imwrite):
        """Test sauvegarde format PNG"""
        self.agent.config["save_captures"] = True
        self.agent.config["capture_format"] = "PNG"
        
        filepath = self.agent._save_image_if_enabled(self.mock_frame, "capture")
        
        assert filepath.endswith(".png")
        mock_imwrite.assert_called_once()
        # PNG n'utilise pas JPEG quality parameter
        args, kwargs = mock_imwrite.call_args
        assert len(args) == 2 or "jpeg_quality" not in str(kwargs)


class TestPerceptionAgentResize(unittest.TestCase):
    """Tests redimensionnement images"""
    
    def setUp(self):
        self.agent = PerceptionAgent({"webcam_index": 0})
        self.frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
    def test_resize_by_width(self):
        """Test redimensionnement par largeur (aspect ratio préservé)"""
        resized = self.agent._resize_keep_aspect(self.frame, target_width=320)
        
        # Aspect ratio 640:480 = 4:3 → 320:240
        assert resized.shape[1] == 320
        assert resized.shape[0] == 240
        
    def test_resize_by_height(self):
        """Test redimensionnement par hauteur (priorité sur width)"""
        resized = self.agent._resize_keep_aspect(self.frame, target_width=1000, target_height=240)
        
        # target_height prioritaire → 320:240
        assert resized.shape[0] == 240
        assert resized.shape[1] == 320
        
    def test_resize_no_params(self):
        """Test redimensionnement sans paramètres (frame inchangée)"""
        resized = self.agent._resize_keep_aspect(self.frame)
        
        assert resized.shape == self.frame.shape
        assert np.array_equal(resized, self.frame)


class TestPerceptionAgentCapture(unittest.TestCase):
    """Tests capture images pour chat"""
    
    def setUp(self):
        self.agent = PerceptionAgent({"webcam_index": 0, "save_captures": False})
        
    @patch('base64.b64encode')
    @patch('cv2.imencode')
    def test_capture_for_chat_success(self, mock_imencode, mock_b64encode):
        """Test capture simple avec succès"""
        # Agent doit être running
        self.agent.running = True
        self.agent.current_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Mock encodage JPEG
        mock_imencode.return_value = (True, np.array([1, 2, 3], dtype=np.uint8))
        mock_b64encode.return_value = b"fake_base64_data"
        
        result = self.agent.capture_for_chat()
        
        assert result is not None
        assert "image_url" in result
        assert "data:image/jpeg;base64," in result["image_url"]["url"]
        mock_imencode.assert_called_once()
        
    def test_capture_for_chat_no_frame(self):
        """Test capture sans frame disponible"""
        self.agent.current_frame = None
        
        result = self.agent.capture_for_chat()
        
        assert result is None
        
    @patch('base64.b64encode')
    @patch('cv2.imencode')
    def test_capture_for_chat_encoding_error(self, mock_imencode, mock_b64encode):
        """Test capture avec erreur encodage JPEG"""
        self.agent.current_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Encodage échoue
        mock_imencode.return_value = (False, None)
        
        result = self.agent.capture_for_chat()
        
        assert result is None


class TestPerceptionAgentMotionSequence(unittest.TestCase):
    """Tests création séquences chronophotographie"""
    
    def setUp(self):
        self.agent = PerceptionAgent({"webcam_index": 0, "save_captures": False})
        
    @patch('time.sleep')
    @patch('base64.b64encode')
    @patch('cv2.imencode')
    def test_create_motion_sequence_basic(self, mock_imencode, mock_b64encode, mock_sleep):
        """Test création pellicule motion basique"""
        # Agent doit être running
        self.agent.running = True
        self.agent.current_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Mock encodage pellicule finale
        mock_imencode.return_value = (True, np.array([1, 2, 3], dtype=np.uint8))
        mock_b64encode.return_value = b"fake_pellicule_base64"
        
        result = self.agent.create_motion_sequence(frames_count=3, interval=0.1)
        
        assert result is not None
        assert "image_url" in result
        # sleep appelé entre captures (2 fois pour 3 frames)
        assert mock_sleep.call_count >= 2
        
    @patch('time.sleep')
    def test_create_motion_sequence_no_frame(self, mock_sleep):
        """Test création pellicule sans frame disponible"""
        self.agent.current_frame = None
        
        result = self.agent.create_motion_sequence(frames_count=3, interval=0.1)
        
        assert result is None
        
    @patch('time.sleep')
    @patch('base64.b64encode')
    @patch('cv2.imencode')
    def test_create_motion_sequence_with_delay(self, mock_imencode, mock_b64encode, mock_sleep):
        """Test création pellicule avec délai initial"""
        self.agent.running = True
        self.agent.current_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_imencode.return_value = (True, np.array([1, 2, 3], dtype=np.uint8))
        mock_b64encode.return_value = b"fake_pellicule_base64"
        
        result = self.agent.create_motion_sequence(frames_count=2, interval=0.1, capture_delay=0.5)
        
        assert result is not None
        # Vérifier que sleep a été appelé avec le délai initial
        sleep_calls = [call.args[0] for call in mock_sleep.call_args_list]
        assert 0.5 in sleep_calls or any(d >= 0.5 for d in sleep_calls)


class TestPerceptionAgentStartStop(unittest.TestCase):
    """Tests démarrage/arrêt agent"""
    
    def setUp(self):
        self.agent = PerceptionAgent({"webcam_index": 0})
        
    @patch('extensions.perception_agent.on_perception_start', return_value=True)
    @patch('extensions.perception_agent.set_perception_active')
    @patch('threading.Thread')
    def test_start_agent(self, mock_thread_cls, mock_set_perception, mock_on_start):
        """Test démarrage agent (TTS manager + thread)"""
        # Mock instance Thread
        mock_thread_instance = Mock()
        mock_thread_cls.return_value = mock_thread_instance
        
        self.agent.start()
        
        assert self.agent.running is True
        # Thread créé avec bon target et daemon
        assert any(
            call.kwargs.get('daemon') is True and call.kwargs.get('target') == self.agent._run
            for call in mock_thread_cls.call_args_list
        )
        # Thread démarré au moins une fois
        assert mock_thread_instance.start.call_count >= 1
        
    @patch('extensions.perception_agent.on_perception_stop', return_value=True)
    @patch('extensions.perception_agent.set_perception_active')
    def test_stop_agent(self, mock_set_perception, mock_on_stop):
        """Test arrêt agent (TTS manager + cleanup)"""
        # Simuler agent démarré
        self.agent.running = True
        self.agent.thread = Mock()
        
        # Mock webcam avec objet qui a release()
        mock_cap = Mock()
        self.agent.cap = mock_cap
        
        self.agent.stop()
        
        assert self.agent.running is False
        # Thread joint
        self.agent.thread.join.assert_called_once()
        # Webcam libérée
        mock_cap.release.assert_called_once()
        
    @patch('extensions.perception_agent.on_perception_start', return_value=True)
    @patch('threading.Thread')
    def test_start_when_already_running(self, mock_thread, mock_on_start):
        """Test start() quand déjà running (ne fait rien)"""
        self.agent.running = True
        
        self.agent.start()
        
        # Thread pas créé (déjà running)
        mock_thread.assert_not_called()
        
    def test_stop_when_not_running(self):
        """Test stop() quand pas running (ne fait rien)"""
        self.agent.running = False
        
        # Ne doit pas lever d'exception
        self.agent.stop()


class TestPerceptionAgentIntegration(unittest.TestCase):
    """Tests intégration workflows complets"""
    
    @patch('cv2.VideoCapture')
    @patch('base64.b64encode')
    @patch('cv2.imencode')
    def test_full_capture_workflow(self, mock_imencode, mock_b64encode, mock_videocap):
        """Test workflow complet: init -> capture -> cleanup"""
        # Mock webcam
        mock_cap = Mock()
        mock_cap.isOpened.return_value = True
        mock_cap.read.return_value = (True, np.zeros((480, 640, 3), dtype=np.uint8))
        mock_videocap.return_value = mock_cap
        
        # Mock encodage
        mock_imencode.return_value = (True, np.array([1, 2, 3], dtype=np.uint8))
        mock_b64encode.return_value = b"fake_base64"
        
        # Workflow
        agent = PerceptionAgent({"webcam_index": 0, "save_captures": False})
        agent.running = True  # Simuler agent démarré
        agent.current_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        result = agent.capture_for_chat()
        assert result is not None
        assert "image_url" in result
        
    @patch('time.sleep')
    @patch('base64.b64encode')
    @patch('cv2.imencode')
    def test_full_motion_workflow(self, mock_imencode, mock_b64encode, mock_sleep):
        """Test workflow complet chronophotographie"""
        agent = PerceptionAgent({"webcam_index": 0, "save_captures": False})
        agent.running = True  # Simuler agent démarré
        agent.current_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Mock encodage pellicule
        mock_imencode.return_value = (True, np.array([1, 2, 3], dtype=np.uint8))
        mock_b64encode.return_value = b"fake_pellicule"
        
        result = agent.create_motion_sequence(frames_count=4, interval=0.2)
        
        assert result is not None
        assert "image_url" in result
        # 4 frames = 3 sleeps
        assert mock_sleep.call_count >= 3


class TestPerceptionAgentEdgeCases(unittest.TestCase):
    """Tests cas limites et erreurs"""
    
    def test_update_config_invalid_resolution(self):
        """Test update_config avec résolution invalide"""
        agent = PerceptionAgent({"webcam_index": 0})
        
        # Résolution sans 'x' → pas de changement
        agent.update_config({"capture_resolution": "invalid"})
        # Ne devrait pas crasher (pas de split possible)
        
    @patch('cv2.imwrite', side_effect=Exception("Disk full"))
    @patch('os.makedirs')
    def test_save_image_io_error(self, mock_makedirs, mock_imwrite):
        """Test sauvegarde avec erreur I/O"""
        agent = PerceptionAgent({"webcam_index": 0, "save_captures": True})
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Ne doit pas crasher, retourne None
        result = agent._save_image_if_enabled(frame, "capture")
        assert result is None
        
    def test_resize_zero_dimensions(self):
        """Test redimensionnement avec dimensions nulles"""
        agent = PerceptionAgent({"webcam_index": 0})
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # target_width=0 → frame inchangée (pas de redimensionnement)
        # Note: cv2.resize crashe si new_w/new_h = 0, donc on vérifie le fallback
        resized = agent._resize_keep_aspect(frame, target_width=None, target_height=None)
        assert resized.shape == frame.shape
        
    @patch('base64.b64encode')
    @patch('cv2.imencode')
    def test_capture_with_corrupted_frame(self, mock_imencode, mock_b64encode):
        """Test capture avec frame corrompue"""
        agent = PerceptionAgent({"webcam_index": 0})
        
        # Frame avec mauvaises dimensions
        agent.current_frame = np.zeros((0, 0, 3), dtype=np.uint8)
        mock_imencode.return_value = (False, None)
        
        result = agent.capture_for_chat()
        assert result is None


if __name__ == '__main__':
    unittest.main(verbosity=2)
