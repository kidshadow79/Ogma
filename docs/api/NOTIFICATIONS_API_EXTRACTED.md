# API Notifications OGMA - Documentation Complète

**Date d'extraction**: 2025-11-05  
**Composant**: Système de notifications (NiceGUI toasts + nettoyage)  
**Fichiers sources**: 
- `ogma_ng.py` (fonction `_notify_safe`)
- `notification_killer.py` (nettoyage brutal)
- `extensions/biographie_profil/notification_cleaner.py` (nettoyage géré)

---

## Vue d'Ensemble

Le système de notifications OGMA repose sur **NiceGUI ui.notify()** avec des wrappers de sécurité et des utilitaires de nettoyage pour gérer les notifications "coincées" ou obsolètes.

### Architecture Globale

```
┌─────────────────────────────────────────┐
│         OGMA Notification System         │
├─────────────────────────────────────────┤
│                                          │
│  1. _notify_safe() (ogma_ng.py)         │
│     └─> ui.notify() + exception wrapper │
│                                          │
│  2. notification_killer.py               │
│     ├─> force_clear_all_notifications()  │
│     ├─> smart_notification_cleanup()     │
│     └─> emergency_notification_reset()   │
│                                          │
│  3. NotificationCleaner (extension)      │
│     ├─> create_managed_notification()    │
│     ├─> dismiss_notification()           │
│     └─> force_cleanup_all()              │
│                                          │
└─────────────────────────────────────────┘
```

### Fonctionnalités Clés

- ✅ **Affichage sécurisé** (hors contexte UI = ignore)
- ✅ **Nettoyage brutal** (bombardement notifications vides)
- ✅ **Nettoyage intelligent** (gestion liste active)
- ✅ **Types multiples** (info, positive, negative, warning, ongoing)
- ✅ **Timeout configurable**
- ✅ **Position personnalisable** (top, center, bottom)

---

## API Publique

### 1. `_notify_safe()` (Core - ogma_ng.py)

**Signature**:
```python
def _notify_safe(message: str, type: str = 'info') -> None
```

**Description**:  
Wrapper sécurisé autour de `ui.notify()`. Attrape les exceptions si appelé hors contexte UI (timers, threads background).

**Paramètres**:
- `message` (str): Texte à afficher
- `type` (str): Type notification ('info', 'positive', 'negative', 'warning', 'ongoing')

**Retour**: None

**Comportement**:
- ✅ Appel normal → `ui.notify(message, type=type)`
- ⚠️ Exception (hors UI slot) → Ignore silencieusement

**Exemple**:
```python
_notify_safe("✅ Opération réussie", type='positive')
_notify_safe("⚠️ Attention requise", type='warning')
```

---

### 2. `force_clear_all_notifications()` (notification_killer.py)

**Signature**:
```python
async def force_clear_all_notifications() -> bool
```

**Description**:  
Nettoyage brutal par "bombardement" de notifications vides. Utilisé pour débloquer interface polluée.

**Techniques**:
1. **Bombardement**: 10 notifications vides (timeout 0.01s)
2. **Remplacement**: Notifications tous types ('ongoing', 'positive', etc.)
3. **Confirmation**: Notification "Interface nettoyée" (2s)
4. **Stabilisation**: Attente 0.5s

**Retour**: 
- `True` si succès
- `False` si erreur

**Exemple**:
```python
import asyncio
success = await force_clear_all_notifications()
print(f"Nettoyage brutal: {'OK' if success else 'ÉCHEC'}")
```

---

### 3. `smart_notification_cleanup()` (notification_killer.py)

**Signature**:
```python
async def smart_notification_cleanup() -> bool
```

**Description**:  
Nettoyage intelligent ciblant les notifications problématiques connues.

**Messages problématiques ciblés**:
- "Phase 1: Génération JSON IA"
- "Phase 2: Transformation JSON → MD"
- "Génération JSON IA pour"
- "Transformation JSON → MD pour"

**Process**:
1. Signal reset global (1s)
2. 5 itérations signaux vides (100ms)
3. Confirmation "Notifications nettoyées" (3s)

**Retour**: 
- `True` si succès
- `False` si erreur

**Exemple**:
```python
success = await smart_notification_cleanup()
```

---

### 4. `emergency_notification_reset()` (notification_killer.py)

**Signature**:
```python
async def emergency_notification_reset() -> bool
```

**Description**:  
Fonction principale combinant nettoyage intelligent + brutal en fallback.

**Workflow**:
1. Essayer `smart_notification_cleanup()` d'abord
2. Si échec → `force_clear_all_notifications()` en dernier recours

**Retour**: 
- `True` si au moins une méthode a réussi
- `False` si toutes échouent

**Exemple**:
```python
import asyncio
reset_success = await emergency_notification_reset()
```

---

### 5. `NotificationCleaner.create_managed_notification()` (Extension)

**Signature**:
```python
def create_managed_notification(
    message: str, 
    type_: str = 'ongoing', 
    timeout: int = 60
) -> object
```

**Description**:  
Crée une notification gérée avec tracking dans liste active.

**Paramètres**:
- `message` (str): Texte notification
- `type_` (str): Type ('ongoing', 'positive', 'negative', 'warning', 'info')
- `timeout` (int): Durée en secondes (60s par défaut)

**Retour**: 
- Objet notification (contrôle manuel)
- `None` si erreur

**Side Effect**: Ajoute à `self.active_notifications`

**Exemple**:
```python
cleaner = NotificationCleaner()
notif = cleaner.create_managed_notification(
    "🔄 Traitement en cours...", 
    type_='ongoing', 
    timeout=30
)
```

---

### 6. `NotificationCleaner.dismiss_notification()` (Extension)

**Signature**:
```python
async def dismiss_notification(notification) -> bool
```

**Description**:  
Ferme une notification spécifique avec vérifications.

**Paramètres**:
- `notification` (object): Objet retourné par `create_managed_notification()`

**Retour**: 
- `True` si fermée avec succès
- `False` si erreur ou déjà fermée

**Side Effect**: Retire de `self.active_notifications`

**Exemple**:
```python
notif = cleaner.create_managed_notification("⏳ Calcul...")
# ... travail ...
await cleaner.dismiss_notification(notif)
```

---

### 7. `NotificationCleaner.force_cleanup_all()` (Extension)

**Signature**:
```python
async def force_cleanup_all() -> int
```

**Description**:  
Nettoyage forcé de TOUTES les notifications gérées par cette instance.

**Méthodes combinées**:
1. Fermer toutes les notifications dans `active_notifications`
2. Signal nettoyage global (notification vide)
3. Confirmation "Interface rafraîchie"
4. Clear de la liste active

**Retour**: Nombre de notifications nettoyées

**Exemple**:
```python
cleaner = NotificationCleaner()
# ... créer plusieurs notifications ...
count = await cleaner.force_cleanup_all()
print(f"{count} notifications nettoyées")
```

---

## Types de Notifications

### Types Supportés (NiceGUI)

| Type | Apparence | Usage OGMA |
|------|-----------|------------|
| `info` | Bleu | Informations générales |
| `positive` | Vert | Succès, confirmations |
| `negative` | Rouge | Erreurs critiques |
| `warning` | Orange | Avertissements |
| `ongoing` | Bleu animé | Opérations en cours (risque de "coincer") |

### Paramètres Additionnels

**Position**:
```python
ui.notify('Message', position='top')     # Haut
ui.notify('Message', position='center')  # Centre
ui.notify('Message', position='bottom')  # Bas (défaut)
```

**Timeout**:
```python
ui.notify('Message', timeout=5)    # 5 secondes
ui.notify('Message', timeout=0)    # Reste jusqu'à fermeture manuelle
ui.notify('Message', timeout=0.1)  # Très rapide (nettoyage)
```

---

## Problèmes Connus & Solutions

### Problème 1: Notifications "Ongoing" Coincées

**Symptôme**: Notification "Phase 1: Génération JSON IA pour Luna..." reste visible indéfiniment.

**Cause**: Type `ongoing` + timeout long + changement contexte UI

**Solution**:
```python
# Au lieu de:
ui.notify("Phase 1: Génération...", type='ongoing', timeout=60)

# Utiliser:
notif = cleaner.create_managed_notification(
    "Phase 1: Génération...", 
    type_='ongoing', 
    timeout=10
)
# Puis fermer explicitement:
await cleaner.dismiss_notification(notif)
```

---

### Problème 2: Notifications Hors Contexte UI

**Symptôme**: `Exception: Client has been deleted` lors d'appels depuis timers/threads.

**Cause**: `ui.notify()` nécessite un contexte UI actif

**Solution**: Utiliser `_notify_safe()` partout
```python
# ❌ Risqué dans timer/thread:
ui.notify("Message")

# ✅ Sécurisé:
_notify_safe("Message")
```

---

### Problème 3: Interface Polluée Après Erreurs

**Symptôme**: Multiples notifications obsolètes visibles

**Solution**: Bouton nettoyage d'urgence
```python
import asyncio
from notification_killer import emergency_notification_reset

async def on_cleanup_button_click():
    await emergency_notification_reset()
    
ui.button('🧹 Nettoyer Notifications', on_click=on_cleanup_button_click)
```

---

## Patterns de Test Recommandés

### Test 1: `_notify_safe()` Context Safe
```python
def test_notify_safe_normal_context():
    """Test notification en contexte UI normal"""
    # Setup: Context UI actif
    # Action: _notify_safe("Test", type='info')
    # Assert: ui.notify appelé avec bons paramètres
```

### Test 2: `_notify_safe()` Hors Contexte
```python
def test_notify_safe_no_context():
    """Test notification hors contexte (exception silencieuse)"""
    # Setup: Mock ui.notify pour lever exception
    # Action: _notify_safe("Test")
    # Assert: Aucune exception propagée
```

### Test 3: Types de Notifications
```python
@pytest.mark.parametrize('type_', ['info', 'positive', 'negative', 'warning', 'ongoing'])
def test_notify_types(type_):
    """Test tous les types supportés"""
    # Action: _notify_safe("Message", type=type_)
    # Assert: Type correctement passé à ui.notify
```

### Test 4: Nettoyage Brutal
```python
async def test_force_clear_all():
    """Test nettoyage brutal notifications"""
    # Action: success = await force_clear_all_notifications()
    # Assert: success == True
    # Assert: ui.notify appelé multiple fois (bombardement)
```

### Test 5: Nettoyage Intelligent
```python
async def test_smart_cleanup():
    """Test nettoyage intelligent ciblé"""
    # Action: success = await smart_notification_cleanup()
    # Assert: success == True
    # Assert: Messages problématiques ciblés
```

### Test 6: NotificationCleaner - Création
```python
def test_cleaner_create_managed():
    """Test création notification gérée"""
    # Setup: cleaner = NotificationCleaner()
    # Action: notif = cleaner.create_managed_notification("Test", type_='ongoing', timeout=30)
    # Assert: notif is not None
    # Assert: notif in cleaner.active_notifications
```

### Test 7: NotificationCleaner - Dismiss
```python
async def test_cleaner_dismiss():
    """Test fermeture notification spécifique"""
    # Setup: cleaner, notif créée
    # Action: success = await cleaner.dismiss_notification(notif)
    # Assert: success == True
    # Assert: notif not in cleaner.active_notifications
```

### Test 8: NotificationCleaner - Force Cleanup All
```python
async def test_cleaner_force_cleanup_all():
    """Test nettoyage toutes notifications gérées"""
    # Setup: cleaner avec 3 notifications actives
    # Action: count = await cleaner.force_cleanup_all()
    # Assert: count == 3
    # Assert: cleaner.active_notifications == []
```

---

## Dépendances

### Modules Python
- `nicegui` (ui.notify)
- `asyncio` (async cleanup)

### Modules OGMA
- `ogma_ng.py` (_notify_safe)
- `notification_killer.py` (nettoyage brutal)
- `extensions/biographie_profil/notification_cleaner.py` (gestion)

### État Global
- Contexte UI NiceGUI actif pour `ui.notify()`

---

## Workflow Typique

### Notification Simple
```python
# 1. Import
from ogma_ng import _notify_safe

# 2. Utilisation
_notify_safe("✅ Opération réussie", type='positive')
```

### Notification Longue Durée (Géré)
```python
# 1. Setup
from extensions.biographie_profil.notification_cleaner import NotificationCleaner
cleaner = NotificationCleaner()

# 2. Créer notification
notif = cleaner.create_managed_notification(
    "🔄 Traitement en cours...", 
    type_='ongoing', 
    timeout=60
)

# 3. Travail
process_long_task()

# 4. Fermer explicitement
await cleaner.dismiss_notification(notif)
_notify_safe("✅ Traitement terminé", type='positive')
```

### Nettoyage D'urgence
```python
# 1. Import
from notification_killer import emergency_notification_reset

# 2. Déclencher nettoyage
success = await emergency_notification_reset()

if success:
    print("Interface nettoyée")
else:
    print("Échec nettoyage")
```

---

## Notes d'Implémentation

### Design Patterns
- **Defensive Programming**: `_notify_safe()` ignore exceptions hors contexte
- **Layered Cleanup**: Intelligent → Brutal (fallback)
- **Managed Resources**: `NotificationCleaner` track notifications actives

### Limitations
- ⚠️ `ui.notify()` nécessite contexte UI actif
- ⚠️ Type `ongoing` peut "coincer" si timeout trop long
- ⚠️ Nettoyage brutal = expérience utilisateur dégradée (flash notifications)

### Best Practices
1. ✅ Toujours utiliser `_notify_safe()` dans code asynchrone/timers
2. ✅ Fermer explicitement notifications `ongoing` longues
3. ✅ Timeout court (≤5s) pour notifications non critiques
4. ✅ Bouton nettoyage d'urgence accessible dans UI

---

**Dernière mise à jour**: 2025-11-05  
**Tests prévus**: 10 tests (voir section Patterns de Test)  
**Couverture estimée**: 100% (3 fonctions core + NotificationCleaner)
