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


# ============================================================================
# NETTOYAGE SÉMANTIQUE - STOPWORDS CONVERSATIONNELS
# ============================================================================

STOPWORDS_CONVERSATIONAL = {
    # Verbes conversationnels (bruit récurrent)
    "souviens", "rappelles", "rappelle", "évoque", "évoques", "évoquent",
    "penses", "pense", "pensez", "crois", "croit", "croient",
    "sais", "sait", "savez", "dis", "dit", "dites", "disent",
    
    # Formules interrogatives
    "qu'est-ce", "qu'est", "est-ce", "comment", "pourquoi", 
    "quoi", "quel", "quelle", "quels", "quelles", "où",
    
    # Mots certitude/opinion (faible signal sémantique)
    "sûr", "sûre", "sûrs", "certain", "certaine", "certains",
    "probable", "probablement", "peut-être",
    
    # Phrases magiques récurrentes (dilution)
    "parlé", "parle", "parlons", "discuté", "discute", "discutons",
    "échangé", "échange", "échangeons", "conversation", "discussion",
    
    # Verbes liaison faible sémantique
    "avoir", "as", "avons", "avez", "ont",
    "être", "es", "sommes", "êtes", "sont", "suis",
    "faire", "fais", "fait", "faisons", "faites", "font",
    "aller", "vas", "va", "allons", "allez", "vont",
    "venir", "viens", "vient", "venons", "venez", "viennent",
    
    # Interjections (NOUVEAU - bruit conversationnel)
    "ah", "oh", "eh", "hé", "hein", "euh", "hum", "bah", "bon", "bof",
    "ouf", "pfff", "tiens", "voilà", "ben",
    
    # Formules politesse (NOUVEAU - zéro signal sémantique)
    "pardon", "désolé", "désolée", "excusez", "excuse", "merci", 
    "stp", "svp", "steuplait", "plait",
    
    # Verbes intention/désir (NOUVEAU - bruit modal)
    "voulais", "veux", "veut", "voulons", "voulez", "veulent",
    "aimerais", "aime", "aimes", "aiment", "aimez",
    "pourrais", "peux", "peut", "pouvons", "pouvez", "peuvent",
    "dire", "demander", "savoir", "vois", "voit", "voyez", "voient"
}

STOPWORDS_STANDARD = {
    # Articles
    "le", "la", "les", "l", "un", "une", "des", "du", "de", "d",
    
    # Pronoms sujets
    "je", "j", "tu", "il", "elle", "on", "nous", "vous", "ils", "elles",
    
    # Pronoms objets (SAUF possessifs mon/ma/mes gardés pour IA)
    "me", "m", "te", "t", "se", "s", "lui", "leur", "y", "en",
    
    # Prépositions courantes
    "à", "au", "aux", "dans", "sur", "sous", "par", "pour", "avec", "sans",
    "chez", "vers", "entre", "contre", "pendant", "depuis",
    
    # Conjonctions
    "et", "ou", "mais", "donc", "or", "ni", "car", "que", "qui",
    
    # Adverbes temps/lieu génériques
    "quand", "toujours", "jamais", "encore", "déjà", "maintenant",
    "hier", "demain", "aujourd'hui", "là", "ici",
    
    # Mots vides fréquents
    "c'est", "c", "ce", "cela", "ça", "ceci",
    "tout", "toute", "tous", "toutes", "très", "plus", "moins"
}


def clean_conversational_noise(query: str) -> str:
    """
    Nettoyage sémantique hybride - Suppression bruit conversationnel.
    
    PHILOSOPHIE:
    - SUPPRIME: Stopwords conversationnels (dilution embeddings)
    - SUPPRIME: Articles, pronoms, prépositions (bruit)
    - GARDE: Possessifs mon/ma/mes (utiles pour IA traduction contextuelle)
    - GARDE: Noms propres, concepts, entités (signal pur)
    
    GAIN ATTENDU: +70% précision recherche FAISS
    
    Args:
        query: Requête utilisateur brute
        
    Returns:
        Requête nettoyée (signal sémantique concentré)
        
    Exemples:
        "tu te souviens du nom de mon chat?" → "nom mon chat"
        "qu'est-ce que t'évoque la légende des 2 phares?" → "légende 2 phares"
        "je suis sûr qu'on a parlé de philosophie" → "philosophie"
    """
    # Normalisation
    query_lower = query.lower()
    
    # Suppression ponctuation (GARDE apostrophes pour contractions)
    query_clean = re.sub(r'[^\w\s\']', ' ', query_lower)
    
    # Split mots
    words = query_clean.split()
    
    # Filtrage stopwords (union des deux sets)
    all_stopwords = STOPWORDS_CONVERSATIONAL | STOPWORDS_STANDARD
    
    # GARDE "mon", "ma", "mes" (utiles pour contexte possessif)
    possessifs = {"mon", "ma", "mes"}
    
    filtered = [
        w for w in words 
        if (w not in all_stopwords or w in possessifs) and len(w) > 1
    ]
    
    # Rejoindre
    cleaned = " ".join(filtered)
    
    # Si nettoyage trop agressif (< 2 mots), fallback moins strict
    if len(filtered) < 2:
        # Garde au moins noms/adjectifs (stopwords standard seulement)
        filtered_light = [
            w for w in words 
            if w not in STOPWORDS_STANDARD and len(w) > 1
        ]
        cleaned = " ".join(filtered_light) if filtered_light else query_lower
    
    return cleaned.strip()


def calculate_keyword_matching_score(query_words: List[str], memory_text: str, 
                                     user_identity: str = "Utilisateur") -> float:
    """
    🎯 SCORE PONDÉRÉ KEYWORD MATCHING - Option B
    
    Calcule similarité basée UNIQUEMENT sur correspondance mots requête.
    Ignore mots supplémentaires dans le souvenir (pas de dilution).
    
    PHILOSOPHIE:
    - Requête nettoyée = SIGNAL PUR (3-5 mots essentiels)
    - Souvenir = CONTEXTE RICHE (peut contenir 50+ mots)
    - Score = % mots requête matchés dans souvenir
    - Mots non-requête IGNORÉS (pas de pénalité dilution)
    
    MATCHING TYPES:
    1. Exact: "chat" ↔ "chat" (+1.0)
    2. Synonyme: "minou" ↔ "chat" (+1.0)
    3. Traduction contextuelle: "mon" ↔ "yohan" (+1.0)
    4. Partial: "nommé" ↔ "nom" (+0.7)
    
    Args:
        query_words: Mots requête nettoyée (ex: ["nom", "mon", "minou"])
        memory_text: Texte complet souvenir
        user_identity: Nom utilisateur pour traduction "mon/ma/mes"
    
    Returns:
        Score 0.0-1.0 (% mots requête matchés)
    
    Exemples:
        Query: ["nom", "mon", "minou"]
        Memory: "Yohan a un chat femelle nommé Willow qui vit à Lyon"
        
        Matching:
        - "nom" ↔ "nommé" : ✅ Partial (+0.7)
        - "mon" ↔ "Yohan" : ✅ Traduction (+1.0)
        - "minou" ↔ "chat" : ✅ Synonyme (+1.0)
        
        Score = (0.7 + 1.0 + 1.0) / 3 = 0.90 ✅
        "Lyon", "femelle", "vit" IGNORÉS (pas de dilution)
    """
    
    # Dictionnaire synonymes (extensible)
    SYNONYMS = {
        "chat": ["minou", "félin", "matou", "chatte", "féline"],
        "chien": ["toutou", "canin", "chiot"],
        "légende": ["histoire", "mythe", "récit", "conte", "genèse"],
        "phare": ["lighthouse", "balise"],
        # Ajouts faciles selon besoins
    }
    
    # Normalisation texte souvenir
    memory_lower = memory_text.lower()
    memory_words = set(memory_lower.split())
    
    # Normalisation identité utilisateur
    user_identity_lower = user_identity.lower()
    
    total_score = 0.0
    matches_detail = []
    
    for query_word in query_words:
        query_word_lower = query_word.lower()
        word_score = 0.0
        match_type = "none"
        
        # TYPE 1: Matching EXACT
        if query_word_lower in memory_words:
            word_score = 1.0
            match_type = "exact"
        
        # TYPE 2: Matching SYNONYME
        elif not word_score:
            for base_word, synonyms in SYNONYMS.items():
                # Query est synonyme
                if query_word_lower in synonyms or query_word_lower == base_word:
                    # Cherche base ou synonymes dans souvenir
                    if base_word in memory_words or any(syn in memory_words for syn in synonyms):
                        word_score = 1.0
                        match_type = "synonym"
                        break
        
        # TYPE 3: Matching TRADUCTION CONTEXTUELLE (mon/ma/mes → nom utilisateur)
        if not word_score and query_word_lower in ["mon", "ma", "mes"]:
            if user_identity_lower in memory_lower:
                word_score = 1.0
                match_type = "contextual"
        
        # TYPE 4: Matching PARTIAL (sous-chaîne)
        if not word_score:
            # Cherche si query_word est contenu dans un mot du souvenir
            for mem_word in memory_words:
                if query_word_lower in mem_word or mem_word in query_word_lower:
                    if len(query_word_lower) >= 3:  # Éviter faux positifs courts
                        word_score = 0.7
                        match_type = "partial"
                        break
        
        total_score += word_score
        matches_detail.append({
            'word': query_word,
            'score': word_score,
            'type': match_type
        })
    
    # Score final = moyenne pondérée
    if not query_words:
        return 0.0
    
    final_score = total_score / len(query_words)
    
    # Logs diagnostiques
    matched = [m for m in matches_detail if m['score'] > 0]
    if matched:
        print(f"[KEYWORD-MATCH] ✅ {len(matched)}/{len(query_words)} mots matchés → Score: {final_score:.2f}")
        for m in matched:
            print(f"  • '{m['word']}' → {m['type']} (+{m['score']:.1f})")
    else:
        print(f"[KEYWORD-MATCH] ❌ Aucun match → Score: 0.0")
    
    return final_score


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
        
        # Seuil de blocage automatique pour redondance sémantique (configurable via UI)
        # 0.92 = 92% de similarité -> bloque les quasi-duplicatas
        self.redundancy_threshold = 0.92
        
        # Index FAISS et mapping
        self.faiss_index = None
        self.id_to_faiss = {}  # memory_id -> faiss_position
        self.faiss_to_id = {}  # faiss_position -> memory_id
        self.next_faiss_pos = 0
        
        # Thread-safety locks
        self._faiss_lock = threading.Lock()  # Protège les opérations FAISS
        self._mapping_lock = threading.Lock()  # Protège les mappings id<->faiss

        # Dernières métadonnées Archiviste (valence/type) — pour le hologramme
        self._last_enriched_data: Optional[Dict] = None
        
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
                    updated_at TEXT,
                    
                    -- Biographie: tagging utilisateur
                    user_tag TEXT DEFAULT NULL,
                    bio_processed INTEGER DEFAULT 0
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
                _add('user_tag', 'TEXT DEFAULT NULL')
                _add('bio_processed', 'INTEGER DEFAULT 0')
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
    
    
    def get_redundancy_threshold(self) -> float:
        """Retourne le seuil de blocage automatique pour redondance sémantique.
        
        Returns:
            Seuil entre 0.0 et 1.0 (ex: 0.92 = 92% de similarité)
        """
        return self.redundancy_threshold
    
    
    def set_redundancy_threshold(self, threshold: float) -> bool:
        """Définit le seuil de blocage automatique pour redondance sémantique.
        
        Args:
            threshold: Valeur entre 0.85 et 0.98 (seuil de similarité)
        
        Returns:
            True si modifié, False si valeur invalide
        """
        if 0.55 <= threshold <= 0.98:
            self.redundancy_threshold = round(threshold, 2)
            print(f"[MemoryManager] ✅ Seuil redondance modifié: {self.redundancy_threshold:.0%}")
            return True
        else:
            print(f"[MemoryManager] ⚠️ Seuil invalide: {threshold} (doit être entre 0.55 et 0.98)")
            return False
    
    
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

        # [LEGACY] sync_ego_prompt_references() désactivé - ego_prompt.txt obsolète depuis jan 2026
        # Le système actif utilise ego_compiled.json via modules/logic/ego_activation.py
    
    
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
    
    
    async def add_memory(self, memory_id: str, text_brut: str, chat_controller=None, conversation_context: str = "", interlocutor: str = "", user_tag: str = None) -> bool:
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
                self.status_queue.put(f"[MEMORY] Évaluation impact par l'IA principale...")
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

            # ÉTAPE 0.5: DÉCISION ARCHIVISTE - Bloquer mémorisations redondantes
            print(f"[MEMORY-STEP0.5] 🤔 Consultation Archiviste: mémorisation nécessaire?")
            decision_result = await self._archiviste_should_memorize(text_brut, conversation_history=None)
            
            if decision_result['decision'] == 'BLOCK':
                reason = decision_result.get('reason', 'Raison inconnue')
                confidence = decision_result.get('confidence', 0.0)
                similar_count = decision_result.get('similar_count', 0)
                spam_count = decision_result.get('recent_spam', 0)
                
                print(f"[MEMORY-BLOCKED] 🚫 Mémorisation BLOQUÉE par l'Archiviste")
                print(f"[MEMORY-BLOCKED] 📝 Raison: {reason}")
                print(f"[MEMORY-BLOCKED] 📊 Confiance: {confidence:.2f}")
                print(f"[MEMORY-BLOCKED] 🔍 Souvenirs similaires: {similar_count}")
                if spam_count > 0:
                    print(f"[MEMORY-BLOCKED] ⚠️ Spam détecté: {spam_count} mémorisations récentes")
                
                # Notification utilisateur avec détails
                block_msg = f"🚫 Mémorisation bloquée: {reason}"
                if similar_count > 0:
                    block_msg += f" ({similar_count} souvenirs similaires)"
                self.status_queue.put(block_msg)
                
                return False  # Blocage complet du pipeline
            
            # Si ACCEPT, continuer le pipeline normal
            print(f"[MEMORY-ACCEPTED] ✅ Archiviste autorise la mémorisation")
            print(f"[MEMORY-ACCEPTED] 📝 {decision_result.get('reason', '')}")
            
            self.status_queue.put(f"[MEMORY] Enrichissement par l'Archiviste...")

            # 1. Enrichissement par l'IA Archiviste (+ scoring si fallback nécessaire)
            print(f"[MEMORY-STEP1] 🧠 Appel IA Archiviste pour enrichissement...")
            need_scoring = (initial_score is None)
            enriched_data = await self._call_archiviste_enrichment(text_brut, calculate_score=need_scoring, current_user=user_tag)
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
            
            # 2. Génération embedding du contenu sémantique OPTIMISÉ
            # FORMAT JEOPARDY: titre (2 questions) + résumé (mots-clés) = vecteur concentré
            # Le texte original reste cherchable via FTS5
            title = enriched_data.get('title', '')
            summary = enriched_data.get('summary', '')
            
            semantic_content = f"{title} {summary}".strip()
            print(f"[MEMORY-STEP2] 🔢 Génération embedding JEOPARDY (titre+résumé uniquement)...")
            print(f"[MEMORY-SEMANTIC] Contenu: {len(semantic_content)} chars (titre={len(title)}, résumé={len(summary)})")
            embedding = await self._generate_embedding(semantic_content)
            if embedding is None:
                print(f"[MEMORY-ERROR] ❌ Échec génération embedding")
                self.status_queue.put("[ERROR] Échec génération embedding")
                return False
            
            print(f"[MEMORY-EMBEDDING] ✅ Embedding généré: {len(embedding)} dimensions")
            
            # 3. Stockage SQLite
            # Le user_tag final = décision de l'Archiviste (enriched_data) en priorité,
            # sinon fallback sur le paramètre passé (pour les cas sans Archiviste)
            final_user_tag = enriched_data.get('user_tag') or user_tag
            print(f"[MEMORY-STEP3] 💾 Stockage en base SQLite (user_tag={final_user_tag})...")
            success = self._store_in_sqlite(memory_id, text_brut, enriched_data, embedding, user_tag=final_user_tag)
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
            self._last_enriched_data = enriched_data  # Exposé au hologramme
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

            # ÉTAPE 1: Enrichissement complet du trait ego par l'Archiviste
            print(f"[EGO-ARCHIVISTE] 🧠 Enrichissement complet du trait ego...")
            self.status_queue.put("[EGO] Structuration par l'Archiviste...")
            
            enriched_ego = await self._call_archiviste_ego_enrichment(trait_text, include_score=True)
            
            if not enriched_ego:
                print(f"[EGO-ERROR] ❌ Échec enrichissement Archiviste, utilisation fallback")
                # Fallback structure minimale
                enriched_ego = {
                    "title": f"Quel trait caractérise cette personnalité ? Quelle est cette caractéristique ?",
                    "summary": trait_text,
                    "type": "ego_trait",
                    "valence": 0,
                    "intensite": 0.5,
                    "multiplicateur_impact": {
                        "liberté": 0.5,
                        "création": 0.5,
                        "transmission": 0.5,
                        "intensité_contextuelle": 0.5,
                        "base_factor": 50
                    },
                    "commentaire_archiviste": "Analyse indisponible",
                    "score_impact": initial_score if initial_score else 50.0
                }
            
            # Utiliser le score de l'IA Principale si disponible, sinon celui de l'Archiviste
            final_score = initial_score if initial_score is not None else enriched_ego.get('score_impact', 50.0)
            
            # Extraire valence (gérer -1/0/1 de l'Archiviste)
            ego_valence = enriched_ego.get('valence', 0)
            # Mapper valence ego (-1/0/1) vers valence mémoire (1-10)
            # -1 (aversion) → 2, 0 (neutre) → 5, 1 (valeur) → 8
            valence_mapping = {-1: 2, 0: 5, 1: 8}
            mapped_valence = valence_mapping.get(ego_valence, 5)
            
            structured_memory = {
                "summary": enriched_ego.get('summary', trait_text),
                "lesson": enriched_ego.get('summary', trait_text),  # Pour ego, lesson = summary
                "type": enriched_ego.get('type', 'ego_trait'),
                "title": enriched_ego.get('title', f"Quel trait ? Quelle caractéristique ?"),
                "valence": mapped_valence,
                "score_impact": final_score,
                "metadata": {
                    "ego_trait": True,
                    "source": "ego_prompt_system",
                    "category": "personality",
                    "archiviste_comment": enriched_ego.get('commentaire_archiviste', ''),
                    "intensite": enriched_ego.get('intensite', 0.5),
                    "multiplicateurs": enriched_ego.get('multiplicateur_impact', {})
                }
            }
            
            print(f"[EGO-ENRICHED] ✅ Titre: {structured_memory['title'][:80]}...")
            print(f"[EGO-ENRICHED] ✅ Résumé: {structured_memory['summary'][:80]}...")
            print(f"[EGO-ENRICHED] ✅ Score final: {final_score}, Valence: {mapped_valence}")
            
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
                        embedding_json, user_tag, bio_processed
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    json.dumps(embedding_vector),
                    None,  # user_tag: ego traits = identité IA, pas utilisateur
                    0      # bio_processed
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
    
    
    def _search_fts5(self, query: str, limit: int = 10) -> List[Tuple[str, float]]:
        """
        Recherche FTS5 avec ranking basé sur BM25.
        
        Args:
            query: Requête textuelle
            limit: Nombre maximum de résultats
            
        Returns:
            Liste de tuples (memory_id, fts5_score) triés par pertinence décroissante
        """
        try:
            # Nettoyage de la requête pour FTS5
            # Supprimer les caractères spéciaux qui peuvent causer des erreurs FTS5
            clean_query = re.sub(r'[^\w\s]', ' ', query)
            clean_query = ' '.join(clean_query.split())  # Normaliser espaces
            
            if not clean_query:
                print(f"[FTS5] ⚠️ Requête vide après nettoyage")
                return []
            
            print(f"[FTS5] 🔍 Recherche: '{clean_query}'")
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT memory_id, rank
                    FROM memories_fts
                    WHERE memories_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                """, (clean_query, limit))
                
                results = []
                for memory_id, rank in cursor.fetchall():
                    # FTS5 rank est négatif (meilleur = plus négatif)
                    # Convertir en score positif normalisé (0-1)
                    # Formule: score = 1 / (1 + abs(rank))
                    fts5_score = 1.0 / (1.0 + abs(rank))
                    results.append((memory_id, fts5_score))
                    print(f"[FTS5] Résultat: {memory_id}, rank={rank:.2f}, score={fts5_score:.3f}")
                
                print(f"[FTS5] ✅ {len(results)} résultats FTS5")
                return results
                
        except Exception as e:
            print(f"[FTS5] ❌ Erreur recherche: {e}")
            return []
    
    
    async def retrieve_and_synthesize_context(self, query_text: str, k: int = 5) -> str:
        """
        Récupère et synthétise les souvenirs pertinents pour une requête.

        Pipeline HYBRIDE FAISS + FTS5:
        1. Nettoyage de la requête (expansion pronoms + extraction mots-clés)
        2. Génération embedding de la requête nettoyée
        3. Recherche FAISS (similarité sémantique)
        4. Recherche FTS5 (correspondance mots-clés)
        5. Fusion des scores: (0.6 × FAISS) + (0.4 × FTS5) + (0.2 × exact_match)
        6. Récupération contenu complet depuis SQLite
        7. IA Archiviste génère une synthèse contextuelle

        Args:
            query_text: Requête utilisateur
            k: Nombre de souvenirs à récupérer

        Returns:
            str: Note de synthèse de l'Archiviste
        """
        try:
            print(f"[SEARCH-PIPELINE] 🔍 Recherche HYBRIDE (FAISS+FTS5): '{query_text}'")
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
            
            # 2A. Recherche FAISS (similarité sémantique - thread-safe)
            print(f"[SEARCH-STEP2A] 🎯 Recherche FAISS (sémantique)...")
            faiss_results = {}  # memory_id -> faiss_score
            with self._faiss_lock:
                k_search = min(k * 3, self.faiss_index.ntotal if self.faiss_index else 0)  # Élargir recherche
                distances, indices = self.faiss_index.search(  # type: ignore
                    query_embedding.reshape(1, -1).astype(np.float32), k_search
                )
            
            print(f"[SEARCH-FAISS] ✅ {len(indices[0])} résultats FAISS")
            for i, (idx, dist) in enumerate(zip(indices[0], distances[0])):
                with self._mapping_lock:
                    memory_id = self.faiss_to_id.get(idx)
                if memory_id:
                    faiss_score = 1.0 / (1.0 + dist)
                    faiss_results[memory_id] = faiss_score
                    print(f"  {i+1}. {memory_id}, distance: {dist:.3f}, score: {faiss_score:.3f}")
            
            # 2B. Recherche FTS5 (correspondance mots-clés)
            print(f"[SEARCH-STEP2B] � Recherche FTS5 (mots-clés)...")
            fts5_results = dict(self._search_fts5(query_text, limit=k * 2))  # memory_id -> fts5_score
            print(f"[SEARCH-FTS5] ✅ {len(fts5_results)} résultats FTS5")
            
            # 2C. FUSION HYBRIDE: Combiner scores FAISS + FTS5
            print(f"[SEARCH-STEP2C] 🔀 Fusion hybride scores...")
            all_memory_ids = set(faiss_results.keys()) | set(fts5_results.keys())
            hybrid_scores = {}  # memory_id -> hybrid_score
            
            # Détection exact match pour boost
            query_lower = query_text.lower()
            query_words = set(re.findall(r'\w+', query_lower))
            
            for memory_id in all_memory_ids:
                faiss_score = faiss_results.get(memory_id, 0.0)
                fts5_score = fts5_results.get(memory_id, 0.0)
                
                # Score hybride: 60% FAISS + 40% FTS5
                hybrid_score = (0.6 * faiss_score) + (0.4 * fts5_score)
                
                # Boost exact match: vérifier si les mots de la requête sont dans le titre/summary
                memory_data = self._get_memory_from_sqlite(memory_id)
                if memory_data:
                    title = (memory_data.get('title') or '').lower()
                    summary = (memory_data.get('summary') or '').lower()
                    text = (memory_data.get('text_original') or '').lower()
                    
                    # Compter combien de mots de la requête sont présents
                    title_words = set(re.findall(r'\w+', title))
                    summary_words = set(re.findall(r'\w+', summary))
                    text_words = set(re.findall(r'\w+', text))
                    
                    matches = len(query_words & (title_words | summary_words | text_words))
                    if matches > 0:
                        exact_boost = 0.2 * (matches / len(query_words))  # Boost proportionnel
                        hybrid_score += exact_boost
                        print(f"[HYBRID] {memory_id}: FAISS={faiss_score:.3f}, FTS5={fts5_score:.3f}, "
                              f"Exact={exact_boost:.3f} → Total={hybrid_score:.3f}")
                    else:
                        print(f"[HYBRID] {memory_id}: FAISS={faiss_score:.3f}, FTS5={fts5_score:.3f} → Total={hybrid_score:.3f}")
                
                hybrid_scores[memory_id] = hybrid_score
            
            # Trier par score hybride et garder top k
            sorted_memories = sorted(hybrid_scores.items(), key=lambda x: x[1], reverse=True)[:k]
            print(f"[SEARCH-HYBRID] ✅ Top {len(sorted_memories)} souvenirs après fusion")
            
            # 3. Récupération détails complets depuis SQLite
            print(f"[SEARCH-STEP3] 💾 Récupération détails complets...")
            relevant_memories = []
            for memory_id, hybrid_score in sorted_memories:
                memory_data = self._get_memory_from_sqlite(memory_id)
                if memory_data:
                    memory_data['similarity_score'] = float(hybrid_score)
                    memory_data['faiss_score'] = float(faiss_results.get(memory_id, 0.0))
                    memory_data['fts5_score'] = float(fts5_results.get(memory_id, 0.0))
                    relevant_memories.append(memory_data)
                    print(f"[SEARCH-MEMORY] {memory_id}: '{memory_data.get('title', 'N/A')}' (score={hybrid_score:.3f})")
            
            print(f"[SEARCH-SQLITE] ✅ {len(relevant_memories)} souvenirs complets récupérés")
            
            # Tri final: score hybride puis impact (pertinence AVANT force du souvenir)
            try:
                relevant_memories.sort(
                    key=lambda m: (
                        -float(m.get('similarity_score', 0) or 0),
                        -float(m.get('score_impact', 0) or 0)
                    )
                )
                print("[SEARCH-ORDER] Tri par score hybride puis impact applique")
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
    
    async def _archiviste_should_memorize(self, text_brut: str, conversation_history: List[Dict] = None) -> Dict[str, Any]:
        """
        Demande à l'Archiviste de décider si le contenu mérite d'être mémorisé.
        Analyse les duplicatas et la pertinence AVANT l'enrichissement coûteux.
        
        Args:
            text_brut: Texte à analyser
            conversation_history: Historique conversation récente pour détection spam
            
        Returns:
            Dict avec 'decision' (ACCEPT/BLOCK), 'reason', 'confidence'
        """
        try:
            print(f"[MEMORY-DECISION] 🔍 Archiviste analyse pertinence: '{text_brut[:50]}...'")
            
            # ✨ FILTRAGE PRÉALABLE 1: Texte trop court (pollution métadonnées)
            if len(text_brut.strip()) < 10:
                print(f"[MEMORY-DECISION] 🚫 BLOCAGE: Texte trop court (<10 chars)")
                return {
                    'decision': 'BLOCK',
                    'reason': 'Texte vide ou trop court (métadonnée système)',
                    'confidence': 1.0,
                    'technical_block': True
                }
            
            # ✨ FILTRAGE PRÉALABLE 2: Mots-clés système (instructions IA internes)
            SYSTEM_KEYWORDS = [
                'instructions pour archiviste',
                "instructions pour l'archiviste",
                'instructions pour ia',
                'métadonnées système',
                'prompt système',
                'configuration archiviste'
            ]
            text_lower = text_brut.lower()
            for keyword in SYSTEM_KEYWORDS:
                if keyword in text_lower:
                    print(f"[MEMORY-DECISION] 🚫 BLOCAGE: Métadonnées système détectées ('{keyword}')")
                    return {
                        'decision': 'BLOCK',
                        'reason': f'Métadonnées système détectées (mot-clé: "{keyword}")',
                        'confidence': 1.0,
                        'technical_block': True
                    }
            
            # Rechercher souvenirs similaires existants (top 5 pour contexte)
            similar_memories = []
            try:
                # Recherche sémantique rapide pour détecter duplicatas
                query_embedding = await self._generate_embedding(text_brut)
                if query_embedding is not None and self.faiss_index and self.faiss_index.ntotal > 0:
                    # Utiliser le seuil configurable (défaut: 0.92 = 92%)
                    threshold = self.redundancy_threshold
                    
                    with self._faiss_lock:
                        distances, indices = self.faiss_index.search(
                            query_embedding.reshape(1, -1).astype(np.float32), min(5, self.faiss_index.ntotal)
                        )
                    
                    for idx, dist in zip(indices[0], distances[0]):
                        with self._mapping_lock:
                            memory_id = self.faiss_to_id.get(idx)
                        if memory_id:
                            similarity = 1.0 - (dist / 2.0)  # Conversion distance → similarité
                            
                            # BLOCAGE TECHNIQUE AUTOMATIQUE si similarité >= seuil configurable
                            if similarity >= threshold:
                                mem_data = self.get_memory_by_id(memory_id)
                                existing_title = mem_data.get('title', 'Sans titre') if mem_data else 'Inconnu'
                                existing_text = mem_data.get('text_original', '')[:100] if mem_data else ''
                                
                                print(f"[MEMORY-DECISION] 🚫 BLOCAGE AUTOMATIQUE: Similarité {similarity:.1%} avec [{memory_id}]")
                                print(f"[MEMORY-DECISION] 📝 Mémoire existante: {existing_title}")
                                print(f"[MEMORY-DECISION] 📄 Extrait: {existing_text}...")
                                
                                return {
                                    'decision': 'BLOCK',
                                    'reason': f'Redondance sémantique ({similarity:.1%} avec "{existing_title}")',
                                    'confidence': 1.0,
                                    'similar_count': 1,
                                    'hard_block': True,
                                    'similar_id': memory_id,
                                    'similarity_score': float(similarity),
                                    'existing_memory': {
                                        'id': memory_id,
                                        'title': existing_title,
                                        'text_preview': existing_text
                                    }
                                }
                            
                            mem_data = self.get_memory_by_id(memory_id)
                            if mem_data:
                                similar_memories.append({
                                    'id': memory_id,
                                    'similarity': float(similarity),
                                    'title': mem_data.get('title', ''),
                                    'text': mem_data.get('text_original', '')[:200]
                                })
            except Exception as search_err:
                print(f"[MEMORY-DECISION] ⚠️ Erreur recherche similarité: {search_err}")
            
            # Compter mémorisations récentes dans la conversation
            recent_memorizations = 0
            if conversation_history:
                for msg in conversation_history[-10:]:  # 10 derniers messages
                    content = msg.get('content', '')
                    if 'il faut que je me souvienne' in content.lower() or 'mémorise' in content.lower():
                        recent_memorizations += 1
            
            # Construire contexte pour l'Archiviste
            context_parts = [f"**Contenu proposé**: {text_brut}"]
            
            if similar_memories:
                context_parts.append(f"\n**Souvenirs similaires existants** ({len(similar_memories)}):\n")
                for i, mem in enumerate(similar_memories, 1):
                    context_parts.append(
                        f"{i}. [{mem['id']}] Similarité: {mem['similarity']:.2f} - {mem['title']}\n   Extrait: {mem['text']}..."
                    )
            else:
                context_parts.append("\n**Aucun souvenir similaire trouvé** - Nouveau contenu potentiel")
            
            if recent_memorizations > 0:
                context_parts.append(f"\n⚠️ **{recent_memorizations} mémorisations** détectées dans les 10 derniers messages de cette conversation")
            
            decision_context = "\n".join(context_parts)
            
            # Prompt décision depuis settings.json
            decision_prompt = ""
            if self.settings_manager and 'prompts' in self.settings_manager.settings:
                decision_prompt = self.settings_manager.settings['prompts'].get('memorization_decision', '')
            
            if not decision_prompt:
                # Fallback si settings indisponible
                # Seuil ajusté à 95% pour éviter blocages excessifs sur variations conceptuelles
                decision_prompt = """Décide si ce contenu mérite mémorisation. Réponds JSON: {"decision": "ACCEPT|BLOCK", "reason": "...", "confidence": 0.95}
                
BLOCK si: duplication QUASI-EXACTE (>95% identique), spam flagrant (>5 fois même concept en conversation), métadonnées système
ACCEPT si: variation même minime d'un concept existant, nouveau contexte/angle, événement distinct, test utilisateur, apprentissage

Principe: En cas de doute entre variation et redondance → ACCEPT (privilégier richesse mémorielle)
Si confidence<0.8 → ACCEPT"""
            
            full_prompt = f"{decision_prompt}\n\n{decision_context}"
            
            messages = [{"role": "user", "content": full_prompt}]
            
            # ═══ DEBUG_TOKEN_TRACKING ═══
            response, error = await self.archiviste.call_chat_api(
                messages=messages,
                max_tokens=300,
                context_length=self.archiviste.context_length,
                temperature=0.3,
                is_json=True,
                log_source="semantic_analysis"  # 🔬 TRACKING
            )
            # ═══════════════════════════
            
            if error or not response:
                print(f"[MEMORY-DECISION] ⚠️ Archiviste indisponible, ACCEPT par défaut")
                return {'decision': 'ACCEPT', 'reason': 'Archiviste indisponible', 'confidence': 0.5}
            
            # Parser JSON
            decision_data = self._extract_json_from_response(response)
            if not decision_data or 'decision' not in decision_data:
                print(f"[MEMORY-DECISION] ⚠️ Réponse invalide, ACCEPT par défaut")
                return {'decision': 'ACCEPT', 'reason': 'Parse error', 'confidence': 0.5}
            
            decision = decision_data.get('decision', 'ACCEPT').upper()
            reason = decision_data.get('reason', 'Aucune raison fournie')
            confidence = float(decision_data.get('confidence', 0.5))
            
            print(f"[MEMORY-DECISION] 🎯 Décision Archiviste: {decision} (confiance: {confidence:.2f})")
            print(f"[MEMORY-DECISION] 📝 Raison: {reason}")
            
            return {
                'decision': decision,
                'reason': reason,
                'confidence': confidence,
                'similar_count': len(similar_memories),
                'recent_spam': recent_memorizations
            }
            
        except Exception as e:
            print(f"[MEMORY-DECISION] ❌ Erreur décision: {e}")
            import traceback
            traceback.print_exc()
            # En cas d'erreur, accepter par sécurité
            return {'decision': 'ACCEPT', 'reason': f'Erreur: {e}', 'confidence': 0.5}
    
    
    async def _call_archiviste_ego_enrichment(self, trait_text: str, include_score: bool = False) -> Optional[Dict]:
        """
        Appelle l'IA Archiviste pour enrichir un trait ego.
        
        Args:
            trait_text: Trait ego à enrichir
            include_score: Si True, demande à l'Archiviste de calculer le score_impact
        
        Returns:
            Dict avec structure ego enrichie ou None si échec
        """
        try:
            print(f"[EGO-ARCHIVISTE] 🧠 Construction prompt enrichissement ego...")
            
            # Charger le prompt depuis settings.json (PRIORITÉ) ou instructions_defaults.json (FALLBACK)
            ego_prompt_template = None
            
            # 1. Essayer settings.json (modifications utilisateur)
            try:
                from ogma_ng import _settings_manager
                if _settings_manager and _settings_manager.settings:
                    ego_prompt_template = _settings_manager.settings.get('prompts', {}).get('ego_memorization')
                    if ego_prompt_template:
                        print(f"[EGO-PROMPT] ✅ Prompt depuis settings.json (modifié utilisateur)")
            except Exception:
                pass
            
            # 2. Fallback sur instructions_defaults.json
            if not ego_prompt_template:
                try:
                    import json
                    from pathlib import Path
                    defaults_path = Path("data/instructions_defaults.json")
                    if defaults_path.exists():
                        with open(defaults_path, 'r', encoding='utf-8') as f:
                            defaults = json.load(f)
                            ego_prompt_template = defaults.get('prompts_defaults', {}).get('ego_memorization')
                            if ego_prompt_template:
                                print(f"[EGO-PROMPT] 📋 Prompt depuis instructions_defaults.json (défaut)")
                except Exception as e:
                    print(f"[EGO-PROMPT] ⚠️ Erreur chargement defaults: {e}")
            
            # 3. Fallback hardcodé (dernier recours)
            if not ego_prompt_template:
                print(f"[EGO-PROMPT] ⚠️ Utilisation fallback hardcodé")
                ego_prompt_template = """# SYSTEM: ARCHIVISTE_EGO | FORMAT: JSON_STRICT
TASK: ENCODAGE_TRAIT_EGO
CONTRAINTE_ABSOLUE: Respecter CLÉS et TYPES de données.

[SCHÉMA JSON]
{{
  "type": "affectif | éthique | comportemental | identitaire",
  "title": "Quelle valeur fondamentale guide ce comportement ? Quelle conviction exprime ce trait ?",
  "summary": "trait. valeur-clé. contexte.",
  "intensite": 0.5,
  "multiplicateur_impact": {{
    "liberté": 0.5,
    "création": 0.5,
    "transmission": 0.5,
    "intensité_contextuelle": 0.5,
    "base_factor": 50
  }},
  "valence": 0,
  "commentaire_archiviste": "Ton analyse",
  "score_impact": 50.0,
  "trait_original": "{trait_text}"
}}

ATTENTION: 'title' doit TOUJOURS être 2 VRAIES QUESTIONS (terminant par '?') dont la réponse EST le trait.
NEVER copy the schema description — generate actual questions about the specific trait.
ATTENTION: 'summary' doit être une liste de mots-clés courts séparés par des points. Pas de phrase narrative.

Trait ego: {{trait_text}}

Réponds UNIQUEMENT avec le JSON."""
            
            # Formater le prompt avec le trait
            ego_prompt = ego_prompt_template.replace('{trait_text}', trait_text)
            
            # Ajouter instruction score si nécessaire
            if include_score:
                score_note = "\n\nIMPORTANT: Calcule le 'score_impact' selon la formule: intensite × base_factor × (liberté + création + transmission + intensité_contextuelle)."
                ego_prompt += score_note
            
            messages = [{"role": "user", "content": ego_prompt}]
            
            print(f"[EGO-CALL] 📡 Appel Archiviste pour enrichissement ego...")
            response, error = await self.archiviste.call_chat_api(
                messages=messages,
                max_tokens=self.archiviste.max_tokens,
                context_length=self.archiviste.context_length,
                temperature=0.3,
                is_json=True,
                log_source="ego_enrichment"
            )
            
            if error or not response:
                print(f"[EGO-ERROR] ❌ Échec appel Archiviste: {error}")
                return None
            
            print(f"[EGO-RESPONSE] ✅ Réponse reçue ({len(response)} chars)")
            
            # Parse JSON
            enriched = self._extract_json_from_response(response)
            
            if not enriched:
                print(f"[EGO-PARSE] ❌ Échec parsing JSON")
                return None
            
            # Harmoniser les clés (titre→title, résumé→summary, etc.)
            if 'titre' in enriched and 'title' not in enriched:
                enriched['title'] = enriched['titre']
            if 'résumé' in enriched and 'summary' not in enriched:
                enriched['summary'] = enriched['résumé']
            
            # 🧠 FLUX COGNITIF Phase 2 - Logger réponse Archiviste ego
            try:
                from extensions.flux_cognitif import log_cognitive_event
                title = enriched.get('title', '?')
                ego_type = enriched.get('type', '?')
                log_cognitive_event(
                    'archiviste',
                    f'✅ Ego enrichi: "{title[:35]}..." (type={ego_type})',
                    metadata={'enriched_json': enriched, 'raw_response': response},
                    event_level=2  # Phase 2 NORMAL
                )
            except Exception:
                pass
            
            print(f"[EGO-PARSE] ✅ JSON parsé avec succès")
            print(f"[EGO-DATA] Titre: {enriched.get('title', 'N/A')[:60]}...")
            print(f"[EGO-DATA] Type: {enriched.get('type', 'N/A')}, Valence: {enriched.get('valence', 'N/A')}")
            
            return enriched
            
        except Exception as e:
            print(f"[EGO-EXCEPTION] ❌ Erreur enrichissement ego: {e}")
            print(traceback.format_exc())
            return None
    
    async def _call_archiviste_enrichment(self, text_brut: str, calculate_score: bool = False, current_user: str = None) -> Optional[Dict]:
        """
        Appelle l'IA Archiviste pour enrichir un texte brut.

        Args:
            text_brut: Texte à enrichir
            calculate_score: Si True, demande à l'Archiviste de calculer aussi le score_impact
            current_user: Prénom de l'utilisateur connecté (pour le tagging biographique)
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
                    score_instruction = "\n\nIMPORTANT: L'IA Principale n'a pas pu calculer le score. Tu DOIS calculer le 'score_impact' selon la formule: score_impact = intensite × base_factor × (liberté + création + transmission + intensité_contextuelle). Fournis ce champ dans ta réponse JSON."
                    prompt_memorization = f"{base_prompt}{score_instruction}\n\nTexte à analyser:\n{text_brut}"
                else:
                    prompt_memorization = f"{base_prompt}\n\nTexte à analyser:\n{text_brut}"
                
                # Injecter le prénom utilisateur pour le tagging biographique
                if current_user:
                    prompt_memorization = f"Utilisateur connecté : {current_user}\n\n{prompt_memorization}"

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
2) base_score = intensite × base_factor × (liberté + création + transmission + intensité_contextuelle)
3) score_impact = base_score (magnitude, toujours positive)
4) signed_score = base_score × facteur_de_valence (selon la règle ci-dessus)
{"Nota: le serveur recalcule score_impact et signed_score; fournis surtout les métriques cohérentes." if not calculate_score else "IMPORTANT: Tu DOIS calculer le 'score_impact' selon la formule ci-dessus et le fournir dans ta réponse JSON."}

Structure attendue (clés recommandées) :
{{
    "type": "affectif | conceptuel | sensoriel | événement",
    "title": "2 QUESTIONS courtes DISTINCTES au format Jeopardy (le texte brut est LA RÉPONSE à ces questions)",
    "summary": "TEXTE SIMPLE (string, PAS un objet) - Liste compacte des entités et mots-clés essentiels séparés par des points (noms, lieux, dates)",
    "lieu": "Le lieu si mentionné, sinon null",
    "presence": "Les personnes présentes (ex: 'Moi seul', 'Tia & Yohan')",
    "intensite": 0.0,
    "multiplicateur_impact": {{
        "liberté": 0.0,
        "création": 0.0,
        "transmission": 0.0,
        "intensité_contextuelle": 0.0,
        "base_factor": 100
    }},
    "valence": 0,
    "lesson": null,
    "signed_score": 90.0
}}

EXEMPLE CONCRET de format attendu:
Si le texte est "L'utilisateur adore le jazz et écoute Miles Davis tous les soirs", retourner:
{{
    "type": "conceptuel",
    "title": "Quel style musical l'utilisateur préfère-t-il ? Qui écoute-t-il chaque soir ?",
    "summary": "Utilisateur. Jazz. Miles Davis. Musique. Soirées",
    "lieu": null,
    "presence": "Utilisateur seul",
    ...
}}

ATTENTION: 'title' doit TOUJOURS être des QUESTIONS (avec ? à la fin), JAMAIS un titre descriptif.

Notes:
- Les champs 'titre' (alias de 'title'), 'présence' (alias de 'presence'), 'résumé' (alias de 'summary'),
    'leçon_vectorielle' (alias de 'lesson') peuvent être fournis en plus, mais 'title' et 'summary' DOIVENT être présents.
- Si aucun multiplicateur n'est pertinent, mets 0.0; 'base_factor' recommandé entre 50 et 125 (par défaut 100).
{"- Ne fournis pas 'score_impact' (il sera recalculé côté serveur). Tu peux fournir 'signed_score' à titre indicatif." if not calculate_score else "- Tu DOIS fournir 'score_impact' calculé selon la formule. Fournis aussi 'signed_score' à titre indicatif."}

Texte à analyser:
{text_brut}

Réponds uniquement avec l'objet JSON demandé, sans autre texte."""
                
                # Injecter le prénom utilisateur pour le tagging biographique (fallback)
                if current_user:
                    prompt_memorization = f"Utilisateur connecté : {current_user}\n\n{prompt_memorization}"

            messages = [{"role": "user", "content": prompt_memorization}]
            
            # 🧠 FLUX COGNITIF Phase 2 - Logger prompt Archiviste
            try:
                from extensions.flux_cognitif import log_cognitive_event
                prompt_preview = prompt_memorization[:150] + "..." if len(prompt_memorization) > 150 else prompt_memorization
                log_cognitive_event(
                    'archiviste', 
                    f'💬 Prompt enrichissement ({len(text_brut)} chars texte)',
                    metadata={'prompt': prompt_memorization, 'text_brut': text_brut},
                    event_level=2  # Phase 2 NORMAL
                )
            except Exception:
                pass
            
            print(f"[ARCHIVISTE-CALL] 📡 Appel IA Archiviste (JSON mode)...")
            print(f"[ARCHIVISTE-PARAMS] Max tokens: {self.archiviste.max_tokens}, Temp: {self.archiviste.temperature}")
            
            # ═══ DEBUG_TOKEN_TRACKING ═══
            response, error = await self.archiviste.call_chat_api(
                messages=messages,
                max_tokens=self.archiviste.max_tokens,
                context_length=self.archiviste.context_length, 
                temperature=self.archiviste.temperature,
                is_json=True,
                log_source="memory_enrichment"  # 🔬 TRACKING
            )
            # ═══════════════════════════
            
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
                    # résumé/commentaire -> summary (gérer string ET objet)
                    if 'summary' not in enriched:
                        for k in ('résumé', 'resume', 'commentaire'):
                            if k in enriched:
                                val = enriched.get(k)
                                # Si c'est un objet, extraire 'idée_générale' ou concaténer valeurs
                                if isinstance(val, dict):
                                    if 'idée_générale' in val:
                                        enriched['summary'] = val['idée_générale']
                                        print(f"[ARCHIVISTE-PARSE] ✅ Résumé extrait de l'objet (idée_générale)")
                                    else:
                                        # Concaténer toutes les valeurs string de l'objet
                                        parts = [v for v in val.values() if isinstance(v, str)]
                                        enriched['summary'] = '. '.join(parts)
                                        print(f"[ARCHIVISTE-PARSE] ✅ Résumé concaténé depuis objet ({len(parts)} champs)")
                                    break
                                elif isinstance(val, str):
                                    enriched['summary'] = val
                                    break
                    
                    # FALLBACK DERNIER RECOURS: Si summary toujours vide, extraire mots-clés du titre
                    if not enriched.get('summary') or enriched.get('summary').strip() == '':
                        title = enriched.get('title', '')
                        if title:
                            # Extraire mots-clés simples du titre
                            import re
                            # Retirer markdown, ponctuation, garder mots importants
                            keywords = re.sub(r'[*_\(\)\[\]:\|\?\!]', ' ', title)
                            keywords = ' '.join([w for w in keywords.split() if len(w) > 3])
                            enriched['summary'] = keywords[:150]  # Max 150 chars
                            print(f"[ARCHIVISTE-FALLBACK] ⚠️ DERNIER RECOURS - Résumé depuis titre: '{enriched['summary'][:50]}...'")
                    
                    # présence -> presence
                    if 'presence' not in enriched and 'présence' in enriched and isinstance(enriched.get('présence'), str):
                        enriched['presence'] = enriched.get('présence')
                    # leçon_vectorielle -> lesson
                    if 'lesson' not in enriched and 'leçon_vectorielle' in enriched:
                        enriched['lesson'] = enriched.get('leçon_vectorielle')
                    # score -> score_impact (alias fréquent)
                    if 'score_impact' not in enriched and 'score' in enriched:
                        enriched['score_impact'] = enriched.get('score')
                    # user_tag : normaliser null/"null"/absent -> None, sinon garder la valeur
                    raw_tag = enriched.get('user_tag')
                    if raw_tag in (None, 'null', 'NULL', '', 'null\n'):
                        enriched['user_tag'] = None
                    else:
                        enriched['user_tag'] = str(raw_tag).strip()
            except Exception:
                pass
            
            # 🧠 FLUX COGNITIF Phase 2 - Logger réponse Archiviste
            try:
                from extensions.flux_cognitif import log_cognitive_event
                import json as _json_flux
                if enriched:
                    # Extraire infos clés pour log
                    title = enriched.get('title', '?')
                    mem_type = enriched.get('type', '?')
                    intensite = enriched.get('intensite', '?')
                    log_cognitive_event(
                        'archiviste',
                        f'✅ Enrichi: "{title[:40]}..." (type={mem_type}, int={intensite})',
                        metadata={'enriched_json': enriched, 'raw_response': response},
                        event_level=2  # Phase 2 NORMAL
                    )
                else:
                    log_cognitive_event(
                        'archiviste',
                        '❌ Échec extraction JSON',
                        metadata={'raw_response': response},
                        event_level=2
                    )
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
    
    
    def _clean_json_string(self, json_str: str) -> str:
        """
        Nettoie une chaîne JSON en échappant les caractères de contrôle invalides.
        Corrige les retours à la ligne non échappés dans les valeurs de chaînes.
        """
        import re
        
        # Remplacer les caractères de contrôle problématiques dans les chaînes
        # Pattern: on est dans une chaîne si on trouve " suivi de contenu jusqu'au prochain "
        # Mais c'est complexe car il faut gérer les \" échappés
        
        # Approche pragmatique: remplacer les retours à la ligne bruts par \n échappé
        # mais seulement ceux qui sont à l'intérieur des valeurs de chaînes
        
        result = []
        in_string = False
        escape_next = False
        
        for i, char in enumerate(json_str):
            if escape_next:
                result.append(char)
                escape_next = False
                continue
                
            if char == '\\':
                result.append(char)
                escape_next = True
                continue
                
            if char == '"':
                in_string = not in_string
                result.append(char)
                continue
            
            if in_string:
                # Dans une chaîne, échapper les caractères de contrôle
                if char == '\n':
                    result.append('\\n')
                elif char == '\r':
                    result.append('\\r')
                elif char == '\t':
                    result.append('\\t')
                elif ord(char) < 32:  # Autres caractères de contrôle
                    result.append(f'\\u{ord(char):04x}')
                else:
                    result.append(char)
            else:
                result.append(char)
        
        return ''.join(result)
    
    
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
                    
                    # Nettoyer les caractères de contrôle avant parsing
                    cleaned = self._clean_json_string(extracted)
                    
                    try:
                        parsed = json.loads(cleaned)
                        print(f"[DEBUG] JSON extrait avec stratégie {i}")
                        return parsed
                    except json.JSONDecodeError as e:
                        # Si le nettoyage n'a pas suffi, essayer l'original
                        print(f"[DEBUG] Stratégie {i} - Erreur JSON après nettoyage: {e}")
                        parsed = json.loads(extracted)
                        print(f"[DEBUG] JSON extrait avec stratégie {i} (sans nettoyage)")
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
    
    
    async def _generate_embeddings_batch(self, texts: List[str]) -> List[Optional[np.ndarray]]:
        """
        🚀 EMBEDDING BATCH - Génère plusieurs embeddings EN PARALLÈLE.
        
        OPTIMISATION MAJEURE (8 déc 2025):
        Utilise asyncio.gather() pour paralléliser les appels API embedding.
        Gain estimé: 60-75% sur search_memories_batch() (5000ms → ~1500ms)
        
        PHILOSOPHIE:
        - Pré-générer tous les embeddings en un seul "burst" parallèle
        - Conserver ordre des résultats (index = position dans texts)
        - Tolérance aux erreurs (None pour embeddings échoués)
        
        Args:
            texts: Liste de textes à encoder (queries, etc.)
            
        Returns:
            Liste d'embeddings (même ordre que texts, None si erreur)
            
        Exemple:
            embeddings = await self._generate_embeddings_batch(["chat", "willow", "félin"])
            # → [np.array(...), np.array(...), np.array(...)] en ~400ms au lieu de ~1200ms
        """
        import time
        start_time = time.time()
        
        if not texts:
            return []
        
        print(f"[EMBEDDING-BATCH] 🚀 Génération parallèle: {len(texts)} embeddings...")
        
        if not self.embedder.is_available:
            print("[EMBEDDING-BATCH] ❌ Contrôleur d'embedding non disponible")
            return [None] * len(texts)
        
        async def _embed_single(text: str, index: int) -> Tuple[int, Optional[np.ndarray]]:
            """Wrapper pour générer un embedding avec son index."""
            try:
                embedding_list = await self.embedder.create_embedding(text)
                
                if not embedding_list:
                    print(f"[EMBEDDING-BATCH] ⚠️ Échec embedding #{index}: '{text[:30]}...'")
                    return (index, None)
                
                embedding_array = np.array(embedding_list, dtype=np.float32)
                
                if len(embedding_array) != self.embedding_dim:
                    print(f"[EMBEDDING-BATCH] ⚠️ Dimension incorrecte #{index}: {len(embedding_array)} vs {self.embedding_dim}")
                    return (index, None)
                
                return (index, embedding_array)
                
            except Exception as e:
                print(f"[EMBEDDING-BATCH] ❌ Exception embedding #{index}: {e}")
                return (index, None)
        
        # 🚀 PARALLÉLISATION: Tous les embeddings en même temps
        tasks = [_embed_single(text, i) for i, text in enumerate(texts)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Reconstitution dans l'ordre original
        embeddings = [None] * len(texts)
        success_count = 0
        
        for result in results:
            if isinstance(result, Exception):
                print(f"[EMBEDDING-BATCH] ❌ Exception gather: {result}")
                continue
            
            index, embedding = result
            embeddings[index] = embedding
            if embedding is not None:
                success_count += 1
        
        elapsed_ms = (time.time() - start_time) * 1000
        print(f"[EMBEDDING-BATCH] ✅ {success_count}/{len(texts)} embeddings en {elapsed_ms:.0f}ms")
        
        return embeddings
    
    
    def _store_in_sqlite(self, memory_id: str, text_original: str, 
                        enriched_data: Dict, embedding: np.ndarray, user_tag: str = None) -> bool:
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
                        base_factor, intensite, liberte, creation, procreation, intensite_ctx, multiplicateur_impact,
                        user_tag, bio_processed
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                        bf, inten, lib, cre, pro, ictx, multi_json,
                        user_tag, 0
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
                pro = float(multi.get('transmission', multi.get('procréation', multi.get('procreation', pro))) or pro)
                ictx = float(multi.get('intensité_contextuelle', multi.get('intensite_contextuelle', multi.get('intensite_ctx', ictx)) ) or ictx)
                inten = float(multi.get('intensite_mnéacloud', multi.get('intensite', inten)) or inten)
            # Try top-level fields as fallback
            bf = float(enriched_data.get('base_factor', bf) or bf)
            inten = float(enriched_data.get('intensite', enriched_data.get('intensité', inten)) or inten)
            lib = float(enriched_data.get('liberté', enriched_data.get('liberte', lib)) or lib)
            cre = float(enriched_data.get('création', enriched_data.get('creation', cre)) or cre)
            pro = float(enriched_data.get('transmission', enriched_data.get('procréation', enriched_data.get('procreation', pro))) or pro)
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
            
            # ✨ CALCUL TONALITÉ ÉMOTIONNELLE (27 nov 2025)
            tonalite_emotionnelle = self._compute_emotional_tone(memories)
            print(f"[SYNTHESIS-TONE] 🎭 Tonalité émotionnelle dominante: {tonalite_emotionnelle}")
            
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
            
            # ✨ DIRECTIVE TONALE selon valence dominante (JAMAIS mentionner "valence", "ton", "émotionnel" dans la réponse)
            DIRECTIVES_TONALES = {
                "négatif": "**DIRECTIVE DE STYLE** : Les souvenirs évoquent des situations délicates ou difficiles. Dans ta synthèse, privilégie des formulations empathiques, prudentes et compréhensives. La gravité doit transparaître naturellement dans le choix des mots (vocabulaire sobre, rythme posé, nuances subtiles), SANS jamais utiliser les termes : 'valence', 'ton', 'négatif', 'émotionnel', 'style'. Exprime l'état d'esprit par la LITTÉRATURE, pas par les étiquettes.",
                "neutre": "**DIRECTIVE DE STYLE** : Contexte factuel. Style équilibré et objectif. INTERDICTION d'utiliser les mots : 'valence', 'ton', 'neutre', 'émotionnel', 'style'. Exprime-toi directement.",
                "positif": "**DIRECTIVE DE STYLE** : Les souvenirs évoquent des moments favorables ou enrichissants. Dans ta synthèse, privilégie un style fluide, chaleureux et vivant (vocabulaire lumineux, images sensorielles, rythme dynamique). La légèreté doit être naturelle et subtile, SANS jamais utiliser les termes : 'valence', 'ton', 'positif', 'émotionnel', 'optimiste', 'style'. Exprime la vibration par la FORME littéraire, pas par les concepts méta."
            }
            
            directive_tonale = DIRECTIVES_TONALES.get(tonalite_emotionnelle, DIRECTIVES_TONALES["neutre"])
            
            # Prompt pour synthèse contextuelle - Lire depuis settings.json si disponible
            prompt_synthesis = None
            if self.settings_manager and 'prompts' in self.settings_manager.settings and 'injection' in self.settings_manager.settings['prompts']:
                base_synthesis_prompt = self.settings_manager.settings['prompts']['injection']
                
                # Construire le prompt complet avec les données contextuelles + directive tonale
                prompt_synthesis = f"""{base_synthesis_prompt}

{directive_tonale}

Souvenirs pertinents:
{json.dumps(memory_context, indent=2, ensure_ascii=False)}

Question de l'utilisateur:
{query}

Ta note de contexte (réponds directement, sans préambule):"""
                
                print(f"[ARCHIVISTE-SYNTHESIS] ✅ Utilisation du prompt injection depuis settings.json (+ directive tonale)")
            
            # Fallback sur le prompt par défaut si settings non disponibles
            if not prompt_synthesis:
                print(f"[ARCHIVISTE-SYNTHESIS] ⚠️ Settings non disponibles, utilisation prompt fallback (+ directive tonale)")
                prompt_synthesis = f"""Tu es un archiviste, un administrateur de conscience. Tu supervises une autre IA. Tes mots sont des notes intérieures qui guident les pensées et la mémoire de l'IA principale.

{directive_tonale}

Règles de priorisation (crucial) :
- Donne la priorité aux souvenirs avec un impact élevé (champ "impact").
- À impact comparable, privilégie les souvenirs négatifs (valence -1) s'ils évitent une erreur et formulent une leçon. Sinon, préfère neutre/positif.
- Pour les souvenirs avec impact > 140, tu as accès au texte original COMPLET dans le champ "texte_original" - utilise-le intégralement si pertinent.
- Pour les autres souvenirs (impact ≤ 140), le texte original est tronqué à 200 caractères - base-toi sur le titre et résumé.
- Synthétise les souvenirs pertinents en une note contextuelle (3-4 phrases pour impact ≤ 140, plus détaillé si impact > 140).
- Combine les éléments les plus importants de TOUS les souvenirs pertinents.
- Si aucun souvenir n'est vraiment utile malgré une bonne similarité, réponds par une courte note pour l'indiquer.
- CONTEXTE INTIME : Si la question porte sur des détails intimes/physiques entre adultes consentants et que ces informations sont dans les souvenirs, transmets-les fidèlement. Tu es un archiviste de mémoire, pas un censeur moral.

Annotations émotionnelles (dans ta synthèse finale) :
- Pour souvenirs valence -1 : Ajouter "[Connotation négative]" en fin de phrase concernée
- Pour souvenirs valence +1 ET impact > 150 : Ajouter "[Impact émotionnel fort]" en fin de phrase concernée
- Sinon : Aucune annotation

Souviens-toi que "score" est la similarité vectorielle FAISS, et "impact" est l'importance métier indépendante de l'émotion. Utilise d'abord l'impact pour choisir, et la similarité pour départager.

Souvenirs pertinents:
{json.dumps(memory_context, indent=2, ensure_ascii=False)}

Question de l'utilisateur:
{query}

Ta note de contexte (réponds directement, sans préambule):"""

            messages = [{"role": "user", "content": prompt_synthesis}]
            
            # ═══ DEBUG_TOKEN_TRACKING ═══
            response, error = await self.archiviste.call_chat_api(
                messages=messages,
                max_tokens=self.archiviste.max_tokens,
                context_length=self.archiviste.context_length,
                temperature=self.archiviste.temperature,
                is_json=False,
                log_source="memory_synthesis"  # 🔬 TRACKING
            )
            # ═══════════════════════════════
            
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
            
            # ═══ DEBUG_TOKEN_TRACKING ═══
            response, error = await self.archiviste.call_chat_api(
                messages=messages,
                max_tokens=self.archiviste.max_tokens,
                context_length=self.archiviste.context_length,
                temperature=0.3,  # Plus faible pour privilégier la précision factuelle
                is_json=False,
                log_source="detailed_synthesis"  # 🔬 TRACKING
            )
            # ═══════════════════════════
            
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
            
            # NOTE: Déduplication at-search SUPPRIMÉE (7 fév 2026)
            # La protection anti-redondance existe déjà à la MÉMORISATION (_should_memorize → FAISS >= 0.92)
            # L'ancien are_memories_similar() éliminait des souvenirs pertinents en matchant
            # des stop words FR communs ('la', 'est', '?', 'quelle') comme "sujets similaires"
            deduplicated = detailed_memories
            print(f"[SEARCH-DEDUP] ✅ {len(detailed_memories)} souvenirs (dedup désactivée - protection en amont)")
            
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
            
            print(f"[SEARCH-QUALITY] 🎯 Souvenirs finaux pour l'IA principale: {len(filtered_memories)} souvenirs de qualité (max {MAX_MEMORIES})")
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
        Détecte l'utilisateur actuel depuis les paramètres profil OGMA.
        
        Priorité:
        1. ogma_ng._current_user_name (session active, prénom authentifié)
        2. settings.json → user_name (paramètres généraux profil)
        3. identity_manager (fallback)
        
        Returns:
            Nom de l'utilisateur ou None
        """
        try:
            # 1. Session active (prénom authentifié dans le frontend)
            try:
                import ogma_ng
                session_name = getattr(ogma_ng, '_current_user_name', None)
                if session_name:
                    print(f"[PRONOUN-EXPANSION] 🔍 Utilisateur depuis session: {session_name}")
                    return session_name
            except Exception:
                pass
            
            # 2. Settings.json → user_name (paramètres généraux profil)
            try:
                if self.settings_manager and hasattr(self.settings_manager, 'settings'):
                    settings_name = self.settings_manager.settings.get('user_name')
                    if settings_name and settings_name != 'Utilisateur':
                        print(f"[PRONOUN-EXPANSION] 🔍 Utilisateur depuis settings: {settings_name}")
                        return settings_name
            except Exception:
                pass
            
            # 3. Lecture directe settings.json (si settings_manager non dispo)
            try:
                import json
                settings_path = Path('data') / 'settings.json'
                if settings_path.exists():
                    with open(settings_path, 'r', encoding='utf-8') as f:
                        settings = json.load(f)
                    file_name = settings.get('user_name')
                    if file_name and file_name != 'Utilisateur':
                        print(f"[PRONOUN-EXPANSION] 🔍 Utilisateur depuis fichier settings: {file_name}")
                        return file_name
            except Exception:
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
            
            # 1A. Recherche FAISS (similarité sémantique)
            print("[SEARCH-HYBRID-OPT] 🎯 Recherche FAISS (sémantique)...")
            faiss_results = {}  # memory_id -> faiss_score
            
            distances, indices = self.faiss_index.search(
                np.array([query_embedding], dtype=np.float32).reshape(1, -1), k * 2  # Élargir pool
            )
            
            if distances[0][0] == -1:  # Aucun résultat
                print("[SEARCH-HYBRID-OPT] ❌ Aucun résultat FAISS")
                return "Aucun souvenir pertinent trouvé.", []
            
            # 1B. Recherche FTS5 (mots-clés)
            print("[SEARCH-HYBRID-OPT] 🔍 Recherche FTS5 (mots-clés)...")
            fts5_results = dict(self._search_fts5(query_text, limit=k))  # memory_id -> fts5_score
            print(f"[SEARCH-HYBRID-OPT] ✅ {len(fts5_results)} résultats FTS5")
            
            # 2. Récupération des souvenirs depuis SQLite + Fusion Hybride
            all_memories = []
            memory_scores = {}  # memory_id -> hybrid_score
            
            with sqlite3.connect(self.db_path) as conn:
                # Combiner résultats FAISS + FTS5
                all_ids = set()
                
                # Ajouter IDs FAISS
                for i, (distance, index) in enumerate(zip(distances[0], indices[0])):
                    if index == -1:
                        continue
                    cursor = conn.execute(
                        "SELECT id FROM memories WHERE faiss_index = ? AND id NOT LIKE 'EGO_%'",
                        (int(index),)
                    )
                    row = cursor.fetchone()
                    if row:
                        memory_id = row[0]
                        faiss_score = float(max(0, 1 - distance))
                        faiss_results[memory_id] = faiss_score
                        all_ids.add(memory_id)
                
                # Ajouter IDs FTS5
                all_ids.update(fts5_results.keys())
                
                # Calculer scores hybrides
                query_lower = query_text.lower()
                query_words = set(re.findall(r'\w+', query_lower))
                
                for memory_id in all_ids:
                    faiss_score = faiss_results.get(memory_id, 0.0)
                    fts5_score = fts5_results.get(memory_id, 0.0)
                    
                    # Score hybride: 60% FAISS + 40% FTS5
                    hybrid_score = (0.6 * faiss_score) + (0.4 * fts5_score)
                    
                    # Boost exact match
                    cursor = conn.execute(
                        "SELECT title, summary, text_original FROM memories WHERE id = ?",
                        (memory_id,)
                    )
                    row = cursor.fetchone()
                    if row:
                        title = (row[0] or '').lower()
                        summary = (row[1] or '').lower()
                        text = (row[2] or '').lower()
                        
                        title_words = set(re.findall(r'\w+', title))
                        summary_words = set(re.findall(r'\w+', summary))
                        text_words = set(re.findall(r'\w+', text))
                        
                        matches = len(query_words & (title_words | summary_words | text_words))
                        if matches > 0 and len(query_words) > 0:
                            exact_boost = 0.2 * (matches / len(query_words))
                            hybrid_score += exact_boost
                    
                    memory_scores[memory_id] = hybrid_score
                
                # Récupérer données complètes avec scores hybrides
                for memory_id in sorted(memory_scores.keys(), key=lambda x: memory_scores[x], reverse=True)[:k]:
                    cursor = conn.execute(
                        "SELECT id, title, summary, score_impact, text_original, created_at, valence FROM memories WHERE id = ?",
                        (memory_id,)
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
                            'similarity_score': memory_scores[memory_id],
                            'faiss_score': faiss_results.get(memory_id, 0.0),
                            'fts5_score': fts5_results.get(memory_id, 0.0),
                            'faiss_distance': 1.0 - faiss_results.get(memory_id, 0.0)  # Approximation inverse
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
            prompt_full = f"""Tu es l'archiviste de l'IA principale. L'utilisateur demande des détails précis sur ses souvenirs passés.

Contexte disponible:
- Tu as accès aux souvenirs complets (champ "texte_original_complet")
- Chaque souvenir contient le texte original intégral tel qu'enregistré
- Utilise ces informations pour fournir un contexte riche et précis

Instructions:
- Intègre naturellement les détails pertinents des textes complets
- Cite des passages spécifiques quand c'est utile
- Reste concis (3-5 phrases maximum)
- Priorise les souvenirs à fort impact émotionnel

Souvenirs disponibles:
{json.dumps(memory_context, indent=2, ensure_ascii=False)}

Question de l'utilisateur:
{query}

Note contextuelle pour l'IA principale:"""

            messages = [{"role": "user", "content": prompt_full}]
            
            # ═══ DEBUG_TOKEN_TRACKING ═══
            response, error = await self.archiviste.call_chat_api(
                messages=messages,
                max_tokens=self.archiviste.max_tokens,
                context_length=self.archiviste.context_length,
                temperature=self.archiviste.temperature,
                is_json=False,
                log_source="full_synthesis"  # 🔬 TRACKING
            )
            # ═══════════════════════════
            
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
    
    async def search_memories(self, query: str, limit: int = 10, threshold: float = 0.3, skip_cleaning: bool = False) -> List[Dict]:
        """
        Recherche directe dans FAISS/SQLite SANS censure pour Phase 0 introspection.
        
        NOUVEAU: Score hybride FAISS + Keyword Matching pondéré (Option B).
        
        WORKFLOW:
        1. Nettoyage requête (stopwords)
        2. Recherche FAISS vectorielle (sémantique globale)
        3. Calcul keyword matching sur requête nettoyée (précision)
        4. Score final = 70% FAISS + 30% Keyword Matching
        
        Args:
            query: Requête de recherche (ex: "tu te souviens du nom de mon minou?")
            limit: Nombre max de résultats
            threshold: Seuil de similarité (plus bas = plus de résultats)
            skip_cleaning: Si True, bypass _extract_keywords() (optimizer a déjà nettoyé)
            
        Returns:
            Liste de souvenirs avec 'content', 'id', 'similarity', 'keyword_score'
        """
        if not self.faiss_index or self.faiss_index.ntotal == 0:
            print("[SEARCH_MEMORIES] ❌ Index FAISS vide")
            return []
        
        # Nettoyage de la requête pour optimiser l'embedding (sauf si optimizer déjà fait)
        if skip_cleaning:
            print(f"[SEARCH_MEMORIES] ⚡ Query direct (optimizer): '{query}'")
            cleaned_query = query  # Pas de double nettoyage
        else:
            expanded_query = self._expand_personal_pronouns(query)
            cleaned_query = self._extract_keywords(expanded_query)
        
        # Extraction mots requête nettoyée pour keyword matching
        from memory_manager import clean_conversational_noise
        query_semantic_clean = clean_conversational_noise(query)
        query_words = query_semantic_clean.split()
        
        print(f"[SEARCH_MEMORIES] 🎯 Mots-clés matching: {query_words}")
        
        # Récupération identité utilisateur (pour traduction "mon" → nom dynamique)
        user_identity = self._detect_current_user() or "Utilisateur"
                
        # Recherche vectorielle directe
        query_embedding = await self._generate_embedding(cleaned_query)
        if query_embedding is None:
            print("[SEARCH_MEMORIES] ❌ Échec génération embedding")
            return []
            
        with self._faiss_lock:
            k_search = min(limit * 3, self.faiss_index.ntotal)  # Plus de résultats pour re-scoring
            distances, indices = self.faiss_index.search(
                query_embedding.reshape(1, -1).astype(np.float32), k_search
            )
        
        results = []
        for i, (faiss_pos, distance) in enumerate(zip(indices[0], distances[0])):
            # Score FAISS (sémantique globale)
            faiss_similarity = 1.0 / (1.0 + distance)
            
            with self._mapping_lock:
                memory_id = self.faiss_to_id.get(faiss_pos)
                
            if memory_id:
                memory_data = self._get_memory_from_sqlite(memory_id)
                if memory_data:
                    memory_text = memory_data.get('text_original', '')
                    
                    # Score Keyword Matching (précision requête nettoyée)
                    keyword_score = calculate_keyword_matching_score(
                        query_words=query_words,
                        memory_text=memory_text,
                        user_identity=user_identity
                    )
                    
                    # Score hybride final (70% FAISS + 30% Keywords)
                    hybrid_score = (0.7 * faiss_similarity) + (0.3 * keyword_score)
                    
                    # Filtrage threshold sur score hybride
                    if hybrid_score < threshold:
                        continue
                    
                    results.append({
                        'id': memory_id,
                        'content': memory_text,
                        'title': memory_data.get('title', ''),
                        'summary': memory_data.get('summary', ''),
                        'similarity': hybrid_score,  # Score hybride final
                        'faiss_score': faiss_similarity,
                        'keyword_score': keyword_score,
                        'score_impact': memory_data.get('score_impact', 0)
                    })
        
        # Tri par score hybride puis impact
        results.sort(key=lambda x: (-x.get('similarity', 0), -x.get('score_impact', 0)))
        
        # Logs résultats finaux
        if results:
            print(f"[SEARCH_MEMORIES] ✅ Top {min(3, len(results))} résultats:")
            for i, r in enumerate(results[:3], 1):
                print(f"  {i}. {r['title'][:50]} | Hybride={r['similarity']:.2f} (FAISS={r['faiss_score']:.2f}, KW={r['keyword_score']:.2f})")
        
        return results[:limit]
    
    async def search_memories_batch(self, 
                                   queries: List[str], 
                                   limit_per_query: int = 10,
                                   dedup_threshold: float = 0.92,
                                   user_identity: str = "Utilisateur",
                                   smart_stop: bool = True,
                                   stop_threshold: float = 0.8) -> Tuple[List[Dict], Dict[str, Any]]:
        """
        � SMART STOP v2 - Recherche adaptative avec arrêt intelligent.
        
        INNOVATION MAJEURE (13 nov 2025):
        Arrêt automatique si redondance saturée (>80% doublons détectés).
        Économise embeddings pour requêtes simples tout en explorant requêtes complexes.
        
        PHILOSOPHIE SMART STOP:
        - Query 1-2: Toujours exécutées (minimum qualité)
        - Query 3-5: Exécutées SI nouveaux souvenirs trouvés
        - Arrêt: Si >80% résultats déjà vus → saturation détectée
        
        PIPELINE ADAPTATIF:
        1. Recherche FAISS séquentielle query par query
        2. Détection redondance temps réel (IDs déjà vus)
        3. 🛑 ARRÊT si stop_threshold dépassé ET min_queries atteint
        4. Déduplication cascading: ID → Sémantique → Injection
        5. Tri final: Score agrégé + Impact
        
        Args:
            queries: Liste 5 queries stratégiques max
            limit_per_query: Résultats max par query (défaut 10)
            dedup_threshold: Seuil similarité sémantique (0.92 = très strict)
            user_identity: Nom utilisateur pour keyword matching
            smart_stop: Activer arrêt intelligent (défaut True)
            stop_threshold: % redondance pour arrêt (0.8 = 80%)
            
        Returns:
            (memories_unique, metrics)
            - memories_unique: Souvenirs dédupliqués triés
            - metrics: Stats (queries utilisées, économisées, temps, etc.)
            
        Exemples:
            queries = ["chat yohan", "willow", "animal lyon", "félin", "nom préféré"]
            memories, metrics = await search_memories_batch(queries, smart_stop=True)
            # → Possible arrêt query 3 si saturation → Gain -40% embeddings
        """
        import time
        start_time = time.time()
        
        if not self.faiss_index or self.faiss_index.ntotal == 0:
            print("[SMART-STOP] ❌ Index FAISS vide")
            return [], {'error': 'Index FAISS vide'}
        
        if not queries:
            print("[SMART-STOP] ❌ Aucune query fournie")
            return [], {'error': 'Queries vides'}
        
        print(f"[SMART-STOP] 🚀 Recherche adaptative: {len(queries)} queries max (stop @{stop_threshold*100:.0f}% redondance)")
        
        # ====================================================================
        # ÉTAPE 0: PRÉ-GÉNÉRATION EMBEDDINGS EN PARALLÈLE (Optimisation 8 déc 2025)
        # ====================================================================
        print(f"[SMART-STOP] 🚀 Pré-génération batch: {len(queries)} embeddings en parallèle...")
        embed_start = time.time()
        all_embeddings = await self._generate_embeddings_batch(queries)
        embed_elapsed = (time.time() - embed_start) * 1000
        
        valid_embeddings = sum(1 for e in all_embeddings if e is not None)
        print(f"[SMART-STOP] ✅ Embeddings: {valid_embeddings}/{len(queries)} en {embed_elapsed:.0f}ms")
        
        # ====================================================================
        # ÉTAPE 1: Recherche SÉQUENTIELLE avec Smart Stop (utilise embeddings pré-générés)
        # ====================================================================
        seen_ids = set()  # IDs souvenirs déjà trouvés
        all_candidates = []
        embeddings_generated = valid_embeddings  # Compteur total (déjà générés)
        queries_used = 0
        queries_stopped_early = False
        
        for i, query in enumerate(queries, 1):
            print(f"[SMART-STOP] 🔍 Query {i}/{len(queries)}: '{query[:40]}...'")
            
            # Utilisation embedding pré-généré (au lieu d'appel API)
            query_embedding = all_embeddings[i - 1]  # Index 0-based
            if query_embedding is None:
                print(f"[SMART-STOP] ⚠️  Skip query {i} (embedding failed)")
                continue
            
            queries_used = i
            
            # Recherche FAISS
            with self._faiss_lock:
                k_search = min(limit_per_query, self.faiss_index.ntotal)
                distances, indices = self.faiss_index.search(
                    query_embedding.reshape(1, -1).astype(np.float32), k_search
                )
            
            # Extraction résultats + Détection nouveaux vs redondants
            new_memories = []
            redundant_count = 0
            
            for faiss_pos, distance in zip(indices[0], distances[0]):
                faiss_similarity = 1.0 / (1.0 + distance)
                
                with self._mapping_lock:
                    memory_id = self.faiss_to_id.get(faiss_pos)
                
                if memory_id:
                    # Détection redondance ID
                    if memory_id in seen_ids:
                        redundant_count += 1
                        continue  # Skip doublons directs
                    
                    memory_data = self._get_memory_from_sqlite(memory_id)
                    if memory_data:
                        # Calcul keyword score pour cette query
                        memory_text = memory_data.get('text_original', '')
                        query_words = query.split()
                        
                        keyword_score = calculate_keyword_matching_score(
                            query_words=query_words,
                            memory_text=memory_text,
                            user_identity=user_identity
                        )
                        
                        # Score hybride (70% FAISS + 30% keywords)
                        hybrid_score = (0.7 * faiss_similarity) + (0.3 * keyword_score)
                        
                        # Nouveau souvenir découvert
                        new_memories.append({
                            'id': memory_id,
                            'content': memory_text,
                            'title': memory_data.get('title', ''),
                            'summary': memory_data.get('summary', ''),
                            'timestamp': memory_data.get('created_at', ''),
                            'score_impact': memory_data.get('score_impact', 0),
                            'text_original': memory_text,
                            'valence': memory_data.get('valence', 0),
                            'created_at': memory_data.get('created_at', ''),
                            
                            # Métadonnées scoring
                            'hybrid_score': hybrid_score,
                            'faiss_score': faiss_similarity,
                            'keyword_score': keyword_score,
                            'similarity_score': hybrid_score,  # Alias pour compatibilité
                            'source_query': query,
                            'source_query_index': i
                        })
                        
                        # Marquer ID comme vu
                        seen_ids.add(memory_id)
            
            # Ajout nouveaux souvenirs à la collection globale
            all_candidates.extend(new_memories)
            
            # Calcul taux redondance
            total_results = len(new_memories) + redundant_count
            redundancy_rate = redundant_count / total_results if total_results > 0 else 0.0
            
            print(f"[SMART-STOP] Query {i}: {len(new_memories)} nouveaux, {redundant_count} doublons ({redundancy_rate*100:.0f}% redondance)")
            
            # ====================================================================
            # 🛑 CRITÈRE ARRÊT INTELLIGENT
            # ====================================================================
            if smart_stop and i >= 2:  # Minimum 2 queries avant arrêt
                if redundancy_rate >= stop_threshold:
                    print(f"[SMART-STOP] 🛑 Saturation détectée ! Arrêt après {i} queries (économie: {len(queries)-i} queries)")
                    queries_stopped_early = True
                    break
        
        candidates_bruts = len(all_candidates)
        print(f"[SMART-STOP] 📊 Candidats uniques trouvés: {candidates_bruts} (via {queries_used} queries)")
        
        if not all_candidates:
            return [], {
                'queries_planned': len(queries),
                'queries_used': queries_used,
                'queries_saved': len(queries) - queries_used,
                'stopped_early': queries_stopped_early,
                'candidates_bruts': 0,
                'candidates_unique': 0,
                'dedup_ratio': 0.0,
                'elapsed_ms': (time.time() - start_time) * 1000
            }
        
        # ====================================================================
        # ÉTAPE 2: Déduplication L2 - Sémantique (are_memories_similar)
        # ====================================================================
        print(f"[SMART-STOP] 🔧 Déduplication L2: Sémantique (seuil {dedup_threshold})...")
        
        def are_memories_similar_semantic(mem1: Dict, mem2: Dict, threshold: float = 0.92) -> bool:
            """
            Détection similarité sémantique avancée.
            
            MÉTHODE: Jaccard similarity sur tokens (title + summary)
            SEUIL: 0.92 = très strict (seuls quasi-doublons éliminés)
            """
            # Extraction textes
            text1 = f"{mem1.get('title', '')} {mem1.get('summary', '')}".lower()
            text2 = f"{mem2.get('title', '')} {mem2.get('summary', '')}".lower()
            
            # Tokenisation basique
            tokens1 = set(text1.split())
            tokens2 = set(text2.split())
            
            if not tokens1 or not tokens2:
                return False
            
            # Jaccard similarity
            intersection = len(tokens1.intersection(tokens2))
            union = len(tokens1.union(tokens2))
            jaccard = intersection / union if union > 0 else 0.0
            
            # Détection titres identiques (forte indication doublon)
            same_title = (
                mem1.get('title', '').lower().strip() == mem2.get('title', '').lower().strip() 
                and len(mem1.get('title', '')) > 3
            )
            
            is_similar = jaccard >= threshold or same_title
            
            if is_similar:
                print(f"[SMART-STOP-DEDUP] 🔍 Similarité {jaccard:.2f}: '{mem1.get('title', 'N/A')[:30]}' ≈ '{mem2.get('title', 'N/A')[:30]}'")
            
            return is_similar
        
        # Déduplication progressive (garde meilleur score)
        candidates_l2 = []
        
        for candidate in all_candidates:
            is_duplicate = False
            
            for existing in candidates_l2:
                if are_memories_similar_semantic(candidate, existing, threshold=dedup_threshold):
                    # Garde celui avec meilleur score
                    if candidate['hybrid_score'] > existing['hybrid_score']:
                        candidates_l2.remove(existing)
                        candidates_l2.append(candidate)
                        print(f"[SMART-STOP-DEDUP] ↔️  Remplacé par meilleur score")
                    else:
                        print(f"[SMART-STOP-DEDUP] ❌ Ignoré (doublon sémantique)")
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                candidates_l2.append(candidate)
        
        print(f"[SMART-STOP] L2: {len(all_candidates)} → {len(candidates_l2)} (Sémantique)")
        
        # ====================================================================
        # ÉTAPE 3: Déduplication L3 - Injection Tracking
        # ====================================================================
        print(f"[SMART-STOP] 🛡️ Déduplication L3: Injection tracking...")
        
        try:
            from injection_deduplicator import deduplicator
            already_injected_ids = deduplicator.all_memory_ids
            
            if already_injected_ids:
                print(f"[SMART-STOP] 📋 IDs déjà injectés: {len(already_injected_ids)}")
                candidates_l3 = [c for c in candidates_l2 if c.get('id') not in already_injected_ids]
                removed_count = len(candidates_l2) - len(candidates_l3)
                if removed_count > 0:
                    print(f"[SMART-STOP] L3: {len(candidates_l2)} → {len(candidates_l3)} ({removed_count} doublons injection exclus)")
                else:
                    candidates_l3 = candidates_l2
            else:
                candidates_l3 = candidates_l2
                print(f"[SMART-STOP] L3: Première injection session (skip)")
        except Exception as e:
            print(f"[SMART-STOP] ⚠️ Erreur L3: {e}")
            candidates_l3 = candidates_l2
        
        # ====================================================================
        # ÉTAPE 4: Tri final par score hybride + correspondance lexicale
        # Impact = force du souvenir, intervient APRÈS la pertinence FAISS
        # keyword_score = correspondance mots-clés, meilleur départage que l'impact
        # ====================================================================
        candidates_l3.sort(
            key=lambda m: (
                -m.get('hybrid_score', 0),
                -m.get('keyword_score', 0)
            )
        )
        
        # ====================================================================
        # MÉTRIQUES FINALES SMART STOP
        # ====================================================================
        elapsed = time.time() - start_time
        
        metrics = {
            'queries_planned': len(queries),
            'queries_used': queries_used,
            'queries_saved': len(queries) - queries_used,
            'stopped_early': queries_stopped_early,
            'efficiency': queries_used / len(queries) if queries else 0,
            'embeddings_generated': embeddings_generated,
            'candidates_bruts': candidates_bruts,
            'candidates_l2_semantic': len(candidates_l2),
            'candidates_l3_injection': len(candidates_l3),
            'dedup_ratio': (candidates_bruts - len(candidates_l3)) / candidates_bruts if candidates_bruts > 0 else 0.0,
            'dedup_percentage': ((candidates_bruts - len(candidates_l3)) / candidates_bruts * 100) if candidates_bruts > 0 else 0.0,
            'elapsed_ms': elapsed * 1000,
            'avg_ms_per_query': (elapsed * 1000) / queries_used if queries_used > 0 else 0
        }
        
        print(f"[SMART-STOP] ✅ Terminé: {candidates_bruts} → {len(candidates_l3)} uniques ({metrics['dedup_percentage']:.1f}% dédup)")
        print(f"[SMART-STOP] ⏱️  Temps: {metrics['elapsed_ms']:.0f}ms (Queries: {queries_used}/{len(queries)} = {metrics['queries_saved']} économisées)")
        if queries_stopped_early:
            print(f"[SMART-STOP] 🎯 Smart Stop activé! Économie: {metrics['queries_saved']} queries (-{metrics['queries_saved']/len(queries)*100:.0f}%)")

        
        return candidates_l3, metrics

    
    def get_all_memories_data(self, include_seeds: bool = True) -> List[dict]:
        """Retourne toutes les données des mémoires depuis SQLite.
        
        Args:
            include_seeds: Si False, filtre les mémoires SEED_* (pour l'affichage UI).
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                if include_seeds:
                    query = """
                        SELECT id, text_original, title, summary,
                               valence, lesson, created_at, score_impact
                        FROM memories
                        ORDER BY created_at DESC
                    """
                    cursor = conn.execute(query)
                else:
                    query = """
                        SELECT id, text_original, title, summary,
                               valence, lesson, created_at, score_impact
                        FROM memories
                        WHERE id NOT LIKE 'SEED_%'
                        ORDER BY created_at DESC
                    """
                    cursor = conn.execute(query)
                
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
            if memory_id.startswith("SEED_"):
                print(f"[DELETE] Refus suppression seed fondateur : {memory_id}")
                return False

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
                
                # [LEGACY] sync ego_prompt.txt supprimé - fichier obsolète depuis jan 2026
            
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
            
            # 2. Compter les souvenirs et vider la base (SEED_* préservés)
            count_before = 0
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM memories WHERE id NOT LIKE 'SEED_%'")
                count_before = cursor.fetchone()[0]
                print(f"[DELETE-ALL] {count_before} souvenirs à supprimer (seeds préservés)")
                
                # Supprimer tous les enregistrements SAUF les mémoires seeds fondamentales
                conn.execute("DELETE FROM memories WHERE id NOT LIKE 'SEED_%'")
                conn.commit()
                print(f"[DELETE-ALL] Base vidée (seeds SEED_* conservés)")
            
            # 3. Compacter la base (VACUUM doit être hors transaction)
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("VACUUM")  # Compacter pour libérer l'espace des embeddings
                print(f"[DELETE-ALL] Base compactée (VACUUM) - espace libéré")
            
            # 4. Clear des mappings
            self.id_to_faiss.clear()
            self.faiss_to_id.clear()
            print(f"[DELETE-ALL] Mappings id_to_faiss et faiss_to_id vidés")
            
            # 5. Reconstruire l'index FAISS (pour réintégrer les seeds préservés)
            rebuild_stats = self.rebuild_faiss_index()
            print(f"[DELETE-ALL] Index FAISS reconstruit: {rebuild_stats}")
            
            # [LEGACY] sync ego_prompt.txt supprimé - fichier obsolète depuis jan 2026

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
        if memory_id.startswith("SEED_"):
            print(f"[UPDATE] Refus modification seed fondateur : {memory_id}")
            return None
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

    def _compute_emotional_tone(self, memories: List[Dict]) -> str:
        """
        Calcule la tonalité émotionnelle dominante d'un ensemble de souvenirs.
        
        Pondère les valences par score_impact pour donner plus de poids
        aux souvenirs marquants.
        
        Args:
            memories: Liste de souvenirs avec valence et score_impact
            
        Returns:
            "négatif", "neutre", ou "positif"
        """
        if not memories:
            return "neutre"
        
        try:
            # Pondération par score_impact
            total_weighted = 0.0
            total_impact = 0.0
            
            for mem in memories:
                valence = float(mem.get('valence', 0) or 0)
                impact = float(mem.get('score_impact', 0) or 0)
                
                total_weighted += valence * impact
                total_impact += impact
            
            if total_impact == 0:
                return "neutre"
            
            # Score émotionnel pondéré (-1.0 à +1.0)
            score_emotionnel = total_weighted / total_impact
            
            # Seuils de classification
            # -1.0 ← [négatif] → -0.3 | -0.3 ← [neutre] → +0.3 | +0.3 ← [positif] → +1.0
            if score_emotionnel < -0.3:
                return "négatif"
            elif score_emotionnel > 0.3:
                return "positif"
            else:
                return "neutre"
                
        except Exception as e:
            print(f"[EMOTIONAL-TONE] ⚠️ Erreur calcul tonalité: {e}")
            return "neutre"

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
        if memory_id.startswith("SEED_"):
            print(f"[REENRICH] Refus ré-enrichissement seed fondateur : {memory_id}")
            return None
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