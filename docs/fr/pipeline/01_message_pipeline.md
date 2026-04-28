# Pipeline d'un message utilisateur

**Sources vérifiées** : `logic_callbacks.py` (fonctions `chat_fn`, `get_parallel_context`), `ogma_ng.py` (gestion des phrases magiques, streaming)

---

## Vue d'ensemble

Quand l'utilisateur envoie un message, OGMA ne se contente pas de le transmettre à l'IA. Plusieurs étapes se déroulent avant que la réponse commence à s'afficher, et plusieurs autres après.

```
Message utilisateur
    │
    ├── Enrichissement du message (images, fichiers attachés)
    ├── Recherche contexte mémoire (parallèle)
    ├── Construction du prompt système complet
    ├── Appel IA principale (streaming)
    ├── Affichage progressif de la réponse
    └── Traitement post-réponse (phrases magiques, ego, mémoire)
```

---

## Étape 1 — Enrichissement du message

Avant tout traitement IA, le message peut être enrichi avec du contenu multimodal :

- Si un fichier image est attaché, son contenu base64 est ajouté au message.
- Si un fichier texte/document est attaché, son contenu est inséré dans le message utilisateur.
- Si l'agent de perception (webcam) est actif, une capture est automatiquement ajoutée.

Le texte brut du message reste inchangé pour l'affichage dans l'interface. Seule la version envoyée à l'IA contient les données enrichies.

---

## Étape 2 — Recherche de contexte en parallèle

`get_parallel_context()` lance simultanément plusieurs recherches :

- **Souvenirs personnels** : recherche dans le `MemoryManager` les souvenirs les plus pertinents par rapport au message (pipeline hybride FAISS + FTS5, synthèse Archiviste)
- **Conversations passées** : recherche dans les conversations précédentes
- **Contexte visuel** : récupération des événements de la file de perception si disponible

Ces recherches s'exécutent en parallèle (`asyncio.gather`) avec un timeout de sécurité (10 secondes par défaut). Si une recherche échoue, les autres continuent et la défaillante retourne une chaîne vide.

Si l'`ArchivisteMemoryOptimizer` est disponible, il est utilisé à la place de la recherche directe : l'Archiviste analyse d'abord la requête pour en extraire les concepts clés, ce qui améliore la précision des résultats.

---

## Étape 3 — Construction du prompt système

Le prompt système est assemblé dans cet ordre :

| Composant | Source |
|---|---|
| Contenu ego compilé | `data/ego_compiled.json` |
| Instructions principales | `settings.json` → `prompts.instructions` |
| Contexte persistant | `data/persistent_context.txt` |
| Contexte visuel | File d'événements de perception |
| Instructions perception | `settings.json` → `prompts.perception` (si webcam active) |

Le contexte mémoire (souvenirs) n'est **pas** injecté dans le prompt système ici. Il a été injecté directement dans l'historique de conversation à l'étape précédente pour éviter la redondance.

L'historique de conversation est tronqué pour rester dans les 75% de la fenêtre de contexte du modèle. Les messages trop anciens sont supprimés en commençant par les plus vieux. Les phrases magiques d'introspection présentes dans l'historique sont occultées pour éviter des déclenchements accidentels.

---

## Étape 4 — Appel IA et streaming

L'IA principale est appelée via `call_chat_api_streaming()`. Chaque token généré est transmis à une fonction callback qui met à jour le widget de message dans l'interface en temps réel. Un spinner JavaScript est injecté dans le DOM pendant la génération pour indiquer l'activité.

---

## Étape 5 — Traitement post-réponse

Une fois la réponse complète, elle est analysée à la recherche de **phrases magiques** :

| Phrase détectée | Action déclenchée |
|---|---|
| `"il faut que je me souvienne de ça : [contenu]"` | Appel `memory_manager.add_memory()` en tâche de fond |
| `"ceci est une part de moi maintenant : [contenu]"` | Appel `memory_manager.store_ego_trait()` |
| `"il faut que je réfléchisse sur : [thème]"` | Déclenchement du Cognitive Mirror |
| `"il faut que je te vois"` | Activation de la webcam |
| `"il faut que je cherche sur internet [sujet]"` | Déclenchement Web Navigator |
| `"je dois créer une image de : [description]"` | Génération d'image via text2img |

Ces traitements sont non-bloquants : ils sont lancés en tâches asynchrones en arrière-plan et ne retardent pas l'affichage de la réponse.
