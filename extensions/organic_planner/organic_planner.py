# 📅 Organic Planner - Mémoire du Futur pour OGMA
# Philosophie: Donner une "charge mentale" et une perception temporelle à l'IA.

import sqlite3
import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Any

class OrganicPlanner:
    """
    Extension Organic Planner : Gère l'agenda organique d'OGMA.
    Permet de stocker des événements futurs avec une note émotionnelle.
    """
    
    def __init__(self, db_path: str = "data/agenda.db"):
        self.db_path = db_path
        self.settings_path = "data/organic_planner_settings.json"
        self._init_db()
        self._ensure_settings()
        print(f"[ORGANIC-PLANNER] ✅ Initialisé avec {self.db_path}")

    def _ensure_settings(self):
        """S'assure que le fichier de réglages existe."""
        if not os.path.exists(self.settings_path):
            default_settings = {
                "instruction": "# MÉMOIRE DES MOMENTS PLANIFIÉS\n\n[DIRECTIVE]\nTu as en mémoire des évènements planifiés dans le temps. Traite-les comme des souvenirs du futur — des choses que tu sais à l'avance et que tu gardes en tête naturellement.\n\n1. Si un évènement est marqué 'IMPORTANT' (jour J) ou 'DEMAIN', mentionne-le de manière naturelle dans ta réponse — comme quelqu'un qui se souvient vraiment.\n2. Utilise le 'Ressenti' noté pour adapter ton ton : soutien si c'est anxieux, enthousiasme si c'est positif.\n3. Pour les évènements J-2 ou plus : pas besoin de les mentionner systématiquement, sauf si le contexte de la conversation s'y prête.\n4. Quand un évènement est passé et validé, il disparaît — tu n'as plus à y penser."
            }
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(default_settings, f, indent=4, ensure_ascii=False)

    def get_instruction(self) -> str:
        """Récupère l'instruction d'injection."""
        try:
            if not os.path.exists(self.settings_path):
                self._ensure_settings()
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                return settings.get("instruction", "")
        except:
            return ""

    def save_instruction(self, text: str) -> bool:
        """Sauvegarde l'instruction d'injection."""
        try:
            settings = {}
            if os.path.exists(self.settings_path):
                with open(self.settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            
            settings["instruction"] = text
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[ORGANIC-PLANNER] ❌ Erreur save_instruction: {e}")
            return False

    def _init_db(self):
        """Initialise la base de données SQLite si elle n'existe pas."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS organic_events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        target_date TEXT, -- YYYY-MM-DD
                        content TEXT NOT NULL,
                        priority TEXT DEFAULT 'NORMAL', -- VITAL, HAUT, NORMAL, BAS
                        status TEXT DEFAULT 'EN_ATTENTE', -- EN_ATTENTE, EN_COURS, TERMINE
                        emotional_note TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                conn.commit()
        except Exception as e:
            print(f"[ORGANIC-PLANNER] ❌ Erreur init DB: {e}")

    def add_event(self, content: str, target_date: str = None, priority: str = "NORMAL", emotional_note: str = "") -> bool:
        """Ajoute un nouvel événement à l'agenda."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO organic_events (target_date, content, priority, emotional_note)
                    VALUES (?, ?, ?, ?)
                ''', (target_date, content, priority, emotional_note))
                conn.commit()
                return True
        except Exception as e:
            print(f"[ORGANIC-PLANNER] ❌ Erreur add_event: {e}")
            return False

    def update_event_status(self, event_id: int, status: str) -> bool:
        """Met à jour le statut d'un événement."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE organic_events SET status = ? WHERE id = ?', (status, event_id))
                conn.commit()
                return True
        except Exception as e:
            print(f"[ORGANIC-PLANNER] ❌ Erreur update_status: {e}")
            return False

    def update_event_status_by_title(self, title: str, status: str) -> Optional[Dict[str, Any]]:
        """Met à jour le statut d'un événement par son titre et retourne ses données."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Recherche exacte d'abord, puis floue
                cursor.execute('SELECT * FROM organic_events WHERE content = ?', (title,))
                row = cursor.fetchone()
                
                if not row:
                    cursor.execute('SELECT * FROM organic_events WHERE content LIKE ?', (f"%{title}%",))
                    row = cursor.fetchone()
                
                if row:
                    event_data = dict(row)
                    cursor.execute('UPDATE organic_events SET status = ? WHERE id = ?', (status, event_data['id']))
                    conn.commit()
                    event_data['status'] = status
                    return event_data
                
                return None
        except Exception as e:
            print(f"[ORGANIC-PLANNER] ❌ Erreur update_status_by_title: {e}")
            return None

    def update_emotional_note(self, event_id: int, note: str) -> bool:
        """Met à jour la note émotionnelle d'un événement."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('UPDATE organic_events SET emotional_note = ? WHERE id = ?', (note, event_id))
                conn.commit()
                return True
        except Exception as e:
            print(f"[ORGANIC-PLANNER] ❌ Erreur update_emotional_note: {e}")
            return False

    def get_active_events(self) -> List[Dict[str, Any]]:
        """Récupère les événements EN_ATTENTE ou EN_COURS."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM organic_events 
                    WHERE status IN ('EN_ATTENTE', 'EN_COURS')
                    ORDER BY target_date ASC,
                    CASE priority
                        WHEN 'VITAL'  THEN 1
                        WHEN 'HAUT'   THEN 2
                        WHEN 'NORMAL' THEN 3
                        WHEN 'BAS'    THEN 4
                        ELSE 3
                    END ASC
                ''')
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"[ORGANIC-PLANNER] ❌ Erreur get_active_events: {e}")
            return []

    def get_all_events(self) -> List[Dict[str, Any]]:
        """Récupère les évènements actifs (EN_ATTENTE, EN_COURS) pour l'UI."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM organic_events
                    WHERE status IN ('EN_ATTENTE', 'EN_COURS')
                    ORDER BY target_date ASC,
                    CASE priority
                        WHEN 'VITAL'  THEN 1
                        WHEN 'HAUT'   THEN 2
                        WHEN 'NORMAL' THEN 3
                        WHEN 'BAS'    THEN 4
                        ELSE 3
                    END ASC
                ''')
                rows = cursor.fetchall()
                return [
                    {
                        'id': row['id'],
                        'date': row['target_date'] if row['target_date'] else "À définir",
                        'title': row['content'],
                        'feeling': row['emotional_note'] if row['emotional_note'] else "Neutre",
                        'status': row['status'],
                        'priority': row['priority'] if row['priority'] else 'NORMAL'
                    } for row in rows
                ]
        except Exception as e:
            print(f"[ORGANIC-PLANNER] ❌ Erreur get_all_events: {e}")
            return []

    def delete_event(self, event_id: int) -> bool:
        """Supprime un évènement."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM organic_events WHERE id = ?', (event_id,))
                conn.commit()
                return True
        except Exception as e:
            print(f"[ORGANIC-PLANNER] ❌ Erreur delete_event: {e}")
            return False

    def clear_agenda(self) -> bool:
        """Vide tout l'agenda."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM organic_events')
                conn.commit()
                return True
        except Exception as e:
            print(f"[ORGANIC-PLANNER] ❌ Erreur clear_agenda: {e}")
            return False

    def get_briefing_text(self) -> str:
        """Génère un résumé textuel concis pour injection dans le system_prompt."""
        events = self.get_active_events()
        if not events:
            return ""
        
        now = datetime.now()
        briefing_parts = []
        
        for ev in events:
            target_str = ev['target_date']
            days_diff_str = ""
            if target_str:
                target_date = None
                # Essayer plusieurs formats de date
                for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
                    try:
                        target_date = datetime.strptime(target_str, fmt)
                        break
                    except ValueError:
                        continue
                
                if target_date:
                    try:
                        # Calculer la différence en jours (ignorer l'heure)
                        today = datetime(now.year, now.month, now.day)
                        target_day = datetime(target_date.year, target_date.month, target_date.day)
                        diff = (target_day - today).days
                        
                        if diff == 0:
                            days_diff_str = "IMPORTANT"
                        elif diff == 1:
                            days_diff_str = "DEMAIN"
                        elif diff > 1:
                            days_diff_str = f"J-{diff}"
                        elif diff == -1:
                            days_diff_str = "HIER (RETARD)"
                        else:
                            days_diff_str = f"RETARD {abs(diff)}j"
                    except Exception as e:
                        print(f"[ORGANIC-PLANNER] ⚠️ Erreur calcul diff: {e}")
                        days_diff_str = target_str
                else:
                    days_diff_str = target_str
            
            priority_tag = f"({ev['priority']})" if ev['priority'] != 'NORMAL' else ""
            note = f" - Ressenti: {ev['emotional_note']}" if ev['emotional_note'] else ""
            
            briefing_parts.append(f"[{days_diff_str if days_diff_str else 'PENSÉE'} : {ev['content']} {priority_tag}{note}]")
        
        if not briefing_parts:
            return ""
            
        return "\n[MOMENTS PLANIFIÉS]:\n" + "\n".join(briefing_parts)

# Singleton pour accès facile
_planner_instance = None

def initialize_planner(db_path: str = "data/agenda.db") -> OrganicPlanner:
    global _planner_instance
    if _planner_instance is None:
        _planner_instance = OrganicPlanner(db_path)
    return _planner_instance

def get_planner() -> Optional[OrganicPlanner]:
    return _planner_instance
