# 🧠 Cognitive Mirror - Intégration Mémoire

"""
Intégration avec le système de mémoire OGMA pour souvenirs "REF"
Sauvegarde contexte réflexions, enrichissement mémoire, recherche contextuelle
"""

import json
import time
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

class MemoryIntegration:
    """
    Gestionnaire intégration mémoire pour Cognitive Mirror
    
    Responsabilités:
    - Sauvegarde souvenirs "REF" (préfixe réflexion)
    - Enrichissement contexte conversation
    - Recherche réflexions antérieures
    - Interface avec MemoryManager OGMA
    """
    
    def __init__(self, memory_manager, config):
        """
        Initialise l'intégration mémoire
        
        Args:
            memory_manager: Instance MemoryManager OGMA
            config: Instance CognitiveMirrorConfig
        """
        self.memory_manager = memory_manager
        self.config = config
        
        # Cache réflexions récentes
        self.recent_reflections = []
        self.cache_size = self.config.get("max_cached_reflections", 50)
        
        # Statistiques
        self.stats = {
            "total_reflections_saved": 0,
            "last_reflection_time": None,
            "memory_integration_active": True
        }
        
        print("[MEMORY-INTEGRATION] 💾 Intégration mémoire initialisée")
    
    async def save_reflection_memory(self, session_id: str, reflection_context: str, conversation_context: Dict[str, Any]) -> bool:
        """
        Sauvegarde une réflexion comme souvenir "REF"
        
        Args:
            session_id: Identifiant session réflexive
            reflection_context: Contexte généré par la réflexion
            conversation_context: Contexte conversation actuelle
        
        Returns:
            bool: True si sauvegarde réussie
        """
        try:
            if not self.config.get("auto_save_reflections", True):
                print("[MEMORY-INTEGRATION] ⚠️ Sauvegarde automatique désactivée")
                return False
            
            # Génération ID mémoire REF unique
            ref_id = f"REF_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
            
            # Construction structure mémoire
            memory_entry = {
                "id": ref_id,
                "type": "cognitive_reflection",
                "prefix": self.config.get_system_messages()["memory_ref_prefix"],
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                
                # Contenu réflexion
                "reflection_summary": reflection_context,
                "insights": self._extract_insights_from_context(reflection_context),
                
                # Contexte conversation
                "conversation_context": conversation_context,
                "user_activity_patterns": self._analyze_user_patterns(conversation_context),
                
                # Métadonnées
                "metadata": {
                    "extension_version": getattr(self.config, 'VERSION', 'unknown'),
                    "creation_source": "cognitive_mirror_reflection",
                    "importance_score": self._calculate_importance_score(reflection_context),
                    "tags": self._generate_memory_tags(reflection_context, conversation_context)
                }
            }
            
            # Sauvegarde via MemoryManager OGMA
            success = await self._save_to_ogma_memory(memory_entry)
            
            if success:
                # Mise à jour cache et stats
                self._update_reflection_cache(memory_entry)
                self.stats["total_reflections_saved"] += 1
                self.stats["last_reflection_time"] = datetime.now().isoformat()
                
                print(f"[MEMORY-INTEGRATION] ✅ Réflexion sauvée: {ref_id}")
                return True
            else:
                print(f"[MEMORY-INTEGRATION] ❌ Erreur sauvegarde: {ref_id}")
                return False
                
        except Exception as e:
            print(f"[MEMORY-INTEGRATION] ❌ Exception sauvegarde réflexion: {e}")
            return False
    
    def get_reflection_context_for_conversation(self, conversation_topic: str = None) -> Optional[str]:
        """
        Récupère contexte réflexions pertinentes pour enrichir conversation
        
        Args:
            conversation_topic: Sujet conversation actuelle (optionnel)
        
        Returns:
            str: Contexte réflexions ou None
        """
        try:
            # Recherche réflexions récentes pertinentes
            relevant_reflections = self._find_relevant_reflections(conversation_topic)
            
            if not relevant_reflections:
                return None
            
            # Synthèse contexte enrichi
            context_parts = ["[Insights réflexions antérieures]"]
            
            for reflection in relevant_reflections[:3]:  # Max 3 plus pertinentes
                insights = reflection.get("insights", [])
                if insights:
                    context_parts.append(f"• {reflection['timestamp'][:10]}: {'; '.join(insights[:2])}")
            
            return " | ".join(context_parts)
            
        except Exception as e:
            print(f"[MEMORY-INTEGRATION] ❌ Erreur récupération contexte: {e}")
            return None
    
    def search_reflections(self, query: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Recherche dans l'historique des réflexions sauvées
        
        Args:
            query: Requête de recherche (optionnel)
            limit: Nombre maximum résultats
        
        Returns:
            list: Réflexions correspondantes
        """
        try:
            # Recherche via MemoryManager OGMA si disponible
            if hasattr(self.memory_manager, 'search_memories_by_type'):
                results = self.memory_manager.search_memories_by_type(
                    memory_type="cognitive_reflection",
                    query=query,
                    limit=limit
                )
                return results
            
            # Fallback recherche cache local
            filtered_reflections = []
            
            for reflection in self.recent_reflections:
                if query is None:
                    filtered_reflections.append(reflection)
                else:
                    # Recherche simple dans contenu
                    content = f"{reflection.get('reflection_summary', '')} {' '.join(reflection.get('insights', []))}"
                    if query.lower() in content.lower():
                        filtered_reflections.append(reflection)
                
                if len(filtered_reflections) >= limit:
                    break
            
            return filtered_reflections
            
        except Exception as e:
            print(f"[MEMORY-INTEGRATION] ❌ Erreur recherche réflexions: {e}")
            return []
    
    def get_reflection_statistics(self) -> Dict[str, Any]:
        """
        Retourne statistiques utilisation mémoire réflexions
        
        Returns:
            dict: Statistiques détaillées
        """
        stats = self.stats.copy()
        
        # Statistiques cache
        stats.update({
            "cached_reflections": len(self.recent_reflections),
            "cache_size_limit": self.cache_size,
            "memory_manager_available": self.memory_manager is not None
        })
        
        # Statistiques réflexions récentes
        if self.recent_reflections:
            recent_dates = [r.get("timestamp", "") for r in self.recent_reflections]
            stats["oldest_cached_reflection"] = min(recent_dates) if recent_dates else None
            stats["newest_cached_reflection"] = max(recent_dates) if recent_dates else None
        
        return stats
    
    def cleanup_old_reflections(self, max_age_days: int = 30):
        """
        Nettoie les réflexions anciennes du cache
        
        Args:
            max_age_days: Age maximum en jours
        """
        try:
            cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 3600)
            
            # Filtrage cache local
            filtered_cache = []
            cleaned_count = 0
            
            for reflection in self.recent_reflections:
                reflection_time = datetime.fromisoformat(reflection.get("timestamp", "")).timestamp()
                
                if reflection_time >= cutoff_time:
                    filtered_cache.append(reflection)
                else:
                    cleaned_count += 1
            
            self.recent_reflections = filtered_cache
            
            if cleaned_count > 0:
                print(f"[MEMORY-INTEGRATION] 🧹 {cleaned_count} réflexions anciennes nettoyées")
        
        except Exception as e:
            print(f"[MEMORY-INTEGRATION] ❌ Erreur nettoyage: {e}")
    
    def export_reflections(self, filepath: Path = None) -> bool:
        """
        Exporte l'historique des réflexions vers un fichier JSON
        
        Args:
            filepath: Chemin fichier export (optionnel)
        
        Returns:
            bool: True si export réussi
        """
        try:
            if filepath is None:
                filepath = Path(f"data/cognitive_mirror_reflections_export_{int(datetime.now().timestamp())}.json")
            
            # Récupération toutes les réflexions
            all_reflections = self.search_reflections(limit=1000)
            
            # Structure export
            export_data = {
                "export_timestamp": datetime.now().isoformat(),
                "extension_version": getattr(self.config, 'VERSION', 'unknown'),
                "total_reflections": len(all_reflections),
                "reflections": all_reflections,
                "statistics": self.get_reflection_statistics()
            }
            
            # Sauvegarde fichier
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            print(f"[MEMORY-INTEGRATION] 📦 Export réussi: {filepath}")
            return True
            
        except Exception as e:
            print(f"[MEMORY-INTEGRATION] ❌ Erreur export: {e}")
            return False
    
    # === MÉTHODES PRIVÉES ===
    
    async def _save_to_ogma_memory(self, memory_entry: Dict[str, Any]) -> bool:
        """Sauvegarde via MemoryManager OGMA"""
        try:
            if self.memory_manager and hasattr(self.memory_manager, 'add_memory'):
                # Adaptateur pour interface MemoryManager OGMA
                memory_id = memory_entry.get("id", f"CM_{int(time.time())}")
                
                # Reconstruction du texte brut à partir du contenu
                # Support de différents formats de memory_entry
                text_parts = []
                
                # Format introspection v2 (nouveau)
                if "synthesis" in memory_entry and memory_entry["synthesis"]:
                    text_parts.append(f"Synthèse introspection: {memory_entry['synthesis']}")
                if "main_ai_analysis" in memory_entry and memory_entry["main_ai_analysis"]:
                    text_parts.append(f"Analyse initiale: {memory_entry['main_ai_analysis']}")
                if "dialogue_messages" in memory_entry and memory_entry["dialogue_messages"]:
                    dialogue_summary = f"{len(memory_entry['dialogue_messages'])} échanges IA↔Archiviste"
                    text_parts.append(f"Dialogue: {dialogue_summary}")
                
                # Format réflexion legacy (ancien)
                if "reflection_summary" in memory_entry:
                    text_parts.append(f"Réflexion: {memory_entry['reflection_summary']}")
                if "insights" in memory_entry and memory_entry['insights']:
                    text_parts.append(f"Insights: {', '.join(memory_entry['insights'])}")
                if "conversation_context" in memory_entry:
                    text_parts.append(f"Contexte: {memory_entry['conversation_context']}")
                
                text_brut = "\n".join(text_parts) if text_parts else str(memory_entry.get('synthesis', memory_entry.get('reflection_summary', '')))
                
                print(f"[MEMORY-INTEGRATION] 📝 Appel add_memory: id={memory_id}, text_brut={len(text_brut)} chars")
                
                # Appel direct au MemoryManager async
                try:
                    success = await self.memory_manager.add_memory(memory_id, text_brut)
                except Exception as memory_error:
                    print(f"[MEMORY-INTEGRATION] ❌ ERREUR CRITIQUE - Échec add_memory: {memory_error}")
                    print(f"[MEMORY-INTEGRATION] ⚠️ FALLBACK ACTIVÉ - Sauvegarde locale utilisée à cause de: {type(memory_error).__name__}")
                    # Fallback informatif : sauvegarde locale
                    success = self._save_to_local_file(memory_entry)
                    if success:
                        print(f"[MEMORY-INTEGRATION] ✅ Fallback réussi - Données sauvées localement (à intégrer manuellement)")
                    return success
                
                print(f"[MEMORY-INTEGRATION] {'✅' if success else '❌'} MemoryManager.add_memory: {success}")
                return success
            
            elif self.memory_manager and hasattr(self.memory_manager, 'save_memory'):
                # Méthode alternative
                self.memory_manager.save_memory(memory_entry)
                return True
            
            else:
                # Fallback sauvegarde fichier local
                return self._save_to_local_file(memory_entry)
                
        except Exception as e:
            print(f"[MEMORY-INTEGRATION] ❌ Erreur interface MemoryManager: {e}")
            return self._save_to_local_file(memory_entry)
    
    def _save_to_local_file(self, memory_entry: Dict[str, Any]) -> bool:
        """Sauvegarde fallback fichier local"""
        try:
            filepath = Path("data/cognitive_mirror_reflections.jsonl")
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            # Ajout ligne JSONL
            with open(filepath, 'a', encoding='utf-8') as f:
                f.write(json.dumps(memory_entry, ensure_ascii=False) + '\n')
            
            return True
            
        except Exception as e:
            print(f"[MEMORY-INTEGRATION] ❌ Erreur sauvegarde locale: {e}")
            return False
    
    def _extract_insights_from_context(self, reflection_context: str) -> List[str]:
        """Extrait les insights clés du contexte de réflexion"""
        insights = []
        
        # Patterns extraction insights
        if "je recommande" in reflection_context.lower():
            parts = reflection_context.lower().split("je recommande")
            for part in parts[1:]:
                insight = part.split(".")[0].strip()
                if insight and len(insight) < 100:
                    insights.append(f"Recommandation: {insight}")
        
        if "l'utilisateur valorise" in reflection_context.lower():
            parts = reflection_context.lower().split("l'utilisateur valorise")
            for part in parts[1:]:
                value = part.split(".")[0].strip()
                if value and len(value) < 80:
                    insights.append(f"Valorise: {value}")
        
        if "stratégie:" in reflection_context.lower():
            parts = reflection_context.lower().split("stratégie:")
            if len(parts) > 1:
                strategy = parts[1].split("|")[0].strip()
                if strategy:
                    insights.append(f"Stratégie: {strategy}")
        
        return insights[:5]  # Max 5 insights
    
    def _analyze_user_patterns(self, conversation_context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyse patterns comportement utilisateur"""
        patterns = {
            "interaction_frequency": "regular",  # TODO: Calcul réel
            "response_style": "detailed",        # TODO: Analyse conversation
            "preferred_approach": "structured"   # TODO: Détection préférences
        }
        
        # TODO: Intégration avec données conversation réelles
        return patterns
    
    def _calculate_importance_score(self, reflection_context: str) -> float:
        """Calcule score importance réflexion (0.0-1.0)"""
        score = 0.5  # Base
        
        # Facteurs augmentant importance
        if "recommande" in reflection_context.lower():
            score += 0.2
        
        if "stratégie" in reflection_context.lower():
            score += 0.2
        
        if len(reflection_context) > 200:  # Réflexion détaillée
            score += 0.1
        
        return min(1.0, score)
    
    def _generate_memory_tags(self, reflection_context: str, conversation_context: Dict[str, Any]) -> List[str]:
        """Génère tags pour classification mémoire"""
        tags = ["cognitive_reflection"]
        
        # Tags basés contenu
        context_lower = reflection_context.lower()
        
        if "recommande" in context_lower:
            tags.append("recommendation")
        
        if "stratégie" in context_lower or "approche" in context_lower:
            tags.append("strategy")
        
        if "utilisateur" in context_lower:
            tags.append("user_analysis")
        
        if "patterns" in context_lower or "comportement" in context_lower:
            tags.append("behavioral_pattern")
        
        # Tags temporels
        current_hour = datetime.now().hour
        if 9 <= current_hour <= 17:
            tags.append("business_hours")
        else:
            tags.append("outside_hours")
        
        return tags
    
    def _update_reflection_cache(self, memory_entry: Dict[str, Any]):
        """Met à jour le cache des réflexions récentes"""
        self.recent_reflections.append(memory_entry)
        
        # Limitation taille cache
        if len(self.recent_reflections) > self.cache_size:
            self.recent_reflections = self.recent_reflections[-self.cache_size:]
    
    def _find_relevant_reflections(self, topic: str = None) -> List[Dict[str, Any]]:
        """Trouve réflexions pertinentes pour contexte actuel"""
        if not self.recent_reflections:
            return []
        
        # Si pas de sujet spécifique, retourne les plus récentes
        if topic is None:
            return sorted(
                self.recent_reflections,
                key=lambda r: r.get("timestamp", ""),
                reverse=True
            )[:3]
        
        # Recherche par pertinence sujet
        relevant = []
        topic_lower = topic.lower()
        
        for reflection in self.recent_reflections:
            context = reflection.get("reflection_summary", "").lower()
            insights = " ".join(reflection.get("insights", [])).lower()
            
            # Score pertinence basique
            relevance_score = 0
            for word in topic_lower.split():
                if word in context:
                    relevance_score += 2
                if word in insights:
                    relevance_score += 1
            
            if relevance_score > 0:
                reflection_copy = reflection.copy()
                reflection_copy["relevance_score"] = relevance_score
                relevant.append(reflection_copy)
        
        # Tri par pertinence puis date
        return sorted(
            relevant,
            key=lambda r: (r["relevance_score"], r.get("timestamp", "")),
            reverse=True
        )[:3]
    
    async def save_conversation_memory(self, session_id: str, conversation_data: Dict[str, Any]) -> bool:
        """
        Sauvegarde une conversation Subconscience en mémoire
        
        Args:
            session_id: ID de la session de conversation
            conversation_data: Données complètes de la conversation
            
        Returns:
            bool: Succès de la sauvegarde
        """
        try:
            memory_entry = {
                "id": f"subconscience_{session_id}",
                "type": "subconscience_conversation",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "participants": conversation_data.get("participants", []),
                "messages": conversation_data.get("messages", []),
                "duration": conversation_data.get("duration", 0),
                "trigger": conversation_data.get("trigger", "inactivity"),
                "insights": self._extract_conversation_insights(conversation_data),
                "tags": ["subconscience", "automated", "ia_principale", "archiviste"]
            }
            
            # Sauvegarde via MemoryManager OGMA
            if await self._save_to_ogma_memory(memory_entry):
                self.stats["total_reflections_saved"] += 1
                print(f"[MEMORY-INTEGRATION] 💾 Conversation Subconscience sauvée (ID: {session_id})")
                return True
            else:
                print(f"[MEMORY-INTEGRATION] ❌ Échec sauvegarde conversation {session_id}")
                return False
                
        except Exception as e:
            print(f"[MEMORY-INTEGRATION] ❌ Erreur sauvegarde conversation: {e}")
            return False
    
    def get_relevant_context(self, conversation_topic: str = None) -> str:
        """
        Récupère le contexte mémoire pertinent pour une conversation
        
        Args:
            conversation_topic: Sujet de conversation (optionnel)
            
        Returns:
            str: Contexte formaté pour la conversation
        """
        try:
            # Recherche des conversations Subconscience récentes
            recent_conversations = self.search_reflections(
                query="subconscience automated",
                limit=3
            )
            
            # Recherche des réflexions pertinentes
            relevant_reflections = self._find_relevant_reflections(conversation_topic)
            
            # Construction du contexte
            context_parts = []
            
            if recent_conversations:
                context_parts.append("## Conversations Subconscience récentes:")
                for conv in recent_conversations[:2]:
                    context_parts.append(f"- {conv.get('timestamp', 'Date inconnue')}: {len(conv.get('messages', []))} échanges")
            
            if relevant_reflections:
                context_parts.append("## Réflexions pertinentes:")
                for ref in relevant_reflections[:2]:
                    context_parts.append(f"- {ref.get('summary', 'Réflexion sans résumé')}")
            
            if not context_parts:
                context_parts.append("Première conversation Subconscience - pas de contexte antérieur disponible.")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            print(f"[MEMORY-INTEGRATION] ❌ Erreur récupération contexte: {e}")
            return "Contexte mémoire non disponible"
    
    def _extract_conversation_insights(self, conversation_data: Dict[str, Any]) -> List[str]:
        """
        Extrait les insights d'une conversation Subconscience
        
        Args:
            conversation_data: Données de la conversation
            
        Returns:
            List[str]: Liste des insights extraits
        """
        insights = []
        
        messages = conversation_data.get("messages", [])
        if len(messages) >= 4:
            insights.append(f"Conversation riche: {len(messages)} échanges")
        
        participants = conversation_data.get("participants", [])
        # Détection dialogue IA↔Archiviste (générique)
        if len(participants) >= 2 and "Archiviste" in participants:
            insights.append("Dialogue IA principale-Archiviste complet")
        
        duration = conversation_data.get("duration", 0)
        if duration > 60:
            insights.append(f"Conversation longue: {duration}s")

        return insights

    async def save_introspection_conditional(self, introspection_data: Dict[str, Any]) -> bool:
        """
        Sauvegarde introspection v2.0 SEULEMENT si l'IA décide (NOUVEAU)

        Args:
            introspection_data: {
                "session_id": str,
                "save_decision": "yes/no",
                "reason": str,
                "importance": int (0-10),
                "main_ai_analysis": str,
                "dialogue_messages": list,
                "synthesis": str,
                "duration": float,
                "exchanges_count": int
            }

        Returns:
            bool: Succès de la sauvegarde
        """
        try:
            # Vérifier décision IA
            save_decision = introspection_data.get("save_decision", "no")
            if save_decision != "yes":
                reason = introspection_data.get("reason", "Non spécifié")
                print(f"[MEMORY-INTEGRATION] 🚫 L'IA a décidé de ne pas sauvegarder")
                print(f"[MEMORY-INTEGRATION] 📝 Raison: {reason}")
                return False

            # Vérifier seuil importance
            importance = introspection_data.get("importance", 5)
            threshold = self.config.get("importance_threshold", 5)

            if importance < threshold:
                print(f"[MEMORY-INTEGRATION] ⚠️ Importance {importance} < seuil {threshold} - sauvegarde ignorée")
                return False

            # Construction entrée mémoire
            session_id = introspection_data.get("session_id", f"introspection_{int(time.time())}")

            memory_entry = {
                "id": f"introspection_{session_id}",
                "type": "introspection_v2",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),

                # Contenu introspection
                "main_ai_analysis": introspection_data.get("main_ai_analysis", ""),
                "dialogue_messages": introspection_data.get("dialogue_messages", []),
                "synthesis": introspection_data.get("synthesis", ""),

                # Métadonnées IA
                "ia_save_decision": save_decision,
                "ia_importance": importance,
                "ia_reason": introspection_data.get("reason", ""),

                # Statistiques
                "duration": introspection_data.get("duration", 0),
                "exchanges_count": introspection_data.get("exchanges_count", 0),

                # Tags
                "tags": ["introspection", "v2", "ia_principale", "archiviste", f"importance_{importance}"]
            }

            # Sauvegarde via MemoryManager OGMA
            success = await self._save_to_ogma_memory(memory_entry)

            if success:
                self.stats["total_reflections_saved"] += 1
                print(f"[MEMORY-INTEGRATION] 💾 Introspection sauvegardée (ID: {session_id}, importance: {importance}/10)")
                return True
            else:
                print(f"[MEMORY-INTEGRATION] ❌ Échec sauvegarde introspection {session_id}")
                return False

        except Exception as e:
            print(f"[MEMORY-INTEGRATION] ❌ Erreur sauvegarde conditionnelle: {e}")
            import traceback
            traceback.print_exc()
            return False