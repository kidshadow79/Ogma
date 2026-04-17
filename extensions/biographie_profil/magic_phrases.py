"""
Gestionnaire des phrases magiques pour l'extension Biographie Profil
================================================================

Gère:
- Détection automatique des prénoms dans la conversation
- Injection automatique du Volume 1 lors de la première mention
- Phrases magiques IA pour consultation
- Phrases magiques utilisateur pour mise à jour
"""

import re
import json
from typing import Optional, Dict, List, Set
from pathlib import Path

class BiographyMagicPhrases:
    """Gestionnaire des phrases magiques et détection automatique biographie"""

    def __init__(self, biography_manager, archiviste_controller=None, status_queue=None):
        self.biography_manager = biography_manager
        self.archiviste_controller = archiviste_controller  # 🚀 NOUVEAU: Contrôleur Archiviste pour sélection
        self.status_queue = status_queue  # 🔔 NOUVEAU: Queue pour notifications frontend
        self.conversation_message_count = 0  # Compteur de messages pour détecter première interaction
        self.last_injection_message = -1  # Éviter les doubles injections sur le même message

        print("[BIOGRAPHY-MAGIC] ✅ Gestionnaire phrases magiques initialisé (lazy load activé)")

    def reset_conversation(self):
        """Reset le compteur pour une nouvelle conversation"""
        self.conversation_message_count = 0
        self.last_injection_message = -1
        print("[BIOGRAPHY-MAGIC] 🔄 Reset conversation - injection automatique réactivée")
    
    def _should_inject_biography(self, message: str, message_count: int) -> bool:
        """
        🚀 OPTIMISATION: Analyse intelligente si injection biographie nécessaire (lazy load)
        
        Règles (ORDRE DE PRIORITÉ):
        1. Présentation utilisateur avec biographie → INJECT (priorité haute)
        2. Messages simples (salutations sans présentation) → SKIP injection
        3. Questions personnelles → INJECT
        4. Contexte riche (>10 mots) → INJECT
        5. Mots-clés personnels après message 1 → INJECT
        
        Returns:
            True si injection nécessaire, False sinon
        """
        message_lower = message.lower().strip()
        
        # RÈGLE 1 (PRIORITÉ HAUTE): Présentation utilisateur avec biographie existante → INJECT
        # Pattern "c'est [prénom]", "c est [prénom]", "je suis [prénom]", "je m'appelle [prénom]"
        # ⚠️ VÉRIFIE que le prénom correspond à une biographie existante
        # Note: Accepte "c'est" et "c est" (avec ou sans apostrophe)
        presentation_patterns = [
            (r"\bc['']?est\s+([A-ZÀ-Ÿa-zà-ÿ]+)\b", "c'est"),  # c'est, c est, c'est (apostrophe typographique)
            (r"\bc\s+est\s+([A-ZÀ-Ÿa-zà-ÿ]+)\b", "c est"),    # "c est" avec espace
            (r"\bje\s+suis\s+([A-ZÀ-Ÿa-zà-ÿ]+)\b", "je suis"),
            (r"\bje\s+m['']?appelle\s+([A-ZÀ-Ÿa-zà-ÿ]+)\b", "je m'appelle")  # m'appelle ou m appelle
        ]
        
        # Récupérer la liste des utilisateurs avec biographie
        available_users = self.biography_manager.get_existing_users() if self.biography_manager else []
        available_users_lower = [u.lower() for u in available_users]
        
        for pattern, pattern_type in presentation_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                detected_name = match.group(1)
                # Vérifier si ce prénom a une biographie existante
                if detected_name.lower() in available_users_lower:
                    print(f"[BIO-LAZY] ✅ Présentation '{pattern_type} {detected_name}' détectée (biographie existante), injection requise")
                    return True
                else:
                    print(f"[BIO-LAZY] ⚪ Prénom '{detected_name}' sans biographie, skip injection")
                    # Continuer à chercher d'autres patterns
        
        # RÈGLE 2: Premier message simple (SANS présentation) → SKIP (économie 70% cas)
        if message_count == 1:
            # Messages simples courants
            simple_greetings = [
                "salut", "bonjour", "hello", "coucou", "hey", "hi",
                "ça va", "comment vas-tu", "quoi de neuf"
            ]
            
            # Vérifier si c'est un message simple (exact match ou court)
            if message_lower in simple_greetings or len(message.split()) <= 3:
                print(f"[BIO-LAZY] ⚪ Message simple '{message[:30]}...', skip injection (économie tokens)")
                return False
        
        # RÈGLE 3: Questions personnelles → INJECT (haute pertinence)
        personal_questions = [
            "qui suis-je", "qui es-tu", "qui est",
            "parle-moi de", "dis-moi qui", 
            "rappelle-toi", "souviens-toi",
            "notre histoire", "notre relation",
            "qu'est-ce que tu sais de"
        ]
        
        message_lower = message.lower()
        if any(pattern in message_lower for pattern in personal_questions):
            print(f"[BIO-LAZY] ✅ Question personnelle détectée, injection requise")
            return True
        
        # RÈGLE 4: Contexte riche (>10 mots) → INJECT (probablement pertinent)
        word_count = len(message.split())
        if word_count > 10:
            print(f"[BIO-LAZY] ✅ Contexte riche ({word_count} mots), injection requise")
            return True
        
        # RÈGLE 5: Mots-clés personnels basiques → INJECT seulement si message_count > 1
        # (évite double injection premier message si déjà traité par RÈGLE 1)
        if message_count > 1:
            personal_keywords_pattern = r'\b(moi|mon|ma|mes|je|j\')\b'
            if re.search(personal_keywords_pattern, message_lower):
                print(f"[BIO-LAZY] ✅ Mots-clés personnels détectés, injection requise")
                return True
        
        # Par défaut: SKIP (contexte non pertinent)
        print(f"[BIO-LAZY] ⚪ Contexte non pertinent, skip injection (économie tokens)")
        return False
    
    def _deduplicate_memories_with_history(self, memories: List[Dict], conversation_history: List[Dict]) -> List[Dict]:
        """
        🎯 DÉDUPLICATION: Filtre souvenirs déjà présents dans l'historique conversationnel
        
        Args:
            memories: Liste souvenirs biographiques à injecter
            conversation_history: Historique conversation [{role, content}, ...]
        
        Returns:
            Liste souvenirs NON redondants avec historique
        """
        if not conversation_history or len(conversation_history) < 2:
            # Pas d'historique significatif → garder tous les souvenirs
            print(f"[BIO-DEDUP] ⚪ Historique vide, aucune déduplication (garde {len(memories)} souvenirs)")
            return memories
        
        # Extraire texte complet de l'historique (derniers 10 messages)
        recent_history = conversation_history[-10:]
        history_text = " ".join([
            msg.get('content', '') 
            for msg in recent_history 
            if isinstance(msg.get('content'), str)
        ]).lower()
        
        if not history_text.strip():
            print(f"[BIO-DEDUP] ⚪ Historique sans texte, garde {len(memories)} souvenirs")
            return memories
        
        # Filtrer souvenirs dont le contenu est déjà largement présent dans l'historique
        deduplicated = []
        removed_count = 0
        
        for memory in memories:
            memory_content = memory.get('content', '').lower()
            
            if not memory_content:
                continue
            
            # Extraire mots significatifs du souvenir (>3 chars, pas stopwords)
            words = [w for w in re.findall(r'\b\w{4,}\b', memory_content) if w not in ['avec', 'pour', 'dans', 'cette', 'sont', 'plus']]
            
            if not words:
                deduplicated.append(memory)
                continue
            
            # Calculer taux de présence dans historique
            words_in_history = sum(1 for w in words if w in history_text)
            presence_rate = words_in_history / len(words) if words else 0
            
            # SEUIL: >70% mots présents = redondant
            if presence_rate > 0.7:
                removed_count += 1
                print(f"[BIO-DEDUP] 🗑️ Souvenir redondant ({presence_rate*100:.0f}% présence): '{memory_content[:50]}...'")
            else:
                deduplicated.append(memory)
        
        print(f"[BIO-DEDUP] ✅ Déduplication: {len(memories)} → {len(deduplicated)} souvenirs ({removed_count} redondants supprimés)")
        
        return deduplicated

    async def handle_magic_phrases(self, user_input: str, is_ai_message: bool = False, conversation_history: List[Dict] = None) -> Optional[Dict]:
        """
        Détecte et traite les phrases magiques de biographie

        Args:
            user_input: Texte du message (utilisateur ou IA)
            is_ai_message: True si c'est un message de l'IA (pour détection auto)
            conversation_history: Historique conversation pour déduplication (NOUVEAU)

        Returns:
            Dict avec 'content' et 'type' ('display' ou 'inject') ou None
        """
        try:
            print(f"[BIOGRAPHY-MAGIC] 🔍 Analyse message: '{user_input[:50]}...'")

            # 1. PHRASES MAGIQUES IA (consultation explicite)
            if is_ai_message:
                luna_response = self._handle_luna_magic_phrases(user_input)
                if luna_response:
                    return {'content': luna_response, 'type': 'display'}

            # 2. PHRASES MAGIQUES UTILISATEUR (mise à jour)
            if not is_ai_message:
                user_response = await self._handle_user_magic_phrases(user_input)
                if user_response:
                    return {'content': user_response, 'type': 'display'}

            # 3. DÉTECTION AUTOMATIQUE PRÉNOMS (injection première fois)
            if not is_ai_message:  # Seulement sur messages utilisateur
                auto_injection = await self._handle_auto_detection(user_input, conversation_history or [])
                if auto_injection:
                    return {'content': auto_injection, 'type': 'inject'}
            return None

        except Exception as e:
            print(f"[BIOGRAPHY-MAGIC] ❌ Erreur traitement phrases magiques: {e}")
            return None

    def _handle_luna_magic_phrases(self, message: str) -> Optional[str]:
        """Gère les phrases magiques de l'IA pour consultation biographie"""

        # Pattern: "il faut que je consulte la biographie de [prénom]"
        consultation_pattern = r"il\s+faut\s+que\s+je\s+consulte\s+la\s+biographie\s+de\s+([a-zA-ZÀ-ÿ]+)"

        match = re.search(consultation_pattern, message, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            print(f"[BIOGRAPHY-MAGIC] 🎯 IA principale demande consultation biographie: {name}")

            # Charger la biographie Volume 1
            biography_data = self.biography_manager.load_volume1_memories(name)

            if biography_data:
                formatted_content = self._format_volume1_for_ai(biography_data)
                print(f"[BIOGRAPHY-MAGIC] ✅ Biographie {name} fournie à l'IA principale")
                return formatted_content
            else:
                print(f"[BIOGRAPHY-MAGIC] ❌ Aucune biographie trouvée pour {name}")
                return f"[BIOGRAPHY] Aucune biographie trouvée pour {name}. Utilisez le bouton 🔄 pour traiter les souvenirs existants."

        return None

    async def _handle_user_magic_phrases(self, message: str) -> Optional[str]:
        """Gère les phrases magiques utilisateur pour mise à jour biographie"""

        # Patterns pour mise à jour Volume 2
        update_patterns = [
            r"complète\s+ma\s+biographie",
            r"complète\s+ma\s+bio",
            r"met\s+à\s+jour\s+ma\s+biographie",
            r"enrichis\s+mon\s+profil"
        ]

        for pattern in update_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                print(f"[BIOGRAPHY-MAGIC] 📝 Demande mise à jour biographie utilisateur")

                # Détecter le nom de l'utilisateur dans la conversation
                user_name = await self._detect_current_user()

                if not user_name:
                    return "[BIOGRAPHY] ⚠️ Impossible de détecter votre nom. Présentez-vous d'abord (ex: 'Salut c'est [votre nom]')."

                return f"[BIOGRAPHY] ℹ️ Pour mettre à jour votre biographie, utilisez les boutons 🧠 Phase 1 et 📖 Phase 2 dans les paramètres de l'extension Biographie (bouton ✒️ en haut)."
        return None

    async def _detect_current_user(self) -> Optional[str]:
        """
        Détecte le nom de l'utilisateur actuel depuis l'historique récent
        AMÉLIORATION: Analyse les derniers messages utilisateur pour trouver le nom
        """
        try:
            # 1. Analyser les derniers messages de la conversation actuelle
            def _get_ogma():
                import ogma_ng
                return ogma_ng
            
            chat_history = _get_ogma()._chat_history if hasattr(_get_ogma(), '_chat_history') else []

            if chat_history:
                # Chercher prénoms dans les 15 derniers messages utilisateur
                recent_user_messages = [
                    msg for msg in chat_history[-30:]  # 30 derniers messages au total
                    if msg.get('role') == 'user'
                ][-15:]  # Garder 15 derniers messages utilisateur

                print(f"[BIOGRAPHY-MAGIC] 🔍 Analyse {len(recent_user_messages)} messages utilisateur récents")

                # Compter occurrences de chaque nom détecté
                name_counts = {}
                for msg in reversed(recent_user_messages):  # Du plus récent au plus ancien
                    content = msg.get('content', '')
                    detected_names = self.biography_manager.detect_user_names(content)

                    for name in detected_names:
                        # Vérifier si ce nom a une biographie existante
                        if self.biography_manager.load_volume1_memories(name):
                            name_counts[name] = name_counts.get(name, 0) + 1

                # Retourner le nom le plus fréquent parmi ceux avec biographie
                if name_counts:
                    most_frequent = max(name_counts.items(), key=lambda x: x[1])
                    detected_user = most_frequent[0]
                    print(f"[BIOGRAPHY-MAGIC] 👤 Utilisateur détecté: {detected_user} ({most_frequent[1]} mentions)")
                    return detected_user

            # 2. Fallback: Utiliser l'utilisateur connecté (session)
            try:
                import ogma_ng
                current_user = ogma_ng._current_user_name if hasattr(ogma_ng, '_current_user_name') else None
                
                if current_user:
                    # Vérifier si l'utilisateur connecté a une biographie
                    if current_user.lower() in [u.lower() for u in users]:
                        print(f"[BIOGRAPHY-MAGIC] 👤 Utilisateur détecté (session): {current_user}")
                        return current_user
                    else:
                        print(f"[BIOGRAPHY-MAGIC] ⚠️ Utilisateur connecté '{current_user}' sans biographie")
            except Exception as e:
                print(f"[BIOGRAPHY-MAGIC] ❌ Erreur récupération session utilisateur: {e}")

            # 3. Dernier recours: Premier utilisateur alphabétique (ancien comportement)
            if users:
                detected_user = users[0]
                print(f"[BIOGRAPHY-MAGIC] 👤 Utilisateur détecté (fallback alphabétique): {detected_user}")
                return detected_user

            return None

        except Exception as e:
            print(f"[BIOGRAPHY-MAGIC] ❌ Erreur détection utilisateur: {e}")
            return None

    def _get_profile_identities(self) -> Dict[str, str]:
        """Récupère les identités du profil actuel"""
        try:
            from identity_manager import get_identity_manager
            identity_manager = get_identity_manager()
            current_identity = identity_manager.get_current_identity()
            return {
                'user_name': current_identity.get('user_name', ''),
                'ai_name': current_identity.get('ai_name', '')
            }
        except Exception as e:
            print(f"[BIOGRAPHY-MAGIC] ❌ Erreur récupération identités: {e}")
            return {'user_name': '', 'ai_name': ''}

    def _select_target_user_intelligent(self, message: str, available_users: List[str], 
                                      detected_names: List[str], has_personal_keywords: bool) -> Optional[str]:
        """Sélectionne intelligemment l'utilisateur cible selon le profil"""
        profile_identities = self._get_profile_identities()
        
        for user_name in available_users:
            # RÈGLE IA : Seulement si mentionnée explicitement
            if user_name.lower() == profile_identities['ai_name'].lower():
                if user_name in detected_names:
                    print(f"[BIOGRAPHY-MAGIC] 🤖 IA {user_name} mentionnée explicitement")
                    return user_name
                else:
                    print(f"[BIOGRAPHY-MAGIC] ⚪ IA {user_name} ignorée (pas de mention explicite)")
                    continue
            
            # RÈGLE UTILISATEUR : Mots-clés personnels OU son propre nom
            elif user_name.lower() == profile_identities['user_name'].lower():
                if has_personal_keywords or user_name in detected_names:
                    trigger_type = "nom explicite" if user_name in detected_names else "mots-clés personnels"
                    print(f"[BIOGRAPHY-MAGIC] 👤 Utilisateur {user_name} sélectionné ({trigger_type})")
                    return user_name
        
        return None

    async def _handle_auto_detection(self, message: str, conversation_history: List[Dict]) -> Optional[str]:
        """Détection automatique : première interaction OU mots-clés personnels intelligents"""
        
        # Incrémenter le compteur de messages
        self.conversation_message_count += 1
        
        # 🚀 OPTIMISATION LAZY LOAD: Analyser pertinence AVANT injection
        if not self._should_inject_biography(message, self.conversation_message_count):
            # Message non pertinent → skip injection (économie tokens + performance)
            return None
        
        # Éviter double injection sur le même message
        if self.last_injection_message == self.conversation_message_count:
            return None
        
        # Détecter les utilisateurs avec biographie existante
        available_users = self.biography_manager.get_existing_users()
        if not available_users:
            return None
        
        # TRIGGER 1: Première interaction de la conversation (PRIORITAIRE)
        if self.conversation_message_count == 1:
            # 🔧 FIX MULTI-USER: Utiliser l'utilisateur connecté (_current_user_name) au lieu du premier alphabétique
            # Récupérer le nom de l'utilisateur connecté
            try:
                import ogma_ng
                current_user = ogma_ng._current_user_name if hasattr(ogma_ng, '_current_user_name') else None
                
                # Vérifier si l'utilisateur connecté a une biographie
                if current_user and current_user.lower() in [u.lower() for u in available_users]:
                    user_name = current_user
                    print(f"[BIOGRAPHY-MAGIC] 👤 Utilisateur connecté détecté: {user_name}")
                else:
                    # Fallback si pas de session utilisateur ou pas de biographie
                    print(f"[BIOGRAPHY-MAGIC] ⚠️ Utilisateur connecté '{current_user}' sans biographie, skip injection")
                    return None
            except Exception as e:
                print(f"[BIOGRAPHY-MAGIC] ❌ Erreur récupération utilisateur connecté: {e}")
                return None
            
            # 🚀 INJECTION CIBLÉE ARCHIVISTE OBLIGATOIRE (pas de fallback)
            if not self.archiviste_controller:
                error_msg = "⚠️ Absence de subconscience (Archiviste) - Injection biographie impossible"
                print(f"[BIOGRAPHY-MAGIC] ❌ ARCHIVISTE REQUIS: Pas d'injection sans Archiviste (première interaction)")
                
                # Notification frontend
                if self.status_queue:
                    self.status_queue.put(error_msg)
                
                return None
            
            selected_memories = await self.biography_manager.select_memories_archiviste(
                user_name, message, self.archiviste_controller, max_memories=10
            )
            
            if selected_memories:
                # 🎯 DÉDUPLICATION avec historique (premier message = historique vide, donc pas de filtrage)
                deduplicated_memories = self._deduplicate_memories_with_history(selected_memories, conversation_history)
                
                if deduplicated_memories:
                    print(f"[BIOGRAPHY-MAGIC] 🎯 INJECTION AUTO: Première interaction détectée (Archiviste)")
                    self.last_injection_message = self.conversation_message_count
                    formatted_content = self._format_selected_memories(
                        user_name, deduplicated_memories, trigger_type="première_interaction"
                    )
                    print(f"[BIOGRAPHY-MAGIC] ✅ Biographie {user_name} injectée (première interaction, {len(deduplicated_memories)} souvenirs après dédup)")
                    return formatted_content
                else:
                    print(f"[BIOGRAPHY-MAGIC] ⚠️ Tous les souvenirs étaient redondants avec historique")
                    return None
            else:
                print(f"[BIOGRAPHY-MAGIC] ⚠️ Archiviste n'a sélectionné aucun souvenir")
                return None
        
        # TRIGGER 2: Logique intelligente basée sur le profil (SEULEMENT si pas première interaction)
        # Vérifier qu'aucune injection n'a déjà eu lieu sur ce message
        if self.last_injection_message == self.conversation_message_count:
            print(f"[BIOGRAPHY-MAGIC] ⚪ Injection déjà effectuée sur ce message, TRIGGER 2 ignoré")
            return None
        
        # Détecter les noms mentionnés dans le message
        detected_names = self.biography_manager.detect_user_names(message)
        
        # Mots-clés personnels (sans les noms d'utilisateurs - logique séparée)
        personal_keywords = [
            r"\bmoi\b",
            r"\bje\b", r"\bj'\b",
            r"\bmon\b", r"\bma\b", r"\bmes\b",
            r"\bnotre\b", r"\bnos\b"
        ]
        
        # Vérifier si le message contient des mots-clés personnels
        has_personal_keywords = any(re.search(pattern, message, re.IGNORECASE) for pattern in personal_keywords)
        
        # Utiliser la sélection intelligente basée sur le profil
        target_user = self._select_target_user_intelligent(message, available_users, detected_names, has_personal_keywords)
        
        if target_user:
            # Déterminer le type de déclenchement
            if target_user in detected_names:
                trigger_type = "mention_explicite"
                print(f"[BIOGRAPHY-MAGIC] 🎯 INJECTION AUTO: Mention explicite détectée")
            else:
                trigger_type = "mots_clés_personnels" 
                print(f"[BIOGRAPHY-MAGIC] 🎯 INJECTION AUTO: Mots-clés personnels détectés")
            
            # 🚀 INJECTION CIBLÉE ARCHIVISTE OBLIGATOIRE (pas de fallback)
            if not self.archiviste_controller:
                error_msg = "⚠️ Absence de subconscience (Archiviste) - Injection biographie impossible"
                print(f"[BIOGRAPHY-MAGIC] ❌ ARCHIVISTE REQUIS: Pas d'injection sans Archiviste ({trigger_type})")
                
                # Notification frontend
                if self.status_queue:
                    self.status_queue.put(error_msg)
                
                return None
            
            selected_memories = await self.biography_manager.select_memories_archiviste(
                target_user, message, self.archiviste_controller, max_memories=10
            )
            
            if selected_memories:
                # 🎯 DÉDUPLICATION avec historique (TRIGGER 2 aussi)
                deduplicated_memories = self._deduplicate_memories_with_history(selected_memories, conversation_history)
                
                if deduplicated_memories:
                    self.last_injection_message = self.conversation_message_count
                    formatted_content = self._format_selected_memories(
                        target_user, deduplicated_memories, trigger_type=trigger_type
                    )
                    print(f"[BIOGRAPHY-MAGIC] ✅ Biographie {target_user} injectée ({trigger_type}, {len(deduplicated_memories)} souvenirs après dédup)")
                    return formatted_content
                else:
                    print(f"[BIOGRAPHY-MAGIC] ⚠️ Tous les souvenirs redondants avec historique pour {trigger_type}")
                    return None
            else:
                print(f"[BIOGRAPHY-MAGIC] ⚠️ Archiviste n'a sélectionné aucun souvenir pour {trigger_type}")
                return None
        
        return None

    def _format_volume1_for_ai(self, biography_data: Dict, trigger_type: str = "consultation") -> str:
        """Formate les données biographiques Volume 1 pour l'IA"""

        user_name = biography_data.get('user_name', 'Utilisateur')
        total_memories = biography_data.get('total_memories', 0)
        memories = biography_data.get('memories', [])
        created_at = biography_data.get('created_at', 'Date inconnue')

        # Header différent selon contexte
        if trigger_type in ["première_interaction", "mots_clés_personnels", "mention_explicite"]:
            header = f"[BIOGRAPHIE AUTO-INJECTION] Profil de {user_name}"
        else:
            header = f"[BIOGRAPHIE CONSULTATION] Profil de {user_name}"

        # Construction du contenu formaté
        content_lines = [
            header,
            "=" * len(header),
            f"📊 {total_memories} souvenirs classés",
            f"📅 Dernière mise à jour: {created_at[:10]}",
            "",
            "📖 VOLUME 1 - SOUVENIRS PERTINENTS:",
            ""
        ]

        # Ajouter les souvenirs (limiter à 10 pour ne pas surcharger)
        displayed_memories = memories[:10]

        for i, memory in enumerate(displayed_memories, 1):
            memory_summary = memory.get('summary', memory.get('content', 'Contenu non disponible'))
            # Limiter chaque souvenir à 150 caractères
            if len(memory_summary) > 150:
                memory_summary = memory_summary[:147] + "..."

            content_lines.append(f"{i}. {memory_summary}")

        if len(memories) > 10:
            content_lines.append(f"... et {len(memories) - 10} autres souvenirs")

        content_lines.extend([
            "",
            f"💡 Utilisez ces informations pour personnaliser vos interactions avec {user_name}.",
        ])

        if trigger_type == "première_interaction":
            content_lines.append("🔄 Cette biographie sera ré-injectée automatiquement si vous utilisez des mots-clés personnels (moi, je, mon, ma, etc.).")
        elif trigger_type == "mots_clés_personnels":
            content_lines.append("🔄 Biographie injectée suite à l'utilisation de mots-clés personnels.")
        elif trigger_type == "mention_explicite":
            content_lines.append("🔄 Biographie injectée suite à mention explicite du nom.")

        return "\n".join(content_lines)
    
    def _format_selected_memories(self, user_name: str, selected_memories: List[Dict], 
                                  trigger_type: str = "consultation") -> str:
        """
        🚀 NOUVEAU: Formate souvenirs sélectionnés par Archiviste (textes intégraux)
        
        Args:
            user_name: Nom utilisateur
            selected_memories: Liste souvenirs sélectionnés (3-10)
            trigger_type: Type déclenchement (première_interaction, mots_clés_personnels, mention_explicite)
        
        Returns:
            Texte formaté injection
        """
        # Header différent selon contexte
        if trigger_type in ["première_interaction", "mots_clés_personnels", "mention_explicite"]:
            header = f"[BIOGRAPHIE AUTO-INJECTION] Profil de {user_name}"
        else:
            header = f"[BIOGRAPHIE CONSULTATION] Profil de {user_name}"
        
        # Construction du contenu formaté
        content_lines = [
            header,
            "=" * len(header),
            f"📊 {len(selected_memories)} souvenirs pertinents sélectionnés",
            "",
            "📖 VOLUME 1 - SOUVENIRS PERTINENTS:",
            ""
        ]
        
        # Ajouter souvenirs TEXTES INTÉGRAUX (vs résumés 150 chars)
        for i, memory in enumerate(selected_memories, 1):
            memory_content = memory.get('content', 'Contenu non disponible')
            # CHANGEMENT: Texte intégral sans limitation (vs 150 chars avant)
            content_lines.append(f"{i}. {memory_content}")
        
        content_lines.extend([
            "",
            f"💡 Utilisez ces informations pour personnaliser vos interactions avec {user_name}.",
        ])
        
        if trigger_type == "première_interaction":
            content_lines.append("🔄 Cette biographie sera ré-injectée automatiquement si vous utilisez des mots-clés personnels (moi, je, mon, ma, etc.).")
        elif trigger_type == "mots_clés_personnels":
            content_lines.append("🔄 Biographie injectée suite à l'utilisation de mots-clés personnels.")
        elif trigger_type == "mention_explicite":
            content_lines.append("🔄 Biographie injectée suite à mention explicite du nom.")
        
        return "\n".join(content_lines)

    def get_existing_biographies(self) -> List[str]:
        """Retourne la liste des noms ayant des biographies"""
        return self.biography_manager.get_existing_users()