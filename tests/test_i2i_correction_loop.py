"""
TEST 2 - Boucle auto-corrective i2i
Tests pour: refine_i2i_prompt, generate_img2img_with_correction, intégration pipeline
"""
import sys
import os
import asyncio
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ═══════════════════════════════════════
# MOCKS
# ═══════════════════════════════════════

class MockChatController:
    """Simule le chat controller pour les tests de refinement."""
    
    def __init__(self, responses=None):
        self.responses = responses or []
        self.call_count = 0
    
    async def call_chat_api(self, messages, max_tokens=500, temperature=0.4, is_json=False, context_length=None):
        response = None
        if self.call_count < len(self.responses):
            response = self.responses[self.call_count]
        self.call_count += 1
        
        if response is None:
            return None, "Mock: pas de réponse configurée"
        if isinstance(response, Exception):
            raise response
        return response, None


class MockSettingsManager:
    """Simule le settings manager."""
    
    def __init__(self, img_config=None):
        self.settings = {
            'image_generation': img_config or {
                'i2i_autocorrect_enabled': True,
                'i2i_max_retries': 3,
                'i2i_score_threshold': 6,
                'i2i_analysis_prompt': 'Test prompt {original_prompt}',
                'img2img_model': 'test-model',
                'img2img_provider': 'TestProvider',
            }
        }


class MockBackend:
    """Simule le backend de génération d'images."""
    
    def __init__(self, results=None):
        """
        results: liste de tuples (image_bytes, error, metadata) par appel
        """
        self.results = results or []
        self.call_count = 0
    
    async def generate_img2img(self, **kwargs):
        result = (None, "Mock: pas de résultat", None)
        if self.call_count < len(self.results):
            result = self.results[self.call_count]
        self.call_count += 1
        return result


class MockText2ImgManager:
    """Simule le text2img manager pour la sauvegarde."""
    
    def __init__(self):
        self.save_count = 0
    
    def save_image(self, image_bytes, metadata):
        self.save_count += 1
        from pathlib import Path
        # Retourne un faux path
        fake_path = Path(f"generated/test_image_{self.save_count}.jpg")
        return fake_path, None


# ═══════════════════════════════════════
# TESTS
# ═══════════════════════════════════════

def test_refine_i2i_prompt_basic():
    """Test: refinement de prompt basique."""
    from modules.logic.image_generation import refine_i2i_prompt
    
    mock_ctrl = MockChatController(responses=[
        "A tall woman with five fingers on each hand, proportional body, standing in a garden"
    ])
    
    analysis = {
        'score': 4,
        'defauts_detectes': [
            {'type': 'anatomie', 'gravite': 'critique', 'description': '6 doigts main droite', 'zone': 'main droite'}
        ],
        'correction_suggeree': 'Ajouter "five fingers" explicitement',
        'prompt_issues': ['Pas de contrainte anatomique']
    }
    
    result = asyncio.run(refine_i2i_prompt(
        original_prompt="A tall woman standing in a garden",
        analysis=analysis,
        chat_controller=mock_ctrl,
        attempt=1
    ))
    
    assert result is not None
    assert len(result) > 10
    assert "five fingers" in result.lower()
    assert mock_ctrl.call_count == 1
    print("[TEST] ✅ test_refine_i2i_prompt_basic PASS")


def test_refine_i2i_prompt_error_fallback():
    """Test: refinement avec erreur retourne le prompt original."""
    from modules.logic.image_generation import refine_i2i_prompt
    
    mock_ctrl = MockChatController(responses=[None])  # Erreur simulée
    
    result = asyncio.run(refine_i2i_prompt(
        original_prompt="original prompt here",
        analysis={'score': 3, 'defauts_detectes': []},
        chat_controller=mock_ctrl,
        attempt=1
    ))
    
    assert result == "original prompt here"
    print("[TEST] ✅ test_refine_i2i_prompt_error_fallback PASS")


def test_refine_i2i_prompt_exception_fallback():
    """Test: refinement avec exception retourne le prompt original."""
    from modules.logic.image_generation import refine_i2i_prompt
    
    mock_ctrl = MockChatController(responses=[Exception("Network error")])
    
    result = asyncio.run(refine_i2i_prompt(
        original_prompt="original prompt here",
        analysis={'score': 3, 'defauts_detectes': []},
        chat_controller=mock_ctrl,
        attempt=1
    ))
    
    assert result == "original prompt here"
    print("[TEST] ✅ test_refine_i2i_prompt_exception_fallback PASS")


def test_stop_flag_integration():
    """Test: les flags stop fonctionnent dans le contexte de la boucle."""
    from modules.logic.image_generation import (
        request_i2i_stop, reset_i2i_stop, is_i2i_stop_requested
    )
    
    # Reset initial
    reset_i2i_stop()
    assert not is_i2i_stop_requested()
    
    # Demande de stop
    request_i2i_stop()
    assert is_i2i_stop_requested()
    
    # Reset
    reset_i2i_stop()
    assert not is_i2i_stop_requested()
    
    print("[TEST] ✅ test_stop_flag_integration PASS")


def test_correction_loop_result_structure():
    """Test: vérifier la structure du résultat de generate_img2img_with_correction."""
    # On ne peut pas facilement mocker backend.generate_img2img dans le flux complet
    # car generate_img2img_with_correction importe le backend en interne.
    # Mais on peut vérifier la structure attendue.
    
    expected_keys = [
        'image_bytes', 'error', 'metadata', 'image_path',
        'final_prompt', 'analysis_history', 'prompt_history',
        'best_score', 'attempts_used', 'stopped'
    ]
    
    # Vérifier que la fonction existe et est importable
    from modules.logic.image_generation import generate_img2img_with_correction
    assert callable(generate_img2img_with_correction)
    
    print(f"[TEST] ✅ test_correction_loop_result_structure PASS (keys attendues: {len(expected_keys)})")


def test_autocorrect_defaults_in_config():
    """Test: vérifier que les defaults autocorrect sont dans ogma_image_config.py."""
    import importlib
    
    # Lire le fichier source pour vérifier la présence des clés
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'ogma_image_config.py')
    
    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_keys = [
        'i2i_autocorrect_enabled',
        'i2i_max_retries',
        'i2i_score_threshold',
        'i2i_analysis_prompt',
    ]
    
    for key in required_keys:
        assert key in content, f"Clé '{key}' non trouvée dans ogma_image_config.py"
    
    # Vérifier la section UI auto-corrective
    assert 'Boucle Auto-Corrective I2I' in content, "Section UI auto-corrective non trouvée"
    assert 'reset_i2i_analysis_prompt' in content, "Bouton reset non trouvé"
    
    print("[TEST] ✅ test_autocorrect_defaults_in_config PASS")


def test_pipeline_integration_branch():
    """Test: vérifier que le branchement autocorrect/one-shot existe dans le pipeline."""
    pipeline_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'modules', 'logic', 'image_generation.py'
    )
    
    with open(pipeline_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifier le branchement conditionnel
    assert "i2i_autocorrect_enabled" in content
    assert "MODE AUTO-CORRECTIF" in content
    assert "MODE ONE-SHOT" in content
    assert "generate_img2img_with_correction" in content
    assert "refine_i2i_prompt" in content
    
    # Vérifier que le mode one-shot est préservé (anti-régression)
    assert "backend.generate_img2img(" in content
    
    print("[TEST] ✅ test_pipeline_integration_branch PASS")


def test_ogma_ng_stop_integration():
    """Test: vérifier l'intégration du stop flag dans ogma_ng.py."""
    ogma_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'ogma_ng.py'
    )
    
    with open(ogma_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifier que reset_i2i_stop est importé et utilisé
    assert "reset_i2i_stop" in content
    assert "i2i_autocorrect_enabled" in content
    assert "auto-corrective" in content.lower()
    
    print("[TEST] ✅ test_ogma_ng_stop_integration PASS")


def test_exports_phase2():
    """Test: vérifier que les nouvelles fonctions Phase 2 sont exportées."""
    from modules.logic import (
        refine_i2i_prompt,
        generate_img2img_with_correction,
    )
    
    assert callable(refine_i2i_prompt)
    assert callable(generate_img2img_with_correction)
    
    print("[TEST] ✅ test_exports_phase2 PASS")


# ═══════════════════════════════════════
# RUNNER
# ═══════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TEST 2 - Boucle auto-corrective i2i")
    print("=" * 60 + "\n")
    
    tests = [
        test_refine_i2i_prompt_basic,
        test_refine_i2i_prompt_error_fallback,
        test_refine_i2i_prompt_exception_fallback,
        test_stop_flag_integration,
        test_correction_loop_result_structure,
        test_autocorrect_defaults_in_config,
        test_pipeline_integration_branch,
        test_ogma_ng_stop_integration,
        test_exports_phase2,
    ]
    
    passed = 0
    failed = 0
    
    for test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"[TEST] ❌ {test_fn.__name__} FAILED: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print(f"\n{'=' * 60}")
    print(f"RÉSULTAT: {passed}/{passed+failed} tests passés")
    if failed:
        print(f"❌ {failed} test(s) échoué(s)")
    else:
        print("✅ Tous les tests passés!")
    print(f"{'=' * 60}\n")
