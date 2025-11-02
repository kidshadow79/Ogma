"""
Backend Pollinations.AI pour génération d'images
=================================================
Utilise l'API HTTP de Pollinations.ai pour la génération d'images.

API Endpoint: https://image.pollinations.ai/prompt/{prompt}
Documentation: https://pollinations.ai/
Modèles disponibles: flux, turbo, etc.
"""

import asyncio
import aiohttp
from typing import Optional, Dict, Any
from urllib.parse import quote
import io

# Import du PromptEnhancer pour enrichissement qualité Perchance
from .prompt_enhancer import get_enhancer

class PerchanceHTTPBackend:
    """Backend de génération d'images via API HTTP Pollinations.ai"""

    def __init__(self):
        self.is_available = False
        self.backend_name = "Pollinations.AI"
        self.model_name = "Flux"

        # API endpoint
        self.base_url = "https://image.pollinations.ai/prompt"

        # Paramètres par défaut (optimisés pour qualité Perchance)
        self.default_width = 1536  # Augmenté de 1024 pour meilleure qualité
        self.default_height = 1536
        self.default_timeout = 120  # 2 minutes
        self.default_model = "flux"  # flux (défaut), turbo
        self.default_safe_mode = False  # NSFW autorisé
        self.default_enhance = True  # Enhancement LLM du prompt activé
        self.default_nologo = True  # Pas de logo Pollinations
        
        # PromptEnhancer pour enrichissement qualité Perchance
        self.prompt_enhancer = None
        self.enable_prompt_enhancement = True  # Activé par défaut

    def initialize(self) -> bool:
        """
        Initialise le backend Perchance HTTP

        Returns:
            bool: True si l'initialisation a réussi
        """
        try:
            print(f"[TEXT2IMG-HTTP] 🔧 Initialisation backend Perchance HTTP...")

            # Vérifier aiohttp
            try:
                import aiohttp
                print(f"[TEXT2IMG-HTTP] ✅ Bibliothèque aiohttp disponible")
            except ImportError:
                print(f"[TEXT2IMG-HTTP] ❌ Bibliothèque aiohttp non installée")
                print(f"[TEXT2IMG-HTTP] 💡 Installez avec: pip install aiohttp")
                return False

            # Initialiser le PromptEnhancer
            if self.enable_prompt_enhancement:
                try:
                    self.prompt_enhancer = get_enhancer(debug=False)
                    print(f"[TEXT2IMG-HTTP] ✅ PromptEnhancer initialisé (qualité Perchance)")
                except Exception as e:
                    print(f"[TEXT2IMG-HTTP] ⚠️ Erreur init PromptEnhancer: {e}")
                    print(f"[TEXT2IMG-HTTP] ℹ️ Fonctionnement sans enrichissement prompts")
                    self.prompt_enhancer = None

            self.is_available = True
            print(f"[TEXT2IMG-HTTP] ✅ Backend Perchance HTTP initialisé")
            print(f"[TEXT2IMG-HTTP] 🌐 API: {self.base_url}")
            print(f"[TEXT2IMG-HTTP] 📐 Résolution défaut: {self.default_width}×{self.default_height}")
            print(f"[TEXT2IMG-HTTP] 🎨 Enhancement: {self.default_enhance} | Safe: {self.default_safe_mode}")
            return True

        except Exception as e:
            print(f"[TEXT2IMG-HTTP] ❌ Erreur initialisation: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def generate_image(
        self,
        prompt: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        guidance_scale: Optional[float] = None,
        steps: Optional[int] = None,
        seed: Optional[int] = None,
        negative_prompt: Optional[str] = None,
        model: str = "flux",
        safe_mode: Optional[bool] = None,
        enhance: Optional[bool] = None,
        nologo: Optional[bool] = None,
        **kwargs
    ) -> tuple[Optional[bytes], Optional[str]]:
        """
        Génère une image via API HTTP Pollinations.ai avec enrichissement Perchance

        Args:
            prompt: Description de l'image à générer
            width: Largeur de l'image (défaut: 1536)
            height: Hauteur de l'image (défaut: 1536)
            seed: Graine aléatoire (défaut: None = random)
            model: Modèle à utiliser (flux, turbo)
            safe_mode: Filtre NSFW strict (défaut: False)
            enhance: Enhancement LLM du prompt (défaut: True)
            nologo: Désactiver logo Pollinations (défaut: True)
            guidance_scale: Non supporté
            steps: Non supporté
            negative_prompt: Non supporté nativement

        Returns:
            tuple[bytes, str]: (données image, message d'erreur)
                - Si succès: (bytes, None)
                - Si échec: (None, message d'erreur)
        """
        if not self.is_available:
            return None, "Backend Pollinations HTTP non initialisé"

        # Valeurs par défaut
        width = width or self.default_width
        height = height or self.default_height
        model = model or self.default_model
        safe_mode = safe_mode if safe_mode is not None else self.default_safe_mode
        enhance = enhance if enhance is not None else self.default_enhance
        nologo = nologo if nologo is not None else self.default_nologo
        
        # ENRICHISSEMENT PROMPT PERCHANCE
        original_prompt = prompt
        if self.prompt_enhancer and self.enable_prompt_enhancement:
            try:
                prompt = self.prompt_enhancer.enhance(prompt)
                print(f"[TEXT2IMG-HTTP] 🚀 Prompt enrichi ({len(original_prompt)} → {len(prompt)} chars)")
            except Exception as e:
                print(f"[TEXT2IMG-HTTP] ⚠️ Erreur enrichissement prompt: {e}")
                print(f"[TEXT2IMG-HTTP] ℹ️ Utilisation prompt original")
                prompt = original_prompt

        try:
            print(f"[TEXT2IMG-HTTP] 🎨 Génération image...")
            print(f"[TEXT2IMG-HTTP]    Prompt original: '{original_prompt[:60]}...'")
            print(f"[TEXT2IMG-HTTP]    Résolution: {width}×{height}")
            print(f"[TEXT2IMG-HTTP]    Modèle: {model} | Safe: {safe_mode}")

            # Encoder le prompt pour URL
            encoded_prompt = quote(prompt)

            # Construire l'URL complète avec paramètres
            url = f"{self.base_url}/{encoded_prompt}"

            # Construire les paramètres query
            params = []
            params.append(f"width={width}")
            params.append(f"height={height}")
            params.append(f"model={model}")
            params.append(f"safe={'true' if safe_mode else 'false'}")
            params.append(f"enhance={'true' if enhance else 'false'}")
            params.append(f"nologo={'true' if nologo else 'false'}")

            if seed is not None:
                params.append(f"seed={seed}")

            url += "?" + "&".join(params)

            print(f"[TEXT2IMG-HTTP] 🚀 Requête: {url[:120]}...")

            # Créer session aiohttp avec timeout
            timeout = aiohttp.ClientTimeout(total=self.default_timeout)

            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        error_msg = f"HTTP {response.status}: {response.reason}"
                        print(f"[TEXT2IMG-HTTP] ❌ {error_msg}")
                        return None, error_msg

                    # Vérifier le content-type
                    content_type = response.headers.get('content-type', '').lower()
                    if not content_type.startswith('image/'):
                        error_msg = f"Réponse non-image reçue: {content_type}"
                        print(f"[TEXT2IMG-HTTP] ❌ {error_msg}")
                        return None, error_msg

                    # Lire les bytes de l'image
                    image_bytes = await response.read()

                    if len(image_bytes) == 0:
                        return None, "Image vide générée"

                    print(f"[TEXT2IMG-HTTP] ✅ Image générée ({len(image_bytes)} bytes)")

                    return image_bytes, None

        except asyncio.TimeoutError:
            error_msg = f"Timeout après {self.default_timeout}s"
            print(f"[TEXT2IMG-HTTP] ⏱️ {error_msg}")
            return None, error_msg

        except aiohttp.ClientError as e:
            error_msg = f"Erreur connexion: {str(e)}"
            print(f"[TEXT2IMG-HTTP] ❌ {error_msg}")
            return None, error_msg

        except Exception as e:
            error_msg = f"Erreur génération: {str(e)}"
            print(f"[TEXT2IMG-HTTP] ❌ {error_msg}")
            import traceback
            traceback.print_exc()
            return None, error_msg

    def get_backend_info(self) -> Dict[str, Any]:
        """
        Retourne les informations sur le backend

        Returns:
            dict: Informations du backend
        """
        return {
            "name": self.backend_name,
            "model": self.model_name,
            "available": self.is_available,
            "free": True,
            "unlimited": True,
            "api_key_required": False,
            "censorship": "minimal",
            "api_url": self.base_url,
            "supported_params": ["width", "height", "seed"],
            "default_params": {
                "width": self.default_width,
                "height": self.default_height,
                "timeout": self.default_timeout
            }
        }
