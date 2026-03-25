
import sys
import os

# Ajout du chemin racine au path
sys.path.append(os.getcwd())

def test_audio_import():
    print("Testing audio imports...")
    try:
        from modules.audio import play_audio_file
        print("✅ Import 'play_audio_file' from 'modules.audio' SUCCESS")
    except ImportError as e:
        print(f"❌ Import 'play_audio_file' from 'modules.audio' FAILED: {e}")
        return False

    try:
        from modules.audio.tts_utils import play_audio_file as paf
        print("✅ Import 'play_audio_file' from 'modules.audio.tts_utils' SUCCESS")
    except ImportError as e:
        print(f"❌ Import 'play_audio_file' from 'modules.audio.tts_utils' FAILED: {e}")
        return False
        
    return True

if __name__ == "__main__":
    if test_audio_import():
        print("=== AUDIO IMPORT TEST PASSED ===")
        sys.exit(0)
    else:
        print("=== AUDIO IMPORT TEST FAILED ===")
        sys.exit(1)
