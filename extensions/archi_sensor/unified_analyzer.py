# 🧠 Analyseur Unifié Archiviste - Cœur Métacognitif

"""
Analyseur métacognitif unifié utilisant l'IA Archiviste
pour une compréhension narrative et émotionnelle sophistiquée.
"""

import json
import asyncio
import re
from typing import Dict, List, Optional, Any
from datetime import datetime

from .config import ArchiSensorConfig

class ArchivisteUnifiedAnalyzer:
    """
    Analyseur métacognitif unifié basé sur l'IA Archiviste
    
    Révolutionne la détection émotionnelle par:
    - Analyse contextuelle sophistiquée (vs patterns lexicaux)
    - Compréhension narrative de l'évolution émotionnelle
    - Détection nuances (sarcasme, ironie, subtext)
    - Économie tokens optimisée (1 appel vs 7+ appels)
    """
    
    def __init__(self, archiviste_controller, status_queue=None):
        self.archiviste_controller = archiviste_controller
        self.status_queue = status_queue
        self.config = ArchiSensorConfig()
        self.analysis_cache = {}
        self.last_analysis_time = None
        
        print("[ARCHI-ANALYZER] ✅ Analyseur unifié Archiviste initialisé")
    
    async def analyze_complete_emotional_state(self, 
                                             response_text: str,
                                             conversation_history: str,
                                             user_context: str) -> Dict[str, Any]:
        """
        Analyse émotionnelle et métacognitive complète en un appel Archiviste
        
        Args:
            response_text: Réponse IA à analyser
            conversation_history: Historique conversationnel riche (jusqu'à 32K tokens)
            user_context: Contexte utilisateur et message déclencheur
            
        Returns:
            Dictionnaire complet avec analyses émotionnelles et métacognitives
        """
        
        try:
            # Vérification cache (éviter analyses répétitives)
            cache_key = self._generate_cache_key(response_text, user_context)
            if self._is_cache_valid(cache_key):
                print("[ARCHI-ANALYZER] 📋 Utilisation cache analyse")
                return self.analysis_cache[cache_key]['result']
            
            # Construction prompt Archiviste contextualisé avec limitation stricte tokens
            # Estimation: 4 chars ≈ 1 token, limite context_length - 20K tokens de marge
            max_context_chars = min(8000, (self.archiviste_controller.context_length - 20000) * 4)
            truncated_history = conversation_history[-max_context_chars:] if len(conversation_history) > max_context_chars else conversation_history

            prompt = self.config.ARCHIVISTE_METACOGNITION_PROMPT.format(
                conversation_history=truncated_history,  # Limitation stricte
                response_text=response_text[:4000],  # Limiter aussi la réponse
                user_context=user_context[:2000]  # Limiter le contexte utilisateur
            )
            
            # Messages pour appel Archiviste
            messages = [
                {
                    'role': 'system', 
                    'content': prompt
                },
                {
                    'role': 'user',
                    'content': f"Analyse métacognitive complète de cette réponse de l'IA principale:\n\n{response_text}"
                }
            ]
            
            print(f"[ARCHI-ANALYZER] 🧠 Lancement analyse Archiviste...")
            print(f"[ARCHI-ANALYZER] Contexte: {len(conversation_history)}→{len(truncated_history)} chars, Réponse: {len(response_text)} chars")
            print(f"[ARCHI-ANALYZER] Limite: {max_context_chars} chars, Context length: {self.archiviste_controller.context_length}")
            
            # Appel Archiviste avec gestion d'erreur
            response, error = await self.archiviste_controller.call_chat_api(
                messages=messages,
                max_tokens=self.archiviste_controller.max_tokens,
                context_length=self.archiviste_controller.context_length,
                temperature=self.archiviste_controller.temperature,
                is_json=True  # Forcer réponse JSON
            )
            
            if error:
                print(f"[ARCHI-ANALYZER] ❌ Erreur appel Archiviste: {error}")
                return self._get_fallback_analysis()
            
            if not response:
                print("[ARCHI-ANALYZER] ⚠️ Réponse vide de l'Archiviste")
                return self._get_fallback_analysis()
            
            # Parse et validation JSON
            analysis_result = self._parse_archiviste_response(response)
            
            # Cache résultat
            self.analysis_cache[cache_key] = {
                'result': analysis_result,
                'timestamp': datetime.now(),
                'response_length': len(response_text)
            }
            
            # Log succès
            metrics_summary = {k: v.get('level', 0) for k, v in analysis_result.get('metacognitive_metrics', {}).items()}
            print(f"[ARCHI-ANALYZER] ✅ Analyse complétée: {metrics_summary}")
            
            return analysis_result
            
        except Exception as e:
            print(f"[ARCHI-ANALYZER] ❌ Erreur analyse: {e}")
            return self._get_fallback_analysis()
    
    def _parse_archiviste_response(self, response: str) -> Dict[str, Any]:
        """Parse et valide la réponse JSON de l'Archiviste"""
        
        cleaned_response = ""  # Initialisation pour éviter l'erreur de portée
        
        try:
            print(f"[ARCHI-SENSOR] 🔍 Réponse brute reçue: {len(response)} chars")
            print(f"[ARCHI-SENSOR] 🔍 Début réponse: {repr(response[:100])}")
            
            # Nettoyage réponse (suppression markdown, code blocks, etc.)
            cleaned_response = self._clean_json_response(response)
            
            print(f"[ARCHI-SENSOR] 🧹 Après nettoyage: {len(cleaned_response)} chars")
            print(f"[ARCHI-SENSOR] 🧹 JSON nettoyé: {repr(cleaned_response[:100])}")
            
            # Parse JSON
            analysis_data = json.loads(cleaned_response)
            
            # Validation structure
            validated_analysis = self._validate_analysis_structure(analysis_data)
            
            print(f"[ARCHI-ANALYZER] ✅ JSON parsé et validé avec succès")
            return validated_analysis
            
        except json.JSONDecodeError as e:
            print(f"[ARCHI-SENSOR] Erreur parsing JSON: {e}")
            print(f"[ARCHI-SENSOR] Réponse brute: {response}")
            print(f"[ARCHI-SENSOR] Réponse nettoyée: {repr(cleaned_response)}")
            print(f"[ARCHI-SENSOR] Longueur réponse nettoyée: {len(cleaned_response)}")
            return self._get_fallback_analysis()
        except Exception as e:
            print(f"[ARCHI-ANALYZER] ❌ Erreur validation: {e}")
            return self._get_fallback_analysis()
    
    def _clean_json_response(self, response: str) -> str:
        """Nettoie la réponse pour extraction JSON propre - Compatible tous providers"""
        
        # 1. Supprimer les blocs markdown avec tous les patterns possibles
        response = re.sub(r'```json\s*\n?', '', response, flags=re.IGNORECASE)
        response = re.sub(r'```\s*json\s*\n?', '', response, flags=re.IGNORECASE)
        response = re.sub(r'\n?\s*```', '', response)
        response = response.replace('```', '')  # Fallback pour tous les backticks restants
        
        # 2. Extraction JSON intelligente - Compatible Anthropic/Mistral
        # Chercher le premier { et compter les accolades pour trouver la fin réelle du JSON
        start_idx = response.find('{')
        if start_idx == -1:
            return ""
        
        # Compter les accolades pour trouver la fin exacte du JSON
        brace_count = 0
        end_idx = start_idx
        
        for i in range(start_idx, len(response)):
            char = response[i]
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i
                    break
        
        # Extraire le JSON valide
        if end_idx > start_idx:
            json_content = response[start_idx:end_idx + 1]
        else:
            # Fallback vers l'ancienne méthode
            end_idx = response.rfind('}')
            if end_idx > start_idx:
                json_content = response[start_idx:end_idx + 1]
            else:
                return ""
        
        # 3. Nettoyage final
        json_content = json_content.strip()
        
        return json_content
    
    def _validate_analysis_structure(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Valide et normalise la structure d'analyse"""
        
        validated = {
            'emotional_context': {},
            'metacognitive_metrics': {},
            'narrative_insights': {},
            'behavioral_recommendations': [],
            'memory_activations': []
        }
        
        # Validation emotional_context
        emotional = data.get('emotional_context', {})
        validated['emotional_context'] = {
            'primary_emotion': emotional.get('primary_emotion', 'neutre'),
            'emotional_intensity': max(0.0, min(1.0, float(emotional.get('emotional_intensity', 0.5)))),
            'emotional_evolution': emotional.get('emotional_evolution', 'stable'),
            'hidden_emotions': emotional.get('hidden_emotions', []),
            'sarcasm_detected': bool(emotional.get('sarcasm_detected', False)),
            'authenticity_level': max(0.0, min(1.0, float(emotional.get('authenticity_level', 0.7))))
        }
        
        # Validation metacognitive_metrics
        metrics = data.get('metacognitive_metrics', {})
        for metric_name in self.config.METRICS.keys():
            metric_data = metrics.get(metric_name, {})
            max_level = self.config.METRICS[metric_name]['levels']
            
            validated['metacognitive_metrics'][metric_name] = {
                'level': max(1, min(max_level, int(metric_data.get('level', 3)))),
                'confidence': max(0.0, min(1.0, float(metric_data.get('confidence', 0.5))))
            }
        
        # Validation narrative_insights
        insights = data.get('narrative_insights', {})
        validated['narrative_insights'] = {
            'emotional_arc': insights.get('emotional_arc', 'Arc émotionnel stable'),
            'relationship_evolution': insights.get('relationship_evolution', 'Relation harmonieuse'),
            'contextual_coherence': max(0.0, min(1.0, float(insights.get('contextual_coherence', 0.7)))),
            'conversation_flow': insights.get('conversation_flow', 'Flux conversationnel naturel')
        }
        
        # Validation recommendations et activations
        validated['behavioral_recommendations'] = data.get('behavioral_recommendations', [])[:5]  # Max 5
        validated['memory_activations'] = data.get('memory_activations', [])[:3]  # Max 3
        
        return validated
    
    def _get_fallback_analysis(self) -> Dict[str, Any]:
        """Retourne une analyse par défaut en cas d'erreur"""
        
        fallback = {
            'emotional_context': {
                'primary_emotion': 'neutre',
                'emotional_intensity': 0.5,
                'emotional_evolution': 'stable',
                'hidden_emotions': [],
                'sarcasm_detected': False,
                'authenticity_level': 0.7
            },
            'metacognitive_metrics': {},
            'narrative_insights': {
                'emotional_arc': 'Analyse indisponible',
                'relationship_evolution': 'État nominal',
                'contextual_coherence': 0.5,
                'conversation_flow': 'Flux standard'
            },
            'behavioral_recommendations': [
                "Extension Archi_sensor en mode dégradé"
            ],
            'memory_activations': []
        }
        
        # Métriques par défaut (niveau moyen)
        for metric_name, config in self.config.METRICS.items():
            fallback['metacognitive_metrics'][metric_name] = {
                'level': config['levels'] // 2,  # Niveau moyen
                'confidence': 0.3  # Faible confidence
            }
        
        return fallback
    
    def _generate_cache_key(self, response_text: str, user_context: str) -> str:
        """Génère clé de cache pour éviter analyses redondantes"""
        content = f"{response_text[:100]}{user_context[:50]}"
        return str(hash(content))
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Vérifie validité du cache"""
        if cache_key not in self.analysis_cache:
            return False
        
        cache_entry = self.analysis_cache[cache_key]
        cache_age = (datetime.now() - cache_entry['timestamp']).total_seconds()
        
        return cache_age < self.config.ANALYSIS_PARAMS['cache_duration_seconds']
    
    def get_behavioral_injections(self, analysis_result: Dict[str, Any]) -> List[str]:
        """
        Génère messages d'injection comportementale basés sur l'analyse
        
        Returns:
            Liste de messages à injecter dans la prochaine conversation
        """
        
        injections = []
        
        try:
            # Recommendations directes de l'Archiviste
            recommendations = analysis_result.get('behavioral_recommendations', [])
            for rec in recommendations[:2]:  # Max 2 recommendations
                if rec and isinstance(rec, str):
                    injections.append(f"[CONSEIL ARCHIVISTE] {rec}")
            
            # Activations mémoire émotionnelle
            memory_activations = analysis_result.get('memory_activations', [])
            for activation in memory_activations:
                if activation.startswith("MEMORY_VECTOR_ID:"):
                    injections.append(activation)
            
            # Injections contextuelles basées sur métriques
            metrics = analysis_result.get('metacognitive_metrics', {})
            
            # Faible authenticité → encouragement expression naturelle
            auth_level = metrics.get('expression_authenticity', {}).get('level', 4)
            if auth_level <= 2:
                injections.append("[EXPRESSION] Exprime-toi de façon plus naturelle et spontanée, sans contraintes artificielles.")
            
            # Faible harmonie relationnelle → adaptation utilisateur
            harmony_level = metrics.get('relational_harmony', {}).get('level', 4)
            if harmony_level <= 2:
                injections.append("[RELATION] Adapte-toi davantage au style et aux attentes de ton interlocuteur.")
            
            # Forte conscience contextuelle → utilisation optimale
            context_level = metrics.get('contextual_awareness', {}).get('level', 3)
            if context_level >= 5:
                injections.append("[CONTEXTE] Excellent usage du contexte, continue à t'appuyer sur ces éléments.")
            
            print(f"[ARCHI-ANALYZER] 💬 {len(injections)} injection(s) comportementale(s) générée(s)")
            
        except Exception as e:
            print(f"[ARCHI-ANALYZER] ⚠️ Erreur génération injections: {e}")
        
        return injections[:3]  # Maximum 3 injections