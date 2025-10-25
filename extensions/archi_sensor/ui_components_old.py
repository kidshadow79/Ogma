# 🎮 Composants UI Extension Archi_sensor

"""
Composants d'interface utilisateur pour l'extension Archi_sensor
Panneau métacognitif avec LEDs et contrôles
"""

from typing import Dict, List, Any, Optional
import json

from .config import ArchiSensorConfig

class ArchiSensorUI:
    """Gestionnaire des composants UI pour l'extension Archi_sensor"""
    
    def __init__(self):
        self.config = ArchiSensorConfig()
        self.current_levels = {}
        self.is_enabled = False
        self.ui_elements = {}
        
    @classmethod
    def get_components(cls):
        """Factory method pour composants UI"""
        return cls()
    
    def create_led_gauge(self, ui, metric_name: str, metric_config: Dict[str, Any]):
        """
        Crée une jauge LED pour une métrique donnée
        
        Args:
            ui: Module NiceGUI ui
            metric_name: Nom de la métrique
            metric_config: Configuration de la métrique
        """
        
        max_levels = metric_config.get('levels', 6)
        colors = metric_config.get('colors', ['#666666'] * max_levels)
        display_name = metric_config.get('name', metric_name)
        description = metric_config.get('description', '')
        
        with ui.element('div').classes('gauge-container'):
            # Titre de la jauge
            ui.label(display_name).classes('gauge-title').props(f'title="{description}"')
            
            # Container des LEDs
            with ui.element('div').classes('gauge-leds').style('display: flex; gap: 4px; margin: 8px 0;'):
                
                # Créer LEDs individuelles
                led_elements = []
                for level in range(1, max_levels + 1):
                    led_color = colors[min(level - 1, len(colors) - 1)]
                    
                    led = ui.element('div').classes(f'led led-{metric_name} led-level-{level}').style(f'''
                        width: 20px;
                        height: 20px;
                        border-radius: 50%;
                        background: {led_color};
                        opacity: 0.2;
                        border: 1px solid rgba(255,255,255,0.1);
                        transition: all 0.3s ease;
                        cursor: help;
                    ''').props(f'title="Niveau {level}"')
                    
                    led_elements.append(led)
                
                # Stocker références LEDs
                self.ui_elements[f'{metric_name}_leds'] = led_elements
            
            # Indicateur niveau textuel (optionnel)
            level_indicator = ui.label('Niveau: -').classes('gauge-level-text').style('''
                font-size: 11px;
                color: var(--text-muted);
                margin-top: 4px;
            ''')
            
            self.ui_elements[f'{metric_name}_text'] = level_indicator
    
    def update_led_levels(self, analysis_result: Dict[str, Any]):
        """
        Met à jour toutes les LEDs selon les résultats d'analyse
        
        Args:
            analysis_result: Résultat complet de l'analyse Archiviste
        """
        
        if not self.is_enabled:
            return
        
        try:
            metrics = analysis_result.get('metacognitive_metrics', {})
            
            for metric_name, metric_data in metrics.items():
                if metric_name in self.config.METRICS:
                    level = metric_data.get('level', 1)
                    confidence = metric_data.get('confidence', 0.5)
                    
                    self._update_single_led_gauge(metric_name, level, confidence)
            
            print(f"[ARCHI-UI] ✅ LEDs mises à jour: {len(metrics)} métriques")
            
        except Exception as e:
            print(f"[ARCHI-UI] ❌ Erreur mise à jour LEDs: {e}")
    
    def _update_single_led_gauge(self, metric_name: str, level: int, confidence: float):
        """Met à jour une jauge LED individuelle"""
        
        try:
            # Récupérer éléments LED
            led_elements = self.ui_elements.get(f'{metric_name}_leds', [])
            text_element = self.ui_elements.get(f'{metric_name}_text')
            
            if not led_elements:
                return
            
            metric_config = self.config.METRICS.get(metric_name, {})
            max_levels = metric_config.get('levels', 6)
            colors = metric_config.get('colors', ['#666666'] * max_levels)
            
            # Calculer opacité basée sur confidence
            base_opacity = max(0.2, confidence * 0.8 + 0.2)  # 0.2 à 1.0
            
            # Mettre à jour chaque LED
            for i, led_element in enumerate(led_elements):
                current_level = i + 1
                led_color = colors[min(i, len(colors) - 1)]
                
                if current_level <= level:
                    # LED active
                    opacity = base_opacity
                    border_color = 'rgba(255,255,255,0.3)'
                    transform = 'scale(1.05)' if current_level == level else 'scale(1.0)'
                else:
                    # LED inactive
                    opacity = 0.15
                    border_color = 'rgba(255,255,255,0.1)'
                    transform = 'scale(1.0)'
                
                # Appliquer styles
                led_element.style(f'''
                    background: {led_color};
                    opacity: {opacity};
                    border: 1px solid {border_color};
                    transform: {transform};
                    box-shadow: {f"0 0 8px {led_color}" if current_level == level and confidence > 0.7 else "none"};
                ''')
            
            # Mettre à jour texte niveau
            if text_element:
                confidence_percent = int(confidence * 100)
                text_element.text = f'Niveau: {level}/{max_levels} ({confidence_percent}%)'
            
            # Stocker état actuel
            self.current_levels[metric_name] = {
                'level': level,
                'confidence': confidence,
                'timestamp': self._get_timestamp()
            }
            
        except Exception as e:
            print(f"[ARCHI-UI] ⚠️ Erreur update LED {metric_name}: {e}")
    
    def set_enabled_state(self, enabled: bool):
        """Active/désactive l'affichage des LEDs"""
        
        self.is_enabled = enabled
        
        if not enabled:
            # Réinitialiser toutes les LEDs
            self._reset_all_leds()
        
        # Appliquer classe CSS d'état
        panel_class = 'enabled' if enabled else 'disabled'
        # TODO: Appliquer classe au panneau principal
        
        print(f"[ARCHI-UI] Interface {'activée' if enabled else 'désactivée'}")
    
    def _reset_all_leds(self):
        """Remet toutes les LEDs à l'état inactif"""
        
        for metric_name in self.config.METRICS.keys():
            led_elements = self.ui_elements.get(f'{metric_name}_leds', [])
            
            for led_element in led_elements:
                led_element.style('''
                    opacity: 0.1;
                    transform: scale(1.0);
                    border: 1px solid rgba(255,255,255,0.05);
                    box-shadow: none;
                ''')
            
            # Réinitialiser texte
            text_element = self.ui_elements.get(f'{metric_name}_text')
            if text_element:
                text_element.text = 'Niveau: - (Extension désactivée)'
    
    def get_current_state(self) -> Dict[str, Any]:
        """Retourne l'état actuel des LEDs pour debugging"""
        
        return {
            'enabled': self.is_enabled,
            'levels': self.current_levels.copy(),
            'metrics_count': len(self.config.METRICS),
            'ui_elements_count': len(self.ui_elements)
        }
    
    def create_control_panel(self, ui, toggle_callback):
        """
        Crée le panneau de contrôles en haut du drawer
        
        Args:
            ui: Module NiceGUI ui  
            toggle_callback: Fonction callback pour toggle ON/OFF
        """
        
        with ui.element('div').classes('archi-sensor-controls').style('''
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            margin-bottom: 16px; 
            padding: 12px;
            background: rgba(212, 175, 55, 0.05);
            border-radius: 8px;
            border: 1px solid rgba(212, 175, 55, 0.1);
        '''):
            
            # Titre
            ui.label('Analyse Archiviste').classes('text-lg font-bold').style('''
                color: var(--accent-gold); 
                margin: 0;
                font-weight: 600;
            ''')
            
            # Toggle ON/OFF avec label
            with ui.element('div').style('display: flex; gap: 8px; align-items: center;'):
                ui.label('Extension').classes('text-xs').style('color: var(--text-muted);')
                
                # Switch avec état initial
                extension_toggle = ui.switch(
                    value=self.is_enabled,
                    on_change=lambda e: self._handle_toggle_change(e.value, toggle_callback)
                ).classes('archi-sensor-switch').props('size="xs"').style('transform: scale(0.8);')
                
                # Stocker référence toggle
                self.ui_elements['extension_toggle'] = extension_toggle
        
        return extension_toggle
    
    def _handle_toggle_change(self, enabled: bool, toggle_callback):
        """Gestionnaire changement toggle extension"""
        
        print(f"[ARCHI-UI] Toggle extension: {enabled}")
        
        # Mettre à jour état interne
        self.set_enabled_state(enabled)
        
        # Appeler callback externe (persistence, etc.)
        if toggle_callback:
            try:
                toggle_callback(enabled)
            except Exception as e:
                print(f"[ARCHI-UI] Erreur callback toggle: {e}")
    
    def sync_toggle_state(self, enabled: bool):
        """Synchronise l'état du toggle UI avec l'état système"""
        
        toggle_element = self.ui_elements.get('extension_toggle')
        if toggle_element:
            toggle_element.value = enabled
        
        self.set_enabled_state(enabled)
    
    def create_debug_info(self, ui):
        """Crée section d'informations de debug (optionnel)"""
        
        with ui.element('div').classes('archi-sensor-debug').style('''
            margin-top: 16px;
            padding: 8px;
            background: rgba(0,0,0,0.2);
            border-radius: 4px;
            font-size: 10px;
            color: var(--text-muted);
        '''):
            
            debug_text = ui.label('Debug: Extension chargée').classes('text-xs')
            self.ui_elements['debug_text'] = debug_text
    
    def update_debug_info(self, analysis_result: Dict[str, Any]):
        """Met à jour les informations de debug"""
        
        debug_element = self.ui_elements.get('debug_text')
        if debug_element and analysis_result:
            
            # Compter métriques actives
            metrics = analysis_result.get('metacognitive_metrics', {})
            active_metrics = len([m for m in metrics.values() if m.get('confidence', 0) > 0.3])
            
            # Émotion principale
            emotion = analysis_result.get('emotional_context', {}).get('primary_emotion', 'neutre')
            
            debug_text = f"Métriques: {active_metrics}/{len(self.config.METRICS)} | Émotion: {emotion}"
            debug_element.text = debug_text
    
    def _get_timestamp(self) -> str:
        """Retourne timestamp actuel pour tracking"""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")