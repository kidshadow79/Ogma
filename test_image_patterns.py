"""
Test des patterns de détection de génération d'image
"""
import re

# Patterns mis à jour
patterns = [
    r"je dois créer une image de\s*[:]\s*(.*?)(?:[.\n]|$)",  # Original
    r"il faut que je crée une image de\s*[:]\s*(.*?)(?:[.\n]|$)",  # Variante
    r"je (?:vais|dois) (?:générer|créer) une image de\s*[:]\s*(.*?)(?:[.\n]|$)",  # Variantes
]

# Tests
test_cases = [
    # Format original (devrait marcher)
    "je dois créer une image de : une femme latina nue",
    
    # Format utilisé par Luna dans les logs (ÉTAIT CASSÉ)
    "il faut que je crée une image de : une bomba latina sensuelle aux courbes voluptueuses",
    
    # Autres variantes possibles
    "je vais créer une image de : nous deux enlacés",
    "je vais générer une image de : scène torride",
    "je dois générer une image de : Luna nue",
]

print("="*80)
print("TEST DES PATTERNS DE DÉTECTION")
print("="*80)

for i, test in enumerate(test_cases, 1):
    print(f"\n{i}. Test: '{test[:60]}...'")
    
    matched = False
    for j, pattern in enumerate(patterns, 1):
        match = re.search(pattern, test, re.IGNORECASE | re.DOTALL)
        if match:
            description = match.group(1).strip()
            print(f"   ✅ Pattern {j} détecté!")
            print(f"   📝 Description extraite: '{description[:80]}...'")
            matched = True
            break
    
    if not matched:
        print(f"   ❌ AUCUN pattern détecté")

print("\n" + "="*80)
print("RÉSUMÉ")
print("="*80)

# Test spécifique du cas problématique
problematic_text = "il faut que je crée une image de : une bomba latina sensuelle aux courbes voluptueuses, peau caramel luisante de sueur sous une lumière tamisée"

detected = False
for pattern in patterns:
    if re.search(pattern, problematic_text, re.IGNORECASE | re.DOTALL):
        detected = True
        break

if detected:
    print("✅ SUCCESS: Le cas problématique des logs est maintenant détecté!")
else:
    print("❌ FAIL: Le cas problématique n'est toujours pas détecté")
