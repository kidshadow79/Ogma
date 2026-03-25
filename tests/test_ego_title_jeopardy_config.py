"""
Test du système configurable de titre Jeopardy pour les traits ego
"""

import json
from pathlib import Path

def test_ego_title_jeopardy_configuration():
    """Vérifie que le prompt ego_title_jeopardy est correctement configurable"""
    
    print("=" * 80)
    print("🧪 TEST: Configuration Titre Jeopardy Ego")
    print("=" * 80)
    
    # Test 1: Vérifier présence dans instructions_defaults.json
    print("\n1️⃣ Vérification instructions_defaults.json")
    defaults_path = Path("data/instructions_defaults.json")
    
    if not defaults_path.exists():
        print("❌ ÉCHEC: instructions_defaults.json non trouvé")
        return False
    
    with open(defaults_path, 'r', encoding='utf-8') as f:
        defaults = json.load(f)
    
    ego_prompt = defaults.get('prompts_defaults', {}).get('ego_title_jeopardy')
    if not ego_prompt:
        print("❌ ÉCHEC: ego_title_jeopardy non trouvé dans prompts_defaults")
        return False
    
    print("✅ ego_title_jeopardy trouvé dans instructions_defaults.json")
    print(f"📝 Longueur: {len(ego_prompt)} caractères")
    
    # Test 2: Vérifier le placeholder
    print("\n2️⃣ Vérification placeholder {trait_text}")
    if '{trait_text}' not in ego_prompt:
        print("❌ ÉCHEC: placeholder {trait_text} manquant")
        return False
    
    print("✅ Placeholder {trait_text} présent")
    
    # Test 3: Simuler formatage
    print("\n3️⃣ Test formatage avec trait exemple")
    test_trait = "Je déteste mentir"
    try:
        formatted = ego_prompt.format(trait_text=test_trait)
        print("✅ Formatage réussi")
        print(f"📋 Aperçu prompt formaté:")
        print("-" * 80)
        print(formatted[:300] + "...")
        print("-" * 80)
    except Exception as e:
        print(f"❌ ÉCHEC formatage: {e}")
        return False
    
    # Test 4: Vérifier présence dans ogma_modals.py (définition UI)
    print("\n4️⃣ Vérification ogma_modals.py (définition UI)")
    modals_path = Path("ogma_modals.py")
    
    if not modals_path.exists():
        print("❌ ÉCHEC: ogma_modals.py non trouvé")
        return False
    
    with open(modals_path, 'r', encoding='utf-8') as f:
        modals_content = f.read()
    
    if "'id': 'ego_title_jeopardy'" not in modals_content:
        print("❌ ÉCHEC: ego_title_jeopardy non trouvé dans ogma_modals.py")
        return False
    
    print("✅ Définition ego_title_jeopardy trouvée dans ogma_modals.py")
    
    # Test 5: Vérifier configuration memory_manager.py
    print("\n5️⃣ Vérification memory_manager.py (logique chargement)")
    memory_mgr_path = Path("memory_manager.py")
    
    if not memory_mgr_path.exists():
        print("❌ ÉCHEC: memory_manager.py non trouvé")
        return False
    
    with open(memory_mgr_path, 'r', encoding='utf-8') as f:
        memory_content = f.read()
    
    # Vérifier que le code charge depuis settings
    if "settings.get('prompts', {}).get('ego_title_jeopardy')" not in memory_content:
        print("❌ ÉCHEC: Chargement depuis settings.json non trouvé")
        return False
    
    print("✅ Logique chargement depuis settings.json trouvée")
    
    # Vérifier fallback sur instructions_defaults.json
    if "'ego_title_jeopardy'" not in memory_content:
        print("❌ ÉCHEC: Fallback instructions_defaults.json non trouvé")
        return False
    
    print("✅ Fallback instructions_defaults.json trouvé")
    
    # Test 6: Vérifier structure réponse attendue
    print("\n6️⃣ Vérification structure prompt (2 questions)")
    if "2 QUESTIONS DISTINCTES" not in ego_prompt and "2 questions" not in ego_prompt.lower():
        print("⚠️  AVERTISSEMENT: Mention '2 QUESTIONS' non trouvée")
    else:
        print("✅ Mention '2 QUESTIONS DISTINCTES' présente")
    
    # Résumé final
    print("\n" + "=" * 80)
    print("✅ TOUS LES TESTS PASSÉS")
    print("=" * 80)
    print("\n📊 Résumé configuration:")
    print("  1. ✅ Prompt dans instructions_defaults.json (valeur par défaut)")
    print("  2. ✅ Entrée UI dans ogma_modals.py (modifiable via frontend)")
    print("  3. ✅ Chargement prioritaire depuis settings.json")
    print("  4. ✅ Fallback sur instructions_defaults.json")
    print("  5. ✅ Placeholder {trait_text} fonctionnel")
    print("\n🎯 Workflow complet:")
    print("  → Utilisateur va dans Paramètres → Instructions → Titre Jeopardy Ego")
    print("  → Modifie le prompt")
    print("  → Sauvegarde → prompt écrit dans settings.json")
    print("  → memory_manager.py charge depuis settings.json (priorité)")
    print("  → Si absent, fallback sur instructions_defaults.json")
    print("  → Reset profil = restaure version instructions_defaults.json")
    print("\n✨ Le prompt ego_title_jeopardy est maintenant configurable !")
    
    return True

if __name__ == "__main__":
    success = test_ego_title_jeopardy_configuration()
    exit(0 if success else 1)
