# Test intégration Introspection v2.1
"""
Test complet du système introspection avec mocks des contrôleurs IA
"""
import sys
import asyncio
sys.path.insert(0, r"c:\IA\OGMA")

print("=" * 60)
print("TEST INTÉGRATION INTROSPECTION v2.1")
print("=" * 60)


class MockAIController:
    """Mock contrôleur IA pour test"""
    
    def __init__(self, name: str, responses: list = None):
        self.name = name
        self.responses = responses or []
        self.call_count = 0
    
    async def call_chat_api(self, messages, max_tokens=1000, context_length=8192, temperature=0.7, is_json=False):
        """Simule appel API"""
        self.call_count += 1
        
        if self.call_count <= len(self.responses):
            response = self.responses[self.call_count - 1]
            print(f"   [{self.name}] Appel #{self.call_count} → {len(response)} chars")
            return response, None
        
        return f"Réponse par défaut {self.name} #{self.call_count}", None


class MockMemoryManager:
    """Mock memory manager"""
    
    async def search_memories(self, query, limit=5, threshold=0.5):
        return [
            {"content": "Souvenir 1: Discussion précédente sur l'IA"},
            {"content": "Souvenir 2: Préférence utilisateur pour réponses concises"}
        ]


async def test_full_introspection():
    """Test une introspection complète"""
    
    from extensions.cognitive_mirror.introspection_engine import IntrospectionEngine
    from extensions.cognitive_mirror.config_v2 import get_introspection_config
    
    print("\n📋 Configuration:")
    config = get_introspection_config()
    print(f"   - Mode: {config.get_introspection_mode()}")
    print(f"   - Tokens step1: {config.get('step1_max_tokens')}")
    print(f"   - API timeout: {config.get('api_timeout')}s")
    
    # Réponses simulées - 6 appels Conscient attendus
    conscious_responses = [
        # Step 1: Analyse (appel #1)
        """🎯 INTENTION: L'utilisateur veut comprendre le fonctionnement de sa mémoire
❓ À DEMANDER À MON INCONSCIENT: 
- Qu'ai-je retenu de nos conversations précédentes sur ce sujet?
💭 PISTE DE RÉPONSE: Expliquer le système hybride SQLite+FAISS""",
        
        # Step 2: Tour 1 conscient (appel #2)
        """Mon Inconscient, rappelle-moi comment j'ai répondu à des questions techniques similaires?""",
        
        # Step 2: Tour 2 conscient (appel #3)
        """Qu'est-ce que mon ego me dit sur l'approche pédagogique à adopter?""",
        
        # Step 2: Tour 3 conscient (appel #4)
        """Comment puis-je rendre cette explication accessible?""",
        
        # Step 2: Tour 4 conscient (appel #5)
        """je suis prêt à formuler ma réponse""",  # Phrase magique fin dialogue
        
        # Step 3: Synthèse (appel #6)
        """<INSIGHTS>
Le dialogue m'a rappelé que l'utilisateur préfère des explications structurées.
Mon ego me pousse à être pédagogue sans être condescendant.
</INSIGHTS>

<RÉPONSE>
Ta mémoire fonctionne sur un système hybride :
1. **SQLite** pour le stockage structuré des souvenirs
2. **FAISS** pour la recherche sémantique rapide

C'est ce qui me permet de retrouver des informations pertinentes même quand tu utilises des mots différents !
</RÉPONSE>

<SAVE>
{"save": true, "importance": 7, "reason": "Explication technique importante"}
</SAVE>"""
    ]
    
    # 4 appels Inconscient pour Step 2
    unconscious_responses = [
        """📚 MÉMOIRE: 2 conversations passées sur concepts techniques.
Tu utilises des listes numérotées et analogies.
🎭 EGO: Tu es pédagogue et patient.""",
        
        """🔮 Tu préfères expliquer avec des exemples concrets.
L'utilisateur apprécie la clarté.""",
        
        """💬 HISTORIQUE: Questions techniques bien reçues.
Propose des métaphores simples.""",
        
        """✨ Tu es prêt à synthétiser maintenant."""
    ]
    
    # Créer mocks
    conscious = MockAIController("CONSCIENT", conscious_responses)
    unconscious = MockAIController("INCONSCIENT", unconscious_responses)
    memory = MockMemoryManager()
    
    print("\n🚀 Initialisation engine...")
    
    # Messages callback pour affichage
    messages_received = []
    def on_message(step, role, content):
        messages_received.append((step, role, len(content)))
        print(f"   📨 Step {step} | {role}: {len(content)} chars")
    
    def on_progress(step, total, name):
        print(f"   📍 Étape {step}/{total}: {name}")
    
    engine = IntrospectionEngine(
        chat_controller=conscious,
        archiviste_controller=unconscious,
        memory_manager=memory,
        on_message_callback=on_message,
        on_progress_callback=on_progress
    )
    
    print("\n🧠 Lancement introspection...")
    
    result = await engine.run_introspection(
        user_message="Comment fonctionne ta mémoire?",
        context={
            "main_ai_identity": "Luna",
            "user_identity": "Tytan",
            "relationship_context": "Collaboration technique depuis 6 mois"
        },
        trigger_source="user"
    )
    
    print("\n📊 Résultat:")
    print(f"   - Succès: {result.get('success')}")
    print(f"   - Durée: {result.get('duration', 0):.2f}s")
    print(f"   - Messages dialogue: {len(result.get('dialogue', []))}")
    print(f"   - Save décidé: {result.get('save_decision')}")
    print(f"   - Importance: {result.get('importance')}")
    
    if result.get('success'):
        print(f"\n💬 Réponse finale ({len(result.get('final_response', ''))} chars):")
        response = result.get('final_response', '')
        # Afficher premiers 300 chars
        print(f"   {response[:300]}...")
        
        # Vérifications
        assert "SQLite" in response or "FAISS" in response, "Réponse devrait mentionner le système"
        assert result.get('save_decision') == True, "Should save"
        assert result.get('importance') == 7, "Importance should be 7"
        
        print("\n✅ INTROSPECTION COMPLÈTE RÉUSSIE!")
    else:
        print(f"\n❌ ÉCHEC: {result.get('error')}")
        if result.get('user_message'):
            print(f"   Message: {result.get('user_message')}")
        return False
    
    return True


async def test_error_handling():
    """Test gestion erreurs explicites"""
    
    from extensions.cognitive_mirror.introspection_engine import IntrospectionEngine
    
    print("\n" + "=" * 60)
    print("TEST GESTION ERREURS EXPLICITES")
    print("=" * 60)
    
    # Mock qui échoue
    class FailingController:
        async def call_chat_api(self, *args, **kwargs):
            return None, "Erreur API simulée"
    
    engine = IntrospectionEngine(
        chat_controller=FailingController(),
        archiviste_controller=FailingController(),
        memory_manager=MockMemoryManager()
    )
    
    print("\n🧪 Test avec contrôleur défaillant...")
    
    result = await engine.run_introspection(
        user_message="Test erreur",
        context={},
        trigger_source="user"
    )
    
    print(f"\n📊 Résultat:")
    print(f"   - Succès: {result.get('success')}")
    
    if not result.get('success'):
        error = result.get('error', {})
        print(f"   - Type erreur: {error.get('error_type')}")
        print(f"   - Message: {result.get('user_message')}")
        print(f"   - Recoverable: {result.get('recoverable')}")
        
        # Vérifier que l'erreur est explicite
        assert result.get('user_message') is not None, "Devrait avoir message utilisateur"
        assert 'error' in result, "Devrait avoir détails erreur"
        
        print("\n✅ ERREUR GÉRÉE EXPLICITEMENT!")
        return True
    else:
        print("\n❌ Aurait dû échouer!")
        return False


async def main():
    """Exécute tous les tests"""
    
    try:
        # Test introspection complète
        success1 = await test_full_introspection()
        
        # Test gestion erreurs
        success2 = await test_error_handling()
        
        print("\n" + "=" * 60)
        if success1 and success2:
            print("✅ TOUS LES TESTS D'INTÉGRATION RÉUSSIS!")
        else:
            print("❌ CERTAINS TESTS ONT ÉCHOUÉ")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERREUR FATALE: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
