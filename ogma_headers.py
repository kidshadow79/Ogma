"""
OGMA Headers
============
Interface d'en-tête et indicateurs de statut.

CONTIENT :
- En-tête principal de l'application
- Indicateurs de statut IA                         # Ouvre le popup de paramètres au lieu de faire un toggle
                        if hasattr(cognitive_mirror, 'ui_components') and cognitive_mirror.ui_components:
                            print("[SUBCONSCIENCE] CONFIG Ouverture popup paramètres...")
                            cognitive_mirror.ui_components.show_parameters_popup()
                            print("[SUBCONSCIENCE] OK Popup paramètres ouvert")
                        else:
                            print("[SUBCONSCIENCE] ERROR UI components non disponibles")
                            # Fallback: log l'état actuel pour debug
                            current_state = cognitive_mirror.is_enabled()
                            print(f"[SUBCONSCIENCE] STATS État actuel: {current_state}")hiviste, Embeddings)
- Bouton Archi Sensor flottant
- Gestion des conteneurs d'en-tête
"""

from nicegui import ui


def _get_ogma_ng_function(func_name):
    """Helper pour récupérer une fonction d'ogma_ng"""
    try:
        import sys
        ogma_ng = sys.modules.get('ogma_ng')
        if ogma_ng and hasattr(ogma_ng, func_name):
            return getattr(ogma_ng, func_name)
        return None
    except Exception:
        return None


def _get_global_var(var_name, default=None):
    """Helper pour accéder aux variables globales d'ogma_ng"""
    try:
        import sys
        ogma_ng = sys.modules.get('ogma_ng')
        if ogma_ng and hasattr(ogma_ng, var_name):
            return getattr(ogma_ng, var_name)
        return default
    except Exception:
        return default


def _get_current_conversation_id():
    """Récupère l'ID de la conversation actuelle depuis OGMA"""
    try:
        current_id = _get_global_var('_current_conversation_id')
        if current_id:
            print(f"[JOURNAL] Conversation actuelle trouvée: {current_id}")
            return current_id
        else:
            # Fallback: générer un ID temporaire
            import uuid
            temp_id = f"temp_conv_{uuid.uuid4().hex[:8]}"
            print(f"[JOURNAL] Aucune conversation active, ID temporaire: {temp_id}")
            return temp_id
    except Exception as e:
        print(f"[JOURNAL] Erreur récupération conversation ID: {e}")
        import uuid
        return f"error_conv_{uuid.uuid4().hex[:8]}"


def _status_dot(initial='#dc2626'):
    """Crée un indicateur de statut coloré"""
    # Import de la fonction depuis ogma_displays
    try:
        from ogma_displays import _status_dot as status_dot_func
        return status_dot_func(initial)
    except ImportError:
        # Fallback simple si ogma_displays n'est pas disponible
        return ui.element('div').style(f'width: 12px; height: 12px; border-radius: 50%; display: inline-block; margin-right: 4px; background: {initial};').classes('status-dot')


def _header():
    """Crée l'en-tête principal de l'application avec indicateurs de statut IA"""
    # Accès aux variables globales
    _header_container = _get_global_var('_header_container')
    _ia_status_indicators = _get_global_var('_ia_status_indicators', {})

    with ui.element('div').classes('app-header'):
        # Container flex pour titre centré et indicateurs IA
        with ui.element('div').classes('header-content').style('display: flex; align-items: center; width: 100%; position: relative;'):

            header_container = ui.element('div').classes('header-title-container')
            with header_container:
                # Titre descriptif supprimé pour économiser l'espace
                pass

            # Mettre à jour la variable globale
            try:
                import sys
                ogma_ng = sys.modules.get('ogma_ng')
                if ogma_ng:
                    ogma_ng._header_container = header_container
            except Exception:
                pass

            # Indicateurs d'état IA dans le header
            with ui.element('div').classes('ia-status-container').style('display: flex; align-items: center; gap: 16px; position: absolute; left: 50%; transform: translateX(-50%); justify-content: center;'):
                # IA PRINCIPALE (Chat)
                with ui.element('div').classes('ia-status-item').style('display: flex; align-items: center; gap: 6px;'):
                    chat_dot = _status_dot(initial='#dc2626')  # Rouge par défaut
                    with ui.element('div').style('display: flex; flex-direction: column; font-size: 12px;'):
                        ui.label('IA PRINCIPALE').classes('text-xs font-semibold').style('color: var(--text-primary); margin: 0; line-height: 1.2;')
                        chat_model = ui.label('Aucun modèle').classes('text-xs').style('color: var(--text-muted); margin: 0; line-height: 1.2;')

                # ARCHIVISTE
                with ui.element('div').classes('ia-status-item').style('display: flex; align-items: center; gap: 6px;'):
                    archiviste_dot = _status_dot(initial='#dc2626')  # Rouge par défaut
                    with ui.element('div').style('display: flex; flex-direction: column; font-size: 12px;'):
                        ui.label('ARCHIVISTE').classes('text-xs font-semibold').style('color: var(--text-primary); margin: 0; line-height: 1.2;')
                        archiviste_model = ui.label('Aucun modèle').classes('text-xs').style('color: var(--text-muted); margin: 0; line-height: 1.2;')

                # IA EMBED
                with ui.element('div').classes('ia-status-item').style('display: flex; align-items: center; gap: 6px;'):
                    embeddings_dot = _status_dot(initial='#dc2626')  # Rouge par défaut
                    with ui.element('div').style('display: flex; flex-direction: column; font-size: 12px;'):
                        ui.label('IA EMBED').classes('text-xs font-semibold').style('color: var(--text-primary); margin: 0; line-height: 1.2;')
                        embeddings_model = ui.label('Aucun modèle').classes('text-xs').style('color: var(--text-muted); margin: 0; line-height: 1.2;')

        # Mettre à jour les indicateurs globaux
        try:
            import sys
            ogma_ng = sys.modules.get('ogma_ng')
            if ogma_ng and hasattr(ogma_ng, '_ia_status_indicators'):
                ogma_ng._ia_status_indicators.update({
                    'chat_dot': chat_dot,
                    'chat_model': chat_model,
                    'archiviste_dot': archiviste_dot,
                    'archiviste_model': archiviste_model,
                    'embeddings_dot': embeddings_dot,
                    'embeddings_model': embeddings_model
                })
        except Exception:
            pass

    # [ARCHI_SENSOR] et [PERCEPTION] - Boutons extensions à droite
    _archi_sensor_modal = _get_ogma_ng_function('_archi_sensor_modal')
    archi_sensor_overlay = _archi_sensor_modal() if _archi_sensor_modal else None

    # [PERCEPTION] Vérifier disponibilité extension (plus d'overlay)
    try:
        from extensions.perception_ui import get_perception_ui
        perception_ui = get_perception_ui()
        perception_available = perception_ui is not None
    except ImportError:
        perception_available = False

    with ui.element('div').style('display: flex; align-items: center; gap: 8px; position: fixed; top: 16px; right: 16px; z-index: 999;'):
        # Bouton Journal de Bord
        journal_btn = ui.button(icon='book').classes('settings-floating-btn').props('title="Journal de Bord"')

        # Bouton Biographie Profil
        biography_btn = ui.button(icon='person').classes('settings-floating-btn').props('title="Biographie Profil"')

        # Bouton Analyse Métacognitive avec icône "M" interne
        archi_sensor_btn = ui.button(icon='psychology').classes('settings-floating-btn').props('title="Analyse Métacognitive"')

        # Bouton Perception avec style paramètres généraux
        perception_btn = ui.button(icon='visibility').classes('settings-floating-btn').props('title="Vision Perception"')

        # Bouton Cognitive Mirror - Transparence cognitive
        cognitive_mirror_btn = ui.button(icon='psychology_alt').classes('settings-floating-btn q-btn--secondary').props('title="Cognitive Mirror - Réflexion visible"')

        def toggle_journal():
            """Créé une entrée de journal à partir de la conversation actuelle"""
            try:
                print("[JOURNAL] Clic bouton - création entrée de journal")
                from extensions.journal_de_bord import create_manual_entry, is_available
                import asyncio

                if is_available():
                    # Récupération de la conversation actuelle depuis OGMA
                    current_conversation_id = _get_current_conversation_id()
                    
                    # 🔧 FIX: Récupérer l'historique de conversation réel
                    chat_history_ui = _get_global_var('_chat_history_ui', [])
                    print(f"[JOURNAL] Historique récupéré: {len(chat_history_ui)} messages")
                    
                    # Capturer le contexte UI avant la tâche asynchrone
                    from nicegui import context
                    current_context = context.client

                    # Création asynchrone de l'entrée
                    async def create_entry():
                        try:
                            print(f"[JOURNAL] Création entrée pour conversation: {current_conversation_id}")
                            success = await create_manual_entry(
                                conversation_id=current_conversation_id,
                                conversation_history=chat_history_ui,  # 🔧 FIX: Passer l'historique réel
                                source="button_click",
                                manual=True
                            )

                            # Utilisation du contexte capturé pour les notifications
                            with current_context:
                                if success:
                                    print("[JOURNAL] Entrée créée avec succès")
                                    ui.notify("✅ Conversation ajoutée au journal", type='positive')
                                else:
                                    print("[JOURNAL] Échec création entrée")
                                    ui.notify("Erreur lors de la création de l'entrée", type='negative')
                        except Exception as e:
                            print(f"[JOURNAL] Erreur création entrée: {e}")
                            with current_context:
                                ui.notify("Erreur lors de la création de l'entrée", type='negative')

                    # Exécution asynchrone
                    asyncio.create_task(create_entry())

                else:
                    print("[JOURNAL] Extension non disponible")
                    ui.notify("Journal de Bord non disponible", type='warning')
            except Exception as e:
                print(f"[JOURNAL] Erreur traitement journal: {e}")
                ui.notify("Erreur Journal de Bord", type='negative')

        def toggle_biography():
            """Ouvre la modal de paramètres de l'extension Biographie Profil"""
            try:
                print("[BIOGRAPHY] Clic bouton - ouverture modal paramètres")
                from extensions.biographie_profil import open_settings_modal, is_available

                if is_available():
                    success = open_settings_modal()
                    if success:
                        print("[BIOGRAPHY] Modal paramètres ouverte avec succès")
                    else:
                        print("[BIOGRAPHY] Erreur ouverture modal paramètres")
                        ui.notify("Erreur ouverture paramètres biographie", type='negative')
                else:
                    print("[BIOGRAPHY] Extension non disponible")
                    ui.notify("Extension Biographie Profil non disponible", type='warning')
            except Exception as e:
                print(f"[BIOGRAPHY] Erreur traitement biographie: {e}")
                ui.notify("Erreur Extension Biographie Profil", type='negative')

        def toggle_archi_sensor():
            if archi_sensor_overlay:
                archi_sensor_overlay.visible = not archi_sensor_overlay.visible
                print(f"[ARCHI-SENSOR] Overlay {'affiché' if archi_sensor_overlay.visible else 'masqué'}")
            else:
                print("[ARCHI-SENSOR] Overlay non disponible")

        def open_perception_page():
            """Ouvre la page Perception dans une fenêtre popup dédiée"""
            print("[PERCEPTION] Ouverture fenêtre popup /perception")
            # Popup compacte carrée 440×440 (optimale pour stream uniquement)
            ui.run_javascript('''
                window.open(
                    '/perception',
                    'PerceptionWindow',
                    'width=440,height=440,left=100,top=100,menubar=no,toolbar=no,location=no,status=no,resizable=yes,scrollbars=auto'
                );
            ''')

        def toggle_cognitive_mirror():
            """Ouvre le popup de paramètres Subconscience au lieu de faire un toggle"""
            try:
                print("[SUBCONSCIENCE] CLICK Clic bouton - ouverture popup paramètres")
                _ensure_cognitive_mirror = _get_ogma_ng_function('_ensure_cognitive_mirror')
                if _ensure_cognitive_mirror:
                    print("[SUBCONSCIENCE] SEARCH Fonction _ensure_cognitive_mirror trouvée")
                    cognitive_mirror = _ensure_cognitive_mirror()
                    if cognitive_mirror:
                        print("[SUBCONSCIENCE] BRAIN Extension obtenue")
                        
                        # Ouvre le popup de paramètres au lieu de faire un toggle
                        if hasattr(cognitive_mirror, 'ui_components') and cognitive_mirror.ui_components:
                            print("[SUBCONSCIENCE] CONFIG Ouverture popup paramètres...")
                            cognitive_mirror.ui_components.show_parameters_popup()
                            print("[SUBCONSCIENCE] OK Popup paramètres ouvert")
                        else:
                            print("[SUBCONSCIENCE] ERROR UI components non disponibles")
                            # Fallback: log l'état actuel pour debug
                            current_state = cognitive_mirror.is_enabled()
                            print(f"[SUBCONSCIENCE] STATS État actuel: {current_state}")
                    else:
                        print("[SUBCONSCIENCE] ERROR Extension non initialisée")
                else:
                    print("[SUBCONSCIENCE] ERROR Fonction _ensure_cognitive_mirror non trouvée")
            except Exception as e:
                print(f"[SUBCONSCIENCE] ERROR Erreur ouverture popup: {e}")
                import traceback
                traceback.print_exc()

        journal_btn.on('click', toggle_journal)
        biography_btn.on('click', toggle_biography)
        archi_sensor_btn.on('click', toggle_archi_sensor)
        perception_btn.on('click', open_perception_page)
        cognitive_mirror_btn.on('click', toggle_cognitive_mirror)
        
        # Synchronisation initiale du bouton Cognitive Mirror
        def sync_cognitive_mirror_button():
            """Synchronise l'apparence du bouton avec l'état réel de l'extension"""
            try:
                _ensure_cognitive_mirror = _get_ogma_ng_function('_ensure_cognitive_mirror')
                if _ensure_cognitive_mirror:
                    cognitive_mirror = _ensure_cognitive_mirror()
                    if cognitive_mirror:
                        current_state = cognitive_mirror.is_enabled
                        print(f"[COGNITIVE-MIRROR] UPDATE Synchronisation bouton: état réel = {current_state}")
                        
                        # Mise à jour visuelle bouton selon état réel
                        icon = 'psychology' if current_state else 'psychology_alt'
                        color = 'primary' if current_state else 'secondary'
                        
                        # Mise à jour icône
                        cognitive_mirror_btn.props(f'icon={icon}')
                        
                        # Mise à jour classes CSS - Méthode correcte NiceGUI
                        if current_state:
                            # État activé
                            cognitive_mirror_btn.classes(add='q-btn--primary')
                            cognitive_mirror_btn.classes(remove='q-btn--secondary')
                        else:
                            # État désactivé
                            cognitive_mirror_btn.classes(add='q-btn--secondary') 
                            cognitive_mirror_btn.classes(remove='q-btn--primary')
                        
                        print(f"[COGNITIVE-MIRROR] STYLE Bouton synchronisé: icon={icon}, color={color}")
                    else:
                        print("[COGNITIVE-MIRROR] CONFIG Extension non initialisée pour synchronisation")
                else:
                    print("[COGNITIVE-MIRROR] CONFIG Fonction _ensure_cognitive_mirror non disponible")
            except Exception as e:
                print(f"[COGNITIVE-MIRROR] WARN Erreur synchronisation bouton: {e}")
        
        # Appel de synchronisation avec délai pour laisser le temps à l'extension de s'initialiser
        import threading
        def delayed_sync():
            import time
            time.sleep(1)  # Attendre 1 seconde
            sync_cognitive_mirror_button()
        
        sync_thread = threading.Thread(target=delayed_sync, daemon=True)
        sync_thread.start()


# ============================================================================
# PERCEPTION OVERLAY - SINGLETON PATTERN
