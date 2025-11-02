"""
Manager principal de l'extension Text2Image
============================================
Orchestre la génération d'images, la sauvegarde et l'historique.
"""

import asyncio
import json
from typing import Optional, Dict, Any, List
from pathlib import Path
from datetime import datetime
import uuid

from .perchance_http_backend import PerchanceHTTPBackend

class Text2ImageManager:
    """Gestionnaire principal de génération d'images"""

    def __init__(self, settings_manager):
        self.settings_manager = settings_manager
        self.backend = None
        self.history = []

        # Chemins
        self.generated_images_dir = Path("data/generated_images")
        self.history_file = self.generated_images_dir / "generation_history.json"

        # Créer le dossier si nécessaire
        self.generated_images_dir.mkdir(parents=True, exist_ok=True)

        # Charger l'historique
        self._load_history()

    def initialize_backend(self) -> bool:
        """
        Initialise le backend de génération (actuellement Perchance HTTP)

        Returns:
            bool: True si l'initialisation a réussi
        """
        try:
            print("[TEXT2IMG-MANAGER] 🔧 Initialisation backend...")

            # Utiliser le backend HTTP (plus fiable que la lib Python)
            # Passer settings_manager pour accès aux paramètres custom
            self.backend = PerchanceHTTPBackend(settings_manager=self.settings_manager)
            success = self.backend.initialize()

            if success:
                print("[TEXT2IMG-MANAGER] ✅ Backend initialisé")
                return True
            else:
                print("[TEXT2IMG-MANAGER] ❌ Échec initialisation backend")
                return False

        except Exception as e:
            print(f"[TEXT2IMG-MANAGER] ❌ Erreur initialisation backend: {e}")
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
            **kwargs: Paramètres additionnels (width, height, etc.)

        Returns:
            tuple: (image_bytes, error_message, metadata)
                - Si succès: (bytes, None, metadata)
                - Si échec: (None, error_message, None)
        """
        if not self.backend or not self.backend.is_available:
            return None, "Backend non disponible", None

        try:
            # Récupérer les paramètres depuis settings image_generation (compatible avec ancien système)
            img_settings = self.settings_manager.settings.get('image_generation', {})
            text2img_settings = self.settings_manager.settings.get('text2img', {})

            width = kwargs.get('width', img_settings.get('default_width', 1024))
            height = kwargs.get('height', img_settings.get('default_height', 1024))
            model = kwargs.get('model', img_settings.get('model', text2img_settings.get('model', 'flux')))
            safe_mode = kwargs.get('safe_mode', img_settings.get('safe_mode', text2img_settings.get('safe_mode', True)))
            enhance = kwargs.get('enhance', text2img_settings.get('enhance', False))
            nologo = kwargs.get('nologo', text2img_settings.get('nologo', True))
            seed = kwargs.get('seed', text2img_settings.get('seed', None))

            # Générer l'image
            image_bytes, error = await self.backend.generate_image(
                prompt=prompt,
                width=width,
                height=height,
                model=model,
                safe_mode=safe_mode,
                enhance=enhance,
                nologo=nologo,
                seed=seed
            )

            if error:
                return None, error, None

            # Créer les métadonnées
            metadata = {
                "timestamp": datetime.now().isoformat(),
                "prompt": prompt,
                "width": width,
                "height": height,
                "model": model,
                "safe_mode": safe_mode,
                "enhance": enhance,
                "seed": seed,
                "backend": self.backend.backend_name
            }

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

        Args:
            image_bytes: Données binaires de l'image
            metadata: Métadonnées de génération

        Returns:
            tuple: (chemin_fichier, error_message)
                - Si succès: (Path, None)
                - Si échec: (None, error_message)
        """
        try:
            # Vérifier si la sauvegarde est activée
            settings = self.settings_manager.settings.get('text2img', {})
            if not settings.get('save_images', True):
                print("[TEXT2IMG-MANAGER] ℹ️ Sauvegarde désactivée")
                return None, None

            # Générer le nom de fichier
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            prompt_slug = metadata.get('prompt', 'image')[:30]
            prompt_slug = "".join(c if c.isalnum() or c in (' ', '-', '_') else '' for c in prompt_slug).strip()
            prompt_slug = prompt_slug.replace(' ', '_')

            filename = f"generated_{timestamp}_{prompt_slug}.png"
            filepath = self.generated_images_dir / filename

            # Sauvegarder l'image
            with open(filepath, 'wb') as f:
                f.write(image_bytes)

            print(f"[TEXT2IMG-MANAGER] 💾 Image sauvegardée: {filepath}")

            # Ajouter le filename aux métadonnées
            metadata['filename'] = filename
            metadata['filepath'] = str(filepath)

            # Ajouter à l'historique
            self.history.append(metadata)
            self._save_history()

            return filepath, None

        except Exception as e:
            error_msg = f"Erreur sauvegarde: {str(e)}"
            print(f"[TEXT2IMG-MANAGER] ❌ {error_msg}")
            import traceback
            traceback.print_exc()
            return None, error_msg

    def _load_history(self):
        """Charge l'historique des générations depuis le fichier JSON"""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.history = json.load(f)
                print(f"[TEXT2IMG-MANAGER] 📜 Historique chargé: {len(self.history)} générations")
            else:
                self.history = []
                print(f"[TEXT2IMG-MANAGER] 📜 Aucun historique existant")
        except Exception as e:
            print(f"[TEXT2IMG-MANAGER] ⚠️ Erreur chargement historique: {e}")
            self.history = []

    def _save_history(self):
        """Sauvegarde l'historique des générations dans le fichier JSON"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, indent=2, ensure_ascii=False)
            print(f"[TEXT2IMG-MANAGER] 📜 Historique sauvegardé: {len(self.history)} générations")
        except Exception as e:
            print(f"[TEXT2IMG-MANAGER] ⚠️ Erreur sauvegarde historique: {e}")

    def get_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Récupère l'historique des générations

        Args:
            limit: Nombre maximum de résultats (None = tous)

        Returns:
            List[Dict]: Liste des métadonnées de génération
        """
        if limit:
            return self.history[-limit:]
        return self.history

    def get_backend_info(self) -> Optional[Dict[str, Any]]:
        """
        Retourne les informations sur le backend actif

        Returns:
            dict: Informations du backend, ou None si non disponible
        """
        if self.backend:
            return self.backend.get_backend_info()
        return None
