"""
project_manager.py
------------------
Gestionnaire mémoire projet isolé : SQLite + FAISS séparés de la mémoire OGMA.
Gère le stockage et la recherche de chunks de documents.
"""

import sqlite3
import json
import numpy as np
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("[PROJECT-RAG] FAISS non disponible")


class ProjectMemory:
    """
    Mémoire projet isolée avec SQLite + FAISS.
    Chaque projet a sa propre DB et son propre index vectoriel.
    """

    def __init__(self, project_dir: Path, embedding_dim: int = 1536):
        """
        Args:
            project_dir: Dossier du projet (SQLite et FAISS sont placés dedans)
            embedding_dim: Dimension des vecteurs d'embedding
        """
        project_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = project_dir / "project_memory.db"
        self.faiss_path = project_dir / "project_faiss.index"
        self.embedding_dim = embedding_dim

        # Index FAISS et mappings
        self.faiss_index = None
        self.id_to_faiss: Dict[str, int] = {}   # chunk_id -> faiss_position
        self.faiss_to_id: Dict[int, str] = {}   # faiss_position -> chunk_id
        self.next_faiss_pos = 0

        # Thread-safety
        self._faiss_lock = threading.Lock()
        self._db_lock = threading.Lock()

        # Init
        self._init_database()
        self._init_faiss_index()
        self._load_existing_data()

        print(f"[PROJECT-MEMORY] Initialisé: {self.next_faiss_pos} chunks, dim={self.embedding_dim}")

    def _init_database(self):
        """Crée les tables SQLite si nécessaire."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS files (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    file_type TEXT,
                    file_size INTEGER,
                    chunk_count INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    id TEXT PRIMARY KEY,
                    file_id TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    text_small TEXT NOT NULL,
                    text_parent TEXT NOT NULL,
                    embedding_json TEXT,
                    faiss_position INTEGER,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_chunks_file_id ON chunks(file_id)
            """)
            conn.commit()

        print(f"[PROJECT-MEMORY] Base de données: {self.db_path}")

    def _init_faiss_index(self):
        """Initialise l'index FAISS CPU (IndexFlatL2)."""
        if not FAISS_AVAILABLE:
            print("[PROJECT-MEMORY] FAISS indisponible, recherche désactivée")
            return

        self.faiss_index = faiss.IndexFlatL2(self.embedding_dim)
        print(f"[PROJECT-MEMORY] Index FAISS initialisé (dim={self.embedding_dim})")

    def _load_existing_data(self):
        """Charge les embeddings existants dans FAISS au démarrage."""
        if not FAISS_AVAILABLE or self.faiss_index is None:
            return

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT id, embedding_json, faiss_position FROM chunks "
                    "WHERE embedding_json IS NOT NULL ORDER BY faiss_position"
                )
                rows = cursor.fetchall()

            if not rows:
                return

            # Auto-détection de la dimension réelle depuis le premier vecteur
            first_emb = json.loads(rows[0][1])
            actual_dim = len(first_emb)
            if actual_dim != self.embedding_dim:
                print(f"[PROJECT-MEMORY] Correction dimension au chargement: {self.embedding_dim} -> {actual_dim}")
                self.embedding_dim = actual_dim
                self.faiss_index = faiss.IndexFlatL2(actual_dim)

            vectors = []
            for chunk_id, emb_json, faiss_pos in rows:
                try:
                    emb = json.loads(emb_json)
                    vec = np.array(emb, dtype=np.float32)
                    if vec.shape[0] != self.embedding_dim:
                        continue
                    vectors.append(vec)
                    pos = len(vectors) - 1
                    self.id_to_faiss[chunk_id] = pos
                    self.faiss_to_id[pos] = chunk_id
                except Exception:
                    continue

            if vectors:
                matrix = np.vstack(vectors)
                with self._faiss_lock:
                    self.faiss_index.add(matrix)
                self.next_faiss_pos = len(vectors)
                print(f"[PROJECT-MEMORY] {len(vectors)} chunks chargés dans FAISS (dim={self.embedding_dim})")

        except Exception as e:
            print(f"[PROJECT-MEMORY] Erreur chargement données: {e}")

    # === CRUD Fichiers ===

    def add_file(self, file_id: str, filename: str, file_type: str,
                 file_size: int) -> bool:
        """Enregistre un fichier dans la table files."""
        try:
            with self._db_lock:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        "INSERT OR REPLACE INTO files (id, filename, file_type, file_size, chunk_count, created_at) "
                        "VALUES (?, ?, ?, ?, 0, ?)",
                        (file_id, filename, file_type, file_size, datetime.now().isoformat())
                    )
                    conn.commit()
            return True
        except Exception as e:
            print(f"[PROJECT-MEMORY] Erreur add_file: {e}")
            return False

    def remove_file(self, file_id: str) -> bool:
        """Supprime un fichier et tous ses chunks (DB + FAISS)."""
        try:
            # Récupérer les chunk IDs à supprimer de FAISS
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT id FROM chunks WHERE file_id = ?", (file_id,)
                )
                chunk_ids = [row[0] for row in cursor.fetchall()]

            # Supprimer de la DB (CASCADE supprime les chunks)
            with self._db_lock:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("PRAGMA foreign_keys = ON")
                    conn.execute("DELETE FROM chunks WHERE file_id = ?", (file_id,))
                    conn.execute("DELETE FROM files WHERE id = ?", (file_id,))
                    conn.commit()

            # Reconstruire FAISS sans les chunks supprimés
            if chunk_ids:
                self._rebuild_faiss_index()

            print(f"[PROJECT-MEMORY] Fichier {file_id} supprimé ({len(chunk_ids)} chunks)")
            return True

        except Exception as e:
            print(f"[PROJECT-MEMORY] Erreur remove_file: {e}")
            return False

    # === CRUD Chunks ===

    def add_chunks(self, file_id: str, chunks: List[Dict[str, Any]],
                   embeddings: List[List[float]]) -> int:
        """
        Ajoute des chunks avec leurs embeddings.

        Args:
            file_id: ID du fichier parent
            chunks: Liste de dicts avec 'text_small', 'text_parent', 'chunk_index'
            embeddings: Liste de vecteurs correspondants (pour text_small)

        Returns:
            Nombre de chunks ajoutés
        """
        if len(chunks) != len(embeddings):
            print(f"[PROJECT-MEMORY] Mismatch chunks/embeddings: {len(chunks)} vs {len(embeddings)}")
            return 0

        # Auto-détection de la dimension réelle depuis le premier embedding
        if embeddings and FAISS_AVAILABLE:
            actual_dim = len(embeddings[0])
            if actual_dim != self.embedding_dim:
                print(f"[PROJECT-MEMORY] Correction dimension: {self.embedding_dim} -> {actual_dim}")
                self.embedding_dim = actual_dim
                # Recréer l'index FAISS avec la bonne dimension
                # (sûr tant qu'il n'y a pas encore de données dans l'index)
                if self.next_faiss_pos == 0:
                    self.faiss_index = faiss.IndexFlatL2(actual_dim)
                    print(f"[PROJECT-MEMORY] Index FAISS recree (dim={actual_dim})")
                else:
                    print(f"[PROJECT-MEMORY] WARN: dim mismatch avec donnees existantes ({self.next_faiss_pos} vecteurs)")

        added = 0
        now = datetime.now().isoformat()

        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            chunk_id = f"{file_id}_chunk_{chunk.get('chunk_index', i)}"
            emb_json = json.dumps(emb)

            try:
                # Ajouter en DB
                with self._db_lock:
                    with sqlite3.connect(self.db_path) as conn:
                        conn.execute(
                            "INSERT OR REPLACE INTO chunks "
                            "(id, file_id, chunk_index, text_small, text_parent, "
                            "embedding_json, faiss_position, created_at) "
                            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                            (chunk_id, file_id, chunk.get('chunk_index', i),
                             chunk['text_small'], chunk['text_parent'],
                             emb_json, self.next_faiss_pos, now)
                        )
                        conn.commit()

                # Ajouter dans FAISS
                if FAISS_AVAILABLE and self.faiss_index is not None:
                    vec = np.array([emb], dtype=np.float32)
                    with self._faiss_lock:
                        self.faiss_index.add(vec)
                    self.id_to_faiss[chunk_id] = self.next_faiss_pos
                    self.faiss_to_id[self.next_faiss_pos] = chunk_id
                    self.next_faiss_pos += 1

                added += 1

            except Exception as e:
                import traceback
                print(f"[PROJECT-MEMORY] Erreur ajout chunk {chunk_id}: {type(e).__name__}: {e!r}")
                traceback.print_exc()

        # Mettre à jour le compteur de chunks du fichier
        try:
            with self._db_lock:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(
                        "UPDATE files SET chunk_count = ? WHERE id = ?",
                        (added, file_id)
                    )
                    conn.commit()
        except Exception:
            pass

        print(f"[PROJECT-MEMORY] {added}/{len(chunks)} chunks ajoutés pour {file_id}")
        return added

    # === Recherche ===

    def search_similar(self, query_embedding: List[float], k: int = 3,
                       threshold: float = 0.3) -> List[Dict[str, Any]]:
        """
        Recherche les chunks les plus similaires via FAISS.

        Args:
            query_embedding: Vecteur de la requête
            k: Nombre de résultats max
            threshold: Seuil de similarité minimum (0-1, converti depuis distance L2)

        Returns:
            Liste de dicts avec 'chunk_id', 'text_parent', 'text_small',
            'score', 'file_id', 'filename'
        """
        if not FAISS_AVAILABLE or self.faiss_index is None:
            return []

        if self.faiss_index.ntotal == 0:
            return []

        try:
            query_vec = np.array([query_embedding], dtype=np.float32)
            actual_k = min(k, self.faiss_index.ntotal)

            with self._faiss_lock:
                distances, indices = self.faiss_index.search(query_vec, actual_k)

            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx < 0:
                    continue

                chunk_id = self.faiss_to_id.get(int(idx))
                if not chunk_id:
                    continue

                # Convertir distance L2 en score similarité (0-1)
                # Plus la distance est petite, plus c'est similaire
                score = 1.0 / (1.0 + float(dist))

                if score < threshold:
                    continue

                # Récupérer les données du chunk
                chunk_data = self._get_chunk_data(chunk_id)
                if chunk_data:
                    chunk_data['score'] = round(score, 4)
                    results.append(chunk_data)

            return results

        except Exception as e:
            print(f"[PROJECT-MEMORY] Erreur recherche: {e}")
            return []

    def _get_chunk_data(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """Récupère les données complètes d'un chunk depuis SQLite."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT c.id, c.file_id, c.chunk_index, c.text_small, c.text_parent, "
                    "f.filename FROM chunks c "
                    "LEFT JOIN files f ON c.file_id = f.id "
                    "WHERE c.id = ?",
                    (chunk_id,)
                )
                row = cursor.fetchone()

            if not row:
                return None

            return {
                'chunk_id': row[0],
                'file_id': row[1],
                'chunk_index': row[2],
                'text_small': row[3],
                'text_parent': row[4],
                'filename': row[5] or 'inconnu',
            }
        except Exception as e:
            print(f"[PROJECT-MEMORY] Erreur lecture chunk {chunk_id}: {e}")
            return None

    # === Utilitaires ===

    def _rebuild_faiss_index(self):
        """Reconstruit l'index FAISS depuis la DB (après suppression)."""
        if not FAISS_AVAILABLE:
            return

        try:
            with self._faiss_lock:
                self.faiss_index = faiss.IndexFlatL2(self.embedding_dim)
                self.id_to_faiss.clear()
                self.faiss_to_id.clear()
                self.next_faiss_pos = 0

            # Recharger
            self._load_existing_data()
            print(f"[PROJECT-MEMORY] Index FAISS reconstruit ({self.next_faiss_pos} chunks)")

        except Exception as e:
            print(f"[PROJECT-MEMORY] Erreur reconstruction FAISS: {e}")

    def get_all_files(self) -> List[Dict[str, Any]]:
        """Retourne la liste de tous les fichiers indexés."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT id, filename, file_type, file_size, chunk_count, created_at "
                    "FROM files ORDER BY created_at DESC"
                )
                rows = cursor.fetchall()

            return [
                {
                    'id': r[0], 'filename': r[1], 'file_type': r[2],
                    'file_size': r[3], 'chunk_count': r[4], 'created_at': r[5]
                }
                for r in rows
            ]
        except Exception as e:
            print(f"[PROJECT-MEMORY] Erreur liste fichiers: {e}")
            return []

    def get_stats(self) -> Dict[str, int]:
        """Retourne les statistiques du projet."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                file_count = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
                chunk_count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
            return {
                'files': file_count,
                'chunks': chunk_count,
                'faiss_vectors': self.faiss_index.ntotal if self.faiss_index else 0,
            }
        except Exception:
            return {'files': 0, 'chunks': 0, 'faiss_vectors': 0}

    def clear_all(self):
        """Supprime toutes les données du projet (DB + FAISS)."""
        try:
            with self._db_lock:
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("DELETE FROM chunks")
                    conn.execute("DELETE FROM files")
                    conn.commit()

            if FAISS_AVAILABLE and self.faiss_index is not None:
                with self._faiss_lock:
                    self.faiss_index = faiss.IndexFlatL2(self.embedding_dim)
                    self.id_to_faiss.clear()
                    self.faiss_to_id.clear()
                    self.next_faiss_pos = 0

            print("[PROJECT-MEMORY] Toutes les données projet supprimées")
        except Exception as e:
            print(f"[PROJECT-MEMORY] Erreur clear_all: {e}")
