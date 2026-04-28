# IDEES & CONCEPTS OGMA
*Brainstorming collaboratif — Yohan / IA codeuse*  
*Document évolutif — ne pas implémenter sans feu vert*

---

## CONCEPT 01 — Hologramme Expressif (Pyramide de Pepper's Ghost)
**Date** : 15 avril 2026  
**Statut** : 💡 Idée validée faisable — à planifier

### L'idée
Donner à OGMA une représentation visuelle physique via un hologramme DIY.  
Principe : un téléphone mobile pose sur une pyramide en plastique transparent (4 trapèzes assemblés). 4 images identiques tournées à 0°/90°/180°/270° sur fond noir se reflètent sur les faces → illusion d'une image flottante au centre.

L'image animée représente **une présence organique** d'OGMA : un nuage/blob vivant avec deux yeux et une zone bouche, dont :
- La **couleur** change selon l'émotion dominante analysée par l'Archiviste
- La **bouche vibre** en synchronisation avec l'émission TTS (binaire speaking/silent)
- Le **corps** se déplace de façon organique (bruit de Perlin)

### Faisabilité
✅ **Oui, pleinement faisable.** Tout le nécessaire existe déjà dans OGMA :

| Besoin | Source dans OGMA |
|--------|-----------------|
| État TTS live (speaking/silent) | `tts_perception_manager.py` + `audio_manager.py` |
| Émotion dominante en temps réel | Archiviste → `logic_callbacks.py` |
| Valence / intensité émotionnelle | Métadonnées souvenirs (valence, intensité) |
| Serveur accessible réseau local | NiceGUI sur port 8080, accès WiFi mobile natif |
| WebSocket temps réel | Supporté nativement par NiceGUI |

### Architecture envisagée
```
extensions/hologram_projector/
├── __init__.py           # API standard extension
├── hologram_server.py    # Route /hologram + WebSocket /hologram/state
├── state_emitter.py      # Hook TTS + Archiviste → état {emotion, is_speaking, intensity}
└── hologram.html         # Canvas JS pur, fond noir, 4 quadrants rotatifs
```

**Flux :** Archiviste analyse émotion → state_emitter → WebSocket → Canvas mobile → projection pyramide

### Mapping émotion → couleur
| Émotion | Couleur |
|---------|---------|
| curiosité | violet/bleu profond |
| joie | doré/ambre |
| calme | blanc nacré/cyan pâle |
| mélancolie | bleu nuit |
| tension/alerte | orange/rouge |
| rêve (Dream Engine actif) | rose mauve lent |
| idle/neutre | gris bleuté en veille |

### Contraintes
- Fond **noir absolu obligatoire** pour que la projection fonctionne
- Sync bouche/TTS = binaire (pas de lip-sync précis, suffisant pour l'illusion)
- Latence WebSocket local < 20ms — imperceptible
- Extension **passive en lecture** — zéro impact sur les conversations

### Hardware DIY
4 trapèzes PVC transparent (feuille plastique de classeur ou plastique de boîtier CD), angles scotchés. Coût : ~2-5€. Dimensions calculées selon la taille de l'écran mobile utilisé.

---

## CONCEPT 02 — Assistant PC Vocal avec Mémoire Longue
**Date** : 16 avril 2026  
**Statut** : 💡 Idée validée faisable — concept différenciateur à affiner

### L'idée
Un logiciel en surcouche de Windows. On lui parle vocalement et il est capable de :
- Voir et comprendre ce qui se passe sur l'écran
- Bouger la souris, cliquer sur des éléments
- Naviguer dans les dossiers Windows
- Trouver un fichier, une image
- Ouvrir un navigateur, écrire dans des champs, envoyer des emails
- Interagir avec n'importe quel environnement affiché à l'écran

### L'état de l'art (ce qui existe déjà)
| Projet | Capacités | Limite |
|--------|-----------|--------|
| **Claude Computer Use** (Anthropic, oct. 2024) | Contrôle PC complet, navigation fichiers, emails | Repart de zéro à chaque session |
| **OpenAI Operator** | Agent web dans navigateur | Limité au navigateur |
| **Open Interpreter** | IA locale, exécute code + contrôle PC | Pas d'interface vocale intégrée |
| **UFO** (Microsoft Research) | Agent Windows basé GPT-4V + Accessibility Tree | Pas de mémoire, pas de voix |

**Ce qui manque à toutes ces solutions : la mémoire longue de l'utilisateur.** Elles repartent de zéro à chaque session.

### La valeur ajoutée différenciatrice
- **Mémoire persistante** des habitudes → "je sais que tu mets toujours les factures dans ce dossier"
- **Voix naturelle avec personnalité** — pas juste "ok j'exécute", une vraie interaction
- **Écoute permanente** (pas push-to-talk)
- **Mode apprentissage** → l'IA observe comment *toi* tu fais les choses et mémorise tes patterns

### Technologies nécessaires
| Besoin | Technologie |
|--------|------------|
| Contrôle souris/clavier | `pyautogui`, `pynput`, `pywinauto` |
| Voix STT/TTS | Pipeline OGMA réutilisable tel quel |
| Vision écran | GPT-4o / Claude multimodal + OmniParser |
| Overlay Windows non-bloquant | PyQt5 ou NiceGUI always-on-top transparent |
| Mémoire utilisateur | Architecture OGMA réutilisable |

### Contraintes réelles
- Fiabilité ~80% sur tâches complexes (se trompe ~1 fois sur 5)
- Latence 2-8s par action (amélioration attendue avec modèles locaux)
- Coût API si screenshot envoyé à chaque frame → résolu par le Concept 03

### Lien avec OGMA
`core_logic.py`, pipeline STT/TTS et système mémoire sont réutilisables directement. Ce serait un projet distinct mais construit sur les mêmes fondations.

---

## CONCEPT 03 — Cartographie Textuelle d'Écran (Screen Braille)
**Date** : 16 avril 2026  
**Statut** : 💡 Idée originale validée — brique technique clé du Concept 02

### L'idée
Plutôt qu'envoyer des screenshots (images base64 coûteuses) à l'API à chaque action, **traduire l'écran en représentation textuelle avec coordonnées spatiales**, stockée localement. L'IA navigue ensuite sur la carte textuelle — sans appel API vision — jusqu'à ce qu'un changement soit détecté.

Métaphore résumant le concept : **"voir une fois, lire en braille ensuite"**.

### Pourquoi c'est intelligent
| Approche | Coût par action | Vitesse |
|----------|----------------|---------|
| Screenshot → base64 → API | ~800 tokens image | 1-3s |
| Carte textuelle en cache | ~100 tokens texte | < 50ms |
| Zone diff (re-parse partiel) | ~100-200 tokens image | 200ms |

**Division par 8 du coût, vitesse multipliée.** Et la carte peut être interrogée, filtrée, comparée sans aucun appel API.

### Format de la carte textuelle
```
SCREEN_MAP v1 | app:chrome | hash:a3f9b2
---
[BAR_ONGLETS]
  TAB "Gmail"        @ (120, 32)  state:ACTIVE
  TAB "Google"       @ (220, 32)  state:idle
[URL_BAR]
  INPUT              @ (400, 35)  value:"mail.google.com"
[PAGE_CONTENT]
  BTN "Composer"     @ (50, 150)  style:prominent
  LIST emails        @ (200,200)→(1800,900)
    ITEM "Facture Free - 15/04" @ (200,220)  unread
    ITEM "Yohan - Re: projet"  @ (200,260)  read
[STATIC_CHROME]     hash:f2a1c9  ← jamais re-parsé (zone statique)
```

### Le système de diff de zones (partie la plus originale)
Avec `PIL` ou `numpy`, comparer deux screenshots prend < 5ms et retourne les rectangles modifiés :
```python
changed_zones = diff_screenshots(screen_before, screen_after)
# → [(200, 200, 1800, 900)]  # seule la liste d'emails a changé
```
**Seule la zone modifiée est renvoyée à l'API vision** pour mise à jour de la carte. Le reste reste intact en mémoire locale.

### Les trois couches combinées (architecture hybride)
```
Application ouverte ?
    ├── C'est un navigateur       → injection DOM (précision max, coût zéro)
    ├── C'est une app Windows     → Accessibility Tree (natif, < 5ms, gratuit)
    └── App canvas/jeu/inconnu   → Screenshot + vision IA → génère carte textuelle
                                    (coût one-shot, puis navigation sur carte)
```

### Gestion de l'obsolescence
Chaque zone de la carte a un **hash des pixels source**. À chaque cycle :
- Hash actuel ≠ hash stocké → zone invalidée → re-parse uniquement cette zone
- Hash identique → carte valide → aucun appel API
- Zones "statiques connues" (menus, barres d'outils) → blacklistées du check après N confirmations

### Limites identifiées
- **Apps canvas/WebGL** (Figma, jeux) : pas d'Accessibility Tree, pas de DOM — vision obligatoire à chaque action
- **Risque de carte périmée** si le système loupe une invalidation → mitigé par le hash de zone
- **Premier parsing** reste coûteux — investissement one-shot, mutualisable si la même app est revue

### Lien avec OGMA
Le `cognitive_cache` d'OGMA est conceptuellement très proche — cache sémantique de réponses. La même logique (stocker, invalider, revalider) s'applique ici aux cartes d'écran.

---

## CONCEPT 04 — Outil de Captionning Guidé pour LoRA (LoRA Dataset Builder)
**Date** : 25 avril 2026  
**Statut** : 💡 Idée originale validée — projet indépendant à fort potentiel communautaire

### L'idée
Un outil web/desktop qui automatise la création de datasets d'entraînement pour LoRAs image (FLUX, SDXL, WAN...). L'utilisateur définit via un formulaire ce qu'il veut que le LoRA retienne (visage, mains, style, etc.), uploade ses images, et l'outil génère automatiquement les paires `image.jpg + image.txt` prêtes pour kohya_ss ou CivitAI Training.

**Problème résolu** : aujourd'hui les créateurs de LoRAs écrivent les captions à la main ou utilisent des outils génériques (Joy Caption) qui décrivent tout sans intention. Le manque c'est l'**intention guidée** — "je veux capturer X, ignorer Y".

### Pipeline technique
```
[Formulaire]  →  focus : "visage, mains"
                 trigger word : "yw_person"
                 modèle cible : FLUX.1 / SDXL / WAN

[Upload images]  →  stockées temporairement

[Molmo2 via API Wavespeed]  →  description visuelle brute orientée
                                ($0.002/image, REST simple)

[LLM reformateur]  →  reçoit description brute + contexte formulaire
                       produit la caption LoRA ciblée avec trigger word

[Export ZIP]  →  dossier prêt pour kohya / CivitAI :
                  image_001.jpg + image_001.txt
                  image_002.jpg + image_002.txt
                  ...
```

### Format de caption LoRA idéal (exemple visage)

**Prompt Molmo2 orienté** :
> *"Describe only the person. Focus exclusively on: face shape, skin tone, eye color and shape, eyebrow style, nose, lips, hair color, hair texture, hair length. Ignore clothing, background, objects."*

**Caption finale produite** :
> `yw_woman, young woman, oval face, light olive skin, dark brown almond eyes, thick arched eyebrows, full lips, long dark brown hair, detailed face, photorealistic, portrait`

### Règle d'or du captionning ciblé
| Élément | Dans la caption ? |
|---|---|
| Visage détaillé (si focus visage) | ✅ Toujours, avec précision |
| Vêtements | ✅ 2-3 mots maximum |
| Fond / lieu | ✅ 1 mot (outdoor, bar, studio) |
| Émotions figées (smiling) | ⚠️ Seulement si constant sur toutes les images |
| Accessoires non constants | ❌ À éviter |

**Principe** : le LoRA apprend par superposition similarités/différences. Ce qui est constant entre toutes les images = ce qui est encodé. Décrire avec la même densité tous les éléments dilue le signal de l'élément cible.

### Compatibilité
- **kohya_ss** : format natif (dossier image + txt)
- **CivitAI Training** : zip upload direct, même format
- **SimpleTuner / AI-Toolkit** : même format

### Stack technique envisagée
- **Backend** : Python + FastAPI
- **Vision** : `wavespeed-ai/molmo2/image-captioner` (3 niveaux : low/medium/high, $0.002/img)
- **Reformatage** : GPT-4o mini ou Mistral (Molmo2 = les yeux, LLM = le rédacteur ciblé)
- **UI** : NiceGUI ou Gradio
- **Export** : ZIP généré côté serveur

### Distribution potentielle
- GitHub + post CivitAI section "Tools"
- Communauté r/StableDiffusion, r/LocalLLaMA
- Version locale (Python) ou SaaS léger (quota API à l'usage)

---

## CONCEPT 05 — Assistant IA Permanent sur Android (Edge AI)
**Date** : 25 avril 2026  
**Statut** : 💡 Idée exploratoire — dépend de la maturité des SDK Gemma mobile

### L'idée
Un assistant IA qui tourne **nativement sur un téléphone Android**, sans dépendance cloud, disponible en permanence même hors ligne. Basé sur Gemma 4 de Google, optimisé pour les SoC mobiles (Snapdragon/Tensor/Kirin).

Ce n'est pas un accès à un LLM distant (comme l'app Gemini) — c'est un modèle qui **vit sur le téléphone**.

### Ce que ça change fondamentalement
| Approche actuelle | Edge AI |
|---|---|
| Requiert internet | Fonctionne hors ligne |
| Données envoyées au cloud | 100% privé, données sur device |
| Coût par requête | Zéro coût d'inférence |
| Latence réseau | Réponse en millisecondes |

### Modèles réalistes selon hardware
| Modèle | Faisabilité sur Kirin 980 / 8GB RAM |
|---|---|
| Gemma 4 1B (quantisé 4-bit) | ✅ Confortable |
| Gemma 4 2B (quantisé 4-bit) | ✅ Fonctionnel, légèrement lent |
| Gemma 4 4B+ | ❌ Trop lourd |

### SDK / frameworks possibles
- **Google AI Edge / MediaPipe** (officiel, nécessite Google Play Services)
- **MLC-LLM** : framework open-source, pas de dépendance Google
- **llama.cpp Android** : via Termux ou app native, très flexible

### Vision à deux niveaux

**Niveau 1 — Standalone** : assistant personnel sur téléphone, répond à des questions, accède au contexte local (agenda, notes, messages).

**Niveau 2 — Interface mobile d'OGMA** : quand le téléphone est sur WiFi, se synchronise avec OGMA (mémoire persistante, historique, contexte long). Le modèle mobile = interface légère. OGMA = cerveau étendu.

```
[Hors ligne]  →  Gemma 4 local sur device  →  réponses légères
[Sur WiFi]    →  Gemma 4 + sync OGMA       →  mémoire longue + personnalité complète
```

### Lien avec OGMA
Ce concept est naturellement complémentaire à OGMA plutôt que concurrent. OGMA reste le cerveau principal (PC, mémoire longue, Archiviste) ; l'app mobile est sa **présence mobile légère** — toujours disponible, avec accès partiel à la mémoire quand connecté.

---

*Prochaines idées à documenter ici au fil du brainstorming*
