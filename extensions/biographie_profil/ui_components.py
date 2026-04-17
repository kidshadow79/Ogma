"""
Composants Interface Utilisateur pour l'extension Biographie Profil
================================================================

Gère:
- Bouton d'extension (icône plume)
- Modal de paramètres avec ON/OFF, INFO, actions
- Intégration CSS cohérente avec OGMA
"""

from nicegui import ui
from typing import Optional
import asyncio
from .notification_cleaner import notification_cleaner

class BiographyUI:
    """Interface utilisateur de l'extension biographie"""
    
    def __init__(self, settings_manager, biography_manager):
        self.settings_manager = settings_manager
        self.biography_manager = biography_manager
        self.modal_dialog = None
        self.name_input = None  # Champ de saisie nom utilisateur (initialisé dans la modal)
        self.volume2_instructions = None  # Champ instructions Volume 2 (initialisé dans la modal)

        # Charger l'état sauvegardé ou défaut à False
        self.is_enabled = self._load_extension_state()

        print(f"[BIOGRAPHY-UI] ✅ Interface utilisateur initialisée (état: {'activée' if self.is_enabled else 'désactivée'})")

    def _load_extension_state(self):
        """Charge l'état sauvegardé de l'extension"""
        try:
            import json
            from pathlib import Path

            config_file = Path("data/extensions/biography_config.json")

            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    enabled = config.get('is_enabled', False)
                    print(f"[BIOGRAPHY-UI] 📂 État chargé depuis config: {'activée' if enabled else 'désactivée'}")
                    return enabled
            else:
                print(f"[BIOGRAPHY-UI] 📂 Aucune config trouvée, défaut: désactivée")
                return False

        except Exception as e:
            print(f"[BIOGRAPHY-UI] ❌ Erreur chargement config: {e}")
            return False

    def _save_extension_state(self):
        """Sauvegarde l'état de l'extension"""
        try:
            import json
            from pathlib import Path

            config_dir = Path("data/extensions")
            config_dir.mkdir(parents=True, exist_ok=True)

            config_file = config_dir / "biography_config.json"

            config = {
                'is_enabled': self.is_enabled,
                'last_updated': Path(__file__).stat().st_mtime
            }

            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            print(f"[BIOGRAPHY-UI] 💾 État sauvegardé: {'activée' if self.is_enabled else 'désactivée'}")
            return True

        except Exception as e:
            print(f"[BIOGRAPHY-UI] ❌ Erreur sauvegarde config: {e}")
            return False

    def create_extension_button(self):
        """
        Crée le bouton d'extension (icône plume)
        Style cohérent avec le bouton journal existant
        """
        try:
            with ui.button().classes('biography-header-btn').props('title="Biographie Profil"').style(
                'width: 50px; height: 50px; border-radius: 50%; '
                'background: linear-gradient(135deg, #2E4057 0%, #4A90E2 100%); '
                'border: 2px solid #1E3A8A; box-shadow: 0 4px 12px rgba(46, 64, 87, 0.3); '
                'display: flex; align-items: center; justify-content: center; '
                'transition: all 0.3s ease; cursor: pointer; padding: 0; margin-right: 10px;'
            ) as biography_btn:
                # Icône plume (caractère Unicode)
                ui.html('<div style="color: white; font-size: 24px; line-height: 1;">✒️</div>')
                
                # Action au clic
                biography_btn.on('click', self.open_settings_modal)
            
            print("[BIOGRAPHY-UI] ✅ Bouton extension créé")
            return biography_btn
            
        except Exception as e:
            print(f"[BIOGRAPHY-UI] ❌ Erreur création bouton: {e}")
            return None
    
    def open_settings_modal(self):
        """Ouvre la modal de paramètres de l'extension"""
        try:
            # Vérifier si une modal est déjà ouverte
            if self.modal_dialog is not None:
                print("[BIOGRAPHY-UI] ℹ️ Modal déjà ouverte, fermeture de l'ancienne")
                try:
                    self.modal_dialog.close()
                except:
                    pass

            # Nettoyer les références précédentes
            self.modal_dialog = None
            self.name_input = None
            self.volume2_instructions = None

            with ui.dialog() as dialog, ui.card().style('min-width: 600px; max-width: 800px'):
                dialog.open()
                self.modal_dialog = dialog
                
                # Titre
                with ui.row().classes('w-full justify-between items-center mb-4'):
                    ui.label('🖋️ Extension Biographie Profil').classes('text-xl font-bold')
                    ui.button('✕', on_click=lambda: self._close_modal(dialog)).classes('text-lg').style('background: none; border: none')
                
                # Section ON/OFF
                with ui.row().classes('w-full items-center mb-6'):
                    ui.label('Statut de l\'extension:').classes('font-semibold')
                    ui.space()

                    # Bouton toggle custom pour éviter les problèmes de sérialisation Switch
                    toggle_text = "✅ Activée" if self.is_enabled else "❌ Désactivée"
                    toggle_color = "bg-green-500" if self.is_enabled else "bg-red-500"

                    def toggle_and_update():
                        self.is_enabled = not self.is_enabled
                        status = "activée" if self.is_enabled else "désactivée"
                        print(f"[BIOGRAPHY-UI] 🔄 Extension {status}")

                        # Sauvegarde automatique de l'état
                        save_success = self._save_extension_state()

                        # Mettre à jour le bouton
                        new_text = "✅ Activée" if self.is_enabled else "❌ Désactivée"
                        new_color = "bg-green-500" if self.is_enabled else "bg-red-500"
                        status_toggle.text = new_text
                        status_toggle.classes(f'{new_color} text-white px-4 py-2 rounded')

                        # Notification
                        if self.is_enabled:
                            msg = '🖋️ Extension Biographie Profil activée'
                            if save_success:
                                msg += ' et sauvegardée'
                            ui.notify(msg, type='positive')
                        else:
                            msg = '🖋️ Extension Biographie Profil désactivée'
                            if save_success:
                                msg += ' et sauvegardée'
                            ui.notify(msg, type='info')

                    status_toggle = ui.button(
                        toggle_text,
                        on_click=toggle_and_update
                    ).classes(f'{toggle_color} text-white px-4 py-2 rounded')
                
                ui.separator()
                
                # Section INFO
                with ui.column().classes('w-full mb-6'):
                    ui.label('ℹ️ À propos de cette extension').classes('text-lg font-semibold mb-2')
                    info_text = """
                    L'extension Biographie Profil permet à l'IA principale de créer et maintenir des bibliothèques biographiques personnalisées pour chaque utilisateur.

                    📖 **Volume 1**: Collection de souvenirs classés chronologiquement et thématiquement (consultation automatique par l'IA)
                    📝 **Volume 2**: Journal biographique narratif avec analyse psychologique approfondie (mis à jour sur demande)

                    **🎯 Phrases magiques IA (consultation):**
                    • "il faut que je consulte la biographie de [prénom]"

                    **👤 Phrases magiques Utilisateur (mise à jour):**
                    • "complète ma biographie"
                    • "complète ma bio"
                    • "met à jour ma biographie"
                    • "enrichis mon profil"

                    **🔄 Injection automatique:**
                    • Détection automatique des prénoms dans la conversation
                    • Injection du Volume 1 lors de la première mention d'un nom
                    • Une seule injection par nom et par conversation
                    • Reset automatique à chaque nouvelle conversation

                    **⚙️ Fonctionnement:**
                    1. L'utilisateur se présente dans la conversation
                    2. L'IA détecte automatiquement le prénom
                    3. Injection automatique de la biographie Volume 1 (première fois)
                    4. Consultation via phrases magiques pour les fois suivantes
                    5. Mise à jour du profil sur demande utilisateur
                    """
                    ui.markdown(info_text).classes('text-sm text-white p-4 rounded').style('background-color: #374151;')
                
                ui.separator()

                # Section Actions
                with ui.column().classes('w-full mb-4'):
                    ui.label('🔧 Actions').classes('text-lg font-semibold mb-3')
                    
                    # Liste des utilisateurs existants
                    users = self.biography_manager.get_existing_users()
                    if users:
                        ui.label(f'📊 Utilisateurs avec biographies: {", ".join(users)}').classes('text-sm text-gray-600 mb-3')
                    else:
                        ui.label('📊 Aucune biographie créée pour le moment').classes('text-sm text-gray-600 mb-3')
                    
                    # Saisie du nom pour traitement biographie
                    with ui.column().classes('w-full mb-4'):
                        ui.label('👤 Créer/Mettre à jour une biographie:').classes('font-medium mb-2')

                        with ui.row().classes('w-full items-end gap-3'):
                            # Champ de saisie pour le nom
                            self.name_input = ui.input(
                                label='Nom de la personne',
                                placeholder='Ex: Yohan, Marie, Pierre...'
                            ).classes('flex-1')

                            # Bouton traitement Volume 1
                            process_btn = ui.button(
                                '🔄 Traiter souvenirs',
                                on_click=self.process_specific_user_memories
                            ).classes('bg-blue-500 text-white px-4 py-2')
                            process_btn.tooltip('Analyse les souvenirs FAISS pour cette personne et crée/met à jour sa biographie Volume 1')

                            # PHASE 1: Génération JSON IA 
                            json_btn = ui.button(
                                '🧠 Phase 1: JSON IA',
                                on_click=self.generate_volume2_json_ia
                            ).classes('bg-blue-600 text-white px-4 py-2 ml-2')
                            json_btn.tooltip('PHASE 1: Génération JSON structuré par GROK - Analyse IA pure des données')

                            # PHASE 2: Transformation JSON → MD IA
                            md_btn = ui.button(
                                '📖 Phase 2: MD IA',
                                on_click=self.generate_volume2_md_ia
                            ).classes('bg-green-600 text-white px-4 py-2 ml-2')
                            md_btn.tooltip('PHASE 2: Transformation JSON → Markdown narratif par GROK')

                
                ui.separator()
                
                # 🆕 BOUTON NETTOYAGE URGENCE
                with ui.row().classes('w-full mt-4'):
                    ui.label('🧹 Outils:').classes('font-semibold')
                    ui.space()
                    
                    clean_btn = ui.button(
                        '🧹 Nettoyer Notifications',
                        on_click=self.emergency_cleanup_notifications
                    ).classes('bg-orange-500 text-white px-3 py-1')
                    clean_btn.tooltip('URGENCE: Nettoie les notifications coincées dans l\'interface')
                
                ui.separator()
                
                # Section accès aux fichiers et sauvegarde
                with ui.row().classes('w-full mt-4'):
                    ui.label('📁 Accès aux données:').classes('font-semibold')
                    ui.space()
                    files_btn = ui.button('Ouvrir dossier biographies', on_click=self.open_data_folder).classes('bg-gray-500 text-white')
                    files_btn.tooltip('Ouvre le dossier data/biographies dans l\'explorateur')

                # Section sauvegarde
                with ui.row().classes('w-full mt-4'):
                    ui.label('💾 Sauvegarde:').classes('font-semibold')
                    ui.space()
                    save_btn = ui.button('💾 Sauvegarder paramètres', on_click=self.manual_save_settings).classes('bg-orange-500 text-white')
                    save_btn.tooltip('Sauvegarde manuellement l\'état ON/OFF de l\'extension pour les prochaines sessions')
                
                # Boutons de fermeture
                with ui.row().classes('w-full justify-end mt-6'):
                    ui.button('Fermer', on_click=lambda: self._close_modal(dialog)).classes('bg-gray-500 text-white px-6 py-2')

                # Gestionnaire de fermeture automatique
                dialog.on('close', self._on_modal_close)
                    
        except Exception as e:
            print(f"[BIOGRAPHY-UI] ❌ Erreur ouverture modal: {e}")

    def _close_modal(self, dialog):
        """Ferme la modal et nettoie les références"""
        try:
            dialog.close()
            self._on_modal_close()
        except Exception as e:
            print(f"[BIOGRAPHY-UI] ❌ Erreur fermeture modal: {e}")

    def _on_modal_close(self):
        """Nettoie les références quand la modal se ferme"""
        self.modal_dialog = None
        self.name_input = None
        self.volume2_instructions = None
        print("[BIOGRAPHY-UI] 🧹 Références modal nettoyées")



    async def process_specific_user_memories(self):
        """Traite les souvenirs pour un utilisateur spécifique saisi dans le champ"""
        try:
            # Récupérer le nom saisi
            user_name = self.name_input.value.strip()

            if not user_name:
                ui.notify('⚠️ Veuillez saisir un nom de personne', type='warning')
                return

            # Notification de démarrage
            ui.notify(f'🔄 Traitement des souvenirs pour {user_name}...', type='info')

            # Traitement pour l'utilisateur spécifique
            success = await self.biography_manager.process_existing_memories_for_user(user_name)

            # Notification de fin
            if success:
                ui.notify(f'✅ Biographie de {user_name} créée/mise à jour avec succès', type='positive')
                print(f"[BIOGRAPHY-UI] ✅ Biographie {user_name} traitée avec succès")

                # Vider le champ après succès
                self.name_input.value = ''
            else:
                ui.notify(f'ℹ️ Aucun souvenir trouvé pour {user_name}', type='info')

        except Exception as e:
            print(f"[BIOGRAPHY-UI] ❌ Erreur traitement souvenirs pour {user_name}: {e}")
            ui.notify(f'❌ Erreur lors du traitement de la biographie de {user_name}', type='negative')

    def manual_save_settings(self):
        """Sauvegarde manuelle des paramètres de l'extension"""
        try:
            success = self._save_extension_state()

            if success:
                state_text = "activée" if self.is_enabled else "désactivée"
                ui.notify(f'💾 Paramètres sauvegardés - Extension {state_text}', type='positive')
                print(f"[BIOGRAPHY-UI] ✅ Sauvegarde manuelle réussie - Extension {state_text}")
            else:
                ui.notify('❌ Erreur lors de la sauvegarde', type='negative')

        except Exception as e:
            print(f"[BIOGRAPHY-UI] ❌ Erreur sauvegarde manuelle: {e}")
            ui.notify('❌ Erreur lors de la sauvegarde des paramètres', type='negative')

    def open_data_folder(self):
        """Ouvre le dossier des biographies dans l'explorateur"""
        try:
            import os
            import subprocess
            import sys
            from pathlib import Path
            
            data_path = Path("data/biographies")
            
            # Créer le dossier s'il n'existe pas
            data_path.mkdir(parents=True, exist_ok=True)
            
            # Convertir en chemin absolu
            abs_path = data_path.resolve()
            
            # Ouvrir dans l'explorateur selon l'OS
            if sys.platform == 'win32':
                # Windows: explorer avec chemin absolu
                os.startfile(str(abs_path))
            elif sys.platform == 'darwin':
                # macOS
                subprocess.Popen(['open', str(abs_path)])
            else:
                # Linux
                subprocess.Popen(['xdg-open', str(abs_path)])
            
            print(f"[BIOGRAPHY-UI] ✅ Dossier ouvert: {abs_path}")
            ui.notify('📁 Dossier biographies ouvert', type='positive')
            
        except Exception as e:
            print(f"[BIOGRAPHY-UI] ❌ Erreur ouverture dossier: {e}")
            import traceback
            traceback.print_exc()
            ui.notify(f'❌ Impossible d\'ouvrir le dossier: {e}', type='negative')

    # =============================
    # 🏗️ NOUVELLE ARCHITECTURE V2.0 - CALLBACKS
    # =============================

    async def generate_volume2_json_ia(self):
        """
        🧠 PHASE 1: Génération JSON structuré par IA
        ============================================
        """
        notification_active = False
        progress_notification = None
        start_time = None

        try:
            # Validation nom utilisateur
            if not self.name_input or not self.name_input.value.strip():
                ui.notify('⚠️ Veuillez saisir un nom d\'utilisateur', type='warning')
                return

            user_name = self.name_input.value.strip()

            # Variable pour stocker la notification actuelle
            import time
            start_time = time.time()

            # Callback de progression
            async def progress_callback(step, total, message, data):
                """Mise à jour de la notification en temps réel"""
                nonlocal progress_notification, start_time

                # Utiliser le temps écoulé fourni par le manager si disponible, sinon calculer
                if 'elapsed' in data:
                    elapsed = data['elapsed']
                else:
                    elapsed = int(time.time() - start_time)

                # Construire le message de progression
                progress_text = f"🧠 Phase 1 JSON IA - Étape {step}/{total}\n"
                progress_text += f"{message}\n"
                progress_text += f"⏱️ Temps écoulé: {elapsed}s / 240s max\n"

                # Ajouter les détails si disponibles
                if 'vol1_size' in data:
                    vol1_kb = data['vol1_size'] // 1024
                    progress_text += f"📖 Volume 1: {vol1_kb} KB\n"
                if 'conv_size' in data:
                    conv_kb = data['conv_size'] // 1024
                    progress_text += f"💬 Conversations: {conv_kb} KB\n"
                if 'sum_size' in data:
                    sum_kb = data['sum_size'] // 1024
                    progress_text += f"📊 Résumés: {sum_kb} KB\n"
                if 'total_size' in data:
                    total_kb = data['total_size'] // 1024
                    progress_text += f"📦 Total données: {total_kb} KB"

                # Fermer l'ancienne notification et créer la nouvelle
                if progress_notification:
                    try:
                        await notification_cleaner.dismiss_notification(progress_notification)
                    except:
                        pass

                progress_notification = notification_cleaner.create_managed_notification(
                    progress_text,
                    type_='ongoing',
                    timeout=300  # 5 minutes max
                )

                print(f"[BIOGRAPHY-UI] 📊 Étape {step}/{total}: {message}")

            notification_active = True
            print(f"[BIOGRAPHY-UI] 🧠 Phase 1 JSON IA demandée pour: {user_name}")

            try:
                # 🔧 APPEL SÉCURISÉ avec timeout global UI et callback de progression
                success = await asyncio.wait_for(
                    self.biography_manager.generate_volume2_json_with_grok(user_name, progress_callback),
                    timeout=240.0  # 240 secondes max au niveau UI (4 minutes)
                )
            except asyncio.TimeoutError:
                print(f"[BIOGRAPHY-UI] ❌ TIMEOUT UI Phase 1 (>240s)")
                success = False
            
            # 🔧 FERMETURE GÉRÉE via le nettoyeur
            if progress_notification:
                await notification_cleaner.dismiss_notification(progress_notification)
            
            # Puis afficher le résultat
            if success:
                ui.notify(f'✅ Phase 1 terminée: JSON structuré généré !', type='positive')
                ui.notify(f'📋 Données structurées prêtes pour Phase 2', type='info')
                print(f"[BIOGRAPHY-UI] ✅ Phase 1 JSON réussie pour {user_name}")
            else:
                ui.notify(f'❌ Échec Phase 1: Génération JSON IA', type='negative')
                print(f"[BIOGRAPHY-UI] ❌ Échec Phase 1 pour {user_name}")
                
        except Exception as e:
            ui.notify(f'❌ Erreur Phase 1: {str(e)[:100]}...', type='negative')
            print(f"[BIOGRAPHY-UI] ❌ Erreur Phase 1: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # 🔧 NETTOYAGE GARANTI MULTI-MÉTHODES
            try:
                # Méthode 1: Nettoyeur professionnel
                await notification_cleaner.force_cleanup_all()
                
                # Méthode 2: Force brute préventive
                for i in range(5):
                    ui.notify('', type='ongoing', timeout=0.01)
                    ui.notify('', type='info', timeout=0.01)
                await asyncio.sleep(0.2)
                
                print(f"[BIOGRAPHY-UI] 🧹 Nettoyage multi-méthodes Phase 1 terminé")
                
            except Exception as cleanup_error:
                print(f"[BIOGRAPHY-UI] ⚠️ Erreur nettoyage final: {cleanup_error}")

    async def generate_volume2_md_ia(self):
        """
        📖 PHASE 2: Transformation JSON → Markdown narratif par IA  
        ==========================================================
        """
        try:
            # Validation nom utilisateur
            if not self.name_input or not self.name_input.value.strip():
                ui.notify('⚠️ Veuillez saisir un nom d\'utilisateur', type='warning')
                return

            user_name = self.name_input.value.strip()

            # Variable pour stocker la notification actuelle
            import time
            start_time = time.time()
            progress_notification_p2 = None

            # Callback de progression Phase 2
            async def progress_callback_p2(step, total, message, data):
                """Mise à jour de la notification Phase 2 en temps réel"""
                nonlocal progress_notification_p2, start_time

                # Utiliser le temps écoulé fourni par le manager si disponible, sinon calculer
                if 'elapsed' in data:
                    elapsed = data['elapsed']
                else:
                    elapsed = int(time.time() - start_time)

                # Construire le message de progression
                progress_text = f"📖 Phase 2 JSON→MD - Étape {step}/{total}\n"
                progress_text += f"{message}\n"
                progress_text += f"⏱️ Temps écoulé: {elapsed}s / 240s max\n"

                # Ajouter les détails si disponibles
                if 'json_size' in data:
                    json_kb = data['json_size'] // 1024
                    progress_text += f"📊 JSON source: {json_kb} KB"

                # Fermer l'ancienne notification et créer la nouvelle
                if progress_notification_p2:
                    try:
                        await notification_cleaner.dismiss_notification(progress_notification_p2)
                    except:
                        pass

                progress_notification_p2 = notification_cleaner.create_managed_notification(
                    progress_text,
                    type_='ongoing',
                    timeout=300  # 5 minutes max
                )

                print(f"[BIOGRAPHY-UI] 📖 Phase 2 - Étape {step}/{total}: {message} ({elapsed}s)")

            print(f"[BIOGRAPHY-UI] 📖 Phase 2 MD IA demandée pour: {user_name}")

            # Appeler Phase 2 avec timeout de 240s et callback de progression
            try:
                markdown_content = await asyncio.wait_for(
                    self.biography_manager.generate_volume2_md_with_grok(user_name, progress_callback_p2),
                    timeout=240.0  # 240 secondes max (4 minutes)
                )
            except asyncio.TimeoutError:
                print(f"[BIOGRAPHY-UI] ❌ TIMEOUT UI Phase 2 (>240s)")
                markdown_content = None
            
            # 🔧 FERMETURE GÉRÉE Phase 2
            await notification_cleaner.dismiss_notification(progress_notification_p2)
            
            if markdown_content and len(markdown_content) > 100:
                ui.notify(f'✅ Phase 2 terminée: Journal narratif généré !', type='positive')
                ui.notify(f'📖 {len(markdown_content):,} caractères - Journal développé', type='info')
                print(f"[BIOGRAPHY-UI] ✅ Phase 2 MD réussie: {len(markdown_content):,} chars")
                
                # Afficher chemin fichier
                structured_manager = self.biography_manager.get_structured_manager(user_name)
                journal_path = structured_manager.user_dir / "volume2_journal.md"
                ui.notify(f'📁 Journal: {journal_path}', type='info')
                
            else:
                ui.notify(f'❌ Échec Phase 2: Transformation MD', type='negative')
                if not markdown_content:
                    ui.notify(f'💡 Vérifiez que la Phase 1 (JSON) a été exécutée', type='info')
                print(f"[BIOGRAPHY-UI] ❌ Échec Phase 2 pour {user_name}")
                
        except Exception as e:
            ui.notify(f'❌ Erreur Phase 2: {str(e)[:100]}...', type='negative')
            print(f"[BIOGRAPHY-UI] ❌ Erreur Phase 2: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # 🔧 NETTOYAGE GARANTI MULTI-MÉTHODES Phase 2
            try:
                # Méthode 1: Nettoyeur professionnel
                await notification_cleaner.force_cleanup_all()
                
                # Méthode 2: Force brute préventive
                for i in range(5):
                    ui.notify('', type='ongoing', timeout=0.01)
                    ui.notify('', type='info', timeout=0.01)
                await asyncio.sleep(0.2)
                
                print(f"[BIOGRAPHY-UI] 🧹 Nettoyage multi-méthodes Phase 2 terminé")
                
            except Exception as cleanup_error:
                print(f"[BIOGRAPHY-UI] ⚠️ Erreur nettoyage final Phase 2: {cleanup_error}")

    async def emergency_cleanup_notifications(self):
        """
        🚨 NETTOYAGE D'URGENCE: Notifications coincées
        ============================================
        
        Méthode d'urgence pour nettoyer les notifications qui restent visibles
        malgré la fin des processus. Utilise une approche force brute.
        """
        try:
            print(f"[BIOGRAPHY-UI] 🚨 NETTOYAGE D'URGENCE FORCE BRUTE demandé")
            
            # 🔥 MÉTHODE FORCE BRUTE: Bombardement de notifications vides
            ui.notify('🧹 Nettoyage force brute en cours...', type='warning', timeout=2)
            
            # Bombardement de notifications vides (multiple types)
            for i in range(15):
                for type_ in ['ongoing', 'info', 'positive', 'negative', 'warning']:
                    ui.notify('', type=type_, timeout=0.01)
                await asyncio.sleep(0.03)
            
            # Nettoyage via le système professionnel également
            await notification_cleaner.emergency_reset()
            
            # Attente stabilisation
            await asyncio.sleep(0.5)
            
            # Confirmation finale
            ui.notify('✅ FORCE BRUTE: Notifications fantômes éliminées', type='positive', timeout=4)
            print(f"[BIOGRAPHY-UI] ✅ Nettoyage FORCE BRUTE terminé")
            
        except Exception as e:
            ui.notify(f'❌ Erreur nettoyage: {str(e)[:50]}', type='negative')
            print(f"[BIOGRAPHY-UI] ❌ Erreur nettoyage d'urgence: {e}")