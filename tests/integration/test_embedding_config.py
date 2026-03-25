"""Test rapide de la configuration embedding après corrections."""
from core_logic import SettingsManager
from pathlib import Path

sm = SettingsManager(Path('data/settings.json'))
emb = sm.settings['embedding_api']

print("=" * 60)
print("CONFIGURATION EMBEDDING APRÈS CORRECTIONS")
print("=" * 60)
print(f"Provider: {emb.get('provider')}")
print(f"Model: {emb.get('api_model')}")
print(f"API Key: {emb.get('api_key')[:15]}...")
print(f"Backend Type: {emb.get('backend_type')}")
print("=" * 60)

if emb.get('api_model') == 'mistral-embed':
    print("✅ Configuration embedding CORRECTE (mistral-embed)")
else:
    print(f"❌ Configuration embedding INCORRECTE: '{emb.get('api_model')}'")
