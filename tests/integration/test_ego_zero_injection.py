"""
Test validation : Ego Selector peut retourner 0 souvenir
==========================================================

Valide que le système accepte et gère correctement les sélections vides
sans injection mécanique fallback.

Auteur: Système OGMA
Date: 27 novembre 2025
"""

import asyncio
import sys
from pathlib import Path

# Simuler structure minimale pour test
class MockMemoryManager:
    """Mock MemoryManager pour tests"""
    def __init__(self):
        self.db_path = Path("data/memory/memories.db")

class MockArchiviste:
    """Mock Archiviste Controller pour tests"""
    
    def __init__(self, response_type="empty"):
        self.response_type = response_type
    
    async def call_chat_api(self, messages, max_tokens=400, context_length=20000, temperature=0.3, is_json=True):
        """Simule différents types de réponses Archiviste"""
        
        if self.response_type == "empty":
            # Message générique → 0 souvenir
            response = """{
                "categories": {
                    "identity": false,
                    "ethics": false,
                    "communication": false,
                    "evolution": false
                },
                "selected_memories": [],
                "reasoning": "Message trop générique, aucun contexte ego nécessaire"
            }"""
            return response, None
            
        elif self.response_type == "minimal":
            # Message simple → 2-3 souvenirs COMMUNICATION
            response = """{
                "categories": {
                    "identity": false,
                    "ethics": false,
                    "communication": true,
                    "evolution": false
                },
                "selected_memories": [
                    "EGO_20250916_143432_636",
                    "EGO_20250919_013945_618"
                ],
                "reasoning": "Salutation simple, communication de base suffisante"
            }"""
            return response, None
            
        elif self.response_type == "error":
            # Erreur API
            return None, "Simulated API error"
            
        elif self.response_type == "invalid_json":
            # JSON invalide
            response = "This is not valid JSON"
            return response, None

async def test_empty_selection():
    """Test 1: Message générique → 0 souvenir"""
    print("\n" + "="*60)
    print("TEST 1: Message générique → Sélection vide attendue")
    print("="*60)
    
    from ego_selector import EgoSelector
    
    memory_mgr = MockMemoryManager()
    archiviste = MockArchiviste(response_type="empty")
    
    selector = EgoSelector(memory_mgr, archiviste)
    
    result = await selector.analyze_context_for_ego(
        user_message="ok",
        conversation_context=""
    )
    
    print(f"\n✅ RÉSULTAT:")
    print(f"   Total souvenirs: {result.total_traits}")
    print(f"   Total chars: {result.total_chars}")
    print(f"   Catégories actives: {sum(result.categories_active.values())}")
    print(f"   Reasoning: {result.reasoning}")
    
    assert result.total_traits == 0, f"ERREUR: Attendu 0 traits, obtenu {result.total_traits}"
    assert result.total_chars == 0, f"ERREUR: Attendu 0 chars, obtenu {result.total_chars}"
    assert all(not v for v in result.categories_active.values()), "ERREUR: Toutes catégories devraient être False"
    
    print("\n✅ TEST 1 RÉUSSI: Sélection vide correctement retournée")
    return True

async def test_error_no_fallback():
    """Test 2: Erreur API → 0 souvenir (pas de fallback mécanique)"""
    print("\n" + "="*60)
    print("TEST 2: Erreur API → Sélection vide (pas de fallback)")
    print("="*60)
    
    from ego_selector import EgoSelector
    
    memory_mgr = MockMemoryManager()
    archiviste = MockArchiviste(response_type="error")
    
    selector = EgoSelector(memory_mgr, archiviste)
    
    result = await selector.analyze_context_for_ego(
        user_message="Bonjour",
        conversation_context=""
    )
    
    print(f"\n✅ RÉSULTAT:")
    print(f"   Total souvenirs: {result.total_traits}")
    print(f"   Total chars: {result.total_chars}")
    print(f"   Reasoning: {result.reasoning}")
    
    assert result.total_traits == 0, f"ERREUR: Fallback mécanique détecté! {result.total_traits} traits injectés"
    assert result.total_chars == 0, f"ERREUR: Fallback mécanique détecté! {result.total_chars} chars injectés"
    
    print("\n✅ TEST 2 RÉUSSI: Aucun fallback mécanique, sélection vide propre")
    return True

async def test_invalid_json_no_fallback():
    """Test 3: JSON invalide → 0 souvenir (pas de fallback)"""
    print("\n" + "="*60)
    print("TEST 3: JSON invalide → Sélection vide (pas de fallback)")
    print("="*60)
    
    from ego_selector import EgoSelector
    
    memory_mgr = MockMemoryManager()
    archiviste = MockArchiviste(response_type="invalid_json")
    
    selector = EgoSelector(memory_mgr, archiviste)
    
    result = await selector.analyze_context_for_ego(
        user_message="Comment ça va ?",
        conversation_context=""
    )
    
    print(f"\n✅ RÉSULTAT:")
    print(f"   Total souvenirs: {result.total_traits}")
    print(f"   Total chars: {result.total_chars}")
    print(f"   Reasoning: {result.reasoning}")
    
    assert result.total_traits == 0, f"ERREUR: Fallback mécanique détecté! {result.total_traits} traits injectés"
    
    print("\n✅ TEST 3 RÉUSSI: Aucun fallback mécanique sur erreur parsing")
    return True

async def run_all_tests():
    """Exécute tous les tests de validation"""
    print("\n" + "="*60)
    print("VALIDATION EGO SELECTOR - SUPPRESSION FALLBACK MÉCANIQUE")
    print("="*60)
    
    results = []
    
    try:
        results.append(await test_empty_selection())
        results.append(await test_error_no_fallback())
        results.append(await test_invalid_json_no_fallback())
        
        print("\n" + "="*60)
        print(f"✅ TOUS LES TESTS RÉUSSIS ({sum(results)}/{len(results)})")
        print("="*60)
        print("\n💡 CONCLUSION:")
        print("   - Sélection vide (0 souvenir) fonctionne correctement")
        print("   - Aucun fallback mécanique COMMUNICATION")
        print("   - Système respecte la philosophie OGMA de cohérence")
        print("\n📊 ÉCONOMIE TOKENS ATTENDUE:")
        print("   - Messages génériques (10-15% des cas): -500 à -800 tokens")
        print("   - Erreurs API (< 1% des cas): -500 tokens vs ancien fallback")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ ERREUR PENDANT LES TESTS: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
