# Contexte persistant et prompts système

**Sources vérifiées** : `data/persistent_context.default.txt`, `data/instructions_defaults.json`, `data/settings.json` (section `prompts`)

---

## Deux niveaux de configuration textuelle

OGMA distingue deux types de textes qui guident le comportement de l'IA principale :

- **Le contexte persistant** : un texte court, libre, que l'utilisateur peut modifier. Il est injecté à chaque conversation comme fondation comportementale.
- **Les prompts système** : des instructions structurées, plus techniques, qui définissent comment l'Archiviste encode les souvenirs, comment l'IA principale répond, comment la mémoire est sélectionnée et injectée.

---

## Le contexte persistant — `data/persistent_context.txt`

C'est le fichier que l'utilisateur voit et peut modifier depuis l'interface. Il contient des règles comportementales fondamentales en langage naturel :

> *"Tu parles de manière naturelle, tu ne simules jamais tes réponses. Si tu ne sais pas, tu le dis. Quand on ne sait pas, on parle au conditionnel..."*

Ce texte est injecté au début de chaque session comme partie du prompt système de l'IA principale. Si le fichier `persistent_context.txt` n'existe pas au premier démarrage, `launch_ogma.py` le crée depuis le modèle `persistent_context.default.txt`.

---

## Les prompts système — `data/instructions_defaults.json`

Ce fichier contient les prompts par défaut pour chaque rôle dans le système. Ces prompts sont écrits dans un style compact appelé "Communication Haute Densité" (CHD) : instructions denses, structurées en blocs nommés, sans phrases longues. C'est volontaire — les modèles IA suivent mieux des instructions concises et explicites.

Les prompts principaux :

| Clé | Usage |
|---|---|
| `instructions` | Prompt système de l'IA principale — identité, règles absolues, liste des phrases magiques disponibles, règle éthique |
| `memorization` | Prompt de l'Archiviste pour encoder un souvenir en JSON structuré avec scoring d'impact |
| `injection` | Prompt de l'Archiviste pour sélectionner et formater le souvenir à injecter dans une conversation |
| `perception` | Prompt pour l'analyse d'images (webcam, vision) |
| `salutations` | Prompt de continuité — comment l'IA principale accueille l'utilisateur selon la durée d'absence |
| `temporal_guardian` | Guide d'adaptation comportementale selon le rythme temporel de l'utilisateur |
| `ego_memorization` | Prompt de l'Archiviste pour encoder un trait d'ego en JSON |

---

## Le scoring des souvenirs

Le prompt `memorization` définit une formule de scoring d'impact mémoriel :

$$\text{score} = \text{intensité} \times \text{base\_factor} \times (\text{liberté} + \text{création} + \text{transmission} + \text{intensité\_contextuelle})$$

L'Archiviste évalue chaque souvenir selon ces dimensions (de 0.0 à 1.0) et produit un JSON structuré. Ce score détermine ensuite la priorité du souvenir lors des injections futures.

---

## Règle de priorité

Les prompts dans `settings.json` (section `prompts`) ont la priorité sur les défauts de `instructions_defaults.json`. Si l'utilisateur a personnalisé ses instructions depuis l'interface, c'est sa version qui est utilisée. Le fichier `instructions_defaults.json` sert uniquement de filet de sécurité si `settings.json` ne contient pas ces clés.

---

## Les phrases magiques

Le prompt `instructions` liste des phrases déclencheurs que l'IA principale peut écrire dans ses réponses pour activer des fonctions du système (mémorisation, introspection, génération d'image, recherche web...). Ces phrases sont détectées par `magic_phrase_guard.py` et le système de callbacks. Elles ne sont jamais simulées — si l'IA les écrit, le système les exécute réellement.
