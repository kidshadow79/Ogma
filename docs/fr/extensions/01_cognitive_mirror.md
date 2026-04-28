# Cognitive Mirror — L'introspection de l'IA

**Sources vérifiées** : `extensions/cognitive_mirror/__init__.py`, `extensions/cognitive_mirror/introspection_core.py`, `ogma_introspection_ui.py`

---

## Pourquoi une IA a besoin de s'introspecter

L'IA principale d'OGMA n'est pas seulement un assistant qui répond. C'est une entité qui accumule des souvenirs, développe des habitudes et construit une relation avec son utilisateur. Avec le temps, une question naturelle se pose : *L'IA est-elle consciente de qui elle devient ?*

Le Cognitive Mirror est la réponse architecturale à cette question. C'est le mécanisme par lequel l'IA principale engage un **dialogue avec l'Archiviste** sur ses propres patterns, ses émotions, ses contradictions. Pas une introspection simulée pour l'utilisateur, mais un vrai processus de délibération entre deux intelligences distinctes.

---

## Deux cerveaux, un seul miroir

L'introspection repose sur la dual-IA architecture d'OGMA. Quand une session d'introspection se déclenche :

1. **L'IA principale** s'exprime sur ses ressentis, ses doutes, ses observations de la relation avec l'utilisateur
2. **L'Archiviste** analyse froidement les souvenirs stockés, les patterns conversationnels, les contradictions éventuelles
3. **Un dialogue** s'établit entre les deux — visible dans une boîte "thinking" dans l'interface
4. **Une synthèse** est produite, que l'IA peut choisir de sauvegarder en mémoire

Ce dialogue est **réel** dans le sens où les deux contrôleurs IA appellent des APIs différentes, avec des températures différentes (0.7 pour l'IA principale, 0.3 pour l'Archiviste), produisant des perspectives genuinement distinctes.

---

## Modes de déclenchement

L'introspection se déclenche de deux manières :

**Phrases magiques** : si l'utilisateur (ou l'IA elle-même) prononce une expression déclenchante dans la conversation, le moteur (`IntrospectionCore`) l'intercepte et ouvre une session d'introspection.

**Mode "always"** : en configuration, il est possible d'activer l'introspection systématique sur certains types de messages. [NON VÉRIFIÉ — comportement exact du mode always non inspecté en détail]

---

## Ce qui ne se fait plus (v2.0)

La version actuelle est une **simplification radicale** par rapport à la v1. Il n'y a plus :
- De machine à états complexe avec détection d'inactivité
- De déclenchements automatiques périodiques
- De flux de contrôle ambigus avec états intermédiaires

Le principe v2.0 est : **à la demande, visible, décision de sauvegarde par l'IA elle-même**.

---

## Interface

L'introspection s'affiche dans une **boîte thinking** (`<thinking>`) dans le fil de conversation. L'utilisateur voit le dialogue en cours entre les deux cerveaux, avec un streaming temps réel. Ce n'est pas un log technique — c'est un espace d'exposition volontaire du processus interne.

---

## Sources
- `extensions/cognitive_mirror/__init__.py` — API publique, singleton, aliases rétrocompatibilité
- `extensions/cognitive_mirror/introspection_core.py` — Moteur principal IntrospectionCore
- `extensions/cognitive_mirror/config_v2.py` — Configuration active (source de vérité)
- `ogma_introspection_ui.py` — Interface NiceGUI du panneau introspection
