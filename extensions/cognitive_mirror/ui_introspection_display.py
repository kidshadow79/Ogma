# 🧠 Introspection v2.1 - Composants d'affichage UI

"""
Composants visuels pour l'affichage de l'introspection:
- Barre de progression 3 étapes
- Indicateur typing/loading
- Affichage dialogue coloré (Conscient/Inconscient)
- Timer avec ETA
"""

from typing import Optional, Callable, Dict, Any, List
import asyncio
import time

try:
    from nicegui import ui
    NICEGUI_AVAILABLE = True
except ImportError:
    NICEGUI_AVAILABLE = False


# ============================================================================
# CONSTANTES VISUELLES
# ============================================================================

COLORS = {
    "conscious": "#3b82f6",      # Bleu - Conscient (IA)
    "unconscious": "#8b5cf6",    # Violet - Inconscient (Archiviste)
    "analysis": "#10b981",       # Vert - Analyse
    "synthesis": "#f59e0b",      # Orange - Synthèse
    "error": "#ef4444",          # Rouge - Erreur (pas de fallback silencieux)
    "background": "#1f2937",     # Fond sombre
    "text": "#e5e7eb",           # Texte clair
    "muted": "#9ca3af",          # Texte secondaire
}

STEP_ICONS = {
    1: "�️",  # Ouverture
    2: "⚔️",   # Joute
    3: "✨",   # Synthèse
}

STEP_NAMES = {
    1: "Ouverture",
    2: "Joute",
    3: "Synthèse",
}


# ============================================================================
# BARRE DE PROGRESSION
# ============================================================================

class IntrospectionProgressBar:
    """
    Barre de progression visuelle pour les 3 étapes d'introspection
    """
    
    def __init__(self, container=None):
        self.container = container
        self.current_step = 0
        self.step_elements = {}
        self.progress_element = None
        self.timer_element = None
        self.start_time = None
        
    def create(self):
        """Crée la barre de progression"""
        if not NICEGUI_AVAILABLE:
            return None
        
        with ui.row().classes('w-full items-center justify-between').style(f'''
            background: {COLORS["background"]};
            padding: 12px 16px;
            border-radius: 8px;
            margin-bottom: 12px;
        ''') as self.container:
            
            # Étapes
            with ui.row().classes('items-center gap-4'):
                for step_num in [1, 2, 3]:
                    self.step_elements[step_num] = self._create_step_indicator(step_num)
            
            # Timer
            self.timer_element = ui.label('0:00').style(f'''
                color: {COLORS["muted"]};
                font-family: monospace;
                font-size: 14px;
            ''')
        
        return self.container
    
    def _create_step_indicator(self, step_num: int):
        """Crée un indicateur d'étape"""
        with ui.row().classes('items-center gap-2') as step_row:
            # Icône/numéro
            icon_label = ui.label(STEP_ICONS[step_num]).style(f'''
                font-size: 16px;
                opacity: 0.5;
            ''')
            
            # Nom
            name_label = ui.label(STEP_NAMES[step_num]).style(f'''
                color: {COLORS["muted"]};
                font-size: 13px;
                font-weight: 500;
            ''')
            
            # Connecteur (sauf dernier)
            if step_num < 3:
                ui.label('→').style(f'color: {COLORS["muted"]}; margin: 0 8px;')
        
        return {
            'container': step_row,
            'icon': icon_label,
            'name': name_label
        }
    
    def set_step(self, step_num: int, status: str = "active"):
        """
        Met à jour l'état d'une étape
        
        Args:
            step_num: 1, 2 ou 3
            status: "pending", "active", "completed"
        """
        if step_num not in self.step_elements:
            return
        
        elements = self.step_elements[step_num]
        
        if status == "active":
            self.current_step = step_num
            # Démarrer timer si étape 1
            if step_num == 1:
                self.start_time = time.time()
            
            # Style actif
            color = self._get_step_color(step_num)
            elements['icon'].style(f'font-size: 18px; opacity: 1;')
            elements['name'].style(f'color: {color}; font-weight: 600;')
            
        elif status == "completed":
            elements['icon'].style(f'font-size: 16px; opacity: 1;')
            elements['icon'].set_text('✓')
            elements['name'].style(f'color: {COLORS["text"]}; font-weight: 500;')
            
        else:  # pending
            elements['icon'].style(f'font-size: 16px; opacity: 0.5;')
            elements['name'].style(f'color: {COLORS["muted"]}; font-weight: 400;')
    
    def _get_step_color(self, step_num: int) -> str:
        """Retourne couleur pour étape"""
        colors = {
            1: COLORS["analysis"],
            2: COLORS["conscious"],
            3: COLORS["synthesis"]
        }
        return colors.get(step_num, COLORS["text"])
    
    def update_timer(self):
        """Met à jour le timer"""
        if self.start_time and self.timer_element:
            elapsed = int(time.time() - self.start_time)
            minutes = elapsed // 60
            seconds = elapsed % 60
            self.timer_element.set_text(f'{minutes}:{seconds:02d}')
    
    def reset(self):
        """Réinitialise la barre"""
        self.current_step = 0
        self.start_time = None
        for step_num in [1, 2, 3]:
            self.set_step(step_num, "pending")
        if self.timer_element:
            self.timer_element.set_text('0:00')


# ============================================================================
# INDICATEUR TYPING
# ============================================================================

class TypingIndicator:
    """Indicateur de saisie/réflexion animé"""
    
    def __init__(self):
        self.container = None
        self.dots_label = None
        self.message_label = None
        self.animation_task = None
        self.is_active = False
        
    def create(self, initial_message: str = "Réflexion en cours"):
        """Crée l'indicateur"""
        if not NICEGUI_AVAILABLE:
            return None
        
        with ui.row().classes('items-center gap-2').style(f'''
            padding: 8px 12px;
            background: rgba(59, 130, 246, 0.1);
            border-radius: 12px;
            border-left: 3px solid {COLORS["conscious"]};
        ''') as self.container:
            
            self.message_label = ui.label(initial_message).style(f'''
                color: {COLORS["text"]};
                font-size: 13px;
                font-style: italic;
            ''')
            
            self.dots_label = ui.label('').style(f'''
                color: {COLORS["conscious"]};
                font-weight: bold;
                width: 24px;
            ''')
        
        self.container.set_visibility(False)
        return self.container
    
    async def start(self, message: str = None):
        """Démarre l'animation"""
        if message:
            self.message_label.set_text(message)
        
        self.is_active = True
        if self.container:
            self.container.set_visibility(True)
        
        # Animation des points
        dots = ['', '.', '..', '...']
        i = 0
        while self.is_active:
            if self.dots_label:
                self.dots_label.set_text(dots[i % 4])
            i += 1
            await asyncio.sleep(0.4)
    
    def stop(self):
        """Arrête l'animation"""
        self.is_active = False
        if self.container:
            self.container.set_visibility(False)
    
    def set_role(self, role: str):
        """Change le style selon le rôle"""
        if role == "conscious":
            color = COLORS["conscious"]
            border_color = COLORS["conscious"]
        elif role == "unconscious":
            color = COLORS["unconscious"]
            border_color = COLORS["unconscious"]
        else:
            color = COLORS["text"]
            border_color = COLORS["muted"]
        
        if self.container:
            self.container.style(f'''
                padding: 8px 12px;
                background: rgba({self._hex_to_rgb(color)}, 0.1);
                border-radius: 12px;
                border-left: 3px solid {border_color};
            ''')
        if self.dots_label:
            self.dots_label.style(f'color: {color}; font-weight: bold; width: 24px;')
    
    def _hex_to_rgb(self, hex_color: str) -> str:
        """Convertit hex en rgb string"""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f'{r}, {g}, {b}'


# ============================================================================
# AFFICHAGE DIALOGUE
# ============================================================================

class DialogueDisplay:
    """
    Affichage du dialogue Conscient ↔ Inconscient avec coloration
    """
    
    def __init__(self):
        self.container = None
        self.messages = []
        
    def create(self):
        """Crée le conteneur de dialogue"""
        if not NICEGUI_AVAILABLE:
            return None
        
        with ui.column().classes('w-full gap-2').style(f'''
            background: {COLORS["background"]};
            padding: 16px;
            border-radius: 8px;
            max-height: 400px;
            overflow-y: auto;
        ''') as self.container:
            pass
        
        return self.container
    
    def add_message(self, role: str, content: str, step: int = 2):
        """
        Ajoute un message au dialogue
        
        Args:
            role: "conscious", "unconscious", "analysis", "synthesis", "error"
            content: Contenu du message
            step: Numéro d'étape (1, 2, 3)
        """
        if not NICEGUI_AVAILABLE or not self.container:
            return
        
        # Déterminer style selon rôle
        if role == "conscious":
            icon = "🧠"
            label = "Conscient"
            color = COLORS["conscious"]
            align = "items-start"
        elif role == "unconscious":
            icon = "🔮"
            label = "Inconscient"
            color = COLORS["unconscious"]
            align = "items-end"
        elif role == "analysis":
            icon = "🔍"
            label = "Analyse"
            color = COLORS["analysis"]
            align = "items-start"
        elif role == "error":
            # ERREUR EXPLICITE - pas de fallback silencieux
            icon = "❌"
            label = "Erreur"
            color = COLORS["error"]
            align = "items-center"
        else:  # synthesis
            icon = "✨"
            label = "Synthèse"
            color = COLORS["synthesis"]
            align = "items-start"
        
        with self.container:
            with ui.column().classes(f'w-full {align}').style('max-width: 85%;'):
                # Header
                with ui.row().classes('items-center gap-2'):
                    ui.label(f'{icon} {label}').style(f'''
                        color: {color};
                        font-weight: 600;
                        font-size: 12px;
                    ''')
                
                # Contenu
                with ui.card().style(f'''
                    background: rgba({self._hex_to_rgb(color)}, 0.1);
                    border-left: 3px solid {color};
                    padding: 12px;
                    border-radius: 8px;
                    margin-top: 4px;
                '''):
                    ui.markdown(content).style(f'''
                        color: {COLORS["text"]};
                        font-size: 13px;
                        line-height: 1.5;
                    ''')
        
        self.messages.append({'role': role, 'content': content, 'step': step})
    
    def _hex_to_rgb(self, hex_color: str) -> str:
        """Convertit hex en rgb string"""
        hex_color = hex_color.lstrip('#')
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f'{r}, {g}, {b}'
    
    def clear(self):
        """Vide le dialogue"""
        if self.container:
            self.container.clear()
        self.messages = []


# ============================================================================
# COMPOSANT PRINCIPAL - BOÎTE INTROSPECTION
# ============================================================================

class IntrospectionBox:
    """
    Boîte complète d'affichage introspection combinant:
    - Barre de progression
    - Indicateur typing
    - Affichage dialogue
    """
    
    def __init__(self):
        self.container = None
        self.progress_bar = IntrospectionProgressBar()
        self.typing_indicator = TypingIndicator()
        self.dialogue_display = DialogueDisplay()
        self.is_visible = False
        
    def create(self):
        """Crée la boîte complète"""
        if not NICEGUI_AVAILABLE:
            return None
        
        with ui.card().classes('w-full').style(f'''
            background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
            border: 1px solid #374151;
            border-radius: 12px;
            padding: 16px;
            margin: 8px 0;
        ''') as self.container:
            
            # Header
            with ui.row().classes('w-full items-center justify-between').style('margin-bottom: 12px;'):
                with ui.row().classes('items-center gap-2'):
                    ui.icon('psychology', size='24px').style(f'color: {COLORS["conscious"]};')
                    ui.label('Introspection').style(f'''
                        color: {COLORS["text"]};
                        font-size: 16px;
                        font-weight: 600;
                    ''')
                
                # Bouton réduire/fermer
                with ui.row().classes('gap-1'):
                    ui.button(icon='minimize', on_click=self.toggle_minimize).props(
                        'flat dense round size=sm'
                    ).style(f'color: {COLORS["muted"]};')
            
            # Barre de progression
            self.progress_bar.create()
            
            # Indicateur typing
            self.typing_indicator.create()
            
            # Zone dialogue
            self.dialogue_display.create()
        
        self.container.set_visibility(False)
        return self.container
    
    def show(self):
        """Affiche la boîte"""
        if self.container:
            self.container.set_visibility(True)
            self.is_visible = True
    
    def hide(self):
        """Masque la boîte"""
        if self.container:
            self.container.set_visibility(False)
            self.is_visible = False
    
    def toggle_minimize(self):
        """Bascule entre état réduit/étendu"""
        if self.dialogue_display.container:
            current = self.dialogue_display.container.visible
            self.dialogue_display.container.set_visibility(not current)
    
    def reset(self):
        """Réinitialise tout"""
        self.progress_bar.reset()
        self.typing_indicator.stop()
        self.dialogue_display.clear()
    
    # =========================================================================
    # API CALLBACKS POUR ENGINE
    # =========================================================================
    
    def on_step_start(self, step_num: int, step_name: str):
        """Callback: début d'étape"""
        # Marquer précédentes comme terminées
        for i in range(1, step_num):
            self.progress_bar.set_step(i, "completed")
        
        # Activer l'étape courante
        self.progress_bar.set_step(step_num, "active")
    
    def on_step_complete(self, step_num: int):
        """Callback: fin d'étape"""
        self.progress_bar.set_step(step_num, "completed")
    
    async def on_role_thinking(self, role: str, message: str = None):
        """Callback: un rôle réfléchit"""
        self.typing_indicator.set_role(role)
        
        if role == "conscious":
            msg = message or "Le Conscient réfléchit..."
        elif role == "unconscious":
            msg = message or "L'Inconscient consulte la mémoire..."
        else:
            msg = message or "Réflexion en cours..."
        
        await self.typing_indicator.start(msg)
    
    def on_role_done(self):
        """Callback: rôle a fini de réfléchir"""
        self.typing_indicator.stop()
    
    def on_message(self, step: int, role: str, content: str):
        """Callback: nouveau message dans le dialogue"""
        self.dialogue_display.add_message(role, content, step)
    
    def on_complete(self, success: bool = True):
        """Callback: introspection terminée"""
        self.typing_indicator.stop()
        if success:
            for i in range(1, 4):
                self.progress_bar.set_step(i, "completed")


# ============================================================================
# FACTORY FUNCTION
# ============================================================================

def create_introspection_box() -> Optional[IntrospectionBox]:
    """
    Crée et retourne une IntrospectionBox
    
    Returns:
        IntrospectionBox ou None si NiceGUI non disponible
    """
    if not NICEGUI_AVAILABLE:
        return None
    
    box = IntrospectionBox()
    box.create()
    return box


# Export
__all__ = [
    'IntrospectionBox',
    'IntrospectionProgressBar', 
    'TypingIndicator',
    'DialogueDisplay',
    'create_introspection_box',
    'COLORS'
]
