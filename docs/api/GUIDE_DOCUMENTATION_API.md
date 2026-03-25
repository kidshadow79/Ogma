# 📚 GUIDE : Documenter l'API Memory Manager

**Objectif** : Extraire et documenter toutes les signatures de méthodes publiques de `MemoryManager` pour permettre la création de tests stricts fiables.

---

## 🎯 Étape 1 : Extraction Automatique

### Commande PowerShell

```powershell
# Extraire toutes les définitions de méthodes
Select-String -Path "memory_manager.py" -Pattern "^\s*(async )?def [^_]" -CaseInsensitive | 
    ForEach-Object { $_.Line } > docs/api/MEMORY_MANAGER_SIGNATURES.txt

# Extraire le schéma SQLite complet
Select-String -Path "memory_manager.py" -Pattern "CREATE TABLE" -Context 0,40 |
    Out-File docs/api/MEMORY_MANAGER_SCHEMA.txt
```

### Méthodes à Documenter (Priorité)

**CRITIQUE** (nécessaires pour tests stricts) :
- [ ] `__init__(...)` - Initialisation
- [ ] `add_memory(...)` - ✅ DÉJÀ DOCUMENTÉ
- [ ] `search_memories(...)` - ⚠️ SIGNATURE INCONNUE
- [ ] `update_memory(...)` - ⚠️ SIGNATURE INCONNUE
- [ ] `delete_memory(...)` - ⚠️ ASYNC/SYNC INCONNU
- [ ] `get_memory_by_id(...)` - Signature à vérifier
- [ ] `get_all_memories(...)` - Signature à vérifier
- [ ] `get_memory_count(...)` - Signature à vérifier

**IMPORTANT** (pour tests avancés) :
- [ ] `rebuild_faiss_index(...)` - Reconstruction index
- [ ] `cleanup(...)` - Nettoyage ressources
- [ ] `_search_fts5(...)` - Méthode interne (documenter quand même)
- [ ] `_search_faiss(...)` - Méthode interne

**OPTIONNEL** (backup/restore si existent) :
- [ ] `create_backup(...)` - ⚠️ INEXISTANT ?
- [ ] `restore_from_backup(...)` - ⚠️ INEXISTANT ?
- [ ] `export_memories(...)` - Alternative backup ?

---

## 📝 Étape 2 : Template Documentation

Pour **chaque méthode**, documenter dans `docs/api/MEMORY_MANAGER_API.md` :

### Format Standard

```markdown
### `add_memory()`

**Signature** :
```python
async def add_memory(
    self,
    memory_id: str,
    text_brut: str,
    chat_controller=None,
    conversation_context: str = "",
    interlocutor: str = ""
) -> bool
```

**Description** : Ajoute un nouveau souvenir en base SQLite + index FAISS.

**Paramètres** :
- `memory_id` (str, requis) : Identifiant unique du souvenir
- `text_brut` (str, requis) : Texte original à mémoriser
- `chat_controller` (AIController, optionnel) : Contrôleur IA pour contexte
- `conversation_context` (str, optionnel) : Contexte conversationnel
- `interlocutor` (str, optionnel) : Nom de l'interlocuteur

**Retour** :
- `bool` : `True` si ajout réussi, `False` sinon

**Comportement** :
1. Appelle Archiviste pour enrichissement (génère title/summary/valence)
2. Génère embedding via `embedding_ia.create_embedding()`
3. Stocke en base SQLite (table `memories`)
4. Ajoute vecteur à index FAISS
5. Sauvegarde index FAISS sur disque

**Exceptions** :
- Aucune levée (gestion interne, retourne `False` en cas d'erreur)

**Exemple** :
```python
success = await memory_manager.add_memory(
    memory_id="MSG-001",
    text_brut="Discussion importante sur l'architecture"
)
print(f"Ajout: {'✅' if success else '❌'}")
```

**Tests Associés** :
- `test_add_memory_persists_to_database` ✅
- `test_add_memory_generates_valid_embedding` ✅
```

---

## 🔍 Étape 3 : Reverse-Engineering Rapide

### Pour `search_memories()`

```bash
# Trouver la signature
grep -A 20 "async def search_memories\|def search_memories" memory_manager.py

# Trouver tous les appels dans le code (exemples d'usage)
grep -r "search_memories(" --include="*.py" | head -20
```

**À documenter** :
- Nom du paramètre query (`query_text` ? `query` ? `search_query` ?)
- Limite résultats (`limit` ? `k` ? `max_results` ?)
- Mode recherche (`mode` existe ? `"hybrid"/"faiss"/"fts5"` ?)
- Filtrage (`threshold` ? `filters` ? `min_score` ?)
- Retour (liste de dict ? objets Memory ? format JSON ?)

### Pour `update_memory()`

```bash
grep -A 15 "async def update_memory\|def update_memory" memory_manager.py
```

**À documenter** :
- Quels champs sont modifiables ? (title/summary/tags/valence ?)
- Paramètres acceptés (dict metadata ? kwargs ?)
- Comportement re-embedding (recalculé ou conservé ?)
- Retour (bool ? dict updated ? None ?)

### Pour `delete_memory()`

```bash
grep -A 10 "async def delete_memory\|def delete_memory" memory_manager.py
```

**À documenter** :
- Async ou sync ?
- Suppression cascade (FAISS + SQLite) ?
- Soft delete ou hard delete ?
- Retour (bool success ?)

---

## 🧪 Étape 4 : Validation par Tests

Pour **chaque méthode documentée**, créer un **micro-test de validation** :

```python
# tests/api_validation/test_search_memories_signature.py

def test_search_memories_accepts_query_text():
    """Valide que search_memories accepte query_text comme paramètre."""
    from memory_manager import MemoryManager
    import inspect
    
    sig = inspect.signature(MemoryManager.search_memories)
    params = list(sig.parameters.keys())
    
    # Validation stricte de la signature
    assert 'query_text' in params, f"Paramètre attendu: 'query_text', trouvé: {params}"
    assert 'limit' in params or 'k' in params, "Paramètre limite manquant"
    
    print(f"✅ Signature validée: {sig}")
```

---

## 📊 Étape 5 : Tableau de Suivi

Créer `docs/api/DOCUMENTATION_PROGRESS.md` :

```markdown
| Méthode | Signature Extraite | Paramètres Documentés | Retour Documenté | Exemple Créé | Test Validé |
|---------|--------------------|-----------------------|------------------|--------------|-------------|
| `add_memory` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `search_memories` | ⏳ | ❌ | ❌ | ❌ | ❌ |
| `update_memory` | ❌ | ❌ | ❌ | ❌ | ❌ |
| `delete_memory` | ❌ | ❌ | ❌ | ❌ | ❌ |
| ... | ... | ... | ... | ... | ... |
```

---

## ⚡ Étape 6 : Génération Auto (Bonus)

Si tu veux automatiser, utilise ce script :

```python
# scripts/generate_api_doc.py

import ast
import inspect
from pathlib import Path

def extract_function_signatures(file_path):
    """Extrait toutes les signatures de fonctions d'un fichier Python."""
    with open(file_path, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read())
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Filtrer méthodes publiques (pas _private)
            if not node.name.startswith('_'):
                args = [arg.arg for arg in node.args.args]
                defaults = [ast.unparse(d) for d in node.args.defaults]
                
                print(f"\n### `{node.name}()`\n")
                print(f"**Paramètres** : {', '.join(args)}")
                print(f"**Async** : {'✅' if isinstance(node, ast.AsyncFunctionDef) else '❌'}")

if __name__ == "__main__":
    extract_function_signatures("memory_manager.py")
```

---

## 🎯 Objectif Final

**Créer `docs/api/MEMORY_MANAGER_API.md`** avec :

```markdown
# Memory Manager - API Reference

## Table des Matières
1. [Initialisation](#initialisation)
2. [Création Mémoires](#création-mémoires)
3. [Recherche](#recherche)
4. [Mise à Jour](#mise-à-jour)
5. [Suppression](#suppression)
6. [Statistiques](#statistiques)
7. [Backup/Restore](#backup-restore)
8. [Maintenance](#maintenance)

---

## Initialisation

### `__init__(...)`
[Documentation complète]

## Création Mémoires

### `add_memory(...)`
[Documentation complète avec exemple]

## Recherche

### `search_memories(...)`
⚠️ **SIGNATURE À DOCUMENTER**

Hypothèses actuelles (à valider) :
- Paramètre query : `query_text` ?
- Limite : `limit` ou `k` ?
- Mode : `mode="hybrid"` supporté ?

[TODO: Extraire signature réelle]

...
```

---

## ⏱️ Temps Estimé

- **Extraction automatique** : 10 minutes
- **Documentation manuelle** : 2-4 heures (8 méthodes critiques)
- **Validation tests** : 1-2 heures
- **Total** : **4-7 heures**

Une fois terminé, les **tests stricts pourront être adaptés** et atteindre **80%+ de succès**.

---

## 📋 Checklist Finale

**Avant de commencer les tests stricts** :

- [ ] Toutes signatures extraites
- [ ] 8 méthodes critiques documentées
- [ ] Schéma SQLite complet documenté
- [ ] Exemples d'usage pour chaque méthode
- [ ] Tests de validation signature créés
- [ ] Documentation validée par essai réel

**Critère de succès** : Pouvoir écrire un test strict sans ouvrir `memory_manager.py`

---

**Guide créé le** : 5 novembre 2025  
**Contributeur** : GitHub Copilot  
**Prochaine étape** : Appliquer ce guide pour documenter l'API complète
