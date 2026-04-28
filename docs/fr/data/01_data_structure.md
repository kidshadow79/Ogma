# Structure des données persistantes

**Sources vérifiées** : `data/` (inspection directe), `data/settings.example.json` (structure)

---

## Vue d'ensemble

Le dossier `data/` est la source de vérité pour toutes les données persistantes d'OGMA. Rien n'est stocké en base de données externe — tout réside dans ce dossier, ce qui simplifie les backups et la portabilité.

---

## `settings.json` — Configuration centrale

Fichier de configuration principal. Contient les paramètres pour chaque contrôleur IA, les APIs, le TTS et les préférences utilisateur.

```json
{
  "chat_api": {"provider": "...", "api_key": "...", "backend_type": "API"},
  "reasoning_api": {"provider": "...", "api_model": "..."},
  "embedding_api": {"provider": "...", "backend_type": "API"},
  "tts": {"engine": "...", "voice": "..."},
  "ui_lang": "fr"
}
```

`settings.example.json` fournit un modèle de configuration sans clés API.

---

## `memory/` — Mémoire vectorielle

Contient la base SQLite (`memory.db`) et l'index FAISS. Backups automatiques dans `memory/backup/` (rotation 10 fichiers).

---

## `conversations/` — Historique conversations

Fichiers JSON horodatés (`YYYY-MM-DD_HH-MM-SS_xxxx.json`) et `index.json` léger. Format v2.2+ inclut les résumés intégrés directement dans les fichiers de conversation.

---

## `biographies/` — Portraits utilisateurs

Portraits structurés générés par l'extension `biographie_profil`. Un fichier par identité utilisateur.

---

## `cognitive_cache/` — Cache cognitif par conversation

Fichiers JSON par conversation (`{conv_id}.json`). Maximum 10 conservés.

---

## `extensions/` — Données des extensions

Chaque extension peut avoir ses propres données sous `data/extensions/{nom_extension}/`. Ces données suivent le cycle de vie de l'extension.

---

## Fichiers de configuration extensions (à la racine de `data/`)

Ces fichiers JSON prennent la priorité sur les valeurs Python par défaut au runtime :

| Fichier | Extension |
|---|---|
| `introspection_settings_v2.json` | Cognitive Mirror |
| `organic_planner_settings.json` | Organic Planner |
| `capability_advisor_config.json` | Capability Advisor |
| `ego_compiled.json` | Ego System |

**Important** : un nouvel utilisateur qui clone OGMA charge ces JSON, pas les constantes Python. Ils doivent rester synchronisés avec le code.

---

## `i18n/` — Traductions

Dictionnaires de traduction par langue. Chargés par `utils/i18n.py`.

---

## `identities.json` — Identités utilisateurs

Liste des profils utilisateurs actifs. `identities.default.json` fournit la configuration bootstrap.

---

## `persistent_context.txt` — Contexte permanent

Texte libre injecté dans chaque prompt système. Permet à l'utilisateur de définir un contexte permanent ("je suis développeur, je travaille sur...").

---

## `journal_reves.json` / `journal_reves.md`

Journal des rêves du Dream Engine. Format JSON queryable par l'IA, format Markdown pour lecture humaine.
