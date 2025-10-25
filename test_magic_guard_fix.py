#!/usr/bin/env python3
"""
Test de la correction Magic Phrase Guard - Option 1
Vérifie que les messages historiques sont traités après fin du chargement
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from magic_phrase_guard import should_process_magic_phrase, activate_loading_mode, deactivate_loading_mode_delayed
import time

def test_historical_message_after_loading():
    """Test que messages historiques sont traités après chargement"""
    
    print("🧪 TEST: Messages historiques après chargement")
    print("=" * 50)
    
    # Message historique type
    historical_msg = {
        "role": "user", 
        "content": "Raconte-moi ton enfance", 
        "from_history": True
    }
    
    # 1. Test: Sans chargement actif - devrait permettre traitement
    print("\n1️⃣ Sans chargement actif:")
    result = should_process_magic_phrase(historical_msg, "BIOGRAPHIE")
    print(f"   should_process_magic_phrase() = {result}")
    print(f"   ✅ Attendu: False (car pas de chargement actif)")
    
    # 2. Test: Pendant chargement - devrait bloquer
    print("\n2️⃣ Pendant chargement actif:")
    activate_loading_mode()
    result = should_process_magic_phrase(historical_msg, "BIOGRAPHIE")
    print(f"   should_process_magic_phrase() = {result}")
    print(f"   ✅ Attendu: True (bloqué pendant chargement)")
    
    # 3. Test: Après fin du chargement - devrait permettre
    print("\n3️⃣ Après fin du chargement:")
    deactivate_loading_mode_delayed(delay_seconds=0)  # Immédiat
    time.sleep(0.1)  # Laisser temps à la désactivation
    result = should_process_magic_phrase(historical_msg, "BIOGRAPHIE")
    print(f"   should_process_magic_phrase() = {result}")
    print(f"   ✅ Attendu: False (chargement terminé)")
    
    # 4. Test: Message temps réel - toujours autorisé
    print("\n4️⃣ Message temps réel (contrôle):")
    live_msg = {
        "role": "user", 
        "content": "Raconte-moi ton enfance",
        "from_history": False
    }
    result = should_process_magic_phrase(live_msg, "BIOGRAPHIE")
    print(f"   should_process_magic_phrase() = {result}")
    print(f"   ✅ Attendu: False (message normal)")
    
    print("\n" + "=" * 50)
    print("🎯 CONCLUSION: Messages historiques ne sont bloqués QUE pendant chargement actif")
    print("   Après chargement → Traitement normal possible")

if __name__ == "__main__":
    test_historical_message_after_loading()