#!/usr/bin/env python3
"""
Script de réparation du Journal - Nettoie les résumés corrompus
Corrige les entrées qui commencent par '": "' ou des guillemets résiduels
"""

import json
import re
from pathlib import Path
from datetime import datetime

# Chemin du journal
JOURNAL_PATH = Path("extensions/journal_de_bord/data/journal_2025.json")
BACKUP_PATH = Path(f"extensions/journal_de_bord/data/backups/journal_2025_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

def clean_summary(summary: str) -> str:
    """Nettoie un résumé corrompu"""
    if not isinstance(summary, str):
        return summary
    
    original = summary
    
    # Nettoyer les guillemets résiduels au début
    # Pattern 1: ": "Texte...
    if summary.startswith('": "'):
        summary = summary[4:]  # Retirer '": "'
    
    # Pattern 2: ":Texte...
    elif summary.startswith('":'):
        summary = summary[2:].lstrip()
    
    # Pattern 3: "Texte... (guillemet au début)
    elif summary.startswith('"') and not summary.startswith('{"'):
        summary = summary[1:]
    
    # Nettoyer les guillemets échappés
    summary = summary.replace('\\"', '"')
    
    # Nettoyer les doubles espaces
    summary = re.sub(r'\s+', ' ', summary)
    
    # Retirer guillemet final s'il y en a un orphelin
    if summary.endswith('"') and summary.count('"') == 1:
        summary = summary[:-1]
    
    summary = summary.strip()
    
    if summary != original:
        print(f"  ✅ Nettoyé: '{original[:50]}...' → '{summary[:50]}...'")
        return summary
    
    return summary

def repair_journal():
    """Répare tous les résumés du journal"""
    print("=" * 80)
    print("🔧 RÉPARATION DU JOURNAL DE BORD")
    print("=" * 80)
    
    # Chargement du journal
    print(f"\n📂 Chargement: {JOURNAL_PATH}")
    with open(JOURNAL_PATH, 'r', encoding='utf-8') as f:
        journal_data = json.load(f)
    
    print(f"✅ Journal chargé: {journal_data['metadata']['total_entries']} entrées totales")
    
    # Backup avant modification
    print(f"\n💾 Création backup: {BACKUP_PATH}")
    BACKUP_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(BACKUP_PATH, 'w', encoding='utf-8') as f:
        json.dump(journal_data, f, ensure_ascii=False, indent=2)
    print("✅ Backup créé")
    
    # Statistiques
    total_entries = 0
    repaired_entries = 0
    
    # Parcourir toutes les entrées
    print("\n🔍 Recherche des entrées corrompues...")
    
    if "months" in journal_data:
        for month_key, month_data in journal_data["months"].items():
            if "days" not in month_data:
                continue
            
            for day_key, day_data in month_data["days"].items():
                if "entries" not in day_data:
                    continue
                
                for entry in day_data["entries"]:
                    total_entries += 1
                    
                    if "summary" in entry:
                        original_summary = entry["summary"]
                        cleaned_summary = clean_summary(original_summary)
                        
                        if cleaned_summary != original_summary:
                            entry["summary"] = cleaned_summary
                            repaired_entries += 1
                            print(f"\n📝 Entrée {entry.get('id', 'unknown')} ({entry.get('timestamp', '')[:10]})")
    
    # Sauvegarde des modifications
    if repaired_entries > 0:
        print(f"\n💾 Sauvegarde des réparations...")
        with open(JOURNAL_PATH, 'w', encoding='utf-8') as f:
            json.dump(journal_data, f, ensure_ascii=False, indent=2)
        print("✅ Journal réparé et sauvegardé")
    else:
        print("\n✨ Aucune réparation nécessaire")
    
    # Rapport final
    print("\n" + "=" * 80)
    print("📊 RAPPORT DE RÉPARATION")
    print("=" * 80)
    print(f"Total entrées analysées: {total_entries}")
    print(f"Entrées réparées: {repaired_entries}")
    print(f"Entrées OK: {total_entries - repaired_entries}")
    
    if repaired_entries > 0:
        print(f"\n✅ Réparation terminée avec succès !")
        print(f"📁 Backup disponible: {BACKUP_PATH}")
    else:
        print("\n✅ Journal déjà en bon état")
    
    print("=" * 80)

if __name__ == "__main__":
    try:
        repair_journal()
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
