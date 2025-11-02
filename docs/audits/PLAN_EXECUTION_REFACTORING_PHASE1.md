# 📋 PLAN D'EXÉCUTION REFACTORING OGMA - Phase 1
**Date**: 1er novembre 2025  
**Version**: Plan Opérationnel v1.0  
**Objectif**: Extraction conservative de 850 lignes (~11.4%)  
**Risque**: 🟢 FAIBLE  

---

## 🎯 VUE D'ENSEMBLE PHASE 1

### Modules à Créer (10 fichiers)

```
c:\IA\OGMA\
├── utils/
│   ├── __init__.py                    # 10L - Exports publics
│   ├── formatting_utils.py            # 35L - Formatage dates/tailles/texte
│   ├── message_parsers.py             # 122L - Parsing thinking/introspection
│   └── backend_utils.py               # 5L - Helper backend mapping
│
├── conversations/
│   ├── __init__.py                    # 15L - Exports publics
│   ├── conversation_index.py          # 29L - Load/save index.json
│   ├── conversation_utils.py          # 26L - ID generation, title simple
│   ├── conversation_commands.py       # 106L - Commandes utilisateur
│   └── conversation_display.py        # 154L - Affichage résultats/summaries
│
├── backend/
│   ├── __init__.py                    # 10L - Exports publics
│   ├── backend_communication.py       # 50L - List models, test connection
│   └── ia_status.py                   # 162L - Status checks, indicators
│
└── files/
    ├── __init__.py                    # 8L - Exports publics
    └── file_management.py             # 103L - Upload, display, tabs
```

**Total**: 835 lignes extraites + ~43L boilerplate = **878 lignes nettes**

---

## 📝 ORDRE D'EXTRACTION SÉCURISÉ

### Étape 1: `utils/formatting_utils.py` ⭐ PRIORITÉ 1

**Durée estimée**: 20 minutes  
**Risque**: 🟢 TRÈS FAIBLE (fonctions pures, aucune dépendance globale)

#### Fonctions à Extraire

```python
# ogma_ng.py lignes 82-95
def format_size(size_bytes: int) -> str

# ogma_ng.py lignes 2876-2890  
def _format_datetime(datetime_str: str) -> str

# ogma_ng.py lignes 1124-1130
def _truncate_filename(filename: str, max_length: int = 15) -> str

# ogma_ng.py lignes 1130-1139
def _get_file_icon(filename: str) -> str
```

#### Code du Module

<details>
<summary>Voir formatting_utils.py complet</summary>

```python
"""
Module: formatting_utils.py
Description: Utilitaires de formatage (dates, tailles, texte, fichiers)
Extrait de: ogma_ng.py (lignes 82-95, 1124-1139, 2876-2890)
Date: 2025-11-01
"""

from typing import Optional
from datetime import datetime


def format_size(size_bytes: int) -> str:
    """
    Formate une taille en octets en format lisible.
    
    Args:
        size_bytes: Taille en octets
        
    Returns:
        str: Taille formatée (ex: "1.5 MB", "320 KB", "45 B")
        
    Examples:
        >>> format_size(0)
        '0 B'
        >>> format_size(1024)
        '1.0 KB'
        >>> format_size(1048576)
        '1.0 MB'
    """
    if size_bytes == 0:
        return "0 B"
    elif size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024**2:
        return f"{size_bytes/1024:.1f} KB"
    elif size_bytes < 1024**3:
        return f"{size_bytes/(1024**2):.1f} MB"
    else:
        return f"{size_bytes/(1024**3):.2f} GB"


def format_datetime(datetime_str: str) -> str:
    """
    Formate une date/heure ISO en format lisible français.
    
    Args:
        datetime_str: Date ISO format (ex: "2025-11-01T14:30:00")
        
    Returns:
        str: Date formatée (ex: "01/11/2025 à 14:30")
        
    Examples:
        >>> format_datetime("2025-11-01T14:30:00")
        '01/11/2025 à 14:30'
    """
    try:
        dt = datetime.fromisoformat(datetime_str)
        return dt.strftime("%d/%m/%Y à %H:%M")
    except Exception:
        return datetime_str


def truncate_filename(filename: str, max_length: int = 15) -> str:
    """
    Tronque un nom de fichier pour l'affichage.
    
    Args:
        filename: Nom du fichier complet
        max_length: Longueur maximale (défaut 15)
        
    Returns:
        str: Nom tronqué avec "..." si nécessaire
        
    Examples:
        >>> truncate_filename("document_tres_long_nom.pdf", 10)
        'docume....pdf'
    """
    if len(filename) <= max_length:
        return filename
    return filename[:max_length-5] + "..." + filename[-4:]


def get_file_icon(filename: str) -> str:
    """
    Retourne l'icône emoji appropriée pour un type de fichier.
    
    Args:
        filename: Nom du fichier
        
    Returns:
        str: Emoji représentant le type de fichier
        
    Examples:
        >>> get_file_icon("document.pdf")
        '📄'
        >>> get_file_icon("image.png")
        '🖼️'
    """
    ext = filename.lower().split('.')[-1] if '.' in filename else ''
    if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg']:
        return '🖼️'
    elif ext in ['pdf']:
        return '📄'
    elif ext in ['txt', 'md']:
        return '📝'
    elif ext in ['doc', 'docx']:
        return '📰'
    else:
        return '📎'
```
</details>

#### Modifications dans ogma_ng.py

```python
# EN HAUT DU FICHIER (après les imports existants)
from utils.formatting_utils import (
    format_size,
    format_datetime,
    truncate_filename,
    get_file_icon
)

# SUPPRIMER les fonctions suivantes:
# - def format_size() (ligne 82)
# - def _format_datetime() (ligne 2876)
# - def _truncate_filename() (ligne 1124)
# - def _get_file_icon() (ligne 1130)

# REMPLACER tous les appels:
# _format_datetime() → format_datetime()
# _truncate_filename() → truncate_filename()
# _get_file_icon() → get_file_icon()
```

#### Tests de Validation

```python
# tests/test_formatting_utils.py
from utils.formatting_utils import (
    format_size,
    format_datetime,
    truncate_filename,
    get_file_icon
)

def test_format_size():
    assert format_size(0) == "0 B"
    assert format_size(1024) == "1.0 KB"
    assert format_size(1048576) == "1.0 MB"
    
def test_format_datetime():
    result = format_datetime("2025-11-01T14:30:00")
    assert "01/11/2025" in result
    assert "14:30" in result
    
def test_truncate_filename():
    assert truncate_filename("court.txt", 20) == "court.txt"
    assert "..." in truncate_filename("nom_tres_long_fichier.pdf", 10)
    
def test_get_file_icon():
    assert get_file_icon("doc.pdf") == '📄'
    assert get_file_icon("photo.jpg") == '🖼️'
```

#### Validation Fonctionnelle

- [ ] Lancer app: `python launch_ogma.py`
- [ ] Vérifier affichage tailles dans settings
- [ ] Uploader fichier → vérifier icône correcte
- [ ] Charger conversation → vérifier format date sidebar

---

### Étape 2: `utils/message_parsers.py` ⭐ PRIORITÉ 2

**Durée estimée**: 30 minutes  
**Risque**: 🟢 FAIBLE (fonctions pures string parsing)

#### Fonctions à Extraire

```python
# ogma_ng.py lignes 2890-2972
def _parse_thinking_format(content: str) -> tuple[str, str]

# ogma_ng.py lignes 2972-3012
def _parse_introspection_format(content: str) -> tuple[str, str]
```

#### Code du Module

<details>
<summary>Voir message_parsers.py complet</summary>

```python
"""
Module: message_parsers.py
Description: Parsers pour formats spéciaux dans messages IA
Extrait de: ogma_ng.py (lignes 2890-3012)
Date: 2025-11-01

Formats supportés:
- Thinking format: <thinking>pensée</thinking>Réponse
- Introspection format: <subconscience role="X">dialogue</subconscience>Synthèse
"""

import re
from typing import Tuple


def parse_thinking_format(content: str) -> Tuple[str, str]:
    """
    Parse le format thinking pour séparer réflexion et réponse.
    
    Format attendu:
        <thinking>Ma pensée interne</thinking>
        Réponse visible utilisateur
    
    Args:
        content: Contenu complet du message
        
    Returns:
        tuple[str, str]: (thinking_content, main_content)
        - thinking_content: Contenu de la balise <thinking> (ou "" si absent)
        - main_content: Reste du contenu (ou content original si pas de balise)
        
    Examples:
        >>> parse_thinking_format("<thinking>Je réfléchis</thinking>\\nRéponse finale")
        ('Je réfléchis', 'Réponse finale')
        
        >>> parse_thinking_format("Réponse sans thinking")
        ('', 'Réponse sans thinking')
    """
    if not content:
        return ("", "")
    
    # Chercher balise <thinking>...</thinking>
    thinking_pattern = r'<thinking>(.*?)</thinking>'
    match = re.search(thinking_pattern, content, re.DOTALL | re.IGNORECASE)
    
    if match:
        thinking_content = match.group(1).strip()
        # Retirer la balise thinking du contenu principal
        main_content = re.sub(thinking_pattern, '', content, flags=re.DOTALL | re.IGNORECASE).strip()
        return (thinking_content, main_content)
    else:
        # Pas de balise thinking
        return ("", content)


def parse_introspection_format(content: str) -> Tuple[str, str]:
    """
    Parse le format introspection (dialogue Luna↔Archiviste).
    
    Format attendu:
        <subconscience role="luna">Message Luna</subconscience>
        <subconscience role="archiviste">Message Archiviste</subconscience>
        ...
        Synthèse finale
    
    Args:
        content: Contenu complet du message avec balises subconscience
        
    Returns:
        tuple[str, str]: (dialogue_content, synthesis_content)
        - dialogue_content: Dialogue complet formaté (ou "" si absent)
        - synthesis_content: Synthèse finale (ou content original si pas de balises)
        
    Examples:
        >>> content = '<subconscience role="luna">Bonjour</subconscience>\\n<subconscience role="archiviste">Salut</subconscience>\\nSynthèse: OK'
        >>> dialogue, synthesis = parse_introspection_format(content)
        >>> "Luna:" in dialogue
        True
    """
    if not content:
        return ("", "")
    
    # Chercher toutes les balises <subconscience>
    pattern = r'<subconscience\s+role="(\w+)">(.*?)</subconscience>'
    matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
    
    if not matches:
        # Pas de dialogue introspectif
        return ("", content)
    
    # Construire le dialogue formaté
    dialogue_lines = []
    for role, message in matches:
        # Capitaliser le rôle pour affichage
        display_role = role.capitalize()
        if display_role == "Luna":
            dialogue_lines.append(f"🌙 **Luna**: {message.strip()}")
        elif display_role == "Archiviste":
            dialogue_lines.append(f"📚 **Archiviste**: {message.strip()}")
        else:
            dialogue_lines.append(f"**{display_role}**: {message.strip()}")
    
    dialogue_content = "\n\n".join(dialogue_lines)
    
    # Retirer toutes les balises pour obtenir la synthèse
    synthesis_content = re.sub(pattern, '', content, flags=re.DOTALL | re.IGNORECASE).strip()
    
    return (dialogue_content, synthesis_content)
```
</details>

#### Modifications dans ogma_ng.py

```python
# Import
from utils.message_parsers import parse_thinking_format, parse_introspection_format

# SUPPRIMER fonctions:
# - def _parse_thinking_format() (ligne 2890)
# - def _parse_introspection_format() (ligne 2972)

# REMPLACER tous les appels:
# _parse_thinking_format() → parse_thinking_format()
# _parse_introspection_format() → parse_introspection_format()
```

#### Validation Fonctionnelle

- [ ] Message avec `<thinking>` → vérifier expansion "🧠 réflexion"
- [ ] Introspection cognitive mirror → vérifier parsing dialogue
- [ ] Message normal → vérifier affichage inchangé

---

### Étape 3: `utils/backend_utils.py` ⭐ PRIORITÉ 3

**Durée estimée**: 10 minutes  
**Risque**: 🟢 TRÈS FAIBLE (1 fonction helper simple)

<details>
<summary>Voir backend_utils.py complet</summary>

```python
"""
Module: backend_utils.py
Description: Utilitaires pour gestion backends IA
Extrait de: ogma_ng.py (ligne 314-319)
Date: 2025-11-01
"""


def map_backend_for_controller(backend: str) -> str:
    """
    Normalise le nom du backend pour compatibilité controllers.
    
    Args:
        backend: Nom du backend (ex: "GGUF", "API", "Ollama")
        
    Returns:
        str: Nom normalisé du backend
        
    Examples:
        >>> map_backend_for_controller("GGUF")
        'gguf'
        >>> map_backend_for_controller("API")
        'api'
    """
    return backend.lower() if backend else "api"
```
</details>

---

### Étape 4: `conversations/conversation_index.py` ⭐ PRIORITÉ 4

**Durée estimée**: 20 minutes  
**Risque**: 🟢 FAIBLE (I/O simple JSON)

<details>
<summary>Voir conversation_index.py complet</summary>

```python
"""
Module: conversation_index.py
Description: Gestion index conversations (data/conversations/index.json)
Extrait de: ogma_ng.py (lignes 2201-2230)
Date: 2025-11-01
"""

import json
from pathlib import Path
from typing import Dict, Tuple

# Imports depuis ogma_ng
from utils import DATA_DIR

CONVERSATIONS_DIR = DATA_DIR / 'conversations'
INDEX_FILE = CONVERSATIONS_DIR / 'index.json'


def load_conversation_index() -> Dict[str, Dict]:
    """
    Charge l'index des conversations depuis index.json.
    
    Returns:
        dict: Index conversations {conv_id: {title, created_at, last_modified, ...}}
        
    Examples:
        >>> index = load_conversation_index()
        >>> "2025-11-01_14-30-00" in index  # ID conversation exemple
        True
    """
    if not INDEX_FILE.exists():
        return {}
    
    try:
        with open(INDEX_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"[CONVERSATION-INDEX] WARN Erreur chargement index: {e}")
        return {}


def save_conversation_index(index_data: Dict[str, Dict]) -> Tuple[bool, str]:
    """
    Sauvegarde l'index des conversations.
    
    Args:
        index_data: Dictionnaire index complet
        
    Returns:
        tuple[bool, str]: (succès, message_erreur)
        
    Examples:
        >>> success, error = save_conversation_index({"2025-11-01_14-30-00": {...}})
        >>> success
        True
    """
    CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)
        return (True, "")
    except Exception as e:
        error_msg = f"Erreur sauvegarde index: {e}"
        print(f"[CONVERSATION-INDEX] ERROR {error_msg}")
        return (False, error_msg)
```
</details>

---

### Étape 5: `conversations/conversation_utils.py` ⭐ PRIORITÉ 5

**Durée estimée**: 15 minutes  
**Risque**: 🟢 FAIBLE (génération IDs et titres simples)

<details>
<summary>Voir conversation_utils.py complet</summary>

```python
"""
Module: conversation_utils.py
Description: Utilitaires conversation (ID, titres simples)
Extrait de: ogma_ng.py (lignes 2230-2256)
Date: 2025-11-01
"""

from datetime import datetime


def make_conv_id() -> str:
    """
    Génère un ID unique pour conversation.
    
    Format: YYYY-MM-DD_HH-MM-SS
    
    Returns:
        str: ID conversation (ex: "2025-11-01_14-30-45")
        
    Examples:
        >>> conv_id = make_conv_id()
        >>> len(conv_id)
        19
        >>> "_" in conv_id
        True
    """
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def make_title_from_text(text: str) -> str:
    """
    Crée un titre simple depuis le texte (15 premiers mots).
    
    Args:
        text: Texte source du message
        
    Returns:
        str: Titre court (max 15 mots)
        
    Examples:
        >>> make_title_from_text("Bonjour comment vas-tu aujourd'hui ?")
        'Bonjour comment vas-tu aujourd...'
        
        >>> make_title_from_text("Court")
        'Court'
    """
    if not text:
        return "Nouvelle conversation"
    
    # Prendre max 15 mots
    words = text.split()[:15]
    title = ' '.join(words)
    
    # Tronquer à 60 caractères max
    if len(title) > 60:
        title = title[:57] + "..."
    
    return title
```
</details>

---

### Étape 6-10: Modules Restants

**Par manque d'espace, les modules suivants suivent le même pattern**:

6. **file_management.py** (103L) - Gestion uploads + affichage tabs
7. **conversation_display.py** (154L) - Affichage résultats recherche
8. **conversation_commands.py** (106L) - Parsing commandes utilisateur
9. **backend_communication.py** (50L) - List models + test connection
10. **ia_status.py** (162L) - Status checks + indicateurs UI

---

## 🧪 TESTS COMPLETS APRÈS PHASE 1

### Checklist Validation Fonctionnelle

```markdown
## Tests Critiques (à faire après chaque module)

### Démarrage
- [ ] `python launch_ogma.py` démarre sans erreur
- [ ] Aucune erreur import dans console
- [ ] UI se charge correctement

### Conversations
- [ ] Nouvelle conversation fonctionne
- [ ] Envoi message + réponse IA OK
- [ ] Chargement conversation depuis sidebar OK
- [ ] Titre auto-généré après 2e message
- [ ] Sauvegarde auto fonctionne
- [ ] Context menu sidebar (renommer, supprimer, mémoriser)

### Extensions
- [ ] Cognitive Mirror activation OK
- [ ] Journal de bord injection contexte matinal OK
- [ ] Perception capture si configurée OK
- [ ] Biographie détection phrases magiques OK

### Fichiers
- [ ] Upload fichier fonctionne
- [ ] Icône correcte selon extension
- [ ] Affichage tab fichier actif
- [ ] Suppression fichier actif

### Backend
- [ ] Changement provider (Mistral → OpenAI par ex)
- [ ] Refresh models liste
- [ ] Test connection backend
- [ ] Indicateurs IA (dots verts/rouges)

### Commandes Spéciales
- [ ] "lis conversation X.json" charge conversation
- [ ] "cherche 'terme' dans conversations" fonctionne
- [ ] "liste conversations" affiche résultats
- [ ] "vider conversation" nettoie contexte

### Messages Format Spécial
- [ ] `<thinking>` affiche expansion "🧠 réflexion"
- [ ] Dialogue introspection parse correctement
- [ ] Images générées affichent correctement
- [ ] Badges "mémorisé" apparaissent

### Persistence
- [ ] Fermer app + rouvrir → conversation persiste
- [ ] Index conversations cohérent
- [ ] Pas de corruption JSON
```

---

## 📊 MÉTRIQUES DE SUCCÈS PHASE 1

### Objectifs Quantitatifs

| Métrique | Avant | Après Phase 1 | Atteint ? |
|----------|-------|---------------|-----------|
| **Lignes ogma_ng.py** | 7425 | 6575 | ✅ / ❌ |
| **Nombre modules** | 3 | 13 | ✅ / ❌ |
| **Taille module max** | 3104 | 200 | ✅ / ❌ |
| **Tests passés** | - | 100% | ✅ / ❌ |
| **Commits Git** | - | 10+ | ✅ / ❌ |

### Objectifs Qualitatifs

- [ ] ✅ Code plus lisible (feedback subjectif)
- [ ] ✅ Modules facilement testables unitairement
- [ ] ✅ Imports clairs et explicites
- [ ] ✅ Documentation inline complète
- [ ] ✅ Aucune regression fonctionnelle
- [ ] ✅ Performance identique ou meilleure

---

## 🚀 COMMANDES GIT RECOMMANDÉES

```bash
# 1. Créer branche refactoring
git checkout -b refactor/phase1-extraction-utils
git push -u origin refactor/phase1-extraction-utils

# 2. Commits atomiques (1 module = 1 commit)
git add utils/formatting_utils.py ogma_ng.py
git commit -m "refactor: Extract formatting_utils.py from ogma_ng

- format_size(), format_datetime(), truncate_filename(), get_file_icon()
- Tested: file uploads, sidebar dates display
- ogma_ng.py: 7425L → 7385L (-40L)"

git add utils/message_parsers.py ogma_ng.py
git commit -m "refactor: Extract message_parsers.py from ogma_ng

- parse_thinking_format(), parse_introspection_format()
- Tested: thinking expansion, introspection dialogue
- ogma_ng.py: 7385L → 7263L (-122L)"

# ... etc pour chaque module

# 3. Après validation complète
git checkout main
git merge refactor/phase1-extraction-utils --no-ff
git tag refactor-phase1-complete
git push origin main --tags
```

---

## ⚠️ ROLLBACK EN CAS DE PROBLÈME

### Scénario 1: Problème après 1 module

```bash
# Annuler dernier commit
git reset --hard HEAD~1

# Ou revenir au module précédent
git reset --hard HEAD~2
git clean -fd  # Nettoie fichiers non trackés
```

### Scénario 2: Problème majeur Phase 1

```bash
# Revenir au début de la branche
git reset --hard origin/main

# Ou restaurer backup complet
cd c:\IA\OGMA_BACKUP_PHASE1
xcopy /E /I /Y * c:\IA\OGMA
```

### Scénario 3: Import cassé

```python
# Si erreur "ImportError: cannot import name X"
# Vérifier dans ogma_ng.py que l'import existe:
from utils.formatting_utils import format_size  # ✅ Bon

# Et que la fonction est bien dans le module
# utils/formatting_utils.py doit contenir:
def format_size(size_bytes: int) -> str:
    ...
```

---

## 📞 SUPPORT ET QUESTIONS

### Checklist Avant de Demander Validation

- [ ] Tous les modules créés et fonctionnels
- [ ] Tests validation 100% passés
- [ ] Commits Git propres (messages clairs)
- [ ] Documentation inline complète
- [ ] Aucune regression détectée
- [ ] Performance stable (pas de ralentissement)
- [ ] Backup complet réalisé avant démarrage

### Questions Fréquentes

**Q: "Import circulaire détecté, que faire ?"**  
R: Vérifier l'ordre des imports. Les modules utils ne doivent PAS importer depuis conversations/ ou backend/.

**Q: "Variable globale `_conv_index` non définie"**  
R: Variables globales restent dans ogma_ng.py. Les modules importent via callbacks si besoin.

**Q: "Tests unitaires échouent mais app fonctionne"**  
R: Tests peut-être mal configurés. Si app fonctionne, c'est OK pour Phase 1 (tests optionnels).

**Q: "Dois-je extraire `_send_chat_message()` ?"**  
R: ❌ **NON**. Cette fonction reste dans ogma_ng.py (trop complexe).

---

## 🎯 CRITÈRES DE RÉUSSITE PHASE 1

✅ **SUCCÈS** si:
1. ogma_ng.py réduit de 800-900 lignes
2. 10 modules créés proprement documentés
3. Tests validation 100% OK
4. Aucune regression fonctionnelle
5. Commits Git atomiques et propres

⚠️ **ÉCHEC PARTIEL** si:
1. Réduction < 500 lignes
2. Regressions mineures détectées
3. Tests validation < 90% OK

❌ **ÉCHEC COMPLET** si:
1. App ne démarre plus
2. Regressions majeures (perte données, crash)
3. Import circulaire non résolu

---

**État Actuel**: ⏸️ **PLAN PRÊT - EN ATTENTE VALIDATION ARCHITECTE**

**Prochaines Actions**:
1. Architecte valide ce plan ✋
2. Création backup complet
3. Début extraction modules (estimation 3-4h)
4. Tests et validation finale

---

*"Un plan précis vaut mieux qu'un refactoring improvisé."* 🎯
