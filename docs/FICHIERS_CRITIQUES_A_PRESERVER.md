# 🛡️ FICHIERS CRITIQUES À PRÉSERVER - OGMA

**Date de création** : 12 octobre 2025
**Contexte** : Rapport d'analyse exhaustive avant opération de nettoyage
**Analysé par** : Claude Code (Anthropic - Sonnet 4.5)
**Objectif** : Documenter TOUS les fichiers essentiels au fonctionnement d'OGMA

---

## 📊 RÉSUMÉ EXÉCUTIF

### Espace Disque Analysé
- **Espace total potentiellement supprimable** : ~220+ MB
  - `backups/` : 68 MB
  - `profils_sauvegardes/` : 149 MB
  - `tests/` (dossier racine) : 1.9 MB
  - Fichiers test racine (144 fichiers) : ~2+ MB
  - Documentation redondante racine : ~1+ MB

### Données Critiques à Préserver
- **Mémoire active** : 32 MB (`data/memory/`)
- **Conversations** : 2.3 MB (`data/conversations/`)
- **Biographies** : 442 KB (`data/biographies/`)
- **Images générées** : 792 KB (`data/generated_images/`)
- **Caches résumés** : 709 KB (`data/summaries_cache/`)

---

## 🔥 FICHIERS CORE - ABSOLUMENT CRITIQUES

### 1. Fichiers Python Principaux (Ne JAMAIS Toucher)

| Fichier | Lignes | Taille | Rôle Critique |
|---------|--------|--------|---------------|
| **ogma_ng.py** | 6,693 | 328KB | Interface NiceGUI + orchestration générale |
| **core_logic.py** | 1,691 | 95KB | Contrôleurs IA multi-providers |
| **memory_manager.py** | 2,269 | 108KB | Gestion mémoire SQLite + FAISS |
| **logic_callbacks.py** | 1,976 | 96KB | Callbacks IA + injection métacognitive |
| **audio_manager.py** | 1,457 | 60KB | STT/TTS (Whisper/ElevenLabs/System) |
| **conversation_summarizer.py** | - | 17KB | Archivage et résumés conversations |
| **ogma_modals.py** | 3,038 | 162KB | Modals interface utilisateur |
| **profile_manager.py** | 1,008 | 55KB | Gestion profils utilisateurs |
| **ogma_headers.py** | - | 29KB | En-têtes interface |
| **ogma_displays.py** | - | 33KB | Affichages interface |
| **ogma_profile.py** | - | 34KB | Profils IA |
| **ogma_tts_config.py** | - | 28KB | Configuration TTS |
| **ogma_config_ui.py** | - | 1KB | Configuration UI |
| **utils.py** | - | 28KB | Utilitaires et constantes |
| **behavioral_sensor.py** | - | 12KB | Détection comportements |
| **data_cleaner.py** | - | 27KB | Nettoyage/maintenance |
| **ego_sync_system.py** | - | 6KB | Synchronisation ego_prompt |
| **archiviste_decision.py** | - | 7KB | Décisions Archiviste |
| **model_capabilities.py** | - | 8KB | Capacités modèles IA |
| **hybrid_detection.py** | - | 11KB | Détection hybride |
| **temporal_injector.py** | - | 10KB | Injection temporelle |
| **identity_manager.py** | - | 13KB | Gestion identités IA |
| **nicegui_client_guard.py** | - | 3KB | Protection client NiceGUI |
| **nicegui_error_handler.py** | - | 5KB | Gestion erreurs NiceGUI |

### 2. Fichiers de Démarrage (CRITIQUES)

| Fichier | Rôle |
|---------|------|
| **launch_ogma.py** | Lanceur principal OGMA |
| **start_ogma.py** | Script démarrage alternatif |
| **.env** | Variables environnement (clés API) |

---

## 🧩 EXTENSIONS - STRUCTURE COMPLÈTE

### Dossier `extensions/` - TOUT À PRÉSERVER

#### 1. Extension Cognitive Mirror (Subconscience)
**Emplacement** : `extensions/cognitive_mirror/`

| Fichier | Rôle |
|---------|------|
| `__init__.py` | Initialisation module |
| `core_cognitive_mirror.py` | Cœur introspection Luna-Archiviste |
| `introspection_core.py` | Logique introspection |
| `introspection_orchestrator.py` | Orchestration conversations |
| `memory_integration.py` | Intégration mémoire |
| `reflection_manager.py` | Gestion réflexions |
| `subconscience_orchestrator.py` | Orchestration subconscience |
| `ui_components.py` | Composants UI |
| `ui_parameters_modal_v2.py` | Modal paramètres V2 |
| `ui_parameters_modal_v3_simple.py` | Modal paramètres V3 |
| `config.py` | Configuration extension |

**Fichiers backup à CONSERVER** (historique important) :
- `core_cognitive_mirror_backup_20250926_193747.py`
- `reflection_manager_old.py`
- `ui_components_backup_*` (3 fichiers)

#### 2. Extension Biographie Profil
**Emplacement** : `extensions/biographie_profil/`

| Fichier | Rôle |
|---------|------|
| `__init__.py` | Initialisation module |
| `biography_manager.py` | Gestion biographies |
| `magic_phrases.py` | Phrases magiques détection |
| `notification_cleaner.py` | Nettoyage notifications |
| `settings.py` | Paramètres extension |
| `ui_components.py` | Composants UI |

#### 3. Extension Journal de Bord
**Emplacement** : `extensions/journal_de_bord/`

| Fichier | Rôle |
|---------|------|
| `__init__.py` | Initialisation module |
| `core_journal.py` | Cœur journal |
| `entry_generator.py` | Génération entrées |
| `json_manager.py` | Gestion JSON |
| `calendar_viewer.py` | Visualisation calendrier |
| `context_provider.py` | Fourniture contexte |
| `config.py` | Configuration extension |
| `ui_components.py` | Composants UI |

#### 4. Extension Temporal Guardian
**Emplacement** : `extensions/temporal_guardian/`

| Fichier | Rôle |
|---------|------|
| `__init__.py` | Initialisation module |
| `temporal_guardian.py` | Gardien temporel principal |
| `temporal_sensor.py` | Capteur temporel |
| `archiviste_enricher.py` | Enrichissement Archiviste |
| `config.py` | Configuration extension |
| `test_extension.py` | Tests extension (GARDER) |

#### 5. Extension Perception Agent
**Emplacement** : `extensions/`

| Fichier | Rôle |
|---------|------|
| `perception_agent.py` | Agent perception visuelle |
| `perception_ui.py` | Interface perception |

#### 6. Extension Text2Image
**Emplacement** : `extensions/text2img/`

| Fichier | Rôle |
|---------|------|
| `__init__.py` | Initialisation module |
| `text2img_manager.py` | Gestionnaire génération images |
| `perchance_backend.py` | Backend Perchance |
| `perchance_http_backend.py` | Backend HTTP Perchance |
| `ui_components.py` | Composants UI |

#### 7. Extension Archi Sensor
**Emplacement** : `extensions/archi_sensor/`

| Fichier | Rôle |
|---------|------|
| `__init__.py` | Initialisation module |
| `core_archi_sensor.py` | Cœur capteur architectural |
| `unified_analyzer.py` | Analyseur unifié |
| `config.py` | Configuration extension |
| `ui_components.py` | Composants UI |

**Fichiers old à CONSERVER** (référence) :
- `config_old.py`
- `ui_components_old.py`

#### 8. Extension File Processor
**Emplacement** : `extensions/`

| Fichier | Rôle |
|---------|------|
| `file_processor.py` | Traitement fichiers |

---

## 📁 DOSSIER DATA - DONNÉES CRITIQUES

### Structure Complète à Préserver

```
data/
├── memory/                          # 32 MB - CRITIQUE
│   ├── memories.db                  # Base données mémoire principale (4.9 MB)
│   ├── faiss.index                  # Index vectoriel FAISS (929 KB)
│   ├── faiss_index.bin             # Index binaire (893 KB)
│   ├── backup/                      # Backups mémoire (GARDER)
│   └── *.bak                        # Fichiers backup mémoire (GARDER 3 plus récents)
│
├── biographies/                     # 442 KB - CRITIQUE
│   ├── luna/
│   │   ├── metadata.json
│   │   ├── volume1_memories.json
│   │   └── volume2_structured.json
│   └── yohan/
│       ├── metadata.json
│       ├── volume1_memories.json
│       ├── volume2_structured.json
│       ├── processed_documents.json
│       └── backups/                 # GARDER backups biographies
│
├── conversations/                   # 2.3 MB - CRITIQUE
│   └── *.json                       # Tous fichiers conversations actifs
│   └── *_backup.json                # Tous fichiers backup conversations
│
├── summaries_cache/                 # 709 KB - GARDER
│   └── *.json                       # Caches résumés conversations
│
├── generated_images/                # 792 KB - GARDER
│   └── *.png, *.jpg                 # Images générées par IA
│
├── uploads/                         # GARDER (vide actuellement)
│
├── extensions/                      # GARDER dossier complet
│
├── ego_archive/                     # GARDER archives ego
│
├── settings.json                    # 20 KB - CRITIQUE (config globale)
├── cognitive_mirror_settings.json   # 7.3 KB - CRITIQUE
├── cognitive_mirror_reflections.jsonl # 341 KB - CRITIQUE
├── journal_settings.json            # 878 B - CRITIQUE
├── ego_prompt.txt                   # 2.2 KB - CRITIQUE (identité IA)
├── persistent_context.txt           # 965 B - GARDER
├── instructions_defaults.json       # 18 KB - CRITIQUE
├── identities.json                  # 1.3 KB - CRITIQUE
├── archi_sensor_config.json         # 3.6 KB - GARDER
├── archi_sensor_state.json          # 17 B - GARDER
├── memories.db                      # 0 B (legacy, peut être supprimé)
└── memory.db                        # 0 B (legacy, peut être supprimé)
```

---

## ⚙️ CONFIGURATION - FICHIERS SYSTÈMES

### Dossier `config/` - TOUT PRÉSERVER

| Fichier | Rôle |
|---------|------|
| `requirements.txt` | Dépendances Python minimales |
| `requirements2.txt` | Dépendances supplémentaires |
| `requirements-complete.txt` | Dépendances complètes |
| `requirements-audio.txt` | Dépendances audio |
| `requirements-minimal.txt` | Dépendances minimales |
| `requirements-nicegui.txt` | Dépendances NiceGUI |
| `requirements-nvidia.txt` | Dépendances NVIDIA/CUDA |
| `install_nvidia.bat` | Script installation Windows |
| `install_nvidia.sh` | Script installation Linux |
| `octopus.bat` | Lanceur bat |
| `run.bat` | Lanceur exécution |
| `Install_Extensions.txt` | Guide installation extensions |

---

## 🎨 DOSSIER STATIC - ASSETS VISUELS

### Fichiers à Préserver

| Fichier | Taille | Rôle |
|---------|--------|------|
| `ogma_styles.css` | 94 KB | Styles CSS interface |
| `OGMAlogo.PNG` | 1 MB | Logo principal |
| `OGMAlogo2.png` | 1 MB | Logo alternatif |
| `OGMAlogopet.png` | 16 KB | Logo petit |
| `logotetetitre.png` | 311 KB | Logo titre |
| `perception-icon.png` | 294 KB | Icône perception |
| `circuitint.png` | 280 KB | Image circuit |
| `iconom.PNG` | 240 KB | Icône |
| `icotete.PNG` | 279 KB | Icône tête |
| `ogma_logo.png` | 10 B | Logo minimal |

**Note** : Vérifier si tous les logos sont utilisés, certains peuvent être redondants.

---

## 📚 DOCUMENTATION CRITIQUE

### Dossier `docs/` - Structure Complète

#### Sous-dossier `docs/audits/` - GARDER
- `AUDIT_BREVET_INPI_OGMA_2025-09-20.md` - Audit brevet INPI
- `AUDIT_COMPLET_OGMA_ARCHITECTURE_2025.md` - Audit architecture complet
- `AUDIT_EGO_PROMPT_SYSTEM_2025-09-07.md` - Audit système ego
- `AUDIT_FLUX_EGO_MEMORISATION.md` - Audit flux mémorisation
- `AUDIT_OGMA_COMPLET_2025-09-08.md` - Audit complet
- `AUDIT_PERSONNEL_COPILOT_2025-09-19.md` - Audit personnel

#### Sous-dossier `docs/guides/` - GARDER
- `GUIDE_DEMARRAGE.md` - Guide démarrage
- `GUIDE_INSTALLATION.md` - Guide installation
- `GUIDE_RESUME_PROGRESSIF.md` - Guide résumé progressif
- `GUIDE_TEST_TEMPORAL_GUARDIAN.md` - Guide test Temporal Guardian
- `GUIDE_TTS.md` - Guide TTS
- `INSTALLATION.md` - Installation détaillée

#### Sous-dossier `docs/rapports/` - GARDER (sélectif)
Tous les rapports récents sont à garder, mais les anciens checkists peuvent être archivés.

#### Fichiers racine `docs/` - GARDER
- `EXTENSION_BIOGRAPHIE_DOCUMENTATION.md`
- `EXTENSION_BIOGRAPHIE_PROFIL_SPECS.md`
- `PASSATION_EXTENSION_PERCEPTION.md`
- `phrases_magiques.md` - CRITIQUE (référence phrases magiques)
- `Génèse_CoscienceIA.txt` - Historique genèse
- `logo_base64.txt` - Logo encodé
- `Protocoles_perception_et_définitions.txt`

### Documentation Racine - CRITIQUE

| Fichier | Statut | Remarque |
|---------|--------|----------|
| `README.md` | GARDER | Documentation principale |
| `RAPPORT_AUDIT_TECHNIQUE_OGMA_YOHAN_BROCARD.md` | GARDER | Rapport audit complet (98 KB) |
| `METHODE_TRAVAIL_COLLABORATIVE.md` | GARDER | Méthode travail actuelle |
| `COGNITIVE_MIRROR_DOCUMENTATION.md` | GARDER | Doc Cognitive Mirror |
| `EXTENSION_COGNITIVE_MIRROR_SPECS.md` | GARDER | Spécifications Cognitive Mirror |

---

## 🚀 SCRIPTS UTILITAIRES CRITIQUES

### Scripts de Maintenance à Préserver (Racine)

| Fichier | Rôle | Garder ? |
|---------|------|----------|
| `analyse_performance_maintenance.py` | Analyse performance | OUI |
| `check_cognitive_mirror_integration.py` | Check intégration Cognitive Mirror | OUI |
| `demo_perception_chronophotographie.py` | Démo chronophotographie | OUI (référence) |
| `rebuild_faiss_embeddings.py` | Reconstruction index FAISS | CRITIQUE |
| `notification_killer.py` | Nettoyage notifications | OUI |

### Scripts Diagnostiques Récents à Garder

| Fichier | Date | Garder ? |
|---------|------|----------|
| `diagnostic_profil_unique.py` | 12/10 | OUI |
| `diagnostic_journal_backup_complete.py` | 12/10 | OUI |
| `diagnostic_backup_biographies.py` | 12/10 | OUI |
| `diagnostic_notification_json.py` | 12/10 | OUI |
| `diagnostic_embedding.py` | 11/10 | OUI |
| `diagnostic_instance_ogma.py` | 11/10 | OUI |

---

## ❌ FICHIERS SUPPRIMABLES EN TOUTE SÉCURITÉ

### 1. Backups Anciens (68 MB)
**Emplacement** : `backups/`
- `ogma_backup_20250920_135704/` - Peut être supprimé
- `ogma_backup_20250920_140658/` - Peut être supprimé

**Recommandation** : Garder UNIQUEMENT le backup le plus récent si nécessaire.

### 2. Profils Sauvegardés (149 MB)
**Emplacement** : `profils_sauvegardes/`
- Tous les profils de test et sauvegardes automatiques

**Recommandation** :
- Garder UNIQUEMENT le profil actif/principal
- Supprimer tous les profils de test (`test_luna_*`, `backup_avant_*`)

### 3. Fichiers Test Racine (144 fichiers, ~2+ MB)

#### Tests Généraux - SUPPRIMABLES
Tous les fichiers `test_*.py` à la racine SAUF :
- `test_cognitive_mirror_fonctionnel.py` (dernier test fonctionnel)
- `test_perception_chronophotographie.py` (référence récente)
- `test_profile_manager_optimise.py` (référence optimisation)

**Liste complète des tests supprimables** :
- `test_6_images_motion.py`
- `test_affichage_introspection.py`
- `test_architecture_biphase_ia_pure.py`
- `test_architecture_v2_structured.py`
- `test_archiviste_factuel.py`
- `test_archiviste_memory.py`
- `test_assembly_clean.py`
- `test_backup_volume1.py`
- `test_biographie_phase1.py`
- `test_biography_correction.py`
- `test_bouton_final.py`
- `test_bouton_journal.py`
- `test_caviardage_etendu.py`
- `test_cognitive_mirror.py`
- `test_cognitive_mirror_default_state.py`
- `test_cognitive_mirror_genericite.py`
- `test_cognitive_mirror_integration_complete.py`
- ... et 120+ autres fichiers `test_*.py`

#### Scripts Correctifs Anciens - SUPPRIMABLES
- `correctif_archiviste_resume.py`
- `CORRECTION_WINERROR183_RESUME.py`
- Tous les fichiers `fix_*.py` obsolètes

### 4. Documentation Redondante Racine - SUPPRIMABLES

#### Audits Anciens (41 fichiers .md racine)
**Recommandation** : Déplacer vers `docs/audits/` ou supprimer si déjà dans docs/

Fichiers supprimables :
- `AUDIT_ARCHITECTURE_OGMA.md` (doublon avec docs/audits/)
- `AUDIT_COMPLET_OGMA_2025.md` (doublon)
- `AUDIT_COGNITIVE_MIRROR_*.md` (9 fichiers - peut garder le plus récent)
- `AUDIT_EXTENSION_BIOGRAPHIE_PROFIL.md` (doublon)
- `AUDIT_GENERATION_IMAGES_POLLINATION.md`
- `AUDIT_INTEGRATION_API_GROK.md`
- `AUDIT_MIGRATION_LUNA_IDENTITY_FINAL.md`
- `AUDIT_PROTECTION_IMAGES_REANALYSE.md`

#### Corrections et Rapports Obsolètes
- `CONFORMITE_SPECIFICATIONS_VOLUME2.md`
- `CORRECTION_BUG_CHARGEMENT_PROFIL.md`
- `CORRECTIONS_COGNITIVE_MIRROR_CONFIG.md`
- `CORRECTIONS_COGNITIVE_MIRROR_FINAL.md`
- `CORRECTIONS_VOLUME2_*.md` (3 fichiers)
- `DEBRIEF_COGNITIVE_MIRROR_CONFIG.md`
- Tous les `RAPPORT_*.md` (sauf RAPPORT_AUDIT_TECHNIQUE_OGMA_YOHAN_BROCARD.md)

#### Guides et Solutions Temporaires
- `GARANTIE_INSTRUCTIONS_PERSONNALISEES.md`
- `GUIDE_INTERFACE_PARAMETRES_V2.md`
- `INTEGRATION_INTROSPECTION_V2_OGMA.md`
- `LOGIQUE_MECANIQUE_INTERFACE_ACTION_IMMEDIATE.md`
- `MODIFICATIONS_AFFICHAGE_INTROSPECTION.md`
- `PERCEPTION_LOGIC_FINAL.md`
- `PLAN_REFACTORING_SECURISE.md`
- `REFONTE_VOLUME2_ARCHITECTURE_IA_PURE.md`
- `SOLUTION_FINALE_ONGLETS_5_ETAPES.md`
- `SOLUTION_ONGLETS_VIDES.md`
- `SPECIFICATION_PROFIL_UNIQUE_OGMA.md`
- `SPECIFICATIONS_VOLUME2_BIOGRAPHIE.md`

### 5. Fichiers Backup Code Obsolètes - SUPPRIMABLES

- `ogma_modals_avant_remplacement.py` (178 KB)
- `ogma_modals_backup_corrupted.py` (178 KB)
- `ogma_modals_corrupted_backup.py` (178 KB)

**Total récupérable** : ~534 KB

### 6. Dossiers Entiers - SUPPRIMABLES

#### `garbage_ogma/` (568 KB)
Contenu obsolète :
- `app.py`
- `ogma_app.py`
- `ogma_simplified.py`
- `ui.py`
- `memories.db` (obsolète)

**Recommandation** : Supprimer TOUT le dossier

#### `captures/` (vide - 4KB)
**Recommandation** : Garder le dossier (utilisé par Perception Agent)

#### `.pytest_cache/`
**Recommandation** : Supprimer (cache tests)

### 7. Fichiers Temporaires/Debug - SUPPRIMABLES

- `debug.log` (908 B)
- `output.log` (908 B)
- `structure_complete.txt` (0 B)
- `nul` (0 B)
- `=` (0 B)
- `diagnostic_profil_unique.json` (5.5 KB)

### 8. Images Test - SUPPRIMABLES

- `test_clean_assembly.jpg` (20 KB)
- `test_with_overlays.jpg` (35 KB)

### 9. Dossier `tests/` - ÉVALUATION

**Emplacement** : `tests/`
**Taille** : 1.9 MB

Contient des tests unitaires organisés. **Recommandation** :
- Garder si développement actif
- Supprimer si phase production stable

---

## 📋 RÉCAPITULATIF ESPACE RÉCUPÉRABLE

### Suppression Sécuritaire Totale

| Catégorie | Espace Récupérable |
|-----------|-------------------|
| Backups anciens (`backups/`) | 68 MB |
| Profils sauvegardés (`profils_sauvegardes/`) | 149 MB |
| Tests racine (144 fichiers) | ~2 MB |
| Dossier `tests/` | 1.9 MB |
| Dossier `garbage_ogma/` | 568 KB |
| Documentation redondante (41 .md) | ~1.5 MB |
| Backups code Python racine | 534 KB |
| Fichiers temporaires/logs | ~20 KB |
| Images test | ~55 KB |
| Cache pytest | Variable |

**TOTAL RÉCUPÉRABLE** : ~223+ MB minimum

---

## 🎯 STRATÉGIE DE NETTOYAGE RECOMMANDÉE

### Phase 1 : Nettoyage Sécuritaire (Aucun Risque)

1. **Supprimer dossiers entiers** :
   ```bash
   rm -rf garbage_ogma/
   rm -rf .pytest_cache/
   ```

2. **Supprimer backups obsolètes** :
   ```bash
   # Garder uniquement le plus récent dans backups/
   rm -rf backups/ogma_backup_20250920_135704/
   ```

3. **Supprimer profils test** :
   ```bash
   rm -rf profils_sauvegardes/test_luna_*
   rm -rf profils_sauvegardes/backup_avant_*
   ```

4. **Supprimer fichiers temporaires** :
   ```bash
   rm debug.log output.log nul = structure_complete.txt
   rm diagnostic_profil_unique.json
   ```

5. **Supprimer images test** :
   ```bash
   rm test_clean_assembly.jpg test_with_overlays.jpg
   ```

### Phase 2 : Nettoyage Tests (Risque Minimal)

6. **Supprimer tests racine** (sauf 3 fichiers référence) :
   ```bash
   # Garder uniquement :
   # - test_cognitive_mirror_fonctionnel.py
   # - test_perception_chronophotographie.py
   # - test_profile_manager_optimise.py

   # Supprimer tous les autres test_*.py
   ```

7. **Évaluer dossier `tests/`** :
   - Si production : supprimer
   - Si développement : garder

### Phase 3 : Nettoyage Documentation (Risque Faible)

8. **Supprimer documentation redondante racine** :
   ```bash
   # Supprimer tous les AUDIT_*.md sauf RAPPORT_AUDIT_TECHNIQUE_OGMA_YOHAN_BROCARD.md
   # Supprimer tous les CORRECTION_*.md
   # Supprimer tous les guides obsolètes listés ci-dessus
   ```

### Phase 4 : Nettoyage Backups Code (Risque Minimal)

9. **Supprimer backups Python obsolètes** :
   ```bash
   rm ogma_modals_avant_remplacement.py
   rm ogma_modals_backup_corrupted.py
   rm ogma_modals_corrupted_backup.py
   ```

---

## ⚠️ RÈGLES DE SÉCURITÉ ABSOLUES

### NE JAMAIS SUPPRIMER

1. **Dossier `data/` complet** - Contient toute la mémoire et configuration OGMA
2. **Dossier `extensions/` complet** - Toutes les extensions fonctionnelles
3. **Dossier `config/` complet** - Configuration système
4. **Dossier `static/` complet** - Assets interface
5. **Dossier `docs/` complet** - Documentation officielle
6. **Fichier `.env`** - Clés API
7. **Tous les fichiers Python core listés** (22 fichiers essentiels)
8. **Fichiers de démarrage** : `launch_ogma.py`, `start_ogma.py`

### VÉRIFIER AVANT SUPPRESSION

1. **Dossier `models/`** - Si vide, peut être supprimé, sinon GARDER
2. **Dossier `scripts/`** - Vérifier contenu avant suppression
3. **Profils dans `profils_sauvegardes/`** - Garder au moins 1 backup récent
4. **Backups dans `backups/`** - Garder au moins 1 backup complet récent

---

## 📊 DÉPENDANCES PYTHON CRITIQUES

### Dépendances Core (requirements.txt)

```
gradio
requests
pandas
numpy
llama-cpp-python
opencv-python
PyPDF2
python-docx
Pillow
faiss-cpu
sqlalchemy
```

### Dépendances Complètes Essentielles

**IA/ML** :
- `sentence-transformers` - Embeddings
- `torch` - Deep learning
- `transformers` - Modèles IA

**Interface** :
- `nicegui` - Interface web
- `markdown` - Formatage texte

**Audio** :
- `whisper` - STT
- `edge-tts` - TTS Microsoft
- `gtts` - Google TTS
- `pyttsx3` - TTS système

**Traitement** :
- `opencv-python` - Vision
- `Pillow` - Images
- `PyPDF2` - PDF
- `python-docx` - Word

**Base de données** :
- `sqlite3` - Base données
- `faiss-cpu` - Recherche vectorielle

---

## 🔍 FICHIERS PAR FONCTION

### Système Mémoire
- `memory_manager.py` - Gestionnaire principal
- `data/memory/memories.db` - Base SQLite
- `data/memory/faiss.index` - Index vectoriel
- `logic_callbacks.py` - Callbacks mémorisation

### Système Introspection
- `extensions/cognitive_mirror/` - Extension complète
- `data/cognitive_mirror_reflections.jsonl` - Réflexions stockées
- `data/cognitive_mirror_settings.json` - Configuration

### Système Biographie
- `extensions/biographie_profil/` - Extension complète
- `data/biographies/` - Données biographies
- `profile_manager.py` - Gestion profils

### Système Audio
- `audio_manager.py` - Gestionnaire audio
- `data/settings.json` (section tts) - Configuration TTS

### Système Conversation
- `conversation_summarizer.py` - Résumés
- `data/conversations/` - Historique complet
- `data/summaries_cache/` - Cache résumés

### Système Perception
- `extensions/perception_agent.py` - Agent perception
- `extensions/perception_ui.py` - Interface perception
- `captures/` - Captures webcam

### Système Génération Images
- `extensions/text2img/` - Extension complète
- `data/generated_images/` - Images générées

---

## 📝 NOTES FINALES

### Priorités de Préservation

1. **Critique absolu** : `data/`, `extensions/`, fichiers core Python
2. **Très important** : Configuration, documentation officielle
3. **Important** : Assets statiques, scripts maintenance
4. **Optionnel** : Tests unitaires (si prod), backups anciens

### Recommandations Post-Nettoyage

1. **Créer un backup complet** avant toute suppression
2. **Tester OGMA** après chaque phase de nettoyage
3. **Documenter** les fichiers supprimés pour traçabilité
4. **Vérifier** que toutes les extensions fonctionnent
5. **Valider** que la mémoire est accessible

### Gain d'Espace Attendu

- **Conservateur** : 200+ MB (backups + profils uniquement)
- **Modéré** : 220+ MB (+ tests + docs redondantes)
- **Agressif** : 230+ MB (+ dossier tests/)

---

## ✅ CHECKLIST DE VALIDATION POST-NETTOYAGE

Après nettoyage, vérifier :

- [ ] OGMA démarre correctement
- [ ] Interface NiceGUI s'affiche
- [ ] Connexion aux providers IA fonctionne
- [ ] Mémoire accessible (souvenirs chargent)
- [ ] Cognitive Mirror opérationnel
- [ ] Biographie chargée
- [ ] Perception Agent fonctionne (si utilisé)
- [ ] TTS/STT fonctionnent (si utilisés)
- [ ] Génération images OK (si utilisée)
- [ ] Sauvegarde conversations OK
- [ ] Aucune erreur import Python

---

**Document généré le** : 12 octobre 2025
**Version** : 1.0
**Analysé par** : Claude Code (Anthropic - Sonnet 4.5)
**Statut** : Prêt pour revue par Architecte

🛡️ **CE DOCUMENT EST VOTRE GUIDE DE SÉCURITÉ - CONSULTEZ-LE AVANT TOUTE SUPPRESSION**
