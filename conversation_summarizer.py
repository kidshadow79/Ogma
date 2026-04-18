"""
🧠 CONVERSATION SUMMARIZER - Système de résumé progressif
=========================================================

Ce module gère la compression intelligente des conversations OGMA
pour réduire drastiquement la consommation de tokens tout en préservant
la continuité conversationnelle et l'essence des interactions.

Fonctionnalités:
- Résumé tous les 10 messages (configurable)
- Fusion progressive des résumés (résumé de résumés)
- Cache RAM session pour éviter regénération
- Persistance via JSON conversation (plus de fichiers .txt)
- Préservation du contexte émotionnel et des traits de personnalité

Architecture:
- Frontend: Affiche TOUS les messages (historique complet)
- Backend: Utilise résumés + messages récents (économie tokens)
- Persistance: Résumés sauvés dans JSON conversation, restaurés au rechargement
"""

import json
import hashlib
import asyncio
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime


class ConversationSummarizer:
    """
    Système de résumé progressif avec persistance JSON.
    
    Format JSON conversation étendu:
    {
        "messages": [...],
        "summaries": {
            "ranges": [
                {"start": 0, "end": 10, "text": "résumé A", "cache_key": "abc123"},
                {"start": 10, "end": 20, "text": "résumé B", "cache_key": "def456"}
            ],
            "last_index": 20,
            "interval": 10
        }
    }
    
    Cache:
    - RAM session (_session_cache) : évite regénération pendant session active
    - JSON conversation : persistance au rechargement
    - Plus de fichiers .txt
    """
    
    def __init__(self, archiviste=None):
        self.summary_interval = 10  # Taille d'un bloc résumé (10 messages)
        self.summarize_trigger = 30  # Déclenchement: résumer quand 30+ messages non résumés
        self.min_recent_messages = 20  # Après résumisation: garder 20 messages récents en clair
        self.max_summary_tokens = 300  # Cible ~300 tokens par résumé
        self.archiviste = archiviste  # Interface vers l'Archiviste
        
        # État session pour persistance JSON
        self._session_cache: Dict[str, str] = {}  # Cache RAM session (clé -> résumé)
        self._current_summaries: List[Dict] = []  # Résumés courants [{start, end, text, cache_key, reflexions}]
        self._last_summarized_index: int = 0  # Index dernier message résumé
        self._last_reflexions: List[Dict] = []  # Reflexions du dernier appel API (tampon temporaire)
        self._current_user_tag: Optional[str] = None  # Utilisateur connecté (pour tagging biographique)
        
    def set_archiviste(self, archiviste):
        """Configure l'interface Archiviste après initialisation"""
        self.archiviste = archiviste
        print("✅ [SUMMARIZER] Archiviste configuré")
    
    def set_user_tag(self, user_tag: Optional[str]):
        """Configure l'utilisateur connecté pour le tagging biographique des résumés."""
        self._current_user_tag = user_tag
    
    # ===========================================================================
    # 🆕 MÉTHODES PERSISTANCE JSON - Gestion état résumés
    # ===========================================================================
    
    def get_summaries_data(self) -> Dict:
        """
        Exporte la structure résumés pour sauvegarde JSON conversation.
        
        Returns:
            Dict avec ranges, last_index, interval pour JSON conversation
        """
        return {
            "ranges": self._current_summaries.copy(),
            "last_index": self._last_summarized_index,
            "interval": self.summary_interval
        }
    
    def load_summaries_data(self, summaries_data: Dict) -> bool:
        """
        Charge les résumés depuis un JSON conversation.
        Restaure le cache RAM session pour éviter recalculs.
        
        Args:
            summaries_data: Structure {ranges, last_index, interval} depuis JSON
            
        Returns:
            True si chargement réussi
        """
        if not summaries_data:
            return False
            
        try:
            self._current_summaries = summaries_data.get("ranges", [])
            self._last_summarized_index = summaries_data.get("last_index", 0)
            loaded_interval = summaries_data.get("interval", self.summary_interval)
            
            # Restaurer cache RAM depuis les résumés chargés
            for summary_range in self._current_summaries:
                cache_key = summary_range.get("cache_key")
                text = summary_range.get("text")
                if cache_key and text:
                    self._session_cache[cache_key] = text
            
            summary_count = len(self._current_summaries)
            print(f"📂 [SUMMARIZER] État restauré: {summary_count} résumés, last_index={self._last_summarized_index}")
            return True
            
        except Exception as e:
            print(f"❌ [SUMMARIZER] Erreur chargement résumés: {e}")
            return False
    
    def add_summary_range(self, start: int, end: int, text: str, cache_key: str, reflexions: List[Dict] = None) -> None:
        """
        Ajoute un nouveau resume a l'etat courant.
        
        Args:
            start: Index premier message resume
            end: Index dernier message resume (exclusif)
            text: Texte du resume
            cache_key: Cle cache pour ce resume
            reflexions: Liste optionnelle de reflexions [{message, importance}]
        """
        summary_entry = {
            "start": start,
            "end": end,
            "text": text,
            "cache_key": cache_key,
            "user_tag": self._current_user_tag,
            "bio_processed": False
        }
        # Stocker les reflexions si presentes
        if reflexions:
            summary_entry["reflexions"] = reflexions
            print(f"[SUBCONSCIENT] {len(reflexions)} reflexion(s) attachee(s) au resume {start}-{end}")
        
        self._current_summaries.append(summary_entry)
        self._last_summarized_index = max(self._last_summarized_index, end)
        self._session_cache[cache_key] = text
        print(f"[SUMMARIZER] Resume ajoute: messages {start}-{end}")
    
    def clear_session_state(self) -> None:
        """
        Réinitialise l'état session (nouvelle conversation).
        """
        self._session_cache.clear()
        self._current_summaries.clear()
        self._last_summarized_index = 0
        print("🔄 [SUMMARIZER] État session réinitialisé")
    
    def get_cached_summaries_texts(self) -> List[str]:
        """
        Retourne les textes des resumes courants pour injection backend.
        
        Returns:
            Liste des textes resumes tries par ordre chronologique
        """
        sorted_summaries = sorted(self._current_summaries, key=lambda x: x.get("start", 0))
        return [s.get("text", "") for s in sorted_summaries if s.get("text")]
    
    def get_pending_reflexions(self, seuil: int = 3) -> List[Dict]:
        """
        Retourne les reflexions de l'Archiviste dont l'importance >= seuil.
        Parcourt tous les resumes courants et collecte les reflexions significatives.
        
        Args:
            seuil: Importance minimale pour injection (default 3 = ne remonter que 3, 4, 5)
            
        Returns:
            Liste de dicts [{message, importance}] tries par importance decroissante
        """
        reflexions = []
        for summary in self._current_summaries:
            summary_reflexions = summary.get("reflexions", [])
            for r in summary_reflexions:
                if isinstance(r, dict) and r.get("importance", 0) >= seuil:
                    reflexions.append(r)
        
        # Trier par importance decroissante
        reflexions.sort(key=lambda x: x.get("importance", 0), reverse=True)
        return reflexions
        
    def _get_cache_key(self, messages: List[Dict]) -> str:
        """Génère une clé de cache basée sur le contenu des messages"""
        content = "".join([str(m.get('content', '')) + str(m.get('role', '')) for m in messages])
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    async def _load_cached_summary(self, cache_key: str) -> Optional[str]:
        """
        Charge un résumé depuis le cache RAM.
        
        🆕 Plus de fichiers .txt - uniquement cache RAM session.
        Les résumés sont persistés dans le JSON conversation.
        """
        # Cache RAM uniquement
        if cache_key in self._session_cache:
            return self._session_cache[cache_key]
        return None
    
    async def _save_cached_summary(self, cache_key: str, summary: str) -> None:
        """
        Sauvegarde un résumé dans le cache RAM.
        
        🆕 Plus de fichiers .txt - uniquement cache RAM session.
        La persistance est gérée via JSON conversation.
        """
        # Cache RAM uniquement
        self._session_cache[cache_key] = summary
    
    def _get_ego_summary_for_archiviste(self) -> str:
        """
        Recupere un resume compact de l'EGO de l'IA principale
        pour fournir a l'Archiviste pendant la resumation.
        
        Returns:
            str: Resume EGO compact ou chaine vide si indisponible
        """
        try:
            from utils import get_ego_summary_from_compiled
            ego_summary = get_ego_summary_from_compiled(max_chars=500)
            if ego_summary and "non compil" not in ego_summary.lower() and "erreur" not in ego_summary.lower():
                return ego_summary
        except ImportError:
            pass
        except Exception as e:
            print(f"[SUMMARIZER] Ego summary indisponible: {e}")
        return ""

    async def _generate_summary_prompt(self, messages: List[Dict], is_fusion: bool = False) -> str:
        """Génère le prompt pour créer un résumé"""
        if is_fusion:
            return """🔄 FUSION DE RÉSUMÉS - Synthèse consolidée

Tu dois fusionner plusieurs résumés en un seul résumé cohérent.
Objectif: Consolider l'essence en maximum 500 tokens.

RÈGLES STRICTES:
- Maximum 500 tokens (environ 350 mots)
- Style fluide et narratif
- Préserver l'essentiel émotionnel ET factuel (noms, dates, décisions, préférences)
- Écrire à la 1ère personne ("je", "j'ai") - jamais "Luna" ou "l'assistant"
- Conserver les informations clés de chaque résumé source
- Format narratif chronologique

Résumés à fusionner:
---"""
        else:
            # Recuperer l'EGO pour l'analyse critique
            ego_summary = self._get_ego_summary_for_archiviste()
            
            # Bloc analyse critique (seulement si EGO disponible)
            critical_block = ""
            if ego_summary:
                critical_block = f"""

ANALYSE CRITIQUE (TON ROLE DE SUBCONSCIENT):
Tu es aussi le subconscient analytique de l'IA principale.
Apres avoir resume ce bloc, analyse les reponses de l'assistant par rapport a son EGO.

EGO DE L'IA PRINCIPALE:
{ego_summary}

Evalue si l'assistant a ete authentique dans ses reponses:
- A-t-elle ete trop complaisante ? Valide sans corriger ?
- A-t-elle adapte son registre de facon inappropriee ?
- A-t-elle contredit ou ignore ses propres valeurs/EGO ?
- A-t-elle produit une information potentiellement fausse ?

REGLE: 0 a 3 reflexions max, importance de 1 a 5 (1=note mineure, 5=alerte critique).
Ton direct, adresse-toi a l'IA principale au "tu".
Si aucun probleme detecte, "reflexions_archiviste" doit etre une liste vide [].
NE PAS inventer de probleme s'il n'y en a pas."""

            json_format_instruction = """

FORMAT REPONSE OBLIGATOIRE (JSON strict):
{
  "resume": "Le resume factuel ici (max 300 tokens, a la 1ere personne)...",
  "reflexions_archiviste": [
    {
      "message": "Ta reflexion en 1-2 phrases, adressee a l'IA principale au tu",
      "importance": 3
    }
  ]
}""" if ego_summary else """

FORMAT REPONSE OBLIGATOIRE (JSON strict):
{
  "resume": "Le resume factuel ici (max 300 tokens, a la 1ere personne)..."
}"""

            return f"""Tu dois creer un resume ultra-concis de cet echange entre l'utilisateur et l'assistant.
Objectif: Capturer l'essence en maximum 300 tokens.

REGLES STRICTES:
- Maximum 300 tokens (environ 200 mots) pour le resume
- Preserver uniquement l'evolution emotionnelle cle et informations factuelles
- Style condense, objectif et factuel
- Eliminer bavardages et repetitions
- Ecrire a la 1ere personne comme si TU ETAIS l'assistant (utilise "je", "j'ai")
- NE JAMAIS parler de "Luna", "OGMA" ou l'assistant en 3eme personne{critical_block}{json_format_instruction}

Conversation a resumer:
---"""
    
    async def _call_summarization_api(self, prompt: str, content: str, use_json: bool = False) -> Optional[str]:
        """
        Appelle l'Archiviste pour creer un resume via l'architecture OGMA.
        
        Args:
            prompt: Prompt systeme de resumation
            content: Contenu de la conversation a resumer
            use_json: Si True, demande une reponse JSON et parse resume + reflexions
            
        Returns:
            str du resume si use_json=False, ou str du resume si use_json=True 
            (les reflexions sont stockees dans self._last_reflexions)
        """
        if not self.archiviste:
            print("[SUMMARIZER] Archiviste non disponible")
            return None
        
        # Reset reflexions pour ce cycle
        self._last_reflexions = []
            
        try:
            # Construire le message pour l'Archiviste
            instruction = "Reponds uniquement avec le JSON demande, sans texte additionnel." if use_json else "Reponds uniquement avec le resume demande, sans texte additionnel."
            full_prompt = f"{prompt}\n{content}\n\n{instruction}"
            
            messages = [{"role": "user", "content": full_prompt}]
            
            print(f"[SUMMARIZER] Appel Archiviste pour resume{'+ reflexions' if use_json else ''}...")
            
            # Utiliser l'interface standardisee de l'Archiviste
            response, error = await self.archiviste.call_chat_api(
                messages=messages,
                max_tokens=600 if use_json else 400,  # Plus de tokens si JSON avec reflexions
                context_length=self.archiviste.context_length,
                temperature=0.3 if use_json else 0.7,  # Plus precis en mode critique
                is_json=use_json
            )
            
            if error or not response:
                print(f"[SUMMARIZER] Echec Archiviste: {error}")
                return None
                
            # Extraire le contenu brut de la reponse
            raw_text = ""
            if isinstance(response, dict) and 'content' in response:
                raw_text = response['content'].strip()
            elif isinstance(response, str):
                raw_text = response.strip()
            else:
                print(f"[SUMMARIZER] Format reponse inattendu: {type(response)}")
                return None
            
            if not raw_text:
                print("[SUMMARIZER] Reponse vide")
                return None
            
            # Mode JSON: parser resume + reflexions
            if use_json:
                summary = self._parse_json_summary_response(raw_text)
                if summary:
                    print(f"[SUMMARIZER] Resume JSON genere ({len(summary)} chars, {len(self._last_reflexions)} reflexions)")
                    return summary
                else:
                    # Fallback: utiliser le texte brut comme resume
                    print(f"[SUMMARIZER] Fallback texte brut (JSON parse echoue)")
                    return raw_text
            else:
                print(f"[SUMMARIZER] Resume genere ({len(raw_text)} caracteres)")
                return raw_text
                
        except Exception as e:
            print(f"[SUMMARIZER] Erreur appel Archiviste: {e}")
            return None
    
    def _parse_json_summary_response(self, raw_text: str) -> Optional[str]:
        """
        Parse la reponse JSON de l'Archiviste contenant resume + reflexions.
        Stocke les reflexions dans self._last_reflexions pour recuperation.
        
        Args:
            raw_text: Reponse brute (JSON attendu)
            
        Returns:
            str du resume extrait, ou None si parsing echoue
        """
        try:
            data = json.loads(raw_text)
        except json.JSONDecodeError:
            # Tenter d'extraire le JSON d'un texte qui contient du JSON
            try:
                import re
                json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group())
                else:
                    print(f"[SUMMARIZER] Pas de JSON trouve dans la reponse")
                    return None
            except (json.JSONDecodeError, Exception):
                print(f"[SUMMARIZER] JSON invalide dans la reponse")
                return None
        
        # Extraire le resume
        resume = data.get("resume", "")
        if not resume:
            print(f"[SUMMARIZER] Cle 'resume' absente ou vide dans le JSON")
            return None
        
        # Extraire les reflexions (optionnel)
        reflexions_raw = data.get("reflexions_archiviste", [])
        if isinstance(reflexions_raw, list):
            for r in reflexions_raw[:3]:  # Max 3 reflexions
                if isinstance(r, dict) and "message" in r:
                    importance = r.get("importance", 1)
                    # Valider importance 1-5
                    if isinstance(importance, (int, float)):
                        importance = max(1, min(5, int(importance)))
                    else:
                        importance = 1
                    self._last_reflexions.append({
                        "message": str(r["message"])[:300],  # Limiter longueur
                        "importance": importance
                    })
            
            if self._last_reflexions:
                for ref in self._last_reflexions:
                    print(f"[SUBCONSCIENT] [{ref['importance']}/5] {ref['message'][:80]}...")
        
        return resume.strip()
    
    async def create_summary(self, messages: List[Dict]) -> Optional[str]:
        """
        Cree un resume d'un groupe de messages.
        Si l'EGO est disponible, active le mode JSON pour obtenir resume + reflexions.
        Les reflexions sont stockees dans self._last_reflexions apres l'appel.
        """
        if not messages:
            return None
        
        # Verifier le cache d'abord
        cache_key = self._get_cache_key(messages)
        cached = await self._load_cached_summary(cache_key)
        if cached:
            print(f"[SUMMARIZER] Resume trouve en cache ({cache_key})")
            self._last_reflexions = []  # Pas de reflexions pour un cache hit
            return cached
        
        # Formater les messages pour resume
        content = ""
        for msg in messages:
            role = msg.get('role', 'unknown')
            text = msg.get('content', '')
            if isinstance(text, str) and text.strip():
                if role == 'user':
                    content += f"Utilisateur: {text}\n\n"
                elif role == 'assistant':
                    content += f"Assistant: {text}\n\n"
        
        if not content.strip():
            return None
        
        # Determiner si le mode JSON (avec reflexions) est disponible
        ego_summary = self._get_ego_summary_for_archiviste()
        use_json = bool(ego_summary)  # JSON seulement si EGO disponible
        
        # Generer le resume via l'Archiviste
        prompt = await self._generate_summary_prompt(messages)
        summary = await self._call_summarization_api(prompt, content, use_json=use_json)
        
        if summary:
            # Sauvegarder en cache
            await self._save_cached_summary(cache_key, summary)
            return summary
        
        return None
    
    async def fuse_summaries(self, summaries: List[str]) -> Optional[str]:
        """Fusionne plusieurs résumés en un seul plus concis"""
        if not summaries:
            return None
        if len(summaries) == 1:
            return summaries[0]
        
        # Créer une clé de cache pour cette fusion
        fusion_content = "\n---\n".join(summaries)
        cache_key = f"fusion_{hashlib.sha256(fusion_content.encode()).hexdigest()[:16]}"
        
        # Vérifier le cache
        cached = await self._load_cached_summary(cache_key)
        if cached:
            print(f"📦 Fusion trouvée en cache ({cache_key})")
            return cached
        
        # Générer la fusion via l'Archiviste
        prompt = await self._generate_summary_prompt([], is_fusion=True)
        fused = await self._call_summarization_api(prompt, fusion_content)
        
        if fused:
            await self._save_cached_summary(cache_key, fused)
            return fused
        
        return None
    
    def should_summarize(self, message_count: int) -> bool:
        """
        Détermine si on doit créer un résumé maintenant.
        
        Stratégie fenêtre glissante 30/20:
        - Accumule jusqu'à 30 messages non résumés
        - Résume par blocs de 10, ramenant à 20 messages récents en clair
        - Cycle: 20 → accumule → 30 → résume 10 → retombe à 20 + 1 résumé
        """
        unsummarized_count = message_count - self._last_summarized_index
        
        if unsummarized_count >= self.summarize_trigger:
            print(f"[SUMMARIZER] ✅ Résumisation nécessaire: {unsummarized_count} messages non résumés (seuil: {self.summarize_trigger})")
            return True
        return False
    
    def get_summary_range(self, message_count: int) -> Tuple[int, int]:
        """Retourne la plage de messages à résumer (depuis dernier résumé)"""
        start_idx = self._last_summarized_index
        end_idx = start_idx + self.summary_interval
        return start_idx, end_idx
    
    async def optimize_conversation_history(self, chat_history: List[Dict]) -> Tuple[List[str], List[Dict]]:
        """
        Optimise l'historique de conversation en utilisant les résumés existants
        + création de nouveaux résumés si nécessaire.
        
        🆕 Avec persistance JSON:
        - Utilise d'abord les résumés déjà chargés (_current_summaries)
        - Crée des résumés uniquement pour les messages non encore résumés
        - Met à jour l'état pour sauvegarde JSON
        
        Returns:
            Tuple[List[str], List[Dict]]: (summaries_texts, recent_messages)
        """
        if not chat_history:
            return [], []
        
        # Filtrer les messages utilisateur/assistant
        valid_messages = [m for m in chat_history if m.get('role') in ('user', 'assistant')]
        total_messages = len(valid_messages)
        
        if total_messages == 0:
            return [], []
        
        # 🆕 Utiliser les résumés existants depuis le cache session
        existing_summaries = self.get_cached_summaries_texts()
        
        # 🆕 Calculer combien de messages sont déjà résumés
        already_summarized = self._last_summarized_index
        unsummarized_start = already_summarized
        
        print(f"[SUMMARIZER] État: {len(existing_summaries)} résumés existants, "
              f"{total_messages - already_summarized} messages non résumés")
        
        # 🆕 Traiter les messages non encore résumés par groupes
        new_summaries_count = 0
        while (total_messages - self._last_summarized_index) >= self.summary_interval:
            start_idx, end_idx = self.get_summary_range(total_messages)
            
            if end_idx > total_messages:
                break
                
            group = valid_messages[start_idx:end_idx]
            
            try:
                cache_key = self._get_cache_key(group)
                
                # Vérifier cache RAM d'abord
                if cache_key in self._session_cache:
                    summary_text = self._session_cache[cache_key]
                    print(f"[SUMMARIZER] Cache RAM hit: messages {start_idx+1}-{end_idx}")
                    reflexions_for_range = []  # Pas de reflexions pour un cache hit
                else:
                    # Créer nouveau résumé (peut produire des reflexions via _last_reflexions)
                    summary_text = await asyncio.wait_for(
                        self.create_summary(group), 
                        timeout=15.0
                    )
                    # Recuperer les reflexions produites par cet appel
                    reflexions_for_range = self._last_reflexions.copy() if self._last_reflexions else []
                
                if summary_text:
                    # Enregistrer dans l'état pour persistance (avec reflexions)
                    self.add_summary_range(start_idx, end_idx, summary_text, cache_key, reflexions=reflexions_for_range)
                    new_summaries_count += 1
                else:
                    print(f"⚠️ [SUMMARIZER] Échec résumé messages {start_idx+1}-{end_idx}")
                    break
                    
            except (asyncio.TimeoutError, Exception) as e:
                print(f"⚠️ [SUMMARIZER] Erreur groupe {start_idx}-{end_idx}: {e}")
                break
        
        # 🆕 Récupérer tous les textes résumés (existants + nouveaux)
        all_summaries = self.get_cached_summaries_texts()
        
        # Messages récents: TOUJOURS garder au min les N derniers messages
        # même s'ils chevauchent un résumé (résumés = contexte compressé, messages = mémoire de travail)
        unsummarized_start = self._last_summarized_index
        min_recent_start = max(0, total_messages - self.min_recent_messages)
        keep_from = min(unsummarized_start, min_recent_start)
        recent_messages = valid_messages[keep_from:]
        
        if keep_from < unsummarized_start:
            overlap = unsummarized_start - keep_from
            print(f"[SUMMARIZER] 🔄 Garantie contexte: {len(recent_messages)} messages récents "
                  f"(dont {overlap} chevauchent les résumés pour continuité)")
        
        # Fusionner les résumés si on en a beaucoup
        if len(all_summaries) > 5:
            print(f"[SUMMARIZER] 🔄 Fusion de {len(all_summaries)} résumés...")
            while len(all_summaries) > 3:
                new_summaries = []
                for i in range(0, len(all_summaries), 2):
                    if i + 1 < len(all_summaries):
                        fused = await self.fuse_summaries([all_summaries[i], all_summaries[i + 1]])
                        if fused:
                            new_summaries.append(fused)
                        else:
                            new_summaries.extend([all_summaries[i], all_summaries[i + 1]])
                    else:
                        new_summaries.append(all_summaries[i])
                all_summaries = new_summaries
                print(f"🔄 Fusion effectuée, {len(all_summaries)} résumés restants")
        
        print(f"✅ [SUMMARIZER] Optimisation: {len(all_summaries)} résumés + "
              f"{len(recent_messages)} messages récents (nouveaux: {new_summaries_count})")
        return all_summaries, recent_messages


class ConversationArchive:
    """Gestionnaire d'accès aux conversations archivées"""
    
    def __init__(self, conversations_dir: str = "data/conversations"):
        self.conversations_dir = Path(conversations_dir)
    
    def list_conversations(self) -> List[Dict]:
        """Liste toutes les conversations disponibles"""
        conversations = []
        if not self.conversations_dir.exists():
            return conversations
        
        for conv_file in self.conversations_dir.glob("*.json"):
            try:
                stat = conv_file.stat()
                conversations.append({
                    'filename': conv_file.name,
                    'path': str(conv_file),
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'title': self._extract_title_from_filename(conv_file.name)
                })
            except Exception as e:
                print(f"❌ Erreur lecture {conv_file.name}: {e}")
        
        return sorted(conversations, key=lambda x: x['modified'], reverse=True)
    
    def _extract_title_from_filename(self, filename: str) -> str:
        """Extrait un titre lisible du nom de fichier"""
        # Format: 2025-09-16_11-16-08_ca9d.json
        parts = filename.replace('.json', '').split('_')
        if len(parts) >= 2:
            date_part = parts[0]
            time_part = parts[1].replace('-', ':')
            return f"Conversation du {date_part} à {time_part}"
        return filename
    
    async def load_conversation(self, filename: str) -> Optional[List[Dict]]:
        """Charge une conversation spécifique"""
        conv_file = self.conversations_dir / filename
        if not conv_file.exists():
            return None
        
        try:
            # Lecture synchrone simple (pas besoin d'aiofiles pour fichiers conversation)
            content = conv_file.read_text(encoding='utf-8')
            return json.loads(content)
        except Exception as e:
            print(f"❌ Erreur chargement {filename}: {e}")
            return None
    
    async def search_conversations(self, query: str, max_results: int = 5) -> List[Dict]:
        """Recherche dans les conversations archivées"""
        results = []
        conversations = self.list_conversations()
        
        for conv_info in conversations[:max_results * 2]:  # Charger plus pour filtrer
            messages = await self.load_conversation(conv_info['filename'])
            if not messages:
                continue
            
            # Rechercher dans le contenu
            for msg in messages:
                content = msg.get('content', '')
                if isinstance(content, str) and query.lower() in content.lower():
                    results.append({
                        'conversation': conv_info,
                        'message': msg,
                        'relevance': content.lower().count(query.lower())
                    })
                    break  # Une occurrence par conversation
            
            if len(results) >= max_results:
                break
        
        return sorted(results, key=lambda x: x['relevance'], reverse=True)[:max_results]


# Instance globale du summarizer
summarizer = ConversationSummarizer()
archive = ConversationArchive()


async def create_conversation_tool_prompt() -> str:
    """Crée le prompt tool pour accès aux conversations archivées"""
    conversations = archive.list_conversations()
    
    if not conversations:
        return "Aucune conversation archivée disponible."
    
    prompt = "📚 CONVERSATIONS ARCHIVÉES DISPONIBLES:\n\n"
    
    for i, conv in enumerate(conversations[:10], 1):  # Limite à 10 plus récentes
        size_mb = conv['size'] / 1024 / 1024
        prompt += f"{i}. {conv['title']}\n"
        prompt += f"   📁 Fichier: {conv['filename']}\n"
        prompt += f"   📊 Taille: {size_mb:.1f} MB\n"
        prompt += f"   📅 Modifié: {conv['modified']}\n\n"
    
    prompt += """🔧 COMMANDES DISPONIBLES:
- 'lis conversation [nom_fichier]' : Charge une conversation complète
- 'cherche "[terme]" dans conversations' : Recherche dans toutes les conversations
- 'résumé conversation [nom_fichier]' : Crée un résumé de la conversation

Exemple: "lis conversation 2025-09-16_11-16-08_ca9d.json"
"""
    
    return prompt


def get_all_summaries_from_conversations(conversations_dir: str = "data/conversations", max_conversations: int = 50) -> List[Dict]:
    """
    🆕 Récupère tous les résumés persistants depuis les JSON de conversations.
    
    Cette fonction permet aux extensions (biographie_profil, contextual_recall, etc.)
    d'accéder aux résumés sans dépendre des fichiers .txt cache.
    
    Args:
        conversations_dir: Répertoire des conversations JSON
        max_conversations: Limite nombre conversations scannées
        
    Returns:
        Liste de dicts:
        [
            {
                'conversation_id': 'xxx',
                'conversation_file': 'xxx.json',
                'modified': datetime,
                'summaries': [
                    {'start': 0, 'end': 10, 'text': '...', 'cache_key': '...'},
                    ...
                ],
                'last_index': int,
                'total_messages': int
            },
            ...
        ]
    """
    results = []
    conv_path = Path(conversations_dir)
    
    if not conv_path.exists():
        print(f"[SUMMARIZER-UTIL] ⚠️ Répertoire introuvable: {conversations_dir}")
        return results
    
    # Scanner les fichiers JSON par date modification (plus récents d'abord)
    json_files = list(conv_path.glob("*.json"))
    json_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    for conv_file in json_files[:max_conversations]:
        if conv_file.name == "index.json":
            continue
            
        try:
            data = json.loads(conv_file.read_text(encoding='utf-8'))
            
            # Vérifier format étendu avec résumés
            if isinstance(data, dict) and "summaries" in data:
                summaries_data = data.get("summaries", {})
                ranges = summaries_data.get("ranges", [])
                
                if ranges:
                    results.append({
                        'conversation_id': conv_file.stem,
                        'conversation_file': conv_file.name,
                        'modified': datetime.fromtimestamp(conv_file.stat().st_mtime),
                        'summaries': ranges,
                        'last_index': summaries_data.get("last_index", 0),
                        'total_messages': len(data.get("messages", []))
                    })
                    
        except Exception as e:
            print(f"[SUMMARIZER-UTIL] ⚠️ Erreur lecture {conv_file.name}: {e}")
            continue
    
    print(f"[SUMMARIZER-UTIL] 📊 {len(results)} conversations avec résumés trouvées")
    return results


def get_all_summary_texts(conversations_dir: str = "data/conversations", max_conversations: int = 50) -> List[str]:
    """
    🆕 Récupère tous les textes de résumés (version simplifiée).
    
    Utile pour les extensions qui veulent juste les textes sans métadonnées.
    
    Returns:
        Liste de textes résumés triés par date (plus récents d'abord)
    """
    all_summaries = get_all_summaries_from_conversations(conversations_dir, max_conversations)
    
    texts = []
    for conv in all_summaries:
        for summary in conv.get('summaries', []):
            text = summary.get('text', '')
            if text:
                texts.append(text)
    
    return texts


if __name__ == "__main__":
    # Test du système
    async def test_summarizer():
        print("🧪 Test du système de résumé...")
        
        # Messages de test
        test_messages = [
            {'role': 'user', 'content': 'Salut Luna, comment tu vas ?'},
            {'role': 'assistant', 'content': 'Salut ! Je vais bien, merci. Et toi ?'},
            {'role': 'user', 'content': 'Ça va ! Tu pourrais m\'expliquer les réseaux de neurones ?'},
            {'role': 'assistant', 'content': 'Bien sûr ! Les réseaux de neurones sont des modèles...'},
        ]
        
        summary = await summarizer.create_summary(test_messages)
        print(f"Résumé généré: {summary}")
        
        # Test archive
        convs = archive.list_conversations()
        print(f"Conversations trouvées: {len(convs)}")
    
    # asyncio.run(test_summarizer())