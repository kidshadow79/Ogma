#!/usr/bin/env python3
"""
Script de nettoyage rapide pour créer un profil OGMA vierge
Usage: python clean_for_fresh_profile.py
"""

import os
import sys
from pathlib import Path
from data_cleaner import OGMADataCleaner, format_size
from datetime import datetime


def confirm_deletion() -> bool:
    """Demande confirmation à l'utilisateur"""
    print("\n" + "="*60)
    print("⚠️  ATTENTION - SUPPRESSION DÉFINITIVE DES DONNÉES OGMA")
    print("="*60)
    print()
    print("Cette action va supprimer DÉFINITIVEMENT:")
    print("• 🧠 Toute la mémoire de Luna (souvenirs, index FAISS)")
    print("• 💬 Toutes les conversations")
    print("• 🎭 Les données de personnalité (ego)")
    print("• 🗑️ Les fichiers temporaires")
    print()
    print("Une sauvegarde automatique sera créée avant suppression.")
    print()
    
    # Triple confirmation
    confirmation1 = input("Tapez 'OUI' pour continuer: ").strip().upper()
    if confirmation1 != 'OUI':
        print("❌ Annulation de l'opération")
        return False
    
    confirmation2 = input("Êtes-vous VRAIMENT sûr? Tapez 'SUPPRIMER': ").strip().upper()
    if confirmation2 != 'SUPPRIMER':
        print("❌ Annulation de l'opération")
        return False
    
    confirmation3 = input("Dernière confirmation - Tapez 'DELETE-ALL-OGMA-DATA': ").strip()
    if confirmation3 != 'DELETE-ALL-OGMA-DATA':
        print("❌ Code de confirmation incorrect")
        return False
    
    return True


def main():
    """Point d'entrée principal"""
    
    print("🧹 NETTOYAGE OGMA - Création d'un Profil Vierge")
    print("=" * 50)
    
    # Initialiser le cleaner
    cleaner = OGMADataCleaner()
    
    # Étape 1: Analyser les données existantes
    print("\n📊 Analyse des données existantes...")
    analysis = cleaner.analyze_current_data()
    
    # Afficher le résumé
    print(f"\n📈 RÉSUMÉ:")
    print(f"   Total fichiers: {analysis['total_files']}")
    print(f"   Taille totale: {format_size(analysis['total_size'])}")
    
    # Détails par catégorie
    if analysis['memory'].get('file_count', 0) > 0:
        memory = analysis['memory']
        print(f"\n🧠 MÉMOIRE: {memory['file_count']} fichiers ({format_size(memory['total_size'])})")
        if memory.get('memory_count'):
            print(f"   → {memory['memory_count']} souvenirs stockés")
    
    if analysis['conversations'].get('file_count', 0) > 0:
        conv = analysis['conversations']
        print(f"\n💬 CONVERSATIONS: {conv['file_count']} fichiers ({format_size(conv['total_size'])})")
        print(f"   → {conv['conversation_count']} conversations actives")
    
    if analysis['ego_data'].get('file_count', 0) > 0:
        ego = analysis['ego_data']
        print(f"\n🎭 DONNÉES EGO: {ego['file_count']} fichiers ({format_size(ego['total_size'])})")
        if ego.get('ego_prompt'):
            print(f"   → Ego prompt: {ego['ego_prompt']['lines']} lignes")
    
    if analysis['temp_files'].get('file_count', 0) > 0:
        temp = analysis['temp_files']
        print(f"\n🗑️ FICHIERS TEMPORAIRES: {temp['file_count']} fichiers ({format_size(temp['total_size'])})")
    
    # Vérifier s'il y a des données à supprimer
    total_files = analysis['total_files']
    if total_files == 0:
        print("\n✅ Aucune donnée trouvée - OGMA a déjà un profil vierge!")
        return
    
    # Demander confirmation
    if not confirm_deletion():
        print("\n✋ Opération annulée par l'utilisateur")
        return
    
    print("\n" + "="*60)
    print("🚀 DÉBUT DU PROCESSUS DE NETTOYAGE")
    print("="*60)
    
    
    backup_dir = None
    
    try:
        # Étape 2: Créer une sauvegarde
        print("\n💾 Création de la sauvegarde...")
        backup_dir = cleaner.create_backup()
        print(f"✅ Sauvegarde créée: {backup_dir}")
        
        # Calculer la taille de la sauvegarde
        backup_size = sum(f.stat().st_size for f in backup_dir.rglob('*') if f.is_file())
        print(f"📦 Taille sauvegarde: {format_size(backup_size)}")
        
        # Étape 3: Supprimer les données
        print("\n🗑️ Suppression des données en cours...")
        
        categories_to_delete = ['memory', 'conversations', 'ego_data', 'temp_files']
        deletion_log = cleaner.delete_selected_data(
            categories=categories_to_delete,
            confirmation_code="DELETE-ALL-OGMA-DATA"
        )
        
        print("\n📋 JOURNAL DE SUPPRESSION:")
        for log_entry in deletion_log:
            print(f"   {log_entry}")
        
        # Étape 4: Vérifier le nettoyage
        print("\n🔍 Vérification du nettoyage...")
        verification = cleaner.verify_clean_state()
        
        if verification['all_clean']:
            print("\n🎉 SUCCÈS!")
            print("✅ Nettoyage terminé avec succès")
            print("🆕 OGMA a maintenant un profil complètement vierge")
            print(f"💾 Sauvegarde disponible dans: {backup_dir}")
            
        else:
            print("\n⚠️ NETTOYAGE PARTIEL")
            print("Quelques éléments n'ont pas pu être supprimés:")
            for issue in verification['issues']:
                print(f"   • {issue}")
            print(f"💾 Sauvegarde disponible dans: {backup_dir}")
        
        print("\n" + "="*60)
        print("✨ OGMA EST PRÊT POUR UN NOUVEAU DÉPART!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ ERREUR CRITIQUE: {e}")
        print("⚠️ Le processus de nettoyage a échoué")
        try:
            if backup_dir:
                print(f"💾 Sauvegarde disponible pour récupération: {backup_dir}")
        except NameError:
            print("💾 Aucune sauvegarde créée")
        sys.exit(1)


if __name__ == "__main__":
    main()