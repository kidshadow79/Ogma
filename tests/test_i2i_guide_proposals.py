"""
TEST 4 - Cycle complet e2e : Propositions guide + Versioning + Anti-régression
"""
import sys
import os
import asyncio
import tempfile
import json
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ═══════════════════════════════════════
# MOCKS
# ═══════════════════════════════════════

class MockChatController:
    def __init__(self, responses=None):
        self.responses = responses or []
        self.call_count = 0
    
    async def call_chat_api(self, messages, max_tokens=500, temperature=0.4, is_json=False, context_length=None):
        response = None
        if self.call_count < len(self.responses):
            response = self.responses[self.call_count]
        self.call_count += 1
        if response is None:
            return None, "Mock: pas de réponse"
        return response, None


class MockSettingsManager:
    def __init__(self, img_config=None):
        self.settings = {
            'image_generation': img_config or {
                'img2img_guide': 'GARDE: elements importants\nSUPPRIME: elements inutiles\nCHANGE: modifications',
                'i2i_autocorrect_enabled': True,
                'i2i_max_retries': 3,
                'i2i_score_threshold': 6,
            }
        }
        self._saved = False
    
    def save_settings(self):
        self._saved = True


def get_temp_manager():
    from modules.logic.i2i_lessons import I2ILessonsManager
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_lessons.db"
    return I2ILessonsManager(db_path=db_path)


# ═══════════════════════════════════════
# TESTS
# ═══════════════════════════════════════

def test_guide_proposals_table():
    """Test: la table guide_proposals existe."""
    mgr = get_temp_manager()
    conn = mgr._get_conn()
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    table_names = {t['name'] for t in tables}
    assert 'guide_proposals' in table_names
    mgr.close()
    print("[TEST] ✅ test_guide_proposals_table PASS")


def test_should_propose_not_enough_lessons():
    """Test: pas de proposition si pas assez de leçons."""
    mgr = get_temp_manager()
    assert not mgr.should_propose_guide_update(min_lessons=5)
    
    # Ajouter 3 leçons (pas assez)
    for i in range(3):
        mgr.store_lesson('anatomie', 'critique', f'prompt {i}', f'fixed {i}', 3, 7)
    
    assert not mgr.should_propose_guide_update(min_lessons=5)
    mgr.close()
    print("[TEST] ✅ test_should_propose_not_enough_lessons PASS")


def test_should_propose_enough_lessons():
    """Test: proposition possible avec assez de leçons récurrentes."""
    mgr = get_temp_manager()
    
    # 5 leçons avec erreurs récurrentes (anatomie x3, proportion x2)
    mgr.store_lesson('anatomie', 'critique', 'p1', 'f1', 2, 7)
    mgr.store_lesson('anatomie', 'critique', 'p2', 'f2', 3, 8)
    mgr.store_lesson('anatomie', 'majeur', 'p3', 'f3', 4, 7)
    mgr.store_lesson('proportion', 'majeur', 'p4', 'f4', 3, 6)
    mgr.store_lesson('proportion', 'mineur', 'p5', 'f5', 5, 7)
    
    assert mgr.should_propose_guide_update(min_lessons=5)
    mgr.close()
    print("[TEST] ✅ test_should_propose_enough_lessons PASS")


def test_should_not_propose_if_pending_exists():
    """Test: pas de nouvelle proposition s'il y en a déjà une en attente."""
    mgr = get_temp_manager()
    
    for i in range(6):
        mgr.store_lesson('anatomie', 'critique', f'p{i}', f'f{i}', 2, 8)
    
    assert mgr.should_propose_guide_update(min_lessons=5)
    
    # Simuler une proposition pending
    conn = mgr._get_conn()
    conn.execute("""
        INSERT INTO guide_proposals (status, proposal_text, reason, based_on_lessons, current_guide_snapshot)
        VALUES ('pending', 'test', 'test reason', '[]', 'old guide')
    """)
    conn.commit()
    
    assert not mgr.should_propose_guide_update(min_lessons=5)
    mgr.close()
    print("[TEST] ✅ test_should_not_propose_if_pending_exists PASS")


def test_lessons_summary():
    """Test: résumé des leçons pour la proposition."""
    mgr = get_temp_manager()
    
    mgr.store_lesson('anatomie', 'critique', 'woman hands flowers', 'woman five fingers', 2, 8)
    mgr.store_lesson('anatomie', 'majeur', 'person waving', 'person five fingers waving', 3, 7)
    mgr.store_lesson('proportion', 'majeur', 'tall building', 'proportional building', 4, 7)
    
    summary = mgr.get_lessons_summary_for_guide()
    
    assert 'ERREURS RÉCURRENTES' in summary
    assert 'MEILLEURES CORRECTIONS' in summary
    assert 'ANATOMIE' in summary or 'anatomie' in summary
    
    mgr.close()
    print("[TEST] ✅ test_lessons_summary PASS")


def test_generate_guide_proposal():
    """Test: génération de proposition via IA mock."""
    mgr = get_temp_manager()
    
    for i in range(6):
        mgr.store_lesson('anatomie', 'critique', f'woman p{i}', f'woman fixed {i}', 2, 8)
    
    mock_ctrl = MockChatController(responses=[
        json.dumps({
            "raison": "Erreurs anatomiques récurrentes sur les mains",
            "nouvelles_regles": [
                "Toujours spécifier 'five fingers on each hand' dans les prompts",
                "Ajouter 'anatomically correct' pour les personnages"
            ]
        })
    ])
    
    result = asyncio.run(mgr.generate_guide_proposal(
        chat_controller=mock_ctrl,
        current_guide="GARDE: elements existants"
    ))
    
    assert result is not None
    assert result['id'] > 0
    assert 'five fingers' in result['proposal_text']
    assert len(result['nouvelles_regles']) == 2
    assert mock_ctrl.call_count == 1
    
    # Vérifier inscription en DB
    proposals = mgr.get_pending_proposals()
    assert len(proposals) == 1
    assert proposals[0]['id'] == result['id']
    
    mgr.close()
    print("[TEST] ✅ test_generate_guide_proposal PASS")


def test_approve_proposal():
    """Test: approbation d'une proposition."""
    mgr = get_temp_manager()
    
    # Insérer manuellement une proposition
    conn = mgr._get_conn()
    conn.execute("""
        INSERT INTO guide_proposals (status, proposal_text, reason, based_on_lessons, current_guide_snapshot)
        VALUES ('pending', '- Nouvelle règle 1\n- Nouvelle règle 2', 'Test raison', '[]', 'old guide')
    """)
    conn.commit()
    
    # Approuver
    text = mgr.approve_proposal(1)
    assert text is not None
    assert 'Nouvelle règle 1' in text
    
    # Vérifier statut
    row = conn.execute("SELECT status, applied_at FROM guide_proposals WHERE id = 1").fetchone()
    assert row['status'] == 'approved'
    assert row['applied_at'] is not None
    
    # Plus de propositions pending
    assert len(mgr.get_pending_proposals()) == 0
    
    mgr.close()
    print("[TEST] ✅ test_approve_proposal PASS")


def test_reject_proposal():
    """Test: rejet d'une proposition."""
    mgr = get_temp_manager()
    
    conn = mgr._get_conn()
    conn.execute("""
        INSERT INTO guide_proposals (status, proposal_text, reason, based_on_lessons, current_guide_snapshot)
        VALUES ('pending', '- Règle rejetée', 'Bad raison', '[]', 'old guide')
    """)
    conn.commit()
    
    mgr.reject_proposal(1)
    
    row = conn.execute("SELECT status FROM guide_proposals WHERE id = 1").fetchone()
    assert row['status'] == 'rejected'
    
    mgr.close()
    print("[TEST] ✅ test_reject_proposal PASS")


def test_apply_proposal_to_guide():
    """Test: application d'une proposition au guide settings."""
    mgr = get_temp_manager()
    mock_sm = MockSettingsManager()
    
    conn = mgr._get_conn()
    conn.execute("""
        INSERT INTO guide_proposals (status, proposal_text, reason, based_on_lessons, current_guide_snapshot)
        VALUES ('pending', '- Toujours spécifier anatomie\n- Vérifier proportions', 'Erreurs récurrentes', '[]', 'old')
    """)
    conn.commit()
    
    new_guide = mgr.apply_proposal_to_guide(1, mock_sm)
    
    assert new_guide is not None
    assert 'GARDE:' in new_guide  # Ancien contenu préservé
    assert 'RÈGLES AUTO-APPRISES' in new_guide  # Nouveau séparateur
    assert 'Toujours spécifier anatomie' in new_guide  # Nouvelle règle
    assert mock_sm._saved  # Settings sauvegardées
    
    # Vérifier que settings est à jour
    assert mock_sm.settings['image_generation']['img2img_guide'] == new_guide
    
    mgr.close()
    print("[TEST] ✅ test_apply_proposal_to_guide PASS")


def test_guide_history():
    """Test: historique des modifications du guide."""
    mgr = get_temp_manager()
    
    conn = mgr._get_conn()
    for i in range(3):
        conn.execute("""
            INSERT INTO guide_proposals (status, proposal_text, reason, based_on_lessons, current_guide_snapshot)
            VALUES (?, ?, ?, '[]', 'guide')
        """, (
            ['approved', 'rejected', 'pending'][i],
            f'rule {i}',
            f'reason {i}'
        ))
    conn.commit()
    
    history = mgr.get_guide_history()
    assert len(history) == 3
    # Vérifier que tous les statuts sont présents
    statuses = {h['status'] for h in history}
    assert statuses == {'approved', 'rejected', 'pending'}
    
    mgr.close()
    print("[TEST] ✅ test_guide_history PASS")


def test_pipeline_guide_proposal_integration():
    """Test: vérifier l'intégration de la proposition dans le pipeline."""
    pipeline_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'modules', 'logic', 'image_generation.py'
    )
    
    with open(pipeline_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifier les éléments de la boucle corrective
    assert 'guide_proposal' in content
    assert 'generate_guide_proposal' in content
    assert 'should_propose_guide_update' in content
    
    # Vérifier la notification dans le replacement
    assert 'Proposition d' in content or 'proposition' in content.lower()
    
    print("[TEST] ✅ test_pipeline_guide_proposal_integration PASS")


def test_full_anti_regression():
    """Test: anti-régression - tous les imports fonctionnent."""
    from modules.logic import (
        # Phase 1
        analyze_i2i_result,
        _parse_i2i_analysis_json,
        _prepare_image_for_vision,
        # Phase 2
        request_i2i_stop,
        reset_i2i_stop,
        is_i2i_stop_requested,
        refine_i2i_prompt,
        generate_img2img_with_correction,
        # Phase 3
        get_lessons_manager,
        cleanup_lessons,
        I2ILessonsManager,
        # Pipeline
        process_image_generation,
        process_img2img_generation,
    )
    
    # Tout est callable
    for fn in [analyze_i2i_result, _parse_i2i_analysis_json, _prepare_image_for_vision,
               request_i2i_stop, reset_i2i_stop, is_i2i_stop_requested,
               refine_i2i_prompt, generate_img2img_with_correction,
               get_lessons_manager, cleanup_lessons,
               process_image_generation, process_img2img_generation]:
        assert callable(fn), f"{fn} not callable"
    
    assert I2ILessonsManager is not None
    
    print("[TEST] ✅ test_full_anti_regression PASS")


# ═══════════════════════════════════════
# RUNNER
# ═══════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TEST 4 - Cycle complet e2e")
    print("=" * 60 + "\n")
    
    tests = [
        test_guide_proposals_table,
        test_should_propose_not_enough_lessons,
        test_should_propose_enough_lessons,
        test_should_not_propose_if_pending_exists,
        test_lessons_summary,
        test_generate_guide_proposal,
        test_approve_proposal,
        test_reject_proposal,
        test_apply_proposal_to_guide,
        test_guide_history,
        test_pipeline_guide_proposal_integration,
        test_full_anti_regression,
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
