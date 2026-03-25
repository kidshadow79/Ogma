# 📅 Extension Organic Planner pour OGMA

from .organic_planner import initialize_planner, get_planner, OrganicPlanner

def is_available() -> bool:
    """Vérifie si l'extension est initialisée."""
    return get_planner() is not None

def get_briefing() -> str:
    """Récupère le briefing pour injection."""
    planner = get_planner()
    if planner:
        return planner.get_briefing_text()
    return ""


def cleanup():
    """Nettoyage propre de l'extension organic_planner."""
    try:
        from . import organic_planner as _mod
        _mod._planner_instance = None
        print("[ORGANIC-PLANNER] Cleanup effectue")
    except Exception as e:
        print(f"[ORGANIC-PLANNER] Erreur cleanup: {e}")
