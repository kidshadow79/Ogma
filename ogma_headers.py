"""
OGMA Headers
============
Interface d'en-tête et indicateurs de statut.

CONTIENT :
- En-tête principal de l'application
- Indicateurs de statut IA (Chat, Archiviste, Embeddings)
- Bouton Archi Sensor flottant
- Gestion des conteneurs d'en-tête
"""

from nicegui import ui


def _show_organic_planner_dialog():
    """Alias dynamique vers _show_organic_planner_dialog dans ogma_modals"""
    try:
        from ogma_modals import _show_organic_planner_dialog as show_dialog
        return show_dialog()
    except Exception as e:
        print(f"[HEADERS] Erreur ouverture Organic Planner: {e}")
        ui.notify("Erreur ouverture Organic Planner", type='negative')


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
        return ui.element('div').style(f'width: 12px; height: 12px; border-radius: 50%; display: inline-block; margin-right: 4px; background: {initial};').classes('status-dot cyber-dot')


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
                    # Spinner d'activité IA Principale (vert)
                    chat_spinner = ui.spinner('audio', size='md').props('color="green"').style('display: none;')
                    with ui.element('div').style('display: flex; flex-direction: column; font-size: 12px;'):
                        ui.label('IA PRINCIPALE').classes('text-xs font-semibold').style('color: var(--text-primary); margin: 0; line-height: 1.2;')
                        chat_model = ui.label('Aucun modèle').classes('text-xs').style('color: var(--text-muted); margin: 0; line-height: 1.2;')

                # ARCHIVISTE
                with ui.element('div').classes('ia-status-item').style('display: flex; align-items: center; gap: 6px;'):
                    archiviste_dot = _status_dot(initial='#dc2626')  # Rouge par défaut
                    # Spinner d'activité Archiviste (vert)
                    archiviste_spinner = ui.spinner('audio', size='md').props('color="green"').style('display: none;')
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
                    'chat_spinner': chat_spinner,
                    'archiviste_dot': archiviste_dot,
                    'archiviste_model': archiviste_model,
                    'archiviste_spinner': archiviste_spinner,
                    'embeddings_dot': embeddings_dot,
                    'embeddings_model': embeddings_model
                })
        except Exception:
            pass

    # [PERCEPTION] Vérifier disponibilité extension (plus d'overlay)
    try:
        from extensions.perception_ui import get_perception_ui
        perception_ui = get_perception_ui()
        perception_available = perception_ui is not None
    except ImportError:
        perception_available = False
    
    # [CAPABILITY ADVISOR] - Bouton toujours créé, initialisation au clic
    # (Pattern identique à Biography, Journal, Cognitive Mirror)
    capability_advisor_overlay = None  # Sera initialisé au premier clic

    # [FLUX COGNITIF] - État de visibilité et instance UI
    flux_cognitif_visible = False
    flux_cognitif_ui = None

    with ui.element('div').style('display: flex; align-items: center; gap: 8px; position: fixed; top: 16px; right: 16px; z-index: 999;') as header_container:
        
        # [VOICE] Indicateur vocal - Premier élément (à gauche des boutons)
        _voice_indicator_container = None
        try:
            import sys
            ogma_ng = sys.modules.get('ogma_ng')
            if ogma_ng and getattr(ogma_ng, 'VOICE_MODULE_AVAILABLE', False):
                voice_config = {}
                sm = _get_ogma_ng_function('_ensure_settings_manager')
                if sm:
                    settings_manager = sm()
                    if settings_manager:
                        voice_config = settings_manager.settings.get('voice', {})
                
                if voice_config.get('enabled', False):
                    from modules.voice import create_voice_indicator
                    # Créer un slot pour l'indicateur
                    _voice_indicator_container = ui.element('div').classes('voice-indicator-slot')
                    # Passer le container en paramètre pour que l'indicateur soit créé dedans
                    # force_recreate=True car le header est recréé à chaque page load
                    voice_indicator = create_voice_indicator(_voice_indicator_container, force_recreate=True)
                    # Stocker la référence dans ogma_ng
                    if ogma_ng:
                        ogma_ng._voice_indicator = voice_indicator
                    print("[VOICE-HEADER] ✅ Indicateur vocal injecté dans le header")
        except Exception as e:
            print(f"[VOICE-HEADER] ⚠️ Indicateur vocal non créé: {e}")
            import traceback
            traceback.print_exc()
        
        # Bouton Journal de Bord - Création immédiate, initialisation lazy au clic
        journal_btn = ui.button(icon='book').classes('settings-floating-btn').props('title="Journal de Bord"')
        
        async def _open_journal_lazy():
            """Initialisation lazy du Journal au premier clic"""
            try:
                from extensions.journal_de_bord import is_available, get_journal, initialize_ui
                
                # Vérifier si initialisé et si UI disponible
                if is_available():
                    journal = get_journal()
                    # Si UI non initialisée, la créer
                    if journal.ui_components is None:
                        print("[JOURNAL-HEADER] Initialisation UI lazy...")
                        initialize_ui()
                    # Ouvrir modal (await car async)
                    await journal.ui_components.open_main_modal()
                else:
                    # Si pas initialisé du tout, initialiser maintenant
                    print("[JOURNAL-HEADER] Initialisation complète du journal...")
                    from extensions.journal_de_bord import initialize_journal, initialize_ui
                    from ogma_ng import _ensure_archiviste_controller, _ensure_memory_manager
                    
                    success = initialize_journal(
                        archiviste_controller=_ensure_archiviste_controller(),
                        memory_manager=_ensure_memory_manager()
                    )
                    
                    if success:
                        # Initialiser UI après init réussie (badge disponible immédiatement)
                        initialize_ui()
                        journal = get_journal()
                        # Ouvrir modal (await car async)
                        await journal.ui_components.open_main_modal()
                    else:
                        ui.notify("Impossible d'initialiser le journal", type='negative')
                        
            except Exception as e:
                print(f"[JOURNAL-HEADER] ⚠️ Erreur ouverture journal: {e}")
                import traceback
                traceback.print_exc()
                ui.notify(f"Erreur: {e}", type='negative')
        
        journal_btn.on('click', _open_journal_lazy)

        # Bouton Biographie Profil
        biography_btn = ui.button(icon='person').classes('settings-floating-btn').props('title="Biographie Profil"')

        # Bouton Perception avec style paramètres généraux
        perception_btn = ui.button(icon='visibility').classes('settings-floating-btn').props('title="Vision Perception"')

        # Bouton Cognitive Mirror - Transparence cognitive
        cognitive_mirror_btn = ui.button(icon='psychology_alt').classes('settings-floating-btn q-btn--secondary').props('title="Cognitive Mirror - Réflexion visible"')
        
        # Bouton Capability Advisor - Conseils capacités IA (toujours créé, comme les autres)
        capability_advisor_btn = ui.button(icon='lightbulb').classes('settings-floating-btn q-btn--accent').props('title="Capability Advisor - Conseils IA"')

        # Bouton Organic Planner - Agenda & Charge Mentale
        organic_planner_btn = ui.button(icon='event_note').classes('settings-floating-btn').props('title="Organic Planner - Agenda"')

        # Bouton Flux Cognitif - Visualisation transparence pensées
        flux_cognitif_btn = ui.button(icon='psychology').classes('settings-floating-btn').props('title="Flux Cognitif - Transparence IA"')

        # Bouton Dream Engine — toggle veille/réveil avec état visuel
        dream_engine_btn = ui.button(icon='bedtime').classes('settings-floating-btn').props('title="Dream Engine - Rêves"')
        
        async def _async_dream_toggle():
            """Toggle rêve/réveil avec mise à jour visuelle du bouton."""
            try:
                from extensions.dream_engine import start_dream, wake_up, is_dreaming, is_available
                if not is_available():
                    return
                if is_dreaming():
                    # Sursaut : réveiller l'IA (peut prendre jusqu'à 10 min si image en cours)
                    await wake_up("button_click")
                    dream_engine_btn.classes(remove='dream-btn-active')
                    dream_engine_btn.props(remove='color=deep-purple')
                else:
                    # Endormir l'IA
                    success = await start_dream()
                    if success:
                        dream_engine_btn.classes(add='dream-btn-active')
                        dream_engine_btn.props(add='color=deep-purple')
            except Exception as e:
                print(f"[DREAM-HEADER] ⚠️ Erreur: {e}")
        
        def _dream_btn_click():
            import asyncio
            asyncio.create_task(_async_dream_toggle())
        
        dream_engine_btn.on('click', _dream_btn_click)
        
        # Enregistrer référence pour sync visuelle au réveil
        try:
            from extensions.dream_engine.dream_ui import register_dream_header_btn
            register_dream_header_btn(dream_engine_btn)
        except Exception:
            pass

        # [FLUX COGNITIF] Handler pour toggle overlay ambre
        def toggle_flux_cognitif():
            """Active/désactive l'overlay Flux Cognitif"""
            nonlocal flux_cognitif_visible, flux_cognitif_ui
            
            # Initialisation lazy de l'UI OU recréation si overlay invalide
            if flux_cognitif_ui is None or not flux_cognitif_ui._is_overlay_valid():
                try:
                    from extensions.flux_cognitif import get_flux_cognitif
                    from extensions.flux_cognitif.stream_ui import create_flux_ui
                    
                    flux_instance = get_flux_cognitif()
                    if flux_instance:
                        # Reset état si recréation
                        if flux_cognitif_ui is not None:
                            print("[FLUX-COGNITIF] 🔄 Recréation overlay (ancien invalidé)")
                        flux_cognitif_ui = create_flux_ui(flux_instance)
                        flux_cognitif_visible = False  # Reset état visibilité
                    else:
                        ui.notify("Flux Cognitif non initialisé", type='warning')
                        return
                except Exception as e:
                    print(f"[FLUX-COGNITIF] ❌ Erreur initialisation UI: {e}")
                    ui.notify(f"Erreur: {e}", type='negative')
                    return
            
            # Toggle affichage
            flux_cognitif_visible = not flux_cognitif_visible
            
            if flux_cognitif_visible:
                flux_cognitif_ui.show_overlay()
                flux_cognitif_btn.classes(add='q-btn--primary')
            else:
                flux_cognitif_ui.hide_overlay()
                flux_cognitif_btn.classes(remove='q-btn--primary')
        
        flux_cognitif_btn.on('click', toggle_flux_cognitif)

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
            """Ouvre le popup de paramètres Introspection v4"""
            try:
                print("[SUBCONSCIENCE] CLICK Clic bouton - ouverture popup paramètres")
                _ensure_cognitive_mirror = _get_ogma_ng_function('_ensure_cognitive_mirror')
                if _ensure_cognitive_mirror:
                    print("[SUBCONSCIENCE] SEARCH Fonction _ensure_cognitive_mirror trouvée")
                    cognitive_mirror = _ensure_cognitive_mirror()
                    if cognitive_mirror:
                        print("[SUBCONSCIENCE] BRAIN Extension obtenue")
                        
                        # v4 / v2.0+: ui_components disponible → popup v4
                        if hasattr(cognitive_mirror, 'ui_components') and cognitive_mirror.ui_components:
                            print("[SUBCONSCIENCE] CONFIG Ouverture popup paramètres...")
                            cognitive_mirror.ui_components.show_parameters_popup()
                            print("[SUBCONSCIENCE] OK Popup v4 ouvert")
                        else:
                            print("[SUBCONSCIENCE] INFO Introspection sans UI - popup v2.1")
                            _show_introspection_v21_popup(cognitive_mirror)
                    else:
                        print("[SUBCONSCIENCE] ERROR Extension non initialisée")
                else:
                    print("[SUBCONSCIENCE] ERROR Fonction _ensure_cognitive_mirror non trouvée")
            except Exception as e:
                print(f"[SUBCONSCIENCE] ERROR Erreur ouverture popup: {e}")
                import traceback
                traceback.print_exc()
        
        def _show_introspection_v21_popup(engine):
            """Affiche le popup complet de configuration Introspection v2.1"""
            try:
                config = engine.config
                
                # Récupérer tous les paramètres
                is_enabled = config.is_enabled()
                mode = config.get_introspection_mode()
                is_active = engine.is_active if hasattr(engine, 'is_active') else False
                stats = engine.stats if hasattr(engine, 'stats') else {}
                
                # Paramètres techniques
                step1_tokens = config.get("step1_max_tokens", 400)
                step2_conscious_tokens = config.get("step2_conscious_max_tokens", 500)
                step2_unconscious_tokens = config.get("step2_unconscious_max_tokens", 600)
                step3_tokens = config.get("step3_max_tokens", 800)
                min_exchanges = config.get("min_dialogue_exchanges", 4)
                max_exchanges = config.get("max_dialogue_exchanges", 6)
                max_duration = config.get("max_introspection_duration", 300)
                memory_threshold = config.get("memory_search_threshold", 0.5)
                memory_results = config.get("memory_max_results", 5)
                auto_save = config.get("auto_save_enabled", False)
                importance_threshold = config.get("importance_threshold", 6)
                show_dialogue = config.get("show_dialogue_details", True)
                show_progress = config.get("show_progress_indicator", True)
                typing_anim = config.get("typing_animation", True)
                
                with ui.dialog() as main_dialog, ui.card().classes('p-4').style('min-width: 520px; max-height: 85vh; overflow-y: auto;'):
                    ui.label('🧠 Introspection v2.1').classes('text-xl font-bold')
                    ui.label('Configuration IA Principale ↔ Archiviste').classes('text-xs text-gray-400 mb-4')
                    
                    # === SECTION ÉTAT ===
                    with ui.expansion('📊 État actuel', icon='info').classes('w-full').tooltip('Affiche l\'état actuel de l\'extension et les statistiques'):
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('circle', color='green' if is_enabled else 'red').classes('text-xs')
                            ui.label(f"Extension: {'Activée' if is_enabled else 'Désactivée'}")
                        with ui.row().classes('items-center gap-2'):
                            ui.icon('psychology', color='blue' if is_active else 'gray')
                            ui.label(f"Introspection: {'En cours...' if is_active else 'Inactive'}")
                        with ui.row().classes('items-center gap-2'):
                            ui.label(f"Sessions totales: {stats.get('total_sessions', 0)}")
                    
                    # === SECTION ACTIVATION ===
                    with ui.expansion('⚡ Activation', icon='power_settings_new', value=True).classes('w-full').tooltip('Active/désactive l\'introspection et définit le mode de déclenchement'):
                        def toggle_enabled(e):
                            config.set("extension_enabled", e.value)
                            config.save_config()
                            _sync_btn = _get_ogma_ng_function('_sync_cognitive_mirror_button')
                            if _sync_btn: _sync_btn()
                        
                        ui.switch('Activer l\'introspection', value=is_enabled, on_change=toggle_enabled).tooltip('Active ou désactive complètement l\'introspection')
                        
                        def change_mode(e):
                            config.set("introspection_mode", e.value)
                            config.save_config()
                        
                        ui.select(
                            label='Mode de déclenchement',
                            options={'on_demand': '🎯 À la demande (phrases magiques)', 'always': '🔄 Automatique'},
                            value=mode,
                            on_change=change_mode
                        ).classes('w-full').tooltip('À la demande: déclenché par phrases magiques. Automatique: analyse chaque message.')
                        
                        ui.label('💡 Phrases magiques: "réfléchis", "introspection", "qu\'en penses-tu vraiment"').classes('text-xs text-gray-400')
                    
                    # === SECTION DIALOGUE ===
                    with ui.expansion('💬 Paramètres du dialogue', icon='forum').classes('w-full').tooltip('Configure la durée et le nombre d\'échanges du dialogue interne'):
                        ui.label('💡 Minimum d\'échanges = réflexion approfondie obligatoire').classes('text-xs text-gray-400 mb-2')
                        
                        def update_min_exchanges(e):
                            new_val = int(e.value)
                            # S'assurer que min <= max
                            current_max = config.get("max_dialogue_exchanges", 8)
                            if new_val > current_max:
                                config.set("max_dialogue_exchanges", new_val)
                            config.set("min_dialogue_exchanges", new_val)
                            config.save_config()
                        
                        def update_max_exchanges(e):
                            new_val = int(e.value)
                            # S'assurer que max >= min
                            current_min = config.get("min_dialogue_exchanges", 4)
                            if new_val < current_min:
                                config.set("min_dialogue_exchanges", new_val)
                            config.set("max_dialogue_exchanges", new_val)
                            config.save_config()
                        
                        with ui.row().classes('w-full gap-4'):
                            ui.number(
                                label='Minimum d\'échanges (obligatoire)',
                                value=min_exchanges, min=2, max=10, step=1,
                                on_change=update_min_exchanges
                            ).classes('flex-1').tooltip('Nombre minimum d\'allers-retours Conscient↔Archiviste avant de pouvoir conclure')
                            
                            ui.number(
                                label='Maximum d\'échanges',
                                value=max_exchanges, min=2, max=12, step=1,
                                on_change=update_max_exchanges
                            ).classes('flex-1').tooltip('Limite haute pour éviter des dialogues trop longs')
                        
                        def update_duration(e):
                            config.set("max_introspection_duration", int(e.value))
                            config.save_config()
                        
                        ui.number(
                            label='Durée max introspection (secondes)',
                            value=max_duration, min=60, max=600, step=30,
                            on_change=update_duration
                        ).classes('w-full').tooltip('Timeout global pour éviter les blocages (5min recommandé pour 8 échanges)')
                    
                    # === SECTION TOKENS ===
                    with ui.expansion('📝 Tokens par étape', icon='tune').classes('w-full').tooltip('Contrôle la longueur des réponses générées à chaque étape'):
                        ui.label('Contrôle la longueur des réponses à chaque étape').classes('text-xs text-gray-400 mb-2')
                        
                        def update_step1(e): config.set("step1_max_tokens", int(e.value)); config.save_config()
                        def update_conscious(e): config.set("step2_conscious_max_tokens", int(e.value)); config.save_config()
                        def update_unconscious(e): config.set("step2_unconscious_max_tokens", int(e.value)); config.save_config()
                        def update_step3(e): config.set("step3_max_tokens", int(e.value)); config.save_config()
                        
                        ui.number(label='Étape 1 - Analyse', value=step1_tokens, min=100, max=1000, on_change=update_step1).classes('w-full').tooltip('Analyse initiale du message et récupération mémoire')
                        ui.number(label='Étape 2 - IA Principale', value=step2_conscious_tokens, min=100, max=1500, on_change=update_conscious).classes('w-full').tooltip('Réponse de l\'IA Principale (pensée logique, expression)')
                        ui.number(label='Étape 2 - Archiviste', value=step2_unconscious_tokens, min=100, max=1500, on_change=update_unconscious).classes('w-full').tooltip('Réponse de l\'Archiviste (mémoire profonde, souvenirs)')
                        ui.number(label='Étape 3 - Synthèse finale', value=step3_tokens, min=200, max=2000, on_change=update_step3).classes('w-full').tooltip('Synthèse du dialogue pour la réponse utilisateur')
                    
                    # === SECTION MÉMOIRE ===
                    with ui.expansion('🧠 Accès mémoire', icon='memory').classes('w-full').tooltip('Configure comment l\'introspection accède aux souvenirs'):
                        with ui.row().classes('items-center gap-2 w-full'):
                            threshold_label = ui.label(f'Seuil de similarité: {memory_threshold:.2f}').classes('text-sm')
                            ui.icon('help_outline', size='xs').tooltip('Plus le seuil est bas, plus de souvenirs sont récupérés (même moins pertinents)')
                        def update_threshold(e, lbl=threshold_label): 
                            config.set("memory_search_threshold", float(e.value))
                            config.save_config()
                            lbl.set_text(f'Seuil de similarité: {float(e.value):.2f}')
                        def update_results(e): config.set("memory_max_results", int(e.value)); config.save_config()
                        ui.slider(
                            value=memory_threshold, min=0.1, max=0.9, step=0.05,
                            on_change=update_threshold
                        ).classes('w-full')
                        
                        ui.number(
                            label='Nombre max de souvenirs récupérés',
                            value=memory_results, min=1, max=15, step=1,
                            on_change=update_results
                        ).classes('w-full').tooltip('Limite le nombre de souvenirs injectés dans le contexte')
                    
                    # === SECTION SAUVEGARDE ===
                    with ui.expansion('💾 Sauvegarde automatique', icon='save').classes('w-full').tooltip('L\'IA peut décider de sauvegarder des insights importants'):
                        def toggle_autosave(e): config.set("auto_save_enabled", e.value); config.save_config()
                        def update_importance(e): config.set("importance_threshold", int(e.value)); config.save_config()
                        
                        ui.switch('Sauvegarder automatiquement les insights', value=auto_save, on_change=toggle_autosave).tooltip('Permet à l\'IA de créer des souvenirs depuis ses réflexions')
                        ui.number(
                            label='Seuil d\'importance (1-10)',
                            value=importance_threshold, min=1, max=10, step=1,
                            on_change=update_importance
                        ).classes('w-full')
                        ui.label('L\'IA évalue l\'importance et sauvegarde si ≥ seuil').classes('text-xs text-gray-400')
                    
                    # === SECTION AFFICHAGE ===
                    with ui.expansion('🎨 Affichage', icon='visibility').classes('w-full').tooltip('Options visuelles pour le rendu de l\'introspection'):
                        def toggle_dialogue(e): config.set("show_dialogue_details", e.value); config.save_config()
                        def toggle_progress(e): config.set("show_progress_indicator", e.value); config.save_config()
                        def toggle_typing(e): config.set("typing_animation", e.value); config.save_config()
                        
                        ui.switch('Afficher le dialogue détaillé', value=show_dialogue, on_change=toggle_dialogue).tooltip('Montre les échanges IA Principale↔Archiviste en temps réel')
                        ui.switch('Afficher l\'indicateur de progression', value=show_progress, on_change=toggle_progress).tooltip('Affiche une barre de progression pendant l\'introspection')
                        ui.switch('Animation de frappe', value=typing_anim, on_change=toggle_typing).tooltip('Effet visuel de frappe pour les réponses')
                    
                    # === SECTION INSTRUCTIONS (intégré) ===
                    with ui.expansion('📜 Instructions (avancé)', icon='code').classes('w-full').tooltip('Personnalisez les instructions données à chaque étape de l\'introspection'):
                        ui.label('Modifiez les instructions de chaque étape').classes('text-xs text-gray-400 mb-2')
                        
                        # Onglets pour les 4 instructions
                        with ui.tabs().classes('w-full').props('dense') as instr_tabs:
                            tab_s1 = ui.tab('Analyse', icon='search')
                            tab_conscious = ui.tab('IA Principale', icon='lightbulb')
                            tab_unconscious = ui.tab('Archiviste', icon='nights_stay')
                            tab_synth = ui.tab('Synthèse', icon='auto_awesome')
                        
                        # Variables pour stocker les références aux textareas
                        instruction_fields = {}
                        
                        with ui.tab_panels(instr_tabs, value=tab_s1).classes('w-full'):
                            with ui.tab_panel(tab_s1):
                                instruction_fields['step1'] = ui.textarea(
                                    value=config.get_instruction_text("step1_analysis") if hasattr(config, 'get_instruction_text') else "",
                                    placeholder="Instructions pour l'analyse initiale..."
                                ).classes('w-full')
                            
                            with ui.tab_panel(tab_conscious):
                                instruction_fields['conscious'] = ui.textarea(
                                    value=config.get_instruction_text("step2_conscious") if hasattr(config, 'get_instruction_text') else "",
                                    placeholder="Instructions pour l'IA Principale..."
                                ).classes('w-full')
                            
                            with ui.tab_panel(tab_unconscious):
                                instruction_fields['unconscious'] = ui.textarea(
                                    value=config.get_instruction_text("step2_unconscious") if hasattr(config, 'get_instruction_text') else "",
                                    placeholder="Instructions pour l'Archiviste (gardien de la mémoire)..."
                                ).classes('w-full')
                            
                            with ui.tab_panel(tab_synth):
                                instruction_fields['synthesis'] = ui.textarea(
                                    value=config.get_instruction_text("step3_synthesis") if hasattr(config, 'get_instruction_text') else "",
                                    placeholder="Instructions pour la synthèse finale..."
                                ).classes('w-full')
                        
                        # Boutons d'action
                        with ui.row().classes('w-full justify-between mt-2'):
                            def save_all_instructions():
                                if hasattr(config, 'set_instruction'):
                                    config.set_instruction("step1_analysis", instruction_fields['step1'].value)
                                    config.set_instruction("step2_conscious", instruction_fields['conscious'].value)
                                    config.set_instruction("step2_unconscious", instruction_fields['unconscious'].value)
                                    config.set_instruction("step3_synthesis", instruction_fields['synthesis'].value)
                                    config.save_config()
                                    ui.notify('✅ Instructions sauvegardées et actives immédiatement', type='positive')
                                else:
                                    ui.notify('❌ Méthode non disponible', type='warning')
                            
                            def reset_all_instructions():
                                if hasattr(config, 'reset_instructions'):
                                    config.reset_instructions()
                                    # Mettre à jour les textareas avec les nouvelles valeurs
                                    instruction_fields['step1'].value = config.get_instruction_text("step1_analysis")
                                    instruction_fields['conscious'].value = config.get_instruction_text("step2_conscious")
                                    instruction_fields['unconscious'].value = config.get_instruction_text("step2_unconscious")
                                    instruction_fields['synthesis'].value = config.get_instruction_text("step3_synthesis")
                                    ui.notify('🔄 Instructions réinitialisées aux valeurs par défaut', type='info')
                                else:
                                    ui.notify('❌ Méthode non disponible', type='warning')
                            
                            ui.button('Appliquer', on_click=save_all_instructions, icon='check', color='positive').props('dense').tooltip('Sauvegarde et applique immédiatement les modifications')
                            ui.button('Réinitialiser', on_click=reset_all_instructions, icon='restart_alt', color='warning').props('dense outline').tooltip('Restaure les instructions par défaut')
                    
                    ui.separator()
                    
                    with ui.row().classes('justify-end gap-2 mt-2'):
                        ui.button('Fermer', on_click=main_dialog.close).props('flat')
                
                main_dialog.open()
                # Force la hauteur des textareas après rendu Quasar
                ui.run_javascript('''
                    setTimeout(() => {
                        document.querySelectorAll(".q-dialog textarea, .q-dialog .q-field__native").forEach(el => {
                            el.style.setProperty("min-height", "420px", "important");
                            el.style.setProperty("height", "420px", "important");
                            el.style.setProperty("resize", "vertical", "important");
                            el.style.setProperty("font-family", "Consolas, Monaco, monospace", "important");
                            el.style.setProperty("font-size", "11px", "important");
                        });
                    }, 300);
                ''')
                print("[SUBCONSCIENCE] OK Popup v2.1 complet ouvert")
                
            except Exception as e:
                print(f"[SUBCONSCIENCE] ERROR Popup v2.1: {e}")
                import traceback
                traceback.print_exc()

        # 🔧 FIX: Callback désactivé - le bouton Journal est maintenant géré par ui_components.py
        # qui injecte son propre bouton avec _on_header_button_click() pour ouvrir le modal
        # journal_btn.on('click', toggle_journal)  # ← Ancien comportement (création entrée)
        
        biography_btn.on('click', toggle_biography)
        perception_btn.on('click', open_perception_page)
        cognitive_mirror_btn.on('click', toggle_cognitive_mirror)
        organic_planner_btn.on('click', lambda: _show_organic_planner_dialog())
        
        # Callback Capability Advisor - Initialisation lazy au premier clic
        def toggle_capability_advisor():
            """Ouvre l'overlay Capability Advisor (initialisation lazy)"""
            nonlocal capability_advisor_overlay
            try:
                print("[CAPABILITY-ADVISOR] Clic bouton - toggle overlay")
                
                # Initialisation lazy si pas encore fait
                if capability_advisor_overlay is None:
                    try:
                        _ensure_capability_advisor = _get_ogma_ng_function('_ensure_capability_advisor')
                        if _ensure_capability_advisor:
                            advisor = _ensure_capability_advisor()
                            if advisor and hasattr(advisor, 'ui'):
                                advisor.ui.create_overlay()
                                capability_advisor_overlay = advisor.ui.overlay_dialog
                                print("[CAPABILITY-ADVISOR] ✅ Overlay créé (lazy init)")
                    except Exception as init_e:
                        print(f"[CAPABILITY-ADVISOR] ⚠️ Erreur init: {init_e}")
                        ui.notify("Capability Advisor non disponible", type='warning')
                        return
                
                # Toggle overlay
                if capability_advisor_overlay:
                    capability_advisor_overlay.visible = not capability_advisor_overlay.visible
                    print(f"[CAPABILITY-ADVISOR] Overlay {'affiché' if capability_advisor_overlay.visible else 'masqué'}")
                else:
                    print("[CAPABILITY-ADVISOR] Overlay non disponible")
                    ui.notify("Capability Advisor non disponible", type='warning')
            except Exception as e:
                print(f"[CAPABILITY-ADVISOR] Erreur toggle: {e}")
                import traceback
                traceback.print_exc()
        
        capability_advisor_btn.on('click', toggle_capability_advisor)
        
        # Synchronisation initiale du bouton Cognitive Mirror
        def sync_cognitive_mirror_button():
            """Synchronise l'apparence du bouton avec l'état réel de l'extension"""
            try:
                _ensure_cognitive_mirror = _get_ogma_ng_function('_ensure_cognitive_mirror')
                if _ensure_cognitive_mirror:
                    cognitive_mirror = _ensure_cognitive_mirror()
                    if cognitive_mirror:
                        from extensions.cognitive_mirror import is_enabled as cm_is_enabled
                        current_state = cm_is_enabled()
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
