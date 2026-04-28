# Configuration des paramètres d'extension

**Sources vérifiées** : `data/*.json` (inspection directe), `extensions/cognitive_mirror/config_v2.py` (structure), `.github/copilot-instructions.md` (règle synchronisation)

---

## Principe de priorité

Chaque extension peut avoir un fichier JSON dans `data/` qui **prend la priorité sur les valeurs Python par défaut** au runtime. Ce fichier est la source de vérité pour un utilisateur qui clone le dépôt.

Au démarrage, l'extension lit son JSON de configuration. Si le fichier n'existe pas, les constantes `DEFAULT_*` Python prennent le relais. Mais si le JSON est présent, il écrase les valeurs Python.

---

## Fichiers de configuration actifs

| Fichier | Extension | Contenu |
|---|---|---|
| `data/introspection_settings_v2.json` | Cognitive Mirror | Activation, paramètres dialogue |
| `data/organic_planner_settings.json` | Organic Planner | Activation, briefing, rappels |
| `data/capability_advisor_config.json` | Capability Advisor | Activation, seuils de suggestion |
| `data/ego_compiled.json` | Ego System | Structure traits compilés (sortie) |
| `data/journal_reves.json` | Dream Engine | Journal des rêves (sortie) |

---

## Règle de synchronisation commit

Quand un fichier `extensions/*/config*.py` est modifié, le JSON correspondant dans `data/` doit être commité dans le même push. Un nouvel utilisateur qui clone OGMA charge le JSON, pas les constantes Python.

```bash
git status                          # Vérifier les JSON data/ modifiés
git add data/[extension]_settings.json
git commit -m "sync: JSON data/ aligné sur config Python"
```

---

## Structure type d'un fichier de config extension

```json
{
  "enabled": true,
  "version": "2.1",
  "settings": {
    "param1": "valeur",
    "param2": 42
  }
}
```

Le champ `enabled` est systématiquement présent et contrôle l'activation de l'extension.

---

## Données de sortie vs configuration

Certains fichiers JSON dans `data/` sont des **sorties** générées par les extensions (ex: `ego_compiled.json`, `journal_reves.json`) et non des configurations à éditer manuellement. La distinction est importante : modifier ces fichiers manuellement peut corrompre l'état de l'extension.
