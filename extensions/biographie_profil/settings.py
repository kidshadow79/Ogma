"""
Configuration et paramètres pour l'extension Biographie Profil
=============================================================

Gère les paramètres configurables:
- Instructions pour Volume 2
- Templates par défaut
- Configuration de l'extension
"""

import json
from pathlib import Path
from typing import Dict, Any

class BiographySettings:
    """Gestionnaire des paramètres de l'extension"""
    
    def __init__(self):
        self.settings_file = Path("data/biography_settings.json")
        self.default_settings = self.get_default_settings()
        self.settings = self.load_settings()
        
        print("[BIOGRAPHY-SETTINGS] ✅ Paramètres initialisés")
    
    def get_default_settings(self) -> Dict[str, Any]:
        """Retourne les paramètres par défaut"""
        return {
            "extension_enabled": False,
            "volume2_template": self.get_default_volume2_template(),
            "volume2_instructions": self.get_default_volume2_instructions(),
            "auto_detect_names": True,
            "min_name_length": 3,
            "max_name_length": 15,
            "backup_count": 5,
            "version": "1.0.0"
        }
    
    def get_default_volume2_template(self) -> str:
        """Template par défaut pour le Volume 2"""
        return """=== BIOGRAPHIE DE {user_name} ===

== PROFIL GÉNÉRAL ==
{general_profile}

== ASPECTS PSYCHOLOGIQUES ==
{psychological_aspects}

== ASPECTS INTELLECTUELS ==
{intellectual_aspects}

== ASPECTS PROFESSIONNELS ==
{professional_aspects}

== ASPECTS FAMILIAUX ==
{family_aspects}

== PROJETS ==
{projects}

== SOUVENIRS ==
{memories}

== TRAITS ET SPÉCIFICITÉS PHYSIQUES ==
{physical_traits}

== HISTORIQUE RELATIONNEL ==
{relationship_history}

== SOURCES ET RÉFÉRENCES ==
{sources_references}"""
    
    def get_default_volume2_instructions(self) -> str:
        """Instructions par défaut pour la rédaction du Volume 2 - Architecture V2.0"""
        return """# INSTRUCTIONS VOLUME 2 - ARCHITECTURE V2.0 🆕

## CONTEXTE
Tu travailles avec des données JSON structurées collectées depuis multiples sources :
- Volume 1 FAISS, Conversations courantes, Historique OGMA, Summaries Cache

## MISSION
Transformer ce JSON en journal biographique élégant et professionnel.

## STYLE RÉDACTIONNEL V2.0
- **Narratif expert** : Portrait psychologique de qualité psychiatrique
- **Structure claire** : Markdown avec sections organisées  
- **Ton bienveillant** : Analytique mais empathique
- **Synthèse intelligente** : Pas de copier-coller brut du JSON

## MÉTHODE DE TRANSFORMATION

### 1. CHRONOLOGIE
- Présente les événements par ordre temporel
- Format : **Date** | Événement (*Source*)
- Identifie les patterns et évolutions

### 2. ANALYSE PSYCHOLOGIQUE
- Synthétise les traits du JSON en profil cohérent
- MBTI avec justifications basées sur données
- Mécanismes de défense et vulnérabilités avec tact

### 3. PROFIL INTELLECTUEL  
- Patterns de pensée observés et documentés
- Capacités et centres d'intérêt confirmés
- Évolution des compétences dans le temps

### 4. PRÉFÉRENCES PERSONNELLES
- Goûts et aversions identifiés par répétition
- Évolutions des préférences documentées
- Influences et facteurs de changement

## RÈGLES QUALITÉ
✅ **Traçabilité** : Mentionne les sources des insights
✅ **Cohérence** : Liens logiques entre observations  
✅ **Évolution** : Montre changements temporels
✅ **Nuance** : Évite les affirmations absolues
✅ **Respect** : Ton professionnel et bienveillant

❌ **Éviter** : Répétition brute, généralités, ton froid"""
    
    def load_settings(self) -> Dict[str, Any]:
        """Charge les paramètres depuis le fichier"""
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                
                # Merger avec les défauts pour ajouter nouvelles clés
                settings = self.default_settings.copy()
                settings.update(loaded)
                return settings
            else:
                return self.default_settings.copy()
                
        except Exception as e:
            print(f"[BIOGRAPHY-SETTINGS] ❌ Erreur chargement paramètres: {e}")
            return self.default_settings.copy()
    
    def save_settings(self) -> bool:
        """Sauvegarde les paramètres"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            
            print("[BIOGRAPHY-SETTINGS] ✅ Paramètres sauvegardés")
            return True
            
        except Exception as e:
            print(f"[BIOGRAPHY-SETTINGS] ❌ Erreur sauvegarde paramètres: {e}")
            return False
    
    def get(self, key: str, default=None):
        """Récupère une valeur de paramètre"""
        return self.settings.get(key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """Définit une valeur de paramètre"""
        try:
            self.settings[key] = value
            return self.save_settings()
        except Exception as e:
            print(f"[BIOGRAPHY-SETTINGS] ❌ Erreur définition paramètre: {e}")
            return False
    
    def is_enabled(self) -> bool:
        """Vérifie si l'extension est activée"""
        return self.settings.get("extension_enabled", False)
    
    def enable(self) -> bool:
        """Active l'extension"""
        return self.set("extension_enabled", True)
    
    def disable(self) -> bool:
        """Désactive l'extension"""
        return self.set("extension_enabled", False)