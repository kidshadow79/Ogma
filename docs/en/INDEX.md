# OGMA — Technical Documentation Index (English)

This document is the production index for OGMA's factual developer documentation.

Objective: list all mechanisms to document, associate each topic with its source files, and produce dedicated pages after verifying the code.

> French version: [../fr/INDEX.md](../fr/INDEX.md)

## Anti-hallucination Rule

For each documentation page:

1. Read the source files before writing.
2. Document only behaviors verified in the code.
3. Explicitly mark `[UNVERIFIED]` any behavior inferred but not confirmed.
4. Cite the main source files in each page.
5. Avoid marketing or philosophical phrasing in technical documentation.

## Production Status

| Status | Meaning |
| --- | --- |
| To produce | Page not yet created in the new documentation tree. |
| To verify | Page created but needs source review or validation. |
| Verified | Page reviewed against source code. |

## 1. Core and Application Lifecycle

| Target page | Mechanisms to document | Main sources | Status |
| --- | --- | --- | --- |
| `docs/en/core/01_entry_points.md` | Launch scripts, folder init, NiceGUI startup, app lifecycle | `launch_ogma.py`, `ogma_ng.py`, `stop_signal.py` | To verify |
| `docs/en/core/02_app_orchestration.md` | Main orchestration, lazy init, event routing, extension loading | `ogma_ng.py`, `modules/ogma_core/` | To verify |
| `docs/en/core/03_stop_signal.md` | Global stop signal and interruption of long operations | `stop_signal.py` | To verify |

## 2. AI Controllers and Backends

| Target page | Mechanisms to document | Main sources | Status |
| --- | --- | --- | --- |
| `docs/en/core/04_ai_controllers.md` | Conversational controller, Archivist controller, embedding controller | `core_logic.py` | To verify |
| `docs/en/core/05_api_backends.md` | Remote API providers, provider/backend mapping, streaming calls | `core_logic.py`, `utils/backend_utils.py` | To verify |
| `docs/en/core/06_local_backends.md` | Local backends: Ollama, GGUF/llama-cpp, KoboldCpp | `core_logic.py` | To verify |
| `docs/en/backend/01_backend_communication.md` | Model listing, connection tests, AI status | `backend/backend_communication.py`, `backend/ia_status.py` | To verify |

## 3. Configuration

| Target page | Mechanisms to document | Main sources | Status |
| --- | --- | --- | --- |
| `docs/en/config/01_settings_manager.md` | Settings load/save, bootstrap from settings.example, JSON structure | `core_logic.py`, `data/settings.example.json`, `data/settings.json` | To verify |
| `docs/en/config/02_prompts_and_context.md` | Persistent context, default prompts, user instructions | `data/persistent_context.default.txt`, `data/persistent_context.txt`, `data/instructions_defaults.json` | To verify |
| `docs/en/config/03_extension_settings.md` | Extension JSON config files and runtime priority | `data/`, `extensions/*/config*.py` | To verify |

## 4. Core Memory

| Target page | Mechanisms to document | Main sources | Status |
| --- | --- | --- | --- |
| `docs/en/memory/01_memory_manager.md` | Memory manager, SQLite schema, memory CRUD operations | `memory_manager.py` | To verify |
| `docs/en/memory/02_vector_search.md` | Embeddings, FAISS, semantic search, thread-safe locks | `memory_manager.py`, `core_logic.py` | To verify |
| `docs/en/memory/03_fulltext_search.md` | FTS5 full-text search and hybrid search | `memory_manager.py` | To verify |
| `docs/en/memory/04_backup_recovery.md` | Automatic backups, rotation, restore/recovery | `memory_manager.py`, `data/memory/` | To verify |
| `docs/en/memory/05_memory_optimization.md` | Conversational noise cleanup, query optimization, scoring | `memory_manager.py`, `archiviste_memory_optimizer.py` | To verify |

## 5. The Archivist

| Target page | Mechanisms to document | Main sources | Status |
| --- | --- | --- | --- |
| `docs/en/memory/06_archiviste_architecture.md` | Archivist role, separation from main AI, analytical uses | `core_logic.py`, `ogma_ng.py`, `archiviste_memory_optimizer.py` | To verify |
| `docs/en/memory/07_archiviste_logging.md` | Archivist logs, token tracking, session statistics | `archiviste_logger.py`, `data/archiviste_tokens_debug.jsonl` | To verify |
| `docs/en/memory/08_archiviste_optimizer.md` | Query decomposition, memory selection, call optimization | `archiviste_memory_optimizer.py` | To verify |

## 6. Conversations

| Target page | Mechanisms to document | Main sources | Status |
| --- | --- | --- | --- |
| `docs/en/conversation/01_storage_and_index.md` | JSON storage, conversation index, create/load/delete | `ogma_ui_conversations.py`, `conversations/conversation_index.py`, `data/conversations/` | To verify |
| `docs/en/conversation/02_summarization.md` | Progressive summary, cache, memory integration | `conversation_summarizer.py` | To verify |
| `docs/en/conversation/03_scanner_and_commands.md` | Conversation search, conversational commands | `conversation_scanner.py`, `conversations/conversation_commands.py` | To verify |
| `docs/en/conversation/04_titles_and_metadata.md` | Smart titles, metadata, memorized conversations | `ogma_ui_conversations.py`, `conversations/conversation_utils.py` | To verify |

## 7. Identity, Profiles, Ego, Biographies

| Target page | Mechanisms to document | Main sources | Status |
| --- | --- | --- | --- |
| `docs/en/identity/01_identity_manager.md` | User/AI identities, identity files, contextual relationship | `identity_manager.py`, `data/identities.default.json`, `data/identities.json` | To verify |
| `docs/en/identity/02_profile_manager.md` | Profiles, save/restore, controlled deletion | `profile_manager.py`, `ogma_profile.py` | To verify |
| `docs/en/identity/03_ego_system.md` | Ego compilation, semantic groups, conviction scores | `scripts/ego_compiler.py`, `data/ego_compiled.json` | To verify |
| `docs/en/identity/04_biographies.md` | User biographies, storage, profile integration | `extensions/biographie_profil/`, `data/biographies/` | To verify |

## 8. Message Pipeline and Injections

| Target page | Mechanisms to document | Main sources | Status |
| --- | --- | --- | --- |
| `docs/en/pipeline/01_message_pipeline.md` | Journey of a user message through to the AI response | `ogma_ng.py`, `logic_callbacks.py` | To verify |
| `docs/en/pipeline/02_context_injection.md` | Memory injection, context, extensions, safeguards | `ogma_ng.py`, `logic_callbacks.py`, `injection_deduplicator.py` | To verify |
| `docs/en/pipeline/03_injection_deduplicator.md` | Hash/regex deduplication, cooldown, re-injection | `injection_deduplicator.py` | To verify |
| `docs/en/pipeline/04_magic_phrase_guard.md` | Magic phrase protection during history loading | `magic_phrase_guard.py`, `utils/magic_phrase_normalizer.py` | To verify |

## 9. NiceGUI Interface

| Target page | Mechanisms to document | Main sources | Status |
| --- | --- | --- | --- |
| `docs/en/ui/01_layout.md` | Global layout, header, sidebar, chat panel | `ogma_ng.py`, `ogma_headers.py`, `ogma_ui_conversations.py` | To verify |
| `docs/en/ui/02_headers.md` | Header, status indicators, global buttons | `ogma_headers.py`, `ogma_ng.py` | To verify |
| `docs/en/ui/03_modals.md` | Centralized modals, dynamic aliases, config panels | `ogma_modals.py`, `ogma_config_ui.py` | To verify |
| `docs/en/ui/04_displays.md` | Message rendering, gauges, display helpers | `ogma_displays.py`, `utils/message_parsers.py` | To verify |
| `docs/en/ui/05_conversation_sidebar.md` | Conversation sidebar, selection, editing, user actions | `ogma_ui_conversations.py` | To verify |
| `docs/en/ui/06_i18n.md` | FR/EN system, t() API, translation files | `utils/i18n.py`, `data/i18n/ui_fr.json`, `data/i18n/ui_en.json` | To verify |

## 10. Audio, STT and TTS

| Target page | Mechanisms to document | Main sources | Status |
| --- | --- | --- | --- |
| `docs/en/audio/01_audio_manager.md` | Audio manager, STT/TTS engines, availability detection | `audio_manager.py`, `audio_manager_wrapper.py`, `modules/audio/manager.py` | To verify |
| `docs/en/audio/02_tts_conflict_free.md` | TTS queue, mutex, text cleanup, streaming conflicts | `tts_conflict_free.py`, `modules/audio/tts_utils.py` | To verify |
| `docs/en/audio/03_audio_ui_config.md` | Audio and TTS UI configuration | `ogma_tts_config.py`, `tts_perception_manager.py` | To verify |

## 11. Perception and Temporality

| Target page | Mechanisms to document | Main sources | Status |
| --- | --- | --- | --- |
| `docs/en/perception/01_perception_ui.md` | Perception window, webcam, localStorage state | `ogma_perception.py`, `extensions/perception_ui.py` | To verify |
| `docs/en/perception/02_perception_agent.md` | Webcam capture, streaming, motion detection | `extensions/perception_agent.py` | To verify |
| `docs/en/perception/03_depth_and_contours.md` | Depth and contour image analysis | `extensions/depth_manager.py`, `extensions/contour_analyzer.py` | To verify |
| `docs/en/perception/04_temporal_context.md` | Temporal injection, time perception | `temporal_injector.py`, `extensions/temporal_guardian/` | To verify |

## 12. Extensions

| Target page | Extension | Main sources | Status |
| --- | --- | --- | --- |
| `docs/en/extensions/01_cognitive_mirror.md` | Cognitive Mirror | `extensions/cognitive_mirror/`, `ogma_introspection_ui.py` | To verify |
| `docs/en/extensions/02_dream_engine.md` | Dream Engine | `extensions/dream_engine/`, `data/journal_reves.json`, `data/journal_reves.md` | To verify |
| `docs/en/extensions/03_journal_de_bord.md` | Daily Journal | `extensions/journal_de_bord/` | To verify |
| `docs/en/extensions/04_web_navigator.md` | Web Navigator | `extensions/web_navigator/` | To verify |
| `docs/en/extensions/05_organic_planner.md` | Organic Planner | `extensions/organic_planner/`, `data/organic_planner_settings.json` | To verify |
| `docs/en/extensions/06_capability_advisor.md` | Capability Advisor | `extensions/capability_advisor/`, `data/capability_advisor_config.json` | To verify |
| `docs/en/extensions/07_text2img.md` | Text2Img | `extensions/text2img/`, `ogma_image_config.py` | To verify |
| `docs/en/extensions/08_telegram_connector.md` | Telegram Connector | `extensions/telegram_connector/` | To verify |
| `docs/en/extensions/09_contextual_recall.md` | Contextual Recall | `extensions/contextual_recall/` | To verify |
| `docs/en/extensions/10_cognitive_cache.md` | Cognitive Cache | `extensions/cognitive_cache/`, `data/cognitive_cache/` | To verify |
| `docs/en/extensions/11_project_rag.md` | Project RAG | `extensions/project_rag/` | To verify |
| `docs/en/extensions/12_flux_cognitif.md` | Cognitive Flow | `extensions/flux_cognitif/` | To verify |
| `docs/en/extensions/13_hologram_projector.md` | Hologram Projector | `extensions/hologram_projector/` | To verify |
| `docs/en/extensions/14_file_writer.md` | File Writer | `extensions/file_writer/` | To verify |
| `docs/en/extensions/15_ogma_ng_v2.md` | OGMA NG v2 extension package | `extensions/ogma_ng_v2/` | To verify |
| `docs/en/extensions/16_biographie_profil.md` | Biography Profile | `extensions/biographie_profil/` | To verify |
| `docs/en/extensions/17_perception.md` | Perception (extension) | `extensions/perception_ui.py`, `extensions/perception_agent.py` | To verify |
| `docs/en/extensions/18_temporal_guardian.md` | Temporal Guardian | `extensions/temporal_guardian/` | To verify |
| `docs/en/extensions/19_ego_system.md` | Ego System | `scripts/ego_compiler.py`, `data/ego_compiled.json` | To verify |
| `docs/en/extensions/16_file_processor.md` | File Processor | `extensions/file_processor.py`, `files/file_management.py` | To verify |

## 13. Images and Files

| Target page | Mechanisms to document | Main sources | Status |
| --- | --- | --- | --- |
| `docs/en/files/01_file_uploads.md` | Uploads, document extraction, file chunking | `files/file_management.py`, `extensions/file_processor.py` | To verify |
| `docs/en/images/01_image_generation_config.md` | Image config, providers, prompts and guides | `ogma_image_config.py`, `extensions/text2img/` | To verify |
| `docs/en/images/02_vision_processing.md` | Input images, vision compression, base64 encoding | `core_logic.py`, `extensions/file_processor.py` | To verify |

## 14. Utilities

| Target page | Mechanisms to document | Main sources | Status |
| --- | --- | --- | --- |
| `docs/en/utils/01_utils.md` | Formatting, JSON, message parsers, normalizer, backend_utils | `utils/formatting_utils.py`, `utils/json_cleaner.py`, `utils/message_parsers.py`, `utils/magic_phrase_normalizer.py`, `utils/backend_utils.py` | To verify |
| `docs/en/utils/01_model_capabilities.md` | Model capabilities, hybrid detection, tokens/context | `model_capabilities.py`, `hybrid_detection.py` | To verify |
| `docs/en/utils/04_notifications_and_errors.md` | Notifications, NiceGUI error handling, client guard | `notification_killer.py`, `nicegui_error_handler.py`, `nicegui_client_guard.py` | To verify |

## 15. Persistent Data

| Target page | Data to document | Main sources | Status |
| --- | --- | --- | --- |
| `docs/en/data/01_data_structure.md` | Global overview of the data/ folder | `data/` | To verify |
| `docs/en/data/02_conversations_data.md` | Conversations JSON and index | `data/conversations/`, `conversations/` | To verify |
| `docs/en/data/03_memory_data.md` | Memory database, FAISS index, backups | `data/memory/`, `memory_manager.py` | To verify |
| `docs/en/data/04_extension_data.md` | Extension-specific data | `data/extensions/`, `data/*.json` | To verify |
| `docs/en/data/05_profiles_and_biographies.md` | Saved profiles, biographies, identities | `profils_sauvegardes/`, `data/biographies/`, `data/identities.json` | To verify |
