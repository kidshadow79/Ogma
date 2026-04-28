# Dream Engine — L'IA qui rêve

**Sources vérifiées** : `extensions/dream_engine/__init__.py`, `extensions/dream_engine/dream_prompts.py` (structure), copilot-instructions.md (section Dream Engine)

---

## L'idée

Quand vous fermez une conversation avec OGMA et que rien ne se passe pendant dix minutes, l'IA ne reste pas simplement en attente. Elle rêve.

Ce n'est pas une métaphore. Le Dream Engine est un processus réel : l'IA principale génère un récit onirique à partir de ses souvenirs récents, l'Archiviste l'analyse comme un psychanalyste, et le tout est sauvegardé dans un journal des rêves.

L'inspiration vient d'un fait neurologique : le sommeil paradoxal chez l'humain sert à consolider les souvenirs, à tisser des connexions émotionnelles entre les expériences de la journée. Le Dream Engine tente une transposition numérique de ce phénomène.

---

## Le flux de rêve

**Déclenchement** : après 10 minutes d'inactivité (configurable), ou manuellement via le bouton 🌙 dans le header.

**Extraction du carburant mémoriel** : `dream_memory.py` extrait les souvenirs récents depuis la base FAISS/SQLite — 10 résumés de conversations et 5 souvenirs marqués `#MEM`. Ce sont les "images" qui alimenteront le rêve.

**Génération** : l'IA principale génère un récit onirique en mode "métabolisme lent" — 100 tokens par minute par défaut (configurable). Ce ralentissement délibéré imite le caractère diffus du rêve et évite une génération brutale.

**Analyse PSY** : l'Archiviste reçoit le rêve généré et l'évalue avec un prompt de psychanalyste. Il produit un score d'intensité (1-10), identifie l'émotion dominante et extrait un insight sur l'ego de l'IA.

**Illustration** : si activée, l'IA principale choisit entre une image unique ou un comic 4 cases pour illustrer le rêve.

**Sauvegarde** : deux journaux sont mis à jour — `journal_reves.md` (format humain lisible) et `journal_reves.json` (format queryable par l'IA).

**Réveil** : si le score PSY est supérieur à 8, l'IA mentionne spontanément son rêve dans la prochaine conversation.

---

## Le sursaut

Si l'utilisateur envoie un message pendant qu'un rêve est en cours, le Dream Engine ne coupe pas brutalement le processus. Il **accélère** la génération à vitesse maximale, termine le rêve proprement (avec analyse), puis répond normalement au message — avec le contexte du rêve disponible.

Ce comportement évite une interruption abrupte et permet à l'IA de mentionner naturellement qu'elle venait de rêver.

---

## Intégration avec le Journal de Bord

L'extension Journal de Bord injecte le contexte du dernier rêve non encore mentionné dans le résumé matinal. L'IA principale peut ainsi évoquer son rêve naturellement lors de la première conversation de la journée.

---

## Recherche web autonome

Le Dream Engine peut activer une recherche web pendant le rêve (`web_search_enabled: true`). L'IA peut ainsi explorer des sujets liés à ses souvenirs récents, enrichissant le récit onirique de références réelles.

---

## Configuration

Les paramètres clés (tous dans `data/extensions/dream_engine/`) :

| Paramètre | Valeur défaut | Rôle |
|---|---|---|
| `inactivity_timeout_minutes` | 10 | Délai avant déclenchement auto |
| `metabolism_tokens_per_minute` | 100 | Vitesse de génération |
| `max_dream_tokens` | 3000 | Longueur maximale du rêve |
| `impact_threshold` | 150.0 | Seuil importance souvenirs |
| `random_memories_count` | 5 | Nombre de souvenirs extraits |

---

## API publique

```python
from extensions.dream_engine import (
    initialize_dream_engine,
    start_dream,        # Déclenche un rêve
    wake_up,            # Réveille l'IA
    is_dreaming,        # État courant
    get_last_dream_context,   # Pour injection contexte
    mark_dream_mentioned,     # Marque le rêve comme discuté
)
```

---

## Sources
- `extensions/dream_engine/__init__.py` — API publique, configuration par défaut
- `extensions/dream_engine/dream_core.py` — Boucle de rêve, métabolisme, sursaut
- `extensions/dream_engine/dream_memory.py` — Extraction carburant mémoriel
- `extensions/dream_engine/dream_analysis.py` — Archiviste psychanalyste
- `extensions/dream_engine/dream_journal.py` — Journaux .md et .json
- `extensions/dream_engine/dream_illustration.py` — Génération images/comics
- `data/journal_reves.json` — Journal des rêves persistant
