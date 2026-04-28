# Contextual Recall — La mémoire du passé récent

**Source vérifiée** : `extensions/contextual_recall/__init__.py`

---

## Concept

Quand un utilisateur dit "comme je te disais il y a deux jours" ou "tu te souviens de notre conversation de la semaine dernière ?", l'IA doit pouvoir accéder à ces souvenirs sans que l'utilisateur répète tout.

Contextual Recall résout ce problème en détectant automatiquement les références temporelles dans les messages et en chargeant les résumés de conversations correspondantes.

---

## Fonctionnement

**TemporalParser** identifie les expressions temporelles dans le message : "hier", "il y a 2 jours", "la semaine dernière", dates précises, etc.

**SummaryLoader** accède aux résumés persistés dans les fichiers JSON de conversations (format v2.2+) pour la période identifiée.

**ContextBuilder** formate ces résumés et les injecte dans le contexte système de la conversation courante.

L'utilisateur ne voit rien de ce processus — l'IA répond simplement avec accès au bon passé.

---

## Philosophie

Pas de phrase magique, pas de commande. La détection est **entièrement automatique et transparente**. Le module s'active uniquement quand une référence temporelle est détectée, évitant les injections inutiles.
