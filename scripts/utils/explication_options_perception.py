# explication_options_perception.py
"""
📋 EXPLICATION DES OPTIONS DE PERCEPTION OGMA

Ce script explique la différence entre les deux options principales de perception :
1. "Capture automatique lors des envois de message"
2. "Sauvegarder les captures localement"
"""

def expliquer_options():
    print("🎥 OGMA - OPTIONS DE PERCEPTION")
    print("=" * 60)
    
    print("\n📋 VUE D'ENSEMBLE:")
    print("OGMA propose 2 options distinctes pour gérer la perception webcam :")
    print("1️⃣ Capture automatique lors des envois de message")
    print("2️⃣ Sauvegarder les captures localement")
    
    print("\n" + "=" * 60)
    print("1️⃣ CAPTURE AUTOMATIQUE LORS DES ENVOIS")
    print("=" * 60)
    print("🎯 OBJECTIF:")
    print("   • Déclenche automatiquement une photo webcam à chaque message envoyé")
    print("   • L'image est incluse dans la conversation avec l'IA")
    print("   • Permet à l'IA de 'voir' votre contexte actuel")
    
    print("\n💡 FONCTIONNEMENT:")
    print("   • ✅ ACTIVÉ : Photo webcam prise automatiquement à chaque envoi")
    print("   • ❌ DÉSACTIVÉ : Pas de capture automatique (capture manuelle uniquement)")
    
    print("\n🔍 DANS LE CODE:")
    print("   • Variable: 'capture_on_send' dans ogma_ng.py ligne 5357")
    print("   • Déclenchement: fonction au moment de l'envoi de message")
    print("   • Transmission: image envoyée directement à l'IA en temps réel")
    
    print("\n📝 EXEMPLE D'USAGE:")
    print("   • Vous tapez: 'Regarde ce que je fais'")
    print("   • Si ACTIVÉ: Photo webcam prise + message + photo envoyés ensemble")
    print("   • L'IA voit votre environnement actuel et peut commenter")
    
    print("\n" + "=" * 60)
    print("2️⃣ SAUVEGARDER LES CAPTURES LOCALEMENT")
    print("=" * 60)
    print("🎯 OBJECTIF:")
    print("   • Contrôle si les images capturées sont sauvées sur disque")
    print("   • Permet de conserver un historique visuel local")
    print("   • Option indépendante de la capture automatique")
    
    print("\n💡 FONCTIONNEMENT:")
    print("   • ✅ ACTIVÉ : Images sauvées dans ./captures/")
    print("   • ❌ DÉSACTIVÉ : Images utilisées mais pas conservées")
    print("   • ⚡ EXCEPTION : Pellicules motion TOUJOURS sauvées")
    
    print("\n🔍 DANS LE CODE:")
    print("   • Variable: 'save_captures' dans perception_agent.py ligne 185")
    print("   • Fonction: '_save_image_if_enabled()' gère la sauvegarde")
    print("   • Dossier: ./captures/ par défaut")
    
    print("\n📝 EXEMPLE D'USAGE:")
    print("   • Capture prise (automatique ou manuelle)")
    print("   • Si ACTIVÉ: Image sauvée + utilisée pour l'IA")
    print("   • Si DÉSACTIVÉ: Image utilisée pour l'IA puis supprimée")
    
    print("\n" + "=" * 60)
    print("🔄 COMBINAISONS POSSIBLES")
    print("=" * 60)
    
    scenarios = [
        {
            "capture_auto": True,
            "save_local": True,
            "description": "Mode COMPLET",
            "comportement": "Photo automatique à chaque message + sauvegarde locale"
        },
        {
            "capture_auto": True,
            "save_local": False,
            "description": "Mode AUTOMATIQUE TEMPORAIRE",
            "comportement": "Photo automatique mais pas de conservation locale"
        },
        {
            "capture_auto": False,
            "save_local": True,
            "description": "Mode MANUEL ARCHIVÉ",
            "comportement": "Capture manuelle uniquement + sauvegarde des captures"
        },
        {
            "capture_auto": False,
            "save_local": False,
            "description": "Mode MINIMAL",
            "comportement": "Capture manuelle uniquement, pas de sauvegarde"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{i}. {scenario['description']}")
        print(f"   📸 Capture auto: {'✅' if scenario['capture_auto'] else '❌'}")
        print(f"   💾 Sauvegarde: {'✅' if scenario['save_local'] else '❌'}")
        print(f"   🎯 Résultat: {scenario['comportement']}")
    
    print("\n" + "=" * 60)
    print("⚠️ POINTS IMPORTANTS")
    print("=" * 60)
    print("🔸 Les pellicules motion (détection mouvement) sont TOUJOURS sauvées")
    print("🔸 'save_captures' n'affecte QUE les captures simples")
    print("🔸 Les deux options sont complètement indépendantes")
    print("🔸 L'image est toujours envoyée à l'IA si capturée")
    print("🔸 'save_captures' détermine juste si on garde une copie locale")
    
    print("\n" + "=" * 60)
    print("💡 RECOMMANDATIONS D'USAGE")
    print("=" * 60)
    print("🏠 Usage domestique/test:")
    print("   • Capture auto: ✅ (pratique)")
    print("   • Sauvegarde: ❌ (évite l'encombrement)")
    
    print("\n🏢 Usage professionnel:")
    print("   • Capture auto: ❌ (contrôle précis)")
    print("   • Sauvegarde: ✅ (archivage/audit)")
    
    print("\n🎮 Usage démo/présentation:")
    print("   • Capture auto: ✅ (fluidité)")
    print("   • Sauvegarde: ✅ (garder les moments clés)")
    
    print("\n📊 Usage analyse:")
    print("   • Capture auto: Variable selon contexte")
    print("   • Sauvegarde: ✅ (données pour analyse)")

def demonstration_technique():
    """Montre comment ça marche dans le code"""
    print("\n\n🔧 DÉMONSTRATION TECHNIQUE")
    print("=" * 60)
    
    print("📄 1. DANS L'INTERFACE (ogma_modals.py ligne 2943-2944):")
    print('   capture_on_send_check = ui.checkbox("Capture automatique...", value=True)')
    print('   save_captures_check = ui.checkbox("Sauvegarder les captures...", value=False)')
    
    print("\n📄 2. DÉCLENCHEMENT AUTOMATIQUE (ogma_ng.py ligne 5357):")
    print("   if perception_ui.current_config.get('capture_on_send', False):")
    print("       perception_image_data = perception_ui.capture_for_chat()")
    
    print("\n📄 3. SAUVEGARDE CONDITIONNELLE (perception_agent.py ligne 185):")
    print("   if not is_motion_pellicule and not self.config.get('save_captures', False):")
    print("       return None  # Pas de sauvegarde")
    print("   # Sinon, sauvegarde l'image")
    
    print("\n🎯 FLUX COMPLET:")
    print("   Message envoyé → Vérif capture_on_send → Photo webcam")
    print("   Photo prise → Vérif save_captures → Sauvegarde conditionnelle")
    print("   Image → Envoyée à l'IA (toujours si capturée)")

if __name__ == "__main__":
    expliquer_options()
    demonstration_technique()
    
    print("\n\n✨ EN RÉSUMÉ:")
    print("• 'Capture automatique' = QUAND prendre la photo")
    print("• 'Sauvegarder localement' = SI garder la photo sur disque")
    print("• Les deux sont complètement indépendants !")
    print("• L'IA reçoit toujours l'image si elle est capturée")