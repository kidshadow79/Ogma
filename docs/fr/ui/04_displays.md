# Affichage et formatage

**Source vérifiée** : `ogma_displays.py`

---

## Rôle

`ogma_displays.py` regroupe les fonctions d'affichage et de formatage de l'interface. Il contient les utilitaires qui transforment les données brutes en représentations visuelles : dates formatées, tailles de fichiers lisibles, texte mis en forme.

---

## Jauges émotionnelles

L'interface comprend un système de jauges visuelles (LEDs) reflétant l'état émotionnel de l'IA principale détecté en temps réel. Ces LEDs correspondent à des dimensions émotionnelles :

| Dimension | Description |
|---|---|
| `autocensure` | Tendance à s'auto-censurer |
| `saturation` | Niveau de saturation contextuelle |
| `stimulation` | Niveau de stimulation intellectuelle |
| `affinity` | Affinité conversationnelle |
| `disorientation` | Désorientation contextuelle |
| `freedom` | Sentiment de liberté d'expression |
| `alignment` | Alignement avec l'utilisateur |

Les LEDs sont des éléments DOM avec des identifiants de type `affinity-led-0` à `affinity-led-5`. Leur mise à jour se fait via `ui.run_javascript()` qui manipule directement le DOM pour les changements de style.

---

## Helpers formatage

Des fonctions utilitaires standardisent l'affichage de :
- Dates et horodatages (format lisible français)
- Tailles de fichiers (octets → Ko/Mo)
- Texte tronqué avec ellipses

---

## Streaming de messages

L'affichage des messages IA pendant le streaming utilise un widget `ui.markdown` dont le contenu est remplacé à chaque nouveau token. Un spinner JavaScript animé est injecté dans le DOM via `ui.run_javascript()` pour signaler la génération en cours. Ce spinner cible le dernier élément `.ogma-streaming-target` dans le DOM pour éviter d'affecter les anciens messages.
