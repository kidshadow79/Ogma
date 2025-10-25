"""
Test des phrases magiques Perception (IA)
Vérifie la détection et le caviarder des phrases d'activation/désactivation
par l'IA (dans ses réponses)
"""

import re
from typing import List

def _strip_magic_phrases(s: str) -> str:
    """Fonction identique à celle dans ogma_ng.py pour tester"""
    if not s:
        return s
    pattern = (
        r"(?:"
        r"il\s*faut\s*que\s*je\s*me\s*souvienne\s*de\s*(?:ça|ca)\s*[:\-]\s*.+?(?=$|\n|\r)"
        r"|m[ée]morise(?:s)?\s*(?:ça|ca)\s*[:\-]\s*.+?(?=$|\n|\r)"
        r"|il\s+faut\s+que\s+je\s+(?:te\s+)?vois"
        r"|je\s+veux\s+te\s+voir"
        r"|je\s+n'ai\s+plus\s+besoin\s+de\s+te\s+voir"
        r"|je\s+(?:peux|vais)\s+arrêter\s+de\s+te\s+(?:voir|regarder)"
        r"|je\s+ferme\s+(?:ma\s+)?vision"
        r"|je\s+coupe\s+(?:ma\s+)?caméra"
        r")"
    )
    return re.sub(pattern, "", s, flags=re.IGNORECASE).strip()

def test_activation_patterns():
    """Test des patterns d'activation IA"""
    print("\n" + "="*70)
    print("🧪 TEST PATTERNS D'ACTIVATION (RÉPONSES IA)")
    print("="*70)
    
    activation_patterns = [
        r"il\s+faut\s+que\s+je\s+(?:te\s+)?vois",
        r"je\s+veux\s+te\s+voir",
        r"il\s+faut\s+que\s+je\s+vois"
    ]
    
    test_phrases = [
        "il faut que je te vois",
        "Il faut que je te vois",
        "IL FAUT QUE JE TE VOIS",
        "je veux te voir",
        "Je veux te voir maintenant",
        "il faut que je vois",
        "il faut que je vois quelque chose",
        "Bonjour, je veux te voir aujourd'hui",
        "Salut il faut que je te vois pour discuter",
        "Pour t'aider, il faut que je vois ton écran",
        # Phrases qui NE doivent PAS matcher
        "il faut que je voie ça",
        "je veux voir le résultat",
        "tu veux me voir",
    ]
    
    for phrase in test_phrases:
        matched = any(re.search(pattern, phrase, re.IGNORECASE) for pattern in activation_patterns)
        status = "✅ DÉTECTÉ" if matched else "❌ NON DÉTECTÉ"
        print(f"{status}: \"{phrase}\"")

def test_deactivation_patterns():
    """Test des patterns de désactivation IA"""
    print("\n" + "="*70)
    print("🧪 TEST PATTERNS DE DÉSACTIVATION (RÉPONSES IA)")
    print("="*70)
    
    deactivation_patterns = [
        r"je\s+n'ai\s+plus\s+besoin\s+de\s+te\s+voir",
        r"je\s+(?:peux|vais)\s+arrêter\s+de\s+te\s+(?:voir|regarder)",
        r"je\s+ferme\s+(?:ma\s+)?vision",
        r"je\s+coupe\s+(?:ma\s+)?caméra"
    ]
    
    test_phrases = [
        "je n'ai plus besoin de te voir",
        "Je n'ai plus besoin de te voir",
        "JE N'AI PLUS BESOIN DE TE VOIR",
        "je peux arrêter de te voir",
        "je vais arrêter de te voir",
        "je peux arrêter de te regarder",
        "Je vais arrêter de te regarder maintenant",
        "je ferme vision",
        "je ferme ma vision",
        "Je ferme ma vision maintenant",
        "je coupe caméra",
        "je coupe ma caméra",
        "Je coupe ma caméra maintenant",
        # Phrases qui NE doivent PAS matcher
        "arrête de parler",
        "je vais fermer la fenêtre",
        "tu peux arrêter de me voir",
    ]
    
    for phrase in test_phrases:
        matched = any(re.search(pattern, phrase, re.IGNORECASE) for pattern in deactivation_patterns)
        status = "✅ DÉTECTÉ" if matched else "❌ NON DÉTECTÉ"
        print(f"{status}: \"{phrase}\"")

def test_stripping():
    """Test du caviarder des phrases magiques IA"""
    print("\n" + "="*70)
    print("🧪 TEST CAVIARDER (STRIP) DES PHRASES IA")
    print("="*70)
    
    test_cases = [
        ("il faut que je te vois", ""),
        ("Bonjour, il faut que je te vois aujourd'hui", "Bonjour, aujourd'hui"),
        ("je veux te voir pour t'aider", "pour t'aider"),
        ("je n'ai plus besoin de te voir maintenant", "maintenant"),
        ("je peux arrêter de te voir s'il te plaît", "s'il te plaît"),
        ("je ferme ma vision immédiatement", "immédiatement"),
        ("Salut ! je veux te voir. Comment vas-tu ?", "Salut ! . Comment vas-tu ?"),
        ("je coupe ma caméra", ""),
        ("Pour t'aider, il faut que je vois ton problème", "Pour t'aider, ton problème"),
        ("mémorise ça: test mémoire", ""),  # Autre phrase magique
        ("Texte normal sans phrase magique", "Texte normal sans phrase magique"),
    ]
    
    for original, expected in test_cases:
        result = _strip_magic_phrases(original)
        # Normaliser les espaces multiples
        result_normalized = " ".join(result.split())
        expected_normalized = " ".join(expected.split())
        
        status = "✅ OK" if result_normalized == expected_normalized else "❌ ÉCHEC"
        print(f"{status}:")
        print(f"  Original: \"{original}\"")
        print(f"  Résultat: \"{result}\"")
        print(f"  Attendu:  \"{expected}\"")
        if result_normalized != expected_normalized:
            print(f"  ⚠️ Différence détectée!")
        print()

def test_case_insensitivity():
    """Test de l'insensibilité à la casse"""
    print("\n" + "="*70)
    print("🧪 TEST INSENSIBILITÉ À LA CASSE")
    print("="*70)
    
    variations = [
        "il faut que je te vois",
        "Il Faut Que Je Te Vois",
        "IL FAUT QUE JE TE VOIS",
        "iL fAuT qUe Je Te VoIs",
        "je veux te voir",
        "JE VEUX TE VOIR",
        "Je Veux Te Voir",
        "je n'ai plus besoin de te voir",
        "JE N'AI PLUS BESOIN DE TE VOIR",
        "Je N'Ai Plus Besoin De Te Voir",
        "je peux arrêter de te voir",
        "JE PEUX ARRÊTER DE TE VOIR",
    ]
    
    for phrase in variations:
        stripped = _strip_magic_phrases(phrase)
        status = "✅ CAVIARDER" if stripped == "" else "❌ NON CAVIARDER"
        print(f"{status}: \"{phrase}\" → \"{stripped}\"")

if __name__ == "__main__":
    print("\n" + "🎯 TEST DES PHRASES MAGIQUES PERCEPTION (IA)" + "\n")
    print("Ce script teste la détection et le caviarder des phrases magiques")
    print("utilisées par l'IA dans ses réponses pour contrôler l'extension Perception.")
    
    test_activation_patterns()
    test_deactivation_patterns()
    test_stripping()
    test_case_insensitivity()
    
    print("\n" + "="*70)
    print("✅ TESTS TERMINÉS")
    print("="*70)
    print("\n💡 Pour tester en conditions réelles:")
    print("   1. Lancez OGMA: python launch_ogma.py")
    print("   2. Configurez Luna pour qu'elle utilise les phrases dans ses réponses")
    print("   3. Demandez quelque chose nécessitant vision:")
    print("      Utilisateur: 'Peux-tu m'aider avec ce que tu vois ?'")
    print("      Luna: 'Bien sûr ! il faut que je te vois pour t'aider.'")
    print("   4. Vérifiez:")
    print("      - Notification UI toast 'Perception activée par Luna'")
    print("      - Webcam démarre automatiquement")
    print("      - Logs console [PERCEPTION]")
    print("      - Phrase caviarder dans l'affichage")
    print()
    print("💡 Phrases de désactivation:")
    print("   Luna: 'C'est bon, je n'ai plus besoin de te voir maintenant.'")
    print("   → Webcam s'arrête automatiquement")
    print()
