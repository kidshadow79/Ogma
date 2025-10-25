"""
Gestionnaire des phrases magiques pour l'extension Biographie Profil
================================================================

Gère:
- Détection automatique des prénoms dans la conversation
- Injection automatique du Volume 1 lors de la première mention
- Phrases magiques Luna pour consultation
- Phrases magiques utilisateur pour mise à jour
"""

import re
import json
from typing import Optional, Dict, List, Set
from pathlib import Path

class BiographyMagicPhrases:
    """Gestionnaire des phrases magiques et détection automatique biographie"""

    def __init__(self, biography_manager):
        self.biography_manager = biography_manager
        self.conversation_message_count = 0  # Compteur de messages pour détecter première interaction
        self.last_injection_message = -1  # Éviter les doubles injections sur le même message

        print("[BIOGRAPHY-MAGIC] ✅ Gestionnaire phrases magiques initialisé")

    def reset_conversation(self):
        """Reset le compteur pour une nouvelle conversation"""
        self.conversation_message_count = 0
        self.last_injection_message = -1
        print("[BIOGRAPHY-MAGIC] 🔄 Reset conversation - injection automatique réactivée")

    async def handle_magic_phrases(self, user_input: str, is_ai_message: bool = False) -> Optional[Dict]:
        """
        Détecte et traite les phrases magiques de biographie

        Args:
            user_input: Texte du message (utilisateur ou IA)
            is_ai_message: True si c'est un message de l'IA (pour détection auto)

        Returns:
            Dict avec 'content' et 'type' ('display' ou 'inject') ou None
        """
        try:
            print(f"[BIOGRAPHY-MAGIC] 🔍 Analyse message: '{user_input[:50]}...'")

            # 1. PHRASES MAGIQUES LUNA (consultation explicite)
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
                auto_injection = self._handle_auto_detection(user_input)
                if auto_injection:
                    return {'content': auto_injection, 'type': 'inject'}
            return None

        except Exception as e:
            print(f"[BIOGRAPHY-MAGIC] ❌ Erreur traitement phrases magiques: {e}")
            return None

    def _handle_luna_magic_phrases(self, message: str) -> Optional[str]:
        """Gère les phrases magiques de Luna pour consultation biographie"""

        # Pattern: "il faut que je consulte la biographie de [prénom]"
        consultation_pattern = r"il\s+faut\s+que\s+je\s+consulte\s+la\s+biographie\s+de\s+([a-zA-ZÀ-ÿ]+)"

        match = re.search(consultation_pattern, message, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            print(f"[BIOGRAPHY-MAGIC] 🎯 Luna demande consultation biographie: {name}")

            # Charger la biographie Volume 1
            biography_data = self.biography_manager.load_volume1_memories(name)

            if biography_data:
                formatted_content = self._format_volume1_for_ai(biography_data)
                print(f"[BIOGRAPHY-MAGIC] ✅ Biographie {name} fournie à Luna")
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

                # Créer le Volume 2
                volume2_path = await self.biography_manager.create_volume2_narrative(user_name)

                if volume2_path:
                    return f"[BIOGRAPHY] ✅ **Volume 2 créé avec succès !**\n\n📖 Votre biographie narrative complète a été générée et sauvegardée dans:\n`{volume2_path}`\n\n💡 Cette analyse psychologique approfondie contient votre portrait narratif, vos patterns relationnels et votre évolution personnelle."
                else:
                    return f"[BIOGRAPHY] ❌ Erreur lors de la création du Volume 2 pour {user_name}. Vérifiez que le Volume 1 existe (utilisez le bouton de traitement des souvenirs d'abord)."
        return None

    async def _detect_current_user(self) -> Optional[str]:
        """
        Détecte le nom de l'utilisateur actuel depuis l'historique récent
        AMÉLIORATION: Analyse les derniers messages utilisateur pour trouver le nom
        """
        try:
            # 1. Analyser les derniers messages de la conversation actuelle
            import ogma_ng
            chat_history = getattr(ogma_ng, '_chat_history', [])

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

            # 2. Fallback: Retourner premier utilisateur alphabétique avec biographie
            users = self.biography_manager.get_existing_users()
            if users:
                detected_user = users[0]
                print(f"[BIOGRAPHY-MAGIC] 👤 Utilisateur détecté (fallback): {detected_user}")
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

    def _handle_auto_detection(self, message: str) -> Optional[str]:
        """Détection automatique : première interaction OU mots-clés personnels intelligents"""
        
        # Incrémenter le compteur de messages
        self.conversation_message_count += 1
        
        # Éviter double injection sur le même message
        if self.last_injection_message == self.conversation_message_count:
            return None
        
        # Détecter les utilisateurs avec biographie existante
        available_users = self.biography_manager.get_existing_users()
        if not available_users:
            return None
        
        # TRIGGER 1: Première interaction de la conversation (PRIORITAIRE)
        if self.conversation_message_count == 1:
            # Prendre le premier utilisateur disponible (logique générique)
            user_name = available_users[0]
            biography_data = self.biography_manager.load_volume1_memories(user_name)
            
            if biography_data:
                print(f"[BIOGRAPHY-MAGIC] 🎯 INJECTION AUTO: Première interaction détectée")
                self.last_injection_message = self.conversation_message_count
                formatted_content = self._format_volume1_for_ai(biography_data, trigger_type="première_interaction")
                print(f"[BIOGRAPHY-MAGIC] ✅ Biographie {user_name} injectée (première interaction)")
                return formatted_content
        
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
            biography_data = self.biography_manager.load_volume1_memories(target_user)
            
            if biography_data:
                # Déterminer le type de déclenchement pour le formatage
                if target_user in detected_names:
                    trigger_type = "mention_explicite"
                    print(f"[BIOGRAPHY-MAGIC] 🎯 INJECTION AUTO: Mention explicite détectée")
                else:
                    trigger_type = "mots_clés_personnels" 
                    print(f"[BIOGRAPHY-MAGIC] 🎯 INJECTION AUTO: Mots-clés personnels détectés")
                
                self.last_injection_message = self.conversation_message_count
                formatted_content = self._format_volume1_for_ai(biography_data, trigger_type=trigger_type)
                print(f"[BIOGRAPHY-MAGIC] ✅ Biographie {target_user} injectée ({trigger_type})")
                return formatted_content
        
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

    def get_existing_biographies(self) -> List[str]:
        """Retourne la liste des noms ayant des biographies"""
        return self.biography_manager.get_existing_users()