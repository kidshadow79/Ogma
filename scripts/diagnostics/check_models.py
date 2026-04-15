import json
import sys
import requests
from pathlib import Path

# Lit les clés depuis data/settings.json (comme le reste d'OGMA)
def _load_keys():
    settings_path = Path(__file__).parent.parent.parent / "data" / "settings.json"
    try:
        with open(settings_path, encoding="utf-8") as f:
            s = json.load(f)
        vault = s.get("api_keys_vault", {})
        return vault.get("Kie", ""), vault.get("WaveSpeed", "")
    except Exception as e:
        print(f"[ERROR] Impossible de lire data/settings.json : {e}")
        sys.exit(1)

KIE_KEY, WAVESPEED_KEY = _load_keys()

def check_kie():
    print("\n--- Checking Kie.ai Models ---")
    urls = [
        "https://api.kie.ai/api/v1/models",
        # "https://api.kie.ai/v1/models",
        # "https://api.kie.ai/models"
    ]
    headers = {"Authorization": f"Bearer {KIE_KEY}"}
    
    for url in urls:
        try:
            print(f"Trying {url}...")
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                print("Success!")
                try:
                    data = resp.json()
                    # Check format
                    models = []
                    if isinstance(data, list):
                        models = data
                    elif isinstance(data, dict):
                        if 'data' in data:
                            models = data['data']
                        elif 'models' in data:
                            models = data['models']
                        else:
                             print(f"Unknown structure keys: {data.keys()}")
                             # print(json.dumps(data, indent=2))
                    
                    print(f"Found {len(models)} models or items")
                    
                    keywords = ['edit', 'inpainting', 'image-to-image', 'i2i', 'pro', 'seedream', 'flux', 'qwen', 'fill', 'variations']
                    
                    found_relevant = False
                    for m in models:
                        mid = ""
                        if isinstance(m, str):
                            mid = m
                        else:
                            mid = m.get('id', m.get('model_id', m.get('name', str(m))))
                        
                        # Check relevance
                        is_relevant = any(k in mid.lower() for k in keywords)
                        if is_relevant:
                            print(f"MATCH: {mid}")
                            found_relevant = True
                    
                    if not found_relevant:
                        print("No keywords matched, printing first 20 IDs:")
                        for i, m in enumerate(models[:20]):
                             mid = m if isinstance(m, str) else m.get('id', m.get('name', str(m)))
                             print(f"  {mid}")
                    
                    return
                except Exception as e:
                    print(f"Could not parse JSON: {e}")
            else:
                print(f"Failed: {resp.status_code} - {resp.text[:100]}")
        except Exception as e:
            print(f"Error: {e}")

def check_wavespeed():
    print("\n--- Checking WaveSpeed.ai Models ---")
    urls = [
        "https://api.wavespeed.ai/api/v3/models",
        # "https://api.wavespeed.ai/v3/models", 
        # "https://api.wavespeed.ai/models"
    ]
    headers = {"Authorization": f"Bearer {WAVESPEED_KEY}"}
    
    for url in urls:
        try:
            print(f"Trying {url}...")
            resp = requests.get(url, headers=headers, timeout=10)
            if resp.status_code == 200:
                print("Success!")
                try:
                    data = resp.json()
                    models = []
                    if isinstance(data, list):
                        models = data
                    elif isinstance(data, dict):
                         if 'data' in data:
                            models = data['data']
                         else:
                             print(f"Unknown structure keys: {data.keys()}")
                    
                    print(f"Found {len(models)} models")
                    keywords = ['edit', 'inpainting', 'image-to-image', 'i2i', 'pro', 'seedream', 'flux', 'qwen', 'fill', 'variations']

                    found_relevant = False
                    for m in models:
                        mid = ""
                        if isinstance(m, str):
                            mid = m
                        else:
                             mid = m.get('id', m.get('name', str(m)))
                        
                        is_relevant = any(k in mid.lower() for k in keywords)
                        if is_relevant:
                            print(f"MATCH: {mid}")
                            found_relevant = True
                            
                    if not found_relevant:
                         print("No keywords matched, printing top 20:")
                         for i, m in enumerate(models[:20]):
                             mid = m if isinstance(m, str) else m.get('id', m.get('name', str(m)))
                             print(f"  {mid}")

                    return
                except Exception as e:
                    print(f"Could not parse JSON: {e}")
            else:
                print(f"Failed: {resp.status_code} - {resp.text[:100]}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    check_kie()
    check_wavespeed()
