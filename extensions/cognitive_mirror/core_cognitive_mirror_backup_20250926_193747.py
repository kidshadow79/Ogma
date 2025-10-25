# 🧠 Cognitive Mirror - Moteur Principal

"""
Moteur central de l'extension Cognitive Mir            # Initialisation observateur de réflexion
            self.conversation_manager = ConversationManager(
                chat_controller=self.chat_controller,
                archiviste_controller=self.archiviste_controller
            )
            self.conversation_manager.on_message_received = self._on_message_receivedrchestre la détection d'inactivité, les sessions réflexives et l'interface utilisateur
"""

import asyncio
import threading
import time
from typing import Optional, Dict, Any, Callable
from datetime import datetime
import uuid

from .config import get_config, CognitiveMirrorConfig

class CognitiveMirrorCore:
    """
    Moteur principal extension Cognitive Mirror
    
    Pattern singleton pour cohérence avec architecture OGMA
    Responsabilités:
    - Orchestration détection inactivité
    - Coordination sessions réflexives
    - Gestion état extension (ON/OFF)
    - Interface avec pipeline OGMA
    """
    
    def __init__(self, chat_controller, archiviste_controller, memory_manager, ui_container=None):
        """
        Initialise le moteur avec les dépendances OGMA
        
        Args:
            chat_controller: Instance AIController (IA principale)
            archiviste_controller: Instance AIController (Archiviste) 
            memory_manager: Instance MemoryManager OGMA
            ui_container: Container NiceGUI pour overlay (optionnel)
        """
        self.config = get_config()
        
        # Dépendances OGMA
        self.chat_controller = chat_controller
        self.archiviste_controller = archiviste_controller
        self.memory_manager = memory_manager
        self.ui_container = ui_container
        
        # Composants extension (initialisés dans initialize())
        self.inactivity_detector = None
        self.conversation_manager = None  # Changé de reflection_manager
        self.ui_components = None
        self.memory_integration = None
        
        # État interne
        self.is_initialized = False
        self.active_reflection_session = None
        self.last_reflection_context = None
        self.session_id = None
        
        # Threading
        self.background_thread = None
        self.shutdown_event = threading.Event()
        
        # Callbacks pour intégration OGMA
        self.on_reflection_start = None
        self.on_reflection_end = None
        self.on_state_change = None
        self.on_external_settings_change = None  # Callback vers OGMA pour événements spéciaux
        
        print(f"[COGNITIVE-MIRROR] 🧠 Moteur initialisé (état: {'ON' if self.is_enabled() else 'OFF'})")
    
    def initialize(self) -> bool:
        """
        Initialisation complète des composants
        
        Returns:
            bool: True si initialisation réussie
        """
        try:
            print("[COGNITIVE-MIRROR] 🔧 Initialisation des composants...")
            
            # Import dynamique pour éviter les erreurs circulaires
            from .inactivity_detector import InactivityDetector
            from .reflection_manager import ConversationManager
            from .ui_components import CognitiveMirrorUI
            from .memory_integration import MemoryIntegration
            
            # Initialisation détecteur d'inactivité
            self.inactivity_detector = InactivityDetector(
                config=self.config,
                on_inactivity_detected=self._on_inactivity_detected,
                on_activity_resumed=self._on_activity_resumed
            )
            
            # Initialisation observateur de réflexion (philosophie OGMA)
            self.conversation_manager = ConversationManager(
                chat_controller=self.chat_controller,
                archiviste_controller=self.archiviste_controller
            )
            self.conversation_manager.on_message_received = self._on_message_received
            
            # Initialisation interface utilisateur
            self.ui_components = CognitiveMirrorUI(
                config=self.config,
                ui_container=self.ui_container,
                on_toggle_extension=self._on_toggle_extension,
                on_settings_change=self._on_settings_change
            )
            
            # Initialisation intégration mémoire
            self.memory_integration = MemoryIntegration(
                memory_manager=self.memory_manager,
                config=self.config
            )
            
            # Démarrage thread de surveillance
            self._start_background_thread()
            
            self.is_initialized = True
            print("[COGNITIVE-MIRROR] ✅ Tous les composants initialisés")
            return True
            
        except Exception as e:
            print(f"[COGNITIVE-MIRROR] ❌ Erreur initialisation: {e}")
            return False
    
    def is_ready(self) -> bool:
        """Vérifie si l'extension est prête à fonctionner"""
        return (self.is_initialized and 
                self.inactivity_detector and 
                self.conversation_manager and 
                self.ui_components)
    
    def is_enabled(self) -> bool:
        """Vérifie si l'extension est activée"""
        return self.config.is_enabled()
    
    def toggle_enabled(self) -> bool:
        """
        Bascule l'état ON/OFF de l'extension
        
        Returns:
            bool: Nouvel état
        """
        new_state = self.config.toggle_enabled()
        
        # Notification changement d'état
        if self.on_state_change:
            self.on_state_change(new_state)
        
        # Gestion du monitoring selon l'état
        if new_state:
            # Extension activée : nettoyer l'état et redémarrer
            print("[COGNITIVE-MIRROR] 🧹 Nettoyage état précédent...")
            if self.active_reflection_session:
                self.stop_reflection_session("reactivation")
            
            # Vérification de l'état prêt
            ready_state = self.is_ready()
            print(f"[COGNITIVE-MIRROR] 🔍 État is_ready(): {ready_state}")
            
            if ready_state:
                self.start_inactivity_monitoring()
                print("[COGNITIVE-MIRROR] ✅ Surveillance démarrée avec succès")
            else:
                print("[COGNITIVE-MIRROR] ⚠️ Extension pas prête pour surveillance")
                print(f"[COGNITIVE-MIRROR] 🔧 Debug: initialized={self.is_initialized}, detector={self.inactivity_detector is not None}, observer={self.conversation_manager is not None}, ui={self.ui_components is not None}")
        else:
            # Extension désactivée : tout arrêter
            self.stop_inactivity_monitoring()
            if self.active_reflection_session:
                self.stop_reflection_session("deactivation")
        
        # Mise à jour UI
        if self.ui_components:
            self.ui_components.update_toggle_state(new_state)
        
        print(f"[COGNITIVE-MIRROR] 🔄 Extension {'activée' if new_state else 'désactivée'}")
        return new_state
    
    def start_inactivity_monitoring(self):
        """Démarre la surveillance d'inactivité (appelé après envoi message utilisateur)"""
        if not self.is_enabled() or not self.is_ready():
            return
        
        if self.inactivity_detector:
            self.inactivity_detector.start_monitoring()
            print("[COGNITIVE-MIRROR] 👀 Surveillance d'inactivité démarrée")
    
    def stop_inactivity_monitoring(self):
        """Arrête la surveillance d'inactivité"""
        if self.inactivity_detector:
            self.inactivity_detector.stop_monitoring()
    
    def start_reflection_session(self, trigger_type: str = "inactivity"):
        """
        Démarre une session de réflexion IA-Archiviste
        
        Args:
            trigger_type: Type de déclenchement ("inactivity", "manual", "timeout")
        """
        if not self.is_enabled() or not self.is_ready():
            return False
        
        if self.active_reflection_session:
            print("[COGNITIVE-MIRROR] ⚠️ Session réflexive déjà active")
            return False
        
        try:
            # Génération ID session unique
            self.session_id = f"reflection_{int(time.time())}_{uuid.uuid4().hex[:8]}"
            
            # Arrêt surveillance inactivité
            self.stop_inactivity_monitoring()
            
            # Affichage overlay UI
            if self.ui_components:
                self.ui_components.show_reflection_overlay()
            
            # Démarrage observation réflexive (NOUVELLE APPROCHE) avec ID synchronisé
            returned_session_id = self.conversation_manager.start_conversation(
                trigger_type=trigger_type,
                conversation_context=self._get_conversation_context(),
                session_id=self.session_id  # Passer l'ID généré par le core
            )
            
            # Vérifier que l'ID retourné correspond bien à celui envoyé
            self.active_reflection_session = returned_session_id
            if returned_session_id != self.session_id:
                print(f"[COGNITIVE-MIRROR] ⚠️ ID session mismatch: core={self.session_id}, observer={returned_session_id}")
                # Utiliser l'ID retourné par l'observer pour cohérence
                self.session_id = returned_session_id
            
            # Marquer la session réflexive comme active pour le détecteur d'inactivité
            if self.inactivity_detector:
                self.inactivity_detector.set_reflection_session_active(True)
            
            # Callback notification
            if self.on_reflection_start:
                self.on_reflection_start(self.session_id, trigger_type)
            
            print(f"[COGNITIVE-MIRROR] 🧠 Session réflexive démarrée (ID: {self.session_id})")
            return True
            
        except Exception as e:
            print(f"[COGNITIVE-MIRROR] ❌ Erreur démarrage réflexion: {e}")
            self.active_reflection_session = None
            return False
    
    def stop_reflection_session(self, reason: str = "user_return"):
        """
        Arrête la session de réflexion en cours
        
        Args:
            reason: Raison d'arrêt ("user_return", "timeout", "manual", "error")
        """
        if not self.active_reflection_session:
            return
        
        try:
            # Arrêt observation réflexive
            self.conversation_manager.stop_conversation(reason)
            
            # Sauvegarde contexte simple
            self.last_reflection_context = {"reason": reason, "session_id": self.session_id}
            
            # Intégration mémoire (souvenir REF) - simplifiée
            if self.memory_integration:
                try:
                    self.memory_integration.save_reflection_memory(
                        session_id=self.session_id,
                        reflection_context=self.last_reflection_context,
                        conversation_context=self._get_conversation_context()
                    )
                except Exception as e:
                    print(f"[COGNITIVE-MIRROR] ⚠️ Erreur sauvegarde mémoire: {e}")
            
            # Masquage overlay UI
            if self.ui_components:
                self.ui_components.hide_reflection_overlay()
            
            # Marquer que la session réflexive n'est plus active
            if self.inactivity_detector:
                self.inactivity_detector.set_reflection_session_active(False)
            
            # Callback notification
            if self.on_reflection_end:
                self.on_reflection_end(self.session_id, reason, self.last_reflection_context)
            
            print(f"[COGNITIVE-MIRROR] ✅ Session réflexive terminée (raison: {reason})")
            
        except Exception as e:
            print(f"[COGNITIVE-MIRROR] ❌ Erreur arrêt réflexion: {e}")
        
        finally:
            self.active_reflection_session = None
            self.session_id = None
    
    def get_reflection_context(self) -> Optional[str]:
        """
        Retourne le contexte de réflexion pour enrichissement conversation
        
        Returns:
            str: Résumé dernière réflexion ou None
        """
        return self.last_reflection_context
    
    def get_ui_components(self) -> Dict[str, Any]:
        """
        Retourne les composants UI pour intégration OGMA
        
        Returns:
            dict: Bouton toggle, overlay, paramètres
        """
        if self.ui_components:
            return self.ui_components.get_components()
        return {}
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut détaillé de l'extension
        
        Returns:
            dict: Statut complet
        """
        return {
            "available": self.is_ready(),
            "enabled": self.is_enabled(),
            "initialized": self.is_initialized,
            "active_reflection": self.active_reflection_session is not None,
            "session_id": self.session_id,
            "last_reflection_time": getattr(self, 'last_reflection_time', None),
            "monitoring_inactivity": self.inactivity_detector.is_monitoring() if self.inactivity_detector else False,
            "config": {
                "no_message_delay": self.config.get("trigger_delay_no_message"),
                "no_typing_delay": self.config.get("trigger_delay_no_typing"),
                "max_duration": self.config.get("max_reflection_duration")
            }
        }
    
    def set_callbacks(self, on_reflection_start=None, on_reflection_end=None, on_state_change=None, on_external_settings_change=None):
        """Configure les callbacks pour intégration OGMA"""
        self.on_reflection_start = on_reflection_start
        self.on_reflection_end = on_reflection_end
        self.on_state_change = on_state_change
        self.on_external_settings_change = on_external_settings_change
    
    def cleanup(self):
        """Nettoyage et fermeture propre de l'extension"""
        print("[COGNITIVE-MIRROR] 🔄 Nettoyage extension...")
        
        # Signal arrêt
        self.shutdown_event.set()
        
        # Arrêt session active
        if self.active_reflection_session:
            self.stop_reflection_session(reason="shutdown")
        
        # Nettoyage composants
        if self.inactivity_detector:
            self.inactivity_detector.cleanup()
        
        if self.conversation_manager:
            # Pas de cleanup nécessaire pour le nouvel observateur
            pass
        
        if self.ui_components:
            self.ui_components.cleanup()
        
        # Arrêt thread
        if self.background_thread and self.background_thread.is_alive():
            self.background_thread.join(timeout=2)
        
        self.is_initialized = False
        print("[COGNITIVE-MIRROR] ✅ Nettoyage terminé")
    
    # === MÉTHODES PRIVÉES ===
    
    def _start_background_thread(self):
        """Démarre le thread de surveillance en arrière-plan"""
        self.background_thread = threading.Thread(
            target=self._background_loop,
            name="CognitiveMirror-Background",
            daemon=True
        )
        self.background_thread.start()
    
    def _background_loop(self):
        """Boucle principale du thread de surveillance"""
        while not self.shutdown_event.is_set():
            try:
                # Nouvelle approche : pas de timeout car observation ponctuelle
                # L'observation s'arrête automatiquement quand Luna finit sa réflexion
                if self.active_reflection_session:
                    # Simple vérification si la session est toujours valide
                    pass
                
                # Sleep avec vérification shutdown
                self.shutdown_event.wait(1.0)  # Vérification chaque seconde
                
            except Exception as e:
                print(f"[COGNITIVE-MIRROR] ❌ Erreur thread surveillance: {e}")
                time.sleep(5)  # Pause avant retry
    
    def _get_conversation_context(self) -> Dict[str, Any]:
        """Récupère le contexte de conversation actuel"""
        # TODO: Intégration avec le système de conversation OGMA
        # Pour l'instant, contexte basique
        return {
            "timestamp": datetime.now().isoformat(),
            "session_active": self.active_reflection_session is not None,
            "last_user_activity": getattr(self, 'last_user_activity', None)
        }
    
    def _on_inactivity_detected(self, detection_type: str, duration: float):
        """Callback détection inactivité utilisateur"""
        print(f"[COGNITIVE-MIRROR] 👀 Inactivité détectée: {detection_type} ({duration:.1f}s)")
        
        # Debug des conditions
        enabled = self.is_enabled()
        active_session = self.active_reflection_session
        ready = self.is_ready()
        
        print(f"[COGNITIVE-MIRROR] 🔍 État: enabled={enabled}, active_session={active_session is not None}, ready={ready}")
        
        if enabled and not active_session:
            print("[COGNITIVE-MIRROR] 🚀 Démarrage session réflexive...")
            success = self.start_reflection_session(trigger_type=detection_type)
            print(f"[COGNITIVE-MIRROR] 📊 Résultat démarrage: {success}")
        elif enabled and active_session:
            # Session existe déjà, forcer l'affichage de l'overlay
            print("[COGNITIVE-MIRROR] 🔄 Session active détectée, affichage overlay...")
            if self.ui_components:
                print("[COGNITIVE-MIRROR] 🖼️ Affichage overlay avec session existante...")
                self.ui_components.show_reflection_overlay()
            else:
                print("[COGNITIVE-MIRROR] ⚠️ UI components non initialisées")
        else:
            if not enabled:
                print("[COGNITIVE-MIRROR] ⚠️ Extension désactivée")
            if active_session:
                print("[COGNITIVE-MIRROR] ⚠️ Session déjà active")
    
    def _on_activity_resumed(self):
        """Callback retour d'activité utilisateur pendant session réflexive"""
        print("[COGNITIVE-MIRROR] 🔄 Activité utilisateur détectée")
        
        if self.active_reflection_session:
            print("[COGNITIVE-MIRROR] 🛑 Fermeture session réflexive (retour activité)")
            self.stop_reflection_session("user_activity_resumed")
            
            # Marquer que la session réflexive n'est plus active
            if self.inactivity_detector:
                self.inactivity_detector.set_reflection_session_active(False)
    
    def _on_message_received(self, session_id: str, message_data: Dict[str, Any]):
        """Callback appelé quand un nouveau message est reçu dans la conversation"""
        print(f"[COGNITIVE-MIRROR] 📨 Callback message_received: session={session_id}, data={message_data}")
        
        if session_id == self.session_id:
            print(f"[COGNITIVE-MIRROR] ✅ Session match: {session_id}")
            # Mise à jour UI avec nouveau contenu
            if self.ui_components:
                print("[COGNITIVE-MIRROR] 🖼️ UI components disponibles, mise à jour...")
                self.ui_components.update_conversation_content(message_data)
            else:
                print("[COGNITIVE-MIRROR] ⚠️ UI components non initialisées")
        else:
            print(f"[COGNITIVE-MIRROR] ⚠️ Session mismatch: attendu {self.session_id}, reçu {session_id}")
    
    def _on_toggle_extension(self, new_state: bool):
        """Callback changement état extension via UI"""
        if new_state != self.is_enabled():
            self.toggle_enabled()
    
    def enrich_conversation_context(self, conversation_context: Dict[str, Any]):
        """
        Enrichit le contexte de conversation pour les futures observations
        
        Args:
            conversation_context: Contexte de la conversation actuelle
        """
        try:
            if self.conversation_manager and hasattr(self.conversation_manager, 'current_conversation_context'):
                self.conversation_manager.current_conversation_context = conversation_context
            elif self.conversation_manager:
                # Stocker dans le gestionnaire pour usage futur
                self.conversation_manager.conversation_context = conversation_context
            
            print(f"[COGNITIVE-MIRROR] ✅ Contexte enrichi pour réflexions")
        except Exception as e:
            print(f"[COGNITIVE-MIRROR] ❌ Erreur enrichissement contexte: {e}")

    def _on_settings_change(self, setting_key: str, new_value: Any):
        """Callback modification paramètres via UI"""
        self.config.set(setting_key, new_value)
        print(f"[COGNITIVE-MIRROR] ⚙️ Paramètre modifié: {setting_key} = {new_value}")
        
        # Application immédiate des changements
        if setting_key in ["trigger_delay_no_message", "trigger_delay_no_typing"]:
            if self.inactivity_detector:
                self.inactivity_detector.update_settings()
        
        elif setting_key == "max_reflection_duration":
            # Nouvelle approche n'a pas de timeout configurable
            # L'observation s'arrête naturellement avec la réflexion de Luna
            print(f"[COGNITIVE-MIRROR] ⚙️ Paramètre durée modifié (observateur auto-géré): {new_value}")
        
        # Transmettre les événements spéciaux à OGMA via callback externe
        if self.on_external_settings_change and setting_key in ['integrate_reflection_summary', 'force_stop_reflection']:
            try:
                self.on_external_settings_change(setting_key, new_value)
            except Exception as e:
                print(f"[COGNITIVE-MIRROR] ❌ Erreur callback externe {setting_key}: {e}")