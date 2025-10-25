# 🛠️ Guide de Développement - Journal de Bord OGMA

## 🎯 **Introduction**

Ce guide détaille la méthodologie de développement de l'extension Journal de Bord, en appliquant les bonnes pratiques observées dans l'extension cognitive_mirror et en évitant les écueils identifiés.

---

## 📋 **Plan de Développement**

### **Phase 1 : Architecture & Fondations**
```
┌─ Jour 1-2: Structure & Configuration
├─ Jour 3-4: Persistance JSON
├─ Jour 5-6: Génération résumés Archiviste  
└─ Jour 7: Tests & validation Phase 1
```

### **Phase 2 : Interface Utilisateur**
```
┌─ Jour 8-9: Bouton header & modal basique
├─ Jour 10-11: Calendrier de navigation
├─ Jour 12-13: Contexte matinal
└─ Jour 14: Tests & validation Phase 2
```

### **Phase 3 : Fonctionnalités Avancées**
```
┌─ Jour 15-16: Recherche & filtrage
├─ Jour 17-18: Optimisations performance
├─ Jour 19-20: Intégration OGMA complète
└─ Jour 21: Tests finaux & documentation
```

---

## 🏗️ **Méthodologie de Développement**

### **Principes Directeurs**
1. **Modularité absolue** : Chaque composant indépendant et testable
2. **Pas de refactoring** : Architecture stable dès le départ
3. **Intégration non-invasive** : Hooks propres sans modification core OGMA
4. **Performance first** : Optimisations dès la conception
5. **Validation utilisateur** : Tests réels à chaque étape

### **Pattern de Développement**
```python
# Structure de développement par composant

# 1. SPÉCIFICATION
def define_component_specs():
    """Définir clairement les responsabilités"""
    pass

# 2. INTERFACE
def design_public_api():
    """API publique stable et intuitive"""
    pass

# 3. IMPLÉMENTATION
def implement_core_logic():
    """Logique métier sans dépendances externes"""
    pass

# 4. TESTS
def write_comprehensive_tests():
    """Tests unitaires + intégration"""
    pass

# 5. INTÉGRATION
def integrate_with_ogma():
    """Hooks et points d'accroche OGMA"""
    pass

# 6. VALIDATION
def user_testing():
    """Tests utilisateur réels"""
    pass
```

---

## 🎯 **Ordre d'Implémentation Optimal**

### **1. Configuration & Core (Jour 1-2)**
```python
# Priorité 1: Fondations solides
extensions/journal_de_bord/
├── config.py              # ✅ Configuration centralisée
├── core_journal.py        # ✅ Singleton pattern
└── __init__.py            # ✅ Points d'entrée publics

# Validation immédiate
- Configuration charge correctement
- Singleton fonctionne
- APIs publiques définies
```

### **2. Persistance JSON (Jour 3-4)**
```python
# Priorité 2: Gestion des données
├── json_manager.py        # ✅ CRUD operations
├── data_schemas.py        # ✅ Validation schemas
└── data/                  # ✅ Structure fichiers

# Tests critiques
- Création/lecture/écriture JSON
- Validation des schémas
- Performance sur gros volumes
```

### **3. Génération Résumés (Jour 5-6)**
```python
# Priorité 3: Intégration Archiviste
├── entry_generator.py     # ✅ Génération résumés
├── summary_templates.py   # ✅ Templates prompts
└── ai_integration.py      # ✅ Interface Archiviste

# Validation IA
- Qualité des résumés
- Gestion des timeouts
- Fallbacks en cas d'erreur
```

### **4. Interface Header (Jour 8-9)**
```python
# Priorité 4: Première intégration UI
├── ui_components.py       # ✅ Bouton header
├── modal_basic.py         # ✅ Modal simple
└── ogma_hooks.py          # ✅ Intégration header

# Tests visuels
- Bouton s'affiche correctement
- Modal s'ouvre/ferme
- Styles cohérents OGMA
```

### **5. Contexte Matinal (Jour 12-13)**
```python
# Priorité 5: Valeur utilisateur immédiate
├── context_provider.py    # ✅ Injection contexte
├── conversation_hooks.py  # ✅ Hooks début conversation
└── context_formatter.py   # ✅ Formatage contexte

# Validation utilisateur
- Contexte pertinent affiché
- Performance acceptable
- Intégration naturelle
```

---

## 🛡️ **Bonnes Pratiques Identifiées**

### **✅ À REPRODUIRE (cognitive_mirror success patterns)**

#### **1. Architecture Modulaire Claire**
```python
# Pattern réussi: séparation des responsabilités
class JournalCore:           # Orchestration générale
class JSONManager:           # Persistance pure
class EntryGenerator:        # Logique IA
class UIComponents:          # Interface utilisateur
class ContextProvider:       # Injection contexte
```

#### **2. Configuration Centralisée**
```python
# Pattern réussi: config.py avec validation
class JournalConfig:
    DEFAULT_SETTINGS = {
        "auto_context_display": True,
        "summary_min_tokens": 200,
        "summary_max_tokens": 400,
        # ... paramètres avec valeurs par défaut
    }
    
    def get_required(self, key: str):
        """Validation stricte sans fallbacks"""
        if key not in self.current_settings:
            raise ValueError(f"Paramètre obligatoire manquant: '{key}'")
        return self.current_settings[key]
```

#### **3. Singleton Pattern Robuste**
```python
# Pattern réussi: instance globale contrôlée
_journal_instance = None

def get_journal() -> JournalCore:
    """Retourne l'instance singleton"""
    global _journal_instance
    if _journal_instance is None:
        raise RuntimeError("Journal non initialisé - appelez initialize_journal() d'abord")
    return _journal_instance
```

#### **4. Hooks Non-Invasifs**
```python
# Pattern réussi: intégration propre dans OGMA
def _inject_journal_hooks():
    """Ajoute les hooks sans modifier le core"""
    
    # Hook header: ajout bouton
    original_header = ogma_ng._header
    def enhanced_header():
        original_header()
        _add_journal_button()
    ogma_ng._header = enhanced_header
    
    # Hook conversation: injection contexte
    original_send = ogma_ng._send_chat_message
    async def enhanced_send(input_el):
        await _inject_daily_context()
        return await original_send(input_el)
    ogma_ng._send_chat_message = enhanced_send
```

### **❌ À ÉVITER ABSOLUMENT (cognitive_mirror pitfalls)**

#### **1. Arrêt de Surveillance Critique**
```python
# ❌ PIÈGE ÉVITÉ: Ne jamais couper la surveillance en cours d'utilisation
# Dans cognitive_mirror: arrêt du monitoring bloquait la détection d'activité

def start_conversation_tracking(self):
    """CORRECT: maintenir la surveillance pendant utilisation"""
    # Ne PAS arrêter le monitoring existant
    # self.stop_monitoring()  # ❌ ERREUR cognitive_mirror
    
    # ✅ CORRECT: ajouter tracking sans couper existant
    self.conversation_active = True
    self.track_current_conversation()
```

#### **2. Vérifications enabled Bloquantes**
```python
# ❌ PIÈGE ÉVITÉ: Vérification enabled qui bloque fonctionnalités critiques

def save_entry(self, entry_data: dict):
    """CORRECT: sauvegarder même si extension temporairement désactivée"""
    
    # ❌ ERREUR cognitive_mirror pattern
    # if not self.is_enabled():
    #     return False
    
    # ✅ CORRECT: toujours sauvegarder les données importantes
    return self.json_manager.save_entry(entry_data)
```

#### **3. Fallbacks Masquants**
```python
# ❌ PIÈGE ÉVITÉ: Fallbacks qui masquent les vrais problèmes

def get_archiviste_summary(self, conversation_data: dict):
    """CORRECT: gestion d'erreur explicite sans fallback"""
    
    try:
        summary = self.archiviste.generate_summary(conversation_data)
        if not summary:
            raise ValueError("Archiviste retourné résumé vide")
        return summary
    except Exception as e:
        # ✅ CORRECT: erreur explicite
        raise RuntimeError(f"Échec génération résumé: {e}")
        
        # ❌ ERREUR cognitive_mirror pattern
        # return "Résumé par défaut"  # Masque le problème !
```

#### **4. Modifications DEFAULT_SETTINGS**
```python
# ❌ PIÈGE ÉVITÉ: Modifier DEFAULT_SETTINGS ne sauvegarde pas

def update_setting(self, key: str, value: Any):
    """CORRECT: utiliser la méthode de sauvegarde"""
    
    # ❌ ERREUR cognitive_mirror pattern
    # self.config.DEFAULT_SETTINGS[key] = value  # Ne sauvegarde PAS !
    
    # ✅ CORRECT: méthode qui sauvegarde réellement
    self.config.set(key, value)  # Sauvegarde dans le fichier JSON
```

---

## 🧪 **Stratégie de Tests**

### **Tests par Phase**
```python
# Phase 1: Tests Fondations
def test_config_loading():
    """Configuration se charge correctement"""
    
def test_singleton_pattern():
    """Une seule instance du journal"""
    
def test_json_operations():
    """CRUD operations JSON"""

# Phase 2: Tests UI
def test_header_button():
    """Bouton apparaît dans header"""
    
def test_modal_operations():
    """Modal s'ouvre/ferme correctement"""
    
def test_context_injection():
    """Contexte injecté en début conversation"""

# Phase 3: Tests Intégration
def test_archiviste_integration():
    """Génération résumés fonctionne"""
    
def test_ogma_compatibility():
    """Pas de conflit avec autres extensions"""
    
def test_performance_benchmarks():
    """Respect des objectifs performance"""
```

### **Validation Utilisateur Continue**
```python
# Tests utilisateur à chaque milestone
def validate_phase_1():
    """L'utilisateur peut configurer l'extension"""
    
def validate_phase_2():
    """L'utilisateur voit le bouton et peut créer une entrée"""
    
def validate_phase_3():
    """L'utilisateur voit le contexte matinal utile"""
```

---

## 🚀 **Points de Validation Critiques**

### **Checkpoint 1 (Jour 7): Fondations**
- [ ] Configuration charge sans erreur
- [ ] JSON Manager crée/lit/écrit correctement
- [ ] Tests unitaires passent (>95%)
- [ ] Performance JSON acceptable (<50ms)

### **Checkpoint 2 (Jour 14): Interface**
- [ ] Bouton apparaît dans header OGMA
- [ ] Modal s'ouvre avec contenu
- [ ] Génération résumé Archiviste fonctionne
- [ ] Utilisateur peut créer une entrée manuellement

### **Checkpoint 3 (Jour 21): Production**
- [ ] Contexte matinal s'affiche automatiquement
- [ ] Performance globale respectée
- [ ] Intégration OGMA complète sans conflit
- [ ] Documentation utilisateur terminée

---

## 🔧 **Outils de Développement**

### **Environnement de Dev**
```python
# Structure pour développement efficace
tools/
├── dev_server.py          # Serveur de dev avec hot reload
├── test_runner.py         # Runner de tests avec coverage
├── performance_profiler.py # Profiling performance
└── data_generator.py      # Génération données de test
```

### **Scripts d'Aide**
```bash
# Scripts de développement
./tools/dev_server.py      # Lance OGMA en mode dev
./tools/test_all.py        # Lance tous les tests
./tools/profile.py         # Profile les performances
./tools/validate.py        # Validation complète
```

---

## 📚 **Documentation Continue**

### **Documentation Code**
```python
# Standard de documentation
class JournalCore:
    """
    Moteur principal du journal de bord OGMA.
    
    Responsabilités:
    - Orchestration des composants journal
    - Interface publique pour OGMA
    - Gestion du cycle de vie de l'extension
    
    Usage:
        journal = JournalCore()
        journal.initialize(archiviste, memory_manager)
        context = journal.get_today_context()
    
    Performance:
        - Cold start: <100ms
        - Context retrieval: <20ms
        - Entry creation: <3s (avec Archiviste)
    """
```

### **Documentation Utilisateur**
```markdown
# Documentation en parallèle du développement
├── USER_GUIDE.md          # Guide utilisateur simple
├── FAQ.md                 # Questions fréquentes
├── TROUBLESHOOTING.md     # Résolution problèmes
└── EXAMPLES.md            # Exemples d'utilisation
```

---

## 🎯 **Définition of Done**

### **Critères d'Acceptation par Fonctionnalité**

#### **Configuration**
- [ ] Fichier config.json créé automatiquement
- [ ] Paramètres modifiables depuis interface
- [ ] Validation des valeurs utilisateur
- [ ] Sauvegarde automatique des changements

#### **Persistance JSON**
- [ ] Structure hiérarchique année/mois/jour
- [ ] Sauvegarde atomique (pas de corruption)
- [ ] Index de recherche maintenu
- [ ] Performance <50ms pour 1000+ entrées

#### **Génération Résumés**
- [ ] Intégration Archiviste fonctionnelle
- [ ] Résumés 200-400 tokens
- [ ] Gestion timeouts et erreurs
- [ ] Tags automatiques extraits

#### **Interface Utilisateur**
- [ ] Bouton header style OGMA
- [ ] Modal responsive et accessible
- [ ] Navigation calendrier intuitive
- [ ] Contexte matinal non-intrusif

#### **Intégration OGMA**
- [ ] Hooks non-invasifs
- [ ] Pas de conflit autres extensions
- [ ] Performance globale maintenue
- [ ] Compatibilité versions futures

---

**Version Guide** : 1.0.0  
**Dernière mise à jour** : 2024-09-28  
**Auteur** : Équipe OGMA  
**Statut** : Guide finalisé, prêt pour développement