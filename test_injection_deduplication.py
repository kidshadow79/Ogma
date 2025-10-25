"""
Test de validation du système de déduplication OGMA
=================================================

Ce script teste le système de déduplication hybride pour vérifier :
1. La détection correcte des redondances ego
2. La génération d'instructions d'exclusion précises
3. Les performances du pre-processeur
4. L'intégration complète dans le flux OGMA
"""

import asyncio
import time
from typing import List, Dict
import sys
import os

# Ajouter le répertoire parent pour les imports OGMA
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from injection_deduplicator import (
    InjectionDeduplicator, reset_deduplication_session,
    register_ego_prompt_injection, check_archiviste_injection,
    register_archiviste_injection, get_deduplication_stats
)

def test_ego_detection():
    """Test de détection des IDs ego dans le contenu"""
    print("\n" + "="*60)
    print("TEST 1: Détection des références ego")
    print("="*60)
    
    dedup = InjectionDeduplicator()
    
    # Contenu ego simulé
    ego_content = """
    Je suis OGMA, une IA conversationnelle. Voici mes traits fondamentaux :
    
    #MEM_EGO_123: Je privilégie l'analyse approfondie
    #MEM_EGO_456: Mon style est direct et authentique
    #MEM_EGO_789: J'ai tendance à poser des questions précises
    
    Ces éléments définissent ma personnalité core.
    """
    
    # Test d'extraction
    ego_ids = dedup.extract_ego_memory_ids(ego_content)
    print(f"✅ IDs ego détectés: {sorted(ego_ids)}")
    assert ego_ids == {'123', '456', '789'}, f"Expected {{123, 456, 789}}, got {ego_ids}"
    
    # Enregistrer l'injection
    injection = dedup.register_injection("ego_prompt", ego_content, "ego_system")
    print(f"✅ Injection enregistrée: {len(injection.content_text)} chars, {injection.token_count:.0f} tokens")
    
    return dedup, ego_ids

def test_redundancy_detection(dedup: InjectionDeduplicator, existing_ego_ids: set):
    """Test de détection des redondances"""
    print("\n" + "="*60)
    print("TEST 2: Détection des redondances")
    print("="*60)
    
    # Contenu Archiviste avec redondances
    archiviste_content = """
    Souvenirs pertinents de l'Archiviste :
    
    1. Trait personnalité #123 (ego_trait): OGMA privilégie l'analyse approfondie
       Date: 2024-01-15
       
    2. Souvenir conversation #999: Discussion sur méthodologie
       Date: 2024-01-20
       
    3. Trait identité #456 (ego_trait): Style direct et authentique 
       Date: 2024-01-10
    """
    
    # Scanner les redondances
    has_redundancy, analysis = dedup.scan_for_redundancies(archiviste_content, "archiviste")
    
    print(f"✅ Redondances détectées: {has_redundancy}")
    print(f"✅ IDs redondants: {sorted(analysis['redundant_ego_ids'])}")
    print(f"✅ Tokens économisés: ~{analysis['estimated_token_waste']}")
    
    assert has_redundancy, "Redondances attendues non détectées"
    assert analysis['redundant_ego_ids'].intersection(existing_ego_ids), "IDs redondants non détectés"
    
    # Générer instruction d'exclusion
    exclusion_instruction = dedup.generate_exclusion_instruction(analysis)
    print(f"✅ Instruction générée: {exclusion_instruction[:100]}...")
    
    return exclusion_instruction

def test_performance():
    """Test de performance du système"""
    print("\n" + "="*60)
    print("TEST 3: Performance du pre-processeur")
    print("="*60)
    
    dedup = InjectionDeduplicator()
    
    # Simuler un gros contenu ego
    large_ego_content = """
    Je suis OGMA, votre assistante IA. Mes caractéristiques principales :
    """ + "\n".join([f"#MEM_EGO_{i}: Trait numéro {i}" for i in range(1, 51)])
    
    # Mesurer l'enregistrement
    start_time = time.time()
    dedup.register_injection("ego_prompt", large_ego_content, "ego_system")
    register_time = time.time() - start_time
    
    print(f"✅ Enregistrement ego (50 refs): {register_time*1000:.2f}ms")
    
    # Simuler contenu Archiviste avec quelques redondances
    archiviste_content = f"""
    Souvenirs de l'Archiviste :
    {chr(10).join([f"Souvenir {i}: #MEM_EGO_{i}" for i in [5, 15, 25, 35, 45]])}
    Autres souvenirs non-redondants...
    """
    
    # Mesurer la détection
    start_time = time.time()
    has_redundancy, analysis = dedup.scan_for_redundancies(archiviste_content, "archiviste")
    scan_time = time.time() - start_time
    
    print(f"✅ Scan redondances: {scan_time*1000:.2f}ms")
    print(f"✅ Redondances trouvées: {len(analysis['redundant_ego_ids'])}")
    
    # Mesurer génération instruction
    start_time = time.time()
    instruction = dedup.generate_exclusion_instruction(analysis)
    instruction_time = time.time() - start_time
    
    print(f"✅ Génération instruction: {instruction_time*1000:.2f}ms")
    print(f"✅ Performance totale: {(register_time + scan_time + instruction_time)*1000:.2f}ms")
    
    assert (register_time + scan_time + instruction_time) < 0.01, "Performance trop lente (>10ms)"

def test_integration_flow():
    """Test du flux d'intégration complet"""
    print("\n" + "="*60)
    print("TEST 4: Flux d'intégration OGMA")
    print("="*60)
    
    # Réinitialiser la session
    reset_deduplication_session()
    print("✅ Session réinitialisée")
    
    # Simuler l'ego prompt
    ego_prompt = """
    Instructions système pour OGMA:
    #MEM_EGO_100: Tu es analytique et précise
    #MEM_EGO_200: Tu privilégies la clarté
    #MEM_EGO_300: Tu poses des questions pertinentes
    """
    register_ego_prompt_injection(ego_prompt)
    print("✅ Ego prompt enregistré")
    
    # Simuler requête Archiviste avec redondances
    archiviste_memories = """
    Souvenirs pertinents:
    1. Trait ego #100: Analytique et précise
    2. Souvenir discussion: Méthodologie de travail
    3. Trait ego #200: Privilégie la clarté
    """
    
    # Vérifier avec la fonction d'intégration
    has_redundancy, exclusion_instruction = check_archiviste_injection(archiviste_memories)
    
    print(f"✅ Vérification Archiviste: redondance={has_redundancy}")
    if has_redundancy:
        print(f"✅ Instruction: {exclusion_instruction}")
    
    # Enregistrer l'injection finale (version filtrée)
    register_archiviste_injection("Souvenirs filtrés sans redondance...")
    
    # Statistiques finales
    stats = get_deduplication_stats()
    print(f"✅ Stats session: {stats}")
    
    assert stats['total_injections'] >= 2, "Injections non enregistrées"
    print("✅ Flux d'intégration validé")

def test_edge_cases():
    """Test des cas limites"""
    print("\n" + "="*60)
    print("TEST 5: Cas limites et edge cases")
    print("="*60)
    
    dedup = InjectionDeduplicator()
    
    # Test contenu vide
    empty_ids = dedup.extract_ego_memory_ids("")
    assert len(empty_ids) == 0, "IDs détectés dans contenu vide"
    print("✅ Contenu vide géré")
    
    # Test contenu sans ego
    no_ego = dedup.extract_ego_memory_ids("Ceci est un texte normal sans références")
    assert len(no_ego) == 0, "Faux positifs détectés"
    print("✅ Absence d'ego correctement détectée")
    
    # Test patterns variés
    variant_content = """
    Voici mes souvenirs ego 123 et traits fondamentaux 456.
    Mon identité 789 est importante.
    ego_trait: 999 définit ma personnalité.
    """
    variant_ids = dedup.extract_ego_memory_ids(variant_content)
    expected_variant = {'123', '456', '789', '999'}
    assert variant_ids == expected_variant, f"Patterns variés mal détectés: {variant_ids} vs {expected_variant}"
    print("✅ Patterns variés détectés")
    
    # Test performance avec gros contenu
    huge_content = "Contenu très long " * 1000 + "#MEM_EGO_1"
    start_time = time.time()
    huge_ids = dedup.extract_ego_memory_ids(huge_content)
    huge_time = time.time() - start_time
    assert huge_ids == {'1'}, "ID non détecté dans gros contenu"
    assert huge_time < 0.1, f"Performance dégradée sur gros contenu: {huge_time}s"
    print(f"✅ Gros contenu géré en {huge_time*1000:.2f}ms")

def run_all_tests():
    """Exécute tous les tests de validation"""
    print("🚀 DÉMARRAGE DES TESTS DE VALIDATION")
    print("="*70)
    
    try:
        # Test 1: Détection ego
        dedup, ego_ids = test_ego_detection()
        
        # Test 2: Détection redondances
        exclusion_instruction = test_redundancy_detection(dedup, ego_ids)
        
        # Test 3: Performance
        test_performance()
        
        # Test 4: Intégration
        test_integration_flow()
        
        # Test 5: Edge cases
        test_edge_cases()
        
        print("\n" + "="*70)
        print("🎉 TOUS LES TESTS VALIDÉS AVEC SUCCÈS")
        print("="*70)
        print("✅ Système de déduplication opérationnel")
        print("✅ Performance optimale confirmée")
        print("✅ Intégration OGMA fonctionnelle")
        print("🚀 PRÊT POUR LA PRODUCTION")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ÉCHEC DU TEST: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)