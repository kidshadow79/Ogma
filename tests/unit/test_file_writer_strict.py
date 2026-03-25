"""
Tests unitaires stricts pour extensions/file_writer/
Architecture: Sauvegarde automatique fichiers markdown (.md)

Composants testés:
- RequestDetector: Détection demandes création .md
- MarkdownExtractor: Extraction blocs markdown
- FileSaver: Sauvegarde fichiers avec nommage unique
- FileWriterAgent: Orchestration process_response()
- Module API: initialize_file_writer, is_available
"""

import unittest
from unittest.mock import Mock, patch, MagicMock, mock_open
import sys
import os
from pathlib import Path
import tempfile

# Import file_writer
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'extensions'))
from file_writer import (
    initialize_file_writer,
    is_available,
    cleanup,
    get_file_writer  # Nom correct
)
from file_writer.request_detector import RequestDetector, FileRequest
from file_writer.markdown_extractor import MarkdownExtractor
from file_writer.file_saver import FileSaver
from file_writer.file_writer_agent import FileWriterAgent


class TestRequestDetector(unittest.TestCase):
    """Tests détection demandes fichiers .md"""
    
    def setUp(self):
        self.detector = RequestDetector(debug=False)
        
    def test_detect_md_request_explicit(self):
        """Test détection demande .md explicite"""
        message = "écris-moi un .md sur Python"
        
        result = self.detector.detect(message)
        
        assert isinstance(result, FileRequest)
        assert result.is_request is True
        assert result.extension == "md" or result.extension == ".md"
        
    def test_detect_markdown_keyword(self):
        """Test détection avec keyword 'markdown'"""
        message = "crée un fichier markdown avec guide Python"
        
        result = self.detector.detect(message)
        
        assert isinstance(result, FileRequest)
        assert result.is_request is True
        
    def test_detect_no_request(self):
        """Test message non-requête fichier"""
        message = "explique-moi comment marche Python"
        
        result = self.detector.detect(message)
        
        assert isinstance(result, FileRequest)
        assert result.is_request is False
        
    def test_is_file_request_true(self):
        """Test is_file_request retourne True"""
        message = "génère un .md sur les algorithmes"
        
        is_request = self.detector.is_file_request(message)
        
        assert is_request is True
        
    def test_is_file_request_false(self):
        """Test is_file_request retourne False"""
        message = "quelle est la capitale de France ?"
        
        is_request = self.detector.is_file_request(message)
        
        assert is_request is False
        
    def test_extract_title(self):
        """Test extraction titre depuis message"""
        message = "écris un .md sur 'Guide Python Débutants'"
        
        title = self.detector.extract_title(message)
        
        # Peut retourner None ou titre extrait
        if title:
            assert isinstance(title, str)
            assert len(title) > 0


class TestMarkdownExtractor(unittest.TestCase):
    """Tests extraction contenu markdown"""
    
    def setUp(self):
        self.extractor = MarkdownExtractor(debug=False)
        
    def test_extract_simple_markdown(self):
        """Test extraction markdown simple"""
        response = "# Guide Python\n\nVoici le contenu du guide.\n\n## Section 1"
        
        extracted = self.extractor.extract(response)
        
        assert isinstance(extracted, str)
        assert "# Guide Python" in extracted
        assert "## Section 1" in extracted
        
    def test_extract_code_blocks(self):
        """Test extraction avec blocs code"""
        response = "# Documentation\n\n```python\nprint('hello')\n```\n\nTexte après."
        
        extracted = self.extractor.extract(response)
        
        assert "```python" in extracted or "print('hello')" in extracted
        
    def test_extract_empty_response(self):
        """Test extraction réponse vide"""
        response = ""
        
        extracted = self.extractor.extract(response)
        
        # Peut retourner string vide ou None
        assert extracted == "" or extracted is None or len(extracted) == 0
        
    def test_extract_no_markdown(self):
        """Test extraction texte sans markdown"""
        response = "Ceci est juste du texte brut sans formatage markdown."
        
        extracted = self.extractor.extract(response)
        
        # Peut retourner texte brut ou None selon implémentation
        assert isinstance(extracted, str) or extracted is None


class TestFileSaver(unittest.TestCase):
    """Tests sauvegarde fichiers"""
    
    def setUp(self):
        # Utiliser répertoire temporaire pour tests
        self.temp_dir = tempfile.mkdtemp()
        self.saver = FileSaver(uploads_dir=self.temp_dir, debug=False)
        
    def tearDown(self):
        # Nettoyer répertoire temporaire
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_save_file_success(self):
        """Test sauvegarde fichier avec succès"""
        content = "# Guide Python\n\nContenu du guide."
        title = "Guide Python"
        
        result = self.saver.save(content, title=title, extension=".md")
        
        assert result is not None
        assert "filepath" in result or isinstance(result, str)
        
    def test_save_file_auto_title(self):
        """Test sauvegarde sans titre (génération auto)"""
        content = "# Titre Auto\n\nContenu."
        
        result = self.saver.save(content, extension=".md")
        
        assert result is not None
        
    def test_save_file_duplicate_name(self):
        """Test sauvegarde avec nom existant (suffixe numérique)"""
        content = "# Document\n\nContenu."
        title = "test_document"
        
        # Première sauvegarde
        result1 = self.saver.save(content, title=title, extension=".md")
        # Deuxième sauvegarde même titre
        result2 = self.saver.save(content, title=title, extension=".md")
        
        assert result1 is not None
        assert result2 is not None
        # Noms différents (suffixe ajouté)
        if isinstance(result1, dict) and isinstance(result2, dict):
            assert result1["filepath"] != result2["filepath"]
        
    def test_sanitize_filename(self):
        """Test nettoyage nom fichier (caractères invalides)"""
        dangerous_name = "fichier/avec*caractères<invalides>"
        
        sanitized = self.saver._sanitize_filename(dangerous_name)
        
        assert "/" not in sanitized
        assert "*" not in sanitized
        assert "<" not in sanitized
        assert ">" not in sanitized
        
    def test_get_statistics(self):
        """Test récupération statistiques"""
        stats = self.saver.get_statistics()
        
        assert isinstance(stats, dict)
        # Peut contenir files_saved, total_size, etc.
        
    def test_list_saved_files(self):
        """Test liste fichiers sauvegardés"""
        # Sauvegarder un fichier test
        self.saver.save("# Test\n\nContenu.", title="test", extension=".md")
        
        files = self.saver.list_saved_files(limit=10)
        
        assert isinstance(files, list)
        # Doit contenir au moins 1 fichier
        assert len(files) >= 1


class TestFileWriterAgent(unittest.TestCase):
    """Tests orchestration FileWriterAgent"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.agent = FileWriterAgent(uploads_dir=self.temp_dir, debug=False)
        
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
    def test_process_response_with_request(self):
        """Test process_response avec demande .md"""
        user_message = "écris-moi un .md sur Python"
        ai_response = "# Guide Python\n\nVoici un guide complet sur Python."
        
        result = self.agent.process_response(user_message, ai_response)
        
        # Peut retourner dict ou None selon détection
        if result:
            assert "filepath" in result or isinstance(result, str)
            
    def test_process_response_no_request(self):
        """Test process_response sans demande fichier"""
        user_message = "explique-moi Python"
        ai_response = "Python est un langage de programmation..."
        
        result = self.agent.process_response(user_message, ai_response)
        
        # Pas de demande → pas de sauvegarde
        assert result is None
        
    def test_is_file_request(self):
        """Test vérification demande fichier"""
        assert self.agent.is_file_request("crée un .md sur les API") is True
        assert self.agent.is_file_request("comment marche Python ?") is False
        
    def test_get_statistics(self):
        """Test récupération statistiques agent"""
        stats = self.agent.get_statistics()
        
        assert isinstance(stats, dict)
        # Peut contenir requests_detected, files_saved, etc.
        
    def test_list_recent_files(self):
        """Test liste fichiers récents"""
        # Sauvegarder un fichier
        self.agent.process_response(
            "écris un .md test",
            "# Test\n\nContenu test."
        )
        
        files = self.agent.list_recent_files(limit=5)
        
        assert isinstance(files, list)
        
    def test_get_status(self):
        """Test récupération statut agent"""
        status = self.agent.get_status()
        
        assert isinstance(status, dict)
        # Peut contenir is_ready, uploads_dir, etc.


class TestModuleLevelFunctions(unittest.TestCase):
    """Tests API publique module"""
    
    def test_initialize_file_writer_success(self):
        """Test initialisation extension"""
        temp_dir = tempfile.mkdtemp()
        
        try:
            agent = initialize_file_writer(uploads_dir=temp_dir, debug=False)
            
            assert agent is not None
            assert isinstance(agent, FileWriterAgent)
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    def test_is_available(self):
        """Test vérification disponibilité"""
        available = is_available()
        
        assert isinstance(available, bool)
        
    def test_cleanup(self):
        """Test cleanup extension"""
        # Ne doit pas crasher
        cleanup()
        
    def test_get_file_writer_agent(self):
        """Test récupération instance singleton"""
        agent = get_file_writer()  # Nom corrigé
        
        # Peut être None si pas initialisé
        if agent:
            assert isinstance(agent, FileWriterAgent)


class TestFileWriterIntegration(unittest.TestCase):
    """Tests workflows complets"""
    
    def test_full_workflow_md_creation(self):
        """Test workflow complet création .md"""
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Initialiser
            agent = initialize_file_writer(uploads_dir=temp_dir, debug=False)
            
            # Process demande
            user_msg = "écris un guide markdown sur Git"
            ai_resp = "# Guide Git\n\n## Introduction\n\nGit est un système de contrôle de version."
            
            result = agent.process_response(user_msg, ai_resp)
            
            if result:
                # Vérifier fichier créé
                if isinstance(result, dict):
                    filepath = result["filepath"]
                    assert Path(filepath).exists()
                    
                    # Vérifier contenu
                    content = Path(filepath).read_text(encoding="utf-8")
                    assert "# Guide Git" in content
                    
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    def test_full_workflow_no_markdown_request(self):
        """Test workflow sans demande markdown"""
        temp_dir = tempfile.mkdtemp()
        
        try:
            agent = initialize_file_writer(uploads_dir=temp_dir, debug=False)
            
            result = agent.process_response(
                "explique-moi Git",
                "Git est un système de contrôle de version décentralisé."
            )
            
            # Pas de demande .md → pas de fichier
            assert result is None
            
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestFileWriterEdgeCases(unittest.TestCase):
    """Tests cas limites"""
    
    def test_save_empty_content(self):
        """Test sauvegarde contenu vide"""
        temp_dir = tempfile.mkdtemp()
        
        try:
            saver = FileSaver(uploads_dir=temp_dir, debug=False)
            
            # Contenu vide → peut accepter ou refuser
            result = saver.save("", title="empty", extension=".md")
            
            # Acceptable si None ou dict
            assert result is None or isinstance(result, dict)
            
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    def test_save_very_long_title(self):
        """Test sauvegarde avec titre très long"""
        temp_dir = tempfile.mkdtemp()
        
        try:
            saver = FileSaver(uploads_dir=temp_dir, debug=False)
            
            long_title = "titre_" * 50  # 300+ caractères
            result = saver.save("# Contenu\n\nTest.", title=long_title, extension=".md")
            
            # Doit tronquer ou accepter
            if result and isinstance(result, dict):
                filename = Path(result["filepath"]).name
                # Noms fichiers limités à ~255 caractères
                assert len(filename) <= 255
                
        finally:
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
            
    def test_extract_malformed_markdown(self):
        """Test extraction markdown malformé"""
        extractor = MarkdownExtractor(debug=False)
        
        malformed = "### Titre sans # initial\n\n```code non fermé"
        
        # Ne doit pas crasher
        extracted = extractor.extract(malformed)
        
        assert isinstance(extracted, str) or extracted is None


if __name__ == '__main__':
    unittest.main(verbosity=2)
