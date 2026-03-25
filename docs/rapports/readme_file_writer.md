# Extension File Writer — Documentation Exhaustive

**Dossier** : `extensions/file_writer/`
**Version** : 1.0.0
**Rôle** : Détection automatique des demandes de création de fichiers Markdown dans les messages utilisateur, extraction du contenu généré par l'IA, et sauvegarde sur disque.

---

## Vue d'ensemble

L'extension File Writer opère en trois étapes successives orchestrées par `FileWriterAgent` :

```
Message utilisateur
      │
      ▼
RequestDetector      ← Détecte si la demande porte sur un fichier .md
      │ FileRequest(is_request, title, confidence)
      ▼
MarkdownExtractor    ← Extrait le contenu markdown de la réponse IA
      │ Optional[str]
      ▼
FileSaver            ← Sauvegarde physique dans data/uploads/
      │ Optional[str] (chemin fichier)
      ▼
Résultat retourné à ogma_ng.py
```

Un second mode, `DocumentGenerator`, génère un document complet via un appel IA dédié asynchrone (en arrière-plan), distinct de la réponse conversationnelle.

---

## Architecture — Fichiers

| Fichier | Classe principale | Rôle |
|---------|-------------------|------|
| `__init__.py` | — | API publique singleton |
| `request_detector.py` | `RequestDetector`, `FileRequest` | Détection par regex |
| `markdown_extractor.py` | `MarkdownExtractor` | Extraction contenu MD |
| `file_saver.py` | `FileSaver` | Sauvegarde disque |
| `file_writer_agent.py` | `FileWriterAgent` | Orchestrateur pipeline |
| `document_generator.py` | `DocumentGenerator` | Génération IA dédiée async |

---

## API Publique (`__init__.py`)

Singleton global : `_file_writer_agent : Optional[FileWriterAgent]`

| Fonction | Paramètres | Description |
|----------|-----------|-------------|
| `initialize_file_writer(uploads_dir, debug)` | `str, bool` | Crée `FileWriterAgent`, initialise `uploads_dir`, retourne instance ou `None` |
| `is_available()` | — | `True` si singleton initialisé |
| `get_file_writer()` | — | Retourne le singleton |
| `detect_request(user_message)` | `str` | Raccourci → `FileWriterAgent.is_file_request()` |
| `process_response(user_message, ai_response)` | `str, str` | Pipeline complet, retourne chemin fichier ou `None` |
| `get_statistics()` | — | `{requests_detected, files_saved, total_bytes, success_rate}` |
| `cleanup()` | — | Remet `_file_writer_agent` à `None` |

---

## `request_detector.py` — Classe `FileRequest` et `RequestDetector`

### Dataclass `FileRequest`

| Champ | Type | Description |
|-------|------|-------------|
| `is_request` | `bool` | Demande détectée |
| `title` | `Optional[str]` | Titre extrait ou déduit |
| `extension` | `str` | Toujours `"md"` |
| `confidence` | `float` | Score de confiance 0.0–1.0 |
| `pattern_matched` | `Optional[str]` | Nom du pattern qui a matché |

### Classe `RequestDetector`

**`__init__(debug=False)`** — initialise 8 patterns de détection et 6 patterns d'extraction de titre.

#### Patterns de détection (avec seuil de confiance)

| Pattern | Exemple | Confiance |
|---------|---------|-----------|
| `/doc ` | `/doc architecture` | 0.98 |
| verbe + `.md` explicite | `génère un fichier test.md` | 0.95 |
| verbe + `fichier markdown` | `crée un fichier markdown` | 0.90 |
| verbe + `document markdown/.md` | `rédige un document .md` | 0.90 |
| verbe + `markdown sur/pour/de` | `écris du markdown sur Python` | 0.85 |
| verbe + `fichier sur/pour/de` | `fais un fichier sur la mémoire` | 0.75 |
| verbe + `doc sur/pour/de` | `prépare un doc de refactoring` | 0.70 |

**Méthodes publiques :**

| Méthode | Retour | Description |
|---------|--------|-------------|
| `detect(message)` | `FileRequest` | Teste tous les patterns, retourne le meilleur match |
| `is_file_request(message)` | `bool` | Raccourci booléen |
| `extract_title(message)` | `Optional[str]` | Extrait titre depuis le message |

**Méthodes privées :**

| Méthode | Description |
|---------|-------------|
| `_extract_title(message)` | Essaie 6 patterns d'extraction → fallback 3–5 derniers mots |
| `_clean_title(title)` | Retire ponctuation, remplace espaces par `_`, limite à 50 chars, lowercase |

---

## `markdown_extractor.py` — Classe `MarkdownExtractor`

**Rôle** : Extraire le contenu Markdown depuis la réponse brute de l'IA.

**`__init__(debug=False)`** — pas d'état interne.

### Stratégie d'extraction (2 étapes, ordre prioritaire)

**Étape 1 — Blocs de code** : Cherche ` ```md ` ou ` ```markdown ` avec gestion des blocs imbriqués via un compteur de profondeur (`depth`). La méthode `_find_matching_end()` navigue niveau par niveau pour trouver le vrai ` ``` ` de fermeture.

**Étape 2 — Markdown brut** : Si aucun bloc trouvé, détecte la première ligne header (`#`) ou liste (`- `, `* `, `1. `), extrait jusqu'à 3 lignes vides consécutives, minimum 50 chars.

| Méthode | Description |
|---------|-------------|
| `extract(ai_response)` | Point d'entrée — essaie bloc code puis markdown brut |
| `_extract_code_block(text)` | Extrait contenu entre ` ```md/markdown ` ... ` ``` ` |
| `_find_matching_end(text)` | Compteur imbrication pour trouver la fermeture exacte |
| `_looks_like_markdown(text)` | Vérifie headers, listes, liens, code inline, bold |
| `_extract_raw_markdown(text)` | Extraction depuis première ligne structurée |
| `clean_content(content)` | Retire trailing whitespace, réduit lignes vides à 2 max |

---

## `file_saver.py` — Classe `FileSaver`

**Rôle** : Écriture physique des fichiers avec gestion des collisions de noms.

**`__init__(uploads_dir, debug=False)`** — crée `uploads_dir` si absent, initialise stats.

| Méthode | Paramètres | Description |
|---------|-----------|-------------|
| `save(content, title, extension)` | `str, str, str` | Sanitise titre → génère nom unique → écrit UTF-8 → màj stats → retourne chemin |
| `_sanitize_filename(filename)` | `str` | Retire `< > : " / \ \| ? *`, limite 200 chars, fallback `"document"` |
| `_generate_unique_filename(base_name, extension)` | `str, str` | Essaie `base.md`, puis `base_1.md`, `base_2.md`… jusqu'à 1000, fallback timestamp |
| `get_statistics()` | — | `{files_saved, total_bytes, last_save, uploads_dir, dir_exists}` |
| `list_saved_files(limit)` | `int` | Glob `*.md` dans `uploads_dir`, trié par date décroissante |

---

## `file_writer_agent.py` — Classe `FileWriterAgent`

**Rôle** : Orchestrateur — coordonne `RequestDetector → MarkdownExtractor → FileSaver`.

**`__init__(uploads_dir, debug=False)`** — instancie les 3 composants, initialise stats.

| Méthode | Retour | Description |
|---------|--------|-------------|
| `process_response(user_message, ai_response)` | `Optional[str]` | Pipeline complet : détecte → extrait → nettoie → sauvegarde |
| `is_file_request(user_message)` | `bool` | Raccourci vers `detector.is_file_request()` |
| `get_statistics()` | `dict` | Stats agrégées agent + saver |
| `list_recent_files(limit)` | `list` | Délègue à `saver.list_saved_files()` |

**Stats trackées** : `requests_processed`, `requests_detected`, `files_saved`, `extractions_failed`, `saves_failed`.

Métriques calculées dans `get_statistics()` :
- `success_rate` = `files_saved / requests_detected` (si > 0)
- `extraction_rate` = `(requests_detected - extractions_failed) / requests_detected`
- `uploads_dir` — chemin du répertoire cible

---

## `document_generator.py` — Classe `DocumentGenerator`

**Rôle** : Génération d'un document `.md` complet via un appel IA **asynchrone** (arrière-plan), distinct de la réponse conversationnelle.

**Répertoire cible** : `data/downloads/` (≠ `data/uploads/` du pipeline classique)

**Prompt système** : `DOCUMENT_GENERATION_SYSTEM` — force structure Markdown professionnelle, minimum 3000 chars, sections titrées.

**`__init__(ai_controller, downloads_dir, debug=False)`** — crée répertoire, init stats, liste tâches pending.

| Méthode | Description |
|---------|-------------|
| `set_controller(ai_controller)` | Injecte ou remplace le contrôleur IA |
| `generate_and_save_async(user_request, title, context, conversation_history, on_complete, on_error)` | **Méthode principale async** : construit prompt → appelle IA → nettoie → sauvegarde → déclenche callbacks |
| `_build_full_prompt(user_request, context, conversation_history)` | Sections : demande, mémoire, 10 derniers messages historique |
| `_generate_content_async(prompt, user_request)` | Appelle `ai_controller.call_chat_api()` |
| `_clean_content(content)` | Retire artefacts ` ```markdown `, ` ```md `, ` ``` ` début/fin |
| `_save_document(content, title)` | Nom : `{safe_title}_{timestamp}.md` dans `downloads_dir` |
| `_sanitize_filename(title)` | Retire caractères spéciaux, underscores multiples, lowercase, max 40 chars |
| `get_statistics()` | `{documents_generated, total_chars, generation_errors, save_errors}` |
| `get_pending_count()` | Nombre de tâches asyncio en cours |

**Fonctions module-level (singleton)** :

| Fonction | Description |
|----------|-------------|
| `get_document_generator(ai_controller, downloads_dir, debug)` | Retourne ou crée l'instance singleton |
| `generate_document_async(user_request, title, ai_controller, context, conversation_history, downloads_dir, on_complete, on_error, debug)` | Wrapper utilitaire async |

---

## Flux d'intégration dans OGMA

### Pipeline classique (post-traitement réponse)
Appelé depuis `ogma_ng.py` dans le handler de réponse IA :
```python
# Après réception réponse IA
if file_writer and file_writer.detect_request(user_message):
    file_path = file_writer.process_response(user_message, ai_response)
    if file_path:
        # Notification UI + lien téléchargement
```

### Pipeline DocumentGenerator (génération dédiée)
Appelé de manière asynchrone, en parallèle de la réponse conversationnelle :
```python
generate_document_async(
    user_request=user_msg,
    title=extracted_title,
    ai_controller=chat_controller,
    context=memory_context,
    conversation_history=history,
    downloads_dir="data/downloads/",
    on_complete=lambda path: ui.notify(f"Document : {path}"),
    on_error=lambda e: ui.notify(f"Erreur : {e}", type="negative")
)
```

---

## Fichiers de données

| Chemin | Type | Description |
|--------|------|-------------|
| `data/uploads/` | Répertoire | Fichiers `.md` générés via pipeline classique |
| `data/downloads/` | Répertoire | Documents `.md` complets générés via DocumentGenerator |

---

## Statistiques disponibles

Via `get_statistics()` de `FileWriterAgent` :
```python
{
    "requests_processed": int,    # Total appels process_response()
    "requests_detected": int,     # Demandes de fichier détectées
    "files_saved": int,           # Fichiers sauvegardés avec succès
    "extractions_failed": int,    # Échecs extraction markdown
    "saves_failed": int,          # Échecs sauvegarde disque
    "success_rate": float,        # files_saved / requests_detected
    "extraction_rate": float,     # Taux succès extraction
    "total_bytes": int,           # Volume total écrit
    "uploads_dir": str            # Chemin répertoire cible
}
```
