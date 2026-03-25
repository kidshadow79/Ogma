# 🎨 Extension Text2Image - Guide d'Utilisation

## 📋 Ce qui a été modifié

### ✅ **Interface Utilisateur (Frontend)**

**Localisation:** Paramètres > Image (bouton dans le header OGMA)

**3 nouvelles zones de texte modifiables:**

#### 1️⃣ **Quality Boosts** (Qualité générale)
- **Valeur par défaut** (274 caractères):
  ```
  highly detailed, photorealistic, 8k uhd resolution, sharp focus, 
  professional photography, studio quality lighting, cinematic composition, 
  masterpiece quality, perfect anatomy, natural skin texture, realistic details, 
  high definition, crisp image, professional color grading
  ```
- **Utilisation**: Ajoutés à TOUS les prompts automatiquement
- **Modifiable**: Oui, tu peux ajouter/retirer/modifier les qualifiers

#### 2️⃣ **NSFW Boosts** (Réalisme anatomique)
- **Valeur par défaut** (185 caractères):
  ```
  anatomically correct, natural proportions, realistic body, 
  authentic human anatomy, detailed skin pores, natural skin imperfections, 
  subtle muscle definition, realistic lighting on skin
  ```
- **Utilisation**: Ajoutés UNIQUEMENT si contenu NSFW détecté (mots-clés: nue, naked, seins, etc.)
- **Modifiable**: Oui

#### 3️⃣ **Prompt Négatif**
- **Valeur par défaut** (54 caractères):
  ```
  blurry, low quality, distorted, bad anatomy, deformed
  ```
- **Utilisation**: Intégré au prompt via `| AVOID: ...`
- **Modifiable**: Oui
- **Astuce**: Plus c'est détaillé, meilleure est la qualité

---

## 🔧 Fonctionnement Technique

### **Pipeline de génération:**

```
1. Luna dit: "je dois créer une image de : femme latina sensuelle"
   ↓
2. PromptEnhancer enrichit le prompt:
   - Détecte mots-clés (femme, latina, sensuelle)
   - Ajoute expansions anatomiques
   - Ajoute quality_boosts depuis settings
   - Détecte NSFW → Ajoute nsfw_boosts depuis settings
   - Ajoute negative_prompt via "| AVOID: ..."
   ↓
3. Prompt final envoyé à Pollinations:
   "femme latina sensuelle, beautiful woman, feminine features, 
    latina woman, caramel skin tone, sensual expression, 
    highly detailed, photorealistic, 8k uhd resolution, [...] 
    | AVOID: blurry, low quality, distorted, bad anatomy, deformed"
   ↓
4. Image générée et affichée dans le chat
```

### **Sauvegarde des paramètres:**

- **Fichier**: `data/settings.json`
- **Section**: `image_generation.prompt_enhancement`
- **Format**:
  ```json
  {
    "image_generation": {
      "prompt_enhancement": {
        "quality_boosts": "...",
        "nsfw_boosts": "...",
        "custom_boosts": ""
      },
      "negative_prompt": "..."
    }
  }
  ```

---

## 🎯 Comment Modifier les Paramètres

### **Via l'Interface:**

1. Lance OGMA: `python launch_ogma.py`
2. Clique sur le bouton **"Paramètres"** dans le header
3. Clique sur **"🎨 Image"**
4. Modifie les 3 zones de texte:
   - Quality Boosts
   - NSFW Boosts  
   - Prompt Négatif
5. Clique sur **"Sauvegarder"**
6. L'extension se recharge automatiquement

### **Via le fichier settings.json:**

1. Ouvre `data/settings.json`
2. Modifie la section `image_generation.prompt_enhancement`
3. Sauvegarde le fichier
4. Relance OGMA

### **Reset aux valeurs par défaut:**

```bash
python update_image_settings_defaults.py
```

---

## 📊 Exemples de Personnalisation

### **Style Artistique:**
```
Quality Boosts:
digital art, concept art, trending on artstation, highly detailed, 
fantasy art, dramatic lighting, vibrant colors, artistic masterpiece

NSFW Boosts:
artistic nude, tasteful, elegant composition, classical beauty

Negative Prompt:
photorealistic, amateur, low quality, blurry, distorted, deformed
```

### **Style Photographique Réaliste:**
```
Quality Boosts:
professional photography, DSLR, 85mm lens, bokeh background, 
natural lighting, high resolution, sharp focus, color graded, 
editorial quality

NSFW Boosts:
natural body, authentic anatomy, skin texture detail, 
professional model, studio lighting

Negative Prompt:
cartoon, anime, illustration, painting, 3d render, cgi, 
fake, artificial, low quality, blurry
```

### **Style Minimaliste (peu de boosts):**
```
Quality Boosts:
high quality, detailed, professional

NSFW Boosts:
natural, realistic

Negative Prompt:
low quality, blurry
```

---

## 🐛 Debugging

### **Vérifier que les boosts sont bien utilisés:**

Regarde les logs dans le terminal OGMA après génération:

```
[TEXT2IMG-HTTP] 📊 Quality boosts: 274 chars
[TEXT2IMG-HTTP] 🔞 NSFW boosts: 185 chars
[TEXT2IMG-HTTP] 🚫 Negative prompt: 'blurry, low quality...'
[TEXT2IMG-HTTP] 🚀 Prompt enrichi (25 → 548 chars)
```

### **Problèmes courants:**

1. **Les boosts ne s'appliquent pas:**
   - Vérifie que `settings.json` contient bien les valeurs
   - Relance OGMA après modification
   - Vérifie les logs pour voir le prompt enrichi

2. **Format CSV incorrect:**
   - Utilise des virgules pour séparer les qualifiers
   - Pas besoin de guillemets
   - Exemple: `quality1, quality2, quality3`

3. **Prompt négatif ignoré:**
   - Pollinations ne supporte pas nativement les prompts négatifs
   - On les ajoute via `| AVOID: ...` (workaround)
   - Efficacité variable selon le modèle

---

## 📚 Ressources

### **Qualifiers populaires:**

- **Qualité**: `highly detailed, ultra detailed, 8k, 4k, sharp focus, crisp`
- **Style photo**: `professional photography, DSLR, studio lighting, bokeh`
- **Style art**: `digital art, concept art, artstation, fantasy art, oil painting`
- **Réalisme**: `photorealistic, hyperrealistic, lifelike, authentic`
- **Cinéma**: `cinematic lighting, dramatic, film grain, anamorphic lens`

### **Prompts négatifs communs:**

- **Défauts techniques**: `blurry, low quality, pixelated, jpeg artifacts, noise`
- **Défauts anatomiques**: `bad anatomy, deformed, disfigured, missing limbs, extra fingers`
- **Styles indésirables**: `cartoon, anime, 3d render, painting, illustration`

---

## ✅ Validation Complète

**Fichiers modifiés:**
- ✅ `ogma_ng.py` - UI avec 3 textareas
- ✅ `extensions/text2img/prompt_enhancer.py` - Support CSV boosts
- ✅ `extensions/text2img/perchance_http_backend.py` - Intégration settings
- ✅ `extensions/text2img/text2img_manager.py` - Pass settings_manager
- ✅ `data/settings.json` - Valeurs par défaut initialisées

**Tests:**
- ✅ Syntaxe Python (4/4 fichiers OK)
- ✅ Settings sauvegardés correctement
- ✅ Logs backend affichent les boosts

**Commits Git:**
- ✅ `feat(text2img): Expose PromptEnhancer settings in UI` (385e704)
- ✅ `chore(text2img): Initialize default prompt enhancement settings` (f0b6f8c)
