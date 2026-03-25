"""
OGMA EXTENSIONS LOADER - Chargement centralisé des extensions
==============================================================

Gère le chargement lazy et la disponibilité des extensions OGMA.
Chaque extension est chargée uniquement quand nécessaire.
"""

from typing import Optional, Dict, Any, Callable
from pathlib import Path

# Import du module globals local
from . import globals as g

# ============================================================================
# DÉTECTION DE DISPONIBILITÉ DES EXTENSIONS
# ============================================================================

# Cache de disponibilité des extensions
_extension_availability: Dict[str, bool] = {}

def _check_extension_available(extension_name: str) -> bool:
    """Vérifie si une extension est disponible (importable)."""
    if extension_name in _extension_availability:
        return _extension_availability[extension_name]
    
    try:
        if extension_name == 'cognitive_mirror':
            from extensions.cognitive_mirror import initialize_cognitive_mirror
            _extension_availability[extension_name] = True
        elif extension_name == 'file_writer':
            from extensions.file_writer import initialize_file_writer
            _extension_availability[extension_name] = True
        elif extension_name == 'web_navigator':
            from extensions.web_navigator import WebNavigatorExtension
            _extension_availability[extension_name] = True
        elif extension_name == 'temporal_guardian':
            from extensions.temporal_guardian import create_temporal_guardian
            _extension_availability[extension_name] = True
        elif extension_name == 'contextual_recall':
            from extensions.contextual_recall import initialize_recall
            _extension_availability[extension_name] = True
        elif extension_name == 'capability_advisor':
            from extensions.capability_advisor import initialize_capability_advisor
            _extension_availability[extension_name] = True
        elif extension_name == 'text2img':
            from extensions.text2img import initialize_text2img
            _extension_availability[extension_name] = True
        elif extension_name == 'biographie_profil':
            from extensions.biographie_profil import initialize_biography
            _extension_availability[extension_name] = True
        elif extension_name == 'journal_de_bord':
            from extensions.journal_de_bord import initialize_journal
            _extension_availability[extension_name] = True
        elif extension_name == 'organic_planner':
            from extensions.organic_planner import initialize_planner
            _extension_availability[extension_name] = True
        elif extension_name == 'preanalysis_optimizer':
            from modules.preanalysis_optimizer.integration import get_optimized_context_for_message
            _extension_availability[extension_name] = True
        elif extension_name == 'memory_optimizer':
            from archiviste_memory_optimizer import create_memory_optimizer
            _extension_availability[extension_name] = True
        else:
            _extension_availability[extension_name] = False
            print(f"[EXT-LOADER] ⚠️ Extension inconnue: {extension_name}")
    except ImportError as e:
        _extension_availability[extension_name] = False
        print(f"[EXT-LOADER] ⚠️ Extension {extension_name} non disponible: {e}")
    except Exception as e:
        _extension_availability[extension_name] = False
        print(f"[EXT-LOADER] ❌ Erreur vérification {extension_name}: {e}")
    
    return _extension_availability.get(extension_name, False)


def is_extension_available(extension_name: str) -> bool:
    """API publique pour vérifier la disponibilité d'une extension."""
    return _check_extension_available(extension_name)


def get_available_extensions() -> list:
    """Retourne la liste des extensions disponibles."""
    all_extensions = [
        'cognitive_mirror',
        'file_writer', 
        'web_navigator',
        'temporal_guardian',
        'contextual_recall',
        'capability_advisor',
        'text2img',
        'biographie_profil',
        'journal_de_bord',
        'organic_planner',
        'preanalysis_optimizer',
        'memory_optimizer',
    ]
    
    return [ext for ext in all_extensions if _check_extension_available(ext)]


# ============================================================================
# CHARGEMENT DES EXTENSIONS
# ============================================================================

def load_extension(extension_name: str, **kwargs) -> Optional[Any]:
    """
    Charge une extension par son nom avec les paramètres fournis.
    
    Args:
        extension_name: Nom de l'extension à charger
        **kwargs: Paramètres spécifiques à l'extension
        
    Returns:
        Instance de l'extension ou None si échec
    """
    if not _check_extension_available(extension_name):
        return None
    
    try:
        if extension_name == 'cognitive_mirror':
            return _load_cognitive_mirror(**kwargs)
        elif extension_name == 'file_writer':
            return _load_file_writer(**kwargs)
        elif extension_name == 'web_navigator':
            return _load_web_navigator(**kwargs)
        elif extension_name == 'temporal_guardian':
            return _load_temporal_guardian(**kwargs)
        elif extension_name == 'contextual_recall':
            return _load_contextual_recall(**kwargs)
        elif extension_name == 'capability_advisor':
            return _load_capability_advisor(**kwargs)
        elif extension_name == 'organic_planner':
            return _load_organic_planner(**kwargs)
        elif extension_name == 'preanalysis_optimizer':
            return _load_preanalysis_optimizer(**kwargs)
        elif extension_name == 'memory_optimizer':
            return _load_memory_optimizer(**kwargs)
        else:
            print(f"[EXT-LOADER] ⚠️ Loader non implémenté pour: {extension_name}")
            return None
            
    except Exception as e:
        print(f"[EXT-LOADER] ❌ Erreur chargement {extension_name}: {e}")
        import traceback
        traceback.print_exc()
        return None


# ============================================================================
# LOADERS SPÉCIFIQUES PAR EXTENSION
# ============================================================================

def _load_cognitive_mirror(
    chat_controller=None, 
    archiviste_controller=None, 
    memory_manager=None,
    ui_container=None,
    **kwargs
) -> Optional[Any]:
    """Charge l'extension Cognitive Mirror."""
    if g._cognitive_mirror is not None:
        return g._cognitive_mirror
    
    try:
        from extensions.cognitive_mirror import (
            initialize_cognitive_mirror, 
            get_cognitive_mirror
        )
        
        success = initialize_cognitive_mirror(
            chat_controller=chat_controller,
            archiviste_controller=archiviste_controller,
            memory_manager=memory_manager,
            ui_container=ui_container
        )
        
        if success:
            g._cognitive_mirror = get_cognitive_mirror()
            print("[EXT-LOADER] 🧠 Cognitive Mirror chargé")
            return g._cognitive_mirror
        else:
            print("[EXT-LOADER] ❌ Échec initialisation Cognitive Mirror")
            return None
            
    except Exception as e:
        print(f"[EXT-LOADER] ❌ Erreur Cognitive Mirror: {e}")
        return None


def _load_file_writer(uploads_dir: str = "data/uploads", debug: bool = True, **kwargs) -> Optional[Any]:
    """Charge l'extension File Writer."""
    if g._file_writer_ext is not None:
        return g._file_writer_ext
    
    try:
        from extensions.file_writer import initialize_file_writer
        
        g._file_writer_ext = initialize_file_writer(
            uploads_dir=uploads_dir,
            debug=debug
        )
        
        if g._file_writer_ext:
            print("[EXT-LOADER] 📝 File Writer chargé")
        return g._file_writer_ext
        
    except Exception as e:
        print(f"[EXT-LOADER] ❌ Erreur File Writer: {e}")
        return None


def _load_web_navigator(**kwargs) -> Optional[Any]:
    """Charge l'extension Web Navigator (singleton)."""
    if g._web_navigator_ext is not None:
        return g._web_navigator_ext
    
    try:
        from extensions.web_navigator import WebNavigatorExtension
        
        g._web_navigator_ext = WebNavigatorExtension()
        print("[EXT-LOADER] 🌐 Web Navigator chargé")
        return g._web_navigator_ext
        
    except Exception as e:
        print(f"[EXT-LOADER] ❌ Erreur Web Navigator: {e}")
        return None


def _load_temporal_guardian(config: dict = None, debug: bool = False, **kwargs) -> Optional[Any]:
    """Charge l'extension Temporal Guardian."""
    if g._temporal_guardian is not None:
        return g._temporal_guardian
    
    try:
        from extensions.temporal_guardian import create_temporal_guardian
        
        g._temporal_guardian = create_temporal_guardian(config or {}, debug=debug)
        
        if debug:
            print("[EXT-LOADER] 🕒 Temporal Guardian chargé")
        return g._temporal_guardian
        
    except Exception as e:
        print(f"[EXT-LOADER] ❌ Erreur Temporal Guardian: {e}")
        return None


def _load_contextual_recall(
    conversations_path: str = "data/conversations",
    debug: bool = False,
    **kwargs  # Rétrocompatibilité (ignore summaries_cache_path obsolète)
) -> Optional[Any]:
    """Charge l'extension Contextual Recall."""
    if g._contextual_recall_ext is not None:
        return g._contextual_recall_ext
    
    try:
        from extensions.contextual_recall import initialize_recall
        
        g._contextual_recall_ext = initialize_recall(
            conversations_path=conversations_path,
            debug=debug
        )
        
        if g._contextual_recall_ext:
            print("[EXT-LOADER] 📚 Contextual Recall chargé")
        return g._contextual_recall_ext
        
    except Exception as e:
        print(f"[EXT-LOADER] ❌ Erreur Contextual Recall: {e}")
        return None


def _load_capability_advisor(
    chat_controller=None,
    archiviste_controller=None,
    memory_manager=None,
    **kwargs
) -> Optional[Any]:
    """Charge l'extension Capability Advisor."""
    if g._capability_advisor is not None:
        return g._capability_advisor
    
    try:
        from extensions.capability_advisor import initialize_capability_advisor, is_available
        
        if not is_available():
            return None
        
        if archiviste_controller and memory_manager:
            g._capability_advisor = initialize_capability_advisor(
                chat_controller=chat_controller,
                archiviste_controller=archiviste_controller,
                memory_manager=memory_manager
            )
            print("[EXT-LOADER] 🎯 Capability Advisor chargé")
        return g._capability_advisor
        
    except Exception as e:
        print(f"[EXT-LOADER] ❌ Erreur Capability Advisor: {e}")
        return None


def _load_organic_planner(db_path: str = "data/agenda.db", **kwargs) -> Optional[Any]:
    """Charge l'extension Organic Planner."""
    if g._organic_planner is not None:
        return g._organic_planner
    
    try:
        from extensions.organic_planner import initialize_planner
        
        g._organic_planner = initialize_planner(db_path=db_path)
        
        if g._organic_planner:
            print("[EXT-LOADER] 📅 Organic Planner chargé")
        return g._organic_planner
        
    except Exception as e:
        print(f"[EXT-LOADER] ❌ Erreur Organic Planner: {e}")
        return None


def _load_preanalysis_optimizer(
    chat_controller=None,
    archiviste_controller=None,
    memory_manager=None,
    embedding_controller=None,
    settings_manager=None,
    **kwargs
) -> Optional[Any]:
    """Charge le module Preanalysis Optimizer."""
    if g._preanalysis_optimizer is not None:
        return g._preanalysis_optimizer
    
    try:
        from modules.preanalysis_optimizer import initialize_preanalysis
        
        g._preanalysis_optimizer = initialize_preanalysis(
            chat_controller=chat_controller,
            archiviste_controller=archiviste_controller,
            memory_manager=memory_manager,
            embedding_controller=embedding_controller,
            settings_manager=settings_manager
        )
        
        if g._preanalysis_optimizer:
            print("[EXT-LOADER] ⚡ Preanalysis Optimizer chargé")
        return g._preanalysis_optimizer
        
    except Exception as e:
        print(f"[EXT-LOADER] ❌ Erreur Preanalysis Optimizer: {e}")
        return None


def _load_memory_optimizer(
    archiviste_controller=None,
    memory_manager=None,
    embedding_controller=None,
    **kwargs
) -> Optional[Any]:
    """Charge le Memory Optimizer."""
    if g._memory_optimizer is not None:
        return g._memory_optimizer
    
    try:
        from archiviste_memory_optimizer import create_memory_optimizer
        
        if not archiviste_controller or not memory_manager:
            print("[EXT-LOADER] ⚠️ Memory Optimizer: dépendances manquantes")
            return None
        
        g._memory_optimizer = create_memory_optimizer(
            archiviste_controller=archiviste_controller,
            memory_manager=memory_manager,
            embedding_controller=embedding_controller
        )
        
        print("[EXT-LOADER] 🧠 Memory Optimizer chargé")
        return g._memory_optimizer
        
    except Exception as e:
        print(f"[EXT-LOADER] ❌ Erreur Memory Optimizer: {e}")
        return None


# ============================================================================
# DÉCHARGEMENT ET CLEANUP
# ============================================================================

def unload_extension(extension_name: str) -> bool:
    """
    Décharge une extension proprement.
    
    Args:
        extension_name: Nom de l'extension à décharger
        
    Returns:
        True si déchargement réussi
    """
    try:
        if extension_name == 'cognitive_mirror' and g._cognitive_mirror is not None:
            if hasattr(g._cognitive_mirror, 'cleanup'):
                g._cognitive_mirror.cleanup()
            g._cognitive_mirror = None
            print(f"[EXT-LOADER] 🔌 {extension_name} déchargé")
            return True
            
        elif extension_name == 'file_writer' and g._file_writer_ext is not None:
            if hasattr(g._file_writer_ext, 'cleanup'):
                g._file_writer_ext.cleanup()
            g._file_writer_ext = None
            return True
            
        elif extension_name == 'web_navigator' and g._web_navigator_ext is not None:
            if hasattr(g._web_navigator_ext, 'cleanup'):
                g._web_navigator_ext.cleanup()
            g._web_navigator_ext = None
            return True
            
        elif extension_name == 'temporal_guardian' and g._temporal_guardian is not None:
            g._temporal_guardian = None
            return True
            
        elif extension_name == 'contextual_recall' and g._contextual_recall_ext is not None:
            g._contextual_recall_ext = None
            return True
            
        elif extension_name == 'capability_advisor' and g._capability_advisor is not None:
            g._capability_advisor = None
            return True
            
        elif extension_name == 'memory_optimizer' and g._memory_optimizer is not None:
            g._memory_optimizer = None
            return True
            
        elif extension_name == 'preanalysis_optimizer' and g._preanalysis_optimizer is not None:
            g._preanalysis_optimizer = None
            return True
            
    except Exception as e:
        print(f"[EXT-LOADER] ❌ Erreur déchargement {extension_name}: {e}")
        return False
    
    return False


def unload_all_extensions():
    """Décharge toutes les extensions chargées."""
    extensions_to_unload = [
        'cognitive_mirror',
        'file_writer',
        'web_navigator', 
        'temporal_guardian',
        'contextual_recall',
        'capability_advisor',
        'memory_optimizer',
        'preanalysis_optimizer',
    ]
    
    for ext_name in extensions_to_unload:
        unload_extension(ext_name)
    
    print("[EXT-LOADER] 🔌 Toutes les extensions déchargées")


# ============================================================================
# UTILITAIRES
# ============================================================================

def get_extension_status() -> Dict[str, Dict[str, Any]]:
    """
    Retourne le statut de toutes les extensions.
    
    Returns:
        Dict avec nom extension -> {available: bool, loaded: bool, instance: Any}
    """
    status = {}
    
    extensions_globals = {
        'cognitive_mirror': g._cognitive_mirror,
        'file_writer': g._file_writer_ext,
        'web_navigator': g._web_navigator_ext,
        'temporal_guardian': g._temporal_guardian,
        'contextual_recall': g._contextual_recall_ext,
        'capability_advisor': g._capability_advisor,
        'memory_optimizer': g._memory_optimizer,
        'preanalysis_optimizer': g._preanalysis_optimizer,
    }
    
    for ext_name, instance in extensions_globals.items():
        status[ext_name] = {
            'available': _check_extension_available(ext_name),
            'loaded': instance is not None,
            'instance': instance,
        }
    
    return status


def print_extension_status():
    """Affiche le statut de toutes les extensions."""
    status = get_extension_status()
    
    print("\n" + "="*50)
    print("📦 STATUT DES EXTENSIONS OGMA")
    print("="*50)
    
    for ext_name, info in status.items():
        avail = "✅" if info['available'] else "❌"
        loaded = "🟢" if info['loaded'] else "⚪"
        print(f"  {avail} {loaded} {ext_name}")
    
    print("="*50 + "\n")


print("[OGMA-EXT-LOADER] ✅ Extensions loader chargé")
