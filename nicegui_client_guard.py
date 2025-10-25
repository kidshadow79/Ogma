"""
Module de protection pour les clients NiceGUI déconnectés
Évite les erreurs KeyError lors de déconnexions inattendues
"""

import functools
from nicegui import Client
import logging

logger = logging.getLogger(__name__)

def safe_client_operation(func):
    """
    Décorateur pour protéger les opérations NiceGUI contre les clients déconnectés.
    Utilise le client actuel automatiquement.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            # Vérifier si on a un client actuel valide (avec gestion silencieuse)
            if not hasattr(Client, 'current') or Client.current is None:
                logger.debug("Aucun client actuel - opération ignorée")
                return None
            current_client = Client.current
            
            # Vérifier si le client existe encore dans les instances
            if current_client.id not in Client.instances:
                logger.debug(f"Client {current_client.id} déconnecté - opération ignorée")
                return None
            
            # Client valide, exécuter la fonction
            return func(*args, **kwargs)
            
        except KeyError as e:
            logger.debug(f"Client déconnecté pendant l'opération: {e}")
            return None
        except AttributeError as e:
            # Ignorer silencieusement les erreurs d'attribut Client.current
            if "'Client' has no attribute 'current'" in str(e):
                logger.debug("Client pas encore initialisé - opération différée")
                return None
            logger.error(f"Erreur attribut client: {e}")
            return None
        except Exception as e:
            logger.error(f"Erreur dans opération client: {e}")
            return None
    
    return wrapper

def safe_timer_callback(callback):
    """
    Protège les callbacks de ui.timer contre les clients déconnectés
    """
    @safe_client_operation
    def protected_callback():
        return callback()
    
    return protected_callback

def safe_async_timer_callback(async_callback):
    """
    Protège les callbacks asynchrones de ui.timer contre les clients déconnectés
    """
    @safe_client_operation
    async def protected_async_callback():
        return await async_callback()
    
    return protected_async_callback

# Fonction utilitaire pour vérifier la validité du client
def is_client_valid():
    """
    Vérifie si le client actuel est valide et connecté
    """
    try:
        # Vérification silencieuse de l'existence du client
        if not hasattr(Client, 'current') or Client.current is None:
            return False
        current_client = Client.current
        return current_client.id in Client.instances
    except:
        return False