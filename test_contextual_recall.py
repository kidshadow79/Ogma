#!/usr/bin/env python3
"""
🧪 TEST CONTEXTUAL RECALL - Validation extension mémoire conversationnelle
==========================================================================

Ce script teste l'extension Contextual Recall en isolation pour vérifier:
1. Détection patterns temporels dans requêtes utilisateur
2. Récupération résumés depuis summaries_cache
3. Construction contexte formaté
4. Injection contexte dans messages système

USAGE:
    python test_contextual_recall.py

TESTS:
- Patterns temporels: "il y a 2 jours", "la semaine dernière", etc.
- Chargement résumés existants
- Formatage contexte avec budget tokens
- Statistiques extension
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Ajouter répertoire racine au path
sys.path.insert(0, str(Path(__file__).parent))

def test_temporal_parser():
    """Test du parser d'expressions temporelles."""
    print("\n" + "="*70)
    print("TEST 1: TEMPORAL PARSER - Détection expressions temporelles")
    print("="*70)
    
    from extensions.contextual_recall.temporal_parser import TemporalParser
    
    parser = TemporalParser(debug=True)
    
    # Requêtes de test
    test_queries = [
        "tu te souviens de notre conversation il y a 2 jours ?",
        "qu'est-ce qu'on a dit la semaine dernière sur le projet ?",
        "hier on a parlé de quoi déjà ?",
        "rappelle-moi notre échange d'avant-hier",
        "quelle était ta réponse il y a 3 semaines ?",
        "salut Luna, comment ça va ?",  # Pas de pattern temporel
    ]
    
    results = []
    
    for query in test_queries:
        print(f"\n📝 Requête: '{query}'")
        matches = parser.parse(query)
        
        if matches:
            best = matches[0]
            print(f"   ✅ Pattern détecté: {best.pattern_type}")
            print(f"   📅 Plage: {best.date_start.date()} → {best.date_end.date()}")
            print(f"   🎯 Confiance: {best.confidence:.2f}")
            results.append(True)
        else:
            print(f"   ⚪ Aucun pattern détecté")
            results.append(False)
    
    success_rate = sum(results) / len(results)
    print(f"\n📊 Résultats: {sum(results)}/{len(results)} patterns détectés ({success_rate*100:.0f}%)")
    
    return success_rate >= 0.7  # Au moins 70% de détection


def test_summary_loader():
    """Test du chargeur de résumés."""
    print("\n" + "="*70)
    print("TEST 2: SUMMARY LOADER - Accès cache résumés")
    print("="*70)
    
    from extensions.contextual_recall.summary_loader import SummaryLoader
    
    loader = SummaryLoader(
        cache_dir="data/summaries_cache",
        debug=True
    )
    
    # Statistiques cache
    stats = loader.get_statistics()
    print(f"\n📊 Statistiques cache:")
    print(f"   - Total résumés: {stats['total_summaries']}")
    print(f"   - Résumés simples: {stats['simple_summaries']}")
    print(f"   - Résumés fusion: {stats['fusion_summaries']}")
    print(f"   - Taille totale: {stats['total_size_bytes'] / 1024:.1f} KB")
    
    if stats['oldest_date'] and stats['newest_date']:
        print(f"   - Plus ancien: {stats['oldest_date'].strftime('%d/%m/%Y %H:%M')}")
        print(f"   - Plus récent: {stats['newest_date'].strftime('%d/%m/%Y %H:%M')}")
    
    # Test récupération résumés récents
    recent = loader.get_recent_summaries(max_count=5)
    print(f"\n📚 {len(recent)} résumés les plus récents:")
    for i, summary in enumerate(recent[:3], 1):
        print(f"   {i}. {summary['name']} ({summary['size']} bytes)")
        print(f"      Modifié: {summary['modified'].strftime('%d/%m/%Y %H:%M')}")
    
    # Test filtrage par plage
    now = datetime.now()
    start = now - timedelta(days=7)
    filtered = loader.filter_by_date_range(start, now)
    print(f"\n🔍 Résumés derniers 7 jours: {len(filtered)}")
    
    # Test chargement contenu
    if recent:
        first_summary = recent[0]
        content = loader.load_summary_content(first_summary['name'])
        if content:
            preview = content[:200] + "..." if len(content) > 200 else content
            print(f"\n📖 Aperçu résumé '{first_summary['name']}':")
            print(f"   {preview}")
    
    return stats['total_summaries'] > 0


def test_context_builder():
    """Test du constructeur de contexte."""
    print("\n" + "="*70)
    print("TEST 3: CONTEXT BUILDER - Formatage contexte")
    print("="*70)
    
    from extensions.contextual_recall.context_builder import ContextBuilder
    from extensions.contextual_recall.summary_loader import SummaryLoader
    
    loader = SummaryLoader(cache_dir="data/summaries_cache", debug=False)
    builder = ContextBuilder(max_tokens=800, max_summaries=3, debug=True)
    
    # Récupérer quelques résumés
    recent = loader.get_recent_summaries(max_count=3)
    loaded = loader.load_multiple(recent)
    
    if not loaded:
        print("   ⚠️ Aucun résumé chargé - test non applicable")
        return False
    
    # Construire contexte
    now = datetime.now()
    start = now - timedelta(days=7)
    
    context = builder.build_context(
        loaded,
        start,
        now,
        user_query="Notre conversation récente"
    )
    
    if context:
        tokens = builder.estimate_tokens(context)
        print(f"\n✅ Contexte généré:")
        print(f"   - Longueur: {len(context)} caractères")
        print(f"   - Estimation tokens: {tokens}")
        print(f"   - Résumés inclus: {len(loaded)}")
        print(f"\n📄 Aperçu contexte:")
        print("-" * 70)
        preview = context[:500] + "\n[...]" if len(context) > 500 else context
        print(preview)
        print("-" * 70)
        
        return True
    else:
        print("   ❌ Échec génération contexte")
        return False


def test_recall_agent():
    """Test de l'agent orchestrateur complet."""
    print("\n" + "="*70)
    print("TEST 4: RECALL AGENT - Orchestration complète")
    print("="*70)
    
    from extensions.contextual_recall import initialize_recall
    
    # Initialiser extension
    agent = initialize_recall(
        summaries_cache_path="data/summaries_cache",
        conversations_path="data/conversations",
        debug=True
    )
    
    if not agent:
        print("   ❌ Échec initialisation agent")
        return False
    
    # Tests différents types de requêtes
    test_messages = [
        "tu te souviens de notre conversation il y a 2 jours ?",
        "qu'est-ce qu'on a dit hier ?",
        "la semaine dernière on parlait de quoi ?",
        "salut Luna !",  # Pas de pattern
    ]
    
    results = []
    
    for msg in test_messages:
        print(f"\n💬 Message: '{msg}'")
        context = agent.process_message(msg)
        
        if context:
            tokens = len(context) // 4  # Approximation
            print(f"   ✅ Contexte généré ({tokens} tokens)")
            print(f"   📄 Aperçu: {context[:150]}...")
            results.append(True)
        else:
            print(f"   ⚪ Pas de contexte généré")
            results.append(False)
    
    # Statistiques
    stats = agent.get_statistics()
    print(f"\n📊 Statistiques agent:")
    print(f"   - Requêtes traitées: {stats['queries_processed']}")
    print(f"   - Patterns détectés: {stats['temporal_detected']}")
    print(f"   - Contextes générés: {stats['contexts_generated']}")
    print(f"   - Taux succès: {stats['hit_rate']*100:.1f}%")
    
    return stats['contexts_generated'] > 0


def test_integration():
    """Test d'intégration avec messages système."""
    print("\n" + "="*70)
    print("TEST 5: INTÉGRATION - Injection messages système")
    print("="*70)
    
    from extensions.contextual_recall import initialize_recall
    
    agent = initialize_recall(debug=False)
    
    if not agent:
        print("   ⚠️ Extension non disponible")
        return False
    
    # Simuler workflow OGMA
    user_message = "tu te souviens de ce qu'on a dit hier ?"
    messages = [
        {'role': 'system', 'content': 'Tu es Luna, une IA conversationnelle.'}
    ]
    
    print(f"\n📨 Message utilisateur: '{user_message}'")
    print(f"📋 Messages système avant injection: {len(messages)}")
    
    # Traiter message
    context = agent.process_message(user_message)
    
    if context:
        # Injecter contexte
        messages[0]['content'] += f"\n\n{context}"
        
        print(f"✅ Contexte injecté dans message système")
        print(f"📏 Longueur finale: {len(messages[0]['content'])} chars")
        print(f"\n📄 Message système complet:")
        print("-" * 70)
        preview = messages[0]['content'][:600] + "\n[...]" if len(messages[0]['content']) > 600 else messages[0]['content']
        print(preview)
        print("-" * 70)
        
        return True
    else:
        print("   ⚪ Pas de contexte à injecter pour ce message")
        return False


def main():
    """Exécute tous les tests."""
    print("\n" + "="*70)
    print("🧪 TEST SUITE CONTEXTUAL RECALL EXTENSION")
    print("="*70)
    print(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    tests = [
        ("Temporal Parser", test_temporal_parser),
        ("Summary Loader", test_summary_loader),
        ("Context Builder", test_context_builder),
        ("Recall Agent", test_recall_agent),
        ("Integration", test_integration),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"\n❌ ERREUR TEST {test_name}: {e}")
            import traceback
            traceback.print_exc()
            results[test_name] = False
    
    # Rapport final
    print("\n" + "="*70)
    print("📊 RAPPORT FINAL")
    print("="*70)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    success_count = sum(results.values())
    total_count = len(results)
    success_rate = success_count / total_count if total_count > 0 else 0
    
    print(f"\n🎯 Résultat global: {success_count}/{total_count} tests réussis ({success_rate*100:.0f}%)")
    
    if success_rate == 1.0:
        print("\n🎉 TOUS LES TESTS SONT PASSÉS !")
        return 0
    elif success_rate >= 0.8:
        print("\n⚠️ Quelques tests ont échoué mais système fonctionnel")
        return 0
    else:
        print("\n❌ ÉCHEC - Système nécessite corrections")
        return 1


if __name__ == "__main__":
    sys.exit(main())
