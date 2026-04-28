# Project RAG — Documents à portée de main

**Source vérifiée** : `extensions/project_rag/__init__.py`

---

## Concept

Le Project RAG (Retrieval-Augmented Generation) permet d'uploader des documents et de les rendre interrogeables par l'IA principale. Chaque projet est isolé avec sa propre base de connaissances.

L'idée : vous avez 200 pages d'un rapport, un code source, ou des notes de réunion. Au lieu de tout coller dans un prompt, le RAG indexe ces documents et injecte **uniquement les passages pertinents** à chaque message.

---

## Architecture isolée par projet

Chaque projet possède sa propre mémoire SQLite + index FAISS, indépendante de la mémoire principale d'OGMA. Cette isolation garantit que les documents d'un projet ne contaminent pas les recherches d'un autre.

| Module | Rôle |
|---|---|
| `project_config.py` | Configuration JSON par projet |
| `project_manager.py` | Mémoire isolée SQLite + FAISS |
| `project_chunker.py` | Chunking adaptatif par type de fichier |
| `project_retriever.py` | Recherche sémantique + cache |
| `project_injector.py` | Injection contexte dans le pipeline chat |
| `project_ui.py` | Interface NiceGUI overlay |

---

## Chunking adaptatif

Le découpage des documents dépend du type de fichier (PDF, code, markdown, texte plain). Chaque type utilise une stratégie de découpage optimisée pour préserver la cohérence sémantique des passages.

---

## Cache de recherche

Le `project_retriever.py` maintient un cache des résultats de recherche pour éviter de ré-indexer les mêmes requêtes fréquentes. Ce cache est lié à la session.
