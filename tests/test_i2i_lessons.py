"""
TEST 3 - Système de leçons persistantes i2i
Tests pour: I2ILessonsManager (stockage, retrieval, stats, injection)
"""
import sys
import os
import tempfile
import json
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ═══════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════

def get_temp_manager():
    """Crée un manager avec DB temporaire."""
    from modules.logic.i2i_lessons import I2ILessonsManager
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_lessons.db"
    return I2ILessonsManager(db_path=db_path)


# ═══════════════════════════════════════
# TESTS
# ═══════════════════════════════════════

def test_db_initialization():
    """Test: la DB se crée correctement."""
    mgr = get_temp_manager()
    assert mgr.db_path.exists(), "DB file should exist"
    
    # Vérifier les tables
    conn = mgr._get_conn()
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    table_names = {t['name'] for t in tables}
    assert 'lessons' in table_names
    assert 'lesson_stats' in table_names
    
    mgr.close()
    print("[TEST] ✅ test_db_initialization PASS")


def test_store_lesson():
    """Test: stockage d'une leçon basique."""
    mgr = get_temp_manager()
    
    lesson_id = mgr.store_lesson(
        error_type='anatomie',
        severity='critique',
        original_prompt='A woman standing in a garden',
        corrected_prompt='A woman with five fingers on each hand standing in a garden',
        score_before=3,
        score_after=7,
        defects=[{
            'type': 'anatomie',
            'gravite': 'critique',
            'description': '6 doigts main droite',
            'zone': 'main droite'
        }],
        context='Test unitaire'
    )
    
    assert lesson_id > 0
    
    # Vérifier en DB
    conn = mgr._get_conn()
    row = conn.execute("SELECT * FROM lessons WHERE id = ?", (lesson_id,)).fetchone()
    assert row is not None
    assert row['error_type'] == 'anatomie'
    assert row['severity'] == 'critique'
    assert row['score_before'] == 3
    assert row['score_after'] == 7
    assert row['score_gain'] == 4  # Colonne calculée
    assert 'woman' in row['keywords'] or 'garden' in row['keywords'] or 'fingers' in row['keywords']
    
    mgr.close()
    print("[TEST] ✅ test_store_lesson PASS")


def test_store_lessons_from_correction():
    """Test: extraction de leçons depuis une session de correction."""
    mgr = get_temp_manager()
    
    analysis_history = [
        {
            'attempt': 1,
            'prompt': 'A cat sitting on a chair',
            'score': 3,
            'defauts_detectes': [
                {'type': 'proportion', 'gravite': 'majeur', 'description': 'Chat trop grand', 'zone': 'corps'}
            ]
        },
        {
            'attempt': 2,
            'prompt': 'A small cat sitting proportionally on a chair',
            'score': 7,
            'defauts_detectes': []
        }
    ]
    
    prompt_history = [
        'A cat sitting on a chair',
        'A small cat sitting proportionally on a chair'
    ]
    
    lesson_ids = mgr.store_lessons_from_correction(analysis_history, prompt_history)
    
    assert len(lesson_ids) == 1, f"Expected 1 lesson, got {len(lesson_ids)}"
    
    # Vérifier la leçon
    conn = mgr._get_conn()
    row = conn.execute("SELECT * FROM lessons WHERE id = ?", (lesson_ids[0],)).fetchone()
    assert row['error_type'] == 'proportion'
    assert row['score_gain'] == 4  # 7 - 3
    
    mgr.close()
    print("[TEST] ✅ test_store_lessons_from_correction PASS")


def test_no_lesson_if_no_improvement():
    """Test: pas de leçon si score ne s'améliore pas."""
    mgr = get_temp_manager()
    
    analysis_history = [
        {'attempt': 1, 'score': 5, 'defauts_detectes': [{'type': 'artefact', 'gravite': 'mineur', 'description': 'bruit'}]},
        {'attempt': 2, 'score': 4, 'defauts_detectes': []}  # Régression
    ]
    prompt_history = ['prompt A', 'prompt B']
    
    lesson_ids = mgr.store_lessons_from_correction(analysis_history, prompt_history)
    assert len(lesson_ids) == 0, "No lesson should be stored on regression"
    
    mgr.close()
    print("[TEST] ✅ test_no_lesson_if_no_improvement PASS")


def test_single_attempt_no_lesson():
    """Test: pas de leçon avec une seule tentative."""
    mgr = get_temp_manager()
    
    lesson_ids = mgr.store_lessons_from_correction(
        [{'attempt': 1, 'score': 8}],
        ['prompt A']
    )
    assert len(lesson_ids) == 0
    
    mgr.close()
    print("[TEST] ✅ test_single_attempt_no_lesson PASS")


def test_find_relevant_lessons():
    """Test: recherche de leçons pertinentes par mots-clés."""
    mgr = get_temp_manager()
    
    # Stocker des leçons variées
    mgr.store_lesson('anatomie', 'critique', 'woman hands fingers', 'woman five fingers each hand', 3, 8)
    mgr.store_lesson('proportion', 'majeur', 'tall building city', 'tall building proportional city', 4, 7)
    mgr.store_lesson('artefact', 'mineur', 'landscape sunset', 'landscape clean sunset', 5, 6)
    
    # Rechercher avec prompt similaire aux mains
    results = mgr.find_relevant_lessons('woman holding flowers with fingers', max_results=5)
    
    assert len(results) > 0, "Should find at least one relevant lesson"
    # La leçon "anatomie" devrait être la plus pertinente (overlap: woman, fingers)
    assert results[0]['error_type'] == 'anatomie'
    assert results[0]['score_gain'] == 5  # 8 - 3
    assert len(results[0]['keywords_overlap']) > 0
    
    mgr.close()
    print("[TEST] ✅ test_find_relevant_lessons PASS")


def test_find_no_relevant_lessons():
    """Test: pas de leçon pertinente retournée pour un prompt sans overlap."""
    mgr = get_temp_manager()
    
    mgr.store_lesson('anatomie', 'critique', 'woman hands', 'woman five fingers', 3, 8)
    
    # Rechercher avec un prompt totalement différent
    results = mgr.find_relevant_lessons('spaceship flying mars', max_results=5)
    
    assert len(results) == 0, "No lessons should match"
    
    mgr.close()
    print("[TEST] ✅ test_find_no_relevant_lessons PASS")


def test_format_lessons_for_injection():
    """Test: formatage des leçons pour injection contexte."""
    mgr = get_temp_manager()
    
    mgr.store_lesson(
        'anatomie', 'critique',
        'woman portrait', 'woman portrait five fingers',
        3, 8,
        defects=[{'type': 'anatomie', 'gravite': 'critique', 'description': '6 doigts', 'zone': 'main'}]
    )
    
    lessons = mgr.find_relevant_lessons('woman portrait close-up')
    formatted = mgr.format_lessons_for_injection(lessons)
    
    assert 'LEÇONS APPRISES' in formatted
    assert 'ANATOMIE' in formatted
    assert '+5' in formatted  # gain
    
    mgr.close()
    print("[TEST] ✅ test_format_lessons_for_injection PASS")


def test_format_empty_lessons():
    """Test: formatage vide si aucune leçon."""
    mgr = get_temp_manager()
    formatted = mgr.format_lessons_for_injection([])
    assert formatted == ""
    mgr.close()
    print("[TEST] ✅ test_format_empty_lessons PASS")


def test_error_stats():
    """Test: statistiques d'erreurs."""
    mgr = get_temp_manager()
    
    # Vide
    stats = mgr.get_error_stats()
    assert stats['total_lessons'] == 0
    
    # Ajouter des leçons
    mgr.store_lesson('anatomie', 'critique', 'p1', 'p2', 2, 7)
    mgr.store_lesson('anatomie', 'majeur', 'p3', 'p4', 3, 6)
    mgr.store_lesson('proportion', 'majeur', 'p5', 'p6', 4, 8)
    
    stats = mgr.get_error_stats()
    assert stats['total_lessons'] == 3
    assert stats['most_common_error'] == 'anatomie'
    assert stats['best_fix_gain'] == 5  # 7-2=5
    assert 'anatomie' in stats['error_types']
    assert stats['error_types']['anatomie']['count'] == 2
    
    mgr.close()
    print("[TEST] ✅ test_error_stats PASS")


def test_mark_lesson_applied():
    """Test: marquage d'une leçon comme appliquée."""
    mgr = get_temp_manager()
    
    lid = mgr.store_lesson('anatomie', 'critique', 'p1', 'p2', 3, 8)
    
    # Appliquer 3 fois
    mgr.mark_lesson_applied(lid)
    mgr.mark_lesson_applied(lid)
    mgr.mark_lesson_applied(lid)
    
    conn = mgr._get_conn()
    row = conn.execute("SELECT times_applied, last_applied_at FROM lessons WHERE id = ?", (lid,)).fetchone()
    assert row['times_applied'] == 3
    assert row['last_applied_at'] is not None
    
    mgr.close()
    print("[TEST] ✅ test_mark_lesson_applied PASS")


def test_exports():
    """Test: exports du module."""
    from modules.logic import get_lessons_manager, cleanup_lessons, I2ILessonsManager
    
    assert callable(get_lessons_manager)
    assert callable(cleanup_lessons)
    assert I2ILessonsManager is not None
    
    print("[TEST] ✅ test_exports PASS")


# ═══════════════════════════════════════
# RUNNER
# ═══════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("TEST 3 - Système de leçons persistantes i2i")
    print("=" * 60 + "\n")
    
    tests = [
        test_db_initialization,
        test_store_lesson,
        test_store_lessons_from_correction,
        test_no_lesson_if_no_improvement,
        test_single_attempt_no_lesson,
        test_find_relevant_lessons,
        test_find_no_relevant_lessons,
        test_format_lessons_for_injection,
        test_format_empty_lessons,
        test_error_stats,
        test_mark_lesson_applied,
        test_exports,
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
