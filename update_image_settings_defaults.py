"""
Script pour mettre à jour les settings par défaut de l'extension Text2Image
Ajoute les quality_boosts et nsfw_boosts modifiables depuis l'UI
"""

import json
from pathlib import Path

# Valeurs par défaut du PromptEnhancer (backend)
DEFAULT_QUALITY_BOOSTS = "highly detailed, photorealistic, 8k uhd resolution, sharp focus, professional photography, studio quality lighting, cinematic composition, masterpiece quality, perfect anatomy, natural skin texture, realistic details, high definition, crisp image, professional color grading"

DEFAULT_NSFW_BOOSTS = "anatomically correct, natural proportions, realistic body, authentic human anatomy, detailed skin pores, natural skin imperfections, subtle muscle definition, realistic lighting on skin"

DEFAULT_NEGATIVE_PROMPT = "blurry, low quality, distorted, bad anatomy, deformed"

# Charger settings.json
settings_path = Path("data/settings.json")

if not settings_path.exists():
    print(f"❌ Fichier {settings_path} introuvable")
    exit(1)

with open(settings_path, 'r', encoding='utf-8') as f:
    settings = json.load(f)

# Mettre à jour la section image_generation
if 'image_generation' not in settings:
    settings['image_generation'] = {}

img_settings = settings['image_generation']

# Ajouter/mettre à jour prompt_enhancement
img_settings['prompt_enhancement'] = {
    'quality_boosts': DEFAULT_QUALITY_BOOSTS,
    'nsfw_boosts': DEFAULT_NSFW_BOOSTS,
    'custom_boosts': ''
}

# Ajouter negative_prompt si absent
if 'negative_prompt' not in img_settings:
    img_settings['negative_prompt'] = DEFAULT_NEGATIVE_PROMPT

# Sauvegarder
with open(settings_path, 'w', encoding='utf-8') as f:
    json.dump(settings, f, indent=2, ensure_ascii=False)

print("✅ Settings mis à jour avec succès!")
print(f"📊 Quality boosts: {len(DEFAULT_QUALITY_BOOSTS)} chars")
print(f"🔞 NSFW boosts: {len(DEFAULT_NSFW_BOOSTS)} chars")
print(f"🚫 Negative prompt: '{DEFAULT_NEGATIVE_PROMPT}'")
print("\n💡 Lance OGMA et va dans Paramètres > Image pour modifier ces valeurs")
