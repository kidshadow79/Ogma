"""
Extension Biographie Profil pour OGMA
====================================

Extension modulaire permettant à l'IA Principale de créer et maintenir 
des bibliothèques biographiques des utilisateurs.

Architecture:
- Volume 1: Souvenirs/vecteurs classés (filtre FAISS)  
- Volume 2: Journal biographique narratif (.txt)

Version: 1.0 - Phase 1
"""

from .biography_manager import BiographyManager
from .ui_components import BiographyUI
from .settings import BiographySettings
from .magic_phrases import BiographyMagicPhrases

__version__ = "1.0.0"
__author__ = "OGMA Extensions"

# État de l'extension
_biography_manager = None
_biography_ui = None
_biography_magic_phrases = None
_is_initialized = False

def initialize_biography_extension(settings_manager, memory_manager, chat_controller, archiviste_controller=None, status_queue=None):
    """
    Initialise l'extension biographie_profil
    
    Args:
        settings_manager: Gestionnaire paramètres OGMA
        memory_manager: Gestionnaire mémoire OGMA
        chat_controller: Contrôleur IA chat OGMA
        archiviste_controller: Contrôleur IA Archiviste (optionnel, pour sélection intelligente)
        status_queue: Queue pour notifications frontend (optionnel)
    """
    global _biography_manager, _biography_ui, _biography_magic_phrases, _is_initialized

    try:
        # Initialiser le gestionnaire
        _biography_manager = BiographyManager(memory_manager)

        # Initialiser l'interface
        _biography_ui = BiographyUI(settings_manager, _biography_manager)

        # 🚀 OPTIMISATION: Initialiser phrases magiques avec Archiviste + Status Queue
        _biography_magic_phrases = BiographyMagicPhrases(_biography_manager, archiviste_controller, status_queue)

        _is_initialized = True
        mode = "sélection Archiviste" if archiviste_controller else "mode classique"
        print(f"[BIOGRAPHY-EXTENSION] ✅ Extension biographie_profil initialisée ({mode})")
        return True

    except Exception as e:
        print(f"[BIOGRAPHY-EXTENSION] ❌ Erreur initialisation: {e}")
        return False

def is_available():
    """Vérifie si l'extension est disponible"""
    return _is_initialized

def get_biography_manager():
    """Retourne l'instance du gestionnaire de biographie"""
    return _biography_manager if _is_initialized else None

def get_biography_ui():
    """Retourne l'instance de l'interface utilisateur"""
    return _biography_ui if _is_initialized else None

def get_biography_magic_phrases():
    """Retourne l'instance du gestionnaire de phrases magiques"""
    return _biography_magic_phrases if _is_initialized else None

def open_settings_modal():
    """
    Fonction publique pour ouvrir la modal de paramètres
    Pattern compatible avec journal de bord pour intégration OGMA
    """
    global _biography_ui

    if not _is_initialized:
        print("[BIOGRAPHY-EXTENSION] ERROR Extension non initialisée")
        return False

    if _biography_ui:
        try:
            _biography_ui.open_settings_modal()
            print("[BIOGRAPHY-EXTENSION] Modal paramètres ouverte depuis bouton header")
            return True
        except Exception as e:
            print(f"[BIOGRAPHY-EXTENSION] ERROR Erreur ouverture modal: {e}")
            return False
    else:
        print("[BIOGRAPHY-EXTENSION] ERROR Interface utilisateur non disponible")
        return False


def get_bio_context_block(user_name: str, max_facts: int = 15) -> str:
    """
    Retourne un bloc condensé de faits biographiques prêt à injecter dans le system prompt.
    
    Charge directement le JSON (sans nécessiter l'initialisation de l'extension).
    Retourne "" si le fichier est absent, vide ou en cas d'erreur.
    
    Format :
        [PROFIL YOHAN — faits observés]
        - Yohan exprime un amour pour les films de science-fiction.
        - Yohan possède une chatte nommée Willow.
    """
    if not user_name:
        return ""
    try:
        import json
        from pathlib import Path
        structured_file = Path("data/biographies") / user_name.lower() / "volume2_structured.json"
        if not structured_file.exists():
            return ""
        with open(structured_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        facts = data.get("facts", [])
        if not facts:
            return ""
        lines = [f"- {fact['content']}" for fact in facts[:max_facts] if fact.get("content")]
        if not lines:
            return ""
        header = f"[PROFIL {user_name.upper()} — faits observés]"
        return header + "\n" + "\n".join(lines)
    except Exception as e:
        print(f"[BIOGRAPHY-EXTENSION] Erreur lecture profil condensé: {e}")
        return ""


def cleanup():
    """Nettoyage propre de l'extension biographie_profil."""
    global _biography_manager, _biography_ui, _biography_magic_phrases, _is_initialized
    _biography_manager = None
    _biography_ui = None
    _biography_magic_phrases = None
    _is_initialized = False
    print("[BIOGRAPHY-EXTENSION] Cleanup effectue")