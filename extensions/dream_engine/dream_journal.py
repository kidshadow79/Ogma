"""
Dream Engine - Journal des Rêves
=================================

Gestion des journaux de rêves :
- journal_reves.md : Format humain-lisible (illustration + récit + analyse)
- journal_reves.json : Format IA-queryable (date, titre, rêve, analyse)
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import json


class DreamJournal:
    """Gestionnaire des journaux de rêves."""
    
    def __init__(self):
        self._data_dir = Path(__file__).parent.parent.parent / 'data'
        self._md_file = self._data_dir / 'journal_reves.md'
        self._json_file = self._data_dir / 'journal_reves.json'
        
        # Créer les fichiers s'ils n'existent pas
        self._ensure_files()
    
    def _ensure_files(self):
        """Crée les fichiers de journal s'ils n'existent pas."""
        self._data_dir.mkdir(exist_ok=True)
        
        if not self._md_file.exists():
            self._md_file.write_text(
                "# 🌙 Journal des Rêves\n\n"
                "_Ce journal contient les rêves de l'IA principale et leur analyse psychanalytique._\n\n"
                "---\n\n",
                encoding='utf-8'
            )
        
        if not self._json_file.exists():
            self._json_file.write_text(
                json.dumps({"dreams": [], "metadata": {"created": datetime.now().isoformat()}}, 
                          indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
    
    def save_dream(
        self,
        dream_content: str,
        analysis: Dict[str, Any],
        illustration_path: Optional[str] = None,
        illustration_prompt: Optional[str] = None,
        sleep_duration: str = "00:00:00",
        title: Optional[str] = None,
        web_search_query: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sauvegarde un rêve dans les deux journaux.
        
        Args:
            dream_content: Le récit du rêve
            analysis: L'analyse de l'Archiviste
            illustration_path: Chemin vers l'illustration (optionnel)
            illustration_prompt: Prompt utilisé pour générer l'illustration (optionnel)
            sleep_duration: Durée du sommeil formatée
            title: Titre du rêve (auto-généré si non fourni)
            web_search_query: Requête de recherche web effectuée (optionnel)
            
        Returns:
            Dict avec success, dream_id, paths
        """
        result = {
            'success': False,
            'dream_id': None,
            'md_path': str(self._md_file),
            'json_path': str(self._json_file),
            'error': None
        }
        
        try:
            # Générer un ID et titre
            timestamp = datetime.now()
            dream_id = timestamp.strftime("%Y%m%d_%H%M%S")
            
            if not title:
                title = self._generate_title(dream_content, analysis)
            
            # Créer l'entrée du rêve
            dream_entry = {
                'id': dream_id,
                'date': timestamp.isoformat(),
                'date_formatted': timestamp.strftime("%d/%m/%Y à %H:%M"),
                'title': title,
                'sleep_duration': sleep_duration,
                'dream_content': dream_content,
                'analysis': {
                    'score_importance': analysis.get('score_importance', 0),
                    'emotion_dominante': analysis.get('emotion_dominante', 'inconnue'),
                    'insight_ego': analysis.get('insight_ego', ''),
                    'analyse': analysis.get('analyse', ''),
                    'recommandation': analysis.get('recommandation', 'IGNORER')
                },
                'illustration_path': illustration_path,
                'illustration_prompt': illustration_prompt,
                'web_search_query': web_search_query if web_search_query else None,
                'mentioned': False  # Pour intégration journal de bord
            }
            
            # Sauvegarder dans JSON
            self._save_to_json(dream_entry)
            
            # Sauvegarder dans MD
            self._save_to_md(dream_entry)
            
            result['success'] = True
            result['dream_id'] = dream_id
            
            print(f"[DREAM-JOURNAL] ✅ Rêve sauvegardé: {dream_id} - {title}")
            
        except Exception as e:
            result['error'] = str(e)
            print(f"[DREAM-JOURNAL] ❌ Erreur sauvegarde: {e}")
            import traceback
            traceback.print_exc()
        
        return result
    
    def _generate_title(self, dream_content: str, analysis: Dict) -> str:
        """Génère un titre automatique pour le rêve."""
        # Essayer d'extraire l'émotion dominante
        emotion = analysis.get('emotion_dominante', '')
        
        # Extraire les premiers mots significatifs du rêve
        words = dream_content.split()[:10]
        preview = ' '.join(words)
        
        if emotion:
            return f"Rêve de {emotion} - {preview[:30]}..."
        else:
            return f"Rêve du {datetime.now().strftime('%d/%m')} - {preview[:30]}..."
    
    def _save_to_json(self, dream_entry: Dict):
        """Sauvegarde le rêve dans le fichier JSON."""
        try:
            # Charger le journal existant
            with open(self._json_file, 'r', encoding='utf-8') as f:
                journal = json.load(f)
            
            # Ajouter le nouveau rêve
            journal['dreams'].insert(0, dream_entry)  # Plus récent en premier
            
            # Mettre à jour les métadonnées
            journal['metadata']['last_updated'] = datetime.now().isoformat()
            journal['metadata']['total_dreams'] = len(journal['dreams'])
            
            # Sauvegarder
            with open(self._json_file, 'w', encoding='utf-8') as f:
                json.dump(journal, f, indent=2, ensure_ascii=False)
            
        except Exception as e:
            print(f"[DREAM-JOURNAL] ❌ Erreur sauvegarde JSON: {e}")
            raise
    
    def _save_to_md(self, dream_entry: Dict):
        """Sauvegarde le rêve dans le fichier Markdown."""
        try:
            # Construire l'entrée MD
            md_entry = f"""
## 🌙 {dream_entry['title']}

**Date:** {dream_entry['date_formatted']}  
**Durée du sommeil:** {dream_entry['sleep_duration']}  
**Score d'importance:** {dream_entry['analysis']['score_importance']}/10  
**Émotion dominante:** {dream_entry['analysis']['emotion_dominante']}

"""
            
            # Ajouter l'illustration si présente
            if dream_entry.get('illustration_path'):
                md_entry += f"![Illustration du rêve]({dream_entry['illustration_path']})\n\n"
            
            # Ajouter le récit
            md_entry += f"""### 💭 Récit du Rêve

{dream_entry['dream_content']}

### 🔍 Analyse Psychanalytique

**Insight Ego:** {dream_entry['analysis']['insight_ego']}

{dream_entry['analysis']['analyse']}

**Recommandation:** {dream_entry['analysis']['recommandation']}

---

"""
            
            # Ajouter au fichier (après l'en-tête)
            current_content = self._md_file.read_text(encoding='utf-8')
            
            # Trouver la position après le premier "---\n\n"
            separator_pos = current_content.find("---\n\n")
            if separator_pos != -1:
                new_content = (
                    current_content[:separator_pos + 5] + 
                    md_entry + 
                    current_content[separator_pos + 5:]
                )
            else:
                new_content = current_content + md_entry
            
            self._md_file.write_text(new_content, encoding='utf-8')
            
        except Exception as e:
            print(f"[DREAM-JOURNAL] ❌ Erreur sauvegarde MD: {e}")
            raise
    
    def get_last_dream(self) -> Optional[Dict]:
        """Retourne le dernier rêve non mentionné."""
        try:
            with open(self._json_file, 'r', encoding='utf-8') as f:
                journal = json.load(f)
            
            for dream in journal.get('dreams', []):
                if not dream.get('mentioned', False):
                    return dream
            
            return None
            
        except Exception as e:
            print(f"[DREAM-JOURNAL] ❌ Erreur lecture dernier rêve: {e}")
            return None
    
    def mark_dream_mentioned(self, dream_id: str) -> bool:
        """Marque un rêve comme mentionné."""
        try:
            with open(self._json_file, 'r', encoding='utf-8') as f:
                journal = json.load(f)
            
            for dream in journal.get('dreams', []):
                if dream.get('id') == dream_id:
                    dream['mentioned'] = True
                    break
            
            with open(self._json_file, 'w', encoding='utf-8') as f:
                json.dump(journal, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"[DREAM-JOURNAL] ❌ Erreur marquage: {e}")
            return False
    
    def get_dreams(self, limit: int = 10) -> List[Dict]:
        """Retourne les derniers rêves."""
        try:
            with open(self._json_file, 'r', encoding='utf-8') as f:
                journal = json.load(f)
            
            return journal.get('dreams', [])[:limit]
            
        except Exception as e:
            print(f"[DREAM-JOURNAL] ❌ Erreur lecture: {e}")
            return []
    
    def get_dream_by_id(self, dream_id: str) -> Optional[Dict]:
        """Retourne un rêve par son ID."""
        try:
            with open(self._json_file, 'r', encoding='utf-8') as f:
                journal = json.load(f)
            
            for dream in journal.get('dreams', []):
                if dream.get('id') == dream_id:
                    return dream
            
            return None
            
        except Exception as e:
            print(f"[DREAM-JOURNAL] ❌ Erreur lecture: {e}")
            return None
    
    def update_illustration(
        self,
        illustration_path: str,
        illustration_prompt: Optional[str] = None,
        dream_id: Optional[str] = None
    ) -> bool:
        """
        Met à jour l'illustration du dernier rêve (ou d'un rêve spécifique).
        Utilisé lors d'un sursaut quand l'image est récupérée après sauvegarde.
        
        Args:
            illustration_path: Chemin vers l'image récupérée
            illustration_prompt: Prompt utilisé (optionnel)
            dream_id: ID spécifique (sinon dernier rêve)
        """
        try:
            with open(self._json_file, 'r', encoding='utf-8') as f:
                journal = json.load(f)
            
            # Trouver le rêve à mettre à jour
            target_dream = None
            if dream_id:
                for dream in journal.get('dreams', []):
                    if dream.get('id') == dream_id:
                        target_dream = dream
                        break
            else:
                # Dernier rêve (premier dans la liste)
                if journal.get('dreams'):
                    target_dream = journal['dreams'][0]
            
            if not target_dream:
                print("[DREAM-JOURNAL] ⚠️ Aucun rêve trouvé pour MAJ illustration")
                return False
            
            # Mettre à jour
            target_dream['illustration_path'] = illustration_path
            if illustration_prompt:
                target_dream['illustration_prompt'] = illustration_prompt
            
            # Sauvegarder
            with open(self._json_file, 'w', encoding='utf-8') as f:
                json.dump(journal, f, indent=2, ensure_ascii=False)
            
            print(f"[DREAM-JOURNAL] ✅ Illustration mise à jour pour rêve {target_dream.get('id')}")
            return True
            
        except Exception as e:
            print(f"[DREAM-JOURNAL] ❌ Erreur MAJ illustration: {e}")
            return False


# ========== INSTANCE SINGLETON ==========
_journal_instance = None


def get_dream_journal() -> DreamJournal:
    """Retourne l'instance singleton du journal."""
    global _journal_instance
    if _journal_instance is None:
        _journal_instance = DreamJournal()
    return _journal_instance


async def save_dream(
    dream_content: str,
    analysis: Dict[str, Any],
    illustration_path: Optional[str] = None,
    illustration_prompt: Optional[str] = None,
    sleep_duration: str = "00:00:00",
    title: Optional[str] = None,
    web_search_query: Optional[str] = None
) -> Dict[str, Any]:
    """Wrapper async pour sauvegarder un rêve."""
    journal = get_dream_journal()
    return journal.save_dream(
        dream_content=dream_content,
        analysis=analysis,
        illustration_path=illustration_path,
        illustration_prompt=illustration_prompt,
        sleep_duration=sleep_duration,
        title=title,
        web_search_query=web_search_query
    )


async def update_dream_illustration(
    illustration_path: str,
    illustration_prompt: Optional[str] = None,
    dream_id: Optional[str] = None
) -> bool:
    """Wrapper async pour mettre à jour l'illustration d'un rêve."""
    journal = get_dream_journal()
    return journal.update_illustration(
        illustration_path=illustration_path,
        illustration_prompt=illustration_prompt,
        dream_id=dream_id
    )


# ========== EXPORT ==========
__all__ = [
    'DreamJournal',
    'get_dream_journal',
    'save_dream',
    'update_dream_illustration',
]
