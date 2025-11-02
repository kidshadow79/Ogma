#!/usr/bin/env python3
"""Lister les entrées du 31 octobre pour identifier les IDs corrects"""

import json
from pathlib import Path

JOURNAL_PATH = Path("extensions/journal_de_bord/data/journal_2025.json")

with open(JOURNAL_PATH, 'r', encoding='utf-8') as f:
    data = json.load(f)

entries = data.get('2025', {}).get('10', {}).get('31', {}).get('entries', [])

print(f"\n{'='*80}")
print(f"ENTRÉES DU 31 OCTOBRE 2025 - Total: {len(entries)}")
print(f"{'='*80}\n")

for i, entry in enumerate(entries, 1):
    entry_id = entry.get('entry_id', 'N/A')
    timestamp = entry.get('timestamp', 'N/A')
    conv_id = entry.get('conversation_id', 'N/A')
    summary = entry.get('summary', '')
    
    print(f"{i}. ID: {entry_id}")
    print(f"   Timestamp: {timestamp}")
    print(f"   Conversation ID: {conv_id}")
    print(f"   Résumé ({len(summary)} chars): {summary[:150]}...")
    
    # Détecter les résumés suspects (placeholder)
    if "Journal de Bord" in summary and "extension" in summary:
        print(f"   ⚠️  SUSPECT: Résumé générique détecté!")
    
    print()
