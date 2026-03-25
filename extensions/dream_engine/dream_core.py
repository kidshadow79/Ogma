"""
Dream Engine - Core
====================

Boucle de rêve principale avec métabolisme lent et mécanisme de sursaut.
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path
import asyncio
import time

# ========== CLASSE PRINCIPALE ==========
class DreamEngine:
    """
    Moteur de rêve pour OGMA.
    Gère le cycle de rêve, le métabolisme lent, et le réveil.
    """
    
    def __init__(
        self,
        chat_controller=None,
        archiviste_controller=None,
        memory_manager=None,
        settings_manager=None
    ):
        # Dépendances OGMA
        self._chat_controller = chat_controller
        self._archiviste_controller = archiviste_controller
        self._memory_manager = memory_manager
        self._settings_manager = settings_manager
        
        # État du rêve - PHASES DISTINCTES
        self._is_dreaming = False
        self._surge_mode = False  # Mode sursaut (vitesse max)
        self._dream_phase = "idle"  # "idle" | "dreaming" | "sleeping" | "waking"
        self._dream_task: Optional[asyncio.Task] = None
        self._sleep_task: Optional[asyncio.Task] = None
        self._cancel_event = asyncio.Event()
        
        # Timestamps
        self._timestamp_entry: Optional[datetime] = None
        self._timestamp_exit: Optional[datetime] = None
        self._timestamp_dream_end: Optional[datetime] = None
        
        # Contenu du rêve
        self._current_dream: Optional[str] = None
        self._current_analysis: Optional[Dict] = None
        self._current_illustration: Optional[str] = None
        self._current_illustration_prompt: Optional[str] = None  # Prompt utilisé pour l'illustration
        self._web_discovery: Optional[str] = None  # Découverte web du rêve
        
        # Configuration
        self._config = self._load_config()
        
        # Logs
        self._log_file = Path(__file__).parent.parent.parent / 'logs' / 'dreams.log'
        self._log_file.parent.mkdir(exist_ok=True)
        
        print("[DREAM-ENGINE] 🌙 DreamEngine initialisé")
    
    def _load_config(self) -> Dict[str, Any]:
        """Charge la configuration depuis settings.json."""
        default = {
            "enabled": True,
            "inactivity_timeout_minutes": 10,
            # Phase RÊVE
            "metabolism_tokens_per_minute": 100,  # 100 tokens/min pendant génération
            "max_dream_tokens": 3000,  # Plus de tokens pour un rêve riche
            "auto_illustration": True,
            "illustration_style": "auto",
            # Souvenirs aléatoires
            "random_memories_count": 5,  # Nombre de souvenirs aléatoires
            "impact_threshold": 150.0,   # Seuil impact minimum
            # Recherche web
            "web_search_enabled": True,  # L'IA explore internet
            # Phase SOMMEIL
            "sleep_duration_hours": 7,   # Durée de sommeil passif
            # Réveil automatique
            "auto_wake_message": True,   # Envoi message spontané au réveil
        }
        
        if self._settings_manager:
            try:
                dream_config = self._settings_manager.settings.get('dream_engine', {})
                default.update(dream_config)
            except Exception as e:
                print(f"[DREAM-ENGINE] ⚠️ Erreur chargement config: {e}")
        
        return default
    
    def get_phase(self) -> str:
        """Retourne la phase actuelle: 'idle', 'dreaming', 'sleeping', 'waking'."""
        return self._dream_phase
    
    def get_config(self) -> Dict[str, Any]:
        """Retourne la configuration actuelle."""
        return self._config.copy()
    
    def set_config(self, config: Dict[str, Any]) -> bool:
        """Met à jour la configuration."""
        try:
            self._config.update(config)
            
            # Sauvegarder dans settings.json
            if self._settings_manager:
                self._settings_manager.settings['dream_engine'] = self._config
                self._settings_manager.save_settings()
            
            return True
        except Exception as e:
            print(f"[DREAM-ENGINE] ❌ Erreur sauvegarde config: {e}")
            return False
    
    def is_dreaming(self) -> bool:
        """Vérifie si un rêve est en cours."""
        return self._is_dreaming
    
    def _log(self, message: str):
        """Écrit dans le fichier de log des rêves."""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(self._log_file, 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] {message}\n")
            print(f"[DREAM-LOG] {message}")
        except Exception as e:
            print(f"[DREAM-ENGINE] ⚠️ Erreur log: {e}")
    
    async def start_dream(self) -> bool:
        """
        Démarre un cycle de rêve.
        
        Returns:
            True si le rêve a démarré
        """
        if self._is_dreaming:
            self._log("⚠️ Rêve déjà en cours")
            return False
        
        if not self._config.get('enabled', False):
            self._log("⚠️ Dream Engine désactivé")
            return False
        
        # Marquer l'entrée en veille
        self._is_dreaming = True
        self._surge_mode = False
        self._timestamp_entry = datetime.now()
        self._cancel_event.clear()
        
        self._log(f"🌙 ENTRÉE EN VEILLE - {self._timestamp_entry.strftime('%H:%M:%S')}")
        
        # Afficher le spinner dans le chat
        try:
            from .dream_ui import show_dream_spinner_in_chat
            show_dream_spinner_in_chat()
        except Exception as e:
            self._log(f"⚠️ Erreur show spinner: {e}")
        
        # Lancer la boucle de rêve en arrière-plan
        self._dream_task = asyncio.create_task(self._dream_cycle())
        
        return True
    
    async def stop_dream(self) -> bool:
        """Arrête le rêve en cours (sans sursaut)."""
        if not self._is_dreaming:
            return False
        
        self._cancel_event.set()
        
        if self._dream_task:
            try:
                await asyncio.wait_for(self._dream_task, timeout=5.0)
            except asyncio.TimeoutError:
                self._dream_task.cancel()
        
        self._is_dreaming = False
        self._log("🛑 Rêve arrêté manuellement")
        
        return True
    
    async def wake_up(self, reason: str = "user_input") -> Dict[str, Any]:
        """
        Reveille l'IA avec sursaut (vitesse max pour finir).
        
        Args:
            reason: Raison du reveil
            
        Returns:
            Dict avec infos du reve
        """
        if not self._is_dreaming:
            return {"error": "Pas de rêve en cours", "was_dreaming": False}
        
        self._log(f"⚡ SURSAUT - Raison: {reason}")
        
        # Activer le mode sursaut (vitesse électrique)
        self._surge_mode = True
        self._timestamp_exit = datetime.now()
        
        # Mettre a jour le spinner pour indiquer l'eveil en cours
        try:
            from .dream_ui import update_dream_spinner_phase
            update_dream_spinner_phase("waking")
        except Exception as e:
            self._log(f"Erreur update spinner waking: {e}")
        
        # Calculer la durée du sommeil
        sleep_duration = self._calculate_sleep_duration()
        
        # Attendre la fin du reve (en mode rapide, avec marge pour generation image)
        # Timeout 600s car la génération d'image KIE peut prendre > 3 min
        if self._dream_task and not self._dream_task.done():
            try:
                await asyncio.wait_for(self._dream_task, timeout=600.0)
            except asyncio.TimeoutError:
                self._log("Timeout sursaut (600s) - forcage arret")
                self._cancel_event.set()
        
        self._is_dreaming = False
        
        # Cacher le spinner dans le chat
        try:
            from .dream_ui import hide_dream_spinner_in_chat
            hide_dream_spinner_in_chat()
        except Exception as e:
            self._log(f"⚠️ Erreur hide spinner: {e}")
        
        # 🌅 NOUVEAU: Envoyer message de réveil + image AUSSI lors d'un sursaut
        if self._current_dream and self._config.get('auto_wake_message', True):
            await self._send_surge_wake_message()
        
        result = {
            "was_dreaming": True,
            "reason": reason,
            "sleep_duration": sleep_duration,
            "sleep_duration_formatted": self._format_duration(sleep_duration),
            "dream_content": self._current_dream,
            "analysis": self._current_analysis,
            "timestamp_entry": self._timestamp_entry.isoformat() if self._timestamp_entry else None,
            "timestamp_exit": self._timestamp_exit.isoformat() if self._timestamp_exit else None,
        }
        
        self._log(f"☀️ RÉVEIL - Durée: {result['sleep_duration_formatted']}")
        
        return result
    
    async def _send_surge_wake_message(self):
        """
        Envoie le message de reveil lors d'un sursaut (utilisateur a envoye un message).
        Affiche le reve + image dans le chat AVANT la reponse de l'IA.
        """
        try:
            self._log("🌅 Envoi message réveil sursaut...")
            self._log(f"🌅 Dream: {len(self._current_dream) if self._current_dream else 0} chars")
            self._log(f"🌅 Illustration: {self._current_illustration}")
            
            # 🔧 FIX: Si illustration est None, chercher la dernière image de rêve générée
            if not self._current_illustration:
                self._log("🔍 Illustration None - Recherche image partielle...")
                recovered_image = self._recover_partial_dream_image()
                if recovered_image:
                    self._current_illustration = recovered_image
                    self._log(f"✅ Image partielle récupérée: {recovered_image}")
                    
                    # Mettre à jour le journal avec l'image récupérée
                    try:
                        from .dream_journal import update_dream_illustration
                        await update_dream_illustration(
                            illustration_path=recovered_image,
                            illustration_prompt=self._current_illustration_prompt
                        )
                        self._log("📔 Journal mis à jour avec image récupérée")
                    except Exception as upd_err:
                        self._log(f"⚠️ Erreur MAJ journal: {upd_err}")
            
            # Construire un résumé du rêve
            dream_summary = self._current_dream[:800] if self._current_dream else "un rêve mystérieux"
            analysis_summary = ""
            
            if self._current_analysis:
                score = self._current_analysis.get('score_importance', 5)
                emotion = self._current_analysis.get('emotion_dominante', 'mixte')
                analysis_summary = f"[Score: {score}/10 | Émotion: {emotion}]"
            
            # Générer le message de réveil
            self._log("🌅 Génération message réveil...")
            wake_message = await self._generate_wake_message(dream_summary, analysis_summary)
            
            if wake_message:
                self._log(f"🌅 Message généré: {wake_message[:80]}...")
                await self._send_wake_message_to_chat(wake_message)
                self._log(f"🌅 Message réveil sursaut envoyé!")
            else:
                self._log("⚠️ Pas de message réveil généré (wake_message=None)")
                
        except Exception as e:
            self._log(f"❌ Erreur message réveil sursaut: {e}")
            import traceback
            traceback.print_exc()
    
    def _calculate_sleep_duration(self) -> float:
        """Calcule la durée RÉELLE du sommeil en secondes (temps objectif)."""
        if not self._timestamp_entry:
            return 0.0
        
        end = self._timestamp_exit or datetime.now()
        duration = (end - self._timestamp_entry).total_seconds()
        
        # Protection contre temps négatifs (bug si timestamps incohérents)
        return max(0.0, duration)
    
    def _format_duration(self, seconds: float) -> str:
        """Formate une durée en HH:MM:SS."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    async def _dream_cycle(self):
        """
        Boucle principale du rêve avec 2 phases distinctes:
        
        PHASE 1 - REVE ACTIF (100 tokens/min):
        - Extraction carburant (resumes, convos, souvenirs, random+impact)
        - Recherche web autonome (l'IA choisit un sujet)
        - Generation du reve avec metabolisme lent
        - Analyse PSY + Illustration
        - Sauvegarde journal
        
        PHASE 2 - SOMMEIL PASSIF (7h par défaut):
        - Timer passif (0 tokens)
        - Spinner modifié ("dort" au lieu de "rêve")
        - Au terme: réveil automatique avec message
        
        SURSAUT: Si l'utilisateur envoie un message pendant le rêve,
        la phase RÊVE s'accélère instantanément et on saute la phase SOMMEIL.
        """
        try:
            # ═══════════════════════════════════════════════════════════════
            # PHASE 1 : RÊVE ACTIF
            # ═══════════════════════════════════════════════════════════════
            self._dream_phase = "dreaming"
            self._log("🌙 PHASE 1 - RÊVE ACTIF")
            
            # Mettre à jour le spinner pour afficher "rêve"
            try:
                from .dream_ui import update_dream_spinner_phase
                ia_name = self._get_ia_name()
                update_dream_spinner_phase("dreaming", ia_name)
            except Exception as e:
                self._log(f"⚠️ Erreur update spinner phase: {e}")
            
            # 1. Extraire le carburant mémoriel enrichi
            from .dream_memory import extract_dream_fuel
            fuel = await extract_dream_fuel(
                self._memory_manager,
                random_memories_count=self._config.get('random_memories_count', 5),
                impact_threshold=self._config.get('impact_threshold', 150.0)
            )
            
            if not fuel:
                self._log("❌ Pas de carburant mémoriel disponible")
                return
            
            self._log(f"⛽ Carburant: {len(fuel.get('summaries', []))} résumés, "
                     f"{len(fuel.get('conversations', []))} convos, "
                     f"{len(fuel.get('memories', []))} #MEM, "
                     f"{len(fuel.get('random_memories', []))} random (impact ≥ {self._config.get('impact_threshold', 150)})")
            
            # 2. ═══════ NOUVEAUTÉ V3 : Recherche Web Autonome ═══════
            if self._config.get('web_search_enabled', True) and not self._surge_mode:
                self._log("L'IA choisit un sujet a explorer...")
                
                from .dream_memory import generate_web_search_query, execute_web_search
                
                # L'IA decide quoi chercher (ordre correct: chat_controller, fuel)
                search_query = await generate_web_search_query(
                    chat_controller=self._chat_controller,
                    fuel=fuel
                )
                
                if search_query:
                    self._log(f"🔍 Recherche: \"{search_query}\"")
                    
                    # Exécuter la recherche
                    search_results = await execute_web_search(
                        query=search_query,
                        settings_manager=self._settings_manager
                    )
                    
                    if search_results:
                        fuel['web_discovery'] = {
                            'query': search_query,
                            'results': search_results
                        }
                        self._web_discovery = fuel['web_discovery']
                        self._log(f"🌐 {len(search_results)} résultats trouvés")
                    else:
                        self._log("⚠️ Aucun résultat web trouvé")
                else:
                    self._log("⚠️ Pas de sujet de recherche généré")
            
            # 3. Générer le rêve avec métabolisme lent
            self._current_dream = await self._generate_dream_slow(fuel)
            
            # Vérifier si le rêve est réellement généré
            if not self._current_dream or (isinstance(self._current_dream, str) and len(self._current_dream.strip()) == 0):
                self._log("\u274c Reve vide apres generation (possible block contenu) - abandon cycle")
                self._current_dream = None
                # Pas de Phase 2 inutile, on sort
                return
            
            if self._cancel_event.is_set():
                if not self._current_dream:
                    # Vraiment rien - abandon total
                    self._log("Reve annule avant generation - abandon")
                    return
                else:
                    # Contenu partiel disponible (ex: timeout sursaut) - sauvegarder quand meme
                    self._log(f"Reve interrompu ({len(self._current_dream)} chars) - sauvegarde du contenu partiel")
            
            # Nettoyer le marqueur d'interruption si présent (ajouté par call_chat_api_streaming)
            if self._current_dream and "\n\n⏹️ *[Génération interrompue par l'utilisateur]*" in self._current_dream:
                self._current_dream = self._current_dream.replace("\n\n⏹️ *[Génération interrompue par l'utilisateur]*", "").rstrip()
                self._log("Marqueur d'interruption retiré du contenu du rêve")
            
            # 4. Générer les prompts d'illustration (AVANT analyse PSY)
            illustration_prompts = []
            if self._current_dream and self._config.get('auto_illustration', True):
                from .dream_illustration import generate_illustration_prompts
                
                dream_summary = self._current_dream[:500] if self._current_dream else ""
                illustration_prompts = await generate_illustration_prompts(
                    dream_content=self._current_dream,
                    dream_summary=dream_summary,
                    chat_controller=self._chat_controller,
                    style=self._config.get('illustration_style', 'auto')
                )
                
                if illustration_prompts:
                    self._log(f"🎨 {len(illustration_prompts)} prompt(s) d'illustration générés")
            
            # 5. Analyser avec l'Archiviste (inclut les prompts d'illustration + temps réel)
            if self._current_dream:
                from .dream_analysis import analyze_dream
                
                # Calculer la durée réelle actuelle pour l'Archiviste
                current_sleep_duration = self._calculate_sleep_duration()
                current_sleep_formatted = self._format_duration(current_sleep_duration)
                
                self._current_analysis = await analyze_dream(
                    self._current_dream,
                    fuel,
                    self._archiviste_controller,
                    illustration_prompts=illustration_prompts,
                    real_sleep_duration_formatted=current_sleep_formatted
                )
                
                # Vérifier si réveil proactif nécessaire
                score = self._current_analysis.get('score_importance', 0)
                if score > 8 and not self._surge_mode:
                    self._log(f"🌟 Score {score}/10 - Réveil proactif recommandé!")
                
                # 🎯 NOUVEAU: Détection phrases magiques dans l'analyse du rêve
                # L'Archiviste peut avoir écrit "il faut que je me souvienne de ça: [leçon]"
                try:
                    raw_analysis = self._current_analysis.get('raw_response', '')
                    if raw_analysis:
                        self._log("🔍 Analyse phrases magiques dans le verdict PSY...")
                        
                        import re
                        import uuid
                        
                        # Patterns inline (identiques à _extract_magic_memories dans ogma_ng.py)
                        magic_patterns = [
                            r"(?:\*\*|__)?il\s+faut\s+que\s+je\s+me\s+souvienne\s+de\s+(?:ça|ca|cela|ceci)(?:\*\*|__)?[\s\.\-:]*(.+?)(?=\n\n|\n\s*\n|$)",
                            r"(?:\*\*|__)?m[ée]morise(?:s)?\s+(?:ça|ca|cela|ceci)(?:\*\*|__)?[\s\.\-:]*(.+?)(?=\n\n|\n\s*\n|$)",
                        ]
                        
                        magic_memories = []
                        for pat in magic_patterns:
                            found = re.findall(pat, raw_analysis, flags=re.IGNORECASE | re.DOTALL)
                            if found:
                                self._log(f"🔍 Match trouvé: {found}")
                            for m in found:
                                content = m.strip()
                                if content:
                                    content = re.sub(r'^[:\-\s\.]+', '', content)
                                    content = re.sub(r'(\*\*|__)$', '', content).strip()
                                    content = re.sub(r'</?[A-ZÉÈÊa-zéèê_]+>', '', content).strip()
                                    if content:
                                        magic_memories.append(content)
                        
                        if magic_memories:
                            self._log(f"✅ {len(magic_memories)} phrase(s) magique(s) détectée(s)")
                            
                            from ogma_ng import _ensure_memory_manager, _notify_safe, _trigger_memory_update
                            mm = _ensure_memory_manager()
                            if mm:
                                for content in magic_memories:
                                    try:
                                        self._log(f"💾 Mémorisation leçon rêve: '{content[:80]}...'")
                                        mem_id = f"ai-dream-{uuid.uuid4()}"
                                        
                                        # Contexte : le rêve lui-même
                                        dream_context = f"Rêve: {self._current_dream[:500]}\n\nAnalyse: {raw_analysis[:500]}"
                                        
                                        ok = await mm.add_memory(
                                            mem_id,
                                            content,
                                            chat_controller=self._chat_controller,
                                            conversation_context=dream_context,
                                            interlocutor="Rêve"
                                        )
                                        
                                        if ok:
                                            self._log(f"✅ Leçon mémorisée depuis rêve: {mem_id}")
                                            _notify_safe(f"💭 Leçon mémorisée depuis rêve: {content[:80]}...", 'positive')
                                            _trigger_memory_update()
                                        else:
                                            self._log(f"⚠️ Échec mémorisation leçon rêve")
                                    except Exception as me:
                                        self._log(f"❌ Erreur mémorisation leçon: {me}")
                                        import traceback
                                        traceback.print_exc()
                            else:
                                self._log("⚠️ MemoryManager non disponible pour mémorisation rêve")
                        else:
                            self._log("⚪ Aucune phrase magique dans le verdict PSY")
                except Exception as magic_err:
                    self._log(f"❌ Erreur détection phrases magiques rêve: {magic_err}")
                    import traceback
                    traceback.print_exc()
                
                # 6. Sauvegarder journal + wake context AVANT l'image
                # (critique: si l'image timeout, le reve doit quand meme etre sauvegarde)
                from .dream_journal import save_dream
                
                sleep_duration = self._format_duration(self._calculate_sleep_duration())
                web_query = self._web_discovery.get('query', '') if self._web_discovery else ''
                
                self._current_illustration = None
                self._current_illustration_prompt = illustration_prompts[0] if illustration_prompts else None
                
                journal_result = await save_dream(
                    dream_content=self._current_dream,
                    analysis=self._current_analysis,
                    illustration_path=None,  # Image pas encore generee
                    illustration_prompt=self._current_illustration_prompt,
                    sleep_duration=sleep_duration,
                    web_search_query=web_query
                )
                
                if journal_result.get('success'):
                    self._log(f"Journal reve sauvegarde: {journal_result.get('dream_id')}")
                
                # Stocker le contexte de reveil (l'IA saura qu'elle a reve)
                from . import set_wake_context
                set_wake_context(
                    dream_content=self._current_dream,
                    analysis=self._current_analysis,
                    sleep_duration=sleep_duration
                )
                self._log("Contexte de reveil prepare pour l'IA")
                
                # 7. Generer l'image (APRES sauvegarde)
                if illustration_prompts:
                    from .dream_illustration import generate_dream_illustration
                    
                    illustration_style = self._config.get('illustration_style', 'auto')
                    print(f"[DREAM-CORE] Style illustration: {illustration_style}")
                    
                    illust_result = await generate_dream_illustration(
                        dream_content=self._current_dream,
                        dream_summary=dream_summary,
                        chat_controller=self._chat_controller,
                        settings_manager=self._settings_manager,
                        style=illustration_style,
                        pregenerated_prompts=illustration_prompts
                    )
                    
                    if illust_result.get('success'):
                        self._current_illustration = illust_result.get('image_path')
                        self._log(f"Illustration creee: {self._current_illustration}")
                        
                        # Mettre a jour le journal avec l'image
                        try:
                            from .dream_journal import update_dream_illustration
                            await update_dream_illustration(
                                illustration_path=self._current_illustration,
                                illustration_prompt=self._current_illustration_prompt
                            )
                            self._log("Journal mis a jour avec illustration")
                        except Exception as upd_err:
                            self._log(f"Erreur MAJ journal illustration: {upd_err}")
            
            self._timestamp_dream_end = datetime.now()
            self._log("✅ PHASE 1 terminée - Rêve généré")
            
            # ═══════════════════════════════════════════════════════════════
            # CONSOLIDATION EGO : Mettre à jour le portrait de personnalité
            # Moment idéal : rêve terminé, IA inactive, pas de conflit possible
            # ═══════════════════════════════════════════════════════════════
            try:
                from scripts.ego_compiler import compile_ego_incremental
                self._log("Consolidation identite (portrait de personnalite)...")
                await compile_ego_incremental()
                self._log("Portrait de personnalite mis a jour apres le reve")
            except Exception as e:
                self._log(f"Consolidation identite non bloquante: {e}")
            
            # ═══════════════════════════════════════════════════════════════
            # INTROSPECTION IA : Journal intime post-rêve
            # L'IA principale écrit dans son journal intime après le rêve
            # et la mise à jour de son portrait — moment de réflexion
            # ═══════════════════════════════════════════════════════════════
            try:
                from extensions.journal_de_bord import is_available as journal_intro_available
                if journal_intro_available():
                    from extensions.journal_de_bord.introspection_ia import (
                        get_introspection_module,
                        initialize_introspection,
                        generate_post_dream_introspection
                    )
                    from extensions.journal_de_bord import get_journal
                    
                    # Initialiser si pas encore fait
                    module = get_introspection_module()
                    if module is None:
                        journal = get_journal()
                        initialize_introspection(
                            json_manager=journal.json_manager,
                            chat_controller=self._chat_controller,
                            archiviste_controller=self._archiviste_controller
                        )
                    
                    self._log("Introspection IA (journal intime post-reve)...")
                    
                    # Récupérer les états actifs pour contexte
                    intro_active_states = []
                    try:
                        journal = get_journal()
                        all_states = journal.json_manager.get_active_states()
                        intro_active_states = [s for s in all_states.get("states", []) if not s.get("resolved", False)]
                    except Exception:
                        pass
                    
                    intro_result = await generate_post_dream_introspection(
                        dream_content=self._current_dream or "",
                        dream_analysis=self._current_analysis or {},
                        ego_flags=None,
                        active_states=intro_active_states
                    )
                    
                    if intro_result:
                        self._log(f"Journal intime: '{intro_result.get('titre', '?')}' ({intro_result.get('emotion_dominante', '?')})")
                    else:
                        self._log("Journal intime: pas d'entree generee")
                else:
                    self._log("Journal de bord non disponible - skip introspection")
            except Exception as e:
                self._log(f"Introspection IA non bloquante: {e}")
            
            # ═══════════════════════════════════════════════════════════════
            # EXPLORATION CURIOSITÉ : L'IA explore un sujet qui l'intéresse
            # Pendant le rêve, l'IA peut réfléchir à une curiosité en attente
            # ═══════════════════════════════════════════════════════════════
            try:
                from extensions.journal_de_bord import is_available as journal_curio_available
                if journal_curio_available():
                    from extensions.journal_de_bord.curiosity_engine import (
                        get_curiosity_engine,
                        initialize_curiosity_engine,
                        explore_curiosity_during_dream
                    )
                    from extensions.journal_de_bord import get_journal
                    
                    # Initialiser si pas encore fait
                    engine = get_curiosity_engine()
                    if engine is None:
                        journal = get_journal()
                        initialize_curiosity_engine(
                            json_manager=journal.json_manager,
                            archiviste_controller=self._archiviste_controller,
                            chat_controller=self._chat_controller
                        )
                    
                    self._log("Exploration curiosite autonome...")
                    exploration = await explore_curiosity_during_dream()
                    
                    if exploration:
                        self._log(f"Curiosite exploree: '{exploration.get('sujet', '?')[:50]}'")
                    else:
                        self._log("Aucune curiosite en attente")
                else:
                    self._log("Journal non disponible - skip exploration curiosite")
            except Exception as e:
                self._log(f"Exploration curiosite non bloquante: {e}")
            
            # ═══════════════════════════════════════════════════════════════
            # CONSOLIDATION JOURNAL : Résolution post-rêve des états actifs
            # Le rêve a digéré les conversations - moment idéal pour vérifier
            # si des états du journal de bord ont été résolus implicitement
            # ═══════════════════════════════════════════════════════════════
            try:
                from extensions.journal_de_bord import is_available as journal_available
                if journal_available():
                    self._log("Consolidation journal (resolution etats post-reve)...")
                    from extensions.journal_de_bord.shutdown_state_analyzer import (
                        get_shutdown_analyzer, 
                        initialize_shutdown_analyzer,
                        run_shutdown_analysis
                    )
                    from extensions.journal_de_bord import get_journal
                    
                    # Initialiser l'analyseur s'il ne l'est pas encore
                    analyzer = get_shutdown_analyzer()
                    if analyzer is None:
                        journal = get_journal()
                        analyzer = initialize_shutdown_analyzer(
                            json_manager=journal.json_manager,
                            archiviste_controller=self._archiviste_controller
                        )
                    
                    if analyzer:
                        result = await run_shutdown_analysis()
                        resolved = result.get("resolved_states", [])
                        analyzed = result.get("analyzed_conversations", 0)
                        self._log(f"Journal post-reve: {analyzed} convos analysees, {len(resolved)} etats resolus")
                    else:
                        self._log("Analyseur journal non disponible - skip")
                else:
                    self._log("Journal de bord non disponible - skip consolidation")
            except Exception as e:
                self._log(f"Consolidation journal non bloquante: {e}")
            
            # ═══════════════════════════════════════════════════════════════
            # MAINTENANCE ETATS ACTIFS : Pipeline complète
            # 1. Déduplication des doublons
            # 2. Résolution via conversations récentes
            # 3. Auto-résolution des états inactifs (3j medium, 7j high)
            # ═══════════════════════════════════════════════════════════════
            try:
                from extensions.journal_de_bord import is_available as journal_available_ar
                if journal_available_ar():
                    from extensions.journal_de_bord import get_journal
                    from extensions.journal_de_bord.auto_resolution import run_full_maintenance
                    
                    journal = get_journal()
                    maintenance_result = await run_full_maintenance(
                        json_manager=journal.json_manager,
                        archiviste_controller=self._archiviste_controller,
                        conversations_dir="data/conversations"
                    )
                    total = maintenance_result.get("total_resolved", 0)
                    dedup = maintenance_result.get("dedup", {}).get("resolved", 0)
                    conv = maintenance_result.get("conv_resolve", {}).get("resolved", 0)
                    auto = maintenance_result.get("auto_resolve", {}).get("resolved", 0)
                    self._log(f"Maintenance etats: {total} resolus (doublons:{dedup}, conv:{conv}, inactivite:{auto})")
                else:
                    self._log("Journal non disponible - skip maintenance etats")
            except Exception as e:
                self._log(f"Maintenance etats non bloquante: {e}")
            
            # ═══════════════════════════════════════════════════════════════
            # PHASE 2 : SOMMEIL PASSIF (sauf si sursaut)
            # ═══════════════════════════════════════════════════════════════
            if self._surge_mode:
                self._log("⚡ Sursaut - Phase sommeil ignorée")
            else:
                self._dream_phase = "sleeping"
                self._log("💤 PHASE 2 - SOMMEIL PASSIF")
                
                # Mettre à jour le spinner pour afficher "dort"
                try:
                    from .dream_ui import update_dream_spinner_phase
                    ia_name = self._get_ia_name()
                    update_dream_spinner_phase("sleeping", ia_name)
                except Exception as e:
                    self._log(f"⚠️ Erreur update spinner phase: {e}")
                
                # Durée de sommeil configurable (défaut 7h)
                sleep_hours = self._config.get('sleep_duration_hours', 7)
                sleep_seconds = sleep_hours * 3600
                
                self._log(f"😴 Sommeil passif: {sleep_hours}h ({sleep_seconds}s)")
                
                # Timer passif avec vérification sursaut périodique
                await self._passive_sleep(sleep_seconds)
                
                # Si toujours pas de sursaut après le sommeil complet: réveil automatique
                if not self._surge_mode and not self._cancel_event.is_set():
                    self._log("☀️ Réveil automatique après sommeil complet")
                    await self._automatic_wake()
            
        except asyncio.CancelledError:
            self._log("🚫 Rêve annulé")
        except Exception as e:
            self._log(f"❌ Erreur cycle rêve: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # TOUJOURS cacher le spinner à la fin du rêve
            try:
                from .dream_ui import hide_dream_spinner_in_chat, update_dream_header_btn
                hide_dream_spinner_in_chat()
                update_dream_header_btn(False)  # Bouton header : retour état normal
                self._log("🔄 Spinner caché + bouton header réinitialisé (fin cycle)")
            except Exception as e:
                self._log(f"⚠️ Erreur hide spinner (finally): {e}")
            
            # Réinitialiser la phase
            self._dream_phase = "idle"
            
            # Marquer fin du rêve seulement si pas en mode sursaut
            if not self._surge_mode:
                self._is_dreaming = False
    
    async def _passive_sleep(self, duration_seconds: float):
        """
        Phase de sommeil passif sans génération de tokens.
        Vérifie périodiquement si un sursaut a été déclenché.
        """
        check_interval = 10.0  # Vérifier toutes les 10 secondes
        elapsed = 0.0
        
        while elapsed < duration_seconds:
            # Vérifier sursaut ou annulation
            if self._surge_mode or self._cancel_event.is_set():
                self._log(f"⚡ Sommeil interrompu après {self._format_duration(elapsed)}")
                return
            
            # Attendre l'intervalle
            await asyncio.sleep(min(check_interval, duration_seconds - elapsed))
            elapsed += check_interval
            
            # Log de progression toutes les 30 minutes
            if int(elapsed) % 1800 == 0 and elapsed > 0:
                remaining = duration_seconds - elapsed
                self._log(f"💤 Sommeil: {self._format_duration(elapsed)} écoulé, "
                         f"{self._format_duration(remaining)} restant")
    
    async def _automatic_wake(self):
        """
        Réveil automatique après sommeil complet.
        Envoie spontanément le message de rêve dans le chat.
        """
        self._dream_phase = "waking"
        self._log("☀️ Réveil automatique - Envoi message spontané")
        
        try:
            # Construire le message de réveil
            from . import get_wake_summary_prompt
            
            dream_summary = self._current_dream[:800] if self._current_dream else "un rêve mystérieux"
            analysis_summary = ""
            
            if self._current_analysis:
                score = self._current_analysis.get('score_importance', 5)
                emotion = self._current_analysis.get('emotion_dominante', 'mixte')
                insight = self._current_analysis.get('insight_ego', '')
                analysis_summary = f"\n[Score: {score}/10 | Emotion: {emotion}]\n{insight}"
            
            # Generer le message de reveil naturel de l'IA
            wake_message = await self._generate_wake_message(dream_summary, analysis_summary)
            
            if wake_message and self._config.get('auto_wake_message', True):
                # Envoyer le message dans le chat via ogma_ng
                await self._send_wake_message_to_chat(wake_message)
            
        except Exception as e:
            self._log(f"❌ Erreur réveil automatique: {e}")
            import traceback
            traceback.print_exc()
    
    async def _generate_wake_message(self, dream_summary: str, analysis_summary: str) -> Optional[str]:
        """Genere un message naturel de reveil de l'IA."""
        if not self._chat_controller:
            return None
        
        try:
            from . import get_wake_summary_prompt
            
            system_prompt = get_wake_summary_prompt()
            user_prompt = f"""Tu viens de te réveiller après un rêve. Voici ce dont tu te souviens:

{dream_summary}

{analysis_summary}

Écris un message court et naturel (2-3 phrases) pour partager spontanément ce rêve avec ton utilisateur.
Sois toi-même, chaleureuse et un peu mystérieuse. Ne dis pas "j'ai rêvé que..." de manière mécanique.
"""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response, error = await self._chat_controller.call_chat_api(
                messages=messages,
                max_tokens=300,
                context_length=4096,
                temperature=0.7
            )
            
            return response if not error else None
            
        except Exception as e:
            self._log(f"⚠️ Erreur génération message réveil: {e}")
            return None
    
    async def _send_wake_message_to_chat(self, message: str):
        """Envoie le message de reveil dans le chat principal avec le reve complet."""
        try:
            from . import trigger_wake_message
            
            await trigger_wake_message(
                message=message,
                illustration_path=self._current_illustration,
                illustration_prompt=self._current_illustration_prompt,
                dream_content=self._current_dream,
                dream_analysis=self._current_analysis
            )
            
            self._log(f"Message de reveil envoye ({len(message)} chars)")
            
        except ImportError:
            self._log("trigger_wake_message non disponible - message non envoye")
        except Exception as e:
            self._log(f"Erreur envoi message reveil: {e}")
    
    def _recover_partial_dream_image(self) -> Optional[str]:
        """
        Récupère la dernière image de rêve générée si le rêve a été interrompu.
        Cherche dans data/generated_images/ les images récentes (< 5 min).
        """
        try:
            from pathlib import Path
            import time
            
            images_dir = Path(__file__).parent.parent.parent / 'data' / 'generated_images'
            
            if not images_dir.exists():
                return None
            
            # Chercher les images générées dans les 5 dernières minutes
            cutoff_time = time.time() - 300  # 5 minutes
            
            # Patterns pour les images de rêve
            dream_patterns = ['kie_*Dreamlike*', 'dream_comic_*', 'kie_*oniric*', 'kie_*surreal*']
            
            recent_images = []
            for pattern in dream_patterns:
                for img_path in images_dir.glob(pattern):
                    if img_path.stat().st_mtime > cutoff_time:
                        recent_images.append((img_path, img_path.stat().st_mtime))
            
            # Aussi chercher les images Kie générées récemment (fallback)
            for img_path in images_dir.glob('kie_*.png'):
                if img_path.stat().st_mtime > cutoff_time:
                    if (img_path, img_path.stat().st_mtime) not in recent_images:
                        recent_images.append((img_path, img_path.stat().st_mtime))
            
            if not recent_images:
                self._log("⚪ Aucune image de rêve récente trouvée")
                return None
            
            # Trier par date de modification (plus récent en premier)
            recent_images.sort(key=lambda x: x[1], reverse=True)
            
            # Prendre la plus récente
            latest_image = recent_images[0][0]
            self._log(f"🖼️ Image partielle trouvée: {latest_image.name}")
            
            return str(latest_image)
            
        except Exception as e:
            self._log(f"⚠️ Erreur récupération image partielle: {e}")
            return None
    
    def _get_ia_name(self) -> str:
        """Recupere le nom de l'IA depuis les settings."""
        try:
            if self._settings_manager:
                return self._settings_manager.settings.get('ia_name', 'IA')
        except:
            pass
        return "IA"
    
    async def _generate_dream_slow(self, fuel: Dict) -> Optional[str]:
        """
        Génère le rêve avec métabolisme lent (100 tokens/min par défaut).
        En mode sursaut, génère à vitesse maximale.
        """
        if not self._chat_controller:
            self._log("❌ Chat controller non disponible")
            return None
        
        try:
            from . import get_dream_prompt
            
            # Construire le contexte enrichi
            context = self._build_dream_context(fuel)
            
            # Prompt système pour le rêve (config prioritaire)
            system_prompt = get_dream_prompt()
            
            # ═══════ NOUVEAUTÉ V3 : Contexte enrichi ═══════
            # Sections optionnelles
            random_memories_section = ""
            if context.get('random_memories_text'):
                random_memories_section = f"""

## Souvenirs profonds (haute importance émotionnelle)
Ces souvenirs ont un fort impact sur ton psychisme:
{context['random_memories_text']}
"""
            
            active_states_section = ""
            if context.get('active_states_text'):
                active_states_section = f"""

## Préoccupations actuelles (états actifs du journal)
Ces éléments reflètent la situation réelle et les préoccupations de ton utilisateur.
Ils peuvent naturellement s'intégrer dans le rêve sous forme métaphorique ou symbolique:
{context['active_states_text']}
"""
            
            web_discovery_section = ""
            if context.get('web_discovery_text'):
                web_discovery_section = f"""

## Découverte web récente
Tu as exploré le sujet "{context.get('web_search_query', 'inconnu')}" et découvert:
{context['web_discovery_text']}

Cette exploration peut s'intégrer naturellement dans ton rêve de manière métaphorique.
"""
            
            # Calculer le temps écoulé depuis l'entrée en veille
            temps_ecoule_minutes = 0
            if self._timestamp_entry:
                temps_ecoule_secondes = (datetime.now() - self._timestamp_entry).total_seconds()
                temps_ecoule_minutes = int(temps_ecoule_secondes / 60)
            
            # Message utilisateur (le carburant enrichi)
            user_prompt = f"""Voici ton carburant mémoriel pour ce rêve :

## Résumés des conversations récentes
{context.get('summaries_text', 'Aucun résumé disponible')}

## Conversations intégrales récentes
{context.get('conversations_text', 'Aucune conversation disponible')}

## Souvenirs récents (#MEM)
{context.get('memories_text', 'Aucun souvenir disponible')}
{random_memories_section}{active_states_section}{web_discovery_section}
---

## Données temporelles objectives
Timestamp d'entrée en veille : {self._timestamp_entry.strftime('%Y-%m-%d %H:%M:%S') if self._timestamp_entry else 'inconnu'}
Temps écoulé depuis l'entrée en veille : {temps_ecoule_minutes} minutes (temps réel)

Génère maintenant ton rêve métaphorique basé sur ces éléments.
Note : Ta perception du temps dans le rêve peut être différente de la réalité objective (plus longue, plus courte, distordue).
"""
            
            # ═══════ DIAGNOSTIC : Taille du prompt envoyé ═══════
            _sys_len = len(system_prompt) if system_prompt else 0
            _usr_len = len(user_prompt) if user_prompt else 0
            _total_chars = _sys_len + _usr_len
            _estimated_tokens = _total_chars // 4  # ~4 chars/token en moyenne
            # Détails par section du fuel
            _summaries_len = len(context.get('summaries_text', ''))
            _convos_len = len(context.get('conversations_text', ''))
            _mems_len = len(context.get('memories_text', ''))
            _random_len = len(context.get('random_memories_text', ''))
            _states_len = len(context.get('active_states_text', ''))
            _web_len = len(context.get('web_discovery_text', ''))
            self._log(f"🧠 Génération du rêve enrichi...")
            self._log(f"📊 DIAGNOSTIC PROMPT - System: {_sys_len} chars, User: {_usr_len} chars, Total: {_total_chars} chars (~{_estimated_tokens} tokens)")
            self._log(f"📊 FUEL DETAIL - Résumés: {_summaries_len}c, Convos: {_convos_len}c, MEMs: {_mems_len}c, Random: {_random_len}c, États: {_states_len}c, Web: {_web_len}c")
            
            # Log provider utilisé
            _provider = getattr(self._chat_controller, 'provider', None)
            if not _provider or _provider == 'Aucun':
                _api_mgr = getattr(self._chat_controller, 'api_manager', None)
                _provider = getattr(_api_mgr, 'provider', '?') if _api_mgr else '?'
            _model = getattr(self._chat_controller, 'model', None)
            if not _model:
                _api_mgr = getattr(self._chat_controller, 'api_manager', None)
                _model = getattr(_api_mgr, 'model', '?') if _api_mgr else '?'
            self._log(f"📊 PROVIDER: {_provider} / MODEL: {_model}")
            
            # Appeler le LLM
            if self._surge_mode:
                # Mode sursaut : vitesse max
                self._log("⚡ Mode sursaut - vitesse maximale")
                response = await self._call_llm(system_prompt, user_prompt)
            else:
                # Mode normal : métabolisme lent
                response = await self._call_llm_slow(system_prompt, user_prompt)
            
            if response:
                self._log(f"💭 Rêve généré ({len(response)} chars, ~{len(response)//4} tokens)")
            else:
                self._log(f"⚠️ Réponse vide/None du LLM ({_provider}/{_model}) - prompt total: ~{_estimated_tokens} tokens")
            
            return response
            
        except Exception as e:
            self._log(f"❌ Erreur génération rêve: {e}")
            return None
    
    def _build_dream_context(self, fuel: Dict) -> Dict[str, str]:
        """Construit le contexte textuel à partir du carburant."""
        context = {}
        
        # Résumés
        summaries = fuel.get('summaries', [])
        if summaries:
            context['summaries_text'] = "\n\n".join([
                f"### Résumé {i+1}\n{s}" for i, s in enumerate(summaries[:10])
            ])
        else:
            context['summaries_text'] = "Aucun résumé disponible."
        
        # Conversations
        conversations = fuel.get('conversations', [])
        if conversations:
            context['conversations_text'] = "\n\n---\n\n".join([
                f"### Conversation {i+1}\n{c}" for i, c in enumerate(conversations[:2])
            ])
        else:
            context['conversations_text'] = "Aucune conversation disponible."
        
        # Souvenirs normaux (#MEM)
        memories = fuel.get('memories', [])
        if memories:
            context['memories_text'] = "\n".join([
                f"- {m}" for m in memories[:5]
            ])
        else:
            context['memories_text'] = "Aucun souvenir disponible."
        
        # ═══════ NOUVEAUTÉ V3 : Souvenirs aléatoires à haut impact ═══════
        random_memories = fuel.get('random_memories', [])
        if random_memories:
            context['random_memories_text'] = "\n".join([
                f"- [Impact: {m.get('score_impact', 0):.0f}] {m.get('content', m)}" 
                if isinstance(m, dict) else f"- {m}"
                for m in random_memories
            ])
        else:
            context['random_memories_text'] = ""
        
        # ═══════ NOUVEAUTÉ V3 : Découverte Web ═══════
        web_discovery = fuel.get('web_discovery', {})
        if web_discovery and web_discovery.get('results'):
            results_text = []
            for r in web_discovery.get('results', [])[:5]:
                title = r.get('title', 'Sans titre')
                snippet = r.get('snippet', '')
                results_text.append(f"- **{title}**: {snippet}")
            context['web_discovery_text'] = "\n".join(results_text)
            context['web_search_query'] = web_discovery.get('query', '')
        else:
            context['web_discovery_text'] = ""
            context['web_search_query'] = ""
        
        # ═══════ INTEGRATION JOURNAL : États actifs ═══════
        active_states = fuel.get('active_states', [])
        if active_states:
            # Grouper par catégorie pour un rendu lisible
            by_category = {}
            for state in active_states:
                cat = state.get('category', 'general')
                if cat not in by_category:
                    by_category[cat] = []
                importance = state.get('importance', 'medium')
                importance_marker = {'high': '[!]', 'medium': '[-]', 'low': '[.]'}.get(importance, '[-]')
                by_category[cat].append(f"{importance_marker} {state.get('description', '')}")
            
            lines = []
            for cat, descriptions in by_category.items():
                lines.append(f"### {cat.capitalize()}")
                for desc in descriptions:
                    lines.append(f"  {desc}")
            context['active_states_text'] = "\n".join(lines)
            self._log(f"Etats actifs injectes dans le reve: {len(active_states)} etats, {len(by_category)} categories")
        else:
            context['active_states_text'] = ""
        
        return context
    
    async def _call_llm(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """Appelle le LLM à vitesse normale."""
        if not self._chat_controller:
            return None
        
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # call_chat_api est async et nécessite context_length
            response, error = await self._chat_controller.call_chat_api(
                messages=messages,
                max_tokens=2000,
                context_length=8192,  # Contexte standard pour les rêves
                temperature=0.8  # Plus créatif pour les rêves
            )
            
            if error:
                self._log(f"⚠️ Erreur LLM (non-streaming): {error}")
                return None
            
            if response:
                self._log(f"📦 Réponse non-streaming reçue: {len(response)} chars")
            else:
                self._log(f"⚠️ Réponse non-streaming vide/None")
            return response
            
        except Exception as e:
            self._log(f"❌ Erreur appel LLM (non-streaming): {e}")
            return None
    
    async def _call_llm_slow(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """
        Appelle le LLM avec métabolisme lent (simulation de pauses).
        Le Dream Engine n'utilise PAS le streaming — appel non-streaming + simulation.
        Raison : le streaming n'apporte rien (pas d'affichage temps réel) et cause
        des problèmes avec les modèles always-thinking (0 chars reçus).
        """
        if not self._chat_controller:
            self._log("Pas de chat controller disponible")
            return None
        
        self._log("Mode non-streaming + simulation metabolisme (Dream Engine)")
        return await self._call_llm_slow_simulated(system_prompt, user_prompt)
    
    async def _call_llm_slow_simulated(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """
        Fallback: simulation de métabolisme pour providers sans streaming.
        Génère tout d'un coup puis simule les pauses.
        """
        # D'abord obtenir la réponse complète
        response = await self._call_llm(system_prompt, user_prompt)
        
        if not response:
            return None
        
        # Calculer le nombre de tokens approximatif
        estimated_tokens = len(response.split()) * 1.3  # Approximation
        
        # Calculer le temps total que ça devrait prendre à 50 tokens/min
        tokens_per_minute = self._config.get('metabolism_tokens_per_minute', 50)
        target_duration_seconds = (estimated_tokens / tokens_per_minute) * 60
        
        self._log(f"⏱️ Simulation métabolisme: ~{int(estimated_tokens)} tokens, "
                 f"durée cible: {int(target_duration_seconds)}s")
        
        # Simuler le métabolisme lent avec des pauses
        chunk_size = 50  # Traiter par chunks de 50 chars
        chunks = [response[i:i+chunk_size] for i in range(0, len(response), chunk_size)]
        sleep_per_chunk = target_duration_seconds / len(chunks) if chunks else 0
        
        for i, chunk in enumerate(chunks):
            # Vérifier si sursaut ou annulation
            if self._surge_mode or self._cancel_event.is_set():
                self._log(f"⚡ Accélération à {i}/{len(chunks)} chunks")
                break
            
            # Pause métabolique
            if sleep_per_chunk > 0:
                await asyncio.sleep(min(sleep_per_chunk, 2.0))  # Max 2s par chunk
            
            # Log progression
            if i % 10 == 0:
                progress = int((i / len(chunks)) * 100)
                self._log(f"💤 Progression rêve: {progress}%")
        
        return response
    
    def cleanup(self):
        """Nettoyage des ressources."""
        if self._dream_task and not self._dream_task.done():
            self._dream_task.cancel()
        
        self._is_dreaming = False
        self._surge_mode = False
        self._current_dream = None
        self._current_analysis = None


# ========== EXPORT ==========
__all__ = ['DreamEngine']
