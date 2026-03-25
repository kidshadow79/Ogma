"""
TEST 1 : Parsing JSON analyse i2i + helper vision + flags stop
================================================================
Valide que la Phase 1 (fondation) fonctionne correctement.
"""
import sys
import os
import json
import tempfile

# Ajouter le dossier racine au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_parse_json_direct():
    """JSON parfait retourne directement par le LLM."""
    from modules.logic.image_generation import _parse_i2i_analysis_json
    
    raw = json.dumps({
        "score": 8,
        "satisfaisant": True,
        "defauts_detectes": [
            {"type": "mineur", "gravite": "mineur", "description": "leger flou", "zone": "fond"}
        ],
        "elements_bien_preserves": ["pose homme", "visage"],
        "prompt_issues": [],
        "correction_suggérée": ""
    })
    
    result = _parse_i2i_analysis_json(raw)
    assert result['score'] == 8, f"Score attendu 8, obtenu {result['score']}"
    assert result['satisfaisant'] == True
    assert result['_parse_method'] == 'json_direct'
    assert len(result['defauts_detectes']) == 1
    print("  [OK] JSON direct parse correctement")


def test_parse_json_markdown_wrapped():
    """JSON entoure de ```json ... ``` (comportement frequent des LLM)."""
    from modules.logic.image_generation import _parse_i2i_analysis_json
    
    raw = """Voici mon analyse :

```json
{
  "score": 4,
  "satisfaisant": false,
  "defauts_detectes": [
    {"type": "deformation", "gravite": "critique", "description": "bras gauche deforme", "zone": "corps"}
  ],
  "elements_bien_preserves": ["fond"],
  "prompt_issues": ["description trop vague du bras"],
  "correction_suggérée": "Keep man's left arm unchanged. Add woman on his right side."
}
```

En resume, l'image a des problemes majeurs."""
    
    result = _parse_i2i_analysis_json(raw)
    assert result['score'] == 4, f"Score attendu 4, obtenu {result['score']}"
    assert result['satisfaisant'] == False
    assert result['_parse_method'] == 'json_markdown'
    assert len(result['defauts_detectes']) == 1
    assert result['defauts_detectes'][0]['gravite'] == 'critique'
    print("  [OK] JSON markdown wrapped parse correctement")


def test_parse_json_brace_extract():
    """JSON melange dans du texte sans balises markdown."""
    from modules.logic.image_generation import _parse_i2i_analysis_json
    
    raw = 'Mon analyse: {"score": 7, "satisfaisant": true, "defauts_detectes": [], "correction_suggérée": ""} voila.'
    
    result = _parse_i2i_analysis_json(raw)
    assert result['score'] == 7, f"Score attendu 7, obtenu {result['score']}"
    assert result['satisfaisant'] == True
    assert result['_parse_method'] == 'json_brace_extract'
    print("  [OK] JSON brace extract parse correctement")


def test_parse_regex_fallback():
    """JSON casse mais champs extractibles par regex."""
    from modules.logic.image_generation import _parse_i2i_analysis_json
    
    raw = '{"score": 3, "satisfaisant": false, "defauts_detectes": [INVALID], "correction_suggérée": "reformuler le prompt"}'
    
    result = _parse_i2i_analysis_json(raw)
    assert result['score'] == 3, f"Score attendu 3, obtenu {result['score']}"
    assert result['satisfaisant'] == False
    assert result['correction_suggérée'] == 'reformuler le prompt'
    assert result['_parse_method'] == 'regex_extraction'
    print("  [OK] Regex fallback fonctionne")


def test_parse_total_garbage():
    """Reponse completement inutilisable -> fallback neutre score 5."""
    from modules.logic.image_generation import _parse_i2i_analysis_json
    
    raw = "Je ne peux pas analyser cette image car elle contient du contenu inapproprie."
    
    result = _parse_i2i_analysis_json(raw)
    assert result['score'] == 5, f"Score attendu 5, obtenu {result['score']}"
    assert result['_parse_method'] == 'fallback_neutre'
    print("  [OK] Garbage -> fallback neutre (score=5)")


def test_parse_empty_and_none():
    """Reponse vide ou None -> fallback neutre."""
    from modules.logic.image_generation import _parse_i2i_analysis_json
    
    for val in [None, "", "   ", "\n"]:
        result = _parse_i2i_analysis_json(val)
        assert result['score'] == 5
        assert result['_parse_method'] == 'fallback_neutre'
    print("  [OK] None/vide -> fallback neutre")


def test_normalize_score_bounds():
    """Score borne entre 1 et 10."""
    from modules.logic.image_generation import _normalize_analysis
    
    # Score trop haut
    result = _normalize_analysis({"score": 15})
    assert result['score'] == 10, f"Score attendu 10, obtenu {result['score']}"
    
    # Score trop bas
    result = _normalize_analysis({"score": -3})
    assert result['score'] == 1, f"Score attendu 1, obtenu {result['score']}"
    
    # Score non-numerique
    result = _normalize_analysis({"score": "huit"})
    assert result['score'] == 5, f"Score attendu 5, obtenu {result['score']}"
    
    # Float arrondi
    result = _normalize_analysis({"score": 7.8})
    assert result['score'] == 7, f"Score attendu 7, obtenu {result['score']}"
    
    print("  [OK] Normalisation score fonctionne (bornes, types)")


def test_prepare_image_for_vision():
    """Helper vision cree un base64 valide depuis une image temporaire."""
    from modules.logic.image_generation import _prepare_image_for_vision
    
    # Creer une image test temporaire
    try:
        from PIL import Image
    except ImportError:
        print("  [SKIP] PIL non disponible")
        return
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        tmp_path = f.name
        img = Image.new('RGB', (1200, 900), color=(100, 150, 200))
        img.save(f, format='PNG')
    
    try:
        # Test avec resize
        b64 = _prepare_image_for_vision(tmp_path, target_size=800, log_prefix="[TEST]")
        assert b64 is not None, "base64 ne devrait pas etre None"
        assert len(b64) > 100, "base64 trop court"
        
        # Verifier que c'est du base64 valide
        import base64
        decoded = base64.b64decode(b64)
        assert len(decoded) > 0, "decoded vide"
        
        # Test avec image inexistante
        b64_none = _prepare_image_for_vision("/chemin/inexistant.png", log_prefix="[TEST]")
        assert b64_none is None, "Devrait retourner None pour chemin inexistant"
        
        print("  [OK] _prepare_image_for_vision fonctionne (resize + base64 + fallback)")
    finally:
        os.unlink(tmp_path)


def test_i2i_stop_flags():
    """Flags d'interruption de la boucle corrective."""
    from modules.logic.image_generation import (
        request_i2i_stop, reset_i2i_stop, is_i2i_stop_requested
    )
    
    # Etat initial
    reset_i2i_stop()
    assert not is_i2i_stop_requested(), "Flag devrait etre False apres reset"
    
    # Demander stop
    request_i2i_stop()
    assert is_i2i_stop_requested(), "Flag devrait etre True apres request"
    
    # Re-reset
    reset_i2i_stop()
    assert not is_i2i_stop_requested(), "Flag devrait etre False apres re-reset"
    
    print("  [OK] Flags stop i2i fonctionnent")


def test_defaults_config_present():
    """Verifie que les nouveaux defaults sont dans ogma_image_config.py."""
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ogma_image_config.py')
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    assert 'i2i_autocorrect_enabled' in content, "i2i_autocorrect_enabled manquant dans defaults"
    assert 'i2i_max_retries' in content, "i2i_max_retries manquant dans defaults"
    assert 'i2i_score_threshold' in content, "i2i_score_threshold manquant dans defaults"
    assert 'i2i_analysis_prompt' in content, "i2i_analysis_prompt manquant dans defaults"
    assert 'CHECKLIST' in content, "Checklist manquante dans le prompt d'analyse"
    
    print("  [OK] Defaults config presents dans ogma_image_config.py")


def test_exports_init():
    """Verifie que les nouvelles fonctions sont exportees dans __init__.py."""
    from modules.logic import (
        analyze_i2i_result,
        request_i2i_stop,
        reset_i2i_stop,
        is_i2i_stop_requested,
        _parse_i2i_analysis_json,
        _prepare_image_for_vision,
    )
    
    assert callable(analyze_i2i_result)
    assert callable(request_i2i_stop)
    assert callable(reset_i2i_stop)
    assert callable(is_i2i_stop_requested)
    assert callable(_parse_i2i_analysis_json)
    assert callable(_prepare_image_for_vision)
    
    print("  [OK] Tous les exports fonctionnent")


if __name__ == "__main__":
    print("=" * 60)
    print("TEST 1 : Parsing JSON analyse i2i + Vision helper + Flags")
    print("=" * 60)
    
    tests = [
        test_parse_json_direct,
        test_parse_json_markdown_wrapped,
        test_parse_json_brace_extract,
        test_parse_regex_fallback,
        test_parse_total_garbage,
        test_parse_empty_and_none,
        test_normalize_score_bounds,
        test_prepare_image_for_vision,
        test_i2i_stop_flags,
        test_defaults_config_present,
        test_exports_init,
    ]
    
    passed = 0
    failed = 0
    
    for test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {test_fn.__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print(f"\n{'=' * 60}")
    print(f"RESULTAT : {passed} passed, {failed} failed / {len(tests)} total")
    print(f"{'=' * 60}")
    
    if failed > 0:
        sys.exit(1)
    else:
        print("TEST 1 PASSE !")
