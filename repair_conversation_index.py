"""
Script de réparation de l'index des conversations
Reconstruit index.json depuis les fichiers .json existants
"""

import json
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).parent / 'data'
CONV_DIR = DATA_DIR / 'conversations'

def repair_index():
    """Reconstruit l'index depuis les fichiers de conversations"""
    print("\n🔧 RÉPARATION INDEX CONVERSATIONS\n")
    print("=" * 50)
    
    # Charger l'index actuel (probablement vide)
    index_path = CONV_DIR / 'index.json'
    
    if index_path.exists():
        try:
            with open(index_path, 'r', encoding='utf-8-sig') as f:
                content = f.read().strip()
                if content:
                    data = json.loads(content)
                    current_index = data.get('conversations', {}) if isinstance(data, dict) else {}
                else:
                    current_index = {}
        except Exception as e:
            print(f"⚠️ Erreur lecture index actuel: {e}")
            current_index = {}
    else:
        current_index = {}
    
    print(f"📊 Index actuel: {len(current_index)} conversations")
    
    # Lister tous les fichiers .json (sauf index.json et backups)
    conv_files = []
    for f in CONV_DIR.glob('*.json'):
        if f.name == 'index.json' or '_backup' in f.name or 'index_backup' in f.name:
            continue
        conv_files.append(f)
    
    print(f"📁 Fichiers trouvés: {len(conv_files)} conversations\n")
    
    # Reconstruire l'index
    new_index = {}
    repaired = 0
    skipped = 0
    errors = 0
    
    for conv_file in sorted(conv_files):
        conv_id = conv_file.stem  # Nom sans extension
        
        try:
            # Lire le fichier de conversation
            with open(conv_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content or content == '[]':
                    print(f"⏭️  {conv_id}: Fichier vide, ignoré")
                    skipped += 1
                    continue
                
                conv_data = json.loads(content)
                
                # Extraire les métadonnées
                if isinstance(conv_data, list) and len(conv_data) > 0:
                    # Format liste de messages
                    first_msg = conv_data[0]
                    last_msg = conv_data[-1]
                    
                    # Titre: premier message utilisateur ou auto-généré
                    title = None
                    for msg in conv_data:
                        if msg.get('role') == 'user':
                            title = msg.get('content', '')[:60].strip()
                            break
                    if not title:
                        title = f"Conversation du {conv_id[:10]}"
                    
                    # Dates
                    created = first_msg.get('timestamp', conv_file.stat().st_ctime)
                    updated = last_msg.get('timestamp', conv_file.stat().st_mtime)
                    
                    # Convertir timestamps si nécessaire
                    if isinstance(created, (int, float)):
                        created = datetime.fromtimestamp(created).isoformat()
                    if isinstance(updated, (int, float)):
                        updated = datetime.fromtimestamp(updated).isoformat()
                    
                    new_index[conv_id] = {
                        'id': conv_id,
                        'title': title,
                        'created': created,
                        'updated': updated,
                        'auto_title': True,
                        'message_count': len(conv_data)
                    }
                    
                    print(f"✅ {conv_id}: \"{title[:40]}...\" ({len(conv_data)} msgs)")
                    repaired += 1
                    
                else:
                    print(f"⚠️  {conv_id}: Format non reconnu")
                    skipped += 1
                    
        except Exception as e:
            print(f"❌ {conv_id}: Erreur - {e}")
            errors += 1
    
    # Sauvegarder le nouvel index
    print(f"\n{'=' * 50}")
    print(f"📊 RÉSUMÉ:")
    print(f"   ✅ Réparées: {repaired}")
    print(f"   ⏭️  Ignorées: {skipped}")
    print(f"   ❌ Erreurs: {errors}")
    print(f"   📦 Total: {len(new_index)} conversations dans l'index\n")
    
    if repaired > 0:
        # Backup de l'ancien index
        if index_path.exists():
            backup_path = CONV_DIR / f"index_backup_corrupted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            import shutil
            shutil.copy(index_path, backup_path)
            print(f"💾 Backup ancien index: {backup_path.name}")
        
        # Sauvegarder le nouvel index
        payload = {"conversations": new_index}
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Index reconstruit: {len(new_index)} conversations")
        print(f"📁 Fichier: {index_path}")
        print(f"\n🎉 Réparation terminée avec succès !\n")
    else:
        print("⚠️ Aucune conversation à réparer\n")

if __name__ == '__main__':
    repair_index()
