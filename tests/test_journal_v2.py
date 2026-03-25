#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test Suite Journal de Bord v2.0
Validation des nouvelles fonctionnalités :
- Auto-archivage tous les 40 messages
- Détection états actifs
- Micro-entrées automatiques
- Injection contexte ÉTATS_ACTIFS
- Continuation conversations
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

# Ajouter le répertoire racine au path
sys.path.insert(0, str(Path(__file__).parent))

# Import des composants Journal
from extensions.journal_de_bord import config as journal_config
from extensions.journal_de_bord.json_manager import JSONManager
from extensions.journal_de_bord.entry_generator import EntryGenerator
from extensions.journal_de_bord.context_provider import ContextProvider

# Mock simple pour ArchivisteController
class MockArchiviste:
    """Mock Archiviste pour tests sans API"""
    
    def __init__(self):
        self.context_length = 4096
    
    async def call_chat_api(self, messages, max_tokens=500, context_length=4096, temperature=0.7):
        """Simule un appel Archiviste"""
        prompt = messages[0]['content'] if messages else ""
        
        # Détection type de requête
        if "ÉTATS ACTIFS" in prompt or "états_détectés" in prompt:
            # Réponse JSON pour détection états
            return ('''
{
  "états_détectés": [
    {
      "category": "santé",
      "description": "Grippe en cours - symptômes depuis 3 jours",
      "importance": "high",
      "confidence": 0.85
    },
    {
      "category": "projet",
      "description": "Développement Journal v2.0 en cours",
      "importance": "medium",
      "confidence": 0.92
    }
  ]
}
''', None)
        
        elif "MICRO-RÉSUMÉ" in prompt:
            # Micro-résumé court
            return ("Discussion technique sur implémentation auto-archivage Journal v2.0.", None)
        
        elif "Mets à jour ce résumé" in prompt:
            # Mise à jour résumé existant
            return ("Discussion technique Journal v2.0 + tests validation nouvelles fonctionnalités.", None)
        
        else:
            # Résumé standard
            return ("Conversation de test pour validation système Journal de Bord v2.0 avec nouvelles fonctionnalités.", None)


class TestJournalV2:
    """Suite de tests pour Journal v2.0"""
    
    def __init__(self):
        self.config = None
        self.json_manager = None
        self.entry_generator = None
        self.context_provider = None
        self.mock_archiviste = MockArchiviste()
        
        # Résultats tests
        self.results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "errors": []
        }
    
    def setup(self):
        """Initialisation des composants"""
        print("\n" + "="*70)
        print("🧪 JOURNAL DE BORD v2.0 - TEST SUITE")
        print("="*70)
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        try:
            # Config
            config_file = Path("data/journal_settings.json")
            self.config = journal_config.JournalConfig(config_file)
            
            # Activer toutes les nouvelles features pour les tests
            self.config.set("enable_active_states", True)
            self.config.set("auto_archive_enabled", True)
            self.config.set("auto_archive_frequency", 40)
            self.config.set("update_same_conversation", True)
            
            print("✅ Configuration chargée")
            
            # JSON Manager
            data_dir = Path("extensions/journal_de_bord/data")
            self.json_manager = JSONManager(self.config, data_dir)
            print(f"✅ JSON Manager initialisé ({self.json_manager.stats['total_entries']} entrées)")
            
            # Entry Generator avec mock Archiviste
            self.entry_generator = EntryGenerator(self.mock_archiviste, self.config)
            print("✅ Entry Generator initialisé (Mock Archiviste)")
            
            # Context Provider
            self.context_provider = ContextProvider(self.json_manager, self.config)
            print("✅ Context Provider initialisé")
            
            print("\n" + "-"*70 + "\n")
            return True
            
        except Exception as e:
            print(f"❌ ERREUR Setup: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def assert_test(self, test_name: str, condition: bool, details: str = ""):
        """Assertion avec tracking résultats"""
        self.results["total"] += 1
        
        if condition:
            self.results["passed"] += 1
            status = "✅ PASS"
        else:
            self.results["failed"] += 1
            status = "❌ FAIL"
            self.results["errors"].append(f"{test_name}: {details}")
        
        print(f"{status} | {test_name}")
        if details and not condition:
            print(f"     └─ {details}")
    
    async def test_1_json_manager_states(self):
        """Test #1: Méthodes de gestion états actifs"""
        print("📋 TEST #1: JSON Manager - Gestion États Actifs")
        print("-"*70)
        
        try:
            # Test get_active_states
            états = self.json_manager.get_active_states()
            self.assert_test(
                "get_active_states() retourne structure valide",
                isinstance(états, dict) and "metadata" in états and "states" in états,
                f"Structure reçue: {type(états)}"
            )
            
            # Test update_active_state
            success = self.json_manager.update_active_state(
                category="test",
                new_state={
                    "description": "État de test automatique",
                    "importance": "low",
                    "source_entry_id": "test-001"
                }
            )
            self.assert_test(
                "update_active_state() crée nouvel état",
                success,
                "Échec création état"
            )
            
            # Vérifier qu'il est bien créé
            états_after = self.json_manager.get_active_states()
            test_states = [s for s in états_after["states"] if s.get("category") == "test"]
            self.assert_test(
                "État créé présent dans get_active_states()",
                len(test_states) > 0,
                f"Trouvé {len(test_states)} états 'test'"
            )
            
            if test_states:
                state_id = test_states[-1]["state_id"]
                
                # Test add_state_to_history
                success_history = self.json_manager.add_state_to_history(
                    state_id=state_id,
                    action="updated",
                    entry_id="test-002"
                )
                self.assert_test(
                    "add_state_to_history() ajoute entrée",
                    success_history,
                    f"État ID: {state_id}"
                )
                
                # Test resolve_state
                success_resolve = self.json_manager.resolve_state(
                    state_id=state_id,
                    resolution_note="Test résolution automatique",
                    entry_id="test-003"
                )
                self.assert_test(
                    "resolve_state() marque comme résolu",
                    success_resolve,
                    f"État ID: {state_id}"
                )
            
            # Test get_unresolved_states
            unresolved = self.json_manager.get_unresolved_states()
            self.assert_test(
                "get_unresolved_states() filtre correctement",
                isinstance(unresolved, list),
                f"Type retourné: {type(unresolved)}"
            )
            
            # L'état de test doit être résolu maintenant
            test_unresolved = [s for s in unresolved if s.get("category") == "test"]
            self.assert_test(
                "État résolu n'apparaît pas dans get_unresolved_states()",
                len(test_unresolved) == 0,
                f"Trouvé {len(test_unresolved)} états test non résolus"
            )
            
        except Exception as e:
            self.assert_test("Test JSON Manager États", False, f"Exception: {e}")
            import traceback
            traceback.print_exc()
        
        print()
    
    async def test_2_micro_entry_generation(self):
        """Test #2: Génération micro-entrées"""
        print("🤏 TEST #2: Génération Micro-Entrées Automatiques")
        print("-"*70)
        
        try:
            # Simuler historique conversation (plus long pour dépasser 50 tokens)
            conversation_history = [
                {"role": "user", "content": "Bonjour Luna, comment vas-tu aujourd'hui ? J'espère que tout va bien de ton côté."},
                {"role": "assistant", "content": "Bonjour Yohan ! Je vais très bien merci, c'est gentil de demander. Comment puis-je t'aider aujourd'hui ? As-tu des questions ou des projets sur lesquels tu travailles ?"},
                {"role": "user", "content": "Je voudrais tester le nouveau système d'auto-archivage du Journal de Bord v2.0 que nous avons développé ensemble. C'est une fonctionnalité importante."},
                {"role": "assistant", "content": "Excellente idée ! Le système d'auto-archivage est très utile. Il génère automatiquement des micro-entrées toutes les 40 interactions pour garder une trace de nos conversations sans intervention manuelle. C'est un vrai gain de temps !"},
                {"role": "user", "content": "Oui exactement. J'aimerais voir si la détection automatique des états actifs fonctionne bien aussi."},
                {"role": "assistant", "content": "La détection d'états actifs est très performante. L'Archiviste analyse le contexte et identifie automatiquement les éléments importants à suivre comme la santé, les projets en cours, l'humeur, etc."},
            ]
            
            # Générer micro-entrée
            micro_entry = await self.entry_generator.generate_micro_entry(
                conversation_id="test-conv-001",
                conversation_history=conversation_history,
                json_manager=self.json_manager,
                participants=["user", "assistant"]
            )
            
            self.assert_test(
                "generate_micro_entry() retourne entrée valide",
                micro_entry is not None and isinstance(micro_entry, dict),
                f"Retour: {type(micro_entry)}"
            )
            
            if micro_entry:
                # Vérifier flag auto_generated
                self.assert_test(
                    "Micro-entrée a flag auto_generated=True",
                    micro_entry.get("auto_generated") == True,
                    f"auto_generated: {micro_entry.get('auto_generated')}"
                )
                
                # Vérifier importance=low
                self.assert_test(
                    "Micro-entrée a importance='low'",
                    micro_entry.get("importance") == "low",
                    f"importance: {micro_entry.get('importance')}"
                )
                
                # Vérifier longueur résumé
                summary = micro_entry.get("summary", "")
                token_estimate = len(summary.split()) * 0.75
                self.assert_test(
                    "Résumé micro-entrée < 100 tokens",
                    token_estimate < 100,
                    f"Estimé: {token_estimate} tokens ({len(summary)} chars)"
                )
                
                # Vérifier présence conversation_id
                self.assert_test(
                    "Micro-entrée contient conversation_id",
                    micro_entry.get("conversation_id") == "test-conv-001",
                    f"conversation_id: {micro_entry.get('conversation_id')}"
                )
        
        except Exception as e:
            self.assert_test("Test Micro-Entry", False, f"Exception: {e}")
            import traceback
            traceback.print_exc()
        
        print()
    
    async def test_3_active_states_detection(self):
        """Test #3: Détection automatique états actifs"""
        print("🎯 TEST #3: Détection Automatique États Actifs")
        print("-"*70)
        
        try:
            # Contexte avec informations d'état
            conversation_context = """
Conversation avec l'utilisateur Yohan.

User: J'ai attrapé une grippe il y a 3 jours, j'ai de la fièvre.
Assistant: Je suis désolé d'apprendre ça. Prends soin de toi et repose-toi bien.

User: Je travaille aussi sur le développement du Journal v2.0 pour OGMA.
Assistant: C'est un super projet ! Comment avance l'implémentation ?
"""
            
            # Détecter états
            detected_states = await self.entry_generator.detect_active_states(
                conversation_context=conversation_context,
                entry_id="test-detection-001",
                json_manager=self.json_manager
            )
            
            self.assert_test(
                "detect_active_states() retourne liste",
                isinstance(detected_states, list),
                f"Type: {type(detected_states)}"
            )
            
            self.assert_test(
                "Au moins 1 état détecté",
                len(detected_states) > 0,
                f"Détectés: {len(detected_states)}"
            )
            
            if detected_states:
                # Vérifier qu'un état santé a été détecté
                health_states = [s for s in detected_states if s.get("category") == "santé"]
                self.assert_test(
                    "État 'santé' détecté (grippe)",
                    len(health_states) > 0,
                    f"États santé: {len(health_states)}"
                )
                
                # Vérifier qu'un état projet a été détecté
                project_states = [s for s in detected_states if s.get("category") == "projet"]
                self.assert_test(
                    "État 'projet' détecté (Journal v2.0)",
                    len(project_states) > 0,
                    f"États projet: {len(project_states)}"
                )
                
                # Vérifier confidence
                for state in detected_states:
                    confidence = state.get("confidence", 0.0)
                    self.assert_test(
                        f"État '{state.get('category')}' a confidence >= 0.6",
                        confidence >= 0.6,
                        f"Confidence: {confidence}"
                    )
                    break  # Test 1 seul pour ne pas spammer
        
        except Exception as e:
            self.assert_test("Test Détection États", False, f"Exception: {e}")
            import traceback
            traceback.print_exc()
        
        print()
    
    async def test_4_continuation_detection(self):
        """Test #4: Détection continuation conversation"""
        print("🔄 TEST #4: Détection Continuation Conversation")
        print("-"*70)
        
        try:
            # Créer une première entrée
            conv_id = "test-continuation-001"
            
            first_history = [
                {"role": "user", "content": "Bonjour Luna ! Aujourd'hui je voudrais débuter une conversation de test très complète pour valider le système de continuation du Journal de Bord v2.0. C'est vraiment important que cette fonctionnalité fonctionne correctement car elle permet d'économiser beaucoup d'espace en fusionnant les conversations qui se suivent rapidement."},
                {"role": "assistant", "content": "Bonjour Yohan ! Excellente idée de tester cette fonctionnalité en profondeur. La conversation test est maintenant démarrée avec succès. Je vais suivre attentivement cette discussion pour observer comment le système gère intelligemment les continuations dans le Journal v2.0. Cette capacité de fusion est effectivement très intéressante et pratique pour maintenir un historique cohérent sans dupliquer l'information."}
            ]
            
            first_entry = await self.entry_generator.generate_micro_entry(
                conversation_id=conv_id,
                conversation_history=first_history,
                json_manager=self.json_manager
            )
            
            self.assert_test(
                "Première entrée créée",
                first_entry is not None,
                f"Entry ID: {first_entry.get('entry_id') if first_entry else 'None'}"
            )
            
            if first_entry:
                # Attendre un peu (simuler continuation rapide)
                await asyncio.sleep(0.5)
                
                # Créer continuation (même conversation_id, < 2h)
                continuation_history = first_history + [
                    {"role": "user", "content": "Suite de la conversation pour tester la détection de continuation. Est-ce que le système va bien fusionner les deux parties ?"},
                    {"role": "assistant", "content": "Continuation détectée avec succès ! Le système devrait maintenant fusionner cette partie avec la précédente pour créer un résumé complet et cohérent de toute notre échange."}
                ]
                
                second_entry = await self.entry_generator.generate_micro_entry(
                    conversation_id=conv_id,
                    conversation_history=continuation_history,
                    json_manager=self.json_manager
                )
                
                self.assert_test(
                    "Continuation traitée (retourne entrée)",
                    second_entry is not None,
                    "Aucune entrée retournée"
                )
                
                # Vérifier que le résumé a été mis à jour (devrait contenir les deux parties)
                if second_entry:
                    updated_summary = second_entry.get("summary", "")
                    self.assert_test(
                        "Résumé mis à jour contient plus d'infos",
                        len(updated_summary) > len(first_entry.get("summary", "")),
                        f"Original: {len(first_entry.get('summary', ''))} chars, MAJ: {len(updated_summary)} chars"
                    )
                    
                    # Vérifier métadata update_count
                    update_count = second_entry.get("metadata", {}).get("update_count", 0)
                    self.assert_test(
                        "Metadata contient update_count",
                        update_count > 0,
                        f"update_count: {update_count}"
                    )
        
        except Exception as e:
            self.assert_test("Test Continuation", False, f"Exception: {e}")
            import traceback
            traceback.print_exc()
        
        print()
    
    async def test_5_context_injection(self):
        """Test #5: Injection ÉTATS_ACTIFS dans contexte"""
        print("💉 TEST #5: Injection ÉTATS_ACTIFS dans Contexte")
        print("-"*70)
        
        try:
            # Créer quelques états actifs de test
            self.json_manager.update_active_state(
                category="santé",
                new_state={
                    "description": "Test état santé pour injection",
                    "importance": "high",
                    "source_entry_id": "test-inject-001"
                }
            )
            
            self.json_manager.update_active_state(
                category="projet",
                new_state={
                    "description": "Test état projet pour injection",
                    "importance": "medium",
                    "source_entry_id": "test-inject-002"
                }
            )
            
            # Générer contexte
            context = self.context_provider.get_recent_context_with_cascade(max_entries=3)
            
            self.assert_test(
                "get_recent_context_with_cascade() retourne contexte",
                context is not None and len(context) > 0,
                f"Longueur: {len(context) if context else 0} chars"
            )
            
            if context:
                # Vérifier présence section ÉTATS_ACTIFS
                self.assert_test(
                    "Contexte contient section 'ÉTATS ACTIFS'",
                    "ÉTATS ACTIFS" in context,
                    "Section manquante"
                )
                
                # Vérifier présence des états créés
                self.assert_test(
                    "Contexte contient état 'santé'",
                    "santé" in context.lower() or "🏥" in context,
                    "État santé manquant"
                )
                
                self.assert_test(
                    "Contexte contient état 'projet'",
                    "projet" in context.lower() or "📋" in context,
                    "État projet manquant"
                )
                
                # Vérifier ordre (ÉTATS_ACTIFS doit être en premier)
                states_pos = context.find("ÉTATS ACTIFS")
                temporal_pos = context.find("CONTEXTE TEMPOREL")
                
                if states_pos != -1 and temporal_pos != -1:
                    self.assert_test(
                        "ÉTATS_ACTIFS apparaît AVANT CONTEXTE TEMPOREL",
                        states_pos < temporal_pos,
                        f"Positions: ÉTATS={states_pos}, TEMPOREL={temporal_pos}"
                    )
                
                # Afficher un aperçu du contexte
                print(f"\n📄 Aperçu contexte généré ({len(context)} chars):")
                print("-"*70)
                print(context[:500] + "..." if len(context) > 500 else context)
                print("-"*70 + "\n")
        
        except Exception as e:
            self.assert_test("Test Injection Contexte", False, f"Exception: {e}")
            import traceback
            traceback.print_exc()
        
        print()
    
    async def test_6_config_parameters(self):
        """Test #6: Validation paramètres configuration v2.0"""
        print("⚙️ TEST #6: Validation Configuration v2.0")
        print("-"*70)
        
        try:
            # Vérifier présence nouveaux paramètres
            params_v2 = [
                "auto_archive_enabled",
                "auto_archive_frequency",
                "enable_active_states",
                "max_active_states",
                "archive_retention_months",
                "faiss_transfer_months",
                "auto_archive_min_tokens",
                "update_same_conversation",
                "same_conversation_window_hours",
                "state_auto_resolve_days"
            ]
            
            for param in params_v2:
                value = self.config.get(param)
                self.assert_test(
                    f"Paramètre '{param}' existe",
                    value is not None,
                    f"Valeur: {value}"
                )
            
            # Vérifier valeurs par défaut cohérentes
            self.assert_test(
                "auto_archive_frequency = 40",
                self.config.get("auto_archive_frequency") == 40,
                f"Valeur: {self.config.get('auto_archive_frequency')}"
            )
            
            self.assert_test(
                "max_active_states = 10",
                self.config.get("max_active_states") == 10,
                f"Valeur: {self.config.get('max_active_states')}"
            )
            
            self.assert_test(
                "same_conversation_window_hours = 2",
                self.config.get("same_conversation_window_hours") == 2,
                f"Valeur: {self.config.get('same_conversation_window_hours')}"
            )
        
        except Exception as e:
            self.assert_test("Test Configuration", False, f"Exception: {e}")
            import traceback
            traceback.print_exc()
        
        print()
    
    def print_results(self):
        """Affiche résumé des résultats"""
        print("\n" + "="*70)
        print("📊 RÉSULTATS DES TESTS")
        print("="*70)
        
        total = self.results["total"]
        passed = self.results["passed"]
        failed = self.results["failed"]
        
        success_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"Total: {total} tests")
        print(f"✅ Réussis: {passed} ({success_rate:.1f}%)")
        print(f"❌ Échoués: {failed}")
        print()
        
        if failed > 0:
            print("❌ ERREURS DÉTECTÉES:")
            print("-"*70)
            for error in self.results["errors"]:
                print(f"  • {error}")
            print()
        
        # Verdict final
        if failed == 0:
            print("🎉 TOUS LES TESTS SONT PASSÉS !")
            print("✅ Journal de Bord v2.0 est OPÉRATIONNEL")
        else:
            print("⚠️ CERTAINS TESTS ONT ÉCHOUÉ")
            print("🔧 Corrections nécessaires avant mise en production")
        
        print("="*70 + "\n")
        
        return failed == 0
    
    async def run_all_tests(self):
        """Exécute tous les tests"""
        if not self.setup():
            print("❌ Impossible de lancer les tests (setup échoué)")
            return False
        
        # Exécution séquentielle des tests
        await self.test_1_json_manager_states()
        await self.test_2_micro_entry_generation()
        await self.test_3_active_states_detection()
        await self.test_4_continuation_detection()
        await self.test_5_context_injection()
        await self.test_6_config_parameters()
        
        # Résultats
        return self.print_results()


async def main():
    """Point d'entrée principal"""
    tester = TestJournalV2()
    success = await tester.run_all_tests()
    
    # Code de sortie
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
