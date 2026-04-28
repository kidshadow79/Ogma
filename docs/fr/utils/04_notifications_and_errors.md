# Notifications, erreurs NiceGUI et garde client

**Sources vérifiées** : `notification_killer.py`, `nicegui_error_handler.py`, `nicegui_client_guard.py`

---

## Problème de fond

NiceGUI est un framework web réactif : plusieurs clients peuvent se connecter simultanément, et un client peut se déconnecter en pleine opération (fermeture d'onglet, perte réseau). Sans protection, ces déconnexions provoquent des `KeyError` sur `Client.instances` qui remontent en stack trace.

Par ailleurs, des notifications peuvent rester visibles dans l'interface même après leur expiration (notifications "fantômes").

---

## `nicegui_client_guard.py` — Décorateur de protection

Fournit le décorateur `@safe_client_operation`. Avant d'exécuter une fonction, il vérifie :
1. Que `Client.current` existe
2. Que l'identifiant du client est toujours dans `Client.instances`

Si l'une de ces conditions échoue, la fonction est ignorée silencieusement (retourne `None`). Les `KeyError` et `AttributeError` sur `Client.current` sont capturées et loggées en debug, jamais en erreur visible.

---

## `nicegui_error_handler.py` — Timeout et tracking d'activité

Deux mécanismes :

**Patch timeout** : le timeout interne de NiceGUI pour les timers est augmenté de 60 secondes à **30 minutes** (`TIMER_TIMEOUT_OVERRIDE = 1800.0`). Sans ce patch, les longues générations en streaming déclenchent des déconnexions de client.

**Tracking activité** : `track_client_activity(client_id)` est appelée à chaque interaction utilisateur. `get_client_last_activity()` retourne le timestamp. Un `ACTIVITY_GRACE_PERIOD` de 10 minutes protège les clients actifs de la déconnexion automatique même pendant une longue génération.

---

## `notification_killer.py` — Nettoyage notifications fantômes

Certaines notifications NiceGUI restent visibles après leur traitement (notifications de génération en cours). `force_clear_all_notifications()` utilise trois techniques de force brute :
1. Bombardement de notifications vides à timeout minimal
2. Notifications de remplacement pour chaque type (`ongoing`, `positive`, `negative`, `warning`)
3. Notification de confirmation rapide pour nettoyer

Cette fonction est accessible via un bouton dans l'interface OGMA.
