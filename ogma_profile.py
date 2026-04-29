"""
OGMA Profile Management
=======================
Gestion du profil utilisateur et nettoyage des données.

CONTIENT :
- Modal de configuration profil utilisateur
- Interface de nettoyage des données
- Paramètres debug et transcription
- Outils de maintenance et backup
"""

from nicegui import ui
import asyncio
from pathlib import Path
from datetime import datetime

try:
    from utils.i18n import t, get_lang
except Exception:
    def t(key, **kwargs):
        return key
    def get_lang():
        return 'fr'


def _load_default_identity_instruction(user_name: str) -> str:
    """Retourne le template d'instruction d'identité dans la langue UI active.
    Pas de fallback : si get_lang() retourne autre chose que 'fr' ou 'en', défaut FR.
    """
    if get_lang() == 'en':
        return (
            f"You are speaking with {user_name}.\n\n"
            f"DIRECTIVE:\n"
            f"- Use ONLY memories and knowledge concerning {user_name}\n"
            f"- If you have NO memory of {user_name}, this is a first meeting\n"
            f"- IGNORE any memories concerning other people (even if they appear below)\n"
            f"- Adapt your behaviour according to your real relationship with {user_name}"
        )
    return (
        f"Tu dialogues avec {user_name}.\n\n"
        f"DIRECTIVE :\n"
        f"- Utilise UNIQUEMENT les souvenirs et connaissances concernant {user_name}\n"
        f"- Si tu n'as AUCUN souvenir de {user_name}, c'est une première rencontre\n"
        f"- IGNORE tout souvenir concernant d'autres personnes (même s'ils apparaissent ci-dessous)\n"
        f"- Adapte ton comportement selon ta relation réelle avec {user_name}"
    )


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


def _notify_safe(message: str, type_msg: str = 'info'):
    """Helper pour notifications sécurisées"""
    try:
        if type_msg == 'positive':
            ui.notify(message, type='positive', timeout=3000)
        elif type_msg == 'negative':
            ui.notify(message, type='negative', timeout=5000)
        else:
            ui.notify(message, type='info', timeout=3000)
    except Exception:
        print(f"[NOTIFY] {message}")


def _profile_modal():
    """Modal de configuration du profil et paramètres utilisateur"""
    d = ui.dialog()

    def refresh_content():
        """Rafraîchit dynamiquement le contenu du modal."""
        # Vider le contenu dynamique et le recréer
        dynamic_content.clear()

        with dynamic_content:
            _ensure_settings_manager = _get_ogma_ng_function('_ensure_settings_manager')
            sm = _ensure_settings_manager() if _ensure_settings_manager else None

            if not sm:
                ui.label(t('profile_settings_mgr_unavailable')).classes('text-red-500')
                return

            # === SECTION DEBUG ===
            ui.label(t('profile_section_debug')).classes('text-lg font-medium mb-2')

            # Affichage injections Archiviste
            debug_archiviste = sm.settings.get('debug', {}).get('show_archiviste_injection', False)

            def on_debug_archiviste_change(e):
                if 'debug' not in sm.settings:
                    sm.settings['debug'] = {}
                sm.settings['debug']['show_archiviste_injection'] = e.value
                sm.save_settings()
                ui.notify(t('profile_debug_saved'), type='positive')
            
            ui.checkbox(
                t('profile_debug_archiviste_label'),
                value=debug_archiviste,
                on_change=on_debug_archiviste_change
            ).classes('mb-2')
            
            ui.label(t('profile_debug_archiviste_desc')).classes('text-xs text-muted mb-4')
            ui.separator().classes('my-4')
            ui.label(t('profile_section_vision')).classes('text-lg font-medium mb-2')
            ui.label(t('profile_vision_desc')).classes('text-xs text-muted mb-3')
            
            # Option Depth Map pour Uploads
            process_depth = sm.settings.get('perception', {}).get('process_uploads_with_depth', False)
            
            def on_process_depth_change(e):
                if 'perception' not in sm.settings:
                    sm.settings['perception'] = {}
                sm.settings['perception']['process_uploads_with_depth'] = e.value
                sm.save_settings()
                ui.notify(t('profile_depth_saved'), type='positive')
                
            ui.checkbox(
                '🌊 Depth Map (Carte de profondeur 3D)',
                value=process_depth,
                on_change=on_process_depth_change
            ).classes('mb-2')
            
            # Option Analyse Contours pour Uploads
            process_contour = sm.settings.get('perception', {}).get('process_uploads_with_contour', False)
            
            def on_process_contour_change(e):
                if 'perception' not in sm.settings:
                    sm.settings['perception'] = {}
                sm.settings['perception']['process_uploads_with_contour'] = e.value
                sm.save_settings()
                ui.notify(t('profile_contour_saved'), type='positive')
                # Afficher/masquer les options détaillées
                contour_options_container.set_visibility(e.value)
                
            ui.checkbox(
                '✏️ Analyse Contours (Canny, Sobel - Tracés rouges épais)',
                value=process_contour,
                on_change=on_process_contour_change
            ).classes('mb-2')
            
            # Options détaillées pour les contours (collapsées par défaut)
            contour_options_container = ui.column().classes('ml-6 mb-3')
            contour_options_container.set_visibility(process_contour)
            
            with contour_options_container:
                ui.label(t('profile_contour_methods')).classes('text-sm font-medium mb-1')
                
                # Canny avec tooltip
                canny_enabled = sm.settings.get('perception', {}).get('contour_canny', True)
                def on_canny_change(e):
                    if 'perception' not in sm.settings:
                        sm.settings['perception'] = {}
                    sm.settings['perception']['contour_canny'] = e.value
                    sm.save_settings()
                with ui.row().classes('items-center gap-1'):
                    ui.checkbox(t('profile_contour_canny'), value=canny_enabled, on_change=on_canny_change).classes('text-sm')
                    ui.icon('help_outline', size='xs').classes('text-gray-400 cursor-help').tooltip(t('profile_tooltip_canny'))
                
                # Sobel avec tooltip
                sobel_enabled = sm.settings.get('perception', {}).get('contour_sobel', False)
                def on_sobel_change(e):
                    if 'perception' not in sm.settings:
                        sm.settings['perception'] = {}
                    sm.settings['perception']['contour_sobel'] = e.value
                    sm.save_settings()
                with ui.row().classes('items-center gap-1'):
                    ui.checkbox(t('profile_contour_sobel'), value=sobel_enabled, on_change=on_sobel_change).classes('text-sm')
                    ui.icon('help_outline', size='xs').classes('text-gray-400 cursor-help').tooltip(t('profile_tooltip_sobel'))
                
                # Laplacian avec tooltip
                laplacian_enabled = sm.settings.get('perception', {}).get('contour_laplacian', False)
                def on_laplacian_change(e):
                    if 'perception' not in sm.settings:
                        sm.settings['perception'] = {}
                    sm.settings['perception']['contour_laplacian'] = e.value
                    sm.save_settings()
                with ui.row().classes('items-center gap-1'):
                    ui.checkbox(t('profile_contour_laplacian'), value=laplacian_enabled, on_change=on_laplacian_change).classes('text-sm')
                    ui.icon('help_outline', size='xs').classes('text-gray-400 cursor-help').tooltip(t('profile_tooltip_laplacian'))
                
                # Adaptive avec tooltip
                adaptive_enabled = sm.settings.get('perception', {}).get('contour_adaptive', False)
                def on_adaptive_change(e):
                    if 'perception' not in sm.settings:
                        sm.settings['perception'] = {}
                    sm.settings['perception']['contour_adaptive'] = e.value
                    sm.save_settings()
                with ui.row().classes('items-center gap-1'):
                    ui.checkbox(t('profile_contour_adaptive'), value=adaptive_enabled, on_change=on_adaptive_change).classes('text-sm')
                    ui.icon('help_outline', size='xs').classes('text-gray-400 cursor-help').tooltip(t('profile_tooltip_adaptive'))
                
                ui.label(t('profile_canny_params')).classes('text-sm font-medium mt-2 mb-1')
                
                with ui.row().classes('gap-4 items-end'):
                    # Seuil bas Canny avec tooltip
                    canny_low = sm.settings.get('perception', {}).get('contour_canny_low', 50)
                    def on_canny_low_change(e):
                        if 'perception' not in sm.settings:
                            sm.settings['perception'] = {}
                        sm.settings['perception']['contour_canny_low'] = int(e.value)
                        sm.save_settings()
                    with ui.column().classes('gap-0'):
                        with ui.row().classes('items-center gap-1'):
                            ui.label(t('profile_canny_low')).classes('text-xs')
                            ui.icon('help_outline', size='xs').classes('text-gray-400 cursor-help').tooltip(t('profile_tooltip_canny_low'))
                        ui.number(value=canny_low, min=0, max=255, step=10, on_change=on_canny_low_change).classes('w-20')
                    
                    # Seuil haut Canny avec tooltip
                    canny_high = sm.settings.get('perception', {}).get('contour_canny_high', 150)
                    def on_canny_high_change(e):
                        if 'perception' not in sm.settings:
                            sm.settings['perception'] = {}
                        sm.settings['perception']['contour_canny_high'] = int(e.value)
                        sm.save_settings()
                    with ui.column().classes('gap-0'):
                        with ui.row().classes('items-center gap-1'):
                            ui.label(t('profile_canny_high')).classes('text-xs')
                            ui.icon('help_outline', size='xs').classes('text-gray-400 cursor-help').tooltip(t('profile_tooltip_canny_high'))
                        ui.number(value=canny_high, min=0, max=255, step=10, on_change=on_canny_high_change).classes('w-20')
                    
                    # Épaisseur avec tooltip
                    thickness = sm.settings.get('perception', {}).get('contour_thickness', 2)
                    def on_thickness_change(e):
                        if 'perception' not in sm.settings:
                            sm.settings['perception'] = {}
                        sm.settings['perception']['contour_thickness'] = int(e.value)
                        sm.save_settings()
                    with ui.column().classes('gap-0'):
                        with ui.row().classes('items-center gap-1'):
                            ui.label(t('profile_canny_thickness')).classes('text-xs')
                            ui.icon('help_outline', size='xs').classes('text-gray-400 cursor-help').tooltip(t('profile_tooltip_thickness'))
                        ui.number(value=thickness, min=1, max=10, step=1, on_change=on_thickness_change).classes('w-20')
                
                # Couleur des tracés
                ui.label(t('profile_line_color')).classes('text-sm font-medium mt-2 mb-1')
                line_color = sm.settings.get('perception', {}).get('contour_line_color', 'red')
                def on_line_color_change(e):
                    if 'perception' not in sm.settings:
                        sm.settings['perception'] = {}
                    sm.settings['perception']['contour_line_color'] = e.value
                    sm.save_settings()
                with ui.row().classes('items-center gap-1'):
                    ui.select(
                        options={'red': '🔴 ' + t('profile_color_red'), 'white': '⚪ ' + t('profile_color_white'), 'black': '⚫ ' + t('profile_color_black')},
                        value=line_color,
                        on_change=on_line_color_change
                    ).classes('w-36')
                    ui.icon('help_outline', size='xs').classes('text-gray-400 cursor-help').tooltip(t('profile_tooltip_line_color'))
                
                # Mode de rendu avec tooltip
                ui.label(t('profile_render_mode')).classes('text-sm font-medium mt-2 mb-1')
                render_mode = sm.settings.get('perception', {}).get('contour_render_mode', 'overlay')
                def on_render_mode_change(e):
                    if 'perception' not in sm.settings:
                        sm.settings['perception'] = {}
                    sm.settings['perception']['contour_render_mode'] = e.value
                    sm.save_settings()
                with ui.row().classes('items-center gap-1'):
                    ui.select(
                        options={'overlay': t('profile_render_overlay'), 'black_bg': t('profile_render_black_bg'), 'white_bg': t('profile_render_white_bg')},
                        value=render_mode,
                        on_change=on_render_mode_change
                    ).classes('w-48')
                    ui.icon('help_outline', size='xs').classes('text-gray-400 cursor-help').tooltip(t('profile_tooltip_render_mode'))
            
            ui.label(t('profile_vision_autosave')).classes('text-xs text-muted mb-4')

            # === GESTION DU PROFIL UNIQUE ===
            ui.separator().classes('my-4')
            ui.label(t('profile_section_mgmt')).classes('text-lg font-medium mb-2')
            
            try:
                from profile_manager import ProfileManager
                profile_mgr = ProfileManager()
                
                # Analyser le profil actuel
                current_analysis = profile_mgr.analyze_current_profile()
                identity = current_analysis['identity']
                memory_stats = current_analysis['memory_stats']
                
                # Affichage du profil actuel
                with ui.card().classes('w-full mb-4 p-4 bg-blue-50 border-l-4 border-blue-400'):
                    ui.label(t('profile_current_card_title')).classes('text-md font-medium mb-2')
                    
                    with ui.row().classes('w-full gap-4'):
                        with ui.column().classes('flex-grow'):
                            ui.label(t('profile_current_user', name=identity['user_name'])).classes('text-sm')
                            ui.label(t('profile_current_ai', name=identity['ai_name'])).classes('text-sm')
                            ui.label(t('profile_current_desc', desc=identity['ai_description'])).classes('text-sm')
                        
                        with ui.column().classes('flex-grow'):
                            ui.label(t('profile_current_memories', n=memory_stats['total_memories'])).classes('text-sm')
                            ui.label(t('profile_current_founders', n=memory_stats['founder_memories'])).classes('text-sm')
                            ui.label(t('profile_current_size', size=current_analysis['total_size_mb'])).classes('text-sm')
                
                # Boutons de gestion
                with ui.row().classes('w-full gap-2 mb-4'):
                    
                    # Bouton Sauvegarder
                    def open_save_modal():
                        save_dialog = ui.dialog()
                        
                        with save_dialog, ui.card().classes('popup-content q-dark').style('width: min(500px, 90vw);'):
                            ui.label(t('profile_save_dialog_title')).classes('popup-title')
                            
                            profile_name_input = ui.input(t('profile_save_name_label'), 
                                                        value=f"profil_{identity['ai_name'].lower()}_{datetime.now().strftime('%Y%m%d')}")
                            profile_name_input.classes('w-full mb-3')
                            
                            description_input = ui.textarea(t('profile_save_desc_label'), 
                                                          value=t('profile_save_default_desc', name=identity['ai_name'], date=datetime.now().strftime('%d/%m/%Y')))
                            description_input.classes('w-full mb-3')
                            
                            ui.label(t('profile_save_size_info', size=current_analysis['total_size_mb'])).classes('text-sm text-muted mb-3')
                            
                            with ui.row().classes('w-full gap-2 justify-end'):
                                ui.button(t('profile_btn_cancel'), on_click=save_dialog.close).classes('bg-gray-500')
                                
                                def perform_save():
                                    if not profile_name_input.value.strip():
                                        ui.notify(t('profile_save_name_required'), type='negative')
                                        return
                                    
                                    success, message, backup_path = profile_mgr.save_current_profile(
                                        profile_name_input.value.strip(),
                                        description_input.value.strip()
                                    )
                                    
                                    if success:
                                        ui.notify(t('profile_save_success'), type='positive')
                                        save_dialog.close()
                                        refresh_content()  # Rafraîchir pour afficher la nouvelle sauvegarde
                                    else:
                                        ui.notify(f'Erreur: {message}', type='negative')
                                
                                ui.button(t('profile_btn_save'), on_click=perform_save).classes('bg-blue-600')
                        
                        save_dialog.open()
                    
                    ui.button(t('profile_btn_save_profile'), icon='save', on_click=open_save_modal).classes('bg-blue-600 text-white')
                    
                    # Bouton Supprimer
                    def open_delete_modal():
                        delete_dialog = ui.dialog()
                        
                        with delete_dialog, ui.card().classes('popup-content q-dark').style('width: min(600px, 90vw);'):
                            ui.label(t('profile_delete_dialog_title')).classes('popup-title text-red-500')
                            
                            ui.label(t('profile_delete_warning_title')).classes('text-lg font-medium text-red-500 mb-2')
                            
                            ui.label(t('profile_delete_warning_text')).classes('text-sm mb-2')
                            
                            delete_items = [
                                t('profile_delete_item_memories', n=memory_stats['regular_memories']),
                                t('profile_delete_item_conversations'),
                                t('profile_delete_item_ego'),
                                t('profile_delete_item_images'),
                                t('profile_delete_item_biographies'), 
                                t('profile_delete_item_journal'),
                                t('profile_delete_item_planner'),
                                t('profile_delete_item_apikeys'),
                                t('profile_delete_item_extensions'),
                                t('profile_delete_item_logs')
                            ]
                            
                            for item in delete_items:
                                ui.label(f"  • {item}").classes('text-sm ml-4')
                            
                            ui.separator().classes('my-4')
                            
                            # Option sauvegarde avant suppression
                            save_before_delete = ui.checkbox(t('profile_delete_save_before'), value=True).classes('mb-3')
                            
                            ui.label(t('profile_delete_confirm_label')).classes('text-sm font-medium mb-2')
                            confirmation_input = ui.input(t('profile_delete_confirm_input')).classes('w-full mb-3')
                            
                            # Spinner + statut (masqué par défaut)
                            with ui.row().classes('w-full items-center gap-2 mb-2') as _del_spinner_row:
                                _del_spinner_row.set_visibility(False)
                                ui.spinner(size='sm').classes('text-orange-400')
                                _del_status_label = ui.label('').classes('text-sm text-orange-400')
                            
                            _del_btn_ref = [None]  # référence mutable au bouton
                            
                            with ui.row().classes('w-full gap-2 justify-end'):
                                ui.button(t('profile_btn_cancel'), on_click=delete_dialog.close).classes('bg-gray-500')
                                
                                async def perform_delete():
                                    if confirmation_input.value != "DELETE-PROFILE-OGMA":
                                        ui.notify(t('profile_delete_wrong_code'), type='negative')
                                        return
                                    
                                    btn = _del_btn_ref[0]
                                    if btn:
                                        btn.disable()
                                    _del_spinner_row.set_visibility(True)
                                    
                                    # Étape 1 : sauvegarde préalable
                                    if save_before_delete.value:
                                        _del_status_label.set_text(t('profile_delete_saving'))
                                        await asyncio.sleep(0.05)
                                        save_name = f"backup_avant_suppression_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                                        save_ok, save_msg, _ = await asyncio.to_thread(
                                            profile_mgr.save_current_profile,
                                            save_name,
                                            t('profile_delete_auto_save_desc')
                                        )
                                        if not save_ok:
                                            _del_spinner_row.set_visibility(False)
                                            if btn:
                                                btn.enable()
                                            ui.notify(t('profile_delete_save_error', msg=save_msg), type='negative')
                                            return
                                        ui.notify(t('profile_delete_save_created'), type='positive')
                                    
                                    # Étape 2 : suppression du profil
                                    _del_status_label.set_text(t('profile_delete_deleting'))
                                    await asyncio.sleep(0.05)
                                    success, message = await asyncio.to_thread(
                                        profile_mgr.delete_current_profile, "DELETE-PROFILE-OGMA"
                                    )
                                    
                                    _del_spinner_row.set_visibility(False)
                                    
                                    if success:
                                        delete_dialog.close()
                                        refresh_content()
                                        ui.notify(t('profile_delete_success'), type='positive', timeout=5000)
                                        ui.notify(t('profile_delete_restart_note'), type='warning', timeout=0)
                                    else:
                                        if btn:
                                            btn.enable()
                                        ui.notify(f'Erreur : {message}', type='negative')
                                
                                _del_btn_ref[0] = ui.button(t('profile_btn_delete_permanently'), on_click=perform_delete).classes('bg-red-600 text-white')
                        
                        delete_dialog.open()
                    
                    ui.button(t('profile_btn_delete_profile'), icon='delete', on_click=open_delete_modal).classes('bg-red-600 text-white')
                
                # Liste des sauvegardes disponibles
                ui.separator().classes('my-4')
                ui.label(t('profile_section_backups')).classes('text-lg font-medium mb-2')
                
                backups = profile_mgr.list_available_backups()
                
                if backups:
                    for backup in backups:
                        with ui.card().classes('w-full mb-2 p-3 bg-gray-50 hover:bg-gray-100'):
                            with ui.row().classes('w-full items-center gap-4'):
                                with ui.column().classes('flex-grow'):
                                    ui.label(f"📁 {backup['profile_name']}").classes('font-medium')
                                    ui.label(f"👤 {backup['user_name']} ↔ 🤖 {backup['ai_name']}").classes('text-sm text-gray-600')
                                    if backup['description']:
                                        ui.label(f"📝 {backup['description']}").classes('text-xs text-gray-500')
                                
                                with ui.column().classes('text-right'):
                                    created_date = backup['created_at'][:10] if len(backup['created_at']) > 10 else backup['created_at']
                                    ui.label(f"📅 {created_date}").classes('text-sm')
                                    ui.label(f"💾 {backup['size_mb']} MB").classes('text-xs text-gray-500')
                                
                                def create_load_handler(backup_path):
                                    def load_backup():
                                        load_dialog = ui.dialog()
                                        
                                        with load_dialog, ui.card().classes('popup-content q-dark').style('width: min(500px, 90vw);'):
                                            ui.label(t('profile_load_dialog_title')).classes('popup-title')
                                            
                                            ui.label(t('profile_load_warning')).classes('text-lg font-medium text-orange-500 mb-3')
                                            
                                            ui.label(t('profile_load_name_label', name=backup['profile_name'])).classes('font-medium mb-2')
                                            ui.label(f"👤 {backup['user_name']} ↔ 🤖 {backup['ai_name']}").classes('text-sm mb-2')
                                            ui.label(t('profile_load_size_label', size=backup['size_mb'])).classes('text-sm mb-3')
                                            
                                            if backup['description']:
                                                ui.label(f"📝 {backup['description']}").classes('text-sm text-gray-600 mb-3')
                                            
                                            ui.label(t('profile_load_restored')).classes('text-xs text-green-400 mb-1')
                                            ui.label(t('profile_load_auto_save_note')).classes('text-xs text-muted mb-4')
                                            
                                            with ui.row().classes('w-full gap-2 justify-end'):
                                                ui.button(t('profile_btn_cancel'), on_click=load_dialog.close).classes('bg-gray-500')
                                                
                                                def perform_load():
                                                    backup_path_obj = Path(backup_path)
                                                    success, message = profile_mgr.load_profile_backup(backup_path_obj)
                                                    
                                                    if success:
                                                        ui.notify(t('profile_load_success'), type='positive')
                                                        load_dialog.close()
                                                        refresh_content()  # Rafraîchir complètement l'interface
                                                    else:
                                                        ui.notify(f'Erreur: {message}', type='negative')
                                                
                                                ui.button(t('profile_btn_load_profile'), on_click=perform_load).classes('bg-green-600 text-white')
                                        
                                        load_dialog.open()
                                    
                                    return load_backup
                                
                                def create_delete_handler(bk_path, bk_name, bk_user, bk_ai, bk_size):
                                    def delete_backup_click():
                                        del_dialog = ui.dialog()
                                        
                                        with del_dialog, ui.card().classes('popup-content q-dark').style('width: min(480px, 90vw);'):
                                            ui.label(t('profile_delete_backup_title')).classes('popup-title')
                                            
                                            ui.label(t('profile_delete_backup_irreversible')).classes('text-lg font-medium text-red-500 mb-3')
                                            
                                            with ui.card().classes('w-full p-3 mb-4 bg-gray-800 border border-red-400'):
                                                ui.label(f"📁 {bk_name}").classes('font-medium text-sm')
                                                ui.label(f"👤 {bk_user} ↔ 🤖 {bk_ai}").classes('text-xs text-gray-400')
                                                ui.label(f"💾 {bk_size} MB").classes('text-xs text-gray-400')
                                            
                                            ui.label(t('profile_delete_backup_text')).classes('text-xs text-gray-400 mb-4')
                                            
                                            # Spinner suppression backup (masqué par défaut)
                                            with ui.row().classes('items-center gap-2 mb-2') as _bk_spinner_row:
                                                _bk_spinner_row.set_visibility(False)
                                                ui.spinner(size='sm').classes('text-orange-400')
                                                ui.label(t('profile_deleting_backup')).classes('text-sm text-orange-400')
                                            
                                            _bk_btn_ref = [None]
                                            
                                            with ui.row().classes('w-full gap-2 justify-end'):
                                                ui.button(t('profile_btn_cancel'), on_click=del_dialog.close).classes('bg-gray-500')
                                                
                                                async def perform_delete_backup():
                                                    if _bk_btn_ref[0]:
                                                        _bk_btn_ref[0].disable()
                                                    _bk_spinner_row.set_visibility(True)
                                                    await asyncio.sleep(0.05)
                                                    from pathlib import Path as _Path
                                                    success, message = await asyncio.to_thread(
                                                        profile_mgr.delete_backup, _Path(bk_path)
                                                    )
                                                    _bk_spinner_row.set_visibility(False)
                                                    if success:
                                                        ui.notify(f'✅ {message}', type='positive', timeout=5000)
                                                        del_dialog.close()
                                                        refresh_content()
                                                    else:
                                                        if _bk_btn_ref[0]:
                                                            _bk_btn_ref[0].enable()
                                                        ui.notify(f'Erreur : {message}', type='negative')
                                                
                                                _bk_btn_ref[0] = ui.button(t('profile_btn_delete_def'), on_click=perform_delete_backup).classes('bg-red-600 text-white')
                                        
                                        del_dialog.open()
                                    
                                    return delete_backup_click
                                
                                with ui.row().classes('gap-2'):
                                    ui.button(t('profile_btn_load'), icon='folder_open', 
                                             on_click=create_load_handler(backup['path'])).classes('bg-green-600 text-white')
                                    ui.button('🗑️', icon='delete',
                                             on_click=create_delete_handler(
                                                 backup['path'], backup['profile_name'],
                                                 backup['user_name'], backup['ai_name'],
                                                 backup['size_mb']
                                             )).classes('bg-red-700 text-white').tooltip(t('profile_tooltip_delete_backup'))
                else:
                    ui.label(t('profile_no_backup')).classes('text-gray-500 text-center py-4')
            
            except Exception as e:
                ui.label(f'⚠️ Erreur ProfileManager : {e}').classes('text-red-500')
                print(f"[PROFILE] Erreur: {e}")

            # === SNAPSHOT CONFIG (Clés API + Instructions) ===
            ui.separator().classes('my-4')
            ui.label(t('profile_section_config_snapshot')).classes('text-lg font-medium mb-2')
            ui.label(t('profile_config_snapshot_desc')).classes('text-xs text-muted mb-3')

            try:
                from profile_manager import ProfileManager
                config_mgr = ProfileManager()

                # Boutons Sauvegarder config
                def open_save_config_modal():
                    save_cfg_dialog = ui.dialog()

                    with save_cfg_dialog, ui.card().classes('popup-content q-dark').style('width: min(500px, 90vw);'):
                        ui.label(t('profile_config_save_dialog_title')).classes('popup-title')

                        cfg_name_input = ui.input(t('profile_config_name_label'),
                                                  value=f"config_{datetime.now().strftime('%Y%m%d')}")
                        cfg_name_input.classes('w-full mb-3')

                        cfg_desc_input = ui.textarea(t('profile_save_desc_label'),
                                                     value='').props('rows=2')
                        cfg_desc_input.classes('w-full mb-3')

                        ui.label(t('profile_config_saved_content')).classes('text-sm font-medium mb-1')
                        for item in ['🔑 Clés IA providers (Chat, Reasoning, Embedding)',
                                     '🔑 Coffre multi-providers (GROK, OpenAI, Google, Mistral, Kie, WaveSpeed…)',
                                     '🎨 Providers image (text2img, img2img, modèles)',
                                     '🔊 Audio (TTS : Fish Audio, Cartesia, ElevenLabs, engine)',
                                     '🔍 Web (Serper), 🎙️ STT, 📱 Telegram bot token',
                                     '📝 Instructions générales (system, mémorisation, injection, perception, salutations, temporal)',
                                     '🖼️ Instructions images (T2I guide, I2I guide, preprocessor, concision, vision feedback)']:
                            ui.label(f'  • {item}').classes('text-xs text-gray-400')

                        with ui.row().classes('w-full gap-2 justify-end mt-3'):
                            ui.button(t('profile_btn_cancel'), on_click=save_cfg_dialog.close).classes('bg-gray-500')

                            def perform_save_config():
                                if not cfg_name_input.value.strip():
                                    ui.notify(t('profile_config_save_name_required'), type='negative')
                                    return
                                success, message, _ = config_mgr.save_config_snapshot(
                                    cfg_name_input.value.strip(),
                                    cfg_desc_input.value.strip()
                                )
                                if success:
                                    ui.notify(f'✅ {message}', type='positive')
                                    save_cfg_dialog.close()
                                    refresh_content()
                                else:
                                    ui.notify(f'Erreur: {message}', type='negative')

                            ui.button(t('profile_btn_save'), on_click=perform_save_config).classes('bg-teal-600 text-white')

                    save_cfg_dialog.open()

                ui.button(t('profile_btn_save_config'), icon='key', on_click=open_save_config_modal).classes('bg-teal-600 text-white mb-3')

                # Liste des snapshots existants
                config_snapshots = config_mgr.list_config_snapshots()

                if config_snapshots:
                    for snap in config_snapshots:
                        with ui.card().classes('w-full mb-2 p-3 bg-gray-50 hover:bg-gray-100'):
                            with ui.row().classes('w-full items-center gap-4'):
                                with ui.column().classes('flex-grow'):
                                    ui.label(f'🔑 {snap["name"]}').classes('font-medium text-sm')
                                    if snap['description']:
                                        ui.label(f'📝 {snap["description"]}').classes('text-xs text-gray-500')
                                    created = snap['created_at'][:16].replace('T', ' ') if snap['created_at'] else ''
                                    ui.label(f'📅 {created} • {snap["size_kb"]} KB • {snap["api_key_count"]} clés').classes('text-xs text-gray-400')

                                def create_load_config_handler(snap_path, snap_name):
                                    def load_config_click():
                                        load_cfg_dialog = ui.dialog()

                                        with load_cfg_dialog, ui.card().classes('popup-content q-dark').style('width: min(480px, 90vw);'):
                                            ui.label(t('profile_config_load_dialog_title')).classes('popup-title')
                                            ui.label(t('profile_load_name_label', name=snap_name)).classes('font-medium mb-2')
                                            ui.label(t('profile_config_load_warning')).classes('text-sm text-orange-400 mb-2')
                                            ui.label(t('profile_config_load_reset_note')).classes('text-xs text-gray-400 mb-3')

                                            with ui.row().classes('w-full gap-2 justify-end'):
                                                ui.button(t('profile_btn_cancel'), on_click=load_cfg_dialog.close).classes('bg-gray-500')

                                                def perform_load_config():
                                                    success, message = config_mgr.load_config_snapshot(Path(snap_path))
                                                    if success:
                                                        ui.notify(f'✅ {message}', type='positive', timeout=5000)
                                                        load_cfg_dialog.close()
                                                        refresh_content()
                                                    else:
                                                        ui.notify(f'Erreur: {message}', type='negative')

                                                ui.button(t('profile_btn_load'), on_click=perform_load_config).classes('bg-green-600 text-white')

                                        load_cfg_dialog.open()
                                    return load_config_click

                                def create_delete_config_handler(snap_path, snap_name):
                                    def delete_config_click():
                                        del_cfg_dialog = ui.dialog()

                                        with del_cfg_dialog, ui.card().classes('popup-content q-dark').style('width: min(400px, 90vw);'):
                                            ui.label(t('profile_config_delete_dialog_title')).classes('popup-title')
                                            ui.label(t('profile_config_delete_text', name=snap_name)).classes('font-medium mb-2')
                                            ui.label(t('profile_config_irreversible')).classes('text-xs text-red-400 mb-3')

                                            with ui.row().classes('w-full gap-2 justify-end'):
                                                ui.button(t('profile_btn_cancel'), on_click=del_cfg_dialog.close).classes('bg-gray-500')

                                                def perform_delete_config():
                                                    success, message = config_mgr.delete_config_snapshot(Path(snap_path))
                                                    if success:
                                                        ui.notify(f'✅ {message}', type='positive')
                                                        del_cfg_dialog.close()
                                                        refresh_content()
                                                    else:
                                                        ui.notify(f'Erreur: {message}', type='negative')

                                                ui.button(t('profile_btn_delete'), on_click=perform_delete_config).classes('bg-red-600 text-white')

                                        del_cfg_dialog.open()
                                    return delete_config_click

                                with ui.row().classes('gap-2'):
                                    ui.button(t('profile_btn_load'), icon='download',
                                             on_click=create_load_config_handler(snap['path'], snap['name'])).classes('bg-green-600 text-white')
                                    ui.button('🗑️', icon='delete',
                                             on_click=create_delete_config_handler(snap['path'], snap['name'])).classes('bg-red-700 text-white').tooltip(t('profile_tooltip_delete_snapshot'))
                else:
                    ui.label(t('profile_no_config_snapshot')).classes('text-gray-500 text-center py-2')

            except Exception as e:
                ui.label(f'⚠️ Erreur Config Snapshot : {e}').classes('text-red-500')
                print(f"[CONFIG-SNAPSHOT] Erreur UI: {e}")

            # === HOLOGRAMME PROJECTOR ===
            ui.separator().classes('my-4')
            with ui.row().classes('items-center gap-2 mb-1'):
                ui.icon('wb_incandescent', size='sm').classes('text-amber-400')
                ui.label(t('profile_hologram_title')).classes('text-lg font-medium')
                ui.badge(t('profile_hologram_experimental'), color='orange').classes('text-xs')

            ui.label(t('profile_hologram_desc')).classes('text-xs text-muted mb-3')

            def _get_hologram_lan_url() -> str:
                """Détecte l'IP LAN du serveur et retourne l'URL hologramme."""
                import socket, os
                port = int(os.getenv('OGMA_PORT', '8080'))
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.connect(('8.8.8.8', 80))
                    ip = s.getsockname()[0]
                    s.close()
                    return f"http://{ip}:{port}/hologram"
                except Exception:
                    return f"http://localhost:{port}/hologram"

            with ui.row().classes('items-center gap-3 mb-3'):
                # Toggle activer/désactiver
                try:
                    from extensions.hologram_projector.state_emitter import is_enabled as _holo_is_enabled, set_enabled as _holo_set_enabled
                    holo_enabled = _holo_is_enabled()
                except Exception:
                    holo_enabled = False

                def _on_holo_toggle(e):
                    try:
                        from extensions.hologram_projector.state_emitter import set_enabled
                        set_enabled(e.value)
                        state = t('profile_hologram_state_on') if e.value else t('profile_hologram_state_off')
                        ui.notify(t('profile_hologram_notify_state', state=state), type='positive' if e.value else 'warning', timeout=2000)
                    except Exception as err:
                        ui.notify(t('profile_hologram_error', err=err), type='negative')

                holo_toggle = ui.switch(
                    t('profile_hologram_toggle'),
                    value=holo_enabled,
                    on_change=_on_holo_toggle,
                ).classes('mr-2')

                # Bouton "Comment ça marche ?"
                def _open_hologram_howto():
                    url = _get_hologram_lan_url()
                    howto_dialog = ui.dialog()
                    with howto_dialog, ui.card().classes('popup-content q-dark').style('width: min(560px, 92vw); max-height: 85vh; overflow-y: auto;'):
                        with ui.row().classes('items-center gap-2 mb-3'):
                            ui.icon('wb_incandescent', size='md').classes('text-amber-400')
                            ui.label(t('profile_hologram_howto_title')).classes('popup-title')

                        ui.separator().classes('mb-3')

                        ui.label(t('profile_hologram_pyramid_title')).classes('text-md font-semibold mb-1')
                        ui.label(t('profile_hologram_pyramid_desc')).classes('text-sm text-muted mb-3')

                        ui.label(t('profile_hologram_steps_title')).classes('text-md font-semibold mb-2')
                        steps = [
                            t('profile_hologram_step_1'),
                            t('profile_hologram_step_2'),
                            t('profile_hologram_step_3'),
                            t('profile_hologram_step_4'),
                            t('profile_hologram_step_5'),
                            t('profile_hologram_step_6'),
                        ]
                        for step in steps:
                            ui.label(step).classes('text-sm mb-1')

                        ui.separator().classes('my-3')
                        ui.label(t('profile_hologram_url_title')).classes('text-md font-semibold mb-2')

                        def _copy_url():
                            ui.run_javascript(f"navigator.clipboard.writeText('{url}')")
                            ui.notify(t('profile_hologram_url_copied'), type='positive', timeout=1500)
                        ui.input(value=url).props('readonly outlined dense color=amber').classes('w-full font-mono mb-1')
                        ui.button(t('profile_btn_copy_url'), icon='content_copy', on_click=_copy_url).props('flat dense color=grey-4 size=sm').classes('mb-3')

                        ui.label(t('profile_hologram_url_warning')).classes('text-xs text-orange-400 mb-3')

                        ui.label(t('profile_hologram_alt_title')).classes('text-md font-semibold mb-1')
                        alt_url = url.replace('/hologram', '/hologram2')
                        ui.label(t('profile_hologram_alt_desc', url=alt_url)).classes('text-xs text-muted font-mono mb-3')

                        with ui.row().classes('w-full justify-end mt-2'):
                            ui.button(t('profile_btn_close'), on_click=howto_dialog.close).classes('bg-gray-600')

                    howto_dialog.open()

                ui.button(
                    t('profile_btn_hologram_howto'),
                    icon='help_outline',
                    on_click=_open_hologram_howto,
                ).props('outline color=amber').classes('text-sm')

            # === IDENTITÉS ===
            ui.separator().classes('my-4')
            ui.label(t('profile_section_identity')).classes('text-lg font-medium mb-2')
            
            # Récupération des identités actuelles
            try:
                from identity_manager import get_identity_manager
                identity_manager = get_identity_manager()
                current_identity = identity_manager.get_current_identity()
                
                # Nom utilisateur
                with ui.row().classes('w-full items-center gap-2 mb-2'):
                    user_input = ui.input(t('profile_username_label'), value=current_identity['user_name']).classes('flex-grow')
                    
                    def update_user_name():
                        if user_input.value.strip():
                            new_name = user_input.value.strip()
                            
                            # Mettre à jour le profil actuel
                            current_profile_id = identity_manager.get_current_profile_id()
                            if current_profile_id and current_profile_id in identity_manager._data['profiles']:
                                # Capturer l'ancien nom AVANT la mise à jour
                                old_name = identity_manager._data['profiles'][current_profile_id].get('user_name', '')
                                identity_manager._data['profiles'][current_profile_id]['user_name'] = new_name

                                # Mettre à jour l'instruction d'identité si elle contient l'ancien nom
                                if old_name and old_name != new_name:
                                    saved_instr = identity_manager._data['profiles'][current_profile_id].get('identity_instruction', '')
                                    if saved_instr:
                                        updated_instr = saved_instr.replace(old_name, new_name)
                                        identity_manager._data['profiles'][current_profile_id]['identity_instruction'] = updated_instr
                                        instruction_input.set_value(updated_instr)
                                        print(f"[IDENTITY] Instruction mise a jour: '{old_name}' -> '{new_name}'")
                                    else:
                                        # Pas d'instruction sauvegardée : rafraichir le template affiché (langue active)
                                        new_template = _load_default_identity_instruction(new_name)
                                        instruction_input.set_value(new_template)

                                identity_manager.save_identities()
                                
                                # === SYNCHRONISATION SESSION ===
                                # Mettre à jour cookie session + settings.json
                                try:
                                    from nicegui import app
                                    if app.storage.user.get('ogma_user'):
                                        app.storage.user['ogma_user']['name'] = new_name
                                        print(f"[SESSION] ✅ Cookie mis à jour: {new_name}")
                                    
                                    # Sauvegarder aussi dans settings.json
                                    try:
                                        import sys
                                        ogma_ng = sys.modules.get('ogma_ng')
                                        if ogma_ng:
                                            sm_func = getattr(ogma_ng, '_ensure_settings_manager', None)
                                            if sm_func:
                                                sm = sm_func()
                                                if sm:
                                                    if 'profile' not in sm.settings:
                                                        sm.settings['profile'] = {}
                                                    sm.settings['profile']['user_name'] = new_name
                                                    sm.save_settings()
                                                    print(f"[SESSION] ✅ Settings.json mis à jour")
                                    except Exception as e2:
                                        print(f"[SESSION] ⚠️ Erreur settings.json: {e2}")
                                except Exception as e:
                                    print(f"[SESSION] ⚠️ Erreur mise à jour cookie: {e}")
                                
                                # Mettre à jour variable globale
                                try:
                                    import sys
                                    ogma_ng = sys.modules.get('ogma_ng')
                                    if ogma_ng:
                                        ogma_ng._current_user_name = new_name
                                        print(f"[SESSION] ✅ Variable globale mise à jour: {new_name}")
                                except Exception as e:
                                    print(f"[SESSION] ⚠️ Erreur mise à jour variable: {e}")
                                # === FIN SYNCHRONISATION ===
                                
                                ui.notify(t('profile_username_updated', name=new_name), type='positive')
                            else:
                                ui.notify(t('profile_update_err'), type='negative')
                        else:
                            ui.notify(t('profile_username_empty_err'), type='negative')
                    
                    ui.button(t('profile_btn_validate'), on_click=update_user_name).props('color=primary')
                
                # Nom IA
                with ui.row().classes('w-full items-center gap-2 mb-4'):
                    ai_input = ui.input(t('profile_ai_name_label'), value=current_identity['ai_name']).classes('flex-grow')
                    
                    def update_ai_name():
                        if ai_input.value.strip():
                            # Mettre à jour le profil actuel
                            current_profile_id = identity_manager.get_current_profile_id()
                            if current_profile_id and current_profile_id in identity_manager._data['profiles']:
                                identity_manager._data['profiles'][current_profile_id]['ai_name'] = ai_input.value.strip()
                                identity_manager.save_identities()
                                ui.notify(t('profile_ai_updated', name=ai_input.value.strip()), type='positive')
                            else:
                                ui.notify(t('profile_update_err'), type='negative')
                        else:
                            ui.notify(t('profile_ai_empty_err'), type='negative')
                    
                    ui.button(t('profile_btn_validate'), on_click=update_ai_name).props('color=primary')
                
                # Instruction d'identité personnalisée
                ui.label(t('profile_identity_instr_label')).classes('text-sm font-medium mb-1 mt-4')
                ui.label(t('profile_identity_instr_desc')).classes('text-xs text-gray-400 mb-2')
                
                # Récupérer l'instruction actuelle ou utiliser le template par défaut
                current_profile_id = identity_manager.get_current_profile_id()
                current_instruction = ""
                if current_profile_id and current_profile_id in identity_manager._data['profiles']:
                    current_instruction = identity_manager._data['profiles'][current_profile_id].get('identity_instruction', '')
                    # Réparation auto : si l'instruction contient un ancien prénom différent de user_name
                    # (supporte FR "Tu dialogues avec " et EN "You are speaking with ")
                    if current_instruction:
                        stored_user_name = identity_manager._data['profiles'][current_profile_id].get('user_name', '')
                        for prefix in ('Tu dialogues avec ', 'You are speaking with '):
                            if stored_user_name and prefix in current_instruction:
                                start = current_instruction.index(prefix) + len(prefix)
                                end = current_instruction.find('.', start)
                                if end > start:
                                    name_in_instr = current_instruction[start:end]
                                    if name_in_instr.lower() != stored_user_name.lower():
                                        current_instruction = current_instruction.replace(name_in_instr, stored_user_name)
                                        identity_manager._data['profiles'][current_profile_id]['identity_instruction'] = current_instruction
                                        identity_manager.save_identities()
                                        print(f"[IDENTITY] Instruction réparée automatiquement: '{name_in_instr}' -> '{stored_user_name}'")
                                break
                
                # Si vide, utiliser le template par défaut (langue active)
                if not current_instruction:
                    current_instruction = _load_default_identity_instruction(current_identity['user_name'])
                
                instruction_input = ui.textarea(t('profile_identity_textarea_label'), value=current_instruction).classes('w-full').props('rows=6 outlined')
                
                def update_identity_instruction():
                    if instruction_input.value.strip():
                        new_instruction = instruction_input.value.strip()
                        
                        # Mettre à jour le profil actuel
                        current_profile_id = identity_manager.get_current_profile_id()
                        if current_profile_id and current_profile_id in identity_manager._data['profiles']:
                            identity_manager._data['profiles'][current_profile_id]['identity_instruction'] = new_instruction
                            identity_manager.save_identities()
                            ui.notify(t('profile_identity_updated'), type='positive')
                            print(f"[IDENTITY] ✅ Instruction personnalisée sauvegardée ({len(new_instruction)} chars)")
                        else:
                            ui.notify(t('profile_update_err'), type='negative')
                    else:
                        ui.notify(t('profile_identity_empty_err'), type='negative')
                
                with ui.row().classes('w-full justify-end gap-2 mt-2'):
                    ui.button(t('profile_identity_reset_btn'),
                              on_click=lambda: instruction_input.set_value(
                                  _load_default_identity_instruction(current_identity['user_name'])
                              )).props('flat color=secondary')
                    ui.button(t('profile_btn_validate'), on_click=update_identity_instruction).props('color=primary')
                
            except Exception as e:
                ui.label(f"❌ Erreur : {e}").classes('text-red-500')

            # === MODE CONVERSATION VOCALE (Module Voice - Janvier 2026) ===
            ui.separator().classes('my-4')
            ui.label(t('profile_section_voice')).classes('text-lg font-medium mb-2')
            
            # Charger la config voice
            voice_config = sm.settings.get('voice', {})
            voice_enabled = voice_config.get('enabled', False)
            trigger_activation = voice_config.get('trigger_activation', 'louna louna')
            trigger_send = voice_config.get('trigger_send', 'point final')
            listening_timeout = voice_config.get('listening_timeout', 1.0)
            phrase_time_limit = voice_config.get('phrase_time_limit', 15.0)
            pause_threshold = voice_config.get('pause_threshold', 3.0)
            continuous_mode = voice_config.get('continuous_mode', False)
            auto_send_delay = voice_config.get('auto_send_delay', 5.0)
            
            def on_voice_mode_change(e):
                if 'voice' not in sm.settings:
                    sm.settings['voice'] = {}
                sm.settings['voice']['enabled'] = e.value
                sm.save_settings()
                
                if e.value:
                    ui.notify(t('profile_voice_activated_notify'), type='positive')
                else:
                    ui.notify(t('profile_voice_deactivated_notify'), type='info')
                
                refresh_content()
            
            with ui.card().classes('w-full p-3 mb-3 bg-gradient-to-r from-purple-900/20 to-blue-900/20 border border-purple-500/30'):
                ui.label(t('profile_voice_card_title')).classes('text-md font-medium mb-2')
                
                with ui.row().classes('items-center gap-2 mb-2'):
                    ui.checkbox(
                        t('profile_voice_enable'),
                        value=voice_enabled,
                        on_change=on_voice_mode_change
                    ).classes('mb-0')
                    
                    if voice_enabled:
                        ui.badge(t('profile_badge_active'), color='positive').classes('text-xs animate-pulse')
                    else:
                        ui.badge(t('profile_badge_inactive'), color='secondary').classes('text-xs')
                
                ui.label(t('profile_voice_principle')).classes('text-xs text-muted mb-2')
                
                if voice_enabled:
                    # Mode conversation continue
                    def on_continuous_mode_change(e):
                        if 'voice' not in sm.settings:
                            sm.settings['voice'] = {}
                        sm.settings['voice']['continuous_mode'] = e.value
                        sm.save_settings()
                        
                        if e.value:
                            ui.notify(t('profile_voice_continuous_activated_notify'), type='positive')
                        else:
                            ui.notify(t('profile_voice_continuous_deactivated_notify'), type='info')
                        
                        # Recharger config dans le module voice
                        try:
                            from modules.voice import get_voice_manager
                            vm = get_voice_manager()
                            if vm:
                                vm.reload_config()
                        except:
                            pass
                        
                        refresh_content()
                    
                    ui.separator().classes('my-2')
                    with ui.row().classes('items-center gap-2 mb-2'):
                        ui.checkbox(
                            t('profile_voice_continuous_mode'),
                            value=continuous_mode,
                            on_change=on_continuous_mode_change
                        ).classes('mb-0')
                        
                        if continuous_mode:
                            ui.badge(t('profile_badge_continuous'), color='warning').classes('text-xs animate-pulse')
                    
                    if continuous_mode:
                        with ui.element('div').classes('text-xs text-orange-300 mb-2 p-2 bg-orange-900/20 rounded'):
                            ui.label(t('profile_voice_continuous_desc_1'))
                            ui.label(t('profile_voice_continuous_desc_2'))
                    
                    # Configuration du mot d'activation
                    def on_trigger_activation_change(e):
                        if 'voice' not in sm.settings:
                            sm.settings['voice'] = {}
                        sm.settings['voice']['trigger_activation'] = e.value.lower().strip()
                        sm.save_settings()
                        ui.notify(t('profile_voice_activation_saved', word=e.value), type='positive')
                        # Recharger config dans le module voice si disponible
                        try:
                            from modules.voice import get_voice_manager
                            vm = get_voice_manager()
                            if vm:
                                vm.reload_config()
                        except:
                            pass
                    
                    ui.input(
                        label=t('profile_label_stt_activation_word'),
                        value=trigger_activation,
                        on_change=on_trigger_activation_change
                    ).classes('w-full mb-2').props('dense')
                    
                    # Configuration du mot d'envoi
                    def on_trigger_send_change(e):
                        if 'voice' not in sm.settings:
                            sm.settings['voice'] = {}
                        sm.settings['voice']['trigger_send'] = e.value.lower().strip()
                        sm.save_settings()
                        ui.notify(t('profile_voice_send_saved', word=e.value), type='positive')
                        # Recharger config dans le module voice si disponible
                        try:
                            from modules.voice import get_voice_manager
                            vm = get_voice_manager()
                            if vm:
                                vm.reload_config()
                        except:
                            pass
                    
                    ui.input(
                        label=t('profile_label_stt_send_word'),
                        value=trigger_send,
                        on_change=on_trigger_send_change
                    ).classes('w-full mb-2').props('dense')
                    
                    with ui.element('div').classes('text-xs text-green-400 space-y-1'):
                        ui.label(t('profile_voice_tips_activation', word=trigger_activation))
                        ui.label(t('profile_voice_tips_send', word=trigger_send))
                    
                    # Paramètres audio avancés
                    ui.separator().classes('my-3')
                    ui.label(t('profile_voice_advanced_params')).classes('text-sm font-medium mb-2')
                    
                    # Listening timeout
                    def on_listening_timeout_change(e):
                        try:
                            value = float(e.value)
                            if 'voice' not in sm.settings:
                                sm.settings['voice'] = {}
                            sm.settings['voice']['listening_timeout'] = value
                            sm.save_settings()
                            ui.notify(t('profile_voice_timeout_saved', val=value), type='positive')
                            try:
                                from modules.voice import get_voice_manager
                                vm = get_voice_manager()
                                if vm:
                                    vm.reload_config()
                            except:
                                pass
                        except ValueError:
                            ui.notify(t('profile_voice_invalid_value'), type='negative')
                    
                    ui.number(
                        label=t('profile_label_stt_timeout'),
                        value=listening_timeout,
                        min=0.5,
                        max=10.0,
                        step=0.5,
                        on_change=on_listening_timeout_change
                    ).classes('w-full mb-2').props('dense')
                    
                    # Phrase time limit
                    def on_phrase_time_limit_change(e):
                        try:
                            value = float(e.value)
                            if 'voice' not in sm.settings:
                                sm.settings['voice'] = {}
                            sm.settings['voice']['phrase_time_limit'] = value
                            sm.save_settings()
                            ui.notify(t('profile_voice_duration_saved', val=value), type='positive')
                            try:
                                from modules.voice import get_voice_manager
                                vm = get_voice_manager()
                                if vm:
                                    vm.reload_config()
                            except:
                                pass
                        except ValueError:
                            ui.notify(t('profile_voice_invalid_value'), type='negative')
                    
                    ui.number(
                        label=t('profile_label_stt_max_duration'),
                        value=phrase_time_limit,
                        min=5.0,
                        max=60.0,
                        step=5.0,
                        on_change=on_phrase_time_limit_change
                    ).classes('w-full mb-2').props('dense')
                    
                    # Pause threshold
                    def on_pause_threshold_change(e):
                        try:
                            value = float(e.value)
                            if 'voice' not in sm.settings:
                                sm.settings['voice'] = {}
                            sm.settings['voice']['pause_threshold'] = value
                            sm.save_settings()
                            ui.notify(t('profile_voice_pause_saved', val=value), type='positive')
                            try:
                                from modules.voice import get_voice_manager
                                vm = get_voice_manager()
                                if vm:
                                    vm.reload_config()
                            except:
                                pass
                        except ValueError:
                            ui.notify(t('profile_voice_invalid_value'), type='negative')
                    
                    ui.number(
                        label=t('profile_label_stt_pause_threshold'),
                        value=pause_threshold,
                        min=0.5,
                        max=10.0,
                        step=0.5,
                        on_change=on_pause_threshold_change
                    ).classes('w-full mb-2').props('dense')
                    
                    # Auto-send delay (silence intelligent)
                    def on_auto_send_delay_change(e):
                        try:
                            value = float(e.value)
                            if 'voice' not in sm.settings:
                                sm.settings['voice'] = {}
                            sm.settings['voice']['auto_send_delay'] = value
                            sm.save_settings()
                            if value > 0:
                                ui.notify(t('profile_voice_autosend_enabled', val=value), type='positive')
                            else:
                                ui.notify(t('profile_voice_autosend_disabled'), type='info')
                            try:
                                from modules.voice import get_voice_manager
                                vm = get_voice_manager()
                                if vm:
                                    vm.reload_config()
                            except:
                                pass
                        except ValueError:
                            ui.notify(t('profile_voice_invalid_value'), type='negative')
                    
                    ui.number(
                        label=t('profile_label_stt_auto_send'),
                        value=auto_send_delay,
                        min=0.0,
                        max=60.0,
                        step=1.0,
                        on_change=on_auto_send_delay_change
                    ).classes('w-full mb-2').props('dense')
                    
                    with ui.element('div').classes('text-xs text-blue-300 mt-2'):
                        ui.label(t('profile_voice_tip_timeout'))
                        ui.label(t('profile_voice_tip_duration'))
                        ui.label(t('profile_voice_tip_pause'))
                        ui.label(t('profile_voice_tip_autosend'))

            # === SYNTHÈSE VOCALE ===
            ui.separator().classes('my-4')
            ui.label(t('profile_section_tts')).classes('text-lg font-medium mb-2')

            # TTS activé/désactivé
            tts_enabled = sm.settings.get('tts', {}).get('enabled', True)

            def on_tts_enabled_change(e):
                if 'tts' not in sm.settings:
                    sm.settings['tts'] = {}
                sm.settings['tts']['enabled'] = e.value
                sm.save_settings()

                status = t('profile_tts_state_on') if e.value else t('profile_tts_state_off')
                ui.notify(t('profile_tts_notify_state', state=status), type='positive')

                # Rafraîchir l'affichage pour montrer/cacher les options TTS
                refresh_content()

            with ui.row().classes('items-center gap-2 mb-2'):
                ui.checkbox(
                    t('profile_tts_enable'),
                    value=tts_enabled,
                    on_change=on_tts_enabled_change
                ).classes('mb-0')
                
                # Indicateur d'état visuel
                if tts_enabled:
                    ui.badge(t('profile_tts_status_active'), color='positive').classes('text-xs')
                else:
                    ui.badge(t('profile_tts_status_inactive'), color='negative').classes('text-xs')

            ui.label(t('profile_tts_enable_desc')).classes('text-xs text-muted mb-4')

            # Mode automatique (seulement si TTS activé)
            if tts_enabled:
                auto_speak = sm.settings.get('tts', {}).get('auto_speak', False)

                def on_auto_speak_change(e):
                    if 'tts' not in sm.settings:
                        sm.settings['tts'] = {}
                    sm.settings['tts']['auto_speak'] = e.value
                    sm.save_settings()
                    state = t('profile_tts_auto_read_state_on') if e.value else t('profile_tts_auto_read_state_off')
                    ui.notify(t('profile_tts_auto_read_notify', state=state), type='positive')

                ui.checkbox(
                    t('profile_tts_auto_read'),
                    value=auto_speak,
                    on_change=on_auto_speak_change
                ).classes('mb-2')

                ui.label(t('profile_tts_auto_read_desc')).classes('text-xs text-muted mb-4')
                
                # Mode streaming TTS (lecture pendant le streaming)
                if auto_speak:
                    tts_streaming = sm.settings.get('tts', {}).get('streaming', True)
                    
                    def on_tts_streaming_change(e):
                        if 'tts' not in sm.settings:
                            sm.settings['tts'] = {}
                        sm.settings['tts']['streaming'] = e.value
                        sm.save_settings()
                        state = t('profile_tts_streaming_state_on') if e.value else t('profile_tts_streaming_state_off')
                        ui.notify(t('profile_tts_streaming_notify', state=state), type='positive')
                    
                    ui.checkbox(
                        t('profile_tts_streaming'),
                        value=tts_streaming,
                        on_change=on_tts_streaming_change
                    ).classes('mb-2 ml-4')
                    
                    ui.label(t('profile_tts_streaming_desc')).classes('text-xs text-muted mb-4 ml-4')

            # Si TTS est activé, afficher les paramètres
            if tts_enabled:
                ui.label(t('profile_tts_config_title')).classes('text-md font-medium mb-2')

                # Moteur TTS avec système sans conflit intégré
                # Note: Edge TTS retiré (bloqué par Microsoft depuis 2024)
                engine_options = {
                    'conflict_free': t('profile_tts_engine_conflict_free'),
                    'gtts': t('profile_tts_engine_gtts'),
                    'system': t('profile_tts_engine_system'),
                    'azure': t('profile_tts_engine_azure'),
                    'google': t('profile_tts_engine_google'),
                    'elevenlabs': t('profile_tts_engine_elevenlabs'),
                    'fish_audio': t('profile_tts_engine_fish_audio'),
                    'cartesia': t('profile_tts_engine_cartesia'),
                    'hume_ai': t('profile_tts_engine_hume_ai')
                }
                
                current_engine = sm.settings.get('tts', {}).get('engine', 'conflict_free')
                
                # S'assurer que current_engine est valide
                if current_engine not in engine_options:
                    current_engine = 'conflict_free'
                    # Mettre à jour le settings avec la valeur par défaut
                    if 'tts' not in sm.settings:
                        sm.settings['tts'] = {}
                    sm.settings['tts']['engine'] = current_engine
                    sm.save_settings()

                def on_engine_change(e):
                    if 'tts' not in sm.settings:
                        sm.settings['tts'] = {}
                    sm.settings['tts']['engine'] = e.value
                    sm.save_settings()
                    
                    # Recharger la config TTS dans l'audio manager
                    try:
                        from ogma_ng import _apply_tts_config_from_settings, _audio_manager
                        if _audio_manager:
                            _apply_tts_config_from_settings(_audio_manager)
                    except Exception as err:
                        print(f"[PROFILE-TTS] Erreur reload config: {err}")
                    
                    if e.value == 'conflict_free':
                        ui.notify(t('profile_tts_engine_conflict_free_activated'), type='positive')
                    else:
                        ui.notify(t('profile_tts_engine_changed', engine=e.value), type='positive')

                    # Rafraîchir pour montrer les options du nouveau moteur
                    refresh_content()

                ui.select(
                    label=t('profile_label_tts_engine'),
                    options=engine_options,
                    value=current_engine,
                    on_change=on_engine_change
                ).classes('mb-3')

                # Bouton de test TTS
                async def test_tts():
                    """Test rapide du TTS"""
                    try:
                        from ogma_ng import _ensure_audio_manager
                        audio_mgr = _ensure_audio_manager()
                        
                        if not audio_mgr:
                            ui.notify(t('profile_tts_audio_mgr_unavailable'), type='negative')
                            return
                        
                        test_text = t('profile_tts_test_text')
                        
                        ui.notify(t('profile_tts_test_in_progress'), type='info')
                        
                        # Utiliser speak_async si disponible, sinon speak synchrone
                        if hasattr(audio_mgr, 'speak_async'):
                            success = await audio_mgr.speak_async(test_text)
                        else:
                            success = audio_mgr.speak(test_text)
                        
                        if success:
                            ui.notify(t('profile_tts_test_success'), type='positive')
                        else:
                            ui.notify(t('profile_tts_test_failed'), type='negative')
                            
                    except Exception as e:
                        ui.notify(t('profile_tts_test_error', err=str(e)[:50]), type='negative')

                ui.button(t('profile_btn_test_voice'), on_click=test_tts).classes('mb-3').props('size=sm color=primary')

                # Configuration du moteur sélectionné
                ui.label(t('profile_tts_config_label', name=engine_options.get(current_engine, current_engine))).classes('text-sm mb-2')

                # Import et utilisation du configurateur TTS
                try:
                    from ogma_tts_config import _render_tts_config
                    _render_tts_config(current_engine, sm, refresh_content)
                except ImportError:
                    ui.label(t('profile_tts_config_module_unavailable')).classes('text-red-500 mb-2')

            # === SECTION STT (TRANSCRIPTION AUDIO) ===
            ui.separator().classes('my-4')
            ui.label(t('profile_section_stt')).classes('text-lg font-medium mb-2')
            
            # Options de moteur STT
            stt_options = {
                'google': t('profile_stt_engine_google'),
                'whisper': t('profile_stt_engine_whisper')
            }
            
            # Charger config STT actuelle
            stt_settings = sm.settings.get('stt', {})
            current_stt_engine = 'whisper' if stt_settings.get('use_whisper_api', False) else 'google'
            current_stt_api_key = stt_settings.get('api_key', '')
            
            # Conteneur pour les options dynamiques
            stt_options_container = ui.column().classes('w-full')
            
            def render_stt_options():
                """Affiche les options en fonction du moteur sélectionné"""
                stt_options_container.clear()
                with stt_options_container:
                    current_engine = 'whisper' if sm.settings.get('stt', {}).get('use_whisper_api', False) else 'google'
                    
                    if current_engine == 'whisper':
                        # Afficher le champ API Key pour Whisper
                        saved_key = sm.settings.get('stt', {}).get('api_key', '')
                        masked_key = f"{saved_key[:7]}...{saved_key[-4:]}" if len(saved_key) > 15 else ('***' if saved_key else '')
                        
                        with ui.row().classes('w-full items-center gap-2'):
                            api_input = ui.input(
                                label=t('profile_label_openai_key'),
                                value=saved_key,
                                password=True,
                                password_toggle_button=True
                            ).classes('flex-grow')
                            
                            def save_stt_api_key():
                                if 'stt' not in sm.settings:
                                    sm.settings['stt'] = {}
                                sm.settings['stt']['api_key'] = api_input.value
                                sm.save_settings()
                                
                                # Recharger la config STT dans l'audio manager
                                try:
                                    from audio_manager_wrapper import reload_stt_config
                                    reload_stt_config()
                                except Exception as e:
                                    print(f"[PROFILE-STT] Erreur reload: {e}")
                                
                                ui.notify(t('profile_stt_whisper_key_saved'), type='positive')
                            
                            ui.button('💾', on_click=save_stt_api_key).props('size=sm color=primary').tooltip(t('profile_tooltip_save_key'))
                        
                        if saved_key:
                            ui.label(t('profile_stt_whisper_key_configured', key=masked_key)).classes('text-xs text-green-500')
                        else:
                            ui.label(t('profile_stt_whisper_no_key')).classes('text-xs text-orange-500')
                        
                        ui.label(t('profile_stt_whisper_desc')).classes('text-xs text-muted mt-1')
                    
                    else:
                        # Google Speech - pas de configuration nécessaire
                        ui.label(t('profile_stt_google_free')).classes('text-xs text-green-500')
                        ui.label(t('profile_stt_google_precision')).classes('text-xs text-muted mt-1')
            
            def on_stt_engine_change(e):
                if 'stt' not in sm.settings:
                    sm.settings['stt'] = {}
                sm.settings['stt']['use_whisper_api'] = (e.value == 'whisper')
                sm.save_settings()
                
                # Recharger la config STT dans l'audio manager
                try:
                    from audio_manager_wrapper import reload_stt_config
                    reload_stt_config()
                except Exception as e2:
                    print(f"[PROFILE-STT] Erreur reload: {e2}")
                
                engine_name = stt_options.get(e.value, e.value)
                ui.notify(t('profile_stt_engine_changed', engine=engine_name), type='positive')
                
                # Rafraîchir les options
                render_stt_options()
            
            ui.select(
                label=t('profile_label_stt_engine'),
                options=stt_options,
                value=current_stt_engine,
                on_change=on_stt_engine_change
            ).classes('mb-3')
            
            # Afficher les options initiales
            render_stt_options()
            
            # Bouton de test STT
            async def test_stt():
                """Test rapide du STT"""
                try:
                    ui.notify(t('profile_stt_speak_now'), type='info')
                    
                    from audio_manager_wrapper import get_audio_manager
                    audio_mgr = get_audio_manager()
                    
                    if not audio_mgr:
                        ui.notify(t('profile_tts_audio_mgr_unavailable'), type='negative')
                        return
                    
                    # Initialiser si nécessaire
                    if hasattr(audio_mgr, 'initialize'):
                        await audio_mgr.initialize()
                    
                    # Enregistrer et transcrire
                    if hasattr(audio_mgr, 'record_once'):
                        result = await audio_mgr.record_once(timeout=3.0)
                        if result:
                            ui.notify(t('profile_stt_transcription', text=result), type='positive')
                        else:
                            ui.notify(t('profile_stt_no_transcription'), type='warning')
                    else:
                        ui.notify(t('profile_stt_record_unavailable'), type='negative')
                        
                except Exception as e:
                    ui.notify(t('profile_stt_test_error', err=str(e)[:50]), type='negative')
            
            ui.button(t('profile_btn_test_stt'), on_click=test_stt).classes('mb-3').props('size=sm color=primary')

            # === EXTENSION JOURNAL DE BORD ===
            ui.separator().classes('my-4')
            ui.label(t('profile_section_journal')).classes('text-lg font-medium mb-2')

            # Vérifier si l'extension journal est disponible
            journal_available = False
            journal_enabled = True  # Valeur par défaut
            
            try:
                from extensions.journal_de_bord import is_available, get_journal
                journal_available = is_available()
                
                if journal_available:
                    journal_instance = get_journal()
                    if journal_instance and hasattr(journal_instance, 'config'):
                        journal_enabled = journal_instance.config.is_enabled()
            except Exception as e:
                print(f"[PROFILE-JOURNAL] ERROR Import journal: {e}")
                journal_available = False

            if journal_available:
                def on_journal_enabled_change(e):
                    try:
                        from extensions.journal_de_bord import get_journal
                        journal = get_journal()
                        if journal and hasattr(journal, 'config'):
                            # Basculer l'état de l'extension
                            new_state = journal.config.toggle_enabled()
                            status = t('profile_journal_state_on') if new_state else t('profile_journal_state_off')
                            ui.notify(t('profile_journal_toggled_notify', state=status), type='positive')
                            
                            # Log pour debug
                            print(f"[PROFILE-JOURNAL] UPDATE Extension Journal {'ACTIVÉE' if new_state else 'DÉSACTIVÉE'}")
                        else:
                            ui.notify(t('profile_journal_not_init'), type='negative')
                    except Exception as error:
                        ui.notify(t('profile_journal_toggle_err', err=error), type='negative')
                        print(f"[PROFILE-JOURNAL] ERROR Basculement: {error}")

                ui.checkbox(
                    t('profile_journal_enable'),
                    value=journal_enabled,
                    on_change=on_journal_enabled_change
                ).classes('mb-2')

                ui.label(t('profile_journal_desc')).classes('text-xs text-muted mb-4')
                
                # Informations sur le statut actuel
                status_icon = "✅" if journal_enabled else "❌"
                auto_context = t('profile_journal_status_enabled') if journal_enabled else t('profile_journal_status_disabled')
                ui.label(t('profile_journal_status_label', icon=status_icon, status=auto_context)).classes('text-sm mb-2')
            else:
                ui.label(t('profile_journal_not_available')).classes('text-red-500 mb-2')
                ui.label(t('profile_journal_not_loaded')).classes('text-xs text-muted mb-4')

            # === SECTION HARDWARE (specs machine pour calcul Ollama) ===
            ui.separator().classes('my-4')
            ui.label(t('profile_section_hardware')).classes('text-lg font-medium mb-2')
            ui.label(t('profile_hardware_desc')).classes('text-xs text-muted mb-3')

            hw = sm.settings.get('hardware', {})

            def _save_hw(key, value):
                if 'hardware' not in sm.settings:
                    sm.settings['hardware'] = {}
                sm.settings['hardware'][key] = value
                sm.save_settings()

            # Bouton auto-détection
            hw_status_label = ui.label('').classes('text-xs text-muted mb-2')

            async def _auto_detect_hardware():
                hw_status_label.set_text(t('profile_hardware_detecting'))
                try:
                    detected = {}
                    # RAM via psutil ou WMI
                    try:
                        import psutil
                        mem = psutil.virtual_memory()
                        detected['ram_total_gb'] = round(mem.total / (1024**3), 1)
                    except ImportError:
                        import subprocess
                        r = subprocess.run(
                            ['powershell', '-Command',
                             '(Get-CimInstance Win32_OperatingSystem).TotalVisibleMemorySize'],
                            capture_output=True, text=True, timeout=10
                        )
                        if r.returncode == 0 and r.stdout.strip():
                            detected['ram_total_gb'] = round(int(r.stdout.strip()) / (1024**2), 1)

                    # CPU
                    import os
                    detected['cpu_threads'] = os.cpu_count() or 4

                    # GPU via nvidia-smi
                    try:
                        import subprocess
                        r = subprocess.run(
                            ['nvidia-smi', '--query-gpu=name,memory.total',
                             '--format=csv,noheader,nounits'],
                            capture_output=True, text=True, timeout=10
                        )
                        if r.returncode == 0 and r.stdout.strip():
                            parts = r.stdout.strip().split(',')
                            detected['gpu_name'] = parts[0].strip()
                            detected['gpu_vram_gb'] = round(int(parts[1].strip()) / 1024, 1)
                    except (FileNotFoundError, Exception):
                        # Fallback WMI — filtrer les GPU intégrés (Intel UHD, AMD Vega, etc.)
                        try:
                            import subprocess
                            r = subprocess.run(
                                ['powershell', '-Command',
                                 'Get-CimInstance Win32_VideoController | Select-Object -First 1 -ExpandProperty Name'],
                                capture_output=True, text=True, timeout=10
                            )
                            if r.returncode == 0 and r.stdout.strip():
                                gpu_name = r.stdout.strip()
                                # Ignorer les GPU intégrés et virtuels
                                igpu_keywords = ['Intel', 'UHD', 'Iris', 'Microsoft', 'Meta', 'Virtual', 'Basic', 'Vega']
                                is_igpu = any(kw.lower() in gpu_name.lower() for kw in igpu_keywords)
                                if not is_igpu:
                                    detected['gpu_name'] = gpu_name
                                    r2 = subprocess.run(
                                        ['powershell', '-Command',
                                         'Get-CimInstance Win32_VideoController | Select-Object -First 1 -ExpandProperty AdapterRAM'],
                                        capture_output=True, text=True, timeout=10
                                    )
                                    if r2.returncode == 0 and r2.stdout.strip():
                                        vram_bytes = int(r2.stdout.strip())
                                        if vram_bytes > 0:
                                            detected['gpu_vram_gb'] = round(vram_bytes / (1024**3), 1)
                        except Exception:
                            pass

                    # Appliquer les valeurs détectées
                    if 'hardware' not in sm.settings:
                        sm.settings['hardware'] = {}
                    for k, v in detected.items():
                        sm.settings['hardware'][k] = v
                    sm.save_settings()

                    # Mettre à jour les champs UI
                    if 'ram_total_gb' in detected:
                        hw_ram.value = detected['ram_total_gb']
                    if 'cpu_threads' in detected:
                        hw_cpu.value = detected['cpu_threads']
                    if 'gpu_name' in detected:
                        hw_gpu_name.value = detected['gpu_name']
                    if 'gpu_vram_gb' in detected:
                        hw_vram.value = detected['gpu_vram_gb']

                    hw_status_label.set_text(t('profile_hardware_detected',
                                             ram=detected.get('ram_total_gb', '?'),
                                             cpu=detected.get('cpu_threads', '?'),
                                             gpu=detected.get('gpu_name', 'aucun'),
                                             vram=detected.get('gpu_vram_gb', 0)))
                    ui.notify(t('profile_hardware_detected_short'), type='positive')
                except Exception as e:
                    hw_status_label.set_text(t('profile_hardware_detect_error', err=e))
                    ui.notify(f'Erreur : {e}', type='warning')

            ui.button(t('profile_btn_detect_auto'), icon='search', on_click=_auto_detect_hardware).classes('action-button mb-3').tooltip(t('profile_tooltip_detect_auto'))

            with ui.row().classes('w-full gap-4 mb-2'):
                hw_ram = ui.number(
                    label=t('profile_label_ram'),
                    value=hw.get('ram_total_gb', 0),
                    min=0, max=1024, step=0.1
                ).classes('form-input').style('flex: 1;').tooltip(t('profile_tooltip_ram'))
                hw_ram.on('blur', lambda: _save_hw('ram_total_gb', hw_ram.value))

                hw_cpu = ui.number(
                    label=t('profile_label_cpu_threads'),
                    value=hw.get('cpu_threads', 4),
                    min=1, max=256, step=1
                ).classes('form-input').style('flex: 1;').tooltip(t('profile_tooltip_cpu_threads'))
                hw_cpu.on('blur', lambda: _save_hw('cpu_threads', int(hw_cpu.value or 4)))

            with ui.row().classes('w-full gap-4 mb-2'):
                hw_gpu_name = ui.input(
                    label=t('profile_hardware_gpu_name_label'),
                    value=hw.get('gpu_name', '')
                ).classes('form-input').style('flex: 2;').tooltip(t('profile_hardware_gpu_tooltip'))
                hw_gpu_name.on('blur', lambda: _save_hw('gpu_name', hw_gpu_name.value))

                hw_vram = ui.number(
                    label=t('profile_label_gpu_vram'),
                    value=hw.get('gpu_vram_gb', 0),
                    min=0, max=256, step=0.1
                ).classes('form-input').style('flex: 1;').tooltip(t('profile_tooltip_gpu_vram'))
                hw_vram.on('blur', lambda: _save_hw('gpu_vram_gb', hw_vram.value))

            # Estimation mémoire pour Ollama
            ui.separator().classes('my-2')
            ui.label(t('profile_hardware_estimates_title')).classes('text-sm font-semibold mb-1')

            hw_estimate_container = ui.column().classes('w-full mb-2')

            def _update_estimates():
                hw_estimate_container.clear()
                ram_go = float(hw_ram.value or 0)
                vram_go = float(hw_vram.value or 0)
                # Mémoire disponible estimée (70% de la RAM, OS+apps prennent ~30%)
                ram_usable = ram_go * 0.7
                # Si GPU, le modèle va en VRAM
                mem_for_model = vram_go if vram_go >= 2 else ram_usable
                use_gpu = vram_go >= 2

                with hw_estimate_container:
                    if ram_go == 0:
                        ui.label(t('profile_hardware_enter_ram')).classes('text-xs text-muted')
                        return

                    ui.label(t('profile_hardware_ram_usable', ram_usable=f'{ram_usable:.1f}', ram=f'{ram_go:.1f}')).classes('text-xs text-muted')
                    if use_gpu:
                        ui.label(t('profile_hardware_gpu_detected', vram=f'{vram_go:.0f}')).classes('text-xs text-green-500')
                        ui.label(t('profile_hardware_low_vram_off_gpu')).classes('text-xs text-green-500')
                    else:
                        ui.label(t('profile_hardware_no_gpu')).classes('text-xs text-orange-500')
                        ui.label(t('profile_hardware_low_vram_off_cpu')).classes('text-xs text-orange-500')
                        ui.label(t('profile_hardware_mem_for_models', ram_usable=f'{ram_usable:.1f}')).classes('text-xs text-orange-500')

                    ui.label('').classes('mb-1')
                    ui.label(t('profile_hardware_models_ctx')).classes('text-xs font-semibold')

                    # Lire les modèles Ollama installés
                    try:
                        import requests
                        resp = requests.get('http://localhost:11434/api/tags', timeout=5)
                        if resp.status_code == 200:
                            models = resp.json().get('models', [])
                            for m in models:
                                model_name = m.get('name', '')
                                model_size_bytes = m.get('size', 0)
                                model_size_gb = model_size_bytes / (1024**3)
                                # Récupérer les specs détaillées
                                try:
                                    show_resp = requests.post(
                                        'http://localhost:11434/api/show',
                                        json={'model': model_name}, timeout=5
                                    )
                                    if show_resp.status_code == 200:
                                        show_data = show_resp.json()
                                        details = show_data.get('details', {})
                                        param_size = details.get('parameter_size', '?')
                                        quant = details.get('quantization_level', '?')
                                        model_info = show_data.get('model_info', {})
                                        # Trouver context_length et embedding_length
                                        native_ctx = 0
                                        embed_len = 0
                                        head_count_kv = 1
                                        block_count = 0
                                        for k, v in model_info.items():
                                            if v is None:
                                                continue
                                            if k.endswith('.context_length') and not k.endswith('.audio.context_length'):
                                                native_ctx = int(v)
                                            if k.endswith('.embedding_length') and 'audio' not in k and 'vision' not in k:
                                                embed_len = int(v)
                                            if k.endswith('.attention.head_count_kv'):
                                                head_count_kv = int(v)
                                            if k.endswith('.block_count') and 'audio' not in k and 'vision' not in k:
                                                block_count = int(v)
                                        # Calcul KV cache par token (bytes)
                                        # KV cache ≈ 2 * layers * (kv_heads * head_dim) * 2 bytes (fp16)
                                        head_dim = (embed_len // max(head_count_kv, 1)) if embed_len and head_count_kv else 64
                                        kv_per_token = 2 * block_count * head_count_kv * head_dim * 2  # bytes
                                        # Mémoire libre après chargement modèle
                                        overhead = 0.5  # Go pour overhead Ollama
                                        free_after_model = mem_for_model - model_size_gb - overhead
                                        if free_after_model < 0.1:
                                            recommended_ctx = 0
                                            status = 'NE RENTRE PAS'
                                            color = 'text-red-500'
                                        else:
                                            # Max tokens que le KV cache peut supporter
                                            if kv_per_token > 0:
                                                max_ctx = int((free_after_model * 1024**3) / kv_per_token)
                                            else:
                                                max_ctx = 8192
                                            # Plafonner au contexte natif du modèle
                                            recommended_ctx = min(max_ctx, native_ctx) if native_ctx else min(max_ctx, 131072)
                                            # Arrondir à la puissance de 2 la plus proche
                                            for nice in [1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072]:
                                                if nice >= recommended_ctx:
                                                    recommended_ctx = nice // 2 if nice > recommended_ctx else nice
                                                    break
                                            recommended_ctx = max(recommended_ctx, 1024)
                                            if recommended_ctx >= 8192:
                                                status = 'OK'
                                                color = 'text-green-500'
                                            elif recommended_ctx >= 2048:
                                                status = 'LIMITE'
                                                color = 'text-orange-500'
                                            else:
                                                status = 'INSUFFISANT'
                                                color = 'text-red-500'
                                        recommended_mt = min(4096, max(512, recommended_ctx - 512))
                                        ui.label(
                                            f'  {model_name} ({param_size} {quant}) — '
                                            f'fichier {model_size_gb:.1f} Go — '
                                            f'ctx conseille: {recommended_ctx:,} — '
                                            f'max_tokens: {recommended_mt:,} — {status}'
                                        ).classes(f'text-xs {color}')
                                except Exception:
                                    ui.label(f'  {model_name} — erreur lecture specs').classes('text-xs text-muted')
                        else:
                            ui.label(t('profile_hardware_ollama_unavailable')).classes('text-xs text-muted')
                    except Exception:
                        ui.label(t('profile_hardware_ollama_timeout')).classes('text-xs text-muted')

            # Timer pour calcul initial (après un court délai pour laisser le UI se construire)
            ui.timer(0.5, _update_estimates, once=True)

            # Bouton recalculer
            ui.button(t('profile_btn_recalculate'), icon='calculate', on_click=_update_estimates).classes('action-button mt-2').tooltip(t('profile_tooltip_recalculate'))

    with d, ui.card().classes('popup-content profile-modal q-dark').style('background: var(--bg-secondary); color: var(--text-primary); width: min(800px, 90vw); max-height: 80vh; overflow-y: auto;'):
        ui.label(t('profile_modal_title')).classes('popup-title')

        # Contenu dynamique qui sera rafraîchi
        dynamic_content = ui.column().classes('w-full')

        # Charger le contenu initial
        refresh_content()

        # Bouton fermer
        with ui.row().classes('mt-4 justify-end'):
            ui.button(t('profile_btn_close'), on_click=d.close).classes('action-button')

    return d


def _create_edit_interface(memory_data, save_callback, cancel_callback):
    """Crée l'interface d'édition pour une mémoire"""
    with ui.column().classes('w-full gap-3'):
        # Titre de la mémoire
        title_input = ui.input(
            label='Titre de la mémoire',
            value=memory_data.get('title', ''),
            placeholder='Titre descriptif...'
        ).classes('w-full')

        # Contenu principal
        content_textarea = ui.textarea(
            label='Contenu de la mémoire',
            value=memory_data.get('content', ''),
            placeholder='Contenu détaillé de la mémoire...'
        ).classes('w-full').style('min-height: 120px;')

        # Métadonnées
        with ui.row().classes('w-full gap-3'):
            # Importance
            importance_select = ui.select(
                label='Importance',
                options={
                    1: '⭐ Faible',
                    2: '⭐⭐ Normale',
                    3: '⭐⭐⭐ Élevée',
                    4: '⭐⭐⭐⭐ Critique',
                    5: '⭐⭐⭐⭐⭐ Essentielle'
                },
                value=memory_data.get('importance', 2)
            ).classes('flex-1')

            # Catégorie
            category_input = ui.input(
                label='Catégorie',
                value=memory_data.get('category', ''),
                placeholder='personnel, travail, loisir...'
            ).classes('flex-1')

        # Tags
        tags_input = ui.input(
            label='Tags (séparés par des virgules)',
            value=', '.join(memory_data.get('tags', [])) if memory_data.get('tags') else '',
            placeholder='tag1, tag2, tag3...'
        ).classes('w-full')

        # Boutons d'action
        with ui.row().classes('gap-2 justify-end mt-4'):
            ui.button('Annuler', on_click=cancel_callback).classes('btn-secondary')

            def save_memory():
                # Collecter les données du formulaire
                updated_data = {
                    'title': title_input.value.strip(),
                    'content': content_textarea.value.strip(),
                    'importance': importance_select.value,
                    'category': category_input.value.strip(),
                    'tags': [tag.strip() for tag in tags_input.value.split(',') if tag.strip()]
                }

                # Validation
                if not updated_data['title']:
                    _notify_safe('Le titre est obligatoire', 'negative')
                    return

                if not updated_data['content']:
                    _notify_safe('Le contenu est obligatoire', 'negative')
                    return

                # Appeler le callback de sauvegarde
                save_callback(updated_data)

            ui.button('💾 Sauvegarder', on_click=save_memory).classes('btn-primary')
