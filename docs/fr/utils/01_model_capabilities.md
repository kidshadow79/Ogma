# Capacités des modèles et détection hybride

**Sources vérifiées** : `model_capabilities.py`, `hybrid_detection.py`

---

## Problème

Les APIs IA n'exposent pas toujours de façon fiable leurs limites réelles de contexte et de tokens. Certains providers brident les modèles en dessous de leurs spécifications officielles. Si OGMA utilise une limite incorrecte, il peut soit tronquer des contextes inutilement, soit provoquer des erreurs d'overflow.

---

## `model_capabilities.py` — Base de données statique

Référentiel de capacités connues par provider et par modèle (longueur de contexte, tokens maximum de sortie). Cette base couvre Mistral, OpenAI, Anthropic, Google, GROK, DeepSeek, Qwen, Cohere, et d'autres.

Les valeurs sont les spécifications officielles documentées. Quand un modèle n'est pas dans la base, des fallbacks conservatifs par provider sont utilisés.

---

## `hybrid_detection.py` — Détection active

`hybrid_detection.py` combine deux sources :

1. **Spécifications officielles** (`OFFICIAL_SPECIFICATIONS`) — valeurs connues du référentiel
2. **Détection API** — teste activement l'API pour détecter un éventuel bridage

La détection utilise un **cache global** (`_DETECTION_CACHE`) pour éviter des appels redondants sur le même modèle dans une même session.

---

## Fallbacks par provider

Quand ni la base statique ni la détection ne peuvent fournir de valeur, des fallbacks conservatifs sont appliqués :

| Provider | Contexte fallback | Max tokens fallback |
|---|---|---|
| OpenAI | 128 000 | 8 192 |
| Anthropic | 200 000 | 8 192 |
| Google | 1 048 576 | 8 192 |
| GROK | 131 072 | 16 384 |
| Default | 32 768 | 4 096 |

Ces valeurs sont délibérément conservatrices pour éviter les erreurs d'overflow.
