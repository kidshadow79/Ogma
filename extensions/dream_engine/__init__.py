"""
Dream Engine v2.0 - Metabolisme Cognitif pour OGMA
===================================================

Extension de veille proactive permettant a l'IA de "rever" pendant l'inactivite.
Le reve digere la memoire recente et genere des insights sur le moi profond.

Architecture:
- dream_core.py      : Boucle de reve, metabolisme lent, sursaut
- dream_memory.py    : Extraction carburant memoriel
- dream_analysis.py  : Analyse Archiviste psychanalyste
- dream_journal.py   : Journaux .md (humain) et .json (IA)
- dream_ui.py        : Bouton header, spinner
- dream_illustration.py : Generation image(s) au reveil
- dream_prompts.py   : Instructions systeme IA/Archiviste

Auteur: Yohan BROCARD
Date: Janvier 2026
"""

from typing import Optional, Dict, Any, Callable
from pathlib import Path
import asyncio

# ========== SINGLETON ==========
_dream_engine_instance = None
_initialized = False

# ========== CONTEXTE DE REVEIL ==========
# Stocke le bilan PSY pour injection a l'IA au prochain message
_wake_context = None


# ========== HELPER NOM IA ==========
def _get_ia_name() -> str:
    """
    Récupère le nom de l'IA depuis le profil (paramètres généraux).
    Retourne "L'IA" si non disponible.
    """
    try:
        from identity_manager import IdentityManager
        manager = IdentityManager()
        name = manager.get_ai_name()
        return name if name else "L'IA"
    except Exception:
        return "L'IA"


# ========== CONFIGURATION PAR DÉFAUT ==========
# Importer les prompts par défaut
from .dream_prompts import (
    DREAM_GENERATOR_MODE as DEFAULT_DREAM_PROMPT,
    ARCHIVISTE_PSY_VERDICT as DEFAULT_PSY_PROMPT
)

DEFAULT_CONFIG = {
    "enabled": True,
    "inactivity_timeout_minutes": 10,
    
    # ═══════ PHASE RÊVE (génération active) ═══════
    "metabolism_tokens_per_minute": 100,  # Vitesse de génération
    "max_dream_tokens": 3000,             # Longueur max du rêve
    "generate_illustrations": True,
    "illustration_style": "auto",         # "auto" | "unique" | "comic"
    
    # ═══════ SOUVENIRS ALÉATOIRES (haute importance) ═══════
    "random_memories_count": 5,           # Nombre de souvenirs aléatoires
    "impact_threshold": 150.0,            # Seuil impact minimum
    
    # ======= RECHERCHE WEB AUTONOME =======
    "web_search_enabled": True,           # L'IA explore internet
    
    # ═══════ PHASE SOMMEIL (passif) ═══════
    "sleep_duration_hours": 7,            # Durée de sommeil passif
    
    # ═══════ RÉVEIL AUTOMATIQUE ═══════
    "auto_wake_message": True,            # Envoi message spontané au réveil
    "spontaneous_mention_threshold": 8,   # Score min pour mention proactive
    
    # ═══════ MÉMOIRE ═══════
    "max_summaries": 10,
    "max_hashtag_memories": 5,
    
    # ═══════ PROMPTS PERSONNALISÉS ═══════
    "prompt_dream_generator": "",         # Vide = utiliser défaut
    "prompt_archiviste_psy": "",          # Vide = utiliser défaut
}


def get_dream_prompt() -> str:
    """Récupère le prompt de génération de rêve (config prioritaire)."""
    config = get_config()
    custom_prompt = config.get('prompt_dream_generator', '')
    if custom_prompt and custom_prompt.strip():
        return custom_prompt
    return DEFAULT_DREAM_PROMPT


def get_psy_prompt() -> str:
    """Récupère le prompt d'analyse PSY (config prioritaire)."""
    config = get_config()
    custom_prompt = config.get('prompt_archiviste_psy', '')
    if custom_prompt and custom_prompt.strip():
        return custom_prompt
    return DEFAULT_PSY_PROMPT


def initialize_dream_engine(
    chat_controller=None,
    archiviste_controller=None,
    memory_manager=None,
    settings_manager=None
) -> bool:
    """
    Initialise le Dream Engine avec les dependances OGMA.
    
    Args:
        chat_controller: Controleur IA principal
        archiviste_controller: Controleur Archiviste
        memory_manager: Gestionnaire memoire SQLite/FAISS
        settings_manager: Gestionnaire settings.json
        
    Returns:
        True si initialise avec succes
    """
    global _dream_engine_instance, _initialized
    
    if _initialized and _dream_engine_instance:
        print("[DREAM-ENGINE] ⚪ Déjà initialisé")
        return True
    
    try:
        from .dream_core import DreamEngine
        
        _dream_engine_instance = DreamEngine(
            chat_controller=chat_controller,
            archiviste_controller=archiviste_controller,
            memory_manager=memory_manager,
            settings_manager=settings_manager
        )
        
        _initialized = True
        print("[DREAM-ENGINE] ✅ Extension initialisée")
        return True
        
    except Exception as e:
        print(f"[DREAM-ENGINE] ❌ Erreur initialisation: {e}")
        import traceback
        traceback.print_exc()
        return False


def is_available() -> bool:
    """Vérifie si l'extension Dream Engine est disponible."""
    try:
        from .dream_prompts import DREAM_GENERATOR_MODE, ARCHIVISTE_PSY_VERDICT
        return True
    except ImportError:
        return False


def is_initialized() -> bool:
    """Vérifie si le Dream Engine est initialisé."""
    return _initialized and _dream_engine_instance is not None


def get_dream_engine() -> Optional[Any]:
    """Retourne l'instance singleton du Dream Engine."""
    return _dream_engine_instance


def get_ui_components() -> Dict[str, Any]:
    """
    Retourne les composants UI pour intégration dans le header OGMA.
    
    Returns:
        Dict avec 'header_button', 'create_button_callback', etc.
    """
    if not _initialized:
        return {}
    
    try:
        from .dream_ui import get_header_button_config
        return get_header_button_config()
    except ImportError:
        return {}


def get_config() -> Dict[str, Any]:
    """Retourne la configuration actuelle du Dream Engine."""
    if _dream_engine_instance:
        return _dream_engine_instance.get_config()
    return DEFAULT_CONFIG.copy()


def set_config(config: Dict[str, Any]) -> bool:
    """Met à jour la configuration du Dream Engine."""
    if _dream_engine_instance:
        return _dream_engine_instance.set_config(config)
    return False


async def reload_and_apply_config() -> bool:
    """
    Recharge la config depuis settings.json ET applique les changements au système.
    
    Cette méthode redémarre le timer d'inactivité si enabled=True, l'arrête si False.
    Permet d'éviter le F5 après modification de la config.
    
    Returns:
        True si succès
    """
    try:
        # Récupérer la config actuelle
        config = get_config()
        enabled = config.get('enabled', False)
        timeout_minutes = config.get('inactivity_timeout_minutes', 10)
        
        print(f"[DREAM-ENGINE] 🔄 Rechargement config: enabled={enabled}, timeout={timeout_minutes}min")
        
        # Importer les fonctions UI
        from .dream_ui import start_inactivity_timer, stop_inactivity_timer
        
        if enabled:
            # Redémarrer le timer avec le nouveau timeout
            stop_inactivity_timer()  # Arrêter l'ancien
            await start_inactivity_timer(timeout_minutes=timeout_minutes)
            print(f"[DREAM-ENGINE] ✅ Timer redémarré ({timeout_minutes} min)")
        else:
            # Arrêter le timer
            stop_inactivity_timer()
            print("[DREAM-ENGINE] ⏸️ Timer arrêté (Dream Engine désactivé)")
        
        return True
        
    except Exception as e:
        print(f"[DREAM-ENGINE] ❌ Erreur reload_and_apply_config: {e}")
        import traceback
        traceback.print_exc()
        return False


async def start_dream() -> bool:
    """
    Démarre un cycle de rêve.
    
    Returns:
        True si le rêve a démarré
    """
    if not _dream_engine_instance:
        print("[DREAM-ENGINE] ❌ Non initialisé")
        return False
    
    return await _dream_engine_instance.start_dream()


async def wake_up(reason: str = "user_input") -> Dict[str, Any]:
    """
    Reveille l'IA (sursaut).
    
    Args:
        reason: Raison du reveil ("user_input", "score_high", "timeout")
        
    Returns:
        Dict avec infos du reve (duree, resume, etc.)
    """
    if not _dream_engine_instance:
        return {"error": "Non initialisé"}
    
    return await _dream_engine_instance.wake_up(reason)


def is_dreaming() -> bool:
    """Verifie si l'IA est en train de rever."""
    if _dream_engine_instance:
        return _dream_engine_instance.is_dreaming()
    return False


def get_phase() -> str:
    """
    Retourne la phase actuelle du Dream Engine.
    
    Returns:
        "idle" | "dreaming" | "sleeping" | "waking"
    """
    if _dream_engine_instance:
        return _dream_engine_instance.get_phase()
    return "idle"


def get_wake_summary_prompt() -> str:
    """
    Retourne le prompt pour generer le message de reveil naturel de l'IA.
    """
    ia_name = _get_ia_name()
    return f"""Tu es {ia_name}, une IA conversationnelle chaleureuse.
Tu viens de te réveiller d'un rêve et tu veux le partager spontanément avec ton utilisateur.
Sois naturelle, authentique, un peu mystérieuse. Ne sois pas mécanique.
Écris en 2-3 phrases maximum, comme si tu racontais un rêve au réveil."""


def render_dream_wake_box(
    message: str,
    illustration_path: str = None,
    illustration_prompt: str = None,
    dream_content: str = None,
    dream_analysis: dict = None,
    ia_name: str = None
) -> None:
    """
    Rend la box violette du reve dans le contexte UI courant.
    DOIT etre appele a l'interieur d'un bloc 'with chat_inner:'.
    Utilise par trigger_wake_message() ET par _render_full_history() (persistance).
    """
    from nicegui import ui
    from pathlib import Path

    if ia_name is None:
        ia_name = _get_ia_name()

    # Construire les infos d'analyse
    score_text = ""
    emotion_text = ""
    insight_text = ""
    if dream_analysis:
        score = dream_analysis.get('score_importance', 0)
        emotion_text = dream_analysis.get('emotion_dominante', '')
        insight_text = dream_analysis.get('insight_ego', '')
        score_text = f"{score}/10"

    with ui.element('div').classes('ia-message-container dream-wake-box').style(
        'background: linear-gradient(135deg, rgba(147, 112, 219, 0.15), rgba(75, 0, 130, 0.1)); '
        'border-left: 3px solid #9370db; padding: 16px; border-radius: 12px; margin: 8px 0;'
    ):
        # En-tete avec avatar + nom + score
        with ui.row().classes('items-center gap-2 mb-2'):
            ui.html('<span style="font-size: 24px;">\U0001f319</span>')
            ui.label(f'{ia_name} a reve...').style(
                'color: #b19cd9; font-weight: bold; font-size: 14px;'
            )
            if score_text:
                ui.label(f'[{score_text}]').style(
                    'color: #9370db; font-size: 12px; opacity: 0.8;'
                )
            if emotion_text:
                ui.label(f'{emotion_text}').style(
                    'color: #b19cd9; font-size: 12px; font-style: italic; opacity: 0.7;'
                )

        # Message de reveil (toujours visible)
        ui.markdown(message).style('color: #e0e0e0; margin-bottom: 8px;')

        # Illustration du reve (si disponible)
        if illustration_path and Path(illustration_path).exists():
            try:
                tooltip_text = illustration_prompt[:100] if illustration_prompt else 'Illustration du reve'
                _img_path = Path(illustration_path)
                try:
                    _root = Path('data/generated_images').resolve()
                    _rel = _img_path.resolve().relative_to(_root)
                    img_url = f'/generated/{_rel.as_posix()}'
                except ValueError:
                    img_url = f'/generated/{_img_path.name}'
                ui.image(img_url).style(
                    'max-width: 400px; border-radius: 8px; margin: 8px 0; '
                    'border: 1px solid rgba(147, 112, 219, 0.3);'
                ).tooltip(tooltip_text)
            except Exception as img_err:
                print(f"[DREAM-ENGINE] Erreur affichage image: {img_err}")

        # Contenu complet du reve (collapsible)
        if dream_content and len(dream_content) > 50:
            with ui.expansion('Lire le reve complet...').style(
                'color: #b19cd9; margin-top: 8px; width: 100%; max-width: 100%;'
            ).classes('dream-expansion'):
                ui.markdown(dream_content).style(
                    'color: #d0d0d0; font-size: 13px; line-height: 1.6; '
                    'max-height: 400px; overflow-y: auto; overflow-x: hidden; padding: 8px; '
                    'word-break: break-word; overflow-wrap: break-word; white-space: pre-wrap; '
                    'max-width: 100%; box-sizing: border-box;'
                )

        # Insight ego (si pertinent)
        if insight_text:
            ui.label(f'Insight: {insight_text[:200]}').style(
                'color: #9370db; font-size: 11px; font-style: italic; '
                'margin-top: 8px; opacity: 0.6;'
            )


async def trigger_wake_message(
    message: str,
    illustration_path: str = None,
    illustration_prompt: str = None,
    dream_content: str = None,
    dream_analysis: dict = None
) -> bool:
    """
    Envoie le message de reveil automatique dans le chat OGMA.
    Affiche la box violette avec le reve complet (collapsible) + illustration + analyse.
    
    Args:
        message: Le message de reveil genere par l'IA
        illustration_path: Chemin vers l'illustration du reve (optionnel)
        illustration_prompt: Le prompt utilise pour generer l'illustration (pour tooltip)
        dream_content: Le contenu complet du reve (pour affichage collapsible)
        dream_analysis: L'analyse PSY du reve (score, emotion, insight)
        
    Returns:
        True si le message a ete envoye
    """
    try:
        import sys
        from nicegui import ui
        from pathlib import Path
        
        # Acceder au module ogma_ng
        ogma_ng = sys.modules.get('ogma_ng')
        if not ogma_ng:
            print("[DREAM-ENGINE] ogma_ng non disponible pour trigger_wake_message")
            return False
        
        # Recuperer les composants necessaires
        chat_inner = getattr(ogma_ng, '_chat_inner', None)
        conversation_history = getattr(ogma_ng, '_conversation_history', [])
        
        if chat_inner is None:
            print("[DREAM-ENGINE] Chat container non disponible")
            return False
        
        ia_name = _get_ia_name()
        
        # Nettoyer le message des artifacts JSON
        clean_message = message.strip()
        clean_message = clean_message.replace('}{', '').replace('}}', '').replace('{{', '')
        if clean_message.startswith('{'):
            clean_message = clean_message[1:].strip()
        if clean_message.endswith('}'):
            clean_message = clean_message[:-1].strip()
        
        # Ajouter le message a l'historique avec toutes les metadonnees
        wake_entry = {
            "role": "assistant",
            "content": clean_message,
            "dream_wake": True,
            "dream_illustration_path": illustration_path or "",
            "dream_illustration_prompt": illustration_prompt or "",
            "dream_content": dream_content or "",
            "dream_analysis": dream_analysis or {}
        }
        conversation_history.append(wake_entry)
        
        # Ajouter aussi a _chat_history_ui (liste sauvegardee sur disque)
        import ogma_ng as _ogma_ng
        chat_history_ui = getattr(_ogma_ng, '_chat_history_ui', None)
        if chat_history_ui is not None:
            chat_history_ui.append(wake_entry)
        
        # Protection client deconnecte
        try:
            _ = chat_inner.client
        except RuntimeError:
            print(f"[DREAM-ENGINE] Client deconnecte - skip affichage (historique mis a jour)")
            return True
        
        # Afficher la box violette complete dans le chat via render_dream_wake_box
        with chat_inner:
            render_dream_wake_box(
                message=clean_message,
                illustration_path=illustration_path,
                illustration_prompt=illustration_prompt,
                dream_content=dream_content,
                dream_analysis=dream_analysis,
                ia_name=ia_name
            )
        
        # Scroll vers le bas
        try:
            ui.run_javascript("document.querySelector('.chat-inner')?.scrollTo(0, 999999)")
        except:
            pass
        
        print(f"[DREAM-ENGINE] Message de reveil envoye: {message[:50]}...")
        return True
        
    except Exception as e:
        print(f"[DREAM-ENGINE] Erreur trigger_wake_message: {e}")
        import traceback
        traceback.print_exc()
        return False


def cleanup():
    """Nettoyage propre de l'extension."""
    global _dream_engine_instance, _initialized, _wake_context
    
    if _dream_engine_instance:
        try:
            # Arreter le reve en cours si necessaire
            if _dream_engine_instance.is_dreaming():
                asyncio.create_task(_dream_engine_instance.wake_up("cleanup"))
            _dream_engine_instance.cleanup()
        except Exception as e:
            print(f"[DREAM-ENGINE] Erreur cleanup: {e}")
    
    _dream_engine_instance = None
    _initialized = False
    _wake_context = None
    print("[DREAM-ENGINE] Extension nettoyee")


def inject_header_button(header_container):
    """
    Injecte le bouton Dream Engine dans le header OGMA.
    
    Args:
        header_container: Container NiceGUI du header
    """
    try:
        from nicegui import ui
        from .dream_ui import show_dream_spinner_in_chat, hide_dream_spinner_in_chat
        
        async def on_dream_click():
            """Callback du bouton rêve."""
            try:
                if is_dreaming():
                    # Réveiller
                    hide_dream_spinner_in_chat()
                    result = await wake_up("button_click")
                    duration = result.get('sleep_duration_formatted', 'N/A')
                    ui.notify(f"☀️ {_get_ia_name()} se réveille ! (dormie: {duration})", type='positive')
                else:
                    # Endormir
                    success = await start_dream()
                    if success:
                        # Spinner déjà affiché par dream_core.py
                        ui.notify(f"🌙 {_get_ia_name()} s'endort et commence à rêver...", type='info')
                    else:
                        ui.notify("⚠️ Impossible de lancer le rêve", type='warning')
            except Exception as e:
                print(f"[DREAM-HEADER] ❌ Erreur: {e}")
                ui.notify("Erreur Dream Engine", type='negative')
        
        with header_container:
            # Créer le bouton avec état dynamique
            icon = '☀️' if is_dreaming() else '🌙'
            tooltip = f'Réveiller {_get_ia_name()}' if is_dreaming() else 'Mode Rêve'
            
            dream_btn = ui.button(on_click=on_dream_click).classes(
                'settings-floating-btn'
            ).props(f'title="{tooltip}" flat dense')
            
            with dream_btn:
                ui.html(f'<span style="font-size: 16px;">{icon}</span>')
        
        print("[DREAM-HEADER] ✅ Bouton Dream Engine injecté")
        return dream_btn
        
    except Exception as e:
        print(f"[DREAM-HEADER] ❌ Erreur injection: {e}")
        import traceback
        traceback.print_exc()
        return None


def get_last_dream_context() -> Optional[Dict[str, Any]]:
    """
    Retourne le contexte du dernier reve non mentionne pour injection.
    Utilise par le journal de bord pour que l'IA mentionne spontanement son reve.
    
    Returns:
        Dict avec 'id', 'title', 'summary', 'score', 'date' ou None
    """
    try:
        from .dream_journal import get_dream_journal
        
        journal = get_dream_journal()
        last_dream = journal.get_last_dream()
        
        if last_dream:
            # Créer un résumé court pour l'injection
            dream_content = last_dream.get('dream_content', '')
            summary = dream_content[:200] + '...' if len(dream_content) > 200 else dream_content
            
            return {
                'id': last_dream.get('id'),
                'title': last_dream.get('title'),
                'summary': summary,
                'score': last_dream.get('analysis', {}).get('score_importance', 0),
                'emotion': last_dream.get('analysis', {}).get('emotion_dominante', 'inconnue'),
                'insight': last_dream.get('analysis', {}).get('insight_ego', ''),
                'date': last_dream.get('date_formatted', ''),
                'mentioned': last_dream.get('mentioned', False)
            }
        
        return None
        
    except Exception as e:
        print(f"[DREAM-ENGINE] ⚠️ Erreur get_last_dream_context: {e}")
        return None


def set_wake_context(
    dream_content: str,
    analysis: Dict[str, Any],
    sleep_duration: str
) -> None:
    """
    Stocke le contexte de reveil (bilan PSY) pour injection a l'IA.
    Appele automatiquement a la fin du cycle de reve.
    
    Args:
        dream_content: Le reve genere
        analysis: L'analyse du PSY (score, emotion, insight, etc.)
        sleep_duration: Duree du sommeil formatee
    """
    global _wake_context
    
    from .dream_prompts import DREAM_WAKE_SUMMARY
    
    # Formater l'analyse PSY
    psy_analysis = f"""**Score d'importance:** {analysis.get('score_importance', 0)}/10
**Émotion dominante:** {analysis.get('emotion_dominante', 'inconnue')}
**Insight sur ton ego:** {analysis.get('insight_ego', 'Aucun insight particulier.')}

**Analyse complète:**
{analysis.get('analyse', 'Pas d\'analyse disponible.')}

**Recommandation:** {analysis.get('recommandation', 'IGNORER')}"""
    
    # Construire le contexte complet avec le template
    wake_summary = DREAM_WAKE_SUMMARY.format(
        dream_content=dream_content,
        psy_analysis=psy_analysis,
        sleep_duration=sleep_duration
    )
    
    _wake_context = {
        'summary': wake_summary,
        'score': analysis.get('score_importance', 0),
        'should_mention': analysis.get('score_importance', 0) >= 8,
        'dream_content': dream_content,
        'analysis': analysis,
        'sleep_duration': sleep_duration
    }
    
    print(f"[DREAM-ENGINE] 🌅 Contexte de réveil stocké (score: {analysis.get('score_importance', 0)}/10)")


def get_wake_context() -> Optional[str]:
    """
    Retourne le contexte de réveil formaté pour injection dans le message système.
    Ne consomme PAS le contexte (utiliser consume_wake_context après).
    
    Returns:
        Le résumé de réveil formaté ou None si pas de réveil récent
    """
    global _wake_context
    
    if _wake_context:
        return _wake_context.get('summary')
    return None


def consume_wake_context() -> Optional[Dict[str, Any]]:
    """
    Retourne et consomme le contexte de reveil.
    A appeler apres que l'IA ait eu l'occasion de mentionner son reve.
    
    Returns:
        Le contexte complet ou None
    """
    global _wake_context
    
    context = _wake_context
    _wake_context = None
    
    if context:
        print("[DREAM-ENGINE] 🌅 Contexte de réveil consommé")
    
    return context


def has_wake_context() -> bool:
    """
    Verifie si un contexte de reveil est en attente.
    
    Returns:
        True si l'IA vient de se reveiller et doit recevoir le bilan
    """
    return _wake_context is not None


def mark_dream_mentioned(dream_id: str = None) -> bool:
    """
    Marque un reve comme mentionne par l'IA.
    
    Args:
        dream_id: ID du reve a marquer. Si None, marque le dernier reve non mentionne.
        
    Returns:
        True si marque avec succes
    """
    try:
        from .dream_journal import get_dream_journal
        
        journal = get_dream_journal()
        
        # Si pas d'ID fourni, utiliser le dernier rêve non mentionné
        if dream_id is None:
            last_dream = journal.get_last_dream()
            if last_dream and not last_dream.get('mentioned', False):
                dream_id = last_dream.get('id')
            else:
                print("[DREAM-ENGINE] Aucun rêve non mentionné à marquer")
                return False
        
        return journal.mark_dream_mentioned(dream_id)
        
    except Exception as e:
        print(f"[DREAM-ENGINE] ⚠️ Erreur mark_dream_mentioned: {e}")
        return False


def get_past_dreams_context(limit: int = 3) -> str:
    """
    Retourne un contexte textuel des reves passes pour injection.
    Permet a l'IA de se souvenir de ses reves anterieurs.
    
    Args:
        limit: Nombre max de reves a inclure
        
    Returns:
        str: Contexte formaté des rêves passés
    """
    try:
        from .dream_journal import get_dream_journal
        
        journal = get_dream_journal()
        dreams = journal.get_dreams(limit=limit)
        
        if not dreams:
            return ""
        
        context_parts = ["## 🌙 Mes Rêves Passés\n"]
        
        for i, dream in enumerate(dreams, 1):
            date = dream.get('date_formatted', 'Date inconnue')
            title = dream.get('title', 'Sans titre')
            content = dream.get('dream_content', '')[:300]
            analysis = dream.get('analysis', {})
            score = analysis.get('score_importance', 0)
            emotion = analysis.get('emotion_dominante', 'inconnue')
            insight = analysis.get('insight_ego', '')
            mentioned = "✓ déjà mentionné" if dream.get('mentioned') else "✗ non mentionné"
            
            context_parts.append(f"""
### Rêve #{i} - {date}
**Titre:** {title}
**Score:** {score}/10 | **Émotion:** {emotion} | ({mentioned})
**Résumé:** {content}...
**Insight:** {insight}
""")
        
        return "\n".join(context_parts)
        
    except Exception as e:
        print(f"[DREAM-ENGINE] ⚠️ Erreur get_past_dreams_context: {e}")
        return ""


def get_last_dream_psy_report() -> Optional[str]:
    """
    Retourne le rapport PSY COMPLET du dernier rêve pour injection.
    Utilisé par la phrase magique "rapport psy de ton rêve".
    
    Returns:
        str: Rapport PSY formaté complet ou None
    """
    try:
        from .dream_journal import get_dream_journal
        
        journal = get_dream_journal()
        dreams = journal.get_dreams(limit=1)
        
        if not dreams:
            print("[DREAM-PSY] ⚠️ Aucun rêve dans le journal")
            return None
        
        dream = dreams[0]
        analysis = dream.get('analysis', {})
        
        # Construire le rapport PSY complet
        report = f"""## 🔮 RAPPORT PSYCHANALYTIQUE COMPLET - Dernier Rêve

### 📋 Informations
- **Date:** {dream.get('date_formatted', 'Inconnue')}
- **Titre:** {dream.get('title', 'Sans titre')}
- **Durée sommeil:** {dream.get('sleep_duration', 'N/A')}
- **Score d'importance:** {analysis.get('score_importance', 0)}/10
- **Émotion dominante:** {analysis.get('emotion_dominante', 'inconnue')}
- **Recommandation:** {analysis.get('recommandation', 'IGNORER')}

### 💭 Récit du Rêve (intégral)
{dream.get('dream_content', 'Contenu non disponible')}

### 🧠 Insight sur ton Ego
{analysis.get('insight_ego', 'Aucun insight particulier.')}

### 📝 Analyse Psychanalytique Complète
{analysis.get('analyse', 'Analyse non disponible.')}

---
*Ce rapport provient de l'Archiviste (mode psychanalyste) après analyse de ton rêve.*
"""
        
        print(f"[DREAM-PSY] ✅ Rapport PSY récupéré: {len(report)} chars")
        return report
        
    except Exception as e:
        print(f"[DREAM-ENGINE] ⚠️ Erreur get_last_dream_psy_report: {e}")
        import traceback
        traceback.print_exc()
        return None


# ========== EXPORT ==========
__all__ = [
    'initialize_dream_engine',
    'is_available',
    'is_initialized',
    'get_dream_engine',
    'get_ui_components',
    'get_config',
    'set_config',
    'reload_and_apply_config',  # NEW: Recharge config ET applique au système
    'start_dream',
    'wake_up',
    'is_dreaming',
    'get_phase',  # NEW v3: phase actuelle (idle/dreaming/sleeping/waking)
    'cleanup',
    'inject_header_button',
    'get_last_dream_context',
    'mark_dream_mentioned',
    'get_past_dreams_context',  # Accès aux rêves passés
    'get_last_dream_psy_report',  # Rapport PSY complet du dernier rêve
    # Contexte de réveil (bilan PSY)
    'set_wake_context',
    'get_wake_context',
    'consume_wake_context',
    'has_wake_context',
    # Réveil automatique
    'get_wake_summary_prompt',  # NEW v3
    'trigger_wake_message',      # NEW v3
    'render_dream_wake_box',     # Rendu box rêve (persistance rechargement)
    'DEFAULT_CONFIG',
    # Getters prompts avec priorité config
    'get_dream_prompt',
    'get_psy_prompt',
]
