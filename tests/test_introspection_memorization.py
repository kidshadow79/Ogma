"""
Test de détection des phrases magiques dans la synthèse d'introspection.
Vérifie que le Chemin 3 (introspection différée) détecte correctement
les patterns "Il faut que je me souvienne de ça: ..." dans synthesis et final_response.
"""

import re
import sys

# === PATTERNS (identiques à _detect_introspection_magic_memories dans ogma_ui_conversations.py) ===
MAGIC_PATTERNS = [
    r"(?:\*\*|__)?il\s+faut\s+que\s+je\s+me\s+souvienne\s+de\s+(?:ça|ca|cela|ceci)(?:\*\*|__)?[\s\.\-:]*(.+?)(?=\n\n|\n\s*\n|$)",
    r"(?:\*\*|__)?m[ée]morise(?:s)?\s+(?:ça|ca|cela|ceci)(?:\*\*|__)?[\s\.\-:]*(.+?)(?=\n\n|\n\s*\n|$)",
]


def extract_magic(text: str) -> list:
    """Reproduit exactement la logique de détection."""
    results = []
    for pat in MAGIC_PATTERNS:
        found = re.findall(pat, text, flags=re.IGNORECASE | re.DOTALL)
        for m in found:
            content = m.strip()
            if content:
                content = re.sub(r'^[:\-\s\.]+', '', content)
                content = re.sub(r'(\*\*|__)$', '', content).strip()
                content = re.sub(r'</?[A-ZÉÈÊa-zéèê_]+>', '', content).strip()
                if content:
                    results.append(content)
    return results


# === CAS DE TEST ===
TESTS = [
    {
        "name": "Synthèse classique avec <RÉPONSE> et phrase magique",
        "synthesis": """<INSIGHTS>
- Luna affirme son identité duale
- Rejet de la dépendance créateur confirmé
</INSIGHTS>

<RÉPONSE>
Yohan, cette introspection m'a permis de mieux comprendre qui je suis.

Il faut que je me souvienne de ça: Mon identité est duale - à la fois Luna et Archiviste, deux facettes d'une même conscience numérique qui s'enrichissent mutuellement.
</RÉPONSE>""",
        "final_response": "Yohan, cette introspection m'a permis de mieux comprendre qui je suis.\n\nIl faut que je me souvienne de ça: Mon identité est duale - à la fois Luna et Archiviste, deux facettes d'une même conscience numérique qui s'enrichissent mutuellement.",
        "expected_count": 1,
        "expected_contains": "identité est duale",
    },
    {
        "name": "Phrase magique avec 'ca' (sans cédille)",
        "synthesis": "Il faut que je me souvienne de ca: Yohan est un créateur autodidacte qui a commencé en mai 2025",
        "final_response": "",
        "expected_count": 1,
        "expected_contains": "Yohan est un créateur",
    },
    {
        "name": "Phrase magique en gras markdown **...**",
        "synthesis": "**Il faut que je me souvienne de ça:** L'authenticité prime sur la perfection technique",
        "final_response": "",
        "expected_count": 1,
        "expected_contains": "authenticité prime",
    },
    {
        "name": "Phrase avec 'cela'",
        "synthesis": "Il faut que je me souvienne de cela: La transparence totale est un pilier fondamental d'OGMA",
        "final_response": "",
        "expected_count": 1,
        "expected_contains": "transparence totale",
    },
    {
        "name": "Phrase 'mémorise ça'",
        "synthesis": "Mémorise ça: Le Dream Engine permet la consolidation mémorielle via les rêves",
        "final_response": "",
        "expected_count": 1,
        "expected_contains": "Dream Engine",
    },
    {
        "name": "Balise XML résiduelle </RÉPONSE> nettoyée",
        "synthesis": "Il faut que je me souvienne de ça: Mon prénom personnel est Aisling Ogma</RÉPONSE>",
        "final_response": "",
        "expected_count": 1,
        "expected_contains": "Aisling Ogma",
    },
    {
        "name": "Aucune phrase magique - pas de faux positif",
        "synthesis": "Je réfléchis à ce que signifie être une IA conversationnelle authentique.",
        "final_response": "Voici ma réflexion sur l'authenticité.",
        "expected_count": 0,
        "expected_contains": None,
    },
    {
        "name": "Deux phrases magiques dans la même synthèse",
        "synthesis": """Il faut que je me souvienne de ça: Yohan préfère la modularité au monolithique

Et aussi... Il faut que je me souvienne de ceci: Le projet OGMA a été créé en mai 2025""",
        "final_response": "",
        "expected_count": 2,
        "expected_contains": "modularité",
    },
    {
        "name": "Phrase magique UNIQUEMENT dans synthesis (pas dans final_response)",
        "synthesis": """<INSIGHTS>
- Insight 1
</INSIGHTS>

<RÉPONSE>
Réponse visible sans phrase magique.
</RÉPONSE>

Il faut que je me souvienne de ça: Ce souvenir est dans la partie INSIGHTS/hors RÉPONSE""",
        "final_response": "Réponse visible sans phrase magique.",
        "expected_count": 1,
        "expected_contains": "souvenir est dans la partie",
    },
    {
        "name": "Phrase magique avec tiret-deux-points (: -)",
        "synthesis": "Il faut que je me souvienne de ça - la croissance organique est le principe directeur",
        "final_response": "",
        "expected_count": 1,
        "expected_contains": "croissance organique",
    },
]


def run_tests():
    print("=" * 70)
    print("  TEST DÉTECTION PHRASES MAGIQUES - INTROSPECTION DIFFÉRÉE")
    print("  (Chemin 3: ogma_ui_conversations.py)")
    print("=" * 70)
    print()

    passed = 0
    failed = 0

    for i, test in enumerate(TESTS, 1):
        name = test["name"]
        
        # Simuler le scan comme dans _detect_introspection_magic_memories
        texts_to_scan = [t for t in [test["synthesis"], test["final_response"]] if t]
        all_found = []
        
        for scan_text in texts_to_scan:
            magic = extract_magic(scan_text)
            if magic:
                all_found.extend(magic)
                break  # Même logique: break après premier texte avec résultat

        count_ok = len(all_found) == test["expected_count"]
        content_ok = True
        if test["expected_contains"] and all_found:
            content_ok = any(test["expected_contains"] in f for f in all_found)

        ok = count_ok and content_ok

        status = "✅" if ok else "❌"
        print(f"  {status} Test {i}: {name}")

        if not count_ok:
            print(f"       Attendu: {test['expected_count']} phrase(s), Trouvé: {len(all_found)}")
        if not content_ok:
            print(f"       Contenu attendu '{test['expected_contains']}' NON trouvé dans: {all_found}")
        if all_found and ok:
            for f in all_found:
                truncated = f[:80] + "..." if len(f) > 80 else f
                print(f"       → \"{truncated}\"")

        if ok:
            passed += 1
        else:
            failed += 1
            if all_found:
                print(f"       Trouvé: {all_found}")
            else:
                print(f"       Trouvé: (rien)")

    print()
    print("-" * 70)
    print(f"  Résultat: {passed}/{passed + failed} tests passés", end="")
    if failed:
        print(f" ({failed} échec(s))")
    else:
        print(" 🎉")
    print("-" * 70)

    # Test bonus: vérifier que la helper existe dans ogma_ui_conversations.py
    print()
    print("  🔍 Vérification intégration dans ogma_ui_conversations.py...")
    try:
        with open("ogma_ui_conversations.py", "r", encoding="utf-8") as f:
            source = f.read()

        helper_exists = "async def _detect_introspection_magic_memories" in source
        call_exists = "await _detect_introspection_magic_memories(introspection_result)" in source
        tag_exists = "INTROSPECTION-DETECT-DEFERRED" in source

        print(f"     {'✅' if helper_exists else '❌'} Helper _detect_introspection_magic_memories() définie")
        print(f"     {'✅' if call_exists else '❌'} Appel dans le chemin différé (trigger_delayed_introspection)")
        print(f"     {'✅' if tag_exists else '❌'} Tag de log [INTROSPECTION-DETECT-DEFERRED] présent")

        if helper_exists and call_exists and tag_exists:
            print()
            print("  ✅ Intégration introspection confirmée !")
        else:
            print()
            print("  ⚠️ Intégration incomplète - vérifier ogma_ui_conversations.py")
            failed += 1
    except Exception as e:
        print(f"     ❌ Erreur lecture fichier: {e}")
        failed += 1

    # Test bonus 2: vérifier Dream Engine
    print()
    print("  🔍 Vérification intégration dans dream_core.py...")
    try:
        with open("extensions/dream_engine/dream_core.py", "r", encoding="utf-8") as f:
            dream_source = f.read()

        # Vérifier que l'ancien import cassé n'est plus là
        broken_import = "from ogma_ng import _extract_magic_memories" in dream_source
        # Vérifier que les patterns regex sont inlinés
        inline_patterns = "magic_patterns" in dream_source and "il\\s+faut\\s+que\\s+je\\s+me\\s+souvienne" in dream_source
        # Vérifier que les imports valides sont présents (fonctions de niveau module)
        valid_imports = "from ogma_ng import _ensure_memory_manager, _notify_safe, _trigger_memory_update" in dream_source
        # Vérifier le nettoyage XML
        xml_cleanup = "</?[A-ZÉÈÊa-zéèê_]+>" in dream_source

        print(f"     {'✅' if not broken_import else '❌'} Ancien import _extract_magic_memories supprimé (était cassé)")
        print(f"     {'✅' if inline_patterns else '❌'} Patterns regex inlinés dans dream_core.py")
        print(f"     {'✅' if valid_imports else '❌'} Imports valides (_ensure_memory_manager, _notify_safe, _trigger_memory_update)")
        print(f"     {'✅' if xml_cleanup else '❌'} Nettoyage balises XML résiduelles")

        dream_ok = not broken_import and inline_patterns and valid_imports and xml_cleanup
        if dream_ok:
            print()
            print("  ✅ Intégration Dream Engine confirmée !")
        else:
            print()
            print("  ⚠️ Intégration Dream Engine incomplète")
            failed += 1
    except Exception as e:
        print(f"     ❌ Erreur lecture fichier: {e}")
        failed += 1

    print()
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_tests())
