# 🎯 Capability Advisor - LED Manager
"""
Gestionnaire états LEDs capacités avec animations
Pattern identique à Archi Sensor tubes
"""

import asyncio
from typing import Dict, Optional
from .capability_catalog import CAPABILITIES


class LEDManager:
    """Gestionnaire états LEDs capacités (pattern Archi Sensor)"""
    
    def __init__(self, led_timeout: int = 30):
        """
        Initialise LED manager
        
        Args:
            led_timeout: [DÉSACTIVÉ] Timeout secondes avant extinction auto LED
        """
        self.led_timeout = led_timeout  # ⚠️ Non utilisé - timeout désactivé
        
        # États LEDs (False = éteinte, True = allumée)
        self.led_states: Dict[str, bool] = {
            cap_id: False for cap_id in CAPABILITIES.keys()
        }
        
        # Éléments UI LEDs (injectés par ui_components)
        self.led_ui_elements: Dict[str, any] = {}
        
        # Timers extinction auto (asyncio tasks)
        self._deactivation_timers: Dict[str, asyncio.Task] = {}
        
        print(f"[CAPABILITY-ADVISOR] ✅ LEDManager initialisé (timeout: {led_timeout}s)")
    
    def activate_led(self, capability_id: str):
        """
        Allume LED capacité déclenchée
        
        Args:
            capability_id: ID capacité à allumer
        """
        if capability_id not in CAPABILITIES:
            print(f"[CAPABILITY-ADVISOR] ⚠️ LED inconnue: {capability_id}")
            return
        
        # Mettre à jour état
        self.led_states[capability_id] = True
        
        # Mettre à jour UI
        self._update_ui_led(capability_id, state=True)
        
        # Annuler timer existant si présent
        if capability_id in self._deactivation_timers:
            self._deactivation_timers[capability_id].cancel()
            del self._deactivation_timers[capability_id]
        
        print(f"[CAPABILITY-ADVISOR] 💡 LED {capability_id} ALLUMÉE")
    
    def deactivate_led(self, capability_id: str):
        """
        Éteint LED après utilisation capacité
        
        Args:
            capability_id: ID capacité à éteindre
        """
        if capability_id not in CAPABILITIES:
            print(f"[CAPABILITY-ADVISOR] ⚠️ LED inconnue: {capability_id}")
            return
        
        # Mettre à jour état
        self.led_states[capability_id] = False
        
        # Mettre à jour UI
        self._update_ui_led(capability_id, state=False)
        
        # Annuler timer si présent
        if capability_id in self._deactivation_timers:
            self._deactivation_timers[capability_id].cancel()
            del self._deactivation_timers[capability_id]
        
        print(f"[CAPABILITY-ADVISOR] ⚫ LED {capability_id} ÉTEINTE")
    
    def schedule_deactivation(self, capability_id: str, timeout: Optional[int] = None):
        """
        Planifie extinction auto LED si pas utilisée
        
        Args:
            capability_id: ID capacité
            timeout: Timeout personnalisé (ou utilise config par défaut)
        """
        if capability_id not in CAPABILITIES:
            return
        
        actual_timeout = timeout if timeout is not None else self.led_timeout
        
        async def deactivate_after_timeout():
            """Coroutine extinction après timeout"""
            await asyncio.sleep(actual_timeout)
            self.deactivate_led(capability_id)
            print(f"[CAPABILITY-ADVISOR] ⏱️ LED {capability_id} éteinte après timeout ({actual_timeout}s)")
        
        # Créer task asyncio
        try:
            # Annuler timer existant
            if capability_id in self._deactivation_timers:
                self._deactivation_timers[capability_id].cancel()
            
            # Créer nouveau timer
            loop = asyncio.get_event_loop()
            timer_task = loop.create_task(deactivate_after_timeout())
            self._deactivation_timers[capability_id] = timer_task
            
            print(f"[CAPABILITY-ADVISOR] ⏱️ Timer extinction planifié: {capability_id} ({actual_timeout}s)")
        except Exception as e:
            print(f"[CAPABILITY-ADVISOR] ⚠️ Erreur planification timer: {e}")
    
    def _update_ui_led(self, capability_id: str, state: bool):
        """
        Met à jour visuel LED dans overlay UI
        
        Args:
            capability_id: ID capacité
            state: True = allumée, False = éteinte
        """
        if capability_id not in self.led_ui_elements:
            # UI pas encore créée (normal au démarrage)
            return
        
        try:
            led_element = self.led_ui_elements[capability_id]
            
            if led_element is None:
                return
            
            # Changer STYLE directement pour forcer visuel
            if state:
                # Allumer LED (FORCE MAXIMALE tous les styles)
                led_element.style(
                    'width: 14px !important; height: 14px !important; border-radius: 50% !important; flex-shrink: 0 !important; '
                    'background-color: #FF9800 !important; background: #FF9800 !important; '
                    'box-shadow: 0 0 20px rgba(255, 152, 0, 1.0), 0 0 40px rgba(255, 152, 0, 0.8), 0 0 60px rgba(255, 152, 0, 0.5) !important; '
                    'filter: brightness(1.5) saturate(1.3) contrast(1.2) !important; '
                    'opacity: 1 !important; '
                    'backdrop-filter: none !important; '
                    'position: relative !important; '
                    'z-index: 1000 !important;'
                )
                # Ajouter classe pour animation CSS
                led_element.classes(add='led-on')
                led_element.classes(remove='led-off')
                # FORCER update UI NiceGUI
                led_element.update()
                print(f"[CAPABILITY-ADVISOR] 🔥 UI LED {capability_id} → ORANGE ULTRA-VIF (force maximale)")
            else:
                # Éteindre LED (FORCE MAXIMALE style gris pour écraser orange)
                led_element.style(
                    'width: 14px !important; height: 14px !important; border-radius: 50% !important; flex-shrink: 0 !important; '
                    'background-color: #444 !important; background: #444 !important; '
                    'box-shadow: 0 0 5px rgba(0,0,0,0.3) !important; '
                    'filter: none !important; '
                    'opacity: 0.6 !important; '
                    'backdrop-filter: none !important; '
                    'position: relative !important; '
                    'z-index: 1000 !important;'
                )
                led_element.classes(add='led-off')
                led_element.classes(remove='led-on')
                # FORCER update UI NiceGUI
                led_element.update()
                print(f"[CAPABILITY-ADVISOR] ⚫ UI LED {capability_id} → GRIS (FORCE MAXIMALE !important)")
        
        except Exception as e:
            print(f"[CAPABILITY-ADVISOR] ⚠️ Erreur update UI LED: {e}")
            import traceback
            traceback.print_exc()
    
    def get_led_state(self, capability_id: str) -> bool:
        """
        Récupère état actuel LED
        
        Args:
            capability_id: ID capacité
            
        Returns:
            bool: True si allumée, False si éteinte
        """
        return self.led_states.get(capability_id, False)
    
    def get_all_led_states(self) -> Dict[str, bool]:
        """
        Récupère états toutes LEDs
        
        Returns:
            dict: États LEDs {cap_id: bool}
        """
        return self.led_states.copy()
    
    def reset_all_leds(self):
        """Éteint toutes les LEDs (reset complet)"""
        for cap_id in CAPABILITIES.keys():
            self.deactivate_led(cap_id)
        
        print(f"[CAPABILITY-ADVISOR] 🔄 Toutes les LEDs réinitialisées")
    
    def cleanup(self):
        """Nettoyage timers avant fermeture"""
        # Annuler tous les timers en cours
        for cap_id, timer_task in self._deactivation_timers.items():
            timer_task.cancel()
        
        self._deactivation_timers.clear()
        print(f"[CAPABILITY-ADVISOR] 🧹 LEDManager cleanup terminé")
