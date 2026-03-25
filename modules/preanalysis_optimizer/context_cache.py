"""
CONTEXT CACHE - Cache contextuel intelligent pour OGMA
=======================================================

Évite les analyses répétitives en cachant les résultats basés sur:
1. Hash du message utilisateur + contexte récent
2. Détection de similarité sémantique (optionnel)
3. TTL (Time-To-Live) avec expiration automatique

GAINS:
- Messages similaires: -700ms (cache hit = 0 appels API)
- Token savings: ~4000 tokens économisés par cache hit

Usage:
    cache = ContextCache()
    
    # Générer clé unique
    key = cache.generate_key(user_message, conversation_history)
    
    # Vérifier cache
    cached = cache.get(key)
    if cached:
        return cached  # Skip toutes les analyses!
    
    # Après analyses, stocker
    cache.set(key, result)
"""

import hashlib
import time
from typing import Optional, Dict, Any, List
from collections import OrderedDict


class ContextCache:
    """
    Cache LRU avec TTL pour contextes analysés.
    
    Features:
    - LRU eviction (max_size entries)
    - TTL expiration (max_age_seconds)
    - Clés basées sur hash message + contexte
    - Invalidation sélective ou totale
    """
    
    def __init__(self, max_size: int = 50, max_age_seconds: int = 300):
        """
        Initialise le cache.
        
        Args:
            max_size: Nombre max d'entrées (LRU eviction après)
            max_age_seconds: Durée de vie max en secondes (5 min par défaut)
        """
        self._cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._max_size = max_size
        self._max_age_seconds = max_age_seconds
        
        # Statistiques
        self._stats = {
            'hits': 0,
            'misses': 0,
            'evictions': 0,
            'expirations': 0
        }
        
        # Configuration similarité
        self._similarity_threshold = 0.85  # 85% similarité = cache hit
        self._use_similarity = False  # Désactivé par défaut (coûteux)
        
        print(f"[CONTEXT-CACHE] 📦 Cache initialisé (max={max_size}, TTL={max_age_seconds}s)")
    
    def generate_key(self, user_message: str, conversation_history: list = None) -> str:
        """
        Génère une clé unique basée sur le message et le contexte.
        
        La clé inclut:
        - Hash du message utilisateur
        - Hash des 3 derniers échanges (contexte court)
        - Hash de la longueur totale conversation (changement notable)
        
        Args:
            user_message: Message utilisateur actuel
            conversation_history: Historique conversation
            
        Returns:
            str: Clé de cache unique (24 caractères hex)
        """
        components = []
        
        # 1. Message utilisateur (normalisé)
        normalized_message = self._normalize_text(user_message)
        components.append(f"msg:{normalized_message}")
        
        # 2. Contexte récent (3 derniers messages)
        if conversation_history:
            recent = conversation_history[-3:] if len(conversation_history) > 3 else conversation_history
            for msg in recent:
                role = msg.get('role', 'unknown')
                content = self._normalize_text(msg.get('content', ''))[:100]
                components.append(f"{role}:{content}")
            
            # 3. Taille conversation (détecte gros changements)
            components.append(f"len:{len(conversation_history)}")
        
        # Générer hash
        combined = "|".join(components)
        return hashlib.sha256(combined.encode()).hexdigest()[:24]
    
    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Récupère une entrée du cache.
        
        Args:
            key: Clé générée par generate_key()
            
        Returns:
            dict ou None: Résultat caché ou None si miss/expiré
        """
        if key not in self._cache:
            self._stats['misses'] += 1
            return None
        
        entry = self._cache[key]
        
        # Vérifier expiration
        age = time.time() - entry['timestamp']
        if age > self._max_age_seconds:
            # Expiré, supprimer
            del self._cache[key]
            self._stats['expirations'] += 1
            self._stats['misses'] += 1
            return None
        
        # Hit! Déplacer en fin (LRU)
        self._cache.move_to_end(key)
        self._stats['hits'] += 1
        
        return entry['data']
    
    def set(self, key: str, data: Dict[str, Any]):
        """
        Stocke une entrée dans le cache.
        
        Args:
            key: Clé unique
            data: Données à cacher (dict contexte optimisé)
        """
        # Éviction LRU si plein
        while len(self._cache) >= self._max_size:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            self._stats['evictions'] += 1
        
        # Stocker avec timestamp
        self._cache[key] = {
            'data': data.copy(),  # Copie pour éviter mutations
            'timestamp': time.time()
        }
        
        # Déplacer en fin
        self._cache.move_to_end(key)
    
    def invalidate(self, key: str = None):
        """
        Invalide une entrée ou tout le cache.
        
        Args:
            key: Clé spécifique ou None pour tout invalider
        """
        if key is None:
            # Tout invalider
            count = len(self._cache)
            self._cache.clear()
            print(f"[CONTEXT-CACHE] 🗑️ Cache vidé ({count} entrées)")
        elif key in self._cache:
            del self._cache[key]
    
    def invalidate_older_than(self, max_age_seconds: int):
        """
        Invalide les entrées plus vieilles que max_age_seconds.
        
        Args:
            max_age_seconds: Âge max en secondes
        """
        current_time = time.time()
        keys_to_delete = []
        
        for key, entry in self._cache.items():
            if current_time - entry['timestamp'] > max_age_seconds:
                keys_to_delete.append(key)
        
        for key in keys_to_delete:
            del self._cache[key]
            self._stats['expirations'] += 1
        
        if keys_to_delete:
            print(f"[CONTEXT-CACHE] 🕐 {len(keys_to_delete)} entrées expirées supprimées")
    
    def get_similar(self, user_message: str, conversation_history: list = None) -> Optional[Dict[str, Any]]:
        """
        Cherche une entrée similaire dans le cache (fuzzy matching).
        
        Plus coûteux que get() exact, utilisé en fallback.
        
        Args:
            user_message: Message à comparer
            conversation_history: Contexte
            
        Returns:
            dict ou None: Résultat similaire ou None
        """
        if not self._use_similarity or len(self._cache) == 0:
            return None
        
        normalized_msg = self._normalize_text(user_message)
        best_match = None
        best_score = 0
        
        for key, entry in self._cache.items():
            # Vérifier expiration
            if time.time() - entry['timestamp'] > self._max_age_seconds:
                continue
            
            # Extraire message original du cache (stocké dans data)
            cached_msg = entry['data'].get('_original_message', '')
            if not cached_msg:
                continue
            
            # Calcul similarité simple (ratio mots communs)
            score = self._calculate_similarity(normalized_msg, cached_msg)
            
            if score > best_score and score >= self._similarity_threshold:
                best_score = score
                best_match = entry['data']
        
        if best_match:
            self._stats['hits'] += 1
            print(f"[CONTEXT-CACHE] 🎯 Similarité trouvée ({best_score:.0%})")
        
        return best_match
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retourne les statistiques du cache.
        
        Returns:
            dict: {hits, misses, hit_rate, size, evictions, expirations}
        """
        total = self._stats['hits'] + self._stats['misses']
        hit_rate = (self._stats['hits'] / total * 100) if total > 0 else 0
        
        return {
            **self._stats,
            'size': len(self._cache),
            'max_size': self._max_size,
            'hit_rate': round(hit_rate, 1),
            'ttl_seconds': self._max_age_seconds
        }
    
    def _normalize_text(self, text: str) -> str:
        """
        Normalise le texte pour hashing cohérent.
        
        - Lowercase
        - Strip whitespace
        - Supprime ponctuation excessive
        """
        if not text:
            return ""
        
        # Lowercase et strip
        normalized = text.lower().strip()
        
        # Réduire whitespace multiple
        import re
        normalized = re.sub(r'\s+', ' ', normalized)
        
        return normalized
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calcule un score de similarité simple entre deux textes.
        
        Utilise ratio de mots communs (Jaccard simplifié).
        
        Returns:
            float: Score 0.0 à 1.0
        """
        if not text1 or not text2:
            return 0.0
        
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1 & words2
        union = words1 | words2
        
        return len(intersection) / len(union)
    
    def set_similarity_mode(self, enabled: bool, threshold: float = 0.85):
        """
        Active/désactive le mode similarité.
        
        Args:
            enabled: True pour activer
            threshold: Seuil de similarité (0.0-1.0)
        """
        self._use_similarity = enabled
        self._similarity_threshold = threshold
        mode = "activé" if enabled else "désactivé"
        print(f"[CONTEXT-CACHE] 🔄 Mode similarité {mode} (seuil={threshold:.0%})")
    
    def cleanup_expired(self):
        """Nettoie les entrées expirées (appeler périodiquement)"""
        self.invalidate_older_than(self._max_age_seconds)


class ConversationAwareCache(ContextCache):
    """
    Extension du cache avec awareness conversation.
    
    Invalide automatiquement quand la conversation change significativement.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._conversation_id = None
        self._last_conversation_len = 0
    
    def set_conversation(self, conversation_id: str):
        """
        Définit la conversation active.
        Invalide le cache si changement de conversation.
        """
        if self._conversation_id != conversation_id:
            print(f"[CONTEXT-CACHE] 🔄 Changement conversation, invalidation cache")
            self.invalidate()
            self._conversation_id = conversation_id
            self._last_conversation_len = 0
    
    def check_conversation_growth(self, current_len: int):
        """
        Vérifie si la conversation a grandi significativement.
        Invalide les anciennes entrées si croissance > 5 messages.
        """
        growth = current_len - self._last_conversation_len
        
        if growth > 5:
            # Conversation a beaucoup évolué, invalider vieilles entrées
            self.invalidate_older_than(60)  # Garder seulement < 1 minute
            print(f"[CONTEXT-CACHE] 📈 Croissance conversation (+{growth}), nettoyage ancien cache")
        
        self._last_conversation_len = current_len
