"""
Composants d'interface utilisateur pour l'extension Web Navigator

Interface de configuration dans les paramètres OGMA (NiceGUI)
"""

from typing import Dict, Any, Optional, Callable

try:
    from utils.i18n import t
except Exception:
    def t(key, **kwargs):
        return key

try:
    import importlib
    _ng = importlib.import_module('nicegui')
    _ui = getattr(_ng, 'ui', None)
except Exception:
    _ui = None

class _Dummy:
    """Dummy pour éviter erreurs quand NiceGUI absent"""
    def __getattr__(self, name): return _Dummy()
    def __call__(self, *args, **kwargs): return _Dummy()

ui: Any = _ui if _ui is not None else _Dummy()

class WebNavigatorUI:
    """Interface utilisateur pour l'extension Web Navigator avec Serper"""
    
    def __init__(self, config, commands_handler):
        self.config = config
        self.commands_handler = commands_handler
        
        # Éléments UI (seront créés dynamiquement)
        self.provider_select = None
        self.enabled_switch = None
        self.api_key_input = None
        self.api_status_label = None
        self.web_search_switch = None  
        self.news_search_switch = None
        self.image_search_switch = None
        self.scholar_search_switch = None
        self.results_per_query_input = None
        self.language_select = None
        self.country_select = None
        self.timeout_input = None
        self.rate_limit_input = None
        self.save_images_switch = None
        self.stats_container = None
        
        print("[WEB-NAV-UI] 🎨 Interface utilisateur Serper initialisée")
    
    def create_settings_panel(self, container) -> None:
        """Crée le panel de paramètres dans les paramètres généraux OGMA"""
        
        with container:
            # En-tête de l'extension
            ui.markdown(t('wn_title'))
            ui.markdown(t('wn_subtitle'))
            ui.separator()

            # ── SÉLECTEUR DE MOTEUR DE RECHERCHE ──────────────────────────────
            with ui.card().classes('w-full mb-4').style(
                'background: rgba(46, 204, 113, 0.1); border: 1px solid rgba(46, 204, 113, 0.4);'
            ):
                ui.markdown(t('wn_section_provider')).style('color: #27ae60; font-weight: bold;')
                with ui.row().classes('w-full items-center gap-4'):
                    self.provider_select = ui.select(
                        label=t('wn_label_provider'),
                        options={
                            "serper": t('wn_provider_serper'),
                            "duckduckgo": t('wn_provider_duckduckgo'),
                        },
                        value=self.config.get_search_provider()
                    ).on_value_change(self._on_provider_changed).classes('flex-1')
                ui.markdown(
                    t('wn_provider_explain')
                ).style('color: #7f8c8d; font-size: 0.85em;')

            # Section clé API
            with ui.card().classes('w-full mb-4').style('background: rgba(52, 152, 219, 0.1); border: 1px solid rgba(52, 152, 219, 0.3);'):
                ui.markdown(t('wn_section_api')).style('color: #3498db; font-weight: bold;')
                ui.markdown(t('wn_steps_intro'))
                ui.markdown(t('wn_step_1'))
                ui.markdown(t('wn_step_2'))
                ui.markdown(t('wn_step_3'))
                ui.markdown(t('wn_step_4'))
                ui.markdown(t('wn_free_quota')).style('color: #27ae60; font-weight: bold;')
                
                with ui.row().classes('w-full items-center mb-2'):
                    try:
                        from api_keys_vault_ui import api_key_status_indicator, VirtualKeyInput
                        api_key_status_indicator('Serper', t('wn_label_api_key'))
                        # Remplacement transparent pour la configuration
                        self.api_key_input = VirtualKeyInput(lambda: "Serper")
                    except ImportError:
                        pass
                        
                    ui.button(
                        t('wn_btn_test'),
                        on_click=self._test_serper_connection
                    ).classes('bg-blue-500 ml-auto')
                    
                self.api_status_label = ui.label().classes('mt-2')
                self._update_api_status()
            
            # Section activation
            with ui.card().classes('w-full mb-4'):
                ui.markdown(t('wn_section_activation'))
                
                with ui.row().classes('w-full items-center'):
                    self.enabled_switch = ui.switch(
                        t('wn_switch_enabled'),
                        value=self.config.is_enabled()
                    ).on_value_change(self._on_enabled_changed)
                    
                with ui.row().classes('w-full items-center'):
                    self.web_search_switch = ui.switch(
                        t('wn_switch_web'),
                        value=self.config.is_web_search_enabled()
                    ).on_value_change(self._on_web_search_changed)
                    
                with ui.row().classes('w-full items-center'):
                    self.news_search_switch = ui.switch(
                        t('wn_switch_news'),
                        value=self.config.is_news_search_enabled()
                    ).on_value_change(self._on_news_search_changed)
                    
                with ui.row().classes('w-full items-center'):
                    self.image_search_switch = ui.switch(
                        t('wn_switch_image'),
                        value=self.config.is_image_search_enabled()
                    ).on_value_change(self._on_image_search_changed)
            
            # Section paramètres de recherche Serper
            with ui.card().classes('w-full mb-4'):
                ui.markdown(t('wn_section_params'))
                
                with ui.row().classes('w-full gap-4'):
                    self.results_per_query_input = ui.number(
                        t('wn_label_results_per_query'),
                        value=self.config.get_results_per_query(),
                        min=1,
                        max=20,
                        step=1
                    ).on_value_change(self._on_results_per_query_changed).classes('flex-1')
                    
                    self.language_select = ui.select(
                        label=t('wn_label_language'),
                        options={"fr": "Français", "en": "English", "es": "Español", "de": "Deutsch"},
                        value=self.config.get_language(),
                        on_change=self._on_language_changed
                    ).classes('flex-1')
                    
                    self.country_select = ui.select(
                        label=t('wn_label_country'), 
                        options={"fr": "France", "us": "United States", "gb": "United Kingdom", "de": "Germany"},
                        value=self.config.get_country(),
                        on_change=self._on_country_changed
                    ).classes('flex-1')
                
                with ui.row().classes('w-full gap-4'):
                    self.timeout_input = ui.number(
                        t('wn_label_timeout'),
                        value=self.config.get_request_timeout(),
                        min=5,
                        max=60,
                        step=5
                    ).on_value_change(self._on_timeout_changed).classes('flex-1')
                    
                    self.rate_limit_input = ui.number(
                        t('wn_label_rate_limit'),
                        value=self.config.get_rate_limit(),
                        min=0.5,
                        max=10.0,
                        step=0.5
                    ).on_value_change(self._on_rate_limit_changed).classes('flex-1')
            
            # Section gestion des images
            with ui.card().classes('w-full mb-4'):
                ui.markdown(t('wn_section_images'))
                
                with ui.row().classes('w-full items-center'):
                    self.save_images_switch = ui.switch(
                        t('wn_switch_save_images'),
                        value=self.config.get("save_downloaded_images", True)
                    ).on_value_change(self._on_save_images_changed)
                
                ui.markdown(t('wn_label_save_dir', dir=self.config.get('image_save_directory', 'data/uploads')))
                ui.markdown(t('wn_label_formats', formats=', '.join(self.config.get_supported_image_formats())))
                ui.markdown(t('wn_label_max_size', size=self.config.get('max_image_size_mb', 10.0)))
            
            # Section statistiques
            self.stats_container = ui.card().classes('w-full mb-4')
            self._update_stats_display()
            
            # Section commandes et aide
            with ui.card().classes('w-full mb-4'):
                ui.markdown(t('wn_section_commands'))
                
                with ui.column().classes('w-full'):
                    ui.markdown(t('wn_help_block'))
                
                # Boutons d'action
                with ui.row().classes('w-full gap-2'):
                    ui.button(
                        t('wn_btn_save_all'),
                        on_click=self._save_all_settings
                    ).classes('bg-green-600 text-white font-bold')
                    
                    ui.button(
                        t('wn_btn_refresh_stats'),
                        on_click=self._update_stats_display
                    ).classes('bg-blue-500')
                    
                    ui.button(
                        t('wn_btn_reset_config'),
                        on_click=self._reset_config
                    ).classes('bg-orange-500')
                    
                    ui.button(
                        t('wn_btn_test_api'), 
                        on_click=self._test_serper_connection
                    ).classes('bg-green-500')
    
    def _on_provider_changed(self, event):
        """Gestionnaire changement de moteur de recherche actif"""
        value = event.value
        success = self.config.set("search_provider", value)
        if success:
            label = "DuckDuckGo (gratuit)" if value == "duckduckgo" else "Serper (API)"
            ui.notify(t('wn_notify_provider_set', label=label), type='positive')
        else:
            ui.notify(t('wn_notify_provider_save_err'), type='negative')

    def _on_enabled_changed(self, event):
        """Gestionnaire changement activation générale"""
        value = event.value
        success = self.config.set("enabled", value)
        if success:
            ui.notify(
                f"Extension Web Navigator {'activée' if value else 'désactivée'}",
                type='positive' if value else 'info'
            )
        else:
            ui.notify(t('wn_notify_save_err'), type='negative')
            if self.enabled_switch:
                self.enabled_switch.value = not value
    
    def _on_api_key_changed(self, event):
        """Gestionnaire changement clé API Serper"""
        # Juste mettre à jour le statut, ne pas sauver automatiquement
        self._update_api_status()
    
    def _save_api_key(self):
        """Sauvegarde explicite de la clé API"""
        if not self.api_key_input:
            return
            
        value = self.api_key_input.value.strip() if self.api_key_input.value else ""
        
        if value:
            success = self.config.set("serper_api_key", value)
            if success:
                ui.notify(t('wn_notify_api_saved'), type='positive')
                self._update_api_status()
            else:
                ui.notify(t('wn_notify_api_save_err'), type='negative')
        else:
            self.config.set("serper_api_key", "")
            ui.notify(t('wn_notify_api_removed'), type='info')
            self._update_api_status()
    
    def _update_api_status(self):
        """Met à jour l'affichage du statut de l'API"""
        if not self.api_status_label:
            return
            
        try:
            import api_keys_vault
            current_key = api_keys_vault.get_api_key("Serper")
        except ImportError:
            current_key = self.api_key_input.value.strip() if hasattr(self, 'api_key_input') and self.api_key_input and hasattr(self.api_key_input, 'value') and self.api_key_input.value else ""
            
        if not current_key:
            status = "❌ Aucune clé API saisie dans le Coffre-Fort"
            color = "text-red-400"
        elif len(current_key) < 10:
            status = "⚠️ Clé API trop courte (minimum 10 caractères)"
            color = "text-orange-400"
        elif self.config.has_valid_api_key():
            status = "✅ Clé API valide et sauvegardée dans le Coffre-Fort"
            color = "text-green-400"
        else:
            status = "❌ Clé API invalide"
            color = "text-red-400"
            
        self.api_status_label.text = status
        self.api_status_label.classes(f'{color} font-medium')
    
    def _on_web_search_changed(self, event):
        """Gestionnaire changement recherche web"""
        value = event.value
        success = self.config.set("web_search_enabled", value)
        if success:
            ui.notify(
                f"Recherche web {'activée' if value else 'désactivée'}",
                type='positive' if value else 'info'
            )
    
    def _on_news_search_changed(self, event):
        """Gestionnaire changement recherche actualités"""
        value = event.value
        success = self.config.set("news_search_enabled", value)
        if success:
            ui.notify(
                f"Recherche actualités {'activée' if value else 'désactivée'}",
                type='positive' if value else 'info'
            )
    
    def _on_image_search_changed(self, event):
        """Gestionnaire changement recherche images"""
        value = event.value
        success = self.config.set("image_search_enabled", value)
        if success:
            ui.notify(
                f"Recherche images {'activée' if value else 'désactivée'}",
                type='positive' if value else 'info'
            )
    
    def _on_results_per_query_changed(self, event):
        """Gestionnaire changement nombre de résultats"""
        value = event.value
        if value and value > 0:
            success = self.config.set("results_per_query", value)
            if success:
                ui.notify(t('wn_notify_results_per_query', value=value), type='positive')
    
    def _on_language_changed(self, event):
        """Gestionnaire changement langue"""
        value = event.value
        if value:
            success = self.config.set("language", value)
            if success:
                ui.notify(t('wn_notify_language', value=value), type='positive')
    
    def _on_country_changed(self, event):
        """Gestionnaire changement pays"""
        value = event.value
        if value:
            success = self.config.set("country", value)
            if success:
                ui.notify(t('wn_notify_country', value=value), type='positive')
    
    def _on_timeout_changed(self, event):
        """Gestionnaire changement timeout"""
        value = event.value
        if value and value > 0:
            success = self.config.set("request_timeout", value)
            if success:
                ui.notify(t('wn_notify_timeout', value=value), type='positive')
    
    def _on_rate_limit_changed(self, event):
        """Gestionnaire changement rate limit"""
        value = event.value
        if value and value > 0:
            success = self.config.set("rate_limit_seconds", value)
            if success:
                ui.notify(t('wn_notify_rate_limit', value=value), type='positive')
    
    def _on_save_images_changed(self, event):
        """Gestionnaire changement sauvegarde images"""
        value = event.value
        success = self.config.set("save_downloaded_images", value)
        if success:
            ui.notify(
                f"Sauvegarde images {'activée' if value else 'désactivée'}",
                type='positive' if value else 'info'
            )
    
    def _update_stats_display(self):
        """Met à jour l'affichage des statistiques Serper"""
        if not self.stats_container:
            return
        
        with self.stats_container:
            self.stats_container.clear()
            ui.markdown(t('wn_section_stats'))
            
            stats = self.commands_handler.get_stats()
            
            with ui.row().classes('w-full gap-4'):
                with ui.column().classes('flex-1'):
                    ui.markdown(t('wn_stat_web', n=stats.get('web_searches', 0)))
                    ui.markdown(t('wn_stat_news', n=stats.get('news_searches', 0)))
                
                with ui.column().classes('flex-1'):
                    ui.markdown(t('wn_stat_image', n=stats.get('image_searches', 0)))
                    ui.markdown(t('wn_stat_image_dl', n=stats.get('image_downloads', 0)))
                
                with ui.column().classes('flex-1'):
                    ui.markdown(t('wn_stat_success', n=stats.get('successful_requests', 0)))
                    ui.markdown(t('wn_stat_errors', n=stats.get('errors', 0)))
                    ui.markdown(t('wn_stat_last_used', value=stats.get('last_used', t('wn_stat_never'))))
    
    def _reset_config(self):
        """Remet la configuration aux valeurs par défaut"""
        success = self.config.reset_to_defaults()
        if success:
            ui.notify(t('wn_notify_reset_ok'), type='positive')
            # Recharger les valeurs dans l'interface
            self._reload_ui_values()
        else:
            ui.notify(t('wn_notify_reset_err'), type='negative')
    
    def _reload_ui_values(self):
        """Recharge les valeurs dans l'interface après reset"""
        if self.enabled_switch:
            self.enabled_switch.value = self.config.is_enabled()
        # L'input est maintenant géré par le vault, pas besoin de le recharger ici
        if self.web_search_switch:
            self.web_search_switch.value = self.config.is_web_search_enabled()
        if self.news_search_switch:
            self.news_search_switch.value = self.config.is_news_search_enabled()
        if self.image_search_switch:
            self.image_search_switch.value = self.config.is_image_search_enabled()
        if self.results_per_query_input:
            self.results_per_query_input.value = self.config.get_results_per_query()
        if self.language_select:
            self.language_select.value = self.config.get_language()
        if self.country_select:
            self.country_select.value = self.config.get_country()
        if self.timeout_input:
            self.timeout_input.value = self.config.get_request_timeout()
        if self.rate_limit_input:
            self.rate_limit_input.value = self.config.get_rate_limit()
        if self.save_images_switch:
            self.save_images_switch.value = self.config.get("save_downloaded_images", True)
        
        # Mettre à jour le statut de l'API
        self._update_api_status()
    
    def _test_serper_connection(self):
        """Test de connexion à l'API Serper"""
        if not self.config.has_valid_api_key():
            ui.notify(t('wn_notify_api_missing'), type='negative')
            return
        
        try:
            # Test simple avec l'API Serper
            from .serper_client import SerperClient
            client = SerperClient(self.config)
            
            # Test recherche simple
            response, error = client.search_web("test")
            
            if error:
                ui.notify(t('wn_notify_api_test_failed', error=error), type='negative')
            else:
                ui.notify(t('wn_notify_api_ok'), type='positive')
                
        except Exception as e:
            ui.notify(t('wn_notify_api_test_err', err=str(e)), type='negative')
    
    def _save_all_settings(self):
        """Sauvegarde tous les paramètres de l'extension"""
        try:
            # Sauver la clé API si elle a été modifiée
            if self.api_key_input and self.api_key_input.value:
                current_key = self.api_key_input.value.strip()
                if current_key != self.config.get_serper_api_key():
                    self.config.set("serper_api_key", current_key)
            
            # Forcer la sauvegarde de tous les paramètres
            if hasattr(self.config, 'settings_manager') and self.config.settings_manager:
                self.config.settings_manager.save_settings()
                ui.notify(t('wn_notify_all_saved'), type='positive')
                self._update_api_status()
            else:
                ui.notify(t('wn_notify_no_manager'), type='warning')
                
        except Exception as e:
            ui.notify(t('wn_notify_save_all_err', err=str(e)), type='negative')

# ========== SPINNER RECHERCHE WEB DANS LE CHAT ==========
_web_search_spinner_container = None


def show_web_search_spinner_in_chat():
    """Affiche un spinner 'Recherche en cours...' dans la zone de chat OGMA."""
    global _web_search_spinner_container
    try:
        from nicegui import ui as _nicegui_ui
        import sys
        ogma_ng = sys.modules.get('ogma_ng')
        if ogma_ng:
            chat_inner = getattr(ogma_ng, '_chat_inner', None)
            if chat_inner:
                with chat_inner:
                    _web_search_spinner_container = _nicegui_ui.element('div').classes('web-search-spinner-container').style(
                        'display:flex;flex-direction:column;align-items:center;justify-content:center;'
                        'padding:16px;margin:12px auto;max-width:360px;'
                        'background:rgba(52,152,219,0.1);border:1px solid rgba(52,152,219,0.3);'
                        'border-radius:14px;'
                    )
                    with _web_search_spinner_container:
                        _nicegui_ui.html(
                            '<div style="display:flex;flex-direction:column;align-items:center;">'
                            '<div style="width:32px;height:32px;border:3px solid #1a1a2e;'
                            'border-top:3px solid #3498db;border-radius:50%;'
                            'animation:web-spin 1.2s linear infinite;"></div>'
                            '<span style="font-size:13px;color:#3498db;margin-top:8px;font-style:italic;">'
                            '&#127760; Recherche en cours...</span>'
                            '</div>'
                            '<style>@keyframes web-spin{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}</style>'
                        )
                print("[WEB-NAV-UI] Spinner recherche affiché dans le chat")
    except Exception as e:
        print(f"[WEB-NAV-UI] Erreur affichage spinner: {e}")


def hide_web_search_spinner_in_chat():
    """Cache le spinner de recherche web dans le chat."""
    global _web_search_spinner_container
    try:
        if _web_search_spinner_container:
            try:
                _ = _web_search_spinner_container.client
                _web_search_spinner_container.delete()
            except RuntimeError:
                print("[WEB-NAV-UI] Spinner déjà supprimé (client déconnecté)")
            _web_search_spinner_container = None
            print("[WEB-NAV-UI] Spinner recherche retiré du chat")
    except Exception as e:
        print(f"[WEB-NAV-UI] Erreur suppression spinner: {e}")


def integrate_into_settings(settings_container, web_navigator_extension):
    """
    Intègre l'interface Web Navigator dans les paramètres généraux d'OGMA
    
    Args:
        settings_container: Conteneur des paramètres OGMA  
        web_navigator_extension: Instance de l'extension Web Navigator
    """
    
    if not web_navigator_extension:
        print("[WEB-NAV-UI] ⚠️ Extension Web Navigator non disponible")
        return
    
    # Créer l'interface et l'intégrer
    ui_handler = WebNavigatorUI(
        web_navigator_extension.config,
        web_navigator_extension.commands
    )
    
    ui_handler.create_settings_panel(settings_container)
    
    print("[WEB-NAV-UI] ✅ Interface intégrée dans les paramètres OGMA")