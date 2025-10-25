# 🧠 **OGMA - IA Conversationnelle NiceGUI**

## 🎯 **NOUVELLE INTERFACE PROFESSIONAL**

OGMA est maintenant disponible avec une interface NiceGUI moderne, inspirée de ChatGPT et Claude, avec un design sobre et professionnel.

---

## 🚀 **LANCEMENT RAPIDE**

### **Méthode 1 : Script de lancement automatique**
```bash
python launch_ogma.py
```

### **Méthode 2 : Lancement direct**
```bash
python ogma_app.py
```

### **Interface web**
- **URL** : `http://localhost:8080`
- **Design** : Dark mode avec accents dorés
- **Style** : ChatGPT/Claude professionnel

---

## 🎨 **DESIGN SYSTEM**

### **Palette de couleurs**
- **Fond principal** : `#1a1a1a` (gris très sombre)
- **Fond secondaire** : `#2d2d2d` (gris sombre)
- **Zone de saisie** : `#404040` (gris moyen)
- **Accent doré** : `#d4af37` (or élégant)
- **Texte principal** : `#e8e8e8` (blanc cassé)

### **Caractéristiques visuelles**
- ✅ **Aucun fond blanc** - Design 100% sombre
- ✅ **Bordures dorées fines** sur éléments actifs
- ✅ **Animations fluides** et transitions subtiles
- ✅ **Typographie professionnelle** sans icônes ludiques
- ✅ **Zone de saisie overlay** comme ChatGPT

---

## 🔧 **FONCTIONNALITÉS INTERFACE**

### **💬 Zone de Conversation**
- Messages utilisateur : Fond gris, alignés à droite
- Messages IA : Fond sombre, bordure dorée, alignés à gauche  
- Messages système : Centrés, style discret
- Scroll fluide avec scrollbar personnalisée

### **✍️ Zone de Saisie (Overlay)**
- **Position** : Fixe en bas, overlay sur conversation
- **Design** : Bordure arrondie, effet de flou d'arrière-plan
- **Boutons intégrés** :
  - 📎 **Fichier** : Upload PDF, DOCX, images
  - 💭 **Mémoire** : Mémorisation manuelle
  - ⚙️ **Paramètres** : Configuration IA
  - **Envoyer** : Bouton doré principal

### **🔧 Popups Professionnelles**
- **Paramètres IA** : Configuration providers, modèles, clés API
- **Mémorisation** : Zone de texte pour souvenirs manuels
- **Upload fichiers** : Drag & drop avec formats supportés
- **Design** : Modales centrées avec blur background

---

## ⚙️ **CONFIGURATION**

### **Paramètres IA disponibles**
- **💬 IA Chat** : Provider, modèle, clé API, tokens
- **🧠 IA Archiviste** : Configuration mémoire/synthèse  
- **🔢 IA Embeddings** : Configuration vectorisation

### **Providers supportés**
- OpenAI (GPT-4, GPT-3.5)
- Mistral (Pixtral, Mistral Large)
- Anthropic (Claude)
- Google (Gemini)
- Ollama (local)

---

## 🔒 **SÉCURITÉ**

### **Clés API sécurisées**
```env
# .env file (recommandé)
MISTRAL_API_KEY=your_real_key_here
OPENAI_API_KEY=your_real_key_here
ANTHROPIC_API_KEY=your_real_key_here
```

### **Configuration via interface**
- Champs password masqués
- Sauvegarde sécurisée dans settings.json
- Support variables d'environnement

---

## 📁 **STRUCTURE INTERFACE**

```
Interface OGMA NiceGUI
├── Header
│   ├── Titre "OGMA" (doré)
│   └── Sous-titre descriptif
├── Zone Conversation
│   ├── Messages utilisateur (droite)
│   ├── Messages IA (gauche, bordure dorée)
│   └── Messages système (centre)
└── Zone Saisie Overlay
    ├── Bouton Fichier (📎)
    ├── Bouton Mémoire (💭) 
    ├── Zone de texte (extensible)
    ├── Bouton Paramètres (⚙️)
    └── Bouton Envoyer (doré)
```

---

## 🎯 **AVANTAGES vs GRADIO**

### **✅ Améliorations NiceGUI**
- **Performance** : Plus rapide et réactif
- **Design** : Esthétique moderne et professionnelle
- **Personnalisation** : CSS complet et flexible
- **UX** : Interactions plus fluides
- **Mobile** : Responsive design optimal

### **🔄 Compatibilité Backend**
- **100% compatible** avec tous les modules OGMA existants
- **Même API** : AIController, MemoryManager, etc.
- **Même fonctionnalités** : Mémoire, perception, embeddings
- **Migration transparente** : Aucune perte de données

---

## 🚨 **TROUBLESHOOTING**

### **Problèmes courants**

#### **Port 8080 occupé**
```bash
# Modifier le port dans ogma_app.py ligne 890
ui.run(port=8081, ...)
```

#### **NiceGUI non installé**
```bash
pip install nicegui>=2.20.0
```

#### **Backend non initialisé**
```bash
# Vérifier que tous les modules sont présents
python -c "import core_logic, memory_manager"
```

#### **Clés API manquantes**
- Configurez dans `.env` ou via l'interface ⚙️
- Vérifiez les permissions de vos clés API

---

## 🎨 **PERSONNALISATION**

### **Modifier les couleurs**
Éditez `static/ogma_styles.css` :
```css
:root {
    --accent-gold: #your_color;
    --bg-main: #your_background;
}
```

### **Ajuster la mise en page**
Modifiez `ogma_app.py` dans la classe `OGMAStyles`

### **Personnaliser les messages**
Éditez la classe `MessageComponent` pour changer l'apparence

---

## 📊 **PERFORMANCE**

### **Optimisations incluses**
- CSS externes minifiés
- Images compressées  
- Animations GPU-accelerated
- Lazy loading des composants
- WebSocket optimisé pour temps réel

### **Métriques typiques**
- **Démarrage** : ~2-3 secondes
- **Réponse IA** : Dépend de l'API (1-5s)
- **Mémoire** : ~100-200MB RAM
- **CPU** : Minimal sauf traitement IA

---

## 🔮 **FONCTIONNALITÉS À VENIR**

- [ ] **Mode sombre/clair** : Toggle theme
- [ ] **Raccourcis clavier** : Navigation rapide
- [ ] **Recherche conversations** : Interface dédiée
- [ ] **Export conversations** : PDF, Markdown
- [ ] **Plugins** : Architecture extensible
- [ ] **Voice input** : Reconnaissance vocale
- [ ] **Multi-sessions** : Utilisateurs multiples

---

## 💡 **UTILISATION AVANCÉE**

### **Commandes rapides**
- `Ctrl+Enter` : Envoyer message
- `Shift+Enter` : Nouvelle ligne  
- `Ctrl+/` : Ouvrir aide
- `Ctrl+K` : Rechercher

### **Astuces d'usage**
- **Mémorisation** : Utilisez 💭 pour des infos importantes
- **Fichiers** : Drag & drop directement sur 📎
- **Paramètres** : Testez différents modèles via ⚙️
- **Contexte** : L'IA se souvient automatiquement

---

**🧠 OGMA - L'IA conversationnelle qui se souvient, maintenant en beauté !**