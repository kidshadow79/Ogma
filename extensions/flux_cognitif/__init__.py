"""
🧠 Flux Cognitif - Visualisation temps réel des pensées OGMA
================================================================

Extension remplaçant Ego Mirror par un stream cognitif professionnel.
Affiche les décisions et injections de l'Archiviste, Biography, Journal, Dream Engine
dans un écran ambré translucide type overlay paramètres.

Architecture:
- stream_core.py : Gestion événements cognitifs (singleton)
- stream_ui.py : Interface NiceGUI overlay ambre
- Hooks dans ogma_ng.py pour logging temps réel

Philosophie: Transparence Totale - rendre visible les pensées de l'IA

Version: 1.0.0 (Phase 1 - SURFACE)
Date: 13 février 2026
"""

from typing import Optional, Dict, Any
from datetime import datetime
import os
import json

# Fichier de persistance des preferences (filtres + niveau)
_PREFS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'flux_prefs.json')

# Singleton instance
_flux_instance: Optional['FluxCognitif'] = None


class FluxCognitif:
    """Gestionnaire principal du flux cognitif"""
    
    def __init__(self):
        self.events = []  # Liste événements cognitifs
        self.max_events = 50  # Limite mémoire (évite surcharge)
        self.enabled = True
        
        # Filtres par défaut
        self._default_filters = {
            'archiviste': True,
            'biography': True,
            'dream': True,
            'journal': True,
            'directive': True,
            'web': False,
            'capability': False,
            'cache': True   # Cache cognitif - pensées secrètes de l'IA
        }
        self.filters = dict(self._default_filters)
        
        # Niveau introspection (1=SURFACE, 2=NORMAL, 3=DEEP)
        self.level = 1
        
        # Charger preferences sauvegardees (filtres + niveau)
        self._load_prefs()
        
        print("[FLUX-COGNITIF] Instance initialisee")
    
    def log_event(self, source: str, message: str, metadata: Dict = None, event_level: int = 1):
        """
        Enregistre un événement cognitif.
        Stocke TOUS les événements - le filtrage se fait a l'affichage.
        
        Args:
            source: Source (archiviste, biography, dream, journal, directive, web, capability)
            message: Message descriptif court
            metadata: Données supplémentaires optionnelles
            event_level: Niveau requis pour afficher (1=SURFACE, 2=NORMAL, 3=DEEP)
        """
        if not self.enabled:
            return
        
        event = {
            'timestamp': datetime.now(),
            'source': source,
            'message': message,
            'metadata': metadata or {},
            'level': event_level
        }
        
        self.events.append(event)
        
        # Limiter taille mémoire
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events:]
        
        level_prefix = ['', '▪', '▸', '▸▸'][event_level] if event_level <= 3 else '▸▸▸'
        print(f"[FLUX-COGNITIF] {level_prefix} {source.upper()}: {message}")
    
    def get_recent_events(self, limit: int = 20) -> list:
        """Retourne les N derniers événements"""
        return self.events[-limit:] if self.events else []
    
    def clear_events(self):
        """Vide l'historique des événements"""
        self.events = []
        print("[FLUX-COGNITIF] 🗑️ Historique vidé")
    
    def set_filter(self, source: str, enabled: bool):
        """Active/desactive un filtre par source et sauvegarde"""
        if source in self.filters:
            self.filters[source] = enabled
            self._save_prefs()
            print(f"[FLUX-COGNITIF] Filtre {source}: {'ON' if enabled else 'OFF'}")
    
    def set_level(self, level: int):
        """Definit le niveau d'introspection (1-3) et sauvegarde"""
        if 1 <= level <= 3:
            self.level = level
            self._save_prefs()
            print(f"[FLUX-COGNITIF] Niveau: {level}")
    
    def get_filtered_events(self, limit: int = 20) -> list:
        """Retourne les evenements filtres par sources actives et niveau courant"""
        filtered = [
            e for e in self.events
            if self.filters.get(e['source'], False) and e.get('level', 1) <= self.level
        ]
        return filtered[-limit:] if filtered else []
    
    def _load_prefs(self):
        """Charge les preferences (filtres + niveau) depuis le fichier persistant"""
        try:
            if os.path.exists(_PREFS_FILE):
                with open(_PREFS_FILE, 'r', encoding='utf-8') as f:
                    prefs = json.load(f)
                saved_filters = prefs.get('filters', {})
                for source, enabled in saved_filters.items():
                    if source in self.filters:
                        self.filters[source] = bool(enabled)
                saved_level = prefs.get('level', 1)
                if 1 <= saved_level <= 3:
                    self.level = saved_level
                active = [s for s, v in self.filters.items() if v]
                print(f"[FLUX-COGNITIF] Prefs chargees: niveau={self.level}, filtres actifs={active}")
        except Exception as e:
            print(f"[FLUX-COGNITIF] Prefs par defaut (erreur chargement: {e})")
    
    def _save_prefs(self):
        """Sauvegarde les preferences (filtres + niveau) dans le fichier persistant"""
        try:
            prefs = {
                'filters': self.filters,
                'level': self.level
            }
            with open(_PREFS_FILE, 'w', encoding='utf-8') as f:
                json.dump(prefs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[FLUX-COGNITIF] Erreur sauvegarde prefs: {e}")


# ============================================================================
# API PUBLIQUE - Singleton Pattern
# ============================================================================

def initialize_flux_cognitif() -> FluxCognitif:
    """Initialise le flux cognitif (appelé au démarrage OGMA)"""
    global _flux_instance
    if _flux_instance is None:
        _flux_instance = FluxCognitif()
    return _flux_instance


def get_flux_cognitif() -> Optional[FluxCognitif]:
    """Retourne l'instance active du flux cognitif"""
    return _flux_instance


def log_cognitive_event(source: str, message: str, metadata: Dict = None, event_level: int = 1):
    """
    Fonction raccourci pour logger un événement cognitif
    
    Args:
        source: Source (archiviste, biography, dream, journal, web, capability)
        message: Message court
        metadata: Données optionnelles (prompt, response, etc.)
        event_level: Niveau (1=SURFACE Phase 1, 2=NORMAL Phase 2, 3=DEEP Phase 3)
    
    Usage:
        # Phase 1 - Événements basiques
        log_cognitive_event('archiviste', 'Ego: IDENTITE (3 traits)')
        
        # Phase 2 - Dialogues Archiviste
        log_cognitive_event('archiviste', 'Enrichissement souvenir #123', 
                           metadata={'prompt': '...', 'response': '...'}, event_level=2)
    """
    if _flux_instance:
        _flux_instance.log_event(source, message, metadata, event_level)


def is_available() -> bool:
    """Vérifie si le flux cognitif est disponible"""
    return _flux_instance is not None


def get_recent_events(limit: int = 20) -> list:
    """
    Retourne les N derniers événements du flux cognitif
    
    Args:
        limit: Nombre max d'événements à retourner
        
    Returns:
        Liste des derniers événements (vide si flux non initialisé)
    """
    if _flux_instance:
        return _flux_instance.get_recent_events(limit)
    return []


def cleanup():
    """Nettoyage propre de l'extension flux_cognitif."""
    global _flux_instance
    if _flux_instance is not None:
        try:
            _flux_instance.events.clear()
        except Exception:
            pass
    _flux_instance = None
    print("[FLUX-COGNITIF] Cleanup effectue")


# Export API publique
__all__ = [
    'initialize_flux_cognitif',
    'get_flux_cognitif',
    'log_cognitive_event',
    'get_recent_events',
    'is_available',
    'cleanup',
    'FluxCognitif'
]
