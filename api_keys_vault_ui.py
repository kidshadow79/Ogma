"""
UI Components for API Keys Vault
================================
Fournit l'Overlay (Modale) du Coffre-Fort et les composants d'indicateurs de statut.
"""
from nicegui import ui
import api_keys_vault
try:
    from utils.i18n import t
except ImportError:
    def t(key, **kwargs):
        return key

# Domaines logiques pour regrouper les clés dans l'UI
PROVIDER_CATEGORIES = {
    "Modèles IA (LLMs)": ["OpenAI", "Anthropic", "Mistral", "Google", "GROK", "AIHorde", "OpenRouter"],
    "Services Vocaux (Audio)": ["OpenAI_STT", "OpenAI_TTS", "Google_TTS", "ElevenLabs", "FishAudio", "Cartesia", "HumeAI", "Azure"],
    "Génération d'Images (Vision)": ["AtlasCloud", "Fal", "StabilityAI", "Midjourney", "Kie", "WaveSpeed"],
    "Services Externes": ["Serper", "Telegram", "OpenWeather"]
}

class VirtualKeyInput:
    """
    Objet virtuel qui simule un `ui.input` de NiceGUI.
    Permet aux anciennes fonctions backend qui faisaient `input.value`
    d'aller lire dynamiquement la clé depuis le vault sans casser le code existant.
    """
    def __init__(self, provider_getter):
        self.provider_getter = provider_getter
    
    @property
    def value(self):
        provider = self.provider_getter()
        if not provider or provider == 'Aucun':
            return ''
        # Mapping si nécessaire (ex: si le selecteur envoie juste 'Google' et que le backend s'attend à 'Google_TTS')
        return api_keys_vault.get_api_key(provider) or ''


def api_key_status_indicator(provider: str, label: str = None) -> ui.button:
    """
    Crée un bouton plat (badge interactif) indiquant si la clé existe pour le provider.
    Au clic, ouvre la modale du Coffre-Fort.
    
    Args:
        provider: Nom du provider dans le vault
        label: Label personnalisé. Si None, utilise le nom par défaut.
    """
    if label is None:
        label = f"Clé {provider}"
        
    has_key = api_keys_vault.has_saved_key(provider)
    
    color = "positive" if has_key else "warning"
    icon = "check_circle" if has_key else "warning"
    text = f"{label} : Configurée" if has_key else f"{label} : À renseigner"
    
    btn = ui.button(text, icon=icon, on_click=open_vault_modal)
    btn.props(f'flat color={color} size=sm no-caps')
    btn.classes('mb-2 ml-1')
    btn.tooltip('Clé renseignée dans le coffre-fort.' if has_key else 'Cliquez ici pour configurer la clé API de ce service.')
    
    return btn


def open_vault_modal():
    """
    Ouvre l'overlay centralisé (Dialog) pour gérer toutes les clés API.
    """
    with ui.dialog() as dialog, ui.card().style('min-width: 500px; max-width: 800px; max-height: 90vh;'):
        ui.label('🔐 Coffre-Fort API').classes('text-2xl font-bold mb-2')
        ui.label("Toutes vos clés sont gérées de manière centralisée. Lorsqu'un service a besoin d'une clé, il la cherchera automatiquement ici.").classes('text-sm text-gray-500 mb-4')
        
        with ui.tabs().classes('w-full') as tabs:
            tab_llm = ui.tab('IA Models', icon='psychology')
            tab_audio = ui.tab('Audio', icon='mic')
            tab_vision = ui.tab('Vision', icon='visibility')
            tab_services = ui.tab('Services', icon='language')
            
        with ui.scroll_area().classes('w-full flex-grow').style('max-height: 50vh;'):
            with ui.tab_panels(tabs, value=tab_llm).classes('w-full'):
                with ui.tab_panel(tab_llm):
                    _render_provider_inputs("Modèles IA (LLMs)")
                with ui.tab_panel(tab_audio):
                    _render_provider_inputs("Services Vocaux (Audio)")
                with ui.tab_panel(tab_vision):
                    _render_provider_inputs("Génération d'Images (Vision)")
                with ui.tab_panel(tab_services):
                    _render_provider_inputs("Services Externes")
                
        with ui.row().classes('w-full justify-end mt-4'):
            # Bouton fermer rechargera la page pour actualiser les badges de l'UI en dessous
            ui.button('Enregistrer & Fermer', on_click=lambda: (dialog.close(), ui.run_javascript('window.location.reload()'))).props('flat color=primary')
            
    dialog.open()


def _render_provider_inputs(category: str):
    """Génère les champs de saisie pour une catégorie spécifique"""
    providers = PROVIDER_CATEGORIES.get(category, [])
    for provider in providers:
        current_key = api_keys_vault.get_api_key(provider) or ""
        
        def update_key(e, p=provider):
            new_key = e.value.strip()
            if new_key:
                api_keys_vault.save_api_key(p, new_key)
            else:
                api_keys_vault.delete_api_key(p)
                
        with ui.row().classes('w-full items-center justify-between mb-2'):
            ui.label(provider).classes('font-medium w-1/3')
            inp = ui.input(value=current_key, password=True, password_toggle_button=True, on_change=update_key).classes('w-2/3')
            inp.props('outlined dense')
