# JOURNAL Extension Journal de Bord - Fournisseur de Contexte

"""
Fournisseur de contexte journalier pour injection en début de conversation
Formatage intelligent, sélection des entrées pertinentes, performance optimisée
"""

from datetime import datetime, date, timedelta
from typing import Dict, Any, List, Optional
import re

class ContextProvider:
    """
    Fournisseur de contexte journalier pour enrichir les conversations
    
    Responsabilités:
    - Récupération des entrées du jour courant
    - Formatage intelligent du contexte selon les préférences
    - Sélection des entrées les plus pertinentes
    - Génération de contexte adaptatif selon l'historique
    - Performance optimisée pour injection rapide
    
    Performance:
    - Génération contexte: <20ms
    - Cache intelligent pour éviter re-calculs
    - Formatage adaptatif selon volume d'entrées
    """
    
    def __init__(self, json_manager, config):
        """Initialise le fournisseur de contexte"""
        self.json_manager = json_manager
        self.config = config
        
        # Paramètres de contexte
        self.context_settings = self.config.get_context_settings()
        self.auto_display = self.context_settings["auto_display"]
        self.max_entries = self.context_settings["max_entries"]
        self.format_style = self.context_settings["format"]
        self.position = self.context_settings["position"]
        
        # Templates de formatage
        self.format_templates = {
            "minimal": self._get_minimal_template(),
            "summary": self._get_summary_template(),
            "detailed": self._get_detailed_template()
        }
        
        # Cache pour éviter re-calculs
        self.context_cache = {}
        self.cache_timestamps = {}
        self.cache_duration = 300  # 5 minutes
        
        print(f"[CONTEXT-PROVIDER] OK Initialisé (format: {self.format_style}, max_entries: {self.max_entries})")
    
    def get_daily_context(self, target_date: str = None, max_entries: int = None) -> str:
        """
        Génère le contexte journalier pour injection en conversation
        
        Args:
            target_date: Date cible (défaut: aujourd'hui) au format YYYY-MM-DD
            max_entries: Nombre max d'entrées (défaut: config)
        
        Returns:
            str: Contexte formaté prêt pour injection ou chaîne vide
        """
        if not self.auto_display:
            return ""
        
        try:
            # Date par défaut = aujourd'hui
            if not target_date:
                target_date = date.today().isoformat()
            
            # Limite d'entrées
            entry_limit = max_entries or self.max_entries
            
            # Vérification cache
            cache_key = f"{target_date}_{entry_limit}_{self.format_style}"
            if self._is_cache_valid(cache_key):
                return self.context_cache[cache_key]
            
            # Récupération des entrées du jour
            day_entries = self.json_manager.get_day_entries(target_date)
            
            if not day_entries:
                context = self._format_no_entries_context(target_date)
            else:
                # Sélection des entrées les plus pertinentes
                selected_entries = self._select_relevant_entries(day_entries, entry_limit)
                
                # Formatage selon le style configuré
                context = self._format_entries_context(selected_entries, target_date)
            
            # Mise en cache
            self._cache_context(cache_key, context)
            
            return context
            
        except Exception as e:
            print(f"[CONTEXT-PROVIDER] ERROR Erreur génération contexte: {e}")
            return ""
    
    def get_context_preview(self, target_date: str) -> Dict[str, Any]:
        """
        Génère un aperçu du contexte pour l'interface utilisateur
        
        Args:
            target_date: Date au format YYYY-MM-DD
        
        Returns:
            Dict: Aperçu avec métadonnées (count, tags, importance, etc.)
        """
        try:
            day_entries = self.json_manager.get_day_entries(target_date)
            
            if not day_entries:
                return {
                    "date": target_date,
                    "entry_count": 0,
                    "has_context": False,
                    "preview": "Aucune entrée pour cette date",
                    "tags": [],
                    "importance_levels": []
                }
            
            # Analyse des entrées
            all_tags = set()
            importance_levels = []
            total_tokens = 0
            
            for entry in day_entries:
                all_tags.update(entry.get("tags", []))
                importance_levels.append(entry.get("importance", "normal"))
                total_tokens += entry.get("tokens", 0)
            
            # Génération aperçu court
            preview = self._generate_short_preview(day_entries[:2])  # 2 premières entrées
            
            return {
                "date": target_date,
                "entry_count": len(day_entries),
                "has_context": True,
                "preview": preview,
                "tags": list(all_tags)[:5],  # Top 5 tags
                "importance_levels": list(set(importance_levels)),
                "total_tokens": total_tokens,
                "formatted_date": self._format_date_human(target_date)
            }
            
        except Exception as e:
            print(f"[CONTEXT-PROVIDER] ERROR Erreur aperçu contexte: {e}")
            return {"date": target_date, "entry_count": 0, "has_context": False, "preview": "Erreur"}
    
    def get_weekly_summary(self, week_start_date: str = None) -> str:
        """
        Génère un résumé de la semaine pour contexte étendu
        
        Args:
            week_start_date: Date de début de semaine (défaut: lundi courant)
        
        Returns:
            str: Résumé de la semaine formaté
        """
        try:
            # Calcul des dates de la semaine
            if not week_start_date:
                today = date.today()
                week_start = today - timedelta(days=today.weekday())
                week_start_date = week_start.isoformat()
            
            week_dates = []
            start_date = datetime.fromisoformat(week_start_date).date()
            for i in range(7):
                week_dates.append((start_date + timedelta(days=i)).isoformat())
            
            # Collecte des entrées de la semaine
            week_entries = []
            for day_date in week_dates:
                day_entries = self.json_manager.get_day_entries(day_date)
                week_entries.extend(day_entries)
            
            if not week_entries:
                return "Aucune activité enregistrée cette semaine."
            
            # Analyse et formatage
            return self._format_weekly_summary(week_entries, week_dates)
            
        except Exception as e:
            print(f"[CONTEXT-PROVIDER] ERROR Erreur résumé hebdomadaire: {e}")
            return ""
    
    def invalidate_cache(self, target_date: str = None):
        """
        Invalide le cache de contexte
        
        Args:
            target_date: Date spécifique à invalider (défaut: tout le cache)
        """
        if target_date:
            # Invalidation sélective
            keys_to_remove = [k for k in self.context_cache.keys() if k.startswith(target_date)]
            for key in keys_to_remove:
                self.context_cache.pop(key, None)
                self.cache_timestamps.pop(key, None)
        else:
            # Invalidation complète
            self.context_cache.clear()
            self.cache_timestamps.clear()
        
        print(f"[CONTEXT-PROVIDER] UPDATE Cache invalidé ({'tout' if not target_date else target_date})")
    
    # === MÉTHODES PRIVÉES ===
    
    def _select_relevant_entries(self, entries: List[Dict[str, Any]], limit: int) -> List[Dict[str, Any]]:
        """Sélectionne les entrées les plus pertinentes selon critères"""
        if len(entries) <= limit:
            return entries
        
        # Scoring des entrées par pertinence
        scored_entries = []
        for entry in entries:
            score = self._calculate_relevance_score(entry)
            scored_entries.append((score, entry))
        
        # Tri par score décroissant et sélection du top
        scored_entries.sort(key=lambda x: x[0], reverse=True)
        return [entry for score, entry in scored_entries[:limit]]
    
    def _calculate_relevance_score(self, entry: Dict[str, Any]) -> float:
        """Calcule un score de pertinence pour une entrée"""
        score = 0.0
        
        # Score par importance
        importance_scores = {"critical": 10, "high": 7, "normal": 5, "low": 2}
        importance = entry.get("importance", "normal")
        score += importance_scores.get(importance, 5)
        
        # Score par longueur (plus long = plus important)
        tokens = entry.get("tokens", 0)
        if tokens > 300:
            score += 3
        elif tokens > 200:
            score += 2
        elif tokens > 100:
            score += 1
        
        # Score par nombre de tags (plus de contexte)
        tag_count = len(entry.get("tags", []))
        score += min(tag_count * 0.5, 2)  # Max +2 pour les tags
        
        # Score par récence dans la journée (plus récent = plus pertinent)
        timestamp = entry.get("timestamp", "")
        if timestamp:
            try:
                entry_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                hour = entry_time.hour
                # Score plus élevé pour les entrées récentes dans la journée
                if hour >= 18:      # Soirée
                    score += 2
                elif hour >= 12:    # Après-midi
                    score += 1.5
                elif hour >= 9:     # Matinée
                    score += 1
            except ValueError:
                pass
        
        return score
    
    def _format_entries_context(self, entries: List[Dict[str, Any]], target_date: str) -> str:
        """Formate les entrées selon le style configuré"""
        template = self.format_templates.get(self.format_style, self.format_templates["summary"])
        
        # Variables communes
        variables = {
            "date": target_date,
            "formatted_date": self._format_date_human(target_date),
            "entry_count": len(entries),
            "total_entries": len(entries)
        }
        
        # Formatage spécifique selon le style
        if self.format_style == "minimal":
            return self._format_minimal_context(entries, variables)
        elif self.format_style == "detailed":
            return self._format_detailed_context(entries, variables)
        else:  # summary (défaut)
            return self._format_summary_context(entries, variables)
    
    def _format_minimal_context(self, entries: List[Dict[str, Any]], variables: Dict[str, Any]) -> str:
        """Format minimal - juste l'essentiel"""
        if not entries:
            return ""
        
        # Une seule ligne par entrée, très concise
        entry_lines = []
        for entry in entries:
            importance_icon = {"critical": "🔴", "high": "🟠", "normal": "🔵", "low": "⚪"}.get(
                entry.get("importance", "normal"), "🔵"
            )
            summary = entry.get("summary", "")[:60] + ("..." if len(entry.get("summary", "")) > 60 else "")
            entry_lines.append(f"{importance_icon} {summary}")
        
        context = f"JOURNAL **{variables['formatted_date']}** - {variables['entry_count']} entrée(s):\n"
        context += "\n".join(entry_lines)
        
        return context
    
    def _format_summary_context(self, entries: List[Dict[str, Any]], variables: Dict[str, Any]) -> str:
        """Format résumé - équilibre entre détail et concision"""
        context_parts = []
        
        # En-tête
        context_parts.append(f"JOURNAL **Contexte de la journée** - {variables['formatted_date']}")
        context_parts.append(f"*{variables['entry_count']} conversation(s) importante(s) enregistrée(s)*")
        context_parts.append("")
        
        # Entrées avec format moyen
        for i, entry in enumerate(entries, 1):
            importance = entry.get("importance", "normal")
            importance_text = {
                "critical": "🔴 **Critique**",
                "high": "🟠 **Important**", 
                "normal": "🔵 Normal",
                "low": "⚪ Info"
            }.get(importance, "🔵 Normal")
            
            # Résumé tronqué intelligemment
            summary = entry.get("summary", "")
            if len(summary) > 150:
                # Coupe au dernier point ou à 150 chars
                cut_point = summary.rfind('.', 0, 150)
                if cut_point > 100:
                    summary = summary[:cut_point + 1]
                else:
                    summary = summary[:147] + "..."
            
            # Tags principaux
            tags = entry.get("tags", [])[:3]  # Max 3 tags
            tag_text = f" `{' · '.join(tags)}`" if tags else ""
            
            context_parts.append(f"**{i}.** {importance_text}{tag_text}")
            context_parts.append(f"   {summary}")
            context_parts.append("")
        
        # Pied de page
        context_parts.append("---")
        context_parts.append("*Ce contexte vous aide à reprendre le fil de vos conversations précédentes.*")
        
        return "\n".join(context_parts)
    
    def _format_detailed_context(self, entries: List[Dict[str, Any]], variables: Dict[str, Any]) -> str:
        """Format détaillé - information complète"""
        context_parts = []
        
        # En-tête enrichi
        context_parts.append(f"JOURNAL **Journal de Bord - {variables['formatted_date']}**")
        
        # Analyse globale
        all_tags = set()
        importance_counts = {"critical": 0, "high": 0, "normal": 0, "low": 0}
        total_tokens = 0
        
        for entry in entries:
            all_tags.update(entry.get("tags", []))
            importance_counts[entry.get("importance", "normal")] += 1
            total_tokens += entry.get("tokens", 0)
        
        # Résumé global
        context_parts.append(f"STATS **Résumé**: {variables['entry_count']} conversations ({total_tokens} tokens)")
        
        if importance_counts["critical"] > 0:
            context_parts.append(f"🔴 **{importance_counts['critical']} conversation(s) critique(s)**")
        if importance_counts["high"] > 0:
            context_parts.append(f"🟠 {importance_counts['high']} conversation(s) importante(s)")
        
        if all_tags:
            top_tags = sorted(all_tags)[:5]
            context_parts.append(f"🏷️ **Thèmes**: {' · '.join(top_tags)}")
        
        context_parts.append("")
        context_parts.append("---")
        context_parts.append("")
        
        # Détail des entrées
        for i, entry in enumerate(entries, 1):
            timestamp = entry.get("timestamp", "")
            time_str = ""
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = f" ({dt.strftime('%H:%M')})"
                except ValueError:
                    pass
            
            importance_full = {
                "critical": "🔴 **CRITIQUE**",
                "high": "🟠 **IMPORTANT**",
                "normal": "🔵 **Normal**",
                "low": "⚪ **Information**"
            }.get(entry.get("importance", "normal"), "🔵 **Normal**")
            
            context_parts.append(f"### {i}. {importance_full}{time_str}")
            
            # Métadonnées
            tokens = entry.get("tokens", 0)
            participants = entry.get("participants", [])
            reading_time = entry.get("reading_time_seconds", 0)
            
            meta_parts = []
            if tokens > 0:
                meta_parts.append(f"{tokens} tokens")
            if len(participants) > 1:
                meta_parts.append(f"{len(participants)} participants")
            if reading_time > 0:
                meta_parts.append(f"{reading_time}s de lecture")
            
            if meta_parts:
                context_parts.append(f"*{' · '.join(meta_parts)}*")
            
            # Résumé complet
            summary = entry.get("summary", "")
            context_parts.append(f"\n{summary}")
            
            # Tags détaillés
            tags = entry.get("tags", [])
            if tags:
                context_parts.append(f"\n🏷️ {' · '.join(tags)}")
            
            context_parts.append("")
            context_parts.append("---")
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def _format_no_entries_context(self, target_date: str) -> str:
        """Formate le contexte quand aucune entrée n'existe"""
        formatted_date = self._format_date_human(target_date)
        
        # Messages selon le format
        if self.format_style == "minimal":
            return f"JOURNAL {formatted_date} - Nouvelle journée"
        
        elif self.format_style == "detailed":
            return f"""JOURNAL **Journal de Bord - {formatted_date}**

🌟 **Nouvelle journée !**

Aucune conversation n'a encore été enregistrée aujourd'hui. 
Cette journée est une page blanche dans votre journal de bord.

*Vos futures conversations importantes seront automatiquement résumées et ajoutées ici.*

---"""
        
        else:  # summary
            return f"""JOURNAL **Contexte de la journée** - {formatted_date}

🌟 **Nouvelle journée !** Aucune conversation enregistrée pour le moment.

*Vos conversations importantes seront automatiquement ajoutées à ce contexte.*

---"""
    
    def _generate_short_preview(self, entries: List[Dict[str, Any]]) -> str:
        """Génère un aperçu court pour l'interface"""
        if not entries:
            return "Aucune entrée"
        
        if len(entries) == 1:
            summary = entries[0].get("summary", "")
            return summary[:80] + ("..." if len(summary) > 80 else "")
        
        # Plusieurs entrées - résumé très court
        important_count = sum(1 for e in entries if e.get("importance") in ["critical", "high"])
        normal_count = len(entries) - important_count
        
        preview_parts = []
        if important_count > 0:
            preview_parts.append(f"{important_count} conversation(s) importante(s)")
        if normal_count > 0:
            preview_parts.append(f"{normal_count} autre(s)")
        
        return " et ".join(preview_parts)
    
    def _format_weekly_summary(self, week_entries: List[Dict[str, Any]], week_dates: List[str]) -> str:
        """Formate un résumé hebdomadaire"""
        if not week_entries:
            return "Semaine sans activité enregistrée."
        
        # Analyse hebdomadaire
        days_with_activity = len(set(entry.get("timestamp", "")[:10] for entry in week_entries))
        total_tokens = sum(entry.get("tokens", 0) for entry in week_entries)
        
        # Top tags de la semaine
        all_tags = []
        for entry in week_entries:
            all_tags.extend(entry.get("tags", []))
        
        tag_counts = {}
        for tag in all_tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        top_tags = sorted(tag_counts.keys(), key=lambda t: tag_counts[t], reverse=True)[:5]
        
        summary = f"""📅 **Résumé de la semaine**

STATS **Activité**: {len(week_entries)} conversations sur {days_with_activity}/7 jours
💬 **Volume**: {total_tokens} tokens générés
🏷️ **Thèmes principaux**: {' · '.join(top_tags) if top_tags else 'Aucun tag'}

Cette semaine vous avez été {'très actif' if days_with_activity >= 5 else 'actif' if days_with_activity >= 3 else 'peu actif'} dans vos conversations avec OGMA."""
        
        return summary
    
    def _format_date_human(self, date_str: str) -> str:
        """Formate une date de manière humaine"""
        try:
            date_obj = datetime.fromisoformat(date_str).date()
            today = date.today()
            
            if date_obj == today:
                return "Aujourd'hui"
            elif date_obj == today - timedelta(days=1):
                return "Hier"
            elif date_obj == today + timedelta(days=1):
                return "Demain"
            else:
                # Format français
                months = [
                    "janvier", "février", "mars", "avril", "mai", "juin",
                    "juillet", "août", "septembre", "octobre", "novembre", "décembre"
                ]
                return f"{date_obj.day} {months[date_obj.month - 1]} {date_obj.year}"
        
        except ValueError:
            return date_str
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Vérifie la validité du cache"""
        if cache_key not in self.context_cache:
            return False
        
        timestamp = self.cache_timestamps.get(cache_key, 0)
        return (datetime.now().timestamp() - timestamp) < self.cache_duration
    
    def _cache_context(self, cache_key: str, context: str):
        """Met en cache un contexte"""
        self.context_cache[cache_key] = context
        self.cache_timestamps[cache_key] = datetime.now().timestamp()
        
        # Nettoyage cache si trop volumineux
        if len(self.context_cache) > 50:
            oldest_key = min(self.cache_timestamps.keys(), key=self.cache_timestamps.get)
            self.context_cache.pop(oldest_key, None)
            self.cache_timestamps.pop(oldest_key, None)
    
    # === TEMPLATES ===
    
    def _get_minimal_template(self) -> str:
        """Template minimal pour contexte discret"""
        return "JOURNAL {formatted_date} - {entry_count} entrée(s)"
    
    def _get_summary_template(self) -> str:
        """Template résumé pour équilibre optimal"""
        return """JOURNAL **Contexte de la journée** - {formatted_date}
*{entry_count} conversation(s) importante(s) enregistrée(s)*

{entries}

---
*Ce contexte vous aide à reprendre le fil de vos conversations précédentes.*"""
    
    def _get_detailed_template(self) -> str:
        """Template détaillé pour contexte complet"""
        return """JOURNAL **Journal de Bord - {formatted_date}**

STATS **Résumé**: {entry_count} conversations 

{entries}"""