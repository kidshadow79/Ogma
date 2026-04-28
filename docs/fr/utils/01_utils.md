# Utilitaires de formatage et parsing

**Sources vérifiées** : `utils/formatting_utils.py`, `utils/message_parsers.py`, `utils/json_cleaner.py`, `utils/magic_phrase_normalizer.py`, `utils/backend_utils.py`

---

## Vue d'ensemble

Le dossier `utils/` contient des fonctions utilitaires extraites de `ogma_ng.py` lors du refactoring. Chaque module est centré sur une responsabilité unique.

---

## `formatting_utils.py` — Formatage lisible

`format_size(size_bytes)` convertit une taille en octets en format humain lisible ("1.5 MB", "320 KB"). Utilisé pour l'affichage des tailles de fichiers et de la mémoire dans l'interface.

---

## `message_parsers.py` — Parseurs de formats IA

Deux parseurs pour les formats spéciaux dans les réponses IA :

**`parse_thinking_format(content)`** : certaines IA retournent des structures JSON complexes avec une section `thinking` (réflexion interne) et une section `text` (réponse visible). Ce parseur extrait les deux et retourne un tuple `(thinking_content, main_text)`.

**`parse_introspection_format(content)`** : parse les balises `<introspection>...</introspection>` que l'IA principale utilise pour les dialogues d'introspection. Le contenu entre balises est extrait et affiché dans la boîte dédiée.

---

## `json_cleaner.py` — Nettoyage réponses JSON

Les réponses IA contenant du JSON incluent souvent des balises markdown (` ```json ``` `), des commentaires `//` ou des caractères de contrôle. `clean_json_response()` nettoie la réponse brute avant parsing.

---

## `magic_phrase_normalizer.py` — Normalisation multilingue

Traduit les phrases magiques anglaises en équivalents français canoniques avant toute analyse. Cela permet à l'utilisateur d'écrire en anglais ("remember that...") et que les détecteurs français continuent de fonctionner.

La transformation est non destructive : le payload de la phrase magique (le contenu après la commande) est préservé tel quel.

---

## `backend_utils.py` — Normalisation backends

`map_backend_for_controller(backend)` normalise les noms de backends en MAJUSCULES pour compatibilité avec les dictionnaires internes des `AIController`. Cette normalisation est critique — "GGUF" et "gguf" doivent être traités identiquement.
