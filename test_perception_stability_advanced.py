# test_perception_stability_advanced.py

"""
Test avancé de stabilité Perception avec surveillance des redémarrages
"""

import time
import threading
import psutil
import os
import sys
from datetime import datetime

def monitor_perception_status():
    """Surveille le statut de Perception en continu"""
    print("🔍 === SURVEILLANCE PERCEPTION AVANCÉE ===")
    
    try:
        sys.path.append('.')
        from extensions.perception_ui import get_perception_ui
        from tts_conflict_free import get_conflict_free_tts
        
        perception_ui = get_perception_ui()
        tts_safe = get_conflict_free_tts()
        
        # Initialiser TTS
        tts_safe.initialize()
        
        # Stats de surveillance
        stats = {
            'starts': 0,
            'stops': 0,
            'crashes': 0,
            'tts_calls': 0,
            'perception_restarts': 0,
            'cpu_peaks': [],
            'memory_growth': []
        }
        
        start_time = time.time()
        last_status = None
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        print(f"[MONITOR] Mémoire initiale: {initial_memory:.1f} MB")
        print(f"[MONITOR] CPU initial: {psutil.cpu_percent()}%")
        print()
        
        # Surveillance pendant 60 secondes
        for i in range(60):
            current_time = datetime.now().strftime("%H:%M:%S")
            
            # État Perception
            is_active = perception_ui.is_enabled and perception_ui.perception_agent is not None
            
            # Détecter changement d'état
            if last_status != is_active:
                if is_active:
                    stats['starts'] += 1
                    print(f"[{current_time}] 🟢 PERCEPTION DÉMARRÉE (#{stats['starts']})")
                else:
                    stats['stops'] += 1
                    print(f"[{current_time}] 🔴 PERCEPTION ARRÊTÉE (#{stats['stops']})")
                    
                    # Si arrêt non prévu = crash
                    if i > 5 and stats['stops'] > stats['starts']:
                        stats['crashes'] += 1
                        print(f"[{current_time}] 💥 CRASH DÉTECTÉ ! (#{stats['crashes']})")
                
                last_status = is_active
            
            # Métriques système
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory_mb = process.memory_info().rss / 1024 / 1024
            memory_growth = memory_mb - initial_memory
            
            if cpu_percent > 50:
                stats['cpu_peaks'].append((i, cpu_percent))
                print(f"[{current_time}] ⚠️ CPU élevé: {cpu_percent:.1f}%")
            
            if memory_growth > 100:  # +100MB = problème
                stats['memory_growth'].append((i, memory_growth))
                print(f"[{current_time}] ⚠️ Mémoire élevée: +{memory_growth:.1f}MB")
            
            # Test TTS périodique (simulation utilisation)
            if i % 10 == 0 and i > 0:
                stats['tts_calls'] += 1
                try:
                    from tts_conflict_free import speak_safe, set_perception_active
                    
                    # Simuler activation Perception
                    set_perception_active(True)
                    time.sleep(0.1)
                    
                    # Test TTS
                    success = speak_safe(f"Test stabilité {stats['tts_calls']}")
                    
                    # Désactiver Perception
                    set_perception_active(False)
                    
                    if success:
                        print(f"[{current_time}] 🔊 TTS #{stats['tts_calls']} réussi")
                    else:
                        print(f"[{current_time}] ⚠️ TTS #{stats['tts_calls']} échoué")
                        
                except Exception as e:
                    print(f"[{current_time}] ❌ Erreur TTS: {e}")
            
            # Affichage status compact toutes les 5s
            if i % 5 == 0:
                status_icon = "🟢" if is_active else "⚪"
                print(f"[{current_time}] {status_icon} T+{i}s | CPU:{cpu_percent:.0f}% | RAM:{memory_growth:+.0f}MB | TTS:{stats['tts_calls']}")
            
            time.sleep(1)
        
        # Rapport final
        total_time = time.time() - start_time
        final_memory = process.memory_info().rss / 1024 / 1024
        total_memory_growth = final_memory - initial_memory
        
        print("\n" + "="*50)
        print("📊 RAPPORT SURVEILLANCE 60s")
        print("="*50)
        print(f"Durée totale: {total_time:.1f}s")
        print(f"Démarrages Perception: {stats['starts']}")
        print(f"Arrêts Perception: {stats['stops']}")
        print(f"Crashes détectés: {stats['crashes']}")
        print(f"Redémarrages: {stats['stops'] - 1 if stats['stops'] > 1 else 0}")
        print(f"Tests TTS: {stats['tts_calls']}")
        print(f"Pics CPU (>50%): {len(stats['cpu_peaks'])}")
        print(f"Croissance mémoire: +{total_memory_growth:.1f}MB")
        print()
        
        # Diagnostic
        if stats['crashes'] > 0:
            print("🚨 PROBLÈME: Crashes détectés")
            print("   → Perception instable, nécessite investigation")
        elif stats['stops'] > stats['starts']:
            print("🚨 PROBLÈME: Plus d'arrêts que de démarrages")
            print("   → Arrêts non contrôlés détectés")
        elif len(stats['cpu_peaks']) > 5:
            print("⚠️ ATTENTION: Nombreux pics CPU")
            print("   → Possible surcharge système")
        elif total_memory_growth > 200:
            print("⚠️ ATTENTION: Forte croissance mémoire")
            print("   → Possible fuite mémoire")
        else:
            print("✅ EXCELLENT: Stabilité confirmée")
            print("   → Perception fonctionne normalement")
        
        # Nettoyage
        tts_safe.stop()
        
        return stats['crashes'] == 0
        
    except Exception as e:
        print(f"❌ Erreur surveillance: {e}")
        return False

def main():
    print("🎯 === TEST STABILITÉ PERCEPTION AVANCÉ ===")
    print()
    
    # Démarrer surveillance
    success = monitor_perception_status()
    
    print(f"\n🎯 RÉSULTAT FINAL: {'✅ STABLE' if success else '❌ INSTABLE'}")

if __name__ == "__main__":
    main()