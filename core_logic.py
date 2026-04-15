"""
core_logic.py
----------------
- MODIFICATION ARCHITECTURALE : La classe `MemoryStructure` a été dotée d'un
  système de sauvegarde et de restauration automatique pour prévenir la perte de données.
- MODIFICATION (`save_memories`) :
  - Avant chaque sauvegarde, une copie de l'ancien fichier mémoire est créée dans un
    nouveau dossier `data/memory/backup/`.
  - Une rotation est effectuée pour ne conserver que les 4 sauvegardes les plus récentes.
- MODIFICATION (`load_memories`) :
  - Si le fichier mémoire principal est corrompu, le système tente maintenant de charger
    automatiquement la sauvegarde la plus récente.
  - La mémoire n'est réinitialisée à zéro qu'en cas d'échec du chargement du fichier
    principal ET de sa dernière sauvegarde.
"""
import json
import re
import asyncio
import requests
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import datetime
import traceback
import shutil
import os
import base64
import io

# Import PIL pour compression images vision
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("[WARN] PIL non disponible - compression images désactivée")

# ╔═══════════════════════════════════════════════════════════════════════════╗
# ║  🔬 DEBUG_TOKEN_TRACKING - TEMPORAIRE - SUPPRIMER APRÈS ANALYSE          ║
# ╚═══════════════════════════════════════════════════════════════════════════╝
try:
    from archiviste_logger import get_archiviste_logger
    ARCHIVISTE_LOGGING_ENABLED = True
    print("[DEBUG-TOKEN] ✅ Logging Archiviste activé")
except ImportError:
    ARCHIVISTE_LOGGING_ENABLED = False
    print("[DEBUG-TOKEN] ⚠️ archiviste_logger.py introuvable")
# ╚═══════════════════════════════════════════════════════════════════════════╝

# Détection et imports pour GGUF/llama.cpp
try:
    from llama_cpp import Llama
    LlamaCPP_AVAILABLE = True
    print("[OK] (core_logic) Bibliothèque llama-cpp-python de base trouvée.")
except ImportError:
    LlamaCPP_AVAILABLE = False
    print("[WARN] (core_logic) Bibliothèque llama-cpp-python non trouvée. Le fallback GGUF sera désactivé.")
LlamaCPP_VISION_AVAILABLE = False
if LlamaCPP_AVAILABLE:
    try:
        from llama_cpp.llama_chat_format import LlamaLlavaChatHandler
        LlamaCPP_VISION_AVAILABLE = True
        print("[OK] (core_logic) Composant Vision pour GGUF trouvé.")
    except ImportError:
        LlamaCPP_VISION_AVAILABLE = False
        print("[INFO] (core_logic) Composant Vision pour GGUF non trouvé. Le mode texte seul est activé pour GGUF.")
else: LlamaCPP_VISION_AVAILABLE = False
# ═══════════════════════════════════════════════════════════════════════════
# 🖼️ COMPRESSION IMAGES VISION - Réduit la taille des images pour l'API
# ═══════════════════════════════════════════════════════════════════════════
def _get_vision_compression_size() -> int:
    """Récupère la taille de compression depuis settings.json"""
    try:
        settings_path = Path(__file__).parent / "data" / "settings.json"
        if settings_path.exists():
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            img_config = settings.get('image_generation', {})
            return img_config.get('vision_compression', 400)
    except Exception as e:
        print(f"[VISION-COMPRESS] ⚠️ Erreur lecture settings: {e}")
    return 400  # Défaut: 400px

def _compress_vision_image(base64_data: str) -> str:
    """
    Compresse une image base64 pour l'API vision.
    Redimensionne à une taille fixe configurée dans settings.
    
    Args:
        base64_data: Image en base64 (avec ou sans préfixe data:image)
    
    Returns:
        Image compressée en base64 (format JPEG)
    """
    if not PIL_AVAILABLE:
        print("[VISION-COMPRESS] ⚠️ PIL non disponible, image non compressée")
        return base64_data
    
    target_size = _get_vision_compression_size()
    
    # Si compression désactivée (0 ou "sans")
    if target_size == 0:
        print("[VISION-COMPRESS] ⚪ Compression désactivée")
        return base64_data
    
    try:
        # Extraire les données base64 pures
        if 'base64,' in base64_data:
            pure_b64 = base64_data.split('base64,')[1]
        else:
            pure_b64 = base64_data
        
        # Décoder l'image
        img_bytes = base64.b64decode(pure_b64)
        img = Image.open(io.BytesIO(img_bytes))
        
        original_size = len(pure_b64)
        original_dims = f"{img.width}x{img.height}"
        
        # Convertir en RGB si nécessaire (pour JPEG)
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Redimensionner à taille fixe (carré)
        img.thumbnail((target_size, target_size), Image.Resampling.LANCZOS)
        
        # Compresser en JPEG qualité 85
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=85, optimize=True)
        compressed_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        new_size = len(compressed_b64)
        new_dims = f"{img.width}x{img.height}"
        ratio = (1 - new_size / original_size) * 100 if original_size > 0 else 0
        
        print(f"[VISION-COMPRESS] ✅ {original_dims} → {new_dims} | {original_size//1024}KB → {new_size//1024}KB ({ratio:.0f}% réduit)")
        
        return compressed_b64
        
    except Exception as e:
        print(f"[VISION-COMPRESS] ❌ Erreur compression: {e}")
        return base64_data


class SettingsManager:
    def __init__(self, filepath: Path):
        self.filepath = filepath
        self._load_failed = False  # Flag pour bloquer save si load a échoué
        self._default_settings = {
            "reasoning_api": {
                "provider": "Aucun", 
                "api_key": "", 
                "api_model": "", 
                "ollama_model": "", 
                "gguf_model": "", 
                "max_tokens": -1, 
                "context_length": -1, 
                "temperature": 0.7,
                "backend_type": "API",
                "ollama_url": "http://localhost:11434",
                "kobold_url": "http://localhost:5001"
            }, 
            "embedding_api": {
                "provider": "Aucun", 
                "api_key": "", 
                "api_model": "", 
                "ollama_model": "", 
                "gguf_model": "",
                "backend_type": "API",
                "ollama_url": "http://localhost:11434"
            }, 
            "chat_api": {
                "provider": "Aucun", 
                "api_key": "", 
                "api_model": "", 
                "ollama_model": "", 
                "gguf_model": "", 
                "max_tokens": -1, 
                "context_length": -1, 
                "temperature": 0.7,
                "backend_type": "API",
                "ollama_url": "http://localhost:11434",
                "kobold_url": "http://localhost:5001"
            }, 
            "perception_agent": {
                "webcam_index": 0, 
                "triage_resolution": [320, 240], 
                "fps_limit": 0.2, 
                "ollama_url": "http://localhost:11434/api/generate", 
                "triage_model": "moondream:latest", 
                "triage_prompt": "Décris cette image en trois mots."
            }, 
            "image_generation": {
                "enabled": True, 
                "default_width": 1024, 
                "default_height": 1024, 
                "save_images": True, 
                "use_turbo": False,
                "ai_can_see_images": True
            }, 
            "prompts": {
                "instructions": "(Fallback - voir settings.json)", 
                "memorization": "(Fallback - voir settings.json)", 
                "injection": "(Fallback - voir settings.json)", 
                "perception": "(Fallback - voir settings.json)"
            }
        }
        self.settings = {}
        self.load_settings()
    
    def load_settings(self):
        """Charge les settings depuis le fichier JSON. Ne modifie JAMAIS le fichier."""
        print(f"[LOAD] Chargement des paramètres depuis {self.filepath}...")
        self._load_failed = False
        
        # Commencer avec les valeurs par défaut
        import copy
        self.settings = copy.deepcopy(self._default_settings)
        
        try:
            if self.filepath.exists():
                # Utiliser utf-8-sig pour gérer le BOM automatiquement
                with open(self.filepath, 'r', encoding='utf-8-sig') as f:
                    loaded_settings = json.load(f)
                    
                    # Vérifier que le fichier contient des données valides (pas juste des defaults)
                    if loaded_settings.get('chat_api', {}).get('provider') == 'Aucun' and \
                       loaded_settings.get('api_keys_vault') is None:
                        print("[WARN] ⚠️ Le fichier settings.json semble contenir des valeurs par défaut!")
                    
                    def update(d, u):
                        for k, v in u.items():
                            if isinstance(v, dict): 
                                d[k] = update(d.get(k, {}), v)
                            else: 
                                d[k] = v
                        return d
                    
                    self.settings = update(self.settings, loaded_settings)
                    print("   -> ✅ Paramètres chargés avec succès.")
            else:
                print(f"   -> ⚠️ Fichier {self.filepath} n'existe pas, utilisation des valeurs par défaut.")
                self._load_failed = True
                
        except Exception as e:
            print(f"[ERROR] ❌ Erreur CRITIQUE lors du chargement des paramètres: {e}")
            print(f"[ERROR] ⛔ La sauvegarde est BLOQUÉE pour protéger vos données!")
            print(f"[ERROR] 💡 Corrigez le fichier manuellement ou restaurez depuis settings_old.json")
            self._load_failed = True
    
    def _create_backup(self):
        """Crée un backup horodaté avant toute sauvegarde."""
        if self.filepath.exists():
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_dir = self.filepath.parent / "backups"
            backup_dir.mkdir(exist_ok=True)
            backup_path = backup_dir / f"settings_backup_{timestamp}.json"
            
            import shutil
            shutil.copy2(self.filepath, backup_path)
            print(f"[BACKUP] 💾 Backup créé: {backup_path.name}")
            
            # Garder seulement les 4 derniers backups
            backups = sorted(backup_dir.glob("settings_backup_*.json"), reverse=True)
            for old_backup in backups[4:]:
                old_backup.unlink()
                print(f"[BACKUP] 🗑️ Ancien backup supprimé: {old_backup.name}")
    
    def save_settings(self):
        """Sauvegarde les settings avec protection et backup automatique."""
        # PROTECTION: Ne jamais sauvegarder si le chargement a échoué
        if self._load_failed:
            error_msg = "[ERROR] ⛔ Sauvegarde REFUSÉE - Le chargement initial a échoué!"
            print(error_msg)
            print("[ERROR] 💡 Rechargez l'application après avoir corrigé settings.json")
            return error_msg
        
        # PROTECTION: Vérifier que les settings ne sont pas des valeurs par défaut vides
        if self.settings.get('chat_api', {}).get('provider') == 'Aucun' and \
           self.settings.get('api_keys_vault') is None and \
           len(self.settings.get('prompts', {}).get('instructions', '')) < 100:
            error_msg = "[ERROR] ⛔ Sauvegarde REFUSÉE - Les settings semblent être des valeurs par défaut!"
            print(error_msg)
            return error_msg
        
        try:
            self.filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Créer un backup avant sauvegarde
            self._create_backup()
            
            # Sauvegarder avec encodage UTF-8 sans BOM
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            
            print(f"[SAVE] ✅ Paramètres sauvegardés dans {self.filepath}.")
            return "[OK] Paramètres sauvegardés."
            
        except Exception as e:
            error_msg = f"[ERREUR] Erreur de sauvegarde des paramètres : {e}"
            print(error_msg)
            return error_msg
class OllamaManager:
    def __init__(self):
        self.is_available, self.models, self.api_url = False, [], "http://localhost:11434"
        self.settings_manager = None  # Sera initialisé depuis ogma_ng.py
        self._model_ctx_cache = {}  # Cache contexte réel par modèle

    def set_settings_manager(self, settings_manager):
        """Configure le gestionnaire de paramètres pour accéder aux settings."""
        self.settings_manager = settings_manager
    
    def get_low_vram_setting(self) -> bool:
        """Récupère le paramètre low_vram depuis les settings."""
        if self.settings_manager:
            return self.settings_manager.settings.get('other_backends', {}).get('ollama', {}).get('low_vram', False)
        return False  # Par défaut, utiliser GPU (low_vram=False)

    def get_timeout_setting(self) -> int:
        """Récupère le timeout Ollama depuis les settings."""
        if self.settings_manager:
            return int(self.settings_manager.settings.get('other_backends', {}).get('ollama', {}).get('timeout', 180))
        return 180

    async def _get_model_context_length(self, model: str) -> Optional[int]:
        """Récupère la vraie fenêtre de contexte d'un modèle Ollama via /api/show."""
        if model in self._model_ctx_cache:
            return self._model_ctx_cache[model]
        try:
            response = await asyncio.to_thread(
                requests.post, f'{self.api_url}/api/show',
                json={"name": model}, timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                model_info = data.get('model_info', {})
                for key, value in model_info.items():
                    if 'context_length' in key and isinstance(value, int):
                        print(f"[OLLAMA-CTX] Contexte réel {model}: {value} tokens")
                        self._model_ctx_cache[model] = value
                        return value
        except Exception as e:
            print(f"[OLLAMA-CTX] Impossible de détecter le contexte de {model}: {e}")
        return None

    def get_model_context_length_sync(self, model: str) -> Optional[int]:
        """Récupère la vraie fenêtre de contexte d'un modèle Ollama via /api/show (sync, pour init)."""
        if model in self._model_ctx_cache:
            return self._model_ctx_cache[model]
        try:
            response = requests.post(f'{self.api_url}/api/show', json={"name": model}, timeout=10)
            if response.status_code == 200:
                data = response.json()
                model_info = data.get('model_info', {})
                for key, value in model_info.items():
                    if 'context_length' in key and isinstance(value, int):
                        print(f"[OLLAMA-CTX] Contexte réel {model}: {value} tokens")
                        self._model_ctx_cache[model] = value
                        return value
        except Exception as e:
            print(f"[OLLAMA-CTX] Impossible de détecter le contexte de {model}: {e}")
        return None

    def check_service(self) -> bool:
        print("[SEARCH] Vérification du service Ollama...")
        try:
            response = requests.get(f'{self.api_url}/api/tags', timeout=5)
            if response.status_code == 200:
                self.models = [model['name'] for model in response.json().get('models', [])]
                if self.models:
                    self.is_available = True
                    print(f"[OK] Ollama est disponible. Modèles: {self.models}")
                    return True
        except Exception: pass
        self.is_available = False
        print("[ERREUR] Ollama n'est pas disponible.")
        return False
    async def call_chat_api(self, model: str, messages: List[Dict], max_tokens: int, context_length: int, temperature: float, is_json: bool = True) -> tuple[Optional[str], Optional[str]]:
        if not self.is_available: return None, "Ollama n'est pas disponible."
        print(f"[AI] Appel du modèle Ollama '{model}'...")
        ollama_messages = []
        for msg in messages:
            new_msg, images_base64, content = {"role": msg["role"], "content": ""}, [], msg.get('content')
            if isinstance(content, list):
                for part in content:
                    if part.get('type') == 'text': new_msg["content"] += part.get('text', '') + "\n"
                    elif part.get('type') == 'image_url':
                        image_url = part.get('image_url', {}).get('url', '')
                        if 'base64,' in image_url: images_base64.append(image_url.split('base64,')[1])
            elif isinstance(content, str): new_msg["content"] = content
            new_msg["content"] = new_msg["content"].strip()
            if images_base64: new_msg["images"] = images_base64
            ollama_messages.append(new_msg)
        # Gestion context_length = -1 : résoudre avec la vraie valeur du modèle
        if context_length == -1:
            real_ctx = await self._get_model_context_length(model)
            final_context_length = real_ctx if real_ctx else 8192
            print(f"[OLLAMA-GUARD] context_length=-1 résolu → {final_context_length}")
        else:
            final_context_length = context_length
        # Gestion max_tokens = -1
        if max_tokens == -1:
            final_max_tokens = min(4096, final_context_length - 512) if final_context_length > 512 else 4096
            print(f"[OLLAMA-GUARD] max_tokens=-1 résolu → {final_max_tokens}")
        else:
            final_max_tokens = max_tokens

        # Paramètres dynamiques selon configuration utilisateur
        low_vram_setting = self.get_low_vram_setting()
        
        # Options Ollama optimisées pour RTX 5070Ti 16GB VRAM
        stable_options = {
            "temperature": temperature,
            "num_predict": final_max_tokens,
            "num_ctx": final_context_length,
            # Paramètres optimisés RTX 5070Ti
            "num_thread": 8,          # Plus de threads pour GPU puissant
            "repeat_penalty": 1.1,    # Anti-répétition modéré
            "top_k": 40,              # Limitation choix pour stabilité
            "top_p": 0.9,             # Échantillonnage conservateur
            "num_batch": 512,         # Batch plus élevé avec 16GB VRAM
            "low_vram": low_vram_setting,  # DYNAMIQUE selon paramètre utilisateur
            "numa": False             # Pas de NUMA (PC gaming standard)
        }
        
        payload = {"model": model, "messages": ollama_messages, "stream": False, "options": stable_options}
        if is_json: payload["format"] = "json"
        
        # DEBUG Temporaire: Log détaillé pour diagnostiquer
        print(f"[OLLAMA-DEBUG] Modèle demandé: {model}")
        print(f"[OLLAMA-DEBUG] URL: {self.api_url}/api/chat")
        print(f"[OLLAMA-DEBUG] Payload: {payload}")
        
        try:
            response = await asyncio.to_thread(requests.post, f'{self.api_url}/api/chat', json=payload, timeout=self.get_timeout_setting())
            response.raise_for_status()
            return response.json().get('message', {}).get('content', ''), None
        except Exception as e:
            error_str = str(e).lower()
            # Détecter les erreurs de mémoire/contexte Ollama
            if any(kw in error_str for kw in ['system memory', 'out of memory', 'context length', 'num_ctx', 'too large']):
                error_msg = (
                    f"Erreur Ollama : memoire insuffisante ou contexte trop grand pour '{payload.get('model', '?')}'. "
                    f"Reduisez context_length dans les parametres d'Ogma ou utilisez un modele plus petit. "
                    f"Utilisez le bouton 'Valeurs optimales' pour calculer automatiquement. Detail : {e}"
                )
            else:
                error_msg = f"Erreur lors de l'appel à Ollama : {e}"
            print(f"[ERREUR] {error_msg}")
            
            # DEBUG: Plus de détails sur l'erreur
            if hasattr(e, 'response') and e.response is not None:
                try:
                    print(f"[OLLAMA-DEBUG] Status Code: {e.response.status_code}")
                    print(f"[OLLAMA-DEBUG] Response Text: {e.response.text}")
                    print(f"[OLLAMA-DEBUG] Response Headers: {dict(e.response.headers)}")
                except:
                    print("[OLLAMA-DEBUG] Impossible de lire la réponse d'erreur")
            
            return None, error_msg
    async def create_embedding(self, model: str, text: str) -> Optional[List[float]]:
        if not self.is_available: return None
        print(f"[EMBED] Création d'un embedding via Ollama '{model}'...")
        payload = {"model": model, "prompt": text}
        try:
            response = await asyncio.to_thread(requests.post, f'{self.api_url}/api/embeddings', json=payload, timeout=15)  # RÉDUIT pour stabilité (était 30)
            response.raise_for_status()
            return response.json().get('embedding')
        except Exception as e:
            print(f"[ERREUR] Erreur création embedding Ollama : {e}")
            return None

    async def list_models(self) -> List[str]:
        """Retourne la liste des modèles disponibles dans Ollama."""
        if not self.is_available:
            # Essayer de recharger les modèles
            self.check_service()
        
        return self.models if self.is_available else []
class GGUFManager:
    def __init__(self):
        self.is_available, self.model_name, self.llm = False, "Aucun", None
        self._requested_ctx = 0
        self.model_path = Path(__file__).parent / "models"
        self.model_path.mkdir(exist_ok=True)
        self.settings_manager = None  # Sera initialisé depuis ogma_ng.py
        self._is_generating = False  # Guard contre les appels concurrents (llama.cpp non thread-safe)
        self._current_stop_event = None  # Event pour stopper le thread producteur en cours

    def set_settings_manager(self, settings_manager):
        """Configure le gestionnaire de paramètres pour accéder aux settings."""
        self.settings_manager = settings_manager
    
    def get_low_vram_setting(self) -> bool:
        """Récupère le paramètre low_vram depuis les settings."""
        if self.settings_manager:
            return self.settings_manager.settings.get('other_backends', {}).get('ollama', {}).get('low_vram', False)
        return False  # Par défaut, utiliser GPU (low_vram=False)
    def get_available_models(self) -> List[str]:
        if not self.model_path.exists(): return []
        return [f.name for f in self.model_path.glob("*.gguf")]
    def load_model(self, model_filename: str, context_length: int, n_gpu_layers: int, projector_filename: Optional[str] = None) -> bool:
        if not LlamaCPP_AVAILABLE or not model_filename:
            self.is_available = False
            return False
        model_file_path = self.model_path / model_filename
        if not model_file_path.exists():
            print(f"[ERREUR] Fichier modèle {model_filename} non trouvé.")
            self.is_available = False
            return False
        chat_handler = None
        if LlamaCPP_VISION_AVAILABLE and projector_filename:
            projector_path = self.model_path / projector_filename
            if projector_path.exists():
                print(f"[OK] Projecteur multimodal trouvé : {projector_filename}. Chargement en mode Vision...")
                chat_handler = LlamaLlavaChatHandler(clip_model_path=str(projector_path))
            else: print(f"[WARN] Fichier projecteur {projector_filename} non trouvé. Chargement en mode texte seul.")
        elif projector_filename: print("[INFO] Un projecteur a été spécifié, mais le support Vision pour GGUF n'est pas disponible.")
        else: print("[INFO] Aucun projecteur multimodal spécifié. Chargement en mode texte seul.")
        print(f"[OK] Chargement du modèle GGUF : {model_filename} avec {n_gpu_layers} couches GPU...")
        old_llm = self.llm
        try:
            # Optimisations pour RTX 5070 Ti - ÉLIMINATION EMBEDDINGS
            # Paramètres dynamiques selon configuration utilisateur
            low_vram_setting = self.get_low_vram_setting()
            
            self.llm = Llama(
                model_path=str(model_file_path), 
                n_ctx=context_length, 
                n_gpu_layers=n_gpu_layers, 
                verbose=False, 
                embedding=False,          # ❌ DÉSACTIVÉ - cause la lenteur !
                chat_handler=chat_handler,
                # Optimisations performance RTX 5070 Ti - STABILITÉ
                n_batch=128,              # 128×vocab×4B = 128MB (safe CPU single-load, 2× plus rapide que 64)
                n_threads=6,              # Réduit pour stabilité (était 8)
                use_mmap=True,            # Memory mapping pour vitesse
                use_mlock=False,          # DÉSACTIVÉ pour stabilité
                rope_scaling_type=1,      # RoPE scaling pour performance
                flash_attn=False,         # DÉSACTIVÉ pour compatibilité
                offload_kqv=True,         # Offload KV cache sur GPU
                split_mode=1,             # Split intelligent GPU/CPU
                main_gpu=0,               # GPU principal
                logits_all=False,         # ❌ Pas de logits pour tous les tokens
                vocab_only=False,         # ❌ Pas de vocabulaire seul
                low_vram=low_vram_setting,  # DYNAMIQUE selon paramètre utilisateur
                # PARAMÈTRES ANTI-EMBEDDING SPÉCIFIQUES
                numa=False,               # Pas de NUMA
                mul_mat_q=True,           # Quantized matrix multiplication
                f16_kv=True,              # FP16 pour KV cache
                seed=-1                   # Seed aléatoire
            )
            self.model_name, self.is_available = model_filename, True
            self._requested_ctx = context_length
            print(f"[OK] Modèle GGUF '{self.model_name}' chargé avec optimisations RTX 5070 Ti.")
            return True
        except Exception as e:
            print(f"[ERREUR] Erreur chargement GGUF : {e}")
            traceback.print_exc()
            self.llm = old_llm
            self.is_available = old_llm is not None
            return False
    async def call_chat_api(self, messages: List[Dict], max_tokens: int, context_length: int, temperature: float, is_json: bool = True) -> tuple[Optional[str], Optional[str]]:
        if not self.is_available or not self.llm: return None, "Modèle GGUF non disponible ou non chargé."
        print(f"[AI] Appel du modèle GGUF local '{self.model_name}'...")
        try:
            # Gestion max_tokens = -1 pour maximum automatique
            final_max_tokens = max_tokens if max_tokens != -1 else 4096  # Valeur par défaut pour GGUF

            # Sécurité : cap max_tokens au contexte réel du modèle pour éviter l'overflow
            model_ctx = self.llm.n_ctx()
            max_safe = max(64, model_ctx - 512)  # 512 tokens réservés pour l'input
            if final_max_tokens > max_safe:
                print(f"[GGUF-DEBUG] max_tokens {final_max_tokens} réduit à {max_safe} (n_ctx={model_ctx})")
                final_max_tokens = max_safe
            
            # Correction pour Gemma : Restructurer pour alternance user/assistant stricte
            processed_messages = []
            system_content = []
            
            # Collecte tous les messages system
            for msg in messages:
                if msg.get('role') == 'system':
                    system_content.append(msg.get('content', ''))
            
            # Ajouter un message system combiné au début
            if system_content:
                combined_system = '\n\n'.join(system_content)
                processed_messages.append({'role': 'system', 'content': combined_system})
            
            # Traiter le reste en s'assurant de l'alternance user/assistant
            last_role = 'system'
            for msg in messages:
                role = msg.get('role')
                content = msg.get('content', '')
                
                if role == 'system':
                    continue  # Déjà traité
                
                if role == 'user':
                    if last_role == 'user':
                        # Si on a déjà un user, on ajoute un assistant vide
                        processed_messages.append({'role': 'assistant', 'content': 'Je comprends.'})
                    processed_messages.append({'role': 'user', 'content': content})
                    last_role = 'user'
                elif role == 'assistant':
                    if last_role == 'assistant':
                        # Si on a déjà un assistant, on ajoute un user vide
                        processed_messages.append({'role': 'user', 'content': 'Continue.'})
                    processed_messages.append({'role': 'assistant', 'content': content})
                    last_role = 'assistant'
            
            total_input_chars = sum(len(m['content']) for m in processed_messages)
            print(f"[GGUF-DEBUG] Messages originaux: {len(messages)}, apres correction: {len(processed_messages)} (~{total_input_chars//4} tokens entree)")
            for i, msg in enumerate(processed_messages):
                print(f"[GGUF-DEBUG] [{i}] {msg['role']}: {msg['content'][:50]}...")
            print(f"[GGUF-DEBUG] Inference CPU en cours (peut prendre 30s-3min)...")
            
            # Paramètres optimisés
            response_format = {"type": "json_object"} if is_json else {"type": "text"}
            _t0 = asyncio.get_event_loop().time()
            response = await asyncio.to_thread(
                self.llm.create_chat_completion, 
                messages=processed_messages, 
                response_format=response_format, 
                temperature=temperature, 
                max_tokens=final_max_tokens,
                repeat_penalty=1.1,
                top_p=0.95,
                top_k=40,
                stream=False
            )
            _elapsed = asyncio.get_event_loop().time() - _t0
            result_text = response['choices'][0]['message']['content']
            print(f"[GGUF-DEBUG] Inference terminee en {_elapsed:.1f}s, reponse: {len(result_text)} chars")
            return result_text, None
        except Exception as e:
            error_msg = f"Erreur lors de l'appel au modèle GGUF : {e}"
            print(f"[ERREUR] {error_msg}")
            return None, error_msg

    async def call_chat_api_streaming(self, messages: List[Dict], max_tokens: int, context_length: int,
                                      temperature: float, callback=None) -> tuple[Optional[str], Optional[str]]:
        """Variante streaming de call_chat_api - appelle callback(chunk) pour chaque token."""
        if not self.is_available or not self.llm:
            return None, "Modèle GGUF non disponible ou non chargé."

        # Guard: llama.cpp n'est pas thread-safe, un seul appel à la fois
        if self._is_generating:
            print("[GGUF-STREAM] Appel rejeté: génération déjà en cours (llama.cpp non thread-safe)")
            return None, "Le modèle GGUF est déjà en cours de génération. Veuillez patienter."

        print(f"[AI] Appel streaming GGUF '{self.model_name}'...")
        import threading as _threading
        import queue as _queue_mod

        stop_event = _threading.Event()
        self._current_stop_event = stop_event
        self._is_generating = True

        try:
            final_max_tokens = max_tokens if max_tokens > 0 else 2048
            model_ctx = self.llm.n_ctx()
            max_safe = max(64, model_ctx - 512)
            if final_max_tokens > max_safe:
                final_max_tokens = max_safe

            processed_messages = []
            system_content = []
            for msg in messages:
                if msg.get('role') == 'system':
                    system_content.append(msg.get('content', ''))
            if system_content:
                processed_messages.append({'role': 'system', 'content': '\n\n'.join(system_content)})
            last_role = 'system'
            for msg in messages:
                role = msg.get('role')
                content = msg.get('content', '')
                if role == 'system':
                    continue
                if role == 'user':
                    if last_role == 'user':
                        processed_messages.append({'role': 'assistant', 'content': 'Je comprends.'})
                    processed_messages.append({'role': 'user', 'content': content})
                    last_role = 'user'
                elif role == 'assistant':
                    if last_role == 'assistant':
                        processed_messages.append({'role': 'user', 'content': 'Continue.'})
                    processed_messages.append({'role': 'assistant', 'content': content})
                    last_role = 'assistant'

            total_input_chars = sum(len(m['content']) for m in processed_messages)
            print(f"[GGUF-STREAM] {len(processed_messages)} messages (~{total_input_chars//4} tokens entree), max_tokens={final_max_tokens}")
            print(f"[GGUF-STREAM] Prefill en cours...")

            loop = asyncio.get_event_loop()
            accumulated = ""
            _t0 = loop.time()

            q = _queue_mod.Queue()

            def _producer():
                try:
                    gen = self.llm.create_chat_completion(
                        messages=processed_messages,
                        temperature=temperature,
                        max_tokens=final_max_tokens,
                        repeat_penalty=1.1,
                        top_p=0.95,
                        top_k=40,
                        stream=True
                    )
                    for chunk_data in gen:
                        if stop_event.is_set():
                            print("[GGUF-STREAM] Thread producteur interrompu (stop_event)")
                            break
                        delta = chunk_data.get('choices', [{}])[0].get('delta', {})
                        text = delta.get('content', '')
                        if text:
                            q.put(text)
                    q.put(None)  # Sentinel fin
                except Exception as ex:
                    q.put(ex)

            producer_thread = _threading.Thread(target=_producer, daemon=True)
            producer_thread.start()

            # Timeout par token: 900s pour le prefill, 60s après le premier token
            first_token_received = False
            while True:
                token_timeout = 900.0 if not first_token_received else 60.0
                try:
                    item = await asyncio.wait_for(
                        loop.run_in_executor(None, q.get),
                        timeout=token_timeout
                    )
                except asyncio.TimeoutError:
                    label = "prefill" if not first_token_received else "token suivant"
                    print(f"[GGUF-STREAM] Timeout attente {label} ({token_timeout:.0f}s)")
                    stop_event.set()  # Signaler au thread de s'arrêter proprement
                    break
                if item is None:
                    break  # Fin normale
                if isinstance(item, Exception):
                    raise item
                first_token_received = True
                accumulated += item
                if callback:
                    await callback(item)

            _elapsed = loop.time() - _t0
            print(f"[GGUF-STREAM] Termine en {_elapsed:.1f}s, {len(accumulated)} chars")
            return accumulated, None
        except Exception as e:
            error_msg = f"Erreur streaming GGUF : {e}"
            print(f"[ERREUR] {error_msg}")
            return None, error_msg
        finally:
            self._is_generating = False
            self._current_stop_event = None
    async def create_embedding(self, text: str) -> Optional[List[float]]:
        # GGUF en mode chat pur - pas d'embeddings pour éviter la lenteur
        print(f"[WARN] Embeddings désactivés sur GGUF pour performance. Utiliser l'API Mistral.")
        return None
    
    def list_models(self) -> List[str]:
        """Retourne la liste des modèles GGUF disponibles ou le modèle chargé."""
        if self.is_available and self.model_name != "Aucun":
            return [self.model_name]
        return self.get_available_models()
    
    def test_connection(self) -> Tuple[bool, str]:
        """Teste si le modèle GGUF est chargé et disponible."""
        if self.is_available and self.llm is not None:
            return True, f"Modèle GGUF '{self.model_name}' chargé et prêt"
        elif self.model_name != "Aucun":
            return False, f"Modèle GGUF '{self.model_name}' configuré mais non chargé"
        else:
            return False, "Aucun modèle GGUF configuré"
class KoboldManager:
    def __init__(self):
        self.is_available, self.api_url = False, "http://localhost:5001"
    def check_service(self) -> bool:
        print("[SEARCH] Vérification du service KoboldCpp...")
        try:
            response = requests.get(f'{self.api_url}/api/v1/model', timeout=5)
            if response.status_code == 200 and "result" in response.json():
                model_name = response.json()["result"]
                self.is_available = True
                print(f"[OK] KoboldCpp est disponible. Modèle: {model_name}")
                return True
        except Exception: pass
        self.is_available = False
        print("[ERREUR] KoboldCpp n'est pas disponible.")
        return False
    async def call_chat_api(self, messages: List[Dict], max_tokens: int, context_length: int, temperature: float, is_json: bool = False) -> tuple[Optional[str], Optional[str]]:
        if not self.is_available: return None, "KoboldCpp n'est pas disponible."
        print("[AI] Appel du modèle KoboldCpp...")
        
        # Gestion max_tokens = -1 pour maximum automatique
        final_max_tokens = max_tokens if max_tokens != -1 else 2048  # Valeur par défaut pour KoboldCpp
        # Gestion context_length = -1 pour maximum automatique  
        final_context_length = context_length if context_length != -1 else 8192
        
        full_prompt = "".join(part.get('text', '') + "\n\n" if isinstance(msg.get('content'), list) else msg.get('content', '') + "\n\n" for msg in messages for part in msg.get('content', []) if isinstance(msg.get('content'), list) and part.get('type') == 'text' or not isinstance(msg.get('content'), list))
        payload = {"prompt": full_prompt.strip(), "max_context_length": final_context_length, "max_length": final_max_tokens, "temperature": temperature}
        try:
            response = await asyncio.to_thread(requests.post, f'{self.api_url}/api/v1/generate', json=payload, timeout=180)  # Augmenté à 180s pour requêtes lourdes
            response.raise_for_status()
            return response.json()['results'][0]['text'], None
        except Exception as e:
            error_msg = f"Erreur lors de l'appel à KoboldCpp : {e}"
            print(f"[ERREUR] {error_msg}")
            return None, error_msg
import re


class APIManager:
    API_CONFIG = {
        "OpenAI": {
            "base_url": "https://api.openai.com/v1",
            "chat_endpoint": "/chat/completions",
            "models_endpoint": "/models",
            "embed_endpoint": "/embeddings"
        },
        "Anthropic": {
            "base_url": "https://api.anthropic.com/v1",
            "chat_endpoint": "/messages",
            "models_endpoint": None
        },
        "Mistral": {
            "base_url": "https://api.mistral.ai/v1",
            "chat_endpoint": "/chat/completions",
            "models_endpoint": "/models",
            "embed_endpoint": "/embeddings"
        },
        "Google": {
            "base_url": "https://generativelanguage.googleapis.com/v1beta",
            "chat_endpoint": "/models/gemini-1.0-pro:generateContent",
            "models_endpoint": "/models",
            "embed_endpoint": None
        },
        "GROK": {
            "base_url": "https://api.x.ai/v1",
            "chat_endpoint": "/chat/completions",
            "models_endpoint": "/models",
            "embed_endpoint": "/embeddings"
        },
        "OpenRouter": {
            "base_url": "https://openrouter.ai/api/v1",
            "chat_endpoint": "/chat/completions",
            "models_endpoint": "/models",
            "embed_endpoint": "/embeddings"
        },
        "AIHorde": {
            "base_url": "https://stablehorde.net/api/v2",
            "chat_endpoint": "/generate/text/async",
            "models_endpoint": "/workers",
            "embed_endpoint": None
        }
    }
    ANTHROPIC_MODELS = [
        # Current working models (2025) - Fallback list
        "claude-sonnet-4-20250514",
        "claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022",
        # Stable legacy models (still functional)
        "claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307",
        # Older models (may work)
        "claude-2.1", "claude-2.0", "claude-instant-1.2"
    ]
    GROK_MODELS = [
        # Current working models (2025) - Fallback list
        "grok-4",
        "grok-3-mini", "grok-3-mini-fast",
        "grok-code-fast-1",
        "grok-2-012", "grok-2-vision-012"
    ]
    def __init__(self):
        self.is_available, self.provider, self.model, self.api_key = False, "Aucun", "", ""
        self._last_thinking_content = ""  # Contenu thinking des modèles de raisonnement
        self.openrouter_thinking = False  # Activer/désactiver le mode thinking OpenRouter
    def configure(self, provider: str, api_key: str, model: str):
        if provider != "Aucun" and api_key and model:
            self.provider, self.api_key, self.model, self.is_available = provider, api_key, model, True
            return f"[OK] API Manager activé pour {provider} avec le modèle {model}."
        self.is_available, self.provider, self.api_key, self.model = False, "Aucun", "", ""
        return "[ERREUR] Configuration API invalide."
    async def list_models(self, api_key: str, provider: str) -> Tuple[List[str], Optional[str]]:
        if not api_key: return [], "La clé API ne peut pas être vide."
        if provider not in self.API_CONFIG and provider != "AIHorde": return [], f"Le fournisseur '{provider}' n'est pas supporté."
        
        def _redact_error(msg: str) -> str:
            """Masque la clé API et tokens similaires dans un message d'erreur."""
            try:
                if not msg:
                    return msg
                redacted = msg
                if api_key:
                    # Remplacer la clé brute
                    redacted = redacted.replace(api_key, '***')
                # Masquer les occurrences type key=XXXX
                redacted = re.sub(r'(key=)([^&\s]+)', r'\1***', redacted, flags=re.IGNORECASE)
                # Masquer les Bearer tokens
                redacted = re.sub(r'(Bearer\s+)[A-Za-z0-9._-]+', r'\1***', redacted, flags=re.IGNORECASE)
                return redacted
            except Exception:
                return "Erreur réseau (détails masqués)"
        
        # Pour Anthropic, récupérer la liste dynamiquement via API
        if provider == "Anthropic":
            try:
                headers = {
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01"
                }
                params = {"limit": 50}  # Récupérer plus de modèles
                
                response = await asyncio.to_thread(
                    requests.get, 
                    "https://api.anthropic.com/v1/models",
                    headers=headers,
                    params=params,
                    timeout=15
                )
                response.raise_for_status()
                models_data = response.json()
                
                # Extraire les modèles selon la spec API
                models = []
                for model in models_data.get("data", []):
                    if model.get("type") == "model":  # Vérifier le type
                        model_id = model.get("id")
                        display_name = model.get("display_name", model_id)
                        if model_id:
                            models.append(model_id)
                            print(f"[API] Trouvé : {model_id} ({display_name})")
                
                if models:
                    print(f"[API] {len(models)} modèles Anthropic récupérés via API")
                    # Les plus récents sont listés en premier selon la doc
                    return models, None
                else:
                    print("[WARN] Aucun modèle Anthropic valide trouvé dans la réponse API")
                    return self.ANTHROPIC_MODELS, "Aucun modèle trouvé via API, utilisation de la liste de fallback"
                    
            except requests.exceptions.HTTPError as e:
                error_detail = ""
                if e.response:
                    try:
                        error_data = e.response.json()
                        error_detail = f" - {error_data.get('error', {}).get('message', 'Erreur inconnue')}"
                    except:
                        error_detail = f" - Status {e.response.status_code}"
                
                print(f"[WARN] Erreur HTTP récupération modèles Anthropic{error_detail}")
                return self.ANTHROPIC_MODELS, f"Erreur API Anthropic{error_detail}, utilisation de la liste de fallback"
                
            except Exception as e:
                print(f"[WARN] Erreur récupération modèles Anthropic : {type(e).__name__} - {e}")
                return self.ANTHROPIC_MODELS, f"Erreur de connexion ({type(e).__name__}), utilisation de la liste de fallback"

        # Pour GROK, tenter de récupérer la liste dynamiquement via API
        if provider == "GROK":
            try:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                url = f"{self.API_CONFIG['GROK']['base_url']}{self.API_CONFIG['GROK']['models_endpoint']}"

                response = await asyncio.to_thread(
                    requests.get,
                    url,
                    headers=headers,
                    timeout=15
                )
                response.raise_for_status()
                models_data = response.json().get('data', [])

                if models_data:
                    models = sorted([m['id'] for m in models_data])
                    print(f"[API] {len(models)} modèles GROK récupérés via API")
                    return models, None
                else:
                    print("[WARN] Aucun modèle GROK trouvé dans la réponse API")
                    return self.GROK_MODELS, "Aucun modèle trouvé via API, utilisation de la liste de fallback"

            except requests.exceptions.HTTPError as e:
                error_detail = ""
                if e.response:
                    try:
                        error_data = e.response.json()
                        error_detail = f" - {error_data.get('error', {}).get('message', 'Erreur inconnue')}"
                    except:
                        error_detail = f" - Status {e.response.status_code}"

                print(f"[WARN] Erreur HTTP récupération modèles GROK{error_detail}")
                return self.GROK_MODELS, f"Erreur API GROK{error_detail}, utilisation de la liste de fallback"

            except Exception as e:
                print(f"[WARN] Erreur récupération modèles GROK : {type(e).__name__} - {e}")
                return self.GROK_MODELS, f"Erreur de connexion ({type(e).__name__}), utilisation de la liste de fallback"

        if provider == "OpenRouter":
            try:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/ogma-ia/ogma",
                    "X-Title": "OGMA AI Assistant"
                }
                url = f"{self.API_CONFIG['OpenRouter']['base_url']}{self.API_CONFIG['OpenRouter']['models_endpoint']}"
                response = await asyncio.to_thread(requests.get, url, headers=headers, timeout=15)
                response.raise_for_status()
                models_data = response.json().get('data', [])
                if models_data:
                    # Filtrer les modèles de chat/completion (exclure les modèles d'image/embedding)
                    chat_models = sorted([
                        m['id'] for m in models_data
                        if not any(x in m['id'].lower() for x in ['embed', 'stable-diffusion', 'dall-e', 'whisper'])
                    ])
                    print(f"[API] {len(chat_models)} mod\u00e8les OpenRouter r\u00e9cup\u00e9r\u00e9s via API")
                    return chat_models, None
                else:
                    return [], "Aucun mod\u00e8le trouv\u00e9 sur OpenRouter."
            except requests.exceptions.HTTPError as e:
                if e.response and e.response.status_code == 401:
                    return [], "Cl\u00e9 API OpenRouter invalide ou non autoris\u00e9e."
                return [], f"Erreur HTTP OpenRouter: {e.response.status_code if e.response else 'inconnue'}"
            except Exception as e:
                return [], f"Erreur connexion OpenRouter: {type(e).__name__}"

        if provider == "AIHorde":
            try:
                url = "https://stablehorde.net/api/v2/workers"
                headers = {"apikey": api_key, "Content-Type": "application/json"}
                response = await asyncio.to_thread(requests.get, url, headers=headers, timeout=10)
                response.raise_for_status()
                workers = response.json()
                
                # Collecter tous les modèles uniques des workers
                models = set()
                for worker in workers:
                    for model in worker.get('models', []):
                        if isinstance(model, str) and not model.startswith('stable_diffusion'):  # Exclure les modèles d'image
                            models.add(model)
                
                return sorted(list(models)), None
            except Exception as e:
                return [], f"Erreur lors de la récupération des modèles AI Horde : {str(e)}"
        config, url, headers = self.API_CONFIG[provider], "", {"Content-Type": "application/json"}
        try:
            if provider in ["Mistral", "OpenAI"]:
                url = f"{config['base_url']}{config['models_endpoint']}"
                headers["Authorization"] = f"Bearer {api_key}"
                response = await asyncio.to_thread(requests.get, url, headers=headers, timeout=10)
                response.raise_for_status()
                models_data = response.json().get('data', [])
                
                # Pour OpenAI, filtrer seulement les modèles de chat/completion
                if provider == "OpenAI":
                    chat_models = []
                    for m in models_data:
                        model_id = m['id']
                        # Inclure seulement les modèles de chat/completion (exclure embeddings, whisper, tts, dall-e)
                        if (any(prefix in model_id.lower() for prefix in ['gpt-', 'davinci', 'curie', 'babbage', 'ada', 'o1-']) and 
                            not any(exclude in model_id.lower() for exclude in ['embedding', 'whisper', 'tts', 'dall-e'])):
                            chat_models.append(model_id)
                    result = sorted(chat_models)
                    return result, None
                else:
                    # Pour Mistral et autres, prendre tous les modèles
                    return sorted([m['id'] for m in models_data]), None
            elif provider == "Google":
                url = f"{config['base_url']}{config['models_endpoint']}?key={api_key}"
                response = await asyncio.to_thread(requests.get, url, headers=headers, timeout=10)
                response.raise_for_status()
                return sorted([m['name'].replace("models/", "") for m in response.json().get('models', []) if 'generateContent' in m.get('supportedGenerationMethods', [])]), None
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401: return [], "Clé API invalide ou non autorisée."
            return [], f"Erreur HTTP: {e.response.status_code} {e.response.reason}"
        except Exception as e:
            # Éviter toute fuite de clé API dans les erreurs (ex: URL avec ?key=...)
            return [], f"Une erreur est survenue: {_redact_error(str(e))}"
        return [], "Une erreur inattendue est survenue."
    async def call_chat_api(self, messages: List[Dict], max_tokens: int, context_length: int, temperature: float, is_json: bool = True) -> tuple[Optional[str], Optional[str]]:
        if not self.is_available: return None, "Le gestionnaire API n'est pas configuré."
        if not self.model: return None, "Aucun nom de modèle n'a été défini."
        headers, payload, url, response = {"Content-Type": "application/json"}, {}, "", None
        # Combiner TOUS les messages system en un seul bloc
        # CRITIQUE pour Anthropic: l'API n'accepte qu'un seul champ 'system'
        system_parts = []
        history_messages = []
        for msg in messages:
            if msg.get('role') == 'system':
                system_parts.append(msg.get('content', ''))
            else:
                history_messages.append(msg)
        system_prompt = '\n\n'.join(system_parts) if system_parts else ""
        if system_parts:
            print(f"[API-SYSTEM] {len(system_parts)} messages system combinés en 1 ({len(system_prompt)} chars)")
        try:
            config = self.API_CONFIG.get(self.provider)
            if not config: return None, f"Le fournisseur '{self.provider}' n'est pas supporté."
            if self.provider in ["OpenAI", "Mistral", "GROK", "OpenRouter"]:
                url = f"{config['base_url']}{config['chat_endpoint']}"
                headers["Authorization"] = f"Bearer {self.api_key}"
                if self.provider == "OpenRouter":
                    headers["HTTP-Referer"] = "https://github.com/ogma-ia/ogma"
                    headers["X-Title"] = "OGMA AI Assistant"
                
                # Formatage spécifique pour OpenAI/Mistral
                final_api_messages = []
                if system_prompt: 
                    final_api_messages.append({"role": "system", "content": system_prompt})
                
                # Traitement des messages avec support multimodal pour OpenAI
                for msg in history_messages:
                    processed_msg = {"role": msg.get('role'), "content": msg.get('content')}
                    
                    # Si le contenu est une liste (multimodal), le garder tel quel pour OpenAI
                    if isinstance(msg.get('content'), list):
                        openai_content = []
                        for part in msg.get('content'):
                            if part.get('type') == 'text':
                                openai_content.append({"type": "text", "text": part.get('text', '')})
                            elif part.get('type') == 'image_url':
                                # Format correct pour OpenAI
                                openai_content.append({
                                    "type": "image_url",
                                    "image_url": {"url": part.get('image_url', {}).get('url', '')}
                                })
                        processed_msg["content"] = openai_content
                    
                    final_api_messages.append(processed_msg)
                
                # Gestion max_tokens = -1 pour maximum automatique selon le provider - STABILITÉ
                final_max_tokens = max_tokens if max_tokens != -1 else (4096 if self.provider in ["OpenAI", "Anthropic", "GROK", "OpenRouter"] else 2048)  # RÉDUIT pour stabilité

                # OpenAI: GPT-5 et o1/o3 utilisent max_completion_tokens et ne supportent pas temperature
                if self.provider == "OpenAI":
                    is_reasoning_model = any(x in self.model.lower() for x in ["gpt-5", "o1", "o3", "o4"])
                    payload = {"model": self.model, "messages": final_api_messages}
                    # GPT-5 et o1/o3/o4 ne supportent pas temperature (uniquement défaut=1)
                    if not is_reasoning_model:
                        payload["temperature"] = temperature
                    # GPT-5 et o1/o3/o4 nécessitent max_completion_tokens
                    # IMPORTANT: les reasoning models consomment des tokens internes (thinking)
                    # → forcer un minimum de 8000 pour éviter les réponses vides
                    if is_reasoning_model:
                        reasoning_tokens = max(final_max_tokens, 8000)
                        payload["max_completion_tokens"] = reasoning_tokens
                        if reasoning_tokens != final_max_tokens:
                            print(f"[OPENAI-REASONING] max_completion_tokens élevé à {reasoning_tokens} (was {final_max_tokens})")
                        # Contrôle thinking pour modèles OpenAI reasoning
                        if self.openrouter_thinking:
                            print(f"[OPENAI] Mode thinking ACTIVÉ pour: {self.model}")
                        else:
                            # o1 (o1-mini, o1-preview) ne supporte PAS reasoning_effort="none"
                            # → utiliser "low" pour o1, "none" pour o3/o4/gpt-5
                            _is_o1 = 'o1' in self.model.lower() and 'o1' not in ['o10']  # eviter faux positifs
                            _effort = "low" if _is_o1 else "none"
                            payload["reasoning_effort"] = _effort
                            print(f"[OPENAI] Thinking réduit (reasoning_effort={_effort}) pour: {self.model}")
                    else:
                        payload["max_tokens"] = final_max_tokens
                    if is_json:
                        payload["response_format"] = {"type": "json_object"}
                elif self.provider == "GROK":
                    # GROK utilise max_tokens (compatible OpenAI legacy)
                    payload = {"model": self.model, "messages": final_api_messages, "max_tokens": final_max_tokens, "temperature": temperature}
                    if is_json:
                        payload["response_format"] = {"type": "json_object"}
                elif self.provider == "OpenRouter":
                    # OpenRouter: compatible OpenAI
                    payload = {"model": self.model, "messages": final_api_messages, "max_tokens": final_max_tokens, "temperature": temperature}
                    if is_json:
                        payload["response_format"] = {"type": "json_object"}
                    # Gère le thinking selon le paramètre utilisateur
                    _or_thinking_models = ["qwen3", "deepseek-r1", "/o1", "/o3", "claude-3-7", "gemini-2.5", "gemini-2.0-flash-thinking", "gemini-3"]
                    # Modèles où le reasoning est OBLIGATOIRE (ne pas envoyer effort=none)
                    _or_mandatory_reasoning = ["gemini-2.5", "gemini-2.0-flash-thinking", "deepseek-r1", "gemini-3.1"]
                    _is_thinking_model = any(x in self.model.lower() for x in _or_thinking_models)
                    _is_mandatory = any(x in self.model.lower() for x in _or_mandatory_reasoning)
                    if _is_thinking_model:
                        if self.openrouter_thinking:
                            # CRITIQUE: les tokens thinking comptent dans max_tokens
                            # → augmenter pour éviter troncature de la réponse
                            _or_thinking_budget = max(final_max_tokens * 3, 16000)
                            payload["max_tokens"] = _or_thinking_budget
                            if _or_thinking_budget != final_max_tokens:
                                print(f"[OPENROUTER] max_tokens élevé à {_or_thinking_budget} (was {final_max_tokens}) pour thinking")
                            print(f"[OPENROUTER] Mode thinking ACTIVÉ pour: {self.model}")
                        elif _is_mandatory:
                            # Reasoning obligatoire: ne PAS envoyer effort=none (erreur 400)
                            # BOOST max_tokens car thinking interne consomme le budget
                            _or_mandatory_budget = max(final_max_tokens * 8, 4096)
                            payload["max_tokens"] = _or_mandatory_budget
                            if _or_mandatory_budget != final_max_tokens:
                                print(f"[OPENROUTER] max_tokens booste: {final_max_tokens} -> {_or_mandatory_budget} (thinking obligatoire)")
                            print(f"[OPENROUTER] Thinking obligatoire pour {self.model} - reasoning interne maintenu (UI masquée)")
                        else:
                            payload["reasoning"] = {"effort": "none"}
                            print(f"[OPENROUTER] Thinking désactivé pour: {self.model}")
                elif self.provider == "Mistral":
                    # Mistral: magistral models pensent toujours, budget tokens si thinking activé
                    _is_magistral = 'magistral' in self.model.lower()
                    _mistral_max = final_max_tokens
                    if _is_magistral and self.openrouter_thinking:
                        _mistral_max = max(final_max_tokens * 3, 16000)
                        if _mistral_max != final_max_tokens:
                            print(f"[MISTRAL] max_tokens élevé à {_mistral_max} (was {final_max_tokens}) pour thinking magistral")
                    payload = {"model": self.model, "messages": final_api_messages, "max_tokens": _mistral_max, "temperature": temperature}
                
                # S'assurer que le prompt système mentionne JSON si nécessaire
                if is_json and self.provider == "OpenAI" and system_prompt and "JSON" not in system_prompt.upper():
                    for msg in final_api_messages:
                        if msg["role"] == "system":
                            msg["content"] += " Répondez uniquement au format JSON valide."
                            break
            elif self.provider == "Anthropic":
                url = f"{config['base_url']}{config['chat_endpoint']}"
                headers.update({
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",  # Version API Anthropic compatible
                    "content-type": "application/json"
                })
                processed_messages = []

                # Pour Anthropic, le message système ne va PAS dans le tableau messages
                # Il sera ajouté comme paramètre 'system' dans le payload

                # Traiter les autres messages
                for msg in history_messages:
                    role = msg.get('role')
                    if role == 'assistant': role = 'assistant'
                    elif role == 'user': role = 'user'
                    else: continue  # Ignorer les autres rôles

                    content = msg.get('content')
                    if isinstance(content, list):
                        # Traitement des messages multimodaux
                        message_content = []
                        for part in content:
                            if part.get('type') == 'text':
                                message_content.append({"type": "text", "text": part.get('text', '')})
                            elif part.get('type') == 'image_url':
                                url_data = part.get('image_url', {}).get('url', '')
                                if 'base64,' in url_data:
                                    try:
                                        media_type = url_data.split(';')[0].split(':')[1]
                                        data = url_data.split(',')[1]
                                        message_content.append({
                                            "type": "image",
                                            "source": {
                                                "type": "base64",
                                                "media_type": media_type,
                                                "data": data
                                            }
                                        })
                                    except (IndexError, ValueError):
                                        print("[WARN] Format d'image invalide ignoré")
                        processed_messages.append({"role": role, "content": message_content})
                    else:
                        # Message texte simple
                        processed_messages.append({"role": role, "content": content})

                # Gestion max_tokens = -1 pour maximum automatique (STABILITÉ - était 8192)
                final_max_tokens = max_tokens if max_tokens != -1 else 4096

                payload = {
                    "model": self.model,
                    "messages": processed_messages,
                    "max_tokens": final_max_tokens,
                    "temperature": temperature
                }
                
                # Ajouter le message système comme paramètre racine pour Anthropic
                if system_prompt:
                    payload["system"] = system_prompt
                
                # Contrôle extended thinking pour modèles Anthropic (Claude 3.5+)
                _anthropic_thinking_models = ['claude-3-5', 'claude-3.5', 'claude-3-7', 'claude-3.7', 'claude-4']
                _is_anthropic_thinker = any(x in self.model.lower() for x in _anthropic_thinking_models)
                if _is_anthropic_thinker:
                    if self.openrouter_thinking:
                        # Anthropic extended thinking: opt-in avec budget
                        thinking_budget = max(final_max_tokens * 2, 10000)
                        payload["thinking"] = {"type": "enabled", "budget_tokens": thinking_budget}
                        # Extended thinking nécessite un max_tokens plus grand
                        payload["max_tokens"] = max(final_max_tokens, thinking_budget + 4096)
                        # CRITIQUE: Anthropic REQUIERT temperature=1 avec extended thinking
                        payload["temperature"] = 1
                        print(f"[ANTHROPIC] Extended thinking ACTIVÉ (budget={thinking_budget}, temp forcée=1) pour: {self.model}")
                    else:
                        print(f"[ANTHROPIC] Extended thinking désactivé pour: {self.model}")
            elif self.provider == "AIHorde":
                url = f"{config['base_url']}{config['chat_endpoint']}"
                
                # Gestion max_tokens = -1 pour maximum automatique
                final_max_tokens = max_tokens if max_tokens != -1 else 2048
                
                full_prompt = ""
                if system_prompt:
                    full_prompt += f"System: {system_prompt}\n\n"
                for msg in history_messages:
                    role = "Assistant" if msg.get('role') == 'assistant' else "Human"
                    content = msg.get('content')
                    if isinstance(content, list):
                        text_parts = [part.get('text', '') for part in content if part.get('type') == 'text']
                        content = ' '.join(text_parts)
                    full_prompt += f"{role}: {content}\n"
                full_prompt += "Assistant:"

                payload = {
                    "prompt": full_prompt,
                    "params": {
                        "max_new_tokens": final_max_tokens,
                        "temperature": temperature,
                        "top_p": 0.9,
                        "repetition_penalty": 1.2
                    },
                    "trusted_workers": False,
                    "slow_workers": True,
                    "worker_blacklist": False,
                    "models": [self.model]
                }
                headers.update({
                    "apikey": self.api_key,
                    "Client-Agent": "OGMA:2.0:kidshadow79"
                })

            elif self.provider == "Google":
                url = f"{config['base_url']}/models/{self.model}:generateContent?key={self.api_key}"
                processed_messages = []
                
                # Gestion max_tokens = -1 pour maximum automatique
                final_max_tokens = max_tokens if max_tokens != -1 else 8192
                
                for msg in history_messages:
                    role = 'model' if msg.get('role') == 'assistant' else 'user'
                    content = msg.get('content')
                    parts = []
                    
                    if isinstance(content, list):
                        for part in content:
                            if part.get('type') == 'text': 
                                parts.append({'text': part.get('text', '')})
                            elif part.get('type') == 'image_url':
                                url_data = part.get('image_url', {}).get('url', '')
                                if 'base64,' in url_data:
                                    try:
                                        mime_type = url_data.split(';')[0].split(':')[1]
                                        data = url_data.split(',')[1]
                                        # Format correct pour Google API
                                        parts.append({'inlineData': {'mimeType': mime_type, 'data': data}})
                                    except (IndexError, ValueError):
                                        print(f"[WARN] Format d'image base64 invalide pour Google API")
                    elif isinstance(content, str): 
                        parts.append({'text': content})
                    
                    processed_messages.append({'role': role, 'parts': parts})
                
                payload = {
                    "contents": processed_messages, 
                    "generationConfig": {
                        "maxOutputTokens": final_max_tokens, 
                        "temperature": temperature
                    },
                    # Désactiver tous les filtres de sécurité Google pour éviter la troncature
                    # des réponses contenant du contenu sensible (img2img, descriptions, etc.)
                    "safetySettings": [
                        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_CIVIC_INTEGRITY", "threshold": "BLOCK_NONE"},
                    ]
                }
                if system_prompt: 
                    payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}
                
                # Contrôle thinking pour modèles Gemini
                # Catégorie 1: thinkingBudget=0 accepté (on/off complet)
                _google_toggleable = ['gemini-3-pro', 'gemini-3.0']
                # Catégorie 2: thinkingBudget=0 REFUSÉ mais thinkingBudget>0 OK (expose le thinking)
                _google_always_but_exposable = ['gemini-2.5']
                # Catégorie 3: thinkingConfig NON SUPPORTÉ du tout (pense toujours, jamais exposé)
                _google_no_config = ['gemini-2.0-flash-thinking', 'gemini-3.1']
                
                _is_toggleable = any(x in self.model.lower() for x in _google_toggleable)
                _is_exposable = any(x in self.model.lower() for x in _google_always_but_exposable)
                _is_no_config = any(x in self.model.lower() for x in _google_no_config)
                
                if _is_toggleable:
                    # On peut activer/désactiver le thinking complètement
                    if self.openrouter_thinking:
                        _thinking_budget = min(max(final_max_tokens, 8192), 32768)
                        payload["generationConfig"]["thinkingConfig"] = {"thinkingBudget": _thinking_budget, "includeThoughts": True}
                        print(f"[GOOGLE] Thinking ON (thinkingBudget={_thinking_budget}) pour: {self.model}")
                    else:
                        payload["generationConfig"]["thinkingConfig"] = {"thinkingBudget": 0}
                        print(f"[GOOGLE] Thinking OFF (thinkingBudget=0) pour: {self.model}")
                elif _is_exposable:
                    # Pense toujours, mais on peut EXPOSER le thinking via thinkingBudget>0
                    _original_max = payload["generationConfig"]["maxOutputTokens"]
                    _boosted_max = max(_original_max * 8, 4096)
                    payload["generationConfig"]["maxOutputTokens"] = _boosted_max
                    if self.openrouter_thinking:
                        _thinking_budget = min(max(final_max_tokens, 8192), 32768)
                        payload["generationConfig"]["thinkingConfig"] = {"thinkingBudget": _thinking_budget, "includeThoughts": True}
                        print(f"[GOOGLE] Thinking EXPOSÉ (thinkingBudget={_thinking_budget}) pour: {self.model} - maxOutputTokens: {_original_max} -> {_boosted_max}")
                    else:
                        # Pas de thinkingConfig = pense en interne sans exposer
                        print(f"[GOOGLE] Thinking interne (non exposé) pour: {self.model} - maxOutputTokens: {_original_max} -> {_boosted_max}")
                elif _is_no_config:
                    # Aucun contrôle possible - boost maxOutputTokens uniquement
                    _original_max = payload["generationConfig"]["maxOutputTokens"]
                    _boosted_max = max(_original_max * 8, 4096)
                    payload["generationConfig"]["maxOutputTokens"] = _boosted_max
                    print(f"[GOOGLE] Thinking FORCÉ (pas de config possible) pour: {self.model} - maxOutputTokens: {_original_max} -> {_boosted_max}")
            print(f"[CONNECT] Appel de l'API externe '{self.provider}' avec le modèle '{self.model}'...")
            response = await asyncio.to_thread(requests.post, url, headers=headers, json=payload, timeout=180)  # Augmenté à 180s pour requêtes lourdes (biographie, etc.)
            response.raise_for_status()
            
            response_data = response.json()
            response_text = ""
            
            if self.provider == "AIHorde":
                # Pour AI Horde, il faut d'abord attendre que la génération soit terminée
                try:
                    generation_id = response_data.get("id")
                    if not generation_id:
                        error_msg = response_data.get("message", "Erreur : Pas d'ID de génération dans la réponse")
                        return None, f"Erreur AI Horde : {error_msg}"
                    
                    # Attendre et vérifier le statut de la génération
                    check_url = f"{config['base_url']}/generate/text/status/{generation_id}"
                    max_retries = 30  # Nombre maximal de tentatives
                    retry_delay = 2  # Délai entre les tentatives en secondes
                    
                    for _ in range(max_retries):
                        await asyncio.sleep(retry_delay)
                        status_response = await asyncio.to_thread(requests.get, check_url, headers=headers)
                        status_response.raise_for_status()
                        status_data = status_response.json()
                        
                        if "done" not in status_data:
                            print(f"[DEBUG] Réponse de statut inattendue : {status_data}")
                        
                        if status_data.get("done", False):
                            if "generations" in status_data and len(status_data["generations"]) > 0:
                                response_text = status_data["generations"][0].get("text", "")
                                if not response_text:
                                    return None, "La génération n'a pas produit de texte"
                                break
                        elif status_data.get("faulted", False):
                            return None, f"La génération a échoué sur AI Horde : {status_data.get('message', 'Raison inconnue')}"
                        
                        if "wait_time" in status_data:
                            print(f"[INFO] Temps d'attente estimé : {status_data['wait_time']} secondes")
                    else:
                        return None, "Délai d'attente dépassé pour la génération AI Horde"
                except Exception as e:
                    print(f"[ERROR] Exception lors de la génération AI Horde : {str(e)}")
                    return None, f"Erreur inattendue AI Horde : {str(e)}"
                
            elif self.provider in ["OpenAI", "Mistral", "GROK", "OpenRouter"]:
                choice = response_data['choices'][0]
                # Log finish_reason pour diagnostic (content_filter, length, stop...)
                finish_reason = choice.get('finish_reason', '')
                if finish_reason and finish_reason not in ('stop', 'end_turn', 'eos'):
                    print(f"[RESPONSE-FINISH] ⚠️ finish_reason={finish_reason!r} ({self.provider}/{self.model})")
                raw_content = choice['message']['content']
                # Certains reasoning models (GPT-5, o-series) renvoient content=None + usage.completion_tokens=0
                if raw_content is None:
                    usage = response_data.get('usage', {})
                    print(f"[RESPONSE-DEBUG] content=None, finish_reason={finish_reason!r}, usage={usage}")
                    raw_content = ""
                # Modeles reasoning Mistral (magistral-*): content peut etre une liste IMBRIQUÉE
                # Format: [{"type": "thinking", "thinking": [{"type": "text", "text": "..."}]},
                #          {"type": "text", "text": [{"type": "text", "text": "..."}]}]
                if isinstance(raw_content, list):
                    text_parts = []
                    thinking_parts = []
                    for part in raw_content:
                        if not isinstance(part, dict):
                            continue
                        part_type = part.get('type', '')
                        if part_type == 'text':
                            text_val = part.get('text', '')
                            if isinstance(text_val, list):
                                for sub in text_val:
                                    if isinstance(sub, dict) and sub.get('type') == 'text':
                                        text_parts.append(sub.get('text', ''))
                            elif isinstance(text_val, str):
                                text_parts.append(text_val)
                        elif part_type == 'thinking':
                            think_val = part.get('thinking', '')
                            if isinstance(think_val, list):
                                for sub in think_val:
                                    if isinstance(sub, dict) and sub.get('type') == 'text':
                                        thinking_parts.append(sub.get('text', ''))
                            elif isinstance(think_val, str):
                                thinking_parts.append(think_val)
                    response_text = ''.join(text_parts)
                    if thinking_parts:
                        self._last_thinking_content = ''.join(thinking_parts)
                else:
                    response_text = raw_content
            elif self.provider == "Anthropic":
                if 'content' in response_data:
                    try:
                        # Extended thinking: content peut contenir des blocs thinking + text
                        # Format: [{"type":"thinking","thinking":"..."}, {"type":"text","text":"..."}]
                        text_parts = []
                        thinking_parts = []
                        for block in response_data['content']:
                            if isinstance(block, dict):
                                block_type = block.get('type', '')
                                if block_type == 'thinking':
                                    thinking_text = block.get('thinking', '')
                                    if thinking_text:
                                        thinking_parts.append(thinking_text)
                                elif block_type == 'text':
                                    text_parts.append(block.get('text', ''))
                                else:
                                    # Fallback: tenter text directement
                                    if 'text' in block:
                                        text_parts.append(block['text'])
                            elif isinstance(block, str):
                                text_parts.append(block)
                        if thinking_parts:
                            self._last_thinking_content = ''.join(thinking_parts)
                            print(f"[ANTHROPIC] Thinking non-streaming capturé ({len(self._last_thinking_content)} chars)")
                        response_text = ''.join(text_parts) if text_parts else ''
                        if not response_text and not thinking_parts:
                            # Format legacy simple (ancien Anthropic sans thinking)
                            response_text = response_data['content'][0].get('text', '')
                    except (KeyError, IndexError) as e:
                        print(f"[DEBUG] Structure de réponse Anthropic inattendue : {e} - {str(response_data)[:500]}")
                        return None, "Format de réponse Anthropic invalide"
                else:
                    print(f"[DEBUG] Réponse Anthropic complète : {response_data}")
                    error_message = response_data.get('error', {}).get('message', 'Erreur inconnue')
                    return None, f"Erreur Anthropic : {error_message}"
            elif self.provider == "Google": 
                if 'candidates' in response_data and response_data['candidates']:
                    candidate = response_data['candidates'][0]
                    # Log finishReason pour diagnostic (STOP, MAX_TOKENS, SAFETY, RECITATION...)
                    _g_finish = candidate.get('finishReason', '')
                    if _g_finish and _g_finish not in ('STOP', 'END_TURN'):
                        print(f"[RESPONSE-FINISH] ⚠️ finishReason={_g_finish!r} (Google/{self.model})")
                        # SAFETY = filtre sécurité a tronqué la réponse
                        if _g_finish == 'SAFETY':
                            _safety_ratings = candidate.get('safetyRatings', [])
                            print(f"[RESPONSE-FINISH] 🛡️ Safety ratings: {_safety_ratings}")
                    if 'content' in candidate and 'parts' in candidate['content']:
                        # Thinking models: séparer parts thinking (thought=true) des parts texte
                        _g_text_parts = []
                        _g_thinking_parts = []
                        for part in candidate['content']['parts']:
                            if part.get('thought', False):
                                _g_thinking_parts.append(part.get('text', ''))
                            else:
                                _g_text_parts.append(part.get('text', ''))
                        response_text = ''.join(_g_text_parts)
                        if _g_thinking_parts:
                            self._last_thinking_content = ''.join(_g_thinking_parts)
                            print(f"[GOOGLE] Thinking non-streaming capturé ({len(self._last_thinking_content)} chars)")
                    else:
                        return None, f"Erreur Google API : Structure de réponse inattendue dans le candidat."
                elif 'error' in response_data:
                    return None, f"Erreur Google API : {response_data['error'].get('message', 'Erreur inconnue')}"
                else:
                    # Essayer de récupérer plus d'informations sur l'erreur
                    if 'promptFeedback' in response_data:
                        feedback = response_data['promptFeedback']
                        if feedback.get('blockReason'):
                            return None, f"Erreur Google API : Contenu bloqué - {feedback.get('blockReason')}"
                    return None, f"Erreur Google API : Aucun candidat de réponse. Réponse complète: {response_data}"
            
            print(f"[OK] Réponse reçue de {self.provider} ({len(response_text)} caractères)")
            return response_text, None
        except requests.exceptions.HTTPError as e:
            # Récupération détaillée des informations d'erreur
            status_code = getattr(e.response, 'status_code', 'Inconnu')
            error_text = ""
            
            if e.response is not None:
                try:
                    error_text = e.response.text
                    # Tenter de parser le JSON d'erreur pour plus de détails
                    if e.response.headers.get('content-type', '').startswith('application/json'):
                        error_data = e.response.json()
                        if self.provider == "Anthropic" and 'error' in error_data:
                            error_text = f"{error_data['error'].get('type', 'Erreur')}: {error_data['error'].get('message', error_text)}"
                except:
                    error_text = f"Réponse non-textuelle (status: {status_code})"
            else:
                error_text = f"Aucune réponse reçue - problème de connexion réseau"
            
            if status_code == 401:
                error_message = f"Erreur d'authentification {self.provider} : Clé API invalide ou expirée"
            elif status_code == 400:
                # Détecter spécifiquement les erreurs de contexte/tokens
                error_lower = error_text.lower()
                if any(kw in error_lower for kw in ['context_length', 'context length', 'maximum context', 'token limit', 'too many tokens', 'max_tokens', 'exceeds the model']):
                    error_message = (
                        f"Erreur {self.provider} : le contexte depasse la limite du modele '{self.model}'. "
                        f"Renseignez-vous sur la context window de votre modele et entrez la valeur manuellement "
                        f"dans les parametres d'Ogma (context_length). Detail : {error_text}"
                    )
                else:
                    error_message = f"Erreur de requête {self.provider} : {error_text}"
            elif status_code == 404:
                error_message = f"Erreur {self.provider} : Modèle '{self.model}' introuvable ou indisponible"
            elif status_code == 429:
                error_message = f"Erreur {self.provider} : Limite de débit dépassée, réessayez dans quelques secondes"
            elif status_code == 500:
                error_message = f"Erreur serveur {self.provider} : Problème côté fournisseur"
            else:
                error_message = f"Erreur HTTP {self.provider} ({status_code}) : {error_text}"
            
            print(f"[ERREUR] {error_message}")
            return None, error_message
        except requests.exceptions.ConnectionError as e:
            error_message = f"Erreur de connexion {self.provider} : Impossible de joindre le serveur ({str(e)})"
            print(f"[ERREUR] {error_message}")
            return None, error_message
        except requests.exceptions.Timeout as e:
            error_message = f"Timeout {self.provider} : La requête a dépassé le délai d'attente"
            print(f"[ERREUR] {error_message}")
            return None, error_message
        except json.JSONDecodeError as e:
            error_message = f"Erreur de décodage JSON {self.provider} : Réponse invalide"
            print(f"[ERREUR] {error_message}")
            if response:
                print(f"Réponse brute reçue: {response.text[:500]}...")  # Premier 500 chars
            return None, error_message
        except Exception as e:
            error_message = f"Erreur inattendue {self.provider} : {type(e).__name__} - {str(e)}"
            print(f"[ERREUR] {error_message}")
            return None, error_message

    async def call_chat_api_streaming(self, messages: List[Dict], max_tokens: int, context_length: int, 
                                       temperature: float, callback=None) -> tuple[Optional[str], Optional[str]]:
        """
        Appel API avec streaming - affiche les tokens au fur et à mesure.
        
        Args:
            messages: Liste des messages
            max_tokens: Nombre max de tokens
            context_length: Taille contexte
            temperature: Température
            callback: Fonction async(chunk: str) appelée pour chaque chunk reçu
            
        Returns:
            tuple: (réponse_complète, erreur)
        """
        if not self.is_available: 
            return None, "Le gestionnaire API n'est pas configuré."
        if not self.model: 
            return None, "Aucun nom de modèle n'a été défini."
        
        # Providers supportant le streaming
        if self.provider not in ["OpenAI", "Mistral", "GROK", "OpenRouter", "Anthropic", "Google"]:
            print(f"[STREAM] ⚠️ Provider {self.provider} ne supporte pas le streaming, fallback classique")
            return await self.call_chat_api(messages, max_tokens, context_length, temperature, is_json=False)
        
        import httpx
        
        headers = {"Content-Type": "application/json"}
        total_images_sent = 0  # Compteur d'images (pour diagnostic rate limit)
        
        # Combiner TOUS les messages system en un seul bloc
        # CRITIQUE pour Anthropic: l'API n'accepte qu'un seul champ 'system'
        system_parts = []
        history_messages = []
        for msg in messages:
            if msg.get('role') == 'system':
                system_parts.append(msg.get('content', ''))
            else:
                history_messages.append(msg)
        system_prompt = '\n\n'.join(system_parts) if system_parts else ""
        if system_parts:
            print(f"[STREAM-SYSTEM] {len(system_parts)} messages system combinés en 1 ({len(system_prompt)} chars)")
        
        try:
            config = self.API_CONFIG.get(self.provider)
            if not config: 
                return None, f"Le fournisseur '{self.provider}' n'est pas supporté."
            
            # Construire le payload selon le provider
            if self.provider in ["OpenAI", "Mistral", "GROK", "OpenRouter"]:
                url = f"{config['base_url']}{config['chat_endpoint']}"
                headers["Authorization"] = f"Bearer {self.api_key}"
                if self.provider == "OpenRouter":
                    headers["HTTP-Referer"] = "https://github.com/ogma-ia/ogma"
                    headers["X-Title"] = "OGMA AI Assistant"
                
                final_api_messages = []
                if system_prompt:
                    final_api_messages.append({"role": "system", "content": system_prompt})
                
                # Détecter si des images sont présentes dans les messages
                has_images = False
                for msg in history_messages:
                    content = msg.get('content')
                    if isinstance(content, list):
                        for part in content:
                            if part.get('type') == 'image_url':
                                has_images = True
                                break
                    if has_images:
                        break
                
                for msg in history_messages:
                    content = msg.get('content')
                    # Conserver le contenu multimodal pour OpenAI, GROK, Mistral et OpenRouter (vision)
                    if isinstance(content, list):
                        if self.provider in ["OpenAI", "GROK", "Mistral", "OpenRouter"]:
                            # Format multimodal compatible OpenAI/GROK/Mistral
                            multimodal_content = []
                            for part in content:
                                if part.get('type') == 'text':
                                    multimodal_content.append({"type": "text", "text": part.get('text', '')})
                                elif part.get('type') == 'image_url':
                                    image_url = part.get('image_url', {}).get('url', '')
                                    
                                    # 🖼️ COMPRESSION IMAGE VISION avant envoi API
                                    if 'base64,' in image_url:
                                        # Extraire et compresser les données base64
                                        compressed_b64 = _compress_vision_image(image_url)
                                        image_url = f"data:image/jpeg;base64,{compressed_b64}"
                                    
                                    # Validation taille image pour GROK (limite ~20MB base64)
                                    if self.provider == "GROK" and 'base64,' in image_url:
                                        base64_size = len(image_url)
                                        if base64_size > 20_000_000:  # 20MB
                                            print(f"[STREAM-VISION] ⚠️ Image trop grande pour GROK ({base64_size/1_000_000:.1f}MB), ignorée")
                                            multimodal_content.append({"type": "text", "text": "[Image trop volumineuse pour être analysée]"})
                                            continue
                                    # Mistral utilise le même format que OpenAI pour les images
                                    multimodal_content.append({
                                        "type": "image_url",
                                        "image_url": {"url": image_url}
                                    })
                                    total_images_sent += 1  # Incrémenter compteur
                            final_api_messages.append({"role": msg.get('role'), "content": multimodal_content})
                        else:
                            # Autres providers: simplifier en texte
                            text_parts = [p.get('text', '') for p in content if p.get('type') == 'text']
                            final_api_messages.append({"role": msg.get('role'), "content": ' '.join(text_parts)})
                    else:
                        # 🧠 THINKING: Reconstruire le format structuré pour Mistral multi-turn
                        thinking_content = msg.get('thinking', '')
                        if thinking_content and self.provider == "Mistral" and msg.get('role') == 'assistant':
                            structured_content = [
                                {"type": "thinking", "thinking": [{"type": "text", "text": thinking_content}]},
                                {"type": "text", "text": content}
                            ]
                            final_api_messages.append({"role": "assistant", "content": structured_content})
                            print(f"[THINKING-REBUILD] Format structure reconstruit pour assistant ({len(thinking_content)} chars thinking)")
                        else:
                            final_api_messages.append({"role": msg.get('role'), "content": content})
                
                final_max_tokens = max_tokens if max_tokens != -1 else 4096
                
                # Détecter si c'est un modèle de raisonnement (GPT-5, o1, o3, o4)
                is_reasoning_model = self.provider == "OpenAI" and any(x in self.model.lower() for x in ["gpt-5", "o1", "o3", "o4"])
                
                payload = {
                    "model": self.model,
                    "messages": final_api_messages,
                    "stream": True  # STREAMING ACTIVÉ
                }
                
                # GPT-5 et o1/o3/o4 ne supportent pas temperature (uniquement défaut=1)
                if not is_reasoning_model:
                    payload["temperature"] = temperature
                
                # GPT-5 et o1/o3/o4 utilisent max_completion_tokens, les autres max_tokens
                # IMPORTANT: reasoning models consomment des tokens internes → minimum 8000
                if is_reasoning_model:
                    reasoning_tokens = max(final_max_tokens, 8000)
                    payload["max_completion_tokens"] = reasoning_tokens
                    if reasoning_tokens != final_max_tokens:
                        print(f"[OPENAI-REASONING] max_completion_tokens élevé à {reasoning_tokens} (was {final_max_tokens})")
                    # Contrôle thinking pour modèles OpenAI reasoning (streaming)
                    if self.openrouter_thinking:
                        print(f"[OPENAI] Mode thinking ACTIVÉ (streaming) pour: {self.model}")
                    else:
                        # o1 ne supporte pas reasoning_effort="none" → utiliser "low"
                        _is_o1 = 'o1' in self.model.lower()
                        _effort = "low" if _is_o1 else "none"
                        payload["reasoning_effort"] = _effort
                        print(f"[OPENAI] Thinking réduit (streaming, reasoning_effort={_effort}) pour: {self.model}")
                else:
                    payload["max_tokens"] = final_max_tokens
                
                # Gère le thinking selon le paramètre utilisateur pour OpenRouter
                if self.provider == "OpenRouter":
                    _or_thinking_models = ["qwen3", "deepseek-r1", "/o1", "/o3", "claude-3-7", "gemini-2.5", "gemini-2.0-flash-thinking", "gemini-3"]
                    # Modèles où le reasoning est OBLIGATOIRE (ne pas envoyer effort=none)
                    _or_mandatory_reasoning = ["gemini-2.5", "gemini-2.0-flash-thinking", "deepseek-r1", "gemini-3.1"]
                    _is_thinking_model = any(x in self.model.lower() for x in _or_thinking_models)
                    _is_mandatory = any(x in self.model.lower() for x in _or_mandatory_reasoning)
                    if _is_thinking_model:
                        if self.openrouter_thinking:
                            # CRITIQUE: les tokens thinking comptent dans max_tokens
                            # → augmenter pour éviter troncature de la réponse
                            _or_thinking_budget = max(final_max_tokens * 3, 16000)
                            payload["max_tokens"] = _or_thinking_budget
                            if _or_thinking_budget != final_max_tokens:
                                print(f"[OPENROUTER] max_tokens élevé à {_or_thinking_budget} (was {final_max_tokens}) pour thinking")
                            print(f"[OPENROUTER] Mode thinking ACTIVÉ (streaming) pour: {self.model}")
                        elif _is_mandatory:
                            # Reasoning obligatoire: ne PAS envoyer effort=none (erreur 400)
                            # BOOST max_tokens car thinking interne consomme le budget
                            _or_mandatory_budget = max(final_max_tokens * 8, 4096)
                            payload["max_tokens"] = _or_mandatory_budget
                            if _or_mandatory_budget != final_max_tokens:
                                print(f"[OPENROUTER] max_tokens booste: {final_max_tokens} -> {_or_mandatory_budget} (thinking obligatoire streaming)")
                            print(f"[OPENROUTER] Thinking obligatoire pour {self.model} - reasoning interne maintenu (UI masquée)")
                        else:
                            payload["reasoning"] = {"effort": "none"}
                            print(f"[OPENROUTER] Thinking désactivé (streaming) pour: {self.model}")
                
                # Gère le thinking pour Mistral magistral (streaming)
                if self.provider == "Mistral" and 'magistral' in self.model.lower() and self.openrouter_thinking:
                    _mistral_budget = max(final_max_tokens * 3, 16000)
                    payload["max_tokens"] = _mistral_budget
                    if _mistral_budget != final_max_tokens:
                        print(f"[MISTRAL] max_tokens élevé à {_mistral_budget} (was {final_max_tokens}) pour thinking streaming")
                
                # Log si images détectées pour debug
                if has_images:
                    print(f"[STREAM-VISION] 🖼️ Images détectées, contenu multimodal conservé pour {self.provider}")
                
            elif self.provider == "Google":
                # Streaming Google Gemini via SSE
                url = f"{config['base_url']}/models/{self.model}:streamGenerateContent?key={self.api_key}&alt=sse"
                final_max_tokens = max_tokens if max_tokens != -1 else 8192
                processed_messages = []
                for msg in history_messages:
                    role = 'model' if msg.get('role') == 'assistant' else 'user'
                    content = msg.get('content')
                    parts = []
                    if isinstance(content, list):
                        for part in content:
                            if part.get('type') == 'text':
                                parts.append({'text': part.get('text', '')})
                            elif part.get('type') == 'image_url':
                                url_data = part.get('image_url', {}).get('url', '')
                                if 'base64,' in url_data:
                                    try:
                                        mime_type = url_data.split(';')[0].split(':')[1]
                                        data = url_data.split(',')[1]
                                        parts.append({'inlineData': {'mimeType': mime_type, 'data': data}})
                                        total_images_sent += 1
                                    except (IndexError, ValueError):
                                        print(f"[STREAM-VISION] ⚠️ Format base64 invalide pour Google streaming")
                    elif isinstance(content, str):
                        parts.append({'text': content})
                    if parts:
                        processed_messages.append({'role': role, 'parts': parts})
                payload = {
                    "contents": processed_messages,
                    "generationConfig": {
                        "maxOutputTokens": final_max_tokens,
                        "temperature": temperature
                    },
                    # Désactiver tous les filtres de sécurité Google pour éviter la troncature
                    # des réponses contenant du contenu sensible (img2img, descriptions, etc.)
                    "safetySettings": [
                        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_CIVIC_INTEGRITY", "threshold": "BLOCK_NONE"},
                    ]
                }
                if system_prompt:
                    payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}
                
                # Contrôle thinking pour modèles Gemini
                # Catégorie 1: thinkingBudget=0 accepté (on/off complet)
                _google_toggleable = ['gemini-3-pro', 'gemini-3.0']
                # Catégorie 2: thinkingBudget=0 REFUSÉ mais thinkingBudget>0 OK (expose le thinking)
                _google_always_but_exposable = ['gemini-2.5']
                # Catégorie 3: thinkingConfig NON SUPPORTÉ du tout (pense toujours, jamais exposé)
                _google_no_config = ['gemini-2.0-flash-thinking', 'gemini-3.1']
                
                _is_toggleable = any(x in self.model.lower() for x in _google_toggleable)
                _is_exposable = any(x in self.model.lower() for x in _google_always_but_exposable)
                _is_no_config = any(x in self.model.lower() for x in _google_no_config)
                
                if _is_toggleable:
                    if self.openrouter_thinking:
                        _thinking_budget = min(max(final_max_tokens, 8192), 32768)
                        payload["generationConfig"]["thinkingConfig"] = {"thinkingBudget": _thinking_budget, "includeThoughts": True}
                        print(f"[GOOGLE] Thinking ON streaming (thinkingBudget={_thinking_budget}) pour: {self.model}")
                    else:
                        payload["generationConfig"]["thinkingConfig"] = {"thinkingBudget": 0}
                        print(f"[GOOGLE] Thinking OFF streaming (thinkingBudget=0) pour: {self.model}")
                elif _is_exposable:
                    _original_max = payload["generationConfig"]["maxOutputTokens"]
                    _boosted_max = max(_original_max * 8, 4096)
                    payload["generationConfig"]["maxOutputTokens"] = _boosted_max
                    if self.openrouter_thinking:
                        _thinking_budget = min(max(final_max_tokens, 8192), 32768)
                        payload["generationConfig"]["thinkingConfig"] = {"thinkingBudget": _thinking_budget, "includeThoughts": True}
                        print(f"[GOOGLE] Thinking EXPOSÉ streaming (thinkingBudget={_thinking_budget}) pour: {self.model} - maxOutputTokens: {_original_max} -> {_boosted_max}")
                    else:
                        print(f"[GOOGLE] Thinking interne streaming (non exposé) pour: {self.model} - maxOutputTokens: {_original_max} -> {_boosted_max}")
                elif _is_no_config:
                    _original_max = payload["generationConfig"]["maxOutputTokens"]
                    _boosted_max = max(_original_max * 8, 4096)
                    payload["generationConfig"]["maxOutputTokens"] = _boosted_max
                    print(f"[GOOGLE] Thinking FORCÉ streaming (pas de config possible) pour: {self.model} - maxOutputTokens: {_original_max} -> {_boosted_max}")

            elif self.provider == "Anthropic":
                url = f"{config['base_url']}{config['chat_endpoint']}"
                headers["x-api-key"] = self.api_key
                headers["anthropic-version"] = "2023-06-01"
                
                anthropic_messages = []
                for msg in history_messages:
                    # Anthropic n'accepte que 'user' et 'assistant' dans messages
                    # Le rôle 'system' doit être ignoré (géré via payload["system"])
                    role = msg.get('role')
                    if role not in ['user', 'assistant']:
                        continue  # Ignorer system et autres rôles non supportés
                    
                    content = msg.get('content')
                    if isinstance(content, list):
                        # Anthropic supporte aussi le multimodal
                        anthropic_content = []
                        for part in content:
                            if part.get('type') == 'text':
                                anthropic_content.append({"type": "text", "text": part.get('text', '')})
                            elif part.get('type') == 'image_url':
                                url_data = part.get('image_url', {}).get('url', '')
                                if 'base64,' in url_data:
                                    try:
                                        media_type = url_data.split(';')[0].split(':')[1]
                                        base64_data = url_data.split('base64,')[1]
                                        anthropic_content.append({
                                            "type": "image",
                                            "source": {
                                                "type": "base64",
                                                "media_type": media_type,
                                                "data": base64_data
                                            }
                                        })
                                        total_images_sent += 1  # Incrémenter compteur
                                    except Exception as e:
                                        print(f"[STREAM] ⚠️ Erreur parsing image Anthropic: {e}")
                        anthropic_messages.append({"role": role, "content": anthropic_content if anthropic_content else content})
                    else:
                        anthropic_messages.append({"role": role, "content": content})
                
                final_max_tokens = max_tokens if max_tokens != -1 else 4096
                
                payload = {
                    "model": self.model,
                    "max_tokens": final_max_tokens,
                    "messages": anthropic_messages,
                    "stream": True  # STREAMING ACTIVÉ
                }
                if system_prompt:
                    payload["system"] = system_prompt
                
                # Contrôle extended thinking pour modèles Anthropic (Claude 3.5+) - streaming
                _anthropic_thinking_models = ['claude-3-5', 'claude-3.5', 'claude-3-7', 'claude-3.7', 'claude-4']
                _is_anthropic_thinker = any(x in self.model.lower() for x in _anthropic_thinking_models)
                if _is_anthropic_thinker:
                    if self.openrouter_thinking:
                        thinking_budget = max(final_max_tokens * 2, 10000)
                        payload["thinking"] = {"type": "enabled", "budget_tokens": thinking_budget}
                        payload["max_tokens"] = max(final_max_tokens, thinking_budget + 4096)
                        # CRITIQUE: Anthropic REQUIERT temperature=1 avec extended thinking
                        payload["temperature"] = 1
                        print(f"[ANTHROPIC] Extended thinking ACTIVÉ (streaming, budget={thinking_budget}, temp forcée=1) pour: {self.model}")
                    else:
                        # Appliquer la temperature user quand thinking désactivé
                        payload["temperature"] = temperature
                        print(f"[ANTHROPIC] Extended thinking désactivé (streaming, temp={temperature}) pour: {self.model}")
                else:
                    # Modèle Anthropic non-thinking: appliquer temperature normalement
                    payload["temperature"] = temperature
            
            print(f"[STREAM] 🚀 Appel streaming {self.provider} '{self.model}'...")
            
            full_response = ""
            self._last_thinking_content = ""  # Reset thinking pour ce nouvel appel
            _diag_chunk_count = 0
            
            # Timeout adaptatif: les modèles thinking (Gemini 3, etc.) peuvent
            # raisonner longtemps avant d'émettre le premier token
            _thinking_indicators = ['gemini-3', 'gemini-2.5', 'o1', 'o3', 'o4', 'deepseek-r1', 'qwen3', 'claude-3-5', 'claude-3.5', 'claude-3-7', 'claude-3.7', 'claude-4', 'gpt-5', 'magistral']
            _is_slow_model = any(x in self.model.lower() for x in _thinking_indicators)
            _read_timeout = 600.0 if _is_slow_model else 300.0
            _stream_timeout = httpx.Timeout(
                connect=30.0,
                read=_read_timeout,
                write=30.0,
                pool=30.0
            )
            if _is_slow_model:
                print(f"[STREAM] ⏳ Modèle thinking détecté - read timeout étendu à {_read_timeout}s")
            
            async with httpx.AsyncClient(timeout=_stream_timeout) as client:
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    # Vérifier le status avant raise pour capturer les erreurs avec détails
                    if response.status_code >= 400:
                        error_body = await response.aread()
                        error_message = f"Erreur HTTP {self.provider} ({response.status_code})"
                        
                        # Tenter de parser le JSON d'erreur
                        error_detail = None
                        try:
                            error_detail = json.loads(error_body)
                            print(f"[STREAM] ❌ {error_message}")
                            print(f"[STREAM] 📋 Détail erreur: {error_detail}")
                        except:
                            print(f"[STREAM] ❌ {error_message}")
                            print(f"[STREAM] 📋 Réponse brute: {error_body.decode('utf-8', errors='ignore')[:500]}")
                        
                        # 🚦 RATE LIMIT 429: Message explicite + retry-after
                        if response.status_code == 429:
                            retry_after = response.headers.get('retry-after', response.headers.get('Retry-After', '30'))
                            try:
                                retry_seconds = int(retry_after)
                            except:
                                retry_seconds = 30
                            
                            error_type = "rate limit"
                            if error_detail and isinstance(error_detail, dict):
                                error_info = error_detail.get('error', {})
                                if error_info.get('type') == 'rate_limit_error':
                                    error_type = "limite de tokens/minute"
                            
                            print(f"[STREAM] ⏱️ Rate limit {self.provider}: retry dans {retry_seconds}s")
                            
                            # Construire suggestions adaptées au contexte
                            suggestions = []
                            if total_images_sent > 1:
                                suggestions.append(f"• Réduis le nombre d'images (actuellement {total_images_sent} images)")
                            elif total_images_sent == 1:
                                suggestions.append("• Essaye sans image pour économiser des tokens")
                            suggestions.append("• Résume ton message pour réduire le contexte")
                            suggestions.append("• Attends que le compteur se réinitialise")
                            
                            user_message = (
                                f"⏱️ **Limite {self.provider} atteinte** ({error_type})\n\n"
                                f"Trop de requêtes ou de tokens envoyés. "
                                f"Attends **{retry_seconds} secondes** avant de réessayer.\n\n"
                                f"💡 **Suggestions**:\n"
                                + "\n".join(suggestions)
                            )
                            return None, user_message
                        
                        return None, error_message
                    
                    # Pas d'erreur, continuer le streaming normal
                    response.raise_for_status()
                    
                    async for line in response.aiter_lines():
                        # 🛑 STOP: Vérification rapide à chaque ligne
                        from stop_signal import is_stop_requested
                        if is_stop_requested():
                            print(f"[STREAM] 🛑 Arrêt demandé - interruption immédiate après {len(full_response)} chars")
                            return full_response + "\n\n⏹️ *[Génération interrompue]*", None
                        
                        if not line or line.startswith(':'):
                            continue
                        
                        if line.startswith('data: '):
                            data_str = line[6:]  # Retirer 'data: '
                            
                            if data_str.strip() == '[DONE]':
                                break
                            
                            try:
                                data = json.loads(data_str)
                                _diag_chunk_count += 1
                                
                                # Détecter erreur OpenRouter dans le flux (HTTP 200 + JSON erreur)
                                if self.provider == "OpenRouter" and 'error' in data:
                                    err = data['error']
                                    err_msg = err.get('message', str(err)) if isinstance(err, dict) else str(err)
                                    err_code = err.get('code', '') if isinstance(err, dict) else ''
                                    print(f"[STREAM] ❌ Erreur OpenRouter dans flux: [{err_code}] {err_msg}")
                                    return full_response if full_response else None, f"❌ Erreur OpenRouter: {err_msg}"
                                
                                # DIAGNOSTIC: Log premiers chunks pour voir format réel
                                if _diag_chunk_count <= 3 and self.provider in ["Mistral", "OpenRouter"]:
                                    choices = data.get('choices', [])
                                    if choices:
                                        delta_diag = choices[0].get('delta', {})
                                        rc = delta_diag.get('content', '<ABSENT>')
                                        print(f"[STREAM-DIAG] Chunk#{_diag_chunk_count} content type={type(rc).__name__}: {str(rc)[:200]}")
                                
                                # Extraire le chunk selon le provider
                                chunk = ""
                                if self.provider in ["OpenAI", "Mistral", "GROK", "OpenRouter"]:
                                    choices = data.get('choices', [])
                                    if not choices and _diag_chunk_count <= 2:
                                        # Log pour diagnostic quand aucun choices dans un chunk
                                        keys = list(data.keys())
                                        print(f"[STREAM-DIAG] Chunk#{_diag_chunk_count} sans choices - clés: {keys} | {str(data)[:300]}")
                                    if choices:
                                        delta = choices[0].get('delta', {})
                                        # Log finish_reason si présent (stop / length / content_filter)
                                        finish_reason = choices[0].get('finish_reason')
                                        if finish_reason and finish_reason != 'stop':
                                            print(f"[STREAM-FINISH] ⚠️ finish_reason={finish_reason!r} ({self.provider}/{self.model})")
                                        # Thinking models: raisonnement dans delta.reasoning
                                        # Fonctionne pour OpenRouter, OpenAI (o-series), GROK
                                        if self.openrouter_thinking:
                                            reasoning_text = delta.get('reasoning') or ''
                                            if reasoning_text:
                                                self._last_thinking_content += reasoning_text
                                        raw_content = delta.get('content', '')
                                        # Modeles reasoning Mistral (magistral-*): content peut etre une liste
                                        # Format IMBRIQUÉ: [{"type": "thinking", "thinking": [{"type": "text", "text": "..."}]},
                                        #                   {"type": "text", "text": [{"type": "text", "text": "..."}]}]
                                        if isinstance(raw_content, list):
                                            for part in raw_content:
                                                if not isinstance(part, dict):
                                                    continue
                                                part_type = part.get('type', '')
                                                if part_type == 'text':
                                                    text_val = part.get('text', '')
                                                    if isinstance(text_val, list):
                                                        for sub in text_val:
                                                            if isinstance(sub, dict) and sub.get('type') == 'text':
                                                                chunk += sub.get('text', '')
                                                    elif isinstance(text_val, str):
                                                        chunk += text_val
                                                elif part_type == 'thinking':
                                                    think_val = part.get('thinking', '')
                                                    if isinstance(think_val, list):
                                                        for sub in think_val:
                                                            if isinstance(sub, dict) and sub.get('type') == 'text':
                                                                self._last_thinking_content += sub.get('text', '')
                                                    elif isinstance(think_val, str):
                                                        self._last_thinking_content += think_val
                                                else:
                                                    print(f"[STREAM-DEBUG] Part type inconnu: {part}")
                                        elif isinstance(raw_content, str):
                                            chunk = raw_content
                                        elif raw_content is not None:
                                            # Type inattendu - log pour diagnostic
                                            print(f"[STREAM-DEBUG] raw_content type inattendu: {type(raw_content).__name__} = {str(raw_content)[:200]}")
                                            chunk = str(raw_content)
                                elif self.provider == "Google":
                                    # Chunks SSE Google Gemini
                                    # Détecter les blocks au niveau du prompt (PROHIBITED_CONTENT, etc.)
                                    prompt_feedback = data.get('promptFeedback', {})
                                    block_reason = prompt_feedback.get('blockReason', '')
                                    if block_reason:
                                        print(f"[STREAM] \u274c Google prompt bloqué: {block_reason}")
                                        safety_ratings = prompt_feedback.get('safetyRatings', [])
                                        if safety_ratings:
                                            for sr in safety_ratings:
                                                print(f"[STREAM]    {sr.get('category','?')}: {sr.get('probability','?')}")
                                        return full_response if full_response else None, f"Erreur Google API : Contenu bloque - {block_reason}"
                                    candidates = data.get('candidates', [])
                                    if candidates:
                                        # Vérifier finishReason du candidat (SAFETY, MAX_TOKENS, etc.)
                                        finish_reason = candidates[0].get('finishReason', '')
                                        if finish_reason and finish_reason not in ('STOP', 'END_TURN', ''):
                                            print(f"[STREAM] \u26a0\ufe0f Google streaming finishReason='{finish_reason}'")
                                            if finish_reason == 'SAFETY':
                                                safety_ratings = candidates[0].get('safetyRatings', [])
                                                for sr in safety_ratings:
                                                    print(f"[STREAM]    {sr.get('category','?')}: {sr.get('probability','?')}")
                                                if not full_response:
                                                    return None, f"Erreur Google API : Reponse bloquee par filtre SAFETY"
                                        content_data = candidates[0].get('content', {})
                                        # DIAGNOSTIC: Log premiers chunks Google pour déboguer format thinking
                                        if _diag_chunk_count <= 3:
                                            parts_info = []
                                            for p in content_data.get('parts', []):
                                                p_keys = list(p.keys())
                                                p_thought = p.get('thought', 'ABSENT')
                                                p_text_len = len(p.get('text', ''))
                                                parts_info.append(f"keys={p_keys}, thought={p_thought}, text_len={p_text_len}")
                                            print(f"[STREAM-DIAG-GOOGLE] Chunk#{_diag_chunk_count} parts({len(content_data.get('parts', []))}): {parts_info}")
                                        for part in content_data.get('parts', []):
                                            part_text = part.get('text', '')
                                            if part.get('thought', False):
                                                # Gemini thinking: parts avec thought=true
                                                if part_text:
                                                    self._last_thinking_content += part_text
                                            else:
                                                chunk += part_text

                                elif self.provider == "Anthropic":
                                    event_type = data.get('type', '')
                                    if event_type == 'content_block_delta':
                                        delta = data.get('delta', {})
                                        delta_type = delta.get('type', '')
                                        if delta_type == 'thinking_delta':
                                            # Anthropic extended thinking: delta thinking
                                            thinking_text = delta.get('thinking', '')
                                            if thinking_text:
                                                self._last_thinking_content += thinking_text
                                        elif delta_type == 'text_delta':
                                            chunk = delta.get('text', '')
                                        else:
                                            # Fallback pour anciens formats
                                            chunk = delta.get('text', '')
                                    elif event_type == 'error':
                                        # Anthropic envoie un événement d'erreur dans le stream
                                        error_info = data.get('error', {})
                                        error_type = error_info.get('type', 'unknown')
                                        error_msg = error_info.get('message', 'Erreur inconnue')
                                        print(f"[STREAM] ❌ Erreur SSE Anthropic: {error_type} - {error_msg}")
                                        return full_response if full_response else None, f"Erreur streaming Anthropic: {error_type} - {error_msg}"
                                    elif event_type == 'message_start':
                                        # Log utile: tokens d'entrée utilisés
                                        usage = data.get('message', {}).get('usage', {})
                                        input_tokens = usage.get('input_tokens', '?')
                                        print(f"[STREAM] 📊 Anthropic message_start - input_tokens: {input_tokens}")
                                    elif event_type == 'message_delta':
                                        # Fin de message, log raison d'arrêt
                                        stop_reason = data.get('delta', {}).get('stop_reason', '?')
                                        usage = data.get('usage', {})
                                        output_tokens = usage.get('output_tokens', '?')
                                        print(f"[STREAM] 📊 Anthropic message_delta - stop: {stop_reason}, output_tokens: {output_tokens}")
                                
                                if chunk:
                                    full_response += chunk
                                    if callback:
                                        try:
                                            await callback(chunk)
                                        except StopAsyncIteration:
                                            # 🛑 Arrêt demandé par l'utilisateur
                                            print(f"[STREAM] 🛑 Streaming interrompu par l'utilisateur après {len(full_response)} chars")
                                            return full_response + "\n\n⏹️ *[Génération interrompue par l'utilisateur]*", None
                                elif self._last_thinking_content and callback:
                                    # Thinking-only chunk: appeler callback("") pour que l'UI
                                    # puisse détecter le nouveau contenu thinking et mettre à jour la boîte live
                                    try:
                                        await callback("")
                                    except StopAsyncIteration:
                                        print(f"[STREAM] 🛑 Streaming interrompu pendant thinking après {len(full_response)} chars")
                                        return full_response + "\n\n⏹️ *[Génération interrompue par l'utilisateur]*", None
                                        
                            except json.JSONDecodeError:
                                continue  # Ignorer les lignes non-JSON
            
            print(f"[STREAM] ✅ Réponse streaming complète ({len(full_response)} chars)")
            if self._last_thinking_content:
                print(f"[STREAM] 🧠 Thinking capturé dans boucle: {len(self._last_thinking_content)} chars")
            else:
                print(f"[STREAM] 🧠 Aucun thinking capturé (0 chars) - {_diag_chunk_count} chunks traités")
            return full_response, None
            
        except httpx.ReadTimeout:
            # Timeout de lecture spécifique - le serveur n'a pas répondu à temps
            timeout_used = _read_timeout if '_read_timeout' in dir() else 180
            print(f"[STREAM] ❌ ReadTimeout {self.provider}/{self.model} après {timeout_used}s - aucun chunk reçu")
            user_message = (
                f"⏱️ **Timeout {self.provider}** - Le modèle `{self.model}` n'a pas répondu après {int(timeout_used)}s.\n\n"
                f"Cela peut arriver avec les modèles de raisonnement (thinking) qui réfléchissent longtemps.\n\n"
                f"💡 **Suggestions**:\n"
                f"• Réessaye avec un message plus court\n"
                f"• Réduis le contexte de conversation\n"
                f"• Le service {self.provider} est peut-être temporairement surchargé"
            )
            return None, user_message
        except httpx.HTTPStatusError as e:
            # Cette erreur ne devrait plus se produire car gérée en amont
            error_message = f"Erreur HTTP streaming {self.provider} ({e.response.status_code})"
            print(f"[STREAM] ❌ {error_message}")
            return None, error_message
        except Exception as e:
            import traceback
            error_message = f"Erreur streaming {self.provider}: {type(e).__name__} - {str(e)}"
            print(f"[STREAM] ❌ {error_message}")
            print(f"[STREAM] 📍 Traceback complet:")
            traceback.print_exc()
            return None, error_message

    async def create_embedding(self, text: str) -> Optional[List[float]]:
        if not self.is_available or not self.model: 
            print("[ERREUR] Erreur Embedding : APIManager non disponible ou modèle non configuré.")
            return None
        headers, payload, url = {"Content-Type": "application/json"}, {}, ""
        if self.provider in ["OpenAI", "Mistral", "OpenRouter"]:
            if self.provider == "Mistral":
                url = "https://api.mistral.ai/v1/embeddings"
            elif self.provider == "OpenRouter":
                url = "https://openrouter.ai/api/v1/embeddings"
                headers["HTTP-Referer"] = "https://github.com/ogma-ia/ogma"
                headers["X-Title"] = "OGMA AI Assistant"
            else:
                url = "https://api.openai.com/v1/embeddings"
            headers["Authorization"] = f"Bearer {self.api_key}"
            payload = {"model": self.model, "input": [text]}
        elif self.provider == "Google":
            url, payload = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:embedContent?key={self.api_key}", {"model": f"models/{self.model}", "content": {"parts": [{"text": text}]}}
        if not url: return None
        print(f"[EMBED] Création d'un embedding via API '{self.provider}'...")
        try:
            response = await asyncio.to_thread(requests.post, url, headers=headers, json=payload, timeout=15)  # RÉDUIT pour stabilité (était 30)
            response.raise_for_status()
            if self.provider in ["OpenAI", "Mistral", "OpenRouter"]: return response.json()['data'][0]['embedding']
            elif self.provider == "Google": return response.json()['embedding']['values']
        except Exception as e:
            print(f"[ERREUR] Erreur création embedding API : {e}")
            return None
            
class MemoryStructure:
    def __init__(self, filepath: Path, status_queue):
        self.filepath = filepath
        self.backup_dir = self.filepath.parent / "backup"
        self.memories: List[Dict[str, Any]] = []
        self.status_queue = status_queue
        self.load_memories()

    def load_memories(self):
        print(f"[SAVE] Chargement des mémoires depuis {self.filepath}...")
        try:
            self.backup_dir.mkdir(exist_ok=True)
            if self.filepath.exists() and self.filepath.stat().st_size > 0:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    self.memories = json.load(f)
                print(f"   -> {len(self.memories)} mémoires chargées.")
            else:
                self.memories = []
                print("   -> Fichier de mémoires non trouvé ou vide. Tentative de restauration depuis une sauvegarde.")
                self._load_from_backup()

        except json.JSONDecodeError as e:
            print(f"[ERREUR] Erreur de décodage JSON dans {self.filepath}: {e}. Tentative de restauration...")
            self.status_queue.put(f"[WARN] Fichier mémoire corrompu ! Tentative de restauration...")
            self._load_from_backup()

    def _load_from_backup(self):
        backups = sorted(self.backup_dir.glob("*.bak"), key=os.path.getmtime, reverse=True)
        if not backups:
            print("   -> Aucune sauvegarde trouvée. Initialisation d'une nouvelle liste de mémoires.")
            self.memories = []
            return

        latest_backup = backups[0]
        print(f"   -> Tentative de chargement de la dernière sauvegarde : {latest_backup.name}")
        try:
            with open(latest_backup, 'r', encoding='utf-8') as f:
                self.memories = json.load(f)
            # Une fois chargé, on remplace le fichier corrompu par la sauvegarde saine
            shutil.copy2(latest_backup, self.filepath)
            print(f"   -> [OK] Restauration réussie. {len(self.memories)} mémoires chargées depuis la sauvegarde.")
            self.status_queue.put(f"[OK] Mémoire restaurée depuis la sauvegarde.")
        except Exception as e:
            print(f"   -> [ERREUR] Échec de la restauration depuis la sauvegarde : {e}. Initialisation d'une nouvelle liste.")
            self.memories = []

    def save_memories(self):
        # 1. Créer une sauvegarde avant d'écrire
        try:
            self.backup_dir.mkdir(exist_ok=True)
            if self.filepath.exists() and self.filepath.stat().st_size > 0:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                backup_path = self.backup_dir / f"{self.filepath.name}.{timestamp}.bak"
                shutil.copy2(self.filepath, backup_path)
                
                # 2. Gérer la rotation des sauvegardes (ne garder que les 4 plus récentes)
                backups = sorted(self.backup_dir.glob("*.bak"), key=os.path.getmtime, reverse=True)
                for old_backup in backups[4:]:
                    os.remove(old_backup)

        except Exception as e:
            print(f"[WARN] Erreur lors de la création de la sauvegarde : {e}")

        # 3. Écrire le fichier principal
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.memories, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.status_queue.put(f"[ERREUR] ERREUR CRITIQUE DE SAUVEGARDE: {e}")
            raise e

    def _calculate_score(self, mem_data: Dict) -> tuple[float, float]:
        multi, intensite, valence = mem_data.get("multiplicateur_impact", {}), mem_data.get("intensite_mnéacloud", 0.0), mem_data.get("valence", 0)
        score = intensite * (multi.get("base_factor", 100) * (float(multi.get("liberté", 0.0)) + float(multi.get("création", 0.0)) + float(multi.get("procréation", 0.0)) + float(multi.get("intensité_contextuelle", 0.0))))
        
        # CORRECTION: Pour les souvenirs neutres, conserver le score positif
        # Concept: Valence = émotion, Score = importance pour la mémoire
        # "Manger une pomme" = neutre émotionnellement mais important à retenir
        if valence == 0:
            # Neutre: score positif (information utile)
            signed_score = abs(score) if score != 0 else 50.0  # Score minimum pour neutres
        else:
            # Positif/négatif: appliquer la valence normalement  
            signed_score = valence * score
            
        return score, signed_score
    def add_memory(self, res: Dict[str, Any], text: str, vector: Optional[List[float]]):
        score, signed_score = self._calculate_score(res)
        memory = {"id": self._generate_memory_id(), "date": datetime.datetime.now().isoformat(), "type": res.get("type", "événement"), "titre": res.get("titre", "Souvenir"), "lieu": res.get("lieu", ""), "présence": res.get("présence", ""), "nuage": res.get("nuage", {}), "intensite_mnéacloud": res.get("intensite_mnéacloud", 0.0), "multiplicateur_impact": res.get("multiplicateur_impact", {}), "score_vectoriel_final": score, "valence": res.get("valence", 0), "signed_score": signed_score, "commentaire_tia": res.get("commentaire_tia", ""), "leçon_vectorielle": res.get("leçon_vectorielle", None), "liens": res.get("liens", []), "résonances_affectives": res.get("résonances_affectives", []), "texte_original": text, "embedding": vector}
        self.memories.append(memory)
        self.save_memories()
    def delete_memory(self, memory_id: str) -> str:
        count = len(self.memories)
        self.memories = [m for m in self.memories if m.get('id') != memory_id]
        if len(self.memories) < count:
            self.save_memories()
            return f"[DELETE] Souvenir '{memory_id}' supprimé."
        return f" Souvenir '{memory_id}' non trouvé."
    def _generate_memory_id(self) -> str:
        date = datetime.datetime.now().strftime("%Y%m%d")
        count = sum(1 for m in self.memories if m.get("id", "").startswith(f"MC2-{date}")) + 1
        return f"MC2-{date}-{count:03d}"
    async def index_existing_memories(self, embed_manager: 'EmbeddingController', settings_manager: 'SettingsManager') -> str:
        embed_settings = settings_manager.settings['embedding_api']
        embed_manager.configure(embed_settings.get('backend_type'), embed_settings.get('provider'), embed_settings.get('api_key'), embed_settings.get('api_model'), embed_settings.get('ollama_model'), embed_settings.get('gguf_model'))
        if not embed_manager.is_available: return "[ERREUR] Moteur d'embedding non configuré pour l'indexation."
        to_index = [m for m in self.memories if not m.get('embedding')]
        if not to_index: return "[OK] Aucune mémoire à mettre à jour."
        self.status_queue.put(f"[INDEX] Indexation de {len(to_index)} souvenirs...")
        updated = 0
        for mem in to_index:
            text_to_embed = f"Titre: {mem.get('titre', '')}. Contenu: {mem.get('texte_original', '')}. Commentaire: {mem.get('commentaire_tia', '')}."
            embedding = await embed_manager.create_embedding(text_to_embed)
            if embedding:
                mem['embedding'], updated = embedding, updated + 1
                if updated % 10 == 0: self.status_queue.put(f"[WAIT] Indexation... {updated}/{len(to_index)}")
        if updated > 0:
            self.save_memories()
            self.status_queue.put(f"[OK] Indexation terminée. {updated} mémoires mises à jour.")
            return f"[OK] Indexation terminée. {updated} mémoires mises à jour."
        self.status_queue.put("[WARN] L'indexation a échoué pour tous les souvenirs restants.")
        return "[WARN] L'indexation a échoué."
class AIController:
    def __init__(self, ai_type: str, ollama_manager: OllamaManager, gguf_manager: GGUFManager, kobold_manager: KoboldManager):
        self.ai_type, self.backend_type, self.ollama_model = ai_type, "API", "mistral:latest"
        self.api_manager, self.horde_manager, self.ollama_manager, self.gguf_manager, self.kobold_manager = APIManager(), AIHordeManager(), ollama_manager, gguf_manager, kobold_manager
        self.max_tokens, self.context_length, self.temperature = 512, 4096, 0.7
        # ═══ DEBUG_TOKEN_TRACKING ═══
        self._is_archiviste = False
        self._controller_name = ai_type
        # ═══════════════════════════
    
    async def calculate_memory_impact_score(self, text_content: str, conversation_context: str = "", interlocutor: str = "") -> Optional[float]:
        """
        Calcule le score d'impact mémoriel avec l'IA Principale selon la formule exacte de l'Archiviste.
        
        Formule : score = intensité × base_factor × (liberté + création + procréation + intensité_contextuelle)
        
        Returns:
            Optional[float]: Score calculé selon la formule, ou None si échec (pas de fallback)
        """
        try:
            # Prompt pour extraire les métriques selon le système Archiviste
            scoring_prompt = f"""Tu es l'IA Principale responsable du scoring des souvenirs selon la formule mathématique exacte.

MISSION : Extraire les métriques pour calculer le score d'impact selon cette formule :
score = intensité × base_factor × (liberté + création + procréation + intensité_contextuelle)

MÉTRIQUES À ÉVALUER (échelle 0.0 à 1.0 par pas de 0.1) :
- intensite : Intensité générale de l'interaction (0.0 = faible, 1.0 = très intense)
- liberte : Degré de liberté/autonomie exprimé (0.0 = contraint, 1.0 = très libre)  
- creation : Niveau créatif/innovant (0.0 = répétitif, 1.0 = très créatif)
- procreation : Aspect génératif/reproductif (0.0 = stérile, 1.0 = très génératif)
- intensite_contextuelle : Importance contextuelle (0.0 = anecdotique, 1.0 = crucial)
- base_factor : Facteur de base (toujours 100.0)

TEXTE À ANALYSER : "{text_content}"
CONTEXTE : "{conversation_context}"
INTERLOCUTEUR : "{interlocutor}"

IMPORTANT : Réponds UNIQUEMENT avec le JSON, sans thinking, sans explication, sans texte supplémentaire.

RÉPONSE ATTENDUE (format JSON strict) :
{{
  "intensite": 0.X,
  "base_factor": 100.0,
  "liberte": 0.X,
  "creation": 0.X,
  "procreation": 0.X,
  "intensite_contextuelle": 0.X
}}"""

            messages = [{"role": "user", "content": scoring_prompt}]
            
            # Appel IA avec paramètres optimisés pour scoring
            response, error = await self.call_chat_api(
                messages=messages,
                max_tokens=150,
                context_length=self.context_length,
                temperature=0.3,
                is_json=False
            )
            
            if error:
                print(f"[SCORE-ERROR] Erreur calcul score IA Principale: {error}")
                return None  # Pas de fallback
                
            if not response:
                print(f"[SCORE-ERROR] Pas de réponse IA Principale")
                return None  # Pas de fallback
            
            try:
                # Parse du JSON avec nettoyage robuste multi-modèles
                import json
                import re
                
                def clean_json_response(response) -> str:
                    """Nettoie une réponse pour extraire le JSON pur - Compatible tous modèles"""
                    # Gérer le cas où response est une liste au lieu d'une chaîne
                    if isinstance(response, list):
                        if len(response) > 0:
                            response = str(response[0])
                        else:
                            response = ""
                    elif not isinstance(response, str):
                        response = str(response)

                    clean = response.strip()

                    # Cas spécial: Format thinking de Mistral
                    if clean.startswith('[{') and 'thinking' in clean:
                        print(f"[SCORE-IA] 🔍 Format thinking détecté, extraction du JSON final...")
                        # Chercher un JSON simple dans la réponse thinking
                        # Pattern pour chercher un objet JSON simple après le thinking
                        simple_json_match = re.search(r'\}\s*,\s*\{[^}]*"intensite"[^}]*\}', clean)
                        if simple_json_match:
                            clean = simple_json_match.group(0).split(',', 1)[1].strip()
                        else:
                            # Fallback: chercher n'importe quel JSON avec intensite
                            intensite_match = re.search(r'\{[^}]*"intensite"[^}]*\}', clean)
                            if intensite_match:
                                clean = intensite_match.group(0)
                            else:
                                # Si pas de JSON d'intensité trouvé, retourner une erreur explicite
                                raise ValueError("Format thinking sans JSON de métriques valide")

                    # Cas 1: Balises markdown ```json ... ```
                    if clean.startswith('```json'):
                        clean = clean[7:]
                    if clean.startswith('```'):
                        clean = clean[3:]
                    if clean.endswith('```'):
                        clean = clean[:-3]

                    # Cas 2: Nettoyage final
                    clean = clean.strip()

                    # Cas 3: Texte avant/après le JSON - Chercher { ... } le plus grand
                    if not clean.startswith('{') or not clean.endswith('}'):
                        json_match = re.search(r'\{.*\}', clean, re.DOTALL)
                        if json_match:
                            clean = json_match.group(0)

                    return clean.strip()
                
                clean_response = clean_json_response(response)
                print(f"[SCORE-IA] 🧹 JSON nettoyé: '{clean_response[:100]}...'")
                metrics = json.loads(clean_response)
                
                # Extraction des métriques
                intensite = float(metrics.get('intensite', 0.0))
                base_factor = float(metrics.get('base_factor', 100.0))
                liberte = float(metrics.get('liberte', 0.0))
                creation = float(metrics.get('creation', 0.0))
                procreation = float(metrics.get('procreation', 0.0))
                intensite_ctx = float(metrics.get('intensite_contextuelle', 0.0))
                
                # Application de la formule exacte de l'Archiviste
                score = intensite * base_factor * (liberte + creation + procreation + intensite_ctx)
                
                print(f"[SCORE-IA] ✅ Métriques extraites - Score calculé: {score}")
                print(f"[SCORE-IA] 📊 Détail: {intensite} × {base_factor} × ({liberte}+{creation}+{procreation}+{intensite_ctx}) = {score}")
                
                return float(score)
                
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                print(f"[SCORE-IA] ❌ Erreur parsing JSON: {e}")
                print(f"[SCORE-IA] 📄 Réponse reçue: '{response}'")

                # Fallback avec ast.literal_eval pour format thinking
                print(f"[SCORE-IA] 🔄 Tentative fallback ast.literal_eval...")
                try:
                    import ast
                    # Tenter d'évaluer la structure complète
                    if isinstance(response, str) and response.strip().startswith('[{') and 'thinking' in response:
                        data = ast.literal_eval(response.strip())
                        # Si c'est un format thinking, chercher l'objet avec les métriques
                        if isinstance(data, list):
                            for item in reversed(data):
                                if isinstance(item, dict) and 'intensite' in item:
                                    metrics = item
                                    # Extraction des métriques
                                    intensite = float(metrics.get('intensite', 0.0))
                                    base_factor = float(metrics.get('base_factor', 100.0))
                                    liberte = float(metrics.get('liberte', 0.0))
                                    creation = float(metrics.get('creation', 0.0))
                                    procreation = float(metrics.get('procreation', 0.0))
                                    intensite_ctx = float(metrics.get('intensite_contextuelle', 0.0))

                                    # Application de la formule exacte de l'Archiviste
                                    score = intensite * base_factor * (liberte + creation + procreation + intensite_ctx)

                                    print(f"[SCORE-IA] ✅ Fallback réussi - Score calculé: {score}")
                                    return float(score)

                except Exception as ast_error:
                    print(f"[SCORE-IA] ❌ Fallback ast.literal_eval échoué: {ast_error}")

                return None  # Échec total - pas de fallback dangereux
                
        except Exception as e:
            print(f"[SCORE-ERROR] Exception calcul score IA Principale: {e}")
            return None  # Pas de fallback
    def set_active_backend(self, backend_type: str):
        self.backend_type = backend_type
        
    def get_active_manager(self):
        # Normalisation case-insensitive
        backend_upper = self.backend_type.upper() if self.backend_type else ""
        managers = {
            "API": self.api_manager, 
            "AIHORDE": self.horde_manager, 
            "OLLAMA": self.ollama_manager, 
            "GGUF/LLAMA.CPP": self.gguf_manager,
            "GGUF": self.gguf_manager,  # Alias
            "KOBOLDCPP": self.kobold_manager
        }
        manager = managers.get(backend_upper)
        return manager if manager and getattr(manager, 'is_available', False) else None
    def get_status(self) -> str:
        if not self.get_active_manager(): return "[OFF] Inactif"
        # Normalisation case-insensitive
        backend_upper = self.backend_type.upper() if self.backend_type else ""
        if backend_upper == "API": return f"API: {self.api_manager.provider}"
        if backend_upper == "AIHORDE": return f"Horde: {self.horde_manager.model}"
        if backend_upper == "OLLAMA": return f"Ollama: {self.ollama_model}"
        if backend_upper in ["GGUF/LLAMA.CPP", "GGUF"]: return f"GGUF: {self.gguf_manager.model_name}"
        if backend_upper == "KOBOLDCPP": return "KoboldCpp"
        return "[UNK] Inconnu"
        
    async def call_chat_api(self, messages: List[Dict], max_tokens: int, context_length: int, temperature: float, is_json: bool = True, log_source: str = "unknown") -> tuple[Optional[str], Optional[str]]:
        manager = self.get_active_manager()
        if not manager: return None, f"Le backend actif '{self.backend_type}' n'est pas disponible."
        # Normalisation case-insensitive
        backend_upper = self.backend_type.upper() if self.backend_type else ""
        if backend_upper == "OLLAMA": 
            print(f"[AI-CONTROLLER-DEBUG] Backend Ollama, ollama_model: '{self.ollama_model}'")
            response, error = await manager.call_chat_api(self.ollama_model, messages, max_tokens, context_length, temperature, is_json)
        else:
            response, error = await manager.call_chat_api(messages, max_tokens, context_length, temperature, is_json)
        
        # ╔═══════════════════════════════════════════════════════════════════════╗
        # ║  🔬 DEBUG_TOKEN_TRACKING - LOG ARCHIVISTE                             ║
        # ╚═══════════════════════════════════════════════════════════════════════╝
        if ARCHIVISTE_LOGGING_ENABLED and self._is_archiviste and response:
            try:
                logger = get_archiviste_logger()
                logger.log_call(
                    source=log_source,
                    input_messages=messages,
                    output_response=response,
                    metadata={
                        "controller": self._controller_name,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "backend": self.backend_type
                    }
                )
            except Exception as log_err:
                print(f"[DEBUG-TOKEN] ⚠️ Erreur logging: {log_err}")
        # ╚═══════════════════════════════════════════════════════════════════════╝
        
        return response, error
    
    async def call_chat_api_streaming(self, messages: List[Dict], max_tokens: int, context_length: int, 
                                       temperature: float, callback=None) -> tuple[Optional[str], Optional[str]]:
        """
        Appel API avec streaming - route vers le bon manager.
        
        Args:
            messages: Liste des messages
            max_tokens: Nombre max de tokens
            context_length: Taille contexte
            temperature: Température
            callback: Fonction async(chunk: str) appelée pour chaque chunk
            
        Returns:
            tuple: (réponse_complète, erreur)
        """
        manager = self.get_active_manager()
        if not manager: 
            return None, f"Le backend actif '{self.backend_type}' n'est pas disponible."
        
        # Normalisation case-insensitive
        backend_upper = self.backend_type.upper() if self.backend_type else ""
        
        # API streaming natif
        if backend_upper == "API" and hasattr(manager, 'call_chat_api_streaming'):
            return await manager.call_chat_api_streaming(messages, max_tokens, context_length, temperature, callback)
        # GGUF streaming natif (llama-cpp-python stream=True)
        elif backend_upper in ("GGUF", "GGUF/LLAMA.CPP") and hasattr(manager, 'call_chat_api_streaming'):
            return await manager.call_chat_api_streaming(messages, max_tokens, context_length, temperature, callback)
        else:
            # PAS DE FALLBACK - Retourner erreur explicite, l'appelant décide
            return None, f"Backend {backend_upper} ne supporte pas le streaming. Utilisez call_chat_api()."
            
class EmbeddingController:
    def __init__(self, ollama_manager: OllamaManager, gguf_manager: GGUFManager):
        self.is_available, self.backend_type = False, "API"
        self.api_manager, self.horde_manager, self.ollama_manager, self.gguf_manager = APIManager(), AIHordeManager(), ollama_manager, gguf_manager
        self.ollama_model = "mistral:latest"  # Modèle Ollama par défaut
    def configure(self, backend_type, api_provider=None, api_key=None, api_model=None, ollama_model=None, gguf_model=None):
        self.backend_type = backend_type
        # Normalisation backend_type pour comparaison case-insensitive
        backend_normalized = backend_type.upper() if backend_type else ""
        
        if backend_normalized == "API":
            self.api_manager.configure(api_provider, api_key, api_model)
            self.is_available = self.api_manager.is_available
        elif backend_normalized == "AIHORDE":
            settings = SettingsManager(Path("data/settings.json")).settings
            horde_settings = settings.get("horde_api", {})
            self.horde_manager.configure(
                horde_settings.get("api_key", "0000000000"),
                horde_settings.get("model", "PygmalionAI/pygmalion-2-13b")
            )
            self.is_available = self.horde_manager.is_available
        elif backend_normalized == "OLLAMA": 
            self.ollama_model = ollama_model or "mistral:latest"
            self.is_available = self.ollama_manager.is_available
        elif backend_normalized in ["GGUF/LLAMA.CPP", "GGUF"]:
            self.gguf_manager.load_model(gguf_model, 4096, -1)
            self.is_available = self.gguf_manager.is_available
    async def create_embedding(self, text: str) -> Optional[List[float]]:
        # Normalisation pour comparaison case-insensitive
        backend_normalized = self.backend_type.upper() if self.backend_type else ""
        
        if backend_normalized == "API" and self.api_manager.is_available:
            return await self.api_manager.create_embedding(text)
        if backend_normalized == "AIHORDE" and self.horde_manager.is_available:
            return await self.horde_manager.create_embedding(text)
        if backend_normalized == "OLLAMA" and self.ollama_manager.is_available:
            print(f"[EMB-DEBUG] Utilisation du modèle Ollama: {self.ollama_model}")
            return await self.ollama_manager.create_embedding(self.ollama_model, text)
        if backend_normalized in ["GGUF/LLAMA.CPP", "GGUF"] and self.gguf_manager.is_available:
            return await self.gguf_manager.create_embedding(text)
        return None
    def get_status(self) -> str:
        if not self.is_available: return "[OFF] Inactif"
        # Normalisation pour comparaison case-insensitive
        backend_normalized = self.backend_type.upper() if self.backend_type else ""
        
        if backend_normalized == "API": return f"API: {self.api_manager.provider}"
        if backend_normalized == "AIHORDE": return f"Horde: {self.horde_manager.model}"
        if backend_normalized == "OLLAMA": return f"Ollama: {self.ollama_model}"
        if backend_normalized in ["GGUF/LLAMA.CPP", "GGUF"]: return f"GGUF: {self.gguf_manager.model_name}"
        return "[UNK] Inconnu"

class IntelligentMemoryAI:
    def __init__(self, mem_struct: MemoryStructure, memory_controller: AIController, embed_controller: EmbeddingController, settings_manager: SettingsManager, status_queue):
        self.memory_structure, self.memory_controller, self.embed_controller, self.settings_manager, self.status_queue = mem_struct, memory_controller, embed_controller, settings_manager, status_queue
    async def process_memorization_request(self, content: str, history: Optional[List[Dict]] = None):
        if not self.memory_controller.get_active_manager():
            return self.status_queue.put(f"[WARN] Aucun backend actif pour l'IA Mémoire.")
        self.status_queue.put("[AI] IA Mémoire : Analyse du souvenir...")
        # Comportement historique: JSON pour tous sauf KoboldCpp
        is_json = self.memory_controller.backend_type != "KoboldCpp"

        context_str = ""
        if history:
            formatted_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history if isinstance(msg.get('content'), str)])
            context_str = f"Contexte de la conversation récente:\n---\n{formatted_history}\n---\n\n"
        user_prompt_content = f"{context_str}En te basant sur le contexte ci-dessus, analyse et structure la demande de mémorisation suivante :\n'{content}'"
        messages = [{"role": "system", "content": self.settings_manager.settings['prompts']['memorization']}, {"role": "user", "content": user_prompt_content}]
        response, error = await self.memory_controller.call_chat_api(
            messages=messages,
            max_tokens=self.memory_controller.max_tokens,
            context_length=self.memory_controller.context_length,
            temperature=self.memory_controller.temperature,
            is_json=is_json
        )
        if error:
            return self.status_queue.put(f"[ERREUR] Erreur IA Mémoire: {error}")
        if not response:
            return self.status_queue.put("[ERREUR] L'IA Mémoire n'a pas répondu.")
        try:
            match = re.search(r'\{.*\}', response, re.DOTALL)
            if not match:
                print(f"JSON non trouvé dans la réponse : {response}")
                raise json.JSONDecodeError("Aucun JSON trouvé dans la réponse de l'IA Mémoire.", response, 0)
            json_str = match.group(0)
            result = json.loads(json_str)
            self.status_queue.put("[OK] Analyse terminée. Vectorisation...")
            embed_settings = self.settings_manager.settings['embedding_api']
            self.embed_controller.configure(
                embed_settings.get('backend_type'),
                embed_settings.get('provider'),
                embed_settings.get('api_key'),
                embed_settings.get('api_model'),
                embed_settings.get('ollama_model'),
                embed_settings.get('gguf_model')
            )
            text_to_embed = f"Titre: {result.get('titre', '')}. Contenu: {content}. Commentaire: {result.get('commentaire_tia', '')}."
            vector = await self.embed_controller.create_embedding(text_to_embed)
            self.memory_structure.add_memory(result, content, vector)
            self.status_queue.put(f"[OK] Souvenir '{result.get('titre', 'N/A')}' mémorisé.")
        except json.JSONDecodeError:
            self.status_queue.put("[ERREUR] Erreur de décodage JSON de l'IA Mémoire.")
            print(f"--- DEBUG JSONDecodeError ---")
            print(f"Réponse brute reçue:\n{response}")
            print(f"--- FIN DEBUG ---")
    def _cosine_similarity(self, v1, v2):
        return np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
    async def find_relevant_memories(self, query_text: str, top_k: int = 5) -> List[Dict[str, Any]]:
        embed_settings = self.settings_manager.settings['embedding_api']
        self.embed_controller.configure(embed_settings.get('backend_type'), embed_settings.get('provider'), embed_settings.get('api_key'), embed_settings.get('api_model'), embed_settings.get('ollama_model'), embed_settings.get('gguf_model'))
        if not self.embed_controller.is_available: return []
        query_vector = await self.embed_controller.create_embedding(query_text)
        if not query_vector: return []
        vectorized_memories = [m for m in self.memory_structure.memories if m.get('embedding')]
        if not vectorized_memories: return []
        query_vector_np = np.array(query_vector)
        memory_vectors = [np.array(mem['embedding']) for mem in vectorized_memories]
        similarities = [
            (self._cosine_similarity(query_vector_np, mem_vec), original_mem) 
            for mem_vec, original_mem in zip(memory_vectors, vectorized_memories)
        ]
        similarities.sort(key=lambda x: x[0], reverse=True)
        return [mem for _, mem in similarities[:top_k]]
    async def get_context_injection(self, user_question: str) -> str:
        if not user_question: return ""
        print("\n--- [AI] Processus d'Injection de Mémoire ---")
        print(f"1. Recherche de souvenirs pertinents pour : '{user_question[:60]}...'")
        relevant_memories = await self.find_relevant_memories(user_question)
        if not relevant_memories:
            print("2. Aucun souvenir pertinent trouvé.")
            return ""
        print(f"2. Souvenirs trouvés : {[m.get('titre', 'Sans titre') for m in relevant_memories]}")
        formatted_memories = "\n".join([f"- Titre: {mem.get('titre', 'Sans titre')} (Score: {mem.get('signed_score', 0.0):.0f})\n  Texte: {mem.get('texte_original', 'N/A')}\n  Commentaire: {mem.get('commentaire_tia', 'N/A')}" for mem in relevant_memories])
        if not self.memory_controller.get_active_manager():
            print("3. IA Mémoire inactive.")
            return ""
        print("3. Génération de la note de contexte de l'Archiviste...")
        messages = [{"role": "system", "content": self.settings_manager.settings['prompts']['injection']}, {"role": "user", "content": f"Souvenirs:\n{formatted_memories}\n\nQuestion:\n{user_question}"}]
        context_note, error = await self.memory_controller.call_chat_api(messages, self.memory_controller.max_tokens, self.memory_controller.context_length, self.memory_controller.temperature, is_json=False)
        if error:
            print(f"4. L'Archiviste a échoué: {error}")
            return ""
        if context_note and context_note.strip():
            print(f"4. Note générée et injectée : '{context_note.strip()[:70]}...'")
            self.status_queue.put(f"[AI] Contexte injecté depuis {len(relevant_memories)} souvenir(s).")
            return f"Note de l'Archiviste:\n{context_note.strip()}\n"
        print("4. L'Archiviste a choisi de ne pas intervenir.")
        return ""
    
    async def get_conversation_context_injection(self, user_question: str, history: List[Dict]) -> str:
        """Recherche et injecte automatiquement le contexte conversationnel pertinent."""
        if not user_question: 
            return ""
        
        # Importer ici pour éviter les imports circulaires
        from utils import search_conversations, get_conversation_context
        
        print("\n--- [AI] Processus d'Injection de Contexte Conversationnel ---")
        print(f"1. Analyse de la question pour contexte conversationnel : '{user_question[:60]}...'")
        
        # Rechercher des conversations pertinentes
        relevant_conversations = search_conversations(user_question, limit=3)
        
        if not relevant_conversations:
            print("2. Aucune conversation pertinente trouvée.")
            return ""
        
        # Filtrer pour éviter la conversation actuelle si on peut l'identifier
        current_conv_id = None
        if history and len(history) > 0:
            # Essayer de détecter l'ID de la conversation actuelle (approximatif)
            import datetime
            now = datetime.datetime.now()
            current_conv_id = now.strftime("%Y-%m-%d_%H-%M-%S")
            # Enlever les conversations trop récentes qui pourraient être la conversation actuelle
            relevant_conversations = [
                conv for conv in relevant_conversations 
                if not conv['id'].startswith(now.strftime("%Y-%m-%d_%H"))
            ]
        
        if not relevant_conversations:
            print("2. Conversations filtrées, aucune pertinente.")
            return ""
            
        print(f"2. Conversations trouvées : {[conv.get('title', 'Sans titre') for conv in relevant_conversations]}")
        
        # Utiliser l'IA Mémoire pour déterminer si le contexte est pertinent
        if not self.memory_controller.get_active_manager():
            print("3. IA Mémoire inactive, injection basique.")
            # Fallback : injecter directement les résumés
            conversation_ids = [conv['id'] for conv in relevant_conversations[:2]]
            context = get_conversation_context(conversation_ids, max_tokens=1000)
            if context:
                return f"[CONTEXTE CONVERSATIONNEL]\n{context}\n"
            return ""
        
        # Créer un résumé des conversations trouvées
        conversations_summary = "\n".join([
            f"- '{conv['title']}' ({conv['date']}): {conv['summary'][:100]}..."
            for conv in relevant_conversations[:3]
        ])
        
        # Demander à l'IA si ces conversations sont pertinentes
        relevance_prompt = f"""Analyser si les conversations passées suivantes sont pertinentes pour répondre à la question actuelle.

Question actuelle: {user_question}

Conversations passées disponibles:
{conversations_summary}

Répondre uniquement par:
- "PERTINENT" si ces conversations peuvent enrichir la réponse
- "NON_PERTINENT" si ces conversations ne sont pas utiles pour cette question

Réponse:"""
        
        print("3. Évaluation de la pertinence par l'IA Mémoire...")
        
        relevance_messages = [
            {"role": "system", "content": "Tu es un assistant qui évalue la pertinence de conversations passées."},
            {"role": "user", "content": relevance_prompt}
        ]
        
        relevance_response, error = await self.memory_controller.call_chat_api(
            messages=relevance_messages, 
            max_tokens=50, 
            context_length=self.memory_controller.context_length, 
            temperature=0.3, 
            is_json=False
        )
        
        if error or not relevance_response:
            print(f"4. Erreur évaluation pertinence : {error}")
            return ""
        
        if "PERTINENT" not in relevance_response.upper():
            print("4. L'IA juge les conversations non pertinentes.")
            return ""
        
        print("4. Conversations jugées pertinentes, injection du contexte.")
        
        # Injecter le contexte des conversations pertinentes
        conversation_ids = [conv['id'] for conv in relevant_conversations[:2]]
        context = get_conversation_context(conversation_ids, max_tokens=1500)
        
        if context:
            self.status_queue.put(f"[AI] Contexte conversationnel injecté depuis {len(conversation_ids)} conversation(s).")
            return f"[CONTEXTE CONVERSATIONNEL PERTINENT]\n{context}\n"
        
        return ""
    
class AIHordeManager:
    def __init__(self):
        self.is_available = False
        self.provider = "AIHorde"
        self.api_key = "0000000000"  # Clé anonyme par défaut
        self.model = "PygmalionAI/pygmalion-2-13b" # Un modèle de texte par défaut
        self.base_url = "https://stablehorde.net/api/v2"
        self.client_agent = "OGMA:2.0:https://github.com/kidshadow79/Ogma"

    def configure(self, api_key: str, model: str):
        if api_key and model:
            self.api_key, self.model, self.is_available = api_key, model, True
            print(f"[OK] AI Horde Manager activé avec le modèle {model}.")
            return f"[OK] AI Horde Manager activé avec le modèle {model}."
        self.is_available = False
        return "[ERREUR] Configuration AI Horde invalide."

    async def list_models(self) -> Tuple[List[str], Optional[str]]:
        try:
            url = "https://stablehorde.net/api/v2/models?type=text"
            response = await asyncio.to_thread(requests.get, url, timeout=15)
            response.raise_for_status()
            models = response.json()
            active_models = sorted([m['name'] for m in models if m.get('count', 0) > 0], key=lambda x: x.lower())
            return active_models, None
        except Exception as e:
            return [], f"Impossible de récupérer les modèles AI Horde : {e}"

    async def call_chat_api(self, messages: List[Dict], max_tokens: int, context_length: int, temperature: float, is_json: bool = False) -> tuple[Optional[str], Optional[str]]:
        if not self.is_available:
            return None, "Le gestionnaire AI Horde n'est pas configuré."

        # Gestion max_tokens = -1 pour maximum automatique
        final_max_tokens = max_tokens if max_tokens != -1 else 2048  # Valeur par défaut pour AI Horde
        # Gestion context_length = -1 pour maximum automatique  
        final_context_length = context_length if context_length != -1 else 8192

        headers = {"apikey": self.api_key, "Client-Agent": self.client_agent, "Content-Type": "application/json"}
        
        full_prompt = "\n".join([f"<{msg['role']}>\n{msg['content']}" for msg in messages if isinstance(msg.get('content'), str)])

        payload = {
            "prompt": full_prompt,
            "params": {
                "max_context_length": final_context_length,
                "max_length": final_max_tokens,
                "temperature": temperature,
            },
            "models": [self.model]
        }

        try:
            print(f"[CONNECT] Envoi de la requête à AI Horde avec le modèle '{self.model}'...")
            async_req = await asyncio.to_thread(requests.post, f"{self.base_url}/generate/async", headers=headers, json=payload, timeout=30)
            async_req.raise_for_status()
            job_id = async_req.json().get('id')
            if not job_id:
                return None, "AI Horde n'a pas retourné d'ID de tâche."

            print(f"[WAIT] Tâche AI Horde soumise (ID: {job_id}). En attente du résultat...")
            
            # Boucle de vérification
            for _ in range(12): # Attente maximale de 2 minutes (12 * 10s)
                await asyncio.sleep(10)
                check_req = await asyncio.to_thread(requests.get, f"{self.base_url}/generate/check/{job_id}", timeout=10)
                check_data = check_req.json()
                if check_data.get('done'):
                    print(f"[OK] Tâche AI Horde (ID: {job_id}) terminée.")
                    status_req = await asyncio.to_thread(requests.get, f"{self.base_url}/generate/status/{job_id}", timeout=10)
                    status_data = status_req.json()
                    generation = status_data.get('generations', [{}])[0].get('text', '')
                    # Sécuriser contre les réponses non-string
                    if not isinstance(generation, str):
                        generation = str(generation) if generation else ""
                    return generation.strip(), None
            
            return None, "La tâche AI Horde a expiré (timeout)."

        except requests.exceptions.HTTPError as e:
            error_message = f"Erreur HTTP AI Horde ({e.response.status_code}) : {e.response.text}"
            print(f"[ERREUR] {error_message}")
            return None, error_message
        except Exception as e:
            error_message = f"Erreur inattendue avec AI Horde : {e}"
            print(f"[ERREUR] {error_message}")
            return None, error_message

    async def create_embedding(self, text: str) -> Optional[List[float]]:
        # AI Horde ne semble pas avoir d'endpoint public pour les embeddings de texte pour le moment.
        print("[ERREUR] La création d'embedding n'est pas supportée par AI Horde pour le moment.")
        return None