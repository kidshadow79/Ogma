# Workflow Profil Générique OGMA
**Version générique v1.0 - Février 2026**

## 🎯 Objectif
Ce document décrit le workflow complet de gestion des profils pour une version générique d'OGMA, garantissant que les données personnelles sont sauvegardées et restaurées correctement.

---

## 📋 Fichiers Critiques du Profil

### **Fichiers d'Identité & Configuration**
- `data/settings.json` - Clés API et configuration providers
- `data/identities.json` - Noms utilisateur/IA, relation
- `data/persistent_context.txt` - Contexte persistant personnalisé
- `data/instructions_defaults.json` - Instructions par défaut (génériques)

### **Fichiers Ego (Personnalité IA)**
- `data/ego_prompt.txt` - Prompt ego principal
- `data/ego_compiled.json` - Ego compilé structuré
- `data/ego_compiled_boolean.md` - Ego version booléenne
- `data/ego_compiled_minimal.md` - Ego version minimale

### **Mémoire**
- `data/memory/memories.db` - Base SQLite des souvenirs
- `data/memory_index.faiss` - Index vectoriel FAISS
- `data/memory/backup/` - Backups automatiques

### **Extensions**
- `extensions/journal_de_bord/data/` - Journal quotidien
- `data/agenda.db` - Organic Planner
- `data/cognitive_mirror_reflections.jsonl` - Réflexions introspectives
- Autres configs extensions (archi_sensor, capability_advisor, etc.)

### **Médias**
- `captures/` - Photos webcam
- `generated_images/` - Images créées
- `conversations/` - Historique conversations

---

## 🔄 Workflow 1 : Sauvegarde de Profil

### **Méthode** : `ProfileManager.save_current_profile()`

### **Étapes**
1. ✅ **Analyse du profil actuel**
   - Taille totale, nombre de souvenirs, identité

2. ✅ **Optimisation préventive** (si > 50 MB)
   - Nettoyage conversations dupliquées
   - Compactage base de données

3. ✅ **Création dossier sauvegarde**
   - Format : `{nom_profil}_{timestamp}`
   - Exemple : `profil_luna_20260202_143525`

4. ✅ **Sauvegarde fichiers**
   - `metadata.json` - Métadonnées profil
   - `instructions_defaults.json` - Instructions par défaut
   - **`data/` COMPLET** (incluant fichiers ego ✅)
   - `extensions/*/data/` - Données extensions
   - `captures/` - Photos webcam

5. ✅ **Vérification fichiers ego**
   - Log explicite : "✅ Fichiers ego sauvegardés: ego_compiled.json, ..."

6. ✅ **Rapport de sauvegarde**
   - `backup_report.json` - Statistiques
   - Nettoyage auto anciennes sauvegardes (garde 10 max)

### **Résultat**
```
✅ Profil sauvegardé avec succès!
📂 profil_luna_20260202_143525
💾 123.4 MB
✅ Fichiers ego sauvegardés: ego_compiled.json, ego_compiled_boolean.md, ego_compiled_minimal.md
🗑️ Nettoyage auto: 2 sauvegardes anciennes supprimées (45.2 MB)
```

---

## 🗑️ Workflow 2 : Suppression/Reboot Profil

### **Méthode** : `ProfileManager.delete_current_profile()`

### **Code confirmation** : `"DELETE-PROFILE-OGMA"`

### **Étapes**
1. ✅ **Fermeture MemoryManager**
   - Évite conflits fichiers Windows

2. ✅ **Suppression dossiers données**
   - `conversations/`, `generated_images/`
   - `uploads/`, `biographies/`, `ego_archive/`, `logs/`
   - `captures/` (photos webcam)
   - ~~`summaries_cache/`~~ *(obsolète depuis v2.3 - résumés intégrés aux JSON conversations)*

3. ✅ **Traitement mémoire**
   - Option A : Supprime tout sauf souvenirs fondateurs (Capability Advisor)
   - Option B : Suppression complète

4. ✅ **Suppression données extensions**
   - Journal de bord, agenda, configurations

5. ✅ **Réinitialisation configurations**
   - `settings.json` → Defaults
   - `identities.json` → User générique
   - `ego_prompt.txt` → Structure vide
   - `persistent_context.txt` → Contexte par défaut

6. ✅ **🆕 Réinitialisation fichiers ego compilés**
   - `ego_compiled.json` → `{}`
   - `ego_compiled_boolean.md` → Contenu générique
   - `ego_compiled_minimal.md` → Contenu générique

### **Résultat**
```
✅ Profil supprimé avec succès!

Éléments supprimés:
  📁 conversations/
  📁 generated_images/
  📸 Captures webcam
  🧠 Mémoire (fondateurs préservés)
  📖 Journal de bord
  📅 Organic Planner (agenda)
  🔧 Configurations extensions
  ⚙️ Paramètres réinitialisés
  👤 Identité réinitialisée
  🎭 Ego réinitialisé
  🎭 Fichiers ego compilés vidés ← NOUVEAU
  📋 Contexte persistant réinitialisé
```

---

## 📂 Workflow 3 : Restauration Profil

### **Méthode** : `ProfileManager.load_profile_backup()`

### **Étapes**
1. ✅ **Validation sauvegarde**
   - Vérifie présence `metadata.json`

2. ✅ **Backup automatique état actuel**
   - Sauvegarde préventive avant écrasement

3. ✅ **Suppression profil actuel**
   - Appelle `delete_current_profile()`

4. ✅ **Restauration données**
   - `data/` COMPLET copié depuis backup
   - **Vérification explicite fichiers ego** ✅
   - Extensions restaurées
   - Captures webcam restaurées

5. ✅ **Réinitialisation managers**
   - MemoryManager rechargé
   - SettingsManager rechargé (nouvelles clés API)
   - Contrôleurs IA marqués pour réinit

6. ✅ **Analyse profil restauré**
   - Vérification intégrité

### **Log attendu**
```
📂 Chargement profil: profil_luna
  💾 Sauvegarde actuelle créée: backup_avant_load_20260202_150000
  🗑️ Profil actuel supprimé
  ✅ Données principales restaurées
  ✅ Fichiers ego restaurés: ego_compiled.json, ego_compiled_boolean.md, ego_compiled_minimal.md, ego_prompt.txt ← NOUVEAU
  ✅ Journal de bord restauré
  ✅ Captures webcam restaurées
  🔄 MemoryManager réinitialisé avec nouveau profil
  🔄 SettingsManager réinitialisé avec nouvelles clés API

✅ Profil chargé avec succès!

📋 Profil: profil_luna
👤 Utilisateur: Yohan
🤖 IA: Luna
🧠 Mémoires: 342
💾 Taille: 123.4 MB

Le profil est maintenant actif.
```

---

## ✅ Checklist de Vérification

### **Avant distribution version générique**
- [ ] Tester `save_current_profile()` → Vérifier fichiers ego sauvegardés
- [ ] Tester `delete_current_profile()` → Vérifier fichiers ego vidés
- [ ] Tester `load_profile_backup()` → Vérifier fichiers ego restaurés
- [ ] Vérifier log "Fichiers ego sauvegardés: ..." dans sauvegarde
- [ ] Vérifier log "Fichiers ego restaurés: ..." dans restauration
- [ ] Vérifier `ego_compiled.json` = `{}` après delete
- [ ] Vérifier `.md` contiennent texte générique après delete

### **Test workflow complet**
```bash
# 1. Sauvegarder profil actuel
python -c "from profile_manager import ProfileManager; pm = ProfileManager(); pm.save_current_profile('test_avant', 'Test')"

# 2. Supprimer profil (reboot)
python -c "from profile_manager import ProfileManager; pm = ProfileManager(); pm.delete_current_profile('DELETE-PROFILE-OGMA')"

# 3. Vérifier fichiers ego vides
cat data/ego_compiled.json  # Doit être {}

# 4. Restaurer profil
python -c "from profile_manager import ProfileManager; pm = ProfileManager(); pm.load_profile_backup(Path('profils_sauvegardes/test_avant_...'))"

# 5. Vérifier fichiers ego restaurés
cat data/ego_compiled.json  # Doit contenir données originales
```

---

## 🔧 Méthodes ProfileManager

### **Méthodes publiques**
- `save_current_profile(name, description)` - Sauvegarde complète
- `delete_current_profile(code, preserve_founders)` - Suppression/reboot
- `load_profile_backup(backup_path)` - Restauration
- `list_available_backups()` - Liste sauvegardes
- `analyze_current_profile()` - Analyse état actuel

### **Méthodes privées critiques**
- `_reset_ego_compiled_files()` - **🆕 Vide fichiers ego**
- `_reset_ego_to_default()` - Réinitialise ego_prompt.txt
- `_reset_settings_to_defaults()` - Réinitialise settings
- `_reset_identities_to_defaults()` - Réinitialise identities
- `_reinit_memory_manager()` - Recharge MemoryManager
- `_reinit_settings_manager()` - Recharge SettingsManager

---

## 📝 Notes de Version

### **v1.0 - Février 2026**
✅ Sauvegarde automatique fichiers ego dans profil
✅ Réinitialisation fichiers ego lors reboot
✅ Vérification explicite restauration fichiers ego
✅ Logs détaillés pour chaque étape
✅ Support complet workflow générique

---

**Auteur** : Yohan BROCARD (Architecture)  
**Implémentation** : Copilot (Exécution technique)  
**Date** : 2 février 2026
