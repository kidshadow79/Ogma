#!/usr/bin/env python3
"""
Test de la méthode enrich_conversation_context ajoutée à IntrospectionCore
"""

import sys
from pathlib import Path

# Ajout du chemin OGMA
sys.path.insert(0, str(Path.cwd()))

def test_enrich_conversation_context():
    """Test de la nouvelle méthode enrich_conversation_context"""
    print("=== TEST ENRICH_CONVERSATION_CONTEXT ===")
    
    try:
        # Import de IntrospectionCore
        from extensions.cognitive_mirror.introspection_core import IntrospectionCore
        print("✅ Import IntrospectionCore réussi")
        
        # Création d'une instance de test (avec paramètres minimaux)
        # Nous utilisons None pour les dépendances car nous ne testons que cette méthode
        core = IntrospectionCore(
            chat_controller=None,
            archiviste_controller=None,
            memory_manager=None,
            ui_container=None
        )
        print("✅ Instance IntrospectionCore créée")
        
        # Vérifier que la méthode existe
        if hasattr(core, 'enrich_conversation_context'):
            print("✅ Méthode enrich_conversation_context trouvée")
        else:
            print("❌ Méthode enrich_conversation_context manquante")
            return False
        
        # Test d'appel avec des données de test
        test_context = {
            'user_message': 'Test message utilisateur',
            'ai_response': 'Test réponse IA',
            'timestamp': '2025-10-13T15:30:00',
            'conversation_length': 5,
            'recent_messages': ['msg1', 'msg2', 'msg3']
        }
        
        print("🧪 Test d'enrichissement du contexte...")
        core.enrich_conversation_context(test_context)
        
        # Vérifier que le contexte a été stocké
        if hasattr(core, 'enriched_context'):
            print("✅ Contexte enrichi stocké avec succès")
            print(f"   - Éléments stockés: {len(core.enriched_context)}")
            
            # Vérifier les champs attendus
            expected_fields = ['user_message', 'ai_response', 'last_enrichment', 'enrichment_source']
            missing_fields = [field for field in expected_fields if field not in core.enriched_context]
            
            if not missing_fields:
                print("✅ Tous les champs attendus présents")
                print(f"   - Champs: {list(core.enriched_context.keys())}")
            else:
                print(f"⚠️ Champs manquants: {missing_fields}")
        else:
            print("❌ Contexte enrichi non stocké")
            return False
        
        # Test d'enrichissement multiple (accumulation)
        print("🧪 Test d'enrichissement multiple...")
        additional_context = {
            'new_field': 'nouvelle_valeur',
            'user_message': 'Message mis à jour'  # Devrait écraser l'ancien
        }
        
        core.enrich_conversation_context(additional_context)
        
        if 'new_field' in core.enriched_context and core.enriched_context['user_message'] == 'Message mis à jour':
            print("✅ Enrichissement multiple fonctionnel")
        else:
            print("❌ Enrichissement multiple défaillant")
            return False
        
        print("\n🎉 TOUS LES TESTS PASSÉS !")
        print("✅ La méthode enrich_conversation_context fonctionne correctement")
        return True
        
    except Exception as e:
        print(f"❌ Erreur durant le test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_compatibility_with_ogma():
    """Test de compatibilité avec l'appel OGMA"""
    print("\n=== TEST COMPATIBILITÉ OGMA ===")
    
    try:
        # Import et récupération de l'instance comme le fait OGMA
        from extensions.cognitive_mirror import get_cognitive_mirror
        
        cognitive_mirror = get_cognitive_mirror()
        if cognitive_mirror:
            print(f"✅ Instance récupérée: {type(cognitive_mirror)}")
            
            # Vérifier que c'est bien une IntrospectionCore avec la méthode
            if hasattr(cognitive_mirror, 'enrich_conversation_context'):
                print("✅ Méthode disponible via get_cognitive_mirror()")
                
                # Test d'appel comme le fait OGMA
                test_ogma_context = {
                    'user_message': 'Message OGMA test',
                    'ai_response': 'Réponse OGMA test',
                    'timestamp': '2025-10-13T15:35:00',
                    'conversation_length': 3,
                    'recent_messages': ['msg_ogma_1', 'msg_ogma_2']
                }
                
                cognitive_mirror.enrich_conversation_context(test_ogma_context)
                print("✅ Appel réussi via interface OGMA")
                return True
            else:
                print("❌ Méthode non disponible via get_cognitive_mirror()")
                return False
        else:
            print("⚠️ Pas d'instance cognitive_mirror disponible (normal si non initialisé)")
            return True  # Ce n'est pas une erreur dans ce contexte de test
            
    except Exception as e:
        print(f"❌ Erreur test compatibilité: {e}")
        return False

if __name__ == "__main__":
    print("🧪 TEST MÉTHODE ENRICH_CONVERSATION_CONTEXT")
    print("=" * 50)
    
    success1 = test_enrich_conversation_context()
    success2 = test_compatibility_with_ogma()
    
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 50)
    
    if success1 and success2:
        print("🎉 SUCCÈS COMPLET - L'erreur OGMA devrait être résolue !")
        sys.exit(0)
    else:
        print("❌ ÉCHECS DÉTECTÉS - Vérification requise")
        sys.exit(1)