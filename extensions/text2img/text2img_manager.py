"""
Manager de génération d'images (Multi-Provider)
================================================
Orchestre le backend multi-provider, la sauvegarde et l'historique.
Providers supportés: GROK (xAI), OpenAI (DALL-E), Google (Imagen)

"""

import json
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime

from .image_backend import get_image_backend, reset_backend, ImageGenerationBackend


class Text2ImageManager:
    """Gestionnaire principal de génération d'images"""

    def __init__(self, settings_manager):
        self.settings_manager = settings_manager
        self.backend: Optional[ImageGenerationBackend] = None
        self.history: List[Dict] = []

        # Chemins
        self.generated_images_dir = Path("data/generated_images")
        self.history_file = self.generated_images_dir / "generation_history.json"

        # Créer le dossier si nécessaire
        self.generated_images_dir.mkdir(parents=True, exist_ok=True)

        # Charger l'historique
        self._load_history()

    def initialize_backend(self) -> bool:
        """
        Initialise le backend de génération multi-provider

        Returns:
            bool: True si au moins un provider est disponible
        """
        try:
            print("[TEXT2IMG-MANAGER] 🔧 Initialisation backend multi-provider...")
            
            # Reset et recréer le backend
            reset_backend()
            self.backend = get_image_backend(self.settings_manager)
            
            if not self.backend:
                print("[TEXT2IMG-MANAGER] ❌ Impossible de créer le backend")
                return False
            
            providers = self.backend.get_available_providers()
            
            if providers:
                print(f"[TEXT2IMG-MANAGER] ✅ Backend initialisé avec {len(providers)} provider(s): {', '.join(providers)}")
                return True
            else:
                print("[TEXT2IMG-MANAGER] ⚠️ Aucun provider configuré (clés API manquantes)")
                return False

        except Exception as e:
            print(f"[TEXT2IMG-MANAGER] ❌ Erreur initialisation: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def generate_image(
        self,
        prompt: str,
        **kwargs
    ) -> tuple[Optional[bytes], Optional[str], Optional[Dict]]:
        """
        Génère une image à partir d'un prompt

        Args:
            prompt: Description de l'image
            **kwargs: provider, model, width, height, etc.

        Returns:
            tuple: (image_bytes, error_message, metadata)
        """
        if not self.backend:
            return None, "Backend non initialisé", None

        try:
            # Récupérer la config depuis settings
            img_config = self.settings_manager.settings.get('image_generation', {})
            
            # Paramètres avec fallback sur config
            provider = kwargs.get('provider', img_config.get('provider', 'GROK'))
            model = kwargs.get('model', img_config.get('model'))
            width = kwargs.get('width', img_config.get('width', 1024))
            height = kwargs.get('height', img_config.get('height', 1024))

            # Générer l'image
            image_bytes, error, metadata = await self.backend.generate(
                prompt=prompt,
                provider=provider,
                model=model,
                width=width,
                height=height
            )

            if error:
                return None, error, None

            # Enrichir les métadonnées
            metadata["timestamp"] = datetime.now().isoformat()
            metadata["original_prompt"] = prompt

            return image_bytes, None, metadata

        except Exception as e:
            error_msg = f"Erreur génération: {str(e)}"
            print(f"[TEXT2IMG-MANAGER] ❌ {error_msg}")
            import traceback
            traceback.print_exc()
            return None, error_msg, None

    def save_image(
        self,
        image_bytes: bytes,
        metadata: Dict[str, Any]
    ) -> tuple[Optional[Path], Optional[str]]:
        """
        Sauvegarde une image générée avec ses métadonnées

        Returns:
            tuple: (chemin_fichier, error_message)
        """
        try:
            # Vérifier si la sauvegarde est activée
            img_config = self.settings_manager.settings.get('image_generation', {})
            if not img_config.get('save_images', True):
                print("[TEXT2IMG-MANAGER] ℹ️ Sauvegarde désactivée")
                return None, None

            # Générer le nom de fichier
            # IMPORTANT: On utilise des TIRETS (-) et NON des underscores (_)
            # car NiceGUI ui.markdown() interprète _text_ comme <em>text</em>
            # ce qui corrompt les URL des images dans les balises <img src="...">
            # Les nombres consécutifs de 6+ chiffres sont aussi interprétés comme pattern _XXX_
            # donc on sépare TOUT avec des tirets: YYYY-MM-DD-HH-MM-SS
            timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
            prompt_slug = metadata.get('prompt', 'image')[:30]
            
            # 🛡️ NETTOYAGE RENFORCÉ pour éviter OSError [WinError 123]
            # 1. Nettoyer balises HTML/Markdown (y compris échappées comme <\em>)
            import re
            prompt_slug = re.sub(r'<[^>]*>', '', prompt_slug)  # Balises normales
            prompt_slug = re.sub(r'<\\[^>]*>', '', prompt_slug)  # Balises échappées <\em>
            
            # 2. Remplacer DIRECTEMENT les caractères interdits Windows (<>:"/\|?*)
            invalid_chars = r'<>:"/\|?*'
            prompt_slug = ''.join(c if c not in invalid_chars else '-' for c in prompt_slug)
            
            # 3. Remplacer les accents par équivalents ASCII (é→e, à→a, etc.)
            import unicodedata
            prompt_slug = unicodedata.normalize('NFKD', prompt_slug)
            prompt_slug = prompt_slug.encode('ascii', 'ignore').decode('ascii')
            
            # 4. Garder uniquement alphanumériques, espaces et tirets
            prompt_slug = "".join(c if c.isalnum() or c in (' ', '-') else '' for c in prompt_slug).strip()
            prompt_slug = prompt_slug.replace(' ', '-')

            provider = metadata.get('provider', 'unknown').lower()
            
            # 🎲 BATCH SUPPORT: Ajouter suffixe -v{N} pour éviter écrasement
            batch_index = metadata.get('batch_index')
            if batch_index:
                filename = f"{provider}-{timestamp}-{prompt_slug}-v{batch_index}.png"
            else:
                filename = f"{provider}-{timestamp}-{prompt_slug}.png"
            
            filepath = self.generated_images_dir / filename

            # Sauvegarder l'image
            with open(filepath, 'wb') as f:
                f.write(image_bytes)

            print(f"[TEXT2IMG-MANAGER] 💾 Image sauvegardée: {filepath}")

            # Ajouter aux métadonnées
            metadata['filename'] = filename
            metadata['filepath'] = str(filepath)

            # Ajouter à l'historique
            self.history.append(metadata)
            self._save_history()

            return filepath, None

        except Exception as e:
            error_msg = f"Erreur sauvegarde: {str(e)}"
            print(f"[TEXT2IMG-MANAGER] ❌ {error_msg}")
            return None, error_msg

    def get_available_providers(self) -> List[str]:
        """Retourne les providers disponibles"""
        if self.backend:
            return self.backend.get_available_providers()
        return []

    def get_provider_models(self, provider: str) -> List[str]:
        """Retourne les modèles pour un provider"""
        if self.backend:
            return self.backend.get_provider_models(provider)
        return []

    def provider_supports_nsfw(self, provider: str) -> bool:
        """Vérifie si un provider supporte Unfiltered"""
        if self.backend:
            return self.backend.provider_supports_nsfw(provider)
        return False

    def get_history(self, limit: int = 50) -> List[Dict]:
        """Retourne l'historique des générations"""
        return self.history[-limit:] if limit else self.history

    def get_backend_info(self) -> Dict[str, Any]:
        """Retourne les informations sur le backend"""
        if not self.backend:
            return {"status": "non initialisé", "providers": []}
        
        providers = self.backend.get_available_providers()
        return {
            "status": "actif" if providers else "aucun provider",
            "providers": providers,
            "providers_info": {
                p: {
                    "models": self.backend.get_provider_models(p),
                    "nsfw_support": self.backend.provider_supports_nsfw(p)
                }
                for p in providers
            }
        }

    def _load_history(self):
        """Charge l'historique depuis le fichier JSON"""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
                print(f"[TEXT2IMG-MANAGER] 📜 Historique chargé: {len(self.history)} générations")
            else:
                self.history = []
        except Exception as e:
            print(f"[TEXT2IMG-MANAGER] ⚠️ Erreur chargement historique: {e}")
            self.history = []

    def _save_history(self):
        """Sauvegarde l'historique dans le fichier JSON"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[TEXT2IMG-MANAGER] ⚠️ Erreur sauvegarde historique: {e}")
