"""
test_memory_optimization_baseline.py
====================================

BASELINE METRICS - Comportement système mémoire ACTUEL
-------------------------------------------------------

Documente métriques PRÉ-refactoring pour comparaison:
- Volumes souvenirs (bruts, après dédup, synthèse)
- Temps exécution (analyse, recherche, synthèse)
- Qualité déduplication (ratio doublons détectés)
- Tokens consommés (estimation)

OBJECTIF: Référence validée AVANT Option C.

Auteur: GitHub Copilot
Date: 13 novembre 2025
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


# ============================================================================
# CONFIGURATION TEST
# ============================================================================

# Requêtes test (variété cas d'usage)
TEST_QUERIES = [
    {
        "query": "tu te souviens du nom de mon chat?",
        "description": "Requête simple identité animal",
        "expected_type": "personal"
    },
    {
        "query": "qu'est-ce qu'on a discuté sur la légende des deux phares?",
        "description": "Requête conversation passée",
        "expected_type": "conversation"
    },
    {
        "query": "quels souvenirs as-tu de mes projets créatifs?",
        "description": "Requête large multi-souvenirs",
        "expected_type": "personal"
    },
    {
        "query": "rappelle-moi ce qu'on a dit sur l'intelligence artificielle",
        "description": "Requête thématique générale",
        "expected_type": "conversation"
    },
    {
        "query": "mon anniversaire",
        "description": "Requête ultra-courte (2 mots)",
        "expected_type": "personal"
    }
]

# Paramètres système actuels (copie ogma_ng.py)
K_PERSONAL = 5
K_CONVERSATION = 7


# ============================================================================
# BASELINE RUNNER
# ============================================================================

class BaselineRunner:
    """Exécute tests baseline sur système actuel"""
    
    def __init__(self):
        self.results = []
        self.archiviste_controller = None
        self.memory_manager = None
        self.optimizer = None
        
    async def initialize_components(self):
        """Initialise composants OGMA nécessaires"""
        print("[BASELINE] 🔧 Initialisation composants OGMA...")
        
        # Import lazy pour éviter dépendances circulaires
        try:
            # Tente d'importer depuis ogma_ng (méthode idéale)
            import sys
            sys.path.insert(0, str(Path(__file__).parent))
            
            # Importe contrôleurs directement
            from core_logic import CoreLogicController
            from memory_manager import MemoryManager
            from archiviste_memory_optimizer import ArchivisteMemoryOptimizer
            
            # Chargement settings
            settings_path = Path("data/settings.json")
            if not settings_path.exists():
                print(f"[BASELINE] ❌ Fichier settings.json introuvable: {settings_path}")
                return False
                
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            
            # Archiviste Controller
            archiviste_api = settings.get('reasoning_api', {})
            self.archiviste_controller = CoreLogicController(
                api_key=archiviste_api.get('api_key', ''),
                provider=archiviste_api.get('provider', 'openai'),
                api_model=archiviste_api.get('api_model', 'gpt-4o-mini'),
                backend_type=archiviste_api.get('backend_type', 'API')
            )
            
            # Memory Manager
            db_path = Path("data/memory/memories_v2.db")
            faiss_path = Path("data/memory/faiss_index.bin")
            
            if not db_path.exists():
                print(f"[BASELINE] ❌ Base mémoire introuvable: {db_path}")
                return False
                
            self.memory_manager = MemoryManager(
                db_path=str(db_path),
                faiss_index_path=str(faiss_path),
                embedding_controller=None,  # Utilise provider interne
                embedding_provider=settings.get('embedding_api', {}).get('provider', 'openai'),
                embedding_api_key=settings.get('embedding_api', {}).get('api_key', '')
            )
            
            # Optimizer
            self.optimizer = ArchivisteMemoryOptimizer(
                archiviste_controller=self.archiviste_controller,
                memory_manager=self.memory_manager,
                embedding_controller=None,
                user_name="Yohan"
            )
            
            print("[BASELINE] ✅ Composants initialisés")
            return True
            
        except Exception as e:
            print(f"[BASELINE] ❌ Erreur initialisation: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def run_single_test(self, test_case: Dict[str, str]) -> Dict[str, Any]:
        """
        Exécute un test baseline sur une requête.
        
        Returns:
            Métriques: temps, volumes, dédup ratio, tokens
        """
        query = test_case['query']
        description = test_case['description']
        
        print(f"\n[BASELINE] 🧪 Test: {description}")
        print(f"[BASELINE] 📝 Requête: '{query}'")
        
        start_time = time.time()
        
        try:
            # Appel optimizer actuel
            result = await self.optimizer.get_optimized_context(
                message=query,
                k_personal=K_PERSONAL,
                k_conversation=K_CONVERSATION
            )
            
            elapsed = time.time() - start_time
            
            # Extraction métriques
            metrics = result.metrics
            analysis = result.analysis
            
            # Calcul volumes
            total_memories = len(result.memories_personal) + len(result.memories_conversation)
            
            # Estimation tokens (approximation: 1 token ≈ 0.75 mots)
            synthesis_tokens = len(result.synthesis.split()) * 0.75
            memories_tokens = sum(
                len(m.get('summary', m.get('text', '')).split()) * 0.75
                for m in (result.memories_personal + result.memories_conversation)
            )
            total_tokens_estimated = synthesis_tokens + memories_tokens
            
            # Calcul dédup ratio (si doublons détectés)
            # Note: Système actuel ne track pas doublons
            dedup_ratio = 0.0  # Baseline: pas de tracking
            
            test_result = {
                'query': query,
                'description': description,
                'timestamp': datetime.now().isoformat(),
                
                # Temps
                'elapsed_ms': elapsed * 1000,
                
                # Appels API
                'api_calls_total': metrics.get('total_api_calls', 0),
                'api_calls_analysis': metrics.get('analysis_calls', 0),
                'api_calls_embedding': metrics.get('embedding_calls', 0),
                'api_calls_synthesis': metrics.get('synthesis_calls', 0),
                
                # Volumes souvenirs
                'queries_generated': len(result.queries_used),
                'memories_personal': len(result.memories_personal),
                'memories_conversation': len(result.memories_conversation),
                'memories_total': total_memories,
                
                # Keywords analysés
                'keywords_core': len(analysis.keywords_core),
                'keywords_context': len(analysis.keywords_context),
                
                # Tokens
                'tokens_synthesis': synthesis_tokens,
                'tokens_memories': memories_tokens,
                'tokens_total': total_tokens_estimated,
                
                # Déduplication
                'dedup_ratio': dedup_ratio,
                
                # Qualité (subjectif)
                'synthesis_length': len(result.synthesis),
                'synthesis_preview': result.synthesis[:200] + "..." if len(result.synthesis) > 200 else result.synthesis
            }
            
            print(f"[BASELINE] ⏱️  Temps: {test_result['elapsed_ms']:.0f}ms")
            print(f"[BASELINE] 🔢 Appels API: {test_result['api_calls_total']}")
            print(f"[BASELINE] 📚 Souvenirs: {test_result['memories_total']} ({test_result['memories_personal']} perso, {test_result['memories_conversation']} conv)")
            print(f"[BASELINE] 🎯 Queries: {test_result['queries_generated']}")
            print(f"[BASELINE] 📊 Tokens estimés: {test_result['tokens_total']:.0f}")
            
            return test_result
            
        except Exception as e:
            print(f"[BASELINE] ❌ Erreur test: {e}")
            import traceback
            traceback.print_exc()
            
            return {
                'query': query,
                'description': description,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def run_all_tests(self):
        """Exécute suite complète tests baseline"""
        print("\n" + "="*80)
        print("BASELINE METRICS - Système Mémoire ACTUEL")
        print("="*80)
        
        # Initialisation
        if not await self.initialize_components():
            print("[BASELINE] ❌ Échec initialisation - Abandon tests")
            return
        
        # Exécution tests
        for test_case in TEST_QUERIES:
            result = await self.run_single_test(test_case)
            self.results.append(result)
            
            # Pause entre tests (éviter rate limits)
            await asyncio.sleep(2)
        
        # Agrégation résultats
        self.generate_summary_report()
        
        # Sauvegarde résultats
        self.save_results()
    
    def generate_summary_report(self):
        """Génère rapport synthétique baseline"""
        print("\n" + "="*80)
        print("RAPPORT SYNTHÉTIQUE BASELINE")
        print("="*80)
        
        # Filtrage résultats valides (sans erreur)
        valid_results = [r for r in self.results if 'error' not in r]
        
        if not valid_results:
            print("[BASELINE] ❌ Aucun test valide")
            return
        
        # Calculs moyennes
        avg_elapsed = sum(r['elapsed_ms'] for r in valid_results) / len(valid_results)
        avg_api_calls = sum(r['api_calls_total'] for r in valid_results) / len(valid_results)
        avg_memories = sum(r['memories_total'] for r in valid_results) / len(valid_results)
        avg_queries = sum(r['queries_generated'] for r in valid_results) / len(valid_results)
        avg_tokens = sum(r['tokens_total'] for r in valid_results) / len(valid_results)
        
        print(f"\n📊 MÉTRIQUES MOYENNES ({len(valid_results)} tests):")
        print(f"  ⏱️  Temps moyen: {avg_elapsed:.0f}ms")
        print(f"  🔢 Appels API moyen: {avg_api_calls:.1f}")
        print(f"  📚 Souvenirs moyen: {avg_memories:.1f}")
        print(f"  🎯 Queries moyennes: {avg_queries:.1f}")
        print(f"  📊 Tokens moyens: {avg_tokens:.0f}")
        
        # Détails par test
        print(f"\n📋 DÉTAILS PAR TEST:")
        for i, result in enumerate(valid_results, 1):
            print(f"\n  {i}. {result['description']}")
            print(f"     Requête: '{result['query']}'")
            print(f"     Temps: {result['elapsed_ms']:.0f}ms | API: {result['api_calls_total']} | Souvenirs: {result['memories_total']} | Tokens: {result['tokens_total']:.0f}")
        
        # Limites système actuel
        print(f"\n⚠️  LIMITES IDENTIFIÉES (Baseline):")
        print(f"  - Déduplication: ID-only (pas sémantique)")
        print(f"  - Queries: 3 max (core + context limité)")
        print(f"  - Injection tracking: passif (warnings sans blocage)")
        print(f"  - are_memories_similar(): INACTIVE dans workflow")
        
        print("\n" + "="*80)
    
    def save_results(self):
        """Sauvegarde résultats JSON pour comparaison future"""
        output_path = Path("data/baseline_metrics.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        report = {
            'test_date': datetime.now().isoformat(),
            'system_version': 'ACTUEL (pré-Option C)',
            'test_queries': TEST_QUERIES,
            'results': self.results,
            'configuration': {
                'k_personal': K_PERSONAL,
                'k_conversation': K_CONVERSATION
            }
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Résultats sauvegardés: {output_path}")


# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Point d'entrée tests baseline"""
    runner = BaselineRunner()
    await runner.run_all_tests()


if __name__ == "__main__":
    print("🧪 BASELINE TEST - Système Mémoire OGMA")
    print("Collecte métriques PRÉ-refactoring Option C\n")
    
    asyncio.run(main())
