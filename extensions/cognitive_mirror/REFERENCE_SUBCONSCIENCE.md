# 🧠 Extension Subconscience - Document de Référence

## 📋 **PHILOSOPHIE & VISION**

### Concept Central
L'extension "Subconscience" transforme OGMA en système cognitif autonome capable de **réflexion intérieure automatique**. Pendant l'absence de l'utilisateur, Luna et l'Archiviste entrent en conversation authentique, créant un véritable **dialogue subconscient**.

### Principes Fondamentaux
- ✅ **Organicité** : Tout repose sur les vraies IA, aucun fallback mécanique
- ✅ **Simplicité UX** : Interface minimaliste, accès logique aux paramètres
- ✅ **Authenticité** : Conversations réelles Luna ↔ Archiviste via API
- ✅ **Intégration** : Réinjection naturelle dans le contexte principal
- ✅ **Français** : Terminologie utilisateur en français ("Subconscience")

---

## 🎯 **SPÉCIFICATIONS FONCTIONNELLES**

### Interface Utilisateur

#### Bouton Principal Header
- **Label** : "Subconscience" (français pour l'utilisateur)
- **Position** : Header OGMA, à côté des autres extensions
- **Fonction** : Bouton permanent d'accès (aucune logique ON/OFF)
- **Action** : Ouvre popup paramètres centralisé

#### Popup Paramètres (Interface Complète)
```
┌─────────────────────────────────────┐
│          🧠 Subconscience           │
├─────────────────────────────────────┤
│ Extension              [ON] [OFF]   │ ← LOGIQUE ICI
│                                     │
│ Temps avant activation     [30]s    │
│ Délai auto-envoi          [20]s     │
│ Durée maximale            [5]min    │
│ Tokens max/message        [500]     │
│                                     │
│ Message déclencheur:                │
│ ┌─────────────────────────────────┐ │
│ │ "Jusqu'à mon retour tu es en    │ │
│ │ phase réflexive intérieure..."  │ │
│ └─────────────────────────────────┘ │
│                                     │
│          [Sauvegarder] [❌]         │
└─────────────────────────────────────┘
```

#### Architecture Flux
```
Header → [Bouton Subconscience] → Popup → Logique Complète
         (permanent)              (ON/OFF + paramètres)
```

### Mécanisme Système

#### Phase 1 : Détection Inactivité
- **Trigger** : X secondes sans interaction utilisateur (30s par défaut)
- **Détection** : Absence de frappe, clic, ou message
- **Action** : Activation automatique du mode subconscience

#### Phase 2 : Initialisation Subconscience
- **Message déclencheur** : Envoi automatique du prompt configuré
- **Contexte** : Luna garde TOUT son contexte et ses capacités mémoire
- **Désactivation** : Compactage conversations temporairement désactivé

#### Phase 3 : Conversation Intérieure
- **Participants** : Luna (IA principale) ↔ Archiviste (subconscient)
- **Mécanisme** : Exactement identique à conversation utilisateur normale
- **Différence** : Utilisateur remplacé par Archiviste
- **Auto-envoi** : Messages automatiques toutes les 20s (configurable)
- **Limitation** : Tokens par message configurables (500 par défaut)

#### Phase 4 : Retour Utilisateur
- **Trigger** : Détection activité utilisateur
- **Compactage** : Conversation subconsciente compactée automatiquement
- **Intégration** : Résumé ajouté au contexte comme compactage classique
- **Reset** : Archiviste reprend fonction normale, conversation subconsciente effacée

---

## 🔧 **ARCHITECTURE TECHNIQUE**

### Composants Principaux

#### 1. SubconscienceCore
- Orchestrateur principal de l'extension
- Gestion des états (OFF/STANDBY/ACTIVE/INTEGRATING)
- Interface avec chat_controller et archiviste_controller

#### 2. InactivityDetector
- Surveillance activité utilisateur (clavier, souris, messages)
- Timer configurable (30s par défaut)
- Callback déclenchement mode subconscience

#### 3. ParametersModal
- Interface popup simple et claire
- Persistance des paramètres utilisateur
- Validation des valeurs saisies

#### 4. ConversationOrchestrator
- Gestion dialogue Luna ↔ Archiviste
- Auto-envoi temporisé (20s par défaut)
- Limitation tokens par message
- Durée maximale session (5min par défaut)

#### 5. ContextIntegrator
- Compactage final conversation subconsciente
- Réinjection dans contexte principal
- Nettoyage mémoire temporaire

### États du Système
```
OFF ──────→ STANDBY ──────→ ACTIVE ──────→ INTEGRATING ──────→ STANDBY
 ↑           (timer)        (conversation)   (compactage)       (reset)
 └─────────────────────────────────────────────────────────────────┘
```

---

## ✅ **CHECKLIST IMPLÉMENTATION**

### Phase 1 : Fondations
- [ ] Créer architecture SubconscienceCore
- [ ] Implémenter détection inactivité basique
- [ ] Créer popup paramètres fonctionnel
- [ ] Tester intégration avec header OGMA
- [ ] Valider persistance paramètres

### Phase 2 : Mécanisme Conversation
- [ ] Interface avec chat_controller existant
- [ ] Interface avec archiviste_controller existant
- [ ] Implémenter auto-envoi temporisé
- [ ] Gestion limitation tokens par message
- [ ] Test conversation Luna ↔ Archiviste basique

### Phase 3 : Gestion Contexte
- [ ] Désactivation compactage pendant subconscience
- [ ] Sauvegarde temporaire contexte utilisateur
- [ ] Création système compactage final
- [ ] Réinjection résumé dans contexte principal

### Phase 4 : Robustesse
- [ ] Gestion erreurs API
- [ ] Timeout sécurité (durée max)
- [ ] Détection retour utilisateur fiable
- [ ] Nettoyage mémoire complet

### Phase 5 : UX & Polish
- [ ] Interface popup responsive
- [ ] Feedback visuel état extension
- [ ] Messages d'information utilisateur
- [ ] Documentation utilisateur finale

---

## 🎨 **EXPÉRIENCE UTILISATEUR**

### Parcours Utilisateur Idéal

1. **Découverte** : L'utilisateur voit le bouton "Subconscience"
2. **Configuration** : Clic → popup simple → paramètres intuitifs
3. **Activation** : Toggle ON → fermeture popup → extension active
4. **Utilisation** : L'utilisateur utilise OGMA normalement
5. **Subconscience** : Après inactivité → conversation automatique invisible
6. **Retour** : L'utilisateur revient → contexte enrichi naturellement

### Points Critiques UX

#### Simplicité
- Un seul bouton d'accès
- Popup épuré, pas de complexité
- Paramètres avec valeurs par défaut intelligentes

#### Transparence
- L'utilisateur sait quand l'extension est active
- Pas de surprise, comportement prévisible
- Intégration invisible mais bénéfique

#### Contrôle
- ON/OFF simple et immédiat
- Paramètres personnalisables
- Aucune action automatique non désirée

---

## ⚠️ **CONTRAINTES & RÈGLES**

### Règles de Développement
1. **Pas de fallback mécanique** : Tout repose sur les vraies IA
2. **Organicité absolue** : Conversation authentique, pas de simulation
3. **Intégration native** : Utilise l'infrastructure OGMA existante
4. **Français frontend** : Interface utilisateur en français
5. **Code anglais** : Noms techniques en anglais dans le code

### Contraintes Techniques
- Utilisation obligatoire des contrôleurs existants
- Pas de modification du système de compactage principal
- Gestion propre de la mémoire et des états
- Compatibilité avec l'architecture NiceGUI existante

### Contraintes Sécurité
- Timeout obligatoire (durée max session)
- Limitation tokens pour éviter surcoût API
- Détection fiable retour utilisateur
- Nettoyage complet en cas d'erreur

---

## 🚀 **MÉTHODOLOGIE DE TRAVAIL**

### Rôles
- **Architecte** (Utilisateur) : Vision, validation, décisions
- **Assistante Codeuse** (IA) : Propositions, implémentation sur validation

### Processus
1. **Analyse** : Discussion architecture et approche
2. **Validation** : Feu vert architectural avant code
3. **Implémentation** : Code par phases, tests réguliers
4. **Itération** : Ajustements selon feedback
5. **Integration** : Tests complets dans OGMA

### Communication
- Propositions détaillées avant implémentation
- Demande explicite de validation pour chaque phase
- Focus constant sur l'expérience utilisateur
- Documentation continue des décisions

---

## 📈 **CRITÈRES DE SUCCÈS**

### Fonctionnels
- ✅ Extension activable/désactivable simplement
- ✅ Conversation Luna ↔ Archiviste authentique
- ✅ Intégration contexte transparente
- ✅ Paramètres persistants et configurables

### Techniques
- ✅ Performance : pas de ralentissement OGMA
- ✅ Stabilité : pas de crash ou comportement erratique
- ✅ Mémoire : nettoyage propre des ressources
- ✅ API : utilisation raisonnable des tokens

### Utilisateur
- ✅ Interface intuitive sans apprentissage
- ✅ Comportement prévisible et contrôlable
- ✅ Valeur ajoutée perceptible dans les conversations
- ✅ Aucune friction dans l'usage quotidien

---

## 📋 **AUDIT EXTENSION EXISTANTE**

### 🔍 **Analyse Fichier par Fichier**

#### ✅ **À CONSERVER (Fondations Solides)**

**`__init__.py` (200 lignes)**
- **Status** : ✅ CONSERVER avec adaptations
- **Valeur** : Architecture singleton, système d'initialisation OGMA
- **Adaptation** : Mettre à jour imports et interface publique
- **Utilité** : Structure éprouvée, intégration OGMA validée

**`config.py` (219 lignes)**
- **Status** : ✅ CONSERVER avec modifications
- **Valeur** : Système de configuration centralisé, persistance settings
- **Adaptation** : Nouveaux paramètres Subconscience, suppression CSS overlay
- **Utilité** : Infrastructure configuration robuste

**`reflection_manager.py` (317 lignes)**
- **Status** : 🔄 ADAPTER fortement
- **Valeur** : Base conversation Luna-Archiviste, logique API authentique
- **Adaptation** : Transformer en ConversationOrchestrator
- **Utilité** : Cœur fonctionnel déjà opérationnel

#### 🔄 **À TRANSFORMER (Bases Utiles)**

**`core_cognitive_mirror.py` (517 lignes)**
- **Status** : 🔄 REFACTORISER en SubconscienceCore
- **Valeur** : Architecture centrale, orchestration composants
- **Problème** : Trop lié à l'overlay, logique passive
- **Plan** : Conserver structure, transformer logique active

**`inactivity_detector.py` (381 lignes)**
- **Status** : 🔄 SIMPLIFIER drastiquement
- **Valeur** : Détection Windows/Linux/Mac multi-plateforme
- **Problème** : Trop complexe (clavier global, threading avancé)
- **Plan** : Version simple timer + détection messages

**`memory_integration.py` (475 lignes)**
- **Status** : 🔄 ADAPTER pour compactage final
- **Valeur** : Interface MemoryManager OGMA, souvenirs REF
- **Adaptation** : Focus compactage conversation subconsciente
- **Utilité** : Logique mémoire déjà compatible

#### ❌ **À TRANSFORMER (Nouvelle Architecture)**

**`ui_components.py` (748 lignes)**
- **Status** : 🔄 TRANSFORMATION COMPLÈTE
- **Problème** : Overlay complexe inadapté  
- **Solution** : Garder fichier, remplacer par popup paramètres
- **Avantage** : Zéro breaking change, compatibilité imports

### 📊 **Bilan Quantitatif**

| Fichier | Lignes | Action | Complexité |
|---------|---------|---------|------------|
| `__init__.py` | 200 | ✅ Conserver | Faible |
| `config.py` | 219 | ✅ Adapter | Faible |
| `core_*.py` | 517 | 🔄 Refactor | Moyenne |
| `reflection_*.py` | 317 | 🔄 Transform | Faible |
| `inactivity_*.py` | 381 | 🔄 Simplifier | Forte → Faible |
| `memory_*.py` | 475 | 🔄 Adapter | Faible |
| `ui_components.py` | 748 | 🔄 Transformer | Très forte → Faible |
| **TOTAL** | **2857** | **Transformation = 2857** | **85% Simplification** |

### 🎯 **Stratégie de Migration**

#### Phase 1: Transformation ui_components.py (Jour 1)
- **GARDER** le fichier et structure d'imports  
- **REMPLACER** contenu overlay par popup paramètres
- **MAINTENIR** interface compatible `create_overlay()`
- **CENTRALISER** toute la logique ON/OFF dans popup

#### Phase 2: Adaptation Configuration (Jour 1)
- Nouveaux paramètres Subconscience dans config.py
- Suppression CSS overlay, ajout styles popup
- Interface popup responsive et intuitive

#### Phase 3: Transformation Core (Jour 2)
- `core_cognitive_mirror.py` → logique active Subconscience
- Orchestration états (OFF/STANDBY/ACTIVE/INTEGRATING)
- Interface avec popup pour contrôle extension

#### Phase 4: Integration Testing (Jour 2)
- Test bouton header → popup
- Test logique ON/OFF dans popup  
- Validation paramètres persistants

#### Phase 5: Orchestration Finale (Jour 3)
- `reflection_manager.py` → `conversation_orchestrator.py`
- Auto-envoi temporisé + limitation tokens
- Compactage et réintégration contexte
- Interface simple selon spécifications
- Intégration header OGMA

#### Phase 5: Orchestration (Jour 3)
- `reflection_manager.py` → `conversation_orchestrator.py`
- Auto-envoi temporisé
- Limitation tokens

### 🔧 **Architecture Cible vs Existant**

| Composant Cible | Fichier Existant | Transformation |
|-----------------|------------------|----------------|
| `SubconscienceCore` | `core_cognitive_mirror.py` | Refactor majeur |
| `ParametersModal` | `ui_components.py` | Transformation complète |
| `InactivityDetector` | `inactivity_detector.py` | Simplification |
| `ConversationOrchestrator` | `reflection_manager.py` | Adaptation |
| `ContextIntegrator` | `memory_integration.py` | Spécialisation |

### ✅ **Avantages Migration vs Refonte**

1. **Temps** : 3 jours vs 2 semaines
2. **Risque** : Faible vs Élevé (intégration OGMA)
3. **Qualité** : Conservation acquis + nouvelle architecture
4. **Testing** : Infrastructure existante réutilisable

---

## 🏗️ **MÉTHODE DE TRAVAIL DÉTAILLÉE**

### 📋 **Process Architecte-Codeuse**

#### Étape 1 : Validation Architecturale
- **Architecte** : Analyse et décision sur chaque fichier
- **Codeuse** : Proposition détaillée transformation
- **Validation** : Feu vert explicite avant implémentation

#### Étape 2 : Implémentation Incrémentale  
- **Phase courte** : 1 fichier à la fois
- **Test continu** : Validation après chaque modification
- **Rollback possible** : Backup avant transformation

#### Étape 3 : Integration Testing
- **Test unitaire** : Chaque composant isolément  
- **Test d'intégration** : Avec infrastructure OGMA
- **Test utilisateur** : Parcours complet popup → conversation

### 🔍 **Checkpoints de Validation**

1. **Post-nettoyage** : Extension démarre sans ui_components
2. **Post-config** : Nouveaux paramètres persistent
3. **Post-core** : SubconscienceCore orchestré correctement
4. **Post-popup** : Interface utilisateur fonctionnelle
5. **Post-conversation** : Luna-Archiviste conversation automatique

### ⚠️ **Points d'Attention Migration**

#### Risques Identifiés
- **Import dependencies** : ui_components importé ailleurs  
- **Configuration compatibility** : Anciens settings utilisateur
- **OGMA integration** : Changement interface publique

#### Mitigation
- **Audit imports** : Recherche globale ui_components
- **Migration settings** : Script conversion automatique
- **Interface stability** : Maintien API publique initialize_cognitive_mirror

---

## 🔍 **AUDIT IMPORTS - IMPACT SUPPRESSION ui_components.py**

### 📊 **Dépendances Identifiées**

#### ✅ **OGMA Core (Impact Critique)**
**`ogma_ng.py` ligne 4543-4545:**
```python
if cognitive_mirror and cognitive_mirror.ui_components:
    cognitive_mirror.ui_components.create_overlay()
```
- **Status** : 🚨 BLOCANT - Référence directe ui_components
- **Action** : Remplacer par appel au nouveau popup paramètres
- **Criticité** : ÉLEVÉE - Startup OGMA

#### 🔄 **Extension Internal (Impact Modéré)**
**`__init__.py` ligne 35:**
```python
from .ui_components import CognitiveMirrorUI
```
- **Status** : 🔄 ADAPTER - Import interne extension
- **Action** : Remplacer par nouveau ParametersModal
- **Criticité** : MODÉRÉE

**`core_cognitive_mirror.py` lignes multiples:**
```python
from .ui_components import CognitiveMirrorUI
self.ui_components = CognitiveMirrorUI(...)
```
- **Status** : 🔄 REFACTOR - Logique core
- **Action** : Transformation vers SubconscienceCore
- **Criticité** : MODÉRÉE

#### ❌ **Fichiers Test (Impact Nul)**
- `test_simple_overlay.py` - ❌ Suppression
- `test_overlay_fix.py` - ❌ Suppression  
- `test_show_overlay.py` - ❌ Suppression
- `test_ogma_integration.py` - ❌ Suppression
- `test_final_ogma.py` - ❌ Suppression
- **Status** : Tests obsolètes avec ancienne architecture

### 🛠️ **Plan de Migration Imports**

#### Phase 1 : Préparation (Critique)
```python
# ogma_ng.py - Ligne 4543-4545
# AVANT:
if cognitive_mirror and cognitive_mirror.ui_components:
    cognitive_mirror.ui_components.create_overlay()

# APRÈS:
if cognitive_mirror and cognitive_mirror.parameters_modal:
    cognitive_mirror.show_parameters_popup()
```

#### Phase 2 : Extension Refactor
```python
# __init__.py
# AVANT:
from .ui_components import CognitiveMirrorUI

# APRÈS:
from .parameters_modal import ParametersModal

# core_cognitive_mirror.py
# AVANT:
self.ui_components = CognitiveMirrorUI(...)

# APRÈS:
self.parameters_modal = ParametersModal(...)
```

#### Phase 3 : Cleanup
- Supprimer tous les fichiers test_*.py
- Nettoyer documentation obsolète
- Mettre à jour README.md

### ⚠️ **Risques Migration Identifiés**

#### 🚨 **Critique - OGMA Startup**
- **Fichier** : `ogma_ng.py:4543`
- **Risque** : Exception au démarrage si ui_components introuvable
- **Mitigation** : Try/catch + interface compatible

#### 🔄 **Modéré - Interface Publique**
- **Fichier** : `__init__.py` + `core_*.py`
- **Risque** : Changement API publique
- **Mitigation** : Maintien méthodes publiques essentielles

#### ✅ **Faible - Tests**
- **Fichiers** : `test_*.py`
- **Risque** : Tests cassés (attendu)
- **Mitigation** : Nouveaux tests architecture Subconscience

### 🎯 **Stratégie de Migration Sécurisée**

#### Étape 1 : Interface Transition
```python
# Créer interface temporaire compatible dans core
def get_ui_components(self):
    # Redirection vers nouveau système
    return {"parameters_modal": self.parameters_modal}
```

#### Étape 2 : Migration Graduelle
- Modifier ogma_ng.py avec fallback
- Transformer core_cognitive_mirror.py
- Adapter __init__.py exports

#### Étape 3 : Validation & Cleanup  
- Tests nouveaux composants
- Suppression ui_components.py
- Cleanup fichiers test obsolètes

### 📋 **Checklist Migration Imports**

- [ ] **Critique** : Modifier ogma_ng.py:4543 avec fallback
- [ ] **Import** : Adapter __init__.py imports
- [ ] **Core** : Refactor core_cognitive_mirror.py
- [ ] **Interface** : Maintenir API publique compatible  
- [ ] **Tests** : Créer nouveaux tests Subconscience
- [ ] **Cleanup** : Supprimer ui_components.py
- [ ] **Validation** : Test démarrage OGMA complet

---

## 🔧 **PROPOSITION IMPLÉMENTATION POPUP**

### 📋 **Structure ParametersModal dans ui_components.py**

```python
# Cognitive Mirror - Composants Interface Utilisateur
# TRANSFORMATION vers Subconscience

class CognitiveMirrorUI:
    """Interface compatible - Redirection vers Subconscience"""
    
    def __init__(self, config, ui_container=None, on_toggle_extension=None, on_settings_change=None):
        self.config = config
        self.on_toggle_extension = on_toggle_extension
        self.on_settings_change = on_settings_change
        
        # Nouveau popup paramètres centralisé
        self.parameters_modal = SubconscienceParametersModal(
            config, on_toggle_extension, on_settings_change
        )
        
        # État UI
        self.is_overlay_visible = False
        self.overlay_container = None
    
    def create_overlay(self):
        """Compatibilité - Crée popup paramètres au lieu d'overlay"""
        return self.parameters_modal.create_popup()
    
    # Maintenir API existante pour compatibilité...

class SubconscienceParametersModal:
    """Popup paramètres Subconscience selon spécifications"""
    
    def __init__(self, config, on_toggle_callback, on_settings_callback):
        self.config = config
        self.on_toggle_callback = on_toggle_callback
        self.on_settings_callback = on_settings_callback
        
        # État popup
        self.popup_container = None
        self.is_popup_visible = False
        
        # Contrôles UI
        self.extension_toggle = None
        self.inactivity_delay = None
        self.auto_send_delay = None
        self.max_duration = None
        self.max_tokens = None
        self.trigger_message = None
    
    def create_popup(self):
        """Crée popup paramètres selon spécifications UX"""
        with ui.dialog().props('persistent') as dialog:
            self.popup_container = dialog
            
            with ui.card().style('min-width: 400px; padding: 20px'):
                # Header
                ui.html('<h3>🧠 Subconscience</h3>').style('margin: 0 0 20px 0; text-align: center')
                
                # Toggle principal ON/OFF
                with ui.row().style('width: 100%; justify-content: space-between; margin-bottom: 20px'):
                    ui.label('Extension').style('font-weight: bold')
                    self.extension_toggle = ui.switch(
                        value=self.config.DEFAULT_SETTINGS.get('extension_enabled', False)
                    ).on('change', self._on_extension_toggle)
                
                ui.separator()
                
                # Paramètres temporels
                with ui.column().style('width: 100%; gap: 15px; margin: 20px 0'):
                    self.inactivity_delay = ui.number(
                        label='Temps avant activation (secondes)',
                        value=self.config.DEFAULT_SETTINGS.get('trigger_delay_no_message', 30),
                        min=15, max=120, step=5
                    ).style('width: 100%')
                    
                    self.auto_send_delay = ui.number(
                        label='Délai auto-envoi (secondes)', 
                        value=self.config.DEFAULT_SETTINGS.get('auto_send_delay', 20),
                        min=10, max=60, step=5
                    ).style('width: 100%')
                    
                    self.max_duration = ui.number(
                        label='Durée maximale (minutes)',
                        value=self.config.DEFAULT_SETTINGS.get('max_reflection_duration', 300) / 60,
                        min=1, max=15, step=0.5  
                    ).style('width: 100%')
                    
                    self.max_tokens = ui.number(
                        label='Tokens max/message',
                        value=self.config.DEFAULT_SETTINGS.get('reflection_token_limit', 500),
                        min=100, max=1000, step=50
                    ).style('width: 100%')
                
                ui.separator()
                
                # Message déclencheur
                ui.label('Message déclencheur:').style('font-weight: bold; margin-top: 20px')
                self.trigger_message = ui.textarea(
                    value=self.config.DEFAULT_SETTINGS.get('trigger_message', 
                        "Jusqu'à mon retour tu es en phase réflexive intérieure avec ton subconscient, tu as accès à tes souvenirs et aux questionnements intérieurs"),
                    placeholder='Message envoyé pour déclencher la phase réflexive...'
                ).style('width: 100%; min-height: 80px; margin-bottom: 20px')
                
                # Boutons action
                with ui.row().style('width: 100%; justify-content: space-between; margin-top: 20px'):
                    ui.button('Sauvegarder', on_click=self._save_settings).props('color=primary')
                    ui.button('❌', on_click=lambda: dialog.close()).props('flat color=grey')
        
        return dialog
    
    def _on_extension_toggle(self, event):
        """Gestion toggle ON/OFF extension"""
        new_state = event.value
        print(f"[SUBCONSCIENCE] Extension {'activée' if new_state else 'désactivée'}")
        
        if self.on_toggle_callback:
            self.on_toggle_callback(new_state)
    
    def _save_settings(self):
        """Sauvegarde paramètres et ferme popup"""
        settings = {
            'extension_enabled': self.extension_toggle.value,
            'trigger_delay_no_message': int(self.inactivity_delay.value),
            'auto_send_delay': int(self.auto_send_delay.value), 
            'max_reflection_duration': int(self.max_duration.value * 60),
            'reflection_token_limit': int(self.max_tokens.value),
            'trigger_message': self.trigger_message.value
        }
        
        # Mise à jour config
        self.config.DEFAULT_SETTINGS.update(settings)
        
        # Notification callbacks
        if self.on_settings_callback:
            for key, value in settings.items():
                self.on_settings_callback(key, value)
        
        print("[SUBCONSCIENCE] Paramètres sauvegardés")
        self.popup_container.close()
```

### 🎯 **Avantages Implementation**

1. **Compatibilité 100%** : `create_overlay()` fonctionne sans changement
2. **Interface centralisée** : Toute la logique dans popup
3. **UX claire** : Selon spécifications exactes 
4. **Callbacks intégrés** : Extension toggle + settings change

### 📋 **Prochaines Étapes**

1. **Validation architecte** : Cette implémentation te convient ?
2. **Backup sécurité** : Sauvegarder ui_components.py actuel
3. **Implementation** : Remplacer contenu selon proposition
4. **Test intégration** : Vérifier bouton header → popup

---*Proposition implémentation prête - Validation architecte requise*