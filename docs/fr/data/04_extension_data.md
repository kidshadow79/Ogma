# Données des extensions

**Sources vérifiées** : `data/extensions/` (inspection directe), `data/*.json` (inspection directe)

---

## `data/extensions/`

Dossier dédié aux données propres aux extensions. Actuellement :

| Fichier | Extension | Rôle |
|---|---|---|
| `biography_config.json` | Biographie Profil | Configuration du module biographie |

Chaque extension peut créer son propre sous-dossier ici si elle a besoin de données persistantes volumineuses.

---

## Fichiers JSON racine `data/`

Les fichiers JSON à la racine de `data/` sont soit des **configurations** d'extensions, soit des **sorties** générées :

**Configurations** (éditables, priorité sur Python) :
- `introspection_settings_v2.json` — Cognitive Mirror
- `organic_planner_settings.json` — Organic Planner
- `capability_advisor_config.json` + `capability_advisor_prompt.txt` — Capability Advisor

**Sorties générées** (ne pas modifier manuellement) :
- `ego_compiled.json` — traits ego compilés par l'EgoCompiler
- `journal_reves.json` + `journal_reves.md` — journal rêves du Dream Engine
- `archiviste_tokens_debug.jsonl` — log de tokens Archiviste (JSONL append-only)

**Données de référence** (templates/defaults) :
- `identities.default.json` — profil identité par défaut (bootstrap)
- `instructions_defaults.json` + `instructions_defaults_en.json` — prompts système par défaut
- `persistent_context.default.txt` + `persistent_context.default_en.txt` — contexte persistant par défaut

---

## `data/cognitive_cache/`

Cache cognitif par conversation. Fichiers JSON nommés par `conv_id`. Maximum 10 conversations conservées.

---

## `data/generated_images/`

Images générées par l'extension Text2Image. Sauvegardées avec un nom horodaté.

---

## `data/projects/`

Données isolées par projet pour l'extension Project RAG. Chaque projet a son propre sous-dossier avec sa base SQLite et son index FAISS.
