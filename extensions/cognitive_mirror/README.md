# 🧠 Extension Cognitive Mirror

> **Extension d'introspection transparente pour OGMA — v4**
> *Joute visible IA Principale ↔ Archiviste déclenchée à la demande*

---

## 🎯 Principe de Fonctionnement

L'extension déclenche une **joute interne visible** entre les deux cerveaux d'OGMA :

- **IA Principale** — formule sa position initiale, défend ou révise sous la pression de l'Archiviste
- **Archiviste** — miroir exigeant : confronte, pointe les contradictions d'identité (ego), protège la cohérence historique. Il n'est pas une base de données — il challenge.

Ce dialogue se déroule en **3 phases** :

1. **Ouverture** — L'IA Principale formule le sujet et sa position initiale, avec les souvenirs FAISS pertinents injectés
2. **Joute** — Échanges IA Principale ↔ Archiviste (min/max configurables). La recherche mémoire se refait à chaque tour en fonction de l'évolution du dialogue.
3. **Synthèse** — L'IA Principale tire les vraies conclusions de la confrontation et rédige la réponse finale

La sauvegarde en mémoire est **décidée par l'IA elle-même** selon un seuil d'importance qu'elle évalue.

---

## ⚡ Modes de Déclenchement

| Mode | Comportement |
|---|---|
| ``on_demand`` | Déclenché par phrases magiques dans le message utilisateur |
| ``always`` | Analyse systématique de chaque message |

**Phrases magiques par défaut** : ``réfléchis``, ``introspection``, ``lance une introspection``, et autres.

> **Note technique** : le déclenchement utilisateur réel passe par des regex hardcodées dans ``ogma_ng.py``. Le déclenchement auto-IA passe par ``ogma_ui_conversations.py``. La méthode ``check_magic_phrases()`` de ``introspection_core.py`` consulte la config mais n'est pas le chemin actif.

---

## 🏗️ Architecture des Fichiers

```
extensions/cognitive_mirror/
├── __init__.py                    # API publique, singleton, aliases rétrocompatibilité
├── config_v2.py                   # Source de vérité — IntrospectionConfigV2
├── introspection_core.py          # Moteur principal — IntrospectionCore
├── introspection_orchestrator.py  # Orchestrateur joute IA Principale ↔ Archiviste
├── memory_integration.py          # Sauvegarde souvenirs "REF"
├── ui_components.py               # Interface principale (popup paramètres)
├── ui_parameters_v2.py            # Popup paramètres v4
├── ui_introspection_display.py    # Composants visuels (barre progression, dialogue coloré)
└── _archive/                      # Documentation historique des versions précédentes
```

### Rôle de chaque fichier

**``introspection_core.py``** — Moteur principal. Reçoit un message, décide si l'introspection est nécessaire, délègue à l'orchestrateur, retourne la réponse enrichie.

**``introspection_orchestrator.py``** — Gère la joute séquentielle avec callback temps réel. Construit les prompts par étape avec identité complète (ego + contexte permanent), injecte les souvenirs FAISS pertinents à chaque tour, extrait les métadonnées (décision de sauvegarde, importance).

**``config_v2.py``** — Toute la configuration : instructions par étape, limites tokens, phrases magiques, paramètres de mémoire. Persistance JSON dans ``data/introspection_settings_v2.json``.

**``memory_integration.py``** — Sauvegarde les réflexions importantes comme souvenirs préfixés ``[REF]`` dans la mémoire OGMA.

**``ui_introspection_display.py``** — Composants visuels NiceGUI : barre de progression, affichage dialogue coloré.

---

## 🔌 API Publique

```python
from extensions.cognitive_mirror import (
    initialize_introspection,    # Initialise l'extension
    get_introspection,           # Retourne l'instance IntrospectionCore
    is_available,                # Vérifie si initialisé
    is_v21,                      # Vérifie si version v4 active (toujours True)
    is_enabled,                  # Vérifie si activé (config)
    toggle_enabled,              # Bascule ON/OFF
    check_magic_phrases,         # Détection phrases magiques (source="user"|"ia")
    stop_current_introspection,  # Arrêt de la session en cours
    get_introspection_config,    # Accès direct à la config
)
```

### Initialisation (via ogma_ng.py)

```python
success = initialize_introspection(
    chat_controller=chat_ctrl,
    archiviste_controller=archiviste_ctrl,
    memory_manager=memory_mgr,
    settings_manager=settings_mgr  # Optionnel — pour injection ego/instructions système
)
```

### Point d'entrée session

```python
core = get_introspection()
result = await core.run_introspection(
    user_message=text,
    context=conversation_context   # dict: chat_history, user_identity, main_ai_identity, ...
)
# result["success"], result["final_response"], result["synthesis"], result["dialogue_messages"]
```

### Aliases de rétrocompatibilité

``initialize_cognitive_mirror()`` et ``get_cognitive_mirror()`` redirigent automatiquement vers l'API v4.

---

## ⚙️ Configuration

Fichier de configuration : ``data/introspection_settings_v2.json``

| Paramètre | Défaut | Description |
|---|---|---|
| ``extension_enabled`` | ``false`` | Activation/désactivation |
| ``introspection_mode`` | ``on_demand`` | ``on_demand`` ou ``always`` |
| ``min_dialogue_exchanges`` | ``4`` | Minimum d'allers-retours avant synthèse autorisée |
| ``max_dialogue_exchanges`` | ``8`` | Maximum d'échanges dans la joute |
| ``max_introspection_duration`` | ``300`` | Timeout global (secondes) |
| ``step1_max_tokens`` | ``600`` | Tokens étape Ouverture |
| ``step2_conscious_max_tokens`` | ``800`` | Tokens tours IA Principale |
| ``step2_unconscious_max_tokens`` | ``900`` | Tokens tours Archiviste |
| ``step3_max_tokens`` | ``3500`` | Tokens Synthèse finale |
| ``auto_save_enabled`` | ``false`` | Sauvegarde auto souvenirs |
| ``importance_threshold`` | ``6`` | Seuil importance pour sauvegarde (1-10) |
| ``memory_search_threshold`` | ``0.5`` | Seuil similarité FAISS (recherche mémoire) |

> **Note tokens** : la limite API réelle est `max_tokens × 2` (filet anti-troncature). Pour la synthèse, le multiplicateur est `× 5`.

Les **instructions de chaque étape** sont éditables directement via l'interface (onglet "Instructions").

---

## 🎨 Interface Utilisateur

Accessible via le bouton 🧠 dans le header d'OGMA.

Le popup contient 3 onglets :
- **Général** — switch ON/OFF, mode de déclenchement, phrases magiques actives
- **Instructions** — édition directe des prompts des 4 étapes (Ouverture, IA Principale, Archiviste, Synthèse) avec tokens configurables et bouton "Restaurer défaut"
- **Avancé** — échanges min/max, timeout, seuil similarité mémoire, sauvegarde automatique, affichage

---

## 🧠 Philosophie v4 : La Joute

L'architecture v4 abandonne le modèle Conscient/Inconscient pour une joute plus directe :

- L'**IA Principale** est honnête — elle ne fabrique pas de souvenirs. Si elle n'en a pas, elle le dit.
- L'**Archiviste** confronte et challenge — il n'est pas là pour valider ni pour servir de base de données.
- Les souvenirs FAISS sont injectés **automatiquement** à chaque tour selon le fil du dialogue — pas de paramètre à régler.
- Le dialogue est **visible** — l'utilisateur peut lire toute la joute dans la boîte de réflexion.
- La sauvegarde est **optionnelle et décidée par l'IA** — jamais automatique sauf si l'option est activée.
- L'ego complet (406 flags) est injecté dans le **système prompt de l'Archiviste** pour détecter les contradictions d'identité.

---

## 🔧 Intégration OGMA

L'extension est initialisée dans ``ogma_ng.py`` via ``_ensure_cognitive_mirror()``.
Le déclenchement utilisateur est détecté par regex dans ``ogma_ng.py`` (avant appel API principal).
Le déclenchement auto-IA est géré dans ``ogma_ui_conversations.py`` (après affichage réponse IA).
Le bouton header est géré dans ``ogma_headers.py``.
