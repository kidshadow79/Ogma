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
**Version** : 1.0.0  
**Licence** : MIT  
**Contact** : Voir documentation principale OGMA