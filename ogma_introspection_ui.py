"""
OGMA - Module UI Introspection
Gestion de l'affichage des messages d'introspection (Cognitive Mirror / Subconscience)

Extrait de ogma_ng.py - 8 décembre 2025
"""

from typing import Optional, Any

# Import NiceGUI avec fallback
try:
    import importlib
    _ng = importlib.import_module('nicegui')
    _ui = getattr(_ng, 'ui', None)
except Exception:
    _ui = None

class _Dummy:
    def __getattr__(self, name):
        return self
    def __call__(self, *args, **kwargs):
        return self
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False

ui: Any = _ui if _ui is not None else _Dummy()


# ============================================================
# Variables globales injectées depuis ogma_ng.py
# ============================================================
_chat_inner = None
_introspection_md_widget = None
_introspection_box_content = []
_cognitive_mirror = None
COGNITIVE_MIRROR_AVAILABLE = False
OGMA_CORE_AVAILABLE = False
_ensure_cognitive_mirror_core = None
_handle_cognitive_mirror_callback = None
_message = None  # Fonction d'affichage message


def _sync_introspection_globals():
    """
    Synchronise les variables globales depuis ogma_ng.py.
    Doit être appelée avant utilisation des fonctions de ce module.
    """
    global _chat_inner, _introspection_md_widget, _introspection_box_content
    global _cognitive_mirror, COGNITIVE_MIRROR_AVAILABLE, OGMA_CORE_AVAILABLE
    global _ensure_cognitive_mirror_core, _handle_cognitive_mirror_callback, _message
    
    try:
        import ogma_ng
        _chat_inner = getattr(ogma_ng, '_chat_inner', None)
        _introspection_md_widget = getattr(ogma_ng, '_introspection_md_widget', None)
        _introspection_box_content = getattr(ogma_ng, '_introspection_box_content', [])
        _cognitive_mirror = getattr(ogma_ng, '_cognitive_mirror', None)
        COGNITIVE_MIRROR_AVAILABLE = getattr(ogma_ng, 'COGNITIVE_MIRROR_AVAILABLE', False)
        OGMA_CORE_AVAILABLE = getattr(ogma_ng, 'OGMA_CORE_AVAILABLE', False)
        _handle_cognitive_mirror_callback = getattr(ogma_ng, '_handle_cognitive_mirror_callback', None)
        
        # Import _message depuis ogma_ui_conversations
        try:
            from ogma_ui_conversations import _message as msg_func
            _message = msg_func
        except ImportError:
            _message = None
        
        # Import _ensure_cognitive_mirror_core depuis modules.ogma_core
        try:
            from modules.ogma_core.controllers import ensure_cognitive_mirror as cm_core
            _ensure_cognitive_mirror_core = cm_core
        except ImportError:
            _ensure_cognitive_mirror_core = None
            
    except ImportError as e:
        print(f"[INTROSPECTION-UI] ⚠️ Erreur sync globals: {e}")


def _update_ogma_globals():
    """Met à jour les variables globales dans ogma_ng.py après modification."""
    global _introspection_md_widget, _introspection_box_content, _cognitive_mirror
    
    try:
        import ogma_ng
        ogma_ng._introspection_md_widget = _introspection_md_widget
        ogma_ng._introspection_box_content = _introspection_box_content
        ogma_ng._cognitive_mirror = _cognitive_mirror
    except ImportError:
        pass


# ============================================================
# TRAITEMENT MESSAGES SUBCONSCIENCE
# ============================================================

def _process_subconscience_messages():
    """Timer pour traiter les messages Subconscience - un déroulé par message"""
    global _chat_inner, _introspection_box_content, _introspection_md_widget
    
    # Synchroniser les globales
    _sync_introspection_globals()
    
    try:
        # Vérifier si l'extension est activée globalement
        from extensions.cognitive_mirror import is_enabled
        if not is_enabled():
            return
            
        # Vérifier si l'extension Subconscience est disponible et initialisée
        try:
            from extensions.subconscience import get_instance as get_subconscience
            subconscience = get_subconscience()
            if subconscience is None:
                return  # Extension pas encore initialisée
        except ImportError:
            return  # Extension pas disponible
        
        # Récupérer les messages en attente
        messages = subconscience.get_pending_messages()
        if not messages:
            return
        
        # Traiter chaque message
        for msg in messages:
            try:
                role = msg.get('role', 'subconscience')
                content = msg.get('content', '')
                original_role = msg.get('original_role', role)
                
                if not content:
                    continue
                
                # Afficher dans un déroulé dédié pour ce message
                if _chat_inner is not None:
                    with _chat_inner:
                        # Créer un déroulé séparé pour chaque message
                        with ui.expansion().classes('thinking-expansion subconscience-expansion') as exp:
                            # Déterminer le label selon le type
                            if original_role == 'archiviste':
                                label_text = '🧠 réflexion archiviste'
                                label_color = 'rgba(150, 200, 255, 0.7)'
                            elif original_role == 'metacognitive':
                                label_text = '🔮 analyse métacognitive'
                                label_color = 'rgba(200, 150, 255, 0.7)'
                            else:
                                label_text = '💭 subconscience'
                                label_color = 'rgba(180, 180, 180, 0.7)'
                            
                            exp.props('label=""')
                            with exp.add_slot('header'):
                                ui.html(f'<span style="color: {label_color}; font-size: 12px; font-style: italic;">{label_text}</span>')
                            
                            # Contenu du message
                            md_widget = ui.markdown(content)
                            md_widget.style(
                                'color: rgba(255, 255, 255, 0.85); '
                                'font-size: 13px; '
                                'line-height: 1.5; '
                                'margin: 0; '
                                'padding: 8px 0; '
                                'font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;'
                            )
                            md_widget.classes('subconscience-content')
                        
                        print(f"[SUBCONSCIENCE] OK Message {original_role} affiché dans déroulé séparé")
                        
            except Exception as e:
                print(f"[SUBCONSCIENCE] WARN Erreur traitement message: {e}")
                
    except ImportError:
        # Extension Subconscience pas disponible - pas d'erreur
        pass
    except Exception as e:
        print(f"[SUBCONSCIENCE-TIMER] ERROR Erreur traitement messages: {e}")


# ============================================================
# CALLBACKS INTROSPECTION
# ============================================================

def _on_synthesis_ready(synthesis_text: str):
    """Callback pour afficher la synthèse de réflexion dans l'UI principale"""
    global _chat_inner, _message
    
    _sync_introspection_globals()
    
    print(f"[COGNITIVE-MIRROR] 📝 Réception synthèse ({len(synthesis_text)} chars)")

    try:
        if _chat_inner is not None and _message is not None:
            with _chat_inner:
                _message('assistant', synthesis_text)
                print("[COGNITIVE-MIRROR] ✅ Synthèse affichée dans chat principal")
        else:
            print("[COGNITIVE-MIRROR] ⚠️ Chat inner non disponible - synthèse non affichée")
    except Exception as e:
        print(f"[COGNITIVE-MIRROR] ❌ Erreur affichage synthèse: {e}")


async def _on_introspection_message_callback(role: str, content: str):
    """Callback pour affichage temps réel des messages d'introspection"""
    global _introspection_md_widget, _introspection_box_content, _chat_inner
    
    _sync_introspection_globals()
    
    try:
        print(f"[INTROSPECTION-CALLBACK] 📝 Nouveau message {role}: {content[:50]}...")
        
        # 🔧 CORRECTION COMPATIBILITÉ: Créer boîte expansion si inexistante
        # (Cas: IA déclenche introspection via phrase magique dans SA réponse)
        if _introspection_md_widget is None and _chat_inner is not None:
            print("[INTROSPECTION-CALLBACK] 🆕 Création automatique boîte expansion")
            
            # Réinitialiser buffer
            _introspection_box_content = []
            
            with _chat_inner:
                with ui.expansion().classes('thinking-expansion') as introspection_box:
                    introspection_box.props('label=""')
                    with introspection_box.add_slot('header'):
                        ui.html('<span style="color: rgba(255, 200, 100, 0.7); font-size: 12px; font-style: italic;">🧠 introspection ia-principale-archiviste</span>')

                    _introspection_md_widget = ui.markdown("_Dialogue en cours..._")
                    _introspection_md_widget.style(
                        'color: rgba(255, 255, 255, 0.85); '
                        'font-size: 13px; '
                        'line-height: 1.5; '
                        'margin: 0; '
                        'padding: 8px 0; '
                        'font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;'
                    )
                    _introspection_md_widget.classes('introspection-dialogue')
                    
            print("[INTROSPECTION-CALLBACK] ✅ Boîte expansion créée automatiquement")
            _update_ogma_globals()
        
        if _introspection_md_widget is not None:
            # Ajouter le nouveau message au buffer
            if role == "analysis":
                # ÉTAPE 1: Analyse initiale
                formatted_message = f"📋 **ÉTAPE 1 - Analyse Initiale**\nIA Principale: {content}\n\n"
            elif role == "main_ai":
                # IA Principale dans le dialogue
                formatted_message = f"**IA Principale:** {content}\n\n"
            elif role == "archiviste":
                # Réponse Archiviste
                formatted_message = f"**Archiviste:** {content}\n\n"
            else:
                formatted_message = f"**{role.title()}:** {content}\n\n"
            
            _introspection_box_content.append(formatted_message)
            
            # Mettre à jour l'affichage
            full_content = "".join(_introspection_box_content)
            _introspection_md_widget.content = full_content
            print(f"[INTROSPECTION-CALLBACK] ✅ Affichage mis à jour ({len(_introspection_box_content)} messages)")
            _update_ogma_globals()
        
    except Exception as e:
        print(f"[INTROSPECTION-CALLBACK] ❌ Erreur affichage: {e}")


async def _on_message_ready(role: str, content: str):
    """Callback pour afficher un nouveau message d'introspection en temps réel"""
    global _introspection_box_content, _introspection_md_widget, _chat_inner

    _sync_introspection_globals()

    try:
        # 🔧 CORRECTION COMPATIBILITÉ: Créer boîte expansion si inexistante
        # (Cas: IA déclenche introspection via phrase magique dans SA réponse)
        if _introspection_md_widget is None and _chat_inner is not None:
            print("[INTROSPECTION] 🆕 Création automatique boîte expansion (IA déclenche)")
            
            # Réinitialiser buffer
            _introspection_box_content = []
            
            with _chat_inner:
                with ui.expansion().classes('thinking-expansion') as introspection_box:
                    introspection_box.props('label=""')
                    with introspection_box.add_slot('header'):
                        ui.html('<span style="color: rgba(255, 200, 100, 0.7); font-size: 12px; font-style: italic;">🧠 introspection ia-principale-archiviste</span>')

                    _introspection_md_widget = ui.markdown("_Dialogue en cours..._")
                    _introspection_md_widget.style(
                        'color: rgba(255, 255, 255, 0.85); '
                        'font-size: 13px; '
                        'line-height: 1.5; '
                        'margin: 0; '
                        'padding: 8px 0; '
                        'font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;'
                    )
                    _introspection_md_widget.classes('introspection-dialogue')
                    
            print("[INTROSPECTION] ✅ Boîte expansion créée automatiquement")
            _update_ogma_globals()
        
        # Ajouter au buffer
        _introspection_box_content.append({"role": role, "content": content})

        # Formater le contenu selon les 5 étapes v2.0
        formatted_lines = []
        
        # Séparer les messages par type pour affichage structuré
        analysis_msg = None
        dialogue_msgs = []
        synthesis_msg = None
        
        for msg in _introspection_box_content:
            if msg["role"] == "analysis":
                analysis_msg = msg
            elif msg["role"] in ["main_ai", "archiviste"]:
                dialogue_msgs.append(msg)
            elif msg["role"] == "synthesis":
                synthesis_msg = msg

        # Analyse initiale (sans titre d'étape)
        if analysis_msg:
            formatted_lines.append("**IA Principale :**")
            formatted_lines.append(f"{analysis_msg['content']}")
            formatted_lines.append("")  # Saut de ligne

        # Dialogue (sans titre d'étape, formatage naturel)
        if dialogue_msgs:
            current_speaker = None
            for msg in dialogue_msgs:
                speaker = "**IA Principale :**" if msg["role"] == "main_ai" else "**Archiviste :**"
                
                # Saut de ligne entre différents intervenants
                if current_speaker and current_speaker != speaker:
                    formatted_lines.append("")
                
                formatted_lines.append(speaker)
                formatted_lines.append(f"{msg['content']}")
                formatted_lines.append("")  # Saut de ligne après chaque intervention
                current_speaker = speaker

        # Synthèse finale (sans titre d'étape)
        if synthesis_msg:
            if dialogue_msgs or analysis_msg:  # Saut supplémentaire avant synthèse
                formatted_lines.append("---")
                formatted_lines.append("")
            formatted_lines.append("**IA Principale :**")
            formatted_lines.append(f"{synthesis_msg['content']}")
            formatted_lines.append("")

        # Note: ÉTAPE 5 (réponse utilisateur) va maintenant dans la conversation principale uniquement
        
        full_content = "\n".join(formatted_lines)

        # Mettre à jour le widget si disponible
        if _introspection_md_widget:
            _introspection_md_widget.set_content(full_content)
            print(f"[INTROSPECTION] 💬 Message {role} affiché")
            
            # 🔧 FIX: Réinitialiser après la synthèse finale pour permettre nouvelle boîte
            if role == "synthesis":
                print("[INTROSPECTION] 🔄 Réinitialisation variables pour prochaine session")
                _introspection_md_widget = None
                _introspection_box_content = []
                _update_ogma_globals()
        else:
            print(f"[INTROSPECTION] ⚠️ Widget markdown non disponible")

        _update_ogma_globals()

    except Exception as e:
        print(f"[INTROSPECTION] ❌ Erreur affichage message: {e}")


# ============================================================
# ENSURE COGNITIVE MIRROR
# ============================================================

def _ensure_cognitive_mirror():
    """Wrapper: Délègue à ogma_core.controllers avec callbacks UI"""
    global _cognitive_mirror, _ensure_cognitive_mirror_core, _handle_cognitive_mirror_callback
    global OGMA_CORE_AVAILABLE, COGNITIVE_MIRROR_AVAILABLE
    
    _sync_introspection_globals()
    
    if OGMA_CORE_AVAILABLE and _cognitive_mirror is None and _ensure_cognitive_mirror_core is not None:
        result = _ensure_cognitive_mirror_core()
        _cognitive_mirror = result
        # Configurer les callbacks UI si extension disponible
        if _cognitive_mirror:
            try:
                if hasattr(_cognitive_mirror, 'on_message_ready'):
                    _cognitive_mirror.on_message_ready = _on_introspection_message_callback
                if hasattr(_cognitive_mirror, 'set_callbacks'):
                    _cognitive_mirror.set_callbacks(
                        on_state_change=None,
                        on_reflection_start=None,
                        on_reflection_end=None,
                        on_external_settings_change=_handle_cognitive_mirror_callback,
                        on_synthesis_ready=_on_synthesis_ready,
                        on_message_ready=_on_message_ready
                    )
                print("[COGNITIVE-MIRROR] ✅ Callbacks UI configurés")
            except Exception as e:
                print(f"[COGNITIVE-MIRROR] ⚠️ Erreur config callbacks: {e}")
        _update_ogma_globals()
        return result
    if _cognitive_mirror is not None:
        return _cognitive_mirror
    # Fallback si module non disponible
    if not COGNITIVE_MIRROR_AVAILABLE:
        return None
    return None
