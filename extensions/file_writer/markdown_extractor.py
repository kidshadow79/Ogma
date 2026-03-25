#!/usr/bin/env python3
"""
📄 MARKDOWN EXTRACTOR - Extraction contenu markdown depuis réponses IA
=======================================================================

Extrait blocs markdown depuis réponses Luna, avec support:
- Blocs code markdown (```md ... ```)
- Contenu brut markdown (headers, listes, etc.)
- Nettoyage formatage excessif

USAGE:
    extractor = MarkdownExtractor(debug=True)
    
    response = "Voici le document:\n```md\n# Titre\nContenu\n```"
    content = extractor.extract(response)
    # content = "# Titre\nContenu"
"""

import re
from typing import Optional


class MarkdownExtractor:
    """Extracteur de contenu markdown depuis réponses IA."""
    
    def __init__(self, debug: bool = False):
        """
        Initialise l'extracteur.
        
        Args:
            debug: Active logs debug
        """
        self.debug = debug
    
    def extract(self, ai_response: str) -> Optional[str]:
        """
        Extrait contenu markdown depuis réponse IA.
        
        Stratégie:
        1. Chercher blocs code markdown (```md ou ```markdown)
        2. Si pas trouvé, extraire contenu brut markdown
        3. Nettoyer contenu extrait
        
        Args:
            ai_response: Réponse IA complète
            
        Returns:
            Contenu markdown extrait ou None
        """
        if not ai_response or not isinstance(ai_response, str):
            return None
        
        # 1. Tentative extraction bloc code markdown
        md_content = self._extract_code_block(ai_response)
        
        if md_content:
            if self.debug:
                print(f"[EXTRACTOR] Bloc code markdown trouvé ({len(md_content)} chars)")
            return md_content
        
        # 2. Fallback: extraire contenu brut si contient syntaxe markdown
        if self._looks_like_markdown(ai_response):
            md_content = self._extract_raw_markdown(ai_response)
            if md_content:
                if self.debug:
                    print(f"[EXTRACTOR] Contenu markdown brut extrait ({len(md_content)} chars)")
                return md_content
        
        if self.debug:
            print("[EXTRACTOR] Aucun contenu markdown détecté")
        
        return None
    
    def _extract_code_block(self, text: str) -> Optional[str]:
        """
        Extrait contenu depuis blocs code markdown.
        
        Patterns:
        - ```md\n...\n```
        - ```markdown\n...\n```
        
        IMPORTANT: Gère les blocs de code imbriqués (```python, ```json, etc.)
        en comptant les ouvertures/fermetures de blocs.
        
        Args:
            text: Texte source
            
        Returns:
            Contenu bloc ou None
        """
        # Chercher le début du bloc markdown
        start_patterns = [
            (r'```md\s*\n', 'md'),
            (r'```markdown\s*\n', 'markdown'),
        ]
        
        for start_pattern, block_type in start_patterns:
            match = re.search(start_pattern, text, re.IGNORECASE)
            if match:
                start_pos = match.end()
                
                # Trouver la fin du bloc en comptant les niveaux de blocs imbriqués
                content = self._find_matching_end(text[start_pos:])
                
                if content:
                    if self.debug:
                        print(f"[EXTRACTOR] Bloc {block_type} extrait: {len(content)} chars")
                    return content.strip()
        
        return None
    
    def _find_matching_end(self, text: str) -> Optional[str]:
        """
        Trouve la fin du bloc markdown en gérant les blocs imbriqués.
        
        Compte les ``` d'ouverture et de fermeture pour trouver le bon ```.
        
        Args:
            text: Texte après l'ouverture ```markdown
            
        Returns:
            Contenu jusqu'au ``` de fermeture correspondant
        """
        lines = text.split('\n')
        result_lines = []
        depth = 0  # Compteur de profondeur des blocs imbriqués
        
        for line in lines:
            stripped = line.strip()
            
            # Vérifier si c'est une ouverture de bloc (```quelquechose ou ``` seul au milieu)
            if stripped.startswith('```') and len(stripped) > 3:
                # Ouverture d'un bloc imbriqué (```python, ```json, etc.)
                depth += 1
                result_lines.append(line)
            elif stripped == '```':
                if depth > 0:
                    # Fermeture d'un bloc imbriqué
                    depth -= 1
                    result_lines.append(line)
                else:
                    # C'est notre fermeture finale - on s'arrête ici
                    break
            else:
                result_lines.append(line)
        
        if result_lines:
            return '\n'.join(result_lines)
        
        return None
    
    def _looks_like_markdown(self, text: str) -> bool:
        """
        Vérifie si texte contient syntaxe markdown.
        
        Indicateurs:
        - Headers (#, ##, ###)
        - Listes (-, *, 1.)
        - Links ([text](url))
        - Code inline (`code`)
        - Bold/Italic (**, __)
        
        Args:
            text: Texte à analyser
            
        Returns:
            True si contient markdown
        """
        markdown_indicators = [
            r'^#{1,6}\s+\w+',  # Headers
            r'^\s*[-*+]\s+\w+',  # Listes non ordonnées
            r'^\s*\d+\.\s+\w+',  # Listes ordonnées
            r'\[.+?\]\(.+?\)',  # Links
            r'`[^`]+`',  # Code inline
            r'\*\*.+?\*\*',  # Bold
            r'__.+?__',  # Bold alt
        ]
        
        for pattern in markdown_indicators:
            if re.search(pattern, text, re.MULTILINE):
                return True
        
        return False
    
    def _extract_raw_markdown(self, text: str) -> Optional[str]:
        """
        Extrait contenu markdown brut (sans bloc code).
        
        Stratégie:
        - Détecter première ligne markdown (header, liste)
        - Extraire jusqu'à fin ou ligne vide multiple
        
        Args:
            text: Texte source
            
        Returns:
            Contenu markdown ou None
        """
        lines = text.split('\n')
        
        # Trouver début contenu markdown
        start_idx = None
        for i, line in enumerate(lines):
            stripped = line.strip()
            # Headers
            if re.match(r'^#{1,6}\s+\w+', stripped):
                start_idx = i
                break
            # Listes
            if re.match(r'^[-*+]\s+\w+', stripped) or re.match(r'^\d+\.\s+\w+', stripped):
                start_idx = i
                break
        
        if start_idx is None:
            return None
        
        # Extraire jusqu'à fin ou lignes vides multiples
        content_lines = []
        empty_count = 0
        
        for line in lines[start_idx:]:
            if line.strip():
                content_lines.append(line)
                empty_count = 0
            else:
                empty_count += 1
                # Stopper après 3 lignes vides consécutives
                if empty_count >= 3:
                    break
                content_lines.append(line)
        
        content = '\n'.join(content_lines).strip()
        
        # Validation minimale (au moins 50 chars)
        if len(content) < 50:
            return None
        
        return content
    
    def clean_content(self, content: str) -> str:
        """
        Nettoie contenu markdown extrait.
        
        - Retire lignes vides excessives
        - Normalise indentation
        - Retire espaces trailing
        
        Args:
            content: Contenu brut
            
        Returns:
            Contenu nettoyé
        """
        if not content:
            return ""
        
        lines = content.split('\n')
        
        # Retirer trailing whitespace
        lines = [line.rstrip() for line in lines]
        
        # Réduire lignes vides multiples à 2 max
        cleaned_lines = []
        empty_count = 0
        
        for line in lines:
            if line.strip():
                cleaned_lines.append(line)
                empty_count = 0
            else:
                if empty_count < 2:
                    cleaned_lines.append(line)
                empty_count += 1
        
        return '\n'.join(cleaned_lines).strip()


if __name__ == "__main__":
    # Tests
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
    
    print("TEST 1: Bloc code markdown")
    content1 = extractor.extract(response1)
    print(f"Extrait: {content1}\n")
    
    # Test 2: Markdown brut
    response2 = """# Documentation API

## Endpoints

### GET /users

Récupère la liste des utilisateurs.

**Paramètres:**
- `limit`: Nombre max résultats
- `offset`: Position départ

**Réponse:**
```json
{"users": [...]}
```"""
    
    print("\nTEST 2: Markdown brut")
    content2 = extractor.extract(response2)
    print(f"Extrait: {content2[:200]}...")
    
    # Test 3: Pas de markdown
    response3 = "Salut ! Comment ça va ? Tout va bien de mon côté."
    
    print("\n\nTEST 3: Pas de markdown")
    content3 = extractor.extract(response3)
    print(f"Extrait: {content3}")
