# 🧠 Introspection - Moteur Principal v2.0

"""
Extension Introspection v2.0 - Architecture Simplifiée Sans États

NOUVEAU PARADIGME:
- Pas de machine à états complexe
- Déclenchement à la demande (phrases magiques ou mode always)
- Dialogue visible IA Principale <-> Archiviste dans boîte thinking
- Sauvegarde conditionnelle décidée par l'IA
- Aucune détection automatique d'inactivité

FLUX:
1. Détection phrase magique OU mode always
2. Affichage boîte introspection
3. Dialogue streaming IA principale ↔ Archiviste
4. Synthèse finale
5. Sauvegarde si IA décide
6. Retour réponse utilisateur
"""

import asyncio
import time
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime
import uuid
import json
import re

from .config_v2 import get_introspection_config as get_config, IntrospectionConfigV2 as CognitiveMirrorConfig


class IntrospectionCore:
    """
    Moteur principal Introspection v2.0

    Simplifié - Sans états - À la demande
    Compatible avec API OGMA existante
    """

    def __init__(self, chat_controller, archiviste_controller, memory_manager, ui_container=None, settings_manager=None):
        """
        Initialise le moteur Introspection

        Args:
            chat_controller: Instance AIController (IA principale/Entité numérique)
            archiviste_controller: Instance AIController (Archiviste/Subconscient)
            memory_manager: Instance MemoryManager OGMA
            ui_container: Container NiceGUI pour boîte introspection
            settings_manager: SettingsManager pour accès prompts système
        """
        print("[INTROSPECTION-CORE] 🎭 Initialisation du moteur...")
        print(f"[INTROSPECTION-CORE] Paramètres reçus:")
        print(f"  - chat_controller: {type(chat_controller) if chat_controller else None}")
        print(f"  - archiviste_controller: {type(archiviste_controller) if archiviste_controller else None}")
        print(f"  - memory_manager: {type(memory_manager) if memory_manager else None}")
        print(f"  - ui_container: {type(ui_container) if ui_container else None}")
        print(f"  - settings_manager: {type(settings_manager) if settings_manager else None}")
        
        self.config = get_config()

        # Dépendances OGMA
        self.chat_controller = chat_controller
        self.archiviste_controller = archiviste_controller
        self.memory_manager = memory_manager
        self.ui_container = ui_container
        self.settings_manager = settings_manager

        # Composants extension
        self.introspection_orchestrator = None  # Initialisé dans initialize()
        self.ui_components = None
        self.memory_integration = None

        # État simple
        # self.is_enabled = False  # Maintenant une propriété, pas d'init direct
        self.is_introspection_active = False
        self.current_session_id = None
        self.last_introspection_result = None  # Stocke le dernier résultat complet

        # Statistiques
        self.stats = {
            "total_introspections": 0,
            "total_saved": 0,
            "last_introspection_time": None,
            "average_duration": 0
        }

        # Callbacks OGMA
        self.on_introspection_start = None
        self.on_introspection_complete = None
        self.on_message_ready = None  # Callback pour affichage messages
        self.on_synthesis_ready = None
        self.on_external_settings_change = None  # Callback changement paramètres UI vers OGMA

        print(f"[INTROSPECTION-CORE] 🆕 Moteur v2.0 initialisé")

    def reload_config_from_file(self):
        """Recharge config depuis fichier (synchronisation interface paramètres)"""
        try:
            print("[INTROSPECTION-CORE] 🔄 Rechargement config depuis interface...")
            
            # Recharger orchestrateur
            if self.introspection_orchestrator:
                self.introspection_orchestrator.reload_config()
            
            # Recharger config locale si nécessaire
            if hasattr(self, '_config') and self._config:
                self._config = None  # Force reload via property
                _ = self.is_enabled  # Déclenche reload via property
            
            print("[INTROSPECTION-CORE] ✅ Config rechargée depuis interface")
            
        except Exception as e:
            print(f"[INTROSPECTION-CORE] ❌ Erreur rechargement config: {e}")

    def initialize(self):
        """Initialise tous les composants de l'extension"""
        try:
            print("[INTROSPECTION-CORE] 🔧 Initialisation composants...")

            # Import des composants (import tardif pour éviter dépendances circulaires)
            from .introspection_orchestrator import IntrospectionOrchestrator
            from .ui_components import CognitiveMirrorUI
            from .memory_integration import MemoryIntegration

            # Orchestrateur dialogue IA principale ↔ Archiviste
            print(f"[INTROSPECTION-CORE] 🎬 Création orchestrateur avec memory_manager: {type(self.memory_manager)}")
            self.introspection_orchestrator = IntrospectionOrchestrator(
                config=self.config,
                chat_controller=self.chat_controller,
                archiviste_controller=self.archiviste_controller,
                memory_manager=self.memory_manager,
                settings_manager=self.settings_manager,
                on_message_callback=self._on_dialogue_message
            )
            print("[INTROSPECTION-CORE] ✅ Orchestrateur initialisé")

            # Interface utilisateur (popup paramètres + boîte introspection)
            self.ui_components = CognitiveMirrorUI(
                config=self.config,
                ui_container=self.ui_container,
                on_toggle_extension=self._on_toggle_callback,
                on_settings_change=self._on_settings_change_callback,
                core_reference=self
            )
            print("[INTROSPECTION-CORE] ✅ UI initialisée")

            # Intégration mémoire
            self.memory_integration = MemoryIntegration(
                memory_manager=self.memory_manager,
                config=self.config
            )
            print("[INTROSPECTION-CORE] ✅ Mémoire initialisée")

            # État initial depuis config - sera lu dynamiquement via propriété
            # self.is_enabled = self.config.is_enabled()  # Supprimé - maintenant une propriété

            print(f"[INTROSPECTION-CORE] ✅ Extension initialisée (état: {'ON' if self.is_enabled else 'OFF'})")
            return True

        except Exception as e:
            print(f"[INTROSPECTION-CORE] ❌ Erreur initialisation: {e}")
            import traceback
            traceback.print_exc()
            return False

    # ===== API PUBLIQUE =====

    async def process_user_message(self, user_message: str, conversation_context: Dict[str, Any]) -> Optional[str]:
        """
        Point d'entrée principal - Traite un message utilisateur

        Décide si introspection nécessaire selon:
        1. Mode always + extension ON
        2. Phrase magique détectée

        Args:
            user_message: Message de l'utilisateur
            conversation_context: Contexte conversationnel complet

        Returns:
            Réponse finale enrichie ou None (pas d'introspection)
        """
        if not self.is_enabled:
            return None

        # Vérifier si introspection nécessaire
        should_introspect = self._should_trigger_introspection(user_message)

        if not should_introspect:
            return None

        # Lancer introspection
        return await self.trigger_introspection(user_message, conversation_context, trigger_source="user_message")

    async def trigger_introspection(self, user_message: str, conversation_context: Dict[str, Any], trigger_source: str = "manual") -> Optional[str]:
        """
        Déclenche une session d'introspection complète

        Args:
            user_message: Message de l'utilisateur
            conversation_context: Contexte conversationnel
            trigger_source: Source déclenchement ("user_message", "magic_phrase", "manual")

        Returns:
            Réponse finale ou None si erreur
        """
        if self.is_introspection_active:
            print("[INTROSPECTION-CORE] ⚠️ Introspection déjà en cours - ignoré")
            return None

        self.is_introspection_active = True
        self.current_session_id = f"introspection_{int(time.time())}_{uuid.uuid4().hex[:8]}"
        start_time = time.time()

        print(f"[INTROSPECTION-CORE] 🧠 Démarrage introspection (ID: {self.current_session_id}, source: {trigger_source})")

        # Callback début
        if self.on_introspection_start:
            self.on_introspection_start(self.current_session_id, trigger_source)

        try:
            # Lancer orchestrateur dialogue
            result = await self.introspection_orchestrator.run_introspection_dialogue(
                user_message=user_message,
                conversation_context=conversation_context,
                session_id=self.current_session_id
            )

            # Traiter résultat
            if result and result.get("success"):
                duration = time.time() - start_time

                # Statistiques
                self.stats["total_introspections"] += 1
                self.stats["last_introspection_time"] = datetime.now().isoformat()
                self._update_average_duration(duration)

                # Stocker résultat complet pour accès ultérieur
                self.last_introspection_result = result

                # Sauvegarde conditionnelle
                if result.get("save_decision") == "yes":
                    await self._save_introspection_memory(result)

                # Callback fin
                if self.on_introspection_complete:
                    self.on_introspection_complete(self.current_session_id, result)

                print(f"[INTROSPECTION-CORE] ✅ Introspection terminée ({duration:.1f}s)")

                return result.get("final_response")

            else:
                print(f"[INTROSPECTION-CORE] ❌ Introspection échouée: {result.get('error')}")
                return None

        except Exception as e:
            print(f"[INTROSPECTION-CORE] ❌ Erreur introspection: {e}")
            import traceback
            traceback.print_exc()
            return None

        finally:
            self.is_introspection_active = False
            self.current_session_id = None

    def _phrase_matches_exactly(self, phrase: str, text: str) -> bool:
        """
        Vérifie si une phrase correspond exactement dans le texte
        
        Args:
            phrase: Phrase à chercher
            text: Texte où chercher
            
        Returns:
            True si correspondance exacte trouvée
        """
        import re
        
        # Créer un pattern qui cherche la phrase exacte avec boundaries
        # Échapper les caractères spéciaux regex
        escaped_phrase = re.escape(phrase.lower())
        
        # Créer le pattern avec word boundaries (\b) ou boundaries de phrase
        pattern = r'\b' + escaped_phrase + r'\b'
        
        return bool(re.search(pattern, text.lower(), re.IGNORECASE))

    def check_magic_phrases(self, text: str, source: str = "user") -> Optional[str]:
        """
        Vérifie présence phrases magiques dans un texte

        Args:
            text: Texte à vérifier
            source: "user" ou "ia"

        Returns:
            Type de phrase détectée ou None
        """
        if source == "user":
            # NOTE v4: ces clés ne sont PAS dans DEFAULT_SETTINGS — config.get() renvoie toujours [].
            # Le vrai déclenchement user passe par les regex hardcodées dans ogma_ng.py.
            # La détection IA (source="ia") passe par ogma_ui_conversations.py.
            # Cette méthode est conservée pour compatibilité mais n'est pas le chemin actif.
            stop_phrases = self.config.get_magic_phrases("user_stop")
            for phrase in stop_phrases:
                if self._phrase_matches_exactly(phrase, text):
                    return "stop"

            trigger_phrases = self.config.get_magic_phrases("user_trigger")
            for phrase in trigger_phrases:
                if self._phrase_matches_exactly(phrase, text):
                    return "trigger"

        elif source == "ia":
            ia_phrases = self.config.get_magic_phrases("ia_reflection")
            for phrase in ia_phrases:
                if self._phrase_matches_exactly(phrase, text):
                    return "trigger"

        return None

    def stop_current_introspection(self, reason: str = "user_stop"):
        """
        Arrête l'introspection en cours

        Args:
            reason: Raison de l'arrêt
        """
        if not self.is_introspection_active:
            print("[INTROSPECTION-CORE] ⚠️ Aucune introspection active à arrêter")
            return

        print(f"[INTROSPECTION-CORE] 🛑 Arrêt introspection demandé (raison: {reason})")

        # Arrêter orchestrateur
        if self.introspection_orchestrator:
            self.introspection_orchestrator.stop_current_session()

        self.is_introspection_active = False
        self.current_session_id = None

    def force_trigger_conversation(self) -> bool:
        """
        Déclenche manuellement une introspection (LEGACY - utiliser trigger_introspection_sync)

        Compatible avec API legacy force_trigger_conversation()

        Returns:
            bool: True si introspection démarrée
        """
        if not self.is_enabled:
            print("[INTROSPECTION-CORE] ⚠️ Extension désactivée - impossible de déclencher")
            return False

        if self.is_introspection_active:
            print("[INTROSPECTION-CORE] ⚠️ Introspection déjà en cours")
            return False

        print("[INTROSPECTION-CORE] 🔧 Déclenchement manuel demandé (mode legacy async)")

        # Créer contexte minimal pour déclenchement manuel
        asyncio.create_task(self.trigger_introspection(
            user_message="[Déclenchement manuel]",
            conversation_context={"source": "manual_trigger"},
            trigger_source="manual"
        ))

        return True

    async def run_introspection(self, user_message: str, context: Dict[str, Any], trigger_source: str = "manual") -> Dict[str, Any]:
        """
        API publique compatible avec chemin B dans ogma_ng.py (mode streaming).

        Adaptateur mince vers trigger_introspection_sync().
        Bridge aussi le callback on_message(step, role, content) vers on_message_ready(role, content).

        Returns:
            Dict avec {success, synthesis, dialogue: [{role, content}, ...]}
        """
        # Bridge on_message (step, role, content) → on_message_ready (role, content)
        if getattr(self, 'on_message', None):
            outer_cb = self.on_message
            step_counter = [0]

            async def _bridge(role: str, content: str):
                step_counter[0] += 1
                try:
                    res = outer_cb(step_counter[0], role, content)
                    if asyncio.iscoroutine(res):
                        await res
                except Exception as bridge_err:
                    print(f"[INTROSPECTION-CORE] ⚠️ Erreur callback on_message: {bridge_err}")

            self.on_message_ready = _bridge

        result = await self.trigger_introspection_sync(
            user_message=user_message,
            conversation_context=context
        )

        # Adapter format retour : dialogue_messages → dialogue (attendu par ogma_ng.py)
        if result.get('success'):
            result['dialogue'] = result.pop('dialogue_messages', [])

        return result

    async def trigger_introspection_sync(self, user_message: str, conversation_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Déclenche introspection de manière synchrone et retourne le résultat complet

        Args:
            user_message: Message utilisateur
            conversation_context: Contexte conversationnel

        Returns:
            Dict avec dialogue_messages, synthesis, save_decision, etc.
        """
        if not self.is_enabled:
            print("[INTROSPECTION-CORE] ⚠️ Extension désactivée")
            return {"success": False, "error": "Extension désactivée"}

        if self.is_introspection_active:
            print("[INTROSPECTION-CORE] ⚠️ Introspection déjà en cours")
            return {"success": False, "error": "Introspection déjà active"}

        # Lancer introspection et attendre résultat
        final_response = await self.trigger_introspection(
            user_message=user_message,
            conversation_context=conversation_context,
            trigger_source="sync_call"
        )

        # Récupérer données complètes depuis last_introspection_result
        if self.last_introspection_result and final_response:
            # Combiner avec données orchestrateur
            full_result = {
                "success": True,
                "dialogue_messages": self.last_introspection_result.get("dialogue_messages", []),
                "main_ai_analysis": self.last_introspection_result.get("main_ai_analysis", ""),
                "synthesis": self.last_introspection_result.get("synthesis", ""),
                "save_decision": self.last_introspection_result.get("save_decision", "no"),
                "importance": self.last_introspection_result.get("importance", 5),
                "final_response": final_response
            }
            return full_result

        return {"success": False, "error": "Échec introspection"}

    def toggle_enabled(self) -> bool:
        """
        Bascule l'état ON/OFF de l'extension

        Returns:
            Nouvel état
        """
        new_state = not self.is_enabled
        # self.is_enabled = new_state  # Maintenant géré par le setter de la propriété
        self.config.set("extension_enabled", new_state)

        print(f"[INTROSPECTION-CORE] {'🟢' if new_state else '🔴'} Extension {'ACTIVÉE' if new_state else 'DÉSACTIVÉE'}")

        return new_state

    @property
    def is_enabled(self) -> bool:
        """
        Propriété dynamique pour vérifier l'état d'activation
        
        Lit toujours depuis la configuration pour synchronisation temps réel
        
        Returns:
            bool: True si extension activée
        """
        return self.config.is_enabled()
    
    @is_enabled.setter
    def is_enabled(self, value: bool):
        """
        Setter pour l'état d'activation
        
        Met à jour la configuration sous-jacente
        
        Args:
            value: Nouvel état d'activation
        """
        self.config.set('extension_enabled', value)

    def is_enabled_check(self) -> bool:
        """
        Vérifie si l'extension est activée (méthode callable)

        Compatible avec appels is_enabled() depuis ogma_ng.py

        Returns:
            bool: True si extension activée
        """
        return self.is_enabled

    def get_status(self) -> Dict[str, Any]:
        """Retourne statut complet de l'extension"""
        return {
            "enabled": self.is_enabled,
            "introspection_active": self.is_introspection_active,
            "current_session_id": self.current_session_id,
            "mode": self.config.get_introspection_mode(),
            "stats": self.stats.copy(),
            "version": self.config.VERSION
        }

    def get_ui_components(self):
        """Retourne composants UI pour intégration OGMA"""
        return self.ui_components

    def enrich_conversation_context(self, conversation_context: Dict[str, Any]):
        """
        Enrichit le contexte de conversation pour les futures introspections.
        
        Cette méthode est appelée par OGMA pour fournir du contexte supplémentaire
        aux conversations d'introspection. Adaptation v2.0 de l'API legacy.
        
        Args:
            conversation_context: Contexte conversationnel à enrichir
        """
        try:
            print("[INTROSPECTION-CORE] 🔍 Enrichissement contexte conversation")
            
            # Stocker le contexte pour utilisation future dans les introspections
            if not hasattr(self, 'enriched_context'):
                self.enriched_context = {}
            
            # Fusionner avec contexte existant
            self.enriched_context.update(conversation_context)
            
            # Ajouter timestamp d'enrichissement et métadonnées v2.0
            from datetime import datetime
            self.enriched_context['last_enrichment'] = datetime.now().isoformat()
            self.enriched_context['enrichment_source'] = 'ogma_conversation_hook'
            
            print(f"[INTROSPECTION-CORE] ✅ Contexte enrichi avec {len(conversation_context)} éléments")
            
            # Optionnel: Si une introspection est active, notifier l'orchestrateur
            if (self.is_introspection_active and 
                self.introspection_orchestrator and 
                hasattr(self.introspection_orchestrator, 'update_context')):
                try:
                    self.introspection_orchestrator.update_context(conversation_context)
                    print("[INTROSPECTION-CORE] 📡 Contexte transmis à l'orchestrateur actif")
                except Exception as orch_e:
                    print(f"[INTROSPECTION-CORE] ⚠️ Erreur transmission orchestrateur: {orch_e}")
            
        except Exception as e:
            print(f"[INTROSPECTION-CORE] ❌ Erreur enrichissement contexte: {e}")

    # ===== MÉTHODES PRIVÉES =====

    def _should_trigger_introspection(self, user_message: str) -> bool:
        """Détermine si introspection doit être déclenchée"""
        # Mode always
        mode = self.config.get_introspection_mode()
        if mode == "always":
            return True

        # Mode on_demand - vérifier phrases magiques
        if mode == "on_demand":
            magic_type = self.check_magic_phrases(user_message, source="user")
            return magic_type == "trigger"

        return False

    async def _save_introspection_memory(self, introspection_result: Dict[str, Any]):
        """Sauvegarde introspection en mémoire"""
        try:
            importance = introspection_result.get("importance", 5)
            threshold = self.config.get("importance_threshold", 5)

            if importance < threshold:
                print(f"[INTROSPECTION-CORE] 🚫 Importance {importance} < seuil {threshold} - pas de sauvegarde")
                return

            # Sauvegarder via memory_integration
            success = await self.memory_integration.save_introspection_conditional(introspection_result)

            if success:
                self.stats["total_saved"] += 1
                print(f"[INTROSPECTION-CORE] 💾 Introspection sauvegardée (importance: {importance}/10)")

        except Exception as e:
            print(f"[INTROSPECTION-CORE] ❌ Erreur sauvegarde mémoire: {e}")

    def _update_average_duration(self, duration: float):
        """Met à jour durée moyenne des introspections"""
        total = self.stats["total_introspections"]
        current_avg = self.stats["average_duration"]

        # Moyenne mobile
        new_avg = ((current_avg * (total - 1)) + duration) / total
        self.stats["average_duration"] = new_avg

    def set_callbacks(self, on_state_change=None, on_reflection_start=None, on_reflection_end=None,
                      on_external_settings_change=None, on_synthesis_ready=None, on_message_ready=None):
        """
        Configure les callbacks externes vers OGMA

        Args:
            on_state_change: Callback(new_state) appelé lors changement état
            on_reflection_start: Callback(session_id) appelé début introspection
            on_reflection_end: Callback(session_id, result) appelé fin introspection
            on_external_settings_change: Callback(key, value) appelé changement paramètre
            on_synthesis_ready: Callback(synthesis) appelé synthèse prête
            on_message_ready: Callback(role, content) appelé nouveau message dialogue
        """
        if on_state_change:
            self.on_state_change = on_state_change
        if on_reflection_start:
            self.on_introspection_start = on_reflection_start
        if on_reflection_end:
            self.on_introspection_complete = on_reflection_end
        if on_external_settings_change:
            self.on_external_settings_change = on_external_settings_change
        if on_synthesis_ready:
            self.on_synthesis_ready = on_synthesis_ready
        if on_message_ready:
            self.on_message_ready = on_message_ready

        print("[INTROSPECTION-CORE] ✅ Callbacks configurés")

    def _on_toggle_callback(self, new_state: bool):
        """Callback toggle extension depuis UI"""
        # Mettre à jour la configuration (maintenant is_enabled est une propriété)
        self.config.set('extension_enabled', new_state)
        print(f"[INTROSPECTION-CORE] 🔄 Toggle UI: {'ON' if new_state else 'OFF'} - Config mise à jour")

    def _on_settings_change_callback(self, setting_key: str, new_value: Any):
        """Callback changement paramètres depuis UI"""
        print(f"[INTROSPECTION-CORE] ⚙️ Paramètre modifié: {setting_key} = {new_value}")
        
        # Assurer la synchronisation de la configuration
        if setting_key == 'extension_enabled':
            # Forcer la mise à jour dans la config si pas déjà fait
            current_value = self.config.get('extension_enabled', False)
            if current_value != new_value:
                self.config.set('extension_enabled', new_value)
                print(f"[INTROSPECTION-CORE] 🔄 Configuration synchronisée: extension_enabled = {new_value}")

        # 🎛️ SYNCHRONISATION INTERFACE → ACTION IMMÉDIATE
        # Paramètres qui nécessitent rechargement des templates/comportement
        template_related_settings = [
            'synthesis_structure_instruction', 'main_ai_introspection_instruction',
            'archiviste_introspection_instruction', 'initial_analysis_instruction',
            'direct_memory_access_instruction', 'introspection_box_template'
        ]
        
        behavior_related_settings = [
            'max_dialogue_exchanges', 'max_introspection_duration',
            'main_ai_tokens_per_message', 'archiviste_tokens_per_message',
            'synthesis_max_tokens', 'introspection_mode'
        ]
        
        if setting_key in template_related_settings or setting_key in behavior_related_settings:
            print(f"[INTROSPECTION-CORE] 🔄 Rechargement automatique pour: {setting_key}")
            self.reload_config_from_file()
            print(f"[INTROSPECTION-CORE] ✅ Paramètre '{setting_key}' appliqué immédiatement")

        # Callback externe vers OGMA si défini
        if self.on_external_settings_change:
            self.on_external_settings_change(setting_key, new_value)

    async def _on_dialogue_message(self, role: str, content: str):
        """
        Callback interne appelé par orchestrator pour chaque nouveau message
        Transmet au callback externe (OGMA) pour affichage temps réel
        """
        if self.on_message_ready:
            await self.on_message_ready(role, content)

    def format_dialogue_for_thinking_box(self, dialogue_messages: List[Dict], analysis: str = "", synthesis: str = "") -> str:
        """
        Formate le dialogue IA Principale-Archiviste pour affichage structuré et épuré

        Args:
            dialogue_messages: Liste des messages {role, content, timestamp}
            analysis: Analyse initiale (optionnelle)
            synthesis: Synthèse finale optionnelle

        Returns:
            str: Dialogue formaté en markdown structuré sans mentions d'étapes
        """
        lines = []
        
        # Analyse initiale (si fournie)
        if analysis:
            lines.append("**IA Principale :**")
            lines.append(f"{analysis}")
            lines.append("")

        # Dialogue
        if dialogue_messages:
            current_speaker = None
            for msg in dialogue_messages:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")

                if role == "main_ai":
                    if current_speaker != "main_ai":
                        if current_speaker is not None:
                            lines.append("")  # Saut entre intervenants différents
                        lines.append("**IA Principale :**")
                        current_speaker = "main_ai"
                    lines.append(f"{content}")
                    
                elif role == "archiviste":
                    if current_speaker != "archiviste":
                        if current_speaker is not None:
                            lines.append("")  # Saut entre intervenants différents
                        lines.append("**Archiviste :**")
                        current_speaker = "archiviste"
                    lines.append(f"{content}")
            
            lines.append("")

        # Synthèse finale (si fournie)
        if synthesis:
            lines.append("**IA Principale :**")
            lines.append(f"{synthesis}")

        return "\n".join(lines)

    def cleanup(self):
        """Nettoyage et arrêt propre de l'extension"""
        print("[INTROSPECTION-CORE] 🧹 Nettoyage en cours...")

        # Arrêter introspection active
        if self.is_introspection_active:
            self.stop_current_introspection("cleanup")

        # Cleanup composants
        if self.ui_components:
            self.ui_components.cleanup()

        if self.introspection_orchestrator:
            self.introspection_orchestrator.cleanup()

        print("[INTROSPECTION-CORE] ✅ Nettoyage terminé")


# ===== API SINGLETON =====

_introspection_core_instance = None

def initialize_introspection_core(chat_controller, archiviste_controller, memory_manager, ui_container=None, settings_manager=None) -> bool:
    """
    Initialise l'instance globale IntrospectionCore

    Args:
        chat_controller: AIController IA principale
        archiviste_controller: AIController Archiviste
        memory_manager: MemoryManager OGMA
        ui_container: Container NiceGUI
        settings_manager: SettingsManager pour accès prompts système

    Returns:
        True si succès
    """
    global _introspection_core_instance

    try:
        _introspection_core_instance = IntrospectionCore(
            chat_controller=chat_controller,
            archiviste_controller=archiviste_controller,
            memory_manager=memory_manager,
            ui_container=ui_container,
            settings_manager=settings_manager
        )

        success = _introspection_core_instance.initialize()

        if success:
            print("[INTROSPECTION-CORE] ✅ Instance globale initialisée")

        return success

    except Exception as e:
        print(f"[INTROSPECTION-CORE] ❌ Erreur initialisation globale: {e}")
        return False

def get_introspection_core() -> Optional[IntrospectionCore]:
    """Retourne l'instance globale IntrospectionCore"""
    return _introspection_core_instance


# Exports
__all__ = ['IntrospectionCore', 'initialize_introspection_core', 'get_introspection_core']
