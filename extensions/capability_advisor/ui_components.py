# 🎯 Capability Advisor - UI Components
"""
Interface utilisateur: Bouton header + Overlay LEDs + Modal config prompt
Pattern identique à Archi Sensor
"""

try:
    from nicegui import ui
    NICEGUI_AVAILABLE = True
except ImportError:
    NICEGUI_AVAILABLE = False
    print("[CAPABILITY-ADVISOR] ⚠️ NiceGUI non disponible")

try:
    from utils.i18n import t
except Exception:
    def t(key, **kwargs):
        return key

from .capability_catalog import CAPABILITIES
from .config import CapabilityAdvisorConfig
from .led_manager import LEDManager


class CapabilityAdvisorUI:
    """Composants UI Capability Advisor"""
    
    def __init__(self, led_manager: LEDManager, config: CapabilityAdvisorConfig):
        """
        Initialise composants UI
        
        Args:
            led_manager: Gestionnaire LEDs
            config: Configuration extension
        """
        self.led_manager = led_manager
        self.config = config
        self.overlay_dialog = None
        self.prompt_editor_dialog = None
        
        print(f"[CAPABILITY-ADVISOR] ✅ UI Components initialisés")
    
    def create_header_button(self):
        """
        Crée bouton header (à côté bouton Archi Sensor)
        Pattern identique aux boutons Biography/Journal
        """
        if not NICEGUI_AVAILABLE:
            print("[CAPABILITY-ADVISOR] ⚠️ NiceGUI non disponible, bouton header ignoré")
            return
        
        try:
            print("[CAPABILITY-ADVISOR] 🎨 Création bouton header...")
            
            # Créer l'overlay d'abord
            if self.overlay_dialog is None:
                self.create_overlay()
            
            # Créer le bouton avec le même style que Biography/Journal
            with ui.button().classes('capability-advisor-header-btn').props('title="Capability Advisor"').style(
                'width: 50px; height: 50px; border-radius: 50%; '
                'background: linear-gradient(135deg, #7C3AED 0%, #A855F7 100%); '
                'border: 2px solid #6D28D9; box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3); '
                'display: flex; align-items: center; justify-content: center; '
                'transition: all 0.3s ease; cursor: pointer; padding: 0; margin-right: 10px; '
                'flex-shrink: 0; min-width: 50px; min-height: 50px; max-width: 50px; max-height: 50px;'
            ) as advisor_btn:
                # Icône psychology (cerveau)
                ui.html('<span style="font-size: 22px; color: white;">🧠</span>')
                
                def toggle_overlay():
                    if self.overlay_dialog:
                        self.overlay_dialog.visible = not self.overlay_dialog.visible
                        print(f"[CAPABILITY-ADVISOR] Overlay {'affiché' if self.overlay_dialog.visible else 'masqué'}")
                
                advisor_btn.on('click', toggle_overlay)
            
            print("[CAPABILITY-ADVISOR] ✅ Bouton header créé")
            
        except Exception as e:
            print(f"[CAPABILITY-ADVISOR] ❌ Erreur création bouton header: {e}")
            import traceback
            traceback.print_exc()
    
    def create_overlay(self):
        """
        Crée overlay LEDs capacités
        Pattern identique à Archi Sensor overlay (ui.element fixe, pas ui.dialog)
        """
        if not NICEGUI_AVAILABLE:
            return
        
        # Créer overlay fixe à droite de l'écran (comme Archi Sensor)
        overlay_container = ui.element('div').classes('capability-advisor-overlay').style('''
            position: fixed;
            top: 80px;
            right: 20px;
            width: 230px;
            max-height: 90vh;
            overflow-y: auto;
            background: linear-gradient(145deg, #1a1a1a 0%, #2d2d2d 100%);
            border: 1px solid var(--border-default);
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.6);
            z-index: 50;
            padding: 16px;
        ''')
        
        # Commencer invisible
        overlay_container.visible = False
        
        with overlay_container:
            # Header overlay compact
            with ui.row().classes('items-center justify-between w-full mb-3'):
                ui.label(t('ca_label_capabilities')).classes('text-sm font-bold').style('color: var(--text-primary);')
                
                # Icône paramètres pour éditer prompt Archiviste
                with ui.button(
                    icon='settings', 
                    on_click=lambda: self.open_prompt_editor()
                ).classes('').props('flat dense round').style('padding: 4px;'):
                    ui.tooltip(t('ca_tooltip_config'))
            
            ui.separator().classes('mb-2')
            
            # Liste verticale des 6 capacités (une colonne)
            with ui.column().classes('w-full gap-2'):
                for cap_id, cap_info in CAPABILITIES.items():
                    self._create_led_card(cap_id, cap_info)
            
            ui.separator().classes('mt-3')
            
            # Bouton fermer compact
            ui.button(t('ca_btn_close'), on_click=lambda: setattr(overlay_container, 'visible', False)).classes('w-full').props('flat dense size=sm')
        
        self.overlay_dialog = overlay_container
        print("[CAPABILITY-ADVISOR] ✅ Overlay container créé")
    
    def _create_led_card(self, cap_id: str, cap_info: dict):
        """
        Crée carte LED pour une capacité (version compacte verticale)
        
        Args:
            cap_id: ID capacité
            cap_info: Infos capacité
        """
        with ui.row().classes('items-center gap-2 w-full p-1 flex-nowrap').style('background: rgba(255,255,255,0.02); border-radius: 6px;'):
            # LED visuelle (sans style inline background pour permettre CSS classes)
            led_indicator = ui.element('div').classes('led-indicator led-off').style(
                'width: 14px; height: 14px; border-radius: 50%; flex-shrink: 0;'
            )
            
            # Enregistrer élément UI dans led_manager
            self.led_manager.led_ui_elements[cap_id] = led_indicator
            
            # Nom capacité compact
            cap_name = t(f'ca_cap_{cap_id}')
            if cap_name == f'ca_cap_{cap_id}':
                cap_name = cap_info['name']
            ui.label(cap_name).classes('text-xs font-medium').style('color: var(--text-primary); line-height: 1.2; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex: 1; min-width: 0;')
    
    def create_prompt_editor_modal(self):
        """Crée modal édition prompt Archiviste + IDs mémoire"""
        if not NICEGUI_AVAILABLE:
            return
        
        # Récupération prompt actuel
        current_prompt = self.config.get_advisor_prompt_template()
        
        with ui.dialog() as prompt_modal:
            with ui.card().style('width: 900px; max-width: 95vw; max-height: 90vh; overflow-y: auto;'):
                ui.label(t('ca_modal_title')).classes('text-lg font-bold mb-2')
                ui.separator()
                
                # ======== SECTION 1: PROMPT ARCHIVISTE ========
                ui.label(t('ca_section_prompt')).classes('text-md font-semibold mt-4')
                
                # Zone édition prompt avec style visible
                prompt_area = ui.textarea(
                    label=t('ca_label_prompt_system'),
                    value=current_prompt,
                    placeholder=t('ca_placeholder_prompt')
                ).classes('w-full').props('rows=12 outlined').style(
                    'color: white !important; '
                    'background-color: #2a2a2a !important;'
                )
                
                # Variables disponibles
                ui.label(t('ca_label_variables')).classes('text-sm font-semibold mt-2')
                with ui.column().classes('text-xs text-gray-400 ml-4 gap-1'):
                    ui.label(t('ca_var_user_message'))
                    ui.label(t('ca_var_recent_context'))
                    ui.label(t('ca_var_capabilities'))
                
                ui.separator().classes('my-4')
                
                # ======== SECTION 2: ACTIVATION EXTENSION ========
                ui.label(t('ca_section_activation')).classes('text-md font-semibold')
                ui.label(t('ca_section_activation_help')).classes('text-caption mb-2')
                
                with ui.row().classes('items-center gap-3 mb-4'):
                    is_currently_enabled = self.config.is_enabled()
                    
                    enable_switch = ui.switch(
                        t('ca_label_extension_enabled'),
                        value=is_currently_enabled
                    ).classes('text-base')
                    
                    ui.label(t('ca_label_disabled_note')).classes('text-caption text-muted')
                
                ui.separator().classes('my-4')
                
                # ======== SECTION 2: SEUILS CONFIANCE ========
                ui.label(t('ca_section_thresholds')).classes('text-md font-semibold')
                ui.label(t('ca_section_thresholds_help')).classes('text-xs text-gray-400 mb-2')
                
                # Récupérer seuils actuels
                current_thresholds = self.config.get_capability_thresholds()
                threshold_inputs = {}
                
                # Grille 2 colonnes pour 6 capacités
                with ui.grid(columns=2).classes('w-full gap-3'):
                    for cap_id, cap_info in CAPABILITIES.items():
                        default_threshold = cap_info.get('confidence_threshold', 0.70)
                        custom_threshold = current_thresholds.get(cap_id, None)
                        
                        with ui.column().classes('gap-1'):
                            cap_label = t(f'ca_cap_{cap_id}')
                            if cap_label == f'ca_cap_{cap_id}':
                                cap_label = cap_info['name']
                            ui.label(f"{cap_info['icon']} {cap_label}").classes('text-sm font-medium')
                            
                            threshold_input = ui.number(
                                label=t('ca_label_threshold', value=default_threshold),
                                value=custom_threshold if custom_threshold is not None else default_threshold,
                                min=0.0,
                                max=1.0,
                                step=0.05,
                                format='%.2f'
                            ).classes('w-full').props('outlined dense')
                            
                            # Note explicative
                            status_text = t('ca_status_active', value=custom_threshold) if custom_threshold is not None else t('ca_status_default', value=default_threshold)
                            ui.label(status_text).classes('text-xs text-gray-500')
                            
                            threshold_inputs[cap_id] = threshold_input
                
                ui.separator().classes('my-4')
                
                # Boutons actions
                with ui.row().classes('justify-between w-full'):
                    # Gauche: Reset
                    with ui.row().classes('gap-2'):
                        ui.button(
                            t('ca_btn_reset_prompt'), 
                            on_click=lambda: self._reset_prompt(prompt_area, prompt_modal)
                        ).props('flat color=warning size=sm')
                        
                        ui.button(
                            t('ca_btn_reset_ids'), 
                            on_click=lambda: self._reset_memory_ids(memory_id_inputs)
                        ).props('flat color=warning size=sm')
                        
                        ui.button(
                            t('ca_btn_reset_thresholds'), 
                            on_click=lambda: self._reset_thresholds(threshold_inputs)
                        ).props('flat color=warning size=sm')
                    
                    # Droite: Annuler/Enregistrer
                    with ui.row().classes('gap-2'):
                        ui.button(t('common_cancel'), on_click=prompt_modal.close).props('flat')
                        
                        ui.button(
                            t('ca_btn_save_all'), 
                            on_click=lambda: self._save_all_config(prompt_area.value, threshold_inputs, enable_switch, prompt_modal)
                        ).classes('bg-primary')
        
        self.prompt_editor_dialog = prompt_modal
    
    def _reset_prompt(self, prompt_area, modal):
        """Réinitialise prompt au défaut"""
        self.config.reset_to_default_prompt()
        prompt_area.value = self.config.get_advisor_prompt_template()
        ui.notify(t('ca_notify_prompt_reset'), type='info')
    
    def _reset_thresholds(self, threshold_inputs: dict):
        """Réinitialise seuils aux valeurs par défaut du catalog"""
        self.config.reset_capability_thresholds()
        
        # Mettre à jour UI inputs avec valeurs catalog
        for cap_id, input_widget in threshold_inputs.items():
            cap_info = CAPABILITIES.get(cap_id, {})
            default_threshold = cap_info.get('confidence_threshold', 0.70)
            input_widget.value = default_threshold
        
        ui.notify(t('ca_notify_thresh_reset'), type='info')
    
    def _save_prompt(self, prompt_text: str, modal):
        """Sauvegarde prompt personnalisé"""
        if not prompt_text.strip():
            ui.notify(t('ca_notify_empty_prompt'), type='warning')
            return
        
        self.config.save_custom_prompt(prompt_text)
        ui.notify(t('ca_notify_prompt_saved'), type='positive')
        modal.close()
    
    def _save_all_config(self, prompt_text: str, threshold_inputs: dict, enable_switch, modal):
        """Sauvegarde prompt + Seuils confiance + Activation"""
        # Valider prompt
        if not prompt_text.strip():
            ui.notify(t('ca_notify_empty_prompt_neg'), type='negative')
            return
        
        # Extraire seuils depuis inputs
        thresholds = {}
        for cap_id, input_widget in threshold_inputs.items():
            threshold_value = input_widget.value
            if threshold_value is not None:
                thresholds[cap_id] = threshold_value
        
        # Sauvegarder prompt
        self.config.save_custom_prompt(prompt_text)
        
        # Sauvegarder seuils
        self.config.save_capability_thresholds(thresholds)
        
        # Sauvegarder état activation
        self.config.set_enabled(enable_switch.value)
        
        ui.notify(t('ca_notify_full_saved'), type='positive')
        modal.close()
    
    def open_overlay(self):
        """Ouvre overlay LEDs"""
        if self.overlay_dialog is None:
            self.create_overlay()
        
        self.overlay_dialog.open()
    
    def open_prompt_editor(self):
        """Ouvre modal édition prompt"""
        if self.prompt_editor_dialog is None:
            self.create_prompt_editor_modal()
        
        self.prompt_editor_dialog.open()
    
    def inject_css_styles(self):
        """
        Injecte styles CSS LEDs dans page
        À appeler depuis ogma_ng.py après ui.run()
        """
        if not NICEGUI_AVAILABLE:
            return
        
        ui.add_head_html("""
<style>
/* Capability Advisor - LEDs Animations */
.led-indicator {
    width: 14px;
    height: 14px;
    border-radius: 50%;
    transition: all 0.3s ease;
    flex-shrink: 0;
}

.led-off {
    background-color: #444 !important;
    box-shadow: 0 0 5px rgba(0,0,0,0.3) !important;
}

.led-on {
    background-color: #FF9800 !important;
    box-shadow: 0 0 15px rgba(255, 152, 0, 0.9),
                0 0 30px rgba(255, 152, 0, 0.6),
                0 0 45px rgba(255, 152, 0, 0.3) !important;
    animation: pulse-led 1.5s infinite !important;
    filter: brightness(1.2) !important;
}

@keyframes pulse-led {
    0%, 100% { 
        opacity: 1; 
        transform: scale(1);
    }
    50% { 
        opacity: 1.0;
        transform: scale(1.08);
    }
}

.capability-led-card {
    border-radius: 8px;
    transition: background 0.2s ease;
}

.capability-led-card:hover {
    background: rgba(255,255,255,0.08) !important;
}

.capability-advisor-btn {
    transition: all 0.2s ease;
}

.capability-advisor-btn:hover {
    background: rgba(255,255,255,0.1) !important;
}

.capability-advisor-overlay {
    background: rgb(30, 30, 30);
    border-radius: 12px;
}

/* ── Thème Clarté : corrections overlay Capability Advisor ── */
body[data-ogma-theme="light"] .capability-advisor-overlay {
    background: rgba(245, 245, 252, 0.97) !important;
    border: 1px solid rgba(0, 0, 0, 0.15) !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15) !important;
}

/* LEDs : annuler opacity 0.3 hérité des jauges audio en thème Clarté */
body[data-ogma-theme="light"] .capability-advisor-overlay .led-indicator {
    opacity: 0.85 !important;
    border: 1px solid rgba(90, 90, 90, 0.5) !important;
}

/* LED éteinte visible sur fond clair */
body[data-ogma-theme="light"] .capability-advisor-overlay .led-off {
    background-color: #888 !important;
    background: #888 !important;
    box-shadow: none !important;
}
</style>
        """)
