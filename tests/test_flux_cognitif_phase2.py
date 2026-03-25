#!/usr/bin/env python3
"""
🧪 TEST FLUX COGNITIF PHASE 2
Vérifie l'implémentation Phase 2 (NORMAL) avec événements enrichis
"""

import sys
sys.path.insert(0, "c:\\IA\\OGMA")

from extensions.flux_cognitif import (
    initialize_flux_cognitif,
    log_cognitive_event,
    get_recent_events,
    is_available
)

def test_phase2_events():
    """Test logging événements Phase 2 avec metadata"""
    print("\n=== TEST 1: Initialisation ===")
    flux = initialize_flux_cognitif()
    print(f"✅ Flux initialisé: {flux}")
    print(f"✅ Niveau actuel: {flux.level}")
    
    # Définir niveau 1 (SURFACE) - événements Phase 2 doivent être filtrés
    print("\n=== TEST 2: Niveau SURFACE (filtrage Phase 2) ===")
    flux.set_level(1)
    
    # Logger événement Phase 1
    log_cognitive_event('archiviste', 'Souvenirs: 10 injectés', event_level=1)
    
    # Logger événement Phase 2 (ne devrait PAS apparaître)
    log_cognitive_event(
        'archiviste',
        'Enrichissement souvenir #123',
        metadata={'prompt': 'Test prompt...', 'response': 'Test response...'},
        event_level=2
    )
    
    events = get_recent_events(limit=10)
    print(f"✅ Événements enregistrés (niveau 1): {len(events)}")
    if len(events) == 1:
        print("✅ Filtrage Phase 2 fonctionne (1 événement Phase 1 seulement)")
    else:
        print(f"❌ ERREUR: {len(events)} événements (attendu: 1)")
        return False
    
    # Définir niveau 2 (NORMAL) - événements Phase 2 doivent apparaître
    print("\n=== TEST 3: Niveau NORMAL (affichage Phase 2) ===")
    flux.clear_events()
    flux.set_level(2)
    
    # Logger événements Phase 1
    log_cognitive_event('archiviste', 'Souvenirs: 5 injectés', event_level=1)
    log_cognitive_event('biography', 'Biographie (3 souvenirs)', event_level=1)
    
    # Logger événements Phase 2 (doivent apparaître)
    log_cognitive_event(
        'archiviste',
        '💬 Prompt enrichissement (150 chars texte)',
        metadata={
            'prompt': 'Tu es une IA de mémoire consciente... [PROMPT COMPLET ICI]',
            'text_brut': 'Texte brut à enrichir...'
        },
        event_level=2
    )
    
    log_cognitive_event(
        'archiviste',
        '✅ Enrichi: "Souvenir test..." (type=affectif, int=0.8)',
        metadata={
            'enriched_json': {
                'type': 'affectif',
                'title': 'Souvenir test',
                'intensite': 0.8,
                'valence': 1
            },
            'raw_response': '{"type": "affectif", ...}'
        },
        event_level=2
    )
    
    events = get_recent_events(limit=10)
    print(f"✅ Événements enregistrés (niveau 2): {len(events)}")
    
    phase1_count = sum(1 for e in events if e.get('level', 1) == 1)
    phase2_count = sum(1 for e in events if e.get('level', 1) == 2)
    
    print(f"   - Phase 1: {phase1_count} événements")
    print(f"   - Phase 2: {phase2_count} événements")
    
    if phase1_count == 2 and phase2_count == 2:
        print("✅ Affichage Phase 2 fonctionne (2 Phase 1 + 2 Phase 2)")
    else:
        print(f"❌ ERREUR: {phase1_count} Phase 1, {phase2_count} Phase 2 (attendu: 2+2)")
        return False
    
    # Vérifier metadata
    print("\n=== TEST 4: Vérification metadata Phase 2 ===")
    phase2_events = [e for e in events if e.get('level', 1) == 2]
    
    for i, event in enumerate(phase2_events, start=1):
        print(f"\n📋 Événement Phase 2 #{i}:")
        print(f"   - Source: {event['source']}")
        print(f"   - Message: {event['message']}")
        print(f"   - Metadata keys: {list(event.get('metadata', {}).keys())}")
        
        metadata = event.get('metadata', {})
        if i == 1:  # Premier événement (prompt)
            if 'prompt' in metadata and 'text_brut' in metadata:
                print("   ✅ Metadata prompt présentes")
            else:
                print(f"   ❌ Metadata manquantes: {metadata.keys()}")
                return False
        elif i == 2:  # Second événement (réponse)
            if 'enriched_json' in metadata and 'raw_response' in metadata:
                print("   ✅ Metadata réponse présentes")
                enriched = metadata['enriched_json']
                print(f"   ✅ JSON enrichi: type={enriched.get('type')}, intensite={enriched.get('intensite')}")
            else:
                print(f"   ❌ Metadata manquantes: {metadata.keys()}")
                return False
    
    # Tester niveau 3 (DEEP) - pas encore implémenté mais doit fonctionner
    print("\n=== TEST 5: Niveau DEEP (Phase 3 - futur) ===")
    flux.clear_events()
    flux.set_level(3)
    
    log_cognitive_event('archiviste', 'Événement Phase 1', event_level=1)
    log_cognitive_event('archiviste', 'Événement Phase 2', event_level=2)
    log_cognitive_event('archiviste', 'Événement Phase 3 (futur)', event_level=3)
    
    events = get_recent_events(limit=10)
    if len(events) == 3:
        print(f"✅ Niveau DEEP affiche tous les événements ({len(events)})")
    else:
        print(f"❌ ERREUR: {len(events)} événements (attendu: 3)")
        return False
    
    return True

def test_level_filtering():
    """Test système de filtrage par niveau"""
    print("\n=== TEST 6: Filtrage hiérarchique niveaux ===")
    flux = initialize_flux_cognitif()
    
    scenarios = [
        (1, [1, 2, 3], [1]),  # Niveau 1: affiche seulement event_level 1
        (2, [1, 2, 3], [1, 2]),  # Niveau 2: affiche 1 et 2
        (3, [1, 2, 3], [1, 2, 3])  # Niveau 3: affiche tout
    ]
    
    for level, event_levels, expected_visible in scenarios:
        flux.clear_events()
        flux.set_level(level)
        
        # Logger événements de tous niveaux
        for ev_level in event_levels:
            log_cognitive_event(
                'archiviste',
                f'Événement niveau {ev_level}',
                event_level=ev_level
            )
        
        events = get_recent_events(limit=10)
        visible_levels = [e.get('level', 1) for e in events]
        
        print(f"\n📊 Niveau {level}:")
        print(f"   - Événements loggés: {event_levels}")
        print(f"   - Attendu visible: {expected_visible}")
        print(f"   - Réellement visible: {visible_levels}")
        
        if visible_levels == expected_visible:
            print(f"   ✅ Filtrage correct")
        else:
            print(f"   ❌ Filtrage incorrect")
            return False
    
    return True

# ========================================
# MAIN
# ========================================

if __name__ == "__main__":
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║  🧪 TEST FLUX COGNITIF PHASE 2 (NORMAL)                 ║")
    print("║  Vérification dialogues Archiviste ↔ IA principale      ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    
    tests = [
        ("Événements Phase 2 avec metadata", test_phase2_events),
        ("Filtrage hiérarchique niveaux", test_level_filtering)
    ]
    
    resultats = []
    for nom, test_func in tests:
        print(f"\n{'='*60}")
        print(f"TEST: {nom}")
        print('='*60)
        try:
            resultat = test_func()
            resultats.append(resultat)
            if resultat:
                print(f"\n✅ {nom}: SUCCÈS")
            else:
                print(f"\n❌ {nom}: ÉCHEC")
        except Exception as e:
            print(f"\n❌ ERREUR CRITIQUE: {e}")
            import traceback
            traceback.print_exc()
            resultats.append(False)
    
    # Résumé
    print("\n" + "="*60)
    print("RÉSUMÉ")
    print("="*60)
    total = len(resultats)
    succes = sum(resultats)
    print(f"Tests réussis: {succes}/{total} ({succes/total*100:.1f}%)")
    
    if all(resultats):
        print("\n🎉 TOUS LES TESTS PASSENT !")
        print("✅ Phase 2 (NORMAL) implémentée avec succès")
        print("\n📋 Fonctionnalités validées:")
        print("   ✓ Filtrage événements par niveau (1/2/3)")
        print("   ✓ Metadata enrichies (prompt, response, JSON)")
        print("   ✓ Logging prompts Archiviste")
        print("   ✓ Logging réponses Archiviste")
        print("   ✓ Hiérarchie niveaux (SURFACE < NORMAL < DEEP)")
    else:
        print("\n⚠️ CERTAINS TESTS ONT ÉCHOUÉ")
        print("❌ Vérifier les logs ci-dessus")
    
    sys.exit(0 if all(resultats) else 1)
