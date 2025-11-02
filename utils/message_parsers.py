"""
Module: message_parsers.py
Description: Parsers pour formats spéciaux dans messages IA
Extrait de: ogma_ng.py (lignes 2890-3012)
Date: 2025-11-02

Formats supportés:
- Thinking format: Format JSON complexe avec réflexions internes
- Introspection format: <introspection>dialogue</introspection>
"""

import re
import json
from typing import Tuple


def parse_thinking_format(content: str) -> Tuple[str, str]:
    """
    Parse le format thinking des IA qui retournent des structures JSON complexes.
    
    Format attendu: "[{'type': 'thinking', 'thinking': [...], {'type': 'text', 'text': '...'}]"
    
    Args:
        content: Contenu complet du message
        
    Returns:
        tuple[str, str]: (thinking_content, main_text)
        - thinking_content: Le contenu de réflexion interne (peut être vide)
        - main_text: Le texte principal à afficher
        
    Examples:
        >>> parse_thinking_format('[{"type":"thinking","thinking":[...]},{"type":"text","text":"Réponse"}]')
        ('Pensée interne...', 'Réponse')
    """
    # Si le contenu ne ressemble pas au format thinking, retourner tel quel
    # Gérer le cas où le JSON est entre guillemets
    test_content = content.strip()
    if test_content.startswith('"') and test_content.endswith('"'):
        test_content = test_content[1:-1]  # Enlever les guillemets de début/fin

    if not (test_content.startswith('[{') and 'thinking' in content):
        return "", content
    
    try:
        # Utiliser le contenu nettoyé (sans guillemets externes si présents)
        working_content = test_content

        print(f"[THINKING-PARSER] DEBUG Content original: {content[:100]}...")
        print(f"[THINKING-PARSER] DEBUG Content nettoyé: {working_content[:100]}...")

        # Tenter de corriger les guillemets simples en guillemets doubles pour JSON valide
        # Cette correction est nécessaire car les IA renvoient parfois des JSON malformés
        json_content = working_content
        
        # Remplacer les guillemets simples par des guillemets doubles dans les clés
        json_content = re.sub(r"'(type|thinking|text)':", r'"\1":', json_content)
        
        # Plus complexe : gérer les guillemets simples dans les valeurs qui peuvent contenir des apostrophes
        # On utilise une approche plus sûre en essayant d'abord le parsing direct
        try:
            data = json.loads(json_content)
        except json.JSONDecodeError:
            # Si ça échoue, on essaie de convertir tout avec ast.literal_eval (plus permissif)
            import ast
            try:
                data = ast.literal_eval(working_content)
            except (ValueError, SyntaxError):
                # Dernière tentative : retourner le contenu original
                return "", content
        
        thinking_parts = []
        text_parts = []
        
        # Parcourir la structure
        for item in data:
            if isinstance(item, dict):
                if item.get('type') == 'thinking' and 'thinking' in item:
                    # Extraire le contenu thinking
                    thinking_data = item['thinking']
                    if isinstance(thinking_data, list):
                        for thinking_item in thinking_data:
                            if isinstance(thinking_item, dict) and thinking_item.get('type') == 'text':
                                thinking_parts.append(thinking_item.get('text', ''))
                    elif isinstance(thinking_data, str):
                        thinking_parts.append(thinking_data)
                        
                elif item.get('type') == 'text' and 'text' in item:
                    # Extraire le texte principal
                    text_parts.append(item['text'])
        
        thinking_content = '\n'.join(thinking_parts).strip()
        main_text = '\n'.join(text_parts).strip()
        
        print(f"[THINKING-PARSER] OK Parsing réussi - Thinking: {len(thinking_content)} chars, Text: {len(main_text)} chars")
        return thinking_content, main_text
        
    except Exception as e:
        print(f"[THINKING-PARSER] WARN Erreur parsing format thinking: {e}")
        # En cas d'erreur, retourner le contenu original
        return "", content


def parse_introspection_format(content: str) -> Tuple[str, str]:
    """
    Parse le format introspection pour les dialogues Subconscience Luna-Archiviste.
    
    Format attendu: "<introspection>dialogue Luna-Archiviste</introspection>"
    
    Args:
        content: Contenu complet du message avec balises introspection
        
    Returns:
        tuple[str, str]: (introspection_content, main_text)
        - introspection_content: Le contenu du dialogue subconscient (peut être vide)
        - main_text: Le texte principal restant à afficher
        
    Examples:
        >>> parse_introspection_format("<introspection>Dialogue interne</introspection>\\nRéponse")
        ('Dialogue interne', 'Réponse')
    """
    # Si pas de balises introspection, retourner tel quel
    if '<introspection>' not in content or '</introspection>' not in content:
        return "", content
    
    try:
        # Pattern pour extraire le contenu entre les balises
        pattern = r'<introspection>(.*?)</introspection>'
        match = re.search(pattern, content, re.DOTALL)
        
        if match:
            introspection_content = match.group(1).strip()
            # Supprimer les balises introspection du contenu principal
            main_content = re.sub(pattern, '', content, flags=re.DOTALL).strip()
            
            print(f"[INTROSPECTION-PARSER] OK Parsing réussi - Introspection: {len(introspection_content)} chars, Text: {len(main_content)} chars")
            return introspection_content, main_content
        else:
            # Balises trouvées mais pattern invalide
            print("[INTROSPECTION-PARSER] WARN Balises introspection malformées")
            return "", content
            
    except Exception as e:
        print(f"[INTROSPECTION-PARSER] WARN Erreur parsing format introspection: {e}")
        # En cas d'erreur, retourner le contenu original
        return "", content
