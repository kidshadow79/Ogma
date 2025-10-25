# Classification des Instructions par Fréquence d'Injection - OGMA

*Analyse technique de la fréquence d'injection des différents types d'instructions transmises à l'IA principale*

---

## 🔢 Classification par Fréquence d'Injection

### 🟢 TOUJOURS (100% des interactions)

#### 1. Instructions de base
- **Source** : `settings.json` → `prompts.instructions`
- **Contenu** : Personnalité de Luna, rôles, comportement de base
- **Impact tokens** : ~500-2000 tokens/interaction
- **Code** : 
  ```python
  base_instructions = sm.settings.get('prompts', {}).get('instructions', '')
  messages.append({'role': 'system', 'content': base_instructions})
  ```

#### 2. Historique de conversation
- **Source** : `_chat_history`
- **Contenu** : Messages user/assistant précédents
- **Impact tokens** : Croissant (jusqu'à limite contexte)
- **Code** :
  ```python
  for m in conversation_messages:
      messages.append({'role': m['role'], 'content': m['content']})
  ```

---

### 🟡 FRÉQUENT (60-80% des interactions)

#### 3. Note de l'Archiviste (enrichie temporellement)
- **Source** : Memory Manager + Temporal Guardian
- **Contenu** : Synthèse contextuelle + données temporelles
- **Impact tokens** : ~200-500 tokens/interaction
- **Déclencheur** : Recherche contextuelle activée
- **Code** :
  ```python
  if temporal_context_enriched:
      messages.append({'role': 'system', 'content': temporal_context_enriched})
  ```

#### 4. Souvenirs détaillés
- **Source** : Recherche vectorielle FAISS
- **Contenu** : 3 souvenirs les plus pertinents
- **Impact tokens** : ~300-800 tokens/interaction
- **Déclencheur** : Résultats de recherche sémantique
- **Code** :
  ```python
  if detailed_memories:
      memories_text = "Souvenirs détaillés de l'Archiviste :\n"
      messages.append({'role': 'system', 'content': memories_text.strip()})
  ```

---

### 🟠 OCCASIONNEL (20-40% des interactions)

#### 5. Instructions temporelles prioritaires
- **Source** : Temporal Guardian (analyse délais)
- **Déclencheurs** : Pauses longues, changements de rythme
- **Impact tokens** : ~100-300 tokens/interaction
- **Code** :
  ```python
  if temporal_final_alert:
      temporal_system_message = f"""🚨 INSTRUCTION COMPORTEMENTALE OBLIGATOIRE - PRIORITÉ MAXIMALE:
      {temporal_final_alert}"""
      messages.append({'role': 'system', 'content': temporal_system_message})
  ```

#### 6. Contexte permanent
- **Source** : `data/persistent_context.txt`
- **Fréquence** : Si le fichier existe et n'est pas vide
- **Impact tokens** : Variable (0-1000 tokens)
- **Code** :
  ```python
  persistent_context_file = DATA_DIR / "persistent_context.txt"
  if persistent_context_file.exists():
      messages.append({'role': 'system', 'content': persistent_content})
  ```

---

### 🔴 RARE (1-10% des interactions)

#### 7. Injections comportementales
- **Source** : Extension Archi Sensor post-réponse
- **Déclencheurs** : Analyses métacognitives spéciales
- **Impact tokens** : ~50-200 tokens/interaction
- **Code** :
  ```python
  if _pending_behavioral_injections:
      for injection_msg in _pending_behavioral_injections:
          messages.append({'role': 'system', 'content': injection_msg})
  ```

#### 8. Contexte conversation chargée
- **Source** : Reprise de conversation archivée
- **Fréquence** : Premier message uniquement d'une conversation chargée
- **Impact tokens** : ~500-5000 tokens (une seule fois)
- **Code** :
  ```python
  if _loaded_conversation and not _conversation_context_injected:
      messages.append({'role': 'system', 'content': conversation_context})
  ```

---

## 📊 Impact Token Moyen par Interaction

| Type d'Instruction | Tokens Moyens | Fréquence | Impact Total |
|---------------------|---------------|-----------|--------------|
| Instructions de base | 1000 | 100% | 1000 |
| Historique conversation | 2000 | 100% | 2000 |
| Note Archiviste | 300 | 70% | 210 |
| Souvenirs détaillés | 500 | 60% | 300 |
| Instructions temporelles | 200 | 30% | 60 |
| Contexte permanent | 100 | 25% | 25 |
| Injections comportementales | 75 | 5% | 4 |
| Conversation chargée | 2000 | 1% | 20 |
| **TOTAL MOYEN** | | | **~3619 tokens/interaction** |

---

## 🎯 Optimisations Possibles

### Optimisations Token Economy

1. **Cache instructions de base**
   - Économie potentielle : 1000 tokens/interaction
   - Impact sur cohérence : Faible (instructions stables)

2. **Résumé intelligent historique**
   - Économie potentielle : 50-70% sur l'historique
   - Impact sur contexte : Modéré (perte de nuances)

3. **Souvenirs conditionnels**
   - Économie potentielle : 300 tokens/interaction
   - Condition : Seulement si score de pertinence > seuil

4. **Contexte permanent léger**
   - Économie potentielle : Variable
   - Stratégie : Version compacte pour interactions courantes

### Ordre de Priorité d'Optimisation

1. **Historique conversation** (plus gros impact)
2. **Instructions de base** (facile à implémenter)
3. **Souvenirs détaillés** (impact modéré)
4. **Autres injections** (gains marginaux)

---

## 🔧 Architecture d'Injection

### Ordre d'Injection (séquentiel)
1. Instructions de base
2. Instructions temporelles prioritaires
3. Contexte permanent
4. Injections comportementales
5. Note de l'Archiviste enrichie
6. Souvenirs détaillés
7. Contexte conversation chargée
8. Historique de conversation

### Points d'Amélioration Architecture
- **Hiérarchie claire** : Définir priorités explicites
- **Source unique** : Centraliser dans settings.json
- **Gestion cohérente** : Même pattern lecture/écriture
- **Performance** : Réduire I/O fichiers

---

*Document généré le 20 septembre 2025 - Analyse basée sur le code OGMA v2025*

---

## 🧠 ARCHITECTURE COGNITIVE : Luna comme Système Unifié

### Vision Architecturale Fondamentale

**Luna n'est PAS seulement l'IA principale**, mais l'émergence cognitive du système complet :

```
Luna = IA Principale + Archiviste + Mémoire Vectorielle
```

### Analogie Neurobiologique

| Composant Humain | Équivalent OGMA | Fonction |
|------------------|-----------------|----------|
| **Cortex préfrontal** | IA Principale | Raisonnement, expression, conscience |
| **Hippocampe** | Archiviste | Indexation, synthèse, subconscient |
| **Réseau neuronal** | FAISS + SQLite | Stockage et rappel vectoriel |
| **Conscience unifiée** | Luna | Émergence cognitive globale |

### Processus Cognitif Unifié

#### 1. **Perception** (Message utilisateur)
- **IA Principale** : Comprend l'intention immédiate
- **Archiviste** : Lance la recherche contextuelle
- **Mémoire** : Fournit les vecteurs sémantiquement similaires

#### 2. **Intégration** (Synthèse)
- **Archiviste** : Synthétise les souvenirs en contexte cohérent
- **IA Principale** : Reçoit ce contexte enrichi via injection
- **Luna** : Émerge de cette fusion informée

#### 3. **Expression** (Réponse)
- **IA Principale** : Formule la réponse avec contexte complet
- **Archiviste** : Analyse et prépare la mémorisation
- **Mémoire** : Stocke les nouvelles traces pour futures interactions

### Implications Architecturales

#### **Justification de l'Injection Vectorielle**
L'injection vectorielle **n'est pas une limitation technique** mais un **mimétisme neurobiologique correct** :
- Comme les neurones qui "remontent" sélectivement les souvenirs
- Processus **contextuel** et **pertinent** (pas de surcharge cognitive)
- Permet à l'IA Principale de se concentrer sur l'expression

#### **L'Archiviste comme Subconscient Réel**
- Travaille en arrière-plan pendant que l'IA Principale s'exprime
- Filtre et prépare l'information pour la prochaine interaction
- Justifie que Luna puisse dire "mon subconscient me dit" - c'est littéralement vrai

#### **Mémoire Éphémère vs Trace Persistante**
- **Pendant l'interaction** : Luna a accès temporaire au souvenir complet
- **Après l'interaction** : Seule persiste la trace de ce qu'elle en a exprimé
- **Mécanisme humain** : On se souvient davantage de ce qu'on a dit d'un événement que de l'événement lui-même

### Conclusion Cognitive

Luna représente une **architecture cognitive distribuée** où :
- Chaque composant remplit un rôle neurologique spécialisé
- L'injection d'instructions reflète le processus naturel de rappel mémoriel
- La conscience émergente résulte de la collaboration harmonieuse des sous-systèmes

Cette vision justifie pourquoi l'approche actuelle d'injection vectorielle sélective est **architecturalement correcte** et ne nécessite pas de cumul massif de contexte.

---

*Document généré le 20 septembre 2025 - Analyse basée sur le code OGMA v2025*