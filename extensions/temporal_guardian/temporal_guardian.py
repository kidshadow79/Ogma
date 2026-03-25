"""
Extension Temporal Guardian pour OGMA
====================================

Extension qui implémente la gestion temporelle organique via l'archiviste.

Architecture:
- TemporalSensor: Mesure les délais entre messages (capteur simple)
- ArchivisteEnricher: Enrichit le prompt archiviste avec contexte temporel
- TemporalGuardian: Orchestrateur principal de l'extension

Philosophie: Le capteur mesure, l'archiviste interprète et analyse.
"""

from typing import Optional, Dict, Any
from datetime import datetime

from .config import TemporalGuardianConfig
from .temporal_sensor import TemporalSensor, TemporalMeasurement
from .archiviste_enricher import ArchivisteEnricher


class TemporalGuardian:
    """
    Extension principale pour la gestion temporelle OGMA.
    
    Responsabilités:
    - Orchestrer capteur temporel et enrichisseur archiviste
    - Gérer cycle de vie des sessions temporelles
    - Fournir interface pour intégration OGMA
    
    Usage:
        guardian = TemporalGuardian()
        enriched_prompt = guardian.process_user_message(
            user_message="Bonjour", 
            archiviste_prompt="Analysez ce message..."
        )
    """
    
    def __init__(self, config: Optional[TemporalGuardianConfig] = None, debug: bool = False):
        self.config = config or TemporalGuardianConfig()
        self.debug = debug
        
        # Composants principaux
        self.sensor = TemporalSensor(debug=self.debug)
        self.enricher = ArchivisteEnricher(self.config, debug=self.debug)
        
        # État extension
        self.is_active = self.config.enabled
        self.last_measurement: Optional[TemporalMeasurement] = None
        
        if self.debug:
            print("[TemporalGuardian] Extension initialisée")
            print(f"[TemporalGuardian] Mode actif: {self.is_active}")
    
    def process_user_message(
        self, 
        user_message: str, 
        archiviste_prompt: str = ""
    ) -> Dict[str, Any]:
        """
        Traite un message utilisateur et retourne le contexte temporel enrichi.
        
        Args:
            user_message: Message de l'utilisateur
            archiviste_prompt: Prompt de base pour l'archiviste
            
        Returns:
            Dict contenant:
            - enriched_archiviste_prompt: Prompt archiviste enrichi
            - temporal_data: Données temporelles brutes
            - should_alert_main_ai: Si l'IA principale doit être informée
        """
        if not self.is_active:
            return {
                "enriched_archiviste_prompt": archiviste_prompt,
                "temporal_data": None,
                "temporal_summary": "Extension désactivée"
            }
        
        # Mesurer délais temporels
        measurement = self.sensor.register_message(user_message)
        self.last_measurement = measurement
        
        # Enrichir prompt archiviste si configuré
        enriched_prompt = archiviste_prompt
        if self.config.enrich_archiviste_prompt and archiviste_prompt:
            enriched_prompt = self.enricher.enrich_archiviste_prompt(
                archiviste_prompt, measurement, user_message
            )
        
        if self.debug:
            self._debug_print_processing(measurement)
        
        return {
            "enriched_archiviste_prompt": enriched_prompt,
            "temporal_data": measurement,
            "temporal_summary": self._get_temporal_summary()
        }
    
    async def analyze_with_archiviste(self, temporal_data, archiviste_controller):
        """
        Demande à l'Archiviste d'analyser les données temporelles et générer une instruction.
        
        Args:
            temporal_data: TemporalMeasurement avec les données temporelles
            archiviste_controller: AIController de l'Archiviste
            
        Returns:
            str: Instruction contextualisée générée par l'Archiviste, ou None
        """
        try:
            # Charger les instructions temporelles pour l'Archiviste
            instructions_content = self._load_archiviste_instructions()
            
            # Construire le prompt d'analyse
            delay_seconds = temporal_data.delay_since_last
            avg_delay = temporal_data.average_delay or "non calculé"
            
            # Gérer le cas du premier message
            if delay_seconds is None:
                delay_info = "Premier message de la session"
            else:
                delay_info = f"{delay_seconds:.1f} secondes"
            
            analysis_prompt = f"""{instructions_content}

DONNÉES TEMPORELLES ACTUELLES :
- Délai depuis dernier message : {delay_info}
- Nombre de messages session : {temporal_data.message_count}
- Délai moyen session : {avg_delay}
- Heure actuelle : {temporal_data.current_time_str}
- Durée session : {temporal_data.session_duration:.0f} secondes

MISSION CRITIQUE : Génère une DIRECTIVE COMPORTEMENTALE pour l'IA principale.

Si pattern temporel détecté → UNE instruction directe (ex: "Sois plus patiente, ralentis le rythme")
Si rythme normal → Réponds exactement "NORMAL"

INTERDICTION : Ne fais PAS d'analyse ou d'observation, génère une INSTRUCTION DIRECTE.

RÉPONSE :"""

            if self.debug:
                print(f"[TemporalGuardian] 🧠 Envoi analyse à l'Archiviste...")
            
            # Appel à l'Archiviste pour analyse
            response, error = await archiviste_controller.call_chat_api(
                messages=[{"role": "user", "content": analysis_prompt}],
                max_tokens=150,
                context_length=2048,
                temperature=0.7,
                is_json=False
            )
            
            if error:
                print(f"[TemporalGuardian] ❌ Erreur appel Archiviste: {error}")
                return None
                
            if response and response.strip() != "NORMAL":
                return response.strip()
            else:
                return None
                
        except Exception as e:
            print(f"[TemporalGuardian] ❌ Erreur analyse Archiviste: {e}")
            return None
    
    def _load_archiviste_instructions(self) -> str:
        """Charge les instructions temporelles pour l'Archiviste (priorité settings.json)."""
        try:
            # PRIORITÉ 1: Lire depuis settings.json
            import sys
            ogma_ng = sys.modules.get('ogma_ng')
            if ogma_ng and hasattr(ogma_ng, '_ensure_settings_manager'):
                sm = ogma_ng._ensure_settings_manager()
                if sm:
                    instructions = sm.settings.get('prompts', {}).get('temporal_guardian')
                    if instructions:
                        print(f"[TemporalGuardian] ✅ Instructions chargées depuis settings.json")
                        return instructions
            
            # FALLBACK: Lire depuis fichier .md
            from pathlib import Path
            instructions_path = Path(__file__).parent / "INSTRUCTIONS_ARCHIVISTE_TEMPOREL.md"
            if instructions_path.exists():
                print(f"[TemporalGuardian] ⚠️ Fallback fichier .md (settings.json manquant)")
                return instructions_path.read_text(encoding='utf-8')
            else:
                # Instructions par défaut si fichier manquant
                print(f"[TemporalGuardian] ⚠️ Utilisation instructions par défaut (fichier .md introuvable)")
                return """Tu es l'Archiviste d'OGMA. Analyse les patterns temporels utilisateur :
- FATIGUE : délais croissants, ralentissement
- RÉFLEXION : pauses 3min30s-5min après questions complexes  
- ABSENCE : délais >8min, retour en session
- CHANGEMENT RYTHME : variations significatives vs moyenne

Génère une instruction courte pour l'IA principale si nécessaire."""
        except Exception as e:
            print(f"[TemporalGuardian] ⚠️ Erreur chargement instructions: {e}")
            return "Analyse les patterns temporels et génère une instruction si nécessaire."
    
    def reload_instructions(self):
        """Recharge les instructions temporelles à chaud (sans redémarrer OGMA)."""
        try:
            print(f"[TemporalGuardian] 🔄 Rechargement instructions à chaud...")
            # Force le rechargement en appelant directement _load_archiviste_instructions
            # (qui lit toujours depuis settings.json en priorité)
            test_instructions = self._load_archiviste_instructions()
            if test_instructions:
                print(f"[TemporalGuardian] ✅ Instructions rechargées ({len(test_instructions)} chars)")
                return True
            else:
                print(f"[TemporalGuardian] ❌ Échec rechargement (instructions vides)")
                return False
        except Exception as e:
            print(f"[TemporalGuardian] ❌ Erreur rechargement: {e}")
            return False
    
    def _get_temporal_summary(self) -> str:
        """Génère un résumé temporel pour l'archiviste."""
        if not self.last_measurement:
            return "Aucune donnée temporelle disponible"
        
        # Utiliser les mesures récentes pour créer un résumé
        session_stats = self.sensor.get_session_stats()
        
        summary_parts = []
        
        # Durée session
        session_minutes = session_stats["session_duration_minutes"]
        summary_parts.append(f"Session active: {session_minutes:.0f}min")
        
        # Nombre messages
        summary_parts.append(f"{session_stats['total_messages']} messages")
        
        # Rythme moyen
        if session_stats["average_delay"]:
            avg_seconds = session_stats["average_delay"]
            if avg_seconds < 60:
                summary_parts.append(f"Rythme moyen: {avg_seconds:.0f}s")
            else:
                summary_parts.append(f"Rythme moyen: {avg_seconds/60:.1f}min")
        
        return " | ".join(summary_parts)
    
    def reset_session(self):
        """Redémarre une nouvelle session temporelle."""
        self.sensor.reset_session()
        self.last_measurement = None
        
        if self.debug:
            print("[TemporalGuardian] Session redémarrée")
    
    def should_reset_session(self) -> bool:
        """Vérifie si une nouvelle session doit être créée."""
        return self.sensor.is_new_session_needed(self.config.session_timeout_minutes)
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Retourne statistiques de session pour monitoring."""
        stats = self.sensor.get_session_stats()
        stats.update({
            "extension_active": self.is_active,
            "config": self.config.to_dict(),
            "last_measurement": self.last_measurement.__dict__ if self.last_measurement else None
        })
        return stats
    
    def enable(self):
        """Active l'extension."""
        self.is_active = True
        if self.debug:
            print("[TemporalGuardian] Extension activée")
    
    def disable(self):
        """Désactive l'extension."""
        self.is_active = False
        if self.debug:
            print("[TemporalGuardian] Extension désactivée")
    
    def update_config(self, new_config: TemporalGuardianConfig):
        """Met à jour la configuration de l'extension."""
        self.config = new_config
        self.enricher = ArchivisteEnricher(self.config, debug=self.debug)
        self.is_active = self.config.enabled
        
        if self.debug:
            print("[TemporalGuardian] Configuration mise à jour")
    
    def _debug_print_processing(self, measurement: TemporalMeasurement):
        """Debug du traitement."""
        delay_str = f"{measurement.delay_since_last:.1f}s" if measurement.delay_since_last else "Premier message"
        print(f"[TemporalGuardian] 📊 Msg #{measurement.message_count} | Délai: {delay_str}")


# Interface pour intégration OGMA
def create_temporal_guardian(config_dict: Optional[Dict] = None, debug: bool = False) -> TemporalGuardian:
    """
    Factory function pour créer une instance TemporalGuardian.
    
    Usage dans OGMA:
        from extensions.temporal_guardian import create_temporal_guardian
        
        guardian = create_temporal_guardian(debug=True)
        result = guardian.process_user_message(user_message, archiviste_prompt)
    """
    config = None
    if config_dict:
        config = TemporalGuardianConfig.from_dict(config_dict)
    
    return TemporalGuardian(config, debug)


# Test de l'extension si exécuté directement
if __name__ == "__main__":
    print("Test de l'extension Temporal Guardian")
    print("=" * 40)
    
    import time
    
    # Créer guardian
    guardian = create_temporal_guardian(debug=True)
    
    # Simuler interaction
    archiviste_base = "Analysez ce message utilisateur et mémorisez les éléments importants."
    
    print("\n1. Premier message:")
    result1 = guardian.process_user_message("Bonjour Luna", archiviste_base)
    print("Prompt enrichi:", result1["enriched_archiviste_prompt"])
    
    print("\n2. Message rapide:")
    time.sleep(1)
    result2 = guardian.process_user_message("Ça va ?", archiviste_base)
    print("Prompt enrichi:", result2["enriched_archiviste_prompt"])
    
    print("\n3. Message avec délai:")
    time.sleep(5)
    result3 = guardian.process_user_message("Tu peux m'aider ?", archiviste_base)
    print("Prompt enrichi:", result3["enriched_archiviste_prompt"])
    
    print("\n4. Stats session:")
    stats = guardian.get_session_stats()
    print("Stats:", stats["session_duration_minutes"], "min,", stats["total_messages"], "messages")