"""Interface utilisateur pour l'extension Text2Image"""

from nicegui import ui
from pathlib import Path
import json

class Text2ImageUI:
    """Composants UI pour la gestion de la génération d'images"""

    def __init__(self, text2img_manager):
        self.manager = text2img_manager

    def render_settings_panel(self):
        """Affiche le panneau de configuration avancée"""
        with ui.card().classes('q-dark p-4').style('background: rgba(255,255,255,0.05);'):
            ui.label('⚙️ Paramètres Avancés').classes('font-semibold mb-3')

            # Récupérer settings actuels
            settings = self.manager.settings_manager.settings.get('text2img', {})

            with ui.column().classes('gap-3 w-full'):
                # Backend selection
                with ui.row().classes('gap-2 items-center'):
                    ui.label('Backend:').classes('text-sm')
                    backend_select = ui.select(
                        options=['perchance', 'fal.ai', 'comfyui'],
                        value=settings.get('backend', 'perchance')
                    ).classes('flex-1')

                # Guidance scale
                with ui.row().classes('gap-2 items-center'):
                    ui.label('Guidance Scale:').classes('text-sm')
                    guidance_slider = ui.slider(
                        min=1,
                        max=20,
                        step=0.5,
                        value=settings.get('guidance_scale', 7.5)
                    ).classes('flex-1')
                    guidance_value = ui.label(f"{settings.get('guidance_scale', 7.5)}").classes('text-sm')
                    guidance_slider.on('update:model-value', lambda e: guidance_value.set_text(f"{e.args:.1f}"))

                # Steps
                with ui.row().classes('gap-2 items-center'):
                    ui.label('Steps:').classes('text-sm')
                    steps_input = ui.number(
                        value=settings.get('steps', 30),
                        min=10,
                        max=100,
                        step=5
                    ).classes('flex-1')

                # Negative prompt
                ui.label('Negative Prompt:').classes('text-sm')
                negative_prompt = ui.textarea(
                    value=settings.get('negative_prompt', 'blurry, low quality, distorted'),
                    placeholder='Elements to avoid in generation...'
                ).classes('w-full')

                # Seed
                with ui.row().classes('gap-2 items-center'):
                    ui.label('Seed (optional):').classes('text-sm')
                    seed_input = ui.number(
                        value=settings.get('seed', None),
                        placeholder='Random if empty'
                    ).classes('flex-1')

            def save_advanced_settings():
                """Sauvegarde les paramètres avancés"""
                new_settings = {
                    'backend': backend_select.value,
                    'guidance_scale': guidance_slider.value,
                    'steps': int(steps_input.value),
                    'negative_prompt': negative_prompt.value,
                    'seed': int(seed_input.value) if seed_input.value else None
                }

                # Merger avec settings existants
                current = self.manager.settings_manager.settings.get('text2img', {})
                current.update(new_settings)
                self.manager.settings_manager.settings['text2img'] = current
                self.manager.settings_manager.save_settings()

                ui.notify('✅ Paramètres avancés sauvegardés', type='positive')

            ui.button('Sauvegarder paramètres avancés', on_click=save_advanced_settings).classes('primary-action-button mt-3')

    def render_history_panel(self):
        """Affiche l'historique des générations"""
        history_file = Path('data/generation_history.json')

        with ui.card().classes('q-dark p-4').style('background: rgba(255,255,255,0.05);'):
            ui.label('📜 Historique des Générations').classes('font-semibold mb-3')

            if not history_file.exists():
                ui.label('Aucune génération enregistrée').classes('text-sm text-gray-400')
                return

            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)

                if not history:
                    ui.label('Aucune génération enregistrée').classes('text-sm text-gray-400')
                    return

                # Afficher les 10 dernières générations
                for entry in reversed(history[-10:]):
                    with ui.card().classes('q-dark p-3 mb-2').style('background: rgba(255,255,255,0.03);'):
                        with ui.row().classes('gap-3 items-center'):
                            # Miniature
                            if Path(entry['filepath']).exists():
                                ui.image(entry['filepath']).classes('w-16 h-16 rounded')

                            # Info
                            with ui.column().classes('flex-1'):
                                ui.label(entry['prompt']).classes('text-sm font-medium')
                                ui.label(f"📅 {entry['timestamp']}").classes('text-xs text-gray-400')
                                ui.label(f"⚙️ {entry['width']}×{entry['height']} | {entry.get('backend', 'perchance')}").classes('text-xs text-gray-400')

            except Exception as e:
                ui.label(f'Erreur chargement historique: {e}').classes('text-sm text-red-400')
