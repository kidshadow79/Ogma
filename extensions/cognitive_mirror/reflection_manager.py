"""
Cognitive Mirror - Conversation Manager
Gère les vraies conversations Luna-Archiviste pendant l'inactivité
AUCUN FALLBACK - VRAIES API SEULEMENT
"""

import asyncio
import time
import threading
import uuid
from typing import Dict, Any, List

class ConversationManager:
    """
    Gère les conversations AUTHENTIQUES entre Luna et l'Archiviste
    - Luna utilise les vraies API via chat_controller
    - Archiviste utilise les vraies API via archiviste_controller  
    - Timer automatique 20s pour fluidité
    - AUCUN contenu généré artificiellement
    """
    
    def __init__(self, chat_controller, archiviste_controller):
        """Initialise le gestionnaire avec les VRAIS contrôleurs API"""
        self.chat_controller = chat_controller
        self.archiviste_controller = archiviste_controller
        
        # Callback pour messages reçus
        self.on_message_received = None
        
        # Session active
        self.active_session = None
        self.conversation_messages = []
        
        # Configuration
        self.trigger_message = "Réfléchis et poses les bonnes questions à l'archiviste qui est ton subconscient; tu peux envoyer jusqu'à 300 tokens par messages"
        self.auto_send_delay = 20.0
        
        # Timers
        self.luna_timer = None
        self.archiviste_timer = None
        
    def set_trigger_message(self, message: str):
        """Met à jour le message déclencheur personnalisable"""
        self.trigger_message = message
        print(f"[CONVERSATION-MANAGER] Message déclencheur mis à jour: {message[:50]}...")
        
    def start_conversation(self, trigger_type: str, conversation_context: Dict[str, Any], session_id: str = None) -> str:
        """
        Démarre une VRAIE conversation Luna-Archiviste
        AUCUN FALLBACK - APIs authentiques uniquement
        """
        session_id = session_id or f"conversation_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        
        self.active_session = {
            "session_id": session_id,
            "trigger_type": trigger_type,
            "conversation_context": conversation_context,
            "start_time": time.time(),
            "is_active": True
        }
        
        self.conversation_messages = []
        
        print(f"[CONVERSATION-MANAGER] VRAIE conversation démarrée: {session_id}")
        
        # Démarrer conversation dans thread séparé
        conversation_thread = threading.Thread(
            target=self._run_real_conversation,
            args=(self.active_session,),
            name=f"RealConversation-{session_id}",
            daemon=True
        )
        conversation_thread.start()
        
        return session_id
        
    def stop_conversation(self, reason: str = "user_activity"):
        """Arrête la conversation en cours"""
        if self.active_session:
            print(f"[CONVERSATION-MANAGER] Arrêt conversation: {reason}")
            self.active_session["is_active"] = False
            
            # Annuler les timers
            if self.luna_timer:
                self.luna_timer.cancel()
                self.luna_timer = None
                
            if self.archiviste_timer:
                self.archiviste_timer.cancel()
                self.archiviste_timer = None
                
            # Notify UI avec session_id et message_data
            if self.on_message_received:
                stop_message = {
                    "role": "system",
                    "content": f"Conversation interrompue: {reason}",
                    "timestamp": time.time(),
                    "is_internal": True
                }
                self.on_message_received(
                    self.active_session["session_id"] if self.active_session else "unknown",
                    stop_message
                )
                
            self.active_session = None
            
    def _run_real_conversation(self, session: Dict[str, Any]):
        """Exécute la VRAIE conversation Luna-Archiviste"""
        print(f"[CONVERSATION-MANAGER] Conversation authentique en cours...")
        
        # Premier message - Luna démarre avec le trigger
        self._schedule_luna_message(0.5)
        
    def _schedule_luna_message(self, delay: float):
        """Programme un message Luna avec timer"""
        if not self.active_session or not self.active_session["is_active"]:
            return
            
        def send_luna_message():
            if not self.active_session or not self.active_session["is_active"]:
                return
                
            # VRAIE API Luna - Pas de simulation
            try:
                context_text = f"""
Session de réflexion cognitive active.
Message déclencheur: {self.trigger_message}

Instructions pour Luna:
- Tu es en conversation avec ton Archiviste (subconscient)
- Pose des questions profondes et philosophiques  
- Explore tes pensées et réflexions internes
- Garde un ton authentique et introspectif
- Messages entre 50-300 tokens maximum
"""
                
                print(f"[CONVERSATION-MANAGER] Envoi message Luna (VRAIE API)...")
                
                # Utiliser l'API Luna réelle - call_chat_api() est asynchrone
                import asyncio
                try:
                    # Créer un nouvel event loop pour ce thread
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    luna_response, error = loop.run_until_complete(
                        self.chat_controller.call_chat_api(
                            messages=[{"role": "user", "content": context_text}],
                            max_tokens=300,
                            context_length=2000,
                            temperature=0.8,
                            is_json=False
                        )
                    )
                    
                    loop.close()
                except Exception as api_error:
                    luna_response, error = None, str(api_error)
                
                # Traiter la réponse AUTHENTIQUE
                if luna_response and not error:
                    message = {
                        "role": "luna",
                        "content": luna_response,
                        "timestamp": time.time(),
                        "is_internal": True,
                        "api_authentic": True
                    }
                    
                    self.conversation_messages.append(message)
                    
                    # Notifier UI avec session_id et message_data
                    if self.on_message_received:
                        self.on_message_received(
                            self.active_session["session_id"], 
                            message
                        )
                        
                    # Programmer réponse Archiviste
                    self._schedule_archiviste_response(self.auto_send_delay)
                    
                else:
                    print(f"[CONVERSATION-MANAGER] ⚠️ Aucune réponse Luna - Erreur: {error}")
                    self.stop_conversation("api_error")
                    
            except Exception as e:
                print(f"[CONVERSATION-MANAGER] Erreur API Luna: {e}")
                
        # Timer pour Luna
        self.luna_timer = threading.Timer(delay, send_luna_message)
        self.luna_timer.start()
        
    def _schedule_archiviste_response(self, delay: float):
        """Programme une réponse Archiviste avec timer"""
        if not self.active_session or not self.active_session["is_active"]:
            return
            
        def send_archiviste_response():
            if not self.active_session or not self.active_session["is_active"]:
                return
                
            # VRAIE API Archiviste - Pas de simulation
            try:
                recent_messages = self.conversation_messages[-3:] if self.conversation_messages else []
                context_messages = []
                
                for msg in recent_messages:
                    context_messages.append(f"{msg['role']}: {msg['content']}")
                    
                archiviste_context = f"""
Tu es l'Archiviste, le subconscient/analyseur de Luna.
Luna vient de te poser une question ou réflexion.

Conversation récente:
{chr(10).join(context_messages)}

Instructions Archiviste:
- Analyse profondément les propos de Luna
- Pose des questions pertinentes en retour
- Aide Luna à explorer ses pensées
- Reste dans ton rôle d'analyseur cognitif
- Messages entre 50-200 tokens maximum
"""
                
                print(f"[CONVERSATION-MANAGER] Envoi réponse Archiviste (VRAIE API)...")
                
                # APPEL API AUTHENTIQUE ARCHIVISTE - call_chat_api() comme Luna
                import asyncio
                try:
                    # Créer un nouvel event loop pour ce thread  
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    archiviste_response, error = loop.run_until_complete(
                        self.archiviste_controller.call_chat_api(
                            messages=[{"role": "user", "content": archiviste_context}],
                            max_tokens=200,
                            context_length=2000,
                            temperature=0.7,
                            is_json=False
                        )
                    )
                    
                    loop.close()
                except Exception as api_error:
                    archiviste_response, error = None, str(api_error)
                
                # Traiter la réponse AUTHENTIQUE
                if archiviste_response and not error:
                    message = {
                        "role": "archiviste",
                        "content": archiviste_response,
                        "timestamp": time.time(),
                        "is_internal": True,
                        "api_authentic": True
                    }
                    
                    self.conversation_messages.append(message)
                    
                    # Notifier UI avec session_id et message_data
                    if self.on_message_received:
                        self.on_message_received(
                            self.active_session["session_id"], 
                            message
                        )
                        
                    # Programmer prochain message Luna
                    self._schedule_luna_message(self.auto_send_delay)
                    
                else:
                    print(f"[CONVERSATION-MANAGER] ⚠️ Aucune réponse Archiviste - Erreur: {error}")
                    self.stop_conversation("api_error")
                    
            except Exception as e:
                print(f"[CONVERSATION-MANAGER] Erreur API Archiviste: {e}")
                
        # Timer pour Archiviste
        self.archiviste_timer = threading.Timer(delay, send_archiviste_response)
        self.archiviste_timer.start()
        
    def get_conversation_messages(self) -> List[Dict[str, Any]]:
        """Retourne les messages de conversation AUTHENTIQUES uniquement"""
        return [msg for msg in self.conversation_messages if msg.get("api_authentic", False)]
        
    def is_conversation_active(self) -> bool:
        """Vérifie si une conversation est active"""
        return self.active_session is not None and self.active_session.get("is_active", False)
        
    def get_session_info(self) -> Dict[str, Any]:
        """Retourne les informations de session active"""
        if not self.active_session:
            return {}
            
        return {
            "session_id": self.active_session["session_id"],
            "trigger_type": self.active_session["trigger_type"],
            "start_time": self.active_session["start_time"],
            "duration": time.time() - self.active_session["start_time"],
            "message_count": len(self.conversation_messages),
            "is_active": self.active_session["is_active"]
        }

# Compatibilité avec l'ancien système - DEPRECATED
class ReflectionObserver:
    """Classe de compatibilité - utilisez ConversationManager à la place"""
    
    def __init__(self, *args, **kwargs):
        print("[REFLECTION-OBSERVER] DEPRECATED - Utilisez ConversationManager")
        self.on_message_received = None
        
    def start_reflection(self, *args, **kwargs):
        print("[REFLECTION-OBSERVER] Méthode deprecated - utilisez start_conversation")
        return "legacy_session"
        
    def stop_reflection(self, *args, **kwargs):
        print("[REFLECTION-OBSERVER] Méthode deprecated - utilisez stop_conversation")
        pass