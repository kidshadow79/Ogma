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
                # Bouton journal avec style OGMA cohérent
                self.header_button = ui.button(
                    "JOURNAL Journal",
                    on_click=self._on_header_button_click
                ).classes(
                    "journal-header-button bg-orange-600 hover:bg-orange-700 "
                    "text-white font-medium px-3 py-2 rounded-md transition-all "
                    "duration-200 shadow-sm hover:shadow-md"
                ).props('dense').style(
                    "font-size: 14px; "
                    "background: linear-gradient(135deg, #8B5A2B 0%, #CD853F 100%); "
                    "border: 1px solid #A0522D;"
                )

                # Tooltip explicatif
                with self.header_button:
                    ui.tooltip("Journal de Bord - Capturer et consulter vos conversations")

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

        except Exception as e:
            print(f"[JOURNAL-UI] ERROR Erreur affichage détail: {e}")

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

            # Création via core_journal
            entry = await self.core_journal.create_entry_from_conversation()

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