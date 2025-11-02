import sys
sys.path.insert(0, 'c:/IA/OGMA')

from extensions.journal_de_bord.context_provider import ContextProvider
from extensions.journal_de_bord.json_manager import JSONManager
from extensions.journal_de_bord.config import get_journal_config

# Configuration
config = get_journal_config()

# Initialiser les managers
json_manager = JSONManager(config=config)
context_provider = ContextProvider(json_manager=json_manager, config=config)

# Générer le contexte pour aujourd'hui
context = context_provider.get_daily_context(target_date="2025-10-31", max_entries=3)

print("=" * 80)
print("CONTEXTE JOURNAL GÉNÉRÉ:")
print("=" * 80)
print(context)
print("=" * 80)
print(f"\nLongueur: {len(context)} caractères")
