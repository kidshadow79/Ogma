"""
Module: conversation_utils.py
Description: Utilitaires conversation (ID, titres simples)
Extrait de: ogma_ng.py (lignes 2230-2256)
Date: 2025-11-02
"""

from datetime import datetime


def make_conv_id() -> str:
    """
    Génère un ID unique pour conversation.
    
    Format: YYYY-MM-DD_HH-MM-SS
    
    Returns:
        str: ID conversation (ex: "2025-11-02_14-30-45")
        
    Examples:
        >>> conv_id = make_conv_id()
        >>> len(conv_id)
        19
        >>> "_" in conv_id
        True
    """
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def make_title_from_text(text: str) -> str:
    """
    Crée un titre simple depuis le texte (15 premiers mots).
    
    Args:
        text: Texte source du message
        
    Returns:
        str: Titre court (max 15 mots)
        
    Examples:
        >>> make_title_from_text("Bonjour comment vas-tu aujourd'hui ?")
        'Bonjour comment vas-tu aujourd...'
        
        >>> make_title_from_text("Court")
        'Court'
    """
    if not text:
        return "Nouvelle conversation"
    
    # Prendre max 15 mots
    words = text.split()[:15]
    title = ' '.join(words)
    
    # Tronquer à 60 caractères max
    if len(title) > 60:
        title = title[:57] + "..."
    
    return title
