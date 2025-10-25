# 🧠 Core Extension Archi_sensor - Orchestrateur Principal

"""
Orchestrateur principal de l'extension Archi_sensor
Gère l'analyse métacognitive par IA Archiviste avec persistance et intégration OGMA
"""

import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from .unified_analyzer import ArchivisteUnifiedAnalyzer
from .ui_components import ArchiSensorUI
from .config import ArchiSensorConfig

class ArchiSensorCore:
    """
    Cœur de l'extension Archi_sensor
    
    Responsabilités:
    - Orchestration analyse métacognitive Archiviste
    - Gestion état ON/OFF persistant
    - Coordination avec UI et système OGMA
    - Toggle exclusif avec metacognition_sensor
    """
    
    _instance = None
    
    def __init__(self, archiviste_controller, status_queue=None):
        self.archiviste_controller = archiviste_controller
        self.status_queue = status_queue
        self.config = ArchiSensorConfig()
        
        # Composants principaux
        self.analyzer = ArchivisteUnifiedAnalyzer(archiviste_controller, status_queue)
        self.ui_manager = ArchiSensorUI()
        
        # État extension
        self.is_enabled = False
        self.is_ready = False
        self.last_analysis_result = None
        self.pending_behavioral_injections = []
        
        # Initialisation
        self._initialize()
        
        # Singleton pattern
        ArchiSensorCore._instance = self
        
        print("[ARCHI-CORE] ✅ Extension Archi_sensor initialisée")
    
    @classmethod
    def get_instance(cls) -> Optional['ArchiSensorCore']:
        """Retourne l'instance singleton"""
        return cls._instance
    
    def _initialize(self):
        """Initialisation complète de l'extension"""
        
        try:
            # Créer répertoire données
            self.config.ensure_data_dir()
            
            # Charger état persistant
            self.is_enabled = self._load_enabled_state()
            
            # Configurer UI
            self.ui_manager.set_enabled_state(self.is_enabled)
            
            # Marquer comme prêt
            self.is_ready = True
            
            print(f"[ARCHI-CORE] Extension initialisée - État: {'ON' if self.is_enabled else 'OFF'}")
            
        except Exception as e:
            print(f"[ARCHI-CORE] ❌ Erreur initialisation: {e}")
            self.is_ready = False
    
    def is_ready(self) -> bool:
        """Vérifie si l'extension est prête à fonctionner"""
        return self.is_ready and self.archiviste_controller is not None
    
    async def analyze_post_response(self, 
                                  response_text: str,
                                  conversation_context: str,
                                  user_message: str) -> Dict[str, Any]:
        """
        Analyse post-réponse par l'Archiviste (point d'entrée principal)
        
        Args:
            response_text: Réponse IA à analyser
            conversation_context: Contexte conversationnel complet
            user_message: Message utilisateur déclencheur
            
        Returns:
            Résultat analyse avec métriques et recommandations
        """
        
        if not self.is_enabled or not self.is_ready:
            print("[ARCHI-CORE] Extension désactivée ou non prête")
            return self._get_disabled_response()
        
        try:
            print(f"[ARCHI-CORE] 🧠 Lancement analyse post-réponse...")
            
            # Analyse complète par Archiviste
            analysis_result = await self.analyzer.analyze_complete_emotional_state(
                response_text=response_text,
                conversation_history=conversation_context,
                user_context=user_message
            )
            
            # Stocker résultat
            self.last_analysis_result = analysis_result
            
            # Générer injections comportementales
            behavioral_injections = self.analyzer.get_behavioral_injections(analysis_result)
            self.pending_behavioral_injections.extend(behavioral_injections)
            
            # Mettre à jour UI
            self.ui_manager.update_led_levels(analysis_result)
            self.ui_manager.update_debug_info(analysis_result)
            
            # Log succès
            metrics = analysis_result.get('metacognitive_metrics', {})
            emotion = analysis_result.get('emotional_context', {}).get('primary_emotion', 'neutre')
            
            print(f"[ARCHI-CORE] ✅ Analyse terminée - Émotion: {emotion}, Métriques: {len(metrics)}")
            
            # Formater pour compatibilité système OGMA
            return self._format_for_ogma(analysis_result)
            
        except Exception as e:
            print(f"[ARCHI-CORE] ❌ Erreur analyse: {e}")
            return self._get_error_response()
    
    def toggle_enabled_state(self, enabled: bool):
        """
        Toggle état ON/OFF extension avec persistance
        
        Args:
            enabled: Nouvel état (True=ON, False=OFF)
        """
        
        previous_state = self.is_enabled
        self.is_enabled = enabled
        
        # Sauvegarder état
        self._save_enabled_state(enabled)
        
        # Mettre à jour UI
        self.ui_manager.set_enabled_state(enabled)
        
        # Notification changement
        if self.status_queue:
            status_msg = f"🧠 Extension Archi_sensor {'activée' if enabled else 'désactivée'}"
            self.status_queue.put(status_msg)
        
        print(f"[ARCHI-CORE] État extension: {previous_state} → {enabled}")
        
        # Effacer injections pendantes si désactivation
        if not enabled:
            self.pending_behavioral_injections.clear()
    
    def get_pending_injections(self) -> List[str]:
        """
        Récupère et vide la liste des injections comportementales pendantes
        
        Returns:
            Liste des messages à injecter dans la prochaine conversation
        """
        
        if not self.is_enabled:
            return []
        
        injections = self.pending_behavioral_injections.copy()
        self.pending_behavioral_injections.clear()
        
        if injections:
            print(f"[ARCHI-CORE] 💬 {len(injections)} injection(s) comportementale(s) récupérée(s)")
        
        return injections
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Retourne les métriques actuelles pour affichage"""
        
        if not self.last_analysis_result:
            return {}
        
        return self.last_analysis_result.get('metacognitive_metrics', {})
    
    def get_emotional_context(self) -> Dict[str, Any]:
        """Retourne le contexte émotionnel actuel"""
        
        if not self.last_analysis_result:
            return {}
        
        return self.last_analysis_result.get('emotional_context', {})
    
    def _load_enabled_state(self) -> bool:
        """Charge l'état ON/OFF depuis fichier persistant"""
        
        try:
            if self.config.STATE_FILE.exists():
                state_content = self.config.STATE_FILE.read_text().strip()
                enabled = state_content == 'enabled'
                print(f"[ARCHI-CORE] État chargé depuis fichier: {enabled}")
                return enabled
        except Exception as e:
            print(f"[ARCHI-CORE] ⚠️ Erreur lecture état: {e}")
        
        return False  # Défaut: désactivé
    
    def _save_enabled_state(self, enabled: bool):
        """Sauvegarde l'état ON/OFF dans fichier persistant"""
        
        try:
            state_content = 'enabled' if enabled else 'disabled'
            self.config.STATE_FILE.write_text(state_content)
            print(f"[ARCHI-CORE] État sauvegardé: {enabled}")
        except Exception as e:
            print(f"[ARCHI-CORE] ⚠️ Erreur sauvegarde état: {e}")
    
    def _format_for_ogma(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Formate le résultat d'analyse pour compatibilité système OGMA
        (compatible avec format metacognition_sensor existant)
        """
        
        try:
            # Convertir métriques au format attendu par OGMA
            states = []
            metrics = analysis_result.get('metacognitive_metrics', {})
            
            for metric_name, metric_data in metrics.items():
                states.append({
                    'name': metric_name,
                    'level': metric_data.get('level', 1),
                    'confidence': metric_data.get('confidence', 0.5),
                    'score': metric_data.get('confidence', 0.5)  # Alias pour compatibilité
                })
            
            # Messages d'injection
            injection_messages = self.pending_behavioral_injections.copy()
            
            # Format compatible OGMA
            ogma_format = {
                'states': states,
                'injection_messages': injection_messages,
                'emotional_context': analysis_result.get('emotional_context', {}),
                'narrative_insights': analysis_result.get('narrative_insights', {}),
                'analysis_timestamp': datetime.now().isoformat(),
                'extension_name': 'archi_sensor'
            }
            
            return ogma_format
            
        except Exception as e:
            print(f"[ARCHI-CORE] ⚠️ Erreur formatage OGMA: {e}")
            return self._get_error_response()
    
    def _get_disabled_response(self) -> Dict[str, Any]:
        """Réponse quand extension désactivée"""
        
        return {
            'states': [],
            'injection_messages': [],
            'emotional_context': {},
            'narrative_insights': {},
            'extension_status': 'disabled'
        }
    
    def _get_error_response(self) -> Dict[str, Any]:
        """Réponse en cas d'erreur"""
        
        return {
            'states': [],
            'injection_messages': ["[ARCHI-SENSOR] Analyse en mode dégradé"],
            'emotional_context': {'primary_emotion': 'neutre'},
            'narrative_insights': {'emotional_arc': 'Analyse indisponible'},
            'extension_status': 'error'
        }
    
    def get_status_info(self) -> Dict[str, Any]:
        """Informations de statut pour debugging"""
        
        return {
            'extension_name': 'archi_sensor',
            'version': self.config.VERSION,
            'is_enabled': self.is_enabled,
            'is_ready': self.is_ready,
            'analyzer_available': self.analyzer is not None,
            'archiviste_available': self.archiviste_controller is not None,
            'last_analysis': self.last_analysis_result is not None,
            'pending_injections': len(self.pending_behavioral_injections),
            'ui_state': self.ui_manager.get_current_state()
        }
    
    def cleanup(self):
        """Nettoyage et fermeture propre"""
        
        try:
            # Sauvegarder état final
            self._save_enabled_state(self.is_enabled)
            
            # Nettoyer caches
            if hasattr(self.analyzer, 'analysis_cache'):
                self.analyzer.analysis_cache.clear()
            
            # Réinitialiser UI
            self.ui_manager.set_enabled_state(False)
            
            print("[ARCHI-CORE] Extension fermée proprement")
            
        except Exception as e:
            print(f"[ARCHI-CORE] ⚠️ Erreur nettoyage: {e}")