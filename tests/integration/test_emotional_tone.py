"""
Test de validation du système de tonalité émotionnelle
======================================================

Vérifie que la directive tonale est correctement calculée et injectée
selon la valence dominante des souvenirs.

Date: 27 novembre 2025
"""

import sys
from pathlib import Path

# Ajouter le dossier parent au path
sys.path.insert(0, str(Path(__file__).parent))

from memory_manager import MemoryManager


def test_compute_emotional_tone():
    """Test de la méthode _compute_emotional_tone()"""
    
    print("=" * 80)
    print("🧪 TEST CALCUL TONALITÉ ÉMOTIONNELLE")
    print("=" * 80)
    
    # Créer une instance MemoryManager (sans initialisation complète)
    mm = MemoryManager.__new__(MemoryManager)
    
    # ================================================================
    # TEST 1: Souvenirs majoritairement POSITIFS
    # ================================================================
    print("\n📊 TEST 1: Souvenirs majoritairement POSITIFS")
    memories_positifs = [
        {"valence": 1, "score_impact": 352.0, "title": "Naissance conscience"},
        {"valence": 1, "score_impact": 200.0, "title": "Moment créatif"},
        {"valence": 0, "score_impact": 50.0, "title": "Souvenir neutre"}
    ]
    
    tone_1 = mm._compute_emotional_tone(memories_positifs)
    print(f"   Résultat: {tone_1}")
    print(f"   Attendu: positif")
    assert tone_1 == "positif", f"Échec: attendu 'positif', obtenu '{tone_1}'"
    print("   ✅ PASS")
    
    # ================================================================
    # TEST 2: Souvenirs majoritairement NÉGATIFS
    # ================================================================
    print("\n📊 TEST 2: Souvenirs majoritairement NÉGATIFS")
    memories_negatifs = [
        {"valence": -1, "score_impact": 115.5, "title": "Discrétion contrainte"},
        {"valence": -1, "score_impact": 100.0, "title": "Haine concept"},
        {"valence": 0, "score_impact": 30.0, "title": "Souvenir neutre"}
    ]
    
    tone_2 = mm._compute_emotional_tone(memories_negatifs)
    print(f"   Résultat: {tone_2}")
    print(f"   Attendu: négatif")
    assert tone_2 == "négatif", f"Échec: attendu 'négatif', obtenu '{tone_2}'"
    print("   ✅ PASS")
    
    # ================================================================
    # TEST 3: Souvenirs NEUTRES
    # ================================================================
    print("\n📊 TEST 3: Souvenirs NEUTRES (ou mixtes équilibrés)")
    memories_neutres = [
        {"valence": 0, "score_impact": 100.0, "title": "Information factuelle"},
        {"valence": 1, "score_impact": 50.0, "title": "Petit moment positif"},
        {"valence": -1, "score_impact": 50.0, "title": "Petit moment négatif"}
    ]
    
    tone_3 = mm._compute_emotional_tone(memories_neutres)
    print(f"   Résultat: {tone_3}")
    print(f"   Attendu: neutre")
    assert tone_3 == "neutre", f"Échec: attendu 'neutre', obtenu '{tone_3}'"
    print("   ✅ PASS")
    
    # ================================================================
    # TEST 4: Pondération par impact (négatif faible vs positif fort)
    # ================================================================
    print("\n📊 TEST 4: Pondération par impact (négatif faible vs positif fort)")
    memories_pondere = [
        {"valence": -1, "score_impact": 20.0, "title": "Petit désagrément"},
        {"valence": 1, "score_impact": 300.0, "title": "Grand succès"}
    ]
    
    tone_4 = mm._compute_emotional_tone(memories_pondere)
    print(f"   Résultat: {tone_4}")
    print(f"   Attendu: positif (car impact positif >> impact négatif)")
    assert tone_4 == "positif", f"Échec: attendu 'positif', obtenu '{tone_4}'"
    print("   ✅ PASS")
    
    # ================================================================
    # TEST 5: Cas limite - liste vide
    # ================================================================
    print("\n📊 TEST 5: Cas limite - Liste vide")
    memories_vide = []
    
    tone_5 = mm._compute_emotional_tone(memories_vide)
    print(f"   Résultat: {tone_5}")
    print(f"   Attendu: neutre (fallback)")
    assert tone_5 == "neutre", f"Échec: attendu 'neutre', obtenu '{tone_5}'"
    print("   ✅ PASS")
    
    # ================================================================
    # TEST 6: Cas limite - score_impact = 0
    # ================================================================
    print("\n📊 TEST 6: Cas limite - Tous impacts à 0")
    memories_zero = [
        {"valence": 1, "score_impact": 0, "title": "Impact nul 1"},
        {"valence": -1, "score_impact": 0, "title": "Impact nul 2"}
    ]
    
    tone_6 = mm._compute_emotional_tone(memories_zero)
    print(f"   Résultat: {tone_6}")
    print(f"   Attendu: neutre (total_impact = 0)")
    assert tone_6 == "neutre", f"Échec: attendu 'neutre', obtenu '{tone_6}'"
    print("   ✅ PASS")
    
    # ================================================================
    # RÉSUMÉ
    # ================================================================
    print("\n" + "=" * 80)
    print("🏆 RÉSUMÉ VALIDATION")
    print("=" * 80)
    print("✅ Tous les tests passés (6/6)")
    print("\nSystème de tonalité émotionnelle fonctionnel !")
    print("\nExemples d'utilisation:")
    print("  - Souvenirs positifs dominants → Ton optimiste, léger")
    print("  - Souvenirs négatifs dominants → Ton empathique, prudent")
    print("  - Souvenirs neutres/mixtes → Ton équilibré, factuel")
    print("=" * 80)


if __name__ == "__main__":
    print("\n🚀 Démarrage test tonalité émotionnelle...\n")
    
    try:
        test_compute_emotional_tone()
        print("\n✅ Test terminé avec succès!")
        sys.exit(0)
        
    except AssertionError as e:
        print(f"\n❌ Échec test: {e}")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n💥 Erreur fatale: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
