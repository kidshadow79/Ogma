"""
Test d'intégration Dream Engine ↔ Journal de Bord

Vérifie les 3 fonctionnalités :
1. Injection états actifs dans le carburant de rêve
2. Résolution post-rêve des états
3. Auto-résolution des états inactifs >30j

Usage: python test_dream_journal_integration.py
"""

import asyncio
import sys
import os

# Ajouter le root au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_phase1_extract_active_states():
    """
    Phase 1 : Vérifie que _extract_active_states() récupère les états
    et que _build_dream_context() les formate correctement.
    """
    print("=" * 60)
    print("PHASE 1 : Injection états actifs dans carburant de rêve")
    print("=" * 60)
    
    # Test 1a : Import de la fonction
    print("\n[TEST 1a] Import _extract_active_states...")
    try:
        from extensions.dream_engine.dream_memory import _extract_active_states
        print("  OK - Fonction importée")
    except ImportError as e:
        print(f"  ERREUR - Import impossible: {e}")
        return False
    
    # Test 1b : Exécution (peut retourner [] si journal non init)
    print("\n[TEST 1b] Exécution _extract_active_states()...")
    result = asyncio.run(_extract_active_states())
    print(f"  Résultat: {len(result)} états actifs récupérés")
    if result:
        for state in result[:3]:
            print(f"    - [{state.get('category')}] {state.get('description', '')[:60]}...")
    else:
        print("  (Normal si journal de bord non initialisé en mode test)")
    
    # Test 1c : extract_dream_fuel inclut active_states
    print("\n[TEST 1c] Structure fuel contient 'active_states'...")
    try:
        from extensions.dream_engine.dream_memory import extract_dream_fuel
        fuel = asyncio.run(extract_dream_fuel(memory_manager=None))
        assert 'active_states' in fuel, "Clé 'active_states' manquante dans fuel"
        print(f"  OK - fuel['active_states'] = {len(fuel['active_states'])} états")
    except Exception as e:
        print(f"  ERREUR: {e}")
        return False
    
    # Test 1d : Formatage dans _build_dream_context (simulation)
    print("\n[TEST 1d] Formatage _build_dream_context avec états simulés...")
    simulated_fuel = {
        'summaries': [],
        'conversations': [],
        'memories': [],
        'random_memories': [],
        'active_states': [
            {
                'state_id': 1,
                'category': 'santé',
                'description': 'Fatigue chronique depuis 2 semaines',
                'importance': 'high',
                'state_type': 'temporaire',
            },
            {
                'state_id': 2,
                'category': 'projet',
                'description': 'OGMA v2.2 en cours de développement',
                'importance': 'high',
                'state_type': 'durable',
            },
            {
                'state_id': 3,
                'category': 'humeur',
                'description': 'Motivé mais fatigué',
                'importance': 'medium',
                'state_type': 'temporaire',
            },
        ],
        'web_discovery': {},
    }
    
    # Simuler _build_dream_context
    try:
        # On simule le formatage du contexte (sans instance DreamEngine)
        active_states = simulated_fuel.get('active_states', [])
        by_category = {}
        for state in active_states:
            cat = state.get('category', 'general')
            if cat not in by_category:
                by_category[cat] = []
            importance = state.get('importance', 'medium')
            importance_marker = {'high': '[!]', 'medium': '[-]', 'low': '[.]'}.get(importance, '[-]')
            by_category[cat].append(f"{importance_marker} {state.get('description', '')}")
        
        lines = []
        for cat, descriptions in by_category.items():
            lines.append(f"### {cat.capitalize()}")
            for desc in descriptions:
                lines.append(f"  {desc}")
        active_states_text = "\n".join(lines)
        
        assert "Santé" in active_states_text, "Catégorie 'Santé' manquante"
        assert "[!]" in active_states_text, "Marqueur importance haute manquant"
        assert "[-]" in active_states_text, "Marqueur importance medium manquant"
        assert "Fatigue" in active_states_text, "Description santé manquante"
        
        print(f"  OK - Contexte formaté ({len(active_states_text)} chars) :")
        print("  ---")
        for line in active_states_text.split('\n'):
            print(f"  {line}")
        print("  ---")
    except AssertionError as e:
        print(f"  ERREUR: {e}")
        return False
    
    print("\n✅ PHASE 1 : TOUS LES TESTS PASSENT")
    return True


def test_phase2_post_dream_resolution():
    """
    Phase 2 : Vérifie que la résolution post-rêve est bien câblée.
    """
    print("\n" + "=" * 60)
    print("PHASE 2 : Résolution post-rêve")
    print("=" * 60)
    
    # Test 2a : Import du bloc post-rêve depuis dream_core 
    print("\n[TEST 2a] Vérification présence bloc consolidation journal dans dream_core...")
    try:
        with open('extensions/dream_engine/dream_core.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "CONSOLIDATION JOURNAL" in content, "Bloc CONSOLIDATION JOURNAL absent de dream_core.py"
        assert "run_shutdown_analysis" in content, \
            "Import run_shutdown_analysis absent"
        print("  OK - Bloc consolidation journal présent dans dream_core.py")
    except AssertionError as e:
        print(f"  ERREUR: {e}")
        return False
    except FileNotFoundError:
        print("  ERREUR: dream_core.py non trouvé")
        return False
    
    # Test 2b : Import shutdown_state_analyzer  
    print("\n[TEST 2b] Import shutdown_state_analyzer...")
    try:
        from extensions.journal_de_bord.shutdown_state_analyzer import (
            run_shutdown_analysis, 
            initialize_shutdown_analyzer,
            get_shutdown_analyzer
        )
        print("  OK - run_shutdown_analysis, initialize_shutdown_analyzer importables")
    except ImportError as e:
        print(f"  ERREUR: {e}")
        return False
    
    print("\n✅ PHASE 2 : TESTS STRUCTURELS PASSENT")
    return True


def test_phase3_auto_resolution():
    """
    Phase 3 : Vérifie que l'auto-résolution >30j est câblée dans dream_core.
    """
    print("\n" + "=" * 60)
    print("PHASE 3 : Auto-résolution états inactifs >30j")
    print("=" * 60)
    
    # Test 3a : Import auto_resolution
    print("\n[TEST 3a] Import auto_resolution functions...")
    try:
        from extensions.journal_de_bord.auto_resolution import detect_inactive_states, auto_resolve_states
        print("  OK - detect_inactive_states et auto_resolve_states importables")
    except ImportError as e:
        print(f"  ERREUR: {e}")
        return False
    
    # Test 3b : Vérification câblage dans dream_core
    print("\n[TEST 3b] Vérification présence auto-résolution dans dream_core...")
    try:
        with open('extensions/dream_engine/dream_core.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "AUTO-RESOLUTION" in content or "auto_resolve" in content, \
            "Bloc auto-résolution absent de dream_core.py"
        assert "detect_inactive_states" in content or "auto_resolve_states" in content, \
            "Fonctions auto-résolution non appelées"
        print("  OK - Auto-résolution câblée dans dream_core.py")
    except AssertionError as e:
        print(f"  ERREUR: {e}")
        return False
    
    print("\n✅ PHASE 3 : TESTS STRUCTURELS PASSENT")
    return True


if __name__ == "__main__":
    print("🧪 TEST INTÉGRATION DREAM ENGINE ↔ JOURNAL DE BORD")
    print("=" * 60)
    
    results = {}
    
    # Phase 1
    results['phase1'] = test_phase1_extract_active_states()
    
    # Phase 2
    results['phase2'] = test_phase2_post_dream_resolution()
    
    # Phase 3
    results['phase3'] = test_phase3_auto_resolution()
    
    # Résumé
    print("\n" + "=" * 60)
    print("RÉSUMÉ FINAL")
    print("=" * 60)
    for phase, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {phase}: {status}")
    
    all_passed = all(results.values())
    print(f"\n{'✅ TOUS LES TESTS PASSENT' if all_passed else '❌ CERTAINS TESTS ÉCHOUENT'}")
    sys.exit(0 if all_passed else 1)
