# 🗑️ DÉSINSTALLATION DEBUG_TOKEN_TRACKING

## 📋 Checklist Rapide

Pour supprimer complètement le système de logging Archiviste :

### ✅ Étape 1: Supprimer les marqueurs dans core_logic.py

**Fichier**: `core_logic.py`

**Lignes à supprimer** (chercher `DEBUG_TOKEN_TRACKING`) :

1. **Imports (lignes ~17-28)** :
```python
# ╔═══════════════════════════════════════════════════════════════════════╗
# ║  🔬 DEBUG_TOKEN_TRACKING - TEMPORAIRE - SUPPRIMER APRÈS ANALYSE      ║
# ╚═══════════════════════════════════════════════════════════════════════╝
try:
    from archiviste_logger import get_archiviste_logger
    ARCHIVISTE_LOGGING_ENABLED = True
    print("[DEBUG-TOKEN] ✅ Logging Archiviste activé")
except ImportError:
    ARCHIVISTE_LOGGING_ENABLED = False
    print("[DEBUG-TOKEN] ⚠️ archiviste_logger.py introuvable")
# ╚═══════════════════════════════════════════════════════════════════════╝
```

2. **AIController init (lignes ~1418)** :
```python
        # ═══ DEBUG_TOKEN_TRACKING ═══
        self._is_archiviste = False
        self._controller_name = ai_type
        # ═══════════════════════════════════════
```

3. **call_chat_api logging (lignes ~1628)** :
```python
        # ╔═══════════════════════════════════════════════════════════════════╗
        # ║  🔬 DEBUG_TOKEN_TRACKING - LOG ARCHIVISTE                         ║
        # ╚═══════════════════════════════════════════════════════════════════╝
        if ARCHIVISTE_LOGGING_ENABLED and self._is_archiviste and response:
            try:
                logger = get_archiviste_logger()
                logger.log_call(
                    source=log_source,
                    input_messages=messages,
                    output_response=response,
                    metadata={
                        "controller": self._controller_name,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "backend": self.backend_type
                    }
                )
            except Exception as log_err:
                print(f"[DEBUG-TOKEN] ⚠️ Erreur logging: {log_err}")
        # ╚═══════════════════════════════════════════════════════════════════╝
```

4. **Retirer paramètre `log_source`** de la signature `call_chat_api` :
```python
# AVANT
async def call_chat_api(self, messages: List[Dict], max_tokens: int, context_length: int, temperature: float, is_json: bool = True, log_source: str = "unknown") -> tuple[Optional[str], Optional[str]]:

# APRÈS  
async def call_chat_api(self, messages: List[Dict], max_tokens: int, context_length: int, temperature: float, is_json: bool = True) -> tuple[Optional[str], Optional[str]]:
```

---

### ✅ Étape 2: Nettoyer memory_manager.py

**Fichier**: `memory_manager.py`

**Chercher et supprimer** tous les blocs :
```python
# ═══ DEBUG_TOKEN_TRACKING ═══
...
# ═══════════════════════════════
```

Et **retirer le paramètre** `log_source=...` de tous les appels `self.archiviste.call_chat_api()`.

**Exemple** :
```python
# AVANT
response, error = await self.archiviste.call_chat_api(
    messages=messages,
    max_tokens=300,
    context_length=self.archiviste.context_length,
    temperature=0.3,
    is_json=True,
    log_source="semantic_analysis"  # 🔬 TRACKING
)

# APRÈS
response, error = await self.archiviste.call_chat_api(
    messages=messages,
    max_tokens=300,
    context_length=self.archiviste.context_length,
    temperature=0.3,
    is_json=True
)
```

**4 occurrences à modifier** :
- Ligne ~1216 : `semantic_analysis`
- Ligne ~1339 : `memory_enrichment`
- Ligne ~1888 : `memory_synthesis`
- Ligne ~1961 : `detailed_synthesis`
- Ligne ~2644 : `full_synthesis`

---

### ✅ Étape 3: Nettoyer ego_selector.py

**Fichier**: `ego_selector.py`

**Ligne ~150** - Retirer bloc DEBUG_TOKEN_TRACKING et paramètre `log_source`:
```python
# AVANT
# ═══ DEBUG_TOKEN_TRACKING ═══
response, error = await self.archiviste.call_chat_api(
    messages=messages,
    max_tokens=400,
    context_length=20000,
    temperature=0.3,
    is_json=True,
    log_source="ego_selection"  # 🔬 TRACKING
)
# ═══════════════════════════════

# APRÈS
response, error = await self.archiviste.call_chat_api(
    messages=messages,
    max_tokens=400,
    context_length=20000,
    temperature=0.3,
    is_json=True
)
```

---

### ✅ Étape 4: Nettoyer extensions/capability_advisor/advisor_core.py

**Fichier**: `extensions/capability_advisor/advisor_core.py`

**Ligne ~85** - Même opération:
```python
# AVANT
# ═══ DEBUG_TOKEN_TRACKING ═══
response, error = await self.archiviste_controller.call_chat_api(
    messages=messages,
    max_tokens=self.config.config.get('max_tokens', 500),
    context_length=self.archiviste_controller.context_length,
    temperature=self.config.config.get('temperature', 0.3),
    is_json=True,
    log_source="capability_advisor"  # 🔬 TRACKING
)
# ═══════════════════════════════

# APRÈS
response, error = await self.archiviste_controller.call_chat_api(
    messages=messages,
    max_tokens=self.config.config.get('max_tokens', 500),
    context_length=self.archiviste_controller.context_length,
    temperature=self.config.config.get('temperature', 0.3),
    is_json=True
)
```

---

### ✅ Étape 5: Nettoyer extensions/cognitive_mirror/

**2 fichiers à modifier** :

#### **5a. introspection_orchestrator.py**

**Ligne ~500**:
```python
# AVANT
# ═══ DEBUG_TOKEN_TRACKING ═══
response, error = await self.archiviste_controller.call_chat_api(
    messages=messages,
    max_tokens=max_tokens,
    context_length=8192,
    temperature=0.7,
    is_json=False,
    log_source="introspection_dialogue"  # 🔬 TRACKING
)
# ═══════════════════════════════

# APRÈS
response, error = await self.archiviste_controller.call_chat_api(
    messages=messages,
    max_tokens=max_tokens,
    context_length=8192,
    temperature=0.7,
    is_json=False
)
```

#### **5b. subconscience_orchestrator.py**

**Ligne ~387**:
```python
# AVANT
# ═══ DEBUG_TOKEN_TRACKING ═══
response_content, error = await self.archiviste_controller.call_chat_api(
    messages=messages,
    max_tokens=max_tokens,
    context_length=4096,
    temperature=0.7,
    log_source="subconscience_archiviste"  # 🔬 TRACKING
)
# ═══════════════════════════════

# APRÈS
response_content, error = await self.archiviste_controller.call_chat_api(
    messages=messages,
    max_tokens=max_tokens,
    context_length=4096,
    temperature=0.7
)
```

---

### ✅ Étape 6: Nettoyer modules/ogma_core/controllers.py

**Fichier**: `modules/ogma_core/controllers.py`

**Ligne ~143**:
```python
# AVANT
g._archiviste_controller = AIController(
    'archiviste', 
    cast(OllamaManager, g._ollama_mgr), 
    cast(GGUFManager, g._gguf_mgr), 
    cast(KoboldManager, g._kobold_mgr)
)
# ═══ DEBUG_TOKEN_TRACKING ═══
g._archiviste_controller._is_archiviste = True  # 🔬 FLAG LOGGING
# ═══════════════════════════════
arch = sm.settings.get('reasoning_api', {})

# APRÈS
g._archiviste_controller = AIController(
    'archiviste', 
    cast(OllamaManager, g._ollama_mgr), 
    cast(GGUFManager, g._gguf_mgr), 
    cast(KoboldManager, g._kobold_mgr)
)
arch = sm.settings.get('reasoning_api', {})
```

---

### ✅ Étape 7: Supprimer les fichiers temporaires

```bash
# Dans PowerShell
cd c:\IA\OGMA
Remove-Item archiviste_logger.py
Remove-Item PATCH_ARCHIVISTE_LOGGING.md
Remove-Item generate_archiviste_report.py
Remove-Item DESINSTALLER_DEBUG_TOKENS.md
Remove-Item data\archiviste_monitoring.json -ErrorAction SilentlyContinue
```

---

## 🎯 Vérification Finale

Rechercher dans tout le projet s'il reste des traces :

```bash
# PowerShell
cd c:\IA\OGMA
Select-String -Path *.py -Pattern "DEBUG_TOKEN_TRACKING" -Recurse
Select-String -Path *.py -Pattern "log_source" -Recurse
Select-String -Path *.py -Pattern "archiviste_logger" -Recurse
```

Si aucun résultat → ✅ **Désinstallation complète réussie !**

---

## 💾 Conservation des Résultats

**Avant de désinstaller**, sauvegarder le rapport si utile :

```bash
Copy-Item data\archiviste_monitoring.json data\RAPPORT_TOKENS_FINAL.json
```

Le rapport contient les vraies données de consommation pour optimisations futures.

---

## ⚡ Script Auto-Désinstall (Optionnel)

Créer `remove_debug_tokens.py` :

```python
import re
from pathlib import Path

files_to_clean = [
    "core_logic.py",
    "memory_manager.py", 
    "ego_selector.py",
    "extensions/capability_advisor/advisor_core.py",
    "extensions/cognitive_mirror/introspection_orchestrator.py",
    "extensions/cognitive_mirror/subconscience_orchestrator.py",
    "modules/ogma_core/controllers.py"
]

for file_path in files_to_clean:
    p = Path(file_path)
    if not p.exists():
        continue
    
    content = p.read_text(encoding='utf-8')
    
    # Retirer blocs DEBUG_TOKEN_TRACKING
    content = re.sub(r'# ═══ DEBUG_TOKEN_TRACKING ═══.*?# ═══════════════════════════════', '', content, flags=re.DOTALL)
    content = re.sub(r'# ╔═══.*?DEBUG_TOKEN_TRACKING.*?╝\n.*?# ╚═══.*?╝', '', content, flags=re.DOTALL)
    
    # Retirer paramètre log_source
    content = re.sub(r',\s*log_source=["\'][^"\']*["\']', '', content)
    content = re.sub(r'log_source:\s*str\s*=\s*["\'][^"\']*["\'],?\s*', '', content)
    
    p.write_text(content, encoding='utf-8')
    print(f"✅ Nettoyé: {file_path}")

print("\n✅ Désinstallation automatique terminée!")
```

Lancer : `python remove_debug_tokens.py`

---

**Durée estimée désinstallation manuelle** : 5-10 minutes  
**Durée estimée désinstallation auto** : 30 secondes
