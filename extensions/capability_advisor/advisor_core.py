# 🎯 Capability Advisor - Moteur Analyse Archiviste
"""
Analyse contextuelle conversation via Archiviste
Suggère intelligemment capacités IA pertinentes
"""

import json
import re
from typing import Optional, Dict, List
from dataclasses import dataclass

from .config import CapabilityAdvisorConfig
from .capability_catalog import get_capability, get_all_capabilities, format_capabilities_list


@dataclass
class CapabilitySuggestion:
    """Suggestion capacité par Archiviste"""
    needs_capability: bool
    capability_id: Optional[str]
    reasoning: str
    suggestion: str
    confidence: float
    
    def __repr__(self):
        return f"CapabilitySuggestion(id={self.capability_id}, confidence={self.confidence:.2f})"


class AdvisorCore:
    """Moteur analyse contextuelle + suggestion capacités"""
    
    def __init__(self, archiviste_controller, config: CapabilityAdvisorConfig):
        """
        Initialise moteur analyse
        
        Args:
            archiviste_controller: Contrôleur IA Archiviste
            config: Configuration extension
        """
        self.archiviste_controller = archiviste_controller
        self.config = config
        
        print(f"[CAPABILITY-ADVISOR] ✅ AdvisorCore initialisé")
    
    async def analyze_conversation(
        self, 
        user_message: str, 
        conversation_history: list
    ) -> Optional[CapabilitySuggestion]:
        """
        Analyse conversation et suggère capacité si pertinent
        
        Args:
            user_message: Message utilisateur actuel
            conversation_history: Historique conversation complet
            
        Returns:
            CapabilitySuggestion | None: Suggestion capacité ou None
        """
        try:
            # 1. Extraire contexte récent
            recent_context = self._extract_recent_exchanges(
                conversation_history, 
                last_n=self.config.config.get('recent_context_messages', 3)
            )
            
            # 2. Construire prompt analyse Archiviste
            # Injecter seuils effectifs par capacité (UI config > catalog > global)
            global_threshold = self.config.config.get('confidence_threshold', 0.70)
            threshold_parts = []
            for cap_id, cap_info in get_all_capabilities().items():
                catalog_thresh = cap_info.get('confidence_threshold', 0.70)
                custom_thresh = self.config.get_capability_threshold(cap_id, None)
                effective = custom_thresh if custom_thresh is not None else catalog_thresh
                final_thresh = max(effective, global_threshold)
                threshold_parts.append(f"{cap_id}:{final_thresh:.2f}")
            capability_thresholds_str = " | ".join(threshold_parts)

            analysis_prompt = self.config.get_advisor_prompt_template().format(
                user_message=user_message,
                recent_context=recent_context,
                available_capabilities=format_capabilities_list(),
                capability_thresholds=capability_thresholds_str
            )
            
            # 3. Appel Archiviste pour analyse JSON
            print(f"[CAPABILITY-ADVISOR] 🔍 Analyse contexte: '{user_message[:50]}...'")
            
            messages = [
                {"role": "system", "content": analysis_prompt},
                {"role": "user", "content": "Analyse ce contexte et suggère UNE capacité si pertinent (format JSON strict)."}
            ]
            
            # ═══ DEBUG_TOKEN_TRACKING ═══
            response, error = await self.archiviste_controller.call_chat_api(
                messages=messages,
                max_tokens=self.config.config.get('max_tokens', 500),
                context_length=self.archiviste_controller.context_length,
                temperature=self.config.config.get('temperature', 0.3),
                is_json=True,
                log_source="capability_advisor"  # 🔬 TRACKING
            )
            # ═══════════════════════════
            
            if error:
                print(f"[CAPABILITY-ADVISOR] ❌ Erreur Archiviste: {error}")
                return None
            
            if not response:
                print(f"[CAPABILITY-ADVISOR] ⚠️ Réponse Archiviste vide")
                return None
            
            # 4. Parser réponse JSON
            suggestion = self._parse_archiviste_response(response)
            
            if suggestion is None:
                print(f"[CAPABILITY-ADVISOR] ⚪ Aucune suggestion pertinente")
                return None
            
            # 5. Valider threshold confidence
            capability_info = get_capability(suggestion.capability_id)
            if not capability_info:
                print(f"[CAPABILITY-ADVISOR] ⚠️ Capacité inconnue: {suggestion.capability_id}")
                return None
            
            # Priorité des seuils: 1. Configuré UI > 2. Défaut catalog > 3. Global
            capability_threshold_catalog = capability_info.get('confidence_threshold', 0.70)
            capability_threshold_custom = self.config.get_capability_threshold(suggestion.capability_id, None)
            global_threshold = self.config.config.get('confidence_threshold', 0.70)
            
            # Utiliser seuil custom si configuré, sinon catalog
            effective_threshold = capability_threshold_custom if capability_threshold_custom is not None else capability_threshold_catalog
            
            # Prendre le threshold le plus strict entre effective et global
            min_threshold = max(effective_threshold, global_threshold)
            
            if suggestion.confidence < min_threshold:
                print(f"[CAPABILITY-ADVISOR] ⚠️ Confidence trop faible: {suggestion.confidence:.2f} < {min_threshold:.2f} ({'custom' if capability_threshold_custom else 'catalog'})")
                return None
            
            print(f"[CAPABILITY-ADVISOR] ✅ Suggestion validée: {suggestion.capability_id} (confidence: {suggestion.confidence:.2f})")
            print(f"[CAPABILITY-ADVISOR] 📝 Conseil: {suggestion.suggestion[:100]}...")
            
            return suggestion
            
        except Exception as e:
            print(f"[CAPABILITY-ADVISOR] ❌ Erreur analyse: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _extract_recent_exchanges(self, history: list, last_n: int = 3) -> str:
        """
        Extrait derniers échanges conversation pour contexte
        
        Args:
            history: Historique conversation
            last_n: Nombre messages récents à extraire
            
        Returns:
            str: Contexte conversationnel formaté
        """
        if not history:
            return "Début de conversation (pas d'historique)"
        
        # Prendre derniers messages (user + assistant)
        recent_messages = history[-last_n*2:] if len(history) > last_n*2 else history
        
        context_lines = []
        for msg in recent_messages:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            
            # Limiter longueur contenu
            if isinstance(content, str):
                content_short = content[:200] + "..." if len(content) > 200 else content
            else:
                content_short = str(content)[:200]
            
            context_lines.append(f"{role.upper()}: {content_short}")
        
        return "\n".join(context_lines)
    
    def _parse_archiviste_response(self, response: str) -> Optional[CapabilitySuggestion]:
        """
        Parse réponse JSON Archiviste
        
        Args:
            response: Réponse brute Archiviste
            
        Returns:
            CapabilitySuggestion | None: Suggestion parsée ou None
        """
        try:
            # Nettoyage JSON (compatible tous providers)
            cleaned_response = self._clean_json_response(response)
            
            if not cleaned_response:
                print(f"[CAPABILITY-ADVISOR] ⚠️ JSON vide après nettoyage")
                return None
            
            # Nettoyer les caractères de contrôle dans les strings JSON
            cleaned_response = self._clean_json_control_chars(cleaned_response)
            
            # Debug: afficher les premiers caractères pour vérifier
            # print(f"[CAPABILITY-ADVISOR] 🔧 JSON après nettoyage: {cleaned_response[:100]}...")
            
            # Parser JSON avec try-except spécifique
            try:
                analysis_result = json.loads(cleaned_response)
            except json.JSONDecodeError as json_err:
                # Tentative de nettoyage plus agressif
                import re
                # Remplacer les vraies newlines dans le JSON par des espaces
                fallback_cleaned = re.sub(r'(?<!\\)\\n', '\\\\n', cleaned_response)
                fallback_cleaned = re.sub(r'\n', ' ', fallback_cleaned)
                fallback_cleaned = re.sub(r'\r', ' ', fallback_cleaned)
                fallback_cleaned = re.sub(r'\t', ' ', fallback_cleaned)
                try:
                    analysis_result = json.loads(fallback_cleaned)
                    print(f"[CAPABILITY-ADVISOR] 🔧 JSON récupéré après nettoyage agressif")
                except:
                    raise json_err  # Relever l'erreur originale
            
            # Vérifier structure JSON
            if not isinstance(analysis_result, dict):
                print(f"[CAPABILITY-ADVISOR] ⚠️ JSON invalide (pas un dict)")
                return None
            
            # Extraire champs obligatoires
            needs_capability = analysis_result.get('needs_capability', False)
            
            # Si pas besoin de capacité, retourner None
            if not needs_capability:
                return None
            
            capability_id = analysis_result.get('capability_id')
            reasoning = analysis_result.get('reasoning', '')
            suggestion = analysis_result.get('suggestion', '')
            confidence = float(analysis_result.get('confidence', 0.0))
            
            # Validation champs
            if not capability_id or not suggestion:
                print(f"[CAPABILITY-ADVISOR] ⚠️ Champs manquants dans JSON")
                return None
            
            # Créer suggestion
            return CapabilitySuggestion(
                needs_capability=True,
                capability_id=capability_id,
                reasoning=reasoning,
                suggestion=suggestion,
                confidence=confidence
            )
            
        except json.JSONDecodeError as e:
            print(f"[CAPABILITY-ADVISOR] ❌ Erreur parsing JSON: {e}")
            print(f"[CAPABILITY-ADVISOR] Réponse brute: {response[:200]}...")
            return None
        except Exception as e:
            print(f"[CAPABILITY-ADVISOR] ❌ Erreur parse: {e}")
            return None
    
    def _clean_json_response(self, response: str) -> str:
        """
        Nettoie réponse JSON (compatible tous providers)
        Pattern identique à archi_sensor
        
        Args:
            response: Réponse brute
            
        Returns:
            str: JSON nettoyé
        """
        # 1. Supprimer blocs markdown
        response = re.sub(r'```json\s*\n?', '', response, flags=re.IGNORECASE)
        response = re.sub(r'```\s*json\s*\n?', '', response, flags=re.IGNORECASE)
        response = re.sub(r'\n?\s*```', '', response)
        response = response.replace('```', '')
        
        # 2. Extraction JSON intelligente
        start_idx = response.find('{')
        if start_idx == -1:
            return ""
        
        # Compter accolades pour trouver fin exacte JSON
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
        
        # Extraire JSON valide
        if end_idx > start_idx:
            json_content = response[start_idx:end_idx + 1]
        else:
            # Fallback méthode ancienne
            end_idx = response.rfind('}')
            if end_idx > start_idx:
                json_content = response[start_idx:end_idx + 1]
            else:
                return ""
        
        return json_content.strip()
    
    def _clean_json_control_chars(self, json_str: str) -> str:
        """
        Nettoie les caractères de contrôle dans les valeurs de chaînes JSON.
        Certains LLMs génèrent des newlines/tabs non échappés dans les strings.
        
        Args:
            json_str: Chaîne JSON potentiellement mal formée
            
        Returns:
            Chaîne JSON avec caractères de contrôle échappés
        """
        result = []
        in_string = False
        escape_next = False
        
        for char in json_str:
            if escape_next:
                result.append(char)
                escape_next = False
                continue
            
            if char == '\\':
                result.append(char)
                escape_next = True
                continue
            
            if char == '"':
                in_string = not in_string
                result.append(char)
                continue
            
            # Si on est dans une chaîne, échapper les caractères de contrôle
            if in_string:
                if char == '\n':
                    result.append('\\n')
                elif char == '\r':
                    result.append('\\r')
                elif char == '\t':
                    result.append('\\t')
                elif ord(char) < 32:  # Autres caractères de contrôle
                    result.append(f'\\u{ord(char):04x}')
                else:
                    result.append(char)
            else:
                result.append(char)
        
        return ''.join(result)
