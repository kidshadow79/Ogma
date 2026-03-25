"""Test du système de cooldown Capability Advisor"""
import sys
sys.path.insert(0, 'c:/IA/OGMA')

from extensions.capability_advisor.config import CapabilityAdvisorConfig

print("=" * 60)
print("TEST COOLDOWN CAPABILITY ADVISOR")
print("=" * 60)

config = CapabilityAdvisorConfig()

print(f"\nConfiguration par défaut:")
print(f"  - Cooldown messages: {config.config.get('cooldown_messages', 'NON DÉFINI')}")
print(f"  - Confidence threshold: {config.config.get('confidence_threshold')}")
print(f"  - LED timeout: {config.config.get('led_timeout')}s")

print(f"\nConstantes classe:")
print(f"  - COOLDOWN_MESSAGES: {config.COOLDOWN_MESSAGES}")
print(f"  - CONFIDENCE_THRESHOLD_GLOBAL: {config.CONFIDENCE_THRESHOLD_GLOBAL}")

print("\n" + "=" * 60)
print("RÉSULTAT:")
if config.config.get('cooldown_messages') == 3:
    print("✅ Cooldown configuré correctement (3 messages minimum)")
else:
    print(f"❌ Cooldown incorrect: {config.config.get('cooldown_messages')}")
print("=" * 60)
