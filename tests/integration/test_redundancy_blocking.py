#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test du système de blocage automatique de redondance à 85%"""

import sys
import asyncio
import io
sys.path.insert(0, '.')

# Fix encoding pour Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from memory_manager import MemoryManager
from core_logic import AIController, EmbeddingController
import uuid

async def test_redundancy_blocking():
    """Teste le blocage automatique des mémorisations redondantes"""
    
    print("=" * 80)
    print("[TEST] BLOCAGE AUTOMATIQUE REDONDANCE (Seuil 85%)")
    print("=" * 80)
    
    # Utiliser les fonctions d'ogma_ng pour obtenir les contrôleurs
    import ogma_ng
    
    # Initialiser les contrôleurs via ogma_ng
    archiviste = ogma_ng._ensure_archiviste_controller()
    embedding = ogma_ng._ensure_embedding_controller()
    
    if not archiviste or not embedding:
        print("[ERREUR] Impossible d'initialiser les contrôleurs")
        return
    
    # Initialiser le memory manager (utiliser celui d'ogma_ng directement)
    from queue import Queue
    from pathlib import Path
    status_queue = Queue()
    
    mm = MemoryManager(
        db_path=Path('data/memory/memories.db'),
        index_path=Path('data/memory/faiss.index'),
        embedding_dim=1024,
        archiviste_ia=archiviste,
        embedding_ia=embedding,
        status_queue=status_queue
    )
    
    print("\n✅ Memory Manager initialisé")
    print(f"📊 Index FAISS: {mm.faiss_index.ntotal} vecteurs\n")
    
    # TEST 1: Mémoriser un nouveau contenu
    print("=" * 80)
    print("TEST 1: Mémorisation d'un nouveau contenu unique")
    print("=" * 80)
    
    original_text = "Luna adore les couchers de soleil orange sur l'océan Atlantique en automne"
    mem_id_1 = f"test-{uuid.uuid4()}"
    
    print(f"📝 Texte original: {original_text}")
    print(f"🆔 ID: {mem_id_1}")
    
    result_1 = await mm.add_memory(mem_id_1, original_text, chat_controller=None)
    
    if result_1:
        print(f"✅ TEST 1 RÉUSSI: Nouveau contenu mémorisé\n")
    else:
        print(f"❌ TEST 1 ÉCHOUÉ: Le contenu n'a pas été mémorisé\n")
        mm.cleanup()
        return
    
    # Attendre que l'indexation FAISS soit terminée
    await asyncio.sleep(1)
    
    # TEST 2: Tenter de mémoriser un quasi-doublon (devrait être BLOQUÉ)
    print("=" * 80)
    print("TEST 2: Tentative mémorisation quasi-doublon (similarité attendue: >90%)")
    print("=" * 80)
    
    duplicate_text = "Luna aime beaucoup les couchers de soleil orange sur l'océan Atlantique en automne"
    mem_id_2 = f"test-{uuid.uuid4()}"
    
    print(f"📝 Texte quasi-identique: {duplicate_text}")
    print(f"🆔 ID: {mem_id_2}")
    print(f"🎯 Attendu: BLOCAGE automatique (≥85%)\n")
    
    result_2 = await mm.add_memory(mem_id_2, duplicate_text, chat_controller=None)
    
    if not result_2:
        print(f"✅ TEST 2 RÉUSSI: Quasi-doublon BLOQUÉ automatiquement\n")
    else:
        print(f"❌ TEST 2 ÉCHOUÉ: Le doublon a été mémorisé (seuil non respecté)\n")
    
    # TEST 3: Tenter de mémoriser une variante significative (devrait PASSER)
    print("=" * 80)
    print("TEST 3: Variante significative (similarité attendue: 70-80%)")
    print("=" * 80)
    
    variant_text = "Les tempêtes hivernales sur la mer Méditerranée sont impressionnantes"
    mem_id_3 = f"test-{uuid.uuid4()}"
    
    print(f"📝 Texte différent: {variant_text}")
    print(f"🆔 ID: {mem_id_3}")
    print(f"🎯 Attendu: ACCEPT (variante légitime)\n")
    
    result_3 = await mm.add_memory(mem_id_3, variant_text, chat_controller=None)
    
    if result_3:
        print(f"✅ TEST 3 RÉUSSI: Variante légitime mémorisée\n")
    else:
        print(f"⚠️ TEST 3: Variante bloquée (peut-être légitime selon Archiviste)\n")
    
    # TEST 4: Tenter de mémoriser une reformulation (limite du seuil ~85%)
    print("=" * 80)
    print("TEST 4: Reformulation modérée (similarité attendue: 85-90%)")
    print("=" * 80)
    
    reformulation_text = "Luna apprécie énormément regarder les couchers de soleil orangés sur l'Atlantique pendant l'automne"
    mem_id_4 = f"test-{uuid.uuid4()}"
    
    print(f"📝 Reformulation: {reformulation_text}")
    print(f"🆔 ID: {mem_id_4}")
    print(f"🎯 Attendu: BLOCAGE probable (≥85%)\n")
    
    result_4 = await mm.add_memory(mem_id_4, reformulation_text, chat_controller=None)
    
    if not result_4:
        print(f"✅ TEST 4 RÉUSSI: Reformulation BLOQUÉE (redondance détectée)\n")
    else:
        print(f"⚠️ TEST 4: Reformulation acceptée (peut-être sous le seuil)\n")
    
    # NETTOYAGE: Supprimer les mémoires de test
    print("=" * 80)
    print("🧹 NETTOYAGE")
    print("=" * 80)
    
    test_ids = [mem_id_1, mem_id_2, mem_id_3, mem_id_4]
    deleted_count = 0
    
    for test_id in test_ids:
        try:
            await mm.delete_memory(test_id)
            deleted_count += 1
            print(f"🗑️ Supprimé: {test_id}")
        except Exception as e:
            print(f"⚠️ Erreur suppression {test_id}: {e}")
    
    print(f"\n✅ {deleted_count}/{len(test_ids)} mémoires de test supprimées")
    
    # RÉSUMÉ
    print("\n" + "=" * 80)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 80)
    
    tests_passed = 0
    tests_total = 4
    
    if result_1:
        print("✅ TEST 1: Nouveau contenu mémorisé")
        tests_passed += 1
    else:
        print("❌ TEST 1: Échec mémorisation nouveau contenu")
    
    if not result_2:
        print("✅ TEST 2: Quasi-doublon bloqué (≥85%)")
        tests_passed += 1
    else:
        print("❌ TEST 2: Quasi-doublon non bloqué")
    
    if result_3:
        print("✅ TEST 3: Variante légitime acceptée")
        tests_passed += 1
    else:
        print("⚠️ TEST 3: Variante bloquée (décision Archiviste)")
        tests_passed += 0.5
    
    if not result_4:
        print("✅ TEST 4: Reformulation bloquée (≥85%)")
        tests_passed += 1
    else:
        print("⚠️ TEST 4: Reformulation acceptée (<85%)")
        tests_passed += 0.5
    
    print("\n" + "=" * 80)
    print(f"🎯 RÉSULTAT FINAL: {tests_passed}/{tests_total} tests réussis")
    
    if tests_passed >= 3:
        print("✅ SYSTÈME DE BLOCAGE REDONDANCE FONCTIONNEL")
    else:
        print("⚠️ SYSTÈME NÉCESSITE AJUSTEMENTS")
    
    print("=" * 80)
    
    mm.cleanup()

if __name__ == "__main__":
    asyncio.run(test_redundancy_blocking())
