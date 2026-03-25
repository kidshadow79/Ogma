# JOURNAL Extension Journal de Bord - Composants Interface Utilisateur

"""
Composants interface utilisateur pour l'extension Journal de Bord
Bouton header, modal principal, calendrier, intégration NiceGUI
"""

from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, date, timedelta
import asyncio
import time

try:
    import importlib
    _ng = importlib.import_module('nicegui')
    _ui = getattr(_ng, 'ui', None)
    _app = getattr(_ng, 'app', None)
except Exception:  # environnement sans NiceGUI installé (lint only)
    _ui = None  # type: ignore
    _app = None  # type: ignore

class _Dummy:
    def __getattr__(self, name):
        return self
    def __call__(self, *args, **kwargs):
        return self
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False

# Forcer un type Any pour éviter les erreurs d'analyse lorsque NiceGUI n'est pas présent
ui: Any = _ui if _ui is not None else _Dummy()

class JournalUI:
    """
    Interface utilisateur principale pour l'extension Journal de Bord

    Responsabilités:
    - Bouton header intégré dans OGMA
    - Modal principal avec calendrier et navigation
    - Interface de recherche et filtrage
    - Affichage des entrées et détails
    - Intégration NiceGUI cohérente avec OGMA
    """

    def __init__(self, config, core_journal, json_manager):
        """Initialise l'interface utilisateur"""
        self.config = config
        self.core_journal = core_journal
        self.json_manager = json_manager

        # Paramètres UI
        self.ui_settings = self.config.get_ui_settings()
        self.button_position = self.ui_settings["button_position"]
        self.modal_size = self.ui_settings["modal_size"]
        self.theme_mode = self.ui_settings["theme_mode"]

        # État UI
        self.header_button = None
        self.main_modal = None
        self.calendar_component = None
        self.entries_panel = None
        self.detail_panel = None

        # Données UI
        self.selected_date = None
        self.current_entries = []
        self.search_query = ""
        self.active_filters = {}

        # Callbacks
        self.on_entry_selected = None
        self.on_date_changed = None
        self.on_search_performed = None

        print(f"[JOURNAL-UI] OK Interface initialisée (thème: {self.theme_mode})")

    def inject_header_button(self, header_container):
        """
        Injecte le bouton journal dans le header OGMA

        Args:
            header_container: Container du header OGMA
        """
        try:
            print("[JOURNAL-UI] 🔧 Injection bouton header")

            with header_container:
                # Bouton journal avec style OGMA cohérent (icône book comme les autres)
                self.header_button = ui.button(
                    icon="book",
                    on_click=self._on_header_button_click
                ).classes(
                    "settings-floating-btn"
                ).props('dense flat').style(
                    "background: linear-gradient(135deg, #8B5A2B 0%, #CD853F 100%); "
                    "border: 1px solid #A0522D;"
                )

                # Tooltip explicatif
                with self.header_button:
                    ui.tooltip("Journal de Bord - Capturer et consulter vos conversations")
                    
                    # Badge compteur auto-archive (v2.0) - directement dans le bouton
                    if self.config.get("auto_archive_enabled", False):
                        frequency = self.config.get("auto_archive_frequency", 20)
                        self.auto_archive_counter = ui.badge(f"0/{frequency}", color="orange").props('floating').classes(
                            "text-xs font-mono font-bold"
                        ).style("font-size: 10px;")
                        
                        with self.auto_archive_counter:
                            ui.tooltip("Progression vers prochaine auto-archive")

            print("[JOURNAL-UI] OK Bouton header injecté avec succès")

        except Exception as e:
            print(f"[JOURNAL-UI] ERROR Erreur injection header: {e}")
            raise

    async def _on_header_button_click(self):
        """Gestionnaire clic bouton header - ouvre le modal principal"""
        try:
            print("[JOURNAL-UI] JOURNAL Ouverture modal journal")
            await self.open_main_modal()
        except Exception as e:
            print(f"[JOURNAL-UI] ERROR Erreur ouverture modal: {e}")
            ui.notify(f"Erreur ouverture journal: {e}", type="negative")

    async def open_main_modal(self):
        """Ouvre le modal principal du journal"""
        try:
            # Fermer modal existant si ouvert
            if self.main_modal:
                self.main_modal.close()

            # Calcul taille selon configuration
            modal_sizes = {
                "small": "60vw",
                "medium": "80vw",
                "large": "90vw"
            }
            modal_width = modal_sizes.get(self.modal_size, "90vw")

            # Création du modal principal
            with ui.dialog() as self.main_modal:
                with ui.card().classes("w-full").style(f"width: {modal_width}; height: 85vh; max-width: 1400px;"):
                    # Header du modal
                    await self._create_modal_header()

                    # Contenu principal avec layout flex
                    with ui.row().classes("w-full h-full gap-0").style("flex: 1; height: calc(100% - 60px);"):
                        # Panneau calendrier (gauche)
                        await self._create_calendar_panel()

                        # Panneau entrées (centre)
                        await self._create_entries_panel()

                        # Panneau détail (droite)
                        await self._create_detail_panel()

            # Ouverture du modal
            self.main_modal.open()

            # Initialisation avec la date actuelle
            await self._load_today_entries()

            print("[JOURNAL-UI] OK Modal principal ouvert")

        except Exception as e:
            print(f"[JOURNAL-UI] ERROR Erreur création modal: {e}")
            ui.notify(f"Erreur ouverture journal: {e}", type="negative")

    async def _create_modal_header(self):
        """Crée l'en-tête du modal"""
        with ui.row().classes("w-full items-center justify-between p-4 border-b").style("min-height: 60px;"):
            # Titre avec icône
            with ui.row().classes("items-center gap-2"):
                ui.icon("book", size="24px").classes("text-orange-600")
                ui.label("Journal de Bord").classes("text-xl font-bold text-gray-800")

                # Badge avec stats
                stats = self.core_journal.get_journal_stats()
                ui.badge(f"{stats['total_entries']} entrées").classes("bg-orange-100 text-orange-800")

            # Actions header
            with ui.row().classes("gap-2"):
                # Bouton États Actifs v2.0
                ui.button(
                    "🎯 États Actifs",
                    on_click=self.open_active_states_modal
                ).classes("bg-purple-600 hover:bg-purple-700 text-white")
                
                # Bouton Maintenance (Option C)
                ui.button(
                    "🧹 Maintenance",
                    on_click=self.open_maintenance_modal
                ).classes("bg-amber-600 hover:bg-amber-700 text-white")
                
                # Bouton nouvelle entrée
                ui.button(
                    "CREATE Capturer conversation",
                    on_click=self._on_create_entry_click
                ).classes("bg-green-600 hover:bg-green-700 text-white")

                # Bouton recherche
                ui.button(
                    "SEARCH",
                    on_click=self._toggle_search_panel
                ).classes("bg-blue-600 hover:bg-blue-700 text-white").props('dense')

                # Bouton fermer
                ui.button(
                    "✕",
                    on_click=lambda: self.main_modal.close()
                ).classes("bg-gray-500 hover:bg-gray-600 text-white").props('dense')

    async def _create_calendar_panel(self):
        """Crée le panneau calendrier de navigation"""
        with ui.column().classes("w-80 border-r bg-gray-50 p-4").style("min-width: 320px; max-width: 320px;"):
            # Titre panneau
            ui.label("📅 Navigation").classes("text-lg font-semibold mb-4")

            # Sélecteur mois/année
            with ui.row().classes("w-full items-center gap-2 mb-4"):
                current_date = datetime.now()

                # Boutons navigation mois
                ui.button("‹", on_click=self._prev_month).classes("bg-gray-200 hover:bg-gray-300").props('dense')

                # Affichage mois/année actuel
                self.month_label = ui.label(current_date.strftime("%B %Y")).classes("flex-1 text-center font-medium")

                ui.button("›", on_click=self._next_month).classes("bg-gray-200 hover:bg-gray-300").props('dense')

            # Mini calendrier (simplifié pour le moment)
            await self._create_mini_calendar()

            # Statistiques rapides
            with ui.card().classes("w-full mt-4 p-3"):
                ui.label("STATS Statistiques").classes("font-medium mb-2")

                stats = self.core_journal.get_journal_stats()
                ui.label(f"Total entrées: {stats['total_entries']}").classes("text-sm")
                ui.label(f"Jours actifs: {stats['days_with_entries']}").classes("text-sm")
                if stats['last_entry_date']:
                    ui.label(f"Dernière: {stats['last_entry_date']}").classes("text-sm")

    async def _create_mini_calendar(self):
        """Crée un mini calendrier de navigation"""
        # Pour le moment, liste simple des derniers jours
        # TODO: Implémenter vrai calendrier graphique

        ui.label("Derniers jours:").classes("text-sm font-medium mb-2")

        with ui.column().classes("w-full gap-1"):
            # Générer les 14 derniers jours
            today = date.today()
            for i in range(14):
                check_date = today - timedelta(days=i)
                date_str = check_date.strftime("%Y-%m-%d")

                # Vérifier si des entrées existent pour cette date
                entries = self.json_manager.get_day_entries(date_str)
                entry_count = len(entries) if entries else 0

                # Style selon activité
                if entry_count > 0:
                    classes = "bg-orange-100 hover:bg-orange-200 text-orange-800"
                    indicator = f"• {entry_count}"
                else:
                    classes = "bg-gray-100 hover:bg-gray-200 text-gray-600"
                    indicator = ""

                # Bouton jour
                day_label = check_date.strftime("%d/%m")
                if i == 0:
                    day_label = "Aujourd'hui"
                elif i == 1:
                    day_label = "Hier"

                ui.button(
                    f"{day_label} {indicator}",
                    on_click=lambda d=date_str: self._on_date_selected(d)
                ).classes(f"w-full justify-start text-left {classes}").props('dense')

    async def _create_entries_panel(self):
        """Crée le panneau liste des entrées"""
        with ui.column().classes("flex-1 p-4").style("min-width: 400px;"):
            # Header panneau entrées
            with ui.row().classes("w-full items-center justify-between mb-4"):
                self.entries_title = ui.label("📝 Entrées d'aujourd'hui").classes("text-lg font-semibold")

                # Filtres rapides
                with ui.row().classes("gap-2"):
                    ui.select(
                        ["Toutes", "Importantes", "Normales", "Récentes"],
                        value="Toutes",
                        on_change=self._on_filter_change
                    ).classes("w-32").props('dense')

            # Zone recherche (masquée par défaut)
            self.search_panel = ui.row().classes("w-full gap-2 mb-4 hidden")
            with self.search_panel:
                self.search_input = ui.input(
                    placeholder="Rechercher dans les entrées...",
                    on_change=self._on_search_change
                ).classes("flex-1")
                ui.button("SEARCH", on_click=self._perform_search).props('dense')

            # Liste des entrées
            with ui.scroll_area().classes("w-full").style("height: calc(100vh - 300px);"):
                self.entries_container = ui.column().classes("w-full gap-2")

    async def _create_detail_panel(self):
        """Crée le panneau détail d'entrée"""
        with ui.column().classes("w-96 border-l bg-gray-50 p-4").style("min-width: 384px; max-width: 384px;"):
            # Header détail
            ui.label("SEARCH Détail").classes("text-lg font-semibold mb-4")

            # Zone détail (vide par défaut)
            self.detail_container = ui.column().classes("w-full")
            with self.detail_container:
                ui.label("Sélectionnez une entrée pour voir les détails").classes("text-gray-500 text-center")

    async def _load_today_entries(self):
        """Charge les entrées d'aujourd'hui"""
        today_str = date.today().strftime("%Y-%m-%d")
        await self._load_entries_for_date(today_str)

    async def _load_entries_for_date(self, date_str: str):
        """Charge les entrées pour une date donnée"""
        try:
            print(f"[JOURNAL-UI] 📅 Chargement entrées pour {date_str}")

            # Récupération des entrées
            entries = self.json_manager.get_day_entries(date_str)
            self.current_entries = entries or []

            # Mise à jour titre
            formatted_date = datetime.strptime(date_str, "%Y-%m-%d").strftime("%d/%m/%Y")
            if date_str == date.today().strftime("%Y-%m-%d"):
                date_label = "aujourd'hui"
            else:
                date_label = formatted_date

            self.entries_title.text = f"📝 Entrées du {date_label} ({len(self.current_entries)})"

            # Effacer ancien contenu
            self.entries_container.clear()

            # Afficher entrées
            if self.current_entries:
                for entry in self.current_entries:
                    await self._create_entry_card(entry)
            else:
                with self.entries_container:
                    ui.label("Aucune entrée pour cette date").classes("text-gray-500 text-center p-4")
                    ui.button(
                        "CREATE Créer une entrée",
                        on_click=self._on_create_entry_click
                    ).classes("bg-green-600 hover:bg-green-700 text-white mx-auto")

            print(f"[JOURNAL-UI] OK {len(self.current_entries)} entrées chargées")

        except Exception as e:
            print(f"[JOURNAL-UI] ERROR Erreur chargement entrées: {e}")
            ui.notify(f"Erreur chargement: {e}", type="negative")

    async def _create_entry_card(self, entry: Dict[str, Any]):
        """Crée une carte d'entrée dans la liste"""
        with self.entries_container:
            with ui.card().classes("w-full cursor-pointer hover:shadow-md transition-shadow").on('click', lambda e=entry: self._on_entry_click(e)):
                with ui.row().classes("w-full items-start gap-3 p-2"):
                    # Indicateur importance
                    importance = entry.get("importance", "normal")
                    importance_colors = {
                        "critical": "bg-red-500",
                        "high": "bg-orange-500",
                        "normal": "bg-blue-500",
                        "low": "bg-gray-500"
                    }
                    ui.icon("circle").classes(f"text-xs {importance_colors.get(importance, 'bg-blue-500')} rounded-full")

                    # Contenu entrée
                    with ui.column().classes("flex-1 gap-1"):
                        # Résumé (tronqué)
                        summary = entry.get("summary", "")
                        preview = summary[:100] + "..." if len(summary) > 100 else summary
                        ui.label(preview).classes("text-sm font-medium")

                        # Métadonnées
                        with ui.row().classes("gap-2 text-xs text-gray-600"):
                            # Heure
                            timestamp = entry.get("timestamp", "")
                            if timestamp:
                                time_str = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).strftime("%H:%M")
                                ui.label(f"🕐 {time_str}")

                            # Tags
                            tags = entry.get("tags", [])[:3]  # Max 3 tags affichés
                            for tag in tags:
                                ui.badge(tag).classes("bg-gray-200 text-gray-700 text-xs")

                            # Tokens
                            tokens = entry.get("tokens", 0)
                            if tokens:
                                ui.label(f"📄 {tokens}t").classes("text-xs")

    def _on_entry_click(self, entry: Dict[str, Any]):
        """Gestionnaire clic sur une entrée"""
        try:
            print(f"[JOURNAL-UI] 👆 Sélection entrée: {entry.get('id', 'unknown')}")
            self._show_entry_detail(entry)

            # Callback externe si défini
            if self.on_entry_selected:
                self.on_entry_selected(entry)

        except Exception as e:
            print(f"[JOURNAL-UI] ERROR Erreur sélection entrée: {e}")

    def _show_entry_detail(self, entry: Dict[str, Any]):
        """Affiche le détail d'une entrée dans le panneau droit"""
        try:
            # Effacer contenu précédent
            self.detail_container.clear()

            with self.detail_container:
                # Header détail
                with ui.row().classes("w-full items-center gap-2 mb-4"):
                    importance = entry.get("importance", "normal")
                    importance_icons = {
                        "critical": "🔴",
                        "high": "🟠",
                        "normal": "🔵",
                        "low": "⚪"
                    }
                    ui.label(importance_icons.get(importance, "🔵")).classes("text-lg")
                    ui.label("Détail de l'entrée").classes("font-semibold")

                # Métadonnées principales
                with ui.card().classes("w-full p-3 mb-3"):
                    ui.label("📋 Informations").classes("font-medium mb-2")

                    # ID et timestamp
                    ui.label(f"ID: {entry.get('id', 'N/A')}").classes("text-xs text-gray-600")

                    timestamp = entry.get("timestamp", "")
                    if timestamp:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        ui.label(f"📅 {dt.strftime('%d/%m/%Y à %H:%M')}").classes("text-sm")

                    # Tokens et modèle
                    tokens = entry.get("tokens", 0)
                    model = entry.get("generation_model", "N/A")
                    ui.label(f"📄 {tokens} tokens (via {model})").classes("text-sm")

                # Résumé complet
                with ui.card().classes("w-full p-3 mb-3"):
                    ui.label("📝 Résumé").classes("font-medium mb-2")
                    summary = entry.get("summary", "Aucun résumé disponible")
                    ui.label(summary).classes("text-sm leading-relaxed")

                # Tags et catégorie
                tags = entry.get("tags", [])
                if tags:
                    with ui.card().classes("w-full p-3 mb-3"):
                        ui.label("🏷️ Tags").classes("font-medium mb-2")
                        with ui.row().classes("gap-1 flex-wrap"):
                            for tag in tags:
                                ui.badge(tag).classes("bg-blue-100 text-blue-800")

                # Participants
                participants = entry.get("participants", [])
                if participants:
                    with ui.card().classes("w-full p-3 mb-3"):
                        ui.label("👥 Participants").classes("font-medium mb-2")
                        ui.label(", ".join(participants)).classes("text-sm")

                # Actions
                with ui.row().classes("w-full gap-2 mt-4"):
                    ui.button(
                        "📋 Copier résumé",
                        on_click=lambda: self._copy_summary(entry)
                    ).classes("bg-blue-600 hover:bg-blue-700 text-white").props('dense')

                    ui.button(
                        "🔗 Voir conversation",
                        on_click=lambda: self._show_conversation(entry)
                    ).classes("bg-green-600 hover:bg-green-700 text-white").props('dense')

                    ui.button(
                        "🗑️ Supprimer",
                        on_click=lambda: self._delete_entry(entry)
                    ).classes("bg-red-600 hover:bg-red-700 text-white").props('dense')

        except Exception as e:
            print(f"[JOURNAL-UI] ERROR Erreur affichage détail: {e}")

    def _delete_entry(self, entry: Dict[str, Any]):
        """Supprime une entrée après confirmation"""
        entry_id = entry.get("id", "unknown")
        
        # Extraire la date depuis le timestamp (format YYYY-MM-DD)
        timestamp = entry.get("timestamp", "")
        date_str = timestamp[:10] if timestamp else entry.get("date", "")
        
        if not date_str:
            ui.notify("❌ Impossible de déterminer la date de l'entrée", type="negative")
            return
        
        # Dialogue de confirmation créé directement dans le contexte UI
        with ui.dialog() as dialog, ui.card().classes("p-6"):
            ui.label("⚠️ Confirmer la suppression").classes("text-lg font-bold mb-3")
            ui.label(f"Voulez-vous vraiment supprimer cette entrée ?").classes("mb-2")
            ui.label(f"Date: {date_str}").classes("text-sm text-gray-600 mb-4")
            ui.label("Cette action est irréversible.").classes("text-sm text-red-600 mb-4")
            
            with ui.row().classes("w-full gap-2 justify-end"):
                ui.button("Annuler", on_click=dialog.close).classes("bg-gray-500 hover:bg-gray-600 text-white")
                ui.button("Supprimer", on_click=lambda: self._confirm_delete_entry(entry_id, date_str, dialog)).classes("bg-red-600 hover:bg-red-700 text-white")
        
        dialog.open()

    def _confirm_delete_entry(self, entry_id: str, date_str: str, dialog):
        """Exécute la suppression après confirmation"""
        try:
            # Suppression via json_manager
            success = self.json_manager.delete_entry(entry_id, date_str)
            
            if success:
                print(f"[JOURNAL-UI] ✅ Entrée {entry_id} supprimée")
                ui.notify("✅ Entrée supprimée avec succès", type="positive")
                dialog.close()
                
                # Rafraîchir la liste
                self._refresh_entries_list()
                
                # Vider le panneau de détail
                self.detail_container.clear()
            else:
                print(f"[JOURNAL-UI] ❌ Échec suppression entrée {entry_id}")
                ui.notify("❌ Erreur lors de la suppression", type="negative")
                
        except Exception as e:
            print(f"[JOURNAL-UI] ERROR Erreur suppression: {e}")
            ui.notify(f"Erreur: {e}", type="negative")

    def _refresh_entries_list(self):
        """Rafraîchit la liste des entrées affichées"""
        try:
            # Recharger les entrées pour la date sélectionnée
            if self.selected_date:
                entries = self.json_manager.get_entries_by_date(self.selected_date)
                self.current_entries = entries
                
                # Rafraîchir l'affichage (créer directement les cartes dans le contexte UI)
                self.entries_container.clear()
                
                # Créer les cartes d'entrée en synchrone
                import asyncio
                for entry in entries:
                    # Créer la carte directement (version synchrone)
                    with self.entries_container:
                        with ui.card().classes("w-full cursor-pointer hover:shadow-md transition-shadow").on('click', lambda e=entry: self._on_entry_click(e)):
                            with ui.row().classes("w-full items-start gap-3 p-2"):
                                # Indicateur importance
                                importance = entry.get("importance", "normal")
                                importance_colors = {
                                    "critical": "bg-red-500",
                                    "high": "bg-orange-500",
                                    "normal": "bg-blue-500",
                                    "low": "bg-gray-500"
                                }
                                ui.icon("circle").classes(f"text-xs {importance_colors.get(importance, 'bg-blue-500')} rounded-full")

                                # Contenu entrée
                                with ui.column().classes("flex-1 gap-1"):
                                    # Résumé (tronqué)
                                    summary = entry.get("summary", "")
                                    preview = summary[:100] + "..." if len(summary) > 100 else summary
                                    ui.label(preview).classes("text-sm font-medium")

                                    # Métadonnées
                                    with ui.row().classes("gap-2 text-xs text-gray-600"):
                                        # Heure
                                        timestamp = entry.get("timestamp", "")
                                        if timestamp:
                                            time_str = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).strftime("%H:%M")
                                            ui.label(f"🕐 {time_str}")

                                        # Tags
                                        tags = entry.get("tags", [])[:3]  # Max 3 tags affichés
                                        for tag in tags:
                                            ui.badge(tag).classes("bg-gray-200 text-gray-700 text-xs")

                                        # Tokens
                                        tokens = entry.get("tokens", 0)
                                        if tokens:
                                            ui.label(f"📄 {tokens}t").classes("text-xs")
                
                print(f"[JOURNAL-UI] ✅ Liste rafraîchie: {len(entries)} entrées")
        except Exception as e:
            print(f"[JOURNAL-UI] ERROR Erreur rafraîchissement liste: {e}")

    def _copy_summary(self, entry: Dict[str, Any]):
        """Copie le résumé dans le presse-papiers"""
        summary = entry.get("summary", "")
        # TODO: Implémenter copie presse-papiers
        ui.notify("Résumé copié !", type="positive")

    def _show_conversation(self, entry: Dict[str, Any]):
        """Affiche la conversation complète"""
        conv_id = entry.get("conversation_id", "")
        # TODO: Implémenter affichage conversation
        ui.notify(f"Ouverture conversation {conv_id}", type="info")

    def _on_date_selected(self, date_str: str):
        """Gestionnaire sélection de date"""
        try:
            print(f"[JOURNAL-UI] 📅 Date sélectionnée: {date_str}")
            self.selected_date = date_str
            asyncio.create_task(self._load_entries_for_date(date_str))

            # Callback externe si défini
            if self.on_date_changed:
                self.on_date_changed(date_str)

        except Exception as e:
            print(f"[JOURNAL-UI] ERROR Erreur sélection date: {e}")

    def _prev_month(self):
        """Navigation mois précédent"""
        # TODO: Implémenter navigation mois
        ui.notify("Navigation mois précédent", type="info")

    def _next_month(self):
        """Navigation mois suivant"""
        # TODO: Implémenter navigation mois
        ui.notify("Navigation mois suivant", type="info")

    def _toggle_search_panel(self):
        """Bascule l'affichage du panneau recherche"""
        if "hidden" in self.search_panel.classes:
            self.search_panel.classes = self.search_panel.classes.replace("hidden", "")
            self.search_input.focus()
        else:
            self.search_panel.classes += " hidden"
            self.search_input.value = ""

    def _on_filter_change(self, e):
        """Gestionnaire changement filtre"""
        filter_value = e.value
        print(f"[JOURNAL-UI] SEARCH Filtre changé: {filter_value}")
        # TODO: Implémenter filtrage
        ui.notify(f"Filtre: {filter_value}", type="info")

    def _on_search_change(self, e):
        """Gestionnaire changement recherche"""
        self.search_query = e.value
        if len(self.search_query) >= 3:
            # Recherche automatique après 3 caractères
            asyncio.create_task(self._perform_search())

    async def _perform_search(self):
        """Effectue une recherche dans les entrées"""
        try:
            if not self.search_query.strip():
                return

            print(f"[JOURNAL-UI] SEARCH Recherche: '{self.search_query}'")

            # Recherche via json_manager
            results = self.json_manager.search_entries(
                query=self.search_query,
                **self.active_filters
            )

            # Affichage résultats
            self.entries_title.text = f"SEARCH Résultats recherche: '{self.search_query}' ({len(results)})"

            # Effacer liste actuelle
            self.entries_container.clear()

            if results:
                for entry in results:
                    await self._create_entry_card(entry)
            else:
                with self.entries_container:
                    ui.label("Aucun résultat trouvé").classes("text-gray-500 text-center p-4")

            # Callback externe si défini
            if self.on_search_performed:
                self.on_search_performed(self.search_query, results)

            ui.notify(f"Recherche: {len(results)} résultats", type="info")

        except Exception as e:
            print(f"[JOURNAL-UI] ERROR Erreur recherche: {e}")
            ui.notify(f"Erreur recherche: {e}", type="negative")

    async def _on_create_entry_click(self):
        """Gestionnaire création nouvelle entrée"""
        try:
            print("[JOURNAL-UI] CREATE Création nouvelle entrée")

            # Afficher dialog de confirmation
            with ui.dialog() as create_dialog:
                with ui.card():
                    ui.label("CREATE Créer une nouvelle entrée").classes("text-lg font-bold mb-4")
                    ui.label("Cette action va capturer la conversation actuelle et générer un résumé via l'Archiviste.").classes("mb-4")

                    with ui.row().classes("gap-2"):
                        ui.button(
                            "Annuler",
                            on_click=create_dialog.close
                        ).classes("bg-gray-500 hover:bg-gray-600 text-white")

                        ui.button(
                            "CREATE Créer l'entrée",
                            on_click=lambda: self._create_entry_confirmed(create_dialog)
                        ).classes("bg-green-600 hover:bg-green-700 text-white")

            create_dialog.open()

        except Exception as e:
            print(f"[JOURNAL-UI] ERROR Erreur création entrée: {e}")
            ui.notify(f"Erreur: {e}", type="negative")

    async def _create_entry_confirmed(self, dialog):
        """Crée effectivement une nouvelle entrée"""
        try:
            dialog.close()

            # Notification en cours
            ui.notify("🤖 Génération du résumé en cours...", type="info")

            # 🔧 FIX: Récupérer conversation_id et historique pour création
            import sys
            ogma_headers = sys.modules.get('ogma_headers')
            
            if ogma_headers:
                conversation_id = ogma_headers._get_current_conversation_id()
                conversation_history = ogma_headers._get_global_var('_chat_history_ui', [])
            else:
                # Fallback si module non chargé
                conversation_id = None
                conversation_history = []
                print("[JOURNAL-UI] WARN ogma_headers non disponible - mode fallback")
            
            print(f"[JOURNAL-UI] CREATE Métadonnées: conv_id={conversation_id}, history={len(conversation_history)} msgs")

            # Création via core_journal avec métadonnées
            entry = await self.core_journal.create_entry_from_conversation(
                conversation_id=conversation_id,
                conversation_history=conversation_history
            )

            if entry:
                ui.notify("OK Entrée créée avec succès !", type="positive")

                # Recharger les entrées du jour actuel
                await self._load_today_entries()

                # Afficher le détail de la nouvelle entrée
                self._show_entry_detail(entry)
            else:
                ui.notify("ERROR Erreur lors de la création", type="negative")

        except Exception as e:
            print(f"[JOURNAL-UI] ERROR Erreur création entrée confirmée: {e}")
            ui.notify(f"Erreur création: {e}", type="negative")

    def get_components(self) -> Dict[str, Any]:
        """
        Retourne les composants UI pour intégration externe

        Returns:
            Dict: Composants UI disponibles
        """
        return {
            "header_button": self.header_button,
            "main_modal": self.main_modal,
            "calendar_component": self.calendar_component,
            "entries_panel": self.entries_panel,
            "detail_panel": self.detail_panel
        }

    def set_callbacks(self, **callbacks):
        """Configure les callbacks d'événements UI"""
        for callback_name, callback_func in callbacks.items():
            if hasattr(self, callback_name):
                setattr(self, callback_name, callback_func)
                print(f"[JOURNAL-UI] OK Callback {callback_name} configuré")

    # =========================================================================
    # COMPTEUR AUTO-ARCHIVE v2.0
    # =========================================================================
    
    def update_auto_archive_counter(self, current_count: int):
        """
        Met à jour le badge compteur auto-archive dans le header
        
        Args:
            current_count: Nombre actuel de messages dans la conversation
        """
        try:
            if not self.config.get("auto_archive_enabled", False):
                return
            
            if not hasattr(self, 'auto_archive_counter') or self.auto_archive_counter is None:
                return
            
            frequency = self.config.get("auto_archive_frequency", 20)
            progress = current_count % frequency
            
            # Mise à jour texte
            self.auto_archive_counter.text = f"{progress}/{frequency}"
            
            # Couleur progressive (ocre → orange → rouge)
            percentage = (progress / frequency) * 100
            if percentage >= 90:
                # Rouge - proche du trigger
                self.auto_archive_counter.classes(remove="bg-yellow-600 bg-orange-600", add="bg-red-600")
            elif percentage >= 70:
                # Orange vif - mi-chemin
                self.auto_archive_counter.classes(remove="bg-yellow-600 bg-red-600", add="bg-orange-600")
            else:
                # Jaune/Ocre - début
                self.auto_archive_counter.classes(remove="bg-orange-600 bg-red-600", add="bg-yellow-600")
            
        except Exception as e:
            print(f"[JOURNAL-UI] WARN Erreur MAJ compteur: {e}")
    
    # =========================================================================
    # GESTION ÉTATS ACTIFS v2.0
    # =========================================================================
    
    async def open_active_states_modal(self):
        """Ouvre le modal de gestion des états actifs"""
        try:
            print("[JOURNAL-UI] 🎯 Ouverture modal états actifs")
            
            # Récupérer états actifs
            états_actifs = self.json_manager.get_active_states()
            all_states = états_actifs.get("states", [])
            unresolved = [s for s in all_states if not s.get("resolved", False)]
            
            # Création modal
            with ui.dialog() as states_modal, ui.card().classes("w-full").style("width: 90vw; max-width: 1200px; max-height: 90vh; display: flex; flex-direction: column;"):
                # Header
                with ui.row().classes("w-full items-center justify-between mb-4 pb-4 border-b border-gray-300"):
                    ui.label("🎯 États Actifs - Suivi en Cours").classes("text-2xl font-bold")
                    ui.button(icon="close", on_click=states_modal.close).props("flat dense").classes("text-gray-500")
                
                # Statistiques globales (compactes)
                with ui.row().classes("w-full gap-4 mb-4"):
                    with ui.card().classes("flex-1 bg-blue-50").style("padding: 8px;"):
                        ui.label(f"{len(all_states)}").classes("text-xl font-bold text-blue-600")
                        ui.label("Total états").classes("text-xs text-gray-600")
                    
                    with ui.card().classes("flex-1 bg-orange-50").style("padding: 8px;"):
                        ui.label(f"{len(unresolved)}").classes("text-xl font-bold text-orange-600")
                        ui.label("En cours").classes("text-xs text-gray-600")
                    
                    with ui.card().classes("flex-1 bg-green-50").style("padding: 8px;"):
                        resolved_count = len([s for s in all_states if s.get("resolved", False)])
                        ui.label(f"{resolved_count}").classes("text-xl font-bold text-green-600")
                        ui.label("Résolus").classes("text-xs text-gray-600")
                
                # Filtres
                with ui.row().classes("w-full gap-4 mb-4"):
                    selected_category = ui.select(
                        label="Catégorie",
                        options=["Toutes", "santé", "projet", "humeur", "apprentissage", "technique", "personnel"],
                        value="Toutes"
                    ).classes("flex-1")
                    
                    selected_importance = ui.select(
                        label="Importance",
                        options=["Toutes", "high", "medium", "low"],
                        value="Toutes"
                    ).classes("flex-1")
                    
                    show_resolved = ui.checkbox("Afficher résolus", value=False)
                
                # Liste des états en grid 2 colonnes
                states_container = ui.element('div').classes("w-full overflow-y-auto").style(
                    "display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; max-height: 60vh; min-height: 400px;"
                )
                
                async def refresh_states_list():
                    """Rafraîchit la liste des états selon les filtres"""
                    nonlocal states_container
                    states_container.clear()
                    
                    # Filtrage
                    filtered_states = all_states.copy()
                    
                    # Filtre résolution
                    if not show_resolved.value:
                        filtered_states = [s for s in filtered_states if not s.get("resolved", False)]
                    
                    # Filtre catégorie
                    if selected_category.value != "Toutes":
                        filtered_states = [s for s in filtered_states if s.get("category") == selected_category.value]
                    
                    # Filtre importance
                    if selected_importance.value != "Toutes":
                        filtered_states = [s for s in filtered_states if s.get("importance") == selected_importance.value]
                    
                    # Affichage
                    with states_container:
                        if not filtered_states:
                            ui.label("Aucun état actif correspondant aux filtres").classes("text-gray-500 text-center p-8")
                        else:
                            for state in filtered_states:
                                await self._create_state_card(state, refresh_states_list)
                
                # Bind filtres
                selected_category.on_value_change(lambda: refresh_states_list())
                selected_importance.on_value_change(lambda: refresh_states_list())
                show_resolved.on_value_change(lambda: refresh_states_list())
                
                # Chargement initial
                await refresh_states_list()
            
            states_modal.open()
            
        except Exception as e:
            print(f"[JOURNAL-UI] ERROR Erreur modal états actifs: {e}")
            import traceback
            traceback.print_exc()
            ui.notify(f"Erreur états actifs: {e}", type="negative")
    
    async def _create_state_card(self, state: Dict[str, Any], refresh_callback: Callable):
        """Crée une carte pour un état actif"""
        state_id = state.get("state_id")
        category = state.get("category", "général")
        description = state.get("description", "")
        importance = state.get("importance", "medium")
        resolved = state.get("resolved", False)
        created_at = state.get("created_at", "")
        last_update = state.get("last_update", "")
        
        # Icônes catégories
        category_icons = {
            "santé": "🏥",
            "projet": "📋",
            "humeur": "💭",
            "apprentissage": "📚",
            "technique": "💻",
            "personnel": "🧑"
        }
        icon = category_icons.get(category, "📌")
        
        # Couleurs importance
        importance_colors = {
            "high": "border-red-500 bg-red-50",
            "medium": "border-orange-500 bg-orange-50",
            "low": "border-gray-500 bg-gray-50"
        }
        border_color = importance_colors.get(importance, "border-gray-500 bg-gray-50")
        
        # Card avec hauteur augmentée pour meilleure lisibilité en grid
        with ui.card().classes(f"w-full border-l-4 {border_color} {'opacity-50' if resolved else ''}").style("min-height: 180px; padding: 12px;"):
            with ui.row().classes("w-full items-start justify-between"):
                # Contenu principal
                with ui.column().classes("flex-1 gap-2"):
                    # Header
                    with ui.row().classes("items-center gap-2"):
                        ui.label(icon).classes("text-2xl")
                        ui.label(category.capitalize()).classes("font-bold text-lg")
                        
                        # Badge importance
                        if importance == "high":
                            ui.badge("IMPORTANT").classes("bg-red-500 text-white")
                        elif importance == "low":
                            ui.badge("info").classes("bg-gray-400 text-white")
                        
                        # Badge résolu
                        if resolved:
                            ui.badge("✅ Résolu").classes("bg-green-500 text-white")
                    
                    # Description
                    ui.label(description).classes("text-base mt-2")
                    
                    # Métadonnées
                    with ui.row().classes("gap-4 mt-3 text-xs text-gray-600"):
                        if created_at:
                            created_date = datetime.fromisoformat(created_at).strftime("%d/%m/%Y %H:%M")
                            ui.label(f"📅 Créé: {created_date}")
                        
                        if last_update:
                            update_date = datetime.fromisoformat(last_update).strftime("%d/%m/%Y %H:%M")
                            ui.label(f"🔄 MAJ: {update_date}")
                    
                    # Historique (si existe)
                    update_history = state.get("update_history", [])
                    if update_history:
                        with ui.expansion("Historique", icon="history").classes("w-full mt-2"):
                            with ui.column().classes("w-full gap-2 p-2").style("max-height: 300px; overflow-y: auto; min-height: 100px;"):
                                for i, update in enumerate(update_history[:5]):  # Max 5 derniers
                                    timestamp_hist = datetime.fromisoformat(update.get("timestamp", "")).strftime("%d/%m/%Y %H:%M")
                                    action = update.get("action", "")
                                    entry_id = update.get("entry_id", "")
                                    
                                    action_icons = {
                                        "created": "➕",
                                        "updated": "🔄",
                                        "resolved": "✅",
                                        "noted": "📝"
                                    }
                                    action_icon = action_icons.get(action, "•")
                                    
                                    ui.label(f"{action_icon} {timestamp_hist} - {action}").classes("text-xs text-gray-600")
                
                # Actions
                with ui.column().classes("gap-2"):
                    if not resolved:
                        ui.button(
                            icon="check_circle",
                            on_click=lambda sid=state_id: self._resolve_state(sid, refresh_callback)
                        ).props("flat dense").classes("text-green-600").tooltip("Marquer comme résolu")
                    
                    ui.button(
                        icon="info",
                        on_click=lambda s=state: self._show_state_details(s)
                    ).props("flat dense").classes("text-blue-600").tooltip("Détails complets")
    
    async def _resolve_state(self, state_id: int, refresh_callback: Callable):
        """Marque un état comme résolu"""
        try:
            # Dialog de confirmation
            with ui.dialog() as confirm_dialog, ui.card():
                ui.label("Marquer cet état comme résolu ?").classes("text-lg font-semibold mb-4")
                
                resolution_note = ui.input(
                    label="Note de résolution (optionnel)",
                    placeholder="Ex: Problème résolu, symptômes disparus..."
                ).classes("w-full mb-4")
                
                with ui.row().classes("w-full justify-end gap-2"):
                    ui.button("Annuler", on_click=confirm_dialog.close).props("flat")
                    
                    async def confirm_resolve():
                        success = self.json_manager.resolve_state(
                            state_id=state_id,
                            resolution_note=resolution_note.value or None
                        )
                        
                        if success:
                            ui.notify(f"✅ État résolu avec succès", type="positive")
                            confirm_dialog.close()
                            await refresh_callback()
                        else:
                            ui.notify("❌ Erreur résolution état", type="negative")
                    
                    ui.button("✅ Confirmer", on_click=confirm_resolve).classes("bg-green-600 text-white")
            
            confirm_dialog.open()
            
        except Exception as e:
            print(f"[JOURNAL-UI] ERROR Résolution état: {e}")
            ui.notify(f"Erreur: {e}", type="negative")
    
    def _show_state_details(self, state: Dict[str, Any]):
        """Affiche les détails complets d'un état"""
        try:
            with ui.dialog() as details_dialog, ui.card().classes("w-full").style("max-width: 800px;"):
                ui.label(f"Détails État #{state.get('state_id')}").classes("text-xl font-bold mb-4")
                
                # Affichage JSON structuré
                import json
                details_json = json.dumps(state, indent=2, ensure_ascii=False)
                
                ui.code(details_json).classes("w-full").style("max-height: 500px; overflow-y: auto;")
                
                ui.button("Fermer", on_click=details_dialog.close).classes("mt-4")
            
            details_dialog.open()
            
        except Exception as e:
            print(f"[JOURNAL-UI] ERROR Détails état: {e}")
    
    async def open_maintenance_modal(self):
        """Ouvre le modal de maintenance (Option C)"""
        try:
            print("[JOURNAL-UI] 🧹 Ouverture modal maintenance")
            
            # Vérifier disponibilité modules Option C
            try:
                from .purge_manager import get_purge_manager
                from .auto_resolution import detect_inactive_states, get_auto_resolution_stats
                from .scheduler import get_scheduler
            except ImportError as e:
                ui.notify(f"Modules maintenance non disponibles: {e}", type="warning")
                return
            
            purge_manager = get_purge_manager()
            scheduler = get_scheduler()
            
            # Création modal
            with ui.dialog() as maintenance_modal, ui.card().classes("w-full").style("width: 90vw; max-width: 1200px; max-height: 90vh;"):
                # Header
                with ui.row().classes("w-full items-center justify-between mb-4 pb-4 border-b border-gray-300"):
                    ui.label("🧹 Maintenance Journal v2.0").classes("text-2xl font-bold")
                    ui.button(icon="close", on_click=maintenance_modal.close).props("flat dense").classes("text-gray-500")
                
                # Tabs navigation
                with ui.tabs().classes("w-full") as tabs:
                    purge_tab = ui.tab("🗜️ Purge")
                    auto_resolve_tab = ui.tab("✅ Auto-Résolution")
                    config_tab = ui.tab("⚙️ Configuration")
                
                # Tabs content
                with ui.tab_panels(tabs, value=purge_tab).classes("w-full"):
                    # TAB 1: Purge manuelle
                    with ui.tab_panel(purge_tab):
                        await self._create_purge_tab(purge_manager)
                    
                    # TAB 2: Auto-résolution
                    with ui.tab_panel(auto_resolve_tab):
                        await self._create_auto_resolve_tab()
                    
                    # TAB 3: Configuration scheduler
                    with ui.tab_panel(config_tab):
                        await self._create_config_tab(scheduler)
            
            maintenance_modal.open()
            print("[JOURNAL-UI] OK Modal maintenance ouvert")
            
        except Exception as e:
            print(f"[JOURNAL-UI] ERROR Modal maintenance: {e}")
            import traceback
            traceback.print_exc()
            ui.notify(f"Erreur maintenance: {e}", type="negative")
    
    async def _create_purge_tab(self, purge_manager):
        """Onglet purge manuelle"""
        with ui.column().classes("w-full gap-4 p-4"):
            ui.label("Purge et Compression des Entrées Anciennes").classes("text-xl font-bold mb-2")
            ui.label("Compresse les entrées anciennes via résumé LLM et/ou archive dans FAISS").classes("text-sm text-gray-600 mb-4")
            
            # Configuration purge
            with ui.card().classes("w-full bg-gray-50"):
                ui.label("Configuration").classes("font-semibold mb-3")
                
                with ui.row().classes("w-full gap-4 items-end"):
                    age_input = ui.number(
                        label="Âge minimum (jours)",
                        value=90,
                        min=30,
                        max=365
                    ).classes("flex-1")
                    
                    mode_select = ui.select(
                        label="Mode",
                        options=["compress", "archive"],
                        value="compress"
                    ).classes("flex-1").tooltip("compress: Résumé LLM uniquement\narchive: Résumé + transfert FAISS")
                    
                    exclude_states = ui.checkbox("Exclure entrées avec états actifs", value=True).classes("mt-4")
            
            # Preview
            preview_container = ui.column().classes("w-full gap-2")
            
            with ui.row().classes("gap-2 mt-4"):
                async def run_preview():
                    preview_container.clear()
                    
                    if not purge_manager:
                        ui.notify("PurgeManager non disponible", type="warning")
                        return
                    
                    with preview_container:
                        ui.label("🔍 Analyse en cours...").classes("text-blue-600")
                    
                    # Récupérer entrées purgeable
                    entries = purge_manager.get_purgeable_entries(
                        age_days=int(age_input.value),
                        exclude_active_states=exclude_states.value
                    )
                    
                    preview_container.clear()
                    with preview_container:
                        if not entries:
                            ui.label("Aucune entrée éligible pour purge").classes("text-gray-500")
                        else:
                            ui.label(f"✅ {len(entries)} entrées détectées").classes("text-green-600 font-bold mb-2")
                            
                            # Statistiques
                            total_size = sum(e["size_bytes"] for e in entries)
                            compressed_count = sum(1 for e in entries if e["compressed"])
                            
                            with ui.row().classes("gap-4 mb-4"):
                                with ui.card().classes("flex-1 bg-blue-50"):
                                    ui.label(f"{len(entries)}").classes("text-2xl font-bold text-blue-600")
                                    ui.label("Entrées").classes("text-xs text-gray-600")
                                
                                with ui.card().classes("flex-1 bg-orange-50"):
                                    ui.label(f"{total_size // 1024} KB").classes("text-2xl font-bold text-orange-600")
                                    ui.label("Taille totale").classes("text-xs text-gray-600")
                                
                                with ui.card().classes("flex-1 bg-green-50"):
                                    ui.label(f"{compressed_count}").classes("text-2xl font-bold text-green-600")
                                    ui.label("Déjà compressées").classes("text-xs text-gray-600")
                            
                            # Liste preview (10 premières)
                            ui.label("Aperçu (10 premières):").classes("font-semibold mb-2")
                            for entry in entries[:10]:
                                with ui.card().classes("w-full bg-white border-l-4 border-gray-300"):
                                    with ui.row().classes("items-center justify-between"):
                                        ui.label(f"📅 {entry['date']}").classes("font-mono")
                                        ui.label(f"{entry['age_days']}j").classes("text-sm text-gray-500")
                                        if entry["compressed"]:
                                            ui.badge("Compressée").classes("bg-green-500")
                
                ui.button("🔍 Preview", on_click=run_preview).classes("bg-blue-600 text-white")
                
                async def run_purge():
                    if not purge_manager:
                        ui.notify("PurgeManager non disponible", type="warning")
                        return
                    
                    # Confirmation
                    with ui.dialog() as confirm_dialog, ui.card():
                        ui.label("⚠️ Confirmer la purge ?").classes("text-lg font-bold mb-2")
                        ui.label(f"Âge: {age_input.value}j | Mode: {mode_select.value}").classes("text-sm mb-4")
                        ui.label("Cette action est irréversible (sauf backup automatique)").classes("text-xs text-red-600 mb-4")
                        
                        with ui.row().classes("gap-2"):
                            ui.button("Annuler", on_click=confirm_dialog.close).props("flat")
                            
                            async def confirm():
                                confirm_dialog.close()
                                ui.notify("🗜️ Purge en cours...", type="info")
                                
                                stats = purge_manager.purge_old_entries(
                                    age_days=int(age_input.value),
                                    mode=mode_select.value,
                                    dry_run=False
                                )
                                
                                ui.notify(f"✅ Purge terminée: {stats.get('compressed', 0)} compressées, "
                                         f"{stats.get('archived', 0)} archivées", type="positive")
                                
                                # Rafraîchir preview
                                await run_preview()
                            
                            ui.button("✅ Confirmer Purge", on_click=confirm).classes("bg-red-600 text-white")
                    
                    confirm_dialog.open()
                
                ui.button("🗜️ Lancer Purge", on_click=run_purge).classes("bg-red-600 text-white")
    
    async def _create_auto_resolve_tab(self):
        """Onglet auto-résolution états inactifs"""
        from .auto_resolution import detect_inactive_states, auto_resolve_states, get_auto_resolution_stats
        
        with ui.column().classes("w-full gap-4 p-4"):
            ui.label("Auto-Résolution États Actifs Inactifs").classes("text-xl font-bold mb-2")
            ui.label("Résout automatiquement les états non mis à jour depuis longtemps").classes("text-sm text-gray-600 mb-4")
            
            # Configuration
            with ui.card().classes("w-full bg-gray-50"):
                ui.label("Configuration").classes("font-semibold mb-3")
                
                with ui.row().classes("w-full gap-4 items-end"):
                    threshold_input = ui.number(
                        label="Inactivité minimum (jours)",
                        value=30,
                        min=7,
                        max=180
                    ).classes("flex-1")
                    
                    exclude_high = ui.checkbox("Exclure importance HIGH", value=True).classes("mt-4")
                    llm_validation = ui.checkbox("Validation LLM (Archiviste)", value=True).classes("mt-4")
            
            # Stats et détection
            stats_container = ui.column().classes("w-full gap-2")
            states_container = ui.column().classes("w-full gap-2")
            
            with ui.row().classes("gap-2 mt-4"):
                async def run_detection():
                    stats_container.clear()
                    states_container.clear()
                    
                    with stats_container:
                        ui.label("🔍 Détection en cours...").classes("text-blue-600")
                    
                    # Détecter états inactifs
                    inactive = detect_inactive_states(
                        json_manager=self.json_manager,
                        threshold_days=int(threshold_input.value),
                        exclude_high_importance=exclude_high.value
                    )
                    
                    stats_container.clear()
                    with stats_container:
                        if not inactive:
                            ui.label("Aucun état inactif détecté").classes("text-gray-500")
                        else:
                            ui.label(f"✅ {len(inactive)} états inactifs détectés").classes("text-orange-600 font-bold mb-4")
                            
                            # Stats par catégorie
                            from collections import Counter
                            by_category = Counter(s["category"] for s in inactive)
                            
                            with ui.row().classes("gap-2 mb-4"):
                                for cat, count in by_category.items():
                                    ui.badge(f"{cat}: {count}").classes("bg-orange-100 text-orange-800")
                    
                    # Afficher liste états
                    states_container.clear()
                    with states_container:
                        if inactive:
                            ui.label("États détectés:").classes("font-semibold mb-2")
                            for state in inactive:
                                with ui.card().classes("w-full border-l-4 border-orange-400"):
                                    with ui.row().classes("items-start justify-between"):
                                        with ui.column().classes("flex-1"):
                                            ui.label(state["description"]).classes("font-semibold")
                                            ui.label(f"Catégorie: {state['category']} | Importance: {state['importance']}").classes("text-xs text-gray-600")
                                            ui.label(f"Inactif depuis: {state['days_inactive']} jours").classes("text-xs text-orange-600")
                
                ui.button("🔍 Détecter", on_click=run_detection).classes("bg-blue-600 text-white")
                
                async def run_auto_resolve():
                    # Récupérer archiviste
                    archiviste = self.core_journal.archiviste_controller if hasattr(self.core_journal, 'archiviste_controller') else None
                    
                    if not archiviste and llm_validation.value:
                        ui.notify("Archiviste non disponible pour validation LLM", type="warning")
                        return
                    
                    # Confirmation
                    with ui.dialog() as confirm_dialog, ui.card():
                        ui.label("⚠️ Confirmer l'auto-résolution ?").classes("text-lg font-bold mb-2")
                        ui.label(f"Seuil: {threshold_input.value}j | Validation LLM: {llm_validation.value}").classes("text-sm mb-4")
                        
                        with ui.row().classes("gap-2"):
                            ui.button("Annuler", on_click=confirm_dialog.close).props("flat")
                            
                            async def confirm():
                                confirm_dialog.close()
                                ui.notify("✅ Auto-résolution en cours...", type="info")
                                
                                stats = auto_resolve_states(
                                    json_manager=self.json_manager,
                                    archiviste_controller=archiviste,
                                    threshold_days=int(threshold_input.value),
                                    dry_run=False,
                                    require_llm_validation=llm_validation.value
                                )
                                
                                ui.notify(f"✅ Terminé: {stats.get('resolved', 0)} résolus, "
                                         f"{stats.get('rejected', 0)} rejetés", type="positive")
                                
                                # Rafraîchir détection
                                await run_detection()
                            
                            ui.button("✅ Confirmer", on_click=confirm).classes("bg-green-600 text-white")
                    
                    confirm_dialog.open()
                
                ui.button("✅ Auto-Résoudre", on_click=run_auto_resolve).classes("bg-green-600 text-white")
    
    async def _create_config_tab(self, scheduler):
        """Onglet configuration scheduler"""
        with ui.column().classes("w-full gap-4 p-4"):
            ui.label("Configuration Maintenance Automatique").classes("text-xl font-bold mb-2")
            ui.label("Planification hebdomadaire de la maintenance").classes("text-sm text-gray-600 mb-4")
            
            if not scheduler:
                ui.label("⚠️ Scheduler non initialisé").classes("text-red-600 font-bold")
                ui.label("Relancez OGMA pour activer le scheduler").classes("text-sm text-gray-500")
                return
            
            config = scheduler.config
            
            # Statut scheduler
            with ui.card().classes("w-full bg-blue-50 mb-4"):
                status = scheduler.get_status()
                
                with ui.row().classes("items-center gap-4"):
                    if status["is_running"]:
                        ui.icon("check_circle", size="32px").classes("text-green-600")
                        ui.label("Scheduler actif").classes("text-lg font-bold text-green-600")
                    else:
                        ui.icon("cancel", size="32px").classes("text-gray-400")
                        ui.label("Scheduler inactif").classes("text-lg font-bold text-gray-600")
                
                if config.get("last_maintenance"):
                    last_maint = datetime.fromisoformat(config["last_maintenance"]).strftime("%d/%m/%Y %H:%M")
                    ui.label(f"Dernière maintenance: {last_maint}").classes("text-sm text-gray-600 mt-2")
            
            # Configuration
            with ui.card().classes("w-full"):
                ui.label("Paramètres").classes("font-semibold mb-3")
                
                auto_purge_enabled = ui.checkbox(
                    "Activer purge automatique",
                    value=config.get("auto_purge_enabled", False)
                ).classes("mb-2")
                
                purge_age = ui.number(
                    label="Âge purge (jours)",
                    value=config.get("purge_age_days", 90),
                    min=30,
                    max=365
                ).classes("w-full mb-2")
                
                auto_resolve_enabled = ui.checkbox(
                    "Activer auto-résolution",
                    value=config.get("auto_resolve_enabled", False)
                ).classes("mb-2")
                
                resolve_threshold = ui.number(
                    label="Seuil inactivité (jours)",
                    value=config.get("resolve_threshold_days", 30),
                    min=7,
                    max=180
                ).classes("w-full mb-2")
                
                maintenance_interval = ui.number(
                    label="Intervalle maintenance (jours)",
                    value=config.get("maintenance_interval_days", 7),
                    min=1,
                    max=30
                ).classes("w-full mb-2")
                
                require_llm = ui.checkbox(
                    "Validation LLM pour auto-résolution",
                    value=config.get("require_llm_validation", True)
                )
            
            # Actions
            with ui.row().classes("gap-2 mt-4"):
                def save_config():
                    success = scheduler.update_config(
                        auto_purge_enabled=auto_purge_enabled.value,
                        purge_age_days=int(purge_age.value),
                        auto_resolve_enabled=auto_resolve_enabled.value,
                        resolve_threshold_days=int(resolve_threshold.value),
                        maintenance_interval_days=int(maintenance_interval.value),
                        require_llm_validation=require_llm.value
                    )
                    
                    if success:
                        ui.notify("✅ Configuration sauvegardée", type="positive")
                    else:
                        ui.notify("❌ Erreur sauvegarde", type="negative")
                
                ui.button("💾 Sauvegarder", on_click=save_config).classes("bg-blue-600 text-white")
                
                def toggle_scheduler():
                    if scheduler._is_running:
                        scheduler.stop()
                        ui.notify("🛑 Scheduler arrêté", type="info")
                    else:
                        scheduler.start()
                        ui.notify("✅ Scheduler démarré", type="positive")
                
                ui.button("▶️ Toggle Scheduler", on_click=toggle_scheduler).classes("bg-green-600 text-white")
                
                async def run_manual():
                    ui.notify("🧹 Maintenance manuelle en cours...", type="info")
                    
                    stats = scheduler.run_maintenance_now(dry_run=False)
                    
                    ui.notify(f"✅ Terminé: {stats.get('auto_resolution', {}).get('resolved', 0)} résolus, "
                             f"{stats.get('purge', {}).get('compressed', 0)} compressées", type="positive")
                
                ui.button("🧹 Exécuter Maintenant", on_click=run_manual).classes("bg-orange-600 text-white")
    
    def cleanup(self):
        """Nettoyage des ressources UI"""
        try:
            if self.main_modal:
                self.main_modal.close()
                self.main_modal = None

            # Reset état
            self.header_button = None
            self.calendar_component = None
            self.entries_panel = None
            self.detail_panel = None

            print("[JOURNAL-UI] OK Interface nettoyée")

        except Exception as e:
            print(f"[JOURNAL-UI] WARN Erreur cleanup: {e}")


# Fonctions utilitaires pour intégration

def create_journal_ui(config, core_journal, json_manager) -> JournalUI:
    """
    Factory function pour créer une instance JournalUI

    Args:
        config: Configuration extension
        core_journal: Instance JournalCore
        json_manager: Instance JSONManager

    Returns:
        JournalUI: Instance interface utilisateur
    """
    return JournalUI(config, core_journal, json_manager)

def inject_journal_styles():
    """Injecte les styles CSS spécifiques au journal"""
    try:
        # Styles CSS pour le journal intégrés à OGMA
        styles = """
        .journal-header-button {
            transition: all 0.2s ease;
        }

        .journal-header-button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(139, 90, 43, 0.3);
        }

        .journal-entry-card {
            transition: box-shadow 0.2s ease;
        }

        .journal-entry-card:hover {
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }
        """

        ui.add_head_html(f"<style>{styles}</style>")
        print("[JOURNAL-UI] OK Styles CSS injectés")

    except Exception as e:
        print(f"[JOURNAL-UI] WARN Erreur injection styles: {e}")