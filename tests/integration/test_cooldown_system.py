"""
Test validation : Système Cooldown (20 messages)
================================================

Valide que le système cooldown fonctionne correctement :
1. Compteur de messages incrémenté à chaque tour
2. Souvenirs bloqués pendant 20 messages
3. Souvenirs réautorisés après 20 messages

Auteur: Système OGMA
Date: 27 novembre 2025
"""

import sys
from pathlib import Path

def test_cooldown_implementation():
    """Vérifie l'implémentation complète du système cooldown"""
    
    print("\n" + "="*60)
    print("TEST COOLDOWN : Validation système anti-répétition")
    print("="*60)
    
    # Import du déduplicateur
    from injection_deduplicator import InjectionDeduplicator
    
    dedup = InjectionDeduplicator()
    
    # Test 1: Vérifier seuil 20 messages
    print("\n📋 TEST 1: Vérification seuil cooldown...")
    
    if dedup.cooldown_threshold == 20:
        print(f"✅ PASS: Seuil cooldown = {dedup.cooldown_threshold} messages")
        test1_pass = True
    else:
        print(f"❌ FAIL: Seuil cooldown incorrect = {dedup.cooldown_threshold}")
        test1_pass = False
    
    # Test 2: Simulation injection + cooldown
    print("\n📋 TEST 2: Simulation cycle injection/cooldown...")
    
    memory_id = "TEST_MEM_123"
    
    # Message 1 : Injection souvenir
    dedup.current_message_count = 1
    dedup.register_memory_injection(memory_id)
    print(f"   Message 1: Souvenir {memory_id} injecté")
    
    # Message 5 : Vérifier cooldown actif
    dedup.current_message_count = 5
    is_cooled, remaining = dedup.is_on_cooldown(memory_id)
    
    if is_cooled and remaining == 16:
        print(f"   Message 5: ✅ Cooldown actif ({remaining} messages restants)")
        test2_pass = True
    else:
        print(f"   Message 5: ❌ Cooldown incorrect (is_cooled={is_cooled}, remaining={remaining})")
        test2_pass = False
    
    # Test 3: Vérifier expiration cooldown
    print("\n📋 TEST 3: Vérification expiration cooldown...")
    
    # Message 21 : Cooldown expiré
    dedup.current_message_count = 21
    is_cooled, remaining = dedup.is_on_cooldown(memory_id)
    
    if not is_cooled and remaining == 0:
        print(f"   Message 21: ✅ Cooldown expiré, souvenir réautorisé")
        test3_pass = True
    else:
        print(f"   Message 21: ❌ Cooldown non expiré (is_cooled={is_cooled})")
        test3_pass = False
    
    # Test 4: Filtrage mémoires avec cooldown
    print("\n📋 TEST 4: Test filtrage batch mémoires...")
    
    dedup.reset_session()
    dedup.current_message_count = 1
    
    # Créer souvenirs test
    memories = [
        {'id': 'MEM_A', 'title': 'Souvenir A'},
        {'id': 'MEM_B', 'title': 'Souvenir B'},
        {'id': 'MEM_C', 'title': 'Souvenir C'},
    ]
    
    # Injecter MEM_A au message 1
    dedup.register_memory_injection('MEM_A')
    
    # Message 5 : Filtrer batch
    dedup.current_message_count = 5
    allowed, blocked = dedup.filter_memories_by_cooldown(memories)
    
    allowed_ids = [m['id'] for m in allowed]
    blocked_ids = [m['id'] for m in blocked]
    
    if 'MEM_A' in blocked_ids and 'MEM_B' in allowed_ids and 'MEM_C' in allowed_ids:
        print(f"   ✅ Filtrage correct:")
        print(f"      - Autorisés: {allowed_ids}")
        print(f"      - Bloqués: {blocked_ids}")
        test4_pass = True
    else:
        print(f"   ❌ Filtrage incorrect:")
        print(f"      - Autorisés: {allowed_ids}")
        print(f"      - Bloqués: {blocked_ids}")
        test4_pass = False
    
    # Test 5: Vérifier intégration ogma_ng.py
    print("\n📋 TEST 5: Vérification intégration ogma_ng.py...")
    
    ogma_file = Path("ogma_ng.py")
    content = ogma_file.read_text(encoding='utf-8')
    
    if "increment_message_count()" in content:
        print("   ✅ Incrément compteur présent dans ogma_ng.py")
        test5_pass = True
    else:
        print("   ❌ Incrément compteur manquant dans ogma_ng.py")
        test5_pass = False
    
    # Test 6: Vérifier intégration archiviste_memory_optimizer.py
    print("\n📋 TEST 6: Vérification intégration archiviste...")
    
    optimizer_file = Path("archiviste_memory_optimizer.py")
    content = optimizer_file.read_text(encoding='utf-8')
    
    if "filter_memories_by_cooldown" in content and "register_memory_injection" in content:
        print("   ✅ Filtrage cooldown présent dans archiviste_memory_optimizer.py")
        test6_pass = True
    else:
        print("   ❌ Filtrage cooldown manquant")
        test6_pass = False
    
    # Résumé
    print("\n" + "="*60)
    all_tests = [test1_pass, test2_pass, test3_pass, test4_pass, test5_pass, test6_pass]
    passed = sum(all_tests)
    total = len(all_tests)
    
    if passed == total:
        print(f"✅ TOUS LES TESTS RÉUSSIS ({passed}/{total})")
        print("="*60)
        print("\n💡 SYSTÈME COOLDOWN OPÉRATIONNEL")
        print("\n📊 FONCTIONNEMENT:")
        print("   - Seuil: 20 messages")
        print("   - Compteur: Incrémenté à chaque message utilisateur")
        print("   - Filtrage: Souvenirs bloqués pendant 20 messages")
        print("   - Réinjection: Autorisée après expiration cooldown")
        print("\n🎯 BÉNÉFICES:")
        print("   - Évite répétition mécanique du même souvenir")
        print("   - Force diversité contextuelle")
        print("   - Prévient effet 'disque rayé'")
        print("   - Économie tokens indirecte (pas de doublons)")
        print("="*60)
        return True
    else:
        print(f"❌ TESTS ÉCHOUÉS ({total-passed}/{total})")
        print("="*60)
        return False

if __name__ == "__main__":
    success = test_cooldown_implementation()
    sys.exit(0 if success else 1)
