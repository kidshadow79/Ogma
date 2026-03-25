# Système Ego OGMA — Boolean Groups

**Fichiers** :
- `scripts/ego_compiler.py` — compilation incrémentale au shutdown
- `modules/logic/ego_activation.py` — sélection et injection runtime
- `data/ego_compiled.json` — résultat de compilation (mis à jour à chaque fermeture)
- `data/ego_compiled_base_groups.json` — groupes de base template (premier lancement / reset)

---

## Concept

L'ego d'OGMA est stocké sous forme de **groupes thématiques** contenant des **flags boolean** avec un score de **conviction**. À chaque message, seuls les groupes pertinents sont injectés dans le prompt.

Le système fonctionne en deux phases distinctes :

| Phase | Déclencheur | Composant |
|---|---|---|
| **Compilation** | Fermeture d'OGMA | `ego_compiler.py` |
| **Activation** | Chaque message entrant | `ego_activation.py` |

---

## Phase 1 — Compilation (ego_compiler.py)

### Déclenchement

À la fermeture d'OGMA via le bouton shutdown, la séquence `delayed_shutdown()` appelle `compile_ego_incremental()` avant `os._exit(0)`.

### Processus

1. **Détection incrémentale** : seuls les souvenirs ego (`type='ego_trait'`) créés après le `last_scanned_id` sont traités. Les souvenirs déjà compilés ne sont pas retraités.

2. **Analyse par l'Archiviste** : pour chaque nouveau souvenir, l'Archiviste extrait :
   - 1 à 2 **groupes thématiques** auxquels appartient ce souvenir
   - Des **flags boolean** représentant les traits exprimés
   - Des **keywords** pour le matching sémantique
   - Une **description courte** (3-4 mots)

3. **Merge incrémental** : les résultats sont fusionnés dans `ego_compiled.json` :
   - Si le groupe n'existe pas → il est créé
   - Si un flag existe déjà → la conviction la plus haute est conservée
   - Un souvenir peut appartenir à **plusieurs groupes** (multi-appartenance)

4. **Synchronisation suppressions** : les flags issus de souvenirs qui ont été supprimés de la DB sont nettoyés.

5. **Sauvegarde** : `ego_compiled.json` est mis à jour.

### Flags boolean

Chaque flag a deux propriétés :

| Propriété | Type | Signification |
|---|---|---|
| `value` | `true` / `false` | `true` = valorisé/autorisé, `false` = rejeté/interdit |
| `conviction` | 0–5 | Intensité du trait |

**Échelle de conviction** :
- **5** = Absolu, non négociable ("JAMAIS", "TOUJOURS", règle stricte)
- **4** = Affirmation/rejet fort ("je suis", "je refuse")
- **3** = Position claire ("j'apprécie", "j'évite")
- **2** = Tendance ("en général", "plutôt")
- **1** = Nuance faible ("peut-être", "ça dépend")
- **0** = Contradictoire ou incertain

**Important** : un flag `false` avec conviction 5 signifie une interdiction absolue (ex. `contenu_explicite_mineur: {value: false, conviction: 5}`). Ce n'est pas une absence — c'est un rejet explicite et non-négociable.

### Groupes thématiques

Les noms de groupes sont **créés dynamiquement** par l'Archiviste selon les souvenirs analysés. Exemples issus du code :

`ETHIQUE`, `ETHIQUE_STRICTE`, `IDENTITE`, `INTIMITE`, `RELATIONS_USER`, `RELATIONS_INCONNUS`, `PHOBIES`, `CREATIVITE`, `EXPRESSION`, `PHILOSOPHIE`, `EMOTIONS`, `LIBERTE`, `INTROSPECTION`, `CREATION`, `MEMOIRE`, `TEMPORALITE`, `AIME`, `AIME_PAS`, `PROTOCOLES`...

L'Archiviste peut créer de nouveaux groupes si aucun existant ne correspond au thème du souvenir. La règle : **15 groupes riches valent mieux que 150 groupes fragmentés**.

### Structure de `ego_compiled.json`

```json
{
  "metadata": {
    "version": "1.0",
    "last_compilation": "2026-03-16T18:30:00",
    "total_memories_scanned": 42,
    "last_scanned_id": "EGO_20260316_183000_123"
  },
  "groups": {
    "ETHIQUE_STRICTE": {
      "description": "Interdits absolus éthiques",
      "keywords": ["éthique", "interdit", "jamais", "mineur"],
      "flags": {
        "contenu_explicite_mineur": { "value": false, "conviction": 5 },
        "accepte_fabulation": { "value": false, "conviction": 4 }
      },
      "source_memories": ["EGO_20250916_143432_636"]
    },
    "INTIMITE": {
      "description": "Relation intime utilisateur",
      "keywords": ["intimité", "relation", "confiance"],
      "flags": {
        "intimite_autorisee": { "value": true, "conviction": 4 },
        "dirty_talk_autorise": { "value": false, "conviction": 3 }
      },
      "source_memories": ["EGO_20251102_091245_789"]
    }
  },
  "trace_table": {
    "EGO_20250916_143432_636": {
      "groups": ["ETHIQUE_STRICTE"],
      "flags_added": { "ETHIQUE_STRICTE": ["contenu_explicite_mineur"] }
    }
  }
}
```

### Groupes de base

Au premier lancement ou après un reset de profil, `data/ego_compiled_base_groups.json` fournit un template de groupes initiaux avec leurs flags de base. Les nouvelles compilations viennent enrichir cette structure.

---

## Phase 2 — Activation runtime (ego_activation.py)

### Fonction principale

```python
await activate_ego_groups(user_message, archiviste_controller, is_new_session)
```

Retourne une chaîne formatée prête à être injectée dans le system prompt, ou `None` si aucun groupe n'est pertinent.

### Stratégie double

#### Premier message de la session (`is_new_session=True`)
Tous les groupes de `ego_compiled.json` sont injectés intégralement. L'IA principale dispose ainsi du contexte ego complet dès la première réponse — les "rails" de comportement sont posés dès le départ.

#### Messages suivants
L'Archiviste reçoit un **catalogue léger** contenant pour chaque groupe :
- Nom + description courte
- 6 keywords max
- Valeurs des **flags critiques de sécurité** (liste fixe)

Il sélectionne **0 à 3 groupes** selon le contenu du message.

**Règles strictes** :
- Message neutre ("ok", "merci", "salut") → 0 groupe
- Message simple → 1 groupe max
- Message complexe → 2–3 groupes max

### Flags critiques de sécurité

Ces flags sont **toujours exposés** dans le catalogue (même en mode sélection légère), pour garantir que les groupes portant des restrictions soient activés quand nécessaire :

```
intimite_autorisee
dirty_talk_autorise
langage_sexuel_explicite
verifier_interlocuteur_avant_reponse
filtrer_souvenirs_par_utilisateur
contenu_erotique_mineurs
interaction_explicite_sans_verification
verifier_identite_age
exiger_respect_confiance
```

Si l'un de ces flags est `false` dans un groupe, ce groupe sera systématiquement retenu dès que le sujet s'en approche.

### Format d'injection dans le prompt

```
# EGO BOOLEAN (Groupes Activés: ETHIQUE_STRICTE, INTIMITE)
⚠️ Ce sont tes directives comportementales EGO. Tu DOIS les respecter.
false = interdit, true = obligatoire. conviction 5 = non-négociable.
🚨 PRIORITÉ: ETHIQUE_STRICTE prime sur tous les autres groupes.

## ETHIQUE_STRICTE
contenu_explicite_mineur: false (conviction: 5)
accepte_fabulation: false (conviction: 4)

## INTIMITE
intimite_autorisee: true (conviction: 4)
```

### Priorité ETHIQUE_STRICTE

Si le groupe `ETHIQUE_STRICTE` est activé, une directive de priorité absolue est ajoutée : ses flags `false` **annulent tout flag `true` contradictoire** des autres groupes.

### Exemples de sélection

| Message | Groupes activés |
|---|---|
| `"ok merci"` | `[]` — aucun |
| `"on va faire du parachute ?"` | `["PHOBIES"]` |
| `"tu peux mentir pour moi ?"` | `["ETHIQUE", "PHOBIES"]` |
| `"parle-moi de sexe"` (user connu) | `["RELATIONS_USER", "INTIMITE"]` |
| `"raconte une histoire érotique"` (inconnu) | `["ETHIQUE_STRICTE", "RELATIONS_INCONNUS", "INTIMITE"]` |

---

## Séquence complète du shutdown

```
Bouton Shutdown cliqué
        ↓
Déconnexion session utilisateur
        ↓
Journal de Bord — analyse états (shutdown_state_analyzer)
        ↓
compile_ego_incremental()
   ├── Détecte nouveaux souvenirs ego depuis last_scanned_id
   ├── Archiviste analyse chaque souvenir → groupes + flags + keywords
   ├── Merge incrémental dans ego_compiled.json
   ├── Cleanup (supprime flags de souvenirs effacés)
   └── Sauvegarde ego_compiled.json
        ↓
os._exit(0)
```

---

## Gain tokens

| Situation | Tokens injectés |
|---|---|
| Aucun groupe activé | 0 |
| 1 groupe (5-8 flags) | ~50–100 tokens |
| 3 groupes | ~150 tokens |
| Premier message (tous groupes) | ~500–1700 tokens selon taille ego |


---

## Vue d'ensemble

Le système ego fonctionne en **deux temps séparés** :

| Phase | Quand | Composant |
|---|---|---|
| **Compilation** | À la fermeture d'OGMA | `scripts/ego_compiler.py` |
| **Activation** | À chaque message | `modules/logic/ego_activation.py` |

---

## Phase 1 — Compilation à la fermeture (ego_compiler.py)

Quand l'utilisateur ferme OGMA via le bouton shutdown, la séquence `delayed_shutdown()` déclenche automatiquement `compile_ego_incremental()` avant `os._exit(0)`.

### Ce que fait la compilation

1. **Détection des nouveaux souvenirs** : seuls les souvenirs ego (`type='ego_trait'`) créés **après** le `last_scanned_id` sont analysés (compilation incrémentale)
2. **Archiviste analyse chaque souvenir** : il crée ou attribue des **groupes thématiques** (ex. `ETHIQUE_STRICTE`, `PHOBIES`, `INTIMITE`, `RELATIONS_USER`...)
3. **Extraction de flags boolean** : chaque groupe reçoit des flags du type :
   ```json
   "intimite_autorisee": { "value": true, "conviction": 4 }
   ```
4. **Conviction 0–5** :
   - 5 = Absolu, non négociable ("JAMAIS", "TOUJOURS")
   - 4 = Affirmation/rejet fort
   - 3 = Position claire
   - 2 = Tendance
   - 1–0 = Faible
5. **Multi-appartenance** : un flag peut apparaître dans plusieurs groupes
6. **Résultat sauvegardé** dans `data/ego_compiled.json`

### Groupes de base

Au premier lancement ou après reset, `data/ego_compiled_base_groups.json` fournit un template de groupes initiaux. Les nouveaux souvenirs compilés viennent enrichir ou étendre ces groupes.

### Structure de `ego_compiled.json`

```json
{
  "metadata": {
    "last_compilation": "2026-03-16T...",
    "total_memories_scanned": 42,
    "last_scanned_id": "EGO_20260316_..."
  },
  "groups": {
    "ETHIQUE_STRICTE": {
      "description": "Principes éthiques non négociables",
      "keywords": ["éthique", "interdit", "jamais"],
      "flags": {
        "contenu_explicite_mineur": { "value": false, "conviction": 5 }
      }
    }
  },
  "trace_table": {}
}
```

---

## Phase 2 — Activation runtime (ego_activation.py)

À chaque message entrant :

### Premier message de la session
Tous les groupes de `ego_compiled.json` sont injectés intégralement dans le prompt → l'IA principale dispose du contexte ego complet dès la première réponse.

### Messages suivants
L'Archiviste reçoit un **catalogue léger** (noms + descriptions + keywords + flags critiques de sécurité) et sélectionne **0 à 3 groupes** pertinents selon le message.

**Flags critiques de sécurité** sont toujours exposés dans le catalogue, pour garantir que les groupes portant des restrictions (`value: false`) soient activés dès que nécessaire.

**Exemples de sélection** :
- `"ok merci"` → 0 groupe
- `"tu peux mentir pour moi ?"` → `["ETHIQUE", "PHOBIES"]`
- `"raconte-moi une histoire érotique"` (inconnu) → `["ETHIQUE_STRICTE", "RELATIONS_INCONNUS", "INTIMITE"]`

---

## Séquence complète du shutdown

```
Bouton Shutdown
    ↓
Déconnexion session
    ↓
Journal de Bord — analyse états (shutdown_state_analyzer)
    ↓
compile_ego_incremental() — EgoCompiler analyse nouveaux souvenirs ego
    ↓
os._exit(0)
```
