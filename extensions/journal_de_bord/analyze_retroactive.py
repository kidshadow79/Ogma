"""
OGMA - Journal de Bord v2.0
Script d'analyse rétroactive des dernières conversations

Analyse les N dernières conversations pour créer des états actifs
qui auraient dû être détectés automatiquement.

NOTE: Ce script doit être lancé depuis OGMA en fonctionnement, 
car il nécessite l'Archiviste initialisé.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Ajouter le dossier parent au path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


async def analyze_last_conversations(n_conversations: int = 3):
    """
    Analyse les N dernières conversations et crée des états actifs
    
    Args:
        n_conversations: Nombre de conversations à analyser (défaut: 3)
    """
    try:
        print("=" * 70)
        print(f"ANALYSE RÉTROACTIVE - {n_conversations} DERNIÈRES CONVERSATIONS")
        print("=" * 70)
        
        # Vérifier que l'extension Journal est disponible
        print("\n[INIT] Vérification extension Journal...")
        try:
            from extensions.journal_de_bord import get_journal_available, get_live_detector
            
            if not get_journal_available():
                print("[ERROR] ❌ Extension Journal non disponible")
                print("[INFO] 💡 Lancez OGMA et utilisez cette fonction depuis l'interface")
                return
            
            print("[OK] ✅ Extension Journal disponible")
            
        except ImportError as e:
            print(f"[ERROR] ❌ Impossible d'importer l'extension Journal: {e}")
            print("[INFO] 💡 Assurez-vous que OGMA est lancé")
            return
        
        # Récupérer le détecteur live (déjà initialisé avec Archiviste)
        print("[INIT] Récupération LiveStateDetector...")
        detector = get_live_detector()
        
        if not detector:
            print("[ERROR] ❌ LiveStateDetector non disponible")
            print("[INFO] 💡 L'Archiviste doit être configuré dans OGMA")
            return
        
        print("[OK] ✅ LiveStateDetector opérationnel")
        
        # Import modules Journal
        from extensions.journal_de_bord.json_manager import JSONManager
        from extensions.journal_de_bord.config import get_journal_config
        # Import modules Journal
        from extensions.journal_de_bord.json_manager import JSONManager
        from extensions.journal_de_bord.config import get_journal_config
        
        print("[INIT] Chargement configuration...")
        config = get_journal_config()
        
        print("[INIT] Initialisation JSONManager...")
        json_manager = JSONManager(config)
        
        # Récupération des entrées
        print(f"\n[SEARCH] Récupération des {n_conversations} dernières conversations...")
        all_entries = json_manager.get_all_entries_sorted()
        
        if not all_entries:
            print("[ERROR] Aucune entrée trouvée dans le journal")
            return
        
        last_entries = all_entries[-n_conversations:] if len(all_entries) >= n_conversations else all_entries
        
        print(f"[OK] {len(last_entries)} entrées à analyser")
        print("-" * 70)
        
        # Analyse chaque entrée
        total_new = 0
        total_resolved = 0
        
        for idx, entry in enumerate(last_entries, 1):
            print(f"\n[{idx}/{len(last_entries)}] Analyse conversation: {entry.get('timestamp', 'date inconnue')}")
            print(f"  Résumé: {entry.get('summary', 'N/A')[:80]}...")
            
            # Simulation message utilisateur depuis résumé
            # (Dans un vrai cas, on aurait la conversation complète)
            user_message = entry.get('summary', '')
            ai_response = "Conversation capturée dans le journal"
            
            # Analyse avec le détecteur
            result = await detector.analyze_message_pair(
                user_message=user_message,
                ai_response=ai_response,
                conversation_context=[]
            )
            
            # Affichage résultats
            if result["new_states"]:
                print(f"  ✨ {len(result['new_states'])} NOUVEAUX états créés")
                total_new += len(result["new_states"])
                for state_id in result["new_states"]:
                    print(f"     → État #{state_id}")
            
            if result["resolved_states"]:
                print(f"  ✅ {len(result['resolved_states'])} états résolus")
                total_resolved += len(result["resolved_states"])
            
            if result["updated_states"]:
                print(f"  🔄 {len(result['updated_states'])} états mis à jour")
            
            if not any([result["new_states"], result["resolved_states"], result["updated_states"]]):
                print("  ⚪ Aucun changement détecté")
        
        # Rapport final
        print("\n" + "=" * 70)
        print("RAPPORT FINAL")
        print("=" * 70)
        print(f"Conversations analysées: {len(last_entries)}")
        print(f"Nouveaux états créés:    {total_new}")
        print(f"États résolus:           {total_resolved}")
        
        # Affichage états actifs finaux
        print("\n[ÉTATS ACTIFS FINAUX]")
        current_states = json_manager.get_active_states()
        unresolved = [s for s in current_states.get("states", []) if not s.get("resolved", False)]
        
        if unresolved:
            print(f"\n{len(unresolved)} état(s) actif(s):")
            for state in unresolved:
                print(f"  #{state['state_id']} [{state['category']}] {state['importance'].upper()}")
                print(f"     {state['description']}")
                print(f"     Créé: {state['created_at'][:10]}")
        else:
            print("Aucun état actif")
        
        print("\n✅ Analyse terminée")
        
    except Exception as e:
        print(f"\n[ERROR] Erreur analyse rétroactive: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyse rétroactive conversations Journal")
    parser.add_argument(
        "-n", "--number",
        type=int,
        default=3,
        help="Nombre de conversations à analyser (défaut: 3)"
    )
    
    args = parser.parse_args()
    
    asyncio.run(analyze_last_conversations(args.number))
