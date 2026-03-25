# ProfileManager - API Publique Extraite

**Date d'extraction** : extract_identity_api
**Fichier source** : `profile_manager.py`
**Total méthodes publiques** : 8

---

## 📊 Statistiques

- **Méthodes synchrones** : 8
- **Méthodes asynchrones** : 0

### Répartition par catégorie

- **Analysis & Info** : 1 méthode(s)
- **Delete & Reset** : 1 méthode(s)
- **Initialization** : 1 méthode(s)
- **Optimization & Maintenance** : 1 méthode(s)
- **Save & Backup** : 4 méthode(s)

---

## 📋 Méthodes par Catégorie

### Initialization

#### `__init__(data_root: str = 'data')`

**Ligne** : 24  
**Retour** : `Any`

**Description** :
> Pas de documentation disponible

### Save & Backup

#### `auto_cleanup_old_backups()`

**Ligne** : 184  
**Retour** : `Tuple[int, float]`

**Description** :
> Nettoie automatiquement les anciennes sauvegardes pour optimiser l'espace disque.
Garde les N plus récentes selon max_backups_to_keep.

Returns:
    (nombre_supprimé: int, espace_libéré_mb: float)

#### `save_current_profile(profile_name: str, description: str = '')`

**Ligne** : 482  
**Retour** : `Tuple[bool, str, Optional[Path]]`

**Description** :
> Sauvegarde complète du profil actuel

Returns:
    (success: bool, message: str, backup_path: Optional[Path])

#### `list_available_backups()`

**Ligne** : 584  
**Retour** : `List[Dict]`

**Description** :
> Liste toutes les sauvegardes disponibles avec leurs métadonnées

#### `load_profile_backup(backup_path: Path)`

**Ligne** : 891  
**Retour** : `Tuple[bool, str]`

**Description** :
> Charge une sauvegarde et remplace le profil actuel

Args:
    backup_path: Chemin vers le dossier de sauvegarde
    
Returns:
    (success: bool, message: str)

### Delete & Reset

#### `delete_current_profile(confirmation_code: str, preserve_founders: bool = True)`

**Ligne** : 640  
**Retour** : `Tuple[bool, str]`

**Description** :
> Supprime le profil actuel et remet OGMA à l'état vierge

Args:
    confirmation_code: Code de confirmation ("DELETE-PROFILE-OGMA")
    preserve_founders: Conserver les souvenirs fondateurs
    
Returns:
    (success: bool, message: str)

### Analysis & Info

#### `analyze_current_profile()`

**Ligne** : 358  
**Retour** : `Dict`

**Description** :
> Analyse le profil actuel pour affichage avant sauvegarde/suppression

### Optimization & Maintenance

#### `optimize_profile_performance()`

**Ligne** : 242  
**Retour** : `Dict[str, any]`

**Description** :
> Optimise les performances du profil actuel en analysant et compactant les données.

Returns:
    Dictionnaire avec les résultats des optimisations
