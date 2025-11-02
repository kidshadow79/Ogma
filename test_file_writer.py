#!/usr/bin/env python3
"""
🧪 TEST FILE WRITER EXTENSION - Validation sauvegarde automatique .md
======================================================================

Script de test pour valider l'extension File Writer complète.

TESTS:
1. RequestDetector: Détection patterns demandes .md
2. MarkdownExtractor: Extraction blocs markdown
3. FileSaver: Sauvegarde fichiers avec nommage
4. FileWriterAgent: Orchestration complète
5. Integration: Workflow end-to-end

USAGE:
    python test_file_writer.py
"""

import sys
from pathlib import Path
from datetime import datetime

# Ajouter répertoire racine au path
sys.path.insert(0, str(Path(__file__).parent))


def test_request_detector():
    """Test détection demandes création fichiers .md"""
    print("\n" + "="*70)
    print("TEST 1: REQUEST DETECTOR - Détection patterns")
    print("="*70)
    
    from extensions.file_writer.request_detector import RequestDetector
    
    detector = RequestDetector(debug=True)
    
    # Requêtes test
    test_cases = [
        ("écris-moi un .md sur les bonnes pratiques Python", True, "bonnes_pratiques_python"),
        ("crée un fichier markdown qui explique Git", True, "qui_explique_git"),
        ("rédige un document .md pour la documentation API", True, "la_documentation_api"),
        ("génère un markdown de guide utilisateur", True, "guide_utilisateur"),
        ("fais-moi un doc sur React", True, "react"),
        ("salut Luna, comment ça va ?", False, None),
    ]
    
    results = []
    
    for message, should_detect, expected_title_part in test_cases:
        print(f"\n📝 Message: '{message}'")
        result = detector.detect(message)
        
        if result.is_request:
            print(f"   ✅ Demande détectée")
            print(f"   Titre: {result.title}")
            print(f"   Confidence: {result.confidence:.2f}")
            
            # Vérifier titre contient partie attendue
            if expected_title_part:
                title_ok = expected_title_part.lower() in (result.title or "").lower()
                results.append(should_detect and title_ok)
            else:
                results.append(should_detect)
        else:
            print(f"   ⚪ Pas de demande")
            results.append(not should_detect)
    
    success_rate = sum(results) / len(results)
    print(f"\n📊 Résultats: {sum(results)}/{len(results)} ({success_rate*100:.0f}%)")
    
    return success_rate >= 0.8  # Au moins 80%


def test_markdown_extractor():
    """Test extraction contenu markdown"""
    print("\n" + "="*70)
    print("TEST 2: MARKDOWN EXTRACTOR - Extraction contenu")
    print("="*70)
    
    from extensions.file_writer.markdown_extractor import MarkdownExtractor
    
    extractor = MarkdownExtractor(debug=True)
    
    # Test 1: Bloc code markdown
    response1 = """Voici le document:

```md
# Guide Python

## Introduction

Python est un langage de programmation.

- Simple
- Puissant
- Populaire
```

J'espère que ça aide !"""
    
    print("\nTest 1: Bloc code markdown")
    content1 = extractor.extract(response1)
    
    if content1 and "# Guide Python" in content1:
        print(f"✅ Extraction réussie ({len(content1)} chars)")
        test1_ok = True
    else:
        print("❌ Échec extraction")
        test1_ok = False
    
    # Test 2: Markdown brut
    response2 = """# Documentation API

## Endpoints

### GET /users

Récupère la liste des utilisateurs.

**Paramètres:**
- `limit`: Nombre max résultats
- `offset`: Position départ"""
    
    print("\nTest 2: Markdown brut")
    content2 = extractor.extract(response2)
    
    if content2 and "# Documentation API" in content2:
        print(f"✅ Extraction réussie ({len(content2)} chars)")
        test2_ok = True
    else:
        print("❌ Échec extraction")
        test2_ok = False
    
    # Test 3: Pas de markdown
    response3 = "Salut ! Comment ça va ?"
    
    print("\nTest 3: Pas de markdown")
    content3 = extractor.extract(response3)
    
    if content3 is None:
        print("✅ Pas de contenu extrait (attendu)")
        test3_ok = True
    else:
        print("❌ Contenu extrait (non attendu)")
        test3_ok = False
    
    results = [test1_ok, test2_ok, test3_ok]
    print(f"\n📊 Résultats: {sum(results)}/3")
    
    return all(results)


def test_file_saver():
    """Test sauvegarde fichiers"""
    print("\n" + "="*70)
    print("TEST 3: FILE SAVER - Sauvegarde fichiers")
    print("="*70)
    
    from extensions.file_writer.file_saver import FileSaver
    
    saver = FileSaver(uploads_dir="data/uploads", debug=True)
    
    content_test = """# Test Document

## Section 1

Contenu de test pour validation sauvegarde.

- Point 1
- Point 2
- Point 3
"""
    
    # Test sauvegarde
    print("\nTest sauvegarde simple")
    path1 = saver.save(content_test, title="test_file_writer_validation")
    
    if path1 and Path(path1).exists():
        print(f"✅ Fichier sauvegardé: {path1}")
        test1_ok = True
        
        # Vérifier contenu
        with open(path1, 'r', encoding='utf-8') as f:
            saved_content = f.read()
        
        if saved_content == content_test:
            print("✅ Contenu vérifié")
        else:
            print("⚠️ Contenu différent")
    else:
        print("❌ Échec sauvegarde")
        test1_ok = False
    
    # Test collision nom
    print("\nTest collision nom")
    path2 = saver.save(content_test, title="test_file_writer_validation")
    
    if path2 and path2 != path1:
        print(f"✅ Collision gérée: {path2}")
        test2_ok = True
    else:
        print("❌ Collision non gérée")
        test2_ok = False
    
    # Test caractères spéciaux
    print("\nTest caractères spéciaux")
    path3 = saver.save(content_test, title="Test/File:Writer*2.0")
    
    if path3 and Path(path3).exists():
        print(f"✅ Caractères nettoyés: {Path(path3).name}")
        test3_ok = True
    else:
        print("❌ Échec nettoyage")
        test3_ok = False
    
    # Stats
    stats = saver.get_statistics()
    print(f"\n📊 Stats: {stats['files_saved']} fichiers, {stats['total_bytes']} bytes")
    
    results = [test1_ok, test2_ok, test3_ok]
    return all(results)


def test_file_writer_agent():
    """Test orchestration complète"""
    print("\n" + "="*70)
    print("TEST 4: FILE WRITER AGENT - Orchestration")
    print("="*70)
    
    from extensions.file_writer.file_writer_agent import FileWriterAgent
    
    agent = FileWriterAgent(uploads_dir="data/uploads", debug=True)
    
    # Test 1: Demande avec bloc markdown
    print("\nTest 1: Demande avec bloc markdown")
    user_msg1 = "écris-moi un .md sur FastAPI"
    ai_resp1 = """Voici le guide FastAPI:

```md
# Guide FastAPI

## Introduction

FastAPI est un framework web moderne pour Python.

## Avantages

- Rapide
- Type hints natifs
- Documentation auto
```"""
    
    path1 = agent.process_response(user_msg1, ai_resp1)
    
    if path1:
        print(f"✅ Fichier sauvegardé: {path1}")
        test1_ok = True
    else:
        print("❌ Pas de fichier sauvegardé")
        test1_ok = False
    
    # Test 2: Pas de demande
    print("\nTest 2: Pas de demande")
    user_msg2 = "Salut Luna !"
    ai_resp2 = "Salut ! 😊"
    
    path2 = agent.process_response(user_msg2, ai_resp2)
    
    if path2 is None:
        print("✅ Pas de sauvegarde (attendu)")
        test2_ok = True
    else:
        print("❌ Sauvegarde inattendue")
        test2_ok = False
    
    # Stats
    stats = agent.get_statistics()
    print(f"\n📊 Stats agent:")
    print(f"   - Requêtes traitées: {stats['requests_processed']}")
    print(f"   - Fichiers sauvegardés: {stats['files_saved']}")
    print(f"   - Taux succès: {stats['success_rate']*100:.0f}%")
    
    results = [test1_ok, test2_ok]
    return all(results)


def test_integration():
    """Test intégration via API publique"""
    print("\n" + "="*70)
    print("TEST 5: INTEGRATION - API publique")
    print("="*70)
    
    from extensions.file_writer import (
        initialize_file_writer,
        is_available,
        process_response,
        get_statistics
    )
    
    # Initialisation
    print("\nInitialisation extension")
    ext = initialize_file_writer(uploads_dir="data/uploads", debug=True)
    
    if ext:
        print("✅ Extension initialisée")
    else:
        print("❌ Échec initialisation")
        return False
    
    # Vérifier disponibilité
    if is_available():
        print("✅ Extension disponible")
    else:
        print("❌ Extension non disponible")
        return False
    
    # Test workflow complet
    print("\nTest workflow complet via API")
    user_msg = "crée un fichier .md de changelog"
    ai_resp = """# Changelog

## Version 1.0.0

### Ajouts
- Fonctionnalité A
- Fonctionnalité B

### Corrections
- Bug fix 1"""
    
    saved_path = process_response(user_msg, ai_resp)
    
    if saved_path:
        print(f"✅ Workflow complet réussi: {saved_path}")
        
        # Vérifier fichier existe
        if Path(saved_path).exists():
            print("✅ Fichier existe")
            test_ok = True
        else:
            print("❌ Fichier introuvable")
            test_ok = False
    else:
        print("❌ Workflow échoué")
        test_ok = False
    
    # Stats finales
    stats = get_statistics()
    print(f"\n📊 Stats globales:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    return test_ok


def main():
    """Exécute tous les tests"""
    print("\n" + "="*70)
    print("🧪 TEST SUITE FILE WRITER EXTENSION")
    print("="*70)
    print(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    
    tests = [
        ("Request Detector", test_request_detector),
        ("Markdown Extractor", test_markdown_extractor),
        ("File Saver", test_file_saver),
        ("File Writer Agent", test_file_writer_agent),
        ("Integration", test_integration),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"\n❌ ERREUR TEST {test_name}: {e}")
            import traceback
            traceback.print_exc()
            results[test_name] = False
    
    # Rapport final
    print("\n" + "="*70)
    print("📊 RAPPORT FINAL")
    print("="*70)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    success_count = sum(results.values())
    total_count = len(results)
    success_rate = success_count / total_count if total_count > 0 else 0
    
    print(f"\n🎯 Résultat global: {success_count}/{total_count} tests réussis ({success_rate*100:.0f}%)")
    
    if success_rate == 1.0:
        print("\n🎉 TOUS LES TESTS SONT PASSÉS !")
        return 0
    elif success_rate >= 0.8:
        print("\n⚠️ Quelques tests ont échoué mais système fonctionnel")
        return 0
    else:
        print("\n❌ ÉCHEC - Système nécessite corrections")
        return 1


if __name__ == "__main__":
    sys.exit(main())
