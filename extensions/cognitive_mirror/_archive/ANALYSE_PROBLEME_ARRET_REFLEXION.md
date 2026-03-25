# ANALYSE DU PROBLÈME - Arrêt Impossible des États Réflexifs
## Extension Cognitive Mirror - Système de Réflexion Subconscience

**Date**: 2025-10-05
**Symptômes**:
- Le compte à rebours reste visible même après STOP
- Le message `[SUBCONSCIENCE] Inactivité ignorée (état: ACTIVE)` continue d'apparaître
- La réflexion redémarre malgré l'appui sur le bouton STOP
- L'IA ne peut pas arrêter la réflexion même si elle le décide

---

## 🔍 DIAGNOSTIC COMPLET

### 1. ARCHITECTURE DU SYSTÈME

Le système de réflexion Cognitive Mirror repose sur **3 composants principaux** :

```
┌─────────────────────────────────────────────────────┐
│  CognitiveMirrorCore (core_cognitive_mirror.py)    │
│  - Machine à états (OFF/STANDBY/ACTIVE/INTEGRATING)│
│  - Orchestration globale                            │
└────────────┬────────────────────────────────────────┘
             │
    ┌────────┴────────┬────────────────────────┐
    │                 │                        │
┌───▼────────────┐ ┌──▼──────────────────┐ ┌──▼──────────────────┐
│InactivityDetect│ │SubconscienceOrchest│ │MemoryIntegration    │
│- Surveille      │ │- Gère conversation  │ │- Sauvegarde         │
│  inactivité     │ │  Luna↔Archiviste    │ │  réflexions         │
│- Thread polling │ │- Boucle async       │ │                     │
└────────────────┘ └─────────────────────┘ └─────────────────────┘
```

---

### 2. FLUX D'ARRÊT NORMAL (Ce qui devrait se passer)

```
Utilisateur appuie STOP
    │
    ▼
[UI] stop_reflection_session("user_stop_request")
    │
    ▼
[CORE] _force_stop_conversation("user_stop_request")
    │
    ├──► [ORCHESTRATOR] stop_conversation("user_stop_request")
    │         │
    │         ├──► stop_event.set()  ← Signal arrêt boucle async
    │         └──► _finalize_conversation()
    │
    ├──► active_conversation_session = None
    ├──► session_id = None
    │
    ├──► _set_state(STANDBY)  ← Retour état STANDBY
    │
    └──► CONDITION: Si raison = "user_stop_request"
              → NE PAS redémarrer monitoring (ligne 600)
              → SINON: _start_inactivity_monitoring() ← PROBLÈME ICI
```

**LIGNE CRITIQUE** : `core_cognitive_mirror.py:596-600`
```python
user_stop_reasons = ["user_stop_request", "user_button_stop", "manual_stop"]
if reason not in user_stop_reasons:
    self._start_inactivity_monitoring()  ← REDÉMARRE LE MONITORING
else:
    print(f"[SUBCONSCIENCE] ⚠️ Arrêt utilisateur ({reason}) - monitoring NON redémarré")
```

---

### 3. PROBLÈMES IDENTIFIÉS

#### ❌ PROBLÈME #1: Race Condition sur `set_reflection_session_active`

**Localisation**: `inactivity_detector.py:148-151` + `core_cognitive_mirror.py:422-423`

**Le bug**:
```python
# Dans _trigger_conversation() - ligne 422
if self.inactivity_detector:
    self.inactivity_detector.set_reflection_session_active(True)  ← Mis à TRUE

# Plus tard, dans _on_activity_resumed() - ligne 687
if self.inactivity_detector:
    self.inactivity_detector.set_reflection_session_active(False)  ← Mis à FALSE
```

**Problème**: Entre le moment où le flag est mis à `False` (ligne 687) et le retour à `STANDBY`, la boucle de surveillance (`inactivity_detector.py:210-251`) continue de tourner.

**Séquence bugguée**:
```
1. État ACTIVE, flag session_active = True
2. Utilisateur appuie STOP
3. _on_activity_resumed() met flag session_active = False
4. _complete_integration() → _set_state(STANDBY)
5. _start_inactivity_monitoring() REDÉMARRE le monitoring
6. Thread InactivityDetector continue dans sa boucle
7. _check_inactivity_triggers() détecte inactivité
8. Callback _on_inactivity_detected() est appelé
9. Nouvelle conversation démarre car état = STANDBY
```

---

#### ❌ PROBLÈME #2: Le Thread InactivityDetector n'est JAMAIS arrêté

**Localisation**: `inactivity_detector.py:210-251` (boucle `_monitoring_loop`)

**Le code actuel**:
```python
def _monitoring_loop(self):
    """Boucle principale de surveillance (thread séparé)"""
    print("[INACTIVITY-DETECTOR] 🔄 Thread de surveillance démarré")

    while not self.shutdown_event.is_set():  ← Continue tant que shutdown_event n'est pas set
        try:
            if not self.is_monitoring_active:  ← Vérifie le flag
                break  ← Sort SEULEMENT si flag = False

            # ... vérifications ...

            trigger_type, duration = self._check_inactivity_triggers()

            if trigger_type:
                if self.on_inactivity_detected:
                    self.on_inactivity_detected(trigger_type, duration)  ← APPELLE CALLBACK

                # LIGNE 236: Reset des timers pour surveiller retour d'activité
                self.last_user_message_time = time.time()  ← ERREUR: ces variables n'existent pas
                if self.keyboard_monitoring_enabled:
                    self.last_keyboard_activity = time.time()  ← ERREUR: variable inexistante
```

**BUG MAJEUR ligne 239-241**: Les variables `last_user_message_time` et `last_keyboard_activity` **n'existent pas** !

Les vraies variables sont:
- `self.last_message_time` (ligne 69)
- `self.last_keypress_time` (ligne 70)

**Conséquence**: Le reset des timers échoue silencieusement, donc :
1. Le détecteur continue de voir de l'inactivité
2. Il rappelle `_on_inactivity_detected()` en boucle
3. Une nouvelle conversation redémarre immédiatement

---

#### ❌ PROBLÈME #3: Redémarrage Automatique du Monitoring

**Localisation**: `core_cognitive_mirror.py:591-600` + `core_cognitive_mirror.py:622-633`

**Le problème**: Il y a **DEUX endroits** où le monitoring peut redémarrer :

**Endroit 1** - `_force_stop_conversation()`:
```python
# Ligne 591-600
if self.current_state != SubconscienceState.OFF and reason != "shutdown":
    self._set_state(SubconscienceState.STANDBY)

    user_stop_reasons = ["user_stop_request", "user_button_stop", "manual_stop"]
    if reason not in user_stop_reasons:
        self._start_inactivity_monitoring()  ← REDÉMARRE
    else:
        print(f"[SUBCONSCIENCE] ⚠️ Arrêt utilisateur ({reason}) - monitoring NON redémarré")
```

**Endroit 2** - `_complete_integration()`:
```python
# Ligne 622-633
if self.is_enabled():
    self._set_state(SubconscienceState.STANDBY)

    user_stop_reasons = ["user_stop_request", "user_button_stop", "manual_stop", "luna_exit"]
    if not hasattr(self, 'last_stop_reason') or self.last_stop_reason not in user_stop_reasons:
        self._start_inactivity_monitoring()  ← REDÉMARRE AUSSI
    else:
        print(f"[SUBCONSCIENCE] ⚠️ Arrêt utilisateur ({self.last_stop_reason}) détecté")
        self.last_stop_reason = None  ← Reset
```

**BUG**: La variable `last_stop_reason` est utilisée mais **n'est jamais définie** dans `_force_stop_conversation()` !

**Séquence du bug**:
```
1. User appuie STOP → raison = "user_stop_request"
2. _force_stop_conversation("user_stop_request")
   → Ne redémarre PAS le monitoring (condition ligne 597)
3. _complete_integration("user_return")
   → Vérifie self.last_stop_reason (ligne 627)
   → MAIS last_stop_reason n'a jamais été définie !
   → hasattr() retourne False
   → REDÉMARRE le monitoring quand même !
```

---

#### ❌ PROBLÈME #4: Le Message "Inactivité ignorée (état: ACTIVE)"

**Localisation**: `core_cognitive_mirror.py:670-676`

```python
def _on_inactivity_detected(self, detection_type: str, duration: float):
    """Callback détection inactivité"""

    # Vérification état extension
    if not self.is_enabled():
        print(f"[SUBCONSCIENCE] 🛑 Callback ignoré - extension désactivée")
        return

    print(f"[SUBCONSCIENCE] Inactivité détectée: {detection_type} ({duration:.1f}s)")

    if self.current_state == SubconscienceState.STANDBY:
        print("[SUBCONSCIENCE] Déclenchement conversation automatique...")
        self._trigger_conversation(detection_type)
    else:
        print(f"[SUBCONSCIENCE] Inactivité ignorée (état: {self.current_state.value})")
        # ← PROBLÈME: Aucune action pour ARRÊTER la détection !
```

**Problème**: Quand l'état est `ACTIVE`, le callback est appelé en boucle par le thread `InactivityDetector`, mais :
1. Rien n'arrête le thread
2. Le message "Inactivité ignorée" spam les logs
3. Dès que l'état repasse à `STANDBY`, une nouvelle conversation démarre

---

### 4. BOUCLE INFINIE RECONSTITUÉE

Voici ce qui se passe étape par étape quand l'utilisateur appuie sur STOP :

```
[T=0s] État: ACTIVE, Conversation en cours, InactivityDetector thread actif

[T=0.1s] Utilisateur appuie STOP
    └─► UI: stop_reflection_session("user_stop_request")
        └─► CORE: _force_stop_conversation("user_stop_request")
            ├─► ORCHESTRATOR: stop_conversation("user_stop_request")
            │    ├─► stop_event.set()  ← Boucle async reçoit signal
            │    └─► _finalize_conversation("user_stop_request")
            │
            ├─► active_conversation_session = None
            ├─► _set_state(STANDBY)
            └─► Vérif raison: "user_stop_request" in user_stop_reasons ?
                 └─► OUI → Monitoring NON redémarré ✅

[T=0.2s] _on_activity_resumed() est AUSSI appelé
    └─► set_reflection_session_active(False)
    └─► _complete_integration("user_return")
        ├─► _set_state(STANDBY)
        └─► Vérif last_stop_reason:
             └─► hasattr(self, 'last_stop_reason') ?
                  └─► NON (jamais définie !) ❌
                       └─► _start_inactivity_monitoring() REDÉMARRE ❌

[T=0.3s] Thread InactivityDetector toujours actif (jamais arrêté)
    └─► Boucle while not self.shutdown_event.is_set()
        ├─► Vérifie inactivité
        ├─► trigger_type = "no_message" (30s écoulés)
        ├─► Appelle on_inactivity_detected("no_message", 30.5)
        │    └─► État actuel: STANDBY
        │         └─► _trigger_conversation("no_message")
        │              └─► NOUVELLE CONVERSATION DÉMARRE ❌
        │
        └─► Reset timers (LIGNE 239-241)
             └─► self.last_user_message_time = time.time()  ← VARIABLE N'EXISTE PAS ❌
             └─► Timer ne se reset JAMAIS

[T=30s] Inactivité détectée à nouveau
    └─► Boucle se répète à l'infini...
```

---

## 🛠️ SOLUTIONS PROPOSÉES

### SOLUTION #1: Arrêter Proprement le Thread InactivityDetector

**Fichier**: `core_cognitive_mirror.py`

**Modification ligne 596-600**:

```python
# AVANT
user_stop_reasons = ["user_stop_request", "user_button_stop", "manual_stop"]
if reason not in user_stop_reasons:
    self._start_inactivity_monitoring()
else:
    print(f"[SUBCONSCIENCE] ⚠️ Arrêt utilisateur ({reason}) - monitoring NON redémarré")

# APRÈS
user_stop_reasons = ["user_stop_request", "user_button_stop", "manual_stop"]
if reason not in user_stop_reasons:
    self._start_inactivity_monitoring()
else:
    print(f"[SUBCONSCIENCE] ⚠️ Arrêt utilisateur ({reason}) - monitoring STOPPÉ")
    self._stop_inactivity_monitoring()  ← AJOUTER CETTE LIGNE
```

---

### SOLUTION #2: Définir last_stop_reason dans _force_stop_conversation

**Fichier**: `core_cognitive_mirror.py`

**Modification ligne 582-600**:

```python
def _force_stop_conversation(self, reason: str):
    """Force l'arrêt de la conversation en cours"""
    if self.conversation_orchestrator:
        self.conversation_orchestrator.stop_conversation(reason)

    self.active_conversation_session = None
    self.session_id = None

    # AJOUTER CETTE LIGNE: Stocker la raison d'arrêt
    self.last_stop_reason = reason  ← NOUVELLE LIGNE

    # Retour état STANDBY seulement si l'extension est toujours activée
    if self.current_state != SubconscienceState.OFF and reason != "shutdown":
        self._set_state(SubconscienceState.STANDBY)

        user_stop_reasons = ["user_stop_request", "user_button_stop", "manual_stop"]
        if reason not in user_stop_reasons:
            self._start_inactivity_monitoring()
        else:
            print(f"[SUBCONSCIENCE] ⚠️ Arrêt utilisateur ({reason}) - monitoring NON redémarré")
            self._stop_inactivity_monitoring()  # Solution #1
```

---

### SOLUTION #3: Corriger les Noms de Variables dans InactivityDetector

**Fichier**: `inactivity_detector.py`

**Modification ligne 236-241**:

```python
# AVANT (LIGNE 236-241)
if trigger_type:
    if self.on_inactivity_detected:
        self.on_inactivity_detected(trigger_type, duration)

    # Reset des timers pour surveiller le retour d'activité
    self.last_user_message_time = time.time()  ← MAUVAIS NOM
    if self.keyboard_monitoring_enabled:
        self.last_keyboard_activity = time.time()  ← MAUVAIS NOM

# APRÈS
if trigger_type:
    if self.on_inactivity_detected:
        self.on_inactivity_detected(trigger_type, duration)

    # Reset des timers pour surveiller le retour d'activité
    self.last_message_time = time.time()  ← CORRIGÉ
    if self.keyboard_monitoring_enabled:
        self.last_keypress_time = time.time()  ← CORRIGÉ
```

---

### SOLUTION #4: Arrêter le Thread quand État = ACTIVE et Inactivité Détectée

**Fichier**: `core_cognitive_mirror.py`

**Modification ligne 670-676**:

```python
# AVANT
def _on_inactivity_detected(self, detection_type: str, duration: float):
    if not self.is_enabled():
        print(f"[SUBCONSCIENCE] 🛑 Callback ignoré - extension désactivée")
        return

    print(f"[SUBCONSCIENCE] Inactivité détectée: {detection_type} ({duration:.1f}s)")

    if self.current_state == SubconscienceState.STANDBY:
        print("[SUBCONSCIENCE] Déclenchement conversation automatique...")
        self._trigger_conversation(detection_type)
    else:
        print(f"[SUBCONSCIENCE] Inactivité ignorée (état: {self.current_state.value})")

# APRÈS
def _on_inactivity_detected(self, detection_type: str, duration: float):
    if not self.is_enabled():
        print(f"[SUBCONSCIENCE] 🛑 Callback ignoré - extension désactivée")
        return

    print(f"[SUBCONSCIENCE] Inactivité détectée: {detection_type} ({duration:.1f}s)")

    if self.current_state == SubconscienceState.STANDBY:
        print("[SUBCONSCIENCE] Déclenchement conversation automatique...")
        self._trigger_conversation(detection_type)
    elif self.current_state == SubconscienceState.ACTIVE:
        # NOUVEAU: Si déjà en conversation, arrêter le monitoring pour éviter spam
        print(f"[SUBCONSCIENCE] Inactivité ignorée (état: ACTIVE) - arrêt monitoring temporaire")
        if self.inactivity_detector:
            self.inactivity_detector.stop_monitoring()
    else:
        print(f"[SUBCONSCIENCE] Inactivité ignorée (état: {self.current_state.value})")
```

---

### SOLUTION #5: Vérifier set_reflection_session_active AVANT Déclenchement

**Fichier**: `inactivity_detector.py`

**Modification ligne 253-274**:

```python
# AVANT
def _check_inactivity_triggers(self) -> tuple[Optional[str], float]:
    current_time = time.time()

    # Vérification inactivité messages
    if self.last_message_time:
        message_inactivity = current_time - self.last_message_time
        if message_inactivity >= self.no_message_delay:
            return ("no_message", message_inactivity)

    # Vérification inactivité clavier
    if self.keyboard_monitoring_enabled and self.last_keypress_time:
        typing_inactivity = current_time - self.last_keypress_time
        if typing_inactivity >= self.no_typing_delay:
            return ("no_typing", typing_inactivity)

    return (None, 0.0)

# APRÈS
def _check_inactivity_triggers(self) -> tuple[Optional[str], float]:
    current_time = time.time()

    # NOUVEAU: Ne PAS déclencher si session réflexive déjà active
    if self.is_reflection_session_active:
        return (None, 0.0)  ← Court-circuit si session active

    # Vérification inactivité messages
    if self.last_message_time:
        message_inactivity = current_time - self.last_message_time
        if message_inactivity >= self.no_message_delay:
            return ("no_message", message_inactivity)

    # Vérification inactivité clavier
    if self.keyboard_monitoring_enabled and self.last_keypress_time:
        typing_inactivity = current_time - self.last_keypress_time
        if typing_inactivity >= self.no_typing_delay:
            return ("no_typing", typing_inactivity)

    return (None, 0.0)
```

---

## 📊 RÉCAPITULATIF DES CORRECTIONS

| # | Fichier | Ligne | Type | Criticité |
|---|---------|-------|------|-----------|
| 1 | `core_cognitive_mirror.py` | 600 | Ajouter `_stop_inactivity_monitoring()` | 🔴 CRITIQUE |
| 2 | `core_cognitive_mirror.py` | 588 | Définir `self.last_stop_reason = reason` | 🔴 CRITIQUE |
| 3 | `inactivity_detector.py` | 239-241 | Corriger noms variables | 🔴 CRITIQUE |
| 4 | `core_cognitive_mirror.py` | 676 | Arrêter monitoring si ACTIVE | 🟡 IMPORTANT |
| 5 | `inactivity_detector.py` | 260 | Court-circuit si session active | 🟡 IMPORTANT |

---

## 🧪 TESTS DE VALIDATION

Après application des corrections, tester :

1. ✅ **Arrêt bouton STOP**:
   - Démarrer une réflexion (inactivité ou manuelle)
   - Appuyer sur STOP
   - Vérifier: Le monitoring s'arrête, pas de redémarrage automatique

2. ✅ **Arrêt par l'IA (Luna décide d'arrêter)**:
   - Laisser Luna envoyer un message de fin
   - Vérifier: La session se termine, monitoring ne redémarre pas immédiatement

3. ✅ **Retour utilisateur pendant réflexion**:
   - Démarrer réflexion
   - Envoyer un message utilisateur
   - Vérifier: Réflexion s'arrête, monitoring ne redémarre pas

4. ✅ **Logs de vérification**:
   - Plus de message `"Inactivité ignorée (état: ACTIVE)"` en boucle
   - Message `"monitoring STOPPÉ"` visible après STOP

---

## 🎯 PRIORITÉ D'IMPLÉMENTATION

**PHASE 1** (Corrections critiques - 15 min):
1. Solution #1: Arrêter monitoring après user_stop
2. Solution #2: Définir last_stop_reason
3. Solution #3: Corriger noms variables

**PHASE 2** (Optimisations - 10 min):
4. Solution #4: Arrêter monitoring si ACTIVE
5. Solution #5: Court-circuit si session active

**PHASE 3** (Tests - 20 min):
- Tests manuels des 4 scénarios
- Vérification logs

---

**FIN DE L'ANALYSE**
