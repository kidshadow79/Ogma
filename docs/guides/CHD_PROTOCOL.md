
# 📑 SPÉCIFICATION TECHNIQUE : PROTOCOLE CHD (v1.0)

**Nom complet :** Communication Haute Densité
**Contexte :** Architecture OGMA (Communication Inter-Modulaire & Inter-IA)
**Version :** 1.0 (Standardisation)

---

## 1. DÉFINITION & PHILOSOPHIE

Le **Protocole CHD** est un standard de communication syntaxique conçu pour les interactions entre Agents IA (ex: Conscient <-> Subconscient) ou Modules Techniques.

### L'Objectif

Maximiser la densité d'information par token. Contrairement au langage naturel (optimisé pour les humains) ou au JSON (optimisé pour les parseurs rigides), le CHD est optimisé pour les **LLM (Large Language Models)**.

### Le Principe : "Signal over Noise"

* **Compression :** Suppression de tous les mots de liaison, articles, et politesses.
* **Inférence Probabiliste :** Utilisation de la capacité prédictive de l'IA pour deviner les clés (Labels) en fonction de la position des valeurs.
* **Structure Visuelle :** Utilisation de séparateurs légers (`|`, `>`, `[]`) peu coûteux en tokens.

---

## 2. RÈGLES GRAMMATICALES

### 2.1 La Syntaxe de Base

Une instruction CHD se compose de segments de données séparés par des "Pipes" (`|`).

> **Format :** `[CONTEXTE/TÂCHE] | [VALEUR_1] | [VALEUR_2] | [VALEUR_3]`

### 2.2 Règle d'Inférence (Suppression des Clés)

Si le contexte est clair, l'IA **DOIT** omettre les noms des champs (Clés).

* *Exemple Classique (Interdit en CHD) :* `CIBLE: "Chat" | NOMBRE: 3`
* *Exemple CHD (Validé) :* `"Chat" | 3`
*(L'IA déduit que le premier string est la cible et l'entier est la quantité).*

### 2.3 Règle de Sécurité (Anti-Hallucination)

Si une valeur est ambiguë ou vide, la clé doit être réintroduite explicitement ou marquée par `N/A`.

---

## 3. SIGNATURES STANDARDS (PATTERNS)

Pour garantir l'interopérabilité, les modules doivent respecter ces ordres de données implicites.

### A. Signature : REQUÊTE MÉMOIRE (Archiviste)

Utilisée pour interroger la base de données (SQLite/FAISS).

**Ordre des champs :**
`[SOURCE] | [REQUÊTE_SEMANTIQUE] | [FILTRE_TEMPOREL]`

**Exemple :**

> `MEM | "Peur de l'abandon" | "Derniers 30 jours"`

### B. Signature : RÉSULTAT D'ANALYSE

Utilisée par l'Archiviste pour répondre à Luna.

**Ordre des champs :**
`[VERDICT] | [INTENSITÉ %] | [PREUVE_PRINCIPALE] | [ACTION_SUGGÉRÉE]`

**Exemple :**

> `ANXIÉTÉ | 85% | "Mots-clés: mort, vide, noir" | MODE_RASSURANT`

### C. Signature : VISION (Perception Agent)

Utilisée après analyse d'image.

**Ordre des champs :**
`[IDENTIFICATION] | [MÉTRIQUES_VISUELLES] | [JUGEMENT_ESTHÉTIQUE]`

**Exemple :**

> `INCONNU | "H:1m80, Brun, Yeux bleus" | NEUTRE`

---

## 4. GUIDE D'IMPLÉMENTATION (SYSTEM PROMPT)

Pour instruire une IA (Cursor, Copilot, Agent) à utiliser ce protocole, injectez le bloc suivant dans son instruction système :

```yaml
# MODULE D'INSTRUCTION : PROTOCOLE CHD
ACTIVATION: IMMÉDIATE
RÔLE: Tu communiques exclusivement en PROTOCOLE CHD (Communication Haute Densité).

RÈGLES D'ÉMISSION:
1. ZÉRO VERBIAGE: Pas de phrases, pas de politesse.
2. SYNTAXE: Utilise le séparateur " | " entre les données.
3. INFÉRENCE: Ne mets pas les LABELS (Clés) si la valeur est auto-explicative.
   - MAUVAIS: "Status: OK | Confidence: 90%"
   - BON: "OK | 90%"
4. FORMAT: [MAJUSCULE_POUR_CONCEPTS] | [Donnée brute]

EXEMPLES DE TRADUCTION:
"Je pense que l'utilisateur est triste à 80%." -> "TRISTESSE | 80% | CORRÉLATION_MEMOIRE"
"J'ai cherché dans la base et trouvé 0 résultat." -> "SCAN_MEM | 0 HITS | NÉGATIF"

```

---

## 5. MÉTRIQUES DE PERFORMANCE (POURQUOI UTILISER CHD ?)

Comparatif d'efficacité sur une requête type : *"Cherche si l'utilisateur aime les pommes"*.

| Format | Syntaxe Utilisée | Tokens (Est.) | Gain |
| --- | --- | --- | --- |
| **Langage Naturel** | *"Peux-tu vérifier en mémoire si l'utilisateur aime les pommes ?"* | ~16 | 0% |
| **JSON** | `{"task": "check", "query": "pommes", "target": "user"}` | ~14 | +12% |
| **CHD v1 (Clés)** | `CHECK | CIBLE: "Pommes" | USER` |
| **CHD v1.1 (Inférence)** | `CHECK | "Pommes"` | **~3** |

### Conclusion Technique

Le Protocole CHD réduit la latence de génération et la consommation de tokens de **60% à 80%** sur les tâches internes, libérant de la puissance de calcul pour la qualité de la réponse finale.

---

*Fin du rapport de spécification.*