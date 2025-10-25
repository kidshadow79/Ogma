"""
Gestionnaire d'erreurs pour les problèmes NiceGUI courants
Capture et traite silencieusement les erreurs KeyError de suppression de clients
"""

import logging
import sys
from typing import Any
from nicegui import Client

# Configuration du logger pour filtrer les erreurs NiceGUI
logger = logging.getLogger(__name__)

class NiceGUIErrorFilter:
    """Filtre pour capturer et traiter les erreurs NiceGUI courantes"""
    
    def __init__(self):
        self.original_delete = None
        self.patch_applied = False
    
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
        
        # Appliquer le patch de suppression sécurisée
        self.apply_client_delete_patch()
        
        # Configuration du logger NiceGUI pour réduire le bruit
        nicegui_logger = logging.getLogger('nicegui')
        
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