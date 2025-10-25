# 🧠 Introspection - Popup Paramètres v2.0
# Nouvelle interface complète avec tous les paramètres et tooltips

"""
Popup paramètres Introspection v2.0
Interface modulaire avec sections organisées et tooltip        # Tokens IA Principale et Archiviste (côte à côte)
        with ui.row().style('gap: 16px; margin-bottom: 16px'):
            with ui.column().style('flex: 1'):
                with ui.row().style('align-items: center; gap: 8px; margin-bottom: 4px'):
                    ui.label('IA Principale - Tokens max/message').style('font-weight: 500; color: #374151; font-size: 14px')
                    ui.icon('info').style('color: #3b82f6; font-size: 18px; cursor: help').tooltip(
                        'Limite tokens pour chaque message de l\'IA Principale en introspection.\n'
                        'Augmenter si réponses tronquées. Utiliser -1 pour illimité.\n\n'
                        'Recommandé: -1 (illimité) ou 400-800 tokens'
                    )
                self.ui_controls['main_ai_tokens'] = ui.number(
                    value=self.config.get('main_ai_tokens_per_message', -1),
                    min=-1, max=2000, step=50
                ).style('width: 100%').props('outlined dense')
"""

from typing import Optional, Callable, Dict, Any
import re

try:
    from nicegui import ui
    NICEGUI_AVAILABLE = True
except ImportError:
    NICEGUI_AVAILABLE = False
    class MockUI:
        def __getattr__(self, name):
            return lambda *args, **kwargs: None
    ui = MockUI()


class IntrospectionParametersModalV2:
    """
    Popup paramètres Introspection v2.0 - Interface complète

    Sections:
    1. Toggle ON/OFF + Mode (always/on_demand)
    2. Instructions personnalisées (IA Principale + Archiviste)
    3. Template structure boîte
    4. Paramètres techniques (tokens, exchanges, duration)
    5. Sauvegarde mémoire (IA décide, seuil)
    6. Affichage (dialogue details, streaming)
    """

    def __init__(self, config, on_toggle_callback, on_settings_callback, core_reference=None):
        """
        Initialise popup paramètres v2.0

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

        # Contrôles UI
        self.ui_controls = {}  # Dictionnaire pour tous les contrôles

        print("[INTROSPECTION-MODAL-V2] 🆕 Popup paramètres v2.0 initialisé")

    def create_popup(self):
        """Crée popup paramètres complet avec toutes les sections"""
        if not NICEGUI_AVAILABLE:
            print("[INTROSPECTION-MODAL-V2] ❌ NiceGUI non disponible")
            return None

        with ui.dialog().props('persistent maximized') as dialog:
            self.popup_container = dialog

            with ui.card().style('width: 900px; max-height: 90vh; overflow-y: auto; padding: 24px; background: #2d2d2d; border-radius: 12px; box-shadow: 0 8px 32px rgba(0,0,0,0.4);'):
                # Header
                ui.html('<h2 style="margin: 0 0 24px 0; text-align: center; color: #f3f4f6;">🧠 Introspection - Paramètres</h2>')

                # Section 1: Configuration générale
                self._create_general_section()

                ui.separator().style('margin: 20px 0; background: rgba(75, 85, 99, 0.3)')

                # Section 2: Instructions
                self._create_instructions_section()

                ui.separator().style('margin: 20px 0; background: rgba(75, 85, 99, 0.3)')

                # Section 3: Template
                self._create_template_section()

                ui.separator().style('margin: 20px 0; background: rgba(75, 85, 99, 0.3)')

                # Section 4: Paramètres techniques
                self._create_technical_section()

                ui.separator().style('margin: 20px 0; background: rgba(75, 85, 99, 0.3)')

                # Section 5: Sauvegarde mémoire
                self._create_memory_section()

                ui.separator().style('margin: 20px 0; background: rgba(75, 85, 99, 0.3)')

                # Section 6: Affichage
                self._create_display_section()

                # Boutons action
                self._create_action_buttons(dialog)

        print("[INTROSPECTION-MODAL-V2] ✅ Popup créé avec succès")
        
        # Force le rafraîchissement de l'interface après création
        self._force_refresh_tabs()
        
        return dialog

    def _create_general_section(self):
        """Section 1: Configuration générale - Style amélioré"""
        ui.label('⚙️ Configuration Générale').style('font-weight: 600; font-size: 18px; margin-bottom: 16px; color: #f3f4f6')

        # Toggle ON/OFF compact
        with ui.row().style('justify-content: flex-start; align-items: center; gap: 16px; margin-bottom: 16px; padding: 12px; background: rgba(55, 65, 81, 0.3); border-radius: 8px; border: 1px solid rgba(75, 85, 99, 0.3); width: fit-content'):
            ui.label('Extension Active').style('font-weight: 500; font-size: 16px; color: #e5e7eb')

            current_state = self.config.get('extension_enabled', False)
            self.ui_controls['extension_toggle'] = ui.switch(
                value=current_state
            ).on('change', self._on_extension_toggle).props('color=primary')
            print(f"[DEBUG-UI] Extension toggle initialisé avec: {current_state}")

        # Tooltip extension
        with ui.row().style('margin-left: 8px; margin-bottom: 20px; align-items: center; gap: 6px'):
            ui.icon('info').style('color: #9ca3af; font-size: 18px')
            ui.label('Active le mode introspection. OFF = phrases magiques uniquement, ON = introspection systématique').style('font-size: 13px; color: #9ca3af')

        # Mode introspection avec meilleur espacement
        with ui.column().style('margin-bottom: 16px'):
            with ui.row().style('align-items: center; gap: 8px; margin-bottom: 8px'):
                ui.label('Mode Introspection').style('font-weight: 500; color: #e5e7eb; font-size: 15px')
                ui.icon('info').style('color: #60a5fa; font-size: 18px; cursor: help').tooltip(
                    'Définit quand l\'introspection se déclenche:\n'
                    '  • ON DEMAND: Uniquement sur phrases magiques\n'
                    '  • ALWAYS: Systématiquement sur chaque message\n\n'
                    'Recommandé: ON DEMAND pour garder le contrôle'
                )

            current_mode = self.config.get('introspection_mode', 'on_demand')
            self.ui_controls['introspection_mode'] = ui.select(
                options={'on_demand': '🎯 Sur demande (phrases magiques)', 'always': '🔄 Systématique (tous les messages)'},
                value=current_mode
            ).style('width: 100%; background: rgba(55, 65, 81, 0.4); color: #e5e7eb').props('outlined dense dark')

    def _create_instructions_section(self):
        """Section 2: Configuration des 5 Étapes d'Introspection"""
        ui.label('🎭 Configuration des 5 Étapes d\'Introspection').style('font-weight: 600; font-size: 18px; margin-bottom: 16px; color: #f3f4f6')

        # Explication du processus
        ui.html('''
        <div style="background: rgba(59, 130, 246, 0.1); border-left: 4px solid #3b82f6; padding: 12px; margin-bottom: 20px; border-radius: 6px;">
            <p style="color: #e5e7eb; margin: 0; font-size: 14px;">
                <strong>🔄 Processus en 5 étapes :</strong><br>
                <span style="color: #93c5fd;">1. Analyse initiale</span> → 
                <span style="color: #34d399;">2-3. Dialogue IA ↔ Archiviste</span> → 
                <span style="color: #a78bfa;">4. Synthèse autonome</span> → 
                <span style="color: #fbbf24;">5. Réponse finale</span>
            </p>
        </div>
        ''')

        # Onglets pour chaque étape - Style amélioré (MAINTENANT 6 ÉTAPES)
        print("[DEBUG-ONGLETS] Création des onglets des 6 étapes...")
        with ui.tabs().classes('w-full').style('background: rgba(55, 65, 81, 0.6); border-radius: 8px; padding: 8px; margin-bottom: 16px') as tabs:
            etape0_tab = ui.tab('🧠 Étape 0', icon='memory').style('color: #f87171; font-weight: 500; padding: 12px 20px; min-width: 120px').on('click', lambda: print("[DEBUG-ONGLETS] Clic sur Étape 0"))
            etape1_tab = ui.tab('🔍 Étape 1', icon='analytics').style('color: #93c5fd; font-weight: 500; padding: 12px 20px; min-width: 120px').on('click', lambda: print("[DEBUG-ONGLETS] Clic sur Étape 1"))
            etape23_tab = ui.tab('💬 Étapes 2-3', icon='forum').style('color: #34d399; font-weight: 500; padding: 12px 20px; min-width: 120px').on('click', lambda: print("[DEBUG-ONGLETS] Clic sur Étapes 2-3"))
            etape4_tab = ui.tab('✨ Étape 4', icon='summarize').style('color: #a78bfa; font-weight: 500; padding: 12px 20px; min-width: 120px').on('click', lambda: print("[DEBUG-ONGLETS] Clic sur Étape 4"))
            affichage_tab = ui.tab('🎨 Affichage Final', icon='visibility').style('color: #fbbf24; font-weight: 500; padding: 12px 20px; min-width: 120px').on('click', lambda: print("[DEBUG-ONGLETS] Clic sur Affichage Final"))
        
        print(f"[DEBUG-ONGLETS] Onglets créés: {len([etape0_tab, etape1_tab, etape23_tab, etape4_tab, affichage_tab])} onglets")

        with ui.tab_panels(tabs, value=etape0_tab).classes('w-full').style('background: rgba(31, 41, 55, 0.8); border-radius: 8px; padding: 20px; min-height: 400px'):
            # ÉTAPE 0: Accès direct mémoire (NOUVEAU)
            with ui.tab_panel(etape0_tab).style('background: rgba(17, 24, 39, 0.8); padding: 16px; border-radius: 6px'):
                print("[DEBUG-ONGLETS] Création contenu Étape 0...")
                ui.html('<h3 style="color: #f87171; margin-bottom: 16px; padding: 8px; background: rgba(248, 113, 113, 0.1); border-radius: 6px;">🧠 ÉTAPE 0 - Accès Direct Mémoire (Non Visible)</h3>')
                
                # Test de visibilité
                ui.label('✅ CONTENU VISIBLE - Étape 0 fonctionne !').style('color: #10b981; font-weight: bold; padding: 8px; background: rgba(16, 185, 129, 0.1); border-radius: 4px; margin-bottom: 16px')
                
                ui.label('L\'IA Principale accède directement à sa mémoire FAISS/SQLite sans censure.').style('color: #9ca3af; margin-bottom: 16px')
                
                with ui.row().style('align-items: center; gap: 8px; margin-bottom: 8px'):
                    ui.label('Instructions pour l\'Accès Direct Mémoire').style('font-weight: 500; color: #e5e7eb')
                    ui.icon('info').style('color: #f87171; cursor: help').tooltip(
                        'Instructions pour l\'accès direct et non censuré à la mémoire.\n\n'
                        'Variables disponibles :\n'
                        '  {user_message} - Message de l\'utilisateur\n'
                        '  {conversation_context} - Contexte conversationnel\n\n'
                        'IMPORTANT: Cette étape donne un accès COMPLET à la mémoire\n'
                        'sans censure, pour contourner les limitations de l\'Archiviste.'
                    )

                current_etape0 = self.config.get('direct_memory_access_instruction', '')
                print(f"[DEBUG-UI] ÉTAPE 0 - Valeur chargée: {len(current_etape0)} chars")
                
                # Force l'affichage avec une valeur par défaut si vide
                if not current_etape0:
                    current_etape0 = "# Instructions pour l'accès direct mémoire\n\nEn attente de chargement..."
                    print("[DEBUG-UI] ÉTAPE 0 - Valeur par défaut appliquée")
                
                self.ui_controls['etape0_instruction'] = ui.textarea(
                    value=current_etape0,
                    placeholder='Instructions pour l\'accès direct à la mémoire...'
                ).style('width: 100%; height: 200px; font-family: monospace; font-size: 12px; background: rgba(55, 65, 81, 0.4); color: #e5e7eb').props('outlined dark')
                
                # Log de confirmation
                print(f"[DEBUG-UI] ÉTAPE 0 - Contrôle UI créé avec {len(current_etape0)} chars")

            # ÉTAPE 1: Analyse initiale
            with ui.tab_panel(etape1_tab).style('background: rgba(17, 24, 39, 0.8); padding: 16px; border-radius: 6px'):
                print("[DEBUG-ONGLETS] Création contenu Étape 1...")
                ui.html('<h3 style="color: #93c5fd; margin-bottom: 16px; padding: 8px; background: rgba(147, 197, 253, 0.1); border-radius: 6px;">🔍 ÉTAPE 1 - Analyse Initiale (Visible)</h3>')
                
                # Test de visibilité
                ui.label('✅ CONTENU VISIBLE - Étape 1 fonctionne !').style('color: #10b981; font-weight: bold; padding: 8px; background: rgba(16, 185, 129, 0.1); border-radius: 4px; margin-bottom: 16px')
                ui.label('L\'IA Principale analyse la demande utilisateur et identifie ses besoins.').style('color: #9ca3af; margin-bottom: 16px')
                
                with ui.row().style('align-items: center; gap: 8px; margin-bottom: 8px'):
                    ui.label('Instructions pour l\'IA Principale').style('font-weight: 500; color: #e5e7eb')
                    ui.icon('info').style('color: #93c5fd; cursor: help').tooltip(
                        'Instructions données à l\'IA Principale pour analyser la demande.\n\n'
                        'Variables disponibles :\n'
                        '  {user_message} - Message de l\'utilisateur\n'
                        '  {conversation_context} - Contexte conversationnel\n\n'
                        'Cette étape génère une analyse courte et visible.'
                    )

                current_etape1 = self.config.get('initial_analysis_instruction', '')
                print(f"[DEBUG-UI] ÉTAPE 1 - Valeur chargée: {len(current_etape1)} chars")
                print(f"[DEBUG-UI] ÉTAPE 1 - Preview: {current_etape1[:100]}...")
                
                # Force l'affichage avec une valeur par défaut si vide
                if not current_etape1:
                    current_etape1 = "# Instructions pour l'analyse initiale\n\nEn attente de chargement..."
                    print("[DEBUG-UI] ÉTAPE 1 - Valeur par défaut appliquée")
                
                self.ui_controls['etape1_instruction'] = ui.textarea(
                    value=current_etape1,
                    placeholder='Instructions pour l\'analyse initiale...'
                ).style('width: 100%; height: 200px; font-family: monospace; font-size: 12px; background: rgba(55, 65, 81, 0.4); color: #e5e7eb').props('outlined dark')
                
                # Log de confirmation
                print(f"[DEBUG-UI] ÉTAPE 1 - Contrôle UI créé avec {len(current_etape1)} chars")

            # ÉTAPES 2-3: Dialogue  
            with ui.tab_panel(etape23_tab).style('background: rgba(17, 24, 39, 0.8); padding: 16px; border-radius: 6px'):
                print("[DEBUG-ONGLETS] Création contenu Étapes 2-3...")
                ui.html('<h3 style="color: #34d399; margin-bottom: 16px; padding: 8px; background: rgba(52, 211, 153, 0.1); border-radius: 6px;">💬 ÉTAPES 2-3 - Dialogue IA ↔ Archiviste (Visible)</h3>')
                
                # Test de visibilité
                ui.label('✅ CONTENU VISIBLE - Étapes 2-3 fonctionnent !').style('color: #10b981; font-weight: bold; padding: 8px; background: rgba(16, 185, 129, 0.1); border-radius: 4px; margin-bottom: 20px')
                ui.label('L\'IA Principale consulte activement l\'Archiviste qui répond avec les souvenirs pertinents.').style('color: #9ca3af; margin-bottom: 20px')
                
                # Instructions IA Principale pour dialogue
                with ui.column().style('margin-bottom: 24px'):
                    with ui.row().style('align-items: center; gap: 8px; margin-bottom: 8px'):
                        ui.label('🤖 Instructions IA Principale - Dialogue').style('font-weight: 500; color: #e5e7eb')
                        ui.icon('info').style('color: #60a5fa; cursor: help').tooltip(
                            'Comment l\'IA Principale doit dialoguer avec l\'Archiviste.\n\n'
                            'Variables disponibles :\n'
                            '  {user_message} - Message utilisateur\n'
                            '  {conversation_context} - Contexte\n'
                            '  {initial_analysis} - Analyse étape 1\n'
                            '  {dialogue_history} - Historique dialogue\n'
                            '  {exchange_number} - Numéro échange\n\n'
                            'Phrase magique : "je suis prête à formuler ma synthèse"'
                        )

                    current_etape23_ia = self.config.get('main_ai_introspection_instruction', '')
                    print(f"[DEBUG-UI] ÉTAPES 2-3 IA - Valeur chargée: {len(current_etape23_ia)} chars")
                    
                    # Force l'affichage avec une valeur par défaut si vide
                    if not current_etape23_ia:
                        current_etape23_ia = "# Instructions dialogue IA Principale\n\nEn attente de chargement..."
                        print("[DEBUG-UI] ÉTAPES 2-3 IA - Valeur par défaut appliquée")
                    
                    self.ui_controls['etape23_ia_instruction'] = ui.textarea(
                        value=current_etape23_ia,
                        placeholder='Instructions dialogue pour l\'IA Principale...'
                    ).style('width: 100%; height: 180px; font-family: monospace; font-size: 12px; background: rgba(55, 65, 81, 0.4); color: #e5e7eb').props('outlined dark')
                    
                    # Log de confirmation
                    print(f"[DEBUG-UI] ÉTAPES 2-3 IA - Contrôle UI créé avec {len(current_etape23_ia)} chars")

                # Instructions Archiviste
                with ui.column():
                    with ui.row().style('align-items: center; gap: 8px; margin-bottom: 8px'):
                        ui.label('📚 Instructions Archiviste - Consultation').style('font-weight: 500; color: #e5e7eb')
                        ui.icon('info').style('color: #34d399; cursor: help').tooltip(
                            'Comment l\'Archiviste doit répondre aux consultations.\n\n'
                            'Variables disponibles :\n'
                            '  {main_ai_question} - Question de l\'IA Principale\n'
                            '  {conversation_context} - Contexte\n'
                            '  {memory_context} - Souvenirs trouvés\n\n'
                            'Rôle : PASSIF, répond aux demandes explicites uniquement'
                        )

                    current_etape23_arch = self.config.get('archiviste_introspection_instruction', '')
                    print(f"[DEBUG-UI] ÉTAPES 2-3 Archiviste - Valeur chargée: {len(current_etape23_arch)} chars")
                    
                    # Force l'affichage avec une valeur par défaut si vide
                    if not current_etape23_arch:
                        current_etape23_arch = "# Instructions consultation Archiviste\n\nEn attente de chargement..."
                        print("[DEBUG-UI] ÉTAPES 2-3 Archiviste - Valeur par défaut appliquée")
                    
                    self.ui_controls['etape23_archiviste_instruction'] = ui.textarea(
                        value=current_etape23_arch,
                        placeholder='Instructions consultation pour l\'Archiviste...'
                    ).style('width: 100%; height: 180px; font-family: monospace; font-size: 12px; background: rgba(55, 65, 81, 0.4); color: #e5e7eb').props('outlined dark')
                    
                    # Log de confirmation
                    print(f"[DEBUG-UI] ÉTAPES 2-3 Archiviste - Contrôle UI créé avec {len(current_etape23_arch)} chars")

            # ÉTAPE 4: Synthèse
            with ui.tab_panel(etape4_tab).style('background: rgba(17, 24, 39, 0.8); padding: 16px; border-radius: 6px'):
                print("[DEBUG-ONGLETS] Création contenu Étape 4...")
                ui.html('<h3 style="color: #a78bfa; margin-bottom: 16px; padding: 8px; background: rgba(167, 139, 250, 0.1); border-radius: 6px;">✨ ÉTAPE 4 - Synthèse Autonome (Visible)</h3>')
                
                # Test de visibilité
                ui.label('✅ CONTENU VISIBLE - Étape 4 fonctionne !').style('color: #10b981; font-weight: bold; padding: 8px; background: rgba(16, 185, 129, 0.1); border-radius: 4px; margin-bottom: 16px')
                ui.label('L\'IA Principale structure sa réflexion et décide de sauvegarder ou non.').style('color: #9ca3af; margin-bottom: 16px')
                
                with ui.row().style('align-items: center; gap: 8px; margin-bottom: 8px'):
                    ui.label('Instructions pour la Synthèse Structurée').style('font-weight: 500; color: #e5e7eb')
                    ui.icon('info').style('color: #a78bfa; cursor: help').tooltip(
                        'Instructions pour générer la synthèse finale structurée.\n\n'
                        'Variables disponibles :\n'
                        '  {dialogue_history} - Tout le dialogue complet\n'
                        '  {user_message} - Message utilisateur initial\n\n'
                        'Doit inclure les métadonnées de sauvegarde JSON :\n'
                        '{"save_decision": "yes/no", "importance": 0-10, "reason": "..."}'
                    )

                current_etape4 = self.config.get('synthesis_structure_instruction', '')
                print(f"[DEBUG-UI] ÉTAPE 4 - Valeur chargée: {len(current_etape4)} chars")
                
                # Force l'affichage avec une valeur par défaut si vide
                if not current_etape4:
                    current_etape4 = "# Instructions synthèse finale\n\nEn attente de chargement..."
                    print("[DEBUG-UI] ÉTAPE 4 - Valeur par défaut appliquée")
                
                self.ui_controls['etape4_instruction'] = ui.textarea(
                    value=current_etape4,
                    placeholder='Instructions pour la synthèse finale...'
                ).style('width: 100%; height: 200px; font-family: monospace; font-size: 12px; background: rgba(55, 65, 81, 0.4); color: #e5e7eb').props('outlined dark')
                
                # Log de confirmation
                print(f"[DEBUG-UI] ÉTAPE 4 - Contrôle UI créé avec {len(current_etape4)} chars")

            # AFFICHAGE FINAL
            with ui.tab_panel(affichage_tab).style('background: rgba(17, 24, 39, 0.8); padding: 16px; border-radius: 6px'):
                print("[DEBUG-ONGLETS] Création contenu Affichage Final...")
                
                # Test de visibilité d'abord
                ui.label('✅ CONTENU VISIBLE - Affichage Final fonctionne !').style('color: #10b981; font-weight: bold; padding: 8px; background: rgba(16, 185, 129, 0.1); border-radius: 4px; margin-bottom: 16px')
                
                self._create_display_template_panel()

    def _create_display_template_panel(self):
        """Panneau configuration affichage final"""
        print("[DEBUG-ONGLETS] Création template panel...")
        ui.html('<h3 style="color: #fbbf24; margin-bottom: 16px;">🎨 Template d\'Affichage Final</h3>')
        ui.label('Personnalisez comment les résultats de l\'introspection sont affichés dans la boîte de dialogue.').style('color: #9ca3af; margin-bottom: 16px')

        # Boutons templates prédéfinis
        with ui.row().style('gap: 12px; margin-bottom: 16px'):
            ui.button('📋 Simple', on_click=lambda: self._set_simple_template()).props('size=sm color=primary')
            ui.button('📊 Détaillé', on_click=lambda: self._set_detailed_template()).props('size=sm')
            ui.button('🎯 Minimal', on_click=lambda: self._set_minimal_template()).props('size=sm')
            ui.button('🔍 Prévisualiser', on_click=self._preview_template).props('size=sm color=secondary')

        # Variables disponibles avec exemples
        with ui.expansion('📋 Variables Disponibles', icon='help').classes('w-full mb-4'):
            ui.html('''
            <div style="font-family: monospace; font-size: 12px; color: #e5e7eb; line-height: 1.6;">
                <p><strong style="color: #93c5fd;">{main_ai_analysis}</strong> - Analyse initiale de l'étape 1</p>
                <p><strong style="color: #34d399;">{dialogue_messages}</strong> - Messages du dialogue IA ↔ Archiviste</p>
                <p><strong style="color: #a78bfa;">{synthesis}</strong> - Synthèse finale structurée</p>
                <p><strong style="color: #f87171;">{save_decision}</strong> - Décision de sauvegarde (yes/no)</p>
                <p><strong style="color: #fbbf24;">{importance}</strong> - Score importance (0-10)</p>
                <p><strong style="color: #10b981;">{save_reason}</strong> - Raison de la sauvegarde</p>
            </div>
            ''')

        current_template = self.config.get('introspection_box_template', '')
        print(f"[DEBUG-UI] Template - Valeur chargée: {len(current_template)} chars")
        
        # Force l'affichage avec une valeur par défaut si vide
        if not current_template:
            current_template = "# Template d'affichage\n\nEn attente de chargement..."
            print("[DEBUG-UI] Template - Valeur par défaut appliquée")
        
        self.ui_controls['box_template'] = ui.textarea(
            value=current_template,
            placeholder='Template d\'affichage des résultats d\'introspection...'
        ).style('width: 100%; height: 250px; font-family: monospace; font-size: 12px; background: rgba(55, 65, 81, 0.4); color: #e5e7eb').props('outlined dark')
        
        # Log de confirmation
        print(f"[DEBUG-UI] Template - Contrôle UI créé avec {len(current_template)} chars")

    def _create_template_section(self):
        """Section 3: Déplacée dans les onglets des instructions"""
        pass  # Cette section est maintenant intégrée dans _create_instructions_section

    def _create_technical_section(self):
        """Section 4: Paramètres techniques - Style amélioré"""
        ui.label('⚙️ Paramètres Techniques').style('font-weight: 600; font-size: 18px; margin-bottom: 16px; color: #f3f4f6')

        # Tokens IA Principale et Archiviste (côte à côte)
        with ui.row().style('gap: 16px; margin-bottom: 16px'):
            with ui.column().style('flex: 1'):
                with ui.row().style('align-items: center; gap: 8px; margin-bottom: 8px'):
                    ui.label('IA Principale - Tokens max/message').style('font-weight: 500; color: #e5e7eb; font-size: 14px')
                    ui.icon('info').style('color: #60a5fa; font-size: 18px; cursor: help').tooltip(
                        'Limite tokens pour chaque message de l\'IA Principale en introspection.\n'
                        'Augmenter si messages tronqués. Utiliser -1 pour illimité.\n\n'
                        'Recommandé: -1 (illimité) ou 400-800 tokens'
                    )
                self.ui_controls['luna_tokens'] = ui.number(
                    value=self.config.get('main_ai_tokens_per_message', -1),
                    min=-1, max=2000, step=50
                ).style('width: 100%; background: rgba(55, 65, 81, 0.4); color: #e5e7eb').props('outlined dense dark')

            with ui.column().style('flex: 1'):
                with ui.row().style('align-items: center; gap: 8px; margin-bottom: 8px'):
                    ui.label('Archiviste - Tokens max/message').style('font-weight: 500; color: #e5e7eb; font-size: 14px')
                    ui.icon('info').style('color: #34d399; font-size: 18px; cursor: help').tooltip(
                        'Limite tokens pour chaque réponse de l\'Archiviste.\n'
                        'Augmenter si analyses tronquées. Utiliser -1 pour illimité.\n\n'
                        'Recommandé: -1 (illimité) ou 300-600 tokens'
                    )
                self.ui_controls['archiviste_tokens'] = ui.number(
                    value=self.config.get('archiviste_tokens_per_message', -1),
                    min=-1, max=2000, step=50
                ).style('width: 100%; background: rgba(55, 65, 81, 0.4); color: #e5e7eb').props('outlined dense dark')

        # Paramètres compacts en grille
        with ui.grid(columns=2).style('gap: 16px; margin-bottom: 16px; width: 100%'):
            # Tokens Synthèse
            with ui.column():
                with ui.row().style('align-items: center; gap: 8px; margin-bottom: 8px'):
                    ui.label('Synthèse - Tokens max').style('font-weight: 500; color: #e5e7eb; font-size: 14px')
                    ui.icon('info').style('color: #a78bfa; font-size: 18px; cursor: help').tooltip(
                        'Limite de tokens pour la génération de la synthèse finale.\n'
                        'Augmenter si synthèses tronquées. Utiliser -1 pour illimité.\n\n'
                        'Recommandé: -1 (illimité) ou 600-1000 tokens'
                    )
                self.ui_controls['synthesis_tokens'] = ui.number(
                    value=self.config.get('synthesis_max_tokens', -1),
                    min=-1, max=2000, step=100
                ).style('width: 100%; background: rgba(55, 65, 81, 0.4); color: #e5e7eb').props('outlined dense dark')

            # Échanges max
            with ui.column():
                with ui.row().style('align-items: center; gap: 8px; margin-bottom: 8px'):
                    ui.label('Échanges max (dialogue)').style('font-weight: 500; color: #e5e7eb; font-size: 14px')
                    ui.icon('info').style('color: #fbbf24; font-size: 18px; cursor: help').tooltip(
                        'Nombre maximum d\'échanges dans le dialogue introspectif.\n'
                        'Plus = réflexion plus profonde mais plus lente.\n\n'
                        'Recommandé: 4-8 échanges pour équilibre profondeur/vitesse'
                    )
                self.ui_controls['max_exchanges'] = ui.number(
                    value=self.config.get('max_dialogue_exchanges', 6),
                    min=2, max=15, step=1
                ).style('width: 100%; background: rgba(55, 65, 81, 0.4); color: #e5e7eb').props('outlined dense dark')

        # Durée max - ligne complète
        with ui.column().style('margin-bottom: 16px'):
            with ui.row().style('align-items: center; gap: 8px; margin-bottom: 8px'):
                ui.label('Durée maximale introspection (minutes)').style('font-weight: 500; color: #e5e7eb; font-size: 14px')
                ui.icon('info').style('color: #f87171; font-size: 18px; cursor: help').tooltip(
                    'Timeout sécurité pour éviter introspections infinies.\n'
                    'L\'introspection s\'arrêtera automatiquement après ce délai.\n\n'
                    'Recommandé: 3-10 minutes'
                )
            self.ui_controls['max_duration'] = ui.number(
                value=self.config.get('max_introspection_duration', 300) / 60,
                min=1, max=20, step=0.5
            ).style('width: 100%; background: rgba(55, 65, 81, 0.4); color: #e5e7eb').props('outlined dense dark')

    def _create_memory_section(self):
        """Section 5: Sauvegarde mémoire - Simplifié"""
        ui.label('💾 Sauvegarde Mémoire').style('font-weight: 600; font-size: 18px; margin-bottom: 16px; color: #f3f4f6')

        # Simple note explicative
        ui.label('💡 L\'IA utilise la phrase magique "il faut que je me souvienne de ça:" pour marquer ce qu\'elle veut retenir.').style('color: #10b981; font-size: 14px; margin-bottom: 16px; font-style: italic')

        # Options simples en ligne
        with ui.row().style('gap: 24px; align-items: center; padding: 12px; background: rgba(55, 65, 81, 0.3); border-radius: 8px'):
            self.ui_controls['ia_decides_save'] = ui.checkbox(
                text="Système seuil automatique (optionnel)",
                value=self.config.get('ia_decides_save', False)
            ).style('color: #e5e7eb')
            
            ui.label('Seuil:').style('color: #9ca3af; margin-left: 16px')
            self.ui_controls['importance_threshold'] = ui.number(
                value=self.config.get('importance_threshold', 5),
                min=0, max=10, step=1
            ).style('width: 80px; background: rgba(55, 65, 81, 0.4); color: #e5e7eb').props('outlined dense dark')

    def _create_display_section(self):
        """Section 6: Affichage - Style amélioré"""
        ui.label('🎨 Affichage').style('font-weight: 600; font-size: 18px; margin-bottom: 16px; color: #f3f4f6')

        with ui.column().style('padding: 16px; background: rgba(55, 65, 81, 0.3); border-radius: 8px; border: 1px solid rgba(75, 85, 99, 0.3)'):
            with ui.row().style('align-items: center; gap: 12px; margin-bottom: 16px'):
                self.ui_controls['show_dialogue'] = ui.checkbox(
                    text="Afficher détails dialogue IA Principale ↔ Archiviste",
                    value=self.config.get('show_dialogue_details', True)
                ).style('font-weight: 500; color: #e5e7eb')
                ui.icon('info').style('color: #9ca3af; font-size: 18px; cursor: help').tooltip(
                    'Désactiver pour ne voir que la synthèse finale (mode clean).\n'
                    'Utile si vous voulez juste le résultat sans le processus.'
                )

            with ui.row().style('align-items: center; gap: 12px'):
                self.ui_controls['streaming_animation'] = ui.checkbox(
                    text="Animation streaming temps réel",
                    value=self.config.get('streaming_animation', True)
                ).style('font-weight: 500; color: #e5e7eb')
                ui.icon('info').style('color: #9ca3af; font-size: 18px; cursor: help').tooltip(
                    'Affiche les messages au fur et à mesure (comme ChatGPT).\n'
                    'Désactiver affiche tout d\'un coup (plus rapide mais moins fluide).'
                )

    def _create_action_buttons(self, dialog):
        """Boutons d'action - Style amélioré"""
        with ui.row().style('width: 100%; justify-content: space-between; gap: 12px; margin-top: 24px; padding-top: 20px; border-top: 1px solid rgba(75, 85, 99, 0.3)'):
            ui.button('🔄 Réinitialiser défauts', on_click=self._reset_to_defaults).props('flat size=md').style('color: #9ca3af')
            with ui.row().style('gap: 12px'):
                ui.button('💾 Sauvegarder', on_click=self._save_all_settings).props('color=primary size=md').style('min-width: 130px')
                ui.button('✖️ Fermer', on_click=lambda: dialog.close()).props('flat size=md').style('color: #9ca3af')

    def _on_extension_toggle(self, event):
        """Gestion toggle ON/OFF extension"""
        new_state = event.value
        print(f"[INTROSPECTION-MODAL-V2] 🎯 Extension {'ACTIVÉE' if new_state else 'DÉSACTIVÉE'}")

        self.config.set('extension_enabled', new_state)

        if self.on_toggle_callback:
            try:
                self.on_toggle_callback(new_state)
                print(f"[INTROSPECTION-MODAL-V2] ✅ Callback exécuté")
            except Exception as e:
                print(f"[INTROSPECTION-MODAL-V2] ❌ Erreur callback: {e}")

    def _save_all_settings(self):
        """Sauvegarde tous les paramètres avec validation"""
        try:
            # Vérifier que tous les contrôles existent (MAINTENANT AVEC ÉTAPE 0)
            required_controls = [
                'extension_toggle', 'introspection_mode',
                'etape0_instruction', 'etape1_instruction', 'etape23_ia_instruction', 'etape23_archiviste_instruction', 'etape4_instruction',
                'box_template', 'luna_tokens', 'archiviste_tokens', 'synthesis_tokens',
                'max_exchanges', 'max_duration', 'ia_decides_save', 'importance_threshold',
                'show_dialogue', 'streaming_animation'
            ]
            
            missing_controls = [ctrl for ctrl in required_controls if ctrl not in self.ui_controls]
            if missing_controls:
                ui.notify(f'❌ Contrôles manquants : {", ".join(missing_controls)}', type='negative')
                print(f"[INTROSPECTION-MODAL-V2] ❌ Contrôles manquants : {missing_controls}")
                return

            settings = {
                # Général
                'extension_enabled': self.ui_controls['extension_toggle'].value,
                'introspection_mode': self.ui_controls['introspection_mode'].value,

                # Instructions par étape (MAINTENANT AVEC ÉTAPE 0)
                'direct_memory_access_instruction': self.ui_controls['etape0_instruction'].value,
                'initial_analysis_instruction': self.ui_controls['etape1_instruction'].value,
                'main_ai_introspection_instruction': self.ui_controls['etape23_ia_instruction'].value,
                'archiviste_introspection_instruction': self.ui_controls['etape23_archiviste_instruction'].value,
                'synthesis_structure_instruction': self.ui_controls['etape4_instruction'].value,

                # Template
                'introspection_box_template': self.ui_controls['box_template'].value,

                # Technique
                'main_ai_tokens_per_message': int(self.ui_controls['luna_tokens'].value),
                'archiviste_tokens_per_message': int(self.ui_controls['archiviste_tokens'].value),
                'synthesis_max_tokens': int(self.ui_controls['synthesis_tokens'].value),
                'max_dialogue_exchanges': int(self.ui_controls['max_exchanges'].value),
                'max_introspection_duration': int(self.ui_controls['max_duration'].value * 60),

                # Sauvegarde
                'ia_decides_save': self.ui_controls['ia_decides_save'].value,
                'importance_threshold': int(self.ui_controls['importance_threshold'].value),

                # Affichage
                'show_dialogue_details': self.ui_controls['show_dialogue'].value,
                'streaming_animation': self.ui_controls['streaming_animation'].value,
            }

            # Validation template
            is_valid, invalid_vars = self.config.validate_template_variables(settings['introspection_box_template'])
            if not is_valid:
                ui.notify(f"⚠️ Variables template invalides: {', '.join(['{'+v+'}' for v in invalid_vars])}", type='warning')

            # Sauvegarde config
            for key, value in settings.items():
                self.config.set(key, value)

            ui.notify('✅ Paramètres sauvegardés et appliqués immédiatement', type='positive')

            # Callbacks
            if self.on_settings_callback:
                for key, value in settings.items():
                    try:
                        self.on_settings_callback(key, value)
                    except Exception as e:
                        print(f"[INTROSPECTION-MODAL-V2] ❌ Erreur callback {key}: {e}")

            self.popup_container.close()

        except Exception as e:
            ui.notify(f'❌ Erreur sauvegarde: {e}', type='negative')
            print(f"[INTROSPECTION-MODAL-V2] ❌ Erreur sauvegarde: {e}")

    def _reset_to_defaults(self):
        """Réinitialise tous les champs aux valeurs par défaut"""
        try:
            defaults = self.config.DEFAULT_SETTINGS

            self.ui_controls['extension_toggle'].value = defaults['extension_enabled']
            self.ui_controls['introspection_mode'].value = defaults['introspection_mode']
            self.ui_controls['etape0_instruction'].value = defaults['direct_memory_access_instruction']
            self.ui_controls['etape1_instruction'].value = defaults['initial_analysis_instruction']
            self.ui_controls['etape23_ia_instruction'].value = defaults['main_ai_introspection_instruction']
            self.ui_controls['etape23_archiviste_instruction'].value = defaults['archiviste_introspection_instruction']
            self.ui_controls['etape4_instruction'].value = defaults['synthesis_structure_instruction']
            self.ui_controls['box_template'].value = defaults['introspection_box_template']
            self.ui_controls['luna_tokens'].value = defaults['main_ai_tokens_per_message']
            self.ui_controls['archiviste_tokens'].value = defaults['archiviste_tokens_per_message']
            self.ui_controls['synthesis_tokens'].value = defaults['synthesis_max_tokens']
            self.ui_controls['max_exchanges'].value = defaults['max_dialogue_exchanges']
            self.ui_controls['max_duration'].value = defaults['max_introspection_duration'] / 60
            self.ui_controls['ia_decides_save'].value = defaults['ia_decides_save']
            self.ui_controls['importance_threshold'].value = defaults['importance_threshold']
            self.ui_controls['show_dialogue'].value = defaults['show_dialogue_details']
            self.ui_controls['streaming_animation'].value = defaults['streaming_animation']

            ui.notify('🔄 Paramètres réinitialisés aux valeurs par défaut', type='info')

        except Exception as e:
            print(f"[INTROSPECTION-MODAL-V2] ❌ Erreur reset: {e}")

    def _set_simple_template(self):
        """Template simple et lisible"""
        template = """🧠 **INTROSPECTION**

**Analyse:**
{main_ai_analysis}

**Dialogue:**
{dialogue_messages}

**Synthèse:**
{synthesis}"""
        self.ui_controls['box_template'].value = template

    def _set_detailed_template(self):
        """Template détaillé avec sauvegarde"""
        template = """=== 🔍 ANALYSE INITIALE ===
{main_ai_analysis}

=== 💬 DIALOGUE IA ↔ ARCHIVISTE ===
{dialogue_messages}

=== ✨ SYNTHÈSE FINALE ===
{synthesis}

---
💾 **Sauvegarde:** {save_decision} | **Importance:** {importance}/10
💡 **Raison:** {save_reason}"""
        self.ui_controls['box_template'].value = template

    def _set_minimal_template(self):
        """Template minimal - synthèse uniquement"""
        template = """💭 **Réflexion terminée**

{synthesis}"""
        self.ui_controls['box_template'].value = template

    def _preview_template(self):
        """Prévisualise le template avec des données d'exemple"""
        template = self.ui_controls['box_template'].value
        
        # Données d'exemple
        preview_data = {
            'main_ai_analysis': 'Analyse : L\'utilisateur demande des informations sur les IA conversationnelles. Il semble intéressé par l\'aspect technique.',
            'dialogue_messages': '''*IA Principale :* Archiviste, rappelle-moi mes souvenirs sur les discussions techniques avec cet utilisateur.
*Archiviste :* [3 souvenirs trouvés] L'utilisateur a souvent posé des questions approfondies sur l'architecture des systèmes IA...
*IA Principale :* Et ses préférences de communication ?
*Archiviste :* Il préfère les explications détaillées avec des exemples concrets.''',
            'synthesis': '''**Insights principaux :** L'utilisateur privilégie la compréhension technique approfondie
**Souvenirs mobilisés :** 3 conversations sur l'architecture IA, préférences pédagogiques
**Conclusion :** Adapter ma réponse avec plus de détails techniques''',
            'save_decision': 'yes',
            'importance': '7',
            'save_reason': 'Interaction riche révélant les préférences utilisateur'
        }
        
        try:
            preview_result = template.format(**preview_data)
            
            # Afficher dans une dialog de prévisualisation
            with ui.dialog().props('maximized') as preview_dialog:
                with ui.card().style('width: 800px; max-height: 80vh; overflow-y: auto; background: #1f2937; color: #e5e7eb'):
                    ui.html('<h3 style="margin-bottom: 16px; color: #fbbf24;">🔍 Prévisualisation du Template</h3>')
                    
                    with ui.scroll_area().style('height: 500px; background: rgba(55, 65, 81, 0.3); padding: 16px; border-radius: 8px; font-family: system-ui'):
                        ui.html(f'<pre style="white-space: pre-wrap; color: #e5e7eb; line-height: 1.6;">{preview_result}</pre>')
                    
                    with ui.row().style('justify-content: flex-end; margin-top: 16px'):
                        ui.button('Fermer', on_click=lambda: preview_dialog.close()).props('color=primary')
            
            preview_dialog.open()
            
        except KeyError as e:
            ui.notify(f'❌ Variable inconnue dans template : {{{e.args[0]}}}', type='negative')
        except Exception as e:
            ui.notify(f'❌ Erreur prévisualisation : {e}', type='negative')

    def show_popup(self):
        """Affiche le popup paramètres"""
        if self.popup_container is None:
            self.create_popup()

        if self.popup_container:
            self.popup_container.open()
            self.is_popup_visible = True
            print("[INTROSPECTION-MODAL-V2] ✅ Popup affiché")

    def close_popup(self):
        """Ferme le popup"""
        if self.popup_container:
            try:
                self.popup_container.close()
                self.is_popup_visible = False
                print("[INTROSPECTION-MODAL-V2] ✅ Popup fermé")
            except Exception as e:
                print(f"[INTROSPECTION-MODAL-V2] ❌ Erreur fermeture: {e}")

    def _force_refresh_tabs(self):
        """Force le rafraîchissement des onglets pour corriger l'affichage vide"""
        try:
            print("[INTROSPECTION-MODAL-V2] 🔄 Force refresh des onglets...")
            
            # Vérifier que les contrôles sont bien créés avec du contenu
            debug_info = []
            for key, control in self.ui_controls.items():
                if 'instruction' in key or key == 'box_template':
                    if hasattr(control, 'value'):
                        value_len = len(control.value) if control.value else 0
                        debug_info.append(f"{key}: {value_len} chars")
                        
                        # Force un update si vide
                        if value_len == 0:
                            print(f"[DEBUG] Contrôle {key} vide, tentative de recharge...")
                            if key == 'etape1_instruction':
                                control.value = self.config.get('initial_analysis_instruction', '# En attente...')
                            elif key == 'etape23_ia_instruction':
                                control.value = self.config.get('main_ai_introspection_instruction', '# En attente...')
                            elif key == 'etape23_archiviste_instruction':
                                control.value = self.config.get('archiviste_introspection_instruction', '# En attente...')
                            elif key == 'etape4_instruction':
                                control.value = self.config.get('synthesis_structure_instruction', '# En attente...')
                            elif key == 'box_template':
                                control.value = self.config.get('introspection_box_template', '# En attente...')
            
            print(f"[INTROSPECTION-MODAL-V2] 📊 État contrôles: {', '.join(debug_info)}")
            
        except Exception as e:
            print(f"[INTROSPECTION-MODAL-V2] ❌ Erreur refresh: {e}")

    def cleanup(self):
        """Nettoyage ressources"""
        if self.popup_container:
            try:
                self.popup_container.close()
            except:
                pass
            self.popup_container = None

        self.is_popup_visible = False
        print("[INTROSPECTION-MODAL-V2] ✅ Cleanup terminé")


# Exports
__all__ = ['IntrospectionParametersModalV2']
