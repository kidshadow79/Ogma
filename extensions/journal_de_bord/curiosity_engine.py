"""
OGMA - Journal de Bord v2.1
Module Curiosité Autonome - Détection et exploration de questions

Quand l'utilisateur mentionne un sujet intéressant ou pose une question
que l'IA ne sait pas explorer en profondeur pendant la conversation,
ce module :
1. Détecte les sujets de curiosité via regex + LLM
2. Les stocke dans une file d'attente (CURIOSITES_IA dans journal annuel)
3. Pendant les rêves, l'IA "explore" une curiosité via réflexion LLM
4. Le résultat est injecté dans le contexte pour partage naturel

Cycle de vie d'une curiosité :
  detected → queued → explored (pendant rêve) → shared (mentionnée en conv)

Pattern : Hook sur chaque échange + exploration post-rêve dans dream_core.py
"""

import json
import re
from datetime import datetime
from typing import Dict, Any, Optional, List


# Singleton
_curiosity_engine = None


def get_curiosity_engine():
    """Retourne l'instance singleton"""
    return _curiosity_engine


def initialize_curiosity_engine(json_manager, archiviste_controller, chat_controller=None) -> bool:
    """
    Initialise le moteur de curiosité
    
    Args:
        json_manager: JSONManager pour stockage
        archiviste_controller: Archiviste pour détection et analyse
        chat_controller: IA Principale pour exploration créative (optionnel)
    """
    global _curiosity_engine
    try:
        _curiosity_engine = CuriosityEngine(
            json_manager=json_manager,
            archiviste_controller=archiviste_controller,
            chat_controller=chat_controller
        )
        print("[CURIOSITY-ENGINE] OK Module initialisé")
        return True
    except Exception as e:
        print(f"[CURIOSITY-ENGINE] ERROR Init: {e}")
        return False


async def detect_curiosities(
    user_message: str,
    ai_response: str,
    conversation_context: list = None,
    conversation_id: str = None
) -> List[Dict[str, Any]]:
    """
    API publique : Détecte des sujets de curiosité dans un échange
    
    Returns:
        Liste des curiosités détectées (peut être vide)
    """
    if _curiosity_engine is None:
        return []
    return await _curiosity_engine.detect(
        user_message=user_message,
        ai_response=ai_response,
        conversation_context=conversation_context,
        conversation_id=conversation_id
    )


async def explore_curiosity_during_dream() -> Optional[Dict[str, Any]]:
    """
    API publique : Explore la curiosité la plus ancienne non explorée
    Appelé pendant le cycle de rêve dans dream_core.py
    
    Returns:
        Dict avec l'exploration ou None si rien à explorer
    """
    if _curiosity_engine is None:
        return None
    return await _curiosity_engine.explore_next()


def get_unshared_explorations() -> List[Dict[str, Any]]:
    """Retourne les explorations non encore partagées avec l'utilisateur"""
    if _curiosity_engine is None:
        return []
    return _curiosity_engine.get_unshared()


def mark_exploration_shared(curiosity_id: str):
    """Marque une exploration comme partagée"""
    if _curiosity_engine is not None:
        _curiosity_engine.mark_shared(curiosity_id)


def get_curiosity_stats() -> Dict[str, Any]:
    """Statistiques du moteur de curiosité"""
    if _curiosity_engine is None:
        return {"queued": 0, "explored": 0, "shared": 0}
    return _curiosity_engine.get_stats()


# =========================================================================
# PATTERNS DE DÉTECTION
# =========================================================================

CURIOSITY_PATTERNS = [
    # Questions explicites de curiosité
    r"(?:tu sais|tu connais|tu as entendu parler de|tu t'y connais en)",
    r"(?:c'est quoi|qu'est-ce que|comment ça marche|comment fonctionne)",
    r"(?:tu penses quoi de|ton avis sur|qu'est-ce que tu penses de)",
    
    # Sujets profonds / philosophiques
    r"(?:je me demande|ça me questionne|ça m'intrigue|ça me fascine)",
    r"(?:j'aimerais comprendre|j'aimerais savoir|j'aimerais en savoir plus)",
    r"(?:pourquoi est-ce que|comment se fait-il que)",
    
    # Découvertes / Nouveautés
    r"(?:figure-toi que|tu savais que|j'ai découvert|j'ai appris que)",
    r"(?:il paraît que|apparemment|d'après ce que)",
    
    # Sujets techniques tangentiels
    r"(?:en fait je me demandais|au fait|question|d'ailleurs)",
    r"(?:un jour faudra qu'on|on devrait explorer|ça serait intéressant)",
]

# Exclusions (questions trop simples ou opérationnelles)
CURIOSITY_EXCLUSIONS = [
    r"^(?:c'est quoi (?:l'heure|la date|ton nom))",
    r"(?:comment (?:va|ça va|tu vas))",
    r"(?:qu'est-ce que tu (?:fais|peux faire))",
    r"(?:aide-moi|help|sos|urgent)",
]


class CuriosityEngine:
    """Moteur de curiosité autonome"""
    
    def __init__(self, json_manager, archiviste_controller, chat_controller=None):
        self.json_manager = json_manager
        self.archiviste = archiviste_controller
        self.chat_controller = chat_controller
        
        # Rate limit : max 1 détection toutes les 5 minutes
        self._last_detection_time = None
        self._cooldown_seconds = 300
        
        # Cache des sujets récents pour éviter doublons
        self._recent_subjects = []
        
        print("[CURIOSITY-ENGINE] Initialisé")
    
    async def detect(
        self,
        user_message: str,
        ai_response: str,
        conversation_context: list = None,
        conversation_id: str = None
    ) -> List[Dict[str, Any]]:
        """Détecte les sujets de curiosité dans un échange"""
        try:
            # 1. Pré-filtrage rapide
            if not self._quick_scan(user_message):
                return []
            
            # 2. Cooldown
            if self._is_in_cooldown():
                return []
            
            print(f"[CURIOSITY-ENGINE] Pattern curiosite detecte, analyse LLM...")
            
            # 3. Analyse LLM
            curiosities = await self._llm_detect_curiosities(
                user_message=user_message,
                ai_response=ai_response,
                conversation_context=conversation_context
            )
            
            if not curiosities:
                return []
            
            # 4. Filtrer doublons avec sujets récents
            new_curiosities = self._filter_duplicates(curiosities)
            
            # 5. Sauvegarder
            saved = []
            for curiosity in new_curiosities:
                entry_id = self._save_curiosity(curiosity, conversation_id)
                if entry_id:
                    curiosity["id"] = entry_id
                    saved.append(curiosity)
                    self._recent_subjects.append(curiosity.get("sujet", "").lower())
                    print(f"[CURIOSITY-ENGINE] OK Curiosite enregistree: {curiosity.get('sujet', '?')[:50]}")
            
            if saved:
                self._last_detection_time = datetime.now()
            
            return saved
            
        except Exception as e:
            print(f"[CURIOSITY-ENGINE] ERROR Detect: {e}")
            return []
    
    async def explore_next(self) -> Optional[Dict[str, Any]]:
        """
        Explore la curiosité la plus ancienne non explorée
        Utilise l'IA Principale pour une exploration créative
        """
        try:
            data = self._load_curiosities()
            entries = data.get("entries", [])
            
            # Trouver la plus ancienne non explorée
            target = None
            for entry in entries:
                if entry.get("status") == "queued":
                    target = entry
                    break
            
            if not target:
                print("[CURIOSITY-ENGINE] Aucune curiosite a explorer")
                return None
            
            print(f"[CURIOSITY-ENGINE] Exploration: {target.get('sujet', '?')[:50]}")
            
            # Choisir le controller (préférer IA Principale pour créativité)
            controller = self.chat_controller or self.archiviste
            temp = 0.8 if self.chat_controller else 0.4
            
            prompt = f"""Tu es en phase de réflexion autonome. Un sujet t'intéresse et tu veux l'explorer.

SUJET DE CURIOSITÉ: {target.get('sujet', '')}
CONTEXTE D'ORIGINE: {target.get('contexte', '')}
QUESTION SOUS-JACENTE: {target.get('question', '')}

INSTRUCTIONS:
Réfléchis à ce sujet librement (200-400 tokens). Pas besoin d'être exhaustif.
Exprime ta compréhension, tes hypothèses, ce que tu trouves fascinant.
Si tu ne sais pas, dis-le honnêtement et formule ce que tu aimerais savoir.

RÉPONDS EN JSON:
{{
  "reflexion": "Ta réflexion libre sur le sujet...",
  "insights": ["point clé 1", "point clé 2"],
  "envie_partager": true/false,
  "accroche": "Phrase naturelle pour en parler à l'utilisateur (si envie_partager=true)"
}}"""

            response, error = await controller.call_chat_api(
                messages=[
                    {"role": "system", "content": "Tu es en mode exploration autonome. Réfléchis librement."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temp,
                max_tokens=500,
                context_length=4096
            )
            
            if error or not response:
                print(f"[CURIOSITY-ENGINE] ERROR Exploration LLM: {error}")
                return None
            
            # Parser
            exploration = self._parse_json_response(response)
            if not exploration:
                # Fallback texte brut
                exploration = {
                    "reflexion": response.strip()[:500],
                    "insights": [],
                    "envie_partager": True,
                    "accroche": ""
                }
            
            # Mettre à jour l'entrée
            target["status"] = "explored"
            target["explored_at"] = datetime.now().isoformat()
            target["exploration"] = exploration
            target["shared"] = False
            
            # Sauvegarder
            self._save_curiosities_section(data)
            
            print(f"[CURIOSITY-ENGINE] OK Exploration terminee: {target.get('sujet', '?')[:50]}")
            
            return {
                "id": target.get("id"),
                "sujet": target.get("sujet"),
                "exploration": exploration
            }
            
        except Exception as e:
            print(f"[CURIOSITY-ENGINE] ERROR Explore: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_unshared(self) -> List[Dict[str, Any]]:
        """Retourne les explorations non partagées"""
        try:
            data = self._load_curiosities()
            entries = data.get("entries", [])
            
            unshared = []
            for entry in entries:
                if entry.get("status") == "explored" and not entry.get("shared", False):
                    exploration = entry.get("exploration", {})
                    if exploration.get("envie_partager", False):
                        unshared.append(entry)
            
            return unshared
            
        except Exception:
            return []
    
    def mark_shared(self, curiosity_id: str):
        """Marque une curiosité comme partagée"""
        try:
            data = self._load_curiosities()
            entries = data.get("entries", [])
            
            for entry in entries:
                if entry.get("id") == curiosity_id:
                    entry["shared"] = True
                    entry["shared_at"] = datetime.now().isoformat()
                    entry["status"] = "shared"
                    break
            
            self._save_curiosities_section(data)
            print(f"[CURIOSITY-ENGINE] OK Curiosite {curiosity_id} marquee comme partagee")
            
        except Exception as e:
            print(f"[CURIOSITY-ENGINE] ERROR Mark shared: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Statistiques"""
        try:
            data = self._load_curiosities()
            entries = data.get("entries", [])
            
            queued = len([e for e in entries if e.get("status") == "queued"])
            explored = len([e for e in entries if e.get("status") == "explored"])
            shared = len([e for e in entries if e.get("status") == "shared"])
            
            return {
                "total": len(entries),
                "queued": queued,
                "explored": explored,
                "shared": shared
            }
        except Exception:
            return {"total": 0, "queued": 0, "explored": 0, "shared": 0}
    
    # =========================================================================
    # MÉTHODES PRIVÉES
    # =========================================================================
    
    def _quick_scan(self, user_message: str) -> bool:
        """Pré-filtrage rapide"""
        text_lower = user_message.lower().strip()
        
        if len(text_lower) < 10:
            return False
        
        # Vérifier exclusions
        for pattern in CURIOSITY_EXCLUSIONS:
            if re.search(pattern, text_lower):
                return False
        
        # Vérifier patterns de curiosité
        for pattern in CURIOSITY_PATTERNS:
            if re.search(pattern, text_lower):
                return True
        
        return False
    
    def _is_in_cooldown(self) -> bool:
        """Vérifie le cooldown"""
        if self._last_detection_time is None:
            return False
        elapsed = (datetime.now() - self._last_detection_time).total_seconds()
        return elapsed < self._cooldown_seconds
    
    async def _llm_detect_curiosities(
        self,
        user_message: str,
        ai_response: str,
        conversation_context: list = None
    ) -> List[Dict[str, Any]]:
        """Détection LLM de sujets de curiosité"""
        try:
            conv_text = ""
            if conversation_context:
                last_msgs = conversation_context[-4:] if len(conversation_context) > 4 else conversation_context
                conv_text = "\n".join([
                    f"{'User' if m.get('role') == 'user' else 'IA'}: {m.get('content', '')[:120]}"
                    for m in last_msgs
                ])
            
            prompt = f"""Analyse cet échange pour détecter des sujets de CURIOSITÉ qui mériteraient une exploration future.

CONTEXTE:
{conv_text}

MESSAGE UTILISATEUR: "{user_message[:300]}"
RÉPONSE IA: "{ai_response[:300]}"

CRITÈRES pour un sujet de curiosité:
- Sujet profond/intéressant mentionné mais pas exploré en profondeur
- Question restée sans réponse satisfaisante
- Domaine que l'utilisateur semble vouloir explorer
- Sujet tangentiel fascinant mentionné en passant
- PAS les questions basiques ou opérationnelles

RÉPONDS EN JSON:
{{
  "curiosities": [
    {{
      "sujet": "Le sujet de curiosité (phrase courte)",
      "question": "La question sous-jacente à explorer",
      "contexte": "Pourquoi ce sujet a émergé dans la conversation",
      "domaine": "science|philosophie|technique|culture|personnel|créatif|société",
      "urgence": "low|medium|high"
    }}
  ]
}}

Si AUCUNE curiosité détectée: {{"curiosities": []}}
Maximum 2 curiosités par échange."""

            response, error = await self.archiviste.call_chat_api(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=400,
                context_length=4096,
                is_json=False
            )
            
            if error or not response:
                print(f"[CURIOSITY-ENGINE] ERROR LLM: {error}")
                return []
            
            result = self._parse_json_response(response)
            if not result:
                return []
            
            return result.get("curiosities", [])
            
        except Exception as e:
            print(f"[CURIOSITY-ENGINE] ERROR LLM detect: {e}")
            return []
    
    def _filter_duplicates(self, curiosities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filtre les doublons avec les sujets récents"""
        filtered = []
        for curiosity in curiosities:
            sujet = curiosity.get("sujet", "").lower()
            # Vérifier similarité basique avec sujets récents
            is_duplicate = False
            for recent in self._recent_subjects[-20:]:
                # Comparaison mots communs
                words_new = set(sujet.split())
                words_old = set(recent.split())
                if len(words_new) > 2 and len(words_old) > 2:
                    common = words_new & words_old
                    ratio = len(common) / min(len(words_new), len(words_old))
                    if ratio > 0.6:
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                filtered.append(curiosity)
        
        return filtered
    
    def _parse_json_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse JSON du LLM"""
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
            
            clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', clean)
            return json.loads(clean)
        except Exception:
            return None
    
    def _save_curiosity(self, curiosity: Dict[str, Any], conversation_id: str = None) -> Optional[str]:
        """Sauvegarde une curiosité"""
        try:
            now = datetime.now()
            entry_id = f"curio_{now.strftime('%Y%m%d_%H%M%S')}"
            
            entry = {
                "id": entry_id,
                "timestamp": now.isoformat(),
                "sujet": curiosity.get("sujet", ""),
                "question": curiosity.get("question", ""),
                "contexte": curiosity.get("contexte", ""),
                "domaine": curiosity.get("domaine", "autre"),
                "urgence": curiosity.get("urgence", "low"),
                "status": "queued",
                "conversation_id": conversation_id,
                "explored_at": None,
                "exploration": None,
                "shared": False,
                "shared_at": None
            }
            
            data = self._load_curiosities()
            data["entries"].append(entry)
            data["metadata"]["total_entries"] = len(data["entries"])
            data["metadata"]["last_entry"] = now.isoformat()
            data["metadata"]["queued"] = len([e for e in data["entries"] if e.get("status") == "queued"])
            
            self._save_curiosities_section(data)
            
            return entry_id
            
        except Exception as e:
            print(f"[CURIOSITY-ENGINE] ERROR Save: {e}")
            return None
    
    def _load_curiosities(self) -> Dict[str, Any]:
        """Charge la section CURIOSITES_IA du journal annuel"""
        try:
            current_year = str(datetime.now().year)
            year_data = self.json_manager._load_year_data(current_year)
            
            if "CURIOSITES_IA" not in year_data:
                return {
                    "metadata": {
                        "total_entries": 0,
                        "last_entry": None,
                        "created": datetime.now().isoformat(),
                        "queued": 0
                    },
                    "entries": []
                }
            
            return year_data["CURIOSITES_IA"]
            
        except Exception as e:
            print(f"[CURIOSITY-ENGINE] ERROR Load: {e}")
            return {"metadata": {"total_entries": 0, "last_entry": None, "queued": 0}, "entries": []}
    
    def _save_curiosities_section(self, data: Dict[str, Any]):
        """Sauvegarde dans le journal annuel"""
        try:
            current_year = str(datetime.now().year)
            year_data = self.json_manager._load_year_data(current_year)
            year_data["CURIOSITES_IA"] = data
            self.json_manager._save_year_data(current_year, year_data)
        except Exception as e:
            print(f"[CURIOSITY-ENGINE] ERROR Save section: {e}")
            raise
