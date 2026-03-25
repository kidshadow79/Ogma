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
EGO_COMPILED_FILE = DATA_DIR / "ego_compiled.json"

# Création des dossiers au démarrage si nécessaire
CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)

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

def save_conversation(conversation_id: str, history: list[dict], summaries_data: dict = None):
    """
    Sauvegarde l'historique d'une conversation dans un fichier JSON et met à jour l'index.
    
    Args:
        conversation_id: ID unique de la conversation
        history: Liste messages user/assistant
        summaries_data: (Optionnel) Structure résumés {ranges, last_index, interval}
    
    Format JSON étendu (si summaries_data présent):
        {"messages": [...], "summaries": {...}}
    Format classique (rétrocompatibilité):
        [...messages...]
    """
    if not conversation_id:
        return

    # 🛡️ MAGIC PHRASE GUARD: Nettoyer métadonnées internes avant sauvegarde
    from magic_phrase_guard import clean_message_for_save

    cleaned_history = []
    for msg in history:
        cleaned_msg = clean_message_for_save(msg)
        cleaned_history.append(cleaned_msg)

    # 🆕 Déterminer format sauvegarde
    filepath = CONVERSATIONS_DIR / f"{conversation_id}.json"
    
    if summaries_data and summaries_data.get("ranges"):
        # Format étendu avec résumés
        conversation_data = {
            "messages": cleaned_history,
            "summaries": summaries_data
        }
        print(f"💾 [SAVE] Format étendu: {len(cleaned_history)} messages + {len(summaries_data['ranges'])} résumés")
    else:
        # Format classique (rétrocompatibilité)
        conversation_data = cleaned_history
        print(f"💾 [SAVE] Format classique: {len(cleaned_history)} messages")
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(conversation_data, f, indent=2, ensure_ascii=False)

    # Mettre à jour l'index avec le résumé (seulement si la conversation a du contenu)
    if cleaned_history and len(cleaned_history) > 0 and isinstance(cleaned_history, list):
        # Vérifier que history contient des dictionnaires valides
        valid_history = [msg for msg in cleaned_history if isinstance(msg, dict)]
        if valid_history:
            update_conversation_index(conversation_id, valid_history)

def load_conversation(conversation_id: str) -> dict:
    """
    Charge l'historique d'une conversation depuis un fichier JSON.
    
    Args:
        conversation_id: ID unique de la conversation
    
    Returns:
        Dict avec clés:
            - "messages": Liste messages user/assistant
            - "summaries": Structure résumés ou None (ancien format)
    
    Rétrocompatibilité:
        Ancien format (liste) → {"messages": [...], "summaries": None}
        Nouveau format (dict) → retour direct
    """
    if not conversation_id:
        return {"messages": [], "summaries": None}
    
    filepath = CONVERSATIONS_DIR / f"{conversation_id}.json"
    if filepath.exists():
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 🆕 Détecter format
        if isinstance(data, list):
            # Ancien format: liste messages directe
            print(f"📂 [LOAD] Format classique: {len(data)} messages")
            return {"messages": data, "summaries": None}
        elif isinstance(data, dict) and "messages" in data:
            # Nouveau format: dict avec messages + summaries
            summaries = data.get("summaries")
            msg_count = len(data["messages"])
            summary_count = len(summaries.get("ranges", [])) if summaries else 0
            print(f"📂 [LOAD] Format étendu: {msg_count} messages + {summary_count} résumés")
            return data
        else:
            # Format invalide
            print(f"⚠️ [LOAD] Format invalide pour {conversation_id}")
            return {"messages": [], "summaries": None}
    
    return {"messages": [], "summaries": None}

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

def get_ego_summary_from_compiled(max_chars: int = 300) -> str:
    """
    Génère un résumé lisible de l'ego depuis ego_compiled.json.
    Utilisé pour introspection et export (remplace ego_prompt.txt).
    
    Args:
        max_chars: Taille maximale du résumé (default 300 pour introspection)
        
    Returns:
        str: Résumé formaté des groupes ego actifs
    """
    if not EGO_COMPILED_FILE.exists():
        return "Ego boolean non compilé - système en attente de souvenirs"
    
    try:
        with open(EGO_COMPILED_FILE, 'r', encoding='utf-8') as f:
            compiled_data = json.load(f)
        
        groups = compiled_data.get('groups', {})
        if not groups:
            return "Aucun groupe ego compilé"
        
        # Construire résumé : liste des groupes avec quelques flags clés
        group_summaries = []
        for group_name, group_data in groups.items():
            flags = group_data.get('flags', {})
            # Compter flags true vs false
            true_flags = sum(1 for f in flags.values() if f.get('value') == True)
            total_flags = len(flags)
            group_summaries.append(f"{group_name} ({true_flags}/{total_flags} traits actifs)")
        
        # Formater en texte lisible
        summary = f"Ego Boolean ({len(groups)} groupes) : " + ", ".join(group_summaries)
        
        # Tronquer si nécessaire
        if len(summary) > max_chars:
            summary = summary[:max_chars-3] + "..."
        
        return summary
        
    except Exception as e:
        print(f"[EGO-SUMMARY] Erreur lecture ego_compiled.json: {e}")
        return "Erreur chargement ego"

