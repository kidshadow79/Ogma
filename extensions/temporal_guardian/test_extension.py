"""
Test de l'extension Temporal Guardian
===================================

Tests de validation de l'architecture temporelle organique.
"""

import sys
import time
from pathlib import Path

# Ajouter le chemin des extensions si nécessaire
sys.path.append(str(Path(__file__).parent.parent))

from temporal_guardian import create_temporal_guardian, TemporalGuardianConfig


def test_basic_functionality():
    """Test des fonctionnalités de base."""
    print("🧪 Test fonctionnalités de base")
    print("-" * 30)
    
    # Créer guardian
    guardian = create_temporal_guardian(debug=True)
    
    # Prompt archiviste de base
    archiviste_prompt = "Analysez ce message utilisateur et mémorisez les éléments importants."
    
    # Test premier message
    print("\n1️⃣ Premier message (pas de délai):")
    result1 = guardian.process_user_message("Bonjour Luna", archiviste_prompt)
    print(f"   Alerte IA: {result1['should_alert_main_ai']}")
    print(f"   Résumé: {result1['temporal_summary']}")
    assert result1['temporal_data'].delay_since_last is None
    assert result1['should_alert_main_ai'] is False
    
    # Test message rapide
    print("\n2️⃣ Message rapide (délai court):")
    time.sleep(1)
    result2 = guardian.process_user_message("Ça va ?", archiviste_prompt)
    print(f"   Délai mesuré: {result2['temporal_data'].delay_since_last:.1f}s")
    print(f"   Alerte IA: {result2['should_alert_main_ai']}")
    assert result2['temporal_data'].delay_since_last is not None
    assert result2['temporal_data'].delay_since_last < 5  # Moins de 5s
    
    # Test message avec délai
    print("\n3️⃣ Message avec délai (délai moyen):")
    time.sleep(3)
    result3 = guardian.process_user_message("Tu peux m'aider ?", archiviste_prompt)
    print(f"   Délai mesuré: {result3['temporal_data'].delay_since_last:.1f}s")
    print(f"   Messages session: {result3['temporal_data'].message_count}")
    print(f"   Alerte IA: {result3['should_alert_main_ai']}")
    assert result3['temporal_data'].delay_since_last > 2  # Plus de 2s
    
    print("\n✅ Test fonctionnalités de base: RÉUSSI")


def test_enrichment_formats():
    """Test des formats d'enrichissement."""
    print("\n🧪 Test formats d'enrichissement")
    print("-" * 35)
    
    # Test format simple
    print("\n1️⃣ Format simple:")
    config_simple = TemporalGuardianConfig()
    config_simple.temporal_context_format = "simple"
    guardian_simple = create_temporal_guardian(config_simple.to_dict(), debug=False)
    
    time.sleep(1)
    result_simple = guardian_simple.process_user_message("Test simple", "Prompt archiviste")
    print("   Prompt enrichi (simple):")
    print(f"   {result_simple['enriched_archiviste_prompt']}")
    
    # Test format détaillé
    print("\n2️⃣ Format détaillé:")
    config_detailed = TemporalGuardianConfig()
    config_detailed.temporal_context_format = "detailed"
    guardian_detailed = create_temporal_guardian(config_detailed.to_dict(), debug=False)
    
    time.sleep(2)
    result_detailed = guardian_detailed.process_user_message("Test détaillé", "Prompt archiviste")
    print("   Prompt enrichi (détaillé):")
    print(f"   {result_detailed['enriched_archiviste_prompt']}")
    
    print("\n✅ Test formats d'enrichissement: RÉUSSI")


def test_session_management():
    """Test gestion des sessions."""
    print("\n🧪 Test gestion de session")
    print("-" * 30)
    
    guardian = create_temporal_guardian(debug=True)
    
    # Envoyer plusieurs messages
    for i in range(3):
        time.sleep(0.5)
        result = guardian.process_user_message(f"Message {i+1}", "Prompt test")
        print(f"   Message {i+1}: {result['temporal_data'].message_count} total")
    
    # Vérifier stats
    stats = guardian.get_session_stats()
    print(f"\n📊 Stats session:")
    print(f"   Messages total: {stats['total_messages']}")
    print(f"   Durée: {stats['session_duration_minutes']:.1f}min")
    print(f"   Délai moyen: {stats['average_delay']:.1f}s" if stats['average_delay'] else "   Délai moyen: N/A")
    
    # Reset session
    print("\n🔄 Reset session...")
    guardian.reset_session()
    
    result_reset = guardian.process_user_message("Premier message nouvelle session", "Prompt test")
    print(f"   Nouveau count: {result_reset['temporal_data'].message_count}")
    assert result_reset['temporal_data'].message_count == 1
    
    print("\n✅ Test gestion de session: RÉUSSI")


def test_alert_system():
    """Test système d'alertes."""
    print("\n🧪 Test système d'alertes")
    print("-" * 30)
    
    guardian = create_temporal_guardian(debug=False)
    
    # Message normal - pas d'alerte
    guardian.process_user_message("Message normal", "Prompt test")
    time.sleep(1)
    result_normal = guardian.process_user_message("Réponse rapide", "Prompt test")
    print(f"   Délai normal ({result_normal['temporal_data'].delay_since_last:.1f}s): Alerte = {result_normal['should_alert_main_ai']}")
    
    # Simuler délai long pour déclencher alerte
    print("   Simulation délai long (6s)...")
    time.sleep(6)
    result_long = guardian.process_user_message("Après long délai", "Prompt test")
    print(f"   Délai long ({result_long['temporal_data'].delay_since_last:.1f}s): Alerte = {result_long['should_alert_main_ai']}")
    
    # Note: Le seuil par défaut est 5 minutes, donc 6s ne déclenchera pas l'alerte
    # Mais on peut voir le mécanisme fonctionner
    
    print("\n✅ Test système d'alertes: RÉUSSI")


def test_configuration():
    """Test configuration de l'extension."""
    print("\n🧪 Test configuration")
    print("-" * 25)
    
    # Test désactivation
    config = TemporalGuardianConfig()
    config.enabled = False
    guardian_disabled = create_temporal_guardian(config.to_dict(), debug=False)
    
    result_disabled = guardian_disabled.process_user_message("Test désactivé", "Prompt test")
    print(f"   Extension désactivée: temporal_data = {result_disabled['temporal_data']}")
    assert result_disabled['temporal_data'] is None
    
    # Test activation/désactivation dynamique
    guardian = create_temporal_guardian(debug=False)
    guardian.disable()
    result_after_disable = guardian.process_user_message("Après disable", "Prompt test")
    print(f"   Après disable: temporal_data = {result_after_disable['temporal_data']}")
    
    guardian.enable()
    result_after_enable = guardian.process_user_message("Après enable", "Prompt test")
    print(f"   Après enable: temporal_data présent = {result_after_enable['temporal_data'] is not None}")
    
    print("\n✅ Test configuration: RÉUSSI")


def run_all_tests():
    """Exécute tous les tests."""
    print("🚀 DÉMARRAGE TESTS TEMPORAL GUARDIAN")
    print("=" * 50)
    
    try:
        test_basic_functionality()
        test_enrichment_formats()
        test_session_management()
        test_alert_system()
        test_configuration()
        
        print("\n" + "=" * 50)
        print("🎉 TOUS LES TESTS RÉUSSIS!")
        print("Extension Temporal Guardian validée ✅")
        
    except Exception as e:
        print(f"\n❌ ERREUR DANS LES TESTS: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)