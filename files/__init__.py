"""
Package: files
Description: Gestion fichiers (upload, affichage, tabs)
Date: 2025-11-02
"""

from .file_management import (
    process_uploaded_file,
    update_header_display,
    update_file_tab_display,
    remove_active_file,
    show_file_upload_dialog
)

__all__ = [
    'process_uploaded_file',
    'update_header_display',
    'update_file_tab_display',
    'remove_active_file',
    'show_file_upload_dialog'
]
