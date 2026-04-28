# Biographie — Portrait évolutif de l'utilisateur

**Source vérifiée** : `extensions/biographie_profil/` (voir aussi [docs/identity/04_biographies.md](../identity/04_biographies.md))

---

## Concept

La Biographie est un portrait structuré et évolutif de l'utilisateur, construit automatiquement à partir des souvenirs FAISS. C'est la réponse à la question : "Si l'IA devait me décrire à quelqu'un qui ne me connaît pas, que dirait-elle ?"

---

## Deux volumes

**Volume 1 — Portrait factuel** : synthèse des souvenirs marqués comme importants dans FAISS (score d'importance élevé). L'Archiviste filtre et structure ces souvenirs en sections thématiques (personnalité, centres d'intérêt, habitudes, relations, projets).

**Volume 2 — Journal narratif** : récit plus personnel, organisé en 10 sections prédéfinies. L'Archiviste maintient ce journal au fil des conversations, sans jamais inférer ce qui n'a pas été observé. Si une section est vide, elle reste vide — "Aucune donnée observée".

---

## Règle d'or anti-inférence

La biographie ne contient **aucune déduction**. Si l'utilisateur n'a pas dit explicitement qu'il aime la musique classique, cette information n'apparaît pas. Cette règle est appliquée au niveau des prompts de l'Archiviste biographe.

---

## Usage par l'IA principale

Quand le Capability Advisor suggère la capacité "Biographie" (👤), l'IA principale peut consulter le portrait pour personnaliser sa réponse. La biographie est également disponible comme contexte de fond pour les conversations profondes sur l'utilisateur.

---

*Pour la documentation technique complète sur le système de biographie, voir [identity/04_biographies.md](../identity/04_biographies.md).*
