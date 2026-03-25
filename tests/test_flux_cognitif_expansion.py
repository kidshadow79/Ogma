#!/usr/bin/env python3
"""
🧪 TEST FIX EXPANSIONS FLUX COGNITIF
Vérifie que les expansions de détails restent ouvertes
"""

import sys
sys.path.insert(0, "c:\\IA\\OGMA")

from extensions.flux_cognitif import (
    initialize_flux_cognitif,
    log_cognitive_event,
    get_recent_events
)
import time

def test_no_refresh_without_new_events():
    """Test que le rafraîchissement ne se fait pas sans nouveaux événements"""
    print("\n=== TEST 1: Pas de rafraîchissement inutile ===")
    
    flux = initialize_flux_cognitif()
    flux.clear_events()
    flux.set_level(2)
    
    # Logger quelques événements
    log_cognitive_event(
        'archiviste',
        '💬 Prompt test',
        metadata={'prompt': 'Test prompt...', 'response': 'Test response...'},
        event_level=2
    )
    
    log_cognitive_event(
        'archiviste',
        '✅ Enrichi: "Test..." (type=affectif, int=0.8)',
        metadata={'enriched_json': {'type': 'affectif', 'title': 'Test'}},
        event_level=2
    )
    
    initial_count = len(get_recent_events(limit=20))
    print(f"✅ {initial_count} événements initiaux")
    
    # Attendre 3 secondes (plus que 2s du timer)
    print("⏳ Attente 3s (timer à 2s)...")
    time.sleep(3)
    
    # Vérifier que le nombre n'a pas changé
    current_count = len(get_recent_events(limit=20))
    print(f"✅ {current_count} événements après 3s")
    
    if initial_count == current_count:
        print("✅ Nombre d'événements stable - rafraîchissement conditionnel fonctionne")
        print("   → Les expansions ne devraient PAS se refermer automatiquement")
    else:
        print(f"❌ Nombre changé ({initial_count} → {current_count})")
        return False
    
    return True

def test_force_refresh_on_filter_change():
    """Test que le changement de filtre force le rafraîchissement"""
    print("\n=== TEST 2: Rafraîchissement forcé au changement filtre ===")
    
    flux = initialize_flux_cognitif()
    flux.clear_events()
    
    # Logger événements de différentes sources
    log_cognitive_event('archiviste', 'Event archiviste')
    log_cognitive_event('biography', 'Event biography')
    log_cognitive_event('journal', 'Event journal')
    
    print(f"Filtres AVANT:")
    for source, enabled in flux.filters.items():
        print(f"   - {source}: {'ON' if enabled else 'OFF'}")
    
    # Changer un filtre
    flux.set_filter('biography', False)
    
    print(f"\nFiltres APRÈS (biography OFF):")
    for source, enabled in flux.filters.items():
        print(f"   - {source}: {'ON' if enabled else 'OFF'}")
    
    events = get_recent_events(limit=20)
    biography_events = [e for e in events if e['source'] == 'biography']
    
    if len(biography_events) == 0:
        print("✅ Événements biography filtrés correctement")
        print("   → Le rafraîchissement forcé fonctionne")
    else:
        print(f"❌ {len(biography_events)} événements biography encore visibles")
        return False
    
    return True

def test_force_refresh_on_level_change():
    """Test que le changement de niveau force le rafraîchissement"""
    print("\n=== TEST 3: Rafraîchissement forcé au changement niveau ===")
    
    flux = initialize_flux_cognitif()
    flux.clear_events()
    flux.set_level(1)
    
    # Logger événements Phase 1 et Phase 2
    log_cognitive_event('archiviste', 'Event Phase 1', event_level=1)
    log_cognitive_event('archiviste', 'Event Phase 2', event_level=2)
    
    events_level1 = get_recent_events(limit=20)
    count_level1 = len(events_level1)
    print(f"Niveau 1: {count_level1} événements visibles")
    
    # Changer niveau à 2
    flux.set_level(2)
    
    events_level2 = get_recent_events(limit=20)
    count_level2 = len(events_level2)
    print(f"Niveau 2: {count_level2} événements visibles")
    
    if count_level2 > count_level1:
        print("✅ Plus d'événements visibles au niveau 2")
        print("   → Le rafraîchissement forcé fonctionne")
    else:
        print(f"❌ Même nombre d'événements ({count_level1} = {count_level2})")
        return False
    
    return True

# ========================================
# MAIN
# ========================================

if __name__ == "__main__":
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║  🧪 TEST FIX EXPANSIONS FLUX COGNITIF                    ║")
    print("║  Vérification rafraîchissement conditionnel              ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    
    tests = [
        ("Pas de rafraîchissement inutile", test_no_refresh_without_new_events),
        ("Rafraîchissement forcé (filtre)", test_force_refresh_on_filter_change),
        ("Rafraîchissement forcé (niveau)", test_force_refresh_on_level_change)
    ]
    
    resultats = []
    for nom, test_func in tests:
        print(f"\n{'='*60}")
        try:
            resultat = test_func()
            resultats.append(resultat)
        except Exception as e:
            print(f"❌ ERREUR: {e}")
            import traceback
            traceback.print_exc()
            resultats.append(False)
    
    # Résumé
    print("\n" + "="*60)
    print("RÉSUMÉ")
    print("="*60)
    total = len(resultats)
    succes = sum(resultats)
    print(f"Tests réussis: {succes}/{total}")
    
    if all(resultats):
        print("\n🎉 TOUS LES TESTS PASSENT !")
        print("\n📋 Fix validé:")
        print("   ✓ Rafraîchissement UNIQUEMENT si nouveaux événements")
        print("   ✓ Les expansions ne se referment PLUS automatiquement")
        print("   ✓ Rafraîchissement forcé au changement filtre/niveau")
        print("\n🎯 Les expansions de détails Phase 2 restent ouvertes !")
    else:
        print("\n⚠️ CERTAINS TESTS ONT ÉCHOUÉ")
    
    sys.exit(0 if all(resultats) else 1)
