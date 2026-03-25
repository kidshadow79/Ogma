"""
Module de génération d'images pour OGMA
=======================================
Gère la génération Text2Img et Image-to-Image (Img2Img).
Extrait de logic_callbacks.py
"""

import re
import json
import base64
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from io import BytesIO
import asyncio

# Variable globale pour l'analyse vision en attente
_pending_vision_analysis = None

# Flag d'interruption boucle corrective i2i
_i2i_stop_requested = False

def get_pending_vision_analysis():
    return _pending_vision_analysis

def clear_pending_vision_analysis():
    global _pending_vision_analysis
    _pending_vision_analysis = None


# ===== FLAG INTERRUPTION BOUCLE CORRECTIVE I2I =====

def request_i2i_stop():
    """Demande l'arret de la boucle corrective i2i en cours."""
    global _i2i_stop_requested
    _i2i_stop_requested = True
    print("[I2I-CORRECT] STOP demande par l'utilisateur")

def reset_i2i_stop():
    """Reinitialise le flag d'arret i2i."""
    global _i2i_stop_requested
    _i2i_stop_requested = False

def is_i2i_stop_requested() -> bool:
    """Verifie si un arret est demande."""
    return _i2i_stop_requested


# ===== HELPER VISION : PREPARATION IMAGE =====

def _prepare_image_for_vision(image_path, target_size: int = 800, log_prefix: str = "[VISION]") -> Optional[str]:
    """
    Prepare une image pour envoi a la Vision API : resize + base64 JPEG.
    
    Factorise le code commun a get_luna_image_feedback() et analyze_i2i_result().
    
    Args:
        image_path: Chemin vers l'image
        target_size: Taille max en pixels (cote le plus long)
        log_prefix: Prefixe pour les logs
    
    Returns:
        str: Image en base64 JPEG, ou None si erreur
    """
    try:
        from PIL import Image
        
        img_path = Path(image_path)
        if not img_path.exists():
            print(f"{log_prefix} Image introuvable : {image_path}")
            return None
        
        with open(img_path, 'rb') as f:
            img = Image.open(f)
            original_size = f"{img.width}x{img.height}"
            
            # Redimensionner en gardant le ratio
            if img.width > target_size or img.height > target_size:
                ratio = min(target_size / img.width, target_size / img.height)
                new_width = int(img.width * ratio)
                new_height = int(img.height * ratio)
                print(f"{log_prefix} Resize {original_size} -> {new_width}x{new_height}")
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            else:
                print(f"{log_prefix} Image {original_size} deja sous {target_size}px")
            
            # Convertir en JPEG qualite 85
            output = BytesIO()
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            img.save(output, format='JPEG', quality=85, optimize=True)
            image_b64 = base64.b64encode(output.getvalue()).decode('utf-8')
            
            estimated_tokens = int((img.width * img.height) / 750)
            b64_size_kb = len(image_b64) / 1024
            print(f"{log_prefix} BASE64 - {b64_size_kb:.1f}KB / {img.width}x{img.height}px / ~{estimated_tokens} tokens")
            
            return image_b64
            
    except Exception as e:
        print(f"{log_prefix} Erreur preparation image: {e}")
        # Fallback: image originale brute
        try:
            with open(image_path, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
        except Exception:
            return None


# ===== ANALYSE STRUCTUREE I2I (JSON) =====

def _parse_i2i_analysis_json(raw_response: str) -> Dict[str, Any]:
    """
    Parse la reponse JSON de l'analyse i2i avec fallbacks robustes.
    
    Strategie :
    1. JSON direct
    2. Extraction JSON depuis markdown (```json ... ```)
    3. Extraction par regex des champs cles
    4. Fallback neutre (score 5)
    
    Returns:
        dict avec au minimum : score, satisfaisant, defauts_detectes, correction_suggeree
    """
    default_result = {
        "score": 5,
        "satisfaisant": False,
        "defauts_detectes": [],
        "elements_bien_preserves": [],
        "prompt_issues": [],
        "correction_suggérée": "",
        "_parse_method": "fallback_neutre"
    }
    
    if not raw_response or not raw_response.strip():
        return default_result
    
    text = raw_response.strip()
    
    # Strategie 1 : JSON direct
    try:
        result = json.loads(text)
        if isinstance(result, dict) and 'score' in result:
            result['_parse_method'] = 'json_direct'
            return _normalize_analysis(result)
    except json.JSONDecodeError:
        pass
    
    # Strategie 2 : Extraire JSON depuis markdown ```json ... ```
    json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?\s*```', text, re.DOTALL)
    if json_match:
        try:
            result = json.loads(json_match.group(1))
            if isinstance(result, dict) and 'score' in result:
                result['_parse_method'] = 'json_markdown'
                return _normalize_analysis(result)
        except json.JSONDecodeError:
            pass
    
    # Strategie 3 : Trouver le premier { ... } dans le texte
    brace_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
    if brace_match:
        try:
            result = json.loads(brace_match.group(0))
            if isinstance(result, dict) and 'score' in result:
                result['_parse_method'] = 'json_brace_extract'
                return _normalize_analysis(result)
        except json.JSONDecodeError:
            pass
    
    # Strategie 4 : Regex extraction des champs cles
    score_match = re.search(r'"score"\s*:\s*(\d+)', text)
    if score_match:
        score = int(score_match.group(1))
        correction_match = re.search(r'"correction_sugg[eé]r[eé]e"\s*:\s*"([^"]*)"', text)
        default_result['score'] = min(max(score, 1), 10)
        default_result['satisfaisant'] = score >= 6
        if correction_match:
            default_result['correction_suggérée'] = correction_match.group(1)
        default_result['_parse_method'] = 'regex_extraction'
        return default_result
    
    # Strategie 5 : Fallback neutre
    print("[I2I-ANALYSIS] Impossible de parser le JSON, fallback neutre (score=5)")
    return default_result


def _normalize_analysis(result: Dict[str, Any]) -> Dict[str, Any]:
    """Normalise et valide les champs de l'analyse."""
    score = result.get('score', 5)
    if isinstance(score, (int, float)):
        result['score'] = min(max(int(score), 1), 10)
    else:
        result['score'] = 5
    
    result['satisfaisant'] = result.get('satisfaisant', result['score'] >= 6)
    result.setdefault('defauts_detectes', [])
    result.setdefault('elements_bien_preserves', [])
    result.setdefault('prompt_issues', [])
    result.setdefault('correction_suggérée', '')
    
    return result


async def analyze_i2i_result(
    image_path,
    chat_controller,
    original_prompt: str,
    settings_manager=None
) -> Dict[str, Any]:
    """
    Analyse structuree (JSON) d'une image i2i generee.
    
    Utilise le prompt d'analyse i2i configurable depuis le frontend.
    Retourne un dict JSON avec score, defauts, correction suggeree.
    
    Args:
        image_path: Chemin de l'image generee
        chat_controller: Controleur IA principale (Vision API)
        original_prompt: Prompt i2i utilise pour la generation
        settings_manager: Pour recuperer le prompt d'analyse configure
    
    Returns:
        dict: Analyse structuree {score, satisfaisant, defauts_detectes, correction_suggeree, ...}
    """
    log_prefix = "[I2I-ANALYSIS]"
    
    try:
        # Preparer image pour vision (1200px pour meilleure detection des details anatomiques)
        image_b64 = _prepare_image_for_vision(image_path, target_size=1200, log_prefix=log_prefix)
        if not image_b64:
            return _parse_i2i_analysis_json("")  # Fallback neutre
        
        # Recuperer le prompt d'analyse depuis settings (priorite frontend)
        img_config = settings_manager.settings.get('image_generation', {}) if settings_manager else {}
        analysis_prompt_template = img_config.get('i2i_analysis_prompt', '').strip()
        
        if not analysis_prompt_template:
            # Fallback prompt minimal si non configure
            analysis_prompt_template = (
                'Analyse cette image modifiee avec le prompt: "{original_prompt}". '
                'Reponds en JSON: {{"score": <1-10>, "satisfaisant": <bool>, '
                '"defauts_detectes": [], "correction_suggérée": ""}}'
            )
        
        # Injecter le prompt original
        analysis_prompt = analysis_prompt_template.replace('{original_prompt}', original_prompt)
        
        # Appel Vision API via IA principale
        messages = [
            {'role': 'user', 'content': [
                {'type': 'text', 'text': analysis_prompt},
                {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{image_b64}'}}
            ]}
        ]
        
        raw_response, err = await chat_controller.call_chat_api(
            messages=messages,
            max_tokens=800,
            context_length=8192,
            temperature=0.3,  # Basse pour analyse factuelle
            is_json=False,
            log_source="i2i_analysis"
        )
        
        if err or not raw_response:
            print(f"{log_prefix} Erreur appel Vision API: {err}")
            return _parse_i2i_analysis_json("")
        
        print(f"{log_prefix} Reponse brute ({len(raw_response)} chars): {raw_response[:120]}...")
        
        # Parser le JSON
        result = _parse_i2i_analysis_json(raw_response)
        
        # FIABILITE: Si le parsing a du utiliser regex_extraction, le JSON etait malformé
        # => plafonner le score a 5 car l'analyse n'est pas fiable
        parse_method = result.get('_parse_method', '?')
        if parse_method == 'regex_extraction' and result.get('score', 5) > 5:
            original_score = result['score']
            result['score'] = 5
            result['satisfaisant'] = False
            print(f"{log_prefix} ⚠️ Score plafonné {original_score}→5 (parsing via {parse_method}, JSON malformé = score non fiable)")
        
        print(f"{log_prefix} Score: {result['score']}/10 | Satisfaisant: {result['satisfaisant']} | "
              f"Defauts: {len(result['defauts_detectes'])} | Parse: {parse_method}")
        
        return result
        
    except Exception as e:
        print(f"{log_prefix} Exception: {e}")
        import traceback
        traceback.print_exc()
        return _parse_i2i_analysis_json("")


async def get_ai_error_feedback(error_message: str, original_prompt: str, chat_controller, generation_type: str = "text2img"):
    """
    Fait commenter l'erreur de génération par l'IA immédiatement.
    
    Args:
        error_message: Message d'erreur retourné par le backend
        original_prompt: Prompt original tenté
        chat_controller: Contrôleur IA pour générer le feedback
        generation_type: "text2img" ou "img2img"
    
    Returns:
        str: Commentaire de l'IA sur l'erreur ou None si échec
    """
    try:
        type_label = "générer" if generation_type == "text2img" else "modifier"
        
        feedback_prompt = f"""Tu viens d'essayer de {type_label} une image avec ce prompt:
\"{original_prompt}\"

Mais ça a échoué avec cette erreur:
{error_message}

En 1-2 phrases max, analyse rapidement ce qui n'a pas marché et comment tu vas t'ajuster pour la prochaine fois. Sois concise et naturelle."""

        messages = [{'role': 'user', 'content': feedback_prompt}]
        
        feedback, err = await chat_controller.call_chat_api(
            messages=messages,
            max_tokens=100,
            context_length=4096,
            temperature=0.7,
            is_json=False,
            log_source="image_error_feedback"
        )
        
        if err or not feedback:
            print(f"[ERROR-FEEDBACK] ❌ Erreur génération feedback: {err}")
            return None
        
        print(f"[ERROR-FEEDBACK] ✅ Commentaire IA: {feedback[:80]}...")
        return feedback.strip()
        
    except Exception as e:
        print(f"[ERROR-FEEDBACK] ❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return None


async def get_luna_image_feedback(image_path, chat_controller, prompt_type="text2img", original_prompt="", settings_manager=None):
    """
    Fait commenter l'image générée par l'IA immédiatement après génération.
    
    Args:
        image_path: Chemin de l'image générée
        chat_controller: Contrôleur IA pour vision
        prompt_type: "text2img" ou "img2img"
        original_prompt: Prompt original pour contexte
        settings_manager: Gestionnaire de paramètres (pour récupérer le prompt vision configuré)
    
    Returns:
        str: Commentaire de l'IA ou None si erreur
    """
    try:
        from pathlib import Path
        if not Path(image_path).exists():
            return None
        
        # Redimensionner à 800px pour bon équilibre détails/coût (~500 tokens)
        # Permet de détecter mains/doigts déformés tout en restant économique
        import base64
        from io import BytesIO
        from PIL import Image
        
        try:
            with open(image_path, 'rb') as f:
                img = Image.open(f)
                original_size = f"{img.width}x{img.height}"
                
                # Redimensionner à max 800px en gardant le ratio
                target_size = 800
                if img.width > target_size or img.height > target_size:
                    ratio = min(target_size / img.width, target_size / img.height)
                    new_width = int(img.width * ratio)
                    new_height = int(img.height * ratio)
                    print(f"[VISION-FEEDBACK] 📐 Resize {original_size} → {new_width}x{new_height}")
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                else:
                    print(f"[VISION-FEEDBACK] 📐 Image {original_size} déjà sous 800px")
                
                # Convertir en JPEG qualité 85 pour économiser tokens
                output = BytesIO()
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                img.save(output, format='JPEG', quality=85, optimize=True)
                image_b64 = base64.b64encode(output.getvalue()).decode('utf-8')
                # Estimation tokens vision plus réaliste (basée sur résolution finale)
                estimated_tokens = int((img.width * img.height) / 750)  # ~750 pixels = 1 token
                b64_size_kb = len(image_b64) / 1024
                print(f"[VISION-FEEDBACK] 📊 BASE64 - {b64_size_kb:.1f}KB / {img.width}x{img.height}px / ~{estimated_tokens} tokens")
                
        except Exception as resize_err:
            # Fallback: image originale si erreur redimensionnement
            print(f"[VISION-FEEDBACK] ⚠️ Erreur resize: {resize_err}, image originale")
            with open(image_path, 'rb') as f:
                image_b64 = base64.b64encode(f.read()).decode('utf-8')
        
        # Récupérer le prompt vision depuis la configuration (prioritaire)
        img_config = settings_manager.settings.get('image_generation', {}) if settings_manager else {}
        configured_prompt = img_config.get('vision_feedback_prompt', '').strip()
        
        # Si un prompt est configuré, l'utiliser, sinon fallback sur le prompt par défaut
        if configured_prompt:
            # Remplacer le placeholder {original_prompt} par le prompt réel
            vision_prompt = configured_prompt.replace('{original_prompt}', original_prompt)
        else:
            # Fallback sur le prompt par défaut (rigueur PIXELS_ONLY)
            if prompt_type == "img2img":
                vision_prompt = f"""Tu viens de modifier une image avec le prompt: "{original_prompt}"

Voici le résultat. En 2-3 phrases max, commente rapidement:
- Est-ce que ça correspond OBJECTIVEMENT à ce que tu voulais faire?
- Y a-t-il des ajustements nécessaires?

RÈGLE: PIXELS_ONLY - Base ton commentaire UNIQUEMENT sur ce que tu vois réellement dans l'image. 
Si l'image ne correspond pas, dis-le. Si l'image ne s'est pas chargée, dis-le.
0_Hallucination, 0_Invention."""
            else:  # text2img
                vision_prompt = f"""Tu viens de créer cette image avec le prompt: "{original_prompt}"

RÈGLE: PIXELS_ONLY - Commente UNIQUEMENT ce que tu vois réellement dans l'image.
Si l'image ne correspond pas au prompt, dis-le clairement.
Si l'image ne s'est pas chargée ou est absente, dis-le.
0_Hallucination, 0_Invention.

En 2-3 phrases max, analyse objective du résultat visible."""
        
        # Appel vision avec l'image
        messages = [
            {'role': 'user', 'content': [
                {'type': 'text', 'text': vision_prompt},
                {'type': 'image_url', 'image_url': {'url': f'data:image/png;base64,{image_b64}'}}
            ]}
        ]
        
        feedback, err = await chat_controller.call_chat_api(
            messages=messages,
            max_tokens=600,  # Augmenté pour permettre analyse complète
            context_length=8192,  # Contexte suffisant pour vision simple
            temperature=0.7,
            is_json=False
        )
        
        if err or not feedback:
            print(f"[VISION-FEEDBACK] ❌ Erreur: {err}")
            return None
        
        print(f"[VISION-FEEDBACK] ✅ Commentaire Luna: {feedback[:80]}...")
        return feedback.strip()
        
    except Exception as e:
        print(f"[VISION-FEEDBACK] ❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return None

async def process_image_generation(response_text: str, settings_manager, text2img_manager) -> str:
    """
    Détecte et traite les demandes de génération d'images dans la réponse de l'IA.
    Remplace la phrase magique par l'image générée via l'extension text2img.
    
    ÉTAPE 1: Détecte les tags <img> orphelins (fichiers inexistants) et extrait le prompt
    ÉTAPE 2: Détecte les phrases magiques text2img classiques
    """
    global _pending_vision_analysis
    
    print(f"[IMAGE-DEBUG] Vérification génération dans : '{response_text[:200]}...'")

    if not settings_manager.settings.get('image_generation', {}).get('enabled', True):
        print("[IMAGE-DEBUG] Génération d'images désactivée")
        return response_text

    # === ÉTAPE 1: Détection tags <img> orphelins (Luna a généré HTML directement) ===
    # Pattern: <img src="/generated/[filename]" ... data-prompt="[prompt]" ... />
    orphan_img_pattern = r'<img\s+src="(/generated/[^"]+)"[^>]*data-prompt="([^"]+)"[^>]*/?>'
    orphan_match = re.search(orphan_img_pattern, response_text, re.IGNORECASE)
    
    if orphan_match:
        image_url = orphan_match.group(1)
        extracted_prompt = orphan_match.group(2)
        
        # Vérifier si le fichier existe réellement
        from pathlib import Path
        filename = image_url.split('/')[-1]
        image_path = Path("data/generated_images") / filename
        
        if not image_path.exists():
            print(f"[IMAGE-ORPHAN] 🔍 Tag <img> orphelin détecté: {filename}")
            print(f"[IMAGE-ORPHAN] 📋 Prompt extrait: '{extracted_prompt[:100]}...'")
            
            # Traiter comme une phrase magique - générer l'image
            try:
                print(f"[IMAGE-ORPHAN] 🎨 Auto-génération depuis tag orphelin...")
                
                image_bytes, error, metadata = await text2img_manager.generate_image(extracted_prompt)
                
                if error:
                    replacement = f"❌ Erreur de génération d'image : {error}"
                    
                    # L'IA commente l'erreur si option activée
                    img_config = settings_manager.settings.get('image_generation', {})
                    ai_can_see = img_config.get('ai_can_see_images', False)
                    if ai_can_see:
                        print(f"[ERROR-FEEDBACK] 🔍 L'IA va analyser l'erreur...")
                        try:
                            from ogma_ng import _ensure_chat_controller
                            chat_ctrl = _ensure_chat_controller()
                            if chat_ctrl:
                                error_feedback = await get_ai_error_feedback(
                                    error_message=error,
                                    original_prompt=extracted_prompt,
                                    chat_controller=chat_ctrl,
                                    generation_type="text2img"
                                )
                                if error_feedback:
                                    replacement += f"\n\n💭 *{error_feedback}*"
                        except Exception as e:
                            print(f"[ERROR-FEEDBACK] ⚠️ Erreur feedback: {e}")
                    
                elif not image_bytes:
                    replacement = "❌ Erreur de génération d'image : aucune image générée"
                else:
                    save_images = settings_manager.settings.get('image_generation', {}).get('save_images', True)
                    
                    if save_images and image_bytes:
                        local_image_path, save_error = text2img_manager.save_image(image_bytes, metadata)
                        if local_image_path:
                            print(f"[IMAGE-ORPHAN] ✅ Image générée et sauvegardée: {local_image_path}")
                            
                            # Remplacer le tag orphelin par le bon tag avec vraie image
                            tooltip_description = extracted_prompt.replace('"', '&quot;').replace("'", "&#39;")
                            import json
                            clean_prompt = json.dumps(extracted_prompt, ensure_ascii=False)[1:-1]
                            new_image_url = f"/generated/{local_image_path.name}"
                            save_info = f" | 💾 {local_image_path.name}"
                            
                            # Stocker pour vision
                            _pending_vision_analysis = local_image_path
                            print(f"[VISION] 👁️ File d'analyse : {local_image_path.name}")
                            
                            replacement = f"""<img src="{new_image_url}" title="🎨 {tooltip_description}{save_info} | 📋 Cliquez pour copier" alt="Image générée" data-prompt="{clean_prompt}" onclick="navigator.clipboard.writeText(this.getAttribute('data-prompt')).then(() => {{ const title = this.title; this.title = '✅ Prompt copié !'; setTimeout(() => this.title = title, 2000); }}).catch(err => alert('Erreur copie: ' + err));" style="max-width: 100%; height: auto; border-radius: 8px; margin: 10px 0; cursor: copy;" />"""
                            
                            # Vision feedback si activé
                            img_config = settings_manager.settings.get('image_generation', {})
                            ai_can_see = img_config.get('ai_can_see_images', False)
                            if ai_can_see:
                                print(f"[VISION-FEEDBACK] 🔍 Luna va analyser son image...")
                                try:
                                    from ogma_ng import _ensure_chat_controller
                                    chat_ctrl = _ensure_chat_controller()
                                    if chat_ctrl:
                                        feedback = await get_luna_image_feedback(
                                            image_path=local_image_path,
                                            chat_controller=chat_ctrl,
                                            prompt_type="text2img",
                                            original_prompt=extracted_prompt,
                                            settings_manager=settings_manager
                                        )
                                        if feedback:
                                            replacement += f"\n\n💭 *{feedback}*"
                                except Exception as e:
                                    print(f"[VISION-FEEDBACK] ⚠️ Erreur feedback: {e}")
                            
                            return response_text.replace(orphan_match.group(0), replacement)
                        else:
                            replacement = f"❌ Erreur sauvegarde: {save_error}"
                    else:
                        replacement = "❌ Erreur: Sauvegarde désactivée"
                
                return response_text.replace(orphan_match.group(0), replacement)
                
            except Exception as e:
                print(f"[IMAGE-ORPHAN] ❌ Erreur traitement: {e}")
                import traceback
                traceback.print_exc()
                replacement = f"❌ Erreur traitement tag orphelin: {e}"
                return response_text.replace(orphan_match.group(0), replacement)
        else:
            print(f"[IMAGE-ORPHAN] ✅ Tag <img> valide (fichier existe)")

    # === ÉTAPE 2: Détection phrases magiques classiques ===
    # Patterns de détection : phrases magiques et variantes naturelles
    # Capture jusqu'à double newline (nouveau paragraphe) ou fin de texte pour avoir la description complète
    patterns = [
        r"je dois créer une image de\s*[:]?\s*(.+?)(?:\n\n|$)",
        r"il faut que je crée une image de\s*[:]?\s*(.+?)(?:\n\n|$)",
        r"je (?:vais|dois) (?:générer|créer) une image de\s*[:]?\s*(.+?)(?:\n\n|$)",
    ]

    image_match = None
    for pattern in patterns:
        image_match = re.search(pattern, response_text, re.IGNORECASE | re.DOTALL)
        if image_match:
            print(f"[IMAGE] 🎨 Détection demande d'image")
            break

    if not image_match:
        return response_text

    # Nettoyer la description : retirer points finaux multiples et whitespace
    image_description = image_match.group(1).strip().rstrip('.')

    if not image_description:
        return response_text

    try:
        print(f"[IMAGE] Génération automatique demandée : '{image_description}'")

        image_bytes, error, metadata = await text2img_manager.generate_image(image_description)

        if error:
            replacement = f"❌ Erreur de génération d'image : {error}"
            
            # L'IA commente l'erreur si option activée
            img_config = settings_manager.settings.get('image_generation', {})
            ai_can_see = img_config.get('ai_can_see_images', False)
            if ai_can_see:
                print(f"[ERROR-FEEDBACK] 🔍 L'IA va analyser l'erreur...")
                try:
                    from ogma_ng import _ensure_chat_controller
                    chat_ctrl = _ensure_chat_controller()
                    if chat_ctrl:
                        error_feedback = await get_ai_error_feedback(
                            error_message=error,
                            original_prompt=image_description,
                            chat_controller=chat_ctrl,
                            generation_type="text2img"
                        )
                        if error_feedback:
                            replacement += f"\n\n💭 *{error_feedback}*"
                except Exception as e:
                    print(f"[ERROR-FEEDBACK] ⚠️ Erreur feedback: {e}")
            
        elif not image_bytes:
            replacement = "❌ Erreur de génération d'image : aucune image générée"
        else:
            local_image_path = None
            save_images = settings_manager.settings.get('image_generation', {}).get('save_images', True)

            # Sauvegarder l'image sur disque (OBLIGATOIRE pour affichage)
            local_image_path = None
            if save_images and image_bytes:
                local_image_path, save_error = text2img_manager.save_image(image_bytes, metadata)
                if local_image_path:
                    print(f"[IMAGE] ✅ Image sauvegardée : {local_image_path}")
                else:
                    print(f"[IMAGE] ❌ Erreur sauvegarde: {save_error}")
            elif not save_images:
                print(f"[IMAGE] ❌ save_images désactivé - impossible d'afficher l'image")

            # Vérifier que l'image a bien été sauvegardée
            if not local_image_path:
                replacement = "❌ Erreur: Image générée mais sauvegarde échouée. Activez 'save_images' dans les paramètres."
                print(f"[IMAGE] ❌ PAS DE FALLBACK BASE64 - Sauvegarde requise pour affichage")
            else:
                # Préparer les métadonnées pour l'affichage
                tooltip_description = image_description.replace('"', '&quot;').replace("'", "&#39;")
                import json
                clean_prompt = json.dumps(image_description, ensure_ascii=False)[1:-1]
                
                # URL directe vers le fichier sauvegardé (servie par /generated route)
                image_url = f"/generated/{local_image_path.name}"
                save_info = f" | 💾 {local_image_path.name}"
                
                # Stocker le chemin pour analyse vision
                _pending_vision_analysis = local_image_path
                print(f"[VISION] 👁️ File d'analyse : {local_image_path.name}")
                print(f"[IMAGE] ⚡ URL directe: {image_url}")
                
                replacement = f"""<img src="{image_url}" title="🎨 {tooltip_description}{save_info} | 📋 Cliquez pour copier" alt="Image générée" data-prompt="{clean_prompt}" onclick="navigator.clipboard.writeText(this.getAttribute('data-prompt')).then(() => {{ const title = this.title; this.title = '✅ Prompt copié !'; setTimeout(() => this.title = title, 2000); }}).catch(err => alert('Erreur copie: ' + err));" style="max-width: 100%; height: auto; border-radius: 8px; margin: 10px 0; cursor: copy;" />"""
                
                # Si Luna peut voir ses créations, ajouter son feedback
                img_config = settings_manager.settings.get('image_generation', {})
                ai_can_see = img_config.get('ai_can_see_images', False)
                if ai_can_see:
                    print(f"[VISION-FEEDBACK] 🔍 Luna va analyser son image...")
                    # Récupérer le chat controller depuis ogma_ng
                    try:
                        from ogma_ng import _ensure_chat_controller
                        chat_ctrl = _ensure_chat_controller()
                        if chat_ctrl:
                            feedback = await get_luna_image_feedback(
                                image_path=local_image_path,
                                chat_controller=chat_ctrl,
                                prompt_type="text2img",
                                original_prompt=image_description,
                                settings_manager=settings_manager
                            )
                            if feedback:
                                replacement += f"\n\n💭 *{feedback}*"
                    except Exception as e:
                        print(f"[VISION-FEEDBACK] ⚠️ Erreur feedback: {e}")

        new_response = response_text.replace(image_match.group(0), replacement)
        print(f"[IMAGE] {'✅ Génération réussie' if not error else '❌ Erreur de génération'}")
        return new_response

    except Exception as e:
        print(f"[ERREUR] Erreur traitement génération d'image : {e}")
        return response_text


# ═══════════════════════════════════════════════════════════════════
# 🔄 BOUCLE AUTO-CORRECTIVE I2I
# ═══════════════════════════════════════════════════════════════════

async def refine_i2i_prompt(
    original_prompt: str,
    analysis: dict,
    chat_controller,
    attempt: int = 1,
    lessons_context: str = "",
    user_intent: str = "",
    previous_attempts: list = None
) -> str:
    """
    Strategie "Tabula Rasa": l'IA recoit l'intention utilisateur + les defauts
    et ecrit un prompt NEUF a chaque tentative (pas d'empilement).
    
    Args:
        original_prompt: Le prompt qui a produit l'image defectueuse
        analysis: Dict d'analyse (score, defauts_detectes, correction_suggeree, etc.)
        chat_controller: Controleur IA principale
        attempt: Numero de tentative (pour contexte)
        lessons_context: Lecons apprises formatees pour injection
        user_intent: L'intention originale de l'utilisateur (le "quoi" sans les details techniques)
        previous_attempts: Historique des tentatives precedentes [{prompt, score, defauts_resume}]
    
    Returns:
        Nouveau prompt complet et propre (en anglais)
    """
    defauts = analysis.get('defauts_detectes', [])
    defauts_text = "\n".join(
        f"- [{d.get('gravite', '?')}] {d.get('type', '?')}: {d.get('description', '?')} (zone: {d.get('zone', '?')})"
        for d in defauts
    ) if defauts else "Aucun defaut structure detecte"
    
    correction_suggeree = analysis.get('correction_suggeree', analysis.get('correction_suggérée', ''))
    score = analysis.get('score', 5)
    
    # Tabula Rasa: on donne l'intention, PAS le prompt precedent en entier
    intent_section = user_intent if user_intent else original_prompt[:300]
    
    # Construire la section historique des tentatives precedentes
    history_section = ""
    if previous_attempts:
        history_lines = []
        for prev in previous_attempts:
            p_prompt = prev.get('prompt', '')[:150]
            p_score = prev.get('score', '?')
            p_defauts = prev.get('defauts_resume', 'inconnu')
            history_lines.append(f"  - Tentative (score {p_score}/10): \"{p_prompt}...\" => Defauts: {p_defauts}")
        history_section = "\nTENTATIVES PRECEDENTES (NE PAS REPETER CES APPROCHES):\n" + "\n".join(history_lines) + "\n"
    
    refinement_prompt = f"""Tu es experte en prompts de modification d'image (img2img).
La tentative {attempt} a produit un resultat insatisfaisant (score {score}/10).

INTENTION ORIGINALE DE L'UTILISATEUR:
{intent_section}
{history_section}
DEFAUTS DETECTES SUR LA DERNIERE IMAGE:
{defauts_text}

CORRECTION SUGGEREE PAR L'ANALYSE:
{correction_suggeree if correction_suggeree else 'Aucune suggestion'}
{f'{chr(10)}{lessons_context}' if lessons_context else ''}
MISSION: Ecris un prompt COMPLET et PROPRE en anglais pour generer l'image correctement.
REGLES CRITIQUES:
- NE REPRENDS PAS le prompt precedent tel quel - ecris-en un NEUF
- Integre des garde-fous explicites contre chaque defaut detecte (ex: "exactly five fingers per hand", "proportional human anatomy")
- Sois CONCIS et TECHNIQUE - max 200 mots
- Chaque instruction doit etre une directive claire pour le modele image
- Ajoute des negatifs implicites au besoin ("without deformation", "no extra limbs")
- Retourne UNIQUEMENT le nouveau prompt, sans explication

NOUVEAU PROMPT:"""
    
    try:
        response, error = await chat_controller.call_chat_api(
            messages=[{'role': 'user', 'content': refinement_prompt}],
            max_tokens=500,
            context_length=8192,
            temperature=0.4,
            is_json=False
        )
        
        if response and not error:
            refined = response.strip().strip('"\'')
            print(f"[I2I-REFINE] Prompt original: {original_prompt[:80]}...")
            print(f"[I2I-REFINE] Prompt corrige:  {refined[:80]}...")
            return refined
        else:
            print(f"[I2I-REFINE] Erreur refinement: {error}, retour prompt original")
            return original_prompt
    except Exception as e:
        print(f"[I2I-REFINE] Exception: {e}, retour prompt original")
        return original_prompt


async def generate_img2img_with_correction(
    modification_description: str,
    source_images_base64: list,
    settings_manager,
    chat_controller,
    img_config: dict,
    on_progress=None,
    web_tips_context: str = ""
) -> dict:
    """
    Boucle auto-corrective pour la generation img2img.
    Genere, analyse, corrige le prompt et reessaie si score insuffisant.
    
    Args:
        modification_description: Prompt de modification (anglais)
        source_images_base64: Liste des images source en base64
        settings_manager: Gestionnaire de parametres
        chat_controller: Controleur IA principale (pour analyse + refinement)
        img_config: Config image_generation depuis settings
        on_progress: Callback optionnel (attempt, max_retries, score, status_msg)
        web_tips_context: Tips web pre-fetches pour ce modele (injectes dans lessons_context)
    
    Returns:
        dict avec:
            - image_bytes: bytes de la meilleure image (ou None)
            - error: message d'erreur éventuel
            - metadata: métadonnées de la meilleure image
            - final_prompt: prompt utilisé pour la meilleure image
            - analysis_history: liste des analyses par tentative
            - prompt_history: liste des prompts par tentative
            - best_score: score de la meilleure image
            - attempts_used: nombre de tentatives effectuées
            - stopped: True si arrêté par l'utilisateur
    """
    max_retries = img_config.get('i2i_max_retries', 3)
    score_threshold = img_config.get('i2i_score_threshold', 6)
    
    # État du meilleur résultat
    best_result = {
        'image_bytes': None,
        'error': None,
        'metadata': None,
        'image_path': None,
        'final_prompt': modification_description,
        'analysis_history': [],
        'prompt_history': [modification_description],
        'best_score': 0,
        'attempts_used': 0,
        'stopped': False
    }
    
    current_prompt = modification_description
    
    # Charger les leçons pertinentes pour enrichir le refinement
    lessons_context = ""
    try:
        from modules.logic.i2i_lessons import get_lessons_manager
        lessons_mgr = get_lessons_manager()
        relevant_lessons = lessons_mgr.find_relevant_lessons(modification_description, max_results=3)
        if relevant_lessons:
            lessons_context = lessons_mgr.format_lessons_for_injection(relevant_lessons)
            print(f"[I2I-LOOP] {len(relevant_lessons)} lecon(s) pertinente(s) injectee(s)")
            # Marquer comme appliquées
            for lesson in relevant_lessons:
                lessons_mgr.mark_lesson_applied(lesson['id'])
    except Exception as lesson_err:
        print(f"[I2I-LOOP] Erreur chargement lecons: {lesson_err}")
    
    # Injecter les tips web dans le contexte de lecons
    if web_tips_context:
        img2img_model = img_config.get('img2img_model', 'flux-2/pro-image-to-image')
        lessons_context += f"\n\nTIPS SPECIFIQUES AU MODELE ({img2img_model}):\n{web_tips_context}"
        print(f"[I2I-LOOP] Tips web injectes dans lessons_context")
    
    # Backend i2i
    from extensions.text2img.image_backend import get_image_backend
    backend = get_image_backend(settings_manager)
    if not backend:
        best_result['error'] = "Backend de generation d'images non initialise."
        return best_result
    
    img2img_model = img_config.get('img2img_model', 'flux-2/pro-image-to-image')
    img2img_provider = img_config.get('img2img_provider', 'Kie')
    
    for attempt in range(1, max_retries + 1):
        # Vérifier flag STOP
        if is_i2i_stop_requested():
            print(f"[I2I-LOOP] STOP demande par l'utilisateur a la tentative {attempt}")
            best_result['stopped'] = True
            break
        
        print(f"[I2I-LOOP] === Tentative {attempt}/{max_retries} ===")
        print(f"[I2I-LOOP] Prompt: {current_prompt[:100]}...")
        
        if on_progress:
            try:
                result = on_progress(attempt, max_retries, best_result['best_score'], f"Generation tentative {attempt}/{max_retries}...")
                if asyncio.iscoroutine(result):
                    await result
                else:
                    await asyncio.sleep(0.1)
            except Exception as e:
                print(f"[I2I-LOOP] on_progress error (gen): {e}")
        
        # --- GÉNÉRATION ---
        try:
            # Déterminer width/height selon le provider
            if img2img_provider == 'AtlasCloud':
                _atlas_size = img_config.get('atlas_i2i_size', '1024*1024')
                _atlas_parts = _atlas_size.split('*')
                _i2i_width = int(_atlas_parts[0]) if len(_atlas_parts) == 2 else 1024
                _i2i_height = int(_atlas_parts[1]) if len(_atlas_parts) == 2 else 1024
                _i2i_strength = img_config.get('atlas_i2i_strength', 0.75)
                _i2i_negative = img_config.get('atlas_i2i_negative', 'blurry, ugly, deformed')
                _i2i_seed = img_config.get('atlas_i2i_seed', -1)
            else:
                _i2i_width = img_config.get('width', 1024)
                _i2i_height = img_config.get('height', 1024)
                _i2i_strength = img_config.get('img2img_strength', 0.8)
                _i2i_negative = img_config.get('img2img_negative', 'blurry, ugly')
                _i2i_seed = None

            image_bytes, error, metadata = await backend.generate_img2img(
                prompt=current_prompt,
                source_images_base64=source_images_base64,
                provider=img2img_provider,
                model=img2img_model,
                width=_i2i_width,
                height=_i2i_height,
                size=img_config.get('img2img_size', '2048*2048'),
                aspect_ratio=img_config.get('img2img_aspect_ratio', '1:1'),
                quality=img_config.get('img2img_quality', 'basic'),
                image_size=img_config.get('img2img_image_size', 'square_hd'),
                image_resolution=img_config.get('img2img_image_resolution', '1K'),
                resolution=img_config.get('img2img_resolution', '1K'),
                max_images_output=img_config.get('img2img_max_images', 1),
                output_format=img_config.get('img2img_output_format', 'jpeg'),
                strength=_i2i_strength,
                enable_safety_checker=img_config.get('img2img_safety', True),
                num_inference_steps=img_config.get('img2img_steps', 30),
                guidance_scale=img_config.get('img2img_guidance', 2.5),
                negative_prompt=_i2i_negative,
                seed=_i2i_seed,
                acceleration='none'
            )
        except Exception as gen_err:
            print(f"[I2I-LOOP] Exception generation tentative {attempt}: {gen_err}")
            error = str(gen_err)
            image_bytes = None
            metadata = None
        
        best_result['attempts_used'] = attempt
        
        if error or not image_bytes:
            print(f"[I2I-LOOP] Echec generation tentative {attempt}: {error}")
            best_result['analysis_history'].append({
                'attempt': attempt,
                'prompt': current_prompt,
                'error': error,
                'score': 0
            })
            # Pas de retry sur erreur backend (rate limit, etc.) - arrêter
            best_result['error'] = error
            break
        
        # --- SAUVEGARDE TEMPORAIRE pour analyse ---
        temp_path = None
        try:
            from extensions.text2img import get_text2img_manager
            text2img_mgr = get_text2img_manager()
            if text2img_mgr:
                temp_path, save_err = text2img_mgr.save_image(image_bytes, metadata)
                if temp_path:
                    print(f"[I2I-LOOP] Image tentative {attempt} sauvegardee: {temp_path}")
                else:
                    print(f"[I2I-LOOP] Erreur sauvegarde tentative {attempt}: {save_err}")
        except Exception as save_e:
            print(f"[I2I-LOOP] Exception sauvegarde: {save_e}")
        
        # --- ANALYSE ---
        analysis = await analyze_i2i_result(
            image_path=temp_path,
            chat_controller=chat_controller,
            original_prompt=current_prompt,
            settings_manager=settings_manager
        )
        
        score = analysis.get('score', 5)
        satisfaisant = analysis.get('satisfaisant', score >= score_threshold)
        
        print(f"[I2I-LOOP] Score tentative {attempt}: {score}/10 (seuil: {score_threshold})")
        
        analysis['attempt'] = attempt
        analysis['prompt'] = current_prompt
        best_result['analysis_history'].append(analysis)
        
        if on_progress:
            try:
                defauts = analysis.get('defauts_detectes', [])
                defauts_types = ", ".join(f"{d.get('type','?')} ({d.get('gravite','?')})" for d in defauts[:4])
                status = f"Score: {score}/10" + (f" | {defauts_types}" if defauts_types else " - OK")
                result = on_progress(attempt, max_retries, score, status)
                if asyncio.iscoroutine(result):
                    await result
                else:
                    await asyncio.sleep(0.1)
            except Exception as e:
                print(f"[I2I-LOOP] on_progress error (analysis): {e}")
        
        # Mettre à jour le meilleur résultat si ce score est le plus haut
        if score > best_result['best_score']:
            best_result['best_score'] = score
            best_result['image_bytes'] = image_bytes
            best_result['metadata'] = metadata
            best_result['image_path'] = temp_path
            best_result['final_prompt'] = current_prompt
            best_result['error'] = None
            print(f"[I2I-LOOP] Nouveau meilleur resultat: score {score}")
        
        # --- DÉCISION: satisfaisant ou retry ? ---
        if satisfaisant or score >= score_threshold:
            print(f"[I2I-LOOP] Score {score} >= seuil {score_threshold} - Resultat accepte!")
            break
        
        if attempt >= max_retries:
            print(f"[I2I-LOOP] Max retries atteint ({max_retries}) - Retour meilleur resultat (score {best_result['best_score']})")
            break
        
        # Vérifier flag STOP avant refinement
        if is_i2i_stop_requested():
            print(f"[I2I-LOOP] STOP demande avant refinement")
            best_result['stopped'] = True
            break
        
        # --- REFINEMENT DU PROMPT ---
        print(f"[I2I-LOOP] Score {score} < seuil {score_threshold} - Refinement du prompt...")
        
        if on_progress:
            try:
                result = on_progress(attempt, max_retries, score, f"Correction du prompt (tentative {attempt+1})...")
                if asyncio.iscoroutine(result):
                    await result
                else:
                    await asyncio.sleep(0.1)
            except Exception as e:
                print(f"[I2I-LOOP] on_progress error (refine-start): {e}")
        
        # Construire l'historique des tentatives pour que l'IA ne repete pas les memes erreurs
        prev_attempts = []
        for hist_a in best_result['analysis_history']:
            defauts_list = hist_a.get('defauts_detectes', [])
            defauts_resume = ", ".join(
                f"{d.get('type','?')} ({d.get('gravite','?')})"
                for d in defauts_list[:5]
            ) if defauts_list else hist_a.get('error', 'generation echouee')
            prev_attempts.append({
                'prompt': hist_a.get('prompt', ''),
                'score': hist_a.get('score', 0),
                'defauts_resume': defauts_resume
            })
        
        current_prompt = await refine_i2i_prompt(
            original_prompt=current_prompt,
            analysis=analysis,
            chat_controller=chat_controller,
            attempt=attempt,
            lessons_context=lessons_context,
            user_intent=modification_description,  # Tabula Rasa: toujours l'intention originale
            previous_attempts=prev_attempts  # Historique complet des tentatives
        )
        best_result['prompt_history'].append(current_prompt)
        
        # Notifier le nouveau prompt apres refinement
        if on_progress:
            try:
                prompt_preview = current_prompt[:100].replace('\n', ' ')
                result = on_progress(attempt + 1, max_retries, score, f"Nouveau prompt: {prompt_preview}...")
                if asyncio.iscoroutine(result):
                    await result
                else:
                    await asyncio.sleep(0.1)
            except Exception as e:
                print(f"[I2I-LOOP] on_progress error (refine-done): {e}")
    
    # Reset du flag stop
    reset_i2i_stop()
    
    print(f"[I2I-LOOP] === RÉSULTAT FINAL ===")
    print(f"[I2I-LOOP] Tentatives: {best_result['attempts_used']}/{max_retries}")
    print(f"[I2I-LOOP] Meilleur score: {best_result['best_score']}/10")
    print(f"[I2I-LOOP] Prompt final: {best_result['final_prompt'][:80]}...")
    print(f"[I2I-LOOP] Stoppe: {best_result['stopped']}")
    
    # --- EXTRACTION DES LEÇONS ---
    if best_result['attempts_used'] > 1 and best_result['best_score'] > 0:
        try:
            from modules.logic.i2i_lessons import get_lessons_manager
            lessons_mgr = get_lessons_manager()
            lesson_ids = lessons_mgr.store_lessons_from_correction(
                analysis_history=best_result['analysis_history'],
                prompt_history=best_result['prompt_history']
            )
            best_result['lesson_ids'] = lesson_ids
            
            # --- PROPOSITION AUTO DE MISE À JOUR DU GUIDE ---
            if lessons_mgr.should_propose_guide_update():
                try:
                    current_guide = img_config.get('img2img_guide', '')
                    proposal = await lessons_mgr.generate_guide_proposal(
                        chat_controller=chat_controller,
                        current_guide=current_guide
                    )
                    if proposal:
                        best_result['guide_proposal'] = proposal
                        print(f"[I2I-LOOP] Proposition guide #{proposal['id']} generee")
                except Exception as guide_err:
                    print(f"[I2I-LOOP] Erreur proposition guide: {guide_err}")
                    
        except Exception as lesson_err:
            print(f"[I2I-LOOP] Erreur stockage lecons: {lesson_err}")
            best_result['lesson_ids'] = []
    
    return best_result


def _extract_prompt_for_display(raw_prompt: str) -> str:
    """
    Extrait le prompt réel depuis le texte de modification.
    Retire les wrappers français/anglais générés par la vision IA :
      - "Il faut que je modifie cette image :\n**\"...\"**"
      - "I need to modify this image:\n\n**Full prompt in English:**\n\"...\""
    pour ne garder que le prompt sémantique cliquable.
    """
    import re as _rp
    # Cas 1 (EN): "**Full prompt in English:**\n\"<prompt>\"" ou similaire
    m = _rp.search(r'\*\*Full prompt in English[^*]*\*\*\s*[:\n]+\s*"(.*?)(?:"\s*$|"\s*\*\*|$)', raw_prompt, _rp.DOTALL | _rp.IGNORECASE)
    if m:
        return m.group(1).strip().rstrip('"').strip()
    # Cas 2 (FR/EN): contenu entre **"..."** (format commun)
    m = _rp.search(r'\*\*"(.*?)"\*\*', raw_prompt, _rp.DOTALL)
    if m:
        return m.group(1).strip()
    # Cas 3: contenu entre **"...** sans guillemet fermant
    m = _rp.search(r'\*\*"(.*?)\*\*', raw_prompt, _rp.DOTALL)
    if m:
        return m.group(1).strip().rstrip('"').strip()
    # Cas 4: retirer le préfixe français ou anglais courant
    cleaned = _rp.sub(
        r'^(?:Il faut que je modifie cette image|Je dois créer une image de|'
        r'Je dois modifier cette image|Il faut que je crée une image de|'
        r'I need to modify this image|I must modify this image|'
        r'I need to create an image of|I must create an image of)'
        r'\s*[:\-]?\s*(?:\*\*[^*]*\*\*\s*)?[:\n]+\s*"?\s*',
        '', raw_prompt.strip(), flags=_rp.IGNORECASE | _rp.DOTALL
    )
    if cleaned != raw_prompt.strip():
        return _rp.sub(r'"?\*\*\s*$', '', cleaned).strip().strip('"')
    return raw_prompt


async def process_img2img_generation(response_text: str, settings_manager, active_file_data: dict = None, active_images: list = None, perception_image_data: dict = None, representation_images: list = None, override_prompt: str = None) -> str:
    """
    Détecte et traite les demandes de modification d'images (Image-to-Image).
    
    Args:
        response_text: Texte de la réponse IA
        settings_manager: Gestionnaire de paramètres
        active_file_data: Fichier uploadé (legacy)
        active_images: Liste d'images uploadées (multi-image)
        perception_image_data: Image webcam capturée (format {"type": "image_url", "image_url": {"url": "data:..."}})
        representation_images: Images avatar User/IA HD (séparées de active_images)
        override_prompt: Prompt direct (bypass regex extraction) - utilisé quand le prompt a été composé par le modèle vision en amont
    """
    global _pending_vision_analysis
    
    # Comptage des images disponibles
    images_list = active_images.copy() if active_images else []
    if not images_list and active_file_data and active_file_data.get('type') == 'image':
        images_list = [active_file_data]
    
    # 🎥 NOUVEAU: Ajouter l'image perception/webcam si disponible
    if perception_image_data:
        try:
            # Extraire la base64 de l'image perception
            perception_url = perception_image_data.get('image_url', {}).get('url', '')
            if perception_url.startswith('data:image'):
                # Format: data:image/jpeg;base64,XXXXX
                perception_b64 = perception_url.split(',', 1)[1] if ',' in perception_url else ''
                
                if perception_b64:
                    perception_entry = {
                        'type': 'image',
                        'name': 'webcam_perception.jpg',
                        'data': perception_b64,
                        'source': 'perception_webcam'
                    }
                    images_list.append(perception_entry)
                    print(f"[IMG2IMG] 🎥 Image perception ajoutée ({len(perception_b64)//1000}KB)")
        except Exception as e:
            print(f"[IMG2IMG] ⚠️ Erreur extraction image perception: {e}")
    
    # 🎭 NOUVEAU: Ajouter les avatars HD (User/IA) si fournis
    if representation_images:
        for repr_img in representation_images:
            images_list.append(repr_img)
        print(f"[IMG2IMG] 🎭 {len(representation_images)} avatar(s) HD ajouté(s) pour img2img")
    
    # Fallback: Si toujours aucune image, vérifier dernière capture sur disque
    if not images_list:
        try:
            # Vérifier si l'extension perception est active
            from extensions.perception_ui import get_perception_ui
            perception_ui = get_perception_ui()
            
            if perception_ui and perception_ui.is_enabled and perception_ui.perception_agent:
                print("[IMG2IMG] 🎥 Extension perception active - recherche dernière capture...")
                
                from pathlib import Path
                captures_dir = Path("captures")
                if captures_dir.exists():
                    # Trouver l'image la plus récente
                    image_files = sorted(
                        [f for f in captures_dir.iterdir() if f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.webp']],
                        key=lambda x: x.stat().st_mtime,
                        reverse=True
                    )
                    if image_files:
                        latest_capture = image_files[0]
                        print(f"[IMG2IMG] 📸 Utilisation dernière capture webcam: {latest_capture.name}")
                        
                        # Charger l'image en base64
                        import base64
                        with open(latest_capture, 'rb') as f:
                            img_bytes = f.read()
                            b64_data = base64.b64encode(img_bytes).decode('utf-8')
                            images_list = [{
                                'type': 'image',
                                'name': latest_capture.name,
                                'data': b64_data,
                                'source': 'webcam_capture'
                            }]
            else:
                print("[IMG2IMG] ⚪ Extension perception non active - skip captures webcam")
                
        except Exception as e:
            print(f"[IMG2IMG] ⚠️ Erreur vérification perception/captures: {e}")
    
    print(f"[IMG2IMG-DEBUG] 🚀 Fonction appelée - {len(images_list)} image(s) disponible(s)")
    
    # Log des sources d'images
    for i, img in enumerate(images_list):
        source = img.get('source', 'uploaded')
        name = img.get('name', img.get('filename', f'image_{i}'))
        print(f"[IMG2IMG-DEBUG]   Image {i+1}: {name} (source: {source})")

    img_config = settings_manager.settings.get('image_generation', {})
    if not img_config.get('img2img_enabled', False):
        print("[IMG2IMG-DEBUG] Image-to-Image désactivé")
        return response_text

    patterns = [
        r"🔄\s*\*\*image modifiée\s*:\*\*\s*\"(.+?)\"",
        r"🔄\s*\*\*image modifiée\s*:\*\*\s*(.+?)(?:\n\n|$)",
        r"🔄\s*\*\*image corrigée\s*:\*\*\s*\"(.+?)\"",
        r"🔄\s*\*\*image corrigée\s*:\*\*\s*(.+?)(?:\n\n|$)",
        r"🔄\s*image modifiée\s*[:]\s*\"(.+?)\"",
        r"🔄\s*image modifiée\s*[:]\s*(.+?)(?:\n\n|$)",
        r"🔄\s*image corrigée\s*[:]\s*\"(.+?)\"",
        r"🔄\s*image corrigée\s*[:]\s*(.+?)(?:\n\n|$)",
        # Variantes markdown : OGMA entoure parfois le prompt de **gras** ou *italique*
        r"je dois modifier cette image\s*[:]\s*\*{0,2}\s*(.+?)\s*\*{0,2}\s*(?:\n\n|$)",
        r"il faut que je modifie cette image\s*[:]\s*\*{0,2}\s*(.+?)\s*\*{0,2}\s*(?:\n\n|$)",
        r"je (?:vais|dois) (?:transformer|modifier|éditer) cette image\s*[:]\s*\*{0,2}\s*(.+?)\s*\*{0,2}\s*(?:\n\n|$)",
        r"image modifiée\s*[:]\s*\*{0,2}\s*(.+?)\s*\*{0,2}\s*(?:\n\n|$)",
        r"image corrigée\s*[:]\s*\*{0,2}\s*(.+?)\s*\*{0,2}\s*(?:\n\n|$)",
    ]
    
    img2img_match = None
    for i, pattern in enumerate(patterns):
        img2img_match = re.search(pattern, response_text, re.IGNORECASE | re.DOTALL)
        if img2img_match:
            print(f"[IMG2IMG] 🔄 Détection demande de modification d'image (Pattern #{i+1})")
            break

    if not img2img_match:
        return response_text

    modification_description = img2img_match.group(1).strip()
    modification_description = modification_description.strip('"\'').strip()
    modification_description = modification_description.lstrip('*').rstrip('*').strip()

    # 🎯 OVERRIDE DIRECT: Si un prompt a été passé directement (composé par vision en amont),
    # l'utiliser au lieu du résultat fragile de l'extraction regex.
    # Cela règle définitivement le problème de troncature par \n\n.
    if override_prompt:
        print(f"[IMG2IMG] 🎯 Override prompt direct ({len(override_prompt)} chars) - bypass extraction regex")
        modification_description = override_prompt.strip()

    # Fallback: si le contenu capturé est vide après stripping (ex: OGMA a mis la description
    # sur la ligne suivante ou entre balises markdown **: on élargit la capture),
    if not modification_description:
        # Tenter de capturer le bloc de texte qui suit la phrase magique sur les lignes suivantes
        start_pos = img2img_match.end()
        # Chercher jusqu'au prochain paragraphe vide ou fin de texte
        rest = response_text[start_pos:]
        # Prendre les 500 premiers chars non vides
        fallback_lines = [l.strip().strip('*').strip() for l in rest.split('\n') if l.strip().strip('*').strip()]
        modification_description = ' '.join(fallback_lines[:3])  # Max 3 lignes
        if modification_description:
            print(f"[IMG2IMG] ⚠️ Description vide après extraction directe - fallback multi-ligne utilisé: {modification_description[:80]}...")
        else:
            print(f"[IMG2IMG] ❌ Description vide pour Pattern #{i+1} (raw='{img2img_match.group(1)[:50]}')")
            return response_text

    if not modification_description:
        print(f"[IMG2IMG] ❌ Description toujours vide après fallback - abandon")
        return response_text
    
    # 🌍 AUTO-TRADUCTION: Forcer anglais si Luna a oublié
    # Seedream attend de l'anglais - détection rapide et traduction via Archiviste
    def is_mostly_french(text: str) -> bool:
        """Détection heuristique rapide français vs anglais"""
        french_indicators = ['garde', 'ajoute', 'supprime', 'change', 'avec', 'pour', 'dans', 'sur', 'une', 'des', 'les', 'la', 'le']
        english_indicators = ['keep', 'add', 'remove', 'change', 'with', 'for', 'in', 'on', 'the', 'a', 'an']
        
        text_lower = text.lower()
        french_count = sum(1 for word in french_indicators if f' {word} ' in f' {text_lower} ')
        english_count = sum(1 for word in english_indicators if f' {word} ' in f' {text_lower} ')
        
        # Si plus de 3 mots français et ratio > 2:1, c'est probablement du français
        return french_count >= 3 and french_count > english_count * 2
    
    # Vérifier si traduction auto activée dans settings
    img_config = settings_manager.settings.get('image_generation', {})
    auto_translate = img_config.get('img2img_auto_translate', True)
    
    if auto_translate and is_mostly_french(modification_description):
        print(f"[IMG2IMG] 🇫🇷 Prompt français détecté - traduction auto en anglais...")
        try:
            # Utiliser l'Archiviste pour traduction précise (rapide, ~200ms)
            from ogma_ng import _ensure_archiviste_controller
            archiviste = _ensure_archiviste_controller()
            
            if archiviste:
                # Prompt de traduction SANS labels PROMPT:/ENGLISH TRANSLATION: pour éviter l'écho LLM
                translation_prompt = f"""Translate the following image modification instruction from French to English.
Rules: keep exact structure, translate French words only, keep English technical terms, return ONLY the translation.

{modification_description}"""
                
                translated, err = await archiviste.call_chat_api(
                    messages=[{'role': 'user', 'content': translation_prompt}],
                    max_tokens=1024,
                    context_length=4096,
                    temperature=0.1,
                    is_json=False
                )
                
                if translated and not err:
                    translated_stripped = translated.strip()
                    
                    # 🧹 Nettoyage artefacts LLM: supprimer préfixes/labels parasites
                    import re as _re_translate
                    # Supprimer "PROMPT:", "ENGLISH TRANSLATION:", "Translation:", "Here is the translation:" etc.
                    translated_stripped = _re_translate.sub(
                        r'^(?:PROMPT|ENGLISH TRANSLATION|TRANSLATION|HERE IS THE TRANSLATION|TRANSLATED TEXT)\s*:\s*\n?',
                        '', translated_stripped, flags=_re_translate.IGNORECASE
                    ).strip()
                    # Supprimer guillemets/backticks englobants
                    if (translated_stripped.startswith('"') and translated_stripped.endswith('"')) or \
                       (translated_stripped.startswith('`') and translated_stripped.endswith('`')):
                        translated_stripped = translated_stripped[1:-1].strip()
                    
                    # Vérifier que la traduction n'est pas tronquée (filtre contenu)
                    original_len = len(modification_description)
                    translated_len = len(translated_stripped)
                    ends_with_punct = translated_stripped.rstrip().endswith(('.', '!', '?', '"', "'", ']', ')'))
                    
                    # Détection troncature améliorée:
                    # 1. Fin sans ponctuation ET texte > 50 chars → probablement tronqué
                    # 2. Fin sur préposition/article anglais courant → clairement coupé
                    truncated_endings = ('of', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'with', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 'be', 'by', 'from', 'that', 'this', 'it')
                    last_word = translated_stripped.rstrip().split()[-1].lower() if translated_stripped.strip() else ''
                    ends_on_preposition = last_word in truncated_endings
                    
                    seems_truncated = (not ends_with_punct and translated_len > 50) or ends_on_preposition
                    
                    if seems_truncated:
                        print(f"[IMG2IMG] ⚠️ Traduction tronquée détectée ({translated_len} chars, finit par '{last_word}') - prompt original conservé")
                        print(f"[IMG2IMG] ⚠️ Traduction rejetée: '{translated_stripped[:150]}...'")
                    else:
                        modification_description = translated_stripped
                        print(f"[IMG2IMG] ✅ Traduction: {modification_description[:100]}...")
                else:
                    print(f"[IMG2IMG] ⚠️ Erreur traduction: {err}, utilisation prompt original")
            else:
                print(f"[IMG2IMG] ⚠️ Archiviste indisponible pour traduction, prompt français conservé")
        except Exception as trans_err:
            print(f"[IMG2IMG] ⚠️ Exception traduction: {trans_err}, prompt original conservé")
    else:
        print(f"[IMG2IMG] ✅ Prompt anglais détecté - pas de traduction nécessaire")

    if not images_list:
        error_msg = "❌ Aucune image uploadée pour la modification. Uploadez d'abord une image."
        return response_text.replace(img2img_match.group(0), error_msg)
    
    # 🧹 NETTOYAGE: Supprimer tous les tags <img> corrompus générés par Luna avant traitement
    # Problème: Luna parfois génère des tags <img src="/generated/fichier.pnng"> avec timestamps/extensions incorrects
    # Ces tags orphelins provoquent des "❌ Image non disponible" même si l'image réelle est affichée
    import re as re_clean
    orphan_img_pattern = r'<img\s+src="/generated/[^"]+"\s*[^>]*/?>'
    orphan_tags = re_clean.findall(orphan_img_pattern, response_text)
    if orphan_tags:
        print(f"[IMG2IMG] 🧹 Suppression de {len(orphan_tags)} tag(s) <img> orphelin(s) généré(s) par Luna")
        for tag in orphan_tags:
            response_text = response_text.replace(tag, '')  # Supprimer complètement
    
    source_images_base64 = []
    for img_data in images_list:
        b64 = img_data.get('data', '')
        if b64:
            source_images_base64.append(b64)
    
    if not source_images_base64:
        error_msg = "❌ Images sources invalides ou corrompues."
        return response_text.replace(img2img_match.group(0), error_msg)
    
    # Info: taille des images (l'auto-upscale est géré par WaveSpeed provider si nécessaire)
    try:
        from PIL import Image
        from io import BytesIO
        import base64 as b64_module
        for idx, b64_data in enumerate(source_images_base64):
            img_bytes = b64_module.b64decode(b64_data)
            img = Image.open(BytesIO(img_bytes))
            total_pixels = img.width * img.height
            print(f"[IMG2IMG] 📐 Image {idx+1}: {img.width}x{img.height} = {total_pixels:,} pixels")
    except Exception as diag_err:
        print(f"[IMG2IMG] ⚠️ Diagnostic taille échoué: {diag_err}")
    
    try:
        print(f"[IMG2IMG] 🔄 Modification demandée : '{modification_description}'")
        img2img_model = img_config.get('img2img_model', 'flux-2/pro-image-to-image')
        img2img_provider = img_config.get('img2img_provider', 'Kie')  # Lire le provider depuis settings
        
        from extensions.text2img.image_backend import get_image_backend
        backend = get_image_backend(settings_manager)
        
        if not backend:
            error_msg = "❌ Backend de génération d'images non initialisé."
            return response_text.replace(img2img_match.group(0), error_msg)
        
        print(f"[IMG2IMG] Provider: {img2img_provider}, Modèle: {img2img_model}")
        
        # ═══════════════════════════════════════════════════
        # 🌐 TIPS WEB: Fetch unique par modele (cache en DB)
        # ═══════════════════════════════════════════════════
        web_tips_context = ""
        web_tips_enabled = img_config.get('i2i_web_tips_enabled', True)
        if web_tips_enabled:
            try:
                from modules.logic.i2i_lessons import get_lessons_manager
                lessons_mgr = get_lessons_manager()
                
                # Recuperer chat_controller pour la synthese web si necessaire
                try:
                    from ogma_ng import _ensure_chat_controller
                    _tips_ctrl = _ensure_chat_controller()
                except Exception:
                    _tips_ctrl = None
                
                tips_result = await lessons_mgr.fetch_model_tips(
                    model_name=img2img_model,
                    provider=img2img_provider,
                    chat_controller=_tips_ctrl
                )
                if tips_result.get('success'):
                    cached_str = " (cache)" if tips_result.get('cached') else ""
                    print(f"[IMG2IMG] {tips_result['tips_count']} tips web{cached_str} pour {img2img_model}")
                    web_tips = lessons_mgr.get_web_tips_for_model(img2img_model)
                    if web_tips:
                        web_tips_context = "\n".join(
                            f"- [{t['type'].replace('web_tip_','')}] {t['conseil']}" +
                            (f" | Ex: {t['exemple'][:80]}" if t['exemple'] and t['exemple'] != t['conseil'] else "")
                            for t in web_tips[:5]
                        )
            except Exception as tips_err:
                print(f"[IMG2IMG] Erreur fetch tips web: {tips_err}")
        
        # ═══════════════════════════════════════════════════
        # 🎲 BATCH MODE: Génération multiple avec seeds incrémentaux
        # ═══════════════════════════════════════════════════
        batch_count = img_config.get('img2img_batch_count', 1)
        batch_seed = img_config.get('img2img_batch_seed', -1)
        seed_increment = img_config.get('img2img_seed_increment', 1)
        
        # Le batch mode est disponible pour tous les modèles qui supportent seed
        supports_seed = backend.model_supports_seed(img2img_provider, img2img_model)
        
        if batch_count > 1 and supports_seed:
            print(f"[IMG2IMG] 🎲 MODE BATCH: {batch_count} images (seed={batch_seed}, increment=+{seed_increment})")
            
            # Appeler le backend batch
            images_bytes_list, errors_list, batch_metadata = await backend.generate_img2img_batch(
                prompt=modification_description,
                source_images_base64=source_images_base64,
                provider=img2img_provider,
                model=img2img_model,
                batch_count=batch_count,
                base_seed=batch_seed,
                seed_increment=seed_increment,
                size=img_config.get('img2img_size', '2048*2048'),
                output_format=img_config.get('img2img_output_format', 'jpeg'),
            )
            
            if not images_bytes_list and errors_list:
                error_str = "; ".join(errors_list[:3])
                replacement = f"❌ Erreur batch: {error_str}"
            elif not images_bytes_list:
                replacement = "❌ Erreur batch: aucune image générée"
            else:
                # Sauvegarder toutes les images et construire la grille HTML
                saved_paths = []
                save_images = img_config.get('save_images', True)
                
                if save_images:
                    try:
                        from extensions.text2img import get_text2img_manager
                        text2img_mgr = get_text2img_manager()
                        
                        for idx, img_bytes in enumerate(images_bytes_list):
                            # Métadonnées par image
                            img_meta = {
                                "provider": img2img_provider,
                                "model": img2img_model,
                                "type": "img2img_batch",
                                "batch_index": idx + 1,
                                "batch_total": len(images_bytes_list),
                                "seed": batch_seed + (idx * seed_increment) if batch_seed != -1 else "auto",
                                "prompt": modification_description
                            }
                            
                            local_path, save_err = text2img_mgr.save_image(img_bytes, img_meta)
                            if local_path:
                                saved_paths.append(local_path)
                                print(f"[IMG2IMG-BATCH] ✅ Image {idx+1} sauvegardée: {local_path.name}")
                            else:
                                print(f"[IMG2IMG-BATCH] ❌ Erreur sauvegarde image {idx+1}: {save_err}")
                    except Exception as batch_save_err:
                        print(f"[IMG2IMG-BATCH] ❌ Erreur sauvegarde batch: {batch_save_err}")
                
                if not saved_paths:
                    replacement = "❌ Erreur batch: images générées mais sauvegarde échouée"
                else:
                    # Construire le HTML de la grille avec lightbox
                    tooltip_desc = modification_description.replace('"', '&quot;').replace("'", "&#39;")
                    
                    clean_prompt = json.dumps(_extract_prompt_for_display(modification_description), ensure_ascii=False)[1:-1]
                    
                    # CSS inline pour la grille (max 2 colonnes)
                    grid_html = f'''<div class="ogma-batch-grid" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; max-width: 100%; margin: 10px 0;">'''
                    
                    for idx, path in enumerate(saved_paths):
                        image_url = f"/generated/{path.name}"
                        seed_info = batch_seed + (idx * seed_increment) if batch_seed != -1 else "auto"
                        grid_html += f'''
                        <div class="ogma-batch-item" style="position: relative;">
                            <img src="{image_url}" 
                                 alt="Variante {idx+1}" 
                                 style="width: 100%; height: auto; border-radius: 8px; object-fit: cover; cursor: copy;"
                                 title="#{idx+1} (seed: {seed_info}) | 📋 Clic pour copier le prompt&#10;{tooltip_desc[:100]}..."
                                 data-prompt="{clean_prompt}"
                                 data-seed="{seed_info}"
                                 onclick="navigator.clipboard.writeText(this.getAttribute('data-prompt')).then(() => {{ const title = this.title; this.title = '✅ Prompt copié !'; setTimeout(() => this.title = title, 2000); }}).catch(err => alert('Erreur copie: ' + err));"
                            />
                            <span style="position: absolute; bottom: 4px; left: 4px; background: rgba(0,0,0,0.7); color: white; padding: 2px 6px; border-radius: 4px; font-size: 11px;">#{idx+1}</span>
                        </div>'''
                    
                    grid_html += '</div>'
                    
                    # Ajouter le script lightbox s'il n'existe pas déjà
                    lightbox_script = '''
<script>
if (!window.ogmaLightbox) {
    window.ogmaLightbox = function(src) {
        // Créer overlay
        var overlay = document.createElement('div');
        overlay.id = 'ogma-lightbox-overlay';
        overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.9);z-index:9999;display:flex;align-items:center;justify-content:center;cursor:pointer;';
        overlay.onclick = function() { this.remove(); };
        
        // Image
        var img = document.createElement('img');
        img.src = src;
        img.style.cssText = 'max-width:90%;max-height:90%;border-radius:8px;box-shadow:0 4px 20px rgba(0,0,0,0.5);';
        img.onclick = function(e) { e.stopPropagation(); };
        
        // Bouton fermer
        var closeBtn = document.createElement('span');
        closeBtn.innerHTML = '&times;';
        closeBtn.style.cssText = 'position:absolute;top:20px;right:30px;font-size:40px;color:white;cursor:pointer;font-weight:bold;';
        closeBtn.onclick = function() { overlay.remove(); };
        
        overlay.appendChild(img);
        overlay.appendChild(closeBtn);
        document.body.appendChild(overlay);
        
        // Fermer avec Escape
        var escHandler = function(e) { if(e.key==="Escape"){ overlay.remove(); document.removeEventListener("keydown",escHandler); }};
        document.addEventListener("keydown", escHandler);
    };
}
</script>'''
                    
                    # Info résumé
                    nb_ok = len(saved_paths)
                    nb_err = len(errors_list) if errors_list else 0
                    summary = f"🎲 Batch {nb_ok}/{batch_count} images"
                    if nb_err > 0:
                        summary += f" ({nb_err} erreur(s))"
                    
                    replacement = f"{lightbox_script}{grid_html}\n<small style='color: #888;'>{summary}</small>"
                    
                    # Stocker pour analyse vision future
                    global _pending_vision_analysis
                    _pending_vision_analysis = {
                        'images': [str(p) for p in saved_paths],
                        'prompts': [modification_description] * len(saved_paths),
                        'type': 'img2img_batch',
                        'batch_metadata': batch_metadata
                    }
                    
                    print(f"[IMG2IMG-BATCH] ✅ Grille {nb_ok} images générée avec lightbox")
            
            # Remplacer et retourner
            return response_text.replace(img2img_match.group(0), replacement)
        
        # ═══════════════════════════════════════════════════
        # 🔄 BRANCHEMENT: Mode auto-correctif vs one-shot
        # ═══════════════════════════════════════════════════
        autocorrect_enabled = img_config.get('i2i_autocorrect_enabled', False)
        
        if autocorrect_enabled:
            # --- MODE AUTO-CORRECTIF ---
            print(f"[IMG2IMG] 🔄 Mode auto-correctif ACTIVE")
            
            # Récupérer le chat controller pour analyse + refinement
            try:
                from ogma_ng import _ensure_chat_controller
                chat_ctrl = _ensure_chat_controller()
            except Exception:
                chat_ctrl = None
            
            if not chat_ctrl:
                print(f"[IMG2IMG] ⚠️ Chat controller indisponible - fallback mode one-shot")
                autocorrect_enabled = False
        
        if autocorrect_enabled:
            # Reset du flag stop avant de commencer
            reset_i2i_stop()
            
            # Callback de progression ASYNC pour feedback temps reel dans l'UI
            # Accumule les lignes de progression pour affichage dans le widget streaming
            _progress_lines = []
            
            async def on_progress_callback(attempt, max_retries, score, status_msg):
                """Async callback appele apres chaque etape pour notifier l'utilisateur en temps reel."""
                try:
                    from ogma_ng import _notify_safe, get_streaming_widget_ref
                    
                    # Emojis ASCII-safe pour NiceGUI/orjson (pas de surrogates Unicode)
                    threshold = img_config.get('i2i_score_threshold', 6)
                    if score >= threshold:
                        emoji = "[OK]"
                    elif score > 0:
                        emoji = "[!]"
                    else:
                        emoji = "[...]"
                    
                    msg = f"{emoji} i2i [{attempt}/{max_retries}] {status_msg}"
                    print(f"[I2I-PROGRESS] {msg}")
                    
                    _notify_safe(msg, 'ongoing', timeout=90)
                    
                    # Mise a jour du widget streaming pour feedback visuel live
                    _progress_lines.append(msg)
                    streaming_widget = get_streaming_widget_ref()
                    if streaming_widget:
                        progress_text = "\n\n".join(_progress_lines)
                        streaming_widget.set_content(
                            f"**Modification auto-corrective en cours...**\n\n{progress_text}"
                        )
                        print(f"[I2I-PROGRESS] Widget streaming mis a jour ({len(_progress_lines)} lignes)")
                    else:
                        print(f"[I2I-PROGRESS] Widget streaming non disponible")
                    
                    # CRUCIAL: laisser l'event loop flusher les updates WebSocket vers le navigateur
                    await asyncio.sleep(0.1)
                except Exception as e:
                    print(f"[I2I-PROGRESS] Erreur callback: {e}")
            
            correction_result = await generate_img2img_with_correction(
                modification_description=modification_description,
                source_images_base64=source_images_base64,
                settings_manager=settings_manager,
                chat_controller=chat_ctrl,
                img_config=img_config,
                on_progress=on_progress_callback,
                web_tips_context=web_tips_context
            )
            
            # Extraire les résultats
            image_bytes = correction_result.get('image_bytes')
            error = correction_result.get('error')
            metadata = correction_result.get('metadata')
            local_image_path = correction_result.get('image_path')
            final_prompt = correction_result.get('final_prompt', modification_description)
            best_score = correction_result.get('best_score', 0)
            attempts_used = correction_result.get('attempts_used', 0)
            was_stopped = correction_result.get('stopped', False)
            analysis_history = correction_result.get('analysis_history', [])
            
            # Log résumé
            print(f"[IMG2IMG] 🔄 Auto-correction terminee: {attempts_used} tentative(s), score {best_score}/10" + (" [STOPPE]" if was_stopped else ""))
            
            if error and not image_bytes:
                print(f"[IMG2IMG] ❌ ÉCHEC GÉNÉRATION (auto-correctif): {error}")
                replacement = f"❌ Erreur de modification d'image : {error}"
            elif not image_bytes:
                replacement = "❌ Erreur de modification d'image : aucune image générée"
            else:
                # Image sauvegardée pendant la boucle corrective
                if not local_image_path:
                    replacement = "❌ Erreur: Image modifiée mais sauvegarde échouée."
                    print(f"[IMG2IMG] ❌ PAS DE PATH - Sauvegarde échouée dans la boucle corrective")
                else:
                    # Préparer les métadonnées pour l'affichage
                    tooltip_description = final_prompt.replace('"', '&quot;').replace("'", "&#39;")
                    clean_prompt = json.dumps(_extract_prompt_for_display(final_prompt), ensure_ascii=False)[1:-1]
                    
                    image_url = f"/generated/{local_image_path.name}"
                    save_info = f" | 💾 {local_image_path.name}"
                    
                    # Stocker pour analyse vision future
                    _pending_vision_analysis = local_image_path
                    print(f"[IMG2IMG] ⚡ URL directe: {image_url}")
                    
                    replacement = f"""<img src="{image_url}" title="🎨 {tooltip_description}{save_info} | 📋 Cliquez pour copier" alt="Image modifiée" data-prompt="{clean_prompt}" onclick="navigator.clipboard.writeText(this.getAttribute('data-prompt')).then(() => {{ const title = this.title; this.title = '✅ Prompt copié !'; setTimeout(() => this.title = title, 2000); }}).catch(err => alert('Erreur copie: ' + err));" style="max-width: 100%; height: auto; border-radius: 8px; margin: 10px 0; cursor: copy;" />"""
                    
                    # Ajouter rapport auto-correction détaillé (journal par tentative)
                    threshold = int(img_config.get('i2i_score_threshold', 6))
                    score_emoji = '✅' if best_score >= threshold else '⚠️'
                    prompt_history = correction_result.get('prompt_history', [])
                    
                    correction_report = f"\n\n---\n{score_emoji} **Auto-correction i2i: {best_score}/10** ({attempts_used}/{img_config.get('i2i_max_retries', 3)} tentatives)"
                    if was_stopped:
                        correction_report += " | ⏹ *Arrêté par l'utilisateur*"
                    
                    # Journal détaillé par tentative
                    if analysis_history:
                        for i, analysis in enumerate(analysis_history):
                            a_score = analysis.get('score', '?')
                            a_attempt = analysis.get('attempt', i + 1)
                            a_defauts = analysis.get('defauts_detectes', [])
                            a_error = analysis.get('error')
                            is_best = (i == len(analysis_history) - 1 and a_score == best_score)
                            
                            marker = "🎯" if is_best else "🔄"
                            correction_report += f"\n\n{marker} **Tentative {a_attempt}** — score {a_score}/10"
                            
                            if a_error:
                                correction_report += f"\n❌ *Erreur: {a_error[:80]}*"
                                continue
                            
                            # Défauts détectés
                            critiques = [d for d in a_defauts if d.get('gravite') == 'critique']
                            majeurs = [d for d in a_defauts if d.get('gravite') == 'majeur']
                            mineurs = [d for d in a_defauts if d.get('gravite') == 'mineur']
                            
                            if critiques:
                                for d in critiques[:3]:
                                    correction_report += f"\n❌ *{d.get('type', '?')}: {d.get('description', '?')[:90]}*"
                            if majeurs:
                                for d in majeurs[:2]:
                                    correction_report += f"\n⚠️ *{d.get('type', '?')}: {d.get('description', '?')[:90]}*"
                            if mineurs:
                                correction_report += f"\n🟡 *{len(mineurs)} défaut(s) mineur(s)*"
                            
                            # Correction appliquée au prompt (diff entre tentative N et N+1)
                            if i < len(prompt_history) - 1:
                                next_prompt = prompt_history[i + 1] if (i + 1) < len(prompt_history) else ""
                                current_p = prompt_history[i] if i < len(prompt_history) else ""
                                if next_prompt and next_prompt != current_p:
                                    correction_report += f"\n📝 *Prompt corrigé → {next_prompt[:120]}...*"
                    
                    correction_report += "\n---"
                    replacement += correction_report
                    
                    # Notifier si une proposition de guide a été générée
                    guide_proposal = correction_result.get('guide_proposal')
                    if guide_proposal:
                        proposal_text = guide_proposal.get('proposal_text', '')
                        reason = guide_proposal.get('reason', '')
                        replacement += f"\n\n📋 *Proposition d'amélioration du guide i2i (basée sur {len(guide_proposal.get('lesson_ids', []))} leçons):*\n*{reason}*\n*Règles proposées:*\n*{proposal_text}*\n*→ Approuvez dans Paramètres > Image > Guide i2i*"
                    
                    # Vision feedback sur le résultat final (si activé)
                    ai_can_see = img_config.get('ai_can_see_images', False)
                    if ai_can_see and not analysis_history:
                        # Pas d'analyse dans l'historique = feedback classique
                        try:
                            feedback = await get_luna_image_feedback(
                                image_path=local_image_path,
                                chat_controller=chat_ctrl,
                                prompt_type="img2img",
                                original_prompt=final_prompt,
                                settings_manager=settings_manager
                            )
                            if feedback:
                                replacement += f"\n\n💭 *{feedback}*"
                        except Exception as e:
                            print(f"[VISION-FEEDBACK] ⚠️ Erreur feedback: {e}")
            
            return response_text.replace(img2img_match.group(0), replacement)
        
        # ═══════════════════════════════════════════════════
        # 📸 MODE ONE-SHOT (original, zéro changement)
        # ═══════════════════════════════════════════════════
        # Enrichir le prompt avec les tips web si disponibles
        one_shot_prompt = modification_description
        if web_tips_context:
            print(f"[IMG2IMG] ONE-SHOT: enrichissement prompt avec tips web")
            try:
                from ogma_ng import _ensure_chat_controller
                _enrich_ctrl = _ensure_chat_controller()
                if _enrich_ctrl:
                    enrich_prompt = f"""Tu es experte en prompts img2img. Voici un prompt utilisateur et des conseils specifiques au modele.

PROMPT ORIGINAL:
{modification_description}

TIPS SPECIFIQUES AU MODELE ({img2img_model}):
{web_tips_context}

REECRIS le prompt en integrant les conseils pertinents. Garde l'intention identique, ajoute seulement les garde-fous techniques.
Max 200 mots, en anglais. Retourne UNIQUEMENT le prompt ameliore."""
                    enriched, err = await _enrich_ctrl.call_chat_api(
                        messages=[{'role': 'user', 'content': enrich_prompt}],
                        max_tokens=500,
                        context_length=8192,
                        temperature=0.3,
                        is_json=False
                    )
                    if enriched and not err:
                        one_shot_prompt = enriched.strip().strip('"\'')
                        print(f"[IMG2IMG] ONE-SHOT: prompt enrichi ({len(one_shot_prompt)} chars)")
            except Exception as enrich_err:
                print(f"[IMG2IMG] ONE-SHOT: enrichissement echoue, prompt original utilise: {enrich_err}")
        
        image_bytes, error, metadata = await backend.generate_img2img(
            prompt=one_shot_prompt,
            source_images_base64=source_images_base64,
            provider=img2img_provider,
            model=img2img_model,
            width=img_config.get('width', 1024),
            height=img_config.get('height', 1024),
            size=img_config.get('img2img_size', '2048*2048'),  # Taille Seedream ByteDance
            aspect_ratio=img_config.get('img2img_aspect_ratio', '1:1'),
            quality=img_config.get('img2img_quality', 'basic'),
            image_size=img_config.get('img2img_image_size', 'square_hd'),
            image_resolution=img_config.get('img2img_image_resolution', '1K'),
            resolution=img_config.get('img2img_resolution', '1K'),
            max_images_output=img_config.get('img2img_max_images', 1),
            output_format=img_config.get('img2img_output_format', 'jpeg'),  # jpeg par défaut pour Seedream
            strength=img_config.get('img2img_strength', 0.8),
            enable_safety_checker=img_config.get('img2img_safety', True),
            num_inference_steps=img_config.get('img2img_steps', 30),
            guidance_scale=img_config.get('img2img_guidance', 2.5),
            negative_prompt=img_config.get('img2img_negative', 'blurry, ugly'),
            acceleration='none'
        )

        if error:
            print(f"[IMG2IMG] ❌ ÉCHEC GÉNÉRATION: {error}")
            print(f"[IMG2IMG] ❌ Provider: {img2img_provider}, Modèle: {img2img_model}")
            print(f"[IMG2IMG] ❌ Prompt: {modification_description[:100]}...")
            replacement = f"❌ Erreur de modification d'image : {error}"
            
            # L'IA commente l'erreur si option activée
            img_config = settings_manager.settings.get('image_generation', {})
            ai_can_see = img_config.get('ai_can_see_images', False)
            if ai_can_see:
                print(f"[ERROR-FEEDBACK] 🔍 L'IA va analyser l'erreur...")
                try:
                    from ogma_ng import _ensure_chat_controller
                    chat_ctrl = _ensure_chat_controller()
                    if chat_ctrl:
                        error_feedback = await get_ai_error_feedback(
                            error_message=error,
                            original_prompt=modification_description,
                            chat_controller=chat_ctrl,
                            generation_type="img2img"
                        )
                        if error_feedback:
                            replacement += f"\n\n💭 *{error_feedback}*"
                except Exception as e:
                    print(f"[ERROR-FEEDBACK] ⚠️ Erreur feedback: {e}")
            
        elif not image_bytes:
            print(f"[IMG2IMG] ❌ AUCUNE IMAGE RETOURNÉE (image_bytes=None)")
            print(f"[IMG2IMG] ❌ Provider: {img2img_provider}, Modèle: {img2img_model}")
            replacement = "❌ Erreur de modification d'image : aucune image générée"
        else:
            local_image_path = None
            save_images = img_config.get('save_images', True)

            # Sauvegarder l'image sur disque (OBLIGATOIRE pour affichage)
            if save_images and image_bytes:
                try:
                    from extensions.text2img import get_text2img_manager
                    text2img_mgr = get_text2img_manager()
                    if text2img_mgr:
                        local_image_path, save_error = text2img_mgr.save_image(image_bytes, metadata)
                        if local_image_path:
                            print(f"[IMG2IMG] ✅ Image sauvegardée : {local_image_path}")
                        else:
                            print(f"[IMG2IMG] ❌ Erreur sauvegarde: {save_error}")
                except Exception as e:
                    print(f"[IMG2IMG] ❌ Erreur sauvegarde: {e}")
            elif not save_images:
                print(f"[IMG2IMG] ❌ save_images désactivé - impossible d'afficher l'image")

            # Vérifier que l'image a bien été sauvegardée
            if not local_image_path:
                replacement = "❌ Erreur: Image modifiée mais sauvegarde échouée. Activez 'save_images' dans les paramètres."
                print(f"[IMG2IMG] ❌ PAS DE FALLBACK BASE64 - Sauvegarde requise pour affichage")
            else:
                # Préparer les métadonnées pour l'affichage
                tooltip_description = modification_description.replace('"', '&quot;').replace("'", "&#39;")
                clean_prompt = json.dumps(_extract_prompt_for_display(modification_description), ensure_ascii=False)[1:-1]
                
                # URL directe vers le fichier sauvegardé (servie par /generated route)
                image_url = f"/generated/{local_image_path.name}"
                save_info = f" | 💾 {local_image_path.name}"
                
                # Stocker pour analyse vision future
                _pending_vision_analysis = local_image_path
                print(f"[IMG2IMG] ⚡ URL directe: {image_url}")
                
                replacement = f"""<img src="{image_url}" title="🎨 {tooltip_description}{save_info} | 📋 Cliquez pour copier" alt="Image modifiée" data-prompt="{clean_prompt}" onclick="navigator.clipboard.writeText(this.getAttribute('data-prompt')).then(() => {{ const title = this.title; this.title = '✅ Prompt copié !'; setTimeout(() => this.title = title, 2000); }}).catch(err => alert('Erreur copie: ' + err));" style="max-width: 100%; height: auto; border-radius: 8px; margin: 10px 0; cursor: copy;" />"""
                
                # Si Luna peut voir ses créations, ajouter son feedback
                ai_can_see = img_config.get('ai_can_see_images', False)
                if ai_can_see:
                    print(f"[VISION-FEEDBACK] 🔍 Luna va analyser son image modifiée...")
                    # Récupérer le chat controller depuis ogma_ng
                    try:
                        from ogma_ng import _ensure_chat_controller
                        chat_ctrl = _ensure_chat_controller()
                        if chat_ctrl:
                            feedback = await get_luna_image_feedback(
                                image_path=local_image_path,
                                chat_controller=chat_ctrl,
                                prompt_type="img2img",
                                original_prompt=modification_description,
                                settings_manager=settings_manager
                            )
                            if feedback:
                                replacement += f"\n\n💭 *{feedback}*"
                    except Exception as e:
                        print(f"[VISION-FEEDBACK] ⚠️ Erreur feedback: {e}")

        return response_text.replace(img2img_match.group(0), replacement)

    except Exception as e:
        import traceback
        print(f"[IMG2IMG] ❌ EXCEPTION CRITIQUE: {e}")
        print(f"[IMG2IMG] ❌ Traceback:")
        traceback.print_exc()
        return response_text
