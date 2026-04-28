# Recherche vectorielle et FTS5

**Source vérifiée** : `memory_manager.py` (méthodes `_search_fts5`, `retrieve_and_synthesize_context`, `_expand_personal_pronouns`, `_extract_keywords`)

---

## Pourquoi deux moteurs de recherche ?

Chaque moteur a un angle mort :

- La **recherche sémantique (FAISS)** retrouve des souvenirs par sens, même si les mots sont différents. Mais elle peut rater des correspondances précises sur des noms propres, des dates, ou des termes très spécifiques.
- La **recherche par mots-clés (FTS5)** retrouve les souvenirs qui contiennent exactement les termes de la requête. Mais elle est insensible aux reformulations et aux synonymes.

En les combinant, on couvre les deux cas.

---

## La recherche sémantique avec FAISS

FAISS (Facebook AI Similarity Search) est une bibliothèque de recherche de vecteurs. Chaque souvenir a été transformé en un vecteur numérique de dimension fixe (la "dimension d'embedding") au moment de sa création. Ce vecteur encode le sens du texte sous forme mathématique.

Quand une requête arrive, elle est à son tour transformée en vecteur. FAISS calcule alors la distance entre ce vecteur et tous les vecteurs de l'index, et retourne les `k` vecteurs les plus proches. Plus deux textes sont proches sémantiquement, plus leurs vecteurs sont proches dans cet espace mathématique.

L'index utilisé est `IndexFlatL2` — une recherche exacte par distance L2 (distance euclidienne). C'est précis mais linéaire en temps : la recherche parcourt tous les vecteurs. Pour des volumes importants, une migration vers `IndexIVFFlat` (recherche approximative plus rapide) est prévue [NON IMPLÉMENTÉ à la date de vérification].

---

## La recherche plein texte avec FTS5

SQLite intègre un moteur de recherche plein texte appelé FTS5. OGMA maintient un index FTS5 des textes originaux des souvenirs. Les requêtes utilisent le ranking BM25 (un algorithme standard de pertinence documentaire) fourni nativement par FTS5.

Les scores FTS5 sont négatifs par convention SQLite (un score plus négatif = meilleur résultat). Le `MemoryManager` les convertit en scores positifs normalisés avant la fusion.

---

## Prétraitement de la requête

Avant toute recherche, la requête de l'utilisateur passe par deux étapes :

1. **Expansion des pronoms** : les pronoms personnels ("je", "tu", "il", "me"...) sont remplacés ou étendus par les noms correspondants si disponibles dans le contexte. Cela améliore la qualité de l'embedding.

2. **Extraction des mots-clés** : les mots vides (articles, prépositions...) sont éliminés. Seuls les termes porteurs de sens sont conservés pour générer l'embedding.

---

## Fusion des scores

Le score final d'un souvenir est calculé ainsi :

$$\text{score\_hybride} = (0.6 \times \text{score\_FAISS}) + (0.4 \times \text{score\_FTS5}) + \text{bonus\_exact\_match}$$

Le bonus exact match ajoute jusqu'à 0.2 si les mots de la requête sont retrouvés dans le titre, le résumé ou le texte du souvenir.

Les souvenirs sont triés par score hybride décroissant, et les `k` meilleurs sont transmis à l'Archiviste pour synthèse.

---

## De la recherche à la synthèse

Les souvenirs récupérés ne sont pas injectés bruts dans la conversation. L'Archiviste les lit et génère une **note de synthèse** : un texte court et pertinent qui résume ce qui est utile par rapport à la question posée. C'est cette note qui arrive dans le contexte de l'IA principale, pas les souvenirs eux-mêmes.

Ce passage par l'Archiviste est délibéré : l'IA principale reçoit une information déjà digérée et mise en relation avec la question, pas un dump brut de données.
