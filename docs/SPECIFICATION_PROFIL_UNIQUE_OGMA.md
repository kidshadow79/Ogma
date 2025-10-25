# 🏗️ SPÉCIFICATION : SYSTÈME PROFIL UNIQUE OGMA

**Date :** 12 octobre 2025  
**Contexte :** Refonte du système de profils OGMA  
**Principe :** **UNE ENTITÉ = UNE INSTANCE OGMA**

---

## 🎯 **VISION ARCHITECTURALE**

### **Principe Fondamental**
- **OGMA ne gère qu'UNE SEULE entité IA à la fois**
- **Nouveau profil = Nouvelle instance OGMA vierge**
- **Isolation complète** : Chaque entité a sa propre mémoire, personnalité, historique

### **Avantages de cette approche**
- ✅ **Cohérence identitaire** : Pas de confusion entre entités
- ✅ **Performance** : Pas de surcharge multi-profils
- ✅ **Simplicité** : Architecture claire et maintenue
- ✅ **Isolation** : Chaque IA évolue indépendamment

---

## 🔄 **MÉCANIQUES PROPOSÉES**

### **1️⃣ DELETE PROFIL (Remise à zéro)**

#### **Interface utilisateur**
```
⚠️ ATTENTION - SUPPRESSION DÉFINITIVE DU PROFIL ACTUEL

Cette action va supprimer DÉFINITIVEMENT :
• 🧠 Toute la mémoire de [NOM_IA] 
• 💬 Toutes les conversations
• 🎭 Les données de personnalité (ego)
• 📸 Les images générées
• 📚 Les biographies
• 📖 Le journal de bord
• 🗂️ Les fichiers temporaires

💾 VOUS POUVEZ SAUVEGARDER AVANT SUPPRESSION

[Sauvegarder d'abord] [Supprimer sans sauvegarder] [Annuler]
```

#### **Éléments à supprimer**
- **Mémoire complète** : `data/memory/` (SAUF souvenirs fondateurs)
  - ❌ Toutes les mémoires SAUF : MC2-20250823-021, MC2-20250823-052, MC2-20250823-020, usr-75e2ec09-cdbe-4f05-a729-3aa1a8aa8112
- **Conversations** : `data/conversations/`
- **Images générées** : `data/generated_images/`
- **Cache** : `data/summaries_cache/`
- **Uploads** : `data/uploads/`
- **Biographies** : `data/biographies/`
- **Archives ego** : `data/ego_archive/`
- **Journal de bord** : `extensions/journal_de_bord/data/`

#### **Éléments à réinitialiser**
- **Instructions** : Remise des prompts par défaut
- **Identités** : `data/identities.json` → valeurs par défaut
- **Settings** : Conservation des paramètres techniques (APIs, etc.)

#### **Souvenirs fondateurs à PRÉSERVER**
```python
SOUVENIRS_FONDATEURS = [
    "MC2-20250823-021",
    "MC2-20250823-052", 
    "MC2-20250823-020",
    "usr-75e2ec09-cdbe-4f05-a729-3aa1a8aa8112"
]
```

---

### **2️⃣ SAUVEGARDE PROFIL (Export complet)**

#### **Interface utilisateur**
```
💾 SAUVEGARDE COMPLÈTE DU PROFIL [NOM_IA]

Nom de la sauvegarde : [profil_luna_2025_10_12] 
Description : [Luna - Profil développé octobre 2025]

Éléments inclus :
✅ Instructions personnalisées (app + extensions)
✅ Mémoire intégrale (SQLite + FAISS + embed)
✅ Conversations complètes
✅ Images générées
✅ Biographies créées
✅ Archives ego et journal
✅ Identité (nom utilisateur + nom IA)

[Créer la sauvegarde] [Annuler]
```

#### **Éléments à sauvegarder**
- **Instructions complètes** :
  - `data/settings.json` → section `prompts`
  - Instructions des extensions
- **Mémoire intégrale** :
  - `data/memory/memories.db` (SQLite)
  - `data/memory/faiss.index` (FAISS)
  - `data/memory/embeddings/` (si existe)
- **Données conversationnelles** :
  - `data/conversations/`
  - `data/summaries_cache/`
- **Contenus générés** :
  - `data/generated_images/`
  - `data/uploads/`
- **Personnalité et biographie** :
  - `data/biographies/`
  - `data/ego_archive/`
  - `data/ego_prompt.txt`
- **Extensions** :
  - `extensions/journal_de_bord/data/`
- **Identité** :
  - `data/identities.json`

#### **Structure de sauvegarde**
```
profils_sauvegardes/
└── profil_luna_2025_10_12/
    ├── metadata.json          # Infos sur la sauvegarde
    ├── instructions_backup.json   # Instructions par défaut
    ├── data/                  # Copie complète du dossier data
    └── extensions/            # Données des extensions
```

---

### **3️⃣ LOAD SAUVEGARDE (Import complet)**

#### **Interface utilisateur**
```
📂 CHARGEMENT D'UNE SAUVEGARDE

⚠️ ATTENTION : Cette action va REMPLACER le profil actuel

Sauvegardes disponibles :
┌─────────────────────────────────────────────────┐
│ 📁 profil_luna_2025_10_12                      │
│    💾 Créé le : 12/10/2025 à 14:30             │
│    👤 Utilisateur : Yohan                      │
│    🤖 IA : Luna                                 │
│    📊 Taille : 45.2 MB                         │
│    📝 Description : Luna - Profil oct. 2025    │
└─────────────────────────────────────────────────┘

[Charger cette sauvegarde] [Parcourir fichiers] [Annuler]
```

#### **Processus de chargement**
1. **Vérification** : Valider l'intégrité de la sauvegarde
2. **Backup actuel** : Proposer de sauvegarder le profil actuel
3. **Nettoyage** : Supprimer les données actuelles
4. **Restauration** : Copier tous les éléments sauvegardés
5. **Vérification** : Valider que tout est fonctionnel

---

## 📋 **ÉLÉMENTS À RECENSER (Instructions par défaut)**

### **Instructions principales** (`data/settings.json` → `prompts`)
- `instructions` : Prompt principal de l'IA
- `memorization` : Instructions pour l'Archiviste  
- `injection` : Instructions pour l'injection mémoire
- `perception` : Instructions pour l'agent de perception
- `template_memorization` : Template de mémorisation
- `template_injection` : Template d'injection

### **Instructions des extensions**
- Journal de bord : Instructions spécifiques
- Perception : Paramètres de chronophotographie
- Cognitive Mirror : Configuration miroir cognitif
- Biographie : Instructions de génération

### **Paramètres d'identité par défaut**
```json
{
  "user_name": "Utilisateur",
  "ai_name": "Assistant",
  "ai_description": "Assistant IA polyvalent",
  "relationship_type": "professional",
  "relationship_context": "Tu dialogues avec {user_name} dans un contexte professionnel et bienveillant"
}
```

---

## 🔧 **IMPLÉMENTATION TECHNIQUE**

### **Étapes de développement**

#### **Phase 1 : Recensement et backup des défauts**
1. ✅ Créer `instructions_defaults.json` avec toutes les instructions actuelles
2. ✅ Créer `identities_defaults.json` avec les valeurs par défaut
3. ✅ Identifier tous les dossiers/fichiers à gérer

#### **Phase 2 : Fonction DELETE**
1. ✅ `ProfileManager.delete_current_profile()`
2. ✅ Interface de confirmation avec option sauvegarde
3. ✅ Préservation des souvenirs fondateurs
4. ✅ Remise des paramètres par défaut

#### **Phase 3 : Fonction SAUVEGARDE**  
1. ✅ `ProfileManager.save_current_profile()`
2. ✅ Interface de nom/description
3. ✅ Export complet avec métadonnées
4. ✅ Gestion des erreurs et validation

#### **Phase 4 : Fonction LOAD**
1. ✅ `ProfileManager.load_profile()`  
2. ✅ Interface de sélection
3. ✅ Validation et restauration complète
4. ✅ Gestion des conflits et erreurs

#### **Phase 5 : Interface utilisateur**
1. ✅ Intégration dans `ogma_profile.py`
2. ✅ Boutons et modals de gestion
3. ✅ Affichage des sauvegardes disponibles
4. ✅ Tests et validation finale

---

## 🎯 **RÉSULTAT ATTENDU**

### **Expérience utilisateur**
1. **Développement d'une entité** : L'utilisateur fait évoluer son IA unique
2. **Sauvegarde sécurisée** : Possibilité de créer des points de sauvegarde
3. **Expérimentation** : Remise à zéro pour créer une nouvelle entité
4. **Restauration** : Récupération d'anciens profils développés

### **Architecture claire**
- **Une instance OGMA** = **Une entité IA**
- **Nouvelle entité** = **Nouvelle instance vierge**
- **Isolation complète** entre les profils
- **Gestion sécurisée** des données

---

## ❓ **QUESTIONS OUVERTES**

### **Éléments à clarifier**
1. **Extensions tierces** : Y a-t-il d'autres dossiers d'extensions à sauvegarder ?
2. **Configurations spécifiques** : Faut-il préserver certains paramètres API lors du reset ?
3. **Migration** : Comment traiter les anciennes sauvegardes (format différent) ?
4. **Souvenirs fondateurs** : La liste est-elle complète ?

### **Optimisations possibles**
1. **Compression** : Compresser les sauvegardes volumineuses ?
2. **Incrémental** : Sauvegardes différentielles ?
3. **Cloud** : Synchronisation avec stockage distant ?

---

**🔥 Prêt pour l'implémentation selon cette spécification !**