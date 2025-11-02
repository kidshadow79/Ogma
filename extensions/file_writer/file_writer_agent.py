#!/usr/bin/env python3
"""
🤖 FILE WRITER AGENT - Orchestrateur sauvegarde automatique fichiers .md
=========================================================================

Coordonne la détection, extraction et sauvegarde de fichiers markdown
générés par Luna.

WORKFLOW:
1. Détection demande création .md (RequestDetector)
2. Extraction contenu markdown (MarkdownExtractor)
3. Sauvegarde fichier (FileSaver)
4. Notification utilisateur

USAGE:
    agent = FileWriterAgent(
        uploads_dir="data/uploads",
        debug=True
    )
    
    saved_path = agent.process_response(
        user_message="écris-moi un .md sur Python",
        ai_response="# Guide Python\n\nContenu..."
    )
    
    if saved_path:
        print(f"✅ Fichier sauvegardé: {saved_path}")
"""

from pathlib import Path
from typing import Optional
from datetime import datetime

from .request_detector import RequestDetector, FileRequest
from .markdown_extractor import MarkdownExtractor
from .file_saver import FileSaver


class FileWriterAgent:
    """Orchestrateur principal extension File Writer."""
    
    def __init__(
        self,
        uploads_dir: str = "data/uploads",
        debug: bool = False
    ):
        """
        Initialise l'agent.
        
        Args:
            uploads_dir: Répertoire sauvegarde fichiers
            debug: Active logs debug détaillés
        """
        self.uploads_dir = uploads_dir
        self.debug = debug
        
        # Composants
        self.detector = RequestDetector(debug=debug)
        self.extractor = MarkdownExtractor(debug=debug)
        self.saver = FileSaver(uploads_dir=uploads_dir, debug=debug)
        
        # Stats agent
        self._stats = {
            'requests_processed': 0,
            'requests_detected': 0,
            'files_saved': 0,
            'extractions_failed': 0,
            'saves_failed': 0
        }
        
        if self.debug:
            print(f"[FILE-WRITER-AGENT] Initialisé")
            print(f"[FILE-WRITER-AGENT] Uploads dir: {uploads_dir}")
    
    def process_response(
        self,
        user_message: str,
        ai_response: str
    ) -> Optional[str]:
        """
        Traite paire user_message/ai_response pour détection et sauvegarde.
        
        Workflow:
        1. Vérifier si user_message demande création .md
        2. Si oui, extraire contenu markdown de ai_response
        3. Sauvegarder avec titre extrait
        4. Retourner chemin fichier ou None
        
        Args:
            user_message: Message utilisateur original
            ai_response: Réponse IA générée
            
        Returns:
            Chemin fichier sauvegardé ou None si pas de sauvegarde
        """
        self._stats['requests_processed'] += 1
        
        # 1. Détecter demande création fichier
        detection = self.detector.detect(user_message)
        
        if not detection.is_request:
            if self.debug:
                print("[FILE-WRITER-AGENT] ⚪ Pas de demande fichier détectée")
            return None
        
        self._stats['requests_detected'] += 1
        
        if self.debug:
            print(f"[FILE-WRITER-AGENT] ✅ Demande fichier détectée")
            print(f"[FILE-WRITER-AGENT] Titre: {detection.title}")
            print(f"[FILE-WRITER-AGENT] Confidence: {detection.confidence}")
        
        # 2. Extraire contenu markdown
        md_content = self.extractor.extract(ai_response)
        
        if not md_content:
            self._stats['extractions_failed'] += 1
            if self.debug:
                print("[FILE-WRITER-AGENT] ❌ Échec extraction contenu markdown")
            return None
        
        # Nettoyer contenu
        md_content = self.extractor.clean_content(md_content)
        
        if self.debug:
            print(f"[FILE-WRITER-AGENT] 📄 Contenu extrait: {len(md_content)} chars")
        
        # 3. Sauvegarder fichier
        title = detection.title or "document"
        
        saved_path = self.saver.save(
            content=md_content,
            title=title,
            extension="md"
        )
        
        if saved_path:
            self._stats['files_saved'] += 1
            if self.debug:
                print(f"[FILE-WRITER-AGENT] 💾 Fichier sauvegardé: {saved_path}")
            return saved_path
        else:
            self._stats['saves_failed'] += 1
            if self.debug:
                print("[FILE-WRITER-AGENT] ❌ Échec sauvegarde fichier")
            return None
    
    def is_file_request(self, user_message: str) -> bool:
        """
        Check rapide si message utilisateur demande création fichier.
        
        Args:
            user_message: Message utilisateur
            
        Returns:
            True si demande détectée
        """
        return self.detector.is_file_request(user_message)
    
    def get_statistics(self) -> dict:
        """
        Retourne statistiques complètes extension.
        
        Returns:
            Dict avec métriques agent + composants
        """
        stats = self._stats.copy()
        
        # Ajouter stats saver
        saver_stats = self.saver.get_statistics()
        stats['total_bytes'] = saver_stats.get('total_bytes', 0)
        stats['uploads_dir'] = saver_stats.get('uploads_dir', self.uploads_dir)
        
        # Calculer taux succès
        if stats['requests_detected'] > 0:
            stats['success_rate'] = stats['files_saved'] / stats['requests_detected']
        else:
            stats['success_rate'] = 0.0
        
        # Calculer taux extraction
        if stats['requests_detected'] > 0:
            stats['extraction_rate'] = (
                stats['requests_detected'] - stats['extractions_failed']
            ) / stats['requests_detected']
        else:
            stats['extraction_rate'] = 0.0
        
        return stats
    
    def list_recent_files(self, limit: int = 10) -> list:
        """
        Liste fichiers sauvegardés récents.
        
        Args:
            limit: Nombre max fichiers
            
        Returns:
            Liste dicts avec infos fichiers
        """
        return self.saver.list_saved_files(limit=limit)
    
    def get_status(self) -> dict:
        """
        Retourne état complet extension.
        
        Returns:
            Dict avec status, stats et fichiers récents
        """
        return {
            'status': 'operational',
            'uploads_dir': self.uploads_dir,
            'statistics': self.get_statistics(),
            'recent_files': self.list_recent_files(limit=5)
        }


if __name__ == "__main__":
    # Tests
    print("="*70)
    print("TEST FILE WRITER AGENT")
    print("="*70)
    
    agent = FileWriterAgent(
        uploads_dir="data/uploads",
        debug=True
    )
    
    # Test 1: Demande avec bloc code markdown
    print("\n" + "="*70)
    print("TEST 1: Demande avec bloc code markdown")
    print("="*70)
    
    user_msg1 = "écris-moi un .md sur les bonnes pratiques Python"
    ai_resp1 = """Voici le document sur les bonnes pratiques Python:

```md
# Bonnes Pratiques Python

## Introduction

Python est un langage qui valorise la lisibilité et la simplicité.

## Règles Essentielles

### 1. PEP 8
Suivre le guide de style officiel Python.

### 2. Nommage
- Variables: `snake_case`
- Classes: `PascalCase`
- Constantes: `UPPER_CASE`

### 3. Documentation
Utiliser des docstrings pour toutes les fonctions et classes.

## Conclusion

Respecter ces pratiques améliore la maintenabilité du code.
```

J'espère que ce document vous aide !"""
    
    path1 = agent.process_response(user_msg1, ai_resp1)
    print(f"\n📁 Résultat: {path1}")
    
    # Test 2: Demande avec markdown brut
    print("\n" + "="*70)
    print("TEST 2: Demande avec markdown brut")
    print("="*70)
    
    user_msg2 = "crée un fichier markdown pour la documentation API"
    ai_resp2 = """# Documentation API REST

## Vue d'ensemble

Cette API permet de gérer les utilisateurs et les ressources.

## Endpoints

### GET /users

Récupère la liste des utilisateurs.

**Paramètres:**
- `limit`: Nombre max de résultats (défaut: 10)
- `offset`: Position de départ (défaut: 0)

**Réponse:**
```json
{
  "users": [
    {"id": 1, "name": "Alice"},
    {"id": 2, "name": "Bob"}
  ]
}
```

### POST /users

Crée un nouvel utilisateur.

**Corps de la requête:**
```json
{
  "name": "Charlie",
  "email": "charlie@example.com"
}
```"""
    
    path2 = agent.process_response(user_msg2, ai_resp2)
    print(f"\n📁 Résultat: {path2}")
    
    # Test 3: Pas de demande
    print("\n" + "="*70)
    print("TEST 3: Pas de demande fichier")
    print("="*70)
    
    user_msg3 = "Salut Luna, comment ça va ?"
    ai_resp3 = "Salut ! Je vais bien, merci de demander ! 😊"
    
    path3 = agent.process_response(user_msg3, ai_resp3)
    print(f"\n📁 Résultat: {path3}")
    
    # Stats finales
    print("\n" + "="*70)
    print("STATISTIQUES FINALES")
    print("="*70)
    
    stats = agent.get_statistics()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    # Status complet
    print("\n" + "="*70)
    print("STATUS EXTENSION")
    print("="*70)
    
    status = agent.get_status()
    print(f"Status: {status['status']}")
    print(f"Uploads dir: {status['uploads_dir']}")
    print(f"\nFichiers récents:")
    for f in status['recent_files']:
        print(f"  - {f['name']} ({f['size']} bytes)")
