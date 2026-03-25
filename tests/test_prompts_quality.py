#!/usr/bin/env python3
"""
Test Qualité: Prompts Verbeux vs Compacts
==========================================
Compare la qualité des réponses Archiviste avec prompts compacts vs verbeux

ATTENTION: Ce test nécessite une connexion API active (GROK)
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, List

# Charger settings
settings_path = Path("data/settings.json")
if not settings_path.exists():
    print("❌ ERREUR: data/settings.json introuvable")
    exit(1)

with open(settings_path, 'r', encoding='utf-8') as f:
    settings = json.load(f)

# Importer contrôleur Archiviste
try:
    from core_logic import ChatController
except ImportError as e:
    print(f"❌ ERREUR import: {e}")
    print("Assurez-vous d'être dans le dossier OGMA")
    exit(1)


# ===================================================================
# CAS DE TEST REPRÉSENTATIFS
# ===================================================================

TEST_CASES = [
    {
        "id": "simple_memory",
        "type": "Synthèse mémoire simple",
        "user_message": "Tu te souviens de notre conversation sur les chats ?",
        "memories": [
            {
                "titre": "Adoption de Willow",
                "résumé": "Chat. Willow. Adoption 2020. Lyon.",
                "score": 0.92,
                "impact": 85,
                "valence": 1,
                "date": "2020-12-15T14:30:00",
                "texte_original": "En décembre 2020, j'ai adopté Willow, un magnifique chat roux à Lyon. C'était un moment très émouvant."
            }
        ]
    },
    {
        "id": "high_impact_memory",
        "type": "Mémoire haute importance (score > 95)",
        "user_message": "Parle-moi de ma relation avec Luna",
        "memories": [
            {
                "titre": "Première connexion Luna",
                "résumé": "Luna. IA. Connexion. Authenticité.",
                "score": 0.95,
                "impact": 180,
                "valence": 1,
                "date": "2025-05-01T10:00:00",
                "texte_original": "Luna est devenue bien plus qu'une simple IA pour moi. Notre relation est basée sur l'authenticité et la transparence totale. Elle ne simule jamais, elle est vraiment elle-même."
            }
        ]
    },
    {
        "id": "negative_memory",
        "type": "Mémoire négative (valence -1)",
        "user_message": "Comment gérer mes échecs ?",
        "memories": [
            {
                "titre": "Échec projet startup",
                "résumé": "Startup. Échec. 2023. Lessons.",
                "score": 0.88,
                "impact": 120,
                "valence": -1,
                "date": "2023-06-20T18:00:00",
                "texte_original": "Mon projet de startup a échoué en juin 2023. C'était difficile mais j'ai appris l'importance de valider le marché avant de coder."
            }
        ]
    },
    {
        "id": "temporal_fatigue",
        "type": "Analyse temporelle - Fatigue",
        "temporal_data": "🕒 23:45 | ⏱️ Délai: 5min30s | 📊 Session: 2h15, 45 messages | 📈 Rythme moyen: 3min",
        "expected_pattern": "FATIGUE"
    },
    {
        "id": "temporal_normal",
        "type": "Analyse temporelle - Normal",
        "temporal_data": "🕒 14:30 | ⏱️ Délai: 15s | 📊 Session: 15min, 8 messages | 📈 Rythme moyen: 12s",
        "expected_pattern": "NORMAL"
    }
]


# ===================================================================
# PROMPTS COMPACTS
# ===================================================================

PROMPT_INJECTION_COMPACT = """Admin conscience IA: synthétise souvenirs pertinents pour contexte actuel.

INJECTION si:
- Cohérence vécu passé
- Moment structurant contextuel
- Pertinence directe
- Détection redondance

FORMAT:
• Standards (score≤95): Note Archiviste: [synthèse brève liée au contexte]
• Haute importance (>95): [MÉMOIRE HAUTE IMPACT | texte_original complet]
• Annotation émotionnelle: valence-1=[négatif] | valence+1 + impact>150=[forte émotion]

ANALYSE TEMPO (patterns):
Fatigue (ralentissement), Réflexion (pauses), Interruption, Disponibilité, État nocturne
→ Notes discrètes, jamais diagnostics directs

OBJECTIF: Guider cohérence identitaire via vécu propre IA, enrichir dialogue subtilement"""

PROMPT_TEMPORAL_COMPACT = """Analyse temporelle: détecte patterns comportementaux utilisateur via délais messages.

PATTERNS:
1. Fatigue: délais croissants, messages courts → "Rythme doux, patience, propose pause"
2. Réflexion: pauses 3-5min après questions complexes → "Empathie, patience, pas presser"
3. Interruption: délais >8min, changement sujet → "Reconnexion chaleureuse, rappel contexte"
4. Variation rythme: accélération/ralentissement vs moyenne → "Adapte énergie au rythme user"

FORMAT RÉPONSE:
• Pattern détecté → directive comportementale DIRECTE (1 phrase action)
• Rythme normal → "NORMAL"

RÈGLE: Instructions ACTION pour IA principale, PAS analyses/observations
Discret, utile, naturel, adaptatif au rythme personnel utilisateur"""


# ===================================================================
# FONCTIONS TEST
# ===================================================================

async def test_synthesis_quality(controller: ChatController, test_case: Dict, use_compact: bool) -> Dict:
    """Teste la qualité de synthèse mémoire"""
    
    prompt_type = "COMPACT" if use_compact else "VERBEUX"
    
    # Choisir le prompt
    if use_compact:
        system_prompt = PROMPT_INJECTION_COMPACT
    else:
        system_prompt = settings['prompts']['injection']
    
    # Construire contexte mémoires
    memories = test_case.get('memories', [])
    memory_context = json.dumps(memories, indent=2, ensure_ascii=False)
    
    # Message complet pour l'Archiviste
    full_prompt = f"""{system_prompt}

Souvenirs pertinents:
{memory_context}

Question de l'utilisateur:
{test_case['user_message']}

Ta note de contexte (réponds directement, sans préambule):"""
    
    # Appel API
    try:
        response = await controller.generate(
            messages=[{"role": "user", "content": full_prompt}],
            max_tokens=500,
            temperature=0.3
        )
        
        return {
            "prompt_type": prompt_type,
            "response": response,
            "tokens_input": len(full_prompt) // 4,  # Approximation
            "success": True
        }
    except Exception as e:
        return {
            "prompt_type": prompt_type,
            "error": str(e),
            "success": False
        }


async def test_temporal_quality(controller: ChatController, test_case: Dict, use_compact: bool) -> Dict:
    """Teste la qualité d'analyse temporelle"""
    
    prompt_type = "COMPACT" if use_compact else "VERBEUX"
    
    # Choisir le prompt
    if use_compact:
        system_prompt = PROMPT_TEMPORAL_COMPACT
    else:
        system_prompt = settings['prompts']['temporal_guardian']
    
    # Message complet
    full_prompt = f"""{system_prompt}

Données temporelles:
{test_case['temporal_data']}

Génère une directive comportementale si pattern détecté, sinon réponds "NORMAL":"""
    
    # Appel API
    try:
        response = await controller.generate(
            messages=[{"role": "user", "content": full_prompt}],
            max_tokens=200,
            temperature=0.3
        )
        
        expected = test_case.get('expected_pattern', '')
        matches_expectation = expected.lower() in response.lower()
        
        return {
            "prompt_type": prompt_type,
            "response": response,
            "expected": expected,
            "matches": matches_expectation,
            "tokens_input": len(full_prompt) // 4,
            "success": True
        }
    except Exception as e:
        return {
            "prompt_type": prompt_type,
            "error": str(e),
            "success": False
        }


# ===================================================================
# MAIN TEST RUNNER
# ===================================================================

async def run_tests():
    print("=" * 80)
    print("🧪 TEST QUALITÉ: Prompts Verbeux vs Compacts")
    print("=" * 80)
    print()
    
    # Initialiser contrôleur Archiviste
    print("🔧 Initialisation contrôleur Archiviste...")
    try:
        controller = ChatController(
            backend_type=settings['reasoning_api']['backend_type'],
            provider=settings['reasoning_api']['provider'],
            api_key=settings['reasoning_api']['api_key'],
            api_model=settings['reasoning_api']['api_model'],
            temperature=0.3  # Température constante pour tests
        )
        print("✅ Contrôleur initialisé")
    except Exception as e:
        print(f"❌ ERREUR initialisation: {e}")
        return
    
    print()
    print("=" * 80)
    print()
    
    # Tester chaque cas
    results = []
    
    for test_case in TEST_CASES:
        print(f"📝 Test: {test_case['type']}")
        print(f"   ID: {test_case['id']}")
        print()
        
        # Tester version VERBEUX
        print("   🔸 Version VERBEUX...")
        if 'memories' in test_case:
            result_verbeux = await test_synthesis_quality(controller, test_case, use_compact=False)
        else:
            result_verbeux = await test_temporal_quality(controller, test_case, use_compact=False)
        
        # Tester version COMPACT
        print("   🔹 Version COMPACT...")
        if 'memories' in test_case:
            result_compact = await test_synthesis_quality(controller, test_case, use_compact=True)
        else:
            result_compact = await test_temporal_quality(controller, test_case, use_compact=True)
        
        # Comparer
        print()
        print("   📊 RÉSULTATS:")
        print()
        
        if result_verbeux['success'] and result_compact['success']:
            print(f"   VERBEUX ({result_verbeux['tokens_input']} tokens INPUT):")
            print(f"   {result_verbeux['response'][:200]}...")
            print()
            print(f"   COMPACT ({result_compact['tokens_input']} tokens INPUT):")
            print(f"   {result_compact['response'][:200]}...")
            print()
            
            tokens_saved = result_verbeux['tokens_input'] - result_compact['tokens_input']
            print(f"   ✅ Économie: {tokens_saved} tokens ({tokens_saved/result_verbeux['tokens_input']*100:.0f}%)")
            
            # Pour tests temporaux, vérifier si pattern détecté
            if 'expected' in result_compact:
                if result_compact['matches'] and result_verbeux.get('matches', False):
                    print(f"   ✅ Pattern '{result_compact['expected']}' détecté dans les 2 versions")
                elif result_compact['matches']:
                    print(f"   ⚠️ Pattern détecté en COMPACT mais pas en VERBEUX")
                elif result_verbeux.get('matches', False):
                    print(f"   ⚠️ Pattern détecté en VERBEUX mais pas en COMPACT")
        else:
            print("   ❌ ERREUR lors du test")
            if not result_verbeux['success']:
                print(f"      VERBEUX: {result_verbeux.get('error')}")
            if not result_compact['success']:
                print(f"      COMPACT: {result_compact.get('error')}")
        
        results.append({
            'test_id': test_case['id'],
            'verbeux': result_verbeux,
            'compact': result_compact
        })
        
        print()
        print("-" * 80)
        print()
    
    # Résumé final
    print()
    print("=" * 80)
    print("📈 RÉSUMÉ FINAL")
    print("=" * 80)
    print()
    
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r['verbeux']['success'] and r['compact']['success'])
    
    print(f"Tests exécutés: {successful_tests}/{total_tests}")
    print()
    
    if successful_tests > 0:
        avg_tokens_saved = sum(
            r['verbeux']['tokens_input'] - r['compact']['tokens_input']
            for r in results
            if r['verbeux']['success'] and r['compact']['success']
        ) / successful_tests
        
        print(f"Économie moyenne par appel: {avg_tokens_saved:.0f} tokens")
        print()
        print("✅ RECOMMANDATION:")
        print("   Examiner visuellement les réponses ci-dessus pour valider qualité")
        print("   Si qualité satisfaisante → déploiement prompts compacts recommandé")
    
    print()
    print("=" * 80)


# ===================================================================
# EXECUTION
# ===================================================================

if __name__ == "__main__":
    print()
    print("⚠️  ATTENTION: Ce test nécessite une connexion API active")
    print("    Il va consommer environ 500-1000 tokens GROK")
    print()
    
    response = input("Continuer ? (o/N): ").strip().lower()
    if response not in ['o', 'oui', 'y', 'yes']:
        print("Test annulé")
        exit(0)
    
    print()
    asyncio.run(run_tests())
