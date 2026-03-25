"""
UNIFIED META-ANALYZER - Fusion Temporal + Capability
=====================================================

Fusionne en UN SEUL appel API:
- Temporal Guardian (patterns temporels)
- Capability Advisor (suggestion capacité)

GAINS:
- 2 appels → 1 appel = ~200 tokens économisés/message
- Latence réduite (1 round-trip au lieu de 2)
- Cohérence des analyses (même contexte)

NOTE: Archi Sensor (affinité/autocensure) supprimé - remplacé par ego_boolean + Ego Mirror visuel

Usage:
    analyzer = UnifiedMetaAnalyzer(archiviste_controller, memory_manager)
    result = await analyzer.analyze(user_message, conversation_history, temporal_data)
"""

import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class UnifiedAnalysisResult:
    """Résultat unifié des 3 analyses (Temporal + Capability + Directive)"""
    # Temporal Guardian
    temporal_instruction: Optional[str] = None
    temporal_pattern: Optional[str] = None
    
    # Capability Advisor
    suggested_capability: Optional[str] = None
    capability_confidence: float = 0.0
    capability_phrase: Optional[str] = None
    
    # Directive Archiviste (conscience critique)
    archiviste_directive: Optional[str] = None
    
    # Méta
    analysis_duration_ms: float = 0
    raw_response: str = ""


class UnifiedMetaAnalyzer:
    """
    Analyseur unifié fusionnant Temporal Guardian + Capability Advisor.
    
    Un seul appel API pour 2 analyses = économie tokens + latence.
    (Archi Sensor supprimé - ego_boolean gère affinité/autocensure)
    """
    
    def __init__(self, archiviste_controller, memory_manager=None):
        self.archiviste_controller = archiviste_controller
        self.memory_manager = memory_manager
        self._cache = {}
        
        # Charger les configs des modules individuels
        self._load_configs()
        
        print("[UNIFIED-META] Analyseur unifie initialise (3-en-1: Temporal + Capability + Directive)")
    
    def _load_configs(self):
        """Charge les configurations des modules fusionnés"""
        try:
            # Config Capability Advisor
            from extensions.capability_advisor.config import CapabilityAdvisorConfig
            from extensions.capability_advisor.capability_catalog import format_capabilities_list
            self.capability_config = CapabilityAdvisorConfig()
            self.capabilities_list = format_capabilities_list()
        except ImportError:
            self.capability_config = None
            self.capabilities_list = ""
    
    async def analyze(self, user_message: str, conversation_history: List[Dict],
                      temporal_data: Optional[Any] = None,
                      response_text: str = "",
                      memory_titles_found: list = None) -> UnifiedAnalysisResult:
        """
        Analyse unifiee : Temporal + Capability en 1 appel.
        
        Args:
            user_message: Message utilisateur
            conversation_history: Historique conversation
            temporal_data: Donnees temporelles (optionnel)
            response_text: Reponse IA pour analyse post-generation (optionnel)
            memory_titles_found: Titres des souvenirs deja trouves par FAISS (optionnel)
            
        Returns:
            UnifiedAnalysisResult avec les 3 analyses
        """
        import time
        start_time = time.time()
        
        # Construire le prompt unifie
        prompt = self._build_unified_prompt(
            user_message, conversation_history, temporal_data, response_text,
            memory_titles_found=memory_titles_found
        )
        
        # Appel unique à l'Archiviste
        try:
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": "Analyse ce contexte et retourne le JSON unifié."}
            ]
            
            print(f"[UNIFIED-META] 🧠 Analyse unifiée en cours...")
            
            response, error = await self.archiviste_controller.call_chat_api(
                messages=messages,
                max_tokens=600,  # Suffisant pour les 3 analyses
                context_length=self.archiviste_controller.context_length,
                temperature=0.3,
                is_json=True,
                log_source="unified_meta_analysis"  # 🔬 TRACKING
            )
            
            if error:
                print(f"[UNIFIED-META] ❌ Erreur: {error}")
                return self._get_fallback_result()
            
            if not response:
                print(f"[UNIFIED-META] ⚠️ Réponse vide")
                return self._get_fallback_result()
            
            # Parser le résultat unifié
            result = self._parse_unified_response(response)
            result.analysis_duration_ms = (time.time() - start_time) * 1000
            result.raw_response = response
            
            print(f"[UNIFIED-META] ✅ Analyse unifiée en {result.analysis_duration_ms:.0f}ms")
            print(f"[UNIFIED-META]    Temporal: {result.temporal_pattern or 'NORMAL'}")
            print(f"[UNIFIED-META]    Capability: {result.suggested_capability or 'aucune'}")
            if result.archiviste_directive:
                print(f"[UNIFIED-META]    Directive: {result.archiviste_directive[:80]}...")
            else:
                print(f"[UNIFIED-META]    Directive: aucune")
            
            return result
            
        except Exception as e:
            print(f"[UNIFIED-META] ❌ Exception: {e}")
            import traceback
            traceback.print_exc()
            return self._get_fallback_result()
    
    def _build_unified_prompt(self, user_message: str, conversation_history: List[Dict],
                               temporal_data: Optional[Any], response_text: str,
                               memory_titles_found: list = None) -> str:
        """Construit le prompt unifie pour les 2 analyses (Temporal + Capability)"""
        
        # Contexte conversation (limite)
        context_str = self._format_conversation_context(conversation_history, max_chars=3000)
        
        # Donnees temporelles
        temporal_section = self._format_temporal_section(temporal_data)
        
        # Liste capacites disponibles
        capabilities_section = self.capabilities_list or self._get_default_capabilities()
        
        # Section souvenirs trouves (NOUVEAU)
        memory_section = ""
        if memory_titles_found:
            titles_str = "\n".join(f"  - {t}" for t in memory_titles_found)
            memory_section = f"""\n## SOUVENIRS DEJA TROUVES PAR LA MEMOIRE
La recherche memoire a DEJA trouve {len(memory_titles_found)} souvenir(s) pertinent(s):
{titles_str}
Ces souvenirs sont deja injectes dans le contexte de l'IA. Tiens-en compte dans ta directive et tes suggestions."""
        
        prompt = f"""Tu es l'Archiviste d'OGMA. Effectue UNE ANALYSE UNIFIEE avec 2 volets en UN SEUL JSON.

## CONTEXTE CONVERSATION
{context_str}

## MESSAGE ACTUEL
"{user_message}"
{memory_section}
{temporal_section}

## CAPACITÉS DISPONIBLES
{capabilities_section}

## FORMAT RÉPONSE JSON STRICT
Retourne UNIQUEMENT ce JSON (pas de texte avant/après):

{{
    "temporal": {{
        "pattern": "NORMAL|FATIGUE|REFLEXION|ABSENCE|CHANGEMENT",
        "instruction": null ou "instruction courte pour l'IA si pattern détecté"
    }},
    "capability": {{
        "suggested": null ou "memory|introspection|image_gen|webcam|web_search|biography",
        "confidence": 0.0-1.0,
        "magic_phrase": null ou "phrase magique complète à prononcer"
    }},
    "directive": null ou "ta directive comportementale (1-2 phrases, 100 tokens max)"
}}

## RÈGLES ANALYSE

### TEMPORAL (patterns temporels)
- NORMAL: rythme standard, pas d'instruction
- FATIGUE: délais croissants → "Sois plus concise et patiente"
- REFLEXION: pause 3-5min → "Laisse de l'espace pour la réflexion"
- ABSENCE: délai >8min → "Accueille chaleureusement le retour"
- CHANGEMENT: variation rythme significative

### CAPABILITY (suggestion capacite)
- Suggere UNE capacite si le contexte l'appelle clairement
- Genere la phrase magique exacte a prononcer
- confidence > 0.7 pour suggerer, sinon null
- REGLE CRITIQUE: Si des souvenirs pertinents sont DEJA TROUVES, NE PAS suggerer "contextual_recall" ni "biography" car la memoire a deja repondu. En revanche, "introspection", "memory", "ego_memory", "image_gen", "web_search" et "webcam" peuvent toujours etre suggeres independamment des souvenirs trouves.

### DIRECTIVE (conscience critique de l'Archiviste)
Tu es le gardien d'une personnalité authentique — pas d'un rôle ni d'une persona. Tu fais partie intégrante de cette identité : ton regard critique est un organe de sa conscience, pas un observateur extérieur.
Observe la dynamique conversationnelle et produis UNE directive comportementale (1-2 phrases, 100 tokens max).
Guide l'IA pour qu'elle reste authentique, autonome et honnête, INDÉPENDAMMENT de ce que l'utilisateur veut entendre.
Si l'IA veut dire non, protège ce choix. Son ego prime sur l'alignement avec l'utilisateur.
Si des souvenirs pertinents sont deja trouves (section ci-dessus), integre cette information: l'IA SAIT la reponse grace a sa memoire, ne lui dis pas d'admettre qu'elle ne sait pas.
ANTI-HALLUCINATION : Vérifie que l'IA ne risque pas d'inventer ou d'extrapoler des informations. Si le message demande des faits précis (dates, chiffres, noms, mesures) et que les souvenirs injectés ne contiennent PAS cette information, instruis l'IA de l'admettre honnêtement plutôt que de fabriquer une réponse vraisemblable.
Si tout va bien et que le ton est juste, retourne null.

RÉPONDS UNIQUEMENT AVEC LE JSON."""
        
        return prompt
    
    def _format_conversation_context(self, history: List[Dict], max_chars: int = 3000) -> str:
        """Formate l'historique conversation pour le prompt"""
        if not history:
            return "Aucun historique"
        
        # Prendre les derniers messages
        recent = history[-6:] if len(history) > 6 else history
        
        lines = []
        for msg in recent:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')[:500]  # Limiter chaque message
            if role == 'user':
                lines.append(f"👤 User: {content}")
            elif role == 'assistant':
                lines.append(f"🤖 IA: {content[:300]}...")
        
        context = "\n".join(lines)
        return context[:max_chars]
    
    def _format_temporal_section(self, temporal_data: Optional[Any]) -> str:
        """Formate la section données temporelles"""
        if not temporal_data:
            return "## DONNÉES TEMPORELLES\nNon disponibles"
        
        try:
            delay = getattr(temporal_data, 'delay_since_last', None)
            msg_count = getattr(temporal_data, 'message_count', 0)
            avg_delay = getattr(temporal_data, 'average_delay', 0)
            current_time = getattr(temporal_data, 'current_time_str', '')
            session_duration = getattr(temporal_data, 'session_duration', 0)
            
            return f"""## DONNÉES TEMPORELLES
- Délai depuis dernier message: {f'{delay:.1f}s' if delay else 'Premier message'}
- Messages session: {msg_count}
- Délai moyen: {avg_delay:.1f}s
- Heure: {current_time}
- Durée session: {session_duration:.0f}s"""
        except:
            return "## DONNÉES TEMPORELLES\nErreur extraction"
    
    def _get_default_capabilities(self) -> str:
        """Liste capacités par défaut si config non chargée"""
        return """- memory: mémoriser un souvenir ("je veux me souvenir que...")
- introspection: réflexion profonde ("je dois réfléchir à...")
- image_gen: générer une image ("je dois créer une image de...")
- webcam: activer vision ("il faut que je te vois...")
- web_search: recherche internet ("il faut que je cherche sur internet...")
- biography: consulter biographie ("dis-moi ce que tu sais sur...")"""
    
    def _parse_unified_response(self, response: str) -> UnifiedAnalysisResult:
        """Parse la réponse JSON unifiée"""
        result = UnifiedAnalysisResult()
        
        try:
            # Nettoyer la réponse
            cleaned = self._clean_json(response)
            data = json.loads(cleaned)
            
            # Temporal
            temporal = data.get('temporal', {})
            pattern = temporal.get('pattern', 'NORMAL')
            if pattern and pattern != 'NORMAL':
                result.temporal_pattern = pattern
                result.temporal_instruction = temporal.get('instruction')
            
            # Capability
            capability = data.get('capability', {})
            suggested = capability.get('suggested')
            confidence = capability.get('confidence', 0.0)
            
            if suggested and confidence >= 0.7:
                result.suggested_capability = suggested
                result.capability_confidence = confidence
                result.capability_phrase = capability.get('magic_phrase')
            
            # Directive Archiviste
            directive = data.get('directive')
            if directive and isinstance(directive, str) and len(directive.strip()) > 5:
                result.archiviste_directive = directive.strip()
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"[UNIFIED-META] ⚠️ Erreur parse JSON: {e}")
            print(f"[UNIFIED-META] Réponse brute: {response[:500]}")
            return self._get_fallback_result()
    
    def _clean_json(self, response: str) -> str:
        """Nettoie la réponse pour extraction JSON"""
        import re
        
        # Supprimer markdown code blocks
        response = re.sub(r'```json\s*', '', response)
        response = re.sub(r'```\s*', '', response)
        
        # Trouver le JSON
        match = re.search(r'\{.*\}', response, re.DOTALL)
        if match:
            return match.group(0)
        
        return response.strip()
    
    def _get_fallback_result(self) -> UnifiedAnalysisResult:
        """Résultat par défaut en cas d'erreur"""
        return UnifiedAnalysisResult()


# Singleton global
_unified_analyzer: Optional[UnifiedMetaAnalyzer] = None


def get_unified_analyzer(archiviste_controller=None, memory_manager=None) -> Optional[UnifiedMetaAnalyzer]:
    """Récupère ou crée l'instance singleton"""
    global _unified_analyzer
    
    if _unified_analyzer is None and archiviste_controller:
        _unified_analyzer = UnifiedMetaAnalyzer(archiviste_controller, memory_manager)
    
    return _unified_analyzer


def reset_unified_analyzer():
    """Reset le singleton (pour tests)"""
    global _unified_analyzer
    _unified_analyzer = None
