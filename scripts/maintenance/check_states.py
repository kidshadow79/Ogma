import json

with open('extensions/journal_de_bord/data/journal_2025.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

states = [s for s in data['ÉTATS_ACTIFS']['states'] if not s.get('resolved')]

print('\n🎯 ÉTATS ACTIFS:', len(states))
print('=' * 70)
for s in states:
    print(f"\n#{s['state_id']} [{s['category'].upper()}] - {s['importance']}")
    print(f"   {s['description']}")
    if s.get('source_context'):
        conv_id = s['source_context'].get('conversation_id', 'N/A')
        print(f"   📅 Source: {conv_id}")
print('\n' + '=' * 70)
