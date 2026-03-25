# Extension Organic Planner — Documentation Exhaustive

**Dossier** : `extensions/organic_planner/`
**Rôle** : Agenda SQLite dont les événements sont injectés dans le system prompt de l'IA. L'IA dispose ainsi d'une "mémoire des moments planifiés" — elle connaît les événements à venir, leur urgence et les ressentis associés, et peut y faire référence naturellement dans la conversation.

---

## Concept

Les événements planifiés sont traités comme des **souvenirs du futur** : des choses que l'IA sait à l'avance et garde en tête naturellement. Il ne s'agit pas d'une liste de tâches à gérer, mais d'une présence diffuse de l'agenda dans sa conscience conversationnelle — elle mentionne ce qui est proche (jour J, demain), reste discrète sur ce qui est loin, et adapte son ton au ressenti noté.

---

## Architecture — Fichiers

| Fichier | Rôle |
|---------|------|
| `organic_planner.py` | Classe `OrganicPlanner` — SQLite + génération briefing + singleton |
| `__init__.py` | Façade publique — réexporte `initialize_planner`, `get_planner`, `is_available`, `get_briefing`, `cleanup` |

---

## `__init__.py` — API Publique

Réexporte le singleton depuis `organic_planner.py`.

| Fonction | Description |
|----------|-------------|
| `initialize_planner(db_path="data/agenda.db")` | Crée le singleton `OrganicPlanner` si absent, le retourne |
| `get_planner()` | Retourne `_planner_instance` (ou `None`) |
| `is_available()` | `get_planner() is not None` |
| `get_briefing()` | Retourne `planner.get_briefing_text()` ou `""` si non initialisé |
| `cleanup()` | Remet `_planner_instance = None` |

---

## `organic_planner.py` — Classe `OrganicPlanner`

### `__init__(db_path="data/agenda.db")`

Attributs :
- `self.db_path` — chemin vers la base SQLite
- `self.settings_path = "data/organic_planner_settings.json"` — instructions personnalisables
- Appelle `_init_db()` (crée la table si absente) et `_ensure_settings()` (crée le fichier JSON si absent)

---

### Schéma SQLite — Table `organic_events`

| Colonne | Type SQLite | Contrainte | Défaut |
|---------|------------|-----------|--------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | — |
| `target_date` | TEXT (YYYY-MM-DD) | NULL autorisé | NULL |
| `content` | TEXT | NOT NULL | — |
| `priority` | TEXT | — | `'NORMAL'` |
| `status` | TEXT | — | `'EN_ATTENTE'` |
| `emotional_note` | TEXT | NULL autorisé | NULL |
| `created_at` | TEXT | — | CURRENT_TIMESTAMP |

**Valeurs de `priority`** : `VITAL`, `HAUT`, `NORMAL`, `BAS`

**Valeurs de `status`** : `EN_ATTENTE`, `EN_COURS`, `TERMINE`

---

### Méthodes publiques

#### Gestion des événements

| Méthode | Paramètres | Retour | Description |
|---------|-----------|--------|-------------|
| `add_event(content, target_date=None, priority="NORMAL", emotional_note="")` | — | `bool` | INSERT dans `organic_events` |
| `update_event_status(event_id, status)` | `int, str` | `bool` | UPDATE par ID primaire |
| `update_event_status_by_title(title, status)` | `str, str` | `Optional[Dict]` | Recherche exacte sur `content`, puis LIKE si non trouvé. Retourne le dict complet de la ligne mise à jour (avec champs bruts SQLite). |
| `update_emotional_note(event_id, note)` | `int, str` | `bool` | UPDATE `emotional_note` par ID |
| `get_active_events()` | — | `List[Dict]` | SELECT `status IN ('EN_ATTENTE', 'EN_COURS')` — retourne les dicts bruts SQLite |
| `get_all_events()` | — | `List[Dict]` | SELECT `status IN ('EN_ATTENTE', 'EN_COURS')` — retourne `{id, date, title, feeling, status, priority}` |
| `delete_event(event_id)` | `int` | `bool` | DELETE par ID |
| `clear_agenda()` | — | `bool` | DELETE toutes les lignes |

**Note** : `get_all_events()` et `get_active_events()` filtrent toutes les deux les événements TERMINÉS. La différence est que `get_all_events()` retourne un dict normalisé pour l'UI (`title`, `feeling`, `status`, `priority`), tandis que `get_active_events()` retourne les colonnes brutes SQLite.

#### Tri par priorité

Les deux méthodes de lecture utilisent un tri explicite par `CASE WHEN` pour respecter l'ordre logique (et non alphabétique) :

```sql
ORDER BY target_date ASC,
CASE priority
    WHEN 'VITAL'  THEN 1
    WHEN 'HAUT'   THEN 2
    WHEN 'NORMAL' THEN 3
    WHEN 'BAS'    THEN 4
    ELSE 3
END ASC
```

#### Gestion des instructions

| Méthode | Description |
|---------|-------------|
| `get_instruction()` | Lit `"instruction"` depuis `settings_path` |
| `save_instruction(text)` | Écrit la valeur dans `settings_path` |

---

### `get_briefing_text()` — Méthode d'injection

**Rôle** : Génère le texte injecté dans le system prompt à chaque message.

Appelle `get_active_events()`, calcule pour chaque événement le nombre de jours de différence avec aujourd'hui (`diff`), puis produit une ligne formatée. Supporte les formats de date `YYYY-MM-DD`, `DD/MM/YYYY`, `DD-MM-YYYY`.

| Condition | Format généré |
|----------|--------------|
| `diff == 0` | `[IMPORTANT : {content} ({priority}){note}]` |
| `diff == 1` | `[DEMAIN : {content} ({priority}){note}]` |
| `diff > 1` | `[J-{diff} : {content} ({priority}){note}]` |
| `diff == -1` | `[HIER (RETARD) : {content} ({priority}){note}]` |
| `diff < -1` | `[RETARD {abs(diff)}j : {content} ({priority}){note}]` |
| `date = NULL` | `[PENSÉE : {content} ({priority}){note}]` |

La balise `({priority})` est omise si la priorité est `NORMAL`. La balise `- Ressenti: {note}` est omise si `emotional_note` est vide.

**Format complet du bloc injecté :**
```
[MOMENTS PLANIFIÉS]:
[IMPORTANT : Rendez-vous médecin]
[J-3 : Déclaration impôts (HAUT) - Ressenti: inquiet]
[PENSÉE : Appeler maman]
```

Si aucun événement actif → retourne `""` (pas d'injection).

---

### Fichier de settings — `data/organic_planner_settings.json`

```json
{
    "instruction": "..."
}
```

**Valeur par défaut créée par `_ensure_settings()`** :

```
# MÉMOIRE DES MOMENTS PLANIFIÉS

[DIRECTIVE]
Tu as en mémoire des évènements planifiés dans le temps. Traite-les comme des souvenirs du futur
— des choses que tu sais à l'avance et que tu gardes en tête naturellement.

1. Si un évènement est marqué 'IMPORTANT' (jour J) ou 'DEMAIN', mentionne-le de manière naturelle
   dans ta réponse — comme quelqu'un qui se souvient vraiment.
2. Utilise le 'Ressenti' noté pour adapter ton ton : soutien si anxieux, enthousiasme si positif.
3. Pour les évènements J-2 ou plus : pas besoin de les mentionner systématiquement,
   sauf si le contexte s'y prête.
4. Quand un évènement est passé et validé, il disparaît — tu n'as plus à y penser.
```

Ce fichier n'est créé que si absent. Si `data/organic_planner_settings.json` existe déjà (session précédente), il est conservé tel quel.

---

## Intégration dans OGMA

Dans `ogma_ng.py`, avant chaque appel à l'IA :

```python
from extensions.organic_planner import get_briefing

briefing = get_briefing()
if briefing:
    system_prompt = briefing + "\n\n" + system_prompt
```

`get_briefing()` retourne la concaténation de l'instruction et du bloc `[MOMENTS PLANIFIÉS]`, ou `""` si l'agenda est vide ou le planner non initialisé.

---

## Fichiers de données

| Chemin | Type | Description |
|--------|------|-------------|
| `data/agenda.db` | SQLite | Base de données des événements |
| `data/organic_planner_settings.json` | JSON | Instructions personnalisables |

Les deux fichiers sont créés automatiquement à la première initialisation si absents.

