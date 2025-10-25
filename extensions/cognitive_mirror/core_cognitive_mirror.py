# 🧠 Subconscience - Moteur Principal Transformé

"""
Extension Subconscience - Architecture États Automatisés
Remplace Cognitive Mirror avec orchestration luna-archiviste autonome

États:
- OFF: Extension désactivée
- STANDBY: En attente, surveillance inactivité active
- ACTIVE: Conversation Luna-Archiviste en cours (invisible)
- INTEGRATING: Finalisation et intégration des résultats

Fonctionnement automatique:
1. Détection inactivité → STANDBY → ACTIVE
2. Conversation invisible Luna/Archiviste 
3. Intégration automatique → retour STANDBY
4. Aucune intervention utilisateur requise
"""

import asyncio
import threading
import time
import queue
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime
import uuid
from enum import Enum

from .config import get_config, CognitiveMirrorConfig

# File globale pour messages Subconscience (thread-safe)
_subconscience_message_queue = queue.Queue()

class SubconscienceState(Enum):
    """États système Subconscience"""
    OFF = "OFF"                    # Extension désactivée
    STANDBY = "STANDBY"           # En attente, surveillance active
    ACTIVE = "ACTIVE"             # Conversation Luna-Archiviste en cours
    INTEGRATING = "INTEGRATING"   # Finalisation et intégration

class CognitiveMirrorCore:
    """
    Moteur principal extension Subconscience (anciennement Cognitive Mirror)
    
    NOUVEAU COMPORTEMENT:
    - Conversations automatiques Luna-Archiviste invisibles
    - États OFF/STANDBY/ACTIVE/INTEGRATING
    - Pas d'overlay conversation - que popup paramètres
    - Orchestrateur autonome avec intégration transparente
    
    Maintient API compatible pour intégration OGMA
    """
    
    def __init__(self, chat_controller, archiviste_controller, memory_manager, ui_container=None):
        """
        Initialise le moteur Subconscience avec les dépendances OGMA
        
        Args:
            chat_controller: Instance AIController (Luna)
            archiviste_controller: Instance AIController (Archiviste) 
            memory_manager: Instance MemoryManager OGMA
            ui_container: Container NiceGUI pour popup (optionnel)
        """
        self.config = get_config()
        
        # Dépendances OGMA
        self.chat_controller = chat_controller      # Luna
        self.archiviste_controller = archiviste_controller  # Archiviste
        self.memory_manager = memory_manager
        self.ui_container = ui_container
        
        # Composants extension (initialisés dans initialize())
        self.inactivity_detector = None
        self.conversation_orchestrator = None  # NOUVEAU: Orchestrateur autonome
        self.ui_components = None              # Popup paramètres uniquement
        self.memory_integration = None
        
        # Nouvel état Subconscience
        self.current_state = SubconscienceState.OFF
        self.state_history = []
        self.active_conversation_session = None
        self.last_integration_context = None
        self.session_id = None
        
        # État interne
        self.is_initialized = False
        
        # Threading
        self.background_thread = None
        self.shutdown_event = threading.Event()
        
        # Callbacks pour intégration OGMA
        self.on_state_transition = None        # Callback changements d'état
        self.on_conversation_complete = None   # Callback fin conversation
        self.on_integration_complete = None    # Callback intégration terminée
        self.on_external_settings_change = None
        self.on_synthesis_ready = None         # Callback synthèse prête pour UI
        
        self._set_state(SubconscienceState.OFF)
        print(f"[SUBCONSCIENCE] Moteur initialisé (état: {self.current_state.value})")
    
    def initialize(self) -> bool:
        """
        Initialisation complète des composants Subconscience
        
        Returns:
            bool: True si initialisation réussie
        """
        try:
            print("[SUBCONSCIENCE] Initialisation des composants...")
            
            # CORRECTION: Lire la configuration sauvegardée au démarrage
            saved_enabled = self.config.get("extension_enabled", False)
            print(f"[SUBCONSCIENCE] 🔧 Config enabled au démarrage: {saved_enabled}")
            
            # Définir l'état initial selon la configuration
            if saved_enabled:
                # Extension était activée -> STANDBY (surveillance active)
                self._set_state(SubconscienceState.STANDBY)
                print(f"[SUBCONSCIENCE] ✅ État initial: STANDBY (config enabled=true)")
            else:
                # Extension était désactivée -> OFF 
                self._set_state(SubconscienceState.OFF)
                print(f"[SUBCONSCIENCE] ⚪ Reste en état OFF (config disabled)")
            
            # Import dynamique pour éviter les erreurs circulaires
            from .inactivity_detector import InactivityDetector
            from .subconscience_orchestrator import SubconscienceOrchestrator  # NOUVEAU
            from .ui_components import CognitiveMirrorUI
            from .memory_integration import MemoryIntegration
            
            # Initialisation détecteur d'inactivité (paramètres popup)
            self.inactivity_detector = InactivityDetector(
                config=self.config,
                on_inactivity_detected=self._on_inactivity_detected,
                on_activity_resumed=self._on_activity_resumed,
                core_reference=self  # Pour vérifier l'état enabled
            )
            
            # NOUVEAU: Initialisation orchestrateur conversations automatiques
            self.conversation_orchestrator = SubconscienceOrchestrator(
                luna_controller=self.chat_controller,
                archiviste_controller=self.archiviste_controller,
                config=self.config,
                on_conversation_start=self._on_conversation_start,
                on_conversation_message=self._on_conversation_message,
                on_conversation_complete=self._on_conversation_complete,
                on_integration_ready=self._on_integration_ready
            )
            
            # Interface utilisateur (popup paramètres centralisé)
            self.ui_components = CognitiveMirrorUI(
                config=self.config,
                ui_container=self.ui_container,
                on_toggle_extension=self._on_toggle_extension,
                on_settings_change=self._on_settings_change,
                core_reference=self  # Pour accéder à is_enabled()
            )
            
            # Intégration mémoire pour contexte conversations
            self.memory_integration = MemoryIntegration(
                memory_manager=self.memory_manager,
                config=self.config
            )
            
            # Démarrage thread de surveillance états
            self._start_background_thread()
            
            self.is_initialized = True
            
            # Si extension enabled dans config, passage STANDBY
            config_enabled = self.config.is_enabled()
            print(f"[SUBCONSCIENCE] 🔧 Config enabled au démarrage: {config_enabled}")
            
            if config_enabled:
                print("[SUBCONSCIENCE] 🔄 Passage automatique OFF → STANDBY (config enabled)")
                self._set_state(SubconscienceState.STANDBY)
            else:
                print("[SUBCONSCIENCE] ⚪ Reste en état OFF (config disabled)")
            
            print("[SUBCONSCIENCE] Tous les composants initialisés")
            return True
            
        except Exception as e:
            print(f"[SUBCONSCIENCE] Erreur initialisation: {e}")
            return False
    
    def is_ready(self) -> bool:
        """Vérifie si l'extension est prête à fonctionner"""
        return (self.is_initialized and 
                self.inactivity_detector and 
                self.conversation_orchestrator and 
                self.ui_components)
    
    def is_enabled(self) -> bool:
        """Vérifie si l'extension est activée (config + état interne)"""
        # Vérifier d'abord la configuration utilisateur
        config_enabled = self.config.get('extension_enabled', False)
        
        # Si désactivée dans config, toujours retourner False
        if not config_enabled:
            return False
            
        # Si activée dans config, vérifier l'état interne
        return self.current_state != SubconscienceState.OFF
    
    def toggle_enabled(self) -> bool:
        """
        Bascule l'état ON/OFF de l'extension
        OFF <-> STANDBY (surveillance activée)
        
        Returns:
            bool: Nouvel état (True = pas OFF)
        """
        if self.current_state == SubconscienceState.OFF:
            # Activation: OFF → STANDBY
            self._set_state(SubconscienceState.STANDBY)
            # Recréer le détecteur d'inactivité s'il a été supprimé
            if self.inactivity_detector is None:
                self._recreate_inactivity_detector()
            self._start_inactivity_monitoring()
            new_enabled = True
        else:
            # Désactivation: tout état → OFF
            self._stop_all_activities()
            self._set_state(SubconscienceState.OFF)
            new_enabled = False
        
        # Mise à jour config
        self.config.set("extension_enabled", new_enabled)
        
        # Notification changement d'état
        if self.on_state_transition:
            self.on_state_transition(self.current_state.value, new_enabled)
        
        print(f"[SUBCONSCIENCE] Extension {'activée' if new_enabled else 'désactivée'}")
        return new_enabled
    
    def get_current_state(self) -> str:
        """Retourne l'état actuel Subconscience"""
        return self.current_state.value
    
    def force_trigger_conversation(self) -> bool:
        """
        Déclenche manuellement une conversation Luna-Archiviste
        Pour tests ou intégration externe

        Returns:
            bool: True si conversation démarrée
        """
        if not self.is_ready():
            print("[SUBCONSCIENCE] Extension non prête pour déclenchement manuel")
            return False

        if self.current_state in [SubconscienceState.ACTIVE, SubconscienceState.INTEGRATING]:
            print("[SUBCONSCIENCE] Conversation déjà en cours")
            return False

        # Force transition vers ACTIVE
        return self._trigger_conversation("magic_phrase_trigger")

    def stop_reflection_session(self, reason: str = "user_request") -> bool:
        """
        Arrête manuellement la session de réflexion en cours
        Utilisé pour les phrases magiques utilisateur

        Args:
            reason: Raison de l'arrêt (par défaut "user_request")

        Returns:
            bool: True si arrêt effectué
        """
        if not self.is_ready():
            print("[SUBCONSCIENCE] Extension non prête")
            return False

        # Vérifier si l'orchestrator a une conversation active (plus fiable que current_state)
        has_active_conversation = (
            self.conversation_orchestrator and
            self.conversation_orchestrator.is_conversation_active
        )

        if not has_active_conversation:
            print(f"[SUBCONSCIENCE] Aucune réflexion en cours à arrêter (état: {self.current_state.value})")
            return False

        print(f"[SUBCONSCIENCE] 🛑 Arrêt forcé de la réflexion en cours (raison: {reason})")
        self._force_stop_conversation(reason)
        return True
    
    def get_ui_components(self) -> Dict[str, Any]:
        """
        Retourne les composants UI pour intégration OGMA
        NOUVELLE APPROCHE: popup paramètres centralisé
        
        Returns:
            dict: Composants popup paramètres
        """
        if self.ui_components:
            return self.ui_components.get_components()
        return {}
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut détaillé Subconscience
        
        Returns:
            dict: Statut complet avec nouveaux états
        """
        return {
            "available": self.is_ready(),
            "enabled": self.is_enabled(),
            "initialized": self.is_initialized,
            "current_state": self.current_state.value,
            "state_history": [s.value for s in self.state_history[-5:]],  # 5 derniers états
            "active_conversation": self.active_conversation_session is not None,
            "session_id": self.session_id,
            "last_integration_time": getattr(self, 'last_integration_time', None),
            "monitoring_inactivity": self.inactivity_detector.is_monitoring() if self.inactivity_detector else False,
            "config": {
                "inactivity_delay": self.config.get("trigger_delay_no_message", 30),
                "auto_send_delay": self.config.get("auto_send_delay", 20),
                "max_duration": self.config.get("max_reflection_duration", 300),
                "trigger_message": self.config.get_required("trigger_message")
            }
        }
    
    def set_callbacks(self, on_state_transition=None, on_conversation_complete=None, on_integration_complete=None, on_external_settings_change=None,
                      on_state_change=None, on_reflection_start=None, on_reflection_end=None, on_synthesis_ready=None):
        """
        Configure les callbacks pour intégration OGMA
        Compatibilité : on_state_change → on_state_transition (ancien nom)
        """
        # Nouveau système Subconscience
        self.on_state_transition = on_state_transition or on_state_change  # Compatibilité
        self.on_conversation_complete = on_conversation_complete or on_reflection_end  # Compatibilité
        self.on_integration_complete = on_integration_complete
        self.on_external_settings_change = on_external_settings_change
        self.on_synthesis_ready = on_synthesis_ready  # Callback affichage synthèse

        # Callbacks compatibilité ancienne API
        if on_reflection_start:
            self.on_conversation_start = on_reflection_start
    
    def cleanup(self):
        """Nettoyage et fermeture propre de l'extension"""
        print("[SUBCONSCIENCE] Nettoyage extension...")
        
        # Signal arrêt
        self.shutdown_event.set()
        
        # Arrêt activités en cours
        self._stop_all_activities()
        
        # Nettoyage composants
        if self.inactivity_detector:
            self.inactivity_detector.cleanup()
        
        if self.conversation_orchestrator:
            self.conversation_orchestrator.cleanup()
        
        if self.ui_components:
            self.ui_components.cleanup()
        
        # Arrêt thread
        if self.background_thread and self.background_thread.is_alive():
            self.background_thread.join(timeout=2)
        
        self._set_state(SubconscienceState.OFF)
        self.is_initialized = False
        print("[SUBCONSCIENCE] Nettoyage terminé")
    
    # === MÉTHODES PRIVÉES - GESTION ÉTATS ===
    
    def _set_state(self, new_state: SubconscienceState):
        """
        Change l'état Subconscience avec historique
        
        Args:
            new_state: Nouvel état du système
        """
        if self.current_state != new_state:
            old_state = self.current_state
            self.current_state = new_state
            self.state_history.append(new_state)
            
            # Garder historique limité
            if len(self.state_history) > 20:
                self.state_history = self.state_history[-20:]
            
            print(f"[SUBCONSCIENCE] Transition état: {old_state.value} → {new_state.value}")
            
            # Callback notification
            if self.on_state_transition:
                try:
                    self.on_state_transition(new_state.value, old_state.value)
                except Exception as e:
                    print(f"[SUBCONSCIENCE] Erreur callback transition: {e}")
    
    def _trigger_conversation(self, trigger_type: str) -> bool:
        """
        Déclenche une conversation Luna-Archiviste automatique
        
        Args:
            trigger_type: Type de déclenchement ("inactivity", "manual", "timeout")
            
        Returns:
            bool: True si conversation démarrée
        """
        if not self.is_ready():
            return False
        
        if self.current_state in [SubconscienceState.ACTIVE, SubconscienceState.INTEGRATING]:
            print("[SUBCONSCIENCE] Conversation déjà en cours")
            return False
        
        try:
            # Génération ID session unique
            self.session_id = f"subconscience_{int(time.time())}_{uuid.uuid4().hex[:8]}"
            
            # Transition vers état ACTIVE
            self._set_state(SubconscienceState.ACTIVE)
            
            # GARDONS la surveillance active pour détecter le retour utilisateur
            # self._stop_inactivity_monitoring()  # SUPPRIMÉ: on veut détecter l'activité pendant introspection
            print("[SUBCONSCIENCE] 🔄 Surveillance inactivité MAINTENUE pour détecter retour utilisateur")
            
            # NOUVEAU: Marquer session réflexive comme active
            if self.inactivity_detector:
                self.inactivity_detector.set_reflection_session_active(True)
                print("[SUBCONSCIENCE] ✅ Flag session_active mis à True")
            
            # Démarrage conversation automatique (invisible)
            success = self.conversation_orchestrator.start_conversation(
                trigger_type=trigger_type,
                session_id=self.session_id,
                conversation_context=self._get_conversation_context(),
                trigger_message=self.config.get_required("trigger_message")
            )
            
            if success:
                self.active_conversation_session = self.session_id
                print(f"[SUBCONSCIENCE] Conversation automatique démarrée (ID: {self.session_id})")
                return True
            else:
                # Échec démarrage, retour STANDBY
                self._set_state(SubconscienceState.STANDBY)
                self._start_inactivity_monitoring()
                return False
                
        except Exception as e:
            print(f"[SUBCONSCIENCE] Erreur démarrage conversation: {e}")
            self._set_state(SubconscienceState.STANDBY)
            self._start_inactivity_monitoring()
            return False
    
    def _start_background_thread(self):
        """Démarre le thread de surveillance états"""
        self.background_thread = threading.Thread(
            target=self._background_loop,
            name="Subconscience-Background",
            daemon=True
        )
        self.background_thread.start()
    
    def _background_loop(self):
        """Boucle principale surveillance états Subconscience"""
        while not self.shutdown_event.is_set():
            try:
                # Surveillance état ACTIVE - timeout sécurité
                if self.current_state == SubconscienceState.ACTIVE:
                    self._check_active_conversation_timeout()
                
                # Surveillance état INTEGRATING - finalisation
                elif self.current_state == SubconscienceState.INTEGRATING:
                    self._check_integration_completion()
                
                # Sleep avec vérification shutdown
                self.shutdown_event.wait(2.0)  # Vérification toutes les 2 secondes
                
            except Exception as e:
                print(f"[SUBCONSCIENCE] Erreur thread surveillance: {e}")
                time.sleep(5)
    
    def _check_active_conversation_timeout(self):
        """Vérification timeout sécurité état ACTIVE"""
        max_duration = self.config.get("max_reflection_duration", 300)  # 5min par défaut
        
        if hasattr(self, 'active_start_time'):
            elapsed = time.time() - self.active_start_time
            if elapsed > max_duration:
                print(f"[SUBCONSCIENCE] Timeout conversation ({elapsed:.1f}s > {max_duration}s)")
                self._force_stop_conversation("timeout")
    
    def _check_integration_completion(self):
        """Vérification finalisation état INTEGRATING"""
        # Délai maximum intégration: 30 secondes
        if hasattr(self, 'integration_start_time'):
            elapsed = time.time() - self.integration_start_time
            if elapsed > 30:
                print("[SUBCONSCIENCE] Timeout intégration - retour STANDBY")
                self._complete_integration("timeout")
    
    def _start_inactivity_monitoring(self):
        """Démarre surveillance inactivité (état STANDBY)"""
        # Vérifier que l'extension est activée et en état STANDBY
        if not self.is_enabled() or self.current_state != SubconscienceState.STANDBY:
            print(f"[SUBCONSCIENCE] ⚠️ Démarrage monitoring ignoré (enabled: {self.is_enabled()}, état: {self.current_state.value})")
            return
        
        # Si pas de détecteur, le recréer
        if self.inactivity_detector is None:
            print("[SUBCONSCIENCE] ⚠️ Pas de détecteur - recréation...")
            self._recreate_inactivity_detector()
            
        # Arrêter l'ancien détecteur s'il existe encore
        if self.inactivity_detector and self.inactivity_detector.is_monitoring():
            print("[SUBCONSCIENCE] ⚠️ Arrêt ancien détecteur avant redémarrage")
            self.inactivity_detector.stop_monitoring()
            
        if self.inactivity_detector:
            self.inactivity_detector.start_monitoring()
            print(f"[SUBCONSCIENCE] ✅ Surveillance inactivité démarrée (état: {self.current_state.value})")
        else:
            print("[SUBCONSCIENCE] ❌ Impossible de démarrer - pas de détecteur")
    
    def start_inactivity_monitoring(self):
        """API PUBLIQUE: Démarre surveillance inactivité (compatible OGMA)"""
        print("[SUBCONSCIENCE] 🚀 API publique: démarrage surveillance inactivité")
        self._start_inactivity_monitoring()
    
    def _stop_inactivity_monitoring(self):
        """Arrête surveillance inactivité et nettoie les références"""
        if self.inactivity_detector:
            print("[SUBCONSCIENCE] 🛑 Arrêt détecteur d'inactivité...")
            self.inactivity_detector.stop_monitoring()
            # Attendre un peu pour s'assurer que le thread se termine
            import time
            time.sleep(0.1)
            self.inactivity_detector = None
            print("[SUBCONSCIENCE] 🗑️ Détecteur d'inactivité supprimé")
    
    def _recreate_inactivity_detector(self):
        """Recrée le détecteur d'inactivité après une désactivation"""
        try:
            from .inactivity_detector import InactivityDetector
            print("[SUBCONSCIENCE] 🔄 Recréation du détecteur d'inactivité...")
            
            self.inactivity_detector = InactivityDetector(
                config=self.config,
                on_inactivity_detected=self._on_inactivity_detected,
                on_activity_resumed=self._on_activity_resumed,
                core_reference=self
            )
            print("[SUBCONSCIENCE] ✅ Détecteur d'inactivité recréé")
        except Exception as e:
            print(f"[SUBCONSCIENCE] ❌ Erreur recréation détecteur: {e}")
            self.inactivity_detector = None
    
    def _stop_all_activities(self):
        """Arrête toutes les activités en cours"""
        # IMPORTANT: Mettre l'état à OFF en premier pour éviter les redémarrages
        was_active = self.current_state in [SubconscienceState.ACTIVE, SubconscienceState.INTEGRATING]
        self._set_state(SubconscienceState.OFF)
        
        # Arrêt conversation si elle était active
        if was_active:
            self._force_stop_conversation("shutdown")
        
        # Arrêt surveillance
        self._stop_inactivity_monitoring()
        
        # Vider la queue des messages en attente
        self._clear_pending_messages()
        
        # Reset session
        self.active_conversation_session = None
        self.session_id = None
    
    def _clear_pending_messages(self):
        """Vide la queue des messages en attente"""
        global _subconscience_message_queue
        try:
            while not _subconscience_message_queue.empty():
                _subconscience_message_queue.get_nowait()
            print("[SUBCONSCIENCE] 🗑️ Queue des messages vidée")
        except Exception as e:
            print(f"[SUBCONSCIENCE] ⚠️ Erreur vidage queue: {e}")
    
    def _force_stop_conversation(self, reason: str):
        """Force l'arrêt de la conversation en cours"""
        if self.conversation_orchestrator:
            self.conversation_orchestrator.stop_conversation(reason)

        self.active_conversation_session = None
        self.session_id = None

        # Stocker la raison d'arrêt pour _complete_integration()
        self.last_stop_reason = reason

        # Retour état STANDBY seulement si l'extension est toujours activée ET ce n'est pas un arrêt complet
        if self.current_state != SubconscienceState.OFF and reason != "shutdown":
            self._set_state(SubconscienceState.STANDBY)

            # NE PAS redémarrer le monitoring si c'est un arrêt utilisateur explicite
            # Cela évite que la réflexion redémarre automatiquement après arrêt
            user_stop_reasons = ["user_stop_request", "user_button_stop", "manual_stop", "ia_exit"]
            if reason not in user_stop_reasons:
                self._start_inactivity_monitoring()
            else:
                print(f"[SUBCONSCIENCE] ⚠️ Arrêt utilisateur ({reason}) - monitoring STOPPÉ")
                self._stop_inactivity_monitoring()
    
    def _complete_integration(self, reason: str = "complete"):
        """Finalise l'intégration et retour STANDBY"""
        self.last_integration_context = {
            "session_id": self.session_id,
            "completion_reason": reason,
            "timestamp": datetime.now().isoformat()
        }
        
        # Callback intégration terminée
        if self.on_integration_complete:
            try:
                self.on_integration_complete(self.session_id, reason, self.last_integration_context)
            except Exception as e:
                print(f"[SUBCONSCIENCE] Erreur callback intégration: {e}")
        
        # Reset session
        self.active_conversation_session = None
        self.session_id = None
        
        # Retour STANDBY seulement si l'extension est encore activée
        if self.is_enabled():
            self._set_state(SubconscienceState.STANDBY)

            # NE PAS redémarrer le monitoring si c'est un arrêt utilisateur explicite
            user_stop_reasons = ["user_stop_request", "user_button_stop", "manual_stop", "ia_exit"]
            if not hasattr(self, 'last_stop_reason') or self.last_stop_reason not in user_stop_reasons:
                self._start_inactivity_monitoring()
            else:
                print(f"[SUBCONSCIENCE] ⚠️ Arrêt utilisateur ({self.last_stop_reason}) détecté - monitoring NON redémarré (éviter boucle)")
                # Réinitialiser last_stop_reason pour la prochaine fois
                self.last_stop_reason = None
        else:
            print("[SUBCONSCIENCE] 🛑 Extension désactivée - pas de retour STANDBY")
        
        print(f"[SUBCONSCIENCE] Intégration terminée ({reason})")
    
    def _get_conversation_context(self) -> Dict[str, Any]:
        """Récupère le contexte pour conversations automatiques"""
        context = {
            "timestamp": datetime.now().isoformat(),
            "state": self.current_state.value,
            "session_active": self.active_conversation_session is not None,
            "last_user_activity": getattr(self, 'last_user_activity', None)
        }
        
        # Enrichissement contexte mémoire si disponible
        if self.memory_integration:
            try:
                memory_context = self.memory_integration.get_relevant_context()
                # memory_context est une string, pas un dict - on l'ajoute comme clé
                context["memory_context"] = memory_context
            except Exception as e:
                print(f"[SUBCONSCIENCE] Erreur contexte mémoire: {e}")
        
        return context
    
    # === CALLBACKS DÉTECTION INACTIVITÉ ===
    
    def _on_inactivity_detected(self, detection_type: str, duration: float):
        """
        Callback détection inactivité → Déclenchement automatique
        NOUVEAU: Transition STANDBY → ACTIVE
        """
        # Vérifier d'abord si l'extension est activée
        if not self.is_enabled():
            print(f"[SUBCONSCIENCE] 🛑 Callback ignoré - extension désactivée (état: {self.current_state.value})")
            return  # Extension désactivée - ignorer silencieusement
            
        print(f"[SUBCONSCIENCE] Inactivité détectée: {detection_type} ({duration:.1f}s)")

        if self.current_state == SubconscienceState.STANDBY:
            print("[SUBCONSCIENCE] Déclenchement conversation automatique...")
            self._trigger_conversation(detection_type)
        elif self.current_state == SubconscienceState.ACTIVE:
            # Si déjà en conversation, arrêter le monitoring pour éviter spam
            print(f"[SUBCONSCIENCE] Inactivité ignorée (état: ACTIVE) - arrêt monitoring temporaire")
            if self.inactivity_detector:
                self.inactivity_detector.stop_monitoring()
        else:
            print(f"[SUBCONSCIENCE] Inactivité ignorée (état: {self.current_state.value})")
    
    def _on_activity_resumed(self):
        """
        Callback retour d'activité utilisateur
        CORRIGÉ: Arrêt immédiat de la conversation quand utilisateur revient
        """
        print("[SUBCONSCIENCE] 🔄 INTERRUPTION UTILISATEUR - Activité détectée")
        
        # IMPORTANT: Notifier immédiatement le détecteur que la session réflexive n'est plus active
        if self.inactivity_detector:
            self.inactivity_detector.set_reflection_session_active(False)
            print("[SUBCONSCIENCE] ✅ Flag session_active mis à False")
        
        if self.current_state == SubconscienceState.ACTIVE:
            print("[SUBCONSCIENCE] 🛑 ARRÊT FORCÉ conversation - retour utilisateur")
            
            # Stopper la conversation immédiatement
            if self.conversation_orchestrator and self.conversation_orchestrator.is_conversation_active:
                self.conversation_orchestrator.stop_conversation("user_activity_resumed")
                print("[SUBCONSCIENCE] ✅ Conversation stoppée")
                
            # Finaliser la session d'introspection en cours
            self._complete_integration("user_return")
            print("[SUBCONSCIENCE] ✅ Session finalisée - retour STANDBY")
            
        elif self.current_state == SubconscienceState.STANDBY:
            print("[SUBCONSCIENCE] Reset timer surveillance inactivité")
    
    # === CALLBACKS ORCHESTRATEUR CONVERSATIONS ===
    
    def _on_conversation_start(self, session_id: str, participants: list):
        """Callback démarrage conversation Luna-Archiviste - AJOUTE MESSAGE À LA FILE"""
        self.active_start_time = time.time()
        print(f"[SUBCONSCIENCE] Conversation Luna-Archiviste démarrée (participants: {participants})")
        
        # Plus de message spam - démarrage silencieux 
        print("[SUBCONSCIENCE] ✅ Session démarrée - en attente des messages Luna/Archiviste")
    
    def _on_conversation_message(self, session_id: str, message_data: Dict[str, Any]):
        """Callback message conversation - AJOUTE MESSAGE À LA FILE"""
        role = message_data.get('role', 'unknown')
        content = message_data.get('content', '')
        
        # Log pour debug
        content_preview = content[:50] + "..." if len(content) > 50 else content
        print(f"[SUBCONSCIENCE] Message {role}: {content_preview}")
        
        # Mapper les rôles - PAS de formatage ici (géré par ogma_ng.py)
        if role == 'luna':
            display_role = 'assistant'
        elif role == 'archiviste':
            display_role = 'assistant'
        else:
            display_role = 'assistant'

        # Ajouter message à la file pour affichage ultérieur
        # Le contenu n'est PAS formaté ici - ogma_ng.py s'en charge
        message = {
            "role": display_role,
            "content": content,  # Contenu brut sans formatage
            "timestamp": datetime.now().isoformat(),
            "type": "subconscience_message",
            "original_role": role  # Rôle original pour formatage par ogma_ng.py
        }
        _subconscience_message_queue.put(message)
        print(f"[SUBCONSCIENCE] ✅ Message {role} ajouté à la file")
    
    @staticmethod
    def add_test_message(role: str, content: str, message_type: str = "subconscience_message"):
        """Ajoute un message de test à la queue Subconscience (pour tests uniquement)"""
        message = {
            'role': role,
            'content': content,
            'type': message_type,
            'timestamp': datetime.now().isoformat()
        }
        _subconscience_message_queue.put(message)
        print(f"[SUBCONSCIENCE-TEST] ✅ Message test ajouté: {message_type}")
    
    @staticmethod
    def get_pending_messages() -> List[Dict[str, Any]]:
        """Récupère tous les messages en attente dans la file (à appeler depuis l'UI principale)"""
        messages = []
        try:
            while True:
                message = _subconscience_message_queue.get_nowait()
                messages.append(message)
        except queue.Empty:
            pass
        
        if messages:
            print(f"[SUBCONSCIENCE] 📤 {len(messages)} messages récupérés de la file")
        
        return messages
    
    def _on_conversation_complete(self, session_id: str, conversation_data: Dict[str, Any]):
        """
        Callback fin conversation → Transition ACTIVE → INTEGRATING
        """
        print(f"[SUBCONSCIENCE] Conversation terminée (session: {session_id})")

        # STOCKER la raison de l'arrêt pour savoir si on doit redémarrer le monitoring
        completion_reason = conversation_data.get("completion_reason", "unknown")
        self.last_stop_reason = completion_reason
        print(f"[SUBCONSCIENCE] 📝 Raison arrêt stockée: {completion_reason}")

        # CORRECTION: Vérifier s'il y a une synthèse à envoyer (peu importe la raison d'arrêt)
        ia_initiated_exit = conversation_data.get("ia_initiated_exit", False)
        user_synthesis = conversation_data.get("user_synthesis", None)

        # NOUVEAU: Générer synthèse dans TOUS les cas où il y a eu une vraie introspection
        if user_synthesis:
            print(f"[SUBCONSCIENCE] 🧠 Synthèse disponible (IA initiated: {ia_initiated_exit}, raison: {completion_reason})")
            print("[SUBCONSCIENCE] 📝 Affichage synthèse pour l'utilisateur...")

            # Envoyer la synthèse via callback vers UI principale
            if self.on_synthesis_ready:
                try:
                    self.on_synthesis_ready(user_synthesis)
                    print("[SUBCONSCIENCE] ✅ Synthèse envoyée via callback")
                except Exception as e:
                    print(f"[SUBCONSCIENCE] ❌ Erreur callback synthèse: {e}")
            else:
                print("[SUBCONSCIENCE] ⚠️ Callback synthèse non défini")
        else:
            print(f"[SUBCONSCIENCE] ℹ️ Pas de synthèse disponible (raison: {completion_reason})")

        # IMPORTANT: Arrêter le monitoring d'inactivité dans tous les cas
        if self.inactivity_detector:
            self.inactivity_detector.set_reflection_session_active(False)
            print("[SUBCONSCIENCE] ✅ Monitoring: session_active mis à False")

        # Transition vers intégration
        self._set_state(SubconscienceState.INTEGRATING)
        self.integration_start_time = time.time()

        # Callback externe notification
        if self.on_conversation_complete:
            try:
                self.on_conversation_complete(session_id, conversation_data)
            except Exception as e:
                print(f"[SUBCONSCIENCE] Erreur callback conversation terminée: {e}")

        # Démarrage intégration automatique
        self._start_integration_process(conversation_data)
    
    def _on_integration_ready(self, session_id: str, integration_data: Dict[str, Any]):
        """Callback données intégration prêtes → Finalisation"""
        print(f"[SUBCONSCIENCE] Données intégration prêtes (session: {session_id})")
        
        # Vérifier que la session est valide
        if not session_id or session_id == "None":
            print("[SUBCONSCIENCE] ⚠️ Session invalide - intégration ignorée")
            return
        
        # Sauvegarde mémoire intégrée
        if self.memory_integration:
            try:
                self.memory_integration.save_conversation_memory(
                    session_id=session_id,
                    conversation_data=integration_data
                )
            except Exception as e:
                print(f"[SUBCONSCIENCE] Erreur sauvegarde mémoire: {e}")
        
        # Finalisation intégration
        self._complete_integration("success")
    
    def _start_integration_process(self, conversation_data: Dict[str, Any]):
        """Démarre le processus d'intégration automatique"""
        try:
            # L'orchestrator gère déjà l'appel à on_integration_ready
            # Cette méthode est conservée pour compatibilité mais ne fait plus rien
            # L'intégration est gérée directement par l'orchestrator via son callback
            print(f"[SUBCONSCIENCE] ⏭️ Intégration gérée par orchestrator")
            pass

        except Exception as e:
            print(f"[SUBCONSCIENCE] Erreur processus intégration: {e}")
            self._complete_integration("error")
    
    # === CALLBACKS UI POPUP ===
    
    def _on_toggle_extension(self, new_state: bool):
        """
        Callback toggle ON/OFF depuis popup paramètres
        Force l'état selon la configuration utilisateur
        """
        print(f"[SUBCONSCIENCE-CORE] 📞 Callback toggle reçu: new_state={new_state}")
        
        # Mettre à jour la config d'abord
        self.config.set('extension_enabled', new_state)
        
        # Forcer l'état interne selon la nouvelle config
        if new_state:
            # Activation demandée
            if self.current_state == SubconscienceState.OFF:
                self._set_state(SubconscienceState.STANDBY)
                if self.inactivity_detector is None:
                    self._recreate_inactivity_detector()
                self._start_inactivity_monitoring()
                print(f"[SUBCONSCIENCE-CORE] ✅ Extension ACTIVÉE (OFF → STANDBY)")
            else:
                print(f"[SUBCONSCIENCE-CORE] ⚪ Extension déjà active (état: {self.current_state})")
        else:
            # Désactivation demandée
            if self.current_state != SubconscienceState.OFF:
                self._stop_all_activities()
                self._set_state(SubconscienceState.OFF)
                print(f"[SUBCONSCIENCE-CORE] ✅ Extension DÉSACTIVÉE (→ OFF)")
            else:
                print(f"[SUBCONSCIENCE-CORE] ⚪ Extension déjà désactivée")
    
    def _on_settings_change(self, setting_key: str, new_value: Any):
        """
        Callback modification paramètres depuis popup
        Application IMMÉDIATE des changements
        """
        print(f"[SUBCONSCIENCE] 🔄 Paramètre modifié: {setting_key} = {new_value}")
        
        # Application immédiate selon paramètre
        if setting_key == "extension_enabled":
            print(f"[SUBCONSCIENCE] 🎯 EXTENSION_ENABLED modifié: {new_value}")
            current_enabled = self.is_enabled() 
            if new_value != current_enabled:
                print(f"[SUBCONSCIENCE] 🔄 Toggle requis: {current_enabled} → {new_value}")
                self.toggle_enabled()
                print(f"[SUBCONSCIENCE] ✅ Extension {'ACTIVÉE' if new_value else 'DÉSACTIVÉE'} immédiatement")
        
        elif setting_key in ["trigger_delay_no_message", "trigger_delay_no_typing", "auto_send_delay"]:
            print(f"[SUBCONSCIENCE] 🔄 Mise à jour détecteur inactivité: {setting_key}")
            if self.inactivity_detector:
                self.inactivity_detector.update_settings()
                print(f"[SUBCONSCIENCE] ✅ Détecteur mis à jour avec {setting_key}={new_value}")
        
        elif setting_key == "trigger_message":
            print(f"[SUBCONSCIENCE] 🔄 Message déclencheur mis à jour pour futures conversations")
        
        elif setting_key in ["entite_token_limit", "archiviste_token_limit"]:  # Renommé: luna → entite
            print(f"[SUBCONSCIENCE] 🔄 Limite tokens mise à jour: {setting_key}={new_value}")
        
        elif setting_key in ["luna_instruction", "archiviste_instruction"]:
            print(f"[SUBCONSCIENCE] 🔄 Instructions mises à jour: {setting_key}")
        
        elif setting_key == "max_reflection_duration":
            print(f"[SUBCONSCIENCE] 🔄 Durée max réflexion mise à jour: {new_value}s")
        
        # Événements spéciaux vers OGMA
        if self.on_external_settings_change and setting_key in ['force_conversation_trigger']:
            try:
                self.on_external_settings_change(setting_key, new_value)
            except Exception as e:
                print(f"[SUBCONSCIENCE] Erreur callback externe {setting_key}: {e}")

    def enrich_conversation_context(self, conversation_context: Dict[str, Any]):
        """
        Enrichit le contexte de conversation pour les futures observations.
        
        Cette méthode est appelée par OGMA pour fournir du contexte supplémentaire
        aux conversations d'introspection.
        
        Args:
            conversation_context: Contexte conversationnel à enrichir
        """
        try:
            print(f"[SUBCONSCIENCE] 🔍 Enrichissement contexte conversation")
            
            # Stocker le contexte pour utilisation future
            if not hasattr(self, 'enriched_context'):
                self.enriched_context = {}
            
            # Fusionner avec contexte existant
            self.enriched_context.update(conversation_context)
            
            # Ajouter timestamp d'enrichissement
            self.enriched_context['last_enrichment'] = datetime.now().isoformat()
            
            print(f"[SUBCONSCIENCE] ✅ Contexte enrichi avec {len(conversation_context)} éléments")
            
        except Exception as e:
            print(f"[SUBCONSCIENCE] ❌ Erreur enrichissement contexte: {e}")

# Maintien compatibilité API existante
__all__ = ['CognitiveMirrorCore', 'SubconscienceState']