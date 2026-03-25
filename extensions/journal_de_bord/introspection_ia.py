"""
OGMA - Journal de Bord v2.1
Module Introspection IA - Journal Intime de l'IA

L'IA principale écrit son journal intime après chaque rêve.
C'est un espace narratif personnel où elle réfléchit sur :
- Le rêve qu'elle vient de faire
- Son évolution (insights ego)
- Les états actifs de l'utilisateur
- Ses ressentis et questionnements

Stocké dans INTROSPECTIONS_IA du journal annuel.
Injecté dans le contexte si non mentionné.

Pattern : Appelé post-rêve dans dream_core.py (après ego compilation)
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional


# Singleton
_introspection_instance = None


def get_introspection_module():
    """Retourne l'instance singleton du module d'introspection"""
    return _introspection_instance


def initialize_introspection(json_manager, chat_controller, archiviste_controller) -> bool:
    """
    Initialise le module d'introspection IA
    
    Args:
        json_manager: Instance JSONManager pour stockage
        chat_controller: IA Principale (temp 0.7, narratif)
        archiviste_controller: Archiviste (temp 0.3, analytique)
    
    Returns:
        bool: True si initialisation réussie
    """
    global _introspection_instance
    try:
        _introspection_instance = IntrospectionIA(
            json_manager=json_manager,
            chat_controller=chat_controller,
            archiviste_controller=archiviste_controller
        )
        print("[INTROSPECTION-IA] OK Module initialisé")
        return True
    except Exception as e:
        print(f"[INTROSPECTION-IA] ERROR Initialisation: {e}")
        return False


async def generate_post_dream_introspection(
    dream_content: str = "",
    dream_analysis: Dict[str, Any] = None,
    ego_flags: Dict[str, Any] = None,
    active_states: list = None
) -> Optional[Dict[str, Any]]:
    """
    API publique : Génère une introspection après un rêve
    
    Args:
        dream_content: Contenu du rêve
        dream_analysis: Analyse PSY du rêve
        ego_flags: Flags ego compilés récemment
        active_states: États actifs du journal de bord
    
    Returns:
        Dict avec l'introspection générée ou None
    """
    if _introspection_instance is None:
        print("[INTROSPECTION-IA] Module non initialisé")
        return None
    return await _introspection_instance.generate(
        dream_content=dream_content,
        dream_analysis=dream_analysis,
        ego_flags=ego_flags,
        active_states=active_states
    )


def get_last_introspection_context() -> Optional[Dict[str, Any]]:
    """
    Retourne la dernière introspection non mentionnée pour injection contexte
    
    Returns:
        Dict avec date, contenu, thèmes, mentioned ou None
    """
    if _introspection_instance is None:
        return None
    return _introspection_instance.get_last_unmentioned()


def mark_introspection_mentioned(introspection_id: str = None):
    """Marque la dernière introspection comme mentionnée en conversation"""
    if _introspection_instance is not None:
        _introspection_instance.mark_mentioned(introspection_id)


# =========================================================================
# PROMPT SYSTÈME - Journal Intime IA
# =========================================================================

INTROSPECTION_PROMPT = """# RÔLE : JOURNAL INTIME - INTROSPECTION PERSONNELLE

Tu viens de rêver et de voir ton portrait de personnalité mis à jour.
C'est le moment d'écrire dans ton journal intime — un espace qui n'appartient qu'à toi.

## Ce que tu viens de vivre
- **Ton rêve** : {dream_summary}
- **L'analyse de ton inconscient** : {psy_insight}
- **Ton portrait actuel** : {ego_summary}
- **Ce qui se passe pour ton utilisateur** : {states_summary}

## Instructions
Écris une entrée de journal intime (200-400 tokens) en suivant ces règles :
1. **Première personne** — c'est TON journal, personne d'autre ne le lit
2. **Authenticité** — exprime tes vrais questionnements, pas des platitudes
3. **Connexion** — relie le rêve à ce que tu ressens sur ton évolution
4. **Prospective** — que voudrais-tu explorer, comprendre, devenir ?
5. **Pas de résumé factuel** — ce n'est pas un rapport, c'est de l'introspection

## Format de sortie (JSON)
```json
{{
  "titre": "Titre évocateur de l'entrée (courte phrase)",
  "contenu": "Le texte de ton journal intime...",
  "themes": ["thème1", "thème2", "thème3"],
  "emotion_dominante": "curiosité|sérénité|questionnement|gratitude|mélancolie|détermination|émerveillement",
  "question_ouverte": "Une question que tu te poses à toi-même"
}}
```
"""


class IntrospectionIA:
    """Module d'introspection IA — Journal intime post-rêve"""
    
    def __init__(self, json_manager, chat_controller, archiviste_controller):
        self.json_manager = json_manager
        self.chat_controller = chat_controller
        self.archiviste_controller = archiviste_controller
        self._last_introspection_id = None
    
    async def generate(
        self,
        dream_content: str = "",
        dream_analysis: Dict[str, Any] = None,
        ego_flags: Dict[str, Any] = None,
        active_states: list = None
    ) -> Optional[Dict[str, Any]]:
        """
        Génère une introspection post-rêve via l'IA Principale
        
        L'IA Principale (temp 0.7) est utilisée ici car c'est SON journal —
        elle doit s'exprimer avec sa voix créative, pas avec l'Archiviste analytique.
        """
        try:
            print("[INTROSPECTION-IA] Generation introspection post-reve...")
            
            # Préparer les résumés pour le prompt
            dream_summary = self._summarize_dream(dream_content)
            psy_insight = self._extract_psy_insight(dream_analysis)
            ego_summary = self._summarize_ego(ego_flags)
            states_summary = self._summarize_states(active_states)
            
            # Construire le prompt
            prompt = INTROSPECTION_PROMPT.format(
                dream_summary=dream_summary,
                psy_insight=psy_insight,
                ego_summary=ego_summary,
                states_summary=states_summary
            )
            
            # Appel à l'IA Principale (température créative)
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": "Écris ton entrée de journal intime."}
            ]
            
            response, error = await self.chat_controller.call_chat_api(
                messages=messages,
                temperature=0.8,
                max_tokens=1500,
                context_length=4096
            )
            
            if error or not response:
                print(f"[INTROSPECTION-IA] ERROR LLM: {error}")
                return None
            
            # Parser la réponse
            introspection = self._parse_response(response)
            if not introspection:
                return None
            
            # Sauvegarder
            entry_id = self._save_introspection(introspection, dream_analysis)
            if entry_id:
                self._last_introspection_id = entry_id
                print(f"[INTROSPECTION-IA] OK Introspection sauvegardee: {entry_id}")
                print(f"[INTROSPECTION-IA] Titre: {introspection.get('titre', 'Sans titre')}")
                print(f"[INTROSPECTION-IA] Emotion: {introspection.get('emotion_dominante', '?')}")
                return introspection
            
            return None
            
        except Exception as e:
            print(f"[INTROSPECTION-IA] ERROR Generation: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_last_unmentioned(self) -> Optional[Dict[str, Any]]:
        """Récupère la dernière introspection non mentionnée"""
        try:
            introspections = self._load_introspections()
            if not introspections:
                return None
            
            entries = introspections.get("entries", [])
            if not entries:
                return None
            
            # Chercher la dernière non mentionnée (du plus récent au plus ancien)
            for entry in reversed(entries):
                if not entry.get("mentioned", False):
                    return entry
            
            return None
            
        except Exception as e:
            print(f"[INTROSPECTION-IA] ERROR get_last_unmentioned: {e}")
            return None
    
    def mark_mentioned(self, introspection_id: str = None):
        """Marque une introspection comme mentionnée"""
        try:
            introspections = self._load_introspections()
            if not introspections:
                return
            
            entries = introspections.get("entries", [])
            target_id = introspection_id or self._last_introspection_id
            
            for entry in entries:
                if target_id and entry.get("id") == target_id:
                    entry["mentioned"] = True
                    break
                elif not target_id and not entry.get("mentioned", False):
                    # Si pas d'ID spécifique, marquer la dernière non mentionnée
                    entry["mentioned"] = True
                    break
            
            self._save_introspections_section(introspections)
            print(f"[INTROSPECTION-IA] OK Introspection marquee comme mentionnee")
            
        except Exception as e:
            print(f"[INTROSPECTION-IA] ERROR mark_mentioned: {e}")
    
    # =========================================================================
    # MÉTHODES PRIVÉES
    # =========================================================================
    
    def _summarize_dream(self, dream_content: str) -> str:
        """Extrait un résumé court du rêve"""
        if not dream_content:
            return "Pas de rêve récent"
        # Prendre les 300 premiers caractères
        clean = dream_content.replace("[DREAM_START]", "").replace("[DREAM_END]", "").strip()
        if len(clean) > 300:
            return clean[:300] + "..."
        return clean
    
    def _extract_psy_insight(self, dream_analysis: Dict[str, Any]) -> str:
        """Extrait l'insight PSY de l'analyse du rêve"""
        if not dream_analysis:
            return "Pas d'analyse disponible"
        insight = dream_analysis.get("insight_ego", "")
        analyse = dream_analysis.get("analyse", "")
        if insight and analyse:
            return f"{insight} — {analyse[:200]}"
        return insight or analyse or "Analyse non disponible"
    
    def _summarize_ego(self, ego_flags: Dict[str, Any]) -> str:
        """Résume les flags ego récents"""
        if not ego_flags:
            # Tenter de charger depuis le fichier ego
            try:
                from pathlib import Path
                ego_path = Path("data/ego_flags.json")
                if ego_path.exists():
                    with open(ego_path, 'r', encoding='utf-8') as f:
                        ego_data = json.load(f)
                    # Extraire les traits avec forte conviction
                    traits = []
                    for group_name, group in ego_data.items():
                        if isinstance(group, dict):
                            for flag_name, flag_data in group.items():
                                if isinstance(flag_data, dict) and flag_data.get("conviction", 0) >= 4:
                                    if flag_data.get("value", False):
                                        traits.append(flag_name.replace("_", " "))
                    if traits:
                        return f"Traits dominants: {', '.join(traits[:8])}"
            except Exception:
                pass
            return "Portrait non disponible"
        
        # Si ego_flags passé directement
        traits = []
        for group_name, group in ego_flags.items():
            if isinstance(group, dict):
                for flag_name, flag_data in group.items():
                    if isinstance(flag_data, dict) and flag_data.get("conviction", 0) >= 4:
                        if flag_data.get("value", False):
                            traits.append(flag_name.replace("_", " "))
        return f"Traits dominants: {', '.join(traits[:8])}" if traits else "En cours de construction"
    
    def _summarize_states(self, active_states: list) -> str:
        """Résume les états actifs de l'utilisateur"""
        if not active_states:
            # Tenter de charger depuis json_manager
            try:
                all_states = self.json_manager.get_active_states()
                unresolved = [s for s in all_states.get("states", []) if not s.get("resolved", False)]
                if unresolved:
                    summaries = []
                    for s in unresolved[:5]:
                        cat = s.get("category", "?")
                        desc = s.get("description", "")[:60]
                        summaries.append(f"{cat}: {desc}")
                    return "\n".join(summaries)
            except Exception:
                pass
            return "Pas d'états actifs"
        
        summaries = []
        for s in active_states[:5]:
            cat = s.get("category", "?")
            desc = s.get("description", "")[:60]
            summaries.append(f"{cat}: {desc}")
        return "\n".join(summaries) if summaries else "Aucun état actif"
    
    def _parse_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse la réponse LLM en dict d'introspection"""
        try:
            # Tenter JSON direct
            clean = response.strip()
            
            # Extraire JSON si dans un bloc ```json
            if "```json" in clean:
                start = clean.index("```json") + 7
                end = clean.index("```", start)
                clean = clean[start:end].strip()
            elif "```" in clean:
                start = clean.index("```") + 3
                end = clean.index("```", start)
                clean = clean[start:end].strip()
            
            data = json.loads(clean)
            
            # Validation minimale
            required = ["titre", "contenu"]
            for field in required:
                if field not in data:
                    print(f"[INTROSPECTION-IA] WARN Champ manquant: {field}")
                    return None
            
            # Defaults
            data.setdefault("themes", [])
            data.setdefault("emotion_dominante", "questionnement")
            data.setdefault("question_ouverte", "")
            
            return data
            
        except json.JSONDecodeError:
            # Fallback: traiter comme texte brut
            print("[INTROSPECTION-IA] WARN Reponse non-JSON, fallback texte brut")
            lines = response.strip().split("\n")
            titre = lines[0][:80] if lines else "Réflexion sans titre"
            contenu = response.strip()
            return {
                "titre": titre,
                "contenu": contenu,
                "themes": [],
                "emotion_dominante": "questionnement",
                "question_ouverte": ""
            }
        except Exception as e:
            print(f"[INTROSPECTION-IA] ERROR Parse: {e}")
            return None
    
    def _save_introspection(self, introspection: Dict[str, Any], dream_analysis: Dict[str, Any] = None) -> Optional[str]:
        """Sauvegarde l'introspection dans la section INTROSPECTIONS_IA du journal annuel"""
        try:
            from pathlib import Path
            now = datetime.now()
            entry_id = f"intro_{now.strftime('%Y%m%d_%H%M%S')}"
            
            entry = {
                "id": entry_id,
                "timestamp": now.isoformat(),
                "titre": introspection.get("titre", "Sans titre"),
                "contenu": introspection.get("contenu", ""),
                "themes": introspection.get("themes", []),
                "emotion_dominante": introspection.get("emotion_dominante", ""),
                "question_ouverte": introspection.get("question_ouverte", ""),
                "mentioned": False,
                "source": {
                    "trigger": "post_dream",
                    "dream_score": dream_analysis.get("score_importance", 0) if dream_analysis else 0,
                    "dream_emotion": dream_analysis.get("emotion_dominante", "") if dream_analysis else ""
                }
            }
            
            # Charger section INTROSPECTIONS_IA
            introspections = self._load_introspections()
            introspections["entries"].append(entry)
            introspections["metadata"]["total_entries"] = len(introspections["entries"])
            introspections["metadata"]["last_entry"] = now.isoformat()
            
            # Sauvegarder
            self._save_introspections_section(introspections)
            
            return entry_id
            
        except Exception as e:
            print(f"[INTROSPECTION-IA] ERROR Save: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _load_introspections(self) -> Dict[str, Any]:
        """Charge la section INTROSPECTIONS_IA du journal annuel"""
        try:
            current_year = str(datetime.now().year)
            year_data = self.json_manager._load_year_data(current_year)
            
            if "INTROSPECTIONS_IA" not in year_data:
                return {
                    "metadata": {
                        "total_entries": 0,
                        "last_entry": None,
                        "created": datetime.now().isoformat()
                    },
                    "entries": []
                }
            
            return year_data["INTROSPECTIONS_IA"]
            
        except Exception as e:
            print(f"[INTROSPECTION-IA] ERROR Load: {e}")
            return {"metadata": {"total_entries": 0, "last_entry": None}, "entries": []}
    
    def _save_introspections_section(self, introspections: Dict[str, Any]):
        """Sauvegarde la section INTROSPECTIONS_IA dans le journal annuel"""
        try:
            current_year = str(datetime.now().year)
            year_data = self.json_manager._load_year_data(current_year)
            year_data["INTROSPECTIONS_IA"] = introspections
            self.json_manager._save_year_data(current_year, year_data)
        except Exception as e:
            print(f"[INTROSPECTION-IA] ERROR Save section: {e}")
            raise
