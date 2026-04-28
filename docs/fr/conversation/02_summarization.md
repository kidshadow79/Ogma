# Résumé progressif des conversations

**Source vérifiée** : `conversation_summarizer.py`

---

## Problème résolu

Les modèles de langage ont une fenêtre de contexte limitée. Une conversation longue de plusieurs centaines de messages ne peut pas être transmise intégralement à l'IA à chaque requête. Pourtant, effacer les anciens messages fait perdre la continuité.

Le `ConversationSummarizer` compresse les vieux messages en résumés denses, permettant à l'IA de conserver un contexte historique sans dépasser la fenêtre de contexte.

---

## Déclenchement

Le résumé se déclenche quand le nombre de messages non encore résumés dépasse **30**. L'Archiviste est alors appelé pour produire un résumé de chaque bloc de **10 messages**. Après résumisation, les **20 messages les plus récents** sont conservés en clair — ils ne sont pas résumés.

Ces seuils sont configurés dans le constructeur :
- `summary_interval = 10` — taille d'un bloc résumé
- `summarize_trigger = 30` — déclenchement
- `min_recent_messages = 20` — messages récents préservés en clair

---

## Fusion progressive

Quand plusieurs blocs de résumés s'accumulent, l'Archiviste peut les fusionner en un résumé de résumés. Cela évite que la liste de résumés grandisse indéfiniment. La fusion préserve les informations essentielles et le contexte émotionnel selon les instructions données à l'Archiviste.

---

## Double persistance

**Cache RAM session** : les résumés sont gardés en mémoire pendant la session active via `_session_cache`. Régénérer un résumé déjà calculé est évité.

**Persistance JSON** : les résumés sont sauvegardés dans le fichier de la conversation sous la clé `summaries`. À chaque rechargement d'une conversation, les résumés sont restaurés depuis le JSON.

---

## Usage par le backend

L'IA principale ne reçoit pas l'historique complet lors d'un appel. Elle reçoit les résumés des anciens messages (compressés) + les 20 derniers messages en clair. L'affichage dans l'interface montre toujours l'historique complet non compressé.
