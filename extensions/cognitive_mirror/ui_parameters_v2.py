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
                    tab_general = ui.tab('Général', icon='settings')
                    tab_instructions = ui.tab('Instructions', icon='edit_note')
                    tab_advanced = ui.tab('Avancé', icon='tune')
                
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
            ui.label('Introspection v4').style('''
                font-size: 24px;
                font-weight: 600;
                color: white;
                margin-left: 12px;
            ''')
            ui.space()
            ui.label('IA Principale ↔ Archiviste').style('''
                color: rgba(255,255,255,0.7);
                font-style: italic;
            ''')
    
    def _create_general_tab(self):
        """Onglet Configuration Générale"""
        
        # Section ON/OFF
        self._section_title("🔌 Activation", "#3b82f6")
        
        with ui.row().classes('w-full items-center gap-4').style('margin-bottom: 24px;'):
            current_state = self.config.is_enabled()
            
            self.ui_controls['enabled'] = ui.switch(
                value=current_state,
                on_change=self._on_toggle_changed
            ).props('color=primary size=lg').tooltip(
                'Active le dialogue intérieur IA Principale ↔ Archiviste. '
                'Désactivé : les phrases magiques sont toujours détectées mais aucun dialogue interne ne se lance.'
            )
            
            with ui.column().classes('gap-1'):
                ui.label('Extension Introspection').style('font-weight: 600; color: #e5e7eb;')
                ui.label(
                    'Activée: dialogue Conscient↔Inconscient' if current_state 
                    else 'Désactivée: phrases magiques uniquement'
                ).style('color: #9ca3af; font-size: 14px;')
        
        # Section Mode
        self._section_title("🎯 Mode de déclenchement", "#8b5cf6")
        
        current_mode = self.config.get_introspection_mode()
        
        with ui.column().classes('gap-3').style('margin-bottom: 24px;'):
            self.ui_controls['mode'] = ui.radio(
                options={
                    'on_demand': '📝 À la demande (phrases magiques)',
                    'always': '🔄 Systématique (chaque message)'
                },
                value=current_mode,
                on_change=self._on_mode_changed
            ).props('inline').style('color: #e5e7eb;').tooltip(
                'À la demande : se déclenche uniquement sur les phrases clés ("réfléchis", "introspection"...). '
                'Systématique : chaque message de l\'utilisateur passe par le dialogue intérieur — plus lent mais plus profond.'
            )
            
            ui.label(
                'À la demande: Utilise les phrases comme "réfléchis", "introspection"...'
            ).style('color: #9ca3af; font-size: 13px; margin-left: 8px;')
        
        # Section Phrases Magiques (lecture seule pour référence)
        self._section_title("✨ Phrases magiques actives", "#10b981")
        
        with ui.card().style('background: rgba(16, 185, 129, 0.1); padding: 24px; border-radius: 8px; min-height: 120px;'):
            phrases = self.config.get_magic_phrases("user_trigger")
            ui.label('Déclenchement: ' + ', '.join(f'"{p}"' for p in phrases)).style(
                'color: #9ca3af; font-size: 14px; line-height: 1.8;'
            )
            
            stop_phrases = self.config.get_magic_phrases("user_stop")
            ui.label('Arrêt: ' + ', '.join(f'"{p}"' for p in stop_phrases)).style(
                'color: #9ca3af; font-size: 14px; margin-top: 12px; line-height: 1.8;'
            )
    
    def _create_instructions_tab(self):
        """Onglet Instructions avec boutons restauration"""
        
        ui.label('Instructions pour chaque étape du dialogue intérieur').style(
            'color: #9ca3af; margin-bottom: 20px;'
        )
        
        # Étape 1: Ouverture
        self._create_instruction_editor(
            step_key="step1_analysis",
            title="🗣️ Ouverture",
            description="L'IA Principale formule le sujet et sa position initiale",
            color="#3b82f6"
        )
        
        # IA Principale (joute)
        self._create_instruction_editor(
            step_key="step2_conscious",
            title="💭 IA Principale",
            description="L'IA Principale continue la joute — défend, admet, change d'angle",
            color="#8b5cf6"
        )
        
        # Archiviste (confronteur)
        self._create_instruction_editor(
            step_key="step2_unconscious",
            title="⚔️ Archiviste",
            description="L'Archiviste confronte et protège la cohérence — n'est PAS une base de données",
            color="#f59e0b"
        )
        
        # Étape 3: Synthèse
        self._create_instruction_editor(
            step_key="step3_synthesis",
            title="✨ Synthèse",
            description="L'IA Principale conclut honnêtement et formule sa réponse",
            color="#10b981"
        )
        
        # Bouton restaurer tout
        with ui.row().classes('w-full justify-center').style('margin-top: 24px;'):
            ui.button(
                '🔄 Restaurer TOUTES les instructions par défaut',
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
                    # Tokens configurables
                    ui.label('Tokens:').style('color: #9ca3af; font-size: 13px;')
                    token_input = ui.number(
                        value=default_tokens,
                        min=100,
                        max=2000,
                        step=100,
                        on_change=lambda e, k=step_key: self._on_tokens_changed(k, e.value)
                    ).props('dense outlined dark').style('width: 80px;').tooltip(
                        'Longueur cible de la réponse en tokens. '
                        'L\'IA reçoit une instruction pour calibrer sa verbosité naturellement et conclure dans cette limite. '
                        'La limite API réelle est 1.4× cette valeur (filet de sécurité anti-troncature).'
                    )
                    self.ui_controls[f'{step_key}_tokens'] = token_input
                    
                    # Bouton restaurer
                    ui.button(
                        icon='restore',
                        on_click=lambda k=step_key: self._restore_instruction(k)
                    ).props('flat dense color=warning').tooltip('Restaurer par défaut')
            
            # Textarea instruction — dans un column qui force la hauteur
            with ui.column().style('width: 100%; min-height: 400px;'):
                self.ui_controls[step_key] = ui.textarea(
                    value=current_text,
                    on_change=lambda e, k=step_key: self._on_instruction_changed(k, e.value)
                ).props('outlined dark').classes('w-full').style('min-height: 380px;')
    
    def _create_advanced_tab(self):
        """Onglet Paramètres Avancés"""
        
        # Dialogue
        self._section_title("💬 Paramètres Dialogue", "#8b5cf6")
        
        with ui.row().classes('gap-6').style('margin-bottom: 24px;'):
            with ui.column().classes('gap-2'):
                ui.label('Échanges min').style('color: #e5e7eb;')
                self.ui_controls['min_exchanges'] = ui.number(
                    value=self.config.get("min_dialogue_exchanges", 2),
                    min=1,
                    max=8,
                    on_change=lambda e: self._on_setting_changed("min_dialogue_exchanges", e.value)
                ).props('outlined dark dense').style('width: 100px;').tooltip(
                    'Nombre minimum d\'allers-retours garantis avant que la synthèse soit autorisée. '
                    'Même si l\'IA Principale veut conclure plus tôt, la joute continuera jusqu\'à ce seuil.'
                )

            with ui.column().classes('gap-2'):
                ui.label('Échanges max').style('color: #e5e7eb;')
                self.ui_controls['max_exchanges'] = ui.number(
                    value=self.config.get("max_dialogue_exchanges", 6),
                    min=2,
                    max=10,
                    on_change=lambda e: self._on_setting_changed("max_dialogue_exchanges", e.value)
                ).props('outlined dark dense').style('width: 100px;').tooltip(
                    'Nombre maximum d\'allers-retours dans la joute. '
                    'Au-delà, passage forcé à la synthèse même si l\'IA Principale n\'a pas conclu.'
                )
            
            with ui.column().classes('gap-2'):
                ui.label('Timeout (sec)').style('color: #e5e7eb;')
                self.ui_controls['timeout'] = ui.number(
                    value=self.config.get("max_introspection_duration", 120),
                    min=30,
                    max=600,
                    step=30,
                    on_change=lambda e: self._on_setting_changed("max_introspection_duration", e.value)
                ).props('outlined dark dense').style('width: 100px;').tooltip(
                    'Durée maximale totale de l\'introspection en secondes. '
                    'Si dépassée, la synthèse est forcée immédiatement quelle que soit la progression.'
                )
        
        # Mémoire
        self._section_title("🧠 Recherche Mémoire", "#10b981")
        
        with ui.row().classes('gap-6').style('margin-bottom: 24px;'):
            with ui.column().classes('gap-2'):
                with ui.row().classes('items-center gap-1'):
                    ui.label('Seuil similarité').style('color: #e5e7eb;')
                    ui.icon('help_outline', size='16px').style('color: #9ca3af; cursor: help;').tooltip(
                        'Seuil de similarité FAISS pour la recherche mémorielle. '
                        '0.1 = récupère beaucoup (large, moins précis). 0.9 = récupère peu (strict, très pertinent). '
                        'Recommandé : 0.5–0.6.'
                    )
                self.ui_controls['memory_threshold'] = ui.slider(
                    value=self.config.get("memory_search_threshold", 0.5),
                    min=0.1,
                    max=0.9,
                    step=0.1,
                    on_change=lambda e: self._on_setting_changed("memory_search_threshold", e.value)
                ).props('label-always').style('width: 200px;')
        
        # Sauvegarde
        self._section_title("💾 Sauvegarde Automatique", "#f59e0b")
        
        with ui.column().classes('gap-4').style('margin-bottom: 24px;'):
            self.ui_controls['auto_save'] = ui.switch(
                'L\'IA décide si sauvegarder l\'introspection',
                value=self.config.get("auto_save_enabled", False),
                on_change=lambda e: self._on_setting_changed("auto_save_enabled", e.value)
            ).style('color: #e5e7eb;').tooltip(
                'L\'IA évalue l\'importance de chaque introspection et décide seule si elle mérite d\'être mémorisée. '
                'Désactivé : aucune sauvegarde automatique.'
            )
            
            with ui.row().classes('items-center gap-2'):
                with ui.row().classes('items-center gap-1'):
                    ui.label('Seuil importance:').style('color: #e5e7eb;')
                    ui.icon('help_outline', size='16px').style('color: #9ca3af; cursor: help;').tooltip(
                        'Seuil minimum d\'importance (1–10) pour la sauvegarde automatique. '
                        '1 = tout sauvegarder. 10 = sauvegarder uniquement les insights majeurs. '
                        'Recommandé : 6–7.'
                    )
                self.ui_controls['importance_threshold'] = ui.slider(
                    value=self.config.get("importance_threshold", 6),
                    min=1,
                    max=10,
                    step=1,
                    on_change=lambda e: self._on_setting_changed("importance_threshold", e.value)
                ).props('label-always').style('width: 200px;')
        
        # Affichage
        self._section_title("👁️ Affichage", "#3b82f6")
        
        with ui.column().classes('gap-2'):
            self.ui_controls['show_dialogue'] = ui.switch(
                'Afficher détails du dialogue',
                value=self.config.get("show_dialogue_details", True),
                on_change=lambda e: self._on_setting_changed("show_dialogue_details", e.value)
            ).style('color: #e5e7eb;').tooltip(
                'Affiche chaque échange IA Principale ↔ Archiviste dans la boîte de pensée. '
                'Désactivé : seule la réponse finale est visible.'
            )
            
            self.ui_controls['show_progress'] = ui.switch(
                'Afficher indicateur de progression',
                value=self.config.get("show_progress_indicator", True),
                on_change=lambda e: self._on_setting_changed("show_progress_indicator", e.value)
            ).style('color: #e5e7eb;').tooltip(
                'Affiche la barre de progression et le numéro d\'échange en cours pendant l\'introspection.'
            )
            
            self.ui_controls['typing_anim'] = ui.switch(
                'Animation de saisie',
                value=self.config.get("typing_animation", True),
                on_change=lambda e: self._on_setting_changed("typing_animation", e.value)
            ).style('color: #e5e7eb;').tooltip(
                'Active l\'animation de frappe progressive lors de l\'affichage des réponses du dialogue. '
                'Désactivé : les réponses apparaissent instantanément.'
            )
    
    def _create_footer(self):
        """Footer avec boutons action"""
        with ui.row().classes('w-full justify-between items-center').style('''
            padding: 16px 24px;
            background: #374151;
            border-radius: 0 0 12px 12px;
        '''):
            ui.button(
                '🔄 Tout restaurer par défaut',
                on_click=self._restore_all_defaults
            ).props('flat color=warning')
            
            with ui.row().classes('gap-2'):
                ui.button('Annuler', on_click=self._close).props('flat color=grey')
                ui.button('Appliquer', on_click=self._apply_and_close).props('color=primary')
    
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
        ui.notify(f"Introspection {'activée' if new_state else 'désactivée'}", type='info')
    
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
            ui.notify(f'Instruction restaurée', type='positive')
        else:
            ui.notify('Erreur restauration', type='negative')
    
    def _restore_all_instructions(self):
        """Restaure toutes les instructions"""
        for step_key in ["step1_analysis", "step2_conscious", "step2_unconscious", "step3_synthesis"]:
            self.config.reset_instruction_to_default(step_key)
            if step_key in self.ui_controls:
                self.ui_controls[step_key].value = self.config.get_instruction_text(step_key)
        ui.notify('Toutes les instructions restaurées', type='positive')
    
    def _restore_all_defaults(self):
        """Restaure TOUT par défaut"""
        self.config.reset_all_to_default()
        ui.notify('Configuration complète restaurée', type='positive')
        # Fermer et rouvrir pour rafraîchir
        self._close()
    
    def _close(self):
        """Ferme le popup"""
        if self.dialog:
            self.dialog.close()
    
    def _apply_and_close(self):
        """Applique et ferme"""
        self.config.save_config()
        ui.notify('Configuration sauvegardée', type='positive')
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
