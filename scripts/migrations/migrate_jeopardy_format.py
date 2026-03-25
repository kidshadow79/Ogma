"""
Script de Migration Format Jeopardy
===================================
Migre tous les souvenirs existants vers le nouveau format :
- Titre : 2 questions courtes dont le texte est la réponse (style Jeopardy)
- Résumé : Liste compacte d'entités/mots-clés séparés par des points
- Embedding : Généré sur titre+résumé uniquement (plus concentré)

Usage:
    python migrate_jeopardy_format.py [--dry-run] [--limit N] [--skip-ego]
    
Options:
    --dry-run   : Affiche les changements sans les appliquer
    --limit N   : Limite à N souvenirs (pour test)
    --skip-ego  : Ignore les souvenirs EGO (traits de personnalité)
"""

import asyncio
import sqlite3
import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
import numpy as np

# Ajout du path OGMA
sys.path.insert(0, str(Path(__file__).parent))

from core_logic import APIManager

# Configuration
DB_PATH = Path("data/memory/memories.db")
FAISS_PATH = Path("data/memory/faiss_index.bin")
BACKUP_SUFFIX = datetime.now().strftime("%Y%m%d_%H%M%S")

# Prompt Jeopardy pour régénération
JEOPARDY_PROMPT = """Tu es l'Archiviste d'OGMA. Tu dois reformater ce souvenir existant vers le nouveau format optimisé.

📋 NOUVEAU FORMAT REQUIS:

{{
    "titre": "2 questions courtes et DISTINCTES dont le texte brut est la réponse (style Jeopardy, max 20 mots total)",
    "résumé": "Liste compacte des entités et mots-clés essentiels séparés par des points (noms, lieux, dates, concepts clés)"
}}

🎯 EXEMPLES:
- Texte: "J'ai adopté mon chat Willow en 2020 chez un éleveur à Lyon"
  → titre: "Comment s'appelle le chat de l'utilisateur ? Où a-t-il été adopté ?"
  → résumé: "Chat. Willow. Adoption 2020. Éleveur Lyon. Animal de compagnie."

- Texte: "Yohan a créé OGMA pour donner une mémoire aux IA"
  → titre: "Qui a créé OGMA ? Quel est le but d'OGMA ?"
  → résumé: "Yohan. Créateur. OGMA. Mémoire IA. Application. Conscience artificielle."

📝 SOUVENIR À REFORMATER:

Titre actuel: {current_title}
Résumé actuel: {current_summary}
Texte original: {text_original}

🎯 Génère UNIQUEMENT un objet JSON avec les clés "titre" et "résumé" au nouveau format. Rien d'autre."""


class JeopardyMigrator:
    def __init__(self, dry_run: bool = False, limit: int = None, skip_ego: bool = False):
        self.dry_run = dry_run
        self.limit = limit
        self.skip_ego = skip_ego
        self.archiviste = None
        self.embedder = None
        self.stats = {
            'total': 0,
            'migrated': 0,
            'skipped': 0,
            'errors': 0
        }
        
    async def initialize(self):
        """Initialise les contrôleurs IA depuis settings.json"""
        print("\n" + "="*70)
        print("🚀 MIGRATION FORMAT JEOPARDY")
        print("="*70)
        
        if self.dry_run:
            print("⚠️  MODE DRY-RUN: Aucune modification ne sera appliquée\n")
        
        # Charger settings
        settings_path = Path("data/settings.json")
        if not settings_path.exists():
            raise FileNotFoundError("settings.json non trouvé")
            
        with open(settings_path, 'r', encoding='utf-8') as f:
            self.settings = json.load(f)
        
        # Initialiser APIManager pour Archiviste (reasoning_api)
        reasoning = self.settings.get('reasoning_api', {})
        self.archiviste_api = APIManager()
        self.archiviste_api.configure(
            provider=reasoning.get('provider', 'GROK'),
            api_key=reasoning.get('api_key', ''),
            model=reasoning.get('api_model', '')
        )
        print(f"✅ Archiviste configuré: {reasoning.get('provider')}/{reasoning.get('api_model')}")
        
        # Initialiser APIManager pour Embedder (embedding_api)
        embedding = self.settings.get('embedding_api', {})
        self.embedder_api = APIManager()
        self.embedder_api.configure(
            provider=embedding.get('provider', 'Mistral'),
            api_key=embedding.get('api_key', ''),
            model=embedding.get('api_model', 'mistral-embed')
        )
        print(f"✅ Embedder configuré: {embedding.get('provider')}/{embedding.get('api_model')}")
        
    def backup_database(self):
        """Crée une sauvegarde de la base avant migration"""
        backup_path = DB_PATH.parent / f"memories_backup_{BACKUP_SUFFIX}.db"
        
        import shutil
        shutil.copy(DB_PATH, backup_path)
        print(f"💾 Backup créé: {backup_path}")
        
        # Backup FAISS aussi
        if FAISS_PATH.exists():
            faiss_backup = FAISS_PATH.parent / f"faiss_index_backup_{BACKUP_SUFFIX}.bin"
            shutil.copy(FAISS_PATH, faiss_backup)
            print(f"💾 Backup FAISS: {faiss_backup}")
            
        return backup_path
        
    def get_memories_to_migrate(self) -> list:
        """Récupère tous les souvenirs à migrer"""
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            
            query = """
                SELECT id, title, summary, text_original, embedding_json, faiss_index
                FROM memories 
                WHERE text_original IS NOT NULL 
                AND text_original != ''
            """
            
            if self.skip_ego:
                query += " AND id NOT LIKE 'EGO_%'"
                
            query += " ORDER BY created_at DESC"
            
            if self.limit:
                query += f" LIMIT {self.limit}"
                
            cursor = conn.execute(query)
            memories = [dict(row) for row in cursor.fetchall()]
            
        print(f"📊 {len(memories)} souvenirs à migrer")
        return memories
        
    async def regenerate_jeopardy(self, memory: dict) -> dict:
        """Régénère titre et résumé au format Jeopardy via l'Archiviste"""
        try:
            prompt = JEOPARDY_PROMPT.format(
                current_title=memory.get('title', 'N/A'),
                current_summary=memory.get('summary', 'N/A'),
                text_original=memory.get('text_original', '')[:2000]  # Limiter pour éviter tokens excessifs
            )
            
            messages = [{"role": "user", "content": prompt}]
            
            # Appel API via APIManager configuré
            response, error = await self.archiviste_api.call_chat_api(
                messages=messages,
                max_tokens=500,
                context_length=4000,
                temperature=0.3,
                is_json=True
            )
            
            if error or not response:
                raise Exception(f"Erreur Archiviste: {error}")
                
            # Parser la réponse JSON
            content = response.get('content', '') if isinstance(response, dict) else str(response)
            
            # Nettoyer les balises markdown
            import re
            cleaned = content.strip()
            
            # Retirer ```json ... ``` ou ``` ... ```
            if cleaned.startswith('```'):
                match = re.search(r'```(?:json)?\s*\n?(.*?)```', cleaned, re.DOTALL)
                if match:
                    cleaned = match.group(1).strip()
            
            # Trouver le JSON dans le texte (entre { et })
            json_match = re.search(r'\{[^{}]*\}', cleaned, re.DOTALL)
            if json_match:
                cleaned = json_match.group(0)
                    
            result = json.loads(cleaned)
            return {
                'title': result.get('titre', result.get('title', memory.get('title'))),
                'summary': result.get('résumé', result.get('resume', result.get('summary', memory.get('summary'))))
            }
        except Exception as e:
            raise Exception(f"{type(e).__name__}: {e}")
        
    async def generate_new_embedding(self, title: str, summary: str) -> np.ndarray:
        """Génère un nouvel embedding sur titre+résumé uniquement"""
        semantic_content = f"{title} {summary}".strip()
        
        # Appel API embedding via APIManager configuré
        embedding = await self.embedder_api.create_embedding(text=semantic_content)
        
        if embedding is None:
            raise Exception("Échec génération embedding")
            
        return np.array(embedding, dtype=np.float32)
        
    def update_memory(self, memory_id: str, new_title: str, new_summary: str, new_embedding: np.ndarray):
        """Met à jour le souvenir en base"""
        embedding_json = json.dumps(new_embedding.tolist())
        
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                UPDATE memories 
                SET title = ?, summary = ?, embedding_json = ?
                WHERE id = ?
            """, (new_title, new_summary, embedding_json, memory_id))
            conn.commit()
            
    async def migrate_single(self, memory: dict, index: int, total: int) -> bool:
        """Migre un seul souvenir"""
        memory_id = memory['id']
        old_title = memory.get('title', 'N/A')
        
        print(f"\n[{index+1}/{total}] {memory_id}")
        print(f"   Ancien titre: {old_title[:60]}...")
        
        try:
            # 1. Régénérer titre/résumé Jeopardy
            new_data = await self.regenerate_jeopardy(memory)
            new_title = new_data['title']
            new_summary = new_data['summary']
            
            print(f"   ✅ Nouveau titre: {new_title[:60]}...")
            print(f"   ✅ Nouveau résumé: {new_summary[:60]}...")
            
            # 2. Générer nouvel embedding
            new_embedding = await self.generate_new_embedding(new_title, new_summary)
            print(f"   ✅ Embedding: {len(new_embedding)}D")
            
            # 3. Sauvegarder si pas dry-run
            if not self.dry_run:
                self.update_memory(memory_id, new_title, new_summary, new_embedding)
                print(f"   💾 Sauvegardé")
            else:
                print(f"   ⏸️  [DRY-RUN] Non sauvegardé")
                
            self.stats['migrated'] += 1
            return True
            
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            self.stats['errors'] += 1
            return False
            
    async def rebuild_faiss_index(self):
        """Reconstruit l'index FAISS depuis les embeddings en base"""
        if self.dry_run:
            print("\n⏸️  [DRY-RUN] Reconstruction FAISS ignorée")
            return
            
        print("\n🔧 Reconstruction de l'index FAISS...")
        
        try:
            import faiss
        except ImportError:
            print("❌ FAISS non disponible - skip reconstruction")
            return
            
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute("""
                SELECT id, embedding_json 
                FROM memories 
                WHERE embedding_json IS NOT NULL
                ORDER BY created_at
            """)
            
            embeddings = []
            id_mapping = {}
            
            for idx, (memory_id, embedding_json) in enumerate(cursor.fetchall()):
                try:
                    embedding = np.array(json.loads(embedding_json), dtype=np.float32)
                    embeddings.append(embedding)
                    id_mapping[idx] = memory_id
                except:
                    continue
                    
        if not embeddings:
            print("❌ Aucun embedding trouvé")
            return
            
        # Créer l'index FAISS
        dimension = len(embeddings[0])
        index = faiss.IndexFlatL2(dimension)
        
        embeddings_matrix = np.vstack(embeddings).astype(np.float32)
        index.add(embeddings_matrix)
        
        # Sauvegarder
        faiss.write_index(index, str(FAISS_PATH))
        
        # Mettre à jour les faiss_index dans la DB
        with sqlite3.connect(DB_PATH) as conn:
            for idx, memory_id in id_mapping.items():
                conn.execute(
                    "UPDATE memories SET faiss_index = ? WHERE id = ?",
                    (idx, memory_id)
                )
            conn.commit()
            
        print(f"✅ Index FAISS reconstruit: {index.ntotal} vecteurs")
        
    async def run(self):
        """Lance la migration complète"""
        await self.initialize()
        
        # Backup
        if not self.dry_run:
            self.backup_database()
        
        # Récupérer souvenirs
        memories = self.get_memories_to_migrate()
        self.stats['total'] = len(memories)
        
        if not memories:
            print("✅ Aucun souvenir à migrer")
            return
            
        # Confirmation
        if not self.dry_run:
            print(f"\n⚠️  Cette opération va modifier {len(memories)} souvenirs.")
            confirm = input("Continuer ? (oui/non): ")
            if confirm.lower() != 'oui':
                print("❌ Migration annulée")
                return
                
        # Migration
        print("\n" + "-"*70)
        print("🔄 MIGRATION EN COURS...")
        print("-"*70)
        
        for i, memory in enumerate(memories):
            await self.migrate_single(memory, i, len(memories))
            
            # Pause pour éviter rate limiting
            if (i + 1) % 10 == 0:
                print(f"\n⏳ Pause 2s (rate limiting)...")
                await asyncio.sleep(2)
                
        # Reconstruction FAISS
        await self.rebuild_faiss_index()
        
        # Stats finales
        print("\n" + "="*70)
        print("📊 RÉSUMÉ MIGRATION")
        print("="*70)
        print(f"   Total souvenirs: {self.stats['total']}")
        print(f"   ✅ Migrés: {self.stats['migrated']}")
        print(f"   ⏭️  Ignorés: {self.stats['skipped']}")
        print(f"   ❌ Erreurs: {self.stats['errors']}")
        
        if not self.dry_run:
            print(f"\n💾 Migration terminée avec succès!")
            print(f"   Backup disponible: memories_backup_{BACKUP_SUFFIX}.db")
        else:
            print(f"\n⏸️  Mode DRY-RUN - Aucune modification appliquée")
            print(f"   Relancez sans --dry-run pour appliquer les changements")


def main():
    parser = argparse.ArgumentParser(description="Migration vers format Jeopardy")
    parser.add_argument('--dry-run', action='store_true', help="Mode test sans modification")
    parser.add_argument('--limit', type=int, default=None, help="Limite le nombre de souvenirs")
    parser.add_argument('--skip-ego', action='store_true', help="Ignore les souvenirs EGO")
    
    args = parser.parse_args()
    
    migrator = JeopardyMigrator(
        dry_run=args.dry_run,
        limit=args.limit,
        skip_ego=args.skip_ego
    )
    
    asyncio.run(migrator.run())


if __name__ == "__main__":
    main()
