# 🎯 Capability Advisor - Configuration (v2 - Sans Memory IDs)
"""
Configuration extension Capability Advisor
Système hybride: Triggers Python + Contexte CHD
"""

from pathlib import Path
from typing import Optional
import json

# Chemins
DATA_DIR = Path(__file__).parent.parent.parent / "data"
CONFIG_FILE = DATA_DIR / "capability_advisor_config.json"
CUSTOM_PROMPT_FILE = DATA_DIR / "capability_advisor_prompt.txt"


class CapabilityAdvisorConfig:
    """Configuration et constantes pour l'extension Capability Advisor"""
    
    # Métadonnées extension
    EXTENSION_NAME = "capability_advisor"
    EXTENSION_VERSION = "2.0"
    
    # Seuils et timing
    CONFIDENCE_THRESHOLD_GLOBAL = 0.7
    LED_TIMEOUT = 30
    COOLDOWN_MESSAGES = 3

    # Archiviste
    MAX_TOKENS_ANALYSIS = 500
    TEMPERATURE = 0.3
    RECENT_CONTEXT_MESSAGES = 3

    # Seuils par capacite (source de verite pour la reconstruction du JSON)
    DEFAULT_CAPABILITY_THRESHOLDS = {
        "memory": 0.85,
        "ego_memory": 0.8,
        "introspection": 0.7,
        "image_gen": 0.7,
        "webcam": 0.8,
        "web_search": 0.75,
        "biography": 0.8,
        "contextual_recall": 0.7
    }
    
    # UI
    ENABLE_OVERLAY = True
    ENABLE_EXTENSION = True
    
    # Prompt Archiviste (Protocole CHD)
    DEFAULT_ADVISOR_PROMPT = """ARCHIVISTE | SUBCONSCIENT | DÉCISION_CAPACITÉ

INPUT | MSG: {user_message} | CTX: {recent_context}
TOOLS | {available_capabilities}
SEUILS | {capability_thresholds}

OUTPUT_JSON | {{"needs_capability": bool, "capability_id": "ID|null", "reasoning": "1phrase", "suggestion": "PHRASE_COMPLÈTE", "confidence": 0-1}}

RÈGLES:
• suggestion = phrase magique MOT_POUR_MOT (copier example_usage + compléter)
• ZÉRO méta ("ORDRE", "TU DOIS") - JUSTE la phrase
• confidence: reflète ta certitude RÉELLE — si ta confidence < seuil de la capacité choisie (ligne SEUILS) → needs_capability:false directement
• Utilise context_chd pour décider

EXEMPLES:
✅ "Montre-moi dragon" → {{"needs_capability":true, "capability_id":"image_gen", "reasoning":"Visuel demandé", "suggestion":"je dois créer une image de : dragon majestueux crachant feu, écailles dorées", "confidence":0.95}}
✅ "Actus IA?" → {{"needs_capability":true, "capability_id":"web_search", "reasoning":"Infos actuelles", "suggestion":"il faut que je cherche sur internet dernières actualités IA 2026", "confidence":0.92}}
❌ "Salut" → {{"needs_capability":false, "capability_id":null, "reasoning":"Social basique", "suggestion":"", "confidence":0.0}}
"""

    DEFAULT_ADVISOR_PROMPT_EN = """ARCHIVIST | SUBCONSCIOUS | CAPABILITY_DECISION

INPUT | MSG: {user_message} | CTX: {recent_context}
TOOLS | {available_capabilities}
THRESHOLDS | {capability_thresholds}

OUTPUT_JSON | {{"needs_capability": bool, "capability_id": "ID|null", "reasoning": "1sentence", "suggestion": "FULL_PHRASE", "confidence": 0-1}}

RULES:
• suggestion = magic phrase WORD_FOR_WORD (copy example_usage + complete it)
• ZERO meta ("ORDER", "YOU MUST") - JUST the phrase
• confidence: reflects your REAL certainty — if your confidence < threshold of chosen capability (THRESHOLDS line) → needs_capability:false directly
• Use context_chd to decide
• Note: magic phrase suggestions must use the exact trigger syntax defined in OGMA (may be in French)

EXAMPLES:
✅ "Show me a dragon" → {{"needs_capability":true, "capability_id":"image_gen", "reasoning":"Visual requested", "suggestion":"je dois créer une image de : majestic dragon breathing fire, golden scales", "confidence":0.95}}
✅ "AI news?" → {{"needs_capability":true, "capability_id":"web_search", "reasoning":"Current info needed", "suggestion":"il faut que je cherche sur internet latest AI news 2026", "confidence":0.92}}
❌ "Hi" → {{"needs_capability":false, "capability_id":null, "reasoning":"Basic social", "suggestion":"", "confidence":0.0}}
"""
    
    def __init__(self):
        """Initialise configuration"""
        self.config = self.load_config()
    
    def load_config(self) -> dict:
        """Charge configuration depuis fichier JSON"""
        default_config = {
            "enabled": self.ENABLE_EXTENSION,
            "confidence_threshold": self.CONFIDENCE_THRESHOLD_GLOBAL,
            "led_timeout": self.LED_TIMEOUT,
            "cooldown_messages": self.COOLDOWN_MESSAGES,
            "max_tokens": self.MAX_TOKENS_ANALYSIS,
            "temperature": self.TEMPERATURE,
            "recent_context_messages": self.RECENT_CONTEXT_MESSAGES,
            "capability_thresholds": self.DEFAULT_CAPABILITY_THRESHOLDS
        }
        
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                existing_config = json.load(f)
                merged_config = default_config.copy()
                merged_config.update(existing_config)
                return merged_config
        except:
            self.save_config(default_config)
            return default_config
    
    def save_config(self, config: dict = None):
        """Sauvegarde configuration"""
        if config is None:
            config = self.config
        try:
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[CAPABILITY-ADVISOR] ❌ Erreur sauvegarde: {e}")
    
    def get_advisor_prompt_template(self) -> str:
        """Récupère prompt Archiviste (custom ou défaut langue-aware)"""
        if CUSTOM_PROMPT_FILE.exists():
            try:
                with open(CUSTOM_PROMPT_FILE, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    # Si le fichier contient le défaut FR exact, appliquer logique langue
                    if content != self.DEFAULT_ADVISOR_PROMPT.strip():
                        return content  # Contenu personnalisé
            except Exception:
                pass
        # Défaut selon langue courante
        try:
            from utils.i18n import get_lang
            if get_lang() == 'en':
                return self.DEFAULT_ADVISOR_PROMPT_EN
        except Exception:
            pass
        return self.DEFAULT_ADVISOR_PROMPT
    
    def save_custom_prompt(self, prompt_text: str):
        """Sauvegarde prompt personnalisé"""
        try:
            CUSTOM_PROMPT_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(CUSTOM_PROMPT_FILE, 'w', encoding='utf-8') as f:
                f.write(prompt_text)
            print(f"[CAPABILITY-ADVISOR] ✅ Prompt sauvegardé")
        except Exception as e:
            print(f"[CAPABILITY-ADVISOR] ❌ Erreur: {e}")
    
    def reset_to_default_prompt(self):
        """Réinitialise au prompt par défaut"""
        if CUSTOM_PROMPT_FILE.exists():
            CUSTOM_PROMPT_FILE.unlink()
    
    def is_enabled(self) -> bool:
        """Vérifie si extension est activée"""
        return self.config.get('enabled', True)
    
    def set_enabled(self, enabled: bool):
        """Active/désactive extension"""
        self.config['enabled'] = enabled
        self.save_config()
    
    def get_capability_thresholds(self) -> dict:
        """Récupère seuils personnalisés"""
        return self.config.get('capability_thresholds', {})
    
    def get_capability_threshold(self, capability_id: str, default: Optional[float] = None) -> Optional[float]:
        """Récupère seuil pour une capacité"""
        return self.get_capability_thresholds().get(capability_id, default)
    
    def save_capability_thresholds(self, thresholds: dict):
        """Sauvegarde seuils personnalisés"""
        validated = {}
        for cap_id, threshold in thresholds.items():
            try:
                t = float(threshold)
                if 0.0 <= t <= 1.0:
                    validated[cap_id] = t
            except:
                pass
        self.config['capability_thresholds'] = validated
        self.save_config()
    
    def reset_capability_thresholds(self):
        """Réinitialise seuils"""
        self.config['capability_thresholds'] = {}
        self.save_config()
