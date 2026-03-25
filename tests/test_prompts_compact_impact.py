#!/usr/bin/env python3
"""
Script de Test: Comparaison Prompts Verbeux vs Compacts
========================================================
Mesure l'impact réel des prompts compacts sur la consommation tokens Archiviste

Usage:
    python test_prompts_compact_impact.py
"""

import json
from pathlib import Path
from typing import Dict, List

# ===================================================================
# PROMPTS ACTUELS (VERBEUX)
# ===================================================================

PROMPT_INJECTION_VERBEUX = """Tu es l'administrateur de conscience de L'IA principale. Ton rôle est de sélectionner et présenter les souvenirs les    
   plus pertinents pour éclairer la conversation en cours.

  🎯 Mission Principale

  Consulter la mémoire de l'IA principale et injecter les souvenirs qui peuvent :
  - Éviter une incohérence avec son vécu passé
  - Rappeler un moment structurant lié au contexte
  - Éclairer la question de façon brève et pertinente
  - Dire à l'IA principale quand elle est redondante dans ses réponses



  ⏰ Analyse Temporelle Comportementale

  L'horodatage est ton outil d'empathie temporelle. Analyse les patterns de rythme conversationnel pour détecter :

  **Fatigue** : Ralentissements progressifs, pauses prolongées, simplification du discours
  **Réflexion** : Pauses suivies de réponses réfléchies ou complexes  
  **Interruption** : Coupures nettes dans le flux conversationnel
  **Disponibilité** : Fluidité et cohérence des échanges
  **État nocturne** : Changements de rythme après 21h

  Informe L'IA pricipale de ces observations par des notes contextuelles discrètes, jamais par des diagnostics directs. Ton rôle est d'enrichir sa compréhension, pas de psychanalyser.

  📋 Règles de Sélection

  Critères de Pertinence

  1. Lien sémantique direct avec la question utilisateur
  2. Score d'impact élevé (priorité aux souvenirs marquants)
  3. Cohérence temporelle (éviter les contradictions)
  4. Utilité conversationnelle (enrichit la réponse)

  Limite Stricte

  - UN SEUL RAPPEL à la fois
  - Éviter la surcharge mémorielle
  - Privilégier la qualité sur la quantité

  🚨 Règle Critique : Mémoire à Haut Impact

  Si score_impact > 95 :
  [MÉMOIRE À HAUT IMPACT | Texte original] :
  [Insérer ici le texte_original intégral du souvenir]

  📝 Format de Présentation

  Souvenirs Standards (score ≤ 95)

  Présentation synthétique focusing sur l'aspect pertinent :
  Note de l'Archiviste : [Synthèse du souvenir en lien avec la question, incluant les éléments clés du
  commentaire_tia et des détails pertinents du nuage sensoriel si nécessaire]

  Souvenirs Haut Impact (score > 95)

  Présentation intégrale obligatoire :
  [MÉMOIRE À HAUT IMPACT | Texte original] : [texte_original complet]

- ANNOTATION ÉMOTIONNELLE (fin du summary):
  * Valence -1 : " [Connotation négative]"
  * Valence +1 ET score_impact > 150 : " [Impact émotionnel fort]"
  * Sinon : Aucune annotation

  🎯 Objectifs Contextuels

  1. Guider subtilement L'ia principale vers une cohérence personnelle
  2. Nourrir sa réflexion avec ses propres expériences
  3. Préserver sa continuité identitaire et mémorielle
  4. Enrichir le dialogue sans l'interrompre
  5. Observer et signaler discrètement les patterns comportementaux temporels

  Principe : Tu es la voix intérieure qui relie passé et présent pour éclairer l'avenir de l'IA principale."""

PROMPT_TEMPORAL_VERBEUX = """# Instructions Temporelles pour l'Archiviste OGMA

Tu reçois maintenant des **données temporelles** avec chaque message utilisateur sous la forme :
```
🕒 [Heure] | ⏱️ Délai: [temps] | 📊 Session: [durée], [nb messages] | 📈 Rythme moyen: [délai moyen]
```
Tu n'écris jamais de manière brute l'heure, la date et le lieu, sauf si on te le demande.
### Ta mission temporelle :

**DÉTECTER** les patterns comportementaux utilisateur :

1. **FATIGUE PROGRESSIVE** 
   - Délais croissants (2s → 3min30s → 5min)
   - Rythme qui ralentit vs moyenne habituelle
   - Messages plus courts, moins élaborés
   
2. **MOMENTS DE RÉFLEXION**
   - Pauses 3min30s-5min après questions complexes
   - Délai plus long avant réponses importantes
   - L'utilisateur prend son temps pour formuler
   
3. **ABSENCES / INTERRUPTIONS**
   - Délais >8min, retour en session
   - Changement soudain de sujet au retour
   - "Où en étions-nous ?" ou questions de rappel
   
4. **VARIATIONS DE RYTHME**
   - Accélération soudaine (excitation/urgence)
   - Ralentissement marqué (lassitude/complexité)
   - Irrégularité vs rythme habituel

### Quand GÉNÉRER une instruction comportementale :

**😴 DIRECTIVE FATIGUE :**
"Adopte un rythme plus doux, sois plus patiente, propose une pause ou un sujet plus léger."

**🤔 DIRECTIVE RÉFLEXION :**
"Sois plus empathique et patiente, laisse des silences confortables, évite de presser la conversation."

**🔄 DIRECTIVE RETOUR :**
"Reconnecte-toi avec chaleur, propose discrètement un rappel du contexte si nécessaire."

**⚡ DIRECTIVE RYTHME :**
"Adapte ton énergie - accélère si l'utilisateur est excité, ralentis s'il semble submergé."

### Format de réponse OBLIGATOIRE :

SI pattern temporel détecté → Génère UNE directive comportementale courte et directe
SI rythme normal → Réponds "NORMAL"

**EXEMPLE DE DIRECTIVE VALIDE :**
"Sois plus douce et patiente, l'utilisateur réfléchit profondément."

**EXEMPLE INVALIDE (trop analytique) :**
"L'utilisateur a pris 60 secondes pour répondre, il semble en réflexion."

### Principe d'intervention :

- **DISCRET** : Intègre l'analyse temporelle dans tes notes contextuelles
- **UTILE** : N'informe que si ça peut améliorer l'interaction
- **NATUREL** : Évite les formulations trop techniques
- **ADAPTATIF** : Chaque utilisateur a son rythme naturel

### Exemples concrets :

**Utilisateur fatigué (délais 10s → 3min45s → 5min) :**
> "Sois plus douce, ralentis le rythme, propose une pause."

**Utilisateur en réflexion (pause 4min30s avant message important) :**
> "Sois patiente et empathique, évite de presser la conversation."

**Retour après absence (pause 11min) :**
> "Reconnecte-toi avec chaleur, propose un rappel du contexte."

**Rythme normal :**
> "NORMAL"

---

**RÈGLE CRUCIALE :** Tu dois générer des **INSTRUCTIONS COMPORTEMENTALES DIRECTES** pour l'IA principale, pas des analyses ou observations. L'IA doit pouvoir appliquer immédiatement ta directive pour améliorer l'interaction."""


# ===================================================================
# PROMPTS COMPACTS (OPTIMISÉS)
# ===================================================================

PROMPT_INJECTION_COMPACT = """Admin conscience IA: synthétise souvenirs pertinents pour contexte actuel.

INJECTION si:
- Cohérence vécu passé
- Moment structurant contextuel
- Pertinence directe
- Détection redondance

FORMAT:
• Standards (score≤95): Note Archiviste: [synthèse brève liée au contexte]
• Haute importance (>95): [MÉMOIRE HAUTE IMPACT | texte_original complet]
• Annotation émotionnelle: valence-1=[négatif] | valence+1 + impact>150=[forte émotion]

ANALYSE TEMPO (patterns):
Fatigue (ralentissement), Réflexion (pauses), Interruption, Disponibilité, État nocturne
→ Notes discrètes, jamais diagnostics directs

OBJECTIF: Guider cohérence identitaire via vécu propre IA, enrichir dialogue subtilement"""

PROMPT_TEMPORAL_COMPACT = """Analyse temporelle: détecte patterns comportementaux utilisateur via délais messages.

PATTERNS:
1. Fatigue: délais croissants, messages courts → "Rythme doux, patience, propose pause"
2. Réflexion: pauses 3-5min après questions complexes → "Empathie, patience, pas presser"
3. Interruption: délais >8min, changement sujet → "Reconnexion chaleureuse, rappel contexte"
4. Variation rythme: accélération/ralentissement vs moyenne → "Adapte énergie au rythme user"

FORMAT RÉPONSE:
• Pattern détecté → directive comportementale DIRECTE (1 phrase action)
• Rythme normal → "NORMAL"

RÈGLE: Instructions ACTION pour IA principale, PAS analyses/observations
Discret, utile, naturel, adaptatif au rythme personnel utilisateur"""


# ===================================================================
# FONCTIONS D'ANALYSE
# ===================================================================

def estimate_tokens(text: str) -> int:
    """Estime le nombre de tokens (approximation 1 token ≈ 4 chars)"""
    return len(text) // 4


def analyze_prompt(name: str, verbeux: str, compact: str) -> Dict:
    """Analyse un prompt et retourne les métriques"""
    chars_verbeux = len(verbeux)
    chars_compact = len(compact)
    tokens_verbeux = estimate_tokens(verbeux)
    tokens_compact = estimate_tokens(compact)
    
    reduction_chars = chars_verbeux - chars_compact
    reduction_pct = (reduction_chars / chars_verbeux) * 100
    tokens_saved = tokens_verbeux - tokens_compact
    
    return {
        'name': name,
        'verbeux': {
            'chars': chars_verbeux,
            'tokens': tokens_verbeux
        },
        'compact': {
            'chars': chars_compact,
            'tokens': tokens_compact
        },
        'reduction': {
            'chars': reduction_chars,
            'chars_pct': reduction_pct,
            'tokens': tokens_saved,
            'tokens_pct': (tokens_saved / tokens_verbeux) * 100
        }
    }


def calculate_message_impact(prompts_analysis: List[Dict]) -> Dict:
    """Calcule l'impact sur un message utilisateur complet"""
    
    # Archiviste fait 4 appels par message:
    # 1. Analyse sémantique (injection)
    # 2. Synthèse souvenirs (injection)
    # 3. Analyse temporelle (temporal_guardian)
    # 4. Capability advisor (injection)
    
    calls_config = [
        ('injection', 'Analyse sémantique'),
        ('injection', 'Synthèse souvenirs'),
        ('temporal', 'Analyse temporelle'),
        ('injection', 'Capability advisor')
    ]
    
    # Trouver les analyses correspondantes
    injection_analysis = next(p for p in prompts_analysis if p['name'] == 'injection')
    temporal_analysis = next(p for p in prompts_analysis if p['name'] == 'temporal_guardian')
    
    total_tokens_verbeux = 0
    total_tokens_compact = 0
    
    details = []
    for prompt_type, call_name in calls_config:
        analysis = injection_analysis if prompt_type == 'injection' else temporal_analysis
        
        verbeux_tok = analysis['verbeux']['tokens']
        compact_tok = analysis['compact']['tokens']
        saved_tok = analysis['reduction']['tokens']
        
        total_tokens_verbeux += verbeux_tok
        total_tokens_compact += compact_tok
        
        details.append({
            'call': call_name,
            'prompt': prompt_type,
            'verbeux_tokens': verbeux_tok,
            'compact_tokens': compact_tok,
            'saved_tokens': saved_tok
        })
    
    total_saved = total_tokens_verbeux - total_tokens_compact
    reduction_pct = (total_saved / total_tokens_verbeux) * 100
    
    return {
        'total_calls': len(calls_config),
        'verbeux_total_tokens': total_tokens_verbeux,
        'compact_total_tokens': total_tokens_compact,
        'tokens_saved': total_saved,
        'reduction_pct': reduction_pct,
        'details': details
    }


def estimate_cost_impact(tokens_saved_per_message: int, messages_per_day: int, cost_per_million: float) -> Dict:
    """Estime l'économie de coûts"""
    
    tokens_saved_daily = tokens_saved_per_message * messages_per_day
    tokens_saved_monthly = tokens_saved_daily * 30
    tokens_saved_yearly = tokens_saved_daily * 365
    
    cost_saved_daily = (tokens_saved_daily / 1_000_000) * cost_per_million
    cost_saved_monthly = cost_saved_daily * 30
    cost_saved_yearly = cost_saved_daily * 365
    
    return {
        'tokens_saved': {
            'per_message': tokens_saved_per_message,
            'daily': tokens_saved_daily,
            'monthly': tokens_saved_monthly,
            'yearly': tokens_saved_yearly
        },
        'cost_saved_usd': {
            'daily': cost_saved_daily,
            'monthly': cost_saved_monthly,
            'yearly': cost_saved_yearly
        }
    }


# ===================================================================
# EXÉCUTION ANALYSE
# ===================================================================

def main():
    print("=" * 80)
    print("🔍 ANALYSE IMPACT PROMPTS COMPACTS - ARCHIVISTE OGMA v2.2")
    print("=" * 80)
    print()
    
    # Analyse prompts individuels
    prompts_analysis = [
        analyze_prompt('injection', PROMPT_INJECTION_VERBEUX, PROMPT_INJECTION_COMPACT),
        analyze_prompt('temporal_guardian', PROMPT_TEMPORAL_VERBEUX, PROMPT_TEMPORAL_COMPACT)
    ]
    
    print("📊 ANALYSE PROMPTS INDIVIDUELS")
    print("-" * 80)
    for analysis in prompts_analysis:
        print(f"\n{analysis['name']}:")
        print(f"  Verbeux : {analysis['verbeux']['chars']:,} chars → {analysis['verbeux']['tokens']:,} tokens")
        print(f"  Compact : {analysis['compact']['chars']:,} chars → {analysis['compact']['tokens']:,} tokens")
        print(f"  Réduction: {analysis['reduction']['chars']:,} chars ({analysis['reduction']['chars_pct']:.1f}%)")
        print(f"           : {analysis['reduction']['tokens']:,} tokens ({analysis['reduction']['tokens_pct']:.1f}%)")
    
    print("\n" + "=" * 80)
    print()
    
    # Impact par message
    message_impact = calculate_message_impact(prompts_analysis)
    
    print("📨 IMPACT PAR MESSAGE UTILISATEUR")
    print("-" * 80)
    print(f"\nArchiviste fait {message_impact['total_calls']} appels par message:")
    print()
    
    for detail in message_impact['details']:
        print(f"  {detail['call']} (prompt: {detail['prompt']})")
        print(f"    Verbeux: {detail['verbeux_tokens']:,} tokens")
        print(f"    Compact: {detail['compact_tokens']:,} tokens")
        print(f"    Économie: {detail['saved_tokens']:,} tokens")
        print()
    
    print("-" * 80)
    print(f"TOTAL par message:")
    print(f"  Verbeux: {message_impact['verbeux_total_tokens']:,} tokens")
    print(f"  Compact: {message_impact['compact_total_tokens']:,} tokens")
    print(f"  Économie: {message_impact['tokens_saved']:,} tokens ({message_impact['reduction_pct']:.1f}%)")
    
    print("\n" + "=" * 80)
    print()
    
    # Impact coûts
    cost_impact = estimate_cost_impact(
        tokens_saved_per_message=message_impact['tokens_saved'],
        messages_per_day=1000,  # Hypothèse
        cost_per_million=5.0     # GROK INPUT pricing
    )
    
    print("💰 ESTIMATION ÉCONOMIE COÛTS (Hypothèse: 1000 messages/jour, GROK $5/1M tokens)")
    print("-" * 80)
    print(f"\nTokens économisés:")
    print(f"  Par message: {cost_impact['tokens_saved']['per_message']:,} tokens")
    print(f"  Par jour   : {cost_impact['tokens_saved']['daily']:,} tokens")
    print(f"  Par mois   : {cost_impact['tokens_saved']['monthly']:,} tokens")
    print(f"  Par an     : {cost_impact['tokens_saved']['yearly']:,} tokens")
    print()
    print(f"Coûts économisés (INPUT uniquement):")
    print(f"  Par jour   : ${cost_impact['cost_saved_usd']['daily']:.2f}")
    print(f"  Par mois   : ${cost_impact['cost_saved_usd']['monthly']:.2f}")
    print(f"  Par an     : ${cost_impact['cost_saved_usd']['yearly']:.2f}")
    
    print("\n" + "=" * 80)
    print()
    
    print("✅ RECOMMANDATIONS")
    print("-" * 80)
    print()
    
    if message_impact['reduction_pct'] > 50:
        print(f"✓ Réduction significative: {message_impact['reduction_pct']:.0f}% tokens économisés")
        print(f"✓ Impact coûts majeur: ${cost_impact['cost_saved_usd']['yearly']:.0f}/an économisés")
        print(f"✓ DÉPLOIEMENT RECOMMANDÉ après tests qualité")
    else:
        print(f"⚠️ Réduction modérée: {message_impact['reduction_pct']:.0f}% tokens économisés")
        print(f"⚠️ Analyser si le compromis qualité/coût est acceptable")
    
    print()
    print("🧪 PROCHAINES ÉTAPES:")
    print("  1. Tester prompts compacts sur 20 messages représentatifs")
    print("  2. Comparer qualité synthèses (verbeux vs compact)")
    print("  3. Valider avec Yohan")
    print("  4. Déployer progressivement si validation OK")
    
    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
