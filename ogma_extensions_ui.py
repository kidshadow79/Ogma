"""
OGMA Extensions UI
==================
Fonctions d'initialisation et UI pour les extensions (Journal, Biography).
Extrait depuis ogma_ng.py pour modularisation.

CONTIENT :
- _initialize_biography_extension() : Init extension biographie profil
- _initialize_journal_extension() : Init extension journal de bord  
- _inject_journal_header_button() : Bouton journal dans header
- _inject_journal_context() : Injection contexte matinal
- _create_header_journal_button() : Bouton journal flottant
- _create_header_journal_button_inline() : Bouton journal inline
- _create_header_biography_button_inline() : Bouton biographie inline
"""

from nicegui import ui
from typing import Optional

# ==============================================================================
# IMPORTS CONDITIONNELS EXTENSIONS
# ==============================================================================

# BIOGRAPHIE PROFIL EXTENSION
try:
    from extensions.biographie_profil import initialize_biography_extension, is_available as biography_available, get_biography_ui
    BIOGRAPHY_EXTENSION_AVAILABLE = True
except ImportError as e:
    BIOGRAPHY_EXTENSION_AVAILABLE = False
    print(f"[EXTENSIONS-UI] BIOGRAPHY extension non disponible: {e}")

# HOLOGRAM PROJECTOR EXTENSION
try:
    from extensions.hologram_projector import initialize_hologram as _init_hologram
    HOLOGRAM_EXTENSION_AVAILABLE = True
except ImportError:
    HOLOGRAM_EXTENSION_AVAILABLE = False

# ==============================================================================
# VARIABLES GLOBALES (seront injectées depuis ogma_ng.py)
# ==============================================================================

# Ces variables seront initialisées via set_globals()
_settings_manager = None
_memory_manager = None
_chat_controller = None
_archiviste_controller = None
_status_queue = None

# États des extensions
_biography_manager = None
_biography_ui = None
_biography_available = False
_journal_instance = None
_journal_available = False


def set_globals(settings_manager, memory_manager, chat_controller, archiviste_controller, status_queue):
    """Configure les dépendances depuis ogma_ng.py"""
    global _settings_manager, _memory_manager, _chat_controller, _archiviste_controller, _status_queue
    _settings_manager = settings_manager
    _memory_manager = memory_manager
    _chat_controller = chat_controller
    _archiviste_controller = archiviste_controller
    _status_queue = status_queue


def get_biography_available():
    """Retourne l'état de disponibilité de l'extension biographie"""
    return _biography_available


def get_journal_available():
    """Retourne l'état de disponibilité de l'extension journal"""
    return _journal_available


def get_journal_instance():
    """Retourne l'instance du journal si disponible (depuis le module journal)"""
    try:
        from extensions.journal_de_bord import get_journal, is_available
        if is_available():
            return get_journal()
    except Exception:
        pass
    return None


# ==============================================================================
# INITIALISATION BIOGRAPHY
# ==============================================================================

def _initialize_biography_extension():
    """Initialise l'extension Biographie Profil si disponible"""
    global _biography_manager, _biography_ui, _biography_available

    if not BIOGRAPHY_EXTENSION_AVAILABLE:
        print("[BIOGRAPHY-EXTENSION] ❌ Extension non disponible")
        return

    try:
        # Forcer initialisation des contrôleurs si nécessaire
        from ogma_ng import _ensure_chat_controller, _ensure_archiviste_controller
        chat_ctrl = _ensure_chat_controller()
        archiviste_ctrl = _ensure_archiviste_controller()

        # Passer Archiviste + Status Queue pour notifications
        success = initialize_biography_extension(_settings_manager, _memory_manager, chat_ctrl, archiviste_ctrl, _status_queue)

        if success:
            _biography_available = True
            from extensions.biographie_profil import get_biography_manager, get_biography_ui
            _biography_manager = get_biography_manager()
            _biography_ui = get_biography_ui()
            print("[BIOGRAPHY-EXTENSION] ✅ Extension biographie_profil initialisée")
        else:
            print("[BIOGRAPHY-EXTENSION] ❌ Échec initialisation extension")

    except Exception as e:
        print(f"[BIOGRAPHY-EXTENSION] ❌ Erreur initialisation: {e}")
        import traceback
        traceback.print_exc()


# ==============================================================================
# INITIALISATION JOURNAL
# ==============================================================================

def _initialize_journal_extension():
    """Initialise l'extension Journal de Bord si disponible"""
    global _journal_instance, _journal_available

    try:
        # Import extension journal
        from extensions.journal_de_bord import initialize_journal, initialize_ui, is_available

        # Vérifier si déjà initialisé
        if is_available():
            _journal_available = True
            print("[JOURNAL-EXTENSION] OK Deja initialise et disponible")
            
            # Initialiser UI si pas encore fait
            try:
                journal = get_journal_instance()  # Utilise la fonction locale
                if journal and not journal.ui_components:
                    print("[JOURNAL-EXTENSION] UI Initialisation UI components...")
                    initialize_ui()
            except Exception as e:
                print(f"[JOURNAL-EXTENSION] ⚠️ Erreur init UI: {e}")
            
            return True

        # Tentative d'initialisation (même sans Archiviste pour l'instant)
        print("[JOURNAL-EXTENSION] Tentative d'initialisation...")

        # Création d'un mock archiviste si pas disponible
        archiviste_to_use = _archiviste_controller
        if not archiviste_to_use:
            print("[JOURNAL-EXTENSION] Archiviste non disponible - mode degrade")
            # Créer un mock simple pour permettre l'initialisation
            class MockArchiviste:
                # Attributs requis par EntryGenerator
                context_length = 4096
                max_tokens = 1024
                temperature = 0.7
                
                async def call_chat_api(self, *args, **kwargs):
                    """Mock async pour compatibilité avec LiveStateDetector - retourne JSON valide"""
                    # Retourner JSON valide pour éviter erreur de parsing
                    return '{"new_states": [], "resolved_state_ids": [], "updated_states": [], "mock": true}', None
                    
                async def call_chat_api_async(self, *args, **kwargs):
                    return '{"new_states": [], "resolved_state_ids": [], "updated_states": [], "mock": true}', None
            archiviste_to_use = MockArchiviste()

        success = initialize_journal(
            archiviste_controller=archiviste_to_use,
            memory_manager=_memory_manager
        )

        if success:
            _journal_available = True
            print("[JOURNAL-EXTENSION] OK Extension initialisee avec succes")
            
            # Initialiser UI après le core
            try:
                print("[JOURNAL-EXTENSION] UI Initialisation UI components...")
                initialize_ui()
            except Exception as e:
                print(f"[JOURNAL-EXTENSION] ⚠️ Erreur init UI: {e}")
            
            return True
        else:
            print("[JOURNAL-EXTENSION] ERREUR Echec initialisation")
            return False

    except ImportError as e:
        print(f"[JOURNAL-EXTENSION] ERREUR Extension non disponible: {e}")
        return False
    except Exception as e:
        print(f"[JOURNAL-EXTENSION] ERREUR initialisation: {e}")
        return False


# ==============================================================================
# INITIALISATION HOLOGRAM PROJECTOR
# ==============================================================================

def initialize_hologram_extension():
    """
    Enregistre la route /hologram sur le serveur NiceGUI.
    Doit être appelé après le démarrage de NiceGUI (routes FastAPI disponibles).
    """
    if not HOLOGRAM_EXTENSION_AVAILABLE:
        return False
    try:
        success = _init_hologram()
        if success:
            print("[HOLOGRAM-EXTENSION] Route /hologram enregistrée")
        return success
    except Exception as e:
        print(f"[HOLOGRAM-EXTENSION] Erreur initialisation : {e}")
        return False


# ==============================================================================
# BOUTONS HEADER JOURNAL
# ==============================================================================

def _inject_journal_header_button():
    """Injecte le bouton journal dans le header"""
    global _journal_available

    try:
        # Tentative d'initialisation si pas encore fait
        if not _journal_available:
            _initialize_journal_extension()

        # Si journal disponible, injecter bouton via UI components
        if _journal_available:
            journal = get_journal_instance()  # Utilise la fonction locale
            if journal and journal.ui_components:
                # Créer un container pour le bouton dans le header courant
                with ui.element() as header_container:
                    # Déléguer à JournalUI pour créer le bouton avec badge
                    journal.ui_components.inject_header_button(header_container)
                print("[JOURNAL-EXTENSION] OK Bouton header injecté avec UI components")
            else:
                # Fallback: ancien bouton sans badge
                from extensions.journal_de_bord import open_journal_ui
                ui.button(
                    "📔 Journal",
                    on_click=lambda: open_journal_ui()
                ).classes(
                    "journal-header-button bg-orange-600 hover:bg-orange-700 "
                    "text-white font-medium px-3 py-2 rounded-md transition-all "
                    "duration-200 shadow-sm hover:shadow-md"
                ).props('dense').style(
                    "font-size: 14px; margin-left: 16px; "
                    "background: linear-gradient(135deg, #8B5A2B 0%, #CD853F 100%); "
                    "border: 1px solid #A0522D;"
                ).tooltip("Journal de Bord - Capturer et consulter vos conversations")
                print("[JOURNAL-EXTENSION] OK Bouton header fallback injecté (sans badge)")
        else:
            print("[JOURNAL-EXTENSION] WARN Extension non disponible - bouton non injecté")

    except Exception as e:
        print(f"[JOURNAL-EXTENSION] ERROR Erreur injection bouton: {e}")


def _inject_journal_context():
    """Injecte le contexte matinal en début de conversation"""
    global _journal_available

    try:
        # Forcer l'initialisation si pas encore disponible
        if not _journal_available:
            print("[JOURNAL-EXTENSION] Extension pas disponible - tentative initialisation...")
            _initialize_journal_extension()

        if _journal_available:
            from extensions.journal_de_bord import hook_conversation_start
            context = hook_conversation_start()

            if context:
                print("[JOURNAL-EXTENSION] JOURNAL Contexte matinal injecté")
                return context

        return ""

    except Exception as e:
        print(f"[JOURNAL-EXTENSION] ERROR Erreur injection contexte: {e}")
        return ""


def _create_header_journal_button():
    """Crée le bouton journal flottant dans le header principal"""
    global _journal_available

    try:
        # Tentative d'initialisation si pas encore fait
        if not _journal_available:
            _initialize_journal_extension()

        # Si journal disponible, créer bouton flottant
        if _journal_available:
            with ui.element('div').style('position: fixed; top: 20px; left: 20px; z-index: 1000;'):
                with ui.button().classes('journal-floating-btn').props('title="Journal de Bord"').style(
                    'width: 50px; height: 50px; border-radius: 50%; '
                    'background: linear-gradient(135deg, #8B5A2B 0%, #CD853F 100%); '
                    'border: 2px solid #A0522D; box-shadow: 0 4px 12px rgba(139, 90, 43, 0.3); '
                    'display: flex; align-items: center; justify-content: center; '
                    'transition: all 0.3s ease; cursor: pointer; padding: 0;'
                ) as journal_btn:
                    # Icône livre ouvert
                    ui.html('<span style="font-size: 24px; color: white; font-weight: bold;">J</span>')

                def open_journal():
                    try:
                        from extensions.journal_de_bord import open_journal_ui
                        open_journal_ui()
                        print("[JOURNAL-EXTENSION] JOURNAL Modal journal ouvert depuis bouton header")
                    except Exception as e:
                        print(f"[JOURNAL-EXTENSION] ERROR Erreur ouverture modal: {e}")

                journal_btn.on('click', open_journal)

                # Style hover CSS
                ui.add_head_html("""
                <style>
                .journal-floating-btn:hover {
                    transform: translateY(-2px) scale(1.05);
                    box-shadow: 0 6px 20px rgba(139, 90, 43, 0.4);
                }
                </style>
                """)

            print("[JOURNAL-EXTENSION] OK Bouton journal flottant cree")
        else:
            print("[JOURNAL-EXTENSION] WARN Extension non disponible - bouton flottant non cree")

    except Exception as e:
        print(f"[JOURNAL-EXTENSION] ERROR Erreur creation bouton flottant: {e}")


def _create_header_journal_button_inline():
    """Crée le bouton journal intégré dans le conteneur header"""
    global _journal_available

    try:
        # Tentative d'initialisation si pas encore fait
        if not _journal_available:
            _initialize_journal_extension()

        # Si journal disponible, créer bouton inline
        if _journal_available:
            with ui.button().classes('journal-header-btn').props('title="Journal de Bord"').style(
                'width: 50px; height: 50px; border-radius: 50%; '
                'background: linear-gradient(135deg, #8B5A2B 0%, #CD853F 100%); '
                'border: 2px solid #A0522D; box-shadow: 0 4px 12px rgba(139, 90, 43, 0.3); '
                'display: flex; align-items: center; justify-content: center; '
                'transition: all 0.3s ease; cursor: pointer; padding: 0; '
                'flex-shrink: 0; min-width: 50px; min-height: 50px; max-width: 50px; max-height: 50px;'
            ) as journal_btn:
                # Icône livre ouvert (sans emoji Unicode)
                ui.html('<span style="font-size: 20px; color: white; font-weight: bold;">J</span>')

                def open_journal():
                    try:
                        from extensions.journal_de_bord import open_journal_ui
                        open_journal_ui()
                        print("[JOURNAL-EXTENSION] JOURNAL Modal journal ouvert depuis bouton header")
                    except Exception as e:
                        print(f"[JOURNAL-EXTENSION] ERROR Erreur ouverture modal: {e}")

                journal_btn.on('click', open_journal)

            print("[OGMA-NG] OK Bouton journal cree dans header")
        else:
            print("[OGMA-NG] WARN Journal non disponible - bouton non cree")

    except Exception as e:
        print(f"[OGMA-NG] ERROR Erreur creation bouton journal: {e}")


# ==============================================================================
# BOUTON HEADER BIOGRAPHY
# ==============================================================================

def _create_header_biography_button_inline():
    """Crée le bouton biographie profil intégré dans le conteneur header - Pattern Journal"""
    global _biography_available

    try:
        print(f"[DEBUG-BIOGRAPHY-BUTTON] === DÉBUT CRÉATION BOUTON ===")
        print(f"[DEBUG-BIOGRAPHY-BUTTON] BIOGRAPHY_EXTENSION_AVAILABLE = {BIOGRAPHY_EXTENSION_AVAILABLE}")
        print(f"[DEBUG-BIOGRAPHY-BUTTON] _biography_available (initial) = {_biography_available}")

        # Tentative d'initialisation si pas encore fait
        if not _biography_available:
            print("[DEBUG-BIOGRAPHY-BUTTON] Initialisation nécessaire, appel _initialize_biography_extension()...")
            _initialize_biography_extension()
            print(f"[DEBUG-BIOGRAPHY-BUTTON] _biography_available (après init) = {_biography_available}")

        # Condition simplifiée comme journal de bord
        if _biography_available:
            print("[DEBUG-BIOGRAPHY-BUTTON] ✅ Extension disponible, création du bouton...")
            with ui.button().classes('biography-header-btn').props('title="Biographie Profil"').style(
                'width: 50px; height: 50px; border-radius: 50%; '
                'background: linear-gradient(135deg, #4A5568 0%, #718096 100%); '
                'border: 2px solid #2D3748; box-shadow: 0 4px 12px rgba(74, 85, 104, 0.3); '
                'display: flex; align-items: center; justify-content: center; '
                'transition: all 0.3s ease; cursor: pointer; padding: 0; margin-right: 10px; '
                'flex-shrink: 0; min-width: 50px; min-height: 50px; max-width: 50px; max-height: 50px;'
            ) as biography_btn:
                # Icône plume
                ui.html('<span style="font-size: 20px; color: white; font-weight: bold;">✒️</span>')

                # Callback simplifié avec import direct (pattern journal)
                def open_biography():
                    from extensions.biographie_profil import open_settings_modal
                    open_settings_modal()
                    print("[BIOGRAPHY-EXTENSION] Modal biographie ouvert depuis bouton header")

                biography_btn.on('click', open_biography)
            print("[OGMA-NG] ✅ Bouton biographie créé dans header")
        else:
            print("[DEBUG-BIOGRAPHY-BUTTON] ❌ Extension biographie NON disponible")

        print(f"[DEBUG-BIOGRAPHY-BUTTON] === FIN CRÉATION BOUTON ===")

    except Exception as e:
        print(f"[OGMA-NG] ERROR Erreur création bouton biographie: {e}")
        import traceback
        traceback.print_exc()


# ==============================================================================
# BOUTON HEADER HOLOGRAM PROJECTOR
# ==============================================================================

def _create_header_hologram_button_inline():
    """Crée le bouton toggle hologramme dans le header OGMA."""
    if not HOLOGRAM_EXTENSION_AVAILABLE:
        return
    try:
        from .hologram_ui import create_header_button_inline as _holo_btn
        _holo_btn()
    except ImportError:
        # Import direct si appelé hors package
        from extensions.hologram_projector.hologram_ui import create_header_button_inline as _holo_btn
        _holo_btn()
    except Exception as e:
        print(f"[HOLOGRAM-UI] Erreur création bouton header: {e}")
