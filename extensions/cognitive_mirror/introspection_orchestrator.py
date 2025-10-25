# 🧠 Introspection - Orchestrateur Dialogue IA Principale ↔ Archiviste

"""
Orchestrateur dialogue introspection v2.0

Gère le dialogue visible streaming entre IA Principale et Archiviste
Affichage temps réel dans boîte thinking
"""

import asyncio
import time
import json
import re
from typing import Optional, Dict, Any, List
from datetime import datetime


class IntrospectionOrchestrator:
    """
    Orchestrateur dialogue introspection IA Principale ↔ Archiviste

    Responsabilités:
    - Gestion dialogue séquentiel avec streaming
    - Détection phrases magiques (synthèse, sortie)
    - Extraction métadonnées IA (save_decision, importance)
    - Construction contexte complet pour chaque message
    """

    def __init__(self, config, chat_controller, archiviste_controller, memory_manager, settings_manager=None, on_message_callback=None):
        """
        Initialise orchestrateur

        Args:
            config: Instance CognitiveMirrorConfig
            chat_controller: AIController IA Principale
            archiviste_controller: AIController Archiviste
            memory_manager: MemoryManager OGMA
            settings_manager: SettingsManager pour accès aux prompts système
            on_message_callback: Callback(role, content) appelé pour chaque nouveau message
        """
        self.config = config
        self.chat_controller = chat_controller
        self.archiviste_controller = archiviste_controller
        self.memory_manager = memory_manager
        self.settings_manager = settings_manager
        self.on_message_callback = on_message_callback

        # État session
        self.current_session_id = None
        self.is_active = False
        self.should_stop = False
        
        # Callback rechargement config (synchronisation interface)
        self.on_config_reload_callbacks = []

        # Données session
        self.dialogue_messages = []
        self.main_ai_analysis = ""
        self.synthesis = ""
        self.save_metadata = {}

        print("[INTROSPECTION-ORCHESTRATOR] 🎭 Orchestrateur initialisé")

    async def run_introspection_dialogue(self, user_message: str, conversation_context: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """
        Lance session d'introspection complète

        Args:
            user_message: Message utilisateur
            conversation_context: Contexte conversationnel
            session_id: ID session

        Returns:
            Résultat complet avec final_response, save_decision, etc.
        """
        self.current_session_id = session_id
        self.is_active = True
        self.should_stop = False
        self.dialogue_messages = []

        print(f"[INTROSPECTION-ORCHESTRATOR] 🎬 Démarrage dialogue (session: {session_id})")

        start_time = time.time()

        try:
            # Configuration
            settings = self.config.get_introspection_settings()
            max_exchanges = settings["max_exchanges"]
            max_duration = settings["max_duration"]

            # PHASE 0: Accès direct mémoire IA Principale (NOUVEAU)
            print("[INTROSPECTION-ORCHESTRATOR] 🧠 Phase 0: Accès direct mémoire IA Principale")
            self.direct_memory_results = await self._main_ai_direct_memory_access(user_message, conversation_context)

            if not self.direct_memory_results:
                print("[INTROSPECTION-ORCHESTRATOR] ⚠️ Accès mémoire direct échoué, passage à l'analyse")
                self.direct_memory_results = "Aucun souvenir direct accessible."

            print(f"[INTROSPECTION-ORCHESTRATOR] 🔍 Accès mémoire terminé: {len(self.direct_memory_results)} chars")

            # PHASE 1: Analyse initiale IA Principale
            print("[INTROSPECTION-ORCHESTRATOR] 📊 Phase 1: Analyse initiale IA Principale")
            self.main_ai_analysis = await self._main_ai_initial_analysis(user_message, conversation_context)

            if not self.main_ai_analysis:
                return {"success": False, "error": "Échec analyse initiale"}
            
            # Affichage ÉTAPE 1 dans UI via callback
            if self.on_message_callback:
                await self.on_message_callback("analysis", self.main_ai_analysis)
                print(f"[INTROSPECTION-ORCHESTRATOR] 👁️ Analyse initiale affichée: {len(self.main_ai_analysis)} chars")

            # PHASE 2: Dialogue IA Principale ↔ Archiviste
            print(f"[INTROSPECTION-ORCHESTRATOR] 💬 Phase 2: Dialogue (max {max_exchanges} échanges)")
            exchange_count = 0

            while exchange_count < max_exchanges and not self.should_stop:
                # Vérifier timeout
                if time.time() - start_time > max_duration:
                    print("[INTROSPECTION-ORCHESTRATOR] ⏱️ Timeout atteint - arrêt dialogue")
                    break

                # IA Principale réfléchit / pose question Archiviste
                main_ai_message = await self._main_ai_reflection_step(
                    user_message, conversation_context, exchange_count
                )

                if not main_ai_message:
                    break

                message_data = {
                    "role": "main_ai",
                    "content": main_ai_message,
                    "timestamp": datetime.now().isoformat()
                }
                self.dialogue_messages.append(message_data)

                # Callback UI pour affichage temps réel
                if self.on_message_callback:
                    await self.on_message_callback("main_ai", main_ai_message)

                # Vérifier phrase de mémorisation pendant dialogue
                memorization_content = self._detect_memorization_phrase(main_ai_message)
                if memorization_content:
                    print(f"[INTROSPECTION-ORCHESTRATOR] 💾 Mémorisation détectée: {memorization_content[:50]}...")
                    # TODO: Déclencher mémorisation immédiate via memory_manager
                    # await self.memory_manager.memorize_immediate(memorization_content)

                # Vérifier si IA Principale prête pour synthèse
                if self._detect_synthesis_ready(main_ai_message):
                    print("[INTROSPECTION-ORCHESTRATOR] ✨ IA Principale prête pour synthèse")
                    break

                # Archiviste répond
                archiviste_response = await self._archiviste_response(
                    main_ai_message, conversation_context
                )

                if archiviste_response:
                    message_data = {
                        "role": "archiviste",
                        "content": archiviste_response,
                        "timestamp": datetime.now().isoformat()
                    }
                    self.dialogue_messages.append(message_data)

                    # Callback UI pour affichage temps réel
                    if self.on_message_callback:
                        await self.on_message_callback("archiviste", archiviste_response)

                exchange_count += 1

            # PHASE 3: Synthèse finale
            print("[INTROSPECTION-ORCHESTRATOR] 🎯 Phase 3: Synthèse finale")
            synthesis_result = await self._main_ai_generate_synthesis(
                user_message, conversation_context
            )

            if not synthesis_result:
                return {"success": False, "error": "Échec génération synthèse"}

            self.synthesis = synthesis_result["synthesis_text"]
            self.save_metadata = synthesis_result["metadata"]

            # Affichage synthèse dans boîte introspection via callback
            if self.on_message_callback:
                await self.on_message_callback("synthesis", self.synthesis)

            # Construction résultat final
            duration = time.time() - start_time

            result = {
                "success": True,
                "session_id": session_id,
                "duration": duration,
                "exchanges_count": len(self.dialogue_messages),

                # Contenu introspection
                "main_ai_analysis": self.main_ai_analysis,
                "dialogue_messages": self.dialogue_messages,
                "synthesis": self.synthesis,

                # Métadonnées IA
                "save_decision": self.save_metadata.get("save_decision", "no"),
                "importance": self.save_metadata.get("importance", 5),
                "save_reason": self.save_metadata.get("reason", ""),

                # Réponse finale pour utilisateur
                "final_response": synthesis_result.get("final_response", self.synthesis)
            }

            print(f"[INTROSPECTION-ORCHESTRATOR] ✅ Dialogue terminé ({duration:.1f}s, {exchange_count} échanges)")

            return result

        except Exception as e:
            print(f"[INTROSPECTION-ORCHESTRATOR] ❌ Erreur dialogue: {e}")
            import traceback
            traceback.print_exc()

            return {
                "success": False,
                "error": str(e),
                "session_id": session_id
            }

        finally:
            self.is_active = False
            self.current_session_id = None

    async def _main_ai_direct_memory_access(self, user_message: str, context: Dict[str, Any]) -> str:
        """ÉTAPE 0: Accès direct mémoire FAISS/SQLite par IA Principale (NON VISIBLE)"""
        try:
            # Construction prompt avec nouvelle instruction ÉTAPE 0
            instruction = self.config.get("direct_memory_access_instruction", "")
            conversation_context_str = self._format_conversation_context(context)

            prompt = instruction.format(
                user_message=user_message,
                conversation_context=conversation_context_str
            )

            # Appel IA Principale avec accès direct mémoire
            settings = self.config.get_introspection_settings()
            max_tokens = settings["main_ai_tokens_per_message"]  # -1 = illimité

            # IMPORTANT: Ici on donnera à l'IA un accès direct aux souvenirs
            # Pour l'instant, simulons cet accès en récupérant des souvenirs pertinents
            memory_results = await self._get_direct_memory_access(user_message, context)

            # Enrichir le prompt avec les résultats mémoire
            enriched_prompt = f"""{prompt}

RÉSULTATS DE RECHERCHE MÉMOIRE DIRECTE:
{memory_results}

Analyse maintenant ces souvenirs et note ce que tu veux développer."""

            response = await self._call_main_ai(enriched_prompt, max_tokens)

            print(f"[INTROSPECTION-ORCHESTRATOR] 🧠 Accès mémoire direct: {len(response)} chars")

            return response

        except Exception as e:
            print(f"[INTROSPECTION-ORCHESTRATOR] ❌ Erreur accès mémoire direct: {e}")
            return ""

    async def _main_ai_initial_analysis(self, user_message: str, context: Dict[str, Any]) -> str:
        """ÉTAPE 1: Analyse initiale par IA Principale (VISIBLE)"""
        try:
            # Construction prompt avec nouvelle instruction ÉTAPE 1
            instruction = self.config.get("initial_analysis_instruction", "")
            conversation_context_str = self._format_conversation_context(context)

            prompt = instruction.format(
                user_message=user_message,
                conversation_context=conversation_context_str
            )

            # Appel IA Principale (tokens illimités)
            settings = self.config.get_introspection_settings()
            max_tokens = settings["main_ai_tokens_per_message"]  # -1 = illimité

            response = await self._call_main_ai(prompt, max_tokens)

            print(f"[INTROSPECTION-ORCHESTRATOR] 💭 Analyse IA Principale: {len(response)} chars")

            return response

        except Exception as e:
            print(f"[INTROSPECTION-ORCHESTRATOR] ❌ Erreur analyse: {e}")
            return ""

    async def _main_ai_reflection_step(self, user_message: str, context: Dict[str, Any], exchange_num: int) -> str:
        """ÉTAPES 2-3: IA Principale demande explicitement ses souvenirs à l'Archiviste"""
        try:
            # Construction contexte dialogue actuel
            dialogue_history = self._format_dialogue_history()
            conversation_context_str = self._format_conversation_context(context)

            # Utiliser instruction IA Principale pour dialogue (étapes 2-3)
            instruction = self.config.get("main_ai_introspection_instruction", "")
            
            prompt = instruction.format(
                user_message=user_message,
                conversation_context=conversation_context_str,
                initial_analysis=self.main_ai_analysis or "Pas encore d'analyse disponible",
                dialogue_history=dialogue_history,
                exchange_number=exchange_num + 1,
                # Nouvelles variables contextuelles
                user_identity=context.get("user_identity", "Utilisateur"),
                main_ai_identity=context.get("main_ai_identity", "IA Principale"),
                relationship_context=context.get("relationship_context", ""),
                ego_prompt=context.get("ego_prompt", "")[:200] + "..." if len(context.get("ego_prompt", "")) > 200 else context.get("ego_prompt", "")
            )

            settings = self.config.get_introspection_settings()
            max_tokens = settings["main_ai_tokens_per_message"]  # -1 = illimité

            response = await self._call_main_ai(prompt, max_tokens)

            print(f"[INTROSPECTION-ORCHESTRATOR] 💭 IA Principale (échange {exchange_num}): {len(response)} chars")

            return response

        except Exception as e:
            print(f"[INTROSPECTION-ORCHESTRATOR] ❌ Erreur réflexion IA Principale: {e}")
            return ""

    async def _archiviste_response(self, main_ai_question: str, context: Dict[str, Any]) -> str:
        """ÉTAPES 2-3: Archiviste PASSIF répond aux demandes explicites de l'IA Principale"""
        try:
            # Construction prompt Archiviste (PASSIF) 
            instruction = self.config.get("archiviste_introspection_instruction", "")
            conversation_context_str = self._format_conversation_context(context)
            
            # Recherche souvenirs à la demande uniquement (pas de pré-chargement)
            memory_context = await self._get_memory_context_for_question(main_ai_question)

            prompt = instruction.format(
                main_ai_question=main_ai_question,
                conversation_context=conversation_context_str,
                memory_context=memory_context,
                # Nouvelles variables contextuelles pour l'Archiviste
                user_identity=context.get("user_identity", "Utilisateur"),
                main_ai_identity=context.get("main_ai_identity", "IA Principale"),
                relationship_context=context.get("relationship_context", ""),
                ego_prompt=context.get("ego_prompt", "")[:200] + "..." if len(context.get("ego_prompt", "")) > 200 else context.get("ego_prompt", "")
            )

            # Appel Archiviste (tokens illimités)
            settings = self.config.get_introspection_settings()
            max_tokens = settings["archiviste_tokens_per_message"]  # -1 = illimité

            response = await self._call_archiviste(prompt, max_tokens)

            print(f"[INTROSPECTION-ORCHESTRATOR] 📚 Archiviste: {len(response)} chars")

            return response

        except Exception as e:
            print(f"[INTROSPECTION-ORCHESTRATOR] ❌ Erreur Archiviste: {e}")
            return ""

    async def _main_ai_generate_synthesis(self, user_message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """ÉTAPE 4: IA Principale génère synthèse structurée + décision sauvegarde"""
        try:
            dialogue_history = self._format_dialogue_history()
            
            # Utiliser nouveau template synthèse structurée
            instruction = self.config.get("synthesis_structure_instruction", "")
            
            prompt = instruction.format(
                dialogue_history=dialogue_history,
                user_message=user_message
            )

            settings = self.config.get_introspection_settings()
            max_tokens = settings["main_ai_tokens_per_message"]  # -1 = illimité

            response = await self._call_main_ai(prompt, max_tokens)

            # Extraction métadonnées JSON
            metadata = self._extract_save_metadata(response)

            # Nettoyage réponse (retirer JSON)
            synthesis_text = re.sub(r'\{.*?"save_decision".*?\}', '', response, flags=re.DOTALL).strip()

            # Extraire la réponse finale pour l'utilisateur depuis la section "Réponse construite"
            final_response = self._extract_final_response_from_synthesis(synthesis_text)

            print(f"[INTROSPECTION-ORCHESTRATOR] ✨ Synthèse: {len(synthesis_text)} chars, réponse: {len(final_response)} chars, save={metadata.get('save_decision')}, importance={metadata.get('importance')}")

            return {
                "synthesis_text": synthesis_text,
                "metadata": metadata,
                "final_response": final_response
            }

        except Exception as e:
            print(f"[INTROSPECTION-ORCHESTRATOR] ❌ Erreur synthèse: {e}")
            return {}

    def _build_full_system_prompt(self) -> str:
        """
        Construit le prompt système complet pour Luna pendant l'introspection
        Inclut: ego_prompt + instructions système + contexte permanent
        """
        try:
            # 1. Récupérer l'ego prompt expansé
            from utils import get_ego_prompt
            ego_prompt = get_ego_prompt()
            
            # 2. Récupérer les instructions système principales
            system_prompt = ""
            try:
                # Récupérer le settings_manager comme dans ogma_ng.py
                if self.settings_manager:
                    settings_manager = self.settings_manager
                else:
                    # Fallback: importer depuis core_logic si disponible
                    from core_logic import SettingsManager
                    from pathlib import Path
                    settings_manager = SettingsManager(Path("data/settings.json"))
                
                system_prompt = settings_manager.settings.get('prompts', {}).get('instructions', '')
            except Exception as e:
                print(f"[INTROSPECTION-ORCHESTRATOR] ⚠️ Erreur récupération instructions: {e}")
                system_prompt = ""
            
            # 3. Récupérer le contexte permanent
            from logic_callbacks import get_persistent_context
            persistent_context = get_persistent_context()
            
            # 4. Construire le prompt complet (même logique que logic_callbacks.py)
            full_system_prompt = "\n\n".join(filter(None, [
                ego_prompt,           # 🧠 Identité Luna en première position
                system_prompt,        # 📋 Instructions système principales  
                persistent_context    # 📌 Contexte permanent
            ]))
            
            print(f"[INTROSPECTION-ORCHESTRATOR] 🧠 Full system prompt: {len(full_system_prompt)} chars")
            print(f"   - Ego prompt: {len(ego_prompt)} chars")
            print(f"   - System prompt: {len(system_prompt)} chars") 
            print(f"   - Persistent context: {len(persistent_context)} chars")
            
            return full_system_prompt
            
        except Exception as e:
            print(f"[INTROSPECTION-ORCHESTRATOR] ❌ Erreur construction full_system_prompt: {e}")
            # Fallback minimal pour éviter crash
            return "Tu es Luna, une IA avancée en mode introspection."

    async def _call_main_ai(self, prompt: str, max_tokens: int) -> str:
        """Appel API IA Principale avec prompt système complet (identité Luna)"""
        try:
            # Construction du prompt système complet avec identité Luna
            full_system_prompt = self._build_full_system_prompt()
            
            # Appel AIController IA Principale avec identité complète
            messages = [
                {"role": "system", "content": full_system_prompt},  # 🧠 Identité Luna complète
                {"role": "user", "content": prompt}
            ]
            
            response, error = await self.chat_controller.call_chat_api(
                messages=messages,
                max_tokens=max_tokens,
                context_length=8192,
                temperature=0.7,
                is_json=False
            )

            if error:
                print(f"[INTROSPECTION-ORCHESTRATOR] ❌ Erreur API IA Principale: {error}")
                return ""

            return response.strip() if response else ""

        except Exception as e:
            print(f"[INTROSPECTION-ORCHESTRATOR] ❌ Erreur appel IA Principale: {e}")
            return ""

    async def _call_archiviste(self, prompt: str, max_tokens: int) -> str:
        """Appel API Archiviste"""
        try:
            # Appel AIController Archiviste via call_chat_api
            messages = [{"role": "user", "content": prompt}]
            response, error = await self.archiviste_controller.call_chat_api(
                messages=messages,
                max_tokens=max_tokens,
                context_length=8192,
                temperature=0.7,
                is_json=False
            )

            if error:
                print(f"[INTROSPECTION-ORCHESTRATOR] ❌ Erreur API Archiviste: {error}")
                return ""

            return response.strip() if response else ""

        except Exception as e:
            print(f"[INTROSPECTION-ORCHESTRATOR] ❌ Erreur appel Archiviste: {e}")
            return ""

    def _detect_synthesis_ready(self, main_ai_message: str) -> bool:
        """Détecte si IA Principale est prête pour la synthèse"""
        synthesis_phrase = self.config.get("synthesis_ready_phrase", "je suis prête à formuler ma synthèse")
        return synthesis_phrase.lower() in main_ai_message.lower()
    
    def _detect_memorization_phrase(self, message: str) -> str:
        """Détecte phrase de mémorisation et extrait le contenu"""
        memorization_phrase = self.config.get("memorization_phrase", "il faut que je me souvienne de ça:")
        pattern = re.compile(rf"{re.escape(memorization_phrase)}\s*(.+?(?:\.|$))", re.IGNORECASE | re.DOTALL)
        
        match = pattern.search(message)
        if match:
            return match.group(1).strip()
        return ""

    def _extract_save_metadata(self, text: str) -> Dict[str, Any]:
        """Extrait métadonnées JSON de sauvegarde depuis réponse IA Principale"""
        try:
            # Recherche pattern JSON
            match = re.search(r'\{.*?"save_decision".*?\}', text, re.DOTALL)

            if match:
                json_str = match.group(0)
                metadata = json.loads(json_str)

                return {
                    "save_decision": metadata.get("save_decision", "no"),
                    "importance": int(metadata.get("importance", 5)),
                    "reason": metadata.get("reason", "")
                }

        except Exception as e:
            print(f"[INTROSPECTION-ORCHESTRATOR] ⚠️ Erreur extraction métadonnées: {e}")

        # Fallback
        return {
            "save_decision": "no",
            "importance": 5,
            "reason": "Métadonnées non trouvées"
        }

    async def _get_memory_context(self) -> str:
        """Récupère contexte mémoire pertinent"""
        try:
            # Utiliser retrieve_synthesis_and_memories de MemoryManager OGMA
            synthesis, memories = await self.memory_manager.retrieve_synthesis_and_memories(
                query_text="introspection contexte conversation",
                k=5,
                top_memories=5
            )

            if memories:
                context = "\n".join([f"- {m.get('text_original', m.get('content', 'N/A'))}" for m in memories[:5]])
                return f"Souvenirs pertinents:\n{context}"

            return "Aucun souvenir pertinent trouvé."

        except Exception as e:
            print(f"[INTROSPECTION-ORCHESTRATOR] ⚠️ Erreur contexte mémoire: {e}")
            return ""

    def _format_conversation_context(self, context: Dict[str, Any]) -> str:
        """Formate contexte conversationnel pour prompts"""
        try:
            # Extraire informations contextuelles enrichies
            user_identity = context.get("user_identity", "Utilisateur")
            main_ai_identity = context.get("main_ai_identity", "IA Principale")
            relationship = context.get("relationship_context", "")
            
            formatted = [f"IDENTITÉS: {main_ai_identity} dialogue avec {user_identity}"]
            if relationship:
                formatted.append(f"RELATION: {relationship}")
            
            # Extraire historique de messages (plus long, moins tronqué)
            messages = context.get("chat_history", [])[-8:]  # 8 derniers messages
            
            if messages:
                formatted.append("\nHISTORIQUE RÉCENT:")
                for msg in messages:
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                    # Moins de troncature (500 chars au lieu de 200)
                    content_display = content[:500] + "..." if len(content) > 500 else content
                    formatted.append(f"{role.upper()}: {content_display}")

            return "\n".join(formatted) if formatted else "Pas de contexte conversationnel"

        except Exception as e:
            print(f"[INTROSPECTION-ORCHESTRATOR] ⚠️ Erreur format contexte: {e}")
            return ""

    async def _get_memory_context_for_question(self, question: str) -> str:
        """Recherche souvenirs spécifiques à la demande de l'IA Principale"""
        try:
            if not self.memory_manager:
                return "Aucun souvenir disponible"
                
            # Recherche ciblée basée sur la question de l'IA Principale  
            synthesis, memories = await self.memory_manager.retrieve_synthesis_and_memories(
                question,  # Premier paramètre positionnel
                k=5,  # Limité à 5 souvenirs pertinents
                top_memories=3  # Les 3 meilleurs souvenirs détaillés
            )
            
            if not memories and not synthesis:
                return "Aucun souvenir pertinent trouvé"
            
            formatted = []
            
            # Ajouter la synthèse si disponible
            if synthesis:
                formatted.append(f"📝 **Synthèse Archiviste:**\n{synthesis}\n")
            
            # Ajouter les souvenirs détaillés
            if memories:
                formatted.append("🧠 **Souvenirs pertinents:**")
                for i, memory in enumerate(memories, 1):
                    title = memory.get("titre", f"Souvenir #{i}")
                    content = memory.get("texte_original", memory.get("résumé", ""))[:400]
                    formatted.append(f"{i}. **{title}**: {content}")
                
            return "\n".join(formatted)
            
        except Exception as e:
            print(f"[INTROSPECTION-ORCHESTRATOR] ⚠️ Erreur recherche mémoire: {e}")
            return "Erreur accès mémoire"

    def _extract_final_response_from_synthesis(self, synthesis_text: str) -> str:
        """
        Extrait la réponse finale destinée à l'utilisateur depuis la synthèse
        Cherche la section "Réponse construite" avec extraction simple
        """
        try:
            # Rechercher section "Réponse construite" - patterns simples
            patterns = [
                r"• \*\*Réponse construite\*\* ?: (.+?)(?:\n• |\n\n|$)",
                r"\*\*Réponse construite\*\* ?: (.+?)(?:\n\*\*|\n\n|$)",
                r"Réponse construite ?: (.+?)(?:\n|$)"
            ]
            
            for pattern in patterns:
                match = re.search(pattern, synthesis_text, re.IGNORECASE | re.DOTALL)
                if match:
                    response = match.group(1).strip()
                    # Nettoyage minimal
                    response = re.sub(r'^\W+', '', response)  # Retirer caractères spéciaux au début
                    if response and len(response) > 20:  # Vérifier que c'est une vraie réponse
                        print(f"[INTROSPECTION-ORCHESTRATOR] 📤 Réponse extraite: {response[:50]}...")
                        return response
            
            # Fallback simple: utiliser toute la synthèse comme réponse
            print("[INTROSPECTION-ORCHESTRATOR] ⚠️ Section 'Réponse construite' non trouvée, utilise synthèse complète")
            return synthesis_text
            
        except Exception as e:
            print(f"[INTROSPECTION-ORCHESTRATOR] ❌ Erreur extraction réponse finale: {e}")
            return synthesis_text

    def _format_dialogue_history(self) -> str:
        """Formate historique dialogue pour prompts"""
        if not self.dialogue_messages:
            return "Début de la réflexion..."

        formatted = []
        for msg in self.dialogue_messages:
            role = "💭 IA PRINCIPALE" if msg["role"] == "main_ai" else "📚 ARCHIVISTE"
            content = msg["content"]
            formatted.append(f"{role}:\n{content}\n")

        return "\n".join(formatted)

    def stop_current_session(self):
        """Arrête session en cours"""
        print("[INTROSPECTION-ORCHESTRATOR] 🛑 Arrêt session demandé")
        self.should_stop = True
    
    def reload_config(self):
        """Recharge la configuration depuis le fichier (synchronisation interface)"""
        try:
            print("[INTROSPECTION-ORCHESTRATOR] 🔄 Rechargement config demandé")
            
            # Recharger depuis fichier
            self.config.load_config()
            
            # Déclencher callbacks
            for callback in self.on_config_reload_callbacks:
                try:
                    callback()
                except Exception as e:
                    print(f"[INTROSPECTION-ORCHESTRATOR] ⚠️ Erreur callback reload: {e}")
            
            print("[INTROSPECTION-ORCHESTRATOR] ✅ Config rechargée et callbacks notifiés")
            
        except Exception as e:
            print(f"[INTROSPECTION-ORCHESTRATOR] ❌ Erreur rechargement config: {e}")
    
    def add_config_reload_callback(self, callback):
        """Ajoute callback appelé lors rechargement config"""
        self.on_config_reload_callbacks.append(callback)

    async def _get_direct_memory_access(self, user_message: str, context: Dict[str, Any]) -> str:
        """
        Accès direct non censuré à la mémoire FAISS/SQLite
        IMPORTANT: Cette méthode donne un accès COMPLET sans censure
        """
        try:
            print("[INTROSPECTION-ORCHESTRATOR] 🔓 Accès direct mémoire SANS censure...")

            # Accès direct au memory_manager pour recherche non censurée
            if not hasattr(self, 'memory_manager') or not self.memory_manager:
                return "Gestionnaire mémoire non disponible"

            # Recherche dans FAISS avec le message utilisateur
            query = f"{user_message} {context.get('recent_context', '')}"
            
            # Accès DIRECT aux souvenirs (pas via l'Archiviste qui censure)
            # Utilisation de search_memories (async) pour accès non censuré
            memories = await self.memory_manager.search_memories(
                query=query,
                limit=10,  # Plus de souvenirs que d'habitude
                threshold=0.3  # Seuil plus bas pour capturer plus de résultats
            )

            if not memories:
                return "Aucun souvenir trouvé dans la recherche directe."

            # Formatage des résultats SANS censure
            formatted_memories = []
            for i, memory in enumerate(memories[:8]):  # Top 8 résultats
                memory_content = memory.get('content', 'Contenu non disponible')
                memory_id = memory.get('id', f'mem_{i}')
                similarity = memory.get('similarity', 0.0)
                
                # IMPORTANT: Aucune censure ici, tout est transmis
                formatted_memories.append(f"""
SOUVENIR #{i+1} (ID: {memory_id}, Similarité: {similarity:.3f}):
{memory_content}
""")

            result = f"""ACCÈS MÉMOIRE DIRECT - {len(memories)} souvenirs trouvés:

{''.join(formatted_memories)}

ANALYSE: Ces souvenirs sont extraits directement de ta mémoire FAISS/SQLite sans aucune censure. 
Utilise ces informations pour préparer tes questions à l'Archiviste."""

            print(f"[INTROSPECTION-ORCHESTRATOR] 🧠 Accès direct: {len(memories)} souvenirs, {len(result)} chars")
            
            return result

        except Exception as e:
            print(f"[INTROSPECTION-ORCHESTRATOR] ❌ Erreur accès direct mémoire: {e}")
            return f"Erreur accès direct mémoire: {str(e)}"

    def cleanup(self):
        """Nettoyage orchestrateur"""
        if self.is_active:
            self.stop_current_session()

        print("[INTROSPECTION-ORCHESTRATOR] ✅ Cleanup terminé")


# Exports
__all__ = ['IntrospectionOrchestrator']
