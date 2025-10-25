# analyse_temporisation_perception.py
"""
🎬 ANALYSE DU SYSTÈME DE TEMPORISATION ET ASSEMBLAGE OGMA

Ce script analyse en détail comment OGMA sélectionne et assemble les images
pour créer les pellicules motion, avec les temporisations exactes.
"""

import time

def analyser_systeme_temporisation():
    print("🎬 SYSTÈME DE TEMPORISATION PERCEPTION OGMA")
    print("=" * 60)
    
    print("📊 VUE D'ENSEMBLE DU SYSTÈME:")
    print("OGMA utilise un système HYBRIDE en 2 phases :")
    print("📁 PHASE 1: Images du cache disque (passé)")
    print("📸 PHASE 2: Capture en temps réel (futur)")
    
    print("\n" + "=" * 60)
    print("⏱️ TEMPORISATIONS DÉTAILLÉES")
    print("=" * 60)
    
    print("\n🔄 1. BUFFER CONTINU (Arrière-plan)")
    print("─" * 40)
    print("• Intervalle: 1.0 seconde (self.buffer_interval = 1.0)")
    print("• Fréquence: 1 FPS (1 image par seconde)")
    print("• Méthode: Thread continu _continuous_capture()")
    print("• Stockage: 3 images en RAM + cache disque rotatif")
    print("• Webcam FPS: 30 FPS configuré (cv2.CAP_PROP_FPS)")
    print("• Stabilité: 5 FPS (sleep 0.2s) pour éviter surcharge")
    
    print("\n📁 2. CACHE DISQUE (Images passées)")
    print("─" * 40)
    print("• Rotation: Toutes les 30 images (max_cache_files = 30)")
    print("• Conservation: 10 images les plus récentes")
    print("• Format: cache_XXXXXX_timestamp.jpg")
    print("• Qualité: 70% JPEG pour économiser l'espace")
    print("• Tri: Par timestamp (plus récent en premier)")
    print("• Sélection: frames_before images (défaut: 3)")
    
    print("\n📸 3. CAPTURE TEMPS RÉEL (Images futures)")
    print("─" * 40)
    print("• Nombre: frames_after images (défaut: 6)")
    print("• Délais optimisés pour chronophotographie:")
    capture_delays = [0.3, 0.7, 1.2, 1.8, 2.5, 3.2]
    for i, delay in enumerate(capture_delays):
        print(f"  ▸ Image {i+1}: {delay}s après déclenchement")
    print("• Progression: Délais croissants pour effet cinématique")
    print("• Durée totale: ~3.2 secondes maximum")
    
    print("\n" + "=" * 60)
    print("🎯 SÉLECTION DES IMAGES")
    print("=" * 60)
    
    print("\n📋 Algorithme de sélection:")
    print("1. Charger X images depuis cache disque (passé récent)")
    print("2. Capturer Y nouvelles images avec délais progressifs")
    print("3. Assembler chronologiquement: [Cache] + [Temps réel]")
    print("4. Créer pellicule avec layout choisi")
    
    print("\n🔍 Détails techniques:")
    print("• Cache: Tri par modification time (os.path.getmtime)")
    print("• Ordre: reversed(recent_files) pour chronologie")
    print("• Thread-safe: frame_lock pour accès concurrent")
    print("• Fallback: Si < 2 images → capture simple")

def analyser_layouts_assemblage():
    print("\n" + "=" * 60)
    print("🎨 LAYOUTS D'ASSEMBLAGE")
    print("=" * 60)
    
    layouts = {
        '3x2': "3 colonnes × 2 lignes (6 images)",
        '2x3': "2 colonnes × 3 lignes (6 images)", 
        '1x6': "1 colonne × 6 lignes (6 images)",
        '6x1': "6 colonnes × 1 ligne (6 images)",
        '2x2': "2 colonnes × 2 lignes (4 images)",
        '1x4': "1 colonne × 4 lignes (4 images)",
        '4x1': "4 colonnes × 1 ligne (4 images)"
    }
    
    print("📐 Layouts disponibles:")
    for layout, description in layouts.items():
        print(f"  • {layout}: {description}")
    
    print("\n🎬 Options d'affichage:")
    print("  • show_timeline: Timeline temporelle sur l'image")
    print("  • show_annotations: Annotations de temps sur chaque frame")
    print("  • Qualité JPEG: 85% pour pellicules finales")

def simulation_temporisation():
    print("\n" + "=" * 60)
    print("⏱️ SIMULATION D'UNE PELLICULE MOTION")
    print("=" * 60)
    
    print("🚀 Scénario: Utilisateur demande pellicule motion")
    print("─" * 50)
    
    # Simulation des timings
    start_time = time.time()
    current_time = start_time
    
    print(f"⏰ T+0.0s: Début pellicule motion")
    print(f"📁 T+0.1s: Chargement 3 images cache disque")
    print(f"   └─ cache_000001_timestamp.jpg (il y a ~3s)")
    print(f"   └─ cache_000002_timestamp.jpg (il y a ~2s)")
    print(f"   └─ cache_000003_timestamp.jpg (il y a ~1s)")
    
    capture_delays = [0.3, 0.7, 1.2, 1.8, 2.5, 3.2]
    
    print(f"\n📸 Captures temps réel:")
    for i, delay in enumerate(capture_delays):
        print(f"   T+{delay}s: Capture image {i+1}/6")
    
    print(f"\n🎬 T+3.3s: Assemblage des 9 images (3 cache + 6 nouvelles)")
    print(f"💾 T+3.4s: Sauvegarde pellicule (toujours active)")
    print(f"📤 T+3.5s: Encodage base64 et envoi au chat")
    print(f"\n✅ Total: ~3.5 secondes pour pellicule complète")

def analyser_optimisations_memoire():
    print("\n" + "=" * 60)
    print("🧠 OPTIMISATIONS MÉMOIRE")
    print("=" * 60)
    
    print("💾 Avant optimisation (problématique):")
    print("  • Buffer: 10 images × 900KB = ~9MB RAM permanent")
    print("  • Accumulation: Mémoire croissante sans limite")
    print("  • Performance: Ralentissements et crashes")
    
    print("\n✅ Après optimisation (actuel):")
    print("  • Buffer RAM: 3 images × 900KB = ~2.7MB (-70%)")
    print("  • Cache disque: Rotation automatique (30 → 10 fichiers)")
    print("  • Nettoyage: Suppression auto des anciens caches")
    print("  • Thread-safe: Protection accès concurrent")
    
    print("\n🔄 Rotation du cache:")
    print("  • Déclenchement: Tous les 30 fichiers")
    print("  • Conservation: 10 fichiers les plus récents")
    print("  • Suppression: 20 fichiers les plus anciens")
    print("  • Espace: ~20MB maximum sur disque")

def analyser_anti_spam():
    print("\n" + "=" * 60)
    print("🔇 SYSTÈME ANTI-SPAM LOGS")
    print("=" * 60)
    
    print("🚫 Problème précédent:")
    print("  • Log 'Buffer: 3/3 frames' toutes les secondes")
    print("  • Spam console → Ralentissements")
    print("  • Difficulté debugging autres composants")
    
    print("\n✅ Solution implémentée:")
    print("  • Premier log: 'HYBRIDE opérationnel'")
    print("  • Logs périodiques: Toutes les 5 minutes")
    print("  • Reset intelligent: Si buffer plus plein")
    print("  • Gestion erreurs: Pause progressive si échecs")
    
    print("\n📊 Exemple de logs optimisés:")
    print("  [MOTION-BUFFER] ✅ HYBRIDE opérationnel: RAM 3/3 + Cache disque actif")
    print("  [5 minutes plus tard]")
    print("  [MOTION-BUFFER] 🔄 HYBRIDE: RAM 3/3, Cache 15 fichiers")

if __name__ == "__main__":
    analyser_systeme_temporisation()
    analyser_layouts_assemblage()
    simulation_temporisation()
    analyser_optimisations_memoire()
    analyser_anti_spam()
    
    print("\n" + "=" * 60)
    print("📋 RÉSUMÉ TEMPORISATIONS CLÉS")
    print("=" * 60)
    print("🔄 Buffer continu: 1 image/seconde (1.0s)")
    print("📸 Capture temps réel: 0.3s, 0.7s, 1.2s, 1.8s, 2.5s, 3.2s")
    print("📁 Cache disque: Rotation tous les 30 fichiers")
    print("🎬 Durée pellicule: ~3.5s total (3s capture + 0.5s assemblage)")
    print("💾 Optimisation: -70% RAM (9MB → 2.7MB)")
    print("🧹 Nettoyage: Automatique, garde 10 fichiers récents")