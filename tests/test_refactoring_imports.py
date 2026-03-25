import sys
import os
import asyncio
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

async def test_refactoring():
    print("=== TEST REFACTORING MODULES ===")
    
    # 1. Test importing new modules
    try:
        from modules.logic import (
            get_visual_events_context,
            caviarder_phrases_magiques_introspection,
            run_ego_selector_analysis,
            trigger_indexing_fn,
            process_image_generation,
            process_img2img_generation
        )
        print("✅ Import modules/logic OK")
    except ImportError as e:
        print(f"❌ Erreur import modules/logic: {e}")
        return

    # 2. Test importing logic_callbacks (legacy Shim)
    try:
        import logic_callbacks
        print("✅ Import logic_callbacks OK")
    except Exception as e:
        print(f"❌ Erreur import logic_callbacks: {e}")
        import traceback
        traceback.print_exc()
        return

    # 3. Verify function references match
    try:
        # Check standard Shim functions (imported from modules)
        assert logic_callbacks.run_ego_selector_analysis == run_ego_selector_analysis
        assert logic_callbacks.trigger_indexing_fn == trigger_indexing_fn
        assert logic_callbacks.process_image_generation == process_image_generation
        assert logic_callbacks.process_img2img_generation == process_img2img_generation
        
        # Check explicit assignments (if any were manual)
        assert logic_callbacks.caviarder_phrases_magiques_introspection == caviarder_phrases_magiques_introspection
        assert logic_callbacks._get_visual_events_context == get_visual_events_context
        
        print("✅ Verification references Shim OK")
        
    except AssertionError as e:
        print(f"❌ Erreur correspondance Shim (AssertionError)")
        return

    print("=== TOUS LES TESTS PASSÉS AVEC SUCCÈS ===")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.run_until_complete(test_refactoring())
