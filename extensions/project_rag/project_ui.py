"""
project_ui.py
-------------
Interface utilisateur NiceGUI pour l'extension Project RAG.
Overlay glassmorphism avec drag & drop fichiers, instructions projet, toggle ON/OFF.
"""

import sys
import uuid
import shutil
import asyncio
from pathlib import Path
from typing import Optional, Callable

try:
    from nicegui import ui, events
    NICEGUI_AVAILABLE = True
except ImportError:
    NICEGUI_AVAILABLE = False


def _get_ogma_ng_function(func_name):
    """Helper pour récupérer une fonction d'ogma_ng."""
    try:
        ogma_ng = sys.modules.get('ogma_ng')
        if ogma_ng and hasattr(ogma_ng, func_name):
            return getattr(ogma_ng, func_name)
    except Exception:
        pass
    return None


class ProjectUI:
    """Interface utilisateur pour l'extension Project RAG."""

    def __init__(self, config, memory, retriever, injector, embedder):
        """
        Args:
            config: ProjectConfig instance
            memory: ProjectMemory instance
            retriever: ProjectRetriever instance
            injector: ProjectInjector instance
            embedder: Embedding controller (pour vectoriser les chunks)
        """
        self.config = config
        self.memory = memory
        self.retriever = retriever
        self.injector = injector
        self.embedder = embedder

        # Références UI pour rafraîchissement
        self._file_list_container = None
        self._stats_label = None
        self._toggle_switch = None
        self._overlay = None

    def show_overlay(self):
        """Affiche le panneau latéral projet (dialog Quasar positionné à droite)."""
        if not NICEGUI_AVAILABLE:
            print("[PROJECT-UI] NiceGUI non disponible")
            return

        # Fermer et détruire l'ancienne instance si elle existe
        if self._overlay is not None:
            try:
                self._overlay.close()
                self._overlay.delete()
            except Exception:
                pass
            self._overlay = None
            self._file_list_container = None
            self._stats_label = None
            self._toggle_switch = None

        self._create_overlay()

    def _create_overlay(self):
        """
        Crée le panneau latéral droit en utilisant ui.dialog() avec
        position Quasar 'right'. Le dialog se téléporte toujours au
        niveau du <body>, indépendamment du contexte d'appel.
        """
        # ui.dialog() est toujours rendu au niveau document (pas dans la sidebar)
        dialog = ui.dialog().props('position="right" full-height persistent')
        dialog.style('''
            --q-dialog-width: 480px;
        ''')
        self._overlay = dialog
        dialog.open()

        with dialog:
            with ui.card().classes('q-dark').style('''
                background: #1e2433 !important;
                border: none !important;
                border-left: 2px solid #3b82f6 !important;
                border-radius: 0 !important;
                box-shadow: -4px 0 24px rgba(0, 0, 0, 0.5) !important;
                width: 480px !important;
                min-height: 100vh !important;
                overflow-y: auto !important;
                padding: 24px !important;
                color: #e5e7eb !important;
            '''):
                # Header
                with ui.row().classes('w-full items-center justify-between mb-4'):
                    with ui.row().classes('items-center gap-3'):
                        ui.icon('folder_open', size='28px').style('color: #3b82f6;')
                        ui.label('Projet RAG').style('''
                            font-size: 1.4rem; font-weight: 600;
                            color: #3b82f6 !important;
                            text-shadow: 0 0 10px rgba(59, 130, 246, 0.3);
                        ''')

                    with ui.row().classes('items-center gap-2'):
                        # Toggle ON/OFF
                        self._toggle_switch = ui.switch(
                            'Actif',
                            value=self.config.active,
                            on_change=self._on_toggle
                        ).style('color: #e5e7eb;')

                        # Bouton fermer
                        ui.button(icon='close', on_click=self._close_overlay).props(
                            'flat round'
                        ).style('color: #e5e7eb;')

                ui.separator().style('background: rgba(59, 130, 246, 0.2);')

                # Stats
                stats = self.memory.get_stats()
                self._stats_label = ui.label(
                    f"{stats['files']} fichiers | {stats['chunks']} chunks"
                ).classes('text-sm mb-3').style('color: #9ca3af;')

                # === Zone instruction projet ===
                with ui.expansion('Instructions projet', icon='edit_note', value=bool(self.config.instruction)).classes('w-full mb-4').style('''
                    background: #252d3d !important;
                    border: 1px solid #3b82f6 !important;
                    border-radius: 8px !important;
                '''):
                    ui.label(
                        'Ces instructions remplacent le contexte permanent quand le projet est actif.'
                    ).classes('text-xs mb-2').style('color: #9ca3af;')

                    instruction_area = ui.textarea(
                        value=self.config.instruction,
                        placeholder='Instructions spécifiques au projet...\nEx: "Tu es un expert en architecture logicielle. Réponds en te basant sur les documents du projet."',
                    ).classes('w-full').style('min-height: 120px; font-size: 13px;')

                    def _save_instruction():
                        self.config.instruction = instruction_area.value or ''
                        ui.notify('Instruction projet sauvegardée', type='positive')

                    ui.button('Sauvegarder instruction', icon='save',
                              on_click=_save_instruction).classes('mt-2').style('''
                        background: #2563eb !important;
                        border: 1px solid #3b82f6 !important;
                        color: #ffffff !important;
                    ''')

                # === Zone upload fichiers ===
                ui.label('Documents du projet').classes('text-sm font-bold mb-2').style(
                    'color: #3b82f6;'
                )

                # Upload zone
                upload = ui.upload(
                    label='Glissez des fichiers ici ou cliquez pour parcourir',
                    multiple=True,
                    auto_upload=True,
                    on_upload=self._on_file_upload,
                ).classes('w-full mb-3').style('''
                    border: 2px dashed rgba(59, 130, 246, 0.3) !important;
                    border-radius: 12px !important;
                    background: rgba(59, 130, 246, 0.03) !important;
                    min-height: 80px !important;
                ''')
                # Extensions acceptées
                upload.props('accept=".txt,.md,.py,.js,.ts,.pdf,.docx,.json,.yaml,.yml,.html,.css,.sql,.csv,.log,.xml,.c,.cpp,.h,.java,.cs,.go,.rs,.rb,.php,.sh,.bash,.ps1,.toml,.ini,.cfg,.conf,.tsx,.jsx"')

                # Liste des fichiers indexés
                self._file_list_container = ui.column().classes('w-full gap-1')
                self._refresh_file_list()

                ui.separator().classes('my-3').style('background: rgba(59, 130, 246, 0.15);')

                # Boutons bas
                with ui.row().classes('w-full justify-between items-center'):
                    ui.button('Vider le projet', icon='delete_sweep',
                              on_click=self._confirm_clear_all).style('''
                        background: rgba(239, 68, 68, 0.15) !important;
                        border: 1px solid rgba(239, 68, 68, 0.3) !important;
                        color: #ef4444 !important;
                    ''')

                    with ui.row().classes('gap-2'):
                        # Stats cache
                        cache_stats = self.retriever.get_stats()
                        ui.label(f"Cache: {cache_stats.get('cache_hit_rate', '0%')}").classes(
                            'text-xs'
                        ).style('color: #6b7280;')

                        ui.button('Fermer', on_click=self._close_overlay).style('''
                            background: #374151 !important;
                            border: 1px solid #4b5563 !important;
                            color: #e5e7eb !important;
                        ''')

    def _close_overlay(self):
        """Ferme et supprime le panneau latéral (dialog)."""
        if self._overlay:
            try:
                self._overlay.close()
                self._overlay.delete()
            except Exception:
                pass
            self._overlay = None
            self._file_list_container = None
            self._stats_label = None
            self._toggle_switch = None

    def _on_toggle(self, e):
        """Active/désactive le projet."""
        self.config.active = e.value
        status = "activé" if e.value else "désactivé"
        ui.notify(f'Projet {self.config.name} {status}', type='positive' if e.value else 'info')
        print(f"[PROJECT-UI] Projet {status}")

    async def _on_file_upload(self, e: events.UploadEventArguments):
        """Traite un fichier uploadé : extraction texte → chunking → vectorisation."""
        try:
            filename = e.name
            file_ext = Path(filename).suffix.lower()
            file_id = str(uuid.uuid4())[:12]

            ui.notify(f'Indexation de {filename}...', type='info')
            print(f"[PROJECT-UI] Upload: {filename} ({file_ext})")

            # Sauver le fichier dans le dossier projet
            dest_path = self.config.files_dir / f"{file_id}_{filename}"
            content_bytes = e.content.read()
            dest_path.write_bytes(content_bytes)

            # Extraire le texte via file_processor
            text_content = self._extract_text(dest_path, file_ext)
            if not text_content or not text_content.strip():
                ui.notify(f'{filename}: aucun texte extractible', type='warning')
                dest_path.unlink(missing_ok=True)
                return

            # Chunking adaptatif
            from .project_chunker import chunk_file
            settings = self.config.settings
            chunks = chunk_file(
                text_content,
                file_ext,
                small_size=settings.get('chunk_size_small', 200),
                parent_size=settings.get('chunk_size_parent', 800),
                overlap=settings.get('chunk_overlap', 50),
            )

            if not chunks:
                ui.notify(f'{filename}: chunking a produit 0 chunks', type='warning')
                return

            # Vectorisation des petits chunks
            embeddings = []
            for chunk in chunks:
                try:
                    emb = await self.embedder.create_embedding(chunk['text_small'])
                    if emb:
                        embeddings.append(emb)
                    else:
                        embeddings.append([0.0] * self.memory.embedding_dim)
                except Exception as emb_err:
                    print(f"[PROJECT-UI] Erreur embedding chunk: {emb_err}")
                    embeddings.append([0.0] * self.memory.embedding_dim)

            # Enregistrer le fichier
            self.memory.add_file(
                file_id, filename, file_ext,
                len(content_bytes)
            )

            # Ajouter les chunks
            added = self.memory.add_chunks(file_id, chunks, embeddings)

            # Enregistrer dans la config
            self.config.add_file_record(
                file_id, filename, file_ext,
                len(content_bytes), added
            )

            # Vider le cache retriever (nouveaux chunks disponibles)
            self.retriever.clear_cache()

            ui.notify(f'{filename}: {added} chunks indexés', type='positive')
            self._refresh_file_list()
            self._update_stats()

        except Exception as ex:
            print(f"[PROJECT-UI] Erreur upload: {ex}")
            import traceback
            traceback.print_exc()
            ui.notify(f'Erreur: {ex}', type='negative')

    def _extract_text(self, file_path: Path, extension: str) -> str:
        """Extrait le texte d'un fichier via file_processor d'OGMA."""
        try:
            from extensions.file_processor import process_file
            result = process_file(file_path)
            if result and result.get('type') == 'text':
                return result.get('content', '')
            return ''
        except Exception as e:
            print(f"[PROJECT-UI] Erreur extraction: {e}")
            # Fallback : lecture brute pour fichiers texte
            try:
                return file_path.read_text(encoding='utf-8')
            except Exception:
                return ''

    def _refresh_file_list(self):
        """Rafraîchit la liste des fichiers affichés."""
        if self._file_list_container is None:
            return

        self._file_list_container.clear()
        files = self.memory.get_all_files()

        with self._file_list_container:
            if not files:
                ui.label('Aucun fichier indexé').classes('text-sm').style(
                    'color: #6b7280; font-style: italic;'
                )
            else:
                for f in files:
                    self._render_file_card(f)

    def _render_file_card(self, file_data: dict):
        """Affiche une carte pour un fichier indexé."""
        with ui.row().classes('w-full items-center justify-between py-1 px-2').style('''
            background: #252d3d;
            border: 1px solid #2d3b55;
            border-radius: 6px;
        '''):
            with ui.row().classes('items-center gap-2'):
                # Icône selon type
                icon_map = {
                    '.py': 'code', '.js': 'code', '.ts': 'code',
                    '.md': 'description', '.txt': 'article',
                    '.pdf': 'picture_as_pdf', '.docx': 'description',
                    '.json': 'data_object', '.html': 'web',
                }
                icon = icon_map.get(file_data.get('file_type', ''), 'insert_drive_file')
                ui.icon(icon, size='18px').style('color: #3b82f6;')

                with ui.column().classes('gap-0'):
                    ui.label(file_data['filename']).classes('text-sm').style(
                        'color: #e5e7eb; line-height: 1.2;'
                    )
                    size_kb = (file_data.get('file_size', 0) or 0) / 1024
                    ui.label(
                        f"{file_data.get('chunk_count', 0)} chunks | {size_kb:.1f} KB"
                    ).classes('text-xs').style('color: #6b7280; line-height: 1.2;')

            # Bouton supprimer
            file_id = file_data['id']
            ui.button(
                icon='delete',
                on_click=lambda fid=file_id: self._remove_file(fid)
            ).props('flat round size=sm').style('color: #ef4444;')

    async def _remove_file(self, file_id: str):
        """Supprime un fichier et ses chunks."""
        try:
            self.memory.remove_file(file_id)
            self.config.remove_file_record(file_id)
            self.retriever.clear_cache()
            ui.notify('Fichier et chunks supprimés', type='info')
            self._refresh_file_list()
            self._update_stats()
        except Exception as e:
            ui.notify(f'Erreur suppression: {e}', type='negative')

    def _confirm_clear_all(self):
        """Confirmation avant de vider tout le projet."""
        with ui.dialog() as confirm_dialog:
            with ui.card().classes('q-dark').style(
                'background: #1e2433; color: #e5e7eb; padding: 20px;'
            ):
                ui.label('Vider le projet ?').classes('text-lg font-bold mb-2')
                ui.label('Tous les fichiers et chunks seront supprimés. Cette action est irréversible.').classes('text-sm mb-4').style('color: #9ca3af;')
                with ui.row().classes('justify-end gap-2'):
                    ui.button('Annuler', on_click=confirm_dialog.close).style(
                        'color: #e5e7eb;'
                    )

                    async def _do_clear():
                        self.memory.clear_all()
                        # Vider les fichiers dans la config
                        self.config._config['files'] = []
                        self.config._save()
                        # Supprimer les fichiers physiques
                        for f in self.config.files_dir.iterdir():
                            try:
                                f.unlink()
                            except Exception:
                                pass
                        self.retriever.clear_cache()
                        confirm_dialog.close()
                        ui.notify('Projet vidé', type='info')
                        self._refresh_file_list()
                        self._update_stats()

                    ui.button('Confirmer', on_click=_do_clear).style('''
                        background: rgba(239, 68, 68, 0.2) !important;
                        border: 1px solid rgba(239, 68, 68, 0.4) !important;
                        color: #ef4444 !important;
                    ''')
        confirm_dialog.open()

    def _update_stats(self):
        """Met à jour le label de statistiques."""
        if self._stats_label:
            stats = self.memory.get_stats()
            self._stats_label.set_text(
                f"{stats['files']} fichiers | {stats['chunks']} chunks"
            )
