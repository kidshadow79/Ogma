"""
Configuration pytest pour tests d'intégration

Charge automatiquement les variables d'environnement depuis .env
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Charger .env depuis la racine du projet
project_root = Path(__file__).parent.parent.parent
env_path = project_root / ".env"

if env_path.exists():
    load_dotenv(env_path)
    print(f"[PYTEST-CONFIG] .env chargé depuis: {env_path}")
else:
    print(f"[PYTEST-CONFIG] ⚠️ .env non trouvé: {env_path}")

# Vérifier clés API chargées
api_keys_status = {
    "GROK": "OK" if os.getenv("GROK_API_KEY") else "MANQUANT",
    "MISTRAL": "OK" if os.getenv("MISTRAL_API_KEY") else "MANQUANT",
    "OPENAI": "OK" if os.getenv("OPENAI_API_KEY") else "MANQUANT",
    "ANTHROPIC": "OK" if os.getenv("ANTHROPIC_API_KEY") else "MANQUANT",
}
print(f"[PYTEST-CONFIG] API Keys: {api_keys_status}")
