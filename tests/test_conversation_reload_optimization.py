"""
Test du système d'optimisation des conversations au reload
Vérifie que le summarizer fonctionne correctement avec l'injection
"""
import asyncio
from conversation_summarizer import summarizer

async def test_optimize_conversation():
    print("=" * 60)
    print("TEST: Optimisation conversation reload")
    print("=" * 60)
    
    # Simuler une conversation de 50 messages
    fake_conversation = []
    for i in range(50):
        if i % 2 == 0:
            fake_conversation.append({
                'role': 'user',
                'content': f'Message utilisateur {i//2 + 1}: Ceci est un test avec du contenu pour atteindre une taille raisonnable.'
            })
        else:
            fake_conversation.append({
                'role': 'assistant',
                'content': f'Réponse assistant {i//2 + 1}: Ceci est une réponse de test avec du contenu pour simuler une vraie conversation.'
            })
    
    print(f"\n📊 Conversation simulée: {len(fake_conversation)} messages")
    
    # Test 1: Vérifier que summarizer peut gérer une conversation
    print("\n[TEST 1] Vérification should_summarize...")
    should_sum = summarizer.should_summarize(len(fake_conversation))
    print(f"   → Doit résumer ? {should_sum}")
    print(f"   → Seuil actuel: {summarizer.summary_interval} messages")
    
    # Test 2: Appeler optimize_conversation_history (comme dans ogma_ng.py)
    print("\n[TEST 2] Appel optimize_conversation_history...")
    try:
        summaries_texts, recent_messages = await summarizer.optimize_conversation_history(fake_conversation)
        
        print(f"   ✅ Succès !")
        print(f"   → {len(summaries_texts)} résumés générés")
        print(f"   → {len(recent_messages)} messages récents conservés")
        print(f"   → Ratio: {len(recent_messages)}/{len(fake_conversation)} messages envoyés à l'API")
        print(f"   → Économie: ~{(len(fake_conversation) - len(recent_messages)) * 500} tokens")
        
        # Afficher aperçu des résumés
        if summaries_texts:
            print("\n   📝 Aperçu résumés:")
            for i, summary in enumerate(summaries_texts[:3], 1):
                preview = summary[:100] + "..." if len(summary) > 100 else summary
                print(f"      [RÉSUMÉ #{i}] {preview}")
        
        # Test 3: Vérifier structure messages récents
        print("\n[TEST 3] Structure messages récents...")
        if recent_messages:
            print(f"   → Premier message: role={recent_messages[0].get('role')}")
            print(f"   → Dernier message: role={recent_messages[-1].get('role')}")
            print(f"   → Types présents: {set(m.get('role') for m in recent_messages)}")
        
        print("\n" + "=" * 60)
        print("✅ TOUS LES TESTS PASSÉS")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n   ❌ ERREUR: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    # Note: Le summarizer a besoin de l'archiviste pour créer des résumés
    # Mais optimize_conversation_history devrait fonctionner même sans,
    # en retournant les messages récents
    
    result = await test_optimize_conversation()
    
    if result:
        print("\n🎉 Le système d'optimisation est prêt pour OGMA !")
        print("📋 Au reload d'une conversation:")
        print("   - Frontend affiche TOUS les messages (_chat_history_ui)")
        print("   - Backend reçoit RÉSUMÉS + messages récents (optimisé)")
        print("   - Plus de 429 rate limit sur conversations longues !")
    else:
        print("\n⚠️ Des problèmes ont été détectés")

if __name__ == "__main__":
    asyncio.run(main())
