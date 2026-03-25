#!/usr/bin/env python3
"""
📄 DOCUMENT GENERATOR - Génération directe de documents markdown
=================================================================

Génère le contenu markdown directement via un appel IA dédié,
sans passer par l'extraction depuis la réponse conversationnelle.

AVANTAGES:
- Économie de tokens (pas de double affichage)
- Pas de troncature (génération directe vers fichier)
- Meilleure qualité (prompt dédié documentation)
- UX améliorée (réponse rapide + fichier complet en background)

WORKFLOW:
1. L'IA répond brièvement ("Je crée le document...")
2. Appel IA ASYNCHRONE génère le contenu complet en background
3. Notification utilisateur quand fichier prêt

USAGE:
    from extensions.file_writer.document_generator import DocumentGenerator
    
    generator = DocumentGenerator(ai_controller, debug=True)
    
    # Lancer génération asynchrone
    asyncio.create_task(generator.generate_and_save_async(
        user_request="crée un doc sur Python",
        title="guide_python",
        context="souvenirs et mémoire...",
        conversation_history=[...],
        on_complete=callback_function
    ))
"""

import asyncio
import re
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Callable, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from core_logic import AIController

# Prompt système pour génération de documentation
DOCUMENT_GENERATION_SYSTEM = """Tu es un expert en rédaction technique et documentation.
Tu dois créer un document markdown COMPLET, PROFESSIONNEL et EXHAUSTIF.

RÈGLES STRICTES:
1. Commence DIRECTEMENT par le titre principal (# Titre)
2. Structure claire avec sections (##) et sous-sections (###)
3. Utilise listes, tableaux, blocs code quand pertinent
4. Contenu EXHAUSTIF et DÉTAILLÉ - ne résume pas, développe !
5. Inclus exemples pratiques, code commenté si applicable
6. Ne mets AUCUN texte avant le titre # ou après la conclusion
7. PAS de bloc ```markdown au début - écris directement le contenu markdown
8. Minimum 3000 caractères pour un document de qualité

FORMAT ATTENDU:
# Titre Principal

## Introduction
Contexte et objectifs...

## Section 1
Contenu détaillé avec exemples...

## Section 2  
Contenu détaillé avec exemples...

## Conclusion
Synthèse et points clés."""


class DocumentGenerator:
    """Générateur de documents markdown via appel IA dédié (asynchrone)."""
    
    def __init__(
        self,
        ai_controller: "AIController" = None,
        downloads_dir: str = "data/downloads",
        debug: bool = False
    ):
        """
        Initialise le générateur.
        
        Args:
            ai_controller: Contrôleur IA pour génération
            downloads_dir: Répertoire de sauvegarde (data/downloads)
            debug: Active logs debug
        """
        self.ai_controller = ai_controller
        self.downloads_dir = Path(downloads_dir)
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
        self.debug = debug
        
        # Stats
        self._stats = {
            'documents_generated': 0,
            'total_chars': 0,
            'generation_errors': 0,
            'save_errors': 0
        }
        
        # Tâches en cours
        self._pending_tasks: List[asyncio.Task] = []
        
        if self.debug:
            print(f"[DOC-GENERATOR] ✅ Initialisé - Répertoire: {self.downloads_dir}")
    
    def set_controller(self, ai_controller: "AIController"):
        """Configure le contrôleur IA."""
        self.ai_controller = ai_controller
        if self.debug:
            print("[DOC-GENERATOR] 🔗 Contrôleur IA configuré")
    
    async def generate_and_save_async(
        self,
        user_request: str,
        title: str,
        context: str = "",
        conversation_history: List[Dict] = None,
        on_complete: Callable[[str, str], None] = None,
        on_error: Callable[[str], None] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Génère et sauvegarde un document markdown de façon ASYNCHRONE.
        
        Cette méthode est conçue pour être lancée en background via asyncio.create_task()
        pendant que l'IA répond brièvement à l'utilisateur.
        
        Args:
            user_request: Demande originale de l'utilisateur
            title: Titre pour le nom de fichier
            context: Contexte mémoire (souvenirs pertinents)
            conversation_history: Historique conversation pour contexte
            on_complete: Callback(content, path) appelé quand terminé
            on_error: Callback(error_msg) appelé en cas d'erreur
            
        Returns:
            Tuple (contenu_généré, chemin_fichier) ou (None, None) si erreur
        """
        if not self.ai_controller:
            error_msg = "Pas de contrôleur IA configuré"
            print(f"[DOC-GENERATOR] ❌ {error_msg}")
            if on_error:
                on_error(error_msg)
            return None, None
        
        try:
            print(f"[DOC-GENERATOR] 🚀 Génération asynchrone démarrée: {title}")
            
            # Construire le prompt complet avec tout le contexte
            generation_prompt = self._build_full_prompt(
                user_request=user_request,
                context=context,
                conversation_history=conversation_history
            )
            
            if self.debug:
                print(f"[DOC-GENERATOR] 📊 Prompt total: {len(generation_prompt)} chars")
            
            # Appel IA pour génération (bloquant mais dans une tâche async)
            content = await self._generate_content_async(generation_prompt, user_request)
            
            if not content:
                self._stats['generation_errors'] += 1
                error_msg = "Échec génération contenu"
                print(f"[DOC-GENERATOR] ❌ {error_msg}")
                if on_error:
                    on_error(error_msg)
                return None, None
            
            # Nettoyer le contenu
            content = self._clean_content(content)
            
            print(f"[DOC-GENERATOR] ✅ Contenu généré: {len(content)} chars")
            
            # Sauvegarder
            file_path = self._save_document(content, title)
            
            if file_path:
                self._stats['documents_generated'] += 1
                self._stats['total_chars'] += len(content)
                print(f"[DOC-GENERATOR] 💾 Document sauvegardé: {file_path}")
                
                if on_complete:
                    on_complete(content, str(file_path))
                
                return content, str(file_path)
            else:
                self._stats['save_errors'] += 1
                error_msg = "Erreur sauvegarde fichier"
                if on_error:
                    on_error(error_msg)
                return content, None
                
        except Exception as e:
            self._stats['generation_errors'] += 1
            error_msg = f"Erreur génération: {e}"
            print(f"[DOC-GENERATOR] ❌ {error_msg}")
            import traceback
            traceback.print_exc()
            if on_error:
                on_error(error_msg)
            return None, None
    
    def _build_full_prompt(
        self,
        user_request: str,
        context: str,
        conversation_history: List[Dict] = None
    ) -> str:
        """
        Construit le prompt complet avec TOUT le contexte disponible.
        
        Inclut:
        - Instructions de formatage
        - Demande utilisateur
        - Mémoire/souvenirs pertinents
        - Historique conversation récent
        """
        sections = []
        
        # Section demande utilisateur
        sections.append("=" * 60)
        sections.append("📝 DEMANDE DE L'UTILISATEUR:")
        sections.append(user_request)
        sections.append("=" * 60)
        
        # Section mémoire/contexte
        if context and context.strip():
            sections.append("")
            sections.append("🧠 MÉMOIRE ET CONNAISSANCES PERTINENTES:")
            sections.append(context)
            sections.append("")
        
        # Section historique conversation (dernier contexte)
        if conversation_history:
            # Prendre les 10 derniers messages pour contexte
            recent_history = conversation_history[-10:]
            if recent_history:
                sections.append("")
                sections.append("💬 CONTEXTE DE CONVERSATION RÉCENT:")
                for msg in recent_history:
                    role = "Utilisateur" if msg.get('role') == 'user' else "Assistant"
                    content = msg.get('content', '')[:500]  # Limiter longueur
                    if len(msg.get('content', '')) > 500:
                        content += "..."
                    sections.append(f"[{role}]: {content}")
                sections.append("")
        
        # Instructions finales
        sections.append("=" * 60)
        sections.append("🎯 MISSION: Génère maintenant le document markdown COMPLET et DÉTAILLÉ.")
        sections.append("Utilise TOUTES tes connaissances sur le sujet + le contexte fourni.")
        sections.append("Le document doit être exhaustif, bien structuré et professionnel.")
        sections.append("=" * 60)
        
        return "\n".join(sections)
    
    async def _generate_content_async(self, prompt: str, user_request: str) -> Optional[str]:
        """Appelle l'IA pour générer le contenu via call_chat_api."""
        try:
            # Messages pour l'IA
            messages = [
                {"role": "system", "content": DOCUMENT_GENERATION_SYSTEM},
                {"role": "user", "content": prompt}
            ]
            
            # Récupérer les paramètres du contrôleur
            max_tokens = getattr(self.ai_controller, 'max_tokens', 8192)
            context_length = getattr(self.ai_controller, 'context_length', 128000)
            temperature = getattr(self.ai_controller, 'temperature', 0.7)
            
            # Appel API async
            response, error = await self.ai_controller.call_chat_api(
                messages=messages,
                max_tokens=max_tokens,
                context_length=context_length,
                temperature=temperature,
                is_json=False
            )
            
            if error:
                print(f"[DOC-GENERATOR] ⚠️ Erreur API: {error}")
                return None
            
            return response
            
        except Exception as e:
            print(f"[DOC-GENERATOR] ❌ Erreur appel IA: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _clean_content(self, content: str) -> str:
        """Nettoie le contenu généré des artefacts markdown."""
        if not content:
            return ""
            
        content = content.strip()
        
        # Supprimer bloc ```markdown au début
        patterns_start = [
            r'^```markdown\s*\n?',
            r'^```md\s*\n?',
            r'^```\s*\n?'
        ]
        for pattern in patterns_start:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)
        
        # Supprimer ``` à la fin
        if content.rstrip().endswith("```"):
            content = content.rstrip()[:-3].rstrip()
        
        return content
    
    def _save_document(self, content: str, title: str) -> Optional[Path]:
        """Sauvegarde le document dans data/downloads."""
        try:
            # Nettoyer le titre pour nom de fichier
            safe_title = self._sanitize_filename(title)
            
            # Ajouter timestamp pour unicité
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Chemin de base
            file_path = self.downloads_dir / f"{safe_title}_{timestamp}.md"
            
            # Écrire le fichier
            file_path.write_text(content, encoding="utf-8")
            
            return file_path
            
        except Exception as e:
            print(f"[DOC-GENERATOR] ❌ Erreur sauvegarde: {e}")
            return None
    
    def _sanitize_filename(self, title: str) -> str:
        """Nettoie un titre pour en faire un nom de fichier valide."""
        # Remplacer caractères spéciaux
        safe = re.sub(r'[<>:"/\\|?*]', '', title)
        safe = re.sub(r'\s+', '_', safe)
        safe = re.sub(r'_+', '_', safe)
        safe = safe.strip('_').lower()
        
        # Limiter longueur
        if len(safe) > 40:
            safe = safe[:40]
        
        return safe or "document"
    
    def get_statistics(self) -> dict:
        """Retourne les statistiques de génération."""
        return self._stats.copy()
    
    def get_pending_count(self) -> int:
        """Retourne le nombre de générations en cours."""
        # Nettoyer les tâches terminées
        self._pending_tasks = [t for t in self._pending_tasks if not t.done()]
        return len(self._pending_tasks)


# Instance singleton
_document_generator: Optional[DocumentGenerator] = None


def get_document_generator(
    ai_controller: "AIController" = None,
    downloads_dir: str = "data/downloads",
    debug: bool = False
) -> DocumentGenerator:
    """
    Retourne l'instance singleton du générateur.
    
    Args:
        ai_controller: Contrôleur IA (optionnel, peut être set après)
        downloads_dir: Répertoire de sauvegarde
        debug: Mode debug
        
    Returns:
        Instance DocumentGenerator
    """
    global _document_generator
    
    if _document_generator is None:
        _document_generator = DocumentGenerator(
            ai_controller=ai_controller,
            downloads_dir=downloads_dir,
            debug=debug
        )
    elif ai_controller and not _document_generator.ai_controller:
        _document_generator.set_controller(ai_controller)
    
    return _document_generator


async def generate_document_async(
    user_request: str,
    title: str,
    ai_controller: "AIController",
    context: str = "",
    conversation_history: List[Dict] = None,
    downloads_dir: str = "data/downloads",
    on_complete: Callable[[str, str], None] = None,
    on_error: Callable[[str], None] = None,
    debug: bool = False
) -> Tuple[Optional[str], Optional[str]]:
    """
    Fonction utilitaire pour générer un document de façon asynchrone.
    
    Args:
        user_request: Demande utilisateur
        title: Titre du document  
        ai_controller: Contrôleur IA
        context: Contexte mémoire
        conversation_history: Historique conversation
        downloads_dir: Répertoire de sauvegarde
        on_complete: Callback succès
        on_error: Callback erreur
        debug: Mode debug
        
    Returns:
        Tuple (contenu, chemin_fichier)
    """
    generator = get_document_generator(
        ai_controller=ai_controller,
        downloads_dir=downloads_dir,
        debug=debug
    )
    
    return await generator.generate_and_save_async(
        user_request=user_request,
        title=title,
        context=context,
        conversation_history=conversation_history,
        on_complete=on_complete,
        on_error=on_error
    )
