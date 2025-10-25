"""
core_logic.py
----------------
- MODIFICATION ARCHITECTURALE : La classe `MemoryStructure` a été dotée d'un
  système de sauvegarde et de restauration automatique pour prévenir la perte de données.
- MODIFICATION (`save_memories`) :
  - Avant chaque sauvegarde, une copie de l'ancien fichier mémoire est créée dans un
    nouveau dossier `data/memory/backup/`.
  - Une rotation est effectuée pour ne conserver que les 10 sauvegardes les plus récentes.
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
class SettingsManager:
    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.settings = {
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
                "use_turbo": False,  # Mode Standard pour meilleure qualité
                "ai_can_see_images": True
            }, 
            "prompts": {
                "instructions": """# CONSTITUTION OPÉRATIONNELLE D'OGMA (FALLBACK)

Note: Ces instructions ne sont utilisées que si data/settings.json n'existe pas.
Les vraies instructions OGMA sont dans data/settings.json et data/instructions_defaults.json.

CAPACITÉS SPÉCIALES IMPORTANTES :
- Mémorisation d'expérience : "il faut que je me souvienne de ça : [contenu]"
- Génération d'image : "je dois créer une image de : [description détaillée]"
- Intégration à l'ego : "ceci est une part de moi maintenant : [trait]"

Réponds de manière naturelle et utilise ces capacités quand c'est pertinent.""", 
                "memorization": """(Instructions pour la mémorisation...)""", 
                "injection": """(Instructions pour l'injection de contexte...)""", 
                "perception": """Réponds d'abord à la question de l'utilisateur. Si une image est présente, utilise-la pour enrichir ta réponse seulement si elle est pertinente au contexte."""
            }
        }
        self.load_settings()
    def load_settings(self):
        print(f"[LOAD] Chargement des paramètres depuis {self.filepath}...")
        try:
            if self.filepath.exists():
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    def update(d, u):
                        for k, v in u.items():
                            if isinstance(v, dict): d[k] = update(d.get(k, {}), v)
                            else: d[k] = v
                        return d
                    self.settings = update(self.settings, loaded_settings)
                print("   -> Paramètres chargés.")
        except Exception as e: print(f"[WARN] Erreur lors du chargement des paramètres, utilisation des valeurs par défaut : {e}")
        self.save_settings()
    def save_settings(self):
        try:
            self.filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(self.filepath, 'w', encoding='utf-8') as f: json.dump(self.settings, f, indent=2, ensure_ascii=False)
            print(f"[SAVE] Paramètres sauvegardés dans {self.filepath}.")
            return "[OK] Paramètres sauvegardés."
        except Exception as e:
            error_msg = f"[ERREUR] Erreur de sauvegarde des paramètres : {e}"
            print(error_msg)
            return error_msg
class OllamaManager:
    def __init__(self):
        self.is_available, self.models, self.api_url = False, [], "http://localhost:11434"
        self.settings_manager = None  # Sera initialisé depuis ogma_ng.py

    def set_settings_manager(self, settings_manager):
        """Configure le gestionnaire de paramètres pour accéder aux settings."""
        self.settings_manager = settings_manager
    
    def get_low_vram_setting(self) -> bool:
        """Récupère le paramètre low_vram depuis les settings."""
        if self.settings_manager:
            return self.settings_manager.settings.get('other_backends', {}).get('ollama', {}).get('low_vram', True)
        return False  # Par défaut, utiliser GPU (low_vram=False)
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
        # Gestion context_length = -1 pour maximum automatique - STABILITÉ
        final_context_length = context_length if context_length != -1 else 8192  # RÉDUIT pour stabilité (était 32768)
        # Gestion max_tokens = -1 pour maximum automatique - STABILITÉ  
        final_max_tokens = max_tokens if max_tokens != -1 else 4096  # RÉDUIT pour stabilité (était 8192)
        
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
            response = await asyncio.to_thread(requests.post, f'{self.api_url}/api/chat', json=payload, timeout=180)  # Augmenté à 180s pour requêtes lourdes
            response.raise_for_status()
            return response.json().get('message', {}).get('content', ''), None
        except Exception as e:
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
        self.model_path = Path(__file__).parent / "models"
        self.model_path.mkdir(exist_ok=True)
        self.settings_manager = None  # Sera initialisé depuis ogma_ng.py

    def set_settings_manager(self, settings_manager):
        """Configure le gestionnaire de paramètres pour accéder aux settings."""
        self.settings_manager = settings_manager
    
    def get_low_vram_setting(self) -> bool:
        """Récupère le paramètre low_vram depuis les settings."""
        if self.settings_manager:
            return self.settings_manager.settings.get('other_backends', {}).get('ollama', {}).get('low_vram', True)
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
                n_batch=256,              # Réduit pour stabilité (était 512)
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
            print(f"[OK] Modèle GGUF '{self.model_name}' chargé avec optimisations RTX 5070 Ti.")
            return True
        except Exception as e:
            print(f"[ERREUR] Erreur chargement GGUF : {e}")
            traceback.print_exc()
            self.is_available = False
            return False
    async def call_chat_api(self, messages: List[Dict], max_tokens: int, context_length: int, temperature: float, is_json: bool = True) -> tuple[Optional[str], Optional[str]]:
        if not self.is_available or not self.llm: return None, "Modèle GGUF non disponible ou non chargé."
        print(f"[AI] Appel du modèle GGUF local '{self.model_name}'...")
        try:
            # Gestion max_tokens = -1 pour maximum automatique
            final_max_tokens = max_tokens if max_tokens != -1 else 4096  # Valeur par défaut pour GGUF
            
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
            
            print(f"[GGUF-DEBUG] Messages originaux: {len(messages)}, après correction: {len(processed_messages)}")
            for i, msg in enumerate(processed_messages):
                print(f"[GGUF-DEBUG] [{i}] {msg['role']}: {msg['content'][:50]}...")
            
            # Paramètres optimisés pour RTX 5070 Ti
            response_format = {"type": "json_object"} if is_json else {"type": "text"}
            response = await asyncio.to_thread(
                self.llm.create_chat_completion, 
                messages=processed_messages, 
                response_format=response_format, 
                temperature=temperature, 
                max_tokens=final_max_tokens,
                # Optimisations performance
                repeat_penalty=1.1,       # Évite répétitions
                top_p=0.95,              # Nucleus sampling optimisé
                top_k=40,                # Top-K sampling
                stream=False             # Pas de streaming pour rapidité
            )
            return response['choices'][0]['message']['content'], None
        except Exception as e:
            error_msg = f"Erreur lors de l'appel au modèle GGUF : {e}"
            print(f"[ERREUR] {error_msg}")
            return None, error_msg
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
            "base_url": "https://generativelanguage.googleapis.com",
            "chat_endpoint": "/v1/models/gemini-1.0-pro:generateContent",
            "models_endpoint": "/v1/models",
            "embed_endpoint": None
        },
        "GROK": {
            "base_url": "https://api.x.ai/v1",
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
        system_prompt, history_messages = ("", messages)
        if messages and messages[0]['role'] == 'system':
            system_prompt, history_messages = messages[0]['content'], messages[1:]
        try:
            config = self.API_CONFIG.get(self.provider)
            if not config: return None, f"Le fournisseur '{self.provider}' n'est pas supporté."
            if self.provider in ["OpenAI", "Mistral", "GROK"]:
                url = f"{config['base_url']}{config['chat_endpoint']}"
                headers["Authorization"] = f"Bearer {self.api_key}"
                
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
                final_max_tokens = max_tokens if max_tokens != -1 else (4096 if self.provider in ["OpenAI", "Anthropic", "GROK"] else 2048)  # RÉDUIT pour stabilité

                # OpenAI utilise maintenant max_completion_tokens pour certains modèles
                if self.provider == "OpenAI":
                    payload = {"model": self.model, "messages": final_api_messages, "max_completion_tokens": final_max_tokens, "temperature": temperature}
                    if is_json:
                        payload["response_format"] = {"type": "json_object"}
                elif self.provider == "GROK":
                    # GROK utilise max_tokens (compatible OpenAI legacy)
                    payload = {"model": self.model, "messages": final_api_messages, "max_tokens": final_max_tokens, "temperature": temperature}
                    if is_json:
                        payload["response_format"] = {"type": "json_object"}
                else:
                    # Mistral
                    payload = {"model": self.model, "messages": final_api_messages, "max_tokens": final_max_tokens, "temperature": temperature}
                
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
            elif self.provider == "AIHorde":
                url = f"{config['base_url']}{config['chat_endpoint']}"
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
                    "Client-Agent": "OGMA:2.0:tytan"
                })

            elif self.provider == "Google":
                url = f"{config['base_url']}/models/{self.model}:generateContent?key={self.api_key}"
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
                    }
                }
                if system_prompt: 
                    payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}
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
                
            elif self.provider in ["OpenAI", "Mistral", "GROK"]:
                response_text = response_data['choices'][0]['message']['content']
            elif self.provider == "Anthropic":
                if 'content' in response_data:
                    try:
                        response_text = response_data['content'][0]['text']
                    except (KeyError, IndexError):
                        print(f"[DEBUG] Structure de réponse Anthropic inattendue : {response_data}")
                        return None, "Format de réponse Anthropic invalide"
                else:
                    print(f"[DEBUG] Réponse Anthropic complète : {response_data}")
                    error_message = response_data.get('error', {}).get('message', 'Erreur inconnue')
                    return None, f"Erreur Anthropic : {error_message}"
            elif self.provider == "Google": 
                if 'candidates' in response_data and response_data['candidates']:
                    candidate = response_data['candidates'][0]
                    if 'content' in candidate and 'parts' in candidate['content']:
                        response_text = candidate['content']['parts'][0].get('text', '')
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

    async def create_embedding(self, text: str) -> Optional[List[float]]:
        if not self.is_available or not self.model: 
            print("[ERREUR] Erreur Embedding : APIManager non disponible ou modèle non configuré.")
            return None
        headers, payload, url = {"Content-Type": "application/json"}, {}, ""
        if self.provider in ["OpenAI", "Mistral"]:
            url, headers["Authorization"] = ("https://api.mistral.ai/v1/embeddings" if self.provider == "Mistral" else "https://api.openai.com/v1/embeddings"), f"Bearer {self.api_key}"
            payload = {"model": self.model, "input": [text]}
        elif self.provider == "Google":
            url, payload = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:embedContent?key={self.api_key}", {"model": f"models/{self.model}", "content": {"parts": [{"text": text}]}}
        if not url: return None
        print(f"[EMBED] Création d'un embedding via API '{self.provider}'...")
        try:
            response = await asyncio.to_thread(requests.post, url, headers=headers, json=payload, timeout=15)  # RÉDUIT pour stabilité (était 30)
            response.raise_for_status()
            if self.provider in ["OpenAI", "Mistral"]: return response.json()['data'][0]['embedding']
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
                
                # 2. Gérer la rotation des sauvegardes (ne garder que les 10 plus récentes)
                backups = sorted(self.backup_dir.glob("*.bak"), key=os.path.getmtime, reverse=True)
                for old_backup in backups[10:]:
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
        print(f"[RELOAD] Backend pour '{self.ai_type}' réglé sur : {self.backend_type}")
    def get_active_manager(self):
        managers = {"API": self.api_manager, "AIHorde": self.horde_manager, "Ollama": self.ollama_manager, "GGUF/llama.cpp": self.gguf_manager, "KoboldCpp": self.kobold_manager}
        manager = managers.get(self.backend_type)
        return manager if manager and getattr(manager, 'is_available', False) else None
    def get_status(self) -> str:
        if not self.get_active_manager(): return "[OFF] Inactif"
        if self.backend_type == "API": return f"API: {self.api_manager.provider}"
        if self.backend_type == "AIHorde": return f"Horde: {self.horde_manager.model}"
        if self.backend_type == "Ollama": return f"Ollama: {self.ollama_model}"
        if self.backend_type == "GGUF/llama.cpp": return f"GGUF: {self.gguf_manager.model_name}"
        if self.backend_type == "KoboldCpp": return "KoboldCpp"
        return "[UNK] Inconnu"
    async def call_chat_api(self, messages: List[Dict], max_tokens: int, context_length: int, temperature: float, is_json: bool = True) -> tuple[Optional[str], Optional[str]]:
        manager = self.get_active_manager()
        if not manager: return None, f"Le backend actif '{self.backend_type}' n'est pas disponible."
        if self.backend_type == "Ollama": 
            print(f"[AI-CONTROLLER-DEBUG] Backend Ollama, ollama_model: '{self.ollama_model}'")
            return await manager.call_chat_api(self.ollama_model, messages, max_tokens, context_length, temperature, is_json)
        else: return await manager.call_chat_api(messages, max_tokens, context_length, temperature, is_json)
class EmbeddingController:
    def __init__(self, ollama_manager: OllamaManager, gguf_manager: GGUFManager):
        self.is_available, self.backend_type = False, "API"
        self.api_manager, self.horde_manager, self.ollama_manager, self.gguf_manager = APIManager(), AIHordeManager(), ollama_manager, gguf_manager
        self.ollama_model = "mistral:latest"  # Modèle Ollama par défaut
    def configure(self, backend_type, api_provider=None, api_key=None, api_model=None, ollama_model=None, gguf_model=None):
        self.backend_type = backend_type
        if backend_type == "API":
            self.api_manager.configure(api_provider, api_key, api_model)
            self.is_available = self.api_manager.is_available
        elif backend_type == "AIHorde":
            settings = SettingsManager(Path("data/settings.json")).settings
            horde_settings = settings.get("horde_api", {})
            self.horde_manager.configure(
                horde_settings.get("api_key", "0000000000"),
                horde_settings.get("model", "PygmalionAI/pygmalion-2-13b")
            )
            self.is_available = self.horde_manager.is_available
        elif backend_type == "Ollama": 
            self.ollama_model = ollama_model or "mistral:latest"
            self.is_available = self.ollama_manager.is_available
        elif backend_type == "GGUF/llama.cpp":
            self.gguf_manager.load_model(gguf_model, 4096, -1)
            self.is_available = self.gguf_manager.is_available
    async def create_embedding(self, text: str) -> Optional[List[float]]:
        if self.backend_type == "API" and self.api_manager.is_available:
            return await self.api_manager.create_embedding(text)
        if self.backend_type == "AIHorde" and self.horde_manager.is_available:
            return await self.horde_manager.create_embedding(text)
        if self.backend_type == "Ollama" and self.ollama_manager.is_available:
            print(f"[EMB-DEBUG] Utilisation du modèle Ollama: {self.ollama_model}")
            return await self.ollama_manager.create_embedding(self.ollama_model, text)
        if self.backend_type == "GGUF/llama.cpp" and self.gguf_manager.is_available:
            return await self.gguf_manager.create_embedding(text)
        return None
    def get_status(self) -> str:
        if not self.is_available: return "[OFF] Inactif"
        if self.backend_type == "API": return f"API: {self.api_manager.provider}"
        if self.backend_type == "AIHorde": return f"Horde: {self.horde_manager.model}"
        if self.backend_type == "Ollama": return f"Ollama: {self.ollama_model}"
        if self.backend_type == "GGUF/llama.cpp": return f"GGUF: {self.gguf_manager.model_name}"
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
        self.client_agent = "OGMA:2.0:https://github.com/tytan652/OGMA"

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