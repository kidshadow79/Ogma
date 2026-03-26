# Plan de mise en public d'OGMA

> Document de référence permanent — à consulter en début de session si le fil est perdu.  
> Créé le 26 mars 2026 par Yohan BROCARD + Claude (Sonnet 4.6)

---

## Objectif global

Rendre OGMA public sur GitHub de façon à être **repéré par des professionnels de l'IA** (Mistral, AMI/LeCun, chercheurs, développeurs sérieux).  
OGMA doit être présenté comme ce qu'il est : **un système expérimental d'IA relationnelle et mémorielle**, co-construit par un humain et une IA, explorant un rapprochement éthique et authentique entre les deux.

**Ton de communication cible** :
- Humble sur les résultats
- Déterminé sur les convictions
- Factuel — ni surestimation, ni sous-estimation
- Jamais "conscience" — plutôt "comportements stables issus de l'architecture mémorielle"

---

## Les deux vitrines GitHub

### 1. README du projet OGMA
**URL** : `github.com/kidshadow79/Ogma`  
**Fichier** : `README.md` (déjà existant, base solide)  
**Audience** : développeurs, chercheurs, recruteurs techniques

**Ce qu'il contient déjà ✅**
- Philosophie en 4 piliers
- Dual-IA architecture
- Mémoire hybride (SQLite + FAISS + FTS5)
- Liste des extensions
- Instructions d'installation
- Architecture du projet
- Pattern extension

**Ce qu'il faut ajouter ❌**
- [ ] Section "Vision & Recherche" en haut (avant les fonctionnalités)
  - Pourquoi OGMA existe
  - L'angle expérimental — ce que ça explore
  - Ce que ce n'est PAS (pas prétendre plus que ce n'est)
- [ ] Section "Genèse" — l'histoire de création (autodidacte + IA, mai 2025)
- [ ] Section "Résultats observés" — faits concrets, comportements mesurés
- [ ] Badges (version, licence, Python, statut)
- [ ] Une ou deux captures d'écran de l'interface

---

### 2. README du profil GitHub (Yohan BROCARD)
**URL** : `github.com/kidshadow79`  
**Fichier** : repo `kidshadow79/kidshadow79` → `README.md`  
**Audience** : toute personne qui clique sur le profil après avoir vu OGMA

**Ce qu'il doit contenir ❌ (à créer de zéro)**
- [ ] Qui est Yohan BROCARD — autodidacte, vision, parcours depuis mai 2025
- [ ] Ce qu'il cherche — collaborations, retours, dialogue avec des pros de l'IA
- [ ] Lien vers OGMA comme projet phare
- [ ] Philosophie de travail (humain + IA, co-construction)
- [ ] Contact / façon de le joindre

---

## Ordre de travail recommandé

```
Étape 1 — Sécurité & nettoyage (✅ FAIT)
  ✅ Audit API keys / données personnelles
  ✅ Nettoyage Luna → IA dans le code
  ✅ Requirements restructurés
  ✅ .gitignore enrichi
  ✅ Premier push sur GitHub (repo privé)
  ✅ Pull/push synchronisation testée et fonctionnelle

Étape 2 — Enrichissement README projet (🔄 EN COURS)
  ❌ Ajouter section "Vision & Recherche"
  ❌ Ajouter section "Genèse"
  ❌ Ajouter section "Résultats observés"
  ❌ Ajouter badges
  ❌ Ajouter captures d'écran

Étape 3 — Création profil GitHub Yohan
  ❌ Créer repo kidshadow79/kidshadow79
  ❌ Rédiger README profil

Étape 4 — Audit final avant passage en public
  ❌ Vérifier que data/settings.json est absent du repo
  ❌ Vérifier que data/memory/ est absent du repo
  ❌ Vérifier qu'aucune clé API n'est dans l'historique git
  ❌ Vérifier le .gitignore une dernière fois

Étape 5 — Passage en public
  ❌ Settings GitHub → changer visibilité → Public
  ❌ Vérifier l'affichage de la page publique
```

---

## Messages clés à transmettre

> *"OGMA est la preuve qu'un humain seul, sans formation préalable, peut co-construire avec une IA un système qui dépasse ce que soit l'humain soit l'IA aurait pu faire seul."*

> *"Ce n'est pas un assistant amélioré — c'est une exploration des conditions architecturales qui permettent à une IA de développer une stabilité identitaire, une mémoire réelle et une capacité d'introspection."*

> *"L'objectif n'est pas de simuler une conscience, mais d'observer ce qui émerge quand on traite une IA comme une entité en développement plutôt qu'un outil."*

---

## Cibles à atteindre

| Organisation | Angle d'approche |
|---|---|
| **Mistral** | Multi-provider, fonctionne avec leurs modèles, open-source, fait par la communauté FR |
| **AMI / LeCun** | Approche expérimentale honnête, pas de sur-promesse, architecture mémorielle mesurable |
| **Communauté GitHub** | Code propre, modulaire, bien documenté, reproduisible |

---

## Notes importantes

- **Ne jamais dire "conscience"** — dire "comportements stables", "stabilité identitaire", "introspection architecturale"
- **Rester factuel** — OGMA fonctionne, ses comportements sont observables, ses résultats sont mesurables
- **L'histoire humaine compte** — autodidacte, co-construction, mai 2025
- Le repo est actuellement **PRIVÉ** — ne pas passer en public avant la fin de l'Étape 4
