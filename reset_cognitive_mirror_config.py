#!/usr/bin/env python3
"""
Script de réinitialisation complète des paramètres Cognitive Mirror
Supprime toute trace de "Luna" et remet les paramètres par défaut
"""

import sys
import os
import json
from pathlib import Path

sys.path.append(os.path.abspath('.'))

def reset_cognitive_mirror():
    """Réinitialise complètement la config Cognitive Mirror"""
    print("🔄 RÉINITIALISATION COGNITIVE MIRROR")
    print("=" * 50)
    
    # 1. Charger la config par défaut propre
    try:
        from extensions.cognitive_mirror.config import CognitiveMirrorConfig
        config = CognitiveMirrorConfig()
        
        print("✅ Config par défaut chargée")
        
        # 2. Forcer la réinitialisation de tous les paramètres
        default_params = {
            'extension_enabled': True,
            'introspection_mode': 'on_demand',
            'main_ai_tokens_per_message': -1,
            'archiviste_tokens_per_message': -1,
            'synthesis_max_tokens': -1,
            'max_dialogue_exchanges': 6,
            'max_introspection_duration': 300,
            'ia_decides_save': False,
            'importance_threshold': 5,
            'show_dialogue_details': True,
            'streaming_animation': True
        }
        
        for key, value in default_params.items():
            config.set(key, value)
            print(f"✅ {key}: {value}")
            
        print("\n📋 Instructions réinitialisées:")
        
        # Instructions par défaut sans Luna
        instructions = {
            'main_ai_introspection_instruction': config.DEFAULT_SETTINGS['main_ai_introspection_instruction'],
            'archiviste_introspection_instruction': config.DEFAULT_SETTINGS['archiviste_introspection_instruction'],
            'introspection_box_template': config.DEFAULT_SETTINGS['introspection_box_template']
        }
        
        for key, value in instructions.items():
            config.set(key, value)
            print(f"✅ {key}: {len(value)} chars")
            
            # Vérifier qu'il n'y a pas de Luna
            if 'luna' in value.lower():
                print(f"⚠️  ATTENTION: 'Luna' détecté dans {key}")
            else:
                print(f"✅ Pas de référence Luna dans {key}")
        
        print("\n🎯 Réinitialisation terminée!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    reset_cognitive_mirror()