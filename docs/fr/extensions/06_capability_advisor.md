# Capability Advisor — L'IA qui sait quand utiliser ses outils

**Source vérifiée** : `extensions/capability_advisor/__init__.py`

---

## Concept

OGMA possède plusieurs capacités spéciales (mémoriser, s'introspecter, générer des images, voir via webcam, chercher sur internet, consulter une biographie). Sans guidance, l'IA peut oublier d'utiliser la bonne capacité au bon moment.

Le Capability Advisor résout ce problème : à chaque message, l'Archiviste analyse le contexte et **suggère une capacité pertinente** si le contexte le justifie. Cette suggestion est visible sous forme de LED dans l'interface, et transmise à l'IA principale comme conseil discret.

---

## Les 6 capacités gérées

| Icône | Capacité | Déclenchement typique |
|---|---|---|
| 💾 | Mémorisation | Information importante à retenir |
| 🧠 | Introspection | Question sur l'IA elle-même |
| 🎨 | Génération Image | Demande de visualisation |
| 📷 | Vision Webcam | Contexte visuel pertinent |
| 🌐 | Recherche Web | Besoin d'information récente |
| 👤 | Biographie | Question personnelle sur l'utilisateur |

---

## Workflow

1. Message utilisateur reçu
2. Archiviste analyse le message (contexte, intention, historique récent)
3. Si un contexte pertinent est détecté → suggestion d'UNE capacité (pas systématique)
4. La LED correspondante s'allume dans le header
5. Un conseil concis est injecté dans le contexte de l'IA principale
6. La LED s'éteint après utilisation effective de la capacité

---

## Philosophie

Le Capability Advisor ne force jamais rien. Il suggère. L'IA principale décide de suivre ou non le conseil. Cette approche évite l'utilisation mécanique des outils et préserve le caractère naturel de la conversation.
