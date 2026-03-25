"""
🧪 TESTS SYSTÈME RÉSUMÉS PERSISTANTS
=====================================

Valide le cycle complet :
1. Création résumés pendant session
2. Sauvegarde dans JSON conversation
3. Rechargement et restauration état
4. Continuité résumisation

Usage:
    python tests/test_summarizer_persistence.py
    
    ou avec pytest:
    pytest tests/test_summarizer_persistence.py -v
"""

import json
import sys
import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Ajouter racine projet au path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Import explicite du fichier utils.py racine (pas le package utils/)
import importlib.util
utils_spec = importlib.util.spec_from_file_location("utils_root", PROJECT_ROOT / "utils.py")
utils_root = importlib.util.module_from_spec(utils_spec)
utils_spec.loader.exec_module(utils_root)


class TestSummarizerPersistence:
    """Tests du système de résumés persistants."""
    
    def setup_method(self):
        """Setup avant chaque test."""
        # Créer répertoire temporaire
        self.temp_dir = tempfile.mkdtemp(prefix="ogma_test_")
        self.conversations_dir = Path(self.temp_dir) / "conversations"
        self.cache_dir = Path(self.temp_dir) / "summaries_cache"
        self.conversations_dir.mkdir(parents=True)
        self.cache_dir.mkdir(parents=True)
        
    def teardown_method(self):
        """Cleanup après chaque test."""
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def _generate_test_messages(self, count: int) -> List[Dict]:
        """Génère des messages de test réalistes."""
        messages = []
        topics = [
            ("Salut ! Comment ça va ?", "Salut ! Ça va bien, merci. Et toi ?"),
            ("Tu peux m'expliquer Python ?", "Bien sûr ! Python est un langage de programmation..."),
            ("C'est quoi une fonction ?", "Une fonction est un bloc de code réutilisable..."),
            ("Et les classes ?", "Les classes permettent de créer des objets avec..."),
            ("Comment gérer les erreurs ?", "En Python, on utilise try/except pour..."),
            ("Parle-moi des listes", "Les listes sont des collections ordonnées..."),
            ("Et les dictionnaires ?", "Les dictionnaires sont des paires clé-valeur..."),
            ("C'est quoi async ?", "Async permet la programmation asynchrone..."),
            ("Comment lire un fichier ?", "On utilise open() avec un context manager..."),
            ("Merci pour tout !", "De rien, c'était un plaisir de t'aider !"),
        ]
        
        for i in range(count):
            topic_idx = i % len(topics)
            user_msg, assistant_msg = topics[topic_idx]
            
            # Ajouter variation pour éviter clés cache identiques
            user_msg = f"{user_msg} (question {i+1})"
            assistant_msg = f"{assistant_msg} (réponse {i+1})"
            
            messages.append({'role': 'user', 'content': user_msg})
            messages.append({'role': 'assistant', 'content': assistant_msg})
        
        return messages
    
    def test_01_summarizer_state_management(self):
        """Test: Gestion état interne du summarizer."""
        print("\n🧪 Test 1: Gestion état summarizer")
        
        from conversation_summarizer import ConversationSummarizer
        
        summarizer = ConversationSummarizer()
        
        # État initial vide
        assert summarizer._current_summaries == []
        assert summarizer._last_summarized_index == 0
        assert summarizer._session_cache == {}
        print("  ✅ État initial vide")
        
        # Ajouter un résumé
        summarizer.add_summary_range(0, 10, "Résumé test 1", "key123")
        
        assert len(summarizer._current_summaries) == 1
        assert summarizer._last_summarized_index == 10
        assert "key123" in summarizer._session_cache
        print("  ✅ Ajout résumé fonctionne")
        
        # Export structure
        data = summarizer.get_summaries_data()
        assert "ranges" in data
        assert len(data["ranges"]) == 1
        assert data["last_index"] == 10
        print("  ✅ Export structure correct")
        
        # Clear
        summarizer.clear_session_state()
        assert summarizer._current_summaries == []
        assert summarizer._last_summarized_index == 0
        print("  ✅ Clear fonctionne")
        
        print("✅ Test 1 PASSÉ")
    
    def test_02_summaries_data_export_import(self):
        """Test: Export/Import structure résumés."""
        print("\n🧪 Test 2: Export/Import résumés")
        
        from conversation_summarizer import ConversationSummarizer
        
        # Summarizer 1: créer des résumés
        summarizer1 = ConversationSummarizer()
        summarizer1.add_summary_range(0, 10, "Premier groupe de messages", "abc123")
        summarizer1.add_summary_range(10, 20, "Deuxième groupe de messages", "def456")
        
        # Exporter
        exported_data = summarizer1.get_summaries_data()
        print(f"  📤 Exporté: {len(exported_data['ranges'])} résumés, last_index={exported_data['last_index']}")
        
        # Summarizer 2: importer
        summarizer2 = ConversationSummarizer()
        success = summarizer2.load_summaries_data(exported_data)
        
        assert success
        assert len(summarizer2._current_summaries) == 2
        assert summarizer2._last_summarized_index == 20
        assert "abc123" in summarizer2._session_cache
        assert "def456" in summarizer2._session_cache
        print(f"  📥 Importé: {len(summarizer2._current_summaries)} résumés restaurés")
        
        # Vérifier textes
        texts = summarizer2.get_cached_summaries_texts()
        assert len(texts) == 2
        assert "Premier groupe" in texts[0]
        print("  ✅ Textes résumés accessibles")
        
        print("✅ Test 2 PASSÉ")
    
    def test_03_json_save_load_format(self):
        """Test: Format JSON conversation avec résumés."""
        print("\n🧪 Test 3: Format JSON étendu")
        
        # Créer données test
        messages = self._generate_test_messages(5)  # 10 messages
        summaries_data = {
            "ranges": [
                {"start": 0, "end": 10, "text": "Test résumé", "cache_key": "test123"}
            ],
            "last_index": 10,
            "interval": 10
        }
        
        conv_id = "test_conv_001"
        conv_file = self.conversations_dir / f"{conv_id}.json"
        
        # Sauvegarder manuellement en format étendu
        conversation_data = {
            "messages": messages,
            "summaries": summaries_data
        }
        conv_file.write_text(json.dumps(conversation_data, ensure_ascii=False, indent=2), encoding='utf-8')
        print(f"  💾 Fichier créé: {conv_file.name}")
        
        # Vérifier structure JSON
        raw_data = json.loads(conv_file.read_text(encoding='utf-8'))
        assert isinstance(raw_data, dict)
        assert "messages" in raw_data
        assert "summaries" in raw_data
        print("  ✅ Format étendu correct")
        
        # Tester load_conversation directement avec le fichier
        from utils import load_conversation
        
        # Simuler en copiant dans le vrai répertoire temporairement
        # import utils - using utils_root instead
        real_conv_file = utils_root.CONVERSATIONS_DIR / f"{conv_id}.json"
        try:
            real_conv_file.write_text(conv_file.read_text(encoding='utf-8'), encoding='utf-8')
            
            loaded = load_conversation(conv_id)
            assert "messages" in loaded
            assert "summaries" in loaded
            assert len(loaded["messages"]) == 10
            assert loaded["summaries"]["last_index"] == 10
            print(f"  📂 Chargé: {len(loaded['messages'])} messages + résumés")
        finally:
            if real_conv_file.exists():
                real_conv_file.unlink()
        
        print("✅ Test 3 PASSÉ")
    
    def test_04_backward_compatibility(self):
        """Test: Rétrocompatibilité ancien format (liste simple)."""
        print("\n🧪 Test 4: Rétrocompatibilité ancien format")
        
        from utils import load_conversation
        # import utils - using utils_root instead
        
        # Créer fichier ancien format (liste directe)
        old_format_messages = [
            {"role": "user", "content": "Ancien message 1"},
            {"role": "assistant", "content": "Ancienne réponse 1"}
        ]
        
        conv_id = "old_format_conv"
        
        # Créer dans le vrai répertoire de conversations
        real_conv_file = utils_root.CONVERSATIONS_DIR / f"{conv_id}.json"
        
        try:
            real_conv_file.write_text(json.dumps(old_format_messages, ensure_ascii=False), encoding='utf-8')
            print(f"  📁 Fichier ancien format créé")
            
            loaded = load_conversation(conv_id)
            
            assert "messages" in loaded
            assert "summaries" in loaded
            assert loaded["summaries"] is None  # Pas de résumés dans ancien format
            assert len(loaded["messages"]) == 2
            print(f"  ✅ Ancien format chargé: {len(loaded['messages'])} messages")
            
        finally:
            if real_conv_file.exists():
                real_conv_file.unlink()
        
        print("✅ Test 4 PASSÉ")
    
    def test_05_should_summarize_logic(self):
        """Test: Logique should_summarize sans limite 100."""
        print("\n🧪 Test 5: Logique should_summarize")
        
        from conversation_summarizer import ConversationSummarizer
        
        summarizer = ConversationSummarizer()
        
        # Cas 1: Pas assez de messages
        assert not summarizer.should_summarize(5)
        print("  ✅ 5 messages: pas de résumé")
        
        # Cas 2: 10 messages, aucun résumé existant
        assert summarizer.should_summarize(10)
        print("  ✅ 10 messages non résumés: résumé nécessaire")
        
        # Cas 3: 10 messages déjà résumés, total 15
        summarizer._last_summarized_index = 10
        assert not summarizer.should_summarize(15)  # Seulement 5 non résumés
        print("  ✅ 15 messages (10 résumés): pas de résumé")
        
        # Cas 4: 20 messages, 10 résumés
        assert summarizer.should_summarize(20)  # 10 non résumés
        print("  ✅ 20 messages (10 résumés): résumé nécessaire")
        
        # Cas 5: PLUS DE LIMITE 100 !
        summarizer._last_summarized_index = 0
        assert summarizer.should_summarize(150)  # Doit fonctionner maintenant
        print("  ✅ 150 messages: fonctionne (plus de limite 100)")
        
        print("✅ Test 5 PASSÉ")
    
    def test_06_get_summary_range(self):
        """Test: Calcul plage résumé."""
        print("\n🧪 Test 6: Calcul plage résumé")
        
        from conversation_summarizer import ConversationSummarizer
        
        summarizer = ConversationSummarizer()
        
        # Cas 1: Premier résumé
        start, end = summarizer.get_summary_range(15)
        assert start == 0
        assert end == 10
        print(f"  ✅ Premier résumé: {start}-{end}")
        
        # Cas 2: Après un résumé
        summarizer._last_summarized_index = 10
        start, end = summarizer.get_summary_range(25)
        assert start == 10
        assert end == 20
        print(f"  ✅ Deuxième résumé: {start}-{end}")
        
        # Cas 3: Après plusieurs résumés
        summarizer._last_summarized_index = 50
        start, end = summarizer.get_summary_range(65)
        assert start == 50
        assert end == 60
        print(f"  ✅ Résumé suivant: {start}-{end}")
        
        print("✅ Test 6 PASSÉ")
    
    def test_07_full_cycle_simulation(self):
        """Test: Cycle complet session → save → load → continue."""
        print("\n🧪 Test 7: Cycle complet (simulation session)")
        
        from conversation_summarizer import ConversationSummarizer
        from utils import save_conversation, load_conversation
        # import utils - using utils_root instead
        
        conv_id = "session_test_001"
        real_conv_file = utils_root.CONVERSATIONS_DIR / f"{conv_id}.json"
        
        try:
            # === SESSION 1: Créer conversation avec résumés ===
            print("  📝 Session 1: Création conversation")
            
            summarizer1 = ConversationSummarizer()
            messages = self._generate_test_messages(15)  # 30 messages
            
            # Simuler résumisation progressive
            summarizer1.add_summary_range(0, 10, "Discussion Python bases", "key1")
            summarizer1.add_summary_range(10, 20, "Fonctions et classes", "key2")
            
            # Sauvegarder manuellement avec format étendu
            summaries_data = summarizer1.get_summaries_data()
            conversation_data = {
                "messages": messages,
                "summaries": summaries_data
            }
            real_conv_file.write_text(json.dumps(conversation_data, ensure_ascii=False, indent=2), encoding='utf-8')
            
            print(f"    💾 Sauvegardé: {len(messages)} messages + {len(summaries_data['ranges'])} résumés")
            
            # === SESSION 2: Recharger et vérifier ===
            print("  📂 Session 2: Rechargement")
            
            summarizer2 = ConversationSummarizer()
            
            # Charger conversation
            loaded = load_conversation(conv_id)
            
            # Restaurer état summarizer
            if loaded["summaries"]:
                summarizer2.load_summaries_data(loaded["summaries"])
            
            assert len(summarizer2._current_summaries) == 2
            assert summarizer2._last_summarized_index == 20
            print(f"    ✅ État restauré: last_index={summarizer2._last_summarized_index}")
            
            # Vérifier textes disponibles
            texts = summarizer2.get_cached_summaries_texts()
            assert len(texts) == 2
            print(f"    ✅ {len(texts)} résumés accessibles")
            
            # === SESSION 2: Continuer résumisation ===
            print("  ➕ Session 2: Continuité résumisation")
            
            # Ajouter nouveaux messages
            new_messages = loaded["messages"] + self._generate_test_messages(5)  # +10 messages = 40 total
            
            # Vérifier si résumisation nécessaire
            needs_summary = summarizer2.should_summarize(len(new_messages))
            assert needs_summary  # 40 - 20 = 20 non résumés >= 10
            print(f"    ✅ {len(new_messages)} messages, résumisation nécessaire: {needs_summary}")
            
            # Simuler nouveau résumé
            summarizer2.add_summary_range(20, 30, "Suite discussion", "key3")
            
            # Sauvegarder mise à jour
            new_summaries_data = summarizer2.get_summaries_data()
            new_conversation_data = {
                "messages": new_messages,
                "summaries": new_summaries_data
            }
            real_conv_file.write_text(json.dumps(new_conversation_data, ensure_ascii=False, indent=2), encoding='utf-8')
            
            assert len(new_summaries_data["ranges"]) == 3
            print(f"    💾 Sauvegardé: {len(new_messages)} messages + {len(new_summaries_data['ranges'])} résumés")
            
            # === VÉRIFICATION FINALE ===
            print("  🔍 Vérification finale")
            
            final_loaded = load_conversation(conv_id)
            assert len(final_loaded["messages"]) == 40
            assert len(final_loaded["summaries"]["ranges"]) == 3
            assert final_loaded["summaries"]["last_index"] == 30
            print(f"    ✅ Conversation finale: {len(final_loaded['messages'])} messages, {len(final_loaded['summaries']['ranges'])} résumés")
            
        finally:
            if real_conv_file.exists():
                real_conv_file.unlink()
        
        print("✅ Test 7 PASSÉ")
    
    def test_08_api_extensions(self):
        """Test: API pour extensions (get_all_summaries_from_conversations)."""
        print("\n🧪 Test 8: API extensions")
        
        from conversation_summarizer import get_all_summaries_from_conversations, get_all_summary_texts
        # import utils - using utils_root instead
        
        created_files = []
        
        try:
            # Créer plusieurs conversations avec résumés dans le vrai répertoire
            for i in range(3):
                messages = self._generate_test_messages(5)
                summaries_data = {
                    "ranges": [
                        {"start": 0, "end": 10, "text": f"Résumé conv {i+1}", "cache_key": f"key_{i}"}
                    ],
                    "last_index": 10,
                    "interval": 10
                }
                
                conv_id = f"api_test_conv_{i:03d}"
                conv_file = utils_root.CONVERSATIONS_DIR / f"{conv_id}.json"
                conversation_data = {
                    "messages": messages,
                    "summaries": summaries_data
                }
                conv_file.write_text(json.dumps(conversation_data, ensure_ascii=False, indent=2), encoding='utf-8')
                created_files.append(conv_file)
            
            print(f"  📁 3 conversations créées avec résumés")
            
            # Tester API
            all_summaries = get_all_summaries_from_conversations(
                str(utils_root.CONVERSATIONS_DIR), 
                max_conversations=50
            )
            
            # Filtrer seulement nos fichiers de test
            test_summaries = [s for s in all_summaries if s['conversation_id'].startswith('api_test_conv_')]
            assert len(test_summaries) == 3
            print(f"  ✅ API retourne {len(test_summaries)} conversations de test")
            
            # Tester API simplifiée
            all_texts = get_all_summary_texts(str(utils_root.CONVERSATIONS_DIR), max_conversations=50)
            
            # Compter les textes de test
            test_texts = [t for t in all_texts if "Résumé conv" in t]
            assert len(test_texts) >= 3
            print(f"  ✅ API simplifiée retourne {len(test_texts)} textes de test")
            
        finally:
            # Nettoyer les fichiers créés
            for f in created_files:
                if f.exists():
                    f.unlink()
        
        print("✅ Test 8 PASSÉ")


def run_all_tests():
    """Exécute tous les tests."""
    print("=" * 60)
    print("🧪 TESTS SYSTÈME RÉSUMÉS PERSISTANTS")
    print("=" * 60)
    
    test_instance = TestSummarizerPersistence()
    tests = [
        ("test_01_summarizer_state_management", "Gestion état summarizer"),
        ("test_02_summaries_data_export_import", "Export/Import résumés"),
        ("test_03_json_save_load_format", "Format JSON étendu"),
        ("test_04_backward_compatibility", "Rétrocompatibilité ancien format"),
        ("test_05_should_summarize_logic", "Logique should_summarize"),
        ("test_06_get_summary_range", "Calcul plage résumé"),
        ("test_07_full_cycle_simulation", "Cycle complet simulation"),
        ("test_08_api_extensions", "API extensions"),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, description in tests:
        try:
            test_instance.setup_method()
            getattr(test_instance, test_name)()
            passed += 1
        except AssertionError as e:
            print(f"\n❌ ÉCHEC: {description}")
            print(f"   Erreur: {e}")
            failed += 1
        except Exception as e:
            print(f"\n💥 ERREUR: {description}")
            print(f"   Exception: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
        finally:
            test_instance.teardown_method()
    
    print("\n" + "=" * 60)
    print(f"📊 RÉSULTATS: {passed} passés, {failed} échoués")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
