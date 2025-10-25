"""
🧹 NETTOYAGE DES CONVERSATIONS EXISTANTES
==========================================

Script pour nettoyer les fichiers JSON de conversations existants
en supprimant les éléments système et ne gardant que les vrais échanges.
"""

import json
import shutil
from pathlib import Path
from datetime import datetime


def clean_conversation_file(file_path: Path) -> tuple[int, int]:
    """
    Nettoie un fichier de conversation en supprimant les messages système
    
    Returns:
        tuple[int, int]: (messages_before, messages_after)
    """
    try:
        # Charger la conversation
        with open(file_path, 'r', encoding='utf-8') as f:
            conversation = json.load(f)
        
        original_count = len(conversation)
        
        # Filtrer pour ne garder que user/assistant
        cleaned_conversation = []
        for msg in conversation:
            role = msg.get('role')
            content = msg.get('content', '')
            
            if role in ('user', 'assistant') and isinstance(content, str):
                # Nettoyer le contenu des injections temporelles pour les messages utilisateur
                if role == 'user':
                    # Supprimer les patterns d'injection temporelle
                    import re
                    # Pattern: "temps outils subtile gère rythme vie discret [timestamp]"
                    cleaned_content = re.sub(
                        r'temps\s+outils\s+subtile\s+gère\s+rythme\s+vie\s+discret\s+\[[^\]]+\]\s*',
                        '',
                        content,
                        flags=re.IGNORECASE
                    ).strip()
                    
                    # Si après nettoyage il ne reste rien, garder original
                    if not cleaned_content:
                        cleaned_content = content
                else:
                    cleaned_content = content
                
                cleaned_conversation.append({
                    'role': role,
                    'content': cleaned_content,
                    'timestamp': msg.get('timestamp'),
                    'memorized': msg.get('memorized', False)
                })
        
        # Créer une sauvegarde
        backup_path = file_path.parent / f"{file_path.stem}_backup{file_path.suffix}"
        shutil.copy2(file_path, backup_path)
        
        # Sauvegarder la version nettoyée
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(cleaned_conversation, f, ensure_ascii=False, indent=2)
        
        print(f"✅ {file_path.name}: {original_count} → {len(cleaned_conversation)} messages")
        return original_count, len(cleaned_conversation)
        
    except Exception as e:
        print(f"❌ Erreur avec {file_path.name}: {e}")
        return 0, 0


def main():
    """Nettoie toutes les conversations existantes"""
    print("🧹 NETTOYAGE DES CONVERSATIONS EXISTANTES")
    print("=" * 50)
    
    conversations_dir = Path("data/conversations")
    
    if not conversations_dir.exists():
        print("❌ Dossier conversations non trouvé")
        return
    
    json_files = list(conversations_dir.glob("*.json"))
    
    if not json_files:
        print("ℹ️ Aucun fichier de conversation trouvé")
        return
    
    print(f"📁 {len(json_files)} fichiers de conversation trouvés")
    print()
    
    total_before = 0
    total_after = 0
    cleaned_files = 0
    
    for json_file in json_files:
        if json_file.name.endswith('_backup.json'):
            continue  # Ignorer les sauvegardes
        
        before, after = clean_conversation_file(json_file)
        if before > 0:
            total_before += before
            total_after += after
            cleaned_files += 1
    
    print()
    print("📊 RÉSUMÉ DU NETTOYAGE:")
    print(f"   📁 Fichiers traités: {cleaned_files}")
    print(f"   📝 Messages avant: {total_before}")
    print(f"   📝 Messages après: {total_after}")
    
    if total_before > 0:
        savings = ((total_before - total_after) / total_before) * 100
        print(f"   💾 Réduction: {savings:.1f}%")
    
    print()
    print("✅ NETTOYAGE TERMINÉ!")
    print("💡 Des sauvegardes ont été créées avec le suffixe '_backup'")


if __name__ == "__main__":
    main()