# utils.py

import json
from pathlib import Path
from datetime import datetime
import os
import asyncio

# ==============================================================================
# GESTION DES CHEMINS
# ==============================================================================
DATA_DIR = Path(__file__).parent / "data"
CONVERSATIONS_DIR = DATA_DIR / "conversations"
EGO_PROMPT_FILE = DATA_DIR / "ego_prompt.txt"
EGO_PROMPT_SYNTHESIZED_FILE = DATA_DIR / "ego_prompt_synthesized.txt"
EGO_ARCHIVE_DIR = DATA_DIR / "ego_archive"

# Création des dossiers au démarrage si nécessaire
CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)
EGO_ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

# ==============================================================================
# GESTION DES CONVERSATIONS ET INDEX
# ==============================================================================

CONVERSATIONS_INDEX_FILE = DATA_DIR / "conversations" / "index.json"

def get_conversations() -> list[str]:
    """Retourne la liste des conversations triées par date de modification."""
    if not CONVERSATIONS_DIR.exists():
        return []
    files = list(CONVERSATIONS_DIR.glob("*.json"))
    # Exclure le fichier index.json
    files = [f for f in files if f.name != "index.json"]
    files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    return [f.stem for f in files]

def save_conversation(conversation_id: str, history: list[dict]):
    """Sauvegarde l'historique d'une conversation dans un fichier JSON et met à jour l'index."""
    if not conversation_id:
        return

    # 🛡️ MAGIC PHRASE GUARD: Nettoyer métadonnées internes avant sauvegarde
    from magic_phrase_guard import clean_message_for_save

    cleaned_history = []
    for msg in history:
        cleaned_msg = clean_message_for_save(msg)
        cleaned_history.append(cleaned_msg)

    # Sauvegarder version nettoyée
    filepath = CONVERSATIONS_DIR / f"{conversation_id}.json"
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(cleaned_history, f, indent=2, ensure_ascii=False)

    # Mettre à jour l'index avec le résumé (seulement si la conversation a du contenu)
    if cleaned_history and len(cleaned_history) > 0 and isinstance(cleaned_history, list):
        # Vérifier que history contient des dictionnaires valides
        valid_history = [msg for msg in cleaned_history if isinstance(msg, dict)]
        if valid_history:
            update_conversation_index(conversation_id, valid_history)

def load_conversation(conversation_id: str) -> list[dict]:
    """Charge l'historique d'une conversation depuis un fichier JSON."""
    if not conversation_id:
        return []
    filepath = CONVERSATIONS_DIR / f"{conversation_id}.json"
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def delete_conversation_file(conversation_id: str):
    """Supprime le fichier d'une conversation."""
    if not conversation_id:
        return
    filepath = CONVERSATIONS_DIR / f"{conversation_id}.json"
    if filepath.exists():
        filepath.unlink()
        print(f"🗑️ Conversation '{conversation_id}' supprimée.")

def rename_conversation_file(old_name: str, new_name: str) -> str:
    """Renomme le fichier d'une conversation."""
    if not old_name or not new_name or old_name == new_name:
        return "Nom invalide."
    old_path = CONVERSATIONS_DIR / f"{old_name}.json"
    new_path = CONVERSATIONS_DIR / f"{new_name}.json"
    if not old_path.exists():
        return f"❌ Conversation '{old_name}' non trouvée."
    if new_path.exists():
        return f"❌ Une conversation nommée '{new_name}' existe déjà."
    try:
        os.rename(old_path, new_path)
        # Mettre à jour l'index si il existe
        update_conversation_index_entry(old_name, new_name)
        return f"✅ Conversation renommée en '{new_name}'."
    except Exception as e:
        return f"❌ Erreur lors du renommage : {e}"

# ==============================================================================
# SYSTÈME DE RÉSUMÉS ET INDEX CONVERSATIONNEL
# ==============================================================================

def load_conversations_index() -> dict:
    """Charge l'index des conversations depuis le fichier."""
    try:
        if CONVERSATIONS_INDEX_FILE.exists():
            with open(CONVERSATIONS_INDEX_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Vérifier que c'est un dictionnaire valide
                if isinstance(data, dict) and "conversations" in data:
                    return data
                else:
                    print("Index conversations corrompu, réinitialisation")
                    return {"conversations": {}, "last_updated": datetime.datetime.now().isoformat()}
        return {"conversations": {}, "last_updated": datetime.datetime.now().isoformat()}
    except Exception as e:
        print(f"Erreur chargement index conversations: {e}")
        return {"conversations": {}, "last_updated": datetime.datetime.now().isoformat()}

def save_conversations_index(index_data: dict):
    """Sauvegarde l'index des conversations."""
    try:
        index_data["last_updated"] = datetime.datetime.now().isoformat()
        with open(CONVERSATIONS_INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Erreur sauvegarde index conversations: {e}")

def extract_conversation_topics(history: list[dict]) -> list[str]:
    """Extrait les sujets principaux d'une conversation."""
    topics = []
    text_content = ""
    
    for msg in history:
        if isinstance(msg, dict) and isinstance(msg.get('content'), str):
            text_content += f"{msg['content']} "
    
    # Extraction simple de mots-clés (peut être améliorée avec NLP)
    words = text_content.lower().split()
    # Filtrer les mots courants et garder les mots significatifs
    stop_words = {'le', 'la', 'les', 'de', 'du', 'des', 'un', 'une', 'et', 'ou', 'mais', 'donc', 'car', 'ni', 'or'}
    significant_words = [w for w in words if len(w) > 3 and w not in stop_words]
    
    # Compter les occurrences et prendre les plus fréquents
    word_count = {}
    for word in significant_words[:100]:  # Limiter pour performance
        word_count[word] = word_count.get(word, 0) + 1
    
    # Prendre les 5 mots les plus fréquents comme topics
    sorted_words = sorted(word_count.items(), key=lambda x: x[1], reverse=True)
    topics = [word for word, count in sorted_words[:5] if count > 1]
    
    return topics

def create_conversation_summary(conversation_id: str, history: list[dict]) -> dict:
    """Crée un résumé automatique d'une conversation."""
    if not history:
        return None
    
    # Compter les messages par rôle
    user_messages = [msg for msg in history if isinstance(msg, dict) and msg.get('role') == 'user']
    assistant_messages = [msg for msg in history if isinstance(msg, dict) and msg.get('role') == 'assistant']
    
    # Extraire le contenu principal pour le résumé
    conversation_text = ""
    key_points = []
    
    for msg in history[-6:]:  # Prendre les 6 derniers messages pour le résumé
        if isinstance(msg, dict) and isinstance(msg.get('content'), str):
            content = msg['content'][:200]  # Limiter la taille
            if msg.get('role') == 'user':
                key_points.append(f"User: {content}")
            else:
                key_points.append(f"AI: {content}")
            conversation_text += content + " "
    
    # Générer un titre simple basé sur le premier message utilisateur
    title = "Conversation"
    if user_messages:
        first_user_msg = user_messages[0].get('content', '')
        if isinstance(first_user_msg, str):
            title = first_user_msg[:50].strip()
            if len(first_user_msg) > 50:
                title += "..."
    
    # Créer un résumé concis
    summary = f"Conversation avec {len(user_messages)} messages utilisateur et {len(assistant_messages)} réponses."
    if conversation_text:
        # Prendre les premiers mots comme résumé simple
        words = conversation_text.split()[:30]
        summary = " ".join(words)
        if len(conversation_text.split()) > 30:
            summary += "..."
    
    return {
        "id": conversation_id,
        "title": title,
        "summary": summary,
        "topics": extract_conversation_topics(history),
        "date": conversation_id.split('_')[0] if '_' in conversation_id else datetime.datetime.now().strftime("%Y-%m-%d"),
        "message_count": len(history),
        "user_messages": len(user_messages),
        "assistant_messages": len(assistant_messages),
        "key_points": key_points,
        "created": datetime.datetime.now().isoformat(),
        "tokens_estimate": sum(estimate_tokens(str(msg.get('content', ''))) for msg in history if isinstance(msg, dict))
    }

def update_conversation_index(conversation_id: str, history: list[dict]):
    """Met à jour l'index avec le résumé de la conversation."""
    try:
        if not isinstance(conversation_id, str) or not isinstance(history, list):
            print(f"Erreur mise à jour index: Types incorrects - conversation_id: {type(conversation_id)}, history: {type(history)}")
            return
            
        # Vérifier que history contient des dictionnaires valides
        valid_history = [msg for msg in history if isinstance(msg, dict) and 'role' in msg]
        if not valid_history:
            print("Erreur mise à jour index: Aucun message valide dans l'historique")
            return
            
        index = load_conversations_index()
        if not isinstance(index, dict):
            print(f"Erreur mise à jour index: Index corrompu - {type(index)}")
            return
            
        summary = create_conversation_summary(conversation_id, valid_history)
        
        if summary and isinstance(summary, dict):
            if "conversations" not in index:
                index["conversations"] = {}
            index["conversations"][conversation_id] = summary
            save_conversations_index(index)
            print(f"[INDEX] Résumé créé pour '{conversation_id}': {summary.get('title', 'Sans titre')}")
        else:
            print("Erreur mise à jour index: Résumé invalide")
    except Exception as e:
        print(f"Erreur mise à jour index: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")

def update_conversation_index_entry(old_id: str, new_id: str):
    """Met à jour l'ID d'une entrée dans l'index lors d'un renommage."""
    try:
        index = load_conversations_index()
        if old_id in index["conversations"]:
            entry = index["conversations"][old_id]
            entry["id"] = new_id
            index["conversations"][new_id] = entry
            del index["conversations"][old_id]
            save_conversations_index(index)
    except Exception as e:
        print(f"Erreur renommage dans index: {e}")

def search_conversations(query: str, limit: int = 10) -> list[dict]:
    """Recherche dans les conversations par mots-clés."""
    try:
        index = load_conversations_index()
        conversations = index.get("conversations", {})
        
        if not query.strip():
            # Retourner les plus récentes si pas de query
            sorted_convs = sorted(
                [conv for conv in conversations.values() if isinstance(conv, dict)], 
                key=lambda x: x.get('created', ''), 
                reverse=True
            )
            return sorted_convs[:limit]
        
        query_lower = query.lower()
        matches = []
        
        for conv in conversations.values():
            if not isinstance(conv, dict):
                continue
                
            score = 0
            # Recherche dans le titre
            if query_lower in conv.get('title', '').lower():
                score += 10
            # Recherche dans le résumé
            if query_lower in conv.get('summary', '').lower():
                score += 5
            # Recherche dans les topics
            for topic in conv.get('topics', []):
                if query_lower in topic.lower():
                    score += 3
            # Recherche dans les points clés
            for point in conv.get('key_points', []):
                if query_lower in point.lower():
                    score += 2
            
            if score > 0:
                conv_copy = conv.copy()
                conv_copy['search_score'] = score
                matches.append(conv_copy)
        
        # Trier par score de pertinence
        matches.sort(key=lambda x: x.get('search_score', 0), reverse=True)
        return matches[:limit]
        
    except Exception as e:
        print(f"Erreur recherche conversations: {e}")
        return []

def get_conversation_context(conversation_ids: list[str], max_tokens: int = 2000) -> str:
    """Récupère le contexte des conversations spécifiées, en priorisant les résumés."""
    try:
        index = load_conversations_index()
        conversations = index.get("conversations", {})
        
        context_parts = []
        current_tokens = 0
        
        for conv_id in conversation_ids:
            if conv_id in conversations:
                conv_summary = conversations[conv_id]
                
                # Vérifier si on peut ajouter le résumé
                summary_tokens = estimate_tokens(conv_summary.get('summary', ''))
                if current_tokens + summary_tokens > max_tokens:
                    break
                
                context_part = f"Conversation '{conv_summary.get('title', conv_id)}' du {conv_summary.get('date', '')}:\n{conv_summary.get('summary', '')}"
                context_parts.append(context_part)
                current_tokens += summary_tokens
                
                # Si il reste de la place, ajouter quelques points clés
                for point in conv_summary.get('key_points', [])[:2]:
                    point_tokens = estimate_tokens(point)
                    if current_tokens + point_tokens > max_tokens:
                        break
                    context_parts.append(f"- {point}")
                    current_tokens += point_tokens
        
        return "\n\n".join(context_parts)
    except Exception as e:
        print(f"Erreur récupération contexte: {e}")
        return ""

# ==============================================================================
# FONCTIONS UTILITAIRES
# ==============================================================================

def estimate_tokens(text: str) -> int:
    """Estime le nombre de tokens dans un texte (approximation simple)."""
    if not isinstance(text, str):
        return 0
    return len(text) // 4

def get_ego_prompt() -> str:
    """Charge le contenu du prompt EGO avec expansion automatique des références mémoire."""
    # PRIORITÉ UNIQUE : ego_prompt.txt (source de vérité avec vraies références)
    if EGO_PROMPT_FILE.exists():
        try:
            raw_content = EGO_PROMPT_FILE.read_text(encoding='utf-8')
            return expand_ego_references(raw_content)
        except Exception as e:
            print(f"Erreur de lecture du fichier ego : {e}")
            return ""
    
    print("[WARNING] Fichier ego_prompt.txt non trouvé")
    return ""


def expand_ego_references(raw_ego_content: str) -> str:
    """
    Expand les références mémoire (#MEM_XXXXX) dans le contenu ego en récupérant
    le contenu réel depuis la base de données FAISS.
    
    Args:
        raw_ego_content: Contenu brut avec références #MEM_XXXXX
        
    Returns:
        str: Contenu avec références expandées vers le vrai contenu des souvenirs
    """
    import re
    import sqlite3
    import json
    
    # Pattern pour détecter les références mémoire
    pattern = r'#MEM_([A-Z0-9_]+)'
    references = re.findall(pattern, raw_ego_content)
    
    if not references:
        return raw_ego_content
    
    expanded_content = raw_ego_content
    
    try:
        # Chemin vers la base de données (utilise le même chemin que le système)
        db_path = DATA_DIR / "memory" / "memories.db"
        
        if not db_path.exists():
            print(f"[WARNING] Base de données mémoire non trouvée : {db_path}")
            return raw_ego_content
        
        # Récupérer le contenu réel des souvenirs depuis la DB
        with sqlite3.connect(str(db_path)) as conn:
            for ref_id in references:
                full_ref = f"#MEM_{ref_id}"
                
                # Récupérer le souvenir complet depuis la DB
                cursor = conn.execute(
                    "SELECT text_original, summary, lesson FROM memories WHERE id = ?", 
                    (ref_id,)
                )
                result = cursor.fetchone()
                
                if result:
                    text_original, summary, lesson = result
                    
                    # Construire le contenu expandé avec le vrai souvenir
                    if text_original:
                        # Utiliser le texte original comme contenu principal
                        expanded_text = f"**{text_original}**"
                    elif summary:
                        # Fallback sur le résumé si pas de texte original
                        expanded_text = f"**{summary}**"
                    elif lesson:
                        # Fallback final sur la leçon
                        expanded_text = f"**{lesson}**"
                    else:
                        # Si vraiment rien, garder une référence minimale
                        expanded_text = f"[Trait ego {ref_id}]"
                    
                    print(f"[EGO-EXPAND] {full_ref} → {expanded_text[:50]}...")
                else:
                    # Référence non trouvée dans la DB
                    expanded_text = f"[Trait ego {ref_id} - référence obsolète]"
                    print(f"[WARNING] Référence ego non trouvée : {full_ref}")
                
                # Remplacer la référence par le contenu expandé
                expanded_content = expanded_content.replace(full_ref, expanded_text)
    
    except Exception as e:
        print(f"[ERROR] Échec expansion ego références: {e}")
        # En cas d'erreur, retourner le contenu original avec les références
        return raw_ego_content
    
    return expanded_content

def update_ego_prompt(new_entry: str, status_queue=None):
    """
    Ajoute une nouvelle entrée au prompt EGO au lieu de l'écraser.
    Archive l'ancienne version avant la modification.
    """
    try:
        old_content = ""
        if EGO_PROMPT_FILE.exists():
            old_content = EGO_PROMPT_FILE.read_text(encoding='utf-8')

            # Archiver l'ancienne version avec millisecondes pour éviter les collisions
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Ajouter millisecondes
            archive_path = EGO_ARCHIVE_DIR / f"ego_prompt_{timestamp}.txt"
            
            # S'assurer que le nom de fichier est unique
            counter = 1
            while archive_path.exists():
                timestamp_unique = f"{timestamp}_{counter}"
                archive_path = EGO_ARCHIVE_DIR / f"ego_prompt_{timestamp_unique}.txt"
                counter += 1
            
            EGO_PROMPT_FILE.rename(archive_path)

        # Combiner l'ancien et le nouveau contenu
        combined_content = (old_content.strip() + "\n\n" + new_entry).strip()

        # Écrire le nouveau contenu combiné
        EGO_PROMPT_FILE.write_text(combined_content, encoding='utf-8')

        # Nettoyage des anciennes archives (garde les 20 plus récentes)
        archives = sorted(EGO_ARCHIVE_DIR.glob("*.txt"), key=os.path.getmtime, reverse=True)
        for old_archive in archives[20:]:
            old_archive.unlink()

        if status_queue:
            status_queue.put("[OK] Identite mise a jour et completee.")

        # Déclencher synthèse asynchrone si nécessaire
        new_tokens = estimate_tokens(combined_content)
        if new_tokens > 1500:  # Seuil pour déclencher synthèse
            print(f"[SYNTHESIS] Déclenchement synthèse ego ({new_tokens} tokens)")
            # Note: La synthèse sera déclenchée par le système appelant avec le chat_ai_controller

    except Exception as e:
        error_msg = f"[ERREUR] Erreur de mise a jour de l'ego: {e}"
        print(error_msg)
        if status_queue:
            status_queue.put(error_msg)

def restructure_ego_prompt(status_queue=None):
    """
    Restructure automatiquement l'ego prompt en analysant et réorganisant son contenu.
    """
    try:
        if not EGO_PROMPT_FILE.exists():
            if status_queue:
                status_queue.put("❌ Fichier ego inexistant, restructuration impossible.")
            return
            
        current_content = EGO_PROMPT_FILE.read_text(encoding='utf-8')
        
        # Sauvegarder avant restructuration
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = EGO_ARCHIVE_DIR / f"ego_prompt_pre_restructure_{timestamp}.txt"
        EGO_PROMPT_FILE.rename(backup_path)
        
        # Analyser le contenu pour extraire les thèmes principaux
        lines = [line.strip() for line in current_content.split('\n') if line.strip()]
        
        # Séparer les sections existantes et le contenu fragmenté
        structured_sections = []
        fragments = []
        current_section = None
        
        for line in lines:
            if line.startswith('#'):
                if current_section:
                    structured_sections.append(current_section)
                current_section = {'title': line, 'content': []}
            elif current_section:
                current_section['content'].append(line)
            else:
                fragments.append(line)
                
        if current_section:
            structured_sections.append(current_section)
        
        # Construire le nouveau contenu restructuré
        restructured_content = []
        
        # Garder les sections bien structurées
        for section in structured_sections:
            restructured_content.append(section['title'])
            restructured_content.append('')
            
            # Nettoyer et déduplicquer le contenu de la section
            clean_content = []
            seen_content = set()
            
            for content_line in section['content']:
                # Éviter les doublons sémantiques
                normalized = content_line.lower().strip()
                if normalized and normalized not in seen_content:
                    clean_content.append(content_line)
                    seen_content.add(normalized)
            
            restructured_content.extend(clean_content)
            restructured_content.append('')
        
        # Ajouter une section pour les fragments non-classés s'il y en a
        if fragments:
            unique_fragments = []
            seen_fragments = set()
            
            for fragment in fragments:
                normalized = fragment.lower().strip()
                if normalized and len(normalized) > 20 and normalized not in seen_fragments:
                    unique_fragments.append(fragment)
                    seen_fragments.add(normalized)
            
            if unique_fragments:
                restructured_content.append('# RÉFLEXIONS COMPLÉMENTAIRES')
                restructured_content.append('')
                restructured_content.extend(unique_fragments)
        
        # Écrire le contenu restructuré
        final_content = '\n'.join(restructured_content).strip()
        EGO_PROMPT_FILE.write_text(final_content, encoding='utf-8')
        
        if status_queue:
            status_queue.put(f"✅ Ego restructuré automatiquement. Sauvegarde: {backup_path.name}")
        
        print(f"[SUCCESS] Ego restructuré automatiquement")

        # Déclencher une nouvelle synthèse après restructuration
        import asyncio
        asyncio.create_task(synthesize_ego_prompt_async(status_queue))

    except Exception as e:
        error_msg = f"[ERREUR] Erreur de restructuration de l'ego : {e}"
        print(error_msg)
        if status_queue:
            status_queue.put(error_msg)


def estimate_tokens(text: str) -> int:
    """Estimation approximative du nombre de tokens."""
    return int(len(text.split()) * 1.3)  # Approximation : 1.3 token par mot


async def synthesize_ego_prompt_async(chat_ai_controller, status_queue=None):
    """Synthétise l'ego prompt de façon asynchrone pour optimiser le contexte."""
    try:
        if not EGO_PROMPT_FILE.exists():
            if status_queue:
                status_queue.put("[INFO] Pas d'ego prompt à synthétiser")
            return

        # Lire le contenu brut
        raw_content = EGO_PROMPT_FILE.read_text(encoding='utf-8')
        
        # Vérifier si synthèse nécessaire
        raw_tokens = estimate_tokens(raw_content)
        if raw_tokens < 1500:  # Seuil configurable
            if status_queue:
                status_queue.put(f"[INFO] Ego prompt compact ({raw_tokens} tokens) - synthèse non nécessaire")
            return

        if status_queue:
            status_queue.put(f"[SYNTHESIS] 🧠 Démarrage synthèse ego ({raw_tokens} tokens)...")

        # Prompt de synthèse
        synthesis_prompt = f"""Tu dois synthétiser ton propre ego prompt de façon optimale.

OBJECTIF : Condenser le contenu en gardant l'ESSENCE de ta personnalité et tes souvenirs importants.

RÈGLES :
1. Préserve les traits de personnalité fondamentaux
2. Garde les souvenirs significatifs et récents
3. Élimine les redondances et détails superflus
4. Reste fidèle à ton identité
5. Vise 60-70% du contenu original maximum

CONTENU ACTUEL ({raw_tokens} tokens) :
{raw_content}

SYNTHÈSE OPTIMISÉE :"""

        # Appel à l'IA pour synthèse
        synthesis_messages = [{"role": "user", "content": synthesis_prompt}]
        synthesized_content, error = await chat_ai_controller.call_chat_api(
            messages=synthesis_messages,
            max_tokens=2048,
            temperature=0.3,  # Plus déterministe pour la synthèse
            is_json=False
        )

        if error:
            if status_queue:
                status_queue.put(f"[ERREUR] Échec synthèse ego : {error}")
            return

        # Vérification et sauvegarde
        synthesized_tokens = estimate_tokens(synthesized_content)
        compression_ratio = raw_tokens / synthesized_tokens if synthesized_tokens > 0 else 1
        
        # Sauvegarde avec timestamp pour debug
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_synthesized = EGO_ARCHIVE_DIR / f"ego_synthesized_backup_{timestamp}.txt"
        
        # Archiver l'ancienne synthèse si elle existe
        if EGO_PROMPT_SYNTHESIZED_FILE.exists():
            EGO_PROMPT_SYNTHESIZED_FILE.rename(backup_synthesized)

        # Écrire la nouvelle synthèse
        EGO_PROMPT_SYNTHESIZED_FILE.write_text(synthesized_content, encoding='utf-8')
        
        if status_queue:
            status_queue.put(f"✅ Ego synthétisé : {raw_tokens}→{synthesized_tokens} tokens (x{compression_ratio:.1f})")
        
        print(f"[SUCCESS] Ego synthétisé avec succès - Compression: x{compression_ratio:.1f}")

    except Exception as e:
        error_msg = f"[ERREUR] Erreur de synthèse ego : {e}"
        print(error_msg)
        if status_queue:
            status_queue.put(error_msg)
        
    except Exception as e:
        error_msg = f"❌ Erreur de restructuration de l'ego: {e}"
        print(error_msg)
        if status_queue:
            status_queue.put(error_msg)
