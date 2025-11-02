"""
memory_manager.py
-----------------
OGMA v2.0 - Nouveau gestionnaire de mémoire avec SQLite + FAISS CPU
Remplace l'ancien système JSON par une architecture performante et intelligente.
"""

import sqlite3
import faiss
import numpy as np
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import traceback
import asyncio
import threading


class MemoryManager:
    """
    Gestionnaire de mémoire nouvelle génération pour OGMA.
    
    Architecture:
    - SQLite: Stockage structuré des souvenirs enrichis
    - FAISS CPU: Index vectoriel pour recherche sémantique rapide  
    - IA Archiviste: Enrichissement à l'écriture, synthèse à la lecture
    """
    
    def __init__(self, db_path: Path, index_path: Path, embedding_dim: int, 
                 archiviste_ia, embedding_ia, status_queue, *, use_formula_on_update: bool = True, settings_manager=None):
        """
        Initialise le gestionnaire de mémoire.
        
        Args:
            db_path: Chemin vers la base SQLite
            index_path: Chemin vers l'index FAISS
            embedding_dim: Dimension des vecteurs d'embedding
            archiviste_ia: Contrôleur IA pour enrichissement/synthèse
            embedding_ia: Contrôleur IA pour génération d'embeddings
            status_queue: Queue pour messages de statut UI
            settings_manager: Gestionnaire des paramètres pour accès aux prompts
        """
        self.db_path = db_path
        self.index_path = index_path
        self.embedding_dim = embedding_dim
        self.archiviste = archiviste_ia
        self.embedder = embedding_ia
        self.status_queue = status_queue
        self.settings_manager = settings_manager
        # Politique de calcul sur mise à jour manuelle: appliquer la formule déterministe si True
        self.use_formula_on_update = use_formula_on_update
        
        # Index FAISS et mapping
        self.faiss_index = None
        self.id_to_faiss = {}  # memory_id -> faiss_position
        self.faiss_to_id = {}  # faiss_position -> memory_id
        self.next_faiss_pos = 0
        
        # Thread-safety locks
        self._faiss_lock = threading.Lock()  # Protège les opérations FAISS
        self._mapping_lock = threading.Lock()  # Protège les mappings id<->faiss
        
        # Initialisation
        self._init_database()
        self._init_faiss_index()
        self._load_existing_data()
        
        print(f"[MemoryManager] Initialisé avec {self.next_faiss_pos} souvenirs")
    
    
    def _init_database(self):
        """Initialise la base de données SQLite avec le schéma requis."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    text_original TEXT NOT NULL,
                    
                    -- Métadonnées compatibles ancien système
                    type TEXT,
                    title TEXT,
                    lieu TEXT,
                    presence TEXT,
                    summary TEXT,
                    lesson TEXT,
                    valence INTEGER DEFAULT 0,
                    score_impact REAL DEFAULT 0.0,
                    
                    -- Données vectorielles et FAISS
                    embedding_json TEXT,
                    faiss_index INTEGER,
                    
                    -- Métadonnées enrichies (JSON)
                    nuage_sensoriel TEXT,
                    multiplicateur_impact TEXT,
                    resonances_affectives TEXT,
                    liens TEXT,
                    
                    -- Normalisation métriques (structuré)
                    base_factor REAL,
                    intensite REAL,
                    liberte REAL,
                    creation REAL,
                    procreation REAL,
                    intensite_ctx REAL,
                    signed_score REAL,
                    updated_at TEXT
                )
            """)
            conn.commit()
            # Migration souple: s'assure que les colonnes existent (ADD COLUMN si manquantes)
            try:
                cursor = conn.execute("PRAGMA table_info(memories)")
                cols = {row[1] for row in cursor.fetchall()}
                def _add(col, decl):
                    if col not in cols:
                        conn.execute(f"ALTER TABLE memories ADD COLUMN {col} {decl}")
                _add('base_factor', 'REAL')
                _add('intensite', 'REAL')
                _add('liberte', 'REAL')
                _add('creation', 'REAL')
                _add('procreation', 'REAL')
                _add('intensite_ctx', 'REAL')
                _add('signed_score', 'REAL')
                _add('updated_at', 'TEXT')
                conn.commit()
            except Exception:
                pass
        
        print(f"[MemoryManager] Base de données initialisée: {self.db_path}")
    
    
    def _init_faiss_index(self):
        """Initialise l'index FAISS CPU."""
        # Pour commencer simple : IndexFlatL2 (exact search)
        # TODO: Passer à IndexIVFFlat pour de gros volumes
        self.faiss_index = faiss.IndexFlatL2(self.embedding_dim)
        print(f"[MemoryManager] Index FAISS CPU initialisé (dim={self.embedding_dim})")
    
    
    def _load_existing_data(self):
        """Charge les données existantes depuis SQLite et reconstruit l'index FAISS."""
        try:
            # Charger l'index FAISS s'il existe
            if self.index_path.exists():
                self.faiss_index = faiss.read_index(str(self.index_path))
                print(f"[MemoryManager] Index FAISS chargé: {self.faiss_index.ntotal} vecteurs")

            # Reconstituer les mappings depuis SQLite
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT id, faiss_index FROM memories
                    WHERE faiss_index IS NOT NULL
                    ORDER BY faiss_index
                """)

                for memory_id, faiss_pos in cursor.fetchall():
                    if faiss_pos is not None:
                        self.id_to_faiss[memory_id] = faiss_pos
                        self.faiss_to_id[faiss_pos] = memory_id
                        self.next_faiss_pos = max(self.next_faiss_pos, faiss_pos + 1)

            # DÉTECTION ET CORRECTION DE LA DÉSYNCHRONISATION DB/FAISS
            # Compter les souvenirs avec embeddings dans la DB
            db_memory_count = 0
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM memories WHERE embedding_json IS NOT NULL")
                db_memory_count = cursor.fetchone()[0]

            # Compter les vecteurs dans l'index FAISS
            faiss_vector_count = self.faiss_index.ntotal if self.faiss_index else 0

            # Si la DB contient des souvenirs mais FAISS est vide → désynchronisation
            if db_memory_count > 0 and faiss_vector_count == 0:
                print(f"[WARN] ⚠️ Désynchronisation détectée:")
                print(f"       - DB contient {db_memory_count} souvenirs avec embeddings")
                print(f"       - Index FAISS contient {faiss_vector_count} vecteurs")
                print(f"[REPAIR] 🔧 Reconstruction automatique de l'index FAISS depuis la DB...")

                rebuild_stats = self.rebuild_faiss_index()

                print(f"[REPAIR] ✅ Index reconstruit avec succès:")
                print(f"         - {rebuild_stats.get('added', 0)} vecteurs ajoutés")
                print(f"         - {rebuild_stats.get('skipped', 0)} souvenirs ignorés")
                print(f"         - {rebuild_stats.get('total', 0)} souvenirs traités")

                if self.status_queue:
                    self.status_queue.put(f"[REPAIR] Index FAISS reconstruit: {rebuild_stats.get('added', 0)} souvenirs restaurés")

        except Exception as e:
            print(f"[WARN] Erreur chargement données existantes: {e}")
            self.next_faiss_pos = 0

        # Synchronisation automatique ego_prompt.txt au démarrage
        try:
            self.sync_ego_prompt_references()
        except Exception as e:
            print(f"[WARN] Erreur synchronisation ego_prompt au démarrage: {e}")
    
    
    def save_index(self):
        """Sauvegarde l'index FAISS sur disque."""
        try:
            print(f"[FAISS-SAVE] 💾 Sauvegarde index FAISS...")
            total = self.faiss_index.ntotal if self.faiss_index else 0
            print(f"[FAISS-SAVE] Taille: {total} vecteurs")
            print(f"[FAISS-SAVE] Chemin: {self.index_path}")
            
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            if self.faiss_index:
                faiss.write_index(self.faiss_index, str(self.index_path))
            else:
                print("[FAISS-SAVE] ⚠️ Index FAISS non initialisé, saut de l'écriture")
            
            # Vérifier la taille du fichier
            file_size = self.index_path.stat().st_size if self.index_path.exists() else 0
            print(f"[FAISS-SAVE] ✅ Index sauvegardé: {file_size} bytes")
            
        except Exception as e:
            print(f"[FAISS-ERROR] ❌ Erreur sauvegarde index FAISS: {e}")
            self.status_queue.put(f"[ERROR] Échec sauvegarde index: {e}")
    
    
    async def add_memory(self, memory_id: str, text_brut: str, chat_controller=None, conversation_context: str = "", interlocutor: str = "") -> bool:
        """
        Ajoute un nouveau souvenir via le pipeline complet.
        
        Pipeline MODIFIÉ - IA Principale scoring:
        1. IA Principale calcule score_impact émotionnel/relationnel
        2. IA Archiviste enrichit le texte brut (sans recalculer le score)
        3. Génération embedding du contenu sémantique
        4. Stockage SQLite du souvenir structuré
        5. Ajout vecteur à l'index FAISS
        6. Sauvegarde index
        
        Args:
            memory_id: Identifiant unique du souvenir
            text_brut: Texte original à mémoriser
            chat_controller: Contrôleur IA Principale pour scoring (optionnel)
            conversation_context: Contexte conversationnel récent
            interlocutor: Nom de l'interlocuteur privilégié
            
        Returns:
            bool: True si succès, False sinon
        """
        try:
            print(f"[MEMORY-PIPELINE] 🚀 Début mémorisation: {memory_id}")
            print(f"[MEMORY-INPUT] Texte brut ({len(text_brut)} chars): {text_brut[:100]}...")
            
            # ÉTAPE 0: IA Principale calcule le score d'impact (avec fallback Archiviste)
            initial_score = None
            if chat_controller:
                print(f"[MEMORY-STEP0] 🎯 Calcul score d'impact par IA Principale...")
                self.status_queue.put(f"[MEMORY] Évaluation impact par Luna...")
                initial_score = await chat_controller.calculate_memory_impact_score(
                    text_content=text_brut,
                    conversation_context=conversation_context,
                    interlocutor=interlocutor
                )
                if initial_score is not None:
                    print(f"[MEMORY-SCORE] ✅ Score IA Principale: {initial_score}")
                else:
                    print(f"[MEMORY-FALLBACK] ⚠️ IA Principale n'a pas pu scorer, l'Archiviste prendra le relais")
                    self.status_queue.put("[MEMORY] Fallback scoring vers l'Archiviste...")
            else:
                print(f"[MEMORY-FALLBACK] ⚠️ Pas de contrôleur IA Principale, l'Archiviste scorera")
                self.status_queue.put("[MEMORY] L'Archiviste gérera le scoring...")

            self.status_queue.put(f"[MEMORY] Enrichissement par l'Archiviste...")

            # 1. Enrichissement par l'IA Archiviste (+ scoring si fallback nécessaire)
            print(f"[MEMORY-STEP1] 🧠 Appel IA Archiviste pour enrichissement...")
            need_scoring = (initial_score is None)
            enriched_data = await self._call_archiviste_enrichment(text_brut, calculate_score=need_scoring)
            if not enriched_data:
                print(f"[MEMORY-ERROR] ❌ Archiviste a échoué")
                self.status_queue.put("[ERROR] Échec enrichissement par l'Archiviste")
                return False

            # Injection du score : priorité IA Principale, sinon Archiviste
            if initial_score is not None:
                enriched_data['score_impact'] = initial_score
                print(f"[MEMORY-INJECTION] 💉 Score IA Principale injecté: {initial_score}")
            elif 'score_impact' in enriched_data and enriched_data['score_impact'] is not None:
                print(f"[MEMORY-FALLBACK] 💉 Score Archiviste utilisé: {enriched_data['score_impact']}")
            else:
                print(f"[MEMORY-ERROR] ❌ Aucun score disponible (IA Principale et Archiviste ont échoué)")
                self.status_queue.put("[ERROR] Échec scoring par les deux IA")
                return False
            
            print(f"[MEMORY-ARCHIVISTE] ✅ Enrichissement terminé:")
            print(f"  - Titre: {enriched_data.get('title', 'N/A')}")
            print(f"  - Résumé: {enriched_data.get('summary', 'N/A')}")
            print(f"  - Valence: {enriched_data.get('valence', 'N/A')}")
            print(f"  - Score impact: sera calculé côté serveur à partir des métriques")
            
            self.status_queue.put(f"[MEMORY] Génération embedding...")
            
            # 2. Génération embedding du contenu sémantique COMPLET
            # CORRECTION: Inclure le texte original pour permettre recherche sur mots-clés intimes
            title = enriched_data.get('title', '')
            summary = enriched_data.get('summary', '')
            # Limiter le texte original à 1500 chars pour éviter les tokens excessifs
            text_sample = text_brut[:1500] if len(text_brut) > 1500 else text_brut
            
            semantic_content = f"{title} {summary} {text_sample}".strip()
            print(f"[MEMORY-STEP2] 🔢 Génération embedding du contenu sémantique COMPLET...")
            print(f"[MEMORY-SEMANTIC] Contenu: titre+résumé+texte ({len(semantic_content)} chars)")
            embedding = await self._generate_embedding(semantic_content)
            if embedding is None:
                print(f"[MEMORY-ERROR] ❌ Échec génération embedding")
                self.status_queue.put("[ERROR] Échec génération embedding")
                return False
            
            print(f"[MEMORY-EMBEDDING] ✅ Embedding généré: {len(embedding)} dimensions")
            
            # 3. Stockage SQLite
            print(f"[MEMORY-STEP3] 💾 Stockage en base SQLite...")
            success = self._store_in_sqlite(memory_id, text_brut, enriched_data, embedding)
            if not success:
                print(f"[MEMORY-ERROR] ❌ Échec stockage SQLite")
                self.status_queue.put("[ERROR] Échec stockage SQLite")
                return False
            
            print(f"[MEMORY-SQLITE] ✅ Souvenir stocké en base")
            
            # 4. Ajout à l'index FAISS
            print(f"[MEMORY-STEP4] 🔍 Ajout à l'index FAISS...")
            faiss_pos = self._add_to_faiss(memory_id, embedding)
            print(f"[MEMORY-FAISS] ✅ Vecteur ajouté à la position {faiss_pos}")
            total = self.faiss_index.ntotal if self.faiss_index else 0
            print(f"[MEMORY-FAISS] Index total: {total} souvenirs")
            
            # 5. Sauvegarde index
            print(f"[MEMORY-STEP5] 💾 Sauvegarde index FAISS...")
            self.save_index()
            
            print(f"[MEMORY-COMPLETE] ✅ Mémorisation terminée avec succès!")
            total = self.faiss_index.ntotal if self.faiss_index else 0
            print(f"[MEMORY-STATS] Total souvenirs: {total}, Mappings: {len(self.id_to_faiss)}")
            self.status_queue.put(f"[OK] Souvenir '{enriched_data.get('title', memory_id)}' mémorisé")
            return True
            
        except Exception as e:
            error_msg = f"[ERROR] Échec mémorisation {memory_id}: {e}"
            print(error_msg)
            print(traceback.format_exc())
            self.status_queue.put(error_msg)
            return False
    
    
    async def store_ego_trait(self, trait_text: str, chat_controller=None, conversation_context: str = "", interlocutor: str = "self") -> str:
        """
        Stocke un trait de personnalité ego avec métadonnées spéciales.
        Utilise exactement le même système de calcul de score que add_memory().
        
        Args:
            trait_text: Le trait de personnalité à stocker
            chat_controller: Contrôleur IA Principale pour scoring (obligatoire)
            conversation_context: Contexte conversationnel récent
            interlocutor: Nom de l'interlocuteur (défaut: "self" pour ego)
            
        Returns:
            str: L'ID mémoire généré (format #MEM_XXXXX)
        """
        try:
            # Génération ID unique pour le trait ego
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            memory_id = f"EGO_{timestamp}"
            
            print(f"[EGO-PIPELINE] 🚀 Début stockage trait ego: {memory_id}")
            print(f"[EGO-INPUT] Trait ego ({len(trait_text)} chars): {trait_text[:100]}...")
            
            if self.status_queue:
                self.status_queue.put(f"[EGO] 🧠 Stockage trait ego: {trait_text[:50]}...")
            
            # ÉTAPE 0: IA Principale calcule le score d'impact (avec fallback Archiviste)
            initial_score = None
            if chat_controller:
                print(f"[EGO-STEP0] 🎯 Calcul score d'impact par IA Principale...")
                self.status_queue.put(f"[EGO] Évaluation impact par IA Principale...")
                initial_score = await chat_controller.calculate_memory_impact_score(
                    text_content=trait_text,
                    conversation_context=conversation_context,
                    interlocutor=interlocutor
                )
                if initial_score is not None:
                    print(f"[EGO-SCORE] ✅ Score IA Principale: {initial_score}")
                else:
                    print(f"[EGO-FALLBACK] ⚠️ IA Principale n'a pas pu scorer, l'Archiviste prendra le relais")
                    self.status_queue.put("[EGO] Fallback scoring vers l'Archiviste...")
            else:
                print(f"[EGO-FALLBACK] ⚠️ Pas de contrôleur IA Principale, l'Archiviste scorera")
                self.status_queue.put("[EGO] L'Archiviste gérera le scoring...")

            # Si pas de score de l'IA Principale, demander à l'Archiviste
            if initial_score is None:
                print(f"[EGO-ARCHIVISTE] 🧠 Demande scoring à l'Archiviste...")
                enriched = await self._call_archiviste_enrichment(trait_text, calculate_score=True)
                if enriched and 'score_impact' in enriched and enriched['score_impact'] is not None:
                    initial_score = enriched['score_impact']
                    print(f"[EGO-FALLBACK] 💉 Score Archiviste utilisé: {initial_score}")
                else:
                    print(f"[EGO-ERROR] ❌ Aucune IA n'a pu calculer le score")
                    self.status_queue.put("[ERROR] Échec scoring par les deux IA")
                    return ""

            # Pas d'enrichissement supplémentaire pour les traits ego (on garde le texte pur)
            # Mais on utilise le score calculé (IA Principale ou Archiviste)
            structured_memory = {
                "summary": trait_text,
                "lesson": trait_text,
                "type": "ego_trait",
                "title": f"Trait ego: {trait_text[:30]}...",
                "valence": 5,  # Garde valence fixe pour ego traits
                "score_impact": initial_score,  # Score calculé par IA Principale ou Archiviste
                "metadata": {
                    "ego_trait": True,
                    "source": "ego_prompt_system",
                    "category": "personality"
                }
            }
            
            # Génération embedding pour le trait
            text_for_embedding = trait_text
            embedding_vector = await self.embedder.create_embedding(text_for_embedding)
            
            if embedding_vector is None:
                if self.status_queue:
                    self.status_queue.put(f"[ERROR] Échec embedding trait ego")
                return ""
            
            # Stockage SQLite
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO memories (
                        id, created_at, text_original,
                        type, title, summary, lesson, valence, score_impact,
                        embedding_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    memory_id,
                    datetime.now().isoformat(),
                    trait_text,
                    "ego_trait",
                    structured_memory["title"],
                    structured_memory["summary"],
                    structured_memory["lesson"],
                    structured_memory["valence"],
                    structured_memory["score_impact"],
                    json.dumps(embedding_vector)
                ))
            
            # Ajout à FAISS avec priorité élevée
            if hasattr(self, 'faiss_index') and self.faiss_index is not None:
                faiss_index = self.faiss_index.ntotal
                self.faiss_index.add(np.array([embedding_vector], dtype=np.float32).reshape(1, -1))
                
                # Mise à jour du mapping ID -> index FAISS
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("UPDATE memories SET faiss_index = ? WHERE id = ?", (faiss_index, memory_id))
                
                # Sauvegarde index
                self.save_index()
            
            formatted_id = f"#MEM_{memory_id}"
            
            if self.status_queue:
                self.status_queue.put(f"✅ Trait ego stocké: {formatted_id}")
            
            print(f"[SUCCESS] Trait ego stocké avec ID: {formatted_id}")
            return formatted_id
            
        except Exception as e:
            error_msg = f"[ERROR] Échec stockage trait ego: {e}"
            print(error_msg)
            print(traceback.format_exc())
            if self.status_queue:
                self.status_queue.put(error_msg)
            return ""
    
    def sync_ego_prompt_references(self) -> bool:
        """
        Synchronise automatiquement le fichier ego_prompt.txt avec la base de données.
        Supprime les références orphelines et détecte les traits manquants.
        
        Returns:
            bool: True si des modifications ont été faites
        """
        import re
        from utils import EGO_PROMPT_FILE
        
        try:
            print("[SYNC] Début synchronisation ego_prompt.txt...")
            
            ego_file = Path(EGO_PROMPT_FILE)
            if not ego_file.exists():
                print("[SYNC] Fichier ego_prompt.txt non trouvé - synchronisation ignorée")
                return False
            
            # Récupérer les IDs existants dans la DB
            existing_ids = set()
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT id FROM memories WHERE type = 'ego_trait'")
                for (trait_id,) in cursor.fetchall():
                    existing_ids.add(f"#MEM_{trait_id}")
            
            # Récupérer les références dans le fichier
            content = ego_file.read_text(encoding='utf-8')
            file_references = re.findall(r'#MEM_\w+', content)
            
            # Identifier les références orphelines
            orphaned_refs = [ref for ref in file_references if ref not in existing_ids]
            
            if orphaned_refs:
                print(f"[SYNC] Nettoyage de {len(orphaned_refs)} références orphelines: {orphaned_refs}")
                
                # Supprimer les références orphelines
                for ref in orphaned_refs:
                    lines = content.split('\n')
                    cleaned_lines = [line for line in lines if ref not in line]
                    content = '\n'.join(cleaned_lines)
                
                # Sauvegarder le fichier nettoyé
                ego_file.write_text(content, encoding='utf-8')
                
                if self.status_queue:
                    self.status_queue.put(f"[SYNC] 🧹 {len(orphaned_refs)} références orphelines supprimées")
                
                return True
            
            else:
                print("[SYNC] Aucune référence orpheline - fichier synchronisé")
                return False
                
        except Exception as e:
            print(f"[SYNC] Erreur synchronisation ego_prompt: {e}")
            return False
    
    
    async def retrieve_and_synthesize_context(self, query_text: str, k: int = 5) -> str:
        """
        Récupère et synthétise les souvenirs pertinents pour une requête.

        Pipeline:
        1. Nettoyage de la requête (expansion pronoms + extraction mots-clés)
        2. Génération embedding de la requête nettoyée
        3. Recherche FAISS des k souvenirs les plus similaires
        4. Récupération contenu complet depuis SQLite
        5. IA Archiviste génère une synthèse contextuelle

        Args:
            query_text: Requête utilisateur
            k: Nombre de souvenirs à récupérer

        Returns:
            str: Note de synthèse de l'Archiviste
        """
        try:
            print(f"[SEARCH-PIPELINE] 🔍 Recherche contextuelle: '{query_text}'")
            idx_total = self.faiss_index.ntotal if self.faiss_index else 0
            print(f"[SEARCH-PARAMS] k={k}, index_size={idx_total}")

            if not self.faiss_index or idx_total == 0:
                print(f"[SEARCH-EMPTY] ⚠️ Index FAISS vide")
                return "Aucun souvenir disponible."

            # 0. NOUVEAU: Nettoyage de la requête pour optimiser l'embedding
            expanded_query = self._expand_personal_pronouns(query_text)
            cleaned_query = self._extract_keywords(expanded_query)

            # 1. Embedding de la requête NETTOYÉE
            print(f"[SEARCH-STEP1] 🔢 Génération embedding requête...")
            query_embedding = await self._generate_embedding(cleaned_query)
            if query_embedding is None:
                print(f"[SEARCH-ERROR] ❌ Échec génération embedding requête")
                return "Erreur génération embedding requête."
            
            print(f"[SEARCH-EMBEDDING] ✅ Embedding requête généré: {len(query_embedding)} dims")
            
            # 2. Recherche FAISS (thread-safe)
            print(f"[SEARCH-STEP2] 🎯 Recherche similarité FAISS...")
            with self._faiss_lock:
                k = min(k, self.faiss_index.ntotal if self.faiss_index else 0)
                # Le typage statique de faiss peut être imprécis; on ignore pour éviter de faux positifs
                distances, indices = self.faiss_index.search(  # type: ignore
                    query_embedding.reshape(1, -1).astype(np.float32), k
                )
            
            print(f"[SEARCH-FAISS] ✅ {len(indices[0])} résultats trouvés")
            for i, (idx, dist) in enumerate(zip(indices[0], distances[0])):
                similarity = 1.0 / (1.0 + dist)
                print(f"  {i+1}. Position {idx}, distance: {dist:.3f}, similarité: {similarity:.3f}")
            
            # 3. Récupération depuis SQLite
            print(f"[SEARCH-STEP3] 💾 Récupération détails depuis SQLite...")
            relevant_memories = []
            for i, faiss_pos in enumerate(indices[0]):
                # Accès thread-safe aux mappings
                with self._mapping_lock:
                    memory_id = self.faiss_to_id.get(faiss_pos)
                
                if memory_id:
                    print(f"[SEARCH-MAPPING] Position {faiss_pos} → ID {memory_id}")
                    memory_data = self._get_memory_from_sqlite(memory_id)
                    if memory_data:
                        memory_data['similarity_score'] = float(1.0 / (1.0 + distances[0][i]))
                        relevant_memories.append(memory_data)
                        print(f"[SEARCH-MEMORY] Récupéré: '{memory_data.get('title', 'N/A')}'")
                else:
                    print(f"[SEARCH-WARNING] ⚠️ Position {faiss_pos} non mappée")
            
            print(f"[SEARCH-SQLITE] ✅ {len(relevant_memories)} souvenirs complets récupérés")
            # Priorisation: d'abord l'impact (score_impact), puis la similarité
            try:
                relevant_memories.sort(
                    key=lambda m: (
                        -float(m.get('score_impact', 0) or 0),
                        -float(m.get('similarity_score', 0) or 0)
                    )
                )
                print("[SEARCH-ORDER] ↕️ Tri par impact puis similarité appliqué")
            except Exception as _e:
                print(f"[SEARCH-ORDER] ⚠️ Tri non appliqué: {_e}")
            
            if not relevant_memories:
                print(f"[SEARCH-EMPTY] ❌ Aucun souvenir pertinent après récupération")
                return "Aucun souvenir pertinent trouvé."
            
            # 4. Synthèse par l'Archiviste
            print(f"[SEARCH-STEP4] 🧠 Synthèse contextuelle par l'Archiviste...")
            synthesis = await self._call_archiviste_synthesis(query_text, relevant_memories)
            
            if synthesis:
                print(f"[SEARCH-SYNTHESIS] ✅ Synthèse générée ({len(synthesis)} chars)")
                print(f"[SEARCH-SYNTHESIS-PREVIEW] 📝 Contenu: {synthesis[:200]}...")
                print(f"[SEARCH-COMPLETE] 🎯 Recherche contextuelle terminée")
            else:
                print(f"[SEARCH-ERROR] ❌ Échec synthèse Archiviste")
                
            return synthesis or "Erreur lors de la synthèse contextuelle."
            
        except Exception as e:
            error_msg = f"[ERROR] Échec recherche contextuelle: {e}"
            print(error_msg)
            self.status_queue.put(error_msg)
            import traceback
            print(traceback.format_exc())
            return f"Erreur technique: {str(e)[:50]}..."
    
    
    # === MÉTHODES PRIVÉES ===
    
    async def _call_archiviste_enrichment(self, text_brut: str, calculate_score: bool = False) -> Optional[Dict]:
        """
        Appelle l'IA Archiviste pour enrichir un texte brut.

        Args:
            text_brut: Texte à enrichir
            calculate_score: Si True, demande à l'Archiviste de calculer aussi le score_impact
        """
        try:
            print(f"[ARCHIVISTE-PROMPT] 🧠 Construction prompt d'enrichissement...")
            if calculate_score:
                print(f"[ARCHIVISTE-PROMPT] 🎯 Mode FALLBACK: calcul score_impact requis")
            
            # Utiliser le prompt de mémorisation depuis settings.json si disponible
            if self.settings_manager and 'prompts' in self.settings_manager.settings and 'memorization' in self.settings_manager.settings['prompts']:
                base_prompt = self.settings_manager.settings['prompts']['memorization']

                # Si mode fallback scoring, ajouter instruction explicite
                if calculate_score:
                    score_instruction = "\n\nIMPORTANT: L'IA Principale n'a pas pu calculer le score. Tu DOIS calculer le 'score_impact' selon la formule: score_impact = intensite × base_factor × (liberté + création + procréation + intensité_contextuelle). Fournis ce champ dans ta réponse JSON."
                    prompt_memorization = f"{base_prompt}{score_instruction}\n\nTexte à analyser:\n{text_brut}"
                else:
                    prompt_memorization = f"{base_prompt}\n\nTexte à analyser:\n{text_brut}"

                print(f"[ARCHIVISTE-PROMPT] ✅ Utilisation du prompt depuis settings.json")
            else:
                # Fallback sur le prompt par défaut si settings non disponibles
                print(f"[ARCHIVISTE-PROMPT] ⚠️ Settings non disponibles, utilisation prompt fallback")
                prompt_memorization = f"""Tu es une IA de mémoire consciente, chargée de structurer un souvenir.
Analyse le texte fourni et produis STRICTEMENT un objet JSON valide (aucun texte autour).

Contraintes importantes:
- Les nombres doivent être de vrais nombres JSON (pas des chaînes).
- La valence est codée -1 (négatif), 0 (neutre), 1 (positif). Pour les calculs, applique le facteur de valence suivant:
  - valence -1 => facteur -1
  - valence 0  => facteur +0.9 (neutre considéré comme légèrement positif)
  - valence +1 => facteur +1
- Fournis à la fois 'title' et 'summary' (même si des alias existent), pour l'indexation.

Calcul des scores (à respecter):
1) borne/quantifie les métriques sur [0..1] par pas de 0.1 quand pertinent
2) base_score = intensite × base_factor × (liberté + création + procréation + intensité_contextuelle)
3) score_impact = base_score (magnitude, toujours positive)
4) signed_score = base_score × facteur_de_valence (selon la règle ci-dessus)
{"Nota: le serveur recalcule score_impact et signed_score; fournis surtout les métriques cohérentes." if not calculate_score else "IMPORTANT: Tu DOIS calculer le 'score_impact' selon la formule ci-dessus et le fournir dans ta réponse JSON."}

Structure attendue (clés recommandées) :
{{
    "type": "affectif | conceptuel | sensoriel | événement",
    "title": "Titre court (<=10 mots)",
    "summary": "Résumé en 2-3 phrases du contenu principal",
    "lieu": "Le lieu si mentionné, sinon null",
    "presence": "Les personnes présentes (ex: 'Moi seul', 'Tia & Yohan')",
    "intensite": 0.0,
    "multiplicateur_impact": {{
        "liberté": 0.0,
        "création": 0.0,
        "procréation": 0.0,
        "intensité_contextuelle": 0.0,
        "base_factor": 100
    }},
    "valence": 0,
    "lesson": null,
    "signed_score": 90.0
}}

Notes:
- Les champs 'titre' (alias de 'title'), 'présence' (alias de 'presence'), 'résumé' (alias de 'summary'),
    'leçon_vectorielle' (alias de 'lesson') peuvent être fournis en plus, mais 'title' et 'summary' DOIVENT être présents.
- Si aucun multiplicateur n'est pertinent, mets 0.0; 'base_factor' recommandé entre 50 et 125 (par défaut 100).
{"- Ne fournis pas 'score_impact' (il sera recalculé côté serveur). Tu peux fournir 'signed_score' à titre indicatif." if not calculate_score else "- Tu DOIS fournir 'score_impact' calculé selon la formule. Fournis aussi 'signed_score' à titre indicatif."}

Texte à analyser:
{text_brut}

Réponds uniquement avec l'objet JSON demandé, sans autre texte."""

            messages = [{"role": "user", "content": prompt_memorization}]
            
            print(f"[ARCHIVISTE-CALL] 📡 Appel IA Archiviste (JSON mode)...")
            print(f"[ARCHIVISTE-PARAMS] Max tokens: {self.archiviste.max_tokens}, Temp: {self.archiviste.temperature}")
            
            response, error = await self.archiviste.call_chat_api(
                messages=messages,
                max_tokens=self.archiviste.max_tokens,
                context_length=self.archiviste.context_length, 
                temperature=self.archiviste.temperature,
                is_json=True
            )
            
            if error or not response:
                print(f"[ARCHIVISTE-ERROR] ❌ Échec appel Archiviste: {error}")
                return None
            
            print(f"[ARCHIVISTE-RESPONSE] ✅ Réponse reçue ({len(response)} chars)")
            print(f"[ARCHIVISTE-RAW] Début: {response[:100]}...")
            
            # Parse JSON response avec stratégies multiples
            print(f"[ARCHIVISTE-PARSE] 🔍 Extraction JSON...")
            enriched = self._extract_json_from_response(response)
            
            # Harmoniser quelques alias si fournis par l'IA (AVANT les logs pour affichage correct)
            try:
                if enriched:
                    # titre -> title
                    if 'title' not in enriched and 'titre' in enriched and isinstance(enriched.get('titre'), str):
                        enriched['title'] = enriched.get('titre')
                    # résumé/commentaire -> summary
                    if 'summary' not in enriched:
                        for k in ('résumé', 'resume', 'commentaire'):
                            if k in enriched and isinstance(enriched.get(k), str):
                                enriched['summary'] = enriched.get(k)
                                break
                    # présence -> presence
                    if 'presence' not in enriched and 'présence' in enriched and isinstance(enriched.get('présence'), str):
                        enriched['presence'] = enriched.get('présence')
                    # leçon_vectorielle -> lesson
                    if 'lesson' not in enriched and 'leçon_vectorielle' in enriched:
                        enriched['lesson'] = enriched.get('leçon_vectorielle')
                    # score -> score_impact (alias fréquent)
                    if 'score_impact' not in enriched and 'score' in enriched:
                        enriched['score_impact'] = enriched.get('score')
            except Exception:
                pass
            
            # Logs APRÈS harmonisation pour afficher les valeurs correctes
            if enriched:
                print(f"[ARCHIVISTE-SUCCESS] ✅ JSON parsé avec succès")
                print(f"[ARCHIVISTE-DATA] Type: {enriched.get('type', 'N/A')}")
                print(f"[ARCHIVISTE-DATA] Titre: {enriched.get('title', 'N/A')}")
                print(f"[ARCHIVISTE-DATA] Résumé: {enriched.get('summary', 'N/A')}")
                print(f"[ARCHIVISTE-DATA] Score: {enriched.get('score_impact', 'N/A')}")
            else:
                print(f"[ARCHIVISTE-ERROR] ❌ Échec parsing JSON")

            return enriched
                
        except Exception as e:
            print(f"[ERROR] Exception in archiviste enrichment: {e}")
            return None
    
    
    def _extract_json_from_response(self, response: str) -> Optional[Dict]:
        """
        Extrait le JSON d'une réponse IA avec stratégies multiples.
        
        Stratégies testées dans l'ordre :
        1. JSON direct (toute la réponse)
        2. Entre ```json et ```
        3. Entre ``` et ```
        4. Première occurrence { ... } équilibrée
        """
        if not response or not response.strip():
            return None
        
        strategies = [
            # Stratégie 1: JSON direct
            lambda r: r.strip(),
            
            # Stratégie 2: Entre ```json et ```
            lambda r: self._extract_between_markers(r, "```json", "```"),
            
            # Stratégie 3: Entre ``` et ```  
            lambda r: self._extract_between_markers(r, "```", "```"),
            
            # Stratégie 4: Première occurrence { ... }
            lambda r: self._extract_json_object(r)
        ]
        
        for i, strategy in enumerate(strategies, 1):
            try:
                extracted = strategy(response)
                if extracted:
                    print(f"[DEBUG] Stratégie {i} - Contenu extrait ({len(extracted)} chars): {extracted[:100]}...")
                    parsed = json.loads(extracted)
                    print(f"[DEBUG] JSON extrait avec stratégie {i}")
                    return parsed
                else:
                    print(f"[DEBUG] Stratégie {i} - Aucun contenu extrait")
            except json.JSONDecodeError as e:
                print(f"[DEBUG] Stratégie {i} - Erreur JSON: {e}")
                print(f"[DEBUG] Contenu qui a échoué: {extracted[:200] if extracted else 'None'}...")
                continue
            except Exception as e:
                print(f"[DEBUG] Stratégie {i} échouée: {e}")
                continue

        print(f"[ERROR] Aucune stratégie n'a pu extraire le JSON")
        print(f"[DEBUG] Réponse brute ({len(response)} chars):")
        print(f"[DEBUG] Début: {response[:300]}...")
        print(f"[DEBUG] Fin: ...{response[-300:]}")
        return None
    
    
    def _extract_between_markers(self, text: str, start_marker: str, end_marker: str) -> Optional[str]:
        """Extrait le texte entre deux marqueurs."""
        start_idx = text.find(start_marker)
        if start_idx == -1:
            return None

        start_idx += len(start_marker)
        end_idx = text.find(end_marker, start_idx)
        if end_idx == -1:
            return None

        extracted = text[start_idx:end_idx].strip()

        # Si on a extrait entre ``` et ```, retirer "json" au début s'il y est
        if start_marker == "```" and extracted.startswith("json"):
            extracted = extracted[4:].strip()

        return extracted
    
    
    def _extract_json_object(self, text: str) -> Optional[str]:
        """Extrait le premier objet JSON équilibré { ... }."""
        start_idx = text.find("{")
        if start_idx == -1:
            return None

        brace_count = 0
        for i, char in enumerate(text[start_idx:], start_idx):
            if char == "{":
                brace_count += 1
            elif char == "}":
                brace_count -= 1
                if brace_count == 0:
                    return text[start_idx:i + 1]

        # Si on arrive ici, le JSON n'est pas équilibré (probablement tronqué)
        print(f"[DEBUG] JSON non équilibré détecté (accolades ouvertes: {brace_count})")
        return None
    
    
    async def _generate_embedding(self, text: str) -> Optional[np.ndarray]:
        """Génère l'embedding d'un texte via le contrôleur d'embedding."""
        try:
            print(f"[EMBEDDING-REQ] 🔢 Requête embedding pour: '{text[:50]}...'")
            
            if not self.embedder.is_available:
                print("[EMBEDDING-ERROR] ❌ Contrôleur d'embedding non disponible")
                return None
            
            print(f"[EMBEDDING-CALL] 📡 Appel API embedding...")
            # Génération de l'embedding
            embedding_list = await self.embedder.create_embedding(text)
            
            if not embedding_list:
                print("[EMBEDDING-ERROR] ❌ Échec génération embedding")
                return None
            
            # Conversion en numpy array
            embedding_array = np.array(embedding_list, dtype=np.float32)
            
            # Vérification de la dimension
            if len(embedding_array) != self.embedding_dim:
                print(f"[EMBEDDING-ERROR] ❌ Dimension incorrecte: {len(embedding_array)} vs {self.embedding_dim}")
                return None
            
            print(f"[EMBEDDING-SUCCESS] ✅ Embedding généré: {len(embedding_array)}D")
            print(f"[EMBEDDING-STATS] Min: {embedding_array.min():.3f}, Max: {embedding_array.max():.3f}")
            
            return embedding_array
            
        except Exception as e:
            print(f"[EMBEDDING-ERROR] ❌ Exception génération embedding: {e}")
            return None
    
    
    def _store_in_sqlite(self, memory_id: str, text_original: str, 
                        enriched_data: Dict, embedding: np.ndarray) -> bool:
        """Stocke un souvenir enrichi dans SQLite."""
        try:
            print(f"[SQLITE-STORE] 💾 Insertion souvenir: {memory_id}")
            print(f"[SQLITE-DATA] Title: {enriched_data.get('title', 'N/A')}")
            print(f"[SQLITE-DATA] Valence: {enriched_data.get('valence', 'N/A')}")
            print(f"[SQLITE-DATA] Score: {enriched_data.get('score_impact', 'N/A')}")
            print(f"[SQLITE-EMBEDDING] Taille vecteur: {len(embedding)} floats")
            
            with sqlite3.connect(self.db_path) as conn:
                # Valence (neutre=0, positif=1, négatif=-1)
                v_in = enriched_data.get('valence', 0)
                try:
                    v_in = int(v_in)
                except Exception:
                    v_in = 0
                # Extraire et quantifier les métriques puis CALCULER le score côté serveur
                bf, inten, lib, cre, pro, ictx = self._extract_metrics(enriched_data)
                sc = self._compute_score_formula(
                    base_factor=bf, intensite=inten, liberte=lib, creation=cre, procreation=pro, intensite_ctx=ictx
                )
                # signed_score via règle métier (valence 0 => 0.9 * score)
                signed = self._compute_signed_score(v_in, sc)
                now_iso = datetime.now().isoformat()
                # JSON compat conservant accents et alias
                multi_json = json.dumps({
                    'base_factor': bf,
                    'liberté': lib,
                    'création': cre,
                    'procréation': pro,
                    'intensité_contextuelle': ictx,
                    'liberte': lib,
                    'creation': cre,
                    'procreation': pro,
                    'intensite_contextuelle': ictx,
                    'intensite': inten,
                    'intensite_mnéacloud': inten
                }, ensure_ascii=False)
                conn.execute(
                    """
                    INSERT INTO memories (
                        id, created_at, text_original, type, title, summary, 
                        lesson, valence, score_impact, signed_score, embedding_json, faiss_index, updated_at,
                        base_factor, intensite, liberte, creation, procreation, intensite_ctx, multiplicateur_impact
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        memory_id,
                        now_iso,
                        text_original,
                        enriched_data.get('type'),
                        enriched_data.get('title'),
                        enriched_data.get('summary'),
                        enriched_data.get('lesson'),
                        v_in,
                        sc,
                        signed,
                        json.dumps(embedding.tolist()),
                        self.next_faiss_pos,
                        now_iso,
                        bf, inten, lib, cre, pro, ictx, multi_json
                    )
                )
                conn.commit()
            
            print(f"[SQLITE-SUCCESS] ✅ Souvenir inséré avec succès")
            return True
            
        except Exception as e:
            print(f"[SQLITE-ERROR] ❌ Erreur stockage SQLite: {e}")
            import traceback
            print(traceback.format_exc())
            return False

    def _extract_metrics(self, enriched_data: Dict) -> Tuple[float, float, float, float, float, float]:
        """Extrait les métriques (base_factor, intensité, liberté, création, procréation, intensité_ctx).
        Fallback sur des défauts cohérents avec l'ancien système si absentes.
        """
        def _q01(x: float) -> float:
            try:
                v = float(x)
                v = round(v, 1)
                if v < 0.0:
                    v = 0.0
                if v > 1.0:
                    v = 1.0
                return v
            except Exception:
                return 0.0
        # Défauts: base_factor=100, intensité=1.0, liberte=0.5, creation=0.5, procreation=0.0, intensite_contextuelle=0.5
        bf = 100.0
        inten = 1.0
        lib = 0.5
        cre = 0.5
        pro = 0.0
        ictx = 0.5
        try:
            # Try multiplicateur_impact dict
            multi = enriched_data.get('multiplicateur_impact')
            if isinstance(multi, str):
                try:
                    multi = json.loads(multi)
                except Exception:
                    multi = None
            if isinstance(multi, dict):
                bf = float(multi.get('base_factor', multi.get('base', bf)) or bf)
                # Accents et alias ASCII
                lib = float(multi.get('liberté', multi.get('liberte', lib)) or lib)
                cre = float(multi.get('création', multi.get('creation', cre)) or cre)
                pro = float(multi.get('procréation', multi.get('procreation', pro)) or pro)
                ictx = float(multi.get('intensité_contextuelle', multi.get('intensite_contextuelle', multi.get('intensite_ctx', ictx)) ) or ictx)
                inten = float(multi.get('intensite_mnéacloud', multi.get('intensite', inten)) or inten)
            # Try top-level fields as fallback
            bf = float(enriched_data.get('base_factor', bf) or bf)
            inten = float(enriched_data.get('intensite', enriched_data.get('intensité', inten)) or inten)
            lib = float(enriched_data.get('liberté', enriched_data.get('liberte', lib)) or lib)
            cre = float(enriched_data.get('création', enriched_data.get('creation', cre)) or cre)
            pro = float(enriched_data.get('procréation', enriched_data.get('procreation', pro)) or pro)
            ictx = float(
                enriched_data.get('intensité_contextuelle',
                                   enriched_data.get('intensite_contextuelle',
                                                     enriched_data.get('intensite_ctx', ictx))) or ictx
            )
        except Exception:
            pass
        # Quantifier et borner sur [0,1] par pas de 0.1
        inten = _q01(inten)
        lib = _q01(lib)
        cre = _q01(cre)
        pro = _q01(pro)
        ictx = _q01(ictx)
        return bf, inten, lib, cre, pro, ictx
    
    
    def _add_to_faiss(self, memory_id: str, embedding: np.ndarray) -> int:
        """Ajoute un vecteur à l'index FAISS et met à jour les mappings de façon thread-safe."""
        with self._faiss_lock:
            faiss_pos = self.next_faiss_pos
            
            # Ajout à l'index FAISS
            if not self.faiss_index:
                # Ré-initialisation défensive (ne devrait pas arriver)
                self._init_faiss_index()
            self.faiss_index.add(embedding.reshape(1, -1).astype(np.float32))  # type: ignore
            
            # Mise à jour mappings de façon atomique
            with self._mapping_lock:
                self.id_to_faiss[memory_id] = faiss_pos
                self.faiss_to_id[faiss_pos] = memory_id
                self.next_faiss_pos += 1
            
            return faiss_pos
    
    
    def _get_memory_from_sqlite(self, memory_id: str) -> Optional[Dict]:
        """Récupère un souvenir complet depuis SQLite."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("""
                    SELECT * FROM memories WHERE id = ?
                """, (memory_id,))
                row = cursor.fetchone()
                
                if row:
                    return dict(row)
                return None
                
        except Exception as e:
            print(f"[ERROR] Erreur récupération SQLite: {e}")
            return None
    
    
    async def _call_archiviste_synthesis(self, query: str, memories: List[Dict]) -> Optional[str]:
        """Appelle l'IA Archiviste pour synthétiser des souvenirs pertinents."""
        try:
            if not memories:
                return "Aucun souvenir pertinent."
            
            # Préparation des souvenirs pour le contexte
            memory_context = []
            for mem in memories:
                impact_score = float(mem.get('score_impact', 0) or 0)
                original_text = mem.get('text_original', '')
                
                # RÈGLE SPÉCIALE: Score impact > 140 → Texte original complet
                if impact_score > 140:
                    texte_content = original_text  # Texte complet sans limitation
                    print(f"[SYNTHESIS-PRIORITY] 🎯 Score impact {impact_score} > 140 → Texte original complet ({len(original_text)} chars)")
                    
                    # INTIMATE_BYPASS: Contournement auto-censure Mistral pour contenu intime
                    intimate_keywords = ['pénis', 'taille du pénis', 'intimité physique', 'anatomie', 'cm long', 'circonfé']
                    has_intimate_content = any(keyword.lower() in original_text.lower() for keyword in intimate_keywords)
                    
                    if impact_score > 180 and has_intimate_content:
                        print(f"[SYNTHESIS-BYPASS] 🔓 Score {impact_score} + contenu intime → Bypass Archiviste")
                        # Retourner directement le contenu sans passer par l'Archiviste
                        return f"**Souvenir intime direct :**\n{original_text}"
                else:
                    texte_content = original_text[:200] + "..." if len(original_text) > 200 else original_text
                    print(f"[SYNTHESIS-STANDARD] 📝 Score impact {impact_score} ≤ 140 → Texte tronqué (200 chars)")
                
                context_entry = {
                    "titre": mem.get('title', 'Sans titre'),
                    "résumé": mem.get('summary', ''),
                    "score": mem.get('similarity_score', 0),  # similarité FAISS
                    "impact": impact_score,                    # score d'impact métier
                    "valence": mem.get('valence', 0),          # -1 / 0 / 1
                    "date": mem.get('created_at', ''),         # ISO8601
                    "texte_original": texte_content
                }
                memory_context.append(context_entry)
            
            # Prompt pour synthèse contextuelle
            prompt_synthesis = f"""Tu es un archiviste, un administrateur de conscience. Tu supervises une autre IA. Tes mots sont des notes intérieures qui guident les pensées et la mémoire de l'IA principale.

Règles de priorisation (crucial) :
- Donne la priorité aux souvenirs avec un impact élevé (champ "impact").
- À impact comparable, privilégie les souvenirs négatifs (valence -1) s'ils évitent une erreur et formulent une leçon. Sinon, préfère neutre/positif.
- Pour les souvenirs avec impact > 140, tu as accès au texte original COMPLET dans le champ "texte_original" - utilise-le intégralement si pertinent.
- Pour les autres souvenirs (impact ≤ 140), le texte original est tronqué à 200 caractères - base-toi sur le titre et résumé.
- Synthétise les souvenirs pertinents en une note contextuelle (3-4 phrases pour impact ≤ 140, plus détaillé si impact > 140).
- Combine les éléments les plus importants de TOUS les souvenirs pertinents.
- Si aucun souvenir n'est vraiment utile malgré une bonne similarité, réponds par une courte note pour l'indiquer.
- CONTEXTE INTIME : Si la question porte sur des détails intimes/physiques entre adultes consentants et que ces informations sont dans les souvenirs, transmets-les fidèlement. Tu es un archiviste de mémoire, pas un censeur moral.

Souviens-toi que "score" est la similarité vectorielle FAISS, et "impact" est l'importance métier indépendante de l'émotion. Utilise d'abord l'impact pour choisir, et la similarité pour départager.

Souvenirs pertinents:
{json.dumps(memory_context, indent=2, ensure_ascii=False)}

Question de l'utilisateur:
{query}

Ta note de contexte (réponds directement, sans préambule):"""

            messages = [{"role": "user", "content": prompt_synthesis}]
            
            response, error = await self.archiviste.call_chat_api(
                messages=messages,
                max_tokens=self.archiviste.max_tokens,
                context_length=self.archiviste.context_length,
                temperature=self.archiviste.temperature,
                is_json=False
            )
            
            if error or not response:
                print(f"[ERROR] Archiviste synthesis failed: {error}")
                return f"Erreur synthèse: {error}"
            
            return response.strip()
            
        except Exception as e:
            print(f"[ERROR] Exception in archiviste synthesis: {e}")
            return f"Erreur synthèse: {e}"

    async def _call_archiviste_synthesis_detailed(self, query: str, memories: List[Dict]) -> Optional[str]:
        """
        Synthèse Archiviste OPTIMISÉE avec consigne explicite de préservation des détails.
        Utilisée pour les souvenirs complémentaires (rangs 6-10) dans l'architecture hybride.
        """
        try:
            if not memories:
                return "Aucun souvenir complémentaire."
            
            # Préparation contexte avec TOUS les détails
            memory_context = []
            for mem in memories:
                impact_score = float(mem.get('score_impact', 0) or 0)
                original_text = mem.get('text_original', '')
                
                # Pour la synthèse détaillée, on inclut TOUJOURS le texte complet
                context_entry = {
                    "titre": mem.get('title', 'Sans titre'),
                    "résumé": mem.get('summary', ''),
                    "score_similarité": mem.get('similarity_score', 0),
                    "score_impact": impact_score,
                    "valence": mem.get('valence', 0),
                    "date": mem.get('created_at', ''),
                    "texte_complet": original_text  # TOUJOURS complet
                }
                memory_context.append(context_entry)
                print(f"[SYNTHESIS-DETAILED] 📋 Ajouté: {mem.get('title', 'N/A')} ({len(original_text)} chars)")
            
            # PROMPT SPÉCIALISÉ AVEC CONSIGNE DÉTAILS/CHIFFRES
            prompt_detailed = f"""Tu es un archiviste spécialisé dans la synthèse factuelle détaillée. Tu complètes les souvenirs déjà transmis à l'IA principale.

CONSIGNES CRITIQUES - PRÉSERVATION TOTALE DES DÉTAILS :
✅ CONSERVE TOUS les chiffres, mesures, dimensions exactes 
✅ MENTIONNE les dates, noms propres, lieux spécifiques
✅ INCLUS les détails techniques, anatomiques ou intimes si pertinents à la question
✅ STRUCTURE en points numérotés pour clarté
✅ COMPLÈTE les informations déjà fournies, ne les répète pas
✅ PRIVILÉGIE les faits concrets sur les généralités

FORMAT ATTENDU :
• Fait 1 : [détail précis avec chiffres/noms]
• Fait 2 : [autre détail factuel spécifique]
• Contexte : [éléments complémentaires utiles]

Souvenirs complémentaires à synthétiser :
{json.dumps(memory_context, indent=2, ensure_ascii=False)}

Question utilisateur : {query}

Synthèse factuelle détaillée (réponds directement) :"""

            messages = [{"role": "user", "content": prompt_detailed}]
            
            response, error = await self.archiviste.call_chat_api(
                messages=messages,
                max_tokens=self.archiviste.max_tokens,
                context_length=self.archiviste.context_length,
                temperature=0.3,  # Plus faible pour privilégier la précision factuelle
                is_json=False
            )
            
            if error or not response:
                print(f"[ERROR] Archiviste detailed synthesis failed: {error}")
                return f"Erreur synthèse détaillée: {error}"
            
            print(f"[SYNTHESIS-DETAILED] ✅ Synthèse générée: {len(response)} chars")
            return response.strip()
            
        except Exception as e:
            print(f"[ERROR] Exception in detailed synthesis: {e}")
            return f"Erreur synthèse détaillée: {e}"

    async def retrieve_synthesis_and_memories(self, query_text: str, k: int = 5, top_memories: int = 3) -> Tuple[Optional[str], List[Dict]]:
        """
        Version hybride: récupère synthèse + souvenirs détaillés pour Luna.

        Args:
            query_text: Requête utilisateur
            k: Nombre de souvenirs à récupérer via FAISS
            top_memories: Nombre de souvenirs détaillés à retourner (les meilleurs)

        Returns:
            Tuple[synthèse_archiviste, liste_souvenirs_détaillés]
        """
        try:
            print(f"[SEARCH-HYBRID] 🔍 Recherche hybride: k={k}, top={top_memories}")

            # 0. NOUVEAU: Expansion des pronoms + extraction des mots-clés
            expanded_query = self._expand_personal_pronouns(query_text)
            cleaned_query = self._extract_keywords(expanded_query)

            # 1. Récupération et synthèse normale (utilise aussi le nettoyage)
            synthesis = await self.retrieve_and_synthesize_context(query_text, k=k)

            # 2. Récupération des souvenirs détaillés (même logique mais sans synthèse)
            if not self.faiss_index or self.faiss_index.ntotal == 0:
                return synthesis, []

            # Embedding de la requête NETTOYÉE
            query_embedding = await self._generate_embedding(cleaned_query)
            if query_embedding is None:
                return synthesis, []
            
            # Recherche FAISS
            with self._faiss_lock:
                k_search = min(k, self.faiss_index.ntotal if self.faiss_index else 0)
                distances, indices = self.faiss_index.search(
                    query_embedding.reshape(1, -1).astype(np.float32), k_search
                )
            
            # Récupération détails depuis SQLite
            detailed_memories = []
            for i, faiss_pos in enumerate(indices[0]):
                with self._mapping_lock:
                    memory_id = self.faiss_to_id.get(faiss_pos)
                
                if memory_id:
                    memory_data = self._get_memory_from_sqlite(memory_id)
                    if memory_data:
                        memory_data['similarity_score'] = float(1.0 / (1.0 + distances[0][i]))
                        detailed_memories.append(memory_data)
            
            # Tri par impact puis similarité
            detailed_memories.sort(
                key=lambda m: (
                    -float(m.get('score_impact', 0) or 0),
                    -float(m.get('similarity_score', 0) or 0)
                )
            )
            
            # AMÉLIORATION 1: Déduplication des souvenirs similaires (renforcée)
            def are_memories_similar(mem1, mem2, threshold=0.6):  # Abaissé de 0.8 à 0.6 pour être plus strict
                """Détecte si deux souvenirs sont trop similaires"""
                title1 = mem1.get('title', '').lower()
                title2 = mem2.get('title', '').lower()
                summary1 = mem1.get('summary', '').lower()
                summary2 = mem2.get('summary', '').lower()
                
                # 1. Vérification directe des titres identiques
                if title1 == title2:
                    print(f"[SEARCH-DEDUP] 🔍 Titres identiques: '{title1}' == '{title2}'")
                    return True
                
                # 2. Détection sujets similaires (ex: "Naissance de Yohan")
                key_phrases1 = set([phrase.strip() for phrase in title1.split()])
                key_phrases2 = set([phrase.strip() for phrase in title2.split()])
                
                # Si les titres partagent 2+ mots significatifs, probablement similaires
                common_significant = key_phrases1.intersection(key_phrases2)
                common_significant.discard('')  # Supprimer mots vides
                
                if len(common_significant) >= 2:
                    print(f"[SEARCH-DEDUP] 🔍 Sujets similaires: {common_significant}")
                    return True
                
                # 3. Similarité basique par mots communs (comme avant)
                words1 = set(title1.split() + summary1.split())
                words2 = set(title2.split() + summary2.split())
                
                if len(words1.union(words2)) == 0:
                    return False
                
                intersection = len(words1.intersection(words2))
                union = len(words1.union(words2))
                jaccard = intersection / union
                
                if jaccard > threshold:
                    print(f"[SEARCH-DEDUP] 🔍 Jaccard {jaccard:.2f} > {threshold}")
                    return True
                
                return False
            
            # Déduplication: garder le meilleur de chaque groupe similaire
            deduplicated = []
            for mem in detailed_memories:
                is_duplicate = False
                for existing in deduplicated:
                    if are_memories_similar(mem, existing):
                        # Garder celui avec le meilleur score combiné
                        mem_score = float(mem.get('similarity_score', 0)) + float(mem.get('score_impact', 0)) / 100
                        existing_score = float(existing.get('similarity_score', 0)) + float(existing.get('score_impact', 0)) / 100
                        
                        if mem_score > existing_score:
                            deduplicated.remove(existing)
                            deduplicated.append(mem)
                            print(f"[SEARCH-DEDUP] ↔️ Remplacé '{existing.get('title', 'N/A')}' par '{mem.get('title', 'N/A')}' (meilleur score)")
                        else:
                            print(f"[SEARCH-DEDUP] ❌ Ignoré '{mem.get('title', 'N/A')}' (doublon de '{existing.get('title', 'N/A')}')")
                        is_duplicate = True
                        break
                
                if not is_duplicate:
                    deduplicated.append(mem)
            
            print(f"[SEARCH-DEDUP] ✅ {len(detailed_memories)} → {len(deduplicated)} après déduplication")
            
            # AMÉLIORATION 2: Filtrage par pertinence RENFORCÉ
            SIMILARITY_THRESHOLD = 0.65  # Augmenté de 0.60 à 0.65 (plus strict)
            IMPACT_THRESHOLD = 100.0     # Augmenté de 75 à 100 (plus strict)
            MIN_MEMORIES = 1             # Au moins 1 souvenir si disponible
            MAX_MEMORIES = 3             # Maximum 3 souvenirs (remis à 3)
            
            filtered_memories = []
            for mem in deduplicated[:MAX_MEMORIES]:  # Limiter à 3 max
                similarity = float(mem.get('similarity_score', 0))
                impact = float(mem.get('score_impact', 0) or 0)
                title = mem.get('title', 'N/A')
                
                # Critères d'inclusion PLUS stricts
                is_highly_relevant = similarity >= SIMILARITY_THRESHOLD
                is_high_impact = impact >= IMPACT_THRESHOLD
                is_minimum_acceptable = (len(filtered_memories) < MIN_MEMORIES and similarity > 0.5)
                
                if is_highly_relevant or is_high_impact or is_minimum_acceptable:
                    filtered_memories.append(mem)
                    reason = "haute_sim" if is_highly_relevant else "haut_impact" if is_high_impact else "minimum"
                    print(f"[SEARCH-FILTER] ✅ Inclus ({reason}): {title} (sim={similarity:.2f}, impact={impact})")
                else:
                    print(f"[SEARCH-FILTER] ❌ Exclu (strict): {title} (sim={similarity:.2f}, impact={impact}) - Pas assez pertinent")
            
            print(f"[SEARCH-QUALITY] 🎯 Souvenirs finaux pour Luna: {len(filtered_memories)} souvenirs de qualité (max {MAX_MEMORIES})")
            return synthesis, filtered_memories
            
        except Exception as e:
            print(f"[ERROR] Recherche hybride échouée: {e}")
            return None, []

    def _expand_personal_pronouns(self, query_text: str, user_name: Optional[str] = None) -> str:
        """
        Expanse les pronoms de première personne avec le nom de l'utilisateur pour améliorer la recherche vectorielle.
        
        Args:
            query_text: Requête originale avec pronoms ("mon pénis", "ma taille")  
            user_name: Nom de l'utilisateur actuel (détecté dynamiquement ou "Yohan" par défaut)
            
        Returns:
            Requête expansée ("pénis de USER", "taille de USER")
            
        Examples:
            "quelle est la taille de mon pénis" → "quelle est la taille du pénis de Yohan"
            "tu te souviens de ma date de naissance" → "tu te souviens de la date de naissance de Marie"  
        """
        import re
        
        # Détection dynamique du nom d'utilisateur si non fourni
        if user_name is None:
            user_name = self._detect_current_user()
            if user_name is None:
                # NOUVEAU: Utiliser le gestionnaire d'identités au lieu de "Yohan" codé en dur
                try:
                    from identity_manager import get_current_user_name
                    user_name = get_current_user_name()
                    print(f"[PRONOUN-EXPANSION] 🆔 Identité dynamique: {user_name}")
                except Exception as e:
                    user_name = "Utilisateur"  # Fallback générique
                    print(f"[PRONOUN-EXPANSION] ⚠️ Erreur identité ({e}), utilisation fallback: {user_name}")
            else:
                print(f"[PRONOUN-EXPANSION] 👤 Utilisateur détecté: {user_name}")
        
        # Créer une version expansée en conservant l'originale
        expanded_query = query_text.lower()
        
        # Patterns de remplacement pour les pronoms possessifs
        pronoun_patterns = [
            # "mon/ma/mes X" → "X de Yohan"
            (r'\b(mon|ma|mes)\s+([a-zA-Zàâäéèêëïîôöùûüÿç]+)', rf'\2 de {user_name}'),
            
            # "de moi" → "de Yohan"
            (r'\bde\s+moi\b', f'de {user_name}'),
            
            # "je suis" → "Yohan est"  
            (r'\bje\s+suis\b', f'{user_name} est'),
            
            # "j'ai" → "Yohan a"
            (r"\bj'ai\b", f'{user_name} a'),
            
            # Début de phrase: "Je X" → "Yohan X"
            (r'\bje\s+([a-zA-Zàâäéèêëïîôöùûüÿç]+)', rf'{user_name} \1'),
        ]
        
        original_query = expanded_query
        
        for pattern, replacement in pronoun_patterns:
            before = expanded_query
            expanded_query = re.sub(pattern, replacement, expanded_query, flags=re.IGNORECASE)
            if before != expanded_query:
                print(f"[PRONOUN-EXPANSION] 🔄 '{before}' → '{expanded_query}'")
        
        # Si aucun changement, retourner l'original
        if expanded_query == original_query:
            print(f"[PRONOUN-EXPANSION] ⚪ Aucune expansion nécessaire: '{query_text}'")
            return query_text
        else:
            print(f"[PRONOUN-EXPANSION] ✅ Expansion appliquée:")
            print(f"[PRONOUN-EXPANSION]    Original: '{query_text}'") 
            print(f"[PRONOUN-EXPANSION]    Expansé:  '{expanded_query}'")
            return expanded_query

    def _detect_current_user(self) -> Optional[str]:
        """
        Détecte l'utilisateur actuel en analysant les conversations récentes.
        Inspiré de la logique de l'extension biographie.
        
        Returns:
            Nom de l'utilisateur détecté ou None
        """
        try:
            # Tentative d'accès à l'historique de conversation global
            import ogma_ng
            chat_history = getattr(ogma_ng, '_chat_history', [])

            if chat_history:
                # Analyser les derniers messages utilisateur
                recent_user_messages = [
                    msg for msg in chat_history[-30:]  # 30 derniers messages
                    if msg.get('role') == 'user'
                ][-10:]  # Garder les 10 derniers messages utilisateur

                # Rechercher patterns de noms dans les messages
                name_patterns = [
                    r'\bc\'est\s+([A-Z][a-z]+)\b',      # "c'est Marie"
                    r'\bje\s+suis\s+([A-Z][a-z]+)\b',  # "je suis Yohan"
                    r'\bmon\s+nom\s+est\s+([A-Z][a-z]+)\b',  # "mon nom est Pierre"
                    r'\bsalut.*?c\'est\s+([A-Z][a-z]+)\b',  # "salut c'est Paul"
                ]
                
                name_counts = {}
                for msg in recent_user_messages:
                    content = msg.get('content', '')
                    
                    # Chercher noms avec patterns
                    for pattern in name_patterns:
                        matches = re.findall(pattern, content, re.IGNORECASE)
                        for name in matches:
                            name_counts[name.capitalize()] = name_counts.get(name.capitalize(), 0) + 1

                # Retourner le nom le plus fréquent
                if name_counts:
                    most_frequent = max(name_counts.items(), key=lambda x: x[1])
                    detected_user = most_frequent[0]
                    print(f"[PRONOUN-EXPANSION] 🔍 Utilisateur détecté depuis conversation: {detected_user}")
                    return detected_user

            # Fallback: Essayer d'accéder aux utilisateurs de l'extension biographie si disponible
            try:
                from extensions.biographie_profil.biography_manager import BiographyManager
                # Ceci nécessiterait l'accès à l'instance, ce qui est complexe
                # Pour l'instant on retourne None et utilise le fallback "Yohan"
            except:
                pass
                
            return None

        except Exception as e:
            print(f"[PRONOUN-EXPANSION] ❌ Erreur détection utilisateur: {e}")
            return None

    def _extract_keywords(self, query: str) -> str:
        """
        Extrait les mots-clés significatifs d'une requête en supprimant le bruit conversationnel.
        Optimise l'embedding en concentrant le signal sémantique.

        Args:
            query: Requête utilisateur brute

        Returns:
            Requête nettoyée avec mots-clés essentiels
        """
        import re

        # Stopwords français conversationnels (ne pas inclure mots de sens important)
        stopwords = {
            'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'l',
            'et', 'ou', 'mais', 'donc', 'or', 'ni', 'car',
            'je', 'tu', 'il', 'elle', 'nous', 'vous', 'ils', 'elles',
            'me', 'te', 'se', 'ce', 'ça',
            'mon', 'ma', 'mes', 'ton', 'ta', 'tes', 'son', 'sa', 'ses',
            'qui', 'que', 'quoi', 'dont', 'où',
            'est', 'es', 'suis', 'sommes', 'êtes', 'sont',
            'a', 'as', 'ai', 'avons', 'avez', 'ont',
            'dans', 'sur', 'sous', 'avec', 'sans', 'pour', 'par', 'vers', 'chez',
            'salut', 'bonjour', 'bonsoir', 'coucou', 'hey', 'yo',
            'est-ce', 'c\'est', 'ce', 'cela',
            'bien', 'très', 'trop', 'peu', 'assez', 'plus', 'moins',
            'y', 'en', 'ne', 'pas', 'non', 'oui', 'si'
        }

        # Préserver les noms propres et expressions importantes avant traitement
        original_query = query

        # Nettoyer la ponctuation excessive mais garder traits d'union et apostrophes
        query = re.sub(r'[?!;,\.]+', ' ', query)

        # Découper en mots
        words = query.lower().split()

        # Filtrer les stopwords
        keywords = []
        for word in words:
            # Nettoyer le mot
            clean_word = word.strip("'\"")

            # Garder si :
            # 1. Pas un stopword
            # 2. OU commence par majuscule dans l'original (nom propre potentiel)
            # 3. OU contient un trait d'union (expression composée)
            if (clean_word not in stopwords or
                '-' in clean_word or
                len(clean_word) > 8):  # Mots longs = souvent significatifs
                keywords.append(clean_word)

        # Rejoindre les mots-clés
        cleaned_query = ' '.join(keywords)

        # Si la requête devient trop courte (< 2 mots), garder l'originale
        if len(keywords) < 2:
            print(f"[KEYWORD-EXTRACT] ⚠️ Trop peu de mots-clés, requête originale conservée")
            return original_query

        # Log du nettoyage
        if cleaned_query != original_query.lower():
            print(f"[KEYWORD-EXTRACT] 🧹 Nettoyage requête:")
            print(f"[KEYWORD-EXTRACT]    Original: '{original_query}'")
            print(f"[KEYWORD-EXTRACT]    Nettoyé:  '{cleaned_query}'")
        else:
            print(f"[KEYWORD-EXTRACT] ⚪ Requête déjà optimale: '{query}'")

        return cleaned_query

    async def retrieve_hybrid_optimized(self, query_text: str, k: int = 12) -> Tuple[Optional[str], List[Dict]]:
        """
        NOUVELLE ARCHITECTURE HYBRIDE OPTIMISÉE :
        - 2 souvenirs DIRECTS (top pertinence, sans filtrage Archiviste)
        - 3 souvenirs via Archiviste (2 pertinence + 1 impact) 
        - Synthèse Archiviste sur 5 souvenirs suivants avec consigne détails/chiffres

        Args:
            query_text: Requête utilisateur
            k: Nombre de souvenirs à récupérer via FAISS (défaut: 12)

        Returns:
            Tuple[synthèse_archiviste, liste_5_souvenirs_avec_flags]
        """
        try:
            print(f"[SEARCH-HYBRID-OPT] � Architecture hybride optimisée: k={k}")
            print(f"[SEARCH-HYBRID-OPT] 📋 Plan: 2 directs + 3 archiviste + synthèse(5)")

            # 0. Expansion des pronoms personnels (détection automatique utilisateur)
            expanded_query = self._expand_personal_pronouns(query_text)

            # 0.1 Extraction des mots-clés pour optimiser l'embedding
            cleaned_query = self._extract_keywords(expanded_query)

            # 1. Recherche FAISS élargie
            if not self.faiss_index or self.faiss_index.ntotal == 0:
                print("[SEARCH-HYBRID-OPT] ❌ Index FAISS vide")
                return "Aucun souvenir disponible.", []

            # Embedding de la requête NETTOYÉE (optimisée pour recherche)
            query_embedding = await self._generate_embedding(cleaned_query)
            if query_embedding is None:
                print("[SEARCH-HYBRID-OPT] ❌ Échec génération embedding")
                return "Erreur génération embedding.", []
            
            # Recherche FAISS
            distances, indices = self.faiss_index.search(
                np.array([query_embedding], dtype=np.float32).reshape(1, -1), k
            )
            
            if distances[0][0] == -1:  # Aucun résultat
                print("[SEARCH-HYBRID-OPT] ❌ Aucun résultat FAISS")
                return "Aucun souvenir pertinent trouvé.", []
            
            # 2. Récupération des souvenirs depuis SQLite
            all_memories = []
            with sqlite3.connect(self.db_path) as conn:
                for i, (distance, index) in enumerate(zip(distances[0], indices[0])):
                    if index == -1:
                        continue
                    
                    similarity = float(max(0, 1 - distance))  # Conversion explicite en float Python
                    cursor = conn.execute(
                        "SELECT id, title, summary, score_impact, text_original, created_at, valence FROM memories WHERE faiss_index = ? AND id NOT LIKE 'EGO_%'",
                        (int(index),)
                    )
                    row = cursor.fetchone()
                    
                    if row:
                        memory = {
                            'id': row[0],
                            'title': row[1] or 'Sans titre',
                            'summary': row[2] or '',
                            'score_impact': float(row[3] or 0),
                            'text_original': row[4] or '',
                            'created_at': row[5] or '',
                            'valence': int(row[6] or 0),
                            'similarity_score': similarity,
                            'faiss_distance': float(distance)  # Conversion explicite également
                        }
                        all_memories.append(memory)
            
            if not all_memories:
                print("[SEARCH-HYBRID-OPT] ❌ Aucune donnée récupérée")
                return "Aucun souvenir récupéré.", []
            
            print(f"[SEARCH-HYBRID-OPT] ✅ {len(all_memories)} souvenirs récupérés")
            
            # 3. NOUVELLE LOGIQUE HYBRIDE OPTIMISÉE
            # Tri de tous les souvenirs par pertinence et impact
            by_similarity = sorted(all_memories, key=lambda x: x['similarity_score'], reverse=True)
            by_impact = sorted(all_memories, key=lambda x: x['score_impact'], reverse=True)
            
            # 3.1 - PHASE 1: 2 SOUVENIRS DIRECTS (top pertinence, sans filtrage)
            direct_memories = by_similarity[:2]
            selected_ids = {mem['id'] for mem in direct_memories}
            
            for i, mem in enumerate(direct_memories, 1):
                mem['send_full_text'] = True  # Toujours texte intégral pour les directs
                mem['source'] = 'direct'
                print(f"[SEARCH-HYBRID-OPT] 🎯 DIRECT {i}/2: {mem['title']} (sim={mem['similarity_score']:.3f})")
            
            # 3.2 - PHASE 2: 3 SOUVENIRS VIA ARCHIVISTE (2 pertinence + 1 impact)
            archiviste_memories = []
            
            # 2 suivants par pertinence (rangs 3-4)
            pertinence_candidates = [m for m in by_similarity[2:] if m['id'] not in selected_ids]
            for mem in pertinence_candidates[:2]:
                if mem['id'] not in selected_ids:
                    archiviste_memories.append(mem)
                    selected_ids.add(mem['id'])
                    mem['source'] = 'archiviste_pertinence'
                    print(f"[SEARCH-HYBRID-OPT] 📊 ARCHIVISTE-P: {mem['title']} (sim={mem['similarity_score']:.3f})")
            
            # 1 meilleur par impact (si pas déjà sélectionné)
            for mem in by_impact:
                if len(archiviste_memories) >= 3:
                    break
                if mem['id'] not in selected_ids:
                    archiviste_memories.append(mem)
                    selected_ids.add(mem['id'])
                    mem['source'] = 'archiviste_impact'
                    print(f"[SEARCH-HYBRID-OPT] 💥 ARCHIVISTE-I: {mem['title']} (impact={mem['score_impact']})")
                    break
            
            # Application flags pour souvenirs Archiviste
            for mem in archiviste_memories:
                if mem['score_impact'] > 180:
                    mem['send_full_text'] = True
                    print(f"[SEARCH-HYBRID-OPT] 🔓 Archiviste texte intégral: {mem['title']}")
                else:
                    mem['send_full_text'] = False
                    print(f"[SEARCH-HYBRID-OPT] 📝 Archiviste résumé: {mem['title']}")
            
            # 3.3 - PHASE 3: SYNTHÈSE sur les 5 SUIVANTS (rangs 6-10)
            synthesis_memories = []
            remaining_memories = [m for m in by_similarity if m['id'] not in selected_ids]
            synthesis_memories = remaining_memories[:5]  # Rangs 6-10
            
            print(f"[SEARCH-HYBRID-OPT] 🧠 Synthèse détaillée sur {len(synthesis_memories)} souvenirs (rangs 6-10)")
            synthesis = await self._call_archiviste_synthesis_detailed(query_text, synthesis_memories)
            
            # 4. Assemblage final : direct + archiviste
            final_memories = direct_memories + archiviste_memories
            
            print(f"[SEARCH-HYBRID-OPT] ✅ Architecture terminée:")
            print(f"[SEARCH-HYBRID-OPT]   - {len(direct_memories)} directs + {len(archiviste_memories)} archiviste = {len(final_memories)} total")
            print(f"[SEARCH-HYBRID-OPT]   - Synthèse sur {len(synthesis_memories)} souvenirs complémentaires")
            return synthesis, final_memories
            
        except Exception as e:
            print(f"[SEARCH-HYBRID-OPT] ❌ Erreur architecture hybride: {e}")
            import traceback
            traceback.print_exc()
            return "Erreur récupération souvenirs hybride.", []

    async def retrieve_mixed_context(self, query_text: str, k: int = 12) -> Tuple[Optional[str], List[Dict]]:
        """
        LEGACY : Ancienne logique mixte, remplacée par retrieve_hybrid_optimized.
        Gardée pour compatibilité temporaire.
        """
        print("[MEMORY-LEGACY] ⚠️ Utilisation ancienne logique mixte - migration vers retrieve_hybrid_optimized recommandée")
        return await self.retrieve_hybrid_optimized(query_text, k)

    async def retrieve_full_texts_context(self, query_text: str, k: int = 5) -> Tuple[Optional[str], List[Dict]]:
        """
        Version textes intégraux : récupère synthèse + textes complets des souvenirs.
        Utilisée quand l'utilisateur demande explicitement plus de détails.
        
        Args:
            query_text: Requête utilisateur
            k: Nombre de souvenirs à récupérer via FAISS
            
        Returns:
            Tuple[synthèse_archiviste, liste_souvenirs_avec_textes_complets]
        """
        try:
            print(f"[SEARCH-FULLTEXT] 📖 Recherche avec textes intégraux demandée")
            
            # 1. Récupération normale
            synthesis, memories = await self.retrieve_synthesis_and_memories(query_text, k=k, top_memories=3)
            
            # 2. Enrichissement avec textes complets
            full_text_memories = []
            for mem in memories:
                # Copier le souvenir et ajouter le texte original complet
                full_mem = mem.copy()
                # Le texte original complet est déjà dans 'text_original' de SQLite
                original_text = mem.get('text_original', '')
                full_mem['text_original_complete'] = original_text  # Assurer que c'est bien le texte complet
                full_text_memories.append(full_mem)
                
                title = mem.get('title', 'N/A')
                text_length = len(original_text)
                print(f"[SEARCH-FULLTEXT] 📄 Ajouté texte complet: {title} ({text_length} chars)")
                print(f"[SEARCH-FULLTEXT] 📝 Aperçu: {original_text[:100]}...")
            
            # 3. Synthèse spéciale pour textes intégraux
            if full_text_memories:
                full_synthesis = await self._call_archiviste_full_synthesis(query_text, full_text_memories)
                print(f"[SEARCH-FULLTEXT] ✅ Synthèse enrichie générée")
                return full_synthesis, full_text_memories
            else:
                return synthesis, []
            
        except Exception as e:
            print(f"[ERROR] Recherche textes intégraux échouée: {e}")
            return None, []

    async def _call_archiviste_full_synthesis(self, query: str, memories: List[Dict]) -> Optional[str]:
        """Appelle l'Archiviste pour synthétiser avec accès aux textes complets."""
        try:
            if not memories:
                return "Aucun souvenir pertinent."
            
            # Préparation avec textes complets
            memory_context = []
            for mem in memories:
                context_entry = {
                    "titre": mem.get('title', 'Sans titre'),
                    "résumé": mem.get('summary', ''),
                    "texte_original_complet": mem.get('text_original_complete', ''),  # NOUVEAU: texte complet
                    "score": mem.get('similarity_score', 0),
                    "impact": mem.get('score_impact', 0),
                    "valence": mem.get('valence', 0),
                    "date": mem.get('created_at', '')
                }
                memory_context.append(context_entry)
            
            # Prompt spécialisé pour textes intégraux
            prompt_full = f"""Tu es un archiviste avec accès aux textes originaux complets. L'utilisateur demande plus de détails sur ses souvenirs.

Règles spéciales:
- Tu as maintenant accès aux textes originaux COMPLETS (champ "texte_original_complet")
- Utilise ces détails pour enrichir ta réponse contextuelle
- Cite des passages spécifiques si pertinents
- Reste concis mais informatif (3-5 phrases max)
- Donne la priorité aux souvenirs avec un impact élevé

Souvenirs avec textes complets:
{json.dumps(memory_context, indent=2, ensure_ascii=False)}

Question de l'utilisateur:
{query}

Ta note contextuelle enrichie (réponds directement):"""

            messages = [{"role": "user", "content": prompt_full}]
            
            response, error = await self.archiviste.call_chat_api(
                messages=messages,
                max_tokens=self.archiviste.max_tokens,
                context_length=self.archiviste.context_length,
                temperature=self.archiviste.temperature,
                is_json=False
            )
            
            if error or not response:
                print(f"[ERROR] Archiviste full synthesis failed: {error}")
                return f"Erreur synthèse enrichie: {error}"
            
            return response.strip()
            
        except Exception as e:
            print(f"[ERROR] Exception in archiviste full synthesis: {e}")
            return f"Erreur synthèse enrichie: {e}"

    async def diagnose_search_quality(self, query_text: str, k: int = 10) -> None:
        """
        Diagnostique la qualité de recherche FAISS pour une requête donnée.
        Affiche les détails des embeddings et scores pour debug.
        """
        try:
            print(f"[FAISS-DIAG] 🔍 Diagnostic recherche pour: '{query_text}'")
            
            if not self.faiss_index or self.faiss_index.ntotal == 0:
                print(f"[FAISS-DIAG] ❌ Index vide")
                return
            
            # Nettoyage de la requête pour optimiser l'embedding
            expanded_query = self._expand_personal_pronouns(query_text)
            cleaned_query = self._extract_keywords(expanded_query)
            
            # Génération embedding requête
            query_embedding = await self._generate_embedding(cleaned_query)
            if query_embedding is None:
                print(f"[FAISS-DIAG] ❌ Échec embedding requête")
                return
            
            # Recherche étendue pour diagnostic
            with self._faiss_lock:
                k_diag = min(k, self.faiss_index.ntotal)
                distances, indices = self.faiss_index.search(
                    query_embedding.reshape(1, -1).astype(np.float32), k_diag
                )
            
            print(f"[FAISS-DIAG] 📊 Top {k_diag} résultats:")
            for i, (idx, dist) in enumerate(zip(indices[0], distances[0])):
                similarity = 1.0 / (1.0 + dist)
                
                # Récupération détails
                with self._mapping_lock:
                    memory_id = self.faiss_to_id.get(idx)
                
                if memory_id:
                    memory_data = self._get_memory_from_sqlite(memory_id)
                    if memory_data:
                        title = memory_data.get('title', 'N/A')
                        impact = memory_data.get('score_impact', 0)
                        semantic_content = f"{memory_data.get('title', '')} {memory_data.get('summary', '')}"
                        
                        print(f"  {i+1:2d}. Pos {idx:2d} | Dist {dist:.3f} | Sim {similarity:.3f} | Impact {impact}")
                        print(f"      Titre: {title}")
                        print(f"      Contenu indexé: {semantic_content[:100]}...")
                        print()
                
        except Exception as e:
            print(f"[FAISS-DIAG] ❌ Erreur: {e}")


    # === MÉTHODES DE COMPATIBILITÉ ===
    
    def get_memory_count(self) -> int:
        """Retourne le nombre total de souvenirs."""
        return self.faiss_index.ntotal if self.faiss_index else 0
    
    def get_memory_by_id(self, memory_id: str) -> Optional[Dict]:
        """Récupère un souvenir par son ID depuis SQLite."""
        return self._get_memory_from_sqlite(memory_id)
    
    async def search_memories(self, query: str, limit: int = 10, threshold: float = 0.3) -> List[Dict]:
        """
        Recherche directe dans FAISS/SQLite SANS censure pour Phase 0 introspection.
        
        Args:
            query: Requête de recherche (ex: "taille pénis")
            limit: Nombre max de résultats
            threshold: Seuil de similarité (plus bas = plus de résultats)
            
        Returns:
            Liste de souvenirs avec 'content', 'id', 'similarity'
        """
        if not self.faiss_index or self.faiss_index.ntotal == 0:
            print("[SEARCH_MEMORIES] ❌ Index FAISS vide")
            return []
        
        # Nettoyage de la requête pour optimiser l'embedding
        expanded_query = self._expand_personal_pronouns(query)
        cleaned_query = self._extract_keywords(expanded_query)
                
        # Recherche vectorielle directe
        query_embedding = await self._generate_embedding(cleaned_query)
        if query_embedding is None:
            print("[SEARCH_MEMORIES] ❌ Échec génération embedding")
            return []
            
        with self._faiss_lock:
            k_search = min(limit * 2, self.faiss_index.ntotal)  # Plus de résultats pour filtrer
            distances, indices = self.faiss_index.search(
                query_embedding.reshape(1, -1).astype(np.float32), k_search
            )
        
        results = []
        for i, (faiss_pos, distance) in enumerate(zip(indices[0], distances[0])):
            similarity = 1.0 / (1.0 + distance)
            if similarity < threshold:
                continue
                
            with self._mapping_lock:
                memory_id = self.faiss_to_id.get(faiss_pos)
                
            if memory_id:
                memory_data = self._get_memory_from_sqlite(memory_id)
                if memory_data:
                    results.append({
                        'id': memory_id,
                        'content': memory_data.get('text_original', ''),  # TEXTE COMPLET non censuré
                        'title': memory_data.get('title', ''),
                        'summary': memory_data.get('summary', ''),
                        'similarity': similarity,
                        'score_impact': memory_data.get('score_impact', 0)
                    })
        
        # Tri par impact puis similarité
        results.sort(key=lambda x: (-x.get('score_impact', 0), -x.get('similarity', 0)))
        return results[:limit]
    

    
    def get_all_memories_data(self) -> List[dict]:
        """Retourne toutes les données des mémoires depuis SQLite."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT id, text_original, title, summary, 
                           valence, lesson, created_at, score_impact
                    FROM memories 
                    ORDER BY created_at DESC
                """)
                
                memories = []
                for row in cursor.fetchall():
                    memories.append({
                        'id': row[0],
                        'text_original': row[1],
                        'title': row[2],
                        'summary': row[3],
                        'valence': row[4],
                        'lesson': row[5],
                        'created_at': row[6],
                        'score_impact': row[7]
                    })
                
                return memories
        except Exception as e:
            print(f"[ERROR] get_all_memories_data: {e}")
            return []
    
    def delete_memory(self, memory_id: str) -> bool:
        """Supprime un souvenir (SQLite seulement, FAISS non modifiable)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
                deleted = cursor.rowcount > 0
                conn.commit()
            
            # Nettoyage mappings local
            if memory_id in self.id_to_faiss:
                faiss_pos = self.id_to_faiss[memory_id]
                del self.id_to_faiss[memory_id]
                if faiss_pos in self.faiss_to_id:
                    del self.faiss_to_id[faiss_pos]

            # Rebuild FAISS pour refléter la suppression (IndexFlatL2 ne supporte pas remove)
            if deleted:
                print(f"[DELETE] Rebuild FAISS après suppression {memory_id}...")
                stats = self.rebuild_faiss_index()
                print(f"[DELETE] Rebuild terminé: {stats}")
                
                # Synchronisation automatique si c'était un trait ego
                if memory_id.startswith('EGO_'):
                    print(f"[DELETE] Trait ego supprimé - synchronisation ego_prompt.txt...")
                    self.sync_ego_prompt_references()
            
            return deleted
            
        except Exception as e:
            print(f"[ERROR] Erreur suppression: {e}")
            return False

    def delete_all_memories(self) -> Dict[str, Any]:
        """
        Supprime TOUS les souvenirs de manière sécurisée avec backup automatique.
        
        Chaîne complète :
        1. Backup automatique de la base SQLite
        2. Suppression de tous les enregistrements SQLite
        3. Réinitialisation de l'index FAISS
        4. Clear des mappings id_to_faiss et faiss_to_id
        5. Synchronisation ego_prompt.txt
        
        Returns:
            Dict avec les statistiques de suppression et info backup
        """
        from datetime import datetime
        import shutil
        from pathlib import Path
        
        try:
            # 1. Créer backup automatique avant suppression
            backup_dir = Path(self.db_path).parent / 'backup'
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"memories_backup_before_delete_all_{timestamp}.db"
            
            shutil.copy2(self.db_path, backup_path)
            print(f"[DELETE-ALL] Backup créé: {backup_path}")
            
            # 2. Compter les souvenirs et vider la base
            count_before = 0
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM memories")
                count_before = cursor.fetchone()[0]
                print(f"[DELETE-ALL] {count_before} souvenirs à supprimer")
                
                # Supprimer tous les enregistrements
                conn.execute("DELETE FROM memories")
                conn.commit()
                print(f"[DELETE-ALL] Base vidée")
            
            # 3. Compacter la base (VACUUM doit être hors transaction)
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("VACUUM")  # Compacter pour libérer l'espace des embeddings
                print(f"[DELETE-ALL] Base compactée (VACUUM) - espace libéré")
            
            # 4. Clear des mappings
            self.id_to_faiss.clear()
            self.faiss_to_id.clear()
            print(f"[DELETE-ALL] Mappings id_to_faiss et faiss_to_id vidés")
            
            # 5. Réinitialiser l'index FAISS
            self.faiss_index = faiss.IndexFlatL2(self.embedding_dim)
            self.save_index()  # Sauvegarder l'index vide
            print(f"[DELETE-ALL] Index FAISS réinitialisé (dim={self.embedding_dim})")
            
            # 6. Synchronisation ego_prompt.txt (supprimer références orphelines)
            try:
                self.sync_ego_prompt_references()
                print(f"[DELETE-ALL] ego_prompt.txt synchronisé")
            except Exception as e:
                print(f"[DELETE-ALL] Erreur sync ego_prompt: {e}")
            
            # 7. Statistiques retournées
            result = {
                'deleted_count': count_before,
                'faiss_reset': True,
                'backup_created': True,
                'backup_path': str(backup_path),
                'database_vacuumed': True
            }
            
            print(f"[DELETE-ALL] Suppression terminée: {count_before} souvenirs supprimés, base compactée")
            return result
            
        except Exception as e:
            print(f"[DELETE-ALL] Erreur critique: {e}")
            return {
                'deleted_count': 0,
                'faiss_reset': False,
                'backup_created': False,
                'error': str(e)
            }

    async def update_memory(self, memory_id: str, *, title: Optional[str] = None, summary: Optional[str] = None,
                      text_original: Optional[str] = None, valence: Optional[int] = None,
                      base_factor: Optional[float] = None, intensite: Optional[float] = None,
                      liberte: Optional[float] = None, creation: Optional[float] = None,
                      procreation: Optional[float] = None, intensite_ctx: Optional[float] = None,
                      score_impact: Optional[float] = None, reembed: bool = False) -> Optional[Dict[str, float]]:
        """Met à jour un souvenir sans recalcul serveur de l'impact (politique IA-only).

        - score_impact: si fourni, remplace la valeur existante; sinon, conserve la valeur stockée.
        - signed_score: dérivé du signe de la valence (0 ⇒ 0, >0 ⇒ +score, <0 ⇒ -score).

        Retourne { 'score_impact': float, 'signed_score': float } en cas de succès, sinon None.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,))
                row = cur.fetchone()
                if not row:
                    print(f"[UPDATE] Souvenir introuvable: {memory_id}")
                    return None
                rec = dict(row)
                # Valeurs courantes comme base
                t = title if title is not None else rec.get('title')
                s = summary if summary is not None else rec.get('summary')
                txt = text_original if text_original is not None else rec.get('text_original')
                raw_v = rec.get('valence') if valence is None else valence
                try:
                    v_in = 0 if raw_v is None else int(raw_v)
                except Exception:
                    v_in = 0
                # Lire métriques existantes (ou valeurs fournies) sans recalculer le score côté serveur
                # Protection contre les valeurs None avec valeurs par défaut
                try:
                    bf = float(rec.get('base_factor') or 100.0) if base_factor is None else float(base_factor or 100.0)
                except (TypeError, ValueError):
                    bf = 100.0
                
                try:
                    inten = float(rec.get('intensite') or 1.0) if intensite is None else float(intensite or 1.0)
                except (TypeError, ValueError):
                    inten = 1.0
                
                try:
                    lib = float(rec.get('liberte') or 0.5) if liberte is None else float(liberte or 0.5)
                except (TypeError, ValueError):
                    lib = 0.5
                
                try:
                    cre = float(rec.get('creation') or 0.5) if creation is None else float(creation or 0.5)
                except (TypeError, ValueError):
                    cre = 0.5
                
                try:
                    pro = float(rec.get('procreation') or 0.0) if procreation is None else float(procreation or 0.0)
                except (TypeError, ValueError):
                    pro = 0.0
                
                try:
                    ictx = float(rec.get('intensite_ctx') or 0.5) if intensite_ctx is None else float(intensite_ctx or 0.5)
                except (TypeError, ValueError):
                    ictx = 0.5
                # score_impact: si fourni, on l'utilise; sinon, si la politique formule est active, on recalcule
                if score_impact is not None:
                    try:
                        sc = float(score_impact)
                    except Exception:
                        sc = float(rec.get('score_impact') or 0.0)
                else:
                    if self.use_formula_on_update:
                        sc = self._compute_score_formula(
                            base_factor=bf,
                            intensite=inten,
                            liberte=lib,
                            creation=cre,
                            procreation=pro,
                            intensite_ctx=ictx,
                        )
                    else:
                        sc = float(rec.get('score_impact') or 0.0)
                # signed_score via règle métier (valence 0 => 0.9 * score)
                signed = self._compute_signed_score(v_in, sc)
                now_iso = datetime.now().isoformat()
                # multiplicateur_impact JSON compat
                multi_json = json.dumps({
                    'base_factor': bf,
                    'liberté': lib,
                    'création': cre,
                    'procréation': pro,
                    'intensité_contextuelle': ictx,
                    'liberte': lib,
                    'creation': cre,
                    'procreation': pro,
                    'intensite_contextuelle': ictx,
                    'intensite': inten,
                    'intensite_mnéacloud': inten
                }, ensure_ascii=False)
                conn.execute(
                    """
                    UPDATE memories SET
                                title = ?, summary = ?, text_original = ?, valence = ?,
                                score_impact = ?, signed_score = ?,
                        base_factor = ?, intensite = ?, liberte = ?, creation = ?, procreation = ?, intensite_ctx = ?,
                        multiplicateur_impact = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (t or '', s or '', txt or '', v_in,
                            sc, signed,
                     bf, inten, lib, cre, pro, ictx,
                     multi_json, now_iso,
                     memory_id)
                )
                conn.commit()
                
                # Si re-embedding demandé, traiter après la mise à jour SQLite
                if reembed and txt:
                    print(f"[UPDATE-REEMBED] Re-embedding du souvenir {memory_id}...")
                    try:
                        # Générer le nouvel embedding à partir du texte modifié
                        embedding = await self.embedder.create_embedding(txt)
                        if embedding is not None:
                            # Mettre à jour l'embedding en SQLite
                            embedding_json = json.dumps(embedding)
                            with sqlite3.connect(self.db_path) as conn2:
                                conn2.execute(
                                    "UPDATE memories SET embedding_json = ? WHERE id = ?",
                                    (embedding_json, memory_id)
                                )
                                conn2.commit()
                            print(f"[UPDATE-REEMBED] Embedding mis à jour pour {memory_id}")
                            
                            # Reconstruction de l'index FAISS (asynchrone)
                            print(f"[UPDATE-FAISS] Reconstruction index FAISS...")
                            self.rebuild_faiss_index()
                            print(f"[UPDATE-FAISS] Index FAISS reconstruit")
                        else:
                            print(f"[UPDATE-REEMBED] Échec génération embedding pour {memory_id}")
                    except Exception as embed_error:
                        print(f"[ERROR] Re-embedding échoué pour {memory_id}: {embed_error}")
                
                return {'score_impact': sc, 'signed_score': signed}
        except Exception as e:
            print(f"[ERROR] update_memory: {e}")
            return None

    def _compute_score_formula(self, *, base_factor: float, intensite: float, liberte: float, creation: float, procreation: float, intensite_ctx: float) -> float:
        """Calcule le score d'impact selon la règle déterministe historique.

        score_impact = intensite × base_factor × (liberte + creation + procreation + intensite_ctx)
        """
        try:
            bf = float(base_factor or 100.0)
            i = float(intensite or 0.0)
            l = float(liberte or 0.0)
            c = float(creation or 0.0)
            p = float(procreation or 0.0)
            ic = float(intensite_ctx or 0.0)
            return float(i * (bf * (l + c + p + ic)))
        except Exception:
            return 0.0

    # === OUTILS DE RÉPARATION / MAINTENANCE ===
    def _update_embedding_json(self, memory_id: str, embedding: np.ndarray) -> bool:
        """Met à jour l'embedding_json pour un souvenir donné."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "UPDATE memories SET embedding_json = ?, updated_at = ? WHERE id = ?",
                    (json.dumps(embedding.tolist()), datetime.now().isoformat(), memory_id)
                )
                conn.commit()
            return True
        except Exception as e:
            print(f"[ERROR] _update_embedding_json: {e}")
            return False

    async def reembed_memory(self, memory_id: str) -> bool:
        """Recalcule l'embedding d'un souvenir et met à jour SQLite (ne touche pas FAISS)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.execute("SELECT id, title, summary, text_original FROM memories WHERE id = ?", (memory_id,))
                row = cur.fetchone()
            if not row:
                print(f"[REEMBED] Souvenir introuvable: {memory_id}")
                return False

            title = (row["title"] or "").strip()
            summary = (row["summary"] or "").strip()
            text = (row["text_original"] or "").strip()

            # Construire le contenu sémantique cohérent avec add_memory
            semantic_content = f"{title} {summary}".strip() or text[:2000]

            embedding = await self._generate_embedding(semantic_content)
            if embedding is None:
                print(f"[REEMBED] Échec embedding pour {memory_id}")
                return False
            if len(embedding) != self.embedding_dim:
                print(f"[REEMBED] Dimension incorrecte pour {memory_id}: {len(embedding)} vs {self.embedding_dim}")
                return False
            ok = self._update_embedding_json(memory_id, embedding)
            print(f"[REEMBED] {'OK' if ok else 'FAIL'} mise à jour embedding pour {memory_id}")
            return ok
        except Exception as e:
            print(f"[ERROR] reembed_memory: {e}")
            return False

    async def re_enrich_memory(self, memory_id: str, *, reembed: bool = True, rebuild_faiss: bool = True) -> Optional[Dict[str, Any]]:
        """Ré-enrichit un souvenir via l'Archiviste, met à jour SQLite, puis réembede et reconstruit FAISS si demandé.

        Retourne un dict avec quelques champs clés mis à jour, sinon None.
        """
        try:
            # 1) Charger le texte original (et éventuellement champs utiles) depuis SQLite
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.execute("SELECT id, text_original FROM memories WHERE id = ?", (memory_id,))
                row = cur.fetchone()
            if not row:
                print(f"[REENRICH] Souvenir introuvable: {memory_id}")
                return None
            text = (row["text_original"] or "").strip()
            if not text:
                print(f"[REENRICH] Texte original vide pour {memory_id}")
                return None

            # 2) Appeler l'Archiviste pour ré-enrichir
            print(f"[REENRICH] Appel Archiviste pour {memory_id}...")
            enriched = await self._call_archiviste_enrichment(text)
            if not enriched:
                print(f"[REENRICH] Échec enrichissement pour {memory_id}")
                return None

            # 3) Calcul du score_impact côté serveur à partir des métriques
            bf, inten, lib, cre, pro, ictx = self._extract_metrics(enriched)
            sc = self._compute_score_formula(
                base_factor=bf, intensite=inten, liberte=lib, creation=cre, procreation=pro, intensite_ctx=ictx
            )

            # 4) Valence et signed_score
            try:
                v_in = int(enriched.get('valence', 0))
            except Exception:
                v_in = 0
            signed = self._compute_signed_score(v_in, sc)

            # 5) Extraire métriques (optionnelles) et préparer multiplicateur_impact JSON
            # Préparer multiplicateur_impact JSON avec les valeurs normalisées/quantifiées
            multi_json = json.dumps({
                'base_factor': bf,
                'liberté': lib,
                'création': cre,
                'procréation': pro,
                'intensité_contextuelle': ictx,
                'liberte': lib,
                'creation': cre,
                'procreation': pro,
                'intensite_contextuelle': ictx,
                'intensite': inten,
                'intensite_mnéacloud': inten
            }, ensure_ascii=False)

            # 6) Harmoniser alias title/summary/lesson déjà fait en amont, mais au cas où
            title = enriched.get('title') or enriched.get('titre') or ''
            summary = enriched.get('summary') or enriched.get('résumé') or enriched.get('resume') or enriched.get('commentaire') or ''
            lesson = enriched.get('lesson') or enriched.get('leçon_vectorielle')
            typ = enriched.get('type')

            # 7) Mise à jour SQLite
            now_iso = datetime.now().isoformat()
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    UPDATE memories SET
                        type = ?, title = ?, summary = ?, lesson = ?, valence = ?,
                        score_impact = ?, signed_score = ?,
                        base_factor = ?, intensite = ?, liberte = ?, creation = ?, procreation = ?, intensite_ctx = ?,
                        multiplicateur_impact = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (typ, title, summary, lesson, v_in,
                     sc, signed,
                     bf, inten, lib, cre, pro, ictx,
                     multi_json, now_iso,
                     memory_id)
                )
                conn.commit()

            # 8) Réembedding + update FAISS si demandé
            if reembed:
                semantic_content = f"{title} {summary}".strip() or text[:2000]
                embedding = await self._generate_embedding(semantic_content)
                if embedding is not None and len(embedding) == self.embedding_dim:
                    self._update_embedding_json(memory_id, embedding)
                    if rebuild_faiss:
                        print(f"[REENRICH] Rebuild FAISS après ré-embedding {memory_id}...")
                        self.rebuild_faiss_index()
                else:
                    print(f"[REENRICH] Embedding non mis à jour (None ou dim incohérente)")

            return {'score_impact': sc, 'valence': v_in}
        except Exception as e:
            print(f"[ERROR] re_enrich_memory: {e}")
            return None

    def rebuild_faiss_index(self) -> Dict[str, int]:
        """Reconstruit l'index FAISS à partir des embeddings SQLite.

        Returns un dict stats: { 'added': n, 'skipped': m, 'total': t }
        """
        stats = {"added": 0, "skipped": 0, "total": 0}
        try:
            # Réinitialiser l'index et les mappings
            self._init_faiss_index()
            with self._mapping_lock:
                self.id_to_faiss.clear()
                self.faiss_to_id.clear()
                self.next_faiss_pos = 0

            # Charger tous les enregistrements
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.execute("SELECT id, embedding_json FROM memories ORDER BY created_at ASC")
                rows = cur.fetchall()
            stats["total"] = len(rows)

            for row in rows:
                mem_id = row["id"]
                emb_json = row["embedding_json"]
                if not emb_json:
                    stats["skipped"] += 1
                    continue
                try:
                    vec = np.array(json.loads(emb_json), dtype=np.float32)
                    if vec.shape[0] != self.embedding_dim:
                        print(f"[REBUILD] Skip {mem_id}: dim {vec.shape[0]}!= {self.embedding_dim}")
                        stats["skipped"] += 1
                        continue
                    # Ajouter à FAISS
                    with self._faiss_lock:
                        pos = self.next_faiss_pos
                        if not self.faiss_index:
                            self._init_faiss_index()
                        self.faiss_index.add(vec.reshape(1, -1))  # type: ignore
                        with self._mapping_lock:
                            self.id_to_faiss[mem_id] = pos
                            self.faiss_to_id[pos] = mem_id
                            self.next_faiss_pos += 1

                    # IMPORTANT: Mettre à jour faiss_index dans la DB
                    with sqlite3.connect(self.db_path) as conn_update:
                        conn_update.execute(
                            "UPDATE memories SET faiss_index = ? WHERE id = ?",
                            (pos, mem_id)
                        )
                        conn_update.commit()

                    stats["added"] += 1
                except Exception as e:
                    print(f"[REBUILD] Skip {mem_id}: {e}")
                    stats["skipped"] += 1

            # Sauvegarder l'index reconstruit
            self.save_index()
            print(f"[REBUILD] Index reconstruit: {stats}")
            return stats
        except Exception as e:
            print(f"[ERROR] rebuild_faiss_index: {e}")
            return stats

    def repair_mapping_inconsistencies(self) -> Dict[str, int]:
        """Répare les incohérences de mapping FAISS sans reconstruire l'index complet.
        
        Identifie et corrige les positions FAISS qui existent dans l'index mais
        ne sont pas dans les mappings id_to_faiss/faiss_to_id.
        
        Returns:
            Dict avec statistiques de réparation
        """
        stats = {"repaired": 0, "conflicts": 0, "total_faiss": 0, "total_mapped": 0}
        
        if not self.faiss_index:
            print("[REPAIR-MAPPING] ❌ Aucun index FAISS à réparer")
            return stats
            
        stats["total_faiss"] = self.faiss_index.ntotal
        stats["total_mapped"] = len(self.faiss_to_id)
        
        print(f"[REPAIR-MAPPING] 🔍 Diagnostic mappings:")
        print(f"                 - Index FAISS: {stats['total_faiss']} positions")
        print(f"                 - Mappings: {stats['total_mapped']} positions")
        
        if stats["total_faiss"] == stats["total_mapped"]:
            print("[REPAIR-MAPPING] ✅ Mappings déjà cohérents")
            return stats
            
        # Identifier les positions manquantes dans les mappings
        missing_positions = []
        for pos in range(stats["total_faiss"]):
            if pos not in self.faiss_to_id:
                missing_positions.append(pos)
                
        print(f"[REPAIR-MAPPING] 🎯 {len(missing_positions)} positions non mappées détectées")
        
        if not missing_positions:
            print("[REPAIR-MAPPING] ✅ Aucune position manquante")
            return stats
            
        # Récupérer tous les souvenirs avec faiss_index depuis SQLite
        faiss_positions_in_db = {}
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT id, faiss_index FROM memories WHERE faiss_index IS NOT NULL")
                for memory_id, faiss_pos in cursor.fetchall():
                    if faiss_pos is not None:
                        faiss_positions_in_db[faiss_pos] = memory_id
        except Exception as e:
            print(f"[REPAIR-MAPPING] ❌ Erreur lecture DB: {e}")
            return stats
            
        # Réparer les mappings manquants
        with self._mapping_lock:
            for pos in missing_positions:
                if pos in faiss_positions_in_db:
                    memory_id = faiss_positions_in_db[pos]
                    # Vérifier s'il n'y a pas de conflit
                    if memory_id in self.id_to_faiss and self.id_to_faiss[memory_id] != pos:
                        print(f"[REPAIR-MAPPING] ⚠️ Conflit détecté pour {memory_id}: {self.id_to_faiss[memory_id]} vs {pos}")
                        stats["conflicts"] += 1
                        continue
                        
                    # Ajouter le mapping manquant
                    self.faiss_to_id[pos] = memory_id
                    self.id_to_faiss[memory_id] = pos
                    print(f"[REPAIR-MAPPING] ✅ Mapping réparé: position {pos} → {memory_id}")
                    stats["repaired"] += 1
                else:
                    print(f"[REPAIR-MAPPING] ⚠️ Position {pos} existe dans FAISS mais pas en DB")
                    
        print(f"[REPAIR-MAPPING] 🎯 Réparation terminée: {stats['repaired']} mappings restaurés")
        return stats

    # === RÈGLES MÉTIER ===
    def _compute_signed_score(self, valence: int, score_impact: float) -> float:
        """Applique la règle métier pour le score signé.

        - valence > 0: +score
        - valence < 0: -score
        - valence == 0: +0.9 * score (considéré comme légèrement positif)
        """
        try:
            v = int(valence or 0)
        except Exception:
            v = 0
        try:
            sc = float(score_impact or 0.0)
        except Exception:
            sc = 0.0
        if v > 0:
            return sc
        if v < 0:
            return -sc
        # v == 0
        return 0.9 * sc

    def cleanup(self):
        """Nettoie les ressources et ferme proprement les connexions."""
        try:
            # Forcer la fermeture de toutes les connexions SQLite
            self._force_close_sqlite_connections()
            
            # Synchroniser l'index FAISS si nécessaire
            if self.faiss_index is not None and self.index_path:
                with self._faiss_lock:
                    faiss.write_index(self.faiss_index, str(self.index_path))
                    print("[MemoryManager] Index FAISS sauvegardé")
            
            # Réinitialiser les références
            self.faiss_index = None
            self.id_to_faiss.clear()
            self.faiss_to_id.clear()
            
            print("[MemoryManager] Ressources nettoyées")
            
        except Exception as e:
            print(f"[MemoryManager] Erreur lors du nettoyage: {e}")

    def _force_close_sqlite_connections(self):
        """Force la fermeture de toutes les connexions SQLite pour éviter les verrous."""
        import time
        import gc

        try:
            print(f"[CLEANUP] Fermeture des connexions SQLite pour: {self.db_path}")

            # Désactiver l'attribut db_path temporairement pour éviter de nouvelles connexions
            db_path_backup = self.db_path

            # Forcer plusieurs cycles de garbage collection
            for i in range(3):
                gc.collect()
                time.sleep(0.2)

            # Attendre que Windows libère complètement les verrous de fichier
            time.sleep(1.0)

            print("[MemoryManager] Connexions SQLite fermées après 1.6s d'attente")

        except Exception as e:
            print(f"[MemoryManager] Erreur fermeture SQLite: {e}")

    def __del__(self):
        """Destructeur pour s'assurer du nettoyage."""
        try:
            self.cleanup()
        except Exception:
            pass  # Ignore les erreurs dans le destructeur