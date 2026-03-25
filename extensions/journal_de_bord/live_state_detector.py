"""
OGMA - Journal de Bord v2.0
Détecteur d'états EN LIVE pendant les conversations

Fonctionnalités :
- Analyse des messages utilisateur/IA en temps réel
- Détection de nouveaux états actifs
- Détection de résolution d'états existants
- Mise à jour automatique sans interruption conversation

Pattern : Hook appelé après chaque échange
"""

import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple


class LiveStateDetector:
    """Détecteur d'états actifs en temps réel pendant conversations"""
    
    def __init__(self, json_manager, archiviste_controller):
        """
        Initialise le détecteur live
        
        Args:
            json_manager: Instance JSONManager pour accès états actifs
            archiviste_controller: Contrôleur LLM pour analyse contextuelle
        """
        self.json_manager = json_manager
        self.archiviste = archiviste_controller
        
        # Patterns de détection rapide (pré-filtrage avant LLM)
        self.creation_patterns = {
            "santé": [
                r"(?:je suis|j'ai|tombé)\s+malade",
                r"(?:grippe|fièvre|mal de|douleur|rhume|sinusite)",
                r"(?:médecin|docteur|rendez-vous medical)",
                r"(?:symptômes|diagnostic|traitement)",
                r"(?:enceinte|grossesse|gestation|trimestre|accouchement)"  # Gestation
            ],
            "projet": [
                r"(?:je commence|je démarre|nouveau projet)",
                r"(?:développer|créer|construire|implémenter)",
                r"(?:projet en cours|travail sur)",
                r"(?:deadline|échéance|livraison)",
                r"(?:jour \d+|semaine \d+)"  # Suivi temporel projet/gestation
            ],
            "apprentissage": [
                r"(?:apprendre|étudier|formation)",
                r"(?:cours|tuto|documentation)",
                r"(?:comprendre|maîtriser)",
                r"(?:certification|examen)"
            ],
            "humeur": [
                r"(?:stressé|anxieux|inquiet)",
                r"(?:fatigué|épuisé|burnout)",
                r"(?:motivé|excité|enthousiaste)",
                r"(?:déprimé|triste|moral bas)"
            ]
        }
        
        self.resolution_patterns = [
            # Terminaison explicite
            r"(?:c'est terminé|c'est fini|résolu|réglé|voilà|ça y est)",
            r"(?:complété|achevé|livré|terminé|enfin fini|bouclé)",
            
            # Négation d'état ("je ne suis plus X")
            r"(?:plus de|fini avec|en ai fini)",
            r"(?:ne .{0,20}plus|n'ai plus|n'est plus|ne suis plus)",
            r"(?:plus jamais|jamais plus|c'est passé)",
            
            # Guérison/Amélioration
            r"(?:guéri|rétabli|soigné|remis)",
            r"(?:va mieux|vais mieux|ça va mieux|se passe mieux)",
            r"(?:ça s'est arrangé|ça s'arrange|s'est amélioré)",
            
            # Abandon/Arrêt
            r"(?:annulé|abandonné|laissé tomber|j'arrête|j'abandonne)",
            r"(?:je laisse tomber|on oublie|tant pis)",
            
            # Réussite/Succès
            r"(?:j'ai eu|j'ai obtenu|j'ai réussi|j'ai passé|j'ai fini)",
            r"(?:c'est fait|c'est bon|tout bon|c'est ok|nickel)",
            r"(?:succès|réussite|obtenu|validé|diplômé|certifié)",
            r"(?:mission accomplie|objectif atteint|but atteint)",
            
            # Remplacement d'état (humeur qui change)
            r"(?:maintenant je suis|désormais je me sens|je suis devenu)"
        ]
        
        # Types d'états : TEMPORAIRE (résolvable) vs DURABLE (évolue mais ne se résout pas)
        self.state_types = {
            "temporaire": ["santé", "projet", "apprentissage", "technique"],  # Peuvent être résolus
            "durable": ["humeur", "personnel", "identité", "relation"]  # Évoluent/se remplacent
        }
        
        # Catégories qui se REMPLACENT au lieu de se RÉSOUDRE
        self.replaceable_categories = ["humeur", "personnel"]
        
        self.update_patterns = [
            r"(?:en fait|correction|erreur|plutôt)",  # Corrections
            r"(?:jour \d+|\d+(?:eme|ème|e)?\s*jour)",  # "jour 8" ou "8eme jour" ou "8e jour"
            r"(?:semaine \d+|\d+(?:eme|ème|e)?\s*semaine)",  # Idem semaines
            r"(?:mois \d+|\d+(?:eme|ème|e)?\s*mois)",  # Idem mois
            r"(?:\d+\s*(?:sur|/)\s*\d+)",              # "8 sur 9" ou "8/9" (progression X/Y)
            r"(?:avancement|progression|évolution)",   # Updates état
            r"(?:maintenant|désormais|actuellement)",  # Changement statut
            r"(?:on en est|tu en es|j'en suis)"        # Expressions de progression
        ]
        
        print("[LIVE-DETECTOR] Initialisé")
    
    async def analyze_message_pair(
        self, 
        user_message: str, 
        ai_response: str,
        conversation_context: List[Dict[str, str]] = None,
        conversation_id: str = None
    ) -> Dict[str, Any]:
        """
        Analyse une paire message utilisateur + réponse IA pour détecter changements d'états
        
        Args:
            user_message: Message de l'utilisateur
            ai_response: Réponse de l'IA
            conversation_context: Historique conversation pour contexte (optionnel)
            conversation_id: ID conversation pour traçabilité (optionnel)
        
        Returns:
            Dict: {
                "new_states": [...],      # Nouveaux états détectés
                "resolved_states": [...], # États résolus
                "updated_states": [...]   # États mis à jour
            }
        """
        try:
            print(f"[LIVE-DETECTOR] 🔍 Analyse message pair...")
            
            result = {
                "new_states": [],
                "resolved_states": [],
                "updated_states": []
            }
            
            # 1. Pré-filtrage rapide (patterns regex)
            quick_scan = self._quick_pattern_scan(user_message)
            
            if not quick_scan["has_potential"]:
                print("[LIVE-DETECTOR] ⚪ Pas de pattern détecté - skip analyse LLM")
                return result
            
            hints = []
            if quick_scan['categories']:
                hints.append(f"Catégories: {', '.join(quick_scan['categories'])}")
            if quick_scan['has_resolution']:
                hints.append("Résolution détectée")
            if quick_scan['has_update']:
                hints.append("Mise à jour détectée")
            
            print(f"[LIVE-DETECTOR] 🎯 Patterns: {' | '.join(hints)}")
            
            # 2. Analyse LLM contextuelle (validation + extraction)
            llm_analysis = await self._llm_deep_analysis(
                user_message, 
                ai_response,
                quick_scan,  # Passer tout le scan, pas juste categories
                conversation_context
            )
            
            if not llm_analysis:
                return result
            
            # 3. Détection nouveaux états
            if llm_analysis.get("new_states"):
                for state_data in llm_analysis["new_states"]:
                    # Enrichir avec infos conversation
                    state_data["conversation_id"] = conversation_id
                    state_data["user_message"] = user_message[:200]  # Extrait
                    new_state_id = self._create_state_from_llm(state_data)
                    if new_state_id:
                        # Retourner un dict pour l'affichage UI/Logs
                        result["new_states"].append({
                            "id": new_state_id,
                            "description": state_data["description"],
                            "category": state_data["category"]
                        })
                        print(f"[LIVE-DETECTOR] ✨ NOUVEAU: {state_data['description'][:50]}...")
            
            # 4. Détection résolutions
            if llm_analysis.get("resolved_state_ids"):
                current_states = self.json_manager.get_active_states()
                for state_id in llm_analysis["resolved_state_ids"]:
                    resolved = self._resolve_state(state_id, llm_analysis.get("resolution_note"))
                    if resolved:
                        result["resolved_states"].append(state_id)
                        print(f"[LIVE-DETECTOR] ✅ RÉSOLU: État #{state_id}")
            
            # 5. Détection mises à jour
            if llm_analysis.get("updated_states"):
                for update_data in llm_analysis["updated_states"]:
                    updated = self._update_state(update_data)
                    if updated:
                        result["updated_states"].append(update_data["state_id"])
                        print(f"[LIVE-DETECTOR] 🔄 MÀJ: État #{update_data['state_id']}")
            
            return result
            
        except Exception as e:
            print(f"[LIVE-DETECTOR] ERROR Analyse: {e}")
            import traceback
            traceback.print_exc()
            return {"new_states": [], "resolved_states": [], "updated_states": []}
    
    def _quick_pattern_scan(self, text: str) -> Dict[str, Any]:
        """
        Scan rapide par patterns regex pour pré-filtrage
        
        Returns:
            Dict: {"has_potential": bool, "categories": List[str], "has_resolution": bool, "has_update": bool}
        """
        text_lower = text.lower()
        detected_categories = []
        
        # Scan création
        for category, patterns in self.creation_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    detected_categories.append(category)
                    break
        
        # Scan résolution
        has_resolution = any(re.search(p, text_lower) for p in self.resolution_patterns)
        
        # Scan mise à jour
        has_update = any(re.search(p, text_lower) for p in self.update_patterns)
        
        return {
            "has_potential": len(detected_categories) > 0 or has_resolution or has_update,
            "categories": detected_categories,
            "has_resolution": has_resolution,
            "has_update": has_update
        }
    
    async def _llm_deep_analysis(
        self, 
        user_message: str, 
        ai_response: str,
        quick_scan: Dict[str, Any],  # Changé de hint_categories à quick_scan
        conversation_context: List[Dict[str, str]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Analyse LLM contextuelle pour validation et extraction précise
        
        Returns:
            Dict: {
                "new_states": [{"category": str, "description": str, "importance": str}],
                "resolved_state_ids": [int],
                "updated_states": [{"state_id": int, "update_note": str}]
            }
        """
        try:
            # Récupérer états actifs actuels pour contexte
            current_states = self.json_manager.get_active_states()
            unresolved = [s for s in current_states.get("states", []) if not s.get("resolved", False)]
            
            # Construction hints depuis quick_scan
            hint_categories = quick_scan.get("categories", [])
            has_resolution = quick_scan.get("has_resolution", False)
            has_update = quick_scan.get("has_update", False)
            
            # Construction prompt
            states_context = "\n".join([
                f"- État #{s['state_id']} ({s['category']}): {s['description']}"
                for s in unresolved
            ]) if unresolved else "Aucun état actif actuellement"
            
            conv_context = ""
            if conversation_context:
                last_3 = conversation_context[-3:] if len(conversation_context) > 3 else conversation_context
                conv_context = "\n".join([
                    f"{'User' if m['role'] == 'user' else 'AI'}: {m['content'][:100]}..."
                    for m in last_3
                ])
            
            # Construire checklist pour états existants
            states_checklist = ""
            if unresolved:
                states_checklist = "CHECKLIST ÉTATS ACTIFS - Vérifie CHAQUE état un par un:\n"
                for s in unresolved:
                    category = s['category']
                    state_type = "TEMPORAIRE (peut être résolu)" if category in self.state_types.get("temporaire", []) else "DURABLE (évolue/se remplace)"
                    states_checklist += f"  □ État #{s['state_id']} ({category}, {state_type}): {s['description'][:80]}...\n"
                states_checklist += "\n"
            
            prompt = f"""Tu es un analyseur d'états actifs. Analyse ce message et détermine les changements d'états.

{states_checklist}CONTEXTE CONVERSATION:
{conv_context}

MESSAGE UTILISATEUR: "{user_message}"
RÉPONSE IA: "{ai_response}"

PRÉ-SCAN: Catégories={", ".join(hint_categories) if hint_categories else "aucune"} | Résolution={"OUI" if has_resolution else "non"} | MàJ={"OUI" if has_update else "non"}

═══════════════════════════════════════════════════════════════
RÈGLES DE RÉSOLUTION:

ÉTATS TEMPORAIRES (santé, projet, apprentissage, technique):
✅ SE RÉSOLVENT quand: terminé, guéri, réussi, abandonné, annulé
   Exemples: "c'est fini", "je vais mieux", "j'ai réussi", "j'abandonne"

ÉTATS DURABLES (humeur, personnel, relation):
✅ NE SE RÉSOLVENT PAS - ils se REMPLACENT par un nouvel état
   Exemple: "excitée" → "calme" = ancien état résolu + nouvel état créé
═══════════════════════════════════════════════════════════════

INSTRUCTIONS:
1. Pour CHAQUE état listé ci-dessus, vérifie si le message indique sa résolution ou évolution
2. Détecte les NOUVEAUX états (durée >1 jour, impact quotidien)
3. IMPORTANT: Ne crée PAS de doublon si un état similaire existe déjà

RÉPONDS EN JSON STRICT:
{{
  "state_analysis": [
    {{
      "state_id": 1,
      "verdict": "unchanged|resolved|updated",
      "reason": "explication courte"
    }}
  ],
  "new_states": [
    {{
      "category": "santé|projet|apprentissage|humeur|technique|personnel",
      "description": "Description courte",
      "importance": "high|medium|low",
      "reasoning": "Pourquoi nouvel état"
    }}
  ],
  "resolved_state_ids": [1, 3],
  "resolution_note": "Note résolution",
  "updated_states": [
    {{
      "state_id": 2,
      "new_description": "Nouvelle description",
      "update_note": "Changement"
    }}
  ]
}}

Si rien ne change: {{"state_analysis": [], "new_states": [], "resolved_state_ids": [], "updated_states": []}}
"""
            
            # Debug type archiviste
            print(f"[LIVE-DETECTOR-DEBUG] Type archiviste: {type(self.archiviste)}")
            print(f"[LIVE-DETECTOR-DEBUG] Has call_chat_api: {hasattr(self.archiviste, 'call_chat_api')}")
            
            # Appel LLM via call_chat_api (API AIController standard)
            response, error = await self.archiviste.call_chat_api(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,  # Précis pour détection
                max_tokens=500,
                context_length=4096,
                is_json=False
            )
            
            if error or not response:
                print(f"[LIVE-DETECTOR] ERROR LLM call: {error}")
                return None
            
            # Parsing JSON
            import json
            import re
            response_text = response.strip()
            
            # Nettoyage markdown si présent
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            # Nettoyage caractères de contrôle (sauf \n, \r, \t)
            response_text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', response_text)
            
            analysis = json.loads(response_text)
            
            print(f"[LIVE-DETECTOR] LLM: {len(analysis.get('new_states', []))} nouveaux, "
                  f"{len(analysis.get('resolved_state_ids', []))} résolus")
            
            return analysis
            
        except Exception as e:
            print(f"[LIVE-DETECTOR] ERROR Analyse LLM: {e}")
            return None
    
    def _create_state_from_llm(self, state_data: Dict[str, Any]) -> Optional[int]:
        """Crée un nouvel état actif depuis données LLM"""
        try:
            # Construction données enrichies
            enriched_data = {
                "description": state_data["description"],
                "importance": state_data.get("importance", "medium"),
                "source_entry_id": state_data.get("conversation_id", "live_detection"),
                # Option B: Stocker contexte conversation
                "source_context": {
                    "conversation_id": state_data.get("conversation_id"),
                    "user_message": state_data.get("user_message", ""),
                    "ai_response": state_data.get("ai_response", ""),
                    "detection_method": "llm_analysis",
                    "reasoning": state_data.get("reasoning", "")
                }
            }
            
            state_id = self.json_manager.create_active_state(
                category=state_data["category"],
                new_state=enriched_data
            )
            return state_id
        except Exception as e:
            print(f"[LIVE-DETECTOR] ERROR Création état: {e}")
            return None
    
    def _resolve_state(self, state_id: int, note: str = None) -> bool:
        """Résout un état actif existant"""
        try:
            return self.json_manager.resolve_state(
                state_id=state_id,
                resolution_note=note or "Résolu automatiquement (détection live)"
            )
        except Exception as e:
            print(f"[LIVE-DETECTOR] ERROR Résolution état: {e}")
            return False
    
    def _update_state(self, update_data: Dict[str, Any]) -> bool:
        """Met à jour un état actif existant (description et/ou note)"""
        try:
            state_id = update_data["state_id"]
            new_description = update_data.get("new_description")
            update_note = update_data.get("update_note", "Mise à jour (détection live)")
            
            result = self.json_manager.modify_active_state(
                state_id=state_id,
                update_note=update_note,
                new_description=new_description
            )
            
            if result and new_description:
                print(f"[LIVE-DETECTOR] 📝 MODIFIÉ: État #{state_id} → {new_description[:50]}...")
            elif result:
                print(f"[LIVE-DETECTOR] 📝 NOTE AJOUTÉE: État #{state_id}")
            
            return result
        except Exception as e:
            print(f"[LIVE-DETECTOR] ERROR MàJ état: {e}")
            return False


# Singleton instance
_live_detector_instance: Optional[LiveStateDetector] = None


def initialize_live_detector(json_manager, archiviste_controller) -> Optional[LiveStateDetector]:
    """
    Initialise le détecteur live (pattern singleton)
    
    Args:
        json_manager: Instance JournalJSONManager
        archiviste_controller: Contrôleur LLM Archiviste
    
    Returns:
        Instance LiveStateDetector ou None si erreur
    """
    global _live_detector_instance
    
    try:
        if _live_detector_instance is None:
            _live_detector_instance = LiveStateDetector(
                json_manager=json_manager,
                archiviste_controller=archiviste_controller
            )
            print("[LIVE-DETECTOR] ✅ Instance singleton créée")
        
        return _live_detector_instance
    
    except Exception as e:
        print(f"[LIVE-DETECTOR] ERROR Initialisation: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_live_detector() -> Optional[LiveStateDetector]:
    """Retourne l'instance singleton LiveStateDetector"""
    return _live_detector_instance
