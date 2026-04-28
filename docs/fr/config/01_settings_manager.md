# Gestionnaire de configuration — `SettingsManager`

**Sources vérifiées** : `core_logic.py` (classe `SettingsManager`), `data/settings.example.json`

---

## Rôle

`SettingsManager` est le point d'accès unique à la configuration d'OGMA. Il charge `data/settings.json` au démarrage et expose un dictionnaire `settings` que tous les composants peuvent lire. Les sauvegardes passent obligatoirement par lui — jamais par écriture directe dans le fichier.

---

## Chargement

Au chargement, le manager part des valeurs par défaut (`_default_settings`) et les fusionne avec le contenu du fichier JSON. Cette fusion est récursive : les clés présentes dans le fichier écrasent les défauts, mais les clés absentes du fichier conservent leur valeur par défaut. Cela signifie qu'un `settings.json` partiel (par exemple après une mise à jour qui ajoute de nouvelles options) reste valide sans intervention manuelle.

Si le fichier est absent, les défauts sont utilisés et le flag `_load_failed` est positionné à `True`. Si le fichier existe mais contient du JSON invalide, la sauvegarde est **bloquée** pour protéger les données existantes — mieux vaut ne rien écraser que d'écraser avec des données corrompues.

---

## Protection à la sauvegarde

Deux gardes protègent `save_settings()` :

1. **Flag `_load_failed`** : si le chargement a échoué, toute tentative de sauvegarde est refusée avec un message explicite.
2. **Détection de valeurs par défaut vides** : si les settings ressemblent à un profil vierge (provider = "Aucun", pas de vault, instructions courtes), la sauvegarde est également refusée. Cela évite d'écraser une vraie configuration avec un état non initialisé.

---

## Backups automatiques

Avant chaque sauvegarde réussie, le fichier actuel est copié dans `data/backups/` avec un horodatage. Seuls les quatre derniers backups sont conservés, les plus anciens sont supprimés automatiquement.

---

## Structure de `settings.json`

Les sections principales du fichier de configuration :

| Section | Contenu |
|---|---|
| `chat_api` | Configuration du contrôleur IA principal (provider, clé, modèle, backend) |
| `reasoning_api` | Configuration de l'Archiviste |
| `embedding_api` | Configuration des embeddings |
| `image_generation` | Génération d'images (activé, dimensions, provider) |
| `audio` | Préférences audio et STT/TTS |
| `voice` | Activation et configuration de la reconnaissance vocale |
| `dream_engine` | Paramètres du Dream Engine (activé, timeout inactivité) |
| `other_backends` | Paramètres spécifiques Ollama (low_vram, timeout) |
| `prompts` | Prompts système principaux (instructions, mémorisation, injection) |
| `perception_agent` | Configuration webcam et modèle de perception |
| `api_keys_vault` | Coffre-fort des clés API (chiffré ou stocké selon config) |

Le fichier `data/settings.example.json` sert de modèle documenté pour un nouveau déploiement.
