"""
Analyse comparative Perchance vs Pollinations
"""
import requests
import re

print("🔍 Analyse des paramètres Perchance AI Text-to-Image Generator\n")
print("="*80)

# Tenter de récupérer la page avec un User-Agent navigateur
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

try:
    # Le générateur principal de Perchance
    url = "https://perchance.org/ai-text-to-image-generator"
    
    # Essayer avec session qui gère les cookies
    session = requests.Session()
    session.headers.update(headers)
    
    # Première requête pour obtenir cookies Cloudflare
    r1 = session.get(url, timeout=15, allow_redirects=True)
    print(f"Première requête: HTTP {r1.status_code}")
    
    if r1.status_code == 200:
        html = r1.text
        
        # Chercher l'URL de l'API utilisée
        print("\n📡 Recherche de l'endpoint API...")
        api_patterns = [
            r'https://[^"\s]+pollinations[^"\s]+',
            r'https://[^"\s]+image[^"\s]+api[^"\s]+',
            r'https://[^"\s]+generate[^"\s]+',
            r'endpoint["\s:]+([^"]+)',
            r'apiUrl["\s:]+([^"]+)',
        ]
        
        for pattern in api_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            if matches:
                print(f"\n✅ Pattern trouvé: {pattern}")
                for match in set(matches[:5]):
                    print(f"   → {match}")
        
        # Chercher les paramètres par défaut
        print("\n⚙️ Recherche des paramètres de génération...")
        param_patterns = [
            (r'model["\s:]+["\']([^"\']+)', 'Modèle'),
            (r'guidance["\s:]+(\d+\.?\d*)', 'Guidance'),
            (r'steps["\s:]+(\d+)', 'Steps'),
            (r'width["\s:]+(\d+)', 'Width'),
            (r'height["\s:]+(\d+)', 'Height'),
            (r'negative[Pp]rompt["\s:]+["\']([^"\']+)', 'Negative Prompt'),
            (r'enhance["\s:]+(\w+)', 'Enhance'),
            (r'seed["\s:]+(\d+)', 'Seed'),
        ]
        
        for pattern, name in param_patterns:
            matches = re.findall(pattern, html)
            if matches:
                print(f"   {name}: {matches[0]}")
        
        # Chercher des indices sur le preprocessing du prompt
        print("\n🎨 Recherche preprocessing prompt...")
        if 'prompt' in html.lower():
            # Extraire code JavaScript lié aux prompts
            js_prompt = re.findall(r'(prompt\s*[=+]\s*[^;]+)', html, re.IGNORECASE)
            for match in js_prompt[:5]:
                print(f"   → {match[:100]}")
                
    else:
        print(f"❌ Cloudflare bloque toujours (HTTP {r1.status_code})")
        
except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
print("HYPOTHÈSES sur la différence de qualité:")
print("="*80)
print("""
1. 📝 PREPROCESSING DU PROMPT:
   Perchance enrichit probablement le prompt avant envoi à Pollinations
   Ex: Ajout automatique de "highly detailed, professional, 8k" etc.

2. ⚙️ PARAMÈTRES OPTIMISÉS:
   Perchance utilise peut-être des paramètres différents:
   - Guidance scale plus élevé
   - Modèle spécifique (flux-pro au lieu de flux)
   - Enhancement activé par défaut
   
3. 🎯 NEGATIVE PROMPTS:
   Perchance ajoute peut-être des negative prompts automatiques
   pour améliorer la qualité (ex: "low quality, blurry, distorted")
   
4. 🔧 POST-PROCESSING:
   Upscaling ou amélioration de l'image après génération
""")
