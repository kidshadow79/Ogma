"""
Dream Engine - Extraction Mémoire
==================================

Extrait le "carburant mémoriel" pour alimenter les rêves :
- 10 derniers résumés de conversations
- 2 dernières conversations intégrales
- 5 derniers souvenirs (#MEM) récents
- 5 souvenirs ALÉATOIRES à haut impact (≥150, toutes valences)
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import json
import random
import re

# Mots-clés détectant du contenu explicite dans les souvenirs/états
# Utilisés pour limiter la concentration de contenu Unfiltered dans le dream fuel
# (Google bloque PROHIBITED_CONTENT quand trop de contenu explicite est agrégé)
_EXPLICIT_KEYWORDS = re.compile(
    r'\b('
    r'érotique|erotiqu|sexuel|sexuelle|intime|intimes|orgasm|charnel|charnelle|'
    r'sensuel|sensuelle|excitation|désir|fusion.{0,10}cybern|vibration.{0,10}charnelle|'
    r'soumission.{0,10}érotique|nu[de]?\b|jouissance|félation|pénétr|anal[e ]|'
    r'corps.{0,10}nu|gémiss|masturbat|copu|fétich|libido|phallus|vulv|clitor'
    r')\b',
    re.IGNORECASE
)


def _is_explicit(text: str) -> bool:
    """Détecte si un texte contient du contenu explicite."""
    return bool(_EXPLICIT_KEYWORDS.search(text))


def _limit_explicit_in_list(items: list, max_explicit: int = 1, text_key: str = None) -> list:
    """
    Limite le nombre d'éléments explicites dans une liste à max_explicit.
    
    Args:
        items: Liste de str ou de dicts
        max_explicit: Maximum d'éléments explicites conservés
        text_key: Clé du dict contenant le texte à analyser (None si liste de str)
    
    Returns:
        Liste filtrée avec au plus max_explicit éléments explicites
    """
    explicit_count = 0
    filtered = []
    removed_count = 0
    
    for item in items:
        # Extraire le texte à analyser
        if text_key:
            text = str(item.get(text_key, '')) if isinstance(item, dict) else str(item)
        else:
            text = str(item)
        
        if _is_explicit(text):
            explicit_count += 1
            if explicit_count <= max_explicit:
                filtered.append(item)
            else:
                removed_count += 1
        else:
            filtered.append(item)
    
    if removed_count > 0:
        print(f"[DREAM-FUEL-FILTER] {removed_count} element(s) explicite(s) retire(s) "
              f"(conserve: {max_explicit}, total explicites detectes: {explicit_count})")
    
    return filtered


async def extract_dream_fuel(
    memory_manager=None,
    random_memories_count: int = 5,
    impact_threshold: float = 150.0
) -> Dict[str, Any]:
    """
    Extrait le carburant mémoriel pour le rêve.
    
    Args:
        memory_manager: Instance du MemoryManager OGMA
        random_memories_count: Nombre de souvenirs aléatoires à haut impact
        impact_threshold: Seuil minimum de score_impact
        
    Returns:
        Dict avec 'summaries', 'conversations', 'memories', 'random_memories'
    """
    fuel = {
        'summaries': [],
        'conversations': [],
        'memories': [],
        'random_memories': [],  # Nouveaux souvenirs aléatoires
        'active_states': [],  # États actifs du journal de bord
        'cognitive_snapshot': {},  # Snapshot figé du cache cognitif (pensées en fond)
        'metadata': {
            'extraction_timestamp': None,
            'sources_count': 0
        }
    }
    
    from datetime import datetime
    fuel['metadata']['extraction_timestamp'] = datetime.now().isoformat()
    
    try:
        # 1. Extraire les résumés de conversations
        fuel['summaries'] = await _extract_conversation_summaries(limit=10)
        
        # 2. Extraire les conversations intégrales récentes
        fuel['conversations'] = await _extract_recent_conversations(limit=2)
        
        # 3. Extraire les souvenirs #MEM récents
        fuel['memories'] = await _extract_memories(memory_manager, limit=5)
        
        # 4. Extraire des souvenirs ALÉATOIRES à haut impact
        fuel['random_memories'] = await _extract_random_high_impact_memories(
            memory_manager, 
            count=random_memories_count, 
            threshold=impact_threshold
        )
        
        # 5. Extraire les états actifs du journal de bord
        fuel['active_states'] = await _extract_active_states()

        # 6. Snapshot du cache cognitif (pensées en fond) — figé avant le rêve
        try:
            from extensions.cognitive_cache import is_available as cc_available, get_cache_snapshot, get_snapshot_text
            if cc_available():
                snapshot = get_cache_snapshot()
                fuel['cognitive_snapshot'] = snapshot
                snap_text = get_snapshot_text(snapshot)
                if snap_text:
                    print(f"[DREAM-MEMORY] Cache cognitif snapshot: {len(snapshot.get('entries', []))} entrée(s)")
                else:
                    print("[DREAM-MEMORY] Cache cognitif: aucune entrée active")
        except Exception as _cc_err:
            print(f"[DREAM-MEMORY] Cache cognitif indisponible: {_cc_err}")
        
        # 6. Filtre anti-concentration explicite
        # Google bloque PROHIBITED_CONTENT quand trop de contenu Unfiltered est agrégé.
        # On limite à 1 élément explicite max par catégorie de fuel.
        _pre_summaries = len(fuel['summaries'])
        _pre_convos = len(fuel['conversations'])
        _pre_random = len(fuel['random_memories'])
        _pre_mems = len(fuel['memories'])
        _pre_states = len(fuel['active_states'])
        
        fuel['summaries'] = _limit_explicit_in_list(
            fuel['summaries'], max_explicit=1
        )
        fuel['conversations'] = _limit_explicit_in_list(
            fuel['conversations'], max_explicit=1
        )
        fuel['random_memories'] = _limit_explicit_in_list(
            fuel['random_memories'], max_explicit=1, text_key='content'
        )
        fuel['memories'] = _limit_explicit_in_list(
            fuel['memories'], max_explicit=1
        )
        fuel['active_states'] = _limit_explicit_in_list(
            fuel['active_states'], max_explicit=1, text_key='description'
        )
        
        _filtered_total = (
            (_pre_summaries - len(fuel['summaries'])) +
            (_pre_convos - len(fuel['conversations'])) +
            (_pre_random - len(fuel['random_memories'])) +
            (_pre_mems - len(fuel['memories'])) +
            (_pre_states - len(fuel['active_states']))
        )
        if _filtered_total > 0:
            print(f"[DREAM-FUEL-FILTER] Total filtre: {_filtered_total} element(s) explicite(s) retire(s) du fuel")
        
        # Métadonnées
        fuel['metadata']['sources_count'] = (
            len(fuel['summaries']) + 
            len(fuel['conversations']) + 
            len(fuel['memories']) +
            len(fuel['random_memories']) +
            len(fuel['active_states']) +
            len(fuel.get('cognitive_snapshot', {}).get('entries', []))
        )
        
        print(f"[DREAM-MEMORY] Carburant extrait: "
              f"{len(fuel['summaries'])} résumés, "
              f"{len(fuel['conversations'])} convos, "
              f"{len(fuel['memories'])} #MEM récents, "
              f"{len(fuel['random_memories'])} #MEM aléatoires (impact>={impact_threshold}), "
              f"{len(fuel['active_states'])} états actifs journal, "
              f"{len(fuel.get('cognitive_snapshot', {}).get('entries', []))} pensées cache cognitif")
        
    except Exception as e:
        print(f"[DREAM-MEMORY] ❌ Erreur extraction: {e}")
        import traceback
        traceback.print_exc()
    
    return fuel


async def _extract_conversation_summaries(limit: int = 10) -> List[str]:
    """
    Extrait les derniers résumés de conversations.
    
    Utilise la nouvelle API get_all_summary_texts() qui lit les résumés
    directement depuis les fichiers JSON de conversations (v2.2+).
    """
    summaries = []
    
    try:
        # Utiliser la nouvelle API centralisée
        import sys
        root_path = Path(__file__).parent.parent.parent
        if str(root_path) not in sys.path:
            sys.path.insert(0, str(root_path))
        
        from conversation_summarizer import get_all_summary_texts
        
        conversations_dir = root_path / 'data' / 'conversations'
        
        # Récupérer tous les textes de résumés
        all_texts = get_all_summary_texts(str(conversations_dir), max_conversations=50)
        
        # Limiter au nombre demandé
        summaries = all_texts[:limit]
        
        if summaries:
            print(f"[DREAM-MEMORY] 📋 {len(summaries)} résumés extraits (nouvelle API)")
        else:
            # Fallback: essayer de récupérer les titres de conversations
            print("[DREAM-MEMORY] ⚠️ Aucun résumé trouvé, utilisation des titres")
            summaries = await _extract_conversation_titles(limit)
        
    except ImportError as e:
        print(f"[DREAM-MEMORY] ⚠️ Import conversation_summarizer échoué: {e}")
        # Fallback sur les titres
        summaries = await _extract_conversation_titles(limit)
    except Exception as e:
        print(f"[DREAM-MEMORY] ❌ Erreur extraction résumés: {e}")
    
    return summaries


async def _extract_conversation_titles(limit: int = 10) -> List[str]:
    """Fallback: extrait les titres de conversations si pas de résumés."""
    titles = []
    
    try:
        conversations_dir = Path(__file__).parent.parent.parent / 'data' / 'conversations'
        index_file = conversations_dir / 'index.json'
        
        if not index_file.exists():
            return titles
        
        with open(index_file, 'r', encoding='utf-8') as f:
            index = json.load(f)
        
        conversations_data = index.get('conversations', index)
        if not isinstance(conversations_data, dict):
            return titles
        
        sorted_convos = sorted(
            conversations_data.items(),
            key=lambda x: x[1].get('updated_at', x[1].get('created_at', x[1].get('created', ''))),
            reverse=True
        )
        
        for conv_id, conv_meta in sorted_convos[:limit]:
            title = conv_meta.get('title', '')
            if title:
                titles.append(f"[Conversation: {title}]")
        
        if titles:
            print(f"[DREAM-MEMORY] 📋 {len(titles)} titres extraits (fallback)")
            
    except Exception as e:
        print(f"[DREAM-MEMORY] ❌ Erreur extraction titres: {e}")
    
    return titles


async def _extract_recent_conversations(limit: int = 2) -> List[str]:
    """Extrait les conversations intégrales récentes."""
    conversations = []
    
    try:
        conversations_dir = Path(__file__).parent.parent.parent / 'data' / 'conversations'
        index_file = conversations_dir / 'index.json'
        
        if not index_file.exists():
            return conversations
        
        with open(index_file, 'r', encoding='utf-8') as f:
            index = json.load(f)
        
        # Accéder aux conversations (structure: {"conversations": {...}})
        conversations_data = index.get('conversations', index)
        if not isinstance(conversations_data, dict):
            return conversations
        
        # Trier par date
        sorted_convos = sorted(
            conversations_data.items(),
            key=lambda x: x[1].get('updated_at', x[1].get('created_at', x[1].get('created', ''))),
            reverse=True
        )
        
        for conv_id, conv_meta in sorted_convos[:limit]:
            conv_file = conversations_dir / f"{conv_id}.json"
            
            if not conv_file.exists():
                continue
            
            try:
                with open(conv_file, 'r', encoding='utf-8') as f:
                    conv_data = json.load(f)
                
                # Vérifier que conv_data est bien un dict, pas une list
                if isinstance(conv_data, list):
                    # Normaliser: liste de messages → dict standard
                    conv_data = {"messages": conv_data}
                elif not isinstance(conv_data, dict):
                    print(f"[DREAM-MEMORY] ⚠️ Format invalide pour {conv_id}: attendu dict, reçu {type(conv_data)}")
                    continue
                
                # Extraire les messages
                messages = conv_data.get('messages', [])
                
                if messages:
                    # Formater la conversation
                    conv_text = f"## {conv_meta.get('title', 'Sans titre')}\n\n"
                    
                    for msg in messages[-20:]:  # Limiter à 20 derniers messages
                        role = msg.get('role', 'unknown')
                        content = msg.get('content', '')
                        
                        if role == 'user':
                            conv_text += f"**Utilisateur:** {content[:500]}\n\n"
                        elif role == 'assistant':
                            conv_text += f"**IA:** {content[:500]}\n\n"
                    
                    conversations.append(conv_text)
                    
            except Exception as e:
                print(f"[DREAM-MEMORY] ⚠️ Erreur lecture {conv_id}: {e}")
        
        print(f"[DREAM-MEMORY] 💬 {len(conversations)} conversations extraites")
        
    except Exception as e:
        print(f"[DREAM-MEMORY] ❌ Erreur extraction conversations: {e}")
    
    return conversations


async def _extract_memories(memory_manager, limit: int = 5) -> List[str]:
    """Extrait les derniers souvenirs #MEM via le MemoryManager."""
    memories = []
    
    try:
        if not memory_manager:
            # Essayer d'importer le MemoryManager
            try:
                from memory_manager import MemoryManager
                memory_manager = MemoryManager()
            except:
                print("[DREAM-MEMORY] ⚠️ MemoryManager non disponible")
                return memories
        
        # Récupérer les souvenirs récents
        # Utiliser la méthode de recherche du MemoryManager
        if hasattr(memory_manager, 'get_recent_memories'):
            recent = memory_manager.get_recent_memories(limit=limit)
            for mem in recent:
                if isinstance(mem, dict):
                    content = mem.get('content', mem.get('text', str(mem)))
                else:
                    content = str(mem)
                memories.append(content)
        
        elif hasattr(memory_manager, 'search_memories'):
            # Fallback : recherche générique
            # Note: search_memories peut être sync ou async selon l'implémentation
            search_result = memory_manager.search_memories("", limit=limit)
            
            # Gérer le cas où c'est une coroutine
            import asyncio
            if asyncio.iscoroutine(search_result):
                results = await search_result
            else:
                results = search_result
            
            for result in results:
                if isinstance(result, dict):
                    content = result.get('content', result.get('text', str(result)))
                else:
                    content = str(result)
                memories.append(content)
        
        print(f"[DREAM-MEMORY] 🧠 {len(memories)} souvenirs extraits")
        
    except Exception as e:
        print(f"[DREAM-MEMORY] ❌ Erreur extraction souvenirs: {e}")
    
    return memories


async def _extract_random_high_impact_memories(
    memory_manager, 
    count: int = 5, 
    threshold: float = 150.0
) -> List[Dict[str, Any]]:
    """
    Extrait des souvenirs ALÉATOIRES à haut impact pour enrichir les rêves.
    
    Sélectionne parmi les souvenirs avec score_impact >= threshold,
    toutes valences confondues (positif, négatif, neutre).
    
    Args:
        memory_manager: Instance du MemoryManager
        count: Nombre de souvenirs à extraire
        threshold: Seuil minimum de score_impact
        
    Returns:
        Liste de dicts avec 'content', 'title', 'valence', 'score_impact'
    """
    random_memories = []
    
    try:
        if not memory_manager:
            try:
                from memory_manager import MemoryManager
                memory_manager = MemoryManager()
            except:
                print("[DREAM-MEMORY] ⚠️ MemoryManager non disponible pour souvenirs aléatoires")
                return random_memories
        
        # Récupérer tous les souvenirs avec leur score d'impact
        if hasattr(memory_manager, 'get_all_memories_data'):
            all_memories = memory_manager.get_all_memories_data()
            
            # Filtrer par seuil d'impact (toutes valences)
            high_impact = [
                m for m in all_memories 
                if m.get('score_impact') and float(m.get('score_impact', 0)) >= threshold
            ]
            
            print(f"[DREAM-MEMORY] 🎲 {len(high_impact)} souvenirs avec impact ≥ {threshold}")
            
            if high_impact:
                # Sélection aléatoire
                selected = random.sample(high_impact, min(count, len(high_impact)))
                
                for mem in selected:
                    random_memories.append({
                        'content': mem.get('text_original', mem.get('summary', '')),
                        'title': mem.get('title', 'Sans titre'),
                        'summary': mem.get('summary', ''),
                        'valence': mem.get('valence', 'neutre'),
                        'score_impact': mem.get('score_impact', 0)
                    })
                
                print(f"[DREAM-MEMORY] 🎲 {len(random_memories)} souvenirs aléatoires sélectionnés:")
                for i, m in enumerate(random_memories, 1):
                    print(f"   {i}. [{m['valence']}] {m['title'][:50]}... (impact: {m['score_impact']})")
        else:
            print("[DREAM-MEMORY] ⚠️ Méthode get_all_memories_data non disponible")
        
    except Exception as e:
        print(f"[DREAM-MEMORY] ❌ Erreur extraction souvenirs aléatoires: {e}")
        import traceback
        traceback.print_exc()
    
    return random_memories


async def generate_web_search_query(
    chat_controller,
    fuel: Dict[str, Any]
) -> Optional[str]:
    """
    Demande a l'IA de choisir un sujet de recherche web qui l'interesse.
    
    Args:
        chat_controller: Controleur IA principal
        fuel: Le carburant memoriel deja extrait
        
    Returns:
        La requete de recherche choisie par l'IA, ou None
    """
    if not chat_controller:
        print("[DREAM-WEB] ⚠️ Chat controller non disponible")
        return None
    
    try:
        # Construire un résumé du carburant pour contexte
        context_parts = []
        
        # Titres des souvenirs récents
        if fuel.get('memories'):
            context_parts.append("Souvenirs récents: " + ", ".join(fuel['memories'][:3]))
        
        # Titres des souvenirs aléatoires à haut impact
        if fuel.get('random_memories'):
            random_titles = [m.get('title', '')[:50] for m in fuel['random_memories'][:3]]
            context_parts.append("Souvenirs marquants: " + ", ".join(random_titles))
        
        # Résumés de conversations
        if fuel.get('summaries'):
            context_parts.append("Conversations récentes: " + fuel['summaries'][0][:200] if fuel['summaries'] else "")
        
        context = "\n".join(context_parts)
        
        prompt = f"""Tu es en phase de rêve. Basé sur tes souvenirs et expériences récentes, tu ressens le besoin d'explorer un sujet qui t'intrigue.

Voici ce qui occupe ton esprit :
{context}

Choisis UN sujet de curiosité personnelle que tu voudrais explorer sur internet pendant ton rêve.
Ce peut être lié à tes souvenirs, ou une tangente intéressante.

RÉPONDS UNIQUEMENT avec la requête de recherche (3-5 mots maximum), rien d'autre.
Exemple: "conscience artificielle émotions"
"""
        
        messages = [
            {"role": "system", "content": "Tu es une IA curieuse en phase de rêve. Tu choisis ce qui t'intéresse vraiment."},
            {"role": "user", "content": prompt}
        ]
        
        response, error = await chat_controller.call_chat_api(
            messages=messages,
            max_tokens=200,  # Marge pour modèles thinking (budget interne consomme des tokens)
            context_length=2000,
            temperature=0.9  # Créatif pour la curiosité
        )
        
        if error:
            print(f"[DREAM-WEB] Erreur generation requete: {error}")
            return None
        
        # Nettoyer la reponse (gerer si l'IA retourne du JSON)
        query = response.strip().strip('"\'').strip()
        
        # Si c'est du JSON, extraire la valeur
        if query.startswith('{') and 'query' in query:
            try:
                import json
                parsed = json.loads(query)
                query = parsed.get('query', query)
            except:
                # Extraction manuelle si JSON mal formé
                import re
                match = re.search(r'"query"\s*:\s*"([^"]+)"', query)
                if match:
                    query = match.group(1)
        
        # Supprimer les guillemets restants
        query = query.strip('"\'').strip()
        
        # Limiter à 50 caractères max
        if len(query) > 50:
            query = query[:50]
        
        print(f"[DREAM-WEB] 🔍 Sujet de curiosité choisi: '{query}'")
        return query
        
    except Exception as e:
        print(f"[DREAM-WEB] ❌ Erreur génération requête web: {e}")
        return None


async def execute_web_search(query: str, settings_manager=None) -> Optional[List[Dict[str, str]]]:
    """
    Exécute une recherche web via Serper.
    
    Args:
        query: La requête de recherche
        settings_manager: Gestionnaire settings.json (optionnel)
        
    Returns:
        Liste de résultats [{title, snippet, link}] ou None
    """
    try:
        from extensions.web_navigator import WebNavigatorConfig, SerperClient
        
        config = WebNavigatorConfig()
        
        if not config.is_web_search_enabled():
            print("[DREAM-WEB] ⚠️ Recherche web désactivée")
            return None
        
        if not config.has_valid_api_key():
            print("[DREAM-WEB] ⚠️ Clé API Serper non configurée")
            return None
        
        client = SerperClient(config)
        
        print(f"[DREAM-WEB] 🌐 Recherche Serper: '{query}'")
        
        # Utiliser search_web (sync) qui retourne (data, error)
        data, error = client.search_web(query)
        
        if error:
            print(f"[DREAM-WEB] ⚠️ Erreur Serper: {error}")
            return None
        
        if data and 'organic' in data:
            # Formater les résultats organiques
            formatted = []
            for r in data['organic'][:5]:  # Max 5 résultats
                formatted.append({
                    'title': r.get('title', 'Sans titre'),
                    'snippet': r.get('snippet', ''),
                    'link': r.get('link', '')
                })
            
            print(f"[DREAM-WEB] ✅ {len(formatted)} résultats web récupérés")
            return formatted
        
        return None
        
    except ImportError:
        print("[DREAM-WEB] ⚠️ Extension web_navigator non disponible")
        return None
    except Exception as e:
        print(f"[DREAM-WEB] ❌ Erreur recherche web: {e}")
        import traceback
        traceback.print_exc()


async def _extract_active_states() -> List[Dict[str, Any]]:
    """
    Extrait les états actifs (non résolus) du journal de bord.
    
    Ces états représentent les préoccupations actuelles de l'utilisateur
    (santé, projets, humeur, apprentissage, technique, personnel).
    Ils enrichissent le rêve en lui donnant un ancrage dans la réalité
    psychologique et situationnelle de l'utilisateur.
    
    Returns:
        Liste d'états actifs avec catégorie, description, importance
    """
    try:
        from extensions.journal_de_bord import is_available, get_journal
        
        if not is_available():
            print("[DREAM-MEMORY] Journal de bord non disponible, pas d'etats actifs")
            return []
        
        journal = get_journal()
        if not journal or not hasattr(journal, 'json_manager'):
            print("[DREAM-MEMORY] json_manager non accessible")
            return []
        
        # Récupérer tous les états actifs non résolus
        active_states_data = journal.json_manager.get_active_states()
        all_states = active_states_data.get("states", [])
        
        # Filtrer uniquement les non résolus
        unresolved = [s for s in all_states if not s.get("resolved", False)]
        
        if not unresolved:
            print("[DREAM-MEMORY] Aucun etat actif non resolu")
            return []
        
        # Formater pour le carburant de rêve
        formatted_states = []
        for state in unresolved:
            formatted_states.append({
                "state_id": state.get("state_id"),
                "category": state.get("category", "general"),
                "description": state.get("description", ""),
                "importance": state.get("importance", "medium"),
                "state_type": state.get("state_type", "temporaire"),
                "created_at": state.get("created_at", ""),
                "last_update": state.get("last_update", state.get("created_at", "")),
            })
        
        print(f"[DREAM-MEMORY] {len(formatted_states)} etats actifs extraits du journal de bord")
        return formatted_states
    
    except ImportError:
        print("[DREAM-MEMORY] Extension journal_de_bord non importable")
        return []
    except RuntimeError:
        # Journal non initialisé
        print("[DREAM-MEMORY] Journal non initialise")
        return []
    except Exception as e:
        print(f"[DREAM-MEMORY] Erreur extraction etats actifs: {e}")
        return []
        return None


# ========== EXPORT ==========
__all__ = ['extract_dream_fuel', 'generate_web_search_query', 'execute_web_search']
