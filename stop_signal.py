# -*- coding: utf-8 -*-
"""
Signal d'arrêt global pour OGMA.
Permet d'interrompre les opérations longues (streaming, polling, etc.)
"""

# État global d'arrêt
_stop_requested = False


def request_stop():
    """Demande l'arrêt des opérations en cours"""
    global _stop_requested
    _stop_requested = True
    print("[STOP-SIGNAL] 🛑 Arrêt demandé")


def is_stop_requested() -> bool:
    """Vérifie si un arrêt a été demandé"""
    return _stop_requested


def reset_stop():
    """Réinitialise le signal d'arrêt (à appeler au début d'une nouvelle opération)"""
    global _stop_requested
    _stop_requested = False


def check_stop_and_raise():
    """Vérifie le stop et lève une exception si demandé"""
    if _stop_requested:
        raise StopAsyncIteration("Arrêt demandé par l'utilisateur")
