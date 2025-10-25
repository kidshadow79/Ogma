# Cognitive Mirror - Composants Interface Utilisateur
# VERSION 2.0 - Introspection

"""
Extension Introspection - Interface Popup Paramètres v2.0
Popup complet avec tous les paramètres et tooltips explicatifs
"""

from typing import Dict, Any, Optional, Callable
import asyncio
import time

try:
    from nicegui import ui
    NICEGUI_AVAILABLE = True
except ImportError:
    NICEGUI_AVAILABLE = False
    # Mock pour développement sans NiceGUI
    class MockUI:
        def __getattr__(self, name):
            return lambda *args, **kwargs: None
    ui = MockUI()

# Import nouveau popup v3.0 SIMPLIFIÉE
try:
    from .ui_parameters_modal_v3_simple import IntrospectionParametersModalV3Simple
    V3_AVAILABLE = True
except ImportError:
    V3_AVAILABLE = False
    print("[INTROSPECTION-UI] ⚠️ Popup v3.0 non disponible - utilisation version legacy")

class CognitiveMirrorUI:
    """
    Interface Introspection v2.0
    Popup paramètres complet avec backward compatibility
    """

    def __init__(self, config, ui_container=None, on_toggle_extension=None, on_settings_change=None, core_reference=None):
        """
        Initialise les composants UI Introspection

        Args:
            config: Instance CognitiveMirrorConfig
            ui_container: Container NiceGUI (ignoré pour popup)
            on_toggle_extension: Callback(new_state)
            on_settings_change: Callback(setting_key, new_value)
            core_reference: Référence au CognitiveMirrorCore pour état actuel
        """
        self.config = config
        self.on_toggle_extension = on_toggle_extension
        self.on_settings_change = on_settings_change
        self.core_reference = core_reference

        # Popup paramètres - Version 3.0 SIMPLIFIÉE si disponible, sinon legacy
        if V3_AVAILABLE:
            self.parameters_modal = IntrospectionParametersModalV3Simple(
                config, on_toggle_extension, on_settings_change, core_reference
            )
            print("[INTROSPECTION-UI] ✅ Interface v3.0 SIMPLIFIÉE initialisée (toutes étapes visibles)")
        else:
            self.parameters_modal = SubconscienceParametersModal(
                config, on_toggle_extension, on_settings_change, core_reference
            )
            print("[INTROSPECTION-UI] ⚠️ Interface legacy initialisée (fallback)")

        # État UI pour compatibilité API
        self.is_overlay_visible = False
        self.overlay_container = None
    
    def create_overlay(self):
        """
        API Compatibilité - Crée popup paramètres au lieu d'overlay
        Appelé par ogma_ng.py
        """
        print("[INTROSPECTION-UI] create_overlay() -> popup parametres v3.0 SIMPLIFIÉE")
        return self.parameters_modal.create_popup()

    def show_reflection_overlay(self):
        """Compatibilité - Affiche popup paramètres"""
        print("[INTROSPECTION-UI] show_reflection_overlay() -> popup parametres")
        self.parameters_modal.show_popup()
        self.is_overlay_visible = True

    def hide_reflection_overlay(self):
        """Compatibilité - Masque popup"""
        print("[INTROSPECTION-UI] hide_reflection_overlay() -> ferme popup")
        self.parameters_modal.close_popup()
        self.is_overlay_visible = False

    def update_conversation_content(self, message_data: Dict[str, Any]):
        """Compatibilité - Mode Introspection sans affichage conversation"""
        print(f"[INTROSPECTION-UI] update_conversation_content: {message_data.get('role', 'unknown')}")
        # En mode Introspection v2.0, dialogue affiché dans boîte séparée

    def cleanup(self):
        """Nettoyage ressources"""
        if self.parameters_modal:
            self.parameters_modal.cleanup()
        print("[INTROSPECTION-UI] Interface nettoyée")

    def show_parameters_popup(self):
        """Ouvre le popup de paramètres Introspection v3.0 SIMPLIFIÉE"""
        print("[INTROSPECTION-UI] show_parameters_popup() -> popup parametres v3.0 SIMPLIFIÉE")
        if self.parameters_modal:
            self.parameters_modal.show_popup()
            self.is_overlay_visible = True
        else:
            print("[INTROSPECTION-UI] ❌ parameters_modal non initialisé")
    
    def get_components(self):
        """Compatibilité - Retourne composants"""
        return {
            "parameters_modal": self.parameters_modal.popup_container,
            "is_popup_visible": self.parameters_modal.is_popup_visible
        }

class SubconscienceParametersModal:
    """
    Popup paramètres Introspection LEGACY (fallback)
    Interface complète : ON/OFF + tous paramètres introspection avec tooltips
    """

    def __init__(self, config, on_toggle_callback, on_settings_callback, core_reference=None):
        """
        Initialise popup paramètres

        Args:
            config: Instance CognitiveMirrorConfig
            on_toggle_callback: Callback extension ON/OFF
            on_settings_callback: Callback changement paramètres
            core_reference: Référence au CognitiveMirrorCore pour état actuel
        """
        self.config = config
        self.on_toggle_callback = on_toggle_callback
        self.on_settings_callback = on_settings_callback
        self.core_reference = core_reference

        # État popup
        self.popup_container = None
        self.is_popup_visible = False

        # Contrôles UI - Général
        self.extension_toggle = None
        self.introspection_mode_select = None

        # Contrôles UI - Instructions
        self.luna_introspection_instruction = None
        self.archiviste_introspection_instruction = None

        # Contrôles UI - Template
        self.box_template = None

        # Contrôles UI - Paramètres techniques
        self.luna_tokens = None
        self.archiviste_tokens = None
        self.synthesis_tokens = None
        self.max_exchanges = None
        self.max_duration = None

        # Contrôles UI - Sauvegarde
        self.ia_decides_save = None
        self.importance_threshold = None

        # Contrôles UI - Affichage
        self.show_dialogue = None
        self.streaming_animation = None

        # Anciens contrôles (LEGACY - compatibilité)
        self.inactivity_delay = None
        self.auto_send_delay = None
        self.entite_tokens = None
        self.archiviste_tokens_legacy = None
        self.luna_instruction = None
        self.archiviste_instruction = None
        self.trigger_message = None

        print("[INTROSPECTION-MODAL] 🆕 Popup paramètres v2.0 initialisé")
    
    def create_popup(self):
        """
        Crée popup paramètres Introspection v2.0
        Interface complète avec tous les nouveaux paramètres et tooltips
        """
        if not NICEGUI_AVAILABLE:
            print("[INTROSPECTION-MODAL] NiceGUI non disponible - mode simulation")
            return None

        with ui.dialog().props('persistent maximized') as dialog:
            self.popup_container = dialog

            with ui.card().style('width: 800px; max-height: 90vh; overflow-y: auto; padding: 24px'):
                # ===== HEADER =====
                ui.html('<h2 style="margin: 0 0 24px 0; text-align: center; color: #1f2937;">🧠 Introspection - Paramètres</h2>')
                
                # Toggle principal ON/OFF - utilise état réel du core
                with ui.row().style('width: 100%; justify-content: space-between; align-items: center; margin-bottom: 24px; padding: 12px; background: #f3f4f6; border-radius: 8px'):
                    ui.label('Extension').style('font-weight: 600; font-size: 16px')
                    
                    # État initial depuis le core ou fallback config
                    if self.core_reference:
                        current_state = self.core_reference.is_enabled()
                        current_enum_state = self.core_reference.current_state
                        print(f"[SUBCONSCIENCE-MODAL] 🔍 État core: is_enabled()={current_state}, current_state={current_enum_state}")
                    else:
                        current_state = self.config.DEFAULT_SETTINGS.get('extension_enabled', False)
                        print(f"[SUBCONSCIENCE-MODAL] 🔍 État config par défaut: {current_state}")
                    
                    print(f"[SUBCONSCIENCE-MODAL] 🎯 Switch initialisé à: {current_state}")
                    
                    # Configuration du callback avec logs détaillés
                    def debug_toggle_callback(event):
                        print(f"[SUBCONSCIENCE-MODAL] 🚨 CALLBACK APPELÉ ! event={event}")
                        print(f"[SUBCONSCIENCE-MODAL] 🚨 event.value={getattr(event, 'value', 'AUCUN_VALUE')}")
                        print(f"[SUBCONSCIENCE-MODAL] 🚨 Type event: {type(event)}")
                        self._on_extension_toggle(event)
                    
                    self.extension_toggle = ui.switch(
                        value=current_state
                    ).on('change', debug_toggle_callback).props('color=primary size=lg')
                    
                    print(f"[SUBCONSCIENCE-MODAL] 🔗 Switch créé avec callback debug")
                
                ui.separator().style('margin: 20px 0')
                
                # Section paramètres temporels
                ui.label('Paramètres Temporels').style('font-weight: 600; margin-bottom: 16px; color: #374151')
                
                with ui.column().style('width: 100%; gap: 16px; margin-bottom: 20px'):
                    self.inactivity_delay = ui.number(
                        label='Temps avant activation (secondes)',
                        value=self.config.DEFAULT_SETTINGS.get('trigger_delay_no_message', 30),
                        min=15, max=600, step=5
                    ).style('width: 100%').props('outlined dense')
                    
                    self.auto_send_delay = ui.number(
                        label='Délai auto-envoi (secondes)', 
                        value=self.config.DEFAULT_SETTINGS.get('auto_send_delay', 20),
                        min=10, max=60, step=5
                    ).style('width: 100%').props('outlined dense')
                    
                    self.max_duration = ui.number(
                        label='Durée maximale (minutes)',
                        value=self.config.DEFAULT_SETTINGS.get('max_reflection_duration', 300) / 60,
                        min=1, max=15, step=0.5  
                    ).style('width: 100%').props('outlined dense')
                    
                    # Tokens séparés pour Entité IA et Archiviste
                    with ui.row().style('gap: 12px'):
                        self.entite_tokens = ui.number(
                            label='Entité IA - Tokens max par message',
                            value=self.config.get('entite_token_limit', 500),
                            min=100, max=2000, step=50
                        ).style('width: 100%').props('outlined dense').tooltip(
                            'Limite tokens pour réponses de l\'entité IA en réflexion. Augmenter si texte coupé.'
                        )

                        self.archiviste_tokens = ui.number(
                            label='Archiviste - Tokens max par message',
                            value=self.config.get('archiviste_token_limit', 400),
                            min=100, max=2000, step=50
                        ).style('width: 100%').props('outlined dense').tooltip(
                            'Limite tokens pour analyses de l\'Archiviste. Augmenter si texte coupé.'
                        )
                
                ui.separator().style('margin: 20px 0')
                
                # Instructions personnalisées (complètes et modifiables)
                ui.label('Instructions Personnalisées').style('font-weight: 600; margin-bottom: 16px; color: #374151')

                self.luna_instruction = ui.textarea(
                    label='Instruction Entité IA (modifiable)',
                    value=self.config.current_settings.get('luna_instruction', ''),
                    placeholder='Instructions complètes pour l\'entité IA en phase réflexive...'
                ).style('width: 100%; min-height: 120px; margin-bottom: 20px').props('outlined')

                self.archiviste_instruction = ui.textarea(
                    label='Instruction Archiviste (modifiable)',
                    value=self.config.current_settings.get('archiviste_instruction', ''),
                    placeholder='Instructions complètes pour l\'Archiviste subconscient...'
                ).style('width: 100%; min-height: 120px; margin-bottom: 20px').props('outlined')
                
                ui.separator().style('margin: 20px 0')
                
                # Section message déclencheur
                ui.label('Message Déclencheur').style('font-weight: 600; margin-bottom: 12px; color: #374151')
                ui.label('Message envoyé pour lancer la phase réflexive').style('font-size: 12px; color: #6b7280; margin-bottom: 8px')
                
                self.trigger_message = ui.textarea(
                    value=self.config.DEFAULT_SETTINGS.get('trigger_message', 
                        "Jusqu'à mon retour tu es en phase réflexive intérieure avec ton subconscient, tu as accès à tes souvenirs et aux questionnements intérieurs"),
                    placeholder='Décrivez le message qui déclenchera la réflexion...'
                ).style('width: 100%; min-height: 100px; margin-bottom: 24px').props('outlined')
                
                # Boutons d'action
                with ui.row().style('width: 100%; justify-content: space-between; gap: 12px'):
                    ui.button('Sauvegarder', on_click=self._save_settings).props('color=primary size=md').style('flex: 1')
                    ui.button('X', on_click=lambda: dialog.close()).props('flat color=grey size=md')
        
        print("[SUBCONSCIENCE-MODAL] Popup créé avec succès")
        return dialog
    
    def show_popup(self):
        """Affiche le popup paramètres - création unique pour maintenir callbacks"""
        print("[SUBCONSCIENCE-MODAL] 🔧 Ouverture popup paramètres...")
        
        # Créer le popup SEULEMENT s'il n'existe pas OU si il est obsolète
        if self.popup_container is None:
            print("[SUBCONSCIENCE-MODAL] 🆕 Première création du popup")
            self.create_popup()
        else:
            # Vérifier si le popup contient tous les champs nécessaires
            if not all([self.entite_tokens, self.archiviste_tokens, self.luna_instruction, self.archiviste_instruction]):
                print("[SUBCONSCIENCE-MODAL] 🔄 Popup obsolète détecté, recréation...")
                # Nettoyer l'ancien popup
                try:
                    self.popup_container.close()
                except:
                    pass
                self.popup_container = None
                self.create_popup()
            else:
                print("[SUBCONSCIENCE-MODAL] 🔄 Réutilisation popup existant")
        
        if self.popup_container:
            # Mettre à jour les valeurs depuis la config avant affichage
            self._update_popup_values()
            self.popup_container.open()
            self.is_popup_visible = True
            print("[SUBCONSCIENCE-MODAL] ✅ Popup affiché")
        else:
            print("[SUBCONSCIENCE-MODAL] ❌ Impossible de créer/afficher le popup")
    
    def close_popup(self):
        """Ferme le popup"""
        if self.popup_container:
            try:
                self.popup_container.close()
                self.is_popup_visible = False
                print("[SUBCONSCIENCE-MODAL] Popup fermé")
            except Exception as e:
                print(f"[SUBCONSCIENCE-MODAL] Erreur fermeture popup: {e}")
                self.is_popup_visible = False
    
    def _update_popup_values(self):
        """Met à jour les valeurs du popup depuis la configuration actuelle"""
        if not self.popup_container:
            return
            
        try:
            # CORRECTION CRITIQUE: Lire l'état depuis la CONFIGURATION ACTUELLE (pas DEFAULT_SETTINGS)
            current_state = self.config.get('extension_enabled', False)
            print(f"[SUBCONSCIENCE-MODAL] 🔄 Mise à jour switch depuis CONFIG: {current_state}")
            
            if self.extension_toggle:
                self.extension_toggle.value = current_state
                    
                # CORRECTION CRITIQUE: Reconnecter le callback à chaque ouverture
                print(f"[SUBCONSCIENCE-MODAL] 🔗 Reconnexion callback switch...")
                
                def debug_toggle_callback(event):
                    print(f"[SUBCONSCIENCE-MODAL] 🚨 CALLBACK APPELÉ ! event={event}")
                    print(f"[SUBCONSCIENCE-MODAL] 🚨 event.value={getattr(event, 'value', 'AUCUN_VALUE')}")
                    print(f"[SUBCONSCIENCE-MODAL] 🚨 Type event: {type(event)}")
                    self._on_extension_toggle(event)
                
                # Forcer reconnexion du callback
                self.extension_toggle.on('change', debug_toggle_callback)
                print(f"[SUBCONSCIENCE-MODAL] ✅ Callback switch reconnecté")
            
            # Mettre à jour les autres valeurs depuis la config
            if self.inactivity_delay:
                self.inactivity_delay.value = self.config.get('trigger_delay_no_message', 30)
            if self.auto_send_delay:
                self.auto_send_delay.value = self.config.get('auto_send_delay', 20)
            if self.max_duration:
                self.max_duration.value = self.config.get('max_reflection_duration', 300) / 60
            # Supprimé: self.max_tokens (reflection_token_limit n'existe pas)
            if self.entite_tokens:
                self.entite_tokens.value = self.config.get('entite_token_limit', 500)
            else:
                print("[SUBCONSCIENCE-MODAL] ⚠️ Champ entite_tokens manquant")
            if self.archiviste_tokens:
                self.archiviste_tokens.value = self.config.get('archiviste_token_limit', 400)
            else:
                print("[SUBCONSCIENCE-MODAL] ⚠️ Champ archiviste_tokens manquant")
            if self.luna_instruction:
                self.luna_instruction.value = self.config.get('luna_instruction', '')
            else:
                print("[SUBCONSCIENCE-MODAL] ⚠️ Champ luna_instruction manquant")
            if self.archiviste_instruction:
                self.archiviste_instruction.value = self.config.get('archiviste_instruction', '')
            else:
                print("[SUBCONSCIENCE-MODAL] ⚠️ Champ archiviste_instruction manquant")
            if self.trigger_message:
                self.trigger_message.value = self.config.get_required('trigger_message')
                    
            print("[SUBCONSCIENCE-MODAL] ✅ Valeurs popup mises à jour")
        except Exception as e:
            print(f"[SUBCONSCIENCE-MODAL] ⚠️ Erreur mise à jour valeurs: {e}")
    
    def _on_extension_toggle(self, event):
        """
        Gestion toggle ON/OFF extension
        Callback vers core pour activation/désactivation
        """
        print(f"[SUBCONSCIENCE-MODAL] 🔄 Toggle événement reçu: {event}")
        print(f"[SUBCONSCIENCE-MODAL] 🔄 Event.value: {event.value}")
        
        new_state = event.value
        print(f"[SUBCONSCIENCE-MODAL] 🎯 Extension {'ACTIVÉE' if new_state else 'DÉSACTIVÉE'}")
        
        # Mise à jour config locale (pour cohérence)
        self.config.set('extension_enabled', new_state)
        print(f"[SUBCONSCIENCE-MODAL] 💾 Config mise à jour: extension_enabled={new_state}")
        
        # Notification callback externe (vers core)
        if self.on_toggle_callback:
            try:
                print(f"[SUBCONSCIENCE-MODAL] 📞 Appel callback: {self.on_toggle_callback}")
                self.on_toggle_callback(new_state)
                print(f"[SUBCONSCIENCE-MODAL] ✅ Callback exécuté avec succès")
            except Exception as e:
                print(f"[SUBCONSCIENCE-MODAL] ❌ Erreur callback toggle: {e}")
                import traceback
                traceback.print_exc()
        else:
            print("[SUBCONSCIENCE-MODAL] ❌ Aucun callback configuré!")
    
    def _save_settings(self):
        """
        Sauvegarde tous les paramètres et ferme popup
        Notifications callbacks + persistance config
        """
        try:
            # Collecte des valeurs avec vérifications de sécurité
            settings = {
                'extension_enabled': self.extension_toggle.value if self.extension_toggle else True,
                'trigger_delay_no_message': int(self.inactivity_delay.value) if self.inactivity_delay else 30,
                'auto_send_delay': int(self.auto_send_delay.value) if self.auto_send_delay else 20,
                'max_reflection_duration': int(self.max_duration.value * 60) if self.max_duration else 300,
                # 'reflection_token_limit' SUPPRIMÉ: Code mort (n'existe pas dans config)
                'entite_token_limit': int(self.entite_tokens.value) if self.entite_tokens else 500,
                'archiviste_token_limit': int(self.archiviste_tokens.value) if self.archiviste_tokens else 400,
                'luna_instruction': self.luna_instruction.value if self.luna_instruction else self.config.get('luna_instruction', ''),
                'archiviste_instruction': self.archiviste_instruction.value if self.archiviste_instruction else self.config.get('archiviste_instruction', ''),
                'trigger_message': self.trigger_message.value if self.trigger_message else self.config.get_required('trigger_message')
            }

            print(f"[SUBCONSCIENCE-MODAL] 🔧 Settings collectés: extension_enabled={settings['extension_enabled']}")
            print(f"[SUBCONSCIENCE-MODAL] 🔧 Entité IA tokens: {settings['entite_token_limit']}, Archiviste tokens: {settings['archiviste_token_limit']}")

            # Vérifier si certains champs sont manquants (popup ancien)
            missing_fields = []
            # if not self.max_tokens: SUPPRIMÉ (code mort)
            if not self.entite_tokens:
                missing_fields.append('entite_tokens')
            if not self.archiviste_tokens:
                missing_fields.append('archiviste_tokens')
            if not self.luna_instruction:
                missing_fields.append('luna_instruction')
            if not self.archiviste_instruction:
                missing_fields.append('archiviste_instruction')
                
            if missing_fields:
                print(f"[SUBCONSCIENCE-MODAL] ⚠️ Champs manquants (popup obsolète): {missing_fields}")
                print("[SUBCONSCIENCE-MODAL] 💡 Le popup sera recréé au prochain affichage avec tous les champs")
                # Forcer la recréation du popup la prochaine fois
                self.popup_container = None
            
            # Mise à jour config CORRECTE avec persistance
            for key, value in settings.items():
                success = self.config.set(key, value)
                if success:
                    print(f"[SUBCONSCIENCE-MODAL] ✅ Paramètre sauvegardé: {key} = {value}")
                else:
                    print(f"[SUBCONSCIENCE-MODAL] ❌ Échec sauvegarde: {key}")
            
            # Notifications callbacks pour chaque paramètre 
            if self.on_settings_callback:
                for key, value in settings.items():
                    try:
                        print(f"[SUBCONSCIENCE-MODAL] 📞 Callback {key}: {value}")
                        self.on_settings_callback(key, value)
                    except Exception as e:
                        print(f"[SUBCONSCIENCE-MODAL] ❌ Erreur callback {key}: {e}")
            
            print("[SUBCONSCIENCE-MODAL] Paramètres sauvegardés avec succès")
            print(f"[SUBCONSCIENCE-MODAL] Extension: {'ON' if settings['extension_enabled'] else 'OFF'}")
            print(f"[SUBCONSCIENCE-MODAL] Inactivité: {settings['trigger_delay_no_message']}s")
            print(f"[SUBCONSCIENCE-MODAL] Auto-envoi: {settings['auto_send_delay']}s")
            
            # Fermeture popup
            if self.popup_container:
                self.popup_container.close()
            self.is_popup_visible = False
            
        except Exception as e:
            print(f"[SUBCONSCIENCE-MODAL] Erreur sauvegarde: {e}")
    
    def cleanup(self):
        """Nettoyage ressources popup"""
        if self.popup_container:
            try:
                self.popup_container.close()
            except:
                pass
            self.popup_container = None
        
        self.is_popup_visible = False
        print("[SUBCONSCIENCE-MODAL] Cleanup terminé")

# Maintien compatibilité exports
__all__ = ['CognitiveMirrorUI', 'SubconscienceParametersModal']