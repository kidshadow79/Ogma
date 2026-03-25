"""Analyse détaillée des appels ego_selection"""
import json

jsonl_file = 'data/archiviste_tokens_debug.jsonl'
ego_calls = []

with open(jsonl_file, 'r', encoding='utf-8') as f:
    for line in f:
        call = json.loads(line)
        if call['source'] == 'ego_selection':
            ego_calls.append(call)

if ego_calls:
    print(f'📊 {len(ego_calls)} appels ego_selection trouvés')
    print()
    
    # Stats
    avg_input = sum(c['input_tokens_estimated'] for c in ego_calls) // len(ego_calls)
    avg_output = sum(c['output_tokens_estimated'] for c in ego_calls) // len(ego_calls)
    avg_total = avg_input + avg_output
    
    print(f'Moyenne INPUT:  {avg_input:,} tokens')
    print(f'Moyenne OUTPUT: {avg_output:,} tokens')
    print(f'Moyenne TOTAL:  {avg_total:,} tokens')
    print()
    
    # Détail premier appel
    first = ego_calls[0]
    print('📄 Premier appel (détail):')
    print(f'  Input chars:  {first["input_chars"]:,}')
    print(f'  Input tokens: {first["input_tokens_estimated"]:,}')
    print(f'  Temperature:  {first["metadata"]["temperature"]}')
    print()
    
    # Estimation contenu
    catalog_est = 50 * 50  # 50 souvenirs × 50 chars titre
    context_est = 6 * 100  # 6 messages × 100 chars
    prompt_overhead = 1000  # Instructions système
    
    total_est = catalog_est + context_est + prompt_overhead
    print('📐 Estimation composition INPUT:')
    print(f'  Catalogue (50 titres):  ~{catalog_est:,} chars (~{catalog_est//4} tokens)')
    print(f'  Contexte (6 messages):  ~{context_est:,} chars (~{context_est//4} tokens)')
    print(f'  Prompt système:         ~{prompt_overhead:,} chars (~{prompt_overhead//4} tokens)')
    print(f'  TOTAL ESTIMÉ:           ~{total_est:,} chars (~{total_est//4} tokens)')
    print()
    print(f'  RÉEL MESURÉ:            {first["input_chars"]:,} chars ({first["input_tokens_estimated"]:,} tokens)')
    print(f'  DIFFÉRENCE:             {first["input_chars"] - total_est:+,} chars')
    
    # Distribution tailles
    print('\n📊 Distribution tailles INPUT:')
    for i, call in enumerate(ego_calls, 1):
        print(f'  Appel {i}: {call["input_tokens_estimated"]:,} tokens (temp={call["metadata"]["temperature"]})')
else:
    print('❌ Aucun appel ego_selection trouvé')
