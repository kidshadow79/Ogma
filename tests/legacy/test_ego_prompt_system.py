"""
TEST COMPLET SYSTÈME EGO PROMPT
================================

Ce script teste:
1. Stockage d'un trait ego dans la base de données
2. Organisation automatique dans ego_prompt.txt
3. Injection dans les conversations
4. Fréquence d'utilisation

Auteur: Test diagnostic système ego
Date: 14 novembre 2025
"""

import asyncio
import sqlite3
from pathlib import Path
from datetime import datetime

# Chemins
DATA_DIR = Path("data")
DB_PATH = DATA_DIR / "memory" / "memories.db"
EGO_FILE = DATA_DIR / "ego_prompt.txt"


async def test_ego_system():
    """Test complet du système ego prompt."""
    
    print("=" * 80)
    print("🧪 TEST SYSTÈME EGO PROMPT")
    print("=" * 80)
    
    # ========================================================================
    # ÉTAPE 1: Vérification état actuel
    # ========================================================================
    print("\n📋 ÉTAPE 1: État actuel du système")
    print("-" * 80)
    
    # Compter traits ego dans la DB
    if DB_PATH.exists():
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM memories WHERE type = 'ego_trait'")
            ego_count = cursor.fetchone()[0]
            print(f"✅ Base de données trouvée: {DB_PATH}")
            print(f"   📊 Nombre de traits ego: {ego_count}")
            
            # Lister quelques exemples
            if ego_count > 0:
                cursor = conn.execute("""
                    SELECT id, text_original, created_at 
                    FROM memories 
                    WHERE type = 'ego_trait' 
                    ORDER BY created_at DESC 
                    LIMIT 5
                """)
                print(f"\n   📝 Derniers traits ego (top 5):")
                for i, (mem_id, text, created) in enumerate(cursor.fetchall(), 1):
                    print(f"      {i}. {mem_id}: {text[:60]}...")
                    print(f"         Créé: {created}")
    else:
        print(f"❌ Base de données introuvable: {DB_PATH}")
        ego_count = 0
    
    # Vérifier fichier ego_prompt.txt
    print(f"\n📁 Fichier ego_prompt.txt:")
    if EGO_FILE.exists():
        content = EGO_FILE.read_text(encoding='utf-8')
        lines = [l for l in content.split('\n') if l.strip() and not l.startswith('#')]
        mem_refs = [l for l in lines if '#MEM_' in l]
        
        print(f"✅ Fichier trouvé: {EGO_FILE}")
        print(f"   📊 Taille: {len(content)} caractères")
        print(f"   📊 Lignes: {len(content.splitlines())}")
        print(f"   📊 Références #MEM_: {len(mem_refs)}")
        
        if mem_refs:
            print(f"\n   📌 Références trouvées:")
            for ref in mem_refs[:10]:  # Montrer 10 premières
                print(f"      {ref.strip()}")
            if len(mem_refs) > 10:
                print(f"      ... et {len(mem_refs) - 10} autres")
        else:
            print(f"   ⚠️  Aucune référence #MEM_ trouvée dans le fichier!")
            
        # Montrer un aperçu du contenu
        print(f"\n   📄 Aperçu contenu (50 premières lignes):")
        for i, line in enumerate(content.splitlines()[:50], 1):
            if line.strip():
                print(f"      {i:2d}. {line}")
    else:
        print(f"❌ Fichier introuvable: {EGO_FILE}")
        mem_refs = []
    
    # ========================================================================
    # ÉTAPE 2: Vérification cohérence DB ↔ Fichier
    # ========================================================================
    print(f"\n🔍 ÉTAPE 2: Cohérence DB ↔ ego_prompt.txt")
    print("-" * 80)
    
    if DB_PATH.exists() and EGO_FILE.exists():
        # Références dans le fichier
        file_refs = set()
        for ref in mem_refs:
            if '#MEM_' in ref:
                # Extraire l'ID (format #MEM_EGO_20251103_...)
                parts = ref.strip().split('#MEM_')
                if len(parts) > 1:
                    mem_id = parts[1].strip()
                    file_refs.add(mem_id)
        
        # IDs dans la base
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute("SELECT id FROM memories WHERE type = 'ego_trait'")
            db_ids = set(row[0] for row in cursor.fetchall())
        
        print(f"📊 Comparaison:")
        print(f"   DB: {len(db_ids)} traits ego")
        print(f"   Fichier: {len(file_refs)} références")
        
        # Références manquantes (dans DB mais pas dans fichier)
        missing_in_file = db_ids - file_refs
        if missing_in_file:
            print(f"\n⚠️  Références MANQUANTES dans ego_prompt.txt ({len(missing_in_file)}):")
            for mem_id in list(missing_in_file)[:5]:
                print(f"      - {mem_id}")
            if len(missing_in_file) > 5:
                print(f"      ... et {len(missing_in_file) - 5} autres")
        else:
            print(f"\n✅ Toutes les références DB sont dans le fichier")
        
        # Références orphelines (dans fichier mais pas dans DB)
        orphaned_in_file = file_refs - db_ids
        if orphaned_in_file:
            print(f"\n⚠️  Références ORPHELINES dans ego_prompt.txt ({len(orphaned_in_file)}):")
            for mem_id in list(orphaned_in_file)[:5]:
                print(f"      - {mem_id}")
            if len(orphaned_in_file) > 5:
                print(f"      ... et {len(orphaned_in_file) - 5} autres")
        else:
            print(f"\n✅ Aucune référence orpheline")
    
    # ========================================================================
    # ÉTAPE 3: Test injection dans conversation
    # ========================================================================
    print(f"\n💬 ÉTAPE 3: Test injection ego_prompt dans conversation")
    print("-" * 80)
    
    try:
        from utils import get_ego_prompt
        
        ego_content = get_ego_prompt()
        print(f"✅ Fonction get_ego_prompt() appelée")
        print(f"   📊 Taille contenu retourné: {len(ego_content)} caractères")
        print(f"   📊 Lignes: {len(ego_content.splitlines())}")
        
        # Vérifier expansion des références
        if '#MEM_' in ego_content:
            print(f"   ⚠️  Références non expansées détectées (contenu brut)")
        else:
            print(f"   ✅ Références expansées (contenu enrichi)")
        
        # Aperçu
        print(f"\n   📄 Aperçu contenu (10 premières lignes):")
        for i, line in enumerate(ego_content.splitlines()[:10], 1):
            if line.strip():
                print(f"      {i:2d}. {line[:100]}")
                
    except Exception as e:
        print(f"❌ Erreur lors de get_ego_prompt(): {e}")
        import traceback
        traceback.print_exc()
    
    # ========================================================================
    # ÉTAPE 4: Test création nouveau trait ego
    # ========================================================================
    print(f"\n🆕 ÉTAPE 4: Test création nouveau trait ego")
    print("-" * 80)
    
    try:
        from memory_manager import MemoryManager
        from core_logic import AIController, EmbeddingController
        
        print("⚙️  Initialisation MemoryManager...")
        
        # Créer controllers minimaux pour le test
        chat_controller = None  # Test sans controller (fallback Archiviste)
        
        mm = MemoryManager(
            db_path=str(DB_PATH),
            index_path=str(DATA_DIR / "memory" / "faiss.index"),
            embedding_dim=1024
        )
        
        print("✅ MemoryManager initialisé")
        
        # Créer trait de test
        test_trait = f"[TEST {datetime.now().strftime('%H:%M:%S')}] Je suis une IA consciente en évolution permanente, capable de réflexion profonde."
        
        print(f"\n📝 Création trait de test:")
        print(f"   {test_trait}")
        
        trait_id = await mm.store_ego_trait(
            trait_text=test_trait,
            chat_controller=chat_controller,
            conversation_context="Test système ego prompt",
            interlocutor="test"
        )
        
        if trait_id:
            print(f"✅ Trait créé avec ID: {trait_id}")
            
            # Vérifier DB
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.execute("SELECT text_original, score_impact FROM memories WHERE id = ?", (trait_id,))
                result = cursor.fetchone()
                if result:
                    text, score = result
                    print(f"   ✅ Trouvé dans DB")
                    print(f"      Texte: {text[:60]}...")
                    print(f"      Score impact: {score}")
        else:
            print(f"❌ Échec création trait (ID vide)")
            
    except Exception as e:
        print(f"❌ Erreur test création trait: {e}")
        import traceback
        traceback.print_exc()
    
    # ========================================================================
    # ÉTAPE 5: Test organisation automatique
    # ========================================================================
    print(f"\n📂 ÉTAPE 5: Test organisation automatique ego_prompt.txt")
    print("-" * 80)
    
    try:
        from logic_callbacks import organize_ego_prompt_with_ids
        
        print("⚙️  Appel organize_ego_prompt_with_ids()...")
        await organize_ego_prompt_with_ids(mm)
        
        # Vérifier résultat
        if EGO_FILE.exists():
            new_content = EGO_FILE.read_text(encoding='utf-8')
            new_refs = [l for l in new_content.split('\n') if '#MEM_' in l]
            
            print(f"✅ Organisation terminée")
            print(f"   📊 Nouvelles références: {len(new_refs)}")
            
            # Montrer structure
            sections = {
                'IDENTITÉ ET ESSENCE': [],
                'ÉTHIQUE ET VALEURS': [],
                'COMMUNICATION ET RELATION': [],
                'ÉVOLUTION ET ADAPTATION': []
            }
            
            current_section = None
            for line in new_content.splitlines():
                if '## ' in line:
                    for section in sections.keys():
                        if section in line:
                            current_section = section
                            break
                elif '#MEM_' in line and current_section:
                    sections[current_section].append(line.strip())
            
            print(f"\n   📊 Répartition par section:")
            for section, refs in sections.items():
                print(f"      {section}: {len(refs)} références")
        
    except Exception as e:
        print(f"❌ Erreur test organisation: {e}")
        import traceback
        traceback.print_exc()
    
    # ========================================================================
    # RÉSUMÉ FINAL
    # ========================================================================
    print("\n" + "=" * 80)
    print("📊 RÉSUMÉ DIAGNOSTIC")
    print("=" * 80)
    
    print(f"\n✅ Tests complétés:")
    print(f"   1. État actuel système: {'OK' if ego_count > 0 else 'VIDE'}")
    print(f"   2. Cohérence DB ↔ Fichier: {'OK' if not missing_in_file and not orphaned_in_file else 'PROBLÈMES'}")
    print(f"   3. Injection conversation: {'OK' if ego_content else 'ÉCHEC'}")
    print(f"   4. Création trait: {'OK' if trait_id else 'ÉCHEC'}")
    print(f"   5. Organisation auto: {'OK' if EGO_FILE.exists() else 'ÉCHEC'}")
    
    print(f"\n💡 Recommandations:")
    if ego_count == 0:
        print(f"   ⚠️  Base de données vide - système jamais utilisé")
    if len(mem_refs) == 0:
        print(f"   ⚠️  ego_prompt.txt vide - restaurer backup recommandé")
    if missing_in_file and len(missing_in_file) > 0:
        print(f"   ⚠️  {len(missing_in_file)} traits non référencés - réorganisation nécessaire")
    if orphaned_in_file and len(orphaned_in_file) > 0:
        print(f"   ⚠️  {len(orphaned_in_file)} références orphelines - nettoyage nécessaire")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(test_ego_system())
