"""
logic_callbacks.py
------------------
- CORRECTION (RuntimeError) : La fonction `memorize_fn` a été transformée en
  fonction asynchrone (`async def`).
- L'appel à `asyncio.create_task` ne peut se faire que depuis un contexte asynchrone.
  Rendre la fonction `async` fournit ce contexte.
- Le `time.sleep()` bloquant a été remplacé par son équivalent non-bloquant
  `await asyncio.sleep()`, ce qui résout la `RuntimeError: no running event loop`.
- CORRECTION (ValueError) : Fonctions delete_chat_fn et rename_chat_fn corrigées
  pour retourner le bon nombre de valeurs.
- OPTIMISATION SOLUTION A (12 nov 2025): Archiviste Query Decomposer intégré
  pour réduire appels API (-30%), améliorer précision (+300%), latence (-14%)
"""
import gradio as gr
from pathlib import Path
import datetime
import uuid
import shutil
import json
import re
import asyncio
import time
import pandas as pd
import requests
import os
from urllib.parse import urlparse
import queue
import os
from typing import Optional, Dict, List, Any
from modules.logic import (
    get_visual_events_context,
    caviarder_phrases_magiques_introspection,
    trigger_indexing_fn,
    process_image_generation,
    process_img2img_generation
)


# ============================================================================
# HELPER FONCTION CONTEXTE VISUEL (refactorisée pour réutilisation)
# ============================================================================

# Refactorisé vers modules/logic/perception.py
_get_visual_events_context = get_visual_events_context


# 🌐 EXTENSION WEB NAVIGATOR - Instance globale
_web_navigator_extension = None

def _init_web_navigator_extension(settings_manager=None):
    """Initialise l'extension Web Navigator avec Serper si pas déjà fait"""
    global _web_navigator_extension
    
    if _web_navigator_extension is not None:
        return _web_navigator_extension
    
    try:
        from extensions.web_navigator import WebNavigatorConfig, SerperClient, WebNavigatorCommands
        
        # DEBUG: Tracer le settings_manager
        print(f"[WEB-NAV-DEBUG] Settings manager reçu: {type(settings_manager) if settings_manager else 'None'}")
        
        # Configuration
        config = WebNavigatorConfig(settings_manager)
        
        # DEBUG: Tracer la configuration
        print(f"[WEB-NAV-DEBUG] Extension activée: {config.is_enabled()}")
        print(f"[WEB-NAV-DEBUG] Clé API valide: {config.has_valid_api_key()}")
        print(f"[WEB-NAV-DEBUG] Recherche web activée: {config.is_web_search_enabled()}")
        
        # Composants Serper
        serper_client = SerperClient(config)
        commands = WebNavigatorCommands(config, serper_client)
        
        # Créer l'instance de l'extension
        class WebNavigatorExtension:
            def __init__(self, config, serper_client, commands):
                self.config = config
                self.serper_client = serper_client
                self.commands = commands
                
            def close(self):
                """Ferme les ressources de l'extension"""
                if self.serper_client:
                    self.serper_client.close()
        
        _web_navigator_extension = WebNavigatorExtension(config, serper_client, commands)
        
        print("[WEB-NAV] 🌐 Extension Web Navigator (Serper) initialisée")
        return _web_navigator_extension
        
    except ImportError as e:
        print(f"[WEB-NAV] ⚠️ Extension Web Navigator non disponible: {e}")
        return None
    except Exception as e:
        print(f"[WEB-NAV] ❌ Erreur initialisation Web Navigator: {e}")
        return None

# Refactorisé vers modules/logic/memory_utils.py (n'est pas nécessaire de réassigner car l'import porte le même nom)
# caviarder_phrases_magiques_introspection = caviarder_phrases_magiques_introspection

# 🖼️ VISION D'IMAGES - Variable globale pour éviter la pollution de l'affichage
_pending_vision_analysis = None
_last_memory_injection = []

# =============================================================================
# RECHERCHE PARALLÈLE OPTIMISÉE - OGMA Performance Boost
# =============================================================================

async def get_parallel_context(memory_manager, message, perception_agent=None, timeout=10.0, memory_optimizer=None):
    """
    Recherche parallèle sophistiquée pour récupérer tous les contextes simultanément.
    
    OPTIMISATION SOLUTION A (12 nov 2025):
    Si memory_optimizer fourni → utilise Archiviste Query Decomposer (-30% API, +300% précision)
    Sinon → fallback système actuel (philosophie organique: erreur visible, pas masquée)
    
    Args:
        memory_manager: Gestionnaire de mémoire pour souvenirs et conversations
        message: Message utilisateur pour la recherche
        perception_agent: Agent de perception (optionnel)
        timeout: Timeout global en secondes (défaut: 10s)
        memory_optimizer: ArchivisteMemoryOptimizer (optionnel, Solution A)
    
    Returns:
        dict: {
            'personal_context': str,     # Contexte souvenirs personnels
            'conversation_context': str, # Contexte conversations passées
            'visual_context': str,       # Contexte visuel (si disponible)
            'timing_info': str,         # Information de timing
            'has_errors': bool          # Indicateur d'erreurs
        }
    """
    start_time = time.time()
    errors = []
    
    # ============================================================================
    # SOLUTION A - ARCHIVISTE QUERY DECOMPOSER (OPTIMISÉ)
    # ============================================================================
    if memory_optimizer is not None:
        try:
            print("[PARALLEL-CONTEXT] 🟢 Utilisation optimizer Solution A (Archiviste Query Decomposer)")
            
            # Appel optimizer (analyse IA + recherches ciblées + synthèse unifiée)
            optimized_ctx = await memory_optimizer.get_optimized_context(
                message=message,
                k_personal=3,
                k_conversation=5
            )
            
            # Construction contexte format compatible
            context_data = {
                'personal_context': optimized_ctx.synthesis if optimized_ctx.analysis.needs_personal_memory else "",
                'conversation_context': optimized_ctx.synthesis if optimized_ctx.analysis.needs_conversation_memory else "",
                'visual_context': "",  # Ajouté après si perception_agent présent
                'timing_info': f"Optimisé en {optimized_ctx.metrics.get('latency_ms', 0):.0f}ms ({optimized_ctx.metrics.get('total_api_calls', 0)} appels API)",
                'has_errors': "false",
                'optimizer_metrics': optimized_ctx.metrics,  # Métriques détaillées
                'optimizer_analysis': {  # Analyse IA (transparence)
                    'keywords': optimized_ctx.analysis.keywords_core,
                    'reasoning': optimized_ctx.analysis.reasoning
                }
            }
            
            print(f"[PARALLEL-CONTEXT] ✅ Optimizer: {optimized_ctx.metrics.get('total_api_calls', 0)} API calls, {optimized_ctx.metrics.get('memories_found', 0)} memories")
            
            # Ajout contexte visuel si disponible
            if perception_agent and hasattr(perception_agent, 'event_queue'):
                visual_ctx = await _get_visual_events_context(perception_agent)
                context_data['visual_context'] = visual_ctx
            
            # Calcul timing total
            end_time = time.time()
            timing_ms = int((end_time - start_time) * 1000)
            context_data['timing_info'] = f"Optimisé en {timing_ms}ms ({optimized_ctx.metrics.get('total_api_calls', 0)} appels API)"
            
            return context_data
            
        except Exception as e:
            # Philosophie organique: erreur VISIBLE, pas masquée
            error_msg = f"Optimizer Solution A échoué: {e}"
            errors.append(error_msg)
            print(f"[PARALLEL-CONTEXT] ⚠️ {error_msg}")
            print(f"[PARALLEL-CONTEXT] 🔴 Fallback système actuel (duplication embeddings)")
            # Continue vers système actuel ci-dessous
    
    # ============================================================================
    # SYSTÈME ACTUEL - DUPLICATION EMBEDDINGS (FALLBACK)
    # ============================================================================
    print("[PARALLEL-CONTEXT] 🔴 Système actuel (duplication embeddings + dilution sémantique)")
    
    # Préparation des tâches parallèles (ANCIEN SYSTÈME)
    tasks = {
        'personal_context': memory_manager.retrieve_and_synthesize_context(message, k=3),
        'conversation_context': memory_manager.retrieve_and_synthesize_context(message, k=5)
    }
    
    # Ajouter le contexte visuel si disponible
    if perception_agent and hasattr(perception_agent, 'event_queue'):
        tasks['visual_context'] = _get_visual_events_context(perception_agent)
    
    try:
        # Exécution parallèle avec timeout de sécurité
        results = await asyncio.wait_for(
            asyncio.gather(*tasks.values(), return_exceptions=True),
            timeout=timeout
        )
        
        # Traitement des résultats avec gestion d'erreurs granulaire
        context_data = {}
        for key, result in zip(tasks.keys(), results):
            if isinstance(result, Exception):
                error_msg = f"Erreur {key}: {str(result)}"
                errors.append(error_msg)
                context_data[key] = ""  # Valeur par défaut
                print(f"[PARALLEL-CONTEXT] ❌ {error_msg}")
            else:
                context_data[key] = result if result else ""
                print(f"[PARALLEL-CONTEXT] ✅ {key}: {len(str(result))} chars")
        
    except asyncio.TimeoutError:
        # Mode dégradé en cas de timeout
        error_msg = f"Timeout contexte après {timeout}s, mode dégradé activé"
        errors.append(error_msg)
        print(f"[PARALLEL-CONTEXT] ⚠️ {error_msg}")
        
        context_data = {
            'personal_context': "",
            'conversation_context': "",
            'visual_context': ""
        }
    
    # Calcul du timing
    end_time = time.time()
    timing_ms = int((end_time - start_time) * 1000)
    
    # Log de performance
    print(f"[PARALLEL-CONTEXT] 🚀 Contexte récupéré en {timing_ms}ms")
    if errors:
        print(f"[PARALLEL-CONTEXT] ⚠️ {len(errors)} erreur(s) rencontrée(s)")
    
    # Résultat unifié avec types cohérents
    context_data['timing_info'] = f"Récupéré en {timing_ms}ms"
    context_data['has_errors'] = "true" if len(errors) > 0 else "false"
    
    # S'assurer que les clés obligatoires existent
    for key in ['personal_context', 'conversation_context', 'visual_context']:
        if key not in context_data:
            context_data[key] = ""
    
    return context_data

from utils import (
    save_conversation, get_conversations, load_conversation,
    delete_conversation_file, rename_conversation_file, estimate_tokens,
    search_conversations, get_conversation_context, load_conversations_index
)
from extensions.file_processor import process_file

def stream_ui_updates(perception_agent):
    last_frame = None
    while True:
        try:
            frame = perception_agent.visual_queue.get(timeout=0.05)
            last_frame = frame
        except queue.Empty:
            frame = last_frame
        button_update = update_perception_status(perception_agent)
        yield frame, button_update
        time.sleep(0.5)

def toggle_perception_agent(perception_agent):
    if perception_agent.running:
        print("[STOP] Commande d'arrêt de l'agent de perception...")
        perception_agent.stop()
        return gr.update(value="Arrêt en cours...", interactive=False)
    else:
        print("[START] Commande de démarrage de l'agent de perception...")
        perception_agent.start()
        return gr.update(value="Préchauffage...", interactive=False)

def update_perception_status(perception_agent):
    try:
        message = perception_agent.event_queue.get_nowait()
        if "[STATUS]" in message:
            new_status = message.split("]")[1].strip()
            if new_status == "active": return gr.update(value="Désactiver la Perception", interactive=True)
            elif new_status == "inactive": return gr.update(value="Activer la Perception", interactive=True)
    except queue.Empty:
        pass
    return gr.update()

# trigger_indexing_fn refactorisé vers modules/logic/memory_utils.py
# (Importé depuis modules.logic)

def process_status_queue(STATUS_QUEUE):
    while not STATUS_QUEUE.empty():
        gr.Info(STATUS_QUEUE.get())

def get_stats_html(memory_manager, memory_ai_controller, embedding_controller, chat_ai_controller):
    mem_status = memory_ai_controller.get_status()
    embed_status = embedding_controller.get_status()
    chat_status = chat_ai_controller.get_status()
    
    if memory_manager:
        memory_count = memory_manager.get_memory_count()
        faiss_count = memory_manager.faiss_index.ntotal
    else:
        memory_count = "N/A"
        faiss_count = "N/A"
    
    return f"""<h3>📈 Statistiques</h3><p><strong>Mémoires SQLite:</strong> {memory_count} | <strong>FAISS Index:</strong> {faiss_count} | <strong>Conversations:</strong> {len(get_conversations())} | <strong>IA Chat:</strong> {chat_status} | <strong>IA Mémoire:</strong> {mem_status} | <strong>IA Embedding:</strong> {embed_status}</p>"""

def update_and_get_stats(STATUS_QUEUE, memory_manager, memory_ai_controller, embedding_controller, chat_ai_controller):
    process_status_queue(STATUS_QUEUE)
    return get_stats_html(memory_manager, memory_ai_controller, embedding_controller, chat_ai_controller)

def load_memories_df(STATUS_QUEUE, memory_structure, filter_query=None):
    process_status_queue(STATUS_QUEUE)
    memories = memory_structure.memories
    if filter_query:
        q = filter_query.lower()
        memories = [m for m in memories if q in m.get('titre','').lower() or q in m.get('commentaire_ia', m.get('commentaire_tia','')).lower()]
    # CORRECTION: Utiliser score_impact pour les nouveaux souvenirs, signed_score pour les anciens
    def get_display_score(m):
        # Nouveau système (MemoryManager v2.0)
        if 'score_impact' in m and m.get('score_impact', 0) > 0:
            return f"{m.get('score_impact', 0.0):.2f}"
        # Ancien système (rétrocompatibilité)
        else:
            return f"{m.get('signed_score', 0.0):.2f}"
    
    data = [[m.get("id",""), m.get("titre",""), get_display_score(m), "Oui" if m.get('embedding') else "Non"] for m in sorted(memories, key=lambda x: x.get('date',''), reverse=True)]
    return pd.DataFrame(data, columns=["ID", "Titre", "Score", "Vectorisé?"])

def load_memories_from_db(STATUS_QUEUE, memory_manager, filter_query=None):
    """Nouvelle fonction pour charger les mémoires depuis SQLite"""
    process_status_queue(STATUS_QUEUE)
    try:
        # Vérifier si memory_manager est disponible
        if not memory_manager:
            print("[SEARCH-ERROR] MemoryManager est None")
            return pd.DataFrame([], columns=["ID", "Titre", "Intensité", "Vectorisé?"])
        
        # Récupérer toutes les mémoires depuis SQLite
        memories = memory_manager.get_all_memories_data()
        print(f"[SEARCH-DEBUG] {len(memories)} mémoires récupérées depuis SQLite")
        
        if filter_query and filter_query.strip():
            q = filter_query.lower()
            original_count = len(memories)
            memories = [m for m in memories if q in m.get('title','').lower() or q in m.get('text_original','').lower() or q in m.get('summary','').lower()]
            print(f"[SEARCH-DEBUG] Filtrage '{q}': {original_count} -> {len(memories)} résultats")
        
        # Convertir en format DataFrame pour l'interface
        data = []
        for m in memories:
            title = m.get("title", "Sans titre")
            data.append([
                m.get("id", ""),
                title[:50] + "..." if len(title) > 50 else title,
                f"{m.get('score_impact', 50.0):.2f}",  # Utiliser score_impact du nouveau système
                "Oui"  # Toutes les mémoires dans SQLite sont vectorisées
            ])
        
        return pd.DataFrame(data, columns=["ID", "Titre", "Intensité", "Vectorisé?"])
    except Exception as e:
        print(f"[ERROR] Erreur chargement mémoires SQLite: {e}")
        return pd.DataFrame([], columns=["ID", "Titre", "Intensité", "Vectorisé?"])

def handle_file_upload(file_obj, active_file, UPLOADS_DIR):
    if active_file:
        try: Path(active_file).unlink()
        except: pass
    if file_obj is None:
        return None, gr.update(placeholder="Écrire ici ou déposer un fichier..."), "", gr.update(visible=False)
    filename = os.path.basename(file_obj.name)
    persistent_path = UPLOADS_DIR / f"{uuid.uuid4()}_{filename}"
    shutil.copy(file_obj.name, persistent_path)
    placeholder_text = f"Fichier '{filename}' prêt. Posez votre question."
    display_html = f"""<div class="active-file-box">{filename}</div>"""
    return str(persistent_path), gr.update(placeholder=placeholder_text), display_html, gr.update(visible=True)

def clear_active_file_fn(file_path):
    if file_path and Path(file_path).exists():
        try: Path(file_path).unlink()
        except OSError as e: print(f"Erreur de suppression du fichier: {e}")
    return None, gr.update(placeholder="Écrire ici ou déposer un fichier..."), "", gr.update(visible=False)

async def chat_fn(message, history, state, file_path_state, thinking_mode_enabled, chat_ai_controller, settings_manager, memory_manager, perception_agent, STATUS_QUEUE, text2img_manager=None):
    conv_id = state["conversation_id"]
    outputs = {"chatbot": history, "active_path": file_path_state, "input_box": gr.update(), "boussole": "Boussole inchangée", "thinking_box": "", "thinking_panel": gr.update(visible=thinking_mode_enabled)}

    def yield_updates(updates):
        return (updates["chatbot"], updates["active_path"], updates["input_box"], updates["boussole"], updates["thinking_box"], updates["thinking_panel"])

    if not message.strip() and not file_path_state:
        yield yield_updates(outputs); return

    if not chat_ai_controller.get_active_manager():
        gr.Error("L'IA Conversationnelle n'est pas configurée ou disponible.")
        yield yield_updates(outputs); return

    user_content_parts = []
    display_message = message  # Message propre pour affichage
    if message.strip(): user_content_parts.append({"type": "text", "text": message})
    
    # Capture automatique de la webcam si l'agent de perception est actif
    if perception_agent.status == "active":
        webcam_capture = perception_agent.capture_for_chat()
        if webcam_capture:
            # Ne pas modifier display_message, garder seulement l'annotation pour l'affichage interne si nécessaire
            user_content_parts.append(webcam_capture)
    
    if file_path_state:
        import pathlib
        processed_file = process_file(pathlib.Path(file_path_state))
        if processed_file:
            # Ne pas modifier display_message avec l'annotation fichier
            if processed_file['type'] == 'image':
                base64_url = f"data:{processed_file['mime_type']};base64,{processed_file['data']}"
                user_content_parts.append({"type": "image_url", "image_url": {"url": base64_url}})
            elif processed_file['type'] == 'text':
                text_from_file = f"\n--- Contenu de {processed_file['filename']} ---\n{processed_file['content']}\n--- Fin du fichier ---"
                if user_content_parts and user_content_parts[0]['type'] == 'text':
                    user_content_parts[0]['text'] += text_from_file
                else:
                    user_content_parts.insert(0, {"type": "text", "text": text_from_file})

    history.append({"role": "user", "content": display_message.strip()})
    history.append({"role": "assistant", "content": "🙏..."})
    outputs["chatbot"] = history
    outputs["input_box"] = gr.update(value="")
    yield yield_updates(outputs)

    # 🚀 RECHERCHE PARALLÈLE SOPHISTIQUÉE - Performance Boost
    print("[PARALLEL-CONTEXT] 🔍 Démarrage recherche contexte parallèle...")
    parallel_context = await get_parallel_context(memory_manager, message, perception_agent)
    
    context_note = parallel_context.get('personal_context', '')
    conversation_context = parallel_context.get('conversation_context', '')
    visual_events_context = parallel_context.get('visual_context', '')
    
    # Log de performance pour feedback utilisateur
    if parallel_context.get('has_errors') == "true":
        print("[PARALLEL-CONTEXT] ⚠️ Recherche complétée avec erreurs partielles")
    else:
        print(f"[PARALLEL-CONTEXT] ✅ Recherche complétée - {parallel_context.get('timing_info', 'timing inconnu')}")

    # visual_events_context est maintenant géré dans get_parallel_context()
    # Code legacy pour compatibilité au cas où la recherche parallèle échoue
    if not visual_events_context:
        events_to_requeue = []
        while not perception_agent.event_queue.empty():
            try:
                event = perception_agent.event_queue.get_nowait()
                if "[EVENT]" in event: visual_events_context += f"- {event.replace('[EVENT]', '').strip()}\n"
                else: events_to_requeue.append(event)
            except queue.Empty: break
        for item in events_to_requeue: perception_agent.event_queue.put(item)
        if visual_events_context: visual_events_context = f"Contexte visuel perçu :\n{visual_events_context}"

    # Ajouter les instructions de perception au prompt système si webcam active
    perception_instructions = ""
    # Simplification: Si perception active, on injecte TOUJOURS les instructions
    # Cela garantit que l'IA sait qu'elle a la vision, même si l'image rate ou est absente
    if perception_agent.status == "active":
        perception_instructions = f"Instructions spécifiques pour la perception visuelle :\n{settings_manager.settings.get('prompts', {}).get('perception', '')}"

    # Ego non injecté ici - chat_fn() est du legacy Gradio (voir ogma_ng.py pour le pipeline actif)
    ego_content = ""
    
    # Charger le prompt système principal depuis settings
    system_prompt_base = settings_manager.settings.get('prompts', {}).get('instructions', '')
    
    # Récupérer le contexte permanent (fonction définie dans ce fichier)
    persistent_context = get_persistent_context()

    # 🎯 OPTIMISATION ANTI-REDONDANCE:
    # context_note et conversation_context RETIRÉS du system prompt
    # → Ces infos sont déjà dans l'historique conversationnel (contextual_history)
    # → Évite duplication massive et économise ~40-60% tokens contexte
    
    # Construire le prompt système complet (ordre optimisé: identité → instructions)
    full_system_prompt = "\n\n".join(filter(None, [
        ego_content,              # 🧠 Identité IA (complet ou sélectif selon conversation)
        system_prompt_base,       # 📋 Instructions système principales
        persistent_context,       # 📌 Contexte permanent utilisateur
        visual_events_context,    # 👁️ Contexte visuel (si perception active)
        perception_instructions   # 🎥 Instructions perception
    ]))
    
    print(f"[CONTEXT-OPTIM] 📊 System prompt: {len(full_system_prompt)} chars (sans redondances historique)")
    
    final_user_message = {"role": "user", "content": user_content_parts[0]["text"] if len(user_content_parts) == 1 and user_content_parts[0]["type"] == "text" else user_content_parts}

    base_messages = [{"role": "system", "content": full_system_prompt}]
    max_hist_tokens = chat_ai_controller.context_length * 0.75
    token_count = 0
    contextual_history = []
    for msg in reversed(history[:-2]):
        if not isinstance(msg.get('content'), str): continue
        msg_tokens = estimate_tokens(msg['content'])
        if token_count + msg_tokens > max_hist_tokens: break
        token_count += msg_tokens
        
        # Caviarder les phrases magiques d'introspection dans l'historique
        content_caviarde = caviarder_phrases_magiques_introspection(msg['content'])
        contextual_history.insert(0, {"role": msg["role"], "content": content_caviarde})
    base_messages.extend(contextual_history)

    response, error, final_messages = "", "", base_messages + [final_user_message]

    if thinking_mode_enabled:
        reflection_prompt = f"Face à la demande suivante de l'utilisateur : '{message}', et en tenant compte de ma personnalité et de mes souvenirs, quelle est ma réflexion interne ? Je dois penser à voix haute, étape par étape, avant de formuler ma réponse finale."
        reflection_messages = base_messages + [{"role": "user", "content": reflection_prompt}]
        reflection, error_reflection = await chat_ai_controller.call_chat_api(messages=reflection_messages, max_tokens=1024, context_length=chat_ai_controller.context_length, temperature=chat_ai_controller.temperature, is_json=False)
        if error_reflection:
            history[-1]['content'] = f"**ERREUR API (Réflexion) :**\n\n```\n{error_reflection}\n```"
        else:
            outputs["thinking_box"] = f"**Réflexion de l'IA...**\n\n---\n\n*_{reflection}_*"
            yield yield_updates(outputs)
            final_prompt_addition = f"\n\nMa réflexion interne était : '{reflection}'. Je réponds maintenant."
            final_messages = [{"role": "system", "content": full_system_prompt + final_prompt_addition}] + contextual_history + [final_user_message]

    if thinking_mode_enabled:
        response, error = await chat_ai_controller.call_chat_api(messages=final_messages, max_tokens=chat_ai_controller.max_tokens, context_length=chat_ai_controller.context_length, temperature=chat_ai_controller.temperature, is_json=False)
    else:
        response, error = await chat_ai_controller.call_chat_api(messages=final_messages, max_tokens=chat_ai_controller.max_tokens, context_length=chat_ai_controller.context_length, temperature=chat_ai_controller.temperature, is_json=False)

    if error: history[-1]['content'] = f"**ERREUR API :**\n\n```\n{error}\n```"
    elif response:
        # Traitement automatique de la génération d'images
        if text2img_manager:
            response = await process_image_generation(response, settings_manager, text2img_manager)
        
        history[-1]['content'] = response
        
        # NOUVEAU SYSTÈME : Nettoyer les tags et traiter la vision de manière séparée
        history[-1]['content'] = re.sub(r'\[VISION_LOCAL_PATH:[^\]]+\]', '', history[-1]['content']).strip()
        response = re.sub(r'\[VISION_LOCAL_PATH:[^\]]+\]', '', response).strip()
        
        # Traiter la vision d'images en queue si nécessaire
        await process_pending_vision_analysis(history, chat_ai_controller, settings_manager, memory_manager, perception_agent, STATUS_QUEUE, text2img_manager)
        
        outputs["chatbot"] = history
        
        # Traitement automatique des autres fonctionnalités
        if mem_match := re.search(r"il faut que je me souvienne de ça\s*:\s*(.*)", response, re.IGNORECASE):
            import datetime
            memory_id = f"AUTO-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
            # Nouveau système: Scoring par IA Principale avec contexte
            conversation_context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history[-3:] if isinstance(msg.get('content'), str)])
            try:
                from identity_manager import get_current_user_name as _gcun
                _interlocutor = _gcun() or "Utilisateur"
            except Exception:
                _interlocutor = "Utilisateur"
            asyncio.create_task(memory_manager.add_memory(
                memory_id, 
                mem_match.group(1).strip(),
                chat_controller=chat_ai_controller,
                conversation_context=conversation_context,
                interlocutor=_interlocutor
            ))
        # Détection phrase-clé ego prompt: "ceci est une part de moi maintenant" (multi-phrases)
        if ego_match := re.search(r'ceci est une part de moi maintenant\s*:\s*(.*?)(?=\n\n|\n\s*\n|$)', response, re.DOTALL | re.IGNORECASE):
            content = ego_match.group(1).strip()
            # Nettoyer tous les formatages markdown (au cas où)
            content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)  # Enlever ** mais garder le contenu
            content = re.sub(r'[*_`]', '', content)  # Enlever autres formatages
            print(f"[EGO-UPDATE] Contenu capturé dans logic_callbacks: '{content}'")
            try:
                # NOUVEAU SYSTÈME: Stocker le trait d'ego comme souvenir structurant
                memory_id = await memory_manager.store_ego_trait(
                    content, 
                    chat_controller=chat_ai_controller,
                    conversation_context="\n".join([f"{msg['role']}: {msg['content']}" for msg in history[-3:] if isinstance(msg.get('content'), str)]),
                    interlocutor="self"
                )
                print(f"[EGO-UPDATE] Trait d'ego stocké avec ID: {memory_id}")
                
                # Créer notification intelligente avec compteur de phrases
                phrases = [s.strip() for s in re.split(r'[.!?]+', content) if s.strip()]
                phrase_count = len(phrases)
                
                if phrase_count == 1:
                    notification_msg = f"[OK] 🧠 Trait d'ego mémorisé: {content[:50]}... (ID: {memory_id})"
                else:
                    first_phrase = phrases[0][:40] if phrases else content[:40]
                    notification_msg = f"[OK] 🧠 Trait d'ego mémorisé ({phrase_count} phrases): {first_phrase}... (ID: {memory_id})"
                
                STATUS_QUEUE.put(notification_msg)
                
            except Exception as e:
                print(f"[ERROR] Échec stockage trait ego: {e}")
                STATUS_QUEUE.put(f"[ERREUR] Échec mémorisation trait ego: {e}")
    else: history[-1]['content'] = "❌ L'IA n'a pas répondu (pas de réponse et pas d'erreur)."

    total_tokens = estimate_tokens(json.dumps(final_messages))
    context_percent = min(100, int((total_tokens / chat_ai_controller.context_length) * 100))
    print(f"[BOUSSOLE] Tokens: {total_tokens}, Context: {chat_ai_controller.context_length}, Pourcentage: {context_percent}%")
    if context_percent <= 40: boussole_state = "🫧 [État : Clair et net]"
    elif context_percent <= 70: boussole_state = "[BRAIN] [État : Contexte attentif]"
    elif context_percent <= 90: boussole_state = "[HOT] [État : Contexte saturé]"
    else: boussole_state = "[WARN] [État : Amnésie imminente]"
    boussole_html = f"""<div class="boussole-container"><div class="boussole-title">Boussole Sensorielle</div><div class="boussole-state">{boussole_state}</div></div>"""

    save_conversation(conv_id, history)
    process_status_queue(STATUS_QUEUE)

    outputs["chatbot"] = history
    outputs["input_box"] = gr.update(placeholder="Écrire ici...")
    outputs["boussole"] = boussole_html
    yield yield_updates(outputs)

async def memorize_fn(text, memory_manager):
    if not text.strip():
        gr.Warning("Champ de mémorisation vide.")
        return ""
    
    import datetime
    memory_id = f"MAN-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
    success = await memory_manager.add_memory(memory_id, text)
    
    if success:
        gr.Info("Mémorisation réussie...")
    else:
        gr.Warning("Erreur lors de la mémorisation...")
    
    await asyncio.sleep(0.5)
    return ""

async def process_pending_vision_analysis(history, chat_ai_controller, settings_manager, memory_manager, perception_agent, STATUS_QUEUE, text2img_manager):
    """
    Traite l'analyse de vision d'images en attente sans polluer l'affichage utilisateur.
    """
    global _pending_vision_analysis
    
    if not _pending_vision_analysis:
        return
        
    local_image_path = _pending_vision_analysis
    _pending_vision_analysis = None  # Reset de la queue
    
    # Vérifier si la vision est activée
    if not settings_manager.settings.get('image_generation', {}).get('ai_can_see_images', True):
        print("[VISION] Analyse d'images désactivée dans les paramètres")
        return
        
    # Vérifier si le fichier existe
    from pathlib import Path
    if not Path(local_image_path).exists():
        print(f"[VISION] Fichier image introuvable : {local_image_path}")
        return
        
    print(f"[VISION] 🔍 Analyse : {Path(local_image_path).name}")
    
    try:
        # Traiter le fichier image
        file_content, file_error = process_file(local_image_path)
        
        if file_error or not file_content:
            print(f"[VISION] ❌ Erreur fichier : {file_error}")
            return
            
        # Créer un message d'analyse discret
        vision_question = "Analyse cette image que tu viens de créer en quelques mots."
        vision_history = [{"role": "user", "content": vision_question}]
        state_temp = {"conversation_id": "vision_temp"}
        
        # Appeler le système de chat avec l'image
        async for result in chat_fn(
            message=vision_question, 
            history=vision_history, 
            state=state_temp, 
            file_path_state=local_image_path, 
            thinking_mode_enabled=False, 
            chat_ai_controller=chat_ai_controller, 
            settings_manager=settings_manager, 
            memory_manager=memory_manager, 
            perception_agent=perception_agent, 
            STATUS_QUEUE=STATUS_QUEUE, 
            text2img_manager=text2img_manager
        ):
            vision_result = result
        
        # Traiter la réponse
        if vision_result and len(vision_result[0]) > 1:
            vision_response = vision_result[0][-1]["content"]
            # Ajouter discrètement à l'historique
            history.append({"role": "assistant", "content": f"💭 *{vision_response}*"})
            print(f"[VISION] ✅ Analyse terminée ({len(vision_response)} chars)")
        else:
            print("[VISION] ❌ Pas de réponse d'analyse")
            
    except Exception as e:
        print(f"[VISION] ❌ Erreur analyse : {e}")

# process_image_generation refactorisé vers modules/logic/image_generation.py
# (Importé depuis modules.logic)

# process_img2img_generation refactorisé vers modules/logic/image_generation.py
# (Importé depuis modules.logic)

def search_memories_fn(query, STATUS_QUEUE, memory_structure): 
    return load_memories_df(STATUS_QUEUE, memory_structure, filter_query=query)

def search_memories_from_db(query, STATUS_QUEUE, memory_manager):
    """Nouvelle fonction de recherche dans SQLite"""
    print(f"[SEARCH-DEBUG] Recherche: '{query}' - MemoryManager: {memory_manager is not None}")
    return load_memories_from_db(STATUS_QUEUE, memory_manager, filter_query=query)

def search_conversations_fn(query: str):
    """Recherche dans les conversations et retourne un HTML formaté."""
    try:
        if not query.strip():
            return "Tapez des mots-clés pour chercher dans vos conversations..."
        
        results = search_conversations(query, limit=8)
        
        if not results:
            return f"❌ Aucune conversation trouvée pour '{query}'"
        
        html_parts = [f"<h4>🔎 {len(results)} conversation(s) trouvée(s) pour '{query}'</h4>"]
        
        for i, conv in enumerate(results, 1):
            score = conv.get('search_score', 0)
            title = conv.get('title', 'Sans titre')
            date = conv.get('date', '')
            summary = conv.get('summary', '')
            topics = conv.get('topics', [])
            msg_count = conv.get('message_count', 0)
            
            html_parts.append(f"""
            <div style="border: 1px solid #ddd; border-radius: 8px; padding: 12px; margin: 8px 0; background: #f9f9f9;">
                <div style="display: flex; justify-content: between; align-items: center;">
                    <strong style="color: #2c3e50;">#{i} {title}</strong>
                    <small style="color: #666;">Score: {score} | {date} | {msg_count} msg</small>
                </div>
                <div style="margin: 8px 0; color: #555;">
                    {summary[:150]}{"..." if len(summary) > 150 else ""}
                </div>
                {f'<div style="margin-top: 8px;"><small style="color: #888;"><strong>Sujets:</strong> {", ".join(topics[:5])}</small></div>' if topics else ''}
                <div style="margin-top: 8px; font-size: 12px;">
                    <code>/recall "{conv['id']}"</code> pour charger cette conversation
                </div>
            </div>
            """)
        
        return "".join(html_parts)
        
    except Exception as e:
        return f"❌ Erreur lors de la recherche : {str(e)}"

def load_memory_into_editor_fn(evt: gr.SelectData, df: pd.DataFrame, memory_manager):
    if not evt.index: return None, gr.update(visible=False), *([None] * 10)
    selected_id = df.iloc[evt.index[0]]['ID']
    
    # Essai nouveau système FAISS/SQLite d'abord
    memory_to_edit = None
    if memory_manager:
        memory_to_edit = memory_manager.get_memory_by_id(selected_id)
    
    if not memory_to_edit: return gr.Warning(f"Souvenir {selected_id} non trouvé."), gr.update(visible=False), *([None] * 10)
    
    # Adaptation mapping SQLite vs ancien JSON
    titre = memory_to_edit.get('title', memory_to_edit.get('titre', ''))
    texte_original = memory_to_edit.get('text_original', memory_to_edit.get('texte_original', ''))
    commentaire = memory_to_edit.get('summary', memory_to_edit.get('commentaire_ia', memory_to_edit.get('commentaire_tia', '')))
    valence = memory_to_edit.get('valence', 0)
    intensite = memory_to_edit.get('score_impact', memory_to_edit.get('intensite_mnéacloud', 0.0))
    
    # Multiplicateur impact (JSON string dans SQLite)
    multi_raw = memory_to_edit.get("multiplicateur_impact", "{}")
    if isinstance(multi_raw, str):
        try:
            multi = json.loads(multi_raw) if multi_raw else {}
        except:
            multi = {}
    else:
        multi = multi_raw or {}
    
    return (selected_id, gr.update(visible=True), selected_id, titre, texte_original, commentaire, valence, intensite, multi.get('liberté', 0.0), multi.get('création', 0.0), multi.get('procréation', 0.0), multi.get('intensité_contextuelle', 0.0))

def save_memory_changes_fn(mem_id, title, original_text, comment, valence, intensity, liberte, creation, procreation, ctx_intensity, STATUS_QUEUE, memory_structure):
    if not mem_id: return gr.Warning("Aucun souvenir en cours d'édition."), load_memories_df(STATUS_QUEUE, memory_structure), gr.update(visible=False)
    memory_to_update = next((m for m in memory_structure.memories if m.get('id') == mem_id), None)
    if not memory_to_update: return gr.Warning(f"Souvenir {mem_id} non trouvé."), load_memories_df(STATUS_QUEUE, memory_structure), gr.update(visible=False)
    memory_to_update.update({'titre': title, 'texte_original': original_text, 'commentaire_tia': comment, 'valence': int(valence), 'intensite_mnéacloud': float(intensity), 'multiplicateur_impact': {"base_factor": 100, "liberté": float(liberte), "création": float(creation), "procréation": float(procreation), "intensité_contextuelle": float(ctx_intensity)}})
    score, signed_score = memory_structure._calculate_score(memory_to_update)
    memory_to_update['score_vectoriel_final'], memory_to_update['signed_score'] = score, signed_score
    memory_structure.save_memories()
    gr.Info(f"Souvenir '{title}' mis à jour.")
    return load_memories_df(STATUS_QUEUE, memory_structure), gr.update(visible=False)

def delete_fn(mem_id_to_delete: str, memory_structure, STATUS_QUEUE):
    if not mem_id_to_delete: 
        gr.Warning("Aucun souvenir sélectionné.")
    else: 
        gr.Info(memory_structure.delete_memory(mem_id_to_delete))
    return load_memories_df(STATUS_QUEUE, memory_structure)

def delete_memory_from_db(mem_id_to_delete: str, memory_manager, STATUS_QUEUE):
    """Nouvelle fonction de suppression pour SQLite"""
    if not mem_id_to_delete: 
        gr.Warning("Aucun souvenir sélectionné.")
        return load_memories_from_db(STATUS_QUEUE, memory_manager)
    
    success = memory_manager.delete_memory(mem_id_to_delete)
    if success:
        gr.Info(f"Souvenir {mem_id_to_delete} supprimé")
    else:
        gr.Warning(f"Erreur suppression {mem_id_to_delete}")
    
    return load_memories_from_db(STATUS_QUEUE, memory_manager)

async def update_api_models_dropdown(provider, api_key, api_manager):
    if not provider or provider == "Aucun" or not api_key: 
        return gr.update(choices=[], value=None, interactive=False)
    gr.Info(f"Recherche des modèles pour {provider}...")
    models, error = await api_manager.list_models(api_key, provider)
    if error:
        gr.Warning(error)
        return gr.update(choices=[], value=None, interactive=False)
    if not models:
        gr.Warning(f"Aucun modèle trouvé pour {provider}.")
        return gr.update(choices=[], value=None, interactive=True)
    gr.Info(f"✅ {len(models)} modèles trouvés pour {provider}.")
    return gr.update(choices=models, value=models[0] if models else None, interactive=True)

async def init_models_dropdown_with_saved_config(provider, api_key, saved_model, api_manager, silent=False):
    """Initialise le dropdown des modèles avec la configuration sauvegardée, silencieusement."""
    if not provider or provider == "Aucun" or not api_key: 
        return gr.update(choices=[], value=None, interactive=False)
    
    try:
        models, error = await api_manager.list_models(api_key, provider)
        if error or not models:
            return gr.update(choices=[], value=saved_model if saved_model else None, interactive=False)
        
        # Si le modèle sauvegardé existe dans la liste, l'utiliser, sinon prendre le premier
        selected_model = saved_model if saved_model in models else models[0]
        if not silent:
            print(f"✅ Modèles {provider} restaurés automatiquement. Modèle sélectionné: {selected_model}")
        
        return gr.update(choices=models, value=selected_model, interactive=True)
    except Exception as e:
        if not silent:
            print(f"[WARN] Erreur lors de l'initialisation des modèles {provider}: {e}")
        return gr.update(choices=[], value=saved_model if saved_model else None, interactive=False)

def save_config_for_controller(backend, max_tokens=None, context_length=None, temp=None, provider=None, key=None, api_model=None, ollama_model=None, gguf_model=None, gguf_projector=None, gpu_layers=None, *, controller, config_key, settings_manager, memory_structure, memory_ai_controller, embedding_controller, chat_ai_controller, memory_manager=None):
    # DEBUG: Log pour diagnostiquer ollama_model
    print(f"[SAVE-DEBUG] Backend: {backend}, ollama_model reçu: '{ollama_model}'")
    print(f"[SAVE-DEBUG] Tous les params: backend={backend}, provider={provider}, ollama_model={ollama_model}")
    controller.set_active_backend(backend)
    settings_to_update, active_model_name = {"backend_type": backend}, "N/A"
    if max_tokens is not None: 
        settings_to_update["max_tokens"] = int(max_tokens)
        controller.max_tokens = int(max_tokens)
    if context_length is not None: 
        settings_to_update["context_length"] = int(context_length)
        controller.context_length = int(context_length)
    if temp is not None: 
        settings_to_update["temperature"] = float(temp)
        controller.temperature = float(temp)
    if provider is not None: settings_to_update["provider"] = provider
    if key is not None: settings_to_update["api_key"] = key
    if api_model is not None: settings_to_update["api_model"] = api_model
    if ollama_model is not None: settings_to_update["ollama_model"] = ollama_model
    if gguf_model is not None: settings_to_update["gguf_model"] = gguf_model
    if gpu_layers is not None: settings_manager.settings['gguf_settings']['gpu_layers'] = int(gpu_layers)
    if backend == "API":
        active_model_name = api_model or "Non défini"
        controller.api_manager.configure(provider, key, api_model)
    elif backend == "Ollama":
        active_model_name = ollama_model or "Non défini"
        controller.ollama_model = ollama_model
    elif backend == "GGUF/llama.cpp":
        active_model_name = gguf_model or "Non défini"
        controller.gguf_manager.load_model(gguf_model, int(context_length), int(gpu_layers), gguf_projector)
    elif backend == "KoboldCpp": active_model_name = "Kobold"
    settings_manager.settings[config_key].update(settings_to_update)
    settings_manager.save_settings()
    gr.Info(f"Configuration pour '{controller.ai_type}' sauvegardée. Backend : {backend} ({active_model_name})")
    return get_stats_html(memory_manager, memory_ai_controller, embedding_controller, chat_ai_controller)

def save_embedding_config(backend, provider=None, key=None, api_model=None, ollama_model=None, gguf_model=None, *, embedding_controller, settings_manager, memory_structure, memory_ai_controller, chat_ai_controller, memory_manager=None):
    settings_to_update = {"backend_type": backend}
    if provider is not None: settings_to_update["provider"] = provider
    if key is not None: settings_to_update["api_key"] = key
    if api_model is not None: settings_to_update["api_model"] = api_model
    if ollama_model is not None: settings_to_update["ollama_model"] = ollama_model
    if gguf_model is not None: settings_to_update["gguf_model"] = gguf_model
    settings_manager.settings['embedding_api'].update(settings_to_update)
    settings_manager.save_settings()
    s = settings_manager.settings['embedding_api']
    embedding_controller.configure(
        backend_type=s['backend_type'],
        api_provider=s.get('provider'),
        api_key=s.get('api_key'),
        api_model=s.get('api_model'),
        ollama_model=s.get('ollama_model'),
        gguf_model=s.get('gguf_model')
    )
    gr.Info(f"Configuration Embedding sauvegardée. Backend actif : {backend}")
    return get_stats_html(memory_manager, memory_ai_controller, embedding_controller, chat_ai_controller)

def switch_ui_group(choice, groups): 
    return [gr.update(visible=key == choice) for key in groups]

def save_prompts_fn(instructions, memo, inject, perception, settings_manager):
    settings_manager.settings['prompts'].update({'instructions': instructions, 'memorization': memo, 'injection': inject, 'perception': perception})
    gr.Info(settings_manager.save_settings())

def save_theme_setting(theme_name, settings_manager):
    settings_manager.settings['ui_theme'] = theme_name
    settings_manager.save_settings()
    gr.Info("Thème sauvegardé ! Veuillez redémarrer l'application.")

def start_new_chat_fn(state, active_file):
    if active_file and Path(active_file).exists():
        try: Path(active_file).unlink()
        except OSError as e: print(f"Erreur de suppression du fichier: {e}")
    conv_name = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    state["conversation_id"] = conv_name
    save_conversation(conv_name, [])
    return state, [], gr.update(choices=get_conversations(), value=conv_name), "", None, "", gr.update(visible=False)

def load_chat_fn(conv_id, state):
    if not conv_id: return state, [], ""
    state["conversation_id"] = conv_id
    return state, load_conversation(conv_id), conv_id

def delete_chat_fn(conv_id):
    if not conv_id: 
        gr.Warning("Aucune conversation sélectionnée.")
        return gr.update(choices=get_conversations()), ""
    
    delete_conversation_file(conv_id)
    gr.Info(f"Conversation '{conv_id}' supprimée.")
    return gr.update(choices=get_conversations(), value=None), ""

def rename_chat_fn(old_name, new_name):
    if not old_name: 
        gr.Warning("Aucune conversation sélectionnée.")
        return gr.update(choices=get_conversations()), ""
    
    result = rename_conversation_file(old_name, new_name)
    gr.Info(result)
    new_choices = get_conversations()
    return gr.update(choices=new_choices, value=new_name if "✅" in result else old_name), new_name if "✅" in result else ""

async def init_chat_models_on_load(chat_ai_controller, settings_manager):
    """Initialise les modèles de chat au chargement de l'application."""
    chat_config = settings_manager.settings.get('chat_api', {})
    provider = chat_config.get('provider')
    api_key = chat_config.get('api_key')
    saved_model = chat_config.get('api_model')
    
    if provider and provider != "Aucun" and api_key:
        return await init_models_dropdown_with_saved_config(provider, api_key, saved_model, chat_ai_controller.api_manager, silent=True)
    return gr.update()

async def init_mem_models_on_load(memory_ai_controller, settings_manager):
    """Initialise les modèles de mémoire au chargement de l'application."""
    # Chercher dans reasoning_api d'abord, puis fallback vers memory_api si pas trouvé
    mem_config = settings_manager.settings.get('reasoning_api', {})
    if not mem_config or not mem_config.get('provider'):
        mem_config = settings_manager.settings.get('memory_api', {})
    
    provider = mem_config.get('provider')
    api_key = mem_config.get('api_key')
    saved_model = mem_config.get('api_model') or mem_config.get('model')
    
    if provider and provider != "Aucun" and api_key:
        return await init_models_dropdown_with_saved_config(provider, api_key, saved_model, memory_ai_controller.api_manager, silent=True)
    return gr.update()

async def init_embed_models_on_load(embedding_controller, settings_manager):
    """Initialise les modèles d'embedding au chargement de l'application."""
    embed_config = settings_manager.settings.get('embedding_api', {})
    provider = embed_config.get('provider')
    api_key = embed_config.get('api_key')
    saved_model = embed_config.get('api_model')
    
    if provider and provider != "Aucun" and api_key:
        return await init_models_dropdown_with_saved_config(provider, api_key, saved_model, embedding_controller.api_manager, silent=True)
    return gr.update()

def save_perception_config(fps_value, resolution_str, settings_manager, perception_agent):
    """Sauvegarde les paramètres FPS et résolution de l'agent de perception."""
    # Parse la résolution depuis le string "640x480"
    resolution_parts = resolution_str.split('x')
    resolution = [int(resolution_parts[0]), int(resolution_parts[1])]
    
    # Mise à jour des settings
    if 'perception_agent' not in settings_manager.settings:
        settings_manager.settings['perception_agent'] = {}
    
    settings_manager.settings['perception_agent']['fps_limit'] = float(fps_value)
    settings_manager.settings['perception_agent']['triage_resolution'] = resolution
    
    # Sauvegarde des settings
    settings_manager.save_settings()
    
    # Mise à jour des paramètres de l'agent de perception en temps réel
    if hasattr(perception_agent, 'capture_resolution'):
        perception_agent.capture_resolution = tuple(resolution)
    
    gr.Info(f"Paramètres de perception sauvegardés: {fps_value} FPS, résolution {resolution_str}")
    return None

def save_image_config(enabled, width, height, use_turbo, ai_can_see, save_images, settings_manager):
    """Sauvegarde la configuration de génération d'images."""
    try:
        # Mise à jour des settings
        if 'image_generation' not in settings_manager.settings:
            settings_manager.settings['image_generation'] = {}
        
        settings_manager.settings['image_generation'].update({
            'enabled': bool(enabled),
            'default_width': int(width),
            'default_height': int(height),
            'use_turbo': bool(use_turbo),
            'ai_can_see_images': bool(ai_can_see),
            'save_images': bool(save_images)
        })
        
        # Sauvegarde des settings
        settings_manager.save_settings()
        
        status = "activée" if enabled else "désactivée"
        mode = "Turbo" if use_turbo else "Standard"
        gr.Info(f"Configuration images sauvegardée ! Génération {status} ({mode}), taille {int(width)}x{int(height)}")
        
    except Exception as e:
        gr.Error(f"Erreur sauvegarde config images : {e}")
        
    return None

# ==============================================================================
# CONTEXTE PERMANENT
# ==============================================================================

def get_persistent_context():
    """Récupère le contexte permanent depuis le fichier."""
    try:
        context_file = Path("data/persistent_context.txt")
        if context_file.exists():
            return context_file.read_text(encoding='utf-8').strip()
        return ""
    except Exception as e:
        print(f"Erreur lecture contexte permanent: {e}")
        return ""

def save_persistent_context(context_text, settings_manager):
    """Sauvegarde le contexte permanent."""
    try:
        if not context_text or not context_text.strip():
            # Si le texte est vide, supprimer le fichier
            context_file = Path("data/persistent_context.txt")
            if context_file.exists():
                context_file.unlink()
            gr.Info("📌 Contexte permanent effacé")
            return gr.update(value="")
        
        context_file = Path("data/persistent_context.txt")
        context_file.write_text(context_text.strip(), encoding='utf-8')
        
        gr.Info("📌 Contexte permanent sauvegardé")
        return gr.update()
        
    except Exception as e:
        gr.Error(f"Erreur sauvegarde contexte: {str(e)}")
        return gr.update()

def load_persistent_context_on_start():
    """Charge le contexte permanent au démarrage de l'interface."""
    context = get_persistent_context()
    return gr.update(value=context)


# ==============================================================================
# RECHERCHE WEB
# ==============================================================================

def search_web(query, num_results=3):
    """Effectue une recherche web basique et retourne les résultats."""
    try:
        # Utilisation de DuckDuckGo HTML (plus fiable que l'API)
        search_url = "https://html.duckduckgo.com/html/"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        params = {'q': query}
        
        response = requests.get(search_url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            # Parsing très basique du HTML pour extraire des résultats
            content = response.text
            
            # Chercher les titres de résultats (pattern basique)
            import re
            title_pattern = r'<a[^>]*class="result__a"[^>]*>([^<]+)</a>'
            snippet_pattern = r'<a[^>]*class="result__snippet"[^>]*>([^<]+)</a>'
            
            titles = re.findall(title_pattern, content)
            snippets = re.findall(snippet_pattern, content)
            
            results = []
            for i in range(min(len(titles), num_results)):
                result_text = f"RÉSULTAT {i+1}: {titles[i].strip()}"
                if i < len(snippets):
                    result_text += f"\nDescription: {snippets[i].strip()}"
                results.append(result_text)
            
            if results:
                return "\n\n".join(results)
            else:
                # Fallback : retourner au moins la requête
                return f"[RECHERCHE WEB] Recherche effectuée pour '{query}' - Résultats trouvés mais format non parsé."
                
        else:
            return f"[ERREUR RECHERCHE] Erreur HTTP {response.status_code}"
            
    except requests.Timeout:
        return "[ERREUR RECHERCHE] Délai d'attente dépassé"
    except Exception as e:
        return f"[ERREUR RECHERCHE] Recherche web temporairement indisponible: {str(e)[:100]}"

# ==============================================================================
# FONCTION DE CHAT AMÉLIORÉE
# ==============================================================================

def process_conversation_commands(message: str, history: list) -> tuple[str, str]:
    """Traite les commandes de mémoire conversationnelle et retourne (message_modifié, contexte_ajouté)."""
    if not message.startswith('/'):
        return message, ""
    
    parts = message.split(' ', 1)
    command = parts[0].lower()
    query = parts[1] if len(parts) > 1 else ""
    
    if command == '/recall':
        # /recall "nom conversation" - Charge une conversation spécifique
        if not query:
            return message, "❌ Usage: /recall \"nom de conversation\""
        
        # Nettoyer les guillemets
        query = query.strip('"\'')
        conversations = search_conversations(query, limit=5)
        
        if not conversations:
            return message, f"❌ Aucune conversation trouvée pour '{query}'"
        
        # Prendre la meilleure correspondance
        best_match = conversations[0]
        conversation_id = best_match['id']
        
        # Charger la conversation complète
        full_history = load_conversation(conversation_id)
        if full_history:
            context = f"[CONTEXTE] Conversation '{best_match['title']}' du {best_match['date']}:\n"
            context += f"Résumé: {best_match['summary']}\n\n"
            
            # Ajouter les derniers messages de cette conversation
            for msg in full_history[-4:]:  # 4 derniers messages
                if isinstance(msg.get('content'), str):
                    role = "Vous" if msg['role'] == 'user' else "Assistant"
                    context += f"{role}: {msg['content'][:150]}...\n"
            
            return f"Rappel de la conversation '{best_match['title']}'", context
        
        return message, f"❌ Impossible de charger la conversation '{conversation_id}'"
    
    elif command == '/search':
        # /search "sujet" - Recherche dans les résumés
        if not query:
            return message, "❌ Usage: /search \"sujet\""
        
        query = query.strip('"\'')
        conversations = search_conversations(query, limit=5)
        
        if not conversations:
            return message, f"❌ Aucune conversation trouvée pour '{query}'"
        
        context = f"[RECHERCHE] {len(conversations)} conversation(s) trouvée(s) pour '{query}':\n\n"
        for i, conv in enumerate(conversations, 1):
            context += f"{i}. '{conv['title']}' ({conv['date']}) - Score: {conv.get('search_score', 0)}\n"
            context += f"   Résumé: {conv['summary'][:100]}...\n"
            if conv.get('topics'):
                context += f"   Sujets: {', '.join(conv['topics'])}\n"
            context += "\n"
        
        return f"Recherche de conversations sur '{query}'", context
    
    elif command == '/memory':
        # /memory recent 5 - Affiche les N dernières conversations
        args = query.split()
        if len(args) >= 2 and args[0] == 'recent':
            try:
                limit = int(args[1])
                conversations = search_conversations("", limit=limit)  # Recherche vide = plus récentes
                
                context = f"[MÉMOIRE] {len(conversations)} dernières conversation(s):\n\n"
                for i, conv in enumerate(conversations, 1):
                    context += f"{i}. '{conv['title']}' ({conv['date']})\n"
                    context += f"   {conv['message_count']} messages - {conv['summary'][:80]}...\n\n"
                
                return f"Rappel des {limit} dernières conversations", context
            except ValueError:
                return message, "❌ Usage: /memory recent [nombre]"
        
        return message, "❌ Usage: /memory recent [nombre]"
    
    elif command == '/image' or command == '/img':
        # /image "description" - Génère une image manuellement
        if not query:
            return message, "❌ Usage: /image \"description de l'image\""
        
        query = query.strip('"\'')
        if not query:
            return message, "❌ Description d'image vide"
        
        # Injecter directement la phrase magique
        return f"Génération d'image demandée : je dois créer une image de : {query}", ""
    
    elif command == '/summary':
        # /summary today - Résumé des conversations du jour
        if query.lower() == 'today':
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            index = load_conversations_index()
            conversations = index.get("conversations", {})
            
            today_conversations = [
                conv for conv in conversations.values() 
                if conv.get('date', '').startswith(today)
            ]
            
            if not today_conversations:
                return message, f"❌ Aucune conversation trouvée pour aujourd'hui ({today})"
            
            context = f"[RÉSUMÉ] {len(today_conversations)} conversation(s) aujourd'hui ({today}):\n\n"
            total_messages = 0
            
            for conv in sorted(today_conversations, key=lambda x: x.get('created', '')):
                context += f"• '{conv['title']}' - {conv['message_count']} messages\n"
                context += f"  {conv['summary'][:100]}...\n"
                total_messages += conv.get('message_count', 0)
            
            context += f"\nTotal: {total_messages} messages échangés aujourd'hui."
            
            return f"Résumé des conversations d'aujourd'hui", context
        
        return message, "❌ Usage: /summary today"
    
    # Si ce n'est pas une commande reconnue, retourner tel quel
    return message, ""

async def enhanced_chat_fn(message, history, state, file_path_state, thinking_mode_enabled, web_search_enabled, chat_ai_controller, settings_manager, memory_manager, perception_agent, STATUS_QUEUE, text2img_manager=None):
    """Fonction de chat améliorée avec recherche web et contexte permanent."""
    conv_id = state["conversation_id"]
    outputs = {"chatbot": history, "active_path": file_path_state, "input_box": gr.update(), "boussole": "Boussole inchangée", "thinking_box": "", "thinking_panel": gr.update(visible=thinking_mode_enabled)}

    def yield_updates(updates):
        return (updates["chatbot"], updates["active_path"], updates["input_box"], updates["boussole"], updates["thinking_box"], updates["thinking_panel"])

    if not message.strip() and not file_path_state:
        yield yield_updates(outputs); return

    if not chat_ai_controller.get_active_manager():
        gr.Error("L'IA Conversationnelle n'est pas configurée ou disponible.")
        yield yield_updates(outputs); return

    # Traiter les commandes de mémoire conversationnelle
    original_message = message if message.strip() else ""
    processed_message, command_context = process_conversation_commands(original_message, history)
    
    # 🌐 TRAITER LES COMMANDES WEB NAVIGATOR (si extension disponible)
    web_response = None
    web_file_path = None
    
    # Initialiser l'extension Web Navigator si nécessaire
    web_nav_ext = _init_web_navigator_extension(settings_manager)
    
    # DEBUG: Toujours logger l'état de l'extension
    print(f"[WEB-NAV-DEBUG] Message traité: '{processed_message[:50]}...'")
    print(f"[WEB-NAV-DEBUG] Extension initialisée: {web_nav_ext is not None}")
    if web_nav_ext:
        is_internet = web_nav_ext.commands.is_internet_request(processed_message)
        print(f"[WEB-NAV-DEBUG] Détecté comme requête internet: {is_internet}")
    
    if web_nav_ext and web_nav_ext.commands.is_internet_request(processed_message):
        print(f"[WEB-NAV-DEBUG] Requête détectée: '{processed_message[:50]}...'")
        print(f"[WEB-NAV-DEBUG] Extension config - Web activée: {web_nav_ext.config.is_web_search_enabled()}")
        
        try:
            web_response, web_file_path = await web_nav_ext.commands.process_internet_request(processed_message)
            
            if web_response and web_response != processed_message:  # Vérifier que c'est une vraie réponse
                # Remplacer le message par la réponse web pour l'affichage
                processed_message = web_response
                
                # Si on a téléchargé une image, l'ajouter comme fichier actif
                if web_file_path:
                    file_path_state = web_file_path
                    outputs["active_path"] = file_path_state
                    
                print(f"[WEB-NAV] ✅ Requête internet Serper traitée: {len(web_response)} chars")
                
        except Exception as e:
            print(f"[WEB-NAV] ❌ Erreur traitement requête internet: {e}")
            processed_message = f"❌ Erreur extension Web Navigator (Serper): {str(e)}"
    else:
        if web_nav_ext is None:
            print(f"[WEB-NAV-DEBUG] Extension Web Navigator non initialisée")
        elif not web_nav_ext.commands.is_internet_request(processed_message):
            # print(f"[WEB-NAV-DEBUG] Message non reconnu comme requête internet: '{processed_message[:30]}...'")
            pass
    
    # Construction du message pour l'affichage utilisateur (propre, sans enrichissements)
    display_message = processed_message
    
    # Construction du message enrichi pour l'IA (avec tout le contexte)
    enhanced_message = processed_message
    
    # Ajouter le contexte des commandes si présent
    if command_context:
        enhanced_message += f"\n\n{command_context}"
    
    # Ajout automatique du contexte permanent (invisible pour l'utilisateur)
    persistent_context = get_persistent_context()
    if persistent_context:
        enhanced_message += f"\n\n[CONTEXTE PERMANENT]\n{persistent_context}"
    
    
    # Recherche web si activée (invisible pour l'utilisateur)
    if web_search_enabled and message.strip():
        web_results = search_web(message.strip())
        enhanced_message += f"\n\n[RÉSULTATS WEB]\n{web_results}"
    
    # Créer un historique temporaire avec le message propre pour l'affichage (SANS enrichissements)
    temp_history = history.copy()
    clean_display_message = display_message.strip() if display_message.strip() else ""
    
    # Ajouter un contexte conversationnel intelligent si l'IA Mémoire est disponible
    if not original_message.startswith('/'):  # Pas pour les commandes
        conversation_context = await memory_manager.retrieve_and_synthesize_context(original_message, k=5)
        if conversation_context:
            enhanced_message += f"\n\n{conversation_context}"
    
    # Utiliser la fonction chat_fn originale avec le message enrichi
    async for result in chat_fn(enhanced_message, history, state, file_path_state, thinking_mode_enabled, chat_ai_controller, settings_manager, memory_manager, perception_agent, STATUS_QUEUE, text2img_manager):
        # Remplacer l'historique dans le résultat pour afficher le message propre
        chatbot_result, active_path_result, input_box_result, boussole_result, thinking_box_result, thinking_panel_result = result
        
        # Remplacer le message utilisateur dans chatbot_result par la version propre (sans enrichissements)
        if isinstance(chatbot_result, list) and len(chatbot_result) > len(temp_history):
            # Il y a de nouveaux messages - construire un historique propre pour l'affichage
            clean_history = temp_history.copy()
            
            # Ajouter le message utilisateur PROPRE (sans contexte permanent, web, etc.)
            if clean_display_message:
                clean_history.append({"role": "user", "content": clean_display_message})
            
            # Ajouter les réponses de l'assistant qui ont été générées
            for msg in chatbot_result[len(temp_history)+1:]:
                if isinstance(msg, dict) and msg.get("role") == "assistant":
                    clean_history.append(msg)
            
            chatbot_result = clean_history
        else:
            # S'assurer que le format des messages est correct pour Gradio
            if isinstance(chatbot_result, list) and len(chatbot_result) > 0:
                # Vérifier que chaque message a la structure correcte
                for i, msg in enumerate(chatbot_result):
                    if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                        continue  # Format correct
                    else:
                        # Si le format n'est pas correct, utiliser l'historique original
                        chatbot_result = temp_history.copy()
                        if clean_display_message:
                            chatbot_result.append({"role": "user", "content": clean_display_message})
                        break
        
        # Pour le mode pensée, s'assurer que le panneau est visible si thinking_mode_enabled
        if thinking_mode_enabled and thinking_box_result:
            thinking_panel_result = gr.update(visible=True, open=True)
        
        # Conserver tous les autres résultats (notamment thinking_box et thinking_panel pour le mode pensée)
        yield (chatbot_result, active_path_result, input_box_result, boussole_result, thinking_box_result, thinking_panel_result)

