# 🧠 Introspection v2.1 - Interface Paramètres Simplifiée

"""
Interface paramètres Introspection v2.1

AMÉLIORATIONS:
- 3 onglets compacts (au lieu de scroll infini)
- Bouton "Restaurer défaut" pour chaque instruction
- Affichage tokens configurables par étape
- Indicateur de progression visuel
"""

from typing import Optional, Callable, Dict, Any
import traceback

try:
    from utils.i18n import t
except Exception:
    def t(key, **kwargs):
        return key

try:
    from nicegui import ui
    NICEGUI_AVAILABLE = True
except ImportError:
    NICEGUI_AVAILABLE = False
    class MockUI:
        def __getattr__(self, name):
            return lambda *args, **kwargs: None
    ui = MockUI()

from .config_v2 import get_introspection_config, IntrospectionConfigV2


class IntrospectionParametersUI:
    """
    Interface paramètres Introspection v2.1
    
    3 onglets:
    1. Configuration Générale
    2. Instructions (3 étapes)
    3. Paramètres Avancés
    """
    
    def __init__(
        self,
        on_toggle_callback: Callable = None,
        on_settings_change: Callable = None
    ):
        """
        Initialise interface
        
        Args:
            on_toggle_callback: Callback(new_state) pour ON/OFF
            on_settings_change: Callback(key, value) pour changements
        """
        self.config = get_introspection_config()
        self.on_toggle = on_toggle_callback
        self.on_change = on_settings_change
        
        # Références UI
        self.dialog = None
        self.ui_controls = {}
        
        print("[INTROSPECTION-UI] 🎨 Interface v2.1 initialisée")
    
    def create_popup(self):
        """Crée le popup paramètres avec onglets"""
        if not NICEGUI_AVAILABLE:
            print("[INTROSPECTION-UI] ❌ NiceGUI non disponible")
            return None
        
        with ui.dialog().props('persistent maximized') as dialog:
            self.dialog = dialog
            
            with ui.card().style('''
                width: 900px; 
                max-height: 90vh; 
                overflow: hidden;
                background: #1f2937; 
                border-radius: 12px;
                padding: 0;
            '''):
                # Header
                self._create_header()
                
                # Onglets
                with ui.tabs().classes('w-full').style('background: #374151;') as tabs:
                    tab_general = ui.tab(t('cm_tab_general'), icon='settings')
                    tab_instructions = ui.tab(t('cm_tab_instructions'), icon='edit_note')
                    tab_advanced = ui.tab(t('cm_tab_advanced'), icon='tune')
                
                with ui.tab_panels(tabs, value=tab_general).classes('w-full').style('''
                    background: #1f2937;
                    max-height: calc(90vh - 180px);
                    overflow-y: auto;
                '''):
                    # Onglet 1: Configuration Générale
                    with ui.tab_panel(tab_general).style('padding: 24px;'):
                        self._create_general_tab()
                    
                    # Onglet 2: Instructions
                    with ui.tab_panel(tab_instructions).style('padding: 24px;'):
                        self._create_instructions_tab()
                    
                    # Onglet 3: Paramètres Avancés
                    with ui.tab_panel(tab_advanced).style('padding: 24px;'):
                        self._create_advanced_tab()
                
                # Footer avec boutons
                self._create_footer()
        
        print("[INTROSPECTION-UI] ✅ Popup créé")
        return dialog
    
    def _create_header(self):
        """Header du popup"""
        with ui.row().classes('w-full items-center').style('''
            background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
            padding: 20px 24px;
            border-radius: 12px 12px 0 0;
        '''):
            ui.icon('psychology', size='32px').style('color: white;')
            ui.label(t('cm_v2_title')).style('''
                font-size: 24px;
                font-weight: 600;
                color: white;
                margin-left: 12px;
            ''')
            ui.space()
            ui.label(t('cm_v2_subtitle')).style('''
                color: rgba(255,255,255,0.7);
                font-style: italic;
            ''')
    
    def _create_general_tab(self):
        """Onglet Configuration Générale"""
        
        # Section ON/OFF
        self._section_title(t('cm_v2_section_activation'), '#3b82f6')
        
        with ui.row().classes('w-full items-center gap-4').style('margin-bottom: 24px;'):
            current_state = self.config.is_enabled()
            
            self.ui_controls['enabled'] = ui.switch(
                value=current_state,
                on_change=self._on_toggle_changed
            ).props('color=primary size=lg').tooltip(t('cm_v2_tooltip_enabled'))
            
            with ui.column().classes('gap-1'):
                ui.label(t('cm_v2_label_ext')).style('font-weight: 600; color: #e5e7eb;')
                ui.label(
                    t('cm_v2_state_enabled') if current_state 
                    else t('cm_v2_state_disabled')
                ).style('color: #9ca3af; font-size: 14px;')
        
        # Section Mode
        self._section_title(t('cm_v2_section_mode'), '#8b5cf6')
        
        current_mode = self.config.get_introspection_mode()
        
        with ui.column().classes('gap-3').style('margin-bottom: 24px;'):
            # Migration: ancienne valeur 'always' → 'autonomous'
            if current_mode == 'always':
                current_mode = 'autonomous'
                self.config.set('introspection_mode', 'autonomous')
            self.ui_controls['mode'] = ui.radio(
                options={
                    'on_demand': t('cm_v2_option_on_demand'),
                    'autonomous': t('cm_v2_option_autonomous')
                },
                value=current_mode,
                on_change=self._on_mode_changed
            ).props('inline').style('color: #e5e7eb;').tooltip(
                t('cm_v2_tooltip_mode')
            )
            
            ui.label(
                t('cm_v2_hint_mode')
            ).style('color: #9ca3af; font-size: 13px; margin-left: 8px;')
        
        # Section Phrases Magiques (lecture seule pour référence)
        self._section_title(t('cm_v2_section_magic_phrases'), "#10b981")
        
        with ui.card().style('background: rgba(16, 185, 129, 0.1); padding: 24px; border-radius: 8px; min-height: 120px;'):
            phrases = self.config.get_magic_phrases("user_trigger")
            ui.label(t('cm_v2_prefix_trigger') + ', '.join(f'"{p}"' for p in phrases)).style(
                'color: #9ca3af; font-size: 14px; line-height: 1.8;'
            )
            
            stop_phrases = self.config.get_magic_phrases("user_stop")
            ui.label(t('cm_v2_prefix_stop') + ', '.join(f'"{p}"' for p in stop_phrases)).style(
                'color: #9ca3af; font-size: 14px; margin-top: 12px; line-height: 1.8;'
            )
    
    def _create_instructions_tab(self):
        """Onglet Instructions avec boutons restauration"""
        
        ui.label(t('cm_v2_subtitle_steps')).style(
            'color: #9ca3af; margin-bottom: 20px;'
        )
        
        # Étape 1: Ouverture
        self._create_instruction_editor(
            step_key="step1_analysis",
            title=t('cm_v2_step_opening'),
            description=t('cm_v2_step_opening_desc'),
            color="#3b82f6"
        )
        
        # IA Principale (joute)
        self._create_instruction_editor(
            step_key="step2_conscious",
            title=t('cm_v2_step_main_ai'),
            description=t('cm_v2_step_main_ai_desc'),
            color="#8b5cf6"
        )
        
        # Archiviste (confronteur)
        self._create_instruction_editor(
            step_key="step2_unconscious",
            title=t('cm_v2_step_archivist'),
            description=t('cm_v2_step_archivist_desc'),
            color="#f59e0b"
        )
        
        # Étape 3: Synthèse
        self._create_instruction_editor(
            step_key="step3_synthesis",
            title=t('cm_v2_step_synthesis'),
            description=t('cm_v2_step_synthesis_desc'),
            color="#10b981"
        )
        
        # Bouton restaurer tout
        with ui.row().classes('w-full justify-center').style('margin-top: 24px;'):
            ui.button(
                t('cm_v2_btn_restore_all'),
                on_click=self._restore_all_instructions
            ).props('flat color=warning')
    
    def _create_instruction_editor(
        self,
        step_key: str,
        title: str,
        description: str,
        color: str
    ):
        """Crée un éditeur d'instruction avec bouton restauration"""
        
        instruction_data = self.config.get_instruction(step_key)
        current_text = instruction_data.get("instruction", "")
        
        # Lire tokens depuis current_settings (source de vérité) et non instruction_data
        token_key_map = {
            "step1_analysis": "step1_max_tokens",
            "step2_conscious": "step2_conscious_max_tokens",
            "step2_unconscious": "step2_unconscious_max_tokens",
            "step3_synthesis": "step3_max_tokens"
        }
        setting_key = token_key_map.get(step_key, f"{step_key}_max_tokens")
        default_tokens = self.config.get(setting_key, instruction_data.get("default_tokens", 500))
        
        with ui.card().style(f'''
            background: rgba(55, 65, 81, 0.3);
            border-left: 3px solid {color};
            padding: 16px;
            margin-bottom: 16px;
            border-radius: 8px;
            min-height: 500px;
        '''):
            # Header avec titre + tokens + bouton restaurer
            with ui.row().classes('w-full items-center justify-between').style('margin-bottom: 12px;'):
                with ui.column().classes('gap-1'):
                    ui.label(title).style(f'color: {color}; font-weight: 600; font-size: 16px;')
                    ui.label(description).style('color: #9ca3af; font-size: 13px;')
                
                with ui.row().classes('items-center gap-2'):
                    # Mots configurables
                    ui.label(t('cm_v2_label_words')).style('color: #9ca3af; font-size: 13px;')
                    token_input = ui.number(
                        value=default_tokens,
                        min=100,
                        max=2000,
                        step=100,
                        on_change=lambda e, k=step_key: self._on_tokens_changed(k, e.value)
                    ).props('dense outlined dark').style('width: 80px;').tooltip(t('cm_v2_tooltip_tokens'))
                    self.ui_controls[f'{step_key}_tokens'] = token_input
                    
                    # Bouton restaurer
                    ui.button(
                        icon='restore',
                        on_click=lambda k=step_key: self._restore_instruction(k)
                    ).props('flat dense color=warning').tooltip(t('cm_v2_tooltip_restore'))
            
            # Textarea instruction — dans un column qui force la hauteur
            with ui.column().style('width: 100%; min-height: 400px;'):
                self.ui_controls[step_key] = ui.textarea(
                    value=current_text,
                    on_change=lambda e, k=step_key: self._on_instruction_changed(k, e.value)
                ).props('outlined dark').classes('w-full').style('min-height: 380px;')
    
    def _create_advanced_tab(self):
        """Onglet Paramètres Avancés"""
        
        # Dialogue
        self._section_title(t('cm_v2_section_dialogue'), '#8b5cf6')
        
        with ui.row().classes('gap-6').style('margin-bottom: 24px;'):
            with ui.column().classes('gap-2'):
                ui.label(t('cm_v2_label_min_exchanges')).style('color: #e5e7eb;')
                self.ui_controls['min_exchanges'] = ui.number(
                    value=self.config.get("min_dialogue_exchanges", 2),
                    min=1,
                    max=8,
                    on_change=lambda e: self._on_setting_changed("min_dialogue_exchanges", e.value)
                ).props('outlined dark dense').style('width: 100px;').tooltip(t('cm_v2_tooltip_min_exchanges'))

            with ui.column().classes('gap-2'):
                ui.label(t('cm_v2_label_max_exchanges')).style('color: #e5e7eb;')
                self.ui_controls['max_exchanges'] = ui.number(
                    value=self.config.get("max_dialogue_exchanges", 6),
                    min=2,
                    max=10,
                    on_change=lambda e: self._on_setting_changed("max_dialogue_exchanges", e.value)
                ).props('outlined dark dense').style('width: 100px;').tooltip(t('cm_v2_tooltip_max_exchanges'))
            
            with ui.column().classes('gap-2'):
                ui.label(t('cm_v2_label_timeout')).style('color: #e5e7eb;')
                self.ui_controls['timeout'] = ui.number(
                    value=self.config.get("max_introspection_duration", 120),
                    min=30,
                    max=600,
                    step=30,
                    on_change=lambda e: self._on_setting_changed("max_introspection_duration", e.value)
                ).props('outlined dark dense').style('width: 100px;').tooltip(t('cm_v2_tooltip_timeout'))
        
        # Mémoire
        self._section_title(t('cm_v2_section_memory'), '#10b981')
        
        with ui.row().classes('gap-6').style('margin-bottom: 24px;'):
            with ui.column().classes('gap-2'):
                with ui.row().classes('items-center gap-1'):
                    ui.label(t('cm_v2_label_similarity')).style('color: var(--text-primary, #e5e7eb);')
                    ui.icon('help_outline', size='16px').style('color: #9ca3af; cursor: help;').tooltip(t('cm_v2_tooltip_similarity'))
                with ui.row().classes('items-center gap-2'):
                    initial_mem = self.config.get("memory_search_threshold", 0.5)
                    mem_label = ui.label(str(initial_mem)).style(
                        'color: #e5e7eb; font-weight: 600; font-size: 14px; min-width: 32px; text-align: center;'
                    )
                    def _on_mem_change(e, lbl=mem_label):
                        lbl.set_text(str(round(e.value, 1)))
                        self._on_setting_changed("memory_search_threshold", e.value)
                    self.ui_controls['memory_threshold'] = ui.slider(
                        value=initial_mem,
                        min=0.1,
                        max=0.9,
                        step=0.1,
                        on_change=_on_mem_change
                    ).style('width: 200px;')
        
        # Sauvegarde
        self._section_title(t('cm_v2_section_autosave'), '#f59e0b')
        
        with ui.column().classes('gap-4').style('margin-bottom: 24px;'):
            self.ui_controls['auto_save'] = ui.switch(
                t('cm_v2_switch_autosave'),
                value=self.config.get("auto_save_enabled", False),
                on_change=lambda e: self._on_setting_changed("auto_save_enabled", e.value)
            ).style('color: #e5e7eb;').tooltip(t('cm_v2_tooltip_autosave'))
            
            with ui.row().classes('items-center gap-2'):
                with ui.row().classes('items-center gap-1'):
                    ui.label(t('cm_v2_label_importance')).style('color: #e5e7eb;')
                    ui.icon('help_outline', size='16px').style('color: #9ca3af; cursor: help;').tooltip(t('cm_v2_tooltip_importance_long'))
                initial_imp = self.config.get("importance_threshold", 6)
                imp_label = ui.label(str(initial_imp)).style(
                    'color: #e5e7eb; font-weight: 600; font-size: 14px; min-width: 32px; text-align: center;'
                )
                def _on_imp_change(e, lbl=imp_label):
                    lbl.set_text(str(int(e.value)))
                    self._on_setting_changed("importance_threshold", e.value)
                self.ui_controls['importance_threshold'] = ui.slider(
                    value=initial_imp,
                    min=1,
                    max=10,
                    step=1,
                    on_change=_on_imp_change
                ).style('width: 200px;')
        
        # Affichage
        self._section_title(t('cm_v2_section_display'), '#3b82f6')
        
        with ui.column().classes('gap-2'):
            self.ui_controls['show_dialogue'] = ui.switch(
                t('cm_v2_switch_show_dialogue'),
                value=self.config.get("show_dialogue_details", True),
                on_change=lambda e: self._on_setting_changed("show_dialogue_details", e.value)
            ).style('color: #e5e7eb;').tooltip(t('cm_v2_tooltip_show_dialogue'))
            
            self.ui_controls['show_progress'] = ui.switch(
                t('cm_v2_switch_show_progress'),
                value=self.config.get("show_progress_indicator", True),
                on_change=lambda e: self._on_setting_changed("show_progress_indicator", e.value)
            ).style('color: #e5e7eb;').tooltip(t('cm_v2_tooltip_show_progress'))
            
            self.ui_controls['typing_anim'] = ui.switch(
                t('cm_v2_switch_typing'),
                value=self.config.get("typing_animation", True),
                on_change=lambda e: self._on_setting_changed("typing_animation", e.value)
            ).style('color: #e5e7eb;').tooltip(t('cm_v2_tooltip_typing'))
    
    def _create_footer(self):
        """Footer avec boutons action"""
        with ui.row().classes('w-full justify-between items-center').style('''
            padding: 16px 24px;
            background: #374151;
            border-radius: 0 0 12px 12px;
        '''):
            ui.button(
                t('cm_v2_btn_restore_defaults'),
                on_click=self._restore_all_defaults
            ).props('flat color=warning')
            
            with ui.row().classes('gap-2'):
                ui.button(t('common_cancel'), on_click=self._close).props('flat color=grey')
                ui.button(t('common_apply'), on_click=self._apply_and_close).props('color=primary')
    
    def _section_title(self, title: str, color: str):
        """Titre de section stylisé"""
        ui.label(title).style(f'''
            color: {color};
            font-size: 18px;
            font-weight: 600;
            margin: 16px 0 12px 0;
            padding-bottom: 8px;
            border-bottom: 2px solid {color}30;
        ''')
    
    # =========================================================================
    # CALLBACKS
    # =========================================================================
    
    def _on_toggle_changed(self, e):
        """Toggle ON/OFF"""
        new_state = e.value
        self.config.set("extension_enabled", new_state)
        if self.on_toggle:
            self.on_toggle(new_state)
        ui.notify(t('cm_v2_notify_state_on') if new_state else t('cm_v2_notify_state_off'), type='info')
    
    def _on_mode_changed(self, e):
        """Changement mode"""
        self.config.set("introspection_mode", e.value)
        if self.on_change:
            self.on_change("introspection_mode", e.value)
    
    def _on_setting_changed(self, key: str, value):
        """Changement paramètre générique"""
        self.config.set(key, value)
        if self.on_change:
            self.on_change(key, value)
    
    def _on_instruction_changed(self, step_key: str, new_text: str):
        """Changement instruction"""
        self.config.set_instruction(step_key, new_text)
    
    def _on_tokens_changed(self, step_key: str, new_value: int):
        """Changement tokens pour une étape"""
        setting_key = f"{step_key}_max_tokens"
        # Convertir step_key en setting_key approprié
        if step_key == "step1_analysis":
            setting_key = "step1_max_tokens"
        elif step_key == "step2_conscious":
            setting_key = "step2_conscious_max_tokens"
        elif step_key == "step2_unconscious":
            setting_key = "step2_unconscious_max_tokens"
        elif step_key == "step3_synthesis":
            setting_key = "step3_max_tokens"
        
        self.config.set(setting_key, int(new_value))
        # Synchroniser aussi dans current_instructions pour cohérence
        if step_key in self.config.current_instructions:
            self.config.current_instructions[step_key]["default_tokens"] = int(new_value)
    
    def _restore_instruction(self, step_key: str):
        """Restaure une instruction par défaut"""
        success = self.config.reset_instruction_to_default(step_key)
        if success:
            # Mettre à jour le textarea
            new_text = self.config.get_instruction_text(step_key)
            if step_key in self.ui_controls:
                self.ui_controls[step_key].value = new_text
            ui.notify(t('cm_v2_notify_instr_restored'), type='positive')
        else:
            ui.notify(t('cm_v2_notify_restore_err'), type='negative')
    
    def _restore_all_instructions(self):
        """Restaure toutes les instructions"""
        for step_key in ["step1_analysis", "step2_conscious", "step2_unconscious", "step3_synthesis"]:
            self.config.reset_instruction_to_default(step_key)
            if step_key in self.ui_controls:
                self.ui_controls[step_key].value = self.config.get_instruction_text(step_key)
        ui.notify(t('cm_v2_notify_all_restored'), type='positive')
    
    def _restore_all_defaults(self):
        """Restaure TOUT par défaut"""
        self.config.reset_all_to_default()
        ui.notify(t('cm_v2_notify_full_restored'), type='positive')
        # Fermer et rouvrir pour rafraîchir
        self._close()
    
    def _close(self):
        """Ferme le popup"""
        if self.dialog:
            self.dialog.close()
    
    def _apply_and_close(self):
        """Applique et ferme"""
        self.config.save_config()
        ui.notify(t('cm_v2_notify_saved'), type='positive')
        self._close()
    
    # =========================================================================
    # API PUBLIQUE
    # =========================================================================
    
    def show(self):
        """Affiche le popup"""
        if self.dialog:
            self.dialog.open()
            # Injecte un <style> dans le DOM — s'applique aux textareas même créés plus tard (changement d'onglet)
            ui.run_javascript('''
                if (!document.getElementById("ogma-textarea-fix")) {
                    const style = document.createElement("style");
                    style.id = "ogma-textarea-fix";
                    style.textContent = `
                        .q-dialog textarea,
                        .q-dialog .q-field__native[rows] {
                            min-height: 420px !important;
                            height: 420px !important;
                            resize: vertical !important;
                            font-family: Consolas, Monaco, monospace !important;
                            font-size: 12px !important;
                            overflow-y: auto !important;
                        }
                    `;
                    document.head.appendChild(style);
                    console.log("[OGMA] Textarea CSS fix injected");
                }
            ''')

    # Alias pour compatibilité avec CognitiveMirrorUI
    def show_popup(self):
        """Ouvre le popup — recréé à chaque ouverture pour garantir fraîcheur après F5"""
        # Toujours recréer : après F5 le dialog appartient à un client NiceGUI obsolète
        if self.dialog is not None:
            try:
                self.dialog.delete()
            except Exception:
                pass
            self.dialog = None
            self.ui_controls = {}
        self.create_popup()
        self.show()

    def close_popup(self):
        """Alias → hide()"""
        self.hide()

    @property
    def popup_container(self):
        """Compatibilité — retourne le dialog NiceGUI sous-jacent"""
        return self.dialog

    @property
    def is_popup_visible(self):
        """Compatibilité — indique si le dialog est ouvert"""
        return self.dialog is not None

    def hide(self):
        """Masque le popup"""
        self._close()
    
    def cleanup(self):
        """Nettoyage"""
        self.dialog = None
        self.ui_controls = {}


# Export
__all__ = ['IntrospectionParametersUI']
