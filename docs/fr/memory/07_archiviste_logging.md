# Logs de l'Archiviste

**Sources vérifiées** : `archiviste_logger.py`, `data/archiviste_tokens_debug.jsonl`

---

## Objectif

L'Archiviste opère en coulisse à chaque requête. Sans monitoring, il est impossible de savoir combien de tokens il consomme, quelles opérations le sollicitent le plus, et si son activité reste dans les limites acceptables. `ArchivisteLogger` répond à ce besoin.

---

## Estimation des tokens

L'Archiviste Logger n'a pas accès au vrai compteur de tokens des APIs (qui nécessiterait un appel supplémentaire). Il utilise une approximation : 1 token ≈ 4 caractères. C'est une estimation conservatrice suffisante pour détecter les dérives de consommation.

---

## Double persistance

Chaque appel Archiviste est enregistré à deux endroits :

**En mémoire session** : liste `calls` dans l'instance, permettant des calculs agrégés instantanés.

**Sur disque en JSONL** : `data/archiviste_tokens_debug.jsonl`, en mode append. Chaque ligne est un objet JSON autonome avec l'horodatage, la source de l'appel, les tokens estimés et les métadonnées. Ce format permet l'analyse post-session avec des outils externes.

---

## Sources tracées

Chaque appel est étiqueté avec sa source :

| Source | Opération |
|---|---|
| `semantic_analysis` | Analyse des intentions utilisateur |
| `memory_synthesis` | Synthèse du contexte mémoriel |
| `memory_enrichment` | Enrichissement d'un souvenir lors de l'ajout |
| `ego_analysis` | Analyse des traits d'identité |
| `introspection` | Sessions du Cognitive Mirror |

---

## Rapport de session

`get_summary()` agrège les statistiques par source : nombre d'appels, tokens en entrée, tokens en sortie, ratio input/output. Les 5 sources les plus consommatrices sont isolées pour identifier rapidement les points chauds.

`save_report()` sauvegarde ce rapport dans `data/archiviste_monitoring.json`.
