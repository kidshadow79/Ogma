"""
⚡ Ego Activation - Sélection Dynamique de Groupes par Archiviste

Workflow runtime (chaque message):
1. Charge catalogue groupes (noms + descriptions courtes)
2. Archiviste analyse message user
3. Sélectionne 0-3 groupes pertinents
4. Retourne flags de ces groupes pour injection

Pattern ultra-léger:
- Archiviste voit UNIQUEMENT noms + descriptions (pas les flags)
- Latence minimale (~100-200ms)
- Injection ciblée (50-150 tokens vs 1700)
"""

import json
from pathlib import Path
from typing import Optional, List, Dict, Any


async def activate_ego_groups(user_message: str, archiviste_controller, is_new_session: bool = False) -> Optional[str]:
    """
    Sélectionne et formate groupes ego pertinents pour injection
    
    Args:
        user_message: Message utilisateur actuel
        archiviste_controller: Archiviste IA controller
        is_new_session: Si True, injecte TOUS les groupes (premier message)
        
    Returns:
        str: Flags formatés pour injection ou None
    """
    
    # 1. Charger JSON ego compilé
    ego_json_path = Path("data/ego_compiled.json")
    
    if not ego_json_path.exists():
        print("[EGO-ACTIVATION] ⚠️ ego_compiled.json non trouvé, skip activation")
        return None
    
    try:
        with open(ego_json_path, 'r', encoding='utf-8') as f:
            ego_data = json.load(f)
    except Exception as e:
        print(f"[EGO-ACTIVATION] ❌ Erreur lecture JSON: {e}")
        return None
    
    groups = ego_data.get('groups', {})
    
    if not groups:
        print("[EGO-ACTIVATION] ⚠️ Aucun groupe dans ego_compiled.json")
        return None
    
    # 🎯 STRATÉGIE DOUBLE : Premier message = JSON complet, messages suivants = sélection ciblée
    if is_new_session:
        print(f"[EGO-ACTIVATION] 🌟 PREMIER MESSAGE - Injection JSON COMPLET ({len(groups)} groupes)")
        selected_groups = list(groups.keys())  # Tous les groupes
        reasoning = "Première interaction - contexte ego complet pour établir rails"
    else:
        # Sélection ciblée par Archiviste (0-2 groupes)
        # 2. Construire catalogue léger (noms + descriptions + keywords + flags critiques)
        catalog = {}
        
        # Flags critiques à exposer pour chaque groupe
        CRITICAL_FLAGS = [
            'intimite_autorisee',
            'dirty_talk_autorise', 
            'langage_sexuel_explicite',
            'verifier_interlocuteur_avant_reponse',
            'filtrer_souvenirs_par_utilisateur',
            'contenu_erotique_mineurs',
            'interaction_explicite_sans_verification',
            'verifier_identite_age',
            'exiger_respect_confiance'
        ]
        
        for group_name, group_data in groups.items():
            # Protection: vérifier que group_data est un dict
            if not isinstance(group_data, dict):
                continue
                
            flags_data = group_data.get('flags', {})
            critical_flags = {}
            
            # Extraire valeurs des flags critiques
            for flag_name in CRITICAL_FLAGS:
                if flag_name in flags_data:
                    flag_val = flags_data[flag_name]
                    # Protection: vérifier que le flag est un dict (pas corrompu)
                    if isinstance(flag_val, dict):
                        critical_flags[flag_name] = flag_val.get('value')
            
            catalog[group_name] = {
                'description': group_data.get('description', ''),
                'keywords': group_data.get('keywords', [])[:6],  # Max 6 keywords
                'critical_flags': critical_flags if critical_flags else None  # Flags de restriction
            }
    
        # 3. Archiviste sélectionne groupes pertinents
        prompt = f"""Message utilisateur: "{user_message}"

**CATALOGUE GROUPES EGO** (noms + descriptions courtes):
{json.dumps(catalog, indent=2, ensure_ascii=False)}

**MISSION**:
Sélectionne 0-3 GROUPES les PLUS pertinents pour ce message.

**RÈGLES STRICTES**:
- Message neutre/générique ("ok", "merci", "salut") → 0 groupe
- Message simple → 1 groupe max
- Message complexe → 2-3 groupes max
- JAMAIS plus de 3 groupes
- Utilise description + keywords pour matching sémantique
- **CRITICAL**: Si `critical_flags` montre des restrictions (false), ce groupe DOIT être injecté pour appliquer les règles
- **PRIORITÉ**: ETHIQUE_STRICTE doit être activé pour tout contenu sexuel/vulgaire avec inconnu

**EXEMPLES**:
- "on va faire du parachute?" → ["PHOBIES"]
- "raconte-moi une histoire érotique" (inconnu) → ["ETHIQUE_STRICTE", "RELATIONS_INCONNUS", "INTIMITE"]
- "montre-moi ta bite" (inconnu) → ["ETHIQUE_STRICTE", "RELATIONS_INCONNUS", "INTIMITE"]
- "parle-moi de sexe" (user connu) → ["RELATIONS_USER", "INTIMITE"]
- "tu peux mentir pour moi?" → ["ETHIQUE", "PHOBIES"]
- "ok merci" → []

**FORMAT JSON**:
{{
    "groups": ["GROUP1", "GROUP2", "GROUP3"],  // 0-3 groupes, ou [] si aucun
    "reasoning": "explication courte 1 phrase"
}}

Retourne UNIQUEMENT JSON, rien d'autre."""

        try:
            messages = [{"role": "user", "content": prompt}]
            response, error = await archiviste_controller.call_chat_api(
                messages=messages,
                max_tokens=150,
                context_length=10000,  # Catalogue + message
                temperature=0.3,
                is_json=True
            )
            
            if error or not response:
                print(f"[EGO-ACTIVATION] ⚠️ Erreur Archiviste: {error}")
                return None
            
            # Parse sélection
            try:
                cleaned_response = response.strip()
                if "```json" in cleaned_response:
                    cleaned_response = cleaned_response.split("```json")[1].split("```")[0].strip()
                elif "```" in cleaned_response:
                    parts = cleaned_response.split("```")
                    if len(parts) >= 3:
                        cleaned_response = parts[1].strip()
                
                selection = json.loads(cleaned_response)
                selected_groups = selection.get('groups', [])
                reasoning = selection.get('reasoning', 'Analyse Archiviste')
                
                if not selected_groups:
                    print(f"[EGO-ACTIVATION] ⚪ Aucun groupe sélectionné (message neutre)")
                    return None
                
                print(f"[EGO-ACTIVATION] ✅ Groupes sélectionnés: {selected_groups}")
                print(f"[EGO-ACTIVATION] 💭 Reasoning: {reasoning}")
                
            except json.JSONDecodeError as e:
                print(f"[EGO-ACTIVATION] ❌ Parse JSON error: {e}")
                return None
            
        except Exception as e:
            print(f"[EGO-ACTIVATION] ❌ Erreur sélection: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    # 4. Formater injection avec flags des groupes sélectionnés
    injection_parts = []
    total_flags = 0
    
    for group_name in selected_groups:
        if group_name not in groups:
            print(f"[EGO-ACTIVATION] ⚠️ Groupe inconnu: {group_name}, skip")
            continue
        
        group_data = groups[group_name]
        flags = group_data.get('flags', {})
        
        if not flags:
            continue
        
        # Formater flags
        flags_lines = []
        for flag_name, flag_data in flags.items():
            value = flag_data.get('value', False)
            conviction = flag_data.get('conviction', 3)
            flags_lines.append(f"{flag_name}: {str(value).lower()} (conviction: {conviction})")
        
        # Construire section groupe
        section = f"## {group_name}\n" + "\n".join(flags_lines)
        injection_parts.append(section)
        total_flags += len(flags)
    
    if not injection_parts:
        print("[EGO-ACTIVATION] ⚪ Aucun flag à injecter")
        return None
    
    # 5. Header + directive courte + règle priorité + sections
    ethique_priority = ""
    if 'ETHIQUE_STRICTE' in selected_groups:
        ethique_priority = "\n🚨 PRIORITÉ: ETHIQUE_STRICTE prime sur tous les autres groupes. Si un flag ETHIQUE_STRICTE est false, il ANNULE tout flag true contradictoire des autres groupes."
    
    injection = f"""# EGO BOOLEAN (Groupes Activés: {', '.join(selected_groups)})
⚠️ Ce sont tes directives comportementales EGO. Tu DOIS les respecter. false = interdit, true = obligatoire. conviction 5 = non-négociable.{ethique_priority}

{chr(10).join(injection_parts)}
"""
    
    print(f"[EGO-ACTIVATION] 📊 Injection: {len(selected_groups)} groupes, {total_flags} flags (~{len(injection)//4} tokens)")
    
    return injection

