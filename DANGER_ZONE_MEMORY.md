# ⚠️ Zone Dangereuse - Suppression Totale Mémoire

## 📍 Accès

**Chemin** : Paramètres généraux → Mémoire → ⚠️ Zone Dangereuse (expansion) → Bouton "Supprimer TOUS les souvenirs"

---

## 🎯 Fonctionnalité

Permet de **supprimer TOUS les souvenirs** de la mémoire OGMA de manière **DÉFINITIVE et IRRÉVERSIBLE**.

### Chaîne de suppression complète

✅ **SQLite** : Toutes les entrées dans `memories.db` supprimées  
✅ **FAISS** : Index vectoriel complètement réinitialisé (nouvel index vide)  
✅ **Embeddings** : Tous les vecteurs effacés  
✅ **Mappings** : Tables `id_to_faiss` et `faiss_to_id` vidées  
✅ **Ego traits** : Synchronisation `ego_prompt.txt` (références supprimées)

---

## 🔐 Sécurités Implémentées

### 1️⃣ **Double Protection**

1. **Modal de confirmation** :
   - Affiche le nombre exact de souvenirs à supprimer
   - Liste tous les éléments impactés (SQLite, FAISS, embeddings, etc.)
   - Génère un **code PIN aléatoire** (4 chiffres : 1000-9999)

2. **Validation PIN** :
   - L'utilisateur DOIT saisir le code PIN exact affiché
   - Aucune suppression sans code correct
   - Impossible de deviner ou "spammer" la validation

### 2️⃣ **Backup Automatique**

Avant toute suppression :
- **Backup SQLite** créé dans `data/memory/backup/`
- Nom : `memories_backup_before_delete_all_YYYYMMDD_HHMMSS.db`
- Notification du chemin de backup dans le modal
- Permet restauration manuelle si erreur

### 3️⃣ **Messages Clairs**

- ⚠️ **Avertissements visuels** : Texte rouge, icônes warning
- 📊 **Statistiques précises** : Nombre de souvenirs, taille index, etc.
- ✅ **Confirmation finale** : "X souvenirs supprimés + backup créé"

---

## 📊 Retour d'Informations

Après exécution, la méthode `delete_all_memories()` retourne :

```python
{
    'deleted_count': 239,  # Nombre de souvenirs supprimés
    'faiss_reset': True,   # Index FAISS réinitialisé
    'backup_created': True,  # Backup créé avec succès
    'backup_path': 'data/memory/backup/memories_backup_before_delete_all_20251026_143052.db'
}
```

En cas d'erreur :
```python
{
    'deleted_count': 0,
    'faiss_reset': False,
    'backup_created': False,
    'backup_path': None,
    'error': 'Message d\'erreur détaillé'
}
```

---

## 🎬 Workflow Utilisateur

### Étape 1 : Ouvrir Paramètres Mémoire
1. Clic icône ⚙️ Paramètres généraux (coin supérieur droit)
2. Clic bouton "Mémoire" (icône `database`)

### Étape 2 : Accéder Zone Dangereuse
3. Scroll vers le bas du modal
4. Clic sur l'expansion **"⚠️ Zone Dangereuse"** (fond rouge)

### Étape 3 : Initier Suppression
5. Clic bouton rouge **"Supprimer TOUS les souvenirs"**
6. Modal de confirmation s'ouvre

### Étape 4 : Validation
7. Lire attentivement :
   - Nombre de souvenirs à supprimer
   - Éléments impactés (SQLite, FAISS, etc.)
   - Code PIN affiché (ex: `3847`)
8. Saisir le code PIN exact dans le champ
9. Clic bouton **"SUPPRIMER TOUT"** (rouge)

### Étape 5 : Exécution
10. Message "⏳ Suppression en cours..."
11. Progression affichée en temps réel
12. Notification succès : "✅ X souvenirs supprimés + backup créé"
13. Modal se ferme automatiquement après 2 secondes
14. Liste mémoire rafraîchie (vide)

---

## 🛠️ Code Technique

### Méthode Backend (memory_manager.py)

```python
def delete_all_memories(self) -> Dict[str, Any]:
    """
    Supprime TOUS les souvenirs (SQLite + FAISS + embeddings).
    ⚠️ IRRÉVERSIBLE ⚠️
    """
    # 1. Créer backup
    backup_path = backup_dir / f"memories_backup_before_delete_all_{timestamp}.db"
    shutil.copy2(self.db_path, backup_path)
    
    # 2. Supprimer SQLite
    with sqlite3.connect(self.db_path) as conn:
        conn.execute("DELETE FROM memories")
        conn.commit()
    
    # 3. Réinitialiser mappings
    self.id_to_faiss.clear()
    self.faiss_to_id.clear()
    self.next_faiss_pos = 0
    
    # 4. Réinitialiser FAISS
    self.faiss_index = faiss.IndexFlatL2(self.embedding_dim)
    self.save_index()
    
    # 5. Synchroniser ego_prompt
    self.sync_ego_prompt_references()
    
    return {
        'deleted_count': count_before,
        'faiss_reset': True,
        'backup_created': True,
        'backup_path': str(backup_path)
    }
```

### Interface Frontend (ogma_modals.py)

```python
# Génération PIN aléatoire
pin_code = str(random.randint(1000, 9999))

# Validation + Exécution
if pin_input.value == pin_code:
    result = mm.delete_all_memories()
    ui.notify(f"{result['deleted_count']} souvenirs supprimés", type='positive')
    refresh_list()
else:
    ui.notify("❌ Code PIN incorrect", type='negative')
```

---

## ⚠️ Cas d'Usage

### ✅ Quand utiliser ?

- **Reset complet** : Développement, tests, nouveaux départs
- **Corruption données** : Index FAISS corrompu, incohérences SQLite
- **Migration** : Changement d'architecture mémoire
- **Nettoyage** : Souvenirs obsolètes, données test à supprimer
- **Privacy** : Effacement complet avant partage/vente machine

### ❌ Quand NE PAS utiliser ?

- **Suppression sélective** : Utiliser "Supprimer" sur souvenir individuel
- **Édition** : Modifier souvenirs existants via formulaire édition
- **Archivage** : Exporter backup AVANT suppression (profil manager)
- **Doute** : Si incertain, faire backup complet profil d'abord

---

## 🔄 Restauration après Suppression

### Option 1 : Backup Automatique

1. Localiser backup : `data/memory/backup/memories_backup_before_delete_all_*.db`
2. Arrêter OGMA
3. Copier backup → `data/memory/memories.db` (remplacer)
4. Relancer OGMA
5. Rebuild FAISS : `python rebuild_faiss_complete.py`

### Option 2 : Backup Profil Complet

Si backup profil existant (`profile_manager.py`) :
1. Menu Profil → Restaurer
2. Sélectionner backup avant suppression
3. Confirmer restauration
4. Redémarrer OGMA

---

## 📝 Logs Console

Lors de l'exécution, logs détaillés dans console :

```
[DELETE-ALL] ⚠️  SUPPRESSION TOTALE DE LA MÉMOIRE DÉMARRÉE...
[DELETE-ALL] ✅ Backup créé: data/memory/backup/memories_backup_before_delete_all_20251026_143052.db
[DELETE-ALL] 📊 239 souvenirs à supprimer...
[DELETE-ALL] 🗑️  SQLite vidé (239 souvenirs supprimés)
[DELETE-ALL] 🔄 Mappings réinitialisés
[DELETE-ALL] ✅ Index FAISS réinitialisé et sauvegardé
[DELETE-ALL] 🔄 ego_prompt.txt synchronisé (références vidées)
[DELETE-ALL] ✅ SUPPRESSION TOTALE TERMINÉE : 239 souvenirs effacés
```

---

## 🎨 Design UI

### Couleurs

- **Fond expansion** : `rgba(220, 53, 69, 0.08)` (rouge transparent)
- **Bordure** : `rgba(220, 53, 69, 0.3)` (rouge semi-opaque)
- **Texte** : `#dc3545` (rouge danger Bootstrap)
- **Bouton** : Fond rouge clair, texte rouge foncé

### Icônes

- **Expansion** : `warning` (⚠️)
- **Bouton principal** : `delete_forever` (🗑️♾️)
- **Modal** : `delete_forever` + texte rouge

### Position

- **Bas du modal mémoire** : Après boutons "Fermer", avant notes
- **Collapsible** : Caché par défaut (expansion fermée)
- **Pleine largeur** : Bouton occupe 100% largeur (`w-full`)

---

## 🧪 Tests Recommandés

### Test 1 : Validation PIN
1. Ouvrir modal → Saisir **mauvais** PIN → Vérifier erreur
2. Saisir **bon** PIN → Vérifier suppression

### Test 2 : Backup
1. Supprimer mémoire
2. Vérifier backup créé dans `data/memory/backup/`
3. Vérifier nom fichier horodaté

### Test 3 : Chaîne Complète
1. Vérifier SQLite vide : `SELECT COUNT(*) FROM memories` → 0
2. Vérifier FAISS vide : `faiss_index.ntotal` → 0
3. Vérifier mappings vides : `len(id_to_faiss)` → 0

### Test 4 : Restauration
1. Supprimer mémoire
2. Restaurer backup
3. Rebuild FAISS
4. Vérifier données récupérées

---

## 📚 Références Code

### Fichiers Modifiés

| Fichier | Lignes | Modifications |
|---------|--------|---------------|
| `memory_manager.py` | +107 | Méthode `delete_all_memories()` |
| `ogma_modals.py` | +115 | Section "Zone Dangereuse" + modal PIN |

### Commit Git

```
commit 27dc0fa
Author: [Auto]
Date: 26 octobre 2025

feat(memory): Suppression totale mémoire avec double protection
```

---

## ⚡ Performance

- **Temps exécution** : ~0.5-2 secondes (selon taille mémoire)
- **Backup** : ~0.1-0.5 secondes (copie SQLite)
- **FAISS reset** : Instantané (nouvel index vide)
- **Mappings** : Instantané (clear dicts)

---

## 🔒 Sécurité Code

### Protection Thread-Safety

```python
# Mappings
with self._mapping_lock:
    self.id_to_faiss.clear()
    self.faiss_to_id.clear()

# FAISS
with self._faiss_lock:
    self.faiss_index = faiss.IndexFlatL2(self.embedding_dim)
```

### Gestion Erreurs

```python
try:
    result = mm.delete_all_memories()
except Exception as e:
    ui.notify(f'Erreur : {e}', type='negative')
    return {
        'deleted_count': 0,
        'error': str(e)
    }
```

---

## 📞 Support

**Problèmes** : Vérifier logs console pour erreurs détaillées  
**Backup perdu** : Chercher dans `data/memory/backup/` (rotation 10 fichiers max)  
**Restauration** : Utiliser `profile_manager.py` ou copie manuelle + rebuild FAISS

---

**Date de création** : 26 octobre 2025  
**Version OGMA** : Compatible toutes versions avec `memory_manager.py` + `ogma_modals.py`  
**Auteur** : Tytan + GitHub Copilot
