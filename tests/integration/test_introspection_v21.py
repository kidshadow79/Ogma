# Test import extension Introspection v2.1
import sys
sys.path.insert(0, r"c:\IA\OGMA")

print("=" * 50)
print("TEST IMPORT EXTENSION INTROSPECTION v2.1")
print("=" * 50)

try:
    # Test imports individuels
    from extensions.cognitive_mirror.config_v2 import get_introspection_config, IntrospectionConfigV2
    print("✅ config_v2.py importé")
    
    from extensions.cognitive_mirror.introspection_engine import get_engine, initialize_engine, IntrospectionEngine
    print("✅ introspection_engine.py importé")
    
    from extensions.cognitive_mirror.ui_parameters_v2 import IntrospectionParametersUI
    print("✅ ui_parameters_v2.py importé")
    
    # Test import __init__
    from extensions.cognitive_mirror import (
        initialize_introspection,
        is_v21,
        is_available,
        is_enabled,
        get_introspection_config,
        check_magic_phrases
    )
    print("✅ __init__.py importé")
    
    # Test configuration
    config = get_introspection_config()
    print(f"\n📋 Configuration v2.1:")
    print(f"   - Extension activée: {config.is_enabled()}")
    print(f"   - Mode: {config.get_introspection_mode()}")
    print(f"   - Step1 tokens: {config.get('step1_max_tokens')}")
    
    # Test phrases magiques
    print(f"\n✨ Phrases magiques:")
    triggers = config.get_magic_phrases("user_trigger")
    print(f"   - Triggers (5 premiers): {triggers[:5]}")
    
    # Test pattern matching
    print(f"\n🔍 Test pattern matching:")
    tests = [
        ("réfléchis à cela", True),
        ("lance une introspection", True),
        ("bonjour comment vas-tu", False),
        ("peux-tu réfléchir", False),  # "réfléchir" ≠ "réfléchis"
    ]
    for text, expected in tests:
        result = config.matches_trigger_pattern(text, "user")
        status = "✅" if result == expected else "❌"
        print(f"   {status} '{text}' → {result} (attendu: {expected})")
    
    # Test parsing synthèse
    print(f"\n📊 Test parsing synthèse:")
    
    sample_response = """
<INSIGHTS>
Le dialogue m'a rappelé notre conversation passée sur les projets IA.
L'ego me dit d'être encourageant mais réaliste.
</INSIGHTS>

<RÉPONSE>
Bien sûr ! Je me souviens de notre discussion. Voici mes suggestions pour ton projet...
</RÉPONSE>

<SAVE>
{"save": true, "importance": 7, "reason": "Discussion importante sur projet IA"}
</SAVE>
"""
    
    # Créer engine temporaire pour test parsing
    engine = IntrospectionEngine.__new__(IntrospectionEngine)
    engine.config = config
    engine.session_data = {}
    
    import json, re
    result = engine._parse_synthesis_response(sample_response)
    
    print(f"   - Insights: {result['insights'][:50]}...")
    print(f"   - Réponse: {result['response'][:50]}...")
    print(f"   - Save: {result['save']}")
    print(f"   - Importance: {result['importance']}")
    print(f"   - Reason: {result['reason']}")
    
    # Vérifications
    assert result['save'] == True, "Save devrait être True"
    assert result['importance'] == 7, "Importance devrait être 7"
    assert "suggestions" in result['response'], "Réponse devrait contenir 'suggestions'"
    print("   ✅ Parsing OK!")
    
    # Test système d'erreurs explicites (Phase 4)
    print(f"\n🚨 Test erreurs explicites (Phase 4):")
    
    from extensions.cognitive_mirror.introspection_engine import (
        IntrospectionError, 
        IntrospectionErrorType
    )
    
    # Créer erreur test
    error = IntrospectionError(
        error_type=IntrospectionErrorType.TIMEOUT,
        message="Test timeout",
        step=2,
        role="conscious",
        details="Timeout après 60s",
        recoverable=True
    )
    
    print(f"   - Type: {error.error_type.value}")
    print(f"   - Message utilisateur: {error.user_message()}")
    print(f"   - Recoverable: {error.recoverable}")
    
    error_dict = error.to_dict()
    assert error_dict['error_type'] == 'timeout', "Type devrait être timeout"
    assert error_dict['recoverable'] == True, "Devrait être recoverable"
    print("   ✅ Erreurs explicites OK!")
    
    # Test couleur erreur UI
    from extensions.cognitive_mirror.ui_introspection_display import COLORS
    assert 'error' in COLORS, "Couleur erreur devrait exister"
    print(f"   - Couleur erreur: {COLORS['error']}")
    print("   ✅ UI erreur OK!")
    
    print("\n" + "=" * 50)
    print("✅ TOUS LES TESTS RÉUSSIS!")
    print("=" * 50)
    
except Exception as e:
    print(f"\n❌ ERREUR: {e}")
    import traceback
    traceback.print_exc()
