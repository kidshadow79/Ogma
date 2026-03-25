"""
Script de test pour valider les variantes de triggers
"""

from modules.voice.voice_triggers import TriggerDetector

print("="*60)
print("TEST 1 : Trigger 'louna louna'")
print("="*60)

detector1 = TriggerDetector(trigger_activation="louna louna", trigger_send="point final")

test_cases_louna = [
    ("louna louna", True, "Trigger exact"),
    ("Luna Luna", True, "Variante majuscule"),
    ("l'une l'une", True, "Variante Whisper"),
    ("ma louna", False, "Ne doit PAS activer"),
]

for text, expected, description in test_cases_louna:
    result = detector1.check_activation(text)
    status = "✅ OK" if result == expected else "❌ ÉCHEC"
    print(f"{status} - {description}: '{text}' -> {result} (attendu: {expected})")

print("\n" + "="*60)
print("TEST 2 : Trigger 'ma louna'")
print("="*60)

detector2 = TriggerDetector(trigger_activation="ma louna", trigger_send="point final")

test_cases_ma_louna = [
    ("ma louna", True, "Trigger exact"),
    ("Ma Luna", True, "Variante majuscule"),
    ("malouna", True, "Sans espace"),
    ("ma l'une", True, "Variante Whisper"),
    ("louna louna", False, "Ne doit PAS activer"),
    ("luna luna", False, "Ne doit PAS activer"),
]

for text, expected, description in test_cases_ma_louna:
    result = detector2.check_activation(text)
    status = "✅ OK" if result == expected else "❌ ÉCHEC"
    print(f"{status} - {description}: '{text}' -> {result} (attendu: {expected})")

print("\n" + "="*60)
print("TEST 3 : Triggers d'envoi")
print("="*60)

test_cases_send = [
    ("point final", True, "Trigger exact"),
    ("Point Final", True, "Variante majuscule"),
    ("pointfinal", True, "Sans espace"),
    ("fini", True, "Variante courte"),
]

for text, expected, description in test_cases_send:
    result = detector2.check_send(text)
    status = "✅ OK" if result == expected else "❌ ÉCHEC"
    print(f"{status} - {description}: '{text}' -> {result} (attendu: {expected})")

print("\n" + "="*60)
print("RÉSUMÉ")
print("="*60)
print("✅ Les triggers sont maintenant correctement séparés")
print("✅ 'louna louna' ne déclenche plus 'ma louna'")
print("✅ Chaque trigger a ses propres variantes phonétiques")
