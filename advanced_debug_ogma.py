# advanced_debug_ogma.py

"""
Diagnostic avancé des problèmes OGMA
Focus sur les boucles infinies et conflits NiceGUI
"""

import psutil
import time
import threading
import subprocess
import sys
from datetime import datetime

class OGMAHealthMonitor:
    """Moniteur de santé OGMA avancé"""
    
    def __init__(self):
        self.monitoring = False
        self.stats = {
            "start_time": None,
            "main_page_calls": 0,
            "last_main_page": None,
            "nicegui_warnings": 0,
            "memory_start": 0,
            "memory_current": 0,
            "perception_active": False,
            "crashes": 0
        }
        
    def monitor_ogma_process(self, duration=300):  # 5 minutes max
        """Surveille le processus OGMA en temps réel"""
        print("🔍 === DIAGNOSTIC AVANCÉ OGMA ===")
        print(f"⏰ Début: {datetime.now().strftime('%H:%M:%S')}")
        print("📊 Surveillance: mémoire, CPU, boucles infinies")
        print("⏹️ Ctrl+C pour arrêter")
        print("=" * 50)
        
        self.monitoring = True
        self.stats["start_time"] = time.time()
        
        # Trouver processus Python OGMA
        ogma_process = None
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['name'] == 'python.exe':
                        cmdline = ' '.join(proc.info['cmdline'] or [])
                        if 'launch_ogma.py' in cmdline or 'ogma_ng.py' in cmdline:
                            ogma_process = psutil.Process(proc.info['pid'])
                            self.stats["memory_start"] = ogma_process.memory_info().rss / 1024 / 1024
                            print(f"🎯 OGMA trouvé: PID {proc.info['pid']}, RAM: {self.stats['memory_start']:.1f} MB")
                            break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            print(f"⚠️ Erreur recherche processus: {e}")
        
        if not ogma_process:
            print("❌ Processus OGMA non trouvé")
            return
        
        # Monitoring loop
        last_check = 0
        loop_count = 0
        
        try:
            while self.monitoring and (time.time() - self.stats["start_time"]) < duration:
                current_time = time.time() - self.stats["start_time"]
                
                if current_time - last_check >= 5:  # Check toutes les 5s
                    try:
                        # Vérifier si processus existe encore
                        if not ogma_process.is_running():
                            print(f"💀 [{current_time:.0f}s] OGMA processus mort !")
                            self.stats["crashes"] += 1
                            break
                        
                        # Stats processus
                        cpu_percent = ogma_process.cpu_percent(interval=1)
                        memory_mb = ogma_process.memory_info().rss / 1024 / 1024
                        self.stats["memory_current"] = memory_mb
                        
                        # Détecter problèmes
                        problems = []
                        
                        if cpu_percent > 80:
                            problems.append(f"CPU élevé: {cpu_percent:.1f}%")
                        
                        memory_growth = memory_mb - self.stats["memory_start"]
                        if memory_growth > 100:  # Plus de 100MB de croissance
                            problems.append(f"Fuite mémoire: +{memory_growth:.1f}MB")
                        
                        # Status
                        status_icon = "🔴" if problems else "🟢"
                        problems_str = " | ".join(problems) if problems else "OK"
                        
                        print(f"{status_icon} [{current_time:.0f}s] CPU: {cpu_percent:.1f}% | RAM: {memory_mb:.1f}MB | {problems_str}")
                        
                        # Détection boucle infinie (si CPU constamment élevé)
                        if cpu_percent > 90:
                            loop_count += 1
                            if loop_count >= 3:  # 3 checks consécutifs
                                print("🚨 BOUCLE INFINIE DÉTECTÉE !")
                                print("💡 Probable cause: main_page() ou NiceGUI Client")
                                break
                        else:
                            loop_count = 0
                        
                        last_check = current_time
                        
                    except psutil.NoSuchProcess:
                        print(f"💀 [{current_time:.0f}s] Processus OGMA fermé")
                        break
                    except Exception as e:
                        print(f"⚠️ [{current_time:.0f}s] Erreur monitoring: {e}")
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            print(f"\n⏹️ Monitoring arrêté après {current_time:.0f}s")
        
        # Rapport final
        self.generate_report(current_time)
    
    def generate_report(self, duration):
        """Génère un rapport de diagnostic"""
        print("\n" + "=" * 50)
        print("📋 === RAPPORT DIAGNOSTIC ===")
        print(f"⏱️ Durée surveillance: {duration:.0f}s")
        print(f"💾 RAM début: {self.stats['memory_start']:.1f}MB")
        print(f"💾 RAM fin: {self.stats['memory_current']:.1f}MB")
        
        memory_diff = self.stats['memory_current'] - self.stats['memory_start']
        print(f"📈 Évolution RAM: {memory_diff:+.1f}MB")
        
        if self.stats["crashes"] > 0:
            print(f"💥 Crashes détectés: {self.stats['crashes']}")
        
        # Recommandations
        print("\n🔧 RECOMMANDATIONS:")
        
        if memory_diff > 50:
            print("- ⚠️ Fuite mémoire détectée - vérifier threads et caches")
        
        if duration < 60 and self.stats["crashes"] > 0:
            print("- 🚨 Crash rapide - probable conflit au démarrage")
        elif duration > 120:
            print("- ✅ Stabilité correcte - problème résolu ou intermittent")
        
        print("- 💡 Utiliser 'python fix_nicegui_loop.py' si boucles détectées")

def watch_logs_file():
    """Surveille les logs en temps réel depuis un fichier"""
    print("📄 Surveillance logs fichier non implémentée")
    print("💡 Utilisez le monitoring processus à la place")

def main():
    if len(sys.argv) < 2:
        print("🔍 === DIAGNOSTIC AVANCÉ OGMA ===")
        print()
        print("USAGE:")
        print("  python advanced_debug_ogma.py monitor    # Monitoring processus temps réel")
        print("  python advanced_debug_ogma.py quick      # Test rapide 1 minute")  
        print("  python advanced_debug_ogma.py logs       # Surveillance logs fichier")
        print()
        print("DIAGNOSTIC:")
        print("- monitor: Surveille CPU, RAM, boucles infinies")
        print("- quick: Version courte pour tests rapides")
        print("- logs: Analyse logs en temps réel")
        print()
        print("💡 Lancez OGMA d'abord, puis ce diagnostic")
        return
    
    command = sys.argv[1].lower()
    monitor = OGMAHealthMonitor()
    
    if command == "monitor":
        print("🔍 Monitoring complet (5 minutes)...")
        monitor.monitor_ogma_process(300)
    elif command == "quick":
        print("⚡ Test rapide (1 minute)...")
        monitor.monitor_ogma_process(60)
    elif command == "logs":
        watch_logs_file()
    else:
        print(f"❌ Commande inconnue: {command}")

if __name__ == "__main__":
    main()