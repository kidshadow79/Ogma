"""
Recherche API Perchance pour génération d'images
"""
import requests

print("🔍 Recherche de l'API Perchance Text-to-Image...\n")

# Endpoints connus de Perchance
generators = [
    'ai-text-to-image-generator',
    'ai-photo-generator', 
    'beautiful-people-generator',
    'nsfw-ai-image-generator'
]

for gen in generators:
    url = f"https://perchance.org/{gen}"
    try:
        r = requests.head(url, timeout=10)
        print(f"✓ {gen}: HTTP {r.status_code}")
    except Exception as e:
        print(f"✗ {gen}: {e}")

print("\n" + "="*80)
print("Analyse du générateur AI principal...")
print("="*80)

try:
    r = requests.get("https://perchance.org/ai-text-to-image-generator", timeout=10)
    
    # Chercher l'API endpoint dans le HTML/JavaScript
    if 'api' in r.text.lower():
        print("\n✅ Mention 'api' trouvée dans la page")
        
        # Extraire les URLs potentielles
        import re
        urls = re.findall(r'https?://[^\s<>"]+', r.text)
        api_urls = [u for u in urls if 'api' in u.lower() or 'generate' in u.lower()]
        
        print(f"\n📡 URLs API potentielles trouvées: {len(api_urls)}")
        for url in api_urls[:10]:  # Limiter à 10
            print(f"  - {url}")
    
    # Chercher des patterns de génération
    if 'generate' in r.text.lower():
        matches = re.findall(r'(generate[a-zA-Z]*\s*[=(].*?[)\n])', r.text.lower())
        print(f"\n🔧 Fonctions de génération trouvées: {len(matches)}")
        for match in matches[:5]:
            print(f"  - {match[:100]}")
            
except Exception as e:
    print(f"❌ Erreur: {e}")
