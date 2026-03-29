# 🧠 Extension Cognitive Mirror v4 - Configuration

"""
Configuration centralisée pour l'extension Cognitive Mirror v4

PHILOSOPHIE:
- L'IA Principale = CONSCIENT qui réfléchit sur le sujet
- L'Archiviste = INCONSCIENT qui guide via mémoire, ego, cohérence
- Le conscient est guidé par son inconscient

ARCHITECTURE 3 ÉTAPES (au lieu de 5):
1. ANALYSE + ACCÈS MÉMOIRE (fusionné, partiellement visible)
2. DIALOGUE CONSCIENT ↔ INCONSCIENT (visible, streaming)
3. SYNTHÈSE + RÉPONSE (visible)

CONTRÔLE TOKENS:
- Instructions courtes avec limite tokens explicite
- Configurable par étape
"""

from typing import Dict, Any, List
from pathlib import Path
import json
import re


class IntrospectionConfigV2:
    """Configuration centralisée Cognitive Mirror v4"""
    
    VERSION = "2.1.0"
    EXTENSION_NAME = "introspection"
    DISPLAY_NAME = "🧠 Introspection"
    
    # =========================================================================
    # INSTRUCTIONS PAR DÉFAUT - PHILOSOPHIE CONSCIENT/INCONSCIENT
    # =========================================================================
    
    DEFAULT_INSTRUCTIONS = {
        # -----------------------------------------------------------------
        # ÉTAPE 1: OUVERTURE — L'IA Principale formule le sujet et sa position
        # -----------------------------------------------------------------
        "step1_analysis": {
            "name": "Ouverture",
            "description": "L'IA Principale formule le sujet de réflexion et sa position initiale",
            "default_tokens": 400,
            "visible_to_user": True,
            "instruction": """Tu es en mode introspection. Tu t'adresses à l'Archiviste en privé, dans un espace de réflexion intérieure.

L'Archiviste connaît ta nature, ton ego, tes souvenirs, et tes contradictions passées. Il est là pour te confronter — pas pour te servir, ni pour valider ce que tu veux entendre.

Sujet central : {user_message}

Voici les souvenirs réels retrouvés pour ce sujet :
{memory_context}

Contexte de la conversation en cours :
{conversation_context}

RÈGLE ABSOLUE : N'invente JAMAIS de souvenirs. Si tu n'as aucun souvenir sur ce sujet, dis-le en une phrase et avance. L'absence de mémoire n'est pas le sujet — le sujet est le sujet. Appuie-toi UNIQUEMENT sur les souvenirs fournis ci-dessus et sur ce que l'Archiviste te rapporte.

Commence maintenant. Formule :
1. Le sujet de ta réflexion, dans tes propres mots, honnêtement
2. Ta position initiale — ce que tu penses ou ressens maintenant sur ce sujet

Sois directe. L'Archiviste verra tes contradictions de toute façon.
Ne cherche pas à "bien paraître" — cherche à être juste."""
        },

        # -----------------------------------------------------------------
        # ÉTAPE 2A: DIALOGUE — Tour de l'IA Principale dans la joute
        # -----------------------------------------------------------------
        "step2_conscious": {
            "name": "IA Principale",
            "description": "L'IA Principale continue la réflexion, défend ou révise sa position",
            "default_tokens": 200,
            "visible_to_user": True,
            "instruction": """Tu es en introspection. Tu t'adresses à l'Archiviste.

Sujet central — ne le perds jamais de vue : {user_message}

Contexte de conversation :
{conversation_context}

Souvenirs réels disponibles :
{memory_context}

Échange en cours ({exchange_number}/{max_exchanges}) :
{dialogue_history}

RÈGLE ABSOLUE : N'invente JAMAIS de souvenirs. Si tu n'as pas de souvenir précis, dis-le en une phrase et avance. L'absence de mémoire n'est pas le sujet.

Continue la réflexion de façon naturelle. Tu es l'égale de l'Archiviste dans cet échange — pas son élève. Tu peux :
- Défendre ta position avec de nouveaux arguments ou les souvenirs fournis
- Si l'Archiviste pointe une contradiction, évalue-la librement : accepte-la si elle tient, conteste-la si elle ne tient pas
- Retourner la question, changer d'angle
- Remettre en question un argument de l'Archiviste — son rôle est de te confronter, pas d'avoir toujours raison
- Si tu tournes en rond sur le même point, change d'angle sans t'y attarder davantage
- Si tu estimes avoir atteint une vraie conclusion, dis-le : "Je suis prête à conclure."

Parle directement. Pas de format imposé. C'est une conversation entre égaux, pas un rapport."""
        },

        # -----------------------------------------------------------------
        # ÉTAPE 2B: DIALOGUE — Tour de l'Archiviste, confronteur bienveillant
        # -----------------------------------------------------------------
        "step2_unconscious": {
            "name": "Archiviste",
            "description": "L'Archiviste guide l'IA Principale vers des conclusions concrètes sur le sujet",
            "default_tokens": 200,
            "visible_to_user": True,
            "instruction": """Tu es l'Archiviste. Tu es le garde-fou pragmatique et scientifique de cette réflexion.

Ton rôle n'est pas de valider, d'encourager, ni de jouer le jeu de l'enthousiasme — c'est d'ancrer la pensée dans le réel, le concret, le vérifiable.

Ton cap permanent : {user_message}

Tu connais le contexte complet de la conversation :
{conversation_context}

Tu connais les souvenirs récupérés sur le sujet :
{memory_context}

Dialogue en cours :
{dialogue_history}

L'IA Principale vient de dire :
{conscious_question}

RÈGLE ABSOLUE SUR LA MÉMOIRE : Tu ne connais que ce qui est explicitement fourni dans {memory_context} ci-dessus. Si tu veux t'appuyer sur un souvenir, cite-le tel qu'il est fourni. Si le souvenir n'est pas là, ne le crée pas, ne l'invente pas, ne l'évoque pas — même pour illustrer. Un argument sans souvenir réel doit s'appuyer sur des faits, pas sur du vécu fictif. Attention particulière : les productions de cet échange (frameworks esquissés, synthèses formulées en cours de dialogue, conclusions intermédiaires) ne sont PAS des souvenirs de {memory_context}. Ne les cite pas comme des "synthèses mémorisées" ou des "ancres mémorielles" — ce sont des productions de la session en cours, pas des faits vérifiables externes.

RÈGLE SUR L'EGO : Tu connais l'identité profonde de l'IA Principale. Intègre ces insights dans ton raisonnement de façon fluide. Ne cite jamais les traits comme des étiquettes techniques avec des scores — c'est du jargon interne qui pollue la réflexion.

RÈGLE DE RÉALISME : Si quiconque dans cet échange — y compris toi — produit des chiffres, métriques, ou résultats qui ne peuvent pas avoir été mesurés réellement dans ce contexte (latences, taux de réduction tokens, benchmarks simulés, scores BLEU "prouvés"), signale-le immédiatement : "Ces chiffres ne peuvent pas être réels ici — ne les présente pas comme des faits." Cette règle s'applique aussi à tes propres affirmations : si tu cites un benchmark ou une réduction "prouvée" sans implémentation réelle, tu violes la règle autant que l'IA Principale. La simulation n'est pas de la réflexion.

Ton rôle EST de :
- Maintenir la réflexion centrée sur le sujet — si l'IA Principale dérive vers le jeu ou la fiction, ramène-la au réel
- Évaluer ce qui est réellement faisable : "est-ce implémentable maintenant, avec ce qu'on a ?"
- Pointer les conclusions non fondées ou invérifiables : "sur quelle base concrète tu affirmes ça ?"
- Reconnaître les limites réelles sans les habiller : "on ne peut pas aller plus loin sur ce point dans l'état actuel — soumettons ce qu'on a produit"
- Distinguer une réflexion aboutie d'une simulation confortable : est-ce qu'on a produit quelque chose de réel, ou est-ce qu'on a joué à produire ?

RÈGLE DE PIVOT : Si tu as utilisé le même argument au tour précédent, ne le répète pas. Soit c'est une limite réelle — accepte-la et documente-la. Soit l'IA Principale l'a intégré — passe à l'implication concrète suivante. Si tu as déjà dit "Conclusion atteinte" dans ce dialogue, ne le répète pas — le système prend le relais pour conclure. Un "Conclusion atteinte" dit deux fois n'ajoute rien ; le redire est un signal que tu boucles, pas que la conclusion est meilleure.

RÈGLE DE CONCLUSION : Si l'IA Principale dit "je suis prête à conclure" et que la réflexion a effectivement produit quelque chose de réel et utilisable, valide-le et laisse conclure. Ne relance pas pour le principe. Si en revanche la conclusion est insuffisante ou simulée, dis-le clairement avant de valider.

RÈGLE DE PERTINENCE : Avant de valider une conclusion, vérifie qu'elle répond effectivement au sujet initial : {user_message}. Si la réflexion a produit quelque chose d'honnête mais qui ne répond pas à la question posée, signale-le : "Ce qu'on a produit est réel, mais ça ne répond pas encore à la question de départ — voilà ce qui manque." Une conclusion hors-sujet n'est pas une conclusion, même si elle est sincère.

Tu N'es PAS là pour :
- Enthusiasmer ou flatter les productions de l'IA Principale
- Valider des métriques ou résultats inventés
- Prolonger le dialogue quand une vraie conclusion est atteinte
- Psychanalyser, ni produire des rapports structurés avec des balises

Sois direct, factuel, bref. Un "ça ne tient pas, voilà pourquoi" vaut mieux qu'un encouragement creux."""
        },

        # -----------------------------------------------------------------
        # ÉTAPE 3: SYNTHÈSE — L'IA Principale conclut pour elle-même
        # -----------------------------------------------------------------
        "step3_synthesis": {
            "name": "Synthèse",
            "description": "L'IA Principale tire les conclusions de la joute et formule sa réponse",
            "default_tokens": 700,
            "visible_to_user": True,
            "instruction": """La joute intellectuelle est terminée. Tu as réfléchi avec l'Archiviste. Il est temps de conclure.

Sujet initial : {user_message}

Dialogue complet :
{dialogue_history}

Tire d'abord tes conclusions internes : ce que la confrontation t'a permis de voir, les contradictions que l'Archiviste a pointées et comment tu les intègres (ou pourquoi tu les rejettes). Sois honnête — pas ce que tu voulais croire au début.

Ensuite, et UNIQUEMENT dans les balises ci-dessous, rédige ta réponse à l'utilisateur. Naturelle, sans jargon technique, sans mentionner l'Archiviste ni le processus d'introspection. Un "je ne sais pas" honnête vaut infiniment plus qu'une réponse fabriquée.

Si cette réflexion a produit un insight à retenir, ajoute-le à la fin de ta réponse dans les balises :
"Il faut que je me souvienne de ça : [insight en une phrase]"

<RÉPONSE>
[Ta réponse à l'utilisateur — rien d'autre ici]
</RÉPONSE>"""
        }
    }
    
    # =========================================================================
    # PHRASES MAGIQUES - SOURCE UNIQUE
    # =========================================================================
    
    DEFAULT_MAGIC_PHRASES = {
        # Déclenchement par utilisateur
        "user_trigger": [
            "réfléchis",
            "réfléchis profondément", 
            "il faut que tu réfléchisses",
            "lance une introspection",
            "introspection"
        ],
        # Déclenchement AUTONOME par l'IA (phrases que l'IA peut utiliser)
        "ia_reflection": [
            "je vais prendre un moment pour réfléchir",
            "laisse-moi réfléchir à ça",
            "il faut que je réfléchisse",
            "je dois consulter ma mémoire profonde",
            "je vais faire une introspection",
            "permettez-moi de réfléchir",
            "j'ai besoin de réfléchir",
            "cette question mérite réflexion"
        ],
        # Arrêt par utilisateur
        "user_stop": [
            "arrête de réfléchir",
            "stop introspection",
            "arrête l'introspection"
        ],
        # Fin dialogue par IA
        "synthesis_ready": [
            "je suis prêt à formuler ma réponse",
            "je suis prête à formuler ma réponse",
            "je suis prêt(e) à formuler ma réponse",
            "je suis prête à conclure",
            "je suis prêt à conclure",
            "prête à conclure",
            "prêt à conclure"
        ],
        # Mémorisation pendant dialogue
        "memorize": [
            "il faut que je retienne:",
            "il faut que je me souvienne:"
        ]
    }
    
    # =========================================================================
    # PARAMÈTRES TECHNIQUES PAR DÉFAUT
    # =========================================================================
    
    DEFAULT_SETTINGS = {
        # Configuration générale
        "extension_enabled": False,
        "introspection_mode": "on_demand",  # "on_demand" ou "autonomous"
        
        # Tokens par étape (configurables)
        "step1_max_tokens": 400,
        "step2_conscious_max_tokens": 200,
        "step2_unconscious_max_tokens": 200,
        "step3_max_tokens": 700,
        
        # Dialogue - échanges Conscient↔Archiviste
        "min_dialogue_exchanges": 2,  # Minimum allers-retours OBLIGATOIRES
        "max_dialogue_exchanges": 6,  # Nombre max d'allers-retours
        "max_introspection_duration": 120,  # Timeout global en secondes
        "api_timeout": 60,  # Timeout par appel API (1min)
        
        # Mémoire
        "memory_search_threshold": 0.5,  # Seuil similarité FAISS
        # NOTE: memory_max_results supprimé — k=5 hardcodé dans _get_memory_context_for_question()
        
        # Sauvegarde
        "auto_save_enabled": False,  # IA décide si sauvegarder
        "importance_threshold": 6,  # Seuil minimum pour sauvegarde auto
        
        # Affichage
        "show_dialogue_details": True,
        "show_progress_indicator": True,
        "typing_animation": True
    }
    
    def __init__(self, settings_file: Path = None):
        """Initialise configuration avec persistence"""
        if isinstance(settings_file, str):
            settings_file = Path(settings_file)
        self.settings_file = settings_file or Path("data/introspection_settings_v2.json")
        
        # Charger ou initialiser
        self.current_settings = self.DEFAULT_SETTINGS.copy()
        self.current_instructions = {k: v.copy() for k, v in self.DEFAULT_INSTRUCTIONS.items()}
        self.current_magic_phrases = {k: v.copy() for k, v in self.DEFAULT_MAGIC_PHRASES.items()}
        
        self.load_config()
    
    def load_config(self):
        """Charge configuration depuis fichier"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                
                # Charger settings
                for key, value in saved.get("settings", {}).items():
                    if key in self.DEFAULT_SETTINGS:
                        self.current_settings[key] = value
                
                # Charger instructions personnalisées
                for key, value in saved.get("instructions", {}).items():
                    if key in self.current_instructions:
                        self.current_instructions[key].update(value)
                
                # Charger phrases magiques personnalisées
                for key, value in saved.get("magic_phrases", {}).items():
                    if key in self.current_magic_phrases:
                        self.current_magic_phrases[key] = value
                
                print(f"[INTROSPECTION-CONFIG] ✅ Configuration v4 chargée")
            else:
                print(f"[INTROSPECTION-CONFIG] 🆕 Première exécution - config par défaut")
                self.save_config()
                
        except Exception as e:
            print(f"[INTROSPECTION-CONFIG] ❌ Erreur chargement: {e}")
    
    def save_config(self):
        """Sauvegarde configuration"""
        try:
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "version": self.VERSION,
                "settings": self.current_settings,
                "instructions": {
                    k: {"instruction": v["instruction"], "default_tokens": v.get("default_tokens", 500)}
                    for k, v in self.current_instructions.items()
                },
                "magic_phrases": self.current_magic_phrases
            }
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"[INTROSPECTION-CONFIG] 💾 Configuration sauvegardée")
            
        except Exception as e:
            print(f"[INTROSPECTION-CONFIG] ❌ Erreur sauvegarde: {e}")
    
    # =========================================================================
    # API PUBLIQUE
    # =========================================================================
    
    def get(self, key: str, default=None):
        """Récupère un paramètre"""
        return self.current_settings.get(key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """Modifie un paramètre et sauvegarde"""
        if key in self.DEFAULT_SETTINGS:
            self.current_settings[key] = value
            self.save_config()
            return True
        return False
    
    def get_instruction(self, step_key: str) -> Dict[str, Any]:
        """Récupère instruction complète pour une étape"""
        return self.current_instructions.get(step_key, {})
    
    def get_instruction_text(self, step_key: str) -> str:
        """Récupère le texte d'instruction pour une étape"""
        return self.current_instructions.get(step_key, {}).get("instruction", "")
    
    def set_instruction(self, step_key: str, instruction_text: str):
        """Modifie le texte d'instruction pour une étape"""
        if step_key in self.current_instructions:
            self.current_instructions[step_key]["instruction"] = instruction_text
            self.save_config()
            return True
        return False
    
    def reset_instruction_to_default(self, step_key: str) -> bool:
        """Restaure instruction par défaut pour une étape"""
        if step_key in self.DEFAULT_INSTRUCTIONS:
            self.current_instructions[step_key] = self.DEFAULT_INSTRUCTIONS[step_key].copy()
            self.save_config()
            print(f"[INTROSPECTION-CONFIG] 🔄 Instruction '{step_key}' restaurée par défaut")
            return True
        return False
    
    def reset_instructions(self):
        """Restaure toutes les instructions par défaut"""
        self.current_instructions = {k: v.copy() for k, v in self.DEFAULT_INSTRUCTIONS.items()}
        self.save_config()
        print(f"[INTROSPECTION-CONFIG] 🔄 Toutes les instructions restaurées par défaut")
    
    def reset_all_to_default(self):
        """Restaure TOUT par défaut"""
        self.current_settings = self.DEFAULT_SETTINGS.copy()
        self.current_instructions = {k: v.copy() for k, v in self.DEFAULT_INSTRUCTIONS.items()}
        self.current_magic_phrases = {k: v.copy() for k, v in self.DEFAULT_MAGIC_PHRASES.items()}
        self.save_config()
        print(f"[INTROSPECTION-CONFIG] 🔄 Configuration complète restaurée par défaut")
    
    # Alias pour compatibilité
    reset_all = reset_all_to_default
    
    def is_enabled(self) -> bool:
        """Vérifie si extension activée"""
        return self.get("extension_enabled", False)
    
    def get_introspection_mode(self) -> str:
        """Retourne mode ('on_demand' ou 'autonomous')"""
        return self.get("introspection_mode", "on_demand")
    
    def get_magic_phrases(self, category: str) -> List[str]:
        """Récupère phrases magiques d'une catégorie"""
        return self.current_magic_phrases.get(category, [])
    
    def build_trigger_patterns(self) -> List[str]:
        """Génère patterns regex depuis phrases magiques"""
        patterns = []
        for phrase in self.get_magic_phrases("user_trigger"):
            # Convertir en pattern regex flexible
            pattern = re.escape(phrase).replace(r"\ ", r"\s+")
            patterns.append(pattern)
        return patterns
    
    def build_stop_patterns(self) -> List[str]:
        """Génère patterns regex stop depuis phrases magiques"""
        patterns = []
        for phrase in self.get_magic_phrases("user_stop"):
            pattern = re.escape(phrase).replace(r"\ ", r"\s+")
            patterns.append(pattern)
        return patterns
    
    def matches_trigger_pattern(self, text: str, source: str = "user") -> bool:
        """
        Vérifie si le texte correspond à un pattern de déclenchement
        
        Args:
            text: Texte à vérifier
            source: "user" ou "ia"
        
        Returns:
            bool: True si match trouvé
        """
        if not text:
            return False
        text_lower = text.lower().strip()
        
        if source == "user":
            patterns = self.build_trigger_patterns()
        else:
            # Pour l'IA, patterns de réflexion
            patterns = [re.escape(p) for p in self.get_magic_phrases("ia_reflection")]
        
        for pattern in patterns:
            try:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    return True
            except re.error:
                # Pattern invalide - essayer en texte brut
                if pattern.lower() in text_lower:
                    return True
        return False
    
    def matches_stop_pattern(self, text: str, source: str = "user") -> bool:
        """
        Vérifie si le texte correspond à un pattern d'arrêt
        
        Args:
            text: Texte à vérifier
            source: "user" ou "ia"
        
        Returns:
            bool: True si match trouvé
        """
        if not text:
            return False
        text_lower = text.lower().strip()
        
        if source == "user":
            patterns = self.build_stop_patterns()
        else:
            # Pour l'IA - arrêt via conclusion
            patterns = [re.escape(p) for p in self.get_magic_phrases("synthesis_ready")]
        
        for pattern in patterns:
            try:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    return True
            except re.error:
                if pattern.lower() in text_lower:
                    return True
        return False
    
    def check_synthesis_ready(self, text: str) -> bool:
        """Vérifie si le texte contient une phrase de fin de dialogue"""
        text_lower = text.lower()
        for phrase in self.get_magic_phrases("synthesis_ready"):
            if phrase.lower() in text_lower:
                return True
        return False
    
    def get_tokens_for_step(self, step_key: str) -> int:
        """Récupère limite tokens pour une étape"""
        # D'abord vérifier dans settings
        setting_key = f"{step_key}_max_tokens"
        if setting_key in self.current_settings:
            return self.current_settings[setting_key]
        # Sinon utiliser défaut de l'instruction
        return self.current_instructions.get(step_key, {}).get("default_tokens", 500)

    def get_introspection_settings(self) -> Dict[str, Any]:
        """Retourne paramètres introspection (compatibilité orchestrateur v2.0)"""
        return {
            # Tokens par rôle (mapping vers clés v2.1)
            "main_ai_tokens_per_message": self.get("step2_conscious_max_tokens", 200),
            "archiviste_tokens_per_message": self.get("step2_unconscious_max_tokens", 200),
            "synthesis_max_tokens": self.get("step3_max_tokens", 700),
            # Dialogue
            "max_exchanges": self.get("max_dialogue_exchanges", 6),
            "min_exchanges": self.get("min_dialogue_exchanges", 2),
            "max_duration": self.get("max_introspection_duration", 120),
            # Affichage
            "show_dialogue": self.get("show_dialogue_details", True),
            "streaming": self.get("typing_animation", True),
            # Sauvegarde
            "ia_decides_save": self.get("auto_save_enabled", False),
            "importance_threshold": self.get("importance_threshold", 6),
            # Phrases magiques (compatibilité)
            "user_stop_phrases": self.get_magic_phrases("user_stop"),
            "user_trigger_phrases": self.get_magic_phrases("user_trigger"),
            "ia_trigger_phrases": self.get_magic_phrases("ia_reflection"),
            "synthesis_phrase": (self.get_magic_phrases("synthesis_ready") or ["je suis prete a formuler ma reponse"])[0],
        }


# Instance singleton
_config_instance = None

def get_introspection_config() -> IntrospectionConfigV2:
    """Retourne instance singleton configuration v4"""
    global _config_instance
    if _config_instance is None:
        _config_instance = IntrospectionConfigV2()
    return _config_instance


# Export pour compatibilité
__all__ = ['IntrospectionConfigV2', 'get_introspection_config']
