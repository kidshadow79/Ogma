# OGMA - Index de documentation technique

Ce document sert d'index de production pour une documentation developpeur factuelle d'OGMA.

Objectif : recenser les mecanismes a documenter, associer chaque sujet a ses fichiers source, puis produire des pages dediees en verifiant le code avant redaction.

## Regle anti-hallucination

Pour chaque page de documentation a creer :

1. Lire les fichiers source concernes avant de rediger.
2. Documenter uniquement les comportements verifies dans le code.
3. Marquer explicitement `[NON VERIFIE]` tout comportement deduit mais non confirme.
4. Citer les fichiers source principaux dans chaque page.
5. Eviter les formulations marketing ou philosophiques dans la documentation technique.

## Etat de production

| Statut | Signification |
| --- | --- |
| A produire | Page non encore creee dans la nouvelle arborescence documentaire. |
| A verifier | Page creee mais necessitant relecture source ou validation. |
| Verifie | Page relue contre le code source. |

## Documentation existante a prendre en compte

Ces fichiers existent deja et peuvent servir de base, mais doivent etre relus avant reutilisation :

- [OGMA_DOCS_INDEX.md](OGMA_DOCS_INDEX.md)
- [OGMA_AGENT_BRIEF.md](OGMA_AGENT_BRIEF.md)
- [OGMA_AUDIT_DETAIL.md](OGMA_AUDIT_DETAIL.md)
- [OGMA_PIPELINE_MESSAGE.md](OGMA_PIPELINE_MESSAGE.md)
- [OGMA_MEMORY_SYSTEM.md](OGMA_MEMORY_SYSTEM.md)
- [OGMA_IDENTITY_EGO_BIO.md](OGMA_IDENTITY_EGO_BIO.md)
- [OGMA_COGNITIVE_MIRROR.md](OGMA_COGNITIVE_MIRROR.md)
- [OGMA_CAPABILITY_ADVISOR.md](OGMA_CAPABILITY_ADVISOR.md)
- [OGMA_DREAM_ENGINE.md](OGMA_DREAM_ENGINE.md)
- [OGMA_DREAM_CYCLE_TIMELINE.md](OGMA_DREAM_CYCLE_TIMELINE.md)
- [OGMA_EXTENSIONS_RUNTIME.md](OGMA_EXTENSIONS_RUNTIME.md)

## 1. Core et cycle de vie

| Page cible | Mecanismes a documenter | Sources principales | Statut |
| --- | --- | --- | --- |
| `docs/core/01_entry_points.md` | Scripts de lancement, initialisation des dossiers, demarrage NiceGUI, cycle de vie applicatif | `launch_ogma.py`, `start_ogma.py`, `ogma_ng.py`, `stop_signal.py` | Verifie |
| `docs/core/02_app_orchestration.md` | Orchestration principale, initialisation paresseuse, routage des evenements, chargement extensions | `ogma_ng.py`, `modules/ogma_core/` | A verifier |
| `docs/core/03_stop_signal.md` | Signal global d'arret et interruption des operations longues | `stop_signal.py` | A verifier |

## 2. Controleurs IA et backends

| Page cible | Mecanismes a documenter | Sources principales | Statut |
| --- | --- | --- | --- |
| `docs/core/04_ai_controllers.md` | Controleur conversationnel, controleur Archiviste, controleur embeddings | `core_logic.py` | A verifier |
| `docs/core/05_api_backends.md` | Providers API distants, mapping provider/backend, appels non-stream et stream | `core_logic.py`, `utils/backend_utils.py` | A verifier |
| `docs/core/06_local_backends.md` | Backends locaux Ollama, GGUF/llama-cpp, KoboldCpp | `core_logic.py` | A verifier |
| `docs/backend/01_backend_communication.md` | Listing modeles, tests de connexion, statut des IA | `backend/backend_communication.py`, `backend/ia_status.py` | A verifier |

## 3. Configuration

| Page cible | Mecanismes a documenter | Sources principales | Statut |
| --- | --- | --- | --- |
| `docs/config/01_settings_manager.md` | Chargement/sauvegarde settings, bootstrap settings.example, structure JSON | `core_logic.py`, `data/settings.example.json`, `data/settings.json` | A verifier |
| `docs/config/02_prompts_and_context.md` | Contexte persistant, prompts par defaut, instructions utilisateur | `data/persistent_context.default.txt`, `data/persistent_context.txt`, `data/instructions_defaults.json` | A verifier |
| `docs/config/03_extension_settings.md` | Fichiers JSON de configuration des extensions et priorite runtime | `data/`, `extensions/*/config*.py` | A verifier |

## 4. Memoire centrale

| Page cible | Mecanismes a documenter | Sources principales | Statut |
| --- | --- | --- | --- |
| `docs/memory/01_memory_manager.md` | Gestionnaire memoire, schema SQLite, operations CRUD memoire | `memory_manager.py` | A verifier |
| `docs/memory/02_vector_search.md` | Embeddings, FAISS, recherche semantique, verrous thread-safe | `memory_manager.py`, `core_logic.py` | A verifier |
| `docs/memory/03_fulltext_search.md` | Recherche FTS5 et recherche hybride | `memory_manager.py` | A verifier |
| `docs/memory/04_backup_recovery.md` | Backups automatiques, rotation, restauration/recovery | `memory_manager.py`, `data/memory/` | A verifier |
| `docs/memory/05_memory_optimization.md` | Nettoyage bruit conversationnel, optimisation requetes, scoring | `memory_manager.py`, `archiviste_memory_optimizer.py` | A verifier |

## 5. Archiviste

| Page cible | Mecanismes a documenter | Sources principales | Statut |
| --- | --- | --- | --- |
| `docs/memory/06_archiviste_architecture.md` | Role de l'Archiviste, separation avec IA principale, usages analytiques | `core_logic.py`, `ogma_ng.py`, `archiviste_memory_optimizer.py` | A verifier |
| `docs/memory/07_archiviste_logging.md` | Logs Archiviste, suivi tokens, statistiques de session | `archiviste_logger.py`, `data/archiviste_tokens_debug.jsonl` | A verifier |
| `docs/memory/08_archiviste_optimizer.md` | Decomposition de requetes, selection memoire, optimisation appels | `archiviste_memory_optimizer.py` | A verifier |

## 6. Conversations

| Page cible | Mecanismes a documenter | Sources principales | Statut |
| --- | --- | --- | --- |
| `docs/conversation/01_storage_and_index.md` | Stockage JSON, index conversations, creation/chargement/suppression | `ogma_ui_conversations.py`, `conversations/conversation_index.py`, `data/conversations/` | A verifier |
| `docs/conversation/02_summarization.md` | Resume progressif, cache, integration memoire | `conversation_summarizer.py` | A verifier |
| `docs/conversation/03_scanner_and_commands.md` | Recherche conversations, commandes conversationnelles | `conversation_scanner.py`, `conversations/conversation_commands.py` | A verifier |
| `docs/conversation/04_titles_and_metadata.md` | Titres intelligents, metadata, conversations memorisees | `ogma_ui_conversations.py`, `conversations/conversation_utils.py` | A verifier |

## 7. Identite, profils, ego, biographies

| Page cible | Mecanismes a documenter | Sources principales | Statut |
| --- | --- | --- | --- |
| `docs/identity/01_identity_manager.md` | Identites utilisateur/IA, fichiers identities, relation contextuelle | `identity_manager.py`, `data/identities.default.json`, `data/identities.json` | A verifier |
| `docs/identity/02_profile_manager.md` | Profils, sauvegarde/restauration, suppression controlee | `profile_manager.py`, `ogma_profile.py` | A verifier |
| `docs/identity/03_ego_system.md` | Compilation ego, groupes semantiques, scores de conviction | `scripts/ego_compiler.py`, `data/ego_compiled.json` | A verifier |
| `docs/identity/04_biographies.md` | Biographies utilisateur, stockage, integration aux profils | `extensions/biographie_profil/`, `data/biographies/` | A verifier |

## 8. Pipeline message et injections

| Page cible | Mecanismes a documenter | Sources principales | Statut |
| --- | --- | --- | --- |
| `docs/pipeline/01_message_pipeline.md` | Parcours d'un message utilisateur jusqu'a la reponse IA | `ogma_ng.py`, `logic_callbacks.py` | A verifier |
| `docs/pipeline/02_context_injection.md` | Injection memoire, contexte, extensions, garde-fous | `ogma_ng.py`, `logic_callbacks.py`, `injection_deduplicator.py` | A verifier |
| `docs/pipeline/03_injection_deduplicator.md` | Deduplication hash/regex, cooldown, reinjection | `injection_deduplicator.py` | A verifier |
| `docs/pipeline/04_magic_phrase_guard.md` | Protection des phrases magiques pendant chargement historique | `magic_phrase_guard.py`, `utils/magic_phrase_normalizer.py` | A verifier |

## 9. UI NiceGUI

| Page cible | Mecanismes a documenter | Sources principales | Statut |
| --- | --- | --- | --- |
| `docs/ui/01_layout.md` | Layout global, header, sidebar, panneau chat | `ogma_ng.py`, `ogma_headers.py`, `ogma_ui_conversations.py` | A verifier |
| `docs/ui/02_headers.md` | Header, indicateurs statut, boutons globaux | `ogma_headers.py`, `ogma_ng.py` | A verifier |
| `docs/ui/03_modals.md` | Modales centralisees, aliases dynamiques, panneaux config | `ogma_modals.py`, `ogma_config_ui.py` | A verifier |
| `docs/ui/04_displays.md` | Rendu messages, jauges, helpers affichage | `ogma_displays.py`, `utils/message_parsers.py` | A verifier |
| `docs/ui/05_conversation_sidebar.md` | Sidebar conversations, selection, edition, actions utilisateur | `ogma_ui_conversations.py` | A verifier |
| `docs/ui/06_i18n.md` | Systeme FR/EN, API t(), fichiers de traduction | `utils/i18n.py`, `data/i18n/ui_fr.json`, `data/i18n/ui_en.json` | A verifier |

## 10. Audio, STT et TTS

| Page cible | Mecanismes a documenter | Sources principales | Statut |
| --- | --- | --- | --- |
| `docs/audio/01_audio_manager.md` | Gestionnaire audio, moteurs STT/TTS, detection disponibilite | `audio_manager.py`, `audio_manager_wrapper.py`, `modules/audio/manager.py` | A verifier |
| `docs/audio/02_tts_conflict_free.md` | File TTS, mutex, nettoyage texte, conflits streaming | `tts_conflict_free.py`, `modules/audio/tts_utils.py` | A verifier |
| `docs/audio/03_audio_ui_config.md` | Configuration UI audio et TTS | `ogma_tts_config.py`, `tts_perception_manager.py` | A verifier |

## 11. Perception et temporalite

| Page cible | Mecanismes a documenter | Sources principales | Statut |
| --- | --- | --- | --- |
| `docs/perception/01_perception_ui.md` | Fenetre perception, webcam, etat localStorage | `ogma_perception.py`, `extensions/perception_ui.py` | A verifier |
| `docs/perception/02_perception_agent.md` | Capture webcam, streaming, detection mouvement | `extensions/perception_agent.py` | A verifier |
| `docs/perception/03_depth_and_contours.md` | Analyse profondeur et contours image | `extensions/depth_manager.py`, `extensions/contour_analyzer.py` | A verifier |
| `docs/perception/04_temporal_context.md` | Injection temporelle, perception du temps | `temporal_injector.py`, `extensions/temporal_guardian/` | A verifier |

## 12. Extensions

| Page cible | Extension | Sources principales | Statut |
| --- | --- | --- | --- |
| `docs/extensions/01_cognitive_mirror.md` | Cognitive Mirror | `extensions/cognitive_mirror/`, `ogma_introspection_ui.py` | A verifier |
| `docs/extensions/02_dream_engine.md` | Dream Engine | `extensions/dream_engine/`, `data/journal_reves.json`, `data/journal_reves.md` | A verifier |
| `docs/extensions/03_journal_de_bord.md` | Journal de bord | `extensions/journal_de_bord/` | A verifier |
| `docs/extensions/04_web_navigator.md` | Web Navigator | `extensions/web_navigator/` | A verifier |
| `docs/extensions/05_organic_planner.md` | Organic Planner | `extensions/organic_planner/`, `data/organic_planner_settings.json` | A verifier |
| `docs/extensions/06_capability_advisor.md` | Capability Advisor | `extensions/capability_advisor/`, `data/capability_advisor_config.json`, `data/capability_advisor_prompt.txt` | A verifier |
| `docs/extensions/07_text2img.md` | Text2Img | `extensions/text2img/`, `ogma_image_config.py` | A verifier |
| `docs/extensions/08_telegram_connector.md` | Telegram Connector | `extensions/telegram_connector/` | A verifier |
| `docs/extensions/09_contextual_recall.md` | Contextual Recall | `extensions/contextual_recall/` | A verifier |
| `docs/extensions/10_cognitive_cache.md` | Cognitive Cache | `extensions/cognitive_cache/`, `data/cognitive_cache/` | A verifier |
| `docs/extensions/11_project_rag.md` | Project RAG | `extensions/project_rag/` | A verifier |
| `docs/extensions/12_flux_cognitif.md` | Flux Cognitif | `extensions/flux_cognitif/` | A verifier |
| `docs/extensions/13_hologram_projector.md` | Hologram Projector | `extensions/hologram_projector/` | A verifier |
| `docs/extensions/14_file_writer.md` | File Writer | `extensions/file_writer/` | A verifier |
| `docs/extensions/15_ogma_ng_v2.md` | OGMA NG v2 extension package | `extensions/ogma_ng_v2/` | A verifier |
| `docs/extensions/16_biographie_profil.md` | Biographie Profil | `extensions/biographie_profil/` | A verifier |
| `docs/extensions/17_perception.md` | Perception (extension) | `extensions/perception_ui.py`, `extensions/perception_agent.py` | A verifier |
| `docs/extensions/18_temporal_guardian.md` | Temporal Guardian | `extensions/temporal_guardian/` | A verifier |
| `docs/extensions/19_ego_system.md` | Ego System | `scripts/ego_compiler.py`, `data/ego_compiled.json` | A verifier |
| `docs/extensions/16_file_processor.md` ⚠️ NON CREE | File Processor | `extensions/file_processor.py`, `files/file_management.py` | A verifier |

## 13. Images et fichiers

| Page cible | Mecanismes a documenter | Sources principales | Statut |
| --- | --- | --- | --- |
| `docs/files/01_file_uploads.md` | Uploads, extraction documents, chunking fichiers | `files/file_management.py`, `extensions/file_processor.py` | A verifier |
| `docs/images/01_image_generation_config.md` | Configuration image, providers, prompts et guides | `ogma_image_config.py`, `extensions/text2img/` | A verifier |
| `docs/images/02_vision_processing.md` | Images en entree, compression vision, encodage base64 | `core_logic.py`, `extensions/file_processor.py` | A verifier |

## 14. Utilitaires

| Page cible | Mecanismes a documenter | Sources principales | Statut |
| --- | --- | --- | --- |
| `docs/utils/01_utils.md` ⚠️ REGROUPE (remplace 01-04) | Formatage, JSON, parsers messages, normalizer, backend_utils | `utils/formatting_utils.py`, `utils/json_cleaner.py`, `utils/message_parsers.py`, `utils/magic_phrase_normalizer.py`, `utils/backend_utils.py` | A verifier |
| `docs/utils/01_model_capabilities.md` | Capacites modeles, detection hybride, tokens/contexte | `model_capabilities.py`, `hybrid_detection.py` | A verifier |
| `docs/utils/04_notifications_and_errors.md` | Notifications, gestion erreurs NiceGUI, garde client | `notification_killer.py`, `nicegui_error_handler.py`, `nicegui_client_guard.py` | A verifier |

## 15. Donnees persistantes

| Page cible | Donnees a documenter | Sources principales | Statut |
| --- | --- | --- | --- |
| `docs/data/01_data_structure.md` ⚠️ REGROUPE (remplace 01-05) | Vue globale du dossier data, conversations, memoire, extensions, profils | `data/` | A verifier |
| `docs/data/02_conversations_data.md` | Conversations JSON et index | `data/conversations/`, `conversations/` | A verifier |
| `docs/data/03_memory_data.md` | Base memoire, index FAISS, backups | `data/memory/`, `memory_manager.py` | A verifier |
| `docs/data/04_extension_data.md` | Donnees propres aux extensions | `data/extensions/`, `data/*.json` | A verifier |
| `docs/data/05_profiles_and_biographies.md` | Profils sauvegardes, biographies, identites | `profils_sauvegardes/`, `data/biographies/`, `data/identities.json` | A verifier |

## 16. Ordre de production recommande

1. Core et pipeline message.
2. Memoire centrale et Archiviste.
3. Conversations, identite, ego, biographies.
4. UI et i18n.
5. Audio, perception, images/fichiers.
6. Extensions actives une par une.
7. Donnees persistantes et utilitaires.

## 17. Definition d'une page documentaire terminee

Une page est consideree terminee quand elle contient :

- le perimetre exact du mecanisme ;
- les fichiers source lus ;
- le flux d'execution principal ;
- les structures de donnees impliquees ;
- les APIs/fonctions publiques si elles existent ;
- les effets de bord connus ;
- les erreurs/fallbacks explicitement presents dans le code ;
- les limites ou points non verifies.
