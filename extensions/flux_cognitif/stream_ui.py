"""
🎨 Flux Cognitif - Interface Utilisateur
==========================================

Overlay sombre avec relief profond type overlay paramètres affichant
le stream des événements cognitifs en temps réel.

Architecture:
- Écran latéral droit (400px largeur)
- Header avec titre + bouton fermer
- Zone scroll logs centrale
- Footer avec contrôles niveau + filtres

Esthétique: Relief profond enfoncé, ombres intérieures, sédimentation progressive
"""

from nicegui import ui
from typing import Optional, Callable
from datetime import datetime


class FluxCognitifUI:
    """Interface NiceGUI pour le flux cognitif"""
    
    def __init__(self, flux_instance):
        self.flux = flux_instance
        self.overlay_visible = False
        self.stream_container = None
        self.overlay_element = None
        self.level_buttons = []  # Références boutons niveau pour Phase 2
        self.filter_buttons = {}  # Références boutons filtres {source: button}
        self.last_event_count = 0  # Pour éviter rafraîchissement inutile
        self._force_refresh = False  # Flag pour forcer le rafraîchissement après toggle filtre/niveau
        
        # Icônes par source
        self.source_icons = {
            'archiviste': '🧠',
            'biography': '📖',
            'dream': '🌙',
            'journal': '📔',
            'directive': '🧭',
            'web': '🔍',
            'capability': '💡'
        }
        
        print("[FLUX-UI] ✅ Interface initialisée")
    
    def _is_overlay_valid(self) -> bool:
        """Vérifie si l'overlay est valide (client non supprimé)"""
        if self.overlay_element is None:
            return False
        try:
            # Tenter d'accéder au client pour vérifier s'il existe toujours
            _ = self.overlay_element.client
            return True
        except (RuntimeError, AttributeError):
            # Client supprimé ou élément invalide
            return False
    
    def create_overlay(self) -> ui.element:
        """Crée l'overlay avec effet relief profond"""
        
        # Injection CSS unique
        self._inject_inset_styles()
        
        # Conteneur principal overlay
        with ui.element('div').classes('flux-cognitif-overlay').style('display: none') as overlay:
            self.overlay_element = overlay
            
            # Header
            with ui.row().classes('flux-header'):
                ui.label('🧠 Flux Cognitif').classes('flux-title')
            
            # Zone logs (scroll)
            with ui.column().classes('flux-logs') as logs_container:
                self.stream_container = logs_container
            
            # Footer contrôles
            with ui.row().classes('flux-footer'):
                # Niveau (Phase 2: activé pour NORMAL et DEEP)
                ui.label('Niveau:').classes('flux-label')
                btn1 = ui.button('●', on_click=lambda: self._set_level(1)).classes('level-btn level-1 active').props('flat dense')
                btn1.tooltip('SURFACE : Événements basiques (injections, recherches)')
                btn2 = ui.button('○', on_click=lambda: self._set_level(2)).classes('level-btn level-2').props('flat dense')
                btn2.tooltip('NORMAL : + Dialogues Archiviste (prompts/réponses enrichissement)')
                btn3 = ui.button('○', on_click=lambda: self._set_level(3)).classes('level-btn level-3').props('flat dense')
                btn3.tooltip('DEEP : Tous les événements cognitifs (métacognition incluse)')
                self.level_buttons = [btn1, btn2, btn3]
                
                ui.separator().props('vertical')
                
                # Filtres catégories
                ui.label('Filtres:').classes('flux-label')
                
                # Définir descriptions filtres
                filter_descriptions = {
                    'archiviste': 'Archiviste : Enrichissement mémoire et souvenirs',
                    'biography': 'Biographie : Phrases magiques et extraction souvenirs',
                    'dream': 'Dream Engine : Rêves et métabolisme cognitif',
                    'journal': 'Journal de Bord : États quotidiens et humeur',
                    'directive': 'Directive : Conscience critique Archiviste (autonomie IA)',
                    'web': 'Web Navigator : Recherches et scraping web',
                    'capability': 'Capability Advisor : Conseils capacités modèles IA'
                }
                
                with ui.row().classes('flux-filters'):
                    for source, icon in self.source_icons.items():
                        is_active = self.flux.filters.get(source, False)
                        btn = ui.button(
                            icon, 
                            on_click=lambda s=source: self._toggle_filter(s)
                        ).props('flat dense').classes(f'filter-btn filter-{source}')
                        
                        # Ajouter tooltip
                        btn.tooltip(filter_descriptions.get(source, source.capitalize()))
                        
                        # Appliquer style selon état
                        if is_active:
                            btn.classes(add='filter-active')
                        else:
                            btn.classes(add='filter-inactive')
                        
                        # Stocker référence
                        self.filter_buttons[source] = btn
        
        # Timer pour rafraîchir les logs
        ui.timer(2.0, self._refresh_logs)
        
        return overlay
    
    def show_overlay(self):
        """Affiche l'overlay (recrée si nécessaire après F5)"""
        # Vérifier si l'overlay est valide (client non supprimé)
        if not self._is_overlay_valid():
            print("[FLUX-UI] ⚠️ Overlay invalide après F5, recréation...")
            self.overlay_element = None
            self.stream_container = None
            self.create_overlay()
        
        if self.overlay_element:
            try:
                self.overlay_element.style('display: flex')
                self.overlay_visible = True
                # Forcer rafraîchissement à l'ouverture pour afficher derniers événements
                self._force_refresh = True
                self._refresh_logs()
                print("[FLUX-UI] ✅ Overlay affiché")
            except RuntimeError as e:
                print(f"[FLUX-UI] ❌ Erreur affichage overlay: {e}")
                # Réinitialiser pour prochaine tentative
                self.overlay_element = None
                self.stream_container = None
    
    def hide_overlay(self):
        """Masque l'overlay"""
        if self._is_overlay_valid():
            try:
                self.overlay_element.style('display: none')
                self.overlay_visible = False
                print("[FLUX-UI] ✅ Overlay masqué")
            except RuntimeError as e:
                print(f"[FLUX-UI] ⚠️ Erreur masquage overlay (client supprimé): {e}")
                self.overlay_visible = False
    
    def toggle_overlay(self):
        """Bascule affichage overlay"""
        if self.overlay_visible:
            self.hide_overlay()
        else:
            self.show_overlay()
    
    def _set_level(self, level: int):
        """Change le niveau d'introspection (Phase 2: NORMAL, Phase 3: DEEP)"""
        # Vérifier validité de l'overlay
        if not self._is_overlay_valid():
            print("[FLUX-UI] ⚠️ Client invalide dans _set_level, skip")
            return
        
        # Mettre à jour le flux cognitif
        self.flux.set_level(level)
        
        # Mettre à jour apparence boutons (avec protection)
        try:
            for i, btn in enumerate(self.level_buttons, start=1):
                if i == level:
                    btn.set_text('●')
                    btn.classes(remove='level-inactive', add='active')
                else:
                    btn.set_text('○')
                    btn.classes(remove='active', add='level-inactive')
        except RuntimeError as e:
            print(f"[FLUX-UI] ⚠️ Erreur mise à jour boutons niveau: {e}")
        
        # Forcer rafraîchissement (changement niveau affecte les événements visibles)
        self._force_refresh = True
        self._refresh_logs()
        
        level_names = {1: 'SURFACE', 2: 'NORMAL', 3: 'DEEP'}
        print(f"[FLUX-UI] ✅ Niveau défini: {level} ({level_names.get(level, 'INCONNU')})")
    
    def _toggle_filter(self, source: str):
        """Active/désactive un filtre avec feedback visuel"""
        # Vérifier validité de l'overlay
        if not self._is_overlay_valid():
            print("[FLUX-UI] ⚠️ Client invalide dans _toggle_filter, skip")
            return
        
        current = self.flux.filters.get(source, True)
        new_state = not current
        self.flux.set_filter(source, new_state)
        
        # Mettre à jour apparence bouton (avec protection)
        try:
            if source in self.filter_buttons:
                btn = self.filter_buttons[source]
                if new_state:  # Filtre activé
                    btn.classes(remove='filter-inactive', add='filter-active')
                else:  # Filtre désactivé
                    btn.classes(remove='filter-active', add='filter-inactive')
        except RuntimeError as e:
            print(f"[FLUX-UI] ⚠️ Erreur mise à jour bouton filtre: {e}")
        
        # Forcer rafraîchissement (changement filtre affecte les événements visibles)
        self._force_refresh = True
        self._refresh_logs()
    
    def _refresh_logs(self):
        """Rafraîchit l'affichage des logs (uniquement si nouveaux événements)"""
        if not self.stream_container or not self.overlay_visible:
            return
        
        # Vérifier validité du client avant toute opération DOM
        if not self._is_overlay_valid():
            print("[FLUX-UI] ⚠️ Client invalide détecté dans _refresh_logs, skip")
            return
        
        # Recuperer evenements filtres par sources et niveau actifs
        events = self.flux.get_filtered_events(limit=20)
        
        # Ne rafraichir que si le total d'evenements a change ou refresh force
        total_events = len(self.flux.events)
        if not self._force_refresh and total_events == self.last_event_count:
            return  # Pas de changement, garder l'affichage actuel
        
        self._force_refresh = False
        self.last_event_count = total_events
        
        # Vider container seulement si changement (avec protection)
        try:
            self.stream_container.clear()
        except RuntimeError as e:
            print(f"[FLUX-UI] ❌ Erreur clear container (client supprimé): {e}")
            return
        
        if not events:
            with self.stream_container:
                # Message d'aide pour diagnostiquer pourquoi vide
                active_filters = [src for src, enabled in self.flux.filters.items() if enabled]
                level_name = {1: 'SURFACE', 2: 'NORMAL', 3: 'DEEP'}.get(self.flux.level, '?')
                
                if not active_filters:
                    ui.label('⚠️ Tous les filtres sont désactivés').classes('flux-empty').style('color: #ff9800')
                    ui.label('Cliquez sur les icônes 🧠📖🌙📔.. pour activer').classes('flux-empty').style('font-size: 0.5rem; margin-top: 5px')
                else:
                    ui.label('Aucun événement récent').classes('flux-empty')
                    ui.label(f'Niveau {level_name} • {len(active_filters)} filtres actifs').classes('flux-empty').style('font-size: 0.5rem; margin-top: 5px')
            return
        
        # Afficher événements (du plus ancien au plus récent)
        with self.stream_container:
            for i, event in enumerate(events):
                age_class = self._get_age_class(i, len(events))
                self._render_log_card(event, age_class)
        
        # Auto-scroll vers bas
        ui.run_javascript('''
            const container = document.querySelector('.flux-logs');
            if (container) {
                container.scrollTop = container.scrollHeight;
            }
        ''')
    
    def _get_age_class(self, index: int, total: int) -> str:
        """Calcule la classe CSS selon l'ancienneté (effet sédimentation)"""
        position = index / max(total - 1, 1)  # 0.0 (ancien) → 1.0 (récent)
        
        if position < 0.3:
            return 'log-ancient'  # Très ancien (opacité 0.3)
        elif position < 0.6:
            return 'log-old'  # Ancien (opacité 0.6)
        else:
            return 'log-recent'  # Récent (opacité 1.0)
    
    def _render_log_card(self, event: dict, age_class: str):
        """Affiche une carte log avec niveau Phase 1/2/3 et support multi-lignes"""
        source = event['source']
        icon = self.source_icons.get(source, '▪️')
        time_str = event['timestamp'].strftime('%H:%M:%S')
        message = event['message']
        level = event.get('level', 1)
        metadata = event.get('metadata', {})
        
        # Escape HTML et convertir \n en <br/>
        import html as _html
        message_html = _html.escape(message).replace('\n', '<br/>')
        
        # Badge niveau pour Phase 2+
        level_badge = ''
        card_class = 'log-card'
        if level == 2:
            level_badge = '<span class="level-badge level-2">NORMAL</span>'
            card_class += ' log-level-2'
        elif level == 3:
            level_badge = '<span class="level-badge level-3">DEEP</span>'
            card_class += ' log-level-3'
        
        with ui.card().classes(f'{card_class} {age_class}'):
            # Header avec badge niveau
            ui.html(f'''
                <div class="log-header">
                    <span class="log-icon">{icon}</span>
                    <span class="log-time">{time_str}</span>
                    {level_badge}
                    <span class="log-source">{source.title()}</span>
                </div>
                <div class="log-message">{message_html}</div>
            ''')
            
            # Phase 2+ : Afficher détails metadata (prompt, response)
            if level >= 2 and metadata:
                with ui.expansion('Détails', icon='info').classes('log-details-expansion'):
                    details_html = ''
                    
                    # Prompt
                    if 'prompt' in metadata:
                        prompt = metadata['prompt']
                        preview = prompt[:200] + '...' if len(prompt) > 200 else prompt
                        details_html += f'<div class="detail-section"><strong>📝 Prompt:</strong><br/><pre class="detail-text">{preview}</pre></div>'
                    
                    # Réponse JSON enrichie
                    if 'enriched_json' in metadata:
                        import json
                        enriched = metadata['enriched_json']
                        json_preview = json.dumps(enriched, indent=2, ensure_ascii=False)[:300] + '...'
                        details_html += f'<div class="detail-section"><strong>✅ JSON:</strong><br/><pre class="detail-text">{json_preview}</pre></div>'
                    
                    # Réponse brute
                    elif 'raw_response' in metadata:
                        response = metadata['raw_response']
                        preview = response[:200] + '...' if len(response) > 200 else response
                        details_html += f'<div class="detail-section"><strong>📄 Réponse:</strong><br/><pre class="detail-text">{preview}</pre></div>'
                    
                    ui.html(details_html)
    
    def _inject_inset_styles(self):
        """Injecte les styles CSS avec effet enfoncement profond"""
        ui.add_head_html('''
        <style>
        /* Overlay principal - Effet enfoncement profond dans l'écran */
        .flux-cognitif-overlay {
            position: fixed;
            top: 80px;
            right: 10px;
            width: 200px;
            height: calc((100vh - 60px) * 0.7);
            
            /* Fond sombre profond avec gradient subtil */
            background: 
                linear-gradient(135deg, 
                    rgba(15, 15, 20, 0.95) 0%,
                    rgba(10, 10, 15, 0.98) 50%,
                    rgba(8, 8, 12, 0.95) 100%
                );
            
            backdrop-filter: blur(12px) saturate(120%);
            -webkit-backdrop-filter: blur(12px) saturate(120%);
            
            /* Bordures pour effet 3D */
            border: 1px solid rgba(60, 60, 70, 0.6);
            border-top: 1px solid rgba(40, 40, 50, 0.5);
            border-bottom: 1px solid rgba(10, 10, 15, 0.8);
            border-right: 1px solid rgba(60, 60, 70, 0.6);
            border-radius: 12px;
            
            /* OMBRES INTÉRIEURES multiples pour effet enfoncement profond */
            box-shadow: 
                /* Ombre extérieure pour détacher du fond */
                -12px 0 40px rgba(0, 0, 0, 0.7),
                /* Ombres intérieures - effet creusé */
                inset 8px 8px 20px rgba(0, 0, 0, 0.6),
                inset -2px -2px 12px rgba(0, 0, 0, 0.5),
                inset 0px 4px 16px rgba(0, 0, 0, 0.7),
                inset 0px -4px 10px rgba(0, 0, 0, 0.4),
                /* Reflet subtil pour réalisme */
                inset -1px 0px 2px rgba(100, 100, 120, 0.1);
            
            animation: slideInRight 0.3s ease-out;
            
            display: flex;
            flex-direction: column;
            z-index: 999;
        }
        
        @keyframes slideInRight {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        /* Header */
        .flux-header {
            padding: 8px 10px;
            border-bottom: 1px solid rgba(80, 80, 100, 0.3);
            background: rgba(20, 20, 30, 0.5);
            justify-content: space-between;
            align-items: center;
            /* Ombre interne header pour continuité effet */
            box-shadow: inset 0 4px 8px rgba(0, 0, 0, 0.4);
        }
        
        .flux-title {
            font-size: 0.7rem;
            font-weight: 600;
            color: #B8C5DB;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.5);
        }
        
        .flux-close-btn {
            color: rgba(160, 170, 190, 0.6);
        }
        
        /* Zone logs */
        .flux-logs {
            flex: 1;
            overflow-y: auto;
            overflow-x: hidden;
            padding: 6px 8px;
            gap: 5px;
            /* Ombre interne pour effet creusé */
            box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.4);
        }
        
        .flux-logs::-webkit-scrollbar {
            width: 6px;
        }
        .flux-logs::-webkit-scrollbar-track {
            background: transparent;
        }
        .flux-logs::-webkit-scrollbar-thumb {
            background: rgba(0, 212, 245, 0.12);
            border-radius: 3px;
        }
        
        /* Message vide */
        .flux-empty {
            color: rgba(140, 150, 170, 0.4);
            text-align: center;
            margin-top: 20px;
            font-style: italic;
            font-size: 0.6rem;
        }
        
        /* Footer */
        .flux-footer {
            padding: 6px 8px;
            border-top: 1px solid rgba(80, 80, 100, 0.3);
            background: rgba(20, 20, 30, 0.5);
            font-size: 0.55rem;
            color: #B8C5DB;
            gap: 6px;
            align-items: center;
            flex-wrap: wrap;
            /* Ombre interne footer pour continuité effet */
            box-shadow: inset 0 -4px 8px rgba(0, 0, 0, 0.4);
        }
        
        .flux-label {
            color: rgba(150, 160, 180, 0.8);
            font-weight: 500;
            font-size: 0.55rem;
        }
        
        .level-btn {
            min-width: 20px;
            height: 20px;
            border-radius: 50%;
            color: rgba(140, 150, 170, 0.5);
            font-size: 0.55rem;
        }
        .level-btn.active {
            color: #A8B8D0 !important;
            background: rgba(60, 70, 90, 0.4) !important;
            box-shadow: 
                0 0 12px rgba(100, 120, 160, 0.3),
                inset 0 0 4px rgba(0, 0, 0, 0.4);
        }
        
        .flux-filters {
            gap: 2px;
        }
        
        .filter-btn {
            font-size: 0.75rem;
            min-width: 24px;
            height: 24px;
            opacity: 1;
            filter: drop-shadow(0 0 4px rgba(80, 100, 140, 0.3));
            transition: all 0.3s ease;
        }
        
        /* États filtres */
        .filter-btn.filter-active {
            opacity: 1;
            transform: scale(1);
            background: rgba(60, 70, 90, 0.3) !important;
            box-shadow: 
                0 0 8px rgba(100, 120, 160, 0.4),
                inset 0 0 4px rgba(0, 0, 0, 0.3);
        }
        
        .filter-btn.filter-inactive {
            opacity: 0.3;
            transform: scale(0.85);
            filter: grayscale(0.8) drop-shadow(0 0 2px rgba(80, 100, 140, 0.1));
        }
        
        .filter-btn.filter-inactive:hover {
            opacity: 0.6;
            transform: scale(0.95);
        }
        
        /* Carte log */
        .log-card {
            background: rgba(25, 25, 35, 0.6);
            border-left: 2px solid rgba(70, 80, 100, 0.5);
            border-radius: 4px;
            padding: 5px 6px;
            font-family: 'Fira Code', 'Consolas', monospace;
            font-size: 0.55rem;
            color: #C5D0E6;
            transition: opacity 0.4s ease-out;
            /* Ombre interne pour effet relief */
            box-shadow: inset 2px 2px 4px rgba(0, 0, 0, 0.4);
        }
        
        .log-card.log-ancient {
            opacity: 0.3;
        }
        
        .log-card.log-old {
            opacity: 0.6;
        }
        
        .log-card.log-recent {
            opacity: 1.0;
        }
        
        .log-header {
            display: flex;
            align-items: center;
            gap: 4px;
            margin-bottom: 4px;
        }
        
        .log-icon {
            font-size: 0.75rem;
            filter: drop-shadow(0 0 4px rgba(80, 100, 140, 0.3));
        }
        
        .log-time {
            color: rgba(120, 130, 150, 0.6);
            font-size: 0.5rem;
        }
        
        .log-source {
            color: rgba(160, 175, 200, 0.9);
            font-weight: 500;
            font-size: 0.55rem;
        }
        
        .log-message {
            padding-left: 18px;
            color: #C5D0E6;
            line-height: 1.2;
            font-size: 0.55rem;
            word-wrap: break-word;
            overflow-wrap: break-word;
        }
        
        /* Phase 2+ - Badges niveau */
        .level-badge {
            font-size: 0.45rem;
            padding: 1px 3px;
            border-radius: 3px;
            font-weight: 600;
            text-transform: uppercase;
            margin-left: 3px;
            box-shadow: inset 1px 1px 2px rgba(0, 0, 0, 0.3);
        }
        .level-badge.level-2 {
            background: rgba(70, 110, 180, 0.4);
            color: #87CEEB;
            border: 1px solid rgba(70, 110, 180, 0.6);
        }
        .level-badge.level-3 {
            background: rgba(100, 40, 180, 0.4);
            color: #C084FC;
            border: 1px solid rgba(100, 40, 180, 0.6);
        }
        
        /* Phase 2+ - Cartes enrichies */
        .log-card.log-level-2 {
            border-left-color: rgba(70, 110, 180, 0.7);
            background: rgba(70, 110, 180, 0.08);
            box-shadow: inset 2px 2px 4px rgba(0, 0, 0, 0.4);
        }
        .log-card.log-level-3 {
            border-left-color: rgba(100, 40, 180, 0.7);
            background: rgba(100, 40, 180, 0.08);
            box-shadow: inset 2px 2px 4px rgba(0, 0, 0, 0.4);
        }
        
        /* Phase 2+ - Expansion détails */
        .log-details-expansion {
            margin-top: 5px;
            font-size: 0.5rem;
        }
        .detail-section {
            margin-bottom: 4px;
            color: rgba(150, 165, 190, 0.8);
            font-size: 0.5rem;
        }
        .detail-text {
            background: rgba(0, 0, 0, 0.4);
            padding: 3px 5px;
            border-radius: 3px;
            font-size: 0.48rem;
            overflow: auto;
            box-shadow: inset 1px 1px 3px rgba(0, 0, 0, 0.5);
            max-height: 100px;
            color: #C5D0E6;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        </style>
        ''')



# Instance globale UI
_flux_ui_instance: Optional[FluxCognitifUI] = None


def create_flux_ui(flux_instance) -> FluxCognitifUI:
    """Crée l'interface UI du flux cognitif"""
    global _flux_ui_instance
    # Recréer si instance inexistante OU overlay invalide (après F5/refresh)
    if _flux_ui_instance is None or not _flux_ui_instance._is_overlay_valid():
        if _flux_ui_instance is not None:
            print("[FLUX-UI] Recréation singleton (overlay invalide apres refresh)")
        _flux_ui_instance = FluxCognitifUI(flux_instance)
        _flux_ui_instance.create_overlay()
    return _flux_ui_instance


def get_flux_ui() -> Optional[FluxCognitifUI]:
    """Retourne l'instance UI active"""
    return _flux_ui_instance
