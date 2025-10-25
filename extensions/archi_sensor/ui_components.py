# 🎮 Composants UI Extension Archi_sensor - Tubes à essai

"""
Composants d'interface utilisateur pour l'extension Archi_sensor
Tubes à essai métacognitifs avec liquide animé
"""

from typing import Dict, List, Any, Optional
import json

from .config import ArchiSensorConfig

class ArchiSensorUI:
    """Gestionnaire des composants UI pour l'extension Archi_sensor avec tubes à essai"""
    
    def __init__(self):
        self.config = ArchiSensorConfig()
        self.current_levels = {}
        self.is_enabled = False
        self.ui_elements = {}
        self.settings_dialog = None

        # Charger l'état sauvegardé
        self.load_saved_state()
        
    @classmethod
    def get_components(cls):
        """Factory method pour composants UI"""
        return cls()
    
    def create_test_tube(self, ui, metric_name: str, metric_config: Dict[str, Any]):
        """
        Crée un tube à essai pour une métrique donnée
        
        Args:
            ui: Module NiceGUI ui
            metric_name: Nom de la métrique
            metric_config: Configuration de la métrique
        """
        
        max_levels = metric_config.get('levels', 6)
        colors = metric_config.get('colors', ['#666666'] * max_levels)
        display_name = metric_config.get('name', metric_name)
        description = metric_config.get('description', '')
        
        tube_config = self.config.UI_CONFIG
        
        with ui.element('div').classes(f'test-tube-container').style(f'''
            display: flex;
            flex-direction: column;
            align-items: center;
            margin: 20px;
            width: {tube_config["tube_width"] + 40}px;
        '''):
            
            # Étiquette du tube
            ui.label(display_name).classes('tube-label').style(f'''
                color: {tube_config["colors"]["labels"]};
                font-size: 12px;
                font-weight: bold;
                margin-bottom: 8px;
                text-align: center;
                width: 100%;
            ''').props(f'title="{description}"')
            
            # Container du tube avec graduations
            with ui.element('div').classes(f'tube-wrapper-{metric_name}').style(f'''
                position: relative;
                width: {tube_config["tube_width"]}px;
                height: {tube_config["tube_height"]}px;
            '''):
                
                # Tube en verre (contour)
                ui.element('div').classes(f'tube-glass-{metric_name}').style(f'''
                    position: absolute;
                    width: 100%;
                    height: 100%;
                    border: 2px solid {tube_config["colors"]["glass_highlight"]};
                    border-radius: 0 0 30px 30px;
                    background: {tube_config["colors"]["glass"]};
                    backdrop-filter: blur(5px);
                    box-shadow: 
                        inset 0 0 20px rgba(255,255,255,0.1),
                        0 0 20px rgba(0,0,0,0.3);
                    z-index: 2;
                ''')
                
                # Liquide animé avec effet d'ondulation
                liquid_element = ui.element('div').classes(f'tube-liquid-{metric_name}').style(f'''
                    position: absolute;
                    bottom: 2px;
                    left: 2px;
                    right: 2px;
                    height: 0%;
                    background: 
                        linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.15) 50%, transparent 70%),
                        linear-gradient(180deg, 
                            rgba(255,255,255,0.3) 0%, 
                            {colors[0]} 50%, 
                            {colors[0]} 100%);
                    background-size: 200% 200%, 100% 100%;
                    border-radius: 0 0 26px 26px;
                    transition: height {tube_config["tube_animation_duration"]}ms {tube_config["liquid_animation_easing"]};
                    z-index: 1;
                    box-shadow: 0 0 15px rgba(34, 197, 94, 0.5);
                    animation: liquidWaveEffect 4s ease-in-out infinite, liquidPulse 2s ease-in-out infinite alternate;
                    overflow: hidden;
                ''')
                
                # Graduations sur le côté
                for level in range(1, max_levels + 1):
                    level_percentage = (level / max_levels) * 100
                    graduation_y = tube_config["tube_height"] - (level_percentage / 100 * tube_config["tube_height"])
                    
                    # Trait de graduation
                    ui.element('div').style(f'''
                        position: absolute;
                        right: -10px;
                        top: {graduation_y}px;
                        width: 6px;
                        height: 1px;
                        background: {tube_config["colors"]["text"]};
                        opacity: 0.6;
                    ''')
                    
                    # Numéro de graduation
                    ui.label(str(level)).style(f'''
                        position: absolute;
                        right: -25px;
                        top: {graduation_y - 6}px;
                        font-size: 8px;
                        color: {tube_config["colors"]["text"]};
                        opacity: 0.8;
                    ''')
            
            # Stockage des éléments pour animation
            self.ui_elements[f'tube_liquid_{metric_name}'] = liquid_element
            
        return liquid_element
    
    def create_overlay_content(self, ui):
        """
        Crée le contenu de l'overlay compact avec les 2 tubes
        Version optimisée pour overlay fixe à droite
        
        Args:
            ui: Module NiceGUI ui
        """
        
        # Container des tubes compact
        with ui.element('div').classes('tubes-overlay-container').style('''
            display: flex;
            justify-content: space-around;
            align-items: flex-end;
            height: 280px;
            width: 100%;
            padding: 8px 0;
        '''):
            
            # Créer les tubes pour chaque métrique (version compacte)
            for metric_name, metric_config in self.config.METRICS.items():
                self.create_compact_tube(ui, metric_name, metric_config)
        
        # Section de contrôle compact (toggle)
        self.create_compact_control_panel(ui)
    
    def create_compact_tube(self, ui, metric_name: str, metric_config: Dict[str, Any]):
        """
        Crée un tube à essai compact pour overlay
        
        Args:
            ui: Module NiceGUI ui
            metric_name: Nom de la métrique
            metric_config: Configuration de la métrique
        """
        
        max_levels = metric_config.get('levels', 6)
        colors = metric_config.get('colors', ['#666666'] * max_levels)
        display_name = metric_config.get('name', metric_name)
        
        # Dimensions compactes pour overlay
        tube_width = 30
        tube_height = 180
        
        with ui.element('div').classes(f'compact-tube-container').style(f'''
            display: flex;
            flex-direction: column;
            align-items: center;
            margin: 8px;
            width: {tube_width + 20}px;
        '''):
            
            # Étiquette du tube compacte
            ui.label(display_name[:8]).classes('tube-label-compact').style('''
                color: var(--text-primary);
                font-size: 9px;
                font-weight: bold;
                margin-bottom: 4px;
                text-align: center;
                width: 100%;
            ''')
            
            # Container du tube avec graduations
            with ui.element('div').classes(f'tube-wrapper-{metric_name}').style(f'''
                position: relative;
                width: {tube_width}px;
                height: {tube_height}px;
            '''):
                
                # Tube en verre (contour)
                ui.element('div').classes(f'tube-glass-{metric_name}').style(f'''
                    position: absolute;
                    width: 100%;
                    height: 100%;
                    border: 1px solid var(--border-default);
                    border-radius: 0 0 15px 15px;
                    background: rgba(26, 26, 26, 0.3);
                    backdrop-filter: blur(3px);
                    box-shadow: 
                        inset 0 0 10px rgba(255,255,255,0.05),
                        0 0 10px rgba(0,0,0,0.4);
                    z-index: 2;
                ''')
                
                # Liquide animé avec effet d'ondulation
                liquid_element = ui.element('div').classes(f'tube-liquid-{metric_name}').style(f'''
                    position: absolute;
                    bottom: 1px;
                    left: 1px;
                    right: 1px;
                    height: 0%;
                    background: 
                        linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.15) 50%, transparent 70%),
                        linear-gradient(180deg, 
                            rgba(255,255,255,0.2) 0%, 
                            {colors[0]} 50%, 
                            {colors[0]} 100%);
                    background-size: 200% 200%, 100% 100%;
                    border-radius: 0 0 13px 13px;
                    transition: height 600ms ease-out;
                    z-index: 1;
                    box-shadow: 0 0 8px rgba(34, 197, 94, 0.3);
                    animation: liquidWaveEffect 4s ease-in-out infinite, liquidPulse 2s ease-in-out infinite alternate;
                    overflow: hidden;
                ''')
                
                # Graduations compactes
                for level in range(1, max_levels + 1):
                    level_percentage = (level / max_levels) * 100
                    graduation_y = tube_height - (level_percentage / 100 * tube_height)
                    
                    # Trait de graduation (plus petit)
                    ui.element('div').style(f'''
                        position: absolute;
                        right: -6px;
                        top: {graduation_y}px;
                        width: 3px;
                        height: 1px;
                        background: var(--text-muted);
                        opacity: 0.5;
                    ''')
                    
                    # Numéro de graduation (compact)
                    ui.label(str(level)).style(f'''
                        position: absolute;
                        right: -16px;
                        top: {graduation_y - 4}px;
                        font-size: 6px;
                        color: var(--text-muted);
                        opacity: 0.7;
                    ''')
            
            # Stockage des éléments pour animation
            self.ui_elements[f'tube_liquid_{metric_name}'] = liquid_element
            
        return liquid_element
    
    def create_compact_control_panel(self, ui):
        """
        Crée le panneau de contrôle compact avec toggle ON/OFF
        
        Args:
            ui: Module NiceGUI ui
        """
        
        with ui.element('div').classes('archi-control-panel-compact').style('''
            margin-top: 12px;
            padding: 8px;
            background: rgba(0,0,0,0.2);
            border-radius: 6px;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 8px;
        '''):
            
            ui.label('ON').classes('text-xs').style('color: var(--text-muted); font-size: 10px;')
            
            # Toggle switch compact pour activer/désactiver
            toggle_switch = ui.switch(value=self.is_enabled).classes('extension-toggle-compact').style('''
                transform: scale(0.7);
            ''')
            toggle_switch.on('update:model-value', self._handle_toggle_change)

            # Stockage pour synchro état
            self.ui_elements['toggle_switch'] = toggle_switch

            # Bouton settings en ASCII
            with ui.button().classes('settings-btn-compact').style('''
                background: rgba(0,0,0,0.3);
                border: 1px solid var(--border-default);
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 14px;
                cursor: pointer;
                transition: all 0.2s;
            ''').props('title="Paramètres avancés"') as settings_btn:
                ui.label('⚙').style('font-size: 14px;')

            settings_btn.on('click', lambda: self.open_settings_dialog())

    def create_popup_content(self, ui):
        """
        Crée le contenu complet du popup avec les 2 tubes
        
        Args:
            ui: Module NiceGUI ui
        """
        
        tube_config = self.config.UI_CONFIG
        
        with ui.element('div').classes('archi-sensor-popup-content').style(f'''
            padding: 20px;
            background: {tube_config["colors"]["background"]};
            border-radius: 12px;
            width: {tube_config["popup_width"]}px;
            height: {tube_config["popup_height"]}px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
            display: flex;
            flex-direction: column;
            align-items: center;
        '''):
            
            # Titre du popup
            ui.label('🧠 Analyse Métacognitive').style(f'''
                color: {tube_config["colors"]["labels"]};
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 20px;
                text-align: center;
            ''')
            
            # Container des tubes
            with ui.element('div').classes('tubes-container').style('''
                display: flex;
                justify-content: space-around;
                align-items: flex-end;
                flex: 1;
                width: 100%;
                padding: 20px 0;
            '''):
                
                # Créer les tubes pour chaque métrique
                for metric_name, metric_config in self.config.METRICS.items():
                    self.create_test_tube(ui, metric_name, metric_config)
            
            # Section de contrôle (toggle)
            self.create_control_panel(ui)
    
    def create_control_panel(self, ui):
        """
        Crée le panneau de contrôle avec toggle ON/OFF
        
        Args:
            ui: Module NiceGUI ui
        """
        
        with ui.element('div').classes('archi-control-panel').style('''
            margin-top: 20px;
            padding: 12px;
            background: rgba(0,0,0,0.2);
            border-radius: 8px;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 12px;
        '''):
            
            ui.label('Extension').classes('text-sm').style('color: var(--text-muted);')
            
            # Toggle switch pour activer/désactiver
            toggle_switch = ui.switch(value=self.is_enabled).classes('extension-toggle')
            toggle_switch.on('update:model-value', self._handle_toggle_change)
            
            # Stockage pour synchro état
            self.ui_elements['toggle_switch'] = toggle_switch
    
    def _handle_toggle_change(self, event):
        """Gestionnaire changement toggle extension"""
        # Correction: event.args est une liste, pas un dict
        if isinstance(event.args, bool):
            enabled = event.args
        elif isinstance(event.args, list) and len(event.args) > 0:
            enabled = event.args[0]
        else:
            enabled = False
        
        self.is_enabled = enabled
        
        print(f"[ARCHI-UI] Extension {'activée' if enabled else 'désactivée'}")
        
        # Sauvegarder l'état dans un fichier
        try:
            import json
            from pathlib import Path
            config_file = Path("data/archi_sensor_state.json")
            config_file.parent.mkdir(exist_ok=True)
            
            with open(config_file, 'w') as f:
                json.dump({"enabled": enabled}, f)
                
            print(f"[ARCHI-UI] État sauvegardé: {enabled}")
        except Exception as e:
            print(f"[ARCHI-UI] Erreur sauvegarde état: {e}")
    
    def load_saved_state(self):
        """Charger l'état sauvegardé de l'extension"""
        try:
            import json
            from pathlib import Path
            config_file = Path("data/archi_sensor_state.json")
            
            if config_file.exists():
                with open(config_file, 'r') as f:
                    data = json.load(f)
                    self.is_enabled = data.get("enabled", False)
                    print(f"[ARCHI-UI] État chargé: {self.is_enabled}")
            else:
                self.is_enabled = False
                print("[ARCHI-UI] Aucun état sauvegardé, défaut: désactivé")
        except Exception as e:
            print(f"[ARCHI-UI] Erreur chargement état: {e}")
            self.is_enabled = False
    
    def update_tube_levels(self, analysis_result: Dict[str, Any]):
        """
        Met à jour les niveaux des tubes avec animation
        
        Args:
            analysis_result: Résultat d'analyse avec métriques
        """
        
        if not self.is_enabled:
            return
        
        metrics = analysis_result.get('metacognitive_metrics', {})
        tube_config = self.config.UI_CONFIG
        
        for metric_name, data in metrics.items():
            if metric_name in self.config.METRICS:
                level = data.get('level', 1)
                confidence = data.get('confidence', 0.0)
                
                self._animate_tube_liquid(metric_name, level, confidence)
    
    def _animate_tube_liquid(self, metric_name: str, level: int, confidence: float):
        """
        Anime le liquide dans un tube vers le niveau spécifié
        
        Args:
            metric_name: Nom de la métrique
            level: Niveau à atteindre (1-N)
            confidence: Confiance de la mesure (0.0-1.0)
        """
        
        liquid_element_key = f'tube_liquid_{metric_name}'
        if liquid_element_key not in self.ui_elements:
            print(f"[ARCHI-UI] ⚠️ Élément {liquid_element_key} introuvable pour animation")
            return
        
        metric_config = self.config.get_metric_config(metric_name)
        max_levels = metric_config.get('levels', 6)
        colors = metric_config.get('colors', ['#666666'])
        
        # Calculer pourcentage de remplissage
        fill_percentage = (level / max_levels) * 100
        
        # Couleur en fonction du niveau
        color_index = max(0, min(level - 1, len(colors) - 1))
        liquid_color = colors[color_index]
        
        # Opacité basée sur la confiance
        opacity = 0.3 + (confidence * 0.7)  # Entre 30% et 100%
        
        # 🔄 ANIMATION RÉACTIVE avec NiceGUI
        liquid_element = self.ui_elements[liquid_element_key]
        
        # Mettre à jour le style avec animation et FORCER la mise à jour
        # Effet liquide ondulant pour tous les niveaux avec double animation
        liquid_wave_animation = "liquidWaveEffect 4s ease-in-out infinite, liquidPulse 2s ease-in-out infinite alternate"
        
        # Effet d'étincelles spécial pour le niveau 7 d'affinité
        sparkle_animation = ""
        if metric_name == 'affinity' and level == 7:
            sparkle_animation = ", sparkleGlow 1.5s ease-in-out infinite"
        
        new_style = f'''
            position: absolute;
            bottom: 2px;
            left: 2px;
            right: 2px;
            height: {fill_percentage}%;
            background: 
                linear-gradient(45deg, transparent 30%, rgba(255,255,255,0.15) 50%, transparent 70%),
                linear-gradient(180deg, 
                    rgba(255,255,255,0.4) 0%, 
                    {liquid_color} 40%, 
                    {liquid_color} 100%);
            background-size: 200% 200%, 100% 100%;
            border-radius: 0 0 26px 26px;
            transition: height 800ms ease-out;
            z-index: 1;
            opacity: {opacity};
            box-shadow: 0 0 15px {liquid_color}66;
            animation: {liquid_wave_animation}{sparkle_animation};
            overflow: hidden;
        '''
        
        # 🚀 MISE À JOUR FORCÉE pour NiceGUI
        try:
            liquid_element.style(new_style)
            # Forcer un re-render en modifiant les classes
            liquid_element.classes(replace=f'tube-liquid-{metric_name} level-{level}')
            
            print(f"[ARCHI-UI] 🔄 Tube {metric_name}: niveau {level}/{max_levels} (confiance: {confidence:.2f}, {fill_percentage:.1f}%)")
        except Exception as e:
            print(f"[ARCHI-UI] ❌ Erreur animation tube {metric_name}: {e}")
        
        # Mettre à jour le cache des niveaux
        self.current_levels[metric_name] = {'level': level, 'confidence': confidence}
    
    def set_enabled_state(self, enabled: bool):
        """Active/désactive l'affichage des tubes"""
        self.is_enabled = enabled
        
        # Synchroniser le toggle UI
        if 'toggle_switch' in self.ui_elements:
            self.ui_elements['toggle_switch'].value = enabled
        
        # Réinitialiser tubes si désactivé
        if not enabled:
            self._reset_all_tubes()
    
    def _reset_all_tubes(self):
        """Remet tous les tubes à l'état vide"""
        
        for metric_name in self.config.METRICS:
            self._animate_tube_liquid(metric_name, 0, 0.0)
        
        self.current_levels.clear()
    
    def get_current_state(self) -> Dict[str, Any]:
        """Retourne l'état actuel des tubes pour debugging"""

        return {
            'enabled': self.is_enabled,
            'levels': self.current_levels.copy(),
            'metrics_count': len(self.config.METRICS),
            'ui_elements_count': len(self.ui_elements)
        }

    def open_settings_dialog(self):
        """Ouvre le dialog de configuration avancée"""
        try:
            from nicegui import ui

            # Charger config actuelle (custom ou default)
            custom_config = self.config.load_custom_config()
            default_config = self.config.get_default_config()
            current_config = custom_config if custom_config else default_config

            # Créer dialog
            with ui.dialog() as dialog, ui.card().classes('settings-dialog').style('''
                min-width: 800px;
                max-width: 90vw;
                max-height: 90vh;
                overflow-y: auto;
                background: var(--bg-primary);
                padding: 20px;
            '''):

                # Titre
                ui.label('⚙ Configuration avancée Archi_sensor').classes('text-h5').style('''
                    color: var(--accent-gold);
                    margin-bottom: 16px;
                    font-weight: bold;
                ''')

                # Banner avertissement
                with ui.element('div').style('''
                    background: rgba(239, 68, 68, 0.1);
                    border-left: 4px solid #ef4444;
                    padding: 12px;
                    margin-bottom: 20px;
                    border-radius: 4px;
                '''):
                    ui.label('⚠️ ATTENTION').style('color: #ef4444; font-weight: bold; font-size: 14px;')
                    ui.label('La modification de ces paramètres peut déstabiliser le système émotionnel de l\'IA. Procédez avec précaution.').style('''
                        color: #fca5a5;
                        font-size: 12px;
                        margin-top: 4px;
                    ''')

                # SECTION 1: Prompt Archiviste
                ui.label('1. Prompt Archiviste').classes('text-h6').style('color: var(--text-primary); margin-top: 16px; margin-bottom: 8px;')
                prompt_textarea = ui.textarea(
                    label='Instructions pour l\'Archiviste',
                    value=current_config.get('archiviste_prompt', default_config['archiviste_prompt'])
                ).classes('w-full').style('min-height: 200px; font-family: monospace; font-size: 11px;')

                # SECTION 2: Messages affinité
                ui.label('2. Messages d\'injection affinité').classes('text-h6').style('color: var(--text-primary); margin-top: 20px; margin-bottom: 8px;')
                affinity_textareas = {}
                affinity_guidance = current_config.get('affinity_guidance', default_config['affinity_guidance'])

                for level in [3, 4, 5, 6, 7]:
                    ui.label(f'Niveau {level}').style('color: var(--text-muted); font-size: 12px; margin-top: 8px;')
                    affinity_textareas[str(level)] = ui.textarea(
                        value=affinity_guidance.get(str(level), '')
                    ).classes('w-full').style('min-height: 60px; font-size: 12px;')

                # SECTION 3: Messages auto-censure
                ui.label('3. Messages d\'injection auto-censure').classes('text-h6').style('color: var(--text-primary); margin-top: 20px; margin-bottom: 8px;')
                autocensure_textareas = {}
                autocensure_guidance = current_config.get('autocensure_guidance', default_config['autocensure_guidance'])

                for level in [3, 4, 5, 6]:
                    ui.label(f'Niveau {level}').style('color: var(--text-muted); font-size: 12px; margin-top: 8px;')
                    autocensure_textareas[str(level)] = ui.textarea(
                        value=autocensure_guidance.get(str(level), '')
                    ).classes('w-full').style('min-height: 60px; font-size: 12px;')

                # SECTION 4: Seuils injection
                ui.label('4. Seuils d\'injection comportementale').classes('text-h6').style('color: var(--text-primary); margin-top: 20px; margin-bottom: 8px;')
                thresholds = current_config.get('injection_thresholds', default_config['injection_thresholds'])

                with ui.row().classes('w-full gap-4'):
                    affinity_interval_input = ui.number(
                        label='Intervalle injection affinité (nb interactions)',
                        value=thresholds.get('affinity_interval', 3),
                        min=1,
                        max=20
                    ).classes('flex-1')

                    autocensure_interval_input = ui.number(
                        label='Intervalle injection auto-censure (nb interactions)',
                        value=thresholds.get('autocensure_interval', 5),
                        min=1,
                        max=20
                    ).classes('flex-1')

                # Boutons action
                with ui.row().classes('w-full gap-3').style('margin-top: 24px; justify-content: flex-end;'):

                    def save_config():
                        # Compiler nouvelle config
                        new_config = {
                            "archiviste_prompt": prompt_textarea.value,
                            "affinity_guidance": {str(k): v.value for k, v in affinity_textareas.items()},
                            "autocensure_guidance": {str(k): v.value for k, v in autocensure_textareas.items()},
                            "injection_thresholds": {
                                "affinity_interval": int(affinity_interval_input.value),
                                "autocensure_interval": int(autocensure_interval_input.value)
                            }
                        }

                        # Sauvegarder
                        if self.config.save_custom_config(new_config):
                            ui.notify('✅ Configuration sauvegardée avec succès', type='positive', position='top')
                            dialog.close()
                        else:
                            ui.notify('❌ Erreur lors de la sauvegarde', type='negative', position='top')

                    def reset_defaults():
                        if self.config.reset_to_defaults():
                            ui.notify('✅ Configuration réinitialisée aux valeurs par défaut', type='positive', position='top')
                            dialog.close()
                            # Rouvrir dialog avec valeurs par défaut
                            self.open_settings_dialog()
                        else:
                            ui.notify('❌ Erreur lors de la réinitialisation', type='negative', position='top')

                    ui.button('Annuler', on_click=dialog.close).props('flat').style('color: var(--text-muted);')
                    ui.button('Réinitialiser défauts', on_click=reset_defaults).props('outline').style('color: #f59e0b;')
                    ui.button('💾 Sauvegarder', on_click=save_config).props('color=primary')

            dialog.open()
            self.settings_dialog = dialog

        except Exception as e:
            print(f"[ARCHI-UI] ❌ Erreur ouverture settings: {e}")
            import traceback
            traceback.print_exc()