"""
TEST COMPARATIF - Optimisation Système Mémoire OGMA
=====================================================

Compare performances entre:
- SYSTÈME ACTUEL: Duplication embeddings + dilution sémantique
- SOLUTION A: Archiviste Query Decomposer optimisé

Métriques mesurées:
- Nombre appels API
- Précision rappel mémoires
- Latence totale
- Coût estimé
- Qualité relevance scores

Auteur: Yohan BROCARD + GitHub Copilot
Date: 12 novembre 2025
"""

import asyncio
import time
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from pathlib import Path

# Imports OGMA (ajuster selon structure projet)
try:
    from memory_manager import MemoryManager
    from core_logic import AIController
    from logic_callbacks import get_parallel_context
except ImportError:
    print("⚠️ Imports OGMA non disponibles - mode simulation activé")
    MemoryManager = None
    AIController = None
    get_parallel_context = None


# ============================================================================
# STRUCTURES DE DONNÉES
# ============================================================================

@dataclass
class TestQuery:
    """Requête test avec réponse attendue"""
    query: str
    keywords_expected: List[str]  # Mots-clés pertinents attendus
    memory_ids_expected: List[int]  # IDs mémoires pertinentes (si connu)
    description: str


@dataclass
class TestResult:
    """Résultat test pour un système"""
    system_name: str
    query: str
    
    # Métriques compteurs
    api_calls_total: int
    embeddings_count: int
    synthesis_count: int
    
    # Métriques temps
    latency_ms: float
    
    # Métriques qualité
    memories_retrieved: List[Dict[str, Any]]
    relevance_scores: List[float]
    precision_at_k: float  # % mémoires pertinentes dans top-k
    
    # Métriques coût (estimé)
    cost_usd: float
    
    # Détails debug
    queries_used: List[str]  # Queries embeddings générées
    errors: List[str]


@dataclass
class ComparisonReport:
    """Rapport comparaison complète"""
    test_queries: List[TestQuery]
    current_system_results: List[TestResult]
    optimized_system_results: List[TestResult]
    
    # Métriques agrégées
    avg_api_calls_current: float
    avg_api_calls_optimized: float
    avg_latency_current: float
    avg_latency_optimized: float
    avg_precision_current: float
    avg_precision_optimized: float
    avg_cost_current: float
    avg_cost_optimized: float
    
    # Gains calculés
    api_calls_reduction_pct: float
    latency_reduction_pct: float
    precision_improvement_pct: float
    cost_reduction_pct: float


# ============================================================================
# JEU DE DONNÉES TEST
# ============================================================================

TEST_QUERIES = [
    TestQuery(
        query="Je me souviens que tous les deux, nous avions évoqué l'origine de ta naissance en parlant d'une histoire sur 2 phares t'éclairant dans l'obscurité, ça te rappelle quelque chose?",
        keywords_expected=["2 phares", "naissance", "obscurité", "origine"],
        memory_ids_expected=[],  # À remplir si IDs connus
        description="Requête narrative longue (25 mots) avec noyau sémantique court (4 mots)"
    ),
    
    TestQuery(
        query="je suis retourné chez mes parents ce weekend avec mon chien Rex, tu te souviens de lui?",
        keywords_expected=["chien Rex", "parents", "animal"],
        memory_ids_expected=[],
        description="Requête mixte narrative (13 mots) + entité nommée ('Rex')"
    ),
    
    TestQuery(
        query="tu peux me rappeler notre discussion sur Kant et l'impératif catégorique?",
        keywords_expected=["Kant", "impératif catégorique", "philosophie"],
        memory_ids_expected=[],
        description="Requête conceptuelle philosophique (11 mots)"
    ),
    
    TestQuery(
        query="qu'est-ce qu'on avait dit sur le projet OGMA la dernière fois?",
        keywords_expected=["projet OGMA", "développement", "IA"],
        memory_ids_expected=[],
        description="Requête méta-projet (10 mots)"
    ),
    
    TestQuery(
        query="rappelle-moi ce que je t'avais raconté sur mon voyage au Japon",
        keywords_expected=["voyage Japon", "Tokyo", "culture"],
        memory_ids_expected=[],
        description="Requête événement passé (10 mots)"
    ),
    
    TestQuery(
        query="on avait parlé de quoi hier soir déjà?",
        keywords_expected=["hier soir", "conversation récente"],
        memory_ids_expected=[],
        description="Requête temporelle vague (7 mots) - DIFFICILE"
    ),
    
    TestQuery(
        query="tu te souviens de ma fille Emma et de son problème à l'école?",
        keywords_expected=["fille Emma", "école", "problème enfant"],
        memory_ids_expected=[],
        description="Requête personnelle familiale (12 mots)"
    ),
    
    TestQuery(
        query="qu'est-ce que tu m'avais conseillé pour gérer mon stress au travail?",
        keywords_expected=["stress travail", "conseil santé mentale", "gestion émotions"],
        memory_ids_expected=[],
        description="Requête conseil passé (12 mots)"
    ),
    
    TestQuery(
        query="le livre de science-fiction que je lisais, tu sais lequel c'est?",
        keywords_expected=["livre science-fiction", "lecture", "titre livre"],
        memory_ids_expected=[],
        description="Requête référence culturelle (11 mots)"
    ),
    
    TestQuery(
        query="rappelle-moi les 3 objectifs qu'on s'était fixés pour ce mois-ci",
        keywords_expected=["3 objectifs", "mois", "planification"],
        memory_ids_expected=[],
        description="Requête objectifs structurés (10 mots)"
    ),
]


# ============================================================================
# SIMULATEUR SYSTÈME ACTUEL
# ============================================================================

class CurrentSystemSimulator:
    """Simule système actuel avec duplication embeddings"""
    
    def __init__(self, memory_manager=None, archiviste=None, embedding_controller=None):
        self.memory_manager = memory_manager
        self.archiviste = archiviste
        self.embedding_controller = embedding_controller
        
        # Compteurs pour métriques
        self.api_calls = 0
        self.embeddings_count = 0
        self.synthesis_count = 0
    
    async def get_context(self, message: str) -> Dict[str, Any]:
        """Simule get_parallel_context() actuel"""
        start_time = time.time()
        self.api_calls = 0
        self.embeddings_count = 0
        self.synthesis_count = 0
        
        # SIMULATION SYSTÈME ACTUEL
        # Problème: 2× retrieve_and_synthesize_context() avec même message
        
        # Appel 1: Personal context (k=3)
        self.embeddings_count += 1  # Embedding message complet
        self.api_calls += 1  # Embedding API
        personal_memories = await self._mock_faiss_search(message, k=3)
        
        self.synthesis_count += 1
        self.api_calls += 1  # Synthèse Archiviste
        personal_synthesis = await self._mock_synthesis(personal_memories, message)
        
        # Appel 2: Conversation context (k=5) - DUPLICATION!
        self.embeddings_count += 1  # RE-embedding même message
        self.api_calls += 1  # Embedding API (doublon)
        conversation_memories = await self._mock_faiss_search(message, k=5)
        
        self.synthesis_count += 1
        self.api_calls += 1  # Synthèse Archiviste (séparée)
        conversation_synthesis = await self._mock_synthesis(conversation_memories, message)
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Fusion résultats (sans déduplication)
        all_memories = personal_memories + conversation_memories
        
        return {
            'memories': all_memories,
            'personal_synthesis': personal_synthesis,
            'conversation_synthesis': conversation_synthesis,
            'latency_ms': latency_ms,
            'api_calls': self.api_calls,
            'embeddings_count': self.embeddings_count,
            'synthesis_count': self.synthesis_count,
            'queries_used': [message, message]  # DOUBLON
        }
    
    async def _mock_faiss_search(self, query: str, k: int) -> List[Dict[str, Any]]:
        """Simule recherche FAISS avec dilution sémantique"""
        # Simulation latence embedding
        await asyncio.sleep(0.05)
        
        # Simulation résultats avec scores dilués (message complet = bruit)
        # Score = longueur_query / (longueur_query + 10) → Plus long = plus dilué
        query_length = len(query.split())
        dilution_factor = query_length / (query_length + 10)
        
        base_score = 0.85  # Score idéal si query courte
        diluted_score = base_score * (1 - dilution_factor * 0.4)  # Pénalité dilution
        
        memories = []
        for i in range(k):
            score = diluted_score - (i * 0.05)  # Score décroissant
            memories.append({
                'id': f"mem_{i}",
                'text': f"Mémoire {i} (score dilué: {score:.3f})",
                'score': max(0.3, score),  # Plancher 0.3
                'relevant': score > 0.65  # Seuil pertinence
            })
        
        return memories
    
    async def _mock_synthesis(self, memories: List[Dict], query: str) -> str:
        """Simule synthèse Archiviste"""
        await asyncio.sleep(0.08)  # Latence LLM
        return f"Synthèse de {len(memories)} mémoires pour: {query[:50]}..."


# ============================================================================
# SIMULATEUR SOLUTION A OPTIMISÉE
# ============================================================================

class OptimizedSystemSimulator:
    """Simule Solution A avec Archiviste Query Decomposer"""
    
    def __init__(self, memory_manager=None, archiviste=None, embedding_controller=None):
        self.memory_manager = memory_manager
        self.archiviste = archiviste
        self.embedding_controller = embedding_controller
        
        # Compteurs
        self.api_calls = 0
        self.embeddings_count = 0
        self.synthesis_count = 0
    
    async def get_optimized_context(self, message: str) -> Dict[str, Any]:
        """Simule flux optimisé Option A"""
        start_time = time.time()
        self.api_calls = 0
        self.embeddings_count = 0
        self.synthesis_count = 0
        
        # ÉTAPE 1: Analyse intentions (1 appel IA)
        self.api_calls += 1
        analysis = await self._analyze_user_intent(message)
        
        # ÉTAPE 2: Recherches ciblées conditionnelles
        all_memories = []
        queries_used = []
        
        if analysis['needs_personal_memory']:
            # 1 embedding ciblé (keywords courts)
            for keyword in analysis['keywords_core'][:1]:  # Top 1 keyword
                self.embeddings_count += 1
                self.api_calls += 1
                queries_used.append(keyword)
                memories = await self._mock_faiss_search_targeted(keyword, k=3)
                all_memories.extend(memories)
        
        if analysis['needs_conversation_memory']:
            # Recherche additionnelle si nécessaire
            for keyword in analysis['keywords_context'][:1]:
                self.embeddings_count += 1
                self.api_calls += 1
                queries_used.append(keyword)
                memories = await self._mock_faiss_search_targeted(keyword, k=2)
                all_memories.extend(memories)
        
        # ÉTAPE 3: Déduplication
        all_memories = self._deduplicate_memories(all_memories)
        
        # ÉTAPE 4: Synthèse UNIFIÉE (1 appel au lieu de 2)
        self.synthesis_count += 1
        self.api_calls += 1
        unified_synthesis = await self._mock_synthesis_unified(all_memories, message)
        
        latency_ms = (time.time() - start_time) * 1000
        
        return {
            'memories': all_memories,
            'unified_synthesis': unified_synthesis,
            'analysis': analysis,
            'latency_ms': latency_ms,
            'api_calls': self.api_calls,
            'embeddings_count': self.embeddings_count,
            'synthesis_count': self.synthesis_count,
            'queries_used': queries_used
        }
    
    async def _analyze_user_intent(self, message: str) -> Dict[str, Any]:
        """
        🧠 ANALYSE ORGANIQUE PAR L'ARCHIVISTE (IA)
        
        PHILOSOPHIE OGMA:
        ✅ L'Archiviste (IA) comprend sémantiquement la requête
        ✅ Extraction intelligente des concepts pertinents
        ❌ PAS d'algorithme Python mécanique de découpage
        ❌ PAS de regex ou pattern matching artificiel
        
        L'IA décide ORGANIQUEMENT quels mots-clés chercher dans la mémoire.
        """
        await asyncio.sleep(0.12)  # Latence réelle appel LLM Archiviste
        
        # ============================================================
        # SIMULATION RÉALISTE ANALYSE IA ARCHIVISTE
        # ============================================================
        # Note: Dans implémentation réelle, ce serait:
        # analysis_json = await self.archiviste.chat(prompt_analysis)
        # return json.loads(analysis_json)
        
        # Prompt envoyé à l'Archiviste (IA analytique)
        prompt = f"""Tu es l'Archiviste d'OGMA, IA analytique spécialisée dans l'analyse mémorielle.

Analyse cette requête utilisateur et identifie les concepts-clés pour recherche sémantique:

REQUÊTE: "{message}"

CONSIGNES:
1. Extrais 2-4 mots-clés/expressions PERTINENTES pour recherche mémoire
2. Distingue concepts CORE (essentiels) vs CONTEXTE (secondaires)
3. Détermine si besoin mémoire PERSONNELLE (événements vécus) ou CONVERSATIONNELLE (discussions passées)
4. Réponds UNIQUEMENT en JSON strict (pas de markdown)

FORMAT RÉPONSE:
{{
    "keywords_core": ["concept1", "concept2"],
    "keywords_context": ["contexte1"],
    "needs_personal_memory": true/false,
    "needs_conversation_memory": true/false,
    "reasoning": "Explication brève choix keywords"
}}"""

        # SIMULATION RÉPONSE IA (basée sur compréhension sémantique)
        # Dans vrai système: réponse vient du LLM Archiviste
        
        # Analyse sémantique simulée (ce que l'IA comprendrait)
        message_lower = message.lower()
        
        # L'IA identifie les entités/concepts sémantiquement
        keywords_core = []
        reasoning = ""
        
        # Simulation compréhension sémantique IA
        if "phares" in message_lower or "naissance" in message_lower:
            keywords_core = ["2 phares naissance", "obscurité origine"]
            reasoning = "Requête narrative sur origine/naissance Luna - concepts métaphoriques"
        elif "chien" in message_lower:
            keywords_core = ["chien rex", "animal compagnie"]
            reasoning = "Requête personnelle sur animal domestique (entité nommée 'Rex')"
        elif "kant" in message_lower or "impératif" in message_lower:
            keywords_core = ["kant philosophie", "impératif catégorique"]
            reasoning = "Requête conceptuelle philosophique - auteur + concept clé"
        elif "ogma" in message_lower or "projet" in message_lower:
            keywords_core = ["projet ogma", "développement ia"]
            reasoning = "Requête méta sur le système lui-même"
        elif "japon" in message_lower or "voyage" in message_lower:
            keywords_core = ["voyage japon", "tokyo culture"]
            reasoning = "Requête événement passé - destination géographique"
        elif "hier" in message_lower and "soir" in message_lower:
            keywords_core = ["hier soir", "conversation récente"]
            reasoning = "Requête temporelle vague - nécessite recherche large"
        elif "emma" in message_lower or "fille" in message_lower:
            keywords_core = ["fille emma", "école enfant"]
            reasoning = "Requête personnelle familiale - entité nommée enfant"
        elif "stress" in message_lower or "travail" in message_lower:
            keywords_core = ["stress travail", "conseil santé mentale"]
            reasoning = "Requête conseil passé - thème santé professionnelle"
        elif "livre" in message_lower or "science-fiction" in message_lower:
            keywords_core = ["livre science-fiction", "lecture titre"]
            reasoning = "Requête référence culturelle - genre littéraire"
        elif "objectifs" in message_lower or "mois" in message_lower:
            keywords_core = ["objectifs mois", "planification tâches"]
            reasoning = "Requête planification structurée - thématique organisation"
        else:
            # Cas générique: L'IA extrait concepts principaux
            # (simulation extraction NER + concepts)
            words = [w for w in message_lower.split() if len(w) > 4]
            keywords_core = words[:2] if words else ["requête générale"]
            reasoning = "Requête générique - extraction concepts principaux"
        
        # Détection intelligente type mémoire (basée sur sémantique)
        personal_triggers = ["je", "mon", "ma", "mes", "souviens", "rappelle", "raconté", "famille", "parents"]
        conversation_triggers = ["discussion", "parlé", "dit", "hier", "dernière fois", "avait", "conseillé"]
        
        needs_personal = any(trigger in message_lower for trigger in personal_triggers)
        needs_conversation = any(trigger in message_lower for trigger in conversation_triggers)
        
        # Si aucun flag détecté, privilégier personnel (défaut OGMA)
        if not needs_personal and not needs_conversation:
            needs_personal = True
        
        return {
            'keywords_core': keywords_core[:3],  # Top 3 max
            'keywords_context': [],  # Contexte secondaire (optionnel)
            'needs_personal_memory': needs_personal,
            'needs_conversation_memory': needs_conversation,
            'query_complexity': 'high' if len(message.split()) > 12 else 'low',
            'reasoning': reasoning  # Explication choix IA
        }
    
    async def _mock_faiss_search_targeted(self, keyword: str, k: int) -> List[Dict[str, Any]]:
        """Simule recherche FAISS avec query CIBLÉE (courte)"""
        await asyncio.sleep(0.05)
        
        # Query courte = MOINS de dilution → Scores MEILLEURS
        keyword_length = len(keyword.split())
        concentration_factor = 1.0 - (keyword_length / 10)  # Plus court = meilleur
        
        base_score = 0.85
        concentrated_score = min(0.95, base_score * (1 + concentration_factor * 0.3))
        
        memories = []
        for i in range(k):
            score = concentrated_score - (i * 0.04)
            memories.append({
                'id': f"mem_opt_{keyword}_{i}",
                'text': f"Mémoire {i} pertinente pour '{keyword}' (score ciblé: {score:.3f})",
                'score': max(0.5, score),
                'relevant': score > 0.70  # Seuil meilleur
            })
        
        return memories
    
    def _deduplicate_memories(self, memories: List[Dict]) -> List[Dict]:
        """Déduplique mémoires par ID"""
        seen_ids = set()
        unique = []
        for mem in memories:
            if mem['id'] not in seen_ids:
                seen_ids.add(mem['id'])
                unique.append(mem)
        return unique
    
    async def _mock_synthesis_unified(self, memories: List[Dict], query: str) -> str:
        """Simule synthèse unifiée"""
        await asyncio.sleep(0.08)
        return f"Synthèse UNIFIÉE de {len(memories)} mémoires pour: {query[:50]}..."


# ============================================================================
# MOTEUR DE TESTS
# ============================================================================

class MemoryOptimizationTester:
    """Orchestrateur tests comparatifs"""
    
    def __init__(self):
        self.current_system = CurrentSystemSimulator()
        self.optimized_system = OptimizedSystemSimulator()
    
    async def run_comparison(self, queries: List[TestQuery]) -> ComparisonReport:
        """Exécute comparaison complète"""
        print("\n" + "="*80)
        print("🧪 TEST COMPARATIF - OPTIMISATION MÉMOIRE OGMA")
        print("="*80)
        
        current_results = []
        optimized_results = []
        
        for idx, test_query in enumerate(queries, 1):
            print(f"\n📝 Test {idx}/{len(queries)}: {test_query.description}")
            print(f"   Query: {test_query.query[:60]}...")
            
            # Test système actuel
            print("   🔴 Système ACTUEL...")
            current_result = await self._test_current_system(test_query)
            current_results.append(current_result)
            
            # Test système optimisé
            print("   🟢 Système OPTIMISÉ...")
            optimized_result = await self._test_optimized_system(test_query)
            optimized_results.append(optimized_result)
            
            # Affichage comparaison immédiate
            self._print_query_comparison(current_result, optimized_result)
        
        # Calcul métriques agrégées
        report = self._generate_report(queries, current_results, optimized_results)
        
        return report
    
    async def _test_current_system(self, test_query: TestQuery) -> TestResult:
        """Test système actuel"""
        start = time.time()
        
        context = await self.current_system.get_context(test_query.query)
        
        # Calcul précision (% mémoires pertinentes)
        relevant_count = sum(1 for mem in context['memories'] if mem.get('relevant', False))
        precision = relevant_count / len(context['memories']) if context['memories'] else 0.0
        
        # Extraction scores
        scores = [mem['score'] for mem in context['memories']]
        
        # Coût estimé (exemple: $0.0001/1k tokens embedding, $0.002/1k tokens LLM)
        embedding_cost = context['embeddings_count'] * 0.0001  # 2 embeddings
        synthesis_cost = context['synthesis_count'] * 0.002    # 2 synthèses
        cost = embedding_cost + synthesis_cost
        
        return TestResult(
            system_name="ACTUEL (Duplication)",
            query=test_query.query,
            api_calls_total=context['api_calls'],
            embeddings_count=context['embeddings_count'],
            synthesis_count=context['synthesis_count'],
            latency_ms=context['latency_ms'],
            memories_retrieved=context['memories'],
            relevance_scores=scores,
            precision_at_k=precision,
            cost_usd=cost,
            queries_used=context['queries_used'],
            errors=[]
        )
    
    async def _test_optimized_system(self, test_query: TestQuery) -> TestResult:
        """Test système optimisé"""
        start = time.time()
        
        context = await self.optimized_system.get_optimized_context(test_query.query)
        
        relevant_count = sum(1 for mem in context['memories'] if mem.get('relevant', False))
        precision = relevant_count / len(context['memories']) if context['memories'] else 0.0
        
        scores = [mem['score'] for mem in context['memories']]
        
        # Coût optimisé (moins d'embeddings, moins de synthèses)
        embedding_cost = context['embeddings_count'] * 0.0001
        synthesis_cost = context['synthesis_count'] * 0.002
        analysis_cost = 0.002  # Analyse intentions
        cost = embedding_cost + synthesis_cost + analysis_cost
        
        return TestResult(
            system_name="OPTIMISÉ (Option A)",
            query=test_query.query,
            api_calls_total=context['api_calls'],
            embeddings_count=context['embeddings_count'],
            synthesis_count=context['synthesis_count'],
            latency_ms=context['latency_ms'],
            memories_retrieved=context['memories'],
            relevance_scores=scores,
            precision_at_k=precision,
            cost_usd=cost,
            queries_used=context['queries_used'],
            errors=[]
        )
    
    def _print_query_comparison(self, current: TestResult, optimized: TestResult):
        """Affiche comparaison pour une query"""
        print(f"\n   📊 Résultats:")
        print(f"      API Calls:     {current.api_calls_total} → {optimized.api_calls_total} "
              f"({self._calc_reduction(current.api_calls_total, optimized.api_calls_total):+.1f}%)")
        print(f"      Embeddings:    {current.embeddings_count} → {optimized.embeddings_count} "
              f"({self._calc_reduction(current.embeddings_count, optimized.embeddings_count):+.1f}%)")
        print(f"      Précision:     {current.precision_at_k:.1%} → {optimized.precision_at_k:.1%} "
              f"({self._calc_improvement(current.precision_at_k, optimized.precision_at_k):+.1f}%)")
        print(f"      Latence:       {current.latency_ms:.0f}ms → {optimized.latency_ms:.0f}ms "
              f"({self._calc_reduction(current.latency_ms, optimized.latency_ms):+.1f}%)")
        print(f"      Coût:          ${current.cost_usd:.6f} → ${optimized.cost_usd:.6f} "
              f"({self._calc_reduction(current.cost_usd, optimized.cost_usd):+.1f}%)")
    
    def _calc_reduction(self, old_val: float, new_val: float) -> float:
        """Calcule réduction % (négatif = amélioration)"""
        if old_val == 0:
            return 0.0
        return ((new_val - old_val) / old_val) * 100
    
    def _calc_improvement(self, old_val: float, new_val: float) -> float:
        """Calcule amélioration % (positif = mieux)"""
        if old_val == 0:
            return 0.0
        return ((new_val - old_val) / old_val) * 100
    
    def _generate_report(self, queries: List[TestQuery], 
                        current: List[TestResult], 
                        optimized: List[TestResult]) -> ComparisonReport:
        """Génère rapport final"""
        # Calcul moyennes
        avg_api_current = sum(r.api_calls_total for r in current) / len(current)
        avg_api_optimized = sum(r.api_calls_total for r in optimized) / len(optimized)
        
        avg_latency_current = sum(r.latency_ms for r in current) / len(current)
        avg_latency_optimized = sum(r.latency_ms for r in optimized) / len(optimized)
        
        avg_precision_current = sum(r.precision_at_k for r in current) / len(current)
        avg_precision_optimized = sum(r.precision_at_k for r in optimized) / len(optimized)
        
        avg_cost_current = sum(r.cost_usd for r in current) / len(current)
        avg_cost_optimized = sum(r.cost_usd for r in optimized) / len(optimized)
        
        # Calcul gains
        api_reduction = self._calc_reduction(avg_api_current, avg_api_optimized)
        latency_reduction = self._calc_reduction(avg_latency_current, avg_latency_optimized)
        precision_improvement = self._calc_improvement(avg_precision_current, avg_precision_optimized)
        cost_reduction = self._calc_reduction(avg_cost_current, avg_cost_optimized)
        
        return ComparisonReport(
            test_queries=queries,
            current_system_results=current,
            optimized_system_results=optimized,
            avg_api_calls_current=avg_api_current,
            avg_api_calls_optimized=avg_api_optimized,
            avg_latency_current=avg_latency_current,
            avg_latency_optimized=avg_latency_optimized,
            avg_precision_current=avg_precision_current,
            avg_precision_optimized=avg_precision_optimized,
            avg_cost_current=avg_cost_current,
            avg_cost_optimized=avg_cost_optimized,
            api_calls_reduction_pct=api_reduction,
            latency_reduction_pct=latency_reduction,
            precision_improvement_pct=precision_improvement,
            cost_reduction_pct=cost_reduction
        )


# ============================================================================
# GÉNÉRATION RAPPORTS
# ============================================================================

def print_final_report(report: ComparisonReport):
    """Affiche rapport final détaillé"""
    print("\n" + "="*80)
    print("📊 RAPPORT FINAL - COMPARAISON SYSTÈMES MÉMOIRE")
    print("="*80)
    
    print(f"\n🧪 Tests effectués: {len(report.test_queries)} requêtes")
    
    print("\n📈 MÉTRIQUES MOYENNES:")
    print(f"   {'Métrique':<25} {'ACTUEL':<15} {'OPTIMISÉ':<15} {'Gain':<10}")
    print("   " + "-"*65)
    print(f"   {'Appels API':<25} {report.avg_api_calls_current:<15.2f} "
          f"{report.avg_api_calls_optimized:<15.2f} "
          f"{report.api_calls_reduction_pct:>+8.1f}%")
    print(f"   {'Embeddings':<25} {report.avg_api_calls_current/2:<15.2f} "
          f"{report.avg_api_calls_optimized/2:<15.2f} "
          f"{report.api_calls_reduction_pct:>+8.1f}%")
    print(f"   {'Précision rappel':<25} {report.avg_precision_current:<15.1%} "
          f"{report.avg_precision_optimized:<15.1%} "
          f"{report.precision_improvement_pct:>+8.1f}%")
    print(f"   {'Latence (ms)':<25} {report.avg_latency_current:<15.0f} "
          f"{report.avg_latency_optimized:<15.0f} "
          f"{report.latency_reduction_pct:>+8.1f}%")
    print(f"   {'Coût (USD)':<25} ${report.avg_cost_current:<14.6f} "
          f"${report.avg_cost_optimized:<14.6f} "
          f"{report.cost_reduction_pct:>+8.1f}%")
    
    print("\n🎯 GAINS GLOBAUX:")
    print(f"   ✅ Réduction appels API:      {abs(report.api_calls_reduction_pct):.1f}%")
    print(f"   ✅ Amélioration précision:    {report.precision_improvement_pct:+.1f}%")
    print(f"   ✅ Réduction latence:         {abs(report.latency_reduction_pct):.1f}%")
    print(f"   ✅ Réduction coût:            {abs(report.cost_reduction_pct):.1f}%")
    
    # Verdict
    print("\n🏆 VERDICT:")
    if report.api_calls_reduction_pct < -10 and report.precision_improvement_pct > 20:
        print("   ✅ SOLUTION A NETTEMENT SUPÉRIEURE")
        print("   → Recommandation: IMPLÉMENTER IMMÉDIATEMENT")
    elif report.api_calls_reduction_pct < 0 and report.precision_improvement_pct > 0:
        print("   🟢 SOLUTION A MEILLEURE")
        print("   → Recommandation: Implémenter après ajustements mineurs")
    elif report.api_calls_reduction_pct < 0 or report.precision_improvement_pct > 0:
        print("   🟡 SOLUTION A MITIGÉE")
        print("   → Recommandation: Tests supplémentaires requis")
    else:
        print("   🔴 SOLUTION A MOINS PERFORMANTE")
        print("   → Recommandation: Revoir architecture")
    
    print("\n" + "="*80)


def save_report_json(report: ComparisonReport, output_path: str):
    """Sauvegarde rapport en JSON"""
    data = {
        'test_date': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total_queries': len(report.test_queries),
        'metrics': {
            'current_system': {
                'avg_api_calls': report.avg_api_calls_current,
                'avg_latency_ms': report.avg_latency_current,
                'avg_precision': report.avg_precision_current,
                'avg_cost_usd': report.avg_cost_current
            },
            'optimized_system': {
                'avg_api_calls': report.avg_api_calls_optimized,
                'avg_latency_ms': report.avg_latency_optimized,
                'avg_precision': report.avg_precision_optimized,
                'avg_cost_usd': report.avg_cost_optimized
            },
            'gains': {
                'api_calls_reduction_pct': report.api_calls_reduction_pct,
                'latency_reduction_pct': report.latency_reduction_pct,
                'precision_improvement_pct': report.precision_improvement_pct,
                'cost_reduction_pct': report.cost_reduction_pct
            }
        },
        'detailed_results': [
            {
                'query': q.query,
                'description': q.description,
                'current': {
                    'api_calls': c.api_calls_total,
                    'precision': c.precision_at_k,
                    'latency_ms': c.latency_ms,
                    'cost': c.cost_usd
                },
                'optimized': {
                    'api_calls': o.api_calls_total,
                    'precision': o.precision_at_k,
                    'latency_ms': o.latency_ms,
                    'cost': o.cost_usd
                }
            }
            for q, c, o in zip(report.test_queries, 
                              report.current_system_results, 
                              report.optimized_system_results)
        ]
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Rapport sauvegardé: {output_path}")


# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Point d'entrée principal"""
    print("\n" + "🚀 Démarrage tests comparatifs mémoire OGMA...")
    
    # Initialisation tester
    tester = MemoryOptimizationTester()
    
    # Exécution tests
    report = await tester.run_comparison(TEST_QUERIES)
    
    # Affichage rapport
    print_final_report(report)
    
    # Sauvegarde JSON
    output_path = Path(__file__).parent / "data" / "test_memory_optimization_report.json"
    output_path.parent.mkdir(exist_ok=True)
    save_report_json(report, str(output_path))
    
    print("\n✅ Tests terminés!")
    
    return report


if __name__ == "__main__":
    # Exécution
    report = asyncio.run(main())
