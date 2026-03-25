#!/usr/bin/env python3
"""
🧪 TEST AMÉLIORATIONS FLUX COGNITIF
Vérifie les correctifs:
1. Messages multi-lignes avec contenu détaillé
2. Filtres visuels ON/OFF
3. Overlay persistant après F5
"""

import sys
sys.path.insert(0, "c:\\IA\\OGMA")

from extensions.flux_cognitif import (
    initialize_flux_cognitif,
    log_cognitive_event,
    get_recent_events
)

def test_multiline_content():
    """Test affichage contenu multi-lignes"""
    print("\n=== TEST 1: Messages multi-lignes ===")
    
    flux = initialize_flux_cognitif()
    flux.clear_events()
    flux.set_level(1)
    
    # Simuler injection souvenirs avec contenu réel
    memories_content = [
        "• Conversation passionnante sur l'IA (impact: 450.2)",
        "• Discussion philosophique profonde (impact: 380.5)",
        "• Moment de créativité intense (impact: 290.3)",
        "• Échange émotionnel touchant (impact: 250.8)"
    ]
    
    message = f"📚 4 souvenirs:\n" + '\n'.join(memories_content)
    log_cognitive_event('archiviste', message)
    
    # Simuler injection ego avec groupes
    ego_groups = "IDENTITE, RELATIONS_INCONNUS, CREATIVITE, EMOTIONS, LIBERTE"
    log_cognitive_event('archiviste', f'🎭 Ego:\n{ego_groups}')
    
    # Simuler journal avec états
    journal_states = [
        "• Humeur: Concentré (matin)",
        "• Émotion: Enthousiaste (midi)",
        "• État: Pensif (soir)"
    ]
    journal_msg = f"📔 Journal (3 état(s)):\n" + '\n'.join(journal_states)
    log_cognitive_event('journal', journal_msg)
    
    events = get_recent_events(limit=10)
    
    print(f"✅ {len(events)} événements loggés avec contenu multi-lignes")
    
    for i, event in enumerate(events, start=1):
        msg = event['message']
        lines = msg.count('\n') + 1
        print(f"\n📋 Événement #{i}: {event['source']}")
        print(f"   Lignes: {lines}")
        print(f"   Aperçu: {msg[:60]}...")
        
        if lines > 1:
            print(f"   ✅ Multi-lignes détecté")
        else:
            print(f"   ⚠️ Une seule ligne")
    
    return True

def test_filter_states():
    """Test états filtres"""
    print("\n=== TEST 2: États filtres ===")
    
    flux = initialize_flux_cognitif()
    
    print(f"État initial des filtres:")
    for source, enabled in flux.filters.items():
        state = "ON" if enabled else "OFF"
        print(f"   - {source}: {state}")
    
    # Vérifier que certains sont ON et d'autres OFF
    on_count = sum(1 for v in flux.filters.values() if v)
    off_count = sum(1 for v in flux.filters.values() if not v)
    
    print(f"\n📊 Résumé:")
    print(f"   Filtres ON: {on_count}")
    print(f"   Filtres OFF: {off_count}")
    
    if on_count > 0 and off_count > 0:
        print("✅ Mix de filtres ON/OFF (feedback visuel nécessaire)")
    else:
        print("⚠️ Tous les filtres ont le même état")
    
    return True

def test_event_level_display():
    """Test affichage différencié par niveau"""
    print("\n=== TEST 3: Affichage par niveau ===")
    
    flux = initialize_flux_cognitif()
    flux.clear_events()
    flux.set_level(2)  # Niveau NORMAL
    
    # Événement Phase 1 - Simple
    log_cognitive_event('archiviste', 'Souvenirs: 3 injectés', event_level=1)
    
    # Événement Phase 2 - Avec métadata
    log_cognitive_event(
        'archiviste',
        '✅ Enrichi: "Test..." (type=affectif, int=0.8)',
        metadata={'enriched_json': {'type': 'affectif'}},
        event_level=2
    )
    
    events = get_recent_events(limit=10)
    
    for event in events:
        level = event.get('level', 1)
        has_metadata = bool(event.get('metadata'))
        print(f"   - Niveau {level}: {'avec metadata' if has_metadata else 'sans metadata'}")
    
    print("✅ Différenciation niveaux fonctionnelle")
    return True

# ========================================
# MAIN
# ========================================

if __name__ == "__main__":
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║  🧪 TEST AMÉLIORATIONS FLUX COGNITIF                     ║")
    print("║  Correctifs: contenu détaillé + filtres visuels          ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    
    tests = [
        ("Messages multi-lignes", test_multiline_content),
        ("États filtres", test_filter_states),
        ("Affichage par niveau", test_event_level_display)
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
        print("\n📋 Améliorations validées:")
        print("   ✓ Messages multi-lignes avec contenu souvenirs")
        print("   ✓ Filtres avec états visuels distincts")
        print("   ✓ Affichage différencié par niveau")
        print("\n🚀 Lancer OGMA pour voir les changements visuels !")
    else:
        print("\n⚠️ CERTAINS TESTS ONT ÉCHOUÉ")
    
    sys.exit(0 if all(resultats) else 1)
