"""
OGMA Telegram Connector - Message Bridge
Pont entre les messages Telegram et le coeur OGMA
"""

import asyncio
import json
import re
from datetime import datetime
from typing import Optional, Dict, Any, Callable, List, Tuple
from pathlib import Path

from .config import get_telegram_config
from .media_handler import get_media_handler


class TelegramMessageBridge:
    """
    Pont de communication entre Telegram et OGMA.
    Reçoit les messages Telegram et les injecte dans OGMA,
    puis renvoie les réponses vers Telegram.
    """
    
    def __init__(self):
        self.config = get_telegram_config()
        self.media_handler = get_media_handler()
        
        # Contrôleurs OGMA (injectés depuis ogma_ng.py)
        self._chat_controller = None
        self._archiviste_controller = None
        self._memory_manager = None
        self._settings_manager = None
        self._text2img_manager = None
        self._web_navigator = None  # Extension Web Navigator pour recherches internet
        
        # Historique de conversation pour contexte
        self._telegram_history: List[Dict[str, str]] = []
        self._max_history = 20
        
        # Callbacks pour les fonctionnalités avancées
        self._on_response_callback: Optional[Callable] = None
        self._on_image_generated_callback: Optional[Callable] = None
        
        # État
        self._is_processing = False
        self._last_user_id: Optional[int] = None
        self._pending_image_base64: Optional[str] = None  # Image en attente pour i2i
        
        print("[TELEGRAM-BRIDGE] ✅ Bridge initialisé")
    
    # === Configuration des contrôleurs OGMA ===
    
    def set_chat_controller(self, controller) -> None:
        """Configure le contrôleur de chat OGMA"""
        self._chat_controller = controller
        print("[TELEGRAM-BRIDGE] ✅ Chat controller connecté")
    
    def set_archiviste_controller(self, controller) -> None:
        """Configure le contrôleur Archiviste"""
        self._archiviste_controller = controller
        print("[TELEGRAM-BRIDGE] ✅ Archiviste controller connecté")
    
    def set_memory_manager(self, manager) -> None:
        """Configure le gestionnaire de mémoire"""
        self._memory_manager = manager
        self.media_handler.set_stt_callback(self._transcribe_audio)
        print("[TELEGRAM-BRIDGE] ✅ Memory manager connecté")
    
    def set_settings_manager(self, manager) -> None:
        """Configure le gestionnaire de paramètres"""
        self._settings_manager = manager
        print("[TELEGRAM-BRIDGE] ✅ Settings manager connecté")
    
    def set_audio_manager(self, manager) -> None:
        """Configure le gestionnaire audio"""
        self.media_handler.set_audio_manager(manager)
    
    def set_text2img_manager(self, manager) -> None:
        """Configure le gestionnaire de génération d'images"""
        self._text2img_manager = manager
        print("[TELEGRAM-BRIDGE] ✅ Text2Img manager connecté")
    
    def set_web_navigator(self, web_nav) -> None:
        """Configure l'extension Web Navigator pour les recherches internet"""
        self._web_navigator = web_nav
        print("[TELEGRAM-BRIDGE] Web Navigator connecté")
    
    async def _enrich_text_with_web_context(self, user_text: str) -> str:
        """
        Enrichit le texte utilisateur avec le contexte web si une recherche est demandée.
        
        Args:
            user_text: Message original de l'utilisateur
            
        Returns:
            Texte enrichi avec le contexte web (ou texte original si pas de recherche)
        """
        if not self._web_navigator:
            return user_text
        
        try:
            # Vérifier si l'utilisateur demande une recherche internet
            if not self._web_navigator.commands.is_internet_request(user_text):
                return user_text
            
            # Vérifier que la recherche web est activée
            if not self._web_navigator.config.is_web_search_enabled():
                print("[TELEGRAM-BRIDGE] Recherche web desactivee")
                return user_text
            
            print(f"[TELEGRAM-BRIDGE] Recherche web detectee dans la requete utilisateur")
            
            # Effectuer la recherche
            web_response, _ = await self._web_navigator.commands.process_internet_request(user_text)
            
            if web_response:
                print(f"[TELEGRAM-BRIDGE] Contexte web recupere: {len(web_response)} caracteres")
                # Enrichir le texte avec le contexte web
                enriched_text = f"{user_text}\n\n[CONTEXTE WEB RÉCENT]\n{web_response}"
                return enriched_text
            else:
                print(f"[TELEGRAM-BRIDGE] Pas de resultats web")
                
        except Exception as e:
            print(f"[TELEGRAM-BRIDGE] Erreur enrichissement web: {e}")
        
        return user_text
    
    # === Traitement des messages ===
    
    async def process_text_message(
        self, 
        text: str, 
        user_id: int, 
        username: str = "Telegram User"
    ) -> Tuple[str, Optional[str]]:
        """
        Traite un message texte depuis Telegram.
        
        Args:
            text: Le message de l'utilisateur
            user_id: ID Telegram de l'utilisateur
            username: Nom d'utilisateur
            
        Returns:
            (response_text, image_path) - réponse + chemin image si générée
        """
        if self._is_processing:
            return "Je suis en train de réfléchir à une autre question... un instant ! 🧠", None
        
        self._is_processing = True
        self._last_user_id = user_id
        
        try:
            print(f"[TELEGRAM-BRIDGE] Message de {username} ({user_id}): {text[:50]}...")
            
            # Enrichir le contexte avec une recherche web si demandée par l'utilisateur
            enriched_text = await self._enrich_text_with_web_context(text)
            
            # Ajouter le message user à l'historique AVANT l'appel IA
            # (pour qu'il soit disponible dans external_history si besoin)
            self._add_to_history("user", text)

            # Utiliser l'API externe OGMA pour bénéficier du contexte complet
            # (ego, mémoire, temporal guardian, journal, rêves, etc.)
            try:
                from ogma_ng import process_external_message
                # Passer l'historique sans le dernier message user (déjà ajouté par process_external_message)
                history_to_pass = self._telegram_history[:-1] if self._telegram_history else []
                response, ai_memorized = await process_external_message(
                    user_text=enriched_text,
                    source="telegram",
                    user_name=username,
                    include_memories=True,
                    save_memories=True,
                    external_history=history_to_pass
                )
                
                if ai_memorized:
                    print(f"[TELEGRAM-BRIDGE] Souvenir mémorisé via Telegram")
                    
            except ImportError:
                print("[TELEGRAM-BRIDGE] Fallback: ogma_ng.process_external_message non disponible")
                # Fallback: utiliser l'ancien système si ogma_ng n'est pas accessible
                if not self._chat_controller:
                    self._telegram_history.pop()  # Retirer le user ajouté en avance
                    return "OGMA n'est pas encore prêt. Réessaie dans quelques secondes.", None
                context_messages = await self._build_context_messages(enriched_text, username)
                response = await self._call_ogma_chat(context_messages)
            
            if not response:
                self._telegram_history.pop()  # Retirer le user ajouté si pas de réponse
                return "Je n'ai pas pu générer de réponse. Réessaie ! 🤔", None
            
            # Traiter la recherche web auto-déclenchée par l'IA (régénération si nécessaire)
            response = await self._process_ai_web_search(response, [{"role": "user", "content": text}])
            
            # Ajouter la réponse à l'historique (user déjà ajouté avant l'appel)
            self._add_to_history("assistant", response)
            
            # Traiter la génération d'image si phrase magique détectée
            image_path = await self._process_image_generation(response)
            
            # Nettoyer la réponse pour Telegram (retirer les balises HTML d'images)
            clean_response = self._clean_response_for_telegram(response)
            
            print(f"[TELEGRAM-BRIDGE] Réponse: {clean_response[:50]}...")
            
            return clean_response, image_path
            
        except Exception as e:
            print(f"[TELEGRAM-BRIDGE] Erreur traitement: {e}")
            import traceback
            traceback.print_exc()
            return f"Une erreur s'est produite: {str(e)[:100]}", None
        finally:
            self._is_processing = False
    
    async def process_image_message(
        self,
        image_bytes: bytes,
        caption: Optional[str],
        user_id: int,
        username: str = "Telegram User"
    ) -> Tuple[str, Optional[str]]:
        """
        Traite une image reçue depuis Telegram.
        
        Args:
            image_bytes: Les bytes de l'image
            caption: Légende optionnelle
            user_id: ID Telegram
            username: Nom d'utilisateur
            
        Returns:
            (response_text, image_path)
        """
        if self._is_processing:
            return "Je traite déjà une demande... un instant ! 🧠", None
        
        self._is_processing = True
        
        try:
            print(f"[TELEGRAM-BRIDGE] 📷 Image de {username} avec caption: {caption or 'aucune'}")
            
            if not self._chat_controller:
                return "⚠️ OGMA n'est pas encore prêt.", None
            
            # Convertir l'image en base64 pour l'API vision
            image_base64 = self.media_handler.image_to_base64(image_bytes)
            
            # Stocker l'image pour i2i potentiel
            self._pending_image_base64 = image_base64
            
            # Texte de la requête (garder original pour mémoire/historique)
            original_query = caption or "Qu'est-ce que tu vois sur cette image ?"
            
            # Vérifier si i2i est activé et si l'utilisateur demande une modification
            img_config = self._settings_manager.settings.get('image_generation', {}) if self._settings_manager else {}
            i2i_enabled = img_config.get('img2img_enabled', False)
            
            # Détecter si l'utilisateur veut modifier l'image
            modification_keywords = ['modifie', 'modifier', 'transforme', 'change', 'ajoute', 'enlève', 'mets', 'avec moi', 'avec toi']
            wants_modification = any(kw in original_query.lower() for kw in modification_keywords)
            
            # Construire le message avec l'image (format vision API)
            # Utiliser original_query pour la recherche mémoire (sans instruction i2i)
            context_messages = await self._build_context_messages(original_query, username)
            
            # Préparer le texte à envoyer à l'IA (avec instruction i2i si pertinent)
            ai_query_text = original_query
            if i2i_enabled and wants_modification:
                ai_query_text = f"""{original_query}

[INSTRUCTION I2I] L'utilisateur t'envoie une image et souhaite que tu la MODIFIES.
Pour modifier cette image, tu DOIS utiliser la phrase magique exacte:
"je dois modifier cette image : [description des modifications]"
Par exemple: "je dois modifier cette image : ajouter une femme aux cheveux roux à côté de l'homme"
Ne génère PAS une nouvelle image avec "je dois créer une image", utilise "je dois modifier cette image" pour transformer l'image fournie."""
            
            # Ajouter l'image au dernier message user
            if context_messages and context_messages[-1].get('role') == 'user':
                # Format multi-content pour vision
                context_messages[-1]['content'] = [
                    {"type": "text", "text": ai_query_text},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            
            # Appeler l'IA avec vision
            response = await self._call_ogma_chat(context_messages)
            
            if not response:
                self._pending_image_base64 = None
                return "Je n'ai pas pu analyser cette image. 🤔", None
            
            # Ajouter à l'historique (sans l'image et sans l'instruction i2i)
            self._add_to_history("user", f"[Image] {original_query}")
            self._add_to_history("assistant", response)
            
            # Vérifier si l'IA demande une modification i2i
            image_path = await self._process_img2img_generation(response, image_base64)
            
            # Si pas d'i2i, vérifier si une image text2img a été générée
            if not image_path:
                image_path = await self._process_image_generation(response)
            
            # Nettoyer l'image en attente
            self._pending_image_base64 = None
            
            clean_response = self._clean_response_for_telegram(response)
            
            return clean_response, image_path
            
        except Exception as e:
            print(f"[TELEGRAM-BRIDGE] ❌ Erreur traitement image: {e}")
            return f"Erreur lors de l'analyse de l'image: {str(e)[:100]}", None
        finally:
            self._is_processing = False
    
    async def process_voice_message(
        self,
        audio_path: str,
        user_id: int,
        username: str = "Telegram User"
    ) -> Tuple[str, Optional[str], Optional[str]]:
        """
        Traite un message vocal depuis Telegram.
        
        Args:
            audio_path: Chemin du fichier audio téléchargé
            user_id: ID Telegram
            username: Nom d'utilisateur
            
        Returns:
            (response_text, image_path, voice_response_path)
        """
        try:
            print(f"[TELEGRAM-BRIDGE] 🎤 Vocal de {username}")
            
            # Transcrire l'audio
            transcription = await self.media_handler.transcribe_voice(audio_path)
            
            if not transcription:
                return "Je n'ai pas pu transcrire ton message vocal. 🎤❌", None, None
            
            print(f"[TELEGRAM-BRIDGE] 📝 Transcription: {transcription}")
            
            # Traiter comme un message texte
            response_text, image_path = await self.process_text_message(
                transcription, user_id, username
            )
            
            # Générer une réponse vocale si activé
            voice_path = None
            if self.config.voice_output_enabled:
                voice_path = await self.media_handler.generate_voice_response(response_text)
            
            return response_text, image_path, voice_path
            
        except Exception as e:
            print(f"[TELEGRAM-BRIDGE] ❌ Erreur traitement vocal: {e}")
            return f"Erreur: {str(e)[:100]}", None, None
    
    # === Méthodes privées ===
    
    async def _build_context_messages(
        self, 
        user_message: str, 
        username: str
    ) -> List[Dict[str, Any]]:
        """Construit les messages de contexte pour l'appel IA"""
        messages = []
        
        # Message système avec horodatage
        now = datetime.now()
        horodatage = f"Il est {now.strftime('%H:%M')} le {now.strftime('%A %d %B %Y')}"
        
        system_content = f"""[HORODATAGE] {horodatage}
[SOURCE] Message reçu via Telegram (mobile)
[UTILISATEUR] {username}

Tu es OGMA, l'assistant IA à mémoire persistante. Tu réponds via Telegram.
Adapte tes réponses au format mobile: sois concis mais complet.
Tu as accès à toute ta mémoire et tes capacités habituelles."""
        
        # Ajouter le contexte mémoriel si disponible
        if self._memory_manager:
            try:
                # search_memories est async et retourne une liste de dicts
                memories = await self._memory_manager.search_memories(
                    query=user_message,
                    limit=5
                )
                if memories:
                    memory_context = "\n\n[SOUVENIRS PERTINENTS]\n"
                    for mem in memories[:3]:
                        if isinstance(mem, dict):
                            text = mem.get('text', mem.get('content', mem.get('summary', '')))[:200]
                        else:
                            text = str(mem)[:200]
                        memory_context += f"- {text}\n"
                    system_content += memory_context
            except Exception as e:
                print(f"[TELEGRAM-BRIDGE] ⚠️ Erreur récupération mémoire: {e}")
        
        messages.append({"role": "system", "content": system_content})
        
        # Ajouter l'historique récent
        for msg in self._telegram_history[-10:]:
            messages.append(msg)
        
        # Ajouter le message actuel
        messages.append({"role": "user", "content": f"[{username}] {user_message}"})
        
        return messages
    
    async def _call_ogma_chat(self, messages: List[Dict[str, Any]]) -> Optional[str]:
        """Appelle le contrôleur de chat OGMA"""
        try:
            if not self._chat_controller:
                return None
            
            # Paramètres par défaut pour l'appel
            max_tokens = 4096
            context_length = 128000
            temperature = 0.7
            
            # call_chat_api est async et retourne (response, error)
            response, error = await self._chat_controller.call_chat_api(
                messages,
                max_tokens,
                context_length,
                temperature
            )
            
            if error:
                print(f"[TELEGRAM-BRIDGE] ⚠️ Erreur API: {error}")
                return None
            
            return response
            
        except Exception as e:
            print(f"[TELEGRAM-BRIDGE] ❌ Erreur appel chat: {e}")
            return None
    
    async def _process_image_generation(self, response: str) -> Optional[str]:
        """
        Détecte la phrase magique de génération d'image et génère l'image.
        Retourne le chemin de l'image générée ou None.
        """
        if not self._text2img_manager:
            return None
        
        # Patterns de détection de phrase magique
        text2img_patterns = [
            "je dois créer une image de :",
            "je dois créer une image de:",
            "il faut que je crée une image de :",
            "je vais générer une image de :",
            "je dois générer une image de :"
        ]
        
        response_lower = response.lower()
        prompt = None
        
        for pattern in text2img_patterns:
            if pattern in response_lower:
                # Extraire le prompt après la phrase magique
                idx = response_lower.find(pattern)
                prompt = response[idx + len(pattern):].strip()
                # Couper au premier retour à la ligne ou fin
                if '\n' in prompt:
                    prompt = prompt.split('\n')[0].strip()
                break
        
        if not prompt:
            return None
        
        print(f"[TELEGRAM-BRIDGE] 🎨 Phrase magique détectée! Prompt: {prompt[:80]}...")
        
        try:
            # Générer l'image
            image_bytes, error, metadata = await self._text2img_manager.generate_image(prompt)
            
            if error:
                print(f"[TELEGRAM-BRIDGE] ❌ Erreur génération image: {error}")
                return None
            
            if not image_bytes:
                print("[TELEGRAM-BRIDGE] ❌ Aucune image générée")
                return None
            
            # Sauvegarder l'image
            local_path, save_error = self._text2img_manager.save_image(image_bytes, metadata)
            
            if save_error or not local_path:
                print(f"[TELEGRAM-BRIDGE] ❌ Erreur sauvegarde image: {save_error}")
                return None
            
            print(f"[TELEGRAM-BRIDGE] ✅ Image générée: {local_path}")
            return str(local_path)
            
        except Exception as e:
            print(f"[TELEGRAM-BRIDGE] ❌ Exception génération image: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def _process_img2img_generation(self, response: str, source_image_base64: str) -> Optional[str]:
        """
        Détecte la phrase magique i2i et génère l'image modifiée.
        
        Args:
            response: Réponse de l'IA
            source_image_base64: Image source en base64
            
        Returns:
            Chemin de l'image modifiée ou None
        """
        if not self._text2img_manager or not self._settings_manager:
            return None
        
        # Vérifier si i2i est activé
        img_config = self._settings_manager.settings.get('image_generation', {})
        if not img_config.get('img2img_enabled', False):
            return None
        
        # Patterns de détection de phrase magique i2i
        img2img_patterns = [
            "je dois modifier cette image :",
            "je dois modifier cette image:",
            "il faut que je modifie cette image :",
            "je vais modifier cette image :",
        ]
        
        response_lower = response.lower()
        prompt = None
        
        for pattern in img2img_patterns:
            if pattern in response_lower:
                # Extraire le prompt après la phrase magique
                idx = response_lower.find(pattern)
                prompt = response[idx + len(pattern):].strip()
                # Couper au premier retour à la ligne ou fin
                if '\n' in prompt:
                    prompt = prompt.split('\n')[0].strip()
                break
        
        if not prompt:
            return None
        
        print(f"[TELEGRAM-BRIDGE] 🔄 Phrase magique i2i détectée! Prompt: {prompt[:80]}...")
        
        try:
            # Récupérer le backend et le modèle i2i
            from extensions.text2img.image_backend import get_image_backend
            
            backend = get_image_backend(self._settings_manager)
            if not backend:
                print("[TELEGRAM-BRIDGE] ❌ Backend i2i non disponible")
                return None
            
            img2img_model = img_config.get('img2img_model', 'flux-2/pro-image-to-image')
            
            # Auto-détecter le provider selon le modèle
            # WaveSpeed utilise des noms avec "/" comme bytedance/seedream-v4.5/edit
            # Kie utilise des noms différents comme seedream/4.5-edit
            wavespeed_patterns = ['bytedance/seedream-v4.5/', 'bytedance/seedream-v4/']
            provider = "WaveSpeed" if any(p in img2img_model for p in wavespeed_patterns) else "Kie"
            
            print(f"[TELEGRAM-BRIDGE] 🔄 Génération i2i avec modèle: {img2img_model} (provider: {provider})")
            
            # Générer l'image modifiée (backend retourne 3 valeurs: bytes, error, metadata)
            image_bytes, error, _metadata = await backend.generate_img2img(
                prompt=prompt,
                source_image_base64=source_image_base64,
                model=img2img_model,
                provider=provider
            )
            
            if error:
                print(f"[TELEGRAM-BRIDGE] ❌ Erreur i2i: {error}")
                return None
            
            if not image_bytes:
                print("[TELEGRAM-BRIDGE] ❌ Aucune image i2i générée")
                return None
            
            # Sauvegarder l'image
            local_path, save_error = self._text2img_manager.save_image(
                image_bytes, 
                {'prompt': prompt, 'type': 'img2img'}
            )
            
            if save_error or not local_path:
                print(f"[TELEGRAM-BRIDGE] ❌ Erreur sauvegarde i2i: {save_error}")
                return None
            
            print(f"[TELEGRAM-BRIDGE] ✅ Image i2i générée: {local_path}")
            return str(local_path)
            
        except Exception as e:
            print(f"[TELEGRAM-BRIDGE] ❌ Exception i2i: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def _enrich_with_web_context(
        self, 
        user_text: str, 
        messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Enrichit le contexte avec une recherche web si l'utilisateur le demande.
        
        Args:
            user_text: Message de l'utilisateur
            messages: Messages de contexte existants
            
        Returns:
            Messages enrichis avec le contexte web
        """
        if not self._web_navigator:
            return messages
        
        try:
            # Vérifier si l'utilisateur demande une recherche internet
            if not self._web_navigator.commands.is_internet_request(user_text):
                return messages
            
            # Vérifier que la recherche web est activée
            if not self._web_navigator.config.is_web_search_enabled():
                print("[TELEGRAM-BRIDGE] 🌐 Recherche web désactivée")
                return messages
            
            print(f"[TELEGRAM-BRIDGE] 🌐 Recherche web détectée dans la requête utilisateur")
            
            # Effectuer la recherche
            web_response, _ = await self._web_navigator.commands.process_internet_request(user_text)
            
            if web_response:
                print(f"[TELEGRAM-BRIDGE] ✅ Contexte web récupéré: {len(web_response)} caractères")
                
                # Insérer le contexte web avant le message utilisateur
                web_context_message = {
                    'role': 'system',
                    'content': f"CONTEXTE WEB RÉCENT:\n\n{web_response}\n\nUtilise ces informations récentes pour enrichir ta réponse."
                }
                messages.insert(-1, web_context_message)
            else:
                print(f"[TELEGRAM-BRIDGE] ⚠️ Pas de résultats web")
                
        except Exception as e:
            print(f"[TELEGRAM-BRIDGE] ❌ Erreur enrichissement web: {e}")
        
        return messages
    
    async def _process_ai_web_search(
        self, 
        response: str, 
        original_messages: List[Dict[str, Any]]
    ) -> str:
        """
        Détecte si l'IA demande une recherche web et régénère la réponse avec le contexte.
        
        Args:
            response: Réponse de l'IA
            original_messages: Messages originaux
            
        Returns:
            Réponse (éventuellement régénérée avec contexte web)
        """
        if not self._web_navigator:
            return response
        
        try:
            # Vérifier si l'IA demande une recherche internet dans sa réponse
            if not self._web_navigator.commands.is_internet_request(response):
                return response
            
            # Vérifier que la recherche web est activée
            if not self._web_navigator.config.is_web_search_enabled():
                print("[TELEGRAM-BRIDGE] 🌐 Recherche web auto IA désactivée")
                return response
            
            print(f"[TELEGRAM-BRIDGE] 🌐 L'IA demande une recherche web auto-déclenchée!")
            
            # Effectuer la recherche
            web_response, _ = await self._web_navigator.commands.process_internet_request(response)
            
            if not web_response:
                print(f"[TELEGRAM-BRIDGE] ⚠️ Échec recherche web auto")
                return response
            
            print(f"[TELEGRAM-BRIDGE] ✅ Contexte web récupéré: {len(web_response)} caractères")
            
            # Régénérer la réponse avec le contexte web
            web_context_message = {
                'role': 'system',
                'content': f"INFORMATIONS WEB RÉCUPÉRÉES:\n\n{web_response}\n\nRéponds maintenant à la question en utilisant ces informations récentes."
            }
            
            regeneration_messages = original_messages + [web_context_message]
            
            new_response = await self._call_ogma_chat(regeneration_messages)
            
            if new_response:
                print(f"[TELEGRAM-BRIDGE] ✅ Réponse régénérée avec contexte web")
                return new_response
            else:
                print(f"[TELEGRAM-BRIDGE] ⚠️ Échec régénération - réponse originale conservée")
                return response
                
        except Exception as e:
            print(f"[TELEGRAM-BRIDGE] ❌ Erreur recherche web auto: {e}")
            return response
    
    def _add_to_history(self, role: str, content: str) -> None:
        """Ajoute un message à l'historique de conversation"""
        self._telegram_history.append({"role": role, "content": content})
        
        # Limiter la taille
        if len(self._telegram_history) > self._max_history:
            self._telegram_history = self._telegram_history[-self._max_history:]
    
    def _clean_response_for_telegram(self, response: str) -> str:
        """Nettoie la réponse pour l'affichage Telegram"""
        # Extraire le message si la réponse est au format JSON
        if response.strip().startswith('{'):
            try:
                data = json.loads(response)
                if isinstance(data, dict):
                    # Support multiple key formats: message, output, réponse, response
                    response = data.get('message') or data.get('output') or data.get('réponse') or data.get('response', response)
            except json.JSONDecodeError:
                pass  # Pas du JSON valide, continuer avec la réponse brute
        
        # Convertir les \n littéraux (texte) en vrais retours à la ligne
        response = response.replace('\\n', '\n')
        # Aussi gérer /n/ qui peut apparaître dans certains cas
        response = response.replace('/n/', '\n')
        
        # Retirer les phrases magiques de génération d'image et leur contenu
        text2img_patterns = [
            r'je dois créer une image de\s*:\s*[^\n]+',
            r'il faut que je crée une image de\s*:\s*[^\n]+',
            r'je vais générer une image de\s*:\s*[^\n]+',
            r'je dois générer une image de\s*:\s*[^\n]+'
        ]
        for pattern in text2img_patterns:
            response = re.sub(pattern, '', response, flags=re.IGNORECASE)
        
        # Retirer les phrases magiques i2i et leur contenu
        img2img_patterns = [
            r'je dois modifier cette image\s*:\s*[^\n]+',
            r'il faut que je modifie cette image\s*:\s*[^\n]+',
            r'je vais modifier cette image\s*:\s*[^\n]+'
        ]
        for pattern in img2img_patterns:
            response = re.sub(pattern, '', response, flags=re.IGNORECASE)
        
        # Retirer les balises img HTML
        response = re.sub(r'<img[^>]+>', '', response)
        
        # Retirer les balises markdown d'images
        response = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', response)
        
        # Convertir les balises HTML basiques en markdown Telegram
        response = re.sub(r'<b>([^<]+)</b>', r'*\1*', response)
        response = re.sub(r'<i>([^<]+)</i>', r'_\1_', response)
        response = re.sub(r'<code>([^<]+)</code>', r'`\1`', response)
        
        # Retirer les autres balises HTML
        response = re.sub(r'<[^>]+>', '', response)
        
        # Nettoyer les espaces multiples et lignes vides
        response = re.sub(r'\n{3,}', '\n\n', response)
        response = response.strip()
        
        # Limiter la longueur
        max_len = self.config.max_message_length
        if len(response) > max_len:
            response = response[:max_len-3] + "..."
        
        return response
    
    def _transcribe_audio(self, audio_path: str) -> Optional[str]:
        """Callback STT pour le media handler"""
        # Cette méthode sera appelée par media_handler
        # Elle utilise le audio_manager configuré
        return None  # Fallback géré dans media_handler
    
    def clear_history(self) -> None:
        """Efface l'historique de conversation Telegram"""
        self._telegram_history = []
        print("[TELEGRAM-BRIDGE] 🧹 Historique effacé")
    
    def get_status(self) -> Dict[str, Any]:
        """Retourne le statut du bridge"""
        return {
            "is_processing": self._is_processing,
            "history_length": len(self._telegram_history),
            "chat_controller_ready": self._chat_controller is not None,
            "memory_manager_ready": self._memory_manager is not None,
            "last_user_id": self._last_user_id,
        }


# Singleton
_bridge_instance: Optional[TelegramMessageBridge] = None

def get_message_bridge() -> TelegramMessageBridge:
    """Retourne l'instance singleton du bridge"""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = TelegramMessageBridge()
    return _bridge_instance
