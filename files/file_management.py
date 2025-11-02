"""
Module: file_management.py
Description: Gestion fichiers (upload, affichage tabs, icônes)
Extrait de: ogma_ng.py (lignes 1130-1250)
Date: 2025-11-02
Note: Fonctions get_file_icon et truncate_filename déjà dans utils/formatting_utils.py
      Ce module ne contient que les fonctions UI restantes
"""

import uuid
import asyncio
from pathlib import Path
from nicegui import ui


async def process_uploaded_file(upload_event, data_dir, active_file_data_ref):
    """
    Traite un fichier uploadé et l'active dans la conversation.
    
    Args:
        upload_event: Event NiceGUI upload
        data_dir: Path vers data/
        active_file_data_ref: Référence mutable dict pour stocker données fichier actif
        
    Returns:
        bool: Succès du traitement
    """
    try:
        # Importer le processeur de fichier
        from extensions.file_processor import process_file
        
        # Créer un chemin temporaire
        temp_path = Path(data_dir) / "uploads" / f"temp_{uuid.uuid4()}_{upload_event.name}"
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Sauvegarder le fichier temporaire
        with open(temp_path, 'wb') as f:
            f.write(upload_event.content.read())
        
        # Traiter le fichier
        file_data = process_file(temp_path)
        
        if file_data:
            # Mettre à jour la référence (dict mutable)
            active_file_data_ref['data'] = file_data
            print(f'[SUCCESS] Fichier "{upload_event.name}" ajouté à la conversation')
            return True
        else:
            print('[ERROR] Erreur lors du traitement du fichier')
            return False
            
    except Exception as e:
        print(f"[ERROR] Erreur upload fichier: {e}")
        return False


def update_header_display(header_container):
    """
    Met à jour l'affichage du header (sans les fichiers actifs).
    
    Args:
        header_container: Container NiceGUI pour header
    """
    if header_container is None:
        return
    
    try:
        header_container.clear()
        
        with header_container:
            # Le header n'affiche plus les fichiers actifs
            # Ils sont maintenant affichés sous la boîte de messagerie
            pass
    except Exception as e:
        print(f"[ERROR] Erreur update header: {e}")
        # Fallback silencieux si le client n'est plus disponible


def update_file_tab_display(file_tab_container, active_file_data, get_file_icon_func, truncate_filename_func, remove_callback):
    """
    Met à jour l'affichage de l'onglet fichier sous la boîte de messagerie.
    
    Args:
        file_tab_container: Container NiceGUI pour onglet fichier
        active_file_data: Dict données fichier actif ou None
        get_file_icon_func: Fonction pour obtenir icône fichier
        truncate_filename_func: Fonction pour tronquer nom fichier
        remove_callback: Fonction callback pour supprimer fichier
    """
    if file_tab_container is None:
        return
    
    try:
        file_tab_container.clear()
        
        with file_tab_container:
            if active_file_data:
                # Affichage de l'onglet fichier sous la messagerie
                filename = active_file_data.get('filename', 'Fichier inconnu')
                icon = get_file_icon_func(filename)
                truncated = truncate_filename_func(filename)
                
                with ui.element('div').classes('file-tab-container file-tab-bottom'):
                    with ui.element('div').classes('file-tab'):
                        ui.label(f"{icon} {truncated}").classes('file-tab-label')
                        ui.button('✕', on_click=remove_callback).classes('file-tab-close')
    except Exception as e:
        print(f"[ERROR] Erreur update file tab: {e}")


def remove_active_file(active_file_data_ref, update_display_func):
    """
    Supprime le fichier actif et met à jour l'affichage.
    
    Args:
        active_file_data_ref: Référence mutable dict pour données fichier actif
        update_display_func: Fonction pour mettre à jour affichage
    """
    active_file_data_ref['data'] = None
    update_display_func()  # Met à jour l'onglet sous la messagerie
    try:
        ui.notify('Fichier supprimé de la conversation', type='info')
    except:
        print('[INFO] Fichier supprimé de la conversation')


def show_file_upload_dialog(process_callback):
    """
    Affiche la popup d'upload de fichier.
    
    Args:
        process_callback: Fonction async callback pour traiter fichier uploadé
    """
    with ui.dialog().classes('popup-overlay') as dialog:
        with ui.card().classes('popup-content'):
            ui.html('<div class="popup-title">📎 Ajouter un fichier</div>')
            
            ui.label('Formats supportés: PDF, DOCX, TXT, MD, JSON, Images (JPG, PNG, WebP, GIF)').classes('text-sm text-gray-400 mb-4')
            
            # Zone d'upload
            with ui.element().style('border: 2px dashed #4a4a4a; border-radius: 8px; padding: 40px; text-align: center; margin: 20px 0;'):
                ui.label('Glissez-déposez votre fichier ici ou cliquez pour sélectionner').classes('text-gray-400')
                upload_area = ui.upload(
                    on_upload=lambda e: _handle_upload_and_close(e, dialog, process_callback),
                    multiple=False,
                    max_file_size=10*1024*1024  # 10MB max
                ).classes('mt-4')
            
            with ui.row().classes('justify-end gap-2 mt-4'):
                ui.button('Annuler', on_click=dialog.close).classes('action-button')
    
    dialog.open()


def _handle_upload_and_close(upload_event, dialog, process_callback):
    """Traite l'upload et ferme le dialog (helper interne)."""
    asyncio.create_task(_process_and_close(upload_event, dialog, process_callback))


async def _process_and_close(upload_event, dialog, process_callback):
    """Traite l'upload de façon asynchrone et ferme le dialog (helper interne)."""
    await process_callback(upload_event)
    dialog.close()
