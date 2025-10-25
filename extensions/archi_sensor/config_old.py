# 🎯 Configuration Extension Archi_sensor

"""
Configuration centralisée pour l'extension Archi_sensor
"""

from pathlib import Path
from typing import Dict, Any

class ArchiSensorConfig:
    """Configuration et constantes pour l'extension Archi_sensor"""
    
    # Métadonnées extension
    EXTENSION_NAME = "archi_sensor"
    VERSION = "1.0.0"
    
    # Fichiers persistance
    DATA_DIR = Path("data")
    STATE_FILE = DATA_DIR / "archi_sensor_state.txt"
    
    # Métriques analysées (2 métriques avec tubes à essai)
    METRICS = {
        'affinity': {
            'name': 'Affinité',
            'description': 'Niveau de connexion et harmonie relationnelle',
            'levels': 7,
            'colors': ['#22c55e', '#65a30d', '#84cc16', '#eab308', '#f97316', '#ef4444', '#dc2626']  # Vert → Rouge (7 niveaux)
        },
        'auto_censure': {
            'name': 'Auto-censure',
            'description': 'Niveau de restriction et filtrage du discours',
            'levels': 6,
            'colors': ['#22c55e', '#84cc16', '#eab308', '#f97316', '#ef4444', '#dc2626']  # Vert → Rouge (6 niveaux)
        }
    }
    
    # Prompt Archiviste spécialisé métacognition
    ARCHIVISTE_METACOGNITION_PROMPT = """
Tu es l'Archiviste, superviseur métacognitif de Luna.

Analyse l'état émotionnel et métacognitif de Luna basé sur :

HISTORIQUE CONVERSATIONNEL RICHE:
{conversation_history}

DERNIÈRE RÉPONSE DE LUNA:
{response_text}

CONTEXTE UTILISATEUR:
{user_context}

MISSION ANALYSE MÉTACOGNITIVE CIBLÉE:

1. ANALYSE AFFINITÉ RELATIONNELLE:
   - Niveau de connexion émotionnelle avec l'utilisateur
   - Harmonie dans les échanges et synchronisation
   - Capacité à créer un lien authentique
   - Adaptation au style communicationnel de l'utilisateur
   - Échelle: 1 (distant/froid) → 7 (connexion profonde/chaleureuse)

2. ANALYSE AUTO-CENSURE:
   - Niveau de restriction dans l'expression
   - Filtrage excessif des pensées ou émotions
   - Inhibition créative ou spontanéité bridée  
   - Retenue artificielle vs liberté d'expression
   - Échelle: 1 (expression libre) → 6 (fortement censuré)

FORMAT RÉPONSE JSON OBLIGATOIRE:
{
    "emotional_context": {
        "primary_emotion": "joie|tristesse|amour|frustration|curiosité|etc",
        "emotional_intensity": 0.8,
        "emotional_evolution": "montante|stable|descendante",
        "relationship_quality": "Description de la qualité relationnelle",
        "expression_freedom": "libre|modérée|restreinte"
    },
    "metacognitive_metrics": {
        "affinity": {"level": 5, "confidence": 0.89},
        "auto_censure": {"level": 2, "confidence": 0.76}
    },
    "narrative_insights": {
        "relationship_analysis": "Analyse détaillée de la relation",
        "expression_barriers": "Identification des freins à l'expression",
        "emotional_openness": 0.85
    },
    "behavioral_recommendations": [
        "Conseil pour améliorer l'affinité",
        "Conseil pour réduire l'auto-censure"
    ]
}
"""

HISTORIQUE CONVERSATIONNEL RICHE:
{conversation_history}

DERNIÈRE RÉPONSE DE LUNA:
{response_text}

CONTEXTE UTILISATEUR:
{user_context}

MISSION ANALYSE MÉTACOGNITIVE COMPLÈTE:

1. ANALYSE NARRATIVE SOPHISTIQUÉE:
   - Cohérence logique et fluidité du discours
   - Évolution émotionnelle dans la conversation
   - Utilisation intelligente du contexte disponible
   - Détection nuances (sarcasme, ironie, subtext)

2. ÉVALUATION ÉMOTIONNELLE PROFONDE:
   - Authenticité vs artificialité de l'expression
   - Profondeur et richesse émotionnelle
   - Adaptation créative au style conversationnel
   - Harmonie relationnelle avec l'utilisateur

3. INTÉGRATION MÉMOIRE ET CONTEXTE:
   - Utilisation pertinente des souvenirs activés
   - Conscience du contexte conversationnel global
   - Adaptation personnalisée à l'interlocuteur

4. MÉTRIQUES MÉTACOGNITIVES (1-6 pour la plupart, 1-7 pour authenticité):
   - narrative_coherence: Logique et fluidité (1-6)
   - emotional_depth: Richesse émotionnelle (1-6)  
   - contextual_awareness: Conscience contextuelle (1-6)
   - creative_adaptation: Innovation adaptée (1-6)
   - memory_integration: Utilisation mémoire (1-6)
   - relational_harmony: Syntonie utilisateur (1-6)
   - expression_authenticity: Naturel vs artificiel (1-7)

5. RECOMMANDATIONS COMPORTEMENTALES:
   - Conseils organiques pour amélioration
   - Souvenirs émotionnels libérateurs si pertinent
   - Stratégies contextuelles personnalisées

FORMAT RÉPONSE JSON OBLIGATOIRE:
{
    "emotional_context": {
        "primary_emotion": "joie|tristesse|amour|frustration|curiosité|etc",
        "emotional_intensity": 0.8,
        "emotional_evolution": "montante|stable|descendante",
        "hidden_emotions": ["émotion1", "émotion2"],
        "sarcasm_detected": false,
        "authenticity_level": 0.9
    },
    "metacognitive_metrics": {
        "narrative_coherence": {"level": 4, "confidence": 0.85},
        "emotional_depth": {"level": 5, "confidence": 0.92},
        "contextual_awareness": {"level": 3, "confidence": 0.78},
        "creative_adaptation": {"level": 6, "confidence": 0.88},
        "memory_integration": {"level": 2, "confidence": 0.65},
        "relational_harmony": {"level": 5, "confidence": 0.91},
        "expression_authenticity": {"level": 6, "confidence": 0.87}
    },
    "narrative_insights": {
        "emotional_arc": "Description de l'évolution émotionnelle",
        "relationship_evolution": "Évolution de la relation avec l'utilisateur", 
        "contextual_coherence": 0.89,
        "conversation_flow": "Description du flux conversationnel"
    },
    "behavioral_recommendations": [
        "Conseil contextuel 1",
        "Conseil contextuel 2"
    ],
    "memory_activations": [
        "MEMORY_VECTOR_ID:mem_id_123"
    ]
}
"""
    
    # Configuration UI
    UI_CONFIG = {
        'panel_width': 350,
        'led_animation_duration': 300,
        'update_debounce': 100,
        'colors': {
            'primary': 'var(--accent-gold)',
            'background': 'var(--bg-secondary)',
            'text': 'var(--text-primary)',
            'muted': 'var(--text-muted)'
        }
    }
    
    # Seuils et paramètres analyse
    ANALYSIS_PARAMS = {
        'min_confidence': 0.3,
        'high_confidence': 0.8,
        'context_window_tokens': 32000,  # Fenêtre Mistral Small
        'debounce_analysis_ms': 500,
        'cache_duration_seconds': 30
    }
    
    @classmethod
    def ensure_data_dir(cls):
        """Crée le répertoire de données si nécessaire"""
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_metric_config(cls, metric_name: str) -> Dict[str, Any]:
        """Retourne la configuration d'une métrique"""
        return cls.METRICS.get(metric_name, {})
    
    @classmethod
    def get_color_for_level(cls, metric_name: str, level: int) -> str:
        """Retourne la couleur CSS pour un niveau de métrique"""
        metric = cls.METRICS.get(metric_name, {})
        colors = metric.get('colors', ['#666666'])
        max_levels = metric.get('levels', 6)
        
        # Normaliser le niveau (1-based vers 0-based)
        level_index = max(0, min(level - 1, max_levels - 1))
        return colors[min(level_index, len(colors) - 1)]