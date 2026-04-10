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
                ui.label("❌ Settings Manager non disponible").classes('text-red-500')
                return

            # === SECTION DEBUG ===
            ui.label('🔍 Options de Debug').classes('text-lg font-medium mb-2')

            # Affichage injections Archiviste
            debug_archiviste = sm.settings.get('debug', {}).get('show_archiviste_injection', False)

            def on_debug_archiviste_change(e):
                if 'debug' not in sm.settings:
                    sm.settings['debug'] = {}
                sm.settings['debug']['show_archiviste_injection'] = e.value
                sm.save_settings()
                ui.notify('Paramètre debug sauvegardé', type='positive')

            ui.checkbox(
                'Afficher les injections de contexte de l\'Archiviste dans le chat',
                value=debug_archiviste,
                on_change=on_debug_archiviste_change
            ).classes('mb-2')

            ui.label('Quand activé, vous verrez les notes de contexte injectées par l\'Archiviste en tant que messages système dans la conversation.').classes('text-xs text-muted mb-4')

            # === SECTION VISION AVANCÉE (TRAITEMENT IMAGES) ===
            ui.separator().classes('my-4')
            ui.label('👁️ Vision Avancée (Traitement d\'Images)').classes('text-lg font-medium mb-2')
            ui.label('Ces options s\'appliquent aux images envoyées en pièce jointe. Si les deux sont activées, une image 3 colonnes sera générée.').classes('text-xs text-muted mb-3')
            
            # Option Depth Map pour Uploads
            process_depth = sm.settings.get('perception', {}).get('process_uploads_with_depth', False)
            
            def on_process_depth_change(e):
                if 'perception' not in sm.settings:
                    sm.settings['perception'] = {}
                sm.settings['perception']['process_uploads_with_depth'] = e.value
                sm.save_settings()
                ui.notify('Paramètre Depth Map sauvegardé', type='positive')
                
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
                ui.notify('Paramètre Analyse Contours sauvegardé', type='positive')
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
                ui.label('Méthodes de détection :').classes('text-sm font-medium mb-1')
                
                # Canny avec tooltip
                canny_enabled = sm.settings.get('perception', {}).get('contour_canny', True)
                def on_canny_change(e):
                    if 'perception' not in sm.settings:
                        sm.settings['perception'] = {}
                    sm.settings['perception']['contour_canny'] = e.value
                    sm.save_settings()
                with ui.row().classes('items-center gap-1'):
                    ui.checkbox('Canny (contours nets - recommandé)', value=canny_enabled, on_change=on_canny_change).classes('text-sm')
                    ui.icon('help_outline', size='xs').classes('text-gray-400 cursor-help').tooltip(
                        'Détection de contours par gradient. Détecte les bords nets entre zones de luminosité différente. '
                        'Idéal pour les formes bien définies.'
                    )
                
                # Sobel avec tooltip
                sobel_enabled = sm.settings.get('perception', {}).get('contour_sobel', False)
                def on_sobel_change(e):
                    if 'perception' not in sm.settings:
                        sm.settings['perception'] = {}
                    sm.settings['perception']['contour_sobel'] = e.value
                    sm.save_settings()
                with ui.row().classes('items-center gap-1'):
                    ui.checkbox('Sobel (gradients directionnels)', value=sobel_enabled, on_change=on_sobel_change).classes('text-sm')
                    ui.icon('help_outline', size='xs').classes('text-gray-400 cursor-help').tooltip(
                        'Calcule les gradients horizontaux et verticaux séparément. '
                        'Détecte les transitions de luminosité dans toutes les directions. Plus sensible que Canny.'
                    )
                
                # Laplacian avec tooltip
                laplacian_enabled = sm.settings.get('perception', {}).get('contour_laplacian', False)
                def on_laplacian_change(e):
                    if 'perception' not in sm.settings:
                        sm.settings['perception'] = {}
                    sm.settings['perception']['contour_laplacian'] = e.value
                    sm.save_settings()
                with ui.row().classes('items-center gap-1'):
                    ui.checkbox('Laplacian (contours fins)', value=laplacian_enabled, on_change=on_laplacian_change).classes('text-sm')
                    ui.icon('help_outline', size='xs').classes('text-gray-400 cursor-help').tooltip(
                        'Détecte les contours par dérivée seconde. Produit des lignes très fines. '
                        'Sensible au bruit mais capture les détails subtils.'
                    )
                
                # Adaptive avec tooltip
                adaptive_enabled = sm.settings.get('perception', {}).get('contour_adaptive', False)
                def on_adaptive_change(e):
                    if 'perception' not in sm.settings:
                        sm.settings['perception'] = {}
                    sm.settings['perception']['contour_adaptive'] = e.value
                    sm.save_settings()
                with ui.row().classes('items-center gap-1'):
                    ui.checkbox('Adaptatif (formes contrastées)', value=adaptive_enabled, on_change=on_adaptive_change).classes('text-sm')
                    ui.icon('help_outline', size='xs').classes('text-gray-400 cursor-help').tooltip(
                        'Seuillage adaptatif local. Fonctionne bien avec un éclairage inégal. '
                        'Détecte les formes même dans les zones sombres ou surexposées.'
                    )
                
                ui.label('Paramètres Canny :').classes('text-sm font-medium mt-2 mb-1')
                
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
                            ui.label('Seuil bas').classes('text-xs')
                            ui.icon('help_outline', size='xs').classes('text-gray-400 cursor-help').tooltip(
                                'Seuil minimum pour considérer un pixel comme contour. '
                                'Valeur basse (20-50) = plus de contours détectés, y compris le bruit. '
                                'Valeur haute (80-120) = uniquement les contours les plus marqués.'
                            )
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
                            ui.label('Seuil haut').classes('text-xs')
                            ui.icon('help_outline', size='xs').classes('text-gray-400 cursor-help').tooltip(
                                'Seuil maximum pour confirmer un contour. '
                                'Les pixels entre seuil bas et haut sont gardés seulement s\'ils touchent un contour fort. '
                                'Ratio recommandé : seuil haut = 2-3× seuil bas.'
                            )
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
                            ui.label('Épaisseur').classes('text-xs')
                            ui.icon('help_outline', size='xs').classes('text-gray-400 cursor-help').tooltip(
                                'Épaisseur du trait des contours en pixels. '
                                '1-2 = tracé fin, 3-5 = tracé visible, 6-10 = tracé très épais.'
                            )
                        ui.number(value=thickness, min=1, max=10, step=1, on_change=on_thickness_change).classes('w-20')
                
                # Couleur des tracés
                ui.label('Couleur des tracés :').classes('text-sm font-medium mt-2 mb-1')
                line_color = sm.settings.get('perception', {}).get('contour_line_color', 'red')
                def on_line_color_change(e):
                    if 'perception' not in sm.settings:
                        sm.settings['perception'] = {}
                    sm.settings['perception']['contour_line_color'] = e.value
                    sm.save_settings()
                with ui.row().classes('items-center gap-1'):
                    ui.select(
                        options={'red': '🔴 Rouge', 'white': '⚪ Blanc', 'black': '⚫ Noir'},
                        value=line_color,
                        on_change=on_line_color_change
                    ).classes('w-36')
                    ui.icon('help_outline', size='xs').classes('text-gray-400 cursor-help').tooltip(
                        'Couleur des contours tracés sur l\'image. '
                        'Rouge = visible sur fond clair et sombre. '
                        'Blanc = idéal sur fond noir. '
                        'Noir = idéal sur fond blanc ou images claires.'
                    )
                
                # Mode de rendu avec tooltip
                ui.label('Mode de rendu :').classes('text-sm font-medium mt-2 mb-1')
                render_mode = sm.settings.get('perception', {}).get('contour_render_mode', 'overlay')
                def on_render_mode_change(e):
                    if 'perception' not in sm.settings:
                        sm.settings['perception'] = {}
                    sm.settings['perception']['contour_render_mode'] = e.value
                    sm.save_settings()
                with ui.row().classes('items-center gap-1'):
                    ui.select(
                        options={'overlay': 'Superposé (sur image)', 'black_bg': 'Fond noir', 'white_bg': 'Fond blanc'},
                        value=render_mode,
                        on_change=on_render_mode_change
                    ).classes('w-48')
                    ui.icon('help_outline', size='xs').classes('text-gray-400 cursor-help').tooltip(
                        'Superposé = contours dessinés par-dessus l\'image originale. '
                        'Fond noir = uniquement les contours sur fond noir (style technique/schéma). '
                        'Fond blanc = uniquement les contours sur fond blanc (style dessin).'
                    )
            
            ui.label('Les images traitées sont automatiquement sauvegardées dans le dossier captures/.').classes('text-xs text-muted mb-4')

            # === GESTION DU PROFIL UNIQUE ===
            ui.separator().classes('my-4')
            ui.label('🏗️ Gestion du Profil Unique').classes('text-lg font-medium mb-2')
            
            try:
                from profile_manager import ProfileManager
                profile_mgr = ProfileManager()
                
                # Analyser le profil actuel
                current_analysis = profile_mgr.analyze_current_profile()
                identity = current_analysis['identity']
                memory_stats = current_analysis['memory_stats']
                
                # Affichage du profil actuel
                with ui.card().classes('w-full mb-4 p-4 bg-blue-50 border-l-4 border-blue-400'):
                    ui.label('📊 Profil Actuel').classes('text-md font-medium mb-2')
                    
                    with ui.row().classes('w-full gap-4'):
                        with ui.column().classes('flex-grow'):
                            ui.label(f"👤 Utilisateur : {identity['user_name']}").classes('text-sm')
                            ui.label(f"🤖 IA : {identity['ai_name']}").classes('text-sm')
                            ui.label(f"📝 Description : {identity['ai_description']}").classes('text-sm')
                        
                        with ui.column().classes('flex-grow'):
                            ui.label(f"🧠 Mémoires : {memory_stats['total_memories']} souvenirs").classes('text-sm')
                            ui.label(f"🏛️ Fondateurs : {memory_stats['founder_memories']} préservés").classes('text-sm')
                            ui.label(f"💾 Taille totale : {current_analysis['total_size_mb']} MB").classes('text-sm')
                
                # Boutons de gestion
                with ui.row().classes('w-full gap-2 mb-4'):
                    
                    # Bouton Sauvegarder
                    def open_save_modal():
                        save_dialog = ui.dialog()
                        
                        with save_dialog, ui.card().classes('popup-content q-dark').style('width: min(500px, 90vw);'):
                            ui.label('💾 Sauvegarder le Profil Actuel').classes('popup-title')
                            
                            profile_name_input = ui.input('Nom du profil', 
                                                        value=f"profil_{identity['ai_name'].lower()}_{datetime.now().strftime('%Y%m%d')}")
                            profile_name_input.classes('w-full mb-3')
                            
                            description_input = ui.textarea('Description (optionnel)', 
                                                          value=f"Sauvegarde de {identity['ai_name']} - {datetime.now().strftime('%d/%m/%Y')}")
                            description_input.classes('w-full mb-3')
                            
                            ui.label(f"Cette sauvegarde inclura toutes les données du profil actuel ({current_analysis['total_size_mb']} MB)").classes('text-sm text-muted mb-3')
                            
                            with ui.row().classes('w-full gap-2 justify-end'):
                                ui.button('Annuler', on_click=save_dialog.close).classes('bg-gray-500')
                                
                                def perform_save():
                                    if not profile_name_input.value.strip():
                                        ui.notify('Le nom du profil est obligatoire', type='negative')
                                        return
                                    
                                    success, message, backup_path = profile_mgr.save_current_profile(
                                        profile_name_input.value.strip(),
                                        description_input.value.strip()
                                    )
                                    
                                    if success:
                                        ui.notify('Profil sauvegardé avec succès !', type='positive')
                                        save_dialog.close()
                                        refresh_content()  # Rafraîchir pour afficher la nouvelle sauvegarde
                                    else:
                                        ui.notify(f'Erreur: {message}', type='negative')
                                
                                ui.button('💾 Sauvegarder', on_click=perform_save).classes('bg-blue-600')
                        
                        save_dialog.open()
                    
                    ui.button('💾 Sauvegarder Profil', icon='save', on_click=open_save_modal).classes('bg-blue-600 text-white')
                    
                    # Bouton Supprimer
                    def open_delete_modal():
                        delete_dialog = ui.dialog()
                        
                        with delete_dialog, ui.card().classes('popup-content q-dark').style('width: min(600px, 90vw);'):
                            ui.label('🗑️ Supprimer le Profil Actuel').classes('popup-title text-red-500')
                            
                            ui.label('⚠️ ATTENTION - SUPPRESSION DÉFINITIVE').classes('text-lg font-medium text-red-500 mb-2')
                            
                            ui.label('Cette action va supprimer DÉFINITIVEMENT :').classes('text-sm mb-2')
                            
                            delete_items = [
                                f"🧠 {memory_stats['regular_memories']} souvenirs (fondateurs préservés)",
                                f"💬 Toutes les conversations",
                                f"🎭 Données de personnalité (ego)",
                                f"📸 Images générées + captures webcam",
                                f"📚 Biographies", 
                                f"📖 Journal de bord",
                                f"📅 Organic Planner (agenda)",
                                f"🔑 TOUTES les clés API (sécurité)",
                                f"🔧 Configurations extensions",
                                f"🗂️ Fichiers temporaires et logs"
                            ]
                            
                            for item in delete_items:
                                ui.label(f"  • {item}").classes('text-sm ml-4')
                            
                            ui.separator().classes('my-4')
                            
                            # Option sauvegarde avant suppression
                            save_before_delete = ui.checkbox('💾 Sauvegarder avant suppression (recommandé)', value=True).classes('mb-3')
                            
                            ui.label('Pour confirmer, tapez: DELETE-PROFILE-OGMA').classes('text-sm font-medium mb-2')
                            confirmation_input = ui.input('Code de confirmation').classes('w-full mb-3')
                            
                            # Spinner + statut (masqué par défaut)
                            with ui.row().classes('w-full items-center gap-2 mb-2') as _del_spinner_row:
                                _del_spinner_row.set_visibility(False)
                                ui.spinner(size='sm').classes('text-orange-400')
                                _del_status_label = ui.label('').classes('text-sm text-orange-400')
                            
                            _del_btn_ref = [None]  # référence mutable au bouton
                            
                            with ui.row().classes('w-full gap-2 justify-end'):
                                ui.button('Annuler', on_click=delete_dialog.close).classes('bg-gray-500')
                                
                                async def perform_delete():
                                    if confirmation_input.value != "DELETE-PROFILE-OGMA":
                                        ui.notify('Code de confirmation incorrect', type='negative')
                                        return
                                    
                                    btn = _del_btn_ref[0]
                                    if btn:
                                        btn.disable()
                                    _del_spinner_row.set_visibility(True)
                                    
                                    # Étape 1 : sauvegarde préalable
                                    if save_before_delete.value:
                                        _del_status_label.set_text('💾 Sauvegarde en cours...')
                                        await asyncio.sleep(0.05)
                                        save_name = f"backup_avant_suppression_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                                        save_ok, save_msg, _ = await asyncio.to_thread(
                                            profile_mgr.save_current_profile,
                                            save_name,
                                            "Sauvegarde automatique avant suppression du profil"
                                        )
                                        if not save_ok:
                                            _del_spinner_row.set_visibility(False)
                                            if btn:
                                                btn.enable()
                                            ui.notify(f'Erreur sauvegarde : {save_msg}', type='negative')
                                            return
                                        ui.notify('💾 Sauvegarde créée', type='positive')
                                    
                                    # Étape 2 : suppression du profil
                                    _del_status_label.set_text('🗑️ Suppression du profil en cours...')
                                    await asyncio.sleep(0.05)
                                    success, message = await asyncio.to_thread(
                                        profile_mgr.delete_current_profile, "DELETE-PROFILE-OGMA"
                                    )
                                    
                                    _del_spinner_row.set_visibility(False)
                                    
                                    if success:
                                        delete_dialog.close()
                                        refresh_content()
                                        ui.notify('✅ Profil supprimé avec succès !', type='positive', timeout=5000)
                                        ui.notify('🔄 Redémarrez OGMA pour finaliser la réinitialisation.', type='warning', timeout=0)
                                    else:
                                        if btn:
                                            btn.enable()
                                        ui.notify(f'Erreur : {message}', type='negative')
                                
                                _del_btn_ref[0] = ui.button('🗑️ Supprimer Définitivement', on_click=perform_delete).classes('bg-red-600 text-white')
                        
                        delete_dialog.open()
                    
                    ui.button('🗑️ Supprimer Profil', icon='delete', on_click=open_delete_modal).classes('bg-red-600 text-white')
                
                # Liste des sauvegardes disponibles
                ui.separator().classes('my-4')
                ui.label('📂 Sauvegardes Disponibles').classes('text-lg font-medium mb-2')
                
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
                                            ui.label('📂 Charger une Sauvegarde').classes('popup-title')
                                            
                                            ui.label('⚠️ ATTENTION : Cette action va REMPLACER le profil actuel').classes('text-lg font-medium text-orange-500 mb-3')
                                            
                                            ui.label(f"Profil à charger : {backup['profile_name']}").classes('font-medium mb-2')
                                            ui.label(f"👤 {backup['user_name']} ↔ 🤖 {backup['ai_name']}").classes('text-sm mb-2')
                                            ui.label(f"💾 Taille : {backup['size_mb']} MB").classes('text-sm mb-3')
                                            
                                            if backup['description']:
                                                ui.label(f"📝 {backup['description']}").classes('text-sm text-gray-600 mb-3')
                                            
                                            ui.label('✅ Sera restauré : Mémoires, Clés API, Instructions, Journal, Captures...').classes('text-xs text-green-400 mb-1')
                                            ui.label('💾 Le profil actuel sera automatiquement sauvegardé avant remplacement.').classes('text-xs text-muted mb-4')
                                            
                                            with ui.row().classes('w-full gap-2 justify-end'):
                                                ui.button('Annuler', on_click=load_dialog.close).classes('bg-gray-500')
                                                
                                                def perform_load():
                                                    backup_path_obj = Path(backup_path)
                                                    success, message = profile_mgr.load_profile_backup(backup_path_obj)
                                                    
                                                    if success:
                                                        ui.notify('Profil chargé avec succès !', type='positive')
                                                        load_dialog.close()
                                                        refresh_content()  # Rafraîchir complètement l'interface
                                                    else:
                                                        ui.notify(f'Erreur: {message}', type='negative')
                                                
                                                ui.button('📂 Charger ce Profil', on_click=perform_load).classes('bg-green-600 text-white')
                                        
                                        load_dialog.open()
                                    
                                    return load_backup
                                
                                def create_delete_handler(bk_path, bk_name, bk_user, bk_ai, bk_size):
                                    def delete_backup_click():
                                        del_dialog = ui.dialog()
                                        
                                        with del_dialog, ui.card().classes('popup-content q-dark').style('width: min(480px, 90vw);'):
                                            ui.label('🗑️ Supprimer cette sauvegarde').classes('popup-title')
                                            
                                            ui.label('⚠️ Cette action est IRRÉVERSIBLE').classes('text-lg font-medium text-red-500 mb-3')
                                            
                                            with ui.card().classes('w-full p-3 mb-4 bg-gray-800 border border-red-400'):
                                                ui.label(f"📁 {bk_name}").classes('font-medium text-sm')
                                                ui.label(f"👤 {bk_user} ↔ 🤖 {bk_ai}").classes('text-xs text-gray-400')
                                                ui.label(f"💾 {bk_size} MB").classes('text-xs text-gray-400')
                                            
                                            ui.label('Le dossier complet sera supprimé du disque. Aucune restauration possible.').classes('text-xs text-gray-400 mb-4')
                                            
                                            # Spinner suppression backup (masqué par défaut)
                                            with ui.row().classes('items-center gap-2 mb-2') as _bk_spinner_row:
                                                _bk_spinner_row.set_visibility(False)
                                                ui.spinner(size='sm').classes('text-orange-400')
                                                ui.label('🗑️ Suppression en cours...').classes('text-sm text-orange-400')
                                            
                                            _bk_btn_ref = [None]
                                            
                                            with ui.row().classes('w-full gap-2 justify-end'):
                                                ui.button('Annuler', on_click=del_dialog.close).classes('bg-gray-500')
                                                
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
                                                
                                                _bk_btn_ref[0] = ui.button('🗑️ Supprimer définitivement', on_click=perform_delete_backup).classes('bg-red-600 text-white')
                                        
                                        del_dialog.open()
                                    
                                    return delete_backup_click
                                
                                with ui.row().classes('gap-2'):
                                    ui.button('📂 Charger', icon='folder_open', 
                                             on_click=create_load_handler(backup['path'])).classes('bg-green-600 text-white')
                                    ui.button('🗑️', icon='delete',
                                             on_click=create_delete_handler(
                                                 backup['path'], backup['profile_name'],
                                                 backup['user_name'], backup['ai_name'],
                                                 backup['size_mb']
                                             )).classes('bg-red-700 text-white').tooltip('Supprimer cette sauvegarde')
                else:
                    ui.label('Aucune sauvegarde trouvée').classes('text-gray-500 text-center py-4')
            
            except Exception as e:
                ui.label(f'⚠️ Erreur ProfileManager : {e}').classes('text-red-500')
                print(f"[PROFILE] Erreur: {e}")

            # === SNAPSHOT CONFIG (Clés API + Instructions) ===
            ui.separator().classes('my-4')
            ui.label('🔑 Sauvegarde Config (Clés API + Instructions)').classes('text-lg font-medium mb-2')
            ui.label('Snapshot léger : sauvegarde uniquement les clés API, instructions générales et instructions images (t2i/i2i). Quelques KB seulement.').classes('text-xs text-muted mb-3')

            try:
                from profile_manager import ProfileManager
                config_mgr = ProfileManager()

                # Boutons Sauvegarder config
                def open_save_config_modal():
                    save_cfg_dialog = ui.dialog()

                    with save_cfg_dialog, ui.card().classes('popup-content q-dark').style('width: min(500px, 90vw);'):
                        ui.label('🔑 Sauvegarder Config').classes('popup-title')

                        cfg_name_input = ui.input('Nom de la config',
                                                  value=f"config_{datetime.now().strftime('%Y%m%d')}")
                        cfg_name_input.classes('w-full mb-3')

                        cfg_desc_input = ui.textarea('Description (optionnel)',
                                                     value='').props('rows=2')
                        cfg_desc_input.classes('w-full mb-3')

                        ui.label('Contenu sauvegardé :').classes('text-sm font-medium mb-1')
                        for item in ['🔑 Clés IA providers (Chat, Reasoning, Embedding)',
                                     '🔑 Coffre multi-providers (GROK, OpenAI, Google, Mistral, Kie, WaveSpeed…)',
                                     '🎨 Providers image (text2img, img2img, modèles)',
                                     '🔊 Audio (TTS : Fish Audio, Cartesia, ElevenLabs, engine)',
                                     '🔍 Web (Serper), 🎙️ STT, 📱 Telegram bot token',
                                     '📝 Instructions générales (system, mémorisation, injection, perception, salutations, temporal)',
                                     '🖼️ Instructions images (T2I guide, I2I guide, preprocessor, concision, vision feedback)']:
                            ui.label(f'  • {item}').classes('text-xs text-gray-400')

                        with ui.row().classes('w-full gap-2 justify-end mt-3'):
                            ui.button('Annuler', on_click=save_cfg_dialog.close).classes('bg-gray-500')

                            def perform_save_config():
                                if not cfg_name_input.value.strip():
                                    ui.notify('Le nom est obligatoire', type='negative')
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

                            ui.button('💾 Sauvegarder', on_click=perform_save_config).classes('bg-teal-600 text-white')

                    save_cfg_dialog.open()

                ui.button('💾 Sauvegarder Config', icon='key', on_click=open_save_config_modal).classes('bg-teal-600 text-white mb-3')

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
                                            ui.label('📂 Charger Config').classes('popup-title')
                                            ui.label(f'Profil : {snap_name}').classes('font-medium mb-2')
                                            ui.label('⚠️ Les clés API et instructions actuelles seront remplacées.').classes('text-sm text-orange-400 mb-2')
                                            ui.label('Les contrôleurs IA seront réinitialisés pour utiliser les nouvelles clés.').classes('text-xs text-gray-400 mb-3')

                                            with ui.row().classes('w-full gap-2 justify-end'):
                                                ui.button('Annuler', on_click=load_cfg_dialog.close).classes('bg-gray-500')

                                                def perform_load_config():
                                                    success, message = config_mgr.load_config_snapshot(Path(snap_path))
                                                    if success:
                                                        ui.notify(f'✅ {message}', type='positive', timeout=5000)
                                                        load_cfg_dialog.close()
                                                        refresh_content()
                                                    else:
                                                        ui.notify(f'Erreur: {message}', type='negative')

                                                ui.button('📂 Charger', on_click=perform_load_config).classes('bg-green-600 text-white')

                                        load_cfg_dialog.open()
                                    return load_config_click

                                def create_delete_config_handler(snap_path, snap_name):
                                    def delete_config_click():
                                        del_cfg_dialog = ui.dialog()

                                        with del_cfg_dialog, ui.card().classes('popup-content q-dark').style('width: min(400px, 90vw);'):
                                            ui.label('🗑️ Supprimer Config').classes('popup-title')
                                            ui.label(f'Supprimer : {snap_name}').classes('font-medium mb-2')
                                            ui.label('Cette action est irréversible.').classes('text-xs text-red-400 mb-3')

                                            with ui.row().classes('w-full gap-2 justify-end'):
                                                ui.button('Annuler', on_click=del_cfg_dialog.close).classes('bg-gray-500')

                                                def perform_delete_config():
                                                    success, message = config_mgr.delete_config_snapshot(Path(snap_path))
                                                    if success:
                                                        ui.notify(f'✅ {message}', type='positive')
                                                        del_cfg_dialog.close()
                                                        refresh_content()
                                                    else:
                                                        ui.notify(f'Erreur: {message}', type='negative')

                                                ui.button('🗑️ Supprimer', on_click=perform_delete_config).classes('bg-red-600 text-white')

                                        del_cfg_dialog.open()
                                    return delete_config_click

                                with ui.row().classes('gap-2'):
                                    ui.button('📂 Charger', icon='download',
                                             on_click=create_load_config_handler(snap['path'], snap['name'])).classes('bg-green-600 text-white')
                                    ui.button('🗑️', icon='delete',
                                             on_click=create_delete_config_handler(snap['path'], snap['name'])).classes('bg-red-700 text-white').tooltip('Supprimer ce snapshot')
                else:
                    ui.label('Aucun snapshot de config sauvegardé').classes('text-gray-500 text-center py-2')

            except Exception as e:
                ui.label(f'⚠️ Erreur Config Snapshot : {e}').classes('text-red-500')
                print(f"[CONFIG-SNAPSHOT] Erreur UI: {e}")

            # === IDENTITÉS ===
            ui.separator().classes('my-4')
            ui.label('👤 Identités').classes('text-lg font-medium mb-2')
            
            # Récupération des identités actuelles
            try:
                from identity_manager import get_identity_manager
                identity_manager = get_identity_manager()
                current_identity = identity_manager.get_current_identity()
                
                # Nom utilisateur
                with ui.row().classes('w-full items-center gap-2 mb-2'):
                    user_input = ui.input('Nom utilisateur', value=current_identity['user_name']).classes('flex-grow')
                    
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
                                        # Pas d'instruction sauvegardée : rafraichir le template affiché
                                        new_template = (
                                            f"Tu dialogues avec {new_name}.\n\nDIRECTIVE :\n"
                                            f"- Utilise UNIQUEMENT les souvenirs et connaissances concernant {new_name}\n"
                                            f"- Si tu n'as AUCUN souvenir de {new_name}, c'est une premiere rencontre\n"
                                            f"- IGNORE tout souvenir concernant d'autres personnes (meme s'ils apparaissent ci-dessous)\n"
                                            f"- Adapte ton comportement selon ta relation reelle avec {new_name}"
                                        )
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
                                
                                ui.notify(f'Nom utilisateur mis à jour : {new_name}', type='positive')
                            else:
                                ui.notify('Erreur lors de la mise à jour', type='negative')
                        else:
                            ui.notify('Le nom utilisateur ne peut pas être vide', type='negative')
                    
                    ui.button('Valider', on_click=update_user_name).props('color=primary')
                
                # Nom IA
                with ui.row().classes('w-full items-center gap-2 mb-4'):
                    ai_input = ui.input('Nom IA', value=current_identity['ai_name']).classes('flex-grow')
                    
                    def update_ai_name():
                        if ai_input.value.strip():
                            # Mettre à jour le profil actuel
                            current_profile_id = identity_manager.get_current_profile_id()
                            if current_profile_id and current_profile_id in identity_manager._data['profiles']:
                                identity_manager._data['profiles'][current_profile_id]['ai_name'] = ai_input.value.strip()
                                identity_manager.save_identities()
                                ui.notify(f'Nom IA mis à jour : {ai_input.value.strip()}', type='positive')
                            else:
                                ui.notify('Erreur lors de la mise à jour', type='negative')
                        else:
                            ui.notify('Le nom IA ne peut pas être vide', type='negative')
                    
                    ui.button('Valider', on_click=update_ai_name).props('color=primary')
                
                # Instruction d'identité personnalisée
                ui.label('📋 Instruction d\'identité').classes('text-sm font-medium mb-1 mt-4')
                ui.label('Cette instruction sera injectée à chaque conversation pour clarifier qui vous êtes.').classes('text-xs text-gray-400 mb-2')
                
                # Récupérer l'instruction actuelle ou utiliser le template par défaut
                current_profile_id = identity_manager.get_current_profile_id()
                current_instruction = ""
                if current_profile_id and current_profile_id in identity_manager._data['profiles']:
                    current_instruction = identity_manager._data['profiles'][current_profile_id].get('identity_instruction', '')
                    # Réparation auto : si l'instruction contient un ancien prénom différent de user_name
                    if current_instruction:
                        stored_user_name = identity_manager._data['profiles'][current_profile_id].get('user_name', '')
                        prefix = 'Tu dialogues avec '
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
                
                # Si vide, utiliser le template par défaut
                if not current_instruction:
                    current_instruction = f"""Tu dialogues avec {current_identity['user_name']}.

DIRECTIVE :
- Utilise UNIQUEMENT les souvenirs et connaissances concernant {current_identity['user_name']}
- Si tu n'as AUCUN souvenir de {current_identity['user_name']}, c'est une première rencontre
- IGNORE tout souvenir concernant d'autres personnes (même s'ils apparaissent ci-dessous)
- Adapte ton comportement selon ta relation réelle avec {current_identity['user_name']}"""
                
                instruction_input = ui.textarea('Instruction', value=current_instruction).classes('w-full').props('rows=6 outlined')
                
                def update_identity_instruction():
                    if instruction_input.value.strip():
                        new_instruction = instruction_input.value.strip()
                        
                        # Mettre à jour le profil actuel
                        current_profile_id = identity_manager.get_current_profile_id()
                        if current_profile_id and current_profile_id in identity_manager._data['profiles']:
                            identity_manager._data['profiles'][current_profile_id]['identity_instruction'] = new_instruction
                            identity_manager.save_identities()
                            ui.notify('✅ Instruction d\'identité mise à jour', type='positive')
                            print(f"[IDENTITY] ✅ Instruction personnalisée sauvegardée ({len(new_instruction)} chars)")
                        else:
                            ui.notify('Erreur lors de la mise à jour', type='negative')
                    else:
                        ui.notify('L\'instruction ne peut pas être vide', type='negative')
                
                with ui.row().classes('w-full justify-end gap-2 mt-2'):
                    ui.button('Réinitialiser au défaut', on_click=lambda: instruction_input.set_value(f"""Tu dialogues avec {current_identity['user_name']}.

DIRECTIVE :
- Utilise UNIQUEMENT les souvenirs et connaissances concernant {current_identity['user_name']}
- Si tu n'as AUCUN souvenir de {current_identity['user_name']}, c'est une première rencontre
- IGNORE tout souvenir concernant d'autres personnes (même s'ils apparaissent ci-dessous)
- Adapte ton comportement selon ta relation réelle avec {current_identity['user_name']}""")).props('flat color=secondary')
                    ui.button('Valider', on_click=update_identity_instruction).props('color=primary')
                
            except Exception as e:
                ui.label(f"❌ Erreur : {e}").classes('text-red-500')

            # === MODE CONVERSATION VOCALE (Module Voice - Janvier 2026) ===
            ui.separator().classes('my-4')
            ui.label('🎙️ Mode Conversation Vocale').classes('text-lg font-medium mb-2')
            
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
                    ui.notify('🎙️ Mode vocal activé ! Cliquez dans la zone de message pour commencer.', type='positive')
                else:
                    ui.notify('Mode vocal désactivé', type='info')
                
                refresh_content()
            
            with ui.card().classes('w-full p-3 mb-3 bg-gradient-to-r from-purple-900/20 to-blue-900/20 border border-purple-500/30'):
                ui.label('🎤 Conversation Vocale Intelligente').classes('text-md font-medium mb-2')
                
                with ui.row().classes('items-center gap-2 mb-2'):
                    ui.checkbox(
                        'Activer le mode conversation vocale',
                        value=voice_enabled,
                        on_change=on_voice_mode_change
                    ).classes('mb-0')
                    
                    if voice_enabled:
                        ui.badge('🎙️ ACTIF', color='positive').classes('text-xs animate-pulse')
                    else:
                        ui.badge('⏸️ INACTIF', color='secondary').classes('text-xs')
                
                ui.label('Principe : Cliquez dans la zone de message pour activer l\'écoute. Dites le mot d\'activation pour commencer à dicter, puis le mot d\'envoi pour envoyer.').classes('text-xs text-muted mb-2')
                
                if voice_enabled:
                    # Mode conversation continue
                    def on_continuous_mode_change(e):
                        if 'voice' not in sm.settings:
                            sm.settings['voice'] = {}
                        sm.settings['voice']['continuous_mode'] = e.value
                        sm.save_settings()
                        
                        if e.value:
                            ui.notify('🔄 Mode conversation continue activé ! Plus besoin du trigger d\'activation.', type='positive')
                        else:
                            ui.notify('Mode conversation continue désactivé', type='info')
                        
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
                            '🔄 Mode Conversation Continue',
                            value=continuous_mode,
                            on_change=on_continuous_mode_change
                        ).classes('mb-0')
                        
                        if continuous_mode:
                            ui.badge('🔥 CONTINU', color='warning').classes('text-xs animate-pulse')
                    
                    if continuous_mode:
                        with ui.element('div').classes('text-xs text-orange-300 mb-2 p-2 bg-orange-900/20 rounded'):
                            ui.label("⚡ Mode continu : Dès que l'IA principale finit de parler, le micro s'active automatiquement.")
                            ui.label("Pas besoin du trigger d'activation - seul le trigger d'envoi est nécessaire.")
                    
                    # Configuration du mot d'activation
                    def on_trigger_activation_change(e):
                        if 'voice' not in sm.settings:
                            sm.settings['voice'] = {}
                        sm.settings['voice']['trigger_activation'] = e.value.lower().strip()
                        sm.save_settings()
                        ui.notify(f'Mot d\'activation: "{e.value}"', type='positive')
                        # Recharger config dans le module voice si disponible
                        try:
                            from modules.voice import get_voice_manager
                            vm = get_voice_manager()
                            if vm:
                                vm.reload_config()
                        except:
                            pass
                    
                    ui.input(
                        label='🔵 Mot d\'activation (pour commencer à parler / interrompre)',
                        value=trigger_activation,
                        on_change=on_trigger_activation_change
                    ).classes('w-full mb-2').props('dense')
                    
                    # Configuration du mot d'envoi
                    def on_trigger_send_change(e):
                        if 'voice' not in sm.settings:
                            sm.settings['voice'] = {}
                        sm.settings['voice']['trigger_send'] = e.value.lower().strip()
                        sm.save_settings()
                        ui.notify(f'Mot d\'envoi: "{e.value}"', type='positive')
                        # Recharger config dans le module voice si disponible
                        try:
                            from modules.voice import get_voice_manager
                            vm = get_voice_manager()
                            if vm:
                                vm.reload_config()
                        except:
                            pass
                    
                    ui.input(
                        label='🟢 Mot d\'envoi (pour envoyer le message)',
                        value=trigger_send,
                        on_change=on_trigger_send_change
                    ).classes('w-full mb-2').props('dense')
                    
                    with ui.element('div').classes('text-xs text-green-400 space-y-1'):
                        ui.label(f"💡 Dites \"{trigger_activation}\" pour commencer à dicter ou interrompre l'IA principale.")
                        ui.label(f"💡 Dites \"{trigger_send}\" pour envoyer votre message.")
                    
                    # Paramètres audio avancés
                    ui.separator().classes('my-3')
                    ui.label('🎚️ Paramètres Audio Avancés').classes('text-sm font-medium mb-2')
                    
                    # Listening timeout
                    def on_listening_timeout_change(e):
                        try:
                            value = float(e.value)
                            if 'voice' not in sm.settings:
                                sm.settings['voice'] = {}
                            sm.settings['voice']['listening_timeout'] = value
                            sm.save_settings()
                            ui.notify(f'Timeout d\'écoute: {value}s', type='positive')
                            try:
                                from modules.voice import get_voice_manager
                                vm = get_voice_manager()
                                if vm:
                                    vm.reload_config()
                            except:
                                pass
                        except ValueError:
                            ui.notify('Valeur invalide', type='negative')
                    
                    ui.number(
                        label='⏱️ Timeout initial (sec) - Délai avant de commencer à parler',
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
                            ui.notify(f'Durée max par segment: {value}s', type='positive')
                            try:
                                from modules.voice import get_voice_manager
                                vm = get_voice_manager()
                                if vm:
                                    vm.reload_config()
                            except:
                                pass
                        except ValueError:
                            ui.notify('Valeur invalide', type='negative')
                    
                    ui.number(
                        label='📏 Durée max par segment (sec) - Durée maximale d\'enregistrement continu',
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
                            ui.notify(f'Seuil de pause: {value}s', type='positive')
                            try:
                                from modules.voice import get_voice_manager
                                vm = get_voice_manager()
                                if vm:
                                    vm.reload_config()
                            except:
                                pass
                        except ValueError:
                            ui.notify('Valeur invalide', type='negative')
                    
                    ui.number(
                        label='⏸️ Seuil de pause (sec) - Durée de silence avant coupure automatique',
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
                                ui.notify(f'Envoi automatique après {value}s de silence', type='positive')
                            else:
                                ui.notify('Envoi automatique désactivé', type='info')
                            try:
                                from modules.voice import get_voice_manager
                                vm = get_voice_manager()
                                if vm:
                                    vm.reload_config()
                            except:
                                pass
                        except ValueError:
                            ui.notify('Valeur invalide', type='negative')
                    
                    ui.number(
                        label='🤫 Envoi automatique après silence (sec) - 0 pour désactiver',
                        value=auto_send_delay,
                        min=0.0,
                        max=60.0,
                        step=1.0,
                        on_change=on_auto_send_delay_change
                    ).classes('w-full mb-2').props('dense')
                    
                    with ui.element('div').classes('text-xs text-blue-300 mt-2'):
                        ui.label('💡 Timeout = délai max avant de commencer à parler')
                        ui.label('💡 Durée max = durée totale d\'enregistrement par segment')
                        ui.label('💡 Seuil pause = silence nécessaire pour couper (ne pas couper au milieu d\'une phrase)')
                        ui.label('💡 Envoi auto = silence total avant d\'envoyer le message (5s recommandé, 30s+ pour désactiver)')

            # === SYNTHÈSE VOCALE ===
            ui.separator().classes('my-4')
            ui.label('🔊 Synthèse Vocale (TTS)').classes('text-lg font-medium mb-2')

            # TTS activé/désactivé
            tts_enabled = sm.settings.get('tts', {}).get('enabled', True)

            def on_tts_enabled_change(e):
                if 'tts' not in sm.settings:
                    sm.settings['tts'] = {}
                sm.settings['tts']['enabled'] = e.value
                sm.save_settings()

                status = "activée" if e.value else "désactivée"
                ui.notify(f'Synthèse vocale {status}', type='positive')

                # Rafraîchir l'affichage pour montrer/cacher les options TTS
                refresh_content()

            with ui.row().classes('items-center gap-2 mb-2'):
                ui.checkbox(
                    '🔊 Activer la synthèse vocale',
                    value=tts_enabled,
                    on_change=on_tts_enabled_change
                ).classes('mb-0')
                
                # Indicateur d'état visuel
                if tts_enabled:
                    ui.badge('✅ ACTIF', color='positive').classes('text-xs')
                else:
                    ui.badge('❌ INACTIF', color='negative').classes('text-xs')

            ui.label('Active le système de synthèse vocale. Décoché = pas de TTS du tout.').classes('text-xs text-muted mb-4')

            # Mode automatique (seulement si TTS activé)
            if tts_enabled:
                auto_speak = sm.settings.get('tts', {}).get('auto_speak', False)

                def on_auto_speak_change(e):
                    if 'tts' not in sm.settings:
                        sm.settings['tts'] = {}
                    sm.settings['tts']['auto_speak'] = e.value
                    sm.save_settings()
                    ui.notify(f'Lecture automatique {"activée" if e.value else "désactivée"}', type='positive')

                ui.checkbox(
                    '▶️ Lecture automatique des réponses IA',
                    value=auto_speak,
                    on_change=on_auto_speak_change
                ).classes('mb-2')

                ui.label(f'Coché = lecture automatique | Décoché = bouton ▶️ manuel sous chaque réponse.').classes('text-xs text-muted mb-4')
                
                # Mode streaming TTS (lecture pendant le streaming)
                if auto_speak:
                    tts_streaming = sm.settings.get('tts', {}).get('streaming', True)
                    
                    def on_tts_streaming_change(e):
                        if 'tts' not in sm.settings:
                            sm.settings['tts'] = {}
                        sm.settings['tts']['streaming'] = e.value
                        sm.save_settings()
                        ui.notify(f'TTS streaming {"activé" if e.value else "désactivé"}', type='positive')
                    
                    ui.checkbox(
                        '🔊 Mode streaming (lecture phrase par phrase)',
                        value=tts_streaming,
                        on_change=on_tts_streaming_change
                    ).classes('mb-2 ml-4')
                    
                    ui.label('Coché = lecture progressive pendant le streaming | Décoché = lecture après réponse complète.').classes('text-xs text-muted mb-4 ml-4')

            # Si TTS est activé, afficher les paramètres
            if tts_enabled:
                ui.label('⚙️ Configuration TTS').classes('text-md font-medium mb-2')

                # Moteur TTS avec système sans conflit intégré
                # Note: Edge TTS retiré (bloqué par Microsoft depuis 2024)
                engine_options = {
                    'conflict_free': '🎵 TTS Sans Conflit (recommandé)',
                    'gtts': '🌐 Google TTS Offline (Gratuit)',
                    'system': '🖥️ Système (pyttsx3)',
                    'azure': '☁️ Azure AI Speech (API)',
                    'google': '☁️ Google Cloud TTS (API)',
                    'elevenlabs': '🎯 ElevenLabs (API Premium)',
                    'fish_audio': '🐟 Fish Audio (API)',
                    'cartesia': '🎭 Cartesia AI (API)',
                    'hume_ai': '🧠 Hume AI / Octave (API)'
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
                        ui.notify('🎵 TTS sans conflit activé (optimal)', type='positive')
                    else:
                        ui.notify(f'Moteur TTS: {e.value}', type='positive')

                    # Rafraîchir pour montrer les options du nouveau moteur
                    refresh_content()

                ui.select(
                    label='Moteur de synthèse vocale',
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
                            ui.notify('❌ Audio manager non disponible', type='negative')
                            return
                        
                        test_text = "Bonjour ! Test de la synthèse vocale. Ça fonctionne parfaitement !"
                        
                        ui.notify('🔊 Test TTS en cours...', type='info')
                        
                        # Utiliser speak_async si disponible, sinon speak synchrone
                        if hasattr(audio_mgr, 'speak_async'):
                            success = await audio_mgr.speak_async(test_text)
                        else:
                            success = audio_mgr.speak(test_text)
                        
                        if success:
                            ui.notify('✅ Test TTS réussi !', type='positive')
                        else:
                            ui.notify('❌ Échec test TTS', type='negative')
                            
                    except Exception as e:
                        ui.notify(f'❌ Erreur test TTS: {str(e)[:50]}', type='negative')

                ui.button('🎤 Tester la voix', on_click=test_tts).classes('mb-3').props('size=sm color=primary')

                # Configuration du moteur sélectionné
                ui.label(f'Configuration: {engine_options.get(current_engine, current_engine)}').classes('text-sm mb-2')

                # Import et utilisation du configurateur TTS
                try:
                    from ogma_tts_config import _render_tts_config
                    _render_tts_config(current_engine, sm, refresh_content)
                except ImportError:
                    ui.label("❌ Module de configuration TTS non disponible").classes('text-red-500 mb-2')

            # === SECTION STT (TRANSCRIPTION AUDIO) ===
            ui.separator().classes('my-4')
            ui.label('🎙️ Transcription Audio (Speech-to-Text)').classes('text-lg font-medium mb-2')
            
            # Options de moteur STT
            stt_options = {
                'google': '🌐 Google Speech Recognition (Gratuit)',
                'whisper': '🤖 OpenAI Whisper (API - Haute précision)'
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
                                label='Clé API OpenAI',
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
                                
                                ui.notify('✅ Clé API Whisper sauvegardée', type='positive')
                            
                            ui.button('💾', on_click=save_stt_api_key).props('size=sm color=primary').tooltip('Sauvegarder la clé')
                        
                        if saved_key:
                            ui.label(f'✅ Clé configurée: {masked_key}').classes('text-xs text-green-500')
                        else:
                            ui.label('⚠️ Aucune clé API configurée - ajoutez votre clé OpenAI').classes('text-xs text-orange-500')
                        
                        ui.label('OpenAI Whisper offre une transcription de haute précision. Nécessite une clé API OpenAI.').classes('text-xs text-muted mt-1')
                    
                    else:
                        # Google Speech - pas de configuration nécessaire
                        ui.label('✅ Google Speech Recognition est gratuit et ne nécessite aucune configuration.').classes('text-xs text-green-500')
                        ui.label('Précision correcte pour le français. Requiert une connexion internet.').classes('text-xs text-muted mt-1')
            
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
                ui.notify(f'Moteur STT: {engine_name}', type='positive')
                
                # Rafraîchir les options
                render_stt_options()
            
            ui.select(
                label='Moteur de transcription',
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
                    ui.notify('🎙️ Parlez maintenant pendant 3 secondes...', type='info')
                    
                    from audio_manager_wrapper import get_audio_manager
                    audio_mgr = get_audio_manager()
                    
                    if not audio_mgr:
                        ui.notify('❌ Audio manager non disponible', type='negative')
                        return
                    
                    # Initialiser si nécessaire
                    if hasattr(audio_mgr, 'initialize'):
                        await audio_mgr.initialize()
                    
                    # Enregistrer et transcrire
                    if hasattr(audio_mgr, 'record_once'):
                        result = await audio_mgr.record_once(timeout=3.0)
                        if result:
                            ui.notify(f'✅ Transcription: "{result}"', type='positive')
                        else:
                            ui.notify('❌ Aucune transcription obtenue', type='warning')
                    else:
                        ui.notify('❌ Fonction record_once non disponible', type='negative')
                        
                except Exception as e:
                    ui.notify(f'❌ Erreur test STT: {str(e)[:50]}', type='negative')
            
            ui.button('🎤 Tester la transcription', on_click=test_stt).classes('mb-3').props('size=sm color=primary')

            # === EXTENSION JOURNAL DE BORD ===
            ui.separator().classes('my-4')
            ui.label('📔 Extension Journal de Bord').classes('text-lg font-medium mb-2')

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
                            status = "activée" if new_state else "désactivée"
                            ui.notify(f'Extension Journal de Bord {status}', type='positive')
                            
                            # Log pour debug
                            print(f"[PROFILE-JOURNAL] UPDATE Extension Journal {'ACTIVÉE' if new_state else 'DÉSACTIVÉE'}")
                        else:
                            ui.notify('Erreur: Journal non initialisé', type='negative')
                    except Exception as error:
                        ui.notify(f'Erreur lors du basculement: {error}', type='negative')
                        print(f"[PROFILE-JOURNAL] ERROR Basculement: {error}")

                ui.checkbox(
                    'Activer l\'extension Journal de Bord',
                    value=journal_enabled,
                    on_change=on_journal_enabled_change
                ).classes('mb-2')

                ui.label('Quand activé, le journal injecte automatiquement le contexte de la journée au début des nouvelles conversations (max 3 entrées).').classes('text-xs text-muted mb-4')
                
                # Informations sur le statut actuel
                status_icon = "✅" if journal_enabled else "❌"
                auto_context = "✅ Injection automatique de contexte" if journal_enabled else "❌ Pas d'injection de contexte"
                ui.label(f'{status_icon} Statut: {auto_context}').classes('text-sm mb-2')
            else:
                ui.label('❌ Extension Journal de Bord non disponible').classes('text-red-500 mb-2')
                ui.label('L\'extension n\'est pas chargée ou a rencontré une erreur au démarrage.').classes('text-xs text-muted mb-4')

            # === SECTION HARDWARE (specs machine pour calcul Ollama) ===
            ui.separator().classes('my-4')
            ui.label('🖥️ Caractéristiques Hardware').classes('text-lg font-medium mb-2')
            ui.label('Ces valeurs sont utilisées pour calculer les paramètres Ollama optimaux (context_length, max_tokens, low_vram). Modifiez-les si l\'auto-détection est incorrecte.').classes('text-xs text-muted mb-3')

            hw = sm.settings.get('hardware', {})

            def _save_hw(key, value):
                if 'hardware' not in sm.settings:
                    sm.settings['hardware'] = {}
                sm.settings['hardware'][key] = value
                sm.save_settings()

            # Bouton auto-détection
            hw_status_label = ui.label('').classes('text-xs text-muted mb-2')

            async def _auto_detect_hardware():
                hw_status_label.set_text('Détection en cours...')
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

                    hw_status_label.set_text(f'Detecte : RAM {detected.get("ram_total_gb", "?")} Go, '
                                             f'CPU {detected.get("cpu_threads", "?")} threads, '
                                             f'GPU {detected.get("gpu_name", "aucun")} '
                                             f'({detected.get("gpu_vram_gb", 0)} Go VRAM)')
                    ui.notify('Hardware detecte', type='positive')
                except Exception as e:
                    hw_status_label.set_text(f'Erreur detection : {e}')
                    ui.notify(f'Erreur : {e}', type='warning')

            ui.button('Detecter automatiquement', icon='search', on_click=_auto_detect_hardware).classes('action-button mb-3').tooltip('Detecte automatiquement la RAM, le nombre de coeurs CPU et le GPU de votre machine.\nLes champs ci-dessous seront remplis. Vous pourrez les corriger manuellement si besoin.')

            with ui.row().classes('w-full gap-4 mb-2'):
                hw_ram = ui.number(
                    label='RAM totale (Go)',
                    value=hw.get('ram_total_gb', 0),
                    min=0, max=1024, step=0.1
                ).classes('form-input').style('flex: 1;').tooltip('Memoire vive totale de votre PC en gigaoctets.\nExemple : 8 Go, 16 Go, 32 Go.\nPlus vous avez de RAM, plus gros modeles vous pouvez utiliser.\nSans GPU, c\'est la RAM qui charge le modele.')
                hw_ram.on('blur', lambda: _save_hw('ram_total_gb', hw_ram.value))

                hw_cpu = ui.number(
                    label='Threads CPU',
                    value=hw.get('cpu_threads', 4),
                    min=1, max=256, step=1
                ).classes('form-input').style('flex: 1;').tooltip('Nombre de fils d\'execution de votre processeur.\nExemple : 8 threads pour un i5, 16 pour un i7.\nUtilise pour le parametre num_thread d\'Ollama.\nPlus de threads = generation plus rapide sur CPU.')
                hw_cpu.on('blur', lambda: _save_hw('cpu_threads', int(hw_cpu.value or 4)))

            with ui.row().classes('w-full gap-4 mb-2'):
                hw_gpu_name = ui.input(
                    label='GPU (nom)',
                    value=hw.get('gpu_name', '')
                ).classes('form-input').style('flex: 2;').tooltip('Nom de votre carte graphique.\nExemple : NVIDIA RTX 4060, RTX 3080, etc.\nSi vous n\'avez qu\'un GPU integre (Intel UHD, AMD Vega),\nlaissez vide — le modele sera charge en RAM CPU.')
                hw_gpu_name.on('blur', lambda: _save_hw('gpu_name', hw_gpu_name.value))

                hw_vram = ui.number(
                    label='VRAM GPU (Go)',
                    value=hw.get('gpu_vram_gb', 0),
                    min=0, max=256, step=0.1
                ).classes('form-input').style('flex: 1;').tooltip('Memoire dediee de votre carte graphique en Go.\nExemple : 8 Go pour une RTX 4060, 16 Go pour une RTX 4080.\nSi >= 2 Go, les modeles Ollama seront charges en VRAM (rapide).\nSi 0, tout passe en RAM CPU (plus lent).')
                hw_vram.on('blur', lambda: _save_hw('gpu_vram_gb', hw_vram.value))

            # Estimation mémoire pour Ollama
            ui.separator().classes('my-2')
            ui.label('Estimations Ollama').classes('text-sm font-semibold mb-1')

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
                        ui.label('Renseignez votre RAM pour voir les estimations.').classes('text-xs text-muted')
                        return

                    ui.label(f'RAM utilisable estimee : ~{ram_usable:.1f} Go (70% de {ram_go:.1f})').classes('text-xs text-muted')
                    if use_gpu:
                        ui.label(f'GPU detecte ({vram_go:.0f} Go VRAM) — modeles charges en VRAM (rapide)').classes('text-xs text-green-500')
                        ui.label(f'low_vram conseille : OFF (tout sur le GPU)').classes('text-xs text-green-500')
                    else:
                        ui.label('Pas de GPU dedie — modeles charges en RAM CPU (plus lent)').classes('text-xs text-orange-500')
                        ui.label('low_vram conseille : OFF (sans GPU, ce parametre n\'a pas d\'effet)').classes('text-xs text-orange-500')
                        ui.label(f'Memoire dispo pour les modeles : ~{ram_usable:.1f} Go').classes('text-xs text-orange-500')

                    ui.label('').classes('mb-1')
                    ui.label('Modeles Ollama — context_length conseille :').classes('text-xs font-semibold')

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
                            ui.label('Ollama non disponible — demarrez Ollama pour voir les estimations.').classes('text-xs text-muted')
                    except Exception:
                        ui.label('Ollama non joignable (timeout) — demarrez Ollama pour voir les estimations.').classes('text-xs text-muted')

            # Timer pour calcul initial (après un court délai pour laisser le UI se construire)
            ui.timer(0.5, _update_estimates, once=True)

            # Bouton recalculer
            ui.button('Recalculer estimations', icon='calculate', on_click=_update_estimates).classes('action-button mt-2').tooltip('Recalcule les valeurs conseillee pour chaque modele Ollama installe,\nen tenant compte de vos specs hardware ci-dessus.\nModifiez la RAM ou la VRAM puis cliquez ici pour voir l\'impact.')

    with d, ui.card().classes('popup-content profile-modal q-dark').style('background: var(--bg-secondary); color: var(--text-primary); width: min(800px, 90vw); max-height: 80vh; overflow-y: auto;'):
        ui.label('👤 Profil Utilisateur').classes('popup-title')

        # Contenu dynamique qui sera rafraîchi
        dynamic_content = ui.column().classes('w-full')

        # Charger le contenu initial
        refresh_content()

        # Bouton fermer
        with ui.row().classes('mt-4 justify-end'):
            ui.button('Fermer', on_click=d.close).classes('action-button')

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
