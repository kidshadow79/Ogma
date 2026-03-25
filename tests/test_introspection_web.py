"""
Test de l'intégration Web Search dans l'introspection
"""
import asyncio
import re

def test_web_detection():
    """Test des patterns de détection de recherche web"""
    
    test_cases = [
        ("il faut que je cherche sur internet : théories conscience IA", True),
        ("/web émergence conscience artificielle", True),
        ("Je vais faire une recherche web : philosophie conscience", True),
        ("Cherchons sur internet les dernières découvertes", True),
        ("Je ne sais pas trop, peut-être qu'on devrait...", False),
        ("Les souvenirs montrent que...", False),
    ]
    
    web_patterns = [
        r"il faut que je cherche sur internet\s*[:]*\s*(.+?)(?:\n|$)",
        r"/web\s+(.+?)(?:\n|$)",
        r"recherche web\s*[:]*\s*(.+?)(?:\n|$)",
        r"cherchons sur internet\s*[:]*\s*(.+?)(?:\n|$)",
    ]
    
    print("🧪 TEST DÉTECTION RECHERCHE WEB\n")
    
    for text, should_match in test_cases:
        detected = False
        query = None
        
        for pattern in web_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                detected = True
                query = match.group(1).strip()
                break
        
        status = "✅" if detected == should_match else "❌"
        print(f"{status} '{text[:50]}...'")
        if query:
            print(f"   → Query: '{query}'")
    
    print("\n✨ Tests terminés")

if __name__ == "__main__":
    test_web_detection()
