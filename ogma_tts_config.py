"""
OGMA TTS Configuration
======================
Configuration spécialisée des moteurs Text-to-Speech.

CONTIENT :
- Configuration moteurs TTS (System, Google, ElevenLabs, Azure, gTTS)
- Tests et validation audio
- Paramètres audio communs (vitesse, volume)
- Interface de sélection des voix
"""

from nicegui import ui
import asyncio


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


def _reload_tts_config():
    """Recharge la configuration TTS depuis settings.json vers l'audio manager"""
    try:
        import sys
        ogma_ng = sys.modules.get('ogma_ng')
        if ogma_ng:
            # Appeler _apply_tts_config_from_settings si disponible
            apply_func = getattr(ogma_ng, '_apply_tts_config_from_settings', None)
            audio_mgr = getattr(ogma_ng, '_audio_manager', None)
            sm = getattr(ogma_ng, '_settings_mgr', None)
            
            # Debug: afficher la voix actuelle dans settings
            if sm:
                voice_in_settings = sm.settings.get('tts', {}).get('elevenlabs_voice_id', 'N/A')
                print(f"[TTS-CONFIG] Voice ID dans settings: {voice_in_settings}")
            
            if apply_func and audio_mgr:
                apply_func(audio_mgr)
                print("[TTS-CONFIG] Configuration TTS rechargée")
            else:
                print("[TTS-CONFIG] Fonction ou audio_manager non disponible")
    except Exception as e:
        print(f"[TTS-CONFIG] Erreur reload: {e}")


def _render_tts_config(current_engine, sm, refresh_callback):
    """Affiche la configuration spécifique au moteur TTS sélectionné."""

    # (debug TTS désactivé)

    if current_engine == 'system':
        # Configuration voix système
        ui.label('Configuration Système').classes('text-sm font-medium mb-2')

        _audio_manager = _get_global_var('_audio_manager')
        if _audio_manager is None:
            _ensure_audio_manager = _get_global_var('_ensure_audio_manager')
            if _ensure_audio_manager:
                _audio_manager = _ensure_audio_manager()

        if _audio_manager and hasattr(_audio_manager, 'get_available_voices'):
            available_voices = _audio_manager.get_available_voices()
            if available_voices:
                current_voice_id = sm.settings.get('tts', {}).get('voice_id', 'auto')

                # Créer la liste des options pour le select
                voice_options = {'auto': '🤖 Auto (Sélection automatique)'}
                for voice in available_voices:
                    flag = "🇫🇷" if voice['language'] == 'fr' else "🇬🇧"
                    gender = "♀️" if voice['gender'] == 'female' else "♂️"
                    label = f"{flag} {gender} {voice['name']}"
                    voice_options[voice['id']] = label

                # Vérifier que la voix actuelle existe dans les options
                if current_voice_id not in voice_options:
                    current_voice_id = 'auto'
                    if 'tts' not in sm.settings:
                        sm.settings['tts'] = {}
                    sm.settings['tts']['voice_id'] = 'auto'
                    sm.save_settings()

                def on_voice_change(e):
                    _audio_manager = _get_global_var('_audio_manager')
                    voice_id = e.value
                    if 'tts' not in sm.settings:
                        sm.settings['tts'] = {}
                    sm.settings['tts']['voice_id'] = voice_id
                    sm.save_settings()

                    if _audio_manager and hasattr(_audio_manager, 'set_voice'):
                        _audio_manager.set_voice(voice_id)

                    voice_name = 'Sélection automatique' if voice_id == 'auto' else voice_options.get(voice_id, voice_id)
                    ui.notify(f'Voix changée: {voice_name}', type='positive')

                ui.select(
                    label='Voix système disponibles',
                    options=voice_options,
                    value=current_voice_id,
                    on_change=on_voice_change
                ).classes('mb-3')

                # Bouton test voix système
                def test_system_voice():
                    async def _test():
                        _audio_manager = _get_global_var('_audio_manager')
                        if _audio_manager:
                            test_text = "Bonjour, ceci est un test de la synthèse vocale système."
                            try:
                                # Utiliser speak_async pour compatibilité await
                                if hasattr(_audio_manager, 'speak_async'):
                                    success = await _audio_manager.speak_async(test_text)
                                else:
                                    success = _audio_manager.speak(test_text)
                                if success:
                                    _notify_safe('🔊 Test vocal réussi', 'positive')
                                else:
                                    _notify_safe('❌ Erreur lors du test vocal', 'negative')
                            except Exception as e:
                                _notify_safe(f'❌ Erreur test TTS: {str(e)}', 'negative')
                        else:
                            _notify_safe('❌ Audio manager non disponible', 'negative')

                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.ensure_future(_test())
                        else:
                            loop.run_until_complete(_test())
                    except:
                        asyncio.create_task(_test())

                ui.button('🧪 Tester la voix système', on_click=test_system_voice).classes('mb-3')
            else:
                ui.label("❌ Aucune voix système disponible").classes('text-red-500 mb-2')
                ui.button('🔄 Réessayer', on_click=refresh_callback).classes('mb-2')
        else:
            ui.label("❌ Audio manager non initialisé").classes('text-red-500 mb-2')
            ui.button('🔄 Réessayer', on_click=refresh_callback).classes('mb-2')

    elif current_engine == 'google':
        # Configuration Google Cloud TTS
        ui.label('Configuration Google Cloud TTS').classes('text-sm font-medium mb-2')

        # Clé API Google
        google_api_key = sm.settings.get('tts', {}).get('google_api_key', '')
        def on_google_key_change(e):
            if 'tts' not in sm.settings:
                sm.settings['tts'] = {}
            sm.settings['tts']['google_api_key'] = e.value
            sm.save_settings()
            ui.notify('Clé API Google sauvegardée', type='positive')

        ui.input(
            label='Clé API Google Cloud',
            placeholder='Entrez votre clé API Google Cloud',
            password=True,
            value=google_api_key,
            on_change=on_google_key_change
        ).classes('mb-3')

        # Voix Google
        google_voice = sm.settings.get('tts', {}).get('google_voice', 'fr-FR-Standard-A')
        def on_google_voice_change(e):
            if 'tts' not in sm.settings:
                sm.settings['tts'] = {}
            sm.settings['tts']['google_voice'] = e.value
            sm.save_settings()
            ui.notify(f'Voix Google changée: {e.value}', type='positive')

        google_voice_options = {
            'fr-FR-Standard-A': '🇫🇷 ♀️ Française Standard A',
            'fr-FR-Standard-B': '🇫🇷 ♂️ Français Standard B',
            'fr-FR-Standard-C': '🇫🇷 ♀️ Française Standard C',
            'fr-FR-Standard-D': '🇫🇷 ♂️ Français Standard D',
            'fr-FR-Neural2-A': '🇫🇷 ♀️ Française Neural A',
            'fr-FR-Neural2-B': '🇫🇷 ♂️ Français Neural B',
            'en-US-Standard-A': '🇬🇧 ♀️ Anglaise Standard A',
            'en-US-Standard-B': '🇬🇧 ♂️ Anglais Standard B',
            'en-US-Neural2-A': '🇬🇧 ♀️ Anglaise Neural A',
            'en-US-Neural2-B': '🇬🇧 ♂️ Anglais Neural B'
        }

        ui.select(
            label='Voix Google Cloud',
            options=google_voice_options,
            value=google_voice,
            on_change=on_google_voice_change
        ).classes('mb-3')

        # Bouton test Google TTS
        def test_google_tts():
            async def _test():
                _audio_manager = _get_global_var('_audio_manager')
                if not google_api_key:
                    _notify_safe('❌ Clé API Google manquante', 'negative')
                    return

                if _audio_manager:
                    test_text = "Bonjour, ceci est un test de Google Cloud Text-to-Speech."
                    try:
                        success = await _audio_manager.speak_google_tts(
                            test_text,
                            google_voice,
                            google_api_key
                        )
                        if success:
                            _notify_safe('🔊 Test Google TTS réussi', 'positive')
                        else:
                            _notify_safe('❌ Erreur test Google TTS', 'negative')
                    except Exception as e:
                        _notify_safe(f'❌ Erreur Google TTS: {str(e)}', 'negative')
                else:
                    _notify_safe('❌ Audio manager non disponible', 'negative')

            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(_test())
                else:
                    loop.run_until_complete(_test())
            except:
                asyncio.create_task(_test())

        ui.button('🧪 Tester Google TTS', on_click=test_google_tts).classes('mb-3')

    elif current_engine == 'elevenlabs':
        # Configuration ElevenLabs
        ui.label('Configuration ElevenLabs').classes('text-sm font-medium mb-2')

        # Clé API ElevenLabs
        elevenlabs_api_key = sm.settings.get('tts', {}).get('elevenlabs_api_key', '')
        def on_elevenlabs_key_change(e):
            if 'tts' not in sm.settings:
                sm.settings['tts'] = {}
            sm.settings['tts']['elevenlabs_api_key'] = e.value
            sm.save_settings()
            # Recharger la config TTS dans l'audio manager
            _reload_tts_config()
            ui.notify('Clé API ElevenLabs sauvegardée', type='positive')

        ui.input(
            label='Clé API ElevenLabs',
            placeholder='Entrez votre clé API ElevenLabs',
            password=True,
            value=elevenlabs_api_key,
            on_change=on_elevenlabs_key_change
        ).classes('mb-3')

        # ID de voix ElevenLabs
        elevenlabs_voice_id = sm.settings.get('tts', {}).get('elevenlabs_voice_id', 'pNInz6obpgDQGcFmaJgB')
        def on_elevenlabs_voice_change(e):
            if 'tts' not in sm.settings:
                sm.settings['tts'] = {}
            sm.settings['tts']['elevenlabs_voice_id'] = e.value
            sm.save_settings()
            # Recharger la config TTS dans l'audio manager
            _reload_tts_config()
            ui.notify('Voice ID ElevenLabs sauvegardé', type='positive')

        ui.input(
            label='Voice ID ElevenLabs',
            placeholder='ID de la voix (ex: pNInz6obpgDQGcFmaJgB)',
            value=elevenlabs_voice_id,
            on_change=on_elevenlabs_voice_change
        ).classes('mb-3')

        # Sélection du modèle ElevenLabs
        elevenlabs_model = sm.settings.get('tts', {}).get('elevenlabs_model', 'eleven_multilingual_v2')
        model_options = {
            'eleven_multilingual_v2': '🌍 Multilingual v2 (haute qualité)',
            'eleven_turbo_v2_5': '⚡ Turbo v2.5 (rapide)',
            'eleven_flash_v2_5': '💨 Flash v2.5 (ultra-rapide)'
        }
        def on_elevenlabs_model_change(e):
            if 'tts' not in sm.settings:
                sm.settings['tts'] = {}
            sm.settings['tts']['elevenlabs_model'] = e.value
            sm.save_settings()
            _reload_tts_config()
            ui.notify(f'Modèle ElevenLabs: {model_options.get(e.value, e.value)}', type='positive')

        ui.select(
            label='Modèle',
            options=model_options,
            value=elevenlabs_model,
            on_change=on_elevenlabs_model_change
        ).classes('mb-3')

        # === Paramètres vocaux avancés ===
        with ui.expansion('🎛️ Paramètres vocaux avancés', icon='tune').classes('w-full mb-3'):
            
            # Stability (stabilité de la voix)
            elevenlabs_stability = sm.settings.get('tts', {}).get('elevenlabs_stability', 0.5)
            def on_stability_change(e):
                if 'tts' not in sm.settings:
                    sm.settings['tts'] = {}
                sm.settings['tts']['elevenlabs_stability'] = e.value
                sm.save_settings()
                _reload_tts_config()
            
            with ui.row().classes('w-full items-center gap-2 mb-2'):
                ui.label('Stabilité').classes('text-sm w-24')
                ui.slider(min=0, max=1, step=0.05, value=elevenlabs_stability, on_change=on_stability_change).classes('flex-grow')
                ui.label().bind_text_from(lambda: f'{sm.settings.get("tts", {}).get("elevenlabs_stability", 0.5):.2f}').classes('text-xs w-10')
            ui.label('↑ Plus stable = voix cohérente | ↓ Plus variable = expressif').classes('text-xs text-muted mb-2')

            # Similarity Boost (ressemblance à la voix originale)
            elevenlabs_similarity = sm.settings.get('tts', {}).get('elevenlabs_similarity', 0.75)
            def on_similarity_change(e):
                if 'tts' not in sm.settings:
                    sm.settings['tts'] = {}
                sm.settings['tts']['elevenlabs_similarity'] = e.value
                sm.save_settings()
                _reload_tts_config()
            
            with ui.row().classes('w-full items-center gap-2 mb-2'):
                ui.label('Similarité').classes('text-sm w-24')
                ui.slider(min=0, max=1, step=0.05, value=elevenlabs_similarity, on_change=on_similarity_change).classes('flex-grow')
                ui.label().bind_text_from(lambda: f'{sm.settings.get("tts", {}).get("elevenlabs_similarity", 0.75):.2f}').classes('text-xs w-10')
            ui.label('Ressemblance à la voix clonée/originale').classes('text-xs text-muted mb-2')

            # Style (expressivité)
            elevenlabs_style = sm.settings.get('tts', {}).get('elevenlabs_style', 0.0)
            def on_style_change(e):
                if 'tts' not in sm.settings:
                    sm.settings['tts'] = {}
                sm.settings['tts']['elevenlabs_style'] = e.value
                sm.save_settings()
                _reload_tts_config()
            
            with ui.row().classes('w-full items-center gap-2 mb-2'):
                ui.label('Style').classes('text-sm w-24')
                ui.slider(min=0, max=1, step=0.05, value=elevenlabs_style, on_change=on_style_change).classes('flex-grow')
                ui.label().bind_text_from(lambda: f'{sm.settings.get("tts", {}).get("elevenlabs_style", 0.0):.2f}').classes('text-xs w-10')
            ui.label('Expressivité émotionnelle (0 = neutre, 1 = très expressif)').classes('text-xs text-muted mb-2')

            # Speed (vitesse de parole)
            elevenlabs_speed = sm.settings.get('tts', {}).get('elevenlabs_speed', 1.0)
            def on_speed_change(e):
                if 'tts' not in sm.settings:
                    sm.settings['tts'] = {}
                sm.settings['tts']['elevenlabs_speed'] = e.value
                sm.save_settings()
                _reload_tts_config()
            
            with ui.row().classes('w-full items-center gap-2 mb-2'):
                ui.label('Vitesse').classes('text-sm w-24')
                ui.slider(min=0.5, max=2.0, step=0.1, value=elevenlabs_speed, on_change=on_speed_change).classes('flex-grow')
                ui.label().bind_text_from(lambda: f'{sm.settings.get("tts", {}).get("elevenlabs_speed", 1.0):.1f}x').classes('text-xs w-10')
            ui.label('Vitesse de parole (0.5x lent → 2.0x rapide)').classes('text-xs text-muted mb-2')

            # Speaker Boost (amélioration vocale)
            elevenlabs_speaker_boost = sm.settings.get('tts', {}).get('elevenlabs_speaker_boost', True)
            def on_speaker_boost_change(e):
                if 'tts' not in sm.settings:
                    sm.settings['tts'] = {}
                sm.settings['tts']['elevenlabs_speaker_boost'] = e.value
                sm.save_settings()
                _reload_tts_config()
            
            ui.switch('Speaker Boost (améliore la clarté)', value=elevenlabs_speaker_boost, on_change=on_speaker_boost_change).classes('mb-2')

        # Bouton test ElevenLabs
        def test_elevenlabs_tts():
            async def _test():
                _audio_manager = _get_global_var('_audio_manager')
                # Relire les valeurs actuelles depuis settings (pas les captures de closure)
                current_key = sm.settings.get('tts', {}).get('elevenlabs_api_key', '')
                current_voice = sm.settings.get('tts', {}).get('elevenlabs_voice_id', 'pNInz6obpgDQGcFmaJgB')
                
                if not current_key:
                    _notify_safe('❌ Clé API ElevenLabs manquante', 'negative')
                    return

                if _audio_manager:
                    test_text = "Bonjour, ceci est un test de ElevenLabs Voice AI."
                    try:
                        success = await _audio_manager.speak_elevenlabs(
                            test_text,
                            current_voice,
                            current_key
                        )
                        if success:
                            _notify_safe('🔊 Test ElevenLabs réussi', 'positive')
                        else:
                            _notify_safe('❌ Erreur test ElevenLabs', 'negative')
                    except Exception as e:
                        _notify_safe(f'❌ Erreur ElevenLabs: {str(e)}', 'negative')
                else:
                    _notify_safe('❌ Audio manager non disponible', 'negative')

            # Lancer la tâche asynchrone sans créer de nouvelle tâche
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(_test())
                else:
                    loop.run_until_complete(_test())
            except:
                asyncio.create_task(_test())

        ui.button('🧪 Tester ElevenLabs', on_click=test_elevenlabs_tts).classes('mb-3')

        ui.label('💡 Trouvez les Voice IDs sur votre tableau de bord ElevenLabs').classes('text-xs text-muted mb-3')

    elif current_engine == 'fish_audio':
        # Configuration Fish Audio
        ui.label('Configuration Fish Audio').classes('text-sm font-medium mb-2')

        # Clé API Fish Audio
        fish_audio_api_key = sm.settings.get('tts', {}).get('fish_audio_api_key', '')
        def on_fish_audio_key_change(e):
            if 'tts' not in sm.settings:
                sm.settings['tts'] = {}
            sm.settings['tts']['fish_audio_api_key'] = e.value
            sm.save_settings()
            _reload_tts_config()
            ui.notify('Clé API Fish Audio sauvegardée', type='positive')

        ui.input(
            label='Clé API Fish Audio',
            placeholder='Entrez votre clé API Fish Audio',
            password=True,
            value=fish_audio_api_key,
            on_change=on_fish_audio_key_change
        ).classes('mb-3')

        # ID de voix Fish Audio (reference_id)
        fish_audio_voice_id = sm.settings.get('tts', {}).get('fish_audio_voice_id', '')
        def on_fish_audio_voice_change(e):
            if 'tts' not in sm.settings:
                sm.settings['tts'] = {}
            sm.settings['tts']['fish_audio_voice_id'] = e.value
            sm.save_settings()
            _reload_tts_config()
            ui.notify('Voice ID Fish Audio sauvegardé', type='positive')

        ui.input(
            label='Reference ID (Voice)',
            placeholder='ID du modèle de voix Fish Audio',
            value=fish_audio_voice_id,
            on_change=on_fish_audio_voice_change
        ).classes('mb-3')

        # Modèle Fish Audio
        fish_audio_model = sm.settings.get('tts', {}).get('fish_audio_model', 's2-pro')
        fish_audio_models = {
            's2-pro': 'S2 Pro (dernier, recommandé)',
            's1': 'S1 (standard)',
        }
        def on_fish_audio_model_change(e):
            if 'tts' not in sm.settings:
                sm.settings['tts'] = {}
            sm.settings['tts']['fish_audio_model'] = e.value
            sm.save_settings()
            _reload_tts_config()
            ui.notify(f'Modèle Fish Audio: {e.value}', type='positive')
        ui.select(
            label='Modèle',
            options=fish_audio_models,
            value=fish_audio_model,
            on_change=on_fish_audio_model_change
        ).classes('mb-3')

        # Émotion Fish Audio (injection dans le texte via balises)
        fish_audio_emotion = sm.settings.get('tts', {}).get('fish_audio_emotion', 'none')
        fish_audio_emotion_options = {
            'none': 'Aucune (voix naturelle)',
            'happy': 'Joyeux (happy)',
            'excited': 'Enthousiaste (excited)',
            'calm': 'Calme (calm)',
            'sad': 'Triste (sad)',
            'angry': 'En colère (angry)',
            'curious': 'Curieux (curious)',
            'confident': 'Confiant (confident)',
            'empathetic': 'Empathique (empathetic)',
            'nervous': 'Nerveux (nervous)',
            'grateful': 'Reconnaissant (grateful)',
            'relaxed': 'Détendu (relaxed)',
            'nostalgic': 'Nostalgique (nostalgic)',
            'determined': 'Déterminé (determined)',
            'whispering': 'Chuchotement (whispering)',
            'soft tone': 'Ton doux (soft tone)',
            'in a hurry tone': 'Pressé (in a hurry tone)',
            'shouting': 'Fort (shouting)',
        }
        def on_fish_audio_emotion_change(e):
            if 'tts' not in sm.settings:
                sm.settings['tts'] = {}
            sm.settings['tts']['fish_audio_emotion'] = e.value
            sm.save_settings()
            _reload_tts_config()
        ui.select(
            label='Émotion (injectée dans le texte)',
            options=fish_audio_emotion_options,
            value=fish_audio_emotion,
            on_change=on_fish_audio_emotion_change
        ).classes('mb-1')
        ui.label('S1 : syntaxe (balise). S2-pro : syntaxe [balise] — langage naturel libre.').classes('text-xs text-muted mb-3')

        # Options avancées Fish Audio
        with ui.expansion('Options avancées', icon='tune').classes('mb-3 w-full'):

            # Latence
            fish_audio_latency = sm.settings.get('tts', {}).get('fish_audio_latency', 'normal')
            fish_audio_latency_options = {
                'normal': 'Normal (qualité maximale)',
                'balanced': 'Balanced (~300ms, légèrement moins stable)',
            }
            def on_fish_audio_latency_change(e):
                if 'tts' not in sm.settings:
                    sm.settings['tts'] = {}
                sm.settings['tts']['fish_audio_latency'] = e.value
                sm.save_settings()
                _reload_tts_config()
            ui.select(
                label='Mode latence',
                options=fish_audio_latency_options,
                value=fish_audio_latency,
                on_change=on_fish_audio_latency_change
            ).classes('mb-3')

            # Chunk length
            fish_audio_chunk = sm.settings.get('tts', {}).get('fish_audio_chunk_length', 200)
            def on_fish_audio_chunk_change(e):
                if 'tts' not in sm.settings:
                    sm.settings['tts'] = {}
                val = max(100, min(300, int(e.value or 200)))
                sm.settings['tts']['fish_audio_chunk_length'] = val
                sm.save_settings()
                _reload_tts_config()
            with ui.row().classes('items-center gap-2 w-full mb-1'):
                ui.label('Chunk length').classes('text-sm w-28')
                ui.number(
                    min=100, max=300, step=10, value=fish_audio_chunk,
                    format='%d', suffix='chars',
                    on_change=on_fish_audio_chunk_change
                ).classes('w-32')
            ui.label('Taille des blocs de texte traités (100-300). Plus court = plus rapide.').classes('text-xs text-muted mb-3')

            # Bitrate MP3
            fish_audio_bitrate = sm.settings.get('tts', {}).get('fish_audio_mp3_bitrate', 128)
            fish_audio_bitrate_options = {64: '64 kbps (léger)', 128: '128 kbps (standard)', 192: '192 kbps (haute qualité)'}
            def on_fish_audio_bitrate_change(e):
                if 'tts' not in sm.settings:
                    sm.settings['tts'] = {}
                sm.settings['tts']['fish_audio_mp3_bitrate'] = int(e.value)
                sm.save_settings()
                _reload_tts_config()
            ui.select(
                label='Qualité MP3',
                options=fish_audio_bitrate_options,
                value=fish_audio_bitrate,
                on_change=on_fish_audio_bitrate_change
            ).classes('mb-3')

            # Normalize
            fish_audio_normalize = sm.settings.get('tts', {}).get('fish_audio_normalize', True)
            def on_fish_audio_normalize_change(e):
                if 'tts' not in sm.settings:
                    sm.settings['tts'] = {}
                sm.settings['tts']['fish_audio_normalize'] = e.value
                sm.save_settings()
                _reload_tts_config()
            ui.switch(
                'Normalisation du texte (recommandée)',
                value=fish_audio_normalize,
                on_change=on_fish_audio_normalize_change
            ).classes('mb-2')
            ui.label('Normalise les nombres, abréviations, etc. avant synthèse.').classes('text-xs text-muted mb-2')

        # Bouton test Fish Audio
        def test_fish_audio_tts():
            async def _test():
                _audio_manager = _get_global_var('_audio_manager')
                # Relire les valeurs actuelles depuis settings
                current_key = sm.settings.get('tts', {}).get('fish_audio_api_key', '')
                current_voice = sm.settings.get('tts', {}).get('fish_audio_voice_id', '')
                
                if not current_key:
                    _notify_safe('❌ Clé API Fish Audio manquante', 'negative')
                    return

                if _audio_manager:
                    test_text = "Bonjour, ceci est un test de Fish Audio."
                    try:
                        success = await _audio_manager.speak_fish_audio(
                            test_text,
                            current_voice,
                            current_key
                        )
                        if success:
                            _notify_safe('🔊 Test Fish Audio réussi', 'positive')
                        else:
                            _notify_safe('❌ Erreur test Fish Audio', 'negative')
                    except Exception as e:
                        _notify_safe(f'❌ Erreur Fish Audio: {str(e)}', 'negative')
                else:
                    _notify_safe('❌ Audio manager non disponible', 'negative')

            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(_test())
                else:
                    loop.run_until_complete(_test())
            except:
                asyncio.create_task(_test())

        ui.button('🧪 Tester Fish Audio', on_click=test_fish_audio_tts).classes('mb-3')

        ui.label('💡 Créez vos voix sur fish.audio et copiez le Reference ID').classes('text-xs text-muted mb-3')

    elif current_engine == 'cartesia':
        # Configuration Cartesia AI
        ui.label('Configuration Cartesia AI').classes('text-sm font-medium mb-2')

        # Clé API Cartesia
        cartesia_api_key = sm.settings.get('tts', {}).get('cartesia_api_key', '')
        def on_cartesia_key_change(e):
            if 'tts' not in sm.settings:
                sm.settings['tts'] = {}
            sm.settings['tts']['cartesia_api_key'] = e.value
            sm.save_settings()
            _reload_tts_config()
            ui.notify('Clé API Cartesia sauvegardée', type='positive')

        ui.input(
            label='Clé API Cartesia',
            placeholder='Entrez votre clé API Cartesia',
            password=True,
            value=cartesia_api_key,
            on_change=on_cartesia_key_change
        ).classes('mb-3')

        # ID de voix Cartesia
        cartesia_voice_id = sm.settings.get('tts', {}).get('cartesia_voice_id', '')
        def on_cartesia_voice_change(e):
            if 'tts' not in sm.settings:
                sm.settings['tts'] = {}
            sm.settings['tts']['cartesia_voice_id'] = e.value
            sm.save_settings()
            _reload_tts_config()
            ui.notify('Voice ID Cartesia sauvegardé', type='positive')

        ui.input(
            label='Voice ID Cartesia',
            placeholder='ID de la voix Cartesia',
            value=cartesia_voice_id,
            on_change=on_cartesia_voice_change
        ).classes('mb-3')

        # Modèle Cartesia
        cartesia_model = sm.settings.get('tts', {}).get('cartesia_model', 'sonic-2')
        cartesia_models = {
            'sonic-2': 'Sonic 2 (Standard)',
            'sonic-3': 'Sonic 3 (Premium)'
        }
        def on_cartesia_model_change(e):
            if 'tts' not in sm.settings:
                sm.settings['tts'] = {}
            sm.settings['tts']['cartesia_model'] = e.value
            sm.save_settings()
            _reload_tts_config()
            ui.notify(f'Modèle Cartesia: {e.value}', type='positive')

        ui.select(
            label='Modèle',
            options=cartesia_models,
            value=cartesia_model,
            on_change=on_cartesia_model_change
        ).classes('mb-3')

        # --- Controles sonic-3 uniquement ---
        cartesia_model_for_controls = sm.settings.get('tts', {}).get('cartesia_model', 'sonic-2')
        with ui.expansion('Options avancees (sonic-3)', icon='tune').classes('mb-3 w-full'):
            if cartesia_model_for_controls != 'sonic-3':
                ui.label('Ces options sont disponibles uniquement avec le modele sonic-3.').classes('text-xs text-muted')
            else:
                # Vitesse
                cartesia_speed = sm.settings.get('tts', {}).get('cartesia_speed', 1.0)
                def on_cartesia_speed_change(e):
                    if 'tts' not in sm.settings:
                        sm.settings['tts'] = {}
                    val = round(float(e.value), 2)
                    # Clamp dans la plage valide
                    val = max(0.6, min(1.5, val))
                    sm.settings['tts']['cartesia_speed'] = val
                    sm.save_settings()
                    _reload_tts_config()
                with ui.row().classes('items-center gap-2 w-full mb-1'):
                    ui.label('Vitesse').classes('text-sm w-20')
                    ui.number(
                        min=0.6, max=1.5, step=0.05, value=cartesia_speed,
                        format='%.2f', suffix='x',
                        on_change=on_cartesia_speed_change
                    ).classes('w-28')
                ui.label('0.6x (lent) → 1.0x (normal) → 1.5x (rapide)').classes('text-xs text-muted mb-3')

                # Emotion
                cartesia_emotion = sm.settings.get('tts', {}).get('cartesia_emotion', 'neutral')
                cartesia_emotions = {
                    'neutral': 'Neutre',
                    'excited': 'Enthousiaste',
                    'content': 'Apaisee',
                    'sad': 'Triste',
                    'angry': 'Determinee',
                    'curious': 'Curieuse',
                    'affectionate': 'Affectueuse',
                    'calm': 'Calme',
                    'sympathetic': 'Empathique',
                    'mysterious': 'Mysterieuse',
                }
                def on_cartesia_emotion_change(e):
                    if 'tts' not in sm.settings:
                        sm.settings['tts'] = {}
                    sm.settings['tts']['cartesia_emotion'] = e.value
                    sm.save_settings()
                    _reload_tts_config()
                    ui.notify(f'Emotion: {e.value}', type='positive')
                ui.select(
                    label='Emotion',
                    options=cartesia_emotions,
                    value=cartesia_emotion,
                    on_change=on_cartesia_emotion_change
                ).classes('mb-1')
                ui.label('Guide emotionnel pour la voix (beta Cartesia)').classes('text-xs text-muted mb-2')

        # Bouton test Cartesia
        def test_cartesia_tts():
            async def _test():
                _audio_manager = _get_global_var('_audio_manager')
                # Relire les valeurs actuelles depuis settings
                current_key = sm.settings.get('tts', {}).get('cartesia_api_key', '')
                current_voice = sm.settings.get('tts', {}).get('cartesia_voice_id', '')
                current_model = sm.settings.get('tts', {}).get('cartesia_model', 'sonic-2')
                
                if not current_key:
                    _notify_safe('❌ Clé API Cartesia manquante', 'negative')
                    return

                if _audio_manager:
                    test_text = "Bonjour, ceci est un test de Cartesia AI."
                    try:
                        success = await _audio_manager.speak_cartesia(
                            test_text,
                            current_voice,
                            current_key,
                            current_model
                        )
                        if success:
                            _notify_safe('🔊 Test Cartesia réussi', 'positive')
                        else:
                            _notify_safe('❌ Erreur test Cartesia', 'negative')
                    except Exception as e:
                        _notify_safe(f'❌ Erreur Cartesia: {str(e)}', 'negative')
                else:
                    _notify_safe('❌ Audio manager non disponible', 'negative')

            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(_test())
                else:
                    loop.run_until_complete(_test())
            except:
                asyncio.create_task(_test())

        ui.button('🧪 Tester Cartesia', on_click=test_cartesia_tts).classes('mb-3')

        ui.label('💡 Trouvez vos voix sur cartesia.ai dans la Voice Library').classes('text-xs text-muted mb-3')

    elif current_engine == 'hume_ai' or current_engine.strip().lower() == 'hume_ai':
        # Configuration Hume AI (Octave TTS)
        ui.label('Configuration Hume AI (Octave TTS)').classes('text-sm font-medium mb-2')

        # Clé API Hume AI
        hume_ai_api_key = sm.settings.get('tts', {}).get('hume_ai_api_key', '')
        def on_hume_ai_key_change(e):
            if 'tts' not in sm.settings:
                sm.settings['tts'] = {}
            sm.settings['tts']['hume_ai_api_key'] = e.value
            sm.save_settings()
            # Appliquer la config
            _reload_tts_config()
            ui.notify('Clé API Hume AI sauvegardée', type='positive')

        ui.input(
            label='Clé API Hume AI',
            placeholder='Entrez votre clé API Hume AI',
            password=True,
            value=hume_ai_api_key,
            on_change=on_hume_ai_key_change
        ).classes('mb-3')

        # Sélecteur version Octave
        hume_ai_version = sm.settings.get('tts', {}).get('hume_ai_version', 2)
        def on_hume_version_change(e):
            if 'tts' not in sm.settings:
                sm.settings['tts'] = {}
            sm.settings['tts']['hume_ai_version'] = e.value
            sm.save_settings()
            _reload_tts_config()
            ui.notify(f'Version Octave {e.value} sélectionnée', type='positive')

        octave_version_options = {
            1: '🎵 Octave 1 (stable)',
            2: '⚡ Octave 2 (preview - plus rapide, multi-langues)'
        }

        ui.select(
            label='Version Octave',
            options=octave_version_options,
            value=hume_ai_version,
            on_change=on_hume_version_change
        ).classes('mb-3')

        ui.label('💡 Octave 2 : ~100ms latence, 11 langues | Octave 1 : anglais/espagnol uniquement').classes('text-xs text-muted mb-2')

        # Voice ID personnalisé (priorité haute)
        hume_ai_voice_id = sm.settings.get('tts', {}).get('hume_ai_voice_id', '')
        def on_hume_voice_id_change(e):
            if 'tts' not in sm.settings:
                sm.settings['tts'] = {}
            sm.settings['tts']['hume_ai_voice_id'] = e.value
            sm.save_settings()
            _reload_tts_config()
            ui.notify('Voice ID Hume AI sauvegardé', type='positive')

        ui.input(
            label='Voice ID personnalisé (optionnel - prioritaire)',
            placeholder='Ex: 09ad914d-8e7f-40f8-a279-e34f07f7dab2',
            value=hume_ai_voice_id,
            on_change=on_hume_voice_id_change
        ).classes('mb-2')

        ui.label('💡 Trouvez vos Voice IDs sur app.hume.ai/voices (voix créées ou clonées)').classes('text-xs text-muted mb-3')

        # Nom de la voix Hume (Voice Library) - si pas de Voice ID
        hume_ai_voice_name = sm.settings.get('tts', {}).get('hume_ai_voice_name', '')
        def on_hume_ai_voice_change(e):
            if 'tts' not in sm.settings:
                sm.settings['tts'] = {}
            sm.settings['tts']['hume_ai_voice_name'] = e.value
            sm.save_settings()
            _reload_tts_config()
            ui.notify('Voix Hume AI sauvegardée', type='positive')

        # Voix populaires de la Voice Library Hume
        hume_voice_options = {
            '': '🎲 Voix dynamique (utilise la description)',
            'Dacher': '🎭 Dacher - Voix expressive masculine',
            'Kora': '🎭 Kora - Voix féminine chaleureuse',
            'Aura': '🎭 Aura - Voix féminine douce',
            'Stella': '🎭 Stella - Voix féminine professionnelle',
            'Orion': '🎭 Orion - Voix masculine grave',
            'Zephyr': '🎭 Zephyr - Voix neutre fluide',
            'Atlas': '🎭 Atlas - Voix masculine autoritaire',
            'Ember': '🎭 Ember - Voix féminine énergique',
        }

        ui.select(
            label='Voix Voice Library (si pas de Voice ID)',
            options=hume_voice_options,
            value=hume_ai_voice_name,
            on_change=on_hume_ai_voice_change
        ).classes('mb-3')

        # Description pour voix dynamique
        hume_ai_description = sm.settings.get('tts', {}).get('hume_ai_description', '')
        def on_hume_ai_description_change(e):
            if 'tts' not in sm.settings:
                sm.settings['tts'] = {}
            sm.settings['tts']['hume_ai_description'] = e.value
            sm.save_settings()
            # Appliquer la config
            _reload_tts_config()
            ui.notify('Description Hume AI sauvegardée', type='positive')

        ui.textarea(
            label='Description de la voix (optionnel)',
            placeholder='Ex: "Voix féminine chaleureuse et empathique, avec un léger accent français"',
            value=hume_ai_description,
            on_change=on_hume_ai_description_change
        ).classes('mb-3').style('min-height: 80px')

        ui.label('💡 Si aucune voix n\'est sélectionnée, Hume génère une voix à partir de la description').classes('text-xs text-muted mb-2')

        # Bouton test Hume AI
        def test_hume_ai_tts():
            async def _test():
                _audio_manager = _get_global_var('_audio_manager')
                # Relire les valeurs actuelles depuis settings
                current_key = sm.settings.get('tts', {}).get('hume_ai_api_key', '')
                current_voice_name = sm.settings.get('tts', {}).get('hume_ai_voice_name', '')
                current_voice_id = sm.settings.get('tts', {}).get('hume_ai_voice_id', '')
                current_desc = sm.settings.get('tts', {}).get('hume_ai_description', '')
                current_version = sm.settings.get('tts', {}).get('hume_ai_version', 2)
                
                if not current_key:
                    _notify_safe('❌ Clé API Hume AI manquante', 'negative')
                    return

                if _audio_manager:
                    test_text = "Bonjour, ceci est un test de Hume AI avec Octave."
                    try:
                        success = await _audio_manager.speak_hume_ai(
                            test_text,
                            current_voice_name,
                            current_key,
                            current_desc,
                            current_voice_id,
                            current_version
                        )
                        if success:
                            _notify_safe('🔊 Test Hume AI réussi', 'positive')
                        else:
                            _notify_safe('❌ Erreur test Hume AI', 'negative')
                    except Exception as e:
                        _notify_safe(f'❌ Erreur Hume AI: {str(e)}', 'negative')
                else:
                    _notify_safe('❌ Audio manager non disponible', 'negative')

            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(_test())
                else:
                    loop.run_until_complete(_test())
            except:
                asyncio.create_task(_test())

        ui.button('🧪 Tester Hume AI', on_click=test_hume_ai_tts).classes('mb-3')

        ui.label('💡 Explorez les voix sur app.hume.ai/voices').classes('text-xs text-muted mb-3')

    elif current_engine == 'azure' or current_engine.strip().lower() == 'azure':
        # Configuration Azure AI Speech
        print("[DEBUG-TTS] ✅ SECTION 1 AZURE ACTIVÉE DANS _render_tts_config")
        ui.label('Configuration Azure AI Speech').classes('text-sm font-medium mb-2')

        # Clé API Azure
        azure_api_key = sm.settings.get('tts', {}).get('azure_api_key', '')
        def on_azure_key_change(e):
            if 'tts' not in sm.settings:
                sm.settings['tts'] = {}
            sm.settings['tts']['azure_api_key'] = e.value
            sm.save_settings()
            ui.notify('Clé API Azure sauvegardée', type='positive')

        ui.input(
            label='Clé API Azure',
            placeholder='Entrez votre clé API Azure Speech',
            password=True,
            value=azure_api_key,
            on_change=on_azure_key_change
        ).classes('mb-3')

        # Région Azure
        azure_region = sm.settings.get('tts', {}).get('azure_region', 'eastus')
        def on_azure_region_change(e):
            if 'tts' not in sm.settings:
                sm.settings['tts'] = {}
            sm.settings['tts']['azure_region'] = e.value
            sm.save_settings()
            ui.notify(f'Région Azure: {e.value}', type='positive')

        ui.input(
            label='Région Azure',
            placeholder='eastus, westeurope, etc.',
            value=azure_region,
            on_change=on_azure_region_change
        ).classes('mb-3')

        # Voix Azure
        azure_voice = sm.settings.get('tts', {}).get('azure_voice', 'fr-FR-DeniseNeural')
        def on_azure_voice_change(e):
            if 'tts' not in sm.settings:
                sm.settings['tts'] = {}
            sm.settings['tts']['azure_voice'] = e.value
            sm.save_settings()
            ui.notify(f'Voix Azure changée: {e.value}', type='positive')

        azure_voice_options = {
            'fr-FR-DeniseNeural': '🇫🇷 ♀️ Denise (Neural)',
            'fr-FR-HenriNeural': '🇫🇷 ♂️ Henri (Neural)',
            'fr-FR-AlainNeural': '🇫🇷 ♂️ Alain (Neural)',
            'fr-FR-BrigitteNeural': '🇫🇷 ♀️ Brigitte (Neural)',
            'fr-FR-CelesteNeural': '🇫🇷 ♀️ Celeste (Neural)',
            'fr-FR-ClaudeNeural': '🇫🇷 ♂️ Claude (Neural)',
            'fr-FR-CoralieNeural': '🇫🇷 ♀️ Coralie (Neural)',
            'fr-FR-EloiseNeural': '🇫🇷 ♀️ Eloise (Neural)',
            'fr-FR-JacquelineNeural': '🇫🇷 ♀️ Jacqueline (Neural)',
            'fr-FR-JeromeNeural': '🇫🇷 ♂️ Jerome (Neural)',
            'fr-FR-MauriceNeural': '🇫🇷 ♂️ Maurice (Neural)',
            'fr-FR-YvesNeural': '🇫🇷 ♂️ Yves (Neural)',
            'fr-FR-YvetteNeural': '🇫🇷 ♀️ Yvette (Neural)',
            'fr-CA-AntoineNeural': '🇨🇦 ♂️ Antoine (Canadien)',
            'fr-CA-JeanNeural': '🇨🇦 ♂️ Jean (Canadien)',
            'fr-CA-SylvieNeural': '🇨🇦 ♀️ Sylvie (Canadienne)',
            'en-US-AriaNeural': '🇺🇸 ♀️ Aria (Neural)',
            'en-US-DavisNeural': '🇺🇸 ♂️ Davis (Neural)',
            'en-US-GuyNeural': '🇺🇸 ♂️ Guy (Neural)',
            'en-US-JaneNeural': '🇺🇸 ♀️ Jane (Neural)',
            'en-US-JasonNeural': '🇺🇸 ♂️ Jason (Neural)',
            'en-US-JennyNeural': '🇺🇸 ♀️ Jenny (Neural)',
            'en-US-NancyNeural': '🇺🇸 ♀️ Nancy (Neural)',
            'en-US-SaraNeural': '🇺🇸 ♀️ Sara (Neural)',
            'en-US-TonyNeural': '🇺🇸 ♂️ Tony (Neural)'
        }

        ui.select(
            label='Voix Azure Speech',
            options=azure_voice_options,
            value=azure_voice,
            on_change=on_azure_voice_change
        ).classes('mb-3')

        # Bouton test Azure
        def test_azure_tts():
            async def _test():
                _audio_manager = _get_global_var('_audio_manager')
                if not azure_api_key:
                    _notify_safe('❌ Clé API Azure manquante', 'negative')
                    return

                if _audio_manager:
                    test_text = "Bonjour, ceci est un test d'Azure AI Speech."
                    try:
                        success = await _audio_manager.speak_azure(test_text)
                        if success:
                            _notify_safe('🔊 Test Azure AI Speech réussi', 'positive')
                        else:
                            _notify_safe('❌ Erreur test Azure', 'negative')
                    except Exception as e:
                        _notify_safe(f'❌ Erreur Azure: {str(e)}', 'negative')
                else:
                    _notify_safe('❌ Audio manager non disponible', 'negative')

            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(_test())
                else:
                    loop.run_until_complete(_test())
            except:
                asyncio.create_task(_test())

        ui.button('🧪 Tester Azure AI Speech', on_click=test_azure_tts).classes('mb-3')

        ui.label('💡 Obtenez vos clés API sur le portail Azure Speech Services').classes('text-xs text-muted mb-3')

    elif current_engine == 'gtts' or current_engine.strip().lower() == 'gtts':
        # Configuration Google TTS Offline (gTTS)
        print("[DEBUG-TTS] ✅ SECTION gTTS ACTIVÉE")
        ui.label('Configuration Google TTS Offline (gTTS)').classes('text-sm font-medium mb-2')

        # Langue gTTS
        gtts_lang = sm.settings.get('tts', {}).get('gtts_lang', 'fr')
        def on_gtts_lang_change(e):
            if 'tts' not in sm.settings:
                sm.settings['tts'] = {}
            sm.settings['tts']['gtts_lang'] = e.value
            sm.save_settings()

            _audio_manager = _get_global_var('_audio_manager')
            if _audio_manager:
                _audio_manager.gtts_lang = e.value

            ui.notify(f'Langue gTTS: {e.value}', type='positive')

        gtts_lang_options = {
            'fr': '🇫🇷 Français',
            'en': '🇬🇧 Anglais',
            'es': '🇪🇸 Espagnol (Général)',
            'es-mx': '🇲🇽 Espagnol (Mexique)',
            'es-ar': '🇦🇷 Espagnol (Argentine)',
            'es-co': '🇨🇴 Espagnol (Colombie)',
            'es-cl': '🇨🇱 Espagnol (Chili)',
            'es-ve': '🇻🇪 Espagnol (Venezuela)',
            'pt': '🇵🇹 Portugais',
            'pt-br': '🇧🇷 Portugais (Brésil)',
            'de': '🇩🇪 Allemand',
            'it': '🇮🇹 Italien'
        }

        ui.select(
            label='Langue gTTS',
            options=gtts_lang_options,
            value=gtts_lang,
            on_change=on_gtts_lang_change
        ).classes('mb-3')

        # Bouton test gTTS
        def test_gtts_tts():
            async def _test():
                _audio_manager = _get_global_var('_audio_manager')
                if _audio_manager:
                    test_text = "Bonjour, ceci est un test de Google TTS offline."
                    try:
                        success = await _audio_manager.speak_gtts(test_text, gtts_lang)
                        if success:
                            _notify_safe('🔊 Test gTTS réussi', 'positive')
                        else:
                            _notify_safe('❌ Erreur test gTTS', 'negative')
                    except Exception as e:
                        _notify_safe(f'❌ Erreur gTTS: {str(e)}', 'negative')
                else:
                    _notify_safe('❌ Audio manager non disponible', 'negative')

            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(_test())
                else:
                    loop.run_until_complete(_test())
            except:
                asyncio.create_task(_test())

        ui.button('🧪 Tester Google TTS Offline', on_click=test_gtts_tts).classes('mb-3')

        ui.label('💡 Google TTS offline - gratuit mais nécessite une connexion internet pour la synthèse').classes('text-xs text-muted mb-3')

    # Note: Edge TTS a été retiré (bloqué par Microsoft depuis 2024 - erreur 403 Forbidden)
    # Le service gratuit non-officiel n'est plus fonctionnel.

    # === PARAMÈTRES AUDIO COMMUNS ===
    ui.separator().classes('my-3')
    ui.label('🔧 Paramètres audio').classes('text-md font-medium mb-2')

    # Vitesse de parole (SpinBox)
    tts_speed = sm.settings.get('tts', {}).get('speed', 150)

    def on_speed_change(e):
        _audio_manager = _get_global_var('_audio_manager')
        speed = int(e.value) if e.value else 150
        if 'tts' not in sm.settings:
            sm.settings['tts'] = {}
        sm.settings['tts']['speed'] = speed
        sm.save_settings()

        if _audio_manager and hasattr(_audio_manager, 'set_tts_settings'):
            _audio_manager.set_tts_settings(speed=speed)

        ui.notify(f'Vitesse: {speed} mots/min', type='positive')

    with ui.row().classes('w-full items-center gap-2 mb-2'):
        ui.label('Vitesse de parole:').classes('text-sm w-32').tooltip(
            'Actif pour : Windows SAPI, pyttsx3, Azure, Google TTS.\n'
            'ElevenLabs : utiliser le slider Vitesse dans ses options avancees.\n'
            'Cartesia : utiliser le slider Vitesse dans Options avancees (sonic-3).\n'
            'Cartesia sonic-2 : aucun controle de vitesse disponible via API.'
        )
        ui.number(
            label='mots/min',
            value=tts_speed,
            min=50,
            max=300,
            step=10,
            on_change=on_speed_change
        ).classes('w-32')

    # Volume (SpinBox)
    tts_volume = sm.settings.get('tts', {}).get('volume', 0.8)

    def on_volume_change(e):
        _audio_manager = _get_global_var('_audio_manager')
        volume = float(e.value) if e.value else 0.8
        if volume > 1.0:
            volume = 1.0
        elif volume < 0.1:
            volume = 0.1

        if 'tts' not in sm.settings:
            sm.settings['tts'] = {}
        sm.settings['tts']['volume'] = volume
        sm.save_settings()

        if _audio_manager and hasattr(_audio_manager, 'set_tts_settings'):
            _audio_manager.set_tts_settings(volume=volume)

        ui.notify(f'Volume: {int(volume * 100)}%', type='positive')

    with ui.row().classes('w-full items-center gap-2 mb-4'):
        ui.label('Volume:').classes('text-sm w-32')
        ui.number(
            label='%',
            value=int(tts_volume * 100),
            min=10,
            max=100,
            step=10,
            on_change=lambda e: on_volume_change(type('obj', (object,), {'value': float(e.value) / 100 if e.value else 0.8})())
        ).classes('w-32')