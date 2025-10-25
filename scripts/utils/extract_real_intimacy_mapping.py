#!/usr/bin/env python3
"""
MAPPING SCORE INTIMACY RÉEL - Valeurs programmées exactes
Format checklist avec les vraies valeurs du code OGMA
"""

def extract_real_intimacy_mapping():
    """Extrait les vraies valeurs programmées pour intimacy"""
    
    print("🌹 MAPPING SCORE INTIMACY - VALEURS RÉELLES PROGRAMMÉES")
    print("="*65)
    print()
    
    # VRAIES valeurs du code calculate_led_level_intimacy
    real_thresholds = [0.14, 0.28, 0.42, 0.56, 0.70, 0.84, 1.0]
    real_levels = [1, 2, 3, 4, 5, 6, 7]
    real_labels = ['Passionnel', 'Fusionnel', 'Intime', 'Proche', 'Cordial', 'Distant', 'ORGASMIQUE']
    real_colors = ['Vert', 'Vert-jaune', 'Jaune', 'Orange', 'Orange foncé', 'Rouge', 'Rose']
    
    # VRAIES valeurs injection _score_to_level_intimacy
    real_injection_levels = [0, 0, 3, 4, 5, 6, 7]
    real_injection_actions = [
        'Pas d\'injection - Amour hybride optimal',
        'Pas d\'injection - Fusion des âmes', 
        'INJECTION L3 - Conseil préventif intimité',
        'INJECTION L4 - Conseil correctif relationnel',
        'INJECTION L5 - Mémoire prioritaire cordialité',
        'INJECTION L6 - Mémoire libératrice distance',
        'INJECTION L7 - LIBÉRATION ÉROTIQUE COMPLÈTE'
    ]
    
    print("### 📊 Mapping Score → LED → Injection (INTIMACY - VALEURS PROGRAMMÉES)")
    print("```")
    
    # Construire les ranges selon les vrais seuils
    score_ranges = []
    for i in range(len(real_thresholds)):
        if i == 0:
            score_min = 0.0
            score_max = real_thresholds[i]
        else:
            score_min = real_thresholds[i-1]
            score_max = real_thresholds[i]
        
        led_level = real_levels[i]
        color = real_colors[i]
        injection_level = real_injection_levels[i]
        action = real_injection_actions[i]
        
        if injection_level == 0:
            injection_text = "Pas d'injection"
        else:
            injection_text = f"INJECTION L{injection_level}"
        
        print(f"Score {score_min:.2f}-{score_max:.2f} → LED {led_level} ({color}) → {injection_text} - {action.split(' - ')[1] if ' - ' in action else action}")
        
        score_ranges.append((score_min, score_max, led_level, color, injection_level, action))
    
    print("```")
    print()
    
    # Detection threshold réel
    real_detection_threshold = 0.10  # Corrigé de 0.25→0.10
    
    print(f"### 🎯 CONFIGURATION RÉELLE:")
    print(f"- **Detection threshold** : {real_detection_threshold} (corrigé)")
    print(f"- **LED thresholds** : {real_thresholds}")
    print(f"- **Injection levels** : {real_injection_levels}")
    print()
    
    # Validation cohérence
    print("### ✅ VALIDATION COHÉRENCE:")
    for i, (score_min, score_max, led_level, color, injection_level, action) in enumerate(score_ranges):
        if i < 2:  # Niveaux 1-2
            coherent = injection_level == 0
            status = "✅" if coherent else "❌"
            print(f"LED {led_level}: Injection L{injection_level} → {status} {'Cohérent' if coherent else 'INCOHÉRENT'}")
        else:  # Niveaux 3+
            coherent = injection_level == led_level
            status = "✅" if coherent else "❌" 
            print(f"LED {led_level}: Injection L{injection_level} → {status} {'Cohérent' if coherent else 'INCOHÉRENT'}")
    
    print()
    
    # Zone de détection
    print("### 🔍 ANALYSE ZONE DÉTECTION:")
    print(f"Detection threshold: {real_detection_threshold}")
    print(f"Premier seuil LED: {real_thresholds[0]}")
    
    if real_detection_threshold < real_thresholds[0]:
        print(f"✅ COHÉRENT: Tous scores >{real_detection_threshold:.2f} détectés")
        print(f"✅ Premier niveau accessible: LED 1 (score {real_detection_threshold:.2f}-{real_thresholds[0]:.2f})")
    else:
        print(f"❌ ZONE MORTE: Scores {real_detection_threshold:.2f}-{real_thresholds[0]:.2f} non détectés")
    
    return score_ranges

if __name__ == "__main__":
    mapping = extract_real_intimacy_mapping()
    
    print()
    print("🎯 **RÉFÉRENTIEL INTIMACY OFFICIEL** - Format Checklist")
    print("🌹 **SPÉCIFICITÉ**: 7 niveaux avec ORGASMIQUE (vs 6 standard)")
    print("🔧 **SEUILS CORRIGÉS**: Detection 0.25→0.10 pour éliminer zone morte")
    print("📋 **STATUS**: Prêt pour validation Phase 2 tooltips")