"""
Gestionnaire principal de l'extension Biographie Profil
======================================================

Gère la logique métier pour:
- Détection des noms d'utilisateurs
- Volume 1: Filtrage FAISS par utilisateur  
- Volume 2: Biographies narratives (NOUVEAU: Architecture JSON structurée)
- Gestion des fichiers et backups
"""

import re
import json
import sqlite3
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Import du parser JSON robuste
try:
    from utils.json_cleaner import safe_json_parse
except ImportError:
    # Fallback si le module n'est pas trouvé
    def safe_json_parse(response, fallback=None):
        if fallback is None:
            fallback = {}
        try:
            cleaned = response.strip()
            if cleaned.startswith('```'):
                lines = cleaned.split('\n')
                if len(lines) > 2:
                    cleaned = '\n'.join(lines[1:-1])
                cleaned = cleaned.replace('```json', '').replace('```', '').strip()
            return json.loads(cleaned)
        except:
            return fallback


# ── Instruction journal par défaut (éditable via l'interface Biographie Profil) ─────
JOURNAL_INSTRUCTION_DEFAULT = """
SECTIONS DU JOURNAL (dans cet ordre, toutes obligatoires) :
## 🎭 Portrait général
## 🧠 Psyché & vie émotionnelle
## 💡 Vie intellectuelle
## 🚀 Projets & créations
## ☀️ Vie quotidienne & habitudes
## 👥 Relations & entourage
## 📜 Histoire personnelle
## ⚖️ Valeurs & convictions
## 🌿 Physique & présence
## 🎨 Goûts & préférences

RÈGLES RÉDACTIONNELLES :
- Écris UNIQUEMENT ce qui est soutenu par un fait fourni
- Section sans fait correspondant → écris exactement : Aucune donnée observée.
- ZÉRO psychologie clinique, ZÉRO MBTI, ZÉRO QI sauf si l'utilisateur l'a dit lui-même
- ZÉRO inférence, ZÉRO extrapolation au-delà des faits
- Utilise "il semble que" ou "d'après ses échanges" quand tu synthétises plusieurs faits
- Tu peux ajouter des sections supplémentaires si les faits le justifient
- Toutes les sections ci-dessus doivent TOUJOURS être présentes dans le journal
""".strip()

JOURNAL_INSTRUCTION_DEFAULT_EN = """
JOURNAL SECTIONS (in this order, all mandatory):
## 🎭 General portrait
## 🧠 Psyche & emotional life
## 💡 Intellectual life
## 🚀 Projects & creations
## ☀️ Daily life & habits
## 👥 Relationships & entourage
## 📜 Personal history
## ⚖️ Values & convictions
## 🌿 Physical presence
## 🎨 Tastes & preferences

EDITORIAL RULES:
- Write ONLY what is supported by a provided fact
- Section with no corresponding fact → write exactly: No data observed.
- ZERO clinical psychology, ZERO MBTI, ZERO IQ unless the user said so themselves
- ZERO inference, ZERO extrapolation beyond the facts
- Use "it seems that" or "based on their exchanges" when synthesizing multiple facts
- You may add additional sections if the facts justify it
- All sections above must ALWAYS be present in the journal
""".strip()


class StructuredBiographyManager:
    """
    🏗️ NOUVELLE ARCHITECTURE VOLUME 2 - Gestion JSON structurée
    ============================================================
    
    Remplace l'enrichissement progressif Markdown par une base de données JSON ultra-organisée
    avec génération automatique du journal Markdown.
    """

    def __init__(self, user_name: str, data_dir: Path):
        self.user_name = user_name
        self.user_dir = data_dir / user_name.lower()
        self.user_dir.mkdir(exist_ok=True)
        
        # Fichiers de la nouvelle architecture
        self.structured_file = self.user_dir / "volume2_structured.json"
        self.journal_file = self.user_dir / "volume2_journal.md"
        
        # Initialiser avec structure vide si nécessaire
        self._ensure_structured_file_exists()
        
        print(f"[STRUCTURED-MANAGER] ✅ Gestionnaire structuré initialisé pour {user_name}")

    def _ensure_structured_file_exists(self) -> None:
        """Crée le fichier JSON structuré avec le schéma de base s'il n'existe pas"""
        if not self.structured_file.exists():
            initial_structure = self._get_empty_structure()
            self.save_structured_data(initial_structure)
            print(f"[STRUCTURED-MANAGER] 📋 Structure JSON initialisée pour {self.user_name}")

    def _get_empty_structure(self) -> Dict:
        """Retourne la structure JSON vide conforme au schéma actuel (facts[])"""
        return {
            "metadata": {
                "user_name": self.user_name,
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "total_analyses": 0,
                "data_sources": []
            },
            "facts": [],
            "profile_summary": {
                "projets_actifs": [],
                "preferences": [],
                "competences": [],
                "notes_libres": ""
            }
        }

    # ── Instruction journal personnalisable ─────────────────────────────────────────

    @staticmethod
    def get_journal_instruction() -> str:
        """Charge l'instruction personnalisée du journal, ou retourne le défaut (langue-aware)."""
        instruction_file = Path("data/biographies/journal_instruction.txt")
        try:
            if instruction_file.exists():
                content = instruction_file.read_text(encoding="utf-8").strip()
                if content and content != JOURNAL_INSTRUCTION_DEFAULT:
                    return content  # Contenu personnalisé — retourner tel quel
        except Exception as e:
            print(f"[STRUCTURED-MANAGER] Erreur lecture instruction journal: {e}")
        # Retourner le défaut selon la langue courante
        try:
            from utils.i18n import get_lang
            if get_lang() == 'en':
                return JOURNAL_INSTRUCTION_DEFAULT_EN
        except Exception:
            pass
        return JOURNAL_INSTRUCTION_DEFAULT

    @staticmethod
    def save_journal_instruction(instruction: str) -> bool:
        """Sauvegarde l'instruction personnalisée du journal."""
        try:
            instruction_file = Path("data/biographies/journal_instruction.txt")
            instruction_file.parent.mkdir(parents=True, exist_ok=True)
            instruction_file.write_text(instruction.strip(), encoding="utf-8")
            print(f"[STRUCTURED-MANAGER] Instruction journal sauvegardée ({len(instruction)} chars)")
            return True
        except Exception as e:
            print(f"[STRUCTURED-MANAGER] Erreur sauvegarde instruction journal: {e}")
            return False

    @staticmethod
    def reset_journal_instruction() -> bool:
        """Supprime l'instruction personnalisée pour revenir au défaut."""
        try:
            instruction_file = Path("data/biographies/journal_instruction.txt")
            if instruction_file.exists():
                instruction_file.unlink()
            print("[STRUCTURED-MANAGER] Instruction journal réinitialisée au défaut")
            return True
        except Exception as e:
            print(f"[STRUCTURED-MANAGER] Erreur reset instruction journal: {e}")
            return False

    def load_structured_data(self) -> Dict:
        """Charge les données JSON structurées"""
        try:
            if self.structured_file.exists():
                with open(self.structured_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return self._get_empty_structure()
        except Exception as e:
            print(f"[STRUCTURED-MANAGER] ❌ Erreur chargement données: {e}")
            return self._get_empty_structure()

    def save_structured_data(self, data: Dict) -> bool:
        """Sauvegarde les données JSON structurées"""
        try:
            # S'assurer que metadata existe (robustesse si IA génère JSON incomplet)
            if "metadata" not in data:
                data["metadata"] = {
                    "user_name": self.user_name,
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "total_analyses": 0,
                    "data_sources": []
                }
                print(f"[STRUCTURED-MANAGER] ⚠️ Metadata manquante, structure créée automatiquement")
            
            # Mettre à jour les métadonnées
            data["metadata"]["last_updated"] = datetime.now().isoformat()
            data["metadata"]["total_analyses"] = data["metadata"].get("total_analyses", 0) + 1
            
            with open(self.structured_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"[STRUCTURED-MANAGER] ✅ Données structurées sauvegardées")
            return True
        except Exception as e:
            print(f"[STRUCTURED-MANAGER] ❌ Erreur sauvegarde: {e}")
            return False

    # Correspondance catégories JSON → titres lisibles
    _CATEGORY_LABELS = {
        "preference":   "🎯 Préférences & goûts",
        "relation":     "💞 Relations & proches",
        "competence":   "🛠️ Compétences & savoir-faire",
        "projet":       "🚀 Projets & créations",
        "habitude":     "🔄 Habitudes & routines",
        "sante":        "🏥 Santé & bien-être",
        "histoire":     "📜 Histoire personnelle",
        "valeur":       "⚖️ Valeurs & convictions",
        "travail":      "💼 Travail & carrière",
        "technologie":  "💻 Technologie",
        "autre":        "📌 Divers",
    }

    def generate_facts_journal(self) -> str:
        """
        Génère un journal Markdown lisible depuis facts[] (nouvelle architecture).

        Regroupement par catégorie, tri chronologique au sein de chaque groupe.
        Aucun appel IA — génération Python pure.
        """
        try:
            data = self.load_structured_data()
            facts = data.get("facts", [])
            last_updated = data.get("last_updated") or data.get("metadata", {}).get("last_updated", "")
            date_str = ""
            if last_updated:
                try:
                    dt = datetime.fromisoformat(last_updated)
                    date_str = dt.strftime("%d/%m/%Y à %H:%M")
                except Exception:
                    date_str = last_updated[:10]

            # En-tête
            content = f"# 📔 Journal biographique — {self.user_name}\n\n"
            if date_str:
                content += f"*Dernière mise à jour : {date_str}*  \n"
            content += f"*{len(facts)} fait{'s' if len(facts) != 1 else ''} enregistré{'s' if len(facts) != 1 else ''}*\n\n---\n\n"

            if not facts:
                content += "*Aucun fait enregistré pour le moment.*\n"
                return content

            # Regrouper par catégorie
            groups: Dict[str, list] = {}
            for fact in facts:
                cat = (fact.get("category") or "autre").lower().strip()
                groups.setdefault(cat, []).append(fact)

            # Ordre d'affichage : catégories connues en premier, reste alphabétique
            known_order = list(self._CATEGORY_LABELS.keys())
            sorted_cats = sorted(
                groups.keys(),
                key=lambda c: (known_order.index(c) if c in known_order else len(known_order), c)
            )

            for cat in sorted_cats:
                label = self._CATEGORY_LABELS.get(cat, f"📌 {cat.capitalize()}")
                content += f"## {label}\n\n"

                # Tri par date dans le groupe
                sorted_facts = sorted(
                    groups[cat],
                    key=lambda f: f.get("date", ""),
                )
                for fact in sorted_facts:
                    fact_date = fact.get("date", "")
                    fact_content = fact.get("content", "").strip()
                    if not fact_content:
                        continue
                    date_prefix = f"**{fact_date}** — " if fact_date else ""
                    content += f"- {date_prefix}{fact_content}\n"

                content += "\n"

            content += (
                "---\n\n"
                f"*Journal généré automatiquement par OGMA "
                f"le {datetime.now().strftime('%d/%m/%Y à %H:%M')}*\n"
            )
            return content

        except Exception as e:
            print(f"[STRUCTURED-MANAGER] Erreur génération journal facts: {e}")
            return f"# Erreur de génération\n\nImpossible de générer le journal : {e}"

    def save_facts_journal(self) -> bool:
        """Sauvegarde le journal facts dans volume2_journal.md"""
        try:
            content = self.generate_facts_journal()
            with open(self.journal_file, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"[STRUCTURED-MANAGER] Journal facts sauvegardé: {self.journal_file}")
            return True
        except Exception as e:
            print(f"[STRUCTURED-MANAGER] Erreur sauvegarde journal facts: {e}")
            return False

    async def generate_narrative_journal_ia(
        self,
        chat_controller=None,
        force_reset: bool = False,
    ) -> bool:
        """
        Génère ou enrichit le journal biographique narratif via IA.

        Mode normal (force_reset=False) :
            Lit le journal existant + les faits compilés → l'IA enrichit/corrige.
        Mode reset (force_reset=True) :
            Ignore le journal existant → l'IA repart de zéro depuis tous les faits.

        Source des faits :
            1. bio_compiled.json (groupes thématiques) — prioritaire
            2. Fallback : volume2_structured.json (facts[]) si bio_compiled absent

        Anti-hallucination : le prompt interdit toute inférence hors faits fournis.
        """
        import asyncio
        import time

        try:
            # ── 1. Charger les faits depuis bio_compiled.json ──────────────
            bio_compiled_path = self.user_dir / "bio_compiled.json"
            all_facts_text = ""

            if bio_compiled_path.exists():
                try:
                    compiled = json.loads(bio_compiled_path.read_text(encoding="utf-8"))
                    groups = compiled.get("groups", {})
                    parts = []
                    for group_name, group_data in groups.items():
                        facts = group_data.get("facts", [])
                        lines = [f"  - {f.get('content','').strip()}" for f in facts if f.get("content")]
                        if lines:
                            parts.append(f"[{group_name}]\n" + "\n".join(lines))
                    all_facts_text = "\n\n".join(parts)
                except Exception as e:
                    print(f"[STRUCTURED-MANAGER] Erreur lecture bio_compiled: {e}")

            # Fallback : volume2_structured.json
            if not all_facts_text:
                data = self.load_structured_data()
                facts = data.get("facts", [])
                if facts:
                    all_facts_text = "\n".join(
                        f"  - [{f.get('category','?')}] {f.get('content','').strip()}"
                        for f in facts if f.get("content")
                    )

            if not all_facts_text:
                print(f"[STRUCTURED-MANAGER] Aucun fait disponible pour {self.user_name}, journal impossible")
                return False

            # ── 2. Charger journal existant si mode enrichissement ─────────
            existing_journal = ""
            if not force_reset and self.journal_file.exists():
                try:
                    existing_journal = self.journal_file.read_text(encoding="utf-8")
                    print(f"[STRUCTURED-MANAGER] Journal existant chargé ({len(existing_journal)} chars)")
                except Exception:
                    pass

            # ── 3. Instruction journal (personnalisable via l'interface) ──────
            instruction = StructuredBiographyManager.get_journal_instruction()

            now_str = datetime.now().strftime("%d/%m/%Y à %H:%M")

            if existing_journal:
                prompt = (
                    f"Tu es un biographe rigoureux. Ta mission : enrichir et corriger le journal biographique "
                    f"de {self.user_name} en intégrant les faits disponibles.\n\n"
                    f"INSTRUCTIONS ET STRUCTURE :\n{'='*60}\n{instruction}\n{'='*60}\n\n"
                    f"JOURNAL EXISTANT À ENRICHIR/CORRIGER :\n"
                    f"{'='*60}\n{existing_journal}\n{'='*60}\n\n"
                    f"FAITS DISPONIBLES (source unique — ne jamais aller au-delà) :\n"
                    f"{'='*60}\n{all_facts_text}\n{'='*60}\n\n"
                    f"Génère le journal COMPLET en Markdown avec cet en-tête exact :\n"
                    f"# 📔 Journal biographique — {self.user_name}\n"
                    f"*Dernière mise à jour : {now_str}*\n\n"
                    f"Conserve les informations exactes du journal existant. "
                    f"Enrichis ou corrige uniquement ce que les faits justifient. "
                    f"Retourne le journal complet."
                )
            else:
                prompt = (
                    f"Tu es un biographe rigoureux. Ta mission : rédiger le journal biographique "
                    f"de {self.user_name} exclusivement depuis les faits fournis.\n\n"
                    f"INSTRUCTIONS ET STRUCTURE :\n{'='*60}\n{instruction}\n{'='*60}\n\n"
                    f"FAITS DISPONIBLES (source unique — ne jamais aller au-delà) :\n"
                    f"{'='*60}\n{all_facts_text}\n{'='*60}\n\n"
                    f"Génère le journal complet en Markdown avec cet en-tête exact :\n"
                    f"# 📔 Journal biographique — {self.user_name}\n"
                    f"*Généré le : {now_str}*"
                )

            # ── 4. Récupérer le chat controller ───────────────────────────
            if not chat_controller:
                try:
                    import ogma_ng
                    if hasattr(ogma_ng, "_ensure_chat_controller"):
                        chat_controller = ogma_ng._ensure_chat_controller()
                    elif hasattr(ogma_ng, "_chat_controller"):
                        chat_controller = ogma_ng._chat_controller
                except Exception as e:
                    print(f"[STRUCTURED-MANAGER] Impossible d'accéder au chat controller: {e}")

            if not chat_controller:
                print(f"[STRUCTURED-MANAGER] Aucun chat controller disponible pour journal narratif")
                return False

            # ── 5. Appel IA ────────────────────────────────────────────────
            messages = [
                {
                    "role": "system",
                    "content": (
                        "Tu es un biographe rigoureux. Tu rédiges UNIQUEMENT depuis les faits fournis. "
                        "Format Markdown. Aucune psychologie clinique. Aucune inférence."
                    ),
                },
                {"role": "user", "content": prompt},
            ]

            print(f"[STRUCTURED-MANAGER] Génération journal narratif pour {self.user_name} "
                  f"({'reset' if force_reset else 'enrichissement'})...")

            start_time = time.time()
            chat_task = asyncio.create_task(
                chat_controller.call_chat_api(
                    messages=messages,
                    max_tokens=3000,
                    context_length=chat_controller.context_length,
                    temperature=0.3,
                )
            )

            while not chat_task.done():
                if time.time() - start_time > 180.0:
                    chat_task.cancel()
                    print(f"[STRUCTURED-MANAGER] TIMEOUT journal narratif (>180s)")
                    return False
                await asyncio.sleep(3)

            response, error = await chat_task

            if error or not response:
                print(f"[STRUCTURED-MANAGER] Erreur IA journal: {error}")
                return False

            content = response.get("content", "") if isinstance(response, dict) else str(response)

            if len(content) < 100:
                print(f"[STRUCTURED-MANAGER] Réponse IA trop courte ({len(content)} chars)")
                return False

            # ── 6. Sauvegarder ────────────────────────────────────────────
            self.journal_file.write_text(content, encoding="utf-8")
            print(f"[STRUCTURED-MANAGER] Journal narratif sauvegardé: {self.journal_file} ({len(content)} chars)")
            return True

        except Exception as e:
            print(f"[STRUCTURED-MANAGER] Erreur génération journal narratif: {e}")
            import traceback
            traceback.print_exc()
            return False


class BiographyManager:
    """Gestionnaire principal des biographies utilisateur"""

    def __init__(self, memory_manager):
        self.memory_manager = memory_manager
        self.data_dir = Path("data/biographies")
        self.data_dir.mkdir(exist_ok=True)

        # Pattern de détection des prénoms (version simple pour Phase 1)
        self.name_pattern = r'\b([A-Z][a-z]{2,15})\b'
        
        # 🚀 OPTIMISATION: Cache session pour Volume 1 (évite lectures disque répétées)
        self._session_cache = {}  # {user_name: volume1_data}
        
        # 📝 Template prompt Archiviste (externalisé)
        self._prompt_template_path = Path(__file__).parent / "prompt_archiviste_selection.txt"
        self._prompt_template = None  # Chargé lazy

        print("[BIOGRAPHY-MANAGER] ✅ Gestionnaire initialisé (cache session activé)")

    def get_current_conversation_data(self) -> Dict:
        """
        Récupère les données intégrales de la conversation actuelle
        Retourne le JSON complet avec tous les messages
        """
        try:
            # Import nécessaire pour accéder aux variables globales d'OGMA
            import ogma_ng

            # ✅ IMPORTANT : Utiliser _chat_history_ui pour avoir TOUS les messages originaux
            # _chat_history contient des résumés optimisés pour l'IA
            # _chat_history_ui contient l'historique COMPLET pour l'utilisateur et les extensions
            chat_history = getattr(ogma_ng, '_chat_history_ui', [])

            # Fallback sur _chat_history si _chat_history_ui n'existe pas encore (compatibilité)
            if not chat_history:
                chat_history = getattr(ogma_ng, '_chat_history', [])

            conversation_id = getattr(ogma_ng, '_current_conversation_id', None)

            if not chat_history:
                print("[BIOGRAPHY-MANAGER] ⚠️ Aucune conversation actuelle trouvée")
                return {}

            # Construire le dictionnaire de données de conversation
            conversation_data = {
                'conversation_id': conversation_id,
                'timestamp': datetime.now().isoformat(),
                'total_messages': len(chat_history),
                'messages': []
            }

            # Ajouter tous les messages avec leur contenu intégral
            for i, message in enumerate(chat_history):
                message_data = {
                    'index': i,
                    'role': message.get('role', 'unknown'),
                    'content': message.get('content', ''),
                    'timestamp': message.get('timestamp', datetime.now().isoformat())
                }
                conversation_data['messages'].append(message_data)

            print(f"[BIOGRAPHY-MANAGER] ✅ Conversation COMPLÈTE récupérée: {len(chat_history)} messages (historique UI)")
            return conversation_data

        except Exception as e:
            print(f"[BIOGRAPHY-MANAGER] ❌ Erreur récupération conversation: {e}")
            return {}

    async def _search_memories_for_biography(self, query: str, k: int = 100) -> List[Dict]:
        """
        Recherche directe dans FAISS sans filtrage strict pour la biographie
        Récupère tous les souvenirs pertinents sans limite artificielle
        """
        try:
            if not self.memory_manager:
                return []

            # Générer l'embedding de la requête
            query_embedding = await self.memory_manager._generate_embedding(query)
            if query_embedding is None:
                return []

            # Recherche FAISS directe
            if not self.memory_manager.faiss_index or self.memory_manager.faiss_index.ntotal == 0:
                return []

            k_search = min(k, self.memory_manager.faiss_index.ntotal)

            with self.memory_manager._faiss_lock:
                distances, indices = self.memory_manager.faiss_index.search(query_embedding.reshape(1, -1), k_search)

            # Récupérer les détails depuis SQLite
            memories = []
            for idx, distance in zip(indices[0], distances[0]):
                if idx == -1:  # Pas de résultat trouvé
                    continue

                try:
                    # Récupération depuis SQLite avec connexion temporaire
                    import sqlite3
                    with sqlite3.connect(self.memory_manager.db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute("""
                            SELECT id, text_original, summary, created_at, score_impact, title, type
                            FROM memories
                            WHERE faiss_index = ?
                        """, (int(idx),))  # Utiliser faiss_index directement

                        row = cursor.fetchone()
                        if row:
                            similarity_score = 1.0 - float(distance)  # Convertir distance en similarité
                            memory = {
                                'memory_id': row[0],  # id dans la base
                                'content': row[1] or '',  # text_original
                                'summary': row[2] or '',
                                'created_at': row[3],
                                'score_impact': float(row[4]) if row[4] else 0.0,
                                'title': row[5] or '',
                                'text_original': row[1] or '',  # text_original aussi pour cohérence
                                'type': row[6] or '',
                                'similarity_score': similarity_score
                            }
                            memories.append(memory)

                except Exception as e:
                    print(f"[BIOGRAPHY-MANAGER] ❌ Erreur récupération mémoire {idx}: {e}")
                    continue

            print(f"[BIOGRAPHY-MANAGER] 🔍 Recherche directe: {len(memories)} souvenirs récupérés")
            return memories

        except Exception as e:
            print(f"[BIOGRAPHY-MANAGER] ❌ Erreur recherche directe: {e}")
            return []

    def detect_user_names(self, text: str) -> List[str]:
        """
        Détecte les prénoms dans un texte
        Version Phase 1: Pattern amélioré pour prénoms avec présentations informelles
        """
        # Mots à exclure (noms communs, mots techniques)
        excluded_words = {
            'IA principale', 'OGMA', 'Archiviste', 'Python', 'JSON', 'API', 'Claude',
            'OpenAI', 'GPT', 'Google', 'Microsoft', 'Windows', 'Linux',
            'Bonjour', 'Merci', 'Salut', 'Oui', 'Non', 'Peut', 'Très',
            'Mais', 'Alors', 'Donc', 'Voici', 'Voilà', 'Comment', 'Pourquoi'
        }
        
        # 1. Pattern standard: mots commençant par majuscule
        potential_names = re.findall(self.name_pattern, text)
        
        # 2. Pattern spécial: présentations informelles "c'est [prénom]" (minuscules acceptées)
        informal_patterns = [
            r"c'est\s+([a-zA-Z]{3,15})\b",
            r"je\s+suis\s+([a-zA-Z]{3,15})\b",
            r"moi\s+c'est\s+([a-zA-Z]{3,15})\b",
            r"appellez?\s+moi\s+([a-zA-Z]{3,15})\b"
        ]
        
        for pattern in informal_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            # Capitaliser la première lettre des noms trouvés
            potential_names.extend([name.capitalize() for name in matches])
        
        # Filtrer les exclusions (insensible à la casse)
        valid_names = [name for name in potential_names 
                      if name.capitalize() not in {word.capitalize() for word in excluded_words}]
        
        # Retourner noms uniques avec casse normalisée
        return list(set([name.capitalize() for name in valid_names]))
    
    async def get_user_memories_from_faiss(self, user_name: str) -> List[Dict]:
        """
        Récupère les souvenirs d'un utilisateur depuis FAISS
        Utilise la même méthode que la recherche contextuelle qui fonctionne
        """
        try:
            print(f"[BIOGRAPHY-MANAGER] 🔍 Recherche souvenirs pour {user_name}")

            if not self.memory_manager:
                print("[BIOGRAPHY-MANAGER] ❌ Memory manager non disponible")
                return []

            # Recherche directe dans FAISS sans filtrage strict pour la biographie
            # Récupérer TOUS les souvenirs de l'index (pas de limite artificielle)
            total_in_index = self.memory_manager.faiss_index.ntotal if self.memory_manager.faiss_index else 0
            all_memories = await self._search_memories_for_biography(f"souvenirs concernant {user_name}", k=total_in_index)

            print(f"[BIOGRAPHY-MANAGER] 🔍 {len(all_memories)} souvenirs bruts trouvés")

            # Filtrer les souvenirs qui mentionnent vraiment le nom
            user_memories = []
            for memory in all_memories:
                # Chercher dans tous les champs possibles
                content_fields = [
                    memory.get('content', ''),
                    memory.get('summary', ''),
                    memory.get('text_original', ''),
                    memory.get('title', '')
                ]

                full_content = ' '.join(content_fields).lower()

                if user_name.lower() in full_content:
                    user_memories.append(memory)
                    print(f"[BIOGRAPHY-MANAGER] ✅ Souvenir inclus: {memory.get('title', 'Sans titre')[:50]}...")

            print(f"[BIOGRAPHY-MANAGER] 📊 {len(user_memories)} souvenirs filtrés pour {user_name}")
            return user_memories

        except Exception as e:
            print(f"[BIOGRAPHY-MANAGER] ❌ Erreur récupération souvenirs: {e}")
            return []
    
    def create_user_directory(self, user_name: str) -> Path:
        """Crée le dossier pour un utilisateur si nécessaire"""
        user_dir = self.data_dir / user_name.lower()
        user_dir.mkdir(exist_ok=True)
        return user_dir
    
    def save_volume1_memories(self, user_name: str, memories: List[Dict]) -> bool:
        """
        Sauvegarde les souvenirs du Volume 1 pour un utilisateur
        🔧 NOUVEAU: Avec backup automatique
        """
        try:
            user_dir = self.create_user_directory(user_name)
            volume1_file = user_dir / "volume1_memories.json"
            
            # 🛡️ NOUVEAU: Créer backup AVANT d'écraser le fichier
            if volume1_file.exists():
                self._create_volume1_backup(user_name, volume1_file)
            
            # Préparer les données avec horodatage
            volume1_data = {
                "user_name": user_name,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "total_memories": len(memories),
                "memories": memories
            }
            
            # Sauvegarder
            with open(volume1_file, 'w', encoding='utf-8') as f:
                json.dump(volume1_data, f, ensure_ascii=False, indent=2)
            
            print(f"[BIOGRAPHY-MANAGER] ✅ Volume 1 sauvegardé pour {user_name}")
            return True
            
        except Exception as e:
            print(f"[BIOGRAPHY-MANAGER] ❌ Erreur sauvegarde Volume 1: {e}")
            return False
    
    def load_volume1_memories(self, user_name: str) -> Optional[Dict]:
        """Charge les souvenirs du Volume 1 pour un utilisateur (avec cache session)"""
        try:
            # 🚀 OPTIMISATION: Vérifier cache session d'abord (99% plus rapide)
            if user_name in self._session_cache:
                print(f"[BIO-CACHE] ✅ Hit: {user_name} (0.001ms)")
                return self._session_cache[user_name]
            
            # Cache miss: Charger depuis disque
            user_dir = self.data_dir / user_name.lower()
            volume1_file = user_dir / "volume1_memories.json"
            
            if not volume1_file.exists():
                return None
            
            with open(volume1_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Stocker dans cache pour prochains accès
            self._session_cache[user_name] = data
            print(f"[BIO-CACHE] ⚪ Miss: {user_name} chargé et caché (10ms → cache)")
            return data
                
        except Exception as e:
            print(f"[BIOGRAPHY-MANAGER] ❌ Erreur chargement Volume 1: {e}")
            return None
    
    async def select_memories_archiviste(self, user_name: str, user_message: str, 
                                  archiviste_controller, max_memories: int = 10) -> Optional[List[Dict]]:
        """
        🚀 OPTIMISATION: Sélection intelligente souvenirs via Archiviste
        
        Processus:
        1. Charger Volume 1 complet (cache session)
        2. Créer catalogue souvenirs (titres 80 chars)
        3. Archiviste sélectionne 3-10 pertinents
        4. Retourner textes intégraux (vs résumés 150 chars)
        
        Args:
            user_name: Nom utilisateur
            user_message: Message utilisateur pour contexte
            archiviste_controller: Contrôleur IA Archiviste
            max_memories: Maximum souvenirs à sélectionner (défaut 10)
        
        Returns:
            Liste souvenirs sélectionnés avec texte intégral, None si erreur
        """
        try:
            # Étape 1: Charger Volume 1 (cache automatique via load_volume1_memories)
            volume1_data = self.load_volume1_memories(user_name)
            if not volume1_data:
                print(f"[BIO-ARCHIVISTE] ⚪ Aucun Volume 1 pour {user_name}")
                return None
            
            memories = volume1_data.get('memories', [])
            if not memories:
                print(f"[BIO-ARCHIVISTE] ⚪ Volume 1 vide pour {user_name}")
                return None
            
            # Étape 2: Créer catalogue souvenirs (titres 80 chars)
            catalog = []
            for idx, memory in enumerate(memories):
                content = memory.get('content', '')
                # Titre court 80 chars pour catalogue
                title = content[:77] + "..." if len(content) > 80 else content
                catalog.append(f"{idx+1}. {title}")
            
            catalog_text = "\n".join(catalog)
            print(f"[BIO-ARCHIVISTE] 📋 Catalogue créé: {len(catalog)} souvenirs")
            
            # Étape 3: Charger template prompt Archiviste
            if self._prompt_template is None:
                try:
                    with open(self._prompt_template_path, 'r', encoding='utf-8') as f:
                        self._prompt_template = f.read()
                    print(f"[BIO-ARCHIVISTE] 📄 Template prompt chargé: {self._prompt_template_path.name}")
                except Exception as e:
                    print(f"[BIO-ARCHIVISTE] ⚠️ Erreur chargement template: {e}")
                    # Fallback prompt minimal si fichier introuvable
                    self._prompt_template = """CONTEXTE: "{user_message}"
CATALOGUE: {catalog_text}
Sélectionne 3-{max_memories} souvenirs pertinents.
JSON: {{"selected_indices": [...], "reason": "..."}}"""
            
            # Formater prompt avec variables
            prompt = self._prompt_template.format(
                user_name=user_name,
                user_message=user_message,
                catalog_text=catalog_text,
                max_memories=max_memories
            )

            # Appel Archiviste
            print(f"[BIO-ARCHIVISTE] 🤖 Appel Archiviste pour sélection...")
            
            # Construire conversation format contrôleur
            archiviste_conversation = [{"role": "user", "content": prompt}]
            
            # Appel async via call_chat_api (méthode AIController)
            import asyncio
            
            # Vérifier si on est dans un contexte async
            try:
                # Tenter d'obtenir la loop courante
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # On est dans un contexte async, utiliser create_task
                    response, error = await archiviste_controller.call_chat_api(
                        archiviste_conversation,
                        max_tokens=500,
                        context_length=8000,
                        temperature=0.3,
                        is_json=True,
                        log_source="biography_selection"  # 🔬 TRACKING
                    )
                else:
                    # Loop existe mais n'est pas running, utiliser run_until_complete
                    response, error = loop.run_until_complete(
                        archiviste_controller.call_chat_api(
                            archiviste_conversation,
                            max_tokens=500,
                            context_length=8000,
                            temperature=0.3,
                            is_json=True,
                            log_source="biography_selection"  # 🔬 TRACKING
                        )
                    )
            except RuntimeError:
                # Pas de loop, créer une nouvelle (contexte synchrone)
                response, error = asyncio.run(
                    archiviste_controller.call_chat_api(
                        archiviste_conversation,
                        max_tokens=500,
                        context_length=8000,
                        temperature=0.3,
                        is_json=True,
                        log_source="biography_selection"  # 🔬 TRACKING
                    )
                )
            
            if error or not response:
                print(f"[BIO-ARCHIVISTE] ❌ Erreur appel Archiviste: {error}")
                print(f"[BIO-ARCHIVISTE] ⚠️ Pas de fallback - injection biographie annulée")
                return None
            
            # Étape 4: Parser réponse JSON
            # Utilise le parser robuste importé en haut du fichier
            print(f"[BIO-ARCHIVISTE] 🔍 Réponse brute: {response[:150] if response else 'None'}...")
            
            selection_data = safe_json_parse(response, fallback=None)
            
            if selection_data is None:
                print(f"[BIO-ARCHIVISTE] ❌ Impossible de parser le JSON")
                print(f"[BIO-ARCHIVISTE] ⚠️ Pas de fallback - injection biographie annulée")
                return None
            
            # Vérifier type de selection_data
            if not isinstance(selection_data, dict):
                print(f"[BIO-ARCHIVISTE] ❌ JSON n'est pas un dict: type={type(selection_data)}")
                print(f"[BIO-ARCHIVISTE] ⚠️ Pas de fallback - injection biographie annulée")
                return None
            
            if 'selected_indices' not in selection_data:
                print(f"[BIO-ARCHIVISTE] ❌ Clé 'selected_indices' absente du JSON")
                print(f"[BIO-ARCHIVISTE] 📝 Clés présentes: {list(selection_data.keys())}")
                print(f"[BIO-ARCHIVISTE] ⚠️ Pas de fallback - injection biographie annulée")
                return None
            
            selected_indices = selection_data.get('selected_indices', [])
            reason = selection_data.get('reason', 'Aucune raison')
            
            # Valider indices
            selected_indices = [idx-1 for idx in selected_indices if 0 < idx <= len(memories)]
            
            if not selected_indices:
                print(f"[BIO-ARCHIVISTE] ❌ Aucun index valide dans sélection Archiviste")
                print(f"[BIO-ARCHIVISTE] ⚠️ Pas de fallback - injection biographie annulée")
                return None
            
            # Étape 5: Retourner textes intégraux (pas résumés)
            selected_memories = [memories[idx] for idx in selected_indices]
            
            print(f"[BIO-ARCHIVISTE] ✅ {len(selected_memories)} souvenirs sélectionnés: {reason[:50]}...")
            return selected_memories
            
        except json.JSONDecodeError as e:
            print(f"[BIO-ARCHIVISTE] ❌ Erreur parsing JSON: {e}")
            print(f"[BIO-ARCHIVISTE] ⚠️ Pas de fallback - injection biographie annulée")
            return None
            
        except Exception as e:
            print(f"[BIO-ARCHIVISTE] ❌ Erreur sélection: {e}")
            print(f"[BIO-ARCHIVISTE] ⚠️ Pas de fallback - injection biographie annulée")
            return None
    
    def _load_volume1_as_signals(self, user_name: str) -> list:
        """
        Lit volume1_memories.json et le convertit en format signaux pour Phase 1.
        Utilisé comme bootstrap quand le signal_collector (SQLite user_tag) ne trouve rien.
        Exclut les souvenirs SEED (memory_id commençant par 'SEED_').
        """
        try:
            v1_file = self.data_dir / user_name.lower() / "volume1_memories.json"
            if not v1_file.exists():
                return []

            data = json.loads(v1_file.read_text(encoding="utf-8"))
            memories = data.get("memories", [])
            signals = []

            for mem in memories:
                mem_id = mem.get("memory_id", "")
                # Exclure les souvenirs SEED (métadonnées système, pas des faits utilisateur)
                if mem_id.startswith("SEED_"):
                    continue

                content = mem.get("summary") or mem.get("content") or mem.get("text_original") or ""
                content = content.strip()
                if not content:
                    continue

                signals.append({
                    "source": "volume1_bootstrap",
                    "source_id": mem_id,
                    "date": mem.get("created_at", ""),
                    "content": content,
                    "title": mem.get("title", ""),
                    "score": mem.get("score_impact", 0.0),
                })

            print(f"[BIOGRAPHY-MANAGER] Volume 1 bootstrap: {len(signals)} souvenirs utilisateurs (SEED exclus)")
            return signals

        except Exception as e:
            print(f"[BIOGRAPHY-MANAGER] Erreur lecture Volume 1 pour bootstrap: {e}")
            return []

    async def process_existing_memories_for_user(self, user_name: str) -> bool:
        """
        Traite tous les souvenirs existants pour un utilisateur
        Fonction appelée par le bouton dans l'interface
        """
        try:
            print(f"[BIOGRAPHY-MANAGER] 🔄 Traitement souvenirs existants pour {user_name}")

            # Récupérer souvenirs depuis FAISS
            memories = await self.get_user_memories_from_faiss(user_name)
            
            if not memories:
                print(f"[BIOGRAPHY-MANAGER] ℹ️ Aucun souvenir trouvé pour {user_name}")
                return True
            
            # Sauvegarder dans Volume 1
            success = self.save_volume1_memories(user_name, memories)
            
            # Créer métadonnées
            if success:
                self.create_user_metadata(user_name)
            
            return success
            
        except Exception as e:
            print(f"[BIOGRAPHY-MANAGER] ❌ Erreur traitement souvenirs: {e}")
            return False
    
    def create_user_metadata(self, user_name: str) -> bool:
        """Crée le fichier de métadonnées pour un utilisateur"""
        try:
            user_dir = self.create_user_directory(user_name)
            metadata_file = user_dir / "metadata.json"
            
            metadata = {
                "user_name": user_name,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "volume1_available": True,
                "volume2_available": False,
                "total_conversations": 0,
                "last_biography_update": None
            }
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"[BIOGRAPHY-MANAGER] ❌ Erreur création métadonnées: {e}")
            return False
    
    def get_existing_users(self) -> List[str]:
        """Retourne la liste des utilisateurs ayant des biographies"""
        try:
            users = []
            for user_dir in self.data_dir.iterdir():
                if user_dir.is_dir():
                    metadata_file = user_dir / "metadata.json"
                    if metadata_file.exists():
                        users.append(user_dir.name.title())
            return sorted(users)
        except Exception as e:
            print(f"[BIOGRAPHY-MANAGER] ❌ Erreur lecture utilisateurs: {e}")
            return []

    def _create_volume1_backup(self, user_name: str, volume1_file: Path) -> bool:
        """
        🛡️ NOUVEAU: Crée un backup du Volume 1 avant modification
        Système identique à Volume 2 : garde les 10 derniers backups

        Args:
            user_name: Nom de l'utilisateur
            volume1_file: Chemin du fichier Volume 1 actuel

        Returns:
            True si succès, False sinon
        """
        try:
            if not volume1_file.exists():
                print(f"[BIOGRAPHY-MANAGER] ℹ️ Pas de backup V1: fichier Volume 1 n'existe pas encore")
                return False

            # Créer dossier backups (partagé avec Volume 2)
            user_dir = self.data_dir / user_name.lower()
            backup_dir = user_dir / "backups"
            backup_dir.mkdir(exist_ok=True)

            # Charger métadonnées backup (partagées V1/V2)
            backup_metadata_file = backup_dir / "backup_metadata.json"
            if backup_metadata_file.exists():
                with open(backup_metadata_file, 'r', encoding='utf-8') as f:
                    backup_metadata = json.load(f)
            else:
                backup_metadata = {
                    "total_backups_created": 0,
                    "current_backup_count": 0,
                    "backups": [],
                    "volume1_backups": []  # 🆕 Nouvelle section Volume 1
                }

            # Incrémenter numéro global
            backup_metadata["total_backups_created"] += 1
            backup_number = backup_metadata["total_backups_created"]

            # Créer nom backup : volume1_YYYYMMDD_NNN.json
            timestamp = datetime.now()
            backup_name = f"volume1_{timestamp.strftime('%Y%m%d')}_{backup_number:03d}.json"
            backup_file = backup_dir / backup_name

            # Copier fichier actuel vers backup
            import shutil
            shutil.copy2(volume1_file, backup_file)

            # Ajouter aux métadonnées Volume 1
            backup_info = {
                "filename": backup_name,
                "date": timestamp.isoformat(),
                "size_bytes": backup_file.stat().st_size,
                "backup_number": backup_number,
                "type": "volume1"
            }
            
            if "volume1_backups" not in backup_metadata:
                backup_metadata["volume1_backups"] = []
            
            backup_metadata["volume1_backups"].append(backup_info)

            # Nettoyer vieux backups Volume 1 (garder seulement les 10 derniers)
            if len(backup_metadata["volume1_backups"]) > 10:
                # Trier par date (plus ancien en premier)
                backup_metadata["volume1_backups"].sort(key=lambda x: x["date"])

                # Supprimer les plus anciens
                backups_to_delete = backup_metadata["volume1_backups"][:-10]  # Tous sauf les 10 derniers
                for old_backup in backups_to_delete:
                    old_backup_file = backup_dir / old_backup["filename"]
                    if old_backup_file.exists():
                        old_backup_file.unlink()
                        print(f"[BIOGRAPHY-MANAGER] 🗑️ Backup V1 supprimé: {old_backup['filename']}")

                # Garder seulement les 10 derniers dans métadonnées
                backup_metadata["volume1_backups"] = backup_metadata["volume1_backups"][-10:]

            # Sauvegarder métadonnées
            with open(backup_metadata_file, 'w', encoding='utf-8') as f:
                json.dump(backup_metadata, f, ensure_ascii=False, indent=2)

            print(f"[BIOGRAPHY-MANAGER] 💾 Backup V1 créé: {backup_name} ({backup_info['size_bytes']} bytes)")
            print(f"[BIOGRAPHY-MANAGER] 📊 Total backups V1: {len(backup_metadata['volume1_backups'])}/10")

            return True

        except Exception as e:
            print(f"[BIOGRAPHY-MANAGER] ❌ Erreur création backup V1: {e}")
            return False

    def get_volume1_backups(self, user_name: str) -> List[Dict]:
        """
        🆕 NOUVEAU: Retourne la liste des backups Volume 1 pour un utilisateur

        Args:
            user_name: Nom de l'utilisateur

        Returns:
            Liste des backups Volume 1 (du plus récent au plus ancien)
        """
        try:
            user_dir = self.data_dir / user_name.lower()
            backup_dir = user_dir / "backups"
            backup_metadata_file = backup_dir / "backup_metadata.json"

            if not backup_metadata_file.exists():
                return []

            with open(backup_metadata_file, 'r', encoding='utf-8') as f:
                backup_metadata = json.load(f)

            # Retourner backups Volume 1 du plus récent au plus ancien
            volume1_backups = backup_metadata.get("volume1_backups", [])
            volume1_backups.sort(key=lambda x: x["date"], reverse=True)

            return volume1_backups

        except Exception as e:
            print(f"[BIOGRAPHY-MANAGER] ❌ Erreur lecture backups V1: {e}")
            return []

    def get_structured_manager(self, user_name: str) -> StructuredBiographyManager:
        """Obtient le gestionnaire structuré pour un utilisateur"""
        return StructuredBiographyManager(user_name, self.data_dir)

    def _deep_merge_dict(self, dict1: Dict, dict2: Dict) -> Dict:
        """Fusionne récursivement deux dictionnaires"""
        result = dict1.copy()
        
        for key, value in dict2.items():
            if key in result:
                if isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = self._deep_merge_dict(result[key], value)
                elif isinstance(result[key], list) and isinstance(value, list):
                    # Fusionner les listes en évitant les doublons
                    combined = result[key] + [item for item in value if item not in result[key]]
                    result[key] = combined
                else:
                    # Remplacer si nouvelle valeur non nulle
                    if value is not None:
                        result[key] = value
            else:
                result[key] = value
        
        return result

    def _collect_volume1_memories(self, user_name: str) -> str:
        """Collecte l'INTÉGRALITÉ du Volume 1 dédié à l'utilisateur"""
        try:
            # CHARGER LE FICHIER VOLUME 1 COMPLET (pas via memory_manager limité)
            volume1_file = Path(f"data/biographies/{user_name.lower()}/volume1_memories.json")
            
            if volume1_file.exists():
                with open(volume1_file, 'r', encoding='utf-8') as f:
                    volume1_data = json.load(f)
                
                # Gérer les deux formats possibles : dict avec "memories" ou liste directe
                if isinstance(volume1_data, dict) and "memories" in volume1_data:
                    memories_list = volume1_data["memories"]
                elif isinstance(volume1_data, list):
                    memories_list = volume1_data
                else:
                    memories_list = []
                
                print(f"[BIOGRAPHY-MANAGER] 📖 Volume 1 chargé: {len(memories_list)} mémoires")
                
                # INTÉGRALITÉ - Toutes les mémoires sans limite
                memories_text = []
                for i, memory in enumerate(memories_list):
                    # Gérer les différents formats de mémoire
                    if isinstance(memory, dict):
                        content = memory.get('content', '')
                        summary = memory.get('summary', '')
                        title = memory.get('title', f'Mémoire {i+1}')
                        score = memory.get('score_impact', 0)
                    elif isinstance(memory, str):
                        # Mémoire sous forme de string simple
                        content = memory
                        summary = ''
                        title = f'Mémoire {i+1}'
                        score = 0
                    else:
                        continue
                    
                    memory_entry = f"MÉMOIRE {i+1}: {title} (Impact: {score})\n"
                    if summary:
                        memory_entry += f"Résumé: {summary}\n"
                    memory_entry += f"Contenu: {content[:500]}...\n"
                    memories_text.append(memory_entry)
                
                full_text = "\n".join(memories_text)
                print(f"[BIOGRAPHY-MANAGER] ✅ Volume 1 INTÉGRAL: {len(full_text)} caractères")
                return f"=== VOLUME 1 INTÉGRAL ({len(memories_list)} mémoires) ===\n{full_text}"
            
            else:
                print(f"[BIOGRAPHY-MANAGER] ⚠️ Volume 1 introuvable: {volume1_file}")
                return f"Volume 1 introuvable pour {user_name}"
            
        except Exception as e:
            print(f"[BIOGRAPHY-MANAGER] ❌ Erreur collecte Volume 1 intégral: {e}")
            return f"Erreur accès Volume 1 intégral: {e}"
    
    def _collect_historical_conversations(self) -> str:
        """Collecte les conversations >30KB pour analyse complète par IA"""
        try:
            conversations_dir = Path("data/conversations")
            if not conversations_dir.exists():
                return "Aucune conversation historique disponible"
            
            # IDENTIFIER LES CONVERSATIONS >30KB (selon spécification)
            large_conversations = []
            for file_path in conversations_dir.glob("*.json"):
                try:
                    file_size = file_path.stat().st_size
                    # SEULEMENT les fichiers >30KB (riches en contenu)
                    if file_size > 30 * 1024:  # >30KB
                        large_conversations.append({
                            'path': file_path,
                            'size_kb': file_size // 1024,
                            'mtime': file_path.stat().st_mtime
                        })
                except OSError:
                    continue
            
            if not large_conversations:
                return "Aucune conversation >30KB trouvée"
            
            # Trier par taille décroissante (plus riches d'abord)
            large_conversations.sort(key=lambda x: x['size_kb'], reverse=True)
            
            # TOUTES les conversations >30KB (pas de limite)
            selected_conversations = large_conversations
            
            conversations_content = []
            for conv_info in selected_conversations:
                file_path = conv_info['path']
                try:
                    # CHARGEMENT COMPLET pour analyse IA
                    with open(file_path, 'r', encoding='utf-8') as f:
                        conv_data = json.load(f)
                    
                    # Gérer les deux formats de conversation
                    if isinstance(conv_data, list):
                        messages = conv_data
                    elif isinstance(conv_data, dict):
                        messages = conv_data.get('messages', [])
                    else:
                        messages = []
                    
                    if messages:
                        # 🔧 EXTRACTION ENRICHIE: Plus de contenu pour IA
                        sample_messages = []
                        if len(messages) > 30:
                            # Début (10 messages au lieu de 3)
                            sample_messages.extend(messages[:10])
                            # Milieu étendu (8 messages au lieu de 2)  
                            mid = len(messages) // 2
                            sample_messages.extend(messages[mid-4:mid+4])
                            # Fin étendue (10 messages au lieu de 3)
                            sample_messages.extend(messages[-10:])
                        else:
                            sample_messages = messages
                        
                        # Formater pour IA avec plus de contenu
                        conv_text = f"=== CONVERSATION {file_path.stem} ({conv_info['size_kb']}KB) ===\n"
                        for msg in sample_messages:
                            role = msg.get('role', 'unknown')
                            content = msg.get('content', '')[:1500]  # 1500 chars par message au lieu de 800
                            conv_text += f"{role.upper()}: {content}\n\n"
                        
                        conversations_content.append(conv_text)
                        print(f"[BIOGRAPHY-MANAGER] 📄 Conversation >30KB ajoutée: {file_path.stem} ({conv_info['size_kb']}KB)")
                        
                except Exception as e:
                    print(f"[BIOGRAPHY-MANAGER] ⚠️ Erreur lecture {file_path}: {e}")
                    continue
                        
                except Exception:
                    continue
                    
            return "\n\n".join(conversations_content) if conversations_content else "Aucune conversation lisible"
            
        except Exception as e:
            return f"Erreur accès conversations: {e}"
    
    def _collect_summaries_cache(self) -> str:
        """
        Collecte les résumés progressifs depuis les conversations JSON (v2.2+).
        
        Note: Les résumés sont maintenant stockés dans les fichiers JSON
        de conversations, pas dans summaries_cache/*.txt
        """
        try:
            # Utiliser la nouvelle API centralisée
            import sys
            root_path = Path(__file__).parent.parent.parent
            if str(root_path) not in sys.path:
                sys.path.insert(0, str(root_path))
            
            from conversation_summarizer import get_all_summaries_from_conversations
            
            conversations_dir = root_path / 'data' / 'conversations'
            
            # Récupérer tous les résumés
            all_summaries = get_all_summaries_from_conversations(
                str(conversations_dir), 
                max_conversations=50
            )
            
            if not all_summaries:
                return "Aucun résumé progressif disponible"
            
            summaries_content = []
            for conv_data in all_summaries:
                conv_id = conv_data.get('conversation_id', 'unknown')
                
                for idx, summary_range in enumerate(conv_data.get('summaries', [])):
                    content = summary_range.get('text', '')
                    if content and len(content) > 50:
                        # Aperçu du résumé
                        preview = content[:300] + "..." if len(content) > 300 else content
                        summaries_content.append(f"=== {conv_id} (range {idx}) ===\n{preview}")
            
            return "\n\n".join(summaries_content) if summaries_content else "Aucun résumé accessible"
            
        except ImportError as e:
            return f"Import conversation_summarizer échoué: {e}"
        except Exception as e:
            return f"Erreur accès résumés: {e}"

    async def generate_volume2_json(self, user_name: str, progress_callback=None) -> bool:
        """
        Phase 1: Génération/enrichissement Volume 2 JSON via signaux biographiques.

        Mode incrémental:
        - Lit le JSON existant (s'il y en a un)
        - Collecte les signaux non traités (bio_processed=false)
        - L'IA fusionne les anciens faits + nouveaux signaux
        - Marque les signaux consommés après succès

        Args:
            user_name: Nom de l'utilisateur
            progress_callback: Fonction optionnelle (étape, total, message, données)

        Returns:
            True si succès, False si erreur
        """
        try:
            print(f"[BIOGRAPHY-MANAGER] Phase 1: Generation JSON pour {user_name}")

            if progress_callback:
                await progress_callback(1, 5, "Initialisation...", {})

            # 1. COLLECTE DES SIGNAUX NON TRAITES
            from extensions.biographie_profil.signal_collector import collect_signals

            if progress_callback:
                await progress_callback(2, 5, "Collecte signaux biographiques...", {})

            result = collect_signals(user_name)
            signals = result.get("signals", [])
            counts = result.get("counts", {})

            if not signals:
                # Bootstrap depuis Volume 1 si volume2_structured.json n'a pas encore de faits
                structured_manager_check = self.get_structured_manager(user_name)
                existing_check = structured_manager_check.load_structured_data()
                has_existing_facts = bool(existing_check and existing_check.get("facts"))

                if not has_existing_facts:
                    v1_signals = self._load_volume1_as_signals(user_name)
                    if v1_signals:
                        signals = v1_signals
                        counts = {"total": len(signals), "memory": 0, "cognitive_cache": 0, "summary": 0, "volume1_bootstrap": len(signals)}
                        print(f"[BIOGRAPHY-MANAGER] Bootstrap V1→V2: {len(signals)} souvenirs Volume 1 utilises")
                    else:
                        print(f"[BIOGRAPHY-MANAGER] Aucun signal non traite pour {user_name}")
                        if progress_callback:
                            await progress_callback(5, 5, "Aucun nouveau signal a traiter", counts)
                        return True
                else:
                    print(f"[BIOGRAPHY-MANAGER] Aucun signal non traite pour {user_name}")
                    if progress_callback:
                        await progress_callback(5, 5, "Aucun nouveau signal a traiter", counts)
                    return True

            print(f"[BIOGRAPHY-MANAGER] {counts.get('total', 0)} signaux collectes")

            # 2. CHARGER LE JSON EXISTANT (mode incremental)
            structured_manager = self.get_structured_manager(user_name)
            existing_json = None
            existing_json_str = ""
            try:
                existing_data = structured_manager.load_structured_data()
                if existing_data:
                    existing_json = existing_data
                    existing_json_str = json.dumps(existing_data, ensure_ascii=False, indent=2)
                    existing_facts_count = len(existing_data.get("facts", []))
                    print(f"[BIOGRAPHY-MANAGER] JSON existant charge: {existing_facts_count} faits")
            except Exception:
                pass

            # 3. FORMATER LES SIGNAUX POUR LE PROMPT
            signals_text = []
            for i, sig in enumerate(signals[:50]):  # Limiter a 50 signaux max
                source = sig.get("source", "?")
                date = sig.get("date", "")[:10]
                content = sig.get("content", "")[:500]
                signals_text.append(f"[{i+1}] ({source}, {date}) {content}")

            signals_block = "\n".join(signals_text)

            if progress_callback:
                await progress_callback(3, 5, "Preparation prompt IA...", counts)

            # 4. ACCES AU CONTROLEUR CHAT
            import ogma_ng
            chat_controller = None
            if hasattr(ogma_ng, '_ensure_chat_controller'):
                chat_controller = ogma_ng._ensure_chat_controller()
            elif hasattr(ogma_ng, '_chat_controller') and ogma_ng._chat_controller:
                chat_controller = ogma_ng._chat_controller

            if not chat_controller:
                print(f"[BIOGRAPHY-MANAGER] Controleur chat non disponible")
                return False

            # 5. PROMPT FACTUEL (pas psychiatrique)
            existing_section = ""
            if existing_json_str:
                existing_section = f"""
=== PROFIL EXISTANT (a enrichir, pas a remplacer) ===
{existing_json_str[:8000]}
"""

            prompt = f"""Tu es un analyste factuel. Ta mission: extraire les FAITS observables sur {user_name} depuis les signaux fournis, et produire un JSON structuré.

REGLES ABSOLUES:
- Uniquement des faits explicitement presents dans les signaux
- ZERO psychologie, ZERO MBTI, ZERO inference sur la personnalite
- Si un fait est deja dans le profil existant, ne pas le dupliquer
- Chaque fait doit avoir une source traçable

{existing_section}
=== NOUVEAUX SIGNAUX ({len(signals)} elements) ===
{signals_block}

SCHEMA JSON A PRODUIRE:
```json
{{
  "user_name": "{user_name}",
  "last_updated": "{datetime.now().isoformat()}",
  "facts": [
    {{
      "date": "YYYY-MM-DD",
      "content": "Fait observable en une phrase",
      "source_type": "memory|cognitive_cache|summary",
      "category": "projet|preference|habitude|evenement|competence|relation"
    }}
  ],
  "profile_summary": {{
    "projets_actifs": ["liste des projets mentionnes"],
    "preferences": ["preferences explicites observees"],
    "competences": ["competences demontrees"],
    "notes_libres": ""
  }}
}}
```

IMPORTANT: Inclure TOUS les faits du profil existant + les nouveaux.
Genere UNIQUEMENT le JSON, rien d'autre."""

            messages = [
                {"role": "system", "content": "Tu es un analyste factuel. Tu generes UNIQUEMENT du JSON valide. Aucune psychologie, aucune inference."},
                {"role": "user", "content": prompt}
            ]

            if progress_callback:
                await progress_callback(4, 5, "Analyse IA en cours...", counts)

            print(f"[BIOGRAPHY-MANAGER] Envoi a l'IA ({len(prompt)} chars)...")

            # 6. APPEL IA
            import time
            start_time = time.time()

            chat_task = asyncio.create_task(
                chat_controller.call_chat_api(
                    messages=messages,
                    max_tokens=4000,
                    context_length=chat_controller.context_length,
                    temperature=0.3,
                    is_json=True
                )
            )

            try:
                while not chat_task.done():
                    elapsed = time.time() - start_time
                    if elapsed > 180.0:
                        chat_task.cancel()
                        raise asyncio.TimeoutError()

                    if progress_callback:
                        await progress_callback(4, 5, f"Analyse IA en cours...", {
                            **counts,
                            'elapsed': int(elapsed)
                        })
                    await asyncio.sleep(5)

                response, error = await chat_task
                duration = time.time() - start_time
                print(f"[BIOGRAPHY-MANAGER] IA repondu en {duration:.1f}s")

            except asyncio.TimeoutError:
                print(f"[BIOGRAPHY-MANAGER] TIMEOUT IA (>180s)")
                return False

            if error or not response:
                print(f"[BIOGRAPHY-MANAGER] Erreur IA: {error}")
                return False

            # 7. VALIDATION ET SAUVEGARDE
            json_content = response.get('content', '') if isinstance(response, dict) else str(response)

            try:
                import re
                cleaned_content = json_content.strip()

                # Retirer les balises markdown
                if cleaned_content.startswith('```'):
                    match = re.search(r'^```(?:json)?\s*\n(.*)```\s*$', cleaned_content, re.DOTALL)
                    if match:
                        cleaned_content = match.group(1).strip()

                structured_data = json.loads(cleaned_content)

                # Validation minimale
                if "facts" not in structured_data:
                    print(f"[BIOGRAPHY-MANAGER] Cle 'facts' manquante dans le JSON")
                    return False

                facts_count = len(structured_data.get("facts", []))
                print(f"[BIOGRAPHY-MANAGER] JSON genere: {facts_count} faits")

                # Sauvegarder
                success = structured_manager.save_structured_data(structured_data)

                if success:
                    # 8. MARQUER LES SIGNAUX COMME TRAITES
                    from extensions.biographie_profil.signal_collector import mark_signals_processed
                    marked = mark_signals_processed(signals)
                    print(f"[BIOGRAPHY-MANAGER] {marked} signaux marques bio_processed=true")

                    if progress_callback:
                        await progress_callback(5, 5, f"Biographie enrichie: {facts_count} faits", {
                            **counts,
                            'facts_count': facts_count,
                            'duration': duration
                        })
                    return True
                else:
                    print(f"[BIOGRAPHY-MANAGER] Echec sauvegarde JSON")
                    return False

            except json.JSONDecodeError as e:
                print(f"[BIOGRAPHY-MANAGER] JSON invalide: {e}")
                print(f"Contenu: {json_content[:200]}...")
                return False

        except Exception as e:
            print(f"[BIOGRAPHY-MANAGER] Erreur generation JSON: {e}")
            import traceback
            traceback.print_exc()
            return False

