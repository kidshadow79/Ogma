# 🖋️ EXTENSION BIOGRAPHIE PROFIL - DOCUMENTATION TECHNIQUE

## 📋 Vue d'ensemble

L'extension **Biographie Profil** permet à l'IA principale d'OGMA de créer et maintenir des profils psychologiques approfondis pour chaque utilisateur, facilitant une compréhension empathique et personnalisée des interactions.

---

## 🏗️ Architecture générale

```
extensions/biographie_profil/
├── __init__.py              # Point d'entrée, initialisation
├── biography_manager.py     # Logique métier principale
├── magic_phrases.py         # Détection et traitement phrases magiques
└── ui_components.py         # Interface utilisateur (modal, boutons)

data/biographies/
└── [nom_utilisateur]/
    ├── metadata.json        # Métadonnées utilisateur
    ├── volume1_memories.json # Souvenirs classés (Volume 1)
    └── volume2_narrative.md  # Biographie narrative (Volume 2)
```

---

## 📖 VOLUME 1 - Collection de souvenirs

### Fonctionnement
- **Source** : Base FAISS vectorielle d'OGMA
- **Recherche** : Embedding "souvenirs concernant [nom]"
- **Filtrage** : Souvenirs mentionnant réellement l'utilisateur
- **Format** : JSON structuré avec métadonnées

### Déclenchement
- **Interface** : Bouton "🔄 Traiter souvenirs" dans les paramètres
- **Processus** :
  1. Recherche directe dans FAISS (k=100)
  2. Récupération depuis SQLite avec tous les champs
  3. Filtrage par nom dans content/summary/title/text_original
  4. Sauvegarde JSON dans `volume1_memories.json`

### Structure Volume 1
```json
{
  "user_name": "Utilisateur",
  "created_at": "2025-09-30T...",
  "total_memories": 26,
  "memories": [
    {
      "memory_id": "ai-xxx",
      "content": "Contenu du souvenir",
      "summary": "Résumé",
      "title": "Titre",
      "created_at": "Date",
      "score_impact": 150.0,
      "similarity_score": 0.85
    }
  ]
}
```

### Utilisation
- **Injection automatique** : Première mention du nom dans une conversation
- **Consultation IA** : Phrase magique "il faut que je consulte la biographie de [nom]"

---

## 📝 VOLUME 2 - Biographie narrative (EN DÉVELOPPEMENT)

### Concept
- **Objectif** : Profil psychologique/psychiatrique/intellectuel approfondi
- **Approche** : IA agit comme professionnel du psyché
- **But dual** :
  - Utilisateur comprend mieux sa psychologie
  - IA développe empathie authentique

### Fonctionnement prévu
- **Source** : Conversation actuelle INTÉGRALE (JSON complet)
- **Déclenchement** : Phrase magique "complète ma biographie"
- **Logique** : Enrichissement progressif (jamais effacement)
- **Format** : Markdown structuré avec chapitres thématiques

### Structure Volume 2 (à implémenter)
```markdown
# BIOGRAPHIE PSYCHOLOGIQUE - [Nom]

## I. PROFIL GÉNÉRAL
### Traits dominants
### Mécanismes de défense

## II. PATTERNS RELATIONNELS
### Avec l'IA
### Indices relations humaines

## III. ÉVOLUTION OBSERVÉE
### [Date] - [Changement observé]
Source: [Conversation X]

## IV. ANALYSE APPROFONDIE
### Motivations profondes
### Zones de développement
```

---

## 🎯 Phrases magiques

### Utilisateur (mise à jour)
- `"complète ma biographie"` → Enrichit Volume 2
- `"complète ma bio"`
- `"met à jour ma biographie"`
- `"enrichis mon profil"`

### IA (consultation)
- `"il faut que je consulte la biographie de [nom]"` → Charge Volume 1

### Injection automatique
- **Détection** : Première mention d'un prénom dans la conversation
- **Action** : Injection silencieuse du Volume 1 dans le contexte système
- **Fréquence** : Une seule fois par nom et par conversation

---

## 🔧 Interface utilisateur

### Bouton d'extension
- **Icône** : ✒️ (plume)
- **Position** : Header OGMA, à côté du bouton journal
- **Style** : Gradient bleu cohérent avec le design

### Modal de paramètres
- **Toggle ON/OFF** : Activation/désactivation extension
- **Sauvegarde automatique** : État persistant entre sessions
- **Actions** :
  - `🔄 Traiter souvenirs` : Génère/MAJ Volume 1
  - `📖 Créer Volume 2` : Génère biographie narrative
  - `💾 Sauvegarder paramètres` : Sauvegarde manuelle
  - `📁 Ouvrir dossier` : Accès aux fichiers biographies

---

## ⚙️ Configuration

### Fichiers de config
- `data/extensions/biography_config.json` : État ON/OFF extension
- `data/biographies/[nom]/metadata.json` : Métadonnées utilisateur

### Paramètres persistants
- État activation extension
- Instructions Volume 2 personnalisables (à implémenter)

---

## 🔄 Flux d'exécution

### Initialisation
1. `ogma_ng.py` → `initialize_biography_extension()`
2. Création `BiographyManager` + `BiographyUI` + `BiographyMagicPhrases`
3. Chargement état sauvegardé
4. Intégration bouton header

### Traitement Volume 1
1. Utilisateur saisit nom + clic "🔄 Traiter souvenirs"
2. `biography_manager.get_user_memories_from_faiss()`
3. Recherche directe FAISS + récupération SQLite
4. Filtrage par nom dans tous les champs
5. Sauvegarde JSON + métadonnées

### Détection phrases magiques
1. Message utilisateur → `_send_chat_message()`
2. `magic_phrases.handle_magic_phrases()`
3. Distinction type : 'display' vs 'inject'
4. Traitement approprié selon le type

---

## 🚨 Points d'attention techniques

### Problèmes résolus
- **Import SQLite** : Utilisation `sqlite3.connect(db_path)` temporaire
- **Colonnes SQL** : Mapping correct `id`→`memory_id`, `text_original`→`content`
- **Injection automatique** : Distinction affichage/injection silencieuse
- **Sérialisation UI** : Remplacement Switch par bouton custom

### Volume 2 - À implémenter
- **Instructions modifiables** : Interface paramètres pour customiser prompt IA
- **Accès conversation intégrale** : Récupération JSON complet (pas résumé)
- **Logique enrichissement** : Ajout/correction sans effacement
- **Appel IA fonctionnel** : Résolution problème d'accès API

### Méthodes critiques
- `_search_memories_for_biography()` : Recherche directe FAISS sans filtrage strict
- `handle_magic_phrases()` : Détection et routage phrases magiques
- `_format_volume1_for_ai()` : Formatage pour injection contexte

---

## 📊 État actuel

### ✅ Fonctionnel
- Volume 1 : Création, sauvegarde, chargement, injection
- Phrases magiques : Détection et traitement utilisateur/IA
- Interface : Modal paramètres, boutons, notifications
- Persistance : Sauvegarde état extension

### 🚧 En développement
- Volume 2 : Instructions personnalisables, enrichissement progressif
- Appel IA : Résolution accès API pour génération narrative

### 🎯 Objectifs
- Profil psychologique évolutif de haute qualité
- Empathie IA authentique basée sur compréhension profonde
- Auto-connaissance utilisateur via miroir psychologique professionnel