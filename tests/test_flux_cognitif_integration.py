#!/usr/bin/env python3
"""
🧪 TEST INTÉGRATION FLUX COGNITIF v2.0
Vérifie le remplacement complet de ego_mirror
"""

import os
import sys

def test_fichiers_crees():
    """Vérifier que les fichiers flux_cognitif existent"""
    print("\n=== TEST 1: Fichiers créés ===")
    
    fichiers_requis = [
        "extensions/flux_cognitif/__init__.py",
        "extensions/flux_cognitif/stream_ui.py"
    ]
    
    for fichier in fichiers_requis:
        chemin = os.path.join("c:\\IA\\OGMA", fichier)
        if os.path.exists(chemin):
            taille = os.path.getsize(chemin)
            print(f"✅ {fichier} ({taille} octets)")
        else:
            print(f"❌ {fichier} MANQUANT")
            return False
    
    return True

def test_fichiers_supprimes():
    """Vérifier que les fichiers ego_mirror sont supprimés"""
    print("\n=== TEST 2: Fichiers obsolètes supprimés ===")
    
    fichiers_obsoletes = [
        "modules/ego_mirror_bridge.py",
        "static/ego_mirror_widget.html"
    ]
    
    for fichier in fichiers_obsoletes:
        chemin = os.path.join("c:\\IA\\OGMA", fichier)
        if not os.path.exists(chemin):
            print(f"✅ {fichier} supprimé")
        else:
            print(f"❌ {fichier} EXISTE ENCORE")
            return False
    
    return True

def test_imports_flux_cognitif():
    """Tester l'import de l'extension flux_cognitif"""
    print("\n=== TEST 3: Import extension ===")
    
    try:
        sys.path.insert(0, "c:\\IA\\OGMA")
        from extensions.flux_cognitif import (
            initialize_flux_cognitif,
            log_cognitive_event,
            is_available,
            get_recent_events
        )
        print("✅ Imports API publique OK")
        print(f"   - initialize_flux_cognitif: {initialize_flux_cognitif}")
        print(f"   - log_cognitive_event: {log_cognitive_event}")
        print(f"   - is_available: {is_available}")
        print(f"   - get_recent_events: {get_recent_events}")
        return True
    except Exception as e:
        print(f"❌ Erreur import: {e}")
        return False

def test_singleton_pattern():
    """Vérifier le pattern singleton"""
    print("\n=== TEST 4: Singleton pattern ===")
    
    try:
        from extensions.flux_cognitif import initialize_flux_cognitif, is_available
        
        # Initialiser 2 fois
        flux1 = initialize_flux_cognitif()
        flux2 = initialize_flux_cognitif()
        
        if flux1 is flux2:
            print("✅ Singleton OK (même instance)")
        else:
            print("❌ Singleton FAIL (instances différentes)")
            return False
        
        # Vérifier disponibilité
        if is_available():
            print("✅ is_available() retourne True")
        else:
            print("❌ is_available() retourne False")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Erreur singleton: {e}")
        return False

def test_logging_events():
    """Tester l'enregistrement d'événements"""
    print("\n=== TEST 5: Logging événements ===")
    
    try:
        from extensions.flux_cognitif import log_cognitive_event, get_recent_events
        
        # Logger quelques événements
        log_cognitive_event('archiviste', 'Souvenirs: 10 injectés')
        log_cognitive_event('biography', 'Biographie (5 souvenirs)')
        log_cognitive_event('dream', 'Rêve (rapport PSY)')
        
        # Récupérer événements
        events = get_recent_events(limit=10)
        
        if len(events) >= 3:
            print(f"✅ {len(events)} événements enregistrés")
            for event in events[-3:]:
                print(f"   - [{event['source']}] {event['message']}")
        else:
            print(f"❌ Seulement {len(events)} événements (attendu: >= 3)")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Erreur logging: {e}")
        return False

def test_ui_components():
    """Vérifier que le module UI existe"""
    print("\n=== TEST 6: Composants UI ===")
    
    try:
        from extensions.flux_cognitif.stream_ui import FluxCognitifUI
        print("✅ FluxCognitifUI importé")
        print(f"   - Classe: {FluxCognitifUI}")
        return True
    except Exception as e:
        print(f"❌ Erreur import UI: {e}")
        return False

def test_references_ego_mirror():
    """Vérifier qu'il ne reste pas de références ego_mirror dans le code actif"""
    print("\n=== TEST 7: Pas de références résiduelles ego_mirror ===")
    
    fichiers_actifs = [
        "ogma_ng.py",
        "ogma_headers.py",
        "core_logic.py",
        "memory_manager.py"
    ]
    
    references_trouvees = []
    
    for fichier in fichiers_actifs:
        chemin = os.path.join("c:\\IA\\OGMA", fichier)
        if os.path.exists(chemin):
            with open(chemin, 'r', encoding='utf-8') as f:
                contenu = f.read()
                if 'ego_mirror' in contenu:
                    references_trouvees.append(fichier)
    
    if not references_trouvees:
        print("✅ Aucune référence ego_mirror dans les fichiers actifs")
        return True
    else:
        print(f"❌ Références ego_mirror trouvées dans: {references_trouvees}")
        return False

# ========================================
# MAIN
# ========================================

if __name__ == "__main__":
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║  🧪 TEST INTÉGRATION FLUX COGNITIF v2.0                 ║")
    print("║  Vérification remplacement complet ego_mirror            ║")
    print("╚═══════════════════════════════════════════════════════════╝")
    
    tests = [
        test_fichiers_crees,
        test_fichiers_supprimes,
        test_imports_flux_cognitif,
        test_singleton_pattern,
        test_logging_events,
        test_ui_components,
        test_references_ego_mirror
    ]
    
    resultats = []
    for test in tests:
        try:
            resultats.append(test())
        except Exception as e:
            print(f"❌ ERREUR CRITIQUE: {e}")
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
        print("✅ Remplacement ego_mirror → flux_cognitif COMPLET")
    else:
        print("\n⚠️ CERTAINS TESTS ONT ÉCHOUÉ")
        print("❌ Vérifier les logs ci-dessus")
    
    sys.exit(0 if all(resultats) else 1)
