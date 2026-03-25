"""Debug: simule exactement ce que le popup lit apres creation"""
import sys, json
sys.path.insert(0, '.')
from extensions.cognitive_mirror.config_v2 import get_introspection_config

config = get_introspection_config()

print("=== JSON FILE ===")
with open(config.settings_file, 'r', encoding='utf-8') as f:
    saved = json.load(f)
for k, v in saved.get('settings', {}).items():
    print(f"  JSON  {k}: {v}")

print()
print("=== SINGLETON IN MEMORY (config.get) ===")
for k in saved.get('settings', {}):
    mem = config.get(k, "NOT_IN_DEFAULTS")
    json_v = saved['settings'][k]
    marker = " *** MISMATCH ***" if mem != json_v else ""
    print(f"  MEM   {k}: {mem}{marker}")

print()
print("=== TOKENS: instruction_data vs settings ===")
for step in ['step1_analysis', 'step2_conscious', 'step2_unconscious', 'step3_synthesis']:
    instr_data = config.get_instruction(step)
    instr_tokens = instr_data.get('default_tokens', 500)
    
    # Ce que _on_tokens_changed sauverait comme settings key
    if step == 'step1_analysis': skey = 'step1_max_tokens'
    elif step == 'step2_conscious': skey = 'step2_conscious_max_tokens'
    elif step == 'step2_unconscious': skey = 'step2_unconscious_max_tokens'
    elif step == 'step3_synthesis': skey = 'step3_max_tokens'
    
    setting_tokens = config.get(skey, 'NOT_FOUND')
    marker = " *** UI SHOWS WRONG VALUE ***" if instr_tokens != setting_tokens else ""
    print(f"  {step}: instruction_data.default_tokens={instr_tokens}, settings[{skey}]={setting_tokens}{marker}")

print()
print("=== INSTRUCTION TEXT (80 chars) ===")
for step in ['step1_analysis', 'step2_conscious']:
    curr = config.get_instruction_text(step)[:80]
    default = config.DEFAULT_INSTRUCTIONS[step]['instruction'][:80]
    marker = " *** STILL DEFAULT ***" if curr == default else " (custom)"
    print(f"  {step}: {curr}...{marker}")
