"""
🔍 CONVERSATION SCANNER - Recherche simple dans conversations récentes
========================================================================

Scanner léger qui cherche des mots-clés dans les N dernières conversations
sans index ni base de données complexe.

PHILOSOPHIE:
- Simple et rapide (~50ms pour 20 conversations)
- 0 dépendance (juste pathlib + json)
- Pas d'index à maintenir
- Fonctionne MÊME sans résumés

USAGE:
    from conversation_scanner import search_recent_conversations
    
    results = search_recent_conversations(
        keywords=["Bob", "vol", "PC"],
        max_conversations=20
    )
    
    for r in results:
        print(f"{r['date']}: {r['matched_keywords']} trouvés")

RETOUR:
    Liste de dict [{
        'conv_id': '2026-01-25_15-41-05_bb69',
        'date': '2026-01-25',
        'msg_index': 12,
        'matched_keywords': ['Bob', 'vol'],
        'context': [msg1, msg2, ...],  # 7 messages max
        'score': 2  # Nombre de keywords trouvés
    }]
"""

import json
import re
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime


def search_recent_conversations(
    keywords: List[str],
    max_conversations: int = 20,
    context_size: int = 5,  # 5 messages avant/après = 11 messages total
    max_results: int = 10,
    debug: bool = True
) -> List[Dict]:
    """
    Scanne les N dernières conversations pour trouver des mots-clés.
    
    Args:
        keywords: Liste de mots-clés à chercher (case-insensitive)
        max_conversations: Nombre de conversations récentes à scanner
        context_size: Nombre de messages avant/après le match
        max_results: Nombre max de résultats retournés
        debug: Afficher logs de progression
        
    Returns:
        Liste de résultats triés par score (nombre de keywords trouvés)
    """
    if debug:
        print(f"[CONV-SCANNER] 🔍 Recherche: {keywords}")
        print(f"[CONV-SCANNER] 📚 Scan {max_conversations} conversations récentes...")
    
    conv_dir = Path("data/conversations")
    
    if not conv_dir.exists():
        if debug:
            print(f"[CONV-SCANNER] ❌ Dossier conversations introuvable: {conv_dir}")
        return []
    
    # Lister toutes les conversations (format: 2026-01-25_15-41-05_xxxx.json)
    # Exclure index.json
    conv_files = sorted(
        [f for f in conv_dir.glob("20*.json") if f.name != "index.json"],
        reverse=True  # Plus récentes d'abord
    )[:max_conversations]
    
    if debug:
        print(f"[CONV-SCANNER] 📂 {len(conv_files)} fichiers trouvés")
    
    if not conv_files:
        if debug:
            print("[CONV-SCANNER] ⚠️ Aucune conversation trouvée")
        return []
    
    results = []
    keywords_lower = [kw.lower() for kw in keywords]
    
    # Scanner chaque conversation
    for conv_file in conv_files:
        try:
            with open(conv_file, 'r', encoding='utf-8') as f:
                raw = json.load(f)
            
            # Support format étendu {messages, summaries} ET ancien format liste
            if isinstance(raw, dict) and "messages" in raw:
                messages = raw["messages"]
            elif isinstance(raw, list):
                messages = raw
            else:
                if debug:
                    print(f"[CONV-SCANNER] ⚠️ Format inconnu pour {conv_file.name}")
                continue
            
            # Chercher dans chaque message
            for i, msg in enumerate(messages):
                content = msg.get('content', '')
                role = msg.get('role', 'unknown')
                
                if not content or not isinstance(content, str):
                    continue
                
                content_lower = content.lower()
                
                # FILTRE MÉTA : Exclure UNIQUEMENT les messages USER qui demandent de chercher
                # (Ne pas bloquer les conversations normales entre utilisateurs)
                is_meta = False
                if role == 'user':  # Seulement pour les messages utilisateur
                    meta_patterns = [
                        r'cherch(?:e|er|es?)',
                        r'(?:te |tu )?(?:souviens?|rappelles?)',
                        r'lis (?:la )?conversation',
                        r'consulter?\s+(?:mes\s+)?conversations?',
                        r'scanner?\s+(?:mes\s+)?conversations?',
                    ]
                    is_meta = any(re.search(pattern, content_lower) for pattern in meta_patterns)
                
                if is_meta and debug:
                    print(f"[CONV-SCANNER] 🚫 Message méta ignoré (user demande recherche): '{content[:80]}...'")
                
                # Vérifier quels keywords matchent (MOTS ENTIERS uniquement avec word boundaries)
                matched = []
                for kw, kw_lower in zip(keywords, keywords_lower):
                    # Pattern regex pour match de mot entier (insensible à la casse)
                    pattern = r'\b' + re.escape(kw_lower) + r'\b'
                    if re.search(pattern, content_lower):
                        matched.append(kw)
                
                if matched and not is_meta:  # Ignorer si méta
                    # Extraire contexte (N messages avant + match + N après)
                    start = max(0, i - context_size)
                    end = min(len(messages), i + context_size + 1)
                    context = messages[start:end]
                    
                    # Calculer score amélioré
                    base_score = len(set(matched))  # Keywords uniques
                    
                    # Bonus si conversation plus ancienne (évite méta-boucles)
                    date_str = conv_file.stem[:10]
                    try:
                        from datetime import datetime
                        conv_date = datetime.strptime(date_str, '%Y-%m-%d')
                        today = datetime.now()
                        days_ago = (today - conv_date).days
                        age_bonus = min(days_ago * 0.1, 1.0)  # Max +1.0 pour conversations anciennes
                    except:
                        age_bonus = 0
                    
                    # Bonus si message long (plus de contenu = plus pertinent)
                    length_bonus = 0.5 if len(content) > 100 else 0
                    
                    final_score = base_score + age_bonus + length_bonus
                    
                    results.append({
                        'conv_id': conv_file.stem,
                        'conv_file': str(conv_file),
                        'date': conv_file.stem[:10],  # 2026-01-25
                        'time': conv_file.stem[11:19],  # 15-41-05
                        'msg_index': i,
                        'matched_keywords': matched,
                        'matched_message': content[:200],  # Preview du message
                        'context': context,
                        'score': final_score,
                        'base_score': base_score,
                        'age_bonus': age_bonus,
                        'length_bonus': length_bonus,
                        'context_start': start,
                        'context_end': end
                    })
        
        except Exception as e:
            if debug:
                print(f"[CONV-SCANNER] ⚠️ Erreur lecture {conv_file.name}: {e}")
            continue
    
    # Trier par score décroissant (plus de keywords = plus pertinent)
    results.sort(key=lambda r: r['score'], reverse=True)
    
    # Limiter résultats
    results = results[:max_results]
    
    if debug:
        print(f"[CONV-SCANNER] ✅ {len(results)} résultats trouvés")
        if results:
            print(f"[CONV-SCANNER] 🏆 Top résultat: {results[0]['date']} (score {results[0]['score']})")
    
    return results


def format_results_for_injection(
    results: List[Dict],
    keywords: List[str],
    max_results_display: int = 3,
    max_chars_per_message: int = 150
) -> str:
    """
    Formate les résultats pour injection dans le contexte Luna.
    
    Args:
        results: Résultats de search_recent_conversations()
        keywords: Keywords originaux cherchés
        max_results_display: Nombre max de résultats affichés
        max_chars_per_message: Longueur max par message
        
    Returns:
        Contexte formaté prêt pour injection
    """
    if not results:
        return f"🔍 RECHERCHE CONVERSATIONS: Aucun résultat pour {keywords}"
    
    context_parts = [
        "🔍 RECHERCHE DANS CONVERSATIONS RÉCENTES",
        "",
        f"📌 Keywords: {', '.join(keywords)}",
        f"✅ {len(results)} résultat(s) trouvé(s)",
        ""
    ]
    
    for i, r in enumerate(results[:max_results_display], 1):
        context_parts.append(f"━━━ RÉSULTAT {i}/{min(len(results), max_results_display)} ━━━")
        context_parts.append(f"📅 Date: {r['date']} {r['time'].replace('-', ':')}")
        context_parts.append(f"🎯 Mots trouvés: {', '.join(r['matched_keywords'])} (score: {r['score']})")
        context_parts.append(f"📍 Message #{r['msg_index']} (contexte: {r['context_start']}-{r['context_end']})")
        context_parts.append("")
        context_parts.append("💬 CONTEXTE:")
        
        # Afficher les messages du contexte
        for msg in r['context']:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            
            # Indicateur visuel
            if role == 'user':
                icon = "👤"
            elif role == 'assistant':
                icon = "🌸"
            else:
                icon = "🤖"
            
            # Tronquer si trop long
            if len(content) > max_chars_per_message:
                content = content[:max_chars_per_message] + "..."
            
            context_parts.append(f"{icon} {content}")
        
        context_parts.append("")
    
    context_parts.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    context_parts.append("")
    context_parts.append("⚡ RÉSULTATS DE TA RECHERCHE ACTIVE ⚡")
    context_parts.append("")
    context_parts.append("Tu viens de déclencher une consultation de l'historique conversationnel.")
    context_parts.append("Voici les résultats concrets que tu as trouvés.")
    context_parts.append("")
    context_parts.append("💡 COMMENT UTILISER CES RÉSULTATS:")
    context_parts.append("1. Cite des DÉTAILS PRÉCIS des conversations ci-dessus")
    context_parts.append("2. Mentionne les DATES pour contextualiser")
    context_parts.append("3. Si plusieurs résultats: synthétise ou demande clarification")
    context_parts.append("4. NE DIS PAS 'je ne me souviens pas' - TU AS LES INFOS SOUS LES YEUX")
    if len(results) > max_results_display:
        context_parts.append(f"")
        context_parts.append(f"ℹ️ {len(results) - max_results_display} autre(s) résultat(s) disponible(s) (non affichés)")
    
    return "\n".join(context_parts)


def extract_keywords_from_query(query: str, fallback_keywords: Optional[List[str]] = None) -> List[str]:
    """
    Extrait mots-clés basiques d'une query (fallback simple si IA pas dispo).
    
    Args:
        query: Question utilisateur
        fallback_keywords: Keywords par défaut si extraction échoue
        
    Returns:
        Liste de mots-clés extraits
    """
    # Nettoyer la query
    query_clean = query.lower()
    
    # Retirer mots vides français courants
    stopwords = {
        'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'et', 'ou', 'mais',
        'donc', 'car', 'si', 'que', 'qui', 'quoi', 'où', 'quand', 'comment',
        'tu', 'te', 'toi', 'je', 'me', 'moi', 'il', 'elle', 'on', 'nous', 'vous',
        'souviens', 'rappelle', 'parlé', 'discuté', 'conversation', 'dit'
    }
    
    # Splitter et filtrer
    words = [w.strip('.,!?;:«»""()[]') for w in query_clean.split()]
    keywords = [w for w in words if len(w) > 2 and w not in stopwords]
    
    # Si rien trouvé, fallback
    if not keywords and fallback_keywords:
        return fallback_keywords
    
    # Limiter à 5 keywords max
    return keywords[:5]


# ========================================
# TESTS RAPIDES
# ========================================

if __name__ == "__main__":
    print("🧪 TEST CONVERSATION SCANNER\n")
    
    # Test 1: Recherche Bob
    print("━━━ Test 1: Recherche 'Bob' ━━━")
    results = search_recent_conversations(["Bob"], max_conversations=30, debug=True)
    
    if results:
        print("\n📊 RÉSULTATS:")
        for r in results[:3]:
            print(f"  • {r['date']}: {r['matched_keywords']} (score {r['score']})")
            print(f"    Preview: {r['matched_message'][:100]}...")
        
        print("\n📝 CONTEXTE FORMATÉ:")
        formatted = format_results_for_injection(results, ["Bob"], max_results_display=2)
        print(formatted[:500] + "...\n")
    else:
        print("  ❌ Aucun résultat\n")
    
    # Test 2: Recherche multiple keywords
    print("━━━ Test 2: Recherche 'vol PC' ━━━")
    results = search_recent_conversations(["vol", "PC"], max_conversations=20, debug=True)
    
    if results:
        print(f"\n📊 {len(results)} résultats trouvés")
        print(f"  🏆 Top: {results[0]['date']} (score {results[0]['score']})\n")
    else:
        print("  ❌ Aucun résultat\n")
    
    # Test 3: Extraction keywords basique
    print("━━━ Test 3: Extraction keywords ━━━")
    test_queries = [
        "Tu te souviens de Bob ?",
        "On a parlé du vol de PC hier",
        "Qu'est-ce que Casper a dit ?"
    ]
    
    for q in test_queries:
        kws = extract_keywords_from_query(q)
        print(f"  '{q}' → {kws}")
