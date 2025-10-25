#!/usr/bin/env python3
"""
Test rapide pour vérifier l'ajout de la section Web Navigator 
dans l'interface des phrases magiques OGMA
"""

print("🧪 TEST: Vérification section Web Navigator dans phrases magiques")
print("=" * 70)

# Lire le fichier modifié pour vérifier la section
with open('ogma_ng.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Chercher la section Web Navigator
if '🌐 Recherche Internet' in content:
    print("✅ Section Web Navigator trouvée dans l'interface!")
    
    # Extraire la section pour vérification
    start_marker = "# 🌐 Recherche Internet (Web Navigator)"
    end_marker = "ui.separator().style('background: var(--accent-gold); opacity: 0.3;"
    
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker, start_idx)
    
    if start_idx != -1 and end_idx != -1:
        section = content[start_idx:end_idx]
        print("\n📖 Contenu de la section Web Navigator:")
        print("-" * 50)
        
        # Compter les phrases magiques
        phrases_count = section.count('"')
        if phrases_count > 0:
            print(f"✅ {phrases_count//2} phrases magiques détectées dans la section")
            
            # Afficher quelques exemples
            examples = [
                "/web [terme]",
                "cherche sur internet [terme]", 
                "il faut que je recherche sur le net",
                "actualités sur [sujet]"
            ]
            
            print("\n🔍 Vérification des phrases clés:")
            for example in examples:
                if example in section:
                    print(f"  ✅ '{example}' - Présente")
                else:
                    print(f"  ❌ '{example}' - Manquante")
        else:
            print("❌ Aucune phrase magique trouvée dans la section")
    else:
        print("❌ Impossible d'extraire la section complète")
else:
    print("❌ Section Web Navigator NON trouvée dans l'interface!")

# Vérifier aussi les autres sections principales
print(f"\n🔍 Vérification sections existantes:")
sections_to_check = [
    ('📖 Journal de Bord', '📖 Journal de Bord'),
    ('👤 Biographie Profil', '👤 Biographie Profil'), 
    ('🧠 Miroir Cognitif', '🧠 Miroir Cognitif'),
    ('💾 Mémorisation', '💾 Mémorisation'),
    ('📚 Conversations Archivées', '📚 Conversations Archivées')
]

for name, marker in sections_to_check:
    if marker in content:
        print(f"  ✅ {name} - Présente")
    else:
        print(f"  ❌ {name} - Manquante")

print("\n" + "=" * 70)
print("🎯 RÉSULTAT: Modification de l'interface des phrases magiques OGMA")
print("   La section Web Navigator devrait maintenant être visible")
print("   dans le tooltip 'Phrases magiques OGMA' du panneau de gauche.")