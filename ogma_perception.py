"""
OGMA Perception Page
====================
Page dédiée pour l'extension Perception avec affichage webcam en temps réel.
Extrait depuis ogma_ng.py pour modularisation.

CONTIENT :
- perception_page() : Page UI complète pour la webcam et les paramètres
"""

from nicegui import ui

try:
    from utils.i18n import t
except Exception:
    def t(key, **kwargs):
        return key

# Import du style depuis ogma_displays
try:
    from ogma_displays import _link_styles
except ImportError:
    def _link_styles():
        """Fallback si ogma_displays non disponible"""
        pass


def perception_page():
    """
    Page dédiée pour l'extension Perception avec affichage webcam en temps réel.
    Ouverte dans une fenêtre popup dédiée compacte (580×440).
    """
    print("[PERCEPTION-PAGE] 📹 Chargement page Perception...")
    
    ui.dark_mode()
    _link_styles()
    
    # JavaScript pour gérer la fenêtre popup
    ui.run_javascript('''
        // Focus initial sur la fenêtre popup
        window.focus();
        
        // Mémoriser position/taille si fenêtre déplacée/redimensionnée (localStorage)
        let saveWindowState = () => {
            localStorage.setItem('perceptionWindowX', window.screenX);
            localStorage.setItem('perceptionWindowY', window.screenY);
            localStorage.setItem('perceptionWindowW', window.outerWidth);
            localStorage.setItem('perceptionWindowH', window.outerHeight);
        };
        
        // Sauvegarder état toutes les 3 secondes si modifié
        setInterval(saveWindowState, 3000);
        
        // Au chargement, restaurer position/taille si sauvegardée
        window.addEventListener('load', () => {
            let savedX = localStorage.getItem('perceptionWindowX');
            let savedY = localStorage.getItem('perceptionWindowY');
            let savedW = localStorage.getItem('perceptionWindowW');
            let savedH = localStorage.getItem('perceptionWindowH');
            
            if (savedX && savedY) {
                window.moveTo(parseInt(savedX), parseInt(savedY));
            }
            if (savedW && savedH) {
                window.resizeTo(parseInt(savedW), parseInt(savedH));
            }
        });
    ''')
    
    # Récupérer l'instance perception_ui (singleton)
    from extensions.perception_ui import get_perception_ui
    perception_ui = get_perception_ui()
    
    if not perception_ui:
        with ui.column().classes('w-full h-screen items-center justify-center'):
            ui.label('❌ Extension Perception non disponible').classes('text-xl text-red-500')
        return
    
    # Layout principal (scrollable avec hauteur max)
    with ui.column().classes('w-full').style('padding: 20px; gap: 20px; max-height: 100vh; overflow-y: scroll;'):
        
        # Header
        with ui.row().classes('w-full items-center justify-between'):
            ui.label(t('perc_title')).classes('text-3xl font-bold')
            
            with ui.row().classes('gap-2'):
                # Switch ON/OFF
                perception_toggle = ui.switch(
                    text=t('perc_switch_extension'),
                    value=perception_ui.is_enabled
                ).props('color="green"')
                
                # Bouton fermer popup
                ui.button(
                    t('perc_btn_close'), 
                    icon='close',
                    on_click=lambda: ui.run_javascript('window.close();')
                ).props('outline color="negative"')
        
        # Container principal avec 2 colonnes (flex-wrap pour responsive)
        with ui.row().classes('w-full').style('gap: 20px; flex-wrap: wrap;'):
            
            # COLONNE GAUCHE: Webcam display (réduite de 40% comme demandé)
            with ui.column().style('flex: 1.2; min-width: 400px; max-width: 600px; gap: 12px;'):
                ui.label(t('perc_section_vision')).classes('text-xl font-semibold')
                
                # Webcam container (hauteur réduite)
                with ui.card().classes('w-full').style('background: #000; padding: 0; min-height: 300px; max-height: 400px;'):
                    webcam_display = ui.image().classes('w-full').style('object-fit: contain;')
                    webcam_placeholder = ui.label(t('perc_placeholder_webcam')).classes('absolute-center text-gray-400')
                
                # Status bar
                with ui.row().classes('items-center gap-2'):
                    status_dot = ui.element('div').style('''
                        width: 12px;
                        height: 12px;
                        border-radius: 50%;
                        background: #dc2626;
                        box-shadow: 0 0 8px rgba(220, 38, 38, 0.6);
                    ''')
                    status_label = ui.label(t('perc_status_inactive')).classes('text-sm')
                
                # Boutons action
                with ui.row().classes('gap-2'):
                    capture_btn = ui.button(
                        t('perc_btn_capture'), 
                        icon='camera'
                    ).props('color="primary"')
                    
                    motion_btn = ui.button(
                        t('perc_btn_chrono'),
                        icon='video_library'
                    ).props('color="purple" outline')
            
            # COLONNE DROITE: Contrôles (scrollable si nécessaire)
            with ui.column().style('flex: 1; min-width: 350px; max-width: 450px; gap: 16px;'):
                ui.label(t('perc_section_params')).classes('text-xl font-semibold')
                
                with ui.card().classes('w-full'):
                    with ui.column().style('gap: 12px; padding: 12px;'):
                        
                        # Mode capture
                        ui.label(t('perc_label_capture_mode')).classes('text-sm font-medium text-gray-400')
                        motion_toggle = ui.switch(
                            text=t('perc_switch_film_mode'), 
                            value=perception_ui.current_config.get('motion_capture_enabled', False)
                        ).props('color="purple"')
                        
                        ui.separator()
                        
                        # Délai capture
                        ui.label(t('perc_label_capture_delay')).classes('text-sm font-medium text-gray-400')
                        with ui.row().classes('items-center justify-between w-full'):
                            ui.label(t('perc_label_delay')).classes('text-sm')
                            capture_delay_label = ui.label(
                                f"{perception_ui.current_config.get('capture_delay', 0.0):.1f}s"
                            ).classes('text-sm text-gray-400')
                        capture_delay_slider = ui.slider(
                            min=0.0, max=10.0, step=0.5,
                            value=perception_ui.current_config.get('capture_delay', 0.0)
                        ).props('label-always color="orange"').classes('w-full')
                        
                        # Paramètres chronophoto (conditionnels)
                        motion_params = ui.column().style('gap: 12px;')
                        with motion_params:
                            ui.separator()
                            ui.label(t('perc_label_film_params')).classes('text-sm font-medium text-gray-400')
                            
                            # Intervalle entre images
                            with ui.row().classes('items-center justify-between w-full'):
                                ui.label(t('perc_label_interval')).classes('text-sm')
                                motion_interval_label = ui.label(
                                    f"{perception_ui.current_config.get('motion_interval', 0.5):.1f}s"
                                ).classes('text-sm text-gray-400')
                            motion_interval_slider = ui.slider(
                                min=0.1, max=5.0, step=0.1,
                                value=perception_ui.current_config.get('motion_interval', 0.5)
                            ).props('label-always color="purple"').classes('w-full')
                            
                            # Nombre d'images (jusqu'à 20)
                            with ui.row().classes('items-center justify-between w-full'):
                                ui.label(t('perc_label_num_frames')).classes('text-sm')
                                frames_count_label = ui.label(
                                    f"{perception_ui.current_config.get('motion_frames_after', 6)}"
                                ).classes('text-sm text-gray-400')
                            frames_count_slider = ui.slider(
                                min=2, max=20, step=1,
                                value=perception_ui.current_config.get('motion_frames_after', 6)
                            ).props('label-always color="purple"').classes('w-full')
                            
                            # Durée totale calculée
                            with ui.row().classes('items-center justify-between w-full'):
                                ui.label(t('perc_label_total_duration')).classes('text-sm')
                                initial_duration = (
                                    perception_ui.current_config.get('motion_frames_after', 6) - 1
                                ) * perception_ui.current_config.get('motion_interval', 0.5)
                                duration_label = ui.label(f'{initial_duration:.1f}s').classes('text-sm text-gray-400')
                            
                            # Layout (jusqu'à 4x5)
                            with ui.row().classes('items-center justify-between w-full'):
                                ui.label(t('perc_label_layout')).classes('text-sm')
                                layout_select = ui.select(
                                    options={
                                        '2x2': '2×2 (4)', '3x2': '3×2 (6)', '2x3': '2×3 (6)',
                                        '4x2': '4×2 (8)', '2x4': '2×4 (8)',
                                        '3x3': '3×3 (9)', '4x3': '4×3 (12)', '3x4': '3×4 (12)',
                                        '4x4': '4×4 (16)', '5x4': '5×4 (20)', '4x5': '4×5 (20)',
                                        '1x10': '1×10', '10x1': '10×1', '1x20': '1×20', '20x1': '20×1'
                                    },
                                    value=perception_ui.current_config.get('motion_layout', '3x2')
                                ).classes('text-sm')
                            
                            # Options chronophoto avancées
                            ui.separator()
                            ui.label(t('perc_label_display_options')).classes('text-xs font-medium text-gray-500')
                            
                            timeline_toggle = ui.switch(
                                text=t('perc_switch_timeline'),
                                value=perception_ui.current_config.get('motion_timeline', False)
                            ).props('color="purple" dense').classes('text-xs')
                            
                            annotations_toggle = ui.switch(
                                text=t('perc_switch_annotations'),
                                value=perception_ui.current_config.get('motion_annotations', False)
                            ).props('color="purple" dense').classes('text-xs')
                        
                        ui.separator()
                        
                        # Sauvegarde captures
                        ui.label(t('perc_label_save_section')).classes('text-sm font-medium text-gray-400')
                        save_captures_toggle = ui.switch(
                            text=t('perc_switch_save_local'),
                            value=perception_ui.current_config.get('save_captures', False)
                        ).props('color="amber"')
                        ui.label(t('perc_label_folder')).classes('text-xs text-gray-500')
                        
                        ui.separator()
                        
                        # Source caméra
                        ui.label(t('perc_label_source')).classes('text-sm font-medium text-gray-400')
                        
                        # Détection dynamique des caméras disponibles
                        def detect_cameras():
                            """Détecte toutes les caméras disponibles (hardcode + détection OpenCV)"""
                            available = perception_ui.detect_available_cameras()
                            if not available:
                                # Fallback si aucune caméra détectée
                                available = {0: 'Caméra 0', 1: 'Caméra 1', 2: 'Caméra 2'}
                            return available
                        
                        # Container pour la sélection de caméra avec bouton refresh
                        with ui.row().classes('items-center justify-between w-full gap-2'):
                            ui.label(t('perc_label_camera')).classes('text-sm')
                            
                            # Select avec détection dynamique
                            camera_options = detect_cameras()
                            
                            # Valider que la valeur sauvegardée existe dans les options
                            saved_index = perception_ui.current_config.get('webcam_index', 0)
                            if saved_index not in camera_options:
                                print(f"[PERCEPTION-UI] ⚠️ Index {saved_index} non disponible, fallback à 0")
                                saved_index = 0 if 0 in camera_options else list(camera_options.keys())[0]
                                # 🔧 IMPORTANT: Mettre à jour la config avec le fallback
                                perception_ui.current_config['webcam_index'] = saved_index
                                perception_ui._save_config_to_settings()
                                print(f"[PERCEPTION-UI] ✅ Config mise à jour: webcam_index={saved_index}")
                            
                            camera_select = ui.select(
                                options=camera_options,
                                value=saved_index
                            ).classes('text-sm flex-grow')
                            
                            # Bouton de rafraîchissement des caméras
                            def refresh_cameras():
                                """Rafraîchit la liste des caméras disponibles"""
                                print("[PERCEPTION-UI] 🔄 Rafraîchissement liste caméras...")
                                new_cameras = detect_cameras()
                                camera_select.options = new_cameras
                                camera_select.update()
                                print(f"[PERCEPTION-UI] ✅ {len(new_cameras)} caméra(s) détectée(s)")
                                ui.notify(f'🔄 {len(new_cameras)} caméra(s) disponible(s)', type='info', position='top')
                            
                            ui.button(icon='refresh', on_click=refresh_cameras).props('flat dense round').classes('text-blue-400').tooltip('🔄 Rafraîchir la liste des caméras')
                        
                        # Indication du nombre de caméras détectées
                        ui.label(f'📹 {len(camera_options)} source(s) détectée(s)').classes('text-xs text-gray-500')
                        
                        # Option résolution native
                        use_native_toggle = ui.switch(
                            text=t('perc_switch_native_res'),
                            value=perception_ui.current_config.get('use_native_resolution', False)
                        ).props('color="cyan"')
                        ui.label(t('perc_hint_native_res')).classes('text-xs text-gray-500')
                        
                        # Résolution (désactivée en mode chirurgical OU si résolution native)
                        with ui.row().classes('items-center justify-between w-full'):
                            ui.label(t('perc_label_resolution')).classes('text-sm')
                            resolution_select = ui.select(
                                options={'320x240': '320p', '640x480': '480p', '1280x720': '720p', '1920x1080': '1080p'},
                                value=perception_ui.current_config.get('capture_resolution', '640x480')
                            ).classes('text-sm')
                        
                        # Indicateur mode actif
                        resolution_hint = ui.label(
                            t('perc_hint_resolution')
                        ).classes('text-xs text-gray-400 italic')
                        
                        # Paramètres avancés
                        with ui.expansion(t('perc_expansion_advanced'), icon='settings').classes('w-full'):
                            with ui.column().style('gap: 12px; padding: 8px;'):
                                # === VISION AVANCÉE (Regroupée) ===
                                ui.label(t('perc_adv_vision_title')).classes('text-sm font-bold text-purple-400 mb-1')
                                ui.label(t('perc_adv_vision_hint')).classes('text-xs text-gray-400 mb-2')
                                
                                # Depth Map
                                with ui.row().classes('items-center justify-between w-full').style('background: #2d1b4e; padding: 12px; border-radius: 8px;'):
                                    with ui.column().style('gap: 4px;'):
                                        ui.label(t('perc_adv_depth_label')).classes('text-sm font-bold text-purple-300')
                                        ui.label(t('perc_adv_depth_desc')).classes('text-xs text-gray-400')
                                    
                                    depth_switch = ui.switch(
                                        value=perception_ui.current_config.get('enable_depth', False)
                                    ).props('color="purple" dense')

                                # Analyse Contours
                                with ui.row().classes('items-center justify-between w-full').style('background: #1e3a1e; padding: 12px; border-radius: 8px;'):
                                    with ui.column().style('gap: 4px;'):
                                        ui.label(t('perc_adv_contour_label')).classes('text-sm font-bold text-green-400')
                                        ui.label(t('perc_adv_contour_desc')).classes('text-xs text-gray-400')
                                    
                                    contour_switch = ui.switch(
                                        value=perception_ui.current_config.get('enable_contour', False)
                                    ).props('color="green" dense')
                                
                                # Options détaillées Contours (visible si contour activé)
                                with ui.column().style('gap: 8px; padding-left: 20px; margin-top: 4px;').bind_visibility_from(contour_switch, 'value'):
                                    ui.label(t('perc_adv_methods_label')).classes('text-xs text-gray-400')
                                    with ui.row().classes('gap-4'):
                                        contour_canny_cb = ui.checkbox(
                                            'Canny',
                                            value=perception_ui.current_config.get('contour_canny', True)
                                        ).props('dense color="red"').classes('text-xs')
                                        
                                        contour_sobel_cb = ui.checkbox(
                                            'Sobel',
                                            value=perception_ui.current_config.get('contour_sobel', False)
                                        ).props('dense color="orange"').classes('text-xs')
                                        
                                        contour_laplacian_cb = ui.checkbox(
                                            'Laplacian',
                                            value=perception_ui.current_config.get('contour_laplacian', False)
                                        ).props('dense color="yellow"').classes('text-xs')
                                        
                                        contour_adaptive_cb = ui.checkbox(
                                            t('perc_adv_adaptatif'),
                                            value=perception_ui.current_config.get('contour_adaptive', False)
                                        ).props('dense color="blue"').classes('text-xs')
                                    
                                    ui.label(t('perc_adv_canny_params')).classes('text-xs text-gray-400 mt-2')
                                    with ui.row().classes('gap-4 items-center'):
                                        ui.label(t('perc_adv_low_threshold')).classes('text-xs')
                                        contour_canny_low = ui.slider(
                                            min=0, max=255, step=10,
                                            value=perception_ui.current_config.get('contour_canny_low', 50)
                                        ).props('dense').classes('w-24')
                                        
                                        ui.label(t('perc_adv_high_threshold')).classes('text-xs')
                                        contour_canny_high = ui.slider(
                                            min=0, max=255, step=10,
                                            value=perception_ui.current_config.get('contour_canny_high', 150)
                                        ).props('dense').classes('w-24')
                                        
                                        ui.label(t('perc_adv_thickness')).classes('text-xs')
                                        contour_thickness = ui.slider(
                                            min=1, max=10, step=1,
                                            value=perception_ui.current_config.get('contour_thickness', 2)
                                        ).props('dense').classes('w-20')
                                    
                                    ui.label(t('perc_adv_render_mode')).classes('text-xs text-gray-400 mt-1')
                                    contour_render_mode = ui.select(
                                        options={'overlay': t('perc_adv_overlay'), 'black_bg': t('perc_adv_black_bg'), 'white_bg': t('perc_adv_white_bg')},
                                        value=perception_ui.current_config.get('contour_render_mode', 'overlay')
                                    ).props('dense').classes('w-32')
                                
                                ui.separator()

                                # Mode Chirurgical 🆕
                                with ui.row().classes('items-center justify-between w-full').style('background: #1e293b; padding: 12px; border-radius: 8px;'):
                                    with ui.column().style('gap: 4px;'):
                                        ui.label(t('perc_adv_surgical_label')).classes('text-sm font-bold text-blue-400')
                                        ui.label(t('perc_adv_surgical_desc')).classes('text-xs text-gray-400')
                                        ui.label(t('perc_adv_surgical_stream')).classes('text-xs text-gray-500')
                                        ui.label(t('perc_adv_surgical_captures')).classes('text-xs text-gray-500')
                                        ui.label(t('perc_adv_surgical_cpu')).classes('text-xs text-green-500')
                                    surgical_mode_switch = ui.switch(
                                        value=perception_ui.current_config.get('surgical_mode', False)
                                    ).props('color="blue"')
                                
                                ui.separator()
                                
                                # FPS Preview
                                ui.label(t('perc_adv_fps_hint')).classes('text-xs text-gray-400 italic')
                                with ui.row().classes('items-center justify-between w-full'):
                                    ui.label(t('perc_adv_fps_label')).classes('text-xs')
                                    display_fps_label = ui.label(
                                        f"{perception_ui.current_config.get('display_fps', 15)} fps"
                                    ).classes('text-xs text-gray-400')
                                display_fps_slider = ui.slider(
                                    min=5, max=30, step=5,
                                    value=perception_ui.current_config.get('display_fps', 15)
                                ).props('label-always color="blue"').classes('w-full')
                                
                                # Qualité Stream 🆕
                                ui.label(t('perc_adv_stream_quality_hint')).classes('text-xs text-gray-400 italic')
                                with ui.row().classes('items-center justify-between w-full'):
                                    ui.label(t('perc_adv_stream_quality_label')).classes('text-xs')
                                    stream_quality_label = ui.label(
                                        f"{perception_ui.current_config.get('stream_quality', 75)}%"
                                    ).classes('text-xs text-gray-400')
                                stream_quality_slider = ui.slider(
                                    min=60, max=90, step=5,
                                    value=perception_ui.current_config.get('stream_quality', 75)
                                ).props('label-always color="cyan"').classes('w-full')
                                
                                # Qualité JPEG Capture (renommé)
                                ui.label(t('perc_adv_capture_quality_hint')).classes('text-xs text-gray-400 italic')
                                with ui.row().classes('items-center justify-between w-full'):
                                    ui.label(t('perc_adv_capture_quality_label')).classes('text-xs')
                                    jpeg_quality_label = ui.label(
                                        f"{perception_ui.current_config.get('jpeg_quality', 85)}%"
                                    ).classes('text-xs text-gray-400')
                                jpeg_quality_slider = ui.slider(
                                    min=50, max=100, step=5,
                                    value=perception_ui.current_config.get('jpeg_quality', 85)
                                ).props('label-always color="green"').classes('w-full')
                
                # Bouton Sauvegarder en bas de la card
                with ui.row().classes('w-full justify-center').style('margin-top: 16px;'):
                    save_btn = ui.button(
                        t('perc_btn_save_config'), 
                        icon='save'
                    ).props('color="positive"').classes('w-full')
    
    # ============================================================================
    # LOGIQUE MISE À JOUR WEBCAM avec ui.timer (natif NiceGUI)
    # ============================================================================
    
    import cv2
    import numpy as np
    from typing import Optional
    
    # Note: frame_to_base64 supprimée - JPEG encodé directement dans backend
    
    def update_webcam_display():
        """Mise à jour de l'affichage webcam - OPTIMISÉ: JPEG direct depuis backend"""
        try:
            if not perception_ui or not perception_ui.perception_agent:
                return
            
            # Récupérer JPEG base64 DIRECT depuis la queue (pas de re-traitement)
            if not perception_ui.perception_agent.visual_queue.empty():
                jpeg_base64 = perception_ui.perception_agent.visual_queue.get_nowait()
                
                if jpeg_base64:
                    webcam_display.set_source(f'data:image/jpeg;base64,{jpeg_base64}')
                    webcam_placeholder.set_visibility(False)
                else:
                    webcam_placeholder.set_visibility(True)
            
            # Mettre à jour le status
            if perception_ui.is_enabled and perception_ui.perception_agent:
                status = perception_ui.perception_agent.status
                if status == 'active':
                    status_dot.style('background: #22c55e; box-shadow: 0 0 8px rgba(34, 197, 94, 0.6);')
                    status_label.set_text(t('perc_status_active'))
                elif status == 'warming_up':
                    status_dot.style('background: #eab308; box-shadow: 0 0 8px rgba(234, 179, 8, 0.6);')
                    status_label.set_text(t('perc_status_init'))
                else:
                    status_dot.style('background: #dc2626; box-shadow: 0 0 8px rgba(220, 38, 38, 0.6);')
                    status_label.set_text(t('perc_status_inactive'))
            else:
                status_dot.style('background: #dc2626; box-shadow: 0 0 8px rgba(220, 38, 38, 0.6);')
                status_label.set_text(t('perc_status_disabled'))
                
        except Exception as e:
            print(f"[PERCEPTION-PAGE] ⚠️ Erreur update: {e}")
    
    # Timer simple qui respecte le FPS configuré
    def simple_update():
        """Mise à jour simple basée sur FPS configuré"""
        try:
            update_webcam_display()
        except Exception as e:
            print(f"[PERCEPTION-PAGE] ⚠️ Erreur update: {e}")
    
    # Timer calé sur le FPS configuré (15 FPS = ~67ms entre frames)
    fps_target = perception_ui.current_config.get('display_fps', 15)
    update_interval = 1.0 / fps_target  # Ex: 15 FPS = 0.067s
    ui.timer(update_interval, simple_update)
    
    # Enregistrer les éléments UI
    perception_ui.register_ui_elements(webcam_display, status_dot)
    
    # ============================================================================
    # EVENT HANDLERS
    # ============================================================================
    
    def on_toggle_perception(e):
        enabled = e.args if isinstance(e.args, bool) else perception_toggle.value
        if enabled:
            perception_ui.start_perception()
            ui.notify('✅ Perception activée', type='positive')
        else:
            perception_ui.stop_perception()
            ui.notify('🛑 Perception désactivée', type='info')
    
    def on_capture_click():
        if perception_ui and perception_ui.is_enabled:
            perception_ui.request_capture()
            ui.notify('📸 Capture en cours...', type='info')
        else:
            ui.notify('⚠️ Activez Perception d\'abord', type='warning')
    
    def on_motion_click():
        if perception_ui and perception_ui.is_enabled:
            if perception_ui.current_config.get('motion_capture_enabled'):
                perception_ui.request_motion_capture()
                ui.notify('🎬 Chronophotographie en cours...', type='info')
            else:
                ui.notify('⚠️ Activez le mode Pellicule d\'abord', type='warning')
        else:
            ui.notify('⚠️ Activez Perception d\'abord', type='warning')
    
    def on_motion_toggle(e):
        enabled = e.args if isinstance(e.args, bool) else motion_toggle.value
        perception_ui.current_config['motion_capture_enabled'] = enabled
        motion_params.set_visibility(enabled)
        # Pas de sauvegarde auto - attendre bouton Sauvegarder
    
    def on_capture_delay_change(e):
        value = e.args if isinstance(e.args, (int, float)) else capture_delay_slider.value
        perception_ui.current_config['capture_delay'] = value
        capture_delay_label.set_text(f'{value:.1f}s')
        # Pas de sauvegarde auto
    
    def on_motion_interval_change(e):
        value = e.args if isinstance(e.args, (int, float)) else motion_interval_slider.value
        perception_ui.current_config['motion_interval'] = value
        motion_interval_label.set_text(f'{value:.1f}s')
        # Recalculer durée
        frames = perception_ui.current_config.get('motion_frames_after', 6)
        duration = (frames - 1) * value
        duration_label.set_text(f'{duration:.1f}s')
        # Pas de sauvegarde auto
    
    def on_frames_count_change(e):
        value = int(e.args) if isinstance(e.args, (int, float)) else int(frames_count_slider.value)
        perception_ui.current_config['motion_frames_after'] = value
        frames_count_label.set_text(f'{value}')
        # Recalculer durée
        interval = perception_ui.current_config.get('motion_interval', 0.5)
        duration = (value - 1) * interval
        duration_label.set_text(f'{duration:.1f}s')
        # Pas de sauvegarde auto
    
    def on_layout_change(e):
        value = e.args if isinstance(e.args, str) else layout_select.value
        perception_ui.current_config['motion_layout'] = value
        # Pas de sauvegarde auto
    
    def on_camera_change(e):
        value = e.args if isinstance(e.args, int) else camera_select.value
        perception_ui.current_config['webcam_index'] = value
        # Pas de sauvegarde auto - redémarrage uniquement au clic Sauvegarder
    
    def on_resolution_change(e):
        """Change la résolution du stream (mode Normal uniquement)"""
        value = e.args if isinstance(e.args, str) else resolution_select.value
        perception_ui.current_config['capture_resolution'] = value
        
        # En mode Normal, propager immédiatement (pas besoin restart webcam)
        surgical_mode = perception_ui.current_config.get('surgical_mode', False)
        if not surgical_mode and perception_ui.perception_agent:
            # Mettre à jour la config agent directement
            perception_ui.perception_agent.update_config({'capture_resolution': value})
            ui.notify(f'📐 Résolution stream: {value}', type='info')
        
        # Pas de sauvegarde auto - mais effet immédiat en mode Normal
    
    def on_display_fps_change(e):
        value = e.args if isinstance(e.args, (int, float)) else display_fps_slider.value
        perception_ui.current_config['display_fps'] = int(value)
        display_fps_label.set_text(f'{int(value)} fps')
        # Pas de sauvegarde auto - FPS s'adapte dynamiquement
    
    def on_jpeg_quality_change(e):
        value = e.args if isinstance(e.args, (int, float)) else jpeg_quality_slider.value
        perception_ui.current_config['jpeg_quality'] = int(value)
        jpeg_quality_label.set_text(f'{int(value)}%')
        # Pas de sauvegarde auto
    
    def on_depth_change(e):
        enabled = e.args if isinstance(e.args, bool) else depth_switch.value
        perception_ui.current_config['enable_depth'] = enabled
        # Propager immédiatement
        if perception_ui.perception_agent:
            perception_ui.perception_agent.update_config({'enable_depth': enabled})

    def on_contour_change(e):
        """Active/désactive l'analyse contours"""
        enabled = e.args if isinstance(e.args, bool) else contour_switch.value
        perception_ui.current_config['enable_contour'] = enabled
        # Propager immédiatement
        if perception_ui.perception_agent:
            perception_ui.perception_agent.update_config({'enable_contour': enabled})
        if enabled:
            ui.notify('✏️ Analyse Contours activée (Canny/Sobel)', type='info')

    def on_contour_canny_change(e):
        enabled = e.args if isinstance(e.args, bool) else contour_canny_cb.value
        perception_ui.current_config['contour_canny'] = enabled
        if perception_ui.perception_agent:
            perception_ui.perception_agent.update_config({'contour_canny': enabled})

    def on_contour_sobel_change(e):
        enabled = e.args if isinstance(e.args, bool) else contour_sobel_cb.value
        perception_ui.current_config['contour_sobel'] = enabled
        if perception_ui.perception_agent:
            perception_ui.perception_agent.update_config({'contour_sobel': enabled})

    def on_contour_laplacian_change(e):
        enabled = e.args if isinstance(e.args, bool) else contour_laplacian_cb.value
        perception_ui.current_config['contour_laplacian'] = enabled
        if perception_ui.perception_agent:
            perception_ui.perception_agent.update_config({'contour_laplacian': enabled})

    def on_contour_adaptive_change(e):
        enabled = e.args if isinstance(e.args, bool) else contour_adaptive_cb.value
        perception_ui.current_config['contour_adaptive'] = enabled
        if perception_ui.perception_agent:
            perception_ui.perception_agent.update_config({'contour_adaptive': enabled})

    def on_contour_canny_low_change(e):
        value = int(e.args) if isinstance(e.args, (int, float)) else int(contour_canny_low.value)
        perception_ui.current_config['contour_canny_low'] = value
        if perception_ui.perception_agent:
            perception_ui.perception_agent.update_config({'contour_canny_low': value})

    def on_contour_canny_high_change(e):
        value = int(e.args) if isinstance(e.args, (int, float)) else int(contour_canny_high.value)
        perception_ui.current_config['contour_canny_high'] = value
        if perception_ui.perception_agent:
            perception_ui.perception_agent.update_config({'contour_canny_high': value})

    def on_contour_thickness_change(e):
        value = int(e.args) if isinstance(e.args, (int, float)) else int(contour_thickness.value)
        perception_ui.current_config['contour_thickness'] = value
        if perception_ui.perception_agent:
            perception_ui.perception_agent.update_config({'contour_thickness': value})

    def on_contour_render_mode_change(e):
        value = e.args if isinstance(e.args, str) else contour_render_mode.value
        perception_ui.current_config['contour_render_mode'] = value
        if perception_ui.perception_agent:
            perception_ui.perception_agent.update_config({'contour_render_mode': value})

    def on_surgical_mode_change(e):
        """Active/désactive le mode chirurgical avec optimisations auto"""
        enabled = e.args if isinstance(e.args, bool) else surgical_mode_switch.value
        perception_ui.current_config['surgical_mode'] = enabled
        
        # PROPAGER au backend immédiatement (effet immédiat sur stream)
        if perception_ui.perception_agent:
            perception_ui.perception_agent.update_config({'surgical_mode': enabled})
        
        if enabled:
            # MODE CHIRURGICAL ACTIVÉ 🔬
            ui.notify('🔬 Mode Chirurgical: Stream 720p forcé, captures 1080p @ 95%', type='info')
            
            # DÉSACTIVER le slider résolution (forcé 720p en mode chirurgical)
            resolution_select.set_enabled(False)
            resolution_hint.set_text('🔬 Mode Chirurgical: Stream 720p fixe (optimisé détails)')
            
            # Auto-config optimale
            # 1. Qualité capture IA maximale
            if perception_ui.current_config.get('jpeg_quality', 85) < 95:
                perception_ui.current_config['jpeg_quality'] = 95
                jpeg_quality_slider.set_value(95)
                jpeg_quality_label.set_text('95%')
            
            # 2. Stream qualité bonne (80% pour voir détails)
            if perception_ui.current_config.get('stream_quality', 75) < 80:
                perception_ui.current_config['stream_quality'] = 80
                stream_quality_slider.set_value(80)
                stream_quality_label.set_text('80%')
            
            # 3. FPS modéré si trop élevé (économie CPU)
            current_fps = perception_ui.current_config.get('display_fps', 15)
            if current_fps > 15:
                ui.notify('💡 FPS réduit à 15 (optimal mode chirurgical)', type='info')
                perception_ui.current_config['display_fps'] = 15
                display_fps_slider.set_value(15)
                display_fps_label.set_text('15 fps')
        else:
            # MODE NORMAL RESTAURÉ
            ui.notify('📹 Mode Normal: Utilisez slider Résolution', type='info')
            
            # RÉACTIVER le slider résolution
            resolution_select.set_enabled(True)
            resolution_hint.set_text('💡 En mode Normal, choisissez résolution selon besoin')
            
            # Restaurer config normale
            if perception_ui.current_config.get('jpeg_quality', 85) == 95:
                perception_ui.current_config['jpeg_quality'] = 85
                jpeg_quality_slider.set_value(85)
                jpeg_quality_label.set_text('85%')
            
            if perception_ui.current_config.get('stream_quality', 75) == 80:
                perception_ui.current_config['stream_quality'] = 75
                stream_quality_slider.set_value(75)
                stream_quality_label.set_text('75%')
        
        # Pas de sauvegarde auto - attendre bouton Sauvegarder
    
    def on_stream_quality_change(e):
        """Change la qualité du stream preview"""
        value = e.args if isinstance(e.args, (int, float)) else stream_quality_slider.value
        perception_ui.current_config['stream_quality'] = int(value)
        stream_quality_label.set_text(f'{int(value)}%')
        # Pas de sauvegarde auto
    
    def save_config():
        """Sauvegarde la configuration et redémarre si nécessaire"""
        try:
            # Sauvegarder config AVANT (pour détecter changements)
            old_webcam_index = perception_ui.perception_agent.webcam_index if perception_ui.perception_agent else None
            old_surgical_mode = perception_ui.perception_agent.config.get('surgical_mode', False) if perception_ui.perception_agent else False
            
            # Sauvegarder la config
            perception_ui.update_config(perception_ui.current_config)
            
            # Détecter si changements critiques nécessitent restart
            new_webcam_index = perception_ui.current_config.get('webcam_index')
            new_surgical_mode = perception_ui.current_config.get('surgical_mode', False)
            
            needs_restart = False
            restart_reasons = []
            
            if old_webcam_index is not None and new_webcam_index != old_webcam_index:
                needs_restart = True
                restart_reasons.append(f'caméra {old_webcam_index}→{new_webcam_index}')
            
            if old_surgical_mode != new_surgical_mode:
                needs_restart = True
                mode_name = 'Chirurgical' if new_surgical_mode else 'Normal'
                restart_reasons.append(f'mode {mode_name}')
            
            if needs_restart and perception_ui.is_enabled:
                reason_str = ', '.join(restart_reasons)
                ui.notify(f'⚙️ Redémarrage agent ({reason_str})...', type='info')
                perception_ui.restart_perception_agent()
            else:
                ui.notify('✅ Configuration sauvegardée !', type='positive')
                
        except Exception as e:
            ui.notify(f'❌ Erreur sauvegarde: {e}', type='negative')
            print(f"[PERCEPTION-PAGE] Erreur save_config: {e}")
    
    def on_timeline_toggle(e):
        enabled = e.args if isinstance(e.args, bool) else timeline_toggle.value
        perception_ui.current_config['motion_timeline'] = enabled
        # Pas de sauvegarde auto
    
    def on_annotations_toggle(e):
        enabled = e.args if isinstance(e.args, bool) else annotations_toggle.value
        perception_ui.current_config['motion_annotations'] = enabled
        # Pas de sauvegarde auto
    
    def on_save_captures_toggle(e):
        enabled = e.args if isinstance(e.args, bool) else save_captures_toggle.value
        perception_ui.current_config['save_captures'] = enabled
        if enabled:
            ui.notify('💾 Captures seront sauvegardées dans ./captures/', type='info')
        else:
            ui.notify('🚫 Captures non sauvegardées (mode preview uniquement)', type='info')
        # Pas de sauvegarde auto
    
    def on_use_native_resolution_change(e):
        """Callback pour l'option résolution native"""
        enabled = e.args if isinstance(e.args, bool) else use_native_toggle.value
        perception_ui.update_config({'use_native_resolution': enabled})
        
        # Désactiver/activer le sélecteur de résolution selon l'option
        resolution_select.set_enabled(not enabled)
        
        if enabled:
            ui.notify('📐 Résolution native activée - image en taille source', type='positive')
            resolution_hint.set_text('✨ Résolution native : pas de redimensionnement')
        else:
            ui.notify('🔧 Redimensionnement activé selon résolution choisie', type='info')
            resolution_hint.set_text('💡 En mode Normal, choisissez résolution selon besoin')
    
    # Connecter les handlers
    perception_toggle.on('update:model-value', on_toggle_perception)
    capture_btn.on('click', on_capture_click)
    motion_btn.on('click', on_motion_click)
    motion_toggle.on('update:model-value', on_motion_toggle)
    capture_delay_slider.on('update:model-value', on_capture_delay_change)
    motion_interval_slider.on('update:model-value', on_motion_interval_change)
    frames_count_slider.on('update:model-value', on_frames_count_change)
    layout_select.on('update:model-value', on_layout_change)
    timeline_toggle.on('update:model-value', on_timeline_toggle)
    annotations_toggle.on('update:model-value', on_annotations_toggle)
    save_captures_toggle.on('update:model-value', on_save_captures_toggle)
    use_native_toggle.on('update:model-value', on_use_native_resolution_change)
    camera_select.on('update:model-value', on_camera_change)
    resolution_select.on('update:model-value', on_resolution_change)
    display_fps_slider.on('update:model-value', on_display_fps_change)
    stream_quality_slider.on('update:model-value', on_stream_quality_change)
    jpeg_quality_slider.on('update:model-value', on_jpeg_quality_change)
    depth_switch.on('update:model-value', on_depth_change)
    contour_switch.on('update:model-value', on_contour_change)
    contour_canny_cb.on('update:model-value', on_contour_canny_change)
    contour_sobel_cb.on('update:model-value', on_contour_sobel_change)
    contour_laplacian_cb.on('update:model-value', on_contour_laplacian_change)
    contour_adaptive_cb.on('update:model-value', on_contour_adaptive_change)
    contour_canny_low.on('update:model-value', on_contour_canny_low_change)
    contour_canny_high.on('update:model-value', on_contour_canny_high_change)
    contour_thickness.on('update:model-value', on_contour_thickness_change)
    contour_render_mode.on('update:model-value', on_contour_render_mode_change)
    surgical_mode_switch.on('update:model-value', on_surgical_mode_change)
    save_btn.on('click', save_config)  # Bouton sauvegarder
    
    # Initialiser visibilité motion params
    motion_params.set_visibility(perception_ui.current_config.get('motion_capture_enabled', False))
    
    print("[PERCEPTION-PAGE] ✅ Page Perception chargée")
