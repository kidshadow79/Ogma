"""
Gestionnaire d'erreurs pour les problèmes NiceGUI courants
Capture et traite silencieusement les erreurs KeyError de suppression de clients

🔧 MODE DEBUG: Mettre DEBUG_NICEGUI_ERRORS = True pour voir TOUS les logs
🔧 TIMEOUT FIX: Augmente le timeout des timers de 60s à 300s pour les longues conversations
"""

import logging
import sys
from typing import Any
from nicegui import Client

# Configuration du logger pour filtrer les erreurs NiceGUI
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# 🔧 DEBUG MODE - Mettre à True pour voir TOUS les logs de timeout/reconnection
# ═══════════════════════════════════════════════════════════════════════════════
DEBUG_NICEGUI_ERRORS = True  # ← ACTIVÉ pour diagnostiquer les déconnexions
# ═══════════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════════
# 🔧 FIX TIMEOUT 60s - Patch pour augmenter le timeout des timers NiceGUI
# ═══════════════════════════════════════════════════════════════════════════════
TIMER_TIMEOUT_OVERRIDE = 1800.0  # 30 minutes au lieu de 60 secondes
ACTIVITY_GRACE_PERIOD = 600.0   # 10 minutes - couvre les longues générations streaming
# ═══════════════════════════════════════════════════════════════════════════════

# Tracking de l'activité utilisateur par client
import time as _time
_client_last_activity: dict[str, float] = {}

def track_client_activity(client_id: str):
    """Enregistre l'activité d'un client (appelé sur chaque interaction)"""
    _client_last_activity[client_id] = _time.time()
    
def get_client_last_activity(client_id: str) -> float:
    """Retourne le timestamp de la dernière activité (0 si jamais vu)"""
    return _client_last_activity.get(client_id, 0)

def cleanup_old_activity_records():
    """Nettoie les enregistrements d'activité très anciens (> 1h)"""
    now = _time.time()
    old_clients = [cid for cid, ts in _client_last_activity.items() if now - ts > 3600]
    for cid in old_clients:
        del _client_last_activity[cid]

class NiceGUIErrorFilter:
    """Filtre pour capturer et traiter les erreurs NiceGUI courantes"""
    
    def __init__(self):
        self.original_delete = None
        self.patch_applied = False
        self.timer_timeout_patched = False
        self.prune_patched = False
    
    def apply_prune_instances_patch(self):
        """
        🔧 FIX CRITIQUE: Augmente le seuil de prune_instances de 60s à 300s
        
        NiceGUI supprime les clients "stale" après 60s sans connexion socket.
        Cela cause des rechargements de page intempestifs.
        On augmente ce seuil à 300s pour les longues sessions.
        """
        if self.prune_patched:
            return
        
        try:
            import time
            from nicegui import Client
            from nicegui.logging import log
            
            # Sauvegarder la méthode originale
            original_prune = Client.prune_instances
            
            @classmethod
            def patched_prune_instances(cls, *, client_age_threshold: float = None) -> None:
                """Version patchée avec protection activité utilisateur"""
                # Utiliser notre timeout override au lieu de 60s par défaut
                threshold = client_age_threshold if client_age_threshold is not None else TIMER_TIMEOUT_OVERRIDE
                
                try:
                    # Nettoyer les anciens enregistrements d'activité
                    cleanup_old_activity_records()
                    
                    stale_clients = []
                    for client in cls.instances.values():
                        if getattr(client, 'shared', False) or client.has_socket_connection:
                            continue
                        if client.created > time.time() - threshold:
                            continue
                        
                        # ✅ NOUVEAU: Vérifier l'activité récente
                        last_activity = get_client_last_activity(client.id)
                        activity_age = time.time() - last_activity if last_activity > 0 else float('inf')
                        
                        if activity_age < ACTIVITY_GRACE_PERIOD:
                            # Client avec activité récente - NE PAS supprimer
                            if DEBUG_NICEGUI_ERRORS:
                                print(f"🛡️ [PRUNE-PROTECT] Client {client.id[:8]}... protégé (activité il y a {activity_age:.0f}s)")
                            continue
                        
                        stale_clients.append(client)
                    
                    if stale_clients and DEBUG_NICEGUI_ERRORS:
                        print(f"🔍 [PRUNE-DEBUG] {len(stale_clients)} clients stale détectés (seuil: {threshold}s)")
                        for client in stale_clients:
                            age = time.time() - client.created
                            print(f"   → Client {client.id[:8]}... age={age:.1f}s, socket={client.has_socket_connection}")
                    
                    for client in stale_clients:
                        if DEBUG_NICEGUI_ERRORS:
                            print(f"⚠️ [PRUNE-DEBUG] Suppression client {client.id[:8]}...")
                        client.delete()
                        
                except Exception:
                    log.exception('Error while pruning clients')
            
            # Remplacer la méthode de classe
            Client.prune_instances = patched_prune_instances
            self.prune_patched = True
            
            print(f"✅ [NICEGUI-FIX] Client.prune_instances seuil augmenté de 60s à {TIMER_TIMEOUT_OVERRIDE}s")
            logger.info(f"Prune instances patch appliqué: {TIMER_TIMEOUT_OVERRIDE}s")
            
        except Exception as e:
            print(f"⚠️ [NICEGUI-FIX] Impossible d'appliquer le patch prune: {e}")
            logger.warning(f"Échec du patch prune instances: {e}")
    
    def apply_timer_timeout_patch(self):
        """
        🔧 FIX CRITIQUE: Augmente le timeout des timers NiceGUI
        
        Le timeout par défaut de 60s cause le rechargement de page lors
        de longues conversations (streaming > 60s). On l'augmente à 300s.
        """
        if self.timer_timeout_patched:
            return
        
        try:
            from nicegui.elements import timer as nicegui_timer
            import asyncio
            
            # Créer une nouvelle méthode _can_start avec timeout augmenté
            original_can_start = nicegui_timer.Timer._can_start
            
            async def patched_can_start(self):
                """Version patchée avec timeout augmenté de 60s à 300s"""
                if getattr(self.client, 'shared', False):
                    return True
                
                # Utiliser le timeout augmenté au lieu de 60s
                TIMEOUT = TIMER_TIMEOUT_OVERRIDE  # 300s au lieu de 60s
                try:
                    await self.client.connected(timeout=TIMEOUT)
                    return True
                except TimeoutError:
                    from nicegui.logging import log
                    log.error(f'Timer cancelled because client is not connected after {TIMEOUT} seconds')
                    return False
            
            # Remplacer la méthode
            nicegui_timer.Timer._can_start = patched_can_start
            self.timer_timeout_patched = True
            
            print(f"✅ [NICEGUI-FIX] Timer timeout augmenté de 60s à {TIMER_TIMEOUT_OVERRIDE}s")
            logger.info(f"Timer timeout patch appliqué: {TIMER_TIMEOUT_OVERRIDE}s")
            
        except Exception as e:
            print(f"⚠️ [NICEGUI-FIX] Impossible d'appliquer le patch timeout: {e}")
            logger.warning(f"Échec du patch timeout timer: {e}")
    
    def apply_client_delete_patch(self):
        """
        Applique un patch sécurisé sur la méthode delete de Client
        pour éviter les KeyError lors de suppressions multiples
        """
        if self.patch_applied:
            return
            
        # Sauvegarder la méthode originale de classe
        original_delete = Client.delete
        
        def safe_delete(self):
            """Version sécurisée de Client.delete"""
            try:
                # Vérifier que le client existe encore avant suppression
                if hasattr(self, 'id') and self.id in Client.instances:
                    # Appeler la méthode originale avec self
                    return original_delete(self)
                else:
                    # Client déjà supprimé, rien à faire
                    logger.debug(f"Client {getattr(self, 'id', 'unknown')} déjà supprimé - ignoré")
                    return
            except KeyError as e:
                # Erreur de suppression - probable double suppression
                logger.debug(f"Erreur suppression client ignorée: {e}")
                return
            except Exception as e:
                # Autres erreurs - logger mais ne pas planter
                logger.warning(f"Erreur lors de la suppression client: {e}")
                return
        
        # Remplacer la méthode
        Client.delete = safe_delete
        self.patch_applied = True
        logger.info("Patch de sécurité Client.delete appliqué")
    
    def setup_error_handling(self):
        """Configure la gestion globale des erreurs NiceGUI"""
        
        # 🔧 Appliquer le patch prune_instances AVANT tout le reste
        self.apply_prune_instances_patch()
        
        # 🔧 Appliquer le patch de timeout des timers
        self.apply_timer_timeout_patch()
        
        # Appliquer le patch de suppression sécurisée
        self.apply_client_delete_patch()
        
        # Configuration du logger NiceGUI pour réduire le bruit
        nicegui_logger = logging.getLogger('nicegui')
        
        # 🔧 MODE DEBUG: Afficher TOUS les logs si DEBUG_NICEGUI_ERRORS = True
        if DEBUG_NICEGUI_ERRORS:
            print("=" * 70)
            print("🔍 [NICEGUI-DEBUG] MODE DEBUG ACTIVÉ - Tous les logs seront visibles")
            print("=" * 70)
            
            # Configurer le logger nicegui pour afficher TOUT
            nicegui_logger.setLevel(logging.DEBUG)
            
            # Ajouter un handler console pour voir tous les messages
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.DEBUG)
            console_handler.setFormatter(logging.Formatter(
                '🔴 [NICEGUI-%(levelname)s] %(message)s'
            ))
            nicegui_logger.addHandler(console_handler)
            
            # Créer un filtre qui LOG au lieu de filtrer
            class DebugLogFilter(logging.Filter):
                def filter(self, record):
                    msg = str(record.getMessage()).lower()
                    # Marquer les messages suspects
                    if any(keyword in msg for keyword in [
                        'timeout', 'disconnect', 'reconnect', 'client', 
                        'socket', 'websocket', 'connection', 'closed',
                        'keyerror', 'deleted', 'cancelled', 'timer'
                    ]):
                        print(f"⚠️ [NICEGUI-SUSPECT] {record.levelname}: {record.getMessage()}")
                    return True  # Laisser passer TOUS les messages
            
            nicegui_logger.addFilter(DebugLogFilter())
            logger.info("🔍 MODE DEBUG NiceGUI activé - Filtres désactivés")
            return
        
        # === MODE NORMAL (filtres actifs) ===
        # Créer un filtre personnalisé pour les erreurs KeyError de clients
        class ClientKeyErrorFilter(logging.Filter):
            def filter(self, record):
                # Filtrer les erreurs KeyError liées aux clients
                if (record.levelno == logging.ERROR and 
                    "KeyError" in str(record.getMessage()) and
                    "Client.instances" in str(record.getMessage())):
                    # Convertir en debug au lieu d'erreur
                    record.levelno = logging.DEBUG
                    record.levelname = "DEBUG"
                    record.msg = f"[FILTERED] Client KeyError ignoré: {record.msg}"
                return True
        
        # Créer un filtre pour les warnings de timers annulés
        class TimerCancelledFilter(logging.Filter):
            def filter(self, record):
                # Filtrer les warnings de timers annulés après déconnexion client
                if (record.levelno == logging.ERROR and 
                    "Timer cancelled because client is not connected" in str(record.getMessage())):
                    # Supprimer complètement ces messages (ne pas les afficher)
                    return False
                return True
        
        # Ajouter les filtres au logger NiceGUI
        nicegui_logger.addFilter(ClientKeyErrorFilter())
        nicegui_logger.addFilter(TimerCancelledFilter())
        
        logger.info("Gestionnaire d'erreurs NiceGUI configuré")

# Instance globale du gestionnaire d'erreurs
error_handler = NiceGUIErrorFilter()

def initialize_nicegui_error_handling():
    """
    Fonction utilitaire pour initialiser la gestion d'erreurs NiceGUI
    À appeler au démarrage de l'application
    """
    try:
        error_handler.setup_error_handling()
        return True
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation du gestionnaire d'erreurs: {e}")
        return False