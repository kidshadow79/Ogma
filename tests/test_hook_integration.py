"""
Test rapide de l'intégration du hook Journal dans OGMA
"""

import sys
from pathlib import Path

# Ajouter le répertoire racine au path
sys.path.insert(0, str(Path(__file__).parent))


def test_hook_integration():
    """Vérifie que le hook est bien intégré dans ogma_ng.py"""
    
    print("🧪 Test d'intégration du hook Journal de Bord")
    print("=" * 60)
    
    # Vérifier que le hook existe dans ogma_ng.py
    ogma_ng_path = Path(__file__).parent / "ogma_ng.py"
    
    if not ogma_ng_path.exists():
        print("❌ Fichier ogma_ng.py introuvable")
        return False
    
    with open(ogma_ng_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifications
    checks = [
        ("JOURNAL-HOOK", "[JOURNAL-HOOK]"),
        ("Import hook_message_exchange", "from extensions.journal_de_bord import hook_message_exchange"),
        ("Appel hook", "await hook_message_exchange("),
        ("Détection nouveaux états", 'changes.get("new_states")'),
        ("Détection résolutions", 'changes.get("resolved_states")'),
    ]
    
    print("\n📋 Vérifications:")
    all_ok = True
    for check_name, pattern in checks:
        if pattern in content:
            print(f"  ✅ {check_name}")
        else:
            print(f"  ❌ {check_name} - MANQUANT")
            all_ok = False
    
    # Vérifier Option B dans context_provider
    print("\n📋 Vérification Option B (Hybride):")
    context_provider_path = Path(__file__).parent / "extensions" / "journal_de_bord" / "context_provider.py"
    
    if context_provider_path.exists():
        with open(context_provider_path, 'r', encoding='utf-8') as f:
            cp_content = f.read()
        
        hybrid_checks = [
            ("Détection états actifs", "has_active_states"),
            ("Injection dynamique", "num_entries_to_inject"),
            ("Mode 2 conversations", "min(2, max_entries)"),
            ("Mode 3 conversations", "min(3, max_entries)"),
            ("Logs MODE-HYBRIDE", "[CONTEXT-PROVIDER] MODE-HYBRIDE"),
        ]
        
        for check_name, pattern in hybrid_checks:
            if pattern in cp_content:
                print(f"  ✅ {check_name}")
            else:
                print(f"  ❌ {check_name} - MANQUANT")
                all_ok = False
    else:
        print("  ⚠️ Fichier context_provider.py introuvable")
    
    # Vérifier LiveStateDetector
    print("\n📋 Vérification LiveStateDetector:")
    detector_path = Path(__file__).parent / "extensions" / "journal_de_bord" / "live_state_detector.py"
    
    if detector_path.exists():
        print("  ✅ Module live_state_detector.py présent")
        
        with open(detector_path, 'r', encoding='utf-8') as f:
            detector_content = f.read()
        
        detector_checks = [
            ("Classe LiveStateDetector", "class LiveStateDetector"),
            ("Méthode analyze_message_pair", "async def analyze_message_pair"),
            ("Patterns création", "creation_patterns"),
            ("Patterns résolution", "resolution_patterns"),
            ("Analyse LLM", "_llm_deep_analysis"),
        ]
        
        for check_name, pattern in detector_checks:
            if pattern in detector_content:
                print(f"  ✅ {check_name}")
            else:
                print(f"  ❌ {check_name} - MANQUANT")
                all_ok = False
    else:
        print("  ❌ Module live_state_detector.py introuvable")
        all_ok = False
    
    # Vérifier __init__.py exports
    print("\n📋 Vérification exports extension:")
    init_path = Path(__file__).parent / "extensions" / "journal_de_bord" / "__init__.py"
    
    if init_path.exists():
        with open(init_path, 'r', encoding='utf-8') as f:
            init_content = f.read()
        
        export_checks = [
            ("hook_message_exchange", "hook_message_exchange"),
            ("get_live_detector", "get_live_detector"),
            ("LiveStateDetector init", "LiveStateDetector("),
        ]
        
        for check_name, pattern in export_checks:
            if pattern in init_content:
                print(f"  ✅ {check_name}")
            else:
                print(f"  ❌ {check_name} - MANQUANT")
                all_ok = False
    else:
        print("  ❌ Fichier __init__.py introuvable")
        all_ok = False
    
    # Résultat final
    print("\n" + "=" * 60)
    if all_ok:
        print("✅ INTÉGRATION COMPLÈTE - Tous les composants sont en place")
        print("\n📝 Prochaines étapes:")
        print("  1. Lancer OGMA: python launch_ogma.py")
        print("  2. Tester avec une conversation créant un état")
        print("  3. Vérifier les logs [JOURNAL-HOOK]")
        print("  4. Lancer l'analyse rétroactive:")
        print("     python extensions/journal_de_bord/analyze_retroactive.py -n 3")
    else:
        print("⚠️ INTÉGRATION INCOMPLÈTE - Vérifier les éléments manquants")
    
    print("=" * 60)
    
    return all_ok


if __name__ == "__main__":
    success = test_hook_integration()
    sys.exit(0 if success else 1)
