"""
i2i_lessons.py - Système de leçons persistantes pour la boucle auto-corrective i2i

Stocke et récupère les leçons apprises lors des corrections d'images.
Permet à l'IA de ne pas répéter les mêmes erreurs.

Architecture: SQLite + recherche par mots-clés
Pattern: Singleton avec lazy initialization (cohérent OGMA)
"""

import sqlite3
import json
import os
import time
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime


# ═══════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════

_lessons_manager: Optional['I2ILessonsManager'] = None


def get_lessons_manager() -> 'I2ILessonsManager':
    """Lazy init du singleton lessons manager."""
    global _lessons_manager
    if _lessons_manager is None:
        _lessons_manager = I2ILessonsManager()
    return _lessons_manager


def cleanup_lessons():
    """Nettoyage propre."""
    global _lessons_manager
    if _lessons_manager:
        _lessons_manager.close()
        _lessons_manager = None


# ═══════════════════════════════════════
# MANAGER
# ═══════════════════════════════════════

class I2ILessonsManager:
    """
    Gestionnaire de leçons persistantes pour les corrections img2img.
    
    Chaque leçon contient:
    - Le type d'erreur (anatomie, proportion, artefact, etc.)
    - Le prompt original qui a causé l'erreur
    - Le prompt corrigé qui a résolu le problème
    - Le gain de score (avant/après)
    - Les mots-clés extraits pour la recherche
    - Le contexte optionnel (description de l'image, etc.)
    """
    
    DB_PATH = Path("data/memory/i2i_lessons.db")
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or self.DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
        self._init_db()
    
    def _get_conn(self) -> sqlite3.Connection:
        """Connexion lazy avec row_factory."""
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.row_factory = sqlite3.Row
            # Activer WAL mode pour performances
            self._conn.execute("PRAGMA journal_mode=WAL")
        return self._conn
    
    def _init_db(self):
        """Crée les tables si nécessaire."""
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS lessons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                error_type TEXT NOT NULL,
                severity TEXT DEFAULT 'majeur',
                original_prompt TEXT NOT NULL,
                corrected_prompt TEXT NOT NULL,
                score_before INTEGER NOT NULL,
                score_after INTEGER NOT NULL,
                score_gain INTEGER GENERATED ALWAYS AS (score_after - score_before) STORED,
                defects_json TEXT,
                keywords TEXT NOT NULL,
                context TEXT,
                times_applied INTEGER DEFAULT 0,
                last_applied_at TEXT
            );
            
            CREATE INDEX IF NOT EXISTS idx_lessons_error_type ON lessons(error_type);
            CREATE INDEX IF NOT EXISTS idx_lessons_keywords ON lessons(keywords);
            CREATE INDEX IF NOT EXISTS idx_lessons_score_gain ON lessons(score_gain DESC);
            
            CREATE TABLE IF NOT EXISTS lesson_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                updated_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                total_corrections INTEGER DEFAULT 0,
                total_improvements INTEGER DEFAULT 0,
                avg_score_gain REAL DEFAULT 0.0,
                most_common_error TEXT,
                most_effective_fix TEXT
            );
            
            CREATE TABLE IF NOT EXISTS guide_proposals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                status TEXT NOT NULL DEFAULT 'pending',
                proposal_text TEXT NOT NULL,
                reason TEXT NOT NULL,
                based_on_lessons TEXT,
                current_guide_snapshot TEXT,
                applied_at TEXT
            );
            
            CREATE INDEX IF NOT EXISTS idx_guide_proposals_status ON guide_proposals(status);
        """)
        conn.commit()
        
        # Migration: ajouter colonne 'source' si elle n'existe pas
        try:
            cols = [row[1] for row in conn.execute("PRAGMA table_info(lessons)").fetchall()]
            if 'source' not in cols:
                conn.execute("ALTER TABLE lessons ADD COLUMN source TEXT DEFAULT 'correction'")
                conn.commit()
                print("[I2I-LESSONS] Migration: colonne 'source' ajoutee")
        except Exception as mig_err:
            print(f"[I2I-LESSONS] Migration source: {mig_err}")
        
        print(f"[I2I-LESSONS] DB initialisee: {self.db_path}")
    
    # ─── ÉCRITURE ─────────────────────────
    
    def store_lesson(
        self,
        error_type: str,
        severity: str,
        original_prompt: str,
        corrected_prompt: str,
        score_before: int,
        score_after: int,
        defects: Optional[List[Dict]] = None,
        context: Optional[str] = None,
        source: str = "correction"
    ) -> int:
        """
        Stocke une nouvelle leçon apprise.
        
        Args:
            error_type: Type d'erreur (anatomie, proportion, artefact, etc.)
            severity: Gravité (critique, majeur, mineur)
            original_prompt: Prompt qui a causé l'erreur
            corrected_prompt: Prompt corrigé qui a amélioré le score
            score_before: Score avant correction
            score_after: Score après correction
            defects: Liste des défauts détectés (JSON)
            context: Contexte optionnel
            source: Origine de la lecon ('correction', 'web_tips', 'manual')
        
        Returns:
            ID de la leçon créée
        """
        # Extraire les mots-clés du prompt et des défauts
        keywords = self._extract_keywords(original_prompt, corrected_prompt, defects)
        
        conn = self._get_conn()
        cursor = conn.execute("""
            INSERT INTO lessons (error_type, severity, original_prompt, corrected_prompt,
                                 score_before, score_after, defects_json, keywords, context, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            error_type,
            severity,
            original_prompt,
            corrected_prompt,
            score_before,
            score_after,
            json.dumps(defects, ensure_ascii=False) if defects else None,
            keywords,
            context,
            source
        ))
        conn.commit()
        
        lesson_id = cursor.lastrowid
        gain = score_after - score_before
        print(f"[I2I-LESSONS] Lecon #{lesson_id} stockee: {error_type} ({severity}), gain +{gain}")
        
        # Mettre à jour les stats
        self._update_stats()
        
        return lesson_id
    
    def store_lessons_from_correction(self, analysis_history: List[Dict], prompt_history: List[str]) -> List[int]:
        """
        Extrait et stocke les leçons d'une session de correction complète.
        
        Args:
            analysis_history: Liste des analyses par tentative
            prompt_history: Liste des prompts par tentative
        
        Returns:
            Liste des IDs de leçons créées
        """
        lesson_ids = []
        
        if len(analysis_history) < 2:
            # Pas assez de données pour une leçon (1 seule tentative)
            return lesson_ids
        
        for i in range(len(analysis_history) - 1):
            current = analysis_history[i]
            next_attempt = analysis_history[i + 1]
            
            score_before = current.get('score', 5)
            score_after = next_attempt.get('score', 5)
            
            # Ne stocker que si amélioration (score gain > 0)
            if score_after <= score_before:
                continue
            
            defects = current.get('defauts_detectes', [])
            
            # Déterminer le type d'erreur principal
            if defects:
                # Prendre le défaut le plus grave
                severity_order = {'critique': 3, 'majeur': 2, 'mineur': 1}
                sorted_defects = sorted(
                    defects,
                    key=lambda d: severity_order.get(d.get('gravite', 'mineur'), 0),
                    reverse=True
                )
                main_defect = sorted_defects[0]
                error_type = main_defect.get('type', 'inconnu')
                severity = main_defect.get('gravite', 'majeur')
            else:
                error_type = 'general'
                severity = 'mineur'
            
            # Prompts correspondants
            original_prompt = prompt_history[i] if i < len(prompt_history) else current.get('prompt', '')
            corrected_prompt = prompt_history[i + 1] if i + 1 < len(prompt_history) else next_attempt.get('prompt', '')
            
            lesson_id = self.store_lesson(
                error_type=error_type,
                severity=severity,
                original_prompt=original_prompt,
                corrected_prompt=corrected_prompt,
                score_before=score_before,
                score_after=score_after,
                defects=defects,
                context=f"Tentative {i+1} -> {i+2}"
            )
            lesson_ids.append(lesson_id)
        
        if lesson_ids:
            print(f"[I2I-LESSONS] {len(lesson_ids)} lecon(s) extraite(s) de la session")
        
        return lesson_ids
    
    # ─── LECTURE ──────────────────────────
    
    def find_relevant_lessons(
        self,
        prompt: str,
        max_results: int = 5,
        min_score_gain: int = 1
    ) -> List[Dict]:
        """
        Recherche les leçons pertinentes pour un prompt donné.
        Utilise la correspondance par mots-clés.
        
        Args:
            prompt: Le prompt de modification actuel
            max_results: Nombre max de leçons à retourner
            min_score_gain: Gain minimum de score pour considérer une leçon
        
        Returns:
            Liste de leçons triées par pertinence (score_gain desc)
        """
        # Extraire les mots-clés du prompt
        prompt_keywords = set(self._tokenize(prompt))
        
        if not prompt_keywords:
            return []
        
        conn = self._get_conn()
        
        # Récupérer toutes les leçons avec gain positif
        rows = conn.execute("""
            SELECT * FROM lessons
            WHERE score_gain >= ?
            ORDER BY score_gain DESC, created_at DESC
        """, (min_score_gain,)).fetchall()
        
        # Scorer la pertinence par overlap de mots-clés
        scored = []
        for row in rows:
            lesson_keywords = set(row['keywords'].split(','))
            overlap = prompt_keywords & lesson_keywords
            
            if overlap:
                relevance = len(overlap) / max(len(prompt_keywords), 1)
                scored.append({
                    'id': row['id'],
                    'error_type': row['error_type'],
                    'severity': row['severity'],
                    'original_prompt': row['original_prompt'],
                    'corrected_prompt': row['corrected_prompt'],
                    'score_before': row['score_before'],
                    'score_after': row['score_after'],
                    'score_gain': row['score_gain'],
                    'defects': json.loads(row['defects_json']) if row['defects_json'] else [],
                    'keywords_overlap': list(overlap),
                    'relevance': relevance,
                    'times_applied': row['times_applied'],
                    'created_at': row['created_at']
                })
        
        # Trier par pertinence * score_gain
        scored.sort(key=lambda x: x['relevance'] * x['score_gain'], reverse=True)
        
        return scored[:max_results]
    
    def format_lessons_for_injection(self, lessons: List[Dict], max_chars: int = 800) -> str:
        """
        Formate les leçons pertinentes pour injection dans le contexte de l'IA.
        
        Args:
            lessons: Liste de leçons (de find_relevant_lessons)
            max_chars: Limite de caractères
        
        Returns:
            Texte formaté pour injection
        """
        if not lessons:
            return ""
        
        parts = ["LEÇONS APPRISES (erreurs passées à éviter):"]
        current_len = len(parts[0])
        
        for i, lesson in enumerate(lessons):
            entry = (
                f"\n- [{lesson['error_type'].upper()}] "
                f"Erreur: {lesson.get('defects', [{}])[0].get('description', 'N/A') if lesson.get('defects') else 'N/A'} "
                f"→ Fix: ajout de contraintes dans le prompt (gain +{lesson['score_gain']})"
            )
            
            if current_len + len(entry) > max_chars:
                break
            
            parts.append(entry)
            current_len += len(entry)
        
        return "".join(parts)
    
    def get_error_stats(self) -> Dict:
        """Retourne les statistiques d'erreurs."""
        conn = self._get_conn()
        
        total = conn.execute("SELECT COUNT(*) FROM lessons").fetchone()[0]
        
        if total == 0:
            return {
                'total_lessons': 0,
                'avg_score_gain': 0,
                'error_types': {},
                'most_common_error': None,
                'best_fix_gain': 0
            }
        
        avg_gain = conn.execute("SELECT AVG(score_gain) FROM lessons").fetchone()[0] or 0
        best_gain = conn.execute("SELECT MAX(score_gain) FROM lessons").fetchone()[0] or 0
        
        # Erreurs par type
        type_rows = conn.execute("""
            SELECT error_type, COUNT(*) as count, AVG(score_gain) as avg_gain
            FROM lessons GROUP BY error_type ORDER BY count DESC
        """).fetchall()
        
        error_types = {
            row['error_type']: {'count': row['count'], 'avg_gain': round(row['avg_gain'], 1)}
            for row in type_rows
        }
        
        most_common = type_rows[0]['error_type'] if type_rows else None
        
        return {
            'total_lessons': total,
            'avg_score_gain': round(avg_gain, 1),
            'error_types': error_types,
            'most_common_error': most_common,
            'best_fix_gain': best_gain
        }
    
    def mark_lesson_applied(self, lesson_id: int):
        """Marque une leçon comme appliquée (pour suivi d'usage)."""
        conn = self._get_conn()
        conn.execute("""
            UPDATE lessons 
            SET times_applied = times_applied + 1,
                last_applied_at = datetime('now', 'localtime')
            WHERE id = ?
        """, (lesson_id,))
        conn.commit()
    
    # ─── HELPERS ──────────────────────────
    
    def _extract_keywords(
        self,
        original_prompt: str,
        corrected_prompt: str,
        defects: Optional[List[Dict]] = None
    ) -> str:
        """Extrait les mots-clés pertinents pour la recherche."""
        text = f"{original_prompt} {corrected_prompt}"
        
        if defects:
            for d in defects:
                text += f" {d.get('type', '')} {d.get('description', '')} {d.get('zone', '')}"
        
        tokens = self._tokenize(text)
        return ",".join(tokens)
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenise un texte en mots-clés significatifs (> 3 chars, lowercase)."""
        import re
        # Nettoyer et tokeniser
        words = re.findall(r'[a-zA-ZÀ-ÿ]{4,}', text.lower())
        
        # Stop words basiques
        stop_words = {
            'with', 'from', 'this', 'that', 'have', 'been', 'will', 'would',
            'could', 'should', 'their', 'there', 'these', 'those', 'about',
            'dans', 'avec', 'pour', 'cette', 'sont', 'plus', 'mais', 'aussi',
            'image', 'prompt', 'original', 'correction', 'modifier', 'ajouter',
        }
        
        return list(set(w for w in words if w not in stop_words))
    
    def _update_stats(self):
        """Met à jour les statistiques agrégées."""
        try:
            conn = self._get_conn()
            stats = self.get_error_stats()
            
            conn.execute("""
                INSERT INTO lesson_stats (total_corrections, total_improvements, avg_score_gain, most_common_error)
                VALUES (?, ?, ?, ?)
            """, (
                stats['total_lessons'],
                stats['total_lessons'],  # Toutes les leçons sont des améliorations (gain > 0)
                stats['avg_score_gain'],
                stats['most_common_error']
            ))
            conn.commit()
        except Exception as e:
            print(f"[I2I-LESSONS] Erreur update stats: {e}")
    
    # ─── TIPS WEB PAR MODELE ──────────────────────────
    
    def has_web_tips_for_model(self, model_name: str) -> bool:
        """Verifie si des tips web existent deja pour ce modele."""
        conn = self._get_conn()
        count = conn.execute(
            "SELECT COUNT(*) FROM lessons WHERE source = 'web_tips' AND context LIKE ?",
            (f"%model:{model_name}%",)
        ).fetchone()[0]
        return count > 0
    
    async def fetch_model_tips(self, model_name: str, provider: str = "", chat_controller=None) -> dict:
        """
        Recherche web unique pour recuperer des tips de prompt engineering
        specifiques au modele img2img configure. Stocke les resultats comme lecons.
        
        Appele UNE SEULE FOIS par modele (cache dans la DB via source='web_tips').
        
        Args:
            model_name: Nom du modele (ex: 'bytedance/seedream-v4.5/edit')
            provider: Provider (ex: 'Kie', 'Seedream')
            chat_controller: Controleur IA pour synthetiser les resultats
        
        Returns:
            dict {success, tips_count, error}
        """
        # Verifier le cache
        if self.has_web_tips_for_model(model_name):
            cached = self._get_conn().execute(
                "SELECT COUNT(*) FROM lessons WHERE source = 'web_tips' AND context LIKE ?",
                (f"%model:{model_name}%",)
            ).fetchone()[0]
            print(f"[I2I-TIPS] {cached} tips deja en cache pour {model_name}")
            return {'success': True, 'tips_count': cached, 'error': None, 'cached': True}
        
        print(f"[I2I-TIPS] Recherche web de tips pour: {model_name} ({provider})")
        
        # Extraire un nom court pour la recherche
        short_name = model_name.split('/')[-1] if '/' in model_name else model_name
        
        # Construire la requete de recherche
        search_queries = [
            f"{short_name} img2img prompt engineering tips best practices",
            f"{short_name} image editing prompt guide avoid artifacts",
        ]
        
        try:
            from extensions.web_navigator import SerperClient, WebNavigatorConfig
            config = WebNavigatorConfig()
            
            if not config.has_valid_api_key():
                print("[I2I-TIPS] Pas de cle API Serper - skip recherche web")
                return {'success': False, 'tips_count': 0, 'error': 'Pas de cle API Serper', 'cached': False}
            
            serper = SerperClient(config)
            
            all_content = []
            for query in search_queries:
                try:
                    content, err = await serper.search_with_intelligent_scraping(query, top_pages=3)
                    if content and not err:
                        all_content.append(content)
                        print(f"[I2I-TIPS] Contenu recupere pour: {query[:50]}...")
                    else:
                        print(f"[I2I-TIPS] Echec recherche: {err}")
                except Exception as search_err:
                    print(f"[I2I-TIPS] Exception recherche: {search_err}")
            
            if not all_content:
                return {'success': False, 'tips_count': 0, 'error': 'Aucun contenu web recupere', 'cached': False}
            
            # Synthetiser avec l'IA
            if not chat_controller:
                print("[I2I-TIPS] Pas de chat_controller pour synthetiser")
                return {'success': False, 'tips_count': 0, 'error': 'Chat controller requis', 'cached': False}
            
            combined_content = "\n\n---\n\n".join(all_content)[:8000]  # Limiter
            
            synthesis_prompt = f"""Tu es experte en prompt engineering pour modeles de generation/modification d'images.

Voici du contenu web a propos du modele "{model_name}" ({provider}):

{combined_content}

EXTRAIS exactement 5 a 10 conseils CONCRETS et ACTIONABLES pour ecrire de meilleurs prompts img2img avec ce modele.

Format STRICT (un conseil par ligne, JSON array):
[
  {{{{
    "type": "anatomie|proportion|style|negative|structure|qualite",
    "conseil": "Description courte du conseil (1 phrase)",
    "exemple_prompt": "Fragment de prompt illustrant ce conseil",
    "severite": "critique|majeur|mineur"
  }}}}
]

Retourne UNIQUEMENT le JSON array, sans texte avant/apres."""
            
            response, error = await chat_controller.call_chat_api(
                messages=[{'role': 'user', 'content': synthesis_prompt}],
                max_tokens=2000,
                context_length=16384,
                temperature=0.3,
                is_json=True
            )
            
            if error or not response:
                print(f"[I2I-TIPS] Erreur synthese IA: {error}")
                return {'success': False, 'tips_count': 0, 'error': f'Erreur synthese: {error}', 'cached': False}
            
            # Parser les tips
            try:
                tips = json.loads(response)
                if not isinstance(tips, list):
                    tips = [tips]
            except json.JSONDecodeError:
                # Tenter extraction JSON dans le texte
                import re
                match = re.search(r'\[.*\]', response, re.DOTALL)
                if match:
                    tips = json.loads(match.group())
                else:
                    print(f"[I2I-TIPS] JSON invalide dans la reponse IA")
                    return {'success': False, 'tips_count': 0, 'error': 'Reponse IA non-JSON', 'cached': False}
            
            # Stocker chaque tip comme lecon
            stored = 0
            for tip in tips[:10]:  # Max 10 tips
                try:
                    conseil = tip.get('conseil', '')
                    exemple = tip.get('exemple_prompt', '')
                    tip_type = tip.get('type', 'style')
                    tip_severity = tip.get('severite', 'mineur')
                    
                    if not conseil:
                        continue
                    
                    self.store_lesson(
                        error_type=f"web_tip_{tip_type}",
                        severity=tip_severity,
                        original_prompt=f"[TIP] {conseil}",
                        corrected_prompt=exemple if exemple else conseil,
                        score_before=0,
                        score_after=5,  # Gain virtuel pour que la lecon soit retrouvee
                        defects=[{'type': tip_type, 'description': conseil, 'zone': 'general', 'gravite': tip_severity}],
                        context=f"model:{model_name}|provider:{provider}|source_url:web_search",
                        source="web_tips"
                    )
                    stored += 1
                except Exception as store_err:
                    print(f"[I2I-TIPS] Erreur stockage tip: {store_err}")
            
            print(f"[I2I-TIPS] {stored} tips stockes pour {model_name}")
            return {'success': True, 'tips_count': stored, 'error': None, 'cached': False}
        
        except ImportError:
            print("[I2I-TIPS] Extension web_navigator non disponible")
            return {'success': False, 'tips_count': 0, 'error': 'Web navigator non disponible', 'cached': False}
        except Exception as e:
            print(f"[I2I-TIPS] Exception: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'tips_count': 0, 'error': str(e), 'cached': False}
    
    def get_web_tips_for_model(self, model_name: str) -> List[Dict]:
        """Recupere les tips web caches pour un modele."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT * FROM lessons WHERE source = 'web_tips' AND context LIKE ? ORDER BY created_at DESC",
            (f"%model:{model_name}%",)
        ).fetchall()
        return [
            {
                'id': r['id'],
                'type': r['error_type'],
                'conseil': r['original_prompt'].replace('[TIP] ', ''),
                'exemple': r['corrected_prompt'],
                'severity': r['severity']
            }
            for r in rows
        ]
    
    def close(self):
        """Ferme la connexion."""
        if self._conn:
            self._conn.close()
            self._conn = None
            print("[I2I-LESSONS] Connexion fermee")
    
    # ─── PROPOSITIONS DE MODIFICATION DU GUIDE ───
    
    def should_propose_guide_update(self, min_lessons: int = 5) -> bool:
        """
        Vérifie si assez de leçons ont été accumulées pour proposer une mise à jour du guide.
        
        Conditions:
        - Au moins min_lessons leçons avec gain > 0
        - Au moins 1 type d'erreur récurrent (>= 2 occurrences)
        - Pas de proposition 'pending' existante
        """
        conn = self._get_conn()
        
        # Vérifier pas de proposition en attente
        pending = conn.execute(
            "SELECT COUNT(*) FROM guide_proposals WHERE status = 'pending'"
        ).fetchone()[0]
        if pending > 0:
            return False
        
        # Vérifier nombre de leçons
        total = conn.execute("SELECT COUNT(*) FROM lessons").fetchone()[0]
        if total < min_lessons:
            return False
        
        # Vérifier erreurs récurrentes
        recurrent = conn.execute("""
            SELECT error_type, COUNT(*) as cnt FROM lessons 
            GROUP BY error_type HAVING cnt >= 2
        """).fetchall()
        
        return len(recurrent) > 0
    
    def get_lessons_summary_for_guide(self) -> str:
        """
        Génère un résumé structuré des leçons pour alimenter la proposition de guide.
        """
        conn = self._get_conn()
        
        # Top erreurs récurrentes
        recurrent = conn.execute("""
            SELECT error_type, severity, COUNT(*) as cnt, AVG(score_gain) as avg_gain,
                   GROUP_CONCAT(DISTINCT original_prompt) as examples
            FROM lessons 
            GROUP BY error_type 
            ORDER BY cnt DESC
            LIMIT 5
        """).fetchall()
        
        if not recurrent:
            return ""
        
        summary_parts = []
        for row in recurrent:
            examples = row['examples'][:200] if row['examples'] else 'N/A'
            summary_parts.append(
                f"- {row['error_type'].upper()} ({row['cnt']}x, gain moyen +{row['avg_gain']:.1f}): {examples}"
            )
        
        # Corrections les plus efficaces
        best_fixes = conn.execute("""
            SELECT error_type, corrected_prompt, score_gain
            FROM lessons 
            ORDER BY score_gain DESC
            LIMIT 3
        """).fetchall()
        
        fix_parts = []
        for row in best_fixes:
            fix_parts.append(
                f"- [{row['error_type']}] +{row['score_gain']}: \"{row['corrected_prompt'][:100]}\""
            )
        
        return (
            f"ERREURS RÉCURRENTES:\n" + "\n".join(summary_parts) +
            f"\n\nMEILLEURES CORRECTIONS:\n" + "\n".join(fix_parts)
        )
    
    async def generate_guide_proposal(self, chat_controller, current_guide: str) -> Optional[Dict]:
        """
        Demande à l'IA principale de proposer une mise à jour du guide img2img
        basée sur les leçons accumulées.
        
        Args:
            chat_controller: Contrôleur IA principale
            current_guide: Le guide actuel depuis settings.json
        
        Returns:
            Dict avec 'proposal_text', 'reason', 'lesson_ids' ou None
        """
        if not self.should_propose_guide_update():
            return None
        
        lessons_summary = self.get_lessons_summary_for_guide()
        if not lessons_summary:
            return None
        
        proposal_prompt = f"""Tu es experte en guides de modification d'image (img2img).
Analyse les erreurs récurrentes ci-dessous et propose des AJOUTS au guide existant.

GUIDE ACTUEL:
{current_guide[:2000]}

{lessons_summary}

MISSION: Propose des règles ADDITIONNELLES à ajouter au guide pour prévenir ces erreurs.

CONTEXTE CRITIQUE:
Ce guide est LU PAR TOI-MÊME (l'IA) à chaque génération img2img. Tu écris des instructions pour toi.
Tu dois te comprendre même sans mémoire des conversations passées — chaque règle doit être autonome.

CONTRAINTES DE RÉDACTION:
- Imite exactement le style du GUIDE ACTUEL : mêmes patterns (ATTENTION:, ✅, ⚠️, ❌), mêmes verbes impératifs (garde, supprime, change), mêmes TAGS en anglais technique
- Chaque règle = une instruction précise que tu peux appliquer sans contexte supplémentaire
- Inclus le POURQUOI en 3-5 mots si la règle n'est pas évidente (ex: "sinon le visage disparaît")
- Maximum 5 nouvelles règles, concises (1-2 lignes chacune)
- Ne modifie PAS les règles existantes du guide
- Français sauf termes techniques anglais

Réponds en JSON:
{{"raison": "<justification concise 1-2 phrases>", "nouvelles_regles": ["<règle 1>", "<règle 2>", ...]}}"""
        
        try:
            response, error = await chat_controller.call_chat_api(
                messages=[{'role': 'user', 'content': proposal_prompt}],
                max_tokens=800,
                temperature=0.3,
                is_json=True
            )
            
            if not response or error:
                print(f"[I2I-GUIDE] Erreur generation proposition: {error}")
                return None
            
            # Parser la réponse
            try:
                data = json.loads(response)
            except json.JSONDecodeError:
                # Tenter extraction JSON
                import re
                json_match = re.search(r'\{[^{}]+\}', response, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                else:
                    print(f"[I2I-GUIDE] Impossible de parser la proposition")
                    return None
            
            raison = data.get('raison', 'Basé sur les erreurs récurrentes')
            nouvelles_regles = data.get('nouvelles_regles', [])
            
            if not nouvelles_regles:
                return None
            
            # Formater le texte de proposition
            proposal_text = "\n".join(f"- {r}" for r in nouvelles_regles)
            
            # Stocker en DB
            conn = self._get_conn()
            
            # IDs des leçons utilisées
            lesson_rows = conn.execute("SELECT id FROM lessons ORDER BY created_at DESC LIMIT 10").fetchall()
            lesson_ids = [r['id'] for r in lesson_rows]
            
            cursor = conn.execute("""
                INSERT INTO guide_proposals (status, proposal_text, reason, based_on_lessons, current_guide_snapshot)
                VALUES ('pending', ?, ?, ?, ?)
            """, (
                proposal_text,
                raison,
                json.dumps(lesson_ids),
                current_guide[:3000]
            ))
            conn.commit()
            
            proposal_id = cursor.lastrowid
            print(f"[I2I-GUIDE] Proposition #{proposal_id} creee: {len(nouvelles_regles)} regles")
            
            return {
                'id': proposal_id,
                'proposal_text': proposal_text,
                'reason': raison,
                'nouvelles_regles': nouvelles_regles,
                'lesson_ids': lesson_ids
            }
            
        except Exception as e:
            print(f"[I2I-GUIDE] Exception generation proposition: {e}")
            return None
    
    def get_pending_proposals(self) -> List[Dict]:
        """Retourne les propositions en attente d'approbation."""
        conn = self._get_conn()
        rows = conn.execute("""
            SELECT * FROM guide_proposals WHERE status = 'pending'
            ORDER BY created_at DESC
        """).fetchall()
        
        return [{
            'id': r['id'],
            'created_at': r['created_at'],
            'proposal_text': r['proposal_text'],
            'reason': r['reason'],
            'based_on_lessons': json.loads(r['based_on_lessons']) if r['based_on_lessons'] else []
        } for r in rows]
    
    def approve_proposal(self, proposal_id: int) -> Optional[str]:
        """
        Approuve une proposition et retourne le texte à ajouter au guide.
        
        Returns:
            Le texte de la proposition approuvée, ou None si introuvable
        """
        conn = self._get_conn()
        row = conn.execute(
            "SELECT proposal_text FROM guide_proposals WHERE id = ? AND status = 'pending'",
            (proposal_id,)
        ).fetchone()
        
        if not row:
            return None
        
        conn.execute("""
            UPDATE guide_proposals 
            SET status = 'approved', applied_at = datetime('now', 'localtime')
            WHERE id = ?
        """, (proposal_id,))
        conn.commit()
        
        print(f"[I2I-GUIDE] Proposition #{proposal_id} APPROUVEE")
        return row['proposal_text']
    
    def reject_proposal(self, proposal_id: int) -> bool:
        """Rejette une proposition."""
        conn = self._get_conn()
        conn.execute(
            "UPDATE guide_proposals SET status = 'rejected' WHERE id = ? AND status = 'pending'",
            (proposal_id,)
        )
        conn.commit()
        print(f"[I2I-GUIDE] Proposition #{proposal_id} REJETEE")
        return True
    
    def apply_proposal_to_guide(self, proposal_id: int, settings_manager) -> Optional[str]:
        """
        Approuve une proposition ET l'applique directement au guide dans settings.json.
        Conserve un snapshot de l'ancien guide dans la table guide_proposals.
        
        Args:
            proposal_id: ID de la proposition
            settings_manager: SettingsManager pour modifier settings.json
        
        Returns:
            Le nouveau guide complet, ou None si échec
        """
        proposal_text = self.approve_proposal(proposal_id)
        if not proposal_text:
            return None
        
        try:
            img_config = settings_manager.settings.get('image_generation', {})
            current_guide = img_config.get('img2img_guide', '')
            
            # Ajouter les nouvelles règles à la fin du guide existant
            separator = "\n\n# --- RÈGLES AUTO-APPRISES (leçons i2i) ---\n"
            
            # Vérifier si la section existe déjà
            if separator.strip() in current_guide:
                # Ajouter après la section existante
                new_guide = current_guide + "\n" + proposal_text
            else:
                # Créer la section
                new_guide = current_guide + separator + proposal_text
            
            # Sauvegarder dans settings
            img_config['img2img_guide'] = new_guide
            settings_manager.settings['image_generation'] = img_config
            settings_manager.save_settings()
            
            print(f"[I2I-GUIDE] Guide mis a jour (+{len(proposal_text)} chars)")
            return new_guide
            
        except Exception as e:
            print(f"[I2I-GUIDE] Erreur application proposition: {e}")
            return None
    
    def get_guide_history(self) -> List[Dict]:
        """Retourne l'historique des modifications du guide."""
        conn = self._get_conn()
        rows = conn.execute("""
            SELECT id, created_at, status, reason, applied_at
            FROM guide_proposals
            ORDER BY created_at DESC
            LIMIT 20
        """).fetchall()
        
        return [{
            'id': r['id'],
            'created_at': r['created_at'],
            'status': r['status'],
            'reason': r['reason'],
            'applied_at': r['applied_at']
        } for r in rows]


# ═══════════════════════════════════════
# RESTRUCTURATION GUIDE I2I (PHRASE MAGIQUE)
# ═══════════════════════════════════════

async def restructure_i2i_guide(chat_controller, settings_manager, conversation_context: str = "") -> dict:
    """
    Restructure le guide i2i en integrant toutes les lecons apprises.
    Declenchee par la phrase magique "enrichis ton instruction d'image".
    
    L'IA recoit le guide actuel + toutes les lecons + contexte conversation
    et produit un guide NEUF, optimise et restructure.
    
    Returns:
        dict: {success: bool, new_guide: str, lessons_used: int, error: str}
    """
    try:
        mgr = get_lessons_manager()
        
        # Charger TOUTES les lecons (pas juste les pertinentes)
        conn = mgr._get_conn()
        conn.row_factory = sqlite3.Row  # Permet d'accéder aux colonnes par nom
        rows = conn.execute("""
            SELECT error_type, severity, corrected_prompt, score_gain, defects_json
            FROM lessons
            ORDER BY score_gain DESC, created_at DESC
            LIMIT 30
        """).fetchall()
        
        if not rows:
            return {'success': False, 'new_guide': '', 'lessons_used': 0, 
                    'error': 'Aucune lecon enregistree. Utilise d\'abord la boucle auto-corrective.'}
        
        # Formater les lecons
        lessons_text = "\n".join(
            f"- [{r['severity']}] {r['error_type']}: {(r['defects_json'] or '')[:120]}"
            + (f" | Correction: {r['corrected_prompt'][:80]}" if r['corrected_prompt'] else "")
            + f" (gain: +{r['score_gain']})"
            for r in rows
        )
        
        # Charger les stats d'erreurs recurrentes (groupees par type)
        stats_rows = conn.execute("""
            SELECT error_type, COUNT(*) as occurrences, AVG(score_gain) as avg_gain
            FROM lessons
            GROUP BY error_type
            HAVING occurrences >= 2
            ORDER BY occurrences DESC
            LIMIT 10
        """).fetchall()
        
        stats_text = ""
        if stats_rows:
            stats_text = "\nERREURS RECURRENTES (par frequence):\n" + "\n".join(
                f"- {r['error_type']}: {r['occurrences']}x (gain moyen: +{r['avg_gain']:.1f})"
                for r in stats_rows
            )
        
        # Charger le guide actuel
        img_config = settings_manager.settings.get('image_generation', {})
        current_guide = img_config.get('img2img_guide', '').strip()
        
        if not current_guide:
            return {'success': False, 'new_guide': '', 'lessons_used': 0,
                    'error': 'Guide i2i actuel vide. Configure-le d\'abord dans Parametres > Image.'}
        
        # Construire le prompt de restructuration
        restructure_prompt = f"""Tu dois REECRIRE et OPTIMISER ton propre guide d'instruction img2img.
Ce guide est LU PAR TOI-MEME a chaque generation img2img. Tu ecris pour toi.
Chaque regle doit etre autonome et comprehensible meme sans memoire des conversations passees.

GUIDE ACTUEL (a restructurer):
{current_guide}

LECONS APPRISES (erreurs detectees lors de tes generations precedentes):
{lessons_text}
{stats_text}

{f'CONTEXTE DE LA CONVERSATION EN COURS:{chr(10)}{conversation_context[:1000]}' if conversation_context else ''}

MISSION: Produis un guide REECRIT et AMELIORE qui:
1. Conserve TOUTES les regles existantes qui fonctionnent (ne perds rien)
2. INTEGRE les lecons apprises comme nouvelles regles permanentes
3. FUSIONNE les regles redondantes ou contradictoires
4. RESTRUCTURE pour une lecture claire et hierarchisee
5. PRIORISE les erreurs les plus frequentes en haut

CONTRAINTES:
- Garde exactement le meme style, ton et format que le guide actuel (ATTENTION:, emojis, verbes imperatifs)
- Chaque regle = une instruction precise que tu peux appliquer sans contexte supplementaire
- Inclus le POURQUOI en quelques mots si la regle n'est pas evidente
- Francais sauf termes techniques anglais
- Pas de preambule, pas d'explication — retourne DIRECTEMENT le guide restructure

GUIDE RESTRUCTURE:"""

        response, error = await chat_controller.call_chat_api(
            messages=[{'role': 'user', 'content': restructure_prompt}],
            max_tokens=3000,
            context_length=16384,
            temperature=0.3,
            is_json=False
        )
        
        if not response or error:
            return {'success': False, 'new_guide': '', 'lessons_used': len(rows),
                    'error': f'Erreur LLM: {error}'}
        
        new_guide = response.strip()
        
        # Sauvegarder en versionnant l'ancien
        old_guide = current_guide
        img_config['img2img_guide'] = new_guide
        settings_manager.settings['image_generation'] = img_config
        settings_manager.save_settings()
        
        # Log dans guide_proposals comme historique
        try:
            conn.execute("""
                INSERT INTO guide_proposals 
                (lesson_ids, current_guide_snapshot, proposal_text, reason, status)
                VALUES (?, ?, ?, ?, 'approved')
            """, (
                json.dumps([r['type_erreur'] for r in rows]),
                old_guide,
                new_guide,
                f"Restructuration complete via phrase magique ({len(rows)} lecons integrees)"
            ))
            conn.commit()
        except Exception as log_err:
            print(f"[I2I-RESTRUCTURE] Erreur log historique: {log_err}")
        
        print(f"[I2I-RESTRUCTURE] Guide restructure: {len(old_guide)} -> {len(new_guide)} chars, {len(rows)} lecons integrees")
        
        return {
            'success': True,
            'new_guide': new_guide,
            'lessons_used': len(rows),
            'error': None
        }
        
    except Exception as e:
        print(f"[I2I-RESTRUCTURE] Exception: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'new_guide': '', 'lessons_used': 0, 'error': str(e)}