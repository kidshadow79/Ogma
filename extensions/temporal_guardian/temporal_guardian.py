"""
Extension Temporal Guardian pour OGMA
====================================

DEPRECATED - architecture remplacée par temporal_log_builder.py (31 mars 2026)

Ancien système: Python mesure → Archiviste interprète (appel API) → instruction
Nouveau système: Python mesure ET formate → log JSON injecté → IA principale interprète

Ce fichier est conservé pour ne pas casser les imports existants.
La classe TemporalGuardian est réduite à des stubs sans effet.
"""

from typing import Optional, Dict, Any


class TemporalGuardian:
    """
    DEPRECATED - Stub conservé pour compatibilité imports.
    La logique temporelle est désormais dans temporal_log_builder.py.
    """

    def __init__(self, config=None, debug: bool = False):
        self.config = config
        self.debug = debug
        self.is_active = False  # Désactivé - remplacé par temporal_log_builder
        self.last_measurement = None
        if self.debug:
            print("[TemporalGuardian] Mode stub (remplacé par temporal_log_builder)")

    def process_user_message(self, user_message: str = "", archiviste_prompt: str = "", **kwargs) -> dict:
        """DEPRECATED stub — remplacé par temporal_log_builder.py."""
        return {"enriched_archiviste_prompt": archiviste_prompt, "temporal_data": None}

    async def analyze_with_archiviste(self, temporal_data, archiviste_controller) -> None:
        """DEPRECATED stub — remplacé par temporal_log_builder.py."""
        return None

    def reset_session(self):
        pass

    def should_reset_session(self) -> bool:
        return False


def create_temporal_guardian(config_dict=None, debug: bool = False) -> "TemporalGuardian":
    """Factory conservée pour compatibilité imports."""
    return TemporalGuardian(debug=debug)