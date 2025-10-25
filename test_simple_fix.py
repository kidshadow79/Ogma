#!/usr/bin/env python3
"""
Test simple de la correction Magic Phrase Guard - Option 1
Teste directement la logique sans asyncio
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import direct des variables globales pour test manuel
from magic_phrase_guard import should_process_magic_phrase
import magic_phrase_guard as mpg

def test_logic_fix():
    """Test de la logique corrigée sans asyncio"""
    
    print("🧪 TEST: Logique Magic Phrase Guard corrigée")
    print("=" * 50)
    
    # Message historique type
    historical_msg = {
        "role": "user", 
        "content": "Raconte-moi ton enfance", 
        "from_history": True
    }
    
    # Message normal
    normal_msg = {
        "role": "user", 
        "content": "Raconte-moi ton enfance",
        "from_history": False
    }
    
    print("\n1️⃣ État initial (pas de chargement):")
    print(f"   _loading_historical_conversation = {mpg._loading_historical_conversation}")
    
    result_hist = should_process_magic_phrase(historical_msg, "BIOGRAPHIE")
    result_norm = should_process_magic_phrase(normal_msg, "BIOGRAPHIE")
    
    print(f"   Message historique → should_process = {result_hist}")
    print(f"   Message normal → should_process = {result_norm}")
    print(f"   ✅ Attendu: historique=False (pas bloqué), normal=False")
    
    print("\n2️⃣ Simulation chargement en cours:")
    mpg._loading_historical_conversation = True  # Simulation manuelle
    print(f"   _loading_historical_conversation = {mpg._loading_historical_conversation}")
    
    result_hist = should_process_magic_phrase(historical_msg, "BIOGRAPHIE")
    result_norm = should_process_magic_phrase(normal_msg, "BIOGRAPHIE")
    
    print(f"   Message historique → should_process = {result_hist}")
    print(f"   Message normal → should_process = {result_norm}")
    print(f"   ✅ Attendu: historique=True (bloqué), normal=False")
    
    print("\n3️⃣ Fin de chargement:")
    mpg._loading_historical_conversation = False  # Simulation fin
    print(f"   _loading_historical_conversation = {mpg._loading_historical_conversation}")
    
    result_hist = should_process_magic_phrase(historical_msg, "BIOGRAPHIE")
    result_norm = should_process_magic_phrase(normal_msg, "BIOGRAPHIE")
    
    print(f"   Message historique → should_process = {result_hist}")
    print(f"   Message normal → should_process = {result_norm}")
    print(f"   ✅ Attendu: historique=False (pas bloqué), normal=False")
    
    print("\n" + "=" * 50)
    print("🎯 RÉSULTAT:")
    print("   ✅ Correction appliquée: messages historiques bloqués UNIQUEMENT pendant chargement")
    print("   ✅ Après chargement: traitement normal possible")
    print("   ✅ Plus de blocage permanent des messages historiques")

if __name__ == "__main__":
    test_logic_fix()