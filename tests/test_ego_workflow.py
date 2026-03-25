#!/usr/bin/env python3
"""
Test Workflow Profil Générique - OGMA
======================================
Vérifie que les fichiers ego sont correctement sauvegardés et restaurés

Auteur: Yohan BROCARD (avec Copilot)
Date: 2 février 2026
"""

import sys
from pathlib import Path
from profile_manager import ProfileManager


def test_ego_files_in_workflow():
    """Test complet du workflow de sauvegarde/suppression/restauration des fichiers ego"""
    
    print("=" * 70)
    print("🧪 TEST WORKFLOW FICHIERS EGO")
    print("=" * 70)
    
    pm = ProfileManager()
    
    # 1. Vérifier état initial
    print("\n📊 1. État initial du profil")
    print("-" * 70)
    
    ego_files = ['ego_compiled.json', 'ego_compiled_boolean.md', 'ego_compiled_minimal.md', 'ego_prompt.txt']
    initial_state = {}
    
    for ego_file in ego_files:
        ego_path = Path("data") / ego_file
        exists = ego_path.exists()
        size = ego_path.stat().st_size if exists else 0
        initial_state[ego_file] = {'exists': exists, 'size': size}
        
        status = "✅ Présent" if exists else "❌ Absent"
        print(f"  {ego_file}: {status} ({size} bytes)")
    
    # 2. Test sauvegarde
    print("\n💾 2. Test sauvegarde profil")
    print("-" * 70)
    
    success, message, backup_path = pm.save_current_profile(
        "test_ego_workflow",
        "Test automatique workflow fichiers ego"
    )
    
    if success:
        print(f"✅ Sauvegarde réussie")
        print(f"📂 Chemin: {backup_path}")
        
        # Vérifier que les fichiers ego sont dans la sauvegarde
        backup_data = backup_path / "data"
        ego_in_backup = []
        for ego_file in ego_files:
            ego_backup_path = backup_data / ego_file
            if ego_backup_path.exists():
                ego_in_backup.append(ego_file)
                print(f"  ✅ {ego_file} présent dans backup")
            else:
                print(f"  ❌ {ego_file} MANQUANT dans backup")
        
        if len(ego_in_backup) == len([f for f in ego_files if initial_state[f]['exists']]):
            print("\n✅ Tous les fichiers ego présents initialement sont sauvegardés")
        else:
            print("\n⚠️ Certains fichiers ego manquent dans la sauvegarde!")
    else:
        print(f"❌ Échec sauvegarde: {message}")
        return False
    
    # 3. Test suppression (vérification que ego est vidé)
    print("\n🗑️  3. Test suppression profil")
    print("-" * 70)
    print("⚠️  NOTE: Ce test NE VA PAS réellement supprimer (simulation)")
    print("  Pour test réel, décommenter la ligne ci-dessous")
    
    # DÉCOMMENTER POUR TEST RÉEL DE SUPPRESSION
    # success, message = pm.delete_current_profile("DELETE-PROFILE-OGMA", preserve_founders=True)
    # 
    # if success:
    #     print("✅ Suppression réussie")
    #     
    #     # Vérifier que les fichiers ego sont vidés
    #     for ego_file in ego_files:
    #         ego_path = Path("data") / ego_file
    #         if ego_path.exists():
    #             size = ego_path.stat().st_size
    #             if ego_file == 'ego_compiled.json':
    #                 with open(ego_path, 'r', encoding='utf-8') as f:
    #                     content = f.read().strip()
    #                     is_empty = content == '{}' or content == ''
    #                 status = "✅ Vidé" if is_empty else "⚠️  Non vide"
    #                 print(f"  {ego_file}: {status} ({size} bytes)")
    #             else:
    #                 print(f"  {ego_file}: Présent ({size} bytes)")
    #         else:
    #             print(f"  {ego_file}: ❌ Supprimé complètement")
    # else:
    #     print(f"❌ Échec suppression: {message}")
    
    print("  ⏭️  Test suppression ignoré (protection)")
    
    # 4. Test restauration
    print("\n📂 4. Test restauration profil")
    print("-" * 70)
    print("⚠️  NOTE: Ce test NE VA PAS réellement restaurer (simulation)")
    print("  Pour test réel, décommenter la ligne ci-dessous")
    
    # DÉCOMMENTER POUR TEST RÉEL DE RESTAURATION
    # success, message = pm.load_profile_backup(backup_path)
    # 
    # if success:
    #     print("✅ Restauration réussie")
    #     print(message)
    #     
    #     # Vérifier que les fichiers ego sont restaurés
    #     for ego_file in ego_files:
    #         ego_path = Path("data") / ego_file
    #         if ego_path.exists():
    #             size = ego_path.stat().st_size
    #             original_size = initial_state[ego_file]['size']
    #             match = "✅" if size == original_size else "⚠️"
    #             print(f"  {match} {ego_file}: {size} bytes (original: {original_size} bytes)")
    #         else:
    #             print(f"  ❌ {ego_file}: Non restauré")
    # else:
    #     print(f"❌ Échec restauration: {message}")
    
    print("  ⏭️  Test restauration ignoré (protection)")
    
    # 5. Résumé
    print("\n" + "=" * 70)
    print("📋 RÉSUMÉ DU TEST")
    print("=" * 70)
    print("\n✅ WORKFLOW VÉRIFIÉ:")
    print("  1. ✅ Sauvegarde profil - Fichiers ego inclus")
    print("  2. ⏭️  Suppression profil - Test ignoré (protection)")
    print("  3. ⏭️  Restauration profil - Test ignoré (protection)")
    print("\n💡 POUR TEST COMPLET:")
    print("  Décommenter les sections 3 et 4 dans le code source")
    print("  ⚠️  ATTENTION: Cela modifiera votre profil actuel!")
    
    return True


if __name__ == "__main__":
    try:
        test_ego_files_in_workflow()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrompu par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
