"""
Magic Phrase Normalizer — OGMA
==============================
Traduit les phrases magiques EN → équivalent FR canonique avant analyse.
Tous les détecteurs existants restent en FR et continuent de fonctionner.

Usage:
    from utils.magic_phrase_normalizer import normalize_magic_phrases
    text = normalize_magic_phrases(text)

Principe:
    - Appliqué sur le message utilisateur ET la réponse IA avant tout scan.
    - Transformation non destructive : seule la phrase magique est remplacée,
      le contenu payload (ex: "Yohan is an architect") est préservé tel quel.
    - Idempotent : si la phrase est déjà en FR, aucun changement.
"""

import re
from typing import List, Tuple

# ---------------------------------------------------------------------------
# Table de normalisation  EN phrase  →  FR canonical
# Format: list de (pattern_regex, replacement_with_captured_group)
# Les groupes capturants (\1, \2...) préservent le payload utile.
# ---------------------------------------------------------------------------

_RULES: List[Tuple[str, str]] = [

    # ── MÉMORISATION ────────────────────────────────────────────────────────
    # "memorize this: ..."  /  "remember this: ..."  /  "I need to remember this: ..."
    (
        r"\b(?:please\s+)?(?:memorize|remember)\s+this\s*[:\-]\s*(.+)",
        r"il faut que je me souvienne de ça: \1"
    ),
    (
        r"\bI\s+(?:need|want)\s+to\s+(?:memorize|remember)\s+this\s*[:\-]\s*(.+)",
        r"il faut que je me souvienne de ça: \1"
    ),
    (
        r"\bI\s+(?:must|have\s+to)\s+(?:memorize|remember)\s+(?:this|that)\s*[:\-]\s*(.+)",
        r"il faut que je me souvienne de ça: \1"
    ),
    (
        r"\bI\s+need\s+to\s+remember\s*[:\-]\s*(.+)",
        r"il faut que je me souvienne de ça: \1"
    ),
    # "save this to memory: ..."
    (
        r"\bsave\s+this\s+(?:to\s+)?(?:memory|to\s+your\s+memory)\s*[:\-]\s*(.+)",
        r"il faut que je me souvienne de ça: \1"
    ),
    # "keep this in mind: ..."
    (
        r"\bkeep\s+this\s+in\s+mind\s*[:\-]\s*(.+)",
        r"il faut que je me souvienne de ça: \1"
    ),

    # ── INTROSPECTION ────────────────────────────────────────────────────────
    (
        r"\byou\s+need\s+to\s+reflect\b",
        r"il faut que tu réfléchisses"
    ),
    (
        r"\bstart\s+(?:an?\s+)?introspection\b",
        r"lance une introspection"
    ),
    (
        r"\btrigger\s+(?:an?\s+)?introspection\b",
        r"déclenche une introspection"
    ),
    (
        r"\bactivate\s+(?:the\s+)?(?:subconscious|inner\s+mind)\b",
        r"active la subconscience"
    ),
    (
        r"\breflect\s+deeply\b",
        r"réfléchis en profondeur"
    ),
    (
        r"\bstop\s+reflecting\b",
        r"arrête de réfléchir"
    ),
    (
        r"\bstop\s+the\s+reflection\b",
        r"stop la réflexion"
    ),
    (
        r"\bI\s+need\s+to\s+reflect\s+on\s*[:\-]\s*(.+)",
        r"il faut que je réfléchisse sur : \1"
    ),

    # ── PERCEPTION VISUELLE ──────────────────────────────────────────────────
    (
        r"\bI\s+need\s+to\s+see\s+you\b",
        r"il faut que je te vois"
    ),
    (
        r"\bI\s+want\s+to\s+see\s+you\b",
        r"je veux te voir"
    ),
    (
        r"\bI\s+no\s+longer\s+need\s+to\s+see\s+you\b",
        r"je n'ai plus besoin de te voir"
    ),
    (
        r"\bI\s+can\s+stop\s+seeing\s+you\b",
        r"je peux arrêter de te voir"
    ),
    (
        r"\bI\s+(?:close|shut)\s+(?:my\s+)?(?:vision|camera|webcam)\b",
        r"je ferme ma vision"
    ),
    (
        r"\bactivate\s+(?:the\s+)?webcam\b",
        r"active la webcam"
    ),
    (
        r"\bdeactivate\s+(?:the\s+)?webcam\b",
        r"désactive la webcam"
    ),

    # ── ORGANIC PLANNER ──────────────────────────────────────────────────────
    (
        r"\bI\s+need\s+to\s+note\s+(?:this\s+)?event\s*[:\-]\s*(.+?)\s*-\s*(.+?)\s*-\s*(.+?)(?=\n|$)",
        r"il faut que je note cet évènement: \1 - \2 - \3"
    ),
    (
        r"\bnote\s+(?:this\s+)?event\s*[:\-]\s*(.+?)\s*-\s*(.+?)\s*-\s*(.+?)(?=\n|$)",
        r"note cet évènement: \1 - \2 - \3"
    ),
    (
        r"\badd\s+to\s+(?:the\s+)?(?:agenda|calendar|schedule)\s*[:\-]\s*(.+?)\s*-\s*(.+?)\s*-\s*(.+?)(?=\n|$)",
        r"ajoute à l'agenda: \1 - \2 - \3"
    ),
    (
        r"\bI\s+need\s+to\s+update\s+(?:the\s+)?event\s*[:\-]\s*(.+?)\s*-\s*(.+?)(?=\n|$)",
        r"il faut que je mette à jour l'évènement: \1 - \2"
    ),

    # ── GÉNÉRATION IMAGE ─────────────────────────────────────────────────────
    (
        r"\bI\s+(?:need|have)\s+to\s+create\s+an?\s+image\s+of\s*[:\-]\s*(.+)",
        r"je dois créer une image de : \1"
    ),
    (
        r"\bI\s+(?:need|have)\s+to\s+generate\s+an?\s+image\s+of\s*[:\-]\s*(.+)",
        r"je dois générer une image de : \1"
    ),
    (
        r"\bI(?:'m|\s+am)\s+going\s+to\s+create\s+an?\s+image\s+of\s*[:\-]\s*(.+)",
        r"je vais créer une image de : \1"
    ),

    # ── IMAGE-TO-IMAGE ───────────────────────────────────────────────────────
    (
        r"\bI\s+(?:need|have)\s+to\s+modify\s+this\s+image\s*[:\-]\s*(.+)",
        r"je dois modifier cette image : \1"
    ),
    (
        r"\bI\s+(?:need|have)\s+to\s+transform\s+this\s+image\s*[:\-]\s*(.+)",
        r"je dois transformer cette image : \1"
    ),
    (
        r"\bI(?:'m|\s+am)\s+going\s+to\s+modify\s+this\s+image\s*[:\-]\s*(.+)",
        r"je vais modifier cette image : \1"
    ),

    # ── BIOGRAPHIE ───────────────────────────────────────────────────────────
    (
        r"\bI\s+need\s+to\s+consult\s+(?:the\s+)?biography\s+of\s+(\w+)\b",
        r"il faut que je consulte la biographie de \1"
    ),
    (
        r"\bcomplete\s+my\s+biography\b",
        r"complète ma biographie"
    ),
    (
        r"\bupdate\s+my\s+biography\b",
        r"mets à jour ma biographie"
    ),
    (
        r"\benrich\s+my\s+profile\b",
        r"enrichis mon profil"
    ),

    # ── CONTEXTUAL RECALL ────────────────────────────────────────────────────
    (
        r"\bI\s+need\s+to\s+consult\s+our\s+conversation\s+(?:from|of)\s+(.+)",
        r"il faut que je consulte notre conversation de \1"
    ),

    # ── ÉDITEUR DOCS ─────────────────────────────────────────────────────────
    (
        r"\bcreate\s+a\s+markdown\s+(?:document|file)\s+(?:on|about)\s+(.+)",
        r"crée un document markdown sur \1"
    ),
    (
        r"\bwrite\s+a\s+markdown\s+file\s+(?:that|which)\s+(.+)",
        r"écris un fichier markdown qui \1"
    ),
    (
        r"\bgenerate\s+a\s+markdown\s+document\s+of\s+(.+)",
        r"génère un document markdown de \1"
    ),

    # ── GUIDE I2I ────────────────────────────────────────────────────────────
    (
        r"\benrich\s+your\s+image\s+instruction\b",
        r"enrichis ton instruction d'image"
    ),
    (
        r"\boptimize\s+your\s+image\s+instruction\b",
        r"optimise ton instruction d'image"
    ),
    (
        r"\bimprove\s+your\s+image\s+instruction\b",
        r"ameliore ton instruction d'image"
    ),
    (
        r"\brestructure\s+your\s+i2i\s+guide\b",
        r"restructure ton guide i2i"
    ),

    # ── RECHERCHE WEB (compléments non couverts par web_navigator) ───────────
    (
        r"\bI\s+need\s+to\s+search\s+(?:the\s+)?(?:web|internet|net)\b",
        r"il faut que je recherche sur le net"
    ),
    (
        r"\bI\s+need\s+to\s+check\s+(?:on\s+)?(?:the\s+)?(?:web|internet|online)\b",
        r"il faut que je vérifie sur internet"
    ),

    # ── JOURNAL DE BORD ──────────────────────────────────────────────────────
    # Consultation par date ISO
    (
        r"\bconsult\s+(?:the\s+)?journal\s+(?:for|on)\s+(\d{4}-\d{2}-\d{2})\b",
        r"consulte le journal du \1"
    ),
    # Consultation de la semaine
    (
        r"\bconsult\s+(?:this\s+week'?s?|the\s+week'?s?|last\s+week'?s?)\s+journal\b",
        r"consulte le journal de la semaine"
    ),
    # Consultation par jour nommé
    (r"\bconsult\s+yesterday'?s?\s+journal\b", r"consulte le journal d'hier"),
    (r"\bconsult\s+today'?s?\s+journal\b",     r"consulte le journal d'aujourd'hui"),
    (r"\bconsult\s+monday'?s?\s+journal\b",    r"consulte le journal de lundi"),
    (r"\bconsult\s+tuesday'?s?\s+journal\b",   r"consulte le journal de mardi"),
    (r"\bconsult\s+wednesday'?s?\s+journal\b", r"consulte le journal de mercredi"),
    (r"\bconsult\s+thursday'?s?\s+journal\b",  r"consulte le journal de jeudi"),
    (r"\bconsult\s+friday'?s?\s+journal\b",    r"consulte le journal de vendredi"),
    (r"\bconsult\s+saturday'?s?\s+journal\b",  r"consulte le journal de samedi"),
    (r"\bconsult\s+sunday'?s?\s+journal\b",    r"consulte le journal de dimanche"),
    # Contexte formaté
    (
        r"\bshow\s+(?:journal\s+)?context\s+for\s+(\d{4}-\d{2}-\d{2})\b",
        r"montre le contexte du \1"
    ),
    (r"\bshow\s+(?:journal\s+)?context\s+for\s+yesterday\b", r"montre le contexte d'hier"),
    (r"\bshow\s+(?:journal\s+)?context\s+for\s+today\b",     r"montre le contexte d'aujourd'hui"),
    # Recherche journal
    (
        r"\bjournal\s+search\s+(.+)",
        r"journal recherche \1"
    ),
    # Résumés temporels
    (
        r"\bsummarize\s+(?:the\s+)?week\s+(?:of\s+)?(\d{4}-\d{2}-\d{2})\b",
        r"résume la semaine du \1"
    ),
    (
        r"\bsummarize\s+(?:the\s+)?month\s+(\d{4}-\d{2})\b",
        r"résume le mois \1"
    ),
    # Sauvegarde / ajout journal
    (
        r"\bsave\s+(?:the\s+)?conversation\s+to\s+(?:the\s+)?journal\b",
        r"sauvegarde la conversation dans le journal"
    ),
    (
        r"\badd\s+(?:the\s+)?conversation\s+to\s+(?:the\s+)?journal\b",
        r"ajoute la conversation au journal"
    ),
    # Ouverture journal par jour
    (r"\bopen\s+yesterday'?s?\s+journal\b", r"ouvre le journal d'hier"),
    (r"\bopen\s+today'?s?\s+journal\b",     r"ouvre le journal d'aujourd'hui"),
    # Affichage filtré
    (
        r"\bjournal\s+show\s+(.+)",
        r"journal affiche \1"
    ),

    # ── SOUVENIR PAR ID ──────────────────────────────────────────────────────
    (
        r"\bread\s+memory\s+(usr-[a-f0-9\-]+)\b",
        r"lis le souvenir \1"
    ),
    (
        r"\bconsult\s+memory\s+(usr-[a-f0-9\-]+)\b",
        r"consulte le souvenir \1"
    ),

    # ── ARCHIVES / CONVERSATIONS ─────────────────────────────────────────────
    (
        r"\bgo\s+read\s+(?:the\s+)?conversation\s+([^\s,\.]+(?:\.json)?)",
        r"va lire la conversation \1"
    ),
    (
        r"\bread\s+(?:the\s+)?conversation\s+([^\s,\.]+(?:\.json)?)",
        r"lis la conversation \1"
    ),
    (
        r"\bload\s+(?:the\s+)?conversation\s+([^\s,\.]+(?:\.json)?)",
        r"charge la conversation \1"
    ),
    (
        r"\bopen\s+(?:the\s+)?conversation\s+([^\s,\.]+(?:\.json)?)",
        r"ouvre la conversation \1"
    ),

    # ── RAPPEL MÉMORIEL (memory triggers temporal_parser) ───────────────────
    (
        r"\bdo\s+you\s+remember\s+(?:when\s+)?(.+)",
        r"tu te souviens de \1"
    ),
    (
        r"\bdo\s+you\s+recall\s+when\s+(.+)",
        r"tu te rappelles quand \1"
    ),
    (
        r"\bwhen\s+we\s+(?:talked|spoke|discussed)\s+about\s+(.+)",
        r"quand on a parlé de \1"
    ),
    (
        r"\bour\s+conversation\s+(?:about|on|regarding)\s+(.+)",
        r"notre conversation sur \1"
    ),
    (
        r"\bwhat\s+we\s+said\s+(?:about|on)\s+(.+)",
        r"ce qu'on a dit sur \1"
    ),
    (
        r"\bremind\s+me\s+(?:of\s+)?what\s+(.+)",
        r"rappelle-moi ce que \1"
    ),

    # ── EXPRESSIONS TEMPORELLES (pour contextual recall) ────────────────────
    (r"\b(\d+)\s+days?\s+ago\b",           r"il y a \1 jours"),
    (r"\b(\d+)\s+weeks?\s+ago\b",          r"il y a \1 semaines"),
    (r"\b(\d+)\s+months?\s+ago\b",         r"il y a \1 mois"),
    (r"\bthe\s+day\s+before\s+yesterday\b", r"avant-hier"),
    (r"\blast\s+week\b",                    r"la semaine dernière"),
    (r"\blast\s+month\b",                   r"le mois dernier"),

    # ── ÉDITEUR DOCS (compléments) ───────────────────────────────────────────
    (
        r"\bdraft\s+a\s+\.md\s+(?:on|about)\s+(.+)",
        r"rédige un .md sur \1"
    ),
    (
        r"\bmake\s+(?:me\s+)?a\s+markdown\s+file\s+for\s+(.+)",
        r"fais-moi un fichier markdown pour \1"
    ),
    (
        r"\bwrite\s+a\s+\.md\s+(?:that|which)\s+(.+)",
        r"écris un .md qui \1"
    ),

    # ── EGO ──────────────────────────────────────────────────────────────────
    # "this is now a part of me: ..."  →  phrase ego canonique FR
    (
        r"\bthis\s+is\s+now\s+a\s+part\s+of\s+me\s*[:\-]\s*(.+)",
        r"ceci est une part de moi maintenant: \1"
    ),
    # "I need to restructure my ego now"
    (
        r"\bI\s+need\s+to\s+restructure\s+my\s+ego\s+now\b",
        r"il faut que je restructure mon ego maintenant"
    ),
]

# Compilation des patterns pour performance
_COMPILED_RULES: List[Tuple[re.Pattern, str]] = [
    (re.compile(pattern, re.IGNORECASE), replacement)
    for pattern, replacement in _RULES
]


def normalize_magic_phrases(text: str) -> str:
    """
    Remplace les phrases magiques EN par leur équivalent FR canonique.

    Traite chaque ligne séparément pour ne pas confondre le payload
    multi-ligne avec la phrase déclencheuse.

    Args:
        text: Message utilisateur ou réponse IA brute.

    Returns:
        Texte avec phrases EN remplacées en FR (payload inchangé).
    """
    if not text:
        return text

    lines = text.split('\n')
    result = []
    for line in lines:
        normalized = line
        for pattern, replacement in _COMPILED_RULES:
            new_line = pattern.sub(replacement, normalized)
            if new_line != normalized:
                print(f"[NORMALIZER] EN→FR: «{normalized.strip()}» → «{new_line.strip()}»")
                normalized = new_line
                break  # Une seule règle par ligne (évite doubles substitutions)
        result.append(normalized)

    return '\n'.join(result)
