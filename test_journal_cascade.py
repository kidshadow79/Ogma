# Test du système de cascade journal
# Valide que les dernières conversations sont bien récupérées peu importe leur date

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from extensions.journal_de_bord.json_manager import JSONManager
from extensions.journal_de_bord.context_provider import ContextProvider
from extensions.journal_de_bord.config import JournalConfig

def test_cascade():
    """Test de la cascade intelligente"""
    print("=" * 80)
    print("TEST SYSTÈME CASCADE JOURNAL")
    print("=" * 80)
    
    # Initialisation
    config = JournalConfig()
    settings = config.get_ui_settings()
    json_manager = JSONManager(settings)
    context_provider = ContextProvider(json_manager, config)  # Passer config, pas settings
    
    print("\n1️⃣ TEST get_all_entries_sorted()")
    print("-" * 80)
    
    all_entries = json_manager.get_all_entries_sorted()
    print(f"✅ Total entrées récupérées: {len(all_entries)}")
    
    if all_entries:
        first = all_entries[0]
        last = all_entries[-1]
        print(f"📅 Première entrée: {first.get('timestamp', 'N/A')[:10]}")
        print(f"📅 Dernière entrée: {last.get('timestamp', 'N/A')[:10]}")
        print(f"📝 Résumé dernière: {last.get('summary', 'N/A')[:100]}...")
    
    print("\n2️⃣ TEST get_recent_context_with_cascade()")
    print("-" * 80)
    
    context = context_provider.get_recent_context_with_cascade(max_entries=3)
    
    if context:
        print(f"✅ Contexte généré: {len(context)} caractères")
        print("\n📋 APERÇU DU CONTEXTE:")
        print("-" * 80)
        print(context[:500] + ("..." if len(context) > 500 else ""))
        print("-" * 80)
    else:
        print("⚠️ Aucun contexte généré (journal vide)")
    
    print("\n3️⃣ COMPARAISON ANCIEN VS NOUVEAU")
    print("-" * 80)
    
    # Ancien système (daily_context)
    old_context = context_provider.get_daily_context()
    print(f"📊 Ancien système (daily): {len(old_context)} chars")
    
    # Nouveau système (cascade)
    new_context = context_provider.get_recent_context_with_cascade(max_entries=3)
    print(f"📊 Nouveau système (cascade): {len(new_context)} chars")
    
    print(f"\n💡 Différence: {len(new_context) - len(old_context):+d} chars")
    
    if len(new_context) > len(old_context):
        print("✅ CASCADE FONCTIONNE ! Plus de contexte récupéré")
    elif len(new_context) == len(old_context):
        print("⚠️ Même résultat (conversations aujourd'hui ?)")
    else:
        print("❌ Problème détecté")
    
    print("\n" + "=" * 80)
    print("TEST TERMINÉ")
    print("=" * 80)

if __name__ == "__main__":
    try:
        test_cascade()
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
