"""
Module: conversation_commands.py
Description: Gestion commandes conversation (lecture archives, recherche)
Extrait de: ogma_ng.py (lignes 4843-4950)
Date: 2025-11-02
"""

import re
from typing import Optional


async def handle_conversation_commands(
    text: str,
    archive_module,
    summarizer_module,
    display_archived_func,
    display_search_results_func,
    display_summary_func,
    display_attachment_func,
    notify_func
) -> tuple[bool, Optional[dict], Optional[str]]:
    """
    Gère les commandes spéciales pour accéder aux conversations archivées.
    
    Args:
        text: Texte utilisateur
        archive_module: Module d'archivage (avec load_conversation, search_conversations)
        summarizer_module: Module de résumé (avec create_summary)
        display_archived_func: Fonction affichage conversation archivée
        display_search_results_func: Fonction affichage résultats recherche
        display_summary_func: Fonction affichage résumé
        display_attachment_func: Fonction affichage conversation en attachement
        notify_func: Fonction notification (safe)
        
    Returns:
        tuple[bool, dict|None, str|None]: (commande_traitée, conversation_chargée, filename)
    """
    text_lower = text.lower().strip()
    
    # Debug: vérifier si les imports fonctionnent
    try:
        # Test des imports
        if not hasattr(archive_module, 'load_conversation'):
            notify_func("ERROR Module archive non initialisé correctement", 'negative')
            return (True, None, None)
    except (NameError, AttributeError):
        notify_func("ERROR Module archive non trouvé - réinitialisation nécessaire", 'negative')
        return (True, None, None)
    
    # SEARCH DÉTECTION LANGAGE NATUREL pour lecture de conversation
    natural_patterns = [
        r'va lire\s+(?:la\s+)?conversation\s+([^\s,\.]+(?:\.json)?)',
        r'lis\s+(?:moi\s+)?(?:la\s+)?conversation\s+([^\s,\.]+(?:\.json)?)',
        r'charge\s+(?:la\s+)?conversation\s+([^\s,\.]+(?:\.json)?)',
        r'ouvre\s+(?:la\s+)?conversation\s+([^\s,\.]+(?:\.json)?)',
        r'accède\s+à\s+(?:la\s+)?conversation\s+([^\s,\.]+(?:\.json)?)'
    ]
    
    for pattern in natural_patterns:
        match = re.search(pattern, text_lower)
        if match:
            filename = match.group(1).strip()
            if not filename.endswith('.json'):
                filename += '.json'
            
            notify_func(f"SEARCH Détection automatique: chargement de {filename}", 'info')
            
            try:
                conversation = await archive_module.load_conversation(filename)
                if conversation:
                    # Charger la conversation dans le contexte global pour l'IA
                    await display_attachment_func(filename, conversation)
                    
                    # L'IA va maintenant traiter la demande avec la conversation chargée
                    # On ne return pas True pour laisser l'IA répondre
                    return (False, conversation, filename)  # Continue vers l'IA avec le contexte chargé
                else:
                    notify_func(f"ERROR Conversation non trouvée: {filename}", 'negative')
                    return (True, None, None)
            except Exception as e:
                notify_func(f"ERROR Erreur lors du chargement: {str(e)}", 'negative')
                return (True, None, None)
    
    # Commande: "lis conversation [nom_fichier]"
    if text_lower.startswith('lis conversation '):
        try:
            filename = text[len('lis conversation '):].strip()
            if not filename.endswith('.json'):
                filename += '.json'
            
            notify_func(f"SEARCH Chargement de la conversation: {filename}", 'info')
            conversation = await archive_module.load_conversation(filename)
            if conversation:
                await display_archived_func(filename, conversation)
                notify_func(f"OK Conversation chargée dans le contexte de l'IA. Tu peux maintenant lui poser des questions dessus.", 'positive')
                return (True, conversation, filename)
            else:
                notify_func(f"ERROR Conversation non trouvée: {filename}", 'negative')
        except Exception as e:
            notify_func(f"ERROR Erreur lors du chargement: {str(e)}", 'negative')
        return (True, None, None)
    
    # Commande: "cherche "[terme]" dans conversations"
    if 'cherche ' in text_lower and ' dans conversations' in text_lower:
        # Extraire le terme de recherche
        start = text_lower.find('cherche ') + len('cherche ')
        end = text_lower.find(' dans conversations')
        search_term = text[start:end].strip().strip('"\'')
        
        if search_term:
            results = await archive_module.search_conversations(search_term)
            await display_search_results_func(search_term, results)
        else:
            notify_func("ERROR Terme de recherche vide", 'negative')
        return (True, None, None)
    
    # Commande: "résumé conversation [nom_fichier]"
    if text_lower.startswith('résumé conversation ') or text_lower.startswith('resume conversation '):
        prefix_len = len('résumé conversation ') if 'résumé' in text_lower else len('resume conversation ')
        filename = text[prefix_len:].strip()
        if not filename.endswith('.json'):
            filename += '.json'
        
        conversation = await archive_module.load_conversation(filename)
        if conversation:
            summary = await summarizer_module.create_summary(conversation)
            if summary:
                await display_summary_func(filename, summary)
            else:
                notify_func("ERROR Impossible de créer le résumé", 'negative')
        else:
            notify_func(f"ERROR Conversation non trouvée: {filename}", 'negative')
        return (True, None, None)
    
    # Pas de commande détectée
    return (False, None, None)
