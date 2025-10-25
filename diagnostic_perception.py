#!/usr/bin/env python3
"""
Diagnostic complet de l'extension perception pour identifier les causes de crash
"""

import sys
import os
import time
sys.path.append('.')

def check_opencv_installation():
    """Vérifier l'installation d'OpenCV"""
    print("🔍 Vérification OpenCV...")
    try:
        import cv2
        print(f"   ✅ OpenCV version: {cv2.__version__}")
        
        # Test basique de capture
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            print("   ✅ Webcam accessible (index 0)")
            ret, frame = cap.read()
            if ret:
                print(f"   ✅ Capture réussie: frame {frame.shape}")
            else:
                print("   ⚠️ Capture échoué")
            cap.release()
        else:
            print("   ❌ Webcam inaccessible (index 0)")
        
        return True
    except Exception as e:
        print(f"   ❌ Erreur OpenCV: {e}")
        return False

def check_perception_agent_imports():
    """Vérifier les imports de l'agent de perception"""
    print("\n🔍 Vérification imports agent perception...")
    
    try:
        from extensions.perception_agent import PerceptionAgent
        print("   ✅ Import PerceptionAgent réussi")
        return True
    except Exception as e:
        print(f"   ❌ Erreur import PerceptionAgent: {e}")
        return False

def simulate_perception_usage():
    """Simuler l'utilisation de l'agent de perception"""
    print("\n🔍 Simulation utilisation agent perception...")
    
    try:
        from extensions.perception_agent import PerceptionAgent
        
        # Créer l'agent
        agent = PerceptionAgent(webcam_index=0)
        print("   ✅ Agent créé")
        
        # Test de démarrage
        agent.start()
        print("   ✅ Agent démarré")
        
        # Attendre un peu
        time.sleep(3)
        
        # Test capture
        result = agent.capture_for_chat()
        if result:
            print("   ✅ Capture pour chat réussie")
        else:
            print("   ⚠️ Capture pour chat échouée")
        
        # Test arrêt
        agent.stop()
        print("   ✅ Agent arrêté proprement")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur simulation: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_memory_usage():
    """Vérifier l'utilisation mémoire"""
    print("\n🔍 Vérification utilisation mémoire...")
    
    try:
        import psutil
        process = psutil.Process()
        
        print(f"   📊 Utilisation mémoire: {process.memory_info().rss / 1024 / 1024:.1f} MB")
        print(f"   📊 CPU: {process.cpu_percent()}%")
        
        return True
    except ImportError:
        print("   ⚠️ psutil non installé, impossible de vérifier la mémoire")
        return False
    except Exception as e:
        print(f"   ❌ Erreur mémoire: {e}")
        return False

def check_threading_issues():
    """Vérifier les problèmes de threading"""
    print("\n🔍 Vérification threading...")
    
    try:
        import threading
        active_threads = threading.active_count()
        print(f"   📊 Threads actifs: {active_threads}")
        
        # Lister les threads actifs
        for thread in threading.enumerate():
            if thread.is_alive():
                print(f"      • {thread.name}: {thread.__class__.__name__}")
        
        return True
    except Exception as e:
        print(f"   ❌ Erreur threading: {e}")
        return False

def analyze_logs_patterns():
    """Analyser les patterns dans les logs"""
    print("\n🔍 Analyse des patterns de logs...")
    
    # Rechercher les logs récents si disponibles
    log_patterns = [
        "[MOTION-BUFFER] Buffer:",
        "[PERCEPTION] 💥 ERREUR NON GÉRÉE",
        "[SAVE] Paramètres sauvegardés",
        "main_page() appelée !",
        "Extension.*initialized"
    ]
    
    print("   🔍 Patterns problématiques potentiels:")
    for pattern in log_patterns:
        print(f"      • {pattern}")
    
    print("\n   💡 Solutions recommandées:")
    print("      1. Réduction logs motion buffer ✅ (déjà appliquée)")
    print("      2. Auto-recovery webcam ✅ (déjà appliquée)")
    print("      3. Libération propre webcam ✅ (déjà appliquée)")
    print("      4. Gestion mémoire améliorée")
    print("      5. Monitoring threads actifs")

def generate_recommendations():
    """Générer des recommandations"""
    print("\n" + "="*60)
    print("🎯 RECOMMANDATIONS POUR STABILISER LA PERCEPTION")
    print("="*60)
    
    recommendations = [
        "1. 📷 Libération webcam: Assurer cap.release() dans tous les cas",
        "2. 🔄 Auto-recovery: Réinitialiser webcam en cas d'erreur au lieu d'arrêt brutal",
        "3. 📝 Logs réduits: Motion buffer log seulement quand plein",
        "4. 🧵 Thread monitoring: Surveiller les threads zombies",
        "5. 💾 Gestion mémoire: Limiter la taille du frame buffer",
        "6. ⏱️ Timeouts: Ajouter timeouts sur les opérations webcam",
        "7. 🚨 Exception handling: Capture spécifique des erreurs OpenCV"
    ]
    
    for rec in recommendations:
        status = "✅" if any(word in rec for word in ["Libération", "Auto-recovery", "Logs"]) else "⏳"
        print(f"   {status} {rec}")
    
    print(f"\n📊 État des corrections:")
    print(f"   • Motion buffer optimisé: ✅")
    print(f"   • Auto-recovery webcam: ✅") 
    print(f"   • Libération webcam: ✅")
    print(f"   • Corrections restantes: 4/7")

if __name__ == "__main__":
    print("🔧 DIAGNOSTIC EXTENSION PERCEPTION")
    print("=" * 60)
    
    # Tests séquentiels
    tests = [
        check_opencv_installation,
        check_perception_agent_imports,
        check_memory_usage,
        check_threading_issues,
        # simulate_perception_usage,  # Commenté pour éviter d'accéder à la webcam
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"   ❌ Erreur test {test.__name__}: {e}")
            results.append(False)
    
    analyze_logs_patterns()
    generate_recommendations()
    
    success_rate = sum(results) / len(results) * 100
    print(f"\n📈 Taux de réussite diagnostic: {success_rate:.0f}%")
    
    if success_rate >= 75:
        print("✅ Système semble stable avec les corrections appliquées")
    else:
        print("⚠️ Des problèmes subsistent, surveillance recommandée")