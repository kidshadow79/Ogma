#!/usr/bin/env python3
"""Analyser toutes les entrées du journal pour trouver les données corrompues"""

import json
from pathlib import Path

JOURNAL_PATH = Path("extensions/journal_de_bord/data/journal_2025.json")

with open(JOURNAL_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"\n{'='*80}")
print(f"ANALYSE COMPLÈTE DU JOURNAL 2025")
print(f"{'='*80}\n")

total_entries = 0
corrupted_entries = []

if "2025" in data:
    for month_num, month_data in sorted(data["2025"].items()):
        month_name = ["", "Jan", "Fév", "Mar", "Avr", "Mai", "Jun", 
                     "Jul", "Aoû", "Sep", "Oct", "Nov", "Déc"][int(month_num)]
        
        for day_num, day_data in sorted(month_data.items()):
            entries = day_data.get("entries", [])
            
            if entries:
                print(f"\n📅 {day_num} {month_name} 2025 - {len(entries)} entrée(s)")
                total_entries += len(entries)
                
                for i, entry in enumerate(entries, 1):
                    entry_id = entry.get('entry_id', 'N/A')
                    conv_id = entry.get('conversation_id', 'N/A')
                    summary = entry.get('summary', '')
                    
                    print(f"   {i}. {entry_id}")
                    print(f"      Conv: {conv_id}")
                    print(f"      Résumé ({len(summary)} chars): {summary[:100]}...")
                    
                    # Détecter résumés suspects
                    is_corrupted = False
                    reasons = []
                    
                    if conv_id == "unknown":
                        reasons.append("conversation_id='unknown'")
                        is_corrupted = True
                    
                    if "Journal de Bord" in summary and "extension" in summary:
                        reasons.append("résumé générique 'Journal de Bord extension'")
                        is_corrupted = True
                    
                    if '"token_count"' in summary or '"tokens"' in summary:
                        reasons.append("JSON corrompu dans résumé")
                        is_corrupted = True
                    
                    if is_corrupted:
                        print(f"      ⚠️  CORROMPU: {', '.join(reasons)}")
                        corrupted_entries.append({
                            'date': f"{day_num}/{month_num}/2025",
                            'entry_id': entry_id,
                            'reasons': reasons
                        })

print(f"\n{'='*80}")
print(f"STATISTIQUES")
print(f"{'='*80}")
print(f"Total entrées: {total_entries}")
print(f"Entrées corrompues: {len(corrupted_entries)}")

if corrupted_entries:
    print(f"\n📋 LISTE DES ENTRÉES CORROMPUES À SUPPRIMER:")
    for item in corrupted_entries:
        print(f"   - {item['entry_id']} ({item['date']})")
        for reason in item['reasons']:
            print(f"     → {reason}")
