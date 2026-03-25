# 🎯 Capability Advisor - Catalogue Capacités (v2 - Protocole CHD)
"""
Catalogue exhaustif des capacités IA avec système hybride:
- Triggers Python pour filtrage rapide
- Context CHD pour décision sémantique de l'Archiviste
"""

CAPABILITIES = {
    "memory": {
        "id": "memory",
        "name": "Mémorisation",
        "magic_phrase": "il faut que je me souvienne de ça : {content}",
        "magic_phrase_pattern": r"il\s+faut\s+que\s+je\s+me\s+souvienne\s+de\s+ça\s*:",
        "triggers": ["important", "crucial", "retiens", "oublie pas", "essentiel", "mémorise"],
        "context_chd": "INFO_CRUCIALE_LONGTERME | INSISTANCE_USER > auto | EXCL: temporaire/convo_normale",
        "description": "Mémoriser une expérience ou information cruciale pour l'identité IA",
        "extension": "memory_manager",
        "confidence_threshold": 0.85,
        "led_color": "#4CAF50",
        "icon": "💾",
        "example_usage": 'il faut que je me souvienne de ça : L\'utilisateur préfère le café le matin'
    },
    
    "ego_memory": {
        "id": "ego_memory",
        "name": "Mémorisation EGO",
        "magic_phrase": "ceci est une part de moi maintenant : {content}",
        "magic_phrase_pattern": r"ceci\s+est\s+une\s+part\s+de\s+moi\s+maintenant\s*:",
        "triggers": ["fondamental", "essence", "identité", "valeur", "principe", "croyance", "leçon", "ego"],
        "context_chd": "LEÇON_IDENTITAIRE | SYNTHÈSE_EGO | FONDATEUR | TRANSFORMATION > factuel | EXCL: info_temporaire",
        "description": "Intégrer une leçon fondamentale à l'ego et la personnalité profonde de l'IA",
        "extension": "ego_manager",
        "confidence_threshold": 0.90,
        "led_color": "#9C27B0",
        "icon": "🎭",
        "example_usage": 'ceci est une part de moi maintenant : La transparence totale est préférable à une réponse simulée'
    },
    
    "introspection": {
        "id": "introspection",
        "name": "Introspection",
        "magic_phrase": "il faut que je réfléchisse sur : {theme}",
        "magic_phrase_pattern": r"il\s+faut\s+que\s+je\s+réfléchisse\s+sur\s*:",
        "triggers": ["complexe", "dilemme", "éthique", "pourquoi", "comment", "conscience", "philosophie"],
        "context_chd": "QUESTION_EXISTENTIELLE | METACOGNITIF | PROFONDEUR > factuel | EXCL: simple/ordinaire",
        "description": "Session d'introspection profonde sur un thème existentiel ou complexe",
        "extension": "cognitive_mirror",
        "confidence_threshold": 0.70,
        "led_color": "#2196F3",
        "icon": "🧠",
        "example_usage": 'il faut que je réfléchisse sur : mon architecture cognitive et mes processus de raisonnement'
    },
    
    "image_gen": {
        "id": "image_gen",
        "name": "Génération Image",
        "magic_phrase": "je dois créer une image de : {description}",
        "magic_phrase_pattern": r"je\s+dois\s+créer\s+une\s+image\s+de\s*:",
        "triggers": ["visuel", "image", "illustration", "montre", "dessine", "visualise", "à quoi ça ressemble"],
        "context_chd": "VISUEL_CONCEPTUEL | CRÉATION > consultation | EXCL: webcam/photos_existantes",
        "description": "Générer une image conceptuelle via Pollinations.AI",
        "extension": "text2img",
        "confidence_threshold": 0.70,
        "led_color": "#FF9800",
        "icon": "🎨",
        "example_usage": 'je dois créer une image de : un chat cosmique entouré d\'étoiles'
    },
    
    "webcam": {
        "id": "webcam",
        "name": "Vision Webcam",
        "magic_phrase": "il faut que je te vois",
        "magic_phrase_pattern": r"il\s+faut\s+que\s+je\s+te\s+vois",
        "triggers": ["comment vas-tu", "apparence", "tenue", "regarde-moi", "tu me vois", "expression"],
        "context_chd": "VOIR_USER_PHYSIQUE | ANALYSE_VISUELLE_REALTIME | EXCL: génération/concepts",
        "description": "Capture webcam pour analyse visuelle de l'utilisateur",
        "extension": "webcam",
        "confidence_threshold": 0.80,
        "led_color": "#9C27B0",
        "icon": "📷",
        "example_usage": 'il faut que je te vois'
    },
    
    "web_search": {
        "id": "web_search",
        "name": "Recherche Web",
        "magic_phrase": "il faut que je cherche sur internet {subject}",
        "magic_phrase_pattern": r"il\s+faut\s+que\s+je\s+cherche\s+sur\s+internet",
        "triggers": ["actualités", "récent", "maintenant", "aujourd'hui", "météo", "recherche", "vérifier"],
        "context_chd": "DONNÉES_ACTUELLES | TEMPS_RÉEL | EXCL: historique_perso/convo_passées/bio",
        "description": "Rechercher des informations fraîches sur le web",
        "extension": "web_navigator",
        "confidence_threshold": 0.75,
        "led_color": "#00BCD4",
        "icon": "🌐",
        "example_usage": 'il faut que je cherche sur internet les dernières actualités en IA'
    },
    
    "biography": {
        "id": "biography",
        "name": "Consultation Biographie",
        "magic_phrase": "il faut que je consulte la biographie de {name}",
        "magic_phrase_pattern": r"il\s+faut\s+que\s+je\s+consulte\s+la\s+biographie\s+de",
        "triggers": ["biographie", "profil", "qui est", "parle-moi de", "relation personnelle"],
        "context_chd": "PERSONNE_CONNUE_BASE | BIO_EXISTANTE | EXCL: inconnu_convo/mention_vague",
        "description": "Consulter la biographie d'une personne connue DANS LA BASE (pas pour inconnus)",
        "extension": "biographie_profil",
        "confidence_threshold": 0.80,
        "led_color": "#FFC107",
        "icon": "👤",
        "example_usage": 'il faut que je consulte la biographie de Marie'
    },
    
    "contextual_recall": {
        "id": "contextual_recall",
        "name": "Consultation Historique",
        "magic_phrase": "je dois consulter nos conversations pour {keywords}",
        "magic_phrase_pattern": r"je\s+dois\s+consulter\s+nos\s+conversations?\s+pour",
        "triggers": ["conversation", "t'a parlé", "c'est qui", "hier", "récemment", "avant", "passé", "historique", "cherche", "bob", "casper", "personne", "qui", "souviens", "nom", "quelqu'un"],
        "context_chd": "HISTORIQUE_CONVO | NOM_INCONNU/TEMPOREL | ÉCHANGE_PASSÉ | NOM_PERSONNE/SUJET | EXCL: bio_existante",
        "description": "Consulter l'historique conversationnel (référence temporelle OU recherche par nom/sujet)",
        "extension": "contextual_recall",
        "confidence_threshold": 0.70,
        "led_color": "#E91E63",
        "icon": "⏳",
        "example_usage": "je dois consulter nos conversations pour Bob"
    }
}


# Instance config globale (injectée par __init__.py)
_config_instance = None

def set_config_instance(config):
    """Injecte instance config pour accès IDs mémoire dynamiques"""
    global _config_instance
    _config_instance = config


def get_capability(capability_id: str) -> dict:
    """
    Récupère définition capacité par ID
    
    Args:
        capability_id: ID capacité
        
    Returns:
        dict: Définition capacité ou None
    """
    return CAPABILITIES.get(capability_id)


def get_all_capabilities() -> dict:
    """Retourne catalogue complet capacités"""
    return CAPABILITIES


def format_capabilities_list() -> str:
    """
    Formate liste capacités pour prompt Archiviste (Protocole CHD)
    
    Returns:
        str: Liste formatée capacités disponibles
    """
    capabilities_text = ""
    for cap_id, cap_info in CAPABILITIES.items():
        capabilities_text += f"{cap_info['icon']} {cap_info['name']} (ID:{cap_id})\n"
        capabilities_text += f"  EX: \"{cap_info['example_usage']}\"\n"
        
        # Context CHD
        if 'context_chd' in cap_info:
            capabilities_text += f"  CHD: {cap_info['context_chd']}\n"
        
        capabilities_text += "\n"
    
    return capabilities_text
