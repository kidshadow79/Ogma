# Cognitive Mirror - Composants Interface Utilisateur

"""
Composants interface utilisateur pour l'extension Cognitive Mirror
Overlay réflexion, zone paramètres, bouton toggle avec homogénéité esthétique OGMA
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

class CognitiveMirrorUI:
    """
    Gestionnaire des composants UI pour Cognitive Mirror
    
    Composants:
    - Bouton toggle ON/OFF (intégration header OGMA)
    - Overlay réflexion 30% hauteur
    - Zone paramètres extensible
    - Animations et transitions fluides
    """
    
    def __init__(self, config, ui_container=None, on_toggle_extension=None, on_settings_change=None):
        """
        Initialise les composants UI
        
        Args:
            config: Instance CognitiveMirrorConfig
            ui_container: Container NiceGUI pour l'overlay (optionnel)
            on_toggle_extension: Callback(new_state)
            on_settings_change: Callback(setting_key, new_value)
        """
        self.config = config
        self.ui_container = ui_container
        self.on_toggle_extension = on_toggle_extension
        self.on_settings_change = on_settings_change
        
        # État UI
        self.is_overlay_visible = False
        self.current_messages = []
        
        # Composants UI (créés à la demande)
        self.toggle_button = None
        self.overlay_container = None
        self.reflection_chat = None
        self.settings_panel = None
        
        # Styles
        self.styles = self.config.get_overlay_styles()
        self.system_messages = self.config.get_system_messages()
        
        print(f"[COGNITIVE-MIRROR-UI] Interface initialisee (NiceGUI: {'OK' if NICEGUI_AVAILABLE else 'NO'})")
    
    def create_toggle_button(self, container=None):
        """
        Crée le bouton toggle pour intégration dans header OGMA
        
        Args:
            container: Container NiceGUI où créer le bouton
        
        Returns:
            Bouton toggle créé
        """
        if not NICEGUI_AVAILABLE:
            return None
        
        with (container or ui):
            # Bouton avec style cohérent OGMA
            self.toggle_button = ui.button(
                icon='psychology',
                color='primary' if self.config.is_enabled() else 'secondary',
                on_click=self._on_toggle_clicked
            )
            
            # Tooltip explicatif
            self.toggle_button.tooltip('Cognitive Mirror - Réflexion IA visible')
            
            # Classes CSS pour homogénéité esthétique
            self.toggle_button.classes('cognitive-mirror-toggle')
            
            # État initial
            self.update_toggle_state(self.config.is_enabled())
            
        return self.toggle_button
    
    def create_overlay(self, container=None):
        """
        Crée l'overlay de réflexion 30% hauteur
        
        Args:
            container: Container parent pour l'overlay
        
        Returns:
            Container overlay créé
        """
        if not NICEGUI_AVAILABLE:
            print("[COGNITIVE-MIRROR-UI] ⚠️ NiceGUI non disponible pour création overlay")
            return None
        
        print(f"[COGNITIVE-MIRROR-UI] Creation overlay avec container: {container}")
        print(f"[COGNITIVE-MIRROR-UI] DEBUG - self.ui_container: {self.ui_container}")
        
        try:
            # Utiliser le container fourni ou créer dans le contexte global
            if container:
                context_manager = container
                print(f"[COGNITIVE-MIRROR-UI] Utilise container fourni: {container}")
            else:
                # Pour NiceGUI, on utilise directement la création sans context manager
                # L'overlay sera ajouté à la page courante
                context_manager = None
                print("[COGNITIVE-MIRROR-UI] Creation directe sans context manager")
            
            if context_manager:
                with context_manager:
                    self._create_overlay_content()
                    print("[COGNITIVE-MIRROR-UI] Overlay cree AVEC context manager")
            else:
                # Création directe sans context manager
                self._create_overlay_content()
                print("[COGNITIVE-MIRROR-UI] Overlay cree SANS context manager")
            
            # Overlay initialement masqué
            if self.overlay_container:
                self.overlay_container.visible = False
                print(f"[COGNITIVE-MIRROR-UI] OK Overlay cree avec succes - ID: {id(self.overlay_container)}")
                return self.overlay_container
            else:
                print("[COGNITIVE-MIRROR-UI] ❌ Overlay container non créé")
                return None
            
        except Exception as e:
            print(f"[COGNITIVE-MIRROR-UI] ❌ Erreur création overlay: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _inject_overlay_styles(self):
        """Injecte les styles CSS nécessaires pour l'overlay"""
        if not NICEGUI_AVAILABLE:
            return
        
        try:
            # CSS pour les classes d'animation et positionnement
            css_styles = f"""
            <style>
            .cognitive-mirror-overlay.active {{
                {self.styles.get('active', 'transform: translateY(0);')}
            }}
            </style>
            """
            
            # Injection des styles dans la page
            ui.add_head_html(css_styles)
            print("[COGNITIVE-MIRROR-UI] OK Styles CSS injectes")
            
        except Exception as e:
            print(f"[COGNITIVE-MIRROR-UI] ⚠️ Erreur injection CSS: {e}")
    
    def _create_overlay_content(self):
        """Crée le contenu de l'overlay"""
        # Injection des styles CSS nécessaires
        self._inject_overlay_styles()
        
        # Container principal overlay - créer dans le contexte global NiceGUI
        # Utiliser ui.add() ou créer directement sans context manager
        self.overlay_container = ui.card().style(self.styles["container"])
        self.overlay_container.classes('cognitive-mirror-overlay')
        
        # S'assurer que l'overlay est attaché à la page principale
        # Pour NiceGUI, utiliser .move() pour attacher au body
        try:
            from nicegui import app
            if hasattr(app, 'native') and app.native:
                # Mode natif - utiliser le contexte actuel
                pass
            else:
                # Mode web - attacher au body de la page
                self.overlay_container.move(target=None)  # Attacher à la page courante
        except Exception as e:
            print(f"[COGNITIVE-MIRROR-UI] ⚠️ Impossible d'attacher à la page: {e}")
        
        with self.overlay_container:
            # Zone de chat réflexif - conteneur avec scroll
            self.reflection_chat_container = ui.scroll_area().style(self.styles["chat_area"])
            self.reflection_chat_container.classes('cognitive-mirror-chat')
            
            # Column à l'intérieur du scroll area pour contenir les messages
            with self.reflection_chat_container:
                self.reflection_chat = ui.column().style("width: 100%; padding: 8px;")
                # Message initial
                self._add_system_message("En attente d'une session de réflexion...")
            
            # Panneau de paramètres (initialement masqué)
            self.create_settings_panel(self.overlay_container)
            
            # Barre de contrôles
            with ui.row().style(self.styles["controls"]) as controls:
                controls.classes('cognitive-mirror-controls')
                
                ui.space()  # Espacement
                
                # Bouton paramètres
                ui.button(
                    icon='settings',
                    color='secondary',
                    on_click=self._toggle_settings_panel
                ).classes('settings-toggle')
                
                # Bouton fermeture manuelle
                ui.button(
                    icon='close',
                    color='negative', 
                    on_click=self._force_close_reflection
                ).classes('close-reflection')
    
    def create_settings_panel(self, container=None):
        """
        Crée le panneau de paramètres extensible
        
        Args:
            container: Container pour le panneau
        
        Returns:
            Panneau de paramètres créé
        """
        if not NICEGUI_AVAILABLE:
            return None
        
        with ui.expansion('⚙️ Paramètres Cognitive Mirror', icon='settings') as self.settings_panel:
                self.settings_panel.classes('cognitive-mirror-settings')
                
                # Message déclencheur personnalisable
                with ui.card():
                    ui.label('📝 Message déclencheur').style('font-weight: bold; margin-bottom: 8px;')
                    ui.label('Message envoyé pour déclencher la réflexion intérieure :')
                    self.trigger_message_input = ui.textarea(
                        label='Message utilisateur de base',
                        value=self.config.get('trigger_message'),
                        placeholder='Décrivez votre état mental actuel et vos réflexions...'
                    ).classes('full-width')
                    
                    ui.button(
                        'Sauvegarder message',
                        icon='save',
                        color='primary',
                        on_click=self._save_trigger_message
                    )
                
                # Paramètres de timing
                with ui.card():
                    ui.label('⏱️ Temporisation').style('font-weight: bold; margin-bottom: 8px;')
                    ui.number(
                        label='Temps avant déclenchement (secondes)',
                        value=self.config.get('trigger_delay_no_message'),
                        min=15, max=120, step=5,
                        on_change=lambda e: self._on_setting_change('trigger_delay_no_message', e.value)
                    )
                    
                    ui.number(
                        label='Durée maximale réflexion (minutes)',
                        value=self.config.get('max_reflection_duration') / 60,
                        min=1, max=10, step=0.5,
                        on_change=lambda e: self._on_setting_change('max_reflection_duration', int(e.value * 60))
                    )
                
                # Paramètres IA
                with ui.card():
                    ui.label('🤖 Configuration IA').style('font-weight: bold; margin-bottom: 8px;')
                    ui.number(
                        label='Tokens par message',
                        value=self.config.get('reflection_token_limit'),
                        min=100, max=2000, step=50,
                        on_change=lambda e: self._on_setting_change('reflection_token_limit', int(e.value))
                    )
                    
                    ui.switch(
                        text='Sauvegarde automatique des réflexions',
                        value=self.config.get('auto_save_reflections'),
                        on_change=lambda e: self._on_setting_change('auto_save_reflections', e.value)
                    )
                
                # Paramètres d'interface
                with ui.card():
                    ui.label('🎨 Interface').style('font-weight: bold; margin-bottom: 8px;')
                    ui.number(
                        label='Hauteur overlay (%)',
                        value=self.config.get('overlay_height_percent'),
                        min=20, max=80, step=5,
                        on_change=lambda e: self._on_setting_change('overlay_height_percent', e.value)
                    )
                    
                    ui.switch(
                        text='Mode compact',
                        value=self.config.get('compact_mode'),
                        on_change=lambda e: self._on_setting_change('compact_mode', e.value)
                    )
                
                # Bouton reset
                ui.button(
                    'Réinitialiser paramètres',
                    color='warning',
                    icon='restore',
                    on_click=self._reset_settings
                ).classes('full-width')
        
        return self.settings_panel
        
        return self.settings_panel
    
    def show_reflection_overlay(self):
        """Affiche l'overlay de réflexion avec animation"""
        if not NICEGUI_AVAILABLE:
            print("[COGNITIVE-MIRROR-UI] ⚠️ NiceGUI non disponible")
            return
        
        print(f"[COGNITIVE-MIRROR-UI] DEBUG - ui_container: {self.ui_container}")
        print(f"[COGNITIVE-MIRROR-UI] DEBUG - overlay_container exists: {self.overlay_container is not None}")
        
        # Créer l'overlay si il n'existe pas
        if not self.overlay_container:
            print("[COGNITIVE-MIRROR-UI] Creation de l'overlay a la demande...")
            result = self.create_overlay()
            print(f"[COGNITIVE-MIRROR-UI] DEBUG - create_overlay result: {result}")
            
            if not self.overlay_container:
                print("[COGNITIVE-MIRROR-UI] ❌ Échec création overlay")
                return
        
        # Vérifier que le chat est disponible
        if not self.reflection_chat:
            print("[COGNITIVE-MIRROR-UI] ⚠️ Chat de réflexion non créé")
            return
        
        print("[COGNITIVE-MIRROR-UI] Debut affichage overlay...")
        print(f"[COGNITIVE-MIRROR-UI] DEBUG - overlay_container.visible before: {getattr(self.overlay_container, 'visible', 'N/A')}")
        
        # Nettoyage messages précédents
        self.current_messages = []
        if self.reflection_chat:
            self.reflection_chat.clear()
            print("[COGNITIVE-MIRROR-UI] Chat nettoye")
        
        # Message de démarrage
        self._add_system_message(self.system_messages["typing_indicator"])
        print("[COGNITIVE-MIRROR-UI] Message systeme ajoute")
        
        try:
            # Affichage avec animation CSS
            self.overlay_container.visible = True
            
            # Forcer l'actualisation de l'affichage
            if hasattr(self.overlay_container, 'update'):
                self.overlay_container.update()
                print("[COGNITIVE-MIRROR-UI] Container.update() appele")
            
            # Appliquer directement le style d'affichage au lieu d'utiliser une classe CSS
            # Ceci remplace le transform: translateY(-100%) par transform: translateY(0)
            current_style = self.overlay_container.style.copy()
            current_style['transform'] = 'translateY(0)'
            current_style['opacity'] = '1'  # Forcer opacité
            current_style['display'] = 'block'  # Forcer affichage
            self.overlay_container.style.update(current_style)
            
            print(f"[COGNITIVE-MIRROR-UI] Style transform mis a jour: translateY(0)")
            
            print(f"[COGNITIVE-MIRROR-UI] DEBUG - overlay_container.visible after: {getattr(self.overlay_container, 'visible', 'N/A')}")
            print(f"[COGNITIVE-MIRROR-UI] DEBUG - overlay_container style: {self.overlay_container.style}")
            
            self.is_overlay_visible = True
            print("[COGNITIVE-MIRROR-UI] OK Overlay affiche et visible")
            
        except Exception as e:
            print(f"[COGNITIVE-MIRROR-UI] ❌ Erreur affichage overlay: {e}")
            import traceback
            traceback.print_exc()
    
    def hide_reflection_overlay(self):
        """Masque l'overlay de réflexion avec animation et intégration des conversations"""
        if not NICEGUI_AVAILABLE or not self.overlay_container:
            return
        
        # Intégrer les conversations avec l'Archiviste dans le contexte normal
        self._integrate_reflection_to_context()
        
        # Animation de fermeture - remettre le transform vers le haut
        current_style = self.overlay_container.style.copy()
        current_style['transform'] = 'translateY(-100%)'
        self.overlay_container.style.update(current_style)
        
        # Masquage après délai animation
        try:
            # Tenter d'utiliser asyncio si un event loop est actif
            asyncio.create_task(self._delayed_hide())
        except RuntimeError:
            # Fallback synchrone pour les tests
            print("[COGNITIVE-MIRROR-UI] Fermeture synchrone (pas d'event loop)")
            if self.overlay_container:
                self.overlay_container.visible = False
        
        self.is_overlay_visible = False
        print("[COGNITIVE-MIRROR-UI] Overlay masque")
    
    def update_conversation_content(self, message_data: Dict[str, Any]):
        """
        Met à jour le contenu de l'overlay avec nouveaux messages de conversation
        
        Args:
            message_data: Données de message (type, message, etc.)
        """
        if not NICEGUI_AVAILABLE or not self.reflection_chat:
            print("[COGNITIVE-MIRROR-UI] ⚠️ Impossible mettre à jour contenu: NICEGUI ou chat manquant")
            return
        
        print(f"[COGNITIVE-MIRROR-UI] 📨 Mise à jour conversation: {message_data}")
        
        # NOUVEAU: Support des messages directs du ConversationManager
        if "role" in message_data and "content" in message_data:
            role = message_data["role"]
            content = message_data["content"]
            
            # Mapper les rôles aux noms d'affichage
            if role == "luna":
                sender = "Luna"
            elif role == "archiviste":
                sender = "Archiviste"
            elif role == "system":
                sender = "Système"
            else:
                sender = role.capitalize()
                
            print(f"[COGNITIVE-MIRROR-UI] 💬 Message direct {sender}: {content[:50]}...")
            
            # Ajouter le message au chat
            self._add_message_to_chat(sender, content)
            
        # Ancien format (pour compatibilité)
        elif message_data.get("type") == "message":
            message = message_data["message"]
            sender = message["sender"]
            content = message["content"]
            
            print(f"[COGNITIVE-MIRROR-UI] 💬 Ajout message {sender}: {content[:50]}...")
            
            # Ajouter le message au chat
            self._add_message_to_chat(sender, content)
            
        elif message_data.get("type") == "error":
            error_message = message_data["error"]
            print(f"[COGNITIVE-MIRROR-UI] ❌ Erreur reçue: {error_message}")
            
            # Ajouter message d'erreur
            self._add_message_to_chat("Système", f"Erreur: {error_message}")
        
        else:
            print(f"[COGNITIVE-MIRROR-UI] ⚠️ Type de données non supporté: {message_data.get('type', 'unknown')}")
            print(f"[COGNITIVE-MIRROR-UI] 🔍 DEBUG - Clés disponibles: {list(message_data.keys())}")
    
    def _add_message_to_chat(self, sender: str, content: str):
        """Ajoute un message au chat avec formatage approprié"""
        try:
            print(f"[COGNITIVE-MIRROR-UI] ➕ Ajout message {sender} dans le chat...")
            
            # Si c'est le premier message, nettoyer le chat
            if len(self.current_messages) == 0:
                print("[COGNITIVE-MIRROR-UI] 🧹 Premier message: nettoyage chat")
                self.reflection_chat.clear()
            
            # Ajouter le message dans la column avec les composants NiceGUI appropriés
            with self.reflection_chat:
                if sender == "Luna":
                    ui.chat_message(content, name=sender, stamp='Luna').style("margin-bottom: 8px;")
                elif sender == "Archiviste":  
                    ui.chat_message(content, name=sender, stamp='Archiviste').style("margin-bottom: 8px;")
                else:
                    ui.chat_message(content, name=sender, stamp=sender).style("margin-bottom: 8px;")
            
            # Stocker le message
            self.current_messages.append({"sender": sender, "content": content, "timestamp": time.time()})
            
            print(f"[COGNITIVE-MIRROR-UI] ✅ Message {sender} ajouté au chat")
            print(f"[COGNITIVE-MIRROR-UI] 📊 Total messages: {len(self.current_messages)}")
            
            # Forcer le scroll vers le bas - méthode corrigée pour ScrollArea
            if self.reflection_chat_container:
                try:
                    self.reflection_chat_container.scroll_to(percent=1.0)
                except:
                    # Alternative si scroll_to n'existe pas
                    pass
                
        except Exception as e:
            print(f"[COGNITIVE-MIRROR-UI] ❌ Erreur ajout message: {e}")
    
    def update_reflection_content(self, observation_data: Dict[str, Any]):
        """
        DEPRECATED: Utilisez update_conversation_content() à la place
        Méthode conservée pour compatibilité temporaire
        """
        print("[COGNITIVE-MIRROR-UI] ⚠️ DEPRECATED: update_reflection_content appelé, utilisez update_conversation_content")
        
        # Convertir vers nouveau format si possible
        if observation_data.get("type") == "new_observation":
            observation = observation_data["observation"]
            message_data = {
                "type": "message",
                "message": {
                    "sender": "Luna" if observation["type"] == "luna_thinking" else "Archiviste",
                    "content": observation["content"],
                    "timestamp": observation.get("timestamp", time.time()),
                    "type": observation["type"]
                }
            }
            self.update_conversation_content(message_data)
            
        # Support ancien format pour compatibilité
        elif "new_message" in observation_data:
            message = observation_data["new_message"]
            print(f"[COGNITIVE-MIRROR-UI] 💬 Ajout message {message['sender']}: {message['content'][:50]}...")
            self._add_reflection_message(message["sender"], message["content"])
    
    def update_toggle_state(self, enabled: bool):
        """Met à jour l'état visuel du bouton toggle"""
        if not NICEGUI_AVAILABLE or not self.toggle_button:
            return
        
        # Couleur bouton
        self.toggle_button.props(f'color={"primary" if enabled else "secondary"}')
        
        # Icône animée
        icon = 'psychology' if enabled else 'psychology_alt'
        self.toggle_button.props(f'icon={icon}')
        
        # Tooltip informatif
        tooltip_text = 'Cognitive Mirror activé - Réflexions automatiques' if enabled else 'Cognitive Mirror désactivé'
        self.toggle_button.tooltip(tooltip_text)
    
    def get_components(self) -> Dict[str, Any]:
        """
        Retourne les composants UI créés pour intégration OGMA
        
        Returns:
            dict: Composants disponibles
        """
        return {
            "toggle_button": self.toggle_button,
            "overlay": self.overlay_container,
            "settings_panel": self.settings_panel,
            "is_overlay_visible": self.is_overlay_visible
        }
    
    def cleanup(self):
        """Nettoyage et fermeture propre de l'interface"""
        print("[COGNITIVE-MIRROR-UI] 🔄 Nettoyage interface...")
        
        # Masquage overlay si visible
        if self.is_overlay_visible:
            self.hide_reflection_overlay()
        
        # Reset références
        self.toggle_button = None
        self.overlay_container = None
        self.reflection_chat = None
        self.settings_panel = None
        
        print("[COGNITIVE-MIRROR-UI] ✅ Interface nettoyée")
    
    # === MÉTHODES PRIVÉES ===
    
    async def _delayed_hide(self):
        """Masque l'overlay après délai d'animation"""
        await asyncio.sleep(0.3)  # Durée animation CSS
        if self.overlay_container:
            self.overlay_container.visible = False
    
    def _add_system_message(self, content: str):
        """Ajoute un message système à l'overlay"""
        if not NICEGUI_AVAILABLE or not self.reflection_chat:
            return
        
        with self.reflection_chat:
            ui.chat_message(
                content,
                name='System',
                stamp=''
            ).style('font-style: italic; opacity: 0.8; color: #9ca3af;')
    
    def _add_reflection_message(self, sender: str, content: str):
        """Ajoute un message de réflexion à l'overlay"""
        if not NICEGUI_AVAILABLE or not self.reflection_chat:
            print("[COGNITIVE-MIRROR-UI] ⚠️ Impossible ajouter message: NICEGUI ou chat manquant")
            return
        
        print(f"[COGNITIVE-MIRROR-UI] ➕ Ajout message {sender} dans le chat...")
        
        # Suppression message système initial si présent
        if len(self.current_messages) == 0:
            self.reflection_chat.clear()
            print("[COGNITIVE-MIRROR-UI] 🧹 Premier message: nettoyage chat")
        
        # Style selon expéditeur
        if sender == "IA":
            message_style = self.styles["message_ia"]
        elif sender == "Archiviste":
            message_style = self.styles["message_archiviste"] 
        else:
            message_style = ""
        
        with self.reflection_chat:
            with ui.card().style(message_style):
                ui.label(f"**{sender}:**").style('font-weight: bold; margin-bottom: 8px;')
                ui.label(content).style('line-height: 1.4;')
        
        print(f"[COGNITIVE-MIRROR-UI] ✅ Message {sender} ajouté au chat")
        
        # Scroll automatique vers le bas - corrigé pour ScrollArea
        if self.reflection_chat_container:
            try:
                self.reflection_chat_container.scroll_to(percent=1.0)
            except:
                pass
        
        # Enregistrement message
        self.current_messages.append({"sender": sender, "content": content})
        print(f"[COGNITIVE-MIRROR-UI] 📊 Total messages: {len(self.current_messages)}")
    
    def _on_toggle_clicked(self):
        """Callback clic bouton toggle"""
        current_state = self.config.is_enabled()
        new_state = not current_state
        
        # Notification callback
        if self.on_toggle_extension:
            self.on_toggle_extension(new_state)
        
        print(f"[COGNITIVE-MIRROR-UI] 🔄 Toggle clicked: {current_state} -> {new_state}")
    
    def _toggle_settings_panel(self):
        """Bascule l'affichage du panneau de paramètres"""
        try:
            if not hasattr(self, 'settings_panel') or self.settings_panel is None:
                print("[COGNITIVE-MIRROR-UI] Panneau de parametres non initialise")
                return
                
            # Pour les expansions NiceGUI, utiliser la propriété 'open'
            if hasattr(self.settings_panel, 'open'):
                current_state = getattr(self.settings_panel, 'open', False)
                self.settings_panel.open = not current_state
                print(f"[COGNITIVE-MIRROR-UI] Panneau parametres: {'ouvert' if not current_state else 'ferme'}")
            elif hasattr(self.settings_panel, 'toggle'):
                self.settings_panel.toggle()
                print(f"[COGNITIVE-MIRROR-UI] Panneau parametres bascule (methode toggle)")
            else:
                print("[COGNITIVE-MIRROR-UI] Aucune methode de bascule trouvee sur le panneau")
                    
        except Exception as e:
            print(f"[COGNITIVE-MIRROR-UI] Erreur toggle panneau parametres: {e}")
            import traceback
            traceback.print_exc()
    
    def _force_close_reflection(self):
        """Force la fermeture de la session de réflexion"""
        try:
            print("[COGNITIVE-MIRROR-UI] Fermeture forcee reflexion")
            
            # Intégrer les conversations avec l'Archiviste dans le contexte normal
            self._integrate_reflection_to_context()
            
            # Fermer l'overlay
            self.hide_reflection_overlay()
            
            # Notifier le callback pour arrêter la session active
            if self.on_settings_change:
                self.on_settings_change('force_stop_reflection', True)
                
        except Exception as e:
            print(f"[COGNITIVE-MIRROR-UI] Erreur fermeture forcee: {e}")
            try:
                self.hide_reflection_overlay()
            except:
                pass
    
    def _integrate_reflection_to_context(self):
        """Intègre les conversations de réflexion dans le contexte de conversation normal"""
        if not self.current_messages:
            print("[COGNITIVE-MIRROR-UI] INFO Aucun message de reflexion a integrer")
            return
        
        print(f"[COGNITIVE-MIRROR-UI] 📋 Intégration de {len(self.current_messages)} messages de réflexion")
        
        # Créer un résumé des conversations de réflexion
        reflection_summary = "🧠 **Réflexion cognitive terminée**\n\n"
        reflection_summary += "Voici un résumé des échanges entre Luna et l'Archiviste pendant la session de réflexion :\n\n"
        
        for msg in self.current_messages:
            sender = msg.get('sender', 'Inconnu')
            content = msg.get('content', '')
            
            # Tronquer les messages très longs
            if len(content) > 200:
                content = content[:200] + "..."
            
            reflection_summary += f"**{sender}** : {content}\n\n"
        
        reflection_summary += "Cette réflexion enrichit maintenant notre conversation."
        
        # Envoyer le résumé au callback pour intégration dans OGMA
        if self.on_settings_change:
            self.on_settings_change('integrate_reflection_summary', reflection_summary)
        
        print("[COGNITIVE-MIRROR-UI] ✅ Résumé de réflexion créé et envoyé pour intégration")
    
    def _on_setting_change(self, setting_key: str, new_value: Any):
        """Callback modification paramètre"""
        if self.on_settings_change:
            self.on_settings_change(setting_key, new_value)
    
    def _save_trigger_message(self):
        """Sauvegarde le message déclencheur personnalisé"""
        try:
            if hasattr(self, 'trigger_message_input') and self.trigger_message_input:
                new_message = self.trigger_message_input.value.strip()
                if new_message:
                    self._on_setting_change('trigger_message', new_message)
                    print(f"[COGNITIVE-MIRROR-UI] ✅ Message déclencheur sauvegardé: {new_message[:50]}...")
                else:
                    print("[COGNITIVE-MIRROR-UI] ⚠️ Message déclencheur vide, pas de sauvegarde")
            else:
                print("[COGNITIVE-MIRROR-UI] ⚠️ Input message déclencheur non trouvé")
        except Exception as e:
            print(f"[COGNITIVE-MIRROR-UI] ❌ Erreur sauvegarde message déclencheur: {e}")
    
    def _reset_settings(self):
        """Remet les paramètres par défaut"""
        self.config.reset_to_defaults()
        
        # Notification utilisateur
        if NICEGUI_AVAILABLE:
            ui.notify("Paramètres réinitialisés", type='positive')
        
        print("[COGNITIVE-MIRROR-UI] 🔄 Paramètres réinitialisés")