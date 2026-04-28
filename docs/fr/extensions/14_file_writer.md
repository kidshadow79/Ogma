# File Writer — Sauvegarde automatique de fichiers

**Source vérifiée** : `extensions/file_writer/__init__.py`

---

## Concept

Le File Writer détecte quand l'IA principale génère du contenu destiné à être sauvegardé sous forme de fichier Markdown, et le sauvegarde automatiquement dans `data/uploads/`.

---

## Mécanisme

L'extension analyse les réponses de l'IA principale à la recherche de blocs Markdown contenant un titre de document. Si un bloc est détecté et que le contexte suggère une demande de création de fichier (résumé, rapport, article, etc.), le contenu est extrait et sauvegardé avec le titre du document comme nom de fichier.

Une notification discrète informe l'utilisateur du fichier créé.

---

## Déclenchement

Deux conditions doivent être réunies :
1. La réponse IA contient un bloc Markdown structuré avec titre
2. La demande utilisateur suggère une création de fichier ("rédige un rapport", "crée un document", etc.)

L'extension ne sauvegarde pas tous les blocs de code ou Markdown — uniquement ceux clairement destinés à être des fichiers.
