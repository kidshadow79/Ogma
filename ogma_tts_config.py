"""
OGMA TTS Configuration
======================
Configuration spécialisée des moteurs Text-to-Speech.

CONTIENT :
- Configuration moteurs TTS (System, Google, ElevenLabs, Azure, gTTS, Edge TTS)
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


def _render_tts_config(current_engine, sm, refresh_callback):
    """Affiche la configuration spécifique au moteur TTS sélectionné."""

    print(f"[DEBUG-TTS] ========================")
    print(f"[DEBUG-TTS] _render_tts_config() APPELÉE")
    print(f"[DEBUG-TTS] Moteur reçu: '{current_engine}'")
    print(f"[DEBUG-TTS] Type: {type(current_engine)}")
    print(f"[DEBUG-TTS] Longueur: {len(current_engine)}")
    print(f"[DEBUG-TTS] Repr: {repr(current_engine)}")
    print(f"[DEBUG-TTS] ========================")

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
                            success = await _audio_manager.speak(test_text)
                            if success:
                                _notify_safe('🔊 Test vocal réussi', 'positive')
                            else:
                                _notify_safe('❌ Erreur lors du test vocal', 'negative')
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
            ui.notify('Voice ID ElevenLabs sauvegardé', type='positive')

        ui.input(
            label='Voice ID ElevenLabs',
            placeholder='ID de la voix (ex: pNInz6obpgDQGcFmaJgB)',
            value=elevenlabs_voice_id,
            on_change=on_elevenlabs_voice_change
        ).classes('mb-3')

        # Bouton test ElevenLabs
        def test_elevenlabs_tts():
            async def _test():
                _audio_manager = _get_global_var('_audio_manager')
                if not elevenlabs_api_key:
                    _notify_safe('❌ Clé API ElevenLabs manquante', 'negative')
                    return

                if _audio_manager:
                    test_text = "Bonjour, ceci est un test de ElevenLabs Voice AI."
                    try:
                        success = await _audio_manager.speak_elevenlabs(
                            test_text,
                            elevenlabs_voice_id,
                            elevenlabs_api_key
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

    elif current_engine == 'edge_tts' or current_engine.strip().lower() == 'edge_tts':
        # Configuration Microsoft Edge TTS
        print("[DEBUG-TTS] ✅ SECTION Edge TTS ACTIVÉE")
        ui.label('Configuration Microsoft Edge TTS').classes('text-sm font-medium mb-2')

        # Voix Edge TTS
        edge_voice = sm.settings.get('tts', {}).get('edge_tts_voice', 'fr-FR-DeniseNeural')
        def on_edge_voice_change(e):
            if 'tts' not in sm.settings:
                sm.settings['tts'] = {}
            sm.settings['tts']['edge_tts_voice'] = e.value
            sm.save_settings()

            _audio_manager = _get_global_var('_audio_manager')
            if _audio_manager:
                _audio_manager.edge_tts_voice = e.value

            ui.notify(f'Voix Edge TTS: {e.value}', type='positive')

        edge_voice_options = {
            # Voix françaises
            'fr-FR-DeniseNeural': '🇫🇷 ♀️ Denise (Française)',
            'fr-FR-HenriNeural': '🇫🇷 ♂️ Henri (Français)',
            'fr-CA-SylvieNeural': '🇨🇦 ♀️ Sylvie (Canadienne)',
            'fr-CA-JeanNeural': '🇨🇦 ♂️ Jean (Canadien)',
            'fr-CA-AntoineNeural': '🇨🇦 ♂️ Antoine (Canadien)',
            'fr-BE-CharlineNeural': '🇧🇪 ♀️ Charline (Belge)',
            'fr-BE-GerardNeural': '🇧🇪 ♂️ Gerard (Belge)',
            'fr-CH-FabriceNeural': '🇨🇭 ♂️ Fabrice (Suisse)',
            'fr-CH-ArianeNeural': '🇨🇭 ♀️ Ariane (Suisse)',

            # Voix espagnoles sud-américaines (FÉMININES)
            'es-AR-ElenaNeural': '🇦🇷 ♀️ Elena (Argentine)',
            'es-AR-TomasNeural': '🇦🇷 ♂️ Tomas (Argentin)',
            'es-CL-CatalinaNeural': '🇨🇱 ♀️ Catalina (Chilienne)',
            'es-CL-LorenzoNeural': '🇨🇱 ♂️ Lorenzo (Chilien)',
            'es-CO-SalomeNeural': '🇨🇴 ♀️ Salome (Colombienne)',
            'es-CO-GonzaloNeural': '🇨🇴 ♂️ Gonzalo (Colombien)',
            'es-MX-DaliaNeural': '🇲🇽 ♀️ Dalia (Mexicaine)',
            'es-MX-JorgeNeural': '🇲🇽 ♂️ Jorge (Mexicain)',
            'es-PE-CamilaNeural': '🇵🇪 ♀️ Camila (Péruvienne)',
            'es-PE-AlexNeural': '🇵🇪 ♂️ Alex (Péruvien)',
            'es-VE-PaolaNeural': '🇻🇪 ♀️ Paola (Vénézuélienne)',
            'es-VE-SebastianNeural': '🇻🇪 ♂️ Sebastian (Vénézuélien)',

            # Voix portugaises brésiliennes
            'pt-BR-FranciscaNeural': '🇧🇷 ♀️ Francisca (Brésilienne)',
            'pt-BR-AntonioNeural': '🇧🇷 ♂️ Antonio (Brésilien)',

            # Voix anglaises
            'en-US-AriaNeural': '🇺🇸 ♀️ Aria (US)',
            'en-US-GuyNeural': '🇺🇸 ♂️ Guy (US)',
            'en-US-JennyNeural': '🇺🇸 ♀️ Jenny (US)',
            'en-GB-LibbyNeural': '🇬🇧 ♀️ Libby (UK)',
            'en-GB-MaisieNeural': '🇬🇧 ♀️ Maisie (UK)',
            'en-GB-RyanNeural': '🇬🇧 ♂️ Ryan (UK)'
        }

        ui.select(
            label='Voix Microsoft Edge TTS',
            options=edge_voice_options,
            value=edge_voice,
            on_change=on_edge_voice_change
        ).classes('mb-3')

        # Bouton test Edge TTS
        def test_edge_tts_button():
            async def _test():
                _audio_manager = _get_global_var('_audio_manager')
                if _audio_manager:
                    test_text = "Bonjour, ceci est un test de Microsoft Edge TTS."
                    try:
                        success = await _audio_manager.speak_edge_tts(test_text, edge_voice)
                        if success:
                            _notify_safe('🔊 Test Edge TTS réussi', 'positive')
                        else:
                            _notify_safe('❌ Erreur test Edge TTS', 'negative')
                    except Exception as e:
                        _notify_safe(f'❌ Erreur Edge TTS: {str(e)}', 'negative')
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

        ui.button('🧪 Tester Microsoft Edge TTS', on_click=test_edge_tts_button).classes('mb-3')

        ui.label('💡 Microsoft Edge TTS - gratuit, haute qualité, 35+ voix (France, Sud-Amérique, Brésil)').classes('text-xs text-muted mb-3')

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
        ui.label('Vitesse de parole:').classes('text-sm w-32')
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