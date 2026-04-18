"""
🧬 Bio Activation - Injection ciblée du profil biographique

Miroir de ego_activation.py pour la biographie utilisateur.

Workflow runtime (sur déclencheur magic phrase) :
1. Charge bio_compiled.json (groupes thématiques + faits)
2. Archiviste analyse le message → sélectionne 0-3 groupes pertinents
3. Retourne les faits des groupes sélectionnés pour injection

Stratégie double :
- Premier message → TOUS les groupes (portrait de départ)
- Messages suivants → sélection Archiviste (0-3 groupes, par magic phrase)

Latence : ~100-200ms (catalogue léger fourni à l'Archiviste)
Token budget : ~50-200 tokens selon nombre de faits injectés
"""

import json
from pathlib import Path
from typing import Optional


async def activate_bio_groups(
    user_message: str,
    archiviste_controller,
    user_name: str,
    is_new_session: bool = False,
) -> Optional[str]:
    """
    Sélectionne et formate les faits biographiques pertinents pour injection.

    Args:
        user_message      : Message utilisateur actuel
        archiviste_controller : Archiviste IA controller
        user_name         : Nom de l'utilisateur connecté
        is_new_session    : Si True, injecte TOUS les groupes (premier message)

    Returns:
        str formaté pour injection dans le system prompt, ou None si rien à injecter.
    """
    if not user_name:
        print("[BIO-ACTIVATION] Aucun utilisateur, skip.")
        return None

    # 1. Charger bio_compiled.json
    bio_json_path = Path("data/biographies") / user_name.lower() / "bio_compiled.json"

    if not bio_json_path.exists():
        print(f"[BIO-ACTIVATION] bio_compiled.json absent pour {user_name}, skip.")
        return None

    try:
        with open(bio_json_path, "r", encoding="utf-8") as f:
            bio_data = json.load(f)
    except Exception as e:
        print(f"[BIO-ACTIVATION] Erreur lecture bio_compiled.json: {e}")
        return None

    groups = bio_data.get("groups", {})
    if not groups:
        print(f"[BIO-ACTIVATION] Aucun groupe compilé pour {user_name}, skip.")
        return None

    # 2. Stratégie : premier message = ALL, sinon Archiviste sélectionne
    if is_new_session:
        selected_groups = list(groups.keys())
        reasoning = f"Premier message — portrait complet ({len(selected_groups)} groupes)"
        print(f"[BIO-ACTIVATION] Premier message → tous les groupes ({len(selected_groups)})")
    else:
        # Catalogue léger : nom + description + keywords (pas les faits)
        catalog = {
            name: {
                "description": data.get("description", ""),
                "keywords": data.get("keywords", [])[:6],
            }
            for name, data in groups.items()
            if isinstance(data, dict)
        }

        prompt = f"""Message utilisateur: "{user_message}"

**CATALOGUE GROUPES BIOGRAPHIQUES DE {user_name.upper()}** :
{json.dumps(catalog, indent=2, ensure_ascii=False)}

**MISSION** :
Sélectionne 0-3 groupes biographiques les plus pertinents pour ce message.

**RÈGLES** :
- Message neutre/salutation ("ok", "merci", "salut") → 0 groupe
- Pronoms personnels (je, moi, mon, ma, mes) ou prénom → 1-2 groupes
- Question sur l'utilisateur, ses goûts, sa vie → 1-3 groupes
- Jamais plus de 3 groupes
- Utilise description + keywords pour matching sémantique

**EXEMPLES** :
- "tu te souviens de mon chat?" → ["ANIMAUX"] ou ["RELATIONS"]
- "qu'est-ce que j'aime comme films?" → ["GOUTS"]
- "parle-moi de moi" → tous les groupes disponibles (max 3)
- "quelle heure est-il?" → []

**FORMAT JSON** :
{{
    "groups": ["GROUPE1", "GROUPE2"],
    "reasoning": "explication courte 1 phrase"
}}

Retourne UNIQUEMENT le JSON, rien d'autre."""

        try:
            messages = [{"role": "user", "content": prompt}]
            response, error = await archiviste_controller.call_chat_api(
                messages=messages,
                max_tokens=100,
                context_length=8000,
                temperature=0.2,
                is_json=True,
            )

            if error or not response:
                print(f"[BIO-ACTIVATION] Erreur Archiviste: {error}")
                return None

            selection = json.loads(response)
            selected_groups = selection.get("groups", [])
            reasoning = selection.get("reasoning", "")

            if not selected_groups:
                print(f"[BIO-ACTIVATION] Aucun groupe sélectionné (message neutre)")
                return None

            print(f"[BIO-ACTIVATION] Groupes sélectionnés: {selected_groups}")
            print(f"[BIO-ACTIVATION] Reasoning: {reasoning}")

        except json.JSONDecodeError as e:
            print(f"[BIO-ACTIVATION] Parse JSON error: {e}")
            return None
        except Exception as e:
            print(f"[BIO-ACTIVATION] Erreur sélection: {e}")
            return None

    # 3. Construire l'injection depuis les faits des groupes sélectionnés
    injection_parts = []
    total_facts = 0
    seen_contents: set = set()  # Déduplication inter-groupes (multi-appartenance)

    for group_name in selected_groups:
        if group_name not in groups:
            print(f"[BIO-ACTIVATION] Groupe inconnu: {group_name}, skip")
            continue

        group_data = groups[group_name]
        facts = group_data.get("facts", [])

        if not facts:
            continue

        facts_lines = []
        for fact in facts:
            content = fact.get("content", "")
            if not content or content in seen_contents:
                continue
            seen_contents.add(content)
            facts_lines.append(f"- {content}")

        if not facts_lines:
            continue

        section = f"### {group_name}\n" + "\n".join(facts_lines)
        injection_parts.append(section)
        total_facts += len(facts_lines)

    if not injection_parts:
        print("[BIO-ACTIVATION] Aucun fait à injecter")
        return None

    injection = (
        f"# PROFIL {user_name.upper()} — faits connus "
        f"(Groupes: {', '.join(selected_groups)})\n"
        + "\n\n".join(injection_parts)
        + "\n"
    )

    print(
        f"[BIO-ACTIVATION] Injection: {len(selected_groups)} groupes, "
        f"{total_facts} faits (~{len(injection)//4} tokens)"
    )
    return injection
