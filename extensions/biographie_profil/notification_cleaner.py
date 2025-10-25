#!/usr/bin/env python3
"""
🧹 UTILITAIRE DE NETTOYAGE NOTIFICATIONS OGMA
============================================

Utilitaire pour nettoyer les notifications "coincées" dans l'interface NiceGUI.

Problème résolu:
- Notifications "ongoing" qui restent visibles malgré la fin du travail
- Interface polluée par des notifications obsolètes

Usage: Intégrer dans ui_components.py ou appeler manuellement
"""

import asyncio
from nicegui import ui

class NotificationCleaner:
    """Gestionnaire de nettoyage des notifications coincées"""
    
    def __init__(self):
        self.active_notifications = []
    
    def create_managed_notification(self, message: str, type_: str = 'ongoing', timeout: int = 60) -> object:
        """
        Crée une notification gérée avec nettoyage automatique
        
        Args:
            message: Message à afficher
            type_: Type de notification ('ongoing', 'positive', etc.)
            timeout: Timeout en secondes
            
        Returns:
            Objet notification pour contrôle manuel
        """
        try:
            notification = ui.notify(message, type=type_, timeout=timeout)
            self.active_notifications.append(notification)
            
            print(f"[NOTIF-CLEANER] ✅ Notification créée: {message[:50]}...")
            return notification
            
        except Exception as e:
            print(f"[NOTIF-CLEANER] ❌ Erreur création notification: {e}")
            return None
    
    async def dismiss_notification(self, notification) -> bool:
        """
        Ferme une notification spécifique avec vérifications
        
        Args:
            notification: Objet notification à fermer
            
        Returns:
            True si succès, False sinon
        """
        try:
            if notification and hasattr(notification, 'dismiss'):
                notification.dismiss()
                
                # Retirer de la liste active
                if notification in self.active_notifications:
                    self.active_notifications.remove(notification)
                    
                print(f"[NOTIF-CLEANER] ✅ Notification fermée explicitement")
                return True
                
        except Exception as e:
            print(f"[NOTIF-CLEANER] ⚠️ Erreur fermeture notification: {e}")
            
        return False
    
    async def force_cleanup_all(self) -> int:
        """
        Nettoyage forcé de TOUTES les notifications actives
        
        Returns:
            Nombre de notifications nettoyées
        """
        cleaned_count = 0
        
        try:
            print(f"[NOTIF-CLEANER] 🧹 Nettoyage forcé: {len(self.active_notifications)} notifications")
            
            # Méthode 1: Fermer toutes les notifications gérées
            for notification in self.active_notifications[:]:  # Copie pour éviter modification pendant itération
                if await self.dismiss_notification(notification):
                    cleaned_count += 1
            
            # Méthode 2: Signal de nettoyage global
            ui.notify('', type='info', timeout=0.1)
            await asyncio.sleep(0.2)
            
            # Méthode 3: Notification de confirmation rapide
            ui.notify('🔄 Interface rafraîchie', type='info', timeout=1.5)
            
            self.active_notifications.clear()
            print(f"[NOTIF-CLEANER] ✅ Nettoyage terminé: {cleaned_count} notifications")
            
            return cleaned_count
            
        except Exception as e:
            print(f"[NOTIF-CLEANER] ❌ Erreur nettoyage global: {e}")
            return cleaned_count
    
    async def emergency_reset(self) -> None:
        """
        Réinitialisation d'urgence de l'interface notifications
        
        À utiliser en cas de notifications complètement bloquées
        """
        try:
            print(f"[NOTIF-CLEANER] 🚨 RÉINITIALISATION D'URGENCE")
            
            # Vider toutes les listes
            self.active_notifications.clear()
            
            # Multiples signaux de nettoyage
            for i in range(3):
                ui.notify('', type='info', timeout=0.05)
                await asyncio.sleep(0.1)
            
            # Notification de redémarrage
            ui.notify('🔄 Interface réinitialisée', type='warning', timeout=2)
            
            print(f"[NOTIF-CLEANER] ✅ Réinitialisation d'urgence terminée")
            
        except Exception as e:
            print(f"[NOTIF-CLEANER] ❌ Erreur réinitialisation d'urgence: {e}")

# Instance globale pour utilisation dans OGMA
notification_cleaner = NotificationCleaner()

async def test_cleaner():
    """Test du nettoyeur de notifications"""
    print("🧪 TEST NETTOYEUR NOTIFICATIONS")
    print("=" * 35)
    
    # Simuler notifications coincées
    notif1 = notification_cleaner.create_managed_notification("Test notification 1", "ongoing")
    notif2 = notification_cleaner.create_managed_notification("Test notification 2", "ongoing")
    
    await asyncio.sleep(1)
    
    # Test nettoyage
    cleaned = await notification_cleaner.force_cleanup_all()
    print(f"Nettoyées: {cleaned}")
    
    # Test réinitialisation d'urgence
    await notification_cleaner.emergency_reset()

if __name__ == "__main__":
    print("🧹 Utilitaire de nettoyage notifications OGMA")
    print("Intégrer dans ui_components.py pour utilisation")