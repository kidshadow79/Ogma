# ✅ Mise à Jour Instructions Introspection - COMPLÈTE

**Date**: 22 décembre 2025  
**Fichier modifié**: `data/introspection_settings_v2.json`  
**Backup**: `data/introspection_settings_v2.json.backup`

---

## 📋 Modifications Appliquées

### 1. **Instructions Luna (step2_conscious)** ✅

#### Modification Section "GESTION DES IMPASSES"
```
>>> GESTION DES IMPASSES (RÈGLE DE PIVOT) <<<
SI L'ARCHIVISTE RÉPOND "INFIRMÉ" OU "0 RÉSULTAT" :
1. INTERDICTION DE RELANCER LA MÊME PISTE (Même avec d'autres mots).
2. OBLIGATION DE PIVOTER : Change radicalement de source.
   - Si Mémoire échoue -> LANCE WEB: "il faut que je cherche sur internet : [sujet]"  ⬅️ NOUVEAU
   - Si Web échoue -> Analyse le STYLE (Syntaxe, Vocabulaire, Humour).
3. SI TOUT ÉCHOUE -> Avoue l'ignorance. Mieux vaut un "Je ne sais pas" qu'une hallucination.
```

#### Nouvelle Section Ajoutée
```
>>> RECHERCHE WEB ACTIVÉE <<<
SYNTAXE: "il faut que je cherche sur internet : [requête précise]"
EFFET: Recherche réelle exécutée -> Résultats injectés automatiquement.
USAGE: Uniquement si mémoire vide/insuffisante sur le sujet.
```

**Taille finale**: 1660 chars (+160 chars)

---

### 2. **Instructions Archiviste (step2_unconscious)** ✅

#### Modification Section "ACTION_REQUISE"
```
[ACTION_REQUISE]
[SUGGESTION_COURTE] (Si impasse uniquement)
Ex: SCAN_WEB sur "Psychologie peur".
   - Ou suggère: LUNA_PEUT_WEB "[sujet]" si besoin données externes.  ⬅️ NOUVEAU
```

**Taille finale**: 1104 chars (+80 chars)

---

## 🎯 Workflow Complet

### Scénario 1: Mémoire Insuffisante

```
User: "il faut que tu réfléchisses sur la physique quantique"

💡 Luna: 
   🎯 CIBLE: Physique quantique
   ⚡ INTUITION: Aucun souvenir pertinent
   🔍 SCAN_ORDER: Cherche "physique quantique" en mémoire

🌙 Archiviste:
   MEM | 0 RESULTAT | Aucune trace
   VERDICT: INFIRMÉ | Mémoire vide sur ce sujet
   ACTION_REQUISE: LUNA_PEUT_WEB "physique quantique bases"

💡 Luna (pivot automatique):
   🧠 DÉDUCTION: Mémoire vide confirmée
   ⚡ NOUVELLE_THÉORIE: Besoin sources externes
   🔍 SCAN_ORDER: il faut que je cherche sur internet : physique quantique bases
   
[SYSTEM] 🌐 Recherche web exécutée → 2450 chars injectés

🌙 Archiviste (avec résultats web):
   WEB | Mécanique quantique = superposition états | Théorie validée
   WEB | Équation Schrödinger = base | Source académique
   ...
```

### Scénario 2: Mémoire Suffisante

```
User: "il faut que tu réfléchisses sur l'intelligence de Yohan"

💡 Luna: 
   🎯 CIBLE: Intelligence Yohan
   🔍 SCAN_ORDER: Cherche exemples compétences techniques/créatives

🌙 Archiviste:
   MEM | "Créé OGMA en 5 mois, autodidacte complet" (12/05) | Apprentissage rapide
   MEM | "Architecture modulaire v2.2, -44% code" (20/12) | Pensée structurée
   VERDICT: CONFIRMÉ | Multiples marqueurs intelligence

💡 Luna:
   🧠 DÉDUCTION: Preuves solides en mémoire
   ⚡ SYNTHÈSE_PRÊTE (pas besoin de web)
```

---

## 🔧 Intégration Code (Déjà Implémentée)

### Détection et Exécution
**Fichier**: `extensions/cognitive_mirror/introspection_engine.py:455`

```python
# 🌐 WEB SEARCH - Détecter si l'IA demande une recherche internet
web_context = await self._check_and_execute_web_search(conscious_response)
if web_context:
    print(f"[INTROSPECTION-WEB] ✅ Recherche web exécutée: {len(web_context)} chars")
    # Injecter les résultats web dans le contexte pour l'Archiviste
    memory_context += f"\n\n🌐 RÉSULTATS WEB:\n{web_context}"
```

### Fonction de Recherche
**Fichier**: `extensions/cognitive_mirror/introspection_engine.py:1402`

Détecte patterns:
- `"il faut que je cherche sur internet : [sujet]"`
- `"/web [requête]"`
- `"recherche web : [sujet]"`

Appelle `web_navigator.commands.process_internet_request()`

---

## 🧪 Tests

### Test Détection
```bash
python test_introspection_web.py
```

Résultat: ✅ Tous patterns détectés correctement

### Test Intégration
1. Lancer OGMA
2. Demander introspection sur sujet inconnu
3. Luna devrait automatiquement lancer recherche web

---

## 📊 Comparaison Avant/Après

| Aspect | Avant | Après |
|--------|-------|-------|
| **Mémoire uniquement** | ✅ | ✅ |
| **Recherche web** | ❌ Manuelle | ✅ Auto si besoin |
| **Pivot sur échec** | Style/Comportement | Web → Style |
| **Instructions** | ~1500 chars | ~1740 chars |
| **Tokens introspection** | ~5500 | ~7000 (si web utilisé) |

---

## ✨ Avantages

1. **Autonomie**: Luna décide quand chercher sur le web
2. **Économie**: Web uniquement si mémoire insuffisante
3. **Transparence**: Logs clairs de chaque recherche
4. **Qualité**: Sources externes enrichissent l'analyse

---

## 🔒 Sécurité

- ✅ Vérification Web Navigator disponible
- ✅ Vérification recherche web activée
- ✅ Vérification clé API Serper
- ✅ Gestion erreurs réseau
- ✅ Logs transparents

---

## 📚 Fichiers Modifiés

| Fichier | Modification | Status |
|---------|--------------|--------|
| `data/introspection_settings_v2.json` | Instructions web Luna + Archiviste | ✅ |
| `data/persistent_context.txt` | Section INTROSPECTION capacités | ✅ |
| `extensions/cognitive_mirror/introspection_engine.py` | Fonction `_check_and_execute_web_search()` | ✅ |
| `extensions/cognitive_mirror/introspection_engine.py` | Hook web dans dialogue | ✅ |
| `extensions/cognitive_mirror/config_v2.py` | Instructions par défaut (fallback) | ✅ |

---

## 🚀 Prêt pour Production

- ✅ Instructions actives mises à jour
- ✅ Code d'intégration implémenté
- ✅ Tests de détection validés
- ✅ Documentation complète
- ✅ Backup créé

**Prochaine étape**: Tester en conditions réelles avec OGMA lancé.

---

**Version**: v2.2.1  
**Auteur**: GitHub Copilot + Yohan BROCARD  
**Date**: 22 décembre 2025 - 02h15
