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

*Prochaines idées à documenter ici au fil du brainstorming*
