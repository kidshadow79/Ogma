#!/usr/bin/env python3
"""
📝 FILE WRITER EXTENSION - Sauvegarde automatique fichiers markdown
====================================================================

Extension OGMA permettant de détecter les demandes de création de fichiers .md
et de les sauvegarder automatiquement dans data/uploads/.

FONCTIONNALITÉS:
- Détection automatique demandes création .md
- Extraction blocs markdown depuis réponses Luna
- Sauvegarde avec titre document comme nom fichier
- Notification simple utilisateur

USAGE:
    from extensions.file_writer import initialize_file_writer
    
    file_writer = initialize_file_writer(
        uploads_dir="data/uploads",
        debug=False
    )
    
    # Dans workflow chat
    saved_path = file_writer.process_response(
        user_message="écris-moi un .md sur Python",
        ai_response="# Guide Python\n\nVoici le contenu..."
    )
    
    if saved_path:
        print(f"Fichier sauvegardé: {saved_path}")

ARCHITECTURE:
- request_detector.py: Détection patterns demandes .md
- markdown_extractor.py: Extraction contenu markdown
- file_saver.py: Sauvegarde fichiers avec nommage
- file_writer_agent.py: Orchestrateur principal

API PUBLIQUE:
- initialize_file_writer(): Initialise extension
- is_available(): Vérifie disponibilité
- process_response(): Traite paire user_message/ai_response
- get_statistics(): Métriques utilisation
"""

from pathlib import Path
import sys

# Pattern singleton
_file_writer_agent = None

def initialize_file_writer(
    uploads_dir: str = "data/uploads",
    debug: bool = False
) -> object:
    """
    Initialise l'extension File Writer pour sauvegarde automatique .md
    
    Args:
        uploads_dir: Répertoire sauvegarde fichiers (défaut: data/uploads)
        debug: Active logs debug détaillés
        
    Returns:
        FileWriterAgent instance ou None si erreur
    """
    global _file_writer_agent
    
    if _file_writer_agent is not None:
        return _file_writer_agent
    
    try:
        from .file_writer_agent import FileWriterAgent
        
        # Vérifier/créer répertoire uploads
        uploads_path = Path(uploads_dir)
        uploads_path.mkdir(parents=True, exist_ok=True)
        
        _file_writer_agent = FileWriterAgent(
            uploads_dir=str(uploads_path),
            debug=debug
        )
        
        if debug:
            print(f"[FILE-WRITER] ✅ Extension initialisée")
            print(f"[FILE-WRITER] 📁 Répertoire: {uploads_path}")
        
        return _file_writer_agent
        
    except Exception as e:
        print(f"[FILE-WRITER] ❌ Erreur initialisation: {e}")
        import traceback
        traceback.print_exc()
        return None


def is_available() -> bool:
    """
    Vérifie si l'extension File Writer est disponible.
    
    Returns:
        True si extension initialisée et opérationnelle
    """
    return _file_writer_agent is not None


def get_file_writer():
    """
    Retourne l'instance singleton FileWriterAgent.
    
    Returns:
        FileWriterAgent instance ou None si non initialisée
    """
    return _file_writer_agent


def process_response(user_message: str, ai_response: str) -> str:
    """
    Interface publique pour traiter paire user_message/ai_response.
    
    Args:
        user_message: Message utilisateur
        ai_response: Réponse IA générée
        
    Returns:
        Chemin fichier sauvegardé ou None si pas de sauvegarde
    """
    if _file_writer_agent is None:
        return None
    
    return _file_writer_agent.process_response(user_message, ai_response)


def get_statistics() -> dict:
    """
    Récupère les statistiques d'utilisation extension.
    
    Returns:
        Dict avec métriques (requests_detected, files_saved, etc.)
    """
    if _file_writer_agent is None:
        return {
            'requests_detected': 0,
            'files_saved': 0,
            'total_bytes': 0,
            'success_rate': 0.0
        }
    
    return _file_writer_agent.get_statistics()


def cleanup():
    """Nettoyage propre de l'extension."""
    global _file_writer_agent
    
    if _file_writer_agent is not None:
        print("[FILE-WRITER] 🧹 Cleanup extension")
        _file_writer_agent = None


# Export API publique
__all__ = [
    'initialize_file_writer',
    'is_available',
    'get_file_writer',
    'process_response',
    'get_statistics',
    'cleanup'
]
