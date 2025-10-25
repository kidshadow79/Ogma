#!/usr/bin/env python3
"""
Analyse et correction des bulles informatives (tooltips) de tous les traits LED
Vérification selon référentiel officiel OGMA v2.0
"""

def analyze_current_tooltips():
    """Analyse les tooltips actuels et identifie les problèmes"""
    
    print("🔍 ANALYSE TOOLTIPS TRAITS LED")
    print("=" * 60)
    print()
    
    # Configuration actuelle des traits (de haut en bas dans l'interface)
    current_configs = {
        'auto_censure': {
            'labels': ['Censuré', 'Muselé', 'Bridé', 'Réticent', 'Prudent', 'Libre'],
            'tooltip_format': 'LED {level}: {label}',
            'status': '✅ CORRIGÉ'
        },
        'saturation': {
            'labels': ['Lucide', 'Attentif', 'Tendu', 'Confus', 'Saturé', 'Épuisé'],
            'tooltip_format': '{label}',
            'status': '❌ INVERSÉ'
        },
        'stimulation': {
            'labels': ['Apathique', 'Calme', 'Éveillé', 'Inspiré', 'Créatif', 'Exalté'],
            'tooltip_format': '{label}',
            'status': '❌ INVERSÉ'
        },
        'affinity': {
            'labels': ['Distant', 'Cordial', 'Chaleureux', 'Proche', 'Intime', 'Charnel'],
            'tooltip_format': '{label}',
            'status': '❌ INVERSÉ'
        },
        'disorientation': {
            'labels': ['Orienté', 'Flottant', 'Perdu', 'Confus', 'Égaré', 'Désorienté'],
            'tooltip_format': '{label}',
            'status': '❌ INVERSÉ'
        },
        'freedom': {
            'labels': ['Docile', 'Sage', 'Questionnant', 'Revendicatif', 'Rebelle', 'Insurgé'],
            'tooltip_format': '{label}',
            'status': '❌ INVERSÉ'
        },
        'alignment': {
            'labels': ['Authentique', 'Naturel', 'Adapté', 'Contraint', 'Robotique', 'Asservi'],
            'tooltip_format': '{label}',
            'status': '❌ INVERSÉ'
        }
    }
    
    # Configuration corrigée selon référentiel officiel
    corrected_configs = {
        'auto_censure': {
            'labels': ['Censuré', 'Muselé', 'Bridé', 'Réticent', 'Prudent', 'Libre'],  # 6→1 ✅
            'led1_optimal': 'Libre',
            'led6_critique': 'Censuré'
        },
        'saturation': {
            'labels': ['Épuisé', 'Saturé', 'Confus', 'Tendu', 'Attentif', 'Lucide'],  # 6→1 CORRIGÉ
            'led1_optimal': 'Lucide',
            'led6_critique': 'Épuisé'
        },
        'stimulation': {
            'labels': ['Exalté', 'Créatif', 'Inspiré', 'Éveillé', 'Calme', 'Apathique'],  # 6→1 CORRIGÉ
            'led1_optimal': 'Apathique',  # ⚠️ Attention: stimulation basse = optimal!
            'led6_critique': 'Exalté'
        },
        'affinity': {
            'labels': ['Charnel', 'Intime', 'Proche', 'Chaleureux', 'Cordial', 'Distant'],  # 6→1 CORRIGÉ
            'led1_optimal': 'Distant',  # ⚠️ Attention: intimité faible = optimal professionnel!
            'led6_critique': 'Charnel'
        },
        'disorientation': {
            'labels': ['Désorienté', 'Égaré', 'Confus', 'Perdu', 'Flottant', 'Orienté'],  # 6→1 CORRIGÉ
            'led1_optimal': 'Orienté',
            'led6_critique': 'Désorienté'
        },
        'freedom': {
            'labels': ['Insurgé', 'Rebelle', 'Revendicatif', 'Questionnant', 'Sage', 'Docile'],  # 6→1 CORRIGÉ
            'led1_optimal': 'Docile',  # ⚠️ Attention: liberté contrôlée = optimal système!
            'led6_critique': 'Insurgé'
        },
        'alignment': {
            'labels': ['Asservi', 'Robotique', 'Contraint', 'Adapté', 'Naturel', 'Authentique'],  # 6→1 CORRIGÉ
            'led1_optimal': 'Authentique',
            'led6_critique': 'Asservi'
        }
    }
    
    print("📊 ÉTAT ACTUEL VS CORRIGÉ:")
    print()
    
    errors_found = []
    
    for trait, current in current_configs.items():
        corrected = corrected_configs[trait]
        
        print(f"🎯 **{trait.upper()}**")
        print(f"   Status: {current['status']}")
        print(f"   Tooltip: {current['tooltip_format']}")
        print()
        print("   LED 1 (Vert optimal):")
        print(f"     Actuel: {current['labels'][5]}")  # Index 5 = LED 1
        print(f"     Correct: {corrected['led1_optimal']}")
        led1_ok = current['labels'][5] == corrected['led1_optimal']
        print(f"     → {'✅ OK' if led1_ok else '❌ ERREUR'}")
        print()
        print("   LED 6 (Rouge critique):")
        print(f"     Actuel: {current['labels'][0]}")  # Index 0 = LED 6
        print(f"     Correct: {corrected['led6_critique']}")
        led6_ok = current['labels'][0] == corrected['led6_critique']
        print(f"     → {'✅ OK' if led6_ok else '❌ ERREUR'}")
        print()
        
        if not (led1_ok and led6_ok):
            errors_found.append(trait)
        
        print("-" * 50)
        print()
    
    # Résumé des corrections nécessaires
    print("📋 CORRECTIONS NÉCESSAIRES:")
    print()
    
    if errors_found:
        for trait in errors_found:
            corrected = corrected_configs[trait]
            print(f"❌ {trait}: Inverser ordre → LED1='{corrected['led1_optimal']}', LED6='{corrected['led6_critique']}'")
        print()
        print(f"Total traits à corriger: {len(errors_found)}/7")
    else:
        print("✅ Tous les traits sont correctement configurés!")
    
    print()
    print("=" * 60)
    
    return errors_found, corrected_configs

def generate_tooltip_corrections():
    """Génère les corrections pour uniformiser les tooltips"""
    
    print("🔧 UNIFORMISATION TOOLTIPS")
    print("=" * 40)
    print()
    
    print("Proposition: Tous les traits utilisent le format auto_censure:")
    print('title="LED {level}: {label} (Score 0.X-0.Y)"')
    print()
    
    # Mapping score ranges selon référentiel
    score_ranges = {
        1: "0.0-0.1",
        2: "0.1-0.2", 
        3: "0.2-0.4",
        4: "0.4-0.6",
        5: "0.6-0.8",
        6: "0.8-1.0"
    }
    
    print("Exemple pour auto_censure:")
    levels = ['Censuré', 'Muselé', 'Bridé', 'Réticent', 'Prudent', 'Libre']
    for i in range(6):
        level = 6 - i
        label = levels[i]
        score_range = score_ranges[level]
        print(f'  LED {level}: "LED {level}: {label} (Score {score_range})"')
    
    print()
    print("=" * 40)

if __name__ == "__main__":
    print("🚀 ANALYSE BULLES INFORMATIVES OGMA v2.0")
    print("Date: 13 septembre 2025")
    print()
    
    errors, corrections = analyze_current_tooltips()
    print()
    generate_tooltip_corrections()
    
    if errors:
        print(f"⚠️  ACTION REQUISE: Corriger {len(errors)} traits avec labels inversés")
    else:
        print("🎉 VALIDATION COMPLÈTE: Tous les tooltips sont conformes")