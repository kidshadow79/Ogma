"""
GÉNÉRATEUR DE RAPPORT ARCHIVISTE
=================================
Script autonome pour afficher et sauvegarder le rapport de consommation tokens.

Usage:
    python generate_archiviste_report.py

Résultat:
    - Affichage console formaté
    - Sauvegarde data/archiviste_monitoring.json
"""

import sys
from pathlib import Path

def main():
    """Point d'entrée principal"""
    try:
        from archiviste_logger import get_archiviste_logger, save_and_print_report
        
        print("\n" + "="*70)
        print("📊 GÉNÉRATION DU RAPPORT ARCHIVISTE")
        print("="*70 + "\n")
        
        # Générer et afficher le rapport
        save_and_print_report()
        
        print("\n✅ Rapport généré avec succès!")
        print(f"📄 Fichier: {Path('data/archiviste_monitoring.json').absolute()}")
        
    except ImportError:
        print("❌ Erreur: archiviste_logger.py introuvable")
        print("💡 Le logging n'a probablement pas été activé ou OGMA pas lancé")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur génération rapport: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
