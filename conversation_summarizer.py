"""
🧠 CONVERSATION SUMMARIZER - Système de résumé progressif
=========================================================

Ce module gère la compression intelligente des conversations OGMA
pour réduire drastiquement la consommation de tokens tout en préservant
la continuité conversationnelle et l'essence des interactions.

Fonctionnalités:
- Résumé tous les 10 messages (configurable)
- Fusion progressive des résumés (résumé de résumés)
- Cache des résumés pour éviter regénération
- Accès aux conversations archivées via JSON
- Préservation du contexte émotionnel et des traits de personnalité
"""

import json
import hashlib
import asyncio
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import aiofiles


class ConversationSummarizer:
    def __init__(self, cache_dir: str = "data/summaries_cache", archiviste=None):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.summary_interval = 10  # Résumé tous les 10 messages
        self.max_summary_tokens = 300  # Cible ~300 tokens par résumé
        self.archiviste = archiviste  # Interface vers l'Archiviste
        
    def set_archiviste(self, archiviste):
        """Configure l'interface Archiviste après initialisation"""
        self.archiviste = archiviste
        print("✅ [SUMMARIZER] Archiviste configuré")
        
    def _get_cache_key(self, messages: List[Dict]) -> str:
        """Génère une clé de cache basée sur le contenu des messages"""
        content = "".join([str(m.get('content', '')) + str(m.get('role', '')) for m in messages])
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    async def _load_cached_summary(self, cache_key: str) -> Optional[str]:
        """Charge un résumé depuis le cache"""
        cache_file = self.cache_dir / f"{cache_key}.txt"
        if cache_file.exists():
            try:
                async with aiofiles.open(cache_file, 'r', encoding='utf-8') as f:
                    return await f.read()
            except Exception as e:
                print(f"❌ Erreur lecture cache {cache_key}: {e}")
        return None
    
    async def _save_cached_summary(self, cache_key: str, summary: str) -> None:
        """Sauvegarde un résumé dans le cache"""
        cache_file = self.cache_dir / f"{cache_key}.txt"
        try:
            async with aiofiles.open(cache_file, 'w', encoding='utf-8') as f:
                await f.write(summary)
        except Exception as e:
            print(f"❌ Erreur sauvegarde cache {cache_key}: {e}")
    
    async def _generate_summary_prompt(self, messages: List[Dict], is_fusion: bool = False) -> str:
        """Génère le prompt pour créer un résumé"""
        if is_fusion:
            return """🔄 FUSION DE RÉSUMÉS - Synthèse ultra-compacte

Tu dois fusionner plusieurs résumés en un seul résumé très concis.
Objectif: Condenser l'essence en maximum 200 tokens.

RÈGLES STRICTES:
- Maximum 200 tokens (environ 150 mots)
- Style télégraphique mais fluide
- Préserver uniquement l'essentiel émotionnel et factuel
- Éliminer les détails secondaires
- Format narratif condensé

Résumés à fusionner:
---"""
        else:
            return """📝 RÉSUMÉ CONVERSATIONNEL - Compression maximale

Tu dois créer un résumé ultra-concis de cet échange entre l'utilisateur et OGMA Luna.
Objectif: Capturer l'essence en maximum 300 tokens.

RÈGLES STRICTES:
- Maximum 300 tokens (environ 200 mots)
- Préserver uniquement l'évolution émotionnelle clé
- Garder les informations factuelles importantes
- Style condensé mais naturel
- Éliminer bavardages et répétitions
- Focus sur progression relationnelle

Conversation à résumer:
---"""
    
    async def _call_summarization_api(self, prompt: str, content: str) -> Optional[str]:
        """
        Appelle l'Archiviste pour créer un résumé via l'architecture OGMA
        """
        if not self.archiviste:
            print("⚠️ [SUMMARIZER] Archiviste non disponible")
            return None
            
        try:
            # Construire le message pour l'Archiviste
            full_prompt = f"{prompt}\n{content}\n\nRéponds uniquement avec le résumé demandé, sans texte additionnel."
            
            messages = [{"role": "user", "content": full_prompt}]
            
            print(f"📡 [SUMMARIZER] Appel Archiviste pour résumé...")
            
            # Utiliser l'interface standardisée de l'Archiviste
            response, error = await self.archiviste.call_chat_api(
                messages=messages,
                max_tokens=400,  # Suffisant pour un résumé
                context_length=self.archiviste.context_length,  # Utiliser la config de l'archiviste
                temperature=0.7,  # Créativité modérée
                is_json=False    # Résumé en texte libre
            )
            
            if error or not response:
                print(f"❌ [SUMMARIZER] Échec Archiviste: {error}")
                return None
                
            # Extraire le contenu du résumé
            if isinstance(response, dict) and 'content' in response:
                summary = response['content'].strip()
            elif isinstance(response, str):
                summary = response.strip()
            else:
                print(f"❌ [SUMMARIZER] Format réponse inattendu: {type(response)}")
                return None
                
            if summary:
                print(f"✅ [SUMMARIZER] Résumé généré ({len(summary)} caractères)")
                return summary
            else:
                print("⚠️ [SUMMARIZER] Résumé vide")
                return None
                
        except Exception as e:
            print(f"❌ [SUMMARIZER] Erreur appel Archiviste: {e}")
            return None
    
    async def create_summary(self, messages: List[Dict]) -> Optional[str]:
        """Crée un résumé d'un groupe de messages"""
        if not messages:
            return None
        
        # Vérifier le cache d'abord
        cache_key = self._get_cache_key(messages)
        cached = await self._load_cached_summary(cache_key)
        if cached:
            print(f"📦 Résumé trouvé en cache ({cache_key})")
            return cached
        
        # Formater les messages pour résumé
        content = ""
        for msg in messages:
            role = msg.get('role', 'unknown')
            text = msg.get('content', '')
            if isinstance(text, str) and text.strip():
                if role == 'user':
                    content += f"👤 Utilisateur: {text}\n\n"
                elif role == 'assistant':
                    content += f"🌙 Luna: {text}\n\n"
        
        if not content.strip():
            return None
        
        # Générer le résumé via l'Archiviste
        prompt = await self._generate_summary_prompt(messages)
        summary = await self._call_summarization_api(prompt, content)
        
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
        """Détermine si on doit créer un résumé maintenant"""
        # Protection anti-crash: éviter résumisation si trop de messages d'un coup
        if message_count > 100:  # Limite de sécurité
            print(f"[SUMMARIZER] ⚠️ Trop de messages ({message_count}) - résumisation différée")
            return False
        return message_count > 0 and message_count % self.summary_interval == 0
    
    def get_summary_range(self, message_count: int) -> Tuple[int, int]:
        """Retourne la plage de messages à résumer"""
        end_idx = message_count
        start_idx = max(0, end_idx - self.summary_interval)
        return start_idx, end_idx
    
    async def optimize_conversation_history(self, chat_history: List[Dict]) -> Tuple[List[str], List[Dict]]:
        """
        Optimise l'historique de conversation en créant des résumés progressifs
        
        Returns:
            Tuple[List[str], List[Dict]]: (summaries, recent_messages)
        """
        if not chat_history:
            return [], []
        
        # Filtrer les messages utilisateur/assistant
        valid_messages = [m for m in chat_history if m.get('role') in ('user', 'assistant')]
        total_messages = len(valid_messages)
        
        # Protection anti-crash: limites de sécurité
        if total_messages > 150:  # Limite absolue
            print(f"[SUMMARIZER] ⚠️ Trop de messages ({total_messages}) - traitement partiel")
            valid_messages = valid_messages[-150:]  # Garde seulement les 150 derniers
            total_messages = 150
        
        if total_messages <= self.summary_interval:
            # Pas assez de messages pour résumer
            return [], valid_messages
        
        summaries = []
        remaining_messages = []
        
        # Découper en groupes de summary_interval
        full_groups = total_messages // self.summary_interval
        
        # Protection anti-crash: limiter le nombre de groupes traités d'un coup
        max_groups_per_run = 5  # Maximum 5 groupes par exécution
        if full_groups > max_groups_per_run:
            print(f"[SUMMARIZER] ⚠️ {full_groups} groupes détectés - limitation à {max_groups_per_run}")
            full_groups = max_groups_per_run
        
        for i in range(full_groups):
            start_idx = i * self.summary_interval
            end_idx = (i + 1) * self.summary_interval
            group = valid_messages[start_idx:end_idx]
            
            try:
                # Timeout par groupe
                summary = await asyncio.wait_for(self.create_summary(group), timeout=10.0)
                if summary:
                    summaries.append(summary)
                    print(f"📝 Résumé créé pour messages {start_idx+1}-{end_idx}")
                else:
                    # Si échec résumé, garder les messages originaux
                    remaining_messages.extend(group)
            except (asyncio.TimeoutError, Exception) as e:
                print(f"⚠️ [SUMMARIZER] Erreur groupe {i+1}: {e} - messages gardés")
                remaining_messages.extend(group)
        
        # Garder les messages restants non résumés
        remaining_start = full_groups * self.summary_interval
        if remaining_start < total_messages:
            remaining_messages.extend(valid_messages[remaining_start:])
        
        # Fusionner les résumés si on en a beaucoup
        if len(summaries) > 5:
            # Fusionner par paires pour réduire
            while len(summaries) > 3:
                new_summaries = []
                for i in range(0, len(summaries), 2):
                    if i + 1 < len(summaries):
                        fused = await self.fuse_summaries([summaries[i], summaries[i + 1]])
                        if fused:
                            new_summaries.append(fused)
                        else:
                            new_summaries.extend([summaries[i], summaries[i + 1]])
                    else:
                        new_summaries.append(summaries[i])
                summaries = new_summaries
                print(f"🔄 Fusion effectuée, {len(summaries)} résumés restants")
        
        print(f"✅ Optimisation terminée: {len(summaries)} résumés + {len(remaining_messages)} messages")
        return summaries, remaining_messages


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
            async with aiofiles.open(conv_file, 'r', encoding='utf-8') as f:
                content = await f.read()
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