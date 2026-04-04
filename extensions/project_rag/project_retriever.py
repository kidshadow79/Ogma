"""
project_retriever.py
--------------------
Recherche sémantique dans les chunks du projet + semantic cache.
Économie ~30-50% des appels embeddings grâce au cache.
"""

import time
import numpy as np
from typing import List, Dict, Any, Optional, Tuple

from .project_manager import ProjectMemory


class SemanticCache:
    """
    Cache sémantique local : si une query est très similaire à une query récente,
    on réutilise les résultats sans refaire l'embedding + la recherche FAISS.
    """

    def __init__(self, ttl: int = 300, similarity_threshold: float = 0.92):
        """
        Args:
            ttl: Durée de vie du cache en secondes
            similarity_threshold: Seuil de similarité pour réutilisation
        """
        self.ttl = ttl
        self.similarity_threshold = similarity_threshold
        # Stockage : [(embedding, results, timestamp), ...]
        self._cache: List[Tuple[np.ndarray, List[Dict], float]] = []
        self._max_entries = 50  # Limite mémoire

    def lookup(self, query_embedding: List[float]) -> Optional[List[Dict[str, Any]]]:
        """
        Cherche une query similaire dans le cache.

        Returns:
            Résultats cachés si trouvé, None sinon
        """
        now = time.time()
        query_vec = np.array(query_embedding, dtype=np.float32)

        # Nettoyer les entrées expirées
        self._cache = [(emb, res, ts) for emb, res, ts in self._cache
                       if now - ts < self.ttl]

        # Chercher une correspondance
        for cached_emb, cached_results, ts in self._cache:
            similarity = self._cosine_similarity(query_vec, cached_emb)
            if similarity >= self.similarity_threshold:
                return cached_results

        return None

    def store(self, query_embedding: List[float], results: List[Dict[str, Any]]):
        """Stocke une query et ses résultats dans le cache."""
        vec = np.array(query_embedding, dtype=np.float32)
        self._cache.append((vec, results, time.time()))

        # Limite mémoire
        if len(self._cache) > self._max_entries:
            self._cache = self._cache[-self._max_entries:]

    def clear(self):
        """Vide le cache."""
        self._cache.clear()

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Cosine similarity entre deux vecteurs."""
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))


class ProjectRetriever:
    """
    Recherche intelligente dans la mémoire projet.
    Utilise FAISS via ProjectMemory + semantic cache.
    """

    def __init__(self, project_memory: ProjectMemory, embedder,
                 cache_ttl: int = 300, max_results: int = 3,
                 search_threshold: float = 0.3):
        """
        Args:
            project_memory: Instance ProjectMemory (SQLite + FAISS)
            embedder: Contrôleur d'embedding (embedding_controller)
            cache_ttl: TTL du cache en secondes
            max_results: Nombre max de chunks retournés
            search_threshold: Seuil de similarité minimum
        """
        self.memory = project_memory
        self.embedder = embedder
        self.max_results = max_results
        self.search_threshold = search_threshold
        self.cache = SemanticCache(ttl=cache_ttl)

        self._stats = {'queries': 0, 'cache_hits': 0, 'faiss_searches': 0}

    async def search(self, query: str, k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Recherche les chunks les plus pertinents pour une query.

        Args:
            query: Texte de la requête (message utilisateur)
            k: Nombre de résultats (défaut: self.max_results)

        Returns:
            Liste de chunks pertinents avec scores
        """
        if k is None:
            k = self.max_results

        self._stats['queries'] += 1

        # Générer l'embedding de la query
        try:
            query_embedding = await self.embedder.create_embedding(query)
            if not query_embedding:
                print("[PROJECT-RETRIEVER] Embedding vide pour la query")
                return []
        except Exception as e:
            print(f"[PROJECT-RETRIEVER] Erreur embedding: {e}")
            return []

        # Vérifier le cache sémantique
        cached = self.cache.lookup(query_embedding)
        if cached is not None:
            self._stats['cache_hits'] += 1
            print(f"[PROJECT-RETRIEVER] Cache hit (total: {self._stats['cache_hits']}/{self._stats['queries']})")
            return cached[:k]

        # Recherche FAISS
        self._stats['faiss_searches'] += 1
        results = self.memory.search_similar(
            query_embedding, k=k, threshold=self.search_threshold
        )

        # Stocker dans le cache
        if results:
            self.cache.store(query_embedding, results)

        print(f"[PROJECT-RETRIEVER] {len(results)} chunks trouvés (FAISS search #{self._stats['faiss_searches']})")
        return results

    def get_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du retriever."""
        cache_rate = 0
        if self._stats['queries'] > 0:
            cache_rate = round(self._stats['cache_hits'] / self._stats['queries'] * 100, 1)
        return {
            **self._stats,
            'cache_hit_rate': f"{cache_rate}%",
            'cache_entries': len(self.cache._cache),
        }

    def clear_cache(self):
        """Vide le cache sémantique."""
        self.cache.clear()
        print("[PROJECT-RETRIEVER] Cache vidé")
