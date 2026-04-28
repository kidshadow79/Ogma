# Profils sauvegardés, biographies et identités

**Sources vérifiées** : `profils_sauvegardes/` (inspection directe), `data/biographies/` (inspection directe), `data/identities.json` (inspecté dans sessions précédentes)

---

## `profils_sauvegardes/`

Dossier de backups de profils complets créés par `profile_manager.py`. Chaque backup est une archive ZIP contenant l'intégralité des données d'un profil utilisateur (mémoire, conversations, identité, ego).

Structure : `profils_sauvegardes/configs/` — sous-dossier pour les backups de configuration.

La rotation est limitée à 10 backups. Le plus ancien est supprimé automatiquement lors de la création du 11ème.

---

## `data/biographies/`

Portraits structurés des utilisateurs générés par l'extension `biographie_profil`. Le dossier contient un sous-dossier par identité utilisateur :

```
data/biographies/
├── utilisateur/   ← profil générique
└── yohan/         ← profil Yohan Brocard
```

Chaque sous-dossier contient :
- Volume 1 : synthèse factuelle des souvenirs FAISS marqués importants
- Volume 2 : journal narratif en 10 sections

---

## `data/identities.json`

Liste des identités utilisateur actives avec leurs paramètres (nom, langue préférée, profil IA associé). `data/identities.default.json` est le template bootstrap utilisé à la première installation.

---

## `data/i18n/`

Dictionnaires de traduction de l'interface :
- `ui_fr.json` — interface en français
- `ui_en.json` — interface en anglais

Chargés par `utils/i18n.py` à la demande, mis en cache par langue.
