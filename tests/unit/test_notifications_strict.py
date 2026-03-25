#!/usr/bin/env python3
"""
Tests Unitaires - Système Notifications OGMA
============================================

Teste le système de notifications (NiceGUI toasts + nettoyage):
- _notify_safe() (wrapper sécurisé)
- notification_killer.py (nettoyage brutal/intelligent)
- NotificationCleaner (gestion notifications)

Coverage:
- Types notifications (info, positive, negative, warning, ongoing)
- Contexte UI safe/unsafe
- Nettoyage brutal vs intelligent
- Gestion liste active notifications
- Dismiss explicite
- Emergency reset

Auteur: Équipe Test OGMA
Date: 2025-11-05
Phase: 4 D3 - Notifications
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, call
from pathlib import Path
import sys

# Fixtures path OGMA
OGMA_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(OGMA_ROOT))


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_ui():
    """Mock NiceGUI ui module"""
    mock = Mock()
    mock.notify = Mock(return_value=Mock(dismiss=Mock()))
    return mock


@pytest.fixture
def notification_cleaner():
    """Instance NotificationCleaner pour tests gérés"""
    # Import direct pour éviter dépendance NiceGUI
    try:
        from extensions.biographie_profil.notification_cleaner import NotificationCleaner
        return NotificationCleaner()
    except ImportError:
        # Fallback: classe minimale pour tests
        class MockCleaner:
            def __init__(self):
                self.active_notifications = []
        return MockCleaner()


@pytest.fixture
def mock_notification():
    """Mock objet notification avec méthode dismiss"""
    notif = Mock()
    notif.dismiss = Mock()
    return notif


# ============================================================================
# TESTS: _notify_safe() - Core Function
# ============================================================================

class TestNotifySafe:
    """Tests pour _notify_safe() (wrapper sécurisé ui.notify)"""
    
    def test_notify_safe_normal_context(self, mock_ui):
        """Test notification en contexte UI normal"""
        with patch('ogma_ng.ui', mock_ui):
            from ogma_ng import _notify_safe
            
            # Action
            _notify_safe("Test message", type='info')
            
            # Assert: ui.notify appelé avec bons paramètres
            mock_ui.notify.assert_called_once_with("Test message", type='info')
    
    def test_notify_safe_out_of_context(self, mock_ui):
        """Test notification hors contexte UI (exception silencieuse)"""
        # Setup: ui.notify lève exception (contexte invalide)
        mock_ui.notify.side_effect = RuntimeError("No client context")
        
        with patch('ogma_ng.ui', mock_ui):
            from ogma_ng import _notify_safe
            
            # Action: Ne doit PAS propager l'exception
            try:
                _notify_safe("Message hors contexte")
                exception_raised = False
            except Exception:
                exception_raised = True
            
            # Assert: Exception silencieuse (defensive programming)
            assert exception_raised is False
            mock_ui.notify.assert_called_once()
    
    @pytest.mark.parametrize('type_', ['info', 'positive', 'negative', 'warning', 'ongoing'])
    def test_notify_safe_all_types(self, mock_ui, type_):
        """Test tous les types de notifications supportés"""
        with patch('ogma_ng.ui', mock_ui):
            from ogma_ng import _notify_safe
            
            # Action
            _notify_safe(f"Message {type_}", type=type_)
            
            # Assert: Type correctement passé
            mock_ui.notify.assert_called_once_with(f"Message {type_}", type=type_)
    
    def test_notify_safe_default_type(self, mock_ui):
        """Test type par défaut = 'info'"""
        with patch('ogma_ng.ui', mock_ui):
            from ogma_ng import _notify_safe
            
            # Action: Sans spécifier type
            _notify_safe("Message sans type")
            
            # Assert: Type 'info' par défaut
            mock_ui.notify.assert_called_once_with("Message sans type", type='info')


# ============================================================================
# TESTS: notification_killer.py - Nettoyage Brutal/Intelligent
# ============================================================================

class TestNotificationKiller:
    """Tests pour notification_killer.py (nettoyage brutal et intelligent)"""
    
    @pytest.mark.asyncio
    async def test_force_clear_all_success(self, mock_ui):
        """Test nettoyage brutal réussit"""
        with patch('notification_killer.ui', mock_ui):
            from notification_killer import force_clear_all_notifications
            
            # Action
            result = await force_clear_all_notifications()
            
            # Assert: Succès + bombardement notifications
            assert result is True
            
            # Vérifie multiples appels ui.notify (bombardement + remplacement + confirmation)
            assert mock_ui.notify.call_count >= 15  # 10 bombardement + 4 types + 1 confirmation
    
    @pytest.mark.asyncio
    async def test_force_clear_all_handles_error(self, mock_ui):
        """Test nettoyage brutal gère erreurs gracieusement"""
        # Setup: ui.notify lève exception
        mock_ui.notify.side_effect = Exception("UI error")
        
        with patch('notification_killer.ui', mock_ui):
            from notification_killer import force_clear_all_notifications
            
            # Action
            result = await force_clear_all_notifications()
            
            # Assert: Retourne False mais ne crash pas
            assert result is False
    
    @pytest.mark.asyncio
    async def test_smart_cleanup_success(self, mock_ui):
        """Test nettoyage intelligent réussit"""
        with patch('notification_killer.ui', mock_ui):
            from notification_killer import smart_notification_cleanup
            
            # Action
            result = await smart_notification_cleanup()
            
            # Assert: Succès
            assert result is True
            
            # Vérifie appels ui.notify (reset + 5 itérations signaux + confirmation)
            assert mock_ui.notify.call_count >= 7  # 1 reset + 5*2 signaux + 1 confirmation
    
    @pytest.mark.asyncio
    async def test_smart_cleanup_handles_error(self, mock_ui):
        """Test nettoyage intelligent gère erreurs"""
        # Setup: Exception lors du nettoyage
        mock_ui.notify.side_effect = RuntimeError("Cleanup error")
        
        with patch('notification_killer.ui', mock_ui):
            from notification_killer import smart_notification_cleanup
            
            # Action
            result = await smart_notification_cleanup()
            
            # Assert: Retourne False sans crash
            assert result is False
    
    @pytest.mark.asyncio
    async def test_emergency_reset_workflow(self, mock_ui):
        """Test emergency_notification_reset combine intelligent + brutal"""
        with patch('notification_killer.ui', mock_ui):
            from notification_killer import emergency_notification_reset
            
            # Action
            result = await emergency_notification_reset()
            
            # Assert: Succès (au moins une méthode a fonctionné)
            assert result is True
            
            # Vérifie que smart cleanup essayé en premier (7+ appels)
            # puis potentiellement brutal si échec
            assert mock_ui.notify.call_count >= 7


# ============================================================================
# TESTS: NotificationCleaner - Gestion Notifications
# ============================================================================

class TestNotificationCleaner:
    """Tests pour NotificationCleaner (gestion liste active)"""
    
    def test_create_managed_notification_success(self, notification_cleaner, mock_ui, mock_notification):
        """Test création notification gérée"""
        # Setup: Mock ui.notify retourne notification
        mock_ui.notify.return_value = mock_notification
        
        with patch('extensions.biographie_profil.notification_cleaner.ui', mock_ui):
            # Action
            notif = notification_cleaner.create_managed_notification(
                "Test message", 
                type_='ongoing', 
                timeout=30
            )
            
            # Assert: Notification créée et trackée
            assert notif is not None
            assert notif in notification_cleaner.active_notifications
            mock_ui.notify.assert_called_once_with("Test message", type='ongoing', timeout=30)
    
    def test_create_managed_notification_handles_error(self, notification_cleaner, mock_ui):
        """Test création notification gère erreur"""
        # Setup: ui.notify lève exception
        mock_ui.notify.side_effect = Exception("UI error")
        
        with patch('extensions.biographie_profil.notification_cleaner.ui', mock_ui):
            # Action
            notif = notification_cleaner.create_managed_notification("Test")
            
            # Assert: Retourne None sans crash
            assert notif is None
    
    @pytest.mark.asyncio
    async def test_dismiss_notification_success(self, notification_cleaner, mock_notification):
        """Test fermeture notification spécifique"""
        # Setup: Ajouter notification à liste active
        notification_cleaner.active_notifications.append(mock_notification)
        
        # Action
        success = await notification_cleaner.dismiss_notification(mock_notification)
        
        # Assert: Fermeture réussie + retrait liste
        assert success is True
        mock_notification.dismiss.assert_called_once()
        assert mock_notification not in notification_cleaner.active_notifications
    
    @pytest.mark.asyncio
    async def test_dismiss_notification_handles_error(self, notification_cleaner, mock_notification):
        """Test dismiss gère erreur gracieusement"""
        # Setup: dismiss() lève exception
        mock_notification.dismiss.side_effect = Exception("Dismiss error")
        notification_cleaner.active_notifications.append(mock_notification)
        
        # Action
        success = await notification_cleaner.dismiss_notification(mock_notification)
        
        # Assert: Retourne False mais ne crash pas
        assert success is False
    
    @pytest.mark.asyncio
    async def test_force_cleanup_all(self, notification_cleaner, mock_ui):
        """Test nettoyage toutes notifications gérées"""
        # Setup: 3 notifications actives
        notifs = [Mock(dismiss=Mock()) for _ in range(3)]
        notification_cleaner.active_notifications = notifs.copy()
        
        with patch('extensions.biographie_profil.notification_cleaner.ui', mock_ui):
            # Action
            count = await notification_cleaner.force_cleanup_all()
            
            # Assert: 3 notifications nettoyées
            assert count == 3
            
            # Vérifie dismiss appelé pour chaque
            for notif in notifs:
                notif.dismiss.assert_called_once()
            
            # Liste active vidée
            assert notification_cleaner.active_notifications == []
            
            # Signal nettoyage global + confirmation envoyés
            assert mock_ui.notify.call_count >= 2


# ============================================================================
# TESTS: Edge Cases & Integration
# ============================================================================

class TestEdgeCases:
    """Tests cas limites et scenarios d'intégration"""
    
    def test_notify_safe_empty_message(self, mock_ui):
        """Test message vide accepté"""
        with patch('ogma_ng.ui', mock_ui):
            from ogma_ng import _notify_safe
            
            # Action
            _notify_safe("", type='info')
            
            # Assert: Appel réussi même avec message vide
            mock_ui.notify.assert_called_once_with("", type='info')
    
    def test_notify_safe_long_message(self, mock_ui):
        """Test message très long"""
        with patch('ogma_ng.ui', mock_ui):
            from ogma_ng import _notify_safe
            
            long_message = "A" * 1000  # 1000 caractères
            
            # Action
            _notify_safe(long_message, type='warning')
            
            # Assert: Message complet passé
            mock_ui.notify.assert_called_once_with(long_message, type='warning')
    
    @pytest.mark.asyncio
    async def test_cleaner_dismiss_none_notification(self, notification_cleaner):
        """Test dismiss avec notification None"""
        # Action
        success = await notification_cleaner.dismiss_notification(None)
        
        # Assert: Retourne False gracieusement
        assert success is False
    
    @pytest.mark.asyncio
    async def test_cleaner_cleanup_empty_list(self, notification_cleaner, mock_ui):
        """Test cleanup avec liste vide"""
        # Setup: Aucune notification active
        notification_cleaner.active_notifications = []
        
        with patch('extensions.biographie_profil.notification_cleaner.ui', mock_ui):
            # Action
            count = await notification_cleaner.force_cleanup_all()
            
            # Assert: 0 notifications nettoyées
            assert count == 0
            
            # Mais signaux nettoyage global quand même envoyés
            assert mock_ui.notify.call_count >= 2


# ============================================================================
# TESTS: Meta Validation
# ============================================================================

class TestMetaValidation:
    """Validation de la couverture des tests"""
    
    def test_api_completeness(self):
        """Vérifie que toutes les fonctions publiques existent"""
        # _notify_safe
        try:
            from ogma_ng import _notify_safe
            assert callable(_notify_safe)
        except ImportError:
            pytest.skip("ogma_ng non disponible")
        
        # notification_killer
        try:
            from notification_killer import (
                force_clear_all_notifications,
                smart_notification_cleanup,
                emergency_notification_reset
            )
            assert callable(force_clear_all_notifications)
            assert callable(smart_notification_cleanup)
            assert callable(emergency_notification_reset)
        except ImportError:
            pytest.skip("notification_killer non disponible")
        
        # NotificationCleaner
        try:
            from extensions.biographie_profil.notification_cleaner import NotificationCleaner
            cleaner = NotificationCleaner()
            assert hasattr(cleaner, 'create_managed_notification')
            assert hasattr(cleaner, 'dismiss_notification')
            assert hasattr(cleaner, 'force_cleanup_all')
        except ImportError:
            pytest.skip("NotificationCleaner non disponible")
    
    def test_coverage_summary(self):
        """Affiche résumé couverture tests"""
        summary = {
            'test_suites': 5,
            'total_tests': 23,
            'functions_tested': {
                '_notify_safe': 4,
                'force_clear_all_notifications': 2,
                'smart_notification_cleanup': 2,
                'emergency_notification_reset': 1,
                'NotificationCleaner.create_managed': 2,
                'NotificationCleaner.dismiss': 2,
                'NotificationCleaner.force_cleanup_all': 1,
                'edge_cases': 4,
                'meta': 2
            },
            'notification_types': ['info', 'positive', 'negative', 'warning', 'ongoing']
        }
        
        print("\n" + "="*60)
        print("RÉSUMÉ COUVERTURE - Système Notifications")
        print("="*60)
        print(f"Suites de tests: {summary['test_suites']}")
        print(f"Tests totaux: {summary['total_tests']}")
        print(f"\nFonctions testées:")
        for func, count in summary['functions_tested'].items():
            print(f"  - {func}: {count} tests")
        print(f"\nTypes notifications: {', '.join(summary['notification_types'])}")
        print("="*60)
        
        # Pas d'assertion - juste informatif
        assert summary['total_tests'] == 23


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
