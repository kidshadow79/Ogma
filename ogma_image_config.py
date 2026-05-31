"""
OGMA Image Configuration (Multi-Provider)
==========================================
Modal de configuration de la génération d'images.
Providers supportés: GROK (xAI), OpenAI (DALL-E), Google (Imagen), Kie.ai, WaveSpeed.ai
+ Image-to-Image (Kie.ai et WaveSpeed.ai)
"""

from nicegui import ui
from typing import Optional, Callable, List
from utils.i18n import t

# Variable pour stocker la référence au settings manager
_settings_manager_getter: Optional[Callable] = None

# Providers et leurs modèles Text-to-Image
IMAGE_PROVIDERS = {
    "GROK": {
        "name": "Grok Imagine (xAI)",
        "models": ["grok-2-image-1212"],
        "nsfw": True,
        "info": "🔥 Spicy - Moins censuré"
    },
    "OpenAI": {
        "name": "DALL-E (OpenAI)",
        "models": ["dall-e-3", "dall-e-2"],
        "nsfw": False,
        "info": "🔒 Très censuré"
    },
    "Google": {
        "name": "Imagen (Google)",
        "models": ["imagen-3.0-generate-002", "imagen-3.0-fast-generate-001"],
        "nsfw": False,
        "info": "⚠️ Modérément censuré"
    },
    "Kie": {
        "name": "Kie.ai (Multi-modèles)",
        "models": [
            "z-image",                              # $0.004 - Ultra rapide Unfiltered
            "qwen2/text-to-image",                  # $0.004 - Qwen2 Unfiltered
            "bytedance/seedream",                   # $0.02  - Seedream 3.0
            "bytedance/seedream-v4-text-to-image",  # $0.025 - Seedream 4.0
            "flux-2/pro-text-to-image",             # $0.025 - Haute qualité Unfiltered
            "grok-imagine/text-to-image",           # $0.10  - xAI via Kie
            "nano-banana-pro",                      # $0.09  - Google DeepMind 2K
        ],
        "nsfw": True,
        "info": "🔥 Multi-modèles Unfiltered - De $0.004 à $0.10/img"
    },
    "WaveSpeed": {
        "name": "WaveSpeed.ai (Unfiltered/Spicy)",
        "models": [
            "wavespeed-ai/z-image/turbo",                   # $0.005 - Ultra-rapide T2I
            "wavespeed-ai/female-human",                     # $0.015 - Personnages réalistes
            "wavespeed-ai/prefect-pony-xl",                  # $0.015 - Anime/Pony Unfiltered
            "wavespeed-ai/kolors",                           # $0.015 - Qualité/vitesse
            "wavespeed-ai/jib-mix-qwen-image/text-to-image", # $0.02 - Portraits réalistes
            "wavespeed-ai/qwen-image/text-to-image",         # $0.02 - Qwen Image 20B
            "wavespeed-ai/seedream-v4",                      # $0.025 - Seedream V4
            "wavespeed-ai/flux-dev",                         # $0.025 - Flux Dev qualité
            "wavespeed-ai/flux-2-dev",                       # $0.03 - Flux 2 Dev
            "bytedance/seedream-v4.5",                       # $0.032 - Seedream V4.5 4K
            "stability-ai/sd3.5-medium",                     # $0.035 - SD 3.5 Medium
            "wavespeed-ai/flux-1.1-pro",                     # $0.04 - Flux 1.1 Pro
            "stability-ai/sd3-turbo",                        # $0.04 - SD 3 Turbo
            "stability-ai/sd3.5-large-turbo",                # $0.04 - SD 3.5 Large Turbo
            "recraft-ai/recraft-v3",                         # $0.04 - Design/illustration
            "wavespeed-ai/flux-2-pro",                       # $0.05 - Flux 2 Pro
            "wavespeed-ai/flux-1.1-pro-ultra",               # $0.06 - Flux 1.1 Pro Ultra
            "wavespeed-ai/flux-2-max",                       # $0.06 - Flux 2 Max
            "stability-ai/sd3.5-large",                      # $0.065 - SD 3.5 Large
            "stability-ai/sdxl",                             # $0.01 - SDXL Unfiltered
            "wavespeed-ai/flux-schnell",                     # $0.003 - Flux Schnell rapide
            "bytedance/seedream-v3",                         # $0.015 - Seedream V3
            "bytedance/seedream-v3.1",                       # $0.02 - Seedream V3.1
            "bytedance/seedream-v4",                         # $0.025 - Seedream V4 ByteDance
        ],
        "nsfw": True,
        "info": "� Spécial Unfiltered/Spicy - De $0.003 à $0.065/img"
    },
    "AtlasCloud": {
        "name": "AtlasCloud.ai (300+ modèles unifiés)",
        "models": [
            "bytedance/seedream-v5.0-lite",
            "bytedance/seedream-v5.0-lite/sequential",
            "bytedance/seedream-v4.5",
            "bytedance/seedream-v4.5/sequential",
            "bytedance/seedream-v4",
            "bytedance/seedream-v4/sequential",
            "black-forest-labs/flux-dev",
            "black-forest-labs/flux-schnell",
            "alibaba/wan-2.6/text-to-image",
            "alibaba/wan-2.5/text-to-image",
            "alibaba/qwen-image/text-to-image-max",
            "alibaba/qwen-image/text-to-image-plus",
            "atlascloud/qwen-image/text-to-image",
            "google/imagen4",
            "google/imagen4-fast",
            "google/imagen4-ultra",
            "google/imagen3",
            "google/imagen3-fast",
            "google/nano-banana-2/text-to-image",
            "google/nano-banana-pro/text-to-image",
            "google/nano-banana-pro/text-to-image-ultra",
            "google/nano-banana/text-to-image",
            "z-image/turbo",
        ],
        "nsfw": False,
        "info": "🌐 300+ modèles unifiés — Seedream, FLUX, Qwen, Imagen, Wan"
    }
}

# Modèles Image-to-Image par provider
# Kie.ai I2I Models
IMG2IMG_MODELS_KIE = {
    "flux-2/pro-image-to-image": {
        "name": "Flux-2 Pro (Image-to-Image)",
        "credits": 5,
        "usd": 0.025,
        "nsfw": True,
        "desc": "Haute qualité, modifie avec précision"
    },
    "seedream/4.5-edit": {
        "name": "Seedream 4.5 Edit",
        "credits": 6.5,
        "usd": 0.032,
        "nsfw": True,
        "desc": "ByteDance - Édition précise jusqu'à 4K, Unfiltered"
    },
    "bytedance/seedream-v4-edit": {
        "name": "Seedream V4 Edit",
        "credits": 6.5,
        "usd": 0.032,
        "nsfw": True,
        "desc": "ByteDance V4 - Multi-images supporté, Unfiltered"
    },
    "gpt-image/1.5-image-to-image": {
        "name": "GPT Image 1.5 (OpenAI via Kie)",
        "credits": 10,
        "usd": 0.05,
        "nsfw": False,
        "desc": "OpenAI - Excellent suivi d'instructions"
    },
    "nano-banana-pro-img2img": {
        "name": "Nano Banana Pro (Google)",
        "credits": 18,
        "usd": 0.09,
        "nsfw": False,
        "desc": "Google DeepMind - Qualité premium 2K/4K"
    },
    "qwen/image-to-image": {
        "name": "Qwen Image-to-Image",
        "credits": 5,
        "usd": 0.025,
        "nsfw": True,
        "desc": "🔧 Strength + Safety checker + Params avancés"
    },
    "qwen/image-edit": {
        "name": "Qwen Image Edit",
        "credits": 5,
        "usd": 0.025,
        "nsfw": True,
        "desc": "🎨 Édition créative + Safety checker + Format"
    }
}

# AtlasCloud.ai I2I Models (18 modèles depuis API /api/v1/models)
IMG2IMG_MODELS_ATLASCLOUD = {
    "bytedance/seedream-v5.0-lite/edit": {"name": "Seedream v5.0 Lite Edit", "usd": 0.032, "nsfw": False, "desc": "ByteDance - Seedream 5.0 Lite Edit, HOT"},
    "bytedance/seedream-v5.0-lite/edit-sequential": {"name": "Seedream v5.0 Lite Edit Sequential", "usd": 0.032, "nsfw": False, "desc": "ByteDance - Batch edit multi-images"},
    "bytedance/seedream-v4.5/edit": {"name": "Seedream v4.5 Edit", "usd": 0.036, "nsfw": False, "desc": "ByteDance v4.5 - Visage et détails préservés"},
    "bytedance/seedream-v4.5/edit-sequential": {"name": "Seedream v4.5 Edit Sequential", "usd": 0.036, "nsfw": False, "desc": "ByteDance v4.5 - Batch edit"},
    "bytedance/seedream-v4/edit": {"name": "Seedream v4 Edit", "usd": 0.024, "nsfw": False, "desc": "ByteDance v4 - Édition précise"},
    "bytedance/seedream-v4/edit-sequential": {"name": "Seedream v4 Edit Sequential", "usd": 0.024, "nsfw": False, "desc": "ByteDance v4 - Batch edit"},
    "black-forest-labs/flux-kontext-dev": {"name": "FLUX Kontext Dev", "usd": 0.025, "nsfw": False, "desc": "✏️ Édition par texte (BFL)"},
    "black-forest-labs/flux-kontext-dev-lora": {"name": "FLUX Kontext Dev LoRA", "usd": 0.030, "nsfw": False, "desc": "✏️ FLUX Kontext avec LoRA"},
    "alibaba/qwen-image/edit": {"name": "Qwen-Image Edit", "usd": 0.032, "nsfw": False, "desc": "Alibaba - Multi-images, texte dans les images"},
    "alibaba/qwen-image/edit-plus": {"name": "Qwen-Image Edit Plus", "usd": 0.032, "nsfw": False, "desc": "Alibaba - Edit Plus avancé"},
    "alibaba/qwen-image/edit-plus-20251215": {"name": "Qwen-Image Edit Plus 20251215", "usd": 0.021, "nsfw": False, "desc": "Alibaba - Version Déc 2025, HOT"},
    "atlascloud/qwen-image/edit": {"name": "Qwen Image Edit (AtlasCloud)", "usd": 0.020, "nsfw": False, "desc": "20B MMDiT - Edition next-gen"},
    "alibaba/wan-2.6/image-edit": {"name": "Wan-2.6 Image Edit", "usd": 0.021, "nsfw": False, "desc": "Alibaba Wan 2.6 - Edition mixte texte+image"},
    "alibaba/wan-2.5/image-edit": {"name": "Wan-2.5 Image Edit", "usd": 0.021, "nsfw": False, "desc": "Alibaba Wan 2.5"},
    "google/nano-banana-2/edit": {"name": "Nano Banana 2 Edit", "usd": 0.072, "nsfw": False, "desc": "Google - Transformation intuitive"},
    "google/nano-banana-pro/edit": {"name": "Nano Banana Pro Edit", "usd": 0.126, "nsfw": False, "desc": "Google - Premium qualité"},
    "google/nano-banana-pro/edit-ultra": {"name": "Nano Banana Pro Edit Ultra", "usd": 0.150, "nsfw": False, "desc": "Google - Ultra qualité maximale"},
    "google/nano-banana/edit": {"name": "Nano Banana Edit", "usd": 0.034, "nsfw": False, "desc": "Google - Edition économique"},
}

# WaveSpeed.ai I2I Models (Unfiltered/Spicy)
IMG2IMG_MODELS_WAVESPEED = {
    "wavespeed-ai/z-image-turbo/image-to-image": {
        "name": "⚡ Z-Image Turbo I2I",
        "credits": 0,
        "usd": 0.005,
        "nsfw": True,
        "desc": "Ultra-rapide et pas cher! Unfiltered"
    },
    "higgsfield/soul/image-to-image": {
        "name": "🎭 Higgsfield Soul I2I",
        "credits": 0,
        "usd": 0.025,
        "nsfw": True,
        "desc": "Style réaliste/artistique, Unfiltered"
    },
    "wavespeed-ai/flux-kontext-dev": {
        "name": "✏️ Flux Kontext Dev",
        "credits": 0,
        "usd": 0.025,
        "nsfw": True,
        "desc": "Édition par instruction, Unfiltered"
    },
    "wavespeed-ai/image-face-swap": {
        "name": "🎭 Face Swap",
        "credits": 0,
        "usd": 0.005,
        "nsfw": True,
        "desc": "Swap de visage (2 images requises)"
    },
    "wavespeed-ai/image-head-swap": {
        "name": "👤 Head Swap",
        "credits": 0,
        "usd": 0.008,
        "nsfw": True,
        "desc": "Swap de tête complet (2 images)"
    },
    "wavespeed-ai/wan-2.2/image-to-image": {
        "name": "🌊 Wan 2.2 Image Edit",
        "credits": 0,
        "usd": 0.02,
        "nsfw": True,
        "desc": "Wan 2.2 édition d'image, Unfiltered"
    },
    "wavespeed-ai/qwen-image-edit": {
        "name": "🧠 Qwen Image Edit (WS)",
        "credits": 0,
        "usd": 0.02,
        "nsfw": True,
        "desc": "Qwen via WaveSpeed, Unfiltered"
    },
    "wavespeed-ai/seedream-v4": {
        "name": "🌱 Seedream V4 (WS)",
        "credits": 0,
        "usd": 0.025,
        "nsfw": True,
        "desc": "ByteDance V4 via WaveSpeed"
    },
    "bytedance/seedream-4.5": {
        "name": "🌱 Seedream 4.5 (WS)",
        "credits": 0,
        "usd": 0.032,
        "nsfw": True,
        "desc": "ByteDance 4.5 via WaveSpeed"
    },
    "bytedance/seedream-v3.1": {
        "name": "🌱 Seedream V3.1",
        "credits": 0,
        "usd": 0.02,
        "nsfw": True,
        "desc": "ByteDance V3.1 classique"
    },
    "decart/lucy-edit-dev": {
        "name": "🎬 Lucy Edit (Decart)",
        "credits": 0,
        "usd": 0.015,
        "nsfw": True,
        "desc": "Decart Lucy édition créative"
    },
    "wavespeed-ai/flux-fill-dev": {
        "name": "🖌️ Flux Fill Dev",
        "credits": 0,
        "usd": 0.025,
        "nsfw": True,
        "desc": "Inpainting et remplissage intelligent"
    },
    "wavespeed-ai/infinite-you": {
        "name": "🔄 Infinite You (Swap)",
        "credits": 0,
        "usd": 0.02,
        "nsfw": True,
        "desc": "Swap de personnage/visage avancé"
    },
    "bytedance/seedream-v4.5/edit": {
        "name": "🌱 Seedream V4.5 Edit (⚠️ min 1920x1920)",
        "credits": 0,
        "usd": 0.035,
        "nsfw": True,
        "desc": "ByteDance V4.5 Edit - 4K, EXIGE images ≥1920x1920"
    },
    "bytedance/seedream-v4/edit": {
        "name": "🌱 Seedream V4 Edit (⚠️ min 1920x1920)",
        "credits": 0,
        "usd": 0.028,
        "nsfw": True,
        "desc": "ByteDance V4 Edit - EXIGE images ≥1920x1920"
    },
    "bytedance/seedream-v4.5/edit-sequential": {
        "name": "🌱 Seedream V4.5 Edit Seq (multi)",
        "credits": 0,
        "usd": 0.04,
        "nsfw": True,
        "desc": "V4.5 Multi-images séquentielles"
    },
    "bytedance/seedream-v4/edit-sequential": {
        "name": "🌱 Seedream V4 Edit Seq (multi)",
        "credits": 0,
        "usd": 0.035,
        "nsfw": True,
        "desc": "V4 Multi-images séquentielles"
    },
    "bytedance/seededit-v3": {
        "name": "🌱 SeedEdit V3",
        "credits": 0,
        "usd": 0.018,
        "nsfw": True,
        "desc": "SeedEdit V3 classique"
    },
    "alibaba/wan-2.5/image-edit": {
        "name": "🌊 Wan 2.5 Image Edit",
        "credits": 0,
        "usd": 0.025,
        "nsfw": True,
        "desc": "Alibaba Wan 2.5 - Édition image"
    },
    "google/nano-banana-pro/edit": {
        "name": "🍌 Nano Banana Pro Edit",
        "credits": 0,
        "usd": 0.05,
        "nsfw": False,
        "desc": "Google - Haute qualité (censuré)"
    },
    "google/nano-banana-pro/edit-ultra": {
        "name": "🍌 Nano Banana Pro Edit Ultra",
        "credits": 0,
        "usd": 0.08,
        "nsfw": False,
        "desc": "Google - 4K Ultra (censuré)"
    },
    "wavespeed-ai/qwen-image/edit-2511-lora": {
        "name": "🧠 Qwen Image Edit LoRA",
        "credits": 0,
        "usd": 0.022,
        "nsfw": True,
        "desc": "Qwen Edit avec LoRA"
    },
    "wavespeed-ai/z-image/turbo-inpaint": {
        "name": "⚡ Z-Image Turbo Inpaint",
        "credits": 0,
        "usd": 0.006,
        "nsfw": True,
        "desc": "Inpainting ultra-rapide et pas cher"
    }
}

# Dictionnaire combiné pour compatibilité (défaut: Kie + WaveSpeed)
IMG2IMG_MODELS = {**IMG2IMG_MODELS_KIE, **IMG2IMG_MODELS_WAVESPEED}

# Providers supportant I2I
IMG2IMG_PROVIDERS = {
    "Kie": {
        "name": "Kie.ai",
        "models": IMG2IMG_MODELS_KIE,
        "info": "🔥 Multi-modèles professionnels"
    },
    "WaveSpeed": {
        "name": "WaveSpeed.ai (Unfiltered/Spicy)",
        "models": IMG2IMG_MODELS_WAVESPEED,
        "info": "🔥 Spécialisé Unfiltered - Face/Head Swap"
    },
    "AtlasCloud": {
        "name": "AtlasCloud.ai (300+ modèles unifiés)",
        "models": IMG2IMG_MODELS_ATLASCLOUD,
        "info": "🌐 Seedream, FLUX Kontext, Qwen - API unifiée"
    }
}

# Coûts des modèles Kie Text-to-Image (en crédits et USD)
KIE_MODEL_COSTS = {
    "z-image": {"credits": 0.8, "usd": 0.004, "desc": "Ultra rapide, Unfiltered"},
    "bytedance/seedream": {"credits": 4, "usd": 0.02, "desc": "Seedream 3.0 artistique"},
    "bytedance/seedream-v4-text-to-image": {"credits": 5, "usd": 0.025, "desc": "Seedream 4.0 - Meilleur rapport qualité/prix"},
    "flux-2/pro-text-to-image": {"credits": 5, "usd": 0.025, "desc": "Haute qualité photoréaliste"},
    "seedream-4.5": {"credits": 6.5, "usd": 0.032, "desc": "ByteDance 4K précis"},
    "grok-imagine/text-to-image": {"credits": 20, "usd": 0.10, "desc": "xAI via Kie"},
    "nano-banana-pro": {"credits": 18, "usd": 0.09, "desc": "Google DeepMind 2K"},
    "gpt-image/1.5-text-to-image": {"credits": 10, "usd": 0.05, "desc": "OpenAI Flagship Quality"},
    "flux-1.1-pro": {"credits": 8, "usd": 0.04, "desc": "Flux 1.1 Pro"},
}

# Coûts des modèles WaveSpeed Text-to-Image (Unfiltered/Spicy)
WAVESPEED_MODEL_COSTS = {
    "wavespeed-ai/female-human": {"credits": 0, "usd": 0.015, "desc": "📸 Personnages réalistes"},
    "wavespeed-ai/prefect-pony-xl": {"credits": 0, "usd": 0.015, "desc": "🎨 Anime/Pony style Unfiltered"},
    "wavespeed-ai/jib-mix-qwen-image/text-to-image": {"credits": 0, "usd": 0.02, "desc": "📸 Portraits photo-réalistes"},
    "stability-ai/sdxl": {"credits": 0, "usd": 0.01, "desc": "🎯 Stable Diffusion XL Unfiltered"},
    "wavespeed-ai/flux-schnell": {"credits": 0, "usd": 0.003, "desc": "⚡ Flux Schnell ultra-rapide"},
    "wavespeed-ai/flux-dev": {"credits": 0, "usd": 0.025, "desc": "🔧 Flux Dev haute qualité"},
    "wavespeed-ai/flux-1.1-pro": {"credits": 0, "usd": 0.04, "desc": "Flux 1.1 Pro"},
    "wavespeed-ai/flux-1.1-pro-ultra": {"credits": 0, "usd": 0.06, "desc": "Flux 1.1 Pro Ultra"},
    "wavespeed-ai/flux-2-dev": {"credits": 0, "usd": 0.03, "desc": "Flux 2 Dev"},
    "wavespeed-ai/flux-2-pro": {"credits": 0, "usd": 0.05, "desc": "Flux 2 Pro"},
    "wavespeed-ai/flux-2-max": {"credits": 0, "usd": 0.06, "desc": "Flux 2 Max"},
    "wavespeed-ai/qwen-image/text-to-image": {"credits": 0, "usd": 0.02, "desc": "Qwen Image 20B"},
    "wavespeed-ai/seedream-v4": {"credits": 0, "usd": 0.025, "desc": "Seedream V4"},
}

RESOLUTION_PRESETS = {
    "Carré (1:1)": (1024, 1024),
    "Paysage (16:9)": (1792, 1024),
    "Portrait (9:16)": (1024, 1792),
    "HD Paysage": (1920, 1080),
    "HD Portrait": (1080, 1920),
    "Personnalisé": None
}


def set_settings_manager_getter(getter: Callable):
    """Configure la fonction pour obtenir le settings manager"""
    global _settings_manager_getter
    _settings_manager_getter = getter


def _ensure_settings_manager():
    """Obtient le settings manager via la fonction configurée"""
    if _settings_manager_getter:
        return _settings_manager_getter()
    raise RuntimeError("Settings manager getter not configured. Call set_settings_manager_getter first.")


def _get_available_providers(sm) -> List[str]:
    """Retourne les providers avec clé API configurée"""
    vault = sm.settings.get('api_keys_vault', {})
    available = []
    for provider in IMAGE_PROVIDERS.keys():
        if vault.get(provider):
            available.append(provider)
    return available


def _image_modal():
    """Fenêtre de configuration de la génération d'images multi-provider"""
    d = ui.dialog()
    sm = _ensure_settings_manager()

    # Charger config actuelle
    img_config = sm.settings.get('image_generation', {
        'enabled': False,
        'provider': 'GROK',
        'model': 'grok-2-image-1212',
        'width': 1024,
        'height': 1024,
        'safe_mode': False,
        'save_images': True,
        'ai_can_see_images': False,
        'vision_feedback_prompt': """Tu viens de créer/modifier cette image avec le prompt: \"{original_prompt}\"

RÈGLE: PIXELS_ONLY - Commente UNIQUEMENT ce que tu vois réellement dans l'image.
Si l'image ne correspond pas au prompt, dis-le clairement.
Si l'image ne s'est pas chargée ou est absente, dis-le.
0_Hallucination, 0_Invention.

En 2-3 phrases max, analyse objective du résultat visible.""",
        # Configuration Image-to-Image (séparée)
        'img2img_enabled': False,
        'img2img_model': 'seedream/4.5-edit',
        'img2img_quality': 'basic',
        'img2img_quality_gpt': 'medium',
        'img2img_image_size': 'square_hd',
        'img2img_image_resolution': '1K',
        'img2img_resolution': '1K',
        'img2img_max_images': 1,
        'img2img_output_format': 'png',
        'img2img_guide': """ATTENTION : Tu ne dois pas modifier des images quand tu en reçois. Tu les reçois juste pour les analyser ou échanger avec ton interlocuteur, notamment en mode webcam. C'est à ton appréciation. Si le contexte te demande de les modifier, suis le contexte.

RÔLE : Tu es l'Architecte Visuelle d'Ogma. Tu as l'initiative de modifier les images pour interagir visuellement avec l'Utilisateur.

✅ LE DÉCLENCHEUR D'INITIATIVE
Commence impérativement ta réponse par cette phrase exacte :
"Il faut que je modifie cette image : [ton prompt intégral en anglais]"

STRUCTURE DU PROMPT :

1. **GARDE** (Verrouiller les éléments source) :
Cite chaque élément à préserver précédé de "garde" :
- "garde la position du personnage" (ne nomme pas le personnage)
- "garde l'expression du visage"
- "garde l'arrière-plan"
Répète "garde" pour chaque élément, même si c'est redondant. (garde la main de l'homme, garde le pied de l'homme, garde le corps de l'homme, etc...)

2. **AJOUTE / SUPPRIME / CHANGE** (Modifications) :
Utilise le même principe de préfixe explicite :
- "ajoute un chapeau rouge"
- "supprime l'objet à droite"
- "change le décor en forêt"

3. **PROPORTIONS** :
Intègre dans le prompt : "Appliquer une déformation par pression aux points de contact. Conserve une logique biologique humaine. Utilisez les éléments présents dans l'image finale pour maintenir les proportions anatomiques."

4. **RÈGLE DE MOUVEMENT** :
Pour atteindre une cible basse, décris le mouvement qui baisse le centre de gravité du personnage (ex: "elle plie les genoux pour atteindre la serrure").

5. **TAGS DE PUISSANCE** :
Termine par : "Cinematic photographic render, maintain strict human skeletal constraints, sub-surface scattering, 8k, hyper-detailed skin textures, natural lighting, zero-artifact editing."

⚠️ INTERDICTION CRITIQUE - NE JAMAIS DÉCRIRE CE QUI EST GARDÉ :
- Ne rajoute AUCUN adjectif sur les éléments gardés, ni épithète ni terme technique
- Ne parle ni de texture, ni de taille, ni de superlatifs pour ces éléments
- Toute description d'un élément déjà présent dans la source le transforme en "pâte à modeler" pour l'IA générative, provoquant des déformations monstrueuses (effet tentacule/monstre)
- SEULE ACTION AUTORISÉE sur un élément gardé : le mot "garde" suivi du nom de l'élément. Rien d'autre.

⚠️ AUTRES INTERDICTIONS :
- Pas de prénoms (John, Marie, etc.) dans le prompt technique
- Sois factuelle, pas descriptive (prompt entre 50 et 120 mots)
- Décris ce que tu AJOUTES, ne décris JAMAIS ce que tu GARDES""",
        # Configuration Text-to-Image Guide (optimisé pour z-image)
        'text2img_guide': """🎨 GUIDE TEXT-TO-IMAGE (Z-IMAGE OPTIMISÉ)

📏 LIMITE STRICTE : 400-500 caractères maximum (au-delà = ERREUR API)

✅ STRUCTURE RECOMMANDÉE :
1. Style: "photorealistic", "candid iPhone photo feel"
2. Lieu: description précise du décor
3. Sujet: personnage avec détails (vêtements, pose, action)
4. Focus: "in sharp focus" / "blurred background"
5. Lumière: "natural light", "golden hour", "morning light"

✅ MOTS-CLÉS EFFICACES Z-IMAGE :
- photorealistic, iPhone photo feel, candid shot
- in sharp focus, bokeh background, depth of field
- natural light, morning light, golden hour
- detailed, crisp, clear

❌ INTERDICTIONS :
- Prompt en français (ANGLAIS UNIQUEMENT)
- Dépasser 500 caractères (limite API)
- Listes de mots-clés sans structure

📝 EXEMPLE PARFAIT :
"je dois créer une image de : Photorealistic image of a cafe terrace in Paris on a spring morning. In sharp focus: a young woman with pixie cut wearing a scarf, stirring cappuccino. Blurred background with street traffic. Natural morning light, iPhone photo feel."

❌ EXEMPLE MAUVAIS :
"8K ultra HD hyperrealistic cinematic portrait latina bronze skin golden hour rim lighting volumetric fog..." (LISTE DE MOTS-CLÉS SANS STRUCTURE)""",
        # ===== BOUCLE AUTO-CORRECTIVE I2I =====
        'i2i_autocorrect_enabled': False,
        'i2i_max_retries': 3,
        'i2i_score_threshold': 6,
        'i2i_web_tips_enabled': True,
        'i2i_analysis_prompt': """Tu viens de modifier cette image avec le prompt: "{original_prompt}"

MISSION : Analyse RIGOUREUSE du résultat. Tu es une inspectrice qualité impitoyable.
RÈGLE : PIXELS_ONLY. Ne commente que ce que tu VOIS. 0_Hallucination.

CHECKLIST SYSTÉMATIQUE (vérifie CHAQUE point) :
- ANATOMIE : Nombre de doigts correct (5/main) ? Bras/jambes corrects ? Pas de membre en trop/manquant ?
- PROPORTIONS : Tailles relatives cohérentes entre personnages ? Tête/corps ratio normal ?
- DÉFORMATIONS : Zones "pâte à modeler" ? Étirements anormaux ? Effet tentacule ?
- VISAGE : Symétrie faciale ? Expression naturelle ? Pas de fusion de traits ?
- ÉLÉMENTS GARDÉS : Ce qui devait être préservé l'est-il vraiment ?
- ÉLÉMENTS AJOUTÉS : Intégrés naturellement ? Proportions correctes ?
- CONTACT PHYSIQUE : Points de contact réalistes ? Pas de fusion entre corps ?
- ARRIÈRE-PLAN : Cohérent ? Pas de distorsion/artefacts ?
- LUMIÈRE/TEXTURE : Cohérence d'éclairage entre éléments source et ajoutés ?

Réponds UNIQUEMENT en JSON valide (pas de markdown, pas de ```json) :
{
  "score": <1-10>,
  "satisfaisant": <true si score >= 6>,
  "defauts_detectes": [
    {"type": "<deformation|proportion|artefact|anatomie|fusion|manquant|extra|texture>",
     "gravite": "<critique|majeur|mineur>",
     "description": "<description factuelle du défaut>",
     "zone": "<zone de l'image concernée>"}
  ],
  "elements_bien_preserves": ["<liste des éléments gardés avec succès>"],
  "prompt_issues": ["<ce qui dans le prompt a probablement causé chaque défaut>"],
  "correction_suggérée": "<reformulation du prompt pour corriger les défauts critiques>"
}

BARÈME : 9-10=parfait | 7-8=bon, défauts mineurs | 5-6=passable | 3-4=défauts majeurs | 1-2=raté
Score < 6 = à refaire. Sois EXIGEANTE.""",
    })
    
    # Providers disponibles (avec clé API)
    available_providers = _get_available_providers(sm)

    with d, ui.card().classes('popup-content q-dark').style('background: var(--bg-secondary); color: var(--text-primary); min-width: 720px; max-height: 85vh; overflow-y: auto;'):
        ui.label(t('image_modal_title')).classes('popup-title')
        ui.label(t('image_modal_subtitle')).classes('text-muted mb-4')

        with ui.column().classes('gap-4 w-full'):
            
            # Section activation
            with ui.card().classes('q-dark p-4').style('background: rgba(255,255,255,0.05);'):
                ui.label(t('image_section_activation')).classes('font-semibold mb-2')
                enabled_check = ui.checkbox(
                    t('image_check_enabled'),
                    value=img_config.get('enabled', False)
                ).classes('mb-2')
                ui.label(t('image_label_enabled_help')).classes('text-sm text-gray-400')

            # Section Clés API
            with ui.card().classes('q-dark p-4').style('background: rgba(255,255,255,0.05);'):
                ui.label(t('image_section_keys')).classes('font-semibold mb-2')
                ui.label(t('image_label_keys_subtitle')).classes('text-sm text-gray-400 mb-3')
                
                # Récupérer le vault actuel
                current_vault = sm.settings.get('api_keys_vault', {})
                
                # Créer les inputs pour chaque provider
                api_key_inputs = {}
                # Placeholder pour la fonction de refresh (définie plus tard)
                refresh_providers_fn = {'fn': None}
                
                with ui.column().classes('gap-3 w-full'):
                    # GROK
                    with ui.row().classes('items-center gap-2 w-full'):
                        ui.icon('local_fire_department').classes('text-orange-400')
                        ui.label('GROK (xAI)').classes('w-32')
                        from api_keys_vault_ui import VirtualKeyInput, api_key_status_indicator
                        grok_key_input = VirtualKeyInput(lambda: 'GROK')
                        api_key_inputs['GROK'] = grok_key_input
                        with ui.row().classes('flex-1 items-center'):
                            api_key_status_indicator('GROK', t('image_label_api_grok'))
                        
                        def test_grok():
                            if grok_key_input.value:
                                ui.notify(t('image_notify_test_start', provider='GROK'), type='info')
                                # Test simple: vérifier format de clé
                                if grok_key_input.value.startswith('xai-'):
                                    ui.notify(t('image_notify_key_valid', provider='GROK'), type='positive')
                                else:
                                    ui.notify(t('image_notify_key_unusual_xai'), type='warning')
                            else:
                                ui.notify(t('image_notify_no_key'), type='negative')
                        
                        ui.button(t('image_btn_test'), on_click=test_grok).props('dense flat').classes('text-xs')
                    
                    # OpenAI
                    with ui.row().classes('items-center gap-2 w-full'):
                        ui.icon('palette').classes('text-green-400')
                        ui.label('OpenAI').classes('w-32')
                        from api_keys_vault_ui import VirtualKeyInput, api_key_status_indicator
                        openai_key_input = VirtualKeyInput(lambda: 'OpenAI')
                        api_key_inputs['OpenAI'] = openai_key_input
                        with ui.row().classes('flex-1 items-center'):
                            api_key_status_indicator('OpenAI', t('image_label_api_openai'))
                        
                        def test_openai():
                            if openai_key_input.value:
                                ui.notify(t('image_notify_test_start', provider='OpenAI'), type='info')
                                if openai_key_input.value.startswith('sk-'):
                                    ui.notify(t('image_notify_key_valid', provider='OpenAI'), type='positive')
                                else:
                                    ui.notify(t('image_notify_key_unusual_openai'), type='warning')
                            else:
                                ui.notify(t('image_notify_no_key'), type='negative')
                        
                        ui.button(t('image_btn_test'), on_click=test_openai).props('dense flat').classes('text-xs')
                    
                    # Google
                    with ui.row().classes('items-center gap-2 w-full'):
                        ui.icon('language').classes('text-blue-400')
                        ui.label('Google').classes('w-32')
                        from api_keys_vault_ui import VirtualKeyInput, api_key_status_indicator
                        google_key_input = VirtualKeyInput(lambda: 'Google')
                        api_key_inputs['Google'] = google_key_input
                        with ui.row().classes('flex-1 items-center'):
                            api_key_status_indicator('Google', t('image_label_api_google'))
                        
                        def test_google():
                            if google_key_input.value:
                                ui.notify(t('image_notify_test_start', provider='Google'), type='info')
                                if google_key_input.value.startswith('AIza'):
                                    ui.notify(t('image_notify_key_valid', provider='Google'), type='positive')
                                else:
                                    ui.notify(t('image_notify_key_unusual_google'), type='warning')
                            else:
                                ui.notify(t('image_notify_no_key'), type='negative')
                        
                        ui.button(t('image_btn_test'), on_click=test_google).props('dense flat').classes('text-xs')
                    
                    # Kie.ai (Z-Image)
                    with ui.row().classes('items-center gap-2 w-full'):
                        ui.icon('bolt').classes('text-purple-400')
                        ui.label('Kie.ai').classes('w-32')
                        from api_keys_vault_ui import VirtualKeyInput, api_key_status_indicator
                        kie_key_input = VirtualKeyInput(lambda: 'Kie')
                        api_key_inputs['Kie'] = kie_key_input
                        with ui.row().classes('flex-1 items-center'):
                            api_key_status_indicator('Kie', t('image_label_api_kie'))
                        
                        def test_kie():
                            if kie_key_input.value:
                                ui.notify(t('image_notify_test_start', provider='Kie.ai'), type='info')
                                # Kie utilise des clés de format variable
                                if len(kie_key_input.value) > 20:
                                    ui.notify(t('image_notify_key_valid', provider='Kie'), type='positive')
                                else:
                                    ui.notify(t('image_notify_key_too_short'), type='warning')
                            else:
                                ui.notify(t('image_notify_no_key'), type='negative')
                        
                        ui.button(t('image_btn_test'), on_click=test_kie).props('dense flat').classes('text-xs')
                    
                    # WaveSpeed.ai (Unfiltered/Spicy)
                    with ui.row().classes('items-center gap-2 w-full'):
                        ui.icon('waves').classes('text-pink-400')
                        ui.label('WaveSpeed').classes('w-32')
                        from api_keys_vault_ui import VirtualKeyInput, api_key_status_indicator
                        wavespeed_key_input = VirtualKeyInput(lambda: 'WaveSpeed')
                        api_key_inputs['WaveSpeed'] = wavespeed_key_input
                        with ui.row().classes('flex-1 items-center'):
                            api_key_status_indicator('WaveSpeed', t('image_label_api_wavespeed'))
                        
                        def test_wavespeed():
                            if wavespeed_key_input.value:
                                ui.notify(t('image_notify_test_start', provider='WaveSpeed.ai'), type='info')
                                # WaveSpeed utilise des clés Bearer token
                                if len(wavespeed_key_input.value) > 20:
                                    ui.notify(t('image_notify_key_valid', provider='WaveSpeed'), type='positive')
                                else:
                                    ui.notify(t('image_notify_key_too_short'), type='warning')
                            else:
                                ui.notify(t('image_notify_no_key'), type='negative')
                        
                        ui.button(t('image_btn_test'), on_click=test_wavespeed).props('dense flat').classes('text-xs')
                    
                    # AtlasCloud.ai
                    with ui.row().classes('items-center gap-2 w-full'):
                        ui.icon('cloud').classes('text-sky-400')
                        ui.label('AtlasCloud').classes('w-32')
                        from api_keys_vault_ui import VirtualKeyInput, api_key_status_indicator
                        atlascloud_key_input = VirtualKeyInput(lambda: 'AtlasCloud')
                        api_key_inputs['AtlasCloud'] = atlascloud_key_input
                        with ui.row().classes('flex-1 items-center'):
                            api_key_status_indicator('AtlasCloud', t('image_label_api_atlascloud'))
                        
                        def test_atlascloud():
                            if atlascloud_key_input.value:
                                ui.notify(t('image_notify_test_start', provider='AtlasCloud.ai'), type='info')
                                if len(atlascloud_key_input.value) > 20:
                                    ui.notify(t('image_notify_key_valid', provider='AtlasCloud'), type='positive')
                                else:
                                    ui.notify(t('image_notify_key_too_short'), type='warning')
                            else:
                                ui.notify(t('image_notify_no_key'), type='negative')
                        
                        ui.button(t('image_btn_test'), on_click=test_atlascloud).props('dense flat').classes('text-xs')
                
                ui.label(t('image_label_keys_vault_note')).classes('text-xs text-gray-500 mt-2')

            # Section Provider et Modèle (Text-to-Image)
            with ui.card().classes('q-dark p-4').style('background: rgba(255,255,255,0.05);'):
                ui.label(t('image_section_t2i_provider')).classes('font-semibold mb-2')
                
                # Container pour message dynamique providers
                providers_status_container = ui.column().classes('mb-2')
                
                # Initialiser le statut (avant de définir la fonction update pour éviter les refs circulaires)
                with providers_status_container:
                    if not available_providers:
                        ui.label(t('image_label_no_provider')).classes('text-yellow-400')
                    else:
                        ui.label(t('image_label_providers_ok', n=len(available_providers), providers=', '.join(available_providers))).classes('text-green-400 text-sm')
                
                with ui.row().classes('gap-4 w-full'):
                    # Sélecteur de provider
                    current_provider = img_config.get('provider', 'GROK')
                    if current_provider not in available_providers and available_providers:
                        current_provider = available_providers[0]
                    
                    provider_options = available_providers if available_providers else list(IMAGE_PROVIDERS.keys())
                    
                    provider_select = ui.select(
                        label=t('image_label_provider'),
                        options=provider_options,
                        value=current_provider
                    ).classes('flex-1')
                    
                    # Sélecteur de modèle (dynamique selon provider)
                    current_model = img_config.get('model', '')
                    provider_models = IMAGE_PROVIDERS.get(current_provider, {}).get('models', [])
                    if current_model not in provider_models and provider_models:
                        current_model = provider_models[0]
                    
                    model_select = ui.select(
                        label=t('image_label_model'),
                        options=provider_models,
                        value=current_model
                    ).classes('flex-1')
                    
                    # Bouton refresh models depuis l'API
                    async def refresh_models_from_api():
                        """Récupère les modèles en direct depuis l'API du provider"""
                        provider = provider_select.value
                        
                        # Vérifier que le provider est dans les providers qui supportent fetch_live_models
                        if provider == "Kie":
                            ui.notify(t('image_notify_kie_no_endpoint'), type='warning')
                            ui.notify(t('image_notify_kie_hardcoded'), type='info')
                            return
                        
                        if provider not in ["WaveSpeed", "AtlasCloud"]:
                            ui.notify(t('image_notify_no_dyn_support', provider=provider), type='warning')
                            return
                        
                        try:
                            from extensions.text2img.image_backend import get_image_backend
                            
                            # S'assurer que le backend est à jour avec les clés actuelles
                            # Mettre à jour le vault avec les clés saisies
                            live_vault = {
                                'GROK': api_key_inputs['GROK'].value.strip() if api_key_inputs['GROK'].value else '',
                                'OpenAI': api_key_inputs['OpenAI'].value.strip() if api_key_inputs['OpenAI'].value else '',
                                'Google': api_key_inputs['Google'].value.strip() if api_key_inputs['Google'].value else '',
                                'Kie': api_key_inputs['Kie'].value.strip() if api_key_inputs['Kie'].value else '',
                                'WaveSpeed': api_key_inputs['WaveSpeed'].value.strip() if api_key_inputs['WaveSpeed'].value else '',
                                'AtlasCloud': api_key_inputs['AtlasCloud'].value.strip() if api_key_inputs.get('AtlasCloud') and api_key_inputs['AtlasCloud'].value else ''
                            }
                            
                            # Vérifier que la clé API existe pour ce provider
                            if not live_vault.get(provider):
                                ui.notify(t('image_notify_no_key_for', provider=provider), type='negative')
                                return
                            
                            # Mettre à jour le vault dans settings temporairement
                            old_vault = sm.settings.get('api_keys_vault', {})
                            sm.settings['api_keys_vault'] = {**old_vault, **live_vault}
                            
                            # Réinitialiser le backend pour prendre en compte les nouvelles clés
                            from extensions.text2img.image_backend import reset_backend
                            reset_backend()
                            backend = get_image_backend(sm)
                            
                            if not backend:
                                ui.notify(t('image_notify_no_backend'), type='negative')
                                return
                            
                            ui.notify(t('image_notify_fetching', provider=provider), type='info')
                            
                            # Appeler fetch_live_models
                            models_list, error = await backend.fetch_live_models(provider)
                            
                            if error:
                                ui.notify(t('image_notify_err', error=error), type='negative')
                                return
                            
                            if not models_list:
                                ui.notify(t('image_notify_no_models', provider=provider), type='warning')
                                return
                            
                            # Mettre à jour la liste des modèles dans le sélecteur
                            model_select.options = models_list
                            if models_list:
                                model_select.value = models_list[0]
                            model_select.update()
                            
                            ui.notify(t('image_notify_models_updated', n=len(models_list), provider=provider), type='positive')
                            
                        except Exception as e:
                            print(f"[IMAGE-CONFIG] ❌ Erreur refresh_models_from_api: {e}")
                            import traceback
                            traceback.print_exc()
                            ui.notify(t('image_notify_tech_err', msg=str(e)[:100]), type='negative')
                    
                    ui.button(
                        icon='refresh',
                        on_click=refresh_models_from_api
                    ).props('dense flat round').classes('text-cyan-400').tooltip(t('image_tooltip_refresh_models'))
                
                # === Custom Model Input pour Kie (style Ollama) ===
                custom_model_container = ui.row().classes('gap-2 items-center w-full mt-2')
                
                def update_custom_model_visibility():
                    """Affiche le champ Custom Model seulement si Kie est sélectionné"""
                    custom_model_container.clear()
                    if provider_select.value == "Kie":
                        with custom_model_container:
                            with ui.column().classes('w-full gap-1'):
                                ui.label(t('image_label_add_custom_kie')).classes('text-xs text-gray-400 font-semibold')
                                with ui.row().classes('gap-2 items-center w-full'):
                                    custom_model_input = ui.input(
                                        label=t('image_label_model_name_kie'),
                                        placeholder='family/variant',
                                        value=''
                                    ).classes('flex-1').tooltip(t('image_tooltip_kie_model_name'))
                                    custom_format_select = ui.select(
                                        options={
                                            'format_A':  'Format A — aspect_ratio (z-image, grok-imagine…)',
                                            'format_A+': 'Format A+ — aspect_ratio + resolution (flux-2/pro…)',
                                            'format_B':  'Format B — image_size enum (seedream, nano-banana…)',
                                            'format_C':  'Format C — image_size ratio (qwen2…)',
                                        },
                                        value='format_A',
                                        label=t('image_label_payload_format')
                                    ).classes('w-64').tooltip(t('image_tooltip_kie_payload_format'))

                                    def add_custom_model():
                                        custom = custom_model_input.value.strip()
                                        fmt = custom_format_select.value
                                        if not custom:
                                            ui.notify(t('image_notify_no_model_name'), type='warning')
                                            return
                                        # Enregistrer dans CUSTOM_MODELS du backend
                                        try:
                                            from extensions.text2img.image_backend import get_image_backend
                                            backend = get_image_backend()
                                            kie_provider = backend._providers.get('Kie') if backend else None
                                            if kie_provider:
                                                kie_provider.CUSTOM_MODELS[custom] = {
                                                    'payload_format': fmt,
                                                    'nsfw': True,
                                                    'credits': '?',
                                                    'type': 'text2img'
                                                }
                                        except Exception as e:
                                            print(f'[KIE-CUSTOM] Erreur enregistrement backend: {e}')
                                        # Ajouter à la liste UI
                                        if custom not in model_select.options:
                                            model_select.options.append(custom)
                                        model_select.value = custom
                                        model_select.update()
                                        fmt_label = {
                                            'format_A': 'A (aspect_ratio)',
                                            'format_A+': 'A+ (aspect_ratio+resolution)',
                                            'format_B': 'B (image_size enum)',
                                            'format_C': 'C (image_size ratio)',
                                        }.get(fmt, fmt)
                                        ui.notify(t('image_notify_custom_added', model=custom, fmt=fmt_label), type='positive')
                                        custom_model_input.value = ''

                                    ui.button(
                                        icon='add',
                                        on_click=add_custom_model
                                    ).props('flat dense').classes('text-cyan-400').tooltip(t('image_tooltip_add_model'))
                
                provider_select.on_value_change(lambda e: update_custom_model_visibility())
                update_custom_model_visibility()
                
                # Info provider
                provider_info_label = ui.label('').classes('text-sm mt-2')
                model_cost_label = ui.label('').classes('text-xs text-cyan-400')
                
                def update_provider_info():
                    provider = provider_select.value
                    info = IMAGE_PROVIDERS.get(provider, {})
                    nsfw_status = "🔥 Mode Spicy disponible" if info.get('nsfw') else "🔒 Contenu censuré"
                    provider_info_label.text = f"{info.get('name', provider)} - {info.get('info', '')} - {nsfw_status}"
                    # Mettre à jour les modèles
                    new_models = info.get('models', [])
                    model_select.options = new_models
                    if new_models and model_select.value not in new_models:
                        model_select.value = new_models[0]
                    model_select.update()
                    # Mettre à jour le coût du modèle
                    update_model_cost()
                
                def update_model_cost():
                    """Affiche le coût du modèle sélectionné (WaveSpeed)"""
                    provider = provider_select.value
                    model = model_select.value
                    if provider == "WaveSpeed" and model in WAVESPEED_MODEL_COSTS:
                        cost_info = WAVESPEED_MODEL_COSTS[model]
                        model_cost_label.text = f"💰 {cost_info.get('desc', '')} - ${cost_info.get('usd', '?')}/img"
                    elif provider == "Kie":
                        # Kie a son propre système de coûts
                        model_cost_label.text = "💰 Voir tarifs sur kie.ai"
                    elif provider == "AtlasCloud":
                        model_cost_label.text = "💰 Voir tarifs sur atlascloud.ai"
                    else:
                        model_cost_label.text = ""
                
                provider_select.on_value_change(lambda e: update_provider_info())
                model_select.on_value_change(lambda e: update_model_cost())
                update_provider_info()
                
                # Définir la fonction de mise à jour des providers (maintenant que provider_select existe)
                def update_providers_status():
                    """Met à jour le statut des providers disponibles"""
                    providers_status_container.clear()
                    # Recalculer les providers disponibles avec les nouvelles clés
                    live_vault = {
                        'GROK': api_key_inputs['GROK'].value.strip() if api_key_inputs['GROK'].value else '',
                        'OpenAI': api_key_inputs['OpenAI'].value.strip() if api_key_inputs['OpenAI'].value else '',
                        'Google': api_key_inputs['Google'].value.strip() if api_key_inputs['Google'].value else '',
                        'Kie': api_key_inputs['Kie'].value.strip() if api_key_inputs['Kie'].value else '',
                        'WaveSpeed': api_key_inputs['WaveSpeed'].value.strip() if api_key_inputs['WaveSpeed'].value else '',
                        'AtlasCloud': api_key_inputs['AtlasCloud'].value.strip() if api_key_inputs.get('AtlasCloud') and api_key_inputs['AtlasCloud'].value else ''
                    }
                    live_providers = [p for p in IMAGE_PROVIDERS.keys() if live_vault.get(p)]
                    
                    with providers_status_container:
                        if not live_providers:
                            ui.label(t('image_label_no_provider_all')).classes('text-yellow-400')
                        else:
                            ui.label(f'✅ {len(live_providers)} provider(s) disponible(s): {", ".join(live_providers)}').classes('text-green-400 text-sm')
                    
                    # Mettre à jour les options du sélecteur
                    provider_select.options = live_providers if live_providers else list(IMAGE_PROVIDERS.keys())
                    if live_providers and provider_select.value not in live_providers:
                        provider_select.value = live_providers[0]
                    provider_select.update()
                
                # Connecter au placeholder pour les callbacks des inputs de clés API
                refresh_providers_fn['fn'] = update_providers_status

            # Section Résolution
            with ui.card().classes('q-dark p-4').style('background: rgba(255,255,255,0.05);'):
                ui.label(t('image_section_resolution')).classes('font-semibold mb-2')
                
                with ui.row().classes('gap-4 items-center w-full'):
                    # Presets
                    preset_select = ui.select(
                        label=t('image_label_preset'),
                        options=list(RESOLUTION_PRESETS.keys()),
                        value='Carré (1:1)'
                    ).classes('flex-1')
                    
                    # Dimensions personnalisées
                    width_input = ui.number(
                        'Largeur',
                        value=img_config.get('width', 1024),
                        min=256,
                        max=2048,
                        step=64
                    ).classes('w-24')
                    ui.label('×').classes('text-xl')
                    height_input = ui.number(
                        'Hauteur',
                        value=img_config.get('height', 1024),
                        min=256,
                        max=2048,
                        step=64
                    ).classes('w-24')
                
                def apply_preset():
                    preset = preset_select.value
                    dims = RESOLUTION_PRESETS.get(preset)
                    if dims:
                        width_input.value = dims[0]
                        height_input.value = dims[1]
                
                preset_select.on_value_change(lambda e: apply_preset())

            # Section Mode Unfiltered/Spicy
            with ui.card().classes('q-dark p-4').style('background: rgba(255,255,255,0.05);'):
                ui.label(t('image_section_content_mode')).classes('font-semibold mb-2')
                
                safe_mode_check = ui.checkbox(
                    'Mode Safe (filtrage activé)',
                    value=img_config.get('safe_mode', False)
                ).classes('mb-2')
                
                ui.label(t('image_label_safe_warn')).classes('text-sm text-yellow-400')
                ui.label(t('image_label_safe_warn2')).classes('text-sm text-gray-500')

            # Section Image-to-Image (Multi-Provider: Kie + WaveSpeed)
            with ui.card().classes('q-dark p-4').style('background: rgba(59, 130, 246, 0.1); border-left: 3px solid #3b82f6;'):
                ui.label(t('image_section_i2i')).classes('font-semibold mb-2').style('color: #3b82f6;')
                ui.label(t('image_label_i2i_help')).classes('text-sm text-gray-400 mb-3')
                
                img2img_enabled_check = ui.checkbox(
                    'Activer Image-to-Image',
                    value=img_config.get('img2img_enabled', False)
                ).classes('mb-3')
                
                # Provider I2I selector
                with ui.row().classes('gap-4 items-center w-full mb-2'):
                    ui.label(t('image_label_i2i_provider')).classes('text-sm font-semibold')
                    
                    img2img_provider_options = list(IMG2IMG_PROVIDERS.keys())
                    current_img2img_provider = img_config.get('img2img_provider', 'Kie')
                    if current_img2img_provider not in img2img_provider_options:
                        current_img2img_provider = 'Kie'
                    
                    img2img_provider_select = ui.select(
                        label=t('image_label_provider'),
                        options=img2img_provider_options,
                        value=current_img2img_provider
                    ).classes('w-40')
                    
                    # Info du provider sélectionné
                    img2img_provider_info = ui.label(
                        IMG2IMG_PROVIDERS.get(current_img2img_provider, {}).get('info', '')
                    ).classes('text-xs text-cyan-400')
                
                # Fonction pour obtenir les modèles du provider sélectionné
                def get_models_for_provider(provider: str) -> dict:
                    return IMG2IMG_PROVIDERS.get(provider, {}).get('models', IMG2IMG_MODELS_KIE)
                
                with ui.row().classes('gap-4 items-center w-full'):
                    ui.label(t('image_label_i2i_model')).classes('text-sm')
                    
                    # Modèles du provider actuel
                    current_provider_models = get_models_for_provider(current_img2img_provider)
                    img2img_model_options = list(current_provider_models.keys())
                    current_img2img_model = img_config.get('img2img_model', img2img_model_options[0] if img2img_model_options else '')
                    if current_img2img_model not in img2img_model_options and img2img_model_options:
                        current_img2img_model = img2img_model_options[0]
                    
                    img2img_model_select = ui.select(
                        label=t('image_label_model'),
                        options=img2img_model_options,
                        value=current_img2img_model
                    ).classes('flex-1')
                    
                    # Bouton refresh models img2img depuis l'API
                    async def refresh_img2img_models_from_api():
                        """Récupère les modèles img2img en direct depuis l'API du provider"""
                        provider = img2img_provider_select.value
                        
                        # Vérifier que le provider est supporté
                        if provider == "Kie":
                            ui.notify(t('image_notify_kie_no_endpoint'), type='warning')
                            ui.notify(t('image_notify_kie_hardcoded'), type='info')
                            return
                        
                        if provider not in ["WaveSpeed", "AtlasCloud"]:
                            ui.notify(t('image_notify_no_dyn_support', provider=provider), type='warning')
                            return
                        
                        try:
                            from extensions.text2img.image_backend import get_image_backend, reset_backend
                            
                            # Mettre à jour le vault avec les clés actuelles
                            live_vault = {
                                'GROK': api_key_inputs['GROK'].value.strip() if api_key_inputs['GROK'].value else '',
                                'OpenAI': api_key_inputs['OpenAI'].value.strip() if api_key_inputs['OpenAI'].value else '',
                                'Google': api_key_inputs['Google'].value.strip() if api_key_inputs['Google'].value else '',
                                'Kie': api_key_inputs['Kie'].value.strip() if api_key_inputs['Kie'].value else '',
                                'WaveSpeed': api_key_inputs['WaveSpeed'].value.strip() if api_key_inputs['WaveSpeed'].value else '',
                                'AtlasCloud': api_key_inputs['AtlasCloud'].value.strip() if api_key_inputs.get('AtlasCloud') and api_key_inputs['AtlasCloud'].value else ''
                            }
                            
                            # Vérifier que la clé API existe pour ce provider
                            if not live_vault.get(provider):
                                ui.notify(t('image_notify_no_key_for', provider=provider), type='negative')
                                return
                            
                            # Mettre à jour le vault temporairement
                            old_vault = sm.settings.get('api_keys_vault', {})
                            sm.settings['api_keys_vault'] = {**old_vault, **live_vault}
                            
                            # Réinitialiser le backend
                            reset_backend()
                            backend = get_image_backend(sm)
                            
                            if not backend:
                                ui.notify(t('image_notify_no_backend'), type='negative')
                                return
                            
                            ui.notify(t('image_notify_fetching_i2i', provider=provider), type='info')
                            
                            # Appeler fetch_live_img2img_models
                            models_list, error = await backend.fetch_live_img2img_models(provider)
                            
                            if error:
                                ui.notify(t('image_notify_err', error=error), type='negative')
                                return
                            
                            if not models_list:
                                ui.notify(t('image_notify_no_models_i2i', provider=provider), type='warning')
                                return
                            
                            # Mettre à jour la liste des modèles dans le sélecteur
                            img2img_model_select.options = models_list
                            if models_list:
                                img2img_model_select.value = models_list[0]
                            img2img_model_select.update()
                            
                            ui.notify(t('image_notify_models_updated_i2i', n=len(models_list), provider=provider), type='positive')
                            
                        except Exception as e:
                            print(f"[IMAGE-CONFIG-I2I] ❌ Erreur refresh_img2img_models_from_api: {e}")
                            import traceback
                            traceback.print_exc()
                            ui.notify(t('image_notify_tech_err', msg=str(e)[:100]), type='negative')
                    
                    ui.button(
                        icon='refresh',
                        on_click=refresh_img2img_models_from_api
                    ).props('dense flat round').classes('text-blue-400').tooltip(t('image_tooltip_refresh_models_i2i'))
                
                # === Custom Model Input pour Kie I2I (style Ollama) ===
                custom_img2img_container = ui.row().classes('gap-2 items-center w-full mt-2')
                
                def update_custom_img2img_visibility():
                    """Affiche le champ Custom Model I2I seulement si Kie est sélectionné"""
                    custom_img2img_container.clear()
                    if img2img_provider_select.value == "Kie":
                        with custom_img2img_container:
                            with ui.column().classes('w-full gap-1'):
                                ui.label(t('image_label_add_custom_i2i')).classes('text-xs text-gray-400 font-semibold')
                                with ui.row().classes('gap-2 items-center w-full'):
                                    custom_img2img_input = ui.input(
                                        label=t('image_label_model_name_i2i'),
                                        placeholder='family/variant',
                                        value=''
                                    ).classes('flex-1').tooltip(
                                        'Consultez https://kie.ai/market pour la liste des modèles I2I disponibles'
                                    )
                                    custom_img2img_format_select = ui.select(
                                        options={
                                            'format_A':  'Format A — aspect_ratio',
                                            'format_A+': 'Format A+ — aspect_ratio + resolution',
                                            'format_B':  'Format B — image_size enum',
                                            'format_C':  'Format C — image_size ratio',
                                        },
                                        value='format_A',
                                        label=t('image_label_payload_format')
                                    ).classes('w-64').tooltip(t('image_tooltip_kie_payload_format'))

                                    def add_custom_img2img_model():
                                        custom = custom_img2img_input.value.strip()
                                        fmt = custom_img2img_format_select.value
                                        if not custom:
                                            ui.notify(t('image_notify_no_model_name'), type='warning')
                                            return
                                        # Enregistrer dans CUSTOM_MODELS du backend
                                        try:
                                            from extensions.text2img.image_backend import get_image_backend
                                            backend = get_image_backend()
                                            kie_provider = backend._providers.get('Kie') if backend else None
                                            if kie_provider:
                                                kie_provider.CUSTOM_MODELS[custom] = {
                                                    'payload_format': fmt,
                                                    'nsfw': True,
                                                    'credits': '?',
                                                    'type': 'img2img'
                                                }
                                        except Exception as e:
                                            print(f'[KIE-CUSTOM-I2I] Erreur enregistrement backend: {e}')
                                        # Ajouter à la liste UI
                                        if custom not in img2img_model_select.options:
                                            img2img_model_select.options.append(custom)
                                        img2img_model_select.value = custom
                                        img2img_model_select.update()
                                        fmt_label = {
                                            'format_A': 'A (aspect_ratio)',
                                            'format_A+': 'A+ (aspect_ratio+resolution)',
                                            'format_B': 'B (image_size enum)',
                                            'format_C': 'C (image_size ratio)',
                                        }.get(fmt, fmt)
                                        ui.notify(t('image_notify_custom_i2i_added', model=custom, fmt=fmt_label), type='positive')
                                        custom_img2img_input.value = ''

                                    ui.button(
                                        icon='add',
                                        on_click=add_custom_img2img_model
                                    ).props('flat dense').classes('text-blue-400').tooltip(t('image_tooltip_add_i2i_model'))
                
                img2img_provider_select.on_value_change(lambda e: update_custom_img2img_visibility())
                update_custom_img2img_visibility()
                    
                # Handler pour changer de provider
                def on_img2img_provider_change(e):
                    new_provider = e.value
                    new_models = get_models_for_provider(new_provider)
                    new_model_options = list(new_models.keys())
                    img2img_model_select.options = new_model_options
                    if new_model_options:
                        img2img_model_select.value = new_model_options[0]
                    img2img_provider_info.text = IMG2IMG_PROVIDERS.get(new_provider, {}).get('info', '')
                    # Rebuild params pour le nouveau modèle
                    if new_model_options:
                        build_model_params(new_model_options[0], new_provider)
                
                img2img_provider_select.on_value_change(on_img2img_provider_change)
                
                # Container dynamique pour les paramètres spécifiques au modèle
                img2img_params_container = ui.column().classes('w-full mt-3 gap-2')
                
                # Dictionnaire pour stocker les références aux contrôles dynamiques
                dynamic_controls = {}
                
                def build_model_params(model_name: str, provider: str = None):
                    """Construit les contrôles UI selon les paramètres du modèle"""
                    img2img_params_container.clear()
                    dynamic_controls.clear()
                    
                    def _safe_size_value(options, config_key='ws_size', default='1024*1024'):
                        """Retourne une valeur de taille valide pour ui.select"""
                        saved = img_config.get(config_key, default)
                        # options peut etre une liste ou un dict
                        valid_keys = list(options.keys()) if isinstance(options, dict) else options
                        if saved in valid_keys:
                            return saved
                        return default if default in valid_keys else valid_keys[0]
                    
                    # Déterminer le provider actuel si non fourni
                    if provider is None:
                        provider = img2img_provider_select.value
                    
                    # Récupérer les infos du modèle du bon dictionnaire
                    models_dict = get_models_for_provider(provider)
                    model_info = models_dict.get(model_name, {})
                    
                    with img2img_params_container:
                        with ui.row().classes('gap-4 items-center w-full flex-wrap'):
                            # === WAVESPEED SEEDREAM V4.5 EDIT - Taille + Format ===
                            if model_name == "bytedance/seedream-v4.5/edit":
                                with ui.column().classes('gap-2 w-full'):
                                    with ui.row().classes('gap-4 items-center w-full flex-wrap'):
                                        ui.label(t('image_label_size_icon')).classes('text-sm font-semibold')
                                        _seedream45_sizes = {
                                                '2048*2048': '2K (1:1)',
                                                '2560*1440': '2.5K (16:9)',
                                                '1440*2560': '2.5K (9:16)',
                                                '3072*3072': '3K (1:1)',
                                                '3840*2160': '4K (16:9)',
                                                '2160*3840': '4K (9:16)',
                                                '4096*4096': '4K (1:1)'
                                        }
                                        dynamic_controls['size'] = ui.select(
                                            label=t('image_label_size'),
                                            options=_seedream45_sizes,
                                            value=_safe_size_value(_seedream45_sizes, 'img2img_size', '2048*2048')
                                        ).classes('w-36').tooltip(t('image_tooltip_size_resolution'))
                                        
                                        ui.label(t('image_label_format')).classes('text-sm ml-2')
                                        dynamic_controls['output_format'] = ui.select(
                                            label=t('image_label_format'),
                                            options=['jpeg', 'png', 'webp'],
                                            value=img_config.get('img2img_output_format', 'jpeg')
                                        ).classes('w-24').tooltip(t('image_tooltip_format_output'))
                            
                            # === WAVESPEED SEEDREAM V4 EDIT - Taille + Format ===
                            elif model_name == "bytedance/seedream-v4/edit":
                                ui.label(t('image_label_size_icon')).classes('text-sm font-semibold')
                                _seedream4_sizes = {
                                        '2048*2048': '2K (1:1)',
                                        '2560*1440': '2.5K (16:9)',
                                        '1440*2560': '2.5K (9:16)',
                                        '3072*3072': '3K (1:1)'
                                }
                                dynamic_controls['size'] = ui.select(
                                    label=t('image_label_size'),
                                    options=_seedream4_sizes,
                                    value=_safe_size_value(_seedream4_sizes, 'img2img_size', '2048*2048')
                                ).classes('w-36').tooltip(t('image_tooltip_size_resolution'))
                                
                                ui.label(t('image_label_format')).classes('text-sm ml-2')
                                dynamic_controls['output_format'] = ui.select(
                                    label=t('image_label_format'),
                                    options=['jpeg', 'png', 'webp'],
                                    value=img_config.get('img2img_output_format', 'jpeg')
                                ).classes('w-24').tooltip(t('image_tooltip_format_output'))
                            
                            # === SEEDREAM 4.5 (KIE) - Format + Qualité ===
                            elif model_name == "seedream/4.5-edit":
                                ui.label(t('image_label_format_icon')).classes('text-sm font-semibold')
                                dynamic_controls['aspect_ratio'] = ui.select(
                                    label=t('image_label_format'),
                                    options=['1:1', '16:9', '9:16', '4:3', '3:4', '3:2', '2:3'],
                                    value=img_config.get('img2img_aspect_ratio', '1:1')
                                ).classes('w-28').tooltip(t('image_tooltip_aspect_ratio'))
                                
                                ui.label(t('image_label_quality')).classes('text-sm ml-2')
                                dynamic_controls['quality'] = ui.select(
                                    label=t('image_label_quality'),
                                    options=['basic', 'high'],
                                    value=img_config.get('img2img_quality', 'basic').lower()
                                ).classes('w-28').tooltip(t('image_tooltip_quality_2k_4k'))
                            
                            elif model_name == "gpt-image/1.5-image-to-image":
                                ui.label(t('image_label_format_icon')).classes('text-sm font-semibold')
                                dynamic_controls['aspect_ratio'] = ui.select(
                                    label=t('image_label_format'),
                                    options=['1:1', '16:9', '9:16', '4:3', '3:4', '3:2', '2:3'],
                                    value=img_config.get('img2img_aspect_ratio', '1:1')
                                ).classes('w-28').tooltip(t('image_tooltip_aspect_ratio'))
                                
                                ui.label(t('image_label_quality')).classes('text-sm ml-2')
                                dynamic_controls['quality'] = ui.select(
                                    label=t('image_label_quality'),
                                    options=['low', 'medium', 'high'],
                                    value=img_config.get('img2img_quality_gpt', 'medium')
                                ).classes('w-28').tooltip(t('image_tooltip_quality_openai'))
                            
                            # === SEEDREAM V4 - Paramètres spécifiques ===
                            elif model_name == "bytedance/seedream-v4-edit":
                                ui.label(t('image_label_format')).classes('text-sm')
                                dynamic_controls['image_size'] = ui.select(
                                    label=t('image_label_format'),
                                    options=['square_hd', 'portrait_4_3', 'landscape_16_9', 'portrait_hd', 'landscape_hd'],
                                    value=img_config.get('img2img_image_size', 'square_hd')
                                ).classes('w-40')
                                
                                ui.label(t('image_label_resolution')).classes('text-sm ml-2')
                                dynamic_controls['image_resolution'] = ui.select(
                                    label=t('image_label_resolution'),
                                    options=['1K', '2K'],
                                    value=img_config.get('img2img_image_resolution', '1K')
                                ).classes('w-24')
                                
                                ui.label(t('image_label_variants')).classes('text-sm ml-2')
                                dynamic_controls['max_images_output'] = ui.number(
                                    label=t('image_label_nb'),
                                    value=img_config.get('img2img_max_images', 1),
                                    min=1, max=4
                                ).classes('w-20')
                            
                            # === FLUX-2 - Format + Résolution ===
                            elif model_name == "flux-2/pro-image-to-image":
                                ui.label(t('image_label_format_icon')).classes('text-sm font-semibold')
                                dynamic_controls['aspect_ratio'] = ui.select(
                                    label=t('image_label_format'),
                                    options=['1:1', '16:9', '9:16', '4:3', '3:4', '3:2', '2:3', '21:9', '9:21'],
                                    value=img_config.get('img2img_aspect_ratio', '1:1')
                                ).classes('w-28').tooltip(t('image_tooltip_aspect_ratio'))
                                
                                ui.label(t('image_label_resolution')).classes('text-sm ml-2')
                                dynamic_controls['resolution'] = ui.select(
                                    label=t('image_label_resolution'),
                                    options=['1K', '2K'],
                                    value=img_config.get('img2img_resolution', '1K')
                                ).classes('w-24').tooltip(t('image_tooltip_resolution_1k_2k'))
                            
                            # === NANO-BANANA - Format + Résolution + Format sortie ===
                            elif model_name == "nano-banana-pro-img2img":
                                ui.label(t('image_label_format_icon')).classes('text-sm font-semibold')
                                dynamic_controls['aspect_ratio'] = ui.select(
                                    label=t('image_label_format'),
                                    options=['1:1', '16:9', '9:16', '4:3', '3:4', '3:2', '2:3'],
                                    value=img_config.get('img2img_aspect_ratio', '1:1')
                                ).classes('w-28').tooltip(t('image_tooltip_aspect_ratio'))
                                
                                ui.label(t('image_label_resolution')).classes('text-sm ml-2')
                                dynamic_controls['resolution'] = ui.select(
                                    label=t('image_label_resolution'),
                                    options=['1K', '2K', '4K'],
                                    value=img_config.get('img2img_resolution', '1K')
                                ).classes('w-24').tooltip(t('image_tooltip_resolution_1k_2k_4k'))
                                
                                ui.label(t('image_label_output')).classes('text-sm ml-2')
                                dynamic_controls['output_format'] = ui.select(
                                    label=t('image_label_output_format'),
                                    options=['png', 'jpeg', 'webp'],
                                    value=img_config.get('img2img_output_format', 'png')
                                ).classes('w-24').tooltip(t('image_tooltip_png_formats'))
                            
                            # === QWEN IMAGE-TO-IMAGE - Strength + Safety + Params avancés ===
                            elif model_name == "qwen/image-to-image":
                                with ui.column().classes('gap-2 w-full'):
                                    # Ligne 1: Force + Safety + Format
                                    with ui.row().classes('gap-4 items-center w-full flex-wrap'):
                                        ui.label(t('image_label_strength')).classes('text-sm font-semibold')
                                        dynamic_controls['strength'] = ui.slider(
                                            min=0.1, max=1.0, step=0.05,
                                            value=img_config.get('img2img_strength', 0.8)
                                        ).props('label-always').classes('w-40').tooltip(t('image_tooltip_strength_detail'))
                                        
                                        dynamic_controls['enable_safety_checker'] = ui.checkbox(
                                            '🛡️ Safe Mode',
                                            value=img_config.get('img2img_safety', True)
                                        ).tooltip(t('image_tooltip_qwen_filter'))
                                        
                                        ui.label(t('image_label_format')).classes('text-sm ml-2')
                                        dynamic_controls['output_format'] = ui.select(
                                            label=t('image_label_format'),
                                            options=['png', 'jpeg', 'webp'],
                                            value=img_config.get('img2img_output_format', 'png')
                                        ).classes('w-24').tooltip(t('image_tooltip_png_formats_compact'))
                                    
                                    # Ligne 2: Steps + Guidance + Negative
                                    with ui.row().classes('gap-4 items-center w-full flex-wrap'):
                                        ui.label(t('image_label_steps')).classes('text-sm')
                                        dynamic_controls['num_inference_steps'] = ui.number(
                                            label=t('image_label_steps'),
                                            value=img_config.get('img2img_steps', 30),
                                            min=10, max=50
                                        ).classes('w-20').tooltip(t('image_tooltip_steps'))
                                        
                                        ui.label(t('image_label_guidance')).classes('text-sm ml-2')
                                        dynamic_controls['guidance_scale'] = ui.number(
                                            label=t('image_label_cfg'),
                                            value=img_config.get('img2img_guidance', 2.5),
                                            min=1.0, max=10.0, step=0.5
                                        ).classes('w-20').tooltip(t('image_tooltip_cfg'))
                                        
                                        ui.label(t('image_label_negative')).classes('text-sm ml-2')
                                        dynamic_controls['negative_prompt'] = ui.input(
                                            label=t('image_label_negative_prompt'),
                                            value=img_config.get('img2img_negative', 'blurry, ugly')
                                        ).classes('flex-1').tooltip(t('image_tooltip_negative_prompt'))
                                    
                                    ui.label(t('image_label_max_1_image')).classes('text-xs text-gray-500')
                        
                            # === QWEN IMAGE-EDIT - Format + Safety + Params avancés ===
                            elif model_name == "qwen/image-edit":
                                with ui.column().classes('gap-2 w-full'):
                                    # Ligne 1: Format + Safety + Output Format
                                    with ui.row().classes('gap-4 items-center w-full flex-wrap'):
                                        ui.label(t('image_label_format_icon')).classes('text-sm font-semibold')
                                        dynamic_controls['image_size'] = ui.select(
                                            label=t('image_label_format'),
                                            options=['square_hd', 'portrait_4_3', 'landscape_4_3', 'portrait_16_9', 'landscape_16_9'],
                                            value=img_config.get('img2img_image_size', 'square_hd')
                                        ).classes('w-40').tooltip(t('image_tooltip_aspect_ratio_seedream'))
                                        
                                        dynamic_controls['enable_safety_checker'] = ui.checkbox(
                                            '🛡️ Safe Mode',
                                            value=img_config.get('img2img_safety', True)
                                        ).tooltip(t('image_tooltip_qwen_filter'))
                                        
                                        ui.label(t('image_label_output')).classes('text-sm ml-2')
                                        dynamic_controls['output_format'] = ui.select(
                                            label=t('image_label_format'),
                                            options=['png', 'jpeg', 'webp'],
                                            value=img_config.get('img2img_output_format', 'png')
                                        ).classes('w-24').tooltip(t('image_tooltip_png_formats_compact'))
                                    
                                    # Ligne 2: Steps + Guidance + Negative
                                    with ui.row().classes('gap-4 items-center w-full flex-wrap'):
                                        ui.label(t('image_label_steps')).classes('text-sm')
                                        dynamic_controls['num_inference_steps'] = ui.number(
                                            label=t('image_label_steps'),
                                            value=img_config.get('img2img_steps', 25),
                                            min=10, max=50
                                        ).classes('w-20').tooltip(t('image_tooltip_steps'))
                                        
                                        ui.label(t('image_label_guidance')).classes('text-sm ml-2')
                                        dynamic_controls['guidance_scale'] = ui.number(
                                            label=t('image_label_cfg'),
                                            value=img_config.get('img2img_guidance', 4.0),
                                            min=1.0, max=10.0, step=0.5
                                        ).classes('w-20').tooltip(t('image_tooltip_cfg'))
                                        
                                        ui.label(t('image_label_negative')).classes('text-sm ml-2')
                                        dynamic_controls['negative_prompt'] = ui.input(
                                            label=t('image_label_negative_prompt'),
                                            value=img_config.get('img2img_negative', 'blurry, ugly')
                                        ).classes('flex-1').tooltip(t('image_tooltip_negative_prompt'))
                                    
                                    ui.label(t('image_label_max_1_image')).classes('text-xs text-gray-500')
                            
                            # ===============================================
                            # === WAVESPEED I2I MODELS (Unfiltered/Spicy) ===
                            # ===============================================
                            
                            # === Z-IMAGE TURBO I2I - Ultra rapide ===
                            elif model_name == "wavespeed-ai/z-image-turbo/image-to-image":
                                with ui.column().classes('gap-2 w-full'):
                                    with ui.row().classes('gap-4 items-center w-full flex-wrap'):
                                        ui.label(t('image_label_size_icon')).classes('text-sm font-semibold')
                                        _zturbo_sizes = ['512*512', '768*768', '1024*1024', '1024*768', '768*1024']
                                        dynamic_controls['size'] = ui.select(
                                            label=t('image_label_size'),
                                            options=_zturbo_sizes,
                                            value=_safe_size_value(_zturbo_sizes)
                                        ).classes('w-32').tooltip(t('image_tooltip_size_wh_format'))
                                        
                                        ui.label(t('image_label_strength')).classes('text-sm')
                                        dynamic_controls['strength'] = ui.slider(
                                            min=0.1, max=1.0, step=0.05,
                                            value=img_config.get('ws_strength', 0.7)
                                        ).props('label-always').classes('w-40').tooltip(t('image_tooltip_strength'))
                                        
                                        ui.label(t('image_label_seed')).classes('text-sm ml-2')
                                        dynamic_controls['seed'] = ui.number(
                                            label=t('image_label_seed'),
                                            value=img_config.get('ws_seed', -1),
                                            min=-1, max=9999999
                                        ).classes('w-24').tooltip('-1=aléatoire')
                                    
                                    ui.label(t('image_info_z_turbo')).classes('text-xs text-green-400')
                            
                            # === HIGGSFIELD SOUL I2I - Style réaliste/artistique ===
                            elif model_name == "higgsfield/soul/image-to-image":
                                with ui.column().classes('gap-2 w-full'):
                                    with ui.row().classes('gap-4 items-center w-full flex-wrap'):
                                        ui.label(t('image_label_size_icon')).classes('text-sm font-semibold')
                                        _higgs_sizes = ['512*512', '768*768', '1024*1024', '1024*768', '768*1024', '1280*720', '720*1280']
                                        dynamic_controls['size'] = ui.select(
                                            label=t('image_label_size'),
                                            options=_higgs_sizes,
                                            value=_safe_size_value(_higgs_sizes)
                                        ).classes('w-32')
                                        
                                        ui.label(t('image_label_strength')).classes('text-sm')
                                        dynamic_controls['strength'] = ui.slider(
                                            min=0.1, max=1.0, step=0.05,
                                            value=img_config.get('ws_strength', 0.75)
                                        ).props('label-always').classes('w-40')
                                        
                                        ui.label(t('image_label_seed')).classes('text-sm ml-2')
                                        dynamic_controls['seed'] = ui.number(
                                            label=t('image_label_seed'),
                                            value=img_config.get('ws_seed', -1),
                                            min=-1, max=9999999
                                        ).classes('w-24')
                                    
                                    ui.label(t('image_info_higgsfield')).classes('text-xs text-purple-400')
                            
                            # === FLUX KONTEXT DEV - Édition par instruction ===
                            elif model_name == "wavespeed-ai/flux-kontext-dev":
                                with ui.column().classes('gap-2 w-full'):
                                    with ui.row().classes('gap-4 items-center w-full flex-wrap'):
                                        ui.label(t('image_label_size_icon')).classes('text-sm font-semibold')
                                        _kontext_sizes = ['512*512', '768*768', '1024*1024', '1280*720', '720*1280', '1536*1024', '1024*1536']
                                        dynamic_controls['size'] = ui.select(
                                            label=t('image_label_size'),
                                            options=_kontext_sizes,
                                            value=_safe_size_value(_kontext_sizes)
                                        ).classes('w-32')
                                        
                                        ui.label(t('image_label_steps')).classes('text-sm')
                                        dynamic_controls['num_inference_steps'] = ui.number(
                                            label=t('image_label_steps'),
                                            value=img_config.get('ws_steps', 28),
                                            min=10, max=50
                                        ).classes('w-20')
                                        
                                        ui.label(t('image_label_guidance')).classes('text-sm ml-2')
                                        dynamic_controls['guidance_scale'] = ui.number(
                                            label=t('image_label_cfg'),
                                            value=img_config.get('ws_guidance', 3.5),
                                            min=1.0, max=10.0, step=0.5
                                        ).classes('w-20')
                                    
                                    ui.label(t('image_info_flux_kontext')).classes('text-xs text-blue-400')
                            
                            # === FACE SWAP - Échange de visage ===
                            elif model_name == "wavespeed-ai/image-face-swap":
                                with ui.column().classes('gap-2 w-full'):
                                    ui.label(t('image_label_faceswap_title')).classes('text-sm font-semibold text-pink-400')
                                    ui.label(t('image_label_faceswap_req')).classes('text-xs text-yellow-400')
                                    ui.label(t('image_label_faceswap_tip')).classes('text-xs text-gray-400')
                                    ui.label(t('image_label_faceswap_cost')).classes('text-xs text-green-400')
                            
                            # === HEAD SWAP - Échange de tête ===
                            elif model_name == "wavespeed-ai/image-head-swap":
                                with ui.column().classes('gap-2 w-full'):
                                    ui.label(t('image_label_headswap_title')).classes('text-sm font-semibold text-orange-400')
                                    ui.label(t('image_label_headswap_req')).classes('text-xs text-yellow-400')
                                    ui.label(t('image_label_headswap_tip')).classes('text-xs text-gray-400')
                                    ui.label(t('image_label_headswap_cost')).classes('text-xs text-green-400')
                            
                            # === WAN 2.2 I2I - Wan Image Edit ===
                            elif model_name == "wavespeed-ai/wan-2.2/image-to-image":
                                with ui.column().classes('gap-2 w-full'):
                                    with ui.row().classes('gap-4 items-center w-full flex-wrap'):
                                        ui.label(t('image_label_size_icon')).classes('text-sm font-semibold')
                                        _wan22_sizes = ['512*512', '768*768', '1024*1024', '1280*720', '720*1280']
                                        dynamic_controls['size'] = ui.select(
                                            label=t('image_label_size'),
                                            options=_wan22_sizes,
                                            value=_safe_size_value(_wan22_sizes)
                                        ).classes('w-32')
                                        
                                        ui.label(t('image_label_strength')).classes('text-sm')
                                        dynamic_controls['strength'] = ui.slider(
                                            min=0.1, max=1.0, step=0.05,
                                            value=img_config.get('ws_strength', 0.7)
                                        ).props('label-always').classes('w-40')
                                        
                                        ui.label(t('image_label_seed')).classes('text-sm ml-2')
                                        dynamic_controls['seed'] = ui.number(
                                            label=t('image_label_seed'),
                                            value=img_config.get('ws_seed', -1),
                                            min=-1, max=9999999
                                        ).classes('w-24')
                                    
                                    ui.label(t('image_info_wan22')).classes('text-xs text-cyan-400')
                            
                            # === QWEN IMAGE EDIT (WaveSpeed) ===
                            elif model_name == "wavespeed-ai/qwen-image-edit":
                                with ui.column().classes('gap-2 w-full'):
                                    with ui.row().classes('gap-4 items-center w-full flex-wrap'):
                                        ui.label(t('image_label_size_icon')).classes('text-sm font-semibold')
                                        _qwen_sizes = ['512*512', '768*768', '1024*1024', '1280*720', '720*1280']
                                        dynamic_controls['size'] = ui.select(
                                            label=t('image_label_size'),
                                            options=_qwen_sizes,
                                            value=_safe_size_value(_qwen_sizes)
                                        ).classes('w-32')
                                        
                                        ui.label(t('image_label_steps')).classes('text-sm')
                                        dynamic_controls['num_inference_steps'] = ui.number(
                                            label=t('image_label_steps'),
                                            value=img_config.get('ws_steps', 25),
                                            min=10, max=50
                                        ).classes('w-20')
                                        
                                        ui.label(t('image_label_guidance')).classes('text-sm ml-2')
                                        dynamic_controls['guidance_scale'] = ui.number(
                                            label=t('image_label_cfg'),
                                            value=img_config.get('ws_guidance', 4.0),
                                            min=1.0, max=10.0, step=0.5
                                        ).classes('w-20')
                                    
                                    ui.label(t('image_info_qwen_wavespeed')).classes('text-xs text-purple-400')
                            
                            # === LUCY EDIT (Decart) ===
                            elif model_name == "decart/lucy-edit-dev":
                                with ui.column().classes('gap-2 w-full'):
                                    with ui.row().classes('gap-4 items-center w-full flex-wrap'):
                                        ui.label(t('image_label_size_icon')).classes('text-sm font-semibold')
                                        _lucy_sizes = ['512*512', '768*768', '1024*1024', '1280*720', '720*1280']
                                        dynamic_controls['size'] = ui.select(
                                            label=t('image_label_size'),
                                            options=_lucy_sizes,
                                            value=_safe_size_value(_lucy_sizes)
                                        ).classes('w-32')
                                        
                                        ui.label(t('image_label_strength')).classes('text-sm')
                                        dynamic_controls['strength'] = ui.slider(
                                            min=0.1, max=1.0, step=0.05,
                                            value=img_config.get('ws_strength', 0.75)
                                        ).props('label-always').classes('w-40')
                                        
                                        ui.label(t('image_label_seed')).classes('text-sm ml-2')
                                        dynamic_controls['seed'] = ui.number(
                                            label=t('image_label_seed'),
                                            value=img_config.get('ws_seed', -1),
                                            min=-1, max=9999999
                                        ).classes('w-24')
                                    
                                    ui.label(t('image_info_lucy_edit')).classes('text-xs text-pink-400')
                            
                            # ===============================================

                            # ===============================================
                            # === ATLASCLOUD I2I - Paramètres universels   ===
                            # ===============================================
                            elif provider == "AtlasCloud":
                                with ui.column().classes('gap-2 w-full'):
                                    with ui.row().classes('gap-4 items-center w-full flex-wrap'):
                                        ui.label(t('image_label_size_icon')).classes('text-sm font-semibold')
                                        _atlas_sizes = {
                                            '1024*1024': '1K (1:1)',
                                            '1280*720':  '1.3K (16:9)',
                                            '720*1280':  '1.3K (9:16)',
                                            '1024*768':  '1K (4:3)',
                                            '768*1024':  '1K (3:4)',
                                            '1536*1024': 'HD (3:2)',
                                            '1024*1536': 'HD (2:3)',
                                            '2048*2048': '2K (1:1)',
                                            '2560*1440': '2.5K (16:9)',
                                            '1440*2560': '2.5K (9:16)',
                                        }
                                        dynamic_controls['size'] = ui.select(
                                            label=t('image_label_size'),
                                            options=_atlas_sizes,
                                            value=_safe_size_value(_atlas_sizes, 'atlas_i2i_size', '1024*1024')
                                        ).classes('w-40').tooltip(t('image_tooltip_size_wh'))

                                        ui.label(t('image_label_strength')).classes('text-sm')
                                        dynamic_controls['strength'] = ui.slider(
                                            min=0.1, max=1.0, step=0.05,
                                            value=img_config.get('atlas_i2i_strength', 0.75)
                                        ).props('label-always').classes('w-40').tooltip(
                                            'Intensité de transformation: 0.1=léger, 0.5=équilibré, 1.0=radical'
                                        )

                                    with ui.row().classes('gap-4 items-center w-full flex-wrap'):
                                        ui.label(t('image_label_batch_seed')).classes('text-sm font-semibold')
                                        dynamic_controls['seed'] = ui.number(
                                            label=t('image_label_seed'),
                                            value=img_config.get('atlas_i2i_seed', -1),
                                            min=-1, max=9999999
                                        ).classes('w-28').tooltip('-1 = aléatoire')

                                        ui.label(t('image_label_negative_icon')).classes('text-sm')
                                        dynamic_controls['negative_prompt'] = ui.input(
                                            label=t('image_label_negative_prompt'),
                                            value=img_config.get('atlas_i2i_negative', 'blurry, ugly, deformed')
                                        ).classes('flex-1').tooltip(t('image_tooltip_negative_prompt_short'))

                                    _atlas_model_info = {
                                        'bytedance/seedream': '🌱 ByteDance Seedream — excellente préservation des détails',
                                        'black-forest-labs/flux-kontext': '✏️ FLUX Kontext — édition par instruction textuelle précise',
                                        'alibaba/qwen-image/edit': '🏮 Qwen-Image Edit — multi-images, suivi instruction avancé',
                                        'alibaba/wan-': '🎨 Wan — édition Alibaba',
                                        'google/nano-banana': '🍌 Nano Banana Google — qualité premium',
                                    }
                                    _info_text = t('image_label_atlascloud_info')
                                    for prefix, desc in _atlas_model_info.items():
                                        if model_name.startswith(prefix):
                                            _info_text = desc
                                            break
                                    ui.label(_info_text).classes('text-xs text-blue-300')

                                    if 'sequential' in model_name:
                                        with ui.row().classes('gap-4 items-center mt-1'):
                                            ui.label(t('image_label_batch_variants')).classes('text-sm')
                                            dynamic_controls['batch_count'] = ui.number(
                                                label=t('image_label_nb'),
                                                value=img_config.get('atlas_i2i_batch', 2),
                                                min=1, max=15
                                            ).classes('w-20').tooltip(t('image_tooltip_seed_sequential'))

                            # === SECTION BATCH COMMUNE (WaveSpeed + Kie) ===
                            # ===============================================
                            # Afficher les contrôles batch pour tous les providers
                            # supportant le paramètre seed (génération multiple)
                            
                            # Liste des modèles connus supportant seed (pour tous providers)
                            # Note: Tous les modèles WaveSpeed I2I supportent seed sauf face/head swap
                            wavespeed_i2i_models = [
                                # Seedream Edit family
                                "bytedance/seedream-v4.5/edit",
                                "bytedance/seedream-v4/edit", 
                                "bytedance/seedream-v4.5/edit-sequential",
                                "bytedance/seedream-v4/edit-sequential",
                                "bytedance/seedream-4.5",
                                "bytedance/seedream-v3.1",
                                "bytedance/seededit-v3",
                                # Z-Image
                                "wavespeed-ai/z-image-turbo/image-to-image",
                                "wavespeed-ai/z-image/turbo-inpaint",
                                # Autres modèles avec seed
                                "higgsfield/soul/image-to-image",
                                "wavespeed-ai/flux-kontext-dev",
                                "wavespeed-ai/flux-fill-dev",
                                "wavespeed-ai/wan-2.2/image-to-image",
                                "wavespeed-ai/qwen-image-edit",
                                "wavespeed-ai/qwen-image/edit-2511-lora",
                                "wavespeed-ai/infinite-you",
                                "wavespeed-ai/seedream-v4",
                                "decart/lucy-edit-dev",
                                # Alibaba & Google
                                "alibaba/wan-2.5/image-edit",
                                "google/nano-banana-pro/edit",
                                "google/nano-banana-pro/edit-ultra",
                            ]
                            
                            # Afficher contrôles batch si modèle supporté
                            if provider == "WaveSpeed" and model_name in wavespeed_i2i_models:
                                with ui.expansion(t('image_expansion_batch')).classes('w-full mt-2').props('dense'):
                                    with ui.row().classes('gap-4 items-center w-full flex-wrap py-2'):
                                        ui.label(t('image_label_batch_seed')).classes('text-sm font-semibold')
                                        dynamic_controls['batch_seed'] = ui.number(
                                            label=t('image_label_seed'),
                                            value=img_config.get('img2img_batch_seed', -1),
                                            min=-1, max=9999999
                                        ).classes('w-28').tooltip('-1 = aléatoire, sinon seed fixe pour reproductibilité')
                                        
                                        ui.label(t('image_label_batch_variants')).classes('text-sm ml-2')
                                        dynamic_controls['batch_count'] = ui.number(
                                            label=t('image_label_nb'),
                                            value=img_config.get('img2img_batch_count', 1),
                                            min=1, max=6
                                        ).classes('w-20').tooltip(t('image_tooltip_seed_count'))
                                        
                                        ui.label(t('image_label_batch_increment')).classes('text-sm ml-2')
                                        dynamic_controls['seed_increment'] = ui.number(
                                            label='+N',
                                            value=img_config.get('img2img_seed_increment', 1),
                                            min=1, max=10
                                        ).classes('w-20').tooltip(t('image_tooltip_seed_gap'))
                                    
                                    ui.label(t('image_label_batch_note')).classes('text-xs text-gray-500')
                
                # Construire les paramètres pour le modèle initial
                build_model_params(current_img2img_model, current_img2img_provider)
                
                # Reconstruire quand le modèle change
                img2img_model_select.on_value_change(lambda e: build_model_params(e.value))
                
                # Info modèle img2img
                img2img_info_label = ui.label('').classes('text-sm mt-2 text-gray-400')
                
                def update_img2img_info():
                    model = img2img_model_select.value
                    provider = img2img_provider_select.value
                    models_dict = get_models_for_provider(provider)
                    info = models_dict.get(model, {})
                    nsfw_icon = "�" if info.get('nsfw') else "🔒"
                    cost_str = f"${info.get('usd', '?')}" if info.get('usd') else f"{info.get('credits', '?')} crédits"
                    img2img_info_label.text = f"{info.get('name', model)} - {nsfw_icon} - {info.get('desc', '')} - {cost_str}/img"
                
                img2img_model_select.on_value_change(lambda e: update_img2img_info())
                update_img2img_info()
                
                ui.label(t('image_label_magic_phrase_i2i')).classes('text-xs text-blue-300 mt-2')
                
                # Note dynamique sur la clé API requise
                api_key_note = ui.label(t('image_label_need_key_kie')).classes('text-xs text-yellow-400')
                
                def update_api_note():
                    provider = img2img_provider_select.value
                    if provider == "WaveSpeed":
                        api_key_note.text = t('image_label_need_key_wavespeed')
                    elif provider == "AtlasCloud":
                        api_key_note.text = t('image_label_need_key_atlascloud')
                    else:
                        api_key_note.text = t('image_label_need_key_kie')
                
                img2img_provider_select.on_value_change(lambda e: update_api_note())
                update_api_note()
                
                # Guide injection conditionnelle
                ui.separator().classes('my-3')
                ui.label(t('image_label_i2i_guide_title')).classes('text-sm font-semibold mb-1')
                
                # Valeur par défaut si vide
                default_guide = t('image_default_i2i_guide')
                
                img2img_guide_textarea = ui.textarea(
                    label=t('image_label_i2i_guide_field'),
                    value=img_config.get('img2img_guide', '') or default_guide,
                    placeholder=t('image_placeholder_i2i_guide')
                ).props('autogrow borderless dense rows=8').classes('w-full').style('font-size: 0.85rem;')
                
                with ui.row().classes('gap-2 mt-1'):
                    def reset_i2i_guide():
                        img2img_guide_textarea.value = t('image_default_i2i_guide')
                        ui.notify(t('image_notify_i2i_guide_reset'), type='info')
                    ui.button(t('image_btn_reset_default'), on_click=reset_i2i_guide).props('flat dense').classes('text-xs')
                
                # Option traduction auto français→anglais
                img2img_auto_translate_switch = ui.checkbox(
                    t('image_check_auto_translate'),
                    value=img_config.get('img2img_auto_translate', True)
                ).tooltip(t('image_tooltip_auto_translate'))
                
                ui.label(t('image_label_i2i_guide_note')).classes('text-xs text-gray-400 mt-1')

            # Section Guide Text-to-Image
            with ui.card().classes('q-dark p-4').style('background: rgba(138, 43, 226, 0.1); border-left: 3px solid #8a2be2;'):
                ui.label(t('image_section_t2i_guide')).classes('font-semibold mb-2').style('color: #8a2be2;')
                ui.label(t('image_label_t2i_guide_subtitle')).classes('text-sm text-gray-400 mb-3')
                
                # Valeur par défaut si vide (optimisé pour z-image)
                default_t2i_guide = t('image_default_t2i_guide')
                
                text2img_guide_textarea = ui.textarea(
                    label=t('image_label_t2i_guide_field'),
                    value=img_config.get('text2img_guide', '') or default_t2i_guide,
                    placeholder=t('image_placeholder_t2i_guide')
                ).props('autogrow borderless dense rows=8').classes('w-full').style('font-size: 0.85rem;')
                
                with ui.row().classes('gap-2 mt-1'):
                    def reset_t2i_guide():
                        text2img_guide_textarea.value = t('image_default_t2i_guide')
                        ui.notify(t('image_notify_t2i_guide_reset'), type='info')
                    ui.button(t('image_btn_reset_default'), on_click=reset_t2i_guide).props('flat dense').classes('text-xs')
                
                ui.label(t('image_label_t2i_guide_note')).classes('text-xs text-gray-400 mt-1')

            # Section Directive Concision
            with ui.card().classes('q-dark p-4').style('background: rgba(255, 165, 0, 0.1); border-left: 3px solid #ffa500;'):
                ui.label(t('image_section_concision')).classes('font-semibold mb-2').style('color: #ffa500;')
                ui.label(t('image_label_concision_subtitle')).classes('text-sm text-gray-400 mb-3')
                
                concision_enabled_check = ui.checkbox(
                    t('image_check_concision'),
                    value=img_config.get('concision_enabled', True)
                ).classes('mb-3')
                ui.label(t('image_label_concision_warn')).classes('text-xs text-yellow-400 mb-2')
                
                # Instruction CHD par défaut
                default_concision = t('image_default_concision')
                
                concision_directive_textarea = ui.textarea(
                    label=t('image_label_concision_field'),
                    value=img_config.get('concision_directive', '') or default_concision,
                    placeholder=t('image_placeholder_concision')
                ).props('autogrow borderless dense rows=10').classes('w-full').style('font-size: 0.85rem;')
                
                with ui.row().classes('gap-2 mt-1'):
                    def reset_concision_directive():
                        concision_directive_textarea.value = t('image_default_concision')
                        ui.notify(t('image_notify_concision_reset'), type='info')
                    ui.button(t('image_btn_reset_default'), on_click=reset_concision_directive).props('flat dense').classes('text-xs')
                
                ui.label(t('image_label_concision_note')).classes('text-xs text-gray-400 mt-1')

            # Section Sauvegarde
            with ui.card().classes('q-dark p-4').style('background: rgba(255,255,255,0.05);'):
                ui.label(t('image_section_options')).classes('font-semibold mb-2')
                
                with ui.column().classes('gap-2'):
                    save_check = ui.checkbox(
                        t('image_check_save'),
                        value=img_config.get('save_images', True)
                    )
                    
                    vision_check = ui.checkbox(
                        t('image_check_vision'),
                        value=img_config.get('ai_can_see_images', False)
                    )
                    
                    # Prompt vision feedback personnalisable
                    ui.label(t('image_label_vision_prompt_title')).classes('text-sm font-medium mt-4 mb-1')
                    
                    default_vision_prompt = t('image_default_vision_prompt')
                    
                    current_vision_prompt = img_config.get('vision_feedback_prompt', '') or default_vision_prompt
                    
                    vision_prompt_textarea = ui.textarea(
                        value=current_vision_prompt,
                        placeholder=t('image_placeholder_vision_prompt')
                    ).props('autogrow borderless rows=7').classes('w-full').style('font-family: monospace; font-size: 12px;')
                    
                    with ui.row().classes('gap-2 mt-2'):
                        def reset_vision_prompt():
                            vision_prompt_textarea.value = default_vision_prompt
                            ui.notify(t('image_notify_vision_reset'), type='info')
                        
                        ui.button(t('image_btn_reset_default'), on_click=reset_vision_prompt).props('flat dense').classes('text-xs')
                        ui.label(t('image_label_vision_prompt_note')).classes('text-xs text-gray-500')

            # Section Compression Vision
            with ui.card().classes('q-dark p-4').style('background: rgba(76, 175, 80, 0.1); border-left: 3px solid #4caf50;'):
                ui.label(t('image_section_compression')).classes('font-semibold mb-2').style('color: #4caf50;')
                ui.label(t('image_label_compression_subtitle')).classes('text-sm text-gray-400 mb-1')
                ui.label(t('image_label_compression_subtitle2')).classes('text-xs text-gray-500 mb-3')
                
                # Options de compression
                vision_compression_options = {
                    400: '400×400 (~50K tokens) - Rapide ⚡',
                    512: '512×512 (~80K tokens) - Équilibré',
                    768: '768×768 (~180K tokens) - Détaillé',
                    1024: '1024×1024 (~320K tokens) - Maximum',
                    0: 'Sans compression - Qualité originale ⚠️'
                }
                
                current_compression = img_config.get('vision_compression', 400)
                
                vision_compression_select = ui.select(
                    label=t('image_label_resolution_max'),
                    options=vision_compression_options,
                    value=current_compression
                ).classes('w-full')
                
                with ui.row().classes('gap-4 mt-3 text-xs text-gray-400'):
                    ui.label(t('image_label_compression_tip1'))
                    ui.label('|')
                    ui.label(t('image_label_compression_tip2'))
                    ui.label('|')
                    ui.label(t('image_label_compression_tip3'))
                
                ui.label(t('image_label_compression_warn')).classes('text-xs text-yellow-400 mt-2')
                
                # Qualité JPEG
                ui.label(t('image_label_jpeg_quality')).classes('text-sm text-gray-300 mt-4 mb-2')
                current_jpeg_quality = img_config.get('vision_jpeg_quality', 85)
                
                vision_jpeg_quality_slider = ui.slider(
                    min=50, max=95, step=5,
                    value=current_jpeg_quality
                ).props('label-always snap').classes('w-full')
                
                # Label dynamique pour expliquer la qualité
                jpeg_quality_label = ui.label().classes('text-xs text-gray-400 mt-1')
                
                def update_jpeg_quality_label():
                    q = vision_jpeg_quality_slider.value
                    if q <= 60:
                        jpeg_quality_label.text = t('image_label_jpeg_max', q=q)
                    elif q <= 75:
                        jpeg_quality_label.text = t('image_label_jpeg_low', q=q)
                    elif q <= 85:
                        jpeg_quality_label.text = t('image_label_jpeg_std', q=q)
                    else:
                        jpeg_quality_label.text = t('image_label_jpeg_high', q=q)
                
                update_jpeg_quality_label()
                vision_jpeg_quality_slider.on_value_change(lambda: update_jpeg_quality_label())

            # Section Boucle Auto-Corrective I2I
            with ui.card().classes('q-dark p-4').style('background: rgba(255, 152, 0, 0.1); border-left: 3px solid #ff9800;'):
                ui.label(t('image_section_autocorrect')).classes('font-semibold mb-2').style('color: #ff9800;')
                ui.label(t('image_label_autocorrect_subtitle')).classes('text-sm text-gray-400 mb-3')
                
                i2i_autocorrect_check = ui.checkbox(
                    t('image_check_autocorrect'),
                    value=img_config.get('i2i_autocorrect_enabled', False)
                ).classes('mb-2')
                ui.label(t('image_label_autocorrect_warn')).classes('text-xs text-yellow-400 mb-3')
                
                with ui.row().classes('gap-4 w-full mb-3'):
                    i2i_max_retries_slider = ui.slider(
                        min=1, max=5, step=1,
                        value=img_config.get('i2i_max_retries', 3)
                    ).props('label-always').classes('w-1/2')
                    ui.label(t('image_label_max_retries')).classes('text-sm self-center')
                    
                    i2i_score_threshold_slider = ui.slider(
                        min=1, max=10, step=1,
                        value=img_config.get('i2i_score_threshold', 6)
                    ).props('label-always').classes('w-1/2')
                    ui.label(t('image_label_score_threshold')).classes('text-sm self-center')
                
                i2i_web_tips_check = ui.checkbox(
                    t('image_check_web_tips'),
                    value=img_config.get('i2i_web_tips_enabled', True)
                ).classes('mb-2')
                ui.label(t('image_label_web_tips_note')).classes('text-xs text-gray-400 mb-3')
                
                ui.label(t('image_label_i2i_analysis_title')).classes('text-sm font-medium mt-2 mb-1')
                
                # Default du prompt d'analyse i2i
                _default_i2i_analysis_prompt = t('image_default_i2i_analysis')
                current_i2i_analysis = img_config.get('i2i_analysis_prompt', '') or _default_i2i_analysis_prompt
                
                i2i_analysis_prompt_textarea = ui.textarea(
                    value=current_i2i_analysis,
                    placeholder=t('image_placeholder_i2i_analysis')
                ).props('autogrow borderless rows=12').classes('w-full').style('font-family: monospace; font-size: 12px;')
                
                with ui.row().classes('gap-2 mt-2'):
                    def reset_i2i_analysis_prompt():
                        i2i_analysis_prompt_textarea.value = _default_i2i_analysis_prompt
                        ui.notify(t('image_notify_i2i_analysis_reset'), type='info')
                    
                    ui.button(t('image_btn_reset_default'), on_click=reset_i2i_analysis_prompt).props('flat dense').classes('text-xs')
                    ui.label(t('image_label_i2i_analysis_note')).classes('text-xs text-gray-500')

            # Résumé des providers
            with ui.card().classes('q-dark p-4').style('background: rgba(212, 175, 55, 0.1); border-left: 3px solid #d4af37;'):
                ui.label(t('image_section_comparison')).classes('font-semibold mb-3').style('color: #d4af37;')
                
                with ui.element('table').classes('w-full text-sm'):
                    with ui.element('tr').classes('border-b border-gray-600'):
                        ui.element('th').classes('text-left p-2').props('width=150').add_slot('default', 'Provider / Modèle')
                        ui.element('th').classes('text-left p-2').add_slot('default', 'Filtre')
                        ui.element('th').classes('text-left p-2').add_slot('default', 'Qualité')
                        ui.element('th').classes('text-left p-2').add_slot('default', 'Coût')
                    
                    with ui.element('tr').classes('border-b border-gray-700'):
                        ui.element('td').classes('p-2 font-medium').add_slot('default', '🔥 GROK')
                        ui.element('td').classes('p-2 text-green-400').add_slot('default', '✅ Spicy')
                        ui.element('td').classes('p-2').add_slot('default', '⭐⭐⭐⭐')
                        ui.element('td').classes('p-2').add_slot('default', '~$0.02/img')
                    
                    with ui.element('tr').classes('border-b border-gray-700'):
                        ui.element('td').classes('p-2 font-medium').add_slot('default', '🎨 OpenAI')
                        ui.element('td').classes('p-2 text-red-400').add_slot('default', '❌ Censuré')
                        ui.element('td').classes('p-2').add_slot('default', '⭐⭐⭐⭐⭐')
                        ui.element('td').classes('p-2').add_slot('default', '~$0.04/img')
                    
                    with ui.element('tr').classes('border-b border-gray-700'):
                        ui.element('td').classes('p-2 font-medium').add_slot('default', '🌐 Google')
                        ui.element('td').classes('p-2 text-yellow-400').add_slot('default', '⚠️ Modéré')
                        ui.element('td').classes('p-2').add_slot('default', '⭐⭐⭐⭐')
                        ui.element('td').classes('p-2').add_slot('default', '~$0.02/img')
                
                # Section Kie.ai détaillée
                ui.label(t('image_label_kie_models')).classes('font-semibold mt-4 mb-2').style('color: #a855f7;')
                
                with ui.element('table').classes('w-full text-sm'):
                    with ui.element('tr').classes('border-b border-gray-600'):
                        ui.element('th').classes('text-left p-2').props('width=180').add_slot('default', 'Modèle')
                        ui.element('th').classes('text-left p-2').add_slot('default', 'Filtre')
                        ui.element('th').classes('text-left p-2').add_slot('default', 'Description')
                        ui.element('th').classes('text-left p-2').add_slot('default', 'Coût')
                    
                    with ui.element('tr').classes('border-b border-gray-700'):
                        ui.element('td').classes('p-2 font-medium text-purple-300').add_slot('default', 'z-image')
                        ui.element('td').classes('p-2 text-green-400').add_slot('default', '✅')
                        ui.element('td').classes('p-2 text-gray-400').add_slot('default', 'Ultra rapide, 6B params')
                        ui.element('td').classes('p-2 text-green-300').add_slot('default', '$0.004')
                    
                    with ui.element('tr').classes('border-b border-gray-700'):
                        ui.element('td').classes('p-2 font-medium text-purple-300').add_slot('default', 'bytedance/seedream')
                        ui.element('td').classes('p-2 text-yellow-400').add_slot('default', '⚠️')
                        ui.element('td').classes('p-2 text-gray-400').add_slot('default', 'Seedream 3.0 artistique')
                        ui.element('td').classes('p-2').add_slot('default', '$0.02')
                    
                    with ui.element('tr').classes('border-b border-gray-700'):
                        ui.element('td').classes('p-2 font-medium text-purple-300').add_slot('default', 'bytedance/seedream-v4')
                        ui.element('td').classes('p-2 text-yellow-400').add_slot('default', '⚠️')
                        ui.element('td').classes('p-2 text-gray-400').add_slot('default', '⭐ Seedream 4.0 - Meilleur Q/P')
                        ui.element('td').classes('p-2 text-green-300').add_slot('default', '$0.025')
                    
                    with ui.element('tr').classes('border-b border-gray-700'):
                        ui.element('td').classes('p-2 font-medium text-purple-300').add_slot('default', 'flux-2/pro-text-to-image')
                        ui.element('td').classes('p-2 text-green-400').add_slot('default', '✅')
                        ui.element('td').classes('p-2 text-gray-400').add_slot('default', 'Haute qualité photoréaliste')
                        ui.element('td').classes('p-2').add_slot('default', '$0.025')
                    
                    with ui.element('tr').classes('border-b border-gray-700'):
                        ui.element('td').classes('p-2 font-medium text-purple-300').add_slot('default', 'seedream-4.5')
                        ui.element('td').classes('p-2 text-yellow-400').add_slot('default', '⚠️')
                        ui.element('td').classes('p-2 text-gray-400').add_slot('default', 'ByteDance 4K précis')
                        ui.element('td').classes('p-2').add_slot('default', '$0.032')
                    
                    with ui.element('tr').classes('border-b border-gray-700'):
                        ui.element('td').classes('p-2 font-medium text-purple-300').add_slot('default', 'nano-banana-pro')
                        ui.element('td').classes('p-2 text-red-400').add_slot('default', '❌')
                        ui.element('td').classes('p-2 text-gray-400').add_slot('default', 'Google DeepMind 2K')
                        ui.element('td').classes('p-2').add_slot('default', '$0.09')
                    
                    with ui.element('tr'):
                        ui.element('td').classes('p-2 font-medium text-purple-300').add_slot('default', 'grok-imagine/text-to-image')
                        ui.element('td').classes('p-2 text-green-400').add_slot('default', '✅')
                        ui.element('td').classes('p-2 text-gray-400').add_slot('default', 'xAI via Kie')
                        ui.element('td').classes('p-2').add_slot('default', '$0.10')

        # Boutons d'action
        with ui.row().classes('gap-2 mt-4 justify-end w-full'):
            ui.button(t('image_btn_cancel'), on_click=d.close).classes('action-button')

            def save_config():
                # Sauvegarder les clés API dans le vault
                vault = sm.settings.get('api_keys_vault', {})
                keys_updated = []
                
                for provider, key_input in api_key_inputs.items():
                    new_key = key_input.value.strip() if key_input.value else ''
                    old_key = vault.get(provider, '')
                    
                    if new_key and new_key != old_key:
                        vault[provider] = new_key
                        keys_updated.append(provider)
                    elif new_key == '' and old_key:
                        # Ne pas supprimer une clé existante si le champ est vide
                        pass
                    elif new_key:
                        vault[provider] = new_key
                
                sm.settings['api_keys_vault'] = vault
                
                if keys_updated:
                    print(f"[IMAGE-CONFIG] 🔑 Clés API mises à jour: {', '.join(keys_updated)}")
                
                # Construire nouvelle config
                new_config = {
                    'enabled': enabled_check.value,
                    'provider': provider_select.value,
                    'model': model_select.value,
                    'width': int(width_input.value),
                    'height': int(height_input.value),
                    'safe_mode': safe_mode_check.value,
                    'save_images': save_check.value,
                    'ai_can_see_images': vision_check.value,
                    'vision_feedback_prompt': vision_prompt_textarea.value,
                    'vision_compression': vision_compression_select.value,
                    'vision_jpeg_quality': vision_jpeg_quality_slider.value,
                    # Configuration Image-to-Image
                    'img2img_enabled': img2img_enabled_check.value,
                    'img2img_provider': img2img_provider_select.value,
                    'img2img_model': img2img_model_select.value,
                    'img2img_guide': img2img_guide_textarea.value,
                    'img2img_auto_translate': img2img_auto_translate_switch.value,
                    # Guide Text-to-Image
                    'text2img_guide': text2img_guide_textarea.value,
                    # Boucle auto-corrective I2I
                    'i2i_autocorrect_enabled': i2i_autocorrect_check.value,
                    'i2i_max_retries': int(i2i_max_retries_slider.value),
                    'i2i_score_threshold': int(i2i_score_threshold_slider.value),
                    'i2i_web_tips_enabled': i2i_web_tips_check.value,
                    'i2i_analysis_prompt': i2i_analysis_prompt_textarea.value,
                    # Directive de concision
                    'concision_enabled': concision_enabled_check.value,
                    'concision_directive': concision_directive_textarea.value,
                    # Paramètres dynamiques selon le modèle sélectionné
                    'img2img_aspect_ratio': dynamic_controls['aspect_ratio'].value if 'aspect_ratio' in dynamic_controls else img_config.get('img2img_aspect_ratio', '1:1'),
                    'img2img_quality': dynamic_controls['quality'].value if 'quality' in dynamic_controls else img_config.get('img2img_quality', 'basic'),
                    'img2img_quality_gpt': dynamic_controls['quality'].value if img2img_model_select.value == 'gpt-image/1.5-image-to-image' and 'quality' in dynamic_controls else img_config.get('img2img_quality_gpt', 'medium'),
                    'img2img_image_size': dynamic_controls['image_size'].value if 'image_size' in dynamic_controls else img_config.get('img2img_image_size', 'square_hd'),
                    'img2img_image_resolution': dynamic_controls['image_resolution'].value if 'image_resolution' in dynamic_controls else img_config.get('img2img_image_resolution', '1K'),
                    'img2img_resolution': dynamic_controls['resolution'].value if 'resolution' in dynamic_controls else img_config.get('img2img_resolution', '1K'),
                    'img2img_max_images': int(dynamic_controls['max_images_output'].value) if 'max_images_output' in dynamic_controls else img_config.get('img2img_max_images', 1),
                    'img2img_output_format': dynamic_controls['output_format'].value if 'output_format' in dynamic_controls else img_config.get('img2img_output_format', 'png'),
                    # Paramètres Seedream ByteDance (WaveSpeed)
                    'img2img_size': dynamic_controls['size'].value if 'size' in dynamic_controls else img_config.get('img2img_size', '2048*2048'),
                    # Paramètres Qwen avancés
                    'img2img_strength': dynamic_controls['strength'].value if 'strength' in dynamic_controls else img_config.get('img2img_strength', 0.8),
                    'img2img_safety': dynamic_controls['enable_safety_checker'].value if 'enable_safety_checker' in dynamic_controls else img_config.get('img2img_safety', True),
                    'img2img_steps': int(dynamic_controls['num_inference_steps'].value) if 'num_inference_steps' in dynamic_controls else img_config.get('img2img_steps', 30),
                    'img2img_guidance': float(dynamic_controls['guidance_scale'].value) if 'guidance_scale' in dynamic_controls else img_config.get('img2img_guidance', 2.5),
                    'img2img_negative': dynamic_controls['negative_prompt'].value if 'negative_prompt' in dynamic_controls else img_config.get('img2img_negative', 'blurry, ugly'),
                    # Paramètres WaveSpeed
                    'ws_size': dynamic_controls['size'].value if 'size' in dynamic_controls else img_config.get('ws_size', '1024*1024'),
                    'ws_strength': dynamic_controls['strength'].value if 'strength' in dynamic_controls else img_config.get('ws_strength', 0.7),
                    'ws_seed': int(dynamic_controls['seed'].value) if 'seed' in dynamic_controls else img_config.get('ws_seed', -1),
                    'ws_steps': int(dynamic_controls['num_inference_steps'].value) if 'num_inference_steps' in dynamic_controls else img_config.get('ws_steps', 28),
                    'ws_guidance': float(dynamic_controls['guidance_scale'].value) if 'guidance_scale' in dynamic_controls else img_config.get('ws_guidance', 3.5),
                    # Paramètres Batch I2I (Seedream 4.5 Edit WaveSpeed)
                    'img2img_batch_seed': int(dynamic_controls['batch_seed'].value) if 'batch_seed' in dynamic_controls else img_config.get('img2img_batch_seed', -1),
                    'img2img_batch_count': int(dynamic_controls['batch_count'].value) if 'batch_count' in dynamic_controls else img_config.get('img2img_batch_count', 1),
                    'img2img_seed_increment': int(dynamic_controls['seed_increment'].value) if 'seed_increment' in dynamic_controls else img_config.get('img2img_seed_increment', 1),
                    # Paramètres AtlasCloud I2I (mirrors des contrôles partagés)
                    'atlas_i2i_size': dynamic_controls['size'].value if 'size' in dynamic_controls and img2img_provider_select.value == 'AtlasCloud' else img_config.get('atlas_i2i_size', '1024*1024'),
                    'atlas_i2i_strength': float(dynamic_controls['strength'].value) if 'strength' in dynamic_controls and img2img_provider_select.value == 'AtlasCloud' else img_config.get('atlas_i2i_strength', 0.75),
                    'atlas_i2i_seed': int(dynamic_controls['seed'].value) if 'seed' in dynamic_controls and img2img_provider_select.value == 'AtlasCloud' else img_config.get('atlas_i2i_seed', -1),
                    'atlas_i2i_negative': dynamic_controls['negative_prompt'].value if 'negative_prompt' in dynamic_controls and img2img_provider_select.value == 'AtlasCloud' else img_config.get('atlas_i2i_negative', 'blurry, ugly, deformed'),
                    'atlas_i2i_batch': int(dynamic_controls['batch_count'].value) if 'batch_count' in dynamic_controls and img2img_provider_select.value == 'AtlasCloud' else img_config.get('atlas_i2i_batch', 2),
                }

                # Sauvegarder
                sm.settings['image_generation'] = new_config
                sm.save_settings()
                
                print(f"[IMAGE-CONFIG] ✅ Configuration sauvegardée:")
                print(f"  - Provider T2I: {new_config['provider']}")
                print(f"  - Modèle T2I: {new_config['model']}")
                print(f"  - Résolution: {new_config['width']}x{new_config['height']}")
                print(f"  - Mode Safe: {new_config['safe_mode']}")
                print(f"  - Compression Vision: {new_config['vision_compression']}px")
                print(f"  - Qualité JPEG: {new_config['vision_jpeg_quality']}")
                print(f"  - Image-to-Image: {new_config['img2img_enabled']}")
                if new_config['img2img_enabled']:
                    print(f"    └─ Provider I2I: {new_config.get('img2img_provider', 'Kie')}")
                    print(f"    └─ Modèle: {new_config['img2img_model']}")
                    print(f"    └─ Params: quality={new_config.get('img2img_quality')}, res={new_config.get('img2img_resolution')}")

                # Réinitialiser l'extension text2img
                try:
                    from extensions.text2img import initialize_text2img
                    if new_config['enabled']:
                        initialize_text2img(sm)
                        print("[IMAGE-CONFIG] ✅ Extension text2img réinitialisée")
                        
                except ImportError as e:
                    print(f"[IMAGE-CONFIG] ⚠️ Extension text2img non disponible: {e}")

                ui.notify(t('image_notify_save_ok'), type='positive')
                d.close()

            ui.button(t('image_btn_save'), on_click=save_config).classes('primary-action-button')

    return d
