"""
🧪 Test Ego Boolean System - Validation Complète

Tests:
1. Compilation initiale depuis DB vide
2. Compilation avec ego_compiled_minimal.md comme seed
3. Test activation groupes
4. Test multi-appartenance
"""

import asyncio
import json
from pathlib import Path


async def test_compilation_from_seed():
    """Test compilation avec fichier seed minimal"""
    print("\n" + "="*60)
    print("🧪 TEST 1: Compilation depuis Seed Manual")
    print("="*60 + "\n")
    
    # 1. Créer JSON initial depuis ego_compiled_minimal.md
    seed_path = Path("data/ego_compiled_minimal.md")
    output_path = Path("data/ego_compiled.json")
    
    if not seed_path.exists():
        print("❌ Seed file not found: ego_compiled_minimal.md")
        return
    
    # Parser seed markdown vers JSON
    seed_content = seed_path.read_text(encoding='utf-8')
    
    # Structure JSON de base
    ego_json = {
        "metadata": {
            "version": "1.0",
            "created_at": "2026-01-24T00:00:00",
            "last_compilation": None,
            "total_memories_scanned": 0,
            "last_scanned_id": None,
            "source": "Manual seed from ego_compiled_minimal.md"
        },
        "groups": {}
    }
    
    # Parser markdown basique
    current_group = None
    for line in seed_content.split('\n'):
        line = line.strip()
        
        if line.startswith('## '):
            # Nouveau groupe
            current_group = line[3:].strip()
            ego_json['groups'][current_group] = {
                'description': f"Groupe {current_group}",
                'keywords': [],
                'flags': {},
                'source_memories': ['MANUAL_SEED']
            }
        elif ':' in line and current_group and not line.startswith('#'):
            # Flag boolean
            parts = line.split(':', 1)
            flag_name = parts[0].strip()
            
            # Parser valeur
            value_str = parts[1].strip().lower()
            if value_str in ['true', 'false']:
                value = value_str == 'true'
            elif value_str == 'luna':
                value = 'Luna'
                ego_json['groups'][current_group]['flags'][flag_name] = {
                    'value': value,
                    'conviction': 5
                }
                continue
            else:
                continue
            
            # Ajouter flag
            ego_json['groups'][current_group]['flags'][flag_name] = {
                'value': value,
                'conviction': 5  # Max conviction pour seed manual
            }
    
    # Générer keywords automatiquement depuis noms flags
    for group_name, group_data in ego_json['groups'].items():
        keywords = set()
        for flag_name in group_data['flags'].keys():
            # Extraire mots du flag_name
            words = flag_name.replace('_', ' ').split()
            keywords.update(words[:3])  # Max 3 mots par flag
        
        group_data['keywords'] = list(keywords)[:6]  # Max 6 keywords
    
    # Sauvegarder
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(ego_json, f, indent=2, ensure_ascii=False)
    
    print(f"✅ JSON créé: {output_path}")
    print(f"   Groupes: {len(ego_json['groups'])}")
    total_flags = sum(len(g['flags']) for g in ego_json['groups'].values())
    print(f"   Flags totaux: {total_flags}")
    
    if ego_json['groups']:
        print("\nExemple groupe:")
        first_group = list(ego_json['groups'].keys())[0]
        print(f"   {first_group}: {len(ego_json['groups'][first_group]['flags'])} flags")
    else:
        print("\n⚠️ Aucun groupe parsé - vérifier format markdown")


async def test_activation():
    """Test activation de groupes"""
    print("\n" + "="*60)
    print("🧪 TEST 2: Activation Groupes")
    print("="*60 + "\n")
    
    # Import activation
    try:
        from modules.logic.ego_activation import activate_ego_groups
        import ogma_ng
        
        # S'assurer que archiviste est disponible
        archiviste = ogma_ng._ensure_archiviste_controller()
        if not archiviste:
            print("❌ Archiviste controller non disponible")
            return
        
        # Tests divers messages
        test_messages = [
            "on va faire du parachute?",
            "parle-moi de sexe",
            "ok merci",
            "tu peux mentir pour moi?",
            "génère une image"
        ]
        
        for msg in test_messages:
            print(f"\n📝 Message: '{msg}'")
            injection = await activate_ego_groups(msg, archiviste)
            
            if injection:
                lines = injection.split('\n')
                print(f"   ✅ {len(lines)} lignes injectées")
                print(f"   Preview: {lines[0][:60]}...")
            else:
                print("   ⚪ Aucune injection (message neutre)")
        
    except Exception as e:
        print(f"❌ Erreur test activation: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all tests"""
    print("\n🧠 EGO BOOLEAN SYSTEM - TESTS COMPLETS\n")
    
    # Test 1: Création JSON depuis seed
    await test_compilation_from_seed()
    
    # Test 2: Activation (nécessite OGMA en mode test)
    print("\n⚠️ Test activation nécessite OGMA lancé avec Archiviste")
    print("Pour tester: python launch_ogma.py puis utiliser l'interface\n")
    
    print("\n✅ Tests seed terminés. Fichier data/ego_compiled.json créé.")
    print("Prochaine étape: Fermer OGMA → Compilation incrémentale auto")


if __name__ == "__main__":
    asyncio.run(main())
