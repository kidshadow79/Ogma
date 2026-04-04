"""
project_injector.py
-------------------
Hook d'injection dans le pipeline de chat OGMA.
Quand le projet est actif :
  - L'instruction projet remplace persistent_context.txt
  - 3 chunks pertinents sont ajoutés au contexte
"""

from typing import List, Dict, Any, Optional


class ProjectInjector:
    """
    Génère le contexte projet à injecter dans les messages système.
    Appelé par ogma_ng.py avant l'envoi au LLM.
    """

    def __init__(self, config, retriever):
        """
        Args:
            config: Instance ProjectConfig
            retriever: Instance ProjectRetriever
        """
        self.config = config
        self.retriever = retriever

    def is_active(self) -> bool:
        """Vérifie si le projet est activé."""
        return self.config.active

    def get_instruction(self) -> str:
        """
        Retourne l'instruction projet (remplace persistent_context).
        Si vide, retourne une chaîne vide (le persistent_context normal sera utilisé).
        """
        if not self.config.active:
            return ""
        return self.config.instruction or ""

    async def get_context_for_message(self, user_message: str) -> Optional[str]:
        """
        Génère le contexte projet complet à injecter.

        Args:
            user_message: Message de l'utilisateur

        Returns:
            Texte formaté à injecter comme message système, ou None si inactif
        """
        if not self.config.active:
            return None

        parts = []

        # 1. Instruction projet (si renseignée)
        instruction = self.config.instruction
        if instruction and instruction.strip():
            parts.append(f"[PROJET: {self.config.name}]\n{instruction.strip()}")

        # 2. Chunks pertinents (recherche sémantique)
        try:
            chunks = await self.retriever.search(user_message)
            if chunks:
                chunks_text = self._format_chunks(chunks)
                parts.append(chunks_text)
        except Exception as e:
            print(f"[PROJECT-INJECTOR] Erreur recherche chunks: {e}")

        if not parts:
            return None

        return "\n\n".join(parts)

    def _format_chunks(self, chunks: List[Dict[str, Any]]) -> str:
        """Formate les chunks pour l'injection dans le prompt."""
        if not chunks:
            return ""

        lines = [
            "[DOCUMENTS PROJET - Extraits pertinents]",
            "IMPORTANT: Ces extraits proviennent de documents réels indexés dans ce projet. "
            "Ils constituent ta SOURCE PRIMAIRE d'information. Utilise-les PRIORITAIREMENT "
            "avant tes connaissances générales. Si les extraits parlent d'une personne, "
            "ces données la concernent directement.",
        ]

        for i, chunk in enumerate(chunks, 1):
            filename = chunk.get('filename', 'inconnu')
            score = chunk.get('score', 0)
            text = chunk.get('text_parent', chunk.get('text_small', ''))

            # Tronquer si trop long (sécurité)
            max_chars = 2000
            if len(text) > max_chars:
                text = text[:max_chars] + "..."

            lines.append(f"\n--- Extrait {i} (source: {filename}, pertinence: {score:.0%}) ---")
            lines.append(text)

        return "\n".join(lines)

    async def get_override_persistent_context(self, user_message: str) -> Optional[str]:
        """
        Point d'entrée principal pour ogma_ng.py.
        Retourne le contexte complet qui REMPLACE persistent_context.txt.

        Si le projet n'est pas actif ou n'a pas d'instruction, retourne None
        (= utiliser le persistent_context normal).

        Args:
            user_message: Dernier message de l'utilisateur

        Returns:
            Texte de remplacement ou None
        """
        if not self.is_active():
            return None

        return await self.get_context_for_message(user_message)
