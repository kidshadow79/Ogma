# test_stabilite_production.py
"""
Test de stabilité en production avec les optimisations mémoire
Surveille la consommation RAM et la stabilité sur plusieurs chronophotographies
"""

import time
import psutil
import requests
import json
import os
from datetime import datetime

def get_ogma_memory():
    """Retourne la consommation mémoire des processus OGMA"""
    total_memory = 0
    python_processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'memory_info']):
        try:
            if 'python' in proc.info['name'].lower():
                memory_mb = proc.info['memory_info'].rss / 1024 / 1024
                python_processes.append({
                    'pid': proc.info['pid'],
                    'memory_mb': memory_mb
                })
                total_memory += memory_mb
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    return total_memory, python_processes

def check_cache_folder():
    """Vérifie l'état du cache disque"""
    cache_folder = "./captures/cache"
    
    if not os.path.exists(cache_folder):
        return {"exists": False, "files": 0, "size_mb": 0}
    
    cache_files = [f for f in os.listdir(cache_folder) if f.startswith('cache_')]
    
    total_size = 0
    for filename in cache_files:
        filepath = os.path.join(cache_folder, filename)
        try:
            total_size += os.path.getsize(filepath)
        except:
            pass
    
    return {
        "exists": True,
        "files": len(cache_files),
        "size_mb": total_size / 1024 / 1024
    }

def test_stabilite():
    """Test principal de stabilité"""
    print("🔬 TEST STABILITÉ PRODUCTION - SYSTÈME HYBRIDE")
    print("=" * 60)
    
    # Mesures initiales
    initial_memory, _ = get_ogma_memory()
    print(f"📊 Mémoire Python initiale: {initial_memory:.1f} MB")
    
    cache_info = check_cache_folder()
    print(f"📁 Cache initial: {cache_info['files']} fichiers, {cache_info['size_mb']:.1f} MB")
    
    # Surveiller sur 5 minutes
    duration_minutes = 5
    check_interval = 30  # toutes les 30 secondes
    
    print(f"\n⏰ Surveillance {duration_minutes} minutes (échantillonnage {check_interval}s)...")
    print("Timestamp       | RAM (MB) | Delta | Cache Files | Cache Size")
    print("-" * 70)
    
    start_time = time.time()
    measurements = []
    
    while time.time() - start_time < duration_minutes * 60:
        try:
            # Mesures actuelles
            current_time = datetime.now().strftime("%H:%M:%S")
            current_memory, processes = get_ogma_memory()
            memory_delta = current_memory - initial_memory
            
            cache_info = check_cache_folder()
            
            # Log
            print(f"{current_time} | {current_memory:8.1f} | {memory_delta:+5.1f} | {cache_info['files']:11d} | {cache_info['size_mb']:9.1f} MB")
            
            # Stockage pour analyse
            measurements.append({
                'timestamp': time.time(),
                'memory_mb': current_memory,
                'memory_delta': memory_delta,
                'cache_files': cache_info['files'],
                'cache_size_mb': cache_info['size_mb'],
                'processes': len(processes)
            })
            
            time.sleep(check_interval)
            
        except KeyboardInterrupt:
            print("\n⏹️ Test interrompu par l'utilisateur")
            break
        except Exception as e:
            print(f"⚠️ Erreur mesure: {e}")
            time.sleep(5)
    
    # Analyse des résultats
    print("\n" + "=" * 60)
    print("📈 ANALYSE STABILITÉ")
    print("=" * 60)
    
    if len(measurements) > 1:
        # Évolution mémoire
        max_memory = max(m['memory_mb'] for m in measurements)
        min_memory = min(m['memory_mb'] for m in measurements)
        memory_variation = max_memory - min_memory
        
        # Évolution cache
        max_cache = max(m['cache_files'] for m in measurements)
        final_cache = measurements[-1]['cache_files']
        
        print(f"🔸 Mémoire RAM:")
        print(f"   Min: {min_memory:.1f} MB")
        print(f"   Max: {max_memory:.1f} MB")
        print(f"   Variation: {memory_variation:.1f} MB")
        
        print(f"🔸 Cache disque:")
        print(f"   Fichiers max: {max_cache}")
        print(f"   Fichiers final: {final_cache}")
        print(f"   Taille finale: {measurements[-1]['cache_size_mb']:.1f} MB")
        
        # Évaluation stabilité
        print(f"\n🎯 ÉVALUATION:")
        
        if memory_variation < 50:
            print(f"✅ Mémoire STABLE (variation {memory_variation:.1f} MB)")
        elif memory_variation < 100:
            print(f"⚠️ Mémoire MODÉRÉE (variation {memory_variation:.1f} MB)")
        else:
            print(f"❌ Mémoire INSTABLE (variation {memory_variation:.1f} MB)")
        
        if final_cache <= 10:
            print(f"✅ Cache OPTIMAL (rotation active: {final_cache} fichiers)")
        elif final_cache <= 20:
            print(f"⚠️ Cache ACCEPTABLE ({final_cache} fichiers)")
        else:
            print(f"❌ Cache ACCUMULATION ({final_cache} fichiers)")
        
        # Recommandations
        print(f"\n💡 RECOMMANDATIONS:")
        if memory_variation > 50:
            print("- Surveiller les fuites mémoire potentielles")
        if final_cache > 15:
            print("- Vérifier la rotation automatique du cache")
        if max_memory > 500:
            print("- Consommation RAM élevée, optimisation nécessaire")
        
        print("- Les optimisations semblent fonctionner correctement")
        
    else:
        print("❌ Pas assez de mesures pour l'analyse")
    
    return measurements

if __name__ == "__main__":
    print("🚀 Démarrage test stabilité production...")
    print("💡 Assurez-vous qu'OGMA tourne sur http://127.0.0.1:8080")
    print()
    
    try:
        # Vérifier qu'OGMA est accessible
        response = requests.get("http://127.0.0.1:8080", timeout=5)
        print("✅ OGMA accessible, démarrage surveillance...")
    except:
        print("❌ OGMA inaccessible sur http://127.0.0.1:8080")
        print("   Lancez d'abord: python launch_ogma.py")
        exit(1)
    
    measurements = test_stabilite()
    
    print(f"\n✅ Test terminé - {len(measurements)} mesures collectées")
    print("💾 Pour plus de détails, surveillez ./captures/cache/")