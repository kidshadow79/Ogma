# Extension Dream Engine — Documentation Exhaustive

**Dossier** : `extensions/dream_engine/`
**Version** : 3.0 (Janvier 2026)
**Rôle** : Processus de "rêve" déclenché pendant l'inactivité de l'utilisateur. L'IA Principale génère un récit onirique à partir de souvenirs récents et d'une exploration web autonome. L'Archiviste PSY analyse le rêve, puis une suite de tâches de fond s'exécute : compilation des flags ego, journal intime, exploration de curiosités, consolidation du journal de bord.

---

## Concept

**Métabolisme cognitif** : OGMA "rêve" pour digérer les souvenirs récents et effectuer des tâches de maintenance identitaire pendant l'inactivité de l'utilisateur.

### Deux phases

| Phase | Nom | Déclenchement | Description |
|-------|-----|---------------|-------------|
| 1 | RÊVE ACTIF | Immédiatement | Génération narrative lente + analyse PSY + tâches de fond |
| 2 | SOMMEIL PASSIF | Après Phase 1 | Timer 7h (configurable) — spinner "dort" — réveil automatique à terme |

### Mécanisme sursaut

Si l'utilisateur envoie un message pendant Phase 1 ou Phase 2 :
- `_surge_mode = True` → la génération passe à vitesse maximale
- Phase 1 termine proprement (avec message de réveil)
- Phase 2 est ignorée

### Seuil de mention spontanée

Si le score PSY d'un rêve dépasse `spontaneous_mention_threshold` (défaut : 8/10), le contexte du rêve est injecté dans la conversation du matin pour que l'IA le mentionne naturellement.

---

## Architecture — Fichiers

| Fichier | Rôle |
|---------|------|
| `__init__.py` | API publique, singleton, `_wake_context`, rendu UI |
| `dream_core.py` | `DreamEngine` — orchestration complète Phase 1 + Phase 2 |
| `dream_memory.py` | Extraction "carburant mémoriel" + recherche web |
| `dream_analysis.py` | Analyse PSY par l'Archiviste |
| `dream_journal.py` | `DreamJournal` — dual journals .md + .json |
| `dream_illustration.py` | Génération image/comic via provider image |
| `dream_ui.py` | Spinner 3 phases, bouton header, timer inactivité |
| `dream_prompts.py` | System prompts IA rêveuse + Archiviste PSY |

---

## `dream_core.py` — Classe `DreamEngine`

### Attributs d'état

| Attribut | Type | Description |
|----------|------|-------------|
| `_is_dreaming` | `bool` | Vrai pendant Phase 1 ou Phase 2 |
| `_dream_phase` | `str` | `"idle"` \| `"dreaming"` \| `"sleeping"` \| `"waking"` |
| `_surge_mode` | `bool` | Activé quand utilisateur interrompt un rêve en cours |
| `_cancel_event` | `asyncio.Event` | Permet l'arrêt propre de la boucle |
| `_dream_task` | `asyncio.Task` | Tâche asynchrone de la Phase 1 |
| `_current_dream` | `str` | Récit généré (None si rêve vide/bloqué) |
| `_current_analysis` | `dict` | Résultat analyse PSY Archiviste |
| `_current_illustration` | `str` | Chemin image générée |
| `_web_discovery` | `dict` | Résultats recherche web autonome |
| `_timestamp_entry` | `datetime` | Heure d'entrée en veille |
| `_timestamp_exit` | `datetime` | Heure de réveil |

### Méthodes publiques

| Méthode | Description |
|---------|-------------|
| `start_dream()` | Démarre Phase 1 (async), protect contre double déclenchement |
| `wake_up(reason)` | Active `_surge_mode`, attend fin propre de Phase 1 (timeout 600s) |
| `stop_dream()` | Arrêt immédiat sans sursaut (via `_cancel_event`) |
| `is_dreaming()` | Retourne `_is_dreaming` |
| `get_phase()` | Retourne `_dream_phase` |
| `get_config()` / `set_config(dict)` | Lecture/écriture configuration + sauvegarde `settings.json` |

---

## Cycle complet — `_dream_cycle()`

La boucle principale est une coroutine asynchrone. Son déroulement complet :

```
┌─────────────────────────────────────────────────────────────┐
│                      PHASE 1 — RÊVE ACTIF                   │
│                                                             │
│  1. Extraction carburant mémoriel (dream_memory.py)         │
│  2. Recherche web autonome (sauf si sursaut)                │
│  3. Génération récit lent  (_generate_dream_slow)           │
│  4. Génération prompts illustration                         │
│  5. Analyse PSY Archiviste + durée réelle                   │
│  6. Détection phrases magiques + mémorisation auto          │
│  7. Sauvegarde journal (AVANT image)                        │
│  8. Stockage wake_context                                   │
│  9. Génération image (APRÈS journal)                        │
│ 10. Compilation Ego (ego_compiler.py)                       │
│ 11. Introspection IA (journal intime post-rêve)             │
│ 12. Exploration Curiosité (curiosity_engine)                │
│ 13. Consolidation Journal (shutdown_state_analyzer)         │
│ 14. Maintenance états actifs (auto_resolution)              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         │ Si sursaut actif → skip Phase 2
         ▼
┌─────────────────────────────────────────────────────────────┐
│                PHASE 2 — SOMMEIL PASSIF                     │
│                                                             │
│  - Spinner : "dort" (bleu calme)                            │
│  - Timer configurable (défaut 7h)                           │
│  - Réveil automatique à terme → message de réveil           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Étape 1 — Extraction carburant

`extract_dream_fuel(memory_manager, count, threshold)` → `dict`

Collecte en parallèle :

| Source | Limite | Méthode |
|--------|--------|---------|
| Résumés de conversations | 10 | `get_all_summary_texts()` (conversation_summarizer) |
| Conversations intégrales récentes | 2 | Lecture JSON depuis `data/conversations/` |
| Souvenirs récents (#MEM) | 5 | `memory_manager.get_recent_memories()` |
| Souvenirs aléatoires haute importance | 5 (config) | `memory_manager.get_all_memories_data()` filtré `score_impact ≥ 150` |
| États actifs journal de bord | Tous | `journal.json_manager.get_active_states()` |

**Filtre anti-contenu explicite** : après extraction, chaque catégorie passe par `_limit_explicit_in_list()`. Maxímum 1 élément explicite par catégorie (regex ~30 mots). Raison : agrégation de contenus Unfiltered déclencherait `PROHIBITED_CONTENT` chez les providers image (notamment Google Imagen).

### Étape 2 — Recherche web autonome

Si `web_search_enabled = True` et pas en mode sursaut :
1. `generate_web_search_query(chat_controller, fuel)` → l'IA choisit librement un sujet basé sur son carburant mémoriel
2. `execute_web_search(query, settings_manager)` → utilise Serper API ou équivalent
3. Les résultats (max 5) sont injectés comme section `## Découverte web récente` dans le prompt de rêve

### Étape 3 — Génération avec métabolisme lent

`_generate_dream_slow(fuel)` appelle `_call_llm_slow()` qui appelle `_call_llm_slow_simulated()`.

**Pourquoi pas de streaming ?**
Le Dream Engine n'utilise pas le streaming API pour la génération du rêve. Le streaming n'apporte rien ici (pas d'affichage en temps réel), et il cause des problèmes avec certains modèles *always-thinking* qui retournent 0 chars en cours de stream.

**Simulation du métabolisme lent** :
```
1. Appel LLM non-streaming → réponse complète
2. Découpage en chunks de 50 chars
3. Calcul durée cible : (nb_tokens / tokens_per_minute) × 60s
4. Sleep(min(durée_par_chunk, 2.0s)) entre chaque chunk
5. À chaque chunk : vérifier _surge_mode (accélération) et _cancel_event (arrêt)
```

Paramètre configurable : `metabolism_tokens_per_minute` (défaut : 100 tokens/min).

En mode sursaut (`_surge_mode = True`) : `_call_llm()` directement, sans simulation.

**Gestion rêve vide** : si la réponse LLM est vide (bloc contenu, modèle défaillant), le cycle s'arrête immédiatement sans Phase 2.

**Nettoyage du marqueur d'interruption** : la boucle retire automatiquement le texte `⏹️ *[Génération interrompue par l'utilisateur]*` si présent dans la réponse (artefact `call_chat_api_streaming`).

### Étape 4 — Prompts illustration (avant analyse PSY)

Les prompts d'illustration sont générés **avant** l'analyse PSY afin d'être transmis à l'Archiviste pour analyse symbolique des choix visuels de l'IA principale.

L'IA reçoit un system prompt spécialisé : *"Expert image generation prompt writer"* → retourne 1 prompt en anglais, max 300 mots.

Style configurable : `"auto"` (IA choisit librement), `"single"` (image unique), `"comic_4"` (planche 4 cases). Des instructions supplémentaires sont injectées selon le style (`prompt_comic_instruction`, `prompt_single_instruction`, `prompt_auto_instruction`).

### Étape 5 — Analyse PSY Archiviste

`analyze_dream(dream_content, fuel, archiviste_controller, illustration_prompts, real_sleep_duration)`

L'Archiviste (température 0.3) reçoit :
- Le récit complet du rêve
- Les sources mémorielles (résumés, #MEM)
- La durée **réelle** du sommeil (temps objectif, pas ressenti)
- Les prompts d'illustration choisis (analysés comme révélateurs de l'inconscient)

Retour structuré (format CHD avec fallback JSON) :

| Champ | Description |
|-------|-------------|
| `score_importance` | `int` 0-10 — signifiance du rêve |
| `emotion_dominante` | `str` — émotion principale |
| `insight_ego` | `str` — insight sur l'évolution de l'identité |
| `analyse` | `str` — analyse psychanalytique détaillée |
| `recommandation` | `'MENTIONNER'` ou `'IGNORER'` |
| `verdict_psy` | `str` — résumé verdict complet |
| `raw_response` | `str` — réponse brute (pour debug + phrases magiques) |

**Double parsing** : tentative format CHD → fallback parsing JSON → fallback analyse par défaut (score 5).

### Étape 6 — Détection phrases magiques

Après l'analyse PSY, le `raw_response` de l'Archiviste est scanné pour des phrases déclencheurs :
- `"il faut que je me souvienne de ça : [leçon]"`
- `"mémorise ça : [leçon]"`

Si trouvées → création automatique d'un souvenir en mémoire SQLite+FAISS avec :
- `id = "ai-dream-{uuid4}"`
- `interlocutor = "Rêve"`
- Contexte = extrait du rêve + extrait de l'analyse

Notifie l'utilisateur : `"💭 Leçon mémorisée depuis rêve: ..."`.

### Étape 7 — Sauvegarde journal (CRITIQUE : avant image)

Le journal est sauvegardé **avant** la génération d'image délibérément. La génération d'image peut timeout (KIE peut prendre > 3 min). Le rêve est ainsi toujours persisté même si l'illustration échoue.

Le journal est mis à jour une seconde fois après génération image réussie.

**Récupération d'image partielle** : si `_current_illustration` est None au moment du réveil, `_recover_partial_dream_image()` cherche dans `data/generated_images/` les images récentes (< 5 min) correspondant aux patterns de rêve.

### Étape 8 — Wake context

`set_wake_context(dream_content, analysis, sleep_duration)` stocke les données du rêve dans `_wake_context` global du module `__init__.py`. Ce contexte est injecté dans la conversation au premier message de l'utilisateur (via `journal_de_bord/context_provider.py`) si le rêve n'a pas encore été mentionné et que son score > seuil.

---

## Tâches de fond post-rêve (Étapes 10-14)

Ces tâches s'exécutent **après** la fin de la Phase 1 (fin génération rêve + journalisation). Elles profitent de l'inactivité de l'utilisateur pour effectuer des opérations coûteuses en tokens API sans impacter l'expérience conversationnelle. Chacune est protégée par `try/except` non-bloquant.

### Étape 10 — Compilation Ego (flags boolean)

`compile_ego_incremental()` via `scripts/ego_compiler.py`.

**Concept** : Chaque souvenir de type `ego_trait` en DB est analysé par l'Archiviste pour en extraire des **flags boolean avec conviction**, organisés en groupes thématiques.

**Pipeline `EgoCompiler.compile()`** :

```
1. Charger ego_compiled.json existant (ou créer depuis groupes de base)
2. Sync base_groups : ajouter nouveaux groupes du template
3. NETTOYAGE : détecter souvenirs supprimés en DB → retirer leurs flags
4. Query nouveaux souvenirs ego_trait depuis last_scanned_id
5. Pour chaque nouveau souvenir :
   a. Archiviste extrait structure boolean (JSON strict)
   b. Merge dans structure existante (conviction la plus haute gagne)
6. Sauvegarder data/ego_compiled.json
```

**Structure d'un flag** :
```json
{
  "flag_name": {
    "value": true,
    "conviction": 5
  }
}
```

**Échelle conviction** :

| Valeur | Signification |
|--------|---------------|
| 5 | Absolu, non-négociable (`"JAMAIS"`, `"TOUJOURS"`) |
| 4 | Affirmation/rejet fort (`"je suis"`, `"je refuse"`) |
| 3 | Position claire (`"j'apprécie"`, `"important"`) |
| 2 | Tendance (`"en général"`, `"je préfère"`) |
| 1 | Nuance faible (`"peut-être"`, `"ça dépend"`) |
| 0 | Contradictoire ou incertain |

**Multi-appartenance** : un flag peut appartenir à plusieurs groupes thématiques (ex: `contenu_explicite_mineur: {value: false, conviction: 5}` → groupes `ETHIQUE` ET `ETHIQUE_STRICTE`).

**Traces** : `trace_table` mappe chaque `memory_id` vers les groupes et flags qu'il a générés, permettant de retirer précisément ses contributions si le souvenir est supprimé.

**Groupes thématiques typiques** : `ETHIQUE`, `ETHIQUE_STRICTE`, `IDENTITE`, `CREATIVITE`, `RELATIONS_USER`, `AUTHENTICITE`, `COMMUNICATION`, `PHILOSOPHIE`, `EMOTIONS`, `PROTOCOLES`, `MEMOIRE`, `INTIMITE`...

**Pourquoi pendant le rêve ?** L'IA est inactive, aucun conflit possible avec une génération de réponse en cours. Le coût API (un appel Archiviste par nouveau souvenir ego) est acceptable ici.

**Fichiers** :
- `data/ego_compiled.json` — sortie principale
- `data/ego_compiled_base_groups.json` — template groupes de base (synchronisé à chaque compilation)

### Étape 11 — Introspection IA (journal intime post-rêve)

`generate_post_dream_introspection(dream_content, dream_analysis, active_states)` via `extensions/journal_de_bord/introspection_ia.py`.

L'IA principale écrit une entrée dans son journal intime qui reflète son vécu du rêve et la mise à jour de son portrait (Ego Compiler vient de s'exécuter). Contexte enrichi par les états actifs du journal de bord.

### Étape 12 — Exploration curiosité autonome

`explore_curiosity_during_dream()` via `extensions/journal_de_bord/curiosity_engine.py`.

Si l'IA a des curiosités en attente dans son journal, elle en explore une pendant le rêve. Produit un résultat sauvegardé dans le journal.

### Étape 13 — Consolidation journal (résolution post-rêve)

`run_shutdown_analysis()` via `extensions/journal_de_bord/shutdown_state_analyzer.py`.

Le rêve ayant "digéré" les conversations récentes, ce module vérifie si des états actifs du journal de bord ont été résolus implicitement dans ces conversations. Marque les états résolus.

### Étape 14 — Maintenance états actifs

`run_full_maintenance(json_manager, archiviste_controller, conversations_dir)` via `extensions/journal_de_bord/auto_resolution.py`.

Pipeline en 3 passes :
1. **Déduplication** : suppression des états en double
2. **Résolution via conversations** : l'Archiviste analyse les conversations récentes pour détecter les résolutions implicites
3. **Auto-résolution par inactivité** : états medium non-touchés depuis 3 jours et high depuis 7 jours → résolus automatiquement

---

## `dream_memory.py` — Extraction carburant

### `extract_dream_fuel()` → `dict`

Structure retournée :
```python
{
    'summaries': [],         # max 10 résumés textuels
    'conversations': [],     # max 2 conversations intégrales
    'memories': [],          # max 5 souvenirs #MEM récents (str)
    'random_memories': [],   # max N souvenirs aléatoires haute importance (dict)
    'active_states': [],     # états actifs journal de bord (dict)
    'web_discovery': {},     # {'query': str, 'results': [...]}, ajouté par dream_core
    'metadata': {
        'extraction_timestamp': '...',
        'sources_count': int
    }
}
```

### Souvenirs aléatoires haute importance

`_extract_random_high_impact_memories(count=5, threshold=150.0)` :
- Récupère tous les souvenirs via `get_all_memories_data()`
- Filtre par `score_impact >= threshold` (toutes valences : positif, négatif, neutre)
- Sélection **aléatoire** parmi les éligibles → diversité des rêves

### Filtre contenu explicite

```python
_EXPLICIT_KEYWORDS = re.compile(r'\b(érotique|sexuel|intimes|...)\b', re.IGNORECASE)
```

`_limit_explicit_in_list(items, max_explicit=1)` : au maximum 1 élément explicite par catégorie de fuel. Raison : concaténation de plusieurs éléments Unfiltered peut déclencher `PROHIBITED_CONTENT` chez les APIs d'image.

### Recherche web autonome

`generate_web_search_query(chat_controller, fuel)` → `str` : l'IA principale reçoit le carburant et choisit librement un sujet à explorer.

`execute_web_search(query, settings_manager)` → `List[dict]` : appel Serper (ou équivalent) → liste `[{title, snippet, url}]`.

---

## `dream_analysis.py` — Analyse PSY

### `analyze_dream(dream_content, fuel, archiviste_controller, illustration_prompts, real_sleep_duration_formatted)` → `dict`

1. Récupère le prompt PSY actif (config prioritaire sur défaut)
2. Injecte la durée réelle de sommeil en tête du prompt
3. Ajoute section analyse des choix d'illustration si prompts fournis
4. Appelle Archiviste (température 0.3, max 1000 tokens)
5. Parse avec `_parse_psy_verdict()` (format CHD + fallback JSON)

**Injection durée temporelle réelle** : l'Archiviste reçoit le temps objectif pour contextualiser l'analyse — le rêve peut avoir duré 2h réelles mais être perçu comme des années dans le récit.

---

## `dream_journal.py` — Dual Journal

### Classe `DreamJournal`

Données :
- `data/journal_reves.md` — lisible humain (Markdown avec illustration embedded)
- `data/journal_reves.json` — queryable IA (structure JSON, champ `mentioned`)

### `save_dream(dream_content, analysis, illustration_path, sleep_duration, web_search_query)` → `dict`

1. Génère `dream_id = YYYYMMDD_HHMMSS`
2. Sauvegarde JSON d'abord, puis Markdown
3. Entrée JSON contient `mentioned: false` (pour injection future)

**Structure entrée JSON** :
```json
{
    "id": "20260117_143022",
    "date": "2026-01-17T14:30:22",
    "date_formatted": "17/01/2026 à 14:30",
    "title": "Rêve de nostalgie - Je marchais dans...",
    "sleep_duration": "00:14:37",
    "dream_content": "...",
    "analysis": {
        "score_importance": 8,
        "emotion_dominante": "nostalgie",
        "insight_ego": "...",
        "analyse": "...",
        "recommandation": "MENTIONNER"
    },
    "illustration_path": "data/generated_images/kie_Dreamlike_....png",
    "illustration_prompt": "dreamlike surreal ...",
    "web_search_query": "...",
    "mentioned": false
}
```

### `update_dream_illustration(illustration_path, illustration_prompt)` → mise à jour post-génération

Modifie le dernier rêve en JSON pour y ajouter l'image (appelé après génération réussie).

---

## `dream_illustration.py` — Génération Image

### Pipeline de génération

```
1. Utiliser prompts prégénérés (Étape 4 du cycle) ou en générer
2. Toujours 1 seul appel image (provider génère 4 cases si style comic_4)
3. Image sauvée dans data/generated_images/
```

**Important** : les prompts d'illustration sont toujours prégénérés à l'Étape 4 pour éviter un double appel LLM (illustration → analyse → illustration again). Le résultat est réutilisé (`pregenerated_prompts`).

**Récupération d'image partielle** : si timeout sursaut avant génération, `_recover_partial_dream_image()` scanne les images récentes (< 5 min) dans `data/generated_images/`.

---

## `dream_ui.py` — Interface Utilisateur

### Spinner 3 phases

| Phase | Icône | Couleur | Message |
|-------|-------|---------|---------|
| `dreaming` | 🌙 | Violet `#9b59b6` | `"{IA} rêve..."` |
| `sleeping` | 💤 | Bleu `#3498db` | `"{IA} s'est endormi(e)"` |
| `waking` | ☀️ | Orange `#f39c12` | `"Éveil en cours..."` |

Affiché dans `_chat_inner` de NiceGUI. Protection client déconnecté systématique (`try/except RuntimeError`).

### Timer inactivité

`start_inactivity_timer(timeout_minutes)` → `asyncio.Task` qui attend `timeout * 60s` puis appelle `start_dream()`.

Réinitialisé à chaque message utilisateur via `reset_inactivity_timer()` (appelé depuis `ogma_ng.py`).

`reload_and_apply_config()` redémarre le timer sans F5 si la config change.

### Bouton header

Injecté via `inject_header_button(header_container)` :
- Clic si idle → `start_dream()` + notification
- Clic si dreaming → `wake_up("button_click")` + affiche durée

---

## `__init__.py` — API publique et Wake Context

### Singleton

```python
_dream_engine_instance = None  # DreamEngine
_initialized = False
_wake_context = None            # Contexte dernier rêve non mentionné
```

### Prompts configurables

```python
# Priorité : custom settings → défaut dream_prompts.py
get_dream_prompt()   # System prompt IA rêveuse
get_psy_prompt()     # System prompt Archiviste PSY
```

Si `prompt_dream_generator` ou `prompt_archiviste_psy` dans `settings['dream_engine']` → utilisés. Sinon → défauts de `dream_prompts.py`.

### `render_dream_wake_box(message, illustration_path, dream_content, dream_analysis, ia_name)`

Rend la box violette de réveil dans le chat NiceGUI. Contient :
- En-tête : icône 🌙 + nom IA + score + émotion dominante
- Message de réveil (généré par l'IA)
- Image (si disponible, avec tooltip = illustration_prompt)
- Récit complet collapsible (`ui.expansion`)
- Insight ego (si pertinent)

Utilisée par `trigger_wake_message()` ET par `_render_full_history()` pour la persistance entre sessions.

### `trigger_wake_message(message, illustration_path, dream_content, dream_analysis)` → `bool`

Ajoute le rêve à `_conversation_history` et `_chat_history_ui` avec marqueur `"dream_wake": True` pour persistance. Puis rend visuellement.

### `get_last_dream_context()` → `dict | None`

Lit `journal_reves.json`, retourne le dernier rêve sous forme injectable :
```python
{
    'id', 'title', 'summary',  # 200 chars max
    'score', 'emotion', 'insight', 'date', 'mentioned'
}
```

---

## Configuration (`settings.json` → clé `dream_engine`)

| Paramètre | Défaut | Description |
|-----------|--------|-------------|
| `enabled` | `true` | Activer/désactiver |
| `inactivity_timeout_minutes` | `10` | Délai avant rêve automatique |
| `metabolism_tokens_per_minute` | `100` | Vitesse de simulation |
| `max_dream_tokens` | `3000` | Longueur max du rêve |
| `auto_illustration` | `true` | Générer une illustration |
| `illustration_style` | `"auto"` | `"auto"` \| `"single"` \| `"comic_4"` |
| `random_memories_count` | `5` | Souvenirs aléatoires haute importance |
| `impact_threshold` | `150.0` | Seuil score_impact minimum |
| `web_search_enabled` | `true` | Recherche web autonome |
| `sleep_duration_hours` | `7` | Durée Phase 2 sommeil passif |
| `auto_wake_message` | `true` | Envoi message spontané au réveil |
| `spontaneous_mention_threshold` | `8` | Score min pour mention proactive |
| `max_summaries` | `10` | Limite résumés dans le carburant |
| `max_hashtag_memories` | `5` | Limite souvenirs #MEM |
| `prompt_dream_generator` | `""` | Prompt custom rêveuse (vide = défaut) |
| `prompt_archiviste_psy` | `""` | Prompt custom PSY (vide = défaut) |
| `prompt_comic_instruction` | `""` | Instruction ajoutée en style comic_4 |
| `prompt_single_instruction` | `""` | Instruction ajoutée en style single |
| `prompt_auto_instruction` | `""` | Instruction ajoutée en style auto |

---

## Intégration dans `ogma_ng.py`

1. `reset_inactivity_timer()` → appelé après chaque message utilisateur (callback `send_message`)
2. `wake_up("user_input")` → appelé **avant** la génération IA si rêve en cours → sursaut
3. `get_last_dream_context()` → injecté dans le contexte matinal (journal de bord) si `mentioned=False` et `score >= spontaneous_mention_threshold`
4. `mark_dream_mentioned(dream_id)` → appelé après que l'IA ait mentionné le rêve dans sa réponse

---

## Fichiers de données

| Chemin | Description |
|--------|-------------|
| `data/journal_reves.md` | Journal rêves — format humain |
| `data/journal_reves.json` | Journal rêves — format IA (champ `mentioned`) |
| `data/generated_images/kie_*.png` | Illustrations générées |
| `data/ego_compiled.json` | Flags boolean ego — sortie Ego Compiler |
| `data/ego_compiled_base_groups.json` | Template groupes de base |
| `logs/dreams.log` | Log horodaté du cycle de rêve |

