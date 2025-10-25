# 🧠 Introspection - Interface Paramètres v3.0 SIMPLIFIÉE
# Interface verticale unique - Toutes les 5 étapes visibles et éditables simultanément

"""
Interface Paramètres Introspection v3.0 - SIMPLIFIÉE VERTICALE

AMÉLIORATION MAJEURE:
- Suppression des 5 onglets complexes
- Interface verticale UNIQUE avec scroll
- Toutes les 5 étapes visibles simultanément
- Tailles uniformes (400px) pour tous les textarea
- Sauvegarde avec application IMMÉDIATE selon principe d'Action Immédiate

SECTIONS:
1. Configuration Base (ON/OFF, Mode)
2. Instructions 5 Étapes (toutes visibles)
3. Paramètres Techniques
4. Sauvegarde & Application Temps Réel
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


class IntrospectionParametersModalV3Simple:
    """
    Interface paramètres Introspection v3.0 - VERSION SIMPLIFIÉE VERTICALE
    
    PRINCIPE: Toutes les 5 étapes modifiables dans une interface unique sans onglets
    - Pas de navigation complexe
    - Tailles uniformes (400px)
    - Application immédiate des changements
    """

    def __init__(self, config, on_toggle_callback, on_settings_callback, core_reference=None):
        """
        Initialise interface simplifiée v3.0

        Args:
            config: Instance CognitiveMirrorConfig
            on_toggle_callback: Callback extension ON/OFF
            on_settings_callback: Callback changement paramètres avec APPLICATION IMMÉDIATE
            core_reference: Référence au CognitiveMirrorCore
        """
        self.config = config
        self.on_toggle_callback = on_toggle_callback
        self.on_settings_callback = on_settings_callback
        self.core_reference = core_reference

        # État popup
        self.popup_container = None
        self.is_popup_visible = False

        # Contrôles UI - organisés par section
        self.ui_controls = {}

        print("[INTROSPECTION-V3-SIMPLE] 🆕 Interface simplifiée v3.0 initialisée")

    def create_popup(self):
        """Crée popup paramètres SIMPLE VERTICAL - toutes étapes visibles"""
        if not NICEGUI_AVAILABLE:
            print("[INTROSPECTION-V3-SIMPLE] ❌ NiceGUI non disponible")
            return None

        with ui.dialog().props('persistent maximized') as dialog:
            self.popup_container = dialog

            # Container principal avec scroll
            with ui.card().style('width: 1000px; max-height: 90vh; overflow-y: auto; padding: 32px; background: #1f2937; border-radius: 12px; box-shadow: 0 8px 32px rgba(0,0,0,0.6);'):
                
                # HEADER PRINCIPAL
                ui.html('<h1 style="margin: 0 0 32px 0; text-align: center; color: #f3f4f6; font-size: 28px;">🧠 Configuration Introspection - Interface Simplifiée</h1>')
                ui.html('<p style="text-align: center; color: #9ca3af; margin-bottom: 40px; font-size: 16px;">Toutes les 5 étapes modifiables simultanément - Application immédiate</p>')

                # SECTION 1: CONFIGURATION BASE
                self._create_base_config_section()
                self._create_separator()

                # SECTION 2: INSTRUCTIONS 5 ÉTAPES (TOUTES VISIBLES)
                self._create_instructions_section_unified()
                self._create_separator()

                # SECTION 3: PARAMÈTRES TECHNIQUES
                self._create_technical_section()
                self._create_separator()

                # SECTION 4: TEMPLATE AFFICHAGE
                self._create_template_section()
                self._create_separator()

                # SECTION 5: BOUTONS ACTION
                self._create_action_buttons(dialog)

        print("[INTROSPECTION-V3-SIMPLE] ✅ Interface simplifiée créée")
        return dialog

    def _create_base_config_section(self):
        """Section 1: Configuration de base - Compact et claire"""
        ui.html('<h2 style="color: #60a5fa; font-size: 22px; margin-bottom: 20px; padding: 12px; background: rgba(96, 165, 250, 0.1); border-radius: 8px; border-left: 4px solid #60a5fa;">⚙️ Configuration de Base</h2>')

        with ui.row().style('gap: 32px; margin-bottom: 24px; align-items: center'):
            # Toggle ON/OFF
            with ui.column():
                ui.label('Extension Active').style('font-weight: 600; font-size: 16px; color: #e5e7eb; margin-bottom: 8px')
                current_state = self.config.get('extension_enabled', False)
                self.ui_controls['extension_toggle'] = ui.switch(
                    value=current_state
                ).on('change', self._on_extension_toggle).props('color=primary size=lg')
                ui.label('OFF = Phrases magiques seulement' if not current_state else 'ON = Introspection active').style('color: #9ca3af; font-size: 14px')

            # Mode introspection
            with ui.column():
                ui.label('Mode Introspection').style('font-weight: 600; font-size: 16px; color: #e5e7eb; margin-bottom: 8px')
                self.ui_controls['introspection_mode'] = ui.select(
                    options=['phrases_magiques', 'systematique'],
                    value='phrases_magiques' if self.config.get('introspection_mode', 'on_demand') == 'on_demand' else 'systematique',
                    with_input=False
                ).style('width: 250px; background: rgba(55, 65, 81, 0.4); color: #e5e7eb').props('outlined dense dark')
                ui.label('Phrases magiques = Sur déclenchement | Systématique = Chaque message').style('color: #9ca3af; font-size: 14px')

    def _create_instructions_section_unified(self):
        """Section 2: Toutes les 5 étapes UNIFIÉES dans une seule section"""
        ui.html('<h2 style="color: #34d399; font-size: 22px; margin-bottom: 20px; padding: 12px; background: rgba(52, 211, 153, 0.1); border-radius: 8px; border-left: 4px solid #34d399;">📝 Instructions des 5 Étapes - Toutes Modifiables</h2>')

        ui.html('<p style="color: #9ca3af; margin-bottom: 24px; font-size: 16px;">✨ Toutes les étapes sont visibles simultanément. Tailles uniformes de 400px pour une meilleure lisibilité.</p>')

        # ÉTAPE 0: Accès Mémoire Direct (PRIVÉE)
        self._create_step_textarea(
            step_number="0",
            title="🧠 Accès Mémoire Direct",
            description="Accès direct et non censuré à la mémoire FAISS/SQLite (étape privée, non visible utilisateur)",
            config_key="direct_memory_access_instruction",
            ui_key="etape0_instruction",
            color="#8b5cf6"  # Violet
        )

        # ÉTAPE 1: Analyse Initiale
        self._create_step_textarea(
            step_number="1", 
            title="🔍 Analyse Initiale",
            description="Analyse rapide de la demande utilisateur pour identifier les concepts clés",
            config_key="initial_analysis_instruction",
            ui_key="etape1_instruction", 
            color="#3b82f6"  # Bleu
        )

        # ÉTAPES 2-3: Dialogue (2 champs côte à côte)
        self._create_dialogue_section()

        # ÉTAPE 4A: Synthèse Complète (Zone Introspection)
        self._create_step_textarea(
            step_number="4A",
            title="✨ Synthèse Complète (Zone Introspection)", 
            description="Génération de la synthèse structurée complète avec toute l'analyse (visible dans la boîte introspection)",
            config_key="synthesis_structure_instruction",
            ui_key="etape4a_instruction",
            color="#a78bfa"  # Violet clair
        )

        # ÉTAPE 4B: Extraction Réponse Utilisateur (Zone Conversation)
        self._create_step_textarea(
            step_number="4B",
            title="💬 Réponse Utilisateur (Zone Conversation)", 
            description="Extraction de la réponse finale pour l'utilisateur (visible dans la conversation, sans structure d'analyse)",
            config_key="user_response_extraction_instruction",
            ui_key="etape4b_instruction",
            color="#10b981"  # Vert
        )

    def _create_step_textarea(self, step_number, title, description, config_key, ui_key, color):
        """Crée un textarea pour une étape avec format uniforme"""
        # Header étape
        ui.html(f'<h3 style="color: {color}; font-size: 18px; margin: 24px 0 12px 0; padding: 8px; background: rgba({self._hex_to_rgba(color)}, 0.1); border-radius: 6px; border-left: 3px solid {color};">ÉTAPE {step_number}: {title}</h3>')
        ui.html(f'<p style="color: #9ca3af; margin-bottom: 16px; font-size: 14px;">{description}</p>')

        # Textarea uniforme 400px
        current_value = self.config.get(config_key, '')
        if not current_value:
            current_value = f"# Instructions Étape {step_number}\n\nEn attente de chargement..."

        self.ui_controls[ui_key] = ui.textarea(
            value=current_value,
            placeholder=f'Instructions pour l\'étape {step_number}...'
        ).style('width: 100%; height: 400px; font-family: "Consolas", "Monaco", monospace; font-size: 13px; background: rgba(55, 65, 81, 0.4); color: #e5e7eb; border: 1px solid rgba(75, 85, 99, 0.3); border-radius: 8px').props('outlined dark')

        print(f"[INTROSPECTION-V3-SIMPLE] ✅ Étape {step_number} créée: {len(current_value)} chars")

    def _create_dialogue_section(self):
        """Étapes 2-3: Section dialogue avec 2 champs côte à côte"""
        ui.html('<h3 style="color: #34d399; font-size: 18px; margin: 24px 0 12px 0; padding: 8px; background: rgba(52, 211, 153, 0.1); border-radius: 6px; border-left: 3px solid #34d399;">ÉTAPES 2-3: 💬 Dialogue IA Principale ↔ Archiviste</h3>')
        ui.html('<p style="color: #9ca3af; margin-bottom: 16px; font-size: 14px;">Instructions pour les 2 acteurs du dialogue introspectif (côte à côte pour comparaison)</p>')

        with ui.row().style('gap: 20px; margin-bottom: 16px'):
            # IA Principale
            with ui.column().style('flex: 1; min-width: 450px'):
                ui.html('<h4 style="color: #60a5fa; margin-bottom: 8px;">🤖 IA Principale</h4>')
                
                current_ia_value = self.config.get('main_ai_introspection_instruction', '')
                if not current_ia_value:
                    current_ia_value = "# Instructions IA Principale\n\nEn attente de chargement..."
                    
                self.ui_controls['etape23_ia_instruction'] = ui.textarea(
                    value=current_ia_value,
                    placeholder='Instructions pour l\'IA Principale en dialogue...'
                ).style('width: 100%; height: 400px; font-family: "Consolas", "Monaco", monospace; font-size: 13px; background: rgba(55, 65, 81, 0.4); color: #e5e7eb; border: 1px solid rgba(96, 165, 250, 0.3); border-radius: 8px').props('outlined dark')

            # Archiviste  
            with ui.column().style('flex: 1; min-width: 450px'):
                ui.html('<h4 style="color: #34d399; margin-bottom: 8px;">📚 Archiviste</h4>')
                
                current_arch_value = self.config.get('archiviste_introspection_instruction', '')
                if not current_arch_value:
                    current_arch_value = "# Instructions Archiviste\n\nEn attente de chargement..."
                    
                self.ui_controls['etape23_archiviste_instruction'] = ui.textarea(
                    value=current_arch_value,
                    placeholder='Instructions pour l\'Archiviste en consultation...'
                ).style('width: 100%; height: 400px; font-family: "Consolas", "Monaco", monospace; font-size: 13px; background: rgba(55, 65, 81, 0.4); color: #e5e7eb; border: 1px solid rgba(52, 211, 153, 0.3); border-radius: 8px').props('outlined dark')

        print(f"[INTROSPECTION-V3-SIMPLE] ✅ Dialogue section créée: IA ({len(current_ia_value)} chars), Archiviste ({len(current_arch_value)} chars)")

    def _create_technical_section(self):
        """Section 3: Paramètres techniques - Layout compact"""
        ui.html('<h2 style="color: #fbbf24; font-size: 22px; margin-bottom: 20px; padding: 12px; background: rgba(251, 191, 36, 0.1); border-radius: 8px; border-left: 4px solid #fbbf24;">🎛️ Paramètres Techniques</h2>')

        # Grille 3x2 pour les paramètres numériques
        with ui.grid(columns=3).style('gap: 20px; margin-bottom: 20px'):
            # Tokens IA Principale
            with ui.column():
                ui.label('Tokens IA Principale').style('font-weight: 500; color: #e5e7eb; margin-bottom: 8px')
                self.ui_controls['main_ai_tokens'] = ui.number(
                    value=self.config.get('main_ai_tokens_per_message', -1),
                    min=-1, max=2000, step=50
                ).style('width: 100%; background: rgba(55, 65, 81, 0.4); color: #e5e7eb').props('outlined dense dark')
                ui.label('-1 = illimité').style('color: #9ca3af; font-size: 12px')

            # Tokens Archiviste
            with ui.column():
                ui.label('Tokens Archiviste').style('font-weight: 500; color: #e5e7eb; margin-bottom: 8px')
                self.ui_controls['archiviste_tokens'] = ui.number(
                    value=self.config.get('archiviste_tokens_per_message', -1),
                    min=-1, max=2000, step=50
                ).style('width: 100%; background: rgba(55, 65, 81, 0.4); color: #e5e7eb').props('outlined dense dark')
                ui.label('-1 = illimité').style('color: #9ca3af; font-size: 12px')

            # Tokens Synthèse
            with ui.column():
                ui.label('Tokens Synthèse').style('font-weight: 500; color: #e5e7eb; margin-bottom: 8px')
                self.ui_controls['synthesis_tokens'] = ui.number(
                    value=self.config.get('synthesis_max_tokens', -1),
                    min=-1, max=2000, step=100
                ).style('width: 100%; background: rgba(55, 65, 81, 0.4); color: #e5e7eb').props('outlined dense dark')
                ui.label('-1 = illimité').style('color: #9ca3af; font-size: 12px')

        # Ligne 2: Échanges et Durée
        with ui.row().style('gap: 32px; align-items: center'):
            with ui.column():
                ui.label('Échanges Maximum').style('font-weight: 500; color: #e5e7eb; margin-bottom: 8px')
                self.ui_controls['max_exchanges'] = ui.number(
                    value=self.config.get('max_dialogue_exchanges', 6),
                    min=2, max=15, step=1
                ).style('width: 150px; background: rgba(55, 65, 81, 0.4); color: #e5e7eb').props('outlined dense dark')
                ui.label('Dialogue IA ↔ Archiviste').style('color: #9ca3af; font-size: 12px')

            with ui.column():
                ui.label('Durée Max (minutes)').style('font-weight: 500; color: #e5e7eb; margin-bottom: 8px')
                self.ui_controls['max_duration'] = ui.number(
                    value=self.config.get('max_introspection_duration', 300) / 60,
                    min=1, max=20, step=0.5
                ).style('width: 150px; background: rgba(55, 65, 81, 0.4); color: #e5e7eb').props('outlined dense dark')
                ui.label('Timeout sécurité').style('color: #9ca3af; font-size: 12px')

    def _create_template_section(self):
        """Section 4: Template d'affichage"""
        ui.html('<h2 style="color: #f87171; font-size: 22px; margin-bottom: 20px; padding: 12px; background: rgba(248, 113, 113, 0.1); border-radius: 8px; border-left: 4px solid #f87171;">🎨 Template d\'Affichage</h2>')

        # Boutons templates prédéfinis
        with ui.row().style('gap: 12px; margin-bottom: 16px'):
            ui.button('📋 Simple', on_click=lambda: self._set_simple_template()).props('size=sm color=primary')
            ui.button('📊 Détaillé', on_click=lambda: self._set_detailed_template()).props('size=sm')
            ui.button('🎯 Minimal', on_click=lambda: self._set_minimal_template()).props('size=sm')

        # Template textarea
        current_template = self.config.get('introspection_box_template', '')
        if not current_template:
            current_template = "# Template d'affichage\n\nEn attente de chargement..."

        self.ui_controls['box_template'] = ui.textarea(
            value=current_template,
            placeholder='Template d\'affichage des résultats...'
        ).style('width: 100%; height: 300px; font-family: "Consolas", "Monaco", monospace; font-size: 13px; background: rgba(55, 65, 81, 0.4); color: #e5e7eb; border: 1px solid rgba(248, 113, 113, 0.3); border-radius: 8px').props('outlined dark')

    def _create_action_buttons(self, dialog):
        """Section 5: Boutons d'action avec application immédiate"""
        self._create_separator()
        
        ui.html('<h2 style="color: #10b981; font-size: 22px; margin-bottom: 20px; padding: 12px; background: rgba(16, 185, 129, 0.1); border-radius: 8px; border-left: 4px solid #10b981;">💾 Sauvegarde & Application</h2>')
        
        ui.html('<p style="color: #10b981; margin-bottom: 16px; font-size: 16px; font-weight: 500;">✨ Selon le principe d\'Action Immédiate : toute modification sera appliquée instantanément</p>')

        with ui.row().style('width: 100%; justify-content: space-between; gap: 16px; padding: 20px; background: rgba(16, 185, 129, 0.05); border-radius: 8px'):
            ui.button('🔄 Réinitialiser', on_click=self._reset_to_defaults).props('flat size=lg color=grey').style('min-width: 160px')
            
            with ui.row().style('gap: 16px'):
                ui.button('💾 SAUVEGARDER & APPLIQUER', on_click=self._save_and_apply_immediately).props('color=green size=lg').style('min-width: 250px; font-weight: bold')
                ui.button('❌ Fermer', on_click=lambda: dialog.close()).props('flat size=lg color=grey').style('min-width: 120px')

    def _save_and_apply_immediately(self):
        """Sauvegarde avec application IMMÉDIATE selon principe d'Action Immédiate"""
        try:
            print("[INTROSPECTION-V3-SIMPLE] 🔄 Début sauvegarde avec application immédiate...")

            # Vérifier contrôles
            required_controls = [
                'extension_toggle', 'introspection_mode', 
                'etape0_instruction', 'etape1_instruction', 
                'etape23_ia_instruction', 'etape23_archiviste_instruction', 
                'etape4a_instruction', 'etape4b_instruction',
                'box_template', 'main_ai_tokens', 'archiviste_tokens', 'synthesis_tokens',
                'max_exchanges', 'max_duration'
            ]

            missing = [ctrl for ctrl in required_controls if ctrl not in self.ui_controls]
            if missing:
                ui.notify(f'❌ Contrôles manquants: {", ".join(missing)}', type='negative')
                return

            # Construire settings avec conversion français → technique
            french_mode = self.ui_controls['introspection_mode'].value
            technical_mode = 'on_demand' if french_mode == 'phrases_magiques' else 'always'
            
            settings = {
                # Configuration base
                'extension_enabled': self.ui_controls['extension_toggle'].value,
                'introspection_mode': technical_mode,

                # Instructions 6 étapes (4A + 4B séparées)
                'direct_memory_access_instruction': self.ui_controls['etape0_instruction'].value,
                'initial_analysis_instruction': self.ui_controls['etape1_instruction'].value,
                'main_ai_introspection_instruction': self.ui_controls['etape23_ia_instruction'].value,
                'archiviste_introspection_instruction': self.ui_controls['etape23_archiviste_instruction'].value,
                'synthesis_structure_instruction': self.ui_controls['etape4a_instruction'].value,
                'user_response_extraction_instruction': self.ui_controls['etape4b_instruction'].value,

                # Template
                'introspection_box_template': self.ui_controls['box_template'].value,

                # Paramètres techniques
                'main_ai_tokens_per_message': int(self.ui_controls['main_ai_tokens'].value),
                'archiviste_tokens_per_message': int(self.ui_controls['archiviste_tokens'].value),
                'synthesis_max_tokens': int(self.ui_controls['synthesis_tokens'].value),
                'max_dialogue_exchanges': int(self.ui_controls['max_exchanges'].value),
                'max_introspection_duration': int(self.ui_controls['max_duration'].value * 60),

                # Affichage par défaut
                'show_dialogue_details': True,
                'streaming_animation': True,
                'ia_decides_save': False,
                'importance_threshold': 5
            }

            # ÉTAPE 1: Sauvegarde dans config
            print("[INTROSPECTION-V3-SIMPLE] 📝 Sauvegarde config...")
            for key, value in settings.items():
                self.config.set(key, value)

            # ÉTAPE 2: Application immédiate via callbacks 
            print("[INTROSPECTION-V3-SIMPLE] ⚡ Application immédiate...")
            changes_applied = 0
            
            if self.on_settings_callback:
                for key, value in settings.items():
                    try:
                        self.on_settings_callback(key, value)
                        changes_applied += 1
                    except Exception as e:
                        print(f"[INTROSPECTION-V3-SIMPLE] ⚠️ Erreur callback {key}: {e}")

            # ÉTAPE 3: Notification utilisateur
            ui.notify(f'✅ {len(settings)} paramètres sauvegardés et {changes_applied} appliqués IMMÉDIATEMENT', type='positive')
            print(f"[INTROSPECTION-V3-SIMPLE] ✅ {len(settings)} paramètres sauvegardés, {changes_applied} appliqués")

            # Fermer popup
            if self.popup_container:
                self.popup_container.close()

        except Exception as e:
            error_msg = f"Erreur sauvegarde: {str(e)}"
            ui.notify(f'❌ {error_msg}', type='negative')
            print(f"[INTROSPECTION-V3-SIMPLE] ❌ {error_msg}")
            print(f"[INTROSPECTION-V3-SIMPLE] 🔍 Traceback: {traceback.format_exc()}")

    def _on_extension_toggle(self, event):
        """Toggle extension avec effet immédiat"""
        new_state = event.value
        print(f"[INTROSPECTION-V3-SIMPLE] 🎯 Extension {'ACTIVÉE' if new_state else 'DÉSACTIVÉE'}")

        # Application immédiate
        self.config.set('extension_enabled', new_state)

        if self.on_toggle_callback:
            try:
                self.on_toggle_callback(new_state)
            except Exception as e:
                print(f"[INTROSPECTION-V3-SIMPLE] ❌ Erreur toggle callback: {e}")

    def _reset_to_defaults(self):
        """Remet tous les champs aux valeurs par défaut"""
        try:
            defaults = self.config.DEFAULT_SETTINGS

            self.ui_controls['extension_toggle'].value = defaults['extension_enabled']
            # Conversion technique → français pour affichage
            technical_mode = defaults['introspection_mode']
            french_mode = 'phrases_magiques' if technical_mode == 'on_demand' else 'systematique'
            self.ui_controls['introspection_mode'].value = french_mode
            self.ui_controls['etape0_instruction'].value = defaults['direct_memory_access_instruction']
            self.ui_controls['etape1_instruction'].value = defaults['initial_analysis_instruction']
            self.ui_controls['etape23_ia_instruction'].value = defaults['main_ai_introspection_instruction']
            self.ui_controls['etape23_archiviste_instruction'].value = defaults['archiviste_introspection_instruction']
            self.ui_controls['etape4a_instruction'].value = defaults['synthesis_structure_instruction']
            self.ui_controls['etape4b_instruction'].value = defaults['user_response_extraction_instruction']
            self.ui_controls['box_template'].value = defaults['introspection_box_template']
            self.ui_controls['main_ai_tokens'].value = defaults['main_ai_tokens_per_message']
            self.ui_controls['archiviste_tokens'].value = defaults['archiviste_tokens_per_message']
            self.ui_controls['synthesis_tokens'].value = defaults['synthesis_max_tokens']
            self.ui_controls['max_exchanges'].value = defaults['max_dialogue_exchanges']
            self.ui_controls['max_duration'].value = defaults['max_introspection_duration'] / 60

            ui.notify('🔄 Paramètres réinitialisés aux valeurs par défaut', type='info')

        except Exception as e:
            print(f"[INTROSPECTION-V3-SIMPLE] ❌ Erreur reset: {e}")

    def _set_simple_template(self):
        """Template simple"""
        template = """🧠 **Introspection**

**Analyse:** {main_ai_analysis}

**Dialogue:** {dialogue_messages}

**Synthèse:** {synthesis}"""
        self.ui_controls['box_template'].value = template

    def _set_detailed_template(self):
        """Template détaillé"""
        template = """=== 🔍 ANALYSE INITIALE ===
{main_ai_analysis}

=== 💬 DIALOGUE IA ↔ ARCHIVISTE ===
{dialogue_messages}

=== ✨ SYNTHÈSE FINALE ===
{synthesis}

---
💾 **Sauvegarde:** {save_decision} | **Importance:** {importance}/10"""
        self.ui_controls['box_template'].value = template

    def _set_minimal_template(self):
        """Template minimal"""
        template = """💭 **Réflexion**
{synthesis}"""
        self.ui_controls['box_template'].value = template

    def _create_separator(self):
        """Crée un séparateur visuel"""
        ui.separator().style('margin: 32px 0; background: rgba(75, 85, 99, 0.3); height: 2px')

    def _hex_to_rgba(self, hex_color):
        """Convertit couleur hex en rgba (helper pour CSS)"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"{r}, {g}, {b}"

    def show_popup(self):
        """Affiche le popup"""
        if not self.popup_container:
            self.create_popup()
        
        if self.popup_container:
            self.popup_container.open()
            self.is_popup_visible = True
            print("[INTROSPECTION-V3-SIMPLE] ✅ Popup affiché")

    def close_popup(self):
        """Ferme le popup"""
        if self.popup_container:
            try:
                self.popup_container.close()
                self.is_popup_visible = False
                print("[INTROSPECTION-V3-SIMPLE] ✅ Popup fermé")
            except Exception as e:
                print(f"[INTROSPECTION-V3-SIMPLE] ❌ Erreur fermeture: {e}")

    def cleanup(self):
        """Nettoyage ressources"""
        if self.popup_container:
            try:
                self.popup_container.close()
            except:
                pass
            self.popup_container = None

        self.is_popup_visible = False
        print("[INTROSPECTION-V3-SIMPLE] ✅ Cleanup terminé")


# Export
__all__ = ['IntrospectionParametersModalV3Simple']