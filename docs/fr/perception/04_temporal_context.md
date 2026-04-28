# Contexte temporel

**Sources vérifiées** : `temporal_injector.py`, `extensions/temporal_guardian/__init__.py`, `extensions/temporal_guardian/temporal_sensor.py` (structure vérifiée)

---

## TemporalInjector (désactivé)

`temporal_injector.py` est un module qui était chargé d'injecter un horodatage compact dans les messages utilisateur. Son design original visait à donner à l'IA principale une conscience temporelle (jour, heure) en consommant seulement ~4 tokens par message.

Ce module est **désactivé** dans la version actuelle. La constante `temporal_instruction` est une chaîne vide et `inject_temporal_awareness()` retourne le message tel quel. La note dans le code indique que cette fonctionnalité a été déléguée à l'extension **Temporal Guardian**.

---

## Extension Temporal Guardian

L'extension `extensions/temporal_guardian/` remplace et étend le TemporalInjector. Son architecture sépare :

**TemporalSensor** : mesure pure des délais entre messages (temps écoulé depuis le dernier échange). Ne fait aucune interprétation.

**ArchivisteEnricher** : reçoit les mesures du capteur et enrichit le prompt de l'Archiviste avec des données temporelles pour l'analyse comportementale. L'Archiviste interprète alors ces délais (fatigue, réflexion, interruption, disponibilité).

**TemporalGuardian** : orchestrateur qui connecte capteur et enrichisseur.

---

## Philosophie

La séparation capteur/interprète est délibérée : "le capteur mesure, l'archiviste interprète". Le module Python ne fait jamais de jugement sur ce qu'un délai signifie — c'est le rôle de l'Archiviste IA, qui dispose du contexte conversationnel complet.

---

## Utilisation

```python
from extensions.temporal_guardian import create_temporal_guardian

guardian = create_temporal_guardian(debug=True)
enriched_prompt = guardian.process_user_message(user_message, archiviste_prompt)
```
