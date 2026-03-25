#!/usr/bin/env python3
"""
Interface NiceGUI pour le système de nettoyage OGMA
Permet de supprimer les données de manière sécurisée avec interface graphique
"""

import asyncio
from nicegui import ui, app
from data_cleaner import OGMADataCleaner, format_size, print_analysis_report
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List


class OGMACleanerUI:
    """Interface utilisateur pour le nettoyage des données OGMA"""
    
    def __init__(self):
        self.cleaner = OGMADataCleaner()
        self.analysis_data = None
        self.backup_created = False
        self.backup_dir = None
        
        # Contrôles UI
        self.selected_categories = {}
        self.confirmation_input = None
        self.delete_button = None
        self.analysis_expansion = None
        
    def create_ui(self):
        """Crée l'interface utilisateur complète"""
        
        # En-tête avec style
        with ui.card().classes('w-full').style('background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white'):
            ui.label('🗑️ Nettoyage Sécurisé des Données OGMA').classes('text-h4 text-center')
            ui.label('Suppression complète pour créer un profil vierge').classes('text-subtitle1 text-center opacity-80')
        
        ui.separator()
        
        # Étape 1: Analyse des données
        with ui.card().classes('w-full'):
            ui.label('📊 Étape 1: Analyse des Données Existantes').classes('text-h6')
            
            with ui.row().classes('w-full items-center'):
                analyze_button = ui.button(
                    '🔍 Analyser les Données', 
                    on_click=self.analyze_data
                ).props('color=primary')
                
                self.analysis_status = ui.label('')
            
            # Zone d'expansion pour les détails d'analyse
            self.analysis_expansion = ui.expansion('Détails de l\'analyse').classes('w-full')
            with self.analysis_expansion:
                self.analysis_content = ui.column()
        
        ui.separator()
        
        # Étape 2: Sélection des données à supprimer
        with ui.card().classes('w-full'):
            ui.label('✅ Étape 2: Sélection des Données à Supprimer').classes('text-h6')
            
            # Zone d'avertissement
            with ui.card().style('background: #ffebee; border-left: 4px solid #f44336; margin: 10px 0'):
                ui.label('⚠️ ATTENTION - SUPPRESSION IRRÉVERSIBLE').classes('text-bold text-red')
                ui.label('Une fois supprimées, ces données ne pourront plus être récupérées (sauf depuis la sauvegarde automatique).')
            
            self.selection_container = ui.column().classes('w-full')
            
        ui.separator()
        
        # Étape 3: Confirmation et exécution
        with ui.card().classes('w-full'):
            ui.label('🔐 Étape 3: Confirmation et Exécution').classes('text-h6')
            
            with ui.column().classes('w-full'):
                ui.label('Pour confirmer la suppression, tapez: DELETE-ALL-OGMA-DATA').classes('text-subtitle2')
                self.confirmation_input = ui.input('Code de confirmation').props('outlined').classes('w-full')
                
                ui.separator()
                
                with ui.row().classes('w-full'):
                    backup_button = ui.button(
                        '💾 Créer Sauvegarde', 
                        on_click=self.create_backup
                    ).props('color=positive outline')
                    
                    self.delete_button = ui.button(
                        '🗑️ SUPPRIMER DÉFINITIVEMENT', 
                        on_click=self.execute_deletion
                    ).props('color=negative')
                    
                # Désactiver le bouton par défaut
                self.delete_button.enabled = False
                
                # Configurer la validation
                self.confirmation_input.on('input', self.validate_confirmation)
        
        # Zone de résultats
        ui.separator()
        with ui.card().classes('w-full'):
            ui.label('📋 Résultats').classes('text-h6')
            self.results_container = ui.column().classes('w-full')
    
    async def analyze_data(self):
        """Analyse les données existantes"""
        self.analysis_status.text = '🔄 Analyse en cours...'
        
        try:
            # Analyser les données
            self.analysis_data = self.cleaner.analyze_current_data()
            
            # Effacer le contenu précédent
            self.analysis_content.clear()
            
            with self.analysis_content:
                # Résumé global
                ui.label(f'📈 Résumé Global').classes('text-subtitle1 text-bold')
                ui.label(f'Total: {self.analysis_data["total_files"]} fichiers ({format_size(self.analysis_data["total_size"])})')
                
                ui.separator()
                
                # Détail par catégorie
                categories = ['memory', 'conversations', 'ego_data', 'temp_files']
                
                for category in categories:
                    data = self.analysis_data.get(category, {})
                    if data.get('file_count', 0) > 0:
                        self.create_category_details(category, data)
            
            # Créer les options de sélection
            self.create_selection_options()
            
            # Ouvrir l'expansion automatiquement
            if self.analysis_expansion:
                self.analysis_expansion.open()
            
            self.analysis_status.text = '✅ Analyse terminée'
            
        except Exception as e:
            self.analysis_status.text = f'❌ Erreur: {e}'
    
    def create_category_details(self, category: str, data: Dict):
        """Crée les détails d'affichage pour une catégorie"""
        
        category_names = {
            'memory': '🧠 Mémoire',
            'conversations': '💬 Conversations', 
            'ego_data': '🎭 Données Ego',
            'temp_files': '🗑️ Fichiers Temporaires'
        }
        
        with ui.expansion(f'{category_names[category]} ({data["file_count"]} fichiers, {format_size(data["total_size"])})'):
            
            if category == 'memory':
                if data.get('memory_count'):
                    ui.label(f'• Souvenirs stockés: {data["memory_count"]}')
                if data.get('memories_db'):
                    ui.label(f'• Base de données: {data["memories_db"]["size_mb"]} MB')
                if data.get('faiss_index'):
                    ui.label(f'• Index FAISS: {data["faiss_index"]["size_mb"]} MB')
                if data.get('backups'):
                    ui.label(f'• Fichiers de sauvegarde: {len(data["backups"])}')
                    
            elif category == 'conversations':
                ui.label(f'• Conversations actives: {data["conversation_count"]}')
                if data.get('conversations'):
                    recent_convs = [c for c in data['conversations'] if '2025-09-20' in c['name']]
                    ui.label(f'• Conversations récentes (aujourd\'hui): {len(recent_convs)}')
                    
            elif category == 'ego_data':
                if data.get('ego_prompt'):
                    ui.label(f'• Ego prompt: {data["ego_prompt"]["lines"]} lignes')
                if data.get('ego_archive'):
                    ui.label(f'• Archives ego: {len(data["ego_archive"])} fichiers')
                if data.get('persistent_context'):
                    ui.label(f'• Contexte persistant: {format_size(data["persistent_context"]["size"])}')
                    
            elif category == 'temp_files':
                for temp_type in ['temp_files', 'cache_files', 'log_files']:
                    files = data.get(temp_type, [])
                    if files:
                        total_size = sum(f['size'] for f in files)
                        ui.label(f'• {temp_type.replace("_", " ").title()}: {len(files)} fichiers ({format_size(total_size)})')
    
    def create_selection_options(self):
        """Crée les options de sélection des catégories"""
        
        self.selection_container.clear()
        self.selected_categories = {}
        
        if not self.analysis_data:
            return
        
        with self.selection_container:
            ui.label('Sélectionnez les données à supprimer:').classes('text-subtitle1')
            
            categories_info = {
                'memory': {
                    'label': '🧠 Mémoire complète (souvenirs, index FAISS, sauvegardes)',
                    'description': f"{self.analysis_data['memory'].get('file_count', 0)} fichiers - {format_size(self.analysis_data['memory'].get('total_size', 0))}",
                    'warning': 'ATTENTION: Supprime tous les souvenirs de l\'IA'
                },
                'conversations': {
                    'label': '💬 Toutes les conversations',
                    'description': f"{self.analysis_data['conversations'].get('file_count', 0)} fichiers - {format_size(self.analysis_data['conversations'].get('total_size', 0))}",
                    'warning': 'ATTENTION: Supprime tout l\'historique de chat'
                },
                'ego_data': {
                    'label': '🎭 Données ego (personnalité, contexte)',
                    'description': f"{self.analysis_data['ego_data'].get('file_count', 0)} fichiers - {format_size(self.analysis_data['ego_data'].get('total_size', 0))}",
                    'warning': 'ATTENTION: Supprime la personnalité de l\'IA'
                },
                'temp_files': {
                    'label': '🗑️ Fichiers temporaires et caches',
                    'description': f"{self.analysis_data['temp_files'].get('file_count', 0)} fichiers - {format_size(self.analysis_data['temp_files'].get('total_size', 0))}",
                    'warning': 'Nettoyage sûr des fichiers temporaires'
                }
            }
            
            for category, info in categories_info.items():
                if self.analysis_data.get(category, {}).get('file_count', 0) > 0:
                    
                    with ui.card().classes('w-full'):
                        checkbox = ui.checkbox(info['label'])
                        self.selected_categories[category] = checkbox
                        
                        ui.label(info['description']).style('color: #666; font-size: 0.9em')
                        
                        # Avertissement
                        warning_color = 'color: #f44336' if 'ATTENTION' in info['warning'] else 'color: #4caf50'
                        ui.label(info['warning']).style(f'{warning_color}; font-weight: bold; font-size: 0.85em')
                        
                        # Configurer la validation à chaque changement
                        checkbox.on('change', self.validate_confirmation)
    
    def validate_confirmation(self):
        """Valide les conditions pour activer le bouton de suppression"""
        if not self.confirmation_input or not self.delete_button:
            return
            
        # Vérifier le code de confirmation
        expected_code = "DELETE-ALL-OGMA-DATA"
        code_valid = self.confirmation_input.value == expected_code
        
        # Vérifier qu'au moins une catégorie est sélectionnée
        has_selection = any(cb.value for cb in self.selected_categories.values())
        
        # Activer le bouton seulement si tout est correct
        self.delete_button.enabled = code_valid and has_selection
    
    async def create_backup(self):
        """Crée une sauvegarde avant suppression"""
        try:
            self.add_result('💾 Création de la sauvegarde...')
            
            # Créer la sauvegarde
            backup_dir = self.cleaner.create_backup()
            self.backup_created = True
            self.backup_dir = backup_dir
            
            # Calculer la taille de la sauvegarde
            backup_size = sum(f.stat().st_size for f in backup_dir.rglob('*') if f.is_file())
            
            self.add_result(f'✅ Sauvegarde créée: {backup_dir}')
            self.add_result(f'📦 Taille sauvegarde: {format_size(backup_size)}')
            
        except Exception as e:
            self.add_result(f'❌ Erreur création sauvegarde: {e}')
    
    async def execute_deletion(self):
        """Exécute la suppression des données sélectionnées"""
        
        if not self.backup_created:
            # Créer automatiquement une sauvegarde
            await self.create_backup()
        
        try:
            # Collecter les catégories sélectionnées
            selected = [cat for cat, cb in self.selected_categories.items() if cb.value]
            
            if not selected:
                self.add_result('❌ Aucune catégorie sélectionnée')
                return
            
            self.add_result(f'🔄 Suppression en cours: {", ".join(selected)}')
            
            # Exécuter la suppression
            confirmation_code = self.confirmation_input.value if self.confirmation_input else ""
            deletion_log = self.cleaner.delete_selected_data(
                categories=selected,
                confirmation_code=confirmation_code
            )
            
            # Afficher les résultats
            for log_entry in deletion_log:
                self.add_result(log_entry)
            
            # Vérifier l'état final
            verification = self.cleaner.verify_clean_state()
            
            if verification['all_clean']:
                self.add_result('✅ Nettoyage terminé avec succès!')
                self.add_result('🎉 OGMA a maintenant un profil complètement vierge')
            else:
                self.add_result('⚠️ Nettoyage partiellement réussi')
                for issue in verification['issues']:
                    self.add_result(f'   • {issue}')
            
            # Désactiver les contrôles après suppression
            if self.delete_button:
                self.delete_button.enabled = False
            for cb in self.selected_categories.values():
                cb.enabled = False
            if self.confirmation_input:
                self.confirmation_input.enabled = False
            
        except Exception as e:
            self.add_result(f'❌ Erreur lors de la suppression: {e}')
    
    def add_result(self, message: str):
        """Ajoute un message dans la zone de résultats"""
        with self.results_container:
            timestamp = datetime.now().strftime('%H:%M:%S')
            ui.label(f'[{timestamp}] {message}')


def main():
    """Point d'entrée principal"""
    
    # Configuration de l'application
    ui.run(
        title="OGMA Data Cleaner",
        port=8081,
        reload=False,
        show=False,  # Ne pas ouvrir automatiquement le navigateur
        storage_secret="ogma_cleaner_secret_key_2025"
    )


@ui.page('/')
def index():
    """Page principale de l'interface"""
    cleaner_ui = OGMACleanerUI()
    cleaner_ui.create_ui()


if __name__ == "__main__":
    print("🚀 Démarrage de l'interface OGMA Data Cleaner...")
    print("📍 Interface disponible sur: http://localhost:8081")
    print("⚠️  ATTENTION: Cette interface permet de supprimer TOUTES les données OGMA!")
    print()
    
    main()