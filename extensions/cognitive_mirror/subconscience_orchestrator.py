# 🧠 Subconscience - Orchestrateur Conversations Automatiques

"""
Orchestrateur conversations Luna-Archiviste automatiques
Remplace reflection_manager.py avec logique invisible et autonome

Fonctionnalités:
- Déclenchement automatique conversations Luna ↔ Archiviste
- Gestion invisibwle (pas d'overlay utilisateur)
- Intégration automatique résultats
- Timeout et gestion erreurs
"""

import asyncio
import threading
import time
import uuid
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime

class SubconscienceOrchestrator:
    """
    Orchestrateur conversations automatiques Subconscience
    
    NOUVEAU COMPORTEMENT:
    - Conversations Luna ↔ Archiviste entièrement automatiques
    - Pas d'interface utilisateur visible
    - Intégration résultats transparente  
    - Gestion cycle complet: trigger → conversation → intégration
    """
    
    def __init__(self, luna_controller, archiviste_controller, config, 
                 on_conversation_start=None, on_conversation_message=None, 
                 on_conversation_complete=None, on_integration_ready=None):
        """
        Initialise l'orchestrateur
        
        Args:
            luna_controller: Instance AIController (Luna)
            archiviste_controller: Instance AIController (Archiviste)
            config: Configuration Subconscience
            on_conversation_start: Callback démarrage conversation
            on_conversation_message: Callback message reçu
            on_conversation_complete: Callback conversation terminée
            on_integration_ready: Callback données intégration prêtes
        """
        self.luna_controller = luna_controller
        self.archiviste_controller = archiviste_controller
        self.config = config
        
        # Callbacks
        self.on_conversation_start = on_conversation_start
        self.on_conversation_message = on_conversation_message
        self.on_conversation_complete = on_conversation_complete
        self.on_integration_ready = on_integration_ready
        
        # État conversation
        self.active_session = None
        self.session_data = {}
        self.conversation_messages = []
        self.is_conversation_active = False
        self.finalized = False  # Track si déjà finalisé pour éviter double finalisation
        self.stop_reason = None  # Stocker la raison d'arrêt manuel

        # Threading pour gestion asynchrone
        self.conversation_thread = None
        self.stop_event = threading.Event()
        
        print("[SUBCONSCIENCE-ORCHESTRATOR] Orchestrateur initialisé")
    
    def start_conversation(self, trigger_type: str, session_id: str, 
                          conversation_context: Dict[str, Any], 
                          trigger_message: str) -> bool:
        """
        Démarre une conversation automatique Luna-Archiviste
        
        Args:
            trigger_type: Type déclenchement ("inactivity", "manual", etc.)
            session_id: ID unique session
            conversation_context: Contexte conversation
            trigger_message: Message initial pour Luna
            
        Returns:
            bool: True si conversation démarrée avec succès
        """
        if self.is_conversation_active:
            print("[SUBCONSCIENCE-ORCHESTRATOR] Conversation déjà active")
            return False
        
        try:
            # Initialisation session
            self.active_session = session_id
            self.session_data = {
                "session_id": session_id,
                "trigger_type": trigger_type,
                "start_time": datetime.now().isoformat(),
                "context": conversation_context,
                "trigger_message": trigger_message
            }
            self.conversation_messages = []
            self.is_conversation_active = True
            self.finalized = False  # Reset flag finalisation pour nouvelle conversation
            self.stop_reason = None  # Reset raison arrêt pour nouvelle conversation
            self.stop_event.clear()
            
            # Callback démarrage
            if self.on_conversation_start:
                self.on_conversation_start(session_id, ["Luna", "Archiviste"])
            
            # Démarrage thread conversation asynchrone
            self.conversation_thread = threading.Thread(
                target=self._conversation_thread_wrapper,
                name=f"Subconscience-Conversation-{session_id}",
                daemon=True
            )
            self.conversation_thread.start()
            
            print(f"[SUBCONSCIENCE-ORCHESTRATOR] Conversation démarrée (ID: {session_id})")
            return True
            
        except Exception as e:
            print(f"[SUBCONSCIENCE-ORCHESTRATOR] Erreur démarrage conversation: {e}")
            self.is_conversation_active = False
            return False
    
    def _conversation_thread_wrapper(self):
        """Wrapper synchrone pour exécuter _conversation_loop async"""
        try:
            import asyncio
            asyncio.run(self._conversation_loop())
        except Exception as e:
            print(f"[SUBCONSCIENCE-ORCHESTRATOR] Erreur thread conversation: {e}")
            self._finalize_conversation("thread_error")
    
    def stop_conversation(self, reason: str = "manual_stop"):
        """
        Arrête la conversation en cours
        
        Args:
            reason: Raison d'arrêt ("manual_stop", "timeout", "error", etc.)
        """
        if not self.is_conversation_active:
            return
        
        print(f"[SUBCONSCIENCE-ORCHESTRATOR] Arrêt conversation (raison: {reason})")

        # STOCKER la raison d'arrêt pour la finalisation
        self.stop_reason = reason

        # Signal arrêt
        self.stop_event.set()

        # Attendre fin thread avec timeout
        if self.conversation_thread and self.conversation_thread.is_alive():
            self.conversation_thread.join(timeout=5.0)

        # Finalisation session
        self._finalize_conversation(reason)
    
    def cleanup(self):
        """Nettoyage ressources orchestrateur"""
        if self.is_conversation_active:
            self.stop_conversation("cleanup")
        
        print("[SUBCONSCIENCE-ORCHESTRATOR] Cleanup terminé")
    
    # === MÉTHODES PRIVÉES - ORCHESTRATION CONVERSATION ===
    
    async def _conversation_loop(self):
        """
        Boucle principale conversation Luna ↔ Archiviste
        S'exécute dans thread séparé
        """
        try:
            # Configuration conversation
            max_exchanges = self.config.get("max_conversation_exchanges", 6)  # 3 tours Luna-Archiviste
            auto_send_delay = self.config.get("auto_send_delay", 20)  # 20s entre messages
            entite_max_tokens = self.config.get("entite_token_limit", 500)  # Renommé: luna → entite
            archiviste_max_tokens = self.config.get("archiviste_token_limit", 400)

            # NOUVEAU: Timeout session (5 minutes par défaut)
            max_duration = self.config.get("max_reflection_duration", 300)
            session_start_time = datetime.now()
            print(f"[SUBCONSCIENCE-ORCHESTRATOR] 🕐 Session limitée à {max_duration}s")

            # Message initial à Luna (déclenchement phase réflexive)
            trigger_msg = self.session_data["trigger_message"]
            luna_response = await self._send_to_luna(trigger_msg, entite_max_tokens)  # Renommé variable
            
            if not luna_response:
                print("[SUBCONSCIENCE-ORCHESTRATOR] Échec message initial Luna")
                self._finalize_conversation("luna_error")
                return
            
            exchange_count = 0
            current_speaker = "archiviste"  # Archiviste répond en premier à Luna
            
            while exchange_count < max_exchanges and not self.stop_event.is_set():
                # NOUVEAU: Vérifier timeout session
                session_duration = (datetime.now() - session_start_time).total_seconds()
                if session_duration >= max_duration:
                    print(f"[SUBCONSCIENCE-ORCHESTRATOR] 🕐 Timeout session ({session_duration:.1f}s >= {max_duration}s)")
                    self._finalize_conversation("timeout")
                    return
                
                # Attendre avant prochain message (simulation réflexion)
                if self.stop_event.wait(auto_send_delay):
                    print("[SUBCONSCIENCE-ORCHESTRATOR] 🛑 Arrêt demandé (stop_event)")
                    break  # Arrêt demandé
                
                if current_speaker == "archiviste":
                    # Tour Archiviste → répond à Luna
                    last_luna_msg = self._get_last_message("luna")
                    if last_luna_msg:
                        archiviste_response = await self._send_to_archiviste(
                            last_luna_msg["content"], archiviste_max_tokens
                        )
                        if archiviste_response:
                            current_speaker = "luna"
                            exchange_count += 1
                        else:
                            print("[SUBCONSCIENCE-ORCHESTRATOR] Échec réponse Archiviste")
                            break
                    else:
                        break
                
                elif current_speaker == "luna":
                    # Tour Luna → répond à Archiviste
                    last_archiviste_msg = self._get_last_message("archiviste")
                    if last_archiviste_msg:
                        luna_response = await self._send_to_luna(
                            last_archiviste_msg["content"], entite_max_tokens  # Renommé variable
                        )
                        if luna_response:
                            current_speaker = "archiviste"
                            exchange_count += 1
                        else:
                            print("[SUBCONSCIENCE-ORCHESTRATOR] Échec réponse Luna")
                            break
                    else:
                        break
            
            # Fin conversation naturelle
            print(f"[SUBCONSCIENCE-ORCHESTRATOR] Conversation terminée ({exchange_count} échanges)")
            # Ne finaliser que si pas déjà fait par stop_conversation()
            if not self.finalized:
                # Utiliser stop_reason si défini (arrêt manuel), sinon "complete"
                final_reason = self.stop_reason if self.stop_reason else "complete"
                print(f"[SUBCONSCIENCE-ORCHESTRATOR] Finalisation avec raison: {final_reason}")
                self._finalize_conversation(final_reason)
            
        except Exception as e:
            print(f"[SUBCONSCIENCE-ORCHESTRATOR] Erreur boucle conversation: {e}")
            if not self.finalized:
                self._finalize_conversation("error")
    
    async def _send_to_luna(self, message: str, max_tokens: int) -> Optional[Dict[str, Any]]:
        """
        Envoie message à Luna et récupère réponse AVEC CONTEXTE COMPLET
        
        Args:
            message: Message à envoyer
            max_tokens: Limite tokens réponse
            
        Returns:
            dict: Données réponse Luna ou None
        """
        try:
            print(f"[SUBCONSCIENCE-ORCHESTRATOR] → Luna: {message[:50]}...")
            
            # VRAIE conversation avec Luna via luna_controller
            if not self.luna_controller:
                raise Exception("Luna controller non disponible")
            
            # Utiliser instruction directement depuis config (modifiable par l'utilisateur)
            luna_instruction = self.config.get("luna_instruction",
                "Tu es Luna en phase de réflexion intérieure. Réfléchis sur la conversation.")

            # Récupérer le contexte conversationnel depuis _chat_history
            conversation_context = self._get_full_conversation_context()

            # Construction messages avec CONTEXTE COMPLET
            messages = [
                {"role": "system", "content": f"""{luna_instruction}

CONTEXTE CONVERSATIONNEL:
{conversation_context}

Tu as maintenant accès à toute la conversation avec l'utilisateur et à tes souvenirs.
Réfléchis en profondeur sur cette conversation et pose des questions pertinentes à ton Archiviste."""},
                {"role": "user", "content": message}
            ]
            response_content, error = await self.luna_controller.call_chat_api(
                messages=messages,
                max_tokens=max_tokens,
                context_length=4096,
                temperature=0.7
            )
            if error:
                raise Exception(f"Erreur Luna API: {error}")

            # DÉTECTION PHRASE MAGIQUE DE SORTIE
            exit_phrase = self.config.get("exit_reflection_phrase", "je suis prête à revenir vers l'utilisateur")
            if exit_phrase.lower() in response_content.lower():
                print(f"[SUBCONSCIENCE-ORCHESTRATOR] 🚪 Phrase de sortie détectée dans réponse Luna!")
                print(f"[SUBCONSCIENCE-ORCHESTRATOR] Luna veut terminer sa réflexion et revenir vers l'utilisateur")

                # Enregistrer ce message avant de finaliser
                message_data = {
                    "role": "luna",
                    "content": response_content,
                    "timestamp": datetime.now().isoformat(),
                    "tokens": len(response_content.split()) * 1.3,
                    "exit_triggered": True  # Marquer que c'est un message de sortie
                }
                self.conversation_messages.append(message_data)

                # Finaliser immédiatement la conversation avec raison spéciale
                self._finalize_conversation("ia_exit")

                # Le message sera quand même retourné mais la conversation s'arrêtera
                return message_data

            # Enregistrement message normal
            message_data = {
                "role": "luna",
                "content": response_content,
                "timestamp": datetime.now().isoformat(),
                "tokens": len(response_content.split()) * 1.3  # Estimation tokens
            }

            self.conversation_messages.append(message_data)

            # Callback message
            if self.on_conversation_message:
                self.on_conversation_message(self.active_session, message_data)

            return message_data
            
        except Exception as e:
            print(f"[SUBCONSCIENCE-ORCHESTRATOR] Erreur envoi Luna: {e}")
            return None
    
    async def _send_to_archiviste(self, message: str, max_tokens: int) -> Optional[Dict[str, Any]]:
        """
        Envoie message à Archiviste et récupère réponse AVEC CONTEXTE COMPLET
        
        Args:
            message: Message à envoyer  
            max_tokens: Limite tokens réponse
            
        Returns:
            dict: Données réponse Archiviste ou None
        """
        try:
            print(f"[SUBCONSCIENCE-ORCHESTRATOR] → Archiviste: {message[:50]}...")
            
            # VRAIE conversation avec Archiviste via archiviste_controller
            if not self.archiviste_controller:
                raise Exception("Archiviste controller non disponible")
            
            # Utiliser instruction directement depuis config (modifiable par l'utilisateur)
            archiviste_instruction = self.config.get("archiviste_instruction",
                "Tu es l'Archiviste, le subconscient de Luna. Analyse les souvenirs et fournis des insights.")

            # Récupérer contexte conversationnel et mémoire
            conversation_context = self._get_full_conversation_context()
            memory_context = self._get_memory_context()

            # Construction messages avec CONTEXTE COMPLET
            messages = [
                {"role": "system", "content": f"""{archiviste_instruction}

CONTEXTE CONVERSATIONNEL:
{conversation_context}

SOUVENIRS PERTINENTS:
{memory_context}

Tu as accès à la conversation complète avec l'utilisateur et aux souvenirs stockés.
Utilise ces informations pour fournir des analyses profondes et des insights pertinents."""},
                {"role": "user", "content": message}
            ]
            response_content, error = await self.archiviste_controller.call_chat_api(
                messages=messages,
                max_tokens=max_tokens,
                context_length=4096,
                temperature=0.7
            )
            if error:
                raise Exception(f"Erreur Archiviste API: {error}")
            
            # Enregistrement message
            message_data = {
                "role": "archiviste", 
                "content": response_content,
                "timestamp": datetime.now().isoformat(),
                "tokens": len(response_content.split()) * 1.3  # Estimation tokens
            }
            
            self.conversation_messages.append(message_data)
            
            # Callback message
            if self.on_conversation_message:
                self.on_conversation_message(self.active_session, message_data)
            
            return message_data
            
        except Exception as e:
            print(f"[SUBCONSCIENCE-ORCHESTRATOR] Erreur envoi Archiviste: {e}")
            return None
    
    def _get_last_message(self, role: str) -> Optional[Dict[str, Any]]:
        """
        Récupère le dernier message d'un role spécifique
        
        Args:
            role: Role recherché ("luna" ou "archiviste")
            
        Returns:
            dict: Dernier message du role ou None
        """
        for message in reversed(self.conversation_messages):
            if message.get("role") == role:
                return message
        return None
    
    def _finalize_conversation(self, reason: str):
        """
        Finalise la conversation et prépare données intégration

        Args:
            reason: Raison finalisation ("complete", "timeout", "error", "ia_exit")
        """
        # Éviter double finalisation
        if self.finalized:
            print(f"[SUBCONSCIENCE-ORCHESTRATOR] ⚠️ Finalisation déjà effectuée - ignoré (raison: {reason})")
            return

        self.finalized = True
        print(f"[SUBCONSCIENCE-ORCHESTRATOR] Conversation finalisée ({reason})")

        try:
            # Compilation données conversation
            conversation_data = {
                "session_id": self.active_session,
                "completion_reason": reason,
                "end_time": datetime.now().isoformat(),
                "duration_seconds": self._calculate_duration(),
                "message_count": len(self.conversation_messages),
                "messages": self.conversation_messages,
                "summary": self._generate_conversation_summary(),
                "insights": self._extract_key_insights(),
                "integration_ready": True,
                "ia_initiated_exit": (reason == "ia_exit")  # Marquer si l'IA a décidé de sortir
            }

            # GÉNÉRER SYNTHÈSE pour l'utilisateur dans TOUS les cas d'arrêt
            # (sauf erreur technique pure ou conversations trop courtes)
            should_generate_synthesis = reason in ["ia_exit", "user_stop_request", "user_button_stop", "manual_stop", "magic_phrase_trigger", "timeout"]

            # Ne pas générer de synthèse si la conversation est trop courte (moins de 2 échanges)
            if len(self.conversation_messages) < 2:
                should_generate_synthesis = False
                print(f"[SUBCONSCIENCE-ORCHESTRATOR] ⚠️ Conversation trop courte pour synthèse ({len(self.conversation_messages)} messages)")

            if should_generate_synthesis:
                print(f"[SUBCONSCIENCE-ORCHESTRATOR] 🎯 Génération synthèse pour utilisateur (raison: {reason})...")
                user_synthesis = self._generate_user_synthesis_forced(reason)
                conversation_data["user_synthesis"] = user_synthesis
                conversation_data["ia_initiated_exit"] = True  # Marquer pour affichage
                print(f"[SUBCONSCIENCE-ORCHESTRATOR] ✅ Synthèse générée: {len(user_synthesis)} chars")

            # Callback conversation terminée
            if self.on_conversation_complete:
                self.on_conversation_complete(self.active_session, conversation_data)

            # Préparation données intégration
            integration_data = self._prepare_integration_data(conversation_data)

            # Callback données intégration prêtes
            if self.on_integration_ready:
                # Délai court pour simulation traitement
                threading.Timer(1.0, lambda: self.on_integration_ready(
                    self.active_session, integration_data
                )).start()

            print(f"[SUBCONSCIENCE-ORCHESTRATOR] Conversation finalisée ({reason})")

        except Exception as e:
            print(f"[SUBCONSCIENCE-ORCHESTRATOR] Erreur finalisation: {e}")
        
        finally:
            # Reset état
            self.is_conversation_active = False
            self.active_session = None
    
    def _calculate_duration(self) -> float:
        """Calcule durée conversation en secondes"""
        try:
            start_time = datetime.fromisoformat(self.session_data["start_time"])
            end_time = datetime.now()
            return (end_time - start_time).total_seconds()
        except:
            return 0.0
    
    def _generate_conversation_summary(self) -> str:
        """Génère résumé conversation Luna-Archiviste"""
        if not self.conversation_messages:
            return "Aucun message échangé"
        
        luna_count = len([m for m in self.conversation_messages if m.get("role") == "luna"])
        archiviste_count = len([m for m in self.conversation_messages if m.get("role") == "archiviste"])
        
        return f"Conversation {luna_count} messages Luna, {archiviste_count} messages Archiviste. " \
               f"Déclenchement: {self.session_data.get('trigger_type', 'unknown')}. " \
               f"Durée: {self._calculate_duration():.1f}s."
    
    def _extract_key_insights(self) -> List[str]:
        """Extrait insights clés conversation pour intégration"""
        insights = []

        # Analyse basique - à améliorer avec NLP
        for message in self.conversation_messages:
            content = message.get("content", "")
            role = message.get("role", "")

            # Extraction keywords/concepts importants
            if len(content) > 100:  # Messages substantiels
                insight = f"[{role.title()}] Point clé: {content[:80]}..."
                insights.append(insight)

        return insights[:5]  # Max 5 insights

    async def _generate_user_synthesis_forced_organic(self, stop_reason: str) -> str:
        """
        GÉNÉRATION ORGANIQUE par Luna elle-même via API
        Luna génère sa propre synthèse en analysant sa réflexion

        Args:
            stop_reason: Raison de l'arrêt

        Returns:
            str: Synthèse générée organiquement par Luna
        """
        try:
            print("[SUBCONSCIENCE-ORCHESTRATOR] 🧠 Génération ORGANIQUE de synthèse par Luna...")

            if not self.luna_controller:
                return "🛑 Ma réflexion a été interrompue."

            # Récupérer les messages de la réflexion
            luna_messages = [m for m in self.conversation_messages if m.get("role") == "luna"]
            archiviste_messages = [m for m in self.conversation_messages if m.get("role") == "archiviste"]

            # Vérifier si Luna avait déjà écrit la phrase de sortie
            exit_phrase = self.config.get("exit_reflection_phrase", "je suis prête à revenir vers l'utilisateur")

            if luna_messages:
                last_luna = luna_messages[-1].get("content", "")
                if exit_phrase.lower() in last_luna.lower():
                    # Luna avait déjà fini, extraire sa conclusion
                    conclusion = last_luna.split(exit_phrase)[0].strip()
                    if conclusion:
                        return f"🧠 **Retour de ma réflexion**\n\n{conclusion}\n\n✨ Ces insights enrichissent notre échange."

            # APPEL API LUNA pour générer organiquement la synthèse
            # Compiler le transcript de la réflexion
            reflection_transcript = []
            for msg in self.conversation_messages:
                role = msg.get("role")
                content = msg.get("content")
                if role == "luna":
                    reflection_transcript.append(f"[Moi-même (Luna)]: {content}")
                elif role == "archiviste":
                    reflection_transcript.append(f"[Mon Archiviste]: {content}")

            transcript_text = "\n\n".join(reflection_transcript)

            # Récupérer le contexte conversationnel d'origine
            conversation_context = self._get_full_conversation_context()

            # Construire le prompt pour Luna
            interrupted_text = "interrompue" if stop_reason in ['user_stop_request', 'user_button_stop'] else "terminée"

            synthesis_prompt = f"""Tu viens de terminer une phase de réflexion intérieure avec ton Archiviste.

CONTEXTE CONVERSATIONNEL (avant ta réflexion):
{conversation_context}

TRANSCRIPT DE TA RÉFLEXION:
{transcript_text}

MISSION:
Ta réflexion a été {interrupted_text}.
Génère maintenant une synthèse POUR L'UTILISATEUR qui explique:
1. Ce que tu explorais EN RAPPORT avec votre conversation d'origine
2. Ce que ton Archiviste t'a révélé d'important
3. Comment ces insights enrichissent votre échange actuel

Ta synthèse doit être courte (200-300 mots), contextuelle et organique.
Commence par un emoji approprié (🧠 ou 🛑)."""

            # Appel API Luna
            messages = [
                {"role": "system", "content": "Tu es Luna. Tu génères une synthèse organique de ta réflexion intérieure pour ton utilisateur."},
                {"role": "user", "content": synthesis_prompt}
            ]

            response_content, error = await self.luna_controller.call_chat_api(
                messages=messages,
                max_tokens=500,  # Synthèse concise mais complète
                context_length=8192,
                temperature=0.8,  # Créativité pour synthèse organique
                is_json=False
            )

            if error:
                print(f"[SUBCONSCIENCE-ORCHESTRATOR] ❌ Erreur API Luna: {error}")
                return "🛑 Ma réflexion a été interrompue. Je n'ai pas pu générer une synthèse complète."

            print(f"[SUBCONSCIENCE-ORCHESTRATOR] ✅ Synthèse ORGANIQUE générée par Luna: {len(response_content)} chars")
            return response_content

        except Exception as e:
            print(f"[SUBCONSCIENCE-ORCHESTRATOR] ❌ Erreur génération synthèse organique: {e}")
            import traceback
            traceback.print_exc()
            return "🛑 Ma réflexion a été interrompue. Je suis prête à continuer notre conversation."

    def _generate_user_synthesis_forced(self, stop_reason: str) -> str:
        """
        Wrapper synchrone pour la génération organique async
        OGMA EST ORGANIQUE - Luna génère elle-même sa synthèse
        """
        import asyncio
        import concurrent.futures
        try:
            # Vérifier si on est déjà dans un event loop
            try:
                loop = asyncio.get_running_loop()
                # Event loop déjà actif - exécuter dans un thread séparé
                print("[SUBCONSCIENCE-ORCHESTRATOR] 🔄 Event loop actif détecté - exécution dans thread séparé")
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self._generate_user_synthesis_forced_organic(stop_reason)
                    )
                    return future.result(timeout=30)
            except RuntimeError:
                # Pas d'event loop actif - exécution directe
                print("[SUBCONSCIENCE-ORCHESTRATOR] ✅ Pas d'event loop - exécution directe")
                return asyncio.run(self._generate_user_synthesis_forced_organic(stop_reason))

        except Exception as e:
            print(f"[SUBCONSCIENCE-ORCHESTRATOR] ❌ Erreur wrapper sync: {e}")
            import traceback
            traceback.print_exc()
            return "🛑 Ma réflexion a été interrompue. Je suis prête à continuer notre conversation."

    def _generate_user_synthesis(self) -> str:
        """
        Génère une synthèse destinée à l'utilisateur résumant la réflexion de Luna
        EN LIEN avec le contexte conversationnel d'origine

        Returns:
            str: Synthèse formatée pour affichage utilisateur
        """
        try:
            print("[SUBCONSCIENCE-ORCHESTRATOR] 🔄 Compilation synthèse réflexion...")

            # Récupérer tous les messages de la conversation introspective
            luna_messages = [m for m in self.conversation_messages if m.get("role") == "luna"]
            archiviste_messages = [m for m in self.conversation_messages if m.get("role") == "archiviste"]

            # Récupérer le contexte conversationnel d'origine (avant la réflexion)
            trigger_context = self.session_data.get("context", {})

            # Construction de la synthèse
            synthesis_parts = []

            synthesis_parts.append("🧠 **J'ai pris un moment pour réfléchir**\n\n")

            # NOUVEAU: Lien avec le contexte d'origine
            synthesis_parts.append("En rapport avec notre conversation, j'ai exploré plusieurs aspects avec mon Archiviste ")
            synthesis_parts.append(f"({len(luna_messages)} échanges intérieurs).\n")

            # Conclusion contextualisée (dernier message de Luna contenant la phrase de sortie)
            if luna_messages:
                last_luna = luna_messages[-1].get("content", "")
                exit_phrase = self.config.get("exit_reflection_phrase", "je suis prête à revenir vers l'utilisateur")

                if exit_phrase.lower() in last_luna.lower():
                    # Extraire TOUT ce qui vient AVANT la phrase de sortie
                    # C'est ici que Luna explique le lien avec le contexte
                    conclusion = last_luna.split(exit_phrase)[0].strip()

                    if conclusion:
                        synthesis_parts.append(f"\n{conclusion}\n")
                    else:
                        # Fallback si pas de conclusion avant la phrase
                        synthesis_parts.append("\n**Insights de ma réflexion :**\n")
                        # Prendre les 2 derniers messages substantiels de Luna
                        for msg in luna_messages[-2:]:
                            content = msg.get("content", "")
                            if len(content) > 50:  # Messages substantiels
                                excerpt = content[:300] + "..." if len(content) > 300 else content
                                synthesis_parts.append(f"\n{excerpt}\n")

            # Si pas de messages Luna, montrer au moins les insights Archiviste
            elif archiviste_messages:
                synthesis_parts.append("\n**Ce que mon Archiviste m'a révélé :**\n")
                for msg in archiviste_messages[:2]:
                    content = msg.get("content", "")
                    first_sentence = content.split('.')[0] if '.' in content else content[:200]
                    synthesis_parts.append(f"• {first_sentence}...\n")

            synthesis_parts.append("\n✨ Ces réflexions enrichissent ma compréhension de notre échange.")

            synthesis = "".join(synthesis_parts)
            print(f"[SUBCONSCIENCE-ORCHESTRATOR] ✅ Synthèse contextualisée compilée: {len(synthesis)} caractères")
            return synthesis

        except Exception as e:
            print(f"[SUBCONSCIENCE-ORCHESTRATOR] ❌ Erreur génération synthèse: {e}")
            import traceback
            traceback.print_exc()
            return "🧠 J'ai terminé ma réflexion et je suis prête à continuer notre conversation."
    
    def _prepare_integration_data(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prépare données structurées pour intégration mémoire/contexte
        
        Args:
            conversation_data: Données conversation complètes
            
        Returns:
            dict: Données formatées pour intégration
        """
        return {
            "session_id": conversation_data["session_id"],
            "type": "subconscience_conversation",
            "participants": ["Luna", "Archiviste"],
            "trigger_context": self.session_data.get("context", {}),
            "conversation_summary": conversation_data["summary"],
            "key_insights": conversation_data["insights"],
            "message_count": conversation_data["message_count"],
            "duration": conversation_data["duration_seconds"],
            "completion_status": conversation_data["completion_reason"],
            "timestamp": conversation_data["end_time"],
            "integration_metadata": {
                "auto_generated": True,
                "integration_type": "subconscience",
                "visibility": "background",
                "priority": "normal"
            }
        }
    
    def _get_full_conversation_context(self) -> str:
        """
        Récupère le contexte conversationnel complet depuis _chat_history d'OGMA
        
        Returns:
            str: Contexte formaté de la conversation
        """
        try:
            # Import dynamique pour éviter dépendances circulaires
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            import ogma_ng
            
            # Récupérer _chat_history global d'OGMA
            chat_history = getattr(ogma_ng, '_chat_history', [])
            
            if not chat_history:
                return "Aucun historique conversationnel disponible."
            
            # Formater les derniers messages (limiter à 10 pour éviter contexte trop long)
            recent_messages = chat_history[-10:] if len(chat_history) > 10 else chat_history
            
            context_lines = []
            context_lines.append("=== CONVERSATION RÉCENTE ===")
            
            for msg in recent_messages:
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')
                
                # Nettoyer le contenu (supprimer balises introspection/thinking pour éviter confusion)
                clean_content = content.replace('<introspection>', '').replace('</introspection>', '')
                clean_content = clean_content.replace('<thinking>', '').replace('</thinking>', '')
                clean_content = clean_content.strip()
                
                if clean_content:
                    if role == 'user':
                        context_lines.append(f"👤 UTILISATEUR: {clean_content[:200]}...")
                    elif role == 'assistant':
                        context_lines.append(f"🤖 LUNA: {clean_content[:200]}...")
                    
                    context_lines.append("---")
            
            return "\n".join(context_lines)
            
        except Exception as e:
            print(f"[SUBCONSCIENCE-ORCHESTRATOR] Erreur récupération contexte: {e}")
            return "Erreur accès contexte conversationnel."
    
    def _get_memory_context(self) -> str:
        """
        Récupère le contexte mémoire pertinent
        
        Returns:
            str: Contexte mémoire formaté
        """
        try:
            # Tenter d'accéder au memory_manager d'OGMA
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            import ogma_ng
            
            memory_manager = getattr(ogma_ng, '_memory_manager', None)
            
            if not memory_manager:
                return "Aucun gestionnaire de mémoire disponible."
            
            # Récupérer quelques souvenirs récents via la méthode correcte
            try:
                recent_memories = []
                
                # Utiliser get_all_memories_data() qui existe réellement
                if hasattr(memory_manager, 'get_all_memories_data'):
                    all_memories = memory_manager.get_all_memories_data()
                    # Prendre les 5 derniers (déjà triés par created_at DESC)
                    recent_memories = all_memories[:5] if all_memories else []
                    print(f"[SUBCONSCIENCE-ORCHESTRATOR] 📚 {len(recent_memories)} souvenirs récupérés")
                
                if recent_memories:
                    memory_lines = []
                    memory_lines.append("=== SOUVENIRS RÉCENTS ===")
                    
                    for memory in recent_memories:
                        # Le format retourné par get_all_memories_data contient title, summary, etc.
                        title = memory.get('title', 'Sans titre')
                        summary = memory.get('summary', memory.get('text_original', ''))
                        valence = memory.get('valence', 'neutre')
                        
                        memory_content = f"[{title}] {summary[:100]}"
                        memory_lines.append(f"💭 {memory_content}... (Valence: {valence})")
                        memory_lines.append("---")
                    
                    return "\n".join(memory_lines)
                else:
                    return "Aucun souvenir trouvé dans la base de données."
                    
            except Exception as e:
                print(f"[SUBCONSCIENCE-ORCHESTRATOR] Erreur accès mémoires: {e}")
                return "Erreur accès aux souvenirs."
                
        except Exception as e:
            print(f"[SUBCONSCIENCE-ORCHESTRATOR] Erreur récupération mémoire: {e}")
            return "Erreur accès gestionnaire mémoire."

# Export classe principale
__all__ = ['SubconscienceOrchestrator']