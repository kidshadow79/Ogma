"""
Tests Unitaires pour Extension Temporal Guardian
================================================

Tests pour les composants TemporalSensor, ArchivisteEnricher et TemporalGuardian.

Usage:
    pytest tests/unit/test_temporal_guardian_strict.py -v
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
import sys

# Ajouter le répertoire racine au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from extensions.temporal_guardian import (
    TemporalSensor,
    TemporalMeasurement,
    ArchivisteEnricher,
    TemporalGuardian,
    TemporalGuardianConfig,
    create_temporal_guardian
)


# ============================================================================
# TESTS TEMPORALSENSOR - Capteur de Mesure Temporelle
# ============================================================================

class TestTemporalSensor:
    """Tests pour le capteur temporel simple."""
    
    def test_sensor_initialization(self):
        """Test l'initialisation correcte du capteur."""
        sensor = TemporalSensor(debug=False)
        
        assert sensor.message_count == 0
        assert sensor.last_message_time is None
        assert len(sensor.message_delays) == 0
        assert sensor.session_start is not None
    
    def test_register_first_message(self):
        """Test l'enregistrement du premier message (pas de délai)."""
        sensor = TemporalSensor()
        
        measurement = sensor.register_message("Bonjour")
        
        assert measurement.message_count == 1
        assert measurement.delay_since_last is None  # Premier message
        assert measurement.average_delay is None  # Pas assez de données
        assert measurement.session_duration >= 0
        assert measurement.current_time_str is not None
        assert sensor.message_count == 1
    
    def test_register_second_message_with_delay(self):
        """Test l'enregistrement du 2ème message avec calcul de délai."""
        import time
        sensor = TemporalSensor()
        
        # Premier message
        sensor.register_message("Message 1")
        
        # Attente courte
        time.sleep(0.1)
        
        # Second message
        measurement = sensor.register_message("Message 2")
        
        assert measurement.message_count == 2
        assert measurement.delay_since_last is not None
        assert measurement.delay_since_last >= 0.1  # Au moins le sleep
        assert len(sensor.message_delays) == 1
        assert measurement.average_delay is None  # Pas encore 3 mesures
    
    def test_average_delay_calculation(self):
        """Test le calcul de la moyenne des délais après 3+ messages."""
        import time
        sensor = TemporalSensor()
        
        # 3 messages avec délais
        sensor.register_message("Message 1")
        time.sleep(0.05)
        sensor.register_message("Message 2")
        time.sleep(0.05)
        measurement = sensor.register_message("Message 3")
        
        assert measurement.message_count == 3
        assert len(sensor.message_delays) == 2  # 2 délais mesurés
        assert measurement.average_delay is None  # Besoin 3 délais
        
        # 4ème message → moyenne disponible
        time.sleep(0.05)
        measurement = sensor.register_message("Message 4")
        
        assert measurement.average_delay is not None
        assert measurement.average_delay >= 0.05  # Au moins un sleep
    
    def test_session_duration_tracking(self):
        """Test le suivi de la durée de session."""
        import time
        sensor = TemporalSensor()
        
        # Message immédiat
        m1 = sensor.register_message("Message 1")
        assert m1.session_duration < 1.0  # Moins de 1 seconde
        
        # Message après délai
        time.sleep(0.2)
        m2 = sensor.register_message("Message 2")
        assert m2.session_duration >= 0.2
        assert m2.session_duration > m1.session_duration
    
    def test_get_session_stats(self):
        """Test la récupération des statistiques de session."""
        import time
        sensor = TemporalSensor()
        
        # Créer historique
        sensor.register_message("M1")
        time.sleep(0.05)
        sensor.register_message("M2")
        time.sleep(0.1)
        sensor.register_message("M3")
        
        stats = sensor.get_session_stats()
        
        assert stats["total_messages"] == 3
        assert stats["delays_count"] == 2
        assert stats["average_delay"] is not None
        assert stats["min_delay"] is not None
        assert stats["max_delay"] is not None
        assert stats["session_duration_minutes"] >= 0
    
    def test_reset_session(self):
        """Test le reset de session."""
        import time
        sensor = TemporalSensor()
        
        # Créer historique
        sensor.register_message("M1")
        time.sleep(0.05)
        sensor.register_message("M2")
        
        assert sensor.message_count == 2
        assert len(sensor.message_delays) == 1
        
        # Reset
        sensor.reset_session()
        
        assert sensor.message_count == 0
        assert len(sensor.message_delays) == 0
        assert sensor.last_message_time is None
    
    def test_is_new_session_needed(self):
        """Test la détection de besoin nouvelle session."""
        sensor = TemporalSensor()
        
        # Pas de message → pas besoin nouvelle session
        assert sensor.is_new_session_needed(30) is False
        
        # Message récent → pas besoin
        sensor.register_message("Recent")
        assert sensor.is_new_session_needed(30) is False
        
        # Simuler ancien message (hack pour test)
        sensor.last_message_time = datetime.now() - timedelta(minutes=35)
        assert sensor.is_new_session_needed(30) is True
    
    def test_max_delays_history_limit(self):
        """Test la limitation de l'historique des délais."""
        import time
        sensor = TemporalSensor()
        sensor.max_delays_history = 5  # Limite réduite pour test
        
        # Créer plus de messages que la limite
        for i in range(8):
            sensor.register_message(f"Message {i}")
            time.sleep(0.01)
        
        # Historique doit être limité
        assert len(sensor.message_delays) <= 5


# ============================================================================
# TESTS ARCHIVISTEENRICHER - Enrichissement Prompt Archiviste
# ============================================================================

class TestArchivisteEnricher:
    """Tests pour l'enrichisseur de prompt archiviste."""
    
    def test_enricher_initialization(self):
        """Test l'initialisation de l'enrichisseur."""
        config = TemporalGuardianConfig()
        enricher = ArchivisteEnricher(config, debug=False)
        
        assert enricher.config == config
        assert enricher.debug is False
    
    def test_enrich_archiviste_prompt_first_message(self):
        """Test l'enrichissement pour le premier message (pas de délai)."""
        config = TemporalGuardianConfig()
        enricher = ArchivisteEnricher(config)
        
        measurement = TemporalMeasurement(
            message_timestamp=datetime.now(),
            delay_since_last=None,  # Premier message
            current_time_str="14:30",
            session_duration=5.0,
            message_count=1,
            average_delay=None
        )
        
        base_prompt = "Analyse ce message."
        enriched = enricher.enrich_archiviste_prompt(
            base_prompt, measurement, "Bonjour"
        )
        
        # Vérifier format réel (emojis + texte concis)
        assert "14:30" in enriched
        assert "Premier message" in enriched or "🆕" in enriched
        assert base_prompt in enriched
    
    def test_enrich_archiviste_prompt_with_delay(self):
        """Test l'enrichissement avec délai mesuré."""
        config = TemporalGuardianConfig()
        enricher = ArchivisteEnricher(config)
        
        measurement = TemporalMeasurement(
            message_timestamp=datetime.now(),
            delay_since_last=45.2,  # Délai significatif
            current_time_str="14:35",
            session_duration=120.0,
            message_count=5,
            average_delay=30.5
        )
        
        base_prompt = "Analyse le message utilisateur."
        enriched = enricher.enrich_archiviste_prompt(
            base_prompt, measurement, "J'ai besoin de réfléchir..."
        )
        
        # Vérifier format réel (arrondi à 45s)
        assert "45s" in enriched or "45.2" in enriched
        assert "5 messages" in enriched or "Message" in enriched
        assert "30s" in enriched or "30.5" in enriched  # Moyenne arrondie
        assert base_prompt in enriched
    
    def test_enrich_disabled_returns_original(self):
        """Test que l'enrichissement désactivé retourne prompt original."""
        config = TemporalGuardianConfig()
        config.enrich_archiviste_prompt = False  # Désactiver après init
        enricher = ArchivisteEnricher(config)
        
        measurement = TemporalMeasurement(
            message_timestamp=datetime.now(),
            delay_since_last=10.0,
            current_time_str="14:30",
            session_duration=60.0,
            message_count=3,
            average_delay=12.0
        )
        
        base_prompt = "Prompt original"
        enriched = enricher.enrich_archiviste_prompt(
            base_prompt, measurement, "Test"
        )
        
        # Si config désactivée, devrait retourner prompt original sans modification
        assert enriched == base_prompt
    
    def test_temporal_context_formatting(self):
        """Test le formatage du contexte temporel."""
        config = TemporalGuardianConfig()
        enricher = ArchivisteEnricher(config)
        
        measurement = TemporalMeasurement(
            message_timestamp=datetime.now(),
            delay_since_last=5.8,
            current_time_str="23:45",
            session_duration=1800.0,  # 30 min
            message_count=15,
            average_delay=8.2
        )
        
        enriched = enricher.enrich_archiviste_prompt(
            "Base prompt", measurement, "Message test"
        )
        
        # Vérifier présence infos clés (format réel compact)
        assert "15 messages" in enriched or "15" in enriched
        assert "6s" in enriched or "5.8" in enriched or "5s" in enriched  # Délai arrondi
        assert "8s" in enriched or "8.2" in enriched  # Moyenne arrondie
        assert "23:45" in enriched


# ============================================================================
# TESTS TEMPORALGUARDIAN - Orchestrateur Principal
# ============================================================================

class TestTemporalGuardian:
    """Tests pour l'orchestrateur principal."""
    
    def test_guardian_initialization(self):
        """Test l'initialisation du guardian."""
        guardian = TemporalGuardian(debug=False)
        
        assert guardian.sensor is not None
        assert guardian.enricher is not None
        assert guardian.is_active is True  # Défaut config
        assert guardian.last_measurement is None
    
    def test_guardian_initialization_with_config(self):
        """Test l'initialisation avec config custom."""
        config = TemporalGuardianConfig()
        config.enabled = False
        config.enrich_archiviste_prompt = False
        guardian = TemporalGuardian(config=config)
        
        assert guardian.is_active is False
        assert guardian.config.enrich_archiviste_prompt is False
    
    def test_process_user_message_disabled(self):
        """Test le traitement quand extension désactivée."""
        config = TemporalGuardianConfig()
        config.enabled = False
        guardian = TemporalGuardian(config=config)
        
        result = guardian.process_user_message(
            "Test message",
            "Archiviste prompt"
        )
        
        assert result["enriched_archiviste_prompt"] == "Archiviste prompt"
        assert result["temporal_data"] is None
        assert "should_alert_main_ai" not in result or result.get("should_alert_main_ai") is False
    
    def test_process_user_message_enabled_first_message(self):
        """Test le traitement du premier message."""
        guardian = TemporalGuardian()
        
        result = guardian.process_user_message(
            "Bonjour OGMA",
            "Base prompt archiviste"
        )
        
        assert "enriched_archiviste_prompt" in result
        assert "temporal_data" in result
        assert "temporal_summary" in result
        
        # Données temporelles
        temporal_data = result["temporal_data"]
        assert temporal_data.message_count == 1
        assert temporal_data.delay_since_last is None
        
        # Prompt enrichi (format réel compact)
        enriched = result["enriched_archiviste_prompt"]
        assert "Premier message" in enriched or "🆕" in enriched
        assert "Base prompt archiviste" in enriched
    
    def test_process_user_message_multiple_messages(self):
        """Test le traitement de plusieurs messages successifs."""
        import time
        guardian = TemporalGuardian()
        
        # Premier message
        r1 = guardian.process_user_message("Message 1", "Prompt base")
        assert r1["temporal_data"].message_count == 1
        
        # Second message
        time.sleep(0.1)
        r2 = guardian.process_user_message("Message 2", "Prompt base")
        assert r2["temporal_data"].message_count == 2
        assert r2["temporal_data"].delay_since_last is not None
        assert r2["temporal_data"].delay_since_last >= 0.1
    
    def test_process_without_archiviste_prompt(self):
        """Test le traitement sans prompt archiviste (optionnel)."""
        guardian = TemporalGuardian()
        
        result = guardian.process_user_message("Message test", "")
        
        assert "temporal_data" in result
        assert result["temporal_data"] is not None
        # Prompt vide doit rester vide ou minimal
        assert result["enriched_archiviste_prompt"] == ""
    
    def test_last_measurement_tracking(self):
        """Test que le guardian garde trace de la dernière mesure."""
        guardian = TemporalGuardian()
        
        assert guardian.last_measurement is None
        
        guardian.process_user_message("Test", "Prompt")
        
        assert guardian.last_measurement is not None
        assert isinstance(guardian.last_measurement, TemporalMeasurement)
    
    @pytest.mark.asyncio
    async def test_analyze_with_archiviste_success(self):
        """Test l'analyse avec l'Archiviste (succès)."""
        guardian = TemporalGuardian(debug=False)
        
        # Mock Archiviste controller
        mock_archiviste = AsyncMock()
        mock_archiviste.call_chat_api = AsyncMock(
            return_value=("Sois plus patient, ralentis le rythme", None)
        )
        
        # Créer mesure temporelle
        measurement = TemporalMeasurement(
            message_timestamp=datetime.now(),
            delay_since_last=120.0,  # 2 min de délai
            current_time_str="14:30",
            session_duration=300.0,
            message_count=5,
            average_delay=30.0
        )
        
        # Analyser
        instruction = await guardian.analyze_with_archiviste(
            measurement, mock_archiviste
        )
        
        assert instruction is not None
        assert "patient" in instruction.lower() or "ralentis" in instruction.lower()
        mock_archiviste.call_chat_api.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_with_archiviste_normal_response(self):
        """Test l'analyse retournant NORMAL (pas d'action)."""
        guardian = TemporalGuardian()
        
        mock_archiviste = AsyncMock()
        mock_archiviste.call_chat_api = AsyncMock(
            return_value=("NORMAL", None)
        )
        
        measurement = TemporalMeasurement(
            message_timestamp=datetime.now(),
            delay_since_last=5.0,
            current_time_str="14:30",
            session_duration=60.0,
            message_count=3,
            average_delay=6.0
        )
        
        instruction = await guardian.analyze_with_archiviste(
            measurement, mock_archiviste
        )
        
        assert instruction is None  # NORMAL → pas d'instruction
    
    @pytest.mark.asyncio
    async def test_analyze_with_archiviste_error_handling(self):
        """Test la gestion d'erreur lors de l'analyse."""
        guardian = TemporalGuardian()
        
        mock_archiviste = AsyncMock()
        mock_archiviste.call_chat_api = AsyncMock(
            return_value=(None, "API Error: Connection failed")
        )
        
        measurement = TemporalMeasurement(
            message_timestamp=datetime.now(),
            delay_since_last=10.0,
            current_time_str="14:30",
            session_duration=60.0,
            message_count=2,
            average_delay=None
        )
        
        instruction = await guardian.analyze_with_archiviste(
            measurement, mock_archiviste
        )
        
        assert instruction is None  # Erreur → pas d'instruction
    
    def test_load_archiviste_instructions_file_exists(self):
        """Test le chargement des instructions Archiviste (fichier existe)."""
        guardian = TemporalGuardian()
        
        instructions = guardian._load_archiviste_instructions()
        
        assert instructions is not None
        assert len(instructions) > 0
        # Devrait contenir instructions ou fallback
        assert "temporel" in instructions.lower() or "archiviste" in instructions.lower()
    
    def test_get_temporal_summary(self):
        """Test la génération du résumé temporel."""
        guardian = TemporalGuardian()
        
        # Avant premier message
        summary = guardian._get_temporal_summary()
        assert "Aucune donnée" in summary
        
        # Après message
        guardian.process_user_message("Test", "Prompt")
        summary = guardian._get_temporal_summary()
        assert summary != "Aucune donnée temporelle disponible"


# ============================================================================
# TESTS FACTORY - Fonction create_temporal_guardian
# ============================================================================

class TestTemporalGuardianFactory:
    """Tests pour la fonction factory."""
    
    def test_create_temporal_guardian_defaults(self):
        """Test la création avec paramètres par défaut."""
        guardian = create_temporal_guardian()
        
        assert isinstance(guardian, TemporalGuardian)
        assert guardian.is_active is True
        assert guardian.debug is False
    
    def test_create_temporal_guardian_with_debug(self):
        """Test la création en mode debug."""
        guardian = create_temporal_guardian(debug=True)
        
        assert guardian.debug is True
        assert guardian.sensor.debug is True
        assert guardian.enricher.debug is True
    
    def test_create_temporal_guardian_disabled(self):
        """Test la création avec extension désactivée."""
        # Factory accepte config_dict, pas config object
        config_dict = {"enabled": False}
        guardian = create_temporal_guardian(config_dict=config_dict)
        
        assert guardian.is_active is False


# ============================================================================
# TESTS INTÉGRATION - Workflow Complet
# ============================================================================

class TestTemporalGuardianIntegration:
    """Tests d'intégration du workflow complet."""
    
    def test_full_workflow_single_message(self):
        """Test le workflow complet pour un message unique."""
        guardian = TemporalGuardian()
        
        result = guardian.process_user_message(
            user_message="Bonjour OGMA, comment vas-tu ?",
            archiviste_prompt="Analyse le message de l'utilisateur."
        )
        
        # Vérifications complètes
        assert result["temporal_data"].message_count == 1
        assert result["temporal_data"].delay_since_last is None
        enriched = result["enriched_archiviste_prompt"]
        assert "Premier message" in enriched or "🆕" in enriched
        assert "Analyse le message de l'utilisateur." in enriched
    
    def test_full_workflow_conversation(self):
        """Test le workflow complet pour une conversation."""
        import time
        guardian = TemporalGuardian()
        
        # Message 1
        r1 = guardian.process_user_message("Salut", "Analyse.")
        assert r1["temporal_data"].message_count == 1
        
        # Message 2 (après délai)
        time.sleep(0.15)
        r2 = guardian.process_user_message("Comment ça va ?", "Analyse.")
        assert r2["temporal_data"].message_count == 2
        assert r2["temporal_data"].delay_since_last >= 0.15
        
        # Message 3 (après délai)
        time.sleep(0.1)
        r3 = guardian.process_user_message("Parle-moi d'IA", "Analyse.")
        assert r3["temporal_data"].message_count == 3
        
        # Message 4 (moyenne disponible)
        time.sleep(0.1)
        r4 = guardian.process_user_message("C'est fascinant", "Analyse.")
        assert r4["temporal_data"].average_delay is not None
    
    @pytest.mark.asyncio
    async def test_full_workflow_with_archiviste_analysis(self):
        """Test le workflow complet incluant analyse Archiviste."""
        import time
        guardian = TemporalGuardian()
        
        # Simuler conversation avec délai croissant (fatigue)
        guardian.process_user_message("Message 1", "Prompt")
        time.sleep(0.1)
        guardian.process_user_message("Message 2", "Prompt")
        time.sleep(0.2)
        guardian.process_user_message("Message 3", "Prompt")
        time.sleep(0.3)
        result = guardian.process_user_message("Message 4", "Prompt")
        
        # Mock Archiviste
        mock_archiviste = AsyncMock()
        mock_archiviste.call_chat_api = AsyncMock(
            return_value=("L'utilisateur semble fatigué, suggère une pause", None)
        )
        
        # Analyser pattern
        instruction = await guardian.analyze_with_archiviste(
            result["temporal_data"], mock_archiviste
        )
        
        assert instruction is not None
        assert "fatigué" in instruction.lower() or "pause" in instruction.lower()


# ============================================================================
# TESTS EDGE CASES - Cas Limites
# ============================================================================

class TestTemporalGuardianEdgeCases:
    """Tests des cas limites et situations exceptionnelles."""
    
    def test_very_long_delay(self):
        """Test un délai très long entre messages."""
        import time
        sensor = TemporalSensor()
        
        sensor.register_message("Message 1")
        time.sleep(1.0)  # 1 seconde (simuler long délai)
        measurement = sensor.register_message("Message 2")
        
        assert measurement.delay_since_last >= 1.0
        # Vérifier qu'un délai de 1s est détecté (même si seuil 30min pour vraie session)
        # On teste juste que la mesure est correcte
        assert measurement.delay_since_last < 2.0  # Marge sécurité
    
    def test_rapid_fire_messages(self):
        """Test des messages très rapides successifs."""
        import time
        sensor = TemporalSensor()
        
        delays = []
        for i in range(10):
            m = sensor.register_message(f"Message {i}")
            if m.delay_since_last:
                delays.append(m.delay_since_last)
            time.sleep(0.01)  # Messages très rapides
        
        assert all(d < 0.1 for d in delays)  # Tous < 100ms
        assert sensor.message_count == 10
    
    def test_empty_message_handling(self):
        """Test le traitement de messages vides."""
        guardian = TemporalGuardian()
        
        result = guardian.process_user_message("", "")
        
        assert result["temporal_data"] is not None
        assert result["temporal_data"].message_count == 1
    
    def test_very_long_message(self):
        """Test un message très long."""
        guardian = TemporalGuardian()
        
        long_message = "A" * 10000  # Message 10k caractères
        result = guardian.process_user_message(
            long_message,
            "Analyse ce long message."
        )
        
        assert result["temporal_data"] is not None
        enriched = result["enriched_archiviste_prompt"]
        # Vérifier enrichissement présent (format compact avec emojis)
        assert "🕒" in enriched or "Premier message" in enriched
        assert "Analyse ce long message." in enriched


# ============================================================================
# EXECUTION
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
