"""
Module: formatting_utils.py
Description: Utilitaires de formatage (dates, tailles, texte, fichiers)
Extrait de: ogma_ng.py (lignes 82-95, 1124-1139, 2876-2890)
Date: 2025-11-02
"""

from typing import Optional
from datetime import datetime


def format_size(size_bytes: int) -> str:
    """
    Formate une taille en octets en format lisible.
    
    Args:
        size_bytes: Taille en octets
        
    Returns:
        str: Taille formatée (ex: "1.5 MB", "320 KB", "45 B")
        
    Examples:
        >>> format_size(0)
        '0 B'
        >>> format_size(1024)
        '1.0 KB'
        >>> format_size(1048576)
        '1.0 MB'
    """
    if size_bytes == 0:
        return "0 B"
    elif size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024**2:
        return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024**3:
        return f"{size_bytes/(1024**2):.1f} MB"
    else:
        return f"{size_bytes/(1024**3):.2f} GB"


def format_datetime(datetime_str: str) -> str:
    """
    Formate une date/heure ISO en format lisible français.
    
    Args:
        datetime_str: Date ISO format (ex: "2025-11-01T14:30:00")
        
    Returns:
        str: Date formatée (ex: "01/11/2025 à 14:30")
        
    Examples:
        >>> format_datetime("2025-11-01T14:30:00")
        '01/11/2025 à 14:30'
    """
    try:
        dt = datetime.fromisoformat(datetime_str)
        return dt.strftime("%d/%m/%Y à %H:%M")
    except Exception:
        return datetime_str


def truncate_filename(filename: str, max_length: int = 15) -> str:
    """
    Tronque un nom de fichier pour l'affichage.
    
    Args:
        filename: Nom du fichier complet
        max_length: Longueur maximale (défaut 15)
        
    Returns:
        str: Nom tronqué avec "..." si nécessaire
        
    Examples:
        >>> truncate_filename("document_tres_long_nom.pdf", 10)
        'docume....pdf'
    """
    if len(filename) <= max_length:
        return filename
    return filename[:max_length-5] + "..." + filename[-4:]


def get_file_icon(filename: str) -> str:
    """
    Retourne l'icône emoji appropriée pour un type de fichier.
    
    Args:
        filename: Nom du fichier
        
    Returns:
        str: Emoji représentant le type de fichier
        
    Examples:
        >>> get_file_icon("document.pdf")
        '📄'
        >>> get_file_icon("image.png")
        '🖼️'
    """
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg']:
        return '🖼️'
    elif ext in ['pdf']:
        return '📄'
    elif ext in ['txt', 'md']:
        return '📝'
    elif ext in ['doc', 'docx']:
        return '📰'
    else:
        return '📎'
