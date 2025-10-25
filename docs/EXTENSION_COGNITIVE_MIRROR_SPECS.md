# 🧠 EXTENSION COGNITIVE MIRROR - Spécifications Techniques

> **Extension révolutionnaire de transparence cognitive**  
> *Fenêtre de réflexion visible entre IA et Archiviste*

---

## 🎯 CONCEPT GÉNÉRAL

### Vision
L'extension **Cognitive Mirror** révèle le processus de réflexion interne d'OGMA en affichant une conversation transparente entre l'IA principale et l'Archiviste. L'utilisateur devient témoin de la pensée de l'IA, renforçant la confiance et l'engagement.

### Philosophie
**"Rendre visible l'invisible"** - Transformer le processus cognitif opaque de l'IA en une expérience transparente et éducative.

---

## ⚙️ MÉCANISMES TECHNIQUES

### 🕐 Détection d'Inactivité

#### **Déclencheurs automatiques (Extension ON)**
1. **Absence d'envoi utilisateur** : 30 secondes sans message
2. **Détection pianotage clavier** : 20 secondes sans frappe détectée
3. **Activation immédiate** si aucune activité détectée

#### **Logique de détection**
```python
# Pseudo-code mécanisme
class InactivityDetector:
    def __init__(self):
        self.last_message_time = None
        self.last_keypress_time = None
        self.trigger_delay_no_message = 30  # secondes
        self.trigger_delay_no_typing = 20   # secondes
    
    def should_trigger_reflection(self):
        current_time = time.time()
        
        # Vérification absence de message
        if self.last_message_time:
            no_message_delay = current_time - self.last_message_time
            if no_message_delay >= self.trigger_delay_no_message:
                return True
        
        # Vérification absence de pianotage
        if self.last_keypress_time:
            no_typing_delay = current_time - self.last_keypress_time
            if no_typing_delay >= self.trigger_delay_no_typing:
                return True
        
        return False
```

### 🎭 Session de Réflexion

#### **Démarrage automatique**
1. Overlay apparaît (30% hauteur, largeur conversation)
2. IA commence conversation avec Archiviste
3. **Prompt de démarrage** : "Analysons ensemble notre conversation en cours avec l'utilisateur..."

#### **Contenu de la réflexion**
- **Consultation mémoires** : Archiviste accède aux souvenirs pertinents
- **Analyse contextuelle** : IA partage ses incertitudes, questionnements
- **Stratégies conversation** : Discussion sur les meilleures approches
- **Enrichissement émotionnel** : Compréhension des nuances utilisateur

#### **Déroulement type**
```
IA: "Archiviste, notre utilisateur semble préoccupé par ce projet. 
     Que nous disent nos souvenirs sur ses patterns de stress ?"

Archiviste: "Selon mes analyses, il montre ces signes quand il 
            approche d'un deadline important. Souvenir REF#2847 
            indique qu'il apprécie les approches structurées."

IA: "Parfait. Je vais donc proposer une planification étape par étape
     tout en restant encourageant. Comment formuler cela ?"

Archiviste: "Utilise un ton rassurant avec des exemples concrets.
            Évite les longs paragraphes, il préfère les listes."
```

### 🔄 Fin de Session

#### **Déclencheurs de fin**
1. **Retour utilisateur** : Détection activité clavier/envoi message
2. **Timeout sécurité** : 5 minutes maximum (configurable)
3. **Conclusion naturelle** : Archiviste signale fin de réflexion

#### **Processus de clôture**
1. **Archiviste génère résumé** de la session réflexive
2. **Création souvenir "REF"** avec préfixe spécial
3. **Intégration contexte** : Résumé ajouté au contexte conversation
4. **Fermeture overlay** : Retour interface normale
5. **IA enrichie** : Réponse suivante bénéficie de la réflexion

---

## 🎨 INTERFACE UTILISATEUR

### 📱 Overlay Principal

#### **Positionnement**
- **Position** : Superposition zone conversation
- **Largeur** : 100% largeur zone conversation
- **Hauteur** : 30% hauteur zone conversation  
- **Ancrage** : Partie haute de l'écran
- **Style** : Semi-transparent avec bordures distinctes

#### **Contenu affiché**
- **Chat réflexif** : Messages IA ↔ Archiviste en temps réel
- **Indicateurs** : Statut session, temps écoulé
- **Animation** : Points de suspension pendant "réflexion"

### ⚙️ Zone Paramètres

#### **Localisation**
- **Position** : Sous l'overlay principal
- **Taille** : Compacte, extensible au clic
- **Accès** : Icône paramètres visible

#### **Paramètres configurables**
- **Délai sans message** : 15-60 secondes (défaut: 30s)
- **Délai sans pianotage** : 10-30 secondes (défaut: 20s)  
- **Timeout sécurité** : 2-10 minutes (défaut: 5min)
- **Mode d'affichage** : Complet / Résumé seulement
- **Fréquence sauvegarde** : Toujours / Sessions importantes

### 🎛️ Contrôles Utilisateur

#### **Bouton ON/OFF**
- **Position** : À côté des autres extensions (Archi Sensor, etc.)
- **États** : 
  - 🟢 **ON** : Extension active, réflexions automatiques
  - ⭕ **OFF** : Extension désactivée
  - 🔄 **EN COURS** : Session réflexive active

#### **Contrôles session**
- **Pause/Resume** : Suspendre temporairement la réflexion
- **Forcer fin** : Terminer manuellement la session
- **Voir historique** : Accès aux réflexions précédentes

---

## 🏗️ ARCHITECTURE TECHNIQUE

### 📁 Structure Extension

```
extensions/cognitive_mirror/
├── __init__.py                    # Point d'entrée + API publique
├── core_cognitive_mirror.py       # Moteur principal logique
├── reflection_manager.py          # Gestion sessions réflexives  
├── inactivity_detector.py         # Détection inactivité utilisateur
├── ui_components.py               # Interface overlay + paramètres
├── memory_integration.py          # Intégration souvenirs "REF"
├── config.py                      # Configuration + settings
├── keyboard_monitor.py            # Monitoring clavier (optionnel)
└── README.md                      # Documentation intégration
```

### 🔌 Points d'Intégration OGMA

#### **1. Pipeline Conversation**
```python
# Intégration dans _send_chat_message()
def _send_chat_message_enriched():
    # Logique OGMA existante...
    
    # Démarrage détection inactivité
    cognitive_mirror.start_inactivity_monitoring()
    
    # Si contexte réflexion disponible
    reflection_context = cognitive_mirror.get_reflection_context()
    if reflection_context:
        # Enrichissement prompt avec résumé réflexion
        enriched_prompt = f"{original_prompt}\n\n[Réflexion interne: {reflection_context}]"
```

#### **2. Interface Utilisateur**
```python
# Intégration dans ogma_headers.py
def _header_with_cognitive_mirror():
    # Headers existants...
    
    # Bouton Cognitive Mirror
    cognitive_mirror_button = ui.button("🧠", on_click=toggle_cognitive_mirror)
    cognitive_mirror_button.classes("cognitive-mirror-toggle")
```

#### **3. Système Mémoire**
```python
# Extension MemoryManager pour souvenirs "REF"
class EnhancedMemoryManager(MemoryManager):
    def save_reflection_memory(self, reflection_summary):
        memory_entry = {
            "id": f"REF_{uuid.uuid4()}",
            "type": "reflection",
            "content": reflection_summary,
            "timestamp": datetime.now(),
            "context": self.current_conversation_context
        }
        self.add_memory(memory_entry)
```

---

## 🎭 FLUX UTILISATEUR DÉTAILLÉ

### 🚀 Scénario Type

#### **Étape 1 : Conversation normale**
```
Utilisateur: "J'ai un problème avec mon projet..."
IA: "Je comprends ta préoccupation. Peux-tu me donner plus de détails ?"
[Utilisateur s'arrête de taper, réfléchit...]
```

#### **Étape 2 : Détection inactivité**
```
⏱️ 20 secondes sans pianotage détectées
🧠 Extension Cognitive Mirror: ACTIVATION
📱 Overlay apparaît en fondu
```

#### **Étape 3 : Session réflexive visible**
```
[OVERLAY - Conversation IA ↔ Archiviste]

IA: "Archiviste, notre utilisateur s'est arrêté après avoir mentionné 
     un problème de projet. Que savons-nous de sa situation ?"

Archiviste: "Analysant nos souvenirs... Il a mentionné il y a 3 jours 
            un deadline serré sur un projet client. Niveau de stress 
            détecté: élevé."

IA: "Intéressant. Ses questions habituelles dans ce cas ?"

Archiviste: "Il cherche généralement des approches structurées et 
            rassurantes. Éviter les solutions trop complexes."

IA: "Parfait. Je vais proposer une méthode étape par étape avec 
     des exemples concrets. Prépare aussi des ressources sur la 
     gestion de stress."

Archiviste: "Session de réflexion complète. Créant souvenir REF#2851 
            avec contexte et stratégie d'aide."
```

#### **Étape 4 : Retour utilisateur**
```
[Utilisateur recommence à taper]
🔄 Détection activité clavier
📱 Overlay se ferme en fondu
💾 Sauvegarde résumé réflexion en souvenir "REF"
```

#### **Étape 5 : Réponse enrichie**
```
IA: "Je comprends que ce projet te préoccupe. Basé sur notre historique, 
     je sais que tu apprécies les approches structurées. 
     Voici une méthode étape par étape qui pourrait t'aider..."
     
[Réponse enrichie par la réflexion]
```

---

## 🔧 PARAMÈTRES TECHNIQUES

### ⚡ Performance

#### **Optimisations requises**
- **Threads séparés** : Détection inactivité non-bloquante
- **Cache contexte** : Éviter rechargement mémoires
- **Limite tokens** : Sessions réflexives contrôlées (max 500 tokens)
- **Lazy loading** : Overlay créé uniquement si nécessaire

#### **Ressources système**
- **Monitoring clavier** : Polling léger (100ms max)
- **RAM additionnelle** : ~50MB pour cache contexte réflexion
- **CPU** : Impact minimal (< 2% en arrière-plan)

### 🛡️ Sécurité & Confidentialité

#### **Protection données**
- **Souvenirs REF** : Mêmes protections que mémoire principale
- **Sessions temporaires** : Auto-nettoyage après sauvegarde
- **Logs réflexion** : Option désactivation complète

#### **Contrôle utilisateur**
- **Opt-in obligatoire** : Extension OFF par défaut
- **Transparence totale** : Utilisateur voit toute la réflexion
- **Suppression** : Possibilité effacer historique réflexions

---

## 🎯 ROADMAP DÉVELOPPEMENT

### 🥇 Phase 1 : Core MVP
- ✅ Détection inactivité basique (30s sans message)
- ✅ Overlay simple avec conversation IA-Archiviste
- ✅ Bouton ON/OFF fonctionnel
- ✅ Intégration basique pipeline conversation

### 🥈 Phase 2 : Détection Avancée
- 🔄 Monitoring clavier temps réel
- 🔄 Paramètres configurables utilisateur
- 🔄 Souvenirs "REF" avec recherche
- 🔄 Interface paramètres sous overlay

### 🥉 Phase 3 : Optimisations
- ⚡ Performance et threading optimisé
- 🎨 Animations et transitions fluides
- 📊 Statistiques usage et efficacité
- 🔍 Historique et recherche réflexions

---

## 💎 VALEUR RÉVOLUTIONNAIRE

### 🚀 Innovation Unique
- **Première IA** à révéler son processus de réflexion
- **Transparence cognitive** inédite dans l'industrie
- **Engagement utilisateur** par la curiosité naturelle
- **Confiance renforcée** par la visibilité des mécanismes

### 🎓 Impact Éducatif
- **Compréhension IA** : Utilisateur apprend comment l'IA "pense"
- **Démystification** : Processus transparent vs "boîte noire"
- **Métacognition** : L'utilisateur développe sa propre réflexion

### 🏆 Avantage Concurrentiel
- **Différenciation totale** : Aucun concurrent n'a cette approche
- **Expérience mémorable** : Utilisateurs fascinés par le concept
- **Viralité naturelle** : Fonctionnalité intrinsèquement partageable

---

*Spécifications complètes - Extension Cognitive Mirror*  
*OGMA v2.0 - Architecture révolutionnaire de transparence cognitive*