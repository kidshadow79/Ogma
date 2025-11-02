#!/usr/bin/env python3
"""Vérifier la dernière entrée du journal pour s'assurer qu'elle est saine"""

import json
from pathlib import Path
from datetime import datetime

JOURNAL_PATH = Path("extensions/journal_de_bord/data/journal_2025.json")

def get_last_entry():
    """Récupère et affiche la dernière entrée du journal"""
    
    print("=" * 80)
    print("VÉRIFICATION DERNIÈRE ENTRÉE DU JOURNAL")
    print("=" * 80)
    
    with open(JOURNAL_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Parcourir toutes les entrées pour trouver la plus récente
    all_entries = []
    
    if "2025" in data:
        for month_key, month_data in data["2025"].items():
            for day_key, day_data in month_data.items():
                if isinstance(day_data, list):
                    # Format ancien
                    for entry in day_data:
                        all_entries.append((entry.get("timestamp", ""), entry))
                elif isinstance(day_data, dict) and "entries" in day_data:
                    # Format nouveau (months structure)
                    pass
    
    if "months" in data:
        for month_num, month_info in data["months"].items():
            if "days" in month_info:
                for day_num, day_info in month_info["days"].items():
                    if "entries" in day_info:
                        for entry in day_info["entries"]:
                            all_entries.append((entry.get("timestamp", ""), entry))
    
    if not all_entries:
        print("❌ Aucune entrée trouvée dans le journal")
        return None
    
    # Trier par timestamp
    all_entries.sort(key=lambda x: x[0], reverse=True)
    
    last_timestamp, last_entry = all_entries[0]
    
    print(f"\n📅 DERNIÈRE ENTRÉE")
    print(f"{'='*80}\n")
    
    print(f"🆔 ID: {last_entry.get('id', 'N/A')}")
    print(f"⏰ Timestamp: {last_timestamp}")
    
    # Parser le timestamp pour format lisible
    try:
        dt = datetime.fromisoformat(last_timestamp.replace('Z', '+00:00'))
        print(f"📆 Date lisible: {dt.strftime('%d/%m/%Y à %H:%M:%S')}")
    except:
        pass
    
    print(f"\n📊 MÉTADONNÉES:")
    print(f"   Tokens: {last_entry.get('tokens', 'N/A')}")
    print(f"   Conversation ID: {last_entry.get('conversation_id', 'N/A')}")
    print(f"   Généré par: {last_entry.get('generated_by', 'N/A')}")
    print(f"   Importance: {last_entry.get('importance', 'N/A')}")
    print(f"   Mots: {last_entry.get('word_count', 'N/A')}")
    
    print(f"\n👥 PARTICIPANTS:")
    participants = last_entry.get('participants', [])
    for p in participants:
        print(f"   - {p}")
    
    print(f"\n🏷️  TAGS:")
    tags = last_entry.get('tags', [])
    for t in tags:
        print(f"   - {t}")
    
    summary = last_entry.get('summary', '')
    print(f"\n📝 RÉSUMÉ ({len(summary)} caractères):")
    print(f"{'-'*80}")
    print(summary[:500])
    if len(summary) > 500:
        print(f"\n... [{len(summary) - 500} caractères restants]")
    print(f"{'-'*80}")
    
    # Vérifications de santé
    print(f"\n🔍 VÉRIFICATIONS:")
    
    checks = []
    
    # Check 1: conversation_id
    if last_entry.get('conversation_id') == 'unknown':
        checks.append("❌ conversation_id = 'unknown' (PROBLÈME)")
    else:
        checks.append(f"✅ conversation_id valide: {last_entry.get('conversation_id')}")
    
    # Check 2: Résumé générique
    if "Journal de Bord" in summary and "extension" in summary and "architecture modulaire" in summary:
        checks.append("❌ Résumé générique 'Journal de Bord extension' détecté (CORROMPU)")
    else:
        checks.append("✅ Résumé unique et spécifique")
    
    # Check 3: JSON dans résumé
    if '"token_count"' in summary or '"tokens"' in summary:
        checks.append("❌ Résidus JSON détectés dans le résumé (CORROMPU)")
    else:
        checks.append("✅ Pas de résidus JSON")
    
    # Check 4: Longueur résumé
    if len(summary) < 100:
        checks.append(f"⚠️  Résumé très court ({len(summary)} chars)")
    elif len(summary) > 3000:
        checks.append(f"⚠️  Résumé très long ({len(summary)} chars)")
    else:
        checks.append(f"✅ Longueur résumé appropriée ({len(summary)} chars)")
    
    # Check 5: Tokens
    tokens = last_entry.get('tokens', 0)
    if tokens == 312:
        checks.append("⚠️  Token count = 312 (valeur placeholder typique)")
    else:
        checks.append(f"✅ Token count: {tokens}")
    
    for check in checks:
        print(f"   {check}")
    
    # Verdict final
    print(f"\n{'='*80}")
    errors = [c for c in checks if c.startswith("❌")]
    warnings = [c for c in checks if c.startswith("⚠️")]
    
    if errors:
        print(f"❌ VERDICT: ENTRÉE CORROMPUE ({len(errors)} erreurs)")
    elif warnings:
        print(f"⚠️  VERDICT: ENTRÉE SUSPECTE ({len(warnings)} avertissements)")
    else:
        print(f"✅ VERDICT: ENTRÉE SAINE ET VALIDE")
    print(f"{'='*80}")
    
    return last_entry

if __name__ == "__main__":
    try:
        entry = get_last_entry()
    except Exception as e:
        print(f"\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
