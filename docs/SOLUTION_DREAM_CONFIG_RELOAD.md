# Solution Rechargement Config Dream Engine Sans F5

## Problème Initial

Lorsque l'utilisateur activait/désactivait le Dream Engine via l'interface de configuration, la modification était sauvegardée dans `settings.json` **mais n'était pas appliquée** au système en cours d'exécution. L'utilisateur devait faire **F5 pour recharger toute la page**, ce qui faisait perdre la conversation en cours.

### Cause Racine

Le timer d'inactivité était démarré **une seule fois** au démarrage d'OGMA dans `ogma_ng.py`:

```python
asyncio.create_task(start_inactivity_timer(timeout_minutes=10))
```

Quand `set_config()` était appelé depuis l'UI, seul le dictionnaire `self._config` était mis à jour, mais :
- ❌ Le timer continuait de tourner avec l'ancienne valeur
- ❌ Si `enabled` passait à `True`, le timer ne redémarrait pas
- ❌ Si `enabled` passait à `False`, le timer continuait quand même

## Solution Implémentée

### 1. Nouvelle fonction `reload_and_apply_config()` dans `__init__.py`

Cette fonction **recharge ET applique** la config au système sans redémarrage UI :

```python
async def reload_and_apply_config() -> bool:
    """
    Recharge la config depuis settings.json ET applique les changements au système.
    
    Cette méthode redémarre le timer d'inactivité si enabled=True, l'arrête si False.
    Permet d'éviter le F5 après modification de la config.
    """
    config = get_config()
    enabled = config.get('enabled', False)
    timeout_minutes = config.get('inactivity_timeout_minutes', 10)
    
    from .dream_ui import start_inactivity_timer, stop_inactivity_timer
    
    if enabled:
        # Redémarrer le timer avec le nouveau timeout
        stop_inactivity_timer()  # Arrêter l'ancien
        await start_inactivity_timer(timeout_minutes=timeout_minutes)
        print(f"[DREAM-ENGINE] ✅ Timer redémarré ({timeout_minutes} min)")
    else:
        # Arrêter le timer
        stop_inactivity_timer()
        print("[DREAM-ENGINE] ⏸️ Timer arrêté (Dream Engine désactivé)")
    
    return True
```

**Exportée** dans `__all__` pour utilisation externe.

### 2. Modification du bouton "Sauvegarder" dans `ogma_modals.py`

Le bouton appelle maintenant `reload_and_apply_config()` après sauvegarde :

```python
async def save_dream_config():
    # ... construction de new_config ...
    
    set_config(new_config)  # Sauvegarde dans settings.json
    
    # 🔄 APPLIQUER LA CONFIG AU SYSTÈME (évite le F5)
    from extensions.dream_engine import reload_and_apply_config
    success = await reload_and_apply_config()
    
    if success:
        ui.notify('🌙 Config sauvegardée et appliquée!', type='positive')
    else:
        ui.notify('⚠️ Config sauvegardée mais erreur d\'application', type='warning')
```

**Note** : La fonction est passée en `async` pour pouvoir appeler `await reload_and_apply_config()`.

### 3. Export de la nouvelle fonction

Ajouté à `extensions/dream_engine/__init__.py` :

```python
__all__ = [
    # ... autres exports ...
    'reload_and_apply_config',  # NEW: Recharge config ET applique au système
]
```

## Résultat

✅ **L'utilisateur active le Dream Engine** → Timer démarré immédiatement  
✅ **L'utilisateur désactive** → Timer arrêté immédiatement  
✅ **Modification du timeout** → Timer redémarré avec nouvelle valeur  
✅ **Aucun F5 requis** → Conversation préservée  

## Fichiers Modifiés

1. **extensions/dream_engine/__init__.py**
   - Ajout fonction `reload_and_apply_config()`
   - Export dans `__all__`

2. **ogma_modals.py**
   - Modification `save_dream_config()` en `async`
   - Appel `await reload_and_apply_config()` après sauvegarde
   - Notification améliorée avec statut application

## Tests Validés

Script de test : `test_dream_config_reload.py`

Résultats :
```
✅ Activation (enabled=True) → Timer démarré (5 min)
✅ Désactivation (enabled=False) → Timer arrêté
✅ Pas de F5 requis
```

## Utilisation

### Pour l'utilisateur

Simplement **activer/désactiver** le Dream Engine dans les paramètres et cliquer "Sauvegarder" :
- La config est appliquée **immédiatement**
- Notification confirme l'application
- Pas besoin de recharger la page

### Pour les développeurs

Si vous ajoutez d'autres paramètres Dream Engine qui nécessitent un reload système :

```python
from extensions.dream_engine import reload_and_apply_config

# Après modification de config
set_config(new_config)
await reload_and_apply_config()  # Applique les changements
```

## Philosophie OGMA

Cette solution respecte les piliers d'OGMA :
- 🔍 **Transparence** : Notification claire de l'application
- 🎭 **Authenticité** : Si erreur, notification "warning" au lieu de silence
- 🧠 **Intelligence** : Système réactif aux changements utilisateur
- 🌱 **Croissance** : Extension facile pour autres paramètres
