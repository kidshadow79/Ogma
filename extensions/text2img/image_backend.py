"""
Backend Multi-Provider pour génération d'images
================================================
Support: GROK (xAI), OpenAI (DALL-E), Google (Imagen)

Architecture unifiée utilisant le vault de clés API existant.
"""

import asyncio
import aiohttp
import base64
import json
from typing import Optional, Dict, Any, Tuple, List
from abc import ABC, abstractmethod


class ImageProviderBase(ABC):
    """Classe de base abstraite pour les providers d'images"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.is_available = bool(api_key)
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Nom du provider"""
        pass
    
    @property
    @abstractmethod
    def supports_nsfw(self) -> bool:
        """Indique si le provider supporte le contenu Unfiltered/Spicy"""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Retourne la liste des modèles disponibles (hardcodée)"""
        pass
    
    async def fetch_live_models(self) -> Tuple[Optional[List[str]], Optional[str]]:
        """
        Récupère la liste des modèles en direct depuis l'API du provider
        
        Returns:
            tuple: (list_models, error_message)
            Par défaut retourne None (non implémenté)
        """
        return None, "Récupération dynamique non implémentée pour ce provider"
    
    async def fetch_live_img2img_models(self) -> Tuple[Optional[List[str]], Optional[str]]:
        """
        Récupère la liste des modèles Image-to-Image en direct depuis l'API du provider
        
        Returns:
            tuple: (list_models, error_message)
            Par défaut retourne None (non implémenté)
        """
        return None, "Récupération dynamique I2I non implémentée pour ce provider"
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        model: str,
        width: int,
        height: int,
        **kwargs
    ) -> Tuple[Optional[bytes], Optional[str]]:
        """
        Génère une image
        
        Returns:
            tuple: (image_bytes, error_message)
        """
        pass


class GrokImageProvider(ImageProviderBase):
    """Provider xAI (Grok) - Supporte le mode Spicy"""
    
    BASE_URL = "https://api.x.ai/v1/images/generations"
    
    @property
    def name(self) -> str:
        return "GROK"
    
    @property
    def supports_nsfw(self) -> bool:
        return True
    
    def get_available_models(self) -> List[str]:
        return [
            "grok-2-image-1212"
        ]
    
    async def generate(
        self,
        prompt: str,
        model: str,
        width: int,
        height: int,
        **kwargs
    ) -> Tuple[Optional[bytes], Optional[str]]:
        if not self.is_available:
            return None, "Clé API GROK manquante"
        
        # Grok supporte des tailles spécifiques
        size = f"{width}x{height}"
        
        payload = {
            "model": model or "grok-2-image-1212",
            "prompt": prompt,
            "n": 1,
            "response_format": "b64_json"
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            print(f"[IMAGE-GROK] 🚀 Génération avec {model}...")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.BASE_URL,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"[IMAGE-GROK] ❌ Erreur API ({response.status}): {error_text[:200]}")
                        return None, f"Erreur xAI: {response.status}"
                    
                    result = await response.json()
                    
                    if 'data' in result and len(result['data']) > 0:
                        b64_data = result['data'][0].get('b64_json')
                        if b64_data:
                            image_bytes = base64.b64decode(b64_data)
                            print(f"[IMAGE-GROK] ✅ Image générée ({len(image_bytes)} bytes)")
                            return image_bytes, None
                        
                        # Fallback URL si pas de b64
                        url_data = result['data'][0].get('url')
                        if url_data:
                            async with session.get(url_data) as img_resp:
                                if img_resp.status == 200:
                                    return await img_resp.read(), None
                    
                    return None, "Format de réponse API inconnu"
                    
        except asyncio.TimeoutError:
            return None, "Délai d'attente dépassé (Timeout)"
        except Exception as e:
            print(f"[IMAGE-GROK] ❌ Erreur: {e}")
            return None, str(e)


class OpenAIImageProvider(ImageProviderBase):
    """Provider OpenAI (DALL-E) - Très censuré"""
    
    BASE_URL = "https://api.openai.com/v1/images/generations"
    
    @property
    def name(self) -> str:
        return "OpenAI"
    
    @property
    def supports_nsfw(self) -> bool:
        return False  # DALL-E est très censuré
    
    def get_available_models(self) -> List[str]:
        return [
            "dall-e-3",
            "dall-e-2"
        ]
    
    async def generate(
        self,
        prompt: str,
        model: str,
        width: int,
        height: int,
        **kwargs
    ) -> Tuple[Optional[bytes], Optional[str]]:
        if not self.is_available:
            return None, "Clé API OpenAI manquante"
        
        # DALL-E 3 supporte: 1024x1024, 1792x1024, 1024x1792
        # DALL-E 2 supporte: 256x256, 512x512, 1024x1024
        if model == "dall-e-3":
            if width > height:
                size = "1792x1024"
            elif height > width:
                size = "1024x1792"
            else:
                size = "1024x1024"
        else:
            size = "1024x1024"
        
        payload = {
            "model": model or "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": size,
            "response_format": "b64_json"
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            print(f"[IMAGE-OPENAI] 🚀 Génération avec {model}...")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.BASE_URL,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"[IMAGE-OPENAI] ❌ Erreur API ({response.status}): {error_text[:200]}")
                        return None, f"Erreur OpenAI: {response.status}"
                    
                    result = await response.json()
                    
                    if 'data' in result and len(result['data']) > 0:
                        b64_data = result['data'][0].get('b64_json')
                        if b64_data:
                            image_bytes = base64.b64decode(b64_data)
                            print(f"[IMAGE-OPENAI] ✅ Image générée ({len(image_bytes)} bytes)")
                            return image_bytes, None
                    
                    return None, "Format de réponse API inconnu"
                    
        except asyncio.TimeoutError:
            return None, "Délai d'attente dépassé (Timeout)"
        except Exception as e:
            print(f"[IMAGE-OPENAI] ❌ Erreur: {e}")
            return None, str(e)


class GoogleImageProvider(ImageProviderBase):
    """Provider Google (Imagen) - Modérément censuré"""
    
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
    
    @property
    def name(self) -> str:
        return "Google"
    
    @property
    def supports_nsfw(self) -> bool:
        return False  # Imagen est modéré
    
    def get_available_models(self) -> List[str]:
        return [
            "imagen-3.0-generate-002",
            "imagen-3.0-fast-generate-001"
        ]
    
    async def generate(
        self,
        prompt: str,
        model: str,
        width: int,
        height: int,
        **kwargs
    ) -> Tuple[Optional[bytes], Optional[str]]:
        if not self.is_available:
            return None, "Clé API Google manquante"
        
        model = model or "imagen-3.0-generate-002"
        url = f"{self.BASE_URL}/{model}:generateImages?key={self.api_key}"
        
        # Google utilise aspectRatio au lieu de dimensions exactes
        if width > height:
            aspect_ratio = "16:9"
        elif height > width:
            aspect_ratio = "9:16"
        else:
            aspect_ratio = "1:1"
        
        payload = {
            "prompt": prompt,
            "config": {
                "numberOfImages": 1,
                "aspectRatio": aspect_ratio,
                "outputMimeType": "image/png"
            }
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        try:
            print(f"[IMAGE-GOOGLE] 🚀 Génération avec {model}...")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"[IMAGE-GOOGLE] ❌ Erreur API ({response.status}): {error_text[:200]}")
                        return None, f"Erreur Google: {response.status}"
                    
                    result = await response.json()
                    
                    # Format de réponse Imagen
                    if 'generatedImages' in result and len(result['generatedImages']) > 0:
                        b64_data = result['generatedImages'][0].get('image', {}).get('bytesBase64Encoded')
                        if b64_data:
                            image_bytes = base64.b64decode(b64_data)
                            print(f"[IMAGE-GOOGLE] ✅ Image générée ({len(image_bytes)} bytes)")
                            return image_bytes, None
                    
                    return None, "Format de réponse API inconnu"
                    
        except asyncio.TimeoutError:
            return None, "Délai d'attente dépassé (Timeout)"
        except Exception as e:
            print(f"[IMAGE-GOOGLE] ❌ Erreur: {e}")
            return None, str(e)


class KieImageProvider(ImageProviderBase):
    """
    Provider Kie.ai - Multi-modèles Unfiltered
    
    Modèles Text-to-Image:
    - z-image: Ultra rapide, $0.004/img
    - flux-2/pro-text-to-image: Haute qualité, $0.025/img
    - seedream-4.5: ByteDance 4K, $0.032/img
    - grok-imagine/text-to-image: xAI via Kie, $0.10/img
    - nano-banana-pro: Google DeepMind 2K, $0.09/img
    
    Modèles Image-to-Image:
    - flux-2/pro-image-to-image: Haute qualité, $0.025/img
    - seedream/4.5-edit: ByteDance Edit, $0.032/img
    - gpt-image/1.5-image-to-image: OpenAI GPT Image, $0.05/img
    - nano-banana-pro: Google (aussi img2img), $0.09/img
    
    Documentation: https://docs.kie.ai/market
    """
    
    BASE_URL = "https://api.kie.ai/api/v1/jobs"
    FILE_UPLOAD_URL = "https://kieai.redpandaai.co/api/file-base64-upload"
    POLL_INTERVAL = 2.0  # secondes entre chaque poll
    MAX_POLLS = 90        # max ~3 minutes d'attente
    MAX_WAITING_POLLS = 60  # abort si 'waiting' ne progresse pas après 2 min
    
    # Modèles Text-to-Image disponibles avec leurs paramètres
    # Format des payloads Kie :
    #   "format_A"  → aspect_ratio: "1:1" (ex: z-image, grok-imagine)
    #   "format_A+" → aspect_ratio + resolution obligatoire (ex: flux-2/pro)
    #   "format_B"  → image_size enum: "square_hd"|"portrait_16_9"|... (ex: bytedance/seedream, nano-banana-pro)
    #   "format_C"  → image_size ratio: "1:1"|"9:16"|... (ex: qwen2/text-to-image)
    MODELS = {
        "z-image": {
            "payload_format": "format_A",
            "nsfw": True,
            "credits": 0.8,
            "type": "text2img"
        },
        "bytedance/seedream": {
            "payload_format": "format_B",
            "nsfw": False,
            "credits": 4,
            "type": "text2img"
        },
        "bytedance/seedream-v4-text-to-image": {
            "payload_format": "format_A",
            "resolution": True,  # Supporte 1K, 2K (optionnel)
            "nsfw": False,
            "credits": 5,
            "type": "text2img"
        },
        "flux-2/pro-text-to-image": {
            "payload_format": "format_A+",  # aspect_ratio + resolution OBLIGATOIRE
            "nsfw": True,
            "credits": 5,
            "type": "text2img"
        },
        "qwen2/text-to-image": {
            "payload_format": "format_C",
            "nsfw": True,
            "credits": 0.8,
            "type": "text2img"
        },
        "grok-imagine/text-to-image": {
            "payload_format": "format_A",
            "nsfw": True,
            "credits": 20,
            "type": "text2img"
        },
        "nano-banana-pro": {
            "payload_format": "format_B",
            "resolution": True,  # Supporte 2K, 4K (optionnel)
            "nsfw": False,
            "credits": 18,
            "type": "text2img"
        }
    }

    # Formats payload pour modèles custom ajoutés via "+"
    # Clé: nom_modèle, Valeur: {"payload_format": "format_X", ...}
    CUSTOM_MODELS: dict = {}
    
    # Modèles Image-to-Image disponibles avec leurs paramètres API spécifiques
    IMG2IMG_MODELS = {
        "flux-2/pro-image-to-image": {
            "nsfw": True,
            "credits": 5,
            "input_key": "input_urls",
            "type": "img2img",
            "max_images": 2,  # Max 2 images en entrée
            "params": {
                "aspect_ratio": {"options": ["1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3", "21:9", "9:21"], "default": "1:1", "label": "Format"},
                "resolution": {"options": ["1K", "2K"], "default": "1K", "label": "Résolution"}
            }
        },
        "seedream/4.5-edit": {
            "nsfw": True,
            "credits": 6.5,
            "input_key": "image_urls",
            "type": "img2img",
            "max_images": 3,  # Max 3 images en entrée
            "params": {
                "aspect_ratio": {"options": ["1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3"], "default": "1:1", "label": "Format"},
                "quality": {"options": ["basic", "high"], "default": "basic", "label": "Qualité", "info": "basic=2K, high=4K"}
            }
        },
        "bytedance/seedream-v4-edit": {
            "nsfw": True,
            "credits": 6.5,
            "input_key": "image_urls",
            "type": "img2img",
            "max_images": 3,
            "params": {
                "image_size": {"options": ["square_hd", "portrait_4_3", "landscape_16_9", "portrait_hd", "landscape_hd"], "default": "square_hd", "label": "Format"},
                "image_resolution": {"options": ["1K", "2K"], "default": "1K", "label": "Résolution"},
                "max_images_output": {"range": [1, 4], "default": 1, "label": "Nb variantes"}
            }
        },
        "gpt-image/1.5-image-to-image": {
            "nsfw": False,
            "credits": 10,
            "input_key": "input_urls",
            "type": "img2img",
            "max_images": 16,  # GPT supporte jusqu'à 16 images
            "params": {
                "aspect_ratio": {"options": ["1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3"], "default": "1:1", "label": "Format"},
                "quality": {"options": ["low", "medium", "high"], "default": "medium", "label": "Qualité"}
            }
        },
        "nano-banana-pro-img2img": {
            "model_name": "nano-banana-pro",  # Vrai nom API
            "nsfw": False,
            "credits": 18,
            "input_key": "image_input",
            "type": "img2img",
            "max_images": 4,
            "params": {
                "aspect_ratio": {"options": ["1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3"], "default": "1:1", "label": "Format"},
                "resolution": {"options": ["1K", "2K", "4K"], "default": "1K", "label": "Résolution"},
                "output_format": {"options": ["png", "jpeg", "webp"], "default": "png", "label": "Format sortie"}
            }
        },
        "qwen/image-to-image": {
            "nsfw": True,  # Avec safety checker désactivable
            "credits": 5,
            "input_key": "image_url",  # SINGULIER - une seule image
            "type": "img2img",
            "max_images": 1,
            "params": {
                "strength": {"range": [0.1, 1.0], "default": 0.8, "step": 0.05, "label": "Force"},
                "enable_safety_checker": {"options": [True, False], "default": True, "label": "Mode Safe"},
                "num_inference_steps": {"range": [10, 50], "default": 30, "label": "Steps"},
                "guidance_scale": {"range": [1.0, 10.0], "default": 2.5, "step": 0.5, "label": "Guidance"},
                "negative_prompt": {"type": "text", "default": "blurry, ugly", "label": "Negative prompt"},
                "output_format": {"options": ["png", "jpeg", "webp"], "default": "png", "label": "Format"},
                "acceleration": {"options": ["none", "tensorrt"], "default": "none", "label": "Accélération"}
            }
        },
        "qwen/image-edit": {
            "nsfw": True,  # Avec safety checker désactivable
            "credits": 5,
            "input_key": "image_url",  # SINGULIER - une seule image
            "type": "img2img",
            "max_images": 1,
            "params": {
                "image_size": {"options": ["square_hd", "portrait_4_3", "landscape_4_3", "portrait_16_9", "landscape_16_9"], "default": "square_hd", "label": "Format"},
                "enable_safety_checker": {"options": [True, False], "default": True, "label": "Mode Safe"},
                "num_inference_steps": {"range": [10, 50], "default": 25, "label": "Steps"},
                "guidance_scale": {"range": [1.0, 10.0], "default": 4.0, "step": 0.5, "label": "Guidance"},
                "negative_prompt": {"type": "text", "default": "blurry, ugly", "label": "Negative prompt"},
                "output_format": {"options": ["png", "jpeg", "webp"], "default": "png", "label": "Format"},
                "acceleration": {"options": ["none", "tensorrt"], "default": "none", "label": "Accélération"}
            }
        }
    }
    
    @property
    def name(self) -> str:
        return "Kie"
    
    @property
    def supports_nsfw(self) -> bool:
        return True  # Dépend du modèle, mais globalement oui
    
    def get_available_models(self) -> List[str]:
        """Retourne les modèles Text-to-Image"""
        return list(self.MODELS.keys())
    
    def get_img2img_models(self) -> List[str]:
        """Retourne les modèles Image-to-Image"""
        return list(self.IMG2IMG_MODELS.keys())
    
    async def fetch_live_models(self) -> Tuple[Optional[List[str]], Optional[str]]:
        """
        Récupère la liste des modèles en direct depuis l'API Kie.ai
        
        Returns:
            tuple: (list_models_text2img, error_message)
        """
        # TODO: Trouver le bon endpoint API Kie pour /models (404 sur /api/v1/models)
        # Désactivé temporairement pour éviter les erreurs 404 dans les logs
        return None, "Endpoint API Kie.ai /models non disponible (à déterminer)"
    
    async def fetch_live_img2img_models(self) -> Tuple[Optional[List[str]], Optional[str]]:
        """
        Récupère la liste des modèles Image-to-Image en direct depuis l'API Kie.ai
        
        Returns:
            tuple: (list_models_img2img, error_message)
        """
        # TODO: Trouver le bon endpoint API Kie pour /models (404 sur /api/v1/models)
        # Désactivé temporairement pour éviter les erreurs 404 dans les logs
        return None, "Endpoint API Kie.ai /models non disponible (à déterminer)"
    
    async def upload_base64_to_kie(self, base64_data: str, filename: str = "image.png") -> Tuple[Optional[str], Optional[str]]:
        """
        Upload une image en base64 vers Kie.ai et retourne l'URL publique
        
        Args:
            base64_data: Données image en base64 (sans préfixe data:image/...)
            filename: Nom du fichier pour l'upload
            
        Returns:
            tuple: (url_publique, error_message)
        """
        if not self.is_available:
            return None, "Clé API Kie manquante"
        
        # Nettoyer le base64 si nécessaire (retirer le préfixe data:image/...)
        if base64_data.startswith('data:'):
            base64_data = base64_data.split(',', 1)[1]
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "base64Data": base64_data,
            "uploadPath": "ogma-img2img",
            "fileName": filename
        }
        
        try:
            print(f"[IMAGE-KIE] 📤 Upload base64 vers Kie.ai ({len(base64_data)} chars)...")
            print(f"[IMAGE-KIE] 🔗 URL: {self.FILE_UPLOAD_URL}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.FILE_UPLOAD_URL,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    
                    response_text = await response.text()
                    print(f"[IMAGE-KIE] 📥 Réponse upload (status={response.status}): {response_text[:300]}")
                    
                    if response.status != 200:
                        print(f"[IMAGE-KIE] ❌ Erreur upload ({response.status}): {response_text[:500]}")
                        return None, f"Erreur upload: {response.status} - {response_text[:100]}"
                    
                    try:
                        result = json.loads(response_text)
                    except json.JSONDecodeError as je:
                        print(f"[IMAGE-KIE] ❌ JSON invalide: {je}")
                        return None, f"Réponse non-JSON: {response_text[:100]}"
                    
                    if result.get('success'):
                        data = result.get('data', {})
                        # L'API retourne downloadUrl, pas fileUrl
                        file_url = data.get('downloadUrl') or data.get('fileUrl')
                        if file_url:
                            print(f"[IMAGE-KIE] ✅ Upload réussi: {file_url}")
                            return file_url, None
                        print(f"[IMAGE-KIE] ⚠️ Pas de downloadUrl/fileUrl dans data: {data}")
                        return None, "Pas d'URL dans la réponse"
                    else:
                        error_msg = result.get('msg', result.get('message', 'Erreur upload inconnue'))
                        print(f"[IMAGE-KIE] ❌ Échec API: {error_msg}")
                        return None, f"Échec upload: {error_msg}"
                        
        except asyncio.TimeoutError:
            print("[IMAGE-KIE] ❌ Timeout upload (60s)")
            return None, "Timeout upload (60s)"
        except Exception as e:
            import traceback
            print(f"[IMAGE-KIE] ❌ Erreur upload: {e}")
            traceback.print_exc()
            return None, str(e)
    
    async def generate_img2img(
        self,
        prompt: str,
        source_image_base64: str = None,
        source_images_base64: List[str] = None,  # MULTI-IMAGE SUPPORT
        model: str = "flux-2/pro-image-to-image",
        width: int = 1024,
        height: int = 1024,
        **kwargs
    ) -> Tuple[Optional[bytes], Optional[str]]:
        """
        Génère une image modifiée à partir d'une ou plusieurs images source
        
        Args:
            prompt: Description des modifications à apporter
            source_image_base64: Image source en base64 (single image - backward compat)
            source_images_base64: Liste d'images en base64 (multi-image support)
            model: Modèle img2img à utiliser
            width: Largeur souhaitée
            height: Hauteur souhaitée
            
        Returns:
            tuple: (image_bytes, error_message)
        """
        if not self.is_available:
            return None, "Clé API Kie manquante"
        
        # Gestion compatibilité single/multi image
        images_list = []
        if source_images_base64:
            images_list = source_images_base64
        elif source_image_base64:
            images_list = [source_image_base64]
        
        if not images_list:
            return None, "Aucune image source fournie"
        
        print(f"[IMAGE-KIE-IMG2IMG] 📸 {len(images_list)} image(s) source à traiter")
        
        # Vérifier que le modèle est un modèle img2img
        if model not in self.IMG2IMG_MODELS:
            return None, f"Modèle img2img inconnu: {model}. Disponibles: {list(self.IMG2IMG_MODELS.keys())}"
        
        model_config = self.IMG2IMG_MODELS[model]
        
        # Étape 1: Upload toutes les images source vers Kie.ai
        import uuid
        image_urls = []
        for idx, img_base64 in enumerate(images_list):
            filename = f"source_{uuid.uuid4().hex[:8]}_{idx+1}.png"
            image_url, upload_error = await self.upload_base64_to_kie(img_base64, filename)
            
            if upload_error:
                return None, f"Échec upload image {idx+1}: {upload_error}"
            
            image_urls.append(image_url)
            print(f"[IMAGE-KIE-IMG2IMG] ✅ Image {idx+1}/{len(images_list)} uploadée")
        
        # Étape 2: Préparer le payload img2img selon le modèle
        aspect_ratio = self._get_aspect_ratio(width, height)
        
        # Récupérer le vrai nom du modèle si alias
        api_model_name = model_config.get("model_name", model)
        input_key = model_config.get("input_key", "input_urls")
        model_params = model_config.get("params", {})
        
        input_params = {
            "prompt": prompt,
        }
        
        # Gestion spéciale: image_url singulier (Qwen) vs image_urls pluriel (autres)
        if input_key == "image_url":
            # Qwen n'accepte qu'une seule image
            input_params[input_key] = image_urls[0] if image_urls else ""
        else:
            # Les autres modèles acceptent une liste
            input_params[input_key] = image_urls
        
        # Ajouter les paramètres selon la configuration du modèle
        # aspect_ratio (si supporté par le modèle)
        if "aspect_ratio" in model_params:
            ar_config = model_params["aspect_ratio"]
            # Si c'est un dict avec options, utiliser la valeur fournie ou default
            if isinstance(ar_config, dict):
                input_params["aspect_ratio"] = kwargs.get("aspect_ratio", ar_config.get("default", "1:1"))
            else:
                # Fallback: calcul auto depuis dimensions (ancien comportement)
                input_params["aspect_ratio"] = aspect_ratio
        
        # quality (Seedream 4.5 et GPT-Image)
        if "quality" in model_params:
            quality_config = model_params["quality"]
            quality_value = kwargs.get("quality", quality_config["default"])
            # Normaliser en lowercase pour Seedream, garder tel quel pour GPT
            if "seedream/4.5" in model.lower():
                input_params["quality"] = quality_value.lower()
            else:
                input_params["quality"] = quality_value
        
        # image_size (Seedream V4 et Qwen)
        if "image_size" in model_params:
            image_size_config = model_params["image_size"]
            input_params["image_size"] = kwargs.get("image_size", image_size_config["default"])
        
        # image_resolution (Seedream V4)
        if "image_resolution" in model_params:
            res_config = model_params["image_resolution"]
            input_params["image_resolution"] = kwargs.get("image_resolution", res_config["default"])
        
        # resolution (Flux-2 et Nano-Banana)
        if "resolution" in model_params:
            res_config = model_params["resolution"]
            input_params["resolution"] = kwargs.get("resolution", res_config["default"])
        
        # max_images_output (nombre de variantes - Seedream V4)
        if "max_images_output" in model_params:
            max_config = model_params["max_images_output"]
            input_params["max_images"] = kwargs.get("max_images_output", max_config["default"])
        
        # output_format (Nano-Banana et Qwen)
        if "output_format" in model_params:
            format_config = model_params["output_format"]
            input_params["output_format"] = kwargs.get("output_format", format_config["default"])
        
        # === Paramètres Qwen spécifiques ===
        # strength (Qwen image-to-image)
        if "strength" in model_params:
            strength_config = model_params["strength"]
            input_params["strength"] = kwargs.get("strength", strength_config["default"])
        
        # enable_safety_checker (Qwen)
        if "enable_safety_checker" in model_params:
            safety_config = model_params["enable_safety_checker"]
            input_params["enable_safety_checker"] = kwargs.get("enable_safety_checker", safety_config["default"])
        
        # num_inference_steps (Qwen)
        if "num_inference_steps" in model_params:
            steps_config = model_params["num_inference_steps"]
            input_params["num_inference_steps"] = int(kwargs.get("num_inference_steps", steps_config["default"]))
        
        # guidance_scale (Qwen)
        if "guidance_scale" in model_params:
            guidance_config = model_params["guidance_scale"]
            input_params["guidance_scale"] = float(kwargs.get("guidance_scale", guidance_config["default"]))
        
        # negative_prompt (Qwen)
        if "negative_prompt" in model_params:
            neg_config = model_params["negative_prompt"]
            input_params["negative_prompt"] = kwargs.get("negative_prompt", neg_config["default"])
        
        # acceleration (Qwen)
        if "acceleration" in model_params:
            accel_config = model_params["acceleration"]
            input_params["acceleration"] = kwargs.get("acceleration", accel_config["default"])
        
        create_payload = {
            "model": api_model_name,
            "input": input_params
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            credits = model_config.get('credits', '?')
            print(f"[IMAGE-KIE-IMG2IMG] 🚀 Création tâche {api_model_name} (~{credits} crédits)...")
            print(f"[IMAGE-KIE-IMG2IMG] 📦 Payload complet:")
            print(json.dumps(create_payload, indent=2))
            
            async with aiohttp.ClientSession() as session:
                # Créer la tâche
                async with session.post(
                    f"{self.BASE_URL}/createTask",
                    headers=headers,
                    json=create_payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"[IMAGE-KIE-IMG2IMG] ❌ Erreur création tâche ({response.status}): {error_text[:200]}")
                        return None, f"Erreur Kie: {response.status}"
                    
                    result = await response.json()
                    
                    if result.get('code') != 200:
                        error_msg = result.get('msg', 'Erreur inconnue')
                        print(f"[IMAGE-KIE-IMG2IMG] ❌ Erreur API: {error_msg}")
                        return None, f"Erreur Kie: {error_msg}"
                    
                    task_id = result.get('data', {}).get('taskId')
                    if not task_id:
                        return None, "Pas de taskId dans la réponse"
                    
                    print(f"[IMAGE-KIE-IMG2IMG] 📋 Tâche créée: {task_id}")
                
                # Étape 3: Poll pour le résultat
                consecutive_waiting = 0
                for poll_count in range(self.MAX_POLLS):
                    # 🛑 STOP: Vérifier si arrêt demandé
                    try:
                        from stop_signal import is_stop_requested
                        if is_stop_requested():
                            print(f"[IMAGE-KIE-IMG2IMG] 🛑 Génération interrompue par l'utilisateur au poll #{poll_count + 1}")
                            return None, "⏹️ Génération interrompue par l'utilisateur"
                    except ImportError:
                        pass  # Module non disponible, continuer
                    
                    await asyncio.sleep(self.POLL_INTERVAL)
                    
                    async with session.get(
                        f"{self.BASE_URL}/recordInfo",
                        params={"taskId": task_id},
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as poll_response:
                        
                        if poll_response.status != 200:
                            continue  # Réessayer
                        
                        poll_result = await poll_response.json()
                        data = poll_result.get('data', {})
                        state = data.get('state', '')
                        
                        print(f"[IMAGE-KIE-IMG2IMG] 🔄 Poll #{poll_count + 1}: {state}")

                        # Early-exit si 'waiting' persiste trop longtemps
                        if state == 'waiting':
                            consecutive_waiting += 1
                            if consecutive_waiting >= self.MAX_WAITING_POLLS:
                                print(f"[IMAGE-KIE-IMG2IMG] ⏰ File d'attente trop longue ({consecutive_waiting} polls 'waiting') - abandon")
                                return None, f"Kie.ai: file d'attente surchargée (>{self.MAX_WAITING_POLLS * 2}s). Réessayez dans quelques minutes ou changez de modèle."
                        else:
                            consecutive_waiting = 0
                        
                        if state == 'success':
                            # Extraire l'URL de l'image
                            result_json_str = data.get('resultJson', '{}')
                            try:
                                result_json = json.loads(result_json_str)
                                image_urls = result_json.get('resultUrls', [])
                                
                                if not image_urls:
                                    return None, "Pas d'URL d'image dans le résultat"
                                
                                image_url_result = image_urls[0]
                                print(f"[IMAGE-KIE-IMG2IMG] 📥 Téléchargement: {image_url_result[:50]}...")
                                
                                # Télécharger l'image
                                async with session.get(
                                    image_url_result,
                                    timeout=aiohttp.ClientTimeout(total=60)
                                ) as img_response:
                                    if img_response.status == 200:
                                        image_bytes = await img_response.read()
                                        print(f"[IMAGE-KIE-IMG2IMG] ✅ Image modifiée générée ({len(image_bytes)} bytes)")
                                        return image_bytes, None
                                    else:
                                        return None, f"Erreur téléchargement image: {img_response.status}"
                                        
                            except Exception as e:
                                return None, f"Erreur parsing résultat: {e}"
                        
                        elif state == 'fail':
                            fail_msg = data.get('failMsg', 'Génération échouée')
                            print(f"[IMAGE-KIE-IMG2IMG] ❌ Échec: {fail_msg}")
                            return None, f"Génération échouée: {fail_msg}"
                        
                        # États intermédiaires: waiting, queuing, generating
                        # Continuer le polling
                
                return None, "Timeout: génération trop longue"
                    
        except asyncio.TimeoutError:
            return None, "Délai d'attente dépassé (Timeout)"
        except Exception as e:
            print(f"[IMAGE-KIE-IMG2IMG] ❌ Erreur: {e}")
            return None, str(e)
    
    def _get_resolution(self, width: int, height: int) -> str:
        """Détermine la résolution (1K, 2K, 4K) selon les dimensions"""
        max_dim = max(width, height)
        if max_dim >= 3000:
            return "4K"
        elif max_dim >= 1500:
            return "2K"
        else:
            return "1K"
    
    def _get_aspect_ratio(self, width: int, height: int) -> str:
        """Convertit width/height en aspect_ratio pour Kie.ai"""
        ratio = width / height
        if ratio > 1.6:  # Plus large que 16:10
            return "16:9"
        elif ratio > 1.2:  # Entre 16:10 et 4:3
            return "4:3"
        elif ratio < 0.625:  # Plus étroit que 10:16
            return "9:16"
        elif ratio < 0.85:  # Entre 10:16 et 3:4
            return "3:4"
        else:  # Proche du carré
            return "1:1"
    
    async def generate(
        self,
        prompt: str,
        model: str,
        width: int,
        height: int,
        **kwargs
    ) -> Tuple[Optional[bytes], Optional[str]]:
        if not self.is_available:
            return None, "Clé API Kie manquante"

        model = model or "z-image"

        # Chercher dans MODELS officiels puis CUSTOM_MODELS — AUCUN fallback silencieux
        model_config = self.MODELS.get(model) or self.CUSTOM_MODELS.get(model)
        if model_config is None:
            return None, (
                f"Modèle Kie inconnu : '{model}'\n"
                f"Vérifiez le nom sur https://kie.ai/market et utilisez le bon format payload (A/B/C)."
            )

        payload_format = model_config.get("payload_format", "format_A")
        aspect_ratio = self._get_aspect_ratio(width, height)
        resolution = self._get_resolution(width, height)

        # Construire input_params selon le format déclaré
        if payload_format == "format_A":
            input_params = {"prompt": prompt, "aspect_ratio": aspect_ratio}
            if model_config.get("resolution"):
                input_params["resolution"] = resolution
        elif payload_format == "format_A+":
            # aspect_ratio + resolution OBLIGATOIRES
            input_params = {"prompt": prompt, "aspect_ratio": aspect_ratio, "resolution": resolution}
        elif payload_format == "format_B":
            # image_size enum texte (square_hd, portrait_16_9, ...)
            ratio_to_enum = {
                "1:1": "square_hd", "16:9": "landscape_16_9", "9:16": "portrait_16_9",
                "4:3": "landscape_4_3", "3:4": "portrait_4_3", "3:2": "landscape_4_3", "2:3": "portrait_4_3"
            }
            image_size = ratio_to_enum.get(aspect_ratio, "square_hd")
            input_params = {"prompt": prompt, "image_size": image_size}
            if model_config.get("resolution"):
                input_params["resolution"] = resolution
        elif payload_format == "format_C":
            # image_size ratio direct ("1:1", "9:16", ...)
            input_params = {"prompt": prompt, "image_size": aspect_ratio}
        else:
            return None, f"Format payload inconnu '{payload_format}' pour le modèle '{model}'"

        # Étape 1: Créer la tâche
        create_payload = {
            "model": model,
            "input": input_params
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            credits = model_config.get('credits', '?')
            print(f"[IMAGE-KIE] 🚀 Création tâche {model} (ratio: {aspect_ratio}, format: {payload_format}, ~{credits} crédits)...")
            
            async with aiohttp.ClientSession() as session:
                # Créer la tâche
                async with session.post(
                    f"{self.BASE_URL}/createTask",
                    headers=headers,
                    json=create_payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"[IMAGE-KIE] ❌ Erreur création tâche ({response.status}): {error_text[:200]}")
                        return None, f"Erreur Kie: {response.status}"
                    
                    result = await response.json()
                    
                    if result.get('code') != 200:
                        error_msg = result.get('msg', 'Erreur inconnue')
                        print(f"[IMAGE-KIE] ❌ Erreur API: {error_msg}")
                        return None, f"Erreur Kie: {error_msg}"
                    
                    task_id = result.get('data', {}).get('taskId')
                    if not task_id:
                        return None, "Pas de taskId dans la réponse"
                    
                    print(f"[IMAGE-KIE] 📋 Tâche créée: {task_id}")
                
                # Étape 2: Poll pour le résultat
                consecutive_waiting = 0
                for poll_count in range(self.MAX_POLLS):
                    # 🛑 STOP: Vérifier si arrêt demandé
                    try:
                        from stop_signal import is_stop_requested
                        if is_stop_requested():
                            print(f"[IMAGE-KIE] 🛑 Génération interrompue par l'utilisateur au poll #{poll_count + 1}")
                            return None, "⏹️ Génération interrompue par l'utilisateur"
                    except ImportError:
                        pass  # Module non disponible, continuer
                    
                    await asyncio.sleep(self.POLL_INTERVAL)
                    
                    async with session.get(
                        f"{self.BASE_URL}/recordInfo",
                        params={"taskId": task_id},
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as poll_response:
                        
                        if poll_response.status != 200:
                            continue  # Réessayer
                        
                        poll_result = await poll_response.json()
                        data = poll_result.get('data', {})
                        state = data.get('state', '')
                        
                        print(f"[IMAGE-KIE] 🔄 Poll #{poll_count + 1}: {state}")

                        # Early-exit si 'waiting' persiste trop longtemps sans progresser
                        if state == 'waiting':
                            consecutive_waiting += 1
                            if consecutive_waiting >= self.MAX_WAITING_POLLS:
                                print(f"[IMAGE-KIE] ⏰ File d'attente trop longue ({consecutive_waiting} polls 'waiting') - abandon")
                                return None, f"Kie.ai: file d'attente surchargée (>{self.MAX_WAITING_POLLS * 2}s). Réessayez dans quelques minutes ou changez de modèle."
                        else:
                            consecutive_waiting = 0  # Reset si état progresse
                        
                        if state == 'success':
                            # Extraire l'URL de l'image
                            result_json_str = data.get('resultJson', '{}')
                            try:
                                result_json = json.loads(result_json_str)
                                image_urls = result_json.get('resultUrls', [])
                                
                                if not image_urls:
                                    return None, "Pas d'URL d'image dans le résultat"
                                
                                image_url = image_urls[0]
                                print(f"[IMAGE-KIE] 📥 Téléchargement: {image_url[:50]}...")
                                
                                # Télécharger l'image
                                async with session.get(
                                    image_url,
                                    timeout=aiohttp.ClientTimeout(total=60)
                                ) as img_response:
                                    if img_response.status == 200:
                                        image_bytes = await img_response.read()
                                        print(f"[IMAGE-KIE] ✅ Image générée ({len(image_bytes)} bytes)")
                                        return image_bytes, None
                                    else:
                                        return None, f"Erreur téléchargement image: {img_response.status}"
                                        
                            except json.JSONDecodeError:
                                return None, "Format resultJson invalide"
                        
                        elif state == 'fail':
                            fail_msg = data.get('failMsg', 'Génération échouée')
                            print(f"[IMAGE-KIE] ❌ Échec: {fail_msg}")
                            return None, f"Génération échouée: {fail_msg}"
                        
                        # États intermédiaires: waiting, queuing, generating
                        # Continuer le polling
                
                return None, "Timeout: génération trop longue"
                    
        except asyncio.TimeoutError:
            return None, "Délai d'attente dépassé (Timeout)"
        except Exception as e:
            print(f"[IMAGE-KIE] ❌ Erreur: {e}")
            return None, str(e)


class WaveSpeedImageProvider(ImageProviderBase):
    """
    Provider WaveSpeed.ai - Multi-modèles Unfiltered/Spicy
    
    API Base: https://api.wavespeed.ai/api/v3/
    Pattern: POST task → Poll result → Download output
    
    Modèles Text-to-Image Unfiltered/Spicy:
    - female-human: Personnages réalistes, $0.015/img
    - prefect-pony-xl: Anime/artistique Unfiltered, $0.015/img
    - jib-mix-qwen-image: Portraits réalistes, $0.02/img
    - stability-ai/sdxl: Stable Diffusion XL, $0.01/img
    
    Modèles Image-to-Image Unfiltered/Spicy:
    - z-image-turbo-i2i: Ultra-rapide, $0.005/img
    - higgsfield-soul-i2i: Réaliste/artistique, $0.025/img
    - flux-kontext-dev: Edition instruite, $0.025/img
    - image-face-swap: Face swap, $0.005/img
    - image-head-swap: Head swap, $0.008/img
    
    Documentation: https://wavespeed.ai/docs
    """
    
    BASE_URL = "https://api.wavespeed.ai/api/v3"
    POLL_INTERVAL = 2.0  # secondes entre chaque poll
    MAX_POLLS = 90  # max 3 minutes d'attente
    
    # Modèles Text-to-Image Unfiltered/Spicy
    MODELS = {
        "wavespeed-ai/female-human": {
            "nsfw": True,
            "credits": 0.015,  # $0.015/img
            "type": "text2img",
            "description": "� Personnages réalistes"
        },
        "wavespeed-ai/prefect-pony-xl": {
            "nsfw": True,
            "credits": 0.015,
            "type": "text2img",
            "description": "🎨 Anime/artistique style Pony"
        },
        "wavespeed-ai/jib-mix-qwen-image/text-to-image": {
            "nsfw": True,
            "credits": 0.02,
            "type": "text2img",
            "description": "📸 Portraits photo-réalistes"
        },
        "stability-ai/sdxl": {
            "nsfw": True,
            "credits": 0.01,
            "type": "text2img",
            "description": "🎯 Stable Diffusion XL (Unfiltered)"
        },
        "wavespeed-ai/flux-schnell": {
            "nsfw": True,
            "credits": 0.003,
            "type": "text2img",
            "description": "⚡ Flux Schnell rapide"
        },
        "wavespeed-ai/flux-dev": {
            "nsfw": True,
            "credits": 0.025,
            "type": "text2img",
            "description": "🔧 Flux Dev qualité"
        },
        "wavespeed-ai/flux-1.1-pro": {
            "nsfw": True,
            "credits": 0.04,
            "type": "text2img",
            "description": "Flux 1.1 Pro"
        },
        "wavespeed-ai/flux-1.1-pro-ultra": {
            "nsfw": True,
            "credits": 0.06,
            "type": "text2img",
            "description": "Flux 1.1 Pro Ultra"
        },
        "wavespeed-ai/flux-2-dev": {
            "nsfw": True,
            "credits": 0.03,
            "type": "text2img",
            "description": "Flux 2 Dev"
        },
        "wavespeed-ai/flux-2-pro": {
            "nsfw": True,
            "credits": 0.05,
            "type": "text2img",
            "description": "Flux 2 Pro"
        },
        "wavespeed-ai/flux-2-max": {
            "nsfw": True,
            "credits": 0.06,
            "type": "text2img",
            "description": "Flux 2 Max"
        },
        "wavespeed-ai/qwen-image/text-to-image": {
            "nsfw": True,
            "credits": 0.02,
            "type": "text2img",
            "description": "Qwen Image 20B"
        },
        "wavespeed-ai/seedream-v4": {
            "nsfw": True,
            "credits": 0.025,
            "type": "text2img",
            "description": "Seedream V4"
        },
        "wavespeed-ai/z-image/turbo": {
            "nsfw": True,
            "credits": 0.005,
            "type": "text2img",
            "description": "⚡ Z-Image Turbo (ultra-rapide, $0.005)"
        },
        "wavespeed-ai/kolors": {
            "nsfw": True,
            "credits": 0.015,
            "type": "text2img",
            "description": "🎨 Kolors (qualité/vitesse)"
        },
        "stability-ai/sd3.5-large": {
            "nsfw": True,
            "credits": 0.065,
            "type": "text2img",
            "description": "🎯 Stable Diffusion 3.5 Large"
        },
        "stability-ai/sd3.5-large-turbo": {
            "nsfw": True,
            "credits": 0.04,
            "type": "text2img",
            "description": "⚡ SD 3.5 Large Turbo"
        },
        "stability-ai/sd3.5-medium": {
            "nsfw": True,
            "credits": 0.035,
            "type": "text2img",
            "description": "🎯 SD 3.5 Medium"
        },
        "stability-ai/sd3-turbo": {
            "nsfw": True,
            "credits": 0.04,
            "type": "text2img",
            "description": "⚡ SD 3 Turbo"
        },
        "recraft-ai/recraft-v3": {
            "nsfw": True,
            "credits": 0.04,
            "type": "text2img",
            "description": "🎨 Recraft V3 (design/illustration)"
        },
        "bytedance/seedream-v4.5": {
            "nsfw": True,
            "credits": 0.032,
            "type": "text2img",
            "description": "🌱 Seedream V4.5 (4K)"
        },
        "bytedance/seedream-v4": {
            "nsfw": True,
            "credits": 0.025,
            "type": "text2img",
            "description": "🌱 Seedream V4"
        },
        "bytedance/seedream-v3.1": {
            "nsfw": True,
            "credits": 0.02,
            "type": "text2img",
            "description": "🌱 Seedream V3.1"
        },
        "bytedance/seedream-v3": {
            "nsfw": True,
            "credits": 0.015,
            "type": "text2img",
            "description": "🌱 Seedream V3"
        }
    }
    
    # Modèles Image-to-Image Unfiltered/Spicy
    IMG2IMG_MODELS = {
        "wavespeed-ai/z-image-turbo/image-to-image": {
            "nsfw": True,
            "credits": 0.005,  # $0.005/img - Ultra pas cher!
            "input_key": "image",
            "type": "img2img",
            "max_images": 1,
            "description": "⚡ Ultra-rapide et pas cher",
            "params": {
                "size": {"options": ["512*512", "768*768", "1024*1024", "1024*768", "768*1024", "1280*720", "720*1280", "1536*1024", "1024*1536"], "default": "1024*1024", "label": "Taille"},
                "strength": {"range": [0.1, 1.0], "default": 0.75, "step": 0.05, "label": "Force"},
                "seed": {"range": [-1, 2147483647], "default": -1, "label": "Seed"},
                "output_format": {"options": ["jpeg", "png", "webp"], "default": "jpeg", "label": "Format"}
            }
        },
        "higgsfield/soul/image-to-image": {
            "nsfw": True,
            "credits": 0.025,  # $0.025/img
            "input_key": "image",
            "type": "img2img",
            "max_images": 1,
            "description": "🎭 Style réaliste/artistique",
            "params": {
                "size": {"options": ["512*512", "768*768", "1024*1024", "1280*720", "720*1280"], "default": "1024*1024", "label": "Taille"},
                "strength": {"range": [0.1, 1.0], "default": 0.7, "step": 0.05, "label": "Force"},
                "seed": {"range": [-1, 2147483647], "default": -1, "label": "Seed"},
                "output_format": {"options": ["jpeg", "png", "webp"], "default": "jpeg", "label": "Format"}
            }
        },
        "wavespeed-ai/flux-kontext-dev": {
            "nsfw": True,
            "credits": 0.025,  # $0.025/img
            "input_key": "image_url",
            "type": "img2img",
            "max_images": 1,
            "description": "✏️ Edition par instruction",
            "params": {
                "size": {"options": ["512*512", "768*768", "1024*1024", "1280*720", "720*1280", "1536*1024", "1024*1536"], "default": "1024*1024", "label": "Taille"},
                "guidance_scale": {"range": [1.0, 20.0], "default": 3.5, "step": 0.5, "label": "Guidance"},
                "num_inference_steps": {"range": [10, 50], "default": 28, "label": "Steps"},
                "seed": {"range": [-1, 2147483647], "default": -1, "label": "Seed"},
                "output_format": {"options": ["jpeg", "png", "webp"], "default": "jpeg", "label": "Format"}
            }
        },
        "wavespeed-ai/flux-kontext-dev-ultra-fast": {
            "nsfw": True,
            "credits": 0.015,
            "input_key": "image_url",
            "type": "img2img",
            "max_images": 1,
            "description": "✏️⚡ Kontext Dev Ultra-Fast",
            "params": {
                "size": {"options": ["512*512", "768*768", "1024*1024", "1280*720", "720*1280"], "default": "1024*1024", "label": "Taille"},
                "guidance_scale": {"range": [1.0, 20.0], "default": 3.5, "step": 0.5, "label": "Guidance"},
                "seed": {"range": [-1, 2147483647], "default": -1, "label": "Seed"},
                "output_format": {"options": ["jpeg", "png", "webp"], "default": "jpeg", "label": "Format"}
            }
        },
        "wavespeed-ai/flux-kontext-pro": {
            "nsfw": True,
            "credits": 0.04,
            "input_key": "image_url",
            "type": "img2img",
            "max_images": 1,
            "description": "✏️ Kontext Pro (haute qualite)",
            "params": {
                "size": {"options": ["512*512", "768*768", "1024*1024", "1280*720", "720*1280", "1536*1024", "1024*1536"], "default": "1024*1024", "label": "Taille"},
                "guidance_scale": {"range": [1.0, 20.0], "default": 3.5, "step": 0.5, "label": "Guidance"},
                "num_inference_steps": {"range": [10, 50], "default": 28, "label": "Steps"},
                "seed": {"range": [-1, 2147483647], "default": -1, "label": "Seed"},
                "output_format": {"options": ["jpeg", "png", "webp"], "default": "jpeg", "label": "Format"}
            }
        },
        "wavespeed-ai/flux-kontext-max": {
            "nsfw": True,
            "credits": 0.06,
            "input_key": "image_url",
            "type": "img2img",
            "max_images": 1,
            "description": "✏️ Kontext Max (qualite maximale)",
            "params": {
                "size": {"options": ["512*512", "768*768", "1024*1024", "1280*720", "720*1280", "1536*1024", "1024*1536"], "default": "1024*1024", "label": "Taille"},
                "guidance_scale": {"range": [1.0, 20.0], "default": 3.5, "step": 0.5, "label": "Guidance"},
                "num_inference_steps": {"range": [10, 50], "default": 28, "label": "Steps"},
                "seed": {"range": [-1, 2147483647], "default": -1, "label": "Seed"},
                "output_format": {"options": ["jpeg", "png", "webp"], "default": "jpeg", "label": "Format"}
            }
        },
        "wavespeed-ai/image-face-swap": {
            "nsfw": True,
            "credits": 0.005,  # $0.005/img
            "input_key": "target_image",
            "secondary_input_key": "source_image",  # Visage source à swapper
            "type": "img2img",
            "max_images": 2,  # target + source
            "description": "🎭 Face Swap (2 images)",
            "params": {}
        },
        "wavespeed-ai/image-head-swap": {
            "nsfw": True,
            "credits": 0.008,  # $0.008/img
            "input_key": "target_image",
            "secondary_input_key": "source_image",
            "type": "img2img",
            "max_images": 2,
            "description": "👤 Head Swap complet",
            "params": {}
        },
        "wavespeed-ai/wan-2.2/image-to-image": {
            "nsfw": True,
            "credits": 0.02,  # $0.02/img
            "input_key": "image",
            "type": "img2img",
            "max_images": 1,
            "description": "🌊 Wan 2.2 Image Edit",
            "params": {
                "size": {"options": ["512*512", "768*768", "1024*1024", "1280*720", "720*1280"], "default": "1024*1024", "label": "Taille"},
                "strength": {"range": [0.1, 1.0], "default": 0.8, "step": 0.05, "label": "Force"},
                "seed": {"range": [-1, 2147483647], "default": -1, "label": "Seed"},
                "output_format": {"options": ["jpeg", "png", "webp"], "default": "jpeg", "label": "Format"}
            }
        },
        "wavespeed-ai/qwen-image-edit": {
            "nsfw": True,
            "credits": 0.02,  # $0.02/img
            "input_key": "image",
            "type": "img2img",
            "max_images": 1,
            "description": "🧠 Qwen Image Edit",
            "params": {
                "size": {"options": ["512*512", "768*768", "1024*1024", "1280*720", "720*1280", "1536*1024", "1024*1536"], "default": "1024*1024", "label": "Taille"},
                "seed": {"range": [-1, 2147483647], "default": -1, "label": "Seed"},
                "output_format": {"options": ["jpeg", "png", "webp"], "default": "jpeg", "label": "Format"}
            }
        },
        "decart/lucy-edit-dev": {
            "nsfw": True,
            "credits": 0.015,  # $0.015/img
            "input_key": "image",
            "type": "img2img",
            "max_images": 1,
            "description": "🎬 Lucy Edit (Decart)",
            "params": {
                "size": {"options": ["512*512", "768*768", "1024*1024"], "default": "1024*1024", "label": "Taille"},
                "strength": {"range": [0.1, 1.0], "default": 0.8, "step": 0.05, "label": "Force"},
                "seed": {"range": [-1, 2147483647], "default": -1, "label": "Seed"},
                "output_format": {"options": ["jpeg", "png", "webp"], "default": "jpeg", "label": "Format"}
            }
        },
        "wavespeed-ai/flux-fill-dev": {
            "nsfw": True,
            "credits": 0.025,
            "input_key": "image",
            "type": "img2img",
            "max_images": 1,
            "description": "🖌️ Inpainting et remplissage intelligent",
            "params": {
                "size": {"options": ["512*512", "768*768", "1024*1024", "1280*720", "720*1280"], "default": "1024*1024", "label": "Taille"},
                "seed": {"range": [-1, 2147483647], "default": -1, "label": "Seed"},
                "output_format": {"options": ["jpeg", "png", "webp"], "default": "jpeg", "label": "Format"}
            }
        },
        "wavespeed-ai/infinite-you": {
            "nsfw": True,
            "credits": 0.02,
            "input_key": "image",
            "type": "img2img",
            "max_images": 1,
            "description": "🔄 Swap de personnage/visage avancé",
            "params": {
                "size": {"options": ["512*512", "768*768", "1024*1024"], "default": "1024*1024", "label": "Taille"},
                "seed": {"range": [-1, 2147483647], "default": -1, "label": "Seed"},
                "output_format": {"options": ["jpeg", "png", "webp"], "default": "jpeg", "label": "Format"}
            }
        },
        "wavespeed-ai/seedream-v4": {
            "nsfw": True,
            "credits": 0.025,
            "input_key": "image",
            "type": "img2img",
            "max_images": 1,
            "description": "🌱 Seedream V4 (WaveSpeed)",
            "params": {
                "size": {"options": ["512*512", "768*768", "1024*1024", "1280*720", "720*1280"], "default": "1024*1024", "label": "Taille"},
                "strength": {"range": [0.1, 1.0], "default": 0.75, "step": 0.05, "label": "Force"},
                "seed": {"range": [-1, 2147483647], "default": -1, "label": "Seed"},
                "output_format": {"options": ["jpeg", "png", "webp"], "default": "jpeg", "label": "Format"}
            }
        },
        "bytedance/seedream-4.5": {
            "nsfw": True,
            "credits": 0.032,
            "input_key": "image",
            "type": "img2img",
            "max_images": 1,
            "description": "🌱 Seedream 4.5 (WaveSpeed)",
            "params": {
                "size": {"options": ["512*512", "768*768", "1024*1024", "1280*720", "720*1280", "1536*1024", "1024*1536"], "default": "1024*1024", "label": "Taille"},
                "strength": {"range": [0.1, 1.0], "default": 0.75, "step": 0.05, "label": "Force"},
                "seed": {"range": [-1, 2147483647], "default": -1, "label": "Seed"},
                "output_format": {"options": ["jpeg", "png", "webp"], "default": "jpeg", "label": "Format"}
            }
        },
        "bytedance/seedream-v3.1": {
            "nsfw": True,
            "credits": 0.02,
            "input_key": "image",
            "type": "img2img",
            "max_images": 1,
            "description": "🌱 Seedream V3.1 classique",
            "params": {
                "size": {"options": ["512*512", "768*768", "1024*1024"], "default": "1024*1024", "label": "Taille"},
                "strength": {"range": [0.1, 1.0], "default": 0.75, "step": 0.05, "label": "Force"},
                "seed": {"range": [-1, 2147483647], "default": -1, "label": "Seed"},
                "output_format": {"options": ["jpeg", "png", "webp"], "default": "jpeg", "label": "Format"}
            }
        },
        "bytedance/seedream-v4.5/edit": {
            "nsfw": True,
            "credits": 0.04,  # $0.04/img selon docs officielles
            "input_key": "images",
            "type": "img2img",
            "max_images": 10,
            "is_array": True,
            "requires_url_upload": True,  # Nécessite upload vers WaveSpeed Media API
            "description": "🌱 Seedream V4.5 Edit (min 2K, jusqu'à 4K)",
            "params": {
                "size": {"options": ["2048*2048", "2560*1440", "1440*2560", "3072*3072", "3840*2160", "2160*3840", "4096*4096"], "default": "2048*2048", "label": "Taille"},
                "seed": {"range": [-1, 2147483647], "default": -1, "label": "Seed"},
                "output_format": {"options": ["jpeg", "png", "webp"], "default": "jpeg", "label": "Format"}
            }
        },
        "bytedance/seedream-v4/edit": {
            "nsfw": True,
            "credits": 0.035,
            "input_key": "images",
            "type": "img2img",
            "max_images": 10,
            "is_array": True,
            "requires_url_upload": True,  # Nécessite upload vers WaveSpeed Media API
            "description": "🌱 Seedream V4 Edit (min 2K)",
            "params": {
                "size": {"options": ["2048*2048", "2560*1440", "1440*2560", "3072*3072"], "default": "2048*2048", "label": "Taille"},
                "seed": {"range": [-1, 2147483647], "default": -1, "label": "Seed"},
                "output_format": {"options": ["jpeg", "png", "webp"], "default": "jpeg", "label": "Format"}
            }
        },
        "bytedance/seedream-v4.5/edit-sequential": {
            "nsfw": True,
            "credits": 0.04,
            "input_key": "image",
            "type": "img2img",
            "max_images": 4,
            "description": "🌱 Seedream V4.5 Edit Sequential (multi-images)",
            "params": {
                "size": {"options": ["512*512", "768*768", "1024*1024", "1536*1024", "1024*1536"], "default": "1024*1024", "label": "Taille"},
                "strength": {"range": [0.1, 1.0], "default": 0.75, "step": 0.05, "label": "Force"},
                "seed": {"range": [-1, 2147483647], "default": -1, "label": "Seed"},
                "output_format": {"options": ["jpeg", "png", "webp"], "default": "jpeg", "label": "Format"}
            }
        },
        "bytedance/seedream-v5.0-lite/edit": {
            "nsfw": True,
            "credits": 0.03,
            "input_key": "images",
            "type": "img2img",
            "max_images": 10,
            "is_array": True,
            "requires_url_upload": True,
            "description": "🌱 Seedream V5.0 Lite Edit (min 2K)",
            "params": {
                "size": {"options": ["1024*1024", "1536*1024", "1024*1536", "2048*2048", "2560*1440", "1440*2560"], "default": "1024*1024", "label": "Taille"},
                "seed": {"range": [-1, 2147483647], "default": -1, "label": "Seed"},
                "output_format": {"options": ["jpeg", "png", "webp"], "default": "jpeg", "label": "Format"}
            }
        },
        "bytedance/seedream-v5.0-lite/edit-sequential": {
            "nsfw": True,
            "credits": 0.03,
            "input_key": "image",
            "type": "img2img",
            "max_images": 4,
            "description": "🌱 Seedream V5.0 Lite Edit Sequential",
            "params": {
                "size": {"options": ["512*512", "768*768", "1024*1024", "1536*1024", "1024*1536"], "default": "1024*1024", "label": "Taille"},
                "strength": {"range": [0.1, 1.0], "default": 0.75, "step": 0.05, "label": "Force"},
                "seed": {"range": [-1, 2147483647], "default": -1, "label": "Seed"},
                "output_format": {"options": ["jpeg", "png", "webp"], "default": "jpeg", "label": "Format"}
            }
        },
        "bytedance/seedream-v4/edit-sequential": {
            "nsfw": True,
            "credits": 0.035,
            "input_key": "image",
            "type": "img2img",
            "max_images": 4,
            "description": "🌱 Seedream V4 Edit Sequential (multi-images)",
            "params": {
                "size": {"options": ["512*512", "768*768", "1024*1024", "1536*1024", "1024*1536"], "default": "1024*1024", "label": "Taille"},
                "strength": {"range": [0.1, 1.0], "default": 0.75, "step": 0.05, "label": "Force"},
                "seed": {"range": [-1, 2147483647], "default": -1, "label": "Seed"},
                "output_format": {"options": ["jpeg", "png", "webp"], "default": "jpeg", "label": "Format"}
            }
        },
        "bytedance/seededit-v3": {
            "nsfw": True,
            "credits": 0.018,
            "input_key": "image",
            "type": "img2img",
            "max_images": 1,
            "description": "🌱 SeedEdit V3",
            "params": {
                "size": {"options": ["512*512", "768*768", "1024*1024"], "default": "1024*1024", "label": "Taille"},
                "strength": {"range": [0.1, 1.0], "default": 0.75, "step": 0.05, "label": "Force"},
                "seed": {"range": [-1, 2147483647], "default": -1, "label": "Seed"},
                "output_format": {"options": ["jpeg", "png", "webp"], "default": "jpeg", "label": "Format"}
            }
        },
        "alibaba/wan-2.5/image-edit": {
            "nsfw": True,
            "credits": 0.025,
            "input_key": "image",
            "type": "img2img",
            "max_images": 1,
            "description": "🌊 Wan 2.5 Image Edit (Alibaba)",
            "params": {
                "size": {"options": ["512*512", "768*768", "1024*1024", "1280*720", "720*1280"], "default": "1024*1024", "label": "Taille"},
                "strength": {"range": [0.1, 1.0], "default": 0.75, "step": 0.05, "label": "Force"},
                "seed": {"range": [-1, 2147483647], "default": -1, "label": "Seed"},
                "output_format": {"options": ["jpeg", "png", "webp"], "default": "jpeg", "label": "Format"}
            }
        },
        "google/nano-banana-pro/edit": {
            "nsfw": False,
            "credits": 0.05,
            "input_key": "image",
            "type": "img2img",
            "max_images": 1,
            "description": "🍌 Nano Banana Pro Edit (Google)",
            "params": {
                "size": {"options": ["512*512", "768*768", "1024*1024", "1536*1024", "1024*1536"], "default": "1024*1024", "label": "Taille"},
                "seed": {"range": [-1, 2147483647], "default": -1, "label": "Seed"},
                "output_format": {"options": ["jpeg", "png", "webp"], "default": "jpeg", "label": "Format"}
            }
        },
        "google/nano-banana-pro/edit-ultra": {
            "nsfw": False,
            "credits": 0.08,
            "input_key": "image",
            "type": "img2img",
            "max_images": 1,
            "description": "🍌 Nano Banana Pro Edit Ultra (Google, 4K)",
            "params": {
                "size": {"options": ["1024*1024", "1536*1024", "1024*1536", "2048*2048"], "default": "1024*1024", "label": "Taille"},
                "seed": {"range": [-1, 2147483647], "default": -1, "label": "Seed"},
                "output_format": {"options": ["jpeg", "png", "webp"], "default": "jpeg", "label": "Format"}
            }
        },
        "wavespeed-ai/qwen-image/edit-2511-lora": {
            "nsfw": True,
            "credits": 0.022,
            "input_key": "image",
            "type": "img2img",
            "max_images": 1,
            "description": "🧠 Qwen Image Edit LoRA",
            "params": {
                "size": {"options": ["512*512", "768*768", "1024*1024", "1280*720", "720*1280"], "default": "1024*1024", "label": "Taille"},
                "seed": {"range": [-1, 2147483647], "default": -1, "label": "Seed"},
                "output_format": {"options": ["jpeg", "png", "webp"], "default": "jpeg", "label": "Format"}
            }
        },
        "wavespeed-ai/qwen-image/edit": {
            "nsfw": True,
            "credits": 0.02,
            "input_key": "images",
            "type": "img2img",
            "max_images": 10,
            "is_array": True,
            "requires_url_upload": True,
            "description": "🧠 Qwen Image Edit",
            "params": {
                "size": {"options": ["512*512", "768*768", "1024*1024", "1280*720", "720*1280", "1536*1024", "1024*1536"], "default": "1024*1024", "label": "Taille"},
                "seed": {"range": [-1, 2147483647], "default": -1, "label": "Seed"},
                "output_format": {"options": ["jpeg", "png", "webp"], "default": "jpeg", "label": "Format"}
            }
        },
        "wavespeed-ai/qwen-image-max/edit": {
            "nsfw": True,
            "credits": 0.04,
            "input_key": "images",
            "type": "img2img",
            "max_images": 10,
            "is_array": True,
            "requires_url_upload": True,
            "description": "🧠 Qwen Image Max Edit",
            "params": {
                "size": {"options": ["512*512", "768*768", "1024*1024", "1280*720", "720*1280", "1536*1024", "1024*1536"], "default": "1024*1024", "label": "Taille"},
                "seed": {"range": [-1, 2147483647], "default": -1, "label": "Seed"},
                "output_format": {"options": ["jpeg", "png", "webp"], "default": "jpeg", "label": "Format"}
            }
        },
        "wavespeed-ai/qwen-image-2.0-pro/edit": {
            "nsfw": True,
            "credits": 0.03,
            "input_key": "images",
            "type": "img2img",
            "max_images": 10,
            "is_array": True,
            "requires_url_upload": True,
            "description": "🧠 Qwen Image 2.0 Pro Edit",
            "params": {
                "size": {"options": ["512*512", "768*768", "1024*1024", "1280*720", "720*1280", "1536*1024", "1024*1536"], "default": "1024*1024", "label": "Taille"},
                "seed": {"range": [-1, 2147483647], "default": -1, "label": "Seed"},
                "output_format": {"options": ["jpeg", "png", "webp"], "default": "jpeg", "label": "Format"}
            }
        },
        "wavespeed-ai/qwen-image-2.0/edit": {
            "nsfw": True,
            "credits": 0.022,
            "input_key": "images",
            "type": "img2img",
            "max_images": 10,
            "is_array": True,
            "requires_url_upload": True,
            "description": "🧠 Qwen Image 2.0 Edit",
            "params": {
                "size": {"options": ["512*512", "768*768", "1024*1024", "1280*720", "720*1280", "1536*1024", "1024*1536"], "default": "1024*1024", "label": "Taille"},
                "seed": {"range": [-1, 2147483647], "default": -1, "label": "Seed"},
                "output_format": {"options": ["jpeg", "png", "webp"], "default": "jpeg", "label": "Format"}
            }
        },
        "wavespeed-ai/z-image/turbo-inpaint": {
            "nsfw": True,
            "credits": 0.006,
            "input_key": "image",
            "type": "img2img",
            "max_images": 1,
            "description": "⚡ Z-Image Turbo Inpaint",
            "params": {
                "size": {"options": ["512*512", "768*768", "1024*1024"], "default": "1024*1024", "label": "Taille"},
                "seed": {"range": [-1, 2147483647], "default": -1, "label": "Seed"},
                "output_format": {"options": ["jpeg", "png", "webp"], "default": "jpeg", "label": "Format"}
            }
        }
    }
    
    @property
    def name(self) -> str:
        return "WaveSpeed"
    
    @property
    def supports_nsfw(self) -> bool:
        return True  # WaveSpeed supporte le contenu Unfiltered
    
    def get_available_models(self) -> List[str]:
        """Retourne les modèles Text-to-Image"""
        return list(self.MODELS.keys())
    
    def get_img2img_models(self) -> List[str]:
        """Retourne les modèles Image-to-Image"""
        return list(self.IMG2IMG_MODELS.keys())
    
    def model_supports_seed(self, model_name: str) -> bool:
        """
        Vérifie si un modèle img2img supporte le paramètre seed.
        
        Args:
            model_name: Nom du modèle img2img
            
        Returns:
            bool: True si le modèle supporte seed
        """
        model_config = self.IMG2IMG_MODELS.get(model_name, {})
        params = model_config.get('params', {})
        return 'seed' in params
    
    async def fetch_live_models(self) -> Tuple[Optional[List[str]], Optional[str]]:
        """
        Récupère la liste des modèles en direct depuis l'API WaveSpeed.ai
        
        Returns:
            tuple: (list_models_text2img, error_message)
        """
        if not self.is_available:
            return None, "Clé API WaveSpeed manquante"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            print("[IMAGE-WAVESPEED] 🔄 Récupération liste modèles depuis API...")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/models",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"[IMAGE-WAVESPEED] ❌ Erreur API models ({response.status}): {error_text[:200]}")
                        return None, f"Erreur API: {response.status}"
                    
                    result = await response.json()
                    
                    if result.get('code') != 200:
                        error_msg = result.get('message', 'Erreur inconnue')
                        return None, f"Erreur WaveSpeed: {error_msg}"
                    
                    models_data = result.get('data', [])
                    
                    # Filtrer uniquement les modèles text-to-image
                    t2i_models = [
                        model['model_id']
                        for model in models_data
                        if model.get('type') == 'text-to-image'
                    ]
                    
                    print(f"[IMAGE-WAVESPEED] ✅ {len(t2i_models)} modèles T2I trouvés (sur {len(models_data)} total)")
                    return t2i_models, None
                    
        except asyncio.TimeoutError:
            return None, "Timeout lors de la récupération des modèles"
        except Exception as e:
            print(f"[IMAGE-WAVESPEED] ❌ Erreur fetch models: {e}")
            return None, str(e)
    
    async def fetch_live_img2img_models(self) -> Tuple[Optional[List[str]], Optional[str]]:
        """
        Récupère la liste des modèles Image-to-Image en direct depuis l'API WaveSpeed.ai
        
        Returns:
            tuple: (list_models_img2img, error_message)
        """
        if not self.is_available:
            return None, "Clé API WaveSpeed manquante"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            print("[IMAGE-WAVESPEED] 🔄 Récupération liste modèles I2I depuis API...")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/models",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"[IMAGE-WAVESPEED] ❌ Erreur API models ({response.status}): {error_text[:200]}")
                        return None, f"Erreur API: {response.status}"
                    
                    result = await response.json()
                    
                    if result.get('code') != 200:
                        error_msg = result.get('message', 'Erreur inconnue')
                        return None, f"Erreur WaveSpeed: {error_msg}"
                    
                    models_data = result.get('data', [])
                    
                    # Filtrer uniquement les modèles image-to-image
                    i2i_models = [
                        model['model_id']
                        for model in models_data
                        if model.get('type') == 'image-to-image'
                    ]
                    
                    print(f"[IMAGE-WAVESPEED] ✅ {len(i2i_models)} modèles I2I trouvés (sur {len(models_data)} total)")
                    return i2i_models, None
                    
        except asyncio.TimeoutError:
            return None, "Timeout lors de la récupération des modèles"
        except Exception as e:
            print(f"[IMAGE-WAVESPEED] ❌ Erreur fetch models I2I: {e}")
            return None, str(e)
    
    async def _upload_image_to_wavespeed(self, base64_data: str, filename: str = "image.png") -> Tuple[Optional[str], Optional[str]]:
        """
        Upload une image en base64 vers WaveSpeed Media Upload API
        
        Args:
            base64_data: Données image en base64 (avec ou sans préfixe data:image/...)
            filename: Nom du fichier pour l'upload
            
        Returns:
            tuple: (download_url, error_message)
        """
        if not self.is_available:
            return None, "Clé API WaveSpeed manquante"
        
        # Nettoyer le base64 si nécessaire
        if base64_data.startswith('data:'):
            base64_data = base64_data.split(',', 1)[1]
        
        try:
            # Décoder le base64 en bytes pour l'upload binaire
            image_bytes = base64.b64decode(base64_data)
            
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            
            # Créer le FormData avec le fichier
            form_data = aiohttp.FormData()
            form_data.add_field(
                'file',
                image_bytes,
                filename=filename,
                content_type='image/png'
            )
            
            print(f"[IMAGE-WAVESPEED] 📤 Upload image vers WaveSpeed ({len(image_bytes):,} bytes)...")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.BASE_URL}/media/upload/binary",
                    headers=headers,
                    data=form_data,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    
                    response_text = await response.text()
                    
                    if response.status != 200:
                        print(f"[IMAGE-WAVESPEED] ❌ Erreur upload ({response.status}): {response_text[:300]}")
                        return None, f"Erreur upload WaveSpeed: {response.status}"
                    
                    try:
                        result = json.loads(response_text)
                    except json.JSONDecodeError as je:
                        print(f"[IMAGE-WAVESPEED] ❌ JSON invalide: {je}")
                        return None, f"Réponse non-JSON: {response_text[:100]}"
                    
                    if result.get('code') == 200:
                        data = result.get('data', {})
                        download_url = data.get('download_url')
                        if download_url:
                            print(f"[IMAGE-WAVESPEED] ✅ Upload réussi: {download_url[:80]}...")
                            return download_url, None
                        print(f"[IMAGE-WAVESPEED] ⚠️ Pas de download_url dans: {data}")
                        return None, "Pas d'URL dans la réponse"
                    else:
                        error_msg = result.get('message', 'Erreur upload inconnue')
                        print(f"[IMAGE-WAVESPEED] ❌ Échec API: {error_msg}")
                        return None, f"Erreur WaveSpeed: {error_msg}"
                        
        except Exception as e:
            print(f"[IMAGE-WAVESPEED] ❌ Exception upload: {e}")
            return None, f"Exception upload: {str(e)}"
    
    async def _poll_for_result(self, session, prediction_id: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Poll le résultat d'une prédiction WaveSpeed
        
        Returns:
            tuple: (output_url, error_message)
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        result_url = f"{self.BASE_URL}/predictions/{prediction_id}/result"
        
        for poll_count in range(self.MAX_POLLS):
            # 🛑 STOP: Vérifier si arrêt demandé
            try:
                from stop_signal import is_stop_requested
                if is_stop_requested():
                    print(f"[IMAGE-WAVESPEED] 🛑 Génération interrompue par l'utilisateur au poll #{poll_count + 1}")
                    return None, "⏹️ Génération interrompue par l'utilisateur"
            except ImportError:
                pass  # Module non disponible, continuer
            
            await asyncio.sleep(self.POLL_INTERVAL)
            
            try:
                async with session.get(
                    result_url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status != 200:
                        continue  # Réessayer
                    
                    result = await response.json()
                    data = result.get('data', {})
                    status = data.get('status', '')
                    
                    print(f"[IMAGE-WAVESPEED] 🔄 Poll #{poll_count + 1}: {status}")
                    
                    if status == 'completed':
                        outputs = data.get('outputs', [])
                        if outputs:
                            return outputs[0], None
                        return None, "Pas d'output dans la réponse"
                    
                    elif status == 'failed':
                        error = data.get('error', 'Génération échouée')
                        return None, f"Échec: {error}"
                    
                    # Statuts intermédiaires: created, processing
                    # Continuer le polling
                    
            except Exception as e:
                print(f"[IMAGE-WAVESPEED] ⚠️ Erreur poll #{poll_count + 1}: {e}")
                continue
        
        return None, "Timeout: génération trop longue"
    
    async def generate(
        self,
        prompt: str,
        model: str,
        width: int,
        height: int,
        **kwargs
    ) -> Tuple[Optional[bytes], Optional[str]]:
        """Génère une image Text-to-Image"""
        if not self.is_available:
            return None, "Clé API WaveSpeed manquante"
        
        model = model or "wavespeed-ai/female-human"
        model_config = self.MODELS.get(model, list(self.MODELS.values())[0])
        
        # Convertir width/height en format WaveSpeed
        size = f"{width}*{height}"
        
        # Payload WaveSpeed
        payload = {
            "prompt": prompt,
            "size": size,
            "seed": kwargs.get("seed", -1),
            "output_format": kwargs.get("output_format", "jpeg"),
            "enable_base64_output": True,
            "enable_sync_mode": False
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            credits = model_config.get('credits', '?')
            print(f"[IMAGE-WAVESPEED] 🚀 T2I avec {model} (~${credits})...")
            
            async with aiohttp.ClientSession() as session:
                # Soumettre la tâche
                async with session.post(
                    f"{self.BASE_URL}/{model}",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"[IMAGE-WAVESPEED] ❌ Erreur ({response.status}): {error_text[:200]}")
                        return None, f"Erreur WaveSpeed: {response.status}"
                    
                    result = await response.json()
                    
                    if result.get('code') != 200:
                        error_msg = result.get('message', 'Erreur inconnue')
                        return None, f"Erreur WaveSpeed: {error_msg}"
                    
                    data = result.get('data', {})
                    prediction_id = data.get('id')
                    
                    if not prediction_id:
                        return None, "Pas d'ID de prédiction"
                    
                    print(f"[IMAGE-WAVESPEED] 📋 Tâche créée: {prediction_id}")
                
                # Poll pour le résultat
                output_url_or_b64, error = await self._poll_for_result(session, prediction_id)
                
                if error:
                    return None, error
                
                # Si c'est une URL, télécharger
                if output_url_or_b64.startswith('http'):
                    async with session.get(
                        output_url_or_b64,
                        timeout=aiohttp.ClientTimeout(total=60)
                    ) as img_response:
                        if img_response.status == 200:
                            image_bytes = await img_response.read()
                            print(f"[IMAGE-WAVESPEED] ✅ Image générée ({len(image_bytes)} bytes)")
                            return image_bytes, None
                        return None, f"Erreur téléchargement: {img_response.status}"
                else:
                    # C'est du base64 - nettoyer le préfixe data:image/...;base64, si présent
                    b64_data = output_url_or_b64
                    if b64_data.startswith('data:'):
                        if ';base64,' in b64_data:
                            b64_data = b64_data.split(';base64,', 1)[1]
                        elif ',' in b64_data:
                            b64_data = b64_data.split(',', 1)[1]
                    
                    image_bytes = base64.b64decode(b64_data)
                    print(f"[IMAGE-WAVESPEED] ✅ Image générée ({len(image_bytes)} bytes)")
                    return image_bytes, None
                    
        except asyncio.TimeoutError:
            return None, "Timeout"
        except Exception as e:
            print(f"[IMAGE-WAVESPEED] ❌ Erreur: {e}")
            return None, str(e)
    
    async def generate_img2img(
        self,
        prompt: str,
        source_image_base64: str = None,
        source_images_base64: List[str] = None,
        model: str = "wavespeed-ai/z-image-turbo/image-to-image",
        width: int = 1024,
        height: int = 1024,
        **kwargs
    ) -> Tuple[Optional[bytes], Optional[str]]:
        """Génère une image Image-to-Image"""
        if not self.is_available:
            return None, "Clé API WaveSpeed manquante"
        
        # Gestion compatibilité single/multi image
        images_list = []
        if source_images_base64:
            images_list = source_images_base64
        elif source_image_base64:
            images_list = [source_image_base64]
        
        if not images_list:
            return None, "Aucune image source fournie"
        
        if model in self.IMG2IMG_MODELS:
            model_config = self.IMG2IMG_MODELS[model]
        else:
            # Fallback : config par defaut pour modeles decouverts via refresh API
            print(f"[IMAGE-WAVESPEED] ⚠ Modele {model} non repertorie - utilisation config par defaut")
            
            # Heuristique: les modeles WaveSpeed recents avec /edit utilisent "images" (array+upload)
            # EXCEPTIONS connues:
            #   - wavespeed-ai/flux-*/edit → image_url (URL simple, comme kontext)
            #   - wavespeed-ai/qwen-image-edit → image (base64, ancien modele)
            model_path = model.lower()
            is_flux_edit = model_path.startswith('wavespeed-ai/flux-') and '/edit' in model_path
            needs_array = (
                not is_flux_edit and (
                    model_path.endswith('/edit') or
                    '/edit-' in model_path or
                    ('seedream' in model_path and 'edit' in model_path)
                )
            )
            needs_url = is_flux_edit  # Flux /edit: URL simple comme kontext
            
            if needs_array:
                print(f"[IMAGE-WAVESPEED] ⚠ Heuristique: modele edit detecte - mode array+upload")
                model_config = {
                    "nsfw": True,
                    "credits": "?",
                    "input_key": "images",
                    "type": "img2img",
                    "max_images": 10,
                    "is_array": True,
                    "requires_url_upload": True,
                    "description": f"🔧 {model} (auto-detecte, edit)",
                    "params": {
                        "size": {"options": ["512*512", "768*768", "1024*1024", "1280*720", "720*1280", "1536*1024", "1024*1536"], "default": "1024*1024", "label": "Taille"},
                        "seed": {"range": [-1, 2147483647], "default": -1, "label": "Seed"},
                        "output_format": {"options": ["jpeg", "png", "webp"], "default": "jpeg", "label": "Format"}
                    }
                }
            elif needs_url:
                print(f"[IMAGE-WAVESPEED] ⚠ Heuristique: modele flux/edit detecte - mode image_url")
                model_config = {
                    "nsfw": True,
                    "credits": "?",
                    "input_key": "image_url",
                    "type": "img2img",
                    "max_images": 1,
                    "description": f"🔧 {model} (auto-detecte, flux)",
                    "params": {
                        "size": {"options": ["512*512", "768*768", "1024*1024", "1280*720", "720*1280", "1536*1024", "1024*1536"], "default": "1024*1024", "label": "Taille"},
                        "guidance_scale": {"range": [1.0, 20.0], "default": 3.5, "step": 0.5, "label": "Guidance"},
                        "seed": {"range": [-1, 2147483647], "default": -1, "label": "Seed"},
                        "output_format": {"options": ["jpeg", "png", "webp"], "default": "jpeg", "label": "Format"}
                    }
                }
            else:
                model_config = {
                    "nsfw": True,
                    "credits": "?",
                    "input_key": "image",
                    "type": "img2img",
                    "max_images": 1,
                    "description": f"🔧 {model} (auto-detecte)",
                    "params": {
                        "size": {"options": ["512*512", "768*768", "1024*1024", "1280*720", "720*1280"], "default": "1024*1024", "label": "Taille"},
                        "seed": {"range": [-1, 2147483647], "default": -1, "label": "Seed"},
                        "output_format": {"options": ["jpeg", "png", "webp"], "default": "jpeg", "label": "Format"}
                    }
                }
        input_key = model_config.get("input_key", "image")
        model_params = model_config.get("params", {})
        is_array_input = model_config.get("is_array", False)
        
        # Note: la vérification min_pixels est maintenant gérée par l'auto-upscale
        # dans la section is_array_input ci-dessous
        
        # Nettoyer les images base64
        cleaned_images = []
        for img_b64 in images_list:
            if img_b64.startswith('data:'):
                img_b64 = img_b64.split(',', 1)[1]
            cleaned_images.append(img_b64)
        
        # Pour les modèles is_array (Seedream Edit), vérifier et upscaler si nécessaire
        # puis uploader vers WaveSpeed car ils attendent des URLs, pas du base64
        if is_array_input:
            # Seedream Edit requiert minimum 3686400 pixels (≈1920x1920)
            MIN_PIXELS_SEEDREAM = 3686400
            
            print(f"[IMAGE-WAVESPEED] 🔍 Vérification taille des {len(cleaned_images)} image(s)...")
            processed_images = []
            
            for i, img_b64 in enumerate(cleaned_images):
                try:
                    import io
                    from PIL import Image as PILImage
                    
                    img_data = base64.b64decode(img_b64)
                    img = PILImage.open(io.BytesIO(img_data))
                    original_pixels = img.width * img.height
                    
                    if original_pixels < MIN_PIXELS_SEEDREAM:
                        # Calculer le facteur d'upscale nécessaire
                        scale_factor = (MIN_PIXELS_SEEDREAM / original_pixels) ** 0.5
                        # Ajouter 10% de marge pour être sûr
                        scale_factor *= 1.1
                        
                        new_width = int(img.width * scale_factor)
                        new_height = int(img.height * scale_factor)
                        
                        print(f"[IMAGE-WAVESPEED] 📐 Image {i+1}: {img.width}x{img.height} ({original_pixels:,}px) → upscale vers {new_width}x{new_height} ({new_width*new_height:,}px)")
                        
                        # Upscaler avec LANCZOS (meilleure qualité)
                        img_upscaled = img.resize((new_width, new_height), PILImage.Resampling.LANCZOS)
                        
                        # Reconvertir en base64
                        buffer = io.BytesIO()
                        img_format = 'PNG' if img.mode == 'RGBA' else 'JPEG'
                        img_upscaled.save(buffer, format=img_format, quality=95)
                        processed_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
                        processed_images.append(processed_b64)
                        
                        print(f"[IMAGE-WAVESPEED] ✅ Image {i+1} upscalée avec succès")
                    else:
                        print(f"[IMAGE-WAVESPEED] ✅ Image {i+1}: {img.width}x{img.height} ({original_pixels:,}px) - OK")
                        processed_images.append(img_b64)
                        
                except Exception as e:
                    print(f"[IMAGE-WAVESPEED] ⚠️ Erreur vérification image {i+1}: {e} - utilisation originale")
                    processed_images.append(img_b64)
            
            # Uploader les images (upscalées ou originales) vers WaveSpeed
            print(f"[IMAGE-WAVESPEED] 📤 Upload {len(processed_images)} image(s) vers WaveSpeed...")
            uploaded_urls = []
            for i, img_b64 in enumerate(processed_images):
                url, error = await self._upload_image_to_wavespeed(img_b64, f"image_{i+1}.png")
                if error:
                    return None, f"Erreur upload image {i+1}: {error}"
                uploaded_urls.append(url)
            print(f"[IMAGE-WAVESPEED] ✅ {len(uploaded_urls)} image(s) uploadée(s)")
            image_input = uploaded_urls
        else:
            # Modèles classiques avec une seule image en base64
            image_input = cleaned_images[0]
        
        # Construire le payload - utiliser le default du modèle si disponible
        default_size = f"{width}*{height}"
        if "size" in model_params and "default" in model_params["size"]:
            default_size = model_params["size"]["default"]
        size = kwargs.get("size", default_size)
        
        # Log pour debug
        print(f"[IMAGE-WAVESPEED] 📐 Taille sortie: {size}")
        
        payload = {
            "prompt": prompt,
            input_key: image_input,  # WaveSpeed accepte base64 direct ou tableau
            "size": size,
            "seed": kwargs.get("seed", -1),
            "output_format": kwargs.get("output_format", "jpeg"),
            "enable_base64_output": True,
            "enable_sync_mode": False
        }
        
        # Ajouter les paramètres spécifiques au modèle
        if "strength" in model_params:
            payload["strength"] = kwargs.get("strength", model_params["strength"]["default"])
        if "guidance_scale" in model_params:
            payload["guidance_scale"] = kwargs.get("guidance_scale", model_params["guidance_scale"]["default"])
        if "num_inference_steps" in model_params:
            payload["num_inference_steps"] = kwargs.get("num_inference_steps", model_params["num_inference_steps"]["default"])
        
        # Gestion Face Swap / Head Swap (2 images) - seulement pour modèles non-array
        secondary_key = model_config.get("secondary_input_key")
        if secondary_key and len(cleaned_images) > 1 and not is_array_input:
            payload[secondary_key] = cleaned_images[1]
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            credits = model_config.get('credits', '?')
            print(f"[IMAGE-WAVESPEED] 🚀 I2I avec {model} (~${credits})...")
            
            async with aiohttp.ClientSession() as session:
                # Soumettre la tâche
                async with session.post(
                    f"{self.BASE_URL}/{model}",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"[IMAGE-WAVESPEED] ❌ Erreur ({response.status}): {error_text[:200]}")
                        return None, f"Erreur WaveSpeed: {response.status}"
                    
                    result = await response.json()
                    
                    if result.get('code') != 200:
                        error_msg = result.get('message', 'Erreur inconnue')
                        return None, f"Erreur WaveSpeed: {error_msg}"
                    
                    data = result.get('data', {})
                    prediction_id = data.get('id')
                    
                    if not prediction_id:
                        return None, "Pas d'ID de prédiction"
                    
                    print(f"[IMAGE-WAVESPEED] 📋 Tâche I2I créée: {prediction_id}")
                
                # Poll pour le résultat
                output_url_or_b64, error = await self._poll_for_result(session, prediction_id)
                
                if error:
                    return None, error
                
                # Télécharger ou décoder
                if output_url_or_b64.startswith('http'):
                    async with session.get(
                        output_url_or_b64,
                        timeout=aiohttp.ClientTimeout(total=60)
                    ) as img_response:
                        if img_response.status == 200:
                            image_bytes = await img_response.read()
                            print(f"[IMAGE-WAVESPEED] ✅ Image I2I générée ({len(image_bytes)} bytes)")
                            return image_bytes, None
                        return None, f"Erreur téléchargement: {img_response.status}"
                else:
                    # Nettoyer le préfixe data:image/...;base64, si présent
                    b64_data = output_url_or_b64
                    if b64_data.startswith('data:'):
                        # Format: data:image/jpeg;base64,/9j/...
                        if ';base64,' in b64_data:
                            b64_data = b64_data.split(';base64,', 1)[1]
                        elif ',' in b64_data:
                            b64_data = b64_data.split(',', 1)[1]
                    
                    image_bytes = base64.b64decode(b64_data)
                    print(f"[IMAGE-WAVESPEED] ✅ Image I2I générée ({len(image_bytes)} bytes)")
                    return image_bytes, None
                    
        except asyncio.TimeoutError:
            return None, "Timeout"
        except Exception as e:
            print(f"[IMAGE-WAVESPEED] ❌ Erreur I2I: {e}")
            return None, str(e)

    async def generate_img2img_batch(
        self,
        prompt: str,
        source_image_base64: str = None,
        source_images_base64: List[str] = None,
        model: str = "bytedance/seedream-v4.5/edit",
        batch_count: int = 1,
        base_seed: int = -1,
        seed_increment: int = 1,
        **kwargs
    ) -> Tuple[List[bytes], List[str]]:
        """
        Génère plusieurs images I2I en batch avec seeds incrémentaux.
        
        Args:
            prompt: Prompt de modification
            source_image_base64: Image source unique
            source_images_base64: Liste d'images sources
            model: Modèle I2I à utiliser
            batch_count: Nombre d'images à générer (1-6)
            base_seed: Seed de départ (-1 = aléatoire pour chaque)
            seed_increment: Écart entre chaque seed (+1, +2, etc.)
            **kwargs: Autres paramètres (size, output_format, etc.)
            
        Returns:
            tuple: (liste_images_bytes, liste_erreurs)
        """
        import random
        
        batch_count = max(1, min(6, batch_count))  # Clamp 1-6
        
        # Si seed -1, générer un seed aléatoire de base
        if base_seed == -1:
            base_seed = random.randint(1, 9999999)
        
        # Calculer les seeds pour chaque image
        seeds = [base_seed + (i * seed_increment) for i in range(batch_count)]
        
        print(f"[IMAGE-WAVESPEED-BATCH] 🎲 Batch {batch_count} images avec seeds: {seeds}")
        
        # Lancer toutes les générations en parallèle
        async def generate_single(seed: int, index: int):
            """Génère une seule image avec un seed donné"""
            print(f"[IMAGE-WAVESPEED-BATCH] 🚀 Image {index+1}/{batch_count} (seed={seed})...")
            kwargs_copy = kwargs.copy()
            kwargs_copy['seed'] = seed
            return await self.generate_img2img(
                prompt=prompt,
                source_image_base64=source_image_base64,
                source_images_base64=source_images_base64,
                model=model,
                **kwargs_copy
            )
        
        # Exécuter en parallèle
        tasks = [generate_single(seed, i) for i, seed in enumerate(seeds)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Séparer résultats et erreurs
        images = []
        errors = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                errors.append(f"Image {i+1}: {str(result)}")
                print(f"[IMAGE-WAVESPEED-BATCH] ❌ Image {i+1} échouée: {result}")
            elif isinstance(result, tuple):
                img_bytes, error = result
                if img_bytes:
                    images.append(img_bytes)
                    print(f"[IMAGE-WAVESPEED-BATCH] ✅ Image {i+1} OK ({len(img_bytes)} bytes)")
                else:
                    errors.append(f"Image {i+1}: {error}")
                    print(f"[IMAGE-WAVESPEED-BATCH] ❌ Image {i+1} échouée: {error}")
            else:
                errors.append(f"Image {i+1}: Résultat inattendu")
        
        print(f"[IMAGE-WAVESPEED-BATCH] 📊 Résultat: {len(images)}/{batch_count} images générées")
        
        return images, errors


class AtlasCloudImageProvider(ImageProviderBase):
    """
    Provider AtlasCloud.ai - Multi-modèles (300+ modèles IA unifiés)

    API Base: https://api.atlascloud.ai/api/v1
    Pattern: POST generateImage → predictionId → Poll getResult → URL finale

    Compatible OpenAI SDK — accès unifié à Seedream, FLUX, Qwen-Image, Ideogram, HiDream et plus
    Documentation: https://www.atlascloud.ai/docs/fr
    """

    BASE_URL = "https://api.atlascloud.ai/api/v1"
    POLL_INTERVAL = 2.0   # secondes entre chaque poll
    MAX_POLLS = 90        # max ~3 minutes d'attente

    # Modèles Text-to-Image (catalogue de fallback — mis à jour depuis l'API au runtime)
    MODELS = {
        "bytedance/seedream-v5.0-lite": {"nsfw": False, "description": "🌱 Seedream v5.0 Lite — ByteDance, haute qualité"},
        "bytedance/seedream-v5.0-lite/sequential": {"nsfw": False, "description": "🌱 Seedream v5.0 Lite Sequential — batch 15 images"},
        "bytedance/seedream-v4.5": {"nsfw": False, "description": "🌱 Seedream v4.5 — typographie et poster excellence"},
        "bytedance/seedream-v4.5/sequential": {"nsfw": False, "description": "🌱 Seedream v4.5 Sequential"},
        "bytedance/seedream-v4": {"nsfw": False, "description": "🌱 Seedream v4"},
        "bytedance/seedream-v4/sequential": {"nsfw": False, "description": "🌱 Seedream v4 Sequential"},
        "black-forest-labs/flux-dev": {"nsfw": False, "description": "⚡ FLUX Dev — haute fidélité"},
        "black-forest-labs/flux-schnell": {"nsfw": False, "description": "🚀 FLUX Schnell — ultra rapide"},
        "alibaba/wan-2.6/text-to-image": {"nsfw": False, "description": "🎨 Wan-2.6 Text-to-image — Alibaba"},
        "alibaba/wan-2.5/text-to-image": {"nsfw": False, "description": "🎨 Wan-2.5 Text-to-image"},
        "alibaba/qwen-image/text-to-image-max": {"nsfw": False, "description": "🏮 Qwen-Image Max — texte dans les images"},
        "alibaba/qwen-image/text-to-image-plus": {"nsfw": False, "description": "🏮 Qwen-Image Plus"},
        "atlascloud/qwen-image/text-to-image": {"nsfw": False, "description": "🏮 Qwen Image T2I — 20B MMDiT"},
        "google/imagen4": {"nsfw": False, "description": "💎 Imagen 4 — Google flagship"},
        "google/imagen4-fast": {"nsfw": False, "description": "🚀 Imagen 4 Fast"},
        "google/imagen4-ultra": {"nsfw": False, "description": "💎 Imagen 4 Ultra — qualité maximale"},
        "google/imagen3": {"nsfw": False, "description": "💎 Imagen 3 — detail et lumière"},
        "google/imagen3-fast": {"nsfw": False, "description": "🚀 Imagen 3 Fast"},
        "google/nano-banana-2/text-to-image": {"nsfw": False, "description": "🍌 Nano Banana 2 — Google"},
        "google/nano-banana-pro/text-to-image": {"nsfw": False, "description": "🍌 Nano Banana Pro"},
        "google/nano-banana-pro/text-to-image-ultra": {"nsfw": False, "description": "🍌 Nano Banana Pro Ultra"},
        "google/nano-banana/text-to-image": {"nsfw": False, "description": "🍌 Nano Banana"},
        "z-image/turbo": {"nsfw": False, "description": "⚡ Z-Image Turbo — sub-seconde, photorealistic"},
    }

    # Modèles Image-to-Image (catalogue de fallback — mis à jour depuis l'API au runtime)
    IMG2IMG_MODELS = {
        "bytedance/seedream-v5.0-lite/edit": {"nsfw": False, "description": "🌱 Seedream v5.0 Lite Edit"},
        "bytedance/seedream-v5.0-lite/edit-sequential": {"nsfw": False, "description": "🌱 Seedream v5.0 Lite Edit Sequential"},
        "bytedance/seedream-v4.5/edit": {"nsfw": False, "description": "🌱 Seedream v4.5 Edit"},
        "bytedance/seedream-v4.5/edit-sequential": {"nsfw": False, "description": "🌱 Seedream v4.5 Edit Sequential"},
        "bytedance/seedream-v4/edit": {"nsfw": False, "description": "🌱 Seedream v4 Edit"},
        "bytedance/seedream-v4/edit-sequential": {"nsfw": False, "description": "🌱 Seedream v4 Edit Sequential"},
        "black-forest-labs/flux-kontext-dev": {"nsfw": False, "description": "✏️ FLUX Kontext Dev — édition par texte"},
        "black-forest-labs/flux-kontext-dev-lora": {"nsfw": False, "description": "✏️ FLUX Kontext Dev LoRA"},
        "alibaba/qwen-image/edit": {"nsfw": False, "description": "🏮 Qwen-Image Edit"},
        "alibaba/qwen-image/edit-plus": {"nsfw": False, "description": "🏮 Qwen-Image Edit Plus"},
        "alibaba/qwen-image/edit-plus-20251215": {"nsfw": False, "description": "🏮 Qwen-Image Edit Plus 20251215 — HOT"},
        "atlascloud/qwen-image/edit": {"nsfw": False, "description": "🏮 Qwen Image Edit — 20B MMDiT"},
        "alibaba/wan-2.6/image-edit": {"nsfw": False, "description": "🎨 Wan-2.6 Image Edit"},
        "alibaba/wan-2.5/image-edit": {"nsfw": False, "description": "🎨 Wan-2.5 Image Edit"},
        "google/nano-banana-2/edit": {"nsfw": False, "description": "🍌 Nano Banana 2 Edit — Google"},
        "google/nano-banana-pro/edit": {"nsfw": False, "description": "🍌 Nano Banana Pro Edit"},
        "google/nano-banana-pro/edit-ultra": {"nsfw": False, "description": "🍌 Nano Banana Pro Edit Ultra"},
        "google/nano-banana/edit": {"nsfw": False, "description": "🍌 Nano Banana Edit"},
    }

    @property
    def name(self) -> str:
        return "AtlasCloud"

    @property
    def supports_nsfw(self) -> bool:
        return False  # Filtrage par défaut côté AtlasCloud

    def get_available_models(self) -> List[str]:
        return list(self.MODELS.keys())

    def get_img2img_models(self) -> List[str]:
        return list(self.IMG2IMG_MODELS.keys())

    async def _fetch_all_models_from_api(self) -> Tuple[Optional[List[dict]], Optional[str]]:
        """Appel unique à GET /api/v1/models, retourne la liste brute ou une erreur."""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/models",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=20)
                ) as response:
                    if response.status != 200:
                        return None, f"Erreur API ({response.status})"
                    result = await response.json()
                    data = result.get("data", [])
                    if not data:
                        return None, "Réponse vide"
                    return data, None
        except asyncio.TimeoutError:
            return None, "Timeout"
        except Exception as e:
            return None, str(e)

    async def fetch_live_models(self) -> Tuple[Optional[List[str]], Optional[str]]:
        """
        Récupère la liste des modèles Text-to-Image depuis l'API AtlasCloud.
        Filtre sur type=Image et catégorie TEXT-TO-IMAGE.
        """
        if not self.is_available:
            return None, "Clé API AtlasCloud manquante"

        data, error = await self._fetch_all_models_from_api()
        if error:
            print(f"[IMAGE-ATLASCLOUD] fetch T2I échoué: {error} — catalogue local utilisé")
            return list(self.MODELS.keys()), None

        models = [
            item["model"]
            for item in data
            if item.get("type") == "Image" and "TEXT-TO-IMAGE" in item.get("categories", [])
        ]
        print(f"[IMAGE-ATLASCLOUD] {len(models)} modèles T2I depuis API")
        return models if models else list(self.MODELS.keys()), None

    async def fetch_live_img2img_models(self) -> Tuple[Optional[List[str]], Optional[str]]:
        """
        Récupère la liste des modèles Image-to-Image depuis l'API AtlasCloud.
        Filtre sur type=Image et catégorie IMAGE-TO-IMAGE.
        """
        if not self.is_available:
            return None, "Clé API AtlasCloud manquante"

        data, error = await self._fetch_all_models_from_api()
        if error:
            print(f"[IMAGE-ATLASCLOUD] fetch I2I échoué: {error} — catalogue local utilisé")
            return list(self.IMG2IMG_MODELS.keys()), None

        models = [
            item["model"]
            for item in data
            if item.get("type") == "Image" and "IMAGE-TO-IMAGE" in item.get("categories", [])
        ]
        print(f"[IMAGE-ATLASCLOUD] {len(models)} modèles I2I depuis API")
        return models if models else list(self.IMG2IMG_MODELS.keys()), None

    async def _poll_for_result(self, session, prediction_id: str) -> Tuple[Optional[str], Optional[str]]:
        """Poll le résultat d'une prédiction AtlasCloud jusqu'à completion"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        result_url = f"{self.BASE_URL}/model/getResult?predictionId={prediction_id}"

        for poll_count in range(self.MAX_POLLS):
            # Vérifier signal d'arrêt
            try:
                from stop_signal import is_stop_requested
                if is_stop_requested():
                    print(f"[IMAGE-ATLASCLOUD] Génération interrompue au poll #{poll_count + 1}")
                    return None, "Génération interrompue par l'utilisateur"
            except ImportError:
                pass

            await asyncio.sleep(self.POLL_INTERVAL)

            try:
                async with session.get(
                    result_url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:

                    if response.status != 200:
                        continue

                    result = await response.json()
                    status = result.get("status", "")

                    print(f"[IMAGE-ATLASCLOUD] Poll #{poll_count + 1}: {status}")

                    if status == "completed":
                        output = result.get("output")
                        if output:
                            return output, None
                        return None, "Pas d'output dans la réponse"

                    elif status == "failed":
                        error = result.get("error", "Génération échouée")
                        return None, f"Échec AtlasCloud: {error}"

                    # status == "processing" → continuer le polling

            except Exception as e:
                print(f"[IMAGE-ATLASCLOUD] Erreur poll #{poll_count + 1}: {e}")
                continue

        return None, "Timeout: génération trop longue"

    async def _upload_image(self, base64_data: str, filename: str = "image.png") -> Tuple[Optional[str], Optional[str]]:
        """Upload une image base64 vers AtlasCloud uploadMedia, retourne l'URL temporaire"""
        if not self.is_available:
            return None, "Clé API AtlasCloud manquante"

        # Nettoyer le préfixe data:image/...;base64, si présent
        if base64_data.startswith("data:"):
            base64_data = base64_data.split(",", 1)[1]

        try:
            image_bytes = base64.b64decode(base64_data)

            headers = {"Authorization": f"Bearer {self.api_key}"}

            form_data = aiohttp.FormData()
            form_data.add_field(
                "file",
                image_bytes,
                filename=filename,
                content_type="image/png"
            )

            print(f"[IMAGE-ATLASCLOUD] Upload image source ({len(image_bytes):,} bytes)...")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.BASE_URL}/model/uploadMedia",
                    headers=headers,
                    data=form_data,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:

                    if response.status != 200:
                        error_text = await response.text()
                        return None, f"Erreur upload ({response.status}): {error_text[:200]}"

                    result = await response.json()
                    url = result.get("url")
                    if url:
                        print(f"[IMAGE-ATLASCLOUD] Upload réussi: {url[:80]}...")
                        return url, None
                    return None, f"Pas d'URL dans la réponse: {result}"

        except Exception as e:
            print(f"[IMAGE-ATLASCLOUD] Erreur upload: {e}")
            return None, f"Exception upload: {str(e)}"

    async def generate(
        self,
        prompt: str,
        model: str,
        width: int,
        height: int,
        **kwargs
    ) -> Tuple[Optional[bytes], Optional[str]]:
        """Génère une image Text-to-Image via AtlasCloud"""
        if not self.is_available:
            return None, "Clé API AtlasCloud manquante"

        model = model or "seedream-3.0"

        payload = {
            "model": model,
            "prompt": prompt,
        }

        # Paramètres facultatifs
        if width and height:
            payload["width"] = width
            payload["height"] = height
        if kwargs.get("negative_prompt"):
            payload["negative_prompt"] = kwargs["negative_prompt"]
        if kwargs.get("seed") is not None and kwargs["seed"] != -1:
            payload["seed"] = kwargs["seed"]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            print(f"[IMAGE-ATLASCLOUD] T2I avec {model}...")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.BASE_URL}/model/generateImage",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:

                    if response.status != 200:
                        error_text = await response.text()
                        print(f"[IMAGE-ATLASCLOUD] Erreur ({response.status}): {error_text[:200]}")
                        return None, f"Erreur AtlasCloud: {response.status}"

                    result = await response.json()
                    prediction_id = result.get("predictionId")

                    if not prediction_id:
                        return None, f"Pas d'ID de prédiction: {result}"

                    print(f"[IMAGE-ATLASCLOUD] Tâche créée: {prediction_id}")

                # Poll pour le résultat
                output_url, error = await self._poll_for_result(session, prediction_id)

                if error:
                    return None, error

                # Télécharger l'image depuis l'URL de sortie
                async with session.get(
                    output_url,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as img_response:
                    if img_response.status == 200:
                        image_bytes = await img_response.read()
                        print(f"[IMAGE-ATLASCLOUD] Image T2I générée ({len(image_bytes)} bytes)")
                        return image_bytes, None
                    return None, f"Erreur téléchargement ({img_response.status})"

        except asyncio.TimeoutError:
            return None, "Timeout"
        except Exception as e:
            print(f"[IMAGE-ATLASCLOUD] Erreur T2I: {e}")
            return None, str(e)

    async def generate_img2img(
        self,
        prompt: str,
        source_image_base64: str = None,
        source_images_base64: List[str] = None,
        model: str = None,
        width: int = 1024,
        height: int = 1024,
        **kwargs
    ) -> Tuple[Optional[bytes], Optional[str]]:
        """Génère une image modifiée via AtlasCloud Image-to-Image (image_url)"""
        if not self.is_available:
            return None, "Clé API AtlasCloud manquante"

        model = model or "seedream-3.0"

        # Prendre la première image source disponible
        source_b64 = None
        if source_images_base64:
            source_b64 = source_images_base64[0]
        elif source_image_base64:
            source_b64 = source_image_base64

        if not source_b64:
            return None, "Image source requise pour img2img AtlasCloud"

        # Upload de l'image source vers AtlasCloud
        image_url, upload_error = await self._upload_image(source_b64)
        if upload_error:
            return None, f"Erreur upload image source: {upload_error}"

        payload = {
            "model": model,
            "prompt": prompt,
            "image_url": image_url,
        }

        # Paramètres facultatifs
        if width and height:
            payload["width"] = width
            payload["height"] = height
        if kwargs.get("strength"):
            payload["strength"] = kwargs["strength"]
        if kwargs.get("negative_prompt"):
            payload["negative_prompt"] = kwargs["negative_prompt"]
        if kwargs.get("seed") is not None and kwargs["seed"] != -1:
            payload["seed"] = kwargs["seed"]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        try:
            print(f"[IMAGE-ATLASCLOUD] I2I avec {model}...")

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.BASE_URL}/model/generateImage",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:

                    if response.status != 200:
                        error_text = await response.text()
                        print(f"[IMAGE-ATLASCLOUD] Erreur I2I ({response.status}): {error_text[:200]}")
                        return None, f"Erreur AtlasCloud I2I: {response.status}"

                    result = await response.json()
                    prediction_id = result.get("predictionId")

                    if not prediction_id:
                        return None, f"Pas d'ID de prédiction I2I: {result}"

                    print(f"[IMAGE-ATLASCLOUD] Tâche I2I créée: {prediction_id}")

                # Poll pour le résultat
                output_url, error = await self._poll_for_result(session, prediction_id)

                if error:
                    return None, error

                # Télécharger l'image résultante
                async with session.get(
                    output_url,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as img_response:
                    if img_response.status == 200:
                        image_bytes = await img_response.read()
                        print(f"[IMAGE-ATLASCLOUD] Image I2I générée ({len(image_bytes)} bytes)")
                        return image_bytes, None
                    return None, f"Erreur téléchargement I2I ({img_response.status})"

        except asyncio.TimeoutError:
            return None, "Timeout"
        except Exception as e:
            print(f"[IMAGE-ATLASCLOUD] Erreur I2I: {e}")
            return None, str(e)


class ImageGenerationBackend:
    """
    Backend unifié de génération d'images multi-provider
    
    Usage:
        backend = ImageGenerationBackend(settings_manager)
        image_bytes, error = await backend.generate("a cat", provider="GROK")
    """
    
    # Providers supportés avec leur classe
    PROVIDERS = {
        "GROK": GrokImageProvider,
        "OpenAI": OpenAIImageProvider,
        "Google": GoogleImageProvider,
        "Kie": KieImageProvider,
        "WaveSpeed": WaveSpeedImageProvider,
        "AtlasCloud": AtlasCloudImageProvider,
    }
    
    def __init__(self, settings_manager):
        self.settings_manager = settings_manager
        self._providers: Dict[str, ImageProviderBase] = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialise les providers avec les clés du vault"""
        vault = self.settings_manager.settings.get('api_keys_vault', {})
        
        for provider_name, provider_class in self.PROVIDERS.items():
            api_key = vault.get(provider_name)
            if api_key:
                self._providers[provider_name] = provider_class(api_key)
                print(f"[IMAGE-BACKEND] ✅ Provider {provider_name} initialisé")
            else:
                print(f"[IMAGE-BACKEND] ⚠️ Provider {provider_name} non configuré (clé manquante)")
    
    def get_available_providers(self) -> List[str]:
        """Retourne la liste des providers disponibles (avec clé API)"""
        return [name for name, provider in self._providers.items() if provider.is_available]
    
    def get_provider_models(self, provider_name: str) -> List[str]:
        """Retourne les modèles disponibles pour un provider"""
        provider = self._providers.get(provider_name)
        if provider:
            return provider.get_available_models()
        return []
    
    def get_img2img_models(self, provider_name: str = "Kie") -> List[str]:
        """Retourne les modèles Image-to-Image disponibles (Kie uniquement pour l'instant)"""
        provider = self._providers.get(provider_name)
        if provider and hasattr(provider, 'get_img2img_models'):
            return provider.get_img2img_models()
        return []
    
    def provider_supports_nsfw(self, provider_name: str) -> bool:
        """Vérifie si un provider supporte le mode Unfiltered/Spicy"""
        provider = self._providers.get(provider_name)
        return provider.supports_nsfw if provider else False
    
    def model_supports_seed(self, provider_name: str, model_name: str) -> bool:
        """
        Vérifie si un modèle img2img supporte le paramètre seed (pour batch mode).
        
        Args:
            provider_name: Nom du provider (WaveSpeed, Kie, etc.)
            model_name: Nom du modèle img2img
            
        Returns:
            bool: True si le modèle supporte seed
        """
        provider = self._providers.get(provider_name)
        if provider and hasattr(provider, 'model_supports_seed'):
            return provider.model_supports_seed(model_name)
        return False
    
    async def fetch_live_models(self, provider_name: str) -> Tuple[Optional[List[str]], Optional[str]]:
        """
        Récupère la liste des modèles en direct depuis l'API du provider
        
        Args:
            provider_name: Nom du provider (GROK, OpenAI, Google, Kie, WaveSpeed)
            
        Returns:
            tuple: (list_models, error_message)
        """
        provider = self._providers.get(provider_name)
        if not provider:
            return None, f"Provider {provider_name} non disponible"
        
        if not provider.is_available:
            return None, f"Clé API manquante pour {provider_name}"
        
        # Appeler la méthode fetch_live_models du provider
        return await provider.fetch_live_models()
    
    async def fetch_live_img2img_models(self, provider_name: str) -> Tuple[Optional[List[str]], Optional[str]]:
        """
        Récupère la liste des modèles Image-to-Image en direct depuis l'API du provider
        
        Args:
            provider_name: Nom du provider (Kie, WaveSpeed)
            
        Returns:
            tuple: (list_models, error_message)
        """
        provider = self._providers.get(provider_name)
        if not provider:
            return None, f"Provider {provider_name} non disponible"
        
        if not provider.is_available:
            return None, f"Clé API manquante pour {provider_name}"
        
        # Vérifier que le provider supporte img2img
        if not hasattr(provider, 'get_img2img_models'):
            return None, f"Provider {provider_name} ne supporte pas img2img"
        
        # Appeler la méthode fetch_live_img2img_models du provider
        return await provider.fetch_live_img2img_models()
    
    async def generate(
        self,
        prompt: str,
        provider: str = "GROK",
        model: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
        **kwargs
    ) -> Tuple[Optional[bytes], Optional[str], Dict[str, Any]]:
        """
        Génère une image avec le provider spécifié
        
        Returns:
            tuple: (image_bytes, error_message, metadata)
        """
        # Vérifier le provider
        if provider not in self._providers:
            return None, f"Provider {provider} non disponible", {}
        
        provider_instance = self._providers[provider]
        if not provider_instance.is_available:
            return None, f"Clé API manquante pour {provider}", {}
        
        # Sélectionner le modèle par défaut si non spécifié
        if not model:
            models = provider_instance.get_available_models()
            model = models[0] if models else None
        
        # Générer l'image
        image_bytes, error = await provider_instance.generate(
            prompt=prompt,
            model=model,
            width=width,
            height=height,
            **kwargs
        )
        
        # Construire les métadonnées
        metadata = {
            "provider": provider,
            "model": model,
            "width": width,
            "height": height,
            "prompt": prompt,
            "supports_nsfw": provider_instance.supports_nsfw
        }
        
        return image_bytes, error, metadata
    
    async def generate_img2img(
        self,
        prompt: str,
        source_image_base64: str = None,
        source_images_base64: List[str] = None,  # MULTI-IMAGE SUPPORT
        provider: str = "Kie",
        model: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
        **kwargs
    ) -> Tuple[Optional[bytes], Optional[str], Dict[str, Any]]:
        """
        Génère une image modifiée à partir d'une ou plusieurs images source (Image-to-Image)
        
        Args:
            prompt: Description des modifications à apporter
            source_image_base64: Image source en base64 (backward compat)
            source_images_base64: Liste d'images en base64 (multi-image support)
            provider: Provider à utiliser (Kie ou WaveSpeed)
            model: Modèle img2img à utiliser
            width: Largeur souhaitée
            height: Hauteur souhaitée
            
        Returns:
            tuple: (image_bytes, error_message, metadata)
        """
        # Providers supportant img2img
        if provider not in ["Kie", "WaveSpeed", "AtlasCloud"]:
            return None, f"Provider {provider} ne supporte pas img2img. Utilisez Kie, WaveSpeed ou AtlasCloud.", {}
        
        if provider not in self._providers:
            return None, f"Provider {provider} non disponible", {}
        
        provider_instance = self._providers[provider]
        if not provider_instance.is_available:
            return None, f"Clé API {provider} manquante", {}
        
        # Sélectionner le modèle par défaut si non spécifié
        if not model:
            models = provider_instance.get_img2img_models()
            model = models[0] if models else "flux-2/pro-image-to-image"
        
        # Comptage des images pour les logs
        nb_images = len(source_images_base64) if source_images_base64 else (1 if source_image_base64 else 0)
        print(f"[IMAGE-BACKEND] 🎨 IMG2IMG avec {nb_images} image(s) source")
        
        # Générer l'image modifiée (transmet les deux paramètres)
        image_bytes, error = await provider_instance.generate_img2img(
            prompt=prompt,
            source_image_base64=source_image_base64,
            source_images_base64=source_images_base64,
            model=model,
            width=width,
            height=height,
            **kwargs
        )
        
        # Construire les métadonnées
        metadata = {
            "provider": provider,
            "model": model,
            "width": width,
            "height": height,
            "prompt": prompt,
            "type": "img2img",
            "source_images_count": nb_images,
            "supports_nsfw": provider_instance.supports_nsfw
        }
        
        return image_bytes, error, metadata

    async def generate_img2img_batch(
        self,
        prompt: str,
        source_image_base64: str = None,
        source_images_base64: List[str] = None,
        provider: str = "WaveSpeed",
        model: str = "bytedance/seedream-v4.5/edit",
        batch_count: int = 1,
        base_seed: int = -1,
        seed_increment: int = 1,
        **kwargs
    ) -> Tuple[List[bytes], List[str], dict]:
        """
        Génère plusieurs images I2I en batch avec seeds incrémentaux.
        
        Args:
            prompt: Prompt de modification
            source_image_base64: Image source unique (backward compat)
            source_images_base64: Liste d'images sources
            provider: Provider à utiliser (WaveSpeed recommandé pour batch)
            model: Modèle I2I à utiliser
            batch_count: Nombre d'images à générer (1-6)
            base_seed: Seed de départ (-1 = aléatoire)
            seed_increment: Écart entre chaque seed
            **kwargs: Autres paramètres (size, output_format, etc.)
            
        Returns:
            tuple: (liste_images_bytes, liste_erreurs, metadata)
        """
        # Seul WaveSpeed supporte le batch pour l'instant
        if provider != "WaveSpeed":
            print(f"[IMAGE-BACKEND-BATCH] ⚠️ Batch non supporté pour {provider}, fallback single image")
            # Fallback: générer une seule image
            img_bytes, error, metadata = await self.generate_img2img(
                prompt=prompt,
                source_image_base64=source_image_base64,
                source_images_base64=source_images_base64,
                provider=provider,
                model=model,
                **kwargs
            )
            return [img_bytes] if img_bytes else [], [error] if error else [], metadata
        
        if provider not in self._providers:
            return [], [f"Provider {provider} non disponible"], {}
        
        provider_instance = self._providers[provider]
        if not provider_instance.is_available:
            return [], [f"Clé API {provider} manquante"], {}
        
        # Vérifier que le provider a la méthode batch
        if not hasattr(provider_instance, 'generate_img2img_batch'):
            print(f"[IMAGE-BACKEND-BATCH] ⚠️ Provider {provider} n'a pas generate_img2img_batch, fallback")
            img_bytes, error, metadata = await self.generate_img2img(
                prompt=prompt,
                source_image_base64=source_image_base64,
                source_images_base64=source_images_base64,
                provider=provider,
                model=model,
                **kwargs
            )
            return [img_bytes] if img_bytes else [], [error] if error else [], metadata
        
        # Comptage des images source
        nb_images_src = len(source_images_base64) if source_images_base64 else (1 if source_image_base64 else 0)
        print(f"[IMAGE-BACKEND-BATCH] 🎨 Batch {batch_count} images avec {nb_images_src} source(s)")
        
        # Générer le batch
        images, errors = await provider_instance.generate_img2img_batch(
            prompt=prompt,
            source_image_base64=source_image_base64,
            source_images_base64=source_images_base64,
            model=model,
            batch_count=batch_count,
            base_seed=base_seed,
            seed_increment=seed_increment,
            **kwargs
        )
        
        # Construire les métadonnées
        metadata = {
            "provider": provider,
            "model": model,
            "prompt": prompt,
            "type": "img2img_batch",
            "batch_count": batch_count,
            "base_seed": base_seed,
            "seed_increment": seed_increment,
            "images_generated": len(images),
            "source_images_count": nb_images_src,
            "supports_nsfw": provider_instance.supports_nsfw
        }
        
        return images, errors, metadata


# Singleton pour accès global
_backend_instance: Optional[ImageGenerationBackend] = None


def get_image_backend(settings_manager=None) -> Optional[ImageGenerationBackend]:
    """Récupère ou crée l'instance du backend"""
    global _backend_instance
    
    if _backend_instance is None and settings_manager:
        _backend_instance = ImageGenerationBackend(settings_manager)
    
    return _backend_instance


def reset_backend():
    """Reset le backend (utile après changement de config)"""
    global _backend_instance
    _backend_instance = None
