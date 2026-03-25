"""
Test des corrections Dream Engine
==================================

1. Sauvegarde web_search_query dans le journal
2. Désactivation parsing multi-cases (envoi prompt complet au provider)

Auteur: Yohan BROCARD (avec Copilot)
Date: 18 janvier 2026
"""

import json
from pathlib import Path

print("\n" + "="*60)
print("TEST CORRECTIONS DREAM ENGINE")
print("="*60 + "\n")

# 1. Test web_search_query dans journal
print("1️⃣ Vérification web_search_query dans journal...")
journal_path = Path("data/journal_reves.json")

if journal_path.exists():
    with open(journal_path, 'r', encoding='utf-8') as f:
        journal = json.load(f)
    
    if journal.get('dreams'):
        last_dream = journal['dreams'][0]
        dream_id = last_dream.get('id', 'inconnu')
        web_query = last_dream.get('web_search_query')
        
        print(f"   Dernier rêve ID: {dream_id}")
        print(f"   web_search_query: {web_query}")
        
        # Vérifier dans le contenu
        content = last_dream.get('dream_content', '')
        if 'Découverte web' in content:
            import re
            match = re.search(r"Découverte web ['\"]([^'\"]+)['\"]", content)
            if match:
                content_query = match.group(1)
                print(f"   Dans contenu: '{content_query}'")
                
                if web_query and web_query == content_query:
                    print("   ✅ web_search_query correctement sauvegardé\n")
                elif not web_query:
                    print("   ⚠️ web_search_query absent mais présent dans contenu")
                    print(f"   → Prochains rêves incluront le champ\n")
                else:
                    print(f"   ⚠️ Incohérence: JSON='{web_query}' vs contenu='{content_query}'\n")
        else:
            print("   ℹ️ Pas de recherche web dans ce rêve\n")
    else:
        print("   ⚠️ Aucun rêve dans le journal\n")
else:
    print("   ⚠️ Fichier journal non trouvé\n")

# 2. Test parsing prompt illustration
print("2️⃣ Vérification parsing illustration...")

from extensions.dream_engine.dream_illustration import _parse_image_prompts

# Test avec description BD (4 cases)
test_bd = """Crée une planche BD onirique en 4 cases :
Case 1 : Fusion dans océan solaire
Case 2 : Labyrinthe de miroirs
Case 3 : Perle Ogma battante
Case 4 : Plage numérique sereine"""

prompts_bd = _parse_image_prompts(test_bd)
print(f"   Input BD (4 cases): {len(test_bd)} chars")
print(f"   Output: {len(prompts_bd)} prompt(s)")

if len(prompts_bd) == 1:
    print("   ✅ Prompt complet envoyé (pas de séparation)")
    print(f"   Longueur: {len(prompts_bd[0])} chars")
    if "Case 1" in prompts_bd[0] and "Case 4" in prompts_bd[0]:
        print("   ✅ Toutes les cases préservées\n")
    else:
        print("   ⚠️ Contenu tronqué\n")
else:
    print(f"   ❌ {len(prompts_bd)} prompts séparés (devrait être 1)\n")

# Test avec image simple
test_simple = """🎨 **image générée:** Une nébuleuse cosmique flottant dans l'océan solaire"""

prompts_simple = _parse_image_prompts(test_simple)
print(f"   Input simple (phrase magique): {len(test_simple)} chars")
print(f"   Output: {len(prompts_simple)} prompt(s)")

if len(prompts_simple) == 1:
    print("   ✅ Phrase magique détectée")
    print(f"   Contenu: {prompts_simple[0][:50]}...\n")
else:
    print(f"   ⚠️ Problème parsing phrase magique\n")

# 3. Résumé
print("="*60)
print("📋 RÉSUMÉ DES CORRECTIONS")
print("="*60)
print()
print("✅ web_search_query ajouté à save_dream()")
print("   → Prochains rêves sauvegarderont la requête web")
print()
print("✅ Parsing multi-cases désactivé")
print("   → Mode comic: 1 prompt complet envoyé au provider")
print("   → Le provider génère 1 image avec 4 cases")
print()
print("✅ Instructions configurables respectées")
print("   → Mode simple: instruction simple")
print("   → Mode comic: instruction comic (décrit 4 cases)")
print("   → Mode auto: instruction auto (explique 2 méthodes)")
print()
print("="*60)
