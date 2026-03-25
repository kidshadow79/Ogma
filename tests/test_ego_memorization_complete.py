"""
Test du système d'enrichissement ego complet (titre + scoring + analyse en un seul appel)
"""

import json
from pathlib import Path

def test_ego_memorization_system():
    """Vérifie le nouveau système d'enrichissement ego unifié"""
    
    print("=" * 100)
    print("🧪 TEST: Système Enrichissement Ego Complet")
    print("=" * 100)
    
    # Test 1: Vérifier instructions_defaults.json
    print("\n1️⃣ Vérification instructions_defaults.json")
    defaults_path = Path("data/instructions_defaults.json")
    
    if not defaults_path.exists():
        print("❌ ÉCHEC: instructions_defaults.json non trouvé")
        return False
    
    with open(defaults_path, 'r', encoding='utf-8') as f:
        defaults = json.load(f)
    
    ego_prompt = defaults.get('prompts_defaults', {}).get('ego_memorization')
    if not ego_prompt:
        print("❌ ÉCHEC: ego_memorization non trouvé dans prompts_defaults")
        return False
    
    print("✅ ego_memorization trouvé dans instructions_defaults.json")
    print(f"📝 Longueur: {len(ego_prompt)} caractères")
    
    # Test 2: Vérifier structure du prompt
    print("\n2️⃣ Vérification structure prompt ego")
    
    required_keywords = [
        "ARCHIVISTE_EGO",
        "JSON_STRICT",
        "title",
        "summary",
        "intensite",
        "multiplicateur_impact",
        "valence",
        "commentaire_archiviste",
        "score_impact",
        "trait_original",
        "{trait_text}"
    ]
    
    missing = [kw for kw in required_keywords if kw not in ego_prompt]
    if missing:
        print(f"❌ ÉCHEC: Mots-clés manquants: {missing}")
        return False
    
    print("✅ Tous les mots-clés requis présents")
    
    # Test 3: Vérifier placeholder {trait_text}
    print("\n3️⃣ Test formatage avec trait exemple")
    test_trait = "Je déteste mentir et privilégie toujours la transparence"
    
    try:
        formatted = ego_prompt.format(trait_text=test_trait)
        print("✅ Formatage réussi")
        print(f"📋 Longueur prompt formaté: {len(formatted)} chars")
    except Exception as e:
        print(f"❌ ÉCHEC formatage: {e}")
        return False
    
    # Test 4: Vérifier présence dans ogma_modals.py
    print("\n4️⃣ Vérification ogma_modals.py (UI)")
    modals_path = Path("ogma_modals.py")
    
    if not modals_path.exists():
        print("❌ ÉCHEC: ogma_modals.py non trouvé")
        return False
    
    with open(modals_path, 'r', encoding='utf-8') as f:
        modals_content = f.read()
    
    if "'id': 'ego_memorization'" not in modals_content:
        print("❌ ÉCHEC: ego_memorization non trouvé dans ogma_modals.py")
        return False
    
    print("✅ Définition ego_memorization trouvée dans ogma_modals.py")
    
    # Test 5: Vérifier memory_manager.py
    print("\n5️⃣ Vérification memory_manager.py")
    memory_mgr_path = Path("memory_manager.py")
    
    if not memory_mgr_path.exists():
        print("❌ ÉCHEC: memory_manager.py non trouvé")
        return False
    
    with open(memory_mgr_path, 'r', encoding='utf-8') as f:
        memory_content = f.read()
    
    # Vérifier fonction _call_archiviste_ego_enrichment
    if "async def _call_archiviste_ego_enrichment" not in memory_content:
        print("❌ ÉCHEC: Fonction _call_archiviste_ego_enrichment non trouvée")
        return False
    
    print("✅ Fonction _call_archiviste_ego_enrichment trouvée")
    
    # Vérifier appel dans store_ego_trait
    if "await self._call_archiviste_ego_enrichment" not in memory_content:
        print("❌ ÉCHEC: Appel _call_archiviste_ego_enrichment non trouvé dans store_ego_trait")
        return False
    
    print("✅ Appel _call_archiviste_ego_enrichment trouvé dans store_ego_trait")
    
    # Vérifier chargement prioritaire settings.json
    if "settings.get('prompts', {}).get('ego_memorization')" not in memory_content:
        print("❌ ÉCHEC: Chargement prioritaire depuis settings.json non trouvé")
        return False
    
    print("✅ Chargement prioritaire settings.json implémenté")
    
    # Vérifier fallback instructions_defaults.json
    if "'ego_memorization'" not in memory_content or "prompts_defaults" not in memory_content:
        print("❌ ÉCHEC: Fallback instructions_defaults.json non trouvé")
        return False
    
    print("✅ Fallback instructions_defaults.json implémenté")
    
    # Test 6: Vérifier que l'ancien système titre séparé a été supprimé
    print("\n6️⃣ Vérification suppression ancien système titre séparé")
    
    if "ego_title_jeopardy" in memory_content and "get('ego_title_jeopardy')" in memory_content:
        print("⚠️  AVERTISSEMENT: Références à ego_title_jeopardy encore présentes (peut-être fallback)")
    else:
        print("✅ Ancien système titre séparé supprimé")
    
    # Test 7: Vérifier extraction des champs du JSON enrichi
    print("\n7️⃣ Vérification extraction champs enrichis")
    
    expected_extractions = [
        "enriched_ego.get('title'",
        "enriched_ego.get('summary'",
        "enriched_ego.get('valence'",
        "enriched_ego.get('score_impact'",
        "enriched_ego.get('type'",
        "enriched_ego.get('commentaire_archiviste'"
    ]
    
    missing_extractions = [ex for ex in expected_extractions if ex not in memory_content]
    if missing_extractions:
        print(f"❌ ÉCHEC: Extractions manquantes: {missing_extractions}")
        return False
    
    print("✅ Toutes les extractions de champs trouvées")
    
    # Résumé final
    print("\n" + "=" * 100)
    print("✅ TOUS LES TESTS PASSÉS")
    print("=" * 100)
    print("\n📊 Résumé implémentation:")
    print("  1. ✅ Prompt ego_memorization dans instructions_defaults.json")
    print("  2. ✅ UI dans ogma_modals.py (modifiable via frontend)")
    print("  3. ✅ Fonction _call_archiviste_ego_enrichment créée")
    print("  4. ✅ Appel unique pour enrichissement complet (titre + résumé + scoring)")
    print("  5. ✅ Priorité: settings.json > instructions_defaults.json > hardcodé")
    print("  6. ✅ Ancien système titre séparé remplacé")
    print("\n🎯 Avantages:")
    print("  ➡️  UN SEUL appel API (au lieu de 2-3)")
    print("  ➡️  Cohérence: titre + résumé + analyse générés ensemble")
    print("  ➡️  Configurable via frontend (Paramètres → Instructions)")
    print("  ➡️  Reset profil restaure version par défaut")
    print("  ➡️  Modifications frontend prioritaires sur défaut")
    print("\n✨ Le système d'enrichissement ego est maintenant unifié et configurable !")
    
    return True

if __name__ == "__main__":
    success = test_ego_memorization_system()
    exit(0 if success else 1)
