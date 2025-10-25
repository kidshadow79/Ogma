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
                                f"📸 Images générées",
                                f"📚 Biographies", 
                                f"📖 Journal de bord",
                                f"🗂️ Fichiers temporaires"
                            ]
                            
                            for item in delete_items:
                                ui.label(f"  • {item}").classes('text-sm ml-4')
                            
                            ui.separator().classes('my-4')
                            
                            # Option sauvegarde avant suppression
                            save_before_delete = ui.checkbox('💾 Sauvegarder avant suppression (recommandé)', value=True).classes('mb-3')
                            
                            ui.label('Pour confirmer, tapez: DELETE-PROFILE-OGMA').classes('text-sm font-medium mb-2')
                            confirmation_input = ui.input('Code de confirmation').classes('w-full mb-3')
                            
                            with ui.row().classes('w-full gap-2 justify-end'):
                                ui.button('Annuler', on_click=delete_dialog.close).classes('bg-gray-500')
                                
                                def perform_delete():
                                    if confirmation_input.value != "DELETE-PROFILE-OGMA":
                                        ui.notify('Code de confirmation incorrect', type='negative')
                                        return
                                    
                                    # Sauvegarder avant suppression si demandé
                                    if save_before_delete.value:
                                        save_name = f"backup_avant_suppression_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                                        success, msg, path = profile_mgr.save_current_profile(
                                            save_name, 
                                            "Sauvegarde automatique avant suppression du profil"
                                        )
                                        if success:
                                            ui.notify('Sauvegarde créée avant suppression', type='positive')
                                        else:
                                            ui.notify(f'Erreur sauvegarde: {msg}', type='negative')
                                            return
                                    
                                    # Procéder à la suppression
                                    success, message = profile_mgr.delete_current_profile("DELETE-PROFILE-OGMA")
                                    
                                    if success:
                                        ui.notify('Profil supprimé avec succès !', type='positive')
                                        delete_dialog.close()
                                        refresh_content()  # Rafraîchir l'affichage
                                    else:
                                        ui.notify(f'Erreur: {message}', type='negative')
                                
                                ui.button('🗑️ Supprimer Définitivement', on_click=perform_delete).classes('bg-red-600 text-white')
                        
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
                                            
                                            ui.label('Le profil actuel sera automatiquement sauvegardé avant remplacement.').classes('text-xs text-muted mb-4')
                                            
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
                                
                                ui.button('📂 Charger', icon='folder_open', 
                                         on_click=create_load_handler(backup['path'])).classes('bg-green-600 text-white')
                else:
                    ui.label('Aucune sauvegarde trouvée').classes('text-gray-500 text-center py-4')
            
            except Exception as e:
                ui.label(f'⚠️ Erreur ProfileManager : {e}').classes('text-red-500')
                print(f"[PROFILE] Erreur: {e}")

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
                            # Mettre à jour le profil actuel
                            current_profile_id = identity_manager.get_current_profile_id()
                            if current_profile_id and current_profile_id in identity_manager._data['profiles']:
                                identity_manager._data['profiles'][current_profile_id]['user_name'] = user_input.value.strip()
                                identity_manager.save_identities()
                                ui.notify(f'Nom utilisateur mis à jour : {user_input.value.strip()}', type='positive')
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
                
            except Exception as e:
                ui.label(f"❌ Erreur : {e}").classes('text-red-500')

            # === TRANSCRIPTION AUDIO ===
            ui.separator().classes('my-4')
            ui.label('Transcription et Auto-envoi').classes('text-lg font-medium mb-2')

            audio_auto_send = sm.settings.get('audio', {}).get('auto_send', False)

            def on_audio_auto_send_change(e):
                if 'audio' not in sm.settings:
                    sm.settings['audio'] = {}
                sm.settings['audio']['auto_send'] = e.value
                sm.save_settings()
                ui.notify('Paramètre audio sauvegardé', type='positive')

            ui.checkbox(
                'Envoi automatique après transcription vocale',
                value=audio_auto_send,
                on_change=on_audio_auto_send_change
            ).classes('mb-2')

            ui.label('Quand activé, les messages transcrits via microphone seront automatiquement envoyés après transcription.').classes('text-xs text-muted mb-4')

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

            # Si TTS est activé, afficher les paramètres
            if tts_enabled:
                ui.label('⚙️ Configuration TTS').classes('text-md font-medium mb-2')

                # Moteur TTS avec système sans conflit intégré
                engine_options = {
                    'conflict_free': '🎵 TTS Sans Conflit (recommandé)',
                    'edge_tts': '🎤 Microsoft Edge TTS (Gratuit)',
                    'gtts': '🌐 Google TTS Offline (Gratuit)',
                    'system': '🖥️ Système (pyttsx3)',
                    'azure': '☁️ Azure AI Speech (API)',
                    'google': '☁️ Google Cloud TTS (API)',
                    'elevenlabs': '🎯 ElevenLabs (API Premium)'
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
                        success = await audio_mgr.speak(test_text)
                        
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