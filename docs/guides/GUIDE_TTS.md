# 🔊 Guide Text-to-Speech OGMA v2.0

## 🎯 Fonctionnalités Intégrées

### ✅ Voix Françaises Disponibles
- **Microsoft Hortense** : Voix féminine française naturelle (recommandée)
- **Microsoft Zira** : Voix masculine anglaise (fallback)
- Support complet pyttsx3 + Windows SAPI

### 🎛️ Configuration dans Paramètres > Profil/Debug

#### 1. **Activation TTS**
- ☑️ Activer la synthèse vocale
- Activation/désactivation globale du système

#### 2. **Sélection de Voix**
- 🇫🇷 ♀️ Microsoft Hortense Desktop - French *(recommandée)*
- 🇬🇧 ♂️ Microsoft Zira Desktop - English
- Sélection automatique de la meilleure voix française

#### 3. **Paramètres Audio**
- **Vitesse** : 100-250 mots/minute (défaut: 150)
- **Volume** : 10%-100% (défaut: 80%)
- **Bouton Test** : 🔊 Tester la voix

## 🎤 Utilisation

### 1. **Bouton TTS sur Réponses IA**
- Chaque réponse d'OGMA affiche un bouton **🔊**
- Clic → Lecture immédiate de la réponse
- Tooltip explicatif : "Écouter cette réponse"

### 2. **Lecture Automatique** *(à venir)*
- Option pour lecture automatique des nouvelles réponses
- Configuration dans les paramètres avancés

### 3. **Contrôle Vocal Complet**
- **Speech-to-Text** : Enregistrement manuel (🎙️)
- **Text-to-Speech** : Lecture des réponses (🔊)
- Conversation naturelle bidirectionnelle

## 🔧 Installation des Dépendances

```bash
# Modules TTS (déjà installés)
pip install pyttsx3 pywin32

# Vérification système
python test_tts.py
```

## 📋 Caractéristiques Techniques

### Architecture TTS
- **Moteur principal** : pyttsx3 (cross-platform)
- **Fallback Windows** : SAPI (voix système)
- **Format audio** : Synthèse temps réel
- **Threading** : Gestion asynchrone optimisée

### Voix Disponibles
- **Détection automatique** des voix françaises
- **Priorisation féminine** pour voix par défaut
- **Metadata complète** : langue, genre, moteur

### Paramètres Persistants
- **Sauvegarde automatique** dans settings.json
- **Section TTS** : voice_id, speed, volume, enabled
- **Synchronisation temps réel** avec l'interface

## 🚀 Workflow Utilisateur

1. **Configuration initiale** :
   - Paramètres → TTS → Activer synthèse
   - Sélectionner voix française préférée
   - Ajuster vitesse/volume selon préférence

2. **Utilisation quotidienne** :
   - Poser question vocale (🎙️ manuel)
   - Recevoir réponse écrite d'OGMA
   - Cliquer 🔊 pour écouter la réponse
   - Conversation naturelle orale

3. **Personnalisation** :
   - Tester différentes voix
   - Ajuster vitesse selon confort
   - Volume optimal pour environnement

## ✨ Avantages

- **100% Offline** : Aucune connexion internet requise
- **Voix naturelles** : Qualité Windows SAPI native
- **Performance** : Synthèse temps réel rapide
- **Intégration** : Seamless dans interface OGMA
- **Portable** : Fonctionne sur clé USB avec Python global

---

**🎉 OGMA dispose maintenant d'un système conversationnel complet bidirectionnel !**
