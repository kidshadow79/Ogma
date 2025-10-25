#!/usr/bin/env python3
"""
Script de diagnostic et réparation pour les limites API OGMA
Analyse les causes et propose des solutions automatiques
"""

import json
import os
from pathlib import Path
from datetime import datetime

def analyze_conversation_load():
    """Analyser la charge de la conversation active"""
    conversations_dir = Path('data/conversations')
    
    if not conversations_dir.exists():
        print("❌ Dossier conversations non trouvé")
        return
    
    # Trouver la conversation la plus récente
    json_files = list(conversations_dir.glob('*.json'))
    if not json_files:
        print("❌ Aucune conversation trouvée")
        return
        
    latest_file = max(json_files, key=lambda f: f.stat().st_mtime)
    
    try:
        conversation = json.loads(latest_file.read_text(encoding='utf-8'))
        total_messages = len(conversation)
        total_chars = sum(len(str(msg)) for msg in conversation)
        estimated_tokens = total_chars // 4
        
        print(f"📊 DIAGNOSTIC CONVERSATION ACTIVE")
        print(f"=" * 50)
        print(f"📁 Fichier: {latest_file.name}")
        print(f"📏 Taille: {latest_file.stat().st_size:,} bytes")
        print(f"💬 Messages: {total_messages}")
        print(f"🔢 Tokens estimés: {estimated_tokens:,}")
        
        # Recommandations basées sur la taille
        if total_messages > 200:
            print(f"⚠️  CONVERSATION TRÈS LONGUE ({total_messages} messages)")
            print("🚨 Recommandation: Créer une nouvelle conversation")
            return "CONVERSATION_TOO_LONG"
        elif total_messages > 100:
            print(f"⚠️  CONVERSATION LONGUE ({total_messages} messages)")
            print("💡 Recommandation: Surveiller l'usage API")
            return "CONVERSATION_LONG"
        else:
            print("✅ Taille de conversation acceptable")
            return "CONVERSATION_OK"
            
    except Exception as e:
        print(f"❌ Erreur analyse conversation: {e}")
        return "ERROR"

def check_system_injections():
    """Vérifier les systèmes d'injection qui peuvent surcharger"""
    settings_file = Path('data/settings.json')
    
    if not settings_file.exists():
        print("❌ Fichier settings.json non trouvé")
        return
    
    try:
        settings = json.loads(settings_file.read_text(encoding='utf-8'))
        
        # Vérifier debug archiviste
        debug_archiviste = settings.get('debug', {}).get('show_archiviste_injection', False)
        
        # Analyser les instructions
        instructions = settings.get('prompts', {}).get('instructions', '')
        inst_tokens = len(instructions) // 4
        
        print(f"🔍 DIAGNOSTIC SYSTÈMES INJECTION")
        print(f"=" * 50)
        print(f"🧠 Debug archiviste: {debug_archiviste}")
        print(f"📋 Instructions: {inst_tokens:,} tokens")
        
        issues = []
        if debug_archiviste:
            issues.append("DEBUG_ARCHIVISTE_ON")
            print("⚠️  Debug archiviste activé (consomme plus de tokens)")
            
        if inst_tokens > 1000:
            issues.append("INSTRUCTIONS_LARGE")
            print(f"⚠️  Instructions volumineuses ({inst_tokens:,} tokens)")
        
        return issues
        
    except Exception as e:
        print(f"❌ Erreur analyse settings: {e}")
        return ["ERROR"]

def provide_solutions(conv_status, injection_issues):
    """Fournir des solutions ciblées"""
    print(f"\n🛠️  SOLUTIONS RECOMMANDÉES")
    print(f"=" * 50)
    
    if conv_status == "CONVERSATION_TOO_LONG":
        print("1. 🆕 CRÉER UNE NOUVELLE CONVERSATION (fortement recommandé)")
        print("2. ✂️  Archiver la conversation actuelle")
        print("3. 🔄 Redémarrer OGMA avec conversation vide")
        
    elif conv_status == "CONVERSATION_LONG":
        print("1. 📊 Surveiller l'usage API de près")
        print("2. 🔇 Désactiver temporairement les injections non-essentielles")
        
    if "DEBUG_ARCHIVISTE_ON" in injection_issues:
        print("3. 🔇 Désactiver le debug archiviste (économise des tokens)")
        
    if "INSTRUCTIONS_LARGE" in injection_issues:
        print("4. 📝 Compresser les instructions système")
    
    print("\n💡 SOLUTION IMMÉDIATE:")
    print("Taper 'nouvelle conversation' dans OGMA pour repartir à zéro")

if __name__ == "__main__":
    print("🔍 DIAGNOSTIC LIMITES API OGMA")
    print("=" * 60)
    
    conv_status = analyze_conversation_load()
    print()
    
    injection_issues = check_system_injections()
    print()
    
    provide_solutions(conv_status, injection_issues)
    
    print(f"\n📅 Diagnostic effectué le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")