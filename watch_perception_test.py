# watch_perception_test.py

"""
Surveillance simple des logs Perception pendant les tests
"""

import time
import subprocess
import sys
from datetime import datetime

def watch_ogma_logs():
    """Surveille les logs OGMA en temps réel"""
    print("👁️ === SURVEILLANCE PERCEPTION (sans TTS) ===")
    print(f"⏰ Début surveillance: {datetime.now().strftime('%H:%M:%S')}")
    print("💡 Actions à faire dans OGMA:")
    print("   1. Activer Perception (bouton 👁️)")
    print("   2. Laisser tourner 2-5 minutes") 
    print("   3. Tester captures manuelles")
    print("⏹️ Ctrl+C pour arrêter")
    print("=" * 50)
    
    start_time = time.time()
    last_activity = time.time()
    
    try:
        # Surveiller les processus Python
        while True:
            current_time = time.time()
            elapsed = current_time - start_time
            
            # Check toutes les 5 secondes
            if current_time - last_activity >= 5:
                try:
                    # Vérifier si OGMA tourne encore
                    result = subprocess.run(
                        ['powershell', '-Command', 'Get-Process python -ErrorAction SilentlyContinue | Measure-Object | Select-Object -ExpandProperty Count'],
                        capture_output=True, text=True, timeout=3
                    )
                    
                    python_processes = int(result.stdout.strip() or 0)
                    
                    print(f"⏱️ [{elapsed:.0f}s] Processus Python actifs: {python_processes}")
                    
                    if python_processes == 0:
                        print("💀 OGMA semble avoir planté !")
                        break
                    
                    # Statistiques
                    if elapsed % 30 == 0 and elapsed > 0:  # Toutes les 30s
                        print(f"📊 [{elapsed:.0f}s] ✅ OGMA stable - Perception fonctionne")
                        
                except Exception as e:
                    print(f"⚠️ Erreur surveillance: {e}")
                
                last_activity = current_time
            
            time.sleep(1)
            
    except KeyboardInterrupt:
        print(f"\n⏹️ Surveillance arrêtée après {elapsed:.0f}s")
        if elapsed > 120:  # Plus de 2 minutes
            print("🎉 SUCCÈS: Perception stable sans TTS !")
        else:
            print("⚠️ Test interrompu trop tôt")

def check_ogma_status():
    """Vérifie rapidement si OGMA tourne"""
    try:
        import requests
        response = requests.get("http://127.0.0.1:8080", timeout=3)
        if response.status_code == 200:
            print("✅ OGMA accessible sur http://127.0.0.1:8080")
            return True
        else:
            print(f"⚠️ OGMA répond avec code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ OGMA non accessible: {e}")
        return False

if __name__ == "__main__":
    print("🧪 TEST PERCEPTION SANS TTS")
    print()
    
    # Vérifier OGMA
    if not check_ogma_status():
        print("💡 Lancez d'abord: python launch_ogma.py")
        sys.exit(1)
    
    print("🎯 OGMA détecté - commencer surveillance...")
    watch_ogma_logs()