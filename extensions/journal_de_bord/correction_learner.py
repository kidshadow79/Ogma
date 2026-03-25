"""
OGMA - Journal de Bord v2.1
Module Apprentissage par Correction - Détection et mémorisation des corrections

Quand l'utilisateur corrige l'IA ("non c'est pas ça", "en fait c'est X pas Y"),
ce module :
1. Détecte le pattern de correction via regex (pré-filtrage rapide)
2. Valide et extrait la correction via LLM (Archiviste)
3. Sauvegarde la leçon dans la section CORRECTIONS_APPRISES du journal annuel
4. Optionnellement crée un souvenir #MEM pour ancrage mémoire à long terme

Pattern : Hook branché sur hook_message_exchange (après chaque échange)
"""

import json
import re
from datetime import datetime
from typing import Dict, Any, Optional, List


# Singleton
_correction_learner = None


def get_correction_learner():
    """Retourne l'instance singleton"""
    return _correction_learner


def initialize_correction_learner(json_manager, archiviste_controller, memory_manager=None) -> bool:
    """
    Initialise le module d'apprentissage par correction
    
    Args:
        json_manager: JSONManager pour stockage
        archiviste_controller: Archiviste pour analyse LLM
        memory_manager: MemoryManager optionnel pour ancrage mémoire
    
    Returns:
        bool: True si initialisé
    """
    global _correction_learner
    try:
        _correction_learner = CorrectionLearner(
            json_manager=json_manager,
            archiviste_controller=archiviste_controller,
            memory_manager=memory_manager
        )
        print("[CORRECTION-LEARNER] OK Module initialisé")
        return True
    except Exception as e:
        print(f"[CORRECTION-LEARNER] ERROR Init: {e}")
        return False


async def analyze_for_corrections(
    user_message: str,
    ai_response: str,
    conversation_context: list = None,
    conversation_id: str = None
) -> Optional[Dict[str, Any]]:
    """
    API publique : Analyse un échange pour détecter une correction
    
    Returns:
        Dict avec la correction détectée ou None si pas de correction
    """
    if _correction_learner is None:
        return None
    return await _correction_learner.analyze(
        user_message=user_message,
        ai_response=ai_response,
        conversation_context=conversation_context,
        conversation_id=conversation_id
    )


def get_corrections_stats() -> Dict[str, Any]:
    """Retourne les stats de corrections apprises"""
    if _correction_learner is None:
        return {"total": 0, "categories": {}}
    return _correction_learner.get_stats()


# =========================================================================
# PATTERNS DE DÉTECTION RAPIDE (pré-filtrage avant LLM)
# =========================================================================

CORRECTION_PATTERNS = [
    # Négation directe de la réponse IA
    r"(?:non|nan|nope|pas du tout|absolument pas)\s*[,.]?\s*(?:c'est|c'était|ce n'est)",
    r"(?:non|nan)\s*[,!]",
    r"(?:t'as tort|tu te trompes|tu as tort|erreur|faux|incorrect)",
    
    # Correction explicite ("en fait c'est X", "plutôt Y")
    r"(?:en fait|en réalité|pour être précis|pour être exact)",
    r"(?:plutôt|au contraire|pas exactement|pas tout à fait|pas vraiment)",
    r"(?:je voulais dire|je parlais de|ce que je veux dire)",
    r"(?:la bonne réponse|la vraie réponse|la réponse correcte)",
    
    # Redirection ("je ne parle pas de X mais de Y")
    r"(?:je ne parle pas de|je ne parlais pas de|pas de ça|c'est pas ça)",
    r"(?:pas ça que je|c'est autre chose|tu confonds|tu mélanges)",
    
    # Incompréhension signalée
    r"(?:tu n'as pas compris|tu comprends pas|tu as mal compris|mauvaise interprétation)",
    r"(?:c'est pas ce que|pas ce que j'ai dit|pas ce que je voulais)",
    
    # Précision/Correction factuelle
    r"(?:attention|attention\s*,|fais gaffe|prends garde)",
    r"(?:sauf que|le truc c'est que|mais en fait)",
    r"(?:je te corrige|petite correction|correction)",
    
    # Auto-correction utilisateur (important aussi)
    r"(?:pardon|désolé|excuse)\s*[,.]?\s*(?:je voulais|c'est|en fait)",
]

# Patterns qui EXCLUENT (faux positifs fréquents)
EXCLUSION_PATTERNS = [
    r"(?:non merci|non pas besoin|non c'est bon|non ça va)",
    r"(?:en fait\s+(?:oui|ok|merci|super|génial))",
    r"(?:plutôt bien|plutôt cool|plutôt sympa)",
]


class CorrectionLearner:
    """Détecteur et mémorisateur de corrections utilisateur"""
    
    def __init__(self, json_manager, archiviste_controller, memory_manager=None):
        self.json_manager = json_manager
        self.archiviste = archiviste_controller
        self.memory_manager = memory_manager
        
        # Cooldown anti-spam : max 1 correction toutes les 3 minutes
        self._last_correction_time = None
        self._cooldown_seconds = 180
        
        print("[CORRECTION-LEARNER] Initialisé")
    
    async def analyze(
        self,
        user_message: str,
        ai_response: str,
        conversation_context: list = None,
        conversation_id: str = None
    ) -> Optional[Dict[str, Any]]:
        """Analyse un échange pour détecter et enregistrer une correction"""
        try:
            # 1. Pré-filtrage rapide par regex
            if not self._quick_scan(user_message):
                return None
            
            # 2. Cooldown anti-spam
            if self._is_in_cooldown():
                print("[CORRECTION-LEARNER] Cooldown actif, skip")
                return None
            
            print(f"[CORRECTION-LEARNER] Pattern correction detecte, analyse LLM...")
            
            # 3. Analyse LLM pour valider et extraire
            correction = await self._llm_extract_correction(
                user_message=user_message,
                ai_response=ai_response,
                conversation_context=conversation_context
            )
            
            if not correction:
                return None
            
            # 4. Sauvegarder la correction
            entry_id = self._save_correction(correction, conversation_id)
            if entry_id:
                self._last_correction_time = datetime.now()
                print(f"[CORRECTION-LEARNER] OK Correction enregistree: {entry_id}")
                print(f"[CORRECTION-LEARNER] Lecon: {correction.get('lecon', '?')[:80]}")
                
                # 5. Optionnel : créer souvenir #MEM si correction importante
                if correction.get("importance") == "high" and self.memory_manager:
                    await self._memorize_correction(correction)
                
                return correction
            
            return None
            
        except Exception as e:
            print(f"[CORRECTION-LEARNER] ERROR: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Statistiques des corrections apprises"""
        try:
            corrections = self._load_corrections()
            entries = corrections.get("entries", [])
            
            categories = {}
            for entry in entries:
                cat = entry.get("categorie", "autre")
                categories[cat] = categories.get(cat, 0) + 1
            
            return {
                "total": len(entries),
                "categories": categories,
                "last_correction": corrections.get("metadata", {}).get("last_entry")
            }
        except Exception:
            return {"total": 0, "categories": {}}
    
    # =========================================================================
    # MÉTHODES PRIVÉES
    # =========================================================================
    
    def _quick_scan(self, user_message: str) -> bool:
        """Pré-filtrage rapide par regex"""
        text_lower = user_message.lower().strip()
        
        # Trop court pour être une correction
        if len(text_lower) < 5:
            return False
        
        # Vérifier exclusions d'abord
        for pattern in EXCLUSION_PATTERNS:
            if re.search(pattern, text_lower):
                return False
        
        # Vérifier patterns de correction
        for pattern in CORRECTION_PATTERNS:
            if re.search(pattern, text_lower):
                return True
        
        return False
    
    def _is_in_cooldown(self) -> bool:
        """Vérifie si on est encore en cooldown"""
        if self._last_correction_time is None:
            return False
        elapsed = (datetime.now() - self._last_correction_time).total_seconds()
        return elapsed < self._cooldown_seconds
    
    async def _llm_extract_correction(
        self,
        user_message: str,
        ai_response: str,
        conversation_context: list = None
    ) -> Optional[Dict[str, Any]]:
        """Extraction LLM de la correction (Archiviste, temp 0.2)"""
        try:
            # Contexte conversation récent
            conv_text = ""
            if conversation_context:
                last_msgs = conversation_context[-6:] if len(conversation_context) > 6 else conversation_context
                conv_text = "\n".join([
                    f"{'User' if m.get('role') == 'user' else 'IA'}: {m.get('content', '')[:150]}"
                    for m in last_msgs
                ])
            
            prompt = f"""Tu es un analyseur de corrections. L'utilisateur a potentiellement corrigé l'IA.

CONTEXTE CONVERSATION:
{conv_text}

DERNIÈRE RÉPONSE IA: "{ai_response[:300]}"
MESSAGE UTILISATEUR: "{user_message}"

ANALYSE:
1. Est-ce que l'utilisateur CORRIGE réellement l'IA ? (pas juste un "non merci" ou un changement de sujet)
2. Si OUI, extrais la correction précise

RÉPONDS EN JSON STRICT:
{{
  "is_correction": true/false,
  "categorie": "factuel|comportemental|comprehension|preference|technique",
  "ce_que_ia_a_dit": "Ce que l'IA a dit/fait de faux (courte phrase)",
  "ce_qui_est_correct": "La correction de l'utilisateur (courte phrase)",
  "lecon": "La leçon à retenir pour le futur (phrase claire et actionnable)",
  "importance": "low|medium|high",
  "reasoning": "Pourquoi c'est/n'est pas une correction"
}}

CATÉGORIES:
- factuel: Erreur de fait (dates, noms, chiffres, définitions)
- comportemental: L'IA a eu un comportement inapproprié (ton, approche, trop/pas assez)
- comprehension: L'IA n'a pas compris la demande
- preference: L'utilisateur exprime une préférence personnelle ("je préfère X")
- technique: Erreur technique (code, config, architecture)

Si ce n'est PAS une correction: {{"is_correction": false, "reasoning": "explication"}}"""

            response, error = await self.archiviste.call_chat_api(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=400,
                context_length=4096,
                is_json=False
            )
            
            if error or not response:
                print(f"[CORRECTION-LEARNER] ERROR LLM: {error}")
                return None
            
            # Parser JSON
            result = self._parse_json_response(response)
            if not result:
                return None
            
            if not result.get("is_correction", False):
                print(f"[CORRECTION-LEARNER] Pas une correction: {result.get('reasoning', '?')[:60]}")
                return None
            
            return result
            
        except Exception as e:
            print(f"[CORRECTION-LEARNER] ERROR LLM extract: {e}")
            return None
    
    def _parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse une réponse JSON du LLM"""
        try:
            clean = response.strip()
            if "```json" in clean:
                start = clean.index("```json") + 7
                end = clean.index("```", start)
                clean = clean[start:end].strip()
            elif "```" in clean:
                start = clean.index("```") + 3
                end = clean.index("```", start)
                clean = clean[start:end].strip()
            
            # Nettoyage caractères de contrôle
            clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', clean)
            
            return json.loads(clean)
        except Exception as e:
            print(f"[CORRECTION-LEARNER] ERROR Parse JSON: {e}")
            return None
    
    def _save_correction(self, correction: Dict[str, Any], conversation_id: str = None) -> Optional[str]:
        """Sauvegarde la correction dans CORRECTIONS_APPRISES du journal annuel"""
        try:
            now = datetime.now()
            entry_id = f"corr_{now.strftime('%Y%m%d_%H%M%S')}"
            
            entry = {
                "id": entry_id,
                "timestamp": now.isoformat(),
                "categorie": correction.get("categorie", "autre"),
                "ce_que_ia_a_dit": correction.get("ce_que_ia_a_dit", ""),
                "ce_qui_est_correct": correction.get("ce_qui_est_correct", ""),
                "lecon": correction.get("lecon", ""),
                "importance": correction.get("importance", "medium"),
                "conversation_id": conversation_id,
                "applied": False  # Sera True quand la leçon a été utilisée dans une réponse
            }
            
            # Charger section
            corrections = self._load_corrections()
            corrections["entries"].append(entry)
            corrections["metadata"]["total_entries"] = len(corrections["entries"])
            corrections["metadata"]["last_entry"] = now.isoformat()
            
            # Incrémenter compteur par catégorie
            cat = correction.get("categorie", "autre")
            cat_counts = corrections["metadata"].get("by_category", {})
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
            corrections["metadata"]["by_category"] = cat_counts
            
            # Sauvegarder
            self._save_corrections_section(corrections)
            
            return entry_id
            
        except Exception as e:
            print(f"[CORRECTION-LEARNER] ERROR Save: {e}")
            return None
    
    async def _memorize_correction(self, correction: Dict[str, Any]):
        """Crée un souvenir #MEM pour les corrections importantes"""
        try:
            lecon = correction.get("lecon", "")
            categorie = correction.get("categorie", "")
            
            memory_text = (
                f"[CORRECTION APPRISE - {categorie.upper()}] "
                f"L'utilisateur m'a corrigee: {correction.get('ce_que_ia_a_dit', '')}. "
                f"La bonne reponse: {correction.get('ce_qui_est_correct', '')}. "
                f"Lecon: {lecon}"
            )
            
            memory_id = f"correction_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            success = await self.memory_manager.add_memory(
                memory_id=memory_id,
                text_brut=memory_text
            )
            
            if success:
                print(f"[CORRECTION-LEARNER] OK Correction memorisee en #MEM: {memory_id}")
            else:
                print(f"[CORRECTION-LEARNER] WARN Memorisation echouee (non bloquant)")
                
        except Exception as e:
            print(f"[CORRECTION-LEARNER] ERROR Memorisation: {e}")
    
    def _load_corrections(self) -> Dict[str, Any]:
        """Charge la section CORRECTIONS_APPRISES du journal annuel"""
        try:
            current_year = str(datetime.now().year)
            year_data = self.json_manager._load_year_data(current_year)
            
            if "CORRECTIONS_APPRISES" not in year_data:
                return {
                    "metadata": {
                        "total_entries": 0,
                        "last_entry": None,
                        "created": datetime.now().isoformat(),
                        "by_category": {}
                    },
                    "entries": []
                }
            
            return year_data["CORRECTIONS_APPRISES"]
            
        except Exception as e:
            print(f"[CORRECTION-LEARNER] ERROR Load: {e}")
            return {"metadata": {"total_entries": 0, "last_entry": None, "by_category": {}}, "entries": []}
    
    def _save_corrections_section(self, corrections: Dict[str, Any]):
        """Sauvegarde la section CORRECTIONS_APPRISES dans le journal annuel"""
        try:
            current_year = str(datetime.now().year)
            year_data = self.json_manager._load_year_data(current_year)
            year_data["CORRECTIONS_APPRISES"] = corrections
            self.json_manager._save_year_data(current_year, year_data)
        except Exception as e:
            print(f"[CORRECTION-LEARNER] ERROR Save section: {e}")
            raise


def get_recent_corrections(max_count: int = 5) -> List[Dict[str, Any]]:
    """
    Retourne les N dernières corrections pour injection contexte
    
    Utilisable par le context_provider pour rappeler les leçons récentes à l'IA
    """
    if _correction_learner is None:
        return []
    
    try:
        corrections = _correction_learner._load_corrections()
        entries = corrections.get("entries", [])
        if not entries:
            return []
        
        # Les plus récentes en premier
        recent = sorted(entries, key=lambda x: x.get("timestamp", ""), reverse=True)
        return recent[:max_count]
        
    except Exception:
        return []
