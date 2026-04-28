# Protection des phrases magiques

**Source vérifiée** : `magic_phrase_guard.py`

---

## Problème résolu

Les "phrases magiques" sont des expressions spéciales dans les réponses de l'IA principale qui déclenchent des actions automatiques : créer un souvenir, lancer une introspection, activer la webcam, générer une image. Ces déclencheurs fonctionnent en analysant le contenu des messages en temps réel.

Un problème surgit lors du chargement d'une conversation historique : les messages anciens contenant ces phrases seraient analysés à nouveau, déclenchant des actions qui avaient déjà eu lieu. `magic_phrase_guard.py` empêche ce double déclenchement.

---

## Double protection

Le module implémente deux mécanismes complémentaires :

### 1. Flag temporel global

Quand une conversation est chargée, `activate_loading_mode()` lève un flag global. Tant que ce flag est actif, `should_process_magic_phrase()` retourne `False` pour tous les messages, quelle que soit leur source. Le flag tombe automatiquement après 5 secondes (filet de sécurité) ou dès que le chargement est terminé via `deactivate_loading_mode_delayed()` (délai de 1,5 secondes par défaut).

### 2. Métadonnée de message

Chaque message chargé depuis l'historique reçoit la métadonnée `from_history: True`. Cette marque permanente permet une vérification supplémentaire, même si le flag temporel est déjà tombé.

---

## API pour les extensions

Toutes les extensions qui traitent des phrases magiques doivent appeler la même fonction :

```python
if should_process_magic_phrase(current_message, "NOM_EXTENSION"):
    # Traiter la phrase magique...
else:
    # Ignorer — message historique
```

La fonction accepte le dictionnaire de message et le nom de l'extension (pour les logs). Elle centralise ainsi la logique de protection et garantit un comportement cohérent entre toutes les extensions.

---

## Statistiques intégrées

Le module maintient des compteurs : nombre total de déclenchements bloqués, répartition par mécanisme de protection (flag vs métadonnée), liste des extensions protégées dans la session. Ces données sont accessibles pour le diagnostic mais ne sont pas exposées dans l'interface utilisateur.
