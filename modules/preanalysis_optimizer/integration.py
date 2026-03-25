"""
PREANALYSIS INTEGRATION - Intégration du module preanalysis_optimizer dans OGMA
================================================================================

Ce fichier fournit les fonctions d'intégration avec ogma_ng.py.
Conçu pour modifications minimales du fichier principal.

USAGE dans ogma_ng.py:

    # En haut du fichier (imports)
    from modules.preanalysis_optimizer.integration import (
        trigger_preanalysis_on_typing,
        get_optimized_context_for_message,
        on_conversation_change
    )
    
    # Dans _input_overlay(), après création du textarea:
    input_field.on('focus', trigger_preanalysis_on_typing)
    input_field.on('input', trigger_preanalysis_on_typing)
    
    # Dans _send_chat_message(), AVANT run_ego_selector_analysis:
    optimized = await get_optimized_context_for_message(text, _chat_history, ...)
    if optimized.get('ego_injection'):
        ego_injection = optimized['ego_injection']
        # Skip run_ego_selector_analysis
        
    # Dans _load_conversation() ou _new_conversation():
    on_conversation_change(conversation_id)

Auteur: OGMA Team
Date: 7 décembre 2025
"""

import asyncio
from typing import Optional, Dict, Any

# Import lazy du module principal
_optimizer = None
_is_enabled = True

def _ensure_optimizer():
    """Lazy load de l'optimizer"""
    global _optimizer
    if _optimizer is None:
        try:
            from modules.preanalysis_optimizer import get_optimizer
            _optimizer = get_optimizer()
            print("[PREANALYSIS-INTEGRATION] ✅ Optimizer chargé")
        except ImportError as e:
            print(f"[PREANALYSIS-INTEGRATION] ⚠️ Module non disponible: {e}")
            return None
    return _optimizer


def set_preanalysis_enabled(enabled: bool):
    """Active/désactive le système de pré-analyse"""
    global _is_enabled
    _is_enabled = enabled
    state = "activé" if enabled else "désactivé"
    print(f"[PREANALYSIS-INTEGRATION] 🔧 Système {state}")


def trigger_preanalysis_on_typing(event=None):
    """
    Callback à brancher sur les événements input/focus.
    
    Déclenche les pré-analyses en arrière-plan pendant que l'utilisateur tape.
    
    Usage NiceGUI:
        input_field.on('focus', trigger_preanalysis_on_typing)
        input_field.on('input', trigger_preanalysis_on_typing)
    """
    if not _is_enabled:
        return
    
    optimizer = _ensure_optimizer()
    if optimizer is None:
        return
    
    # Récupérer l'historique conversation global
    try:
        # Import depuis ogma_ng pour accéder à _chat_history
        import ogma_ng
        conversation_history = getattr(ogma_ng, '_chat_history', [])
        
        # Déclencher pré-analyse
        optimizer.trigger_preanalysis(conversation_history)
        
    except Exception as e:
        # Silencieux - ne pas perturber l'UX
        pass


async def get_optimized_context_for_message(
    user_message: str,
    conversation_history: list,
    memory_manager=None,
    archiviste_controller=None,
    memory_optimizer=None,
    fallback_ego_fn=None,
    fallback_capability_fn=None,
    temporal_guardian=None,
    temporal_data=None,
    memory_titles_found: list = None
) -> Dict[str, Any]:
    """
    Récupère le contexte optimisé pour un message.
    
    Utilise pré-analyses + cache + parallélisation.
    Fallback sur les fonctions existantes si optimizer indisponible.
    
    Args:
        user_message: Message utilisateur
        conversation_history: Historique conversation
        memory_manager: Gestionnaire mémoire OGMA
        archiviste_controller: Contrôleur Archiviste
        memory_optimizer: ArchivisteMemoryOptimizer
        fallback_ego_fn: Fonction ego existante (run_ego_selector_analysis)
        fallback_capability_fn: Fonction capability existante
        temporal_guardian: Instance Temporal Guardian (optionnel)
        temporal_data: Données temporelles (optionnel)
        
    Returns:
        dict: {
            'ego_injection': str,
            'capability_suggestion': dict,
            'archi_guidance': str,
            'memory_context': str,
            'memory_details': list,
            'temporal_instruction': str,   # NOUVEAU
            'optimized': bool  # True si optimizer utilisé
        }
    """
    if not _is_enabled:
        return {'optimized': False}
    
    optimizer = _ensure_optimizer()
    
    if optimizer is None:
        # Fallback mode - utiliser fonctions existantes
        return await _fallback_context(
            user_message, conversation_history,
            memory_manager, archiviste_controller,
            fallback_ego_fn, fallback_capability_fn
        )
    
    try:
        # Utiliser optimizer avec paramètres temporels
        result = await optimizer.get_optimized_context(
            user_message=user_message,
            conversation_history=conversation_history,
            memory_manager=memory_manager,
            archiviste_controller=archiviste_controller,
            memory_optimizer=memory_optimizer,
            temporal_guardian=temporal_guardian,
            temporal_data=temporal_data,
            memory_titles_found=memory_titles_found
        )
        
        result['optimized'] = True
        return result
        
    except Exception as e:
        print(f"[PREANALYSIS-INTEGRATION] ❌ Erreur optimizer: {e}")
        # Fallback
        return await _fallback_context(
            user_message, conversation_history,
            memory_manager, archiviste_controller,
            fallback_ego_fn, fallback_capability_fn
        )


async def _fallback_context(
    user_message: str,
    conversation_history: list,
    memory_manager,
    archiviste_controller,
    fallback_ego_fn,
    fallback_capability_fn
) -> Dict[str, Any]:
    """Mode fallback - appels séquentiels classiques"""
    result = {
        'ego_injection': '',
        'capability_suggestion': None,
        'archi_guidance': '',
        'memory_context': '',
        'memory_details': [],
        'optimized': False
    }
    
    # Ego Selector fallback
    if fallback_ego_fn:
        try:
            history_for_ego = conversation_history[-6:] if len(conversation_history) > 6 else conversation_history
            ego = await fallback_ego_fn(user_message, history_for_ego, memory_manager)
            result['ego_injection'] = ego or ''
        except Exception as e:
            print(f"[PREANALYSIS-INTEGRATION] ⚠️ Ego fallback erreur: {e}")
    
    return result


def on_conversation_change(conversation_id: str = None):
    """
    À appeler quand la conversation change (nouvelle conversation ou chargement).
    
    Invalide le cache et réinitialise les pré-analyses.
    """
    optimizer = _ensure_optimizer()
    if optimizer:
        optimizer.invalidate_cache()
        print(f"[PREANALYSIS-INTEGRATION] 🔄 Cache invalidé (conversation: {conversation_id})")


def get_optimization_stats() -> Dict[str, Any]:
    """
    Retourne les statistiques d'optimisation.
    
    Returns:
        dict: Stats cache hits, pré-analyses, latences, etc.
    """
    optimizer = _ensure_optimizer()
    if optimizer is None:
        return {'enabled': False, 'available': False}
    
    return {
        'enabled': _is_enabled,
        'available': True,
        'optimizer_stats': optimizer.get_stats(),
        'preanalysis_status': optimizer.get_status()
    }


# ============================================================================
# HOOKS POUR INTÉGRATION FACILE
# ============================================================================

def get_javascript_hooks() -> str:
    """
    Retourne le JavaScript à injecter pour déclencher les pré-analyses.
    
    Alternative à l'approche Python pure pour réactivité maximale.
    
    Usage:
        ui.run_javascript(get_javascript_hooks())
    """
    return """
    // Hook sur focus input pour pré-analyses
    document.addEventListener('focusin', function(e) {
        if (e.target.classList.contains('input-field') || 
            e.target.closest('.input-field')) {
            // Appeler backend Python via websocket
            pywebview.api.trigger_preanalysis && pywebview.api.trigger_preanalysis();
        }
    });
    
    // Debounced hook sur input
    let preanalysisTimer = null;
    document.addEventListener('input', function(e) {
        if (e.target.classList.contains('input-field') || 
            e.target.closest('.input-field')) {
            clearTimeout(preanalysisTimer);
            preanalysisTimer = setTimeout(function() {
                pywebview.api.trigger_preanalysis && pywebview.api.trigger_preanalysis();
            }, 500);  // 500ms debounce
        }
    });
    """


# ============================================================================
# INSTRUCTIONS D'INTÉGRATION
# ============================================================================

INTEGRATION_INSTRUCTIONS = """
# 🚀 INSTRUCTIONS D'INTÉGRATION PREANALYSIS OPTIMIZER

## 1. Import dans ogma_ng.py (ligne ~50, section imports)

```python
# Preanalysis Optimizer - Optimisation latence
try:
    from modules.preanalysis_optimizer.integration import (
        trigger_preanalysis_on_typing,
        get_optimized_context_for_message,
        on_conversation_change,
        set_preanalysis_enabled
    )
    PREANALYSIS_AVAILABLE = True
except ImportError:
    PREANALYSIS_AVAILABLE = False
    print("[OGMA] ⚠️ Module preanalysis_optimizer non disponible")
```

## 2. Hook dans _input_overlay() (après création input_field, ~ligne 5125)

```python
_input_field = ui.textarea(placeholder='Écrire un message...').props('autogrow').classes('input-field')

# 🚀 PREANALYSIS: Déclencher pré-analyses au focus/input
if PREANALYSIS_AVAILABLE:
    _input_field.on('focus', trigger_preanalysis_on_typing)
```

## 3. Dans _send_chat_message(), section EGO (~ligne 4072)

AVANT:
```python
from logic_callbacks import run_ego_selector_analysis
ego_injection = await run_ego_selector_analysis(text, history_for_ego, memory_mgr)
```

APRÈS:
```python
# 🚀 PREANALYSIS: Utiliser contexte optimisé si disponible
if PREANALYSIS_AVAILABLE:
    optimized_ctx = await get_optimized_context_for_message(
        user_message=text,
        conversation_history=_chat_history,
        memory_manager=memory_mgr,
        archiviste_controller=_ensure_archiviste_controller()
    )
    if optimized_ctx.get('optimized'):
        ego_injection = optimized_ctx.get('ego_injection', '')
        print(f"[PREANALYSIS] ⚡ Contexte optimisé utilisé")
    else:
        # Fallback séquentiel
        from logic_callbacks import run_ego_selector_analysis
        ego_injection = await run_ego_selector_analysis(text, history_for_ego, memory_mgr)
else:
    from logic_callbacks import run_ego_selector_analysis
    ego_injection = await run_ego_selector_analysis(text, history_for_ego, memory_mgr)
```

## 4. Dans _load_conversation() et _new_conversation()

```python
# 🚀 PREANALYSIS: Invalider cache au changement conversation
if PREANALYSIS_AVAILABLE:
    on_conversation_change(conversation_id)
```

## 5. (Optionnel) Debug dans header settings

Ajouter option pour activer/désactiver:
```python
ui.switch('Optimisation latence', value=True, on_change=lambda e: set_preanalysis_enabled(e.value))
```
"""


def print_integration_instructions():
    """Affiche les instructions d'intégration"""
    print(INTEGRATION_INSTRUCTIONS)


if __name__ == "__main__":
    print_integration_instructions()
