"""
Test rapide du nettoyage de nom de fichier pour images
"""
import re
import unicodedata

def sanitize_filename(prompt_slug: str) -> str:
    """Simule le nouveau code de sanitization."""
    
    # 1. Nettoyer balises HTML/Markdown (y compris échappées comme <\em>)
    prompt_slug = re.sub(r'<[^>]*>', '', prompt_slug)  # Balises normales
    prompt_slug = re.sub(r'<\\[^>]*>', '', prompt_slug)  # Balises échappées <\em>
    
    # 2. Remplacer DIRECTEMENT les caractères interdits Windows (<>:"/\|?*)
    invalid_chars = r'<>:"/\|?*'
    prompt_slug = ''.join(c if c not in invalid_chars else '_' for c in prompt_slug)
    
    # 3. Remplacer les accents par équivalents ASCII (é→e, à→a, etc.)
    prompt_slug = unicodedata.normalize('NFKD', prompt_slug)
    prompt_slug = prompt_slug.encode('ascii', 'ignore').decode('ascii')
    
    # 4. Garder uniquement alphanumériques, espaces, tirets et underscores
    prompt_slug = "".join(c if c.isalnum() or c in (' ', '-', '_') else '' for c in prompt_slug).strip()
    prompt_slug = prompt_slug.replace(' ', '_')
    
    return prompt_slug


# Test avec le nom problématique réel de l'erreur
test_cases = [
    "wavespeed<em>20260122<\\em>144313<em>garde<\\em>la<em>pose<\\em>la<em>position<\\em>et_l",
    "<em>garde la pose</em>",
    "test:avec/caractères*interdits?",
    "café crème à Paris",
    "normal_filename_123"
]

print("=== TEST DE SANITIZATION ===\n")
for i, test in enumerate(test_cases, 1):
    cleaned = sanitize_filename(test[:30])  # Limiter à 30 chars comme dans le code
    print(f"Test {i}:")
    print(f"  Input:  '{test[:50]}'")
    print(f"  Output: '{cleaned}'")
    print(f"  Safe:   {all(c not in r'<>:"/\|?*' for c in cleaned)}")
    print()
