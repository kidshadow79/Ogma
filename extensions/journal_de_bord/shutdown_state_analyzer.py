"""
OGMA - Journal de Bord v2.0
Analyseur d'États à la Fermeture (Shutdown State Analyzer)

Fonctionnalités:
- Analysé les conversations créées/modifiées depuis la dernière fermeture
- Détecte les résolutions d'états manquées par le live detector
- Met à jour les états actifs avant shutdown
- Sauvegarde le timestamp de dernière analyse

Pattern: Hook appelé à la fermeture d'OGMA (shutdown)
"""

import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
import asyncio


class ShutdownStateAnalyzer:
    """Analyse les états actifs à la fermeture d'OGMA"""
    
    def __init__(self, json_manager, archiviste_controller, conversations_dir: Path = None):
        """
        Initialise l'analyseur
        
        Args:
            json_manager: Instance JSONManager pour accès états actifs
            archiviste_controller: Contrôleur LLM pour analyse
            conversations_dir: Dossier des conversations (optionnel)
        """
        self.json_manager = json_manager
        self.archiviste = archiviste_controller
        
        # Dossier conversations
        if conversations_dir:
            self.conversations_dir = conversations_dir
        else:
            self.conversations_dir = Path("data/conversations")
        
        # Fichier pour stocker le timestamp de dernière analyse
        self.last_analysis_file = Path("extensions/journal_de_bord/data/.last_shutdown_analysis")
        
        # Types d'états
        self.state_types = {
            "ephemere": ["humeur", "personnel"],           # TTL 12h
            "temporaire": ["santé", "technique", "apprentissage"],  # TTL 7j
            "long_terme": ["projet"],                     # TTL 30j
            "durable": ["identité", "relation"]            # Jamais auto
        }
        
        print("[SHUTDOWN-ANALYZER] Initialisé")
    
    def _get_last_analysis_timestamp(self) -> Optional[datetime]:
        """Récupère le timestamp de la dernière analyse"""
        try:
            if self.last_analysis_file.exists():
                content = self.last_analysis_file.read_text().strip()
                return datetime.fromisoformat(content)
            return None
        except Exception as e:
            print(f"[SHUTDOWN-ANALYZER] Erreur lecture timestamp: {e}")
            return None
    
    def _save_analysis_timestamp(self):
        """Sauvegarde le timestamp actuel"""
        try:
            self.last_analysis_file.parent.mkdir(parents=True, exist_ok=True)
            self.last_analysis_file.write_text(datetime.now().isoformat())
        except Exception as e:
            print(f"[SHUTDOWN-ANALYZER] Erreur sauvegarde timestamp: {e}")
    
    def _get_conversations_since_last_analysis(self) -> List[Dict[str, Any]]:
        """Récupère les conversations modifiées depuis la dernière analyse"""
        last_analysis = self._get_last_analysis_timestamp()
        conversations = []
        
        try:
            if not self.conversations_dir.exists():
                print(f"[SHUTDOWN-ANALYZER] Dossier conversations non trouvé: {self.conversations_dir}")
                return []
            
            # Parcourir les fichiers JSON de conversation
            for conv_file in self.conversations_dir.glob("*.json"):
                if conv_file.name == "index.json":
                    continue
                
                try:
                    # Vérifier date modification
                    mtime = datetime.fromtimestamp(conv_file.stat().st_mtime)
                    
                    # Si pas de dernière analyse ou fichier modifié depuis
                    if last_analysis is None or mtime > last_analysis:
                        with open(conv_file, 'r', encoding='utf-8') as f:
                            conv_data = json.load(f)
                        
                        # Normaliser en dict (certains fichiers sont des listes)
                        if isinstance(conv_data, list):
                            conv_data = {
                                "messages": conv_data,
                                "_was_list": True
                            }
                        
                        conv_data['_file_path'] = str(conv_file)
                        conv_data['_modified_at'] = mtime.isoformat()
                        conversations.append(conv_data)
                except Exception as e:
                    print(f"[SHUTDOWN-ANALYZER] Erreur lecture {conv_file.name}: {e}")
                    continue
            
            print(f"[SHUTDOWN-ANALYZER] {len(conversations)} conversations à analyser")
            return conversations
            
        except Exception as e:
            print(f"[SHUTDOWN-ANALYZER] Erreur scan conversations: {e}")
            return []
    
    def _extract_conversation_summary(self, conv_data: Dict[str, Any], max_messages: int = 20) -> str:
        """Extrait un résumé de la conversation pour l'analyse"""
        messages = conv_data.get("messages", conv_data.get("history", []))
        
        if not messages:
            return ""
        
        # Prendre les derniers messages
        recent = messages[-max_messages:] if len(messages) > max_messages else messages
        
        summary_parts = []
        for msg in recent:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:200]  # Tronquer
            if content:
                summary_parts.append(f"{role.upper()}: {content}")
        
        return "\n".join(summary_parts)
    
    async def analyze_and_resolve_states(self) -> Dict[str, Any]:
        """
        Analyse principale à la fermeture - Parcourt les conversations récentes
        et détecte les états résolus
        
        Returns:
            Dict: {
                "analyzed_conversations": int,
                "resolved_states": List[int],
                "updated_states": List[int],
                "errors": List[str]
            }
        """
        result = {
            "analyzed_conversations": 0,
            "resolved_states": [],
            "updated_states": [],
            "errors": []
        }
        
        try:
            # 1. Récupérer les états actifs non résolus
            current_states = self.json_manager.get_active_states()
            unresolved = [s for s in current_states.get("states", []) if not s.get("resolved", False)]
            
            if not unresolved:
                print("[SHUTDOWN-ANALYZER] Aucun état actif à analyser")
                self._save_analysis_timestamp()
                return result
            
            print(f"[SHUTDOWN-ANALYZER] {len(unresolved)} états actifs à vérifier")
            
            # 2. Récupérer les conversations récentes
            conversations = self._get_conversations_since_last_analysis()
            
            if not conversations:
                print("[SHUTDOWN-ANALYZER] Aucune nouvelle conversation depuis dernière analyse")
                self._save_analysis_timestamp()
                return result
            
            # 3. Construire le contexte global des conversations
            all_summaries = []
            for conv in conversations:
                summary = self._extract_conversation_summary(conv)
                if summary:
                    conv_id = conv.get("id", conv.get("_file_path", "unknown"))
                    all_summaries.append(f"=== Conversation {conv_id} ===\n{summary}")
            
            if not all_summaries:
                print("[SHUTDOWN-ANALYZER] Aucun contenu extractible des conversations")
                self._save_analysis_timestamp()
                return result
            
            result["analyzed_conversations"] = len(all_summaries)
            
            # 4. Analyse LLM groupée
            analysis = await self._llm_batch_analysis(unresolved, all_summaries)
            
            if analysis:
                # 5. Appliquer les résolutions
                for state_id in analysis.get("resolved_state_ids", []):
                    try:
                        success = self.json_manager.resolve_state(
                            state_id=state_id,
                            resolution_note=f"Auto-résolu à la fermeture: {analysis.get('resolution_notes', {}).get(str(state_id), 'Détecté dans conversations récentes')}"
                        )
                        if success:
                            result["resolved_states"].append(state_id)
                            print(f"[SHUTDOWN-ANALYZER] Résolu état #{state_id}")
                    except Exception as e:
                        result["errors"].append(f"Erreur résolution #{state_id}: {e}")
                
                # 6. Appliquer les mises à jour
                for update in analysis.get("updated_states", []):
                    try:
                        success = self.json_manager.modify_active_state(
                            state_id=update["state_id"],
                            update_note=update.get("update_note", "Mise à jour shutdown"),
                            new_description=update.get("new_description")
                        )
                        if success:
                            result["updated_states"].append(update["state_id"])
                            print(f"[SHUTDOWN-ANALYZER] MàJ état #{update['state_id']}")
                    except Exception as e:
                        result["errors"].append(f"Erreur MàJ #{update.get('state_id')}: {e}")
            
            # 7. Sauvegarder le timestamp
            self._save_analysis_timestamp()
            
            print(f"[SHUTDOWN-ANALYZER] Terminé: {len(result['resolved_states'])} résolus, {len(result['updated_states'])} mis à jour")
            return result
            
        except Exception as e:
            print(f"[SHUTDOWN-ANALYZER] ERROR: {e}")
            import traceback
            traceback.print_exc()
            result["errors"].append(str(e))
            return result
    
    async def _llm_batch_analysis(
        self, 
        states: List[Dict[str, Any]], 
        conversation_summaries: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Analyse LLM groupée de tous les états vs toutes les conversations récentes
        
        Returns:
            Dict: {
                "resolved_state_ids": [int],
                "resolution_notes": {state_id: "note"},
                "updated_states": [{"state_id": int, ...}]
            }
        """
        try:
            # Construire la checklist des états
            states_checklist = "ÉTATS ACTIFS À VÉRIFIER:\n"
            for s in states:
                category = s['category']
                state_type = "TEMPORAIRE" if category in self.state_types.get("temporaire", []) else "DURABLE"
                age_days = 0
                try:
                    created = datetime.fromisoformat(s.get('created_at', datetime.now().isoformat()))
                    age_days = (datetime.now() - created).days
                except:
                    pass
                states_checklist += f"  #{s['state_id']} ({category}, {state_type}, {age_days}j): {s['description'][:100]}...\n"
            
            # Limiter le contexte conversations (éviter dépassement tokens)
            conv_context = "\n\n".join(conversation_summaries[:5])  # Max 5 conversations
            if len(conv_context) > 8000:
                conv_context = conv_context[:8000] + "\n[... tronqué ...]"
            
            prompt = f"""Tu es un analyseur d'états du journal de bord. Ta mission est de détecter les états qui ont été résolus
dans les conversations récentes mais non détectés en temps réel.

{states_checklist}

═════════════════════════════════════════════════════════════════
CONVERSATIONS RÉCENTES (depuis dernière fermeture):
═════════════════════════════════════════════════════════════════
{conv_context}

═════════════════════════════════════════════════════════════════
RÈGLES:
- TEMPORAIRE (santé, projet, apprentissage, technique) → Résolu si: terminé, guéri, réussi, abandonné
- DURABLE (humeur, personnel) → Résolu si REMPLACÉ par un état différent (ex: "je suis calme maintenant" remplace "excitée")
- IMPORTANT: Ne résous que si c'est EXPLICITE dans les conversations

RÉPONDS EN JSON:
{{
  "resolved_state_ids": [1, 3],
  "resolution_notes": {{
    "1": "Raison résolution état 1",
    "3": "Raison résolution état 3"
  }},
  "updated_states": [
    {{
      "state_id": 2,
      "new_description": "Description mise à jour si progression détectée",
      "update_note": "Raison de la mise à jour"
    }}
  ]
}}

Si aucun changement détecté: {{"resolved_state_ids": [], "resolution_notes": {{}}, "updated_states": []}}
"""
            
            # Appel LLM
            if not self.archiviste:
                print("[SHUTDOWN-ANALYZER] Archiviste non disponible")
                return None
            
            response, error = await self.archiviste.call_chat_api(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,  # Très précis
                max_tokens=800,
                context_length=16000,
                is_json=False
            )
            
            if error or not response:
                print(f"[SHUTDOWN-ANALYZER] Erreur LLM: {error}")
                return None
            
            # Parsing JSON
            import re
            response_text = response.strip()
            
            # Nettoyage markdown
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            # Nettoyage caractères contrôle
            response_text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', response_text)
            
            analysis = json.loads(response_text)
            
            resolved_count = len(analysis.get("resolved_state_ids", []))
            updated_count = len(analysis.get("updated_states", []))
            print(f"[SHUTDOWN-ANALYZER] LLM: {resolved_count} résolutions, {updated_count} mises à jour détectées")
            
            return analysis
            
        except Exception as e:
            print(f"[SHUTDOWN-ANALYZER] Erreur analyse LLM: {e}")
            import traceback
            traceback.print_exc()
            return None


# ============================================================
# API PUBLIQUE
# ============================================================

_shutdown_analyzer: Optional[ShutdownStateAnalyzer] = None


def initialize_shutdown_analyzer(json_manager, archiviste_controller, conversations_dir: Path = None) -> Optional[ShutdownStateAnalyzer]:
    """
    Initialise l'analyseur shutdown (singleton)
    
    Args:
        json_manager: Instance JournalJSONManager
        archiviste_controller: Contrôleur LLM Archiviste
        conversations_dir: Dossier des conversations (optionnel)
    
    Returns:
        Instance ShutdownStateAnalyzer ou None si erreur
    """
    global _shutdown_analyzer
    
    try:
        if _shutdown_analyzer is None:
            _shutdown_analyzer = ShutdownStateAnalyzer(
                json_manager=json_manager,
                archiviste_controller=archiviste_controller,
                conversations_dir=conversations_dir
            )
            print("[SHUTDOWN-ANALYZER] Instance singleton créée")
        
        return _shutdown_analyzer
    
    except Exception as e:
        print(f"[SHUTDOWN-ANALYZER] Erreur initialisation: {e}")
        return None


def get_shutdown_analyzer() -> Optional[ShutdownStateAnalyzer]:
    """Retourne l'instance singleton"""
    return _shutdown_analyzer


async def run_shutdown_analysis() -> Dict[str, Any]:
    """
    Lance l'analyse à la fermeture
    
    Returns:
        Résultat de l'analyse ou dict vide si erreur
    """
    global _shutdown_analyzer
    
    if _shutdown_analyzer is None:
        print("[SHUTDOWN-ANALYZER] Non initialisé - skip")
        return {"error": "Non initialisé"}
    
    try:
        return await _shutdown_analyzer.analyze_and_resolve_states()
    except Exception as e:
        print(f"[SHUTDOWN-ANALYZER] Erreur run: {e}")
        return {"error": str(e)}
