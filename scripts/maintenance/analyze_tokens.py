"""Analyse rapide des tokens Archiviste"""
import json
from collections import defaultdict
from pathlib import Path

# Lire fichier JSONL
jsonl_file = Path('data/archiviste_tokens_debug.jsonl')
calls = []
with open(jsonl_file, 'r', encoding='utf-8') as f:
    for line in f:
        calls.append(json.loads(line))

# Statistiques globales
total_input = sum(c['input_tokens_estimated'] for c in calls)
total_output = sum(c['output_tokens_estimated'] for c in calls)
total = total_input + total_output

print('📊 ANALYSE CONSOMMATION ARCHIVISTE')
print('='*70)
print(f'Nombre d\'appels: {len(calls)}')
print(f'Total INPUT:  {total_input:,} tokens')
print(f'Total OUTPUT: {total_output:,} tokens')
print(f'TOTAL:        {total:,} tokens')
print(f'Moyenne/appel: {total//len(calls):,} tokens')
print(f'Ratio INPUT/OUTPUT: {total_input/total_output:.2f}:1')

# Par source
by_source = defaultdict(lambda: {'count': 0, 'input': 0, 'output': 0})
for c in calls:
    src = c['source']
    by_source[src]['count'] += 1
    by_source[src]['input'] += c['input_tokens_estimated']
    by_source[src]['output'] += c['output_tokens_estimated']

print('\n🔥 PAR SOURCE:')
for src, stats in sorted(by_source.items(), key=lambda x: x[1]['input']+x[1]['output'], reverse=True):
    total_src = stats['input'] + stats['output']
    pct = total_src / total * 100
    print(f'  {src}: {total_src:,} tokens ({pct:.1f}%) - {stats["count"]} appels')
    print(f'    IN: {stats["input"]:,} | OUT: {stats["output"]:,}')

# Distribution par taille
print('\n📏 DISTRIBUTION TAILLE APPELS:')
bins = [0, 500, 1000, 2000, 5000, 10000, 50000]
for i in range(len(bins)-1):
    count = sum(1 for c in calls if bins[i] <= c['total_tokens'] < bins[i+1])
    print(f'  {bins[i]}-{bins[i+1]} tokens: {count} appels')
count_huge = sum(1 for c in calls if c['total_tokens'] >= bins[-1])
print(f'  >{bins[-1]:,} tokens: {count_huge} appels')

# Top 5 plus gros appels
print('\n🔝 TOP 5 PLUS GROS APPELS:')
top5 = sorted(calls, key=lambda x: x['total_tokens'], reverse=True)[:5]
for i, c in enumerate(top5, 1):
    print(f'{i}. {c["total_tokens"]:,} tokens ({c["source"]}) - IN:{c["input_tokens_estimated"]:,} OUT:{c["output_tokens_estimated"]:,}')
    print(f'   Temp: {c["metadata"]["temperature"]}, MaxTok: {c["metadata"]["max_tokens"]}')

# Analyse température
print('\n🌡️ PAR TEMPÉRATURE:')
by_temp = defaultdict(lambda: {'count': 0, 'total': 0})
for c in calls:
    temp = c['metadata']['temperature']
    by_temp[temp]['count'] += 1
    by_temp[temp]['total'] += c['total_tokens']

for temp, stats in sorted(by_temp.items()):
    avg = stats['total'] // stats['count']
    print(f'  Temp {temp}: {stats["count"]} appels, avg {avg:,} tokens/appel')
