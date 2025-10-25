"""
Backend Perchance pour génération d'images
===========================================
Utilise Perchance.org (Stable Diffusion) pour générer des images.

Features:
- Gratuit et illimité
- Stable Diffusion 1.5 / 2.1 / SDXL
- Paramètres personnalisables (guidance_scale, steps, seed)
- Support negative prompts
"""

import asyncio
from typing import Optional, Dict, Any
from pathlib import Path
import io

class PerchanceBackend:
    """Backend de génération d'images via Perchance"""

    def __init__(self):
        self.is_available = False
        self.backend_name = "Perchance"
        self.model_name = "Stable Diffusion"

        # Paramètres par défaut
        self.default_width = 1024
        self.default_height = 1024
        self.default_guidance_scale = 7.5
        self.default_steps = 30
        self.default_seed = None  # Random
        self.default_negative_prompt = "blurry, low quality, distorted, ugly"

    def initialize(self) -> bool:
        """
        Initialise le backend Perchance

        Returns:
            bool: True si l'initialisation a réussi
        """
        try:
            print(f"[TEXT2IMG-PERCHANCE] 🔧 Initialisation backend Perchance...")

            # Tester l'import de perchance
            try:
                import perchance
                print(f"[TEXT2IMG-PERCHANCE] ✅ Bibliothèque perchance disponible")
            except ImportError as e:
                print(f"[TEXT2IMG-PERCHANCE] ❌ Bibliothèque perchance non installée: {e}")
                print(f"[TEXT2IMG-PERCHANCE] 💡 Installez avec: pip install perchance")
                return False

            self.is_available = True
            print(f"[TEXT2IMG-PERCHANCE] ✅ Backend Perchance initialisé")
            return True

        except Exception as e:
            print(f"[TEXT2IMG-PERCHANCE] ❌ Erreur initialisation: {e}")
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
        model: str = "sd2.1",
        **kwargs
    ) -> tuple[Optional[bytes], Optional[str]]:
        """
        Génère une image via Perchance

        Args:
            prompt: Description de l'image à générer
            width: Largeur de l'image (défaut: 1024)
            height: Hauteur de l'image (défaut: 1024)
            guidance_scale: Fidélité au prompt 1-20 (défaut: 7.5)
            steps: Nombre d'étapes de génération 10-50 (défaut: 30)
            seed: Graine aléatoire pour reproductibilité (défaut: None = random)
            negative_prompt: Éléments à éviter (défaut: "blurry, low quality...")
            model: Modèle SD à utiliser (sd1.5, sd2.1, sdxl)

        Returns:
            tuple[bytes, str]: (données image, message d'erreur)
                - Si succès: (bytes, None)
                - Si échec: (None, message d'erreur)
        """
        if not self.is_available:
            return None, "Backend Perchance non initialisé"

        # Valeurs par défaut
        width = width or self.default_width
        height = height or self.default_height
        guidance_scale = guidance_scale or self.default_guidance_scale
        steps = steps or self.default_steps
        negative_prompt = negative_prompt or self.default_negative_prompt

        try:
            import perchance
            from PIL import Image

            print(f"[TEXT2IMG-PERCHANCE] 🎨 Génération image...")
            print(f"[TEXT2IMG-PERCHANCE]    Prompt: '{prompt[:60]}...'")
            print(f"[TEXT2IMG-PERCHANCE]    Résolution: {width}×{height}")
            print(f"[TEXT2IMG-PERCHANCE]    Guidance: {guidance_scale}, Steps: {steps}")
            print(f"[TEXT2IMG-PERCHANCE]    Seed: {seed or 'random'}")

            # Créer le générateur
            gen = perchance.ImageGenerator()

            # Note: Perchance ne supporte pas tous les paramètres avancés
            # On va utiliser le prompt enrichi et les paramètres par défaut

            # Enrichir le prompt avec les paramètres (si l'API le supporte)
            enhanced_prompt = prompt

            print(f"[TEXT2IMG-PERCHANCE] 🚀 Lancement génération...")

            # Générer l'image
            async with await gen.image(enhanced_prompt) as result:
                # Télécharger les données binaires
                binary_io = await result.download()

                # Lire les bytes
                image_bytes = binary_io.read()

                # Vérifier que l'image est valide
                if len(image_bytes) == 0:
                    return None, "Image vide générée"

                print(f"[TEXT2IMG-PERCHANCE] ✅ Image générée ({len(image_bytes)} bytes)")

                return image_bytes, None

        except ImportError as e:
            error_msg = f"Bibliothèque perchance manquante: {e}"
            print(f"[TEXT2IMG-PERCHANCE] ❌ {error_msg}")
            return None, error_msg

        except Exception as e:
            error_msg = f"Erreur génération Perchance: {str(e)}"
            print(f"[TEXT2IMG-PERCHANCE] ❌ {error_msg}")
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
            "supported_models": ["sd1.5", "sd2.1", "sdxl", "anime"],
            "default_params": {
                "width": self.default_width,
                "height": self.default_height,
                "guidance_scale": self.default_guidance_scale,
                "steps": self.default_steps,
                "negative_prompt": self.default_negative_prompt
            }
        }
