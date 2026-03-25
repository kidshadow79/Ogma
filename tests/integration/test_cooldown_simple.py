"""
Test simple du système cooldown Capability Advisor
"""
import sys
from extensions.capability_advisor.config import CapabilityAdvisorConfig

print("=" * 60)
print("TEST COOLDOWN CAPABILITY ADVISOR - SIMPLE")
print("=" * 60)

# 1. Test configuration
config = CapabilityAdvisorConfig()
cooldown_value = config.config.get('cooldown_messages')

print(f"\n📋 Configuration chargée:")
print(f"  - cooldown_messages: {cooldown_value}")
print(f"  - Constante COOLDOWN_MESSAGES: {config.COOLDOWN_MESSAGES}")

# 2. Vérification valeur
if cooldown_value == 3:
    print("\n✅ SUCCÈS: Cooldown configuré à 3 messages minimum")
elif cooldown_value is None:
    print("\n❌ ERREUR: cooldown_messages manquant dans config!")
    sys.exit(1)
else:
    print(f"\n⚠️ ATTENTION: cooldown_messages = {cooldown_value} (attendu: 3)")

# 3. Simulation compteur messages
print("\n" + "=" * 60)
print("SIMULATION COOLDOWN (3 messages minimum)")
print("=" * 60)

message_counter = 0
last_suggestion_at = -99
cooldown_messages = 3

for i in range(1, 6):
    message_counter += 1
    messages_since_last = message_counter - last_suggestion_at
    
    print(f"\nMessage #{message_counter}:")
    print(f"  - Messages depuis dernière suggestion: {messages_since_last}")
    
    if messages_since_last < cooldown_messages:
        print(f"  ⏸️ COOLDOWN ACTIF ({messages_since_last}/{cooldown_messages})")
        print(f"  ➡️ Pas d'analyse Archiviste")
    else:
        print(f"  ✅ COOLDOWN OK ({messages_since_last}/{cooldown_messages})")
        print(f"  ➡️ Analyse Archiviste autorisée")
        # Simuler suggestion au message 1 et 4
        if i in [1, 4]:
            last_suggestion_at = message_counter
            print(f"  🎯 Suggestion faite au message #{message_counter}")

print("\n" + "=" * 60)
print("RÉSUMÉ ATTENDU:")
print("=" * 60)
print("Message #1: ✅ Analyse (premier message)")
print("Message #2: ⏸️ Cooldown (1/3)")
print("Message #3: ⏸️ Cooldown (2/3)")
print("Message #4: ✅ Analyse (3/3 → eligible)")
print("Message #5: ⏸️ Cooldown (1/3)")
print("=" * 60)
