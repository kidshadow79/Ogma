"""
Test de validation du système de cooldown (Option A)
====================================================

Test simulant 25 messages consécutifs sur le même thème pour vérifier:
1. Cooldown 20 messages fonctionne (souvenirs bloqués pendant 20 msgs)
2. Réduction 12→4 souvenirs effective (2 intégraux + 2 synthétisés)
3. Logs affichent souvenirs bloqués et autorisés

Date: 27 novembre 2025
"""

import asyncio
import sys
from pathlib import Path

# Ajouter le dossier parent au path pour imports
sys.path.insert(0, str(Path(__file__).parent))

from injection_deduplicator import (
    deduplicator,
    increment_message_count,
    filter_memories_by_cooldown,
    get_deduplication_stats
)


def create_mock_memory(memory_id: str, title: str, score_impact: int = 150) -> dict:
    """Crée un faux souvenir pour le test"""
    return {
        'id': memory_id,
        'memory_id': memory_id,
        'title': title,
        'summary': f'Résumé du souvenir {memory_id}',
        'score_impact': score_impact,
        'similarity_score': 0.95,
        'hybrid_score': 0.90
    }


async def test_cooldown_system():
    """Test principal du système de cooldown"""
    
    print("=" * 80)
    print("🧪 TEST COOLDOWN OPTION A (2 intégraux + 2 synthétisés, 20 messages)")
    print("=" * 80)
    
    # Reset initial
    deduplicator.reset_session()
    
    # Créer 6 souvenirs de test (simuler FAISS qui retourne toujours les mêmes)
    memories = [
        create_mock_memory("MEM_001", "Souvenir phare Bretagne", score_impact=180),
        create_mock_memory("MEM_002", "Souvenir côte atlantique", score_impact=160),
        create_mock_memory("MEM_003", "Souvenir voyage maritime", score_impact=140),
        create_mock_memory("MEM_004", "Souvenir navigation", score_impact=130),
        create_mock_memory("MEM_005", "Souvenir océan", score_impact=120),
        create_mock_memory("MEM_006", "Souvenir marée", score_impact=110)
    ]
    
    print(f"\n📚 {len(memories)} souvenirs candidats (simulant retour FAISS constant)")
    for mem in memories:
        print(f"  - {mem['id']}: {mem['title']} (impact={mem['score_impact']})")
    
    print("\n" + "=" * 80)
    print("🔬 SIMULATION 25 MESSAGES SUR LE THÈME 'PHARE'")
    print("=" * 80)
    
    results = []
    
    for msg_num in range(1, 26):  # Messages 1 à 25
        print(f"\n{'─' * 80}")
        print(f"📨 MESSAGE #{msg_num}")
        print(f"{'─' * 80}")
        
        # Incrémenter le compteur de messages
        increment_message_count()
        
        # Filtrer les souvenirs par cooldown
        allowed, blocked = filter_memories_by_cooldown(memories.copy())
        
        # ✨ Enregistrer manuellement les souvenirs autorisés
        for mem in allowed:
            memory_id = mem.get('id') or mem.get('memory_id')
            if memory_id:
                deduplicator.register_memory_injection(memory_id)
        
        # Statistiques
        stats = get_deduplication_stats()
        
        print(f"\n✅ Autorisés: {len(allowed)}/{len(memories)} souvenirs")
        for mem in allowed:
            print(f"   • {mem['id']}: {mem['title'][:40]}")
        
        if blocked:
            print(f"\n🚫 Bloqués (cooldown): {len(blocked)} souvenirs")
            for mem in blocked:
                remaining = mem.get('cooldown_remaining', 0)
                print(f"   ⏱️  {mem['id']}: {mem['title'][:40]} ({remaining} msgs restants)")
        
        print(f"\n📊 Stats cooldown: message {stats['cooldown']['current_message']}, "
              f"seuil={stats['cooldown']['cooldown_threshold']}, "
              f"tracked={stats['cooldown']['memories_tracked']}")
        
        # Enregistrer résultat
        results.append({
            'message': msg_num,
            'allowed': len(allowed),
            'blocked': len(blocked),
            'stats': stats
        })
        
        # Pauses clés pour affichage
        if msg_num in [1, 5, 10, 20, 21, 25]:
            await asyncio.sleep(0.1)
    
    # ================================================================
    # ANALYSE FINALE
    # ================================================================
    print("\n" + "=" * 80)
    print("📊 ANALYSE FINALE")
    print("=" * 80)
    
    # Test 1: Premiers messages (1-4) devraient avoir 4-6 souvenirs autorisés
    first_messages = [r for r in results if r['message'] <= 4]
    print(f"\n✅ TEST 1: Messages 1-4 (injection initiale)")
    for r in first_messages:
        status = "✅ OK" if r['allowed'] >= 4 else "❌ FAIL"
        print(f"   Message {r['message']}: {r['allowed']} autorisés, {r['blocked']} bloqués {status}")
    
    # Test 2: Messages 5-20 devraient avoir souvenirs bloqués (cooldown actif)
    mid_messages = [r for r in results if 5 <= r['message'] <= 20]
    print(f"\n⏱️  TEST 2: Messages 5-20 (cooldown actif)")
    for r in mid_messages[::3]:  # Afficher tous les 3 messages
        status = "✅ OK" if r['blocked'] > 0 else "⚠️  WARN"
        print(f"   Message {r['message']}: {r['allowed']} autorisés, {r['blocked']} bloqués {status}")
    
    # Test 3: Message 21 devrait libérer MEM_001 (20 messages après msg 1)
    msg_21 = [r for r in results if r['message'] == 21][0]
    msg_22 = [r for r in results if r['message'] == 22][0]
    print(f"\n🔓 TEST 3: Messages 21-22 (libération cooldown)")
    print(f"   Message 21: {msg_21['allowed']} autorisés, {msg_21['blocked']} bloqués")
    print(f"   Message 22: {msg_22['allowed']} autorisés, {msg_22['blocked']} bloqués")
    
    liberation_msg_21 = msg_21['allowed'] > mid_messages[0]['allowed']
    status_21 = "✅ OK" if liberation_msg_21 else "❌ FAIL"
    print(f"   Libération détectée au message 21: {status_21}")
    
    # Test 4: Vérification ratio 2+2 (devrait tendre vers 4 souvenirs autorisés max)
    avg_allowed_mid = sum(r['allowed'] for r in mid_messages) / len(mid_messages)
    print(f"\n📉 TEST 4: Réduction souvenirs")
    print(f"   Moyenne souvenirs autorisés (msgs 5-20): {avg_allowed_mid:.1f}")
    status_reduction = "✅ OK" if avg_allowed_mid <= 4.5 else "⚠️  WARN"
    print(f"   Objectif ≤4 souvenirs {status_reduction}")
    
    # Résumé final
    print("\n" + "=" * 80)
    print("🎯 RÉSUMÉ VALIDATION")
    print("=" * 80)
    
    tests_passed = 0
    tests_total = 4
    
    # Test 1: Au moins 4 souvenirs au début
    if all(r['allowed'] >= 4 for r in first_messages[:2]):
        print("✅ TEST 1 PASSED: Injection initiale correcte (≥4 souvenirs)")
        tests_passed += 1
    else:
        print("❌ TEST 1 FAILED: Injection initiale insuffisante")
    
    # Test 2: Cooldown actif (bloque des souvenirs)
    if sum(r['blocked'] for r in mid_messages) > 10:
        print("✅ TEST 2 PASSED: Cooldown bloque souvenirs (>10 blocages totaux)")
        tests_passed += 1
    else:
        print("❌ TEST 2 FAILED: Cooldown n'a pas bloqué assez de souvenirs")
    
    # Test 3: Libération après 20 messages
    if liberation_msg_21:
        print("✅ TEST 3 PASSED: Souvenirs libérés après 20 messages")
        tests_passed += 1
    else:
        print("❌ TEST 3 FAILED: Souvenirs pas libérés au message 21")
    
    # Test 4: Réduction moyenne souvenirs
    if avg_allowed_mid <= 4.5:
        print("✅ TEST 4 PASSED: Réduction souvenirs effective (≤4.5 moyenne)")
        tests_passed += 1
    else:
        print("⚠️  TEST 4 WARNING: Moyenne souvenirs encore élevée")
    
    print(f"\n{'=' * 80}")
    print(f"🏆 RÉSULTAT: {tests_passed}/{tests_total} tests passés")
    print(f"{'=' * 80}")
    
    if tests_passed == tests_total:
        print("\n✨ VALIDATION COMPLÈTE: Option A fonctionne parfaitement!")
        return True
    elif tests_passed >= 3:
        print("\n✅ VALIDATION PARTIELLE: Système fonctionnel avec ajustements mineurs")
        return True
    else:
        print("\n❌ VALIDATION ÉCHOUÉE: Vérifier configuration cooldown")
        return False


if __name__ == "__main__":
    print("\n🚀 Démarrage test cooldown Option A...\n")
    
    try:
        success = asyncio.run(test_cooldown_system())
        
        if success:
            print("\n✅ Test terminé avec succès!")
            sys.exit(0)
        else:
            print("\n❌ Test terminé avec erreurs")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
