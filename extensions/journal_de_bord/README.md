# 📖 Extension Journal de Bord OGMA

## 🎯 **Vue d'ensemble**

L'extension **Journal de Bord** transforme OGMA en un système conversationnel doté d'une mémoire temporelle structurée. Chaque journée devient une page de journal qui capture et contextualise les interactions importantes pour enrichir les conversations futures.

### **Philosophie & Objectifs**

- **Mémoire temporelle** : Structurer les souvenirs par jour pour un accès rapide au contexte récent
- **Continuité conversationnelle** : L'IA dispose du contexte de la journée dès l'ouverture d'OGMA
- **Capture intelligente** : Résumés générés par l'Archiviste sur demande utilisateur
- **Navigation temporelle** : Exploration aisée des journées passées via interface calendrier

---

## 🏗️ **Architecture Technique**

### **Structure Modulaire**
```
extensions/journal_de_bord/
├── __init__.py                     # Point d'entrée extension
├── core_journal.py                 # Moteur principal + singleton
├── json_manager.py                 # Gestion persistance JSON avancée
├── entry_generator.py              # Génération résumés par Archiviste
├── ui_components.py                # Interface utilisateur (bouton + modal)
├── calendar_viewer.py              # Visualisation calendrier navigation
├── context_provider.py             # Injection contexte journalier
├── config.py                       # Configuration centralisée
├── data/                           # Données persistantes
│   ├── journal_2024.json          # Fichier année (auto-créé)
│   ├── journal_2025.json          # Fichier année suivante
│   └── settings.json               # Configuration utilisateur
├── README.md                       # Documentation principale
└── TECHNICAL_SPECS.md              # Spécifications techniques détaillées
```

### **Patterns Architecturaux**
- **Singleton Pattern** : Une seule instance active du journal
- **Observer Pattern** : Notifications entre composants (nouvelle entrée → UI update)
- **Strategy Pattern** : Différentes stratégies de résumé selon le contexte
- **Repository Pattern** : Abstraction de la persistance JSON

---

## 📊 **Structure de Données JSON**

### **Format Hiérarchique Optimisé**
```json
{
  "metadata": {
    "version": "1.0.0",
    "created": "2024-09-28T00:00:00Z",
    "last_updated": "2024-09-28T18:45:32Z",
    "total_entries": 156,
    "total_days": 45,
    "schema_version": "1.0"
  },
  "years": {
    "2024": {
      "metadata": {
        "total_entries": 89,
        "first_entry": "2024-01-15",
        "last_entry": "2024-09-28"
      },
      "months": {
        "09": {
          "metadata": {
            "total_entries": 23,
            "total_days": 12
          },
          "days": {
            "28": {
              "date": "2024-09-28",
              "day_summary": "Finalisation du système d'introspection et conception du journal de bord",
              "total_entries": 3,
              "importance_level": "high",
              "tags": ["développement", "introspection", "architecture"],
              "entries": [
                {
                  "id": "entry_20240928_144532",
                  "timestamp": "2024-09-28T14:45:32Z",
                  "summary": "Discussion approfondie sur l'extension cognitive mirror. Résolution des problèmes de détection d'activité utilisateur et optimisation du système d'interruption. L'introspection fonctionne maintenant parfaitement avec un timer de 60 secondes et une interruption immédiate lors de l'envoi de messages.",
                  "tokens": 287,
                  "conversation_id": "conv_abc123",
                  "conversation_title": "Debug Cognitive Mirror",
                  "generated_by": "archiviste",
                  "generation_model": "mistral-large",
                  "tags": ["technique", "debug", "introspection", "cognitive_mirror"],
                  "importance": "high",
                  "mood": "productive",
                  "participants": ["utilisateur", "claude", "archiviste"],
                  "context_keywords": ["timer", "interruption", "détection", "activité"],
                  "related_memories": ["REF-20240928-001", "REF-20240928-002"]
                }
              ]
            }
          }
        }
      }
    }
  },
  "search_index": {
    "tags": {
      "développement": ["2024-09-28", "2024-09-27"],
      "introspection": ["2024-09-28", "2024-09-25"]
    },
    "keywords": {
      "cognitive_mirror": ["2024-09-28"],
      "timer": ["2024-09-28", "2024-09-26"]
    }
  }
}
```

### **Avantages de cette Structure**
- **Performance** : Accès direct O(1) à une date spécifique
- **Évolutivité** : Ajout d'années sans restructuration
- **Recherche rapide** : Index des tags et mots-clés
- **Métadonnées riches** : Statistiques et contexte à tous les niveaux
- **Compression** : Chargement partiel (jour actuel uniquement en mémoire)

---

## 🎨 **Interface Utilisateur**

### **Intégration Header OGMA**
- **Bouton Journal** : Icône livre ouvert (`📖`) dans le header principal
- **Style cohérent** : Réutilisation des classes CSS OGMA existantes
- **Position** : À côté des indicateurs d'état IA
- **Tooltip** : "Journal de Bord - Capturer la conversation"

### **Modal de Visualisation**
- **Vue Calendrier** : Navigation mensuelle avec indicateurs d'activité
- **Panneau latéral** : Liste des entrées du jour sélectionné
- **Détail d'entrée** : Affichage complet avec métadonnées
- **Recherche** : Filtrage par tags, dates, mots-clés

### **Contexte Matinal**
- **Affichage automatique** : Page du jour en début de conversation
- **Format discret** : Intégration naturelle dans le flow conversationnel
- **Personnalisable** : Possibilité de désactiver via configuration

---

## 🔄 **Flux Fonctionnels**

### **1. Démarrage de Conversation**
```
Ouverture OGMA → Journal vérifie page du jour → 
Si entrées existent → Affiche contexte matinal → 
Conversation normale avec contexte enrichi
```

### **2. Capture Manuelle**
```
Clic bouton Journal → Modal confirmation → 
Archiviste génère résumé (200-400 tokens) → 
Sauvegarde JSON avec métadonnées → 
Notification succès + mise à jour UI
```

### **3. Navigation Temporelle**
```
Clic bouton Journal → Modal calendrier → 
Sélection date → Affichage entrées → 
Détail entrée → Contexte pour conversation
```

### **4. Recherche & Filtrage**
```
Recherche par mot-clé → Index JSON consulté → 
Résultats filtrés → Affichage pertinent → 
Navigation vers date/entrée
```

---

## ⚙️ **Configuration & Personnalisation**

### **Paramètres Utilisateur**
```json
{
  "auto_context_display": true,
  "context_max_entries": 3,
  "summary_min_tokens": 200,
  "summary_max_tokens": 400,
  "auto_tag_generation": true,
  "importance_detection": true,
  "ui_theme": "default",
  "notification_level": "normal",
  "backup_frequency": "daily",
  "data_retention_days": 365
}
```

### **Personnalisation Archiviste**
- **Style de résumé** : Formel, casual, technique
- **Focus thématique** : Technique, émotionnel, factuel
- **Niveau de détail** : Condensé, équilibré, détaillé

---

## 🔧 **Intégration OGMA**

### **Points d'Accroche**
1. **Header UI** : Ajout bouton dans `_header()` de `ogma_ng.py`
2. **Hook conversation** : Injection contexte en début de conversation
3. **Memory Manager** : Liaison avec système de souvenirs existant
4. **Archiviste API** : Utilisation pour génération de résumés

### **Compatibilité**
- **Extensions existantes** : Aucun conflit avec cognitive_mirror, perception, etc.
- **Versions OGMA** : Compatible avec architecture actuelle
- **Performance** : Impact minimal (<10ms par opération)

---

## 📈 **Cas d'Usage**

### **Développeur/Créateur**
- Suivi des décisions techniques prises
- Historique des bugs résolus
- Évolution des idées et concepts

### **Utilisateur Créatif**
- Journal de projets artistiques
- Évolution des idées créatives
- Suivi des inspirations et références

### **Professionnel**
- Compte-rendu de réunions importantes
- Suivi de projets complexes
- Historique des décisions stratégiques

### **Personnel**
- Journal intime avec IA
- Suivi d'objectifs personnels
- Réflexions et introspections

---

## 🚀 **Roadmap de Développement**

### **Phase 1 : Fondations (MVP)**
- [x] Architecture modulaire définie
- [ ] Structure JSON et persistance
- [ ] Interface basique (bouton + modal simple)
- [ ] Génération résumés Archiviste
- [ ] Contexte matinal basique

### **Phase 2 : Interface Avancée**
- [ ] Calendrier de navigation
- [ ] Recherche et filtrage
- [ ] Thèmes UI personnalisables
- [ ] Exportation de données

### **Phase 3 : Intelligence**
- [ ] Auto-tagging intelligent
- [ ] Détection d'importance automatique
- [ ] Suggestions de contexte
- [ ] Analyse de trends temporels

### **Phase 4 : Intégrations**
- [ ] Liaison avec Memory Manager
- [ ] Export vers formats externes
- [ ] API pour autres extensions
- [ ] Synchronisation cloud (optionnelle)

---

## 🔒 **Sécurité & Confidentialité**

### **Protection des Données**
- **Stockage local** : Toutes les données restent sur la machine utilisateur
- **Chiffrement optionnel** : Possibilité de chiffrer les fichiers JSON
- **Sauvegarde sécurisée** : Copies de sécurité avec versioning

### **Conformité**
- **RGPD** : Contrôle total utilisateur sur ses données
- **Transparence** : Code open-source et auditable
- **Anonymisation** : Option de suppression des métadonnées sensibles

---

## 🎯 **Objectifs de Performance**

### **Benchmarks Cibles**
- **Temps de chargement** : < 50ms pour afficher le contexte du jour
- **Génération résumé** : < 3s avec Archiviste local
- **Recherche** : < 100ms pour 1000+ entrées
- **Taille fichier** : < 1MB par année d'utilisation intensive

### **Optimisations**
- **Lazy loading** : Chargement à la demande des années anciennes
- **Compression** : JSON minifié avec compression gzip
- **Cache intelligent** : Mise en cache des recherches fréquentes
- **Index optimisé** : Structure d'index pour recherche rapide

---

## 📚 **Ressources & Documentation**

### **Documentation Technique**
- `TECHNICAL_SPECS.md` : Spécifications détaillées
- `API_REFERENCE.md` : Documentation API complète
- `DEVELOPMENT_GUIDE.md` : Guide de développement
- `DEPLOYMENT.md` : Instructions de déploiement

### **Exemples & Tutoriels**
- Exemples d'utilisation dans `examples/`
- Tutoriels pas à pas
- Configurations types pour différents cas d'usage

---

**Auteur** : Équipe OGMA  
**Version** : 2.0.0 (avec Option C - Maintenance Automatique)  
**Licence** : MIT  
**Contact** : Voir documentation principale OGMA

---

## 🧹 **Option C - Système de Purge et Auto-Résolution** (v2.0)

### **Vue d'ensemble**

L'Option C introduit un système de maintenance automatique pour gérer la croissance organique du journal et des états actifs. Elle permet de :
- **Compresser** les entrées anciennes via résumé LLM
- **Archiver** les entrées dans FAISS pour recherche sémantique
- **Auto-résoudre** les états actifs inactifs avec validation intelligente
- **Planifier** la maintenance hebdomadaire automatique

---

### **Composants Principaux**

#### **1. PurgeManager (`purge_manager.py`)**

Gestionnaire de compression et archivage des entrées anciennes.

**Fonctionnalités** :
- Détection entrées éligibles selon âge (défaut: 90+ jours)
- Compression via résumé LLM (Archiviste) - cible ~500 caractères
- Transfert vers FAISS avec métadonnées structurées
- Backup automatique avant toute modification
- Restauration possible des entrées compressées

**Utilisation programmatique** :
```python
from extensions.journal_de_bord.purge_manager import initialize_purge_manager

# Initialisation
purge_mgr = initialize_purge_manager(
    json_manager=json_manager,
    memory_manager=memory_manager,
    archiviste_controller=archiviste
)

# Détection entrées purgeable
purgeable = purge_mgr.get_purgeable_entries(
    age_days=90,
    exclude_active_states=True
)

# Purge avec compression
stats = purge_mgr.purge_old_entries(
    age_days=90,
    mode="compress",  # ou "archive" pour + FAISS
    dry_run=False
)
# Résultat: {total: 45, compressed: 42, archived: 0, failed: 3}

# Restauration si nécessaire
success, msg = purge_mgr.restore_compressed_entry(entry_id=150)
```

**Modes de purge** :
- `compress` : Résumé LLM uniquement (économie espace disque)
- `archive` : Résumé + transfert FAISS (recherche sémantique conservée)

---

#### **2. Auto-Resolution (`auto_resolution.py`)**

Système de résolution automatique des états actifs obsolètes.

**Critères de détection** :
- Inactivité > seuil (défaut: 30 jours)
- État non résolu (`resolved: false`)
- Importance != `high` (par défaut, configurable)

**Validation LLM** :
L'Archiviste analyse chaque état inactif avant résolution :
```json
{
  "should_resolve": true,
  "reason": "Aucune mise à jour depuis 45 jours. Historique suggère résolution naturelle."
}
```

**Utilisation** :
```python
from extensions.journal_de_bord.auto_resolution import (
    detect_inactive_states,
    auto_resolve_states
)

# Détection
inactive = detect_inactive_states(
    json_manager=json_manager,
    threshold_days=30,
    exclude_high_importance=True
)

# Auto-résolution avec validation
stats = auto_resolve_states(
    json_manager=json_manager,
    archiviste_controller=archiviste,
    threshold_days=30,
    dry_run=False,
    require_llm_validation=True
)
# Résultat: {total: 8, validated: 6, resolved: 5, rejected: 1, failed: 2}
```

---

#### **3. Scheduler (`scheduler.py`)**

Planificateur de maintenance hebdomadaire avec `threading.Timer`.

**Configuration** (`journal_settings.json`) :
```json
{
  "maintenance": {
    "auto_purge_enabled": false,
    "purge_age_days": 90,
    "purge_mode": "compress",
    "auto_resolve_enabled": false,
    "resolve_threshold_days": 30,
    "require_llm_validation": true,
    "maintenance_interval_days": 7,
    "last_maintenance": "2025-12-21T02:00:00Z"
  }
}
```

**Utilisation** :
```python
from extensions.journal_de_bord.scheduler import initialize_scheduler

# Initialisation
scheduler = initialize_scheduler(
    json_manager=json_manager,
    purge_manager=purge_manager,
    archiviste_controller=archiviste,
    settings_path=Path("data/journal_settings.json"),
    auto_start=True  # Démarre automatiquement
)

# Exécution manuelle immédiate
stats = scheduler.run_maintenance_now(dry_run=False)

# Modification config
scheduler.update_config(
    auto_purge_enabled=True,
    purge_age_days=120,
    auto_resolve_enabled=True
)
```

**Job hebdomadaire automatique** :
1. Détection et résolution états inactifs (si activé)
2. Compression/archivage entrées anciennes (si activé)
3. Logs détaillés et statistiques
4. Reprogrammation automatique

---

### **Interface Utilisateur - Modal Maintenance**

Accessible via bouton **🧹 Maintenance** dans le modal Journal principal.

#### **Onglet 1 : Purge Manuelle**
- **Configuration** : Âge minimum, mode (compress/archive), exclusion états actifs
- **Preview** : Liste entrées détectées avec statistiques (nombre, taille, déjà compressées)
- **Action** : Lancement purge avec confirmation
- **Résultats** : Stats temps réel (X compressées, Y archivées)

#### **Onglet 2 : Auto-Résolution**
- **Configuration** : Seuil inactivité, exclusion HIGH, validation LLM
- **Détection** : Liste états inactifs avec détails (catégorie, jours inactivité)
- **Action** : Auto-résolution avec preview
- **Résultats** : États résolus vs rejetés par LLM

#### **Onglet 3 : Configuration Scheduler**
- **Statut** : Actif/Inactif, dernière maintenance
- **Paramètres** : Enable/disable purge et auto-résolution, seuils, intervalle
- **Actions** : 
  - Sauvegarder configuration
  - Toggle scheduler (start/stop)
  - Exécuter maintenance immédiatement

---

### **Migration et Activation**

#### **Première Activation - Checklist**

**⚠️ AVANT TOUTE ACTIVATION :**

1. **Backup manuel complet** :
   ```bash
   # Sauvegarder le dossier journal
   cp -r extensions/journal_de_bord/data/ backups/journal_backup_$(date +%Y%m%d)/
   ```

2. **Vérifier dépendances** :
   - Archiviste configuré et fonctionnel
   - MemoryManager FAISS disponible (pour mode `archive`)
   - Espace disque suffisant (backups ~20% taille données)

3. **Test en mode dry_run** :
   ```python
   # Via UI ou code
   stats = purge_manager.purge_old_entries(age_days=90, dry_run=True)
   print(f"Preview: {stats['total']} entrées seraient traitées")
   ```

4. **Configuration recommandée initiale** :
   ```json
   {
     "maintenance": {
       "auto_purge_enabled": false,        // Désactivé par défaut
       "purge_age_days": 120,              // Conservateur (4 mois)
       "purge_mode": "compress",           // Sans FAISS initialement
       "auto_resolve_enabled": false,      // Désactivé par défaut
       "resolve_threshold_days": 45,       // Conservateur (1.5 mois)
       "require_llm_validation": true,     // Toujours activé
       "maintenance_interval_days": 7
     }
   }
   ```

5. **Activation progressive** :
   - Semaine 1 : Purge manuelle uniquement (via UI)
   - Semaine 2 : Auto-résolution manuelle
   - Semaine 3+ : Activation scheduler si satisfait

---

### **Seuils Recommandés par Profil**

#### **Utilisateur Occasionnel** (5-10 entrées/mois)
```json
{
  "purge_age_days": 180,           // 6 mois
  "resolve_threshold_days": 60,    // 2 mois
  "maintenance_interval_days": 14  // Bi-mensuel
}
```

#### **Utilisateur Régulier** (20-40 entrées/mois - Yohan)
```json
{
  "purge_age_days": 90,            // 3 mois (défaut)
  "resolve_threshold_days": 30,    // 1 mois
  "maintenance_interval_days": 7   // Hebdomadaire
}
```

#### **Utilisateur Intensif** (100+ entrées/mois)
```json
{
  "purge_age_days": 60,            // 2 mois
  "resolve_threshold_days": 21,    // 3 semaines
  "maintenance_interval_days": 3   // Tous les 3 jours
}
```

---

### **Sécurité et Récupération**

#### **Backups Automatiques**

Chaque opération critique crée un backup :
- **Emplacement** : `data/purge_backups/`
- **Format** : `entry_{id}_{type}_{timestamp}.json`
- **Rotation** : Conservation 10 derniers backups par défaut

#### **Restauration d'Urgence**

**Restaurer une entrée compressée** :
```python
# Via UI : Bouton "Restaurer" sur entrée compressée
# OU programmatique :
success, msg = purge_manager.restore_compressed_entry(entry_id=150)
```

**Restaurer depuis backup** :
```bash
# Copier backup vers emplacement original
cp data/purge_backups/entry_150_pre_compression_20251228.json \
   data/2024/09/2024-09-15.json
```

**Rollback complet** :
```bash
# Restaurer backup complet pré-activation
rm -rf extensions/journal_de_bord/data/
cp -r backups/journal_backup_20251228/ extensions/journal_de_bord/data/
```

---

### **Monitoring et Logs**

#### **Logs Console**

Tous les événements sont loggés :
```
[PURGE-MANAGER] Recherche entrées >90j
[PURGE-MANAGER] ✅ Trouvé 45 entrées purgeable
[PURGE-MANAGER] 🗜️ Compression entrée #150
[PURGE-MANAGER] ✅ Compression réussie : 2500→480 chars (ratio: 0.19)
[PURGE-MANAGER] 📦 Transfert FAISS entrée #150
[PURGE-MANAGER] ✅ Transfert FAISS réussi

[AUTO-RESOLVE] Détection états inactifs >30j
[AUTO-RESOLVE] ✅ Détecté 8 états inactifs
[AUTO-RESOLVE] LLM Validation #3: True - État obsolète, pas de mise à jour récente
[AUTO-RESOLVE] ✅ État #3 résolu: Apprentissage Python (inactif 45j)

[SCHEDULER] 🧹 MAINTENANCE HEBDOMADAIRE - 28/12/2025 02:00
[SCHEDULER] ✅ Auto-résolution: 5 résolus, 2 rejetés
[SCHEDULER] ✅ Purge: 42 compressées, 0 archivées
[SCHEDULER] 🎉 MAINTENANCE TERMINÉE
```

#### **Statistiques UI**

Chaque opération affiche stats temps réel :
- Nombre entrées traitées
- Ratio compression moyen
- Erreurs rencontrées
- Temps exécution

---

### **FAQ - Option C**

**Q: La compression est-elle réversible ?**  
R: Oui, si `content_original` est conservé. La méthode `restore_compressed_entry()` restaure le contenu complet.

**Q: Que se passe-t-il si l'Archiviste échoue ?**  
R: L'entrée reste non compressée. Un log d'erreur est créé. Aucune perte de données.

**Q: Les états actifs peuvent-ils être auto-résolus sans validation LLM ?**  
R: Oui, mais **fortement déconseillé**. Mettez `require_llm_validation: false` à vos risques.

**Q: Quelle est la taille d'un backup type ?**  
R: ~5-20 KB par entrée. Pour 100 entrées, attendez-vous à ~1-2 MB de backups.

**Q: Puis-je désactiver complètement l'Option C ?**  
R: Oui. Mettez `auto_purge_enabled: false` et `auto_resolve_enabled: false`. Le scheduler ne fera rien.

**Q: Les entrées archivées dans FAISS sont-elles encore lisibles ?**  
R: Partiellement. Le résumé compressé est stocké. Pour détails complets, restaurez depuis backup.

**Q: Combien d'espace disque est économisé ?**  
R: Typiquement 60-80% de réduction sur entrées compressées (selon verbosité originale).

---

### **Troubleshooting Option C**

| Problème | Cause Probable | Solution |
|----------|----------------|----------|
| "Archiviste non disponible" | Contrôleur non initialisé | Vérifier config `archiviste_controller` dans `__init__.py` |
| "PurgeManager non disponible" | Module non chargé | Vérifier import dans `__init__.py` : `from .purge_manager import initialize_purge_manager` |
| Compression échoue silencieusement | LLM timeout ou erreur | Vérifier logs Archiviste. Augmenter timeout si nécessaire |
| Scheduler ne démarre pas | Config maintenance désactivée | Activer `auto_purge_enabled` OU `auto_resolve_enabled` |
| Backups manquants | Permission écriture | Vérifier droits dossier `data/purge_backups/` |
| FAISS unavailable | MemoryManager non initialisé | Utiliser mode `compress` uniquement ou initialiser MemoryManager |

---

### **Roadmap Option C**

**v2.1 - Améliorations** (Q1 2026) :
- [ ] Compression différentielle (delta encoding)
- [ ] Export entrées compressées en Markdown
- [ ] Statistiques détaillées (dashboard analytics)
- [ ] Purge sélective par catégorie

**v2.2 - Intelligence** (Q2 2026) :
- [ ] Détection patterns récurrents (états qui reviennent)
- [ ] Suggestions proactives de résolution
- [ ] Apprentissage seuils optimaux par utilisateur
- [ ] Prédiction croissance données

**v3.0 - Cloud** (Q3 2026) :
- [ ] Synchronisation backups cloud optionnelle
- [ ] Compression cloud-native (S3/GCS)
- [ ] Multi-device avec conflict resolution

---

**Note importante** : L'Option C est un système puissant mais **opt-in**. Par défaut, tout est désactivé pour éviter modifications inattendues. Activez progressivement après familiarisation.
