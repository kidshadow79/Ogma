# JOURNAL Extension Journal de Bord pour OGMA

"""
Extension Journal de Bord - Mémoire temporelle structurée pour OGMA

Fonctionnalités:
- Journal quotidien avec entrées horodatées  
- Résumés générés automatiquement par l'Archiviste
- Contexte matinal pour enrichir les conversations
- Interface de navigation temporelle (calendrier)
- Recherche et filtrage avancés
- Persistance JSON optimisée

Architecture:
- core_journal.py: Moteur principal (singleton)
- json_manager.py: Persistance et indexation JSON
- entry_generator.py: Génération résumés via Archiviste  
- context_provider.py: Injection contexte conversationnel
- ui_components.py: Interface utilisateur (bouton + modal)
- config.py: Configuration centralisée

Usage:
    from extensions.journal_de_bord import initialize_journal
    
    # Initialisation avec dépendances OGMA
    success = initialize_journal(
        archiviste_controller=archiviste_ai,
        memory_manager=memory_mgr,  # optionnel
        ui_container=ui_container   # optionnel
    )
    
    # Utilisation
    from extensions.journal_de_bord import get_journal
    journal = get_journal()
    context = journal.get_today_context()
    entry = await journal.create_entry_from_conversation()
"""

from .config import JournalConfig, get_journal_config
from .core_journal import JournalCore, JournalState

__version__ = "1.0.0"
__author__ = "OGMA Team"
__description__ = "Journal de Bord - Mémoire temporelle structurée pour OGMA"

# Instance globale (singleton pattern OGMA)
_journal_instance = None

def initialize_journal(archiviste_controller, memory_manager=None, ui_container=None) -> bool:
    """
    Initialise l'extension Journal de Bord avec les dépendances OGMA
    
    Args:
        archiviste_controller: Instance AIController pour génération résumés
        memory_manager: Instance MemoryManager OGMA (optionnel)
        ui_container: Container UI pour intégration (optionnel)
    
    Returns:
        bool: True si initialisation réussie
    
    Exemple:
        success = initialize_journal(
            archiviste_controller=archiviste_ai,
            memory_manager=memory_mgr
        )
        if success:
            print("Journal de Bord prêt !")
    """
    global _journal_instance
    
    try:
        print(f"[JOURNAL-EXTENSION] INIT Initialisation Journal de Bord v{__version__}")
        
        # Validation des dépendances critiques
        if not archiviste_controller:
            raise ValueError("archiviste_controller est obligatoire pour la génération de résumés")
        
        print("[JOURNAL-EXTENSION] CONFIG Création instance JournalCore...")
        
        # Création instance singleton
        config = get_journal_config()
        _journal_instance = JournalCore(config=config)
        
        # Initialisation des composants
        print("[JOURNAL-EXTENSION] SETUP Initialisation des composants...")
        success = _journal_instance.initialize(
            archiviste_controller=archiviste_controller,
            memory_manager=memory_manager,
            ui_container=ui_container
        )
        
        if success:
            print("[JOURNAL-EXTENSION] OK Extension initialisée avec succès")
            print(f"[JOURNAL-EXTENSION] État: {'ACTIVÉ' if _journal_instance.is_enabled() else 'DÉSACTIVÉ'}")
            
            # Affichage des statistiques initiales
            stats = _journal_instance.get_journal_stats()
            print(f"[JOURNAL-EXTENSION] STATS Journal: {stats['total_entries']} entrées sur {stats['days_with_entries']} jours")
            
            # Initialisation Option C - Purge Manager
            try:
                print("[JOURNAL-EXTENSION] OPTION-C Initialisation PurgeManager...")
                from .purge_manager import initialize_purge_manager
                purge_mgr = initialize_purge_manager(
                    json_manager=_journal_instance.json_manager,
                    memory_manager=memory_manager,
                    archiviste_controller=archiviste_controller
                )
                if purge_mgr:
                    print("[JOURNAL-EXTENSION] ✅ PurgeManager opérationnel")
                else:
                    print("[JOURNAL-EXTENSION] ⚠️ PurgeManager non disponible")
            except Exception as e:
                print(f"[JOURNAL-EXTENSION] WARN PurgeManager init failed: {e}")
            
            # Initialisation Option C - Scheduler
            try:
                print("[JOURNAL-EXTENSION] OPTION-C Initialisation Scheduler...")
                from .scheduler import initialize_scheduler
                from pathlib import Path
                # settings_path depuis json_manager.data_dir (pas config)
                settings_path = Path(_journal_instance.json_manager.data_dir) / "journal_settings.json"
                
                scheduler = initialize_scheduler(
                    json_manager=_journal_instance.json_manager,
                    purge_manager=purge_mgr if 'purge_mgr' in locals() else None,
                    archiviste_controller=archiviste_controller,
                    settings_path=settings_path,
                    auto_start=False  # Démarrage manuel via UI
                )
                if scheduler:
                    print("[JOURNAL-EXTENSION] ✅ Scheduler opérationnel (auto_start=False)")
                else:
                    print("[JOURNAL-EXTENSION] ⚠️ Scheduler non disponible")
            except Exception as e:
                print(f"[JOURNAL-EXTENSION] WARN Scheduler init failed: {e}")
            
            # Initialisation LiveStateDetector - Détection EN LIVE
            try:
                print("[JOURNAL-EXTENSION] LIVE-DETECT Initialisation détecteur états live...")
                from .live_state_detector import initialize_live_detector
                live_detector = initialize_live_detector(
                    json_manager=_journal_instance.json_manager,
                    archiviste_controller=archiviste_controller
                )
                if live_detector:
                    print("[JOURNAL-EXTENSION] ✅ LiveStateDetector opérationnel")
                else:
                    print("[JOURNAL-EXTENSION] ⚠️ LiveStateDetector non disponible")
            except Exception as e:
                print(f"[JOURNAL-EXTENSION] WARN LiveStateDetector init failed: {e}")
            
            # Initialisation CorrectionLearner - Apprentissage par correction
            try:
                print("[JOURNAL-EXTENSION] CORRECTION Initialisation CorrectionLearner...")
                from .correction_learner import initialize_correction_learner
                corr_ok = initialize_correction_learner(
                    json_manager=_journal_instance.json_manager,
                    archiviste_controller=archiviste_controller,
                    memory_manager=memory_manager
                )
                if corr_ok:
                    print("[JOURNAL-EXTENSION] ✅ CorrectionLearner opérationnel")
                else:
                    print("[JOURNAL-EXTENSION] ⚠️ CorrectionLearner non disponible")
            except Exception as e:
                print(f"[JOURNAL-EXTENSION] WARN CorrectionLearner init failed: {e}")
            
            # Initialisation CuriosityEngine - Curiosité autonome
            try:
                print("[JOURNAL-EXTENSION] CURIOSITY Initialisation CuriosityEngine...")
                from .curiosity_engine import initialize_curiosity_engine
                curio_ok = initialize_curiosity_engine(
                    json_manager=_journal_instance.json_manager,
                    archiviste_controller=archiviste_controller
                )
                if curio_ok:
                    print("[JOURNAL-EXTENSION] ✅ CuriosityEngine opérationnel")
                else:
                    print("[JOURNAL-EXTENSION] ⚠️ CuriosityEngine non disponible")
            except Exception as e:
                print(f"[JOURNAL-EXTENSION] WARN CuriosityEngine init failed: {e}")
        else:
            print("[JOURNAL-EXTENSION] ERROR Erreur lors de l'initialisation")
            _journal_instance = None
            
        return success
        
    except Exception as e:
        print(f"[JOURNAL-EXTENSION] ERROR Erreur initialisation: {e}")
        _journal_instance = None
        return False

def get_journal() -> JournalCore:
    """
    Retourne l'instance singleton du Journal de Bord
    
    Returns:
        JournalCore: Instance principale ou None si non initialisé
    
    Raises:
        RuntimeError: Si le journal n'est pas initialisé
    
    Exemple:
        journal = get_journal()
        context = journal.get_today_context()
    """
    if _journal_instance is None:
        raise RuntimeError("Journal non initialisé - appelez initialize_journal() d'abord")
    return _journal_instance

def is_available() -> bool:
    """
    Vérifie si l'extension est disponible et fonctionnelle
    
    Returns:
        bool: True si journal initialisé et prêt
    """
    return _journal_instance is not None and _journal_instance.is_ready()

def update_archiviste(archiviste_controller) -> bool:
    """
    Met à jour l'archiviste du journal (utile si initialisé avec MockArchiviste)
    
    Args:
        archiviste_controller: Nouvelle instance AIController
        
    Returns:
        bool: True si mise à jour réussie
    """
    if _journal_instance is not None:
        return _journal_instance.update_archiviste(archiviste_controller)
    return False

def initialize_ui() -> bool:
    """
    Initialise ou réinitialise l'interface utilisateur du journal
    
    Returns:
        bool: True si initialisation UI réussie
    
    Usage:
        # Initialiser l'UI après que le journal soit prêt
        from extensions.journal_de_bord import initialize_ui
        success = initialize_ui()
    """
    if _journal_instance is None:
        print("[JOURNAL-UI-INIT] Erreur: Journal non initialisé")
        return False
        
    try:
        from .ui_components import JournalUI
        
        # JournalUI attend: config, core_journal, json_manager
        _journal_instance.ui_components = JournalUI(
            config=_journal_instance.config,
            core_journal=_journal_instance,
            json_manager=_journal_instance.json_manager
        )
        print("[JOURNAL-UI-INIT] ✅ Interface UI initialisée")
        return True
    except Exception as e:
        print(f"[JOURNAL-UI-INIT] ❌ Erreur initialisation UI: {e}")
        import traceback
        traceback.print_exc()
        return False

def is_enabled() -> bool:
    """
    Vérifie si l'extension est actuellement activée
    
    Returns:
        bool: True si journal disponible et activé par utilisateur
    """
    return is_available() and _journal_instance.is_enabled()

def get_today_context() -> str:
    """
    Raccourci pour obtenir le contexte de la journée actuelle
    
    Returns:
        str: Contexte formaté pour injection en début de conversation
    
    Exemple:
        context = get_today_context()
        if context:
            # Injecter context dans la conversation
    """
    if is_available():
        return _journal_instance.get_today_context()
    return ""

async def create_manual_entry(conversation_id: str = None, **metadata) -> bool:
    """
    Raccourci pour créer une entrée manuelle
    
    Args:
        conversation_id: ID de la conversation à résumer
        **metadata: Métadonnées additionnelles
    
    Returns:
        bool: True si entrée créée avec succès
    
    Exemple:
        success = await create_manual_entry(
            conversation_id="current_conv",
            title="Discussion technique importante"
        )
    """
    if is_available():
        entry = await _journal_instance.create_entry_from_conversation(
            conversation_id=conversation_id, 
            **metadata
        )
        return entry is not None
    return False

def search_journal(query: str = None, **filters) -> list:
    """
    Raccourci pour rechercher dans le journal
    
    Args:
        query: Texte de recherche libre
        **filters: Filtres (date_start, date_end, tags, importance)
    
    Returns:
        list: Liste des entrées correspondantes
    
    Exemple:
        results = search_journal(
            query="cognitive mirror",
            date_start="2024-09-01",
            importance="high"
        )
    """
    if is_available():
        return _journal_instance.search_entries(query=query, **filters)
    return []

def get_journal_stats() -> dict:
    """
    Raccourci pour obtenir les statistiques du journal
    
    Returns:
        dict: Statistiques complètes du journal
    
    Exemple:
        stats = get_journal_stats()
        print(f"Total: {stats['total_entries']} entrées")
    """
    if is_available():
        return _journal_instance.get_journal_stats()
    return {
        "available": False,
        "enabled": False,
        "error": "Extension non initialisée"
    }

def toggle_journal() -> bool:
    """
    Bascule l'état ON/OFF de l'extension
    
    Returns:
        bool: Nouvel état (True=ON, False=OFF)
    
    Exemple:
        new_state = toggle_journal()
        print(f"Journal: {'ON' if new_state else 'OFF'}")
    """
    if is_available():
        return _journal_instance.config.toggle_enabled()
    return False

def get_ui_components() -> dict:
    """
    Retourne les composants UI pour intégration dans OGMA
    
    Returns:
        dict: Composants UI (bouton, modal, etc.)
    
    Usage OGMA:
        ui_components = get_ui_components()
        header_button = ui_components.get('header_button')
    """
    if is_available() and _journal_instance.ui_components:
        return _journal_instance.ui_components.get_components()
    return {}

def get_ui_component():
    """
    Retourne l'instance UI pour accès direct aux méthodes
    
    Returns:
        JournalUI: Instance UI du journal ou None
    
    Usage OGMA:
        ui = get_ui_component()
        if ui and hasattr(ui, 'inject_header_button'):
            ui.inject_header_button(container)
    """
    if is_available():
        return _journal_instance.ui_components
    return None

async def open_journal_ui():
    """
    Ouvre l'interface principale du journal (modal)
    
    Exemple:
        # Lié au clic sur le bouton header
        await open_journal_ui()
    """
    if is_available() and _journal_instance.ui_components:
        await _journal_instance.ui_components.open_main_modal()
    else:
        print("[JOURNAL-EXTENSION] WARN Interface non disponible")

def set_callbacks(**callbacks):
    """
    Configure les callbacks d'événements du journal
    
    Args:
        on_entry_created: Callback(entry_data) - nouvelle entrée créée
        on_context_requested: Callback(date, context) - contexte demandé
        on_state_changed: Callback(old_state, new_state) - changement d'état
        on_error: Callback(error_type, message) - erreur survenue
    
    Exemple:
        def on_new_entry(entry):
            print(f"Nouvelle entrée: {entry['summary'][:50]}...")
        
        set_callbacks(on_entry_created=on_new_entry)
    """
    if is_available():
        for callback_name, callback_func in callbacks.items():
            if hasattr(_journal_instance, callback_name):
                setattr(_journal_instance, callback_name, callback_func)
                print(f"[JOURNAL-EXTENSION] OK Callback {callback_name} configuré")
            else:
                print(f"[JOURNAL-EXTENSION] WARN Callback inconnu: {callback_name}")

def cleanup():
    """
    Nettoyage et fermeture propre de l'extension
    
    Usage:
        # Appelé lors de la fermeture d'OGMA
        cleanup()
    """
    global _journal_instance
    
    if _journal_instance:
        print("[JOURNAL-EXTENSION] UPDATE Fermeture Journal de Bord")
        _journal_instance.cleanup()
        _journal_instance = None
        print("[JOURNAL-EXTENSION] OK Extension fermée proprement")

# === HOOKS POUR INTÉGRATION OGMA ===

def hook_conversation_start():
    """
    Hook appelé au début d'une nouvelle conversation
    Injecte automatiquement le contexte du jour
    
    Returns:
        str: Contexte à injecter ou chaîne vide
    """
    if not is_enabled():
        return ""
    
    try:
        context = get_today_context()
        if context:
            print("[JOURNAL-EXTENSION] JOURNAL Contexte matinal injecté")
        return context
    except Exception as e:
        print(f"[JOURNAL-EXTENSION] ERROR Erreur hook conversation: {e}")
        return ""

def hook_message_sent():
    """
    Hook appelé après l'envoi d'un message utilisateur
    Peut être utilisé pour le suivi automatique des conversations
    """
    if is_available():
        _journal_instance.last_activity_time = time.time()

# === INTÉGRATION HEADER OGMA ===

def inject_header_button(header_container):
    """
    Injecte le bouton journal dans le header OGMA
    
    Args:
        header_container: Container du header OGMA
    
    Usage OGMA:
        from extensions.journal_de_bord import inject_header_button
        inject_header_button(header_container)
    """
    if not is_available() or not _journal_instance.ui_components:
        print("[JOURNAL-EXTENSION] WARN Interface non disponible pour injection header")
        return
    
    try:
        _journal_instance.ui_components.inject_header_button(header_container)
        print("[JOURNAL-EXTENSION] OK Bouton journal ajouté au header")
    except Exception as e:
        print(f"[JOURNAL-EXTENSION] ERROR Erreur injection header: {e}")

# === FONCTIONS OPTION C ===

def get_purge_manager():
    """
    Retourne l'instance PurgeManager pour opérations de purge
    
    Returns:
        PurgeManager: Instance ou None si non initialisé
    
    Exemple:
        from extensions.journal_de_bord import get_purge_manager
        purge_mgr = get_purge_manager()
        if purge_mgr:
            entries = purge_mgr.get_purgeable_entries(age_days=90)
    """
    try:
        from .purge_manager import get_purge_manager as _get_purge
        return _get_purge()
    except ImportError:
        return None

def get_scheduler():
    """
    Retourne l'instance MaintenanceScheduler pour gestion maintenance
    
    Returns:
        MaintenanceScheduler: Instance ou None si non initialisé
    
    Exemple:
        from extensions.journal_de_bord import get_scheduler
        scheduler = get_scheduler()
        if scheduler:
            scheduler.start()
    """
    try:
        from .scheduler import get_scheduler as _get_sched
        return _get_sched()
    except ImportError:
        return None

def get_auto_resolution_functions():
    """
    Retourne les fonctions d'auto-résolution
    
    Returns:
        dict: {'detect_inactive_states': func, 'auto_resolve_states': func}
    
    Exemple:
        from extensions.journal_de_bord import get_auto_resolution_functions
        funcs = get_auto_resolution_functions()
        if funcs:
            inactive = funcs['detect_inactive_states'](json_manager, threshold_days=30)
    """
    try:
        from .auto_resolution import detect_inactive_states, auto_resolve_states
        return {
            'detect_inactive_states': detect_inactive_states,
            'auto_resolve_states': auto_resolve_states
        }
    except ImportError:
        return None

def get_live_detector():
    """
    Retourne l'instance LiveStateDetector pour détection états en temps réel
    
    Returns:
        LiveStateDetector: Instance ou None si non initialisé
    
    Exemple:
        from extensions.journal_de_bord import get_live_detector
        detector = get_live_detector()
        if detector:
            result = await detector.analyze_message_pair(user_msg, ai_msg)
    """
    try:
        from .live_state_detector import get_live_detector as _get_detector
        return _get_detector()
    except ImportError:
        return None

async def hook_message_exchange(
    user_message: str, 
    ai_response: str, 
    conversation_context: list = None,
    conversation_id: str = None
):
    """
    Hook appelé après chaque échange utilisateur↔IA
    Permet détection live d'états actifs pendant conversation
    
    Args:
        user_message: Message de l'utilisateur
        ai_response: Réponse de l'IA
        conversation_context: Historique conversation (optionnel)
        conversation_id: ID conversation pour traçabilité (optionnel)
    
    Returns:
        dict: Changements détectés (new_states, resolved_states, updated_states)
    
    Usage OGMA:
        # Dans send_chat_message, après génération réponse IA
        from extensions.journal_de_bord import hook_message_exchange
        changes = await hook_message_exchange(
            user_text, ai_response, _chat_history, conversation_id=_current_conversation_id
        )
    """
    if not is_available():
        return {"new_states": [], "resolved_states": [], "updated_states": []}
    
    try:
        detector = get_live_detector()
        if not detector:
            return {"new_states": [], "resolved_states": [], "updated_states": []}
        
        result = await detector.analyze_message_pair(
            user_message=user_message,
            ai_response=ai_response,
            conversation_context=conversation_context,
            conversation_id=conversation_id
        )
        
        # Log si changements détectés
        if any([result["new_states"], result["resolved_states"], result["updated_states"]]):
            print(f"[JOURNAL-LIVE] 🎯 Changements détectés: "
                  f"{len(result['new_states'])} nouveaux, "
                  f"{len(result['resolved_states'])} résolus, "
                  f"{len(result['updated_states'])} màj")
        
        # === CORRECTION LEARNER : Détecter corrections utilisateur ===
        try:
            from .correction_learner import analyze_for_corrections
            correction = await analyze_for_corrections(
                user_message=user_message,
                ai_response=ai_response,
                conversation_context=conversation_context,
                conversation_id=conversation_id
            )
            if correction:
                result["correction"] = correction
                print(f"[JOURNAL-LIVE] 📝 Correction detectee: {correction.get('lecon', '?')[:60]}")
        except Exception as e:
            print(f"[JOURNAL-LIVE] WARN CorrectionLearner: {e}")
        
        # === CURIOSITY ENGINE : Détecter sujets de curiosité ===
        try:
            from .curiosity_engine import detect_curiosities
            curiosities = await detect_curiosities(
                user_message=user_message,
                ai_response=ai_response,
                conversation_context=conversation_context,
                conversation_id=conversation_id
            )
            if curiosities:
                result["curiosities"] = curiosities
                print(f"[JOURNAL-LIVE] 🔍 {len(curiosities)} curiosite(s) detectee(s)")
        except Exception as e:
            print(f"[JOURNAL-LIVE] WARN CuriosityEngine: {e}")
        
        return result
        
    except Exception as e:
        print(f"[JOURNAL-EXTENSION] ERROR Hook message exchange: {e}")
        return {"new_states": [], "resolved_states": [], "updated_states": []}

# Points d'entrée publics pour intégration OGMA
__all__ = [
    # Initialisation et lifecycle
    'initialize_journal',
    'cleanup',
    
    # Accès à l'instance
    'get_journal',
    'is_available', 
    'is_enabled',
    
    # Fonctionnalités principales
    'get_today_context',
    'create_manual_entry',
    'search_journal',
    'get_journal_stats',
    'toggle_journal',
    
    # Interface utilisateur
    'get_ui_components',
    'open_journal_ui',
    'inject_header_button',
    
    # Hooks OGMA
    'hook_conversation_start',
    'hook_message_sent',
    'hook_message_exchange',  # NOUVEAU - Détection live
    
    # Configuration
    'set_callbacks',
    'get_journal_config',
    
    # Option C - Maintenance
    'get_purge_manager',
    'get_scheduler',
    'get_auto_resolution_functions',
    'get_live_detector',  # NOUVEAU
    
    # Classes principales
    'JournalCore',
    'JournalConfig',
    'JournalState'
]