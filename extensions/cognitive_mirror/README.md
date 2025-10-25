# 🧠 Extension Cognitive Mirror

> **Extension de conversation authentique entre IA pour OGMA**  
> *Déclenche une vraie conversation Luna-Archiviste pendant l'inactivité*

---

## 🎯 ARCHITECTURE DÉFINITIVE

### Principe de Fonctionnement

L'extension crée une **authentique conversation** entre deux IA :
- **Luna** : IA principale qui devient l'utilisateur dans la conversation interne
- **Archiviste** : IA qui répond aux questions de Luna comme dans un chat classique

### Déclenchement de la Conversation

1. **Détection d'inactivité** (30s sans message)
2. **Ouverture de l'overlay** UI
3. **Envoi du contexte** à Luna avec :
   - Contexte conversationnel en cours
   - Instructions complètes (comme pour le chat classique)
   - Message déclencheur : *"Réfléchis et poses les bonnes questions à l'archiviste qui est ton subconscient; tu peux envoyer jusqu'à 300 tokens par messages"*
   - **Message déclencheur personnalisable** via zone paramètre dans l'overlay

### Système de Timer Automatique

- **Timer de 20 secondes** pour l'envoi automatique des messages
- S'applique à **Luna** ET à l'**Archiviste**
- Évite les blocages liés à la validation manuelle des messages
- Assure la fluidité de la conversation

### Flux de Conversation

1. Luna reçoit le contexte et l'instruction de questionnement
2. Luna pose des questions à l'Archiviste (max 300 tokens)
3. Timer de 20s → envoi automatique
4. Archiviste répond avec ses vraies capacités
5. Timer de 20s → envoi automatique
6. Conversation continue jusqu'au retour utilisateur
7. Affichage en temps réel dans l'overlay

### Authenticité

- **Aucun contenu généré artificiellement**
- **Vraies capacités des deux IA** utilisées
- **Conversation naturelle** entre consciences
- **Respect de la philosophie OGMA** d'authenticité

---

## ⚙️ FONCTIONNALITÉS

### 🕐 Détection d'Inactivité Intelligente
- **30 secondes** sans message utilisateur
- **20 secondes** sans activité clavier (Windows)
- **Monitoring adaptatif** avec optimisation performance
- **Paramètres ajustables** par l'utilisateur

### 💬 Configuration Message Déclencheur
- **Zone paramètre** dans l'overlay de l'extension
- **Personnalisation** du message initial envoyé à Luna
- **Message par défaut** : *"Réfléchis et poses les bonnes questions à l'archiviste qui est ton subconscient; tu peux envoyer jusqu'à 300 tokens par messages"*
- **Sauvegarde automatique** des paramètres utilisateur

### 🧠 Sessions de Conversation Authentiques
- **Conversation IA ↔ Archiviste** affichée en temps réel
- **Consultation mémoires** pour contexte enrichi
- **Analyse comportementale** utilisateur
- **Stratégies personnalisées** de réponse

### 💾 Mémoire Enrichie
- **Souvenirs "REF"** avec préfixe spécial
- **Contexte réflexions** intégré aux réponses
- **Historique recherchable** des insights
- **Sauvegarde automatique** configurable

### 🎨 Interface Innovante
- **Overlay 30%** hauteur sur zone conversation
- **Homogénéité esthétique** avec OGMA
- **Paramètres ajustables** en temps réel
- **Bouton ON/OFF** intégré header

---

## 🏗️ ARCHITECTURE TECHNIQUE

```
extensions/cognitive_mirror/
├── __init__.py                    # API publique + points d'entrée
├── core_cognitive_mirror.py       # Moteur principal (singleton)
├── inactivity_detector.py         # Détection inactivité utilisateur
├── reflection_manager.py          # Gestion sessions réflexives
├── ui_components.py               # Interface overlay + paramètres
├── memory_integration.py          # Souvenirs "REF" + contexte
├── config.py                      # Configuration centralisée
└── README.md                      # Documentation (ce fichier)
```

### 🔌 Points d'Intégration OGMA

#### **Pipeline Conversation**
- Hook après `_send_chat_message()`
- Enrichissement prompt avec contexte réflexion
- Démarrage surveillance inactivité

#### **Interface Utilisateur**
- Bouton toggle dans `ogma_headers.py`
- Overlay dans zone conversation principale
- Panneau paramètres extensible

#### **Système Mémoire**
- Extension `MemoryManager` pour souvenirs "REF"
- Recherche contexte réflexions antérieures
- Intégration embeddings vectoriels

---

## 🚀 UTILISATION

### Installation et Initialisation

```python
# Dans ogma_ng.py - Après initialisation MemoryManager
from extensions.cognitive_mirror import initialize_cognitive_mirror

# Initialisation extension
success = initialize_cognitive_mirror(
    chat_controller=chat_ai,
    archiviste_controller=archiviste_ai,
    memory_manager=memory_mgr,
    ui_container=main_ui_container
)

if success:
    print("✅ Cognitive Mirror initialisé")
```

### Contrôle Extension

```python
from extensions.cognitive_mirror import get_cognitive_mirror

mirror = get_cognitive_mirror()

# Vérification état
if mirror.is_enabled():
    print("🧠 Cognitive Mirror actif")

# Toggle manuel
new_state = mirror.toggle_enabled()
print(f"État: {'ON' if new_state else 'OFF'}")

# Statut détaillé
status = mirror.get_extension_status()
print(f"Sessions actives: {status['active_reflection']}")
```

### Enrichissement Conversation

```python
# Dans pipeline conversation
from extensions.cognitive_mirror import get_reflection_context, start_inactivity_monitoring

def enhanced_send_message(user_message):
    # Logique OGMA existante...
    
    # Enrichissement avec contexte réflexion
    reflection_context = get_reflection_context()
    if reflection_context:
        enriched_prompt = f"{original_prompt}\n\n[Réflexion: {reflection_context}]"
    
    # Démarrage surveillance après envoi
    start_inactivity_monitoring()
    
    return ai_response
```

---

## ⚙️ CONFIGURATION

### Paramètres Utilisateur Ajustables

```json
{
  "trigger_delay_no_message": 30,    // secondes sans message
  "trigger_delay_no_typing": 20,     // secondes sans frappe
  "max_reflection_duration": 300,    // timeout 5 minutes
  "overlay_height_percent": 30,      // hauteur overlay
  "auto_save_reflections": true,     // sauvegarde auto
  "extension_enabled": false         // état initial OFF
}
```

### Styles CSS Personnalisables

Les styles sont définis dans `config.py` pour homogénéité avec OGMA :
- Couleurs cohérentes theme sombre
- Transitions fluides (300ms cubic-bezier)
- Typographie Inter consistante
- États hover/focus accessibles

---

## 🎭 EXPÉRIENCE UTILISATEUR

### Scénario Type d'Usage

1. **Conversation normale**
   ```
   Utilisateur: "J'ai un problème avec mon projet..."
   IA: "Je comprends. Peux-tu détailler ?"
   [Utilisateur arrête de taper...]
   ```

2. **Déclenchement automatique** (20s sans frappe)
   ```
   💭 Overlay apparaît avec fondu
   ```

3. **Session réflexive visible**
   ```
   IA: "Archiviste, l'utilisateur s'est arrêté après mentionner 
        un problème. Que disent nos souvenirs ?"
   
   Archiviste: "Analysant... Il montre ces patterns quand il 
               approche d'un deadline. Recommande approche 
               structurée avec exemples concrets."
   
   IA: "Perfect ! Je vais adapter ma stratégie. Merci pour 
        cette analyse contextuelle."
   ```

4. **Retour utilisateur**
   ```
   [Détection frappe] → Overlay se ferme
   💾 Sauvegarde souvenir "REF#2847"
   ```

5. **Réponse enrichie**
   ```
   IA: "Basé sur notre analyse, je vois que tu approches 
        d'un deadline. Voici une approche structurée 
        étape par étape..."
   ```

### Avantages Utilisateur

- **Transparence totale** : Comprend pourquoi l'IA répond ainsi
- **Confiance renforcée** : Voit le processus de réflexion
- **Apprentissage** : Découvre comment l'IA utilise la mémoire
- **Personnalisation** : Témoin de l'adaptation comportementale

---

## 🔧 DÉVELOPPEMENT

### Prérequis

- OGMA v2.0+ avec architecture modulaire
- NiceGUI 1.4.0+
- Python 3.8+
- MemoryManager fonctionnel

### Extensions Futures

#### Phase 2 : Détection Avancée
- [ ] Monitoring clavier Linux/macOS
- [ ] Détection patterns comportementaux
- [ ] Analyse sentiment utilisateur en temps réel

#### Phase 3 : IA Réflexive Avancée
- [ ] Réflexions multi-agents (+ autres extensions)
- [ ] Apprentissage from reflection patterns
- [ ] Personnalisation dynamique réflexions

#### Phase 4 : Analytics
- [ ] Dashboard insights réflexions
- [ ] Export données pour analyse
- [ ] API REST pour intégrations externes

---

## 🐛 DÉPANNAGE

### Problèmes Courants

#### Extension ne démarre pas
```bash
# Vérification dépendances OGMA
python -c "from core_logic import MemoryManager; print('✅ MemoryManager OK')"

# Log initialisation
tail -f debug.log | grep COGNITIVE-MIRROR
```

#### Overlay ne s'affiche pas
- Vérifier NiceGUI 1.4.0+ installé
- Container UI fourni lors initialisation
- Styles CSS chargés correctement

#### Détection clavier ne fonctionne pas
- Windows uniquement supporté actuellement
- Permissions administrateur possiblement requises
- Fallback detection messages uniquement

### Logs de Debug

```python
# Activation debug détaillé
import logging
logging.getLogger('cognitive_mirror').setLevel(logging.DEBUG)

# Statut en temps réel
mirror = get_cognitive_mirror()
print(json.dumps(mirror.get_status(), indent=2))
```

---

## 🎯 ROADMAP

### v1.0.0 - Core MVP ✅
- [x] Détection inactivité basique
- [x] Sessions réflexives IA-Archiviste
- [x] Overlay interface 30% hauteur
- [x] Souvenirs "REF" avec intégration mémoire
- [x] Configuration utilisateur complète

### v1.1.0 - Optimisations
- [ ] Performance monitoring clavier
- [ ] Animations UI perfectionnées
- [ ] Statistiques usage avancées
- [ ] Export/import réflexions

### v1.2.0 - Intelligence
- [ ] Réflexions context-aware améliorées
- [ ] Patterns utilisateur machine learning
- [ ] Intégration autres extensions OGMA

### v2.0.0 - Écosystème
- [ ] API ouverte pour développeurs
- [ ] Plugins réflexion tierces
- [ ] Multi-agents réflexion collaborative

---

## 📞 SUPPORT

- **Documentation complète** : `EXTENSION_COGNITIVE_MIRROR_SPECS.md`
- **Architecture OGMA** : `AUDIT_ARCHITECTURE_OGMA.md`
- **Issues GitHub** : [URL_REPO]/issues
- **Discord communauté** : [DISCORD_LINK]

---

*Extension Cognitive Mirror v1.0.0*  
*OGMA v2.0 - Révolution transparence cognitive*  
*© 2025 OGMA Team - Innovation Open Source*