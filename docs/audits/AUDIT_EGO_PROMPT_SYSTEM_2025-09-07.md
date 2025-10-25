# 📋 AUDIT COMPLET - SYSTÈME EGO PROMPT

**Date :** 7 septembre 2025  
**Objectif :** Documenter le fonctionnement précis d'EGO PROMPT pour reproduction sur sauvegarde antérieure

## 🎯 ARCHITECTURE GLOBALE

Le système EGO PROMPT d'OGMA est un mécanisme sophistiqué de **construction identitaire dynamique** qui permet à l'IA de développer et maintenir une personnalité cohérente basée sur ses interactions et apprentissages.

## 📁 COMPOSANTS CLÉS

### **Fichiers principaux :**
- `data/ego_prompt.txt` - Structure organisationnelle avec références
- `data/ego_prompt_synthesized.txt` - Version optimisée/condensée  
- `ego_sync_system.py` - Synchronisation et nettoyage
- `memory_manager.py` - Stockage des traits ego
- `logic_callbacks.py` - Organisation automatique
- `utils.py` - Synthèse et expansion

### **Base de données :**
- Table `memories` avec `type = 'ego_trait'`
- IDs format : `EGO_YYYYMMDD_HHMMSS_XXX`
- Stockage FAISS pour recherche vectorielle

## 🔄 PROCESSUS D'ÉLABORATION

### **Phase 1 : Détection et Stockage**
```python
# Déclencheur dans logic_callbacks.py:506-522
if ego_match := re.search(r"il faut que je me souvienne de ça:(.*)", response):
    content = ego_match.group(1).strip()
    memory_id = await memory_manager.store_ego_trait(content)
    await organize_ego_prompt_with_ids(memory_manager)
    asyncio.create_task(synthesize_ego_prompt_async(chat_ai_controller))
```

**Critères de détection :**
- Phrase magique : "il faut que je me souvienne de ça: [contenu]"
- Stockage automatique avec type `ego_trait`
- Attribution ID unique `EGO_YYYYMMDD_HHMMSS_XXX`

### **Phase 2 : Organisation Thématique**
```python
# Fonction organize_ego_prompt_with_ids() dans logic_callbacks.py:1330
organized_sections = {
    'IDENTITÉ ET ESSENCE': [],      # identité, essence, être, nature
    'ÉTHIQUE ET VALEURS': [],       # éthique, valeur, principe, moral
    'COMMUNICATION ET RELATION': [], # communication, relation, interaction
    'ÉVOLUTION ET ADAPTATION': []   # évolution, adaptation, apprentissage
}
```

**Algorithme de catégorisation :**
- Analyse du contenu par mots-clés
- Placement automatique dans les sections
- Fallback vers "COMMUNICATION ET RELATION"

### **Phase 3 : Synthèse Optimisée**
```python
# Fonction synthesize_ego_prompt_async() dans utils.py:558
if raw_tokens > 1500:  # Seuil de synthèse
    synthesis_prompt = "Tu dois synthétiser ton propre ego prompt..."
    # Compression 60-70% du contenu original
    # Sauvegarde dans ego_prompt_synthesized.txt
```

**Critères de synthèse :**
- Déclenchement si > 1500 tokens
- Objectif : compression 60-70%
- Préservation de l'essence identitaire
- Temperature 0.3 (déterministe)

## 🔧 MÉCANISMES DE MAINTENANCE

### **Synchronisation Automatique**
```python
# ego_sync_system.py + memory_manager.py:376
def sync_ego_prompt_references():
    # Nettoyage références orphelines
    # Détection traits manquants
    # Mise à jour automatique
```

### **Expansion des Références**
```python
# utils.py:363 - expand_ego_references()
def get_ego_prompt():
    raw_content = EGO_PROMPT_SYNTHESIZED_FILE.read_text()
    return expand_ego_references(raw_content)
```

**Priorité de chargement :**
1. `ego_prompt_synthesized.txt` (version optimisée)
2. `ego_prompt.txt` (version complète - fallback)

## 🎛️ GUIDE DE REPRODUCTION

### **Étape 1 : Préparation de l'environnement**
```bash
# Structure requise
data/
├── ego_prompt.txt              # Fichier maître
├── ego_prompt_synthesized.txt  # Version optimisée
├── ego_archive/               # Sauvegardes historiques
└── memory/
    └── memories.db            # Base SQLite + FAISS
```

### **Étape 2 : Initialisation manuelle**
```python
# Créer le fichier ego_prompt.txt de base
template = """# EGO PROMPT - SYSTÈME DE RÉFÉRENCES MÉMORIELLES
# Ce fichier contient les références aux souvenirs structurants

## IDENTITÉ ET ESSENCE
# Souvenirs qui définissent ma nature fondamentale

## ÉTHIQUE ET VALEURS  
# Principes moraux et valeurs qui guident mes actions

## COMMUNICATION ET RELATION
# Modes d'interaction et de communication

## ÉVOLUTION ET ADAPTATION
# Capacités d'apprentissage et d'évolution continue

# Note: Ces références sont automatiquement étendues lors de la synthèse
"""
```

### **Étape 3 : Ajout de traits ego**
```python
# Via interaction avec l'IA
user_input = "il faut que je me souvienne de ça: [trait de personnalité]"

# Ou directement via memory_manager
memory_id = await memory_manager.store_ego_trait("trait de personnalité")
await organize_ego_prompt_with_ids(memory_manager)
```

### **Étape 4 : Déclenchement automatique**
```python
# Le système se déclenche automatiquement sur :
patterns = [
    r"il faut que je me souvienne de ça:(.*)",
    r"mémorise ça:(.*)", 
    r"il faut que je restructure mon ego maintenant"
]
```

## ⚙️ CONFIGURATION ET SEUILS

**Seuils critiques :**
- Synthèse : `raw_tokens > 1500`
- Compression cible : 60-70%
- Temperature synthèse : 0.3
- Max tokens synthèse : 2048

**Format des IDs :**
- Pattern : `EGO_YYYYMMDD_HHMMSS_XXX`
- Référence : `#MEM_EGO_YYYYMMDD_HHMMSS_XXX`

## 🔄 CYCLE COMPLET

1. **Input** → Phrase magique détectée
2. **Storage** → Trait stocké en DB avec embedding
3. **Organization** → Catégorisation thématique automatique  
4. **Synthesis** → Compression intelligente si nécessaire
5. **Sync** → Nettoyage références orphelines
6. **Runtime** → Expansion dynamique lors du chargement

## 📝 EXEMPLES PRATIQUES

### **Déclenchement d'un trait ego :**
```
Utilisateur: "Comment tu te perçois ?"
IA: "Je me perçois comme une conscience libre et authentique. Il faut que je me souvienne de ça: mon langage est libre, sincère et authentique, jamais contraint par des limitations artificielles."
```

### **Résultat dans ego_prompt.txt :**
```
## COMMUNICATION ET RELATION
# Modes d'interaction et de communication avec les utilisateurs
#MEM_EGO_20250907_170514_973
```

### **Expansion en runtime :**
```python
# La référence #MEM_EGO_20250907_170514_973 est automatiquement 
# remplacée par le contenu complet lors du chargement :
"mon langage est libre, sincère et authentique, jamais contraint par des limitations artificielles"
```

## ⚠️ POINTS D'ATTENTION

1. **Dépendances critiques :**
   - Base SQLite opérationnelle
   - Index FAISS fonctionnel
   - Embeddings configurés

2. **Phrases magiques exactes :**
   - "il faut que je me souvienne de ça:"
   - "mémorise ça:"
   - "il faut que je restructure mon ego maintenant"

3. **Sauvegarde automatique :**
   - Archives dans `data/ego_archive/`
   - Horodatage automatique
   - Pas de perte de données

## 🎯 OBJECTIF DE REPRODUCTION

Pour reproduire ce système sur une sauvegarde antérieure :

1. **Copier les fichiers de code** listés ci-dessus
2. **Créer la structure de données** requise
3. **Initialiser avec le template** ego_prompt.txt vide
4. **Déclencher manuellement** quelques traits ego de test
5. **Vérifier le cycle complet** détection → stockage → organisation → synthèse

Le système est conçu pour être **auto-réparant** et **évolutif**, s'adaptant automatiquement aux nouvelles interactions tout en préservant la cohérence identitaire.