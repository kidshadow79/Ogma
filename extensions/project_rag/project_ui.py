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
    from utils.i18n import t
except Exception:
    def t(key, **kwargs):
        return key

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
        self._th = {}  # Palette thème courante (définie dans show_overlay)

    def _get_theme(self) -> dict:
        """Retourne la palette de couleurs selon le thème OGMA actif (neon/classic/light)."""
        try:
            ogma_ng = sys.modules.get('ogma_ng')
            sm = ogma_ng._ensure_settings_manager() if ogma_ng else None
            theme_name = sm.settings.get('ui', {}).get('theme', 'neon') if sm else 'neon'
        except Exception:
            theme_name = 'neon'

        if theme_name == 'light':
            return {
                'q_dark':        '',
                'bg_card':       '#fdfaf5',
                'bg_item':       '#f0ece3',
                'border_left':   '2px solid rgba(160, 124, 10, 0.28)',
                'shadow':        '-4px 0 16px rgba(0, 0, 0, 0.10)',
                'text':          '#1a1410',
                'text2':         '#5a5048',
                'muted':         '#8a7e74',
                'accent':        '#1565c0',
                'sep':           'rgba(0, 0, 0, 0.12)',
                'exp_bg':        '#f0ece3',
                'exp_border':    '1px solid rgba(0, 0, 0, 0.12)',
                'upload_border': 'rgba(21, 101, 192, 0.28)',
                'upload_bg':     'rgba(21, 101, 192, 0.04)',
                'item_bg':       '#ffffff',
                'item_border':   '#e8e2d8',
                'del_icon':      '#b91c1c',
            }
        # neon + classic → thème sombre
        return {
            'q_dark':        'q-dark',
            'bg_card':       '#1e2433',
            'bg_item':       '#252d3d',
            'border_left':   '2px solid #3b82f6',
            'shadow':        '-4px 0 24px rgba(0, 0, 0, 0.5)',
            'text':          '#e5e7eb',
            'text2':         '#9ca3af',
            'muted':         '#6b7280',
            'accent':        '#3b82f6',
            'sep':           'rgba(59, 130, 246, 0.2)',
            'exp_bg':        '#252d3d',
            'exp_border':    '1px solid #3b82f6',
            'upload_border': 'rgba(59, 130, 246, 0.3)',
            'upload_bg':     'rgba(59, 130, 246, 0.03)',
            'item_bg':       '#252d3d',
            'item_border':   '#2d3b55',
            'del_icon':      '#ef4444',
        }

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

        self._th = self._get_theme()
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

        th = self._th
        with dialog:
            with ui.card().classes(th['q_dark']).style(f'''
                background: {th['bg_card']} !important;
                border: none !important;
                border-left: {th['border_left']} !important;
                border-radius: 0 !important;
                box-shadow: {th['shadow']} !important;
                width: 480px !important;
                min-height: 100vh !important;
                overflow-y: auto !important;
                padding: 24px !important;
                color: {th['text']} !important;
            '''):
                # Header
                with ui.row().classes('w-full items-center justify-between mb-4'):
                    with ui.row().classes('items-center gap-3'):
                        ui.icon('folder_open', size='28px').style(f'color: {th["accent"]};')
                        ui.label(t('pr_label_title')).style(f'''
                            font-size: 1.4rem; font-weight: 600;
                            color: {th['accent']} !important;
                        ''')

                    with ui.row().classes('items-center gap-2'):
                        # Toggle ON/OFF
                        self._toggle_switch = ui.switch(
                            t('pr_switch_active'),
                            value=self.config.active,
                            on_change=self._on_toggle
                        ).style(f'color: {th["text"]};')

                        # Bouton fermer
                        ui.button(icon='close', on_click=self._close_overlay).props(
                            'flat round'
                        ).style(f'color: {th["text2"]};')

                ui.separator().style(f'background: {th["sep"]};')

                # Stats
                stats = self.memory.get_stats()
                self._stats_label = ui.label(
                    t('pr_label_stats', files=stats['files'], chunks=stats['chunks'])
                ).classes('text-sm mb-3').style(f'color: {th["text2"]};')

                # === Zone instruction projet ===
                with ui.expansion(t('pr_expansion_instructions'), icon='edit_note', value=bool(self.config.instruction)).classes('w-full mb-4').style(f'''
                    background: {th['exp_bg']} !important;
                    border: {th['exp_border']} !important;
                    border-radius: 8px !important;
                '''):
                    ui.label(
                        t('pr_label_instructions_help')
                    ).classes('text-xs mb-2').style(f'color: {th["muted"]};')

                    instruction_area = ui.textarea(
                        value=self.config.instruction,
                        placeholder=t('pr_placeholder_instructions'),
                    ).classes('w-full').style('min-height: 120px; font-size: 13px;')

                    def _save_instruction():
                        self.config.instruction = instruction_area.value or ''
                        ui.notify(t('pr_notify_instr_saved'), type='positive')

                    ui.button(t('pr_btn_save_instr'), icon='save',
                              on_click=_save_instruction).classes('mt-2').style(f'''
                        background: {th['accent']} !important;
                        border: 1px solid {th['accent']} !important;
                        color: #ffffff !important;
                    ''')

                # === Zone upload fichiers ===
                ui.label(t('pr_label_documents')).classes('text-sm font-bold mb-2').style(
                    f'color: {th["accent"]};'
                )

                # Upload zone
                upload = ui.upload(
                    label=t('pr_upload_label'),
                    multiple=True,
                    auto_upload=True,
                    on_upload=self._on_file_upload,
                ).classes('w-full mb-3').style(f'''
                    border: 2px dashed {th['upload_border']} !important;
                    border-radius: 12px !important;
                    background: {th['upload_bg']} !important;
                    min-height: 80px !important;
                ''')
                # Extensions acceptées
                upload.props('accept=".txt,.md,.py,.js,.ts,.pdf,.docx,.json,.yaml,.yml,.html,.css,.sql,.csv,.log,.xml,.c,.cpp,.h,.java,.cs,.go,.rs,.rb,.php,.sh,.bash,.ps1,.toml,.ini,.cfg,.conf,.tsx,.jsx"')

                # Liste des fichiers indexés
                self._file_list_container = ui.column().classes('w-full gap-1')
                self._refresh_file_list()

                ui.separator().classes('my-3').style(f'background: {th["sep"]};')

                # Boutons bas
                with ui.row().classes('w-full justify-between items-center'):
                    ui.button(t('pr_btn_clear'), icon='delete_sweep',
                              on_click=self._confirm_clear_all).style(f'''
                        background: rgba(185, 28, 28, 0.10) !important;
                        border: 1px solid rgba(185, 28, 28, 0.25) !important;
                        color: {th['del_icon']} !important;
                    ''')

                    with ui.row().classes('gap-2'):
                        # Stats cache
                        cache_stats = self.retriever.get_stats()
                        ui.label(t('pr_label_cache', rate=cache_stats.get('cache_hit_rate', '0%'))).classes(
                            'text-xs'
                        ).style(f'color: {th["muted"]};')

                        ui.button(t('pr_btn_close'), on_click=self._close_overlay).style(f'''
                            background: {th['bg_item']} !important;
                            border: 1px solid {th['item_border']} !important;
                            color: {th['text']} !important;
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
        status = t('pr_status_enabled') if e.value else t('pr_status_disabled')
        ui.notify(t('pr_notify_project_status', name=self.config.name, status=status), type='positive' if e.value else 'info')
        print(f"[PROJECT-UI] Projet {status}")

    async def _on_file_upload(self, e: events.UploadEventArguments):
        """Traite un fichier uploadé : extraction texte → chunking → vectorisation."""
        try:
            filename = e.name
            file_ext = Path(filename).suffix.lower()
            file_id = str(uuid.uuid4())[:12]

            ui.notify(t('pr_notify_indexing', filename=filename), type='info')
            print(f"[PROJECT-UI] Upload: {filename} ({file_ext})")

            # Sauver le fichier dans le dossier projet
            dest_path = self.config.files_dir / f"{file_id}_{filename}"
            content_bytes = e.content.read()
            dest_path.write_bytes(content_bytes)

            # Extraire le texte via file_processor
            text_content = self._extract_text(dest_path, file_ext)
            if not text_content or not text_content.strip():
                ui.notify(t('pr_notify_no_text', filename=filename), type='warning')
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
                ui.notify(t('pr_notify_no_chunks', filename=filename), type='warning')
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

            ui.notify(t('pr_notify_indexed', filename=filename, added=added), type='positive')
            self._refresh_file_list()
            self._update_stats()

        except Exception as ex:
            print(f"[PROJECT-UI] Erreur upload: {ex}")
            import traceback
            traceback.print_exc()
            ui.notify(t('pr_notify_error', ex=ex), type='negative')

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
                ui.label(t('pr_label_no_files')).classes('text-sm').style(
                    'color: #6b7280; font-style: italic;'
                )
            else:
                for f in files:
                    self._render_file_card(f)

    def _render_file_card(self, file_data: dict):
        """Affiche une carte pour un fichier indexé."""
        th = self._th
        with ui.row().classes('w-full items-center justify-between py-1 px-2').style(f'''
            background: {th['item_bg']};
            border: 1px solid {th['item_border']};
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
                ui.icon(icon, size='18px').style(f'color: {th["accent"]};')

                with ui.column().classes('gap-0'):
                    ui.label(file_data['filename']).classes('text-sm').style(
                        f'color: {th["text"]}; line-height: 1.2;'
                    )
                    size_kb = (file_data.get('file_size', 0) or 0) / 1024
                    ui.label(
                        t('pr_label_file_meta', chunks=file_data.get('chunk_count', 0), size=size_kb)
                    ).classes('text-xs').style(f'color: {th["muted"]}; line-height: 1.2;')

            # Bouton supprimer
            file_id = file_data['id']
            ui.button(
                icon='delete',
                on_click=lambda fid=file_id: self._remove_file(fid)
            ).props('flat round size=sm').style(f'color: {th["del_icon"]};')

    async def _remove_file(self, file_id: str):
        """Supprime un fichier et ses chunks."""
        try:
            self.memory.remove_file(file_id)
            self.config.remove_file_record(file_id)
            self.retriever.clear_cache()
            ui.notify(t('pr_notify_file_removed'), type='info')
            self._refresh_file_list()
            self._update_stats()
        except Exception as e:
            ui.notify(t('pr_notify_remove_err', err=str(e)), type='negative')

    def _confirm_clear_all(self):
        """Confirmation avant de vider tout le projet."""
        th = self._th
        with ui.dialog() as confirm_dialog:
            with ui.card().classes(th['q_dark']).style(
                f'background: {th["bg_card"]}; color: {th["text"]}; padding: 20px; border: 1px solid {th["item_border"]};'
            ):
                ui.label(t('pr_dialog_clear_title')).classes('text-lg font-bold mb-2')
                ui.label(t('pr_dialog_clear_help')).classes('text-sm mb-4').style(f'color: {th["text2"]};')
                with ui.row().classes('justify-end gap-2'):
                    ui.button(t('common_cancel'), on_click=confirm_dialog.close).style(
                        f'color: {th["text"]};'
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
                        ui.notify(t('pr_notify_cleared'), type='info')
                        self._refresh_file_list()
                        self._update_stats()

                    ui.button(t('pr_btn_confirm'), on_click=_do_clear).style(f'''
                        background: rgba(185, 28, 28, 0.12) !important;
                        border: 1px solid rgba(185, 28, 28, 0.30) !important;
                        color: {th['del_icon']} !important;
                    ''')
        confirm_dialog.open()

    def _update_stats(self):
        """Met à jour le label de statistiques."""
        if self._stats_label:
            stats = self.memory.get_stats()
            self._stats_label.set_text(
                f"{stats['files']} fichiers | {stats['chunks']} chunks"
            )
