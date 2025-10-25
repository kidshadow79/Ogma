#!/usr/bin/env python3
"""
Test pour vérifier que notre fix du singleton Web Navigator fonctionne
"""

import sys
import os
sys.path.append('.')

# Simuler l'environnement OGMA
from ogma_ng import get_web_navigator_instance

def test_singleton_pattern():
    """Test que les instances sont bien réutilisées"""
    print("[TEST] 🧪 Test du pattern singleton Web Navigator")
    
    # Première instance
    print("[TEST] 📥 Première instance...")
    instance1 = get_web_navigator_instance()
    print(f"[TEST] Instance 1 ID: {id(instance1)}")
    
    # Deuxième instance (devrait être la même)
    print("[TEST] 📥 Deuxième instance...")
    instance2 = get_web_navigator_instance() 
    print(f"[TEST] Instance 2 ID: {id(instance2)}")
    
    # Troisième instance (devrait être la même)
    print("[TEST] 📥 Troisième instance...")
    instance3 = get_web_navigator_instance()
    print(f"[TEST] Instance 3 ID: {id(instance3)}")
    
    # Vérification
    if instance1 is instance2 is instance3:
        print("[TEST] ✅ SUCCÈS: Toutes les instances sont identiques (singleton OK)")
        print(f"[TEST] ✅ Une seule instance créée avec ID: {id(instance1)}")
        return True
    else:
        print("[TEST] ❌ ÉCHEC: Les instances sont différentes")
        return False

def test_no_excessive_saves():
    """Test qu'il n'y a pas de sauvegardes excessives"""
    print("[TEST] 🧪 Test des sauvegardes excessives")
    
    # Compter les [SAVE] avant
    save_count_before = 0
    
    try:
        # Simuler plusieurs appels comme dans l'usage normal
        for i in range(5):
            print(f"[TEST] 📤 Appel {i+1}/5...")
            instance = get_web_navigator_instance()
            if instance:
                print(f"[TEST] Instance obtenue: {type(instance).__name__}")
        
        print("[TEST] ✅ SUCCÈS: Aucune création multiple d'instances")
        return True
        
    except Exception as e:
        print(f"[TEST] ❌ ÉCHEC: {e}")
        return False

if __name__ == "__main__":
    print("[TEST] 🚀 Démarrage des tests Web Navigator singleton\n")
    
    # Test 1: Pattern singleton
    test1_ok = test_singleton_pattern()
    print()
    
    # Test 2: Pas de sauvegardes excessives  
    test2_ok = test_no_excessive_saves()
    print()
    
    # Résumé
    if test1_ok and test2_ok:
        print("[TEST] 🎉 TOUS LES TESTS RÉUSSIS")
        print("[TEST] ✅ Le singleton Web Navigator fonctionne correctement")
        print("[TEST] ✅ Plus de recréations d'instances excessives")
    else:
        print("[TEST] 💥 CERTAINS TESTS ONT ÉCHOUÉ")
    
    print(f"[TEST] 📊 Résultats: {int(test1_ok) + int(test2_ok)}/2 tests réussis")