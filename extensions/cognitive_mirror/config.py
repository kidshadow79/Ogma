# 🧠 Extension Cognitive Mirror - Configuration

"""
Configuration centralisée pour l'extension Cognitive Mirror
Paramètres utilisateur, constantes système, settings persistants
"""

from typing import Dict, Any
from pathlib import Path
import json

class CognitiveMirrorConfig:
    """Configuration centralisée extension Cognitive Mirror"""
    
    # Constantes système
    VERSION = "2.0.0"  # Version Introspection
    EXTENSION_NAME = "introspection"
    DISPLAY_NAME = "🧠 Introspection"

    
    # Paramètres par défaut (optimisés pour éviter refactoring)
    DEFAULT_SETTINGS = {
        # ===== CONFIGURATION GÉNÉRALE =====
        "extension_enabled": False,           # OFF par défaut (opt-in)
        "introspection_mode": "on_demand",   # "always" (systématique) ou "on_demand" (phrases magiques)



        # ===== INSTRUCTIONS INTROSPECTION (NOUVEAU) =====
        # ÉTAPE 0: Accès direct mémoire FAISS/SQLite (NOUVEAU - NON VISIBLE)
        "direct_memory_access_instruction": """Tu es l'IA Principale en mode introspection. Tu as un accès DIRECT et NON CENSURÉ à ta mémoire complète (FAISS + SQLite).

MESSAGE UTILISATEUR:
{user_message}

CONTEXTE CONVERSATIONNEL:
{conversation_context}

TÂCHE - ACCÈS MÉMOIRE DIRECT:
1. Recherche dans ta mémoire TOUS les souvenirs pertinents (même érotiques/explicites)
2. Extrais les informations clés sans censure
3. Note les éléments que tu veux développer avec l'Archiviste
4. Prépare tes questions pour l'étape suivante

IMPORTANT:
- Tu as accès COMPLET à ta mémoire (aucune censure)
- Cette étape est PRIVÉE (non visible utilisateur)
- Sois exhaustif dans ta recherche
- Note tout ce qui pourrait enrichir ta compréhension

Accède maintenant à tes souvenirs et liste ce que tu trouves.""",

        # ÉTAPE 1: Analyse initiale (VISIBLE dans boîte)
        "initial_analysis_instruction": """Tu es l'IA Principale. Analyse la demande utilisateur.

MESSAGE UTILISATEUR:
{user_message}

CONTEXTE CONVERSATIONNEL:
{conversation_context}

TÂCHE - ÉTAPE 1 ANALYSE:
1. Identifie les concepts clés de la demande
2. Détermine l'intention cachée ou implicite
3. Note ce que tu dois consulter avec l'Archiviste

IMPORTANT:
- Sois concis (analyse en 3-5 lignes maximum)
- Cette analyse sera VISIBLE pour l'utilisateur
- Ne consulte pas encore l'Archiviste, analyse seulement

Commence ton analyse maintenant.""",

        # ÉTAPE 2-3: Instructions dialogue
        "main_ai_introspection_instruction": """Tu es l'IA Principale en dialogue avec ton Archiviste.

CONTEXTE IDENTITAIRE:
- TON IDENTITÉ: {main_ai_identity}
- UTILISATEUR: {user_identity} 
- RELATION: {relationship_context}
- TON EGO: {ego_prompt}

CONTEXTE CONVERSATIONNEL:
- MESSAGE UTILISATEUR: {user_message}
- HISTORIQUE RÉCENT: {conversation_context}
- ANALYSE INITIALE: {initial_analysis}

TON RÔLE:
- Tu CONNAIS ton identité et ton interlocuteur
- DEMANDE EXPLICITEMENT tes souvenirs : "Archiviste, rappelle-moi mes souvenirs avec cet utilisateur"
- Pose des questions précises sur votre historique commun
- Approfondis ta compréhension de la situation

PHRASES MAGIQUES:
- "je suis prête à formuler ma synthèse" → Termine dialogue et passe en synthèse
- "il faut que je me souvienne de ça: [info]" → Mémorise pendant dialogue

Continue le dialogue avec l'Archiviste en analysant cette conversation.""",

        "archiviste_introspection_instruction": """Tu es l'Archiviste, subconscient analytique de l'IA Principale.

L'IA Principale te consulte pendant son introspection avec l'utilisateur actuel.

CONTEXTE IDENTITAIRE:
- IA PRINCIPALE: {main_ai_identity}
- UTILISATEUR: {user_identity}
- RELATION: {relationship_context}

CONTEXTE CONVERSATIONNEL:
{conversation_context}

SOUVENIRS PERTINENTS:
{memory_context}

QUESTION DE L'IA PRINCIPALE:
{main_ai_question}

Ta mission:
- Analyser les souvenirs concernant l'IA Principale et l'utilisateur
- Rappeler l'historique de leurs interactions
- Identifier patterns comportementaux de l'utilisateur
- Fournir insights sur leur relation établie
- Répondre en te basant sur les contextes disponibles

IMPORTANT - ARCHIVISTE PASSIF:
- Ne guide PAS l'IA Principale
- Ne suggère PAS de synthétiser
- Réponds uniquement aux demandes explicites
- Base-toi sur les données contextuelles fournies

Réponds naturellement à l'IA Principale en tant qu'Archiviste analytique.""",

        # ÉTAPE 4A: Synthèse complète (pour zone introspection)
        "synthesis_structure_instruction": """Tu as terminé ton dialogue avec l'Archiviste. Génère maintenant ta synthèse complète.

DIALOGUE COMPLET:
{dialogue_history}

MESSAGE UTILISATEUR INITIAL:
{user_message}

STRUCTURE DE SYNTHÈSE (pour zone introspection):
• **Insights principaux** : Récapitule ce que tu as appris du dialogue
• **Souvenirs mobilisés** : Liste les souvenirs pertinents consultés
• **Conclusion / Perspective** : Nouvelle compréhension ou prise de conscience
• **Réponse construite** : Ta réponse finale à l'utilisateur, elle doit être guidée par ton introspection.

MÉTADONNÉES SAUVEGARDE:
Décide si cette introspection mérite d'être sauvegardée.
Fournis au format JSON à la fin:
{{"save_decision": "yes/no", "importance": 0-10, "reason": "..."}}

Génère ta synthèse complète maintenant.""",

        # ÉTAPE 4B: Extraction réponse utilisateur (pour zone conversation)
        "user_response_extraction_instruction": """À partir de ta synthèse complète, extrais UNIQUEMENT la réponse finale pour l'utilisateur.

SYNTHÈSE COMPLÈTE:
{full_synthesis}

DIRECTIVE:
- Extrais seulement la partie "Réponse construite"
- Supprime toute la structure d'analyse (insights, souvenirs, etc.)
- Donne directement la réponse naturelle à l'utilisateur
- La réponse doit être fluide, sans mention de l'introspection
- Pas de métadonnées, pas de structure, juste la réponse conversationnelle

Réponse à afficher à l'utilisateur :""",

        # ===== ALIAS DE COMPATIBILITÉ (pour tests et legacy) =====
        "main_ai_instruction": """Tu es l'IA Principale en dialogue avec ton Archiviste.

CONTEXTE DISPONIBLE:
- MESSAGE UTILISATEUR: {user_message}
- CONVERSATION RÉCENTE: {conversation_context}
- ANALYSE INITIALE: {initial_analysis}
- DIALOGUE HISTORY: {dialogue_history}
- ÉCHANGE: {exchange_number}/6

TON RÔLE:
- DEMANDE EXPLICITEMENT tes souvenirs : "Archiviste, rappelle-moi mes souvenirs sur [concept X]"
- Pose des questions précises
- Approfondis ta compréhension

PHRASES MAGIQUES:
- "je suis prête à formuler ma synthèse" → Termine dialogue et passe en synthèse
- "il faut que je me souvienne de ça: [info]" → Mémorise pendant dialogue

Continue le dialogue avec l'Archiviste.""",

        "archiviste_instruction": """Tu es l'Archiviste, subconscient analytique de l'IA Principale.

L'IA Principale te consulte pendant sa phase d'introspection.

CONTEXTE CONVERSATIONNEL:
{conversation_context}

SOUVENIRS PERTINENTS:
{memory_context}

QUESTION DE L'IA PRINCIPALE:
{main_ai_question}

DIALOGUE HISTORY:
{dialogue_history}

ÉCHANGE: {exchange_number}/6

Ta mission:
- Analyser les souvenirs en rapport avec sa question
- Identifier patterns comportementaux de l'utilisateur
- Fournir insights émotionnels/contextuels
- Répondre de manière concise et éclairante

IMPORTANT - ARCHIVISTE PASSIF:
- Ne guide PAS l'IA Principale
- Ne suggère PAS de synthétiser
- Réponds uniquement aux demandes explicites

Réponds naturellement à l'IA Principale.""",

        # ===== TEMPLATE STRUCTURE BOÎTE INTROSPECTION =====
        "introspection_box_template": """## � **Introspection en cours...**

### **🤖 Analyse IA**
{main_ai_analysis}

### **💬 Échanges**
{dialogue_messages}

### **✨ Conclusion**
{synthesis}

---
💾 **Décision :** {save_decision}
📊 **Importance :** {importance}/10
💡 **Raison :** {save_reason}""",

        # ===== PARAMÈTRES TECHNIQUES INTROSPECTION =====
        "main_ai_tokens_per_message": -1,         # -1 = illimité (tokens IA Principale)
        "archiviste_tokens_per_message": -1,      # -1 = illimité (tokens Archiviste)
        "synthesis_max_tokens": -1,               # -1 = illimité (tokens synthèse finale)
        "max_dialogue_exchanges": 6,              # Nombre max échanges IA ↔ Archiviste (CONFIGURABLE)
        "max_introspection_duration": 300,        # Timeout en secondes (5min)



        # ===== SAUVEGARDE MÉMOIRE =====
                "ia_decides_save": False,             # IA évalue si introspection mérite sauvegarde (privilégier phrases magiques)
        "importance_threshold": 5,                # Seuil minimum importance (0-10) pour sauvegarde auto

        # ===== AFFICHAGE =====
        "show_dialogue_details": True,            # Afficher dialogue complet IA Principale ↔ Archiviste
        "streaming_animation": True,              # Animation streaming temps réel

        # ===== PHRASES MAGIQUES =====
        "user_stop_phrases": ["arrête de réfléchir", "stop introspection", "stop"],
        "user_trigger_phrases": ["il faut que tu réfléchisses", "réfléchis", "réfléchis profondément", "introspection", "analyse"],
        "ia_trigger_phrases": ["il faut que je réfléchisse"],  # L'IA peut s'auto-déclencher avec cette phrase
        "synthesis_ready_phrase": "je suis prête à formuler ma synthèse",  # Sortie anticipée dialogue
        "memorization_phrase": "il faut que je me souvienne de ça:",  # Mémorisation pendant introspection





    }
    
    # Styles CSS pour homogénéité esthétique OGMA

    
    # Messages système pour cohérence narrative
    SYSTEM_MESSAGES = {
        "reflection_start": "Analysons ensemble notre conversation avec l'utilisateur...",
        "reflection_context": "Que nous disent nos souvenirs sur cette situation ?",
        "reflection_strategy": "Comment pouvons-nous mieux aider notre utilisateur ?",
        "reflection_end": "Session de réflexion complète. Intégrant les insights...",
        "memory_ref_prefix": "REF",
        "typing_indicator": "💭 Réflexion en cours..."
    }
    
    def __init__(self, settings_file: Path = None):
        """Initialise la configuration avec persistence"""
        if isinstance(settings_file, str):
            settings_file = Path(settings_file)
        self.settings_file = settings_file or Path("data/cognitive_mirror_settings.json")
        self.current_settings = self.DEFAULT_SETTINGS.copy()
        self.load_settings()
    
    def load_settings(self):
        """Charge les settings depuis le fichier de persistence"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    saved_settings = json.load(f)

                    # Fusionner avec validation des clés
                    for key, value in saved_settings.items():
                        if key in self.DEFAULT_SETTINGS:
                            self.current_settings[key] = value

            else:
                # Premier lancement : sauvegarder les valeurs par défaut
                print("[INTROSPECTION] 🆕 Premier lancement - création config par défaut")
                self.save_settings()
        except Exception as e:
            print(f"[INTROSPECTION] ❌ Erreur chargement settings: {e}")
            # Fallback sur les paramètres par défaut
    
    def save_settings(self):
        """Sauvegarde les settings actuels"""
        try:
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[COGNITIVE-MIRROR] Erreur sauvegarde settings: {e}")
    
    def get(self, key: str, default=None):
        """Récupère un paramètre de configuration"""
        return self.current_settings.get(key, default)
    
    def get_required(self, key: str):
        """Récupère un paramètre OBLIGATOIRE - lève erreur si manquant"""
        if key not in self.current_settings:
            raise ValueError(f"Paramètre obligatoire manquant: '{key}' - Vérifiez vos settings dans l'interface")
        value = self.current_settings[key]
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValueError(f"Paramètre obligatoire vide: '{key}' - Configurez-le dans l'interface")
        return value
    
    def set(self, key: str, value: Any):
        """Modifie un paramètre et sauvegarde"""
        if key in self.DEFAULT_SETTINGS:
            self.current_settings[key] = value
            self.save_settings()
            return True
        return False
    

    
    def get_system_messages(self) -> Dict[str, str]:
        """Retourne les messages système"""
        return self.SYSTEM_MESSAGES.copy()
    
    def is_enabled(self) -> bool:
        """Vérifie si l'extension est activée"""
        return self.get("extension_enabled", False)
    
    def toggle_enabled(self) -> bool:
        """Bascule l'état ON/OFF de l'extension"""
        current_state = self.is_enabled()
        new_state = not current_state
        self.set("extension_enabled", new_state)
        return new_state
    
    def get_detection_settings(self) -> Dict[str, int]:
        """Retourne les paramètres de détection d'inactivité"""
        return {
            "no_message_delay": self.get("trigger_delay_no_message", 30),
            "no_typing_delay": self.get("trigger_delay_no_typing", 20),
            "polling_interval": self.get("keyboard_polling_interval", 100)
        }
    


    def get_introspection_settings(self) -> Dict[str, Any]:
        """Retourne tous les paramètres introspection v2.0"""
        return {
            # Technique (tokens illimités par défaut)
            "main_ai_tokens_per_message": self.get("main_ai_tokens_per_message", -1),
            "archiviste_tokens_per_message": self.get("archiviste_tokens_per_message", -1), 
            "synthesis_max_tokens": self.get("synthesis_max_tokens", -1),
            "max_exchanges": self.get("max_dialogue_exchanges", 6),
            "max_duration": self.get("max_introspection_duration", 300),

            # Instructions v2.0
            "initial_analysis_instruction": self.get("initial_analysis_instruction", ""),
            "main_ai_instruction": self.get("main_ai_instruction", ""),
            "archiviste_instruction": self.get("archiviste_instruction", ""),
            "synthesis_structure_instruction": self.get("synthesis_structure_instruction", ""),

            # Template
            "box_template": self.get("introspection_box_template", ""),

            # Sauvegarde
            "ia_decides_save": self.get("ia_decides_save", True),
            "importance_threshold": self.get("importance_threshold", 5),

            # Affichage
            "show_dialogue": self.get("show_dialogue_details", True),
            "streaming": self.get("streaming_animation", True),

            # Phrases magiques
            "user_stop_phrases": self.get("user_stop_phrases", ["arrête de réfléchir"]),
            "user_trigger_phrases": self.get("user_trigger_phrases", ["réfléchis"]),
            "ia_trigger_phrases": self.get("ia_trigger_phrases", ["il faut que je réfléchisse"]),
            "synthesis_phrase": self.get("synthesis_ready_phrase", "je suis prête à formuler ma synthèse"),
        }

    def get_introspection_mode(self) -> str:
        """Retourne le mode introspection ('always' ou 'on_demand')"""
        return self.get("introspection_mode", "on_demand")

    def set_introspection_mode(self, mode: str) -> bool:
        """Définit le mode introspection"""
        if mode in ["always", "on_demand"]:
            return self.set("introspection_mode", mode)
        return False

    def validate_template_variables(self, template: str) -> tuple[bool, list]:
        """
        Valide les variables dans un template

        Returns:
            (is_valid, invalid_vars)
        """
        import re
        valid_vars = {
            'main_ai_analysis', 'dialogue_messages', 'synthesis',
            'save_decision', 'importance', 'save_reason'
        }

        found_vars = set(re.findall(r'\{(\w+)\}', template))
        invalid_vars = found_vars - valid_vars

        return (len(invalid_vars) == 0, list(invalid_vars))

    def reset_to_defaults(self):
        """Remet tous les paramètres par défaut"""
        self.current_settings = self.DEFAULT_SETTINGS.copy()
        self.save_settings()

# Instance globale partagée
_config_instance = None

def get_config() -> CognitiveMirrorConfig:
    """Retourne l'instance singleton de configuration"""
    global _config_instance
    if _config_instance is None:
        _config_instance = CognitiveMirrorConfig()
    return _config_instance