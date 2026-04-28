# Signal d'arrêt global

**Source vérifiée** : `stop_signal.py`

---

## À quoi ça sert ?

Certaines opérations dans OGMA prennent du temps : générer une réponse token par token, analyser des souvenirs, faire tourner l'Archiviste. Si l'utilisateur clique sur "Arrêter" pendant qu'une de ces opérations tourne, il faut un moyen propre de l'interrompre — sans tuer le processus, sans laisser des états incohérents.

`stop_signal.py` fournit ce mécanisme : un simple drapeau global (`_stop_requested`) que n'importe quelle partie du code peut lever ou vérifier.

---

## Comment ça fonctionne

Le principe est volontairement simple. Il y a trois actions possibles :

- **Lever le signal** : `request_stop()` passe le drapeau à `True`. C'est ce qu'appelle le bouton d'arrêt dans l'interface.
- **Réinitialiser** : `reset_stop()` repasse le drapeau à `False`. C'est appelé au début d'une nouvelle opération, pour s'assurer qu'un arrêt précédent ne bloque pas la suivante.
- **Vérifier et interrompre** : `check_stop_and_raise()` lève une exception `StopAsyncIteration` si le signal est actif. Les générateurs de streaming appellent cette fonction à intervalles réguliers — dès que le signal est levé, la génération s'arrête proprement.

---

## Limites du mécanisme

Ce module ne sait pas *qui* a demandé l'arrêt, ni *quelle* opération est en cours. C'est un signal binaire global. Si deux opérations longues tournent en parallèle (ce qui est rare mais possible), lever le signal les interrompt toutes les deux.

Le module ne gère pas non plus les threads : si une opération bloquante tourne dans un thread Python séparé (ex. chargement d'un modèle GGUF), le signal ne l'atteint pas directement.
