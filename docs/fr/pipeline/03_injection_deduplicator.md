# Déduplication des injections

**Source vérifiée** : `injection_deduplicator.py`

---

## Problème résolu

OGMA injecte des informations dans chaque requête via plusieurs canaux indépendants : le prompt ego, l'Archiviste, les extensions de métacognition. Chacun peut apporter les mêmes souvenirs sans le savoir. Avant ce module, un même souvenir pouvait apparaître trois fois dans une requête, gaspillant jusqu'à 4 500 tokens par message.

`InjectionDeduplicator` est le gardien qui surveille ce qui a déjà été injecté et empêche les doublons.

---

## Mécanisme de suivi

### Suivi par identifiant de souvenir

Chaque souvenir a un identifiant (ex. `usr-abc123`, `#MEM_EGO_456`). Le module maintient un ensemble d'identifiants déjà injectés dans la session en cours. Quand un nouveau contenu est proposé pour injection, ses identifiants sont extraits par regex et comparés à cet ensemble.

Les patterns regex couvrent plusieurs formats d'identifiants : identifiants ego (`#MEM_EGO_*`), identifiants utilisateur (`usr-*`), identifiants auto-censure (`AUTO_CENSURE_*`), et formats génériques.

### Suivi par hash de contenu

En complément, un hash simplifié du début du texte (15 premiers mots) permet de détecter les contenus identiques sans identifiant explicite. Ce mécanisme est délibérément conservateur : il utilise suffisamment de mots pour éviter les faux positifs sur des textes similaires mais sémantiquement différents.

### Système de cooldown

Un souvenir déjà injecté entre en "cooldown" : il ne peut plus être réinjecté tant que 3 tours de conversation ne se sont pas écoulés (seuil configurable). Ce mécanisme évite la répétition des informations récentes sans les bloquer définitivement — un souvenir pertinent revient naturellement dans les requêtes suivantes.

---

## API publique

| Fonction | Rôle |
|---|---|
| `reset_session()` | Remet à zéro tous les trackers (nouvelle conversation) |
| `register_injection(source, content, ...)` | Enregistre un contenu comme injecté |
| `check_archiviste_injection(memory_id)` | Vérifie si un souvenir est déjà connu |
| `register_archiviste_injection(memory_id, content)` | Déclare l'injection d'un souvenir Archiviste |
| `register_ego_prompt_injection(content)` | Déclare l'injection du prompt ego complet |
| `increment_message_count()` | Avance le compteur de cooldown |
| `is_on_cooldown(memory_id)` | Vérifie le cooldown d'un souvenir |

---

## Limites

- La déduplication sémantique (détection de souvenirs similaires en contenu mais avec des IDs différents) est implémentée mais **désactivée par défaut** (`enable_semantic_dedup = False`). Le risque de faux positifs sur des nuances importantes justifie cette prudence.
- Le module est stateful : il maintient son état pour toute la durée d'une conversation et doit être explicitement remis à zéro entre les conversations via `reset_session()`.
