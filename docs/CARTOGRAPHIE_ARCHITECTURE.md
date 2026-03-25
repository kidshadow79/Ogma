# OGMA - Cartographie Architecture & Nettoyage
**Date d'analyse** : 6 mars 2026  
**Version analysée** : v2.2 (post-réinitialisation profil - état vierge)  
**Agent** : GitHub Copilot

---

## 1. Architecture Active (NE PAS TOUCHER)

### Fichiers Core (racine)
| Fichier | Rôle | Taille |
|---|---|---|
| `ogma_ng.py` | Orchestrateur principal + UI NiceGUI | 472 KB |
| `core_logic.py` | Contrôleurs IA multi-providers | 172 KB |
| `memory_manager.py` | Système mémoire hybride SQLite+FAISS | 200 KB |
| `logic_callbacks.py` | Callbacks logiques (phrases magiques, etc.) | 81 KB |
| `ogma_modals.py` | Système de modales UI centralisé | 243 KB |
| `ogma_ui_conversations.py` | UI conversations + cleanup dialog | 254 KB |
| `ogma_image_config.py` | Configuration génération images | 138 KB |
| `ogma_profile.py` | Gestion profils + sauvegardes | 83 KB |
| `ogma_headers.py` | Header UI + boutons extensions | 48 KB |
| `ogma_perception.py` | Intégration perception visuelle | 49 KB |
| `ogma_tts_config.py` | Configuration TTS | 47 KB |
| `ogma_displays.py` | Affichage messages chat | 38 KB |
| `conversation_summarizer.py` | Résumés conversations | 37 KB |
| `utils.py` | Utilitaires globaux | 33 KB |
| `archiviste_memory_optimizer.py` | Optimiseur mémoire Archiviste | 52 KB |
| `injection_deduplicator.py` | Déduplication injections mémoire | 21 KB |
| `ogma_extensions_ui.py` | UI extensions | 19 KB |
| `ogma_introspection_ui.py` | UI introspection | 18 KB |
| `nicegui_error_handler.py` | Gestion erreurs NiceGUI | 15 KB |
| `conversation_scanner.py` | Scan conversations passées | 14 KB |
| `magic_phrase_guard.py` | Protection phrases magiques | 13 KB |
| `identity_manager.py` | Gestion identités | 12 KB |
| `hybrid_detection.py` | Détection hybride | 12 KB |
| `temporal_injector.py` | Injection temporelle | 10 KB |
| `model_capabilities.py` | Capacités modèles IA | 8 KB |
| `tts_perception_manager.py` | TTS + perception | 7.5 KB |
| `archiviste_logger.py` | Logger archiviste | 7 KB |
| `profile_manager.py` | Backend gestion profils | 70 KB |
| `api_keys_vault.py` | Coffre-fort clés API | 6 KB |
| `launch_ogma.py` | Point d'entrée production | 7 KB |
| `start_ogma.py` | Point d'entrée dev | 2 KB |
| `stop_signal.py` | Signal d'arrêt | 1 KB |
| `nicegui_client_guard.py` | Garde client NiceGUI | 3 KB |
| `notification_killer.py` | Suppression notifs excessives | 4 KB |
| `ego_selector.py` | Sélecteur ego | 16 KB |
| `ogma_config_ui.py` | Config UI | 1 KB |
| `audio_manager.py` | Wrapper audio (redirige vers module) | 351 B |
| `audio_manager_wrapper.py` | Wrapper audio (redirige vers module) | 313 B |
| `tts_conflict_free.py` | Wrapper TTS (redirige vers module) | 318 B |

### Modules Core (`modules/`)
| Module | Fichiers clés |
|---|---|
| `modules/ogma_core/` | `globals.py`, `controllers.py`, `extensions_loader.py`, `compat.py`, `utils.py` |
| `modules/logic/` | `image_generation.py`, `archi_sensor.py`, `ego_activation.py`, `i2i_lessons.py`, `memory_utils.py`, `perception.py` |
| `modules/audio/` | `manager.py`, `tts_utils.py`, `wrapper.py` |
| `modules/voice/` | `voice_manager.py`, `voice_triggers.py`, `voice_ui.py` |
| `modules/preanalysis_optimizer/` | `context_cache.py`, `parallel_executor.py`, `preanalysis_engine.py`, `unified_meta_analyzer.py`, `integration.py` |

### Extensions Actives (`extensions/`)
| Extension | Rôle |
|---|---|
| `archi_sensor/` | Détection comportementale Archiviste |
| `biographie_profil/` | Biographies utilisateur |
| `capability_advisor/` | Conseiller capacités + LEDs |
| `cognitive_mirror/` | Introspection IA (miroir cognitif) |
| `contextual_recall/` | Rappel historique conversationnel |
| `dream_engine/` | Système de rêves IA |
| `ego_selector/` | Sélection ego dynamique |
| `file_writer/` | Écriture de fichiers par l'IA |
| `flux_cognitif/` | Flux cognitif streaming |
| `journal_de_bord/` | Journal quotidien |
| `ogma_ng_v2/` | Features modulaires v2 |
| `organic_planner/` | Agenda organique |
| `telegram_connector/` | Connecteur Telegram |
| `temporal_guardian/` | Gardien temporel |
| `text2img/` | Génération images (T2I + I2I) |
| `web_navigator/` | Navigation web + recherche |
| `perception_agent.py` | Agent de perception (fichier racine extensions/) |
| `perception_ui.py` | UI perception |
| `contour_analyzer.py` | Analyse contours images |
| `depth_manager.py` | Gestion profondeur images |
| `file_processor.py` | Traitement fichiers upload |

### Données Actives (`data/`)
| Fichier/Dossier | Rôle | Notes |
|---|---|---|
| `data/memory/memories.db` | **DB mémoire ACTIVE** (SQLite + FTS5) | 7 souvenirs fondateurs |
| `data/memory/faiss.index` | **Index FAISS ACTIF** | 28 KB |
| `data/memory/i2i_lessons.db` | DB leçons I2I | 37 KB |
| `data/settings.json` | Configuration globale | 33 KB |
| `data/identities.json` | Identités profils | 771 B |
| `data/instructions_defaults.json` | Instructions par défaut (template reset) | 16 KB |
| `data/ego_compiled.json` | Ego compilé (vide post-reset) | 231 B |
| `data/ego_compiled_boolean.md` | Ego booléen (vide) | 91 B |
| `data/ego_compiled_minimal.md` | Ego minimal (vide) | 89 B |
| `data/ego_prompt.txt` | Prompt ego | 700 B |
| `data/ego_selector_config.json` | Config sélecteur ego | 4 KB |
| `data/persistent_context.txt` | Contexte persistant | 588 B |
| `data/introspection_settings_v2.json` | Config introspection | 9 KB |
| `data/capability_advisor_config.json` | Config capability advisor | 214 B |
| `data/capability_advisor_prompt.txt` | Prompt advisor | 1 KB |
| `data/extensions/biography_config.json` | Config biographies | 65 B |
| `data/backups/` | Backups settings.json (rotation auto) | ~320 KB |

### Fichiers Statiques (`static/`)
| Fichier | Rôle | Utilisé |
|---|---|---|
| `ogma_styles.css` | Styles CSS OGMA | ✅ Actif |
| `OGMAlogo.PNG` / `OGMAlogo2.png` | Logos OGMA | ✅ Actif |
| `OGMAlogopet.png` | Logo petit | ✅ Actif (favicon) |
| `logotetetitre.png` | Logo tête+titre | ✅ Actif |
| `icotete.PNG` / `icotetes.png` | Icônes tête | ✅ Actif |
| `iconom.PNG` | Icône | ✅ Actif |
| `biologic.png` | Image extension | ✅ Actif |
| `dremengine.png` | Image dream engine | ✅ Actif |
| `egodyn.png` | Image ego dynamique | ✅ Actif |
| `extension.png` | Image extensions | ✅ Actif |
| `reflexecogni.png` | Image réflexe cognitif | ✅ Actif |
| `squelette.png` | Image squelette | ✅ Actif |
| `perception-icon.png` | Icône perception | ✅ Actif |
| `circuitint.jpg` / `.png` | Images circuit | ✅ Actif |

### Autres Actifs
| Dossier/Fichier | Rôle |
|---|---|
| `files/` | Module gestion fichiers (file_management.py) |
| `models/mediapipe/` | Modèles MediaPipe (face/hand/pose) - 16.4 MB |
| `config/` | Fichiers de configuration |
| `backend/` | Communication backend IA |
| `scripts/ego_compiler.py` | Compilateur ego (actif) |
| `requirements.txt` | Dépendances Python |
| `pytest.ini` | Configuration pytest |
| `.env.example` | Template variables d'environnement |
| `.gitignore` | Fichiers ignorés git |
| `README.md` | Documentation projet |
| `CODING_RULES.md` | Règles de coding |

---

## 2. Chemins Mémoire (CRITIQUE)

### Architecture active (v2.2)
```
data/memory/memories.db     ← DB SQLite + FTS5 (ACTIVE)
data/memory/faiss.index     ← Index FAISS (ACTIF, 28 KB)
```
Initialisé dans `modules/ogma_core/controllers.py` ligne 236-237 :
```python
db_path = mem_dir / 'memories.db'   # mem_dir = data/memory
index_path = mem_dir / 'faiss.index'
```

### Fichiers mémoire OBSOLÈTES (anciens systèmes)
```
data/memory.db              ← Ancien schéma, 12 KB, 0 rows
data/memories.db            ← Fichier vide, 0 bytes
data/memory_index.faiss     ← Ancien FAISS, 45 bytes (quasi vide)
data/memory/faiss_index.bin ← Ancien format FAISS, 1.33 MB (non référencé)
```

---

## 3. Fichiers/Dossiers Identifiés pour Suppression

### CATÉGORIE A : Obsolètes certains (aucune référence active)

| Fichier/Dossier | Raison | Taille |
|---|---|---|
| `data/memory.db` | Ancienne DB racine, 0 rows, non référencée par controllers.py | 12 KB |
| `data/memories.db` | Fichier vide (0 bytes) | 0 B |
| `data/memory_index.faiss` | Ancien index FAISS racine, 45 bytes, non utilisé | 45 B |
| `data/memory/faiss_index.bin` | Ancien format binaire FAISS, remplacé par `faiss.index` | 1.33 MB |
| `data/memory/faiss_index_backup_20251212_210819.bin` | Backup ancien FAISS | 0.85 MB |
| `data/memory/memories_backup_20251212_210819.db` | Backup ancien memories.db | 9.16 MB |
| `data/memory/faiss.*.bak` (×3) | Backups FAISS août 2025 | 1.0 MB |
| `data/memory/memories.*.bak` (×3) | Backups memories août 2025 | 5.2 MB |
| `data/memory/repair_report_*.json` (×3) | Rapports réparation août 2025 | ~2 KB |
| `data/memory/backup/` | Dossier backup mémoire (10 fichiers) | 19.16 MB |
| `data/memory_backup_fts5_migration_20251103_171806/` | Backup migration FTS5 complet (nov 2025) | 34.15 MB |
| `data/summaries_cache/` | 364 fichiers de cache résumés (ancien système, non référencé) | 0.34 MB |
| `data/archiviste_tokens_debug.jsonl` | Log debug Archiviste (ancien) | 1.25 MB |
| `data/journal_reves.json` | Journal rêves ancien profil | 0.29 MB |
| `data/journal_reves.md` | Journal rêves ancien profil (markdown) | 0.26 MB |
| `logs/dreams.log` | Log rêves ancien profil | 0.27 MB |
| **Sous-total A** | | **~73 MB** |

### CATÉGORIE B : Archives code (plus aucun usage)

| Fichier/Dossier | Raison | Taille |
|---|---|---|
| `_archive/` (entier) | Backup ancien ogma_ng.py (427 KB), vieux code | 66.4 MB |
| `docs/_archive/` | Audits/docs/rapports anciens | 1.67 MB |
| **Sous-total B** | | **~68 MB** |

### CATÉGORIE C : Fichiers _old / _obsolete / .backup / .broken

| Fichier | Raison | Taille |
|---|---|---|
| `extensions/archi_sensor/config_old.py` | Ancienne config remplacée par config.py | 7.6 KB |
| `extensions/archi_sensor/ui_components_old.py` | Ancien UI remplacé par ui_components.py | 12 KB |
| `extensions/web_navigator/image_fetcher_obsolete.py` | Marqué obsolète explicitement | 709 B |
| `extensions/web_navigator/web_scraper_obsolete.py` | Marqué obsolète explicitement | 607 B |
| `extensions/perception_debug_monitor.py` | Fichier vide (0 bytes) | 0 B |
| `extensions/cognitive_mirror/config_v2.py` | Ancienne config v2 (remplacée) | 24 KB |
| `extensions/cognitive_mirror/ui_parameters_v2.py` | Ancien UI paramètres v2 | 21 KB |
| `tests/unit/test_memory_manager.py.backup` | Backup test | 21 KB |
| `tests/unit/test_memory_manager_strict.py.broken` | Test cassé | 32 KB |
| **Sous-total C** | | **~120 KB** |

### CATÉGORIE D : Fichiers temporaires/debug à la racine

| Fichier | Raison | Taille |
|---|---|---|
| `_temp_ego_audit.py` | Script temporaire | 3 KB |
| `_temp_gen_prompt.py` | Script temporaire | 2 KB |
| `_temp_prompt_escaped.txt` | Fichier temporaire | 3 KB |
| `_debug_batch.py` | Script debug | 2 KB |
| `ego_selector .py.txt` | Doublon avec espace dans le nom | 16 KB |
| **Sous-total D** | | **~26 KB** |

### CATÉGORIE E : Demos/prototypes HTML (static/)

| Fichier | Raison | Taille |
|---|---|---|
| `static/demo_ego_mirror.html` | Prototype UI ego mirror (v1) | 10 KB |
| `static/demo_ego_mirror_fractal.html` | Prototype fractal | 11 KB |
| `static/demo_ego_mirror_glassmorphism.html` | Prototype glassmorphism | 12 KB |
| `static/demo_ego_mirror_threejs.html` | Prototype Three.js v1 | 15 KB |
| `static/demo_ego_mirror_threejs_v2.html` | Prototype Three.js v2 | 19 KB |
| `static/demo_ego_mirror_threejs_v3.html` | Prototype Three.js v3 | 12 KB |
| `static/demo_ego_mirror_threejs_v4.html` | Prototype Three.js v4 | 9 KB |
| `static/demo_ego_mirror_threejs_v5.html` | Prototype Three.js v5 | 6 KB |
| `static/demo_ego_mirror_threejs_v6.html` | Prototype Three.js v6 | 26 KB |
| `static/demo_ego_mirror_v7_ether.html` | Prototype ether v7 | 19 KB |
| `static/demo_ego_mirror_v8_fusion.html` | Prototype fusion v8 | 28 KB |
| **Sous-total E** | | **~167 KB** |

### CATÉGORIE F : Caches Python obsolètes

| Éléments | Raison | Taille estimée |
|---|---|---|
| 21 fichiers `*cpython-310*.pyc` | Python 3.10 (OGMA utilise 3.13) | ~200 KB |
| `extensions/__pycache__/anatomical_analyzer.cpython-313.pyc` | Module supprimé | 21 KB |
| `extensions/__pycache__/sam_manager.cpython-313.pyc` | Module supprimé | 4 KB |
| `modules/__pycache__/ego_mirror_bridge.cpython-313.pyc` | Module supprimé | 9 KB |
| **Sous-total F** | | **~234 KB** |

### CATÉGORIE G : Scripts de diagnostic/analyse ponctuels (racine)

| Fichier | Raison |
|---|---|
| `check_all_memory_db.py` | Diagnostic DB unique |
| `check_db.py` | Diagnostic DB vieille |
| `check_default_memories.py` | Vérification mémoires par défaut |
| `check_memory_detail.py` | Diagnostic mémoire |
| `confirm_trace_table_integration.py` | Confirmation intégration trace |
| `display_base_groups.py` | Affichage groupes ego |
| `fix_ego_prompt.py` | Script de fix ponctuel |
| `analyze_ego_startup.py` | Analyse startup ego |
| `search_genesis_memories.py` | Recherche mémoires genèse |
| `test_*.py` (×21 fichiers racine) | Tests ponctuels (non pytest) |
| **Sous-total G** | | **~150 KB** |

---

## 4. Résumé Gain Estimé

| Catégorie | Gain |
|---|---|
| A - Données obsolètes | ~73 MB |
| B - Archives code | ~68 MB |
| C - Fichiers _old/_obsolete | ~120 KB |
| D - Fichiers temporaires | ~26 KB |
| E - Demos HTML | ~167 KB |
| F - Caches Python obsolètes | ~234 KB |
| G - Scripts diagnostic | ~150 KB |
| **TOTAL** | **~142 MB** |

---

## 5. Fichiers NON SUPPRIMABLES (analyses à conserver)

| Dossier | Raison |
|---|---|
| `scripts/ego_compiler.py` | Utilisé activement par le système ego |
| `scripts/migrations/` | Scripts de migration (utiles pour référence) |
| `tests/` (hors .backup/.broken) | Suite de tests fonctionnelle |
| `docs/` (hors _archive) | Documentation active |
| `data/backups/` | Backups settings.json (rotation automatique, 10 max) |
| `data/memory/i2i_lessons.db` | DB leçons I2I active |
| `static/ogma_styles.css` | CSS actif |
| `static/*.png, *.PNG, *.jpg` (hors demos) | Images UI actives |

---

## 6. Notes Techniques pour Futurs Travaux

### Pattern d'initialisation MemoryManager
```python
# modules/ogma_core/controllers.py, lignes 234-247
mem_dir = DATA_DIR / 'memory'
db_path = mem_dir / 'memories.db'      # SQLite + FTS5
index_path = mem_dir / 'faiss.index'   # FAISS IndexFlatL2
```

### Fichiers créés dynamiquement au runtime
- `data/conversations/*.json` : Conversations sauvegardées
- `data/conversations/index.json` : Index des conversations  
- `data/generated_images/` : Images générées
- `data/uploads/` : Fichiers uploadés temporaires
- `data/ego_archive/` : Archives ego
- `data/biographies/` : Biographies utilisateur
- `extensions/journal_de_bord/data/` : Données journal
- `captures/` : Captures webcam
- `logs/` : Logs runtime

### Port de démarrage
- Retry automatique ports 8080-8090 (launch_ogma.py)

### Conventions de nommage fichiers backup
- `settings_backup_YYYYMMDD_HHMMSS.json` dans `data/backups/`
- `backup_avant_suppression_YYYYMMDD_HHMMSS` dans `profils_sauvegardes/`
