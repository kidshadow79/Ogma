# 📋 Spécifications Techniques - Journal de Bord OGMA

## 🎯 **Architecture Détaillée**

### **Pattern MVC Adapté**
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     View        │    │   Controller    │    │     Model       │
│                 │    │                 │    │                 │
│ - ui_components │◄──►│ - core_journal  │◄──►│ - json_manager  │
│ - calendar_view │    │ - entry_gen     │    │ - data schemas  │
│ - context_ui    │    │ - hooks         │    │ - persistence   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### **Composants Core**

#### **1. CoreJournal (Singleton)**
```python
class JournalCore:
    """Moteur principal du journal de bord"""
    
    def __init__(self):
        self.json_manager = JSONManager()
        self.entry_generator = EntryGenerator() 
        self.context_provider = ContextProvider()
        self.config = JournalConfig()
        
    def initialize(self, archiviste_controller, memory_manager):
        """Initialisation avec dépendances OGMA"""
        
    def get_today_context(self) -> str:
        """Retourne le contexte de la journée actuelle"""
        
    def create_entry(self, conversation_id: str) -> dict:
        """Crée une nouvelle entrée via Archiviste"""
        
    def search_entries(self, query: str, filters: dict) -> list:
        """Recherche dans l'historique"""
```

#### **2. JSONManager (Persistance Avancée)**
```python
class JSONManager:
    """Gestionnaire optimisé de la persistance JSON"""
    
    def __init__(self):
        self.cache = {}  # Cache des données fréquemment utilisées
        self.index = SearchIndex()  # Index de recherche
        
    def load_year(self, year: int) -> dict:
        """Charge une année spécifique"""
        
    def save_entry(self, entry: dict) -> bool:
        """Sauvegarde une entrée avec mise à jour d'index"""
        
    def get_day_entries(self, date: str) -> list:
        """Récupère les entrées d'un jour"""
        
    def build_search_index(self) -> dict:
        """Construit l'index de recherche"""
```

#### **3. EntryGenerator (IA Archiviste)**
```python
class EntryGenerator:
    """Générateur de résumés via Archiviste"""
    
    def __init__(self, archiviste_controller):
        self.archiviste = archiviste_controller
        self.templates = SummaryTemplates()
        
    async def generate_summary(self, conversation_data: dict) -> dict:
        """Génère un résumé de conversation"""
        
    def extract_tags(self, summary: str) -> list:
        """Extraction automatique de tags"""
        
    def assess_importance(self, summary: str, metadata: dict) -> str:
        """Évaluation du niveau d'importance"""
```

---

## 📊 **Schémas de Données**

### **Schéma Entry Complet**
```python
ENTRY_SCHEMA = {
    "type": "object",
    "required": ["id", "timestamp", "summary", "tokens"],
    "properties": {
        # Identifiants
        "id": {"type": "string", "pattern": "^entry_[0-9]{8}_[0-9]{6}$"},
        "timestamp": {"type": "string", "format": "date-time"},
        
        # Contenu principal
        "summary": {
            "type": "string", 
            "minLength": 50, 
            "maxLength": 2000
        },
        "tokens": {"type": "integer", "minimum": 100, "maximum": 500},
        
        # Métadonnées conversation
        "conversation_id": {"type": "string"},
        "conversation_title": {"type": "string"},
        "participants": {
            "type": "array",
            "items": {"type": "string"}
        },
        
        # Génération
        "generated_by": {"type": "string", "enum": ["archiviste", "user", "system"]},
        "generation_model": {"type": "string"},
        "generation_prompt": {"type": "string"},
        
        # Classification
        "tags": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 10
        },
        "importance": {"type": "string", "enum": ["low", "normal", "high", "critical"]},
        "mood": {"type": "string", "enum": ["neutral", "positive", "negative", "mixed"]},
        "category": {"type": "string"},
        
        # Contexte
        "context_keywords": {
            "type": "array",
            "items": {"type": "string"}
        },
        "related_memories": {
            "type": "array", 
            "items": {"type": "string"}
        },
        "related_entries": {
            "type": "array",
            "items": {"type": "string"}
        },
        
        # Techniques
        "word_count": {"type": "integer"},
        "reading_time_seconds": {"type": "integer"},
        "confidence_score": {"type": "number", "minimum": 0, "maximum": 1}
    }
}
```

### **Schéma Day Complete**
```python
DAY_SCHEMA = {
    "type": "object",
    "required": ["date", "entries"],
    "properties": {
        "date": {"type": "string", "format": "date"},
        "entries": {
            "type": "array",
            "items": ENTRY_SCHEMA
        },
        
        # Métadonnées de journée
        "day_summary": {"type": "string"},
        "total_entries": {"type": "integer"},
        "importance_level": {"type": "string"},
        "dominant_mood": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}},
        
        # Statistiques
        "total_tokens": {"type": "integer"},
        "conversation_count": {"type": "integer"},
        "participant_count": {"type": "integer"},
        
        # Temps d'activité
        "first_entry": {"type": "string", "format": "time"},
        "last_entry": {"type": "string", "format": "time"},
        "active_hours": {"type": "array", "items": {"type": "integer"}},
        
        # Relations
        "connected_days": {"type": "array", "items": {"type": "string"}},
        "milestone": {"type": "boolean"},
        "archived": {"type": "boolean"}
    }
}
```

---

## 🔧 **APIs & Interfaces**

### **API Publique Extension**
```python
# Points d'entrée principaux
def initialize_journal(archiviste_controller, memory_manager, ui_container=None) -> bool:
    """Initialise l'extension journal"""

def get_journal() -> JournalCore:
    """Retourne l'instance singleton du journal"""

def get_today_context() -> str:
    """Contexte de la journée pour enrichir conversation"""

def create_manual_entry() -> dict:
    """Déclenche création d'entrée manuelle"""

def open_journal_ui():
    """Ouvre l'interface de navigation du journal"""

def search_journal(query: str, **filters) -> list:
    """Recherche dans l'historique du journal"""

def export_journal(format: str, date_range: tuple) -> str:
    """Export de données (JSON, Markdown, CSV)"""

def get_journal_stats() -> dict:
    """Statistiques d'utilisation du journal"""
```

### **Hooks OGMA**
```python
# Integration points dans ogma_ng.py

# 1. Header button injection
def _add_journal_button():
    """Ajoute le bouton journal au header"""
    
# 2. Conversation start hook  
def _inject_daily_context():
    """Injecte le contexte journalier au début"""
    
# 3. Message processing hook
def _track_conversation():
    """Suit l'évolution de la conversation pour résumé"""
```

---

## 🎨 **Spécifications UI**

### **Bouton Header**
```css
.journal-button {
    background: linear-gradient(135deg, #8B5A2B 0%, #CD853F 100%);
    border: 1px solid #A0522D;
    border-radius: 6px;
    padding: 8px 12px;
    color: white;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.2s ease;
}

.journal-button:hover {
    background: linear-gradient(135deg, #A0522D 0%, #DEB887 100%);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(139, 90, 43, 0.3);
}

.journal-button-icon {
    margin-right: 6px;
    font-size: 16px;
}
```

### **Modal Journal**
```css
.journal-modal {
    width: 90vw;
    max-width: 1200px;
    height: 80vh;
    background: var(--surface-color);
    border-radius: 12px;
    border: 1px solid var(--border-color);
}

.journal-header {
    padding: 20px;
    border-bottom: 1px solid var(--border-color);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.journal-content {
    display: flex;
    height: calc(100% - 80px);
}

.journal-calendar {
    width: 300px;
    border-right: 1px solid var(--border-color);
    padding: 16px;
}

.journal-entries {
    flex: 1;
    padding: 16px;
    overflow-y: auto;
}
```

### **Contexte Matinal**
```css
.daily-context {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border: 1px solid #3a4a6b;
    border-radius: 8px;
    padding: 16px;
    margin: 16px 0;
    position: relative;
}

.daily-context-header {
    color: #e8d5b7;
    font-weight: 600;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
}

.daily-context-content {
    color: #b8c5d1;
    font-size: 14px;
    line-height: 1.6;
}
```

---

## 🚀 **Performance & Optimisations**

### **Stratégies de Performance**
```python
class PerformanceOptimizer:
    """Optimisations performance du journal"""
    
    def __init__(self):
        self.cache = LRUCache(maxsize=100)
        self.index_cache = {}
        self.lazy_loader = LazyDataLoader()
        
    def optimize_json_loading(self):
        """Optimisations de chargement JSON"""
        # - Chargement partiel (streaming)
        # - Compression gzip
        # - Cache intelligent
        # - Index pré-construit
        
    def optimize_search(self):
        """Optimisations de recherche"""
        # - Index inversé
        # - Recherche floue (fuzzy)
        # - Cache des requêtes
        # - Pagination intelligente
```

### **Benchmarks Cibles**
- **Cold start** : < 100ms (premier chargement)
- **Hot reload** : < 10ms (données en cache)
- **Search query** : < 50ms (1000+ entrées)
- **Entry creation** : < 2s (génération Archiviste)
- **Context injection** : < 20ms (début conversation)

---

## 🔒 **Sécurité & Validation**

### **Validation des Données**
```python
class DataValidator:
    """Validation stricte des données journal"""
    
    def validate_entry(self, entry: dict) -> bool:
        """Valide une entrée selon le schéma"""
        
    def sanitize_input(self, text: str) -> str:
        """Nettoie les entrées utilisateur"""
        
    def check_data_integrity(self) -> dict:
        """Vérifie l'intégrité des fichiers JSON"""
```

### **Protection des Données**
- **Chiffrement AES-256** : Option pour fichiers JSON sensibles
- **Sauvegarde versionnée** : Copies avec historique
- **Validation schema** : Protection contre corruption
- **Sandboxing** : Isolation des opérations fichier

---

## 🧪 **Tests & Qualité**

### **Suite de Tests**
```python
# tests/
├── test_core_journal.py        # Tests du moteur principal
├── test_json_manager.py        # Tests persistance
├── test_entry_generator.py     # Tests génération résumés
├── test_ui_components.py       # Tests interface
├── test_performance.py         # Tests de performance
├── test_integration.py         # Tests d'intégration OGMA
└── fixtures/                   # Données de test
    ├── sample_journal.json
    ├── mock_conversations.json
    └── test_configs.json
```

### **Métriques Qualité**
- **Coverage** : > 90% du code
- **Performance** : Benchmarks automatisés
- **Security** : Scan vulnérabilités
- **Compatibility** : Tests multi-environnements

---

## 📦 **Déploiement & Installation**

### **Procédure d'Installation**
```python
# Intégration automatique dans OGMA
def install_journal_extension():
    """Installation automatique de l'extension"""
    
    # 1. Créer structure dossiers
    create_extension_structure()
    
    # 2. Initialiser configurations
    initialize_default_config()
    
    # 3. Intégrer hooks OGMA
    register_ogma_hooks()
    
    # 4. Ajouter bouton UI
    inject_ui_components()
    
    # 5. Vérifier installation
    run_installation_tests()
```

### **Migration de Données**
```python
class DataMigrator:
    """Migration entre versions du journal"""
    
    def migrate_v1_to_v2(self, old_data: dict) -> dict:
        """Migration de schéma v1 vers v2"""
        
    def backup_before_migration(self) -> str:
        """Sauvegarde avant migration"""
        
    def rollback_migration(self, backup_path: str) -> bool:
        """Rollback en cas de problème"""
```

---

## 🔄 **Maintenance & Évolution**

### **Monitoring & Logs**
```python
class JournalLogger:
    """Système de logs dédié au journal"""
    
    def log_entry_creation(self, entry_id: str, duration: float):
        """Log création d'entrée"""
        
    def log_search_query(self, query: str, results_count: int, duration: float):
        """Log requête de recherche"""
        
    def log_performance_metrics(self, metrics: dict):
        """Log métriques de performance"""
```

### **Évolutions Prévues**
- **V1.1** : Recherche avancée avec IA
- **V1.2** : Export vers applications externes
- **V1.3** : Synchronisation cloud optionnelle
- **V2.0** : Analyse de patterns et insights IA

---

**Version** : 1.0.0  
**Dernière mise à jour** : 2024-09-28  
**Auteur** : Équipe OGMA  
**Statut** : Spécifications finalisées, développement en cours