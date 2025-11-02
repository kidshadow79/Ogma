#!/usr/bin/env python3
"""
Script de nettoyage des entrées corrompues du Journal de Bord
Supprime les 3 entrées du 31 octobre 2025 avec résumés placeholder identiques
"""

import json
from datetime import datetime
from pathlib import Path

# Chemin du journal
JOURNAL_PATH = Path("extensions/journal_de_bord/data/journal_2025.json")

# IDs des entrées corrompues à supprimer
CORRUPTED_ENTRIES = [
    "entry_20251031_005317",  # 00:53:17 - Résumé placeholder "Journal de Bord extension"
    "entry_20251031_020359",  # 02:03:59 - Résumé placeholder identique
    "entry_20251031_200342",  # 20:03:42 - Résumé placeholder identique
]

def clean_corrupted_entries():
    """Supprime les entrées corrompues du journal"""
    
    print("=" * 80)
    print("NETTOYAGE JOURNAL DE BORD - Suppression entrées corrompues")
    print("=" * 80)
    
    # Vérifier que le fichier existe
    if not JOURNAL_PATH.exists():
        print(f"❌ ERREUR: Fichier non trouvé: {JOURNAL_PATH}")
        return False
    
    # Charger le JSON
    print(f"\n📖 Chargement: {JOURNAL_PATH}")
    with open(JOURNAL_PATH, 'r', encoding='utf-8') as f:
        journal_data = json.load(f)
    
    print(f"✅ Journal chargé: {len(json.dumps(journal_data))} bytes")
    
    # Statistiques avant nettoyage
    total_entries_before = 0
    corrupted_found = []
    
    # Parcourir la structure année > mois > jour
    if "2025" in journal_data:
        year_data = journal_data["2025"]
        
        if "10" in year_data:  # Octobre
            month_data = year_data["10"]
            
            if "31" in month_data:  # 31 octobre
                day_data = month_data["31"]
                entries = day_data.get("entries", [])
                total_entries_before = len(entries)
                
                print(f"\n📅 Entrées du 31 octobre avant nettoyage: {total_entries_before}")
                
                # Identifier les entrées corrompues
                for entry in entries:
                    entry_id = entry.get("entry_id", "")
                    if entry_id in CORRUPTED_ENTRIES:
                        corrupted_found.append(entry_id)
                        summary = entry.get("summary", "")[:100]
                        print(f"\n🔍 TROUVÉ: {entry_id}")
                        print(f"   Résumé: {summary}...")
                        print(f"   conversation_id: {entry.get('conversation_id', 'N/A')}")
                
                # Filtrer les entrées (garder seulement les bonnes)
                clean_entries = [
                    entry for entry in entries 
                    if entry.get("entry_id") not in CORRUPTED_ENTRIES
                ]
                
                # Mettre à jour le jour avec les entrées nettoyées
                day_data["entries"] = clean_entries
                
                # Mettre à jour le total d'entrées du jour
                day_data["total_entries"] = len(clean_entries)
                
                print(f"\n🧹 Entrées du 31 octobre après nettoyage: {len(clean_entries)}")
                print(f"🗑️  Entrées supprimées: {total_entries_before - len(clean_entries)}")
    
    if not corrupted_found:
        print("\n⚠️  ATTENTION: Aucune entrée corrompue trouvée")
        print(f"   Recherchées: {CORRUPTED_ENTRIES}")
        return False
    
    print(f"\n✅ Entrées corrompues identifiées: {len(corrupted_found)}/{len(CORRUPTED_ENTRIES)}")
    
    # Sauvegarder le JSON nettoyé
    print(f"\n💾 Sauvegarde du journal nettoyé...")
    with open(JOURNAL_PATH, 'w', encoding='utf-8') as f:
        json.dump(journal_data, f, ensure_ascii=False, indent=2)
    
    # Vérifier la taille après nettoyage
    new_size = JOURNAL_PATH.stat().st_size
    print(f"✅ Journal sauvegardé: {new_size} bytes")
    
    # Validation finale
    print(f"\n🔍 Validation finale...")
    with open(JOURNAL_PATH, 'r', encoding='utf-8') as f:
        validated = json.load(f)
    
    # Compter les entrées finales
    final_entries = validated.get("2025", {}).get("10", {}).get("31", {}).get("entries", [])
    print(f"✅ Entrées validées du 31 octobre: {len(final_entries)}")
    
    # Afficher les entrées restantes
    if final_entries:
        print(f"\n📋 Entrées restantes du 31 octobre:")
        for i, entry in enumerate(final_entries, 1):
            entry_id = entry.get("entry_id", "N/A")
            timestamp = entry.get("timestamp", "N/A")
            summary_preview = entry.get("summary", "")[:80]
            print(f"   {i}. {entry_id} ({timestamp})")
            print(f"      '{summary_preview}...'")
    else:
        print(f"\n⚠️  Plus aucune entrée pour le 31 octobre")
    
    print(f"\n" + "=" * 80)
    print("✅ NETTOYAGE TERMINÉ AVEC SUCCÈS")
    print("=" * 80)
    
    return True

if __name__ == "__main__":
    try:
        success = clean_corrupted_entries()
        if success:
            print("\n✅ Le journal a été nettoyé avec succès")
            print(f"💡 Backup disponible: {JOURNAL_PATH}.backup_*")
        else:
            print("\n⚠️  Le nettoyage a échoué ou aucune entrée à supprimer")
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
