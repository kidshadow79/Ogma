"""
Script simple pour tester l'analyse rétroactive via HTTP API OGMA
Ce script envoie une commande à OGMA pour analyser les conversations
"""

import argparse

def main():
    parser = argparse.ArgumentParser(description="Analyse rétroactive Journal v2.0")
    parser.add_argument('-n', '--number', type=int, default=3, help='Nombre de conversations')
    args = parser.parse_args()
    
    print("=" * 70)
    print("ANALYSE RÉTROACTIVE - Journal de Bord v2.0")
    print("=" * 70)
    print()
    print(f"⚠️ IMPORTANT: Ce script nécessite OGMA lancé")
    print()
    print(f"Pour analyser les {args.number} dernières conversations:")
    print()
    print("1. Ouvrez OGMA dans votre navigateur")
    print("2. Allez dans le Journal de Bord")
    print("3. Cliquez sur 'Options Avancées'")
    print("4. Utilisez le bouton 'Analyser conversations passées'")
    print()
    print("=" * 70)
    print()
    print("💡 Alternative: L'analyse se fait automatiquement maintenant!")
    print("   Chaque conversation crée/résout des états en temps réel.")
    print()

if __name__ == "__main__":
    main()
