"""
Dream Engine - Génération d'Illustrations
==========================================

Génère les illustrations des rêves :
- Image unique figurative/abstraite
- Planche 4 cases (bande dessinée)
"""

from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path
from datetime import datetime
import asyncio
import re


async def generate_dream_illustration(
    dream_content: str,
    dream_summary: str,
    chat_controller=None,
    settings_manager=None,
    style: str = "auto",  # "auto", "single", "comic_4"
    pregenerated_prompts: List[str] = None  # Prompts déjà générés (pour éviter double génération)
) -> Dict[str, Any]:
    """
    Génère une illustration pour le rêve.
    
    Args:
        dream_content: Le récit complet du rêve
        dream_summary: Un résumé court pour le prompt
        chat_controller: Contrôleur IA principal
        settings_manager: Gestionnaire settings
        style: Style d'illustration ("auto" laisse l'IA choisir)
        pregenerated_prompts: Si fourni, utilise ces prompts au lieu d'en générer
        
    Returns:
        Dict avec 'success', 'image_path', 'style_used', 'prompts'
    """
    result = {
        'success': False,
        'image_path': None,
        'style_used': None,
        'prompts': [],
        'error': None
    }
    
    try:
        # 1. Utiliser les prompts prégénérés ou en générer de nouveaux
        if pregenerated_prompts:
            prompts = pregenerated_prompts
            print(f"[DREAM-ILLUST] ♻️ Réutilisation de {len(prompts)} prompt(s) prégénérés")
        else:
            prompts = await _generate_illustration_prompts(
                dream_content,
                dream_summary,
                chat_controller,
                style
            )
        
        if not prompts:
            result['error'] = "Pas de prompts générés"
            return result
        
        result['prompts'] = prompts
        
        # 2. Déterminer le style utilisé (pour logging uniquement)
        # Note: On génère toujours 1 seule image, le provider gère les multi-cases
        if style == "comic_4":
            result['style_used'] = "comic_4"
        elif style == "single":
            result['style_used'] = "single"
        else:
            result['style_used'] = "auto"
        
        # 3. Générer l'image (toujours via _generate_single_image)
        # Le prompt peut décrire 4 cases, le provider génère 1 image avec 4 cases
        if prompts:
            image_path = await _generate_single_image(prompts[0], settings_manager)
        else:
            result['error'] = "Aucun prompt généré"
            return result
        
        if image_path:
            result['success'] = True
            result['image_path'] = str(image_path)
            print(f"[DREAM-ILLUST] ✅ Illustration générée: {image_path}")
        else:
            result['error'] = "Échec génération image"
        
    except Exception as e:
        result['error'] = str(e)
        print(f"[DREAM-ILLUST] ❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
    
    return result


async def _generate_illustration_prompts(
    dream_content: str,
    dream_summary: str,
    chat_controller,
    style: str
) -> List[str]:
    """Demande a l'IA principale de generer les prompts d'illustration."""
    prompts = []
    
    try:
        print(f"[DREAM-ILLUST] 🔍 DEBUG: Génération prompts demandée")
        print(f"[DREAM-ILLUST] 🔍 chat_controller disponible: {chat_controller is not None}")
        print(f"[DREAM-ILLUST] 🔍 style: {style}")
        
        from .dream_prompts import DREAM_ILLUSTRATION_PROMPT
        
        # Construire le prompt utilisateur (le system prompt est défini plus bas)
        user_prompt = DREAM_ILLUSTRATION_PROMPT.format(dream_summary=dream_summary)
        
        # 🔧 Instructions configurables depuis settings
        try:
            from extensions.dream_engine import get_config
            config = get_config()
            
            # 🔍 DEBUG: Log config chargée
            print(f"[DREAM-ILLUST] 🔍 Style reçu: {style}")
            print(f"[DREAM-ILLUST] 🔍 Config prompt_comic_instruction: {config.get('prompt_comic_instruction', 'NON_DEFINI')[:100]}")
            
            if style == "comic_4":
                # Instruction comic configurable (défaut si vide)
                comic_instruction = config.get('prompt_comic_instruction', '').strip()
                if not comic_instruction:
                    print(f"[DREAM-ILLUST] ⚠️ prompt_comic_instruction VIDE - Utilisation fallback")
                    comic_instruction = "\n\nGénère une planche BD de 4 cases."
                else:
                    print(f"[DREAM-ILLUST] ✅ Utilisation instruction custom ({len(comic_instruction)} chars)")
                user_prompt += comic_instruction
            elif style == "single":
                # Instruction single configurable (défaut si vide)
                single_instruction = config.get('prompt_single_instruction', '').strip()
                if not single_instruction:
                    single_instruction = "\n\nGénère une seule image."
                user_prompt += single_instruction
            elif style == "auto":
                # Instruction auto configurable (vide par defaut = IA decide)
                auto_instruction = config.get('prompt_auto_instruction', '').strip()
                if auto_instruction:
                    user_prompt += auto_instruction
                # Sinon rien = IA choisit librement
        except:
            # Fallback si config non disponible
            if style == "comic_4":
                user_prompt += "\n\nGénère une planche BD de 4 cases."
            elif style == "single":
                user_prompt += "\n\nGénère une seule image."
        
        # System prompt réécrit : forcer un prompt image direct en anglais
        system_prompt = (
            "You are an expert image generation prompt writer. "
            "The user will describe a dream. Your task: write a vivid, concise image generation prompt "
            "in English describing the key visual scene. "
            "Rules: return ONLY the prompt, no introduction, no explanation, no markdown. "
            "Start directly with visual descriptors (e.g. 'dreamlike surreal...', 'dark ethereal...'). "
            "Maximum 300 words."
        )
        
        if chat_controller:
            # call_chat_api est async et necessite context_length
            print(f"[DREAM-ILLUST] Appel IA pour generation prompts...")
            response, error = await chat_controller.call_chat_api(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=700,
                context_length=4096,
                temperature=0.85
            )
            
            print(f"[DREAM-ILLUST] Reponse IA recue: {len(response) if response else 0} chars")
            print(f"[DREAM-ILLUST] Erreur: {error if error else 'Aucune'}")
            
            if response and not error:
                print(f"[DREAM-ILLUST] Reponse IA: {response[:200]}...")
                prompts = _parse_image_prompts(response)
            elif error:
                print(f"[DREAM-ILLUST] ⚠️ Erreur LLM: {error}")
        else:
            print(f"[DREAM-ILLUST] ⚠️ chat_controller est None - fallback")
            # Fallback sans contrôleur
            prompts = [f"Dreamy abstract illustration: {dream_summary[:100]}"]
        
        print(f"[DREAM-ILLUST] 📝 {len(prompts)} prompt(s) générés")
        if prompts:
            print(f"[DREAM-ILLUST] 📝 Premier prompt: {prompts[0][:150]}...")
        
    except Exception as e:
        print(f"[DREAM-ILLUST] ❌ Erreur génération prompts: {e}")
        import traceback
        traceback.print_exc()
    
    return prompts


# Préfixes bavards courants que les LLMs ajoutent avant le vrai prompt
_PREAMBLE_PATTERNS = [
    r'^(?:voici|here(?:\s+is)?|this\s+is|here\'s)\s+(?:a|an|my|the)?\s*(?:vivid|dream(?:y|like|scape)?|oniric|surreal|concise|detailed|image)?\s*(?:prompt|illustration|interprétation|description|résumé)?\s*[:\-–—]?\s*',
    r'^(?:image\s+(?:prompt|génér[ée]+))\s*[:\-–—]?\s*',
    r'^[*_#]+.*?[*_#]+\s*',  # Ligne markdown title
    r'^(?:planche|case|panel|frame)\s+(?:bd|comic|rêve)?\s*\d*\s*[:\-–—]?\s*',
    r'^\'\"?\s*',  # Guillemets initiaux
]


def _parse_image_prompts(response: str) -> List[str]:
    """Parse les prompts d'image depuis la reponse de l'IA."""
    prompts = []
    
    # Pattern pour image unique (phrase magique)
    single_pattern = r'🎨\s*\*\*image générée\s*:\*\*\s*["\']?(.+?)["\']?(?:\n|$)'
    single_match = re.search(single_pattern, response, re.IGNORECASE | re.DOTALL)
    if single_match:
        return [single_match.group(1).strip()[:800]]
    
    # Détection structure comic BD ("Case 1: \"...\"") → extraire et combiner les cases
    case_pattern = r'(?:Case|case|CASE|Scène|Scene)\s*\d+\s*[:\-–—]\s*["\']?([^"\'](?:[^"\']|(?<=\\)\')*?)["\']?(?=\s*(?:\n|$|[,;]\s*-))'
    # Pattern plus simple et robuste
    case_simple = r'(?:Case|case|CASE|Scène|Scene)\s*\d+\s*[:\-–—]\s*["\']?(.+?)["\']?\s*(?=$|\n)'
    case_matches = re.findall(case_simple, response, re.MULTILINE)
    if case_matches:
        # Combiner les 2 premières cases en un prompt cohérent
        combined = ' | '.join(m.strip().strip('"\'') for m in case_matches[:2] if m.strip())
        if combined:
            return [combined[:800]]
    
    # Nettoyage : retirer les préambules bavards ligne par ligne
    clean = response.strip()
    
    # Retirer les lignes de titre markdown, séparateurs, emoji headers, etc.
    lines = clean.splitlines()
    content_lines = []
    for line in lines:
        stripped = line.strip()
        # Ignorer lignes vides initiales
        if not content_lines and not stripped:
            continue
        # Ignorer séparateurs markdown
        if re.match(r'^[-*_=]{3,}$', stripped):
            continue
        # Ignorer titres markdown (##, **titre**:)
        if re.match(r'^#+\s+', stripped) or re.match(r'^\*{1,2}[^*]+\*{1,2}\s*:', stripped):
            continue
        # Ignorer lignes d'en-tête avec emoji (ex: "🎨 **planche rêve 4 cases :**")
        if re.match(r'^[^\w\s]*[\U0001F300-\U0001FFFF]', stripped) and '**' in stripped:
            continue
        content_lines.append(line)
    
    clean = '\n'.join(content_lines).strip()
    
    # Retirer les préambules du début
    for pattern in _PREAMBLE_PATTERNS:
        new_clean = re.sub(pattern, '', clean, count=1, flags=re.IGNORECASE | re.DOTALL)
        if new_clean != clean and len(new_clean) > 30:
            clean = new_clean.strip()
            break
    
    # Si la première ligne ressemble à une introduction (pas une description visuelle)
    first_line = clean.splitlines()[0] if clean.splitlines() else ''
    intro_words = ('voici', 'here is', 'this is', "here's", 'je vais', "c'est", 'je propose')
    if any(first_line.lower().startswith(w) for w in intro_words):
        rest = '\n'.join(clean.splitlines()[1:]).strip()
        if len(rest) > 50:
            clean = rest
    
    if clean:
        # Limiter à 800 chars (limite KIE API)
        if len(clean) > 800:
            clean = clean[:800]
        prompts = [clean]
    
    return prompts


async def _generate_single_image(prompt: str, settings_manager) -> Optional[Path]:
    """Genere une seule image en utilisant le prompt de l'IA TEL QUEL."""
    try:
        from extensions.text2img import get_text2img_manager
        
        text2img_mgr = get_text2img_manager()
        
        if not text2img_mgr:
            print("[DREAM-ILLUST] ⚠️ Text2Img manager non disponible")
            return None
        
        # 🛡️ SÉCURITÉ: Tronquer si dépasse limite KIE API (~800 chars max)
        MAX_PROMPT_LENGTH = 800
        final_prompt = prompt
        
        if len(prompt) > MAX_PROMPT_LENGTH:
            final_prompt = prompt[:MAX_PROMPT_LENGTH]
            print(f"[DREAM-ILLUST] ⚠️ Prompt tronqué: {len(prompt)} → {MAX_PROMPT_LENGTH} chars (limite KIE API)")
        
        print(f"[DREAM-ILLUST] Generation via Text2Img Manager...")
        print(f"[DREAM-ILLUST] Prompt IA ({len(final_prompt)} chars): {final_prompt[:150]}...")
        
        # Utiliser generate_image qui lit automatiquement la config (provider, model depuis settings)
        image_bytes, error, metadata = await text2img_mgr.generate_image(
            prompt=final_prompt  # Prompt de l'IA (tronque si necessaire)
        )
        
        if error:
            # Fallback: Si échec Unfiltered, réessayer avec le provider img2img
            if 'nsfw' in str(error).lower():
                print(f"[DREAM-ILLUST] ⚠️ Rejet Unfiltered détecté - Fallback vers provider img2img...")
                
                # Récupérer le provider img2img depuis settings
                if settings_manager:
                    try:
                        img2img_provider = settings_manager.settings.get('img2img_provider', 'WaveSpeed')
                        img2img_model = settings_manager.settings.get('img2img_model', 'sd3.5-large-turbo')
                        
                        print(f"[DREAM-ILLUST] 🔄 Tentative avec {img2img_provider}/{img2img_model}...")
                        
                        # Réessayer avec le provider img2img
                        image_bytes, error, metadata = await text2img_mgr.generate_image(
                            prompt=final_prompt,
                            provider_override=img2img_provider,
                            model_override=img2img_model
                        )
                        
                        if not error and image_bytes:
                            print(f"[DREAM-ILLUST] ✅ Fallback réussi avec {img2img_provider}")
                        else:
                            print(f"[DREAM-ILLUST] ❌ Fallback échoué: {error}")
                            return None
                    except Exception as fallback_error:
                        print(f"[DREAM-ILLUST] ❌ Erreur fallback: {fallback_error}")
                        return None
                else:
                    print(f"[DREAM-ILLUST] ❌ Settings manager non disponible pour fallback")
                    return None
            else:
                print(f"[DREAM-ILLUST] ❌ Erreur génération: {error}")
                return None
        
        if not image_bytes:
            print("[DREAM-ILLUST] ❌ Pas d'image retournée")
            return None
        
        # Ajouter metadata dream et sauvegarder
        if metadata is None:
            metadata = {}
        metadata['type'] = 'dream_illustration'
        metadata['prompt'] = prompt  # Prompt de l'IA
        
        local_path, save_error = text2img_mgr.save_image(image_bytes, metadata)
        
        if local_path:
            print(f"[DREAM-ILLUST] ✅ Image sauvegardée: {local_path}")
            return local_path
        else:
            print(f"[DREAM-ILLUST] ❌ Erreur sauvegarde: {save_error}")
        
        return None
        
    except Exception as e:
        print(f"[DREAM-ILLUST] ❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return None


async def _generate_comic_grid(prompts: List[str], settings_manager) -> Optional[Path]:
    """Génère une grille 2x2 à partir de 4 prompts."""
    try:
        from PIL import Image
        from io import BytesIO
        
        # Générer les 4 images
        images = []
        for i, prompt in enumerate(prompts[:4]):
            print(f"[DREAM-ILLUST] 🎨 Case {i+1}/4...")
            image_path = await _generate_single_image(prompt, settings_manager)
            
            if image_path:
                img = Image.open(image_path)
                images.append(img)
            else:
                # Image placeholder si échec
                placeholder = Image.new('RGB', (512, 512), color=(50, 50, 80))
                images.append(placeholder)
        
        if len(images) < 4:
            print("[DREAM-ILLUST] ⚠️ Pas assez d'images pour la grille")
            # Compléter avec des placeholders
            while len(images) < 4:
                placeholder = Image.new('RGB', (512, 512), color=(50, 50, 80))
                images.append(placeholder)
        
        # Redimensionner toutes les images à la même taille
        cell_size = (512, 512)
        resized = [img.resize(cell_size, Image.Resampling.LANCZOS) for img in images]
        
        # Créer la grille 2x2
        grid_width = cell_size[0] * 2
        grid_height = cell_size[1] * 2
        grid = Image.new('RGB', (grid_width, grid_height))
        
        # Placer les images
        grid.paste(resized[0], (0, 0))
        grid.paste(resized[1], (cell_size[0], 0))
        grid.paste(resized[2], (0, cell_size[1]))
        grid.paste(resized[3], (cell_size[0], cell_size[1]))
        
        # Sauvegarder
        output_dir = Path(__file__).parent.parent.parent / 'data' / 'generated_images'
        output_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = output_dir / f"dream_comic_{timestamp}.png"
        
        grid.save(output_path, "PNG")
        print(f"[DREAM-ILLUST] ✅ Grille sauvegardée: {output_path}")
        
        return output_path
        
    except ImportError:
        print("[DREAM-ILLUST] ❌ PIL non disponible pour la grille")
        # Fallback : retourner juste la première image
        if prompts:
            return await _generate_single_image(prompts[0], settings_manager)
        return None
        
    except Exception as e:
        print(f"[DREAM-ILLUST] ❌ Erreur grille: {e}")
        import traceback
        traceback.print_exc()
        return None


# ========== EXPORT ==========
__all__ = ['generate_dream_illustration', 'generate_illustration_prompts']


async def generate_illustration_prompts(
    dream_content: str,
    dream_summary: str,
    chat_controller,
    style: str = "auto"
) -> List[str]:
    """
    Génère les prompts d'illustration (sans créer l'image).
    Utilisé pour l'analyse PSY avant la génération réelle.
    
    Args:
        dream_content: Le récit complet du rêve
        dream_summary: Un résumé court pour le prompt
        chat_controller: Contrôleur IA principal
        style: Style d'illustration ("auto", "single", "comic_4")
        
    Returns:
        List[str]: Les prompts d'illustration générés
    """
    return await _generate_illustration_prompts(
        dream_content, dream_summary, chat_controller, style
    )
