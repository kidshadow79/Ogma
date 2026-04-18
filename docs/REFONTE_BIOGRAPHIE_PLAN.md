# REFONTE SYSTÈME BIOGRAPHIE — Plan de travail

*Démarré le 17 avril 2026 — Terminé le 19 avril 2026*

---

## Statut global : ✅ TERMINÉ

---

## 1. Diagnostic de l'existant (17 avril 2026)

### Architecture initiale (3 volumes — abandonnée)

| Fichier | Généré par | Carburant | Injecté en contexte |
|---|---|---|---|
| `volume1_memories.json` | Bouton "Traiter souvenirs" | FAISS index (filtre par nom) | ✅ Oui — Circuit 1 (supprimé) |
| `volume2_structured.json` | Bouton "Phase 1: JSON IA" | Volume 1 + convs >30KB + résumés | ❌ Non |
| `volume2_journal.md` | Bouton "Phase 2: MD IA" | Volume 2 JSON intégral | ❌ Non |

### Problèmes identifiés

- **Volume 1 pauvre** : filtre FAISS par présence du nom → restrictif, souvent vide
- **Hallucination structurée** : l'IA générait des portraits psychiatriques (MBTI, QI…) à partir de 3 seeds système
- **Seuil 30KB** : les conversations <30KB ignorées → source vide en pratique
- **Circuit 1 fragile** : injection via `magic_phrases.py` → `volume1_memories.json` → filtre FAISS par prénom dans le texte. Approche manuelle, coûteuse, non scalable

---

## 2. Architecture finale implémentée

### Vue d'ensemble

```
Signaux biographiques
(SQLite user_tag + Cognitive Cache + Résumés)
            ↓
   signal_collector.py  [collect_signals()]
            ↓
   volume2_structured.json  (facts[])
            ↓  [Bouton Phase 1 : JSON IA]
   bio_compiler.py  + IA analytique  [compile_bio_incremental()]
            ↓  [Bouton Bio Compiler]
   bio_compiled.json  (groupes thématiques)
            ↓  [automatique à chaque message]
   bio_activation.py  [activate_bio_groups()]
   → Injection 0-3 groupes dans le prompt de l'IA principale


   bio_compiled.json  →  [Bouton Journal Bio]
   volume2_journal.md  (lecture humaine uniquement)
```

---

### 2.1 — Collecte des signaux (`signal_collector.py`)

Le collecteur scanne trois sources, filtrées par `user_tag` et `bio_processed = 0` :

| Source | Flag posé par | Colonne/Champ |
|---|---|---|
| SQLite `memories` | L'Archiviste (JSON enrichissement) | `user_tag TEXT`, `bio_processed INTEGER DEFAULT 0` |
| Cognitive Cache (`data/cognitive_cache/*.json`) | Code (`add_entry` + `_current_user_name`) | `user_tag`, `bio_processed` |
| Résumés conversations (`data/conversations/*.json`) | Archiviste ou code | `user_tag`, `bio_processed` |

Retourne une liste de signaux normalisés `{source, source_id, date, content, ...}`.  
Après traitement réussi : `mark_signals_processed()` marque `bio_processed=true/1`.

**Bootstrap** : si `signals = 0` ET que `volume2_structured.json` n'a pas encore de faits, la Phase 1 bascule automatiquement sur `volume1_memories.json` comme source (souvenirs SEED exclus). Permet de démarrer sans attendre l'alimentation SQLite.

---

### 2.2 — Phase 1 : JSON IA (`biography_manager.py`)

**Bouton** : 🧠 Phase 1 : JSON IA  
**Entrée** : signaux non traités (ou bootstrap Volume 1)  
**Sortie** : `volume2_structured.json` → liste de `facts[]`  
**Mode incrémental** : lit les faits existants + nouveaux signaux → l'IA enrichit sans dupliquer  
**Anti-hallucination** : prompt interdit toute inférence hors signaux fournis  

---

### 2.3 — Bio Compiler (`scripts/bio_compiler.py`)

**Bouton** : ⚡ Bio Compiler  
**Entrée** : `volume2_structured.json` (facts[])  
**Sortie** : `bio_compiled.json` (groupes thématiques)  
**Fonctionnement** : l'IA analytique classe chaque fait dans 1-3 groupes (ANIMAUX, GOÛTS, PROJETS…). Chaque groupe stocke ses faits + description + keywords pour matching sémantique.  
**Mode incrémental** : seuls les faits nouveaux (pas encore dans bio_compiled) sont analysés.  

---

### 2.4 — Injection en conversation (`bio_activation.py`)

**Déclenchement** : automatique à chaque message  
**Fonctionnement** :

1. Chargement du catalogue léger de `bio_compiled.json` (nom + description + keywords, sans les faits complets)
2. L'Archiviste reçoit le message utilisateur + le catalogue → sélectionne 0-3 groupes pertinents
3. Les faits des groupes sélectionnés sont injectés dans le system prompt de l'IA principale

**Règle premier message de session** : tous les groupes injectés d'un coup (portrait de départ), sans appel Archiviste.  
**Budget tokens** : ~30-200 tokens selon le nombre de faits injectés.  

---

### 2.5 — Journal narratif (`biography_manager.py`)

**Boutons** : 📓 Journal Bio / 🗑️ Reset Journal  
**Sortie** : `volume2_journal.md` — lecture humaine uniquement, jamais injecté en conversation  

**Mode enrichissement** (défaut) : lit `volume2_journal.md` existant + faits compilés → l'IA enrichit/corrige sans repartir de zéro  
**Mode reset** : supprime le journal existant + régénère depuis tous les faits compilés  

**Instruction personnalisable** : modifiable depuis l'interface (section "Instruction du journal biographique"). Sauvegardée dans `data/biographies/journal_instruction.txt`. Bouton "↩️ Rétablir défaut" disponible.  

**Instruction par défaut** : 10 sections fixes (Portrait général, Psyché & vie émotionnelle, Vie intellectuelle, Projets & créations, Vie quotidienne, Relations, Histoire personnelle, Valeurs, Physique, Goûts). Règles anti-hallucination strictes.

---

## 3. Circuit 1 — suppression complète

### Qu'était le Circuit 1

Ancien système d'injection via `magic_phrases.py` → filtre FAISS par présence du prénom dans le texte → injection dans `ai_content`.

### Ce qui a été supprimé de `ogma_ng.py`

| Zone | Ce qui était là |
|---|---|
| ~L2286 | Détection phrases magiques utilisateur → `biography_context_early` |
| ~L2621 | Scan post-réponse IA dans le flux Introspection-Detect |
| ~L2966 | Préparation + injection `biography_context` dans `ai_content` |
| ~L5180 | `BIOGRAPHY AUTO-DÉCLENCHÉE` — l'IA pouvait dire "je veux consulter la bio de …" |
| ~L5447 | Scan phrases magiques dans le flux Introspection-Magic |

**Circuit 2 préservé** : `activate_bio_groups` (L~3277) — intact.

---

## 4. Fichiers créés ou modifiés

| Fichier | Statut | Description |
|---|---|---|
| `extensions/biographie_profil/signal_collector.py` | ✅ Créé | Scanner 3 sources, normalisation, marquage |
| `scripts/bio_compiler.py` | ✅ Modifié | Retrait appel auto `save_facts_journal()` |
| `modules/logic/bio_activation.py` | ✅ Existant | Injection Archiviste 0-3 groupes — intact |
| `extensions/biographie_profil/biography_manager.py` | ✅ Refactorisé | 2565 → ~1500 lignes, `generate_narrative_journal_ia()`, `_load_volume1_as_signals()`, bootstrap V1, `JOURNAL_INSTRUCTION_DEFAULT`, méthodes statiques `get/save/reset_journal_instruction()` |
| `extensions/biographie_profil/ui_components.py` | ✅ Modifié | Boutons 📓 Journal Bio + 🗑️ Reset Journal, section instruction journal éditable, tooltips corrigés, section "À propos" réécrite |
| `ogma_ng.py` | ✅ Modifié | Circuit 1 entièrement supprimé (5 zones) |

---

## 5. Flux utilisateur — utilisation normale

### Première fois (bootstrap)

```
1. Saisir le nom dans le champ
2. [Traiter souvenirs]  →  volume1_memories.json  (souvenirs FAISS existants)
3. [Phase 1 : JSON IA]  →  volume2_structured.json  (bootstrap V1 si SQLite vide)
4. [Bio Compiler]       →  bio_compiled.json  (groupes thématiques)
5. [Journal Bio]        →  volume2_journal.md  (lecture humaine)
```

### Mise à jour régulière (après nouvelles conversations)

```
1. [Phase 1 : JSON IA]  →  nouveaux faits ajoutés incrémentalement
2. [Bio Compiler]       →  nouveaux groupes/faits intégrés
3. [Journal Bio]        →  journal enrichi (mode enrichissement)
```

### Si le journal est désynchronisé ou si l'instruction a changé

```
1. Modifier l'instruction → [Sauvegarder instruction]
2. [Reset Journal]      →  repart de zéro depuis bio_compiled.json
```

---

## 6. Tests validés (19 avril 2026)

- ✅ Pipeline complet Yohan : 3 souvenirs bootstrap → 3 faits → 2 groupes (ANIMAUX, GOÛTS) → journal 728 chars
- ✅ Injection en conversation : "elle était malade" → groupe ANIMAUX sélectionné → IA mentionne "Willow" sans que le nom ait été répété
- ✅ Archiviste reasoning : `"Le message discute de la santé du chat de l'utilisateur, qui correspond aux keywords 'chat' et 'animal de compagnie' du groupe ANIMAUX"`
- ✅ Circuit 1 : zéro trace dans `ogma_ng.py` (vérifié par grep)
- ✅ Syntaxe : tous les fichiers modifiés validés sans erreur

---

*Document finalisé le 19 avril 2026*

---

## 1. Diagnostic de l'existant

### Architecture actuelle (3 volumes)

| Fichier | Généré par | Carburant | Injecté en contexte |
|---|---|---|---|
| `volume1_memories.json` | Bouton "Traiter souvenirs" | FAISS index (filtre par nom) | ✅ Oui — via Archiviste |
| `volume2_structured.json` | Bouton "Phase 1: JSON IA" | Volume 1 + convs >30KB + résumés | ❌ Non |
| `volume2_journal.md` | Bouton "Phase 2: MD IA" | Volume 2 JSON intégral | ❌ Non |

### Problèmes identifiés

#### A. Volume 1 trop pauvre
- Filtre les souvenirs FAISS qui **contiennent le nom** → très restrictif
- Actuellement : 3 seeds système, zéro souvenir personnel réel
- Sera toujours pauvre tant que l'utilisateur n'alimente pas FAISS via phrases magiques

#### B. Volume 2 JSON — hallucination structurée
- GROK a produit un portrait psychiatrique élaboré (MBTI, QI 140, micro-expressions...)
- Basé sur **3 seeds OGMA** → fabrication convaincante mais non ancrée dans du réel
- Le JSON semble "correct" car le LLM extrapole avec cohérence narrative
- Risque : l'IA se baserait sur des profils fabriqués comme si c'était de la vérité

#### C. Volume 2 MD — prose sur sable
- Belle narration psychiatrique mais construite sur le JSON halluciné
- Double amplification de l'hallucination

#### D. Seuil 30KB conversations
- Les 20 fichiers de conversations actuels font tous <30KB → source vide
- Phase 1 tourne donc sans carburant conversationnel réel

#### E. Consommation tokens
- Volume 1 intégral + conversations + résumés → prompt Phase 1 potentiellement énorme
- Pas de plafond sur le nombre de conversations >30KB injectées
- Format MD (Phase 2) redondant avec JSON pour l'injection IA

---

## 2. Philosophie de la refonte

### Ce qu'on veut vraiment
L'IA doit **connaître l'utilisateur** de façon fiable, sans halluciner, avec un coût tokens raisonnable.

### Principes directeurs
1. **Aucune inférence sans source** — si ce n'est pas dans les données, ne pas l'inventer
2. **Faits > profil psychologique** — ce que l'utilisateur a dit/fait, pas ce qu'on suppose de sa psyché
3. **Économie de tokens** — injecter une synthèse dense, pas des documents bruts
4. **Croissance organique** — démarrer vide, s'enrichir datum par datum
5. **Transparence** — l'utilisateur sait ce que l'IA "sait" sur lui

---

## 3. Architecture cible — Collecte organique de faits

### Principe fondateur (proposé le 17/04/2026)

> Le système OGMA collecte passivement des **signaux biographiques** au fil des interactions, les marque avec un flag user, puis les traite en batch lors des moments creux (rêve, fermeture, Phase 1 manuelle).

**Règle absolue : aucune inférence sans source explicite.** Zéro psychologie, zéro MBTI sans que l'utilisateur l'ait dit lui-même.

---

### 3.1 — Les sources de signaux (avec leur flag)

#### Qui pose le prénom tampon ?

Trois sources, trois mécanismes distincts :

| Source | Qui décide du prénom tampon ? | Moment |
|---|---|---|
| **Mémoire SQLite** | **L'Archiviste**, dans son JSON de réponse | Lors de l'enrichissement du souvenir |
| **Résumés de conversation** | Le **code** (via `set_user_tag`) | À l'écriture du résumé |
| **Cache cognitif** | Le **code** (via `apply_cache_operations`) | Lors du parsing des commandes CACHE |

**Pourquoi deux logiques différentes ?**
- L'Archiviste fait UN appel IA pour enrichir un souvenir. Il reçoit le texte brut + le prénom de l'utilisateur connecté → il peut évaluer si le contenu le concerne → il ajoute `"user_tag": "Yohan"` ou `"user_tag": null` dans son JSON. Zéro appel supplémentaire.
- Pour les résumés et le cache, l'Archiviste génère du texte (pas du JSON structuré), et l'entrée est écrite par le code Python ensuite → le code tampoune simplement le prénom de la session en cours.

**Règle pour l'Archiviste (mémoire uniquement) :**
L'Archiviste reçoit dans son prompt : `"Utilisateur connecté : [prénom]"`. Il évalue si le contenu du souvenir concerne cet utilisateur (faits, projets, préférences, vie personnelle). Si oui → `user_tag = "[prénom]"`. Si non (contenu technique, concept OGMA, discussion abstraite) → `user_tag = null`.

---

#### Source 1 : Cognitive Cache
**Structure actuelle** d'une entrée :
```json
{"id": "cache-abc123", "type": "observation", "content": "...", "created_at": "...", "active": true}
```
**Modification prévue** : ajouter `user_tag` et `bio_processed` :
```json
{"id": "cache-abc123", "type": "observation", "content": "...", "created_at": "...", "active": true,
 "user_tag": "Yohan",   // _current_user_name au moment de add_entry()
 "bio_processed": false // false = pas encore traité pour biographie
}
```
- **Qui pose le flag ?** : `add_entry()` dans `cache_manager.py` reçoit `user_tag` en paramètre (passé depuis ogma_ng via `_current_user_name`)

#### Source 2 : Mémoire FAISS / SQLite
**Structure actuelle** dans SQLite : `id, created_at, text_original, type, title, summary, lesson, valence, score_impact`
**Modification prévue** : ajouter colonnes :
```sql
ALTER TABLE memories ADD COLUMN user_tag TEXT DEFAULT NULL;
ALTER TABLE memories ADD COLUMN bio_processed INTEGER DEFAULT 0;
```
- **Qui pose le tag ?** : `add_memory()` dans `memory_manager.py` reçoit `_current_user_name` depuis la session active au moment de l'appel — déjà disponible en contexte d'appel

#### Source 3 : Résumés de conversation (`summaries` dans les JSON de conv)
**Structure actuelle** dans les fichiers `data/conversations/*.json` :
```json
{"summaries": [{"date": "...", "summary": "..."}]}
```
**Modification prévue** : ajouter `user_tag` et `bio_processed` par entrée de résumé :
```json
{"summaries": [{
  "date": "...",
  "summary": "Yohan a évoqué sa fatigue et son projet OGMA...",
  "user_tag": "Yohan",     // posé par l'Archiviste si le résumé parle de l'auteur
  "bio_processed": false   // pas encore consommé par Phase 1
}]}
```
- **Qui pose le tag ?** : l'Archiviste, lors de la rédaction du résumé, décide si le contenu parle de l'auteur connecté → instruction dédiée dans son prompt system (voir section 3.6)
- Si le résumé ne parle que de sujets impersonnels → `user_tag: null`, jamais taggé

---

### 3.6 — Instruction Archiviste pour le tagging biographique

L'Archiviste produit déjà un JSON structuré à chaque enrichissement de souvenir. Il suffit d'ajouter un champ `user_tag` à ce JSON — **sans appel supplémentaire, sans tokens supplémentaires**.

**Ce qui change dans le prompt de mémorisation (`instructions_defaults.json`) :**
Le schéma JSON existant reçoit un nouveau champ :
```json
"user_tag": "prénom de l'utilisateur | null"
```
Et une instruction dédiée explique la règle de décision.

**Ce qui change dans le code (`memory_manager.py`) :**
- `_call_archiviste_enrichment()` reçoit le prénom de l'utilisateur connecté en paramètre
- Il l'injecte dans le prompt : `"Utilisateur connecté : [prénom]"`
- Il lit `user_tag` dans la réponse JSON de l'Archiviste
- Ce `user_tag` est transmis à `_store_in_sqlite()`

**L'Archiviste ne tague que ce qui est factuel et observable** — jamais de psychologie, jamais d'extrapolation.

---

### 3.2 — Le traitement batch (le "collecteur")

Un module `biography_signal_collector.py` responsable de :

1. **Scanner** les entrées non traitées (`bio_processed = false/0`) dans :
   - Cognitive cache de toutes les conversations actives
   - SQLite memories avec `bio_processed = 0` et `user_tag IS NOT NULL`
   - Résumés de conversations avec `bio_processed = false` et `user_tag IS NOT NULL`
2. **Grouper** par `user_tag`
3. **Nourrir** la Phase 1 avec ces nouveaux signaux
4. **Marquer** `bio_processed = true/1` sur chaque entrée consommée

**Déclenchement** :
- Pendant un rêve (idle time) → naturel, organique
- À la fermeture d'OGMA (`stop_signal.py`)
- Manuellement via le bouton "Phase 1: JSON IA"

---

### 3.3 — Le JSON biographique cible — mise à jour incrémentale

**Principe** : la biographie ne se régénère **jamais entièrement**. Phase 1 lit le JSON existant, y ajoute les nouveaux faits collectés (`bio_processed=false`), et émet un JSON enrichi. L'historique des faits est conservé.

```
JSON existant  +  nouveaux signaux (bio_processed=false)  →  JSON enrichi
```

Première run (fichier absent) → génération from scratch depuis les signaux disponibles.  
Runs suivantes → enrichissement : seuls les nouveaux signaux sont traités par l'Archiviste.

**Basé sur des faits observés, pas sur des inférences** :
```json
{
  "user_name": "Yohan",
  "last_updated": "ISO_DATE",
  "facts": [
    {
      "date": "2026-04-17T20:00:00",
      "source_type": "cognitive_cache",
      "source_id": "cache-abc123",
      "content": "Yohan travaille sur OGMA depuis mai 2025",
      "processed": true
    },
    {
      "date": "2026-03-29",
      "source_type": "memory",
      "source_id": "MEM_xyz",
      "content": "Yohan préfère les interfaces en mode sombre",
      "processed": true
    }
  ],
  "profile_validated": {
    // Rempli manuellement ou validé par l'utilisateur
    "projets_actifs": ["OGMA"],
    "preferences": ["mode sombre"],
    "notes_libres": ""
  }
}
```

---

### 3.4 — L'injection en contexte

**Format condensé** (~200-300 tokens max) :
```
[PROFIL YOHAN — faits observés]
- Créateur d'OGMA depuis mai 2025
- Préfère les interfaces en mode sombre
- [autres faits récents...]
```
- Injecté **en permanence** à chaque message (portrait stable)
- Généré dynamiquement depuis `facts[]` au lieu d'un bloc MD statique
- Pas de MBTI, pas de QI, pas de psychologie — seulement ce qui a été dit/fait

---

### 3.5 — Système d'injection ego-like (optionnel, à discuter)
Inspiré du sélecteur ego : un score de "pertinence contextuelle" par fait, permettant de n'injecter que les N faits les plus pertinents au message en cours, plutôt que tous.
→ **Décision différée** — à aborder après la collecte basique.

---

## 4. Décisions arrêtées

- [x] **Taille injection** : 300 tokens max pour le profil condensé en contexte
- [x] **Validation utilisateur** : **accumulation silencieuse, sans validation** — comme la mémoire humaine. Les premières impressions s'inscrivent, c'est le temps (et les nouvelles données) qui corrige. Pas de filtre préalable.
- [x] **Suppression** : l'utilisateur peut supprimer un **volume entier** pour forcer une régénération propre — pas de suppression granulaire de fait individuel.
- [x] **Volume 2 MD** : lecture humaine uniquement, pas d'injection IA
- [x] **Psychologie** : bannie de la génération automatique — sauf si l'utilisateur la saisit lui-même dans `profile_validated`
- [x] **Multi-profils** : architecture multi-profils dès le départ, sans surcoût — `user_tag = _current_user_name` (session active), pas de détection de contenu
- [x] **Déclencheur** : collecteur indépendant, appelé depuis Dream Engine + fermeture OGMA + bouton Phase 1 manuel

---

## 5. Ce qu'on garde de l'existant

- `select_memories_archiviste()` — sélection intelligente des souvenirs FAISS → **à conserver**
- Système de backup (Volume 1 + V2) → **à conserver**
- Boutons Phase 1 / Phase 2 → **à recâbler** sur la nouvelle logique de collecte
- `volume2_journal.md` → **à garder** pour lecture humaine uniquement (pas d'injection)

### Système de suppression de volumes

Un utilisateur doit pouvoir **repartir de zéro** sur sa biographie si elle est devenue fausse ou dépassée. Principe : suppression du volume uniquement, pas des signaux sources.

| Action | Ce qui est supprimé | Ce qui est conservé |
|---|---|---|
| Supprimer Volume 1 | `volume1_memories.json` | flags SQLite + cache (non traités) |
| Supprimer Volume 2 | `volume2_structured.json` + `volume2_journal.md` | Volume 1 intact |
| Supprimer tout | Les 3 fichiers volumes | Signaux bruts intacts → régénération possible |

Conséquence : après suppression, regenerer = relancer Phase 1 qui relit tous les signaux `bio_processed=false` pour repartir sur données fraîches. Pas de perte irréversible.

UI : 3 boutons de suppression dans la section biographie (avec confirmation), distincts des boutons de génération.

---

## 6. Modifications techniques par fichier

| Fichier | Modification |
|---|---|
| `memory_manager.py` SQLite | Ajouter colonnes `user_tag TEXT` et `bio_processed INTEGER DEFAULT 0` via migration |
| `memory_manager.py` `add_memory()` | Recevoir `user_tag` en paramètre (passé depuis session active) |
| `extensions/cognitive_cache/cache_manager.py` | Ajouter `user_tag` et `bio_processed` dans `add_entry()` |
| Conversations JSON (`data/conversations/*.json`) | Ajouter `user_tag` et `bio_processed` par entrée dans le champ `summaries[]` |
| `conversation_summarizer.py` (ou équivalent) | Passer `user_tag` lors de l'écriture du résumé |
| `data/instructions_defaults.json` (prompt Archiviste) | Ajouter instruction de tagging biographique (section 3.6) |
| `extensions/biographie_profil/biography_manager.py` | Phase 1 = enrichissement incrémental (lire JSON existant + nouveaux signaux) |
| Nouveau : `extensions/biographie_profil/signal_collector.py` | Scanner les 3 sources, grouper par `user_tag`, marquer `bio_processed=true` après traitement |

---

## 7. Prochaines étapes

1. ✅ Diagnostic terminé
2. ✅ Architecture définie
3. [ ] Répondre aux questions ouvertes (section 4)
4. [ ] Ajouter `user_tag` + `bio_processed` à SQLite (migration)
5. [ ] Modifier `cache_manager.py` pour supporter les flags
6. [ ] Écrire `signal_collector.py`
7. [ ] Recâbler Phase 1 sur le collecteur
8. [ ] Implémenter l'injection condensée en contexte
9. [ ] Tests sur données réelles

---

*Ce document est mis à jour au fil des discussions*

---

## 8. État d'implémentation (18 avril 2026)

### Ce qui est fait ✅

| Élément | Fichier | État |
|---|---|---|
| Colonnes SQLite `user_tag` + `bio_processed` + migration souple | `memory_manager.py` | ✅ |
| Paramètre `user_tag` dans `add_memory()` et `_store_in_sqlite()` | `memory_manager.py` | ✅ |
| Paramètre `user_tag` dans `add_entry()` du cache | `extensions/cognitive_cache/cache_manager.py` | ✅ |
| Paramètre `user_tag` dans `apply_cache_operations()` | `extensions/cognitive_cache/__init__.py` | ✅ |
| `set_user_tag()` + flag dans `add_summary_range()` | `conversation_summarizer.py` | ✅ |
| Appels `set_user_tag()` au login / auto-login / logout | `ogma_ng.py` | ✅ |
| Passage `user_tag=_current_user_name` aveugle sur 7 sites | `ogma_ng.py` | ✅ (temporaire — voir TODO #2) |
| `signal_collector.py` — collecte les 3 sources, marque `bio_processed` | `extensions/biographie_profil/signal_collector.py` | ✅ |
| Phase 1 JSON réécrite — incrémentale, basée sur les signaux | `biography_manager.py` | ✅ |
| Garde-fou Phase 2 — bloque si JSON sans données réelles | `biography_manager.py` | ✅ |
| Déclencheur automatique post-rêve | `extensions/dream_engine/dream_core.py` | ✅ |
| Déclencheur automatique à la fermeture d'OGMA | `ogma_ng.py` | ✅ |
| Nettoyage biography_manager.py — suppression ~17 méthodes MBTI/QI/psychiatrie, code orphelin | `biography_manager.py` | ✅ — 2565 → 1304 lignes |
| Simplification `_get_empty_structure` → structure `{metadata, facts[], profile_summary}` | `biography_manager.py` | ✅ |
| Recâblage bouton `⚡ Bio Compiler` appelant `compile_bio_incremental` | `ui_components.py` | ✅ |
| **Bloc A — A1** : `user_tag` dans le schéma JSON Archiviste (2 prompts) | `data/instructions_defaults.json` | ✅ |
| **Bloc A — A2** : `_call_archiviste_enrichment()` reçoit `current_user` | `memory_manager.py` | ✅ |
| **Bloc A — A3** : Lecture `user_tag` dans la réponse Archiviste | `memory_manager.py` | ✅ |
| **Bloc A — A4** : Propagation `user_tag` Archiviste → SQLite | `memory_manager.py` | ✅ |
| **Bloc A — A5** : `user_tag=_current_user_name` passé à `add_memory()` | `ogma_ng.py` | ✅ |

---

## 9. TODO LIST — Prochaines étapes

### Bloc A — Archiviste décide du prénom tampon (mémoires) — ✅ TERMINÉ

### Bloc B — Tests et validation

| # | Tâche | Détail |
|---|---|---|
| B1 | Vérifier `test_cognitive_cache.py` | Les appels `add_entry(conv_id, type, content)` passent sans user_tag — paramètre optionnel, OK |
| B2 | Test manuel : générer un souvenir, vérifier le `user_tag` en base | Confirmer que l'Archiviste tague bien "Yohan" pour du contenu user et null pour du contenu OGMA |
| B3 | Test Phase 1 après quelques échanges | Vérifier que des signaux sont bien collectés et intégrés dans le JSON |

### Bloc C — PAS encore à coder (sujets ouverts)

| # | Sujet | Note |
|---|---|---|
| C1 | Injection condensée du profil en contexte (section 3.4) | À faire après que le JSON biographique soit fiable |
| C2 | Score de pertinence contextuelle par fait (section 3.5) | Différé — à aborder après collecte basique |
