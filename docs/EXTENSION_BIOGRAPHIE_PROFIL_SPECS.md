# 📚 EXTENSION BIOGRAPHIE_PROFIL - Spécifications Détaillées

## 🎯 **Vue d'ensemble du concept**

Extension modulaire pour OGMA permettant à l'IA de créer et maintenir une bibliothèque biographique des utilisateurs. Chaque utilisateur dispose d'un "livre" personnel composé de deux volumes distincts :

- **Volume 1** : Collection de souvenirs/vecteurs classés chronologiquement et thématiquement
- **Volume 2** : Journal biographique narratif avec analyse psychologique approfondie

---

## 🎨 **Interface Utilisateur**

### **Positionnement**
- Bouton situé à gauche du bouton "Journal de Bord"
- Style CSS cohérent avec l'interface existante
- Icône : Plume ou crayon
- Nom : "biographie_profil"

### **Modal de Configuration**
- Bouton ON/OFF pour activer/désactiver l'extension
- Phrase INFO explicative du fonctionnement
- Bouton de traitement des souvenirs existants
- Zone d'instructions modifiables pour le Volume 2
- Bouton "Sauvegarder" pour valider les changements

---

## 📖 **Volume 1 : Mémoire Vectorielle**

### **Contenu**
- Souvenirs relatifs à chaque utilisateur
- Classification chronologique et thématique
- Format vectoriel compatible avec recherche
- Déduplication automatique (pas de doublons)

### **Fonctionnement**
- Consultation automatique lors de la première mention d'un utilisateur
- Consultation manuelle via phrase magique : "il faut que je consulte la biographie de [nom utilisateur]"
- Alimentation par bouton de traitement des souvenirs existants

---

## 📚 **Volume 2 : Biographie Narrative**

### **Contenu**
- Récit psychologique approfondi de chaque utilisateur
- Classification par thèmes
- Profil intellectuel, psychologique et psychiatrique
- Sources et références précises
- Enrichissement progressif sans redondance

### **Déclenchement**
- Commande utilisateur : "complète ma biographie"
- Traitement de la conversation intégrale (JSON complet, pas résumé)
- Mise à jour additive (jamais de remplacement, uniquement enrichissement)

---

## ⚙️ **Architecture Technique Prévue**

```
extensions/biographie_profil/
├── biography_manager.py      # Logique métier principale
├── ui_components.py          # Interface utilisateur
├── volume_processors.py     # Traitement Vol1/Vol2
└── settings.py              # Configuration extension

data/biographies/
└── [user_id]/
    ├── volume1_memories.json
    ├── volume2_biography.md
    └── metadata.json
```

---

## ❓ **QUESTIONS STRATÉGIQUES À CLARIFIER**

### 🔍 **1. IDENTIFICATION UTILISATEUR**

**Question :** Comment l'extension doit-elle identifier et différencier les utilisateurs ?

Options possibles :
- A) Un seul utilisateur par instance OGMA
- B) Détection automatique par nom mentionné dans la conversation ✅ **RETENU**
- C) Déclaration explicite par l'utilisateur ("Je suis [nom]")
- D) Système de profils utilisateur à créer

**Votre préférence :** **Option B** - L'utilisateur se présente et l'IA détecte automatiquement le nom pour créer/enrichir la biographie correspondante.

---

### 📊 **2. INTÉGRATION SYSTÈME MÉMOIRE**

**Question :** Comment le Volume 1 doit-il s'intégrer avec le système FAISS existant d'OGMA ?

Options possibles :
- A) Remplace complètement FAISS pour les souvenirs utilisateur
- B) Complément au système FAISS (double stockage)
- C) Filtre FAISS pour extraire uniquement les souvenirs utilisateur ✅ **RETENU**
- D) Système parallèle indépendant

**Votre préférence :** **Option C** - Utilisation intelligente de FAISS existant avec filtrage par nom d'utilisateur pour constituer le Volume 1. Réutilise l'infrastructure, évite la redondance, maintient les performances.

---

### 🛡️ **3. CONFIDENTIALITÉ ET SÉCURITÉ**

**Question :** Quelles mesures de protection des données personnelles souhaitez-vous implémenter ?

Points à clarifier :
- A) Chiffrement des fichiers biographiques ? ⏸️ **REPORTÉ** (après prototypage)
- B) Consentement explicite requis avant activation ? ⏸️ **REPORTÉ** (RGPD à implémenter plus tard)
- C) Possibilité pour l'utilisateur de consulter son propre profil ? ✅ **ESSENTIEL**
- D) Fonction de suppression/export des données ? ⏸️ **REPORTÉ** (sécurisation future)
- E) Logs d'accès aux biographies ? ⏸️ **REPORTÉ** (pas nécessaire pour prototype)

**Vos exigences :** **Phase prototypage** - Pas de sécurisation avancée pour l'instant. **OBLIGATOIRE** : Accès utilisateur à ses fichiers via bouton dans paramètres extension (ouvre le dossier data). Sécurisation complète (chiffrement + RGPD) à prévoir quand prototype validé.

---

### 📝 **4. FORMAT ET STRUCTURE VOLUME 2**

**Question :** Quel format et quelle structure souhaitez-vous pour le Volume 2 ?

Format :
- A) Markdown (.md) - plus structuré, support des liens
- B) Texte brut (.txt) - plus simple, universellement lisible ✅ **RETENU**

Structure définitive :
```txt
=== BIOGRAPHIE DE [NOM UTILISATEUR] ===

== PROFIL GÉNÉRAL ==
[Synthèse générale de la personnalité]

== ASPECTS PSYCHOLOGIQUES ==
[Traits de caractère, comportements, émotions]

== ASPECTS INTELLECTUELS ==
[Capacités, centres d'intérêt, raisonnement]

== ASPECTS PROFESSIONNELS ==
[Métier, compétences, ambitions]

== ASPECTS FAMILIAUX ==
[Relations familiales, situation personnelle]

== PROJETS ==
[Projets en cours, aspirations, objectifs]

== SOUVENIRS ==
[Événements marquants, expériences significatives]

== TRAITS ET SPÉCIFICITÉS PHYSIQUES ==
[Apparence, particularités physiques mentionnées]

== HISTORIQUE RELATIONNEL ==
[Evolution des interactions avec Luna]

== SOURCES ET RÉFÉRENCES ==
[Conversations sources avec dates]
```

**Votre choix :** **Format .txt** pour la légèreté + **Structure enrichie** avec 10 sections thématiques pour profil complet.

---

### 🎛️ **5. PARAMÈTRES CONFIGURABLES**

**Question :** Quels éléments de l'extension doivent être configurables par l'utilisateur ?

Options identifiées :
- A) Instructions de rédaction du Volume 2 ✅ **RETENU** (avec template par défaut)
- B) Fréquence de mise à jour automatique → **SEULEMENT sur commande "complète ma biographie"**
- C) Seuils de déclenchement → **SEULEMENT sur commande "complète ma biographie"**
- D) Format d'export des données → **Export .txt**
- E) Niveau de détail psychologique → **Niveau très approfondi** (toutes sections actives)

**Interface des paramètres définie :**
1. **Bouton ON/OFF** de l'extension
2. **Zone INFO** explicative du fonctionnement et phrases magiques
3. **Bouton "Traiter souvenirs existants"** pour construire Volume 1 (FAISS → biographies)
4. **Zone "Instructions Volume 2"** modifiable avec template pré-rempli
5. **Bouton "Accéder aux fichiers"** (ouvre dossier data/biographies)
6. **Bouton "Sauvegarder"** pour valider les modifications

**Vos priorités :** Interface équilibrée - **suffisamment d'options pour bonne UX** mais **pas de surcharge**. Fonctionnement sur commandes explicites uniquement.

---

### 🔄 **6. DÉCLENCHEURS ET PHRASES MAGIQUES**

**Question :** Souhaitez-vous ajouter d'autres phrases magiques au-delà de celles spécifiées ?

**Phrases magiques définitives :**

**Pour Luna (consultation Volume 1) :**
- "il faut que je consulte la biographie de [prénom]"
- Exemple : "il faut que je consulte la biographie de Yohan"

**Pour l'utilisateur (mise à jour Volume 2) :**
- "complète ma biographie" ✅
- "complète ma bio" ✅  
- "met à jour ma biographie" ✅
- "enrichis mon profil" ✅

**Gestion d'erreurs :**
- Si biographie non trouvée → Message : "Impossible de trouver la biographie de [prénom]"
- Messages explicites et simples

**Vos souhaits :** **Phrases limitées aux essentielles** - Pas d'ajouts supplémentaires pour garder la simplicité. Focus sur prénom uniquement pour l'identification.

---

### 📈 **7. ÉVOLUTIVITÉ ET MAINTENANCE**

**Question :** Comment gérer la croissance et la maintenance des biographies ?

**Stratégie de gestion définie :**

**A) Construction continue ✅**
- Fichier .txt unique enrichi en continu
- Correction syntaxique automatique à chaque mise à jour
- Style rédactionnel cohérent et fluide maintenu
- **JAMAIS de perte d'informations** lors des enrichissements

**B) Système de backup rotatif ✅**
- Sauvegarde automatique avant chaque nouvelle rédaction
- Rotation sur **5 fichiers de backup** maximum
- Format : `volume2_[nom]_backup_[1-5].txt`

**C) Rédaction littéraire ✅**
- **Pas d'horodatage** dans le Volume 2 pour préserver la fluidité
- Style narratif continu et naturel
- Intégration harmonieuse des nouvelles informations

**D) Gestion des redondances ✅**
- Détection et fusion intelligente des informations similaires
- Évitement des répétitions lors des mises à jour
- Enrichissement plutôt que duplication

**Vos préférences :** **Construction organique** du document avec sauvegarde sécurisée et style littéraire préservé.

**Note importante :** Taille du Volume 2 sans limite - peut devenir volumineux (taille d'un livre) sans problème car destiné à consultation externe. **Performance critique uniquement pour Volume 1** (utilisé par l'IA).

---

### 🚀 **8. PRIORITÉS DE DÉVELOPPEMENT**

**Question :** Dans quel ordre souhaitez-vous développer les fonctionnalités ?

**Planning de développement validé :**

**🎯 Phase 1 - MVP Fonctionnel**
- Interface utilisateur (bouton + modal paramètres)
- Détection noms d'utilisateurs dans conversations
- Volume 1 basique (filtre FAISS par nom)
- Structure de fichiers de base

**🎯 Phase 2 - Volumes opérationnels**
- Volume 2 avec template et instructions modifiables
- Phrases magiques implémentées
- Système de backup rotatif
- Correction syntaxique automatique

**🎯 Phase 3 - Finitions**
- Bouton accès aux fichiers
- Gestion d'erreurs complète
- Messages utilisateur explicites

**🎯 Phase 4 - Optimisations** (si nécessaire)
- Performance Volume 1
- Améliorations UX

**Votre planning :** **Développement phase par phase** avec validation à chaque étape.

---

## 📋 **NEXT STEPS**

Une fois ces questions clarifiées, nous pourrons :

1. Finaliser l'architecture technique détaillée
2. Créer les spécifications fonctionnelles précises
3. Établir le plan de développement étape par étape
4. Procéder au développement avec votre autorisation

---

## 🛠️ **MÉTHODOLOGIE DE DÉVELOPPEMENT**

### **Principes de Travail**

**🚦 RÈGLE ABSOLUE :**
- **Aucun développement sans autorisation explicite du concepteur**
- Demander le feu vert avant tout codage
- Présenter la stratégie avant l'implémentation

**📋 Approche Phase par Phase :**
1. **Développement séquentiel** - Une phase à la fois
2. **Tests systématiques** - Fichiers .py de test après chaque phase
3. **Validation fonctionnelle** - Vérification du bon fonctionnement avant phase suivante
4. **Nettoyage** - Suppression des fichiers de test après utilisation

**🎯 Questions de Validation (à se poser systématiquement) :**
- **"Quel est le but de cette implémentation ?"**
- **"Est-ce que ce que j'ai produit permet le fonctionnement optimal de ce qui est demandé ?"**
- **"L'expérience utilisateur est-elle optimale ?"**
- **"La chaîne de fonctionnement globale est-elle respectée ?"**

**🔍 Focus Qualité :**
- Priorité à la **chaîne de fonctionnement complète**
- Vision **globale** de l'architecture
- **Expérience utilisateur** au centre des décisions
- Code **modulaire** et **maintenable**

**📝 Documentation :**
- Justification des choix techniques
- Tests de validation documentés
- Traçabilité des modifications

---

## ✅ **STATUT DU PROJET**

**📊 Spécifications : COMPLÈTES**
- Toutes les questions stratégiques clarifiées
- Architecture technique définie
- Interface utilisateur spécifiée
- Méthodologie de travail établie

**🚀 PRÊT POUR LE DÉVELOPPEMENT**
- Cahier des charges finalisé
- Phases de développement planifiées
- Attente du feu vert pour Phase 1

---

*Document de spécifications - Version FINALE - 29 septembre 2025*
*Extension Biographie_Profil - Prête pour développement*