"""
Utilitaire de nettoyage JSON pour OGMA
========================================

Nettoie les réponses IA qui contiennent des balises markdown
avant le parsing JSON.
"""

import json
import re
from typing import Any, Optional

def clean_json_response(response: str) -> str:
    """
    Nettoie une réponse IA pour extraction JSON.
    
    Supprime:
    - Balises markdown ```json ... ```
    - Commentaires // dans le JSON
    - Espaces avant/après
    - Caractères de contrôle non échappés dans les strings
    
    Args:
        response: Réponse brute de l'IA
        
    Returns:
        JSON nettoyé prêt pour parsing
    """
    if not response:
        return "{}"
    
    response_clean = response.strip()
    
    # Supprimer balises markdown si présentes
    if response_clean.startswith('```'):
        lines = response_clean.split('\n')
        # Retirer première ligne (```json) et dernière ligne (```)
        if len(lines) > 2:
            response_clean = '\n'.join(lines[1:-1])
        response_clean = response_clean.replace('```json', '').replace('```', '').strip()
    
    # Supprimer commentaires // (non valides en JSON)
    response_clean = re.sub(r'//.*$', '', response_clean, flags=re.MULTILINE)
    
    return response_clean.strip()


def _clean_control_characters(json_str: str) -> str:
    """
    Nettoie les caractères de contrôle non échappés UNIQUEMENT à l'intérieur des chaînes JSON.
    Remplace les newlines/tabs/carriage returns par des espaces dans les valeurs string.
    """
    result = []
    in_string = False
    escape_next = False
    
    for char in json_str:
        if escape_next:
            result.append(char)
            escape_next = False
            continue
        
        if char == '\\':
            escape_next = True
            result.append(char)
            continue
        
        if char == '"':
            in_string = not in_string
            result.append(char)
            continue
        
        # Si on est dans une chaîne, nettoyer les caractères de contrôle
        if in_string:
            if char == '\n':
                result.append(' ')  # Remplacer newline par espace
            elif char == '\r':
                pass  # Supprimer carriage return
            elif char == '\t':
                result.append(' ')  # Remplacer tab par espace
            elif ord(char) < 32:  # Autres caractères de contrôle
                pass  # Supprimer
            else:
                result.append(char)
        else:
            result.append(char)
    
    return ''.join(result)


def safe_json_parse(response: str, fallback: Optional[Any] = None) -> Any:
    """
    Parse JSON de manière sécurisée avec nettoyage automatique.
    
    Tentatives successives:
    1. Parse direct après nettoyage markdown
    2. Nettoyage des caractères de contrôle dans les strings
    3. Fallback regex agressif
    
    Args:
        response: Réponse brute de l'IA
        fallback: Valeur de secours en cas d'erreur (default: {})
        
    Returns:
        Objet Python parsé ou fallback
    """
    if fallback is None:
        fallback = {}
    
    try:
        cleaned = clean_json_response(response)
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        # Tentative 2: Nettoyer les caractères de contrôle dans les strings
        try:
            deep_cleaned = _clean_control_characters(cleaned)
            result = json.loads(deep_cleaned)
            print(f"[JSON-CLEANER] ✅ Parsing réussi après nettoyage caractères contrôle")
            return result
        except json.JSONDecodeError:
            pass
        
        # Tentative 3: Regex agressif - remplacer TOUS les newlines/tabs par espaces
        try:
            aggressive_cleaned = re.sub(r'[\n\r\t]', ' ', cleaned)
            result = json.loads(aggressive_cleaned)
            print(f"[JSON-CLEANER] ✅ Parsing réussi après nettoyage agressif")
            return result
        except json.JSONDecodeError:
            pass
        
        print(f"[JSON-CLEANER] ❌ Erreur parsing: {e}")
        print(f"[JSON-CLEANER] Réponse nettoyée: {cleaned[:200]}...")
        return fallback
    except Exception as e:
        print(f"[JSON-CLEANER] ❌ Erreur inattendue: {e}")
        return fallback
