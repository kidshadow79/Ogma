# JOURNAL Extension Journal de Bord - Visualiseur Calendrier

"""
Composant calendrier pour navigation temporelle dans le journal
Calendrier graphique, indicateurs d'activité, navigation fluide
"""

from typing import Dict, Any, List, Optional, Callable, Tuple
from datetime import datetime, date, timedelta
import calendar

try:
    import importlib
    _ng = importlib.import_module('nicegui')
    _ui = getattr(_ng, 'ui', None)
except Exception:
    _ui = None

class _Dummy:
    def __getattr__(self, name):
        return self
    def __call__(self, *args, **kwargs):
        return self
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False

ui: Any = _ui if _ui is not None else _Dummy()


class CalendarViewer:
    """
    Visualiseur calendrier pour navigation temporelle dans le journal

    Responsabilités:
    - Affichage calendrier mensuel/annuel graphique
    - Indicateurs visuels d'activité par jour
    - Navigation fluide entre mois/années
    - Sélection de date avec feedback visuel
    - Intégration avec données journal
    """

    def __init__(self, json_manager, config):
        """Initialise le visualiseur calendrier"""
        self.json_manager = json_manager
        self.config = config

        # État calendrier
        self.current_month = datetime.now().month
        self.current_year = datetime.now().year
        self.selected_date = date.today()
        self.view_mode = "month"  # "month", "year"

        # Cache données calendrier
        self.activity_cache = {}
        self.cache_expiry = {}

        # Composants UI
        self.calendar_container = None
        self.navigation_bar = None
        self.day_buttons = {}

        # Callbacks
        self.on_date_selected = None
        self.on_month_changed = None
        self.on_activity_hover = None

        print(f"[CALENDAR-VIEWER] OK Initialisé (mois: {self.current_month}/{self.current_year})")

    async def create_calendar_widget(self, container):
        """
        Crée le widget calendrier dans le container spécifié

        Args:
            container: Container NiceGUI parent
        """
        try:
            with container:
                # Barre de navigation
                await self._create_navigation_bar()

                # Zone calendrier principal
                self.calendar_container = ui.column().classes("w-full")
                await self._render_current_view()

            print("[CALENDAR-VIEWER] OK Widget calendrier créé")

        except Exception as e:
            print(f"[CALENDAR-VIEWER] ERROR Erreur création widget: {e}")
            raise

    async def _create_navigation_bar(self):
        """Crée la barre de navigation du calendrier"""
        with ui.row().classes("w-full items-center justify-between mb-4"):
            # Navigation gauche
            with ui.row().classes("gap-1"):
                ui.button(
                    "‹‹",
                    on_click=self._prev_year
                ).classes("bg-gray-200 hover:bg-gray-300 text-gray-700").props('dense')

                ui.button(
                    "‹",
                    on_click=self._prev_month
                ).classes("bg-gray-200 hover:bg-gray-300 text-gray-700").props('dense')

            # Affichage mois/année central
            self.month_year_label = ui.label().classes("text-lg font-semibold text-center flex-1")
            await self._update_month_year_label()

            # Navigation droite
            with ui.row().classes("gap-1"):
                ui.button(
                    "›",
                    on_click=self._next_month
                ).classes("bg-gray-200 hover:bg-gray-300 text-gray-700").props('dense')

                ui.button(
                    "››",
                    on_click=self._next_year
                ).classes("bg-gray-200 hover:bg-gray-300 text-gray-700").props('dense')

            # Toggle vue mois/année
            ui.button(
                "📅",
                on_click=self._toggle_view_mode
            ).classes("bg-blue-500 hover:bg-blue-600 text-white").props('dense')

    async def _update_month_year_label(self):
        """Met à jour le label mois/année"""
        if self.view_mode == "month":
            month_name = calendar.month_name[self.current_month]
            self.month_year_label.text = f"{month_name} {self.current_year}"
        else:
            self.month_year_label.text = f"Année {self.current_year}"

    async def _render_current_view(self):
        """Rend la vue calendrier actuelle"""
        try:
            # Effacer contenu précédent
            self.calendar_container.clear()

            if self.view_mode == "month":
                await self._render_month_view()
            else:
                await self._render_year_view()

            print(f"[CALENDAR-VIEWER] OK Vue {self.view_mode} rendue")

        except Exception as e:
            print(f"[CALENDAR-VIEWER] ERROR Erreur rendu vue: {e}")

    async def _render_month_view(self):
        """Rend la vue calendrier mensuel"""
        with self.calendar_container:
            # Charger données d'activité pour le mois
            await self._load_month_activity()

            # En-têtes jours de la semaine
            with ui.row().classes("w-full gap-0 mb-2"):
                for day_name in ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]:
                    ui.label(day_name).classes(
                        "flex-1 text-center text-sm font-medium text-gray-600 py-2"
                    )

            # Grille du calendrier
            cal = calendar.monthcalendar(self.current_year, self.current_month)

            for week in cal:
                with ui.row().classes("w-full gap-0 mb-1"):
                    for day in week:
                        if day == 0:
                            # Jour vide (autre mois)
                            ui.label("").classes("flex-1 h-10")
                        else:
                            await self._create_day_button(day)

    async def _create_day_button(self, day: int):
        """Crée un bouton jour avec indicateurs d'activité"""
        try:
            # Date du jour
            day_date = date(self.current_year, self.current_month, day)
            date_str = day_date.strftime("%Y-%m-%d")

            # Données d'activité
            activity = self.activity_cache.get(date_str, {})
            entry_count = activity.get("entry_count", 0)
            importance_level = activity.get("max_importance", "normal")

            # Style selon activité et sélection
            classes = "flex-1 h-10 text-sm transition-all duration-200 "

            if day_date == self.selected_date:
                # Jour sélectionné
                classes += "bg-orange-500 text-white font-bold "
            elif day_date == date.today():
                # Aujourd'hui
                classes += "bg-blue-500 text-white font-medium "
            elif entry_count > 0:
                # Jour avec activité
                if importance_level == "critical":
                    classes += "bg-red-100 text-red-800 hover:bg-red-200 "
                elif importance_level == "high":
                    classes += "bg-orange-100 text-orange-800 hover:bg-orange-200 "
                else:
                    classes += "bg-green-100 text-green-800 hover:bg-green-200 "
            else:
                # Jour sans activité
                classes += "bg-gray-50 text-gray-600 hover:bg-gray-100 "

            # Création du bouton
            day_button = ui.button(
                str(day),
                on_click=lambda d=day_date: self._on_day_click(d)
            ).classes(classes)

            # Tooltip avec détails activité
            if entry_count > 0:
                tooltip_text = f"{entry_count} entrée(s)"
                if importance_level != "normal":
                    tooltip_text += f" (niveau: {importance_level})"
            else:
                tooltip_text = "Aucune entrée"

            with day_button:
                ui.tooltip(tooltip_text)

            # Badge compteur si plusieurs entrées
            if entry_count > 1:
                with day_button:
                    ui.badge(str(entry_count)).classes(
                        "absolute -top-1 -right-1 bg-red-500 text-white text-xs"
                    ).style("font-size: 10px; min-width: 16px; height: 16px;")

            # Stocker référence
            self.day_buttons[date_str] = day_button

        except Exception as e:
            print(f"[CALENDAR-VIEWER] ERROR Erreur création bouton jour {day}: {e}")

    async def _render_year_view(self):
        """Rend la vue calendrier annuel (12 mois)"""
        with self.calendar_container:
            # Charger données d'activité pour l'année
            await self._load_year_activity()

            # Grille 3x4 pour les 12 mois
            for quarter in range(4):
                with ui.row().classes("w-full gap-4 mb-4"):
                    for month_offset in range(3):
                        month_num = quarter * 3 + month_offset + 1
                        await self._create_month_mini_calendar(month_num)

    async def _create_month_mini_calendar(self, month_num: int):
        """Crée un mini calendrier pour la vue annuelle"""
        month_name = calendar.month_abbr[month_num]

        with ui.card().classes("flex-1 p-2 cursor-pointer hover:shadow-md").on(
            'click', lambda m=month_num: self._on_month_click(m)
        ):
            # Header mois
            ui.label(f"{month_name} {self.current_year}").classes(
                "text-sm font-medium text-center mb-2"
            )

            # Mini grille (simplifié)
            cal = calendar.monthcalendar(self.current_year, month_num)
            total_entries = 0

            with ui.column().classes("gap-0"):
                for week in cal[:4]:  # Premières 4 semaines seulement
                    with ui.row().classes("gap-0"):
                        for day in week:
                            if day > 0:
                                day_date = date(self.current_year, month_num, day)
                                date_str = day_date.strftime("%Y-%m-%d")
                                activity = self.activity_cache.get(date_str, {})
                                entry_count = activity.get("entry_count", 0)
                                total_entries += entry_count

                                # Petit indicateur coloré
                                if entry_count > 0:
                                    color = "bg-orange-400"
                                elif day_date == date.today():
                                    color = "bg-blue-400"
                                else:
                                    color = "bg-gray-200"

                                ui.label("•").classes(f"text-xs {color} w-3 h-3 rounded-full")
                            else:
                                ui.label("").classes("w-3 h-3")

            # Compteur total entrées du mois
            if total_entries > 0:
                ui.badge(f"{total_entries}").classes("bg-orange-500 text-white text-xs")

    async def _load_month_activity(self):
        """Charge les données d'activité pour le mois actuel"""
        try:
            cache_key = f"{self.current_year}-{self.current_month:02d}"

            # Vérifier cache
            if cache_key in self.activity_cache and cache_key in self.cache_expiry:
                if datetime.now() < self.cache_expiry[cache_key]:
                    return  # Cache valide

            print(f"[CALENDAR-VIEWER] STATS Chargement activité mois {cache_key}")

            # Charger données depuis json_manager
            month_start = date(self.current_year, self.current_month, 1)
            if self.current_month == 12:
                month_end = date(self.current_year + 1, 1, 1) - timedelta(days=1)
            else:
                month_end = date(self.current_year, self.current_month + 1, 1) - timedelta(days=1)

            # Parcourir chaque jour du mois
            current_date = month_start
            while current_date <= month_end:
                date_str = current_date.strftime("%Y-%m-%d")

                # Récupérer entrées du jour
                entries = self.json_manager.get_day_entries(date_str)
                entry_count = len(entries) if entries else 0

                # Déterminer niveau d'importance max
                max_importance = "normal"
                if entries:
                    importance_levels = {"low": 1, "normal": 2, "high": 3, "critical": 4}
                    max_level = max(
                        importance_levels.get(entry.get("importance", "normal"), 2)
                        for entry in entries
                    )
                    max_importance = next(
                        level for level, value in importance_levels.items()
                        if value == max_level
                    )

                # Stocker dans cache
                self.activity_cache[date_str] = {
                    "entry_count": entry_count,
                    "max_importance": max_importance,
                    "entries": entries[:3] if entries else []  # Preview 3 entrées max
                }

                current_date += timedelta(days=1)

            # Cache valide 5 minutes
            self.cache_expiry[cache_key] = datetime.now() + timedelta(minutes=5)

            print(f"[CALENDAR-VIEWER] OK Activité mois {cache_key} chargée")

        except Exception as e:
            print(f"[CALENDAR-VIEWER] ERROR Erreur chargement activité mois: {e}")

    async def _load_year_activity(self):
        """Charge les données d'activité pour l'année actuelle"""
        try:
            cache_key = f"year-{self.current_year}"

            # Vérifier cache
            if cache_key in self.activity_cache and cache_key in self.cache_expiry:
                if datetime.now() < self.cache_expiry[cache_key]:
                    return

            print(f"[CALENDAR-VIEWER] STATS Chargement activité année {self.current_year}")

            # Charger statistiques par mois
            for month in range(1, 13):
                # Simuler chargement rapide par mois
                month_start = date(self.current_year, month, 1)
                if month == 12:
                    month_end = date(self.current_year + 1, 1, 1) - timedelta(days=1)
                else:
                    month_end = date(self.current_year, month + 1, 1) - timedelta(days=1)

                # Échantillonnage rapide (pas tous les jours)
                sample_dates = []
                current_date = month_start
                while current_date <= month_end:
                    sample_dates.append(current_date.strftime("%Y-%m-%d"))
                    current_date += timedelta(days=3)  # Échantillon tous les 3 jours

                # Charger échantillon
                for date_str in sample_dates:
                    if date_str not in self.activity_cache:
                        entries = self.json_manager.get_day_entries(date_str)
                        self.activity_cache[date_str] = {
                            "entry_count": len(entries) if entries else 0,
                            "max_importance": "normal",
                            "entries": []
                        }

            # Cache valide 10 minutes
            self.cache_expiry[cache_key] = datetime.now() + timedelta(minutes=10)

            print(f"[CALENDAR-VIEWER] OK Activité année {self.current_year} chargée")

        except Exception as e:
            print(f"[CALENDAR-VIEWER] ERROR Erreur chargement activité année: {e}")

    def _on_day_click(self, clicked_date: date):
        """Gestionnaire clic sur un jour"""
        try:
            print(f"[CALENDAR-VIEWER] 📅 Jour sélectionné: {clicked_date}")

            # Mettre à jour sélection
            old_date = self.selected_date
            self.selected_date = clicked_date

            # Actualiser affichage (re-render boutons)
            asyncio.create_task(self._update_day_buttons_style())

            # Callback externe
            if self.on_date_selected:
                self.on_date_selected(clicked_date.strftime("%Y-%m-%d"))

        except Exception as e:
            print(f"[CALENDAR-VIEWER] ERROR Erreur clic jour: {e}")

    def _on_month_click(self, month_num: int):
        """Gestionnaire clic sur un mois (vue année)"""
        try:
            print(f"[CALENDAR-VIEWER] 📅 Mois sélectionné: {month_num}")

            # Passer en vue mois
            self.current_month = month_num
            self.view_mode = "month"

            # Re-render
            asyncio.create_task(self._render_current_view())
            asyncio.create_task(self._update_month_year_label())

            # Callback externe
            if self.on_month_changed:
                self.on_month_changed(self.current_year, month_num)

        except Exception as e:
            print(f"[CALENDAR-VIEWER] ERROR Erreur clic mois: {e}")

    async def _update_day_buttons_style(self):
        """Met à jour le style des boutons jours après changement sélection"""
        # Cette méthode sera appelée après changement de sélection
        # Pour le moment, on re-render la vue complète
        await self._render_current_view()

    def _prev_month(self):
        """Navigation mois précédent"""
        try:
            if self.current_month == 1:
                self.current_month = 12
                self.current_year -= 1
            else:
                self.current_month -= 1

            asyncio.create_task(self._refresh_view())

        except Exception as e:
            print(f"[CALENDAR-VIEWER] ERROR Erreur navigation mois précédent: {e}")

    def _next_month(self):
        """Navigation mois suivant"""
        try:
            if self.current_month == 12:
                self.current_month = 1
                self.current_year += 1
            else:
                self.current_month += 1

            asyncio.create_task(self._refresh_view())

        except Exception as e:
            print(f"[CALENDAR-VIEWER] ERROR Erreur navigation mois suivant: {e}")

    def _prev_year(self):
        """Navigation année précédente"""
        try:
            self.current_year -= 1
            asyncio.create_task(self._refresh_view())

        except Exception as e:
            print(f"[CALENDAR-VIEWER] ERROR Erreur navigation année précédente: {e}")

    def _next_year(self):
        """Navigation année suivante"""
        try:
            self.current_year += 1
            asyncio.create_task(self._refresh_view())

        except Exception as e:
            print(f"[CALENDAR-VIEWER] ERROR Erreur navigation année suivante: {e}")

    def _toggle_view_mode(self):
        """Bascule entre vue mois et vue année"""
        try:
            self.view_mode = "year" if self.view_mode == "month" else "month"
            print(f"[CALENDAR-VIEWER] UPDATE Basculement vue: {self.view_mode}")

            asyncio.create_task(self._refresh_view())

        except Exception as e:
            print(f"[CALENDAR-VIEWER] ERROR Erreur basculement vue: {e}")

    async def _refresh_view(self):
        """Actualise la vue calendrier"""
        try:
            await self._update_month_year_label()
            await self._render_current_view()

            # Callback externe
            if self.on_month_changed:
                self.on_month_changed(self.current_year, self.current_month)

        except Exception as e:
            print(f"[CALENDAR-VIEWER] ERROR Erreur actualisation vue: {e}")

    def navigate_to_date(self, target_date: date):
        """
        Navigue vers une date spécifique

        Args:
            target_date: Date cible
        """
        try:
            print(f"[CALENDAR-VIEWER] TARGET Navigation vers: {target_date}")

            # Mettre à jour mois/année
            self.current_year = target_date.year
            self.current_month = target_date.month
            self.selected_date = target_date
            self.view_mode = "month"  # Forcer vue mois

            # Actualiser
            asyncio.create_task(self._refresh_view())

        except Exception as e:
            print(f"[CALENDAR-VIEWER] ERROR Erreur navigation vers date: {e}")

    def navigate_to_today(self):
        """Navigue vers aujourd'hui"""
        self.navigate_to_date(date.today())

    def get_selected_date(self) -> str:
        """Retourne la date sélectionnée au format ISO"""
        return self.selected_date.strftime("%Y-%m-%d")

    def get_current_period(self) -> Tuple[int, int]:
        """Retourne la période actuelle (année, mois)"""
        return (self.current_year, self.current_month)

    def set_callbacks(self, **callbacks):
        """Configure les callbacks d'événements calendrier"""
        for callback_name, callback_func in callbacks.items():
            if hasattr(self, callback_name):
                setattr(self, callback_name, callback_func)
                print(f"[CALENDAR-VIEWER] OK Callback {callback_name} configuré")

    def clear_cache(self):
        """Vide le cache d'activité (force rechargement)"""
        self.activity_cache.clear()
        self.cache_expiry.clear()
        print("[CALENDAR-VIEWER] UPDATE Cache activité vidé")

    def get_month_stats(self) -> Dict[str, Any]:
        """Retourne les statistiques du mois actuel"""
        try:
            total_entries = 0
            days_with_entries = 0
            importance_counts = {"low": 0, "normal": 0, "high": 0, "critical": 0}

            # Parcourir cache du mois
            for date_str, activity in self.activity_cache.items():
                if date_str.startswith(f"{self.current_year}-{self.current_month:02d}"):
                    entry_count = activity.get("entry_count", 0)
                    if entry_count > 0:
                        total_entries += entry_count
                        days_with_entries += 1
                        importance = activity.get("max_importance", "normal")
                        importance_counts[importance] += 1

            return {
                "total_entries": total_entries,
                "days_with_entries": days_with_entries,
                "total_days": calendar.monthrange(self.current_year, self.current_month)[1],
                "importance_distribution": importance_counts,
                "activity_rate": days_with_entries / calendar.monthrange(self.current_year, self.current_month)[1]
            }

        except Exception as e:
            print(f"[CALENDAR-VIEWER] ERROR Erreur calcul stats mois: {e}")
            return {}


# Fonctions utilitaires

def create_calendar_viewer(json_manager, config) -> CalendarViewer:
    """
    Factory function pour créer une instance CalendarViewer

    Args:
        json_manager: Instance JSONManager
        config: Configuration extension

    Returns:
        CalendarViewer: Instance visualiseur calendrier
    """
    return CalendarViewer(json_manager, config)

def get_activity_color(entry_count: int, importance: str) -> str:
    """
    Retourne la couleur appropriée selon l'activité

    Args:
        entry_count: Nombre d'entrées
        importance: Niveau d'importance max

    Returns:
        str: Classe CSS de couleur
    """
    if entry_count == 0:
        return "bg-gray-100"
    elif importance == "critical":
        return "bg-red-200"
    elif importance == "high":
        return "bg-orange-200"
    else:
        return "bg-green-200"