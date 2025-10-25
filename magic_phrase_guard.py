#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🛡️ MAGIC PHRASE GUARD - Protection Globale Phrases Magiques OGMA

Module de protection empêchant le déclenchement de phrases magiques pour messages historiques.
Utilisé par toutes les extensions OGMA (Introspection, Biographie, Journal, etc.).

Architecture Double Protection:
1. FLAG TEMPOREL : Actif pendant chargement conversation (0-5s)
2. MÉTADONNÉE PERMANENTE : Marque messages chargés avec 'from_history'

Auteur: Claude 4 + Yohan BROCARD
Date: 14 octobre 2025
Version: 1.0.0
"""

from typing import Dict, Any, Optional
import asyncio
import time
from datetime import datetime

__version__ = "1.0.0"
__author__ = "OGMA Team"

# ===== ÉTAT GLOBAL =====
_loading_historical_conversation = False
_loading_start_time: Optional[float] = None
_loading_timeout_task: Optional[asyncio.Task] = None

# ===== STATISTIQUES =====
_stats = {
    "total_blocks": 0,
    "blocks_by_flag": 0,
    "blocks_by_metadata": 0,
    "last_block_time": None,
    "extensions_protected": set(),
    "session_start": datetime.now().isoformat()
}


# ===== API PRINCIPALE =====

def activate_loading_mode():
    """
    Active le mode chargement historique (flag temporel)

    🛡️ PROTECTION 1 : Flag temporel global

    Appelé au DÉBUT de _load_conversation()
    Désactive automatiquement après timeout sécurité (5s)

    Usage:
        activate_loading_mode()
        # ... chargement et affichage messages ...
        await deactivate_loading_mode_delayed()
    """
    global _loading_historical_conversation, _loading_start_time, _loading_timeout_task

    _loading_historical_conversation = True
    _loading_start_time = time.time()

    print("[MAGIC-GUARD] 🛡️ Mode chargement historique ACTIVÉ")

    # Sécurité: timeout automatique après 5 secondes
    if _loading_timeout_task:
        _loading_timeout_task.cancel()

    _loading_timeout_task = asyncio.create_task(_auto_deactivate_after_timeout())


async def _auto_deactivate_after_timeout():
    """
    Désactive automatiquement après timeout sécurité

    Sécurité contre oubli de désactivation manuelle
    Timeout: 5 secondes (largement suffisant pour chargement)
    """
    await asyncio.sleep(5.0)  # 5 secondes max

    if _loading_historical_conversation:
        print("[MAGIC-GUARD] ⚠️ Timeout sécurité atteint (5s) - désactivation forcée")
        deactivate_loading_mode()


def deactivate_loading_mode():
    """
    Désactive le mode chargement historique immédiatement

    Appelé manuellement après affichage complet messages
    Ou automatiquement après timeout sécurité
    """
    global _loading_historical_conversation, _loading_start_time

    if not _loading_historical_conversation:
        return  # Déjà désactivé

    duration = time.time() - _loading_start_time if _loading_start_time else 0
    _loading_historical_conversation = False
    _loading_start_time = None

    print(f"[MAGIC-GUARD] 🛡️ Mode chargement historique DÉSACTIVÉ (durée: {duration:.2f}s)")


async def deactivate_loading_mode_delayed(delay: float = 1.5):
    """
    Désactive le mode après délai sécurité

    Recommandé pour utilisation asynchrone après _load_conversation()

    Args:
        delay: Délai en secondes (défaut 1.5s)

    Usage:
        asyncio.create_task(deactivate_loading_mode_delayed())
    """
    await asyncio.sleep(delay)
    deactivate_loading_mode()


def is_historical_message(message_data: Dict[str, Any]) -> bool:
    """
    Vérifie si message est historique (double protection)

    🛡️ PROTECTION DOUBLE:
    1. Flag temporel global (_loading_historical_conversation)
    2. Métadonnée permanente (from_history dans message)

    Args:
        message_data: Dictionnaire message avec métadonnées

    Returns:
        True si message historique (bloquer phrases magiques)
        False si message temps réel (autoriser phrases magiques)
    """
    # 🛡️ PROTECTION 1: Flag temporel global
    if _loading_historical_conversation:
        _stats["total_blocks"] += 1
        _stats["blocks_by_flag"] += 1
        _stats["last_block_time"] = datetime.now().isoformat()
        return True

    # 🛡️ PROTECTION 2: Métadonnée permanente (seulement pendant chargement actif)
    if message_data.get('from_history', False) and _loading_historical_conversation:
        _stats["total_blocks"] += 1
        _stats["blocks_by_metadata"] += 1
        _stats["last_block_time"] = datetime.now().isoformat()
        return True

    return False


def should_process_magic_phrase(message_data: Dict[str, Any], extension_name: str = "unknown") -> bool:
    """
    Détermine si phrases magiques doivent être traitées

    ⭐ API PRINCIPALE - Utilisée par TOUTES extensions OGMA

    Args:
        message_data: Dictionnaire message complet
        extension_name: Nom extension pour logs (ex: "INTROSPECTION", "BIOGRAPHIE")

    Returns:
        True si traitement autorisé (message temps réel)
        False si bloqué (message historique)

    Usage:
        if should_process_magic_phrase(current_message, "INTROSPECTION"):
            # Traiter phrase magique normalement...
        else:
            # Ignorer (message historique)
    """
    if is_historical_message(message_data):
        # Enregistrer extension protégée
        _stats["extensions_protected"].add(extension_name)

        # Déterminer quelle protection a agi
        protection = "FLAG-TEMPOREL" if _loading_historical_conversation else "MÉTADONNÉE"
        print(f"[MAGIC-GUARD] 🛡️ [{extension_name}] Message historique bloqué ({protection})")
        return False

    return True


def mark_message_as_historical(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Marque un message comme historique

    🛡️ PROTECTION 2 : Métadonnée permanente

    Appelé lors chargement conversation pour CHAQUE message
    Ajoute métadonnée 'from_history': True

    Args:
        message: Message original

    Returns:
        Message avec métadonnée from_history=True

    Usage:
        for msg in loaded_messages:
            msg = mark_message_as_historical(msg)
    """
    message['from_history'] = True
    return message


def unmark_message_as_historical(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Retire la marque historique d'un message

    Appelé lors édition message (message redevient "vivant")
    Retire métadonnée 'from_history'

    Args:
        message: Message avec métadonnée

    Returns:
        Message sans métadonnée from_history

    Usage:
        def _edit_message_load(message_index):
            message = _chat_history_ui[message_index]
            message = unmark_message_as_historical(message)
    """
    if 'from_history' in message:
        del message['from_history']
        print("[MAGIC-GUARD] 🔄 Message démarqué - devient éditable")

    return message


def clean_message_for_save(message: Dict[str, Any]) -> Dict[str, Any]:
    """
    Nettoie un message avant sauvegarde

    Retire métadonnées internes (from_history) pour garder JSON propre
    Les métadonnées sont ajoutées dynamiquement au chargement

    Args:
        message: Message avec potentielles métadonnées internes

    Returns:
        Message nettoyé (sans métadonnées runtime)

    Usage:
        cleaned_history = [clean_message_for_save(msg) for msg in history]
        save_to_json(cleaned_history)
    """
    cleaned = message.copy()

    # Retirer métadonnées runtime
    if 'from_history' in cleaned:
        del cleaned['from_history']

    return cleaned


# ===== UTILITAIRES =====

def is_loading_history() -> bool:
    """
    Vérifie si chargement historique en cours

    Returns:
        True si flag temporel actif, False sinon
    """
    return _loading_historical_conversation


def get_loading_duration() -> Optional[float]:
    """
    Retourne durée chargement en cours (si actif)

    Returns:
        Durée en secondes ou None si pas de chargement actif
    """
    if _loading_historical_conversation and _loading_start_time:
        return time.time() - _loading_start_time
    return None


def get_stats() -> Dict[str, Any]:
    """
    Retourne statistiques du gardien

    Returns:
        Dictionnaire avec statistiques complètes
    """
    return {
        **_stats,
        "currently_loading": _loading_historical_conversation,
        "loading_duration": get_loading_duration(),
        "extensions_protected": list(_stats["extensions_protected"])
    }


def reset_stats():
    """
    Réinitialise les statistiques

    Utile pour tests ou nouveau démarrage session
    """
    global _stats
    _stats = {
        "total_blocks": 0,
        "blocks_by_flag": 0,
        "blocks_by_metadata": 0,
        "last_block_time": None,
        "extensions_protected": set(),
        "session_start": datetime.now().isoformat()
    }
    print("[MAGIC-GUARD] 📊 Statistiques réinitialisées")


def print_stats():
    """Affiche statistiques formatées dans console"""
    stats = get_stats()

    print("\n" + "="*60)
    print("📊 MAGIC PHRASE GUARD - Statistiques")
    print("="*60)
    print(f"Session démarrée: {stats['session_start']}")
    print(f"Chargement actif: {'OUI' if stats['currently_loading'] else 'NON'}")

    if stats['loading_duration']:
        print(f"Durée chargement: {stats['loading_duration']:.2f}s")

    print(f"\n🛡️ Blocages totaux: {stats['total_blocks']}")
    print(f"  - Par flag temporel: {stats['blocks_by_flag']}")
    print(f"  - Par métadonnée: {stats['blocks_by_metadata']}")

    if stats['extensions_protected']:
        print(f"\n🔧 Extensions protégées:")
        for ext in stats['extensions_protected']:
            print(f"  - {ext}")

    if stats['last_block_time']:
        print(f"\nDernier blocage: {stats['last_block_time']}")

    print("="*60 + "\n")


# ===== ALIASES (pour compatibilité/simplicité) =====

start_loading = activate_loading_mode
stop_loading = deactivate_loading_mode


# ===== TESTS UNITAIRES =====

def _run_tests():
    """Tests unitaires du module"""
    print("\n🧪 TESTS MAGIC PHRASE GUARD\n")

    # Test 1: Activation/Désactivation flag
    print("Test 1: Flag temporel...")
    activate_loading_mode()
    assert is_loading_history() == True, "❌ Flag devrait être actif"
    deactivate_loading_mode()
    assert is_loading_history() == False, "❌ Flag devrait être inactif"
    print("✅ Test 1 OK")

    # Test 2: Marquage message
    print("\nTest 2: Marquage message...")
    msg = {"role": "assistant", "content": "test"}
    marked = mark_message_as_historical(msg)
    assert marked.get('from_history') == True, "❌ Métadonnée devrait être présente"
    print("✅ Test 2 OK")

    # Test 3: Détection message historique (métadonnée)
    print("\nTest 3: Détection message historique...")
    historical_msg = {"from_history": True, "content": "test"}
    assert is_historical_message(historical_msg) == True, "❌ Devrait détecter historique"

    live_msg = {"from_history": False, "content": "test"}
    assert is_historical_message(live_msg) == False, "❌ Devrait détecter temps réel"
    print("✅ Test 3 OK")

    # Test 4: Nettoyage message
    print("\nTest 4: Nettoyage message...")
    dirty_msg = {"role": "user", "content": "test", "from_history": True}
    cleaned = clean_message_for_save(dirty_msg)
    assert 'from_history' not in cleaned, "❌ Métadonnée devrait être supprimée"
    assert cleaned.get('content') == "test", "❌ Contenu devrait être préservé"
    print("✅ Test 4 OK")

    # Test 5: Should process (sans flag, sans métadonnée)
    print("\nTest 5: Should process message temps réel...")
    msg_realtime = {"content": "il faut que je réfléchisse"}
    assert should_process_magic_phrase(msg_realtime, "TEST") == True, "❌ Devrait autoriser"
    print("✅ Test 5 OK")

    # Test 6: Should process (avec métadonnée)
    print("\nTest 6: Should process message historique...")
    msg_hist = {"content": "il faut que je réfléchisse", "from_history": True}
    assert should_process_magic_phrase(msg_hist, "TEST") == False, "❌ Devrait bloquer"
    print("✅ Test 6 OK")

    # Test 7: Statistiques
    print("\nTest 7: Statistiques...")
    reset_stats()
    stats = get_stats()
    assert stats['total_blocks'] == 0, "❌ Stats devraient être réinitialisées"
    print("✅ Test 7 OK")

    print("\n✅ TOUS LES TESTS PASSÉS\n")


if __name__ == "__main__":
    # Exécuter tests si lancé directement
    _run_tests()

    # Afficher statistiques exemple
    print_stats()
