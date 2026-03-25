# Extension Biographie Profil — Documentation Exhaustive

**Dossier** : `extensions/biographie_profil/`
**Version** : 1.0.0
**Rôle** : Système de biographie persistante à double volume — Volume 1 (souvenirs FAISS bruts) et Volume 2 (narration structurée JSON + journal Markdown) — avec détection automatique des personnes mentionnées, injection contextuelle intelligente et génération IA de portraits psychologiques/intellectuels complets.

---

## Concept

L'extension maintient des dossiers biographiques pour chaque personne mentionnée dans les conversations (l'utilisateur, l'IA elle-même, et les tierces personnes). Elle injecte automatiquement le profil pertinent dans le contexte de l'IA lorsqu'une personne est identifiée ou évoquée.

---

## Architecture — Fichiers

| Fichier | Rôle |
|---------|------|
| `__init__.py` | Façade singleton et initialisation des 3 composants |
| `settings.py` | `BiographySettings` — configuration persistée JSON |
| `biography_manager.py` | `BiographyManager` + `StructuredBiographyManager` — CRUD + génération IA |
| `magic_phrases.py` | `BiographyMagicPhrases` — détection auto + injection |
| `ui_components.py` | `BiographyUI` — bouton header + modal NiceGUI |
| `notification_cleaner.py` | `NotificationCleaner` — nettoyage des notifications UI |
| `prompt_archiviste_selection.txt` | Template prompt sélection Archiviste |

---

## `__init__.py` — API Publique

**État global** : `_biography_manager`, `_biography_ui`, `_biography_magic_phrases`, `_is_initialized`

### Fonction d'initialisation

`initialize_biography_extension(settings_manager, memory_manager, chat_controller, archiviste_controller=None, status_queue=None)`

→ Instancie dans l'ordre :
1. `BiographyManager(memory_manager)`
2. `BiographyUI(settings_manager, biography_manager)`
3. `BiographyMagicPhrases(biography_manager, archiviste_controller, status_queue)`

**Note** : `archiviste_controller` est **obligatoire** pour la sélection de souvenirs. Il n'y a pas de fallback en son absence.

### Autres fonctions

| Fonction | Description |
|----------|-------------|
| `is_available()` | `_is_initialized` |
| `get_biography_manager()` | Singleton `BiographyManager` |
| `get_biography_ui()` | Singleton `BiographyUI` |
| `get_biography_magic_phrases()` | Singleton `BiographyMagicPhrases` |
| `open_settings_modal()` | Délègue à `_biography_ui.open_settings_modal()` |
| `cleanup()` | Remet tous les singletons à `None` |

---

## `settings.py` — Classe `BiographySettings`

**Fichier de données** : `data/biography_settings.json`

### Paramètres par défaut

| Clé | Défaut | Description |
|-----|--------|-------------|
| `extension_enabled` | `False` | Extension désactivée au premier démarrage |
| `auto_detect_names` | `True` | Détection automatique des prénoms |
| `min_name_length` | `3` | Longueur minimale prénom valide |
| `max_name_length` | `15` | Longueur maximale |
| `backup_count` | `5` | Nombre de backups roulants |
| `version` | `"1.0.0"` | Version du schéma |
| `volume2_template` | Template Markdown multi-sections | Template narration V2 |
| `volume2_instructions` | Instructions V2.0 rédigées | Directives génération journal |

**Méthodes** : `get(key, default)`, `set(key, value)`, `load_settings()`, `save_settings()`, `is_enabled()`, `enable()`, `disable()`

---

## `biography_manager.py` — Deux classes

### Classe `BiographyManager`

Gestionnaire principal — FAISS, Volumes 1 et 2 legacy, architecture V2.0, backups, sélection Archiviste.

**`__init__(memory_manager)`**
- Crée `data/biographies/`
- `self.name_pattern = r'\b([A-Z][a-z]{2,15})\b'`
- `self._session_cache = {}` — cache Volume 1 session
- Charge lazy le template Archiviste depuis `prompt_archiviste_selection.txt`

#### CRUD Volume 1

| Méthode | Description |
|---------|-------------|
| `detect_user_names(text)` | Pattern majuscule + patterns informels (`"c'est X"`, `"je suis X"`, `"je m'appelle X"`). Exclut ~30 mots courants. |
| `get_existing_users()` | Scanne `data/biographies/*/metadata.json`, retourne noms triés |
| `create_user_directory(user_name)` | Crée `data/biographies/{user_name_lower}/` |
| `save_volume1_memories(user_name, memories)` | Sauvegarde JSON + backup auto avant écrasement |
| `load_volume1_memories(user_name)` | Cache session → lecture disque si miss |
| `create_user_metadata(user_name)` | Crée `metadata.json` avec flags `volume1_available`, `volume2_available` |

#### Sélection Archiviste

`async select_memories_archiviste(user_name, user_message, archiviste_controller, max_memories=10)` → `Optional[List[Dict]]`

Pipeline :
1. Charge Volume 1 (cache)
2. Crée catalogue de titres (80 chars max, numérotés)
3. Charge template `prompt_archiviste_selection.txt` (lazy)
4. Appel `archiviste_controller.call_chat_api(temperature=0.3, is_json=True, max_tokens=500, log_source="biography_selection")`
5. Parse JSON → `{'selected_indices': [...], 'reason': '...'}`
6. Retourne textes intégraux des souvenirs sélectionnés
7. **Pas de fallback** — retourne `None` si erreur

#### Volume 2 Legacy

| Méthode | Description |
|---------|-------------|
| `async create_volume2_narrative(user_name)` | Génère narration depuis conversation + enrichissement progressif via Archiviste |
| `load_volume2_narrative(user_name)` | Lit `volume2_narrative.md` |
| `get_volume2_backups(user_name)` | Liste backups depuis `backup_metadata.json` |
| `get_volume1_backups(user_name)` | Liste backups Volume 1 |
| `restore_volume2_backup(user_name, backup_filename)` | Backup du fichier actuel PUIS restauration |

#### Architecture V2.0

| Méthode | Description |
|---------|-------------|
| `get_structured_manager(user_name)` | Retourne `StructuredBiographyManager(user_name, self.data_dir)` |
| `async process_structured_biography(user_name, conversation_source="current")` | Pipeline : collecte multi-sources → analyse structurée → mise à jour JSON → sauvegarde journal |
| `async generate_volume2_json_with_grok(user_name, progress_callback=None)` | Phase 1 : collecte + génération JSON via IA (callbacks progression temps réel) |
| `async generate_volume2_md_with_grok(user_name, progress_callback=None)` | Phase 2 : JSON → Markdown narratif via IA |
| `generate_structured_journal(user_name)` | Génère journal Markdown depuis JSON structuré |
| `save_structured_journal(user_name)` | Écrit `volume2_journal.md` |

**Sources collectées dans `_collect_multiple_sources()` :**
1. Volume 1 FAISS (`volume1_memories.json`)
2. Conversation courante (`ogma_ng._chat_history_ui`)
3. Historique complet >30KB (max 3 fichiers/session)
4. Summaries cache (max 15/session)

**Validation enrichissement `_validate_content_enrichment()` :**

| Taille texte | Seuil qualité |
|-------------|--------------|  
| > 15 KB | minimum 60% de recouvrement |
| > 5 KB | minimum 70% |
| < 5 KB | minimum 80% |

Vérifie aussi : fin propre, structure Markdown valide, longueur minimale.

**Système de backup :**
- Rotation 10 fichiers
- Volume 1 : `backup/volume1_YYYYMMDD_NNN.json`
- Volume 2 : `backup/volume2_YYYYMMDD_NNN.md`
- Tracking partagé : `backup_metadata.json`

---

### Classe `StructuredBiographyManager`

Architecture V2.0 — gestion JSON structuré + génération journal Markdown.

**`__init__(user_name, data_dir)`** — crée `data/biographies/{user_lower}/`

#### Schéma JSON V2.0 (`_get_empty_structure()`)

```python
{
    "metadata": {
        "user_name": str, "created_at": str, "last_updated": str,
        "total_analyses": int, "data_sources": list
    },
    "chronologie": [{"timestamp", "source", "evenement", "conversation_id", "contexte"}],
    "etude_psychique": {"mbti", "profil_psychologique", "intelligence_emotionnelle"},
    "etude_intellectuelle": {"structure_mentale", "structure_memoire", "evaluation_comparative"},
    "etude_physique": {"traits_physiques", "expressions_caracteristiques", "ressemblances_notees"},
    "etude_gouts_preferences": {"preferences_fortes", "repulsions_identifiees", "evolutions_observees"}
}
```

**Méthodes principales :**

| Méthode | Description |
|---------|-------------|
| `load_structured_data()` | Lit JSON ou retourne structure vide |
| `save_structured_data(data)` | Incrémente `total_analyses`, màj `last_updated` |
| `add_chronology_event(event_data)` | Ajoute + retrie par timestamp |
| `update_psychological_profile(updates)` | Merge récursif sur `etude_psychique` |
| `update_intellectual_profile(updates)` | Merge récursif sur `etude_intellectuelle` |
| `generate_markdown_journal()` | Produit journal Markdown complet depuis JSON (chronologie mensuelle, MBTI, profils) |
| `save_generated_journal()` | Écrit dans `volume2_journal.md` |
| `scan_conversation_files(min_size_kb=30)` | Scanne `data/conversations/*.json` > 30KB non encore traités via SHA256 |
| `async integrate_summaries_cache(max_summaries=20)` | Analyse résumés via Archiviste, intègre résultats |
| `async _analyze_summary_content(content, file_info)` | Appel IA (Archiviste prioritaire, sinon Chat) → JSON structuré 5 catégories |

**Fichier tracking** : `data/biographies/{user}/processed_documents.json` (SHA256 fichiers déjà traités)

---

## `magic_phrases.py` — Classe `BiographyMagicPhrases`

**`__init__(biography_manager, archiviste_controller=None, status_queue=None)`**
- `self.conversation_message_count = 0`
- `self.last_injection_message = -1`

### Méthode principale

`async handle_magic_phrases(user_input, is_ai_message=False, conversation_history=None)` → `Optional[Dict]`

Retourne `{'content': str, 'type': 'display' | 'inject'}` ou `None`.

Pipeline :
1. Si `is_ai_message` → `_handle_luna_magic_phrases()` → type `'display'`
2. Si message utilisateur → `_handle_user_magic_phrases()` → type `'display'`
3. Si message utilisateur → `_handle_auto_detection()` → type `'inject'`

### Triggers IA (phrases magiques dans la réponse de l'IA)

- Regex : `"il faut que je consulte la biographie de [prénom]"`
- Action : charge Volume 1, formate avec `_format_volume1_for_ai()`, retourne contenu pour affichage

### Triggers utilisateur

- `"complète ma biographie"`, `"complète ma bio"`, `"met à jour ma biographie"`, `"enrichis mon profil"`
- Action : détecte nom courant, appelle `biography_manager.create_volume2_narrative()`

### Logique de détection auto-injection — `_should_inject_biography(message, message_count)`

| Règle | Condition | Action |
|-------|---------|--------|
| 1 (HAUTE) | Présentation avec bio existante (`"c'est X"`, `"je suis X"`, `"je m'appelle X"`) | INJECT |
| 2 | Message simple (≤3 mots ou salutation) au 1er message | SKIP |
| 3 | Question personnelle (`"qui suis-je"`, `"parle-moi de"`) | INJECT |
| 4 | Contexte riche (>10 mots) | INJECT |
| 5 | Mots-clés personnels (`moi`, `je`, `mon`, `ma`) après message 1 | INJECT |

### Sélection cible intelligente — `_select_target_user_intelligent()`

Consulte `identity_manager.get_current_identity()` :
- L'IA elle-même : injectée uniquement si mentionnée explicitement
- Utilisateur actif : injecté si mots-clés personnels ou nom mentionné

### Déduplication — `_deduplicate_memories_with_history()`

Calcule taux de présence des mots-clés (>4 chars) d'un souvenir dans les 10 derniers messages.
Seuil : >70% de mots déjà présents → souvenir redondant → supprimé.

### Format injection — `_format_selected_memories()`

```
[BIOGRAPHIE AUTO-INJECTION] ou [BIOGRAPHIE CONSULTATION]
{texte intégral des souvenirs sélectionnés}
```

---

## `ui_components.py` — Classe `BiographyUI`

**`__init__(settings_manager, biography_manager)`** — charge état depuis `data/extensions/biography_config.json`.

### Éléments UI

**Bouton header** : `create_extension_button()` — bouton ✒️ 50×50px rond, gradient `#2E4057 → #4A90E2`, `margin-right: 10px`.

**Modal** : `open_settings_modal()` — 600–800px, sections :
- Toggle ON/OFF (persisté)
- INFO : description et phrases magiques
- Instructions V2 : textarea éditable + bouton save
- Actions : champ nom + 6 boutons (voir ci-dessous)
- Outils de nettoyage notifications
- Accès dossier biographies
- Sauvegarde manuelle

### Boutons d'action dans la modal

| Bouton | Méthode | Action |
|--------|---------|--------|
| 🔄 Traiter souvenirs | `process_specific_user_memories()` | `biography_manager.process_existing_memories_for_user(user_name)` |
| 📊 Collecte infos | `collect_biography_info()` | `biography_manager.process_structured_biography(user_name, "current")` |
| 🧠 Phase 1: JSON IA | `generate_volume2_json_ia()` | `biography_manager.generate_volume2_json_with_grok()`, timeout UI 240s |
| 📖 Phase 2: MD IA | `generate_volume2_md_ia()` | `biography_manager.generate_volume2_md_with_grok()`, timeout UI 240s |
| ⚙️ Legacy Python | `generate_volume2_from_json()` | Méthode mécanique dépréciée |
| 🧹 Nettoyer Notifs | `emergency_cleanup_notifications()` | 15×5 notifications vides |

**Persistance état** : `data/extensions/biography_config.json`
```json
{"is_enabled": bool, "last_updated": float, "volume2_instructions": str}
```

---

## `notification_cleaner.py` — Classe `NotificationCleaner`

Utilitaire pour nettoyer les notifications NiceGUI coincées lors des opérations longues.

| Méthode | Description |
|---------|-------------|
| `create_managed_notification(message, type_='ongoing', timeout=60)` | `ui.notify()` + stockage dans liste |
| `async dismiss_notification(notification)` | Ferme + retire de la liste |
| `async force_cleanup_all()` | Ferme toutes + signal global + notification confirmation |
| `async emergency_reset()` | Vide liste + 3x `ui.notify('', timeout=0.05)` + warning |

---

## Fichiers de données complets

| Chemin | Type | Description |
|--------|------|-------------|
| `data/biographies/{user}/volume1_memories.json` | JSON | Souvenirs FAISS Volume 1 |
| `data/biographies/{user}/volume2_narrative.md` | Markdown | Narration legacy Volume 2 |
| `data/biographies/{user}/volume2_structured.json` | JSON | Données structurées V2.0 |
| `data/biographies/{user}/volume2_journal.md` | Markdown | Journal généré depuis V2.0 |
| `data/biographies/{user}/metadata.json` | JSON | Flags `volume1_available`, `volume2_available` |
| `data/biographies/{user}/backups/volume1_*.json` | JSON | Backups roulants Volume 1 (max 10) |
| `data/biographies/{user}/backups/volume2_*.md` | Markdown | Backups roulants Volume 2 (max 10) |
| `data/biographies/{user}/backups/backup_metadata.json` | JSON | Index des backups |
| `data/biographies/{user}/processed_documents.json` | JSON | SHA256 fichiers traités (anti-relecture) |
| `data/biography_settings.json` | JSON | Configuration extension |
| `data/extensions/biography_config.json` | JSON | État enabled + instructions V2 |
| `extensions/biographie_profil/prompt_archiviste_selection.txt` | Texte | Template prompt sélection par Archiviste |
