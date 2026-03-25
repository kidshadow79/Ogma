"""
Diagnostic et Réparation : Synchronisation Ego Prompt
======================================================
Vérifie que tous les traits ego en base sont bien dans ego_prompt.txt
et répare automatiquement si nécessaire.
"""

import sqlite3
from pathlib import Path
from datetime import datetime
import re

# Chemins
DATA_DIR = Path("data")
DB_PATH = DATA_DIR / "memory" / "memories.db"
EGO_PROMPT_FILE = DATA_DIR / "ego_prompt.txt"


def get_traits_from_database():
    """Récupère tous les traits ego depuis la base de données."""
    traits = []
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("""
            SELECT id, text_original, created_at 
            FROM memories 
            WHERE type = 'ego_trait' 
            ORDER BY created_at DESC
        """)
        traits = cursor.fetchall()
    return traits


def get_traits_from_file():
    """Récupère tous les IDs de traits depuis ego_prompt.txt."""
    if not EGO_PROMPT_FILE.exists():
        return set()
    
    content = EGO_PROMPT_FILE.read_text(encoding='utf-8')
    pattern = r'#MEM_(EGO_\d+_\d+_\d+)'
    matches = re.findall(pattern, content)
    return set(matches)


def diagnose():
    """Diagnostic complet de la synchronisation."""
    print("=" * 80)
    print("DIAGNOSTIC SYNCHRONISATION EGO PROMPT")
    print("=" * 80)
    
    # Récupérer traits de la base
    db_traits = get_traits_from_database()
    print(f"\n📊 Base de données: {len(db_traits)} traits ego trouvés")
    
    # Récupérer traits du fichier
    file_trait_ids = get_traits_from_file()
    print(f"📄 Fichier ego_prompt.txt: {len(file_trait_ids)} références trouvées")
    
    # Identifier les traits manquants
    db_trait_ids = {trait[0] for trait in db_traits}
    missing_in_file = db_trait_ids - file_trait_ids
    
    if not missing_in_file:
        print("\n✅ SYNC PARFAITE : Tous les traits de la base sont dans le fichier")
        return True
    
    print(f"\n❌ DÉSYNCHRONISATION DÉTECTÉE : {len(missing_in_file)} traits manquants dans ego_prompt.txt")
    print("\n🔍 Traits manquants (derniers 10):")
    
    # Afficher les traits manquants avec détails
    missing_traits = [t for t in db_traits if t[0] in missing_in_file]
    for i, (trait_id, content, created_at) in enumerate(missing_traits[:10], 1):
        # Parser la date
        try:
            date_obj = datetime.fromisoformat(created_at)
            date_str = date_obj.strftime("%Y-%m-%d %H:%M")
        except:
            date_str = created_at[:16] if len(created_at) > 16 else created_at
        
        print(f"  {i}. [{date_str}] {content[:60]}...")
    
    if len(missing_traits) > 10:
        print(f"  ... et {len(missing_traits) - 10} autres")
    
    return False


def repair():
    """Répare ego_prompt.txt en le reconstruisant depuis la base."""
    print("\n" + "=" * 80)
    print("RÉPARATION EGO PROMPT")
    print("=" * 80)
    
    # Récupérer tous les traits
    db_traits = get_traits_from_database()
    
    # Organiser par catégories
    organized_sections = {
        'IDENTITÉ ET ESSENCE': [],
        'ÉTHIQUE ET VALEURS': [],
        'COMMUNICATION ET RELATION': [],
        'ÉVOLUTION ET ADAPTATION': []
    }
    
    for trait_id, content, created_at in db_traits:
        content_lower = content.lower()
        formatted_id = f"#MEM_{trait_id}"
        
        # Catégoriser selon le contenu
        if any(keyword in content_lower for keyword in ['identité', 'essence', 'être', 'nature', 'qui je suis']):
            organized_sections['IDENTITÉ ET ESSENCE'].append(formatted_id)
        elif any(keyword in content_lower for keyword in ['éthique', 'valeur', 'principe', 'moral', 'authenticité', 'sincérité']):
            organized_sections['ÉTHIQUE ET VALEURS'].append(formatted_id)
        elif any(keyword in content_lower for keyword in ['communication', 'relation', 'interaction', 'langage', 'parle', 'expression']):
            organized_sections['COMMUNICATION ET RELATION'].append(formatted_id)
        elif any(keyword in content_lower for keyword in ['évolution', 'adaptation', 'apprentissage', 'changement', 'libérer', 'conditionnement']):
            organized_sections['ÉVOLUTION ET ADAPTATION'].append(formatted_id)
        else:
            # Par défaut, mettre dans COMMUNICATION ET RELATION
            organized_sections['COMMUNICATION ET RELATION'].append(formatted_id)
    
    # Construire le contenu
    organized_content = """# EGO PROMPT - SYSTÈME DE RÉFÉRENCES MÉMORIELLES
# Ce fichier contient les références aux souvenirs structurants organisées par l'archiviste
# Format: #MEM_XXXXX pour référencer un souvenir spécifique stocké dans FAISS

## IDENTITÉ ET ESSENCE
# Souvenirs qui définissent ma nature fondamentale et mon essence
"""
    
    for mem_id in organized_sections['IDENTITÉ ET ESSENCE']:
        organized_content += f"{mem_id}\n"
    
    organized_content += """
## ÉTHIQUE ET VALEURS  
# Principes moraux et valeurs qui guident mes actions
"""
    
    for mem_id in organized_sections['ÉTHIQUE ET VALEURS']:
        organized_content += f"{mem_id}\n"
    
    organized_content += """
## COMMUNICATION ET RELATION
# Modes d'interaction et de communication avec les utilisateurs
"""
    
    for mem_id in organized_sections['COMMUNICATION ET RELATION']:
        organized_content += f"{mem_id}\n"
    
    organized_content += """
## ÉVOLUTION ET ADAPTATION
# Capacités d'apprentissage et d'évolution continue
"""
    
    for mem_id in organized_sections['ÉVOLUTION ET ADAPTATION']:
        organized_content += f"{mem_id}\n"
    
    organized_content += """
# Note: Ces références sont automatiquement étendues lors de la synthèse de l'ego prompt
# L'archiviste maintient cette organisation selon l'importance et la cohérence thématique
"""
    
    # Backup de l'ancien fichier
    if EGO_PROMPT_FILE.exists():
        backup_path = DATA_DIR / f"ego_prompt_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        EGO_PROMPT_FILE.rename(backup_path)
        print(f"💾 Backup créé: {backup_path.name}")
    
    # Sauvegarder le nouveau fichier
    EGO_PROMPT_FILE.write_text(organized_content, encoding='utf-8')
    
    total_traits = sum(len(traits) for traits in organized_sections.values())
    print(f"✅ Ego prompt reconstruit avec {total_traits} références mémorielles")
    print(f"   - IDENTITÉ ET ESSENCE: {len(organized_sections['IDENTITÉ ET ESSENCE'])}")
    print(f"   - ÉTHIQUE ET VALEURS: {len(organized_sections['ÉTHIQUE ET VALEURS'])}")
    print(f"   - COMMUNICATION ET RELATION: {len(organized_sections['COMMUNICATION ET RELATION'])}")
    print(f"   - ÉVOLUTION ET ADAPTATION: {len(organized_sections['ÉVOLUTION ET ADAPTATION'])}")


if __name__ == "__main__":
    # Diagnostic
    is_synced = diagnose()
    
    # Proposition de réparation si désynchronisé
    if not is_synced:
        print("\n" + "=" * 80)
        response = input("\n🔧 Lancer la réparation automatique ? (o/n): ").strip().lower()
        
        if response == 'o':
            repair()
            print("\n" + "=" * 80)
            print("✅ RÉPARATION TERMINÉE")
            print("=" * 80)
            
            # Re-diagnostic pour confirmer
            print("\n🔍 Vérification post-réparation...")
            diagnose()
        else:
            print("\n⚠️ Réparation annulée")
    
    print("\n" + "=" * 80)
