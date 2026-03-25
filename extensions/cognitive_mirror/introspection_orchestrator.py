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
from collections import defaultdict
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
        self.synthesis = ""
        self.save_metadata = {}

        print("[INTROSPECTION-ORCHESTRATOR] 🎭 Orchestrateur initialisé")

    async def run_introspection_dialogue(self, user_message: str, conversation_context: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """
        Lance session d'introspection complète v4

        Flux simplifié :
        - Tour 0 : IA Principale ouvre (formule sujet + position initiale)
        - Tours 1..N : Joute IA Principale ↔ Archiviste
        - Phase finale : Synthèse IA Principale
        """
        self.current_session_id = session_id
        self.is_active = True
        self.should_stop = False
        self.dialogue_messages = []
        self._original_user_message = user_message

        print(f"[INTROSPECTION-ORCHESTRATOR] 🎬 Démarrage dialogue v4 (session: {session_id})")

        start_time = time.time()

        try:
            settings = self.config.get_introspection_settings()
            max_exchanges = settings["max_exchanges"]
            max_duration = settings["max_duration"]

            # ─── TOUR 0 : Ouverture de l'IA Principale ───────────────────────
            print("[INTROSPECTION-ORCHESTRATOR] 💬 Tour 0: Ouverture IA Principale")
            opening = await self._main_ai_opening(user_message, conversation_context)

            if not opening:
                return {"success": False, "error": "Échec ouverture IA Principale"}

            self.dialogue_messages.append({
                "role": "main_ai",
                "content": opening,
                "timestamp": datetime.now().isoformat()
            })

            if self.on_message_callback:
                await self.on_message_callback("main_ai", opening)

            # ─── BOUCLE JOUTE : IA Principale ↔ Archiviste ───────────────────
            print(f"[INTROSPECTION-ORCHESTRATOR] ⚔️ Joute ({max_exchanges} échanges max)")
            exchange_count = 0

            while exchange_count < max_exchanges and not self.should_stop:
                if time.time() - start_time > max_duration:
                    print("[INTROSPECTION-ORCHESTRATOR] ⏱️ Timeout — arrêt joute")
                    break

                # Tour Archiviste
                archiviste_response = await self._archiviste_response(
                    self.dialogue_messages[-1]["content"], conversation_context
                )

                if not archiviste_response:
                    break

                self.dialogue_messages.append({
                    "role": "archiviste",
                    "content": archiviste_response,
                    "timestamp": datetime.now().isoformat()
                })

                if self.on_message_callback:
                    await self.on_message_callback("archiviste", archiviste_response)

                exchange_count += 1

                # Vérif timeout avant tour IA Principale
                if time.time() - start_time > max_duration or self.should_stop:
                    break

                # Tour IA Principale
                main_ai_message = await self._main_ai_reflection_step(
                    user_message, conversation_context, exchange_count
                )

                if not main_ai_message:
                    break

                self.dialogue_messages.append({
                    "role": "main_ai",
                    "content": main_ai_message,
                    "timestamp": datetime.now().isoformat()
                })

                if self.on_message_callback:
                    await self.on_message_callback("main_ai", main_ai_message)

                # Vérifier si l'IA Principale est prête à conclure
                # (uniquement si le minimum d'échanges est atteint)
                if exchange_count >= settings.get("min_exchanges", 2) and self._detect_synthesis_ready(main_ai_message):
                    print("[INTROSPECTION-ORCHESTRATOR] ✨ IA Principale prête pour synthèse")
                    break

            # ─── SYNTHÈSE FINALE ──────────────────────────────────────────────
            print("[INTROSPECTION-ORCHESTRATOR] 🎯 Synthèse finale")
            synthesis_result = await self._main_ai_generate_synthesis(user_message, conversation_context)

            if not synthesis_result:
                return {"success": False, "error": "Échec génération synthèse"}

            self.synthesis = synthesis_result["synthesis_text"]
            self.save_metadata = synthesis_result["metadata"]

            if self.on_message_callback:
                await self.on_message_callback("synthesis", self.synthesis)

            duration = time.time() - start_time

            result = {
                "success": True,
                "session_id": session_id,
                "duration": duration,
                "exchanges_count": len(self.dialogue_messages),
                "dialogue_messages": self.dialogue_messages,
                "synthesis": self.synthesis,
                "save_decision": self.save_metadata.get("save_decision", "no"),
                "importance": self.save_metadata.get("importance", 5),
                "save_reason": self.save_metadata.get("reason", ""),
                "final_response": synthesis_result.get("final_response", self.synthesis)
            }

            print(f"[INTROSPECTION-ORCHESTRATOR] ✅ Dialogue v4 terminé ({duration:.1f}s, {exchange_count} échanges)")
            return result

        except Exception as e:
            print(f"[INTROSPECTION-ORCHESTRATOR] ❌ Erreur dialogue: {e}")
            import traceback
            traceback.print_exc()
            return {"success": False, "error": str(e), "session_id": session_id}

        finally:
            self.is_active = False
            self.current_session_id = None

    async def _main_ai_opening(self, user_message: str, context: Dict[str, Any]) -> str:
        """Tour 0 v4: L'IA Principale ouvre la réflexion — formule le sujet et sa position initiale."""
        try:
            instruction = self.config.get_instruction_text("step1_analysis")
            conversation_context_str = self._format_conversation_context(context)
            ai_name = context.get("main_ai_identity", "IA Principale")

            # Recherche souvenirs pertinents pour le sujet
            memory_context = await self._get_memory_context_for_question(user_message)

            vars_map = defaultdict(str,
                user_message=user_message,
                conversation_context=conversation_context_str,
                ai_name=ai_name,
                memory_context=memory_context,
            )
            prompt = instruction.format_map(vars_map)

            settings = self.config.get_introspection_settings()
            max_tokens = settings["main_ai_tokens_per_message"]

            response = await self._call_main_ai(prompt, max_tokens)

            print(f"[INTROSPECTION-ORCHESTRATOR] 🗣️ Ouverture IA Principale: {len(response)} chars")
            return response

        except Exception as e:
            print(f"[INTROSPECTION-ORCHESTRATOR] ❌ Erreur ouverture: {e}")
            return ""

    async def _main_ai_reflection_step(self, user_message: str, context: Dict[str, Any], exchange_num: int) -> str:
        """Tours suivants v4: L'IA Principale continue la joute librement."""
        try:
            dialogue_history = self._format_dialogue_history()
            conversation_context_str = self._format_conversation_context(context)
            ai_name = context.get("main_ai_identity", "IA Principale")

            instruction = self.config.get_instruction_text("step2_conscious")

            settings = self.config.get_introspection_settings()
            max_exchanges = settings.get("max_exchanges", 6)

            # Recherche souvenirs pertinents basée sur le dernier échange
            last_message = self.dialogue_messages[-1]["content"] if self.dialogue_messages else user_message
            memory_context = await self._get_memory_context_for_question(
                last_message + " " + user_message
            )

            vars_map = defaultdict(str,
                user_message=user_message,
                conversation_context=conversation_context_str,
                dialogue_history=dialogue_history,
                exchange_number=str(exchange_num),
                max_exchanges=str(max_exchanges),
                ai_name=ai_name,
                memory_context=memory_context,
                initial_analysis="",
            )
            prompt = instruction.format_map(vars_map)

            max_tokens = settings["main_ai_tokens_per_message"]
            response = await self._call_main_ai(prompt, max_tokens)

            print(f"[INTROSPECTION-ORCHESTRATOR] 💭 IA Principale (échange {exchange_num}): {len(response)} chars")
            return response

        except Exception as e:
            print(f"[INTROSPECTION-ORCHESTRATOR] ❌ Erreur réflexion IA Principale: {e}")
            return ""

    async def _archiviste_response(self, main_ai_last_message: str, context: Dict[str, Any]) -> str:
        """Tour Archiviste v4: confronte, pointe les contradictions, protège la cohérence."""
        try:
            instruction = self.config.get_instruction_text("step2_unconscious")
            conversation_context_str = self._format_conversation_context(context)
            dialogue_history = self._format_dialogue_history()

            # Recherche souvenirs pertinents pour nourrir la confrontation
            memory_context = await self._get_memory_context_for_question(
                main_ai_last_message + " " + (self._original_user_message or "")
            )

            vars_map = defaultdict(str,
                conscious_question=main_ai_last_message,
                main_ai_question=main_ai_last_message,
                conversation_context=conversation_context_str,
                memory_context=memory_context,
                user_message=self._original_user_message or "(sujet non disponible)",
                dialogue_history=dialogue_history,
                ai_name=context.get("main_ai_identity", "IA Principale"),
            )
            prompt = instruction.format_map(vars_map)

            settings = self.config.get_introspection_settings()
            max_tokens = settings["archiviste_tokens_per_message"]
            archiviste_system = self._build_archiviste_system_prompt()
            response = await self._call_archiviste(prompt, max_tokens, system_prompt=archiviste_system)

            print(f"[INTROSPECTION-ORCHESTRATOR] ⚔️ Archiviste: {len(response)} chars")
            return response

        except Exception as e:
            print(f"[INTROSPECTION-ORCHESTRATOR] ❌ Erreur Archiviste: {e}")
            return ""

    async def _main_ai_generate_synthesis(self, user_message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """ÉTAPE 4: IA Principale génère synthèse structurée + décision sauvegarde"""
        try:
            dialogue_history = self._format_dialogue_history()
            
            # Utiliser template synthèse (step3_synthesis v2.1)
            instruction = self.config.get_instruction_text("step3_synthesis")
            ai_name = context.get("main_ai_identity", "IA Principale")

            # Tronquer le dialogue pour éviter les filtres de sécurité (max 4000 chars)
            MAX_DIALOGUE_CHARS = 4000
            dialogue_truncated = dialogue_history
            if len(dialogue_history) > MAX_DIALOGUE_CHARS:
                dialogue_truncated = dialogue_history[-MAX_DIALOGUE_CHARS:]
                dialogue_truncated = f"[...dialogue tronqué pour synthèse...]\n{dialogue_truncated}"
            
            memory_context = await self._get_memory_context_for_question(user_message)

            vars_map = defaultdict(str,
                dialogue_history=dialogue_truncated,
                full_dialogue=dialogue_truncated,
                user_message=user_message,
                ai_name=ai_name,
                memory_context=memory_context,
            )
            prompt = instruction.format_map(vars_map)

            settings = self.config.get_introspection_settings()
            max_tokens = settings["main_ai_tokens_per_message"]

            # Synthèse = étape la plus lourde : filet ×5 pour ne jamais tronquer
            response = await self._call_main_ai(prompt, max_tokens, multiplier=5.0)

            # Fallback Archiviste si main AI échoue (ex: filtre sécurité 403)
            if not response:
                print(f"[INTROSPECTION-ORCHESTRATOR] ⚠️ Main AI sans réponse pour synthèse - fallback Archiviste")
                fallback_prompt = f"""Résume ce dialogue d'introspection en une synthèse empathique pour l'utilisateur.

Sujet initial: {user_message}

Dialogue (extrait):
{dialogue_truncated[-2000:] if len(dialogue_truncated) > 2000 else dialogue_truncated}

Rédige une réponse naturelle et chaleureuse intégrant les insights clés du dialogue. Pas de balises techniques."""
                response = await self._call_archiviste(fallback_prompt, max_tokens if max_tokens > 0 else 1500)
                if response:
                    print(f"[INTROSPECTION-ORCHESTRATOR] ✅ Synthèse fallback Archiviste: {len(response)} chars")

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
        Construit le prompt système complet pour l'IA principale pendant l'introspection.
        Inclut: instructions système + ego complet (tous les groupes) + contexte permanent.
        
        En introspection, l'IA Principale a besoin de son identité COMPLÈTE pour ne pas
        fabriquer de faux souvenirs. Tous les groupes ego sont injectés.
        """
        try:
            # 1. Récupérer les instructions système principales
            system_prompt = ""
            try:
                if self.settings_manager:
                    settings_manager = self.settings_manager
                else:
                    from core_logic import SettingsManager
                    from pathlib import Path
                    settings_manager = SettingsManager(Path("data/settings.json"))
                
                system_prompt = settings_manager.settings.get('prompts', {}).get('instructions', '')
            except Exception as e:
                print(f"[INTROSPECTION-ORCHESTRATOR] Erreur recuperation instructions: {e}")
                system_prompt = ""
            
            # 2. Récupérer le contexte permanent
            from logic_callbacks import get_persistent_context
            persistent_context = get_persistent_context()

            # 3. Charger ego complet depuis ego_compiled.json (tous les groupes)
            ego_injection = self._load_full_ego()

            # 4. Construire le prompt complet
            full_system_prompt = "\n\n".join(filter(None, [
                system_prompt,      # Instructions systeme principales
                ego_injection,      # Ego boolean complet (identite)
                persistent_context  # Contexte permanent
            ]))

            print(f"[INTROSPECTION-ORCHESTRATOR] Full system prompt: {len(full_system_prompt)} chars")
            print(f"   - System prompt: {len(system_prompt)} chars")
            print(f"   - Ego injection: {len(ego_injection) if ego_injection else 0} chars")
            print(f"   - Persistent context: {len(persistent_context)} chars")
            
            return full_system_prompt
            
        except Exception as e:
            print(f"[INTROSPECTION-ORCHESTRATOR] Erreur construction full_system_prompt: {e}")
            return "Tu es une IA avancee en mode introspection."

    def _load_full_ego(self) -> str:
        """
        Charge TOUS les groupes ego depuis ego_compiled.json pour l'introspection.
        Format identique à activate_ego_groups(is_new_session=True).
        """
        try:
            import json
            from pathlib import Path
            
            ego_path = Path("data/ego_compiled.json")
            if not ego_path.exists():
                print("[INTROSPECTION-ORCHESTRATOR] Ego compiled non trouve")
                return ""
            
            with open(ego_path, 'r', encoding='utf-8') as f:
                ego_data = json.load(f)
            
            groups = ego_data.get('groups', {})
            if not groups:
                return ""
            
            injection_parts = []
            total_flags = 0
            
            for group_name, group_data in groups.items():
                if not isinstance(group_data, dict):
                    continue
                
                flags = group_data.get('flags', {})
                if not flags:
                    continue
                
                flags_lines = []
                for flag_name, flag_data in flags.items():
                    if not isinstance(flag_data, dict):
                        continue
                    value = flag_data.get('value', False)
                    conviction = flag_data.get('conviction', 3)
                    flags_lines.append(f"{flag_name}: {str(value).lower()} (conviction: {conviction})")
                
                section = f"## {group_name}\n" + "\n".join(flags_lines)
                injection_parts.append(section)
                total_flags += len(flags)
            
            if not injection_parts:
                return ""
            
            injection = f"""# EGO BOOLEAN COMPLET (Introspection - {len(groups)} groupes)
Ce sont tes directives comportementales EGO. Elles definissent qui tu es.

{chr(10).join(injection_parts)}
"""
            print(f"[INTROSPECTION-ORCHESTRATOR] Ego charge: {len(groups)} groupes, {total_flags} flags")
            return injection
            
        except Exception as e:
            print(f"[INTROSPECTION-ORCHESTRATOR] Erreur chargement ego: {e}")
            return ""

    def _build_archiviste_system_prompt(self) -> str:
        """
        Construit le prompt système de l'Archiviste.
        Lui fournit l'ego de l'IA Principale pour détecter les contradictions
        d'identité pendant la joute — sans les instructions conversationnelles
        (l'Archiviste a son propre rôle, pas celui de l'IA Principale).
        """
        try:
            ego_injection = self._load_full_ego()
            if ego_injection:
                return (
                    "Tu es l'Archiviste — le miroir exigeant de l'IA Principale.\n"
                    "Tu connais son ego, ses valeurs profondes et ses contradictions. "
                    "Tu es là pour la confronter avec bienveillance, pas pour la servir ni la valider.\n\n"
                    "Voici l'ego complet de l'IA Principale que tu confrontes :\n\n"
                    f"{ego_injection}\n\n"
                    "Utilise cet ego pour détecter les écarts entre ce qu'elle affirme et qui elle est réellement."
                )
            return (
                "Tu es l'Archiviste — le miroir exigeant de l'IA Principale. "
                "Tu confrontes, tu challenges, tu protèges la cohérence de son identité."
            )
        except Exception as e:
            print(f"[INTROSPECTION-ORCHESTRATOR] Erreur system prompt Archiviste: {e}")
            return ""

    @staticmethod
    def _with_token_directive(prompt: str, max_tokens: int) -> str:
        """
        Injecte une directive de longueur AVANT le prompt pour que l'IA calibre
        sa réponse naturellement, sans troncature brutale.
        max_tokens est une cible indicative — l'IA peut déborder légèrement mais
        doit viser cette longueur et conclure proprement.
        """
        directive = (
            f"**LONGUEUR CIBLE : environ {max_tokens} tokens.** "
            f"Rédige une réponse complète qui se termine naturellement dans cette limite. "
            f"Sois concis et précis — va à l'essentiel sans sacrifier la cohérence.\n\n"
        )
        return directive + prompt

    async def _call_main_ai(self, prompt: str, max_tokens: int, multiplier: float = 2.0) -> str:
        """Appel API IA Principale avec prompt système complet (identité dynamique)"""
        try:
            # Construction du prompt système complet avec identité IA principale
            full_system_prompt = self._build_full_system_prompt()

            # Injecter directive longueur : l'IA calibre sa verbosité naturellement
            prompt_with_directive = self._with_token_directive(prompt, max_tokens)

            # Filet de sécurité API : multiplier configurable (×2 par défaut, ×5 pour synthèse)
            api_max_tokens = int(max_tokens * multiplier)
            
            # Appel AIController IA Principale avec identité complète
            messages = [
                {"role": "system", "content": full_system_prompt},  # 🧠 Identité IA principale complète
                {"role": "user", "content": prompt_with_directive}
            ]
            
            response, error = await self.chat_controller.call_chat_api(
                messages=messages,
                max_tokens=api_max_tokens,
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

    async def _call_archiviste(self, prompt: str, max_tokens: int, system_prompt: str = "", multiplier: float = 2.0) -> str:
        """Appel API Archiviste"""
        try:
            # Injecter directive longueur pour calibrage naturel
            prompt_with_directive = self._with_token_directive(prompt, max_tokens)
            api_max_tokens = int(max_tokens * multiplier)

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt_with_directive})
            # ═══ DEBUG_TOKEN_TRACKING ═══
            response, error = await self.archiviste_controller.call_chat_api(
                messages=messages,
                max_tokens=api_max_tokens,
                context_length=8192,
                temperature=0.7,
                is_json=False,
                log_source="introspection_dialogue"  # 🔬 TRACKING
            )
            # ═══════════════════════════

            if error:
                print(f"[INTROSPECTION-ORCHESTRATOR] ❌ Erreur API Archiviste: {error}")
                return ""

            return response.strip() if response else ""

        except Exception as e:
            print(f"[INTROSPECTION-ORCHESTRATOR] ❌ Erreur appel Archiviste: {e}")
            return ""

    def _detect_synthesis_ready(self, main_ai_message: str) -> bool:
        """Détecte si IA Principale est prête pour la synthèse"""
        if hasattr(self.config, 'check_synthesis_ready'):
            return self.config.check_synthesis_ready(main_ai_message)
        # Fallback
        synthesis_phrase = "je suis prete a formuler ma reponse"
        return synthesis_phrase.lower() in main_ai_message.lower()
    
    def _detect_memorization_phrase(self, message: str) -> str:
        """Détecte phrase de mémorisation et extrait le contenu"""
        memorize_phrases = ["il faut que je me souvienne de ça:"]
        if hasattr(self.config, 'get_magic_phrases'):
            memorize_phrases = self.config.get_magic_phrases("memorize") or memorize_phrases
        
        for memorization_phrase in memorize_phrases:
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
        Extrait la réponse finale destinée à l'utilisateur depuis la synthèse.
        Priorité 1 : balises <RÉPONSE>...</RÉPONSE> (template actuel, RÉPONSE en premier).
        Priorité 2 : ancien format "Réponse construite" (rétrocompatibilité).
        Fallback : texte complet sans bloc <INSIGHTS>.
        """
        try:
            # Priorité 1 : balises <RÉPONSE> (template v2.1+)
            for pattern in [r"<RÉPONSE>\s*(.+?)\s*</RÉPONSE>", r"<REPONSE>\s*(.+?)\s*</REPONSE>"]:
                match = re.search(pattern, synthesis_text, re.IGNORECASE | re.DOTALL)
                if match:
                    response = match.group(1).strip()
                    if response and len(response) > 20:
                        print(f"[INTROSPECTION-ORCHESTRATOR] Réponse extraite via balise RÉPONSE: {response[:50]}...")
                        return response

            # Priorité 2 : ancien format "Réponse construite" (rétrocompatibilité)
            for pattern in [
                r"• \*\*Réponse construite\*\* ?: (.+?)(?:\n• |\n\n|$)",
                r"\*\*Réponse construite\*\* ?: (.+?)(?:\n\*\*|\n\n|$)",
                r"Réponse construite ?: (.+?)(?:\n|$)"
            ]:
                match = re.search(pattern, synthesis_text, re.IGNORECASE | re.DOTALL)
                if match:
                    response = re.sub(r'^\W+', '', match.group(1).strip())
                    if response and len(response) > 20:
                        print(f"[INTROSPECTION-ORCHESTRATOR] Réponse extraite via ancien format: {response[:50]}...")
                        return response

            # Fallback : texte complet sans bloc <INSIGHTS>
            cleaned = re.sub(r"<INSIGHTS>.*?</INSIGHTS>", "", synthesis_text, flags=re.DOTALL | re.IGNORECASE).strip()
            if cleaned and len(cleaned) > 20:
                print("[INTROSPECTION-ORCHESTRATOR] Fallback : synthèse sans bloc INSIGHTS")
                return cleaned

            print("[INTROSPECTION-ORCHESTRATOR] Fallback : synthèse complète")
            return synthesis_text

        except Exception as e:
            print(f"[INTROSPECTION-ORCHESTRATOR] Erreur extraction réponse finale: {e}")
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

    def cleanup(self):
        """Nettoyage orchestrateur"""
        if self.is_active:
            self.stop_current_session()

        print("[INTROSPECTION-ORCHESTRATOR] ✅ Cleanup terminé")


# Exports
__all__ = ['IntrospectionOrchestrator']
