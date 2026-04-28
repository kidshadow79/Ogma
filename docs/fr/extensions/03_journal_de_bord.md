# Journal de Bord — La mémoire du quotidien

**Source vérifiée** : `extensions/journal_de_bord/__init__.py`

---

## Concept

Le Journal de Bord est la mémoire **temporelle structurée** d'OGMA. Là où la mémoire FAISS/SQLite stocke des faits sans date précise, le Journal organise les événements conversationnels par jour, avec horodatage et navigation calendaire.

C'est l'équivalent d'un agenda : l'IA sait ce qui s'est passé hier, ce matin, la semaine dernière.

---

## Ce que fait le Journal

Chaque jour, le Journal accumule des entrées horodatées. En arrière-plan, l'Archiviste génère automatiquement des résumés de la journée. Ces résumés servent à deux choses :
- Alimenter la navigation historique (interface calendaire)
- Fournir un **contexte matinal** à l'IA principale au premier message du jour

Le contexte matinal est injecté dans la conversation du matin, permettant à l'IA de naturellement évoquer ce qui s'est passé la veille ("Hier nous avons parlé de...") sans que l'utilisateur ait besoin de le rappeler.

---

## Intégration Dream Engine

Le `context_provider.py` du Journal récupère également le dernier rêve du Dream Engine non encore mentionné par l'IA. Ce contexte onirique est injecté dans le résumé matinal, permettant à l'IA d'évoquer spontanément ses rêves.

---

## Architecture

| Module | Rôle |
|---|---|
| `core_journal.py` | Moteur principal (singleton) |
| `json_manager.py` | Persistance et indexation JSON |
| `entry_generator.py` | Génération résumés via Archiviste |
| `context_provider.py` | Injection contexte conversationnel |
| `ui_components.py` | Interface (bouton + modal calendaire) |
| `config.py` | Configuration centralisée |
