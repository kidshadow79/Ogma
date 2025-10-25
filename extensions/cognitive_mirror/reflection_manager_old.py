# 🧠 Cognitive Mirror - Gestionnaire de Réflexion

"""
Gestionnaire des sessions de réflexion entre IA et Archiviste
Orchestre les conversations visibles, génère le contexte et gère les timeouts
"""

import asyncio
import time
import threading
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import uuid

class ReflectionSession:
    """Représente une session de réflexion active"""
    
    def __init__(self, session_id: str, trigger_type: str, conversation_context: Dict[str, Any]):
        self.session_id = session_id
        self.trigger_type = trigger_type
        self.conversation_context = conversation_context
        self.start_time = time.time()
        
        # Messages de la réflexion
        self.messages: List[Dict[str, Any]] = []
        self.current_reflection_context = ""
        
        # État session
        self.is_active = True
        self.completion_reason = None
        
    def add_message(self, sender: str, content: str, timestamp: Optional[float] = None):
        """Ajoute un message à la session de réflexion"""
        message = {
            "id": f"msg_{len(self.messages)}_{uuid.uuid4().hex[:8]}",
            "sender": sender,  # "IA" ou "Archiviste"
            "content": content,
            "timestamp": timestamp or time.time()
        }
        self.messages.append(message)
        return message
    
    def get_duration(self) -> float:
        """Retourne la durée de la session en secondes"""
        return time.time() - self.start_time
    
    def get_message_count(self) -> int:
        """Retourne le nombre de messages échangés"""
        return len(self.messages)
    
    def set_context(self, context: str):
        """Met à jour le contexte de réflexion"""
        self.current_reflection_context = context

class ReflectionManager:
    """
    Gestionnaire des sessions de réflexion IA-Archiviste
    
    Responsabilités:
    - Orchestration conversations réflexives
    - Gestion timeout et limitations
    - Génération contexte enrichi
    - Interface avec contrôleurs IA OGMA
    """
    
    def __init__(self, chat_controller, archiviste_controller, config, on_reflection_complete: Optional[Callable] = None):
        """
        Initialise le gestionnaire de réflexion
        
        Args:
            chat_controller: Instance AIController (IA principale)
            archiviste_controller: Instance AIController (Archiviste)
            config: Instance CognitiveMirrorConfig
            on_reflection_complete: Callback(session_id, reflection_data)
        """
        self.chat_controller = chat_controller
        self.archiviste_controller = archiviste_controller
        self.config = config
        self.on_reflection_complete = on_reflection_complete
        
        # Sessions actives
        self.active_sessions: Dict[str, ReflectionSession] = {}
        
        # Configuration
        self.settings = self.config.get_reflection_settings()
        self.max_duration = self.settings["max_duration"]
        self.token_limit = self.settings["token_limit"]
        
        # Messages système
        self.system_messages = self.config.get_system_messages()
        
        # Threading pour génération asynchrone
        self.generation_thread = None
        
        print(f"[REFLECTION-MANAGER] 🧠 Gestionnaire initialisé (timeout: {self.max_duration}s)")
    
    def start_reflection(self, session_id: str, trigger_type: str, conversation_context: Dict[str, Any]) -> ReflectionSession:
        """
        Démarre une nouvelle session de réflexion
        
        Args:
            session_id: Identifiant unique de la session
            trigger_type: Type de déclenchement ("inactivity", "manual", etc.)
            conversation_context: Contexte de conversation actuel
        
        Returns:
            ReflectionSession: Session créée
        """
        if session_id in self.active_sessions:
            raise ValueError(f"Session {session_id} déjà active")
        
        # Création session
        session = ReflectionSession(session_id, trigger_type, conversation_context)
        self.active_sessions[session_id] = session
        
        # Démarrage génération asynchrone
        self._start_reflection_generation(session)
        
        print(f"[REFLECTION-MANAGER] 🚀 Session démarrée: {session_id} ({trigger_type})")
        return session
    
    def stop_reflection(self, session_id: str, reason: str = "user_return") -> Optional[str]:
        """
        Arrête une session de réflexion et retourne le contexte généré
        
        Args:
            session_id: Identifiant de la session
            reason: Raison d'arrêt ("user_return", "timeout", "manual", "error")
        
        Returns:
            str: Contexte de réflexion généré ou None
        """
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        session.is_active = False
        session.completion_reason = reason
        
        # Génération résumé final si messages disponibles
        reflection_context = self._generate_final_context(session)
        
        # Nettoyage
        del self.active_sessions[session_id]
        
        duration = session.get_duration()
        message_count = session.get_message_count()
        
        print(f"[REFLECTION-MANAGER] ✅ Session terminée: {session_id} ({reason}, {duration:.1f}s, {message_count} messages)")
        return reflection_context
    
    def check_timeout(self, session_id: str) -> bool:
        """
        Vérifie si une session a dépassé le timeout
        
        Args:
            session_id: Identifiant de la session
        
        Returns:
            bool: True si timeout dépassé
        """
        if session_id not in self.active_sessions:
            return False
        
        session = self.active_sessions[session_id]
        return session.get_duration() > self.max_duration
    
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retourne le statut d'une session active
        
        Args:
            session_id: Identifiant de la session
        
        Returns:
            dict: Statut de la session ou None
        """
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        return {
            "session_id": session_id,
            "trigger_type": session.trigger_type,
            "duration": session.get_duration(),
            "message_count": session.get_message_count(),
            "is_active": session.is_active,
            "time_remaining": max(0, self.max_duration - session.get_duration())
        }
    
    def update_timeout_settings(self):
        """Met à jour les paramètres de timeout depuis la config"""
        self.settings = self.config.get_reflection_settings()
        self.max_duration = self.settings["max_duration"]
        self.token_limit = self.settings["token_limit"]
        
        print(f"[REFLECTION-MANAGER] ⚙️ Timeout mis à jour: {self.max_duration}s")
    
    def cleanup(self):
        """Nettoyage et fermeture propre"""
        print("[REFLECTION-MANAGER] 🔄 Nettoyage gestionnaire...")
        
        # Arrêt sessions actives
        session_ids = list(self.active_sessions.keys())
        for session_id in session_ids:
            self.stop_reflection(session_id, reason="shutdown")
        
        print("[REFLECTION-MANAGER] ✅ Nettoyage terminé")
    
    # === MÉTHODES PRIVÉES ===
    
    def _start_reflection_generation(self, session: ReflectionSession):
        """Démarre la génération asynchrone de la réflexion"""
        self.generation_thread = threading.Thread(
            target=self._reflection_generation_loop,
            args=(session,),
            name=f"CognitiveMirror-Reflection-{session.session_id}",
            daemon=True
        )
        self.generation_thread.start()
    
    def _reflection_generation_loop(self, session: ReflectionSession):
        """
        Boucle de génération de la conversation réflexive
        Simule l'échange entre IA et Archiviste
        """
        try:
            print(f"[REFLECTION-MANAGER] 🧠 Génération réflexion démarrée: {session.session_id}")
            
            # Message de démarrage IA
            ia_start_message = self._generate_ia_opening_message_sync(session)
            session.add_message("IA", ia_start_message)
            print(f"[REFLECTION-MANAGER] 🤖 Message IA généré: {ia_start_message[:50]}...")
            
            if self.on_reflection_complete:
                print("[REFLECTION-MANAGER] 📨 Appel callback reflection_complete...")
                self.on_reflection_complete(session.session_id, {"new_message": {
                    "sender": "IA", "content": ia_start_message
                }})
                print("[REFLECTION-MANAGER] ✅ Callback envoyé")
            else:
                print("[REFLECTION-MANAGER] ⚠️ Aucun callback reflection_complete configuré")
            
            # Pause réaliste
            time.sleep(2)
            
            # Boucle conversation intelligente (dynamique basée sur l'IA)
            exchange_count = 0
            max_exchanges = 6  # Limite de sécurité pour éviter boucles infinies
            should_continue = True
            
            while should_continue and exchange_count < max_exchanges and session.is_active:
                
                # Réponse Archiviste
                archiviste_message = self._generate_archiviste_response(session, exchange_count)
                session.add_message("Archiviste", archiviste_message)
                
                if self.on_reflection_complete:
                    self.on_reflection_complete(session.session_id, {"new_message": {
                        "sender": "Archiviste", "content": archiviste_message
                    }})
                
                # Pause réaliste
                time.sleep(1.5)
                
                if not session.is_active:
                    break
                
                # Réaction IA
                ia_response = self._generate_ia_response(session, exchange_count)
                session.add_message("IA", ia_response)
                
                if self.on_reflection_complete:
                    self.on_reflection_complete(session.session_id, {"new_message": {
                        "sender": "IA", "content": ia_response
                    }})
                
                # Décision IA : continuer ou conclure ?
                should_continue = self._should_continue_reflection(ia_response, exchange_count)
                exchange_count += 1
                
                # Pause entre échanges
                if should_continue and exchange_count < max_exchanges:
                    time.sleep(2)
            
            # Message de conclusion Archiviste
            if session.is_active:
                conclusion = self._generate_reflection_conclusion(session)
                session.add_message("Archiviste", conclusion)
                session.set_context(self._generate_final_context(session))
                
                if self.on_reflection_complete:
                    self.on_reflection_complete(session.session_id, {"new_message": {
                        "sender": "Archiviste", "content": conclusion
                    }})
        
        except Exception as e:
            print(f"[REFLECTION-MANAGER] ❌ ERREUR CRITIQUE génération réflexion: {e}")
            import traceback
            traceback.print_exc()
            if session.is_active:
                session.add_message("System", f"❌ ÉCHEC GÉNÉRATION: {e}")
            # Re-raise pour voir l'erreur complète  
            raise
    
    def _generate_ia_opening_message_sync(self, session: ReflectionSession) -> str:
        """Version synchrone qui appelle la version async - SANS FALLBACK"""
        import asyncio
        import threading
        
        print(f"[REFLECTION-MANAGER] 🔍 Thread IA opening: {threading.current_thread().name}")
        
        try:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(self._run_ia_opening_in_new_loop, session)
                        result = future.result(timeout=10)
                        print(f"[REFLECTION-MANAGER] ✅ IA opening généré: {result[:50]}...")
                        return result
                else:
                    result = loop.run_until_complete(self._generate_ia_opening_message(session))
                    print(f"[REFLECTION-MANAGER] ✅ IA opening généré: {result[:50]}...")
                    return result
            except RuntimeError:
                result = self._run_ia_opening_in_new_loop(session)
                print(f"[REFLECTION-MANAGER] ✅ IA opening généré: {result[:50]}...")
                return result
        except Exception as e:
            print(f"[REFLECTION-MANAGER] ❌ Erreur IA opening: {e}")
            raise
    
    def _run_ia_opening_in_new_loop(self, session: ReflectionSession) -> str:
        """Exécute l'IA opening dans un nouveau loop asyncio"""
        import asyncio
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(self._generate_ia_opening_message(session))
            return result
        finally:
            loop.close()
    
    async def _generate_ia_opening_message(self, session: ReflectionSession) -> str:
        """Génère le message d'ouverture de l'IA via appel réel au contrôleur"""
        try:
            # Contexte basé sur le trigger
            trigger_context = {
                "no_message": "Notre utilisateur s'est arrêté d'écrire depuis un moment.",
                "no_typing": "Je ne détecte plus d'activité clavier de la part de notre utilisateur.",
                "manual": "Une réflexion a été demandée manuellement.",
                "timeout": "Il est temps de faire le point sur notre conversation."
            }
            
            # Éléments dynamiques pour variabilité
            import random
            
            variations_contexte = [
                f"Que penses-tu de cette pause de l'utilisateur ?",
                f"As-tu des insights sur cette situation ?",
                f"Comment interprètes-tu ce moment de silence ?",
                f"Que nous révèle ce comportement utilisateur ?",
                f"Archiviste, ton analyse de cette interaction ?",
                f"Comment devrions-nous interpréter cette pause ?",
                f"Que suggèrent tes données sur ce pattern ?"
            ]
            
            variations_approche = [
                "Comment mieux accompagner l'utilisateur ?",
                "Quelle stratégie adopter maintenant ?", 
                "Comment ajuster mon approche ?",
                "Que recommandes-tu pour la suite ?",
                "Comment optimiser notre interaction ?",
                "Quelle direction prendre maintenant ?",
                "Comment améliorer l'engagement ?"
            ]
            
            context_desc = trigger_context.get(session.trigger_type, "Analysons notre situation actuelle.")
            question_contexte = random.choice(variations_contexte)
            question_approche = random.choice(variations_approche)
            
            # Prompt dynamique pour l'IA principale
            prompt = f"""Tu es Luna, l'IA principale d'OGMA, et tu entres en mode réflexion interne avec l'Archiviste.

CONTEXTE: {context_desc}

SITUATION: L'utilisateur vient de s'arrêter d'interagir. C'est le moment de faire une analyse réflexive avec l'Archiviste pour comprendre l'interaction et préparer la suite.

CONVERSATION RÉCENTE: {session.conversation_context.get('recent_messages', 'Pas de contexte récent disponible')}

CONSIGNE: Commence une réflexion avec l'Archiviste. {question_contexte} {question_approche} Sois naturelle, comme Luna. Environ 1-2 phrases maximum.

IMPORTANT: Évite les formulations répétitives. Chaque réflexion doit être unique et contextuelle."""

            messages = [{"role": "user", "content": prompt}]
            
            # Appel réel au contrôleur IA
            response, error = await self.chat_controller.call_chat_api(
                messages=messages,
                max_tokens=150,
                context_length=4000, 
                temperature=0.7,
                is_json=False
            )
            
            if error:
                print(f"[REFLECTION-MANAGER] ❌ ERREUR génération message IA: {error}")
                raise Exception(f"Échec génération IA: {error}")
            
            if not response:
                print(f"[REFLECTION-MANAGER] ❌ RÉPONSE VIDE de l'IA")
                raise Exception("Réponse IA vide")
                
            print(f"[REFLECTION-MANAGER] ✅ Message IA généré: {response[:100]}...")
            return response.strip()
            
        except Exception as e:
            print(f"[REFLECTION-MANAGER] ❌ EXCEPTION génération message IA: {e}")
            raise
    
    def _generate_archiviste_response(self, session: ReflectionSession, exchange_count: int) -> str:
        """Version synchrone qui appelle la version async de l'Archiviste - SANS FALLBACK"""
        import asyncio
        import threading
        
        print(f"[REFLECTION-MANAGER] 🔍 Thread actuel: {threading.current_thread().name}")
        
        # Dans un thread séparé, créer un nouvel event loop
        try:
            # Essayer d'obtenir le loop actuel
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    print("[REFLECTION-MANAGER] 🔄 Loop en cours, utilisation ThreadPoolExecutor")
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(self._run_archiviste_in_new_loop, session, exchange_count)
                        result = future.result(timeout=15)
                        print(f"[REFLECTION-MANAGER] ✅ Archiviste réponse générée: {result[:50]}...")
                        return result
                else:
                    print("[REFLECTION-MANAGER] 🔄 Loop disponible, exécution directe")
                    result = loop.run_until_complete(self._generate_archiviste_response_async(session, exchange_count))
                    print(f"[REFLECTION-MANAGER] ✅ Archiviste réponse générée: {result[:50]}...")
                    return result
            except RuntimeError as e:
                print(f"[REFLECTION-MANAGER] ⚠️ Pas de loop dans ce thread: {e}")
                # Pas de loop dans ce thread, en créer un nouveau
                result = self._run_archiviste_in_new_loop(session, exchange_count)
                print(f"[REFLECTION-MANAGER] ✅ Archiviste réponse générée: {result[:50]}...")
                return result
                
        except Exception as e:
            print(f"[REFLECTION-MANAGER] ❌ Erreur configuration asyncio: {e}")
            raise
    
    def _run_archiviste_in_new_loop(self, session: ReflectionSession, exchange_count: int) -> str:
        """Exécute l'Archiviste dans un nouveau loop asyncio"""
        import asyncio
        
        # Créer un nouveau loop pour ce thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(self._generate_archiviste_response_async(session, exchange_count))
            return result
        finally:
            loop.close()

    async def _generate_archiviste_response_async(self, session: ReflectionSession, exchange_count: int) -> str:
        """Génère une vraie réponse de l'Archiviste basée sur le contexte"""
        try:
            # Contexte de la conversation en cours
            recent_messages = "\n".join([
                f"{msg['sender']}: {msg['content'][:100]}..." 
                for msg in session.messages[-3:] if len(session.messages) > 0
            ])
            
            # Adapter le prompt selon le numéro d'échange
            if exchange_count == 0:
                # Premier échange - Analyse des souvenirs
                prompt = f"""Tu es l'Archiviste d'OGMA. L'IA principale vient de t'interpeller pour analyser l'interaction avec l'utilisateur.

CONTEXTE RÉCENT:
{recent_messages}

TRIGGER: {session.trigger_type} - {session.conversation_context.get('trigger_context', 'Pause dans la conversation')}

MISSION: Analyse nos souvenirs sur l'utilisateur et cette interaction. Que peux-tu dire sur ses patterns, son engagement, ses préoccupations récurrentes ? Sois précis et utilise tes connaissances sur l'utilisateur.

Format: 1-2 phrases comme l'Archiviste, analytique et perspicace."""

            elif exchange_count == 1:
                # Deuxième échange - Insights comportementaux
                prompt = f"""Tu es l'Archiviste d'OGMA. Continue l'analyse de l'utilisateur.

CONTEXTE RÉCENT:
{recent_messages}

MISSION: Donne des insights comportementaux précis. Comment l'utilisateur réagit-il quand il fait ce type de pause ? Quelles approches lui conviennent le mieux selon tes données historiques ?

Format: 1-2 phrases analytiques sur ses préférences et son style de communication."""

            else:
                # Échanges suivants - Recommandations
                prompt = f"""Tu es l'Archiviste d'OGMA. Conclus ton analyse.

CONTEXTE RÉCENT:
{recent_messages}

MISSION: Recommande une stratégie d'aide optimale pour ce contexte. Que valorise l'utilisateur ? Comment Luna doit-elle adapter sa prochaine réponse ?

Format: 1-2 phrases de recommandations concrètes."""
            
            messages = [{"role": "user", "content": prompt}]
            
            # Appel réel à l'Archiviste
            response, error = await self.archiviste_controller.call_chat_api(
                messages=messages,
                max_tokens=120,
                context_length=4000,
                temperature=0.6,
                is_json=False
            )
            
            if error:
                print(f"[REFLECTION-MANAGER] ❌ ERREUR Archiviste: {error}")
                raise Exception(f"Échec génération Archiviste: {error}")
            
            if not response:
                print(f"[REFLECTION-MANAGER] ❌ RÉPONSE VIDE de l'Archiviste")  
                raise Exception("Réponse Archiviste vide")
                
            print(f"[REFLECTION-MANAGER] ✅ Archiviste réponse: {response[:100]}...")
            return response.strip()
            
        except Exception as e:
            print(f"[REFLECTION-MANAGER] ❌ EXCEPTION génération Archiviste: {e}")
            raise
    
    def _generate_ia_response(self, session: ReflectionSession, exchange_count: int) -> str:
        """Version synchrone qui appelle la version async de l'IA - SANS FALLBACK"""
        import asyncio
        import threading
        
        print(f"[REFLECTION-MANAGER] 🔍 Thread IA response: {threading.current_thread().name}")
        
        try:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(self._run_ia_response_in_new_loop, session, exchange_count)
                        result = future.result(timeout=15)
                        print(f"[REFLECTION-MANAGER] ✅ IA réponse générée: {result[:50]}...")
                        return result
                else:
                    result = loop.run_until_complete(self._generate_ia_response_async(session, exchange_count))
                    print(f"[REFLECTION-MANAGER] ✅ IA réponse générée: {result[:50]}...")
                    return result
            except RuntimeError:
                result = self._run_ia_response_in_new_loop(session, exchange_count)
                print(f"[REFLECTION-MANAGER] ✅ IA réponse générée: {result[:50]}...")
                return result
        except Exception as e:
            print(f"[REFLECTION-MANAGER] ❌ Erreur IA response: {e}")
            raise
    
    def _run_ia_response_in_new_loop(self, session: ReflectionSession, exchange_count: int) -> str:
        """Exécute l'IA response dans un nouveau loop asyncio"""
        import asyncio
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(self._generate_ia_response_async(session, exchange_count))
            return result
        finally:
            loop.close()

    async def _generate_ia_response_async(self, session: ReflectionSession, exchange_count: int) -> str:
        """Génère une vraie réponse de l'IA dans la conversation réflexive"""
        try:
            # Récupérer le dernier message de l'Archiviste pour contextualiser
            archiviste_last_msg = ""
            for msg in reversed(session.messages):
                if msg['sender'] == 'Archiviste':
                    archiviste_last_msg = msg['content']
                    break
            
            # Adapter le prompt selon le numéro d'échange
            if exchange_count == 0:
                prompt = f"""Tu es Luna, l'IA principale d'OGMA. L'Archiviste vient de te donner une analyse : "{archiviste_last_msg}"

MISSION: Réagis à cette analyse comme Luna. Montre que tu comprends et pose une question pertinente pour approfondir ou demande des conseils concrets.

STYLE: Naturel, comme Luna qui réfléchit et collabore avec l'Archiviste. 1-2 phrases.

Exemple: "Excellente analyse ! Comment puis-je adapter mon approche pour mieux répondre à ce pattern ?" """

            elif exchange_count == 1:
                prompt = f"""Tu es Luna, l'IA principale d'OGMA. L'Archiviste te conseille : "{archiviste_last_msg}"

MISSION: Montre que tu intègres ses recommandations et demande des précisions ou éléments concrets pour optimiser ton aide.

STYLE: Enthousiaste et collaborative, comme Luna qui veut bien faire. 1-2 phrases."""

            else:
                prompt = f"""Tu es Luna, l'IA principale d'OGMA. L'Archiviste conclut : "{archiviste_last_msg}"

MISSION: Remercie l'Archiviste et montre comment tu vas intégrer ses conseils dans ta prochaine interaction avec l'utilisateur.

STYLE: Reconnaissante et déterminée, comme Luna qui se prépare. 1-2 phrases."""
            
            messages = [{"role": "user", "content": prompt}]
            
            # Appel réel à l'IA principale
            response, error = await self.chat_controller.call_chat_api(
                messages=messages,
                max_tokens=100,
                context_length=4000,
                temperature=0.7,
                is_json=False
            )
            
            if error:
                print(f"[REFLECTION-MANAGER] ❌ ERREUR IA response: {error}")
                raise Exception(f"Échec génération IA response: {error}")
            
            if not response:
                print(f"[REFLECTION-MANAGER] ❌ RÉPONSE VIDE de l'IA response")
                raise Exception("Réponse IA response vide")
                
            print(f"[REFLECTION-MANAGER] ✅ IA response: {response[:100]}...")
            return response.strip()
            
        except Exception as e:
            print(f"[REFLECTION-MANAGER] ❌ EXCEPTION génération IA response: {e}")
            raise
    
    def _generate_reflection_conclusion(self, session: ReflectionSession) -> str:
        """Génère le message de conclusion de la réflexion"""
        duration = session.get_duration()
        message_count = session.get_message_count()
        
        return f"{self.system_messages['reflection_end']} Session complète en {duration:.1f}s avec {message_count} échanges. Créant souvenir REF#{int(time.time())} avec contexte et stratégie d'aide optimisée."
    
    def _generate_final_context(self, session: ReflectionSession) -> str:
        """
        Génère le contexte final de réflexion pour enrichissement de la conversation
        
        Args:
            session: Session de réflexion
        
        Returns:
            str: Résumé contexte pour enrichissement
        """
        if not session.messages:
            return ""
        
        # Extraction des insights clés
        key_insights = []
        for message in session.messages:
            if message["sender"] == "Archiviste" and "recommande" in message["content"]:
                # Extraction recommandation
                content = message["content"]
                if "je recommande" in content.lower():
                    insight = content.split("je recommande")[1].split(".")[0].strip()
                    key_insights.append(f"• {insight}")
        
        # Construction contexte enrichi
        context_parts = [
            f"Réflexion interne ({session.trigger_type}, {session.get_duration():.1f}s):"
        ]
        
        if key_insights:
            context_parts.append("Insights Archiviste:")
            context_parts.extend(key_insights)
        
        context_parts.append(
            f"Stratégie: Adapter réponse selon profil utilisateur analysé, privilégier approche personnalisée."
        )
        
        return " | ".join(context_parts)
    
    def enrich_conversation_context(self, conversation_context: Dict[str, Any]):
        """
        Enrichit le contexte de conversation en cours pour les futures réflexions
        
        Args:
            conversation_context: Contexte de la conversation actuelle
        """
        try:
            # Stocker le contexte pour la session active
            if hasattr(self, 'current_conversation_context'):
                self.current_conversation_context.update(conversation_context)
            else:
                self.current_conversation_context = conversation_context.copy()
            
            # Si une session de réflexion est active, enrichir son contexte
            for session in self.active_sessions.values():
                if session.is_active:
                    session.context.update(conversation_context)
        except Exception as e:
            print(f"[REFLECTION-MANAGER] ❌ Erreur enrichissement contexte: {e}")
    
    def _should_continue_reflection(self, last_ia_message: str, exchange_count: int) -> bool:
        """
        Détermine si la conversation de réflexion doit continuer
        basé sur le contenu du dernier message IA
        """
        # Mots/phrases qui indiquent une conclusion
        conclusion_indicators = [
            "merci", "parfait", "compris", "c'est clair", 
            "je vais", "je suis prête", "dès maintenant",
            "intégrer", "appliquer", "conclusion", "terminé"
        ]
        
        # Mots/phrases qui indiquent de continuer
        continue_indicators = [
            "?", "comment", "pourquoi", "que penses-tu",
            "peux-tu", "as-tu", "devrais-je", "pourrais-je",
            "préciser", "approfondir", "exemple"
        ]
        
        last_message_lower = last_ia_message.lower()
        
        # Si l'IA pose une question, on continue
        if any(indicator in last_message_lower for indicator in continue_indicators):
            print(f"[REFLECTION-MANAGER] 🔄 Continuation: question/demande détectée")
            return True
        
        # Si l'IA conclut, on arrête
        if any(indicator in last_message_lower for indicator in conclusion_indicators):
            print(f"[REFLECTION-MANAGER] 🏁 Conclusion: fin détectée")
            return False
        
        # Limite basée sur le nombre d'échanges (sécurité)
        if exchange_count >= 4:
            print(f"[REFLECTION-MANAGER] 🏁 Limite échanges atteinte: {exchange_count}")
            return False
        
        # Par défaut, continuer pour quelques échanges
        print(f"[REFLECTION-MANAGER] 🔄 Continuation: critères neutres")
        return True