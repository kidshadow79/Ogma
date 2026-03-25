"""
OGMA - Journal de Bord v2.0
Module d'auto-résolution des états actifs inactifs

Fonctionnalités :
- Détection états inactifs (non mis à jour depuis X jours)
- Validation LLM avant résolution automatique
- Détection et fusion de doublons sémantiques
- Mode dry_run pour preview
- Logs détaillés et statistiques

Pattern : Fonctions utilitaires sans état
"""

import asyncio
import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


# ========================================================================
# TTL PAR CATÉGORIE — Expiration automatique des états éphémères
# ========================================================================

# Durées de vie par catégorie (en heures)
CATEGORY_TTL_HOURS = {
    "humeur": 12,         # Ephemere par nature
    "personnel": 12,      # Contextuel a la session (intime)
    "sante": 168,          # 7 jours
    "santé": 168,          # 7 jours (accent)
    "technique": 168,      # 7 jours
    "projet": 720,         # 30 jours
    "apprentissage": 168,  # 7 jours
    # identite, relation : pas de TTL (jamais auto)
}


def auto_expire_by_category(json_manager) -> Dict[str, Any]:
    """
    Expire automatiquement les etats actifs dont le TTL par categorie est depasse.
    Base sur created_at (age de l'etat), pas sur last_update.
    
    Categories protegees (jamais auto-expirees) : identite, relation
    
    Returns:
        dict: {"expired_count": int, "expired_states": list, "skipped": int}
    """
    result = {"expired_count": 0, "expired_states": [], "skipped": 0}
    
    try:
        active_states_data = json_manager.get_active_states()
        all_states = active_states_data.get("states", [])
        unresolved = [s for s in all_states if not s.get("resolved", False)]
        
        if not unresolved:
            print("[AUTO-EXPIRE] Aucun etat actif a verifier")
            return result
        
        now = datetime.now()
        print(f"[AUTO-EXPIRE] Verification TTL sur {len(unresolved)} etats actifs...")
        
        for state in unresolved:
            category = state.get("category", "").lower()
            ttl_hours = CATEGORY_TTL_HOURS.get(category)
            
            if ttl_hours is None:
                # Categorie protegee (identite, relation, ou inconnue)
                result["skipped"] += 1
                continue
            
            # Calculer l'age depuis created_at
            created_at_str = state.get("created_at", "")
            if not created_at_str:
                result["skipped"] += 1
                continue
            
            try:
                created_date = datetime.fromisoformat(created_at_str)
                if created_date.tzinfo is not None:
                    created_date = created_date.replace(tzinfo=None)
                
                age_hours = (now - created_date).total_seconds() / 3600
                
                if age_hours > ttl_hours:
                    state_id = state.get("state_id")
                    desc = state.get("description", "")[:60]
                    ttl_days = ttl_hours / 24
                    age_days = age_hours / 24
                    
                    success = json_manager.resolve_state(
                        state_id=state_id,
                        resolution_note=f"Auto-expire: TTL {category} depasse ({age_days:.1f}j > {ttl_days:.0f}j)"
                    )
                    
                    if success:
                        result["expired_count"] += 1
                        result["expired_states"].append({
                            "state_id": state_id,
                            "category": category,
                            "description": desc,
                            "age_hours": round(age_hours, 1),
                            "ttl_hours": ttl_hours
                        })
                        print(f"[AUTO-EXPIRE] Expire: [{category}] {desc} (age: {age_days:.1f}j > TTL: {ttl_days:.0f}j)")
            except Exception as e:
                print(f"[AUTO-EXPIRE] WARN Erreur parsing date etat {state.get('state_id')}: {e}")
                result["skipped"] += 1
        
        print(f"[AUTO-EXPIRE] Termine: {result['expired_count']} expires, {result['skipped']} ignores")
        return result
    
    except Exception as e:
        print(f"[AUTO-EXPIRE] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return result


def detect_inactive_states(
    json_manager,
    threshold_days: int = 3,
    exclude_high_importance: bool = False,
    high_importance_threshold_days: int = 7
) -> List[Dict[str, Any]]:
    """
    Détecte les états actifs non mis à jour depuis un certain temps
    
    Args:
        json_manager: Instance JournalJSONManager
        threshold_days: Seuil d'inactivité en jours pour medium/low (défaut: 3j)
        exclude_high_importance: Exclure les états d'importance "high" (défaut: False)
        high_importance_threshold_days: Seuil spécifique pour les high (défaut: 7j)
    
    Returns:
        Liste d'états inactifs avec métadonnées
    """
    try:
        print(f"[AUTO-RESOLVE] Detection etats inactifs >{threshold_days}j (high: >{high_importance_threshold_days}j)")
        
        # Récupérer tous les états actifs
        active_states_data = json_manager.get_active_states()
        all_states = active_states_data.get("states", [])
        
        # Filtrer les non résolus
        unresolved = [s for s in all_states if not s.get("resolved", False)]
        
        cutoff_date = datetime.now() - timedelta(days=threshold_days)
        cutoff_date_high = datetime.now() - timedelta(days=high_importance_threshold_days)
        inactive_states = []
        
        for state in unresolved:
            try:
                # Récupérer dernière mise à jour
                last_update_str = state.get("last_update", state.get("created_at", ""))
                if not last_update_str:
                    continue
                
                last_update = datetime.fromisoformat(last_update_str)
                importance = state.get("importance", "medium")
                
                # Seuil adaptatif selon importance
                if importance == "high":
                    if exclude_high_importance:
                        continue
                    if last_update >= cutoff_date_high:
                        continue
                else:
                    if last_update >= cutoff_date:
                        continue
                
                # Calculer jours d'inactivité
                days_inactive = (datetime.now() - last_update).days
                
                inactive_states.append({
                    "state_id": state.get("state_id"),
                    "category": state.get("category", "general"),
                    "description": state.get("description", ""),
                    "importance": importance,
                    "last_update": last_update_str,
                    "days_inactive": days_inactive,
                    "created_at": state.get("created_at", ""),
                    "update_history": state.get("update_history", [])
                })
            
            except Exception as e:
                print(f"[AUTO-RESOLVE] WARN Erreur analyse etat {state.get('state_id')}: {e}")
                continue
        
        print(f"[AUTO-RESOLVE] Detecte {len(inactive_states)} etats inactifs")
        return sorted(inactive_states, key=lambda x: x["days_inactive"], reverse=True)
    
    except Exception as e:
        print(f"[AUTO-RESOLVE] ERROR detect_inactive_states: {e}")
        import traceback
        traceback.print_exc()
        return []


async def auto_resolve_states(
    json_manager,
    archiviste_controller,
    states_to_resolve: Optional[List[Dict[str, Any]]] = None,
    threshold_days: int = 30,
    dry_run: bool = True,
    require_llm_validation: bool = True
) -> Dict[str, Any]:
    """
    Résout automatiquement les états inactifs après validation optionnelle LLM
    
    Args:
        json_manager: Instance JournalJSONManager
        archiviste_controller: Contrôleur LLM pour validation
        states_to_resolve: Liste états à résoudre (si None, détection auto)
        threshold_days: Seuil inactivité pour détection auto (défaut: 30j)
        dry_run: Mode simulation sans modification (défaut: True)
        require_llm_validation: Valider avec LLM avant résolution (défaut: True)
    
    Returns:
        Statistiques {total, validated, resolved, rejected, failed, errors}
    """
    try:
        print(f"[AUTO-RESOLVE] {'🔍 SIMULATION' if dry_run else '✅ RÉSOLUTION'} "
              f"threshold={threshold_days}j, llm_validation={require_llm_validation}")
        
        # Détection auto si liste non fournie
        if states_to_resolve is None:
            states_to_resolve = detect_inactive_states(
                json_manager=json_manager,
                threshold_days=threshold_days
            )
        
        stats = {
            "total": len(states_to_resolve),
            "validated": 0,
            "resolved": 0,
            "rejected": 0,
            "failed": 0,
            "errors": []
        }
        
        if dry_run:
            print(f"[AUTO-RESOLVE] MODE SIMULATION - {stats['total']} états détectés (aucune modification)")
            return stats
        
        # Traitement des états
        for state in states_to_resolve:
            state_id = state["state_id"]
            description = state["description"]
            days_inactive = state["days_inactive"]
            
            try:
                # Validation LLM optionnelle
                should_resolve = True
                validation_reason = f"Inactif depuis {days_inactive}j"
                
                if require_llm_validation and archiviste_controller:
                    should_resolve, validation_reason = await _validate_resolution_with_llm(
                        state=state,
                        archiviste_controller=archiviste_controller
                    )
                    
                    if should_resolve:
                        stats["validated"] += 1
                    else:
                        stats["rejected"] += 1
                        print(f"[AUTO-RESOLVE] ⛔ État #{state_id} rejeté: {validation_reason}")
                        continue
                
                # Résolution
                if should_resolve:
                    resolution_note = f"Auto-résolu (inactif {days_inactive}j). {validation_reason}"
                    
                    success = json_manager.resolve_state(
                        state_id=state_id,
                        resolution_note=resolution_note
                    )
                    
                    if success:
                        stats["resolved"] += 1
                        print(f"[AUTO-RESOLVE] ✅ État #{state_id} résolu: {description[:50]}...")
                    else:
                        stats["failed"] += 1
                        stats["errors"].append(f"#{state_id}: Échec résolution")
            
            except Exception as e:
                print(f"[AUTO-RESOLVE] ERROR Traitement état #{state_id}: {e}")
                stats["failed"] += 1
                stats["errors"].append(f"#{state_id}: {str(e)}")
        
        print(f"[AUTO-RESOLVE] ✅ Traitement terminé : {stats}")
        return stats
    
    except Exception as e:
        print(f"[AUTO-RESOLVE] ERROR auto_resolve_states: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


async def _validate_resolution_with_llm(
    state: Dict[str, Any],
    archiviste_controller
) -> Tuple[bool, str]:
    """
    Valide via LLM si un état peut légitimement être auto-résolu
    
    Args:
        state: Données état à valider
        archiviste_controller: Contrôleur LLM Archiviste
    
    Returns:
        Tuple (should_resolve: bool, reason: str)
    """
    try:
        state_id = state["state_id"]
        category = state["category"]
        description = state["description"]
        days_inactive = state["days_inactive"]
        importance = state["importance"]
        update_history = state.get("update_history", [])
        
        # Construire prompt validation
        history_summary = "\n".join([
            f"- {h.get('timestamp', '')[:10]}: {h.get('action', '')}"
            for h in update_history[:5]
        ])
        
        validation_prompt = f"""Analyse cet état actif et détermine s'il peut être auto-résolu.

ÉTAT #{state_id}:
- Catégorie: {category}
- Importance: {importance}
- Description: {description}
- Dernière activité: il y a {days_inactive} jours
- Historique récent:
{history_summary if history_summary else "Aucun historique"}

CRITÈRES DE VALIDATION:
- L'état semble-t-il naturellement résolu par le temps ?
- Y a-t-il des indices de résolution implicite ?
- L'inactivité suggère-t-elle un abandon/oubli plutôt qu'un problème persistant ?

RÉPONSE ATTENDUE (format JSON strict):
{{
    "should_resolve": true/false,
    "reason": "Explication concise (max 100 chars)"
}}

IMPORTANT: Réponds UNIQUEMENT avec le JSON, rien d'autre."""
        
        try:
            # Appel LLM (async call_chat_api)
            response, error = await archiviste_controller.call_chat_api(
                messages=[{"role": "user", "content": validation_prompt}],
                temperature=0.2,
                max_tokens=200,
                context_length=4096,
                is_json=False
            )
            
            if error or not response:
                print(f"[AUTO-RESOLVE] WARN Erreur LLM pour #{state_id}: {error}")
                return False, "Validation LLM echouee (erreur API)"
            
            # Parse réponse JSON
            json_match = re.search(r'\{[^}]+\}', response)
            if not json_match:
                print(f"[AUTO-RESOLVE] WARN Réponse LLM non-JSON pour #{state_id}: {response[:100]}")
                return False, "Validation LLM échouée (format)"
            
            validation_data = json.loads(json_match.group())
            should_resolve = validation_data.get("should_resolve", False)
            reason = validation_data.get("reason", "Validation LLM")
            
            print(f"[AUTO-RESOLVE] LLM Validation #{state_id}: {should_resolve} - {reason}")
            return should_resolve, reason
        
        except Exception as e:
            print(f"[AUTO-RESOLVE] ERROR Validation LLM #{state_id}: {e}")
            # En cas d'erreur LLM, ne pas résoudre par sécurité
            return False, f"Erreur validation: {str(e)}"
    
    except Exception as e:
        print(f"[AUTO-RESOLVE] ERROR _validate_resolution_with_llm: {e}")
        return False, f"Erreur critique: {str(e)}"


def get_auto_resolution_stats(json_manager, threshold_days: int = 30) -> Dict[str, Any]:
    """
    Récupère des statistiques sur les états éligibles pour auto-résolution
    
    Args:
        json_manager: Instance JournalJSONManager
        threshold_days: Seuil inactivité (défaut: 30j)
    
    Returns:
        Dict avec statistiques {total_inactive, by_category, by_importance, by_age_range}
    """
    try:
        inactive_states = detect_inactive_states(
            json_manager=json_manager,
            threshold_days=threshold_days,
            exclude_high_importance=False  # Inclure tous pour stats
        )
        
        # Stats par catégorie
        by_category = {}
        by_importance = {}
        by_age_range = {
            "30-60j": 0,
            "60-90j": 0,
            "90-180j": 0,
            "180j+": 0
        }
        
        for state in inactive_states:
            # Catégorie
            cat = state["category"]
            by_category[cat] = by_category.get(cat, 0) + 1
            
            # Importance
            imp = state["importance"]
            by_importance[imp] = by_importance.get(imp, 0) + 1
            
            # Tranche d'âge
            days = state["days_inactive"]
            if days < 60:
                by_age_range["30-60j"] += 1
            elif days < 90:
                by_age_range["60-90j"] += 1
            elif days < 180:
                by_age_range["90-180j"] += 1
            else:
                by_age_range["180j+"] += 1
        
        stats = {
            "total_inactive": len(inactive_states),
            "by_category": by_category,
            "by_importance": by_importance,
            "by_age_range": by_age_range,
            "threshold_days": threshold_days
        }
        
        print(f"[AUTO-RESOLVE] Stats: {stats['total_inactive']} etats inactifs")
        return stats
    
    except Exception as e:
        print(f"[AUTO-RESOLVE] ERROR get_auto_resolution_stats: {e}")
        return {"error": str(e)}


# ============================================================
# DÉTECTION ET FUSION DE DOUBLONS
# ============================================================

async def detect_duplicate_states(
    json_manager,
    archiviste_controller=None,
    similarity_threshold: float = 0.7
) -> Dict[str, Any]:
    """
    Détecte les doublons parmi les états actifs non résolus.
    
    Stratégie en 2 passes:
    1. Pré-filtre rapide par catégorie + mots-clés communs (sans LLM)
    2. Validation LLM pour les candidats détectés
    
    Args:
        json_manager: Instance JournalJSONManager
        archiviste_controller: Contrôleur LLM (optionnel, pour validation fine)
        similarity_threshold: Seuil de similarité mots-clés (0.0-1.0)
    
    Returns:
        Dict avec {duplicates: [{keep_id, remove_ids, reason}], stats}
    """
    try:
        print("[DEDUP-STATES] Detection doublons etats actifs...")
        
        active_states_data = json_manager.get_active_states()
        all_states = active_states_data.get("states", [])
        unresolved = [s for s in all_states if not s.get("resolved", False)]
        
        if len(unresolved) < 2:
            print("[DEDUP-STATES] Moins de 2 etats - pas de doublons possibles")
            return {"duplicates": [], "stats": {"total": 0, "groups": 0}}
        
        # Passe 1: Regrouper par catégorie
        by_category = {}
        for state in unresolved:
            cat = state.get("category", "general")
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(state)
        
        # Passe 2: Dans chaque catégorie, détecter similarité par mots-clés
        duplicate_groups = []
        
        for cat, states in by_category.items():
            if len(states) < 2:
                continue
            
            # Calculer les mots-clés pour chaque état
            state_keywords = []
            for s in states:
                desc = s.get("description", "").lower()
                # Retirer les mots courants
                stopwords = {"de", "du", "des", "le", "la", "les", "et", "en", "un", "une",
                             "pour", "par", "avec", "dans", "sur", "est", "a", "au", "aux",
                             "ce", "cette", "ces", "qui", "que", "dont", "ou", "vers", "d",
                             "l", "à", "se", "son", "sa", "ses"}
                words = set(re.findall(r'\b[a-zéèêëàâäùûüôöîïç]{3,}\b', desc)) - stopwords
                state_keywords.append((s, words))
            
            # Comparer chaque paire
            processed = set()
            for i in range(len(state_keywords)):
                if state_keywords[i][0].get("state_id") in processed:
                    continue
                    
                group = [state_keywords[i][0]]
                words_i = state_keywords[i][1]
                
                if not words_i:
                    continue
                
                for j in range(i + 1, len(state_keywords)):
                    if state_keywords[j][0].get("state_id") in processed:
                        continue
                    
                    words_j = state_keywords[j][1]
                    if not words_j:
                        continue
                    
                    # Calcul similarité Jaccard
                    intersection = words_i & words_j
                    union = words_i | words_j
                    similarity = len(intersection) / len(union) if union else 0
                    
                    if similarity >= similarity_threshold:
                        group.append(state_keywords[j][0])
                        processed.add(state_keywords[j][0].get("state_id"))
                
                if len(group) > 1:
                    # Garder le plus récent (last_update le plus récent)
                    group.sort(key=lambda s: s.get("last_update", s.get("created_at", "")), reverse=True)
                    keep = group[0]
                    remove = group[1:]
                    
                    duplicate_groups.append({
                        "keep_id": keep.get("state_id"),
                        "keep_description": keep.get("description", "")[:80],
                        "remove_ids": [s.get("state_id") for s in remove],
                        "remove_descriptions": [s.get("description", "")[:80] for s in remove],
                        "category": cat,
                        "reason": f"Similarite mots-cles dans categorie {cat}"
                    })
                    processed.add(keep.get("state_id"))
        
        # Passe 3 (optionnelle): Validation LLM inter-catégories
        if archiviste_controller and len(unresolved) >= 2:
            llm_duplicates = await _detect_duplicates_with_llm(unresolved, archiviste_controller)
            if llm_duplicates:
                # Fusionner avec les doublons déjà détectés
                existing_remove_ids = set()
                for g in duplicate_groups:
                    existing_remove_ids.update(g["remove_ids"])
                
                for llm_group in llm_duplicates:
                    # Ne pas dupliquer les résolutions
                    new_remove = [rid for rid in llm_group["remove_ids"] if rid not in existing_remove_ids]
                    if new_remove:
                        llm_group["remove_ids"] = new_remove
                        duplicate_groups.append(llm_group)
                        existing_remove_ids.update(new_remove)
        
        total_removable = sum(len(g["remove_ids"]) for g in duplicate_groups)
        print(f"[DEDUP-STATES] {len(duplicate_groups)} groupes de doublons, {total_removable} etats a supprimer")
        
        return {
            "duplicates": duplicate_groups,
            "stats": {
                "total_states": len(unresolved),
                "groups": len(duplicate_groups),
                "removable": total_removable
            }
        }
    
    except Exception as e:
        print(f"[DEDUP-STATES] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {"duplicates": [], "stats": {"error": str(e)}}


async def _detect_duplicates_with_llm(
    states: List[Dict[str, Any]], 
    archiviste_controller
) -> List[Dict[str, Any]]:
    """Détection doublons via LLM pour les cas subtils (descriptions reformulées)."""
    try:
        states_list = "\n".join([
            f"  #{s.get('state_id')} [{s.get('category')}]: {s.get('description', '')[:100]}"
            for s in states
        ])
        
        prompt = f"""Analyse ces etats actifs et identifie les DOUBLONS (descriptions semblables ou redondantes).

ETATS ACTIFS:
{states_list}

CRITERES DE DOUBLON:
- Meme theme/sujet reformule differemment
- Un etat est une version plus detaillee d'un autre
- Deux etats decrivent la meme situation/emotion

REPONSE JSON STRICT:
{{
  "duplicate_groups": [
    {{
      "keep_id": 42,
      "remove_ids": [43],
      "reason": "Meme sujet reformule"
    }}
  ]
}}

Si aucun doublon: {{"duplicate_groups": []}}
Reponds UNIQUEMENT en JSON."""
        
        response, error = await archiviste_controller.call_chat_api(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=500,
            context_length=4096,
            is_json=False
        )
        
        if error or not response:
            print(f"[DEDUP-STATES] Erreur LLM dedup: {error}")
            return []
        
        json_match = re.search(r'\{[\s\S]*\}', response)
        if not json_match:
            return []
        
        result = json.loads(json_match.group())
        groups = result.get("duplicate_groups", [])
        
        if groups:
            print(f"[DEDUP-STATES] LLM: {len(groups)} groupes de doublons detectes")
        
        return groups
    
    except Exception as e:
        print(f"[DEDUP-STATES] Erreur LLM dedup: {e}")
        return []


def resolve_duplicate_states(
    json_manager,
    duplicate_groups: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Résout les doublons détectés en gardant le plus récent et résolvant les autres.
    
    Args:
        json_manager: Instance JournalJSONManager
        duplicate_groups: Liste de groupes de doublons depuis detect_duplicate_states
    
    Returns:
        Stats {resolved: int, failed: int, errors: []}
    """
    stats = {"resolved": 0, "failed": 0, "errors": []}
    
    try:
        for group in duplicate_groups:
            keep_id = group.get("keep_id")
            remove_ids = group.get("remove_ids", [])
            reason = group.get("reason", "Doublon detecte")
            
            for rid in remove_ids:
                try:
                    success = json_manager.resolve_state(
                        state_id=rid,
                        resolution_note=f"Doublon de #{keep_id}: {reason}"
                    )
                    if success:
                        stats["resolved"] += 1
                        print(f"[DEDUP-STATES] Doublon #{rid} resolu (conserve #{keep_id})")
                    else:
                        stats["failed"] += 1
                        stats["errors"].append(f"#{rid}: echec resolution")
                except Exception as e:
                    stats["failed"] += 1
                    stats["errors"].append(f"#{rid}: {str(e)}")
        
        print(f"[DEDUP-STATES] Deduplication terminee: {stats['resolved']} resolus, {stats['failed']} echecs")
        return stats
    
    except Exception as e:
        print(f"[DEDUP-STATES] ERROR resolve_duplicate_states: {e}")
        stats["errors"].append(str(e))
        return stats


# ============================================================
# RÉSOLUTION ÉTATS VIA CONVERSATIONS RÉCENTES
# ============================================================

async def detect_resolved_in_conversations(
    json_manager,
    archiviste_controller,
    conversations_dir: str = "data/conversations",
    max_conversations: int = 10
) -> Dict[str, Any]:
    """
    Analyse les conversations récentes pour détecter les états qui 
    ont été implicitement résolus dans les échanges.
    
    Args:
        json_manager: Instance JournalJSONManager
        archiviste_controller: Contrôleur LLM pour analyse
        conversations_dir: Dossier des conversations
        max_conversations: Nombre max de conversations à analyser
    
    Returns:
        Dict {resolved_ids: [int], resolution_notes: {id: note}}
    """
    try:
        print("[CONV-RESOLVE] Analyse conversations pour resolution etats...")
        
        # 1. Récupérer les états actifs
        active_states_data = json_manager.get_active_states()
        all_states = active_states_data.get("states", [])
        unresolved = [s for s in all_states if not s.get("resolved", False)]
        
        if not unresolved:
            print("[CONV-RESOLVE] Aucun etat actif a verifier")
            return {"resolved_ids": [], "resolution_notes": {}}
        
        # 2. Extraire le contenu des conversations récentes
        conv_path = Path(conversations_dir)
        if not conv_path.exists():
            print(f"[CONV-RESOLVE] Dossier conversations non trouve: {conversations_dir}")
            return {"resolved_ids": [], "resolution_notes": {}}
        
        # Trier par date de modification, prendre les plus récentes
        conv_files = sorted(
            [f for f in conv_path.glob("*.json") if f.name != "index.json"],
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )[:max_conversations]
        
        if not conv_files:
            print("[CONV-RESOLVE] Aucune conversation trouvee")
            return {"resolved_ids": [], "resolution_notes": {}}
        
        # 3. Extraire les résumés de conversations
        conversation_summaries = []
        for conv_file in conv_files:
            try:
                with open(conv_file, 'r', encoding='utf-8') as f:
                    conv_data = json.load(f)
                
                # Essayer plusieurs clés pour les messages
                messages = []
                if isinstance(conv_data, dict):
                    messages = conv_data.get("messages", conv_data.get("history", []))
                elif isinstance(conv_data, list):
                    messages = conv_data
                
                if not messages:
                    continue
                
                # Extraire les 30 derniers messages
                recent = messages[-30:] if len(messages) > 30 else messages
                parts = []
                for msg in recent:
                    if isinstance(msg, dict):
                        role = msg.get("role", "?")
                        content = msg.get("content", "")
                        if isinstance(content, str) and content.strip():
                            # Tronquer les messages très longs
                            text = content[:300]
                            parts.append(f"{role.upper()}: {text}")
                
                if parts:
                    conv_name = conv_file.stem
                    summary = "\n".join(parts[-15:])  # Max 15 messages pour le prompt
                    conversation_summaries.append(f"=== {conv_name} ===\n{summary}")
            
            except Exception as e:
                print(f"[CONV-RESOLVE] Erreur lecture {conv_file.name}: {e}")
                continue
        
        if not conversation_summaries:
            print("[CONV-RESOLVE] Aucun contenu extractible")
            return {"resolved_ids": [], "resolution_notes": {}}
        
        print(f"[CONV-RESOLVE] {len(conversation_summaries)} conversations a analyser contre {len(unresolved)} etats")
        
        # 4. Appel LLM pour détecter les résolutions
        result = await _analyze_states_vs_conversations(
            unresolved, 
            conversation_summaries, 
            archiviste_controller
        )
        
        return result
    
    except Exception as e:
        print(f"[CONV-RESOLVE] ERROR: {e}")
        import traceback
        traceback.print_exc()
        return {"resolved_ids": [], "resolution_notes": {}}


async def _analyze_states_vs_conversations(
    states: List[Dict[str, Any]],
    conversation_summaries: List[str],
    archiviste_controller
) -> Dict[str, Any]:
    """Analyse LLM: croise les états actifs avec les conversations pour détecter les résolutions."""
    try:
        # Construire la checklist des états
        states_text = "\n".join([
            f"  #{s.get('state_id')} [{s.get('category')}] ({s.get('importance', 'medium')}): {s.get('description', '')[:120]}"
            for s in states
        ])
        
        # Limiter le contexte conversations
        conv_text = "\n\n".join(conversation_summaries[:5])
        if len(conv_text) > 6000:
            conv_text = conv_text[:6000] + "\n[... tronque ...]"
        
        prompt = f"""Analyse ces etats actifs et determine lesquels ont ete RESOLUS dans les conversations recentes.

ETATS ACTIFS NON RESOLUS:
{states_text}

CONVERSATIONS RECENTES:
{conv_text}

REGLES DE RESOLUTION:
- Un etat est RESOLU si la conversation montre clairement que le sujet est traite/termine/depasse
- "technique": resolu si le probleme technique est corrige ou abandonne (ex: changement de modele deja effectue)
- "humeur": resolu si l'emotion a clairement change ou est depassee
- "apprentissage": resolu si le debat/apprentissage est conclu
- "relation": resolu si la dynamique a evolue ou est integree
- "personnel": resolu si l'identite/situation est confirmee et integree
- Un etat dont la description contient "resolu" ou "termine" EST resolu
- Un etat qui n'est plus mentionne depuis plusieurs conversations EST probablement resolu

REPONDS EN JSON STRICT:
{{
  "resolved_state_ids": [42, 52],
  "resolution_notes": {{
    "42": "Raison factuelle de la resolution",
    "52": "Raison factuelle de la resolution"
  }}
}}

Si aucun etat n'est resolu: {{"resolved_state_ids": [], "resolution_notes": {{}}}}
Reponds UNIQUEMENT en JSON."""
        
        response, error = await archiviste_controller.call_chat_api(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=800,
            context_length=8192,
            is_json=False
        )
        
        if error or not response:
            print(f"[CONV-RESOLVE] Erreur LLM: {error}")
            return {"resolved_ids": [], "resolution_notes": {}}
        
        # Parse JSON
        json_match = re.search(r'\{[\s\S]*\}', response)
        if not json_match:
            print(f"[CONV-RESOLVE] Reponse LLM non-JSON: {response[:100]}")
            return {"resolved_ids": [], "resolution_notes": {}}
        
        result = json.loads(json_match.group())
        resolved = result.get("resolved_state_ids", [])
        notes = result.get("resolution_notes", {})
        
        print(f"[CONV-RESOLVE] LLM: {len(resolved)} etats detectes comme resolus dans les conversations")
        
        return {"resolved_ids": resolved, "resolution_notes": notes}
    
    except Exception as e:
        print(f"[CONV-RESOLVE] Erreur analyse LLM: {e}")
        return {"resolved_ids": [], "resolution_notes": {}}


def apply_conversation_resolutions(
    json_manager,
    resolution_result: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Applique les résolutions détectées dans les conversations.
    
    Args:
        json_manager: Instance JournalJSONManager
        resolution_result: Résultat de detect_resolved_in_conversations
    
    Returns:
        Stats {resolved: int, failed: int}
    """
    stats = {"resolved": 0, "failed": 0, "errors": []}
    
    resolved_ids = resolution_result.get("resolved_ids", [])
    notes = resolution_result.get("resolution_notes", {})
    
    for state_id in resolved_ids:
        try:
            note = notes.get(str(state_id), "Resolu dans les conversations recentes")
            success = json_manager.resolve_state(
                state_id=state_id,
                resolution_note=f"[CONV-RESOLVE] {note}"
            )
            if success:
                stats["resolved"] += 1
                print(f"[CONV-RESOLVE] Etat #{state_id} resolu: {note[:60]}")
            else:
                stats["failed"] += 1
        except Exception as e:
            stats["failed"] += 1
            stats["errors"].append(f"#{state_id}: {str(e)}")
    
    print(f"[CONV-RESOLVE] Resolutions appliquees: {stats['resolved']} OK, {stats['failed']} echecs")
    return stats


# ============================================================
# PIPELINE COMPLÈTE POST-RÊVE
# ============================================================

async def run_full_maintenance(
    json_manager,
    archiviste_controller,
    conversations_dir: str = "data/conversations"
) -> Dict[str, Any]:
    """
    Pipeline complète de maintenance des états actifs.
    Appelée depuis le Dream Engine après le rêve.
    
    Étapes:
    1. Déduplication des doublons
    2. Résolution via conversations récentes  
    3. Auto-résolution des états inactifs (3j medium, 7j high)
    
    Args:
        json_manager: Instance JournalJSONManager
        archiviste_controller: Contrôleur LLM
        conversations_dir: Dossier des conversations
    
    Returns:
        Dict avec résultats de chaque étape
    """
    results = {
        "dedup": {"resolved": 0},
        "conv_resolve": {"resolved": 0},
        "auto_resolve": {"resolved": 0},
        "total_resolved": 0
    }
    
    try:
        print("[MAINTENANCE] Pipeline complete de maintenance etats actifs...")
        
        # Étape 1: Déduplication
        print("[MAINTENANCE] Etape 1/3: Deduplication...")
        dedup_result = await detect_duplicate_states(
            json_manager=json_manager,
            archiviste_controller=archiviste_controller,
            similarity_threshold=0.5
        )
        if dedup_result.get("duplicates"):
            dedup_stats = resolve_duplicate_states(
                json_manager=json_manager,
                duplicate_groups=dedup_result["duplicates"]
            )
            results["dedup"] = dedup_stats
        else:
            print("[MAINTENANCE] Aucun doublon detecte")
        
        # Étape 2: Résolution via conversations
        print("[MAINTENANCE] Etape 2/3: Resolution via conversations...")
        conv_result = await detect_resolved_in_conversations(
            json_manager=json_manager,
            archiviste_controller=archiviste_controller,
            conversations_dir=conversations_dir,
            max_conversations=10
        )
        if conv_result.get("resolved_ids"):
            conv_stats = apply_conversation_resolutions(
                json_manager=json_manager,
                resolution_result=conv_result
            )
            results["conv_resolve"] = conv_stats
        else:
            print("[MAINTENANCE] Aucun etat resolu dans les conversations")
        
        # Étape 3: Auto-résolution inactivité
        print("[MAINTENANCE] Etape 3/3: Auto-resolution inactivite...")
        inactive = detect_inactive_states(
            json_manager=json_manager,
            threshold_days=3,
            exclude_high_importance=False,
            high_importance_threshold_days=7
        )
        if inactive:
            ar_stats = await auto_resolve_states(
                json_manager=json_manager,
                archiviste_controller=archiviste_controller,
                states_to_resolve=inactive,
                dry_run=False,
                require_llm_validation=True
            )
            results["auto_resolve"] = ar_stats
        else:
            print("[MAINTENANCE] Aucun etat inactif a auto-resoudre")
        
        # Total
        results["total_resolved"] = (
            results["dedup"].get("resolved", 0) +
            results["conv_resolve"].get("resolved", 0) +
            results["auto_resolve"].get("resolved", 0)
        )
        
        print(f"[MAINTENANCE] Pipeline terminee: {results['total_resolved']} etats resolus au total")
        print(f"  - Doublons: {results['dedup'].get('resolved', 0)}")
        print(f"  - Conversations: {results['conv_resolve'].get('resolved', 0)}")
        print(f"  - Inactivite: {results['auto_resolve'].get('resolved', 0)}")
        
        return results
    
    except Exception as e:
        print(f"[MAINTENANCE] ERROR pipeline: {e}")
        import traceback
        traceback.print_exc()
        results["error"] = str(e)
        return results
