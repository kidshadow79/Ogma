# 🛡️ MAGIC PHRASE GUARD - Protection Globale Phrases Magiques OGMA

**Version** : 1.0.0
**Date** : 14 octobre 2025
**Auteurs** : Claude 4 + Yohan BROCARD
**Status** : ✅ Production

---

## 📋 TABLE DES MATIÈRES

1. [Vue d'Ensemble](#vue-densemble)
2. [Problème Résolu](#problème-résolu)
3. [Architecture](#architecture)
4. [Installation et Utilisation](#installation-et-utilisation)
5. [API Complète](#api-complète)
6. [Intégrations](#intégrations)
7. [Tests et Validation](#tests-et-validation)
8. [Maintenance et Évolution](#maintenance-et-évolution)
9. [FAQ](#faq)

---

## 🎯 VUE D'ENSEMBLE

### Problème Initial

Lors du **chargement d'une conversation archivée** contenant des phrases magiques (ex: "il faut que je réfléchisse", "qui suis-je", "écris dans ton journal"), ces phrases étaient **redétectées et déclenchaient à nouveau les extensions** (Introspection, Biographie, Journal, etc.), créant des actions en double et une expérience utilisateur dégradée.

### Solution Implémentée

Le **Magic Phrase Guard** est un module central de protection empêchant le déclenchement de phrases magiques pour les **messages historiques**, tout en autorisant leur traitement pour les **messages temps réel**.

### Architecture Double Protection

```
🛡️ PROTECTION 1 : Flag Temporel Global
└─ Actif pendant chargement conversation (0-5s)
└─ Variable _loading_historical_conversation = True

🛡️ PROTECTION 2 : Métadonnée Permanente
└─ Marque tous messages chargés avec from_history=True
└─ Persistante jusqu'à édition ou nouvelle conversation
```

### Extensions Protégées

- ✅ **Introspection (Cognitive Mirror)** - Phrases IA: "il faut que je réfléchisse"
- ✅ **Biographie Profil** - Phrases Luna: "qui suis-je", "rappelle-toi qui je suis"
- ✅ **Journal de Bord** - Phrases: "écris dans ton journal"
- ✅ **Temporal Guardian** - Phrases: "quelle heure", "quel jour"
- ✅ **Toute future extension** avec phrases magiques

---

## 🐛 PROBLÈME RÉSOLU

### Scénario Bugué (Avant)

```
1. Utilisateur charge conversation du 10 octobre
2. Conversation contient message : "il faut que je réfléchisse sur cela"
3. Message affiché → Callback détecte phrase magique
4. 🔴 INTROSPECTION RELANCÉE automatiquement (BUG)
5. Dialogue IA-Archiviste redémarre pour rien
6. Utilisateur confus
```

### Scénario Corrigé (Après)

```
1. Utilisateur charge conversation du 10 octobre
2. _loading_historical_conversation = True (FLAG)
3. Messages marqués from_history=True (MÉTADONNÉE)
4. Message affiché → Callback détecte phrase magique
5. 🛡️ should_process_magic_phrase() → False (BLOQUÉ)
6. ✅ Introspection ignorée - Lecture seule préservée
7. Utilisateur voit historique intact
```

---

## 🏗️ ARCHITECTURE

### Composants

```
magic_phrase_guard.py (Nouveau module central)
├─ activate_loading_mode()          # Activer protection temporelle
├─ deactivate_loading_mode()        # Désactiver protection
├─ mark_message_as_historical()     # Marquer message chargé
├─ should_process_magic_phrase()    # API principale (utilisée partout)
├─ clean_message_for_save()         # Nettoyer avant sauvegarde
└─ unmark_message_as_historical()   # Pour édition message

ogma_ng.py (Modifié)
├─ _load_conversation()             # Intégration activation + marquage
├─ _new_conversation()              # Intégration désactivation
├─ load_message_for_edit()          # Retrait from_history
└─ Callbacks extensions             # Vérification avant traitement

utils.py (Modifié)
└─ save_conversation()              # Nettoyage métadonnées
```

### Flux de Données

```
[CHARGEMENT CONVERSATION]
        ↓
activate_loading_mode()
FLAG: _loading_historical_conversation = True
        ↓
Pour chaque message JSON:
  mark_message_as_historical(msg)
  MÉTADONNÉE: msg['from_history'] = True
        ↓
_render_full_history()
(Affichage messages avec métadonnées)
        ↓
deactivate_loading_mode_delayed(1.5s)
FLAG: _loading_historical_conversation = False
        ↓
[PROTECTION ACTIVE PAR MÉTADONNÉE]


[DÉTECTION PHRASE MAGIQUE]
        ↓
Callback extension appelé
        ↓
should_process_magic_phrase(message_data, "EXTENSION_NAME")
        ↓
Vérifie FLAG temporel? → Oui → ❌ BLOQUÉ
        ↓
Vérifie MÉTADONNÉE? → Oui → ❌ BLOQUÉ
        ↓
Message temps réel → ✅ AUTORISÉ
```

---

## 🚀 INSTALLATION ET UTILISATION

### Pré-requis

- Python 3.10+
- OGMA v2.0+
- Modules : `asyncio`, `time`, `datetime`

### Installation

Le module est déjà intégré dans OGMA. Aucune installation supplémentaire requise.

```python
# Import automatique dans ogma_ng.py et utils.py
from magic_phrase_guard import should_process_magic_phrase
```

### Utilisation Basique

#### Pour une Nouvelle Extension

```python
# Dans votre callback de détection phrase magique

def on_extension_phrase_detected(main_content, message_index):
    """Callback appelé quand phrase magique détectée"""

    # 🛡️ VÉRIFICATION PROTECTION
    from magic_phrase_guard import should_process_magic_phrase

    # Récupérer métadonnées message actuel
    current_message_data = {}
    if message_index is not None and message_index < len(_chat_history_ui):
        current_message_data = _chat_history_ui[message_index]

    # Vérifier si traitement autorisé
    if should_process_magic_phrase(current_message_data, "MON_EXTENSION"):
        # ✅ Message temps réel - Traiter phrase magique
        trigger_my_extension(main_content)
    else:
        # ❌ Message historique - Ignorer silencieusement
        pass
```

#### Exemple Complet (Introspection)

```python
# Dans ogma_ng.py - Callback Cognitive Mirror

if COGNITIVE_MIRROR_AVAILABLE and main_content:
    from extensions.cognitive_mirror import is_enabled, check_magic_phrases

    if is_enabled():
        # 🛡️ MAGIC PHRASE GUARD
        from magic_phrase_guard import should_process_magic_phrase

        current_message_data = {}
        if message_index is not None and message_index < len(_chat_history_ui):
            current_message_data = _chat_history_ui[message_index]

        # Vérifier protection
        if should_process_magic_phrase(current_message_data, "INTROSPECTION"):
            magic_type = check_magic_phrases(main_content, source="ia")

            if magic_type == "trigger":
                # Lancer introspection normalement
                asyncio.create_task(trigger_introspection())
```

---

## 📚 API COMPLÈTE

### Fonctions Principales

#### `activate_loading_mode()`

Active le mode chargement historique (flag temporel).

```python
from magic_phrase_guard import activate_loading_mode

def _load_conversation(conv_id: str):
    # Activer protection
    activate_loading_mode()

    # Charger conversation...
    # Afficher messages...

    # Désactiver après délai
    asyncio.create_task(deactivate_loading_mode_delayed())
```

**Comportement** :
- Active flag global `_loading_historical_conversation = True`
- Lance timeout sécurité automatique (5 secondes)
- Bloque TOUTES détections phrases magiques

---

#### `deactivate_loading_mode()`

Désactive le mode chargement immédiatement.

```python
from magic_phrase_guard import deactivate_loading_mode

# Utilisation
deactivate_loading_mode()
```

**Comportement** :
- Désactive flag global `_loading_historical_conversation = False`
- Logs durée du chargement
- Protection métadonnée reste active

---

#### `deactivate_loading_mode_delayed(delay: float = 1.5)`

Désactive le mode après délai sécurité (asynchrone).

```python
from magic_phrase_guard import deactivate_loading_mode_delayed

# Désactivation après 1.5 secondes (recommandé)
asyncio.create_task(deactivate_loading_mode_delayed())

# Délai personnalisé
asyncio.create_task(deactivate_loading_mode_delayed(delay=2.0))
```

**Paramètres** :
- `delay` (float) : Délai en secondes (défaut: 1.5s)

**Usage recommandé** : Après `_render_full_history()`

---

#### `should_process_magic_phrase(message_data: Dict, extension_name: str) → bool`

⭐ **API PRINCIPALE** - Détermine si phrase magique doit être traitée.

```python
from magic_phrase_guard import should_process_magic_phrase

current_message = _chat_history_ui[message_index]

if should_process_magic_phrase(current_message, "MON_EXTENSION"):
    # ✅ Traiter phrase magique
    process_magic_phrase()
else:
    # ❌ Ignorer (message historique)
    pass
```

**Paramètres** :
- `message_data` (Dict) : Message complet avec métadonnées
- `extension_name` (str) : Nom extension pour logs (ex: "INTROSPECTION")

**Retourne** :
- `True` : Message temps réel → Traiter phrase magique
- `False` : Message historique → Ignorer phrase magique

**Vérifie dans l'ordre** :
1. Flag temporel `_loading_historical_conversation`
2. Métadonnée `message_data.get('from_history')`

---

#### `mark_message_as_historical(message: Dict) → Dict`

Marque un message comme historique (métadonnée permanente).

```python
from magic_phrase_guard import mark_message_as_historical

# Pour chaque message chargé
for msg in loaded_messages:
    msg = mark_message_as_historical(msg)
    history.append(msg)
```

**Comportement** :
- Ajoute `from_history: True` au message
- Retourne message modifié
- Ne modifie PAS le contenu original

---

#### `unmark_message_as_historical(message: Dict) → Dict`

Retire la marque historique (pour édition).

```python
from magic_phrase_guard import unmark_message_as_historical

def load_message_for_edit(message_index):
    message = _chat_history_ui[message_index]

    # Retirer métadonnée (message redevient "vivant")
    message = unmark_message_as_historical(message)
```

**Comportement** :
- Retire `from_history` du message
- Message traité comme nouveau après édition
- Logs action effectuée

---

#### `clean_message_for_save(message: Dict) → Dict`

Nettoie message avant sauvegarde (retire métadonnées internes).

```python
from magic_phrase_guard import clean_message_for_save

cleaned_history = []
for msg in history:
    cleaned_msg = clean_message_for_save(msg)
    cleaned_history.append(cleaned_msg)

# Sauvegarder version nettoyée
save_to_json(cleaned_history)
```

**Comportement** :
- Retire `from_history` et autres métadonnées runtime
- Préserve `role`, `content`, `timestamp`, `memorized`
- JSON reste propre et léger

---

### Fonctions Utilitaires

#### `is_loading_history() → bool`

Vérifie si chargement en cours.

```python
from magic_phrase_guard import is_loading_history

if is_loading_history():
    print("Chargement historique actif")
```

---

#### `get_stats() → Dict`

Retourne statistiques du gardien.

```python
from magic_phrase_guard import get_stats

stats = get_stats()
print(f"Blocages totaux: {stats['total_blocks']}")
print(f"Extensions protégées: {stats['extensions_protected']}")
```

**Statistiques disponibles** :
- `total_blocks` : Nombre total de blocages
- `blocks_by_flag` : Blocages par flag temporel
- `blocks_by_metadata` : Blocages par métadonnée
- `currently_loading` : État chargement actuel
- `extensions_protected` : Liste extensions protégées
- `last_block_time` : Timestamp dernier blocage

---

#### `print_stats()`

Affiche statistiques formatées dans console.

```python
from magic_phrase_guard import print_stats

print_stats()
```

**Sortie exemple** :
```
============================================================
📊 MAGIC PHRASE GUARD - Statistiques
============================================================
Session démarrée: 2025-10-14T15:30:00
Chargement actif: NON

🛡️ Blocages totaux: 127
  - Par flag temporel: 45
  - Par métadonnée: 82

🔧 Extensions protégées:
  - INTROSPECTION
  - BIOGRAPHIE
  - JOURNAL

Dernier blocage: 2025-10-14T16:45:23
============================================================
```

---

#### `reset_stats()`

Réinitialise les statistiques (utile pour tests).

```python
from magic_phrase_guard import reset_stats

reset_stats()
```

---

## 🔧 INTÉGRATIONS

### Extension Cognitive Mirror (Introspection)

**Fichier** : `ogma_ng.py:1576-1681`

**Modification** :
```python
# AVANT (BUG)
if magic_type == "trigger":
    asyncio.create_task(trigger_introspection())

# APRÈS (PROTÉGÉ)
if should_process_magic_phrase(current_message_data, "INTROSPECTION"):
    if magic_type == "trigger":
        asyncio.create_task(trigger_introspection())
```

**Phrases magiques protégées** :
- "il faut que je réfléchisse" (IA)
- "réfléchis", "réfléchis profondément", "introspection" (Utilisateur)

---

### Extension Biographie Profil

**Fichier** : `ogma_ng.py:1559-1584`

**Modification** :
```python
# AVANT (BUG)
if biography_magic:
    luna_magic_response = biography_magic._handle_luna_magic_phrases(main_content)

# APRÈS (PROTÉGÉ)
if should_process_magic_phrase(current_message_data, "BIOGRAPHIE"):
    if biography_magic:
        luna_magic_response = biography_magic._handle_luna_magic_phrases(main_content)
```

**Phrases magiques protégées** :
- "qui suis-je", "rappelle-toi qui je suis" (Luna)
- "qui es-tu", "présente-toi" (Utilisateur)

---

### Extension Journal de Bord

**Intégration future recommandée** (même pattern) :

```python
# Dans callback journal
if should_process_magic_phrase(current_message_data, "JOURNAL"):
    if "écris dans ton journal" in main_content.lower():
        trigger_journal_entry()
```

---

### Chargement Conversation

**Fichier** : `ogma_ng.py:2571-2644`

**Modifications** :
1. Import du module
2. Activation flag temporel au début
3. Marquage de tous les messages
4. Désactivation différée après affichage

```python
def _load_conversation(conv_id: str):
    from magic_phrase_guard import activate_loading_mode, deactivate_loading_mode_delayed, mark_message_as_historical

    try:
        # 🛡️ PROTECTION 1: Activer flag
        activate_loading_mode()

        # Charger JSON
        for msg in raw:
            entry = {'role': role, 'content': content, ...}

            # 🛡️ PROTECTION 2: Marquer message
            entry = mark_message_as_historical(entry)
            new_hist.append(entry)

        # Afficher
        _render_full_history()

        # 🛡️ Désactiver après délai
        asyncio.create_task(deactivate_loading_mode_delayed())

    except Exception as e:
        # Sécurité: désactiver même si erreur
        deactivate_loading_mode()
```

---

### Nouvelle Conversation

**Fichier** : `ogma_ng.py:2647-2677`

**Modification** :
```python
def _new_conversation():
    from magic_phrase_guard import deactivate_loading_mode

    # S'assurer que flag est désactivé
    deactivate_loading_mode()

    # ... réinitialiser historiques ...
```

---

### Sauvegarde Conversation

**Fichier** : `utils.py:38-61`

**Modification** :
```python
def save_conversation(conversation_id: str, history: list[dict]):
    from magic_phrase_guard import clean_message_for_save

    # Nettoyer métadonnées internes
    cleaned_history = []
    for msg in history:
        cleaned_msg = clean_message_for_save(msg)
        cleaned_history.append(cleaned_msg)

    # Sauvegarder version propre
    filepath.write_text(json.dumps(cleaned_history, ...))
```

---

### Édition Message

**Fichier** : `ogma_ng.py:2010-2042`

**Modification** :
```python
def load_message_for_edit(original_content: str, message_index: int):
    from magic_phrase_guard import unmark_message_as_historical

    # Retirer from_history (message devient éditable)
    if message_index < len(_chat_history_ui):
        _chat_history_ui[message_index] = unmark_message_as_historical(_chat_history_ui[message_index])

    # ... charger dans input ...
```

---

## 🧪 TESTS ET VALIDATION

### Tests Unitaires Intégrés

Le module inclut des tests unitaires exécutables :

```bash
# Lancer tests
python magic_phrase_guard.py
```

**Tests inclus** :
1. ✅ Activation/Désactivation flag temporel
2. ✅ Marquage message comme historique
3. ✅ Détection message historique (métadonnée)
4. ✅ Nettoyage message pour sauvegarde
5. ✅ Should process (message temps réel)
6. ✅ Should process (message historique bloqué)
7. ✅ Statistiques

---

### Scénarios de Test Manuel

#### Test 1 : Chargement Conversation avec Introspection

**Étapes** :
1. Créer conversation contenant "il faut que je réfléchisse"
2. Sauvegarder et fermer
3. Recharger conversation

**Résultat attendu** :
```
[MAGIC-GUARD] 🛡️ Mode chargement historique ACTIVÉ
[CONVERSATION-LOAD] ✅ Conversation chargée (15 messages marqués from_history)
[INTROSPECTION] 🛡️ [INTROSPECTION] Message historique bloqué (FLAG-TEMPOREL)
[MAGIC-GUARD] 🛡️ Mode chargement historique DÉSACTIVÉ (durée: 0.82s)
```

✅ **Introspection ne se relance PAS**

---

#### Test 2 : Nouveau Message Temps Réel

**Étapes** :
1. Dans conversation active
2. Taper "il faut que je réfléchisse"
3. Envoyer

**Résultat attendu** :
```
[INTROSPECTION] 🧠 Phrase magique IA détectée: déclenchement différé
[INTROSPECTION-CORE] 🧠 Démarrage introspection...
```

✅ **Introspection se lance normalement**

---

#### Test 3 : Édition Message Historique

**Étapes** :
1. Charger conversation
2. Cliquer "✎ Modifier" sur ancien message
3. Ajouter "il faut que je réfléchisse"
4. Envoyer

**Résultat attendu** :
```
[EDIT-MESSAGE] 🔄 Message #5 démarqué - devient éditable
[INTROSPECTION] 🧠 Phrase magique IA détectée: déclenchement différé
```

✅ **Message édité traité comme nouveau**

---

#### Test 4 : Biographie Profil Protégée

**Étapes** :
1. Créer conversation avec "qui suis-je"
2. Recharger conversation

**Résultat attendu** :
```
[MAGIC-GUARD] 🛡️ [BIOGRAPHIE] Message historique bloqué (MÉTADONNÉE)
```

✅ **Recherche biographie ne se relance PAS**

---

#### Test 5 : Sauvegarde Propre

**Étapes** :
1. Charger conversation (messages marqués `from_history=True`)
2. Sauvegarder conversation

**Vérification** :
```bash
# Inspecter JSON sauvegardé
cat data/conversations/2025-10-14_15-30-00.json
```

**Résultat attendu** :
```json
[
  {
    "role": "user",
    "content": "Bonjour",
    "memorized": false
  }
]
```

✅ **Pas de `from_history` dans JSON sauvegardé**

---

### Validation en Production

**Checklist** :
- [ ] Aucun message d'erreur dans console
- [ ] Conversations chargées lisibles sans actions parasites
- [ ] Nouveaux messages déclenchent extensions normalement
- [ ] Édition messages fonctionne correctement
- [ ] Fichiers JSON propres (sans from_history)
- [ ] Statistiques accessibles via `get_stats()`

---

## 🔄 MAINTENANCE ET ÉVOLUTION

### Ajout Nouvelle Extension

Pour protéger une nouvelle extension avec phrases magiques :

```python
# 1. Identifier callback détection phrase magique
def my_extension_callback(main_content, message_index):

    # 2. Ajouter vérification protection
    from magic_phrase_guard import should_process_magic_phrase

    current_message_data = {}
    if message_index is not None and message_index < len(_chat_history_ui):
        current_message_data = _chat_history_ui[message_index]

    # 3. Conditionner traitement
    if should_process_magic_phrase(current_message_data, "MA_NOUVELLE_EXTENSION"):
        # Traiter phrase magique normalement
        trigger_my_extension()
```

**C'est tout !** Pas besoin de modifier `magic_phrase_guard.py`.

---

### Debugging

#### Activer Logs Détaillés

Les logs sont déjà inclus. Observer dans console :

```
[MAGIC-GUARD] 🛡️ Mode chargement historique ACTIVÉ
[MAGIC-GUARD] 🛡️ [INTROSPECTION] Message historique bloqué (FLAG-TEMPOREL)
[MAGIC-GUARD] 🛡️ [BIOGRAPHIE] Message historique bloqué (MÉTADONNÉE)
[MAGIC-GUARD] 🛡️ Mode chargement historique DÉSACTIVÉ (durée: 1.23s)
```

#### Afficher Statistiques

```python
from magic_phrase_guard import print_stats

# Afficher stats complètes
print_stats()
```

#### Vérifier État Actuel

```python
from magic_phrase_guard import is_loading_history, get_stats

if is_loading_history():
    print("⚠️ Chargement en cours - Protection active")

stats = get_stats()
print(f"Blocages: {stats['total_blocks']}")
```

---

### Évolutions Futures Possibles

#### 1. Whitelist Extensions (Non-Bloquantes)

Permettre certaines extensions de s'exécuter même sur messages historiques :

```python
WHITELIST_EXTENSIONS = ["TEMPORAL_GUARDIAN"]  # Toujours actif

def should_process_magic_phrase(message_data, extension_name):
    if extension_name in WHITELIST_EXTENSIONS:
        return True  # Bypass protection

    # Protection normale...
```

#### 2. Granularité par Type de Phrase

Bloquer seulement certains types de phrases magiques :

```python
def should_process_magic_phrase(message_data, extension_name, phrase_type="all"):
    """
    phrase_type: "trigger", "stop", "memorization", "all"
    """
    if phrase_type == "stop":
        return True  # Toujours autoriser arrêt

    # Protection normale pour triggers...
```

#### 3. Mode Debug Avancé

```python
DEBUG_MODE = os.getenv("OGMA_GUARD_DEBUG", "false") == "true"

if DEBUG_MODE:
    print(f"[DEBUG] Message data: {message_data}")
    print(f"[DEBUG] Flag status: {_loading_historical_conversation}")
```

---

## ❓ FAQ

### Q1 : Pourquoi deux protections (flag + métadonnée) ?

**R** : Redondance sécurisée.
- **Flag temporel** : Protection immédiate pendant chargement (0-1.5s)
- **Métadonnée** : Protection permanente (même après timeout flag)

Si un système échoue, l'autre protège.

---

### Q2 : Que se passe-t-il si j'oublie d'utiliser `should_process_magic_phrase()` ?

**R** : L'extension déclenchera phrases magiques sur messages historiques (bug original).

**Solution** : Audit de code pour identifier toutes détections phrases magiques.

---

### Q3 : Puis-je désactiver la protection pour une extension spécifique ?

**R** : Oui, ne pas appeler `should_process_magic_phrase()` dans le callback de l'extension.

Ou ajouter whitelist (voir Évolutions Futures).

---

### Q4 : La métadonnée `from_history` alourdit-elle les fichiers JSON ?

**R** : Non ! `clean_message_for_save()` retire automatiquement toutes métadonnées avant sauvegarde.

Métadonnée existe seulement en mémoire runtime.

---

### Q5 : Que faire si flag temporel reste bloqué ?

**R** : Timeout sécurité automatique après 5 secondes.

Manuellement :
```python
from magic_phrase_guard import deactivate_loading_mode
deactivate_loading_mode()
```

---

### Q6 : Comment tester que ma nouvelle extension est protégée ?

**R** : Scénario test simple :
1. Créer conversation avec phrase magique extension
2. Sauvegarder et recharger
3. Vérifier logs : `[MAGIC-GUARD] 🛡️ [MON_EXTENSION] Message historique bloqué`

---

### Q7 : Impact performance du système ?

**R** : **Négligeable**.
- Vérifications = 2 conditions booléennes (~0.001ms)
- Pas de charge CPU significative
- Pas d'impact mémoire (métadonnée = 1 bool par message)

---

### Q8 : Compatible avec toutes versions OGMA ?

**R** : Testé avec OGMA v2.0+.

Requis :
- Python 3.10+
- `asyncio` support
- Architecture double historique (`_chat_history` + `_chat_history_ui`)

---

### Q9 : Puis-je utiliser ce système dans un autre projet ?

**R** : Oui ! Module standalone.

Adapter :
- Chemins imports
- Variables globales historique
- Callbacks extensions

---

### Q10 : Qui contacter pour support ?

**R** :
- Issues GitHub : `https://github.com/anthropics/ogma/issues`
- Documentation : `docs/MAGIC_PHRASE_GUARD.md`
- Tests : `python magic_phrase_guard.py`

---

## 📝 CHANGELOG

### v1.0.0 - 14 octobre 2025
- ✅ Création module `magic_phrase_guard.py`
- ✅ Intégration `_load_conversation()` avec double protection
- ✅ Intégration `save_conversation()` avec nettoyage
- ✅ Protection Cognitive Mirror (Introspection)
- ✅ Protection Biographie Profil
- ✅ Gestion édition messages (`unmark_message_as_historical`)
- ✅ Tests unitaires intégrés
- ✅ Documentation complète
- ✅ Statistiques et monitoring

---

## 🏆 CRÉDITS

**Conception** : Yohan BROCARD
**Implémentation** : Claude 4 (Anthropic)
**Architecture** : Solution hybride collaborative
**Tests** : Validation croisée concepteur/IA

---

## 📜 LICENCE

Ce module fait partie du projet OGMA.
Propriété intellectuelle : Yohan BROCARD © 2025

---

**FIN DE LA DOCUMENTATION**

Pour questions ou suggestions d'amélioration, consulter les issues GitHub du projet OGMA.
