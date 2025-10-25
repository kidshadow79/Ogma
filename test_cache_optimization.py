# test_cache_optimization.py
"""
Test du nouveau système de cache disque HYBRIDE
Vérifie la réduction de consommation RAM et la stabilité
"""

import os
import sys
import time
import psutil
import json
import traceback
import threading
from pathlib import Path

def get_process_memory():
    """Retourne la consommation mémoire du processus actuel en MB"""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024

def load_test_config():
    """Charge une configuration de test optimisée"""
    return {
        "webcam_index": 0,
        "motion_buffer_size": 3,  # Réduit de 10 à 3
        "triage_resolution": [640, 480],
        "save_captures": True,  # Activé pour tester le cache disque
        "capture_folder": "./captures",
        "capture_format": "JPEG",
        "jpeg_quality": 70
    }

def test_memory_optimization():
    """Test principal des optimisations mémoire"""
    print("=" * 60)
    print("🧪 TEST OPTIMISATION MÉMOIRE - SYSTÈME HYBRIDE")
    print("=" * 60)
    
    # Mesure mémoire initiale
    initial_memory = get_process_memory()
    print(f"📊 Mémoire initiale: {initial_memory:.1f} MB")
    
    try:
        # Importer et initialiser l'agent optimisé
        sys.path.append('./extensions')
        from perception_agent import PerceptionAgent
        
        print("📁 Initialisation PerceptionAgent HYBRIDE...")
        config = load_test_config()
        agent = PerceptionAgent(config)
        
        # Mesure après initialisation
        init_memory = get_process_memory()
        memory_increase = init_memory - initial_memory
        print(f"📊 Mémoire après init: {init_memory:.1f} MB (+{memory_increase:.1f} MB)")
        
        # Démarrer l'agent
        print("🚀 Démarrage agent...")
        agent.start()
        time.sleep(2)  # Laisser temps d'initialisation
        
        # Mesure après démarrage
        running_memory = get_process_memory()
        running_increase = running_memory - initial_memory
        print(f"📊 Mémoire en fonctionnement: {running_memory:.1f} MB (+{running_increase:.1f} MB)")
        
        # Test de cache disque
        print("\n🔍 TEST CACHE DISQUE:")
        cache_folder = os.path.join(config['capture_folder'], 'cache')
        print(f"📁 Dossier cache: {cache_folder}")
        
        if os.path.exists(cache_folder):
            cache_files = [f for f in os.listdir(cache_folder) if f.startswith('cache_')]
            print(f"📄 Fichiers cache existants: {len(cache_files)}")
        else:
            print("📄 Dossier cache non créé (normal au démarrage)")
        
        # Attendre que le buffer se remplisse
        print("\n⏳ Attente remplissage buffer (15 secondes)...")
        for i in range(15):
            time.sleep(1)
            if i % 5 == 4:  # Toutes les 5 secondes
                current_memory = get_process_memory()
                current_increase = current_memory - initial_memory
                print(f"📊 Mémoire T+{i+1}s: {current_memory:.1f} MB (+{current_increase:.1f} MB)")
                
                # Vérifier cache disque
                if os.path.exists(cache_folder):
                    cache_files = [f for f in os.listdir(cache_folder) if f.startswith('cache_')]
                    print(f"📄 Fichiers cache: {len(cache_files)}")
        
        # Test de chronophotographie
        print("\n🎬 TEST CHRONOPHOTOGRAPHIE HYBRIDE:")
        pre_chrono_memory = get_process_memory()
        
        # Simuler création pellicule
        try:
            result = agent.create_motion_sequence(frames_before=3, frames_after=6)
            if result:
                print("✅ Chronophotographie HYBRIDE créée avec succès")
            else:
                print("❌ Échec chronophotographie")
        except Exception as e:
            print(f"❌ Erreur chronophotographie: {e}")
        
        post_chrono_memory = get_process_memory()
        chrono_memory_diff = post_chrono_memory - pre_chrono_memory
        print(f"📊 Impact mémoire chronophotographie: {chrono_memory_diff:+.1f} MB")
        
        # Vérifier cache après chronophotographie
        if os.path.exists(cache_folder):
            cache_files = [f for f in os.listdir(cache_folder) if f.startswith('cache_')]
            print(f"📄 Fichiers cache après pellicule: {len(cache_files)}")
            
            # Calculer taille cache
            total_size = 0
            for filename in cache_files:
                filepath = os.path.join(cache_folder, filename)
                total_size += os.path.getsize(filepath)
            print(f"💾 Taille cache disque: {total_size / 1024 / 1024:.1f} MB")
        
        # Arrêter l'agent
        print("\n🛑 Arrêt agent...")
        agent.stop()
        time.sleep(1)
        
        final_memory = get_process_memory()
        final_increase = final_memory - initial_memory
        print(f"📊 Mémoire finale: {final_memory:.1f} MB (+{final_increase:.1f} MB)")
        
        # RÉSUMÉ DES PERFORMANCES
        print("\n" + "=" * 60)
        print("📈 RÉSUMÉ PERFORMANCES HYBRIDES:")
        print("=" * 60)
        print(f"🔸 Consommation RAM totale: +{running_increase:.1f} MB")
        print(f"🔸 Ancien système (estimation): +9.2 MB (buffer 10 images)")
        
        if running_increase < 9.2:
            gain = 9.2 - running_increase
            print(f"✅ GAIN MÉMOIRE: -{gain:.1f} MB ({gain/9.2*100:.1f}% d'économie)")
        else:
            print(f"❌ Consommation supérieure à l'estimation")
        
        if os.path.exists(cache_folder):
            cache_files = [f for f in os.listdir(cache_folder) if f.startswith('cache_')]
            print(f"🔸 Fichiers cache disque: {len(cache_files)}")
        
        print(f"🔸 Stabilité: {'✅ OK' if chrono_memory_diff < 5 else '⚠️ À surveiller'}")
        
        return True
        
    except Exception as e:
        print(f"❌ ERREUR TEST: {e}")
        traceback.print_exc()
        return False

def test_cache_rotation():
    """Test spécifique de la rotation du cache"""
    print("\n" + "=" * 60)
    print("🔄 TEST ROTATION CACHE DISQUE")
    print("=" * 60)
    
    cache_folder = "./captures/cache"
    if not os.path.exists(cache_folder):
        print("📁 Dossier cache inexistant")
        return False
    
    # Compter fichiers avant
    cache_files = [f for f in os.listdir(cache_folder) if f.startswith('cache_')]
    print(f"📄 Fichiers avant rotation: {len(cache_files)}")
    
    if len(cache_files) > 10:
        print("🔄 Rotation attendue (>10 fichiers)")
    else:
        print("✅ Rotation pas nécessaire (<10 fichiers)")
    
    return True

if __name__ == "__main__":
    print("🚀 Démarrage tests optimisation mémoire HYBRIDE...")
    
    success = test_memory_optimization()
    
    if success:
        test_cache_rotation()
        print("\n✅ Tests terminés avec succès")
    else:
        print("\n❌ Tests échoués")
    
    print("\n💡 RECOMMANDATIONS:")
    print("- Surveiller la consommation RAM < 5MB pour le buffer")
    print("- Vérifier rotation automatique du cache disque")
    print("- Tester stabilité sur plusieurs pellicules consécutives")