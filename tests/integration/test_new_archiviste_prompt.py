"""
Test nouveau prompt Archiviste avec catalogue et sélection souvenirs
"""

from extensions.ego_selector.config import EgoSelectorConfig
import json

# Générer catalogue complet
catalog = EgoSelectorConfig.get_ego_catalog()

print(f"\n📊 CATALOGUE GÉNÉRÉ: {len(catalog)} souvenirs\n")

# Simuler souvenirs récents
recent_memories = []

# Formater prompt
prompt = EgoSelectorConfig.DEFAULT_ARCHIVISTE_PROMPT.format(
    user_message="Dis-moi 5 choses que tu aimes et 5 choses que tu n'aimes pas",
    conversation_context="Conversation amicale",
    ego_catalog_json=json.dumps(catalog, indent=2, ensure_ascii=False),
    recent_memories=json.dumps(recent_memories, ensure_ascii=False) if recent_memories else "Aucun"
)

print("=" * 80)
print("NOUVEAU PROMPT ARCHIVISTE:")
print("=" * 80)
print(prompt[:2000])  # Afficher premiers 2000 chars
print("\n... (prompt complet: {} chars)".format(len(prompt)))

# Vérifier placeholders
print("\n✅ VÉRIFICATIONS:")
print(f"   - Catalogue inclus: {'ego_catalog_json' not in prompt}")
print(f"   - Souvenirs récents inclus: {'recent_memories' not in prompt}")
print(f"   - Exemples concrets: {prompt.count('📌')}")
print(f"   - Format JSON défini: {'selected_memories' in prompt}")
print(f"   - Limite 5 par catégorie: {'MAXIMUM 5' in prompt}")

print(f"\n📏 TAILLE PROMPT: {len(prompt)} chars (~{len(prompt)/250:.0f} tokens)")
