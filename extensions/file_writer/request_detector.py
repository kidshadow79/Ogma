#!/usr/bin/env python3
"""
🔍 REQUEST DETECTOR - Détection demandes création fichiers .md
===============================================================

Détecte dans les messages utilisateur les demandes de création de documents
markdown via patterns regex.

PATTERNS DÉTECTÉS:
- "écris-moi un .md sur..."
- "crée un document markdown..."
- "rédige un fichier .md..."
- "génère un .md pour..."
- "fais-moi un markdown de..."
- "écris un fichier markdown qui..."

USAGE:
    detector = RequestDetector(debug=True)
    
    if detector.is_file_request("écris-moi un .md sur Python"):
        title = detector.extract_title("écris-moi un .md sur Python")
        # title = "Python"
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class FileRequest:
    """Résultat détection demande fichier."""
    is_request: bool
    title: Optional[str] = None
    extension: str = "md"
    confidence: float = 0.0
    pattern_matched: Optional[str] = None


class RequestDetector:
    """Détecteur de demandes création fichiers markdown."""
    
    def __init__(self, debug: bool = False):
        """
        Initialise le détecteur.
        
        Args:
            debug: Active logs debug
        """
        self.debug = debug
        
        # Patterns détection demandes .md
        self.patterns = [
            # Pattern commande slash
            (r'^/doc\s+', 0.98),
            
            # Pattern explicite .md
            (r'\b(?:écris|rédige|crée|génère|fais)(?:-moi|-nous)?\s+(?:un|le)\s+(?:fichier\s+)?\.md\b', 0.95),
            (r'\b(?:écris|rédige|crée|génère|fais)(?:-moi|-nous)?\s+(?:un|le)\s+fichier\s+markdown\b', 0.9),
            (r'\b(?:écris|rédige|crée|génère|fais)(?:-moi|-nous)?\s+(?:un|le)\s+document\s+(?:markdown|\.md)\b', 0.9),
            
            # Pattern avec "markdown" seul
            (r'\b(?:écris|rédige|crée|génère|fais)(?:-moi|-nous)?\s+(?:un|le)\s+markdown\s+(?:sur|pour|de|qui)\b', 0.85),
            
            # Pattern avec "doc" ou "fichier"
            (r'\b(?:écris|rédige|crée|génère|fais)(?:-moi|-nous)?\s+(?:un|le)\s+doc(?:ument)?\s+(?:sur|pour|de|qui)\b', 0.7),
            (r'\b(?:écris|rédige|crée|génère|fais)(?:-moi|-nous)?\s+(?:un|le)\s+fichier\s+(?:sur|pour|de|qui)\b', 0.75),
        ]
        
        # Patterns extraction titre
        self.title_patterns = [
            # Pattern /doc (tout ce qui suit)
            r'^/doc\s+(.+?)(?:\s*$|[.,;!?])',
            # Après "sur"
            r'(?:\.md|markdown|fichier|document)\s+sur\s+(.+?)(?:\s*$|[.,;!?])',
            # Après "pour"
            r'(?:\.md|markdown|fichier|document)\s+pour\s+(.+?)(?:\s*$|[.,;!?])',
            # Après "de"
            r'(?:\.md|markdown|fichier|document)\s+de\s+(.+?)(?:\s*$|[.,;!?])',
            # Après "qui"
            r'(?:\.md|markdown|fichier|document)\s+qui\s+(.+?)(?:\s*$|[.,;!?])',
            # Entre guillemets
            r'["\'](.+?)["\']',
        ]
    
    def detect(self, message: str) -> FileRequest:
        """
        Détecte si le message contient une demande de création fichier.
        
        Args:
            message: Message utilisateur
            
        Returns:
            FileRequest avec résultats détection
        """
        if not message or not isinstance(message, str):
            return FileRequest(is_request=False)
        
        message_lower = message.lower()
        
        # Tester patterns
        for pattern, confidence in self.patterns:
            if match := re.search(pattern, message_lower, re.IGNORECASE):
                if self.debug:
                    print(f"[DETECTOR] Pattern matched: {pattern}")
                    print(f"[DETECTOR] Confidence: {confidence}")
                
                # Extraire titre
                title = self._extract_title(message)
                
                return FileRequest(
                    is_request=True,
                    title=title,
                    extension="md",
                    confidence=confidence,
                    pattern_matched=pattern
                )
        
        return FileRequest(is_request=False)
    
    def is_file_request(self, message: str) -> bool:
        """
        Check rapide si message est demande fichier.
        
        Args:
            message: Message utilisateur
            
        Returns:
            True si demande détectée
        """
        result = self.detect(message)
        return result.is_request
    
    def extract_title(self, message: str) -> Optional[str]:
        """
        Extrait le titre depuis message utilisateur.
        
        Args:
            message: Message utilisateur
            
        Returns:
            Titre extrait ou None
        """
        return self._extract_title(message)
    
    def _extract_title(self, message: str) -> Optional[str]:
        """
        Extrait titre via patterns regex.
        
        Args:
            message: Message utilisateur
            
        Returns:
            Titre nettoyé ou None
        """
        # Essayer chaque pattern
        for pattern in self.title_patterns:
            if match := re.search(pattern, message, re.IGNORECASE):
                title = match.group(1).strip()
                
                # Nettoyer titre
                title = self._clean_title(title)
                
                if title:
                    if self.debug:
                        print(f"[DETECTOR] Titre extrait: '{title}'")
                    return title
        
        # Fallback: utiliser fin du message (max 50 chars)
        words = message.split()
        if len(words) > 3:
            fallback = " ".join(words[-5:])  # 5 derniers mots
            fallback = self._clean_title(fallback)
            if len(fallback) <= 50:
                if self.debug:
                    print(f"[DETECTOR] Titre fallback: '{fallback}'")
                return fallback
        
        return "document"
    
    def _clean_title(self, title: str) -> str:
        """
        Nettoie titre pour utilisation nom fichier.
        
        Args:
            title: Titre brut
            
        Returns:
            Titre nettoyé (safe pour filesystem)
        """
        if not title:
            return ""
        
        # Retirer ponctuations
        title = re.sub(r'[^\w\s\-_àâäéèêëïîôùûüÿç]', '', title, flags=re.UNICODE)
        
        # Remplacer espaces par underscores
        title = re.sub(r'\s+', '_', title.strip())
        
        # Limiter longueur
        if len(title) > 50:
            title = title[:50]
        
        # Retirer underscores multiples
        title = re.sub(r'_+', '_', title)
        
        # Retirer underscores début/fin
        title = title.strip('_')
        
        return title.lower()


if __name__ == "__main__":
    # Tests
    detector = RequestDetector(debug=True)
    
    test_messages = [
        "écris-moi un .md sur les bonnes pratiques Python",
        "crée un fichier markdown qui explique Git",
        "rédige un document .md pour la documentation API",
        "génère un markdown de guide utilisateur",
        "fais-moi un doc sur React",
        "salut Luna, comment ça va ?",  # Pas une demande
    ]
    
    for msg in test_messages:
        print(f"\n📝 Message: '{msg}'")
        result = detector.detect(msg)
        if result.is_request:
            print(f"✅ Demande détectée")
            print(f"   Titre: {result.title}")
            print(f"   Confidence: {result.confidence}")
        else:
            print(f"⚪ Pas de demande")
