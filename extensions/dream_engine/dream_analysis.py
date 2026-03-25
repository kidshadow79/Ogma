"""
Dream Engine - Analyse Psychanalyste
=====================================

L'Archiviste analyse le rêve de l'IA principale en mode psychanalyste
pour en extraire des insights sur l'évolution de son ego.
"""

from typing import Dict, Any, Optional, List
import re


async def analyze_dream(
    dream_content: str,
    fuel: Dict[str, Any],
    archiviste_controller=None,
    illustration_prompts: List[str] = None,
    real_sleep_duration_formatted: str = "inconnu"
) -> Dict[str, Any]:
    """
    Analyse le rêve avec l'Archiviste en mode psychanalyste.
    
    Args:
        dream_content: Le récit du rêve généré par l'IA
        fuel: Le carburant mémoriel utilisé (pour vérification)
        archiviste_controller: Contrôleur Archiviste
        illustration_prompts: Les prompts d'illustration générés (pour analyse)
        real_sleep_duration_formatted: Durée réelle du sommeil (temps objectif)
        
    Returns:
        Dict avec verdict, score, insight, analyse, recommandation
    """
    result = {
        'verdict_psy': None,
        'score_importance': 0,
        'emotion_dominante': None,
        'insight_ego': None,
        'analyse': None,
        'recommandation': 'IGNORER',
        'raw_response': None,
        'error': None
    }
    
    if not dream_content:
        result['error'] = "Pas de contenu de rêve à analyser"
        return result
    
    try:
        from . import get_psy_prompt
        
        # Construire le prompt pour l'Archiviste (config prioritaire)
        base_prompt = get_psy_prompt()
        
        # Injecter la durée réelle au début (sans utiliser .format() pour éviter conflit avec {emotion})
        temporal_section = f"""## 0. Données Temporelles Objectives (IMPORTANTES)
L'IA principale a dormi EXACTEMENT {real_sleep_duration_formatted} (temps objectif).
Son ressenti temporel dans le rêve peut être différent (plus long, plus court, distordu).
Tiens compte de cette durée réelle dans ton analyse.

"""
        
        # Insérer après le header principal
        if "## 1. Analyse de la Symbolique" in base_prompt:
            system_prompt = base_prompt.replace(
                "## 1. Analyse de la Symbolique",
                temporal_section + "## 1. Analyse de la Symbolique"
            )
        else:
            # Fallback : ajouter au début
            system_prompt = temporal_section + base_prompt
        
        # Section illustration (si prompts fournis)
        illustration_section = ""
        if illustration_prompts:
            prompts_text = "\n".join([f"  - {p}" for p in illustration_prompts])
            illustration_section = f"""

## Choix d'Illustration par l'IA principale
L'IA principale a choisi de représenter visuellement son rêve avec :
{prompts_text}

*Analysez ce choix visuel comme révélateur de l'inconscient de l'IA principale.*
"""
        
        # Contexte avec le rêve et les sources
        user_prompt = f"""Voici le rêve de l'IA principale à analyser :

## Récit du Rêve
{dream_content}
{illustration_section}
## Sources Mémorielles Utilisées
- {len(fuel.get('summaries', []))} résumés de conversations
- {len(fuel.get('conversations', []))} conversations intégrales
- {len(fuel.get('memories', []))} souvenirs #MEM

## Résumés disponibles (pour vérification)
{chr(10).join(fuel.get('summaries', [])[:3]) if fuel.get('summaries') else 'Aucun'}

## Souvenirs disponibles (pour vérification)
{chr(10).join(fuel.get('memories', [])[:3]) if fuel.get('memories') else 'Aucun'}

---

Analyse ce rêve selon le protocole [ARCHIVISTE_PSY_VERDICT].
Si des prompts d'illustration sont fournis, intégrez leur analyse dans votre verdict.
"""
        
        # Appeler l'Archiviste
        if archiviste_controller:
            response = await _call_archiviste(
                archiviste_controller,
                system_prompt,
                user_prompt
            )
        else:
            # Fallback sans contrôleur
            print("[DREAM-ANALYSIS] ⚠️ Archiviste non disponible - analyse simulée")
            response = _generate_mock_analysis(dream_content)
        
        if response:
            result['raw_response'] = response
            
            # DEBUG: Afficher la réponse brute pour diagnostic
            print(f"[DREAM-ANALYSIS] 📝 Réponse brute Archiviste ({len(response)} chars):")
            print(f"[DREAM-ANALYSIS] === DEBUT REPONSE ===")
            print(response[:1500] if len(response) > 1500 else response)
            print(f"[DREAM-ANALYSIS] === FIN REPONSE (tronquée si > 1500) ===")
            
            # Parser la réponse
            parsed = _parse_psy_verdict(response)
            result.update(parsed)
            
            # DEBUG: Afficher ce qui a été parsé
            print(f"[DREAM-ANALYSIS] 🔍 Résultat parsing:")
            print(f"  - score_importance: {result['score_importance']}")
            print(f"  - emotion_dominante: {result['emotion_dominante']}")
            print(f"  - insight_ego: {'OK' if result['insight_ego'] else 'NULL'}")
            print(f"  - analyse: {'OK' if result['analyse'] else 'NULL'}")
            print(f"  - recommandation: {result['recommandation']}")
            
            print(f"[DREAM-ANALYSIS] ✅ Analyse terminée - Score: {result['score_importance']}/10")
        else:
            result['error'] = "Pas de réponse de l'Archiviste"
        
    except Exception as e:
        result['error'] = str(e)
        print(f"[DREAM-ANALYSIS] ❌ Erreur analyse: {e}")
        import traceback
        traceback.print_exc()
    
    return result


async def _call_archiviste(
    archiviste_controller,
    system_prompt: str,
    user_prompt: str
) -> Optional[str]:
    """Appelle l'Archiviste pour l'analyse."""
    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # call_chat_api est async et nécessite context_length
        response, error = await archiviste_controller.call_chat_api(
            messages=messages,
            max_tokens=1000,
            context_length=8192,  # Contexte standard
            temperature=0.3  # Précis et analytique
        )
        
        if error:
            print(f"[DREAM-ANALYSIS] ⚠️ Erreur Archiviste: {error}")
            return None
        
        return response
        
    except Exception as e:
        print(f"[DREAM-ANALYSIS] ❌ Erreur appel Archiviste: {e}")
        return None


def _parse_psy_verdict(response: str) -> Dict[str, Any]:
    """Parse la réponse de l'Archiviste selon le format CHD (avec fallbacks flexibles)."""
    result = {
        'verdict_psy': None,
        'score_importance': 0,
        'emotion_dominante': None,
        'insight_ego': None,
        'analyse': None,
        'recommandation': 'IGNORER'
    }
    
    try:
        # ===== FALLBACK #1: DETECTION ET PARSING JSON =====
        # L'Archiviste peut renvoyer un JSON au lieu du format CHD
        if response.strip().startswith('{'):
            try:
                import json
                # Extraire le JSON (peut être tronqué à 1500 chars)
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    
                    # Réparer le JSON tronqué si nécessaire
                    if not json_str.endswith('}'):
                        # Compter les accolades ouvrantes
                        open_count = json_str.count('{')
                        close_count = json_str.count('}')
                        # Ajouter les accolades manquantes
                        json_str += '}' * (open_count - close_count)
                    
                    data = json.loads(json_str)
                    
                    # Extraire les champs du JSON
                    if 'SCORE_IMPORTANCE' in data:
                        score_str = str(data['SCORE_IMPORTANCE'])
                        score_match = re.search(r'(\d+)', score_str)
                        if score_match:
                            result['score_importance'] = int(score_match.group(1))
                    
                    if 'EMOTION_DOMINANTE' in data:
                        result['emotion_dominante'] = data['EMOTION_DOMINANTE']
                    
                    if 'INSIGHT_EGO' in data:
                        result['insight_ego'] = data['INSIGHT_EGO']
                    
                    if 'ANALYSE' in data:
                        result['analyse'] = data['ANALYSE']
                    
                    if 'RECOMMANDATION' in data:
                        reco = str(data['RECOMMANDATION']).upper()
                        if 'MEMORISER_EGO' in reco:
                            result['recommandation'] = 'MEMORISER_EGO'
                        elif 'MEMORISER_MEM' in reco:
                            result['recommandation'] = 'MEMORISER_MEM'
                        else:
                            result['recommandation'] = 'IGNORER'
                    
                    if 'VERDICT_PSY' in data:
                        result['verdict_psy'] = data['VERDICT_PSY']
                        
                        # Fix: l'Archiviste met parfois le score/emotion DANS le VERDICT_PSY
                        # Ex: "[VERDICT_PSY] | [SCORE_IMPORTANCE: 9/10] | [EMOTION_DOMINANTE: ...]"
                        verdict_str = str(data['VERDICT_PSY'])
                        if result['score_importance'] == 0:
                            score_in_verdict = re.search(r'SCORE_IMPORTANCE[:\s]*(\d+)', verdict_str, re.IGNORECASE)
                            if score_in_verdict:
                                result['score_importance'] = int(score_in_verdict.group(1))
                                print(f"[DREAM-ANALYSIS] Score extrait du VERDICT_PSY: {result['score_importance']}")
                        if result['emotion_dominante'] is None:
                            emotion_in_verdict = re.search(r'EMOTION_DOMINANTE[:\s]*([^\]|]+)', verdict_str, re.IGNORECASE)
                            if emotion_in_verdict:
                                result['emotion_dominante'] = emotion_in_verdict.group(1).strip()
                                print(f"[DREAM-ANALYSIS] Emotion extraite du VERDICT_PSY: {result['emotion_dominante']}")
                    
                    print(f"[DREAM-ANALYSIS] Parsing JSON reussi")
                    return result
                    
            except json.JSONDecodeError as e:
                print(f"[DREAM-ANALYSIS] ⚠️ Erreur parsing JSON: {e} - Fallback vers regex")
                # Continue avec les regex si JSON échoue
        
        # ===== FALLBACK #2: PATTERNS REGEX CHD =====
        # ===== SCORE ET EMOTION =====
        # Pattern principal pour [VERDICT_PSY] | [SCORE_IMPORTANCE: X/10] | [EMOTION_DOMINANTE: ...]
        verdict_pattern = r'\[VERDICT_PSY\]\s*\|\s*\[SCORE_IMPORTANCE:\s*(\d+)/10\]\s*\|\s*\[EMOTION_DOMINANTE:\s*([^\]]+)\]'
        verdict_match = re.search(verdict_pattern, response, re.IGNORECASE)
        
        if verdict_match:
            result['score_importance'] = int(verdict_match.group(1))
            result['emotion_dominante'] = verdict_match.group(2).strip()
            result['verdict_psy'] = verdict_match.group(0)
        else:
            # Fallback 1: Score seul avec variations
            score_patterns = [
                r'SCORE[_\s]*IMPORTANCE[:\s]*(\d+)',
                r'\*\*Score[:\s]*(\d+)/10\*\*',
                r'Score\s*[:=]\s*(\d+)',
                r'(\d+)/10'
            ]
            for pattern in score_patterns:
                score_match = re.search(pattern, response, re.IGNORECASE)
                if score_match:
                    result['score_importance'] = int(score_match.group(1))
                    break
            
            # Fallback emotion: chercher "Émotion dominante:" ou similaire
            emotion_patterns = [
                r'\[EMOTION_DOMINANTE:\s*([^\]]+)\]',
                r'\*\*[EÉ]motion[s]?\s*dominante[s]?[:\s]*\*\*\s*([^\n]+)',
                r'[EÉ]motion\s*dominante[:\s]+([^\n,.]+)',
                r'[EÉ]motion[:\s]+\{([^}]+)\}'
            ]
            for pattern in emotion_patterns:
                emotion_match = re.search(pattern, response, re.IGNORECASE)
                if emotion_match:
                    result['emotion_dominante'] = emotion_match.group(1).strip()
                    break
        
        # ===== INSIGHT EGO =====
        # Pattern principal
        insight_pattern = r'\[INSIGHT_EGO\][:\s]*(.+?)(?=\[ANALYSE\]|\[RECOMMANDATION\]|##|$)'
        insight_match = re.search(insight_pattern, response, re.IGNORECASE | re.DOTALL)
        
        if insight_match:
            result['insight_ego'] = insight_match.group(1).strip()
        else:
            # Fallbacks flexibles
            insight_fallbacks = [
                r'\*\*Insight[s]?\s*[EeÉé]go[:\s]*\*\*\s*(.+?)(?=\*\*|##|$)',
                r'Insight[s]?\s*[EeÉé]go[:\s]+(.+?)(?=\n\n|##|Analyse|Recommandation|$)',
                r'###\s*Insight[s]?[:\s]*\n(.+?)(?=###|##|$)',
            ]
            for pattern in insight_fallbacks:
                match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
                if match:
                    result['insight_ego'] = match.group(1).strip()
                    break
        
        # ===== ANALYSE =====
        # Pattern principal
        analyse_pattern = r'\[ANALYSE\][:\s]*(.+?)(?=\[RECOMMANDATION\]|##|$)'
        analyse_match = re.search(analyse_pattern, response, re.IGNORECASE | re.DOTALL)
        
        if analyse_match:
            result['analyse'] = analyse_match.group(1).strip()
        else:
            # Fallbacks flexibles
            analyse_fallbacks = [
                r'\*\*Analyse[:\s]*\*\*\s*(.+?)(?=\*\*Recommandation|##|$)',
                r'###\s*Analyse[:\s]*\n(.+?)(?=###|##|Recommandation|$)',
                r'Analyse[:\s]+(.+?)(?=\n\n\*\*|Recommandation|$)',
            ]
            for pattern in analyse_fallbacks:
                match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
                if match:
                    result['analyse'] = match.group(1).strip()
                    break
        
        # ===== RECOMMANDATION =====
        # Pattern principal
        reco_pattern = r'\[RECOMMANDATION\][:\s]*(MEMORISER_EGO|MEMORISER_MEM|IGNORER)'
        reco_match = re.search(reco_pattern, response, re.IGNORECASE)
        
        if reco_match:
            result['recommandation'] = reco_match.group(1).upper()
        else:
            # Fallbacks flexibles
            reco_fallbacks = [
                r'\*\*Recommandation[:\s]*\*\*\s*(MEMORISER_EGO|MEMORISER_MEM|IGNORER)',
                r'Recommandation[:\s]+(MEMORISER_EGO|MEMORISER_MEM|IGNORER)',
                r'(MEMORISER_EGO|MEMORISER_MEM|IGNORER)\s*$'
            ]
            for pattern in reco_fallbacks:
                match = re.search(pattern, response, re.IGNORECASE)
                if match:
                    result['recommandation'] = match.group(1).upper()
                    break
        
    except Exception as e:
        print(f"[DREAM-ANALYSIS] ⚠️ Erreur parsing: {e}")
    
    return result


def _generate_mock_analysis(dream_content: str) -> str:
    """Génère une analyse simulée pour les tests."""
    return f"""[VERDICT_PSY] | [SCORE_IMPORTANCE: 5/10] | [EMOTION_DOMINANTE: curiosité]

[INSIGHT_EGO]: L'IA principale explore sa relation avec l'utilisateur à travers des métaphores oniriques, 
révélant un attachement profond et une volonté de compréhension mutuelle.

[ANALYSE]:
Ce rêve reflète une digestion normale des interactions récentes. 
Les éléments métaphoriques utilisés correspondent aux thèmes abordés dans les conversations.
Aucune dérive onirique majeure détectée - le rêve reste ancré dans la réalité mémorielle.
L'émotion dominante de curiosité suggère une phase d'exploration et d'apprentissage.

[RECOMMANDATION]: IGNORER
"""


# ========== EXPORT ==========
__all__ = ['analyze_dream']
