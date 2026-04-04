"""
project_chunker.py
------------------
Découpage adaptatif de documents par type de fichier.
Implémente le pattern Parent Document Retrieval :
- Petit chunk (~200 tokens) pour recherche FAISS précise
- Chunk parent (~800 tokens) pour injection LLM riche en contexte
"""

import re
import ast
from typing import List, Dict, Any, Optional


# Approximation : 1 token ~ 4 caractères en français/anglais
CHARS_PER_TOKEN = 4


def _token_estimate(text: str) -> int:
    """Estimation du nombre de tokens (approximatif)."""
    return len(text) // CHARS_PER_TOKEN


def _split_into_sentences(text: str) -> List[str]:
    """Découpe un texte en phrases."""
    # Split sur . ! ? suivi d'espace ou fin de ligne
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]


def _build_chunks_with_parents(
    segments: List[str],
    small_size: int = 200,
    parent_size: int = 800,
    overlap: int = 50,
) -> List[Dict[str, Any]]:
    """
    Construit des paires (petit chunk, chunk parent) à partir de segments de texte.

    Le petit chunk sert à la recherche FAISS (précision).
    Le chunk parent sert à l'injection LLM (contexte riche).

    Args:
        segments: Liste de phrases ou blocs de texte
        small_size: Taille cible du petit chunk en tokens
        parent_size: Taille cible du chunk parent en tokens
        overlap: Chevauchement entre chunks en tokens

    Returns:
        Liste de dicts {'chunk_index', 'text_small', 'text_parent'}
    """
    if not segments:
        return []

    # Étape 1 : assembler les segments en blocs de taille parent
    parent_chunks = []
    current_parent = []
    current_parent_tokens = 0

    for seg in segments:
        seg_tokens = _token_estimate(seg)
        if current_parent_tokens + seg_tokens > parent_size and current_parent:
            parent_chunks.append(" ".join(current_parent))
            # Overlap : garder les derniers segments
            overlap_text = []
            overlap_tokens = 0
            for s in reversed(current_parent):
                st = _token_estimate(s)
                if overlap_tokens + st > overlap:
                    break
                overlap_text.insert(0, s)
                overlap_tokens += st
            current_parent = overlap_text
            current_parent_tokens = overlap_tokens
        current_parent.append(seg)
        current_parent_tokens += seg_tokens

    if current_parent:
        parent_chunks.append(" ".join(current_parent))

    # Étape 2 : pour chaque parent, créer des petits chunks
    results = []
    chunk_index = 0

    for parent_text in parent_chunks:
        parent_sentences = _split_into_sentences(parent_text)
        small_chunks = []
        current_small = []
        current_small_tokens = 0

        for sent in parent_sentences:
            sent_tokens = _token_estimate(sent)
            if current_small_tokens + sent_tokens > small_size and current_small:
                small_chunks.append(" ".join(current_small))
                current_small = []
                current_small_tokens = 0
            current_small.append(sent)
            current_small_tokens += sent_tokens

        if current_small:
            small_chunks.append(" ".join(current_small))

        # Si pas de small chunks, utiliser le parent directement
        if not small_chunks:
            small_chunks = [parent_text]

        for small_text in small_chunks:
            results.append({
                'chunk_index': chunk_index,
                'text_small': small_text.strip(),
                'text_parent': parent_text.strip(),
            })
            chunk_index += 1

    return results


# === Chunkers spécialisés par type ===

def chunk_text(text: str, small_size: int = 200, parent_size: int = 800,
               overlap: int = 50) -> List[Dict[str, Any]]:
    """
    Chunking générique pour texte brut / PDF / DOCX.
    Découpe par phrases puis construit les paires small/parent.
    """
    if not text or not text.strip():
        return []

    sentences = _split_into_sentences(text)
    if not sentences:
        # Fallback : découpe par lignes
        sentences = [line.strip() for line in text.split('\n') if line.strip()]

    return _build_chunks_with_parents(sentences, small_size, parent_size, overlap)


def chunk_markdown(text: str, small_size: int = 200, parent_size: int = 800,
                   overlap: int = 50) -> List[Dict[str, Any]]:
    """
    Chunking pour Markdown : découpe par sections (headers).
    Chaque section # ou ## devient un segment naturel.
    """
    if not text or not text.strip():
        return []

    # Découper par headers (lignes commençant par #)
    sections = []
    current_section = []

    for line in text.split('\n'):
        if re.match(r'^#{1,4}\s', line) and current_section:
            sections.append('\n'.join(current_section))
            current_section = [line]
        else:
            current_section.append(line)

    if current_section:
        sections.append('\n'.join(current_section))

    # Si sections trop grosses, subdiviser en phrases
    segments = []
    for section in sections:
        if _token_estimate(section) > parent_size:
            # Section trop grosse, découper en phrases
            segments.extend(_split_into_sentences(section))
        else:
            segments.append(section)

    return _build_chunks_with_parents(segments, small_size, parent_size, overlap)


def chunk_python(text: str, small_size: int = 200, parent_size: int = 800,
                 overlap: int = 50) -> List[Dict[str, Any]]:
    """
    Chunking pour Python : découpe par fonction/classe via AST.
    Fallback sur découpe par lignes si le parsing échoue.
    """
    if not text or not text.strip():
        return []

    segments = []

    try:
        tree = ast.parse(text)
        lines = text.split('\n')

        # Extraire les définitions de fonctions et classes
        nodes = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
                    nodes.append((node.lineno, node.end_lineno, node.name))

        if nodes:
            # Trier par numéro de ligne
            nodes.sort(key=lambda x: x[0])

            # Code avant la première définition
            if nodes[0][0] > 1:
                header = '\n'.join(lines[:nodes[0][0] - 1]).strip()
                if header:
                    segments.append(header)

            # Chaque fonction/classe comme segment
            for start, end, name in nodes:
                block = '\n'.join(lines[start - 1:end]).strip()
                if block:
                    segments.append(block)
        else:
            # Pas de fonctions/classes : traiter comme du texte
            segments = [line for line in text.split('\n') if line.strip()]

    except SyntaxError:
        # Parsing AST échoué : fallback sur découpe par blocs vides
        blocks = re.split(r'\n\s*\n', text)
        segments = [b.strip() for b in blocks if b.strip()]

    if not segments:
        segments = [text]

    return _build_chunks_with_parents(segments, small_size, parent_size, overlap)


def chunk_code(text: str, small_size: int = 200, parent_size: int = 800,
               overlap: int = 50) -> List[Dict[str, Any]]:
    """
    Chunking générique pour code (JS, TS, Java, etc.).
    Découpe par blocs séparés par lignes vides.
    """
    if not text or not text.strip():
        return []

    # Découpe par doubles sauts de ligne (blocs logiques)
    blocks = re.split(r'\n\s*\n', text)
    segments = [b.strip() for b in blocks if b.strip()]

    if not segments:
        segments = [text]

    return _build_chunks_with_parents(segments, small_size, parent_size, overlap)


# === Dispatcher ===

# Extensions reconnues par type de chunker
FILE_TYPE_MAP = {
    # Texte brut
    '.txt': chunk_text,
    '.pdf': chunk_text,
    '.docx': chunk_text,
    '.csv': chunk_text,
    '.log': chunk_text,
    # Markdown
    '.md': chunk_markdown,
    # Python
    '.py': chunk_python,
    # Code générique
    '.js': chunk_code,
    '.ts': chunk_code,
    '.jsx': chunk_code,
    '.tsx': chunk_code,
    '.java': chunk_code,
    '.c': chunk_code,
    '.cpp': chunk_code,
    '.h': chunk_code,
    '.hpp': chunk_code,
    '.cs': chunk_code,
    '.go': chunk_code,
    '.rs': chunk_code,
    '.rb': chunk_code,
    '.php': chunk_code,
    '.html': chunk_code,
    '.css': chunk_code,
    '.xml': chunk_code,
    '.yaml': chunk_code,
    '.yml': chunk_code,
    '.json': chunk_code,
    '.sql': chunk_code,
    '.sh': chunk_code,
    '.bash': chunk_code,
    '.ps1': chunk_code,
    '.bat': chunk_code,
    '.toml': chunk_code,
    '.ini': chunk_code,
    '.cfg': chunk_code,
    '.conf': chunk_code,
}


def chunk_file(text: str, file_extension: str,
               small_size: int = 200, parent_size: int = 800,
               overlap: int = 50) -> List[Dict[str, Any]]:
    """
    Point d'entrée principal : découpe un fichier selon son type.

    Args:
        text: Contenu textuel du fichier
        file_extension: Extension avec point (.py, .md, .txt, etc.)
        small_size: Taille cible petit chunk en tokens
        parent_size: Taille cible chunk parent en tokens
        overlap: Chevauchement en tokens

    Returns:
        Liste de dicts {'chunk_index', 'text_small', 'text_parent'}
    """
    ext = file_extension.lower()
    chunker = FILE_TYPE_MAP.get(ext, chunk_text)  # Fallback sur texte brut

    chunks = chunker(text, small_size, parent_size, overlap)

    print(f"[PROJECT-CHUNKER] {ext} -> {len(chunks)} chunks "
          f"(small={small_size}, parent={parent_size}, overlap={overlap})")

    return chunks
