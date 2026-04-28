# Gestionnaire de profils

**Sources vérifiées** : `profile_manager.py`, `profils_sauvegardes/`

---

## Concept de profil unique

OGMA est conçu autour du principe d'une seule entité IA par instance. Un "profil" représente l'état complet de cette entité : tous ses souvenirs, son ego compilé, ses conversations, ses paramètres. Le `ProfileManager` gère la sauvegarde, la restauration et la suppression de cet état.

---

## Sauvegarde d'un profil

Une sauvegarde crée une archive ZIP dans `profils_sauvegardes/`. Elle capture :

- La base SQLite de mémoire (`data/memory/`)
- L'ego compilé (`data/ego_compiled.json`)
- Les conversations (`data/conversations/`)
- Les identités et paramètres (`data/identities.json`, `data/settings.json`)
- Le contexte persistant (`data/persistent_context.txt`)

La compression est activée par défaut. La rotation des backups limite le dossier à **10 sauvegardes** maximum : les plus anciennes sont supprimées automatiquement.

---

## Suppression d'un profil

La suppression supprime les souvenirs et données personnelles tout en **préservant les mémoires fondatrices** (`SEED_*`). Ces seeds contiennent la connaissance des phrases magiques et de l'identité fondamentale de l'IA — ils ne doivent pas disparaître avec l'identité d'un utilisateur spécifique.

La liste des seeds préservés est définie dans le constructeur du `ProfileManager`.

---

## Restauration

La restauration décompresse une archive et écrase les fichiers actuels. Cette opération est irréversible sans sauvegarde préalable du profil courant. L'application doit être redémarrée après restauration pour recharger les contrôleurs IA.

---

## Lien avec `IdentityManager`

`ProfileManager` opère sur les fichiers bruts. `IdentityManager` gère les métadonnées d'identité (noms, relations). Les deux systèmes sont indépendants mais complémentaires : changer de profil nécessite de mettre à jour l'identité active en conséquence.
