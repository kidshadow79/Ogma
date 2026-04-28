# Biographies

**Sources vérifiées** : `extensions/biographie_profil/__init__.py`, `extensions/biographie_profil/biography_manager.py`, `data/biographies/`

---

## Concept

L'extension Biographie Profil permet à l'IA principale de construire et maintenir un journal biographique sur l'utilisateur, alimenté automatiquement par les conversations. Ce n'est pas un profil utilisateur administré manuellement : c'est une observation accumulée et structurée de ce que l'utilisateur a partagé.

---

## Deux volumes

### Volume 1 — Souvenirs filtrés

Un filtre FAISS sélectionne les souvenirs de la base mémoire qui concernent un utilisateur identifié. Ces souvenirs servent de matière première pour le journal.

### Volume 2 — Journal narratif

L'Archiviste rédige un journal biographique structuré en 10 sections :

- Portrait général
- Psyché et vie émotionnelle
- Vie intellectuelle
- Projets et créations
- Vie quotidienne et habitudes
- Relations et entourage
- Histoire personnelle
- Valeurs et convictions
- Physique et présence
- Goûts et préférences

**Règle stricte** : l'Archiviste n'écrit que ce qui est directement soutenu par un fait observé dans les souvenirs. Les sections sans fait correspondant contiennent la mention "Aucune donnée observée." L'inférence et l'extrapolation sont interdites.

---

## Déclenchement

La biographie est mise à jour via une phrase magique détectée dans les messages. L'extension utilise `BiographyMagicPhrases` pour surveiller ces déclencheurs.

Si l'Archiviste est disponible, il sélectionne intelligemment les souvenirs les plus pertinents pour enrichir le journal. Sans Archiviste, la sélection se fait par filtrage FAISS direct.

---

## Stockage

Les biographies sont sauvegardées dans `data/biographies/` sous forme de fichiers JSON structurés. Un système de backup avec rotation est intégré, inspiré du même pattern que les profils.
