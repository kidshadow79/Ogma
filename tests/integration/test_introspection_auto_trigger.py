"""
Test Introspection Auto-Déclenchée
===================================

Simule le scénario où l'IA écrit [RÉFLEXION-STRUCTURÉE] dans sa réponse
pour comprendre pourquoi il y a double déclenchement.

Workflow testé:
1. Message utilisateur normal (ex: "Comment tu fonctionnes?")
2. Capability Advisor suggère introspection → Injecte [RÉFLEXION-STRUCTURÉE]
3. IA génère réponse contenant [RÉFLEXION-STRUCTURÉE]
4. Détection post-génération → Que se passe-t-il ?
"""

import re
import asyncio
from pathlib import Path

# Patterns de détection (copié depuis ogma_ng.py ligne 3334-3338)
INTROSPECTION_PATTERNS_USER = [
    r"il\s+faut\s+que\s+tu\s+réfléchisses",
    r"lance\s+(?:une\s+)?introspection",
    r"déclenche\s+(?:une\s+)?introspection",
    r"réfléchis\s+en\s+profondeur"
]

# Pattern Capability Advisor (nouveau)
INTROSPECTION_PATTERN_AI = r"\[RÉFLEXION-STRUCTURÉE\]"


def test_detection_message_utilisateur():
    """Test 1: Détection phrase magique UTILISATEUR"""
    print("\n" + "="*70)
    print("TEST 1: Détection Phrase Magique UTILISATEUR")
    print("="*70)
    
    test_messages = [
        "Comment tu fonctionnes?",
        "Réfléchis en profondeur à cette question",
        "Lance une introspection",
        "Il faut que tu réfléchisses à ça"
    ]
    
    for msg in test_messages:
        is_magic = any(re.search(pattern, msg, re.IGNORECASE) for pattern in INTROSPECTION_PATTERNS_USER)
        print(f"\nMessage: '{msg}'")
        print(f"  → Phrase magique détectée: {is_magic}")


def test_detection_reponse_ia():
    """Test 2: Détection [RÉFLEXION-STRUCTURÉE] dans RÉPONSE IA"""
    print("\n" + "="*70)
    print("TEST 2: Détection [RÉFLEXION-STRUCTURÉE] dans RÉPONSE IA")
    print("="*70)
    
    test_responses = [
        "Pour répondre à ta question, [RÉFLEXION-STRUCTURÉE] je dois analyser...",
        "[RÉFLEXION-STRUCTURÉE]",
        "Hmm, laisse-moi réfléchir à ça profondément.",
        "Je vais prendre un moment pour méditer sur cette question."
    ]
    
    for response in test_responses:
        is_magic_ai = re.search(INTROSPECTION_PATTERN_AI, response, re.IGNORECASE)
        is_magic_user = any(re.search(pattern, response, re.IGNORECASE) for pattern in INTROSPECTION_PATTERNS_USER)
        
        print(f"\nRéponse IA: '{response[:60]}...'")
        print(f"  → Pattern AI [RÉFLEXION-STRUCTURÉE]: {bool(is_magic_ai)}")
        print(f"  → Pattern USER (il faut que...): {is_magic_user}")


def test_workflow_complet():
    """Test 3: Workflow complet avec Capability Advisor"""
    print("\n" + "="*70)
    print("TEST 3: Workflow Complet Capability Advisor → Introspection")
    print("="*70)
    
    print("\nÉTAPE 1: Message utilisateur")
    user_message = "Comment tu fonctionnes en profondeur?"
    print(f"  User: '{user_message}'")
    
    # Vérifier détection AVANT génération
    is_trigger_before = any(re.search(pattern, user_message, re.IGNORECASE) 
                            for pattern in INTROSPECTION_PATTERNS_USER)
    print(f"\n  ❓ Déclenchement AVANT génération (phrase magique user): {is_trigger_before}")
    
    print("\nÉTAPE 2: Capability Advisor analyse")
    print("  → Archiviste détecte besoin introspection")
    print("  → Suggestion: [RÉFLEXION-STRUCTURÉE]")
    print("  → LED 🧠 introspection allumée")
    
    print("\nÉTAPE 3: Injection system prompt")
    injection = """╔══════════════════════════════════════╗
║  ⚡ OBLIGATION IMMÉDIATE ⚡  ║
╚══════════════════════════════════════╝

TU DOIS ÉCRIRE: "[RÉFLEXION-STRUCTURÉE]"
"""
    print(f"  Injection: {injection[:80]}...")
    
    print("\nÉTAPE 4: IA génère réponse")
    # Simuler 2 cas possibles
    
    print("\n  📊 CAS A: IA obéit et écrit la phrase magique")
    ai_response_A = "Pour répondre à cette question complexe, [RÉFLEXION-STRUCTURÉE] je dois d'abord analyser mes processus internes..."
    print(f"    Réponse: '{ai_response_A[:80]}...'")
    
    is_magic_A = re.search(INTROSPECTION_PATTERN_AI, ai_response_A)
    print(f"    → Pattern détecté: {bool(is_magic_A)}")
    print(f"    ⚠️  PROBLÈME POTENTIEL: Double déclenchement si détection post-génération active!")
    
    print("\n  📊 CAS B: IA ignore et écrit normalement")
    ai_response_B = "Je fonctionne grâce à une architecture OGMA tripartite avec interaction, mémoire et vectorisation..."
    print(f"    Réponse: '{ai_response_B[:80]}...'")
    
    is_magic_B = re.search(INTROSPECTION_PATTERN_AI, ai_response_B)
    print(f"    → Pattern détecté: {bool(is_magic_B)}")
    print(f"    ✅ Pas de détection → LED s'éteindra après timeout")


def test_double_declenchement_scenario():
    """Test 4: Scénario exact du bug rapporté"""
    print("\n" + "="*70)
    print("TEST 4: Scénario Bug - Double Déclenchement Introspection")
    print("="*70)
    
    print("\n📝 CONTEXTE:")
    print("  - Mode introspection: Auto (always)")
    print("  - OU Capability Advisor suggère introspection")
    print("  - IA écrit [RÉFLEXION-STRUCTURÉE] dans sa réponse")
    
    print("\n🔍 HYPOTHÈSE 1: Détection pendant streaming")
    print("  1️⃣  IA commence à générer: 'Pour répondre...'")
    print("  2️⃣  IA écrit: '[RÉFLEXION-STRUCTURÉE]'")
    print("  3️⃣  🚨 DÉTECTION IMMÉDIATE → Crée boîte 'Dialogue en cours...'")
    print("  4️⃣  IA continue: '...je dois analyser mes processus'")
    print("  5️⃣  Génération complète → FIN")
    print("  6️⃣  🚨 DÉTECTION POST-GÉNÉRATION → Crée 2ème boîte introspection")
    print("\n  ❌ RÉSULTAT: Deux boîtes, première vide (arrêtée trop tôt)")
    
    print("\n🔍 HYPOTHÈSE 2: Double workflow (auto + post-détection)")
    print("  1️⃣  Mode auto → Lance introspection AVANT génération")
    print("     → Affiche 'Dialogue en cours...' puis ATTEND callback")
    print("  2️⃣  IA génère réponse avec [RÉFLEXION-STRUCTURÉE]")
    print("  3️⃣  Détection post-génération → Lance 2ème introspection")
    print("  4️⃣  1ère introspection jamais complétée (callback manquant?)")
    print("\n  ❌ RÉSULTAT: Première incomplète, deuxième fonctionne")
    
    print("\n🔍 HYPOTHÈSE 3: Conflit auto-déclenchée vs classique")
    print("  1️⃣  Capability Advisor suggère → Injection [RÉFLEXION-STRUCTURÉE]")
    print("  2️⃣  IA obéit → Écrit [RÉFLEXION-STRUCTURÉE] dans réponse")
    print("  3️⃣  Système détecte phrase magique CLASSIQUE (non auto)")
    print("  4️⃣  Lance introspection CLASSIQUE → Override auto-déclenchée")
    print("\n  ❌ RÉSULTAT: Auto-déclenchée abandonnée, classique prend le relais")


def analyser_code_detection():
    """Test 5: Analyse code OGMA pour trouver hook post-génération"""
    print("\n" + "="*70)
    print("TEST 5: Recherche Hook Post-Génération dans OGMA")
    print("="*70)
    
    ogma_file = Path("ogma_ng.py")
    
    if not ogma_file.exists():
        print("  ⚠️  Fichier ogma_ng.py non trouvé dans répertoire courant")
        return
    
    print(f"\n  📂 Analyse: {ogma_file}")
    
    # Patterns à chercher
    search_patterns = [
        (r"cleaned_reply.*introspection", "Détection introspection dans cleaned_reply"),
        (r"reply.*\[RÉFLEXION", "Détection [RÉFLEXION-STRUCTURÉE] dans reply"),
        (r"capability.*detect.*usage", "Capability Advisor detect_usage"),
        (r"auto.*introspection.*reply", "Auto-introspection dans réponse"),
        (r"after.*generation.*introspection", "Hook après génération")
    ]
    
    with open(ogma_file, 'r', encoding='utf-8') as f:
        content = f.read()
        
    print("\n  🔍 Recherche patterns suspects:")
    found_any = False
    
    for pattern, description in search_patterns:
        matches = re.finditer(pattern, content, re.IGNORECASE)
        match_list = list(matches)
        
        if match_list:
            found_any = True
            print(f"\n  ✅ {description}:")
            for match in match_list[:3]:  # Max 3 résultats
                line_num = content[:match.start()].count('\n') + 1
                context = content[max(0, match.start()-50):min(len(content), match.end()+50)]
                print(f"     Ligne {line_num}: ...{context.strip()}...")
    
    if not found_any:
        print("\n  ℹ️  Aucun pattern de détection post-génération trouvé")
        print("     → Le problème est probablement dans le workflow auto-déclenchée")


def recommandations():
    """Recommandations basées sur les tests"""
    print("\n" + "="*70)
    print("RECOMMANDATIONS")
    print("="*70)
    
    print("""
📋 ACTIONS INVESTIGATIVES:

1. VÉRIFIER workflow introspection auto-déclenchée
   → Regarder extensions/cognitive_mirror/introspection_core.py
   → Fonction: trigger_introspection_sync()
   → Vérifier si callbacks sont appelés correctement

2. CHERCHER détection post-génération [RÉFLEXION-STRUCTURÉE]
   → Grep dans ogma_ng.py après ligne 4600 (post-génération)
   → Vérifier si Capability Advisor a un hook actif
   → Chercher dans logic_callbacks.py

3. TESTER avec logs détaillés
   → Activer mode debug introspection
   → Tracer chaque étape du workflow auto
   → Identifier où ça s'arrête exactement

4. ANALYSER différence [auto-déclenchée] vs normale
   → Comparer les deux workflows
   → Identifier pourquoi auto s'arrête à "Dialogue en cours..."
   
HYPOTHÈSE PRINCIPALE:
L'introspection auto-déclenchée lance le workflow MAIS ne reçoit jamais
les callbacks de l'orchestrateur, créant une boîte "fantôme" qui reste
vide. Pendant ce temps, une 2ème détection (post-génération?) lance
une introspection classique qui fonctionne normalement.

SOLUTION POTENTIELLE:
Désactiver temporairement la capacité 'introspection' dans Capability
Advisor pour éviter l'injection de [RÉFLEXION-STRUCTURÉE] et confirmer
si c'est bien la source du double déclenchement.
""")


if __name__ == "__main__":
    print("\n" + "🧪 TEST INTROSPECTION AUTO-DÉCLENCHÉE 🧪".center(70))
    
    test_detection_message_utilisateur()
    test_detection_reponse_ia()
    test_workflow_complet()
    test_double_declenchement_scenario()
    analyser_code_detection()
    recommandations()
    
    print("\n" + "="*70)
    print("✅ Tests terminés - Voir recommandations ci-dessus")
    print("="*70 + "\n")
