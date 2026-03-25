# 🔧 PATCH - Activation Logging Archiviste

## 📋 Instructions d'Installation

### Étape 1: Modifier `core_logic.py`

Ajouter en haut du fichier (après les imports):

```python
# ============ ARCHIVISTE LOGGING (TEMPORAIRE DEBUG) ============
try:
    from archiviste_logger import get_archiviste_logger
    ARCHIVISTE_LOGGING_ENABLED = True
except ImportError:
    ARCHIVISTE_LOGGING_ENABLED = False
# ================================================================
```

### Étape 2: Instrumenter la méthode Archiviste

Trouver la méthode `call_chat_api` utilisée par l'Archiviste controller (probablement ligne ~200-300).

**AVANT** (exemple):
```python
def call_chat_api(self, messages, temperature=0.7, max_tokens=None):
    # ... code existant ...
    response = self._send_to_api(messages, temperature, max_tokens)
    return response
```

**APRÈS** (avec logging):
```python
def call_chat_api(self, messages, temperature=0.7, max_tokens=None, log_source="unknown"):
    # ... code existant ...
    response = self._send_to_api(messages, temperature, max_tokens)
    
    # ============ ARCHIVISTE LOGGING ============
    if ARCHIVISTE_LOGGING_ENABLED and hasattr(self, '_is_archiviste') and self._is_archiviste:
        logger = get_archiviste_logger()
        logger.log_call(
            source=log_source,
            input_messages=messages,
            output_response=str(response),
            metadata={
                "temperature": temperature,
                "max_tokens": max_tokens,
                "model": getattr(self, 'model', 'unknown')
            }
        )
    # ============================================
    
    return response
```

### Étape 3: Ajouter flag `_is_archiviste` au controller

Dans l'initialisation du controller Archiviste (probablement dans `ogma_ng.py` ou `core_logic.py`):

```python
# Lors de la création du controller Archiviste
archiviste_controller = ChatController(...)
archiviste_controller._is_archiviste = True  # FLAG pour identification
```

### Étape 4: Passer `log_source` dans les appels

Modifier les appels existants pour passer la source:

**Dans `memory_manager.py`**:
```python
# Ligne ~1800 (semantic analysis)
response = self.archiviste_controller.call_chat_api(
    messages, 
    temperature=0.3,
    log_source="semantic_analysis"  # AJOUTER
)

# Ligne ~1900 (memory synthesis)
response = self.archiviste_controller.call_chat_api(
    messages,
    temperature=0.3,
    log_source="memory_synthesis"  # AJOUTER
)
```

**Dans `temporal_injector.py`**:
```python
response = archiviste_controller.call_chat_api(
    messages,
    temperature=0.3,
    log_source="temporal_analysis"  # AJOUTER
)
```

**Dans `extensions/capability_advisor/advisor_core.py`**:
```python
response = self.archiviste_controller.call_chat_api(
    messages,
    temperature=0.3,
    log_source="capability_advisor"  # AJOUTER
)
```

**Dans `extensions/cognitive_mirror/`**:
```python
response = archiviste_controller.call_chat_api(
    messages,
    temperature=0.5,
    log_source="introspection_dialogue"  # AJOUTER
)
```

**Dans `extensions/journal_de_bord/entry_generator.py`**:
```python
response = self._call_archiviste(
    prompt,
    log_source="journal_generation"  # AJOUTER si méthode modifiée
)
```

---

## 🚀 Utilisation

### Démarrer une session de monitoring

1. **Lancer OGMA normalement**
   ```bash
   python launch_ogma.py
   ```

2. **Le logging est automatiquement activé** (si patch appliqué)

3. **Faire 10-20 messages test** avec Luna pour collecter données réelles

4. **Vérifier logs en temps réel** dans la console:
   ```
   [ARCHIVISTE-LOG] semantic_analysis: 845 IN + 156 OUT = 1001 tokens
   [ARCHIVISTE-LOG] memory_synthesis: 2340 IN + 298 OUT = 2638 tokens
   [ARCHIVISTE-LOG] temporal_analysis: 956 IN + 142 OUT = 1098 tokens
   [ARCHIVISTE-LOG] capability_advisor: 1050 IN + 201 OUT = 1251 tokens
   ```

5. **Arrêter OGMA** (Ctrl+C ou fermer proprement)

6. **Générer rapport final**:
   ```bash
   python -c "from archiviste_logger import save_and_print_report; save_and_print_report()"
   ```

### Désactiver temporairement

Dans la console Python d'OGMA:
```python
from archiviste_logger import disable_logging
disable_logging()
```

Réactiver:
```python
from archiviste_logger import enable_logging
enable_logging()
```

---

## 📊 Rapport Généré

Le fichier `data/archiviste_monitoring.json` contiendra:

```json
{
  "summary": {
    "session_duration_minutes": 15.3,
    "total_calls": 48,
    "total_input_tokens": 98450,
    "total_output_tokens": 12300,
    "total_tokens": 110750,
    "avg_tokens_per_call": 2307,
    "ratio_input_output": 8.0,
    "by_source": {
      "semantic_analysis": {"count": 12, "input_tokens": 9840, "output_tokens": 1850},
      "memory_synthesis": {"count": 12, "input_tokens": 28450, "output_tokens": 3580},
      "temporal_analysis": {"count": 12, "input_tokens": 11520, "output_tokens": 1700},
      "capability_advisor": {"count": 12, "input_tokens": 12600, "output_tokens": 2400},
      ...
    },
    "top_consumers": [
      ["memory_synthesis", {"count": 12, "input_tokens": 28450, "output_tokens": 3580}],
      ...
    ]
  },
  "detailed_calls": [...]
}
```

---

## ⚠️ Important

1. **Ce patch est TEMPORAIRE** - pour diagnostic uniquement
2. **Supprimer après analyse** (impact minime perf mais inutile long terme)
3. **Les estimations sont approximatives** (4 chars = 1 token)
4. **Comparer avec dashboard GROK** pour validation

---

## 🔄 Désinstallation

1. Retirer les lignes `# ============ ARCHIVISTE LOGGING ============`
2. Supprimer imports `archiviste_logger`
3. Retirer paramètre `log_source` des appels
4. Optionnel: Supprimer `archiviste_logger.py`

---

## 🎯 Objectif

Obtenir **données réelles** pour:
- ✅ Confirmer estimations théoriques
- ✅ Identifier vrais top consommateurs
- ✅ Mesurer ratio INPUT/OUTPUT réel
- ✅ Valider hypothèses (historique complet? texte_original long?)
- ✅ Prioriser optimisations à fort impact

**Durée test recommandée**: 1-2 heures d'usage normal (10-20 messages)
