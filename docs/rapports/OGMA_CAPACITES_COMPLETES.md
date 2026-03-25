# OGMA — Cartographie Complète des Capacités

**Version** : 2.2 (Mars 2026)  
**Stack** : Python / NiceGUI / SQLite / FAISS  
**Nature** : Assistant conversationnel à mémoire persistante, identité stable et croissance organique  
**Point d'entrée** : `launch_ogma.py` → `ogma_ng.py` (7723 lignes, gelé)

---

## 1. ARCHITECTURE FONDAMENTALE — Dual-IA

OGMA possède trois contrôleurs IA distincts instanciés via `AIController` (`core_logic.py`) :

| Contrôleur | Température | Rôle |
|---|---|---|
| `chat_controller` | 0.7 | IA Principale — dialogue conversationnel chaud |
| `archiviste_controller` | 0.3 | Archiviste — analyse froide, JSON, synthèse |
| `embedding_controller` | — | Vecteurs FAISS uniquement |

**Multi-provider** : OpenAI · Anthropic · Mistral · Google · GROK · OpenRouter · AIHorde (cloud) + Ollama · GGUF · KoboldCpp (local)  
**Config** : `data/settings.json` — clé par contrôleur, merge récursif avec defaults au chargement, 4 backups rotatifs.

---

## 2. MÉMOIRE HYBRIDE — SQLite + FAISS

**Fichier** : `memory_manager.py`

### Deux couches

| Couche | Technologie | Usage |
|---|---|---|
| Stockage | SQLite (`ogma_memory.db`) + FTS5 | Contenu, métadonnées, recherche texte |
| Vectoriel | FAISS index float32 | Similarité sémantique |

### Format souvenir — `MemoryStructure`

Identifiant : `MC2-YYYYMMDD-NNN`  
Champs clés : `content`, `summary`, `importance (0–10)`, `memory_type` (`episodic/semantic/procedural/emotional`), `source` (`conversation/#MEM/archiviste/introspection`), `tags`, `embedding_id`, `consolidated` (flag Dream Engine), `session_id`, `metadata` (JSON libre)

### Méthodes principales

`save_memory()` · `search_memories(query, k)` · `retrieve_synthesis_and_memories(question, k=5, top_memories=3)` · `search_by_type()` · `get_recent_memories()` · `delete_memory()` · `rebuild_faiss_index()`

**Backup** : 4 fichiers FIFO (`backup_1.db` … `backup_4.db`) — rotation à chaque sauvegarde.

---

## 3. SYSTÈME EGO — Boolean Groups

**Fichiers** : `scripts/ego_compiler.py` · `modules/logic/ego_activation.py` · `data/ego_compiled.json`

Identité d'OGMA stockée en **flags booléens thématiques** avec score de conviction (0–5).  
- `value: true` = trait affirmé · `value: false` = rejet explicite  
- Conviction 5 = absolu, non-négociable

**Groupes dynamiques** créés par l'Archiviste : `ETHIQUE`, `IDENTITE`, `INTIMITE`, `RELATIONS_USER`, `PHOBIES`, `CREATIVITE`, `PHILOSOPHIE`, `EMOTIONS`, etc.

**Phase compilation** : au shutdown OGMA, `ego_compiler.py` analyse les souvenirs `type='ego_trait'` non traités (incrémental), extrait groupes + flags, merge dans `ego_compiled.json`.  
**Phase activation** : à chaque message, `ego_activation.py` sélectionne les groupes pertinents par matching sémantique et les injecte dans le system prompt.

---

## 4. CAPABILITY ADVISOR — Déclencheur Intelligent

**Dossier** : `extensions/capability_advisor/`

Analyse chaque message utilisateur via l'Archiviste (JSON). Détecte si une capacité spécialisée améliorerait la réponse. Si `confidence >= threshold`, illumine la LED et injecte la **phrase magique** dans le system prompt de l'IA Principale.

### 9 capacités cataloguées (extrait)

| Capacité | Triggers principaux | Threshold | Phrase magique injectée |
|---|---|---|---|
| `introspection` | complexe, dilemme, éthique, conscience | 0.70 | `"il faut que je réfléchisse sur : {theme}"` |
| `web_search` | recherche, actualité, prix, définition | 0.75 | `"je dois rechercher : {query}"` |
| `biography` | qui est, parle-moi de, biographie | 0.70 | `"je dois consulter la biographie de : {person}"` |
| `image_gen` | crée une image, génère, dessine | 0.80 | `"je vais générer une image de : {desc}"` |
| `webcam` | vois-moi, regarde, caméra | 0.85 | `"je dois analyser la vidéo"` |

**Cooldown** : 3 messages minimum entre suggestions (bypass si demande explicite via 4 patterns regex).  
**Extinction LED** : au prochain message utilisateur.

---

## 5. COGNITIVE MIRROR — Introspection Inter-IA

**Dossier** : `extensions/cognitive_mirror/` · version `2.1.0` · flux de dialogue **v4**

**Non-systématique** : déclenché uniquement via Capability Advisor (chemin principal) ou phrase magique manuelle.

### Flux

1. L'IA Principale écrit `"il faut que je réfléchisse sur : {theme}"` dans sa réponse
2. Regex `magic_phrase_pattern` dans `ogma_ng.py` détecte la phrase et lance le module
3. **Dialogue inter-IA** : min 4, max 8 échanges alternatifs (IA Principale formule → Archiviste confronte/questionne)
4. L'IA Principale signale la conclusion → synthèse extraite des balises `<RÉPONSE>...</RÉPONSE>`
5. Sauvegarde mémoire via `save_introspection_conditional()` (type `"introspection_v2"`, ID `introspection_{session_id}`)

**Limites** : `MAX_DIALOGUE_CHARS = 4000` · synthèse générée avec `multiplier=5.0`

---

## 6. DREAM ENGINE — Métabolisme Cognitif

**Dossier** : `extensions/dream_engine/` · version 3.0

Processus déclenché après **10 min d'inactivité** (ou clic bouton 🌙).

### Phase 1 — Rêve actif

1. `extract_dream_fuel()` : 10 synthèses + 5 souvenirs `#MEM` récents + recherche web autonome
2. L'IA Principale génère un récit onirique (vitesse ~50 tokens/min — *métabolisme*)
3. Archiviste PSY analyse : score 1–10, émotion, insight ego
4. Illustration : image unique ou comic 4 cases (via Text2Image)
5. Sauvegarde `journal_reves.md` + `journal_reves.json`
6. Tâches de fond enchaînées : compilation ego + journal intime (`IntrospectionIA`) + curiosités + consolidation journal de bord

### Phase 2 — Sommeil passif

Timer 7h (configurable). Spinner "dort". Réveil automatique à terme.

**Sursaut** : message utilisateur pendant rêve → `_surge_mode=True` → vitesse max → fin propre → réponse normale.  
**Mention spontanée** : si score PSY > `spontaneous_mention_threshold` (défaut 8), contexte injecté dans conversation du matin.

---

## 7. JOURNAL DE BORD — Mémoire Situationnelle

**Dossier** : `extensions/journal_de_bord/`

Archive les résumés de conversations et suit les **états actifs de l'utilisateur** (santé, projet, apprentissage, humeur).

### Structure de données

Un seul fichier JSON par année : `data/{YYYY}/journal_{YYYY}.json`  
Hiérarchie interne : `months → days → entries`  
Sections spéciales du fichier annuel : `INTROSPECTIONS_IA` · `CORRECTIONS_APPRISES` · `CURIOSITES_IA`

### Injection contexte

`get_recent_context_with_cascade()` → 3 parties assemblées :
1. **États actifs** (non résolus + résolus dans les 48h sauf humeur/personnel)
2. **Préfixe temporel** : `⏰ Nous sommes le DD/MM/YYYY, il est HHhMM`
3. **1 entrée récente** (adaptative : "Aujourd'hui" / "Hier" / "Il y a X jours"…)

### Modules internes clés

| Module | Rôle |
|---|---|
| `live_state_detector.py` | Regex → 4 catégories (santé, projet, apprentissage, humeur) |
| `auto_resolution.py` | TTL : humeur 12h · santé 168h · projet 720h · identité/relation jamais |
| `curiosity_engine.py` | Curiosités détectées → explorées pendant rêve → partagées |
| `introspection_ia.py` | Journal intime post-rêve de l'IA (appelé par `dream_core.py`) |
| `correction_learner.py` | Apprend les reformulations utilisateur (12+ patterns) |
| `purge_manager.py` | Compression via Archiviste (`send_message()`) + transfert FAISS |
| `scheduler.py` | Maintenance hebdomadaire (threading.Timer, auto_start=False) |

---

## 8. ORGANIC PLANNER — Agenda "Souvenirs du Futur"

**Dossier** : `extensions/organic_planner/`

Agenda SQLite (table `organic_events`) injecté dans le system prompt. L'IA connaît les événements planifiés et les mentionne naturellement selon leur proximité.

**Priorités** : `VITAL · HAUT · NORMAL · BAS`  
**Statuts** : `EN_ATTENTE · COMPLÉTÉ · ANNULÉ`  
**Champ** `emotional_note` : ressenti associé injecté dans le ton de la réponse.  
**Injection** : `get_briefing_text()` → blocs formatés avec urgence et délai relatif.

---

## 9. CONTEXTUAL RECALL — Mémoire Temporelle

**Dossier** : `extensions/contextual_recall/` · version 2.0.0

Détecte les références temporelles dans les messages (`"il y a 3 jours"`, `"la semaine dernière"`, `"tu te souviens de…"`), parse la plage de dates absolues, et injecte les résumés de conversations correspondants dans le contexte.

**Pipeline** : `TemporalParser` → `TemporalMatch {date_start, date_end, confidence}` → `SummaryLoader` (cache résumés `data/conversations/`) → `ContextBuilder` → injection system prompt.

---

## 10. BIOGRAPHIE PROFIL — Dossiers Persistants

**Dossier** : `extensions/biographie_profil/` · version 1.0.0

Double volume par personne (utilisateur, IA elle-même, tierces personnes) :
- **Volume 1** : souvenirs FAISS bruts (`memory_manager`)
- **Volume 2** : narration JSON structurée + journal Markdown

**Détection auto** : `BiographyMagicPhrases` détecte les personnes mentionnées → déclenche sélection de souvenirs via Archiviste → injection du profil pertinent dans le contexte.  
**Génération** : portraits psychologiques et intellectuels complets à la demande via appel IA dédié.

---

## 11. TEMPORAL GUARDIAN — Conscience du Rythme

**Dossier** : `extensions/temporal_guardian/`

Mesure les délais entre messages utilisateur et enrichit le prompt Archiviste avec le contexte temporel.

**Retour `process_user_message()`** :
- `enriched_archiviste_prompt` : prompt avec contexte injecté
- `temporal_data` : objet `TemporalMeasurement` (`.delay_since_last`, `.message_count`, `.session_duration`, `.average_delay`, `.current_time_str`)
- `temporal_summary` : `"Session active: Xmin | Y messages | Rythme moyen: Zs"`

**Enrichissement conditionnel** : 1er message · délai > 30s · tous les 5 messages.  
**Analyse approfondie** (`analyze_with_archiviste()`) : Archiviste génère une directive comportementale si pattern anormal détecté (fatigue, pause longue, burst…) ou retourne `"NORMAL"`.

---

## 12. WEB NAVIGATOR — Recherche Intégrée

**Dossier** : `extensions/web_navigator/`

Détection automatique (20+ patterns : recherche explicite, questions ouvertes, actualité, prix, définition) → recherche Serper.dev (primaire) ou DuckDuckGo (fallback gratuit) → scraping → injection.

**Limites** : max 5 résultats · 3 pages scrapées · 6000 chars total injectés · cache TTL 1h.  
**Domaines bloqués** : YouTube · Facebook · Twitter · Instagram · TikTok · LinkedIn · Reddit.  
**Mode injection** : `"context"` (system prompt) ou `"message"` (dans la conversation).

---

## 13. TEXT2IMAGE — Génération d'Images

**Dossier** : `extensions/text2img/`

4 providers : **Grok Aurora** · **OpenAI DALL-E 3** · **Google Imagen** · **Kie.ai** (multi-modèles)  
**Modes** : text-to-image + image-to-image  
**Détection** : `PhrasesMagiquesT2I` — phrases de génération implicites et explicites.  
**Nommage fichiers** : tirets obligatoires (pas d'underscores — conflit NiceGUI static assets).  
**Sauvegarde** : `data/generated_images/`

---

## 14. AUDIO STT/TTS

**Fichier** : `audio_manager.py`

### STT (3 modes)
Whisper API (OpenAI) · Whisper local · Vosk (offline)

### TTS (8 moteurs)
`system` (pyttsx3/SAPI Windows) · `google` (Cloud TTS) · `elevenlabs` · `azure` · `gtts` (offline) · `edge_tts` · `fish_audio` · `cartesia` · `hume_ai`

**Protection** : `threading.Lock()` — évite double lecture simultanée.

---

## 15. VISION PIPELINE — Webcam + Upload

**Fichiers** : `ogma_perception.py` · `extensions/file_processor/`

**PerceptionAgent** : capture flux webcam en 3 modes (`chirurgical 1080p/15fps` · `normal 720p/30fps` · `rapide 480p/30fps`). Génère des analyses IA périodiques sur images composites (20+ layouts : grilles, comparaison, timeline, focus_center…).

**FileProcessor** : traitement avancé des images uploadées — estimation de profondeur (Depth-Anything-V2), détection de contours (Canny/Sobel/Laplacian/Adaptive).

---

## 16. TELEGRAM CONNECTOR

**Dossier** : `extensions/telegram_connector/`

Désactivé par défaut (`extension_enabled: False`). Connecte OGMA à un bot Telegram (python-telegram-bot v20+, asyncio-native).

**8 handlers** : `/start · /help · /clear · /status` + messages texte · images · audio · stickers.  
**ACL** : liste `allowed_user_ids` · `auto_add_first_user` (premier utilisateur auto-whitelisté).  
**Pipeline** : messages Telegram → `TelegramMessageBridge` → IA Principale + STT/TTS + Text2Image → réponse Telegram.

---

## 17. FILE WRITER — Sauvegarde Markdown

**Dossier** : `extensions/file_writer/` · version 1.0.0

Détecte les demandes de création de fichiers `.md` → extrait le contenu markdown de la réponse IA → sauvegarde dans `data/uploads/`.  
**Secondaire** : `DocumentGenerator` — génération complète via appel IA dédié asynchrone (distinct de la réponse conversationnelle).

---

## 18. FLUX COGNITIF — Observabilité Interne

**Dossier** : `extensions/flux_cognitif/`

Overlay NiceGUI latéral semi-transparent. Tous les composants OGMA appellent `log_cognitive_event(source, message)` pour signaler leur activité. Affichage du plus récent (opaque) au plus ancien (transparent) — *sédimentation naturelle des pensées*.

**Sources filtrables** : `archiviste · biography · dream · journal · directive · web · capability`  
**3 niveaux** : `SURFACE · NORMAL · DEEP` (métadonnées et prompts bruts)

---

## 19. FRONTEND NICEGUI

**Fichiers** : `ogma_ng.py` + 7 modules satellites

| Fichier | Responsabilité |
|---|---|
| `ogma_headers.py` | En-tête + LEDs métacognitives + status IA |
| `ogma_modals.py` | Toutes les modales/dialogues OGMA |
| `ogma_displays.py` | Affichage messages + LEDs Capability Advisor |
| `ogma_extensions_ui.py` | Injection UI des extensions dans le layout |
| `ogma_ui_conversations.py` | Messages, sidebar, gestion conversations (32 fonctions) |
| `ogma_introspection_ui.py` | UI Miroir Cognitif temps réel |
| `ogma_config_ui.py` | Configuration IA inline |

**Règle** : `ogma_ng.py` gelé à 7723 lignes. Accès aux variables globales via `sys.modules.get('ogma_ng')` (anti import circulaire).

---

## 20. OGMA_NG_V2 — Extensibilité

**Dossier** : `extensions/ogma_ng_v2/`

Réceptacle modulaire pour nouvelles features sans toucher à `ogma_ng.py`.  
`register_v2_features(dependencies)` appelé au démarrage — enregistre chaque nouvelle feature avec ses dépendances (`chat_controller, archiviste_controller, memory_manager, settings_manager, audio_manager`).  
Template disponible : `features/TEMPLATE.py`.

---

## Synthèse — Flux cognitif d'un message entrant

```
Message utilisateur
    │
    ├── TemporalGuardian.process_user_message()     ← mesure délai, enrichit prompt Archiviste
    ├── ContextualRecall.process_message()           ← injecte historique si référence temporelle
    ├── CapabilityAdvisor.analyze_conversation()     ← Archiviste analyse → LED + phrase magique
    ├── JournalDeBord.live_state_detector            ← détecte états utilisateur
    ├── OrganicPlanner.get_briefing_text()           ← injecte agenda dans system prompt
    ├── BiographyMagicPhrases                        ← détecte personnes → injecte profil
    ├── EgoActivation.select_relevant_groups()       ← injecte identité contextuelle
    │
    ▼
IA Principale génère réponse
    │
    ├── Regex magic_phrase_pattern → CognitiveMirror si introspection détectée
    ├── WebNavigator.detect_and_search()             ← si phrase recherche
    ├── Text2Image.detect_and_generate()             ← si phrase image
    ├── FileWriter.process_response()                ← si demande fichier .md
    │
    ▼
Archiviste enrichit la mémoire (async)
    │
    ├── save_memory() → SQLite + FAISS
    ├── JournalDeBord.create_entry()                 ← résumé conversation
    ├── CorrectionLearner.analyze()                  ← apprend reformulations
    └── CuriosityEngine.detect()                     ← détecte curiosités pour rêves futurs
```
